"""Nebula eel - a ribbon eel that swims through the nebula clouds of the Lantern Star Field
(Water / Space).

View: side, facing right, flying (cell 192, anchor at the body centre).  ~75 art px along the
body (59 px of ribbon body + a 16 px head), laid in an S-curve about 70 px wide and ~28 px
tall with its fins (the player is ~45).
Rig: the spine is integrated backward from the neck ``N`` by arc length, so a travelling
sine of the tangent angle gives the S-wave without changing the body length; the head rides
on the neck direction (``head`` tilts it).
Parts, back to front: speed streaks (FX, behind), translucent dorsal and belly fins running
the length of the body (pale violet membrane, darker rays, bright rim, meeting in a paddle at
the tail tip), the ribbon body (deep teal with magenta nebula clouds drifting over the back and
star specks), a small translucent pectoral fin, then the head (hinged wide lower jaw, dark
violet gape, pale fangs, gill slits, a magenta crown patch) and the glowing cyan eye in a dark
socket.
Idle: a slow S-wave rolls along the body, fins ripple, 1 px bob.  Walk: swims forward, a
stronger wave travels from head to tail.  Windup: coils back into a tight S, jaws gape, the
eyes flare with cyan rays (held).  Attack: a lunging bite that straightens the body, the jaws
snap shut on frame 1 with a small void-ripple in front of the snout.  Hurt: the body jerks
into a kink and star specks scatter off it.  Death: a last jolt, then the ribbon unravels from
the tail into teal and magenta nebula wisps that drift apart and fade.
"""
import math

import numpy as np

import helpers_batch_a as ha
import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "nebula_eel",
    "cell": 192,
    "anchor": [96, 96],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette (5 ramps): nebula teal hide, magenta nebula clouds, pale violet fin membrane,
# ivory fangs; accents: cyan eye glow, star specks, void violet ------------------------------
TEAL = px.material("neel_teal", "#86ecd9", "#2b9fa8", "#1d6585", "#223a6a", outline="#080b22",
                   thresholds=(0.9, 0.55, 0.18))
MAG = px.material("neel_mag", "#ffa8dd", "#cf4fa0", "#8b2f88", "#4b2366", outline="#12071d",
                  thresholds=(0.9, 0.55, 0.18))
FIN = px.material("neel_fin", "#d9ceff", "#6d5ec2", "#56499f", "#3b3282", outline="#0d0a26")
FIN_RAY = px.rgb("#a393ec")
FANG = px.material("neel_fang", "#fffaf0", "#efe6cf", "#c4b8a2", "#8f846f", outline="#1a1320")
MOUTH = px.rgb("#2a0f33")
SOCKET = px.rgb("#141238")
EYE_C = px.rgb("#8ffcff")
EYE_W = px.rgb("#ffffff")
EYE_H = px.rgb("#3fd2e6")
STAR_W = px.rgb("#fff8e0")
STAR_C = px.rgb("#c4f7ff")
STAR_G = px.rgb("#ffe6a1")
VOID_D = px.rgb("#3a1760")
VOID_M = px.rgb("#9a5ce6")
VOID_L = px.rgb("#efe2ff")

L_BODY = 59.0  # arc length of the body, tail tip -> neck
STEP = 0.5
TAU = 2 * math.pi

# ---- poses ------------------------------------------------------------------------------------
# bx, by   neck offset from its rest point            ang  body pitch (deg, + = nose up)
# amp, ph  travelling-wave amplitude (deg) and phase   wl  wavelength (px of arc length)
# k        curvature (deg / px; + droops the tail, - lifts it)
# head     head tilt on top of the neck direction (deg)    jaw  gape 0..1
# eye      open|angry|flare|squeeze|dead    fin  fin ripple phase
# streak   lunge speed streaks      ripple  void-ripple life (None | 1 = hit | 0.5 = fading)
# scatter  star specks thrown off (None | life 0..1)   unravel  0..1 (death: ribbon -> wisps)
# fade     stepped opacity
DEFAULTS = dict(bx=0.0, by=0.0, ang=0.0, amp=56.0, ph=0.0, wl=56.0, k=0.0, head=0.0, jaw=0.0, eye="open",
                fin=0.0, streak=False, ripple=None, scatter=None, unravel=0.0, fade=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # a slow S-wave rolls down the ribbon, fins ripple, 1 px bob
        dict(ph=0.0, fin=0.0),
        dict(ph=TAU / 4, fin=1.0, by=-1),
        dict(ph=TAU / 2, fin=2.0, by=-1, head=-2),
        dict(ph=TAU * 3 / 4, fin=3.0, head=-1),
    ],
    "walk": [  # swimming: a stronger wave travels from head to tail, the head dips and rises
        dict(ph=0.0, amp=62, wl=52, fin=0.0, ang=-2, head=0),
        dict(ph=TAU / 6, amp=62, wl=52, fin=1.0, ang=-2, by=-1, head=-2),
        dict(ph=TAU * 2 / 6, amp=62, wl=52, fin=2.0, ang=-2, by=-1, head=-3),
        dict(ph=TAU * 3 / 6, amp=62, wl=52, fin=3.0, ang=-2, head=-1),
        dict(ph=TAU * 4 / 6, amp=62, wl=52, fin=4.0, ang=-2, by=1, head=1),
        dict(ph=TAU * 5 / 6, amp=62, wl=52, fin=5.0, ang=-2, by=1, head=1),
    ],
    "windup": [  # coils back into a tight S, jaws gape, eyes flare - held on the last frame
        dict(bx=-2, ph=0.6, amp=60, wl=46, head=8, jaw=0.4, eye="angry", fin=1.0, ang=4),
        dict(bx=-4, ph=0.9, amp=68, wl=40, head=14, jaw=0.8, eye="flare", fin=2.0, ang=6, by=-1),
        dict(bx=-5, ph=1.0, amp=72, wl=38, head=17, jaw=1.0, eye="flare", fin=2.5, ang=7, by=-1),
    ],
    "attack": [  # the lunge: the body straightens, the jaws snap shut on frame 1 (void-ripple)
        dict(bx=4, ph=2.0, amp=38, wl=60, head=-4, jaw=1.0, eye="angry", fin=3.0, streak=True, ang=-3),
        dict(bx=7, ph=2.4, amp=32, wl=66, head=-6, jaw=0.15, eye="angry", fin=4.0, streak=True, ripple=1.0,
             ang=-3),
        dict(bx=5, ph=2.9, amp=40, wl=60, head=-3, jaw=0.35, eye="angry", fin=5.0, ripple=0.5, ang=-2),
        dict(bx=2, ph=3.4, amp=50, wl=58, head=-1, jaw=0.1, fin=6.0),
    ],
    "hurt": [  # jerks into a kink, star specks scatter off the body
        dict(bx=-3, by=-2, ph=1.0, amp=50, k=0.7, head=22, jaw=0.6, eye="squeeze", fin=2.0, ang=6, scatter=0.35),
        dict(bx=-1, by=-1, ph=1.4, amp=48, k=0.4, head=10, jaw=0.3, eye="squeeze", fin=3.0, ang=3, scatter=0.8),
    ],
    "death": [  # a last jolt, then the ribbon unravels from the tail into drifting nebula wisps
        dict(bx=-3, by=-2, ph=1.0, amp=52, k=0.8, head=24, jaw=0.8, eye="squeeze", fin=2.0, ang=6,
             scatter=0.3),
        dict(bx=2, by=2, ph=1.6, amp=34, k=-0.1, head=-10, jaw=0.5, eye="dead", fin=3.0, ang=-5, unravel=0.35),
        dict(bx=3, by=4, ph=1.8, amp=34, k=-0.1, head=-14, jaw=0.45, eye="dead", fin=3.5, ang=-5,
             unravel=0.65),
        dict(bx=4, by=5, ph=2.0, amp=34, k=-0.1, head=-16, jaw=0.4, eye="dead", fin=4.0, ang=-5, unravel=0.9,
             fade=0.6),
        dict(bx=4, by=5, ph=2.2, amp=34, k=-0.1, head=-16, jaw=0.4, eye="dead", fin=4.5, ang=-5, unravel=1.0,
             fade=0.3),
    ],
})

# body radius along the ribbon, t = 0 tail tip .. 1 neck
PROFILE = ((0.0, 0.6), (0.12, 1.5), (0.35, 2.6), (0.65, 3.1), (0.9, 3.4), (1.0, 3.6))
# star specks on the body: (t along the body, v across it -1 belly .. +1 back, kind)
BODY_STARS = ((0.2, 0.3, 0), (0.31, -0.35, 1), (0.42, 0.45, 2), (0.5, -0.2, 0), (0.6, 0.3, 1),
              (0.7, -0.45, 0), (0.79, 0.35, 2), (0.87, -0.15, 1))
# magenta nebula clouds drifting over the back: (t0, t1, offset toward the back, thickness)
CLOUDS = ((0.12, 0.3, 0.4, 0.55), (0.48, 0.64, 0.45, 0.55), (0.8, 0.9, 0.5, 0.45))


def _radius(t):
    for (t0, r0), (t1, r1) in zip(PROFILE, PROFILE[1:]):
        if t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return PROFILE[-1][1]


def _theta(u, p):
    """Tangent angle (deg, toward the head) at arc length ``u`` from the tail tip."""
    t = u / L_BODY
    env = (0.55 + 0.45 * (1.0 - t)) * min(1.0, (L_BODY - u) / 8.0)  # the neck stays steady
    return p.ang + p.k * (L_BODY - u) + p.amp * env * math.sin(p.ph + TAU * u / p.wl)


def _spine(N, p):
    """Spine points (tail tip -> neck), integrated backward from the neck ``N``."""
    x, y = N
    pts = [(x, y)]
    n = int(L_BODY / STEP)
    for i in range(n):
        th = math.radians(_theta(L_BODY - (i + 0.5) * STEP, p))
        x -= STEP * math.cos(th)
        y += STEP * math.sin(th)
        pts.append((x, y))
    return pts[::-1]


def _frame(sp):
    """Per-sample t, radius and 'back' normal (left of travel = up for a right-going body)."""
    n = len(sp)
    ts = [k / (n - 1) for k in range(n)]
    rs = [_radius(t) for t in ts]
    ns = [ha.normal_at(sp, k) for k in range(n)]
    return ts, rs, ns


def _at(sp, ns, rs, k, v):
    return (sp[k][0] + ns[k][0] * rs[k] * v, sp[k][1] + ns[k][1] * rs[k] * v)


# ---- parts ------------------------------------------------------------------------------------
def _fin(cv, sp, ts, rs, ns, p, side, k0, k1, height, name):
    """A continuous translucent fin along the body between samples k0..k1 (side +1 back,
    -1 belly): membrane, darker rays, a bright rim just inside the outline."""
    if k1 - k0 < 3:
        return
    outer, inner, rays = [], [], []
    for j, k in enumerate(range(k0, k1 + 1)):
        t = ts[k]
        ph = (k % 8) / 8.0  # a ray every 4 px; the membrane dips between the ray tips
        scallop = 0.78 + 0.22 * abs(math.cos(math.pi * ph))
        h = height(t) * scallop * (1.0 + 0.14 * math.sin(p.fin * 1.3 + t * 15.0 + side))
        nx, ny = ns[k]
        outer.append((sp[k][0] + side * nx * (rs[k] + h), sp[k][1] + side * ny * (rs[k] + h)))
        inner.append((sp[k][0] + side * nx * (rs[k] - 1.3), sp[k][1] + side * ny * (rs[k] - 1.3)))
        if k % 8 == 0 and h > 1.6:
            rays.append(j)
    cv.polygon(outer + inner[::-1], FIN, shade="two", name=name)
    # pale rays, raked back toward the tail, running out to the scallop points
    for j in rays:
        a = inner[j]
        b = outer[max(0, j - 2)]
        cv.line((math.floor(px.lerp_pt(a, b, 0.45)[0]), math.floor(px.lerp_pt(a, b, 0.45)[1])),
                (math.floor(px.lerp_pt(a, b, 0.92)[0]), math.floor(px.lerp_pt(a, b, 0.92)[1])), FIN_RAY,
                decal=True, clip=name, name=name)
    # a thin bright rim along the free edge: the membrane catches the starlight
    edge = cv.mask_of(name) & ~px.erode(cv.mask_of(name)) & ~cv.mask_of("body")
    far = np.zeros_like(edge)
    for k in range(len(outer)):
        far |= cv.mask_ellipse(outer[k][0], outer[k][1], 1.6, 1.6)
    edge &= far
    cv._commit(edge, np.where(edge, 0, -1).astype(np.int8), px.flat(FIN.light, outline=FIN.outline), name=name)


def _dorsal_h(t):
    if t > 0.95:
        return 0.0
    rise = min(1.0, 0.4 + t * 2.0)
    fall = min(1.0, (0.97 - t) / 0.14)
    return 5.2 * rise * fall


def _ventral_h(t):
    if t > 0.62:
        return 0.0
    rise = min(1.0, 0.4 + t * 2.4)
    fall = min(1.0, (0.64 - t) / 0.16)
    return 4.4 * rise * fall


def _body(cv, sp, ts, rs, ns, k_cut):
    """The ribbon tube from sample k_cut to the neck, nebula clouds and star specks as decals."""
    idx = list(range(k_cut, len(sp), 2))
    if idx[-1] != len(sp) - 1:
        idx.append(len(sp) - 1)
    if len(idx) < 2:
        return
    cv.limb([sp[k] for k in idx], [rs[k] for k in idx], TEAL, name="body")
    n = len(sp)
    for (t0, t1, off, th) in CLOUDS:
        ks = [k for k in range(n) if t0 <= ts[k] <= t1 and k >= k_cut]
        if len(ks) < 4:
            continue
        pts, rad = [], []
        for j, k in enumerate(ks[::2]):
            s = j / max(1, len(ks[::2]) - 1)
            wob = 0.18 * math.sin(s * 9.0 + t0 * 20.0)
            pts.append(_at(sp, ns, rs, k, off + wob))
            rad.append(max(0.6, rs[k] * th * math.sin(math.pi * min(1.0, 0.12 + s * 0.88)) ** 0.5))
        cv.limb(pts, rad, MAG, decal=True, clip="body", name="body")
    for t, v, kind in BODY_STARS:
        k = int(round(t * (n - 1)))
        if k < k_cut + 2:
            continue
        x, y = _at(sp, ns, rs, k, v)
        x, y = math.floor(x), math.floor(y)
        if kind == 2:  # a little four-point star
            cv.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], STAR_G, decal=True, clip="body", name="body")
            cv.pixel(x, y, STAR_W, decal=True, clip="body", name="body")
        else:
            cv.pixel(x, y, STAR_W if kind == 0 else STAR_C, decal=True, clip="body", name="body")


def _pectoral(cv, sp, rs, ns, p):
    k = int(len(sp) * 0.9)
    nx, ny = ns[k]
    tx, ty = -ny, nx  # along the body toward the head is (-ny, nx) for the 'up' normal (dy, -dx)
    base = _at(sp, ns, rs, k, -0.25)
    back = _at(sp, ns, rs, k - 12, -0.35)
    sway = math.sin(p.fin * 1.4) * 1.2
    tip = (base[0] - tx * 6.5 - nx * (4.0 + sway), base[1] - ty * 6.5 - ny * (4.0 + sway))
    tip2 = (base[0] - tx * 8.0 - nx * (1.8 + sway), base[1] - ty * 8.0 - ny * (1.8 + sway))
    cv.polygon([base, tip, tip2, back], FIN, shade="two", name="pec", sep="deep")
    cv.line((math.floor(base[0]), math.floor(base[1])), (math.floor(tip[0]), math.floor(tip[1])), FIN.step(1),
            decal=True, clip="pec", name="pec")


def _head(cv, N, deg, p):
    """Skull + snout as one form, hinged wide lower jaw, gape, fangs.  Returns the eye and
    snout-tip points in canvas space."""
    X, Y = N

    def L(x, y):
        return (X + x, Y + y)

    with cv.xform(px.rotate(deg, N), px.scale(1.12, 1.12, N)):
        hinge = L(1.5, 2.2)
        ja = -36.0 * p.jaw
        with cv.xform(px.rotate(ja, hinge)):
            cv.limb([hinge, L(7.5, 3.6), L(12.8, 3.2)], [3.1, 2.4, 1.3], TEAL, shade="nolight", name="jaw")
            if p.jaw > 0.2:  # lower fangs
                for x in (7.3, 10.3):
                    cv.pixels([(math.floor(X + x), math.floor(Y + 1.2)), (math.floor(X + x), math.floor(Y + 2.2))],
                              FANG.base, name="fang")
            lo_lip = [cv.tp(L(12.8, 2.0)), cv.tp(L(5.0, 1.8))]
        skull = cv.union(cv.geom_ellipse(X + 4.2, Y - 0.9, 6.3, 4.7),
                         cv.geom_limb([L(5.5, -0.4), L(9.5, 0.2), L(13.4, 1.0)], [3.9, 3.0, 2.1]),
                         weights=[1.0, 0.8])
        cut = cv.mask_polygon([L(1.0, 2.2), L(20.0, 1.8), L(20.0, 12.0), L(1.0, 12.0)]) if p.jaw > 0.2 else None
        cv.draw_geom(skull, TEAL, name="skull", sep="deep", minus=cut)
        # magenta nebula patch on the crown, gill slits
        cv.ellipse(X + 2.6, Y - 3.4, 4.2, 1.9, MAG, angle=8, decal=True, clip="skull", name="skull")
        for dx in (-1.2, 0.4):
            cv.limb([L(dx + 0.5, -2.4), L(dx - 0.2, 0.0), L(dx + 0.4, 2.2)], 0.45, TEAL.step(2), decal=True,
                    clip="skull", name="skull")
        up_lip = [cv.tp(L(5.0, 2.1)), cv.tp(L(13.2, 1.9))]
        if p.jaw > 0.2:  # dark gape between the jaws
            with cv.xform(np.linalg.inv(cv.M)):
                cv.polygon([cv.tp(hinge)] + up_lip + lo_lip, px.flat(MOUTH), under=True, name="mouth")
        else:  # the long closed mouth line reaching back under the eye
            cv.line((math.floor(X + 2.5), math.floor(Y + 2.2)), (math.floor(X + 12.0), math.floor(Y + 2.0)),
                    TEAL.deep, decal=True, clip=["skull", "jaw"], name="skull")
        # upper fangs hanging over the lip (pale against the gape or the lower jaw)
        for x, ln in ((6.2, 2), (8.9, 3), (11.3, 2)):
            pts = [(math.floor(X + x), math.floor(Y + 2.0 + j)) for j in range(ln if p.jaw > 0.2 else 2)]
            cv.pixels(pts, FANG.base, name="fang")
        eye_at = cv.tp(L(7.8, -2.3))
        snout = cv.tp(L(14.5, 1.8))
    return eye_at, snout


def _eye(cv, E, p):
    x, y = math.floor(E[0]) - 1, math.floor(E[1]) - 1
    if p.eye == "dead":
        cv.stamp(["k.k", ".k.", "k.k"], x, y, {"k": TEAL.deep}, name="eye")
        return
    if p.eye == "squeeze":
        cv.stamp(["h..", ".hh", "h.."], x, y, {"h": EYE_H}, name="eye")
        return
    if p.eye == "flare":  # a bigger, white-hot eye
        cv.stamp([".sss.", "swwcs", "swccs", "scccs", ".sss."], x - 1, y - 1,
                 {"s": SOCKET, "w": EYE_W, "c": EYE_C}, name="eye")
    else:
        cv.stamp([".ss.", "swcs", "sccs", ".ss."], x, y, {"s": SOCKET, "w": EYE_W, "c": EYE_C}, name="eye")
    if p.eye in ("angry", "flare"):
        cv.pixels([(x - 1, y - 1), (x, y - 1), (x + 1, y), (x + 2, y), (x + 3, y + 1)], SOCKET, name="brow")


def _eye_rays(fx, E, frame):
    cx, cy = math.floor(E[0]) + 0.5, math.floor(E[1]) + 0.5
    for k, a in enumerate((150, 100, 45, 200)):
        r0, r1 = 3.5, 6.5 + (1.0 if (k + frame) % 2 else 0.0)
        a0 = px.polar((cx, cy), a, r0)
        a1 = px.polar((cx, cy), a, r1)
        fx.line((math.floor(a0[0]), math.floor(a0[1])), (math.floor(a1[0]), math.floor(a1[1])),
                EYE_H if k % 2 else EYE_C, name="ray")


def _void_ripple(fx, c, life):
    """A small ripple in space: a ring of violet with a bright lip and a void core."""
    d = np.hypot((fx.X - c[0]) / 0.8, fx.Y - c[1])
    if life >= 1.0:
        rings = ((6.6, VOID_M), (5.5, VOID_L), (3.2, VOID_M))
        core = d <= 2.3
        fx._commit(core, np.where(core, 1, -1).astype(np.int8), px.flat(VOID_D), name="void")
        spot = (np.abs(fx.X - c[0]) < 0.6) & (np.abs(fx.Y - c[1]) < 0.6)
        fx._commit(spot, np.where(spot, 1, -1).astype(np.int8), px.flat(EYE_W), name="void")
    else:
        rings = ((8.2, VOID_M), (6.6, VOID_D))
    for r, col in rings:
        m = np.abs(d - r) <= 0.55
        if life < 1.0:  # the fading ripple breaks up into arcs (no lone pixels at the breaks)
            ang = np.degrees(np.arctan2(-(fx.Y - c[1]), fx.X - c[0])) % 360
            m &= (ang % 90) < 58
            nb = np.zeros(m.shape, np.int16)
            for dx, dy in px.N8:
                nb += px._shift(m, dx, dy, False)
            m &= nb >= 1
        fx._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(col), name="void")


def _strands(cv, sp, ts, rs, ns, k_cut, p, frame):
    """The unravelled rear of the ribbon: teal, magenta and violet strands that curl apart,
    billow into little nebula clouds and drift upward, breaking up as they thin out."""
    if k_cut < 4:
        return
    tc = ts[k_cut]
    broken = p.unravel >= 0.85
    for j, (side, mat, rad) in enumerate(((1, MAG, 1.6), (-1, TEAL, 1.7), (0.3, FIN, 1.2))):
        pts, radii = [], []
        for k in range(k_cut, -1, -3):
            d = (tc - ts[k]) / max(0.05, tc)  # 0 at the fraying point, 1 at the old tail tip
            spread = (1.0 + 6.0 * d * p.unravel) * side
            curl = (1.0 + 3.5 * d) * math.sin(p.ph * 1.7 + d * 7.0 + j * 2.1) * min(1.0, d * 3.0)
            x = sp[k][0] + ns[k][0] * (spread + curl) - 1.5 * d * p.unravel
            y = sp[k][1] + ns[k][1] * (spread + curl) - 7.0 * d * d * p.unravel
            pts.append((x, y))
            radii.append(max(0.6, rad * (1.0 - 0.45 * d)))
        if len(pts) < 2:
            continue
        if broken:  # the strands break into drifting shreds
            for i0 in range(0, len(pts) - 1, 4):
                seg = pts[i0:i0 + 3]
                if len(seg) >= 2 and (i0 // 4 + j) % 3 != 2:
                    cv.limb(seg, radii[i0:i0 + 3], mat, shade="soft", name="wisp")
        else:
            cv.limb(pts, radii, mat, shade="soft", name="wisp")
        # nebula puffs billowing out of the strand
        for i in range(2 + j, len(pts) - 1, 5):
            r = radii[i] + 0.6 + 1.2 * p.unravel * (0.5 + 0.5 * math.sin(i * 1.7 + j))
            cv.circle(pts[i][0], pts[i][1] - 0.5 * p.unravel, r, mat, shade="soft", name="wisp")
    # a few freed stars drifting among the wisps
    for i in range(3):
        k = int(k_cut * (0.25 + 0.3 * i))
        x, y = sp[k]
        x, y = math.floor(x - 3 + i * 2), math.floor(y - 6 - 5 * p.unravel - i)
        cv.pixels([(x, y), (x + 1, y)], STAR_W if i % 2 else STAR_C, name="wisp")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    N = (cv.gx + 12.0 + p.bx, cv.gy - 1.5 + p.by)
    sp = _spine(N, p)
    ts, rs, ns = _frame(sp)
    n = len(sp)
    k_cut = int(round(min(1.0, p.unravel) * (n - 1))) if p.unravel > 0 else 0
    back = cv.layer(above=False, outline=False)

    if p.streak:  # speed streaks trailing off the tail and the fin edges
        tail = sp[0]
        for j, (dy, ln, x0) in enumerate(((-6, 8, 3), (0, 11, 2), (6, 7, 4))):
            y = math.floor(tail[1] + dy)
            back.line((math.floor(tail[0] - x0), y), (max(3, math.floor(tail[0] - x0 - ln)), y),
                      STAR_C if j != 1 else FIN.light, name="streak")

    if p.unravel < 0.999:
        # fins behind the body (they fray away with the ribbon)
        k0 = max(1, k_cut)
        _fin(cv, sp, ts, rs, ns, p, 1, k0, int((n - 1) * 0.95), _dorsal_h, "dfin")
        _fin(cv, sp, ts, rs, ns, p, -1, k0, int((n - 1) * 0.62), _ventral_h, "vfin")
        _body(cv, sp, ts, rs, ns, k_cut)
        _pectoral(cv, sp, rs, ns, p)
    # the head rides on the neck direction
    d = (sp[-1][0] - sp[-7][0], sp[-1][1] - sp[-7][1])
    hdeg = math.degrees(math.atan2(-d[1], d[0])) + p.head
    eye_at, snout = None, None
    if p.unravel < 0.95:
        eye_at, snout = _head(cv, N, hdeg, p)
        _eye(cv, eye_at, p)
    if p.unravel > 0.6:  # the head frays too: holes open, crumbs are swept away
        with cv.xform(px.rotate(hdeg, N)):
            s = (p.unravel - 0.6) / 0.4
            hc.erase_blobs(cv, [(N[0] + 3.0, N[1] - 1.0, 2.2 * s + 0.8), (N[0] + 9.0, N[1] + 1.5, 1.8 * s),
                                (N[0] - 1.0, N[1] + 2.0, 2.4 * s)])
        hc.drop_specks(cv, 4)
    if p.unravel > 0:
        _strands(cv, sp, ts, rs, ns, max(k_cut, 8) if p.unravel < 0.999 else n - 1, p, frame)

    # ---- FX ----
    if p.eye == "flare" and eye_at is not None:
        _eye_rays(cv.layer(above=True, outline=False), eye_at, frame)
    if p.ripple is not None and snout is not None:
        fx = cv.layer(above=True, outline=False)
        c = (snout[0] + 1.5, snout[1])
        _void_ripple(fx, c, p.ripple)
        if p.ripple >= 1.0:
            px.impact(fx, c[0] + 0.5, c[1] - 0.5, size=3, color=VOID_L, core=EYE_W)
    if p.scatter is not None:
        fx = cv.layer(above=True, outline=False)
        for j, t in enumerate((0.3, 0.55, 0.8)):
            k = int(t * (n - 1))
            x, y = _at(sp, ns, rs, k, 1.0 if j % 2 == 0 else -1.0)
            hc.sparks(fx, x, y, p.scatter, n=3, radius=8.0, colors=(STAR_W, STAR_C if j % 2 else STAR_G),
                      seed=j + 3, spread=140, aim=100 if j % 2 == 0 else 250)
