# Build-Log

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
