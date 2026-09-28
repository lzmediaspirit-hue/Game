"""Sound: what a sounding weapon (kinds/flute.py, kinds/bell.py) sends out on its blows, as a blade leaves its smear.

Not a layer kind of its own; the flute and the bell draw with it:
  stage(sk)    0 on a blow's hit frame, 1 on the frame after (as a cut's smear shows on both), else None. A blow is
               any punch, swing or thrust in the action catalogue (figure/actions.py): the flute's combo thrusts, the
               bell's swings, and a technique may play any of them. The frame is known by its pose, so the catalogue
               needs no key of its own for it.
  arcs(...)    arcs of light about a point, in the plane that faces the camera, opening along the weapon as it shows
               on screen; a weapon pointed at the camera (or away) closes them into rings. Like the smear, light has no
               ink round it (a `glow` material in the item's Look); the frame after the hit draws them in a fainter
               material, as the sound dies away.
"""
from __future__ import annotations

import math

import numpy as np

from .. import actions as A
from ..geom import SCR_R, TOWARD, unit
from ..raster import cone, sphere

BLOWS = ("punch", "swing", "thrust")
_hits: list | None = None


def _hit_poses() -> list:
    global _hits
    if _hits is None:
        _hits = []
        for name, spec in A.CATALOG.items():
            hit = spec[3]
            if hit is None or name.split("_")[0] not in BLOWS:
                continue
            ps = A.poses(name)
            _hits.append((ps[hit], 0))
            if hit + 1 < len(ps):
                _hits.append((ps[hit + 1], 1))
    return _hits


def stage(sk) -> int | None:
    """0 on a blow's hit frame, 1 on the frame after, None on any other frame (or with the weapon laid down)."""
    if (sk.weapon or {}).get("laid"):
        return None
    for p, st in _hit_poses():
        if sk.p == p:
            return st
    return None


def arcs(centre, axis, radii, spans, mat, band, width=0.52, shrink=0.35, part="sound") -> list:
    """Arcs of light about `centre` (world), each of radius radii[i] spanning spans[i] radians either side of `axis`
    as it shows on screen, in the plane facing the camera. The more `axis` points at the camera or away from it, the
    further the arcs close round, to full rings, `shrink` smaller as they spread round the figure."""
    ax = np.asarray(axis, float)
    flat = ax - TOWARD * float(ax @ TOWARD)
    on_screen = float(np.linalg.norm(flat))
    u = flat / on_screen if on_screen > 1e-3 else SCR_R
    v = np.cross(TOWARD, u)
    close = min(1.0, max(0.0, (0.8 - on_screen) / 0.6))
    S = []
    for r, span in zip(radii, spans):
        span = span + (math.pi - span) * close
        r = r * (1.0 - shrink * close)
        n = max(4, int(math.ceil(2.0 * span * r / 0.9)))
        pts = [centre + r * (math.cos(t) * u + math.sin(t) * v)
               for t in np.linspace(-span, span, n + 1)]
        for j in range(n):
            S.append(cone(pts[j], pts[j + 1], width, width, mat, band=band, part=part))
            S.append(sphere(pts[j], width, mat, band=band, part=part))
        S.append(sphere(pts[-1], width, mat, band=band, part=part))
    return S
