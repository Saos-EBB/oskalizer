"""Was zu hoeren ist: Piper (Stimme Thorsten) spricht, espeak-ng springt ein, wenn
Piper oder die Stimme fehlt. Tondateien aus assets/toene/ ersetzen den gesprochenen
Tierlaut. Solange etwas klingt, meldet spricht() True - der Modus Tiere sperrt
dann die Tasten. Ein neuer Ton (Enter im Tippen-Modus) bricht den laufenden ab.
"""

import io
import queue
import random
import shutil
import subprocess
import sys
import threading
import wave
from pathlib import Path

import pygame

from tiere import TIERE

TOENE = Path(__file__).parent / "assets" / "toene"
PIPER_STIMME = Path.home() / ".local" / "share" / "oskalizer" / "de_DE-thorsten-high.onnx"
ESPEAK_ARGS = ["-v", "de", "-s", "140"]


def lade_piper():
    """PiperVoice oder None. Laden dauert ~1,6 s, deshalb nur einmal beim Start."""
    try:
        from piper import PiperVoice
    except ImportError:
        print("piper-tts fehlt - spreche mit espeak-ng.", file=sys.stderr)
        return None
    if not PIPER_STIMME.exists():
        print(f"Piper-Stimme fehlt ({PIPER_STIMME}) - spreche mit espeak-ng.",
              file=sys.stderr)
        return None
    return PiperVoice.load(str(PIPER_STIMME))


class Ton:
    def __init__(self):
        self.espeak = shutil.which("espeak-ng")
        self.dateien = {}                     # Buchstabe -> pygame.mixer.Sound
        self.stimme = None
        if pygame.mixer.get_init():
            for path in sorted(TOENE.glob("*")):
                if path.suffix in (".ogg", ".wav") and path.stem.upper() in TIERE:
                    self.dateien[path.stem.upper()] = pygame.mixer.Sound(path)
            self.stimme = lade_piper()        # Piper spielt ueber den Mixer
        else:
            print("Kein Audiogeraet - Tondateien bleiben stumm.", file=sys.stderr)
        if self.stimme is None and self.espeak is None:
            print("espeak-ng fehlt - es wird nichts gesprochen.", file=sys.stderr)

        self.sprecher = None                  # laufender espeak-Prozess
        self.kanal = None                     # Mixer-Kanal mit Piper-Sprache
        self.auftrag = 0                      # zaehlt pro Text hoch, Altes verfaellt
        self.rechnet = False                  # Piper-Thread fuer self.auftrag laeuft
        self.ergebnisse = queue.Queue()       # (auftrag, wav-Puffer) aus den Threads
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
        self._sprich(text)

    def sage(self, text):
        """Tippen-Modus: den ganzen Text vorlesen."""
        self.stop()
        self._sprich(text)

    def _sprich(self, text):
        if not text.strip():
            return
        if self.stimme:
            # Piper rechnet 0,2-1 s - im Thread, sonst steht das Bild
            self.auftrag += 1
            self.rechnet = True
            threading.Thread(target=self._rechne, args=(self.auftrag, text),
                             daemon=True).start()
        elif self.espeak:
            self.sprecher = subprocess.Popen(
                [self.espeak, *ESPEAK_ARGS, text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _rechne(self, auftrag, text):
        try:
            puffer = io.BytesIO()
            with wave.open(puffer, "wb") as wav:
                self.stimme.synthesize_wav(text, wav)
            puffer.seek(0)
        except Exception as exc:              # sonst bleibt die Tastensperre ewig
            print(f"Piper-Fehler: {exc}", file=sys.stderr)
            puffer = None
        self.ergebnisse.put((auftrag, puffer))

    def spricht(self):
        """True bis Sprache und nachfolgende Tondatei ganz durch sind."""
        return self.rechnet or self.danach is not None or self._klingt()

    def update(self):
        """Pro Frame: fertige Piper-Sprache abspielen, danach die Tondatei."""
        while not self.ergebnisse.empty():
            auftrag, puffer = self.ergebnisse.get()
            if self.rechnet and auftrag == self.auftrag:
                self.rechnet = False
                if puffer is not None:
                    self.kanal = pygame.mixer.Sound(file=puffer).play()
        if self.danach and not self.rechnet and not self._klingt():
            self.kanal = self.danach.play()
            self.danach = None

    def _klingt(self):
        return ((self.kanal is not None and self.kanal.get_busy())
                or (self.sprecher is not None and self.sprecher.poll() is None))

    def stop(self):
        if self.sprecher and self.sprecher.poll() is None:
            self.sprecher.kill()
        self.sprecher = None
        self.kanal = None
        self.rechnet = False                  # laufender Thread liefert ins Leere
        self.danach = None
        if pygame.mixer.get_init():
            pygame.mixer.stop()
