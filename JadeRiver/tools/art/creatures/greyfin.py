"""Greyfin - a Hollow river fish that lurks in grey puddles and leaps to bite
(Hollow Water).

View: side, facing right.  ~30 art px long, ~11 deep; lives in a flat grey puddle
(~28 px wide) that is part of the body, so the sprite always touches the ground line.
Built with ``helpers_batch_a.hollow_fish`` (forked tail, ragged dorsal fin, dark back /
pale belly, gill arc, toothy hinged jaw, empty white eye in a dark socket).
Everything below the waterline is hidden; the submerged body shows as a dark shadow
inside the puddle.  FX: ripples, bubbles, grey splash crowns, dissolving mist, impact.
"""
import math

import numpy as np

import helpers_batch_a as hb
import pixel as px

SPEC = {
    "id": "greyfin",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 2,
}

LENGTH, HEIGHT = 30.0, 10.0
POOL_RX, POOL_RY = 14.0, 2.6
SPLASH = px.material("hollow_splash", "#f1f4f0", "#c5ced1", "#909da4", "#67747c", outline="#2f3a42")
POOL_RIM = px.rgb("#9aa8ae")
RIPPLE_NEAR = px.rgb("#7a8891")
POOL_SHADOW = px.rgb("#2e3a43")
POOL = px.material("hollow_pool", "#aebbc0", "#607079", "#44525c", "#2e3a43", outline="#0c1217")
TAU = 2 * math.pi

# fx, fy   fish centre relative to the pool centre (fy > 0 = below the surface)
# ang      pitch (deg, + nose up)   amp, ph  swim wave      tail  tail swing (deg)
# jaw      gape 0..1                fin  pectoral flap      eye  open|angry|wide|squeeze|dead
# dorsal   dorsal-fin height         ring  ripple rings: list of radii (0 = none)
# splash   splash life 0..1 at (sx) (None = off)   flip  belly-up    dis  dissolve 0..1
# mist     mist-puff life (None = off)   fade  opacity   hit  impact fx   wake  wake ripples
DEFAULTS = dict(fx=0.0, fy=7.0, ang=0, amp=0.4, ph=0.0, tail=0, jaw=0.0, fin=0, eye="open", dorsal=1.0,
                rings=(), bubbles=0, glint=False, splash=None, sx=0.0, flip=False, dis=0.0, mist=None, fade=1.0, hit=False, wake=0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # only the torn dorsal fin cuts the surface; lazy ripples
        dict(fx=0, fy=5.6, ph=0.0, rings=(6.0,)),
        dict(fx=0.5, fy=5.6, ph=TAU / 4, rings=(8.0,)),
        dict(fx=1.0, fy=5.2, ph=TAU / 2, rings=(10.0,)),
        dict(fx=0.5, fy=5.2, ph=3 * TAU / 4, rings=(5.0,)),
    ],
    "walk": [  # skimming: back, fin and eye break the surface, tail flicks, wake behind
        dict(fx=1, fy=2.4, amp=1.0, ph=0.0, tail=16, wake=0),
        dict(fx=1, fy=2.0, amp=1.0, ph=TAU / 6, tail=8, wake=1),
        dict(fx=1, fy=2.4, amp=1.0, ph=2 * TAU / 6, tail=-6, wake=2),
        dict(fx=1, fy=2.8, amp=1.0, ph=3 * TAU / 6, tail=-14, wake=0),
        dict(fx=1, fy=2.4, amp=1.0, ph=4 * TAU / 6, tail=-4, wake=1),
        dict(fx=1, fy=2.0, amp=1.0, ph=5 * TAU / 6, tail=10, wake=2),
    ],
    "windup": [  # sinks out of sight: the fin slides under, rings spread, cold eye waits
        dict(fx=-1, fy=7.0, dorsal=0.9, rings=(5.0, 9.0), eye="angry"),
        dict(fx=-2, fy=9.0, dorsal=0.8, rings=(6.0, 11.0), eye="angry", bubbles=1),
        dict(fx=-2, fy=11.0, dorsal=0.7, rings=(7.0, 12.5), eye="angry", bubbles=2, glint=True),
    ],
    "attack": [  # leaping bite: burst out nose-up, arc over, snap on frame 2, dive back
        dict(fx=2, fy=-9, ang=52, amp=0.6, ph=1.0, tail=-10, jaw=0.9, eye="angry", splash=0.2, sx=2),
        dict(fx=9, fy=-17, ang=16, amp=0.5, ph=2.0, tail=14, jaw=1.0, eye="angry", rings=(10.0,)),
        dict(fx=11, fy=-12, ang=-28, amp=0.4, ph=3.0, tail=22, jaw=0.0, eye="angry", hit=True, rings=(12.0,)),
        dict(fx=5, fy=3, ang=-68, amp=0.5, ph=4.0, tail=10, jaw=0.2, splash=0.2, sx=5, rings=(6.0,)),
    ],
    "hurt": [  # jolted half out of the water, recoiling
        dict(fx=-4, fy=-5, ang=28, amp=1.2, ph=1.0, tail=24, jaw=0.6, eye="squeeze", fin=-30, splash=0.2,
             sx=-3),
        dict(fx=-3, fy=0, ang=14, amp=0.8, ph=1.6, tail=12, jaw=0.2, eye="squeeze", fin=-15, rings=(11.0,)),
    ],
    "death": [  # thrashes up, floats belly-up on the pool, dissolves tail-first into mist
        dict(fx=-3, fy=-7, ang=34, amp=1.4, ph=1.0, tail=26, jaw=0.7, eye="squeeze", fin=-40, splash=0.25,
             sx=-2),
        dict(fx=-1, fy=-3.5, ang=-4, flip=True, amp=0.6, ph=2.0, tail=-10, jaw=0.5, eye="dead", rings=(12.0,)),
        dict(fx=-1, fy=-3.5, ang=-4, flip=True, amp=0.3, ph=2.4, jaw=0.5, eye="dead", dis=0.45, mist=0.25),
        dict(fx=-1, fy=-3.5, ang=-4, flip=True, amp=0.3, ph=2.4, jaw=0.5, eye="dead", dis=0.9, mist=0.55,
             fade=0.6),
        dict(fx=-1, fy=-3.5, ang=-4, flip=True, amp=0.3, ph=2.4, jaw=0.5, eye="dead", dis=1.0, mist=0.9,
             fade=0.3),
    ],
})


def _pool(cv, P, shadow_mask):
    """Flat grey puddle (drawn under the fish), rim highlight, submerged shadow, ripples."""
    cv.ellipse(P[0], P[1], POOL_RX, POOL_RY, POOL, shade="flat", name="pool", under=True)
    # far rim catches the light; near lip one step darker
    cv.limb([(P[0] - POOL_RX + 2.0, P[1] - POOL_RY + 0.9), (P[0], P[1] - POOL_RY + 0.5),
             (P[0] + POOL_RX - 2.0, P[1] - POOL_RY + 0.9)], 0.5, px.flat(POOL_RIM), decal=True, clip="pool")
    if shadow_mask is not None:  # the body under the surface shows as a dark shape
        m = shadow_mask & cv.mask_of("pool")
        cv._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(POOL_SHADOW), name="pool")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    P = (cv.gx + 0.5, ground - POOL_RY + 1.0)  # pool centre; its bottom row is the ground row
    wl = P[1]  # waterline: the fish is hidden below it
    C = (P[0] + p.fx, wl + p.fy)
    cv.opacity = p.fade
    pts = None
    if p.dis < 1.0:
        xf = [px.flip_y(C[1])] if p.flip else []
        with cv.xform(*xf):
            pts = hb.hollow_fish(cv, C, LENGTH, HEIGHT, ang=p.ang, amp=p.amp, phase=p.ph, tail=p.tail, jaw=p.jaw,
                                 fin=p.fin, eye=p.eye, eye_size=3, dorsal=p.dorsal, teeth=True, jaw_open=38.0,
                                 hinge_back=1.1, form="ellipse", tall_dorsal=True, tail_len=0.32,
                                 tail_spread=34)
    below = cv.filled & (cv.Y > wl)
    shadow = None
    if below.any():
        shadow = below
        cv.fill(below, px.flat("#000000"), erase=True)
        hb.clean_specks(cv, 3)
    if 0 < p.dis < 1.0:
        bb = hb.body_bbox(cv)
        edge = bb[0] + (bb[2] - bb[0] + 1) * p.dis
        cv.fill(hb.sweep_mask(cv, edge, seed=frame, jag=1.5) & ~cv.mask_of(["eye", "eyemark"]),
                px.flat("#000000"), erase=True)
        hb.clean_specks(cv, 4)
    _pool(cv, P, shadow)
    # ripple rings on the pool surface (around the fin / entry point)
    rx0 = min(P[0] + POOL_RX - 3, max(P[0] - POOL_RX + 3, C[0] + 1))
    for r in p.rings:
        hb.ripple(cv, rx0, P[1], r, ry=POOL_RY - 0.3, colour=hb.RIPPLE, dim=RIPPLE_NEAR, clip="pool")
    fx_top = cv.layer(above=True, outline=True)
    if p.wake:  # short wake lines peeling off behind the skimming fish
        for k in range(2):
            x0 = C[0] - 10 - 4 * k - p.wake
            cv.line((math.floor(x0), math.floor(wl) - 1 + k), (math.floor(x0) + 2, math.floor(wl) - 1 + k),
                    hb.RIPPLE, decal=True, clip="pool")
    if p.splash is not None:
        px.splash(fx_top, P[0] + p.sx, math.floor(wl) + 2, p.splash, size=0.8, mat=SPLASH)
    if p.bubbles:  # air rising from the sunken fish
        bl = cv.layer(above=True, outline=True)
        for k in range(p.bubbles):
            bx_ = rx0 + 3 - 4 * k
            bl.circle(bx_, wl - 2.5 - 2.5 * k, 0.9, SPLASH, shade="soft", name="bubble")
    if p.glint:  # the tell: its empty eye glows just under the surface
        gx = math.floor(rx0 + 5)
        g = cv.layer(above=True, outline=False)
        g.pixels([(gx, math.floor(wl)), (gx + 1, math.floor(wl))], hb.EYE_WHITE, name="glint")
        g.pixels([(gx - 1, math.floor(wl)), (gx + 2, math.floor(wl))], hb.EYE_HALO, name="glint")
    if p.mist is not None:
        mist = cv.layer(above=True, outline=True)
        t = p.mist
        front = C[0] - LENGTH * 0.5 + LENGTH * min(1.0, p.dis)
        hb.mist_puff(mist, front - 4, C[1] - 1, t, size=1.0, seed=5, count=4, spread=1.2)
        if t > 0.3:
            hb.mist_puff(mist, front - 11, C[1] - 3, t - 0.15, size=0.9, seed=9, count=3, spread=1.3)
        if t > 0.6:
            hb.mist_wisp(mist, C[0] + 4, C[1] - 6, phase=frame, length=6, direction=1, thick=0.7)
    if p.hit and pts is not None:
        spark = cv.layer(above=True, outline=False)
        px.impact(spark, pts["mouth"][0] + 1, pts["mouth"][1], size=3)
