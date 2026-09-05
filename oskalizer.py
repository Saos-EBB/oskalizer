#!/usr/bin/env python3
"""Keyboard playground: grabbt eine externe Tastatur (+ Maus) exklusiv und malt
bunte, ruhig ein- und ausblendende Farbkleckse. Beenden: Esc 5 Sekunden halten.

Braucht: python-evdev, pygame und Lesezugriff auf /dev/input/* (Gruppe `input`).
"""

# --- CONFIG ----------------------------------------------------------------

KEYBOARD_MATCH = "blackwidow"   # case-insensitive substring im Geraetenamen
GRAB_MOUSE = True

FPS = 60
BACKGROUND = (10, 10, 14)       # bleibt konstant, wird nie geflutet
EXIT_HOLD_SECONDS = 5.0

# Mash-Schutz
MAX_BLOBS = 150                 # Cap auf gleichzeitig aktive Kleckse
MIN_SPAWN_INTERVAL = 0.09       # schnellere Eingaben werden geschluckt
MOTION_SPAWN_INTERVAL = 0.35    # Mausbewegung darf noch viel weniger spawnen
MOTION_DISTANCE = 250           # aufsummierte Pixel bis ein Bewegungs-Cluster kommt

# Kleckse
BLOBS_PER_EVENT = (3, 6)        # pro Eingabe, um eine gemeinsame Mitte gestreut
CLUSTER_SPREAD = 1.6            # Streuung um die Mitte, in groessten Radien
BLOB_RADIUS = (0.015, 0.045)    # Anteil der kuerzeren Bildschirmseite
BLOB_LIFETIME = (1.5, 3.0)      # Sekunden
BLOB_FADE_IN = 0.45             # sanft rein, den Rest der Zeit langsam raus
BLOB_PEAK = 0.85                # maximale Deckkraft, Hintergrund bleibt ahnbar
BLOB_DRIFT = 12                 # Pixel pro Sekunde, sanftes Treiben
RETIRE_FADE = 0.6               # so lange braucht ein verdraengter Klecks zum Gehen

# Farben: volles Spektrum, satt und hell (kein Pastell)
HUE_RANGE = (0, 360)
SATURATION = (0.80, 1.00)
VALUE = (0.90, 1.00)

# --- Ende CONFIG -----------------------------------------------------------

import math
import os
import random
import select
import signal
import sys

import evdev
from evdev import ecodes

import pygame

SUPERSAMPLE = 3                 # nur fuer glatte Kreiskanten, kein Weichzeichner


def play_sound(event):
    """Hook fuer spaeter: hier koennte pro Eingabe ein Ton kommen."""
    pass


# --- Geraete ---------------------------------------------------------------


def is_pointer(device):
    """Zeigegeraet: relative Achsen plus linke Maustaste."""
    caps = device.capabilities()
    return ecodes.EV_REL in caps and ecodes.BTN_LEFT in caps.get(ecodes.EV_KEY, [])


def find_devices():
    """Liefert (keyboards, pointers). Razer haengt mehrere event-Nodes an den
    gleichen Namen (Keys + Media/Macro) - wir nehmen bewusst ALLE."""
    keyboards, pointers = [], []
    needle = KEYBOARD_MATCH.lower()
    denied = 0

    for path in sorted(evdev.list_devices()):
        try:
            device = evdev.InputDevice(path)
        except PermissionError:
            denied += 1
            continue
        except OSError:
            continue

        if needle in device.name.lower():
            keyboards.append(device)
        elif GRAB_MOUSE and is_pointer(device):
            pointers.append(device)
        else:
            device.close()

    if denied and not keyboards:
        raise PermissionError("keine Leserechte auf /dev/input/*")
    return keyboards, pointers


def grab_all(devices):
    """Grabbt was geht, gibt die erfolgreich gegrabbten Geraete zurueck."""
    grabbed = []
    for device in devices:
        try:
            device.grab()
        except OSError as exc:
            print(f"  ! {device.path} ({device.name}): grab fehlgeschlagen: {exc}")
            device.close()
            continue
        grabbed.append(device)
        print(f"  + {device.path}  {device.name}")
    return grabbed


def release_all(devices):
    """Muss IMMER laufen, sonst bleibt die Tastatur gesperrt."""
    for device in devices:
        try:
            device.ungrab()
        except Exception:
            pass
        try:
            device.close()
        except Exception:
            pass


# --- Visuals ---------------------------------------------------------------


def random_color():
    """Zufaellig durchs ganze Spektrum, satt und hell."""
    color = pygame.Color(0)
    color.hsva = (
        random.uniform(*HUE_RANGE) % 360.0,
        random.uniform(*SATURATION) * 100.0,
        random.uniform(*VALUE) * 100.0,
        100.0,
    )
    return color


def make_disc(radius, color):
    """Gefuellter Kreis mit sauberer Kante. Gross zeichnen und herunterskalieren
    glaettet nur die Treppchen am Rand - der Klecks bleibt hart begrenzt."""
    size = max(2, int(radius * 2))
    big = pygame.Surface((size * SUPERSAMPLE,) * 2, pygame.SRCALPHA)
    center = size * SUPERSAMPLE // 2
    pygame.draw.circle(big, color, (center, center), center)
    return pygame.transform.smoothscale(big, (size, size))


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3.0 - 2.0 * x)


class Blob:
    def __init__(self, pos, radius, color, life):
        self.surf = make_disc(radius, color)
        self.rect = self.surf.get_rect(center=pos)
        self.x, self.y = float(pos[0]), float(pos[1])
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.3, 1.0) * BLOB_DRIFT
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.life = max(life, BLOB_FADE_IN + 0.2)
        self.age = 0.0
        self.retiring = False
        self.retire_gain = 1.0

    @property
    def intensity(self):
        if self.age < BLOB_FADE_IN:
            envelope = smoothstep(self.age / BLOB_FADE_IN)
        else:
            rest = (self.age - BLOB_FADE_IN) / (self.life - BLOB_FADE_IN)
            envelope = smoothstep(1.0 - rest)
        return envelope * self.retire_gain * BLOB_PEAK

    @property
    def dead(self):
        return self.age >= self.life or self.retire_gain <= 0.0

    def retire(self):
        """Verdraengt: eigener Ausblend-Faktor, damit die Helligkeit stetig bleibt."""
        self.retiring = True

    def update(self, dt):
        self.age += dt
        if self.retiring:
            self.retire_gain -= dt / RETIRE_FADE
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen):
        alpha = int(self.intensity * 255)
        if alpha <= 1:
            return
        self.surf.set_alpha(alpha)
        screen.blit(self.surf, self.rect)


class Playground:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.short = min(self.width, self.height)
        self.blobs = []
        self.last_spawn = 0.0
        self.last_motion_spawn = 0.0
        self.motion_accum = 0.0

    def spawn(self, now):
        """Ein Cluster aus mehreren Klecksen. Rate-limitiert: schnellere
        Eingaben werden geschluckt statt aufgestaut."""
        if now - self.last_spawn < MIN_SPAWN_INTERVAL:
            return
        self.last_spawn = now

        spread = CLUSTER_SPREAD * BLOB_RADIUS[1] * self.short
        margin = spread + BLOB_RADIUS[1] * self.short
        cx = random.uniform(margin, self.width - margin)
        cy = random.uniform(margin, self.height - margin)

        for _ in range(random.randint(*BLOBS_PER_EVENT)):
            if not self.make_room():
                break
            angle = random.uniform(0, math.tau)
            dist = math.sqrt(random.random()) * spread
            self.blobs.append(Blob(
                (cx + math.cos(angle) * dist, cy + math.sin(angle) * dist),
                random.uniform(*BLOB_RADIUS) * self.short,
                random_color(),
                random.uniform(*BLOB_LIFETIME),
            ))

    def make_room(self):
        """Aeltesten noch lebenden Klecks sanft rauswinken statt hart loeschen.
        Sind schon alle am Ausblenden, wird der Spawn geschluckt."""
        if len(self.blobs) < MAX_BLOBS:
            return True
        victim = next((b for b in self.blobs if not b.retiring), None)
        if victim is None:
            return False
        victim.retire()
        return True

    def on_motion(self, distance, now):
        self.motion_accum += distance
        if self.motion_accum < MOTION_DISTANCE:
            return
        self.motion_accum = 0.0
        if now - self.last_motion_spawn < MOTION_SPAWN_INTERVAL:
            return
        self.last_motion_spawn = now
        self.spawn(now)

    def update(self, dt):
        for blob in self.blobs:
            blob.update(dt)
        self.blobs = [b for b in self.blobs if not b.dead]

    def draw(self, esc_progress):
        self.screen.fill(BACKGROUND)
        for blob in self.blobs:
            blob.draw(self.screen)
        if esc_progress > 0:
            self.draw_exit_hint(esc_progress)

    def draw_exit_hint(self, progress):
        rect = pygame.Rect(0, 0, 26, 26)
        rect.center = (self.width // 2, self.height - 44)
        start = math.pi / 2
        pygame.draw.arc(self.screen, (70, 70, 84), rect, 0, math.tau, 1)
        pygame.draw.arc(self.screen, (150, 150, 175), rect,
                        start, start + math.tau * min(1.0, progress), 2)


# --- Main ------------------------------------------------------------------


def handle_input(device, playground, state, now):
    """Verarbeitet die anstehenden Events eines Geraets."""
    for event in device.read():
        if event.type == ecodes.EV_KEY:
            if event.code == ecodes.KEY_ESC:
                if event.value == 1:
                    state["esc_since"] = now
                elif event.value == 0:
                    state["esc_since"] = None
            if event.value == 1:                      # nur Key-Down, keine Repeats
                play_sound(event)
                playground.spawn(now)
        elif event.type == ecodes.EV_REL:
            if event.code in (ecodes.REL_X, ecodes.REL_Y):
                playground.on_motion(abs(event.value), now)


def run(devices):
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("keyboard playground")
    pygame.mouse.set_visible(False)

    playground = Playground(screen)
    clock = pygame.time.Clock()
    fds = {device.fd: device for device in devices}
    state = {"esc_since": None}

    while True:
        dt = clock.tick(FPS) / 1000.0
        now = pygame.time.get_ticks() / 1000.0
        pygame.event.pump()

        ready, _, _ = select.select(list(fds), [], [], 0)
        for fd in ready:
            try:
                handle_input(fds[fd], playground, state, now)
            except (BlockingIOError, OSError):
                pass

        esc_since = state["esc_since"]
        held = (now - esc_since) if esc_since is not None else 0.0
        if held >= EXIT_HOLD_SECONDS:
            return

        playground.update(dt)
        playground.draw(held / EXIT_HOLD_SECONDS if esc_since is not None else 0.0)
        pygame.display.flip()


def main():
    def bail(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, bail)
    signal.signal(signal.SIGINT, bail)

    try:
        keyboards, pointers = find_devices()
    except PermissionError:
        print("Keine Rechte auf /dev/input/*.\n"
              "  sudo usermod -aG input $USER   (danach neu einloggen)\n"
              "  oder das Tool mit sudo starten.", file=sys.stderr)
        return 1

    if not keyboards:
        print(f"Keine Tastatur gefunden, die '{KEYBOARD_MATCH}' im Namen hat.\n"
              "Namen anschauen mit:  python3 -c \"import evdev;"
              " print([evdev.InputDevice(p).name for p in evdev.list_devices()])\"",
              file=sys.stderr)
        release_all(pointers)
        return 1

    print("Grabbe Geraete:")
    grabbed = grab_all(keyboards) + grab_all(pointers)

    if not any(ecodes.KEY_ESC in d.capabilities().get(ecodes.EV_KEY, []) for d in grabbed):
        print("Kein gegrabbtes Geraet kann Esc senden - ohne das gibt es keinen Exit.",
              file=sys.stderr)
        release_all(grabbed)
        return 1

    print(f"Laeuft. Beenden: Esc {EXIT_HOLD_SECONDS:.0f} Sekunden halten "
          f"(Notausgang: kill {os.getpid()}).")
    try:
        run(grabbed)
    finally:
        release_all(grabbed)
        pygame.quit()
        print("Geraete freigegeben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
