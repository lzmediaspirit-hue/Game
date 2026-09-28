"""The fan family (weapon_families.json `fan`; parts.json weapon `fan`): the iron fan (tools/art/bake_weapons.py
`fan_frame`), cream paper pleated over brown ribs, a band of teal ink along its rim and a gold rivet, cast by
figure/kinds/fan.py. It opens in the blows (the family's swings, and every thrust, punch, the guard and the plunge's
dive, the charged wind-up, the dash and air strikes and the parry) and folds at rest; its third step throws it
(`fan_throw`: open as it is drawn back and swept round, out of the hand from the release). Its cuts leave the jian's
smear of pale jade light."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import fan as K
from ..render import Look

KIND = "weapon_fan"
FAMILY = "fan"

# The side view's paper (f2e8cc, ded0ac, c4b28c), rib brown (5c3a22) and ink band (2c6e68), as five-step ramps.
PAPER = P.ramp("7e6c4e", "c4b28c", "ded0ac", "f2e8cc", "fcf6e4")
RIB = P.ramp("2a1a10", "3e2616", "5c3a22", "7a5234", "98704c")
FAN_INK = P.ramp("0e2e2c", "1c4c48", "2c6e68", "3e8c84", "5eaca2")

ALL = list(range(6))
SPEC = {
    "length": 10.5, "rivet": 1.3, "spread": 52.0, "leaf": 0.36, "pleats": 8, "band": (0.8, 0.2), "thick": 0.4,
    "least": 50.0, "turn": 0.2, "width": (0.55, 1.0),
    "open": {"swing_1": ALL, "swing_2": ALL, "swing_3": ALL, "thrust_1": ALL, "thrust_2": ALL, "thrust_3": ALL,
             "punch_1": ALL, "punch_2": ALL, "punch_3": ALL, "guard": ALL, "plunge": [1, 2],
             "charge_hold": ALL, "dash_slash": ALL, "air_strike": ALL, "parry_deflect": ALL, "fan_throw": [0, 1, 2]},
    # the third step's throw: in flight from the release on (the throw's projectile art draws it)
    "thrown": {"fan_throw": [3, 4, 5]},
}


def items(L: dict) -> list:
    pal = {"paper": PAPER, "rib": RIB, "fan_ink": FAN_INK, "gold": P.GOLD, "smear": P.SMEAR}
    return [Item("weapon", "fan", L["weapon"]["fan"], lambda sk: K.solids(sk, SPEC),
                 Look(highlight=("paper", "gold"), flat={"smear": 2}, glow=("smear",), line_tone={"smear": 0},
                      ink=("paper", "rib", "fan_ink", "gold")),
                 {"none": pal}, list(pal))]
