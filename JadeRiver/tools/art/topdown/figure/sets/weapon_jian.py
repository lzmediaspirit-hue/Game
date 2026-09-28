"""The jian family (weapon_families.json `jian`; parts.json weapon `sword`): a long straight jade-steel blade with a
pale edge, gold guard and pommel, dark hilt, cast by figure/kinds/blade.py."""
from __future__ import annotations

from ..items import steel_weapon
from ..kinds import blade as K

KIND = "weapon_jian"
FAMILY = "jian"
SPEC = {"blade": 18.5, "width": 0.68, "hilt": 3.2, "guard": 1.55}


def items(L: dict) -> list:
    return [steel_weapon("sword", L["weapon"]["sword"], lambda sk: K.solids(sk, SPEC))]
