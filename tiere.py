"""Was auf dem Schirm steht: ein Buchstabe mit Tier, eine Ziffer oder ein Zeichen.
Kennt keine Geraete - bekommt nur evdev-Keycodes.
"""

import random
from pathlib import Path

import pygame
from evdev import ecodes

EMOJI_FONT = "/usr/share/fonts/google-noto-emoji-fonts/NotoEmoji-Regular.ttf"
BILDER = Path(__file__).parent / "assets" / "bilder"
POP_SECONDS = 0.25                  # so lange waechst ein neues Zeichen auf volle Groesse

# Buchstabe -> (Tier, Emoji, Laut). Den Laut spricht espeak-ng, solange keine
# Tondatei fuer den Buchstaben in assets/toene/ liegt (siehe ton.py).
# Die bunte Noto-Variante (COLRv1) zeichnet pygame leer, deshalb die einfarbige
# Schrift, eingefaerbt pro Tastendruck.
TIERE = {
    "A": ("Affe", "🐒", "Uh uh ah ah"),
    "B": ("Bär", "🐻", "Brummm"),
    "C": ("Chamäleon", "🦎", "Zisch"),
    "D": ("Delfin", "🐬", "Ki ki ki"),
    "E": ("Elefant", "🐘", "Törööö"),
    "F": ("Frosch", "🐸", "Quak quak"),
    "G": ("Giraffe", "🦒", "Mmmmh"),
    "H": ("Hund", "🐶", "Wau wau"),
    "I": ("Igel", "🦔", "Schnüff schnüff"),
    "J": ("Jaguar", "🐆", "Grrrr"),
    "K": ("Katze", "🐱", "Miau"),
    "L": ("Löwe", "🦁", "Rrroaaar"),
    "M": ("Maus", "🐭", "Piep piep"),
    "N": ("Nashorn", "🦏", "Schnaub"),
    "O": ("Oktopus", "🐙", "Blubb blubb"),
    "P": ("Pinguin", "🐧", "Quiek quiek"),
    "Q": ("Qualle", "🪼", "Blubb"),
    "R": ("Raupe", "🐛", "Mampf mampf"),
    "S": ("Schwein", "🐷", "Grunz grunz"),
    "T": ("Tiger", "🐯", "Grrraaa"),
    "U": ("Uhu", "🦉", "Uhu uhu"),
    "V": ("Vogel", "🐦", "Tschiep tschiep"),
    "W": ("Wal", "🐳", "Uuuuuuh"),
    "X": ("Xerus", "🐿", "Knabber knabber"),
    "Y": ("Yak", "🐃", "Muuuh"),
    "Z": ("Zebra", "🦓", "Ihahaha"),
}

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
        self.bilder = {}                    # Buchstabe -> eigenes Bild statt Emoji
        for path in sorted(BILDER.glob("*")):
            if path.suffix.lower() in (".png", ".jpg", ".jpeg") and path.stem.upper() in TIERE:
                bild = pygame.image.load(path).convert_alpha()
                size = (int(bild.get_width() * height * 0.4 / bild.get_height()),
                        int(height * 0.4))
                self.bilder[path.stem.upper()] = pygame.transform.smoothscale(bild, size)
        self.bild = None
        self.since = 0.0

    def show(self, zeichen, now):
        color = pygame.Color(0)
        color.hsva = (random.uniform(0.0, 360.0), 75.0, 100.0, 100.0)

        teile = [self.font.render(zeichen, True, color)]
        if zeichen in self.bilder:
            teile.append(self.bilder[zeichen])  # bleibt in seinen eigenen Farben
        elif zeichen in TIERE:
            teile.append(self.emoji_font.render(TIERE[zeichen][1], True, color))

        gap = self.screen.get_height() // 12
        width = sum(t.get_width() for t in teile) + gap * (len(teile) - 1)
        height = max(t.get_height() for t in teile)
        self.bild = pygame.Surface((width, height), pygame.SRCALPHA)
        x = 0
        for teil in teile:
            self.bild.blit(teil, (x, (height - teil.get_height()) // 2))
            x += teil.get_width() + gap
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
