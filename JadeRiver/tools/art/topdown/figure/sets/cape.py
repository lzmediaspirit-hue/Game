"""Capes (parts.json `cape`; side view: cape_solid, cape_tattered), cast by figure/kinds/back.py: a sheet from the
shoulders down the back, trailing the pose's drag; the tattered one ends in rags."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import back as K
from ..render import Look

KIND = "cape"

CAPES = {"solid": {"length": 13.5, "width": 4.4, "ragged": False},
         "tattered": {"length": 11.0, "width": 4.0, "ragged": True}}
COLOURS = {"solid": P.CAPE_GREEN, "tattered": P.CAPE_GREY}


def items(L: dict) -> list:
    return [Item("cape", name, L["cape"][name], lambda sk, spec=spec: K.solids(sk, spec), Look(line_tone={"cape": 0}),
                 {"none": {"cape": COLOURS[name]}}, ["cape"])
            for name, spec in CAPES.items()]
