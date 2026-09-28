"""The spear family (weapon_families.json `spear`; parts.json weapon `spear`): a long pale shaft wound with brown cord,
a jade-steel leaf head on a gold socket, cast by figure/kinds/pole.py."""
from __future__ import annotations

from ..items import steel_weapon
from ..kinds import pole as K

KIND = "weapon_spear"
FAMILY = "spear"
SPEC = {"length": 44.0, "head": 5.2}


def items(L: dict) -> list:
    return [steel_weapon("spear", L["weapon"]["spear"], lambda sk: K.solids(sk, SPEC))]
