"""Hollowed eel - a huge river eel drained grey by the Hollow, rising in an S-curve from
dark water (Hollow element, event creature, invulnerable in the story, cell 256).

View: side, facing right, ~100 art px tall including the pool, on a 128 px canvas.
Flying (the engine hovers it); anchored at the body centre.
Parts, back to front: dark Hollow pool (far half), tube body along a smooth S spine
(Catmull-Rom through a few control points per pose) with a pale belly stripe, a ragged
torn dorsal fin running up the back, gill slits, a ragged pectoral fin, the head (skull
+ long snout shaded as one form, a hinged lower jaw with jagged teeth, empty glowing
white eyes with a cold halo), then the pool's near half, ripples and grey mist.
Everything below the waterline is hidden.  Death: it sinks back into the water.
"""
import math

import numpy as np

import helpers_batch_a as hb
import pixel as px

SPEC = {
    "id": "hollowed_eel",
    "cell": 256,
    "anchor": [112, 140],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: dark-ish Hollow grey (so the huge body is not a white blob), pale belly -----
BODY = px.material("heel_body", "#cfd6d3", "#96a2a6", "#6b7880", "#48545d", outline="#0f151a",
                   thresholds=(0.86, 0.52, 0.2))
BELLY = px.material("heel_belly", "#eef0e9", "#c9d0cd", "#9fabad", "#76838a", outline="#0f151a")
FIN = px.material("heel_fin", "#a9b3b7", "#78848b", "#58646c", "#3f4a52", outline="#0c1116")
FOG = px.material("heel_fog", "#e8ecea", "#c3cccd", "#9ea9ad", "#7c878d", outline="#4a565e")
POOL = px.material("heel_pool", "#8d9ca3", "#3c4953", "#2c3740", "#1f2830", outline="#070b0e")
MOUTH = px.rgb("#1d2328")
TOOTH = px.rgb("#eef0e6")
GILL = BODY.step(2)
RIPPLE_HI = px.rgb("#b7c4c8")
RIPPLE_LO = px.rgb("#56646d")

W0 = (44.0, 112.0)  # where the body meets the water (pool centre line)
POOL_RX, POOL_RY = 40.0, 5.0

# ---- poses --------------------------------------------------------------------------------
# ctrl    spine control points relative to W0, tail (under water) -> head centre
# wave    extra travelling-wave amplitude / phase along the body (undulation)
# head    head tilt (deg, + nose up) on top of the spine direction   jaw  gape 0..1
# eye     open|wide|squeeze|dead    sink  body lowered into the water (px)
# fin     fin flutter phase         mist  mist life offset      fade  opacity   hit  impact
IDLE = ((0, 8), (-6, -12), (8, -32), (20, -50), (12, -70), (24, -84))
DEFAULTS = dict(ctrl=IDLE, wave=(0.0, 0.0), head=0, jaw=0.0, eye="open", sink=0.0, fin=0.0, mist=0.0,
                fade=1.0, hit=False, rings=(14.0,), splash=None)


def _c(*pts):
    return tuple(pts)


POSE = px.poses(DEFAULTS, {
    "idle": [  # slow sway above the water, fin rippling, mist drifting
        dict(ctrl=_c((0, 8), (-6, -12), (8, -32), (20, -50), (12, -70), (24, -84)), fin=0.0, rings=(12.0,)),
        dict(ctrl=_c((0, 8), (-5, -12), (9, -32), (21, -50), (13, -70), (25, -83)), fin=1.0, head=-2,
             rings=(16.0,)),
        dict(ctrl=_c((0, 8), (-4, -12), (10, -32), (21, -50), (14, -70), (26, -83)), fin=2.0, head=-3,
             rings=(20.0,)),
        dict(ctrl=_c((0, 8), (-5, -12), (9, -32), (20, -50), (13, -70), (25, -84)), fin=3.0, head=-1,
             rings=(24.0,)),
    ],
    "walk": [  # undulating: a wave rolls up the body
        dict(wave=(3.0, 0.0), fin=0.0, rings=(12.0,)),
        dict(wave=(3.0, 1.05), fin=1.0, head=-2, rings=(16.0,)),
        dict(wave=(3.0, 2.1), fin=2.0, head=-3, rings=(20.0,)),
        dict(wave=(3.0, 3.14), fin=3.0, head=-2, rings=(24.0,)),
        dict(wave=(3.0, 4.19), fin=4.0, head=0, rings=(28.0,)),
        dict(wave=(3.0, 5.24), fin=5.0, head=1, rings=(32.0,)),
    ],
    "windup": [  # rears back into a tight coil, jaws gaping, eyes flaring - the long tell
        dict(ctrl=_c((0, 8), (-4, -14), (10, -32), (16, -50), (6, -68), (14, -84)), head=12, jaw=0.5,
             eye="wide", fin=1.0),
        dict(ctrl=_c((0, 8), (-2, -16), (12, -32), (12, -50), (0, -66), (4, -84)), head=24, jaw=0.9,
             eye="wide", fin=2.0),
        dict(ctrl=_c((0, 8), (-1, -16), (13, -32), (11, -50), (-2, -66), (2, -85)), head=28, jaw=1.0,
             eye="wide", fin=2.5, rings=(18.0, 30.0)),
    ],
    "attack": [  # the lunge: the body whips straight toward the target, jaws slam (frame 1)
        dict(ctrl=_c((0, 8), (-4, -14), (10, -30), (23, -44), (35, -54), (46, -60)), head=-6, jaw=1.0, eye="wide",
             fin=3.0, splash=0.15),
        dict(ctrl=_c((0, 8), (-2, -14), (13, -28), (28, -40), (42, -48), (54, -51)), head=-12, jaw=0.1,
             eye="wide", fin=4.0, hit=True, splash=0.45),
        dict(ctrl=_c((0, 8), (-4, -13), (10, -30), (24, -46), (30, -64), (42, -74)), head=-4, jaw=0.4, fin=5.0,
             splash=0.8),
        dict(ctrl=_c((0, 8), (-6, -12), (8, -32), (20, -50), (14, -70), (26, -84)), head=0, jaw=0.1, fin=0.0),
    ],
    "hurt": [  # recoils: the head snaps back and up, eyes screwed shut
        dict(ctrl=_c((0, 8), (-5, -12), (10, -32), (16, -50), (4, -68), (8, -86)), head=26, jaw=0.6,
             eye="squeeze", fin=2.0),
        dict(ctrl=_c((0, 8), (-6, -12), (9, -32), (18, -50), (9, -70), (18, -85)), head=12, jaw=0.3,
             eye="squeeze", fin=3.0),
    ],
    "death": [  # shudders, slumps and sinks back beneath the grey water
        dict(ctrl=_c((0, 8), (-5, -12), (10, -32), (16, -50), (4, -68), (8, -86)), head=26, jaw=0.7,
             eye="squeeze", fin=2.0),
        dict(ctrl=_c((0, 8), (-6, -12), (6, -30), (18, -44), (20, -60), (32, -66)), head=-24, jaw=0.5,
             eye="dead", sink=18.0, fin=3.0, rings=(20.0,)),
        dict(ctrl=_c((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54)), head=-32, jaw=0.4,
             eye="dead", sink=42.0, fin=4.0, rings=(16.0, 28.0)),
        dict(ctrl=_c((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54)), head=-36, jaw=0.4,
             eye="dead", sink=62.0, fin=5.0, rings=(12.0, 24.0, 34.0), fade=0.6),
        dict(ctrl=_c((0, 8), (-6, -12), (6, -28), (18, -40), (24, -52), (36, -54)), head=-36, jaw=0.4,
             eye="dead", sink=90.0, fin=5.0, rings=(20.0, 32.0), fade=0.3),
    ],
})

# body radius along the spine, tail (0) -> neck (1)
PROFILE = ((0.0, 9.6), (0.3, 8.8), (0.6, 7.8), (0.85, 6.8), (1.0, 6.4))


def _radius(t):
    for (t0, r0), (t1, r1) in zip(PROFILE, PROFILE[1:]):
        if t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return PROFILE[-1][1]


def _spine(p):
    ctrl = [(W0[0] + x, W0[1] + y + p.sink) for x, y in p.ctrl]
    pts = hb.catmull(ctrl, per=5)
    amp, ph = p.wave
    if amp:
        out = []
        for k, q in enumerate(pts):
            t = k / (len(pts) - 1)
            nx, ny = hb.normal_at(pts, k)
            s = amp * math.sin(ph - t * 6.0) * min(1.0, t * 3) * (1.0 - t * 0.4)
            out.append((q[0] + nx * s, q[1] + ny * s))
        pts = out
    return pts


def _fin_strip(cv, sp, radii, p, k0, k1, height, side=1):
    """Continuous torn fin along the spine between samples k0..k1 on the dorsal side:
    an even sail with notches bitten out of its edge and a few dark fin rays."""
    outer = []
    for k in range(k0, k1 + 1):
        nx, ny = hb.normal_at(sp, k)
        t = (k - k0) / max(1, k1 - k0)
        env = math.sin(math.pi * min(1.0, t * 1.15)) ** 0.5
        notch = 0.55 if (k + int(p.fin)) % 4 == 0 else (0.85 if k % 3 == 1 else 1.0)
        wave = 0.8 * math.sin(k * 0.9 + p.fin * 1.1)
        h = max(1.0, height * env * notch + wave)
        r = radii[k] - 1.0
        outer.append((sp[k][0] + side * nx * (r + h), sp[k][1] + side * ny * (r + h)))
    inner = [(sp[k][0] + side * hb.normal_at(sp, k)[0] * (radii[k] - 2.0),
              sp[k][1] + side * hb.normal_at(sp, k)[1] * (radii[k] - 2.0)) for k in range(k1, k0 - 1, -1)]
    cv.polygon(outer + inner, FIN, shade="two", name="fin")
    for k in range(k0 + 2, k1 - 1, 3):  # fin rays
        nx, ny = hb.normal_at(sp, k)
        a = (sp[k][0] + side * nx * radii[k], sp[k][1] + side * ny * radii[k])
        b = (sp[k][0] + side * nx * (radii[k] + height * 0.6), sp[k][1] + side * ny * (radii[k] + height * 0.6))
        cv.limb([a, b], 0.45, FIN.step(1), decal=True, clip="fin")


def _head(cv, Hc, ang, p):
    """Skull + snout as one form, hinged lower jaw, teeth, eyes.  Local frame faces right."""
    with cv.xform(px.rotate(ang, Hc), px.scale(1.3, 1.3, Hc)):
        hinge = (Hc[0] + 1.0, Hc[1] + 3.2)
        jaw_a = -34.0 * p.jaw
        # lower jaw (drawn first, the skull overlaps its root)
        with cv.xform(px.rotate(jaw_a, hinge)):
            cv.limb([hinge, (Hc[0] + 8.0, Hc[1] + 4.2), (Hc[0] + 13.0, Hc[1] + 4.0)], [3.2, 2.4, 1.4], BODY,
                    shade="nolight", name="jaw")
            if p.jaw > 0.15:  # lower teeth
                for k in range(4):
                    x = Hc[0] + 5.0 + 2.1 * k
                    cv.pixels([(math.floor(x), math.floor(Hc[1] + 2.0))], TOOTH, name="tooth")
        skull = cv.union(cv.geom_ellipse(Hc[0], Hc[1], 7.2, 5.6),
                         cv.geom_limb([(Hc[0] + 3.0, Hc[1] + 0.2), (Hc[0] + 9.0, Hc[1] + 1.0), (Hc[0] + 14.0, Hc[1] + 1.6)],
                                      [4.6, 3.4, 2.0]),
                         weights=[1.0, 0.75])
        cut = cv.mask_polygon([(Hc[0] + 1.0, Hc[1] + 3.0), (Hc[0] + 20, Hc[1] + 2.4), (Hc[0] + 20, Hc[1] + 12),
                               (Hc[0] + 1.0, Hc[1] + 12)]) if p.jaw > 0.15 else None
        cv.draw_geom(skull, BODY, name="skull", sep="deep", minus=cut)
        if p.jaw > 0.15:  # dark gape between the jaws + upper teeth
            with cv.xform(px.rotate(jaw_a, hinge)):
                lo = [cv.tp((Hc[0] + 13.0, Hc[1] + 2.8)), cv.tp((Hc[0] + 6.0, Hc[1] + 2.4))]
            up = [cv.tp((Hc[0] + 6.0, Hc[1] + 2.6)), cv.tp((Hc[0] + 14.0, Hc[1] + 2.2))]
            with cv.xform(np.linalg.inv(cv.M)):
                cv.polygon([cv.tp(hinge)] + up + lo, px.flat(MOUTH), under=True, name="mouth")
            for k in range(4):
                x = Hc[0] + 5.5 + 2.1 * k
                cv.pixels([(math.floor(x), math.floor(Hc[1] + 2.8))], TOOTH, name="tooth")
        else:
            cv.line((math.floor(Hc[0] + 2), math.floor(Hc[1] + 3)), (math.floor(Hc[0] + 13), math.floor(Hc[1] + 3)),
                    BODY.step(2), decal=True, clip="skull")
        # gill slits behind the skull
        for dx in (-4.5, -6.2):
            cv.limb([(Hc[0] + dx + 0.6, Hc[1] - 2.0), (Hc[0] + dx - 0.2, Hc[1] + 0.5), (Hc[0] + dx + 0.4, Hc[1] + 3.0)],
                    0.45, GILL, decal=True, clip=["skull", "body"])
        # empty glowing eye with a cold halo
        ex, ey = math.floor(Hc[0] + 2.6), math.floor(Hc[1] - 2.8)
        state = {"wide": "wide", "open": "open"}.get(p.eye, p.eye)
        hb.eye_glow(cv, ex, ey, state=state, size=3 if state == "wide" else 2, halo=state in ("open", "wide"))
        if state in ("open", "wide"):
            hb.socket(cv, colour=BODY.deep)
            # heavy brow ridge
            cv.limb([(Hc[0] - 0.5, Hc[1] - 5.0), (Hc[0] + 3.5, Hc[1] - 4.6), (Hc[0] + 6.5, Hc[1] - 3.2)],
                    [0.9, 0.8, 0.6], BODY, shade="nolight", name="brow", clip="skull")
        tip = cv.tp((Hc[0] + 15.0, Hc[1] + 2.4))
    return tip


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    wl = W0[1]
    sp = _spine(p)
    n = len(sp)
    radii = [_radius(k / (n - 1)) for k in range(n)]
    Hc = sp[-1]
    d = (sp[-1][0] - sp[-3][0], sp[-1][1] - sp[-3][1])
    ang = math.degrees(math.atan2(-d[1], d[0])) + p.head
    body_pts = sp[:-1]
    # ragged dorsal fin up the back (behind the body), then the body tube
    _fin_strip(cv, sp, radii, p, 2, n - 4, 7.5, side=1)
    cv.limb(body_pts, radii[:-1], BODY, name="body")
    under = []
    for k in range(1, n - 2):
        nx, ny = hb.normal_at(sp, k)
        under.append((sp[k][0] - nx * radii[k] * 0.62, sp[k][1] - ny * radii[k] * 0.62))
    cv.limb(under, [r * 0.42 for r in radii[1:n - 2]], BELLY, shade="two", decal=True, clip="body")
    # ragged pectoral fin just behind the head
    k = n - 5
    nx, ny = hb.normal_at(sp, k)
    base = (sp[k][0] - nx * 2.0, sp[k][1] - ny * 2.0)
    back = (sp[k - 2][0] - nx * 3.0, sp[k - 2][1] - ny * 3.0)
    sway = math.sin(p.fin * 1.3) * 1.2
    tip1 = (base[0] - nx * 7.0 - 3.0 + sway, base[1] - ny * 7.0 + 2.0)
    tip2 = (base[0] - nx * 5.0 - 5.5 + sway, base[1] - ny * 5.0 + 3.5)
    cv.polygon([base, tip1, (tip1[0] - 1.0, tip1[1] + 2.0), tip2, back], FIN, shade="two", name="pecfin", sep="deep")
    tip = _head(cv, Hc, ang, p)
    # below the waterline nothing shows; the pool closes over it
    below = cv.filled & (cv.Y > wl)
    if below.any():
        cv.fill(below, px.flat("#000000"), erase=True)
        hb.clean_specks(cv, 3)
    P = (W0[0] + 18.0, wl)
    cv.ellipse(P[0], P[1], POOL_RX, POOL_RY, POOL, shade="flat", name="pool", under=True)
    cv.limb([(P[0] - POOL_RX + 5, P[1] - POOL_RY + 1.2), (P[0], P[1] - POOL_RY + 0.6), (P[0] + POOL_RX - 5, P[1] - POOL_RY + 1.2)],
            0.5, px.flat(RIPPLE_LO), decal=True, clip="pool")
    for r in p.rings:
        hb.ripple(cv, W0[0] + 1.0, wl, min(r, POOL_RX - 2), ry=POOL_RY - 1.0, colour=RIPPLE_HI, dim=RIPPLE_LO,
                  clip="pool")
    # a low bank of grey Hollow fog lying on the water around the body
    fog = cv.layer(above=False, outline=True)  # behind the body, on the far side of the pool
    drift = (frame % 4) * 0.5 * (1 if action in ("idle", "walk") else 0)
    for (fx_, fy_, rx, ry) in ((-27.0, -4.5, 6.5, 2.4), (-17.0, -6.0, 5.0, 2.2), (12.0, -5.5, 6.0, 2.2),
                               (24.0, -4.0, 5.0, 2.0)):
        fog.ellipse(P[0] + fx_ + drift, wl + fy_, rx, ry, FOG, shade="soft", name="fog")
    if p.splash is not None:
        fx = cv.layer(above=True, outline=True)
        px.splash(fx, W0[0] + 2.0, wl + 1.0, p.splash, size=1.4, mat=px.material(
            "heel_splash", "#eef2ef", "#c2ccd0", "#8e9ba2", "#66737b", outline="#2f3a42"))
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0] + 1.0, tip[1], size=5)
