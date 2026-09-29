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
PUPIL = c("1c2632")      # decision 43: the pupil, a step under the lash line, in the 3-wide eye of the 46 px figure
# The face's small marks (decision 42): a mouth a step deeper than the lips' side-view pink so one pixel reads, a warm
# brow, the nose's shade in three quarters, and a touch of blush under the eye.
MOUTH = c("934536")
BLUSH = c("f3a58c")
BROW = c("3a2b2c")
NOSE = c("c98062")

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

# The creator's other clothes, worn by the villagers (side view: shirt_vneck / cardigan / scholar / sleeveless,
# pants_straight / cuffed / scholar / martial, shoes_folded / boots, hat_straw).
GREY = ramp("3a3e44", "5a6068", "7e858c", "a3a9ae", "c8ccce")          # the cloud tunic's and scholar coat's sleeves
PANEL = ramp("8e9496", "b8bcbc", "dcdfda", "f0f1ec", "fbfbf6")         # their white front panels
ACCENT = ramp("142460", "223a8c", "3354b4", "5a7ad0", "8ea8e6")        # the blue stripe and cloud emblem
ROBE = ramp("083a32", "0c5446", "13705c", "1f8e74", "48b494")          # the sect robe's and the vest's jade
TRAVEL = TROUSERS                                                       # travel pants and leg wraps: the same teal
LEG_WRAP = ramp("2a5040", "3f6e56", "5a9070", "7cb08a", "a6d0aa")      # the leg wraps' pale green
INK_CLOTH = ramp("0d0f13", "16191f", "21252d", "2e333d", "424856")     # scholar pants
NAVY = ramp("0e1830", "162648", "21386a", "30508e", "4f72b0")          # martial pants, the greaves' shoes
STRAW = ramp("5e4520", "8a6a30", "b8924a", "d8b86a", "eed89a")         # the straw hat
TEAL_CLOTH = ramp("023a36", "04525a", "02645f", "2a8a80", "58b0a4")    # the headband and the tied band
JADE_STONE = ramp("0e4a42", "125e56", "2c9e8f", "5cc4b0", "8ae6cc")    # the guan's jade
FELT = ramp("161a22", "20242c", "282c36", "3e4452", "5a6272")          # the weimao's dark felt
RED_BAND = ramp("4e1414", "6e1c1c", "a42e2a", "c8483e", "e0766a")      # its band
VEIL = ramp("56606e", "687080", "9aa2ae", "c4cad2", "e6eaee")          # its gauze
CAPE_GREEN = ramp("02302c", "054b45", "0d6a5e", "1f8a78", "4aa894")    # the solid cape
CAPE_GREY = ramp("121418", "1b1f26", "21262e", "30363f", "474f5a")     # the tattered cape

# Weapons (side view: weapon_sword / dagger / spear sheets) and the training gauntlets.
BLADE = ramp("273841", "467075", "5ba69b", "a0d3c1", "e8f2dc")
HILT = ramp("1d131e", "2b1c1d", "411e05", "62351c", "7d4a2a")
SHAFT = ramp("62351c", "a08462", "cdbfa2", "e8f2dc", "f6faf0")
STEEL = ramp("1c1e24", "4e545e", "808892", "bac0c6", "eceef0")
BRONZE = ramp("4a2a14", "784826", "b0703a", "dea85c", "f2cf8e")
EDGE = [BLADE[1], BLADE[2], BLADE[3], BLADE[4], BLADE[4]]                 # a blade's pale edge
CORD = ramp("2b1c1d", "411e05", "62351c", "7d4a2a", "9a6440")             # the spear's cord winding
SMEAR = ramp("5ba69b", "8fd0bf", "b6e6d6", "d6f5e6", "f2fff8")            # a cut's smear: pale jade light (the water's ramp)

# Which materials a dye recolours, per garment category (the side view dyes shirts and trousers, parts.json _dyes):
# `cloth` takes the dye's ramp, `panel` a step lighter and `edge` a step darker, as the side view's luminance bake maps
# a garment's lighter and darker parts along the dye.
DYEABLE = {"shirt": ["cloth", "panel", "edge"], "pants": ["cloth"]}


def _mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a[:3], b[:3])) + (255,)


def lighter(r: list) -> list:
    return [r[1], r[2], r[3], r[4], _mix(r[4], (255, 255, 255), 0.45)]


def darker(r: list) -> list:
    return [_mix(r[0], (0, 0, 0), 0.35), r[0], r[1], r[2], r[3]]


def garment(ramp_: list, dye: str | None) -> dict:
    """A garment's dyeable materials for the undyed original (`ramp_`) or a side-view dye."""
    base = ramp_ if dye is None else dye_ramp(dye)
    return {"cloth": base, "panel": lighter(base) if dye is not None else None, "edge": darker(base)}


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
