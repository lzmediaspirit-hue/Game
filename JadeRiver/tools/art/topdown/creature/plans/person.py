"""People (M1): the human foes (the Mudwater bandits and their archers, Lieutenant Kuai, Big Toad Tan, the drowned
acolytes, the rogue cultivators...) drawn as the player and the villagers are, not sculpted: the shared character body
of the top-down figure (tools/art/topdown/figure/, decision 32 and 37), dressed in the foe's own outfit (its enemies
row's `art.avatar`: hair and its colour, shirt, trousers, shoes, hat, cape, weapon, the dyes) and cast by the figure's
own pipeline (figure/frame.py cast_all) from the poses of its action catalogue (figure/actions.py), which every layer of
the character is already drawn and reviewed in (AGENTS.md rules 1-4: no new body movement, so no new layer pose). A
person foe is the same pixels as a villager in the same clothes, at the same 46 px.

What a plan does for a creature (a pose for each frame of the foe catalogue) a style does here: it names, frame by
frame, the character's action and frame that frame of the foe's action shows (`frames`, `(action, index)`; the action
`strike` stands for the foe's own strike, below). So the catalogue's counts and the blow on frame 1 hold:

  idle    `stand`     the character's breathing idle, eased over six frames
  walk    `stride`    the character's walk
  windup  `charge`    the tell: its strike's first pull back, then the charged finisher's held wind-up (the weapon drawn
                      back, crouched), held until the blow
          `raise`     a heavy blow's tell: the strike's own wind-up held high (the staff over the head)
          `draw`      the bow raised, the arrow nocked and drawn, held (bow_draw 0-3)
  attack  `strike`    the strike from the frame before its blow: the blow on frame 1, its follow-through, settling
          `loose`     the drawn bow, the release on frame 1 (bow_draw 3-6)
  hurt    `flinch`    the character's hurt, its recoil held a frame
  death   `fall`      the knock-down, lying still at the end

The strike is the first step of its weapon family's combo as the room view plays it (weapon_families.json `combo`,
combat_feel.json `poses`: a dagger, a staff or a spear thrusts, a sword cuts, a heavy sabre cuts two-handed, bare fists
jab), or the spec's `strike` (a club's overhead `swing_3`).

The looks: an elite (and a boss of size) is cast at its size (the figure's density times `k`, never a resample), its
clothes, hair and steel darkened toward the §14 shadow as a sculpted elite's ramps are (the skin less), its eyes gold,
in the ring of Qi (sculpt._aura); `aura` gives a boss the ring in its own colours. A `tint` in the outfit (the drowned's
pallor) multiplies the picture as the side view's and the villagers' tint does.

Variants: `fighter` (charge, strike), `archer` (draw, loose), `brute` (raise, strike with the overhead `swing_3`).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from figure import actions as A
from figure import geom, raster
from figure import items as I
from figure.frame import cast_all
from figure.items import z_of
from figure.render import BANDS, SHADOW, Paint, colourize

from .. import sculpt
from ..sculpt import Pose

ROOT = Path(__file__).resolve().parents[5]

STYLES = {
    "stand": {"frames": (("idle", 0), ("idle", 0), ("idle", 1), ("idle", 2), ("idle", 2), ("idle", 3))},
    "stride": {"frames": tuple(("walk", i) for i in range(8))},
    "charge": {"frames": (("strike", 0), ("charge_hold", 0), ("charge_hold", 1), ("charge_hold", 1))},
    "raise": {"frames": (("charge_hold", 0), ("strike", 0), ("strike", 1), ("strike", 1))},
    "draw": {"frames": (("bow_draw", 0), ("bow_draw", 1), ("bow_draw", 2), ("bow_draw", 3))},
    "strike": {"frames": "strike"},
    "loose": {"frames": (("bow_draw", 3), ("bow_draw", 4), ("bow_draw", 5), ("bow_draw", 6), ("bow_draw", 6), ("bow_draw", 6))},
    "flinch": {"frames": (("hurt", 0), ("hurt", 0), ("hurt", 1))},
    "fall": {"frames": (("knockdown", 0), ("knockdown", 1), ("knockdown", 2), ("knockdown", 3), ("knockdown", 4), ("knockdown", 4),
                        ("knockdown", 4), ("knockdown", 4))},
}
_MOTION = {"idle": "stand", "walk": "stride", "windup": "charge", "attack": "strike", "hurt": "flinch", "death": "fall"}
VARIANTS = {
    "fighter": {"parts": {"strike": None}, "mats": {}, "motion": dict(_MOTION)},
    "archer": {"parts": {"strike": None}, "mats": {}, "motion": dict(_MOTION, windup="draw", attack="loose")},
    "brute": {"parts": {"strike": "swing_3"}, "mats": {}, "motion": dict(_MOTION, windup="raise")},
}
# The outfit's layers in the order the game stacks them (TopdownFigure.CATEGORIES), and the dyeable ones.
CATS = ("body", "shoes", "pants", "shirt", "cape", "hair", "hat", "weapon")
# An elite's eyes, gold (sculpt.GOLD's steps); its skin darkens this much of what its clothes do.
GOLD_IRIS = {"iris": sculpt.GOLD[2][:3], "iris_light": sculpt.GOLD[4][:3], "pupil": sculpt.GOLD[0][:3]}
SKIN_DARK = 0.4

_ITEMS: dict = {}
_DATA: dict = {}


def _items() -> dict:
    """Every item of the character's sets, by (category, look)."""
    if not _ITEMS:
        for it in I.catalog():
            _ITEMS[(it.cat, it.name)] = it
    return _ITEMS


def strike_of(weapon: str) -> str:
    """The first step of the weapon's family's combo as the room view plays it (TopdownPlaces.pose)."""
    if not _DATA:
        fam = json.loads((ROOT / "data/weapon_families.json").read_text())
        _DATA["families"] = fam["entries"] if isinstance(fam, dict) and "entries" in fam else fam
        _DATA["feel"] = json.loads((ROOT / "data/combat_feel.json").read_text())["families"]
    name = "fists"
    for f in _DATA["families"]:
        if (weapon or "none") in (f.get("appearance") or []):
            name = f["id"]
    combo = [c["action"] for f in _DATA["families"] if f["id"] == name for c in f.get("combo", [])]
    first = combo[0] if combo else "punch_1"
    first = _DATA["feel"].get(name, {}).get("poses", {}).get(first, first)
    return A.ALIASES.get(first, first)


class Figure(Pose):
    """A person's frame: the character's pose (figure/actions.py) and the outfit's items to cast it in. `parts` lists the
    items (a frame always has its body); `picture` casts it in a facing and look (creatures.draw calls it in place of
    the sculpture's renderer)."""

    def __init__(self, action: str, index: int, outfit: dict):
        super().__init__()
        self.action, self.index, self.outfit = action, index, outfit
        items = _items()
        self.items = [items[("body", str(outfit.get("body", "light")))]]
        for cat in CATS[1:]:
            look = str(outfit.get(cat, "none"))
            if look not in ("none", ""):
                self.items.append(items[(cat, look)])
        self.parts = [it.key for it in self.items]

    def _variant(self, it) -> str:
        if it.cat == "hair":
            k = str(int(self.outfit.get("hair_color", 0)))
            return k if k in it.palettes else it.variants()[0]
        if it.cat in ("shirt", "pants"):
            k = str(self.outfit.get(it.cat + "_dye", "none"))
            return k if k in it.palettes else "none"
        return "none"

    def _palette(self, it, elite: bool) -> dict:
        pal = dict(it.palettes[self._variant(it)])
        if not elite:
            return pal
        out = {}
        for mat, ramp in pal.items():
            if it.cat == "body" and mat in GOLD_IRIS:
                out[mat] = [GOLD_IRIS[mat]] * len(ramp)
            elif mat in it.look.glow or (it.cat == "body" and mat not in ("skin",)):
                out[mat] = ramp
            else:
                t = SKIN_DARK if it.cat == "body" else 1.0
                out[mat] = [_darken(c, (0.30 - 0.03 * i) * t) for i, c in enumerate(ramp)]
        return out

    def picture(self, facing: str, elite: bool = False, frame_no: int = 0, aura=False, lean_ring: bool = False) -> np.ndarray:
        """The person cast facing `facing` (s, se, e, ne, n) at its size: RGBA on the working canvas, its feet on
        sculpt.FOOT (the figure's anchor)."""
        geom.SCALE = geom.WORLD_SCALE * self.k
        try:
            cast = cast_all(A.poses(self.action)[self.index], facing, self.items)
        finally:
            geom.SCALE = geom.WORLD_SCALE
        stack = []
        for it in self.items:
            L, c = cast[it.key]
            paint = Paint(c.mats, self._palette(it, elite), it.look)
            for b in BANDS:
                if (L[b].mat >= 0).any() or (L[b].out > 0).any():
                    stack.append((z_of(it.cat, b), colourize(L[b], c.mats, paint)))
        stack.sort(key=lambda t: t[0])
        im = Image.new("RGBA", (raster.W, raster.H))
        for _, a in stack:
            im.alpha_composite(Image.fromarray(a, "RGBA"))          # as figure/frame.py compose stacks a figure
        rgba = np.array(im)
        tint = self.outfit.get("tint")
        if tint:
            t = np.array([int(str(tint).lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0
            rgba[..., :3] = np.clip(np.round(rgba[..., :3] * t), 0, 255).astype(np.uint8)
        # The figure's anchor is the sculpture's feet (raster AX, AY == sculpt.FOOT).
        if elite or aura:
            sculpt._aura(rgba, sculpt.ring_seed(rgba) if lean_ring else frame_no, "hollow" if aura == "hollow" else "gold", lean_ring)
        return rgba


def _darken(c, t: float) -> tuple:
    """A colour toward the §14 shadow and a little deeper (sculpt._darken's), keeping its alpha."""
    out = tuple(int(round(c[i] * (1 - t) + SHADOW[i] * t * 0.8)) for i in range(3))
    return out + tuple(c[3:4])


def frames(B, action: str) -> list:
    """The (character action, index) each frame of the foe's `action` shows."""
    st = B.style(action)
    fr = st.get("frames")
    strike = B.parts.get("strike") or strike_of(str(B.parts.outfit.get("weapon", "none")))
    if fr == "strike":
        n, hit = A.CATALOG[strike][0], A.CATALOG[strike][3]
        return [(strike, min(n - 1, hit - 1 + i)) for i in range(6)]
    return [(strike if a == "strike" else a, i) for a, i in fr]


def pose(B, action: str, f: int, **_facing) -> Figure:
    a, i = frames(B, action)[f]
    return Figure(a, min(i, len(A.poses(a)) - 1), dict(B.parts.outfit))
