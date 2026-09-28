"""The brush family (weapon_families.json `brush`; parts.json weapon `brush`): the calligraphy brush
(tools/art/bake_weapons.py `brush_frame`), a jointed bamboo shaft, a lacquered collar and cap, and a tuft pale at the
root and soaked black to its point, cast by figure/kinds/brush.py. Its cuts leave an ink stroke, broad at the brush and
thinning behind it, run dry and broken at its tail."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import brush as K
from ..render import Look

KIND = "weapon_brush"
FAMILY = "brush"

# The side view's bamboo (e2c284, c49e60, 946e3e, joint 76542e), lacquer (7a2e34, 42181e), hair (585a68, 22222c) and
# ink (100e14, drying to 3a363e), as five-step ramps. The stroke is flat: wet ink is tone 1 edged in tone 0.
BAMBOO = P.ramp("5a3e22", "946e3e", "c49e60", "e2c284", "f4e2b4")
JOINT = P.ramp("3a2814", "5a3e22", "76542e", "946e3e", "b08a58")
LACQUER = P.ramp("2a0e12", "42181e", "7a2e34", "9e4a4e", "c0706a")
TUFT = P.ramp("0c0b10", "16161e", "22222c", "3a3a48", "585a68")
TIP = P.ramp("08070b", "100e14", "16141c", "22222c", "3a363e")
INK = P.ramp("08070b", "100e14", "1c1a22", "2e2b36", "4a4656")
INK_DRY = P.ramp("58546a", "2e2b36", "3a363e", "4a4652", "5c5864")    # its edge lighter: dry ink feathers

SPEC = {
    "butt": 1.7, "shaft": 7.0, "radius": 0.46, "joints": [2.6, 5.0], "collar": 1.1, "tuft": 4.0, "belly": 0.82,
    "stroke": (1.6, 0.0), "inset": 0.9, "gap": 10.0, "dry": 30.0, "breaks": [(5.0, 12.0), (18.0, 23.0)],
}


def items(L: dict) -> list:
    pal = {"bamboo": BAMBOO, "joint": JOINT, "lacquer": LACQUER, "tuft": TUFT, "tip": TIP, "ink": INK,
           "ink_dry": INK_DRY}
    return [Item("weapon", "brush", L["weapon"]["brush"], lambda sk: K.solids(sk, SPEC),
                 Look(highlight=("bamboo", "lacquer", "tuft"), flat={"ink": 1, "ink_dry": 1}, glow=("ink", "ink_dry"),
                      line_tone={"ink": 0, "ink_dry": 0}, ink=("bamboo", "joint", "lacquer", "tuft", "tip")),
                 {"none": pal}, list(pal))]
