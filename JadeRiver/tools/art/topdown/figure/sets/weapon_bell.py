"""The bell family (weapon_families.json `bell`; parts.json weapon `bell`): the warden's hand-bell, a bronze bell with a
dark rim and a clapper on a short dark-wood handle with a red cord (the side view's colours, tools/art/bake_weapons.py
BELL, WOOD, CORD), its blows ringing out rings of pale-gold qi (the side view's CHIME), cast by figure/kinds/bell.py."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import bell as K
from ..render import Look

KIND = "weapon_bell"
FAMILY = "bell"
SPEC = {"handle": (-1.3, 2.7), "crown": 3.0, "dome": (1.4, 1.1), "waist": (6.8, 1.7), "lip": (8.6, 2.5),
        "band": (5.3, 5.8), "cord": 1.0,
        # per stage (the hit frame, the one after): the rings' radii about the mouth
        "rings": ((4.6, 7.6), (6.4, 9.6))}

# The side view's bronze (BELL: rim, shadow, body, highlight), its dark rim, the mouth's shadowed inside, the dark wood
# (WOOD) and the red cord (CORD).
BRONZE = P.ramp("4a2e1e", "88562c", "c68e42", "dcb060", "f2d27e")
RIM = P.ramp("24160e", "3a2416", "4a2e1e", "6a4226", "88562c")
MOUTH = P.ramp("4a2e1e", "6a4226", "88562c", "9a6430", "a8703a")
WOOD = P.ramp("24160e", "40281c", "5a3c26", "6e4a2e", "8a6440")
CORD = P.ramp("35101a", "6e1a1e", "b82a2e", "d04a44", "f2866a")
# The peal: pale-gold light (the side view's CHIME), crisp lines with no edge round them (step 5, clear) so the rings
# stay apart over the ground; on the frame after the hit a step fainter.
RING = P.ramp("a8772f", "d1a64d", "eac468", "f6dc96", "fff0c4") + [P.c("000000", 0)]


def items(L: dict) -> list:
    pal = {"bronze": BRONZE, "rim": RIM, "mouth": MOUTH, "wood": WOOD, "cord": CORD, "ring": RING, "ring_fade": RING}
    return [Item("weapon", "bell", L["weapon"]["bell"], lambda sk: K.solids(sk, SPEC),
                 Look(highlight=("bronze", "cord"), flat={"mouth": 2, "ring": 3, "ring_fade": 2},
                      glow=("ring", "ring_fade"), line_tone={"ring": 5, "ring_fade": 5},
                      ink=("bronze", "rim", "mouth", "wood", "cord")),
                 {"none": pal}, list(pal))]
