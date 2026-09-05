"""Dev-Panel: Werte live drehen, Ergebnis per P als CONFIG-Block ausgeben.

Bedienung komplett ueber den gegrabbten Tastenstrom, weil pygame von der
gegrabbten Tastatur nichts mitbekommt.
"""

import pygame
from evdev import ecodes

import visuals

CTRL_KEYS = (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL)
SHIFT_KEYS = (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT)

# Anzeigename, Attribut, (min, max, Schritt) - None heisst zyklische Liste
FIELDS = [
    ("STYLE",   "style",   None),
    ("PALETTE", "palette", None),
    ("COUNT",   "count",   (1, 12, 1)),
    ("SIZE",    "size",    (20, 300, 5)),
    ("LIFE",    "life",    (0.4, 8.0, 0.2)),
    ("DRIFT",   "drift",   (0, 200, 5)),
]
CYCLES = {"style": visuals.STYLES, "palette": visuals.PALETTE_NAMES}

_ARROWS = (ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT)


class DevPanel:
    def __init__(self, cfg):
        self.cfg = cfg
        self.open = False
        self.selected = 0
        self.ctrl = False
        self.shift = False
        self._font = None
        self._bold = None

    # --- Eingabe ---

    def handle_key(self, code, value):
        """True = die Taste war Panel-Bedienung und spawnt keine Kleckse."""
        if code in CTRL_KEYS:
            self.ctrl = value != 0
            return False                        # Modifier bleiben normale Tasten
        if code in SHIFT_KEYS:
            self.shift = value != 0
            return False

        if code == ecodes.KEY_D and self.ctrl and self.shift:
            if value == 1:                      # nur beim Druck, kein Dauerfeuer
                self.open = not self.open
            return True
        if not self.open:
            return False

        if code in _ARROWS and value in (1, 2):     # Wiederholung darf durchlaufen
            if code == ecodes.KEY_UP:
                self.selected = (self.selected - 1) % len(FIELDS)
            elif code == ecodes.KEY_DOWN:
                self.selected = (self.selected + 1) % len(FIELDS)
            else:
                self._adjust(+1 if code == ecodes.KEY_RIGHT else -1)
            return True
        if code == ecodes.KEY_P:
            if value == 1:
                self.print_config()
            return True
        return code in _ARROWS                  # Loslassen der Pfeile schlucken

    def _adjust(self, direction):
        _, attr, span = FIELDS[self.selected]
        if span is None:
            options = CYCLES[attr]
            index = (options.index(getattr(self.cfg, attr)) + direction) % len(options)
            setattr(self.cfg, attr, options[index])
            return
        low, high, step = span
        value = getattr(self.cfg, attr) + direction * step
        value = round(min(high, max(low, value)), 2)
        setattr(self.cfg, attr, type(low)(value) if isinstance(low, int) else value)

    def print_config(self):
        print("\n# --- aktuelle Werte, direkt in den CONFIG-Block ---")
        for label, attr, _ in FIELDS:
            value = getattr(self.cfg, attr)
            shown = f'"{value}"' if isinstance(value, str) else value
            print(f"{label:<7} = {shown}")
        print(flush=True)

    # --- Anzeige ---

    def draw(self, screen):
        if not self.open:
            return
        if self._font is None:
            pygame.font.init()
            self._font = pygame.font.Font(None, 26)
            self._bold = pygame.font.Font(None, 26)
            self._bold.set_bold(True)

        rows = [(label, getattr(self.cfg, attr)) for label, attr, _ in FIELDS]
        width, line = 300, 30
        height = line * (len(rows) + 2) + 16
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((16, 16, 26, 215))
        pygame.draw.rect(panel, (90, 90, 120, 220), panel.get_rect(), 1)

        for i, (label, value) in enumerate(rows):
            y = 10 + i * line
            if i == self.selected:
                pygame.draw.rect(panel, (60, 60, 90, 200), (4, y - 3, width - 8, line - 2))
            shown = value if isinstance(value, str) else f"{value:g}"
            font = self._bold if i == self.selected else self._font
            panel.blit(font.render(label, True, (215, 215, 235)), (14, y))
            panel.blit(font.render(str(shown), True, (255, 255, 255)), (150, y))

        hint = self._font.render("Hoch/Runter  Links/Rechts  P=drucken", True, (140, 140, 165))
        panel.blit(hint, (14, 10 + len(rows) * line + 6))
        screen.blit(panel, (24, 24))
