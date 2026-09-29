"""The heavy sabre family (weapon_families.json `heavy_sabre`; parts.json weapon `sabre`): the side view's broad dao of
grey steel with a pale edge, a bronze guard and pommel and a dark grip, cast by figure/kinds/sabre.py. Its cuts
(swing_1-3) leave a heavy crescent of pale jade light, brightest along the point's path.

The side view's sabre is steel and bronze, not the jian's jade steel and gold, so its ramps are the gauntlets' steel and
bronze (palettes.STEEL, BRONZE); the edge is the steel a step paler, a ramp only this set uses.
"""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import sabre as K
from ..render import BLADE_EDGE, Look

KIND = "weapon_heavy_sabre"
FAMILY = "heavy_sabre"
SPEC = {"blade": 17.5, "width": 1.12, "belly": 1.5, "curve": 1.5, "thick": 0.42, "face": 0.5, "hilt": 4.2,
        "guard": 2.2}

STEEL_EDGE = P.ramp("4e545e", "808892", "bac0c6", "eceef0", "eceef0")   # the cutting edge's bevel


def items(L: dict) -> list:
    pal = {"blade": P.STEEL, "edge": STEEL_EDGE, "bronze": P.BRONZE, "hilt": P.HILT,
           "smear": P.SMEAR, "smear_hi": P.SMEAR, "smear_mid": P.SMEAR, "smear_lo": P.SMEAR}
    smear = ("smear", "smear_hi", "smear_mid", "smear_lo")
    # The flat is the side view's mid grey, its dark band in shade and its light grey only where the sun strikes it
    # full (never the steel's core shadow, which is near the ink's), a glint only from the rim, which stays cool on the
    # bare steel (a warm one turns a flat seen from above cream); the edge's bevel takes the usual light. The broad blade
    # is no thin line: it is solid from half a pixel, as a body is.
    look = Look(highlight=("blade", "edge", "bronze"), flat={"smear": 3, "smear_hi": 4, "smear_mid": 2, "smear_lo": 1},
                thresholds={"blade": (-2.0, -0.3, 0.75, 2.0)}, glow=smear, line_tone={m: 0 for m in smear},
                ink=("blade", "edge", "bronze", "hilt"),
                mats={"blade": {"thin": False, "rim": 0.08}, "edge": dict(BLADE_EDGE["edge"], rim=0.08)})
    return [Item("weapon", "sabre", L["weapon"]["sabre"], lambda sk: K.solids(sk, SPEC), look, {"none": pal},
                 list(pal))]
