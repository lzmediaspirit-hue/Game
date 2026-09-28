"""Shirts, coats and robes (parts.json `shirt`; the robe slot's looks), undyed and in every dye, cast by
figure/kinds/torso.py. Each look's spec after the side-view sheet (in the comment beside it), and its undyed cloth."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import torso as K
from ..render import Look

KIND = "shirt"

SHIRTS = {
    # Disciple tunic (the starting shirt): navy teal, a crossed collar edged in gold, a dark belt with a gold buckle, a
    # short skirt to mid-thigh with a gold hem.
    "disciple": {"collar": "cross", "trim": "trim", "sleeve": "wrist", "cuff": "trim", "hem": 3.6, "flare": 0.8,
                 "hem_trim": True, "belt": "belt", "buckle": True},
    # Cloud tunic: grey sleeves and shoulders, a white front panel crossed by a blue and gold stripe, a white apron to the
    # knee, a dark belt.
    "vneck": {"collar": "vee", "trim": "cloth", "panel": "band", "sleeve": "wrist", "cuff": "cloth", "hem": 3.2,
              "flare": 0.7, "apron": 6.4, "belt": "belt"},
    # Sect robe: a long jade robe to the ankle, a V collar, a gold cord knotted at the waist with its ends hanging.
    "cardigan": {"collar": "vee", "trim": "edge", "sleeve": "wrist", "cuff": "edge", "hem": 12.4, "flare": 1.8,
                 "belt": None, "sash": True},
    # Scholar coat: grey sleeves, a white chest with a blue cloud emblem, a black belt, to the hip.
    "scholar": {"collar": "vee", "trim": "cloth", "panel": "emblem", "sleeve": "wrist", "cuff": "cloth", "hem": 3.0,
                "flare": 0.6, "belt": "belt"},
    # Wanderer: a sleeveless jade vest with gold dots, a dark belt, to the hip; the arms bare.
    "sleeveless": {"collar": "vee", "trim": "edge", "sleeve": "none", "hem": 3.0, "flare": 0.6, "belt": "belt",
                   "dots": True},
}
# The undyed colour of each look's dyeable cloth (the side view's sheets).
CLOTH = {"disciple": P.TUNIC, "vneck": P.GREY, "cardigan": P.ROBE, "scholar": P.GREY, "sleeveless": P.ROBE}


def items(L: dict) -> list:
    out = []
    for name, spec in SHIRTS.items():
        pal = {}
        for d in [None] + P.dye_names():
            g = P.garment(CLOTH[name], d)
            if g["panel"] is None:
                g["panel"] = P.PANEL
            pal["none" if d is None else d] = dict(g, trim=P.GOLD, belt=P.BELT, accent=P.ACCENT)
        out.append(Item("shirt", name, L["shirt"][name], lambda sk, spec=spec: K.solids(sk, spec),
                        Look(highlight=("trim", "panel"), line_tone={"cloth": 0}), pal,
                        ["cloth", "panel", "edge", "trim", "belt", "accent"]))
    return out
