"""Kleckse und die drei Zeichenstile. Kennt weder Geraete noch Tastatur.

Die Spawn-Mathematik ist 1:1 aus dem Browser-Prototyp uebernommen, inklusive
der Eigenheit, dass sich Kleckse pro *Frame* um vx/vy bewegen (nicht pro
Sekunde) - bei clock.tick(60) sieht das genauso aus wie im Original.
"""

import math
import random

import pygame
import pygame.gfxdraw

BACKGROUND = (10, 10, 18)          # #0a0a12, konstant, wird nie geflutet
STYLES = ("ink", "orbs", "goo")
PALETTE_NAMES = ("full_rgb", "neon", "sunset", "ocean", "candy")

_PALETTE_HEX = {
    "neon":   ["#ff3caf", "#7c4dff", "#00e5ff", "#18ffb0", "#ffe14d", "#ff5e3a"],
    "sunset": ["#ff6b6b", "#ffa94d", "#ffd93d", "#f76e9c", "#c15bff", "#ff4d6d"],
    "ocean":  ["#3ad1ff", "#4d7cff", "#7c4dff", "#18ffe0", "#5eead4", "#60a5fa"],
    "candy":  ["#ff9ecd", "#c4a1ff", "#a1e3ff", "#b8ffcf", "#fff3a1", "#ffb3c1"],
}
PALETTES = {name: [tuple(bytes.fromhex(h[1:])) for h in hexes]
            for name, hexes in _PALETTE_HEX.items()}

ORB_TEMPLATE_SIZE = 192            # begrenzt den Speicher pro Klecks (~150 KB)
GOO_SCALE = 4                      # Goo rechnet auf Viertelaufloesung
GOO_THRESHOLD = 90                 # ab hier wird Alpha hochgezogen
GOO_CONTRAST = 4


def ease_out(t):
    return 1.0 - (1.0 - t) ** 3


def pick_color(palette):
    """full_rgb: quer durchs Spektrum. Sonst zufaellig aus der Palettenliste."""
    if palette == "full_rgb":
        color = pygame.Color(0)
        color.hsva = (random.uniform(0.0, 360.0) % 360.0, 90.0, 100.0, 100.0)
        return (color.r, color.g, color.b)
    return random.choice(PALETTES[palette])


def _make_orb_template():
    """Radialer Verlauf Zentrum -> transparent, einmalig."""
    size = ORB_TEMPLATE_SIZE
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for radius in range(center, 0, -1):
        alpha = int(255 * (1.0 - radius / center) ** 1.6)
        pygame.draw.circle(surf, (255, 255, 255, alpha), (center, center), radius)
    return surf


_ORB_TEMPLATE = None


class Blob:
    """Ein Klecks. Alle Werte werden beim Spawn eingefroren."""

    def __init__(self, cfg, px, py):
        angle = random.uniform(0.0, math.tau)
        spread = random.random() * cfg.size * 0.4
        self.x = px + math.cos(angle) * spread
        self.y = py + math.sin(angle) * spread
        self.vx = (random.random() - 0.5) * cfg.drift / 20.0     # Pixel pro Frame
        self.vy = (random.random() - 0.5) * cfg.drift / 20.0
        self.r = cfg.size * (0.5 + random.random() * 0.7)
        self.life = max(0.1, cfg.life * (0.75 + random.random() * 0.5))
        self.color = pick_color(cfg.palette)
        self.age = 0.0
        self._orb = None                                          # erst bei Bedarf

    @property
    def t(self):
        return min(1.0, self.age / self.life)

    @property
    def dead(self):
        return self.age >= self.life

    def update(self, dt):
        self.age += dt
        self.x += self.vx
        self.y += self.vy

    def orb_surface(self):
        """Einmal beim ersten Zeichnen eingefaerbt - pro Frame einfaerben waere
        rund sechsmal so teuer wie das reine Skalieren."""
        global _ORB_TEMPLATE
        if self._orb is None:
            if _ORB_TEMPLATE is None:
                _ORB_TEMPLATE = _make_orb_template()
            size = max(4, min(ORB_TEMPLATE_SIZE, int(self.r * 1.2 * 2)))
            surf = pygame.transform.smoothscale(_ORB_TEMPLATE, (size, size))
            surf.fill((*self.color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._orb = surf
        return self._orb


# --- Stile -----------------------------------------------------------------


def draw_ink(screen, blobs):
    """Ring waechst nach aussen, dahinter eine sehr blasse Fuellung.
    gfxdraw zeichnet kantenglatt und blendet normal - genau was wir wollen."""
    for blob in blobs:
        t = blob.t
        alpha = ease_out(1.0 - t)
        rr = int(blob.r * (0.2 + ease_out(t) * 1.3))
        if rr < 1:
            continue
        x, y = int(blob.x), int(blob.y)
        fill = int(alpha * 0.15 * 255)
        ring = int(alpha * 0.8 * 255)
        if fill > 1:
            pygame.gfxdraw.filled_circle(screen, x, y, rr, (*blob.color, fill))
        if ring > 1:
            for d in (-1, 0, 1):                                  # Dicke ~3 px
                pygame.gfxdraw.aacircle(screen, x, y, rr + d, (*blob.color, ring))


def draw_orbs(screen, blobs):
    for blob in blobs:
        t = blob.t
        if t < 0.2:
            alpha = (t / 0.2) ** 2 * 0.9                          # ease-in bis 0.9
        else:
            alpha = 0.9 * (1.0 - ((t - 0.2) / 0.8) ** 3)          # ease-out auf 0
        rr = int(blob.r * (0.7 + ease_out(t) * 0.5))
        value = int(alpha * 255)
        if rr < 2 or value <= 1:
            continue
        surf = pygame.transform.scale(blob.orb_surface(), (rr * 2, rr * 2))
        surf.set_alpha(value)
        screen.blit(surf, (int(blob.x) - rr, int(blob.y) - rr))


def draw_goo(screen, blobs, scratch):
    """Weiche Kreise auf kleiner Offscreen-Flaeche, dann weichzeichnen und den
    Alphakanal hart nachziehen - dadurch fliessen benachbarte Kleckse zusammen."""
    scratch.fill((0, 0, 0, 0))
    sw, sh = scratch.get_size()
    for blob in blobs:
        t = blob.t
        alpha = int(ease_out(1.0 - t) * 0.9 * 255)
        rr = int(blob.r * (0.7 + ease_out(t) * 0.5)) // GOO_SCALE
        if rr < 1 or alpha <= 1:
            continue
        pygame.gfxdraw.filled_circle(scratch, int(blob.x) // GOO_SCALE,
                                     int(blob.y) // GOO_SCALE, rr,
                                     (*blob.color, alpha))
    blurred = pygame.transform.smoothscale(
        pygame.transform.smoothscale(scratch, (sw // 2, sh // 2)), (sw, sh))
    _boost_alpha(blurred)
    screen.blit(pygame.transform.smoothscale(blurred, screen.get_size()), (0, 0))


def _boost_alpha(surf):
    """Kontrast auf dem Alphakanal. Ohne numpy bleibt es beim reinen Weichzeichner
    (sieht dann diffuser aus, laeuft aber)."""
    try:
        import numpy
    except ImportError:
        return
    alpha = pygame.surfarray.pixels_alpha(surf)
    boosted = (alpha.astype(numpy.int16) - GOO_THRESHOLD) * GOO_CONTRAST
    alpha[:] = numpy.clip(boosted, 0, 255).astype(numpy.uint8)
    del alpha                                                     # Surface freigeben


# --- Feld ------------------------------------------------------------------


class Field:
    """Alle lebenden Kleckse plus Spawn-Regeln."""

    def __init__(self, screen, cfg):
        self.screen = screen
        self.cfg = cfg
        self.width, self.height = screen.get_size()
        self.blobs = []
        self.last_spawn = 0.0
        self.last_motion_spawn = 0.0
        self.motion_accum = 0.0
        self._goo_scratch = pygame.Surface(
            (self.width // GOO_SCALE, self.height // GOO_SCALE), pygame.SRCALPHA)

    def spawn(self, now):
        """Mash-Schutz: schnellere Eingaben als MIN_SPAWN_INTERVAL werden
        geschluckt statt aufgestaut."""
        if now - self.last_spawn < self.cfg.min_spawn_interval:
            return
        self.last_spawn = now

        px = random.uniform(0, self.width)          # abstrakt: keine Taste hat einen Ort
        py = random.uniform(0, self.height)
        for _ in range(self.cfg.count):
            self.blobs.append(Blob(self.cfg, px, py))

        overflow = len(self.blobs) - self.cfg.max_blobs
        if overflow > 0:
            del self.blobs[:overflow]               # aelteste zuerst

    def on_motion(self, distance, now):
        self.motion_accum += distance
        if self.motion_accum < self.cfg.motion_distance:
            return
        self.motion_accum = 0.0
        if now - self.last_motion_spawn < self.cfg.motion_spawn_interval:
            return
        self.last_motion_spawn = now
        self.spawn(now)

    def update(self, dt):
        for blob in self.blobs:
            blob.update(dt)
        self.blobs = [b for b in self.blobs if not b.dead]

    def draw(self):
        self.screen.fill(BACKGROUND)                # jedes Frame neu, kein Trail
        if self.cfg.style == "orbs":
            draw_orbs(self.screen, self.blobs)
        elif self.cfg.style == "goo":
            draw_goo(self.screen, self.blobs, self._goo_scratch)
        else:
            draw_ink(self.screen, self.blobs)
