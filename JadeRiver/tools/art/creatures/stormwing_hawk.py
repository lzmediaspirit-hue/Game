"""Stormwing hawk - dark blue storm hawk with lightning-yellow streaks (Thunder).

View: side, flying right.  ~30 art px tall across the wing beat, ~44 px from wingtip to
wingtip when the wings are spread, on a 64 px art canvas (cell 128).  Flying: the anchor
is the body centre.
Parts, back to front: far wing (dark), banded fan tail, tucked yellow feet, body with a
pale barred breast, head (hooked beak, yellow cere, fierce yellow eye under a heavy brow),
near wing (coverts over fingered primaries) with a zig-zag lightning streak.
Windup mantles the wings forward over the body while sparks crackle; the attack is a
lightning dive, talons first (hit on frame 2); death spirals down and fades.
"""
import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "stormwing_hawk",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 2,
}

# ---- palette: storm blue with a yellow lightning accent ---------------------------------------
BODY = px.material("hawk_body", "#86a6f4", "#4466c2", "#2c4386", "#1b2757", outline="#070b1c",
                   thresholds=(0.88, 0.52, 0.2))
COVERT = px.material("hawk_covert", "#8eacf4", "#5070c8", "#34498e", "#202d61", outline="#070b1c")
FLIGHT = px.material("hawk_flight", "#6682d0", "#3a52a4", "#283b7a", "#1a2552", outline="#070b1c")
BREAST = px.material("hawk_breast", "#e6ecf6", "#b9c7e0", "#8397bd", "#56688f", outline="#070b1c")
BOLT_MAT = px.material("hawk_bolt", "#fff6b0", "#ffd84a", "#d9a82a", "#9c7418", outline="#1c1405")
BEAK = px.material("hawk_beak", "#5a6378", "#343b4d", "#232836", "#161a24", outline="#07090e")
CERE = px.material("hawk_cere", "#fff0a0", "#f2c63a", "#c49522", "#8a6618", outline="#1c1405")
TALON = px.rgb("#1b1d26")
IRIS = px.rgb("#ffd84a")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset      tilt  pitch (deg, + = nose up)   wn, wf  wing key / tuple
# head     head tilt        beak  open 0..1     eye  open|angry|squeeze|dead
# talons   feet: 0 tucked .. 1 thrust forward    tail  tail fan spread 0..1
# spark    crackle sparks (0..1 strength)        bolt  lightning trail (dive)   spin  death roll
DEFAULTS = dict(bx=0, by=0, tilt=4, wn="mid", wf="mid", head=0, beak=0.0, eye="angry", talons=0.0, tail=0.4,
                spark=0.0, bolt=False, hit=False, fade=1.0, seed=0, mantle=False)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(wn="up", wf="up", by=1, tail=0.5),
        dict(wn="mid", wf="mid", by=0, tail=0.4),
        dict(wn="down", wf="down", by=-1, tail=0.3),
        dict(wn="mid", wf="mid", by=0, tail=0.4, head=-3),
    ],
    "walk": [
        dict(wn="up_high", wf="up_high", by=2, tilt=6, tail=0.5),
        dict(wn="up", wf="up", by=1, tilt=5, tail=0.4),
        dict(wn="mid", wf="mid", by=0, tilt=4, tail=0.3),
        dict(wn="down", wf="down", by=-1, tilt=2, tail=0.3),
        dict(wn="down_low", wf="down_low", by=-2, tilt=1, tail=0.4),
        dict(wn=(196, 188, 1, 0.4), wf=(192, 186, 1, 0.4), by=0, tilt=4, tail=0.5),
    ],
    "windup": [  # mantles: wings arched forward over the body, hunched, sparks crackling - held
        dict(wn=(78, 60, -1, 0.9), wf=(84, 66, -1, 0.9), by=-2, tilt=8, head=-10, beak=0.3, tail=0.8,
             spark=0.4, seed=1, mantle=True),
        dict(wn=(66, 18, -1, 1.0), wf=(74, 26, -1, 1.0), by=-4, tilt=10, head=-18, beak=0.6, tail=1.0,
             spark=0.8, seed=2, talons=0.3, mantle=True),
        dict(wn=(62, 6, -1, 1.0), wf=(70, 14, -1, 1.0), by=-4, tilt=10, head=-20, beak=0.7, tail=1.0,
             spark=1.0, seed=3, talons=0.4, mantle=True),
    ],
    "attack": [  # lightning dive: tucks and plunges, talons thrust forward; hit on frame 2
        dict(wn="tuck", wf="tuck", bx=-2, by=-4, tilt=-22, head=-6, beak=0.4, tail=0.1, talons=0.4, bolt=True,
             seed=4),
        dict(wn="tuck", wf="tuck", bx=4, by=2, tilt=-34, head=0, beak=0.6, tail=0.1, talons=0.8, bolt=True,
             seed=5),
        dict(wn="up", wf="up", bx=7, by=5, tilt=6, head=-8, beak=0.8, tail=1.0, talons=1.0, hit=True, spark=0.6,
             seed=6),
        dict(wn="mid", wf="mid", bx=4, by=2, tilt=4, tail=0.6, talons=0.3),
    ],
    "hurt": [
        dict(wn="up_high", wf="up_high", bx=-4, by=-2, tilt=18, head=16, eye="squeeze", beak=0.6, tail=0.9),
        dict(wn="up", wf="up", bx=-2, by=-1, tilt=10, head=8, eye="squeeze", beak=0.2, tail=0.6),
    ],
    "death": [  # spirals down, trailing crackles, fading
        dict(wn="up_high", wf="up_high", bx=-4, by=-2, tilt=18, head=16, eye="squeeze", beak=0.6, tail=0.9),
        dict(wn=(120, 150, 1, 0.5), wf=(116, 146, 1, 0.5), bx=-3, by=2, tilt=-40, head=-10, eye="dead",
             beak=0.5, tail=0.3, spark=0.3, seed=7),
        dict(wn=(140, 170, 1, 0.3), wf=(136, 166, 1, 0.3), bx=-1, by=6, tilt=-110, head=-10, eye="dead",
             beak=0.5, tail=0.2),
        dict(wn=(150, 176, 1, 0.3), wf=(146, 172, 1, 0.3), bx=1, by=9, tilt=-200, head=-10, eye="dead",
             beak=0.5, tail=0.2, fade=0.6),
        dict(wn=(150, 176, 1, 0.3), wf=(146, 172, 1, 0.3), bx=2, by=11, tilt=-290, head=-10, eye="dead",
             beak=0.5, tail=0.2, fade=0.3),
    ],
})

ARM, HAND, CHORD = 7.0, 6.0, 5.6


def _wing(cv, S, key, far):
    arm, hand, trail, fan = hc.FLAP[key] if isinstance(key, str) else key
    if far:
        arm, hand = arm - 14 * trail, hand - 12 * trail
    info = hc.bird_wing(cv, S, arm, hand, ARM, HAND, CHORD, trail, COVERT, FLIGHT, tip=None, n_prim=4, far=far,
                        name="wing_far" if far else "wing", prim_len=1.35, fan=fan, prim_r=0.26, n_sec=3)
    if not far:  # zig-zag lightning streak across the flight feathers
        W, T = info["W"], info["T"]
        tr = hand + 90 * trail
        a = px.polar(px.lerp_pt(S, W, 0.55), arm + 90 * trail, CHORD * 0.62)
        b = px.polar(W, tr, CHORD * 0.72)
        c = px.polar(px.lerp_pt(W, T, 0.55), tr, CHORD * 0.45)
        d = info["tips"][1]
        pts = [a, b, c, px.lerp_pt(c, d, 0.75)]
        for p0, p1 in zip(pts, pts[1:]):
            cv.line((round(p0[0] - 0.5), round(p0[1] - 0.5)), (round(p1[0] - 0.5), round(p1[1] - 0.5)),
                    BOLT_MAT, band=1, decal=True, clip="wing_f", name="wing_f")
    return info


def _eye(cv, x, y, state):
    if state == "squeeze":
        hc.eye_stamp(cv, ["kk.", "..k"], x - 1, y, {})
    elif state == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], x - 1, y - 1, {})
    else:
        hc.eye_stamp(cv, ["gi", "ik"], x, y, {"i": IRIS})


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + p.bx, cv.gy + p.by)
    back = cv.layer(above=False, outline=False)
    with cv.xform(px.rotate(p.tilt, C)):
        _wing(cv, (C[0] + 2.4, C[1] - 3.0), p.wf, True)
        if p.mantle:  # mantling: the near wing arches up over the hunched head, behind it
            _wing(cv, (C[0] + 0.5, C[1] - 2.4), p.wn, False)
        # banded fan tail
        sp = p.tail
        tail = [(C[0] - 4.0, C[1] - 1.2), (C[0] - 15.0, C[1] - 2.6 - sp * 1.8), (C[0] - 15.8, C[1] + 0.6),
                (C[0] - 15.0, C[1] + 3.2 + sp * 1.4), (C[0] - 4.0, C[1] + 1.8)]
        cv.polygon(tail, FLIGHT, shade="two", name="tail")
        for k, t in enumerate((0.62, 0.93)):
            q0 = px.lerp_pt(tail[0], tail[1], t)
            q1 = px.lerp_pt(tail[4], tail[3], t)
            cv.line((round(q0[0]), round(q0[1])), (round(q1[0]), round(q1[1])), BOLT_MAT if k == 1 else BODY.deep,
                    band=None, decal=True, clip="tail", name="tail")
        # feet: tucked under the belly, thrust forward for the strike
        tl = p.talons
        hip = (C[0] + 1.0, C[1] + 3.0)
        for k in (1, 0):
            foot = (C[0] - 2.0 + tl * 9.0 + k * 1.2, C[1] + 5.0 + tl * 2.0 - k * 0.6)
            cv.limb([hip, foot], [1.3, 0.9], CERE, shade="dark" if k else "two", name="leg")
            for j, dx in enumerate((-0.8, 0.6, 1.8)):
                cv.pixel(round(foot[0] + dx), round(foot[1] + 1.2), TALON, name="talon")
        # body: breast + back as one form, then the head
        H = (C[0] + 7.4, C[1] - 2.6)
        body_g = cv.geom_ellipse(C[0], C[1], 7.2, 4.4, angle=6)
        with cv.xform(px.rotate(p.head, (C[0] + 5.0, C[1] - 1.0))):
            head_g = cv.geom_ellipse(H[0], H[1], 3.6, 3.2)
        cv.draw_geom(cv.union(body_g, head_g, weights=[1.0, 0.9]), BODY, name="body")
        cv.ellipse(C[0] + 2.4, C[1] + 2.6, 5.6, 2.6, BREAST, shade="two", decal=True, clip="body")
        for k in range(3):  # breast bars
            x = C[0] + 0.2 + k * 2.2
            cv.line((round(x), round(C[1] + 2.0)), (round(x + 1.0), round(C[1] + 2.0)), BREAST.deep, band=None,
                    decal=True, clip="body", name="body")
        with cv.xform(px.rotate(p.head, (C[0] + 5.0, C[1] - 1.0))):
            cv.ellipse(H[0] + 1.4, H[1] + 1.8, 2.2, 1.3, BREAST, shade="two", decal=True, clip="body")
            # hooked beak: cere, upper mandible with a hook, lower mandible opens
            with cv.xform(px.rotate(-26 * p.beak, (H[0] + 2.6, H[1] + 0.8))):
                cv.polygon([(H[0] + 2.4, H[1] + 0.8), (H[0] + 5.0, H[1] + 1.0), (H[0] + 2.4, H[1] + 2.0)], BEAK,
                           shade="two", name="beak")
            cv.polygon([(H[0] + 2.2, H[1] - 1.4), (H[0] + 4.6, H[1] - 1.0), (H[0] + 6.0, H[1] + 0.4),
                        (H[0] + 5.6, H[1] + 2.2), (H[0] + 4.4, H[1] + 0.8), (H[0] + 2.4, H[1] + 1.0)], BEAK,
                       name="beak", sep="deep")
            cv.polygon([(H[0] + 2.0, H[1] - 1.5), (H[0] + 3.6, H[1] - 1.3), (H[0] + 3.6, H[1] + 0.9),
                        (H[0] + 2.0, H[1] + 1.0)], CERE, shade="two", decal=True, clip="beak", name="beak")
            ex, ey = round(H[0] + 0.4), round(H[1] - 1.2)
            _eye(cv, ex, ey, p.eye)
            if p.eye not in ("dead", "squeeze"):  # fierce brow ridge
                cv.pixels([(ex - 2, ey - 1), (ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex + 2, ey)],
                          BODY.deep, name="brow")
        if not p.mantle:
            _wing(cv, (C[0] + 1.0, C[1] - 1.6), p.wn, False)
        claw = cv.tp((C[0] - 2.0 + p.talons * 9.0 + 2.0, C[1] + 7.5 + p.talons * 2.0))
        if p.bolt:  # the lightning trail it rides down
            hc.bolt(back, (C[0] - 26, C[1] - 5), (C[0] - 6, C[1] - 1), seed=p.seed, jag=2.6, segs=6)
            hc.bolt(back, (C[0] - 22, C[1] + 5), (C[0] - 8, C[1] + 2), seed=p.seed + 11, jag=2.0, segs=5, fork=False)
    if p.spark > 0:
        fx = cv.layer(above=True, outline=False)
        s = p.spark
        for k, (ox, oy, dx, dy) in enumerate(((-9, -14, -3, 7), (7, -16, 3, 6), (-14, -4, -4, 6), (11, -7, 4, 5))):
            if k < 1 + round(s * 3):
                hc.bolt(fx, (C[0] + ox, C[1] + oy), (C[0] + ox + dx, C[1] + oy + dy), seed=p.seed * 7 + k, jag=1.6,
                        segs=4, fork=False)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, claw[0] + 1, claw[1], size=4, color=hc.BOLT)
