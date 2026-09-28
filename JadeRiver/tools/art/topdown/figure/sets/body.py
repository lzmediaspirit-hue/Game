"""The unclothed body (parts.json `body`: the creator's one skin tone), the base every other set is cast over: skin in
the side view's ramp, the face's eyes and mouth stamped flat (figure/body.py)."""
from __future__ import annotations

from .. import body as B
from .. import palettes as P
from ..items import Item
from ..render import Look

KIND = "body"


def _flat(col):
    return [col] * 5


EYE_MATS = {"eye_dark": _flat(P.EYE_DARK), "iris": _flat(P.IRIS), "iris_light": _flat(P.IRIS_LIGHT),
            "eye_white": _flat(P.EYE_WHITE), "mouth": _flat(P.MOUTH)}
SKINS = {"light": P.SKIN}


def items(L: dict) -> list:
    return [Item("body", name, L["body"][name], B.solids,
                 Look(highlight=("skin",), flat={m: 2 for m in EYE_MATS}, line_tone={"skin": 1}),
                 {"none": dict(EYE_MATS, skin=skin)}, ["skin"] + list(EYE_MATS))
            for name, skin in SKINS.items()]
