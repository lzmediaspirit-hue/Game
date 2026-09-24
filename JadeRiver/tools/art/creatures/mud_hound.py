"""Mud hound - lean, mud-caked bandit hound with a leather collar and brass ring (Earth).

View: side, facing right.  ~28 art px tall, ~44 long including the tail (cell 128).
Parts, back to front: far legs (dark), ragged tail, near hind leg, body (haunch + waist +
deep chest shaded as one form), clumped belly / chest tufts, dried mud decals, near
foreleg, neck + head group (jaw, skull + muzzle, nose, teeth, torn ear, eye), collar
with a hanging brass ring.  Windup: head up, barking.  Attack: lunging bite (airborne).
Death: topples onto its side, legs stiff, then fades.
"""
import math

import pixel as px
import helpers_batch_b as hb

SPEC = {
    "id": "mud_hound",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 2,
    "airborne": [["attack", 1], ["attack", 2]],
}

# ---- palette: wet mud browns, violet-grey shadows, warm ochre lights -----------------------
FUR = px.material("hound_fur", "#c7a574", "#927350", "#644f40", "#3e3232", outline="#140f0f",
                  thresholds=(0.9, 0.52, 0.16))
MUD = px.material("hound_mud", "#6a5440", "#4a3b30", "#352b27", "#231c1c", outline="#110c0c")
PALE = px.material("hound_pale", "#e0cda2", "#b8a17a", "#88745c", "#5a4c41", outline="#140f0f")
LEATHER = px.material("collar", "#a4583a", "#7a3b2a", "#552822", "#361a18", outline="#170b0a")
BRASS = px.material("brass", "#ffe6a1", "#e5b84c", "#9a6a35", "#5e4122", outline="#1e1409")
NOSE = px.material("hound_nose", "#5e4b4c", "#3a2d31", "#2a2025", "#1b1418", outline="#0c0809")
TONGUE = px.FLESH_PINK
TOOTH = px.rgb("#f6efd6")
IRIS = px.rgb("#f0b43c")

# ---- poses --------------------------------------------------------------------------------
# bx, by body offset   crouch lower body (px)   sx body stretch   rot body pitch (deg, + = up)
# head  head tilt (deg, + = nose up)   neck  neck lift (px)   jaw  0..1   ear  ear angle
# tail  (angle offset, wave)   feet  (dx, lift) near-front, far-front, near-hind, far-hind
# eye   open|angry|squeeze|dead   breathe  chest swell   lift  whole body off the ground
# side  lying on its side (death)   fade  opacity   hit  impact   bark  bark lines
DEFAULTS = dict(bx=0, by=0, crouch=0, sx=1.0, rot=0, head=0, neck=0, jaw=0.0, ear=0, tail=(0, 0.0),
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), eye="angry", breathe=0.0, lift=0, side=False,
                fade=1.0, hit=False, bark=0, tongue=False, reach=((0, 0), (0, 0), (0, 0), (0, 0)))

POSE = px.poses(DEFAULTS, {
    "idle": [  # menacing stand, panting
        dict(tongue=True, jaw=0.25),
        dict(tongue=True, jaw=0.35, breathe=0.4, tail=(0, 0.8)),
        dict(tongue=True, jaw=0.25, breathe=0.6, tail=(0, 1.6), head=-1),
        dict(tongue=True, jaw=0.35, breathe=0.2, tail=(0, 2.4), ear=-8),
    ],
    "walk": [  # prowling trot: diagonal pairs swap
        dict(feet=((3, 0), (-2, 2), (-3, 1), (2, 0)), tail=(4, 0.0), head=-3),
        dict(feet=((1, 0), (0, 2), (-1, 2), (1, 0)), tail=(4, 1.0), by=-1, head=-2),
        dict(feet=((-2, 2), (2, 1), (2, 0), (-2, 1)), tail=(4, 2.0), head=-3),
        dict(feet=((-2, 2), (3, 0), (2, 0), (-3, 1)), tail=(4, 3.0), head=-3),
        dict(feet=((0, 2), (1, 0), (1, 0), (-1, 2)), tail=(4, 4.0), by=-1, head=-2),
        dict(feet=((2, 1), (-2, 2), (-2, 1), (2, 0)), tail=(4, 5.0), head=-3),
    ],
    "windup": [  # bark: plant the feet, head snaps up, mouth wide - held
        dict(head=10, neck=1, jaw=0.6, ear=-6, tail=(10, 0.5), bx=-1, rot=2, crouch=1, bark=1,
             feet=((1, 0), (1, 0), (-1, 0), (-1, 0))),
        dict(head=22, neck=2, jaw=1.0, ear=-12, tail=(14, 1.0), bx=-2, rot=4, crouch=1, bark=2,
             feet=((2, 0), (2, 0), (-1, 0), (-1, 0))),
        dict(head=24, neck=2, jaw=1.0, ear=-14, tail=(16, 1.4), bx=-2, rot=4, crouch=2, bark=3,
             feet=((2, 0), (2, 0), (-1, 0), (-1, 0))),
    ],
    "attack": [  # lunge: push off, fly with the jaws open, bite on frame 2, land
        dict(bx=1, crouch=2, rot=-4, head=-4, jaw=0.9, ear=-25, tail=(6, 2.0), sx=0.96,
             feet=((1, 0), (1, 0), (-2, 0), (-2, 0))),
        dict(bx=2, by=-3, rot=6, head=10, jaw=1.0, ear=-30, tail=(0, 3.0), sx=1.06, lift=2,
             reach=((5, -3), (4, -2), (-5, 2), (-4, 1))),
        dict(bx=4, by=-2, rot=-2, head=-8, jaw=0.05, ear=-30, tail=(-2, 4.0), sx=1.06, lift=1, hit=True,
             reach=((4, 0), (3, 0), (-5, 2), (-4, 2))),
        dict(bx=3, head=-4, jaw=0.2, ear=-15, tail=(2, 5.0), feet=((2, 0), (1, 0), (-1, 0), (0, 0))),
    ],
    "hurt": [
        dict(bx=-3, by=-1, head=16, ear=-30, eye="squeeze", jaw=0.5, tail=(-10, 1.0), rot=5,
             feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-2, head=8, ear=-20, eye="squeeze", jaw=0.2, tail=(-8, 2.0), rot=2),
    ],
    "death": [  # yelp, legs buckle, topple onto its side, lie still, fade
        dict(bx=-3, by=-1, head=18, ear=-35, eye="squeeze", jaw=0.6, tail=(-10, 1.0), rot=6,
             feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-3, crouch=4, head=-10, ear=-30, eye="squeeze", jaw=0.3, tail=(-14, 2.0), rot=-3,
             feet=((2, 0), (2, 0), (-1, 0), (-1, 0))),
        dict(bx=-3, side=True, head=0, ear=-40, eye="dead", jaw=0.3, tongue=True, tail=(-20, 2.0)),
        dict(bx=-3, side=True, head=0, ear=-40, eye="dead", jaw=0.3, tongue=True, tail=(-20, 2.0),
             fade=0.6),
        dict(bx=-3, side=True, head=0, ear=-40, eye="dead", jaw=0.3, tongue=True, tail=(-20, 2.0),
             fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _tufts(cv, pts, mat, size=1.6, name="tuft", **kw):
    """Little downward-pointing fur clumps hanging from points [(x, y, lean), ...]."""
    for (x, y, lean) in pts:
        cv.polygon([(x - size, y - 0.6), (x + size, y - 0.6), (x + lean, y + size * 1.25)], mat,
                   shade="two", name=name, **kw)


def _front_leg(cv, sh, foot, far, lifted=0, sep=False):
    fx, fy = foot
    wrist = (fx - 0.3, fy - 2.2)
    elbow = (sh[0] - 0.8 + 0.4 * lifted, sh[1] + 5.2 - 0.5 * lifted)
    shade = "dark" if far else "soft"
    cv.limb([sh, elbow, wrist], [2.5, 1.55, 1.25], FUR, shade=shade, name="leg", sep=sep)
    cv.limb([(wrist[0], wrist[1] - 1.8), wrist], [1.3, 1.2], MUD, shade="dark" if far else "two",
            name="leg")  # dried mud sock
    cv.ellipse(fx + 0.9, fy - 0.8, 1.9, 1.05, MUD, shade="dark" if far else "two", name="paw")


def _hind_leg(cv, hip, foot, far, sep=False):
    fx, fy = foot
    stifle = (hip[0] + 2.4, hip[1] + 5.0)
    hock = (fx - 1.8, fy - 4.6)
    shade = "dark" if far else "soft"
    cv.limb([hip, stifle, hock], [3.4, 2.1, 1.35], FUR, shade=shade, name="leg", sep=sep)
    cv.limb([hock, (fx, fy - 1.6)], [1.35, 1.2], MUD, shade="dark" if far else "two", name="leg")
    cv.ellipse(fx + 0.8, fy - 0.8, 1.9, 1.05, MUD, shade="dark" if far else "two", name="paw")


def _tail(cv, root, p):
    ang, ph = p.tail
    pts = [root]
    a = 200 - ang  # pointing back and down
    q = root
    for k, ln in enumerate((3.2, 3.0, 2.8, 2.4)):
        a += 14 + 8 * math.sin(ph * 1.3 + k * 0.9)
        q = px.polar(q, a, ln)
        pts.append(q)
    cv.limb(pts, [1.9, 1.8, 1.5, 1.1, 0.6], FUR, shade="soft", name="tail")
    # clumped hairs hanging off the tail
    for t, ln in ((0.35, 1.6), (0.65, 1.4)):
        i = int(t * (len(pts) - 1))
        c = px.lerp_pt(pts[i], pts[i + 1], 0.5)
        cv.polygon([(c[0] - 1.2, c[1]), (c[0] + 1.0, c[1]), (c[0] - 0.8, c[1] + ln + 0.8)], FUR,
                   shade="two", name="tail")
    cv.limb(pts[-2:], [1.1, 0.6], MUD, shade="two", decal=True, clip="tail")


def _head(cv, H, p):
    """Skull + long muzzle; jaw hinges below.  H = skull centre."""
    jaw_a = -10 - 38 * p.jaw
    j0 = (H[0] + 0.8, H[1] + 2.0)
    if p.jaw > 0.05:
        jt = px.polar(j0, jaw_a, 6.2)
        if p.tongue:
            tt = px.polar(j0, jaw_a + 8, 5.0)
            cv.limb([px.lerp_pt(j0, tt, 0.4), tt, (tt[0] + 0.6, tt[1] + 1.6)], [0.9, 0.9, 0.7], TONGUE,
                    shade="two", name="tongue")
        cv.limb([j0, jt], [1.7, 1.0], FUR, shade="nolight", name="jaw")
        cv.limb([px.lerp_pt(j0, jt, 0.3), jt], [1.0, 0.8], PALE, shade="two", decal=True, clip="jaw")
        # lower fangs
        tip = px.polar(j0, jaw_a, 5.2)
        cv.pixel(math.floor(tip[0]), math.floor(tip[1]) - 1, TOOTH, name="tooth")
    nose = (H[0] + 8.8, H[1] + 1.2)
    head = cv.union(cv.geom_ellipse(H[0], H[1], 4.3, 3.8, angle=10),
                    cv.geom_limb([(H[0] + 1.5, H[1] + 0.3), nose], [2.8, 1.6]),
                    weights=[1.0, 0.8])
    cv.draw_geom(head, FUR, name="head", sep="deep")
    # pale muzzle + cheek
    cv.limb([(H[0] + 1.2, H[1] + 2.2), (nose[0] - 0.5, nose[1] + 1.2)], [1.4, 0.9], PALE, shade="two",
            decal=True, clip="head")
    # nose button
    cv.ellipse(nose[0] + 0.3, nose[1] - 0.3, 1.2, 1.0, NOSE, shade="soft", name="nose")
    if p.jaw > 0.05:  # upper fang
        cv.pixel(math.floor(nose[0]) - 2, math.floor(nose[1]) + 2, TOOTH, name="tooth")
    else:
        cv.line((round(H[0] + 2), round(H[1] + 2)), (round(nose[0] - 1), round(nose[1] + 1)), FUR.deep,
                name="mouth")
    # torn ear: tall triangle with a notch, rotating back with p.ear
    base = (H[0] - 1.6, H[1] - 2.2)
    e = p.ear

    def r(pt):
        return px.rot_pt(pt, e, base)
    ear = [r((H[0] - 3.4, H[1] - 1.6)), r((H[0] - 3.0, H[1] - 6.6)), r((H[0] - 2.0, H[1] - 8.2)),
           r((H[0] - 1.3, H[1] - 6.4)), r((H[0] - 0.6, H[1] - 6.9)), r((H[0] + 0.6, H[1] - 2.8))]
    cv.polygon(ear, FUR, name="ear", sep="deep")
    cv.polygon([r((H[0] - 2.4, H[1] - 2.4)), r((H[0] - 2.1, H[1] - 6.0)), r((H[0] - 0.6, H[1] - 3.0))],
               MUD, shade="two", decal=True, clip="ear")
    # brow ridge + eye
    ex, ey = H[0] + 1.2, H[1] - 1.6
    hb.eye(cv, ex, ey, p.eye, iris=IRIS, brow=FUR.deep)


def _collar(cv, N, ang, p):
    """Leather band across the neck at N (angle = neck direction) + brass ring."""
    a = px.polar(N, ang + 90, 3.6)
    b = px.polar(N, ang - 90, 3.8)
    cv.limb([a, b], 1.05, LEATHER, shade="two", decal=True, clip=["neck", "head", "body"])
    for t in (0.3, 0.62):  # brass studs
        s = px.lerp_pt(a, b, t)
        cv.pixel(math.floor(s[0]), math.floor(s[1]), BRASS.light, name="stud", decal=True,
                 clip=["neck", "body", "head"])
    ring = px.lerp_pt(a, b, 1.02)
    rx, ry = math.floor(ring[0]) - 1, math.floor(ring[1])
    cv.stamp([".bb.", "b..b", "b..d", ".dd."], rx, ry, {"b": BRASS.base, "d": BRASS.shadow}, name="ring")
    cv.pixel(rx + 1, ry, BRASS.light, name="ring")


# (hip offset from C, foot x offset, feet index, kind, far) - far legs first
LEGS = (
    ((7.0, 1.5), 9.5, 1, "front", True),
    ((-9.0, -0.5), -8.0, 3, "hind", True),
    ((-7.5, 0.0), -6.5, 2, "hind", False),
    ((5.5, 2.0), 7.5, 0, "front", False),
)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    cv.opacity = p.fade
    if p.side:
        _draw_side(cv, p, ground)
        return
    C = (cv.gx - 3 + p.bx, ground - 15.0 + p.by + p.crouch - p.lift)

    def foot(dx, i):
        f, rch = p.feet[i], p.reach[i]
        if p.lift:  # airborne: feet tuck / reach relative to the body
            return (C[0] + dx + rch[0], ground - 3 - p.lift * 2 + rch[1] + p.by + 2)
        return (C[0] + dx + f[0], ground - f[1])

    body_pt = lambda q: px.rot_pt(q, p.rot, (C[0] - 6, C[1]))  # noqa: E731

    with cv.xform(px.scale(p.sx, 1.0, (C[0], ground))):
        # far legs, attached through the body pitch
        for hip, fdx, i, kind, far in LEGS[:2]:
            h = body_pt((C[0] + hip[0], C[1] + hip[1]))
            (_front_leg if kind == "front" else _hind_leg)(cv, h, foot(fdx, i), far)
        with cv.xform(px.rotate(p.rot, (C[0] - 6, C[1]))):
            _tail(cv, (C[0] - 12.0, C[1] - 2.5), p)
        hip, fdx, i, kind, far = LEGS[2]
        _hind_leg(cv, body_pt((C[0] + hip[0], C[1] + hip[1])), foot(fdx, i), far)
        with cv.xform(px.rotate(p.rot, (C[0] - 6, C[1]))):
            br = p.breathe
            body = cv.union(cv.geom_ellipse(C[0] - 7.0, C[1] - 0.6, 6.0, 5.4),
                            cv.geom_limb([(C[0] - 6.0, C[1] - 1.2), (C[0] + 4.0, C[1] - 0.6)], [4.6, 5.0]),
                            cv.geom_ellipse(C[0] + 5.2, C[1] + 0.2 - br * 0.5, 6.4, 6.2 + br, angle=6),
                            weights=[1.0, 0.75, 1.0])
            cv.fill(body[0], FUR, name="body", sep="deep")  # dome normals: one continuous back highlight
            # clumped fur hanging off the belly line, chest and thigh
            _tufts(cv, [(C[0] + 3.2, C[1] + 5.4, -0.6), (C[0] + 6.6, C[1] + 5.8, -0.4),
                        (C[0] - 1.6, C[1] + 3.4, -0.6), (C[0] - 10.6, C[1] + 3.8, -0.8)], FUR,
                   size=1.35, name="body")
            # raised hackles: clumped, mud-stiffened fur spikes over the shoulders
            for k, (hx, hy) in enumerate(((-1.5, -5.2), (1.5, -5.6), (4.5, -6.0), (7.5, -6.2))):
                ln = 2.2 + 0.4 * (k % 2)
                cv.polygon([(C[0] + hx - 1.4, C[1] + hy + 1.6), (C[0] + hx + 1.6, C[1] + hy + 1.2),
                            (C[0] + hx - 1.2, C[1] + hy - ln)], FUR, shade="two", name="body")
            # pale throat / chest ruff, dried mud caked along the belly
            cv.ellipse(C[0] + 9.5, C[1] + 1.5, 2.4, 4.0, PALE, shade="two", decal=True, clip="body")
            cv.limb([(C[0] - 9.0, C[1] + 4.2), (C[0] - 2.0, C[1] + 3.6), (C[0] + 7.0, C[1] + 5.6)], [1.6, 1.4, 1.8],
                    MUD, shade="two", decal=True, clip="body")
            N0 = (C[0] + 8.5, C[1] - 2.5)
        # near foreleg over the chest
        hip, fdx, i, kind, far = LEGS[3]
        _front_leg(cv, body_pt((C[0] + hip[0], C[1] + hip[1])), foot(fdx, i), far)
        with cv.xform(px.rotate(p.rot, (C[0] - 6, C[1]))):
            # neck + head group rotate about the base of the neck
            with cv.xform(px.rotate(p.head * 0.5, N0)):
                Nt = (N0[0] + 4.2, N0[1] - 4.6 - p.neck)
                cv.limb([N0, Nt], [4.2, 3.4], FUR, name="neck")
                cv.limb([(N0[0] + 1.5, N0[1] + 2.5), (Nt[0] + 1.0, Nt[1] + 2.0)], 1.2, PALE, shade="two",
                        decal=True, clip="neck")
                with cv.xform(px.rotate(p.head * 0.5, Nt)):
                    H = (Nt[0] + 2.0, Nt[1] - 1.0)
                    _head(cv, H, p)
                    hit_at = cv.tp((H[0] + 8.5, H[1] + 3.0))
                    bark_at = cv.tp((H[0] + 9.5, H[1] - 1.0))
                _collar(cv, px.lerp_pt(N0, Nt, 0.62), math.degrees(math.atan2(-(Nt[1] - N0[1]), Nt[0] - N0[0])), p)
    if p.bark:
        fx = cv.layer(above=True, outline=False)
        for k in range(p.bark):  # short bark strokes fanning out of the mouth
            d = 2.0 + k * 1.6
            for a, ln in ((35, 2), (5, 3), (-25, 2)):
                s = px.polar(bark_at, a, d)
                e = px.polar(bark_at, a, d + ln - 0.5)
                cv_line = (math.floor(s[0]), math.floor(s[1])), (math.floor(e[0]), math.floor(e[1]))
                fx.line(cv_line[0], cv_line[1], px.PALE_GOLD if k == p.bark - 1 else px.PAPER, name="bark")
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, hit_at[0], hit_at[1], size=3)
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, C[0] - 16, C[1] - 1, length=6, count=2, spacing=4, color=px.MIST_BLUE)


def _draw_side(cv, p, ground):
    """Collapsed on its side: body low on the ground, stiff legs splayed out, head down."""
    C = (cv.gx - 3 + p.bx, ground - 6.5)
    # far legs splay out behind the near ones
    for (hx, hy), tip in (((7.0, 2.0), (15.5, ground - 1.0)), ((-8.5, 1.5), (-16.0, ground - 1.2))):
        a, b = (C[0] + hx, C[1] + hy), (C[0] + tip[0], tip[1])
        cv.limb([a, b], [2.0, 1.1], FUR, shade="dark", name="leg")
        cv.limb([px.lerp_pt(a, b, 0.6), b], [1.3, 1.1], MUD, shade="dark", decal=True, clip="leg")
    # tail flat along the ground
    T = (C[0] - 12.0, C[1] + 1.0)
    cv.limb([T, (T[0] - 4.0, T[1] + 2.5), (T[0] - 8.0, ground - 0.5), (T[0] - 10.5, ground - 0.5)],
            [1.9, 1.6, 1.2, 0.6], FUR, shade="soft", name="tail")
    body = cv.union(cv.geom_ellipse(C[0] - 7.0, C[1] + 0.2, 6.0, 4.8),
                    cv.geom_limb([(C[0] - 6.0, C[1] + 0.2), (C[0] + 4.0, C[1] + 0.2)], [4.2, 4.6]),
                    cv.geom_ellipse(C[0] + 5.0, C[1] + 0.3, 6.2, 5.2),
                    weights=[1.0, 0.75, 1.0])
    cv.fill(body[0], FUR, name="body", sep="deep")
    cv.limb([(C[0] - 9.0, C[1] + 3.6), (C[0] + 8.0, C[1] + 3.8)], 1.5, MUD, shade="two", decal=True, clip="body")
    cv.ellipse(C[0] + 9.0, C[1] + 1.5, 2.2, 3.4, PALE, shade="two", decal=True, clip="body")
    # near legs: stiff, splayed forward and back
    for (hx, hy), tip in (((-7.0, 2.5), (-13.0, ground - 0.8)), ((5.5, 3.0), (12.5, ground - 0.8))):
        a, b = (C[0] + hx, C[1] + hy), (C[0] + tip[0], tip[1])
        cv.limb([a, px.lerp_pt(a, b, 0.55), b], [2.3, 1.45, 1.2], FUR, shade="soft", name="leg", sep="deep")
        cv.limb([px.lerp_pt(a, b, 0.6), b], [1.3, 1.2], MUD, shade="two", decal=True, clip="leg")
    # head resting on the ground, tongue lolling
    N0 = (C[0] + 8.5, C[1] - 0.5)
    Nt = (N0[0] + 4.5, N0[1] + 0.5)
    cv.limb([N0, Nt], [3.6, 3.1], FUR, name="neck")
    H = (Nt[0] + 2.0, Nt[1] + 0.8)
    with cv.xform(px.rotate(-6, H)):
        _head(cv, H, p)
    _collar(cv, px.lerp_pt(N0, Nt, 0.6), 0, p)
