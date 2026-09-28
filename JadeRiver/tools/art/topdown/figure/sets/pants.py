"""Trousers (parts.json `pants`; the trousers slot's looks), undyed and in every dye, cast by figure/kinds/legs.py."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import legs as K
from ..render import Look

KIND = "pants"

PANTS = {
    # Silk trousers (the starting pair): loose jade-teal legs gathered at the ankle by grey wraps.
    "loose": {"fit": (1.05, 1.0, 0.95), "bands": [(-1.6, 0.0)], "band": "wrap"},
    # Travel pants: straight teal legs, a grey band under the knee.
    "straight": {"fit": (0.8, 0.75, 0.7), "bands": [(0.6, 1.8)], "band": "wrap"},
    # Leg wraps: teal legs bound with pale green wraps down the shin.
    "cuffed": {"fit": (0.9, 0.75, 0.6), "bands": [(1.0, 2.0), (2.6, 3.6), (-1.4, 0.0)], "band": "wrap"},
    # Scholar pants: plain black, a little wide.
    "scholar": {"fit": (0.95, 0.9, 0.9), "bands": [], "band": "wrap"},
    # Martial pants: navy, tied close at the ankle.
    "martial": {"fit": (1.0, 0.85, 0.55), "bands": [(-1.0, 0.0)], "band": "wrap"},
}
# Each look's undyed cloth and its wraps (the side view's sheets).
CLOTH = {"loose": (P.TROUSERS, P.WRAP), "straight": (P.TRAVEL, P.WRAP), "cuffed": (P.TRAVEL, P.LEG_WRAP),
         "scholar": (P.INK_CLOTH, P.WRAP), "martial": (P.NAVY, P.WRAP)}


def items(L: dict) -> list:
    out = []
    for name, spec in PANTS.items():
        base, wrap = CLOTH[name]
        pal = {("none" if d is None else d): {"cloth": P.garment(base, d)["cloth"], "wrap": wrap}
               for d in [None] + P.dye_names()}
        out.append(Item("pants", name, L["pants"][name], lambda sk, spec=spec: K.solids(sk, spec),
                        Look(line_tone={"cloth": 0}), pal, ["cloth", "wrap"]))
    return out
