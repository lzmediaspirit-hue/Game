"""The flute family (weapon_families.json `flute`; parts.json weapon `flute`): the jade flute, a green bamboo dizi with
dark joints, finger holes and a red tassel (the side view's colours, the side view's weapon bake FLUTE), its notes
ripples of pale jade light, cast by figure/kinds/flute.py."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import flute as K
from ..render import Look

KIND = "weapon_flute"
FAMILY = "flute"
SPEC = {"length": 13.6, "behind": 1.6, "radius": 0.72, "nodes": (4.6, 9.4), "node": 0.42, "holes": (6.2, 7.6, 11.0),
        "tassel": 2.8,
        # per stage (the hit frame, the one after): the ripples' radii and half-spans (radians) about the far end
        "ripples": (((2.4, 5.6, 8.8), (1.0, 0.72, 0.56)), ((4.4, 7.6, 10.8), (0.9, 0.66, 0.5))),
        # played at the lips (flute_play), the ripples leave the open end this much smaller, clear of the face
        "play_ripples": 0.85}

# The side view's jade bamboo (FLUTE: shadow, body, light), its joints (FLUTE_NODE) and the finger holes, and the
# tassel's red (TASSEL).
BAMBOO = P.ramp("223620", "3e603a", "689658", "96c478", "c6e4a0")
NODE = P.ramp("141e12", "22301e", "30462a", "3e603a", "52744a")
HOLE = P.ramp("0e140c", "141c10", "1e281a", "2a3a24", "3a4e32")
TASSEL = P.ramp("35101a", "6e1a1e", "b0282c", "d04a44", "f2866a")
# The note: the cut smear's pale jade light, its edge a translucent halo of it (step 5) rather than a solid rim, so the
# thin ripples stay apart; on the frame after the hit a step fainter, with no halo.
RIPPLE = P.SMEAR + [P.c("8fd0bf", 110)]
RIPPLE_FADE = P.SMEAR + [P.c("000000", 0)]


def items(L: dict) -> list:
    pal = {"bamboo": BAMBOO, "node": NODE, "hole": HOLE, "cord": TASSEL, "tassel": TASSEL, "ripple": RIPPLE,
           "ripple_fade": RIPPLE_FADE}
    return [Item("weapon", "flute", L["weapon"]["flute"], lambda sk: K.solids(sk, SPEC),
                 Look(highlight=("tassel",), flat={"ripple": 3, "ripple_fade": 1}, glow=("ripple", "ripple_fade"),
                      line_tone={"ripple": 5, "ripple_fade": 5},
                      ink=("bamboo", "node", "hole", "cord", "tassel")),
                 {"none": pal}, list(pal))]
