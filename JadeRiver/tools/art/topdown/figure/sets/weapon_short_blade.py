"""The short blade family (weapon_families.json `short_blade`; parts.json weapon `dagger`): a short jade-steel blade,
gold guard, brown hilt, cast by figure/kinds/blade.py."""
from __future__ import annotations

from ..items import steel_weapon
from ..kinds import blade as K

KIND = "weapon_short_blade"
FAMILY = "short_blade"
SPEC = {"blade": 7.2, "width": 0.8, "hilt": 2.4, "guard": 1.3}


def items(L: dict) -> list:
    return [steel_weapon("dagger", L["weapon"]["dagger"], lambda sk: K.solids(sk, SPEC))]
