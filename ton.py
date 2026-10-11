"""Was zu hoeren ist: Piper (Stimme Thorsten) spricht, espeak-ng springt ein, wenn
Piper oder die Stimme fehlt. Familien-Aufnahmen (FAMILIE/<wort>/name|laut/) ersetzen
den Satz "A wie Affe" bzw. den Laut, bei mehreren zufaellig eine. Solange etwas klingt, meldet spricht() True - der Modus Tiere sperrt
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

from tiere import FAMILIE, WOERTER, ordner, person

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
        self.aufnahmen = {}                   # (Ordner, "name"|"laut") -> [(Person, Sound)]
        self.stimme = None
        if pygame.mixer.get_init():
            for path in sorted(FAMILIE.glob("*/*/*")):
                slot = path.parent.name
                if slot in ("name", "laut") and path.suffix.lower() in (".ogg", ".wav"):
                    self.aufnahmen.setdefault((path.parent.parent.name, slot), []).append(
                        (person(path), pygame.mixer.Sound(path)))
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
        self.reihe = []                       # was noch kommt: Text (str) oder Sound

    def play(self, zeichen, wort):
        """Buchstabe: "A wie Affe", dann der Laut des Worts. Ziffer: die Zahl.
        Sonstiges Zeichen: Laut eines zufaelligen Worts.
        Gibt zurueck, von wem die gespielten Familien-Aufnahmen sind."""
        self.stop()
        if wort is None and zeichen.isdigit():
            self.reihe = [zeichen]
            return []
        teile = []
        if wort is None:
            wort = random.choice([w for liste in WOERTER.values() for w in liste])
        else:
            teile.append(self._aufnahme(wort, "name") or f"{zeichen} wie {wort['name']}.")
        teile.append(self._aufnahme(wort, "laut") or wort["laut"])

        personen = []
        for teil in teile:
            if isinstance(teil, str):
                if self.reihe and isinstance(self.reihe[-1], str):
                    self.reihe[-1] += " " + teil      # ein Piper-Auftrag, keine Pause
                else:
                    self.reihe.append(teil)
            else:
                personen.append(teil[0])
                self.reihe.append(teil[1])
        return personen

    def _aufnahme(self, wort, slot):
        """Zufaellige Familien-Aufnahme (Person, Sound) oder None."""
        liste = self.aufnahmen.get((ordner(wort), slot))
        return random.choice(liste) if liste else None

    def sage(self, text):
        """Tippen-Modus: den ganzen Text vorlesen."""
        self.stop()
        self.reihe = [text]

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
        """True bis die ganze Reihe durch ist."""
        return self.rechnet or bool(self.reihe) or self._klingt()

    def update(self):
        """Pro Frame: fertige Piper-Sprache abspielen, dann das Naechste der Reihe."""
        while not self.ergebnisse.empty():
            auftrag, puffer = self.ergebnisse.get()
            if self.rechnet and auftrag == self.auftrag:
                self.rechnet = False
                if puffer is not None:
                    self.kanal = pygame.mixer.Sound(file=puffer).play()
        if self.reihe and not self.rechnet and not self._klingt():
            teil = self.reihe.pop(0)
            if isinstance(teil, str):
                self._sprich(teil)
            else:
                self.kanal = teil.play()

    def _klingt(self):
        return ((self.kanal is not None and self.kanal.get_busy())
                or (self.sprecher is not None and self.sprecher.poll() is None))

    def stop(self):
        if self.sprecher and self.sprecher.poll() is None:
            self.sprecher.kill()
        self.sprecher = None
        self.kanal = None
        self.rechnet = False                  # laufender Thread liefert ins Leere
        self.reihe = []
        if pygame.mixer.get_init():
            pygame.mixer.stop()
