"""Shared helpers for the batch-B creature modules (bamboo_monkey ... riverbed_serpent).

Small, deterministic drawing helpers on top of ``pixel.py`` that several of these
creatures need: expressive eye stamps, water ripples / wakes, sprays and paper strips.
Nothing here changes ``pixel.py`` behaviour.
"""
from __future__ import annotations

import math

import pixel as px

# ---- eyes -------------------------------------------------------------------------------
# Right-facing stamps, top-left anchored.  k ink, g glint, i iris, r glow ring.
EYE2 = {
    "open": ["gi", "ik"],
    "angry": ["gi", "ik"],
    "squeeze": ["k.", ".k", "k."],
    "closed": ["kk"],
    "dead": ["k.k", ".k.", "k.k"],
}
EYE3 = {
    "open": ["gii", "iik", "iik"],
    "angry": ["gii", "iik", "iik"],
    "squeeze": ["kk.", "..k", "kk."],
    "closed": ["...", "kkk"],
    "dead": ["k.k", ".k.", "k.k"],
}


def eye(cv, ex, ey, state="open", iris=None, size=2, brow=None, ink=px.INK, glint=px.GLINT,
        name="eye"):
    """Stamp a small expressive eye at top-left pixel (ex, ey).

    ``brow`` colours the angry brow (defaults to ink).  The squeeze / dead stamps are
    positioned so that they stay centred on the open eye."""
    ex, ey = int(round(ex)), int(round(ey))
    iris = iris if iris is not None else ink
    pal = {"k": ink, "g": glint, "i": iris}
    table = EYE2 if size == 2 else EYE3
    rows = table[state]
    if state == "dead":
        cv.stamp(rows, ex - 1 + (size == 3), ey - 1 + (size == 3), pal, name=name)
    elif state == "squeeze":
        cv.stamp(rows, ex, ey - (1 if size == 2 else 0), pal, name=name)
    elif state == "closed":
        cv.stamp(rows, ex, ey + (1 if size == 2 else 0), pal, name=name)
    else:
        cv.stamp(rows, ex, ey, pal, name=name)
        if state == "angry":  # brow slants down toward the snout
            b = brow if brow is not None else ink
            pts = [(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1)]
            if size == 3:
                pts = [(ex - 1, ey - 2), (ex, ey - 2), (ex + 1, ey - 1), (ex + 2, ey - 1), (ex + 3, ey)]
            cv.pixels(pts, b, name="brow")


# ---- water ------------------------------------------------------------------------------
def ripple(cv, cx, y, w, mat=px.WATER_FX, thick=1.0, name="ripple"):
    """Flat water ripple ring (an ellipse outline with a lighter front lip) centred on
    (cx, y).  ``w`` is the half width.  Draw on an outlined FX layer."""
    h = max(1.0, w * 0.22) * thick
    outer = cv.mask_ellipse(cx, y, w, h)
    inner = cv.mask_ellipse(cx, y - 0.35, max(0.5, w - 1.6), max(0.4, h - 0.9))
    ring = outer & ~inner
    cv.fill(ring, mat, normals=(cv.X * 0, (cv.Y - y) * 0 - 1.0, cv.X * 0 + 0.5), shade="soft", name=name)


def spray(cv, x, y, t, size=1.0, spread=1.0, mat=px.WATER_FX, n=5, seed=0, name="spray"):
    """Fan of droplets thrown up from (x, y) for life ``t`` in [0, 1]."""
    if t < 0 or t > 1:
        return
    for i in range(n):
        a = math.radians(55 + (i / max(1, n - 1) - 0.5) * 110 * spread + (px.hash01(seed, i) - 0.5) * 16)
        v = (4.0 + 3.0 * px.hash01(seed, i, 1)) * size
        tt = t * 1.25
        dx = math.cos(a) * v * tt * 1.4
        dy = -(math.sin(a) * v * tt * 1.6 - 6.0 * tt * tt * size)
        r = max(0.6, (1.2 - 0.6 * t) * size * (1.0 if i % 2 else 0.8))
        cv.circle(x + dx, y + dy, r, mat, shade="soft", name=name)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


# ---- curves and tubes (snakes, eels, tails) ----------------------------------------------------
def catmull(points, samples=6):
    """Centripetal-ish Catmull-Rom through ``points`` -> dense list of points."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out


def resample(points, step=1.5):
    """Points spaced ``step`` apart along a polyline (first and last kept)."""
    out = [points[0]]
    acc = 0.0
    for a, b in zip(points, points[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg < 1e-9:
            continue
        t = (step - acc) / seg
        while t <= 1.0:
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            t += step / seg
        acc = (acc + seg) % step
    if math.hypot(out[-1][0] - points[-1][0], out[-1][1] - points[-1][1]) > step * 0.3:
        out.append(points[-1])
    return out


def path_length(points):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def belly_normals(points, toward=(0.45, 1.0), smooth=2):
    """Unit normals of a path, each flipped to face ``toward`` (default: down + forward),
    lightly smoothed so the belly side never flips from one sample to the next."""
    n = len(points)
    raw = []
    for i in range(n):
        a = points[max(0, i - 1)]
        b = points[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        if nx * toward[0] + ny * toward[1] < 0:
            nx, ny = -nx, -ny
        raw.append((nx, ny))
    out = []
    for i in range(n):
        sx = sum(raw[j][0] for j in range(max(0, i - smooth), min(n, i + smooth + 1)))
        sy = sum(raw[j][1] for j in range(max(0, i - smooth), min(n, i + smooth + 1)))
        ln = math.hypot(sx, sy) or 1.0
        out.append((sx / ln, sy / ln))
    return out


def taper(n, r_tail, r_mid, r_head, mid_at=0.55, head_at=1.0):
    """Radii for n samples from tail tip (index 0) to head end: tail -> fat middle -> neck."""
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        if t <= mid_at:
            u = t / mid_at
            r = r_tail + (r_mid - r_tail) * math.sin(u * math.pi / 2)
        else:
            u = (t - mid_at) / max(1e-6, head_at - mid_at)
            r = r_mid + (r_head - r_mid) * u
        out.append(r)
    return out


def offset(points, normals, radii, k):
    """Points displaced along their normals by ``k * radius``."""
    return [(p[0] + n[0] * r * k, p[1] + n[1] * r * k) for p, n, r in zip(points, normals, radii)]
