#!/usr/bin/env python3
"""Holt die CC0-Tierfotos und -laute aus tierquellen.json nach
~/.local/share/oskalizer/tiere/<wort>/bild|laut/.

    python3 tiere_holen.py            # nur was noch fehlt
    python3 tiere_holen.py --neu      # alles neu holen

Jede Datei landet erst in einer Quarantaene (~/.cache/oskalizer/quarantaene/) und
muss durch: nur https von den erlaubten Hosts, hoechstens 20 MB, Dateityp an den
ersten Bytes erkannt (nicht an der Endung), ClamAV-Scan (Podman-Container clamav/clamav, sonst clamscan; ohne
Scanner bricht es ab). Danach wird alles neu kodiert - Fotos per rembg
freigestellt als PNG, Laute per ffmpeg als OGG (die lauteste Stelle ohne Bass, Rumpeln per Hochpass weg,
hoechstens MAX_SEKUNDEN, laut normalisiert). Von der Originaldatei bleibt nur, was
Pillow/ffmpeg daraus dekodieren; Metadaten und angehaengte Bytes fallen weg.
Braucht ffmpeg, rembg (siehe freistellen.py) und podman oder clamscan.
"""

import array
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from tiere import ordner

QUELLEN = Path(__file__).parent / "tierquellen.json"
TIERE = Path.home() / ".local" / "share" / "oskalizer" / "tiere"
QUARANTAENE = Path.home() / ".cache" / "oskalizer" / "quarantaene"
HOSTS = {"live.staticflickr.com", "upload.wikimedia.org", "cdn.freesound.org"}
MAX_BYTES = 20 * 1024 * 1024
MAX_SEKUNDEN = 4.0
# Nur der erste Kanal statt Mono-Mix: manche Aufnahmen haben gegenphasige Kanaele,
# die sich beim Mischen zu Stille aufheben (gemessen: "seagull 2.wav", -91 dB)
MONO = "pan=mono|c0=c0"
HOCHPASS = 80                                  # Hz, wenn tierquellen.json nichts anderes sagt
CLAMAV_BILD = "docker.io/clamav/clamav:stable"

# erste Bytes -> Typ; was hier nicht passt, fliegt raus
MAGIC = {
    "bild": [(b"\xff\xd8\xff", "jpeg"), (b"\x89PNG\r\n\x1a\n", "png")],
    "laut": [(b"ID3", "mp3"), (b"OggS", "ogg"), (b"RIFF", "wav"), (b"fLaC", "flac")],
}


def lade(url, ziel, versuche=4):
    for i in range(versuche):
        try:
            return _lade(url, ziel)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 503) or i == versuche - 1:
                raise
            time.sleep(20 * (i + 1))           # Wikimedia drosselt, kurz warten


def _lade(url, ziel):
    teile = urllib.parse.urlparse(url)
    if teile.scheme != "https" or teile.hostname not in HOSTS:
        raise ValueError(f"Host nicht erlaubt: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "oskalizer-tiere_holen/1 (https://github.com/Saos-EBB/oskalizer)"})
    with urllib.request.urlopen(req, timeout=60) as antwort, open(ziel, "wb") as f:
        geladen = 0
        while block := antwort.read(65536):
            geladen += len(block)
            if geladen > MAX_BYTES:
                raise ValueError(f"groesser als {MAX_BYTES // 2**20} MB: {url}")
            f.write(block)


def typ(path, slot):
    kopf = path.read_bytes()[:16]
    for magic, name in MAGIC[slot]:
        if kopf.startswith(magic):
            if name == "wav" and kopf[8:12] != b"WAVE":
                break
            return name
    # MP3 ohne ID3-Tag: Frame-Sync (11 Bit) und Layer III, egal ob MPEG 1, 2 oder 2.5
    if slot == "laut" and kopf[0] == 0xFF and kopf[1] & 0xE0 == 0xE0 and kopf[1] & 0x06 == 0x02:
        return "mp3"
    raise ValueError(f"{path.name}: kein erlaubter Dateityp (Kopf {kopf[:8].hex()})")


def scanne(ordner_):
    """ClamAV ueber den ganzen Quarantaene-Ordner. Bricht ab, wenn etwas anschlaegt
    oder kein Scanner da ist."""
    if shutil.which("podman"):
        befehl = ["podman", "run", "--rm", "--network=none",
                  "-v", f"{ordner_}:/scan:ro,Z", CLAMAV_BILD,
                  "clamscan", "--recursive", "--infected", "--no-summary", "/scan"]
    elif shutil.which("clamscan"):
        befehl = ["clamscan", "--recursive", "--infected", "--no-summary", str(ordner_)]
    else:
        sys.exit("Kein Virenscanner (podman oder clamscan) - es wird nichts eingespielt.")
    lauf = subprocess.run(befehl, capture_output=True, text=True)
    if lauf.returncode == 1:
        sys.exit(f"ClamAV schlaegt an:\n{lauf.stdout}")
    if lauf.returncode != 0:
        sys.exit(f"ClamAV-Fehler ({lauf.returncode}):\n{lauf.stderr[-2000:]}")


_SITZUNG = []                                  # rembg-Modell, einmal geladen


def bild(quelle, ziel, unten_weg=0.0):
    from io import BytesIO

    from PIL import Image
    from rembg import new_session, remove

    if not _SITZUNG:
        _SITZUNG.append(new_session("u2net"))

    with Image.open(quelle) as roh:
        roh.load()
        rgb = roh.convert("RGB")           # nur Pixel, keine Metadaten
    if unten_weg:                          # Bildunterschrift-Balken, sonst bleibt er beim Freistellen
        rgb = rgb.crop((0, 0, rgb.width, int(rgb.height * (1 - unten_weg))))
    rgb.thumbnail((1024, 1024))
    puffer = BytesIO()
    rgb.save(puffer, "PNG")
    frei = Image.open(BytesIO(remove(puffer.getvalue(), session=_SITZUNG[0])))
    frei = frei.crop(frei.getbbox() or (0, 0, *frei.size))     # leeren Rand weg
    frei.save(ziel, "PNG")


def lauteste_stelle(quelle, hochpass):
    """Start (s) des lautesten MAX_SEKUNDEN-Fensters. Lange Aufnahmen haben vorn
    oft nur Rauschen. Gemessen ohne Bass: sonst gewinnt Wind- und Mikrofonrumpeln
    gegen den Vogel (gemessen: Amsel, Lerche)."""
    filt = f"{MONO},highpass=f={max(hochpass, 150)}:poles=2,highpass=f={max(hochpass, 150)}:poles=2"
    roh = subprocess.run(["ffmpeg", "-v", "error", "-i", str(quelle), "-vn", "-af", filt,
                          "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    werte = array.array("h", roh[: len(roh) // 2 * 2])
    block = 800                                    # 0,1 s
    energie = [sum(x * x for x in werte[i:i + block]) for i in range(0, len(werte), block)]
    fenster = int(MAX_SEKUNDEN * 10)
    if len(energie) <= fenster:
        return 0.0
    summe = best = sum(energie[:fenster])
    start = 0
    for i in range(fenster, len(energie)):
        summe += energie[i] - energie[i - fenster]
        if summe > best:
            best, start = summe, i - fenster + 1
    return max(0.0, start / 10 - 0.1)


def laut(quelle, ziel, hochpass=HOCHPASS):
    """hochpass (Hz) schneidet Rumpeln weg: 300 fuer Voegel/Insekten, 80 fuer Loewe & Co."""
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", str(lauteste_stelle(quelle, hochpass)), "-i", str(quelle),
         "-vn", "-sn", "-map_metadata", "-1", "-af",
         f"{MONO},highpass=f={hochpass}:poles=2,highpass=f={hochpass}:poles=2,"
         f"atrim=0:{MAX_SEKUNDEN},afade=t=in:d=0.05,afade=t=out:st={MAX_SEKUNDEN - 0.4}:d=0.4,"
         # loudnorm rechnet mit 192 kHz und haelt kurz die Spitzen nicht - Limiter danach
         "loudnorm=I=-16:TP=-1.5,aresample=44100,alimiter=limit=0.7:level=false",
         "-ar", "44100", "-c:a", "libvorbis", "-q:a", "5", str(ziel)], check=True)


def schreibe_quellen(eintraege):
    zeilen = ["# Quellen der Tierfotos und -laute (alle CC0 1.0)", ""]
    for e in eintraege:
        zeilen.append(f"- {e['wort']} ({e['slot']}): „{e['titel']}“ von {e['urheber']}, "
                      f"{e['seite']}")
    (TIERE / "QUELLEN.md").write_text("\n".join(zeilen) + "\n", encoding="utf-8")


def main():
    neu = "--neu" in sys.argv
    eintraege = json.loads(QUELLEN.read_text(encoding="utf-8"))
    offen = []
    for e in eintraege:
        ziel = TIERE / ordner({"name": e["wort"]}) / e["slot"] / (
            hashlib.sha1(e["url"].encode()).hexdigest()[:10] + (".png" if e["slot"] == "bild" else ".ogg"))
        if neu or not ziel.exists():
            offen.append((e, ziel))
    if not offen:
        schreibe_quellen(eintraege)
        print("Alles schon da.")
        return

    # Quarantaene bleibt ueber Abbrueche hinweg liegen (Wikimedia drosselt, ein Lauf
    # dauert lange); eine Datei verschwindet erst, wenn sie fertig kodiert ist
    QUARANTAENE.mkdir(parents=True, exist_ok=True)
    roh = {}
    for e, _ in offen:
        datei = QUARANTAENE / hashlib.sha1(e["url"].encode()).hexdigest()
        if not datei.exists():
            print(f"lade {e['wort']} {e['slot']}: {e['url']}")
            lade(e["url"], datei)
            time.sleep(1)
        try:
            typ(datei, e["slot"])
        except ValueError as exc:              # nur diese Datei fliegt raus
            print(f"  ! verworfen: {e['wort']} {exc}")
            datei.unlink()
            continue
        roh[e["url"]] = datei
    print(f"ClamAV prueft {len(list(QUARANTAENE.iterdir()))} Dateien ...")
    scanne(QUARANTAENE)
    for e, ziel in offen:
        if e["url"] not in roh:
            continue
        ziel.parent.mkdir(parents=True, exist_ok=True)
        print(f"kodiere {ziel.relative_to(TIERE)}")
        if e["slot"] == "bild":
            bild(roh[e["url"]], ziel, e.get("unten_weg", 0.0))
        else:
            laut(roh[e["url"]], ziel, e.get("hochpass", HOCHPASS))
        roh[e["url"]].unlink()

    schreibe_quellen(eintraege)
    print(f"Fertig. Quellen in {TIERE / 'QUELLEN.md'}")


if __name__ == "__main__":
    main()
