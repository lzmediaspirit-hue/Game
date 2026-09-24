"""Cloudpeak roc - a huge white-and-gold storm roc of the high peaks (Wind).

View: side, flying right.  ~70 art px tall body-and-wings at rest in the beat, ~110 px
wing to wing across the full beat, on a 128 px art canvas (cell 256).  Flying: the
anchor is the body centre.
Parts, back to front: far wing (dark), long gold-banded tail fan, tucked golden talons,
body + neck + head as one form, gold crest plumes, hooked gold beak, fierce amber eye
under a heavy brow, near wing (warm-white coverts over fingered primaries with gold
tips).  FX: wind swirls gathering in the windup, a great gust of wind lines in the
attack.
Idle/walk: heavy wing beats; windup: the wings rear back and up gathering wind (held);
attack: a great forward wing gust (hit on frame 1); death: it folds and falls, fading.
"""
import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "cloudpeak_roc",
    "cell": 256,
    "anchor": [128, 128],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: warm white plumage, gold trim, slate-violet shadows ------------------------------
PLUME = px.material("roc_plume", "#ffffff", "#f1ebdc", "#c9bb9c", "#8f7d5f", outline="#211a10",
                    thresholds=(0.88, 0.5, 0.15))
FLIGHT = px.material("roc_flight", "#fbf6ea", "#ddd1b6", "#ad9b78", "#7a6a4f", outline="#211a10")
GOLD = px.material("roc_gold", "#fff2b4", "#e8bb4e", "#b3862f", "#7a5a21", outline="#241806",
                   thresholds=(0.85, 0.5, 0.15))
BEAK = px.material("roc_beak", "#fff0b2", "#efc45a", "#b98b34", "#7c5b23", outline="#241806")
TALON = px.material("roc_talon", "#6a5a4a", "#403428", "#2c231c", "#1c1612", outline="#0c0906")
IRIS = px.rgb("#ffb830")

# ---- poses ------------------------------------------------------------------------------------
# bx, by   body offset       tilt  body pitch (deg)     wn, wf  wing (arm, hand, trail, fan)
# head     head tilt         beak  open 0..1            eye  angry|squeeze|dead
# talons   0 tucked .. 1 thrust forward                 tail  tail fan spread 0..1
# gather   wind-swirl life (windup)    gust  gust-line life (attack)    fade  opacity
UP_HIGH = (98, 116, 1, 1.0)
UP = (76, 104, 1, 1.0)
MID = (150, 166, 1, 0.7)
DOWN = (234, 214, -1, 0.9)
DOWN_LOW = (258, 234, -1, 1.0)
DEFAULTS = dict(bx=0, by=0, tilt=4, wn=MID, wf=MID, head=0, beak=0.0, eye="angry", talons=0.0, tail=0.5,
                gather=None, gust=None, hit=False, fade=1.0, crest=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow, heavy hovering beats
        dict(wn=UP, wf=UP, by=5, crest=0.0),
        dict(wn=MID, wf=MID, by=1, crest=0.5, head=2),
        dict(wn=DOWN, wf=DOWN, by=-2, crest=1.0, head=2),
        dict(wn=(196, 184, 1, 0.5), wf=(192, 182, 1, 0.5), by=0, crest=0.5),
    ],
    "walk": [
        dict(wn=UP_HIGH, wf=UP_HIGH, by=6, tilt=6),
        dict(wn=UP, wf=UP, by=4, tilt=5, crest=0.4),
        dict(wn=MID, wf=MID, by=0, tilt=4, crest=0.8),
        dict(wn=DOWN, wf=DOWN, by=-2, tilt=3, crest=1.0),
        dict(wn=DOWN_LOW, wf=DOWN_LOW, by=-4, tilt=2, crest=0.6),
        dict(wn=(196, 184, 1, 0.5), wf=(192, 182, 1, 0.5), by=0, tilt=4, crest=0.2),
    ],
    "windup": [  # the wings rear back and up, drawing the wind in around them - held
        dict(wn=(112, 140, 1, 1.0), wf=(106, 134, 1, 1.0), by=-2, tilt=8, head=-4, talons=0.3, tail=0.8,
             gather=0.3, beak=0.3),
        dict(wn=(122, 156, 1, 1.0), wf=(116, 150, 1, 1.0), by=-4, tilt=12, head=-8, talons=0.6, tail=1.0,
             gather=0.65, beak=0.6, crest=1.0),
        dict(wn=(126, 162, 1, 1.0), wf=(120, 156, 1, 1.0), by=-5, tilt=14, head=-10, talons=0.7, tail=1.0,
             gather=1.0, beak=0.7, crest=1.0),
    ],
    "attack": [  # a great forward beat: the gust bursts out on frame 1
        dict(wn=(70, 60, 1, 1.0), wf=(64, 56, 1, 1.0), by=-2, tilt=6, head=-4, talons=0.6, tail=0.8, beak=0.9,
             gust=0.1),
        dict(wn=(296, 322, -1, 1.0), wf=(290, 316, -1, 1.0), bx=-3, by=2, tilt=-4, head=0, talons=0.9, tail=1.0,
             beak=1.0, gust=0.45, hit=True, crest=1.0),
        dict(wn=(262, 280, -1, 0.9), wf=(256, 274, -1, 0.9), bx=-4, by=1, tilt=0, talons=0.6, tail=0.8, beak=0.5,
             gust=0.8, crest=0.6),
        dict(wn=MID, wf=MID, bx=-2, by=0, tilt=4, talons=0.2, tail=0.6, crest=0.2),
    ],
    "hurt": [
        dict(wn=UP_HIGH, wf=UP_HIGH, bx=-5, by=-3, tilt=18, head=18, eye="squeeze", beak=0.6, tail=1.0, crest=1.0),
        dict(wn=UP, wf=UP, bx=-3, by=2, tilt=10, head=8, eye="squeeze", beak=0.2, tail=0.7, crest=0.5),
    ],
    "death": [  # a final cry, then the wings fold and it drops, fading away
        dict(wn=UP_HIGH, wf=UP_HIGH, bx=-5, by=-3, tilt=20, head=24, eye="squeeze", beak=0.9, tail=1.0, crest=1.0),
        dict(wn=(118, 148, 1, 0.6), wf=(112, 142, 1, 0.6), bx=-4, by=4, tilt=-14, head=-16, eye="dead", beak=0.5,
             tail=0.6),
        dict(wn=(136, 166, 1, 0.3), wf=(130, 160, 1, 0.3), bx=-3, by=12, tilt=-32, head=-24, eye="dead",
             beak=0.5, tail=0.4),
        dict(wn=(146, 174, 1, 0.2), wf=(140, 168, 1, 0.2), bx=-2, by=18, tilt=-44, head=-28, eye="dead",
             beak=0.5, tail=0.3, fade=0.6),
        dict(wn=(150, 178, 1, 0.2), wf=(144, 172, 1, 0.2), bx=-1, by=22, tilt=-50, head=-30, eye="dead",
             beak=0.5, tail=0.3, fade=0.3),
    ],
})

ARM, HAND, CHORD = 20.0, 15.5, 14.5


def _wing(cv, S, key, far):
    arm, hand, trail, fan = key
    if far:
        arm, hand = arm - 12 * trail, hand - 10 * trail
    return hc.bird_wing(cv, S, arm, hand, ARM, HAND, CHORD, trail, PLUME, FLIGHT, tip=GOLD, n_prim=5, far=far,
                        name="wing_far" if far else "wing", prim_len=1.3, fan=fan, tip_frac=0.3, prim_r=0.2, n_sec=5)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx - 4 + p.bx, cv.gy + p.by)
    with cv.xform(px.rotate(p.tilt, C)):
        _wing(cv, (C[0] + 6.0, C[1] - 7.0), p.wf, True)
        # long tail fan with gold bands
        sp = p.tail
        tail = [(C[0] - 14.0, C[1] - 3.5), (C[0] - 38.0, C[1] - 7.0 - sp * 4.0), (C[0] - 40.0, C[1] + 1.0),
                (C[0] - 38.0, C[1] + 8.0 + sp * 3.0), (C[0] - 14.0, C[1] + 5.0)]
        cv.polygon(tail, FLIGHT, shade="two", name="tail")
        for t, mat in ((0.6, GOLD), (0.92, GOLD)):
            q0 = px.lerp_pt(tail[0], tail[1], t)
            q1 = px.lerp_pt(tail[4], tail[3], t)
            cv.limb([q0, q1], 1.0, mat, shade="two", decal=True, clip="tail", name="tail")
        for k in (1, 2):  # feather splits in the fan
            q0 = px.lerp_pt(tail[0], tail[4], k / 3)
            q1 = px.lerp_pt(tail[1], tail[3], k / 3)
            cv.line((round(q0[0]), round(q0[1])), (round(q1[0]), round(q1[1])), FLIGHT.step(1), band=None,
                    decal=True, clip="tail", name="tail")
        # talons: tucked under the belly, thrust forward in the windup / attack
        tl = p.talons
        for k in (1, 0):
            hip = (C[0] + 2.0 - k * 2.5, C[1] + 9.0)
            foot = (C[0] - 5.0 + tl * 18.0 - k * 2.5, C[1] + 14.0 + tl * 3.0 - k * 1.0)
            cv.limb([hip, foot], [3.6, 2.4], GOLD, shade="dark" if k else "two", name="leg")
            for j, da in enumerate((-40, -10, 20)):
                q = px.polar(foot, da - 20 + tl * 30, 4.0)
                cv.limb([foot, q], [1.2, 0.6], TALON, shade="dark" if k else "two", name="talon")
        # body + neck + head as one form
        H = (C[0] + 23.0, C[1] - 9.5)
        body_g = cv.geom_ellipse(C[0], C[1], 20.0, 13.0, angle=6)
        neck_g = cv.geom_limb([(C[0] + 11.0, C[1] - 3.0), H], [10.0, 7.2])
        with cv.xform(px.rotate(p.head, H)):
            head_g = cv.geom_ellipse(H[0] + 1.0, H[1], 7.8, 7.0, angle=-4)
        cv.draw_geom(cv.union(body_g, neck_g, head_g, weights=[1.0, 0.6, 0.9]), PLUME, name="body")
        # gold breast feather scallops
        for k in range(4):
            q = (C[0] + 6.0 + k * 3.2, C[1] + 5.5 - k * 1.6)
            cv.limb([(q[0] - 2.0, q[1] - 1.0), (q[0], q[1] + 0.6), (q[0] + 2.0, q[1] - 1.0)], 0.5, PLUME.step(1),
                    shade="two", decal=True, clip="body", name="body")
        with cv.xform(px.rotate(p.head, H)):
            # crest plumes sweeping back from the crown
            for k, (dx, ln, a) in enumerate(((-4.0, 12.0, 172), (-1.5, 15.0, 164), (1.0, 11.0, 156))):
                root = (H[0] + dx, H[1] - 5.2)
                tip = px.polar(root, a - p.crest * 10 + k * 2, ln)
                mid = px.lerp_pt(root, tip, 0.5)
                mid = (mid[0], mid[1] - 1.5)
                cv.limb([root, mid, tip], [1.8, 1.4, 0.6], GOLD, shade="two", name="crest", sep="deep")
            # hooked beak: the lower mandible drops open
            with cv.xform(px.rotate(-22 * p.beak, (H[0] + 5.0, H[1] + 2.4))):
                cv.polygon([(H[0] + 4.6, H[1] + 2.2), (H[0] + 12.0, H[1] + 3.4), (H[0] + 5.0, H[1] + 5.0)], BEAK,
                           shade="two", name="beak")
            cv.polygon([(H[0] + 4.0, H[1] - 2.6), (H[0] + 10.0, H[1] - 1.6), (H[0] + 14.0, H[1] + 1.4),
                        (H[0] + 13.6, H[1] + 5.2), (H[0] + 11.6, H[1] + 2.8), (H[0] + 4.4, H[1] + 2.6)], BEAK,
                       name="beak", sep="deep")
            cv.pixel(round(H[0] + 8), round(H[1] - 1), BEAK.deep, name="beak")
            # fierce eye under a heavy brow
            ex, ey = round(H[0] + 2.0), round(H[1] - 1.5)
            if p.eye == "squeeze":
                hc.eye_stamp(cv, ["kkk.", "...k"], ex - 1, ey, {})
            elif p.eye == "dead":
                hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], ex - 1, ey - 1, {})
            else:
                hc.eye_stamp(cv, ["gii", "ikk"], ex, ey, {"i": IRIS})
                cv.limb([(ex - 2.5, ey - 1.0), (ex + 1.5, ey - 1.8), (ex + 4.5, ey - 0.2)], [1.2, 1.1, 0.7],
                        PLUME, shade="nolight", name="brow", sep="deep")
        _wing(cv, (C[0] + 3.0, C[1] - 5.0), p.wn, False)

    if p.gather is not None:  # wind spiralling in around the reared wings
        g = cv.layer(above=True, outline=False)
        t = p.gather
        for k, (cx, cy, r) in enumerate(((C[0] - 20, C[1] - 36, 11), (C[0] + 6, C[1] - 44, 8),
                                         (C[0] - 38, C[1] - 14, 8))):
            rr = r * (1.3 - 0.4 * t)
            hc.spiral(g, (cx, cy), rr, rr * 0.25, 60 + k * 70 - t * 90, -300, hc.WIND if k != 1 else hc.WIND_DIM)
            q = px.polar((cx, cy), 60 + k * 70 - t * 90, rr)
            x0 = max(4.0, q[0] - 8 - 6 * (1 - t))
            hc.wind_streak(g, x0, q[1], q[0] - x0, curl=0.0, color=hc.WIND_DIM)
    if p.gust is not None:  # the great gust: long wind lines blasting forward
        g = cv.layer(above=True, outline=False)
        t = p.gust
        for k, (dy, ln, cu) in enumerate(((-22, 20, 1.5), (-10, 30, 0.0), (0, 36, 2.0), (10, 28, 0.0), (20, 18, 1.0))):
            x0 = C[0] + 30 + t * 14 - abs(dy) * 0.3
            L = ln * (0.45 + 0.35 * min(1.0, t * 1.6))
            if x0 + L < cv.w - 6:
                hc.wind_streak(g, x0, C[1] + dy, L, curl=cu, color=hc.WIND if k % 2 == 0 else px.rgb("#dcecf2"))
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, C[0] + 52, C[1] + 2, size=5)
