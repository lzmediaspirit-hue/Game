"""Tiny deterministic pixel-art drawing library for Jade River icons.

Everything is drawn on a low-resolution *art* canvas (32x32 for items, 16x16 for
HUD glyphs, 12x12 for status icons and markers) and upscaled x2 with nearest
neighbour on export (native pixel scale 2, see docs/art-contracts.md).

Coordinates
-----------
Masks built from continuous shapes (ellipse, poly, seg) sample pixel centres at
(x + 0.5, y + 0.5): a polygon from (2, 2) to (10, 10) covers pixels 2..9.
Pixel helpers (px, rect, bres) use integer pixel indices.

Colour model
------------
A `Ramp` is a list of colours dark -> light plus an outline colour. Painting a
mask with a ramp picks one ramp level per pixel from a shading mode (flat, bevel,
ray, sphere, gradients). Every painted pixel also remembers the outline colour of
its material so the final automatic outline is hue-tinted (dark teal around jade,
dark brown around wood, ...). Light always comes from the upper left.
"""
from __future__ import annotations

import colorsys
import zlib

import numpy as np
from PIL import Image

INK = (7, 16, 21)


# --------------------------------------------------------------------------- colour
def rgb(c):
    """Accept '#RRGGBB', (r, g, b) or a numpy triple and return an int tuple."""
    if isinstance(c, str):
        c = c.lstrip('#')
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    return (int(c[0]), int(c[1]), int(c[2]))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _toward(h, target, amt):
    d = (target - h + 0.5) % 1.0 - 0.5
    if abs(d) <= amt:
        return target % 1.0
    return (h + amt * (1 if d > 0 else -1)) % 1.0


def hsv_shift(c, dh=0.0, ds=0.0, dv=0.0):
    r, g, b = [v / 255.0 for v in rgb(c)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + dh) % 1.0
    s = min(1.0, max(0.0, s + ds))
    v = min(1.0, max(0.0, v + dv))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def dark_of(c, t=0.86):
    """Hue-tinted dark outline colour for a fill colour."""
    return mix(c, INK, t)


class Ramp:
    """Colours dark -> light and the outline colour used around this material."""

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
    """Hue-shifted ramp: shadows drift to blue-green, lights to warm gold."""
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
    if isinstance(m, Ramp):
        return m
    c = rgb(m)
    return Ramp([c], dark_of(c))


def stable_rng(key):
    """Deterministic RNG seeded from a string."""
    return np.random.default_rng(zlib.crc32(key.encode('utf-8')))


# --------------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w=32, h=None):
        h = w if h is None else h
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), bool)          # opaque art pixels
        self.alpha = np.zeros((h, w), np.uint8)  # final alpha (glow bands < 255)
        self.oc = np.zeros((h, w, 3), np.uint8)  # outline colour requested by pixel
        yy, xx = np.mgrid[0:h, 0:w]
        self.X = xx.astype(float) + 0.5
        self.Y = yy.astype(float) + 0.5
        self.xi, self.yi = xx, yy

    # ---------------------------------------------------------------- masks
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
        """Inclusive integer pixel rectangle."""
        return (self.xi >= x0) & (self.xi <= x1) & (self.yi >= y0) & (self.yi <= y1)

    def poly(self, pts):
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
        """Thick segment (distance from pixel centre to segment <= w/2)."""
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

    def bres(self, x0, y0, x1, y1):
        """1-pixel Bresenham line between integer pixels."""
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

    def bres_path(self, pts):
        m = self.empty()
        for a, b in zip(pts, pts[1:]):
            m |= self.bres(a[0], a[1], b[0], b[1])
        return m

    def arc(self, cx, cy, r, w, a0, a1, ry=None):
        """Ring sector; angles in degrees, 0 = right, 90 = up (screen)."""
        m = self.ring(cx, cy, r, w, ry)
        ang = np.degrees(np.arctan2(-(self.Y - cy), self.X - cx)) % 360.0
        a0 %= 360.0
        a1 %= 360.0
        if a0 <= a1:
            sel = (ang >= a0) & (ang <= a1)
        else:
            sel = (ang >= a0) | (ang <= a1)
        return m & sel

    def sector(self, cx, cy, r, a0, a1, ry=None):
        m = self.ellipse(cx, cy, r, ry)
        ang = np.degrees(np.arctan2(-(self.Y - cy), self.X - cx)) % 360.0
        a0 %= 360.0
        a1 %= 360.0
        if a0 <= a1:
            sel = (ang >= a0) & (ang <= a1)
        else:
            sel = (ang >= a0) | (ang <= a1)
        return m & sel

    def diag(self, u0, u1, v0, v1):
        """Band in 45-degree space: u = x - y (along, up-right), v = x + y (across)."""
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
        """Mask from ASCII rows; any char not in ' .' (or in `chars`) is set."""
        m = self.empty()
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                on = (ch in chars) if chars else (ch not in ' .')
                if on:
                    x, y = ox + i, oy + j
                    if 0 <= x < self.w and 0 <= y < self.h:
                        m[y, x] = True
        return m

    # ---------------------------------------------------------------- shading
    def shade_index(self, mask, n, mode='ray', base=None, **kw):
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
            # bands across a 45-degree diagonal strip: small v (upper-left side) lit
            v = self.xi + self.yi
            vv = np.where(mask, v, 10 ** 6)
            u = self.xi - self.yi
            idx = np.full((self.h, self.w), base, int)
            vmin = {}
            vmax = {}
            for uu in np.unique(u[mask]):
                sel = mask & (u == uu)
                vmin[uu] = v[sel].min()
                vmax[uu] = v[sel].max()
            for (y, x) in zip(*np.nonzero(mask)):
                uu = u[y, x]
                lo, hi = vmin[uu], vmax[uu]
                if hi - lo <= 0:
                    continue
                t = (v[y, x] - lo) / float(hi - lo)
                bands = kw.get('bands', ((0.34, 1), (0.67, 0), (9, -1)))
                for thr, off in bands:
                    if t < thr:
                        idx[y, x] = base + off
                        break
            del vv
        if kw.get('despeckle', True):
            idx = despeckle(idx, mask)
        return np.clip(idx, 0, n - 1)

    def put(self, mask, mat, mode='ray', base=None, sep=False, sep_col=None, only_on=False,
            clip=None, out=None, **kw):
        """Paint `mask` with material `mat` using shading `mode`.

        sep:      draw a 1px dark line (part separation) around the new part over
                  pixels already painted.
        only_on:  paint only where something is already painted (decals, engravings).
        """
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
            ring = dilate4(mask) & ~mask & self.a
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

    def pxs(self, pts, col, out=None):
        for x, y in pts:
            self.px(x, y, col, out)

    def recolor(self, mask, col):
        """Change colour of already painted pixels in mask (keeps outline colour)."""
        m = mask & self.a
        self.rgb[m] = rgb(col)

    def erase(self, mask):
        self.a &= ~mask
        self.alpha[mask] = 0
        self.rgb[mask] = 0

    def inline(self, mask, col=None):
        """Darken the inner border of an already painted mask (edge line)."""
        edge = mask & ~erode4(mask)
        c = col if col is not None else INK
        self.recolor(edge, c)

    def stamp(self, rows, cmap, ox=0, oy=0):
        """Paint ASCII art. cmap: char -> colour | (Ramp, idx) | None(erase)."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in ' .' and ch not in cmap:
                    continue
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

    # ---------------------------------------------------------------- outline & glow
    def outline(self, col=None, diag=False, mask=None):
        """Add the 1-art-px dark outline around every opaque pixel."""
        a = self.a
        if not hasattr(self, 'body'):
            self.body = a.copy()  # silhouette before the first outline (clip check)
        target = ~a if mask is None else (~a & mask)
        new_rgb = self.rgb.copy()
        new_a = a.copy()
        best = np.full((self.h, self.w), 10 ** 9)
        offs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        if diag:
            offs += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for dx, dy in offs:
            nb = shift(a, dx, dy)
            noc = shift3(self.oc, dx, dy)
            lum = noc.astype(int).sum(axis=2)
            sel = target & nb & (lum < best)
            new_rgb[sel] = noc[sel] if col is None else rgb(col)
            best = np.where(sel, lum, best)
            new_a |= sel
        ring = new_a & ~a
        self.rgb = new_rgb
        self.a = new_a
        self.alpha[ring] = 255
        self.oc[ring] = self.rgb[ring]
        return ring

    def glow(self, col, alphas=(150, 70), diag=True):
        """Stepped (non-blurred) glow bands outside the outlined silhouette."""
        solid = self.alpha > 0
        cur = solid.copy()
        for al in alphas:
            ring = (dilate8(cur) if diag else dilate4(cur)) & ~cur
            self.rgb[ring] = rgb(col)
            self.alpha[ring] = al
            cur |= ring

    # ---------------------------------------------------------------- output
    def image(self, scale=2):
        arr = np.zeros((self.h, self.w, 4), np.uint8)
        arr[..., :3] = self.rgb
        arr[..., 3] = self.alpha
        arr[self.alpha == 0] = 0
        if scale != 1:
            arr = arr.repeat(scale, axis=0).repeat(scale, axis=1)
        return Image.fromarray(arr, 'RGBA')


# --------------------------------------------------------------------------- mask ops
def shift(m, dx, dy):
    """out[y, x] = m[y + dy, x + dx] (False outside)."""
    h, w = m.shape
    out = np.zeros_like(m)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    if ys0 < ys1 and xs0 < xs1:
        out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def shift3(m, dx, dy):
    h, w = m.shape[:2]
    out = np.zeros_like(m)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    if ys0 < ys1 and xs0 < xs1:
        out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def move(m, dx, dy):
    """Translate a mask by (dx, dy)."""
    return shift(m, -dx, -dy)


def dilate4(m):
    return m | shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)


def dilate8(m):
    out = dilate4(m)
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        out |= shift(m, dx, dy)
    return out


def erode4(m):
    return m & shift(m, 1, 0) & shift(m, -1, 0) & shift(m, 0, 1) & shift(m, 0, -1)


def edge_dist(mask, dx, dy, maxd=40):
    """Number of in-mask steps from each pixel in direction (dx, dy) before leaving."""
    d = np.zeros(mask.shape, int)
    alive = mask.copy()
    for k in range(1, maxd + 1):
        alive &= shift(mask, dx * k, dy * k)
        if not alive.any():
            break
        d += alive
    return d


def light_dists(mask):
    """(a, b): distance to the lit (upper/left) edge and to the shadow edge."""
    a = np.minimum(edge_dist(mask, 0, -1), edge_dist(mask, -1, 0))
    b = np.minimum(edge_dist(mask, 0, 1), edge_dist(mask, 1, 0))
    return a, b


def despeckle(idx, mask):
    """Remove lone pixels whose 4 in-mask neighbours all share another level."""
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


def bbox(mask):
    ys, xs = np.nonzero(mask)
    return xs.min(), ys.min(), xs.max(), ys.max()
