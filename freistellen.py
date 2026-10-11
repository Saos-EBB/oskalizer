"""Schneidet das Tier (oder Opa) aus einem Familien-Foto aus: PNG mit
transparentem Hintergrund, passt zum dunklen oskalizer-Schirm.

    python3 freistellen.py foto.jpg ~/.local/share/oskalizer/familie/igel/bild/papa_2026-10-12.png

Braucht `pip install --user rembg`. Das Modell u2net (~170 MB, Apache-2.0) laedt
beim ersten Lauf nach ~/.rembg/models/. Fest eingestellt, weil rembg sonst bria-rmbg nimmt
(>1 GB, Lizenz nur nicht-kommerziell).
"""

import sys
from pathlib import Path

from rembg import new_session, remove

quelle, ziel = map(Path, sys.argv[1:3])
ziel.parent.mkdir(parents=True, exist_ok=True)
ziel.write_bytes(remove(quelle.read_bytes(), session=new_session("u2net")))
