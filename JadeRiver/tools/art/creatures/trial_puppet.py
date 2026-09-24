"""Trial puppet - a wooden training puppet shaped like a cultivator, animated for sect
trials: jointed wooden limbs lashed with hemp rope, a carved face with painted jade marks,
a plank shield strapped to its left arm (Wood / construct, elite-sized, cell 192).

View: side, facing right, ~53 art px tall (topknot included).
Parts, back to front: far leg, far (left) arm, pelvis + waist rope + chest block (lacquered
as a jade cultivator robe with a pale cross collar and belt), neck dowel, carved head (topknot + jade pin, brow ridge, glowing eye slit,
jade tear stripe and forehead diamond, carved mouth), near leg, plank shield (three planks,
rope straps, iron studs) on the left forearm, near (right) arm with a mitten / open palm.
Rope bands sit on every joint.  Arms and legs are solved with ``px.ik2``.
Windup raises the shield, then drops into a counter stance; the palm strike lands on
``hit_frame`` with a jade Qi flash.  Death: the joints give and it falls into a heap.
"""
import math

import pixel as px

SPEC = {
    "id": "trial_puppet",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: honey training wood, weathered plank shield, hemp rope, jade paint ----------
WOOD = px.material("puppet_wood", "#e6bf85", "#b98752", "#855b3a", "#5a3c2a", outline="#1a0f0a",
                   thresholds=(0.86, 0.5, 0.18))
DARKWOOD = px.material("puppet_dark", "#b88b5a", "#8a6140", "#63452f", "#432f22", outline="#1a0f0a")
PLANK = px.material("shield_plank", "#bba88a", "#86745b", "#5f5243", "#3f372f", outline="#120e0b",
                    thresholds=(0.9, 0.55, 0.2))
ROBE = px.material("robe_lacquer", "#6fc2aa", "#378a78", "#255f57", "#173e3c", outline="#07120f",
                   thresholds=(0.86, 0.5, 0.18))
COLLAR = px.rgb("#efe4c4")
ROPE = px.material("hemp_rope", "#f0e2b0", "#cdb67e", "#9c8659", "#6b5b3f", outline="#1c160c")
JADE = px.material("jade_paint", "#8fe8d0", "#3fb09c", "#23786c", "#164c48", outline="#0a1d1c")
IRON = px.material("shield_iron", "#9aa2a6", "#646c72", "#454b51", "#2c3136", outline="#0d1013")
GLOW = px.rgb("#8ff5dc")
GLOW_CORE = px.rgb("#e8fff6")
CARVE = WOOD.step(2)

# ---- poses --------------------------------------------------------------------------------
# bx, by  hip offset       crouch  lowers the hips (knees bend)   lean  torso tilt (deg, + back)
# head    head tilt (deg)  nh / fh  near / far hand target (dx, dy) from its shoulder
# nb / fb elbow bend side (+1 / -1)   nf / ff  near / far foot (dx from hip, lift)
# shield  shield tilt (deg)   palm  open palm (strike)   eye  open|angry|squeeze|dead
# qi      jade flash at the palm (0 = off)   pile  0 = standing, 1 = falling apart, 2 = heap
DEFAULTS = dict(bx=0, by=0, crouch=0.0, lean=0, head=0, nh=(1.5, 12.0), fh=(7.0, 7.0), nb=-1, fb=-1,
                nf=(2.0, 0), ff=(-2.0, 0), shield=0, palm=False, eye="open", qi=0.0, pile=0, fade=1.0,
                hit=False, loose=0.0, charge=False)

POSE = px.poses(DEFAULTS, {
    "idle": [  # a creaking sway on its pegs, shield held low, head ticking side to side
        dict(),
        dict(head=3, fh=(7.0, 6.5)),
        dict(by=1, head=4, nh=(1.8, 11.5), fh=(7.0, 6.0)),
        dict(head=1, fh=(7.0, 6.5)),
    ],
    "walk": [  # stiff marching step: legs swing on the hip peg, the free arm swings opposite
        dict(nf=(6.0, 0), ff=(-4.5, 0), nh=(-3.0, 11.0), lean=-2),
        dict(nf=(3.0, 0), ff=(-1.0, 3), nh=(-1.0, 11.5), by=-1, lean=-2),
        dict(nf=(-1.0, 0), ff=(3.0, 2), nh=(1.5, 11.5), lean=-2),
        dict(nf=(-4.5, 0), ff=(6.0, 0), nh=(4.0, 11.0), lean=-2),
        dict(nf=(-1.0, 3), ff=(3.0, 0), nh=(2.0, 11.5), by=-1, lean=-2),
        dict(nf=(3.0, 2), ff=(-1.0, 0), nh=(-1.0, 11.5), lean=-2),
    ],
    "windup": [  # raises the plank shield, then sinks into a counter stance, palm drawn back
        dict(fh=(7.0, 0.5), shield=-4, head=-2, nh=(-1.0, 10.5), eye="angry"),
        dict(fh=(8.0, -3.5), shield=-8, crouch=1.5, nf=(4.5, 0), ff=(-4.0, 0), nh=(-3.5, 8.0), head=-4,
             eye="angry"),
        dict(fh=(8.5, -1.0), shield=-4, crouch=3.0, lean=4, nf=(6.5, 0), ff=(-6.0, 0), nh=(-5.5, 5.5), nb=-1,
             palm=True, head=-4, eye="angry", charge=True),
    ],
    "attack": [  # steps in behind the shield and drives the palm out past it (hit on 1)
        dict(fh=(7.0, 1.0), crouch=2.0, bx=2, lean=-4, nf=(7.5, 0), ff=(-5.0, 0), nh=(6.0, 3.0), nb=-1,
             palm=True, eye="angry"),
        dict(fh=(5.0, 4.0), shield=6, crouch=2.0, bx=4, lean=-8, nf=(8.5, 0), ff=(-6.0, 0), nh=(13.0, 1.0),
             nb=-1, palm=True, eye="angry", qi=1.0, hit=True),
        dict(fh=(5.0, 4.5), shield=6, crouch=1.5, bx=4, lean=-6, nf=(8.0, 0), ff=(-5.5, 0), nh=(12.0, 2.0),
             nb=-1, palm=True, eye="angry", qi=0.5),
        dict(fh=(5.0, 6.0), crouch=0.5, bx=3, lean=-2, nf=(4.0, 0), ff=(-3.0, 0), nh=(3.0, 10.0)),
    ],
    "hurt": [  # knocked back: head snaps back, arms fly loose on their ropes
        dict(bx=-3, lean=12, head=16, fh=(1.0, 3.0), nh=(-4.0, 7.0), eye="squeeze", nf=(4.0, 1), ff=(-2.0, 0)),
        dict(bx=-2, lean=6, head=8, fh=(3.0, 5.0), nh=(-2.0, 9.5), eye="squeeze"),
    ],
    "death": [  # the lashings give: it sags at every joint, comes apart, lands in a heap
        dict(bx=-3, lean=12, head=16, fh=(1.0, 3.0), nh=(-4.0, 7.0), eye="squeeze", nf=(4.0, 1), ff=(-2.0, 0)),
        dict(bx=-2, crouch=7.0, lean=-18, head=-30, fh=(3.0, 11.0), nh=(3.0, 12.0), nb=1, fb=1, nf=(5.0, 0),
             ff=(-3.0, 0), eye="dead", loose=0.5),
        dict(pile=1, eye="dead"),
        dict(pile=2, eye="dead", fade=0.6),
        dict(pile=2, eye="dead", fade=0.3),
    ],
})

THIGH, SHIN = 10.8, 10.4
UPPER, FORE = 7.0, 6.6


def _rope(cv, p, direction, r, far=False):
    """Hemp lashing around a joint: a band across the limb with two dark wrap lines.
    Far-side joints skip it (it would only add noise in the shadow)."""
    if far:
        return
    d = direction
    ln = math.hypot(*d) or 1.0
    n = (-d[1] / ln, d[0] / ln)
    u = (d[0] / ln, d[1] / ln)
    a = (p[0] - n[0] * r, p[1] - n[1] * r)
    b = (p[0] + n[0] * r, p[1] + n[1] * r)
    cv.limb([a, b], 1.05, ROPE, shade="dark" if far else "two", name="rope", sep="deep")
    if not far:
        for s in (-0.5, 0.5):
            q0 = (a[0] + u[0] * s, a[1] + u[1] * s)
            q1 = (b[0] + u[0] * s, b[1] + u[1] * s)
            cv.line((math.floor(px.lerp_pt(q0, q1, 0.3)[0]), math.floor(px.lerp_pt(q0, q1, 0.3)[1])),
                    (math.floor(px.lerp_pt(q0, q1, 0.7)[0]), math.floor(px.lerp_pt(q0, q1, 0.7)[1])),
                    ROPE.step(2), decal=True, clip="rope")


def _leg(cv, hip, foot, far):
    shade = "dark" if far else "soft"
    ankle = (foot[0], foot[1] - 2.2)
    knee = px.ik2(hip, ankle, THIGH, SHIN, bend=1)
    sep = False if far else "deep"
    cv.limb([hip, knee], [2.6, 2.1], WOOD, shade=shade, name="leg", sep=sep)
    cv.limb([knee, ankle], [2.0, 1.6], WOOD, shade=shade, name="leg", sep=sep)
    # foot block
    cv.polygon([(ankle[0] - 2.2, ankle[1] - 0.6), (ankle[0] + 1.8, ankle[1] - 0.6), (ankle[0] + 4.6, foot[1] - 1.0),
                (ankle[0] + 4.6, foot[1] + 0.5), (ankle[0] - 2.4, foot[1] + 0.5)], DARKWOOD,
               shade="dark" if far else "two", name="foot", sep=sep)
    _rope(cv, knee, (knee[0] - hip[0], knee[1] - hip[1]), 2.2, far)
    _rope(cv, ankle, (ankle[0] - knee[0], ankle[1] - knee[1]), 1.7, far)


def _arm(cv, sh, hand, bend, far, palm=False):
    shade = "dark" if far else "soft"
    elbow = px.ik2(sh, hand, UPPER, FORE, bend=bend)
    sep = False if far else "deep"
    cv.limb([sh, elbow], [1.9, 1.6], WOOD, shade=shade, name="arm", sep=sep)
    cv.limb([elbow, hand], [1.6, 1.3], WOOD, shade=shade, name="arm", sep=sep)
    cv.circle(elbow[0], elbow[1], 1.7, WOOD, shade="dark" if far else "soft", name="joint", sep=sep)
    _rope(cv, elbow, (elbow[0] - sh[0], elbow[1] - sh[1]), 1.9, far)
    d = (hand[0] - elbow[0], hand[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    if palm:  # open palm pushed out, fingers up
        cv.polygon([(hand[0] - 0.5, hand[1] + 2.2), (hand[0] + 2.4, hand[1] + 1.8), (hand[0] + 2.6, hand[1] - 3.2),
                    (hand[0] + 1.0, hand[1] - 3.6), (hand[0] - 0.8, hand[1] - 1.0)], WOOD,
                   shade="dark" if far else "soft", name="hand", sep=sep)
        tip = (hand[0] + 2.8, hand[1] - 0.8)
    else:  # carved mitten
        c = (hand[0] + u[0] * 1.6, hand[1] + u[1] * 1.6)
        cv.ellipse(c[0], c[1], 2.0, 1.6, WOOD, angle=math.degrees(math.atan2(-u[1], u[0])),
                   shade="dark" if far else "soft", name="hand", sep=sep)
        tip = (c[0] + u[0] * 2.0, c[1] + u[1] * 2.0)
    _rope(cv, hand, d, 1.5, far)
    return elbow, tip


def _shield(cv, c, tilt):
    """Plank shield face-on: three planks, two rope straps, iron studs, a jade training mark."""
    with cv.xform(px.rotate(tilt, c)):
        w, h = 5.0, 7.5
        pts = [(c[0] - w, c[1] - h + 0.8), (c[0] - w + 1.0, c[1] - h), (c[0] + w - 1.0, c[1] - h),
               (c[0] + w, c[1] - h + 0.8), (c[0] + w - 0.4, c[1] + h), (c[0] - w + 0.4, c[1] + h)]
        cv.polygon(pts, PLANK, name="shield", sep="deep")
        # iron edging along the top and bottom
        cv.limb([(c[0] - w + 0.8, c[1] - h + 0.6), (c[0] + w - 0.8, c[1] - h + 0.6)], 0.55, IRON, shade="two",
                decal=True, clip="shield")
        cv.limb([(c[0] - w + 0.8, c[1] + h - 0.6), (c[0] + w - 0.8, c[1] + h - 0.6)], 0.55, IRON, shade="two",
                decal=True, clip="shield")
        for dx in (-1.7, 1.7):  # plank seams
            cv.line((math.floor(c[0] + dx), math.floor(c[1] - h + 1)), (math.floor(c[0] + dx), math.floor(c[1] + h - 1)),
                    PLANK.step(2), decal=True, clip="shield")
        for dy in (-3.8, 3.8):  # rope straps across the planks
            cv.limb([(c[0] - w + 0.6, c[1] + dy), (c[0] + w - 0.6, c[1] + dy)], 0.8, ROPE, shade="two", decal=True,
                    clip="shield")
        for (dx, dy) in ((-3.4, -3.8), (3.4, -3.8), (-3.4, 3.8), (3.4, 3.8)):
            cv.pixel(math.floor(c[0] + dx), math.floor(c[1] + dy), IRON.base, name="stud", clip="shield")
        # painted jade target ring in the middle
        cv.circle(c[0], c[1], 1.7, JADE, shade="two", decal=True, clip="shield")
        cv.pixel(math.floor(c[0]), math.floor(c[1]), PLANK.base, name="shield")


def _head(cv, Hc, p):
    # topknot bun with a jade hairpin
    cv.circle(Hc[0] - 1.6, Hc[1] - 5.2, 2.0, DARKWOOD, shade="soft", name="knot")
    cv.limb([(Hc[0] - 4.8, Hc[1] - 5.8), (Hc[0] + 1.2, Hc[1] - 4.6)], 0.5, JADE, shade="flat", name="pin")
    head = cv.union(cv.geom_ellipse(Hc[0], Hc[1], 4.2, 4.9), cv.geom_ellipse(Hc[0] + 1.6, Hc[1] + 1.8, 3.0, 3.0),
                    weights=[1.0, 0.7])
    cv.draw_geom(head, WOOD, name="head", sep="deep")
    # carved features: brow ridge, eye slit, nose bump, mouth
    ex, ey = math.floor(Hc[0] + 1.5), math.floor(Hc[1] - 0.8)
    cv.line((ex - 1, ey - 2), (ex + 2, ey - 2), CARVE, decal=True, clip="head")
    cv.circle(Hc[0] + 4.3, Hc[1] + 0.8, 1.0, WOOD, shade="soft", name="nose")
    cv.line((ex, ey + 4), (ex + 2, ey + 4), CARVE, decal=True, clip="head")
    # painted jade marks: forehead diamond and a tear stripe under the eye
    cv.stamp([".j.", "jJj", ".j."], ex - 1, ey - 5, {"j": JADE.base, "J": JADE.light}, name="paint", clip="head")
    cv.line((ex, ey + 1), (ex, ey + 3), JADE.base, name="paint", clip="head")
    if p.eye == "dead":
        cv.stamp(["kk"], ex, ey, {"k": CARVE.deep}, name="eye")
    elif p.eye == "squeeze":
        cv.stamp(["kk", "..k"[:2]], ex, ey, {"k": CARVE.deep}, name="eye")
        cv.pixel(ex + 1, ey - 1, CARVE.deep, name="eye")
    else:  # carved slit lit from inside by jade spirit-light
        cv.stamp(["gw"], ex, ey, {"g": GLOW, "w": GLOW_CORE}, name="eye")
        if p.eye == "angry":
            cv.pixels([(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey - 1)], CARVE.deep, name="brow")


def _pile(cv, gx, ground, falling):
    """The puppet in pieces.  ``falling``: mid-collapse (pieces tumbling), else a heap."""
    g = ground
    if falling:
        # legs folding, torso pitching forward, head dropping off, shield sliding down
        _leg(cv, (gx - 3, g - 12.0), (gx - 7, g), True)
        _leg(cv, (gx - 1, g - 11.5), (gx + 5, g), False)
        with cv.xform(px.rotate(-50, (gx - 1, g - 12))):
            cv.ellipse(gx - 1, g - 13.0, 3.8, 2.6, WOOD, name="pelvis", sep="deep")
            chest = cv.union(cv.geom_ellipse(gx - 0.5, g - 22.5, 5.0, 6.0), cv.geom_ellipse(gx - 1, g - 17.0, 3.6, 3.2))
            cv.draw_geom(chest, ROBE, name="torso", sep="deep")
            cv.limb([(gx - 3.5, g - 27.5), (gx + 0.5, g - 22.0), (gx + 3.5, g - 19.5)], 0.6, px.flat(COLLAR),
                    decal=True, clip="torso")
        _arm(cv, (gx + 6.0, g - 16.0), (gx + 9.0, g - 7.0), 1, False)
        with cv.xform(px.rotate(-70, (gx + 15.0, g - 10.0))):
            _head(cv, (gx + 15.0, g - 10.0), _Dead)
        _shield(cv, (gx - 10.0, g - 8.5), 28)
        return
    # heap: torso lying face down, limbs crossed, the head rolled to the front, shield on top
    cv.limb([(gx - 17, g - 1.8), (gx - 6, g - 2.4)], [2.4, 2.0], WOOD, shade="soft", name="leg", sep="deep")
    cv.limb([(gx - 9, g - 1.6), (gx + 1, g - 1.8)], [2.0, 1.6], WOOD, shade="soft", name="leg", sep="deep")
    cv.circle(gx - 6.2, g - 2.4, 2.0, WOOD, shade="soft", name="joint", sep="deep")
    _rope(cv, (gx - 6.2, g - 2.4), (1, 0), 2.1)
    chest = cv.union(cv.geom_ellipse(gx + 5.0, g - 3.5, 6.0, 3.4), cv.geom_ellipse(gx - 1.0, g - 3.0, 3.4, 2.6))
    cv.draw_geom(chest, ROBE, name="torso", sep="deep")
    cv.limb([(gx + 1.0, g - 6.5), (gx + 5.0, g - 3.0), (gx + 9.0, g - 2.0)], 0.6, px.flat(COLLAR), decal=True,
            clip="torso")
    cv.limb([(gx + 2, g - 6.5), (gx + 9, g - 9.0)], [1.7, 1.4], WOOD, shade="soft", name="arm", sep="deep")
    cv.ellipse(gx + 10.2, g - 9.4, 2.0, 1.6, WOOD, shade="soft", name="hand", sep="deep")
    _shield(cv, (gx - 8.0, g - 7.0), 72)
    _head(cv, (gx + 15.5, g - 4.4), _Dead)
    cv.limb([(gx - 2, g - 1.4), (gx + 3, g - 1.2)], [1.4, 1.2], DARKWOOD, shade="two", name="foot", sep="deep")


class _Dead:  # pose stand-in for loose parts
    eye = "dead"


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cv.opacity = p.fade
    if p.pile:
        _pile(cv, cv.gx - 2, ground, p.pile == 1)
        cv.snap_ground = True
        return
    Hp = (cv.gx - 2 + p.bx, ground - 21.0 + p.by + p.crouch)
    lean = px.rotate(p.lean, Hp)
    with cv.xform(lean):
        sh_n, sh_f = cv.tp((Hp[0] + 1.0, Hp[1] - 16.2)), cv.tp((Hp[0] - 0.8, Hp[1] - 16.8))
        neck_top = (Hp[0] + 1.2, Hp[1] - 20.6)
        Hc = (Hp[0] + 1.6, Hp[1] - 25.4)
    # far leg and far (shield) arm behind the body
    _leg(cv, (Hp[0] - 1.2, Hp[1] - 0.5), (Hp[0] + p.ff[0], ground - p.ff[1]), True)
    fhand = (sh_f[0] + p.fh[0], sh_f[1] + p.fh[1])
    felbow, _ = _arm(cv, sh_f, fhand, p.fb, True)
    with cv.xform(lean):
        cv.ellipse(Hp[0], Hp[1] - 1.0, 4.0, 2.8, WOOD, name="pelvis", sep="deep")
        chest = cv.union(cv.geom_ellipse(Hp[0] + 0.6, Hp[1] - 12.2, 5.0, 6.0),
                         cv.geom_ellipse(Hp[0] + 0.2, Hp[1] - 6.2, 3.6, 3.2), weights=[1.0, 0.8])
        cv.draw_geom(chest, ROBE, name="torso", sep="deep")
        # painted cultivator robe: pale cross collar and a wooden belt band
        cv.limb([(Hp[0] - 2.5, Hp[1] - 17.2), (Hp[0] + 1.5, Hp[1] - 12.0), (Hp[0] + 4.6, Hp[1] - 9.5)], 0.6,
                px.flat(COLLAR), decal=True, clip="torso")
        cv.limb([(Hp[0] + 4.2, Hp[1] - 16.5), (Hp[0] + 2.4, Hp[1] - 13.5)], 0.5, px.flat(COLLAR), decal=True,
                clip="torso")
        cv.limb([(Hp[0] - 4.0, Hp[1] - 7.2), (Hp[0] + 4.2, Hp[1] - 6.6)], 1.0, DARKWOOD, shade="two", decal=True,
                clip="torso")
        _rope(cv, (Hp[0] + 0.2, Hp[1] - 3.4), (0, -1), 3.4)  # waist lashing
        cv.limb([(Hp[0] + 0.8, Hp[1] - 18.0), neck_top], [1.4, 1.3], WOOD, shade="two", name="neck")
        _rope(cv, (Hp[0] + 1.0, Hp[1] - 18.6), (0, -1), 1.5)
    with cv.xform(lean, px.rotate(p.head, (neck_top[0], neck_top[1]))):
        _head(cv, Hc, p)
    _leg(cv, (Hp[0] + 1.2, Hp[1] - 0.2), (Hp[0] + p.nf[0], ground - p.nf[1]), False)
    # plank shield strapped on the left forearm, carried in front of the chest
    sc = px.lerp_pt(felbow, fhand, 0.55)
    _shield(cv, (sc[0] + 1.5, sc[1]), p.shield)
    nhand = (sh_n[0] + p.nh[0], sh_n[1] + p.nh[1])
    _rope(cv, sh_n, (0, 1), 2.0)  # shoulder peg
    _, tip = _arm(cv, sh_n, nhand, p.nb, False, palm=p.palm)
    if p.charge:  # the tell: jade spirit-light gathers in the drawn-back palm
        g = cv.layer(above=True, outline=False)
        g.pixels([(math.floor(tip[0]) - 1, math.floor(tip[1]) - 1), (math.floor(tip[0]), math.floor(tip[1]) - 1),
                  (math.floor(tip[0]) - 1, math.floor(tip[1]))], GLOW, name="glow")
        g.pixel(math.floor(tip[0]), math.floor(tip[1]), GLOW_CORE, name="glow")
    if p.qi > 0:  # jade Qi bursting from the palm
        fx = cv.layer(above=True, outline=False)
        r = 1.5 + 2.5 * p.qi
        px.glow_ring(fx, tip[0] + 0.5, tip[1], r, JADE.light, thickness=1.0, inner=JADE.base if p.qi >= 1 else None)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0] + 3.5, tip[1] - 0.5, size=4)
