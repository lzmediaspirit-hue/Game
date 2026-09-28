"""Shoes and boots (parts.json `shoes`; the boots slot's looks), cast by figure/kinds/feet.py."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import feet as K
from ..render import Look

KIND = "shoes"

SHOES = {
    # Cloth shoes (the starting pair): dark brown, a tan upper.
    "slippers": {"boot": 0.0},
    # Jade greaves: navy shoes under pale steel plates to mid-shin.
    "folded": {"boot": 3.6, "cuff": "plate"},
    # Cloud boots: brown boots with a tan cuff.
    "boots": {"boot": 3.0, "cuff": "top"},
}
COLOURS = {"slippers": {"sole": P.SHOE, "top": P.SHOE_TOP}, "boots": {"sole": P.SHOE, "top": P.SHOE_TOP},
           "folded": {"sole": P.NAVY, "top": P.STEEL, "plate": P.STEEL}}


def items(L: dict) -> list:
    return [Item("shoes", name, L["shoes"][name], lambda sk, spec=spec: K.solids(sk, spec),
                 Look(highlight=("plate",)), {"none": dict(COLOURS[name])}, ["sole", "top", "plate"])
            for name, spec in SHOES.items()]
