"""Bamboo monkey - small, agile green-gold monkey with a bamboo-leaf tuft (Wood element).

View: side, facing right.  ~32 art px tall in its hunched crouch (cell 128).
Parts, back to front: curling tail, far leg, far arm (long, knuckles on the ground),
torso (rump + chest as one form, olive mantle over gold fur, pale belly), near leg
(folded frog-crouch, thigh over the rump), head group (ear, skull, pale heart-shaped face,
muzzle, big amber eye, leaf tuft), near arm holding a bamboo shoot.
Walk: a bounding lope (two airborne frames).  Windup: shoot drawn back over the shoulder.
Attack: overhand throw - the shoot leaves the hand on the hit frame (the engine draws the
projectile).  Death: tumbles over backwards and lies still, tail limp.
"""
import math

import pixel as px
import helpers_batch_b as hb

SPEC = {
    "id": "bamboo_monkey",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["walk", 2], ["walk", 3], ["death", 1]],
}

# ---- palette: gold fur, olive-green mantle, pale peach skin, fresh bamboo greens -----------
FUR = px.material("monkey_fur", "#fbd98a", "#d9a24c", "#a06a36", "#63432e", outline="#1a1009",
                  thresholds=(0.9, 0.55, 0.18))
MANTLE = px.material("monkey_mantle", "#bdc460", "#879a3e", "#56693a", "#34452f", outline="#0f170b",
                     thresholds=(0.9, 0.55, 0.18))
SKIN = px.material("monkey_skin", "#ffe4bd", "#efbd92", "#bd8468", "#7d5048", outline="#1e120e")
LEAF = px.material("bamboo_leaf", "#b9ec7c", "#62b34f", "#34804a", "#1f5040", outline="#08170f")
CANE = px.material("bamboo_cane", "#d9f59a", "#8fd05e", "#4f9a4a", "#2b6040", outline="#0a1a10")
NODE = px.material("bamboo_node", "#f4f0c0", "#d6d28a", "#9aa45a", "#5f6c3c", outline="#0a1a10")
IRIS = px.rgb("#d4781e")
MOUTH = px.rgb("#5a2424")
TOOTH = px.rgb("#fbf4dc")

# ---- poses --------------------------------------------------------------------------------
# bx, by   hip offset          crouch  lower the hips       lean  torso lean (deg, + = forward)
# head     head tilt (deg, + = chin up)
# hn       near hand target from the near shoulder (dx, dy)
# hf       far hand target from the far shoulder (dx, dy); hfg=True plants it on the ground
# shoot    shoot angle in the near hand (deg, 90 = up) or None (empty hand)
# fn, ff   near / far foot offset (dx, lift) from the resting stance   tuck  knee lift (air)
# tail     curl phase   eye  open|angry|squeeze|dead   mouth  0..1
# rot      whole-body roll (tumble)   lie  on its back   fade  opacity   whoosh  throw streak
DEFAULTS = dict(bx=0, by=0, crouch=0, lean=32, head=0, hn=(4.5, 5.5), hf=(4.0, 0.0), hfg=True,
                shoot=50, fn=(0, 0), ff=(0, 0), tuck=0, tail=0.0, eye="open", mouth=0.0, rot=0,
                lie=False, fade=1.0, whoosh=0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # hunched on its haunches, knuckles down, shoot at the ready
        dict(),
        dict(tail=0.6, head=3, hn=(4.5, 5.0)),
        dict(tail=1.2, head=3, crouch=1, hn=(4.5, 5.0), shoot=46),
        dict(tail=1.8, head=-1, crouch=1),
    ],
    "walk": [  # bounding lope: plant - gather - push off - fly - reach - land
        dict(crouch=1, lean=44, hf=(9.0, 0.0), fn=(-3, 0), ff=(-2, 0), tail=0.0),
        dict(crouch=2, lean=50, bx=1, hf=(7.0, 0.0), fn=(1, 0), ff=(2, 0), tail=0.6, head=-2),
        dict(bx=2, by=-3, lean=30, hf=(8.0, 5.0), hfg=False, fn=(-4, 2), ff=(-3, 2), tail=1.2, head=4),
        dict(bx=3, by=-4, lean=26, hf=(10.0, 7.0), hfg=False, fn=(0, 4), ff=(1, 4), tuck=2, tail=1.8,
             head=4),
        dict(bx=3, by=-1, lean=38, hf=(11.0, 0.0), fn=(1, 1), ff=(2, 2), tuck=1, tail=2.4),
        dict(bx=1, lean=42, hf=(10.0, 0.0), fn=(-1, 0), ff=(0, 0), tail=3.0),
    ],
    "windup": [  # rears up, shoot drawn back over the shoulder, chattering - held
        dict(lean=18, head=6, hn=(-2.5, -4.0), shoot=128, eye="angry", mouth=0.5, hf=(6.0, 2.0),
             hfg=False, tail=0.4),
        dict(lean=4, head=12, hn=(-5.0, -7.0), shoot=150, eye="angry", mouth=1.0, hf=(6.0, -1.0),
             hfg=False, tail=0.8, bx=-1, crouch=1),
        dict(lean=0, head=14, hn=(-5.5, -8.0), shoot=156, eye="angry", mouth=1.0, hf=(6.5, -2.0),
             hfg=False, tail=1.0, bx=-1, crouch=1),
    ],
    "attack": [  # overhand throw: whip over the top, release on frame 1, follow through
        dict(lean=16, head=8, hn=(0.5, -9.5), shoot=100, eye="angry", mouth=1.0, hf=(4.0, 5.0), hfg=False,
             tail=1.4, whoosh=1),
        dict(lean=40, head=-2, bx=1, hn=(9.0, -2.0), shoot=None, eye="angry", mouth=0.7, hf=(0.0, 7.0),
             hfg=False, tail=1.8, whoosh=2),
        dict(lean=46, head=-4, bx=1, hn=(7.0, 6.0), shoot=None, eye="angry", mouth=0.3, hf=(8.0, 0.0),
             tail=2.2, crouch=1),
        dict(lean=36, head=0, hn=(4.5, 5.0), shoot=None, mouth=0.1, tail=2.6),
    ],
    "hurt": [
        dict(bx=-3, lean=6, head=16, hn=(3.0, 3.0), shoot=20, hf=(1.0, -4.0), hfg=False, eye="squeeze",
             mouth=0.8, tail=2.0),
        dict(bx=-2, lean=18, head=8, hn=(3.5, 4.0), shoot=30, hf=(4.0, 3.0), hfg=False, eye="squeeze", mouth=0.4,
             tail=2.4),
    ],
    "death": [  # knocked back, tumbles over backwards, lands on its back, fades
        dict(bx=-3, lean=0, head=18, hn=(-1.0, -6.0), hf=(0.0, -5.0), hfg=False, eye="squeeze", mouth=0.8,
             shoot=None, tail=2.0),
        dict(bx=-6, by=-4, lean=10, rot=80, head=10, hn=(-3.0, -6.0), hf=(-2.0, -6.0), hfg=False, eye="dead",
             mouth=0.6, shoot=None, fn=(2, 3), ff=(3, 3), tail=2.5),
        dict(lie=True, eye="dead", shoot=None, mouth=0.5),
        dict(lie=True, eye="dead", shoot=None, mouth=0.5, fade=0.6),
        dict(lie=True, eye="dead", shoot=None, mouth=0.5, fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _tail(cv, root, phase, lie=False):
    """Long tail sweeping back, then curling up into a loose spiral."""
    pts = [root]
    a = 200 + 6 * math.sin(phase * 1.4)
    q = root
    for k, ln in enumerate((3.6, 3.6, 3.4, 3.0, 2.6, 2.2, 1.9, 1.6)):
        if lie:
            a -= 5 if k < 5 else 28
        else:
            a -= 4 if k < 2 else 31 + 4 * math.sin(phase * 1.6 + k)
        q = px.polar(q, a, ln)
        pts.append(q)
    cv.limb(pts, [1.7, 1.5, 1.35, 1.2, 1.1, 1.0, 0.9, 0.8, 0.65], MANTLE, shade="soft", name="tail")
    cv.limb(pts[-3:], [1.0, 0.9, 0.65], FUR, shade="soft", decal=True, clip="tail")  # gold tip


def _shoot(cv, hand, ang, name="shoot"):
    """Short bamboo cane with a sharp cut end, gripped near its base: pale nodes, a leaf."""
    base = px.polar(hand, ang, -3.0)
    tip = px.polar(hand, ang, 6.5)
    cv.limb([base, tip], [1.25, 0.9], CANE, shade="soft", name=name, sep="deep")
    n = ang + 90
    for t in (0.18, 0.62):  # nodes
        c = px.lerp_pt(base, tip, t)
        cv.limb([px.polar(c, n, 1.4), px.polar(c, n, -1.4)], 0.55, NODE, shade="flat", decal=True, clip=name)


def _arm(cv, sh, hand, far, sep=False, bend=-1, ln=5.2):
    el = px.ik2(sh, hand, ln, ln, bend=bend)
    shade = "dark" if far else "soft"
    cv.limb([sh, el, hand], [1.9, 1.45, 1.2], FUR, shade=shade, name="arm", sep=sep)
    cv.circle(hand[0] + 0.3, hand[1] + 0.1, 1.4, SKIN, shade="dark" if far else "two", name="hand")


def _leg(cv, hip, foot, far, sep=False, tuck=0):
    """Frog-folded monkey leg: thigh forward and up, shin back down, long flat foot."""
    fx, fy = foot
    ankle = (fx - 1.2, fy - 1.3)
    knee = px.ik2(hip, ankle, 5.6, 5.4, bend=1)
    knee = (knee[0] + 0.5 * tuck, knee[1] - 0.5 * tuck)
    shade = "dark" if far else "soft"
    cv.limb([hip, knee, ankle], [2.8, 1.8, 1.25], FUR, shade=shade, name="leg", sep=sep)
    cv.limb([(ankle[0] - 0.2, fy - 0.8), (fx + 2.4, fy - 0.6)], [1.15, 0.8], SKIN,
            shade="dark" if far else "two", name="foot")


def _head(cv, Hc, p):
    head = cv.union(cv.geom_ellipse(Hc[0], Hc[1], 5.2, 4.9),
                    cv.geom_ellipse(Hc[0] + 4.2, Hc[1] + 2.0, 2.5, 2.1), weights=[1.0, 0.7])
    cv.draw_geom(head, MANTLE, name="head", sep="deep")
    cv.ellipse(Hc[0] - 3.4, Hc[1] + 0.4, 1.5, 1.8, SKIN.step(1), shade="two", name="ear", sep="deep")
    cv.pixel(math.floor(Hc[0] - 3.4), math.floor(Hc[1] + 0.4), SKIN.deep, name="ear")
    # gold cheek ruff behind the face, pale heart-shaped face + muzzle
    cv.ellipse(Hc[0] + 0.6, Hc[1] + 1.6, 3.2, 3.0, FUR, shade="soft", decal=True, clip="head")
    face = cv.union(cv.geom_ellipse(Hc[0] + 2.5, Hc[1] + 0.3, 2.7, 3.3),
                    cv.geom_ellipse(Hc[0] + 4.4, Hc[1] + 2.1, 2.4, 1.9))
    cv.draw_geom(face, SKIN, shade="flatlight", decal=True, clip="head")
    cv.ellipse(Hc[0] + 4.6, Hc[1] + 3.0, 2.0, 0.9, SKIN, shade="flat", decal=True, clip="head")
    nx, ny = math.floor(Hc[0] + 5.4), math.floor(Hc[1] + 1.3)
    cv.pixel(nx, ny, SKIN.deep, name="nose")
    if p.mouth > 0.3:  # chattering: open mouth with teeth
        rows = ["tt.", "mmm", ".m."] if p.mouth > 0.7 else ["tt", "mm"]
        cv.stamp(rows, nx - 2, ny + 2, {"t": TOOTH, "m": MOUTH}, name="mouth")
    else:
        cv.line((nx - 2, ny + 2), (nx, ny + 2), SKIN.deep, name="mouth")
    # heavy brow + big amber eye (2 x 3)
    ex, ey = math.floor(Hc[0] + 2.3), math.floor(Hc[1] - 1.5)
    cv.line((ex - 1, ey - 1), (ex + 2, ey - 1), MANTLE.shadow, name="brow")
    if p.eye in ("open", "angry"):
        cv.stamp(["gi", "ik", "kk"], ex, ey, {"k": px.INK, "g": px.GLINT, "i": IRIS}, name="eye")
        if p.eye == "angry":
            cv.pixels([(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)], MANTLE.deep, name="brow")
    else:
        hb.eye(cv, ex, ey + 1, p.eye)
    # bamboo-leaf tuft sprouting from the crown, swept back
    for ang, ln, w in ((140, 6.2, 1.15), (112, 5.6, 1.1), (88, 4.4, 1.0)):
        root = px.polar((Hc[0] - 0.6, Hc[1] - 3.8), ang, 0.5)
        mid = px.polar(root, ang + 4, ln * 0.5)
        tip = px.polar(mid, ang + 26, ln * 0.55)
        cv.limb([root, mid, tip], [0.6, w, 0.35], LEAF, shade="soft", name="leaf", sep="deep")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cv.opacity = p.fade
    if p.lie:
        _draw_lying(cv, p, ground)
        return
    Hp = (cv.gx - 4 + p.bx, ground - 8.0 + p.crouch + p.by)
    xf = [px.rotate(p.rot, (Hp[0] + 2, Hp[1] - 6))] if p.rot else []
    up = 90 - p.lean
    Sh = px.polar(Hp, up, 11.0)
    Hc = px.polar(Sh, up - 12 + p.head * 0.3, 7.2)

    def foot(base_dx, f):
        return (Hp[0] + base_dx + f[0], ground - f[1])

    fsh = (Sh[0] + 1.0, Sh[1] + 1.0)
    fhand = (fsh[0] + p.hf[0], ground - 1.0 if p.hfg else fsh[1] + p.hf[1])
    nsh = (Sh[0] - 0.8, Sh[1] + 1.6)
    hand = (nsh[0] + p.hn[0], nsh[1] + p.hn[1])
    with cv.xform(*xf):
        _tail(cv, (Hp[0] - 4.0, Hp[1] + 0.5), p.tail)
        _leg(cv, (Hp[0] + 0.5, Hp[1] + 0.5), foot(1.5, p.ff), far=True, tuck=p.tuck)
        reach = math.hypot(fhand[0] - fsh[0], fhand[1] - fsh[1])
        _arm(cv, fsh, fhand, far=True, bend=-1, ln=max(5.2, reach / 2 + 0.2))
        # torso: rump + chest as one form, olive mantle over the back, gold belly
        torso = cv.union(cv.geom_ellipse(Hp[0] - 0.5, Hp[1] - 1.8, 5.0, 4.8),
                         cv.geom_limb([px.polar(Hp, up, 2.5), Sh], [4.8, 4.6]), weights=[1.0, 0.9])
        cv.draw_geom(torso, FUR, name="body", sep="deep")
        back = cv.union(cv.geom_ellipse(Hp[0] - 1.8, Hp[1] - 2.8, 4.6, 4.4),
                        cv.geom_limb([px.polar((Hp[0] - 1.6, Hp[1] - 1.0), up, 2.5), (Sh[0] - 1.7, Sh[1] - 0.8)],
                                     [4.2, 4.0]))
        cv.draw_geom(back, MANTLE, decal=True, clip="body")
        bc = px.polar(Hp, up, 5.5)
        cv.ellipse(bc[0] + 3.0, bc[1] + 1.0, 2.3, 4.6, SKIN, angle=-p.lean, shade="two", decal=True,
                   clip="body")
        _leg(cv, (Hp[0] - 0.8, Hp[1] + 0.2), foot(-0.5, p.fn), far=False, sep="deep", tuck=p.tuck)
        with cv.xform(px.rotate(p.head, (Sh[0] + 1.5, Sh[1] - 1.0))):
            _head(cv, Hc, p)
        drawn_back = p.hn[1] < -2 and p.hn[0] < 2
        if p.shoot is not None and drawn_back:  # shoot behind the arm when cocked back
            _shoot(cv, hand, p.shoot)
        _arm(cv, nsh, hand, far=False, sep="deep", bend=1 if p.hn[1] < 0 else -1)
        if p.shoot is not None and not drawn_back:
            _shoot(cv, hand, p.shoot)
        rel = cv.tp(hand)
    if p.whoosh:  # throw arc: short pale streak trailing the hand
        fx = cv.layer(above=False, outline=False)
        r = math.hypot(p.hn[0], p.hn[1])
        a_hand = math.degrees(math.atan2(-p.hn[1], p.hn[0]))
        for k in range(2, 7):
            q = px.polar(nsh, a_hand + 11 * k, r + 1.0)
            fx.pixel(math.floor(q[0]), math.floor(q[1]), px.PAPER if k < 5 else px.MIST_BLUE, name="whoosh")
    if action == "attack" and frame == SPEC["hit_frame"]:
        top = cv.layer(above=True, outline=False)
        px.impact(top, rel[0] + 3, rel[1], size=2, color=CANE.light)


def _draw_lying(cv, p, ground):
    """On its back after the tumble: belly up, limbs loose, tail trailing."""
    cv.snap_ground = True
    Hp = (cv.gx - 2, ground - 4.5)
    _tail(cv, (Hp[0] - 4.0, Hp[1] + 1.5), 0.0, lie=True)
    # far limbs flopped up
    cv.limb([(Hp[0] + 1, Hp[1] - 1), (Hp[0] + 3, Hp[1] - 7), (Hp[0] + 6, Hp[1] - 7.5)], [2.4, 1.6, 1.2], FUR,
            shade="dark", name="leg")
    torso = cv.union(cv.geom_ellipse(Hp[0] + 1.0, Hp[1] + 0.5, 5.0, 4.4),
                     cv.geom_limb([(Hp[0] + 2.0, Hp[1] + 0.8), (Hp[0] + 10.5, Hp[1] + 1.0)], [4.4, 4.2]),
                     weights=[1.0, 0.9])
    cv.draw_geom(torso, MANTLE, name="body", sep="deep")
    cv.ellipse(Hp[0] + 5.5, Hp[1] - 2.0, 5.5, 2.4, FUR, shade="soft", decal=True, clip="body")
    cv.ellipse(Hp[0] + 6.0, Hp[1] - 2.8, 3.6, 1.4, SKIN, shade="two", decal=True, clip="body")
    # near leg bent up, foot in the air
    cv.limb([(Hp[0] - 0.5, Hp[1] - 1.5), (Hp[0] + 1.5, Hp[1] - 7.0), (Hp[0] + 3.5, Hp[1] - 6.5)],
            [2.6, 1.7, 1.25], FUR, shade="soft", name="leg", sep="deep")
    cv.limb([(Hp[0] + 3.2, Hp[1] - 6.8), (Hp[0] + 6.2, Hp[1] - 7.4)], [1.1, 0.8], SKIN, shade="two", name="foot")
    Hc = (Hp[0] + 15.0, Hp[1] + 0.2)
    with cv.xform(px.rotate(-95, Hc)):
        _head(cv, Hc, p)
    cv.limb([(Hp[0] + 9.5, Hp[1] - 1.5), (Hp[0] + 12.5, Hp[1] - 5.5), (Hp[0] + 17.0, Hp[1] - 6.5)],
            [1.8, 1.4, 1.15], FUR, shade="soft", name="arm", sep="deep")
    cv.circle(Hp[0] + 17.5, Hp[1] - 6.5, 1.4, SKIN, shade="two", name="hand")
