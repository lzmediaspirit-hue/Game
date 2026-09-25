"""Canyon harpy - a russet bird-woman spirit of the Gale Canyons (Wind).

A fierce "human face, bird body" demon out of the old bestiaries: a lean feathered body,
a pale human face with a hooked slate beak of a nose and burning amber eyes, a crest of
long barred russet plumes swept back like a warrior's pheasant-feather headdress, broad
barred wings in place of arms and taloned bird legs.  A tattered crimson silk sash and a
bone-bead necklace are all that is left of the cultivator she once was.

View: side, flying right.  ~46 art px from talon to crown (51-62 with the crest and the
wings) on a 96 px art canvas (cell 192).  Flying: the anchor is the body centre.
Rig: torso centre C; the torso leans forward by ``lean`` (deg) about C, the head
counter-rotates about the neck so the face keeps looking ahead; ``tilt`` rolls the whole
body (the death tumble).  Legs are two-bone limbs solved with ``px.ik2``.
Parts, back to front: far crest plume, far wing (dark), sash streamers, barred tail fan,
far leg, torso (russet back, pale sandstone front, barring, sash band), near leg (shaggy
feathered thigh, scaly sandstone shank, hooked slate talons), neck, plume mane, face
(beak nose, jaw, hair cap), ruff, bone beads, near wing (barred primaries), near crest
plumes + bone clasp, eye + brow.
FX: screech sound rings + amber eye glow (windup), dive streaks, talon rakes + loose
feathers (attack, above layer), feather burst (hurt), landing dust (death).
Idle / walk: hovering and forward wing-beat cycles.  Windup: rears back, wings high,
talons forward, screeching (held).  Attack: a diving talon rake (hit on frame 1).
Death: tumbles out of the air with the wings folding, lands on her back and fades.
"""
import math

import helpers_batch_b as hb
import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "canyon_harpy",
    "cell": 192,
    "anchor": [96, 96],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: russet plumage, sandstone front, slate beak + talons, faded crimson silk -------
# 7 ramps (plume, flight, underside, slate, sash, bone, barring) + amber eye / glow accents;
# shadows lean violet-brown, lights lean warm sand
PLUME = px.material("ch_plume", "#f4be78", "#c77440", "#8a442f", "#522735", outline="#1a0b12",
                    thresholds=(0.88, 0.52, 0.18))
FLIGHT = px.material("ch_flight", "#c47c4a", "#8c4830", "#5f2e2d", "#3b1c2b", outline="#150910",
                     thresholds=(0.88, 0.52, 0.18))
UNDER = px.material("ch_under", "#fcebc6", "#e5c696", "#bb9170", "#80605c", outline="#22141a",
                    thresholds=(0.86, 0.5, 0.16))
SLATE = px.material("ch_slate", "#8e92a2", "#5f6174", "#3f3f53", "#28273a", outline="#0b0a12")
SASH = px.material("ch_sash", "#d9857a", "#a84b48", "#77313f", "#4a2034", outline="#170910")
BONE = px.BONE
BAR = px.material("ch_bar", "#4a2430", "#321827", "#261221", "#261221", outline="#150910")  # dark barring
BAR_P = PLUME.step(2)  # dark barring on the body plumage
IRIS = px.rgb("#ffb52e")
GLOW = px.rgb("#ffdf7a")
MOUTH = px.flat("#2c1020", outline="#0b0a12")
FX_EDGE = px.rgb("#8fb4c8")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset          lean  torso lean (deg, + = forward)   tilt  whole-body roll
# head     extra head tilt      jaw   mouth open 0..1                 eye  open|angry|squeeze|dead
# wn       near wing key (arm_deg, hand_deg, trail, fan); the far wing lags it
# fn, ff   near / far foot offset from the hip (torso frame)   toes  talon spread 0..1
# flow     how far sash / plumes stream back (0 hover .. 1 fast flight)    ph  flutter phase
# tail     tail fan spread    tail_a  tail direction (torso frame, deg)    pl  extra plume angle
# ring     screech rings life   glow  amber eye glow   streak  dive streaks
# rake     talon-rake life      burst  feather-burst life
# land     lying on the floor (death)   dust  landing dust life   fade  opacity
TAU = math.tau
REC = (192, 182, 1, 0.5)

DEFAULTS = dict(bx=0, by=0, lean=10, tilt=0, head=0, jaw=0.0, eye="open", wn=(150, 168, 1, 0.7),
                fn=(1.5, 13.0), ff=(-1.0, 12.5), toes=0.2, flow=0.15, ph=0.0, tail=0.5, tail_a=228, pl=0,
                ring=None, glow=0.0, streak=False, rake=None, burst=None, hit=False, land=False, dust=None,
                fade=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # hovering: slow beats, the body lifting on the downstroke
        dict(wn=(138, 158, 1, 0.8), by=0, ph=0.0),
        dict(wn=(222, 206, -1, 0.9), by=-1, ph=TAU / 4, fn=(1.5, 12.5), ff=(-1.0, 12.0)),
        dict(wn=REC, by=0, ph=TAU / 2),
        dict(wn=(108, 130, 1, 1.0), by=1, ph=TAU * 3 / 4),
    ],
    "walk": [  # driving forward: leaning in, legs trailing, sash streaming back
        dict(wn=(96, 116, 1, 1.0), by=2, lean=30, flow=0.9, ph=0.0, fn=(-4.0, 12.0), ff=(-6.0, 11.0)),
        dict(wn=(130, 150, 1, 0.9), by=1, lean=30, flow=0.9, ph=TAU / 6, fn=(-4.0, 12.0), ff=(-6.0, 11.0)),
        dict(wn=(172, 184, 1, 0.6), by=0, lean=29, flow=0.9, ph=TAU * 2 / 6, fn=(-4.5, 11.5), ff=(-6.5, 10.5)),
        dict(wn=(222, 206, -1, 0.9), by=-1, lean=28, flow=1.0, ph=TAU * 3 / 6, fn=(-5.0, 11.5),
             ff=(-7.0, 10.5)),
        dict(wn=(244, 226, -1, 1.0), by=-2, lean=28, flow=1.0, ph=TAU * 4 / 6, fn=(-5.0, 11.5),
             ff=(-7.0, 10.5)),
        dict(wn=(160, 172, 1, 0.4), by=0, lean=29, flow=0.9, ph=TAU * 5 / 6, fn=(-4.5, 12.0), ff=(-6.5, 11.0)),
    ],
    "windup": [  # rears back, wings flung high, talons forward, a rising screech - held
        dict(wn=(106, 128, 1, 1.0), by=-1, lean=-2, head=6, jaw=0.4, eye="angry", fn=(5.0, 11.0),
             ff=(3.0, 11.0), toes=0.5, ring=0.3, glow=0.4, tail=0.8, ph=0.6),
        dict(wn=(112, 140, 1, 1.0), bx=-1, by=-3, lean=-12, head=12, jaw=0.85, eye="angry", fn=(8.0, 9.0),
             ff=(6.0, 9.5), toes=0.85, ring=0.65, glow=0.8, tail=1.0, ph=1.4),
        dict(wn=(116, 146, 1, 1.0), bx=-2, by=-4, lean=-16, head=14, jaw=1.0, eye="angry", fn=(9.0, 8.0),
             ff=(7.0, 8.5), toes=1.0, ring=1.0, glow=1.0, tail=1.0, ph=2.0),
    ],
    "attack": [  # the dive: plunge, rake the talons through (hit), flare, climb away
        dict(wn=(162, 176, 1, 0.3), bx=4, by=3, lean=42, head=-4, jaw=0.6, eye="angry", fn=(9.0, 10.5),
             ff=(7.0, 11.0), toes=0.6, streak=True, glow=1.0, flow=1.0, tail=0.2, ph=0.3),
        dict(wn=(104, 124, 1, 1.0), bx=9, by=7, lean=14, head=-6, jaw=1.0, eye="angry", fn=(14.0, 6.5),
             ff=(12.0, 7.5), toes=1.0, rake=0.1, burst=0.25, hit=True, glow=1.0, flow=1.0, tail=0.9, ph=1.2),
        dict(wn=(222, 206, -1, 0.9), bx=7, by=4, lean=6, jaw=0.4, eye="angry", fn=(8.0, 10.5), ff=(6.0, 11.0),
             toes=0.5, rake=0.6, burst=0.7, glow=0.5, flow=0.6, tail=0.7, ph=2.0),
        dict(wn=REC, bx=3, by=1, lean=8, fn=(2.5, 12.5), ff=(0.0, 12.0), toes=0.3, ph=2.8),
    ],
    "hurt": [  # knocked back: wings flung up, feathers bursting
        dict(wn=(100, 124, 1, 1.0), bx=-4, by=-2, lean=-16, head=14, jaw=0.7, eye="squeeze", fn=(-2.0, 12.5),
             ff=(-4.0, 12.0), toes=0.8, burst=0.3, tail=1.0, flow=0.6, ph=0.8),
        dict(wn=(132, 152, 1, 0.7), bx=-3, by=-1, lean=-6, head=6, jaw=0.3, eye="squeeze", fn=(-1.0, 12.5),
             ff=(-3.0, 12.0), toes=0.4, burst=0.75, tail=0.7, flow=0.4, ph=1.6),
    ],
    "death": [  # a last shriek, she tumbles out of the air, wings folding, lands on her back
        dict(wn=(100, 122, 1, 1.0), bx=-4, by=-2, lean=-18, head=16, jaw=0.9, eye="squeeze", fn=(-2.0, 12.5),
             ff=(-4.0, 12.0), toes=0.9, burst=0.35, tail=1.0, ph=0.8),
        dict(wn=(140, 160, 1, 0.4), bx=-3, by=6, lean=-6, tilt=45, head=16, jaw=0.6, eye="dead", fn=(4.0, 11.0),
             ff=(2.0, 10.5), toes=0.5, tail=0.6, flow=0.8, ph=1.6),
        dict(wn=(22, 40, -1, 0.4), bx=0, by=12, lean=0, tilt=75, head=10, jaw=0.5, eye="dead", fn=(6.0, 9.0),
             ff=(4.0, 8.5), toes=0.3, tail=0.3, tail_a=252, flow=0.9, pl=-30, ph=2.4),
        dict(wn=(252, 264, -1, 0.9), bx=6, lean=0, tilt=90, head=-16, jaw=0.4, eye="dead", fn=(7.0, 7.0),
             ff=(5.0, 6.5), toes=0.1, tail=0.3, tail_a=268, flow=0.0, pl=-62, land=True, dust=0.35, ph=3.0,
             fade=0.6),
        dict(wn=(252, 264, -1, 0.9), bx=6, lean=0, tilt=90, head=-16, jaw=0.4, eye="dead", fn=(7.0, 7.0),
             ff=(5.0, 6.5), toes=0.1, tail=0.3, tail_a=268, flow=0.0, pl=-62, land=True, ph=3.0, fade=0.3),
    ],
})

ARM, HAND, CHORD = 11.5, 9.5, 8.5
THIGH, SHANK = 6.0, 8.0
HEAD_K = 1.12  # the human head is drawn a little larger than the body scale
LAND_BELOW = 36  # death: the floor row sits this many art px below the anchor


# ---- parts ------------------------------------------------------------------------------------
def _smooth(points, radii, samples=4):
    """Catmull-smoothed poly-line with radii interpolated along it."""
    pts = hb.catmull(points, samples=samples)
    n = len(pts) - 1
    rr = []
    for i in range(len(pts)):
        t = i / n * (len(radii) - 1)
        k = min(int(t), len(radii) - 2)
        rr.append(radii[k] + (radii[k + 1] - radii[k]) * (t - k))
    return pts, rr


def _plume(cv, root, ang, far, name, length=1.0, ph=0.0):
    """One long barred crest feather rising off the crown and streaming back, fluttering."""
    ctrl = [(0.0, 0.0), (-3.0, -3.2), (-7.2, -5.4), (-12.0, -6.2), (-16.6, -5.6), (-20.6, -3.8)]
    pts = []
    for i, (x, y) in enumerate(ctrl):
        t = i / (len(ctrl) - 1)
        w = math.sin(ph + t * 5.0) * 1.6 * t  # flutter, growing toward the tip
        pts.append(px.rot_pt((root[0] + x * length, root[1] + (y + w) * length), ang, root))
    path, rr = _smooth(pts, [0.7, 1.0, 1.05, 0.95, 0.75, 0.4])
    cv.draw_geom(cv.geom_limb(path, rr), PLUME, shade="dark" if far else "soft", name=name,
                 sep=False if far else True)
    for q in hb.resample(path, 2.6)[2:-1]:  # pheasant barring
        cv.circle(q[0], q[1], 0.7, BAR_P, shade="two", decal=True, clip=name, name=name)


def _wing(cv, S, key, far):
    arm, hand, trail, fan = key
    if far:
        arm, hand = arm - 12 * trail, hand - 10 * trail
    name = "wing_far" if far else "wing"
    info = hc.bird_wing(cv, S, arm, hand, ARM, HAND, CHORD, trail, PLUME, FLIGHT, tip=None, n_prim=5, far=far,
                        name=name, prim_len=1.25, fan=fan, tip_frac=0.3, prim_r=0.22, n_sec=4)
    if not far:  # barred primaries: pale sandstone and dark bands across the fanned flight feathers
        roots, tips = info["roots"], info["tips"]
        for f, mat in ((0.34, UNDER), (0.5, BAR), (0.66, UNDER), (0.82, BAR)):
            pts = [px.lerp_pt(r, t, f) for r, t in zip(roots, tips)]
            cv.limb(pts, 0.6, mat, shade="two", decal=True, clip=name + "_f", name=name + "_f")
        for r, t in zip(roots, tips):
            q = px.lerp_pt(r, t, 0.96)
            cv.circle(q[0], q[1], 0.9, BAR, shade="two", decal=True, clip=name + "_f", name=name + "_f")
    return info


def _tail(cv, root, ang, spread):
    """Fan of long barred tail feathers hanging down behind the hips (``ang`` screen deg)."""
    geoms, lines = [], []
    for k in range(5):
        a = ang - 11 * spread * (k - 2.0)
        ln = (12.5, 15.0, 16.0, 14.5, 12.0)[k]
        tip = px.polar(root, a, ln)
        mid = px.polar(root, a + 3, ln * 0.55)
        geoms.append(cv.geom_limb([root, mid, tip], [1.7, 1.9, 1.0]))
        lines.append((root, tip))
    cv.draw_geom(cv.union(*geoms), FLIGHT, shade="nolight", name="tail", sep="deep")
    for f in (0.5, 0.75, 0.95):
        pts = [px.lerp_pt(r, t, f) for r, t in lines]
        cv.limb(pts, 0.6, BAR, shade="two", decal=True, clip="tail", name="tail")


def _streamers(cv, knot, ang, flow, ph):
    """Two tattered crimson silk ribbons trailing from the sash knot (``ang`` screen deg)."""
    for k, (ln, r0, da) in enumerate(((17.0, 1.05, 0.0), (13.0, 0.95, 16.0))):
        a = ang + da * (1.0 - 0.5 * flow)
        pts = []
        for i in range(6):
            t = i / 5
            q = px.polar(knot, a, ln * t)
            pts.append(px.polar(q, a + 90, math.sin(ph + k * 1.9 + t * 5.0) * 1.5 * t))
        path, rr = _smooth(pts, [r0, r0, r0 * 0.95, r0 * 0.9, r0 * 0.8, 0.5])
        cv.draw_geom(cv.geom_limb(path, rr), SASH, shade="nolight" if k else "two", name="streamer")


def _leg(cv, hip, foot, toes, far, name):
    """Shaggy feathered thigh, bare scaly shank, three hooked front talons and a hind one."""
    knee = px.ik2(hip, foot, THIGH, SHANK, bend=1)
    skin = "dark" if far else "two"
    cv.limb([knee, foot], [1.2, 0.95], UNDER, shade=skin, name=name)
    fwd = -40 + 55 * toes  # front toes: relaxed and curled down .. opened wide to grab
    step = 38 + 10 * toes
    for k, a in enumerate((fwd + step, fwd, fwd - step, 212 - 30 * toes)):
        hind = k == 3
        t0 = px.polar(foot, a, 1.9 if hind else 2.8)
        t1 = px.polar(t0, a + (55 if hind else -60), 1.8 if hind else 2.3)
        cv.limb([foot, t0], [0.8, 0.7], UNDER, shade=skin, name=name)
        cv.limb([t0, t1], [0.7, 0.4], SLATE, shade="dark" if far else "two", name=name + "_talon")
    d = math.degrees(math.atan2(-(foot[1] - knee[1]), foot[0] - knee[0]))  # shank direction
    for k in (1, 2):  # scale rings on the shank
        q = px.lerp_pt(knee, foot, 0.45 + 0.2 * k)
        cv.pixel(math.floor(q[0]), math.floor(q[1]), UNDER.step(2).base, clip=name, name=name)
    thigh = cv.union(cv.geom_limb([hip, knee], [3.0, 2.1]),
                     cv.geom_polygon([px.lerp_pt(hip, knee, 0.35), px.polar(knee, d + 60, 2.0),
                                      px.polar(knee, d + 12, 2.9), px.polar(knee, d - 40, 2.0)]))
    cv.draw_geom(thigh, PLUME, shade="dark" if far else "full", name=name + "_thigh",
                 sep=False if far else "deep")


def _head(cv, H, p, parts):
    """Plume mane, pale human face with the hooked slate beak-nose, opening jaw."""
    sway = math.sin(p.ph) * 0.8
    fl = p.flow
    # plume mane behind the head, locks streaming down the nape
    mane = [(H[0] + 0.6, H[1] - 4.8), (H[0] - 2.8, H[1] - 4.4), (H[0] - 4.8, H[1] - 2.4),
            (H[0] - 7.6 - fl, H[1] + 0.2 - fl + sway), (H[0] - 5.2, H[1] + 1.4),
            (H[0] - 8.0 - fl, H[1] + 4.6 - fl + sway), (H[0] - 4.8, H[1] + 4.2),
            (H[0] - 6.2 - fl * 1.5, H[1] + 8.4 - fl + sway), (H[0] - 2.4, H[1] + 5.2), (H[0] - 0.8, H[1] + 2.8)]
    cv.polygon(mane, FLIGHT, name="mane", sep="deep")
    # mouth interior (shows when the jaw drops), jaw + chin, skull
    hinge = (H[0] - 0.6, H[1] + 1.0)
    jaw_a = -34 * p.jaw
    upper = (H[0] + 3.8, H[1] + 2.0)
    if p.jaw > 0.05:
        cv.polygon([(hinge[0] + 0.6, hinge[1] + 0.2), upper, (upper[0] + 0.6, upper[1] + 0.8),
                    px.rot_pt((H[0] + 4.0, H[1] + 3.4), jaw_a, hinge), px.rot_pt((H[0] + 0.8, H[1] + 2.8), jaw_a, hinge)],
                   MOUTH, shade="flat", name="mouth")
    with cv.xform(px.rotate(jaw_a, hinge)):
        cv.limb([(H[0] + 0.0, H[1] + 1.8), (H[0] + 3.0, H[1] + 3.2)], [2.2, 1.3], UNDER, shade="two", name="jaw",
                sep="deep")
    cv.ellipse(H[0], H[1] - 0.8, 4.0, 3.9, UNDER, shade="soft", bulge=0.55, name="head", sep="deep")
    # hair cap over the crown and back of the head: forehead, cheek and chin left bare
    cv.polygon([(H[0] - 4.6, H[1] - 5.2), (H[0] + 3.6, H[1] - 5.4), (H[0] + 4.0, H[1] - 3.8), (H[0] + 1.6, H[1] - 3.4),
                (H[0] - 0.2, H[1] - 2.2), (H[0] - 0.8, H[1] + 0.4), (H[0] - 1.4, H[1] + 5.0), (H[0] - 5.0, H[1] + 5.0)],
               FLIGHT, decal=True, clip="head", name="head")
    # hooked slate beak of a nose, set below the eye
    cv.polygon([(H[0] + 3.2, H[1] - 1.4), (H[0] + 4.6, H[1] - 0.4), (H[0] + 6.2, H[1] + 1.6), (H[0] + 5.6, H[1] + 2.6),
                (H[0] + 4.6, H[1] + 1.6), (H[0] + 3.4, H[1] + 1.6)], SLATE, shade="two", name="nose", sep="deep")
    if p.jaw <= 0.05:
        cv.line((round(H[0] + 2.0), round(H[1] + 2.4)), (round(H[0] + 3.6), round(H[1] + 2.4)), UNDER.deep,
                name="mouth")
    parts["eye"] = cv.tp((H[0] + 1.4, H[1] - 2.0))
    parts["mouth"] = cv.tp((H[0] + 4.4, H[1] + 3.0))


def _feather(fx, at, ang, ln, mat):
    """A single loose feather (FX): a short tapered vane."""
    tip = px.polar(at, ang, ln)
    fx.limb([at, px.lerp_pt(at, tip, 0.45), tip], [0.8, 1.25, 0.5], mat, shade="soft", name="feather")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + p.bx, cv.gy + p.by)

    def L(x, y):  # upright-torso offset -> rig point (torso leaned forward about C)
        return px.rot_pt((C[0] + x, C[1] + y), -p.lean, C)

    parts = {}
    neck = L(1.2, -10.5)
    H = L(3.6, -16.8)
    head_x = px.rotate(p.head + p.lean * 0.6, neck)
    crown = (H[0] + 0.6, H[1] - 4.4)
    pl_near = 3 * math.sin(p.ph) - 10 * p.flow + p.pl
    with cv.xform(px.rotate(p.tilt, C)):
        # far crest plume and far wing, behind everything
        with cv.xform(head_x):
            _plume(cv, (crown[0] - 1.0, crown[1] + 0.2), pl_near + 20, True, "plume_far", 0.85, p.ph + 1.0)
        _wing(cv, L(0.2, -9.4), p.wn, True)
        if p.land:  # lying on her back: the near wing is splayed on the ground beneath her
            _wing(cv, L(-1.2, -8.6), p.wn, False)
        # silk streamers and the barred tail fan
        hang = (262 - p.lean) * (1.0 - p.flow) + 188 * p.flow
        _streamers(cv, L(-3.6, 1.2), hang, p.flow, p.ph)
        _tail(cv, L(-2.4, 6.0), p.tail_a - p.lean, p.tail)
        # far leg
        hip_f, hip_n = L(-0.8, 5.2), L(1.0, 5.4)
        _leg(cv, hip_f, L(-0.8 + p.ff[0], 5.2 + p.ff[1]), p.toes, True, "leg_far")
        # lean torso: chest, waist, hips as one form
        g = cv.union(cv.geom_ellipse(*L(0.8, -5.2), 5.6, 6.0, angle=-p.lean - 6),
                     cv.geom_ellipse(*L(0.2, 0.8), 3.9, 4.4, angle=-p.lean),
                     cv.geom_ellipse(*L(-0.4, 4.6), 4.8, 3.8, angle=-p.lean + 10),
                     weights=[1.0, 0.8, 0.9])
        cv.draw_geom(g, PLUME, name="body")
        # pale sandstone front with fine dark barring, chevrons on the back
        cv.ellipse(*L(5.0, -2.0), 5.6, 10.5, UNDER, angle=-p.lean + 4, decal=True, clip="body", name="body")
        for k in range(4):
            x, y = 3.4 + 0.3 * (k % 2), -5.6 + 2.8 * k
            a, b = L(x - 0.9, y - 0.4), L(x + 0.9, y)
            cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), UNDER.step(2),
                    band=None, decal=True, clip="body", name="body")
        for k in range(3):
            cv.limb([L(-4.0, -6.6 + 3.6 * k), L(-2.8, -5.8 + 3.6 * k), L(-1.4, -6.8 + 3.6 * k)], 0.5, BAR_P,
                    shade="two", decal=True, clip="body", name="body")
        # the faded crimson sash knotted round the waist
        cv.limb([L(-4.4, 0.4), L(0.0, 1.6), L(4.2, 1.2)], [1.3, 1.4, 1.3], SASH, shade="two", decal=True,
                clip="body", name="sash")
        cv.circle(*L(-4.0, 1.1), 1.6, SASH, shade="two", name="sash", sep="deep")
        # near leg
        foot = L(1.0 + p.fn[0], 5.4 + p.fn[1])
        _leg(cv, hip_n, foot, p.toes, False, "leg")
        parts["talon"] = cv.tp((foot[0] + 2.0, foot[1] + 1.5))
        # neck, head, near crest plume
        with cv.xform(head_x):
            cv.limb([L(0.8, -8.5), (H[0] - 0.6, H[1] + 2.6)], [2.4, 1.9], UNDER, shade="two", name="neck")
            with cv.xform(px.scale(HEAD_K, HEAD_K, H)):
                _head(cv, H, p, parts)
        # feather ruff at the base of the neck, bone-bead necklace over it and the chest
        ruff = cv.union(*[cv.geom_ellipse(*L(1.0 + dx, -9.6 + dy), 2.3, 1.9) for dx, dy in
                          ((-2.0, -0.6), (0.0, -1.2), (2.2, 0.0), (0.8, 1.0), (-1.6, 0.8))])
        cv.draw_geom(ruff, PLUME, shade="soft", name="ruff", sep="deep")
        for k, (x, y) in enumerate(((2.0, -8.6), (3.2, -7.9), (4.2, -7.0), (5.0, -6.0))):
            q = L(x, y)
            cv.pixel(math.floor(q[0]), math.floor(q[1]), BONE.light if k % 2 == 0 else BONE.base, name="beads")
        q = L(5.4, -5.0)
        cv.pixels([(math.floor(q[0]), math.floor(q[1])), (math.floor(q[0]), math.floor(q[1]) + 1)], BONE.light,
                  name="beads")
        # near wing in front
        if not p.land:
            _wing(cv, L(-1.2, -8.6), p.wn, False)
        # the near crest plume sweeps back over everything, pinned by a bone clasp
        with cv.xform(head_x):
            _plume(cv, (crown[0] - 1.6, crown[1] + 0.8), pl_near - 16, False, "plume_low", 0.75, p.ph + 2.0)
            _plume(cv, crown, pl_near, False, "plume", 1.0, p.ph)
            cv.pixels([(math.floor(crown[0]) - 1, math.floor(crown[1]) + 1),
                       (math.floor(crown[0]), math.floor(crown[1]) + 1)], BONE.light, name="clasp")

    # ---- eye (stamped 1:1 so it stays crisp) + brow -------------------------------------------
    ex, ey = math.floor(parts["eye"][0]), math.floor(parts["eye"][1])
    face = cv.mask_of(["head"])
    eye_on = 0 <= ey < cv.h and 0 <= ex < cv.w and face[ey, ex]
    if eye_on:
        if p.eye in ("open", "angry"):
            hc.eye_stamp(cv, ["gi", "ik"], ex, ey, {"i": IRIS})
            brow = [(ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey - 1)]
            if p.eye == "angry":
                brow = [(ex - 1, ey - 2), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)]
            cv.pixels(brow, PLUME.deep, name="brow")
        elif p.eye == "squeeze":
            hc.eye_stamp(cv, ["kk.", "..k"], ex - 1, ey, {})
        else:
            hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], ex - 1, ey - 1, {})

    # ---- death: lying on the floor ----------------------------------------------------------
    if p.land:
        cv.snap_ground = True
        cv.gy = cv.gy + LAND_BELOW  # snap onto the floor row, not onto the body-centre anchor
        if p.dust is not None:
            fx = cv.layer(above=True, outline=True)
            floor = cv.gy - 1 - hc.snap_offset(cv)
            px.dust(fx, C[0] - 10, floor, p.dust, size=1.1, direction=-1)
            px.dust(fx, C[0] + 10, floor, p.dust * 0.9, size=1.0, direction=1)

    # ---- FX -----------------------------------------------------------------------------------
    if p.glow > 0 and eye_on and p.eye in ("open", "angry"):  # amber glow trailing back from the eye
        g = cv.layer(above=True, outline=False)
        n = 2 + int(p.glow * 2)
        g.line((ex - 2, ey), (ex - 1 - n, ey - 1), GLOW, name="glow")
    if p.ring is not None:  # screech: sound rings rolling out of the open mouth
        r = cv.layer(above=True, outline=False)
        m = parts["mouth"]
        t = p.ring
        for k in range(1 + int(t * 2.2)):
            rad = 4.0 + k * 3.5 + t * 2.0
            span = 42 - k * 4
            hc.arc_line(r, (m[0] + 0.5, m[1] + 0.5), rad + 1, -span, span, FX_EDGE, name="ring")
            hc.arc_line(r, (m[0], m[1]), rad, -span, span, hc.WIND, name="ring")
    if p.streak:  # dive streaks behind her
        back = cv.layer(above=False, outline=False)
        for k in range(3):
            q0 = (C[0] - 10 - k * 3, C[1] - 10 + k * 5)
            hc.wind_streak(back, q0[0] - 9, q0[1] - 6, 9, curl=0.0, direction=1, color=hc.WIND, dim=FX_EDGE)
    if p.rake is not None:  # three claw rakes torn diagonally through the target
        fx = cv.layer(above=True, outline=False)
        at = parts["talon"]
        t = p.rake
        grow = 1.0 - 0.45 * t
        for k in range(3):
            x0, y0 = at[0] + 1 + k * 4, at[1] - 11 + k
            p0 = (x0, y0 + 10 * (1 - grow))
            p1 = (x0 + 7 * grow, y0 + 13 * grow)
            mid = (px.lerp(p0[0], p1[0], 0.5) + 1.4, px.lerp(p0[1], p1[1], 0.5) - 0.8)
            for a, b in ((p0, mid), (mid, p1)):
                fx.line((round(a[0]) + 1, round(a[1])), (round(b[0]) + 1, round(b[1])), IRIS if t < 0.5 else FX_EDGE,
                        name="rake")
                fx.line((round(a[0]), round(a[1])), (round(b[0]), round(b[1])), px.GLINT, name="rake")
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, parts["talon"][0] + 1, parts["talon"][1] + 1, size=4)
    if p.burst is not None:  # loose feathers bursting out and drifting
        fx = cv.layer(above=True, outline=True)
        t = p.burst
        c0 = C if action != "attack" else (parts["talon"][0] - 6, parts["talon"][1] - 8)
        n = 7 if action != "attack" else 3
        for k in range(n):
            a = 30 + k * (300 / n) + 20 * px.hash01(action, k)
            d = (6.0 + 3.0 * px.hash01(k, 3)) + t * 10.0
            at = px.polar(c0, a, d)
            at = (at[0], at[1] + t * t * 4.0)
            mat = (PLUME, FLIGHT, UNDER)[k % 3]
            _feather(fx, at, a + 60 + t * 90 * (1 if k % 2 else -1), 4.2, mat)
