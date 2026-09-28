"""Sabre: the heavy sabre, a dao, held in the right hand along the pose's `blade` line (or laid on the ground), from a
set's spec (sets/weapon_heavy_sabre.py). A broad single-edged blade of grey steel that swells to a belly near the point
and sweeps back toward its spine, a pale bevel along the cutting edge, a bronze guard and pommel on a dark grip long
enough for the second hand; and on a cut, a heavy crescent of pale jade light where the pose asks for one
(`smear_from`), fat at the blade and thinning to a sliver at its tail, its rim the path of the point.

The blade is flat: its width lies along the pose's `flat` (the edge on its far side), or flat on the ground when laid
down, turned part way toward the camera (`face`) so the broad side reads in every facing, as a sabre drawn in a 3/4
view does.

Spec keys:
  blade  the blade's length          width  its half-width at the guard      belly  its half-width at the belly
  curve  how far the point sweeps back toward the spine                     thick  its thickness against its width
  face   how far the flat turns toward the camera (0: the pose's flat)      hilt   the grip's length
  guard  the guard's half-width
"""
from __future__ import annotations

import math

import numpy as np

from ..geom import SCR_D, TOWARD, unit
from ..raster import cone, ellipsoid, sphere
from ..weapons import DEPTH_STRETCH, band_of, blade_line, flat_frame, stretch

# Stations along the blade (0 at the guard, 1 at the point): the edge widens to the belly, then curves up to meet the
# spine at the point.
STATIONS = (0.0, 0.16, 0.32, 0.48, 0.62, 0.74, 0.84, 0.92, 1.0)
BELLY_AT = 0.72


def _half_width(spec: dict, s: float) -> float:
    w0, wb = spec["width"], spec["belly"]
    if s <= BELLY_AT:
        return w0 + (wb - w0) * (s / BELLY_AT) ** 1.4
    u = (s - BELLY_AT) / (1.0 - BELLY_AT)
    tip = 0.28
    return tip + (wb - tip) * math.sqrt(max(0.0, 1.0 - u ** 2.2))


def _width_axis(sk, d: np.ndarray, flat: np.ndarray, spec: dict) -> np.ndarray:
    """The blade's width direction: the pose's flat (laid down, flat on the ground), turned part way toward the one
    that shows the broad side."""
    x = flat_frame(d, flat)
    if (sk.weapon or {}).get("laid") and abs(float(d[2])) < 0.95:
        x = unit(np.cross(d, np.array([0.0, 0.0, 1.0])))
    cam = np.cross(d, TOWARD)
    if float(np.linalg.norm(cam)) < 1e-6:
        return x
    cam = unit(cam)
    if float(cam @ x) < 0.0:
        cam = -cam
    return flat_frame(d, x * (1.0 - spec["face"]) + cam * spec["face"])


def solids(sk, spec: dict) -> list:
    S = []
    g, d, flat = blade_line(sk)
    x = _width_axis(sk, d, flat, spec)

    def at(k, off=0.0):
        return stretch(sk, g, g + d * k + x * off)
    hilt0 = at(-(spec["hilt"] * 0.5 + 0.1))
    guard = at(spec["hilt"] * 0.5)
    S.append(sphere(at(-(spec["hilt"] * 0.5 + 0.5)), 0.7, "bronze", band=band_of(sk, hilt0), part="pommel"))
    S.append(cone(hilt0, guard, 0.55, 0.52, "hilt", band=band_of(sk, g), part="hilt"))
    # the guard: an oval plate, longest across the blade's width
    S.append(ellipsoid(guard, np.stack([x, np.cross(d, x), d], axis=1), (spec["guard"], spec["guard"] * 0.55, 0.55),
                       "bronze", band=band_of(sk, guard), part="guard"))
    # The blade, cone by cone between the stations, each in its own band. Its spine curves back (+x) toward the point;
    # its edge (-x) bellies out, then sweeps up to meet the spine there.
    base = spec["hilt"] * 0.5 + 0.5
    L = spec["blade"]

    def spine(s):
        return spec["width"] + spec["curve"] * s * s

    for i in range(len(STATIONS) - 1):
        s0, s1 = STATIONS[i], STATIONS[i + 1]
        h0, h1 = _half_width(spec, s0), _half_width(spec, s1)
        a = at(base + L * s0 + (0.1 if i else 0.0), spine(s0) - h0)
        b = at(base + L * s1, spine(s1) - h1)

        def paint(loc, P, nn, h0=h0, h1=h1, ln=float(np.linalg.norm(b - a))):
            # a pale bevel along the cutting edge (the flat's own tones are the set's `thresholds`)
            rad = h0 + (h1 - h0) * np.clip(loc[:, 2] / max(ln, 1e-6), 0.0, 1.0)
            return (np.where(loc[:, 0] < -rad * 0.45, "edge", "blade").astype(object),
                    np.zeros(len(loc), dtype=np.int16))
        S.append(cone(a, b, h0, h1, "blade", k=spec["thick"], side=x, band=band_of(sk, (a + b) * 0.5), part="blade",
                      paint=paint))
    S += _smear(sk, g, d, spec, base)
    return S


def _rotate(v, n, a):
    return v * math.cos(a) + np.cross(n, v) * math.sin(a) + n * float(n @ v) * (1.0 - math.cos(a))


def _on_screen(v) -> np.ndarray:
    """A direction from the grip on screen, the ground's depth stretched as the weapon's is."""
    return np.array([float(v[0]), float(v[1]) * DEPTH_STRETCH * SCR_D[1] + float(v[2]) * SCR_D[2]])


def _over_the_top(sk, d0, d) -> np.ndarray:
    """The way a half-round chop goes over: straight over the head where that shows (a chop in the plane of the view
    would draw as a bar), else leaning toward a shoulder, the sword arm's first: the most upright way whose crescent
    is at least 70% of the widest this facing can show."""
    a, b = _on_screen(d0), _on_screen(d)
    ways = []
    for deg in (0, 20, -20, 35, -35, 50, -50, 65, -65):
        via = unit(sk.up * math.cos(math.radians(deg)) + sk.right * math.sin(math.radians(deg)))
        via = unit(via - d0 * float(via @ d0))
        v = _on_screen(via)
        ways.append((abs(float((v[0] - a[0]) * (b[1] - a[1]) - (v[1] - a[1]) * (b[0] - a[0]))), via))
    widest = max(area for area, _ in ways)
    return next(via for area, via in ways if area >= widest * 0.7)


def _smear(sk, g, d, spec: dict, base: float) -> list:
    """A cut's crescent of pale jade light, swept from the blade's last place (`smear_from`) to where it is now.

    A cut that turns (nearly) half round, the heavy descending chop, goes over the top (`_over_the_top`), not through
    the body. On the blow itself (a wide sweep) the crescent is fat at the blade and thins toward its tail; its rim,
    the path of the point, is the brightest and its tail the dimmest. On the follow-through (a short sweep) what is
    left of it trails the blade, thinner and dimmer, back along the same arc."""
    wp = sk.weapon or {}
    if wp.get("smear_from") is None:
        return []
    d0 = unit(sk.w(wp["smear_from"]))
    cr = np.cross(d0, d)
    if float(np.linalg.norm(cr)) < 0.4 and float(d0 @ d) < 0.0:
        n = unit(np.cross(d0, _over_the_top(sk, d0, d)))
    else:
        n = unit(cr)
    ang = math.atan2(float(np.cross(d0, d) @ n), float(d0 @ d))
    if ang < 0.0:
        ang += 2.0 * math.pi
    miss = d - _rotate(d0, n, ang)      # what the arc's plane leaves out of the blade's place: closed over the sweep
    blow = math.degrees(ang) >= 100.0
    start = 0.0 if blow else -max(0.0, math.radians(80.0) - ang)
    span = ang - start
    L = spec["blade"]
    r_out = base + L * 1.06
    steps = max(8, int(math.degrees(span) / 3.5))
    S = []
    for j in range(steps):
        t = (j + 0.5) / steps
        phi = start + span * t
        dj = unit(_rotate(d0, n, phi) + miss * max(0.0, phi / ang))
        f = (0.12 + 0.55 * t ** 1.3) if blow else (0.08 + 0.26 * t ** 1.3)
        r_in = r_out - L * f
        p0 = stretch(sk, g, g + dj * r_in)
        p1 = stretch(sk, g, g + dj * r_out)
        if not blow:
            body, rim = ("smear_lo", "smear_mid") if t < 0.55 else ("smear_mid", "smear")
        elif t < 0.3:
            body, rim = "smear_lo", "smear_mid"
        elif t < 0.6:
            body, rim = "smear_mid", "smear_hi"
        else:
            body, rim = "smear", "smear_hi"
        ln = float(np.linalg.norm(p1 - p0))
        rim_w = 1.0 + 0.4 * t

        def paint(loc, P, nn, body=body, rim=rim, ln=ln, rim_w=rim_w):
            return (np.where(loc[:, 2] > ln - rim_w, rim, body).astype(object), np.zeros(len(loc), dtype=np.int16))
        S.append(cone(p0, p1, 0.45 + 0.45 * t, 0.7 + 0.5 * t, "smear", band=band_of(sk, (p0 + p1) * 0.5),
                      part="smear", paint=paint))
    return S
