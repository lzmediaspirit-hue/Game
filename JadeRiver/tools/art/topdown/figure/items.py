"""Every drawn item: its category, how it is cast from a skeleton, how it shades, and its palettes (dyes, hair colours).

Layer order (the side view's, redesign plan §1.4): body, shoes, trousers, shirt, cape, hair, hat, weapon, within each
of four bands: back (behind the chest: the far arm, a tail behind the neck, a blade behind the back), mid (the trunk,
legs, clothes), head (the body's head and neck, over the shirt's collar and under the hair) and front (an arm or blade
in front of the chest). A section's z is its band's base plus its category's order.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import body as B
from . import garments as G
from . import hair as HR
from . import palettes as P
from . import weapons as WP
from .render import Look

ORDER = {"body": 10, "shoes": 20, "pants": 30, "shirt": 40, "cape": 50, "hair": 60, "hat": 65, "weapon": 70}
BAND_BASE = {"back": 0, "mid": 100, "head": 155, "front": 200}


def z_of(cat: str, band: str) -> int:
    return BAND_BASE[band] if band == "head" else BAND_BASE[band] + ORDER[cat]


def _flat(col):
    return [col] * 5


EYE_MATS = {"eye_dark": _flat(P.EYE_DARK), "iris": _flat(P.IRIS), "iris_light": _flat(P.IRIS_LIGHT),
            "eye_white": _flat(P.EYE_WHITE), "mouth": _flat(P.MOUTH)}
EDGE = [P.BLADE[1], P.BLADE[2], P.BLADE[3], P.BLADE[4], P.BLADE[4]]
CORD = P.ramp("2b1c1d", "411e05", "62351c", "7d4a2a", "9a6440")
SMEAR = P.ramp("5ba69b", "8fd0bf", "b6e6d6", "d6f5e6", "f2fff8")       # a cut's smear: pale jade light (the water's ramp)


class Item:
    def __init__(self, cat, name, label, cast, look, palettes, mats, stand_in=None):
        self.cat = cat
        self.name = name
        self.label = label
        self.cast = cast            # skeleton -> solids
        self.look = look
        self.palettes = palettes    # variant -> {material: ramp}
        self.mats = mats            # the materials in id order
        self.key = cat + "_" + name

    def variants(self) -> list:
        return list(self.palettes.keys())


def _labels() -> dict:
    """The side view's names for every look (parts.json), so both views call an item the same."""
    parts = json.loads((Path(__file__).resolve().parents[4] / "data/parts.json").read_text())
    return {cat: {k: v.get("label", k) for k, v in parts[cat].items() if isinstance(v, dict)}
            for cat in ("body", "hair", "shirt", "pants", "shoes", "hat", "cape", "weapon")}


# The garments drawn, with the undyed colours of their dyeable cloth (the side view's sheets).
SHIRT_CLOTH = {"disciple": P.TUNIC, "vneck": P.GREY, "cardigan": P.ROBE, "scholar": P.GREY, "sleeveless": P.ROBE}
PANTS_CLOTH = {"loose": (P.TROUSERS, P.WRAP), "straight": (P.TRAVEL, P.WRAP), "cuffed": (P.TRAVEL, P.LEG_WRAP),
               "scholar": (P.INK_CLOTH, P.WRAP), "martial": (P.NAVY, P.WRAP)}
SHOE_LOOK = {"slippers": {"sole": P.SHOE, "top": P.SHOE_TOP}, "boots": {"sole": P.SHOE, "top": P.SHOE_TOP},
             "folded": {"sole": P.NAVY, "top": P.STEEL, "plate": P.STEEL}}


def catalog() -> list:
    L = _labels()
    dyes = [None] + P.dye_names()
    items = []
    items.append(Item("body", "light", L["body"]["light"], B.solids,
                      Look(highlight=("skin",), flat={m: 2 for m in EYE_MATS}, line_tone={"skin": 1}),
                      {"none": dict(EYE_MATS, skin=P.SKIN)}, ["skin"] + list(EYE_MATS)))
    for st in HR.STYLES:
        pal = {str(i): {"hair": P.HAIR[i], "ribbon": P.RIBBON, "pin": P.GOLD} for i in range(len(P.HAIR))}
        items.append(Item("hair", st, L["hair"][st], lambda sk, st=st: HR.solids(sk, st),
                          Look(highlight=("hair", "pin", "ribbon"), line_tone={"hair": 0}), pal, ["hair", "ribbon", "pin"]))
    for name, base in SHIRT_CLOTH.items():
        pal = {}
        for d in dyes:
            g = P.garment(base, d)
            if g["panel"] is None:
                g["panel"] = P.PANEL
            pal["none" if d is None else d] = dict(g, trim=P.GOLD, belt=P.BELT, accent=P.ACCENT)
        items.append(Item("shirt", name, L["shirt"][name], lambda sk, n=name: G.shirt(sk, n),
                          Look(highlight=("trim", "panel"), line_tone={"cloth": 0}), pal,
                          ["cloth", "panel", "edge", "trim", "belt", "accent"]))
    for name, (base, wrap) in PANTS_CLOTH.items():
        pal = {("none" if d is None else d): {"cloth": P.garment(base, d)["cloth"], "wrap": wrap} for d in dyes}
        items.append(Item("pants", name, L["pants"][name], lambda sk, n=name: G.pants(sk, n), Look(line_tone={"cloth": 0}),
                          pal, ["cloth", "wrap"]))
    for name, look in SHOE_LOOK.items():
        items.append(Item("shoes", name, L["shoes"][name], lambda sk, n=name: G.shoes(sk, n),
                          Look(highlight=("plate",)), {"none": dict(look)}, ["sole", "top", "plate"]))
    hat_pal = {"straw": P.STRAW, "band": P.RIBBON, "cloth": P.TEAL_CLOTH, "stud": P.GOLD, "jade": P.JADE_STONE,
               "gold": P.GOLD, "felt": P.FELT, "veil": P.VEIL}
    for name in G.HATS:
        pal = dict(hat_pal, band=P.RED_BAND) if name == "weimao" else hat_pal
        items.append(Item("hat", name, L["hat"][name], lambda sk, n=name: G.hat(sk, n),
                          Look(highlight=("straw", "stud", "jade", "gold")), {"none": pal}, list(hat_pal)))
    for name, col in (("solid", P.CAPE_GREEN), ("tattered", P.CAPE_GREY)):
        items.append(Item("cape", name, L["cape"][name], lambda sk, n=name: G.cape(sk, n), Look(line_tone={"cape": 0}),
                          {"none": {"cape": col}}, ["cape"]))
    items.append(Item("weapon", "gauntlets", L["weapon"]["gauntlets"], G.gauntlets,
                      Look(highlight=("steel", "bronze"), ink=("steel", "bronze")),
                      {"none": {"steel": P.STEEL, "bronze": P.BRONZE}}, ["steel", "bronze"]))
    for name in ("dagger", "sword", "spear", "staff"):
        pal = {"blade": P.BLADE, "edge": EDGE, "gold": P.GOLD, "hilt": P.HILT, "shaft": P.SHAFT, "cord": CORD, "smear": SMEAR}
        items.append(Item("weapon", name, L["weapon"][name], lambda sk, n=name: WP.solids(sk, n),
                          Look(highlight=("blade", "edge", "gold", "shaft"), flat={"smear": 2}, glow=("smear",),
                               line_tone={"smear": 0}, ink=("blade", "edge", "gold", "hilt", "shaft", "cord")),
                          {"none": pal}, list(pal)))
    return items
