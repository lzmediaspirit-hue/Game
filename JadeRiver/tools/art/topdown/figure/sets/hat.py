"""Hats (parts.json `hat`; side view: hat_straw, headband, tied, guan, weimao), cast by figure/kinds/head.py:

  straw     a wide cone of plaited straw with a jade band
  headband  a teal cloth band round the brow, gold studs in front
  tied      a thin teal band tied at the back, its two ends trailing
  guan      a small jade crown on the top knot, gold-rimmed, a gold pin through it
  weimao    a dark wide-brimmed hat with a red band and a pale veil hanging from the brim
"""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import head as K
from ..render import Look

KIND = "hat"

HATS = {"straw": {"kind": "cone", "brim": 8.2, "height": 5.6},
        "headband": {"kind": "band", "at": 0.30, "half": 0.13, "grow": 0.95, "studs": True},
        "tied": {"kind": "band", "at": 0.36, "half": 0.07, "grow": 0.9, "tails": True},
        "guan": {"kind": "crown"},
        "weimao": {"kind": "veil", "brim": 8.0}}
COLOURS = {"straw": P.STRAW, "band": P.RIBBON, "cloth": P.TEAL_CLOTH, "stud": P.GOLD, "jade": P.JADE_STONE,
           "gold": P.GOLD, "felt": P.FELT, "veil": P.VEIL}


# How the hats' materials resolve at 38 px (decision 42; render.MATS): a cloth band a pixel wide stays one unbroken
# line; the guan is a crown of jade a few pixels across, so its jade outvotes the gold rim, cap and pin round it (the
# pin a line a pixel wide, not a thin part that may take two).
MATS = {"cloth": {"line": True}, "jade": {"weight": 2.2, "line": True},
        "gold": {"weight": 1.0, "thin": False, "line": True}}


def items(L: dict) -> list:
    out = []
    for name, spec in HATS.items():
        pal = dict(COLOURS, band=P.RED_BAND) if name == "weimao" else COLOURS
        out.append(Item("hat", name, L["hat"][name], lambda sk, spec=spec: K.solids(sk, spec),
                        Look(highlight=("straw", "stud", "jade", "gold"), mats=MATS), {"none": pal}, list(COLOURS)))
    return out
