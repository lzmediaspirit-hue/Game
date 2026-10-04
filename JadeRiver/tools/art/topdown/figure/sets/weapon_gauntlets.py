"""The gauntlets family (weapon_families.json `gauntlets`; parts.json weapon `gauntlets`): the training gauntlets
(the side view's gauntlet bake), a steel fist over each hand and a bronze-banded steel cuff round the wrist, cast by
figure/kinds/hands.py."""
from __future__ import annotations

from .. import palettes as P
from ..items import Item
from ..kinds import hands as K
from ..render import Look

KIND = "weapon_gauntlets"
FAMILY = "gauntlets"


def items(L: dict) -> list:
    return [Item("weapon", "gauntlets", L["weapon"]["gauntlets"], K.solids,
                 Look(highlight=("steel", "bronze"), ink=("steel", "bronze")),
                 {"none": {"steel": P.STEEL, "bronze": P.BRONZE}}, ["steel", "bronze"])]
