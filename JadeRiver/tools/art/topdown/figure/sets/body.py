"""The unclothed body (parts.json `body`: the creator's one skin tone), the base every other set is cast over: skin in
the side view's ramp, the face's eyes, brows, mouth, nose shade and blush stamped flat (figure/body.py `face`)."""
from __future__ import annotations

from .. import body as B
from .. import palettes as P
from ..items import Item
from ..render import Look

KIND = "body"


def _flat(col):
    return [col] * 5


FACE = {"eye_dark": P.EYE_DARK, "iris": P.IRIS, "iris_light": P.IRIS_LIGHT, "eye_white": P.EYE_WHITE, "brow": P.BROW,
        "nose": P.NOSE, "mouth": P.MOUTH, "blush": P.BLUSH}
EYE_MATS = {m: _flat(FACE[m]) for m in B.FACE_MATS}
SKINS = {"light": P.SKIN}


def items(L: dict) -> list:
    return [Item("body", name, L["body"][name], B.solids,
                 Look(highlight=("skin",), flat={m: 2 for m in EYE_MATS}, line_tone={"skin": 1}),
                 {"none": dict(EYE_MATS, skin=skin)}, ["skin"] + list(EYE_MATS))
            for name, skin in SKINS.items()]
