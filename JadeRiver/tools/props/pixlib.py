"""Deterministic pixel-art toolkit shared by the prop, tile and UI generators.

Everything is drawn on a small "art pixel" canvas (numpy RGB + alpha) using
boolean masks, cluster shading from a bevel height field (light from the upper
left), hue-shifted ramps and dark selective outlines. Nothing here uses
anti-aliasing or random state that is not seeded from a stable string.
"""
from __future__ import annotations

import math
import zlib

import numpy as np
from PIL import Image, ImageDraw

SCALE = 2  # native pixel scale: one art pixel = 2x2 screen pixels


# ---------------------------------------------------------------- colours
def hexc(h: str):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def ramp(*hexes):
    return [hexc(h) for h in hexes]


def seed_of(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0xFFFFFFFF


def rng(*parts):
    return np.random.default_rng(seed_of(*parts))


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.float64)
        self.a = np.zeros((h, w), np.float64)  # 0..1

    # -- basic access
    @property
    def solid(self):
        return self.a > 0.999

    @property
    def mask(self):
        return self.a > 0.0

    def copy(self):
        c = Canvas(self.w, self.h)
        c.rgb = self.rgb.copy()
        c.a = self.a.copy()
        return c

    def empty(self):
        return np.zeros((self.h, self.w), bool)

    def put(self, x, y, c, a=1.0):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.blend_px(x, y, c, a)

    def blend_px(self, x, y, c, a):
        if a >= 1.0:
            self.rgb[y, x] = c
            self.a[y, x] = 1.0
            return
        oa = self.a[y, x]
        na = a + oa * (1 - a)
        if na <= 0:
            return
        self.rgb[y, x] = (np.array(c, float) * a + self.rgb[y, x] * oa * (1 - a)) / na
        self.a[y, x] = na

    def fill(self, m, c, a=1.0):
        """Paint colour c into mask m (alpha a composited over)."""
        m = m & True
        if a >= 1.0:
            self.rgb[m] = c
            self.a[m] = 1.0
            return
        oa = self.a[m]
        na = a + oa * (1 - a)
        col = np.array(c, float)
        self.rgb[m] = (col * a + self.rgb[m] * (oa * (1 - a))[:, None]) / np.maximum(na, 1e-9)[:, None]
        self.a[m] = na

    def fill_idx(self, m, idx, pal):
        pal = np.array(pal, float)
        idx = np.clip(idx, 0, len(pal) - 1).astype(int)
        self.rgb[m] = pal[idx[m]]
        self.a[m] = 1.0

    def erase(self, m):
        self.a[m] = 0.0

    def light(self, m, c, a):
        """Additive-ish light: brightens solid pixels, adds translucent colour on empty ones."""
        col = np.array(c, float)
        solid = m & (self.a > 0)
        self.rgb[solid] = np.clip(self.rgb[solid] + (col - self.rgb[solid] * 0.35) * a, 0, 255)
        empty = m & (self.a <= 0)
        self.rgb[empty] = col
        self.a[empty] = a

    def paste(self, other: "Canvas", dx=0, dy=0):
        """Alpha composite other over self at offset."""
        sx0, sy0 = max(0, -dx), max(0, -dy)
        sx1, sy1 = min(other.w, self.w - dx), min(other.h, self.h - dy)
        if sx1 <= sx0 or sy1 <= sy0:
            return
        sa = other.a[sy0:sy1, sx0:sx1]
        sc = other.rgb[sy0:sy1, sx0:sx1]
        ta = self.a[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx]
        tc = self.rgb[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx]
        na = sa + ta * (1 - sa)
        nc = (sc * sa[..., None] + tc * (ta * (1 - sa))[..., None]) / np.maximum(na, 1e-9)[..., None]
        upd = sa > 0
        tc[upd] = nc[upd]
        ta[upd] = na[upd]

    def shifted(self, dx, dy):
        c = Canvas(self.w, self.h)
        c.paste(self, dx, dy)
        return c

    def flipped(self):
        c = Canvas(self.w, self.h)
        c.rgb = self.rgb[:, ::-1].copy()
        c.a = self.a[:, ::-1].copy()
        return c

    def color_at(self, x, y):
        return tuple(int(round(v)) for v in self.rgb[y, x])

    # -- export
    def to_rgba(self, scale=SCALE, opaque=False):
        rgb = np.clip(np.round(self.rgb), 0, 255).astype(np.uint8)
        # quantise alpha to 1/255 steps deterministically
        a = np.clip(np.round(self.a * 255), 0, 255).astype(np.uint8)
        if opaque:
            a[:] = 255
        rgb[a == 0] = 0
        arr = np.dstack([rgb, a])
        if scale != 1:
            arr = arr.repeat(scale, 0).repeat(scale, 1)
        return arr

    def image(self, scale=SCALE, opaque=False):
        return Image.fromarray(self.to_rgba(scale, opaque), "RGBA")


# ---------------------------------------------------------------- masks
def grid(w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    return xx, yy


def m_rect(w, h, x0, y0, x1, y1):
    """Inclusive rectangle mask."""
    m = np.zeros((h, w), bool)
    x0, x1 = max(0, int(x0)), min(w - 1, int(x1))
    y0, y1 = max(0, int(y0)), min(h - 1, int(y1))
    if x1 >= x0 and y1 >= y0:
        m[y0:y1 + 1, x0:x1 + 1] = True
    return m


def m_ellipse(w, h, cx, cy, rx, ry):
    xx, yy = grid(w, h)
    rx = max(rx, 0.5)
    ry = max(ry, 0.5)
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0


def m_poly(w, h, pts):
    im = Image.new("1", (w, h), 0)
    ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=1, outline=1)
    return np.array(im, bool)


def m_line(w, h, pts, width=1):
    im = Image.new("1", (w, h), 0)
    d = ImageDraw.Draw(im)
    pts = [(int(round(x)), int(round(y))) for x, y in pts]
    if width <= 1:
        for i in range(len(pts) - 1):
            _bres(d, pts[i], pts[i + 1])
        if len(pts) == 1:
            d.point(pts[0], fill=1)
    else:
        d.line(pts, fill=1, width=int(width))
    return np.array(im, bool)


def _bres(d, p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        d.point((x0, y0), fill=1)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def m_curve(w, h, pts, steps=None, width=1):
    """Catmull-Rom through points, rasterised as 1px pixel line."""
    if len(pts) < 3:
        return m_line(w, h, pts, width)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = steps or max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * 1.5))
        for s in range(seg):
            t = s / seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return m_line(w, h, out, width)


def shift(m, dx, dy, fill=False):
    h, w = m.shape
    out = np.full_like(m, fill)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    if xs1 > xs0 and ys1 > ys0:
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return out


def wshift(m, dx, dy):
    """Wrapping shift (for seamless tiles)."""
    return np.roll(np.roll(m, dy, 0), dx, 1)


def erode(m, wrap=False):
    s = wshift if wrap else shift
    return m & s(m, 1, 0) & s(m, -1, 0) & s(m, 0, 1) & s(m, 0, -1)


def dilate(m, wrap=False, diag=False):
    s = wshift if wrap else shift
    o = m | s(m, 1, 0) | s(m, -1, 0) | s(m, 0, 1) | s(m, 0, -1)
    if diag:
        o |= s(m, 1, 1) | s(m, -1, 1) | s(m, 1, -1) | s(m, -1, -1)
    return o


def border(m, wrap=False):
    return m & ~erode(m, wrap)


def top_edge(m):
    return m & ~shift(m, 0, 1)


def bottom_edge(m):
    return m & ~shift(m, 0, -1)


def left_edge(m):
    return m & ~shift(m, 1, 0)


def right_edge(m):
    return m & ~shift(m, -1, 0)


def depth_from_top(m):
    """Number of contiguous mask pixels above each pixel (0 on the top edge)."""
    h, w = m.shape
    d = np.zeros((h, w), int)
    for y in range(1, h):
        d[y] = np.where(m[y] & m[y - 1], d[y - 1] + 1, 0)
    return d


def bbox(m):
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return 0, 0, 0, 0
    return xs.min(), ys.min(), xs.max(), ys.max()


# ---------------------------------------------------------------- noise
def vnoise(w, h, cell, seed, octaves=1, wrap=False):
    """Smooth value noise in [0,1]. With wrap=True it tiles on w x h (cell must divide)."""
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    g = np.random.default_rng(seed)
    c = float(cell)
    for _ in range(octaves):
        gw = int(math.ceil(w / c)) + (0 if wrap else 2)
        gh = int(math.ceil(h / c)) + (0 if wrap else 2)
        gv = g.random((gh, gw))
        xx, yy = grid(w, h)
        fx = xx / c
        fy = yy / c
        x0 = np.floor(fx).astype(int)
        y0 = np.floor(fy).astype(int)
        tx = fx - x0
        ty = fy - y0
        tx = tx * tx * (3 - 2 * tx)
        ty = ty * ty * (3 - 2 * ty)
        if wrap:
            x1 = (x0 + 1) % gw
            y1 = (y0 + 1) % gh
            x0 %= gw
            y0 %= gh
        else:
            x1 = x0 + 1
            y1 = y0 + 1
        v = (gv[y0, x0] * (1 - tx) * (1 - ty) + gv[y0, x1] * tx * (1 - ty)
             + gv[y1, x0] * (1 - tx) * ty + gv[y1, x1] * tx * ty)
        total += v * amp
        norm += amp
        amp *= 0.5
        c /= 2
    return total / norm


# ---------------------------------------------------------------- shading
LIGHT = np.array([-0.55, -0.75, 0.85])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def dist_in(m, R, wrap=False):
    d = np.zeros(m.shape, float)
    cur = m.copy()
    for _ in range(R):
        d += cur
        cur = erode(cur, wrap)
        if not cur.any():
            break
    return d


def height_bevel(m, R, profile="round", wrap=False):
    d = dist_in(m, R, wrap) / float(R)
    if profile == "round":
        return np.sqrt(np.clip(1 - (1 - d) ** 2, 0, 1))
    if profile == "lin":
        return d
    if profile == "dome":
        return np.sqrt(np.clip(d, 0, 1))
    return d


def cyl_normals(m, axis="v"):
    """Per-row (axis v) or per-column (axis h) cylinder normals."""
    h, w = m.shape
    nx = np.zeros((h, w))
    ny = np.zeros((h, w))
    if axis == "v":
        for y in range(h):
            xs = np.nonzero(m[y])[0]
            if len(xs) == 0:
                continue
            x0, x1 = xs.min(), xs.max()
            c = (x0 + x1) / 2.0
            r = max((x1 - x0) / 2.0 + 0.5, 0.5)
            nx[y, x0:x1 + 1] = (np.arange(x0, x1 + 1) - c) / r
    else:
        for x in range(w):
            ys = np.nonzero(m[:, x])[0]
            if len(ys) == 0:
                continue
            y0, y1 = ys.min(), ys.max()
            c = (y0 + y1) / 2.0
            r = max((y1 - y0) / 2.0 + 0.5, 0.5)
            ny[y0:y1 + 1, x] = (np.arange(y0, y1 + 1) - c) / r
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0.02, 1))
    return nx, ny, nz


def intensity(m, mode="bevel", R=3, strength=2.5, profile="round", wrap=False, normal=None):
    """Lambert intensity per pixel, rescaled so a flat face facing the viewer = 0."""
    if mode == "flat":
        return np.zeros(m.shape)
    if mode in ("cyl", "cylh"):
        nx, ny, nz = cyl_normals(m, "v" if mode == "cyl" else "h")
    elif mode == "sphere":
        x0, y0, x1, y1 = bbox(m)
        xx, yy = grid(m.shape[1], m.shape[0])
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = max((x1 - x0) / 2 + .5, .5), max((y1 - y0) / 2 + .5, .5)
        nx = (xx - cx) / rx
        ny = (yy - cy) / ry
        nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0.02, 1))
    else:
        hgt = height_bevel(m, R, profile, wrap) * strength
        if wrap:
            gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / 2
            gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / 2
        else:
            gy, gx = np.gradient(hgt)
        # normal of a height field: (-dh/dx, -dh/dy, 1)
        nx, ny, nz = -gx, -gy, np.ones(m.shape)
    if normal is not None:
        nx = nx + normal[0]
        ny = ny + normal[1]
    n = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    I = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / n
    return I - LIGHT[2]


def despeckle(idx, m, passes=1):
    """Replace isolated single pixels by their neighbours' shared value."""
    idx = idx.copy()
    h, w = idx.shape
    for _ in range(passes):
        up = np.roll(idx, 1, 0)
        dn = np.roll(idx, -1, 0)
        lf = np.roll(idx, 1, 1)
        rt = np.roll(idx, -1, 1)
        mu = np.roll(m, 1, 0)
        md = np.roll(m, -1, 0)
        ml = np.roll(m, 1, 1)
        mr = np.roll(m, -1, 1)
        # neighbours inside mask
        same_ud = (up == dn) & mu & md
        same_lr = (lf == rt) & ml & mr
        lone = m & (idx != up) & (idx != dn) & (idx != lf) & (idx != rt)
        fix = lone & (same_ud | same_lr)
        idx[fix & same_ud] = up[fix & same_ud]
        idx[fix & ~same_ud & same_lr] = lf[fix & ~same_ud & same_lr]
    return idx


def shade_idx(m, n, mode="bevel", R=3, strength=2.5, base=0.5, gain=1.6, profile="round",
              noise=None, namp=0.0, ao=0.0, top=0.0, wrap=False, clean=True, normal=None, bias=None):
    I = intensity(m, mode, R, strength, profile, wrap, normal)
    v = base + I * gain
    if noise is not None:
        v = v + (noise - 0.5) * namp
    if bias is not None:
        v = v + bias
    if ao or top:
        x0, y0, x1, y1 = bbox(m)
        hh = max(1, y1 - y0)
        yy = np.mgrid[0:m.shape[0], 0:m.shape[1]][0]
        t = np.clip((yy - y0) / hh, 0, 1)
        v = v - ao * t ** 2 + top * (1 - t) ** 2
    idx = np.clip(np.floor(v * n), 0, n - 1).astype(int)
    if clean:
        idx = despeckle(idx, m)
    return idx


def shade(cv: Canvas, m, pal, contour=False, contour_c=None, **kw):
    """Shade mask m with ramp pal (dark->light) onto canvas.

    contour=True darkens the pixels of m that touch previously painted pixels
    (internal part separation lines)."""
    m = m.copy()
    if not m.any():
        return m
    prev = cv.solid.copy()
    idx = shade_idx(m, len(pal), **kw)
    cv.fill_idx(m, idx, pal)
    if contour:
        touch = m & (shift(prev & ~m, 1, 0) | shift(prev & ~m, -1, 0) | shift(prev & ~m, 0, 1) | shift(prev & ~m, 0, -1))
        cv.fill(touch, contour_c or pal[0])
    return m


def inner_line(cv, m, c, sides="all"):
    """Darken the inner edge of mask m (bottom/right or all)."""
    if sides == "all":
        e = border(m)
    elif sides == "br":
        e = bottom_edge(m) | right_edge(m)
    elif sides == "b":
        e = bottom_edge(m)
    elif sides == "tl":
        e = top_edge(m) | left_edge(m)
    else:
        e = border(m)
    cv.fill(e & m, c)


INK = hexc("#071015")


def outline(cv: Canvas, ink=INK, t=0.72, diag=False, only_solid=True, skip=None, close_edges=True):
    """Dark hue-aware outline around the opaque silhouette.

    close_edges: solid pixels on the canvas border are darkened in place, so a shape
    that touches the frame edge still reads as outlined instead of clipped."""
    src = cv.a > 0.999 if only_solid else cv.a > 0
    out = dilate(src, diag=diag) & ~src
    if skip is not None:
        out &= ~skip
    h, w = src.shape
    lumv = cv.rgb @ np.array([0.299, 0.587, 0.114])
    best = np.full((h, w), 1e9)
    col = np.zeros((h, w, 3))
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (-1, 1), (1, -1), (-1, -1)] if diag else [])
    for dx, dy in dirs:
        ms = shift(src, dx, dy)
        ls = np.roll(np.roll(lumv, dy, 0), dx, 1)
        cs = np.roll(np.roll(cv.rgb, dy, 0), dx, 1)
        better = ms & (ls < best)
        best = np.where(better, ls, best)
        col[better] = cs[better]
    inkv = np.array(ink, float)
    res = col * (1 - t) + inkv * t
    # keep existing translucent pixels underneath: outline is opaque
    cv.rgb[out] = res[out]
    cv.a[out] = 1.0
    if close_edges:
        e = np.zeros_like(src)
        e[0, :] |= src[0, :]
        e[-1, :] |= src[-1, :]
        e[:, 0] |= src[:, 0]
        e[:, -1] |= src[:, -1]
        cv.rgb[e] = cv.rgb[e] * (1 - t) + np.array(ink, float) * t
    return out


# ---------------------------------------------------------------- small helpers
def ellipse_ring(w, h, cx, cy, rx, ry):
    a = m_ellipse(w, h, cx, cy, rx, ry)
    return a & ~erode(a)


def sparkle(cv, x, y, size, c_core, c_arm, a=1.0):
    """4-point star glint."""
    cv.put(x, y, c_core, a)
    for i in range(1, size + 1):
        col = c_arm if i < size else c_arm
        aa = a if i < size else a * 0.7
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            cv.put(x + dx, y + dy, col, aa)


def glow(cv, cx, cy, rx, ry, c, steps=((1.0, 0.18), (0.72, 0.26), (0.45, 0.34)), m_limit=None):
    """Stepped radial light (no blur): concentric flat ellipses."""
    for s, a in steps:
        m = m_ellipse(cv.w, cv.h, cx, cy, rx * s, ry * s)
        if m_limit is not None:
            m &= m_limit
        cv.light(m, c, a)


def save_png(img: Image.Image, path):
    img.save(path, format="PNG", optimize=False, compress_level=9)
