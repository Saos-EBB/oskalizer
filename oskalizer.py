#!/usr/bin/env python3
"""Keyboard playground: grabbt eine externe Tastatur (+ Maus) exklusiv und malt
abstrakte Kleckse. Beenden: Esc 5 Sekunden halten.

Braucht: python-evdev, pygame und Lesezugriff auf /dev/input/* (Gruppe `input`).
"""

# --- CONFIG ----------------------------------------------------------------

KEYBOARD_MATCH = "blackwidow"   # case-insensitive substring im Geraetenamen
GRAB_MOUSE     = True

STYLE   = "ink"        # "ink" | "orbs" | "goo"
PALETTE = "full_rgb"   # "full_rgb" | "neon" | "sunset" | "ocean" | "candy"
COUNT   = 1            # Kleckse pro Eingabe
SIZE    = 90           # Basisgroesse
LIFE    = 2.2          # Sekunden
DRIFT   = 41           # Anfangsgeschwindigkeit-Streuung
MAX_BLOBS = 180

# Mash-Schutz (das Kind haemmert) und Exit
MIN_SPAWN_INTERVAL    = 0.09    # Sekunden zwischen zwei Spawns, schnellere entfallen
MOTION_SPAWN_INTERVAL = 0.35    # Mausbewegung darf noch viel weniger spawnen
MOTION_DISTANCE       = 250     # aufsummierte Pixel bis ein Bewegungs-Spawn kommt
EXIT_HOLD_SECONDS     = 5.0
FPS = 60

# --- Ende CONFIG -----------------------------------------------------------

import math
import os
import select
import signal
import sys

import evdev
from evdev import ecodes

import pygame

import visuals
from devpanel import DevPanel


class Config:
    """Die im Dev-Panel drehbaren Werte, plus die festen Grenzen."""

    def __init__(self):
        self.style = STYLE
        self.palette = PALETTE
        self.count = COUNT
        self.size = SIZE
        self.life = LIFE
        self.drift = DRIFT
        self.max_blobs = MAX_BLOBS
        self.min_spawn_interval = MIN_SPAWN_INTERVAL
        self.motion_spawn_interval = MOTION_SPAWN_INTERVAL
        self.motion_distance = MOTION_DISTANCE


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


# --- Loop ------------------------------------------------------------------


def handle_input(device, field, panel, state, now):
    """Verarbeitet die anstehenden Events eines Geraets."""
    for event in device.read():
        if event.type == ecodes.EV_KEY:
            if event.code == ecodes.KEY_ESC:
                if event.value == 1:
                    state["esc_since"] = now
                elif event.value == 0:
                    state["esc_since"] = None
            if panel.handle_key(event.code, event.value):
                continue                          # Panel-Bedienung spawnt nichts
            if event.value == 1:                  # nur Key-Down, keine Repeats
                play_sound(event)
                field.spawn(now)
        elif event.type == ecodes.EV_REL:
            if event.code in (ecodes.REL_X, ecodes.REL_Y):
                field.on_motion(abs(event.value), now)


def draw_exit_hint(screen, progress):
    """Kleiner Ring unten mittig, damit der Erwachsene sieht, dass Esc zieht."""
    rect = pygame.Rect(0, 0, 26, 26)
    rect.center = (screen.get_width() // 2, screen.get_height() - 44)
    pygame.draw.arc(screen, (70, 70, 84), rect, 0, math.tau, 1)
    pygame.draw.arc(screen, (150, 150, 175), rect, math.pi / 2,
                    math.pi / 2 + math.tau * min(1.0, progress), 2)


def run(devices, cfg):
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("keyboard playground")
    pygame.mouse.set_visible(False)

    field = visuals.Field(screen, cfg)
    panel = DevPanel(cfg)
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
                handle_input(fds[fd], field, panel, state, now)
            except (BlockingIOError, OSError):
                pass

        esc_since = state["esc_since"]
        held = (now - esc_since) if esc_since is not None else 0.0
        if held >= EXIT_HOLD_SECONDS:
            return

        field.update(dt)
        field.draw()
        if esc_since is not None:
            draw_exit_hint(screen, held / EXIT_HOLD_SECONDS)
        panel.draw(screen)
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

    print(f"Laeuft. Beenden: Esc {EXIT_HOLD_SECONDS:.0f} Sekunden halten. "
          f"Dev-Panel: Strg+Umschalt+D. (Notausgang: kill {os.getpid()})")
    try:
        run(grabbed, Config())
    finally:
        release_all(grabbed)
        pygame.quit()
        print("Geraete freigegeben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
