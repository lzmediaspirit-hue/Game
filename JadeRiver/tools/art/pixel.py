"""Jade River creature pixel-art toolkit.

A small, deterministic "vector parts -> cel-shaded pixels" renderer used to author
creature sprite sheets that follow ``docs/art-contracts.md``.

Mental model
------------
* A :class:`Canvas` is one animation frame at *art* resolution (``cell // 2`` px square).
  Coordinates are art pixels, ``x`` to the right, ``y`` down.  Pixel ``(i, j)`` covers
  ``[i, i+1) x [j, j+1)`` so its centre is ``(i + .5, j + .5)``.  Put a shape centre on
  ``.5`` to get an odd pixel width, on ``.0`` for an even width.
* You draw a creature back-to-front out of *parts* (ellipses, capsule limbs, polygons,
  ASCII stamps).  Every part has a :class:`Material` - a hand-picked 4-tone ramp
  ``light / base / shadow / deep`` plus an ``outline`` colour.  Each primitive knows
  its own surface normals (sphere for ellipses, cylinder for limbs, a distance-field
  dome for polygons), so parts are automatically cluster cel-shaded from the upper-left
  light (:data:`LIGHT`).  Orphan pixels in the tone map are cleaned up.
* ``sep=True`` draws a 1 px separation line where the new part overlaps what is already
  on the canvas (e.g. a near leg over the body).  ``decal=True`` paints only on top of
  existing pixels and *inherits their light band*, so spots, stripes and moss follow
  the shading of the surface they sit on.
* Transforms (``cv.xform(rotate(...), translate(...), scale(...))``) act on the geometry
  *before* rasterisation, so a rotated claw is re-rasterised crisply and stays lit
  from the upper left.  :func:`rotate_nn` / :meth:`Canvas.stamp` rotate raster
  pixel art with nearest neighbour sampling only.
* :meth:`Canvas.finish` adds the 1 px silhouette outline (each outline pixel takes
  the ``outline`` colour of the material it borders), composites FX layers and applies
  the stepped frame opacity.  No anti-aliasing, no blur, no smooth resampling anywhere.
* :func:`build_creature` renders the 6 contract rows (idle, walk, windup, attack, hurt,
  death), upscales x2 nearest neighbour, writes ``art/creatures/<id>.png``, checks
  margins / anchors / stray pixels and merges ``data/creature_art.json``.
  :func:`contact_sheet` renders review sheets on dark and earthy backgrounds.

Everything is deterministic: no unseeded randomness (use :func:`hash01`), no
timestamps, PNGs are written without metadata so re-runs are byte-identical.
"""
from __future__ import annotations

import colorsys
import importlib.util
import json
import math
import sys
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------------------
# Paths and contract constants
# --------------------------------------------------------------------------------------
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parents[1]
CREATURES_DIR = TOOLS_DIR / "creatures"
ART_OUT_DIR = PROJECT_ROOT / "art" / "creatures"
MANIFEST_PATH = PROJECT_ROOT / "data" / "creature_art.json"

SCALE = 2  # native pixel scale: 1 art px = 2x2 screen px
MARGIN = 2  # art px of empty border every frame must keep

# (name, frames, fps, loop) in fixed row order - see docs/art-contracts.md
ACTIONS = (
    ("idle", 4, 6, True),
    ("walk", 6, 10, True),
    ("windup", 3, 8, False),
    ("attack", 4, 12, False),
    ("hurt", 2, 10, False),
    ("death", 5, 10, False),
)
ACTION_NAMES = tuple(a[0] for a in ACTIONS)
FRAMES = {a[0]: a[1] for a in ACTIONS}

# --------------------------------------------------------------------------------------
# Colour helpers and palette tokens
# --------------------------------------------------------------------------------------


def rgb(c) -> tuple:
    """'#rrggbb' | (r, g, b) -> (r, g, b) ints."""
    if isinstance(c, str):
        c = c.lstrip("#")
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    return tuple(int(v) for v in c[:3])


def hexs(c) -> str:
    r, g, b = rgb(c)
    return f"#{r:02x}{g:02x}{b:02x}"


def mix(a, b, t: float) -> tuple:
    """Linear blend of two colours (t=0 -> a, t=1 -> b), rounded to ints."""
    a, b = rgb(a), rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _hue_toward(h: float, target: float, amount: float) -> float:
    d = ((target - h + 0.5) % 1.0) - 0.5
    return (h + d * amount) % 1.0


def shift(c, hue_to: float | None = None, hue_amt: float = 0.0, ds: float = 0.0, dv: float = 0.0):
    """HSV tweak: move hue toward ``hue_to`` (degrees) by ``hue_amt`` (0..1), add ds/dv."""
    r, g, b = (v / 255 for v in rgb(c))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if hue_to is not None:
        h = _hue_toward(h, hue_to / 360.0, hue_amt)
    s = min(1.0, max(0.0, s + ds))
    v = min(1.0, max(0.0, v + dv))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


# Contract palette tokens
INK = rgb("#071015")
RIVER_NIGHT = rgb("#0A2027")
DEEP_TEAL = rgb("#0D3035")
JADE_SHADOW = rgb("#15514F")
JADE = rgb("#2C9E8F")
BRIGHT_JADE = rgb("#67D6BD")
AGED_BRONZE = rgb("#9A6A35")
WARM_GOLD = rgb("#E5B84C")
PALE_GOLD = rgb("#FFE6A1")
PAPER = rgb("#E8E1CF")
MIST_BLUE = rgb("#AFC9D1")
WARNING_RED = rgb("#E45858")
QI_CYAN = rgb("#32BED1")
SOUL_VIOLET = rgb("#9B78D1")
HOLLOW_GREY = rgb("#87949A")
GLINT = rgb("#F4F0DE")  # eye glint / specular pixel
EYE_WHITE = rgb("#F7F5EA")  # hollow eyes

# Review backgrounds
BG_DARK = rgb("#0A2027")
BG_EARTH = rgb("#8a7a58")


def auto_outline(c) -> tuple:
    """Dark, slightly hue-tinted outline colour for a region (mostly ink)."""
    return mix(c, INK, 0.78)


# --------------------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------------------
# Lambert cut-offs (N . L) for the 4 tones.  >= hi: light, >= mid: base,
# >= low: shadow, else deep.  Tuned for small chunky parts.
DEFAULT_THRESHOLDS = (0.90, 0.60, 0.22)

# Band remaps for the ``shade=`` argument of primitives.
SHADE_MODES = {
    "full": (0, 1, 2, 3),  # light, base, shadow, deep
    "soft": (0, 1, 2, 2),  # no deep tone - small parts
    "nolight": (1, 1, 2, 3),  # no highlight - parts in shade / behind
    "two": (1, 1, 2, 2),  # base + shadow only
    "dark": (2, 2, 3, 3),  # far-side limbs: shadow + deep
    "flat": (1, 1, 1, 1),
    "flatdark": (2, 2, 2, 2),
    "flatlight": (0, 0, 0, 0),
}


@dataclass(frozen=True)
class Material:
    """A 4-tone cel ramp for one part.  Colours are (r, g, b) tuples.

    ``outline`` colours the silhouette/separation lines next to this material.
    ``accent`` is a free extra colour for details (claw tips, stripes...).
    ``thresholds`` overrides :data:`DEFAULT_THRESHOLDS` for this material.
    """

    name: str
    light: tuple
    base: tuple
    shadow: tuple
    deep: tuple
    outline: tuple = INK
    accent: tuple | None = None
    thresholds: tuple = DEFAULT_THRESHOLDS

    @property
    def tones(self) -> tuple:
        return (self.light, self.base, self.shadow, self.deep)

    def step(self, k: int = 1) -> "Material":
        """Same ramp shifted ``k`` tones darker (k < 0: lighter), clamped at the ends.

        Use it for decals that must follow the surface's light band but read as a
        crease / seam (``k=1``) or a raised edge (``k=-1``)."""
        t = self.tones
        s = tuple(t[min(3, max(0, i + k))] for i in range(4))
        return replace(self, name=f"{self.name}{'+' if k >= 0 else ''}{k}", light=s[0], base=s[1],
                       shadow=s[2], deep=s[3])

    def with_(self, **kw) -> "Material":
        kw = {k: (rgb(v) if k in ("light", "base", "shadow", "deep", "outline", "accent") and v is not None else v)
              for k, v in kw.items()}
        return replace(self, **kw)


def material(name, light, base, shadow, deep, outline=None, accent=None, thresholds=DEFAULT_THRESHOLDS) -> Material:
    """Hand-picked ramp (preferred for final art).  Hex strings or tuples."""
    deep_c = rgb(deep)
    return Material(name, rgb(light), rgb(base), rgb(shadow), deep_c,
                    rgb(outline) if outline is not None else auto_outline(deep_c),
                    rgb(accent) if accent is not None else None, tuple(thresholds))


def ramp(base, name: str = "ramp", light: float = 0.16, dark: float = 0.20, warm: float = 0.30,
         cool: float = 0.25, accent=None, outline=None) -> Material:
    """Automatic hue-shifted ramp from one base colour.

    Highlights move toward warm gold (hue 48) and get brighter; shadows move toward
    blue-green (hue 195) and get darker and a bit more saturated.  Good for quick
    blocking - hand-tune final colours with :func:`material`.
    """
    b = rgb(base)
    li = shift(b, 48, warm, ds=-0.06, dv=light)
    sh = shift(b, 195, cool, ds=0.04, dv=-dark)
    dp = shift(b, 205, cool * 1.6, ds=0.06, dv=-dark * 1.9)
    return material(name, li, b, sh, dp, outline=outline, accent=accent)


def flat(color, outline=None, name="flat") -> Material:
    """Single-colour material (all tones equal) - for stamps, pixels, eyes."""
    c = rgb(color)
    return Material(name, c, c, c, c, rgb(outline) if outline is not None else auto_outline(c))


HOLLOW_DARK = rgb("#3a444b")
HOLLOW_LIGHT = rgb("#eef2ef")
HOLLOW_OUTLINE = rgb("#141a1f")


def hollow_material(mat: "Material") -> "Material":
    """Grey-white Hollow version of a material that keeps its light/dark structure
    (each tone is re-coloured by its luminance on the #87949A family)."""
    def g(c):
        r, gg, b = rgb(c)
        lum = (0.299 * r + 0.587 * gg + 0.114 * b) / 255.0
        return mix(HOLLOW_DARK, HOLLOW_LIGHT, min(1.0, max(0.0, 0.12 + lum * 1.1)))
    return replace(mat, name=f"hollow_{mat.name}", light=g(mat.light), base=g(mat.base),
                   shadow=g(mat.shadow), deep=g(mat.deep), outline=HOLLOW_OUTLINE,
                   accent=g(mat.accent) if mat.accent is not None else None)


# Element ramps (hue families from the README).  Copy/tweak per creature.
ELEMENTS = {
    "water": material("water", "#8fe3d0", "#3aa9a0", "#1f6f78", "#15414f", outline="#08171d"),
    "earth": material("earth", "#c9985a", "#9a6a3a", "#6b4a33", "#43302a", outline="#1b1512"),
    "stone": material("stone", "#b9bcb2", "#8b8f8a", "#5f6668", "#3c4448", outline="#12181b"),
    "wood": material("wood", "#9fd070", "#5f9a45", "#3a6a3c", "#23443a", outline="#0c1a14"),
    "fire": material("fire", "#ffd27a", "#f08a3a", "#c24a32", "#7a2a2e", outline="#1f0c10"),
    "wind": material("wind", "#ffffff", "#dcecf2", "#a9c6d6", "#7a98b4", outline="#1a2a3a"),
    "thunder": material("thunder", "#6e8fe0", "#3552a8", "#22346e", "#161f48", outline="#070b1c",
                        accent="#ffd84a"),
    "soul": material("soul", "#d9c6f5", "#9b78d1", "#6a4f9e", "#3f2f6a", outline="#120c22"),
    "hollow": material("hollow", "#dfe4e2", "#b4bdbf", "#87949a", "#5c666e", outline="#161c21"),
}

# Common detail materials
BONE = material("bone", "#fbf4dc", "#e9dcb8", "#bfae88", "#8a7b5e", outline="#241d16")
HORN = material("horn", "#d8c79a", "#a8946a", "#77684c", "#4e4536", outline="#17130f")
FLESH_PINK = material("flesh", "#f3b8a8", "#d98a86", "#a95f66", "#6e3c4a", outline="#1f1016")
DUST = material("dust", "#f2e6c4", "#d9c69c", "#b6a079", "#927d5c", outline="#4d3f2d")
WATER_FX = material("splash", "#e9fbf6", "#9fe6dc", "#4fb7b4", "#2a7f8a", outline="#15414f")

# Light direction (x right, y down, z toward the viewer): upper-left, in front.
LIGHT = np.array([-0.62, -0.78, 0.95])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

# --------------------------------------------------------------------------------------
# Small math helpers
# --------------------------------------------------------------------------------------


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pt(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def polar(p, deg: float, length: float):
    """Point ``length`` away from ``p`` at ``deg`` degrees (0 = right, 90 = UP)."""
    a = math.radians(deg)
    return (p[0] + math.cos(a) * length, p[1] - math.sin(a) * length)


def rot_pt(p, deg: float, pivot=(0.0, 0.0)):
    """Rotate point counter-clockwise (on screen) by ``deg`` about ``pivot``."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + c * x + s * y, pivot[1] - s * x + c * y)


def ik2(root, target, l1: float, l2: float, bend: int = 1):
    """Two-bone IK: elbow/knee position for a limb root -> target with segment lengths
    ``l1``, ``l2``.  ``bend`` +1 puts the joint on the counter-clockwise side of the
    root->target line (for a right-facing creature: +1 bends a leg's knee forward when
    the limb points down, and an arm's elbow up/back when it points right)."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = max(1e-6, math.hypot(dx, dy))
    d_c = min(d, l1 + l2 - 1e-6)
    a = (l1 * l1 - l2 * l2 + d_c * d_c) / (2 * d_c)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    mx, my = root[0] + ux * a, root[1] + uy * a
    # counter-clockwise normal on screen (y down) is (uy, -ux)
    return (mx + uy * h * bend, my - ux * h * bend)


def hash01(*args) -> float:
    """Deterministic pseudo-random float in [0, 1) from integer-ish arguments."""
    h = 2166136261
    for a in args:
        for byte in str(a).encode():
            h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)


# --------------------------------------------------------------------------------------
# Affine transforms (3x3, applied to column vectors).  Angles: + = counter-clockwise.
# --------------------------------------------------------------------------------------


def translate(dx: float, dy: float) -> np.ndarray:
    return np.array([[1.0, 0, dx], [0, 1.0, dy], [0, 0, 1.0]])


def rotate(deg: float, pivot=(0.0, 0.0)) -> np.ndarray:
    """Counter-clockwise on screen (nose-up for a right-facing creature)."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    px_, py_ = pivot
    r = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1.0]])
    return translate(px_, py_) @ r @ translate(-px_, -py_)


def scale(sx: float, sy: float | None = None, pivot=(0.0, 0.0)) -> np.ndarray:
    """Squash/stretch about ``pivot`` (use the feet/anchor to keep feet planted)."""
    sy = sx if sy is None else sy
    px_, py_ = pivot
    return translate(px_, py_) @ np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1.0]]) @ translate(-px_, -py_)


def flip_y(pivot_y: float) -> np.ndarray:
    """Mirror vertically about a horizontal line (turn a creature on its back)."""
    return scale(1.0, -1.0, (0.0, pivot_y))


def flip_x(pivot_x: float) -> np.ndarray:
    return scale(-1.0, 1.0, (pivot_x, 0.0))


# --------------------------------------------------------------------------------------
# Mask utilities
# --------------------------------------------------------------------------------------


def _shift(a: np.ndarray, dx: int, dy: int, fill=0) -> np.ndarray:
    """Shift array content by (dx, dy): out[y, x] = a[y - dy, x - dx]."""
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    xs0, xs1 = max(0, dx), min(w, w + dx)
    ys0, ys1 = max(0, dy), min(h, h + dy)
    out[ys0:ys1, xs0:xs1] = a[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


N4 = ((0, -1), (-1, 0), (1, 0), (0, 1))
N8 = N4 + ((-1, -1), (1, -1), (-1, 1), (1, 1))


def dilate(m: np.ndarray, diag: bool = False) -> np.ndarray:
    o = m.copy()
    for dx, dy in (N8 if diag else N4):
        o |= _shift(m, dx, dy, False)
    return o


def erode(m: np.ndarray, diag: bool = False) -> np.ndarray:
    o = m.copy()
    for dx, dy in (N8 if diag else N4):
        o &= _shift(m, dx, dy, False)
    return o


def _clean_bands(band: np.ndarray, mask: np.ndarray, passes: int = 2) -> np.ndarray:
    """Replace orphan tone pixels (no 4-neighbour of the same tone) by the local majority."""
    band = band.copy()
    for _ in range(passes):
        counts = np.zeros((4,) + band.shape, np.int16)
        same = np.zeros(band.shape, np.int16)
        for dx, dy in N4:
            nb = _shift(band, dx, dy, -1)
            nm = _shift(mask, dx, dy, False)
            same += (nm & (nb == band)).astype(np.int16)
            for k in range(4):
                counts[k] += (nm & (nb == k)).astype(np.int16)
        orphan = mask & (same == 0) & (counts.sum(0) > 0)
        if not orphan.any():
            break
        band[orphan] = np.argmax(counts, axis=0)[orphan]
    return band


# --------------------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------------------


class Canvas:
    """One frame at art resolution.  See module docstring.

    Attributes you will use while drawing:
      ``w, h``    canvas size in art px (``cell // 2``)
      ``gx, gy``  anchor in art px: ``gx`` is the ground point between the feet, ``gy``
                  the ground line.  The outline pass puts the last opaque row on
                  ``gy - 1``, so feet must fill row ``gy - 2`` and nothing below it.
      ``ground``  == ``gy - 1.5``, the centre of row ``gy - 2``: end foot limbs here
                  (tip radius <= 0.5) or keep shape bottoms at ``<= gy - 1``.
      ``opacity``      stepped whole-frame opacity for death fades (e.g. 0.6, 0.3).
      ``snap_ground``  True: finish() shifts the frame so its lowest body pixel sits
                       on ``gy - 1`` (tumbling / lying poses).
      ``hollow``       True: Hollow variant - every material is re-coloured grey-white
                       (:func:`hollow_material`) and parts named ``"eye"`` become empty
                       white eyes.  Set it first thing in ``draw``.
    """

    def __init__(self, w: int, h: int, anchor=None, light=LIGHT, _parent=None):
        self.w, self.h = int(w), int(h)
        if anchor is None:
            anchor = (self.w // 2, self.h - self.h // 8)
        self.gx, self.gy = anchor
        self.ground = self.gy - 1.5
        self.light = np.asarray(light, float)
        self.rgb = np.zeros((self.h, self.w, 3), np.uint8)
        self.filled = np.zeros((self.h, self.w), bool)
        self.band = np.full((self.h, self.w), -1, np.int8)
        self.mat = np.full((self.h, self.w), -1, np.int16)
        self.part = np.full((self.h, self.w), -1, np.int16)
        self.materials: list[Material] = []
        self._mat_ix: dict = {}
        self.parts: list[str] = []
        self.opacity = 1.0
        self.outline_enabled = True
        self.outline_color = None  # force one colour for the silhouette (e.g. INK)
        self.snap_ground = False  # finish(): drop/raise the frame onto the ground row
        self.hollow = False  # Hollow variant: grey-white materials, parts named "eye" go white
        self._stack = _parent._stack if _parent is not None else [np.eye(3)]
        self._layers: list[tuple[bool, "Canvas"]] = []
        xs = np.arange(self.w) + 0.5
        ys = np.arange(self.h) + 0.5
        self.X, self.Y = np.meshgrid(xs, ys)
        self.body_image = None  # outlined body only, set by finish()

    # ---- transforms -----------------------------------------------------------------
    @property
    def M(self) -> np.ndarray:
        return self._stack[-1]

    @contextmanager
    def xform(self, *mats):
        """``with cv.xform(A, B): ...`` draws with p -> A @ B @ p (B applied first).

        Nested blocks compose the same way (outer block is applied last).
        """
        m = self.M
        for a in mats:
            m = m @ a
        self._stack.append(m)
        try:
            yield self
        finally:
            self._stack.pop()

    def tp(self, p):
        """Transform a local point to canvas coordinates."""
        v = self.M @ np.array([p[0], p[1], 1.0])
        return (float(v[0]), float(v[1]))

    def _tscale(self) -> float:
        return math.sqrt(abs(np.linalg.det(self.M[:2, :2])))

    # ---- bookkeeping ----------------------------------------------------------------
    def _mi(self, mat: Material) -> int:
        if mat not in self._mat_ix:
            self._mat_ix[mat] = len(self.materials)
            self.materials.append(mat)
        return self._mat_ix[mat]

    def _pi(self, name) -> int:
        if name is None:
            return -1
        if name not in self.parts:
            self.parts.append(name)
        return self.parts.index(name)

    def mask_of(self, names) -> np.ndarray:
        """Boolean mask of pixels currently owned by part name(s)."""
        if isinstance(names, str):
            names = [names]
        m = np.zeros((self.h, self.w), bool)
        for n in names:
            if n in self.parts:
                m |= self.part == self.parts.index(n)
        return m

    def layer(self, above: bool = True, outline: bool = True) -> "Canvas":
        """Create an FX layer (dust, splash, glow) composited in :meth:`finish`.

        The layer shares this canvas' transform stack.  ``outline`` outlines the
        layer's own silhouette with each material's outline colour.
        """
        c = Canvas(self.w, self.h, (self.gx, self.gy), self.light, _parent=self)
        c.outline_enabled = outline
        self._layers.append((above, c))
        return c

    # ---- core commit ----------------------------------------------------------------
    @staticmethod
    def _as_mat(m) -> Material:
        return m if isinstance(m, Material) else flat(m)

    def _bands(self, mask, nx, ny, nz, mat: Material, shade, bulge: float) -> np.ndarray:
        if isinstance(shade, int):
            return np.where(mask, shade, -1).astype(np.int8)
        if bulge != 1.0:
            nx, ny = nx * bulge, ny * bulge
        n = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        lam = (nx * self.light[0] + ny * self.light[1] + nz * self.light[2]) / n
        hi, mid, low = mat.thresholds
        band = np.full(mask.shape, 3, np.int8)
        band[lam >= low] = 2
        band[lam >= mid] = 1
        band[lam >= hi] = 0
        band = _clean_bands(np.where(mask, band, -1).astype(np.int8), mask)
        remap = np.array(SHADE_MODES[shade] if isinstance(shade, str) else shade, np.int8)
        out = np.where(mask, remap[np.clip(band, 0, 3)], -1).astype(np.int8)
        return out

    def _commit(self, mask, band, mat, name=None, sep=False, decal=False, clip=None,
                erase=False, under=False):
        mask = mask.copy()
        if clip is not None:
            mask &= self.mask_of(clip) if not isinstance(clip, np.ndarray) else clip
        if erase:
            self.filled[mask] = False
            self.band[mask] = -1
            self.mat[mask] = -1
            self.part[mask] = -1
            self.rgb[mask] = 0
            return mask
        if decal:
            mask &= self.filled
            band = np.where(self.band >= 0, self.band, band)
        if under:  # draw only where nothing is yet (behind everything drawn so far)
            mask &= ~self.filled
        if not mask.any():
            return mask
        mat = self._as_mat(mat)
        if self.hollow:  # contract: grey-white body, empty white eyes, same silhouette
            mat = flat(EYE_WHITE, outline=INK) if name == "eye" else hollow_material(mat)
        if sep is not False and sep is not None:
            ring = dilate(mask) & ~mask & self.filled
            if ring.any():
                if sep is True or sep == "outline":
                    self.rgb[ring] = mat.outline
                elif sep == "deep":  # the underlying part's darkest tone
                    for mi in np.unique(self.mat[ring]):
                        sel = ring & (self.mat == mi)
                        self.rgb[sel] = self.materials[mi].deep if mi >= 0 else mat.outline
                else:
                    self.rgb[ring] = rgb(sep)
                self.band[ring] = 3
        mi = self._mi(mat)
        tones = np.array(mat.tones, np.uint8)
        b = np.clip(band, 0, 3)
        self.rgb[mask] = tones[b[mask]]
        self.filled[mask] = True
        self.band[mask] = b[mask]
        self.mat[mask] = mi
        self.part[mask] = self._pi(name)
        return mask

    def fill(self, mask, mat, normals=None, **kw) -> np.ndarray:
        """Commit an arbitrary boolean mask.  ``normals`` = (nx, ny, nz) arrays or None
        (then a distance-field dome is used)."""
        if normals is None:
            normals = _dome_normals(mask) if mask.any() else (np.zeros(mask.shape),) * 3
        return self.draw_geom((mask,) + tuple(normals), mat, **kw)

    # ---- geometry (masks + normals, current transform applied) -----------------------
    def geom_ellipse(self, cx, cy, rx, ry, angle=0.0):
        """-> (mask, nx, ny, nz) of a filled ellipse (angle in degrees, CCW)."""
        a = math.radians(angle)
        c, s = math.cos(a), math.sin(a)
        local = np.array([[c * rx, s * ry], [-s * rx, c * ry]])  # unit disk -> local
        L = self.M[:2, :2] @ local
        C = self.tp((cx, cy))
        if abs(np.linalg.det(L)) < 1e-9:
            z = np.zeros((self.h, self.w))
            return z.astype(bool), z, z, z
        Li = np.linalg.inv(L)
        dx, dy = self.X - C[0], self.Y - C[1]
        u = Li[0, 0] * dx + Li[0, 1] * dy
        v = Li[1, 0] * dx + Li[1, 1] * dy
        q2 = u * u + v * v
        # screen-space normal direction: L^-T (u, v), scaled to |q|
        gx = Li[0, 0] * u + Li[1, 0] * v
        gy = Li[0, 1] * u + Li[1, 1] * v
        gl = np.sqrt(gx * gx + gy * gy) + 1e-9
        q = np.sqrt(q2)
        return q2 <= 1.0, gx / gl * q, gy / gl * q, np.sqrt(np.clip(1 - q2, 0, 1))

    def geom_limb(self, points, radii):
        """-> (mask, nx, ny, nz) of a rounded, optionally tapered poly-line."""
        pts = [self.tp(p) for p in points]
        k = self._tscale()
        if isinstance(radii, (int, float)):
            radii = [radii] * len(pts)
        radii = [r * k for r in radii]
        best = np.full((self.h, self.w), -1e9)
        nx = np.zeros((self.h, self.w))
        ny = np.zeros((self.h, self.w))
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            r0, r1 = radii[i], radii[i + 1]
            dx, dy = x1 - x0, y1 - y0
            l2 = dx * dx + dy * dy
            if l2 < 1e-9:
                t = np.zeros_like(self.X)
            else:
                t = np.clip(((self.X - x0) * dx + (self.Y - y0) * dy) / l2, 0, 1)
            cxs, cys = x0 + t * dx, y0 + t * dy
            r = np.maximum(r0 + (r1 - r0) * t, 1e-6)
            vx, vy = self.X - cxs, self.Y - cys
            score = 1 - np.sqrt(vx * vx + vy * vy) / r
            upd = score > best
            best = np.where(upd, score, best)
            nx = np.where(upd, vx / r, nx)
            ny = np.where(upd, vy / r, ny)
        nz = np.sqrt(np.clip(1 - (nx * nx + ny * ny), 0, 1))
        return best >= 0, nx, ny, nz

    def geom_polygon(self, points):
        """-> (mask, nx, ny, nz); dome normals from a distance field."""
        mask = _poly_mask(self.X, self.Y, [self.tp(p) for p in points])
        if not mask.any():
            z = np.zeros((self.h, self.w))
            return mask, z, z, z + 1
        return (mask,) + _dome_normals(mask)

    @staticmethod
    def union(*geoms, weights=None):
        """Merge ``geom_*`` results into one shape shaded as a single form.

        Where shapes overlap, the normal of the most "inside" shape (largest nz x
        weight) wins, so a haunch + chest + head read as one body with one highlight
        instead of three separately lit blobs.  ``weights`` biases which shape
        dominates (e.g. a bigger haunch)."""
        weights = weights or [1.0] * len(geoms)
        mask = np.zeros_like(geoms[0][0])
        best = np.full(mask.shape, -1.0)
        nx = np.zeros(mask.shape)
        ny = np.zeros(mask.shape)
        nz = np.zeros(mask.shape)
        for (m, gx, gy, gz), w in zip(geoms, weights):
            score = np.where(m, gz * w, -1.0)
            upd = score > best
            best = np.where(upd, score, best)
            nx, ny, nz = np.where(upd, gx, nx), np.where(upd, gy, ny), np.where(upd, gz, nz)
            mask = mask | m
        return mask, nx, ny, nz

    def mask_ellipse(self, cx, cy, rx, ry, angle=0.0) -> np.ndarray:
        return self.geom_ellipse(cx, cy, rx, ry, angle)[0]

    def mask_polygon(self, points) -> np.ndarray:
        return _poly_mask(self.X, self.Y, [self.tp(p) for p in points])

    def mask_limb(self, points, radii) -> np.ndarray:
        return self.geom_limb(points, radii)[0]

    # ---- primitives -----------------------------------------------------------------
    # Common keyword arguments of every primitive:
    #   name   part name (for clip= / mask_of())      shade  SHADE_MODES key, 4-tuple or int
    #   bulge  >1 rounder / <1 flatter shading        sep    separation line: True/"outline",
    #   minus  mask(s) removed from the shape                "deep" or a colour
    #   decal  paint only over existing pixels, inheriting their light band
    #   clip   part name(s) or mask to restrict to    under  only where nothing is drawn yet
    #   erase  cut the shape out of the canvas (transparent)
    def draw_geom(self, geom, mat, shade="full", bulge=1.0, minus=None, **kw) -> np.ndarray:
        """Shade and commit a (mask, nx, ny, nz) tuple from a ``geom_*`` method."""
        mask, nx, ny, nz = geom
        mat = self._as_mat(mat)
        if minus is not None:
            mask = mask.copy()
            for m in (minus if isinstance(minus, (list, tuple)) else [minus]):
                mask &= ~m
        band = self._bands(mask, nx, ny, nz, mat, shade, bulge)
        return self._commit(mask, band, mat, **kw)

    def ellipse(self, cx, cy, rx, ry, mat, angle=0.0, **kw) -> np.ndarray:
        """Filled ellipse, sphere-like shading."""
        return self.draw_geom(self.geom_ellipse(cx, cy, rx, ry, angle), mat, **kw)

    def circle(self, cx, cy, r, mat, **kw) -> np.ndarray:
        return self.ellipse(cx, cy, r, r, mat, **kw)

    def limb(self, points, radii, mat, **kw) -> np.ndarray:
        """Thick poly-line with rounded ends and joints: legs, tails, necks, antennae.

        ``points`` [(x, y), ...] (>= 2), ``radii`` a number or one radius per point
        (tapering).  A radius r gives roughly 2r px thickness.  Cylinder shading.
        """
        return self.draw_geom(self.geom_limb(points, radii), mat, **kw)

    def capsule(self, p0, p1, r0, mat, r1=None, **kw) -> np.ndarray:
        """Single-segment limb from p0 to p1 (radius r0 tapering to r1)."""
        return self.limb([p0, p1], [r0, r0 if r1 is None else r1], mat, **kw)

    def polygon(self, points, mat, **kw) -> np.ndarray:
        """Filled polygon (even-odd) with a distance-field dome for shading."""
        return self.draw_geom(self.geom_polygon(points), mat, **kw)

    def rect(self, x, y, w, h, mat, **kw) -> np.ndarray:
        return self.polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], mat, **kw)

    def pixel(self, x, y, color, name=None, band=1, **kw) -> np.ndarray:
        """Set one pixel (local coords of the pixel's top-left corner, transformed)."""
        return self.pixels([(x, y)], color, name=name, band=band, **kw)

    def pixels(self, pts, color, name=None, band=1, **kw) -> np.ndarray:
        mat = self._as_mat(color)
        mask = np.zeros((self.h, self.w), bool)
        for (x, y) in pts:
            cx, cy = self.tp((x + 0.5, y + 0.5))
            ix, iy = int(math.floor(cx)), int(math.floor(cy))
            if 0 <= ix < self.w and 0 <= iy < self.h:
                mask[iy, ix] = True
        b = np.where(mask, 1 if band is None else band, -1).astype(np.int8)
        return self._commit(mask, b, mat, name=name, **kw)

    def line(self, p0, p1, color, name=None, band=1, **kw) -> np.ndarray:
        """1 px Bresenham line between pixel coords (transformed, then rounded)."""
        a = self.tp((p0[0] + 0.5, p0[1] + 0.5))
        b = self.tp((p1[0] + 0.5, p1[1] + 0.5))
        x0, y0 = int(math.floor(a[0])), int(math.floor(a[1]))
        x1, y1 = int(math.floor(b[0])), int(math.floor(b[1]))
        mask = np.zeros((self.h, self.w), bool)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if 0 <= x0 < self.w and 0 <= y0 < self.h:
                mask[y0, x0] = True
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        mat = self._as_mat(color)
        b = np.where(mask, 1 if band is None else band, -1).astype(np.int8)
        return self._commit(mask, b, mat, name=name, **kw)

    def stamp(self, rows, x, y, palette: dict, name=None, **kw) -> np.ndarray:
        """Paste hand-drawn ASCII pixel art.  ``rows`` is a list of equal-length strings;
        ``.`` and space are transparent, other characters index ``palette``
        (colour or Material -> base tone, or (Material, band)).  ``(x, y)`` is the
        top-left pixel in local coords.  Transforms are applied by nearest-neighbour
        inverse mapping (crisp rotation, no holes)."""
        hgt, wid = len(rows), max(len(r) for r in rows)
        corners = [self.tp((x, y)), self.tp((x + wid, y)), self.tp((x, y + hgt)), self.tp((x + wid, y + hgt))]
        x0 = max(0, int(math.floor(min(c[0] for c in corners))) - 1)
        x1 = min(self.w, int(math.ceil(max(c[0] for c in corners))) + 1)
        y0 = max(0, int(math.floor(min(c[1] for c in corners))) - 1)
        y1 = min(self.h, int(math.ceil(max(c[1] for c in corners))) + 1)
        Mi = np.linalg.inv(self.M)
        out = {}
        for py in range(y0, y1):
            for px_ in range(x0, x1):
                lx, ly, _ = Mi @ np.array([px_ + 0.5, py + 0.5, 1.0])
                i, j = int(math.floor(lx - x)), int(math.floor(ly - y))
                if 0 <= j < hgt and 0 <= i < len(rows[j]):
                    ch = rows[j][i]
                    if ch not in ". ":
                        out.setdefault(ch, []).append((px_, py))
        total = np.zeros((self.h, self.w), bool)
        for ch in sorted(out):
            entry = palette[ch]
            if isinstance(entry, tuple) and len(entry) == 2 and isinstance(entry[0], Material):
                mat, band = entry
            else:
                mat, band = self._as_mat(entry), 1
            mask = np.zeros((self.h, self.w), bool)
            for (px_, py) in out[ch]:
                mask[py, px_] = True
            total |= self._commit(mask, np.where(mask, band, -1).astype(np.int8), mat, name=name, **kw)
        return total

    # ---- detail helpers -------------------------------------------------------------
    def eye(self, x, y, size=2, state="open", iris=None, hollow=False, ink=INK, glint=GLINT,
            white=EYE_WHITE, name="eye") -> np.ndarray:
        """Stamp a small eye for a right-facing creature.  ``(x, y)`` = top-left pixel.

        ``size`` 1..4.  ``state``: ``open`` | ``angry`` (open + brow slanting down toward
        the snout) | ``squeeze`` (hurt: a '>' chevron) | ``closed`` | ``dead`` (x).
        ``iris`` colours the ring around the pupil (sizes 3-4).  ``hollow=True`` gives
        the empty white Hollow eye (no pupil, no glint).  Patterns live in ``EYES``;
        creatures are free to stamp their own.
        """
        key = (size, "open" if state == "angry" else state)
        if key not in EYES:
            raise ValueError(f"no eye pattern for size={size} state={state}")
        rows = EYES[key]
        if hollow and key[1] == "open":
            rows = [r.replace("g", "w").replace("k", "w").replace("i", "w") for r in rows]
        pal = {"k": ink, "g": glint, "w": white, "i": iris if iris is not None else ink}
        m = self.stamp(rows, x, y, pal, name=name)
        if state == "angry":  # brow: high at the back, low at the front
            bw = max(2, size)
            m |= self.pixels([(x + i, y - 2 + (1 if i >= bw // 2 else 0)) for i in range(bw)], ink, name=name)
        return m

    # ---- output ---------------------------------------------------------------------
    def _outlined(self) -> np.ndarray:
        img = np.zeros((self.h, self.w, 4), np.uint8)
        img[..., :3] = self.rgb
        img[..., 3] = np.where(self.filled, 255, 0)
        if self.outline_enabled:
            ring = dilate(self.filled) & ~self.filled
            if self.outline_color is not None:
                img[ring, :3] = rgb(self.outline_color)
            else:
                outl = np.array([m.outline for m in self.materials] + [INK], np.uint8)
                # each outline pixel takes the outline colour of a filled 4-neighbour;
                # later directions win, so priority is: below > right > left > above
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    nb_filled = _shift(self.filled, -dx, -dy, False)
                    nb_mat = _shift(self.mat, -dx, -dy, -1)
                    sel = ring & nb_filled
                    img[sel, :3] = outl[nb_mat[sel]]
            img[ring, 3] = 255
        return img

    def finish(self) -> np.ndarray:
        """Outline, composite layers, apply stepped opacity -> RGBA uint8 (h, w, 4).

        If ``self.snap_ground`` is True the whole frame is shifted vertically (whole
        pixels) so the lowest body pixel sits on the ground row ``gy - 1`` - handy for
        tumbling/flipped death poses whose lowest point is hard to predict.
        """
        body = self._outlined()
        layers = [(above, c._outlined()) for above, c in self._layers]
        if self.snap_ground and body[..., 3].any():
            low = int(np.nonzero(body[..., 3].any(1))[0].max())
            dy = (self.gy - 1) - low
            body = _shift(body, 0, dy, 0)
            layers = [(a, _shift(img, 0, dy, 0)) for a, img in layers]
        self.body_image = body
        out = np.zeros_like(body)
        stack = [img for a, img in layers if not a] + [body] + [img for a, img in layers if a]
        for img in stack:
            m = img[..., 3] > 0
            out[m] = img[m]
        if self.opacity < 1.0:
            a = int(round(255 * max(0.0, self.opacity)))
            out[..., 3] = np.where(out[..., 3] > 0, a, 0).astype(np.uint8)
        return out


# Eye patterns (right-facing, top-left anchored): k ink, g glint, i iris, w white.
EYES = {
    (1, "open"): ["k"],
    (1, "squeeze"): ["k"],
    (1, "closed"): ["k"],
    (1, "dead"): ["k"],
    (2, "open"): ["gk", "kk"],
    (2, "squeeze"): ["k.", ".k", "k."],
    (2, "closed"): ["kk"],
    (2, "dead"): ["k.k", ".k.", "k.k"],
    (3, "open"): ["gik", "ikk", ".k."],
    (3, "squeeze"): ["k..", ".kk", "k.."],
    (3, "closed"): ["...", "kkk"],
    (3, "dead"): ["k.k", ".k.", "k.k"],
    (4, "open"): [".ii.", "igki", "ikki", ".ii."],
    (4, "squeeze"): ["kk..", "..kk", "kk.."],
    (4, "closed"): ["....", "kkkk", ".kk."],
    (4, "dead"): ["k..k", ".kk.", ".kk.", "k..k"],
}


def _poly_mask(X, Y, pts) -> np.ndarray:
    inside = np.zeros(X.shape, bool)
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if y0 == y1:
            continue
        cond = (y0 > Y) != (y1 > Y)
        xint = (x1 - x0) * (Y - y0) / (y1 - y0) + x0
        inside ^= cond & (X < xint)
    return inside


def _dome_normals(mask: np.ndarray):
    """Normals of a rounded dome over an arbitrary mask (distance-field based)."""
    h, w = mask.shape
    pad = np.pad(mask, 1)
    edge = dilate(pad) & ~pad
    ey, ex = np.nonzero(edge)
    iy, ix = np.nonzero(pad)
    height = np.zeros(pad.shape)
    if len(iy) and len(ey):
        d = np.full(len(iy), np.inf)
        for s in range(0, len(ey), 256):
            ddx = ix[:, None] - ex[None, s:s + 256]
            ddy = iy[:, None] - ey[None, s:s + 256]
            d = np.minimum(d, np.sqrt(ddx * ddx + ddy * ddy).min(1))
        d = d - 0.5
        R = max(d.max(), 0.5)
        hh = np.sqrt(np.clip(R * R - (R - d) ** 2, 0, None))
        height[iy, ix] = hh / R * min(R, 6.0)
    # smooth (3x3 box, twice) to get stable gradients
    for _ in range(2):
        acc = np.zeros_like(height)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                acc += _shift(height, dx, dy, 0.0)
        height = np.where(pad, acc / 9.0, 0.0)
    gy, gx = np.gradient(height)
    nx, ny = -gx[1:-1, 1:-1], -gy[1:-1, 1:-1]
    nz = np.ones_like(nx) * 0.9
    return nx, ny, nz


def rotate_nn(img: np.ndarray, deg: float, pivot) -> np.ndarray:
    """Rotate an RGBA art-res array CCW about ``pivot`` with nearest-neighbour sampling."""
    h, w = img.shape[:2]
    Mi = np.linalg.inv(rotate(deg, pivot))
    X, Y = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    sx = Mi[0, 0] * X + Mi[0, 1] * Y + Mi[0, 2]
    sy = Mi[1, 0] * X + Mi[1, 1] * Y + Mi[1, 2]
    ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    out = np.zeros_like(img)
    out[ok] = img[iy[ok], ix[ok]]
    return out


# --------------------------------------------------------------------------------------
# FX helpers (draw on a layer: ``fx = cv.layer(above=True)``)
# --------------------------------------------------------------------------------------


def dust(cv: Canvas, x: float, y: float, t: float, size: float = 1.0, direction: int = -1,
         mat: Material = DUST) -> None:
    """Ground dust puff at (x, y = ground line) for life ``t`` in [0, 1].

    t = 0 is a small puff at the hoof; it grows into three lumpy clusters drifting in
    ``direction`` (-1 = backward, i.e. left for a right-facing creature), rises a
    little and breaks into specks after t > 0.6.  Draw it on an outlined FX layer:
    ``px.dust(cv.layer(above=True), x, cv.gy - 1, t)``.
    """
    if t < 0 or t > 1:
        return
    grow = min(1.0, 0.5 + t * 1.5)
    shrink = 1.0 - max(0.0, (t - 0.6) / 0.4) * 0.55
    puffs = ((0.0, 0.0, 2.5), (3.2, -0.4, 2.0), (-2.8, -0.2, 1.6), (1.2, -2.6, 1.7))
    for i, (ox, oy, r) in enumerate(puffs):
        if i == 3 and t < 0.2:
            continue
        rr = max(0.8, r * size * grow * shrink)
        cx = x + direction * (ox + t * 3.5 * (0.6 + 0.3 * i)) * size
        cy = y - rr + oy * size * grow - t * 1.5 * size
        cv.circle(cx, cy, rr, mat, shade="soft", name="dust")
    if t > 0.45:  # detached specks
        speck = flat(mat.light, outline=mat.outline)
        for i in range(2):
            sx = x + direction * (6.5 + i * 2.5 + t * 2.5) * size
            sy = y - 3.0 - i * 2.5 - t * 2.0
            cv.pixel(math.floor(sx), math.floor(sy), speck, name="dust")


def glow_ring(cv: Canvas, cx: float, cy: float, r: float, color, thickness: float = 1.0,
              inner=None) -> None:
    """Crisp pixel ring (Qi charge, wards).  ``inner`` adds a lighter inside ring."""
    d = np.hypot(cv.X - cx, cv.Y - cy)
    m = np.abs(d - r) <= thickness * 0.5 + 0.25
    cv._commit(m, np.where(m, 1, -1).astype(np.int8), flat(color), name="glow")
    if inner is not None:
        m2 = np.abs(d - (r - thickness)) <= 0.5
        m2 &= ~m
        cv._commit(m2, np.where(m2, 1, -1).astype(np.int8), flat(inner), name="glow")


def speed_lines(cv: Canvas, x: float, y: float, length: float = 8, count: int = 3,
                spacing: int = 3, direction: int = -1, color=PAPER) -> None:
    """Horizontal motion streaks trailing from (x, y) in ``direction`` (-1 = left)."""
    for i in range(count):
        ln = length * (1.0 - 0.28 * ((i * 2) % 3))
        yy = round(y + (i - (count - 1) / 2) * spacing)
        x0 = round(x)
        x1 = round(x + direction * ln)
        cv.line((x0, yy), (x1, yy), color, name="speed")


def splash(cv: Canvas, x: float, y: float, t: float, size: float = 1.0, mat: Material = WATER_FX) -> None:
    """Water splash at ground point (x, y): a crown of droplets that rises and falls."""
    if t < 0 or t > 1:
        return
    for i, (vx, vy) in enumerate(((-2.2, 4.2), (-1.0, 5.5), (1.2, 5.2), (2.4, 3.8), (0.1, 6.5))):
        tt = t * 1.2
        dx = vx * tt * 2.2 * size
        dy = -(vy * tt - 5.0 * tt * tt) * 2.0 * size
        r = max(0.7, (1.3 - 0.6 * t) * size * (1.0 if i % 2 else 0.8))
        cv.circle(x + dx, y - 1 + dy, r, mat, shade="soft", name="splash")
    if t < 0.6:
        w = (3 + 6 * t) * size
        cv.ellipse(x, y - 1.2, w, 1.2 * size, mat, shade="soft", name="splash")


def impact(cv: Canvas, x: float, y: float, size: float = 3, color=PALE_GOLD, core=GLINT) -> None:
    """Small 4-ray hit spark centred at (x, y)."""
    xi, yi = round(x), round(y)
    s = int(size)
    cv.line((xi - s, yi), (xi + s, yi), color, name="impact")
    cv.line((xi, yi - s), (xi, yi + s), color, name="impact")
    d = max(1, s - 2)
    cv.line((xi - d, yi - d), (xi + d, yi + d), color, name="impact")
    cv.line((xi - d, yi + d), (xi + d, yi - d), color, name="impact")
    cv.pixel(xi, yi, core, name="impact")


# --------------------------------------------------------------------------------------
# Pose tables
# --------------------------------------------------------------------------------------


def poses(defaults: dict, table: dict):
    """Build a ``pose(action, frame)`` lookup from per-frame override dicts.

    ``table[action]`` must be a list with exactly the contract frame count.  Each
    frame dict overrides ``defaults``; the result is a SimpleNamespace (``p.body_y``).
    """
    for a, n in FRAMES.items():
        if a not in table:
            raise ValueError(f"pose table missing action {a!r}")
        if len(table[a]) != n:
            raise ValueError(f"action {a!r} needs {n} frames, got {len(table[a])}")

    def get(action: str, frame: int) -> SimpleNamespace:
        d = dict(defaults)
        d.update(table[action][frame])
        return SimpleNamespace(**d)

    return get


# --------------------------------------------------------------------------------------
# Sheets, checks, manifest
# --------------------------------------------------------------------------------------


def load_creature(cid: str):
    """Import ``tools/art/creatures/<cid>.py`` and return the module."""
    path = CREATURES_DIR / f"{cid}.py"
    for d in (str(TOOLS_DIR), str(CREATURES_DIR)):  # modules import pixel / their base
        if d not in sys.path:
            sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location(f"jr_creature_{cid}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.SPEC["id"] != cid:
        raise ValueError(f"{path}: SPEC id {mod.SPEC['id']!r} != file name")
    return mod


def list_creatures() -> list:
    return sorted(p.stem for p in CREATURES_DIR.glob("*.py") if not p.stem.startswith("_"))


def new_canvas(spec: dict) -> Canvas:
    size = spec["cell"] // SCALE
    return Canvas(size, size, (spec["anchor"][0] // SCALE, spec["anchor"][1] // SCALE))


def render_frames(mod) -> dict:
    """{action: [(rgba_full, rgba_body_only), ...]} at art resolution."""
    out = {}
    for action, n, _fps, _loop in ACTIONS:
        frames = []
        for f in range(n):
            cv = new_canvas(mod.SPEC)
            mod.draw(cv, action, f)
            img = cv.finish()
            frames.append((img, cv.body_image))
        out[action] = frames
    return out


def upscale(img: np.ndarray, k: int = SCALE) -> np.ndarray:
    return np.repeat(np.repeat(img, k, axis=0), k, axis=1)


def assemble_sheet(spec: dict, frames: dict) -> Image.Image:
    cell = spec["cell"]
    sheet = np.zeros((cell * 6, cell * 6, 4), np.uint8)
    for row, (action, n, _fps, _loop) in enumerate(ACTIONS):
        for col in range(n):
            img = upscale(frames[action][col][0])
            sheet[row * cell:(row + 1) * cell, col * cell:(col + 1) * cell] = img
    return Image.fromarray(sheet, "RGBA")


def check_frames(spec: dict, frames: dict) -> list:
    """Contract checks -> list of warning strings (empty list = clean).

    * every frame fits with MARGIN art px on all sides
    * non-flying: lowest body pixel sits on row ``gy - 1`` unless the frame is listed
      in ``SPEC["airborne"]`` (e.g. ``[["attack", 1]]``)
    * no stray pixels (opaque pixel with no opaque 8-neighbour)
    """
    warns = []
    size = spec["cell"] // SCALE
    gy = spec["anchor"][1] // SCALE
    air = {tuple(a) for a in spec.get("airborne", [])}
    for action, n, _fps, _loop in ACTIONS:
        for f in range(n):
            img, body = frames[action][f]
            a = img[..., 3] > 0
            if not a.any():
                warns.append(f"{action}[{f}]: empty frame")
                continue
            ys, xs = np.nonzero(a)
            if xs.min() < MARGIN or ys.min() < MARGIN or xs.max() > size - 1 - MARGIN or ys.max() > size - 1 - MARGIN:
                warns.append(f"{action}[{f}]: outside {MARGIN}px margin (bbox x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()})")
            b = body[..., 3] > 0
            if not spec.get("flying") and (action, f) not in air and b.any():
                low = np.nonzero(b)[0].max()
                if low != gy - 1:
                    warns.append(f"{action}[{f}]: lowest body row {low}, expected {gy - 1} (ground)")
            nb = np.zeros(a.shape, np.int16)
            for dx, dy in N8:
                nb += _shift(a, dx, dy, False)
            stray = a & (nb == 0)
            if stray.any():
                pts = list(zip(*np.nonzero(stray)))[:4]
                warns.append(f"{action}[{f}]: {int(stray.sum())} stray pixel(s) at (y,x) {pts}")
    return warns


def first_frame_bounds(sheet: Image.Image, cell: int) -> dict:
    """Drawn-pixel box of each action row's first frame, relative to its cell: ``{row: [x, y, w, h]}``.
    Pages fit creatures by these boxes, so the game never reads the sheet back from the GPU."""
    out = {}
    for i in range(len(ACTIONS)):
        box = sheet.crop((0, i * cell, cell, (i + 1) * cell)).getbbox()
        if box:
            out[str(i)] = [box[0], box[1], box[2] - box[0], box[3] - box[1]]
    return out


def manifest_entry(spec: dict, sheet: Image.Image | None = None) -> dict:
    entry = {
        "file": f"res://art/creatures/{spec['id']}.png",
        "cell": int(spec["cell"]),
        "anchor": [int(spec["anchor"][0]), int(spec["anchor"][1])],
        "flying": bool(spec.get("flying", False)),
        "hit_frame": int(spec["hit_frame"]),
        "actions": {a: {"row": i, "frames": n, "fps": fps, "loop": loop}
                    for i, (a, n, fps, loop) in enumerate(ACTIONS)},
    }
    if sheet is not None:
        entry["bounds"] = first_frame_bounds(sheet, int(spec["cell"]))
    return entry


def update_manifest(entries: dict, path: Path = MANIFEST_PATH) -> None:
    """Merge ``{id: entry}`` into the manifest JSON (sorted keys, 2-space indent)."""
    path = Path(path)
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    data.update(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def save_png(img: Image.Image, path: Path) -> None:
    """Deterministic PNG: RGBA, no metadata / colour profile."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = img.convert("RGBA")
    img.info.clear()
    img.save(path, format="PNG", optimize=False, compress_level=9)


def validate_spec(spec: dict) -> None:
    for k in ("id", "cell", "anchor", "hit_frame"):
        if k not in spec:
            raise ValueError(f"SPEC missing {k!r}")
    if spec["cell"] not in (128, 192, 256):
        raise ValueError("cell must be 128, 192 or 256")
    if not 0 <= spec["hit_frame"] < FRAMES["attack"]:
        raise ValueError("hit_frame must index an attack frame (0..3)")


def build_creature(mod_or_id, write: bool = True, manifest: bool = True):
    """Render, check and write one creature.  Returns (sheet Image, warnings, frames)."""
    mod = load_creature(mod_or_id) if isinstance(mod_or_id, str) else mod_or_id
    spec = mod.SPEC
    validate_spec(spec)
    frames = render_frames(mod)
    sheet = assemble_sheet(spec, frames)
    warns = check_frames(spec, frames)
    if write:
        save_png(sheet, ART_OUT_DIR / f"{spec['id']}.png")
    if manifest:
        update_manifest({spec["id"]: manifest_entry(spec, sheet)})
    return sheet, warns, frames


# --------------------------------------------------------------------------------------
# Review sheets
# --------------------------------------------------------------------------------------


def _font():
    try:
        return ImageFont.load_default(size=12)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def _composite_on(img: np.ndarray, bg) -> np.ndarray:
    a = img[..., 3:4].astype(np.float32) / 255.0
    base = np.empty(img.shape[:2] + (3,), np.float32)
    base[:] = rgb(bg)
    return (img[..., :3] * a + base * (1 - a)).round().astype(np.uint8)


def contact_sheet(ids, out_path, zoom: int = 4, backgrounds=(BG_DARK, BG_EARTH), frames_cache=None) -> Path:
    """Review sheet: every frame of each creature on each background, labelled.

    ``zoom`` = screen pixels per art pixel (2 = in-game 1x, 4 = 2x zoom).  Cells are
    cropped to the creature's union bounding box (+margin).  A faint line marks the
    ground (anchor row) and a red tick marks the ``hit_frame``.
    """
    font = _font()
    blocks = []
    for cid in ids:
        mod = load_creature(cid)
        spec = mod.SPEC
        frames = (frames_cache or {}).get(cid) or render_frames(mod)
        size = spec["cell"] // SCALE
        gx, gy = spec["anchor"][0] // SCALE, spec["anchor"][1] // SCALE
        union = np.zeros((size, size), bool)
        for action in ACTION_NAMES:
            for img, _ in frames[action]:
                union |= img[..., 3] > 0
        ys, xs = np.nonzero(union)
        x0, x1 = max(0, xs.min() - 3), min(size, xs.max() + 4)
        y0, y1 = max(0, ys.min() - 3), min(size, max(ys.max(), gy) + 4)
        cw, ch = (x1 - x0) * zoom, (y1 - y0) * zoom
        label_w = 70
        pad = 6
        panel_w = label_w + 6 * (cw + pad)
        panel_h = 22 + 6 * (ch + pad)
        W = panel_w
        H = 26 + len(backgrounds) * panel_h
        im = Image.new("RGB", (W, H), (24, 26, 30))
        dr = ImageDraw.Draw(im)
        dr.text((6, 6), f"{cid}  cell {spec['cell']}  anchor {spec['anchor']}  hit_frame {spec['hit_frame']}"
                        f"{'  flying' if spec.get('flying') else ''}", fill=(230, 225, 205), font=font)
        for bi, bg in enumerate(backgrounds):
            oy = 26 + bi * panel_h
            dr.rectangle([0, oy, W, oy + panel_h - 4], fill=rgb(bg))
            dr.text((6, oy + 4), f"bg {hexs(bg)}", fill=(240, 235, 215) if bi == 0 else (20, 20, 20), font=font)
            for row, (action, n, fps, loop) in enumerate(ACTIONS):
                ry = oy + 22 + row * (ch + pad)
                col = (240, 235, 215) if bi == 0 else (25, 22, 18)
                dr.text((6, ry + ch // 2 - 12), action, fill=col, font=font)
                dr.text((6, ry + ch // 2 + 2), f"{n}f {fps}fps", fill=col, font=font)
                for f in range(n):
                    img = frames[action][f][0][y0:y1, x0:x1]
                    comp = _composite_on(img, bg)
                    # ground line
                    gl = gy - y0
                    if 0 <= gl < comp.shape[0] and not spec.get("flying"):
                        line = comp[gl]
                        empty = img[gl, :, 3] == 0
                        tint = np.array(mix(bg, (255, 255, 255) if bi == 0 else (0, 0, 0), 0.18), np.uint8)
                        line[empty] = tint
                    big = np.repeat(np.repeat(comp, zoom, 0), zoom, 1)
                    cx = label_w + f * (cw + pad)
                    im.paste(Image.fromarray(big, "RGB"), (cx, ry))
                    if action == "attack" and f == spec["hit_frame"]:
                        dr.rectangle([cx, ry + ch, cx + cw - 1, ry + ch + 2], fill=WARNING_RED)
        blocks.append(im)
    W = max(b.width for b in blocks)
    H = sum(b.height for b in blocks) + 8 * (len(blocks) - 1)
    sheet = Image.new("RGB", (W, H), (24, 26, 30))
    y = 0
    for b in blocks:
        sheet.paste(b, (0, y))
        y += b.height + 8
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def frame_strip(cid: str, frames, out_path, zoom: int = 8, backgrounds=(BG_DARK, BG_EARTH),
                hollow: bool = False) -> Path:
    """Close-up review: the given ``[(action, frame), ...]`` of one creature side by
    side at ``zoom`` screen px per art px, one row per background, cropped to their
    union bounding box.  Use it to inspect pixel clusters, outlines and eyes."""
    mod = load_creature(cid)
    imgs = []
    for action, f in frames:
        cv = new_canvas(mod.SPEC)
        cv.hollow = hollow
        mod.draw(cv, action, int(f))
        imgs.append(cv.finish())
    u = np.zeros(imgs[0].shape[:2], bool)
    for im in imgs:
        u |= im[..., 3] > 0
    ys, xs = np.nonzero(u)
    gy = mod.SPEC["anchor"][1] // SCALE
    y0, y1 = max(0, ys.min() - 2), min(u.shape[0], max(ys.max(), gy) + 3)
    x0, x1 = max(0, xs.min() - 2), min(u.shape[1], xs.max() + 3)
    rows = []
    for bg in backgrounds:
        row = []
        for im in imgs:
            c = _composite_on(im[y0:y1, x0:x1], bg)
            row.append(np.repeat(np.repeat(c, zoom, 0), zoom, 1))
            row.append(np.full((row[-1].shape[0], 6, 3), 24, np.uint8))
        rows.append(np.concatenate(row[:-1], 1))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.concatenate(rows, 0), "RGB").save(out_path)
    return out_path


def lineup(ids, out_path, zoom: int = 2, reference: np.ndarray | None = None,
           backgrounds=(BG_DARK, BG_EARTH), action="idle", frame=0) -> Path:
    """Scale check: one frame of each creature side by side at ``zoom`` screen px per
    art px, standing on a shared ground line, optionally next to a reference RGBA
    image (e.g. the player, already at art resolution)."""
    items = []
    if reference is not None:
        items.append(("player", reference, reference.shape[0]))
    for cid in ids:
        mod = load_creature(cid)
        cv = new_canvas(mod.SPEC)
        mod.draw(cv, action, frame)
        img = cv.finish()
        items.append((cid, img, mod.SPEC["anchor"][1] // SCALE))
    crops = []
    for name, img, gy in items:
        a = img[..., 3] > 0
        ys, xs = np.nonzero(a)
        crop = img[: gy, max(0, xs.min() - 2): xs.max() + 3]
        crops.append((name, crop))
    Hmax = max(c.shape[0] for _, c in crops)
    Wtot = sum(c.shape[1] + 6 for _, c in crops) + 6
    font = _font()
    panels = []
    for bg in backgrounds:
        canvas = np.zeros((Hmax + 8, Wtot, 4), np.uint8)
        x = 6
        for name, c in crops:
            canvas[Hmax - c.shape[0]: Hmax, x: x + c.shape[1]] = c
            x += c.shape[1] + 6
        comp = _composite_on(canvas, bg)
        comp[Hmax] = mix(bg, (0, 0, 0), 0.35)
        big = np.repeat(np.repeat(comp, zoom, 0), zoom, 1)
        im = Image.fromarray(big, "RGB")
        dr = ImageDraw.Draw(im)
        x = 6
        for name, c in crops:
            dr.text((x * zoom, (Hmax + 1) * zoom), name, fill=(240, 235, 215), font=font)
            x += c.shape[1] + 6
        panels.append(im)
    out = Image.new("RGB", (panels[0].width, sum(p.height for p in panels)))
    y = 0
    for p in panels:
        out.paste(p, (0, y))
        y += p.height
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    return out_path
