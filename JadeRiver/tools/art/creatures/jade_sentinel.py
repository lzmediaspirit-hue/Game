"""Jade sentinel - a carved jade warrior statue that walks, wielding a bronze halberd (Earth).

View: side, facing right.  ~58 art px tall to the helmet crest and ~62 with the halberd
blade, on a 96 px art canvas (cell 192).
Rig: pelvis P, torso up to the shoulders S (``lean``), two-bone legs and arms solved with
``px.ik2``; the halberd is defined by the near hand's grip point and an angle, the far
hand holds lower on the shaft.
Parts, back to front: far leg, far arm, halberd (behind the near arm), torso (cuirass,
bronze belt, tasset plates), near leg, helmet (crest, cheek guard, stern mask, glowing
eye slit), pauldron, near arm.  Gold rune glyphs glow on the cuirass, pauldron and shaft.
Windup: the halberd is drawn back over the shoulder (held); attack: a wide sweep that
lands low in front (hit on frame 1); death: cracks spread, it topples and the runes die.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "jade_sentinel",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: carved jade stone, aged bronze, glowing gold runes ------------------------------
JADE = px.material("sentinel_jade", "#a7e3c6", "#5fae8e", "#3b7a66", "#244f47", outline="#0a1a18",
                   thresholds=(0.9, 0.55, 0.2))
JADE_D = px.material("sentinel_jade_dark", "#77b89c", "#437f6a", "#2c5a4f", "#1b3a36", outline="#0a1a18")
BRONZE = px.material("sentinel_bronze", "#e8b872", "#b07a40", "#7d532f", "#523522", outline="#1a0f08")
SHAFT = px.material("halberd_shaft", "#8a5a3a", "#5e3a28", "#422a20", "#2b1b16", outline="#110a07")
BLADE = px.material("halberd_blade", "#e9f4ea", "#b9d2c4", "#86a397", "#5a7169", outline="#101816")
RUNE = px.rgb("#ffe6a1")
RUNE_DIM = px.rgb("#e5b84c")
RUNE_DEAD = px.rgb("#2c5a4f")
CRACK = px.rgb("#0f2622")

GLYPHS = (["ggg", ".g.", "g.g"], ["g.g", "ggg", "g.g"], ["gg.", ".gg", "gg."])

# ---- poses ------------------------------------------------------------------------------------
# bx, by   pelvis offset       lean  torso angle (deg, 90 = upright)     head  head tilt
# grip     near-hand grip point relative to the shoulder (dx, dy)       hal  halberd angle
#          (deg, 90 = pointing up)      slide  far-hand distance down the shaft (px)
# fn, ff   near / far foot (dx, lift)   glow  rune brightness 0..2      crack  0..3
# rot      topple roll (deg, + = backwards)   drop  halberd dropped on the ground
# swoosh   sweep-arc life (None = off)        chips  stone-chip burst life
DEFAULTS = dict(bx=0, by=0, lean=90, head=0, grip=(9, 21), hal=88, slide=11, fn=(3, 0), ff=(-3, 0), glow=1,
                crack=0, rot=0, drop=False, swoosh=None, hit=False, chips=None, fade=1.0, eye="open")

POSE = px.poses(DEFAULTS, {
    "idle": [  # a statue at rest: only the runes pulse and the halberd settles
        dict(glow=1),
        dict(glow=1, hal=87, head=1),
        dict(glow=2, hal=87, head=1),
        dict(glow=2),
    ],
    "walk": [  # heavy, deliberate steps; the halberd is carried upright
        dict(fn=(6, 0), ff=(-5, 0), by=0, grip=(10, 20), hal=84),
        dict(fn=(4, 0), ff=(-1, 3), by=-1, grip=(10, 19), hal=85),
        dict(fn=(1, 0), ff=(3, 3), by=-1, grip=(9, 19), hal=86),
        dict(fn=(-4, 0), ff=(5, 0), by=0, grip=(9, 20), hal=88),
        dict(fn=(-1, 3), ff=(3, 0), by=-1, grip=(9, 19), hal=87),
        dict(fn=(3, 3), ff=(0, 0), by=-1, grip=(10, 19), hal=85),
    ],
    "windup": [  # the halberd rises and is drawn back over the shoulder - held
        dict(grip=(7, 6), hal=112, slide=10, lean=92, fn=(4, 0), ff=(-4, 0), glow=1),
        dict(grip=(1, -6), hal=148, slide=9, lean=97, head=4, fn=(5, 0), ff=(-5, 0), glow=2),
        dict(grip=(-1, -8), hal=158, slide=9, lean=99, head=5, fn=(6, 0), ff=(-6, 0), glow=2, by=1),
    ],
    "attack": [  # wide sweep from back-high to front-low; the blade lands on frame 1
        dict(grip=(9, -3), hal=62, slide=9, lean=84, head=-2, fn=(6, 0), ff=(-6, 0), glow=2, swoosh=0.2),
        dict(grip=(10, 7), hal=-30, slide=10, lean=74, head=-6, fn=(7, 0), ff=(-6, 0), glow=2, swoosh=0.6,
             hit=True, by=2, bx=-2),
        dict(grip=(9, 10), hal=-52, slide=10, lean=76, head=-4, fn=(7, 0), ff=(-6, 0), glow=1, swoosh=0.95, by=2,
             bx=-2),
        dict(grip=(10, 16), hal=60, slide=11, lean=86, fn=(5, 0), ff=(-4, 0), glow=1),
    ],
    "hurt": [
        dict(bx=-3, lean=100, head=10, grip=(7, 18), hal=100, eye="dim", chips=0.3, crack=1, glow=0),
        dict(bx=-2, lean=95, head=5, grip=(8, 19), hal=94, crack=1, glow=1),
    ],
    "death": [  # cracks race across the jade, it tips back, falls and lies broken
        dict(bx=-3, lean=100, head=10, grip=(7, 18), hal=100, eye="dim", chips=0.3, crack=2, glow=0),
        dict(bx=-3, lean=102, head=14, grip=(4, 12), hal=120, eye="dim", crack=3, glow=0, chips=0.7),
        dict(bx=6, lean=100, head=10, grip=(4, 12), hal=120, eye="dead", crack=3, glow=0, rot=38, drop=True),
        dict(bx=12, lean=96, head=6, grip=(6, 14), hal=100, eye="dead", crack=3, glow=0, rot=88, drop=True,
             chips=0.4),
        dict(bx=12, lean=96, head=6, grip=(6, 14), hal=100, eye="dead", crack=3, glow=0, rot=90, drop=True,
             chips=0.9),
    ],
})

L_THIGH, L_SHIN = 12.0, 12.0
L_UPPER, L_FORE = 9.5, 10.0
TORSO = 18.0


def _rune(cv, x, y, k, glow):
    col = RUNE_DEAD if glow == 0 else (RUNE if glow == 2 else RUNE_DIM)
    cv.stamp(GLYPHS[k % 3], round(x) - 1, round(y) - 1, {"g": col}, decal=True, name="rune")


def _leg(cv, hip, foot, far, crack):
    shade = "dark" if far else "two"
    knee = px.ik2(hip, (foot[0] - 1.0, foot[1] - 3.0), L_THIGH, L_SHIN, bend=1)
    mat = JADE_D if far else JADE
    cv.limb([hip, knee], [5.2, 4.4], mat, shade=shade, name="leg")
    # greave: a tapered plate over the shin
    cv.limb([knee, (foot[0] - 1.0, foot[1] - 3.0)], [4.6, 3.4], mat, shade=shade, name="leg",
            sep=False if far else "deep")
    cv.circle(knee[0] + 0.8, knee[1], 3.0, BRONZE, shade="dark" if far else "two", name="knee")
    # blocky sabaton
    cv.polygon([(foot[0] - 4.4, foot[1] - 4.4), (foot[0] + 2.2, foot[1] - 4.4), (foot[0] + 6.0, foot[1] - 0.6),
                (foot[0] + 6.0, foot[1] + 1.0), (foot[0] - 4.4, foot[1] + 1.0)], mat, shade=shade, name="foot",
               sep=False if far else "deep")
    if not far and crack >= 2:
        cv.line((round(knee[0]) - 1, round(knee[1]) + 2), (round(knee[0]) + 1, round(knee[1]) + 7), CRACK,
                decal=True, name="leg")


def _arm(cv, shoulder, hand, far):
    shade = "dark" if far else "soft"
    mat = JADE_D if far else JADE
    d = math.hypot(hand[0] - shoulder[0], hand[1] - shoulder[1])
    if d < L_UPPER + L_FORE - 0.3:
        elbow = px.ik2(shoulder, hand, L_UPPER, L_FORE, bend=-1)
    else:
        elbow = px.lerp_pt(shoulder, hand, L_UPPER / (L_UPPER + L_FORE))
    cv.limb([shoulder, elbow, hand], [4.2, 3.6, 3.2], mat, shade=shade, name="arm_far" if far else "arm",
            sep=False if far else "deep")
    # bronze vambrace on the forearm and a stone fist
    cv.limb([px.lerp_pt(elbow, hand, 0.35), px.lerp_pt(elbow, hand, 0.8)], [3.7, 3.3], BRONZE,
            shade="dark" if far else "two", decal=True, clip="arm_far" if far else "arm")
    cv.circle(hand[0], hand[1], 3.0, mat, shade=shade, name="fist", sep=False if far else "deep")


def _halberd(cv, G, ang, glow, name="halberd"):
    """Bronze-shod wooden shaft, jade axe blade facing forward, spear tip and back spike."""
    d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    butt = (G[0] - d[0] * 17.0, G[1] - d[1] * 17.0)
    top = (G[0] + d[0] * 32.0, G[1] + d[1] * 32.0)
    cv.limb([butt, top], 1.1, SHAFT, shade="two", name=name)
    cv.limb([butt, px.lerp_pt(butt, top, 0.06)], 1.4, BRONZE, shade="two", name=name)
    # axe head: the blade sweeps out on the forward side of the shaft
    fwd = ang - 90
    h0 = px.polar(top, ang + 180, 9.0)
    h1 = px.polar(top, ang + 180, 2.5)
    blade = [px.polar(h0, fwd, 1.0), px.polar(px.polar(h0, ang + 180, 1.8), fwd, 7.5),
             px.polar(px.lerp_pt(h0, h1, 0.5), fwd, 8.6), px.polar(px.polar(h1, ang, 1.4), fwd, 7.2),
             px.polar(h1, fwd, 1.0)]
    cv.polygon(blade, BLADE, name=name, sep="deep")
    # the edge: a pale sharpened rim
    cv.line((round(blade[1][0]), round(blade[1][1])), (round(blade[3][0]), round(blade[3][1])), BLADE.light,
            band=0, decal=True, clip=name, name=name)
    # spear tip + back spike + bronze collar
    tip = px.polar(top, ang, 6.5)
    cv.polygon([px.polar(top, fwd, 1.8), tip, px.polar(top, ang + 90, 1.8)], BLADE, name=name, sep="deep")
    cv.polygon([px.polar(px.lerp_pt(h0, h1, 0.4), ang + 90, 1.0), px.polar(px.lerp_pt(h0, h1, 0.55), ang + 90, 5.0),
                px.polar(px.lerp_pt(h0, h1, 0.8), ang + 90, 1.0)], BRONZE, shade="two", name=name)
    cv.limb([px.polar(h0, ang + 180, 1.0), h1], 1.8, BRONZE, shade="two", name=name)
    if glow:  # rune dots along the shaft
        for t in (0.35, 0.5):
            q = px.lerp_pt(butt, top, t)
            cv.pixel(math.floor(q[0]), math.floor(q[1]), RUNE if glow == 2 else RUNE_DIM, name=name)
    return tip, px.lerp_pt(h0, h1, 0.5), px.polar(px.lerp_pt(h0, h1, 0.5), fwd, 8.6)


def _head(cv, H, p):
    """Round helmet with a stone crest, cheek guard and a stern mask with an eye slit."""
    cv.limb([(H[0] - 4.0, H[1] - 3.0), (H[0] - 1.0, H[1] - 8.2), (H[0] + 3.0, H[1] - 7.4)], [1.8, 2.4, 1.4],
            JADE_D, shade="two", name="crest")
    cv.ellipse(H[0], H[1], 6.0, 6.2, JADE, name="helm", sep="deep")
    cv.limb([(H[0] - 5.2, H[1] - 0.6), (H[0] + 4.8, H[1] - 1.4)], 1.1, BRONZE, shade="two", decal=True,
            clip="helm", name="helm")
    # mask: a flat stone face plate at the front of the helmet
    cv.polygon([(H[0] + 1.0, H[1] - 0.2), (H[0] + 5.8, H[1] - 0.6), (H[0] + 6.2, H[1] + 3.2),
                (H[0] + 4.2, H[1] + 5.6), (H[0] + 1.4, H[1] + 5.0)], JADE, shade="two", name="mask", sep="deep")
    cv.line((round(H[0] + 3), round(H[1] + 4)), (round(H[0] + 5), round(H[1] + 4)), JADE.deep, name="mask")
    ex, ey = round(H[0] + 3), round(H[1] + 1)
    if p.eye == "dead":
        cv.pixels([(ex, ey), (ex + 1, ey), (ex + 2, ey)], JADE.deep, name="eye")
    else:
        cv.pixels([(ex, ey), (ex + 1, ey), (ex + 2, ey)], RUNE if p.eye == "open" else RUNE_DIM, name="eye")
        if p.eye == "open":
            cv.pixel(ex + 1, ey - 1, JADE.deep, name="brow")
            cv.pixel(ex + 2, ey - 1, JADE.deep, name="brow")
    if p.crack >= 2:
        cv.line((round(H[0] - 2), round(H[1] - 5)), (round(H[0] + 1), round(H[1] - 1)), CRACK, decal=True,
                name="helm")
        cv.line((round(H[0] + 1), round(H[1] - 1)), (round(H[0]), round(H[1] + 3)), CRACK, decal=True, name="helm")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    ground = cv.ground
    P = (cv.gx - 4 + p.bx, ground - 25.0 + p.by)
    S = px.polar(P, p.lean, TORSO)
    xf = []
    if p.rot:
        xf = [px.rotate(p.rot, (P[0] - 5, ground) if p.rot < 60 else P)]
        cv.snap_ground = True
    G = (S[0] + p.grip[0], S[1] + p.grip[1])
    hd = (math.cos(math.radians(p.hal)), -math.sin(math.radians(p.hal)))
    G2 = (G[0] - hd[0] * p.slide, G[1] - hd[1] * p.slide)
    shoulders = [px.polar(S, p.lean - 90, 2.0), px.polar(S, p.lean - 90, 4.2)]

    def foot(i):
        f = p.fn if i == 0 else p.ff
        return (P[0] + f[0], ground - f[1])

    halb = None
    with cv.xform(*xf):
        _leg(cv, (P[0] + 1.0, P[1] + 1.0), foot(1), True, p.crack)
        if not p.drop:
            _arm(cv, shoulders[1], G2, True)
        # torso: cuirass tapering to the waist, bronze belt, tassets
        up = p.lean
        w = lambda q, a, r: px.polar(q, a, r)
        waist = px.polar(P, up, 3.0)
        chest = [w(waist, up - 90, 6.6), w(S, up - 90, 9.0), w(px.polar(S, up, 2.6), up - 60, 6.2),
                 w(px.polar(S, up, 2.8), up + 60, 6.0), w(S, up + 90, 8.4), w(waist, up + 90, 6.2)]
        cv.polygon(chest, JADE, name="body")
        cv.limb([w(waist, up + 90, 6.4), w(waist, up - 90, 6.8)], 1.8, BRONZE, shade="two", name="belt")
        for k, off in enumerate((-4.8, -0.6, 3.6)):  # tasset plates hanging from the belt
            q = w(waist, up - 90, off)
            cv.polygon([w(q, up + 90, 2.2), w(q, up - 90, 2.2), w(w(q, up + 180, 8.0), up - 90, 2.6),
                        w(w(q, up + 180, 8.4), up + 90, 1.9)], JADE_D if k == 0 else JADE, shade="two", name="tasset",
                       sep="deep")
        tq = w(w(waist, up - 90, 3.6), up + 180, 4.6)  # rune on the front tasset
        _rune(cv, tq[0], tq[1], 2, p.glow)
        # carved seam down the cuirass and a glowing rune on the chest
        c0, c1 = w(S, up + 180, 1.5), w(waist, up + 180, -1.0)
        cv.line((round(c0[0]), round(c0[1])), (round(c1[0]), round(c1[1])), JADE.deep, band=None, decal=True,
                clip="body", name="body")
        rc = w(px.lerp_pt(S, waist, 0.45), up - 90, 3.0)
        _rune(cv, rc[0], rc[1], 0, p.glow)
        if p.crack >= 1:
            a0 = w(px.lerp_pt(S, waist, 0.2), up - 90, 6.5)
            a1 = w(px.lerp_pt(S, waist, 0.5), up - 90, 1.0)
            a2 = w(px.lerp_pt(S, waist, 0.75), up + 90, 3.0)
            for a, b in ((a0, a1), (a1, a2)):
                cv.line((round(a[0]), round(a[1])), (round(b[0]), round(b[1])), CRACK, decal=True, name="body")
        _leg(cv, (P[0] - 1.0, P[1] + 1.5), foot(0), False, p.crack)
        # halberd in the hands (behind the near arm)
        if not p.drop:
            halb = _halberd(cv, G, p.hal, p.glow)
        H = w(S, up + 4, 9.5)
        with cv.xform(px.rotate(p.head, H)):
            _head(cv, H, p)
        # pauldron over the near shoulder with a rune, then the near arm
        pa = w(S, up - 90, 1.0)
        cv.ellipse(pa[0], pa[1] + 0.5, 6.4, 5.2, JADE, angle=up - 90, name="pauldron", sep="deep")
        cv.limb([w(pa, up + 150, 5.6), w(pa, up - 150, 5.8)], 1.1, BRONZE, shade="two", decal=True, clip="pauldron",
                name="pauldron")
        _rune(cv, pa[0], pa[1] - 0.5, 1, p.glow)
        if not p.drop:
            _arm(cv, shoulders[0], G, False)
        else:
            _arm(cv, shoulders[0], w(shoulders[0], up + 150, 16.0), False)
    if p.drop:  # the halberd lies on the ground in front
        halb = _halberd(cv, (cv.gx + 14, ground - 1.6), 172, 0)
    if p.swoosh is not None:
        fx = cv.layer(above=False, outline=False)
        t = p.swoosh
        c = (S[0] + 4, S[1] + 4)
        a1 = 70 - 110 * min(1.0, t + 0.2)
        hc.arc_line(fx, c, 34.0, 95, a1, hc.WIND, name="swoosh")
        hc.arc_line(fx, c, 31.0, 90, a1 + 8, px.rgb("#a7e3c6"), name="swoosh")
        if t > 0.5:
            hc.arc_line(fx, c, 28.0, 60, a1 + 16, px.rgb("#5fae8e"), name="swoosh")
    if p.hit and halb is not None:
        top = cv.layer(above=True, outline=False)
        px.impact(top, halb[2][0], halb[2][1], size=4)
    if p.chips is not None:
        ch = cv.layer(above=True, outline=True)
        t = p.chips
        base = (S[0] - 1, S[1] + 6) if not p.rot else (cv.gx - 6, ground - 8)
        for k, (vx, vy) in enumerate(((-5, 6), (-2, 8), (3, 7), (-7, 3))):
            x = base[0] + vx * t * 1.4
            y = base[1] - (vy * t * 1.6 - 5 * t * t)
            ch.polygon([(x - 1.2, y + 0.8), (x, y - 1.2), (x + 1.2, y + 0.6)], JADE, shade="two", name="chip")
