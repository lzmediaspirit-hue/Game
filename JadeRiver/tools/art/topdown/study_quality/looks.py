"""The study's subset and its hand-tuned detail (decision 42).

The looks are the game's own (figure/sets/: the same generators, specs and colours), so every villager in the two
scenes is drawn. What the study adds on top, by material and part, without touching figure/:

  - hair: loose locks at the temples and over the brow that break the cap's round silhouette and frame the face; the
    cap and knots in a few broad locks instead of thin grooves, a sheen ring broken lock by lock on the sunlit side,
    a darker crown; a groove and a lit strand down each lock of a tail;
  - cloth: folds that hang from the belt and gather at the hem, creases in the elbow and behind the knee, gathers over
    the trousers' ankle wraps, a lit ridge beside each groove;
  - the face: eyes with a lash line, a white, an iris and its lower light (larger at 48 px; at 76 px a pupil, a glint
    and brows), a nose shade, a mouth and a touch of blush, from glyphs drawn for each size (`FACES`);
  - how each material shades (`MATS`): which may reach the light step, which the highlight (sheen, metal, silk),
    which count extra in a pixel's vote (thin trim), which are solid from a quarter of a pixel (trim, the blade), and
    which lighting steps (`th`: the mean N.L at each step) a material uses when the default suits it badly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from figure import items as I  # noqa: E402
from figure import palettes as P  # noqa: E402
from figure.body import SKULL  # noqa: E402
from figure.geom import LIGHT, TOWARD, unit, vec  # noqa: E402
from figure.kinds.hair import CAP_GROW  # noqa: E402
from figure.raster import cone, sphere  # noqa: E402

# ------------------------------------------------------------------ materials
# hi: may reach step 5 (light); glossy: step 6 (a sheen or a glint); weight: its vote in a pixel; thin: solid from a
# quarter of a pixel; ink: its edge over the body stays an outer outline; glow: light, no ink (the smear).
MATS = {
    "skin": {"hi": True, "th": (-0.55, -0.2, 0.36, 0.72)},     # faces read best lit nearly flat
    "hair": {"hi": True, "glossy": True, "th": (-0.05, 0.38, 0.74, 0.95)},
    "ribbon": {"hi": True, "glossy": True, "weight": 1.6},
    "pin": {"hi": True, "glossy": True, "weight": 0.9},
    "cloth": {"hi": True},
    "panel": {"hi": True},
    "edge": {},
    "trim": {"hi": True, "glossy": True, "weight": 1.5, "thin": True},
    "belt": {"hi": True, "weight": 1.3},
    "accent": {"hi": True, "weight": 1.6},
    "wrap": {"hi": True, "weight": 1.3},
    "sole": {"hi": True},
    "top": {"hi": True},
    "plate": {"hi": True, "glossy": True},
    "blade": {"hi": True, "glossy": True, "thin": True, "ink": True},
    "gold": {"hi": True, "glossy": True, "weight": 2.0, "thin": True, "ink": True},
    "hilt": {"weight": 1.5, "thin": True, "ink": True},
    "shaft": {"hi": True, "thin": True, "ink": True},
    "cord": {"thin": True, "ink": True},
    "smear": {"glow": True},
}
# The blade's pale edge is named `edge` in the weapon's own palette; in the weapon it is thin and inked.
WEAPON_MATS = {"edge": {"hi": True, "glossy": True, "thin": True, "ink": True, "weight": 1.8}}

# ------------------------------------------------------------------ face colours (the body's extra materials)
FACE_COLS = {
    "eye_dark": P.EYE_DARK, "iris": P.IRIS, "iris_light": P.IRIS_LIGHT, "eye_white": P.EYE_WHITE,
    "pupil": P.c("1c2632"), "glint": P.c("ffffff"), "brow": P.c("3a2b2c"), "nose": P.c("c98062"),
    "mouth": P.c("934536"), "lip": P.c("d98b72"), "blush": P.c("f3a58c"),
}
GLYPH_MAT = {"K": "eye_dark", "I": "iris", "L": "iris_light", "W": "eye_white", "D": "pupil", "G": "glint",
             "B": "brow", "N": "nose", "M": "mouth", "m": "lip", "P": "blush"}

# Glyphs per size (hifi.Grid.face): rows top to bottom, left to right as seen on screen for the eye on the screen's
# left; the other eye mirrors. `.` leaves skin. `*_dy`, `*_dx`: offsets in px from the feature's projected point.
FACES = {
    "b": {  # 38 px: an eye is 2 wide and 3 tall (lash, white and iris, the iris's lower light), the mouth 1 px
        "eye_front": ["KK", "WI", ".L"], "eye_near": ["KK", "WI", ".L"], "eye_far": ["K", "I"], "eye_side": ["KK", ".I"],
        "eye_shut": ["KK"], "brow": ["BB"], "brow_far": ["B"], "brow_dy": -2,
        "mouth_front": ["M"], "mouth_near": ["M"], "mouth_dy": 0, "nose": None, "nose_side": ["N"],
        "blush": ["P"], "blush_dy": 2, "blush_dx": -1,
    },
    "d": {  # 48 px: an eye is 3 x 3 with a pupil and a lower light, the mouth 2 px
        "eye_front": ["KKK", "WDI", ".IL"], "eye_near": ["KKK", "WDI", ".IL"], "eye_far": ["K", "D", "I"],
        "eye_side": ["KK", ".D", ".I"], "eye_shut": ["KKK"], "brow": ["BB."], "brow_far": ["B"], "brow_dy": -2,
        "mouth_front": ["MM"], "mouth_near": ["M"], "mouth_dy": 0, "nose": None, "nose_side": ["N"],
        "blush": ["P"], "blush_dy": 3, "blush_dx": -1,
    },
    "c": {  # 76 px: an eye is 4 x 3 with a pupil, a glint and a lower light; a brow arches over 3 px
        "eye_front": [".KKK", "KGDI", ".WIL"], "eye_near": [".KKK", "KGDI", ".WIL"], "eye_far": ["KK", "DI", "IL"],
        "eye_side": ["KKK", ".GD", ".IL"], "eye_shut": [".KKK", "K..."],
        "brow": ["..BB", "BB.."], "brow_far": ["BB"], "brow_dy": -4,
        "mouth_front": ["MMM", ".m."], "mouth_near": ["MM", "m."], "mouth_dy": 0, "nose": ["N"], "nose_side": ["N"],
        "blush": ["PP"], "blush_dy": 3, "blush_dx": -1,
    },
}


def _stamp(R, caster, g, sx, sy, glyph, head_id, mirror=False) -> None:
    w = len(glyph[0])
    x0 = int(np.floor(sx + g.AX - (w - 1) * 0.5))
    y0 = int(np.floor(sy + g.AY))
    for j, row in enumerate(glyph):
        if mirror:
            row = row[::-1]
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + i, y0 + j
            if 0 <= y < R.mat.shape[0] and 0 <= x < R.mat.shape[1] and R.part[y, x] == head_id and R.mat[y, x] >= 0:
                R.mat[y, x] = caster.mid(GLYPH_MAT[ch])


def face(g, sk, R, caster) -> None:
    """The face on the head's resolved pixels (the body's head band), as figure/body.face places it, with the study's
    glyphs for this density."""
    F = FACES[getattr(g, "face", "b")]
    Mh = sk.Mh
    yaw = sk.fr.yaw_to_camera(Mh[:, 0])
    a = abs(yaw)
    if a > 118:
        return
    head_id = caster.parts.get("head", -9)
    near = "r" if yaw < 0 else "l"
    hx, _ = g.project(sk.head)
    shut = sk.eyes == "shut"
    for s, sg in (("l", -1.0), ("r", 1.0)):
        p = sk.head + Mh @ vec(4.95, sg * 2.2, 1.0)
        n = (p - sk.head) / np.linalg.norm(p - sk.head)
        if float(n @ TOWARD) < 0.05:
            continue
        sx, sy = g.project(p)
        on_left = sx < hx
        if shut:
            _stamp(R, caster, g, sx, sy, F["eye_shut"], head_id, mirror=not on_left)
            continue
        if a <= 24:
            glyph, brow, mir = F["eye_front"], F["brow"], not on_left
        elif a <= 66:
            if s == near:
                glyph, brow, mir = F["eye_near"], F["brow"], yaw > 0
            else:
                glyph, brow, mir = F["eye_far"], F["brow_far"], yaw > 0
        else:
            if s != near:
                continue
            glyph, brow, mir = F["eye_side"], F["brow_far"], yaw > 0
            sx += (-1 if yaw < 0 else 1) * g.k
        _stamp(R, caster, g, sx, sy + F["brow_dy"], brow, head_id, mirror=mir)
        _stamp(R, caster, g, sx, sy, glyph, head_id, mirror=mir)
        if a <= 66 and (a <= 24 or s == near) and F.get("blush"):
            bx = sx + (F["blush_dx"] * (1 if on_left else -1)) * g.k
            _stamp(R, caster, g, bx, sy + F["blush_dy"], F["blush"], head_id, mirror=mir)
    if shut or a > 80:
        return
    mp = sk.head + Mh @ vec(5.0, 0.0, -2.4)
    mx, my = g.project(mp)
    mouth = F["mouth_front"] if a <= 24 else F["mouth_near"]
    _stamp(R, caster, g, mx, my + F["mouth_dy"], mouth, head_id, mirror=yaw > 0)
    nose = F["nose"] if a <= 24 else F["nose_side"]
    if nose:
        npnt = sk.head + Mh @ vec(5.6, 0.25, -0.9)
        nx, ny = g.project(npnt)
        _stamp(R, caster, g, nx + (0 if a <= 24 else (1 if yaw < 0 else -1)), ny, nose, head_id)


# ------------------------------------------------------------------ hair
HAIR_RADII = np.array(SKULL) + np.array(CAP_GROW)


def _hair_cap_paint(orig, locks: int, sheen: tuple):
    """The cap's clip stays; its paint becomes broad locks, each with a groove and a lit ridge under a sheen ring that
    breaks lock by lock on the sunlit side, and a darker crown past the ring."""

    def paint(loc, P, nrm):
        u = loc / HAIR_RADII
        u = u / np.maximum(np.linalg.norm(u, axis=1), 1e-9)[:, None]
        phi = np.degrees(np.arctan2(u[:, 1], u[:, 0]))
        lat = np.degrees(np.arcsin(np.clip(u[:, 2], -1, 1)))
        a = (phi + 180.0) / 360.0 * locks + (90.0 - lat) * 0.014
        idx = np.floor(a)
        f = a - idx
        names = np.array(["hair"] * len(loc), dtype=object)
        bias = np.zeros(len(loc), dtype=np.float32)
        lit = nrm @ LIGHT
        low = lat < sheen[0] - 4.0
        bias[(f < 0.2) & low] -= 1.0                                 # the groove between two locks, under the sheen
        bias[(f > 0.45) & (f < 0.7) & low & (lit > 0.3)] += 0.6      # each lock's lit ridge
        band = (lat > sheen[0]) & (lat < sheen[1]) & (lit > 0.1)     # the sheen ring round the crown, sunlit side
        cut = (f < 0.12) & (lat < sheen[0] + 5.0)                     # broken where a groove runs up into it
        bias[band & ~cut] += 2.0
        bias[band & ~cut & (lit > 0.5) & (f > 0.3) & (f < 0.8)] += 1.0
        bias[(lat > sheen[1] + 14.0)] -= 0.4                         # the crown past the ring turns away
        return names, bias
    return paint


def _mass_paint(strands: int, spiral: float = 0.0):
    """A knot or a tie: locks wound round it, a sheen on its sunlit cap."""

    def paint(loc, P, nrm):
        n = len(loc)
        r = np.linalg.norm(loc, axis=1) + 1e-9
        phi = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        z = loc[:, 2] / r
        a = (phi + 180.0) / 360.0 * strands + z * spiral
        f = a - np.floor(a)
        bias = np.zeros(n, dtype=np.float32)
        lit = nrm @ LIGHT
        bias[f < 0.16] -= 1.0
        bias[(lit > 0.5) & (f > 0.3) & (f < 0.8)] += 1.2
        return np.array(["hair"] * n, dtype=object), bias
    return paint


def _tail_paint(orig_mat="hair"):
    """A lock of a tail: a groove down one side, a lit strand down the other."""

    def paint(loc, P, nrm):
        n = len(loc)
        ang = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        bias = np.zeros(n, dtype=np.float32)
        lit = nrm @ LIGHT
        bias[np.abs(((ang + 30.0) % 120.0) - 60.0) < 9.0] -= 1.0
        bias[(lit > 0.45) & (np.abs(((ang + 90.0) % 120.0) - 60.0) < 20.0)] += 1.1
        return np.array([orig_mat] * n, dtype=object), bias
    return paint


# Loose locks that break the cap's round silhouette and frame the face, per style, in the head's frame (forward,
# right, up; figure units from the head's centre): (root, tip, root radius, tip radius). A temple strand (given on the
# left) is mirrored to the right; it hangs just in front of the ear to the jaw, behind the cheek, so a three-quarter
# face stays clear. Forelocks fall over the brow.
TEMPLE = ((1.5, -5.8, 2.2), (2.0, -6.4, -3.6), 1.15, 0.4)
LOCKS = {
    "topknot": [TEMPLE, ((4.9, -1.9, 4.6), (5.9, -2.9, 1.5), 0.95, 0.25), ((5.0, 1.2, 4.6), (6.0, 2.0, 1.9), 0.85, 0.25)],
    "short_knot": [TEMPLE, ((4.9, -2.4, 4.3), (5.8, -2.9, 2.0), 0.9, 0.2), ((5.2, -0.2, 4.6), (6.0, 0.3, 2.3), 0.9, 0.2),
                   ((5.0, 2.2, 4.4), (5.8, 2.9, 2.2), 0.85, 0.2)],
    "ponytail": [TEMPLE, ((5.0, -1.4, 4.5), (5.8, -2.3, 2.2), 0.85, 0.2), ((5.1, 1.6, 4.4), (5.8, 2.4, 2.3), 0.8, 0.2)],
    "high_pony": [TEMPLE, ((5.0, -1.4, 4.5), (5.8, -2.3, 2.2), 0.85, 0.2), ((5.1, 1.6, 4.4), (5.8, 2.4, 2.3), 0.8, 0.2)],
    "long_tied": [((1.6, -5.8, 2.2), (2.2, -6.4, -5.0), 1.15, 0.35)],
    "flowing": [((1.6, -5.8, 2.2), (2.2, -6.4, -5.4), 1.2, 0.35)],
}


def hair_locks(sk, style: str) -> list:
    out = []
    Mh = sk.Mh
    for (a, b, r0, r1) in LOCKS.get(style, []):
        pairs = [(a, b)]
        if a[1] < -3.0:                                   # a temple strand: both sides
            pairs.append(((a[0], -a[1], a[2]), (b[0], -b[1], b[2])))
        for aa, bb in pairs:
            pa = sk.head + Mh @ vec(*aa)
            pb = sk.head + Mh @ vec(*bb)
            axis = unit(pb - pa)
            normal = unit(pa - sk.head)
            side = unit(np.cross(axis, normal))
            out.append(cone(pa, pb, r0, r1, "hair", k=0.6, side=side, band="mid", part="lock", paint=_tail_paint()))
            out.append(sphere(pa, r0 * 0.9, "hair", band="mid", part="lock"))
    return out


def tune_hair(solids: list, sk, style: str, tuned: bool) -> list:
    """A hair style's solids with its loose locks added and its cap, knots and tails painted in locks and sheen
    (`tuned`: the player's style, a lock count and sheen band chosen for it)."""
    locks = {"topknot": 7, "short_knot": 8, "ponytail": 7, "high_pony": 7, "long_tied": 9, "flowing": 9}.get(style, 8)
    solids = list(solids) + hair_locks(sk, style)
    for s in solids:
        if s.mat != "hair":
            continue
        if s.part == "hair" and s.kind == "ellipsoid":
            s.paint = _hair_cap_paint(s.paint, locks if tuned else 9, (36.0, 52.0) if tuned else (40.0, 54.0))
        elif s.kind == "ellipsoid" and s.part in ("knot", "tie", "bun", "loop"):
            s.paint = _mass_paint(6 if tuned else 5, 2.2 if tuned else 0.0)
            s.frame = (s.geo["c"], s.geo["M"])
        elif s.kind == "cone" and s.part in ("tail", "fall"):
            s.paint = _tail_paint()
    return solids


# ------------------------------------------------------------------ cloth
def _wrap(orig, mat, extra):
    def paint(loc, P, nrm):
        if orig is None:
            names = np.array([mat] * len(loc), dtype=object)
            bias = np.zeros(len(loc), dtype=np.float32)
        else:
            names, bias = orig(loc, P, nrm)
            bias = np.asarray(bias, dtype=np.float32).copy()
        return names, bias + extra(loc, P, nrm, names)
    return paint


def _skirt_folds(L: float, long: bool):
    """Folds from the belt to the hem: a few broad ones, uneven, each a groove with a lit ridge on its west."""
    centres = np.array([-128.0, -74.0, -22.0, 34.0, 86.0, 142.0])   # angles round the skirt (0 its right side)

    def extra(loc, P, nrm, names):
        th = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        w = loc[:, 2] / max(L, 1e-6)
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        grow = np.clip((w - 0.18) / 0.5, 0.0, 1.0)
        for i, c in enumerate(centres):
            d = (th - c + 180.0) % 360.0 - 180.0
            wid = 7.0 + 5.0 * grow + (i % 2) * 2.0
            out[cloth & (np.abs(d) < wid * 0.45) & (w > 0.2 + 0.1 * (i % 3))] -= 1.0
            out[cloth & (d > wid * 0.45) & (d < wid * 1.1) & (w > 0.3)] += 1.0
        if long:
            out[cloth & (w > 0.92)] -= 0.5
        return out
    return extra


def _chest_folds(sk):
    """Gathers over the belt and two pulls from the belt toward the chest's sides."""
    wu = float((sk.waist - sk.chest) @ sk.Mc[:, 2])

    def extra(loc, P, nrm, names):
        f, r, u = loc[:, 0], loc[:, 1], loc[:, 2]
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        band = (u > wu + 0.95) & (u < wu + 2.0) & (f > 0.2)
        g = np.abs(((r + 3.0) % 1.9) - 0.95) < 0.24
        out[cloth & band & g] -= 1.0
        pull = (f > 0.4) & (u > wu + 1.6) & (u < 3.0)
        for sg in (-1.0, 1.0):
            line = r * sg - (2.1 + (u - wu - 1.6) * 0.55)
            out[cloth & pull & (np.abs(line) < 0.28)] -= 1.0
            out[cloth & pull & (line < -0.28) & (line > -0.8)] += 0.5
        return out
    return extra


def _sleeve_crease(upper: bool, L: float):
    """A crease in the crook of the elbow (the upper sleeve's end), a fold near the cuff."""

    def extra(loc, P, nrm, names):
        z = loc[:, 2]
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        ang = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        if upper:
            out[cloth & (z > L * 0.72) & (z < L * 0.86) & (np.abs(ang) < 70)] -= 1.0
        else:
            out[cloth & (z > L * 0.35) & (z < L * 0.5) & (np.abs(ang - 40) < 60)] -= 1.0
        return out
    return extra


def _trouser_folds(shin: bool, L: float):
    """Behind the knee a crease; over the ankle wrap the cloth gathers in a zigzag."""

    def extra(loc, P, nrm, names):
        z = loc[:, 2]
        out = np.zeros(len(loc), dtype=np.float32)
        cloth = names == "cloth"
        ang = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        if shin:
            zig = z / L - 0.62 - 0.05 * np.abs(((ang + 180.0) % 60.0) - 30.0) / 30.0
            out[cloth & (np.abs(zig) < 0.045)] -= 1.0
            out[cloth & (zig > 0.045) & (zig < 0.1)] += 0.5
            out[cloth & (z < L * 0.16) & (np.abs(ang) < 50)] -= 1.0
        else:
            out[cloth & (np.abs(((ang + 200.0) % 120.0) - 60.0) < 7.0) & (z > 1.2)] -= 1.0
        return out
    return extra


def tune_cloth(solids: list, sk, cat: str) -> list:
    """A shirt's or trousers' solids with their folds and creases added to the paint the generator gave them."""
    for s in solids:
        if cat == "shirt":
            if s.part == "skirt" and s.kind == "cone":
                L = float(s.geo["length"])
                s.paint = _wrap(s.paint, "cloth", _skirt_folds(L, L > 10.0))
            elif s.part == "shirt" and s.frame is not None and s.mat == "cloth" and s.paint is not None:
                s.paint = _wrap(s.paint, "cloth", _chest_folds(sk))
            elif s.part.startswith("sleeve_") and s.kind == "cone":
                upper = s.paint is None
                s.paint = _wrap(s.paint, "cloth", _sleeve_crease(upper, float(s.geo["length"])))
        elif cat == "pants":
            if s.part.startswith("leg_") and s.kind == "cone":
                shin = s.paint is not None
                s.paint = _wrap(s.paint, "cloth", _trouser_folds(shin, float(s.geo["length"])))
    return solids


# ------------------------------------------------------------------ the subset
class StudyItem:
    """A game item (figure/sets/) as the study draws it: its cast wrapped with the hand-tuned detail."""

    def __init__(self, it, tuned: bool):
        self.it = it
        self.cat, self.name, self.key, self.label = it.cat, it.name, it.key, it.label
        self.palettes = it.palettes
        self.mats = list(it.mats) + (list(FACE_COLS) if it.cat == "body" else [])
        self.tuned = tuned
        self.weapon = it.cat == "weapon"

    def cast(self, sk) -> list:
        S = self.it.cast(sk)
        if self.cat == "hair":
            S = tune_hair(S, sk, self.name, self.tuned)
        elif self.cat in ("shirt", "pants"):
            S = tune_cloth(S, sk, self.cat)
        return S

    def mat_info(self, name: str) -> dict:
        if self.weapon and name in WEAPON_MATS:
            return WEAPON_MATS[name]
        return MATS.get(name, {})

    def palette(self, variant: str) -> dict:
        pal = dict(self.palettes[variant])
        if self.cat == "body":
            pal.update({k: [v] * 5 for k, v in FACE_COLS.items()})
        return pal


def study_items(needed: dict, tuned: set) -> dict:
    """{key: StudyItem} for the game items named in `needed` ({key: ...}), `tuned` the keys drawn with extra care."""
    sets = sorted({"body", "hair", "shirt", "pants", "shoes", "hat", "cape", "weapon_jian"})
    out = {}
    for it in I.catalog(sets):
        if it.key in needed:
            out[it.key] = StudyItem(it, it.key in tuned)
    return out
