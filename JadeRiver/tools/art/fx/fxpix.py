"""Palette-index pixel rasteriser for the technique FX sheets (tools/art/fx).

A frame is drawn on an index canvas: every pixel holds a tone index, not a colour, so one drawing of a form
serves every element by a palette swap (elements.py maps indices to an element's ramp). Everything is
deterministic: distance fields on a numpy grid thresholded to crisp masks, no anti-aliasing, no smoothing and no
unseeded randomness (px_hash gives the scatter its variety).

Indices (INK .. HAZE): a dark ink rim, the ramp deep / base / light / glint, a white core, the element's accent
(droplets, embers, stars), and a half-transparent haze of the base colour for dust and dome fills.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

INK, DEEP, BASE, LIGHT, GLINT, CORE, ACCENT, HAZE = 1, 2, 3, 4, 5, 6, 7, 8
# A stroke's cross-section from its centreline out: the share of the half-width each band ends at.
STROKE_BANDS = ((0.22, CORE), (0.45, LIGHT), (0.72, BASE), (1.0, DEEP))
SOFT_BANDS = ((0.35, LIGHT), (0.7, BASE), (1.0, DEEP))       # no white core: dust, cloud, water bodies
GLOW_BANDS = ((0.3, GLINT), (0.6, LIGHT), (1.0, BASE))       # a glow: pale centre, no rim


def px_hash(*args) -> float:
    """Deterministic 0..1 from integers (the scatter's variety)."""
    h = 2166136261
    for a in args:
        h ^= (int(a) * 2654435761) & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= h >> 13
    return ((h * 0x9E3779B1) & 0xFFFFFFFF) / 4294967296.0


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 1.0 - (1.0 - t) * (1.0 - t)


def ease_in(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t


class Canvas:
    """One FX frame at art resolution. x right, y down; pixel (i, j) covers [i, i+1) x [j, j+1)."""

    def __init__(self, w: int, h: int):
        self.w, self.h = int(w), int(h)
        self.idx = np.zeros((self.h, self.w), np.uint8)
        ys, xs = np.mgrid[0:self.h, 0:self.w]
        self.X = xs.astype(np.float32) + 0.5
        self.Y = ys.astype(np.float32) + 0.5

    # ---------------------------------------------------------------- painting
    def paint(self, mask: np.ndarray, idx: int, mode: str = "over") -> None:
        """Set `idx` where `mask`: over (replace), under (only on empty), max (brighter wins, for glows), dither
        (under, on a checkerboard: a half-there haze)."""
        if mode == "dither":
            mask = mask & (((self.X.astype(int) + self.Y.astype(int)) % 2) == 0)
            mode = "under"
        if mode == "over":
            self.idx[mask] = idx
        elif mode == "under":
            self.idx[mask & (self.idx == 0)] = idx
        elif mode == "max":
            cur = self.idx[mask]
            self.idx[mask] = np.where(cur < idx, idx, cur)

    def bands(self, dist: np.ndarray, half: np.ndarray | float, table=STROKE_BANDS, mode: str = "over") -> None:
        """Paint the bands of a stroke from a distance field and a half-width (a scalar or a per-pixel array)."""
        half_arr = np.broadcast_to(np.asarray(half, np.float32), dist.shape)
        inside = (dist <= half_arr) & (half_arr > 0.25)
        if not inside.any():
            return
        rel = np.where(inside, dist / np.maximum(half_arr, 1e-3), 9.0)
        # paint the outer band first so the inner ones sit on top
        for share, idx in table[::-1]:
            m = inside & (rel <= share)
            self.paint(m, idx, mode)

    # ---------------------------------------------------------------- distance fields
    def seg(self, p0, p1):
        """Distance to a segment and the parameter t (0 at p0, 1 at p1) of the nearest point."""
        x0, y0 = p0
        x1, y1 = p1
        dx, dy = x1 - x0, y1 - y0
        l2 = dx * dx + dy * dy
        if l2 < 1e-6:
            return np.hypot(self.X - x0, self.Y - y0), np.zeros_like(self.X)
        t = ((self.X - x0) * dx + (self.Y - y0) * dy) / l2
        t = np.clip(t, 0.0, 1.0)
        px, py = x0 + t * dx, y0 + t * dy
        return np.hypot(self.X - px, self.Y - py), t

    def arc(self, cx, cy, r, a0, a1, sy: float = 1.0):
        """Distance to an arc of radius r (y squashed by sy) from angle a0 to a1 (radians, y down), and t along it."""
        X = self.X - cx
        Y = (self.Y - cy) / max(sy, 1e-3)
        ang = np.arctan2(Y, X)
        lo, hi = min(a0, a1), max(a0, a1)
        # unwrap into [lo, lo + 2pi)
        a = np.mod(ang - lo, 2 * math.pi) + lo
        inside = a <= hi
        rad = np.hypot(X, Y)
        # the squashed-space distance to the ring, brought back to screen px by the ellipse's local gradient, so a
        # ground ring keeps one thickness at its sides and at its near and far edges
        d_arc = np.abs(rad - r) / np.sqrt(np.cos(ang) ** 2 + (np.sin(ang) / max(sy, 1e-3)) ** 2)
        # distance to the two end points
        ex0, ey0 = cx + math.cos(a0) * r, cy + math.sin(a0) * r * sy
        ex1, ey1 = cx + math.cos(a1) * r, cy + math.sin(a1) * r * sy
        d_end = np.minimum(np.hypot(self.X - ex0, (self.Y - ey0)), np.hypot(self.X - ex1, (self.Y - ey1)))
        d = np.where(inside, d_arc, d_end)
        t = np.clip((a - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
        if a0 > a1:
            t = 1.0 - t
        return d, t

    def polyline(self, pts):
        """Distance to a polyline and t along its length."""
        best = None
        best_t = None
        total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) or 1.0
        run = 0.0
        for i in range(len(pts) - 1):
            d, t = self.seg(pts[i], pts[i + 1])
            seg_len = math.dist(pts[i], pts[i + 1])
            tt = (run + t * seg_len) / total
            if best is None:
                best, best_t = d, tt
            else:
                take = d < best
                best = np.where(take, d, best)
                best_t = np.where(take, tt, best_t)
            run += seg_len
        return best, best_t

    # ---------------------------------------------------------------- strokes
    def stroke_seg(self, p0, p1, w0: float, w1: float, table=STROKE_BANDS, mode="over") -> None:
        d, t = self.seg(p0, p1)
        self.bands(d, lerp(w0, w1, t) * 0.5, table, mode)

    def stroke_arc(self, cx, cy, r, a0, a1, w0: float, w1: float, sy: float = 1.0, table=STROKE_BANDS, mode="over") -> None:
        d, t = self.arc(cx, cy, r, a0, a1, sy)
        self.bands(d, lerp(w0, w1, t) * 0.5, table, mode)

    def stroke_poly(self, pts, w0: float, w1: float, table=STROKE_BANDS, mode="over") -> None:
        d, t = self.polyline(pts)
        self.bands(d, lerp(w0, w1, t) * 0.5, table, mode)

    def disc(self, cx, cy, r, table=GLOW_BANDS, mode="over", sy: float = 1.0) -> None:
        d = np.hypot(self.X - cx, (self.Y - cy) / max(sy, 1e-3))
        self.bands(d, float(r), table, mode)

    def ring(self, cx, cy, r, w: float, idx: int = LIGHT, sy: float = 1.0, mode="over", a0=0.0, a1=2 * math.pi) -> None:
        """A thin ring (one tone) of radius r, w px thick, y squashed by sy."""
        if a0 == 0.0 and a1 == 2 * math.pi:
            X, Y = self.X - cx, (self.Y - cy) / max(sy, 1e-3)
            ang = np.arctan2(Y, X)
            d = np.abs(np.hypot(X, Y) - r) / np.sqrt(np.cos(ang) ** 2 + (np.sin(ang) / max(sy, 1e-3)) ** 2)
        else:
            d, _ = self.arc(cx, cy, r, a0, a1, sy)
        self.paint(d <= w * 0.5, idx, mode)

    # ---------------------------------------------------------------- masks (PIL)
    def mask_polygon(self, pts) -> np.ndarray:
        im = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        return np.array(im) > 0

    def mask_ellipse(self, cx, cy, rx, ry) -> np.ndarray:
        return ((self.X - cx) / max(rx, 1e-3)) ** 2 + ((self.Y - cy) / max(ry, 1e-3)) ** 2 <= 1.0

    def polygon(self, pts, idx: int, mode="over") -> None:
        self.paint(self.mask_polygon(pts), idx, mode)

    def shaded_polygon(self, pts, light_from=(-0.6, -0.8), table=((0.35, LIGHT), (0.75, BASE), (1.0, DEEP)), mode="over") -> None:
        """A solid shape lit from the upper left: bands by the position along the light direction."""
        m = self.mask_polygon(pts)
        if not m.any():
            return
        lx, ly = light_from
        proj = self.X * lx + self.Y * ly
        vals = proj[m]
        lo, hi = float(vals.min()), float(vals.max())
        rel = 1.0 - (proj - lo) / max(hi - lo, 1e-3)   # 0 at the lit edge, 1 at the far edge
        prev = 0.0
        for share, idx in table:
            self.paint(m & (rel >= prev) & (rel <= share), idx, mode)
            prev = share

    # ---------------------------------------------------------------- pixels
    def dot(self, x, y, idx: int, size: int = 1, mode="over") -> None:
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        if size <= 1:
            if 0 <= x0 < self.w and 0 <= y0 < self.h:
                if mode == "over" or self.idx[y0, x0] == 0 or (mode == "max" and self.idx[y0, x0] < idx):
                    self.idx[y0, x0] = idx
            return
        for j in range(size):
            for i in range(size):
                xx, yy = x0 - size // 2 + i, y0 - size // 2 + j
                if 0 <= xx < self.w and 0 <= yy < self.h:
                    if mode == "over" or self.idx[yy, xx] == 0 or (mode == "max" and self.idx[yy, xx] < idx):
                        self.idx[yy, xx] = idx

    def plus(self, x, y, idx: int, arm: int = 1) -> None:
        """A star glint: a plus of `arm` px arms."""
        for k in range(-arm, arm + 1):
            self.dot(x + k, y, idx)
            self.dot(x, y + k, idx)

    def line1(self, p0, p1, idx: int) -> None:
        """1 px Bresenham line."""
        x0, y0 = int(math.floor(p0[0])), int(math.floor(p0[1]))
        x1, y1 = int(math.floor(p1[0])), int(math.floor(p1[1]))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.dot(x0, y0, idx)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def stamp(self, rows, x, y, table: dict) -> None:
        """ASCII pixel art: each char of `table` maps to an index; '.' or ' ' is empty."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in table:
                    self.dot(x + i, y + j, table[ch])

    # ---------------------------------------------------------------- whole-frame ops
    def rim(self, idx: int = INK, of=(DEEP, BASE, LIGHT, GLINT, CORE, ACCENT)) -> None:
        """A 1 px rim of `idx` around every pixel of the tones in `of` (4-connected), on empty pixels only."""
        body = np.isin(self.idx, of)
        grown = body.copy()
        grown[1:, :] |= body[:-1, :]
        grown[:-1, :] |= body[1:, :]
        grown[:, 1:] |= body[:, :-1]
        grown[:, :-1] |= body[:, 1:]
        self.idx[grown & (self.idx == 0)] = idx

    def clean(self) -> None:
        """Remove orphan pixels (no 4-neighbour of any tone), the pixel-art rule."""
        body = self.idx > 0
        n = np.zeros_like(body)
        n[1:, :] |= body[:-1, :]
        n[:-1, :] |= body[1:, :]
        n[:, 1:] |= body[:, :-1]
        n[:, :-1] |= body[:, 1:]
        self.idx[body & ~n] = 0

    def flip_x(self) -> None:
        self.idx = self.idx[:, ::-1].copy()

    def ghost(self, other: "Canvas", idx: int = DEEP, dx: int = 0, dy: int = 0, dither: bool = True) -> None:
        """Paint the silhouette of another frame's solid tones, shifted, in one tone under what is drawn (Time's
        echo); dithered to a checkerboard so it reads as half there. Haze and deep pixels leave no echo."""
        src = np.isin(other.idx, (BASE, LIGHT, GLINT, CORE, ACCENT))
        dst = np.zeros_like(src)
        h, w = src.shape
        xs = slice(max(0, dx), min(w, w + dx))
        xd = slice(max(0, -dx), min(w, w - dx))
        ys = slice(max(0, dy), min(h, h + dy))
        yd = slice(max(0, -dy), min(h, h - dy))
        dst[ys, xs] = src[yd, xd]
        if dither:
            yy, xx = np.mgrid[0:h, 0:w]
            dst &= ((xx + yy) % 2) == 0
        self.idx[dst & (self.idx == 0)] = idx

    def figure(self, x: float, y: float, h: float, idx: int, lean: float = 0.0, dither: bool = True) -> None:
        """A ghost of a standing figure `h` tall with its feet at (x, y): a head and a leaning body, one tone,
        dithered (the afterimages of a dash or a blink)."""
        head_r = h * 0.11
        hx, hy = x + lean * h * 0.5, y - h + head_r
        m = self.mask_ellipse(hx, hy, head_r, head_r)
        body = self.mask_polygon([(x - h * 0.14 + lean * h * 0.4, y - h * 0.78), (x + h * 0.14 + lean * h * 0.4, y - h * 0.78),
                                  (x + h * 0.12, y), (x - h * 0.12, y)])
        m |= body
        if dither:
            m &= ((self.X.astype(int) + self.Y.astype(int)) % 2) == 0
        self.paint(m, idx, "under")


def upscale(img: np.ndarray, k: int = 2) -> np.ndarray:
    return np.repeat(np.repeat(img, k, axis=0), k, axis=1)
