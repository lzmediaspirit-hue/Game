"""Hollow minnow - a small river fish drained grey by the Hollow; it swims through the
night air (Hollow element, event creature, flying).

View: side, facing right.  ~15 art px long, ~7 tall (fins included) on a 64 px canvas;
anchored at the body centre (``flying``).  Built with ``helpers_batch_a.hollow_fish``:
forked tail, ragged dorsal fin, dark back / pale belly, empty white eye in a dark socket.
Faint grey mist wisps trail from the tail; the death dissolves the fish into mist.
"""
import math

import helpers_batch_a as hb
import pixel as px

SPEC = {
    "id": "hollow_minnow",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 1,
}

LENGTH, HEIGHT = 16.0, 6.2
TAU = 2 * math.pi

# bx, by   body offset from the anchor      ang  pitch (deg, + nose up)
# amp, ph  swim wave amplitude / phase     tail  extra tail-fin swing (deg)
# jaw      mouth gape 0..1                 fin   pectoral flap (deg)
# eye      open|wide|angry|squeeze|dead    flip  belly-up (death)
# dis      dissolve progress 0..1          mist  mist-puff life (None = off)
# trail    tail-wisp length                 fade  frame opacity    hit  impact fx
DEFAULTS = dict(bx=0, by=0, ang=0, amp=0.35, ph=0.0, tail=0, jaw=0.0, fin=0, eye="open", flip=False,
                dis=0.0, mist=None, trail=4.0, fade=1.0, hit=False, speed=False)

POSE = px.poses(DEFAULTS, {
    "idle": [  # hovering: slow bob, lazy tail and fin
        dict(ph=0.0, fin=0),
        dict(ph=TAU / 4, by=-1, fin=-15, trail=4.5),
        dict(ph=TAU / 2, by=-1, fin=-25, trail=5.0),
        dict(ph=3 * TAU / 4, fin=-10, trail=4.5),
    ],
    "walk": [  # tail-swish swim: a travelling wave down the body
        dict(amp=1.1, ph=0.0, tail=10, fin=-10, trail=5.0),
        dict(amp=1.1, ph=TAU / 6, tail=4, by=-1, fin=-25, trail=5.5),
        dict(amp=1.1, ph=2 * TAU / 6, tail=-8, by=-1, fin=-30, trail=6.0),
        dict(amp=1.1, ph=3 * TAU / 6, tail=-10, fin=-15, trail=5.5),
        dict(amp=1.1, ph=4 * TAU / 6, tail=-4, by=1, fin=0, trail=5.0),
        dict(amp=1.1, ph=5 * TAU / 6, tail=8, by=1, fin=-5, trail=5.0),
    ],
    "windup": [  # draws back, nose up, body curls, mouth opens wide - held
        dict(bx=-2, ang=6, amp=0.9, ph=1.6, tail=14, jaw=0.4, eye="angry", fin=-20, trail=3.0),
        dict(bx=-4, ang=10, amp=1.4, ph=1.6, tail=22, jaw=0.8, eye="angry", fin=-35, trail=2.5),
        dict(bx=-5, ang=12, amp=1.6, ph=1.6, tail=26, jaw=1.0, eye="angry", fin=-40, trail=2.0),
    ],
    "attack": [  # darting nibble: shoot forward, snap shut on frame 1, drift back
        dict(bx=3, ang=-2, amp=0.6, ph=4.0, tail=-14, jaw=1.0, eye="angry", speed=True, trail=7.0),
        dict(bx=8, ang=-6, amp=0.4, ph=4.8, tail=-6, jaw=0.0, eye="angry", hit=True, speed=True, trail=8.0),
        dict(bx=6, ang=-2, amp=0.8, ph=5.6, tail=10, jaw=0.3, trail=6.0),
        dict(bx=2, amp=0.6, ph=0.4, tail=6, trail=5.0),
    ],
    "hurt": [
        dict(bx=-3, by=-1, ang=18, amp=1.2, ph=1.0, tail=24, jaw=0.5, eye="squeeze", fin=-40, trail=2.5),
        dict(bx=-2, ang=8, amp=0.8, ph=1.6, tail=12, jaw=0.2, eye="squeeze", fin=-20, trail=3.0),
    ],
    "death": [  # jerk, roll belly-up, dissolve tail-first into grey mist
        dict(bx=-3, by=-1, ang=24, amp=1.3, ph=1.0, tail=26, jaw=0.6, eye="squeeze", fin=-40, trail=2.0),
        dict(bx=-3, by=1, ang=-8, flip=True, amp=0.8, ph=2.0, tail=-10, jaw=0.4, eye="dead", trail=2.0,
             dis=0.18, mist=0.1),
        dict(bx=-3, by=2, ang=-10, flip=True, amp=0.4, ph=2.4, jaw=0.3, eye="dead", trail=0, dis=0.5, mist=0.35),
        dict(bx=-3, by=2, ang=-10, flip=True, amp=0.4, ph=2.4, jaw=0.3, eye="dead", trail=0, dis=0.82, mist=0.6,
             fade=0.6),
        dict(bx=-3, by=2, ang=-10, flip=True, amp=0.4, ph=2.4, jaw=0.3, eye="dead", trail=0, dis=1.01, mist=0.9,
             fade=0.3),
    ],
})


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    C = (cv.gx + 0.5 + p.bx, cv.gy + 0.5 + p.by)
    cv.opacity = p.fade
    back = cv.layer(above=False, outline=False)
    # faint wisps trailing from the tail (behind the fish)
    if p.trail > 0:
        tt = cv.tp((C[0] - LENGTH * 0.5, C[1]))
        with cv.xform(px.rotate(p.ang, C)):
            t0 = px.rot_pt((C[0] - LENGTH * 0.72, C[1] - 0.5), p.ang, C)
            t1 = px.rot_pt((C[0] - LENGTH * 0.2, C[1] - HEIGHT * 0.95), p.ang, C)
        hb.mist_trail(back, t0[0], t0[1], length=p.trail, phase=p.ph + frame * 0.9, thick=0.7, wave=1.4)
        if p.trail >= 4.5:
            hb.mist_trail(back, t1[0] - 1, t1[1], length=p.trail * 0.55, phase=p.ph + 2.0, thick=0.55, wave=1.0)
    xf = [px.flip_y(C[1])] if p.flip else []
    with cv.xform(*xf):
        pts = hb.hollow_fish(cv, C, LENGTH, HEIGHT, ang=p.ang, amp=p.amp, phase=p.ph, tail=p.tail, jaw=p.jaw,
                             fin=p.fin, eye=p.eye, eye_size=2, dorsal=0.95, detail=False,
                             tail_len=0.36, tail_spread=30)
    if p.dis > 0:
        bb = hb.body_bbox(cv)
        m = hb.dissolve_mask(cv, p.dis, seed=frame, cells=2.0, direction=(-1, 0), bbox=bb)
        cv.fill(m, px.flat("#000000"), erase=True)
        hb.clean_specks(cv, 3)
    if p.mist is not None:
        fx = cv.layer(above=True, outline=True)
        hb.mist_puff(fx, C[0] - 2, C[1] - 1, p.mist, size=0.75, seed=3, count=3, spread=1.2)
        hb.mist_puff(fx, C[0] + 3, C[1] + 1, min(1.0, p.mist * 0.8), size=0.6, seed=7, count=2, spread=1.0)
    if p.speed:
        hb_lines = cv.layer(above=False, outline=False)
        px.speed_lines(hb_lines, C[0] - LENGTH * 0.55, C[1], length=5, count=2, spacing=4, color=hb.MIST.shadow)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, pts["mouth"][0] + 2, pts["mouth"][1] - 1, size=2)
