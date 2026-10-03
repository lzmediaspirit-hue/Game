"""The spirit plan (M1), from the paper talisman ghost (`talisman`): a floating spirit made of layered strips, no legs,
the room view hovering it over the floor (a flyer). Made for the paper ghost first; the wisps and lanterns after it can
lay their own parts over it.

  hood   a hooded dome of wrapped strips over its head (radii, at its height), the strips' seams round it
  face   a dark hollow under the hood's brow, two eyes glowing violet in it (flaring in the tell, squeezed when struck,
         dark when it dies), and a talisman hanging over it from the brow: a red seal at its top, red script down it
  skirt  strips hanging from the hood's rim (`n`, their length and width), torn at their ends, fluttering in an unseen
         draft and streaming back as it drifts. Every strip is paper: flat plates cut square, a column of red script
         down its middle, its end torn ragged
  arms   a bundle of strips at each side; fanned out behind it like a peacock in the tell, the near bundle flung forward
         on the blow (the talisman it throws leaves it then: the room view draws it in flight)
  wisps  violet soul wisps rising off it

The motion styles (STYLES): idle `hover`, walk `drift`, windup `fan`, attack `fling`, hurt `flutter_back`, death
`come_apart`. Channels: `lunge`, `bob`, `tilt` (leaning: - forward), `flutter` (its amplitude), `trail` (the strips
streaming back), `fan` (the arm bundles, 0..1), `fling` (the near bundle's swing, degrees), `glow` (the eyes'), `scatter`
(the strips flying apart as it dies).
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..motion import headon
from ..sculpt import E, Pose, rot, v3

STYLES = {
    "hover": {"bob": (0.0, 0.3, 0.5, 0.3, 0.0, -0.2), "flutter": (1.0,) * 6},
    "drift": {"kind": "drift", "tilt_amp": -8.0, "flutter": (1.4,) * 8, "trail": (1.0,) * 8},
    "fan": {"lunge": (-0.3, -0.7, -1.0, -1.1), "tilt": (4.0, 8.0, 9.0, 9.0), "bob": (0.2, 0.5, 0.6, 0.6), "fan": (0.4, 0.8, 1.0, 1.0),
            "glow": (1.0, 2.0, 2.0, 2.0), "flutter": (1.2, 1.2, 1.0, 1.0)},
    "fling": {"lunge": (-0.6, 1.4, 1.2, 0.6, 0.2, 0.0), "tilt": (6.0, -10.0, -8.0, -4.0, -1.0, 0.0), "fan": (0.8, 0.3, 0.2, 0.1, 0.0, 0.0),
              "fling": (35.0, -25.0, -20.0, -10.0, -4.0, 0.0), "glow": (2.0, 2.0, 1.0, 0.0, 0.0, 0.0), "release": 1,
              "flutter": (1.2, 1.6, 1.4, 1.2, 1.0, 1.0)},
    "flutter_back": {"lunge": (-2.4, -1.4, -0.4), "tilt": (14.0, 8.0, 2.0), "flutter": (2.2, 1.6, 1.2), "trail": (-0.8, -0.4, 0.0),
                     "squint": True},
    "come_apart": {"lunge": (-1.4, -1.6, -1.6, -1.6, -1.6, -1.6, -1.6, -1.6), "tilt": (12.0, 8.0, 4.0, 2.0, 0.0, 0.0, 0.0, 0.0),
                   "flutter": (2.4, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0), "trail": (-0.8,) + (0.0,) * 7,
                   "scatter": (0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.88, 1.0), "dark_from": 1},
}

TALISMAN = {
    "Z": 8.6,                                     # the hood's middle over the floor it hovers over
    "hood": {"r": (2.6, 2.8, 3.1), "strips": 7},
    # The face: a dark hollow under the hood's brow, two eyes glowing in it, and a talisman hanging over it from the brow
    # (its red seal at the top, a column of red script down it).
    "face": {"at": (2.05, 0.0, -0.55), "r": (0.95, 1.85, 1.95), "eyes": (2.95, 0.78, -0.05),
             "strip": {"root": (3.05, 0.0, 1.35), "length": 3.5, "width": 1.0}},
    "skirt": {"n": 8, "ring": (2.6, 2.7, -2.0), "length": 6.8, "width": 1.25},
    "arms": {"at": (0.2, 3.2, -0.6), "n": 3, "length": 4.6, "width": 1.1},
    "wisps": 5,
}
VARIANTS = {
    "talisman": {"parts": TALISMAN, "mats": {"paper": "talisman", "old": "talisman_old", "ink": "cinnabar", "void": "soul_void"},
                 "motion": {"idle": "hover", "walk": "drift", "windup": "fan", "attack": "fling", "hurt": "flutter_back",
                            "death": "come_apart"}},
}


def _strip(P, root, d, side, length, width, mat, group, flutter, ph, ink, n=3, scatter=0.0, k=0, torn=True, seal=False):
    """One talisman strip from `root` along `d` (its fall), its flat face toward `side` x `d`: n flat plates down a gently
    waving line, each a thin slab cut square (a strip of paper, not a ribbon of flesh); a column of red script down its
    middle, a red seal at its top (`seal`), its end torn ragged. Scattering, its plates drift apart."""
    d = d / np.linalg.norm(d)
    side = side / np.linalg.norm(side)
    nrm = np.cross(d, side)
    prev = root
    hw = width * 0.5
    for i in range(n):
        t = (i + 1) / n
        wave = math.sin(ph + t * 2.4 + k * 0.9) * flutter * 0.45 * t
        q = root + d * length * t + nrm * wave
        if scatter > 0.0:
            q = q + (np.array((math.cos(k * 1.7 + i), math.sin(k * 2.3 + i), 0.6)) * scatter * (3.0 + 2.0 * i))
        mid = (prev + q) * 0.5
        seg = q - prev
        ln = float(np.linalg.norm(seg)) or 1e-6
        a = seg / ln
        b = side - a * float(side @ a)
        b = b / (np.linalg.norm(b) or 1.0)
        c = np.cross(a, b)
        hl = ln * 0.5 + 0.2                                  # a little over the next plate, so the strip runs on
        s0 = i * ln - 0.2                                    # where along the strip this plate starts
        last = i == n - 1

        def clip(qs, mid=mid, a=a, b=b, hl=hl, last=last):
            rel = qs - mid
            u, v = rel @ a, rel @ b
            keep = (np.abs(u) <= hl) & (np.abs(v) <= hw)
            if last and torn:                                # the torn end: ragged, in two or three tongues
                keep &= u <= hl - 0.45 - 0.45 * np.sin(v * 5.3 + k * 1.9)
            return keep

        def script(qs, nn, mid=mid, a=a, b=b, hl=hl, s0=s0, first=i == 0):
            rel = qs - mid
            u, v = rel @ a, rel @ b
            along = u + hl + s0                              # from the strip's top
            col = np.abs(v) < hw * 0.32
            stroke = ((along * 1.45 + k * 0.37) % 1.0) < 0.62
            red = col & stroke & (along > 0.55)
            if seal and first:
                red |= (along < 0.75) & (np.abs(v) < hw * 0.7)
            return np.where(red, ink, mat).astype(object), np.zeros(len(qs), dtype=np.int16)

        m_ = np.stack([a, b, c], axis=1)
        P.add(E(mid, (hl * 1.42, hw * 1.42, 0.16), mat, group, m_, script if (ink is not None and scatter < 0.5) else None, clip))
        prev = q
    return prev


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    fr, bk = headon(view)
    lunge = B.pick("lunge", action, f)
    bob = B.pick("bob", action, f)
    tilt = B.pick("tilt", action, f)
    flutter = B.pick("flutter", action, f, 1.0)
    trail = B.pick("trail", action, f)
    fan = B.pick("fan", action, f)
    fling = B.pick("fling", action, f)
    glow = B.pick("glow", action, f)
    scatter = B.pick("scatter", action, f)
    ph = f / 6.0 * math.tau if action == "idle" else f * 1.05
    if st.get("kind") == "drift":
        tilt = st.tilt_amp + 1.0 * math.sin(f / 8.0 * math.tau)
        bob = 0.4 * math.sin(f / 8.0 * math.tau)
    C = v3(lunge, 0.0, p.Z + bob)
    bm = rot("b", -tilt)
    at = lambda q: C + bm @ v3(q)
    dark = action == "death" and f >= st.get("dark_from", 99)
    # The skirt: strips round the hood's rim, falling, streaming back as it drifts; the back ones darker (old paper).
    sk = p.skirt
    for i in range(sk.n):
        ang = math.radians(-150.0 + 300.0 * i / (sk.n - 1))
        ra, rb, rc = sk.ring
        root = at((ra * math.cos(ang) * 0.9, rb * math.sin(ang), rc))
        out = np.array((math.cos(ang), math.sin(ang), 0.0))
        fall = bm @ (np.array((0.0, 0.0, -1.0)) + out * 0.25 + np.array((-0.6 * trail, 0.0, 0.0)))
        side = bm @ np.array((-math.sin(ang), math.cos(ang), 0.0))
        old = math.cos(ang) < -0.2 or i % 2 == 1
        _strip(P, root, fall, side, sk.length * (0.8 + 0.2 * ((i * 7) % 3) / 2.0), sk.width, m.old if old else m.paper, "skirt%d" % i,
               flutter, ph, m.ink, scatter=scatter, k=i)
    # The hood: a dome of wrapped strips, its seams a step dark.
    hd = p.hood

    def wrapped(q, n):
        loc = (q - C) @ bm
        u = (np.arctan2(loc[:, 1], loc[:, 0]) * hd.strips / math.tau + loc[:, 2] * 0.18) % 1.0
        seam = u < 0.14
        old = (np.floor(np.arctan2(loc[:, 1], loc[:, 0]) * hd.strips / math.tau + loc[:, 2] * 0.18) % 2) == 1
        return np.full(len(q), m.old, dtype=object), np.where(seam, -2, np.where(old, -1, 0)).astype(np.int16)

    if scatter < 0.75:
        hood_c = C + v3(0.0, 0.0, 3.0 * scatter)
        P.add(E(hood_c, tuple(r * (1.0 - 0.4 * scatter) for r in hd.r), m.paper, "hood", bm, wrapped))
        # The face: a dark hollow under the brow, its eyes glowing violet in it (flaring in the tell, squeezed when
        # struck, dark as it dies), and the face talisman hanging over it from the brow, its seal at the top.
        fc = p.face
        P.add(E(at(fc.at), fc.r, m.void, "face", bm, line=False))
        for s in (1, -1):
            spot = at((fc.eyes[0], s * fc.eyes[1], fc.eyes[2]))
            if dark:
                continue
            elif st.get("squint"):
                P.mark(spot, M.GHOST_GLOW)
            else:
                P.eye(spot, M.GHOST_GLOW_HI if glow >= 1.0 else M.GHOST_GLOW)
                P.mark(spot + bm @ v3(0.0, 0.0, -0.45), M.GHOST_GLOW)
                if glow >= 1.0:
                    for dd in ((0.3, 0.0, 0.7), (0.3, s * 0.7, 0.2), (0.3, 0.0, -0.9)):
                        P.glow.append((spot + bm @ v3(*dd), M.GHOST_AURA))
        fs = fc.strip
        sway = 0.12 * flutter * math.sin(ph * 0.9)
        _strip(P, at(fs.root), bm @ np.array((0.18 + sway, 0.0, -1.0)), bm @ np.array((0.0, 1.0, 0.0)), fs.length, fs.width,
               m.paper, "face_strip", flutter * 0.4, ph, m.ink, n=2, scatter=scatter, k=21, seal=True)
    # The arm bundles: at its sides, fanned out behind in the tell, the near one flung forward on the blow.
    ar = p.arms
    for s in (1, -1):
        root = at((ar.at[0], s * ar.at[1], ar.at[2]))
        swing = fling if s > 0 else 0.0
        for j in range(ar.n):
            spread = (j - (ar.n - 1) / 2.0) * (14.0 + 30.0 * fan)
            el = -70.0 + 95.0 * fan + spread * 0.4
            az = 180.0 - 60.0 * fan - spread * 0.6 - swing
            dvec = bm @ (rot("c", s * az) @ rot("b", el) @ np.array((1.0, 0.0, 0.0)))
            side = bm @ (rot("c", s * az) @ np.array((0.0, 1.0, 0.0)))
            if action == "attack" and s > 0 and j == ar.n - 1 and f >= st.get("release", 99):
                continue                                     # the flung talisman has left the bundle
            _strip(P, root, dvec, side, ar.length * (1.0 - 0.15 * abs(j - 1)), ar.width, m.paper, "arm%d" % s, flutter, ph + j, m.ink, n=2,
                   scatter=scatter, k=10 + j + 3 * (s > 0))
    # Soul wisps rising off it.
    for k in range(p.wisps):
        ang = math.radians(k * 72.0 + f * 25.0)
        rr = 3.4 + (k % 2) * 0.8
        hgt = (f * 0.9 + k * 1.7) % 6.0
        P.glow.append((C + v3(math.cos(ang) * rr * 0.7, math.sin(ang) * rr, -1.0 + hgt), M.GHOST_GLOW if k % 2 else M.GHOST_AURA))
    if action == "attack" and f == st.get("release", -1):
        tip = at((4.0, 2.0, 0.0))
        for dd in ((0.0, 0.0, 0.0), (0.8, 0.0, 0.4), (1.6, 0.0, 0.8)):
            P.glow.append((tip + v3(*dd), M.GHOST_GLOW))
    if scatter > 0.0:
        P.dissolve = scatter * 0.85
        P.dissolve_col = M.GHOST_GLOW
    return P
