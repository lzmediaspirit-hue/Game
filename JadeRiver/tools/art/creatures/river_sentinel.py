"""River sentinel - an ancient river-stone guardian statue with a stone trident (Water / Earth).

Mirrorwater Lake, Sentinel Causeway (Azure Expanse), levels 70-75, a slow brute guardian.
It has stood waist-deep in the lake for centuries: weathered blue-grey river stone worn
smooth, green algae streaks and barnacles on the legs, a tall scholar-general's helmet
(a crown board rising at the front, a bronze hairpin through it), a carved beard, and
water trickling from the cracks at its joints.  The eye slit glows pale aquamarine.

View: side, facing right.  ~64 art px tall to the crown, on a 96 px art canvas (cell 192).
Rig (adapted from ``jade_sentinel``): pelvis P, torso up to the shoulders S (``lean``),
two-bone legs and arms solved with ``px.ik2``; the trident is defined by the near hand's
grip point and an angle, the far hand holds lower on the shaft.
Parts, back to front: far leg, far arm, torso (cuirass, algae waterline, bronze belt,
tassets), near leg, waterweed tassels, trident, head (neck guard, helmet bowl, face, tall
crown board, bronze brim, cheek guard, glowing eye slit), pauldron, near arm, beard.
Idle: water drips from the knee and elbow cracks.  Windup: the trident rises high and
back while water spirals up the shaft (held).  Attack: a heavy downward drive in front;
the prongs sink into the water on frame 1 with a splash + impact.  Death: the cracks glow,
the statue crumbles into a heap of river stones and the lake washes over it.
"""
import math

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "river_sentinel",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: blue-grey river stone (sand lights, deep-teal shadows), algae, aged bronze,
# aquamarine water glow ------------------------------------------------------------------------
STONE = px.material("rs_stone", "#c4c9b4", "#93a7ad", "#62808b", "#3a5961", outline="#0a171c",
                    thresholds=(0.92, 0.55, 0.2))
STONE_D = px.material("rs_stone_dark", "#a2b1ad", "#6e8891", "#4b6a75", "#2d4a52", outline="#0a171c",
                      thresholds=(0.9, 0.55, 0.2))
ALGAE = px.material("rs_algae", "#a9c46a", "#6f9a48", "#4a7541", "#2e5237", outline="#0b170f")
BRONZE = px.material("rs_bronze", "#d9b276", "#a0703d", "#6f4c2f", "#483322", outline="#170e08")
AQUA = px.material("rs_aqua", "#effffa", "#9ff0dc", "#4fc4b4", "#2a8a86", outline="#0d3035")
SHELL = px.rgb("#efe6cf")
SHELL_D = px.rgb("#a99c80")
CRACK = px.rgb("#1b3036")
SHAFT_UP, SHAFT_DN, PRONG = 24.0, 16.0, 8.0
STRIKE_DX = 24.5  # the prongs sink into the water this far in front of the anchor on the hit frame

# ---- poses ------------------------------------------------------------------------------------
# bx, by   pelvis offset       lean  torso angle (deg, 90 = upright)     head  head tilt
# grip     near-hand grip point relative to the shoulder (dx, dy)       tri  trident angle
#          (deg, 90 = prongs up)        slide  far-hand distance down the shaft (px)
# fn, ff   near / far foot (dx, lift)   glow  eye brightness 0..2      crack  0..3 extra cracks
# cglow    cracks glow aquamarine       drip  idle drip phase (None = no drops)
# sway     waterweed sway (px)          swirl  water spiral up the shaft 0..1 (None = off)
# arc      water flung off the prongs (attack sweep life)   splash  prong splash life
# hit      impact spark                 chips  stone-chip burst life   jets  water jets from cracks
# brk      crumble 0..1 (pieces slip)   drop  "fall" | "lie" trident dropped   pile  0 | 1..3
DEFAULTS = dict(bx=0, by=0, lean=90, head=0, grip=(11, 21), tri=88, slide=11, fn=(3, 0), ff=(-3, 0), glow=1,
                hold=SHAFT_UP, crack=0, cglow=False, drip=None, sway=0.0, swirl=None, arc=None, splash=None, hit=False,
                chips=None, jets=None, brk=0.0, drop=None, pile=0, fade=1.0, eye="open", stomp=None)

POSE = px.poses(DEFAULTS, {
    "idle": [  # a statue at rest: water drips from the joints, the weed sways, the eye pulses
        dict(drip=0, sway=0.0),
        dict(drip=1, sway=0.5, tri=87, head=1),
        dict(drip=2, sway=1.0, tri=87, head=1, glow=2),
        dict(drip=3, sway=0.5, glow=2),
    ],
    "walk": [  # heavy stomps: the body sinks on each planted foot; the trident is carried upright
        dict(fn=(6, 0), ff=(-5, 0), by=1, grip=(12, 20), tri=84, sway=-0.5, stomp=0),
        dict(fn=(4, 0), ff=(-1, 4), by=-1, grip=(12, 19), tri=85, sway=0.5),
        dict(fn=(1, 0), ff=(3, 4), by=-1, grip=(11, 19), tri=86, sway=1.0),
        dict(fn=(-4, 0), ff=(5, 0), by=1, grip=(11, 20), tri=88, sway=0.0, stomp=1),
        dict(fn=(-1, 4), ff=(3, 0), by=-1, grip=(11, 19), tri=87, sway=-1.0),
        dict(fn=(3, 4), ff=(0, 0), by=-1, grip=(12, 19), tri=85, sway=-1.0),
    ],
    "windup": [  # the trident rises high and back, water spirals up the shaft - held
        dict(grip=(8, 4), tri=102, slide=10, lean=92, fn=(4, 0), ff=(-4, 0), glow=2, eye="angry", swirl=0.35,
             sway=-0.5),
        dict(grip=(-1, -9), tri=124, slide=14, hold=20, lean=96, head=3, fn=(5, 0), ff=(-5, 0), glow=2,
             eye="angry", swirl=0.7, sway=-1.0),
        dict(grip=(-3, -12), tri=134, slide=16, hold=19, lean=98, head=4, fn=(6, 0), ff=(-6, 0), glow=2,
             eye="angry", swirl=1.0, by=1, sway=-1.0),
    ],
    "attack": [  # over the top and down: the prongs drive into the water in front on frame 1
        dict(grip=(9, -4), tri=70, slide=10, lean=86, head=-2, fn=(6, 0), ff=(-6, 0), glow=2, eye="angry",
             arc=0.3, sway=1.0),
        dict(grip=(12, 12), tri=-66, slide=11, lean=76, head=-6, fn=(7, 0), ff=(-6, 0), glow=2, eye="angry",
             arc=0.8, splash=0.2, hit=True, by=2, bx=-1, sway=1.5),
        dict(grip=(12, 12), tri=-66, slide=11, lean=77, head=-5, fn=(7, 0), ff=(-6, 0), glow=2, eye="angry",
             splash=0.55, by=2, bx=-1, sway=0.5),
        dict(grip=(10, 15), tri=76, slide=11, lean=86, fn=(5, 0), ff=(-4, 0), glow=1, sway=-0.5, splash=0.9),
    ],
    "hurt": [  # stone chips fly, it rocks back, the light in the eye gutters
        dict(bx=-3, lean=100, head=10, grip=(7, 18), tri=100, eye="dim", chips=0.3, crack=1, glow=0, sway=-1.5),
        dict(bx=-2, lean=95, head=5, grip=(8, 19), tri=94, crack=1, glow=1, sway=-0.5, chips=0.8),
    ],
    "death": [  # cracks flare aquamarine, it crumbles into river stones, the lake washes over
        dict(bx=-3, lean=100, head=10, grip=(7, 18), tri=100, eye="dim", crack=3, cglow=True, glow=0, jets=0.4,
             chips=0.3),
        dict(bx=-2, by=5, lean=94, head=-10, grip=(6, 16), tri=100, eye="dead", crack=3, cglow=True, glow=0,
             brk=1.0, drop="fall", jets=0.9),
        dict(pile=1, eye="dead", drop="lie"),
        dict(pile=2, eye="dead", drop="lie"),
        dict(pile=3, eye="dead", drop="lie"),
    ],
})

L_THIGH, L_SHIN = 12.0, 12.0
L_UPPER, L_FORE = 9.5, 10.0
TORSO = 18.0


def _dir(ang):
    return (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))


def _fl(q):
    return (math.floor(q[0]), math.floor(q[1]))


# ---- parts ------------------------------------------------------------------------------------
def _crack(cv, pts, glow, clip):
    col = AQUA.base if glow else CRACK
    for a, b in zip(pts, pts[1:]):
        cv.line(_fl(a), _fl(b), col, band=None, decal=True, clip=clip, name=clip if isinstance(clip, str) else None)


def _trickle(cv, top, length, clip):
    """A thin run of water down the stone from a joint crack."""
    x, y = _fl(top)
    cv.line((x, y), (x, y + length), AQUA.base, decal=True, clip=clip, name="water")
    cv.pixel(x, y, AQUA.light, decal=True, clip=clip, name="water")


def _barnacles(cv, x, y, clip):
    cv.stamp([".s.", "sks"], math.floor(x), math.floor(y), {"s": SHELL, "k": SHELL_D}, decal=True, clip=clip,
             name="shell")


def _leg(cv, hip, foot, far, p):
    shade = "dark" if far else "two"
    mat = STONE_D if far else STONE
    ank = (foot[0] - 1.0, foot[1] - 3.0)
    knee = px.ik2(hip, ank, L_THIGH, L_SHIN, bend=1)
    cv.limb([hip, knee], [5.4, 4.6], mat, shade=shade, name="leg")
    cv.limb([knee, ank], [4.8, 3.8], mat, shade=shade, name="shin", sep=False if far else "deep")
    # blocky sabaton
    cv.polygon([(foot[0] - 4.6, foot[1] - 4.4), (foot[0] + 2.2, foot[1] - 4.4), (foot[0] + 6.2, foot[1] - 0.6),
                (foot[0] + 6.2, foot[1] + 1.0), (foot[0] - 4.6, foot[1] + 1.0)], mat, shade=shade, name="foot",
               sep=False if far else "deep")
    # algae streaks running down the shin and over the sabaton (the old waterline)
    for k, (off, t0, t1) in enumerate(((-2.0, 0.25, 0.95), (0.5, 0.45, 1.0), (2.6, 0.2, 0.7))):
        a = px.polar(px.lerp_pt(knee, ank, t0), 0, off)
        b = px.polar(px.lerp_pt(knee, ank, t1), 0, off)
        cv.line(_fl(a), _fl(b), ALGAE.shadow if far else ALGAE.base, decal=True, clip="shin", name="shin")
    cv.line(_fl((foot[0] - 3.5, foot[1] - 3.0)), _fl((foot[0] + 2.0, foot[1] - 3.0)),
            ALGAE.shadow if far else ALGAE.base, decal=True, clip="foot", name="foot")
    if not far:
        _barnacles(cv, ank[0] - 2.0, ank[1] - 3.5, "shin")
        _barnacles(cv, foot[0] + 0.5, foot[1] - 2.2, "foot")
        # knee crack with a trickle of water
        kc = (knee[0] + 1.5, knee[1] - 1.0)
        cv.line(_fl(kc), _fl((kc[0] - 2, kc[1] + 2)), CRACK if not p.cglow else AQUA.base, decal=True,
                clip=["leg", "shin"], name="shin")
        _trickle(cv, (kc[0] - 2, kc[1] + 3), 3 + (p.drip or 0) % 2, "shin")
        if p.crack >= 2:
            _crack(cv, [(hip[0] + 2, hip[1] + 2), (hip[0] - 1, hip[1] + 5), (hip[0] + 1, hip[1] + 8)], p.cglow, "leg")
    return knee


def _arm(cv, shoulder, hand, far, p):
    shade = "dark" if far else "soft"
    mat = STONE_D if far else STONE
    d = math.hypot(hand[0] - shoulder[0], hand[1] - shoulder[1])
    if d < L_UPPER + L_FORE - 0.3:  # a hand raised above the shoulder swings its elbow back
        elbow = px.ik2(shoulder, hand, L_UPPER, L_FORE, bend=1 if hand[1] < shoulder[1] - 7 else -1)
    else:
        elbow = px.lerp_pt(shoulder, hand, L_UPPER / (L_UPPER + L_FORE))
    nm = "arm_far" if far else "arm"
    cv.limb([shoulder, elbow, hand], [4.2, 3.6, 3.2], mat, shade=shade, name=nm, sep=False if far else "deep")
    # bronze vambrace on the forearm, then a stone fist
    cv.limb([px.lerp_pt(elbow, hand, 0.35), px.lerp_pt(elbow, hand, 0.8)], [3.7, 3.3], BRONZE,
            shade="dark" if far else "two", decal=True, clip=nm)
    cv.circle(hand[0], hand[1], 3.0, mat, shade=shade, name="fist", sep=False if far else "deep")
    if not far:  # elbow crack, water running from it
        cv.line(_fl((elbow[0] - 1, elbow[1] - 1)), _fl((elbow[0] + 1, elbow[1] + 1)),
                AQUA.base if p.cglow else CRACK, decal=True, clip=nm, name=nm)
    return elbow


def _trident(cv, G, ang, hold=SHAFT_UP, name="trident"):
    """Stone shaft with bronze fittings and three stone prongs (ji).  ``hold`` = shaft
    length from the grip up to the prongs (the rest of the shaft runs below the grip)."""
    d = _dir(ang)
    dn = SHAFT_UP + SHAFT_DN - hold
    butt = (G[0] - d[0] * dn, G[1] - d[1] * dn)
    top = (G[0] + d[0] * hold, G[1] + d[1] * hold)
    cv.limb([butt, top], 1.15, STONE_D, shade="two", name=name)
    cv.limb([butt, px.lerp_pt(butt, top, 0.07)], 1.5, BRONZE, shade="two", name=name)
    fwd, back = ang - 90, ang + 90
    # side prongs: out along the crossbar, then curving up to a point
    for side in (fwd, back):
        root = px.polar(top, side, 3.4)
        cv.limb([px.polar(top, side, 0.5), root, px.polar(root, ang, 4.0), px.polar(px.polar(root, side, -0.6), ang,
                                                                                    PRONG - 1.5)],
                [1.1, 1.1, 0.9, 0.5], STONE, shade="two", name=name)
    # centre prong, longer, with a leaf point
    tip = px.polar(top, ang, PRONG + 1.0)
    cv.limb([px.polar(top, ang, -1.0), px.polar(top, ang, PRONG - 2.0), tip], [1.3, 1.2, 0.5], STONE, shade="two",
            name=name, sep="deep")
    # bronze collar where the head meets the shaft
    cv.limb([px.polar(top, ang, -2.6), px.polar(top, ang, -0.6)], 1.7, BRONZE, shade="two", name=name)
    return butt, top, tip


def _head(cv, H, p):
    """Tall scholar-general helmet: a crown board rising at the front with a bronze pin boss,
    a bronze brim, cheek guard and flared neck guard; a stone face with a glowing eye slit."""
    x, y = H
    cv.polygon([(x - 2.0, y + 0.5), (x - 7.8, y + 5.0), (x - 6.8, y + 7.0), (x - 1.0, y + 5.6)], STONE_D,
               shade="two", name="neckguard")
    # helmet bowl
    cv.ellipse(x, y, 6.2, 6.0, STONE, name="helm", sep="deep")
    # face: nose ridge and chin jut forward from the bowl
    cv.polygon([(x + 4.6, y - 1.0), (x + 7.6, y + 0.6), (x + 7.4, y + 2.2), (x + 6.2, y + 2.8), (x + 6.6, y + 4.6),
                (x + 4.0, y + 6.2)], STONE, shade="two", name="helm")
    # tall crown board: the front rises high, the top slopes down toward the back
    cv.polygon([(x - 5.2, y - 2.4), (x - 5.8, y - 8.6), (x - 3.6, y - 11.6), (x + 0.6, y - 14.6), (x + 3.2, y - 14.8),
                (x + 4.2, y - 13.0), (x + 4.4, y - 2.8)], STONE_D, name="crown", sep="deep")
    cv.limb([(x + 3.4, y - 3.6), (x + 3.2, y - 13.4), (x + 0.8, y - 13.8), (x - 4.4, y - 10.2)], 0.7, BRONZE,
            shade="two", decal=True, clip="crown", name="crown")
    cv.line(_fl((x - 1.0, y - 12.0)), _fl((x - 1.0, y - 4.0)), BRONZE.shadow, decal=True, clip="crown", name="crown")
    # bronze brim with a visor lip over the eyes
    cv.limb([(x - 6.0, y - 1.8), (x + 7.0, y - 2.4)], [1.0, 1.1], BRONZE, shade="two", name="brim", sep="deep")
    # cheek guard over the ear
    cv.polygon([(x - 2.4, y - 1.0), (x + 1.6, y - 1.0), (x + 2.0, y + 5.2), (x - 0.6, y + 6.4), (x - 2.8, y + 4.0)],
               STONE, shade="two", name="cheek", sep="deep")
    cv.line(_fl((x + 5, y + 4)), _fl((x + 6, y + 4)), STONE.deep, decal=True, clip="helm", name="helm")
    cv.line(_fl((x + 2, y - 1)), _fl((x + 6, y - 1)), STONE.deep, decal=True, clip="helm", name="helm")
    ex, ey = math.floor(x + 3), math.floor(y)
    if p.eye == "dead":
        cv.pixels([(ex, ey), (ex + 1, ey), (ex + 2, ey)], STONE.deep, name="eye")
    elif p.eye == "dim":
        cv.pixels([(ex, ey), (ex + 1, ey), (ex + 2, ey)], AQUA.shadow, name="eye")
    else:
        cv.pixels([(ex, ey), (ex + 2, ey)], AQUA.base, name="eye")
        cv.pixel(ex + 1, ey, AQUA.light, name="eye")
        if p.eye == "angry":  # the slit narrows under a scowl and flares
            cv.pixel(ex + 3, ey, AQUA.base, name="eye")
            cv.pixels([(ex + 1, ey - 1), (ex + 2, ey - 1)], STONE.deep, name="eye")
        if p.glow == 2:
            cv.pixel(ex + 1, ey + 1, AQUA.shadow, name="eye")
    if p.crack >= 2:
        _crack(cv, [(x - 4, y - 5), (x - 1, y - 2), (x - 2, y + 2)], p.cglow, "helm")
        _crack(cv, [(x - 1, y - 13), (x + 1, y - 9), (x - 1, y - 5)], p.cglow, "crown")


def _beard(cv, H):
    """Long carved beard falling in front of the chest (drawn over the pauldron)."""
    x, y = H
    cv.polygon([(x + 3.6, y + 4.4), (x + 6.8, y + 4.0), (x + 8.0, y + 8.6), (x + 7.8, y + 13.4), (x + 6.0, y + 10.8),
                (x + 4.2, y + 7.6)], STONE_D, shade="soft", name="beard", sep="deep")
    cv.line(_fl((x + 6, y + 6)), _fl((x + 7, y + 10)), STONE_D.deep, decal=True, clip="beard", name="beard")


def _tassels(cv, belt_pts, sway):
    """Waterweed tassels hanging from the belt: thin strands that sway."""
    for k, q in enumerate(belt_pts):
        s = sway * (0.7 + 0.4 * k)
        ln = 7.0 + 2.0 * (k % 2)
        pts = [q, (q[0] + s * 0.3 - 0.2, q[1] + ln * 0.35), (q[0] + s * 0.7 - 0.6, q[1] + ln * 0.7),
               (q[0] + s - 0.8, q[1] + ln)]
        cv.limb(pts, [1.0, 0.8, 0.7, 0.5], ALGAE, shade="two", name="weed")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    if p.pile:
        _pile(cv, ground, p)
        return
    b = p.brk
    P = (cv.gx - 4 + p.bx, ground - 25.0 + p.by)
    S = px.polar(P, p.lean, TORSO)
    G = (S[0] + p.grip[0], S[1] + p.grip[1])
    hd = _dir(p.tri)
    G2 = (G[0] - hd[0] * p.slide, G[1] - hd[1] * p.slide)
    shoulders = [px.polar(S, p.lean - 90, 2.0), px.polar(S, p.lean - 90, 4.2)]
    up = p.lean
    w = px.polar

    def foot(i):
        f = p.fn if i == 0 else p.ff
        return (P[0] + f[0], ground - f[1])

    def piece(dx, dy):
        return px.translate(dx * b, dy * b)

    tri = None
    with cv.xform(piece(-3, 2)):
        _leg(cv, (P[0] + 1.0, P[1] + 1.0), foot(1), True, p)
    if p.drop is None:
        with cv.xform(piece(-4, 5)):
            _arm(cv, shoulders[1], G2, True, p)
    with cv.xform(piece(0, 3)):
        # torso: broad cuirass tapering to the waist
        waist = px.polar(P, up, 3.0)
        chest = [w(waist, up - 90, 6.8), w(S, up - 90, 9.4), w(px.polar(S, up, 2.6), up - 60, 6.4),
                 w(px.polar(S, up, 2.8), up + 60, 6.2), w(S, up + 90, 8.6), w(waist, up + 90, 6.4)]
        cv.polygon(chest, STONE, name="body")
        # algae waterline stain above the belt
        wl0, wl1 = w(px.polar(waist, up, 3.0), up + 90, 7.0), w(px.polar(waist, up, 2.4), up - 90, 7.4)
        cv.limb([wl0, wl1], 1.3, ALGAE, shade="two", decal=True, clip="body", name="body")
        for k, off in enumerate((-5.0, -1.0, 4.0)):
            a = w(px.polar(waist, up, 3.2), up - 90, off)
            cv.line(_fl(a), _fl(w(a, up + 180, -2.0 - k % 2)), ALGAE.shadow, decal=True, clip="body", name="body")
        belt = [w(waist, up + 90, 6.6), w(waist, up - 90, 7.0)]
        cv.limb(belt, 1.8, BRONZE, shade="two", name="belt")
        for k, off in enumerate((-5.0, -0.8, 3.6)):  # tasset plates hanging from the belt, algae-stained
            q = w(waist, up - 90, off)
            cv.polygon([w(q, up + 90, 2.2), w(q, up - 90, 2.2), w(w(q, up + 180, 8.0), up - 90, 2.6),
                        w(w(q, up + 180, 8.4), up + 90, 1.9)], STONE_D if k == 0 else STONE, shade="two",
                       name="tasset", sep="deep")
        for k, off in enumerate((-0.4, 3.8)):
            q = w(w(waist, up - 90, off), up + 180, 3.5)
            cv.line(_fl(q), _fl(w(q, up + 180, 4.0)), ALGAE.base, decal=True, clip="tasset", name="tasset")
        # hip crack with water running from it
        hc0 = w(w(waist, up - 90, 5.6), up, 2.0)
        cv.line(_fl(hc0), _fl(w(hc0, up + 200, 3.0)), AQUA.base if p.cglow else CRACK, decal=True, clip="body",
                name="body")
        if p.crack >= 1:
            a0 = w(px.lerp_pt(S, waist, 0.15), up - 90, 7.0)
            a1 = w(px.lerp_pt(S, waist, 0.4), up - 90, 0.5)
            a2 = w(px.lerp_pt(S, waist, 0.7), up + 90, 3.5)
            _crack(cv, [a0, a1, a2], p.cglow, "body")
        if p.crack >= 3:
            _crack(cv, [w(S, up + 90, 6.0), w(px.lerp_pt(S, waist, 0.3), up + 90, 3.0),
                        w(px.lerp_pt(S, waist, 0.6), up + 90, 5.0)], p.cglow, "body")
    with cv.xform(piece(1, 1)):
        knee = _leg(cv, (P[0] - 1.0, P[1] + 1.5), foot(0), False, p)
    with cv.xform(piece(0, 3)):
        _tassels(cv, [w(w(waist, up - 90, off), up + 180, 1.0) for off in (-1.6, 3.4)], p.sway)
    if p.drop is None:
        tri = _trident(cv, G, p.tri, p.hold)
    snap = (cv.filled.copy(), cv.part.copy())  # parts drawn from here on hide the swirl's front arcs
    H = w(S, up + 4, 10.5)
    with cv.xform(piece(3, 7), px.rotate(p.head, H)):
        _head(cv, H, p)
    with cv.xform(piece(4, 6)):
        pa = w(S, up - 90, 0.6)
        cv.ellipse(pa[0], pa[1] + 1.0, 6.2, 5.0, STONE, angle=up - 90, name="pauldron", sep="deep", shade="two")
        cv.limb([w(pa, up + 150, 5.8), w(pa, up - 150, 6.0)], 1.1, BRONZE, shade="two", decal=True,
                clip="pauldron", name="pauldron")
        if p.crack >= 3:
            _crack(cv, [w(pa, up + 120, 4.0), w(pa, up, 0.0), w(pa, up - 70, 3.0)], p.cglow, "pauldron")
    with cv.xform(piece(4, 6)):
        if p.drop is None:
            elbow = _arm(cv, shoulders[0], G, False, p)
        else:
            elbow = _arm(cv, shoulders[0], w(shoulders[0], up + 160, 17.0), False, p)
    with cv.xform(piece(3, 7), px.rotate(p.head, H)):
        _beard(cv, H)
    if p.drop == "fall":  # the trident topples forward, its butt still on the ground
        _trident(cv, (cv.gx + 14, ground - 12.0), 38)
    if b > 0:  # pieces already broken off lie at its feet
        g = ground + 1.0
        _stone(cv, P[0] - 12, g, 3.6, 2.6, STONE_D)
        _stone(cv, P[0] + 11, g, 3.0, 2.2, STONE, algae=True)
    # sink anything that went below the ground row (prongs driven into the water)
    below = np.zeros((cv.h, cv.w), bool)
    below[cv.gy - 1:, :] = True
    hc.erase_mask(cv, below & cv.filled)

    # ---- FX ----------------------------------------------------------------------------------
    if p.drip is not None:  # drops falling from the knee and elbow cracks
        fx = cv.layer(above=True, outline=False)
        for k, (src, fall) in enumerate((((knee[0] + 4.6, knee[1] + 2.0), 7.0), ((elbow[0], elbow[1] + 3.0), 7.0))):
            t = ((p.drip + 2 * k) % 4) / 4.0
            dy = fall * t
            x, y = math.floor(src[0]), math.floor(src[1] + dy)
            if y + 1 < cv.gy - 6:
                fx.pixel(x, y, AQUA.light, name="drop")
                fx.pixel(x, y + 1, AQUA.base, name="drop")
    if p.stomp is not None:  # a little splash kicked up by the planted foot
        fx = cv.layer(above=True, outline=True)
        f = foot(0 if p.stomp == 0 else 1)
        px.splash(fx, f[0] + 9.5, cv.gy - 1, 0.2, size=0.9, mat=AQUA)
    if p.swirl is not None and tri is not None:
        hide = cv.filled & (~snap[0] | (cv.part != snap[1]))
        _swirl(cv, tri, p.tri, p.swirl, hide)
    if p.arc is not None and tri is not None:
        fx = cv.layer(above=False, outline=False)
        c = (S[0] + 2, S[1] + 2)
        a1 = 80 - 150 * p.arc
        for r, col, a0, off in ((33.0, AQUA.light, 100, 0), (30.0, AQUA.base, 92, 5)):
            a = a0 - off
            while a - 7 > a1:
                hc.arc_line(fx, c, r, a, a - 7, col, name="arc", step=2.0)
                a -= 12
    if p.splash is not None:  # where the prongs entered the water (attack frames 1-3)
        fx = cv.layer(above=True, outline=True)
        px.splash(fx, cv.gx + STRIKE_DX, cv.gy - 1, p.splash, size=1.5, mat=AQUA)
    if p.hit and tri is not None:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tri[2][0] - 1, cv.gy - 6, size=4, color=AQUA.light, core=px.GLINT)
    if p.chips is not None:
        ch = cv.layer(above=True, outline=True)
        t = p.chips
        base = (S[0] + 8, S[1] - 1)
        for k, (vx, vy) in enumerate(((5, 6), (8, 3), (3, 9), (7, 8))):
            x = base[0] + vx * (0.4 + t) * 1.6
            y = base[1] - (vy * (0.4 + t) * 1.4 - 6 * t * t)
            r = 1.9 - 0.3 * (k % 2)
            ch.polygon([(x - r, y + r * 0.7), (x - r * 0.2, y - r), (x + r, y + r * 0.4)], STONE, shade="soft",
                       name="chip")
    if p.jets is not None:  # water spurting from the glowing cracks
        fx = cv.layer(above=True, outline=False)
        t = p.jets
        for k, (q, a) in enumerate(((w(px.lerp_pt(S, P, 0.4), up - 90, 7.0), 20), (w(S, up + 90, 7.0), 160),
                                    ((knee[0] + 1.5, knee[1]), 10))):
            r0 = 1.5 + 3.0 * t
            for s in range(3):
                e = px.polar(q, a - 25 * s * t, r0 + s * 1.5)
                e2 = px.polar(e, a - 90 * (1 if a < 90 else -1), 1.0)
                fx.line(_fl(e), _fl(e2), AQUA.light if s == 0 else AQUA.base, name="jet")


def _swirl(cv, tri, ang, prog, hide):
    """Water spiralling up the shaft from the butt toward the prongs: a helix (front arcs over
    the body, back arcs behind it) led by a gathering water orb that crowns the prongs."""
    butt, top, tip = tri
    d = _dir(ang)
    n = _dir(ang + 90)
    L = math.hypot(top[0] - butt[0], top[1] - butt[1])
    front = cv.layer(above=True, outline=False)
    back = cv.layer(above=False, outline=False)
    end = L * prog
    u = max(1.0, end - 22.0)
    while u <= end:
        ph = u * 0.62
        amp = 1.6 + 1.2 * (u / L)
        q = (butt[0] + d[0] * u + n[0] * math.sin(ph) * amp, butt[1] + d[1] * u + n[1] * math.sin(ph) * amp)
        ix, iy = math.floor(q[0]), math.floor(q[1])
        if math.cos(ph) > 0:
            if 0 <= iy < cv.h and 0 <= ix < cv.w and hide[iy, ix]:
                u += 0.25
                continue
            front.pixel(math.floor(q[0]), math.floor(q[1]), AQUA.light if u > end - 8 else AQUA.base, name="swirl")
        else:
            back.pixel(math.floor(q[0]), math.floor(q[1]), AQUA.shadow, name="swirl")
        u += 0.25
    orb = cv.layer(above=True, outline=True)
    if prog >= 1.0:  # a ball of water gathers between the prongs
        c = px.lerp_pt(top, tip, 0.3)
        orb.circle(c[0], c[1], 2.3, AQUA, shade="soft", name="orb")
    elif prog < 0.5:  # the leading bead of water climbing the shaft
        c = (butt[0] + d[0] * end, butt[1] + d[1] * end)
        orb.circle(c[0], c[1], 1.3, AQUA, shade="soft", name="orb")


def _stone(cv, x, y, rx, ry, mat, ang=0.0, algae=False, shell=False, name="stone"):
    """One smooth river stone (a worn pebble) resting with its bottom at y."""
    cv.ellipse(x, y - ry, rx, ry, mat, angle=ang, name=name, sep="deep", bulge=0.9)
    if algae:
        cv.ellipse(x - rx * 0.1, y - ry * 0.6, rx * 0.8, ry * 0.45, ALGAE, decal=True, clip=name, name=name,
                   shade="two")
    if shell:
        _barnacles(cv, x + rx * 0.2, y - ry * 1.2, name)


def _pile(cv, ground, p):
    """A low heap of worn river stones; the helmet has rolled off the front, its light gone.
    pile 1: the heap settles as a wave rolls in; 2: the lake washes over it; 3: it drains away."""
    cv.snap_ground = True
    X = cv.gx - 1
    g = ground + 1.0
    # the trident lies behind the heap
    _trident(cv, (X + 12, ground - 1.6), 177)
    # back row, then the crown stone, then the front row
    _stone(cv, X - 11, g - 3, 6.0, 4.4, STONE_D)
    _stone(cv, X + 6, g - 3, 6.5, 4.8, STONE_D, shell=True)
    _stone(cv, X - 3, g - 7, 7.2, 5.4, STONE, ang=6, algae=True)
    _stone(cv, X + 2, g - 14, 4.4, 3.4, STONE, ang=-10)
    _stone(cv, X - 17, g, 5.0, 3.6, STONE_D, ang=-6, algae=True)
    _stone(cv, X - 7, g, 7.0, 5.0, STONE, shell=True)
    _stone(cv, X + 6, g, 6.2, 4.4, STONE, ang=5, algae=True)
    _stone(cv, X + 15, g, 4.2, 3.0, STONE_D)
    # waterweed strewn over the stones
    cv.limb([(X - 9, g - 13), (X - 6, g - 10), (X - 5, g - 6)], [1.0, 0.9, 0.6], ALGAE, shade="two", name="weed",
            sep="deep")
    # the helmet has rolled off the heap and rests tilted on the ground at the front
    H = (X + 20.0, g - 7.0)
    with cv.xform(px.rotate(-38, H)):
        _head(cv, H, p)
    if p.pile == 1:  # a wave rolls in from the left
        fx = cv.layer(above=True, outline=True)
        fx.polygon([(X - 42, g), (X - 40, g - 4), (X - 36, g - 8), (X - 31, g - 9.5), (X - 28, g - 7), (X - 31, g - 6),
                    (X - 32, g - 3), (X - 29, g)], AQUA, shade="soft", name="wave")
        fx.line((X - 36, math.floor(g - 9)), (X - 31, math.floor(g - 10)), AQUA.light, name="wave")
    elif p.pile == 2:  # the water washes over the heap, foam cresting on top
        fx = cv.layer(above=True, outline=True)
        fx.polygon([(X - 40, g), (X - 37, g - 5), (X - 30, g - 9), (X - 20, g - 10), (X - 10, g - 9), (X - 2, g - 11),
                    (X + 8, g - 8), (X + 16, g - 5), (X + 22, g - 2), (X + 25, g)], AQUA, shade="soft", name="wave")
        for (a, b) in (((X - 30, g - 9), (X - 22, g - 10)), ((X - 5, g - 11), (X + 2, g - 11))):
            fx.line(_fl(a), _fl(b), AQUA.light, name="wave")
        for k, q in enumerate(((X - 14, g - 15), (X + 4, g - 16), (X + 12, g - 12))):
            fx.pixel(q[0], q[1], AQUA.light, name="wave")
            fx.pixel(q[0], q[1] + 1, AQUA.base, name="wave")
    else:  # it drains away: a shallow sheen at the base and wet glints on the stones
        fx = cv.layer(above=True, outline=False)
        fx.ellipse(X - 8, g - 0.8, 30.0, 1.3, AQUA, shade="soft", name="sheen")
        fx.line((X - 36, math.floor(g - 1)), (X - 30, math.floor(g - 1)), AQUA.light, name="sheen")
        fx.line((X + 12, math.floor(g - 1)), (X + 18, math.floor(g - 1)), AQUA.light, name="sheen")
        for q in ((X - 5, g - 11), (X + 1, g - 17), (X + 5, g - 7)):
            fx.pixels([(q[0], q[1]), (q[0] + 1, q[1])], AQUA.light, name="glint")
