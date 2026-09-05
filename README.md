# oskalizer

Keyboard playground für ein Kleinkind. Eine externe Tastatur (und optional die
Maus) werden exklusiv gegrabbt — das Kind hämmert, es passiert nur auf dem
Bildschirm etwas, das System bleibt unangetastet.

Jede Eingabe wirft Kleckse auf einen konstant dunklen Hintergrund. Kein
Zusammenhang zwischen Taste und Bild, kein Blitzen, keine Töne. Der Look kommt
1:1 aus dem Browser-Prototyp — gleiche Spawn-Formeln, gleiche Paletten.

Drei Dateien: `oskalizer.py` (Geräte, Schleife, Beenden), `visuals.py`
(Kleckse und die drei Stile), `devpanel.py` (Dev-Panel).

## Setup

```bash
sudo dnf install python3-evdev python3-pygame     # Fedora
sudo usermod -aG input $USER                      # danach neu einloggen!
```

`/dev/input/*` gehört der Gruppe `input`. Ohne Mitgliedschaft (oder root) gibt
es eine Meldung statt eines Crashs. `numpy` ist optional — nur der Stil `goo`
zieht damit den Kontrast nach; fehlt es, bleibt goo beim reinen Weichzeichner.

## Konfigurieren

Oben in `oskalizer.py`:

```python
KEYBOARD_MATCH = "blackwidow"   # Teilstring im Gerätenamen, Groß-/Kleinschreibung egal
GRAB_MOUSE     = True

STYLE   = "ink"        # "ink" | "orbs" | "goo"
PALETTE = "full_rgb"   # "full_rgb" | "neon" | "sunset" | "ocean" | "candy"
COUNT   = 1            # Kleckse pro Eingabe
SIZE    = 90           # Basisgröße
LIFE    = 2.2          # Sekunden
DRIFT   = 41           # Anfangsgeschwindigkeit-Streuung
MAX_BLOBS = 180
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
oskalizer            # Kurzbefehl, siehe unten
python3 oskalizer.py # oder direkt
```

Beenden: **Esc 5 Sekunden am Stück halten.** Unten mittig läuft ein kleiner
Ring voll. Loslassen setzt den Timer zurück. Esc spawnt dabei ganz normal
Kleckse mit.

## Kurzbefehl `oskalizer`

Liegt als `~/.local/bin/oskalizer` (nicht im Repo, weil der Pfad zum Rechner
gehört). Er springt für die Gruppe `input` ein, solange die aktuelle
Anmeldesitzung sie noch nicht kennt — nach `usermod` muss man sich sonst erst
neu anmelden:

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/home/saosgone/Schreibtisch/challangeMyMind/oskalizer/oskalizer.py

if id -nG | grep -qw input; then
    exec python3 "$APP"
elif id -nG "$USER" | grep -qw input; then
    exec sg input -c "python3 '$APP'"
else
    echo "Du bist nicht in der Gruppe 'input' - ohne die geht /dev/input nicht." >&2
    echo "  sudo usermod -aG input \$USER   (danach neu anmelden)" >&2
    exit 1
fi
```

## Beim ersten Test bitte ein zweites Terminal offen haben

Solange das Tool läuft, ist die gegrabbte Tastatur für den Rest des Systems
tot. Falls der Esc-Exit klemmt, brauchst du einen zweiten Weg rein — per SSH
von einem anderen Rechner oder ein zweites TTY:

```bash
kill <pid>          # SIGTERM: gibt alle Grabs frei und beendet sauber
```

`SIGTERM` und `SIGINT` sind abgefangen, die Freigabe der Geräte steht in einem
`finally` — auch bei einem Absturz werden die Grabs gelöst. Die PID steht beim
Start auf der Konsole. Die **interne** Laptop-Tastatur wird nie gegrabbt und
funktioniert die ganze Zeit weiter.

## Dev-Panel

**Strg+Umschalt+D** öffnet und schließt ein halbtransparentes Overlay oben
links. Solange es offen ist:

| Taste | Wirkung |
|---|---|
| Hoch / Runter | Parameter wählen |
| Links / Rechts | Wert ändern (STYLE und PALETTE schalten zyklisch durch) |
| P | aktuelle Werte als fertigen CONFIG-Block ins Terminal drucken |

Nur diese Tasten sind belegt — alle anderen Tasten und die Maus spawnen weiter,
damit man die Wirkung live sieht. Änderungen wirken sofort.

### Die Werte bleiben erhalten

Was im Panel gedreht wurde, überlebt den Neustart. Gespeichert wird nach
`~/.config/oskalizer/settings.json` (bzw. `$XDG_CONFIG_HOME`), und zwar

- beim Zuklappen des Panels und
- beim Beenden, auch bei offenem Panel und auch über `kill` (SIGTERM).

Geschrieben wird über eine temporäre Datei und `rename`, es kann also keine
halbe Datei entstehen.

**Vorrang:** existiert die Datei, gewinnt sie gegen den CONFIG-Block oben in
`oskalizer.py`. Zurück auf die Werte im Code kommt man durch Löschen:

```bash
rm ~/.config/oskalizer/settings.json
```

Beim Start steht auf der Konsole, ob und woher Einstellungen geladen wurden.
Unbrauchbare Einträge in der Datei (kaputtes JSON, unbekannter Stil, Zahlen
außerhalb der Grenzen) werden einzeln verworfen oder auf den erlaubten Bereich
gezogen — das Tool startet in jedem Fall. Nur die sechs Panel-Werte stehen in
der Datei; `MAX_BLOBS`, `KEYBOARD_MATCH` und der Rest bleiben Sache des
CONFIG-Blocks.

**P** druckt die aktuellen Werte weiterhin als fertigen CONFIG-Block ins
Terminal — praktisch, wenn man sie fest in den Code übernehmen will.

## Die drei Stile

- **ink** (Default): ein Ring wächst nach außen und verblasst, dahinter eine
  sehr blasse Füllung. Gezeichnet mit `pygame.gfxdraw` — kantengeglättet und
  normal alpha-geblendet.
- **orbs**: radialer Verlauf von der Mitte nach außen ins Transparente.
  Eingefärbt wird einmalig beim Spawn; pro Frame wird nur noch skaliert und die
  Deckkraft gesetzt. (Pro Frame einzufärben wäre rund sechsmal so teuer.)
- **goo**: weiche Kreise auf einer Viertelauflösung, weichgezeichnet und im
  Alphakanal hart nachgezogen, sodass benachbarte Kleckse verschmelzen.

## Ruhig bleiben, auch beim Hämmern

- höchstens ~11 Eingaben pro Sekunde lösen etwas aus, schnellere werden
  geschluckt statt aufgestaut (gemessen: 1000 Eingaben/s → 11 Kleckse)
- `MAX_BLOBS` wird hart eingehalten, älteste zuerst raus
- normales Alpha-Blending, **nicht** additiv
- der Hintergrund (`#0a0a12`) wird jedes Bild neu gezeichnet und nie geflutet

Gemessen bei 180 simulierten Anschlägen pro Sekunde über 15 Sekunden auf
1920×1080, mit den Defaults:

| Stil | Kleckse | Zeichnen p50 | mittlere Helligkeit | größter Sprung pro Bild |
|---|---|---|---|---|
| ink | 26 | 3,6 ms | 14/255 | 0,12/255 |
| orbs | 26 | 2,8 ms | 14/255 | 0,08/255 |
| goo | 25 | 4,5 ms | 25/255 | 1,34/255 |

Der Schirm bleibt also dunkel, und zwischen zwei Bildern ändert sich die
Helligkeit um Bruchteile eines Prozents. Da flackert nichts.

## Was das Dev-Panel an Bildrate kostet

`SIZE` geht quadratisch in die Zeichenkosten. Gemessen (ms pro Bild, p50,
1920×1080), Budget für 60 fps sind 16,6 ms:

| COUNT | SIZE | Kleckse | ink | orbs | goo |
|---|---|---|---|---|---|
| 1 | 90 | 23 | 3,0 | 2,6 | 4,6 |
| 1 | 180 | 24 | 8,9 | 7,7 | 4,8 |
| 1 | 300 | 23 | 25,0 | 16,0 | 5,3 |
| 4 | 90 | 81 | 11,2 | 7,3 | 5,0 |
| 12 | 90 | 180 | 21,8 | 17,1 | 5,5 |
| 12 | 300 | 180 | 169,0 | 145,1 | 13,3 |

Wer beim Rumprobieren SIZE oder COUNT weit hochdreht, sieht die Bildrate
einbrechen. Es ruckelt dann nicht, sondern alles wird langsamer (die Kleckse
bewegen sich pro *Bild*, nicht pro Sekunde) — einfach wieder runterdrehen.
`goo` bleibt als einziger Stil durchweg günstig, weil er auf Viertelauflösung
rechnet.

## Nicht eingebaut (bewusst)

- **Sound**: nur der leere Hook `play_sound(event)`, keine Audio-Bibliothek.
- Kleckse erscheinen an zufälligen Bildschirmstellen. Die Mausposition wird
  nicht mitgeführt — es soll ja gerade keinen Bezug zwischen Eingabe und Ort
  geben.
- `MAX_BLOBS` ist nicht im Panel drehbar (steht nicht in der Liste der
  tunebaren Werte) — nur im CONFIG-Block.
- Keine Kommandozeilenargumente, keine weiteren Paletten, keine Config-GUI
  außer dem Dev-Panel.
- Kein Auto-Reconnect: wird die Tastatur im Betrieb ausgesteckt, bitte beenden
  und neu starten.
- Geräte, deren Name `KEYBOARD_MATCH` enthält, werden auch dann gegrabbt, wenn
  es Maus-Nodes sind (`GRAB_MOUSE` steuert nur die *fremden* Zeigegeräte).
