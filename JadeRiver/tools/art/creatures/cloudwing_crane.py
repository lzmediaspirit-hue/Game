"""Cloudwing crane - elegant white spirit crane with cloud-swirl wing tips (Wind).

View: side, flying right.  ~50 art px tall across the wing beat, ~54 long from the
trailing feet to the beak tip, on a 96 px art canvas (cell 192).  Flying: the anchor
is the body centre.
Parts, back to front: far wing (dark), trailing legs, tail, body, long neck + head as
one form, slate face mask, red crown, beak, gold eye, near wing (coverts over fanned
primaries whose tips carry pale cloud swirls).
Idle/walk are wing-beat cycles; windup rises with both wings high and the neck coiled;
attack is a swooping peck (hit on frame 1); death folds and falls, fading.
"""

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "cloudwing_crane",
    "cell": 192,
    "anchor": [96, 96],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: white plumage with cool slate-blue shadows, pale cloud tips ---------------------
PLUME = px.material("crane_plume", "#ffffff", "#e8f0f2", "#b3c6d2", "#7b92a6", outline="#141f2b",
                    thresholds=(0.88, 0.5, 0.15))
FLIGHT = px.material("crane_flight", "#eef5f8", "#cbd9e2", "#97aec0", "#687f95", outline="#141f2b")
CLOUD = px.material("cloud_tip", "#d6ecf7", "#9dc0d8", "#7497b6", "#56769a", outline="#122033")
SLATE = px.material("crane_slate", "#6f7f8c", "#4c5a66", "#36424d", "#252e37", outline="#0c1116")
BEAK = px.material("crane_beak", "#fff3b8", "#e3cf7a", "#b39e54", "#78693a", outline="#1d190c")
CROWN = px.material("crane_crown", "#ff8f80", "#e45858", "#b3384a", "#7a2234", outline="#240a10")
SWIRL = px.rgb("#6f8fae")
IRIS = px.rgb("#f2c14a")

# ---- poses ------------------------------------------------------------------------------------
# bx, by    body offset       tilt  body pitch (deg, + = nose up)
# wn, wf    near / far wing: a key of hc.FLAP or (arm, hand, trail, fan)
# neck      1 = straight out, 0 = coiled back (windup)        head  head tilt (deg)
# beak      open 0..1        eye  open|angry|squeeze|dead     legs  leg droop (deg)
# fade      opacity          hit  impact at the beak          wind  gust-line life
DEFAULTS = dict(bx=0, by=0, tilt=4, wn="mid", wf="mid", neck=1.0, head=0, beak=0.0, eye="open", legs=0,
                fade=1.0, hit=False, wind=None, streak=False)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow hovering beat: the body rises on the downstroke
        dict(wn="up", wf="up", by=1),
        dict(wn="mid", wf="mid", by=0, head=2),
        dict(wn="down", wf="down", by=-1, head=2),
        dict(wn="mid", wf="mid", by=0),
    ],
    "walk": [  # full flight stroke
        dict(wn="up_high", wf="up_high", by=2, tilt=6),
        dict(wn="up", wf="up", by=1, tilt=5),
        dict(wn="mid", wf="mid", by=0, tilt=4),
        dict(wn="down", wf="down", by=-1, tilt=3),
        dict(wn="down_low", wf="down_low", by=-2, tilt=2),
        dict(wn=(200, 190, 1, 0.5), wf=(195, 188, 1, 0.5), by=0, tilt=4),
    ],
    "windup": [  # rises, wings lifted high, neck coiled like a spring, beak aimed - held
        dict(wn="up", wf="up", by=-3, tilt=10, neck=0.6, head=-8, eye="angry"),
        dict(wn="up_high", wf="up_high", by=-6, tilt=14, neck=0.2, head=-18, eye="angry", beak=0.2),
        dict(wn=(108, 136, 1, 1.0), wf=(104, 132, 1, 1.0), by=-7, tilt=15, neck=0.0, head=-22, eye="angry",
             beak=0.3),
    ],
    "attack": [  # swooping peck: dives forward-down, the neck shoots out; hit on frame 1
        dict(wn="tuck", wf="tuck", bx=4, by=-2, tilt=-14, neck=0.7, head=-6, eye="angry", beak=0.5,
             streak=True),
        dict(wn="tuck", wf="tuck", bx=9, by=4, tilt=-24, neck=1.25, head=-4, eye="angry", beak=0.0, hit=True,
             streak=True),
        dict(wn="mid", wf="mid", bx=7, by=4, tilt=-12, neck=1.1, head=-2, eye="angry", wind=0.5),
        dict(wn="up", wf="up", bx=3, by=1, tilt=2, neck=1.0, wind=0.9),
    ],
    "hurt": [
        dict(wn="up_high", wf="up_high", bx=-4, by=-2, tilt=16, neck=0.5, head=20, eye="squeeze", beak=0.5,
             legs=12),
        dict(wn="up", wf="up", bx=-2, by=-1, tilt=10, neck=0.8, head=8, eye="squeeze", legs=6),
    ],
    "death": [  # recoil, then the wings fold and it falls, fading away
        dict(wn="up_high", wf="up_high", bx=-4, by=-2, tilt=16, neck=0.5, head=24, eye="squeeze", beak=0.6,
             legs=14),
        dict(wn=(118, 150, 1, 0.6), wf=(112, 146, 1, 0.6), bx=-3, by=3, tilt=-16, neck=0.8, head=-20,
             eye="dead", beak=0.4, legs=20),
        dict(wn=(138, 168, 1, 0.3), wf=(134, 164, 1, 0.3), bx=-2, by=9, tilt=-34, neck=0.9, head=-30, eye="dead",
             beak=0.4, legs=26, fade=1.0),
        dict(wn=(150, 176, 1, 0.2), wf=(146, 172, 1, 0.2), bx=-1, by=13, tilt=-44, neck=0.9, head=-34,
             eye="dead", legs=30, fade=0.6),
        dict(wn=(156, 180, 1, 0.2), wf=(152, 176, 1, 0.2), bx=0, by=16, tilt=-50, neck=0.9, head=-36, eye="dead",
             legs=32, fade=0.3),
    ],
})

ARM, HAND, CHORD = 10.0, 8.5, 8.0

# cloud swirl motif (drawn along the primaries near the wing tip)
SWIRL_ROWS = [".ww.", "w..w", "w.ww", ".w.."]

def _wing(cv, S, key, far):
    arm, hand, trail, fan = hc.FLAP[key] if isinstance(key, str) else key
    if far:  # perspective: the far wing swings a little ahead of the near one
        arm, hand = arm - 14 * trail, hand - 12 * trail
    info = hc.bird_wing(cv, S, arm, hand, ARM, HAND, CHORD, trail, PLUME, FLIGHT, tip=CLOUD, n_prim=4, far=far,
                        name="wing_far" if far else "wing", prim_len=1.3, fan=fan, tip_frac=0.5, prim_r=0.24)
    if not far and fan > 0.45:  # cloud swirl: a pale curl on the blue outer primary
        root, tp = info["roots"][0], info["tips"][0]
        c = px.lerp_pt(root, tp, 0.7)
        with cv.xform(px.rotate(hand - 90, c)):
            cv.stamp(SWIRL_ROWS, round(c[0]) - 2, round(c[1]) - 2, {"w": px.rgb("#ffffff")}, decal=True,
                     clip="wing_f", name="wing_f")
    return info


def _eye(cv, x, y, state):
    if state == "squeeze":
        hc.eye_stamp(cv, ["kk", ".k"], x, y, {})
    elif state == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], x - 1, y - 1, {})
    else:
        hc.eye_stamp(cv, ["gi"], x, y, {"i": IRIS})
        if state == "angry":
            cv.pixels([(x - 1, y - 1), (x, y - 1), (x + 1, y - 1)], SLATE.deep, name="brow")

def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx - 3 + p.bx, cv.gy + p.by)
    body_x = [px.rotate(p.tilt, C)]
    with cv.xform(*body_x):
        # far wing first (behind the body), a little higher and forward (perspective)
        _wing(cv, (C[0] + 3.5, C[1] - 3.5), p.wf, True)
        # trailing legs
        hip = (C[0] - 3.0, C[1] + 3.0)
        for k, off in enumerate((0.0, 2.2)):
            a = 186 + p.legs + k * 4
            knee = px.polar(hip, a - 6, 7.0)
            foot = px.polar(knee, a, 10.5 - k)
            cv.limb([(hip[0] + off * 0.3, hip[1] + off * 0.2), knee, foot], [0.9, 0.6, 0.5], SLATE,
                    shade="dark" if k else "two", name="leg")
            cv.limb([foot, px.polar(foot, a + 25, 2.0)], [0.5, 0.4], SLATE, shade="dark" if k else "two",
                    name="leg")
        # short tail with slate tips
        tail = [(C[0] - 7.0, C[1] - 2.2), (C[0] - 14.0, C[1] - 1.2), (C[0] - 14.8, C[1] + 1.2),
                (C[0] - 7.0, C[1] + 2.6)]
        cv.polygon(tail, FLIGHT, shade="two", name="tail")
        cv.polygon([(C[0] - 11.0, C[1] - 2.0), (C[0] - 15.0, C[1] - 1.2), (C[0] - 15.4, C[1] + 1.4),
                    (C[0] - 11.0, C[1] + 1.8)], SLATE, shade="two", decal=True, clip="tail")
        # neck + head: straight out when neck=1, coiled back up when 0
        n = p.neck
        N0 = (C[0] + 6.5, C[1] - 1.8)
        if n >= 1.0:
            H = (N0[0] + 13.0 * n, N0[1] - 3.0 + (n - 1.0) * 2.0)
            mid = px.lerp_pt(N0, H, 0.5)
            mid = (mid[0], mid[1] - 1.0)
        else:
            H = (N0[0] + 5.0 + 8.0 * n, N0[1] - 8.5 + 5.5 * n)
            mid = (N0[0] + 2.0 + 3.0 * n, N0[1] - 6.0 + 3.5 * n)
        body_g = cv.geom_ellipse(C[0], C[1], 9.5, 5.2, angle=4)
        neck_g = cv.geom_limb([N0, mid, H], [3.2, 1.7, 1.8])
        with cv.xform(px.rotate(p.head, H)):
            head_g = cv.geom_ellipse(H[0] + 0.6, H[1], 2.8, 2.3, angle=-6)
        cv.draw_geom(cv.union(body_g, neck_g, head_g, weights=[1.0, 0.55, 0.8]), PLUME, name="body")
        with cv.xform(px.rotate(p.head, H)):
            # beak (lower mandible drops open), slate face mask, red crown, eye
            with cv.xform(px.rotate(-18 * p.beak, (H[0] + 2.4, H[1] + 0.6))):
                cv.polygon([(H[0] + 2.2, H[1] + 0.2), (H[0] + 9.6, H[1] + 1.0), (H[0] + 2.2, H[1] + 1.6)], BEAK,
                           shade="two", name="beak")
            cv.polygon([(H[0] + 2.0, H[1] - 1.3), (H[0] + 5.0, H[1] - 0.7), (H[0] + 10.4, H[1] + 0.6),
                        (H[0] + 2.2, H[1] + 0.8)], BEAK, name="beak", sep="deep")
            cv.ellipse(H[0] + 1.2, H[1] + 0.2, 1.8, 1.5, SLATE, shade="two", decal=True, clip="body")
            cv.ellipse(H[0] - 0.2, H[1] - 2.0, 1.8, 1.0, CROWN, shade="soft", decal=True, clip="body")
            _eye(cv, round(H[0] + 0.6), round(H[1] - 0.6), p.eye)
            tip = cv.tp((H[0] + 10.4, H[1] + 0.6))
        # near wing on top
        _wing(cv, (C[0] + 1.0, C[1] - 2.0), p.wn, False)

    if p.streak:
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, C[0] - 12, C[1] - 4, length=10, count=3, spacing=4, direction=-1, color=hc.WIND_DIM)
    if p.wind is not None:
        w = cv.layer(above=True, outline=False)
        for k, (dx, dy, ln) in enumerate(((0, -6, 7), (3, 0, 9), (0, 6, 6))):
            hc.wind_streak(w, tip[0] - 6 + dx + p.wind * 4, tip[1] + dy, ln, curl=1.0 if k == 1 else 0.0)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0] + 2, tip[1] + 1, size=4)
