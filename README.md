# oskalizer

Keyboard playground für ein Kleinkind. Eine externe Tastatur (und optional die
Maus) werden exklusiv gegrabbt — das Kind hämmert, es passiert nur auf dem
Bildschirm etwas, das System bleibt unangetastet.

Jede Eingabe malt einen weichen, langsam ein- und ausfadenden Farbklecks.
Kein Zusammenhang zwischen Taste und Bild, kein Blitzen, keine Töne.

## Setup

```bash
sudo dnf install python3-evdev python3-pygame     # Fedora
# oder: pip install --user evdev pygame           # evdev braucht python3-devel
sudo usermod -aG input $USER                      # danach neu einloggen!
```

`/dev/input/*` gehört der Gruppe `input`. Ohne Mitgliedschaft (oder root) gibt
es eine Meldung statt eines Crashs.

## Konfigurieren

Oben in `oskalizer.py`:

```python
KEYBOARD_MATCH = "blackwidow"   # Teilstring im Geraetenamen, Gross-/Kleinschreibung egal
GRAB_MOUSE = True
```

Gerätenamen anzeigen:

```bash
python3 -c "import evdev; print([evdev.InputDevice(p).name for p in evdev.list_devices()])"
```

Razer-Tastaturen hängen **mehrere** `event*`-Nodes an denselben Namen (normale
Tasten + Media/Macro). Das Tool grabbt bewusst alle, die passen — sonst
rutschen Lautstärke- und Makrotasten am Grab vorbei auf den Desktop durch.
Die interne Laptop-Tastatur heißt anders und wird nicht angefasst.

## Starten und Beenden

```bash
python3 oskalizer.py
```

Beenden: **Esc 5 Sekunden am Stück halten.** Unten mittig läuft ein kleiner
Ring voll. Loslassen setzt den Timer zurück.

## Beim ersten Test bitte ein zweites Terminal offen haben

Solange das Tool läuft, ist die gegrabbte Tastatur für den Rest des Systems
tot. Falls der Esc-Exit klemmt, brauchst du einen zweiten Weg rein — per SSH
von einem anderen Rechner oder ein zweites TTY (Strg+Alt+F3, das geht am Grab
vorbei, weil es der Kernel behandelt):

```bash
kill <pid>          # SIGTERM: gibt alle Grabs frei und beendet sauber
```

`SIGTERM` und `SIGINT` sind abgefangen, die Freigabe der Geräte steht in einem
`finally` — auch bei einem Absturz werden die Grabs gelöst. Die PID steht beim
Start auf der Konsole. Die **interne** Laptop-Tastatur wird nie gegrabbt und
funktioniert die ganze Zeit weiter.

## Ruhig bleiben, auch beim Hämmern

- höchstens ~11 neue Kleckse pro Sekunde, schnellere Eingaben werden geschluckt
- 14 gleichzeitig aufblühende Kleckse; ältere werden sanft ausgeblendet, nicht
  hart gelöscht (kurzzeitig sind bis ~20 auf dem Schirm, inklusive der gehenden)
- additive Darstellung mit weichem Gesamt-Helligkeitsdeckel: gemessen bleibt
  der Helligkeitssprung zwischen zwei Bildern unter 0,1 von 255 — es flackert
  nichts, egal wie schnell getippt wird
- Mausbewegung spawnt erst nach ~250 px und höchstens alle 0,35 s

## Nicht eingebaut (bewusst)

- **Sound**: nur der leere Hook `play_sound(event)`, keine Audio-Bibliothek.
- Keine Config-GUI, keine Themes, keine Presets, keine Persistenz.
- Keine Kommandozeilenargumente — Einstellungen stehen im CONFIG-Block.
- Kein Auto-Reconnect: wird die Tastatur im Betrieb ausgesteckt, bitte beenden
  und neu starten.
- Geräte, deren Name `KEYBOARD_MATCH` enthält, werden auch dann gegrabbt, wenn
  es Maus-Nodes sind (`GRAB_MOUSE` steuert nur die *fremden* Zeigegeräte).
