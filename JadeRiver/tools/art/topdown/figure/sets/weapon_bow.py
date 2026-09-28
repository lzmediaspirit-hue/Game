"""The bow family (weapon_families.json `bow`; parts.json weapon `bow`): the spirit bow, a recurve wuxia bow of gold
limbs with dark ears and a dark wrapped grip, strung with pale jade (the side view's colours, art/weapon_bow_*: gold
d1a64d edged in dark 2b1c1d, the string a0d3c1), its arrow a gold shaft with a jade-steel head and red fletching (the
side view's arrow sheet), cast by figure/kinds/bow.py. It is held in the left hand; its shot is `bow_draw`."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import bow as K
from ..render import Look

KIND = "weapon_bow"
FAMILY = "bow"
SPEC = {"half": 13.0, "grip": 1.3, "bend": 3.0, "draw_bend": 2.4, "draw_in": 0.1, "ear": (1.9, 0.78),
        "limb": (0.66, 0.46), "string": 0.52, "arrow": (3.2, 1.6), "sling": ((-3.4, 0.3, 0.6), (3.4, 0.2, 0.3))}

# The side view's gold limbs (P.GOLD), their dark ears and grip wrap (the bow's dark edge, 2b1c1d, as a ramp), the
# arrow's shaft and red fletching. The string is pale jade light (the side view's a0d3c1): flat, with no edge round it
# (step 5 clear) so it stays one pixel wide; humming, the second string a step fainter.
DARK = P.ramp("140c0e", "1d131e", "2b1c1d", "4a3024", "6a4630")
SHAFT = P.ramp("5a3a1a", "8a6230", "b08a4a", "d1a64d", "e8cc80")
FLETCH = P.ramp("3a0e10", "51221e", "8a2e28", "b04a3a", "d07a60")
STRING = P.ramp("467075", "5ba69b", "7cc0b0", "a0d3c1", "d6f0e6") + [P.c("000000", 0)]


def items(L: dict) -> list:
    pal = {"limb": P.GOLD, "ear": DARK, "grip": DARK, "string": STRING, "shaft": SHAFT, "head": P.BLADE,
           "fletch": FLETCH}
    return [Item("weapon", "bow", L["weapon"]["bow"], lambda sk: K.solids(sk, SPEC),
                 Look(highlight=("limb", "head"), flat={"string": 3}, glow=("string",), line_tone={"string": 5},
                      ink=("limb", "ear", "grip", "shaft", "head", "fletch")),
                 {"none": pal}, list(pal))]
