"""Reedtail rat - lean grey-brown river rat with a reed-green banded tail.

View: side, facing right.  ~14 art px tall, ~31 long including the tail.
Parts, back to front: banded reed tail, legs (tucked under the body: far pair first),
body (haunch + chest shaded as one form via ``cv.union``, pale belly decal), head group
rotating about the neck (jaw, skull + snout, nose, teeth, ear, eye).
The lunge frames leave the ground on purpose, so they are listed in ``airborne``.
"""
import math

import pixel as px

SPEC = {
    "id": "reedtail_rat",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 1,
    "airborne": [["attack", 0], ["attack", 1]],
}

# ---- palette ------------------------------------------------------------------------------
FUR = px.material("rat_fur", "#b8a488", "#88745f", "#5f5052", "#3d3340", outline="#15111a",
                  thresholds=(0.93, 0.58, 0.22))
BELLY = px.material("rat_belly", "#e2d3b6", "#bfae90", "#938271", "#655a5e", outline="#15111a")
EAR = px.material("rat_ear", "#c7b397", "#977f68", "#6b5a58", "#453a45", outline="#15111a")
PINK = px.material("rat_pink", "#f7c6b8", "#e39a92", "#b56d72", "#7b4652", outline="#1f1016")
TAIL = px.material("reed_tail", "#bdd877", "#82ad4f", "#557f3b", "#33552f", outline="#0f1a10")
RING = px.material("reed_ring", "#6f9444", "#4b7036", "#355630", "#233b26", outline="#0f1a10")
FOOT = px.material("rat_foot", "#efb9ab", "#cf918a", "#9f676a", "#6c4350", outline="#1f1016")
IRIS = px.rgb("#9a3a28")
TOOTH = px.rgb("#f6efd6")

# ---- poses --------------------------------------------------------------------------------
# bx, by body offset      sx body stretch (lunge)   crouch  lowers body, bends legs
# head   head tilt (deg, + = nose up)   jaw 0..1   ear  ear angle (deg, - = flattened back)
# tail   (lift, wave phase)             feet  (dx, lift) for near-front, far-front,
# near-hind, far-hind                   eye   open|angry|squeeze|dead
# slump  lying flat (legs folded away)  sy  vertical squash about the ground
# fade   frame opacity                  hit impact fx on the bite frame
# nose   nose twitch (px)   breathe  body swell   lift  whole body off the ground (lunge)
DEFAULTS = dict(bx=0, by=0, sx=1.0, crouch=0, head=0, jaw=0.0, ear=0, tail=(0, 0.0),
                feet=((0, 0), (0, 0), (0, 0), (0, 0)), eye="open", fade=1.0, hit=False, nose=0,
                breathe=0.0, lift=0, slump=False, sy=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(tail=(0, 0.0)),
        dict(tail=(0, 0.8), nose=1, breathe=0.3),
        dict(tail=(0, 1.6), breathe=0.4, by=0),
        dict(tail=(0, 2.4), nose=1, ear=-8, breathe=0.1),
    ],
    "walk": [  # quick scurry: diagonal pairs swap, body bobs and stretches
        dict(feet=((2, 0), (-2, 1), (-2, 0), (2, 1)), tail=(1, 0.0), by=0, sx=1.04),
        dict(feet=((1, 1), (-1, 0), (-1, 1), (1, 0)), tail=(1, 1.0), by=-1),
        dict(feet=((-1, 1), (1, 0), (1, 1), (-1, 0)), tail=(1, 2.0), by=-1, sx=0.97),
        dict(feet=((-2, 1), (2, 0), (2, 1), (-2, 0)), tail=(1, 3.0), by=0, sx=1.04),
        dict(feet=((-1, 0), (1, 1), (1, 0), (-1, 1)), tail=(1, 4.0), by=-1),
        dict(feet=((1, 0), (-1, 1), (-1, 0), (1, 1)), tail=(1, 5.0), by=-1, sx=0.97),
    ],
    "windup": [  # crouch low, head down, bare teeth, ears back, tail up - held
        dict(crouch=1, head=-6, jaw=0.3, ear=-15, tail=(2, 0.5), eye="angry", bx=-1),
        dict(crouch=2, head=-10, jaw=0.7, ear=-30, tail=(3, 0.8), eye="angry", bx=-2, sx=0.94,
             feet=((1, 0), (1, 0), (-1, 0), (-1, 0))),
        dict(crouch=2, head=-10, jaw=1.0, ear=-35, tail=(4, 1.0), eye="angry", bx=-2, sx=0.92,
             feet=((1, 0), (1, 0), (-1, 0), (-1, 0))),
    ],
    "attack": [  # lunge bite: hit on frame 1 at full reach
        dict(bx=4, by=-2, sx=1.12, head=4, jaw=1.0, ear=-35, tail=(2, 2.0), eye="angry",
             feet=((4, 2), (3, 2), (-4, 0), (-3, 0)), lift=1),
        dict(bx=7, by=-1, sx=1.14, head=-4, jaw=0.0, ear=-30, tail=(1, 3.0), eye="angry",
             feet=((3, 0), (2, 1), (-3, 1), (-2, 1)), hit=True, lift=1),
        dict(bx=5, sx=1.05, head=-2, jaw=0.2, ear=-20, tail=(1, 4.0),
             feet=((1, 0), (0, 0), (-1, 0), (0, 0))),
        dict(bx=2, head=0, ear=-8, tail=(0, 5.0)),
    ],
    "hurt": [
        dict(bx=-3, by=-2, head=12, ear=-35, eye="squeeze", jaw=0.4, tail=(3, 1.0),
             feet=((1, 2), (0, 1), (1, 0), (0, 0))),
        dict(bx=-2, by=0, head=6, ear=-20, eye="squeeze", tail=(2, 2.0)),
    ],
    "death": [  # recoil, legs buckle, slump flat on the ground, fade
        dict(bx=-3, by=-2, head=14, ear=-35, eye="squeeze", jaw=0.5, tail=(3, 1.0),
             feet=((1, 2), (0, 1), (1, 0), (0, 0))),
        dict(bx=-3, crouch=2, head=-12, ear=-30, eye="squeeze", jaw=0.2, tail=(0, 2.0),
             feet=((2, 0), (2, 0), (-2, 0), (-2, 0))),
        dict(bx=-3, crouch=3, slump=True, sy=0.9, head=-14, ear=-40, eye="dead", tail=(0, 3.0)),
        dict(bx=-3, crouch=3, slump=True, sy=0.85, head=-14, ear=-40, eye="dead", tail=(0, 3.0), fade=0.6),
        dict(bx=-3, crouch=3, slump=True, sy=0.8, head=-14, ear=-40, eye="dead", tail=(0, 3.0), fade=0.3),
    ],
})


# ---- parts --------------------------------------------------------------------------------
def _tail(cv, root, p, ground):
    """Long reed tail: droops, then lifts at the tip; waves with p.tail[1].
    Dark rings every ~2.5 px make the reed segments."""
    lift, ph = p.tail
    pts = [root]
    for k in range(1, 7):
        x = root[0] - 2.5 * k
        droop = (0, 1.4, 2.3, 2.6, 2.2, 1.2, -0.2)[k]
        y = root[1] + droop * (1 - 0.35 * lift) - lift * 0.55 * k + 0.8 * math.sin(ph * 1.2 + k * 0.9) * (k / 6)
        pts.append((x, min(y, ground - 1.0)))
    radii = [1.6, 1.4, 1.2, 1.05, 0.9, 0.75, 0.55]
    cv.limb(pts, radii, TAIL, name="tail")
    for k in (1, 2, 3, 4, 5):
        a, b = pts[k], pts[k + 1]
        c = px.lerp_pt(a, b, 0.15)
        d = (b[0] - a[0], b[1] - a[1])
        ln = math.hypot(*d) or 1.0
        n = (-d[1] / ln * 2.5, d[0] / ln * 2.5)
        cv.limb([(c[0] - n[0], c[1] - n[1]), (c[0] + n[0], c[1] + n[1])], 0.5, RING,
                decal=True, clip="tail")


def _leg(cv, hip, foot, kind, far, p, crouch):
    """kind 'hind': hock + long flat foot; 'front': thin foreleg + small paw."""
    shade = "dark" if far else "soft"
    fx, fy = foot
    if kind == "hind":
        hock = (hip[0] - 2.0, hip[1] + 2.4 - crouch * 0.3)
        cv.limb([hip, hock, (fx - 0.5, fy - 0.3)], [1.6, 1.0, 0.8], FUR, shade=shade, name="leg")
        cv.limb([(fx - 0.5, fy), (fx + 1.8, fy)], [0.75, 0.6], FOOT, shade="flatdark" if far else "two", name="foot")
    else:
        elbow = (hip[0] + 0.2, hip[1] + 2.2 - crouch * 0.4)
        cv.limb([hip, elbow, (fx, fy - 0.3)], [1.2, 0.9, 0.7], FUR, shade=shade, name="leg")
        cv.limb([(fx, fy), (fx + 1.3, fy)], [0.7, 0.55], FOOT, shade="flatdark" if far else "two", name="foot")


# (hip offset from C, foot x offset from C, feet index, kind, far) - far legs first
LEG_SLOTS = (
    ((5.0, 2.0), 6.5, 1, "front", True),
    ((-2.5, 2.2), -2.0, 3, "hind", True),
    ((-4.0, 2.4), -3.5, 2, "hind", False),
    ((3.8, 2.4), 5.0, 0, "front", False),
)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground  # centre of the last filled row (outline lands on gy - 1)
    cr = p.crouch
    C = (cv.gx - 2 + p.bx, ground - 6.8 + p.by + cr)
    cv.opacity = p.fade
    xf = [px.scale(p.sx, p.sy, (C[0], ground))]
    cv.snap_ground = p.slump  # lying down: settle the lowest pixel onto the ground row

    def foot(dx, i):  # foot target on the ground line (+ per-foot step offsets)
        f = p.feet[i]
        return (C[0] + dx + f[0], ground - f[1] - p.lift)

    with cv.xform(*xf):
        # tail first (behind everything)
        _tail(cv, (C[0] - 7.5, C[1] + 0.5), p, ground)
        # legs go under the body: only the lower legs and feet show
        for hip, fdx, i, kind, far in (() if p.slump else LEG_SLOTS):
            _leg(cv, (C[0] + hip[0], C[1] + hip[1]), foot(fdx, i), kind, far, p, cr)
        if p.slump:  # folded legs: just the near feet peeking out under the belly
            cv.limb([(C[0] + 4.0, C[1] + 3.4), (C[0] + 6.5, C[1] + 3.6)], 0.7, FOOT, shade="two", name="foot")
            cv.limb([(C[0] - 4.5, C[1] + 3.4), (C[0] - 1.5, C[1] + 3.6)], 0.75, FOOT, shade="two", name="foot")
        # body: haunch + chest shaded as one form, breathing, pale belly
        br = p.breathe
        body = cv.union(cv.geom_ellipse(C[0] - 3.0, C[1] - 0.4 - br, 5.9, 4.3 + br, angle=-4),
                        cv.geom_ellipse(C[0] + 3.2, C[1] + 0.6, 4.6, 3.2 + br * 0.5, angle=8),
                        weights=[1.0, 0.9])
        cv.draw_geom(body, FUR, name="body", sep="deep")
        cv.ellipse(C[0] + 1.5, C[1] + 3.8, 5.8, 1.9, BELLY, shade="two", decal=True, clip="body")
        # haunch crease: a short shadow arc marks the thigh
        cv.limb([(C[0] - 1.2, C[1] + 0.2), (C[0] - 0.4, C[1] + 2.6)], 0.5, FUR, shade="flatdark",
                decal=True, clip="body")
        # head group rotates about the neck
        neck = (C[0] + 6.0, C[1] - 0.5)
        with cv.xform(px.rotate(p.head, neck)):
            H = (C[0] + 9.0, C[1] - 1.8)
            jaw_a = -8 - 28 * p.jaw
            if p.jaw > 0.05:  # lower jaw hinges open below the snout
                j0 = (H[0] + 0.5, H[1] + 1.8)
                jt = px.polar(j0, jaw_a, 4.2)
                cv.limb([j0, jt], [1.3, 0.7], FUR, shade="nolight", name="jaw")
                cv.pixel(round(jt[0]) - 1, round(jt[1]) - 1, TOOTH, name="tooth")
            nose_t = (H[0] + 6.0, H[1] + 1.4 - 0.5 * p.nose)
            head = cv.union(cv.geom_ellipse(H[0], H[1], 3.7, 3.2),
                            cv.geom_limb([(H[0] + 1.0, H[1] + 0.2), nose_t], [2.6, 0.9]),
                            weights=[1.0, 0.8])
            cv.draw_geom(head, FUR, name="head", sep="deep")
            cv.ellipse(H[0] + 1.8, H[1] + 2.0, 3.0, 1.0, BELLY, shade="soft", decal=True, clip="head")
            cv.pixel(round(nose_t[0]), round(nose_t[1] - 0.5), PINK.base, name="nose")
            if p.jaw > 0.05:  # bared incisors
                cv.pixels([(round(nose_t[0]) - 1, round(nose_t[1]) + 1),
                           (round(nose_t[0]) - 1, round(nose_t[1]) + 2)], TOOTH, name="tooth")
            else:  # mouth line
                cv.pixels([(round(H[0]) + 2, round(H[1]) + 2), (round(H[0]) + 3, round(H[1]) + 2)],
                          FUR.deep, name="mouth")
            # ear: big and round, pink inside, flattens back with p.ear
            ear_c = px.rot_pt((H[0] - 1.5, H[1] - 3.6), p.ear, (H[0] - 1.0, H[1] - 1.5))
            cv.ellipse(ear_c[0], ear_c[1], 2.6, 3.1, EAR, angle=p.ear + 12, name="ear", sep="deep")
            ear_in = px.rot_pt((H[0] - 1.1, H[1] - 3.4), p.ear, (H[0] - 1.0, H[1] - 1.5))
            cv.ellipse(ear_in[0], ear_in[1], 1.3, 2.0, PINK, angle=p.ear + 12, shade="soft",
                       decal=True, clip="ear")
            # eye
            ex, ey = round(H[0] + 1.6), round(H[1] - 1.2)
            if p.eye == "squeeze":
                cv.stamp(["k.", ".k", "k."], ex, ey - 1, {"k": px.INK}, name="eye")
            elif p.eye == "dead":
                cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")
            else:
                cv.stamp(["gi", "ik"], ex, ey, {"k": px.INK, "g": px.GLINT, "i": IRIS}, name="eye")
                if p.eye == "angry":
                    cv.pixels([(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1)], px.INK, name="brow")
        hit_at = cv.tp((C[0] + 9.0 + 6.5, C[1] + 0.5))
    if p.hit:
        fx = cv.layer(above=True, outline=False)
        px.impact(fx, hit_at[0] + 1, hit_at[1], size=3)
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, C[0] - 10, C[1] - 2, length=7, count=2, spacing=4, color=px.MIST_BLUE)
