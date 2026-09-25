"""Wind kite - a wind spirit that took the shape of a giant festival kite (Wind).

View: the silk plane faces the camera, prow pointing right, flying (cell 192, anchor at the
body centre where the bamboo spars cross).  ~36 art px from wing tip to wing tip, ~40 px from
the forked tail to the beak, plus two ~25 px streamer tails.
Parts, back to front: wind trails (FX, behind), two streamer tails (crimson / gold with
festive bands), the swallow-shaped silk sail (crimson, gold-rimmed trailing edges, ink-black
cloud motifs), the bamboo frame (bowed cross spar, spine, leading-edge spars), the bird-head
prow (painted gold, crimson crest and hooked beak, one painted jade eye that glows).
Idle: hovers, silk ripples, streamers flow, 1 px bob.  Walk: glides forward and banks (the
sail foreshortens).  Windup: tilts nose-up and back, streamers pull straight back, wind lines
spiral in at the prow (held).  Attack: a steep dive that slashes across the target with a
wind crescent on frame 1.  Hurt: silk tears flutter.  Death: the spar snaps, the sail folds
and crumples as it spirals down and fades.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "wind_kite",
    "cell": 192,
    "anchor": [96, 96],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: crimson + gold painted silk, ink clouds, pale bamboo, jade eye, white wind -----
SILK = px.material("kite_silk", "#f7865a", "#d8343f", "#9b2150", "#5b1b50", outline="#1b0818",
                   thresholds=(0.86, 0.5, 0.16))
GOLD = px.material("kite_gold", "#fff1ae", "#f0bf48", "#c47a38", "#7e3a4c", outline="#200c14",
                   thresholds=(0.86, 0.5, 0.16))
INKM = px.material("kite_ink", "#3e2c4c", "#281a33", "#1c1128", "#130b1c", outline="#07050c")
BAMBOO = px.material("kite_bamboo", "#fbf4d8", "#eadcae", "#cdb98e", "#a8916f", outline="#1f1812")
JADE = px.material("kite_jade", "#dcfff2", "#67d6bd", "#2c9e8f", "#15514f", outline="#06201e")
WINDM = px.material("kite_wind", "#ffffff", "#e4f2f8", "#a9c6dc", "#7490b8", outline="#26385a")
WIND_HI = px.rgb("#ffffff")
WIND_LO = px.rgb("#a9c6dc")

# ---- sail geometry (local, origin = body centre = spar crossing; lower half, the upper mirrors)
NOSE = (11.0, 0.0)
LEAD_C = (7.5, 12.5)  # leading-edge control point (convex)
TIP = (-6.0, 18.0)  # swept wing tip
TRAIL_C = (-5.0, 7.5)  # trailing-edge control point (concave swallow sweep)
FORK = (-16.0, 5.5)  # tail fork tip (a streamer hangs from each)
NOTCH = (-11.5, 0.0)
HEAD = (14.5, -1.0)

CLOUD_U = [  # ink-black ruyi cloud motifs painted on the silk
    ".kkk...kkk.",
    "k...k.k...k",
    "k.k..k..k.k",
    "k..kk.kk..k",
    ".kk.....kk.",
]
CLOUD_L = [
    "...kkk...",
    ".kk...kk.",
    "k..k.k..k",
    "k.kk.kk.k",
    ".k.....k.",
]

# ---- poses ------------------------------------------------------------------------------------
# bx, by    body offset            tilt   pitch (deg, + = nose up)      size  overall scale
# bank      vertical squash of the sail (1 = flat to the camera, <1 = banking)
# ph        flutter phase (streamers, silk ripple)   amp  streamer wave amplitude
# droop     streamer trailing angle (deg below horizontal-left; - = trailing upward)
# eye       open|angry|squeeze|dead   glow  eye glow 0..2   gather  wind spiralling in at the prow
# dive      dive speed lines   slash  wind crescent (1 = the cut, 0.5 = fading)   tear  silk tears
# fold      upper sail folding onto the spine (death)   snap  broken spar   crumple  holes 0..1
# trail     wind trail length off the wing tips (0 = none)   drift  wind trail animation step
DEFAULTS = dict(bx=0, by=0, tilt=0, size=1.0, bank=1.0, ph=0.0, amp=1.0, droop=24, eye="open", glow=0,
                gather=0, dive=False, slash=0.0, tear=0.0, fold=0.0, snap=False, crumple=0.0, trail=12,
                fade=1.0, ripple=1.0, drift=0, slen=25.0)

HP = math.pi / 2
TP = math.pi / 3

POSE = px.poses(DEFAULTS, {
    "idle": [  # hovering: silk ripples, streamers flow, 1 px bob
        dict(ph=0 * HP, by=0, drift=0),
        dict(ph=1 * HP, by=-1, drift=1),
        dict(ph=2 * HP, by=-1, drift=2),
        dict(ph=3 * HP, by=0, drift=3),
    ],
    "walk": [  # gliding forward, banking (the sail foreshortens) and nosing down a little
        dict(ph=0 * TP, tilt=-6, bank=1.0, droop=14, amp=1.2, trail=18, drift=0),
        dict(ph=1 * TP, tilt=-7, bank=0.92, droop=14, amp=1.2, trail=18, drift=1, by=-1),
        dict(ph=2 * TP, tilt=-9, bank=0.82, droop=12, amp=1.2, trail=18, drift=2, by=-1),
        dict(ph=3 * TP, tilt=-10, bank=0.78, droop=12, amp=1.2, trail=18, drift=3),
        dict(ph=4 * TP, tilt=-9, bank=0.84, droop=12, amp=1.2, trail=18, drift=4, by=1),
        dict(ph=5 * TP, tilt=-7, bank=0.93, droop=14, amp=1.2, trail=18, drift=5, by=1),
    ],
    "windup": [  # tilts up and back, streamers pull straight back, wind gathers at the prow - held
        dict(ph=0.6, tilt=10, bx=-1, by=-1, droop=14, amp=0.5, eye="angry", glow=1, gather=1, trail=8),
        dict(ph=1.2, tilt=19, bx=-2, by=-2, droop=20, amp=0.22, eye="angry", glow=2, gather=2, trail=0),
        dict(ph=1.5, tilt=24, bx=-2, by=-3, droop=24, amp=0.1, eye="angry", glow=2, gather=3, trail=0),
    ],
    "attack": [  # steep dive, slash across the target (hit on frame 1), pull up, recover
        dict(ph=2.0, tilt=-42, bx=3, by=1, droop=-38, amp=0.25, eye="angry", glow=2, dive=True, trail=0),
        dict(ph=2.6, tilt=-16, bx=10, by=8, droop=-14, amp=0.4, eye="angry", glow=2, slash=1.0, trail=0),
        dict(ph=3.4, tilt=12, bx=8, by=5, droop=6, amp=0.9, eye="angry", glow=1, slash=0.5, trail=0),
        dict(ph=4.2, tilt=4, bx=3, by=2, droop=18, amp=1.0, trail=8),
    ],
    "hurt": [  # knocked back, silk tears flutter
        dict(ph=1.0, tilt=16, bx=-3, by=-2, droop=36, amp=1.9, eye="squeeze", tear=1.0, trail=0),
        dict(ph=2.0, tilt=8, bx=-2, by=-1, droop=32, amp=1.5, eye="squeeze", tear=0.6, trail=0),
    ],
    "death": [  # the spar snaps, the sail folds and crumples, spiralling down, fading
        dict(ph=1.0, tilt=16, bx=-3, by=-2, droop=36, amp=2.0, eye="squeeze", tear=1.0, snap=True, fold=0.1,
             trail=0),
        dict(ph=2.0, tilt=-45, bx=-3, by=3, droop=-45, amp=1.6, eye="dead", tear=1.0, snap=True, fold=0.4,
             crumple=0.3, size=0.96, trail=0),
        dict(ph=3.0, tilt=-110, bx=-2, by=9, droop=-65, amp=1.4, eye="dead", tear=1.0, snap=True, fold=0.55,
             crumple=0.55, size=0.92, trail=0),
        dict(ph=4.0, tilt=-165, bx=-1, by=14, droop=-78, amp=1.2, eye="dead", tear=1.0, snap=True, fold=0.62,
             crumple=0.75, size=0.88, trail=0, fade=0.6),
        dict(ph=5.0, tilt=-190, bx=0, by=18, droop=-84, amp=1.0, eye="dead", tear=1.0, snap=True, fold=0.66,
             crumple=0.9, size=0.84, trail=0, fade=0.3),
    ],
})


# ---- small geometry helpers -------------------------------------------------------------------
def _qbez(p0, c, p1, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, d = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        out.append((a * p0[0] + b * c[0] + d * p1[0], a * p0[1] + b * c[1] + d * p1[1]))
    return out


def _mirror(pts, sgn):
    return [(x, sgn * y) for x, y in pts]


def _seg(cv, pts, mat, **kw):
    """1 px poly-line through local points, rasterised crisply in canvas space."""
    cps = [cv.tp(q) for q in pts]
    with cv.xform(np.linalg.inv(cv.M)):
        for a, b in zip(cps, cps[1:]):
            cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), mat, **kw)


def _wline(fx, pts, color, name="wind"):
    """1 px world-space poly-line."""
    for a, b in zip(pts, pts[1:]):
        fx.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), color, name=name)


def _edges(p, k):
    """Lower-half leading edge and rippled trailing edge (local)."""
    lead = _qbez(NOSE, LEAD_C, TIP, 8)
    trail = _qbez(TIP, TRAIL_C, FORK, 8)
    tx, ty = FORK[0] - TIP[0], FORK[1] - TIP[1]
    ln = math.hypot(tx, ty)
    nx, ny = -ty / ln, tx / ln
    rt = []
    for i, q in enumerate(trail):
        s = i / (len(trail) - 1)
        w = p.ripple * math.sin(math.pi * s) * (1.1 * math.sin(p.ph + s * 2 * math.pi + k)
                                                 + 0.4 * math.sin(2 * p.ph - s * 3 * math.pi + k))
        rt.append((q[0] + nx * w, q[1] + ny * w))
    return lead, rt


def _half_poly(p, k):
    lead, trail = _edges(p, k)
    return lead + trail[1:] + [NOTCH, (NOTCH[0], -0.8), (NOSE[0], -0.8)]


def _fold(p, sgn):
    return p.fold if sgn < 0 else p.fold * 0.4


# ---- parts ------------------------------------------------------------------------------------
def _streamer(cv, root, p, key, length, name, mat, band_mat, bend):
    """A long silk ribbon whipping in the wind, drawn in world space from ``root``."""
    n = 16
    d = math.radians(p.droop + bend)
    dx, dy = -math.cos(d), math.sin(d)
    nx, ny = -dy, dx
    pts, radii = [], []
    for i in range(n + 1):
        s = i / n
        off = p.amp * 3.0 * s ** 0.9 * math.sin(p.ph - s * 6.5 + key)
        L = length * s
        pts.append((root[0] + dx * L + nx * off, root[1] + dy * L + ny * off))
        tw = 0.6 + 0.4 * abs(math.cos(p.ph * 0.5 + s * 4.0 + key))  # the ribbon twisting
        radii.append(max(0.55, 1.4 * (1 - 0.3 * s) * tw))
    cv.limb(pts, radii, mat, shade="two", name=name)
    for s0 in (0.3, 0.62):  # festive bands
        i0 = int(round(s0 * n))
        cv.limb(pts[i0:i0 + 2], radii[i0:i0 + 2], band_mat, shade="two", decal=True, clip=name, name=name)


def _sail(cv, p):
    """Both silk halves (each billows as its own panel); the upper half folds in death."""
    geoms, frames = [], {}
    for sgn in (-1, 1):
        with cv.xform(px.scale(1.0, 1.0 - _fold(p, sgn), (0.0, 0.0))):
            geoms.append(cv.geom_polygon(_mirror(_half_poly(p, 0.0 if sgn < 0 else 1.7), sgn)))
            frames[sgn] = cv.M.copy()
    # the silk breathes: the panels billow a little more and less with the flutter phase
    cv.draw_geom(cv.union(*geoms), SILK, name="sail", bulge=1.0 + 0.18 * math.sin(p.ph) * p.ripple)
    return frames


def _inner(lead, sgn, depth):
    out = []
    for i, q in enumerate(lead):
        a = lead[max(0, i - 1)]
        b = lead[min(len(lead) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        if nx * (-1 - q[0]) + ny * (sgn * 6 - q[1]) < 0:
            nx, ny = -nx, -ny
        out.append((q[0] + nx * depth, q[1] + ny * depth))
    return out


def _sail_paint(cv, p, frames):
    """Gold rim, ink clouds and the bamboo frame, each half in its own (folded) frame."""
    for sgn in (-1, 1):
        with cv.xform(np.linalg.inv(cv.M) @ frames[sgn]):
            lead, trail = _edges(p, 0.0 if sgn < 0 else 1.7)
            lead, trail = _mirror(lead, sgn), _mirror(trail, sgn)
            cv.limb(trail + _mirror([FORK, NOTCH], sgn), 1.1, GOLD, shade="two", clip="sail", name="sail")
            if sgn < 0:
                cv.stamp(CLOUD_U, -7, -12, {"k": INKM}, decal=True, clip="sail", name="sail")
            else:
                cv.stamp(CLOUD_L, -5, 6, {"k": INKM}, decal=True, clip="sail", name="sail")
            _seg(cv, _inner(lead, sgn, 1.0)[1:], BAMBOO, decal=True, clip="sail", name="spar")
            cross = _qbez((0.0, 0.0), (-1.2, sgn * 9.0), (TIP[0] + 0.8, sgn * (TIP[1] - 1.2)), 6)
            if p.snap and sgn < 0:  # the spar snapped: the outer piece kinks away
                _seg(cv, cross[:4], BAMBOO, decal=True, clip="sail", name="spar")
                _seg(cv, [(x + 1.6, y + 1.2) for x, y in cross[3:]], BAMBOO, decal=True, clip="sail", name="spar")
            else:
                _seg(cv, cross, BAMBOO, decal=True, clip="sail", name="spar")
    _seg(cv, [(NOTCH[0] + 1, 0.0), (NOSE[0] - 1, 0.0)], BAMBOO, decal=True, clip="sail", name="spar")


def _tears(cv, p, frames):
    """Silk torn at the trailing edges: V notches with flaps (showing the pale unpainted back of
    the silk) fluttering out.  Returns world positions of the scraps blown off behind."""
    scraps = []
    if p.tear <= 0:
        return scraps
    sites = ((-1, 0.4, 4.2), (1, 0.6, 3.8))
    for j, (sgn, s, depth) in enumerate(sites):
        with cv.xform(np.linalg.inv(cv.M) @ frames[sgn]):
            _, trail = _edges(p, 0.0 if sgn < 0 else 1.7)
            i = int(round(s * (len(trail) - 1)))
            q = trail[i]
            a, b = trail[i - 1], trail[i + 1]
            tx, ty = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(tx, ty) or 1.0
            tx, ty = tx / ln, ty / ln
            nx, ny = -ty, tx  # inward (toward the spine) for the lower half
            q, (tx, ty), (nx, ny) = (q[0], sgn * q[1]), (tx, sgn * ty), (nx, sgn * ny)
            d = depth * (0.7 + 0.3 * p.tear)
            cut = [(q[0] + tx * 2.4 - nx * 0.8, q[1] + ty * 2.4 - ny * 0.8), (q[0] + nx * d, q[1] + ny * d),
                   (q[0] - tx * 2.2 - nx * 0.8, q[1] - ty * 2.2 - ny * 0.8)]
            cv.polygon(cut, SILK, erase=True)
            # the torn flap flutters outward from one lip of the cut
            fl = 3.2 + 1.2 * math.sin(p.ph * 2 + j)
            flap = [(q[0] + tx * 2.4, q[1] + ty * 2.4), (q[0] + tx * 0.2 + nx * 1.0, q[1] + ty * 0.2 + ny * 1.0),
                    (q[0] - nx * fl + tx * 0.4, q[1] - ny * fl + ty * 0.4)]
            cv.polygon(flap, SILK, shade=(0, 0, 1, 1), name="flap", sep=True)
            far = 3.5 + 5.0 * (1.0 - p.tear)
            scraps.append(cv.tp((q[0] - nx * far - (2.0 + far * 0.6), q[1] - ny * far)))
    return scraps


def _scrap(fx, x, y, r, spin):
    """A torn scrap of painted silk tumbling away (FX layer, world space)."""
    fx.polygon([(x - r, y - r * 0.8 * spin), (x + r * 1.3, y - r * 0.1), (x - r * 0.3, y + r * spin)], SILK,
               shade="two", name="scrap")
    fx.pixel(math.floor(x), math.floor(y), GOLD.base, name="scrap")


def _head(cv):
    H = HEAD
    # swept-back crimson crest, then neck + head as one gold form, hooked crimson beak
    cv.polygon([(H[0] + 1.0, H[1] - 3.2), (H[0] - 3.2, H[1] - 2.4), (H[0] - 5.8, H[1] - 8.6),
                (H[0] - 3.4, H[1] - 7.0), (H[0] - 0.6, H[1] - 6.2)], SILK, shade="two", name="crest", sep="deep")
    neck = cv.geom_limb([(8.0, 0.0), (11.5, -0.4)], [2.6, 3.0])
    head = cv.geom_ellipse(H[0], H[1], 4.4, 3.8)
    cv.draw_geom(cv.union(neck, head, weights=[0.8, 1.0]), GOLD, name="head", sep="deep")
    cv.polygon([(H[0] + 3.2, H[1] - 1.8), (H[0] + 7.4, H[1] - 0.6), (H[0] + 8.4, H[1] + 1.4),
                (H[0] + 7.0, H[1] + 1.0), (H[0] + 3.4, H[1] + 1.8)], SILK, shade="two", name="beak", sep="deep")
    return cv.tp((H[0] + 0.8, H[1] - 0.6)), cv.tp((H[0] + 13.0, H[1] + 0.5))


def _eye(cv, E, p):
    x, y = round(E[0]) - 2, round(E[1]) - 2
    if p.eye == "dead":
        cv.stamp(["k..k", ".kk.", ".kk.", "k..k"], x, y, {"k": INKM.deep}, name="eye")
        return
    if p.eye == "squeeze":
        cv.stamp(["kk..", "..kk", "kk.."], x, y, {"k": INKM.deep}, name="eye")
        return
    rows = ([".dd.", "dgbd", "dbbd", ".dd."] if p.glow == 0 else
            [".dd.", "dghd", "dhbd", ".dd."] if p.glow == 1 else [".dd.", "dghd", "dhhd", ".dd."])
    cv.stamp(rows, x, y, {"d": JADE.deep, "b": JADE.base, "h": JADE.light, "g": px.GLINT}, name="eye")
    if p.eye == "angry":  # a painted ink brow slanting down toward the beak
        cv.pixels([(x - 1, y - 1), (x, y - 1), (x + 1, y - 1), (x + 2, y), (x + 3, y)], INKM.base, name="brow")


def _wind_trails(fx, tips, p):
    """Wind lines peeling off the wing tips and trailing behind, flowing with ``drift``."""
    if p.trail <= 0:
        return
    for k, (x, y) in enumerate(tips):
        sgn = -1 if k == 0 else 1
        off = (p.drift * 2 + k * 3) % 6
        L = p.trail + (2 if (p.drift + k) % 2 else 0)
        pts = [(x - 1 - off - i, y + sgn * (0.28 * i * i / max(1.0, L))) for i in range(int(L) + 1)]
        cut = max(2, int(len(pts) * 0.45))
        _wline(fx, pts[:cut + 1], WIND_HI)
        _wline(fx, pts[cut:], WIND_LO)
        # a short detached gust dash further back, flowing with the drift
        d0 = int(L) + 3 + (p.drift + 2 * k) % 3
        _wline(fx, [(x - 1 - off - d0, pts[-1][1]), (x - 1 - off - d0 - 3, pts[-1][1])], WIND_LO)
        end, r = pts[-1], 1.5
        if sgn < 0:  # the upper trail curls up, the lower one curls down
            hc.arc_line(fx, (end[0] + 0.5, end[1] - r + 0.5), r, 270, 30, WIND_LO, name="wind")
        else:
            hc.arc_line(fx, (end[0] + 0.5, end[1] + r + 0.5), r, 90, 330, WIND_LO, name="wind")


def _gather(fx, F, p, frame):
    """Wind lines spiralling in toward the point in front of the prow (the held tell)."""
    n = 1 + p.gather
    for j in range(n):
        a0 = 70 + j * (360 / n) + frame * 25
        r0 = 12 - 1.0 * p.gather
        r1 = 5.5 - 1.2 * p.gather
        hc.spiral(fx, F, r0, r1, a0, -120, WIND_LO if j % 2 else WIND_HI, name="wind")
    if p.gather >= 2:
        hc.arc_line(fx, F, 2.5, 0, 300, WIND_HI, name="wind")
    if p.gather >= 3:
        fx.stamp([".w.", "whw", ".w."], math.floor(F[0]) - 1, math.floor(F[1]) - 1, {"w": WIND_LO, "h": WIND_HI},
                 name="wind")


def _crescent(fx, c, r, a0, a1, width, mat, edge=None):
    """A wind-slash crescent: an arc band from a0 to a1 (deg), thickest in the middle."""
    n = 16
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = a0 + (a1 - a0) * t
        w = width * math.sin(math.pi * t) ** 0.8
        outer.append(px.polar(c, a, r))
        inner.append(px.polar(c, a, r - w))
    fx.polygon(outer + inner[::-1], mat, shade="soft", name="slash")
    if edge is not None:
        hc.arc_line(fx, c, r - 0.6, a0 + (a1 - a0) * 0.15, a0 + (a1 - a0) * 0.8, edge, name="slash")


def _crumple(cv, p, frames):
    if p.crumple <= 0:
        return
    holes = ((-4.0, -9.0, 1.8), (-2.0, 11.0, 1.8), (-10.0, 3.5, 1.5))
    k = int(round(p.crumple * len(holes)))
    for j, (x, y, r) in enumerate(holes[:k]):
        with cv.xform(np.linalg.inv(cv.M) @ frames[-1 if y < 0 else 1]):
            hc.erase_blobs(cv, [(x, y, r * (0.8 + 0.4 * p.crumple))])
    hc.drop_specks(cv, 4)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + p.bx, cv.gy + p.by)
    back = cv.layer(above=False, outline=False)
    top = cv.layer(above=True, outline=True)
    body = (px.rotate(p.tilt, C), px.scale(p.size, p.size * p.bank, C), px.translate(C[0], C[1]))
    with cv.xform(*body):
        roots = [cv.tp((FORK[0], s * FORK[1] * (1 - _fold(p, s)))) for s in (-1, 1)]
        tips = [cv.tp((TIP[0] - 0.5, s * TIP[1] * (1 - _fold(p, s)))) for s in (-1, 1)]
    _wind_trails(back, tips, p)
    _streamer(cv, roots[0], p, 0.0, p.slen * p.size, "streamer_u", SILK, GOLD, -5)
    _streamer(cv, roots[1], p, 2.2, (p.slen - 2) * p.size, "streamer_l", GOLD, SILK, 7)
    with cv.xform(*body):
        frames = _sail(cv, p)
        _sail_paint(cv, p, frames)
        scraps = _tears(cv, p, frames)
        eye_at, prow = _head(cv)
        _crumple(cv, p, frames)
        brk = cv.tp((-2.0, -10.0))
        nose = cv.tp((HEAD[0] + 6.0, HEAD[1] + 1.0))
    _eye(cv, eye_at, p)
    for j, (sx, sy) in enumerate(scraps):
        _scrap(top, sx, sy, 1.7 if p.tear > 0.8 else 1.4, 1 if (j + frame) % 2 else -1)
    if p.gather:
        _gather(cv.layer(above=True, outline=False), prow, p, frame)
    if p.dive:  # speed lines streaming off behind the dive
        a = math.radians(p.tilt)
        dx, dy = -math.cos(a), math.sin(a)  # backward along the flight line
        nx, ny = -dy, dx
        for k, (o, s0, ln) in enumerate(((-9, 20, 12), (0, 24, 10), (9, 19, 12))):
            x0, y0 = C[0] + dx * s0 + nx * o, C[1] + dy * s0 + ny * o
            _wline(back, [(x0, y0), (x0 + dx * ln, y0 + dy * ln)], WIND_HI if k != 1 else WIND_LO)
    if p.slash > 0:
        fxs = cv.layer(above=True, outline=True)
        spark = cv.layer(above=True, outline=False)
        if p.slash >= 1:  # the cut: a wind blade sweeping down across the target, with a gust spark
            c = (nose[0] - 7, nose[1] - 4)
            for r, a0, a1 in ((14.5, 70, -35), (11.0, 50, -25)):  # motion echoes of the sweep (behind)
                hc.arc_line(back, c, r, a0, a1, WIND_LO, name="wind")
            _crescent(fxs, c, 19, 88, -58, 4.6, WINDM, edge=WIND_HI)
            hit = px.polar(c, 10, 18)
            px.impact(spark, hit[0] + 1, hit[1], size=4, color=WIND_HI, core=JADE.light)
        else:  # the blade flies on and frays
            c = (nose[0] - 4, nose[1] - 2)
            _crescent(fxs, c, 17, 30, -70, 2.6, WINDM)
            hc.arc_line(back, c, 12.5, 10, -50, WIND_LO, name="wind")
    if p.snap and action == "death" and frame == 0:  # bamboo splinters from the snapped spar
        bx, by = math.floor(brk[0]), math.floor(brk[1])
        top.line((bx - 5, by - 3), (bx - 7, by - 4), BAMBOO, name="splinter")
        top.line((bx + 2, by - 6), (bx + 4, by - 7), BAMBOO, name="splinter")
