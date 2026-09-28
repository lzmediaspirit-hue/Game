"""The staff family (weapon_families.json `staff`; parts.json weapon `staff`): a dark staff ringed with gold bands,
its head curled in a gold hook, cast by figure/kinds/pole.py."""
from __future__ import annotations

from ..items import steel_weapon
from ..kinds import pole as K

KIND = "weapon_staff"
FAMILY = "staff"
SPEC = {"length": 34.0, "head": 0.0, "staff": True}


def items(L: dict) -> list:
    return [steel_weapon("staff", L["weapon"]["staff"], lambda sk: K.solids(sk, SPEC))]
