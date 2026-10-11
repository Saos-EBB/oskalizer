# Fehler

## 2026-10-12 — rembg hängt beim ersten Freistellen, >10 min ohne Ausgabe
**Symptom:** `remove()` kehrt nicht zurück, kaum CPU, kein u2net-Ordner.
**Ursache:** rembg 2.0.85 nimmt ohne Angabe das Modell bria-rmbg und lädt es still (>1 GB) nach `~/.rembg/models/bria-rmbg/`. Lizenz außerdem nur nicht-kommerziell.
**Fix:** `new_session("u2net")` in `freistellen.py` fest eingestellt (~170 MB).
