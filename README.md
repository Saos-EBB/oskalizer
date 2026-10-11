# oskalizer

Keyboard playground für ein Kleinkind. Eine externe Tastatur (und optional die
Maus) werden exklusiv gegrabbt — das Kind hämmert, es passiert nur auf dem
Bildschirm etwas, das System bleibt unangetastet.

Jeder Tastendruck zeigt groß ein Zeichen in der Bildschirmmitte, in einer
zufälligen Farbe, kurz aufpoppend. Die nächste Taste ersetzt es:

- **A–Z**: Buchstabe plus ein Tier dazu (A Affe, B Bär, … Z Zebra)
- **Ziffern** (oben und Nummernblock): die Zahl
- **Zeichen** (`ß ´ Ü + Ö Ä ^ # < , . -` und die Nummernblock-Operatoren): das Zeichen

Dazu kommt Ton. Es spricht **Piper** mit der Stimme *Thorsten (high)*; fehlt
Piper oder die Stimmdatei, springt `espeak-ng` ein (Roboterstimme):

- **A–Z**: „A wie Affe“, danach der Tierlaut („Uh uh ah ah“)
- **Ziffern**: die Zahl wird gesagt
- **Zeichen**: der Laut eines zufälligen Tiers

Solange der Ton läuft (Sprache plus ggf. Tondatei), sind die Zeichentasten
**gesperrt** — gedrückte Tasten verfallen, damit Hämmern keinen Ton-Spam macht.
Esc (Beenden) und Strg+Umschalt+D (Modus) gehen weiterhin.

### Wörter

Die Tiere (Name, Emoji, Laut, Lautschrift) stehen in `woerter.json`. Ein
Buchstabe kann mehrere Einträge haben, z.B. O: Oktopus und Opa. Die kommen dann
der Reihe nach dran. Ä, Ö und Ü dürfen auch Einträge bekommen. Ein Eintrag ohne
`emoji` (z.B. eine Person) braucht ein Foto, sonst steht nur der Buchstabe da.

### Familien-Aufnahmen

Eigene Aufnahmen und Fotos liegen **außerhalb des Repos** unter
`~/.local/share/oskalizer/familie/`, ein Ordner pro Wort (Name klein, Umlaute als
ae/oe/ue, ß als ss, Leerzeichen als `-`):

```
familie/
  affe/name/opa_2026-10-12.ogg    ersetzt den ganzen Satz „A wie Affe“
  affe/laut/oma_2026-10-12.ogg    ersetzt den Laut
  opa/bild/papa_2026-10-12.png    Foto statt Emoji
```

Der Teil vor dem ersten `_` ist die Person: Bei einer Aufnahme steht dann unten
rechts „[von Opa]“. Liegen in einem Slot mehrere Dateien, wird pro Tastendruck
zufällig eine gewählt. Ton nur als OGG/WAV. Andere Formate vorher umwandeln:
`ffmpeg -i in.m4a -af "silenceremove=1:0:-50dB,loudnorm" out.ogg`. Fotos werden
auf 40 % der Bildschirmhöhe skaliert. PNG mit transparentem Hintergrund sieht
auf dem dunklen Schirm am besten aus. Geladen wird alles beim Start.

Leertaste, Enter, F-Tasten, Shift, Esc und die Maus zeigen nichts. Shift wird
nicht ausgewertet — es gibt nur Großbuchstaben und die ungeshifteten Zeichen.
Die Tastenbelegung ist auf ein deutsches QWERTZ-Layout festgelegt.

## Modus Tippen

**Strg+Umschalt+D** schaltet zwischen den Modi „Tiere“ (Start) und „Tippen“ um.
Im Tippen-Modus erscheint jedes getippte Zeichen als Text in der Mitte, die
Leertaste macht Wortabstände. Keine Tiere, kein Ton pro Taste. Zu langer Text
wird umgebrochen; was oben aus dem Bildschirm läuft, ist weg. Es gibt keine
Rücktaste und weiterhin nur Großbuchstaben. Beim Wechsel bleibt der Text des
Tippen-Modus stehen.

**Enter** (auch auf dem Nummernblock) lässt den Text vorlesen. Der
Text bleibt danach stehen; die nächste Taste fängt einen neuen an. Enter
während des Vorlesens fängt von vorn an.

Drei Dateien: `oskalizer.py` (Geräte, Schleife, Beenden), `tiere.py` (lädt
`woerter.json`, Tastenbelegung, Anzeige), `ton.py` (Sprechen und Tondateien).

## Familien-Webseite (`web/`)

Über die Seite spricht die Familie Wörter und Laute ein. Sie zeigt nur ein
Passwortfeld. Jede Person hat ein eigenes Passwort, daher weiß die Seite, wer
es ist. Bei einem falschen Passwort zählt sie stumm 3-2-1 herunter.

Hosting auf Vercel: Projekt aus diesem Repo anlegen, **Root Directory `web`**,
dann unter *Settings → Environment Variables* alle Werte aus `web/.env.example`
eintragen. Für lokal kopierst du `web/.env.example` nach `web/.env` (steht in der
`.gitignore`) und startest in `web/` mit `npm install && npm run build && npx vercel dev`.
`npm run build` kopiert `woerter.json` in die Seite.

Nach dem Login zeigt die Seite alle Wörter. Pro Wort gibt's zwei Knöpfe: **Name**
(den ganzen Satz „A wie Affe“ einsprechen) und **Laut**. Eine Aufnahme dauert
höchstens 15 s, man kann sie anhören, neu aufnehmen und dann senden. Jede
Aufnahme kommt als Mail an `MAIL_TO`. Im Mailtext steht der fertige Befehl, der
sie umwandelt und in den Familien-Ordner legt.

**+ Neues Wort**: Name, Foto und ein Laut sind Pflicht. Das kann ein Tier sein,
aber auch „Opa“ mit dem, was Opa so sagt. Das Foto wird im Browser auf 1024 px
verkleinert. Das Wort kommt auf die Taste seines ersten Buchstabens, auch Ä/Ö/Ü.
Die Mail enthält die Zeile für `woerter.json` und die Befehle zum Ablegen. Das
Foto stellt `freistellen.py` frei, als PNG mit transparentem Hintergrund. Das
braucht einmalig `python3 -m pip install --user rembg`. Beim ersten Lauf lädt es
das Modell u2net (~170 MB) nach `~/.rembg/models/`.

- Person dazu: `FAMILY_PASSWORDS` ergänzen, neu deployen.
- Person raus: Eintrag löschen, neu deployen. Ihr Cookie gilt dann auch nicht mehr.

## Setup

```bash
sudo dnf install python3-evdev python3-pygame google-noto-emoji-fonts espeak-ng   # Fedora
sudo usermod -aG input $USER                      # danach neu einloggen!
```

`/dev/input/*` gehört der Gruppe `input`. Ohne Mitgliedschaft (oder root) gibt
es eine Meldung statt eines Crashs.

Die Stimme (114 MB) liegt nicht im Repo:

```bash
python3 -m pip install --user piper-tts
mkdir -p ~/.local/share/oskalizer
python3 -m piper.download_voices --data-dir ~/.local/share/oskalizer de_DE-thorsten-high
```

Der Pfad steht oben in `ton.py` (`PIPER_STIMME`). Laden dauert beim Start
~1,6 s; danach kommt ein kurzer Satz nach 0,2–0,3 s, ein langer Vorlese-Satz
nach ~1 s. Wird gehämmert, rechnen mehrere Sätze parallel und der letzte kommt
spürbar später (gemessen: dritter von drei schnellen Tasten nach 0,7 s).

Die Tiere kommen aus der **einfarbigen** Schrift Noto Emoji (Pfad oben in
`tiere.py`). Die bunte Variante (`Noto-COLRv1.ttf`) zeichnet pygame leer.

## Konfigurieren

Oben in `oskalizer.py`:

```python
KEYBOARD_MATCH = "blackwidow"   # Teilstring im Gerätenamen, Groß-/Kleinschreibung egal
GRAB_MOUSE     = True
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
Ring voll. Loslassen setzt den Timer zurück.

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
