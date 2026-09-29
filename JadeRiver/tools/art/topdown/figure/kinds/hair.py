"""Hair: a hair style over the skull, from a set's spec (sets/hair.py).

A style is a cap over the skull with a hairline (the face shows through below it; `fringe` lowers it over the brow),
then its pieces in order, each placed in the head's frame (forward, right, up) from `from`: the head, or an earlier
piece's `id`.
  knot     a mass of hair (`radii`), wound in locks
  lump     a plain mass of hair (a tie at the nape), wound in locks
  ribbon   a band of ribbon (`radii`)
  pin      a gold pin from `a` to `b`, radii `r`
  tail     a lock from `at` leaving along back * dir[0] + up * dir[1], `length` long, radii `r` (root, tip), in `segs`
           segments, `stiff` against gravity and the pose's drag; `rings` [(fraction, material)] bind it; `k` flattens
           it; `part` names it
Tails hang by gravity and trail the pose's `drag`; a tail's part behind the neck is drawn in the back band, under the
body.

How it reads at 38 px (decision 42): the cap is painted in a few broad locks (`locks`), each a groove and a lit ridge,
under a sheen ring (`sheen`, the band of latitude it lies in) that breaks lock by lock on the sunlit side, with a darker
crown past it; knots and ties are wound in locks with a sheen on their sunlit cap; each lock of a tail has a groove down
one side and a lit strand down the other. Loose locks (`loose`) at the temples and over the brow break the cap's round
silhouette, so it never reads as a helmet, and frame the face.
"""
from __future__ import annotations

import numpy as np

from .. import geom
from ..body import SKULL, glyphs
from ..geom import LIGHT, SCR_D, SCR_R, TOWARD, depth, project, unit, vec
from ..raster import AX, AY, cone, ellipsoid, sphere

CAP_GROW = (0.65, 0.6, 0.7)
CAP_AT = (-0.35, 0.0, 0.45)
CAP_RADII = np.array(SKULL) + np.array(CAP_GROW)

# The hairline: the lowest unit-height the cap covers, by the angle round the head (0 the face, 180 the nape).
HAIRLINE = [(0, 0.44), (18, 0.38), (34, 0.24), (50, 0.08), (62, 0.0), (68, -0.42), (84, -0.52), (90, -0.12),
            (104, -0.12), (118, -0.4), (135, -0.7), (155, -0.88), (180, -0.94)]
FRINGE = [(0, 0.30), (18, 0.28), (34, 0.16), (50, 0.02), (62, -0.04), (68, -0.46), (84, -0.56), (90, -0.14),
          (104, -0.14), (118, -0.4), (135, -0.7), (155, -0.88), (180, -0.94)]
# A temple strand (given on the left, mirrored to the right), in the head's frame (forward, right, up; units from the
# head's centre): (root, tip, root radius, tip radius). It hangs just in front of the ear to the jaw, behind the cheek,
# so a three-quarter face stays clear. A lock whose root lies further out than 3 units to a side is mirrored.
TEMPLE = ((1.5, -5.8, 2.2), (2.0, -6.4, -3.6), 1.15, 0.4)


def _cap_clip(fringe: bool):
    table = FRINGE if fringe else HAIRLINE
    radii = CAP_RADII

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


def _cap_paint(locks: int, sheen: tuple):
    """The cap in broad locks, each a groove and a lit ridge under a sheen ring that breaks lock by lock on the sunlit
    side, and a darker crown past the ring."""

    def paint(loc, P, nrm):
        u = loc / CAP_RADII
        u = u / np.maximum(np.linalg.norm(u, axis=1), 1e-9)[:, None]
        phi = np.degrees(np.arctan2(u[:, 1], u[:, 0]))
        lat = np.degrees(np.arcsin(np.clip(u[:, 2], -1, 1)))
        a = (phi + 180.0) / 360.0 * locks + (90.0 - lat) * 0.014
        f = a - np.floor(a)
        bias = np.zeros(len(loc), dtype=np.float32)
        lit = nrm @ LIGHT
        low = lat < sheen[0] - 4.0
        bias[(f < 0.2) & low] -= 1.0                                 # the groove between two locks, under the sheen
        bias[(f > 0.45) & (f < 0.7) & low & (lit > 0.3)] += 0.6      # each lock's lit ridge
        band = (lat > sheen[0]) & (lat < sheen[1]) & (lit > 0.1)     # the sheen ring round the crown, sunlit side
        cut = (f < 0.12) & (lat < sheen[0] + 5.0)                     # broken where a groove runs up into it
        bias[band & ~cut] += 2.0
        bias[band & ~cut & (lit > 0.5) & (f > 0.3) & (f < 0.8)] += 1.0
        bias[lat > sheen[1] + 14.0] -= 0.4                           # the crown past the ring turns away
        return np.array(["hair"] * len(loc), dtype=object), bias
    return paint


def _mass_paint(strands: int, spiral: float):
    """A knot or a tie: locks wound round it, a sheen on its sunlit cap."""

    def paint(loc, P, nrm):
        n = len(loc)
        r = np.linalg.norm(loc, axis=1) + 1e-9
        phi = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
        a = (phi + 180.0) / 360.0 * strands + loc[:, 2] / r * spiral
        f = a - np.floor(a)
        bias = np.zeros(n, dtype=np.float32)
        lit = nrm @ LIGHT
        bias[f < 0.16] -= 1.0
        bias[(lit > 0.5) & (f > 0.3) & (f < 0.8)] += 1.2
        return np.array(["hair"] * n, dtype=object), bias
    return paint


def _lock_paint(loc, P, nrm):
    """A lock of a tail: a groove down one side, a lit strand down the other."""
    n = len(loc)
    ang = np.degrees(np.arctan2(loc[:, 1], loc[:, 0]))
    bias = np.zeros(n, dtype=np.float32)
    lit = nrm @ LIGHT
    bias[np.abs(((ang + 30.0) % 120.0) - 60.0) < 9.0] -= 1.0
    bias[(lit > 0.45) & (np.abs(((ang + 90.0) % 120.0) - 60.0) < 20.0)] += 1.1
    return np.array(["hair"] * n, dtype=object), bias


def cap(sk, fringe: bool, locks: int = 8, sheen=(36.0, 52.0)) -> list:
    Mh = sk.Mh
    c = sk.head + Mh @ vec(*CAP_AT)
    return [ellipsoid(c, Mh, CAP_RADII, "hair", part="hair", clip=_cap_clip(fringe), paint=_cap_paint(locks, sheen),
                      frame=(c, Mh))]


def eye_box(sk):
    """Where the eyes are drawn (body.face), as the box a lock of hair or a hat's edge must leave clear so the eyes
    read in every pose (a nod brings the fringe down over them): (the row from which samples are cut, the columns from,
    to), in art px from the feet; the columns a pixel wider than the eyes each side, so no outline lands on them. None
    when no eye faces the camera."""
    yaw = sk.fr.yaw_to_camera(sk.Mh[:, 0])
    if abs(yaw) > 118:
        return None
    hx = project(sk.head)[0]
    cols, rows = [], []
    for sg in (-1.0, 1.0):
        p = sk.head + sk.Mh @ vec(4.95, sg * 2.2, 1.0)
        if float(unit(p - sk.head) @ TOWARD) < 0.05:
            continue
        sx, sy = project(p)
        F = glyphs()
        w = len(F["eye_front"][0])
        if 24 < abs(yaw) <= 66 and ((sg > 0) == (yaw > 0)):
            w = len(F["eye_far"][0])                   # the far eye in three quarters is narrower
        elif abs(yaw) > 66:
            if (sg > 0) == (yaw > 0):
                continue                               # in profile only the near eye shows
            w = len(F["eye_side"][0])
            sx += -1 if yaw < 0 else 1
        x0 = np.floor(sx + AX - (w - 1) * 0.5)
        cols += [x0, x0 + w]
        rows.append(np.floor(sy + AY))
    if not rows:
        return None
    # Shut eyes are one dark row: a row of skin between it and the hair's outline, so it does not read as the outline.
    gap = 2.0 if sk.eyes == "shut" else 1.0
    return min(rows) - gap - AY, min(cols) - 1.0 - AX, max(cols) + 1.0 - AX


def clear_of_eyes(box, o, M, clip=None):
    """A clip (over `clip`, if any) that cuts a solid's samples inside the eye box (`eye_box`), for a solid framed at
    origin `o` with axes `M`."""
    lim, xa, xb = box

    def cut(loc):
        P = o + loc @ M.T
        x, y = P @ SCR_R * geom.SCALE, P @ SCR_D * geom.SCALE
        keep = ~((y >= lim) & (x >= xa) & (x < xb))
        return keep if clip is None else keep & clip(loc)
    return cut


def loose_locks(sk, locks: list) -> list:
    """Loose locks from the head (a list of (root, tip, root radius, tip radius) in the head's frame), each a tapered
    lock with its root rounded into the cap; a temple strand is drawn on both sides."""
    out = []
    Mh = sk.Mh
    for (a, b, r0, r1) in locks:
        pairs = [(a, b)]
        if a[1] < -3.0:
            pairs.append(((a[0], -a[1], a[2]), (b[0], -b[1], b[2])))
        for aa, bb in pairs:
            pa = sk.head + Mh @ vec(*aa)
            pb = sk.head + Mh @ vec(*bb)
            axis = unit(pb - pa)
            side = unit(np.cross(axis, unit(pa - sk.head)))
            out.append(cone(pa, pb, r0, r1, "hair", k=0.6, side=side, band="mid", part="lock", paint=_lock_paint))
            out.append(sphere(pa, r0 * 0.9, "hair", band="mid", part="lock"))
    return out


def keep_eyes_clear(sk, solids: list) -> list:
    """Cut every solid of a hair style or a hat out of the eye box (`eye_box`), so its fringe, forelocks or band and
    their outline end above the eyes in every pose."""
    box = eye_box(sk)
    if box is None:
        return solids
    for s in solids:
        o, M = s.frame if s.frame is not None else (s.geo["c"], s.geo.get("M", np.eye(3)))
        s.clip = clear_of_eyes(box, o, M, s.clip)
        if s.frame is None:
            s.frame = (o, M)
    return solids


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
    """A style's solids. Spec keys besides `pieces` and `fringe`: `locks` the cap's lock count, `sheen` the band of
    latitude its sheen ring lies in, `strands` and `spiral` how knots and ties are wound, `loose` its loose locks."""
    Mh = sk.Mh
    back = -Mh[:, 0]
    up = Mh[:, 2]
    S = cap(sk, bool(spec.get("fringe")), int(spec.get("locks", 8)), tuple(spec.get("sheen", (36.0, 52.0))))
    mass = _mass_paint(int(spec.get("strands", 6)), float(spec.get("spiral", 2.2)))
    at = {"head": sk.head}
    for kind, p in spec["pieces"]:
        o = at[p.get("from", "head")]
        if kind in ("knot", "lump"):
            c = o + Mh @ vec(*p["at"])
            S.append(ellipsoid(c, Mh, p["radii"], "hair", part=p.get("part", "knot" if kind == "knot" else "tie"),
                               paint=mass, frame=(c, Mh)))
            at[p["id"]] = c
        elif kind == "ribbon":
            S.append(ellipsoid(o + Mh @ vec(*p["at"]), Mh, p["radii"], "ribbon", part="ribbon"))
        elif kind == "pin":
            S.append(cone(o + Mh @ vec(*p["a"]), o + Mh @ vec(*p["b"]), p["r"][0], p["r"][1], "pin", part="pin"))
        elif kind == "tail":
            kw = {k: p[k] for k in ("rings", "k", "part") if k in p}
            T = tail(sk, o + Mh @ vec(*p["at"]), back * p["dir"][0] + up * p["dir"][1], p["length"], p["r"][0],
                     p["r"][1], segs=p["segs"], stiff=p["stiff"], **kw)
            for s in T:
                if s.kind == "cone" and s.mat == "hair":
                    s.paint = _lock_paint
            S += T
        else:
            raise ValueError("hair piece " + kind)
    S += loose_locks(sk, spec.get("loose", []))
    return keep_eyes_clear(sk, S)
