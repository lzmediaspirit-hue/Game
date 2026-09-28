"""Hair: a hair style over the skull, from a set's spec (sets/hair.py).

A style is a cap over the skull with a hairline (the face shows through below it; `fringe` lowers it over the brow),
then its pieces in order, each placed in the head's frame (forward, right, up) from `from`: the head, or an earlier
piece's `id`.
  knot     a mass of hair (`radii`) with grooves between `strands` locks
  lump     a plain mass of hair (a tie at the nape)
  ribbon   a band of ribbon (`radii`)
  pin      a gold pin from `a` to `b`, radii `r`
  tail     a lock from `at` leaving along back * dir[0] + up * dir[1], `length` long, radii `r` (root, tip), in `segs`
           segments, `stiff` against gravity and the pose's drag; `rings` [(fraction, material)] bind it; `k` flattens
           it; `part` names it
Tails hang by gravity and trail the pose's `drag`; a tail's part behind the neck is drawn in the back band, under the
body.
"""
from __future__ import annotations

import numpy as np

from ..body import SKULL
from ..geom import depth, unit, vec
from ..raster import cone, ellipsoid, sphere

CAP_GROW = (0.65, 0.6, 0.7)
CAP_AT = (-0.35, 0.0, 0.45)

# The hairline: the lowest unit-height the cap covers, by the angle round the head (0 the face, 180 the nape).
HAIRLINE = [(0, 0.44), (18, 0.38), (34, 0.24), (50, 0.08), (62, 0.0), (68, -0.42), (84, -0.52), (90, -0.12),
            (104, -0.12), (118, -0.4), (135, -0.7), (155, -0.88), (180, -0.94)]
FRINGE = [(0, 0.30), (18, 0.28), (34, 0.16), (50, 0.02), (62, -0.04), (68, -0.46), (84, -0.56), (90, -0.14),
          (104, -0.14), (118, -0.4), (135, -0.7), (155, -0.88), (180, -0.94)]


def _interp(table, a):
    for (a0, v0), (a1, v1) in zip(table, table[1:]):
        if a <= a1:
            return v0 + (v1 - v0) * (a - a0) / (a1 - a0)
    return table[-1][1]


def _cap_clip(fringe: bool):
    table = FRINGE if fringe else HAIRLINE
    radii = np.array(SKULL) + np.array(CAP_GROW)

    def clip(loc):
        u = loc / radii
        n = np.linalg.norm(u, axis=1)
        u = u / np.maximum(n, 1e-9)[:, None]
        phi = np.degrees(np.abs(np.arctan2(u[:, 1], u[:, 0])))
        lim = np.interp(phi, [a for a, _ in table], [v for _, v in table])
        # strand tips along the hairline: every other lock a little longer (the fringe's more so)
        tips = (np.floor((np.degrees(np.arctan2(u[:, 1], u[:, 0])) + 180.0) / (10.0 if fringe else 13.0)) % 2)
        lim = lim - tips * np.where(phi < 45, 0.1 if fringe else 0.05, 0.12)
        return u[:, 2] > lim
    return clip


def _strands(n_strands: int = 13, crown=(0.0, 0.0)):
    """Paint: hair, with darker grooves between locks that run from the crown down."""
    radii = np.array(SKULL) + np.array(CAP_GROW)

    def paint(loc, P, nrm):
        u = loc / radii
        u = u / np.maximum(np.linalg.norm(u, axis=1), 1e-9)[:, None]
        phi = np.degrees(np.arctan2(u[:, 1], u[:, 0]))
        lat = np.degrees(np.arcsin(np.clip(u[:, 2], -1, 1)))
        k = (phi + 180.0) / 360.0 * n_strands + (90.0 - lat) * 0.012
        groove = ((k % 1.0) < 0.2) & (lat < 62)
        names = np.array(["hair"] * len(loc), dtype=object)
        return names, np.where(groove, -1, 0)
    return paint


def cap(sk, fringe: bool) -> list:
    Mh = sk.Mh
    c = sk.head + Mh @ vec(*CAP_AT)
    radii = np.array(SKULL) + np.array(CAP_GROW)
    return [ellipsoid(c, Mh, radii, "hair", part="hair", clip=_cap_clip(fringe), paint=_strands(),
                      frame=(c, Mh))]


def tail(sk, start, first_dir, length: float, r0: float, r1: float, segs: int = 6, stiff: float = 0.55,
         mat="hair", part="tail", k=1.0, rings=None, ragged=False) -> list:
    """A lock or tail from `start` (world), leaving along `first_dir` (world), bending toward gravity and the drag.
    `rings` = [(fraction, material)] binds it at those points. Each segment is in the back band when it is behind the
    neck, else mid (over the shirt)."""
    pts = [np.asarray(start, float)]
    d = unit(first_dir)
    down = vec(0, 0, -1)
    drag = np.asarray(sk.drag, float)
    step = length / segs
    for i in range(segs):
        w = (i + 1) / segs
        target = unit(down + drag * (0.6 + 0.8 * w))
        d = unit(d * stiff + target * (1 - stiff))
        nxt = pts[-1] + d * step
        # keep a hanging tail off the back: never through the torso's back plane
        pts.append(nxt)
    ref = depth(sk.neck) - 1.2
    out = []
    side = sk.right
    for i in range(segs):
        a, b = pts[i], pts[i + 1]
        ra = r0 + (r1 - r0) * i / segs
        rb = r0 + (r1 - r0) * (i + 1) / segs
        band = "back" if depth((a + b) * 0.5) < ref else "mid"
        last = i == segs - 1
        clip = None
        if ragged and last:
            L = float(np.linalg.norm(b - a))
            clip = (lambda loc, L=L: loc[:, 2] < L * (1.0 - 0.75 * ((np.floor((loc[:, 0] + 8.0) / 1.3) % 2) == 1)))
        out.append(cone(a, b, ra, rb, mat, k=k, side=side, band=band, part=part, clip=clip))
        if not (ragged and last):
            out.append(sphere(b, rb, mat, band=band, part=part) if k == 1.0 else
                       ellipsoid(b, _frame(b - a, side), (rb, rb * k, rb), mat, band=band, part=part))
    for frac, rm in (rings or []):
        at = min(segs - 1, int(frac * segs))
        p = pts[at] + (pts[at + 1] - pts[at]) * (frac * segs - at)
        rr = r0 + (r1 - r0) * frac
        band = "back" if depth(p) < ref else "mid"
        out.append(cone(p - unit(pts[at + 1] - pts[at]) * 0.45, p + unit(pts[at + 1] - pts[at]) * 0.45, rr + 0.35,
                        rr + 0.35, rm, k=k, side=side, band=band, part=part + "_ring"))
    return out


def _frame(axis, side):
    w = unit(axis)
    x = unit(side - w * float(side @ w))
    return np.stack([x, np.cross(w, x), w], axis=1)


def solids(sk, spec: dict) -> list:
    Mh = sk.Mh
    back = -Mh[:, 0]
    up = Mh[:, 2]
    S = cap(sk, bool(spec.get("fringe")))
    at = {"head": sk.head}
    for kind, p in spec["pieces"]:
        o = at[p.get("from", "head")]
        if kind in ("knot", "lump"):
            c = o + Mh @ vec(*p["at"])
            if kind == "knot":
                S.append(ellipsoid(c, Mh, p["radii"], "hair", part=p.get("part", "knot"), paint=_strands(p["strands"]),
                                   frame=(c, Mh)))
            else:
                S.append(ellipsoid(c, Mh, p["radii"], "hair", part=p.get("part", "tie")))
            at[p["id"]] = c
        elif kind == "ribbon":
            S.append(ellipsoid(o + Mh @ vec(*p["at"]), Mh, p["radii"], "ribbon", part="ribbon"))
        elif kind == "pin":
            S.append(cone(o + Mh @ vec(*p["a"]), o + Mh @ vec(*p["b"]), p["r"][0], p["r"][1], "pin", part="pin"))
        elif kind == "tail":
            kw = {k: p[k] for k in ("rings", "k", "part") if k in p}
            S += tail(sk, o + Mh @ vec(*p["at"]), back * p["dir"][0] + up * p["dir"][1], p["length"], p["r"][0], p["r"][1],
                      segs=p["segs"], stiff=p["stiff"], **kw)
        else:
            raise ValueError("hair piece " + kind)
    return S
