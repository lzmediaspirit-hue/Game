"""Wild boarlet - young wild boar, round and striped (Earth element).

View: side, facing right.  ~22 art px tall, ~34 long.
Parts, back to front: far legs, corkscrew tail, near legs (tucked under the belly),
body + head + muzzle shaded as one form (``cv.union``), pale piglet stripes and a
bristle ridge as decals, snout disc, tusk, ear, eye; the pawing foreleg is drawn in
front of the chest during the windup.  FX: dust puff (windup paw, charge), impact.
"""
import pixel as px

SPEC = {
    "id": "wild_boarlet",
    "cell": 128,
    "anchor": [64, 112],
    "flying": False,
    "hit_frame": 2,
}

# ---- palette: warm ochre/brown earth ramps --------------------------------------------------
HIDE = px.material("boar_hide", "#c38c50", "#925f35", "#65402e", "#422b28", outline="#1c110e",
                   thresholds=(0.92, 0.58, 0.22))
STRIPE = px.material("boar_stripe", "#f3d89c", "#d6b072", "#a88253", "#72573b", outline="#1c110e")
RIDGE = px.material("boar_ridge", "#7a4f32", "#5c3a28", "#452b22", "#301e1c", outline="#1c110e")
SNOUT = px.material("boar_snout", "#e7b08e", "#c0846a", "#8f5a52", "#5d3940", outline="#22110f")
EAR_IN = px.material("boar_ear_in", "#a8674f", "#7f4a3c", "#5c3530", "#3d2427", outline="#1c110e")
HOOF = px.material("boar_hoof", "#6a5048", "#47342f", "#342624", "#241a1b", outline="#120b0b")
TUSK = px.BONE

# ---- poses --------------------------------------------------------------------------------
# bx, by  body offset     sx, sy  squash/stretch about the feet    head  head tilt (deg)
# feet    (dx, lift) for near-front, far-front, near-hind, far-hind
# ear     ear angle        tail  curl wiggle (px)     eye  open|angry|squeeze|dead
# dust    dust puff life 0..1 (None = off)     breathe  belly swell    crouch  lower body (px)
# paw     draw the near foreleg in front of the chest (pawing)
# slump   lying flat, legs folded     fade  opacity   hit  impact fx
DEFAULTS = dict(bx=0, by=0, sx=1.0, sy=1.0, head=0, feet=((0, 0), (0, 0), (0, 0), (0, 0)),
                ear=0, tail=0.0, eye="open", dust=None, breathe=0.0, slump=False, fade=1.0,
                hit=False, crouch=0, paw=False)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(),
        dict(breathe=0.4, tail=0.5, head=1),
        dict(breathe=0.6, tail=1.0, head=1, by=0),
        dict(breathe=0.2, tail=0.5, ear=-12),
    ],
    "walk": [  # trot: diagonal pairs (near-front + far-hind) alternate
        dict(feet=((2, 0), (-1, 2), (-2, 2), (1, 0)), by=0, tail=0.0),
        dict(feet=((1, 0), (0, 2), (-1, 1), (0, 0)), by=-1, tail=0.5, head=1),
        dict(feet=((-1, 1), (1, 0), (1, 0), (-1, 1)), by=0, tail=1.0),
        dict(feet=((-1, 2), (2, 0), (1, 0), (-2, 2)), by=0, tail=1.0),
        dict(feet=((0, 2), (1, 0), (0, 0), (-1, 1)), by=-1, tail=0.5, head=1),
        dict(feet=((1, 0), (-1, 1), (-1, 1), (1, 0)), by=0, tail=0.0),
    ],
    "windup": [  # head lowered, front hoof paws the ground with a dust puff - held
        dict(head=-7, bx=-1, ear=-15, eye="angry", feet=((3, 3), (0, 0), (0, 0), (0, 0)), crouch=1,
             paw=True),
        dict(head=-11, bx=-2, ear=-25, eye="angry", feet=((-3, 0), (0, 0), (0, 0), (0, 0)),
             crouch=1, dust=0.15, paw=True),
        dict(head=-12, bx=-2, ear=-30, eye="angry", feet=((2, 3), (0, 0), (0, 0), (0, 0)),
             crouch=2, dust=0.5, sx=0.96, paw=True),
    ],
    "attack": [  # short charge: push off, run in, tusk hook on frame 2, settle
        dict(bx=2, head=-14, ear=-30, eye="angry", sx=1.05, feet=((3, 2), (2, 1), (-3, 0), (-2, 0)),
             dust=0.1),
        dict(bx=5, by=-1, head=-10, ear=-30, eye="angry", sx=1.08,
             feet=((4, 1), (3, 2), (-4, 1), (-3, 0)), dust=0.45),
        dict(bx=7, head=10, ear=-20, eye="angry", sx=1.04, feet=((2, 0), (3, 0), (-2, 0), (-1, 0)),
             hit=True, dust=0.75),
        dict(bx=4, head=2, ear=-10, feet=((1, 0), (1, 0), (-1, 0), (0, 0))),
    ],
    "hurt": [
        dict(bx=-3, by=-1, head=12, ear=-30, eye="squeeze", sy=0.95, feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-2, head=6, ear=-20, eye="squeeze"),
    ],
    "death": [  # recoil, knees buckle, flop onto the ground, fade
        dict(bx=-3, by=-1, head=14, ear=-35, eye="squeeze", feet=((1, 2), (0, 1), (0, 0), (0, 0))),
        dict(bx=-3, head=-10, ear=-30, eye="squeeze", crouch=3, sy=0.94),
        dict(bx=-3, head=-14, ear=-40, eye="dead", slump=True, sy=0.86),
        dict(bx=-3, head=-14, ear=-40, eye="dead", slump=True, sy=0.82, fade=0.6),
        dict(bx=-3, head=-14, ear=-40, eye="dead", slump=True, sy=0.78, fade=0.3),
    ],
})

# (hip offset from C, foot x offset from C, feet index, far) - far legs drawn first
LEGS = (
    ((8.0, 4.0), 8.5, 1, True),
    ((-4.5, 4.0), -4.5, 3, True),
    ((-6.5, 4.5), -7.0, 2, False),
    ((6.0, 4.5), 6.0, 0, False),
)


def _leg(cv, hip, foot, far, sep=False):
    """Stubby leg with a dark two-tone hoof."""
    fx, fy = foot
    cv.limb([hip, (fx, fy - 2.6)], [2.3, 1.5], HIDE, shade="dark" if far else "soft", name="leg", sep=sep)
    cv.limb([(fx - 0.1, fy - 1.9), (fx + 0.3, fy - 1.0)], [1.35, 1.3], HOOF, shade="dark" if far else "two",
            name="hoof", sep=False if far else "deep")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    ground = cv.ground  # centre of the last filled row (outline lands on gy - 1)
    C = (cv.gx - 3 + p.bx, ground - 11.0 + p.by + p.crouch)
    cv.opacity = p.fade
    cv.snap_ground = p.slump
    feet_base = ground - (1.0 if p.slump else 0.0)

    def foot(dx, i):
        f = p.feet[i]
        return (C[0] + dx + f[0], feet_base - f[1])

    with cv.xform(px.scale(p.sx, p.sy, (C[0], ground))):
        if not p.slump:
            for hip, fdx, i, far in LEGS[:2]:
                _leg(cv, (C[0] + hip[0], C[1] + hip[1]), foot(fdx, i), far)
        # curly tail at the rump
        t = p.tail
        T = (C[0] - 9.5, C[1] - 3.0)
        curl = [T, (T[0] - 1.8, T[1] - 1.8 - t * 0.5), (T[0] - 3.2, T[1] - 0.6),
                (T[0] - 2.2, T[1] + 0.6 - t * 0.3)]
        if p.slump:
            curl = [T, (T[0] - 2.2, T[1] + 1.0), (T[0] - 3.8, T[1] + 2.4)]
        cv.limb(curl, [0.7, 0.55, 0.5, 0.45], HIDE, shade="two", name="tail")
        # near legs go under the body too (the round belly hides the thighs)
        if not p.slump:
            for hip, fdx, i, far in LEGS[2:3] if p.paw else LEGS[2:]:
                _leg(cv, (C[0] + hip[0], C[1] + hip[1]), foot(fdx, i), far)
        # body + head as one form; the head group tilts about the neck
        neck = (C[0] + 7.0, C[1] + 0.0)
        br = p.breathe
        body_g = cv.union(cv.geom_ellipse(C[0] - 3.0, C[1] + 0.4 - br * 0.5, 7.6, 6.6 + br),
                          cv.geom_ellipse(C[0] + 2.5, C[1] - 0.6 - br * 0.5, 7.8, 7.6 + br))
        with cv.xform(px.rotate(p.head, neck)):
            H = (C[0] + 10.0, C[1] + 1.4)
            head_g = cv.geom_ellipse(H[0], H[1], 5.2, 5.2, angle=-15)
            snout_end = (H[0] + 7.2, H[1] + 2.6)
            muzzle_g = cv.geom_limb([(H[0] + 2.0, H[1] + 0.6), snout_end], [3.6, 2.5])
        cv.draw_geom(cv.union(body_g, head_g, muzzle_g, weights=[1.0, 0.7, 0.55]), HIDE, name="body",
                     sep="deep")
        # pale piglet stripes along the back (decals follow the body shading)
        for y0, y1, x0, x1 in ((-5.6, -6.2, -7.5, 5.0), (-2.6, -3.2, -9.5, 5.5), (0.4, -0.2, -9.5, 5.0)):
            pts = [(C[0] + x0, C[1] + y0 + 1.6), (C[0] + (x0 + x1) / 2, C[1] + y0 - 0.4 - br * 0.3),
                   (C[0] + x1, C[1] + y1 + 1.0)]
            cv.limb(pts, 0.55, STRIPE, shade="two", decal=True, clip="body")
        # dark bristle ridge on the spine with a few tufts
        cv.limb([(C[0] - 7.5, C[1] - 5.6), (C[0] - 1.0, C[1] - 7.9), (C[0] + 6.0, C[1] - 8.0)], 0.9, RIDGE,
                shade="two", decal=True, clip="body")
        if not p.slump:
            cv.pixels([(round(C[0]) - 2, round(C[1] - 8.4) - 1), (round(C[0]) + 1, round(C[1] - 8.8) - 1),
                       (round(C[0]) + 4, round(C[1] - 8.8) - 1)], RIDGE.base, name="bristle")
        with cv.xform(px.rotate(p.head, neck)):
            # snout disc, mouth line, tusk
            cv.ellipse(snout_end[0] + 0.3, snout_end[1], 1.3, 2.5, SNOUT, name="snout", sep="deep")
            cv.pixel(round(snout_end[0]), round(snout_end[1]) - 1, SNOUT.deep, name="nostril")
            mx, my = round(H[0] + 4.0), round(H[1] + 3.2)
            cv.pixels([(mx, my), (mx + 1, my), (mx + 2, my)], HIDE.deep, name="mouth")
            cv.limb([(H[0] + 4.6, H[1] + 3.4), (H[0] + 6.0, H[1] + 2.4), (H[0] + 6.2, H[1] + 0.6)],
                    [0.85, 0.7, 0.45], TUSK, shade="soft", name="tusk", sep="deep")
            # pointed ear, swinging back with p.ear
            ep = (H[0] - 1.8, H[1] - 3.8)
            tip = px.rot_pt((H[0] - 2.6, H[1] - 9.0), p.ear, ep)
            ear = [px.rot_pt((H[0] - 4.2, H[1] - 3.4), p.ear, ep), tip,
                   px.rot_pt((H[0] + 0.8, H[1] - 4.4), p.ear, ep)]
            cv.polygon(ear, HIDE, name="ear", sep="deep")
            cv.polygon([px.lerp_pt(ear[0], ear[2], 0.5), px.lerp_pt(tip, ear[0], 0.25),
                        px.lerp_pt(ear[2], tip, 0.35)], EAR_IN, shade="two", decal=True, clip="ear")
            # small fierce eye under a heavy brow
            ex, ey = round(H[0] + 1.5), round(H[1] - 2.2)
            if p.eye == "squeeze":
                cv.stamp(["kk.", "..k"], ex - 1, ey, {"k": px.INK}, name="eye")
            elif p.eye == "dead":
                cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")
            else:
                cv.stamp(["gk", "kk"], ex, ey, {"k": px.INK, "g": px.GLINT}, name="eye")
                brow = [(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1)]
                if p.eye == "angry":
                    brow = [(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)]
                cv.pixels(brow, HIDE.deep, name="brow")
            hit_at = cv.tp((snout_end[0] + 2.0, snout_end[1] - 3.0))
        if p.paw:  # the pawing foreleg swings in front of the chest
            hip, fdx, i, far = LEGS[3]
            _leg(cv, (C[0] + hip[0], C[1] + hip[1] - 1.0), foot(fdx, i), far, sep=True)
        if p.slump:  # folded legs: hooves peeking out under the belly
            for dx in (-6.5, 6.0):
                cv.limb([(C[0] + dx, C[1] + 6.8), (C[0] + dx + 2.2, C[1] + 7.2)], 1.2, HOOF, shade="two",
                        name="hoof")

    if p.dust is not None:
        fx = cv.layer(above=True, outline=True)
        # windup: kicked back from the scraping front hoof; attack: from the hind hooves
        px.dust(fx, C[0] + (3.0 if action == "windup" else -11.0), cv.gy - 1, p.dust,
                size=0.9, direction=-1)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, hit_at[0], hit_at[1], size=3)
