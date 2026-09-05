# oskalizer

Keyboard playground für ein Kleinkind. Eine externe Tastatur (und optional die
Maus) werden exklusiv gegrabbt — das Kind hämmert, es passiert nur auf dem
Bildschirm etwas, das System bleibt unangetastet.

Jede Eingabe wirft 3–6 Farbkleckse in einer lockeren Wolke auf den Schirm:
klare, gefüllte Kreise mit sauberer Kante, zufällig aus dem gesamten
Farbspektrum, satt und hell. Die Ruhe kommt nicht aus verwaschenen Rändern,
sondern aus dem langsamen Ein- und Ausblenden (1,5–3 s) und sanftem Treiben.
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

- höchstens ~11 Eingaben pro Sekunde lösen etwas aus, schnellere werden
  geschluckt statt aufgestaut
- höchstens 150 Kleckse gleichzeitig; ist es voll, wird der älteste sanft
  ausgeblendet statt hart gelöscht
- normales Alpha-Blending, **nicht** additiv — satte Farben bleiben satt und
  laufen auch beim Übereinanderliegen nie nach Weiß aus
- der Hintergrund wird jedes Bild neu in konstantem Dunkelgrau gezeichnet und
  nie geflutet

Gemessen bei 180 simulierten Anschlägen pro Sekunde über 15 Sekunden
(1920×1080): maximal 118 gleichzeitige Kleckse, mittlere Bildhelligkeit
17 von 255, größter Helligkeitssprung zwischen zwei aufeinanderfolgenden
Bildern **0,15 von 255**. Da leuchtet nichts auf und da flackert nichts.

## Nicht eingebaut (bewusst)

- **Sound**: nur der leere Hook `play_sound(event)`, keine Audio-Bibliothek.
- Keine Config-GUI, keine Themes, keine Presets, keine Persistenz.
- Keine Kommandozeilenargumente — Einstellungen stehen im CONFIG-Block.
- Kein Wachsen der Kleckse: sie treiben langsam, ändern aber ihre Größe nicht
  (jedes Bild neu zu skalieren wäre bei 150 Stück unnötig teuer).
- Kein Auto-Reconnect: wird die Tastatur im Betrieb ausgesteckt, bitte beenden
  und neu starten.
- Geräte, deren Name `KEYBOARD_MATCH` enthält, werden auch dann gegrabbt, wenn
  es Maus-Nodes sind (`GRAB_MOUSE` steuert nur die *fremden* Zeigegeräte).
