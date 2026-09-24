"""Shared helpers for the batch-A creatures (Hollow mist, water ripples, dissolves).

Only used by creature modules; it never changes ``pixel.py`` behaviour.  Everything is
deterministic (no randomness; variety comes from :func:`pixel.hash01`).
"""
import math

import numpy as np

import pixel as px

# ---- Hollow ramps (grey-white #87949A family; lights lean warm paper, shadows cool slate) --
HOLLOW_BODY = px.material("hollow_body", "#d6ddd9", "#aab5b8", "#808d94", "#5a6770", outline="#12181d",
                          thresholds=(0.84, 0.52, 0.2))
HOLLOW_BELLY = px.material("hollow_belly", "#e9ece4", "#cdd4d0", "#a4afb1", "#7d8990", outline="#12181d")
HOLLOW_FIN = px.material("hollow_fin", "#d3dbdb", "#a3aeb3", "#77848c", "#535f69", outline="#12181d")
HOLLOW_DARK = px.material("hollow_dark", "#8d989d", "#67737b", "#4b565f", "#343e47", outline="#0c1116")
# mist puffs / wisps: pale, low contrast, outlined in a soft slate (never ink)
MIST = px.material("hollow_mist", "#eef2ef", "#c9d2d3", "#a3aeb2", "#7f8b92", outline="#4f5b64")
MIST_OUT = px.rgb("#4f5b64")
EYE_WHITE = px.EYE_WHITE
EYE_HALO = px.rgb("#cfe6ea")  # faint cold glow ring around glowing Hollow eyes
RIPPLE = px.rgb("#c4d0d3")
RIPPLE_DIM = px.rgb("#7f8e96")


def mist_wisp(cv, x, y, phase=0.0, length=6.0, rise=1.0, direction=-1, thick=0.9, mat=MIST, sway=1.0):
    """A curling wisp rising from (x, y): a tapered S-curve that climbs ``length`` px
    (times ``rise``) and drifts ``direction`` (-1 = back / left) while it sways with
    ``phase``.  Soft-shaded with the pale mist tones; draw it on a layer."""
    n = 5
    pts = []
    for k in range(n + 1):
        t = k / n
        wx = x + direction * length * 0.6 * t * t + math.sin(phase + t * 4.0) * 1.0 * sway * t
        wy = y - length * rise * t
        pts.append((wx, wy))
    radii = [thick * (1.0 - 0.55 * k / n) for k in range(n + 1)]
    cv.limb(pts, radii, mat, shade="soft", name="mist")


def recolour(cv, part, colour):
    """Repaint every pixel of ``part`` in one colour (bypasses the Hollow re-colouring)."""
    m = cv.mask_of(part)
    if not m.any():
        return
    was, cv.hollow = cv.hollow, False
    cv._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(colour), name=part)
    cv.hollow = was


MIST_DIM = px.material("hollow_mist_dim", "#b7c2c5", "#95a2a8", "#7c8a91", "#66737b", outline="#3a444b")


def mist_trail(cv, x, y, length=6.0, phase=0.0, thick=0.8, direction=-1, wave=1.0, mat=MIST_DIM):
    """Horizontal wavy wisp trailing from (x, y) (behind a swimmer), tapering to a point."""
    n = 5
    pts = [(x + direction * length * k / n, y + math.sin(phase + k * 1.3) * wave * (k / n)) for k in range(n + 1)]
    cv.limb(pts, [thick * (1.0 - 0.5 * k / n) for k in range(n + 1)], mat, shade="soft", name="mist")


def socket(cv, colour=None, part="eye"):
    """Dark 1 px socket around the pixels of ``part`` (Hollow eyes need contrast on pale
    heads).  Paints only over existing body pixels next to the eye."""
    colour = px.rgb(colour) if colour is not None else HOLLOW_DARK.shadow
    m = cv.mask_of(part)
    if not m.any():
        return
    ring = px.dilate(m) & ~m & cv.filled & ~cv.mask_of("eyehalo")
    was, cv.hollow = cv.hollow, False  # already a Hollow colour: skip the re-colouring
    cv._commit(ring, np.where(ring, 3, -1).astype(np.int8), px.flat(colour, outline=HOLLOW_DARK.outline),
               name="socket")
    cv.hollow = was


def mist_puff(cv, x, y, t, size=1.0, seed=0, mat=MIST, count=4, spread=1.0):
    """Rising grey mist puff cluster centred near (x, y) for life ``t`` 0..1: clumps grow
    and drift upward, then thin into specks.  Draw on an outlined layer so each clump
    gets the soft slate outline."""
    if t < 0 or t > 1:
        return
    grow = min(1.0, 0.55 + t * 1.2)
    shrink = 1.0 - max(0.0, (t - 0.55) / 0.45) * 0.6
    for i in range(count):
        a = px.hash01(seed, i, "a") * 2 * math.pi
        d = (1.5 + 2.5 * px.hash01(seed, i, "d")) * spread
        r0 = (1.3 + 1.2 * px.hash01(seed, i, "r")) * size
        rr = max(0.8, r0 * grow * shrink)
        cx = x + math.cos(a) * d * (0.6 + t) * size
        cy = y + math.sin(a) * d * 0.6 * size - t * 5.0 * size * (0.6 + 0.4 * px.hash01(seed, i, "v"))
        cv.circle(cx, cy, rr, mat, shade="soft", name="mist")
    if t > 0.4:
        speck = px.flat(mat.light, outline=mat.outline)
        for i in range(2):
            sx = x + (px.hash01(seed, i, "sx") - 0.5) * 9 * size
            sy = y - 4 - t * 6 * size - i * 2
            cv.pixels([(math.floor(sx), math.floor(sy)), (math.floor(sx) + 1, math.floor(sy))], speck, name="mist")


def sweep_mask(cv, x_edge, seed=0, jag=1.5, direction=-1):
    """Pixels behind a ragged vertical front at ``x_edge`` (direction -1: everything left
    of it).  The front wobbles per 2-row band so the edge looks torn, not ruled."""
    rows = np.arange(cv.h)
    j = np.array([px.hash01(seed, r // 2) for r in rows]) * 2 - 1
    edge = x_edge + jag * j[:, None]
    return (cv.X < edge) if direction < 0 else (cv.X > edge)


def body_bbox(cv):
    """(x0, y0, x1, y1) of the filled body pixels (or None)."""
    ys, xs = np.nonzero(cv.filled)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def clean_specks(cv, min_size=3):
    """Erase body clusters smaller than ``min_size`` px (8-connected) - tidies dissolves
    so no crumbs of 1-2 px survive."""
    f = cv.filled
    h, w = f.shape
    seen = np.zeros_like(f)
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
                    m = np.zeros_like(f)
                    for (y, x) in comp:
                        m[y, x] = True
                    cv._commit(m, np.full(m.shape, 1, np.int8), px.flat("#000000"), erase=True)


def ripple(cv, x, y, rx, ry=None, colour=RIPPLE, dim=RIPPLE_DIM, clip=None, name="ripple"):
    """Flat elliptical water ring on the ground plane centred at (x, y): a 1 px ring,
    bright on its far (upper) arc and dim on its near arc.  ``clip`` keeps it on a pool."""
    ry = max(1.2, rx * 0.2) if ry is None else ry
    outer = ((cv.X - x) / rx) ** 2 + ((cv.Y - y) / ry) ** 2 <= 1.0
    inner = ((cv.X - x) / max(0.5, rx - 1.6)) ** 2 + ((cv.Y - y) / max(0.5, ry - 1.0)) ** 2 <= 1.0
    ring = outer & ~inner
    kw = dict(decal=True, clip=clip) if clip is not None else {}
    top = ring & (cv.Y < y)
    cv._commit(top, np.where(top, 1, -1).astype(np.int8), px.flat(colour, outline=dim), name=name, **kw)
    bot = ring & ~top
    cv._commit(bot, np.where(bot, 1, -1).astype(np.int8), px.flat(dim, outline=dim), name=name, **kw)


def eye_glow(cv, x, y, state="open", size=2, halo=True):
    """Empty glowing Hollow eye at top-left (x, y): solid white, no pupil, with an
    optional 1 px cold halo on the upper-left.  ``squeeze`` draws a white chevron,
    ``dead`` a white X, ``wide`` a larger 3x3 flare."""
    if state == "squeeze":
        rows = {2: ["w.", ".w", "w."], 3: ["w..", ".ww", "w.."]}[min(3, max(2, size))]
        cv.stamp(rows, x, y - (1 if size >= 3 else 0), {"w": EYE_WHITE}, name="eye")
        return
    if state == "dead":
        cv.stamp(["w.w", ".w.", "w.w"], x, y - 1, {"w": px.rgb("#a9b4b8")}, name="eye")
        return
    if state == "closed":
        cv.stamp(["w" * size], x, y + size // 2, {"w": EYE_WHITE}, name="eye")
        return
    n = size + (1 if state == "wide" else 0)
    rows = ["w" * n for _ in range(n)]
    cv.stamp(rows, x, y, {"w": EYE_WHITE}, name="eye")
    if halo:
        pts = [(x - 1, y + k) for k in range(n)] + [(x + k, y - 1) for k in range(n)]
        cv.pixels(pts, EYE_HALO, name="eyehalo", under=False, decal=True)


# ---- Hollow fish (shared by hollow_minnow and greyfin) -----------------------------------
MOUTH_DARK = px.rgb("#2a333b")
FISH_TOOTH = px.rgb("#f2f1e6")


def fish_spine(C, length, amp=0.0, phase=0.0, n=7):
    """Spine points from tail root to nose (fish-local, before rotation).  A travelling
    wave of amplitude ``amp`` grows toward the tail; the head stays steady."""
    lb = length * 0.74
    pts = []
    for k in range(n):
        t = k / (n - 1)  # 0 = tail root, 1 = nose
        env = (1 - t) ** 1.6
        y = C[1] + amp * env * math.sin(phase + 2.4 * (1 - t))
        pts.append((C[0] - lb / 2 + lb * t, y))
    return pts


def hollow_fish(cv, C, length, height, ang=0.0, amp=0.0, phase=0.0, tail=0.0, jaw=0.0, fin=0.0,
                eye="open", eye_size=2, teeth=False, ragged=True, body=HOLLOW_BODY, belly=HOLLOW_BELLY,
                finmat=HOLLOW_FIN, dorsal=1.0, draw_eye=True, eye_back=0.75, detail=True, tail_len=0.30, tail_spread=38, sep="deep",
                jaw_open=34.0, hinge_back=0.7, form="limb", tall_dorsal=False):
    """Side-view Hollow fish facing right, centred at C, ``length`` nose-to-tail-tip,
    ``height`` body depth.  ``ang`` pitch (deg, + nose up), ``amp``/``phase`` swim wave,
    ``tail`` extra tail-fin swing (deg), ``jaw`` 0..1 gape, ``fin`` pectoral flap (deg),
    ``dorsal`` dorsal-fin height factor.  Returns canvas points: nose, mouth, tail, eye."""
    r = height / 2.0
    out = {}
    with cv.xform(px.rotate(ang, C)):
        sp = fish_spine(C, length, amp, phase)
        prof = (0.20, 0.46, 0.78, 0.96, 1.0, 0.84, 0.42)
        radii = [max(0.55, r * f) for f in prof]
        # tail fin: forked, hinged at the tail root, swinging with the wave + ``tail``
        root = sp[0]
        d = (sp[0][0] - sp[1][0], sp[0][1] - sp[1][1])
        base_a = math.degrees(math.atan2(-d[1], d[0])) + tail
        lt = length * tail_len
        up = px.polar(root, base_a + tail_spread, lt)
        lo = px.polar(root, base_a - tail_spread, lt * 0.95)
        notch = px.polar(root, base_a, lt * 0.5)
        cv.polygon([px.polar(root, base_a + 90, r * 0.3), up, px.polar(up, base_a - 150, lt * 0.22), notch,
                    px.polar(lo, base_a + 150, lt * 0.22), lo, px.polar(root, base_a - 90, r * 0.3)],
                   finmat, shade="two", name="fin")
        # dorsal fin (swept back, ragged trailing edge) and small anal fin, both behind the body
        def at(t):
            i = min(len(sp) - 2, int(t * (len(sp) - 1)))
            f = t * (len(sp) - 1) - i
            p = px.lerp_pt(sp[i], sp[i + 1], f)
            rr = radii[i] + (radii[i + 1] - radii[i]) * f
            return p, rr
        def top(t, lift):
            p_, rr = at(t)
            return (p_[0], p_[1] - rr - lift)
        if dorsal > 0 and tall_dorsal:  # tall shark-like sail with a torn trailing edge
            fh = r * 1.3 * dorsal
            pts = [top(0.64, -1.0), top(0.60, fh * 0.35), top(0.54, fh * 0.85), top(0.50, fh),
                   top(0.47, fh * 0.62), top(0.44, fh * 0.74), top(0.41, fh * 0.42), top(0.38, fh * 0.5),
                   top(0.34, fh * 0.22), top(0.32, -1.0)]
            cv.polygon(pts, finmat, shade="two", name="fin")
        elif dorsal > 0:
            (a, ra), (b, rb) = at(0.40), at(0.66)
            fh = r * 1.05 * dorsal
            apex = (a[0] - 0.5, a[1] - ra - fh)
            pts = [(b[0], b[1] - rb + 0.8), (b[0] - 1.0, b[1] - rb - fh * 0.55), apex]
            if ragged:
                pts = [(b[0], b[1] - rb + 0.8), (b[0] - 1.2, b[1] - rb - fh * 0.62),
                       (px.lerp_pt(apex, (b[0] - 1.2, b[1] - rb - fh * 0.62), 0.5)[0] - 0.3,
                        b[1] - rb - fh * 0.62 + 0.3),
                       apex, (a[0] - 1.6, a[1] - ra - fh * 0.45), (a[0] - 2.4, a[1] - ra - fh * 0.3)]
            pts.append((a[0] - 2.6, a[1] - ra + 0.8))
            cv.polygon(pts, finmat, shade="two", name="fin")
        (a, ra), (b, rb) = at(0.18), at(0.36)
        cv.polygon([(b[0], b[1] + rb - 0.8), (a[0] - 1.2, a[1] + ra + r * 0.55), (a[0] + 0.6, a[1] + ra - 0.6)],
                   finmat, shade="two", name="fin")
        # body: one tapered form along the spine.  The lower jaw is the front-lower chunk
        # of the same form, re-rasterised rotated about the hinge when the mouth opens.
        head = sp[-1]
        nose = (head[0] + radii[-1], head[1] + r * 0.1)
        hinge = (head[0] - r * hinge_back, head[1] + r * 0.2)
        jaw_poly = [hinge, (nose[0] + 6, hinge[1] - 0.2), (nose[0] + 6, hinge[1] + 2 * r), (hinge[0], hinge[1] + 2 * r)]
        jaw_a = -jaw_open * jaw
        cut = cv.mask_polygon(jaw_poly) if jaw > 0.05 else None
        lb = length * 0.74

        def body_geom():
            if form == "ellipse":  # one round main form (single highlight) + tapering tail stock
                ex_ = sp[-1][0] + radii[-1] - 0.42 * lb
                main = cv.geom_ellipse(ex_, (sp[-1][1] + sp[-3][1]) / 2, 0.42 * lb, r)
                stock = cv.geom_limb(sp[:4], [r * 0.24, r * 0.42, r * 0.66, r * 0.85])
                return cv.union(main, stock, weights=[1.0, 0.55])
            return cv.geom_limb(sp, radii)
        cv.draw_geom(body_geom(), body, minus=cut, name="fishbody", sep=sep)
        if jaw > 0.05:
            with cv.xform(px.rotate(jaw_a, hinge)):
                g = body_geom()
                cm = cv.mask_polygon(jaw_poly)
                cv.draw_geom((g[0] & cm,) + g[1:], body, shade="nolight", name="fishbody")
                lo_tip = cv.tp((nose[0] - 0.6, hinge[1]))
        if detail and form != "ellipse":
            cv.limb([(p[0], p[1] - rr * 0.62) for p, rr in zip(sp[1:6], radii[1:6])],
                    [rr * 0.42 for rr in radii[1:6]], body.step(1), decal=True, clip="fishbody")
        if form == "ellipse":
            cv.ellipse(sp[-1][0] - 0.36 * lb, sp[-1][1] + r * 0.72, 0.36 * lb, r * 0.5, belly, shade="two",
                       decal=True, clip="fishbody")
        else:
            cv.limb([(p[0], p[1] + rr * 0.55) for p, rr in zip(sp[2:6], radii[2:6])],
                    [rr * 0.5 for rr in radii[2:6]], belly, shade="two", decal=True, clip="fishbody")
        hx, hy = head[0] - r * 0.9, head[1]
        gx = hx - r * 0.55
        if detail:
            cv.limb([(gx + 0.3, hy - r * 0.55), (gx - 0.4, hy), (gx + 0.3, hy + r * 0.5)], 0.5, body.step(2),
                    decal=True, clip="fishbody")
        if jaw > 0.05:  # dark throat at the back of the gape (the front stays open)
            with cv.xform(px.rotate(jaw_a, hinge)):
                lo_mid = cv.tp(px.lerp_pt(hinge, (nose[0], hinge[1]), 0.75))
            up_mid = cv.tp(px.lerp_pt(hinge, (nose[0], hinge[1]), 0.75))
            ih = cv.tp(hinge)
            with cv.xform(np.linalg.inv(cv.M)):
                cv.polygon([(ih[0] - 0.8, ih[1]), (up_mid[0], up_mid[1] - 0.3), (lo_mid[0], lo_mid[1] + 0.3)],
                           px.flat(MOUTH_DARK), under=True, name="mouth")
                if teeth:
                    cv.pixels([(math.floor(up_mid[0]) + 1, math.floor(up_mid[1]) + 1),
                               (math.floor(lo_tip[0]) - 1, math.floor(lo_tip[1]) - 1)], FISH_TOOTH, name="tooth",
                              under=True)
        else:
            cv.line((math.floor(hinge[0]), math.floor(hinge[1])), (math.floor(nose[0]) - 1, math.floor(hinge[1])),
                    body.step(2), decal=True, clip="fishbody")
        # pectoral fin behind the gill, flapping with ``fin``
        pf = (gx - 0.8, hy + r * 0.35)
        cv.polygon([pf, px.polar(pf, 200 + fin, r * 1.25), px.polar(pf, 235 + fin, r * 1.05)], finmat,
                   shade="soft", name="pecfin", sep="deep")
        ex = math.floor(head[0] - r * eye_back - eye_size / 2 + 0.5)
        ey = math.floor(hy - r * 0.42 - eye_size / 2 + 0.5)
        out = {"nose": cv.tp(nose), "mouth": cv.tp((nose[0] + 1, hinge[1])), "tail": cv.tp(notch),
               "tail_tip": cv.tp(px.polar(root, base_a, lt)), "eye": (ex, ey), "top": cv.tp((sp[3][0], sp[3][1] - r)),
               "spine": [cv.tp(p) for p in sp]}
        if draw_eye:
            fish_eye(cv, ex, ey, eye, eye_size)
    return out


def fish_eye(cv, ex, ey, state, size):
    """Empty white Hollow eye with a dark socket (the socket keeps it off the pale body)."""
    if state in ("squeeze", "dead"):
        rows = {("squeeze", 2): ["k.", ".k", "k."], ("squeeze", 3): ["k..", ".kk", "k.."],
                ("dead", 2): ["k.k", ".k.", "k.k"], ("dead", 3): ["k.k", ".k.", "k.k"]}[(state, min(3, size))]
        cv.stamp(rows, ex, ey - (1 if size == 2 else 0), {"k": HOLLOW_DARK.deep}, name="eyemark")
        return
    n = size + (1 if state == "wide" else 0)
    o = -1 if state == "wide" else 0
    cv.stamp(["w" * n] * n, ex + o, ey + o, {"w": EYE_WHITE}, name="eye")
    socket(cv)
    if state == "angry":  # heavy brow slanting down toward the nose
        cv.pixels([(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1)] + ([(ex + 2, ey - 1)] if size >= 3 else []),
                  HOLLOW_DARK.deep, name="brow")


# ---- curves -----------------------------------------------------------------------------
def catmull(points, per=4):
    """Catmull-Rom curve through ``points`` (end points duplicated), ``per`` samples per
    span.  Returns a list of (x, y) including the last point."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(points[-1]))
    return out


def normal_at(pts, i):
    """Unit normal (pointing to the left of travel, i.e. 'up' for a right-going curve)."""
    a = pts[max(0, i - 1)]
    b = pts[min(len(pts) - 1, i + 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    return (dy / ln, -dx / ln)


# ---- crumbling (raster chunks) ------------------------------------------------------------
def crumble(cv, seeds, t, floor_row, seed=0, crack=True, spread=1.0, jitter=1.2):
    """Break everything drawn on ``cv`` into chunks around ``seeds`` (canvas points) and
    let them fall toward ``floor_row`` (the last row a chunk may fill) with progress ``t``
    0..1.  ``crack`` carves 1 px gaps between chunks so each piece gets its own outline.
    Chunks never pass below the floor; lower chunks land first, upper ones tumble outward."""
    f = cv.filled.copy()
    if not f.any():
        return
    h, w = f.shape
    ys, xs = np.nonzero(f)
    # nearest seed with a hashed wobble so the cracks are irregular
    best = np.full(len(xs), 1e9)
    owner = np.zeros(len(xs), int)
    for k, (sx, sy) in enumerate(seeds):
        wob = np.array([px.hash01(seed, k, int(x) // 2, int(y) // 2) for x, y in zip(xs, ys)]) * jitter
        d = np.hypot(xs + 0.5 - sx, ys + 0.5 - sy) + wob
        upd = d < best
        best[upd] = d[upd]
        owner[upd] = k
    lab = np.full((h, w), -1, int)
    lab[ys, xs] = owner
    if crack:  # 1 px gaps where two chunks meet (only on the lower-index side, keeps pieces chunky)
        gap = np.zeros((h, w), bool)
        for dx, dy in ((1, 0), (0, 1)):
            nb = px._shift(lab, -dx, -dy, -1)
            gap |= (lab >= 0) & (nb >= 0) & (nb != lab) & (lab < nb)
        lab[gap] = -1
    src = (cv.rgb.copy(), cv.band.copy(), cv.mat.copy(), cv.part.copy())
    new = [np.zeros_like(a) for a in src]
    new[1][:] = -1
    new[2][:] = -1
    new[3][:] = -1
    nf = np.zeros((h, w), bool)
    order = sorted(range(len(seeds)), key=lambda k: -seeds[k][1])  # lowest chunks first
    cx = sum(s[0] for s in seeds) / len(seeds)
    for k in order:
        m = lab == k
        if not m.any():
            continue
        my, mx = np.nonzero(m)
        low = my.max()
        room = max(0, floor_row - low)
        dy = int(round(min(room, room * min(1.0, t * (1.2 + 0.6 * px.hash01(seed, k, "v"))))))
        dx = int(round((seeds[k][0] - cx) * 0.35 * spread * t + (px.hash01(seed, k, "x") - 0.5) * 2 * t))
        ny, nx = my + dy, mx + dx
        ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        for a, b in zip(new, src):
            a[ny[ok], nx[ok]] = b[my[ok], mx[ok]]
        nf[ny[ok], nx[ok]] = True
    cv.rgb, cv.band, cv.mat, cv.part = new
    cv.filled = nf
