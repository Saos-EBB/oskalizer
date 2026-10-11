# Architektur

## Überblick
Keyboard playground für ein Kleinkind. Eine externe Tastatur (per Namens-Teilstring)
und die Maus werden per evdev exklusiv gegrabbt, pygame zeigt Vollbild. Beenden nur
über 5 s Esc halten oder SIGTERM.
Dazu die Familien-Webseite (`web/`, Vercel): Familie loggt sich mit eigenem
Passwort ein und schickt Aufnahmen per Mail; einsortiert wird von Hand.

## Module
- `oskalizer.py` — CONFIG-Block, Geräte finden/grabben/freigeben, Hauptschleife
  (evdev per `select` lesen, Esc-Timer, zeichnen). Hält den Modus (`state["modus"]`,
  „tiere“ | „tippen“, Wechsel mit Strg+Umschalt+D). Pro Key-Down mit Zeichen: im
  Modus Tiere `tiere.naechstes()` → `Tafel.show()` + `Ton.play()` mit demselben Wort, im Modus Tippen `Schreibtafel.tippe()`,
  bei Enter `Ton.sage(schreib.text)`.
- `woerter.json` — Buchstabe (A–Z, auch Ä/Ö/Ü) → Liste von Wörtern (Tier oder
  Person) mit `name`, `emoji`, `laut`, `lautschrift`. Die Lautschrift ist nur für
  die Familien-Webseite.
- `tiere.py` — lädt `woerter.json` als `WOERTER`, `naechstes(zeichen)` rotiert der
  Reihe nach durch die Wörter eines Buchstabens (None für Ziffern/Zeichen), Tastenbelegung
  `ZEICHEN` (evdev-Keycode → Zeichen, QWERTZ) und `Tafel` (zeichnet das aktuelle
  Zeichen im Modus Tiere; lädt beim Start `FAMILIE/<wort>/bild/*` als Ersatz fürs Emoji,
  zeigt „[von X]“ unten rechts). `ordner(wort)` und `person(path)` übersetzen
  zwischen Wort/Datei und Familien-Ordner.
  `Schreibtafel` zeigt im Modus Tippen den getippten Text, wortweise umgebrochen.
  Kennt keine Geräte. `oskalizer.py` ruft `Tafel.show(zeichen, wort, personen)` pro Key-Down und
  `Tafel.draw()` pro Frame.
- `ton.py` — `Ton`: spricht mit Piper (Modell einmal beim Start geladen, Synthese
  pro Text in einem Daemon-Thread, Ergebnis per Queue zurück, abgespielt über
  `pygame.mixer`); ohne Piper/Stimme per `espeak-ng`-Subprozess. `play` für ein
  Zeichen (gibt die Personen der gewählten Familien-Aufnahmen zurück), `sage` für
  den Tipp-Text. Lädt beim Start `FAMILIE/<wort>/name|laut/*.ogg|wav`. Bekommt das Wort von `oskalizer.py`; liest `WOERTER` nur für
  den zufälligen Laut bei Sonderzeichen. `play` legt eine Reihe aus Texten und
  Sounds an; `Ton.update()` pro Frame spielt fertige Piper-Sprache und startet dann
  das nächste Teil der Reihe. Jeder neue Text bekommt eine
  Auftragsnummer; Ergebnisse älterer Aufträge werden verworfen.

- Familien-Daten — `~/.local/share/oskalizer/familie/<wort>/name|laut|bild/<person>_<…>`,
  außerhalb des Repos (Repo wird öffentlich).
- `web/` — Vercel-Projekt (Root Directory = `web`), einzige Dependency `nodemailer`.
  Der Build (`npm run build`) kopiert `../woerter.json` nach `public/` — eine Quelle
  für oskalizer und Seite.
  `public/index.html` ist die ganze Seite. `api/_sitzung.js`: `personen()` liest
  `FAMILY_PASSWORDS`, `gleich()` vergleicht zeitkonstant, `setzeSitzung()`/`person(req)`
  schreiben/prüfen das HMAC-signierte Cookie `sitzung` (Person + Signatur mit
  `SESSION_SECRET`). `api/login.js` (POST, falsch → 3 s warten, 401), `api/wer.js`
  (GET, Person aus dem Cookie), `api/senden.js` (POST Wort/Slot/Audio als Base64 →
  Gmail-Mail an `MAIL_TO`, Betreff/Anhang mit Wort, Slot, Person, im Text der fertige
  ffmpeg-Befehl zum Einsortieren). Jeder Endpoint nimmt die Person nur aus `person(req)`.

## Datenfluss
Modus Tiere: evdev-Keycode → `tiere.ZEICHEN` → Zeichen → `tiere.naechstes` → Wort →
`Ton.play` (Familien-Aufnahme oder Piper, für Name und Laut getrennt) →
Personen → `Tafel.show` (Foto oder Emoji, „[von X]“). Solange `Ton.spricht()` True ist, ignoriert der Modus Tiere
weitere Zeichentasten.
Modus Tippen: Keycode → `ZEICHEN` (+ Leertaste) → `Schreibtafel.tippe`; Enter →
`Ton.sage(text)`, die nächste Taste leert den Text.

## Entscheidungen
- 2026-10-12 — Aufnahmen als JSON mit Base64 statt Multipart. Grund: Vercels Node-
  Runtime parst JSON selbst, Multipart bräuchte eine Dependency; 15 s Audio sind
  ein paar hundert KB. Format bleibt, was der Browser kann (WebM/Opus oder m4a),
  umgewandelt wird beim Einsortieren.
- 2026-10-12 — Login mit einem Passwort pro Person statt Name + Passwort. Grund: das
  Passwort sagt, wer es ist (für „[von Opa]“), niemand tippt seinen Namen. Cookie
  prüft zusätzlich, ob die Person noch in `FAMILY_PASSWORDS` steht — Eintrag
  löschen + neu deployen reicht zum Rauswerfen. Kein Rate-Limit, nur 3 s
  Verzögerung pro Fehlversuch (ein echtes bräuchte Speicher über Instanzen).
- 2026-10-12 — Familien-Aufnahmen statt `assets/`: pro Wort und Slot (name, laut,
  bild) beliebig viele Dateien, zufällig eine, Person aus dem Dateinamen. Liegt
  außerhalb des Repos, weil das Repo öffentlich wird. Eine Namens-Aufnahme ersetzt
  den ganzen Satz „A wie Affe“. „[von X]“ bleibt stehen, solange das Zeichen steht.
- 2026-10-11 — Tier-Tabelle als `woerter.json` statt Python-Dict, mehrere Wörter pro
  Buchstabe, der Reihe nach. Grund: die Familien-Webseite liest dieselbe Liste,
  und Familie kann eigene Wörter (auch Personen wie „Opa“) dazutun. Reihe statt
  Zufall: für das Kind berechenbar. Die Rotation fängt bei jedem Start vorn an.
- 2026-10-11 — Modus Tiere sperrt Zeichentasten, bis der Ton durch ist (statt
  abbrechen). Grund: Hämmern erzeugte Ton-Spam. Tasten während der Sperre
  verfallen, sie werden nicht nachgeholt.
- 2026-10-10 — Piper (Thorsten high) statt espeak-ng als Stimme, espeak bleibt Ersatz.
  Grund: natürlich klingend, offline. Synthese im Thread, weil sie 0,2–1 s blockiert.
  Stimmdatei außerhalb des Repos (114 MB).
- 2026-10-10 — Moduswechsel per Strg+Umschalt+D, Modifier-Zustand in `oskalizer.py`.
  Grund: pygame sieht die gegrabbte Tastatur nicht, also muss der evdev-Strom die
  Kombination selbst erkennen.
- 2026-10-10 — Tierlaute ohne Dateien als Lautmalerei über die Stimme. Grund: es gibt
  noch keine Aufnahmen.
- 2026-10-10 — Tiere als einfarbige Noto Emoji, pro Tastendruck eingefärbt. Grund:
  die bunte COLRv1-Schrift rendert in pygame/SDL_ttf leer.
- 2026-10-10 — Tastenbelegung fest auf QWERTZ im Code statt über XKB. evdev liefert
  nur Positionen, und es gibt genau eine Tastatur.
- 2026-10-10 — Kleckse (`visuals.py`), Dev-Panel (`devpanel.py`) und gespeicherte
  Einstellungen gelöscht. Grund: die neue Version zeigt Buchstaben mit Tieren statt
  Klecksen; das Panel drehte nur Klecks-Parameter.
- Eingaben kommen nur über evdev, nicht über pygame — pygame sieht von gegrabbten
  Geräten nichts.
