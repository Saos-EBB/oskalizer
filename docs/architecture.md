# Architektur

## Überblick
Keyboard playground für ein Kleinkind. Eine externe Tastatur (per Namens-Teilstring)
und die Maus werden per evdev exklusiv gegrabbt, pygame zeigt Vollbild. Beenden nur
über 5 s Esc halten oder SIGTERM.

## Module
- `oskalizer.py` — CONFIG-Block, Geräte finden/grabben/freigeben, Hauptschleife
  (evdev per `select` lesen, Esc-Timer, zeichnen). `play_sound(event)` ist der Hook
  pro Tastendruck.

## Entscheidungen
- 2026-10-10 — Kleckse (`visuals.py`), Dev-Panel (`devpanel.py`) und gespeicherte
  Einstellungen gelöscht. Grund: die neue Version zeigt Buchstaben mit Tieren statt
  Klecksen; das Panel drehte nur Klecks-Parameter.
- Eingaben kommen nur über evdev, nicht über pygame — pygame sieht von gegrabbten
  Geräten nichts.
