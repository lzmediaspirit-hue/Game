"""The study's options (decision 42) and what each draws.

  A  today's figure: the game's own sheets, untouched (nothing is built for it)
  B  the same size, drawn better: 0.92 art px a unit (38 px sole to crown) on the world's 640x360 grid
  C  twice the density: 1.84 px a unit (76 px) on a 1280x720 grid, over the world shown x2
  D  a larger figure at the world's density: 1.15 px a unit (48 px), no mixed pixel scales

The subset: the player's outfit (the Daoist knot, the disciple tunic, silk trousers, cloth shoes, the jian) in idle,
walk, run and the jian's rising cut, and the villagers of the two scenes in their own outfits, idle; S and SE drawn
(SW mirrored; any other facing shows S). The player's pieces are the hand-tuned ones (looks.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import hifi  # noqa: E402

OPTIONS = {
    # name: (grid, the face's glyph set, the label)
    "B": (lambda: hifi.Grid(0.92, 128, 112, 64, 80, 4), "b", "B · same size (38 px), drawn better"),
    "C": (lambda: hifi.Grid(1.84, 256, 224, 128, 160, 3), "c", "C · double density (76 px on the 1280x720 grid)"),
    "D": (lambda: hifi.Grid(1.15, 160, 140, 80, 100, 4), "d", "D · larger figure (48 px) at the world's density"),
}
# Pixels of the figure per art px of the world: C's are drawn at half size.
DENSITY = {"B": 1, "C": 2, "D": 1}

PLAYER = {"body": "light", "hair": "topknot", "hair_color": 0, "shirt": "disciple", "pants": "loose",
          "shoes": "slippers", "hat": "none", "cape": "none", "weapon": "sword"}
# The villagers the scenes show (data/npcs.json ids): the village square and Jade Gate Street.
NPCS = ["uncle_guo", "little_dou", "washer_mei", "shen_lian_npc", "jade_steward", "jade_deacon", "jade_disciple_a",
        "jade_disciple_b"]

ACTIONS = {"idle": ["s", "se"], "walk": ["s", "se"], "run": ["s", "se"], "swing_1": ["s", "se"]}
NPC_ACTIONS = ["idle"]
DIRS = ["s", "se"]
