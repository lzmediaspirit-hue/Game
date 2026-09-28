"""The creator's six hair styles (parts.json `hair`), after the side-view sheets:

  short_knot  Sage knot      a round bun on the crown's back, jade ribbon, gold pin
  topknot     Daoist knot    a tall knot on the crown, jade ribbon and gold pin, one long lock down the back
  ponytail    Jade tail      a low tail tied at the nape with a jade band, to the shoulder blades
  high_pony   Sky ponytail   a high tail tied at the crown's back with a jade ribbon, sweeping down the back
  long_tied   Long silk tie  a fringe, and one long tail bound with gold and jade rings to the waist
  flowing     Flowing tail   a fringe, a tall loop on the crown and a long fall of hair to the waist

Each is a cap over the skull with a hairline (the face shows through below it), plus its knots and tails. Tails hang
by gravity and trail the pose's `drag`; a tail's part behind the neck is drawn in the back band, under the body.
"""
from __future__ import annotations

import math

import numpy as np

from .body import SKULL
from .geom import depth, unit, vec
from .raster import cone, ellipsoid, sphere

STYLES = ["short_knot", "topknot", "ponytail", "high_pony", "long_tied", "flowing"]
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


def solids(sk, style: str) -> list:
    Mh = sk.Mh
    H = sk.head
    back = -Mh[:, 0]
    up = Mh[:, 2]
    S = cap(sk, style in ("long_tied", "flowing"))
    if style == "short_knot":
        bun = H + Mh @ vec(-2.4, 0.0, 6.9)
        S.append(ellipsoid(bun, Mh, (2.8, 2.8, 2.5), "hair", part="knot", paint=_strands(8), frame=(bun, Mh)))
        S.append(ellipsoid(bun + Mh @ vec(0.2, 0, -1.6), Mh, (2.85, 2.85, 0.8), "ribbon", part="ribbon"))
        S.append(cone(bun + Mh @ vec(2.1, -3.6, 0.7), bun + Mh @ vec(2.1, 3.4, 0.7), 0.5, 0.45, "pin", part="pin"))
    elif style == "topknot":
        knot = H + Mh @ vec(-1.2, 0.0, 8.3)
        S.append(ellipsoid(knot, Mh, (2.5, 2.4, 3.2), "hair", part="knot", paint=_strands(7), frame=(knot, Mh)))
        S.append(ellipsoid(knot + Mh @ vec(0.1, 0, -2.2), Mh, (2.6, 2.5, 0.8), "ribbon", part="ribbon"))
        S.append(cone(knot + Mh @ vec(2.0, -3.4, 0.6), knot + Mh @ vec(2.0, 3.2, 0.6), 0.5, 0.45, "pin", part="pin"))
        S += tail(sk, knot + Mh @ vec(-1.6, 0, 0.4), back * 0.9 - up * 0.4, 13.0, 1.05, 0.7, segs=6, stiff=0.5)
    elif style == "ponytail":
        tie = H + Mh @ vec(-5.8, 0.0, -2.2)
        S.append(ellipsoid(tie, Mh, (1.5, 1.7, 1.5), "hair", part="tie"))
        S.append(ellipsoid(tie + Mh @ vec(-0.6, 0, 0), Mh, (0.9, 1.75, 1.25), "ribbon", part="ribbon"))
        S += tail(sk, tie + Mh @ vec(-0.9, 0, -0.4), back * 0.5 - up, 10.5, 1.45, 0.8, segs=5, stiff=0.6)
    elif style == "high_pony":
        tie = H + Mh @ vec(-4.9, 0.0, 4.6)
        S.append(ellipsoid(tie, Mh, (1.6, 1.8, 1.7), "hair", part="tie"))
        S.append(ellipsoid(tie + Mh @ vec(-0.5, 0, 0.1), Mh, (1.0, 1.9, 1.4), "ribbon", part="ribbon"))
        S += tail(sk, tie + Mh @ vec(-1.2, 0, 0.3), back * 1.0 + up * 0.35, 14.0, 2.0, 0.9, segs=7, stiff=0.72,
                  rings=[(0.08, "ribbon")])
    elif style == "long_tied":
        tie = H + Mh @ vec(-5.7, 0.0, -1.2)
        S.append(ellipsoid(tie, Mh, (1.6, 2.0, 1.8), "hair", part="tie"))
        S += tail(sk, tie + Mh @ vec(-0.8, 0, -0.5), back * 0.35 - up, 17.0, 1.55, 1.0, segs=8, stiff=0.6,
                  rings=[(0.02, "ribbon"), (0.3, "pin"), (0.55, "ribbon"), (0.8, "pin")])
    elif style == "flowing":
        loop = H + Mh @ vec(-1.0, 0.0, 8.4)
        S.append(ellipsoid(loop, Mh, (1.5, 1.35, 2.9), "hair", part="knot", paint=_strands(6), frame=(loop, Mh)))
        S.append(ellipsoid(loop + Mh @ vec(0.1, 0, -2.2), Mh, (1.6, 1.5, 0.65), "ribbon", part="ribbon"))
        S.append(cone(loop + Mh @ vec(0.4, -2.6, -0.8), loop + Mh @ vec(0.4, 2.5, -0.8), 0.45, 0.4, "pin", part="pin"))
        # the fall: a wide flat sheet of hair from the back of the head to the waist
        S += tail(sk, H + Mh @ vec(-4.4, 0, 1.0), back * 0.3 - up, 18.0, 3.4, 2.3, segs=8, stiff=0.55, k=0.42,
                  part="fall")
    return S
