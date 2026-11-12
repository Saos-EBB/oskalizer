#!/usr/bin/env python3
"""Legt einen eigenen Clip (z.B. von YouTube, nur privat) als Video und Laut fuer ein
Tier ab, unter ~/.local/share/oskalizer/clips/<wort>/video|laut/.

    python3 clip_einsortieren.py affe.mp4 Mandrill
    python3 clip_einsortieren.py affe.mp4 Mandrill --start 12.5      # ab Sekunde 12,5
    python3 clip_einsortieren.py affe.mp4 Mandrill --ohne-ton         # nur das Video
    python3 clip_einsortieren.py --fehlt                               # welche Affen/Katzen noch nichts haben

Das Video wird wie die CC0-Videos neu kodiert (VP9, stumm, hoechstens 8 s, 480 Zeilen).
Der Ton kommt aus denselben 8 s: davon die lautesten 4 s, ohne Rumpeln, normalisiert.
Vorher prueft ClamAV die Datei (wie tiere_holen.py). Mehrere Clips pro Tier gehen,
gespielt wird dann zufaellig einer. Rauswerfen: Datei im clips-Ordner loeschen.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tiere_holen
from tiere import CLIPS, TIERE, WOERTER, ordner


def finde(name):
    """Wort aus woerter.json, Gross-/Kleinschreibung egal."""
    for liste in WOERTER.values():
        for wort in liste:
            if wort["name"].lower() == name.lower():
                return wort
    aehnlich = [w["name"] for l in WOERTER.values() for w in l if name.lower()[:3] in w["name"].lower()]
    sys.exit(f"'{name}' steht nicht in woerter.json." + (f" Meintest du: {', '.join(aehnlich)}?" if aehnlich else ""))


def fehlt():
    """Affen- und Katzenarten ohne Video oder ohne echten Laut."""
    for b, liste in WOERTER.items():
        for wort in liste:
            if not wort.get("primaer"):
                continue
            o = ordner(wort)
            video = any([*TIERE.glob(f"{o}/video/*"), *CLIPS.glob(f"{o}/video/*")])
            laut = any([*TIERE.glob(f"{o}/laut/*"), *CLIPS.glob(f"{o}/laut/*")])
            if not (video and laut):
                was = " und ".join(x for x, da in (("Video", video), ("Laut", laut)) if not da)
                print(f"{b}  {wort['name']:24} fehlt: {was}")


def main():
    arg = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    arg.add_argument("datei", nargs="?", type=Path)
    arg.add_argument("tier", nargs="?")
    arg.add_argument("--start", type=float, default=0.0, help="ab dieser Sekunde (Standard 0)")
    arg.add_argument("--ohne-ton", action="store_true", help="nur das Video ablegen")
    arg.add_argument("--fehlt", action="store_true", help="zeigen, welche Affen/Katzen noch etwas brauchen")
    a = arg.parse_args()
    if a.fehlt:
        return fehlt()
    if not a.datei or not a.tier:
        arg.error("Datei und Tier angeben, oder --fehlt")
    if not a.datei.is_file():
        sys.exit(f"Datei nicht gefunden: {a.datei}")
    wort = finde(a.tier)

    stamm = re.sub(r"[^a-z0-9]+", "-", a.datei.stem.lower()).strip("-")[:30] or "clip"
    stamm += "_" + hashlib.sha1(f"{a.datei.resolve()}{a.start}".encode()).hexdigest()[:6]
    ziel = CLIPS / ordner(wort)

    with tempfile.TemporaryDirectory(prefix="oskalizer-clip-") as tmp:
        tmp = Path(tmp)
        (tmp / "scan").mkdir()
        shutil.copy(a.datei, tmp / "scan" / "clip")
        print("ClamAV prueft den Clip ...")
        tiere_holen.scanne(tmp / "scan")

        (ziel / "video").mkdir(parents=True, exist_ok=True)
        video = ziel / "video" / f"{stamm}.webm"
        tiere_holen.video(tmp / "scan" / "clip", video, a.start)
        print(f"Video: {video}")

        if not a.ohne_ton:
            stueck = tmp / "stueck.wav"           # derselbe Ausschnitt wie das Video
            lauf = subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-ss", str(a.start), "-i", str(tmp / "scan" / "clip"),
                 "-t", str(tiere_holen.VIDEO_SEKUNDEN), "-vn", str(stueck)], capture_output=True)
            if lauf.returncode != 0 or not stueck.exists() or stueck.stat().st_size < 1000:
                print("Der Clip hat keinen Ton - nur das Video abgelegt.")
            else:
                (ziel / "laut").mkdir(parents=True, exist_ok=True)
                laut = ziel / "laut" / f"{stamm}.ogg"
                tiere_holen.laut(stueck, laut, 150)
                print(f"Laut:  {laut}")
    print(f"Fertig. Beim naechsten Start zeigt {wort['name']} den Clip.")


if __name__ == "__main__":
    main()
