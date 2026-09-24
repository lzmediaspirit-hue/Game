"""Jade carp - large jade-green river carp with gold-tipped fins and whiskers (Water).

View: side, facing right.  ~36 art px long, ~20 tall (cell 128).  It lives at the water
line: the ground row is the water surface, rippling wherever the fish touches it.
The body is built on a curved spine (centre M, pitch ``ang``, curvature ``k``) so it can
arch, coil and whip: a tapered tube (tail -> head) + forked caudal fin, dorsal fin, pelvic /
anal / pectoral fins with gold tips, pale gold belly, scale lattice, gill arc, big gold-ringed
eye, barbels.  Idle: arches over a small ripple.  Walk: porpoising arcs (3 airborne frames).
Windup: curls its tail up into a tight U on the water (held).  Attack: leaps and whips the
tail over the top in a slap (hit frame 1) with a splash.  Death: flops onto the water, still.
"""
import math

import pixel as px
import helpers_batch_b as hb

SPEC = {
    "id": "jade_carp",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["walk", 1], ["walk", 2], ["walk", 3], ["attack", 0], ["attack", 1], ["attack", 2]],
}

# ---- palette ------------------------------------------------------------------------------
SCALE = px.material("carp_scale", "#a6ecc8", "#3fae8a", "#1f7a6c", "#134c4c", outline="#071a1c",
                    thresholds=(0.9, 0.52, 0.16))
BELLY = px.material("carp_belly", "#fff4c0", "#f0d98a", "#c2a85c", "#86703e", outline="#071a1c")
FIN = px.material("carp_fin", "#b8f2dc", "#67d6bd", "#2c9e8f", "#1a6a66", outline="#071a1c")
GOLD = px.material("carp_gold", "#fff0a8", "#e5b84c", "#b0802e", "#6e4e22", outline="#1a1206")
IRIS = px.rgb("#f2c24a")
WATER = px.WATER_FX

# ---- poses --------------------------------------------------------------------------------
# mx, my   spine centre (dx from the anchor, height above the water line)
# ang      pitch of the head end (deg, 0 = right, + = nose up)   k  curvature (deg / px;
#          + arches head and tail down, - curls them up)      fl  tail-fin flick (deg)
# jaw 0..1   eye open|angry|squeeze|dead   rip  ripple half-width (0 = none) at x offset rx
# splash   splash life (x offset, t)   flop  lying on the water (death)   fade  opacity
DEFAULTS = dict(mx=0.0, my=9.0, ang=0.0, k=3.2, fl=0.0, jaw=0.0, eye="open", rip=(6.0, 0.0), splash=None,
                flop=False, fade=1.0, hit=False, whisk=0.0, whoosh=False)

POSE = px.poses(DEFAULTS, {
    "idle": [  # arching over a ripple, tail and whiskers swaying
        dict(my=11.0, k=4.4, fl=0),
        dict(my=11.5, k=4.5, fl=8, whisk=0.5, jaw=0.3),
        dict(my=12.0, k=4.6, fl=14, whisk=1.0),
        dict(my=11.5, k=4.5, fl=6, whisk=0.5, jaw=0.3),
    ],
    "walk": [  # porpoising: nose out - rise - top - fall - nose in - skim
        dict(mx=-3, my=7.0, ang=28, k=1.8, fl=-10, rip=(6.0, -12.0)),
        dict(mx=-1, my=13.0, ang=18, k=2.4, fl=-4, rip=(8.0, -14.0)),
        dict(mx=1, my=15.0, ang=0, k=3.2, fl=10, rip=(0.0, 0.0)),
        dict(mx=3, my=13.0, ang=-18, k=2.8, fl=16, rip=(0.0, 0.0)),
        dict(mx=4, my=7.5, ang=-30, k=1.6, fl=6, rip=(6.0, 12.0), splash=(14.0, 0.2)),
        dict(mx=1, my=6.0, ang=-4, k=0.4, fl=-6, rip=(9.0, 8.0)),
    ],
    "windup": [  # rests on the water and coils its tail up high behind it, glaring - held
        dict(my=6.5, ang=-2, k=-2.0, fl=-10, eye="angry", rip=(8.0, 0.0), jaw=0.2),
        dict(my=7.0, ang=-6, k=-4.0, fl=-26, eye="angry", rip=(9.0, -2.0), jaw=0.5, mx=-1),
        dict(my=7.0, ang=-8, k=-4.6, fl=-32, eye="angry", rip=(9.5, -2.0), jaw=0.6, mx=-2),
    ],
    "attack": [  # leaps, curls the tail under and forward and slaps it into the target
        dict(mx=0, my=15.0, ang=58, k=-2.0, fl=-20, eye="angry", jaw=0.6, rip=(7.0, -4.0), splash=(-4.0, 0.3)),
        dict(mx=3, my=17.0, ang=168, k=2.6, fl=-30, eye="angry", jaw=0.4, rip=(0.0, 0.0), hit=True, whoosh=True),
        dict(mx=4, my=13.0, ang=262, k=2.0, fl=10, eye="angry", jaw=0.2, rip=(0.0, 0.0), whoosh=True),
        dict(mx=3, my=7.5, ang=2, k=1.6, fl=0, rip=(9.0, 2.0), splash=(8.0, 0.6)),
    ],
    "hurt": [
        dict(mx=-3, my=11.0, ang=26, k=4.2, fl=-20, eye="squeeze", jaw=0.7, rip=(7.0, 0.0)),
        dict(mx=-2, my=10.0, ang=14, k=3.8, fl=-8, eye="squeeze", jaw=0.3, rip=(8.0, 0.0)),
    ],
    "death": [  # thrashes, flops over onto the surface, lies still, fades
        dict(mx=-3, my=12.0, ang=36, k=4.6, fl=-24, eye="squeeze", jaw=0.8, rip=(7.0, 0.0)),
        dict(mx=-2, my=8.0, ang=-12, k=-3.0, fl=20, eye="dead", jaw=0.6, rip=(9.0, 0.0), splash=(0.0, 0.3)),
        dict(flop=True, eye="dead", jaw=0.5, rip=(10.0, 0.0)),
        dict(flop=True, eye="dead", jaw=0.5, rip=(0.0, 0.0), fade=0.6),
        dict(flop=True, eye="dead", jaw=0.5, rip=(0.0, 0.0), fade=0.3),
    ],
})

L_HEAD, L_TAIL = 12.0, 14.0  # spine length in front of / behind the centre


def _spine(M, ang, k):
    """Points from the tail base to the snout along a circular arc through M."""
    pts = []
    for s in range(int(-L_TAIL), int(L_HEAD) + 1):
        # integrate the tangent angle theta(s) = ang - k*s from 0 to s
        n = max(1, abs(s) * 2)
        x, y = M
        for i in range(n):
            u = s * (i + 0.5) / n
            th = math.radians(ang - k * u)
            x += math.cos(th) * s / n
            y -= math.sin(th) * s / n
        pts.append((x, y))
    return pts


def _radius(t):
    """Body half-depth along the spine, t: 0 = tail base .. 1 = snout."""
    if t < 0.52:
        u = t / 0.52
        return 1.6 + (6.4 - 1.6) * (3 * u * u - 2 * u * u * u)
    if t < 0.8:
        return 6.4 - 1.4 * (t - 0.52) / 0.28
    u = (t - 0.8) / 0.2
    return 5.0 - 2.4 * u * u


def _frame(pts, i):
    """Tangent (toward the head) and dorsal normal at sample i."""
    a = pts[max(0, i - 1)]
    b = pts[min(len(pts) - 1, i + 1)]
    tx, ty = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(tx, ty) or 1.0
    tx, ty = tx / ln, ty / ln
    return (tx, ty), (ty, -tx)


def _at(pts, radii, t, side):
    """Point on the body edge at fraction t (0 tail .. 1 snout), side +1 dorsal / -1 belly."""
    i = min(len(pts) - 1, max(0, int(round(t * (len(pts) - 1)))))
    (tx, ty), (dx, dy) = _frame(pts, i)
    r = radii[i]
    return (pts[i][0] + dx * r * side, pts[i][1] + dy * r * side), (tx, ty), (dx, dy)


def _fin(cv, base0, base1, tip, name, sep=False, mat=FIN, gold=0.45):
    cv.polygon([base0, tip, base1], mat, shade="soft", name=name, sep=sep)
    # gold tip: the outer part of the fin, following its shading
    cv.polygon([px.lerp_pt(base0, tip, 1 - gold), tip, px.lerp_pt(base1, tip, 1 - gold)], GOLD, shade="soft",
               decal=True, clip=name, name=name)
    # rays
    for f in (0.35, 0.7):
        b = px.lerp_pt(base0, base1, f)
        e = px.lerp_pt(b, tip, 0.7)
        cv.line((math.floor(b[0]), math.floor(b[1])), (math.floor(e[0]), math.floor(e[1])), mat.shadow, band=None,
                decal=True, clip=name, name=name)


def _fish(cv, M, ang, k, p):
    pts = _spine(M, ang, k)
    n = len(pts)
    radii = [_radius(i / (n - 1)) for i in range(n)]
    tail = pts[0]
    (tx, ty), (dx, dy) = _frame(pts, 0)
    back_a = math.degrees(math.atan2(ty, -tx))  # direction pointing out behind the tail
    # forked caudal fin (behind the body)
    for sgn, ln in ((1, 10.0), (-1, 9.5)):
        a = back_a + sgn * 36 + p.fl
        tip = px.polar(tail, a, ln)
        mid = px.polar(tail, back_a + p.fl, 4.2)
        root_a = (tail[0] + dx * 1.6 * sgn, tail[1] + dy * 1.6 * sgn)
        _fin(cv, root_a, mid, tip, "tailfin", gold=0.5)
    # dorsal fin along the back (behind the body)
    b0, _, dn = _at(pts, radii, 0.3, 1)
    b1, _, dn1 = _at(pts, radii, 0.72, 1)
    top, (ttx, tty), tdn = _at(pts, radii, 0.64, 1)
    tip = (top[0] + tdn[0] * 5.0 - ttx * 0.5, top[1] + tdn[1] * 5.0 - tty * 0.5)
    back = _at(pts, radii, 0.36, 1)
    tail_tip = (back[0][0] + back[2][0] * 2.0, back[0][1] + back[2][1] * 2.0)
    cv.polygon([(b0[0] - dn[0], b0[1] - dn[1]), tail_tip, tip, (b1[0] - dn1[0] * 1.5, b1[1] - dn1[1] * 1.5)], FIN,
               shade="soft", name="dorsal")
    cv.polygon([px.lerp_pt(tail_tip, tip, 0.1), tip, px.lerp_pt(top, tip, 0.5)], GOLD, shade="soft", decal=True,
               clip="dorsal", name="dorsal")
    for f in (0.3, 0.6, 0.85):
        q = px.lerp_pt(b0, b1, f)
        e = px.lerp_pt(tail_tip, tip, f)
        cv.line((math.floor(q[0]), math.floor(q[1])), (math.floor(e[0]), math.floor(e[1])), FIN.shadow, band=None,
                decal=True, clip="dorsal", name="dorsal")
    # anal + pelvic fins under the belly (behind)
    for t0, t1, h in ((0.2, 0.36, 3.2), (0.46, 0.58, 3.4)):
        a0, _, bn = _at(pts, radii, t0, -1)
        a1 = _at(pts, radii, t1, -1)[0]
        tip = (a0[0] - bn[0] * h - (a1[0] - a0[0]) * 0.3, a0[1] - bn[1] * h - (a1[1] - a0[1]) * 0.3)
        _fin(cv, (a0[0] + bn[0] * 2, a0[1] + bn[1] * 2), (a1[0] + bn[0] * 2, a1[1] + bn[1] * 2), tip, "lowfin",
             gold=0.5)
    # body tube
    cv.limb(pts, radii, SCALE, name="body")
    # belly
    belly = [(q[0] - (dq[1][0]) * r * 0.8, q[1] - (dq[1][1]) * r * 0.8)
             for q, r, dq in ((pts[i], radii[i], _frame(pts, i)) for i in range(n))]
    cv.limb(belly, [r * 0.45 for r in radii], BELLY, shade="two", decal=True, clip="body", name="body")
    # lateral line: a dashed darker line along the flank; a few glinting scales on the back
    for i in range(4, n - 9, 2):
        (ux, uy), (vx, vy) = _frame(pts, i)
        q = (pts[i][0] + vx * radii[i] * 0.1, pts[i][1] + vy * radii[i] * 0.1)
        if (i // 2) % 2 == 0:
            cv.line((math.floor(q[0]), math.floor(q[1])), (math.floor(q[0] + ux), math.floor(q[1] + uy)),
                    SCALE.step(1), band=None, decal=True, clip="body", name="body")
    for i in range(6, n - 10, 5):
        (ux, uy), (vx, vy) = _frame(pts, i)
        q = (pts[i][0] + vx * radii[i] * 0.55, pts[i][1] + vy * radii[i] * 0.55)
        with cv.xform(px.rotate(math.degrees(math.atan2(-uy, ux)), q)):
            cv.stamp(["k.", ".k"], math.floor(q[0]), math.floor(q[1]) - 1, {"k": SCALE.step(1)}, name="body",
                     decal=True, clip="body")
    # gill arc
    g = [px.lerp_pt(_at(pts, radii, 0.8, 1)[0], pts[int(0.8 * (n - 1))], 0.25), pts[int(0.79 * (n - 1))],
         px.lerp_pt(_at(pts, radii, 0.8, -1)[0], pts[int(0.8 * (n - 1))], 0.3)]
    cv.limb(g, 0.5, SCALE.step(1), decal=True, clip="body", name="body")
    # pectoral fin over the body behind the gill
    pa, (ptx, pty), pdn = _at(pts, radii, 0.74, -1)
    pbase = (pa[0] + pdn[0] * 2.5, pa[1] + pdn[1] * 2.5)
    ptip = (pbase[0] - ptx * 5.0 - pdn[0] * 2.5, pbase[1] - pty * 5.0 - pdn[1] * 2.5)
    _fin(cv, (pbase[0] + ptx * 1.2, pbase[1] + pty * 1.2), (pbase[0] - pdn[0] * 1.6, pbase[1] - pdn[1] * 1.6), ptip,
         "pectoral", sep="deep", gold=0.5)
    # head details: eye, mouth, barbels
    (hx, hy), (hdx, hdy) = _frame(pts, n - 1)
    snout = pts[-1]
    E = (snout[0] - hx * 4.0 + hdx * 1.4, snout[1] - hy * 4.0 + hdy * 1.4)
    ex, ey = math.floor(E[0]) - 1, math.floor(E[1]) - 1
    if p.eye in ("open", "angry"):
        cv.stamp(["gyy", "ykk", "ykk"], ex, ey, {"g": px.GLINT, "y": IRIS, "k": px.INK}, name="eye")
        if p.eye == "angry":
            cv.pixels([(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)], SCALE.deep, name="brow")
    else:
        hb.eye(cv, ex, ey, p.eye)
    mouth = (snout[0] + hx * 1.8 - hdx * 1.0, snout[1] + hy * 1.8 - hdy * 1.0)
    lip_top = (mouth[0] + hdx * 1.0 * (1 + p.jaw), mouth[1] + hdy * 1.0 * (1 + p.jaw))
    lip_bot = (mouth[0] - hdx * 1.0 * (1 + p.jaw), mouth[1] - hdy * 1.0 * (1 + p.jaw))
    cv.limb([px.lerp_pt(snout, lip_bot, 0.4), lip_bot], [0.9, 0.7], BELLY, shade="two", name="lip")
    if p.jaw > 0.2:
        cv.pixel(math.floor(mouth[0]), math.floor(mouth[1]), px.INK, name="mouth")
    # barbels: two thin gold whiskers trailing from the mouth corner (no outline)
    wl = cv.layer(above=True, outline=False)
    root = (snout[0] - hdx * 1.4 - hx * 0.5, snout[1] - hdy * 1.4 - hy * 0.5)
    for ln, back in ((5.0, 1.6), (3.5, 0.4)):
        w = p.whisk
        end = (root[0] - hx * back - hdx * ln, root[1] - hy * back - hdy * ln + w)
        wl.line((math.floor(root[0]), math.floor(root[1])), (math.floor(end[0]), math.floor(end[1])), GOLD.base,
                name="whisker")
    return pts, radii


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    g = cv.gy - 1  # water surface row (the outline row)
    cv.opacity = p.fade
    if p.flop:
        M = (cv.gx - 1, g - 4.0)
        with cv.xform(px.scale(1.0, 0.9, (M[0], g))):
            pts, radii = _fish(cv, M, -4, 0.8, p)
    else:
        M = (cv.gx - 2 + p.mx, g - p.my)
        pts, radii = _fish(cv, M, p.ang, p.k, p)
    # everything below the surface is hidden: the fish is cut by the water line
    cv.rect(0, g, cv.w, cv.h - g, SCALE, erase=True)
    runs, x = [], 0
    row = cv.filled[g - 1]
    while x < cv.w:
        if row[x]:
            x0 = x
            while x < cv.w and row[x]:
                x += 1
            runs.append((x0, x))
        x += 1
    back = cv.layer(above=False, outline=True)
    front = cv.layer(above=True, outline=True)
    for x0, x1 in runs:  # a ripple ring around each place the body breaks the surface
        c = (x0 + x1) / 2.0
        w = (x1 - x0) / 2.0 + 3.0
        hb.ripple(back, c, g, w, WATER)
        m = front.mask_ellipse(c, g, w, max(1.0, w * 0.22)) & ~front.mask_ellipse(c, g - 0.35, max(0.5, w - 1.6),
                                                                                  max(0.4, w * 0.22 - 0.9))
        m &= front.Y > g + 0.2
        front.fill(m, WATER, normals=(front.X * 0, front.X * 0 - 1.0, front.X * 0 + 0.5), shade="soft",
                   name="ripple")
    if p.splash is not None:
        sx, t = p.splash
        px.splash(front, cv.gx - 2 + sx, g, t, size=0.9)
    if p.whoosh:  # the spin: a pale dashed arc trailing the tail
        streak = cv.layer(above=False, outline=False)
        for k in range(5):
            a0 = math.radians(-40 + k * 26)
            a1 = math.radians(-40 + k * 26 + 10)
            q0 = (M[0] + math.cos(a0) * 16.0, M[1] - math.sin(a0) * 14.0)
            q1 = (M[0] + math.cos(a1) * 16.0, M[1] - math.sin(a1) * 14.0)
            streak.line((math.floor(q0[0]), math.floor(q0[1])), (math.floor(q1[0]), math.floor(q1[1])),
                        px.MIST_BLUE if k % 2 else px.PAPER, name="whoosh")
    if p.hit:
        tail = pts[0]
        top = cv.layer(above=True, outline=False)
        px.impact(top, tail[0] + 2, tail[1] + 2, size=3)
