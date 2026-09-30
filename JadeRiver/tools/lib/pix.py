"""The pixel-art library for new Jade River art tools (audit 45, DUP-08).

Four drawing libraries grew with the art: tools/art/pixel.py (the side-view creatures), tools/icons/pix.py (the icons),
tools/props/pixlib.py (props, tiles, the UI) and tools/art/fx/fxpix.py (the FX sheets), besides the top-down builders'
tools/art/topdown/canvas.py. Each drew the same lines, ellipses and polygons its own way. This is the one for new
work, taken from the best of them; the old ones stay with the art they made (the frozen side view is not redrawn):

- the masks, the shading modes, the painting and the material-tinted outline of tools/icons/pix.py's Canvas, the most
  complete and the best defined (pixel centres, a ramp per material, light from the upper left);
- the mask operations of tools/props/pixlib.py (moves, wrapping moves for tiles, erosion, edges);
- the coordinate hashes and the tileable noise of tools/art/topdown/canvas.py and creature/motion.py (h01, h01v,
  vnoise) and tools/art/fx/fxpix.py (px_hash).

`python3 tools/lib/pix.py --check` proves each of them draws here exactly as in its source. The builders that shared
a copy of a hash or of the noise now import this one (canvas.py, creature/motion.py, fxpix.py, tools/data/topdown_life.py);
the four libraries themselves are left as they are: their conventions differ (pixlib samples pixel corners and its shift
moves a mask where the icons' reads a neighbour), so moving their art onto this one is a redraw, not a refactor.

Conventions
-----------
- A mask is a numpy bool array [h, w]. A shape samples each pixel at its centre (x + 0.5, y + 0.5): a polygon from
  (2, 2) to (10, 10) covers pixels 2..9. The integer helpers (rect, line, pts) take pixel indices, rect inclusive.
- `move(m, dx, dy)` moves a mask: the pixel at (x, y) lands on (x + dx, y + dy). `look(m, dx, dy)` reads the neighbour
  instead: out[y, x] = m[y + dy, x + dx]. Outside the canvas is empty, or wraps round with `wrap=True` (a tile).
- A colour is '#RRGGBB' or an (r, g, b) tuple of ints. A `Ramp` is a material's colours, dark to light, and the outline
  colour drawn round it. Light comes from the upper left.
- Deterministic: no unseeded randomness (the hashes, or `stable_rng(key)`), no anti-aliasing, no blur and no smooth
  resampling; `image(scale)` enlarges by whole pixels, `save_png` writes the same bytes for the same picture.

Use: put JadeRiver/tools on sys.path and `from lib import pix` (tools/icons has a pix.py of its own).
"""
from __future__ import annotations

import colorsys
import zlib

import numpy as np
from PIL import Image

INK = (7, 16, 21)            # the darkest line: every outline leans toward it
WHITE = (255, 253, 244)


# --------------------------------------------------------------------------- hashes and noise
def h01(x: int, y: int, s: int = 0) -> float:
    """A hash of integer coordinates (and a seed) to [0, 1): the scatter's and the noise's variety."""
    n = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def h01v(x, y, s: int = 0):
    """h01 over arrays of integers (floats floored)."""
    n = (np.asarray(x).astype(np.int64) * 374761393 + np.asarray(y).astype(np.int64) * 668265263 + s * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def px_hash(*args) -> float:
    """A hash of any number of integers to [0, 1)."""
    h = 2166136261
    for a in args:
        h ^= (int(a) * 2654435761) & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= h >> 13
    return ((h * 0x9E3779B1) & 0xFFFFFFFF) / 4294967296.0


def stable_rng(key: str):
    """A numpy generator seeded from a string: the same draws for the same key."""
    return np.random.default_rng(zlib.crc32(key.encode('utf-8')))


def _smooth(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def vnoise(i: float, j: float, seed: int, cx: int = 4, cy: int | None = None, period: int = 16) -> float:
    """Value noise on a lattice of cx x cy px that repeats every `period` px, so a tile built from it tiles."""
    cy = cy or cx
    nx, ny = max(1, period // cx), max(1, period // cy)
    fx, fy = i / cx, j / cy
    x0, y0 = int(fx // 1), int(fy // 1)
    tx, ty = _smooth(fx - x0), _smooth(fy - y0)

    def g(a: int, b: int) -> float:
        return h01(a % nx, b % ny, seed)

    top = g(x0, y0) * (1 - tx) + g(x0 + 1, y0) * tx
    bot = g(x0, y0 + 1) * (1 - tx) + g(x0 + 1, y0 + 1) * tx
    return top * (1 - ty) + bot * ty


# --------------------------------------------------------------------------- colour
def rgb(c):
    """'#RRGGBB', (r, g, b) or a numpy triple as an int tuple."""
    if isinstance(c, str):
        c = c.lstrip('#')
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    return (int(c[0]), int(c[1]), int(c[2]))


def mix(a, b, t):
    """From colour a toward b by t (0..1), rounded."""
    a, b = rgb(a), rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def lum(a):
    """Luminance (0..255) of a colour or an array of colours [..., 3]."""
    a = np.asarray(a, np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def _toward(h, target, amt):
    d = (target - h + 0.5) % 1.0 - 0.5
    if abs(d) <= amt:
        return target % 1.0
    return (h + amt * (1 if d > 0 else -1)) % 1.0


def hsv_shift(c, dh=0.0, ds=0.0, dv=0.0):
    """A colour moved in hue (turns), saturation and value."""
    r, g, b = [v / 255.0 for v in rgb(c)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + dh) % 1.0
    s = min(1.0, max(0.0, s + ds))
    v = min(1.0, max(0.0, v + dv))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def dark_of(c, t=0.86):
    """The hue-tinted dark outline colour for a fill colour."""
    return mix(c, INK, t)


class Ramp:
    """A material: colours dark -> light, and the outline colour drawn round it."""

    def __init__(self, cols, out=None):
        self.c = [rgb(x) for x in cols]
        self.out = rgb(out) if out is not None else mix(self.c[0], INK, 0.55)

    def __len__(self):
        return len(self.c)

    def __getitem__(self, i):
        return self.c[max(0, min(len(self.c) - 1, i))]

    def sub(self, lo, hi):
        return Ramp(self.c[lo:hi + 1], self.out)


def hramp(base, dark=2, light=2, step=0.17, out=None, hue_amt=0.03):
    """A hue-shifted ramp round `base`: the shadows drift to blue-green, the lights to warm gold."""
    r, g, b = [v / 255.0 for v in rgb(base)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    cols = []
    for k in range(-dark, light + 1):
        if k < 0:
            hh = _toward(h, 0.53, hue_amt * -k)
            ss = min(1.0, s + 0.07 * -k)
            vv = v * (1.0 - step * 1.35 * -k)
        elif k > 0:
            hh = _toward(h, 0.14, hue_amt * k)
            ss = max(0.0, s - 0.16 * k)
            vv = min(1.0, v + (1.0 - v) * 0.5 * k + 0.06 * k)
        else:
            hh, ss, vv = h, s, v
        rr, gg, bb = colorsys.hsv_to_rgb(hh, ss, max(0.0, vv))
        cols.append((int(round(rr * 255)), int(round(gg * 255)), int(round(bb * 255))))
    return Ramp(cols, out)


def as_ramp(m):
    """A Ramp as it is, or a one-colour material."""
    if isinstance(m, Ramp):
        return m
    c = rgb(m)
    return Ramp([c], dark_of(c))


# --------------------------------------------------------------------------- mask operations
def look(m, dx, dy, wrap=False):
    """Each pixel's neighbour at (dx, dy): out[y, x] = m[y + dy, x + dx] (empty past the edge, or wrapped)."""
    if wrap:
        return np.roll(np.roll(m, -dy, 0), -dx, 1)
    h, w = m.shape[:2]
    out = np.zeros_like(m)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    if ys0 < ys1 and xs0 < xs1:
        out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def move(m, dx, dy, wrap=False):
    """The mask moved by (dx, dy)."""
    return look(m, -dx, -dy, wrap)


def dilate(m, diag=False, wrap=False):
    """Grown by a pixel: the four sides, and with `diag` the corners too."""
    o = m | look(m, 1, 0, wrap) | look(m, -1, 0, wrap) | look(m, 0, 1, wrap) | look(m, 0, -1, wrap)
    if diag:
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            o |= look(m, dx, dy, wrap)
    return o


def erode(m, diag=False, wrap=False):
    """Shrunk by a pixel (a pixel stays when its four, or eight, neighbours are in)."""
    o = m & look(m, 1, 0, wrap) & look(m, -1, 0, wrap) & look(m, 0, 1, wrap) & look(m, 0, -1, wrap)
    if diag:
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            o &= look(m, dx, dy, wrap)
    return o


def border(m, wrap=False):
    """The mask's own edge pixels (inside it)."""
    return m & ~erode(m, wrap=wrap)


def edge(m, side):
    """The mask's pixels on one side: 'top', 'bottom', 'left' or 'right' (nothing of the mask beyond them)."""
    dx, dy = {"top": (0, -1), "bottom": (0, 1), "left": (-1, 0), "right": (1, 0)}[side]
    return m & ~look(m, dx, dy)


def bbox(m):
    """(x0, y0, x1, y1) of the mask, inclusive; None when it is empty."""
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def edge_dist(mask, dx, dy, maxd=40):
    """In-mask steps from each pixel in direction (dx, dy) before it leaves the mask."""
    d = np.zeros(mask.shape, int)
    alive = mask.copy()
    for k in range(1, maxd + 1):
        alive &= look(mask, dx * k, dy * k)
        if not alive.any():
            break
        d += alive
    return d


def light_dists(mask):
    """(a, b): each pixel's distance to the lit (upper, left) edge and to the shadow edge."""
    a = np.minimum(edge_dist(mask, 0, -1), edge_dist(mask, -1, 0))
    b = np.minimum(edge_dist(mask, 0, 1), edge_dist(mask, 1, 0))
    return a, b


def despeckle(idx, mask):
    """Lone pixels whose in-mask neighbours (three or four) all share another level take it."""
    out = idx.copy()
    h, w = idx.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x]:
                continue
            nbs = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and mask[Y, X]:
                    nbs.append(idx[Y, X])
            if len(nbs) >= 3 and all(v == nbs[0] for v in nbs) and nbs[0] != idx[y, x]:
                out[y, x] = nbs[0]
    return out


# --------------------------------------------------------------------------- shapes
class Grid:
    """The shapes of a w x h canvas as masks, sampled at pixel centres."""

    def __init__(self, w=32, h=None):
        h = w if h is None else h
        self.w, self.h = w, h
        yy, xx = np.mgrid[0:h, 0:w]
        self.X = xx.astype(float) + 0.5
        self.Y = yy.astype(float) + 0.5
        self.xi, self.yi = xx, yy

    def empty(self):
        return np.zeros((self.h, self.w), bool)

    def ellipse(self, cx, cy, rx, ry=None):
        ry = rx if ry is None else ry
        return ((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2 <= 1.0

    def circle(self, cx, cy, r):
        return self.ellipse(cx, cy, r, r)

    def ring(self, cx, cy, r, w=1.0, ry=None):
        ry = r if ry is None else ry
        outer = self.ellipse(cx, cy, r, ry)
        inner = self.ellipse(cx, cy, max(0.01, r - w), max(0.01, ry - w))
        return outer & ~inner

    def rect(self, x0, y0, x1, y1):
        """Pixels x0..x1, y0..y1 (inclusive)."""
        return (self.xi >= x0) & (self.xi <= x1) & (self.yi >= y0) & (self.yi <= y1)

    def box(self, x0, y0, x1, y1):
        """The continuous rectangle [x0, x1) x [y0, y1) (fractions allowed)."""
        return (self.X >= x0) & (self.X < x1) & (self.Y >= y0) & (self.Y < y1)

    def rrect(self, x0, y0, x1, y1, r=2.0):
        """A continuous rectangle with round corners of radius r."""
        m = self.box(x0 + r, y0, x1 - r, y1) | self.box(x0, y0 + r, x1, y1 - r)
        for (x, y) in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
            m |= self.circle(x, y, r)
        return m

    def diamond(self, cx, cy, rx, ry=None):
        ry = rx if ry is None else ry
        return (abs(self.X - cx) / rx + abs(self.Y - cy) / ry) <= 1.0

    def poly(self, pts):
        """A polygon (even-odd rule)."""
        X, Y = self.X, self.Y
        inside = np.zeros((self.h, self.w), bool)
        n = len(pts)
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if yi != yj:
                cond = ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / (yj - yi) + xi)
                inside ^= cond
            j = i
        return inside

    def seg(self, x0, y0, x1, y1, w=1.0):
        """A thick segment with round ends: every pixel whose centre is within w/2 of it."""
        X, Y = self.X, self.Y
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        if L2 == 0:
            t = np.zeros_like(X)
        else:
            t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L2, 0.0, 1.0)
        px, py = x0 + t * dx, y0 + t * dy
        return (X - px) ** 2 + (Y - py) ** 2 <= (w / 2.0) ** 2

    def polyline(self, pts, w=1.0):
        m = self.empty()
        for (a, b) in zip(pts, pts[1:]):
            m |= self.seg(a[0], a[1], b[0], b[1], w)
        return m

    def line(self, x0, y0, x1, y1):
        """A 1-pixel line between integer pixels (Bresenham)."""
        m = self.empty()
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if 0 <= x0 < self.w and 0 <= y0 < self.h:
                m[y0, x0] = True
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return m

    def path(self, pts):
        """1-pixel lines through integer points."""
        m = self.empty()
        for a, b in zip(pts, pts[1:]):
            m |= self.line(a[0], a[1], b[0], b[1])
        return m

    def _angle(self, cx, cy, a0, a1):
        ang = np.degrees(np.arctan2(-(self.Y - cy), self.X - cx)) % 360.0
        a0 %= 360.0
        a1 %= 360.0
        return ((ang >= a0) & (ang <= a1)) if a0 <= a1 else ((ang >= a0) | (ang <= a1))

    def arc(self, cx, cy, r, w, a0, a1, ry=None):
        """A ring's sector; angles in degrees, 0 = right, 90 = up the screen."""
        return self.ring(cx, cy, r, w, ry) & self._angle(cx, cy, a0, a1)

    def sector(self, cx, cy, r, a0, a1, ry=None):
        return self.ellipse(cx, cy, r, ry) & self._angle(cx, cy, a0, a1)

    def diag(self, u0, u1, v0, v1):
        """A band in 45-degree space: u = x - y (along, up-right), v = x + y (across)."""
        u = self.xi - self.yi
        v = self.xi + self.yi
        return (u >= u0) & (u <= u1) & (v >= v0) & (v <= v1)

    def pts(self, pts):
        m = self.empty()
        for x, y in pts:
            if 0 <= x < self.w and 0 <= y < self.h:
                m[int(y), int(x)] = True
        return m

    def from_rows(self, rows, ox=0, oy=0, chars=None):
        """A mask from ASCII rows: any character but ' ' and '.' (or any of `chars`) is in."""
        m = self.empty()
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                on = (ch in chars) if chars else (ch not in ' .')
                x, y = ox + i, oy + j
                if on and 0 <= x < self.w and 0 <= y < self.h:
                    m[y, x] = True
        return m


# --------------------------------------------------------------------------- the canvas
class Canvas(Grid):
    """A picture at art resolution: its colours, which pixels are drawn, their alpha, and for each drawn pixel the
    outline colour its material asks for (the final outline takes it: dark teal round jade, brown round wood)."""

    def __init__(self, w=32, h=None):
        super().__init__(w, h)
        self.rgb = np.zeros((self.h, self.w, 3), np.uint8)
        self.a = np.zeros((self.h, self.w), bool)          # drawn pixels
        self.alpha = np.zeros((self.h, self.w), np.uint8)  # their alpha (a glow's bands under 255)
        self.oc = np.zeros((self.h, self.w, 3), np.uint8)  # the outline colour each asks for

    def shade_index(self, mask, n, mode='ray', base=None, **kw):
        """Each pixel's level of an n-colour ramp. Modes: 'flat'; 'ray' (bands by the distance to the lit and the
        shadow edge); 'bevel' (a lit and a dark rim, `hw` and `sw` wide); 'sphere' (a ball lit from `light`);
        'vgrad', 'hgrad', 'dgrad' (down, across, along the diagonal); 'across' (bands across a 45-degree strip).
        `bands` changes a mode's thresholds; lone pixels are smoothed away unless `despeckle=False`."""
        if base is None:
            base = n // 2
        idx = np.full((self.h, self.w), base, int)
        if mode == 'flat' or n == 1:
            return np.clip(idx, 0, n - 1)
        if mode in ('ray', 'bevel'):
            a, b = light_dists(mask)
            if mode == 'bevel':
                hw, sw = kw.get('hw', 1), kw.get('sw', 1)
                lit = a < hw
                dk = b < sw
                idx = np.where(lit & ~dk, base + 1, idx)
                idx = np.where(dk & ~lit, base - 1, idx)
                if kw.get('corner', False):
                    up, left = edge_dist(mask, 0, -1), edge_dist(mask, -1, 0)
                    idx = np.where((up == 0) & (left == 0), base + 2, idx)
            else:
                t = (a + 0.5) / (a + b + 1.0)
                bands = kw.get('bands', ((0.22, 1), (0.64, 0), (0.86, -1), (9, -2)))
                out = np.full((self.h, self.w), base - 2, int)
                for thr, off in reversed(bands):
                    out = np.where(t < thr, base + off, out)
                idx = out
        elif mode == 'sphere':
            ys, xs = np.nonzero(mask)
            if len(xs) == 0:
                return idx
            cx = kw.get('cx', (xs.min() + xs.max() + 1) / 2.0)
            cy = kw.get('cy', (ys.min() + ys.max() + 1) / 2.0)
            rx = kw.get('rx', (xs.max() - xs.min() + 1) / 2.0)
            ry = kw.get('ry', (ys.max() - ys.min() + 1) / 2.0)
            nx = (self.X - cx) / rx
            ny = (self.Y - cy) / ry
            nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
            L = np.array(kw.get('light', (-0.55, -0.65, 0.52)))
            L = L / np.linalg.norm(L)
            I = nx * L[0] + ny * L[1] + nz * L[2]
            bands = kw.get('bands', ((0.93, 2), (0.66, 1), (0.25, 0), (-0.2, -1), (-9, -2)))
            out = np.full((self.h, self.w), base - 2, int)
            for thr, off in reversed(bands):
                out = np.where(I >= thr, base + off, out)
            idx = out
        elif mode in ('vgrad', 'hgrad', 'dgrad'):
            ys, xs = np.nonzero(mask)
            if len(xs) == 0:
                return idx
            if mode == 'vgrad':
                t = (self.yi - ys.min() + 0.5) / (ys.max() - ys.min() + 1.0)
            elif mode == 'hgrad':
                t = (self.xi - xs.min() + 0.5) / (xs.max() - xs.min() + 1.0)
            else:
                s = xs + ys
                t = (self.xi + self.yi - s.min() + 0.5) / (s.max() - s.min() + 1.0)
            bands = kw.get('bands', ((0.25, 1), (0.7, 0), (9, -1)))
            out = np.full((self.h, self.w), base - 1, int)
            for thr, off in reversed(bands):
                out = np.where(t < thr, base + off, out)
            idx = out
        elif mode == 'across':
            v = self.xi + self.yi
            u = self.xi - self.yi
            idx = np.full((self.h, self.w), base, int)
            vmin = {}
            vmax = {}
            for uu in np.unique(u[mask]):
                sel = mask & (u == uu)
                vmin[uu] = v[sel].min()
                vmax[uu] = v[sel].max()
            bands = kw.get('bands', ((0.34, 1), (0.67, 0), (9, -1)))
            for (y, x) in zip(*np.nonzero(mask)):
                lo, hi = vmin[u[y, x]], vmax[u[y, x]]
                if hi - lo <= 0:
                    continue
                t = (v[y, x] - lo) / float(hi - lo)
                for thr, off in bands:
                    if t < thr:
                        idx[y, x] = base + off
                        break
        if kw.get('despeckle', True):
            idx = despeckle(idx, mask)
        return np.clip(idx, 0, n - 1)

    def put(self, mask, mat, mode='ray', base=None, sep=False, sep_col=None, only_on=False, clip=None, out=None, **kw):
        """Paint `mask` with material `mat` (a Ramp or a colour), shaded by `mode` (shade_index).
        sep: a 1-pixel dark line round the new part where it lies over what is drawn (a part's separation).
        only_on: only over what is drawn already (a decal, an engraving). clip: only inside this mask.
        out: the outline colour to ask for (the material's own by default)."""
        mat = as_ramp(mat)
        mask = mask.copy()
        if clip is not None:
            mask &= clip
        if only_on:
            mask &= self.a
        if not mask.any():
            return mask
        n = len(mat)
        if base is None:
            base = 2 if n >= 5 else (n - 1) // 2
            if n == 4:
                base = 2
        idx = self.shade_index(mask, n, mode, base, **kw)
        if sep:
            ring = dilate(mask) & ~mask & self.a
            sc = rgb(sep_col) if sep_col is not None else mat.out
            self.rgb[ring] = sc
            self.oc[ring] = sc
        cols = np.array(mat.c, np.uint8)
        self.rgb[mask] = cols[idx[mask]]
        self.a |= mask
        self.alpha[mask] = 255
        self.oc[mask] = rgb(out) if out is not None else mat.out
        return mask

    def fill(self, mask, col, out=None, only_on=False, clip=None):
        return self.put(mask, as_ramp(col), 'flat', base=0, out=out, only_on=only_on, clip=clip)

    def px(self, x, y, col, out=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rgb[y, x] = rgb(col)
            self.a[y, x] = True
            self.alpha[y, x] = 255
            self.oc[y, x] = rgb(out) if out is not None else dark_of(col)

    def recolor(self, mask, col):
        """Recolour pixels already drawn (their outline colour kept)."""
        self.rgb[mask & self.a] = rgb(col)

    def erase(self, mask):
        self.a &= ~mask
        self.alpha[mask] = 0
        self.rgb[mask] = 0

    def inline(self, mask, col=None):
        """Darken the inner edge of a part already drawn (an edge line)."""
        self.recolor(mask & ~erode(mask), col if col is not None else INK)

    def stamp(self, rows, cmap, ox=0, oy=0):
        """Paint ASCII art: cmap maps a character to a colour, (Ramp, level), or None (erase)."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch not in cmap:
                    continue
                spec = cmap[ch]
                x, y = ox + i, oy + j
                if not (0 <= x < self.w and 0 <= y < self.h):
                    continue
                if spec is None:
                    self.erase(self.rect(x, y, x, y))
                    continue
                if isinstance(spec, tuple) and len(spec) == 2 and isinstance(spec[0], Ramp):
                    col, oc = spec[0][spec[1]], spec[0].out
                else:
                    col, oc = rgb(spec), dark_of(spec)
                self.px(x, y, col, oc)

    def paste(self, other, dx=0, dy=0):
        """Another canvas's drawn pixels over this one's, moved by (dx, dy)."""
        ys, xs = np.nonzero(other.a)
        for y, x in zip(ys, xs):
            X, Y = x + dx, y + dy
            if 0 <= X < self.w and 0 <= Y < self.h:
                self.rgb[Y, X] = other.rgb[y, x]
                self.oc[Y, X] = other.oc[y, x]
                self.a[Y, X] = True
                self.alpha[Y, X] = 255

    def flipped(self):
        c = Canvas(self.w, self.h)
        c.rgb = self.rgb[:, ::-1].copy()
        c.a = self.a[:, ::-1].copy()
        c.alpha = self.alpha[:, ::-1].copy()
        c.oc = self.oc[:, ::-1].copy()
        return c

    def outline(self, col=None, diag=False, mask=None):
        """The 1-pixel outline round every drawn pixel, each in the darkest outline colour its neighbours ask for
        (or `col`); `diag` closes the corners, `mask` limits where it may go. Returns the outline's pixels."""
        a = self.a
        if not hasattr(self, 'body'):
            self.body = a.copy()  # the silhouette before its first outline (a clip check)
        target = ~a if mask is None else (~a & mask)
        new_rgb = self.rgb.copy()
        new_a = a.copy()
        best = np.full((self.h, self.w), 10 ** 9)
        offs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        if diag:
            offs += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for dx, dy in offs:
            nb = look(a, dx, dy)
            noc = look(self.oc, dx, dy)
            dark = noc.astype(int).sum(axis=2)
            sel = target & nb & (dark < best)
            new_rgb[sel] = noc[sel] if col is None else rgb(col)
            best = np.where(sel, dark, best)
            new_a |= sel
        ring = new_a & ~a
        self.rgb = new_rgb
        self.a = new_a
        self.alpha[ring] = 255
        self.oc[ring] = self.rgb[ring]
        return ring

    def glow(self, col, alphas=(150, 70), diag=True):
        """Stepped glow bands round the drawn silhouette, one a pixel wide per alpha (no blur)."""
        cur = self.alpha > 0
        for al in alphas:
            ring = dilate(cur, diag=diag) & ~cur
            self.rgb[ring] = rgb(col)
            self.alpha[ring] = al
            cur |= ring

    def rgba(self):
        """The picture as an RGBA array (undrawn pixels all zero)."""
        arr = np.zeros((self.h, self.w, 4), np.uint8)
        arr[..., :3] = self.rgb
        arr[..., 3] = self.alpha
        arr[self.alpha == 0] = 0
        return arr

    def image(self, scale=2):
        """The picture as a PIL image, enlarged by whole pixels (2: the game's native pixel scale)."""
        return Image.fromarray(upscale(self.rgba(), scale), 'RGBA')


# --------------------------------------------------------------------------- output
def upscale(arr, k=2):
    """An image array enlarged k times, nearest neighbour."""
    return arr if k == 1 else arr.repeat(k, axis=0).repeat(k, axis=1)


def save_png(img, path):
    """A PNG with the same bytes for the same picture (no optimiser, fixed compression)."""
    import os
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path, format='PNG', optimize=False, compress_level=9)


# --------------------------------------------------------------------------- the check
def _load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check():
    """Everything taken from another library draws here exactly as there (the old libraries keep their art)."""
    import os
    import sys
    tools = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    errs = []

    def same(what, a, b):
        if not (np.array_equal(np.asarray(a), np.asarray(b)) and np.asarray(a).dtype == np.asarray(b).dtype):
            errs.append(what)

    # tools/icons/pix.py: the shapes, the ramps, the shading modes, the painting and the outline.
    icons = _load("_icons_pix", os.path.join(tools, "icons", "pix.py"))
    g, ic = Canvas(40, 36), icons.Canvas(40, 36)
    shapes = [("ellipse", (17.3, 15.1, 9.2, 6.4)), ("ellipse", (20, 18, 7, 7)), ("circle", (20, 20, 7.5)),
              ("ring", (18, 17, 12, 2.5, 9)),
              ("rect", (3, 4, 30, 12)), ("poly", ([(2, 2), (30.5, 6), (22, 33), (5.2, 25)],)),
              ("seg", (3, 30, 35.5, 4.2, 3.4)), ("polyline", ([(2, 3), (15, 30), (37, 10)], 2.2)),
              ("arc", (20, 18, 14, 3, 300, 70)), ("sector", (20, 18, 11, 20, 160, 8)), ("diag", (-6, 9, 12, 40)),
              ("pts", ([(1, 1), (39, 35), (40, 2), (-1, 3)],)), ("from_rows", (["..#x.", " ## ", "x..x"], 3, 5))]
    for name, args in shapes:
        same("icons " + name, getattr(g, name)(*args), getattr(ic, name)(*args))
    sq, sc = Grid(40, 40), icons.SCanvas(40, 1.0)   # the HD canvas's continuous shapes, at its scale 1
    for name, args in (("box", (2.5, 3, 30.2, 11.5)), ("rrect", (4, 5, 33, 30, 4.5)), ("diamond", (19, 17, 11, 8))):
        same("icons SCanvas " + name, getattr(sq, name)(*args), getattr(sc, name)(*args))
    same("icons bres", g.line(1, 2, 37, 30), ic.bres(1, 2, 37, 30))
    same("icons bres_path", g.path([(0, 0), (20, 30), (39, 1)]), ic.bres_path([(0, 0), (20, 30), (39, 1)]))
    for base in ("#4f9a7c", (150, 90, 60), "#c8a040"):
        a, b = hramp(base, 3, 2, 0.15, hue_amt=0.04), icons.hramp(base, 3, 2, 0.15, hue_amt=0.04)
        if a.c != b.c or a.out != b.out:
            errs.append("icons hramp %s" % str(base))
        if hsv_shift(base, 0.1, -0.2, 0.05) != icons.hsv_shift(base, 0.1, -0.2, 0.05):
            errs.append("icons hsv_shift")
    ball, slab, strip = g.ellipse(14, 13, 9, 8), g.poly([(20, 6), (37, 9), (35, 30), (18, 26)]), g.diag(-4, 4, 10, 60)
    for lib, cv in ((sys.modules[__name__], g), (icons, ic)):
        jade, wood = lib.hramp("#4f9a7c"), lib.hramp((150, 90, 60), 2, 2)
        cv.put(slab, wood, 'ray')
        cv.put(ball, jade, 'sphere', sep=True)
        cv.put(strip, wood, 'across', only_on=True)
        cv.put(g.rect(2, 28, 12, 34), jade, 'bevel', corner=True)
        cv.put(g.rect(26, 28, 38, 34), jade, 'vgrad')
        cv.fill(g.circle(30, 20, 2.2), "#f0e8c0")
        cv.stamp(["ab", "b."], {"a": "#ff0000", "b": (jade, 1)}, 1, 1)
        cv.outline(diag=True)
        cv.glow("#80ffd0")
    same("icons painting (rgb)", g.rgb, ic.rgb)
    same("icons painting (alpha)", g.alpha, ic.alpha)
    same("icons painting (image)", np.asarray(g.image(2)), np.asarray(ic.image(2)))
    same("icons rng", stable_rng("jade").random(4), icons.stable_rng("jade").random(4))
    # tools/props/pixlib.py: the moves (pixlib's shift moves a mask) and the erosion and edges built on them.
    sys.path.insert(0, os.path.join(tools, "props"))
    try:
        pl = _load("_pixlib", os.path.join(tools, "props", "pixlib.py"))
    finally:
        sys.path.pop(0)
    m = g.poly([(3, 2), (33, 8), (28, 34), (6, 22)]) | g.circle(35, 30, 3)
    for dx, dy in ((3, -2), (-5, 4), (0, 0), (41, 0)):
        same("pixlib shift %d,%d" % (dx, dy), move(m, dx, dy), pl.shift(m, dx, dy))
        same("pixlib wshift %d,%d" % (dx, dy), move(m, dx, dy, wrap=True), pl.wshift(m, dx, dy))
    for wrap in (False, True):
        same("pixlib erode", erode(m, wrap=wrap), pl.erode(m, wrap))
        same("pixlib dilate", dilate(m, wrap=wrap), pl.dilate(m, wrap))
        same("pixlib dilate diag", dilate(m, diag=True, wrap=wrap), pl.dilate(m, wrap, diag=True))
        same("pixlib border", border(m, wrap), pl.border(m, wrap))
    for side in ("top", "bottom", "left", "right"):
        same("pixlib " + side + "_edge", edge(m, side), getattr(pl, side + "_edge")(m))
    if bbox(m) != tuple(int(v) for v in pl.bbox(m)):
        errs.append("pixlib bbox")
    # tools/art/topdown (canvas.py, creature/motion.py) and tools/art/fx/fxpix.py: the hashes and the noise.
    sys.path.insert(0, os.path.join(tools, "art", "topdown"))
    try:
        cvs = _load("_td_canvas", os.path.join(tools, "art", "topdown", "canvas.py"))
    finally:
        sys.path.pop(0)
    motion = _load("_td_motion", os.path.join(tools, "art", "topdown", "creature", "motion.py"))
    fx = _load("_fxpix", os.path.join(tools, "art", "fx", "fxpix.py"))
    for x, y, s in ((0, 0, 0), (13, -7, 3), (-400, 91, 17), (2 ** 20, 5, 99)):
        if h01(x, y, s) != cvs.h01(x, y, s) or h01(x, y, s) != motion.h01(x, y, s):
            errs.append("h01 %s" % str((x, y, s)))
        if px_hash(x, y, s) != fx.px_hash(x, y, s):
            errs.append("px_hash %s" % str((x, y, s)))
    xs, ys = np.mgrid[-9:30, -4:21]
    same("h01v", h01v(xs, ys, 7), motion.h01v(xs, ys, 7))
    for i, j in ((0, 0), (3.5, 17.25), (31, 2), (-5, 40)):
        for args in ((11,), (4, 4, None, 16), (5, 3, 6, 30)):
            if vnoise(i, j, *args) != cvs.vnoise(i, j, *args):
                errs.append("vnoise %s %s" % (str((i, j)), str(args)))
    return errs


if __name__ == "__main__":
    import sys
    if "--check" not in sys.argv[1:]:
        raise SystemExit(__doc__.split("\n\n")[0] + "\n\nUsage: python3 tools/lib/pix.py --check")
    problems = check()
    if problems:
        raise SystemExit("pix: draws otherwise than its sources: " + ", ".join(problems))
    print("pix: every shape, ramp, shading mode, outline, move, hash and noise draws as in its source")
