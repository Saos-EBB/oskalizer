#!/usr/bin/env python3
"""Keyboard playground: grabbt eine externe Tastatur (+ Maus) exklusiv und malt
ruhige, abstrakte Blobs. Beenden: Esc 5 Sekunden halten.

Braucht: python-evdev, pygame und Lesezugriff auf /dev/input/* (Gruppe `input`).
"""

# --- CONFIG ----------------------------------------------------------------

KEYBOARD_MATCH = "blackwidow"   # case-insensitive substring im Geraetenamen
GRAB_MOUSE = True

FPS = 60
BACKGROUND = (6, 6, 10)
EXIT_HOLD_SECONDS = 5.0

# Mash-Schutz
MAX_BLOBS = 14                  # Cap auf gleichzeitig aktive Elemente
MIN_SPAWN_INTERVAL = 0.09       # schnellere Eingaben werden zusammengefasst
MOTION_SPAWN_INTERVAL = 0.35    # Mausbewegung darf noch viel weniger spawnen
MOTION_DISTANCE = 250           # aufsummierte Pixel bis ein Bewegungs-Blob kommt
BRIGHTNESS_BUDGET = 2.4         # Summe der Intensitaeten, danach dimmt alles sanft

# Blobs
BLOB_LIFETIME = (1.6, 3.0)      # Sekunden, langsames Ein-/Ausfaden
BLOB_RADIUS = (0.06, 0.15)      # Anteil der kuerzeren Bildschirmseite
BLOB_PEAK = 0.55                # maximale Helligkeit eines einzelnen Blobs
BLOB_DRIFT = 14                 # Pixel pro Sekunde, sanftes Treiben
RETIRE_FADE = 0.6               # so lange braucht ein verdraengter Blob zum Gehen

PALETTE = [
    (150, 190, 255),   # helles blau
    (255, 180, 210),   # rosa
    (180, 240, 210),   # mint
    (255, 220, 160),   # sand
    (205, 180, 255),   # flieder
    (170, 225, 245),   # eisblau
]

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


def make_blob_template(size=256):
    """Weicher radialer Verlauf in Graustufen, schwarz = traegt additiv nichts bei."""
    surf = pygame.Surface((size, size))
    surf.fill((0, 0, 0))
    center = size // 2
    for radius in range(center, 0, -1):
        t = radius / center
        value = int(255 * (1.0 - t) ** 2.2)
        pygame.draw.circle(surf, (value, value, value), (center, center), radius)
    return surf


class Blob:
    def __init__(self, template, pos, radius, color, life):
        diameter = max(8, int(radius * 2))
        self.base = pygame.transform.smoothscale(template, (diameter, diameter))
        self.buf = self.base.copy()
        self.rect = self.base.get_rect(center=pos)
        self.x, self.y = float(pos[0]), float(pos[1])
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.3, 1.0) * BLOB_DRIFT
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.color = color
        self.life = life
        self.age = 0.0
        self.rate = 1.0
        self.retiring = False

    @property
    def intensity(self):
        phase = min(1.0, max(0.0, self.age / self.life))
        return math.sin(math.pi * phase) ** 1.2 * BLOB_PEAK

    @property
    def dead(self):
        return self.age >= self.life

    def retire(self):
        """Sanft rauswerfen: Intensitaet bleibt stetig, nur die Zeit laeuft schneller."""
        self.retiring = True
        if self.age < self.life * 0.5:
            self.age = self.life - self.age      # auf die fallende Flanke spiegeln
        remaining = self.life - self.age
        if remaining > RETIRE_FADE:
            self.rate = max(self.rate, remaining / RETIRE_FADE)

    def update(self, dt):
        self.age += dt * self.rate
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen, gain):
        level = self.intensity * gain
        if level <= 0.004:
            return
        tint = (int(self.color[0] * level), int(self.color[1] * level), int(self.color[2] * level))
        self.buf.blit(self.base, (0, 0))
        self.buf.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        screen.blit(self.buf, self.rect, special_flags=pygame.BLEND_RGB_ADD)


class Playground:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.template = make_blob_template()
        self.blobs = []
        self.gain = 1.0
        self.last_spawn = 0.0
        self.last_motion_spawn = 0.0
        self.motion_accum = 0.0

    def spawn(self, now):
        """Rate-limitiert. Zu schnelle Eingaben werden auf den letzten Blob
        zusammengefasst statt neue zu erzeugen."""
        if now - self.last_spawn < MIN_SPAWN_INTERVAL:
            return      # geschluckt: bei ~11 Blobs/s ist ohnehin genug los
        self.last_spawn = now

        if len(self.blobs) >= MAX_BLOBS:
            # aeltesten noch "lebenden" Blob sanft rauswinken statt hart loeschen.
            # Die schon ausfadenden zaehlen kurz obendrauf (gemessen: bis ~20
            # gleichzeitig bei Dauerhaemmern), sind aber nach RETIRE_FADE weg.
            victim = next((b for b in self.blobs if not b.retiring), None)
            if victim is None:
                return          # alles faded schon aus - Eingabe wird geschluckt
            victim.retire()

        short = min(self.width, self.height)
        radius = random.uniform(*BLOB_RADIUS) * short
        margin = radius * 0.4
        pos = (
            random.uniform(margin, self.width - margin),
            random.uniform(margin, self.height - margin),
        )
        self.blobs.append(
            Blob(self.template, pos, radius, random.choice(PALETTE),
                 random.uniform(*BLOB_LIFETIME))
        )

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

        # weicher Gesamt-Helligkeitsdeckel: nichts blitzt auf, alles zieht sanft nach
        total = sum(b.intensity for b in self.blobs)
        target = min(1.0, BRIGHTNESS_BUDGET / total) if total > 0 else 1.0
        self.gain += (target - self.gain) * min(1.0, dt * 3.0)

    def draw(self, esc_progress):
        self.screen.fill(BACKGROUND)
        for blob in self.blobs:
            blob.draw(self.screen, self.gain)
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
