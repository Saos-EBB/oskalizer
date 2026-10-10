"""Was auf dem Schirm steht: ein Buchstabe mit Tier, eine Ziffer oder ein Zeichen.
Kennt keine Geraete - bekommt nur evdev-Keycodes.
"""

import random

import pygame
from evdev import ecodes

EMOJI_FONT = "/usr/share/fonts/google-noto-emoji-fonts/NotoEmoji-Regular.ttf"
POP_SECONDS = 0.25                  # so lange waechst ein neues Zeichen auf volle Groesse

# Buchstabe -> (Tier, Emoji). Die bunte Noto-Variante (COLRv1) zeichnet pygame leer,
# deshalb die einfarbige Schrift, eingefaerbt pro Tastendruck.
TIERE = {
    "A": ("Affe", "🐒"),
    "B": ("Bär", "🐻"),
    "C": ("Chamäleon", "🦎"),
    "D": ("Delfin", "🐬"),
    "E": ("Elefant", "🐘"),
    "F": ("Frosch", "🐸"),
    "G": ("Giraffe", "🦒"),
    "H": ("Hund", "🐶"),
    "I": ("Igel", "🦔"),
    "J": ("Jaguar", "🐆"),
    "K": ("Katze", "🐱"),
    "L": ("Löwe", "🦁"),
    "M": ("Maus", "🐭"),
    "N": ("Nashorn", "🦏"),
    "O": ("Oktopus", "🐙"),
    "P": ("Pinguin", "🐧"),
    "Q": ("Qualle", "🪼"),
    "R": ("Raupe", "🐛"),
    "S": ("Schwein", "🐷"),
    "T": ("Tiger", "🐯"),
    "U": ("Uhu", "🦉"),
    "V": ("Vogel", "🐦"),
    "W": ("Wal", "🐳"),
    "X": ("Xerus", "🐿"),
    "Y": ("Yak", "🐃"),
    "Z": ("Zebra", "🦓"),
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
        self.bild = None
        self.since = 0.0

    def show(self, zeichen, now):
        color = pygame.Color(0)
        color.hsva = (random.uniform(0.0, 360.0), 75.0, 100.0, 100.0)

        teile = [self.font.render(zeichen, True, color)]
        if zeichen in TIERE:
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
