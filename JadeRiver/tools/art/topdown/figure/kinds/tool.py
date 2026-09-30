"""Tool: what a villager at work holds (decision 44), cast from the same skeleton as the body, so it is in the hands on
every frame of its action and facing (the held-tool rig). A pose says where each tool goes in its weapon lines,
`tools` (figure/work.py; the idle and walk poses carry some, actions.CARRY): a tool the pose does not name draws
nothing, and the build writes an explicit hidden entry for it (build_character.py).

Each tool is fitted to the hands the pose put on it: a handle runs through both fists (or along the one fist's line),
and what it holds at its other end (the broom's bristles, the axe's head, the rod's line) follows. Where a handle
passes through a fist it is cut away (`_grip`), so the fist closes over it. Pieces lie in the band their own depth
puts them in (figure/weapons.py band_of), as a weapon's do; a long tool held out is lengthened along the ground's
depth as a weapon is (weapons.stretch), and what stands on the ground (the anvil, the mortar, the net's heap) is not.

  broom   a bamboo broom, a fan of twigs bound to its foot; in the sweep its bristles are pressed to the ground (they
          splay on the push), carried upright in the right hand when idle or walking
  pole    a carrying pole on the right shoulder, bowing under two baskets of grain hung on cords
  washing the laundry basket on the shoulder (work_carry) or a cloth held up and laid over a line (work_hang)
  rod     a bamboo rod with its line and a red float: held out, cast, or carried upright with the line wound
  ladle   a clay pot on the left forearm and a ladle stirring in it
  pestle  a stone mortar on the ground and a wooden pestle in the right fist
  axe     an iron axe head on a long haft in both fists; carried hanging from the right hand
  hammer  a smith's hammer, an anvil on its stump before the feet, the tongs in the left hand holding a hot bar on it
  herbs   a herb basket on the left arm, a sprig in the right hand as it is picked; carried hanging from the left hand
  net     a fishing net over the seated lap, its mesh held up in the left hand, a netting needle in the right
"""
from __future__ import annotations

import math

import numpy as np

from ..body import HAND_R
from ..geom import unit
from ..raster import cone, ellipsoid, sphere
from ..weapons import band_of, pole_line, stretch

UP = np.array([0.0, 0.0, 1.0])
FIST = HAND_R + 0.05
Z0 = np.zeros(0)


def ground_band(sk, p) -> str:
    """The band of a thing standing on the ground (the anvil, the mortar, a basket set down, the net's heap): in front of
    the body when it stands nearer the camera on the ground than the chest does, else behind. (`band_of` weighs height
    too, so a low thing before a standing body would rank behind it and a knee would cover it.)"""
    return "front" if float(p[1]) >= float(sk.chest[1]) - 0.4 else "back"


def _paint(fn):
    """A paint from a function of the solid's local point to material names (no bias)."""
    return lambda loc, P, nn: (np.asarray(fn(loc), dtype=object), np.zeros(len(loc), dtype=np.int16))


def _grip(sk, hands):
    """A clip that cuts a handle away inside the fists holding it (world points), so the fist shows over it."""
    hs = [np.asarray(h, float) for h in hands]

    def clip_at(o, M):
        def clip(loc):
            P = o + loc @ M.T
            keep = np.ones(len(loc), dtype=bool)
            for h in hs:
                keep &= np.linalg.norm(P - h, axis=1) > FIST
            return keep
        return clip
    return clip_at


def _rod_piece(sk, a, b, r0, r1, mat, part, hands=(), side=None, k=1.0, paint=None):
    """A piece of a handle from a to b, cut away inside the fists that hold it."""
    s = cone(a, b, r0, r1, mat, k=k, side=side, band=band_of(sk, (a + b) * 0.5), part=part, paint=paint)
    if hands:
        o, M = s.geo["c"], s.geo["M"]
        s.clip = _grip(sk, hands)(o, M)
        s.frame = (o, M)
    return s


def _line_pieces(sk, pts, r, mat, part):
    out = []
    for p0, p1 in zip(pts[:-1], pts[1:]):
        if float(np.linalg.norm(p1 - p0)) < 1e-4:
            continue
        out.append(cone(p0, p1, r, r, mat, band=band_of(sk, (p0 + p1) * 0.5), part=part))
    return out


def _handle(sk, a, b, r, mat, part, hands, n=6, **kw):
    """A handle from a to b in n pieces (each in its own band), cut inside the fists."""
    out = []
    for i in range(n):
        p0 = a + (b - a) * (i / n)
        p1 = a + (b - a) * ((i + 1) / n)
        out.append(_rod_piece(sk, p0, p1, r, r, mat, part, hands, **kw))
    return out


# ------------------------------------------------------------------ the broom
BROOM = {"length": 22.0, "top": 1.3, "handle": 15.0, "bristles": 7.0, "splay": (0.9, 3.1)}


def broom(sk, t: dict, spec=BROOM) -> list:
    if t.get("carry"):
        # upright in the right hand along the pose's pole line, the bristles down by the feet
        d, _ = pole_line(sk)
        g = sk.hand_r
        tip = g - d * 12.6
        top_end = tip + d * spec["length"]
        return _broom_solids(sk, top_end, d, tip, (g,), 0.0)
    hl, hr = sk.hand_l, sk.hand_r
    d = unit(hr - hl)
    top = hl - d * spec["top"]
    # the bristles' tips at the ground (or lifted as the pose says): the bristles splay or gather to meet it
    want = float(t.get("lift", 0.0)) + 0.35
    s = spec["handle"] + spec["bristles"]
    if d[2] < -0.2:
        s = (want - float(top[2])) / float(d[2])
    s = min(max(s, spec["handle"] + spec["bristles"] - 2.5), spec["handle"] + spec["bristles"] + 2.5)
    return _broom_solids(sk, top, d, top + d * s, (hl, hr), float(t.get("press", 0.0)), grip=hr)


def _broom_solids(sk, top, d, tip, hands, press, grip=None, spec=BROOM):
    g = hands[-1] if grip is None else grip
    top_s, tip_s = stretch(sk, g, top), stretch(sk, g, tip)
    L = float(np.linalg.norm(tip_s - top_s))
    dd = unit(tip_s - top_s)
    foot = top_s + dd * min(spec["handle"], L - 4.0)
    S = _handle(sk, top_s, foot, 0.42, "bamboo", "handle", hands, n=5)
    S.append(sphere(top_s, 0.45, "bamboo", band=band_of(sk, top_s), part="handle"))
    # the binding, then the fan of twigs, broad across the sweep and pressed wider on the push
    side = unit(np.cross(dd, UP)) if abs(float(dd[2])) < 0.97 else np.array([1.0, 0.0, 0.0])
    S.append(cone(foot - dd * 0.4, foot + dd * 0.9, 0.62, 0.72, "cord", band=band_of(sk, foot), part="bind"))
    r0, r1 = spec["splay"]
    r1 += 0.9 * press
    tip_s2 = tip_s + side * 0.0
    S.append(cone(foot + dd * 0.5, tip_s2, r0, r1, "twig", k=0.34, side=side, band=band_of(sk, (foot + tip_s2) * 0.5),
                  part="twigs",
                  paint=_paint(lambda loc: np.where((np.floor(loc[:, 0] * 1.6) % 2) == 0, "twig", "twig_dark"))))
    return S


# ------------------------------------------------------------------ the shoulder pole and its baskets
POLE = {"fore": 16.0, "aft": 15.0, "drop": 9.2, "basket": (3.0, 2.5, 3.6)}


def _shoulder(sk):
    """Where a load rides on the right shoulder, and the line along the pole through the right fist."""
    c = sk.shoulder_r + sk.up * 1.75
    d = sk.hand_r + sk.up * 0.75 - c
    d = d - sk.right * float(d @ sk.right) * 0.7        # the pole keeps along the body, not across it
    return c, unit(d)


def pole(sk, t: dict, spec=POLE) -> list:
    c, d = _shoulder(sk)
    bow = float(t.get("bow", 0.5))
    bob = float(t.get("bob", 0.0))
    g = sk.hand_r
    pts = []
    n = 10
    for i in range(n + 1):
        s = -spec["aft"] + (spec["fore"] + spec["aft"]) * i / n
        sag = bow * (abs(s) / spec["fore"]) ** 2 * 1.4
        pts.append(stretch(sk, g, c + d * s - UP * sag))
    S = []
    for p0, p1 in zip(pts[:-1], pts[1:]):
        S.append(_rod_piece(sk, p0, p1, 0.5, 0.5, "bamboo", "pole", (sk.hand_r, sk.hand_l), k=0.7,
                            side=np.cross(unit(p1 - p0), UP)))
    for end in (pts[0], pts[-1]):
        S += _hung_basket(sk, end, spec["drop"] - bob, spec["basket"], "grain")
    return S


def _hung_basket(sk, hook, drop, dims, load):
    """A basket hung from `hook` on three cords, its rim `drop` below, round and tapering to its foot, heaped with its
    load."""
    r_top, r_foot, h = dims
    rim = hook - UP * drop
    S = []
    side = np.cross(sk.fwd, UP)
    side = unit(side) if float(np.linalg.norm(side)) > 1e-6 else np.array([1.0, 0.0, 0.0])
    fw = unit(np.cross(UP, side))
    for k in range(3):
        a = math.radians(90.0 + 120.0 * k)
        p = rim + (side * math.cos(a) + fw * math.sin(a)) * (r_top - 0.3)
        S += _line_pieces(sk, [hook, hook + (p - hook) * 0.5, p], 0.2, "cord", "cords")
    S += _basket(sk, rim, r_top, r_foot, h, load)
    return S


def _basket(sk, rim, r_top, r_foot, h, load, grounded=False):
    """A round wicker basket, its rim at `rim`, heaped with its load; all in one band (a basket set on the ground in
    the band its place on the ground puts it in)."""
    foot = rim - UP * h
    bd = ground_band(sk, foot) if grounded else band_of(sk, rim)
    S = [cone(foot, rim, r_foot, r_top, "wicker", band=bd, part="basket",
              paint=_paint(lambda loc: np.where((np.floor(loc[:, 2] * 1.25) % 2) == 0, "wicker", "wicker_dark"))),
         cone(rim - UP * 0.35, rim + UP * 0.25, r_top + 0.2, r_top + 0.25, "rim", band=bd, part="rim")]
    if load == "grain":
        S.append(ellipsoid(rim + UP * 0.2, np.eye(3), (r_top - 0.25, r_top - 0.25, 1.2), "grain", band=bd, part="load"))
    elif load == "herbs":
        S.append(ellipsoid(rim + UP * 0.2, np.eye(3), (r_top - 0.2, r_top - 0.2, 1.0), "herb", band=bd, part="load"))
        for k in range(3):
            a = math.radians(40.0 + 120.0 * k)
            p = rim + np.array([math.cos(a), math.sin(a), 0.0]) * (r_top * 0.45) + UP * 1.0
            S.append(sphere(p, 0.65, "herb_light", band=bd, part="load"))
    elif load == "washing":
        for k, (dx, dy, m) in enumerate(((-0.8, 0.4, "linen"), (0.9, -0.3, "cloth_blue"), (0.1, -0.9, "linen"))):
            p = rim + np.array([dx, dy, 0.0]) + UP * (0.5 + 0.2 * k)
            S.append(ellipsoid(p, np.eye(3), (r_top * 0.55, r_top * 0.45, 0.8), m, band=bd, part="load"))
    return S


# ------------------------------------------------------------------ the washing
WASH = {"basket": (3.4, 2.8, 2.6)}


def washing(sk, t: dict, spec=WASH) -> list:
    if t.get("basket"):
        # the laundry basket riding on the right shoulder, steadied by both hands at its front
        c, d = _shoulder(sk)
        r_top, r_foot, h = spec["basket"]
        rim = c + UP * (h - 0.4 + float(t.get("bob", 0.0)) * 0.3) + sk.right * 0.6 + d * 0.4
        return _basket(sk, rim, r_top, r_foot, h, "washing")
    hl, hr = sk.hand_l, sk.hand_r
    across = hr - hl
    w = float(np.linalg.norm(across))
    x = unit(across) if w > 1e-3 else sk.right
    hang = float(t.get("hang", 5.0))
    shake = float(t.get("shake", 0.0))
    top = (hl + hr) * 0.5 - UP * 0.5
    if t.get("over"):
        # laid over the line: a short fall before it and a longer one behind
        S = [_cloth(sk, top, x, w, hang * 0.6, 0.0, "linen", "cloth", toward=sk.fwd * 0.4),
             _cloth(sk, top + sk.fwd * 0.6, x, w, hang * 1.3, 0.0, "linen", "cloth_back", toward=sk.fwd * 0.2)]
        return S
    return [_cloth(sk, top, x, w, hang, shake, "linen", "cloth", toward=sk.fwd * 0.6)]


def _cloth(sk, top, x, w, hang, shake, mat, part, toward):
    """A cloth held by its top edge (along x, `w` wide), falling `hang` below it; shaken, its foot swings aside."""
    foot = top - UP * hang + x * shake * 1.2 + toward
    s = cone(top, foot, w * 0.5 + 0.3, w * 0.5 + 0.7, mat, k=0.14, side=x, band=band_of(sk, (top + foot) * 0.5),
             part=part,
             paint=_paint(lambda loc: np.where(np.abs(loc[:, 2] - hang * 0.78) < 0.45, "cloth_blue",
                                               np.where((np.floor(loc[:, 0] * 0.9) % 3) == 0, "linen_fold", "linen"))))
    return s


# ------------------------------------------------------------------ the rod
ROD = {"length": 30.0, "butt": 4.6}


def rod(sk, t: dict, spec=ROD) -> list:
    if t.get("carry"):
        d, _ = pole_line(sk)
        g = sk.hand_r
        butt = g - d * 3.0
        tip_line = {"to": None}
        return _rod_solids(sk, butt, d, g, (g,), -1.4, tip_line, wound=True)
    # along the pose's own line through the front (right) fist, the butt past the left
    hr = sk.hand_r
    d = unit(sk.w(t["dir"]))
    butt = hr - d * spec["butt"]
    return _rod_solids(sk, butt, d, hr, (sk.hand_l, hr), float(t.get("nod", 0.0)), t.get("line") or {}, wound=False)


def _rod_solids(sk, butt, d, g, hands, nod, line, wound, spec=ROD):
    L = spec["length"]
    n = 8
    side = unit(np.cross(d, UP)) if abs(float(d[2])) < 0.97 else np.array([1.0, 0.0, 0.0])
    bend_dir = unit(np.cross(side, d))            # the way the tip bows (down for a rod held out)
    if float(bend_dir[2]) > 0:
        bend_dir = -bend_dir
    pts = []
    for i in range(n + 1):
        s = i / n
        p = butt + d * (L * s) + bend_dir * (nod + 0.9) * s * s
        pts.append(stretch(sk, g, p))
    S = []
    for i, (p0, p1) in enumerate(zip(pts[:-1], pts[1:])):
        r0 = 0.55 - 0.3 * i / n
        r1 = 0.55 - 0.3 * (i + 1) / n
        S.append(_rod_piece(sk, p0, p1, r0, r1, "bamboo" if i else "grip", "rod", hands))
    tip = pts[-1]
    if wound:
        # carried: the line wound short, the float hanging below the tip
        f = tip - UP * 2.4
        S += _line_pieces(sk, [tip, f], 0.2, "line", "line")
        S.append(sphere(f - UP * 0.4, 0.5, "float", band=band_of(sk, f), part="float"))
        return S
    to = line.get("to")
    if to is None:
        return S
    end = stretch(sk, g, sk.pt(to))
    sag = float(line.get("sag", 0.5))
    m = 10
    lp = []
    for k in range(m + 1):
        u = k / m
        p = tip + (end - tip) * u
        lp.append(p - UP * sag * 4.0 * u * (1 - u) * 2.0)
    S += _line_pieces(sk, lp, 0.2, "line", "line")
    if float(end[2]) < 0.5:
        S.append(sphere(end + UP * 0.25, 0.55, "float", band=band_of(sk, end), part="float"))
    return S


# ------------------------------------------------------------------ the ladle and pot
def ladle(sk, t: dict) -> list:
    P = sk.pt(t["pot"])
    S = [ellipsoid(P, np.eye(3), (3.3, 3.3, 2.3), "clay", band=band_of(sk, P), part="pot",
                   clip=lambda loc: loc[:, 2] < 1.3, frame=(P, np.eye(3))),
         cone(P + UP * 1.0, P + UP * 1.9, 2.8, 2.95, "clay_rim", band=band_of(sk, P), part="rim"),
         ellipsoid(P + UP * 1.5, np.eye(3), (2.55, 2.55, 0.18), "broth", band=band_of(sk, P), part="broth")]
    # two lugs either side
    side = unit(np.cross(sk.fwd, UP))
    for sg in (-1.0, 1.0):
        q = P + side * sg * 3.4 + UP * 1.0
        S.append(sphere(q, 0.5, "clay_rim", band=band_of(sk, q), part="lug"))
    bowl = sk.pt(t["bowl"])
    hand = sk.hand_r
    d = unit(hand - bowl)
    end = hand + d * 1.6
    S += _handle(sk, bowl + d * 0.6, end, 0.34, "haft", "ladle", (hand,), n=4)
    S.append(sphere(bowl, 1.05, "iron", band=band_of(sk, bowl), part="bowl"))
    return S


# ------------------------------------------------------------------ the pestle and mortar
def pestle(sk, t: dict) -> list:
    M = sk.pt(t["mortar"])
    S = [cone(M, M + UP * 3.4, 2.8, 3.3, "stone", band=ground_band(sk, M), part="mortar"),
         cone(M + UP * 3.1, M + UP * 3.8, 3.45, 3.5, "stone_rim", band=ground_band(sk, M), part="rim"),
         ellipsoid(M + UP * 3.85, np.eye(3), (2.6, 2.6, 0.15), "hollow", band=ground_band(sk, M), part="hollow")]
    hand = sk.hand_r
    d = unit(sk.w(t.get("tilt", (0.0, 0.0, 1.0))))
    bottom = hand - d * 5.2
    if t.get("down"):
        bottom = M + UP * 1.6 + (hand - M) * np.array([1.0, 1.0, 0.0]) * 0.15
        d = unit(hand - bottom)
    top = hand + d * 1.3
    S += _handle(sk, bottom + d * 1.2, top, 0.45, "haft", "pestle", (hand,), n=4)
    S.append(ellipsoid(bottom + d * 0.6, np.stack([unit(np.cross(d, sk.right)), sk.right, d], axis=1) if abs(float(d @ sk.right)) < 0.95 else np.eye(3),
                       (0.8, 0.8, 1.0), "haft", band=band_of(sk, bottom), part="pestle_head"))
    return S


# ------------------------------------------------------------------ the axe
AXE = {"haft": 16.0, "butt": 1.0}


def axe(sk, t: dict, spec=AXE) -> list:
    if t.get("carry"):
        # hanging from the right hand along the pose's blade line, the head down by the knee
        wp = sk.weapon or {}
        d = unit(sk.w(wp.get("blade", (0.35, 0.3, -1.0))))
        d = unit(d * np.array([0.6, 0.6, 1.0]) - UP * 0.8)
        g = sk.hand_r
        butt = g - d * 2.0
        return _axe_solids(sk, butt, d, g, (g,), spec, carry=True)
    hl, hr = sk.hand_l, sk.hand_r
    d = unit(hr - hl) if float(np.linalg.norm(hr - hl)) > 1.0 else unit(sk.w(t["haft"]))
    butt = hl - d * spec["butt"]
    return _axe_solids(sk, butt, d, hr, (hl, hr), spec)


def _axe_solids(sk, butt, d, g, hands, spec, carry=False):
    L = spec["haft"]
    head = butt + d * (L - 0.9)
    # the edge leads the swing: square to the haft in the figure's upright plane (the chop's plane)
    e = np.cross(sk.right, d)
    if float(np.linalg.norm(e)) < 1e-3:
        e = sk.fwd
    e = unit(e)
    if carry:
        e = unit(sk.fwd - d * float(sk.fwd @ d))
    bs, hs = stretch(sk, g, butt), stretch(sk, g, butt + d * (L + 0.5))
    S = _handle(sk, bs, hs, 0.45, "haft", "haft", hands, n=6)
    hd = stretch(sk, g, head)
    edge = stretch(sk, g, head + e * 3.1)
    poll = stretch(sk, g, head - e * 1.1)
    S.append(cone(hd, edge, 0.95, 2.0, "iron", k=0.36, side=d, band=band_of(sk, (hd + edge) * 0.5), part="head",
                  paint=_paint(lambda loc: np.where(loc[:, 2] > 2.45, "edge", "iron"))))
    S.append(cone(poll, hd, 0.8, 0.95, "iron", k=0.7, side=d, band=band_of(sk, hd), part="head"))
    return S


# ------------------------------------------------------------------ the hammer and anvil
def hammer(sk, t: dict) -> list:
    A = sk.pt(t["anvil"])
    hand = sk.hand_r
    d = unit(sk.w(t["dir"]))
    S = []
    # the anvil: an iron block with its horn on a wooden stump
    S.append(cone(A, A + UP * 7.4, 2.3, 2.0, "log", band=ground_band(sk, A), part="stump",
                  paint=_paint(lambda loc: np.where((np.floor(loc[:, 2] * 0.8) % 3) == 0, "log_dark", "log"))))
    top = A + UP * 8.2
    x = unit(sk.w((0.0, -1.0, 0.0)))
    S.append(ellipsoid(top, np.stack([x, unit(np.cross(UP, x)), UP], axis=1), (2.5, 1.3, 0.85), "iron",
                       band=ground_band(sk, A), part="anvil"))
    S.append(cone(top + x * 2.0, top + x * 4.2, 0.8, 0.2, "iron", band=ground_band(sk, A), part="horn"))
    S.append(cone(top - x * 1.8, top - x * 2.6, 0.9, 0.8, "iron", band=ground_band(sk, A), part="heel"))
    # the hot bar on the anvil's face, held by the tongs from the left hand
    bar0 = top + UP * 0.95 - x * 0.2
    bar1 = bar0 + x * (2.2 if not t.get("turn") else 2.0) + sk.fwd * (0.0 if not t.get("turn") else 0.4)
    S.append(cone(bar0, bar1, 0.34, 0.3, "hot", band=ground_band(sk, A), part="bar"))
    hl = sk.hand_l
    for sg in (-1.0, 1.0):
        j = bar1 + UP * 0.25 * sg
        S += _line_pieces(sk, [hl + UP * 0.2 * sg, (hl + j) * 0.5 + UP * 0.35 * sg, j], 0.22, "tongs", "tongs")
    # the hammer: a short haft through the fist, an iron head square to it, its face leading the blow
    head_c = hand + d * 5.8
    S += _handle(sk, hand - d * 0.9, head_c + d * 0.3, 0.36, "haft", "haft", (hand,), n=4)
    a = np.cross(sk.right, d)
    a = unit(a) if float(np.linalg.norm(a)) > 1e-3 else sk.fwd
    S.append(cone(head_c - a * 1.2, head_c + a * 1.5, 0.85, 0.85, "iron", band=band_of(sk, head_c), part="hammer",
                  paint=_paint(lambda loc: np.where(loc[:, 2] > 2.35, "edge", "iron"))))
    return S


# ------------------------------------------------------------------ the herb basket
HERBS = {"basket": (2.6, 2.1, 2.4)}


def herbs(sk, t: dict, spec=HERBS) -> list:
    r_top, r_foot, h = spec["basket"]
    side = unit(np.cross(sk.fwd, UP))
    if t.get("carry"):
        # hanging from the left hand by its handle
        grip = sk.hand_l
        rim = grip - UP * 2.4
    else:
        # on the ground before the feet, its handle standing up
        rim = sk.pt(t["basket"]) + UP * h
        grip = rim + UP * 2.4
    S = _basket(sk, rim, r_top, r_foot, h, "herbs", grounded=not t.get("carry"))
    arc = [rim + side * r_top, rim + side * r_top * 0.7 + UP * 1.8, grip + UP * 0.3, rim - side * r_top * 0.7 + UP * 1.8,
           rim - side * r_top]
    S += _line_pieces(sk, arc, 0.24, "wicker", "handle")
    if t.get("sprig"):
        g = sk.hand_r
        S.append(cone(g - UP * 0.3, g + UP * 1.8 + sk.fwd * 0.4, 0.25, 0.2, "herb", band=band_of(sk, g), part="sprig"))
        S.append(ellipsoid(g + UP * 2.0 + sk.fwd * 0.4, np.eye(3), (0.9, 0.9, 0.6), "herb_light", band=band_of(sk, g),
                           part="sprig"))
    return S


# ------------------------------------------------------------------ the net
def net(sk, t: dict) -> list:
    hl, hr = sk.hand_l, sk.hand_r
    lap = sk.pt((3.4, 0.0, 5.0))
    heap = sk.pt((7.2, 0.4, 0.6))
    held = hl - UP * 0.9
    # a diamond mesh: pale twine lines about a pixel wide, the shade of the heap through the holes between them
    mesh = _paint(lambda loc: np.where((np.mod((loc[:, 0] + loc[:, 1]) * 0.45, 1.0) < 0.42)
                                       | (np.mod((loc[:, 0] - loc[:, 1]) * 0.45, 1.0) < 0.42), "twine", "mesh"))
    Mf = np.stack([sk.fwd, sk.right, UP], axis=1)
    S = [cone(held, lap + sk.fwd * 1.6, 0.9, 2.6, "twine", k=0.35, side=sk.right, band=band_of(sk, held), part="drape",
              paint=mesh),
         ellipsoid(lap + sk.fwd * 0.6, Mf, (2.8, 4.4, 0.9), "twine", band=ground_band(sk, lap), part="lap", paint=mesh,
                   frame=(lap, Mf)),
         ellipsoid(heap, Mf, (3.4, 4.6, 0.9), "twine", band=ground_band(sk, heap), part="heap", paint=mesh, frame=(heap, Mf))]
    # the corks along its head rope, over the heap
    for k in range(3):
        p = heap + sk.right * (-2.6 + 2.6 * k) + sk.fwd * 2.8 + UP * 0.5
        S.append(sphere(p, 0.5, "cork", band=band_of(sk, p), part="cork"))
    # the netting needle in the right fist, and the twine drawn from the mesh to it
    i = int(t.get("needle", 0))
    nd = unit(sk.fwd * 0.6 + sk.right * 0.7 + UP * 0.4)
    S.append(cone(hr - nd * 0.4, hr + nd * 2.2, 0.35, 0.18, "shuttle", k=0.5, side=UP, band=band_of(sk, hr), part="needle"))
    if i in (1, 2):
        S += _line_pieces(sk, [held + UP * 0.4, hr], 0.18, "line", "twine_drawn")
    return S


GENERATORS = {"broom": broom, "pole": pole, "washing": washing, "rod": rod, "ladle": ladle, "pestle": pestle, "axe": axe,
              "hammer": hammer, "herbs": herbs, "net": net}


def solids(sk, name: str) -> list:
    """The tool `name` as the pose holds it, or nothing where the pose does not name it."""
    t = ((sk.weapon or {}).get("tools") or {}).get(name)
    if t is None:
        return []
    return GENERATORS[name](sk, t)
