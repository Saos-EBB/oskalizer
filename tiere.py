"""Was auf dem Schirm steht. Modus Tiere: ein Buchstabe mit Tier, eine Ziffer oder
ein Zeichen (Tafel). Modus Tippen: der getippte Text (Schreibtafel). Modus Wirbel:
jedes Zeichen landet irgendwo auf dem Schirm und schwebt dort (Wirbeltafel).
Kennt keine Geraete - bekommt nur evdev-Keycodes.
"""

import itertools
import json
import math
import random
import subprocess
import threading
from pathlib import Path

import pygame
from evdev import ecodes

EMOJI_FONT = "/usr/share/fonts/google-noto-emoji-fonts/NotoEmoji-Regular.ttf"
FAMILIE = Path.home() / ".local" / "share" / "oskalizer" / "familie"
TIERE = Path.home() / ".local" / "share" / "oskalizer" / "tiere"   # CC0, von tiere_holen.py
CLIPS = Path.home() / ".local" / "share" / "oskalizer" / "clips"   # eigene, von clip_einsortieren.py
POP_SECONDS = 0.25                  # so lange waechst ein neues Zeichen auf volle Groesse
VIDEO_HOEHE = 0.45                  # Anteil der Bildschirmhoehe fuer ein Tiervideo

# Buchstabe -> Liste von Woertern (Tier oder Person) mit Name, Emoji, Laut und
# Lautschrift. Die Lautschrift ist nur fuer die Familien-Webseite. Hat ein Buchstabe
# mehrere Woerter, kommen sie der Reihe nach dran. Ä/Ö/Ü duerfen Schluessel sein.
# Die bunte Noto-Variante (COLRv1) zeichnet pygame leer, deshalb die einfarbige
# Schrift, eingefaerbt pro Tastendruck.
WOERTER = json.loads((Path(__file__).parent / "woerter.json").read_text(encoding="utf-8"))
PRIMAER_RUNDEN = 2                  # so oft Affe+Katze, bevor ein anderes Tier drankommt


def _reihe(liste):
    """Woerter mit "primaer" (pro Buchstabe eine Affen- und eine Katzenart, die mag
    das Kind am liebsten) kommen bevorzugt: PRIMAER_RUNDEN-mal alle primaeren, dann
    ein anderes Wort, dann wieder von vorn."""
    primaer = [w for w in liste if w.get("primaer")]
    andere = [w for w in liste if not w.get("primaer")]
    if not primaer or not andere:
        return liste
    folge = []
    for wort in andere:
        folge += primaer * PRIMAER_RUNDEN + [wort]
    return folge


_REIHE = {b: itertools.cycle(_reihe(liste)) for b, liste in WOERTER.items()}


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


class Film:
    """Spielt ein stummes Video einmal in Echtzeit ab. ffmpeg dekodiert in einem eigenen
    Prozess (pygame 2.6 kann kein Video), ein Thread liest die Einzelbilder, bild()
    holt das neueste. Am Ende bleibt das letzte Bild stehen."""

    def __init__(self, path, groesse):
        self.groesse = groesse
        breite, hoehe = groesse
        self.prozess = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-re", "-i", str(path), "-an", "-vf", f"scale={breite}:{hoehe}",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.neu = None                     # rohe Bytes des neuesten Bilds aus dem Thread
        self.letztes = None
        threading.Thread(target=self._lies, daemon=True).start()

    def _lies(self):
        laenge = self.groesse[0] * self.groesse[1] * 3
        while len(daten := self.prozess.stdout.read(laenge)) == laenge:
            self.neu = daten

    def bild(self):
        """Neuestes Bild oder None, solange noch keins da ist."""
        if self.neu is not None:
            self.letztes = pygame.image.frombuffer(self.neu, self.groesse, "RGB")
            self.neu = None
        return self.letztes

    def stop(self):
        if self.prozess.poll() is None:
            self.prozess.kill()
        self.prozess.wait()


class Tafel:
    """Zeigt immer genau ein Zeichen. Jeder Tastendruck ersetzt es."""

    def __init__(self, screen):
        self.screen = screen
        height = screen.get_height()
        self.font = pygame.font.Font(None, int(height * 0.55))
        self.emoji_font = pygame.font.Font(EMOJI_FONT, int(height * 0.35))
        self.von_font = pygame.font.Font(None, height // 18)
        # Ordner -> Fotos statt Emoji. Familien-Fotos gehen vor, sonst die CC0-Tierfotos.
        self.bilder = self._lade_bilder(FAMILIE, height)
        for name, liste in self._lade_bilder(TIERE, height).items():
            self.bilder.setdefault(name, liste)
        self.videos = {}                    # Ordner -> CC0-Videos, geladen erst beim Abspielen
        for path in sorted([*TIERE.glob("*/video/*.webm"), *CLIPS.glob("*/video/*.webm")]):
            self.videos.setdefault(path.parent.parent.name, []).append(path)
        self.groessen = {}                  # Video -> Groesse auf dem Schirm, per ffprobe
        self.teile = []                     # Buchstabe, dann Foto/Emoji (Surface) oder Film
        self.film = None
        self.von = None                     # "[von Opa]" unten rechts
        self.since = 0.0

    @staticmethod
    def _lade_bilder(wurzel, height):
        bilder = {}
        for path in sorted(wurzel.glob("*/bild/*")):
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                bild = pygame.image.load(path).convert_alpha()
                size = (int(bild.get_width() * height * 0.4 / bild.get_height()),
                        int(height * 0.4))
                bilder.setdefault(path.parent.parent.name, []).append(
                    pygame.transform.smoothscale(bild, size))
        return bilder

    def show(self, zeichen, wort, personen, now):
        """personen: wer die gerade gespielten Aufnahmen eingesprochen hat."""
        color = pygame.Color(0)
        color.hsva = (random.uniform(0.0, 360.0), 75.0, 100.0, 100.0)

        self.stop()
        self.teile = [self.font.render(zeichen, True, color)]
        familie = wort and any(FAMILIE.glob(f"{ordner(wort)}/bild/*"))
        if wort and ordner(wort) in self.videos and not familie:   # Familien-Foto geht vor
            path = random.choice(self.videos[ordner(wort)])
            self.film = Film(path, self._groesse(path))
            self.teile.append(self.film)
        elif wort and ordner(wort) in self.bilder:
            self.teile.append(random.choice(self.bilder[ordner(wort)]))  # eigene Farben
        elif wort and wort.get("emoji"):
            self.teile.append(self.emoji_font.render(wort["emoji"], True, color))
        self.von = None
        if personen:
            text = f"[von {', '.join(dict.fromkeys(personen))}]"
            self.von = self.von_font.render(text, True, (150, 150, 175))
        self.since = now

    def _groesse(self, path):
        """Videogroesse auf dem Schirm: VIDEO_HOEHE der Hoehe, Seitenverhaeltnis bleibt."""
        if path not in self.groessen:
            ausgabe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                 "stream=width,height", "-of", "csv=p=0", str(path)],
                capture_output=True, text=True).stdout
            breite, hoehe = (int(x) for x in ausgabe.strip().split(",")[:2])
            ziel = int(self.screen.get_height() * VIDEO_HOEHE) // 2 * 2
            self.groessen[path] = (int(breite * ziel / hoehe) // 2 * 2, ziel)
        return self.groessen[path]

    def stop(self):
        """Laufendes Video beenden (neue Taste, Moduswechsel, Ende)."""
        if self.film:
            self.film.stop()
            self.film = None

    def _bild(self):
        """Buchstabe und Tier nebeneinander. Mit Video jedes Frame neu, solange
        noch kein Videobild da ist, haelt eine leere Flaeche den Platz frei."""
        teile = []
        for teil in self.teile:
            if isinstance(teil, Film):
                teil = teil.bild() or pygame.Surface(teil.groesse, pygame.SRCALPHA)
            teile.append(teil)
        gap = self.screen.get_height() // 12
        width = sum(t.get_width() for t in teile) + gap * (len(teile) - 1)
        height = max(t.get_height() for t in teile)
        bild = pygame.Surface((width, height), pygame.SRCALPHA)
        x = 0
        for teil in teile:
            bild.blit(teil, (x, (height - teil.get_height()) // 2))
            x += teil.get_width() + gap
        return bild

    def draw(self, now):
        if not self.teile:
            return
        t = min(1.0, (now - self.since) / POP_SECONDS)
        scale = 0.6 + 0.4 * ease_out(t)
        bild = self._bild()
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

    def tippe(self, zeichen):
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


# Wirbel: wie "Let's talk now" auf kev.dev (src/contact/contact.ts). Jeder Buchstabe
# faellt von etwas weiter oben, leicht verdreht und unsichtbar, an seinen Platz
# (back.out(2.4), 1 s) und schwebt dann fuer sich auf und ab (sine, eigene Dauer
# und eigener Start). Ein Mausklick laesst ihn fallen: Schwerkraft, Abprallen, Stoss
# zwischen Buchstaben und Schubsen mit der Maus wie in src/contact/contact-physics.ts.
# Die Weiten auf kev.dev sind px bei ~1 em (100 px), hier in em.
WIRBEL_MAX = 30                     # mehr schwebende Buchstaben, dann blendet der aelteste aus
WIRBEL_HAUFEN_MAX = 60              # mehr gefallene, dann blendet der aelteste aus
WIRBEL_LANDEN = 1.0                 # s vom Erscheinen bis zum Landen
WIRBEL_AUS = 0.4                    # s Ausblenden
WIRBEL_UEBERSCHWINGEN = 2.4         # back.out(2.4)
# Physik pro Frame (60 fps), Weiten mal em/100 px
FALL_SCHWERKRAFT = 0.4
FALL_ABPRALL = 0.22                 # Energie, die pro Aufprall bleibt
FALL_LUFT = 0.018                   # Bremsen pro Frame in der Luft
FALL_BODEN_X = 0.9                  # Bremsen seitwaerts bei Bodenkontakt
FALL_BODEN_DREH = 0.85              # Bremsen der Drehung bei Bodenkontakt
FALL_MAUS_RADIUS = 0.75             # em: so nah muss die Maus kommen, um zu schubsen
FALL_BODEN_ABSTAND = 0.1            # em: Boden so weit ueber dem unteren Rand
FALL_STUBS = 12                     # Klick auf einen gefallenen: so stark nach oben
FALL_RUHIG = 0.6                    # weniger Weg pro Frame als das ...
FALL_EINSCHLAFEN = 30               # ... so viele Frames lang: liegt still
FALL_WECKEN = 2.0                   # so schnell muss ein anderer aufprallen, um ihn zu wecken


def back_out(t, c1=WIRBEL_UEBERSCHWINGEN):
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


class Wirbelbuchstabe:
    def __init__(self, bild, mitte, groesse, now):
        self.bild = bild
        self.mitte = mitte
        self.since = now
        self.weg = None                     # Zeitpunkt, ab dem er ausblendet
        self.radius = (bild.get_width() + bild.get_height()) / 4
        # Start (wird zu 0): y -46..-26 px, x +-6 px, Drehung +-12 Grad
        self.dy = random.uniform(-0.46, -0.26) * groesse
        self.dx = random.uniform(-0.06, 0.06) * groesse
        self.dreh = random.uniform(-12, 12)
        # Schweben: y +-5 px, Drehung +-3 Grad, 0.9-1.6 s, bis 1 s versetzt
        self.schwebe_y = random.uniform(-0.05, 0.05) * groesse
        self.schwebe_dreh = random.uniform(-3, 3)
        self.schwebe_dauer = random.uniform(0.9, 1.6)
        self.schwebe_start = random.uniform(0, 1)
        self.faellt = False                 # nach dem Klick: Physik statt Schweben
        self.x = self.y = self.winkel = 0.0
        self.vx = self.vy = self.dv = 0.0
        self.liegt = False
        self.ruhig = 0                      # Frames fast ohne Bewegung
        self.am_boden = self.beruehrt = False
        self.vorher = (0.0, 0.0)            # Lage vor dem letzten Physik-Schritt

    def lage(self, now):
        """(x, y, winkel, alpha) fuer diesen Frame."""
        if self.faellt:
            x, y, winkel, alpha = self.x, self.y, self.winkel, 1.0
        else:
            alter = now - self.since
            t = min(1.0, alter / WIRBEL_LANDEN)
            rest = 1 - back_out(t)          # 1 -> 0, schwingt kurz ueber
            x = self.mitte[0] + self.dx * rest
            y = self.mitte[1] + self.dy * rest
            winkel = self.dreh * rest
            alpha = max(0.0, min(1.0, back_out(t)))
            schwebe = alter - WIRBEL_LANDEN - self.schwebe_start
            if schwebe > 0:                 # sine.inOut mit yoyo
                p = (1 - math.cos(math.pi * schwebe / self.schwebe_dauer)) / 2
                y += self.schwebe_y * p
                winkel += self.schwebe_dreh * p
        if self.weg is not None:
            alpha *= max(0.0, 1 - (now - self.weg) / WIRBEL_AUS)
        return x, y, winkel, alpha

    def trifft(self, punkt, now):
        x, y, _, _ = self.lage(now)
        return (abs(punkt[0] - x) <= self.bild.get_width() / 2
                and abs(punkt[1] - y) <= self.bild.get_height() / 2)

    def loslassen(self, now, k):
        """Vom Schweben in die Physik, mit einem kleinen Schubs (wie auf kev.dev)."""
        self.x, self.y, self.winkel, _ = self.lage(now)
        self.faellt = True
        self.vx = random.uniform(-3, 3) * k
        self.vy = random.uniform(2, 6) * k
        self.dv = random.uniform(-5, 5)

    def draw(self, screen, now):
        x, y, winkel, alpha = self.lage(now)
        bild = pygame.transform.rotozoom(self.bild, -winkel, 1.0)
        bild.set_alpha(int(255 * alpha))
        screen.blit(bild, bild.get_rect(center=(int(x), int(y))))

    def fertig(self, now):
        return self.weg is not None and now - self.weg >= WIRBEL_AUS


def _ausmass(b):
    """Halbe Breite/Hoehe des gedrehten Buchstabens."""
    w, h = b.bild.get_size()
    c, s = abs(math.cos(math.radians(b.winkel))), abs(math.sin(math.radians(b.winkel)))
    return (w * c + h * s) / 2, (w * s + h * c) / 2


def _physik(koerper, breite, boden, k):
    """Ein Frame: Schwerkraft, Waende, Boden, dann Stoesse untereinander. Wer eine
    halbe Sekunde fast still ist, schlaeft (liegt) und bewegt sich erst wieder, wenn
    ihn etwas kraeftig trifft, die Maus schubst oder nichts mehr unter ihm ist."""
    for b in koerper:
        b.am_boden = False
        b.vorher = (b.x, b.y)
        if b.liegt:
            b.am_boden = b.y + _ausmass(b)[1] >= boden - 2
            continue
        b.vx *= 1 - FALL_LUFT
        b.vy *= 1 - FALL_LUFT
        b.dv *= 1 - FALL_LUFT
        b.vy += FALL_SCHWERKRAFT * k
        b.x += b.vx
        b.y += b.vy
        b.winkel += b.dv
        halb_b, halb_h = _ausmass(b)
        if b.x < halb_b:
            b.x, b.vx, b.dv = halb_b, abs(b.vx) * FALL_ABPRALL, b.dv * -0.7
        if b.x > breite - halb_b:
            b.x, b.vx, b.dv = breite - halb_b, -abs(b.vx) * FALL_ABPRALL, b.dv * -0.7
        if b.y > boden - halb_h:
            b.am_boden = True
            b.y = boden - halb_h
            b.vy = -abs(b.vy) * FALL_ABPRALL
            b.vx *= FALL_BODEN_X
            b.dv *= FALL_BODEN_DREH

    for b in koerper:
        b.beruehrt = False
    for i, a in enumerate(koerper):
        for b in koerper[i + 1:]:
            dx, dy = b.x - a.x, b.y - a.y
            dist = math.hypot(dx, dy) or 0.0001
            min_d = a.radius + b.radius
            if dist >= min_d + 2:
                continue
            a.beruehrt = b.beruehrt = True
            if dist >= min_d or (a.liegt and b.liegt):
                continue
            nx, ny = dx / dist, dy / dist
            ueber = min_d - dist
            dot = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny      # < 0: aufeinander zu
            if (a.liegt or b.liegt) and -dot > FALL_WECKEN * k:
                a.liegt = b.liegt = False                     # kraeftig getroffen
            if a.liegt:                     # a steht fest, nur b weicht
                b.x += nx * ueber
                b.y += ny * ueber
                if dot < 0:
                    b.vx -= dot * (1 + FALL_ABPRALL) * nx
                    b.vy -= dot * (1 + FALL_ABPRALL) * ny
            elif b.liegt:
                a.x -= nx * ueber
                a.y -= ny * ueber
                if dot < 0:
                    a.vx += dot * (1 + FALL_ABPRALL) * nx
                    a.vy += dot * (1 + FALL_ABPRALL) * ny
            else:
                a.x -= nx * ueber / 2
                a.y -= ny * ueber / 2
                b.x += nx * ueber / 2
                b.y += ny * ueber / 2
                if dot < 0:
                    stoss = -dot * (1 + FALL_ABPRALL) / 2
                    a.vx -= stoss * nx
                    a.vy -= stoss * ny
                    b.vx += stoss * nx
                    b.vy += stoss * ny

    for b in koerper:
        if not b.liegt:                     # Stoesse duerfen nicht durch Boden/Wand druecken
            halb_b, halb_h = _ausmass(b)
            b.x = min(max(b.x, halb_b), breite - halb_b)
            if b.y > boden - halb_h:
                b.y = boden - halb_h
                b.vy = min(b.vy, 0.0)
                b.am_boden = True
        if b.liegt:
            if not b.am_boden and not b.beruehrt:
                b.liegt = False             # Unterlage ist weg
                b.ruhig = 0
            continue
        if math.dist(b.vorher, (b.x, b.y)) < FALL_RUHIG * k and abs(b.dv) < 1:
            b.ruhig += 1
        else:
            b.ruhig = 0
        if b.ruhig > FALL_EINSCHLAFEN and (b.am_boden or b.beruehrt):
            b.vx = b.vy = b.dv = 0.0
            b.liegt = True


def _schubsen(koerper, maus, dx, dy, radius):
    """Wer nah an der Maus ist, wird mit ihrer Geschwindigkeit weggeschubst."""
    tempo = math.hypot(dx, dy)
    if tempo < 0.5:
        return
    for b in koerper:
        ax, ay = b.x - maus[0], b.y - maus[1]
        dist = math.hypot(ax, ay) or 1
        if dist >= radius:
            continue
        kraft = tempo * 0.3
        b.vx += ax / dist * kraft
        b.vy += ay / dist * kraft
        b.dv += random.uniform(-0.5, 0.5) * kraft * 0.3
        b.liegt = False


def _zeiger(hoehe):
    """Pfeil-Mauszeiger, weiss mit dunklem Rand. pygame sieht die Maus nicht (gegrabbt)."""
    s = hoehe / 28 / 19
    punkte = [(2 + x * s, 2 + y * s) for x, y in [(0, 0), (0, 16), (4, 12), (7, 19),
                                                    (10, 18), (7, 11), (12, 11)]]
    bild = pygame.Surface((int(13 * s) + 5, int(20 * s) + 5), pygame.SRCALPHA)
    pygame.draw.polygon(bild, (250, 250, 255), punkte)
    pygame.draw.polygon(bild, (10, 10, 18), punkte, max(2, int(s)))
    return bild


class Wirbeltafel:
    """Wirbel-Modus: jedes Zeichen bekommt einen freien Platz irgendwo auf dem Schirm,
    faellt dort ein und bleibt schwebend stehen. Ein Mausklick laesst es fallen, unten
    waechst ein Haufen, in dem die Maus herumschubst. Mauszeiger wird selbst gezeichnet."""

    def __init__(self, screen):
        self.screen = screen
        self.groesse = screen.get_height() // 5
        self.k = self.groesse / 100         # kev.dev-px -> hier
        self.font = pygame.font.Font(None, self.groesse)
        self.buchstaben = []
        self.maus = [screen.get_width() / 2, screen.get_height() / 2]
        self.maus_weg = [0.0, 0.0]          # Bewegung seit dem letzten Frame
        self.zeiger = _zeiger(screen.get_height())

    def _platz(self):
        """Zufaelliger Platz, moeglichst weit weg von den anderen."""
        breite, hoehe = self.screen.get_size()
        rand = self.groesse * 0.6
        abstand = self.groesse * 0.9
        platz = None
        for _ in range(40):
            platz = (random.uniform(rand, breite - rand), random.uniform(rand, hoehe - rand))
            if all(math.dist(platz, b.mitte) >= abstand
                   for b in self.buchstaben if b.weg is None and not b.faellt):
                break
        return platz

    def _begrenzen(self, now, fallend, hoechstens):
        lebend = [b for b in self.buchstaben if b.weg is None and b.faellt == fallend]
        for b in lebend[:max(0, len(lebend) - hoechstens)]:
            b.weg = now

    def tippe(self, zeichen, now):
        color = pygame.Color(0)
        color.hsva = (random.uniform(0.0, 360.0), 75.0, 100.0, 100.0)
        bild = self.font.render(zeichen, True, color)
        bild = bild.subsurface(bild.get_bounding_rect()).copy()   # nur der Buchstabe
        self.buchstaben.append(Wirbelbuchstabe(bild, self._platz(), self.groesse, now))
        self._begrenzen(now, False, WIRBEL_MAX)

    def bewege(self, dx, dy):
        breite, hoehe = self.screen.get_size()
        self.maus[0] = min(max(0.0, self.maus[0] + dx), breite - 1)
        self.maus[1] = min(max(0.0, self.maus[1] + dy), hoehe - 1)
        self.maus_weg[0] += dx
        self.maus_weg[1] += dy

    def klick(self, now):
        """Schwebender Buchstabe unter der Maus faellt, ein gefallener huepft hoch."""
        for b in reversed(self.buchstaben):             # der oberste zuerst
            if b.weg is None and b.trifft(self.maus, now):
                if b.faellt:
                    b.vy = -FALL_STUBS * self.k
                    b.vx += random.uniform(-3, 3) * self.k
                    b.dv += random.uniform(-6, 6)
                    b.liegt = False
                else:
                    b.loslassen(now, self.k)
                    self._begrenzen(now, True, WIRBEL_HAUFEN_MAX)
                return

    def draw(self, now):
        self.buchstaben = [b for b in self.buchstaben if not b.fertig(now)]
        koerper = [b for b in self.buchstaben if b.faellt]
        breite, hoehe = self.screen.get_size()
        _schubsen(koerper, self.maus, *self.maus_weg, FALL_MAUS_RADIUS * self.groesse)
        self.maus_weg = [0.0, 0.0]
        _physik(koerper, breite, hoehe - FALL_BODEN_ABSTAND * self.groesse, self.k)
        for b in self.buchstaben:
            b.draw(self.screen, now)
        self.screen.blit(self.zeiger, (int(self.maus[0]) - 2, int(self.maus[1]) - 2))
