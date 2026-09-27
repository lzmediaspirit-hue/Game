"""Icon style study: Style B, the painted renderer the study compared with Style A.

Style A ("HD pixel", the chosen style) now lives in the pipeline: `pix.PixelPainter` paints the icon
descriptions in `families/*.py` (their HD drawings, `registry.HD`). `PaintedPainter` renders the same
descriptions the painted way: at 4x (256 px) with smooth normals, specular, ambient occlusion between parts,
a soft contour and a soft grade glow, box-downsampled to 64 so the edges are anti-aliased but still crisp at 1x.
Deterministic: numpy only, no randomness, no timestamps.
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

from pix import WHITE, RIM_COOL, Painter, PixelPainter, Ramp, dilate8, erode4, erode8, rgb, shift  # noqa: E402,F401
from review import hud_ring, nine_slice, scale_box, scale_nearest  # noqa: E402,F401

LIGHT = np.array((-0.55, -0.65, 0.52))
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = LIGHT + np.array((0.0, 0.0, 1.0))
HALF = HALF / np.linalg.norm(HALF)
I_FLAT = float(LIGHT[2])
# specular strength and shininess per material kind (palette.KINDS)
SPEC = {'matte': (0.10, 8), 'metal': (0.85, 26), 'gold': (0.90, 22), 'glass': (0.70, 40), 'jade': (0.55, 30), 'wood': (0.12, 8),
        'cloth': (0.05, 6), 'clay': (0.18, 10), 'paper': (0.05, 6), 'porcelain': (0.65, 30), 'gem': (0.95, 44), 'leather': (0.22, 10),
        'ink': (0.35, 20), 'light': (0.0, 1), 'silk': (0.35, 12)}


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
        a = (np.take(cs, range(2 * r + 1, 2 * r + 1 + n), axis=axis) - np.take(cs, range(0, n), axis=axis)) / float(2 * r + 1)
    return a


def gblur(a, r):
    """Three box blurs approximate a gaussian of sigma ~ r."""
    r = int(max(0, round(r)))
    return a.astype(np.float32) if r == 0 else box_blur(box_blur(box_blur(a, r), r), r)


def bbox(m):
    ys, xs = np.nonzero(m)
    return (0, 0, 0, 0) if len(xs) == 0 else (xs.min(), ys.min(), xs.max(), ys.max())


def interp_ramp(mat, idx):
    """Continuous ramp lookup: idx float array in [0, 6] -> (h, w, 3) float colours."""
    cols = np.array(mat.c, np.float32)
    idx = np.clip(idx, 0.0, 6.0)
    i0 = np.floor(idx).astype(int)
    f = (idx - i0)[..., None]
    return cols[i0] * (1 - f) + cols[np.minimum(i0 + 1, 6)] * f


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
        c, s = self.c, self.s
        if mode == 'sphere':
            x0, y0, x1, y1 = bbox(mask)
            cx = kw.get('cx', (x0 + x1 + 1) / 2.0 / s) * s
            cy = kw.get('cy', (y0 + y1 + 1) / 2.0 / s) * s
            rx = kw.get('rx', (x1 - x0 + 1) / 2.0 / s) * s
            ry = kw.get('ry', (y1 - y0 + 1) / 2.0 / s) * s
            nx, ny = (c.X - cx) / rx, (c.Y - cy) / ry
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
        h = np.where(mask, 1.0 - (1.0 - np.clip(d / r, 0, 1)) ** 2, 0.0)
        h = gblur(h, max(1, int(round(0.35 * s))))
        gy, gx = np.gradient(h)
        k = r * 1.35
        nx, ny = -gx * k, -gy * k
        m = np.sqrt(nx * nx + ny * ny + 1.0)
        return nx / m, ny / m, 1.0 / m

    def part(self, mask, mat, mode='ray', base=0, sep=True, tex=None, axis=90.0, field=None, bands=None,
             rim=True, spec=None, gain=None, **kw):
        c, s = self.c, self.s
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
                tilt = np.where(mask, gblur(tilt * mask, max(1, int(round(0.3 * s)))), 0.0)
                ridge = np.exp(-((f - 0.42) / 0.05) ** 2) * 1.3
            else:
                tilt = np.clip((f - 0.5) * 2.0, -1, 1) * 0.92
                ridge = 0.0
            nX, nY = vx * tilt, vy * tilt
            nz = np.sqrt(np.clip(1 - tilt * tilt, 0, 1))
            idx = b + (nX * LIGHT[0] + nY * LIGHT[1] + nz * LIGHT[2] - I_FLAT) * g + ridge
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
            idx = b + (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2] - I_FLAT) * g
            spec_t = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
        if tex:
            idx = self._texture(mask, idx, tex, axis)
        col = interp_ramp(mat, idx)
        spec_k, shine = SPEC[mat.kind]
        sp = np.zeros_like(spec_t) if mode == 'flat' else (spec_t ** shine) * spec_k
        col = col + (np.array(WHITE, np.float32) - col) * sp[..., None]
        # ambient occlusion on what is already painted, just outside the new part
        if sep and self.a.any():
            ao = np.clip(gblur(mask.astype(np.float32), max(1, int(round(0.55 * s)))) * 1.6, 0, 1) * (~mask) * self.a
            self.rgb *= (1.0 - 0.5 * ao)[..., None]
        self.rgb[mask] = col[mask]
        self.alpha[mask] = 1.0
        self.a |= mask
        if spec is not None:
            self.sparkle(spec[0], spec[1], 1.2, WHITE)
        self.parts.append((mask, mat, rim))
        return mask

    def cylinder(self, fr, mask, hw, mat, base=0, ridge=False, **kw):
        f = fr.field(self.c, hw)[1]
        vdir = fr.v
        if not fr.lit_first():
            f, vdir = 1.0 - f, (-fr.v[0], -fr.v[1])
        return self.part(mask, mat, 'field', base=base, field=f, vdir=vdir, ridge=ridge, **kw)

    def _texture(self, mask, idx, tex, axis):
        c, s = self.c, self.s
        x0, y0, x1, y1 = bbox(mask)
        X, Y = c.X / s, c.Y / s
        if tex == 'wood':
            a = math.radians(axis)
            across = -X * math.sin(a) + Y * math.cos(a)
            along = X * math.cos(a) + Y * math.sin(a)
            return idx + np.sin(across * 2 * math.pi / 2.6 + np.sin(along * 0.9) * 0.9) * 0.28 + np.sin(across * 2 * math.pi / 7.0) * 0.22
        if tex == 'metal':
            v = X + Y
            c0 = ((x0 + y0) / s) + ((x1 + y1 - x0 - y0) / s) * 0.36
            return idx + 1.5 * np.exp(-((v - c0) / 1.6) ** 2) - 0.7 * np.exp(-((v - c0 - 5.5) / 2.2) ** 2)
        if tex in ('glass', 'jade'):
            lo, hi = (x0 + y0) / s, (x1 + y1) / s
            f = np.clip((X + Y - lo) / max(1.0, hi - lo), 0, 1)
            inner = np.clip(dist_inside(mask, cap=int(20 * s)) / s / 4.0, 0, 1)
            # through-lit: the directional shading softened, light pooling on the far side, a lighter core
            return 3.0 + (idx - 3.0) * 0.55 + 1.6 * f * f - 0.5 + inner * 0.5 - 0.4 * (1 - f)
        if tex == 'cloth':
            a = math.radians(axis)
            return idx + 0.38 * np.sin((X * math.cos(a) + Y * math.sin(a)) * 2 * math.pi / 8.5 + (-X * math.sin(a) + Y * math.cos(a)) * 0.12)
        if tex == 'paper':
            return idx + 0.12 * np.sin(Y * 2 * math.pi / 3.0)
        if tex == 'clay':
            c0 = ((x0 + y0) / s) + ((x1 + y1 - x0 - y0) / s) * 0.3
            return idx + 0.7 * np.exp(-((X + Y - c0) / 2.4) ** 2)
        return idx

    def decal(self, mask, mat, lv=0, only_on=True, alpha=1.0):
        m = mask & (self.a if only_on else np.ones_like(mask))
        if not m.any():
            return m
        col = np.array(mat[3 + lv] if isinstance(mat, Ramp) else rgb(mat), np.float32)
        # a hair of softness so the decal does not alias at 1x
        soft = np.clip(gblur(m.astype(np.float32), max(1, int(round(0.3 * self.s)))) * 1.3, 0, 1) * alpha
        if only_on:
            soft = soft * self.a
        self.rgb = self.rgb * (1 - soft[..., None]) + col * soft[..., None]
        if not only_on:
            self.alpha = np.maximum(self.alpha, soft)
            self.a |= m
        return m

    def line(self, pts, mat, lv=0, w=1.0, only_on=True, alpha=1.0):
        return self.decal(self.c.polyline(pts, w), mat, lv, only_on, alpha)

    def erase(self, mask):
        self.a &= ~mask
        self.alpha[mask] = 0
        self.rgb[mask] = 0

    def sparkle(self, x, y, arm=1.0, col=WHITE):
        c = self.c
        m = c.seg(x - arm, y, x + arm, y, 0.6) | c.seg(x, y - arm, x, y + arm, 0.6) | c.circle(x, y, 0.55)
        glow = gblur(c.circle(x, y, arm * 0.9).astype(np.float32), int(round(0.6 * self.s)))
        w = np.maximum(np.clip(gblur(m.astype(np.float32), max(1, int(round(0.25 * self.s)))) * 1.4, 0, 1), glow * 0.45)
        self.rgb = self.rgb * (1 - w[..., None]) + np.array(rgb(col), np.float32) * w[..., None]
        self.alpha = np.maximum(self.alpha, w)
        self.a |= m

    # ---------------------------------------------------------------- output
    def image(self):
        s, n = self.s, self.n
        body = self.a.copy()
        d = dist_inside(body, cap=int(8 * s))
        # rim light on the lower-right edge
        gy, gx = np.gradient(gblur(body.astype(np.float32), max(1, int(round(0.9 * s)))))
        toward = np.clip(-(gx + gy) * s * 2.2, 0, 1)
        band = np.clip(1.0 - d / (1.3 * s), 0, 1) * body
        for mask, mat, rim in self.parts:
            if rim and mat.rim > 0:
                w = band * toward * mask * (mat.rim * 0.9)
                self.rgb = self.rgb * (1 - w[..., None]) + np.array(RIM_COOL, np.float32) * w[..., None]
        # soft dark contour along the silhouette
        self.rgb *= (1.0 - self.contour * np.clip(1.0 - d / (1.1 * s), 0, 1) * body)[..., None]
        # compose: glow, shadow, body (premultiplied)
        out_rgb = np.zeros((n, n, 3), np.float32)
        out_a = np.zeros((n, n), np.float32)

        def over(col, a):
            nonlocal out_rgb, out_a
            a = np.clip(a, 0, 1)
            out_rgb = np.asarray(col, np.float32) * a[..., None] + out_rgb * (1 - a)[..., None]
            out_a = a + out_a * (1 - a)

        for col, strength in self.glows:
            g = np.clip(gblur(dilate8(dilate8(body)).astype(np.float32), int(round(2.2 * s))) * 0.9 * strength, 0, 1) * (1 - body * 0.6)
            over(np.broadcast_to(np.array(col, np.float32), (n, n, 3)), g)
        if self.shadow:
            over(np.zeros((n, n, 3), np.float32), gblur(shift(body, 0, -int(round(1.5 * s))).astype(np.float32), int(round(1.4 * s))) * 0.42)
        # inner glow by grade: a soft light just inside the edge
        for col, strength in self.glows:
            ig = np.clip(1.0 - d / (3.0 * s), 0, 1) * body * 0.42 * strength
            self.rgb = self.rgb * (1 - ig[..., None]) + np.array(col, np.float32) * ig[..., None]
        over(self.rgb, self.alpha)
        # box downsample (premultiplied): the canvas is k x the output
        m = self.size
        k = n // m
        pm = (out_rgb * out_a[..., None]).reshape(m, k, m, k, 3).mean(axis=(1, 3))
        a = out_a.reshape(m, k, m, k).mean(axis=(1, 3))
        arr = np.zeros((m, m, 4), np.uint8)
        arr[..., :3] = np.clip(np.where(a[..., None] > 1e-4, pm / np.maximum(a[..., None], 1e-4), 0) + 0.5, 0, 255).astype(np.uint8)
        arr[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, 'RGBA')
