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

Die Tiere (Name, Emoji, Laut, Lautschrift) stehen in `woerter.json`. Jeder
Buchstabe A–Z hat vier Tiere, keins kommt doppelt vor (A: Affe, Amsel, Ara,
Alpaka). Dazu kommt pro Buchstabe eine Affen- und eine Katzenart (`"primaer": true`,
z.B. B: Brüllaffe und Britisch Kurzhaar), weil das Kind die am liebsten mag. Q und X
haben keine, es gibt keine mit dem Anfangsbuchstaben. Die Lieblingstiere kommen
bevorzugt: zweimal Affe und Katze, dann ein anderes Tier (`PRIMAER_RUNDEN` in
`tiere.py`). Weitere Einträge gehen auch, z.B. O: Opa. Ä, Ö und Ü dürfen auch Einträge bekommen. Ein Eintrag ohne
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

Leertaste, Enter, F-Tasten, Shift, Esc und die Maus zeigen nichts (die Maus nur im Modus Wirbel). Shift wird
nicht ausgewertet — es gibt nur Großbuchstaben und die ungeshifteten Zeichen.
Die Tastenbelegung ist auf ein deutsches QWERTZ-Layout festgelegt.

### Echte Tierfotos und -laute (freie Lizenzen)

Ohne Familien-Foto zeigt ein Tier ein echtes Foto statt des Emojis, ohne
Familien-Laut spielt der echte Tierlaut statt der gesprochenen Lautmalerei.
Familien-Dateien gehen immer vor. Alles steht unter einer freien Lizenz: die
ersten Dateien **CC0**, für die Affen und Katzen auch **CC BY / CC BY-SA** und
gemeinfrei (nie NC oder ND). Fotos und Videos von Wikimedia Commons, Laute von
Freesound und Wikimedia Commons. Welche Datei woher kommt, steht in
`tierquellen.json` (Seite, Urheber, Lizenz), die Namensnennung in `QUELLEN.md`.

Die Dateien liegen nicht im Repo, sondern unter `~/.local/share/oskalizer/tiere/`
(gleiche Ordnernamen wie bei der Familie, `bild/` und `laut/`). Geholt werden sie mit:

```bash
python3 tiere_holen.py          # nur was fehlt;  --neu holt alles neu
```

Das Skript lädt nur per https von Wikimedia/Freesound, höchstens 20 MB pro
Datei, erkennt den Dateityp an den ersten Bytes und lässt alles von **ClamAV**
prüfen (Podman-Container `clamav/clamav`, sonst ein installiertes `clamscan`;
ohne Scanner spielt es nichts ein). Danach wird alles neu kodiert: Fotos per
rembg freigestellt (PNG), Laute als OGG mit der lautesten Stelle, höchstens
4 s, laut normalisiert. Vom Original bleibt nur, was Pillow/ffmpeg dekodieren.
Braucht ffmpeg, rembg (siehe unten) und podman. Die Ordner-Datei
`QUELLEN.md` daneben listet die Urheber.

Keinen echten Laut haben 27 der 104 Tiere, weil es kein brauchbares
CC0-Original gibt: Büffel, Chamäleon, Chinchilla, Giraffe, Gorilla, Iltis, Impala,
Japanmakak, Nashorn, Orang-Utan, Otter, alle vier Q-Tiere, Raupe, Uferschwalbe,
Urson, alle V-Tiere außer Vogel, alle X-Tiere außer Xerus, Yapok, Ypsiloneule und
Zebra. Da bleibt die Lautmalerei. Yak und Kuh muhen mit verschiedenen
Kuh-Aufnahmen, der Jungfernkranich ruft mit einem anderen Kranich. Der Kuckuck hat
kein Foto (auf allen CC0-Fotos sitzt er zu klein im Gebüsch, rembg findet ihn
nicht) und zeigt das Emoji.

Beim Ausschneiden der 4 s wird die lauteste Stelle ohne Bass gesucht, sonst gewinnt
Wind- und Mikrofonrumpeln gegen den Vogel. Ein Hochpass nimmt das Rumpeln auch aus
dem fertigen Laut: 300 Hz für Vögel, Insekten und kleine Tiere, 150 Hz für mittlere,
80 Hz für die großen (Feld `hochpass` in `tierquellen.json`). Eine Datei rauswerfen: Eintrag
aus `tierquellen.json` löschen und die Datei im Ordner löschen.

### Tiervideos

47 Tiere haben ein kurzes Video von Wikimedia Commons (CC0, CC BY oder CC BY-SA),
keins davon aus Zoo, Aquarium, Museum, Labor oder Gehege, nichts mit Jagd oder
Beute (der Zuschauer ist anderthalb). Den Rest füllen eigene Clips. Ein Video läuft statt des Fotos neben dem Buchstaben,
einmal, höchstens 8 s, ohne eigenen Ton (den Laut spielt wie immer `ton.py`), und
bleibt am Ende auf dem letzten Bild stehen. Die nächste Taste bricht es ab. Ein
Familien-Foto geht vor.

pygame 2.6 kann kein Video, darum dekodiert pro Video ein `ffmpeg`-Prozess in
Echtzeit (`-re`), ein Thread liest die Einzelbilder. Geholt werden die Videos mit
`tiere_holen.py` wie Fotos und Laute: Typ an den ersten Bytes (WebM/Ogg), ClamAV,
dann neu kodiert als WebM/VP9 ohne Ton, 480 Zeilen, 24 fps (`~/.local/share/oskalizer/tiere/<wort>/video/`,
zusammen ~65 MB).

Achtung beim Erweitern: Auf Commons liegen zu harmlosen Suchwörtern
auch Schlachtungen, Paarungen, Tierversuche und bei „snake“ sogar Pornografie.
Jedes Video vor dem Eintragen ansehen, und vom fertigen Video Bilder aus der
Mitte und vom Ende prüfen, nicht nur das Vorschaubild.

### Eigene Clips (`clip_einsortieren.py`)

Nicht für jeden Affen und jede Katze gibt es ein freies Video aus der Natur (Zoo-,
Aquarium- und Gehege-Videos sind bewusst raus). Eigene Clips, z.B. von YouTube für
den privaten Gebrauch, sortiert das Skript ein:

```bash
python3 clip_einsortieren.py --fehlt                       # welche Affen/Katzen noch etwas brauchen
python3 clip_einsortieren.py mandrill.mp4 Mandrill          # Video + Ton ab Sekunde 0
python3 clip_einsortieren.py mandrill.mp4 Mandrill --start 12.5
python3 clip_einsortieren.py katze.mp4 Siamkatze --ohne-ton
```

Es prüft den Clip mit ClamAV und kodiert ihn wie die Commons-Videos neu (8 s, VP9, stumm).
Den Laut nimmt es aus denselben 8 s (die lautesten 4 s, ohne Rumpeln). Abgelegt wird
unter `~/.local/share/oskalizer/clips/<wort>/video|laut/`, außerhalb des Repos. Mehrere
Clips pro Tier gehen, dann zufällig einer. Neu geladen wird beim nächsten Start.

### Tastatur-Beleuchtung (`kb-rgb ozk`)

Läuft die Beleuchtung `kb-rgb ozk` (KBD-Kachel, Modus „ozk“: jede gedrückte
Taste leuchtet 5 s in einer zufälligen Farbe), leuchtet sie auch im oskalizer.
Weil der oskalizer die Tastatur exklusiv grabbt, kommt bei `kb-rgb` per evdev
nichts an. Darum schickt er jeden Tastendruck als Datagramm an
`$XDG_RUNTIME_DIR/kb-rgb-ozk.sock`. Läuft `kb-rgb ozk` nicht, verfällt das still.
`kb-rgb` liegt nicht im Repo (`~/.local/bin/kb-rgb`).

## Modus Tippen

**Strg+Umschalt+D** schaltet der Reihe nach durch die Modi „Tiere“ (Start),
„Tippen“ und „Wirbel“.
Im Tippen-Modus erscheint jedes getippte Zeichen als Text in der Mitte, die
Leertaste macht Wortabstände. Keine Tiere, kein Ton pro Taste. Zu langer Text
wird umgebrochen; was oben aus dem Bildschirm läuft, ist weg. Es gibt keine
Rücktaste und weiterhin nur Großbuchstaben. Beim Wechsel bleibt der Text des
Tippen-Modus stehen.

Enter tut nichts (früher las es den Text vor).

## Modus Wirbel

Jedes Zeichen landet an einem zufälligen freien Platz irgendwo auf dem Schirm, in
einer zufälligen Farbe, und bleibt dort stehen. Die Animation ist die von
„Let's talk now“ auf kev.dev: Der Buchstabe fällt leicht verdreht und durchsichtig
von etwas weiter oben ein, schwingt beim Landen kurz über und schwebt danach für
sich auf und ab, jeder mit eigenem Takt. Kein Ton, keine Tiere. Ab 30 Buchstaben
blendet der älteste aus. Beim Wechsel bleiben die Buchstaben stehen.

In diesem Modus gibt es einen **Mauszeiger**. Ein Klick (jede Maustaste) auf einen
schwebenden Buchstaben lässt ihn fallen: Schwerkraft, Abprallen an Boden und Rand,
Stöße mit den anderen. Unten wächst so ein Haufen. Fährt die Maus durch den Haufen,
schubst sie die Buchstaben weg, je schneller, desto weiter. Ein Klick auf einen
gefallenen Buchstaben lässt ihn hochhüpfen. Ab 60 gefallenen blendet der älteste aus.
Die Physik ist die von kev.dev (`src/contact/contact-physics.ts`), mit zwei
Änderungen: Der Stoß zwischen zwei Buchstaben bremst das Aufeinanderprallen (auf
kev.dev hat er das Vorzeichen falsch herum), und Buchstaben, die sich eine halbe
Sekunde kaum bewegen, schlafen ein, damit der Haufen nicht ewig zittert.

Drei Dateien: `oskalizer.py` (Geräte, Schleife, Beenden), `tiere.py` (lädt
`woerter.json`, Tastenbelegung, Anzeige), `ton.py` (Sprechen und Tondateien).
Dazu `tiere_holen.py` (CC0-Tierdateien holen) und `freistellen.py`.

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
Die interne Laptop-Tastatur heißt anders und wird nicht angefasst — solange
die externe angesteckt ist.

**Ohne externe Tastatur** nimmt das Tool beim Start die interne
(Laptop-Tastatur am i8042-Controller, z.B. „AT Translated Set 2 keyboard“) und
grabbt sie. Erkannt wird nur beim Start; anstecken während es läuft ändert nichts.

## Starten und Beenden

```bash
oskalizer            # Kurzbefehl, siehe unten
python3 oskalizer.py # oder direkt
oskalizer --kachel   # im Fenster statt im Vollbild (Tastatur und Maus bleiben gegrabbt)
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
Start auf der Konsole. Die **interne** Laptop-Tastatur wird nicht gegrabbt und
funktioniert die ganze Zeit weiter — außer die externe ist nicht angesteckt,
dann ist die interne gegrabbt und nur Esc-Halten, SSH oder ein anderes TTY
kommen raus.
