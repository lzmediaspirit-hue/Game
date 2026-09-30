"""A drawn item: its category, how it is cast from a skeleton, how it shades, and its palettes (dyes, hair colours).
The items themselves are declared by the layer sets (sets/): `catalog()` gathers them.

Layer order (the side view's, redesign plan §1.4): body, shoes, trousers, shirt, cape, hair, hat, weapon, and the
work tools over them (decision 44: the tool a worker holds, sets/tool.py), within each of four bands: back (behind the chest: the far arm, a tail behind the neck, a blade behind the back), mid (the trunk,
legs, clothes), head (the body's head and neck, over the shirt's collar and under the hair) and front (an arm or blade
in front of the chest). A section's z is its band's base plus its category's order.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import palettes as P
from .render import BLADE_EDGE, Look

ORDER = {"body": 10, "shoes": 20, "pants": 30, "shirt": 40, "cape": 50, "hair": 60, "hat": 65, "weapon": 70, "tool": 75}
BAND_BASE = {"back": 0, "mid": 100, "head": 155, "front": 200}
ROOT = Path(__file__).resolve().parents[4]


def z_of(cat: str, band: str) -> int:
    return BAND_BASE[band] if band == "head" else BAND_BASE[band] + ORDER[cat]


class Item:
    def __init__(self, cat, name, label, cast, look, palettes, mats):
        self.cat = cat
        self.name = name
        self.label = label
        self.cast = cast            # skeleton -> solids
        self.look = look
        self.palettes = palettes    # variant -> {material: ramp}
        self.mats = mats            # the materials in id order
        self.key = cat + "_" + name
        self.kind = ""              # the set that draws it (sets/<kind>.py), filled in by catalog()
        self.actions = None         # a tool's own actions (sets/tool.py ACTIONS): it is hidden in every other

    def variants(self) -> list:
        return list(self.palettes.keys())


def labels() -> dict:
    """The side view's names for every look (parts.json), so both views call an item the same."""
    parts = json.loads((ROOT / "data/parts.json").read_text())
    return {cat: {k: v.get("label", k) for k, v in parts[cat].items() if isinstance(v, dict)}
            for cat in ("body", "hair", "shirt", "pants", "shoes", "hat", "cape", "weapon")}


def steel_weapon(name: str, label: str, cast) -> Item:
    """A weapon of jade steel, gold and a dark hilt (the side view's short blade, jian, spear and staff): the ramps and
    shading every such weapon shares, its cut smear a sheet of pale jade light with no ink round it."""
    pal = {"blade": P.BLADE, "edge": P.EDGE, "gold": P.GOLD, "hilt": P.HILT, "shaft": P.SHAFT, "cord": P.CORD,
           "smear": P.SMEAR}
    return Item("weapon", name, label, cast,
                Look(highlight=("blade", "edge", "gold", "shaft"), flat={"smear": 2}, glow=("smear",),
                     line_tone={"smear": 0}, ink=("blade", "edge", "gold", "hilt", "shaft", "cord"), mats=BLADE_EDGE),
                {"none": pal}, list(pal))


def catalog(kinds: list | None = None) -> list:
    """Every item of the sets named (all when None), each marked with its set."""
    from . import sets
    L = labels()
    found = sets.discover()
    out = []
    for kind in (kinds if kinds is not None else list(found)):
        for it in found[kind].items(L):
            it.kind = kind
            if it.cat == "weapon":
                it.cast = _stowable(it.cast)
            out.append(it)
    return out


def _stowable(cast):
    """A weapon's cast that draws nothing where the pose puts the weapon away (decision 44: a work action's hands hold
    its tool; the build writes the explicit hidden entry)."""
    return lambda sk: [] if (sk.weapon or {}).get("stow") else cast(sk)
