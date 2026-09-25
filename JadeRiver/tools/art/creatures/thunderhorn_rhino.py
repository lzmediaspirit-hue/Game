"""Thunderhorn rhino - a heavy slate-blue rhino whose great horn stores lightning (Thunder).

Azure Expanse, Thunderhorn Plains (64-69).  Built on the thornback boar rig (cell 192): the
thorns become rounded armour plates down the spine, the vines become deep skin folds, and
the head carries a long upcurved nasal horn with a second horn behind it.  Windup: the head
drops and arcs crawl up the horn; attack: a thundering charge that discharges on the hit.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "thunderhorn_rhino",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 2,
}

# ---- palette: dark umber hide, wood-green vines, pale woody thorns --------------------------
HIDE = px.material("tr_hide", "#aab4c6", "#77829a", "#4f586f", "#31374a", outline="#0e1018",
                   thresholds=(0.9, 0.55, 0.18))
MANE = px.material("tr_fold", "#5b6680", "#434c63", "#30374a", "#20253a", outline="#0b0d14")
PLATE = px.material("tr_plate", "#d6dde8", "#a2adc2", "#6f7b95", "#48516a", outline="#0e1018")
HORN = px.material("tr_horn", "#fff6d8", "#e0d0a0", "#a8946a", "#6c5c44", outline="#1a140c")
SNOUT = px.material("tr_lip", "#8c96ac", "#646e86", "#454d62", "#2c3244", outline="#0e1018")
HOOF = px.material("tr_hoof", "#4a4f5e", "#33374a", "#252838", "#181a26", outline="#0a0b10")
STEAM = px.material("tr_steam", "#ffffff", "#dfe8e8", "#b2c2c6", "#8494a0", outline="#3a4650")
TUSK = HORN
EYE_RED = px.rgb("#ffd45a")
EYE_DARK = px.rgb("#a8701e")
BOLT_CORE = px.rgb("#f4fbff")
BOLT_EDGE = px.rgb("#6aa8ff")

# ---- poses --------------------------------------------------------------------------------
# bx, by body offset   sx squash/stretch   head  head tilt (deg)   crouch  lower the body
# feet  (dx, lift) near-front, far-front, near-hind, far-hind    ear  ear angle
# tail  swish   eye  angry|squeeze|dead   thorn  spike length boost (px, enraged)
# paw   near foreleg drawn in front of the chest   dust / steam  FX life 0..1 (None = off)
# pitch body pitch (deg, + = front up) about the hind feet   slump  lying   fade  opacity
DEFAULTS = dict(bx=0, by=0, sx=1.0, head=0, crouch=0, feet=((0, 0), (0, 0), (0, 0), (0, 0)), ear=0,
                tail=0.0, eye="angry", thorn=0.0, paw=False, dust=None, steam=None, pitch=0, slump=False,
                fade=1.0, hit=False, breathe=0.0, streak=False)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(),
        dict(breathe=0.5, tail=0.6, head=1),
        dict(breathe=0.8, tail=1.2, head=1, steam=0.35),
        dict(breathe=0.3, tail=0.6, ear=-10, steam=0.8),
    ],
    "walk": [  # heavy trot: diagonal pairs alternate, the hump rolls
        dict(feet=((3, 0), (-2, 3), (-3, 3), (2, 0)), tail=0.0),
        dict(feet=((2, 0), (0, 3), (-1, 1), (1, 0)), by=-1, tail=0.5, head=1),
        dict(feet=((-1, 1), (2, 0), (1, 0), (-1, 1)), tail=1.0),
        dict(feet=((-2, 3), (3, 0), (2, 0), (-3, 3)), tail=1.0),
        dict(feet=((0, 3), (2, 0), (1, 0), (-1, 1)), by=-1, tail=0.5, head=1),
        dict(feet=((1, 1), (-1, 1), (-1, 1), (1, 0)), tail=0.0),
    ],
    "windup": [  # head drops, thorns bristle, hoof paws the dirt, snorting steam - held
        dict(head=-8, bx=-1, ear=-15, feet=((3, 4), (0, 0), (0, 0), (0, 0)), crouch=1, paw=True, thorn=1.0,
             steam=0.2),
        dict(head=-13, bx=-2, ear=-25, feet=((-4, 0), (0, 0), (0, 0), (0, 0)), crouch=2, paw=True, thorn=2.0,
             dust=0.2, steam=0.5),
        dict(head=-15, bx=-3, ear=-30, feet=((2, 4), (0, 0), (0, 0), (0, 0)), crouch=2, paw=True, thorn=2.5,
             dust=0.55, steam=0.75, sx=0.97),
    ],
    "attack": [  # thorn charge: explode forward, hook the tusks up on frame 2, skid
        dict(bx=3, head=-16, ear=-30, sx=1.05, feet=((4, 3), (3, 1), (-4, 0), (-3, 0)), thorn=2.5, dust=0.1),
        dict(bx=8, by=-1, head=-12, ear=-30, sx=1.08, feet=((5, 1), (4, 3), (-5, 1), (-4, 0)), thorn=2.5,
             dust=0.45, streak=True),
        dict(bx=11, head=12, ear=-20, sx=1.04, feet=((2, 0), (3, 0), (-2, 0), (-1, 0)), thorn=2.0, hit=True,
             dust=0.75, streak=True),
        dict(bx=7, head=3, ear=-10, feet=((1, 0), (1, 0), (-1, 0), (0, 0)), thorn=1.0),
    ],
    "hurt": [
        dict(bx=-3, by=-1, head=14, ear=-30, eye="squeeze", feet=((1, 3), (0, 1), (0, 0), (0, 0)), thorn=1.5),
        dict(bx=-2, head=7, ear=-20, eye="squeeze", thorn=0.5),
    ],
    "death": [  # rears in pain, front knees buckle, collapses onto its side, fades
        dict(bx=-3, by=-1, head=16, ear=-35, eye="squeeze", feet=((1, 3), (0, 1), (0, 0), (0, 0))),
        dict(bx=-3, head=-7, ear=-30, eye="squeeze", crouch=3),
        dict(bx=-3, head=-14, ear=-40, eye="dead", slump=True, thorn=-1.5),
        dict(bx=-3, head=-14, ear=-40, eye="dead", slump=True, thorn=-1.5, fade=0.6),
        dict(bx=-3, head=-14, ear=-40, eye="dead", slump=True, thorn=-1.5, fade=0.3),
    ],
})

# (hip offset from C, foot x offset from C, feet index, far) - far legs drawn first
LEGS = (
    ((11.0, 7.0), 11.5, 1, True),
    ((-12.0, 6.0), -12.0, 3, True),
    ((-14.5, 7.0), -15.0, 2, False),
    ((8.5, 8.0), 8.0, 0, False),
)


def _leg(cv, hip, foot, far, sep=False):
    """Thick leg with a dewclaw-ish fetlock and a split dark hoof."""
    fx, fy = foot
    knee = (fx + 0.3 * (hip[0] - fx), fy - 6.0)
    shade = "dark" if far else "soft"
    cv.limb([hip, knee, (fx, fy - 3.2)], [4.2, 2.6, 2.2], HIDE, shade=shade, name="leg", sep=sep)
    cv.limb([(fx - 0.2, fy - 2.5), (fx + 0.4, fy - 1.2)], [2.2, 2.1], HOOF, shade="dark" if far else "two",
            name="hoof", sep=False if far else "deep")
    if not far:  # split hoof line
        cv.pixel(math.floor(fx + 0.5), math.floor(fy - 1.0), HOOF.deep, name="hoof")


def _spine(C, br):
    """Spine points along the top line of the body (rump -> hump -> nape)."""
    return [(C[0] - 18.0, C[1] - 4.0), (C[0] - 12.5, C[1] - 9.0 - br * 0.4), (C[0] - 5.0, C[1] - 12.0 - br * 0.5),
            (C[0] + 3.0, C[1] - 13.6 - br * 0.5), (C[0] + 10.0, C[1] - 12.0 - br * 0.4), (C[0] + 15.0, C[1] - 7.5)]


def _thorns(cv, spine, boost, slump):
    """Rounded armour plates along the spine (lifted slightly when it is angry)."""
    plates = ((0.2, 2.4), (0.36, 2.9), (0.52, 3.1), (0.68, 2.6))
    n = len(spine) - 1
    for t, r in plates:
        f = t * n
        i = min(n - 1, int(f))
        q = px.lerp_pt(spine[i], spine[i + 1], f - i)
        lift = 0.0 if slump else boost * 0.35
        cv.ellipse(q[0], q[1] + 1.8 - lift, r, r * 0.62, PLATE, shade="soft", name="plate", sep="deep")


def _vines(cv, C, spine, phase):
    """Deep skin folds where the armoured hide overlaps at the shoulder and haunch."""
    for (x0, y0), (xm, ym), (x1, y1) in (((9.0, -11.5), (12.0, -3.0), (10.0, 6.0)),
                                         ((-11.0, -8.5), (-7.5, -1.0), (-10.0, 7.5)),
                                         ((-1.0, -12.0), (1.0, -4.0), (-0.5, 8.5))):
        cv.limb([(C[0] + x0, C[1] + y0), (C[0] + xm, C[1] + ym), (C[0] + x1, C[1] + y1)], 0.8, MANE, shade="two",
                name="body", decal=True, clip="body")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground
    C = (cv.gx - 5 + p.bx, ground - 17.5 + p.by + p.crouch)
    cv.opacity = p.fade
    cv.snap_ground = p.slump
    feet_base = ground - (1.0 if p.slump else 0.0)

    def foot(dx, i):
        f = p.feet[i]
        return (C[0] + dx + f[0], feet_base - f[1])

    xf = [px.scale(p.sx, 1.0, (C[0], ground))]
    if p.pitch:
        xf.append(px.rotate(p.pitch, (C[0] - 14, ground)))
    if p.slump:  # collapsed onto its side: flatter, belly on the ground
        xf.append(px.scale(1.0, 0.86, (C[0], ground)))
    with cv.xform(*xf):
        if not p.slump:
            for hip, fdx, i, far in LEGS[:2]:
                _leg(cv, (C[0] + hip[0], C[1] + hip[1]), foot(fdx, i), far)
        # tufted tail
        T = (C[0] - 20.0, C[1] - 2.0)
        sw = p.tail
        tail = [T, (T[0] - 2.2, T[1] + 2.5 - sw * 0.5), (T[0] - 3.0, T[1] + 6.0), (T[0] - 2.5 + sw * 0.6, T[1] + 8.5)]
        if p.slump:
            tail = [T, (T[0] - 3.0, T[1] + 2.0), (T[0] - 5.5, T[1] + 4.0), (T[0] - 7.5, T[1] + 5.0)]
        cv.limb(tail, [1.0, 0.8, 0.7, 0.6], HIDE, shade="two", name="tail")
        cv.limb(tail[-2:], [1.1, 1.4], MANE, shade="two", name="tail")
        if not p.slump:
            for hip, fdx, i, far in (LEGS[2:3] if p.paw else LEGS[2:]):
                _leg(cv, (C[0] + hip[0], C[1] + hip[1]), foot(fdx, i), far)
        # body + head as one form
        br = p.breathe
        neck = (C[0] + 12.0, C[1] + 0.0)
        body_g = cv.union(cv.geom_ellipse(C[0] - 10.5, C[1] + 1.0 - br * 0.3, 10.0, 9.2 + br * 0.5),
                          cv.geom_ellipse(C[0] + 4.0, C[1] - 1.5 - br * 0.5, 13.0, 12.0 + br))
        with cv.xform(px.rotate(p.head, neck)):
            H = (C[0] + 17.0, C[1] + 3.0)
            head_g = cv.geom_ellipse(H[0], H[1], 7.8, 7.2, angle=-18)
            snout_end = (H[0] + 12.5, H[1] + 4.8)
            muzzle_g = cv.geom_limb([(H[0] + 3.0, H[1] + 1.0), snout_end], [5.2, 3.5])
        cv.draw_geom(cv.union(body_g, head_g, muzzle_g, weights=[1.0, 0.72, 0.55]), HIDE, name="body",
                     sep="deep")
        spine = _spine(C, br)
        # dark bristly mane along the spine and down the neck (thorns rise out of it)
        cv.limb([(q[0], q[1] + 1.6) for q in spine], 2.4, MANE, shade="two", decal=True, clip="body", name="body")
        # belly shadow fold and shoulder crease
        cv.limb([(C[0] - 15.0, C[1] + 7.5), (C[0] + 2.0, C[1] + 9.0), (C[0] + 12.0, C[1] + 7.0)], 1.2,
                HIDE.step(1), decal=True, clip="body", name="body")
        cv.limb([(C[0] + 9.0, C[1] - 6.0), (C[0] + 10.5, C[1] + 1.0), (C[0] + 9.5, C[1] + 6.0)], 0.6,
                HIDE.step(1), decal=True, clip="body", name="body")
        # coarse bristle strokes on the flank
        for (x, y) in ((-6.0, -4.0), (-2.0, 0.0), (2.5, -5.0), (5.0, 1.5), (-9.5, 1.5), (-1.0, -8.0)):
            cv.line((math.floor(C[0] + x), math.floor(C[1] + y)), (math.floor(C[0] + x - 1), math.floor(C[1] + y + 2)),
                    HIDE.step(1), band=None, decal=True, clip="body", name="body")
        _thorns(cv, spine, p.thorn, p.slump)
        _vines(cv, C, spine, 0.0)
        with cv.xform(px.rotate(p.head, neck)):
            # square lip and nostril
            cv.ellipse(snout_end[0] - 0.4, snout_end[1] + 0.6, 2.6, 2.6, SNOUT, name="snout", sep="deep")
            cv.pixel(math.floor(snout_end[0]), math.floor(snout_end[1]) - 1, SNOUT.deep, name="nostril")
            cv.line((math.floor(H[0] + 4), math.floor(H[1] + 5)), (math.floor(H[0] + 9), math.floor(H[1] + 6)),
                    HIDE.deep, name="mouth")
            # the great nasal horn, sweeping up, and a smaller one behind it
            horn = [(snout_end[0] - 3.0, snout_end[1] - 2.8), (snout_end[0] - 1.0, snout_end[1] - 7.5),
                    (snout_end[0] - 2.2, snout_end[1] - 12.0), (snout_end[0] - 5.0, snout_end[1] - 14.5)]
            cv.limb(horn, [2.6, 2.0, 1.2, 0.5], HORN, shade="soft", name="tusk", sep="deep")
            horn2 = [(H[0] + 5.0, H[1] - 3.2), (H[0] + 5.8, H[1] - 6.5), (H[0] + 4.6, H[1] - 8.4)]
            cv.limb(horn2, [1.6, 1.0, 0.4], HORN, shade="soft", name="tusk", sep="deep")
            tusk = horn
            # laid-back ear
            ep = (H[0] - 3.0, H[1] - 5.0)
            tip = px.rot_pt((H[0] - 7.0, H[1] - 10.5), p.ear, ep)
            ear = [px.rot_pt((H[0] - 6.5, H[1] - 4.0), p.ear, ep), tip, px.rot_pt((H[0] - 0.8, H[1] - 6.0), p.ear, ep)]
            cv.polygon(ear, HIDE, shade="two", name="ear", sep="deep")
            cv.polygon([px.lerp_pt(ear[0], ear[2], 0.5), px.lerp_pt(tip, ear[0], 0.3), px.lerp_pt(ear[2], tip, 0.35)],
                       SNOUT.step(2), shade="two", decal=True, clip="ear")
            # small fierce eye under a heavy brow
            ex, ey = math.floor(H[0] + 2.0), math.floor(H[1] - 2.5)
            if p.eye == "squeeze":
                cv.stamp(["kk.", "..k", "kk."], ex - 1, ey - 1, {"k": px.INK}, name="eye")
            elif p.eye == "dead":
                cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")
            else:
                cv.stamp(["gr", "rd"], ex, ey, {"g": px.PALE_GOLD, "r": EYE_RED, "d": EYE_DARK}, name="eye")
            if p.eye != "dead":
                cv.limb([(ex - 2.0, ey - 1.8), (ex + 1.0, ey - 0.8), (ex + 3.5, ey + 0.4)], [1.1, 1.0, 0.7], MANE,
                        shade="two", name="brow")
            hit_at = cv.tp((tusk[-1][0] + 1.5, tusk[-1][1] - 1.0))
            nose_at = cv.tp((snout_end[0] + 1.5, snout_end[1] + 1.0))
        if p.paw:  # the pawing foreleg swings in front of the chest
            hip, fdx, i, far = LEGS[3]
            _leg(cv, (C[0] + hip[0], C[1] + hip[1] - 1.0), foot(fdx, i), far, sep=True)
        if p.slump:  # folded legs: hooves peeking out under the belly
            for dx in (-14.0, 8.0):
                cv.limb([(C[0] + dx, C[1] + 10.0), (C[0] + dx + 3.5, C[1] + 10.5)], 2.0, HOOF, shade="two",
                        name="hoof")
    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        px.dust(fx, C[0] + (4.0 if action == "windup" else -18.0), cv.gy - 1, p.dust,
                size=0.9 if action == "windup" else 1.2, direction=-1)
    if p.steam is not None:  # snort: little puffs of steam blown down and forward from the nostrils
        fx2 = cv.layer(above=True, outline=True)
        t = p.steam
        for k, (d, r) in enumerate(((2.5, 1.0), (7.0, 1.4), (12.0, 1.7))):
            if t < k * 0.3:
                continue
            cx = nose_at[0] + d + t * 2.0
            cy = nose_at[1] + 1.5 - k * 1.2 - t * 1.0
            fx2.circle(cx, cy, r * (0.7 + 0.3 * t), STEAM, shade="soft", name="steam")
    if action == "windup" or (action == "idle" and frame == 2):
        arcs = cv.layer(above=True, outline=False)
        tip = hit_at
        base = cv.tp((C[0] + 26.0, C[1] + 2.0))
        for k in range(2 if action == "idle" else 1 + frame):
            hc.bolt(arcs, (base[0] - k, base[1] - k * 2), (tip[0] + k, tip[1] - 1), seed=frame * 3 + k, jag=1.4, segs=5,
                    core=BOLT_CORE, edge=BOLT_EDGE, fork=k == 1)
    if p.streak:
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, C[0] - 22, C[1] - 4, length=9, count=3, spacing=5, color=px.MIST_BLUE)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        hc.bolt(top, (hit_at[0] - 2, hit_at[1] - 6), (hit_at[0] + 7, hit_at[1] + 2), seed=11, jag=2.0, segs=6,
                core=BOLT_CORE, edge=BOLT_EDGE)
        px.impact(top, hit_at[0], hit_at[1], size=4, color=px.rgb("#a8d4ff"))
