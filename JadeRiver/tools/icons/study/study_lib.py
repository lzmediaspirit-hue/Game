"""Icon style study: one parametric icon description, two renderers.

Every study icon is a function `draw(p, ...)` that paints with a `Painter` in
64-px *icon space* (HUD glyphs in 32-px space). The painter owns a canvas
scaled by `s`, so the same description renders as:

- Style A, "HD pixel": `PixelPainter(64)` draws 64 hard-edged art px with
  7-step ramps, banded shading, pixel textures, a rim light and a selective
  outline (dark local tone inside, near-ink on the outer silhouette).
  `PixelPainter(64, s=0.75)` renders the same description at 48 art px.
- Style B, "painted icon": `PaintedPainter(64)` draws at 4x (256 px) with
  smooth normals, specular, ambient occlusion between parts, a soft contour,
  a soft grade glow, and box-downsamples to 64 so the edges are anti-aliased
  but still crisp at 1x.

Everything is deterministic: numpy only, no randomness, no timestamps.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.normpath(os.path.join(HERE, '..'))
if ICONS not in sys.path:
    sys.path.insert(0, ICONS)

from pix import Canvas, Ramp, rgb, mix, INK, shift, dilate4, dilate8, erode4  # noqa: E402
from palette import R  # noqa: E402
import shapes as S  # noqa: E402,F401

WHITE = (255, 253, 244)
RIM_COOL = (175, 201, 209)      # mist blue: the rim light on the shadow edge
LIGHT = np.array((-0.55, -0.65, 0.52))
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = LIGHT + np.array((0.0, 0.0, 1.0))
HALF = HALF / np.linalg.norm(HALF)
I_FLAT = float(LIGHT[2])


# ----------------------------------------------------------------------------- materials
KINDS = {
    # spec strength, shininess, rim-light strength
    'matte': (0.10, 8, 0.25), 'metal': (0.85, 26, 0.60), 'gold': (0.90, 22, 0.55), 'glass': (0.70, 40, 0.70),
    'jade': (0.55, 30, 0.60), 'wood': (0.12, 8, 0.25), 'cloth': (0.05, 6, 0.20), 'clay': (0.18, 10, 0.30),
    'paper': (0.05, 6, 0.15), 'porcelain': (0.65, 30, 0.45), 'gem': (0.95, 44, 0.60), 'leather': (0.22, 10, 0.30),
    'ink': (0.35, 20, 0.20), 'light': (0.0, 1, 0.0), 'silk': (0.35, 12, 0.35),
}


class Mat:
    """Seven colours dark -> light (index 3 = base), an outline tone and a surface kind."""

    def __init__(self, cols, out=None, kind='matte'):
        self.c = [rgb(x) for x in cols]
        assert len(self.c) == 7
        self.out = rgb(out) if out is not None else mix(self.c[1], INK, 0.55)
        self.kind = kind
        self.spec, self.shine, self.rim = KINDS[kind]

    def __getitem__(self, i):
        return self.c[max(0, min(6, i))]

    def __len__(self):
        return 7

    def ramp5(self):
        return Ramp(self.c[1:6], self.out)


def mat7(ramp5, kind='matte', out=None):
    """Extend a palette 5-step ramp to 7: a deeper shadow below, a specular above."""
    c = ramp5.c if isinstance(ramp5, Ramp) else [rgb(x) for x in ramp5]
    o = out if out is not None else (ramp5.out if isinstance(ramp5, Ramp) else None)
    dark = mix(c[0], INK, 0.42)
    light = mix(c[4], WHITE, 0.55)
    return Mat([dark] + list(c) + [light], o, kind)


def M(name, kind='matte'):
    return mat7(R[name], kind)


def solid(col, kind='matte'):
    """A 7-ramp built round one colour (for decals and small parts)."""
    from pix import hramp
    return mat7(hramp(col, 2, 2, 0.15), kind)


# ----------------------------------------------------------------------------- scaled canvas
class SCanvas(Canvas):
    """A pix.Canvas whose continuous mask builders take icon-space coordinates and scale by `s`."""

    def __init__(self, n, s=1.0):
        super().__init__(int(n))
        self.s = float(s)

    def ellipse(self, cx, cy, rx, ry=None):
        s = self.s
        ry = rx if ry is None else ry
        return Canvas.ellipse(self, cx * s, cy * s, max(0.01, rx * s), max(0.01, ry * s))

    def circle(self, cx, cy, r):
        return self.ellipse(cx, cy, r, r)

    def ring(self, cx, cy, r, w=1.0, ry=None):
        ry = r if ry is None else ry
        return self.ellipse(cx, cy, r, ry) & ~self.ellipse(cx, cy, max(0.01, r - w), max(0.01, ry - w))

    def box(self, x0, y0, x1, y1):
        """Continuous rectangle [x0, x1) x [y0, y1) in icon space."""
        s = self.s
        return (self.X >= x0 * s) & (self.X < x1 * s) & (self.Y >= y0 * s) & (self.Y < y1 * s)

    def rect(self, x0, y0, x1, y1):
        """Inclusive integer rectangle in icon space (pixels x0..x1)."""
        return self.box(x0, y0, x1 + 1, y1 + 1)

    def poly(self, pts):
        s = self.s
        return Canvas.poly(self, [(x * s, y * s) for x, y in pts])

    def seg(self, x0, y0, x1, y1, w=1.0):
        s = self.s
        return Canvas.seg(self, x0 * s, y0 * s, x1 * s, y1 * s, max(1.0, w * s))

    def polyline(self, pts, w=1.0):
        m = self.empty()
        for a, b in zip(pts, pts[1:]):
            m |= self.seg(a[0], a[1], b[0], b[1], w)
        return m

    def _angsel(self, cx, cy, a0, a1):
        s = self.s
        ang = np.degrees(np.arctan2(-(self.Y - cy * s), self.X - cx * s)) % 360.0
        a0 %= 360.0
        a1 %= 360.0
        if a0 <= a1:
            return (ang >= a0) & (ang <= a1)
        return (ang >= a0) | (ang <= a1)

    def arc(self, cx, cy, r, w, a0, a1, ry=None):
        """Ring sector in icon space; angles in degrees, 0 = right, 90 = up (screen)."""
        return self.ring(cx, cy, r, w, ry) & self._angsel(cx, cy, a0, a1)

    def sector(self, cx, cy, r, a0, a1, ry=None):
        return self.ellipse(cx, cy, r, ry) & self._angsel(cx, cy, a0, a1)

    def bres(self, x0, y0, x1, y1):
        if self.s == 1.0:
            return Canvas.bres(self, x0, y0, x1, y1)
        return self.seg(x0 + 0.5, y0 + 0.5, x1 + 0.5, y1 + 0.5, 1.0)

    def bres_path(self, pts):
        m = self.empty()
        for a, b in zip(pts, pts[1:]):
            m |= self.bres(a[0], a[1], b[0], b[1])
        return m

    def pts(self, pts):
        m = self.empty()
        for x, y in pts:
            m |= self.box(x, y, x + 1, y + 1)
        return m

    def from_rows(self, rows, ox=0, oy=0, chars=None):
        m = self.empty()
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                on = (ch in chars) if chars else (ch not in ' .')
                if on:
                    m |= self.box(ox + i, oy + j, ox + i + 1, oy + j + 1)
        return m

    # icon-space helpers ------------------------------------------------------------
    def leaf(self, bx, by, angle, length, width, bend=0.0, **kw):
        return self.poly(S.lens_pts(bx, by, angle, length, width, bend, **kw))

    def diamond(self, cx, cy, rx, ry=None):
        s = self.s
        ry = rx if ry is None else ry
        return (abs(self.X - cx * s) / (rx * s) + abs(self.Y - cy * s) / (ry * s)) <= 1.0

    def rrect(self, x0, y0, x1, y1, r=2.0):
        """Rounded continuous rectangle."""
        m = self.box(x0 + r, y0, x1 - r, y1) | self.box(x0, y0 + r, x1, y1 - r)
        for (x, y) in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
            m |= self.circle(x, y, r)
        return m

    def bez(self, p0, p1, p2, w=1.0, k=24):
        return self.polyline(S.curve_pts(p0, p1, p2, k), w)

    def taper(self, p0, p1, p2, w0, w1, k=24):
        pts = S.curve_pts(p0, p1, p2, k)
        m = self.empty()
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            t = i / float(len(pts) - 1)
            m |= self.seg(a[0], a[1], b[0], b[1], w0 + (w1 - w0) * t)
        return m

    def flame(self, cx, by, w, h, lean=0.0):
        pts = [(cx - w / 2.0, by - h * 0.28), (cx - w * 0.42 + lean * 0.3, by - h * 0.62), (cx - w * 0.18, by - h * 0.46),
               (cx + lean, by - h), (cx + w * 0.2, by - h * 0.52), (cx + w * 0.42 + lean * 0.3, by - h * 0.72),
               (cx + w / 2.0, by - h * 0.3)]
        body = self.ellipse(cx, by - h * 0.28, w / 2.0, h * 0.3)
        return body | self.poly(pts + [(cx + w * 0.3, by - h * 0.1), (cx - w * 0.3, by - h * 0.1)])

    def drop(self, cx, cy, r, h=None):
        h = r * 1.9 if h is None else h
        return self.circle(cx, cy, r) | self.poly([(cx - r * 0.93, cy - r * 0.35), (cx, cy - h), (cx + r * 0.93, cy - r * 0.35)])

    def field_along(self, p0, p1):
        """Per-pixel (t, w): distance along the axis p0->p1 (icon units) and signed offset across it."""
        s = self.s
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        X, Y = self.X / s - p0[0], self.Y / s - p0[1]
        t = X * ux + Y * uy
        w = -X * uy + Y * ux   # positive to the right of the direction (screen)
        return t, w


# ----------------------------------------------------------------------------- numpy helpers
def erode8(m):
    out = m.copy()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        out &= shift(m, dx, dy)
    return out


def dist_inside(m, cap=80):
    """Approximate Euclidean distance (in px) from each inside pixel to the outside; 0 on the edge pixels."""
    d = np.zeros(m.shape, np.float32)
    cur = m.copy()
    for k in range(cap):
        cur = erode4(cur) if k % 2 == 0 else erode8(cur)
        if not cur.any():
            break
        d += cur
    return d


def box_blur(a, r):
    if r <= 0:
        return a.astype(np.float32)
    a = a.astype(np.float32)
    for axis in (0, 1):
        p = np.pad(a, [(r, r) if ax == axis else (0, 0) for ax in (0, 1)], mode='edge')
        cs = np.cumsum(p, axis=axis)
        cs = np.concatenate([np.zeros_like(np.take(cs, [0], axis=axis)), cs], axis=axis)
        n = a.shape[axis]
        hi = np.take(cs, range(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(cs, range(0, n), axis=axis)
        a = (hi - lo) / float(2 * r + 1)
    return a


def gblur(a, r):
    """Three box blurs approximate a gaussian of sigma ~ r."""
    r = int(max(0, round(r)))
    if r == 0:
        return a.astype(np.float32)
    return box_blur(box_blur(box_blur(a, r), r), r)


def bbox(m):
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return 0, 0, 0, 0
    return xs.min(), ys.min(), xs.max(), ys.max()


def interp_ramp(mat, idx):
    """Continuous ramp lookup: idx float array in [0, 6] -> (h, w, 3) float colours."""
    cols = np.array(mat.c, np.float32)
    idx = np.clip(idx, 0.0, 6.0)
    i0 = np.floor(idx).astype(int)
    i1 = np.minimum(i0 + 1, 6)
    f = (idx - i0)[..., None]
    return cols[i0] * (1 - f) + cols[i1] * f


def lum(rgb_arr):
    a = np.asarray(rgb_arr, np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


# ----------------------------------------------------------------------------- the painter contract
class Painter:
    """Shared interface. Coordinates are icon-space; `self.c` builds masks."""

    style = ''

    def __init__(self, size=64, s=1.0):
        self.size = size
        self.s = float(s)
        self.n = int(round(size * s))
        self.c = SCanvas(self.n, self.s)
        self.glows = []
        self.grade = None

    # optional grade glow requested by the icon (colour, strength 0..1)
    def glow(self, col, strength=1.0):
        self.glows.append((rgb(col), float(strength)))

    def image(self):
        raise NotImplementedError


# ============================================================================= Style A: HD pixel
BANDS = {
    'ray': ((0.10, 2), (0.26, 1), (0.52, 0), (0.72, -1), (0.88, -2), (9, -3)),
    'ray_soft': ((0.14, 1), (0.6, 0), (0.86, -1), (9, -2)),
    'sphere': ((0.94, 3), (0.80, 2), (0.52, 1), (0.16, 0), (-0.18, -1), (-0.52, -2), (-9, -3)),
    'vgrad': ((0.22, 1), (0.62, 0), (9, -1)),
    'hgrad': ((0.22, 1), (0.62, 0), (9, -1)),
    'dgrad': ((0.22, 1), (0.62, 0), (9, -1)),
    'field': ((0.14, 1), (0.34, 2), (0.5, 1), (0.66, 0), (0.84, -1), (9, -2)),   # a blade: lit face, ridge, shade face
}


class PixelPainter(Painter):
    style = 'A'

    def __init__(self, size=64, s=1.0):
        super().__init__(size, s)
        self.parts = []          # (mask, mat)
        self.rimmask = self.c.empty()
        self.norim = self.c.empty()

    def part(self, mask, mat, mode='ray', base=0, sep=True, tex=None, axis=90.0, field=None, bands=None,
             rim=True, spec=None, **kw):
        c = self.c
        mask = mask.copy()
        if kw.get('clip') is not None:
            mask &= kw['clip']
        if kw.get('only_on'):
            mask &= c.a
        if not mask.any():
            return mask
        n = 7
        b = 3 + base
        if mode == 'field':
            f = np.clip(field, 0.0, 1.0)
            idx = np.full(mask.shape, b, int)
            bl = bands or BANDS['field']
            out = np.full(mask.shape, b + bl[-1][1], int)
            for thr, off in reversed(bl):
                out = np.where(f < thr, b + off, out)
            idx = out
        elif mode == 'flat':
            idx = np.full(mask.shape, b, int)
        else:
            kw2 = dict(kw)
            kw2.pop('clip', None)
            kw2.pop('only_on', None)
            if mode in ('ray', 'sphere', 'vgrad', 'hgrad', 'dgrad') and 'bands' not in kw2:
                kw2['bands'] = bands or BANDS[mode]
            if mode == 'ray_soft':
                mode = 'ray'
                kw2['bands'] = bands or BANDS['ray_soft']
            if mode == 'sphere':
                for key in ('cx', 'cy', 'rx', 'ry'):
                    if key in kw2:
                        kw2[key] = kw2[key] * self.s
            idx = c.shade_index(mask, n, mode, b, **kw2)
        idx = np.clip(idx, 0, 6)
        if sep:
            ring = dilate4(mask) & ~mask & c.a
            c.rgb[ring] = mat.out
            c.oc[ring] = mat.out
            self.norim |= ring
        cols = np.array(mat.c, np.uint8)
        c.rgb[mask] = cols[idx[mask]]
        c.a |= mask
        c.alpha[mask] = 255
        c.oc[mask] = mat.out
        if tex:
            self._texture(mask, idx, mat, tex, axis)
        if spec is not None:
            sx, sy = spec
            self.decal(self.c.pts([(math.floor(sx), math.floor(sy))]), mat, 3)
        self.parts.append((mask, mat))
        if rim:
            self.rimmask |= mask
        else:
            self.norim |= mask
        return mask

    def _texture(self, mask, idx, mat, tex, axis):
        c = self.c
        s = self.s
        cols = np.array(mat.c, np.uint8)
        inner = erode4(mask)
        x0, y0, x1, y1 = bbox(mask)
        if tex == 'wood':
            a = math.radians(axis)
            across = (-c.X * math.sin(a) + c.Y * math.cos(a)) / s
            grain = inner & (np.floor(across / 1.0).astype(int) % 3 == 0)
            c.rgb[grain] = cols[np.clip(idx[grain] - 1, 0, 6)]
            knot = inner & (np.floor(across / 1.0).astype(int) % 7 == 3) & (np.floor(((c.X * math.cos(a) + c.Y * math.sin(a)) / s) / 5).astype(int) % 2 == 0)
            c.rgb[knot] = cols[np.clip(idx[knot] - 1, 0, 6)]
        elif tex == 'metal':
            v = (c.X + c.Y) / s
            c0 = ((x0 + y0) / s) + ((x1 + y1 - x0 - y0) / s) * 0.36
            c1 = c0 + 5.0
            sheen = inner & (v >= c0 - 1.0) & (v < c0 + 0.6)
            dark = inner & (v >= c1) & (v < c1 + 1.4)
            c.rgb[sheen] = cols[np.clip(idx[sheen] + 2, 0, 6)]
            c.rgb[dark] = cols[np.clip(idx[dark] - 1, 0, 6)]
        elif tex in ('glass', 'jade'):
            far = (c.X + c.Y) / s
            mid = ((x0 + y0) + (x1 + y1)) / 2.0 / s
            in2 = erode4(inner)
            cres = in2 & ~shift(in2, -1, -1) & (far > mid + 1)
            cres2 = in2 & ~shift(in2, -2, -2) & (far > mid + 5)
            c.rgb[cres] = cols[np.clip(idx[cres] + 1, 0, 6)]
            c.rgb[cres2] = cols[np.clip(idx[cres2] + 2, 0, 6)]
            core = erode4(in2) & (far > mid - 2) & (far < mid + 6)
            c.rgb[core] = cols[np.clip(idx[core] + 1, 0, 6)]
        elif tex == 'cloth':
            a = math.radians(axis)
            along = (c.X * math.cos(a) + c.Y * math.sin(a)) / s
            fold = inner & (np.floor(along / 1.0).astype(int) % 7 == 0)
            c.rgb[fold] = cols[np.clip(idx[fold] - 1, 0, 6)]
        elif tex == 'paper':
            ln = inner & (np.floor(c.Y / s).astype(int) % 4 == 1)
            c.rgb[ln] = cols[np.clip(idx[ln] - 1, 0, 6)]
        elif tex == 'clay':
            v = (c.X + c.Y) / s
            c0 = ((x0 + y0) / s) + ((x1 + y1 - x0 - y0) / s) * 0.3
            sheen = inner & (v >= c0 - 0.6) & (v < c0 + 0.6)
            c.rgb[sheen] = cols[np.clip(idx[sheen] + 1, 0, 6)]

    def decal(self, mask, mat, lv=0, only_on=True):
        c = self.c
        m = mask & (c.a if only_on else np.ones_like(mask))
        if not m.any():
            return m
        col = mat[3 + lv] if isinstance(mat, Mat) else rgb(mat)
        c.rgb[m] = col
        if not only_on:
            c.a |= m
            c.alpha[m] = 255
            c.oc[m] = mat.out if isinstance(mat, Mat) else mix(col, INK, 0.7)
        return m

    def line(self, pts, mat, lv=0, w=1.0, only_on=True):
        if w <= 1.0 and self.s == 1.0:
            m = self.c.bres_path([(int(math.floor(x)), int(math.floor(y))) for x, y in pts])
        else:
            m = self.c.polyline(pts, w)
        return self.decal(m, mat, lv, only_on)

    def erase(self, mask):
        self.c.erase(mask)

    def sparkle(self, x, y, arm=1, col=WHITE, mid=None):
        c = self.c
        x, y = int(math.floor(x)), int(math.floor(y))
        pts = [(x, y)] + [(x + dx * k, y + dy * k) for k in range(1, arm + 1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        m = c.pts(pts)
        c.rgb[m] = rgb(col)
        c.a |= m
        c.alpha[m] = 255
        c.oc[m] = mix(col, INK, 0.6)

    def image(self):
        c = self.c
        body = c.a.copy()
        # rim light: a cool 1-px light on the lower-right silhouette edge of parts that take it
        S_ = c.a
        edge = S_ & (~shift(S_, 1, 0) | ~shift(S_, 0, 1)) & ~(~shift(S_, -1, 0) | ~shift(S_, 0, -1))
        for mask, mat in self.parts:
            if mat.rim <= 0:
                continue
            e = edge & mask & self.rimmask & ~self.norim
            if e.any():
                cur = c.rgb[e].astype(np.float32)
                t = min(0.65, mat.rim * 0.9)
                c.rgb[e] = (cur * (1 - t) + np.array(RIM_COOL, np.float32) * t).astype(np.uint8)
        # outline: dark local tone; near ink where the neighbouring body pixel is bright
        ring = c.outline()
        if ring.any():
            nb_l = np.zeros(c.a.shape, np.float32)
            L = lum(c.rgb)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb_l = np.maximum(nb_l, np.where(shift(body, dx, dy), shift(L, dx, dy), 0))
            t = np.clip(0.42 + (nb_l - 60.0) / 200.0, 0.42, 0.78)[..., None]
            cur = c.rgb.astype(np.float32)
            ink = np.array(INK, np.float32)
            out = cur * (1 - t) + ink * t
            c.rgb[ring] = out[ring].astype(np.uint8)
        for col, strength in self.glows:
            alphas = [int(a * strength) for a in (120, 64, 28)]
            c.glow(col, tuple(a for a in alphas if a > 0))
        return c.image(1)


# ============================================================================= Style B: painted
class PaintedPainter(Painter):
    style = 'B'

    def __init__(self, size=64, s=4):
        super().__init__(size, s)
        n = self.n
        self.rgb = np.zeros((n, n, 3), np.float32)
        self.alpha = np.zeros((n, n), np.float32)
        self.a = np.zeros((n, n), bool)
        self.parts = []
        self.shadow = True
        self.contour = 0.38

    # ---------------------------------------------------------------- shading
    def _normal(self, mask, mode, kw):
        c = self.c
        s = self.s
        n = self.n
        if mode == 'sphere':
            x0, y0, x1, y1 = bbox(mask)
            cx = kw.get('cx', (x0 + x1 + 1) / 2.0 / s) * s
            cy = kw.get('cy', (y0 + y1 + 1) / 2.0 / s) * s
            rx = kw.get('rx', (x1 - x0 + 1) / 2.0 / s) * s
            ry = kw.get('ry', (y1 - y0 + 1) / 2.0 / s) * s
            nx = (c.X - cx) / rx
            ny = (c.Y - cy) / ry
            nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
            m = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
            return nx / m, ny / m, nz / m
        # pillow: a quarter-round bevel of radius r inside the edge
        d = dist_inside(mask, cap=int(24 * s))
        x0, y0, x1, y1 = bbox(mask)
        r = kw.get('bevel', None)
        if r is None:
            r = max(1.6, min(3.2, 0.24 * min(x1 - x0 + 1, y1 - y0 + 1) / s))
        r = r * s
        h = 1.0 - (1.0 - np.clip(d / r, 0, 1)) ** 2
        h = np.where(mask, h, 0.0)
        h = gblur(h, max(1, int(round(0.35 * s))))
        gy, gx = np.gradient(h)
        k = r * 1.35
        nx, ny, nz = -gx * k, -gy * k, np.ones_like(h)
        m = np.sqrt(nx * nx + ny * ny + 1.0)
        return nx / m, ny / m, nz / m

    def part(self, mask, mat, mode='ray', base=0, sep=True, tex=None, axis=90.0, field=None, bands=None,
             rim=True, spec=None, gain=None, **kw):
        c = self.c
        s = self.s
        mask = mask.copy()
        if kw.get('clip') is not None:
            mask &= kw['clip']
        if kw.get('only_on'):
            mask &= self.a
        if not mask.any():
            return mask
        b = 3.0 + base
        g = gain if gain is not None else 3.0
        if mode == 'field':
            f = np.clip(field, 0.0, 1.0)
            vx, vy = kw.get('vdir', (0.7071, 0.7071))
            if kw.get('ridge', False):
                # a blade: two flat faces meeting at the ridge, a thin bright line along it
                tilt = np.where(f < 0.42, -0.58, 0.58).astype(np.float32)
                tilt = gblur(tilt * mask, max(1, int(round(0.3 * s))))
                tilt = np.where(mask, tilt, 0.0)
                ridge = np.exp(-((f - 0.42) / 0.05) ** 2) * 1.3
            else:
                tilt = np.clip((f - 0.5) * 2.0, -1, 1) * 0.92
                ridge = 0.0
            nX, nY = vx * tilt, vy * tilt
            nz = np.sqrt(np.clip(1 - tilt * tilt, 0, 1))
            I = nX * LIGHT[0] + nY * LIGHT[1] + nz * LIGHT[2]
            idx = b + (I - I_FLAT) * g + ridge
            spec_t = np.clip(nX * HALF[0] + nY * HALF[1] + nz * HALF[2], 0, 1)
        elif mode == 'flat':
            t = (c.Y - bbox(mask)[1]) / max(1.0, float(bbox(mask)[3] - bbox(mask)[1] + 1))
            idx = b + (0.25 - t) * 0.6
            spec_t = np.zeros(mask.shape, np.float32)
        elif mode in ('vgrad', 'hgrad', 'dgrad'):
            x0, y0, x1, y1 = bbox(mask)
            if mode == 'vgrad':
                t = (c.Y - y0) / max(1.0, float(y1 - y0 + 1))
            elif mode == 'hgrad':
                t = (c.X - x0) / max(1.0, float(x1 - x0 + 1))
            else:
                t = (c.X + c.Y - x0 - y0) / max(1.0, float(x1 + y1 - x0 - y0 + 2))
            idx = b + (0.5 - t) * 2.2
            spec_t = np.zeros(mask.shape, np.float32)
        else:
            nx, ny, nz = self._normal(mask, mode, kw)
            I = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
            idx = b + (I - I_FLAT) * g
            spec_t = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
        if tex:
            idx = self._texture(mask, idx, tex, axis)
        col = interp_ramp(mat, idx)
        # specular
        sp = (spec_t ** mat.shine) * mat.spec
        if mode == 'flat':
            sp = np.zeros_like(sp)
        col = col + (np.array(WHITE, np.float32) - col) * sp[..., None]
        # ambient occlusion on what is already painted, just outside the new part
        if sep and self.a.any():
            ao = gblur(mask.astype(np.float32), max(1, int(round(0.55 * s))))
            ao = np.clip(ao * 1.6, 0, 1) * (~mask) * self.a
            self.rgb *= (1.0 - 0.5 * ao)[..., None]
        self.rgb[mask] = col[mask]
        self.alpha[mask] = 1.0
        self.a |= mask
        if spec is not None:
            x, y = spec
            self.sparkle(x, y, 1.2, WHITE, soft=True)
        self.parts.append((mask, mat, rim))
        return mask

    def _texture(self, mask, idx, tex, axis):
        c = self.c
        s = self.s
        x0, y0, x1, y1 = bbox(mask)
        X, Y = c.X / s, c.Y / s
        if tex == 'wood':
            a = math.radians(axis)
            across = -X * math.sin(a) + Y * math.cos(a)
            along = X * math.cos(a) + Y * math.sin(a)
            wave = np.sin(across * 2 * math.pi / 2.6 + np.sin(along * 0.9) * 0.9) * 0.28 + np.sin(across * 2 * math.pi / 7.0) * 0.22
            return idx + wave
        if tex == 'metal':
            v = X + Y
            c0 = ((x0 + y0) / s) + ((x1 + y1 - x0 - y0) / s) * 0.36
            c1 = c0 + 5.5
            sheen = 1.5 * np.exp(-((v - c0) / 1.6) ** 2) - 0.7 * np.exp(-((v - c1) / 2.2) ** 2)
            return idx + sheen
        if tex in ('glass', 'jade'):
            v = X + Y
            lo, hi = (x0 + y0) / s, (x1 + y1) / s
            f = np.clip((v - lo) / max(1.0, hi - lo), 0, 1)
            d = dist_inside(mask, cap=int(20 * s)) / s
            inner = np.clip(d / 4.0, 0, 1)
            # through-lit: the directional shading softened, light pooling on the far side, a lighter core
            return 3.0 + (idx - 3.0) * 0.55 + 1.6 * f * f - 0.5 + inner * 0.5 - 0.4 * (1 - f)
        if tex == 'cloth':
            a = math.radians(axis)
            along = X * math.cos(a) + Y * math.sin(a)
            across = -X * math.sin(a) + Y * math.cos(a)
            return idx + 0.38 * np.sin(along * 2 * math.pi / 8.5 + across * 0.12)
        if tex == 'paper':
            return idx + 0.12 * np.sin(Y * 2 * math.pi / 3.0)
        if tex == 'clay':
            v = X + Y
            c0 = ((x0 + y0) / s) + ((x1 + y1 - x0 - y0) / s) * 0.3
            return idx + 0.7 * np.exp(-((v - c0) / 2.4) ** 2)
        return idx

    def decal(self, mask, mat, lv=0, only_on=True, alpha=1.0):
        m = mask & (self.a if only_on else np.ones_like(mask))
        if not m.any():
            return m
        col = np.array(mat[3 + lv] if isinstance(mat, Mat) else rgb(mat), np.float32)
        # a hair of softness so the decal does not alias at 1x
        soft = gblur(m.astype(np.float32), max(1, int(round(0.3 * self.s))))
        soft = np.clip(soft * 1.3, 0, 1) * alpha
        if only_on:
            soft = soft * self.a
        self.rgb = self.rgb * (1 - soft[..., None]) + col * soft[..., None]
        if not only_on:
            self.alpha = np.maximum(self.alpha, soft)
            self.a |= m
        return m

    def line(self, pts, mat, lv=0, w=1.0, only_on=True, alpha=1.0):
        m = self.c.polyline(pts, w)
        return self.decal(m, mat, lv, only_on, alpha)

    def erase(self, mask):
        self.a &= ~mask
        self.alpha[mask] = 0
        self.rgb[mask] = 0

    def sparkle(self, x, y, arm=1.0, col=WHITE, mid=None, soft=False):
        c = self.c
        m = c.seg(x - arm, y, x + arm, y, 0.6) | c.seg(x, y - arm, x, y + arm, 0.6) | c.circle(x, y, 0.55)
        glow = gblur(c.circle(x, y, arm * 0.9).astype(np.float32), int(round(0.6 * self.s)))
        colf = np.array(rgb(col), np.float32)
        w = np.clip(gblur(m.astype(np.float32), max(1, int(round(0.25 * self.s)))) * 1.4, 0, 1)
        w = np.maximum(w, glow * 0.45)
        self.rgb = self.rgb * (1 - w[..., None]) + colf * w[..., None]
        self.alpha = np.maximum(self.alpha, w)
        self.a |= m

    # ---------------------------------------------------------------- output
    def image(self):
        s = self.s
        n = self.n
        body = self.a.copy()
        d = dist_inside(body, cap=int(8 * s))
        # rim light on the lower-right edge
        h = gblur(body.astype(np.float32), max(1, int(round(0.9 * s))))
        gy, gx = np.gradient(h)
        toward = np.clip(-(gx + gy) * s * 2.2, 0, 1)
        band = np.clip(1.0 - d / (1.3 * s), 0, 1) * body
        rimcol = np.array(RIM_COOL, np.float32)
        for mask, mat, rim in self.parts:
            if not rim or mat.rim <= 0:
                continue
            w = band * toward * mask * (mat.rim * 0.9)
            self.rgb = self.rgb * (1 - w[..., None]) + rimcol * w[..., None]
        # soft dark contour along the silhouette
        cont = np.clip(1.0 - d / (1.1 * s), 0, 1) * body
        self.rgb *= (1.0 - self.contour * cont)[..., None]
        # compose: glow, shadow, body (premultiplied)
        out_rgb = np.zeros((n, n, 3), np.float32)
        out_a = np.zeros((n, n), np.float32)

        def over(col, a):
            nonlocal out_rgb, out_a
            col = np.asarray(col, np.float32)
            a = np.clip(a, 0, 1)
            out_rgb = col * a[..., None] + out_rgb * (1 - a)[..., None]
            out_a = a + out_a * (1 - a)

        for col, strength in self.glows:
            big = dilate8(dilate8(body))
            g = gblur(big.astype(np.float32), int(round(2.2 * s))) * 0.9 * strength
            g = np.clip(g, 0, 1) * (1 - body * 0.6)
            over(np.broadcast_to(np.array(col, np.float32), (n, n, 3)), g)
        if self.shadow:
            sh = gblur(shift(body, 0, -int(round(1.5 * s))).astype(np.float32), int(round(1.4 * s))) * 0.42
            over(np.zeros((n, n, 3), np.float32), sh)
        # inner glow by grade: a soft light just inside the edge
        for col, strength in self.glows:
            ig = np.clip(1.0 - d / (3.0 * s), 0, 1) * body * 0.42 * strength
            self.rgb = self.rgb * (1 - ig[..., None]) + np.array(col, np.float32) * ig[..., None]
        over(self.rgb, self.alpha)
        # box downsample (premultiplied)
        pm = out_rgb * out_a[..., None]
        m = self.size
        k = n // m              # the canvas is k x the output (s = 4 for 64 out of 256; s = 8 with a 64-px output of a 32-px glyph)
        pm = pm.reshape(m, k, m, k, 3).mean(axis=(1, 3))
        a = out_a.reshape(m, k, m, k).mean(axis=(1, 3))
        rgb_ = np.where(a[..., None] > 1e-4, pm / np.maximum(a[..., None], 1e-4), 0)
        arr = np.zeros((m, m, 4), np.uint8)
        arr[..., :3] = np.clip(rgb_ + 0.5, 0, 255).astype(np.uint8)
        arr[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, 'RGBA')


# ============================================================================= sheet helpers
def nine_slice(src, w, h, slice_px, border_px):
    """CSS border-image with `stretch`: corners scaled from slice_px to border_px, edges and centre stretched."""
    sw, sh = src.size
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sp, bp = slice_px, border_px
    if isinstance(sp, int):
        sp = (sp, sp)
    if isinstance(bp, int):
        bp = (bp, bp)
    sx, sy = sp
    bx, by = bp
    cx, cy = sw - 2 * sx, sh - 2 * sy
    iw, ih = max(0, w - 2 * bx), max(0, h - 2 * by)
    res = Image.Resampling.BOX if (sx > bx) else Image.Resampling.BILINEAR

    def put(box, dst_box):
        dw, dh = dst_box[2] - dst_box[0], dst_box[3] - dst_box[1]
        if dw <= 0 or dh <= 0:
            return
        piece = src.crop(box).resize((dw, dh), res)
        out.alpha_composite(piece, (dst_box[0], dst_box[1]))
    put((0, 0, sx, sy), (0, 0, bx, by))
    put((sw - sx, 0, sw, sy), (w - bx, 0, w, by))
    put((0, sh - sy, sx, sh), (0, h - by, bx, h))
    put((sw - sx, sh - sy, sw, sh), (w - bx, h - by, w, h))
    put((sx, 0, sx + cx, sy), (bx, 0, bx + iw, by))
    put((sx, sh - sy, sx + cx, sh), (bx, h - by, bx + iw, h))
    put((0, sy, sx, sy + cy), (0, by, bx, by + ih))
    put((sw - sx, sy, sw, sy + cy), (w - bx, by, w, by + ih))
    put((sx, sy, sx + cx, sy + cy), (bx, by, bx + iw, by + ih))
    return out


def hud_ring(radius, active=False, gold=False, ss=4):
    """hud.gd ring(): the shadow, the gold rim disc, the jade disc, the inner jade arc and the highlight arc."""
    r = radius
    pad = 14
    n = int((r + pad) * 2 * ss)
    cx = cy = (r + pad) * ss
    yy, xx = np.mgrid[0:n, 0:n]
    X = xx + 0.5 - cx
    Y = yy + 0.5 - cy
    D = np.sqrt(X * X + Y * Y) / ss
    out_rgb = np.zeros((n, n, 3), np.float32)
    out_a = np.zeros((n, n), np.float32)

    def over(col, a):
        nonlocal out_rgb, out_a
        col = np.asarray(col, np.float32)
        a = np.clip(a, 0, 1).astype(np.float32)
        out_rgb = col * a[..., None] + out_rgb * (1 - a)[..., None]
        out_a = a + out_a * (1 - a)

    def disc(rad, top, bottom, cyoff=0.0):
        Yd = (yy + 0.5 - cy - cyoff * ss) / ss
        Xd = X / ss
        Dd = np.sqrt(Xd * Xd + Yd * Yd)
        t = np.clip((Yd / rad + 1) * 0.5, 0, 1)
        col = np.array(rgb(top), np.float32)[None, None, :] * (1 - t)[..., None] + np.array(rgb(bottom), np.float32)[None, None, :] * t[..., None]
        a = np.clip(rad - Dd + 0.5, 0, 1)
        over(col, a)
        edge = np.clip(1.0 - np.abs(Dd - rad) , 0, 1) * 0.6
        over(np.broadcast_to(np.array(mix(bottom, top, 0.3), np.float32), (n, n, 3)), edge)

    def arc(rad, width, col, alpha, a0=0.0, a1=2 * math.pi):
        ang = np.arctan2(Y, X) % (2 * math.pi)
        sel = (ang >= a0) & (ang <= a1) if a0 <= a1 else ((ang >= a0) | (ang <= a1))
        a = np.clip(width / 2.0 - np.abs(D - rad) + 0.5, 0, 1) * alpha * sel
        over(np.broadcast_to(np.array(rgb(col), np.float32), (n, n, 3)), a)

    lit = active or gold
    # shadow
    Ys = (yy + 0.5 - cy - 4 * ss) / ss
    Ds = np.sqrt((X / ss) ** 2 + Ys ** 2)
    over(np.zeros((n, n, 3), np.float32), np.clip(r + 4 - Ds + 0.5, 0, 1) * 0.42)
    if lit:
        for i in range(3):
            arc(r + 5 + i * 3, 3.0, '#E5B84C', 0.30 - i * 0.09)
    disc(r + 2.5, '#f0d08a' if lit else '#c6a262', '#7a5426' if lit else '#5c4424')
    disc(r, '#1d5157', '#061519')
    arc(r - 3.5, 1.5, (102, 214, 189), 0.30 if lit else 0.2)
    arc(r - 2.0, max(2.0, r * 0.07), (255, 255, 255), 0.12, math.pi * 1.15, math.pi * 1.85)
    pm = out_rgb * out_a[..., None]
    m = n // ss
    pm = pm.reshape(m, ss, m, ss, 3).mean(axis=(1, 3))
    a = out_a.reshape(m, ss, m, ss).mean(axis=(1, 3))
    rgb_ = np.where(a[..., None] > 1e-4, pm / np.maximum(a[..., None], 1e-4), 0)
    arr = np.zeros((m, m, 4), np.uint8)
    arr[..., :3] = np.clip(rgb_ + 0.5, 0, 255).astype(np.uint8)
    arr[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA'), (r + pad)


def scale_nearest(img, size):
    return img.resize((size, size), Image.Resampling.NEAREST)


def scale_box(img, size):
    """Area-average downscale on premultiplied alpha (what a good filter gives)."""
    arr = np.asarray(img.convert('RGBA'), np.float32)
    a = arr[..., 3:4] / 255.0
    pm = Image.fromarray(np.concatenate([arr[..., :3] * a, arr[..., 3:4]], axis=2).astype(np.uint8), 'RGBA')
    small = pm.resize((size, size), Image.Resampling.BOX if size < img.width else Image.Resampling.BICUBIC)
    sa = np.asarray(small, np.float32)
    al = sa[..., 3:4] / 255.0
    rgb_ = np.where(al > 1e-3, sa[..., :3] / np.maximum(al, 1e-3), 0)
    out = np.concatenate([np.clip(rgb_, 0, 255), sa[..., 3:4]], axis=2).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')
