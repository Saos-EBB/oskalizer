# Build-Log

## 2026-11-14 — feat(tiere): freie Videos und Fotos für Affen und Katzen
**Was:** Neben CC0 jetzt auch CC BY / CC BY-SA / gemeinfrei von Commons (nie NC/ND), Lizenz und Urheber pro Datei in `tierquellen.json` und `QUELLEN.md`. Pro Lieblingstier Videos und Fotos gesucht, Zoo/Gehege/Labor/Jagd per Stichwort raus, Rest von Hand auf Kontaktbögen gesichtet, vom fertigen Video vier Bilder geprüft (6 Videos und 4 missratene Freistellungen danach wieder raus). Jetzt haben 26 der 48 Lieblingstiere ein Video aus der Natur oder von zu Hause, 20 ein Foto, 2 nur das Emoji. D und R bekommen statt Devon Rex und Ragdoll (kein Video zu finden) Dschungelkatze und Rotluchs als Lieblingskatze. 112 Dateien, alle durch ClamAV.
**Nicht gebaut:** keine Laute aus den neuen Videos (viele haben Ton, z.B. schnurrender Gepard), kein Video für 22 Lieblingstiere (Rassekatzen, seltene Affen: auf Commons nur aus dem Zoo oder gar nicht), kein Foto für York Chocolate und Zwergtigerkatze.

## 2026-11-12 — feat(tiere): Affe und Katze auf jeder Taste, keine Zoo-Videos
**Was:** Beim Testen mit dem Kind: es mag fast nur Affen und Katzen. Jetzt hat jeder Buchstabe eine Affen- und eine Katzenart (`primaer`, 48 Arten, alle verschieden, außer Q und X), die bevorzugt drankommen (zweimal Affe+Katze, dann ein anderes Tier). Alle Videos aus Zoo, Aquarium, Museum oder Gehege sind raus (16 + die neuen Kandidaten), dazu drei, auf denen das Tier nur ein Punkt ist. Für die Lücken `clip_einsortieren.py`: eigener Clip → ClamAV → Video und Laut unter `clips/`, die oskalizer und Vorschau mitladen.
**Nicht gebaut:** kein YouTube-Download (Clips holt der Nutzer selbst), keine Affen/Katzen für Q und X, kein Nachladen ohne Neustart. Mit Video und Laut komplett sind erst 6 der 48 Lieblingstiere.

## 2026-11-12 — feat(tiere): Tiervideos
**Was:** Es soll mehr passieren: 40 Tiere zeigen statt des Fotos ein kurzes CC0-Video (Commons), möglichst zwei pro Taste. `Film` in `tiere.py` lässt `ffmpeg` in Echtzeit in einen Thread dekodieren, `Tafel` setzt jedes Frame neben den Buchstaben; neue Taste, Moduswechsel und Ende beenden den Prozess. `tiere_holen.py` kann den Slot `video` (WebM/Ogg erkannt, bis 80 MB, ClamAV, neu als VP9 ohne Ton, 8 s ab `start`). Jedes Video von Hand gesichtet, vom fertigen Video vier Bilder geprüft.
**Nicht gebaut:** keine Videos für C, X, Y (kein brauchbares CC0), kein Ton aus dem Video, keine Schleife (bleibt am Ende stehen), kein Vorladen (Start beim Tastendruck, ~0,2 s bis zum ersten Bild), keine Familien-Videos.

## 2026-11-12 — fix(laute): Rumpeln statt Tier, kaputte Laute raus
**Was:** Amsel und Gorilla klangen falsch. Ursache Amsel (und viele Vögel/Insekten): die Suche nach der lautesten Stelle wurde von Wind- und Mikrofonrumpeln gewonnen, die Normierung zog es hoch. Jetzt sucht sie ohne Bass, und ein Hochpass pro Laut (`hochpass`: 300/150/80 Hz) nimmt das Rumpeln raus; alle Laute neu kodiert. Danach alle 150 per Spektrogramm, Abstand Ruf/Grundrauschen und Tonhaltigkeit geprüft: 8 Laute raus (Gorilla-Stotter-Effekt, Wal-Sinuston, Kamel-Brummen, fünf Aufnahmen, die nur Wind/Umgebung sind).
**Nicht gebaut:** kein Ersatz für die entfernten Laute, kein automatischer Qualitäts-Check in `tiere_holen.py` (die Prüfskripte liefen nur einmal), niemand hat die Laute angehört.

## 2026-11-11 — feat(tiere): vier Tiere pro Taste
**Was:** Jeder Buchstabe hat jetzt vier Tiere statt einem (78 neue, keins doppelt), damit beim Hämmern mehr passiert. Ausgewählt nach dem, wofür es einen echten CC0-Laut gibt, Fotos danach. `tiere_holen.py` erkennt MP3 jetzt am Frame-Sync (auch MPEG 2.5) und verwirft eine unzulässige Datei einzeln statt alles abzubrechen; optional `unten_weg` schneidet eine Bildunterschrift ab. Quarantäne liegt jetzt dauerhaft in `~/.cache/oskalizer/quarantaene/` (ein abgebrochener Lauf lädt nicht alles neu). Mono heißt jetzt erster Kanal statt Mischung: eine Möwen-Aufnahme hatte gegenphasige Kanäle und wurde beim Mischen stumm. Gemessen: Start 3,3 s statt 2,0 s, 461 MB Speicher.
**Nicht gebaut:** keine Ä/Ö/Ü-Tiere, keine Laute für 25 Tiere (kein CC0-Original), kein Foto für den Kuckuck, kein Nachladen der Dateien bei Bedarf (alles beim Start).

## 2026-11-10 — feat(licht): Tastendrücke an kb-rgb ozk weitergeben
**Was:** Die Tasten-Beleuchtung `kb-rgb ozk` blieb im oskalizer dunkel: der exklusive Grab (EVIOCGRAB) lässt keine Events mehr zu anderen Lesern durch. Jetzt schickt der oskalizer jeden Key-Down per Unix-Datagramm an `$XDG_RUNTIME_DIR/kb-rgb-ozk.sock`, `kb-rgb ozk` hört dort zusätzlich zu evdev.
**Nicht gebaut:** kein automatisches Starten von `kb-rgb ozk` mit dem oskalizer, keine eigene Farblogik im oskalizer.

## 2026-11-10 — feat(tiere): echte CC0-Tierfotos und -laute
**Was:** Es soll mehr passieren: 40 freigestellte Fotos und 46 echte Tierlaute für 26 bzw. 20 Tiere statt Emoji und gesprochener Lautmalerei. `tiere_holen.py` holt sie aus `tierquellen.json`, prüft (Host, Größe, Magic Bytes, ClamAV) und kodiert neu; Familien-Dateien gehen weiter vor.
**Nicht gebaut:** keine GIFs/Animationen, keine Laute für Chamäleon, Giraffe, Qualle, Raupe, Nashorn, Zebra, kein Auswahl-Werkzeug (Liste von Hand), kein automatisches ClamAV-Update.

## 2026-10-13 — feat(geraete): interne Tastatur, wenn die externe fehlt
**Was:** Ist die BlackWidow nicht angesteckt, startet der oskalizer trotzdem und grabbt die Laptop-Tastatur (i8042-Bus) statt mit Fehler abzubrechen. Nebenbei: Geräte werden direkt aus `/dev/input/event*` gelesen, weil `evdev.list_devices()` nicht lesbare stumm weglässt — fehlende `input`-Gruppe kam sonst als „keine Tastatur gefunden“ statt „keine Rechte“.
**Nicht gebaut:** kein Hotplug (anstecken während des Laufs wechselt nicht), keine Erkennung von I2C-/USB-internen Laptop-Tastaturen, kein eigener CONFIG-Schalter.

## 2026-10-12 — chore(repo): Git-Historie vor dem Öffentlich-Schalten geprüft
**Was:** Alle 21 Commits, alle je eingecheckten Dateien und Diffs durchsucht: keine Passwörter, Keys, `.env`, Home-Pfade oder Dateien >200 KB. Sichtbar wird nur die Autor-Mail in den Commits; die Tastatur heißt im Code „blackwidow“.
**Nicht gebaut:** kein Umschreiben der Historie (nichts zu entfernen), kein Secret-Scanner als Hook; öffentlich schaltet der User selbst.

## 2026-10-12 — feat(familie): Fotos neuer Wörter mit rembg freistellen
**Was:** Familie kann irgendein Foto schicken; `freistellen.py` schneidet das Motiv beim Einsortieren aus (PNG, transparent), die Mail zu einem neuen Wort enthält den fertigen Befehl.
**Nicht gebaut:** kein Einsortier-Skript für die ganze Mail, keine Modellwahl, kein Freistellen im Browser.

## 2026-10-12 — feat(web): „+ Neues Wort“ mit Name, Foto und Laut
**Was:** Familie kann eigene Wörter vorschlagen — Tiere, aber auch sich selbst („Opa“); alle drei Felder Pflicht, Foto im Browser auf 1024 px JPEG. Mail-Code nach `api/_mail.js`, weil jetzt zwei Endpoints mailen; Leerzeichen im Wort werden im Ordnernamen zu `-` (sonst bräche der Befehl in der Mail).
**Nicht gebaut:** kein Zuschneiden im Browser, kein geschriebener Laut (Eintrag kommt mit `"laut": ""`), kein automatisches Eintragen in `woerter.json`.

## 2026-10-12 — feat(web): Wörter-Tabelle, Aufnehmen und Versand per Mail
**Was:** Kern der Familien-Seite: jedes Wort aus `woerter.json` mit Lautschrift-Hilfe, Name/Laut aufnehmen (max. 15 s, anhören, neu), Senden schickt eine Gmail-Mail mit Anhang und dem fertigen ffmpeg-Einsortier-Befehl.
**Nicht gebaut:** keine Umwandlung im Browser, keine Pegelanzeige, kein Merken was schon gesendet ist (nur ✓ bis zum Neuladen), keine Prüfung ob das Wort in `woerter.json` steht.

## 2026-10-12 — feat(web): Login mit Passwort pro Person und 3-2-1-Sperre
**Was:** Erster Teil der Familien-Webseite: nur ein Passwortfeld, das Passwort bestimmt die Person (später „[von Opa]“), danach ein signiertes Cookie, das jeder Endpoint prüft. Falsch: Feld leer, 3-2-1, Server hält 3 s zurück.
**Nicht gebaut:** kein echtes Rate-Limit, kein Logout, kein wachsender Lock, kein Light-Mode; nach dem Login steht nur „Hallo Opa!“ — die Tabelle kommt im nächsten Step.

## 2026-10-12 — feat(familie): Familien-Aufnahmen pro Wort, zufällig, mit „[von X]“
**Was:** Der oskalizer spielt Familien-Aufnahmen aus `~/.local/share/oskalizer/familie/` (Name ersetzt „A wie Affe“, Laut den Tierlaut, Foto das Emoji) und zeigt unten rechts, von wem sie sind; `assets/` fliegt raus, weil das Repo öffentlich wird.
**Nicht gebaut:** kein Vorab-Rechnen von Piper (nach einer Namens-Aufnahme kommt der gesprochene Laut mit ~0,2–1 s Pause), kein Nachladen ohne Neustart, kein „[von X]“ für Fotos, keine Warnung bei Ordnern ohne passendes Wort.

## 2026-10-11 — refactor(tiere): Tier-Tabelle als woerter.json, Wörter rotieren pro Buchstabe
**Was:** Grundlage für die Familien-Aufnahmen: Webseite und oskalizer lesen dieselbe Liste, ein Buchstabe kann mehrere Wörter haben (z.B. O: Oktopus, Opa), die der Reihe nach drankommen; neue lesbare Lautschrift als Einsprech-Hilfe. Ä/Ö/Ü sind erlaubte Schlüssel.
**Nicht gebaut:** keine Umbenennung von `tiere.py`, keine Schema-Prüfung der JSON, kein Merken der Rotation über Neustart; Tondateien/Bilder in `assets/` gelten weiter pro Buchstabe.

## 2026-10-11 — fix(tiere): Tasten gesperrt, solange der Ton läuft
**Was:** Hämmern im Modus Tiere hat jeden Ton sofort abgebrochen und neu gestartet — Spam. Jetzt zählt erst wieder eine Taste, wenn Sprache und Tondatei durch sind; ein Piper-Fehler im Thread gibt die Sperre frei, sonst bliebe die Tastatur tot.
**Nicht gebaut:** keine Mindest-Sperrzeit, keine Warteschlange, keine Anzeige der Sperre; Tippen-Modus unverändert.

## 2026-10-10 — feat(ton): Piper-Stimme Thorsten statt espeak-ng
**Was:** Nach Hörproben gewählt — Thorsten high spricht überall (Tiere, Ziffern, Vorlesen); espeak springt nur ein, wenn Piper oder die Stimme fehlt.
**Nicht gebaut:** keine Stimmenwahl, kein Limit paralleler Synthese-Threads beim Hämmern, kein Vorab-Cache der „A wie …“-Sätze.

## 2026-10-10 — feat(tippen): Enter liest den getippten Text vor
**Was:** Im Tippen-Modus spricht espeak-ng mit Enter den Text; die nächste Taste beginnt einen neuen.
**Nicht gebaut:** keine eigene Robo-Stimme/Effekte, kein Mitmarkieren des gesprochenen Worts, keine Warteschlange.

## 2026-10-10 — feat(modus): Strg+Umschalt+D wechselt in den Tippen-Modus
**Was:** Zweiter Modus, in dem getippte Zeichen als Text stehen bleiben statt einzeln mit Tier zu erscheinen.
**Nicht gebaut:** keine Rücktaste, keine Shift-Ebene, keine Modus-Anzeige, kein Merken des Modus über Neustart, kein Cursor.

## 2026-10-10 — feat(tiere): eigene Bilder aus assets/bilder/ statt Emoji
**Was:** Platz für echte Tierbilder später; ein `a.png` ersetzt das Affen-Emoji, ohne Code anzufassen.
**Nicht gebaut:** keine Einfärbung der Bilder, nur PNG/JPG, kein Nachladen zur Laufzeit.

## 2026-10-10 — feat(ton): espeak-ng spricht, Tondateien aus assets/toene/
**Was:** Buchstaben sagen „A wie Affe“ plus Tierlaut, Ziffern sagen die Zahl, Zeichen machen einen zufälligen Tierlaut. Ohne Aufnahmen spricht espeak eine Lautmalerei.
**Nicht gebaut:** keine Lautstärke-Einstellung, keine Warteschlange (neue Taste bricht ab), kein MP3, Dateinamen nur nach Buchstabe.

## 2026-10-10 — feat(tiere): Buchstaben mit Tier, Ziffern und Zeichen anzeigen
**Was:** Neuer Kern statt der Kleckse — jede Zeichentaste zeigt ihr Zeichen groß, A–Z mit passendem Tier daneben.
**Nicht gebaut:** kein Tiername als Text, keine Shift-Ebene, keine Drosselung beim Hämmern (neue Taste ersetzt die alte).

## 2026-10-10 — delete(visuals): Kleckse, Dev-Panel und Settings raus
**Was:** Die Buchstaben-und-Tiere-Version ersetzt die Kleckse; das Panel drehte nur Klecks-Parameter, also fliegt es mit samt `settings.json`-Persistenz.
**Nicht gebaut:** kein Ersatz-Effekt — bis zum nächsten Step bleibt der Schirm dunkel.

## 2026-10-10 — chore(git): .claude/ ignorieren
**Was:** Der lokale Session-State (`.claude/workmode.state`) soll nicht im Repo landen.
**Nicht gebaut:** keine weiteren Ignore-Einträge.
