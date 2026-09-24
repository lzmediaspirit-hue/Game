"""Shared helpers for the batch-A creatures (Hollow mist, water ripples, dissolves).

Only used by creature modules; it never changes ``pixel.py`` behaviour.  Everything is
deterministic (no randomness; variety comes from :func:`pixel.hash01`).
"""
import math

import numpy as np

import pixel as px

# ---- Hollow ramps (grey-white #87949A family; lights lean warm paper, shadows cool slate) --
HOLLOW_BODY = px.material("hollow_body", "#eef0e8", "#bcc5c5", "#8a979d", "#5f6b74", outline="#12181d",
                          thresholds=(0.9, 0.55, 0.2))
HOLLOW_BELLY = px.material("hollow_belly", "#fbfaf2", "#dde2dd", "#b0babb", "#86929a", outline="#12181d")
HOLLOW_FIN = px.material("hollow_fin", "#d3dbdb", "#a3aeb3", "#77848c", "#535f69", outline="#12181d")
HOLLOW_DARK = px.material("hollow_dark", "#8d989d", "#67737b", "#4b565f", "#343e47", outline="#0c1116")
# mist puffs / wisps: pale, low contrast, outlined in a soft slate (never ink)
MIST = px.material("hollow_mist", "#eef2ef", "#c9d2d3", "#a3aeb2", "#7f8b92", outline="#4f5b64")
MIST_OUT = px.rgb("#4f5b64")
EYE_WHITE = px.EYE_WHITE
EYE_HALO = px.rgb("#cfe6ea")  # faint cold glow ring around glowing Hollow eyes
# dark Hollow water (grey pools the Hollow fish live in)
HOLLOW_WATER = px.material("hollow_water", "#aebbc0", "#56646d", "#3b4852", "#29343d", outline="#0c1217",
                           thresholds=(0.95, 0.5, 0.2))
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


def dissolve_mask(cv, t, seed=0, cells=3.0, direction=None, bbox=None):
    """Boolean mask of canvas pixels to erase for a dissolve at progress ``t`` (0..1).

    Pixels are grouped in blocky ``cells``-px clusters (never single pixels) that switch
    off in a hashed order; ``direction`` (dx, dy) biases the order so the dissolve
    sweeps across the body (e.g. (-1, 0): tail first)."""
    h, w = cv.h, cv.w
    ys, xs = np.mgrid[0:h, 0:w]
    ci = np.floor(xs / cells).astype(int)
    cj = np.floor(ys / cells).astype(int)
    # stable hash per cluster
    hv = ((ci * 73856093) ^ (cj * 19349663) ^ (seed * 83492791)) & 0xFFFF
    r = (hv % 997) / 997.0
    if direction is not None and bbox is not None:
        x0, y0, x1, y1 = bbox
        u = ((xs - x0) / max(1, x1 - x0)) if direction[0] >= 0 else ((x1 - xs) / max(1, x1 - x0))
        v = ((ys - y0) / max(1, y1 - y0)) if direction[1] >= 0 else ((y1 - ys) / max(1, y1 - y0))
        sweep = abs(direction[0]) * u + abs(direction[1]) * v
        sweep = sweep / max(1e-6, abs(direction[0]) + abs(direction[1]))
        r = 0.45 * r + 0.55 * (1.0 - sweep)
    return r < t


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


def ripple(cv, x, y, rx, t=0.0, colour=RIPPLE, dim=RIPPLE_DIM, name="ripple"):
    """Flat elliptical water ring on the ground plane at (x, y) (side view: a thin
    ellipse).  Only the top arc is bright, the lower arc is dim."""
    ry = max(1.0, rx * 0.22)
    d = ((cv.X - x) / rx) ** 2 + ((cv.Y - y) / ry) ** 2
    ring = (d <= 1.0) & (d >= (1.0 - 1.9 / max(ry, 1.0)) ** 2 * 0.95)
    top = ring & (cv.Y < y)
    cv._commit(top, np.where(top, 1, -1).astype(np.int8), px.flat(colour, outline=dim), name=name)
    bot = ring & ~top
    cv._commit(bot, np.where(bot, 1, -1).astype(np.int8), px.flat(dim, outline=dim), name=name)


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
                finmat=HOLLOW_FIN, dorsal=1.0, draw_eye=True, eye_back=0.75, detail=True, tail_len=0.30, tail_spread=38):
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
        if True:
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
        if dorsal > 0:
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
        # body: one tapered form along the spine, dark back, pale belly, gill arc
        cv.limb(sp, radii, body, name="fishbody", sep="deep")
        if detail:
            cv.limb([(p[0], p[1] - rr * 0.62) for p, rr in zip(sp[1:6], radii[1:6])],
                    [rr * 0.42 for rr in radii[1:6]], body.step(1), decal=True, clip="fishbody")
        cv.limb([(p[0], p[1] + rr * 0.55) for p, rr in zip(sp[2:7], radii[2:7])],
                [rr * 0.5 for rr in radii[2:7]], belly, shade="two", decal=True, clip="fishbody")
        head = sp[-1]
        hx, hy = head[0] - r * 0.9, head[1]
        gx = hx - r * 0.55
        if detail:
            cv.limb([(gx + 0.3, hy - r * 0.55), (gx - 0.4, hy), (gx + 0.3, hy + r * 0.5)], 0.5, body.step(2),
                    decal=True, clip="fishbody")
        # mouth: a wedge cut into the nose opening with ``jaw``; dark throat, optional teeth
        nose = (head[0] + radii[-1], head[1] + r * 0.1)
        hinge = (head[0] - r * 0.55, head[1] + r * 0.18)
        if jaw > 0.05:
            op = jaw * r * 1.25
            wedge = [hinge, (nose[0] + 3, hinge[1] - op * 0.55 - 0.6), (nose[0] + 3, hinge[1] + op)]
            cv.polygon(wedge, body, erase=True)
            # lower jaw hangs open (keeps a chin below the cut)
            chin_t = px.polar(hinge, -math.degrees(math.atan2(op, nose[0] + 2 - hinge[0])) - 4, r * 1.5)
            cv.limb([hinge, chin_t], [r * 0.45, r * 0.28], body, shade="two", name="fishbody")
            cv.polygon([hinge, (hinge[0] + r * 0.9, hinge[1] - op * 0.25), (hinge[0] + r * 0.9, hinge[1] + op * 0.45)],
                       px.flat(MOUTH_DARK), name="mouth")
            if teeth:
                cv.pixels([(math.floor(nose[0]) - 1, math.floor(hinge[1] - op * 0.25)),
                           (math.floor(chin_t[0]) - 1, math.floor(chin_t[1]) - 1)], FISH_TOOTH, name="tooth")
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
