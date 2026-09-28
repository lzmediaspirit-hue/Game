"""The figure's colours: five-step ramps (deep, shadow, base, light, highlight) per material, taken from the side-view
character so the top-down figure is the same person: the skin, eyes and hair of the body and head sheets, the
disciple tunic's navy and gold, the silk trousers' teal, the cloth shoes' browns, the weapons' jade steel, gold guard
and hilts, and the gauntlets' steel and bronze (tools/art/bake_gauntlets.py). Garment dyes are the side view's own
four-stop ramps (tools/art/bake_dyes.py DYES), hair colours follow the creator's six (parts.json `_colors.hair`).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # tools/art
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # tools/art/topdown

from bake_dyes import DYES  # noqa: E402  the side view's garment dyes, one source for both views

from palette import LINE, LINE_SOFT, c  # noqa: E402  tools/art/topdown/palette.py


def ramp(*hexes: str) -> list:
    return [c(h) for h in hexes]


# The body (side view: body_light_1/2/3 sheets).
SKIN = ramp("99423c", "cc8665", "e4a47c", "f9d5ba", "faece7")
EYE_WHITE = c("f2f7f8")
IRIS = c("5686ae")
IRIS_LIGHT = c("57cee4")
EYE_DARK = c("2a3c49")
MOUTH = c("b0604c")
BLUSH = c("f0b49a")

# Hair: the creator's six colours in parts.json order, as the side view shows them (dark, muted), lifted a step for the
# brighter top-down world. Tone 2 is the colour's body.
HAIR_NAMES = ["Raven", "Silver", "Crimson", "Violet", "Azure", "Ash"]
HAIR = [
    ramp("1b1f25", "2a2e37", "3d424e", "565c6a", "7a8291"),
    ramp("3a4052", "5d6680", "8c93a8", "bcc3d0", "e6eaf0"),
    ramp("2a0c14", "42131f", "5e1a2b", "7e2a3a", "a04a55"),
    ramp("1e1030", "2f1a47", "43285f", "5c3a7c", "7e5aa0"),
    ramp("0c2130", "143142", "1d465c", "2a6078", "437f98"),
    ramp("111419", "1a1e24", "262b33", "353b45", "4b525e"),
]
RIBBON = ramp("0b3a33", "015548", "12705c", "2c9e8f", "67d6bd")        # the jade hair ribbon
GOLD = ramp("6e4a1c", "a8772f", "d1a64d", "e5b84c", "ffe6a1")          # pins, trim, guards

# The starting clothes (side view: shirt_disciple, pants_loose, shoes_slippers).
TUNIC = ramp("0f1d27", "16303e", "1f4256", "2c5a72", "3f7590")         # the disciple tunic's navy teal
BELT = ramp("111317", "181922", "23252e", "32353f", "464a55")
TROUSERS = ramp("062c2b", "074547", "0b5d58", "0e7c70", "2a9a88")      # silk trousers, jade teal
WRAP = ramp("1f2124", "2c2f33", "3c3f43", "50545a", "6a6f75")           # their ankle wraps
SHOE = ramp("2e2013", "4d371e", "5c4127", "7d674c", "9a8058")
SHOE_TOP = ramp("6e5030", "8a6d3a", "b08d4b", "cdab64", "e2c98a")

# Weapons (side view: weapon_sword / dagger / spear sheets) and the training gauntlets.
BLADE = ramp("273841", "467075", "5ba69b", "a0d3c1", "e8f2dc")
HILT = ramp("1d131e", "2b1c1d", "411e05", "62351c", "7d4a2a")
SHAFT = ramp("62351c", "a08462", "cdbfa2", "e8f2dc", "f6faf0")
STEEL = ramp("1c1e24", "4e545e", "808892", "bac0c6", "eceef0")
BRONZE = ramp("4a2a14", "784826", "b0703a", "dea85c", "f2cf8e")

# Which materials a dye recolours, per garment category (the side view dyes shirts and trousers, parts.json _dyes).
DYEABLE = {"shirt": ["cloth"], "pants": ["cloth"]}


def dye_ramp(name: str) -> list:
    """A side-view dye's four stops as a five-step ramp: its darkest stop, the three others, and a highlight half way
    from its lightest stop to white."""
    stops = [c(h) for h in DYES[name]]
    lt = stops[3]
    hi = tuple(int(round(v + (255 - v) * 0.35)) for v in lt[:3]) + (255,)
    return [stops[0], stops[1], stops[2], stops[3], hi]


def dye_names() -> list:
    return list(DYES.keys())


__all__ = ["LINE", "LINE_SOFT", "c", "ramp", "dye_ramp", "dye_names"]
