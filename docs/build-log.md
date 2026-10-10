# Build-Log

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
