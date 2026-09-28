"""Every drawn item: its category, how it is cast from a skeleton, how it shades, and its palettes (dyes, hair colours).

Layer order (the side view's, redesign plan §1.4): body, shoes, trousers, shirt, gauntlets, hair, weapon, within each
of four bands: back (behind the chest: the far arm, a tail behind the neck, a blade behind the back), mid (the trunk,
legs, clothes), head (the body's head and neck, over the shirt's collar and under the hair) and front (an arm or blade
in front of the chest). A section's z is its band's base plus its category's order.
"""
from __future__ import annotations

from . import body as B
from . import garments as G
from . import hair as HR
from . import palettes as P
from . import weapons as WP
from .render import Look

ORDER = {"body": 10, "shoes": 20, "pants": 30, "shirt": 40, "gauntlets": 50, "hair": 60, "weapon": 70}
BAND_BASE = {"back": 0, "mid": 100, "head": 150, "front": 200}


def z_of(cat: str, band: str) -> int:
    return BAND_BASE[band] if band == "head" else BAND_BASE[band] + ORDER[cat]


def _flat(col):
    return [col] * 5


EYE_MATS = {"eye_dark": _flat(P.EYE_DARK), "iris": _flat(P.IRIS), "iris_light": _flat(P.IRIS_LIGHT),
            "eye_white": _flat(P.EYE_WHITE), "mouth": _flat(P.MOUTH)}
EDGE = [P.BLADE[1], P.BLADE[2], P.BLADE[3], P.BLADE[4], P.BLADE[4]]
CORD = P.ramp("2b1c1d", "411e05", "62351c", "7d4a2a", "9a6440")


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


def catalog() -> list:
    items = []
    items.append(Item("body", "light", "Light", B.solids,
                      Look(highlight=("skin",), flat={m: 2 for m in EYE_MATS}, line_tone={"skin": 1}),
                      {"none": dict(EYE_MATS, skin=P.SKIN)}, ["skin"] + list(EYE_MATS)))
    labels = {"short_knot": "Sage knot", "topknot": "Daoist knot", "ponytail": "Jade tail", "high_pony": "Sky ponytail",
              "long_tied": "Long silk tie", "flowing": "Flowing tail"}
    for st in HR.STYLES:
        pal = {str(i): {"hair": P.HAIR[i], "ribbon": P.RIBBON, "pin": P.GOLD} for i in range(len(P.HAIR))}
        items.append(Item("hair", st, labels[st], lambda sk, st=st: HR.solids(sk, st),
                          Look(highlight=("hair", "pin", "ribbon"), line_tone={"hair": 0}), pal, ["hair", "ribbon", "pin"]))
    for name, label in (("disciple", "Disciple tunic"),):
        pal = {"none": {"cloth": P.TUNIC, "trim": P.GOLD, "belt": P.BELT}}
        for d in P.dye_names():
            pal[d] = {"cloth": P.dye_ramp(d), "trim": P.GOLD, "belt": P.BELT}
        items.append(Item("shirt", name, label, lambda sk, n=name: G.shirt(sk, n),
                          Look(highlight=("trim",), line_tone={"cloth": 0}), pal, ["cloth", "trim", "belt"]))
    for name, label in (("loose", "Silk trousers"),):
        pal = {"none": {"cloth": P.TROUSERS, "wrap": P.WRAP}}
        for d in P.dye_names():
            pal[d] = {"cloth": P.dye_ramp(d), "wrap": P.WRAP}
        items.append(Item("pants", name, label, lambda sk, n=name: G.pants(sk, n), Look(line_tone={"cloth": 0}), pal,
                          ["cloth", "wrap"]))
    for name, label in (("slippers", "Cloth shoes"),):
        items.append(Item("shoes", name, label, lambda sk, n=name: G.shoes(sk, n), Look(),
                          {"none": {"sole": P.SHOE, "top": P.SHOE_TOP}}, ["sole", "top"]))
    items.append(Item("weapon", "gauntlets", "Gauntlets", G.gauntlets,
                      Look(highlight=("steel", "bronze"), ink=("steel", "bronze")),
                      {"none": {"steel": P.STEEL, "bronze": P.BRONZE}}, ["steel", "bronze"]))
    for name, label in (("dagger", "Short blade"), ("sword", "Spirit jian"), ("spear", "Jade spear")):
        pal = {"blade": P.BLADE, "edge": EDGE, "gold": P.GOLD, "hilt": P.HILT, "shaft": P.SHAFT, "cord": CORD}
        items.append(Item("weapon", name, label, lambda sk, n=name: WP.solids(sk, n),
                          Look(highlight=("blade", "edge", "gold", "shaft"), ink=("blade", "edge", "gold", "hilt", "shaft", "cord")),
                          {"none": pal}, list(pal)))
    return items
