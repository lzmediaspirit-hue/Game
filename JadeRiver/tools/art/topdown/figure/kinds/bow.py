"""Bow: the spirit bow, a recurve wuxia bow, from a set's spec (sets/weapon_bow.py), after the side view's bow
(art/weapon_bow_*): gold limbs that curve back toward the string and flick forward again at the ears, a dark wrapped
grip and dark ear tips, and a string of pale jade light. It is carried slung across the back, the string across the
chest, and taken into the left hand to shoot: drawn, the string runs to the drawing hand with an arrow on it (a
jade-steel head, red fletching); loosed, it snaps back and hums, shown twice for a frame. Each piece lies in the band
its own depth puts it in (figure/weapons.py), so the limbs can pass behind the body and the string in front of it.

A pose says how it is held (`bow` in its weapon lines, figure/actions.py W):
  None / {}    the carry: slung across the back, the upper limb over the left shoulder, the lower at the right hip,
               the string drawn a little round the chest by the body inside it
  hand         "l" or "r": the hand that holds the grip (the bow is in a hand only when a pose says so)
  dir          the upper limb's direction (the figure's frame); `back` the way the bow's back faces (the string on the
               other side), by default the figure's forward
  draw         "r" (or "l"): the string drawn to that hand, the limbs bent deeper; `arrow` an arrow nocked on it
  loosed       the string just loosed: straight again and humming
The pose's `laid` lays it on the ground.

Spec keys:
  half   the grip to each tip           grip   the grip's half-length
  bend   the limbs' bend back at the ears, braced; `draw_bend` more when drawn, `draw_in` the tips drawn in along the axis
  ear    how far the ears flick forward, and where along the limb they start (a fraction)
  limb   the limb's radius at the grip and at the ear      string  the string's radius
  arrow  the arrow's length past the grip, its head's length
  sling  where the grip sits on the back and where the string crosses the chest (the chest's frame)
"""
from __future__ import annotations

import numpy as np

from ..body import HAND_R
from ..geom import unit
from ..raster import cone, ellipsoid, sphere
from ..weapons import band_of

UP = np.array([0.0, 0.0, 1.0])


def _frame(sk, wp: dict, spec: dict):
    """(grip point, upper limb's axis, the back's direction, the holding hand or None, the pose's bow, the point the
    string is drawn to or None)."""
    laid = wp.get("laid")
    b = dict(wp.get("bow") or {})
    if laid:
        a = unit(sk.w(laid["dir"]))
        back = unit(np.cross(a, UP))
        return sk.pt(laid["at"]) + UP * 0.2, a, back, None, b, None
    if "hand" not in b and "draw" not in b and "dir" not in b:
        # slung across the back: the grip behind the shoulder blades, the string round the front of the chest
        grip, cross = spec["sling"]
        g = sk.chest + sk.Mc @ np.array(grip)
        a = unit(sk.Mc @ np.array([0.0, -0.62, 0.78]))
        back = unit(-sk.Mc[:, 0])
        return g, a, back, None, b, sk.chest + sk.Mc @ np.array(cross)
    hand = sk.hand_l if b.get("hand", "l") == "l" else sk.hand_r
    a = unit(sk.w(b.get("dir", (0.3, -0.2, 1.0))))
    pull = None
    if b.get("draw"):
        # drawn: the back faces away from the drawing hand, square to the limbs
        pull = sk.hand_r if b["draw"] == "r" else sk.hand_l
        back = hand - pull
    else:
        back = sk.w(b.get("back", (1.0, 0.0, 0.0)))
    back = back - a * float(back @ a)
    back = unit(back) if float(np.linalg.norm(back)) > 1e-4 else unit(np.cross(a, UP))
    return hand, a, back, hand, b, pull


def _limb_point(g, a, back, spec, s: float, drawn: bool):
    """A point on the limbs' centre line, s from -1 (the lower ear) to 1 (the upper)."""
    half = spec["half"] * (1.0 - (spec["draw_in"] if drawn else 0.0) * abs(s) ** 2)
    bend = spec["bend"] + (spec["draw_bend"] if drawn else 0.0)
    ear, ear_at = spec["ear"]
    t = abs(s)
    off = -bend * t ** 1.7                                    # the limb bends back toward the string
    if t > ear_at:
        off += ear * ((t - ear_at) / (1.0 - ear_at)) ** 1.6   # and the ear flicks forward again
    return g + a * (s * half) + back * off


def solids(sk, spec: dict) -> list:
    wp = sk.weapon or {}
    g, a, back, hand, b, pull = _frame(sk, wp, spec)
    drawn = pull is not None
    S = []
    fist = HAND_R * 0.92
    # the limbs, piece by piece from the grip to each ear, tapering; the ears dark
    n = 7
    r0, r1 = spec["limb"]
    gh = spec["grip"] / spec["half"]
    ear_at = spec["ear"][1]
    for sgn in (-1.0, 1.0):
        ts = [gh * 0.6] + [gh * 0.6 + (1.0 - gh * 0.6) * (k + 1) / n for k in range(n)]
        for k in range(n):
            s0, s1 = ts[k], ts[k + 1]
            p0 = _limb_point(g, a, back, spec, sgn * s0, drawn)
            p1 = _limb_point(g, a, back, spec, sgn * s1, drawn)
            mat = "ear" if s0 >= ear_at - 1e-6 else "limb"
            ra = r0 + (r1 - r0) * s0
            rb = r0 + (r1 - r0) * s1
            S.append(cone(p0, p1, ra, rb, mat, k=0.8, side=back, band=band_of(sk, (p0 + p1) * 0.5), part="limb"))
            S.append(sphere(p1, rb, mat, band=band_of(sk, p1), part="limb"))
    # the grip: a dark wrap round the middle, the fist closed over it (what is inside the hand is left out)
    q0, q1 = g - a * spec["grip"], g + a * spec["grip"]
    M = np.stack([back, np.cross(a, back), a], axis=1)
    clip = None if hand is None else (lambda loc: np.linalg.norm(q0 + loc @ M.T - hand, axis=1) > fist)
    S.append(cone(q0, q1, r0 + 0.12, r0 + 0.12, "grip", band=band_of(sk, g), part="grip", clip=clip, frame=(q0, M)))
    # the string: tip to tip, or round to where it is drawn
    top = _limb_point(g, a, back, spec, 1.0, drawn)
    bot = _limb_point(g, a, back, spec, -1.0, drawn)
    rs = spec["string"]
    mids = [pull] if drawn else [(top + bot) * 0.5]
    if b.get("loosed"):
        mids.append(mids[0] + back * 0.9)                     # the string humming: shown twice for a frame
    for mid in mids:
        for p0, p1 in ((top, mid), (mid, bot)):
            m = 4
            for k in range(m):
                c0 = p0 + (p1 - p0) * (k / m)
                c1 = p0 + (p1 - p0) * ((k + 1) / m)
                S.append(cone(c0, c1, rs, rs, "string", band=band_of(sk, (c0 + c1) * 0.5), part="string"))
    # the arrow on the string: from the nock through the grip and on past it
    if drawn and b.get("arrow"):
        d = unit(g - pull)
        L, head = spec["arrow"]
        tail = pull - d * 0.4
        tip = g + d * L
        k = 3
        span = float(np.linalg.norm(tip - tail)) - head
        for j in range(k):
            c0 = tail + d * (span * j / k)
            c1 = tail + d * (span * (j + 1) / k)
            S.append(cone(c0, c1, 0.34, 0.34, "shaft", band=band_of(sk, (c0 + c1) * 0.5), part="arrow"))
        h0 = tail + d * span
        S.append(cone(h0, tip, 0.62, 0.12, "head", band=band_of(sk, (h0 + tip) * 0.5), part="head"))
        # the fletching: two red vanes just ahead of the nock
        side = unit(np.cross(d, UP)) if abs(float(d @ UP)) < 0.95 else unit(np.cross(d, back))
        for sg in (-1.0, 1.0):
            f0 = tail + d * 0.5 + side * sg * 0.45
            S.append(ellipsoid(f0 + d * 0.9, np.stack([d, side, np.cross(d, side)], axis=1), (1.3, 0.45, 0.3),
                               "fletch", band=band_of(sk, f0), part="fletch"))
    return S
