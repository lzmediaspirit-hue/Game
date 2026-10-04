"""Fan: a folding war fan held in the right hand along the pose's `blade` line (or laid on the ground), from a set's
spec (sets/weapon_fan.py), after the side view's iron fan (the side view's weapon bake `fan_frame`): brown ribs gathered
at a gold rivet under the fist and a pleated paper leaf with a band of teal ink along its rim.

It opens in the blows the spec names (`open`) and folds at rest, as the side view opens it in the strikes. A pose
carries no action name, so the fan finds its action by the pose's content (`frame_of`).

  folded  a slim bar of stacked ribs and paper, brown at the handle and the tip, stretched along the ground's depth
          as a blade is (figure/weapons.py);
  open    a sector of a thin disc about the rivet: the ribs brown near the rivet, then the paper, every other pleat a
          tone darker, the ink band in the middle of the rim, a guard stick along each side. It shows its face: it is
          turned at least `least` degrees off the camera's line (keeping its direction on screen) and its leaf faces
          the camera, tilted a little (`turn`) with the pose's flat so it catches the light as it sweeps. A cut
          (`smear_from` in the pose) leaves a smear of pale jade light behind the leaf's trailing edge.
  thrown  nothing: from the throw's release the fan is in flight (`fan_throw`), drawn by the throw's own art.

Spec keys:
  length  the ribs' length from the rivet    rivet   how far the rivet sits behind the grip
  spread  the open leaf's half-angle, degrees             leaf    where the paper starts, a fraction of the length
  pleats  the open leaf's pleats             band    the ink band: (inner radius, half-width across), fractions
  thick   the open leaf's thickness          least   the open fan's least angle off the camera's line, degrees
  turn    how far the open leaf tilts with the pose's flat (0: face on to the camera)
  width   the folded fan's half-width at the rivet and at the tip
  open    {action: [frames]} the fan is open in       thrown  {action: [frames]} it is out of the hand in
"""
from __future__ import annotations

import json
import math

import numpy as np

from .. import actions as A
from ..geom import LIGHT, SCR_D, TOWARD, unit
from ..raster import THRESH, cone, ellipsoid, sphere
from ..weapons import band_of, blade_line, flat_frame, stretch

_FRAMES: dict | None = None
UP = np.array([0.0, 0.0, 1.0])


def frame_of(p: dict) -> list:
    """Every (action, frame) of figure/actions.py CATALOG whose pose is `p`: a pose carries no name, so it is found by
    its content (the build casts the catalogue's own poses)."""
    global _FRAMES
    if _FRAMES is None:
        _FRAMES = {}
        for name in A.CATALOG:
            for i, q in enumerate(A.poses(name)):
                _FRAMES.setdefault(json.dumps(q, sort_keys=True), []).append((name, i))
    return _FRAMES.get(json.dumps(p, sort_keys=True), [])


def is_thrown(sk, spec: dict) -> bool:
    return any(i in spec.get("thrown", {}).get(name, ()) for name, i in frame_of(sk.p))


def is_open(sk, spec: dict) -> bool:
    if (sk.weapon or {}).get("laid"):
        return False
    return any(i in spec["open"].get(name, ()) for name, i in frame_of(sk.p))


def off_camera(d, least: float):
    """`d` turned away from the camera's line until it is at least `least` degrees off it, keeping its direction on
    screen. A fan pointed at the camera (or away) would show only its rim."""
    c = float(d @ TOWARD)
    lim = math.cos(math.radians(least))
    if abs(c) <= lim:
        return d
    u = d - TOWARD * c
    u = unit(u) if float(np.linalg.norm(u)) > 1e-6 else SCR_D
    return unit(TOWARD * math.copysign(lim, c) + u * math.sin(math.radians(least)))


def through_paper(nn) -> np.ndarray:
    """The tone bias that lights a thin sheet from either side: where its face turns from the light it takes the tone
    its other face would have (paper lit through), and it never falls below its base tone."""
    s = nn @ LIGHT
    lit = sum((np.abs(s) >= th).astype(np.int16) for th in THRESH)
    now = sum((s >= th).astype(np.int16) for th in THRESH)
    return (np.maximum(lit, 1) - now).astype(np.int16)


def sweep(d0, d, up, t: float):
    """The direction a fraction t of the way along a swing from d0 to d: round the shorter arc, or over `up` (the
    figure's up, a chop over the head) when the two are nearly opposite."""
    def slerp(a, b, u):
        w = math.acos(max(-1.0, min(1.0, float(a @ b))))
        if w < 1e-4:
            return a
        return unit(a * math.sin((1 - u) * w) + b * math.sin(u * w))
    if float(d0 @ d) > -0.85:
        return slerp(d0, d, t)
    k = unit(d - d0)
    m = unit(up - k * float(up @ k))
    return slerp(d0, m, t * 2) if t < 0.5 else slerp(m, d, t * 2 - 1)


def leaf_frame(d, flat, turn: float):
    """The open leaf's spread axis x (in its plane, across d) and its normal n: face on to the camera, tilted by `turn`
    toward the plane the pose's flat gives."""
    n_cam = TOWARD - d * float(TOWARD @ d)
    if float(np.linalg.norm(n_cam)) < 0.25:
        n_cam = UP - d * float(UP @ d)
    n_cam = unit(n_cam)
    n_pose = unit(np.cross(d, flat_frame(d, flat)))
    if float(n_pose @ n_cam) < 0:
        n_pose = -n_pose
    n = unit(n_cam + n_pose * turn)
    return unit(np.cross(n, d)), n


def _folded(sk, spec, g, d, flat, laid) -> list:
    """The ribs and paper stacked in a slim bar, wider in the leaf's plane than through it: brown at the handle (the
    guard sticks round the ribs) and at the tip, the paper's folded edge between."""
    L = spec["length"]
    piv = g - d * spec["rivet"]

    def at(k):
        return stretch(sk, g, piv + d * k)
    x = unit(np.cross(d, UP)) if laid else leaf_frame(d, flat, spec["turn"])[0]
    w0, w1 = spec["width"]
    S = [sphere(at(0.0), 0.5, "gold", band=band_of(sk, at(0.0)), part="rivet")]
    n = 3
    for i in range(n):
        a, b = at(L * i / n), at(L * (i + 1) / n)
        seg = float(np.linalg.norm(b - a))

        def paint(loc, P, nn, i=i, seg=seg):
            t = (i + loc[:, 2] / max(seg, 1e-6)) / n
            return (np.where((t < spec["leaf"] * 0.8) | (t > 0.93), "rib", "paper").astype(object),
                    np.zeros(len(loc), dtype=np.int16))
        S.append(cone(a, b, w0 + (w1 - w0) * i / n, w0 + (w1 - w0) * (i + 1) / n, "paper", k=0.6, side=x,
                      band=band_of(sk, (a + b) * 0.5), part="folded", paint=paint))
    return S


def solids(sk, spec: dict) -> list:
    if is_thrown(sk, spec):
        return []
    g, d, flat = blade_line(sk)
    wp = sk.weapon or {}
    if not is_open(sk, spec):
        return _folded(sk, spec, g, d, flat, bool(wp.get("laid")))
    S = []
    L = spec["length"]
    d = off_camera(d, spec["least"])
    piv = g - d * spec["rivet"]
    x, nrm = leaf_frame(d, flat, spec["turn"])
    Q = np.stack([d, x, nrm], axis=1)
    half = math.radians(spec["spread"])
    leaf0 = spec["leaf"] * L
    b_in, b_w = spec["band"]
    pleats = spec["pleats"]

    def paint(loc, P, nn):
        r = np.hypot(loc[:, 0], loc[:, 1])
        t = (np.arctan2(loc[:, 1], loc[:, 0]) + half) / (2 * half)     # across the leaf, 0 to 1
        k = np.floor(np.clip(t, 0.0, 0.999) * pleats).astype(int)
        names = np.where(r < leaf0, "rib", "paper").astype(object)
        names = np.where((r >= L * b_in) & (np.abs(t - 0.5) <= b_w), "fan_ink", names)
        return names, np.where((r >= leaf0) & (k % 2 == 1), -1, 0).astype(np.int16) + through_paper(nn)
    # The leaf in two halves along its centre line, so each lies in its own band.
    for sgn in (-1.0, 1.0):
        mid = piv + (d * math.cos(half * 0.5) + x * sgn * math.sin(half * 0.5)) * L * 0.6

        def clip(loc, sgn=sgn):
            return (np.abs(np.arctan2(loc[:, 1], loc[:, 0])) <= half) & (loc[:, 1] * sgn >= -0.05)
        S.append(ellipsoid(piv, Q, (L, L, spec["thick"]), "paper", band=band_of(sk, mid), part="leaf", clip=clip,
                           paint=paint))
    # The guard sticks, the heavy outer ribs, along the leaf's two edges.
    for sgn in (-1.0, 1.0):
        e = d * math.cos(half) + x * sgn * math.sin(half)
        a, b = piv + e * 0.6, piv + e * (L + 0.15)
        S.append(cone(a, b, 0.34, 0.3, "rib", band=band_of(sk, (a + b) * 0.5), part="guard"))
    S.append(sphere(piv, 0.5, "gold", band=band_of(sk, piv), part="rivet"))
    # A cut's smear: the arc the rim swept since the frame before, a sheet of pale jade light behind the leaf.
    if wp.get("smear_from") is not None:
        d0 = off_camera(unit(sk.w(wp["smear_from"])), spec["least"])
        ang = float(np.degrees(np.arccos(np.clip(d0 @ d, -1.0, 1.0))))
        steps = max(6, int(ang / 4.0))
        for j in range(steps):
            t = (j + 0.5) / steps
            dj = sweep(d0, d, sk.up, t)
            if float(np.degrees(np.arccos(np.clip(dj @ d, -1.0, 1.0)))) < spec["spread"]:
                continue                                    # under the leaf
            p0, p1 = piv + dj * L * 0.5, piv + dj * L * 1.04
            S.append(cone(p0, p1, 0.5 + 0.3 * t, 0.75 + 0.35 * t, "smear", band=band_of(sk, (p0 + p1) * 0.5),
                          part="smear"))
    return S
