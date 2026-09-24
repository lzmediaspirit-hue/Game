"""Shared helpers for creature batch C (pets, birds, spirits, Hollow beasts, bosses).

Everything here builds on :mod:`pixel` and stays deterministic (no randomness; use
:func:`pixel.hash01` for variety).  FX helpers draw on a layer from ``cv.layer()``.
"""
from __future__ import annotations

import math

import numpy as np

import pixel as px

# ---- shared FX materials ----------------------------------------------------------------------
MIST = px.material("mist", "#f2f6f4", "#cfdade", "#a4b4bc", "#7d8e98", outline="#3c4a54")
HOLLOW_MIST = px.material("hollow_mist", "#eef2ef", "#c9d1d2", "#9aa6ab", "#707d84", outline="#2e383e")
EMBER = px.material("ember", "#fff1b8", "#ffc85a", "#f07a32", "#b8402c", outline="#3a1210")
SPARK_Y = px.rgb("#ffe36a")
SPARK_W = px.rgb("#fffbe6")
BOLT = px.rgb("#fff4a8")
BOLT_EDGE = px.rgb("#f2b92e")
WIND = px.rgb("#eef8fb")
WIND_DIM = px.rgb("#a9c6d6")
SOUL_GLOW = px.rgb("#d9c6f5")
SOUL_CORE = px.rgb("#fbf6ff")


def eye_stamp(cv, rows, x, y, pal, name="eye"):
    """Stamp an eye pattern (``k`` ink, ``g`` glint, ``i`` iris, ``w`` white, custom keys)."""
    base = {"k": px.INK, "g": px.GLINT, "w": px.EYE_WHITE}
    base.update(pal)
    return cv.stamp(rows, x, y, base, name=name)


def sparks(fx, cx, cy, t, n=5, radius=6.0, colors=(SPARK_W, SPARK_Y), seed=0, spread=360.0, aim=90.0,
           length=2):
    """Short 2-pixel spark streaks flying out of (cx, cy) for life ``t`` in [0, 1].

    Each spark is a tiny line (bright head + tinted tail) so it never counts as a stray
    pixel.  ``aim``/``spread`` restrict the burst direction (deg, 90 = up)."""
    if t < 0 or t > 1:
        return
    for i in range(n):
        h = px.hash01(seed, i)
        a = aim - spread / 2 + spread * ((i + 0.5 * h) / n)
        r = radius * (0.35 + 0.75 * t) * (0.7 + 0.5 * px.hash01(seed, i, 7))
        head = px.polar((cx, cy), a, r)
        tail = px.polar((cx, cy), a, max(0.0, r - length))
        hx, hy = math.floor(head[0]), math.floor(head[1])
        tx, ty = math.floor(tail[0]), math.floor(tail[1])
        if (hx, hy) == (tx, ty):
            tx -= 1
        fx.line((tx, ty), (hx, hy), colors[1], name="spark")
        fx.pixel(hx, hy, colors[0], name="spark")


def ember_specks(fx, pts, colors=(SPARK_W, SPARK_Y)):
    """Explicit 2-px embers at the given (x, y, dir) points (dir: 0 up, 1 up-left, 2 up-right)."""
    for (x, y, d) in pts:
        x, y = math.floor(x), math.floor(y)
        tail = {0: (x, y + 1), 1: (x + 1, y + 1), 2: (x - 1, y + 1)}[d]
        fx.pixel(tail[0], tail[1], colors[1], name="spark")
        fx.pixel(x, y, colors[0], name="spark")


def flame(cv, base, height, width, phase, mats, lean=0.0, name="flame", tongues=3):
    """Flickering flame rooted at ``base`` (x, y) growing upward ``height`` px.

    ``mats`` = (outer, mid, core) colours or materials, drawn as nested flat polygons.
    ``phase`` animates the tongue heights; ``lean`` tilts the tip (px per height, + right).
    """
    bx, by = base
    out = []

    def shape(h, w, k):
        steps = 6
        left, right = [], []
        for s in range(steps):
            t = s / steps
            y = by - h * t
            half = w * math.sin(math.pi * min(1.0, 0.3 + t * 0.85)) * (1 - t) ** 0.5
            wob = 0.5 * math.sin(phase * 2.1 + t * 6.0 + k) * t
            left.append((bx - half + lean * h * t * t + wob, y))
            tongue = 0.0
            if tongues and 0.3 < t < 0.8:
                tongue = 1.0 * max(0.0, math.sin(phase * 2.7 + t * 9.0 + k * 1.3))
            right.append((bx + half + tongue + lean * h * t * t + wob, y))
        tip = (bx + lean * h + 0.4 * math.sin(phase * 1.7 + k),
               by - h - 0.4 - 0.9 * (0.5 + 0.5 * math.sin(phase * 2.3 + k)))
        return left + [tip] + right[::-1]

    outer, mid, core = (m if isinstance(m, px.Material) else px.flat(m) for m in mats)
    for (fh, fw, mat, k) in ((1.0, 1.0, outer, 0.0), (0.68, 0.62, mid, 1.3), (0.4, 0.34, core, 2.1)):
        pts = shape(height * fh, width * fw, k)
        out.append(cv.polygon(pts, mat, shade="flat", name=name))
    thin_body(cv, cv.mask_of(name))  # a flame tip must never leave detached pixels
    return out


def bolt(fx, p0, p1, seed=0, jag=2.0, segs=6, core=BOLT, edge=BOLT_EDGE, fork=True):
    """Jagged lightning from p0 to p1: a 1 px bright core with a darker edge beside it."""
    pts = [p0]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    for s in range(1, segs):
        t = s / segs
        off = (px.hash01(seed, s) * 2 - 1) * jag
        pts.append((p0[0] + dx * t + nx * off, p0[1] + dy * t + ny * off))
    pts.append(p1)
    for a, b in zip(pts, pts[1:]):
        fx.line((round(a[0]) + 1, round(a[1])), (round(b[0]) + 1, round(b[1])), edge, name="bolt")
    for a, b in zip(pts, pts[1:]):
        fx.line((round(a[0]), round(a[1])), (round(b[0]), round(b[1])), core, name="bolt")
    if fork and len(pts) > 3:
        m = pts[len(pts) // 2]
        f = (m[0] + nx * jag * 2.2 + dx / segs, m[1] + ny * jag * 2.2 + dy / segs)
        fx.line((round(m[0]), round(m[1])), (round(f[0]), round(f[1])), core, name="bolt")
    return pts


def arc_line(fx, c, r, a0, a1, color, name="wind", step=4.0):
    """1 px circular arc from angle a0 to a1 (deg, 90 = up) around c."""
    n = max(2, int(abs(a1 - a0) / step))
    prev = None
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        p = px.polar(c, a, r)
        q = (math.floor(p[0]), math.floor(p[1]))
        if prev is not None and q != prev:
            fx.line(prev, q, color, name=name)
        prev = q


def wind_streak(fx, x, y, length, curl=1.0, direction=1, color=WIND, dim=WIND_DIM, name="wind"):
    """Horizontal wind line with a curl at its leading end.

    (x, y) is the tail; the line runs ``length`` px in ``direction`` then curls up."""
    x, y = round(x), round(y)
    x1 = x + direction * round(length)
    fx.line((x, y), (x1 - direction * 2, y), dim, name=name)
    fx.line((x + direction * round(length * 0.35), y), (x1, y), color, name=name)
    if curl > 0:
        r = 1.5 + curl
        c = (x1 + 0.5, y - r + 0.5)
        if direction > 0:
            arc_line(fx, c, r, -90, 150, color, name=name)
        else:
            arc_line(fx, c, r, 270, 30, color, name=name)


def mist_puff(fx, x, y, r, mat=MIST, name="mist"):
    """One lumpy mist cloud (three overlapping circles) centred at (x, y)."""
    fx.circle(x - r * 0.55, y + r * 0.2, r * 0.7, mat, shade="soft", name=name)
    fx.circle(x + r * 0.5, y + r * 0.25, r * 0.62, mat, shade="soft", name=name)
    fx.circle(x, y - r * 0.2, r * 0.8, mat, shade="soft", name=name)


def wisp(fx, x, y, length, phase, mat=MIST, width=1.2, rise=1.0, name="mist"):
    """A curling mist strand rising from (x, y), tapering to a point."""
    pts = [(x, y)]
    for s in range(1, 5):
        t = s / 4
        pts.append((x + math.sin(phase + t * 3.2) * 1.6 * t - length * 0.35 * t,
                    y - length * t * rise))
    fx.limb(pts, [width, width * 0.9, width * 0.7, width * 0.5, 0.45], mat, shade="soft", name=name)


def erase_blobs(cv, blobs):
    """Cut holes (x, y, r) out of the body (dissolve / shatter).  Returns the erased mask."""
    m = np.zeros((cv.h, cv.w), bool)
    for (x, y, r) in blobs:
        if r > 0:
            m |= cv.mask_ellipse(x, y, r, r)
    if m.any():
        cv._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(px.INK), erase=True)
    return m


def drop_specks(cv, min_size=3):
    """Remove tiny disconnected body fragments (< ``min_size`` px, 8-connectivity)."""
    f = cv.filled.copy()
    seen = np.zeros_like(f)
    h, w = f.shape
    kill = np.zeros_like(f)
    for y0 in range(h):
        for x0 in range(w):
            if f[y0, x0] and not seen[y0, x0]:
                stack = [(y0, x0)]
                comp = []
                seen[y0, x0] = True
                while stack:
                    y, x = stack.pop()
                    comp.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < h and 0 <= xx < w and f[yy, xx] and not seen[yy, xx]:
                                seen[yy, xx] = True
                                stack.append((yy, xx))
                if len(comp) < min_size:
                    for (y, x) in comp:
                        kill[y, x] = True
    if kill.any():
        cv._commit(kill, np.where(kill, 1, -1).astype(np.int8), px.flat(px.INK), erase=True)
    return kill


def thin_body(cv, within=None):
    """Clean 1-px spurs from the body mask (pixels with <= 1 filled 4-neighbour),
    optionally only inside the mask ``within``."""
    f = cv.filled
    nb = np.zeros(f.shape, np.int16)
    for dx, dy in px.N4:
        nb += px._shift(f, dx, dy, False)
    spur = f & (nb <= 1)
    if within is not None:
        spur &= within
    if spur.any():
        cv._commit(spur, np.where(spur, 1, -1).astype(np.int8), px.flat(px.INK), erase=True)
    return spur


# ---- birds ------------------------------------------------------------------------------------
def _ang_lerp(a, b, t):
    d = ((b - a + 180.0) % 360.0) - 180.0
    return a + d * t


def bird_wing(cv, S, arm_deg, hand_deg, l_arm, l_hand, chord, trail, covert, flight, tip=None, n_prim=5,
              far=False, name="wing", prim_len=1.2, fan=1.0, tip_frac=0.45, prim_r=0.24, body_sep=True,
              line=None, n_sec=4):
    """Side-view feathered wing drawn as one clean silhouette.

    ``S`` shoulder; the arm points ``arm_deg`` for ``l_arm`` px to the wrist, the hand
    ``hand_deg`` for ``l_hand`` px to the tip (deg, 0 = forward/right, 90 = up).
    ``chord`` is the feather depth; ``trail`` (+1 / -1) picks the side the feathers
    hang toward (+1: 90 deg counter-clockwise from the bone - back for a raised wing;
    -1 for a lowered wing).  ``fan`` 0..1 spreads the primaries apart.
    The flight feathers (secondaries + fingered primaries) are one shaded form with
    1 px feather lines as decals; the coverts sit on top with a separation line.
    Materials: ``covert``, ``flight``, ``tip`` (optional primary tips), ``line`` (feather
    line colour, default one tone darker than ``flight``).  Returns a dict of points.
    """
    W = px.polar(S, arm_deg, l_arm)
    T = px.polar(W, hand_deg, l_hand)
    tr_a = arm_deg + 90 * trail
    tr_h = hand_deg + 90 * trail
    shade_f = "dark" if far else "two"
    shade_c = "dark" if far else "full"
    fname = name + "_f"
    geoms = []
    # secondaries: a scalloped panel hanging off the arm
    pts = [S, W]
    for i in range(n_sec + 1):
        t = 1 - i / n_sec
        root = px.lerp_pt(S, W, t)
        ln = chord * (0.95 - 0.3 * (1 - t))
        a = _ang_lerp(tr_a, tr_h, 0.3 * t)
        pts.append(px.polar(root, a, ln + (0.7 if i % 2 == 0 else 0.0)))
    geoms.append(cv.geom_polygon(pts))
    # primaries: the outermost continues the hand's line, inner ones rotate toward the
    # trailing side and get shorter, which gives the fingered wing tip
    prims = []
    r0 = max(0.9, chord * prim_r)
    for i in range(n_prim):
        root = px.lerp_pt(T, W, min(0.92, i * 0.22))
        a = hand_deg + trail * (4 + i * 21 * (0.3 + 0.7 * fan))
        ln = chord * prim_len * (1.0 - 0.09 * i)
        tp = px.polar(root, a, ln)
        prims.append((root, tp, a))
        geoms.append(cv.geom_limb([root, px.lerp_pt(root, tp, 0.55), tp], [r0, r0 * 0.95, 0.6]))
    cv.draw_geom(cv.union(*geoms), flight, shade=shade_f, name=fname, sep=body_sep if not far else False)
    ln_mat = line if line is not None else flight.step(1)
    for i, (root, tp, a) in enumerate(prims):
        if tip is not None:
            cv.limb([px.lerp_pt(root, tp, 1 - tip_frac), tp], [r0 + 0.3, 0.9], tip, shade=shade_f, decal=True,
                    clip=fname, name=fname)
        if i > 0 and not far:  # feather line on the leading side of each inner primary
            off = a - 90 * trail
            p0 = px.polar(root, off, r0 * 0.75)
            p1 = px.polar(px.lerp_pt(root, tp, 0.85), off, 0.6)
            cv.line((round(p0[0] - 0.5), round(p0[1] - 0.5)), (round(p1[0] - 0.5), round(p1[1] - 0.5)), ln_mat,
                    band=None, decal=True, clip=fname, name=fname)
    if not far:  # secondary feather lines
        for i in range(1, n_sec):
            t = 1 - i / n_sec
            root = px.lerp_pt(S, W, t)
            q = px.polar(root, _ang_lerp(tr_a, tr_h, 0.3 * t), chord * 0.8)
            cv.line((round(root[0] - 0.5), round(root[1] - 0.5)), (round(q[0] - 0.5), round(q[1] - 0.5)), ln_mat,
                    band=None, decal=True, clip=fname, name=fname)
    # coverts over the leading edge
    cov = [S, W, T, px.polar(px.lerp_pt(W, T, 0.75), tr_h, chord * 0.42),
           px.polar(W, _ang_lerp(tr_a, tr_h, 0.5), chord * 0.55),
           px.polar(px.lerp_pt(S, W, 0.4), tr_a, chord * 0.52), px.polar(S, tr_a, chord * 0.35)]
    cg = cv.union(cv.geom_polygon(cov), cv.geom_limb([S, W, T], [max(1.0, chord * 0.22), max(0.9, chord * 0.2),
                                                                  0.8]))
    cv.draw_geom(cg, covert, shade=shade_c, name=name, sep=False if far else "deep")
    return {"W": W, "T": T, "tips": [tp for _, tp, _ in prims], "roots": [r for r, _, _ in prims]}


# wing flap keys: (arm_deg, hand_deg, trail, fan) for a right-facing bird, near wing
FLAP = {
    "up_high": (96, 112, 1, 1.0),
    "up": (74, 104, 1, 1.0),
    "mid": (150, 168, 1, 0.7),
    "down": (236, 214, -1, 0.9),
    "down_low": (262, 236, -1, 1.0),
    "tuck": (176, 184, 1, 0.1),
}


def snap_offset(cv):
    """The vertical shift ``finish()`` will apply when ``cv.snap_ground`` is set (call it
    after the body is drawn).  Ground FX drawn at ``cv.gy - 1 - snap_offset(cv)`` end up
    on the ground line after the snap."""
    if not cv.snap_ground or not cv.filled.any():
        return 0
    low = int(np.nonzero(cv.filled.any(1))[0].max()) + (1 if cv.outline_enabled else 0)
    return (cv.gy - 1) - low


def erase_mask(cv, m):
    """Erase the pixels of boolean mask ``m`` from the canvas (transparent again)."""
    if m.any():
        cv._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(px.INK), erase=True)


def mist_rise(fx, x, y, h, phase, mat=HOLLOW_MIST, r0=1.8, name="mist"):
    """A column of shrinking mist blobs rising ``h`` px from (x, y), swaying with ``phase``.
    Meant for an unoutlined layer so it reads as soft vapour, not spikes."""
    n = 4
    for i in range(n):
        t = i / (n - 1)
        cx = x + math.sin(phase * 1.3 + t * 3.0) * 1.4 * t - t * 1.5
        cy = y - h * t - (phase % 1.0) * 0.0
        r = r0 * (1.0 - 0.55 * t)
        fx.circle(cx, cy, max(1.25, r), mat, shade="soft", name=name)


def spiral(fx, c, r0, r1, a0, sweep, color, name="wind", step=5.0):
    """1 px spiral from radius r0 at angle a0 winding ``sweep`` deg to radius r1."""
    n = max(3, int(abs(sweep) / step))
    prev = None
    for i in range(n + 1):
        t = i / n
        p = px.polar(c, a0 + sweep * t, r0 + (r1 - r0) * t)
        q = (math.floor(p[0]), math.floor(p[1]))
        if prev is not None and q != prev:
            fx.line(prev, q, color, name=name)
        prev = q
