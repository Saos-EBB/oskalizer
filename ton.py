"""Was zu hoeren ist: espeak-ng spricht, Tondateien aus assets/toene/ ersetzen den
gesprochenen Tierlaut. Jeder neue Tastendruck bricht den laufenden Ton ab.
"""

import random
import shutil
import subprocess
import sys
from pathlib import Path

import pygame

from tiere import TIERE

TOENE = Path(__file__).parent / "assets" / "toene"
ESPEAK_ARGS = ["-v", "de", "-s", "140"]


class Ton:
    def __init__(self):
        self.espeak = shutil.which("espeak-ng")
        if self.espeak is None:
            print("espeak-ng fehlt - es wird nichts gesprochen.", file=sys.stderr)
        self.dateien = {}                     # Buchstabe -> pygame.mixer.Sound
        if pygame.mixer.get_init():
            for path in sorted(TOENE.glob("*")):
                if path.suffix in (".ogg", ".wav") and path.stem.upper() in TIERE:
                    self.dateien[path.stem.upper()] = pygame.mixer.Sound(path)
        else:
            print("Kein Audiogeraet - Tondateien bleiben stumm.", file=sys.stderr)
        self.sprecher = None                  # laufender espeak-Prozess
        self.danach = None                    # Tondatei, die nach dem Sprechen kommt

    def play(self, zeichen):
        """Buchstabe: "A wie Affe", dann Tierlaut. Ziffer: die Zahl.
        Sonstiges Zeichen: Laut eines zufaelligen Tiers."""
        self.stop()
        tier = None
        if zeichen in TIERE:
            text, tier = f"{zeichen} wie {TIERE[zeichen][0]}.", zeichen
        elif zeichen.isdigit():
            text = zeichen
        else:
            text, tier = "", random.choice(list(TIERE))

        if tier in self.dateien:
            self.danach = self.dateien[tier]
        elif tier:
            text += " " + TIERE[tier][2]
        if text.strip() and self.espeak:
            self.sprecher = subprocess.Popen(
                [self.espeak, *ESPEAK_ARGS, text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def update(self):
        """Pro Frame: Tondatei starten, sobald das Sprechen vorbei ist."""
        if self.danach and (self.sprecher is None or self.sprecher.poll() is not None):
            self.danach.play()
            self.danach = None

    def stop(self):
        if self.sprecher and self.sprecher.poll() is None:
            self.sprecher.kill()
        self.sprecher = None
        self.danach = None
        if pygame.mixer.get_init():
            pygame.mixer.stop()
