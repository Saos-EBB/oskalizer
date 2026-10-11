"""Was auf dem Schirm steht. Modus Tiere: ein Buchstabe mit Tier, eine Ziffer oder
ein Zeichen (Tafel). Modus Tippen: der getippte Text (Schreibtafel).
Kennt keine Geraete - bekommt nur evdev-Keycodes.
"""

import itertools
import json
import random
from pathlib import Path

import pygame
from evdev import ecodes

EMOJI_FONT = "/usr/share/fonts/google-noto-emoji-fonts/NotoEmoji-Regular.ttf"
FAMILIE = Path.home() / ".local" / "share" / "oskalizer" / "familie"
POP_SECONDS = 0.25                  # so lange waechst ein neues Zeichen auf volle Groesse

# Buchstabe -> Liste von Woertern (Tier oder Person) mit Name, Emoji, Laut und
# Lautschrift. Die Lautschrift ist nur fuer die Familien-Webseite. Hat ein Buchstabe
# mehrere Woerter, kommen sie der Reihe nach dran. Ä/Ö/Ü duerfen Schluessel sein.
# Die bunte Noto-Variante (COLRv1) zeichnet pygame leer, deshalb die einfarbige
# Schrift, eingefaerbt pro Tastendruck.
WOERTER = json.loads((Path(__file__).parent / "woerter.json").read_text(encoding="utf-8"))
_REIHE = {b: itertools.cycle(liste) for b, liste in WOERTER.items()}


def naechstes(zeichen):
    """Das naechste Wort fuer diesen Buchstaben, None fuer Ziffern/Zeichen."""
    return next(_REIHE[zeichen]) if zeichen in _REIHE else None


def ordner(wort):
    """Ordner eines Worts unter FAMILIE: "Tante Bär" -> "tante-baer"."""
    name = wort["name"].lower()
    for umlaut, ersatz in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), (" ", "-")):
        name = name.replace(umlaut, ersatz)
    return name


def person(path):
    """Wer eine Familien-Datei eingesprochen hat: "opa_2026-10-12.ogg" -> "Opa"."""
    return path.stem.split("_")[0].capitalize()


# evdev liefert die Tastenposition einer US-Tastatur. Hier das deutsche QWERTZ-Layout
# drauf, ohne Shift. Tasten, die hier fehlen, tun nichts.
ZEICHEN = {getattr(ecodes, f"KEY_{c}"): c for c in "ABCDEFGHIJKLMNOPQRSTUVWX"}
ZEICHEN[ecodes.KEY_Y] = "Z"
ZEICHEN[ecodes.KEY_Z] = "Y"
for d in "0123456789":
    ZEICHEN[getattr(ecodes, f"KEY_{d}")] = d
    ZEICHEN[getattr(ecodes, f"KEY_KP{d}")] = d
ZEICHEN.update({
    ecodes.KEY_MINUS: "ß", ecodes.KEY_EQUAL: "´", ecodes.KEY_LEFTBRACE: "Ü",
    ecodes.KEY_RIGHTBRACE: "+", ecodes.KEY_SEMICOLON: "Ö", ecodes.KEY_APOSTROPHE: "Ä",
    ecodes.KEY_GRAVE: "^", ecodes.KEY_BACKSLASH: "#", ecodes.KEY_102ND: "<",
    ecodes.KEY_COMMA: ",", ecodes.KEY_DOT: ".", ecodes.KEY_SLASH: "-",
    ecodes.KEY_KPPLUS: "+", ecodes.KEY_KPMINUS: "-", ecodes.KEY_KPASTERISK: "*",
    ecodes.KEY_KPSLASH: "/", ecodes.KEY_KPDOT: ",",
})


def ease_out(t):
    return 1.0 - (1.0 - t) ** 3


class Tafel:
    """Zeigt immer genau ein Zeichen. Jeder Tastendruck ersetzt es."""

    def __init__(self, screen):
        self.screen = screen
        height = screen.get_height()
        self.font = pygame.font.Font(None, int(height * 0.55))
        self.emoji_font = pygame.font.Font(EMOJI_FONT, int(height * 0.35))
        self.von_font = pygame.font.Font(None, height // 18)
        self.bilder = {}                    # Ordner -> Familien-Fotos statt Emoji
        for path in sorted(FAMILIE.glob("*/bild/*")):
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                bild = pygame.image.load(path).convert_alpha()
                size = (int(bild.get_width() * height * 0.4 / bild.get_height()),
                        int(height * 0.4))
                self.bilder.setdefault(path.parent.parent.name, []).append(
                    pygame.transform.smoothscale(bild, size))
        self.bild = None
        self.von = None                     # "[von Opa]" unten rechts
        self.since = 0.0

    def show(self, zeichen, wort, personen, now):
        """personen: wer die gerade gespielten Aufnahmen eingesprochen hat."""
        color = pygame.Color(0)
        color.hsva = (random.uniform(0.0, 360.0), 75.0, 100.0, 100.0)

        teile = [self.font.render(zeichen, True, color)]
        if wort and ordner(wort) in self.bilder:
            teile.append(random.choice(self.bilder[ordner(wort)]))  # eigene Farben
        elif wort and wort.get("emoji"):
            teile.append(self.emoji_font.render(wort["emoji"], True, color))

        gap = self.screen.get_height() // 12
        width = sum(t.get_width() for t in teile) + gap * (len(teile) - 1)
        height = max(t.get_height() for t in teile)
        self.bild = pygame.Surface((width, height), pygame.SRCALPHA)
        x = 0
        for teil in teile:
            self.bild.blit(teil, (x, (height - teil.get_height()) // 2))
            x += teil.get_width() + gap
        self.von = None
        if personen:
            text = f"[von {', '.join(dict.fromkeys(personen))}]"
            self.von = self.von_font.render(text, True, (150, 150, 175))
        self.since = now

    def draw(self, now):
        if self.bild is None:
            return
        t = min(1.0, (now - self.since) / POP_SECONDS)
        scale = 0.6 + 0.4 * ease_out(t)
        bild = self.bild
        if scale < 1.0:
            size = (int(bild.get_width() * scale), int(bild.get_height() * scale))
            bild = pygame.transform.smoothscale(bild, size)
        self.screen.blit(bild, bild.get_rect(center=self.screen.get_rect().center))
        if self.von:
            rand = self.screen.get_height() // 30
            self.screen.blit(self.von, self.von.get_rect(
                bottomright=(self.screen.get_width() - rand, self.screen.get_height() - rand)))


class Schreibtafel:
    """Tippen-Modus: die getippten Zeichen als Text, wortweise umgebrochen.
    Was oben aus dem Schirm laeuft, faellt auch aus dem Text."""

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, screen.get_height() // 6)
        self.text = ""
        self.zeilen = []
        self.vorgelesen = False             # nach Enter beginnt die naechste Taste neu

    def tippe(self, zeichen):
        if self.vorgelesen:
            self.text = ""
            self.vorgelesen = False
        self.text += zeichen
        self.zeilen = self._umbrechen()
        sichtbar = int(self.screen.get_height() * 0.9) // self.font.get_linesize()
        if len(self.zeilen) > sichtbar:
            self.zeilen = self.zeilen[-sichtbar:]
            self.text = " ".join(self.zeilen)

    def _umbrechen(self):
        breite = self.screen.get_width() * 0.9
        zeilen, zeile = [], ""
        for wort in self.text.split(" "):
            kandidat = f"{zeile} {wort}" if zeile else wort
            if self.font.size(kandidat)[0] <= breite:
                zeile = kandidat
                continue
            if zeile:
                zeilen.append(zeile)
            while self.font.size(wort)[0] > breite:     # Wort laenger als eine Zeile
                n = len(wort)
                while n > 1 and self.font.size(wort[:n])[0] > breite:
                    n -= 1
                zeilen.append(wort[:n])
                wort = wort[n:]
            zeile = wort
        zeilen.append(zeile)
        return zeilen

    def draw(self, now):
        line = self.font.get_linesize()
        top = (self.screen.get_height() - line * len(self.zeilen)) // 2
        for i, zeile in enumerate(self.zeilen):
            bild = self.font.render(zeile, True, (235, 235, 245))
            self.screen.blit(bild, bild.get_rect(midtop=(self.screen.get_width() // 2,
                                                        top + i * line)))
