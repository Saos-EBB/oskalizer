# Architektur

## Überblick
Keyboard playground für ein Kleinkind. Eine externe Tastatur (per Namens-Teilstring)
und die Maus werden per evdev exklusiv gegrabbt, pygame zeigt Vollbild. Beenden nur
über 5 s Esc halten oder SIGTERM.

## Module
- `oskalizer.py` — CONFIG-Block, Geräte finden/grabben/freigeben, Hauptschleife
  (evdev per `select` lesen, Esc-Timer, zeichnen). Pro Key-Down mit Zeichen:
  `Tafel.show()` und `Ton.play()`.
- `tiere.py` — Tier-Tabelle `TIERE` (Buchstabe → Name, Emoji), Tastenbelegung
  `ZEICHEN` (evdev-Keycode → Zeichen, QWERTZ) und `Tafel` (zeichnet das aktuelle
  Zeichen; lädt beim Start `assets/bilder/<buchstabe>.png|jpg` als Ersatz fürs Emoji).
  Kennt keine Geräte. `oskalizer.py` ruft `Tafel.show()` pro Key-Down und
  `Tafel.draw()` pro Frame.
- `ton.py` — `Ton`: startet `espeak-ng` als Subprozess, lädt `assets/toene/<buchstabe>.ogg|wav`
  per `pygame.mixer`. Liest `TIERE` aus `tiere.py`. `Ton.update()` pro Frame startet
  die Tondatei, sobald espeak fertig ist.

## Datenfluss
evdev-Keycode → `tiere.ZEICHEN` → Zeichen → `Tafel.show` (Bild) + `Ton.play` (espeak,
danach ggf. Datei). Ein neues Zeichen bricht Bild und Ton des vorigen ab.

## Entscheidungen
- 2026-10-10 — Tierlaute ohne Dateien als Lautmalerei über espeak-ng. Grund: es gibt
  noch keine Aufnahmen; Dateien in `assets/toene/` ersetzen den Laut pro Buchstabe.
- 2026-10-10 — Tondateien nach Buchstabe benannt (`a.ogg`), nicht nach Tiername.
  Grund: keine Umlaute in Dateinamen, Tier tauschen ohne Umbenennen.
- 2026-10-10 — Tiere als einfarbige Noto Emoji, pro Tastendruck eingefärbt. Grund:
  die bunte COLRv1-Schrift rendert in pygame/SDL_ttf leer.
- 2026-10-10 — Tastenbelegung fest auf QWERTZ im Code statt über XKB. evdev liefert
  nur Positionen, und es gibt genau eine Tastatur.
- 2026-10-10 — Kleckse (`visuals.py`), Dev-Panel (`devpanel.py`) und gespeicherte
  Einstellungen gelöscht. Grund: die neue Version zeigt Buchstaben mit Tieren statt
  Klecksen; das Panel drehte nur Klecks-Parameter.
- Eingaben kommen nur über evdev, nicht über pygame — pygame sieht von gegrabbten
  Geräten nichts.
