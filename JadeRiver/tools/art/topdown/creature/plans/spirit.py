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
from ..sculpt import E, L, Pose, S, on, rot, v3

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
    if "shards" in B.parts:
        return _wisp(B, action, f, view)
    if "globe" in B.parts:
        return _lantern(B, action, f, view)
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


# ================================================================================================= the wisp and the lantern (M2)
# The mirror wisp: a single great eye floating in a ring of mirror-bright crystal shards (`shards`); the weeping lantern: a
# haunted paper lantern with a sad painted face, a violet soul flame inside, crying wax tears (`globe`). Channels: `bob`,
# `lunge`, `tilt`, `spin` (the shards' turn round the eye, degrees), `lens` (0..1: the shards swung round before the eye
# into a lens), `glow` (the eye's, the flame's), `scatter` (0..1: flying apart as it dies), `flare` (the lantern's flame
# out of its top), `burst` (a ring of light thrown off on the blow), `crumple` (the paper crushed as it dies), `drop`
# (fallen to the floor), `squint`.
SPIRIT2_STYLES = {
    "orbit": {"spin": (0.0, 10.0, 20.0, 30.0, 40.0, 50.0), "bob": (0.0, 0.3, 0.5, 0.3, 0.0, -0.2)},
    "drift_orbit": {"spin": (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0, 105.0), "bob": (0.0, 0.3, 0.5, 0.3, 0.0, -0.3, -0.5, -0.3),
                    "tilt": (-6.0,) * 8},
    "lens": {"lens": (0.3, 0.65, 0.9, 1.0), "glow": (0.5, 1.0, 1.5, 2.0), "spin": (0.0, 20.0, 35.0, 40.0), "lunge": (-0.3, -0.6, -0.8, -0.9),
             "bob": (0.2, 0.4, 0.5, 0.5)},
    "flash": {"lens": (1.0, 0.6, 0.3, 0.1, 0.0, 0.0), "glow": (2.0, 2.0, 1.0, 0.5, 0.0, 0.0), "burst": (0.0, 1.0, 1.6, 0.0, 0.0, 0.0),
              "spin": (40.0, 60.0, 80.0, 90.0, 100.0, 110.0), "scatter": (0.0, 0.25, 0.15, 0.05, 0.0, 0.0), "lunge": (-0.9, 0.6, 0.6, 0.3, 0.1, 0.0)},
    "jolt": {"scatter": (0.35, 0.15, 0.0), "lunge": (-2.2, -1.2, -0.4), "tilt": (14.0, 6.0, 0.0), "squint": True, "spin": (0.0, -12.0, -18.0)},
    "shatter": {"scatter": (0.0, 0.15, 0.35, 0.55, 0.75, 0.9, 1.0, 1.0), "crack": (0.3, 0.7, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
                "spin": (0.0, 10.0, 25.0, 40.0, 50.0, 55.0, 58.0, 60.0), "dark_from": 2},
    # the lantern
    "sway_hang": {"bob": (0.0, 0.3, 0.5, 0.3, 0.0, -0.2), "tilt": (2.0, 3.0, 2.0, 0.0, -2.0, -1.0), "tears": True},
    "drift_hang": {"bob": (0.0, 0.3, 0.5, 0.3, 0.0, -0.3, -0.5, -0.3), "tilt": (-8.0,) * 8, "tears": True},
    "flame_rise": {"flare": (0.3, 0.6, 0.9, 1.0), "glow": (0.5, 1.0, 1.5, 2.0), "bob": (0.2, 0.5, 0.7, 0.8), "tilt": (2.0, 4.0, 5.0, 5.0)},
    "flare_burst": {"flare": (1.0, 0.8, 0.5, 0.3, 0.1, 0.0), "glow": (2.0, 2.0, 1.2, 0.6, 0.2, 0.0), "burst": (0.0, 1.0, 1.5, 1.9, 0.0, 0.0),
                    "bob": (0.6, 0.0, 0.0, 0.2, 0.3, 0.2), "squash": {1: (1.08, 1.08, 0.9)}},
    "swing_back": {"lunge": (-2.0, -1.2, -0.4), "tilt": (18.0, 8.0, 2.0), "squint": True, "bob": (0.6, 0.3, 0.1)},
    "gutter_out": {"crumple": (0.0, 0.15, 0.3, 0.45, 0.6, 0.7, 0.75, 0.75), "drop": (0.0, 0.1, 0.25, 0.45, 0.7, 0.9, 1.0, 1.0),
                   "tilt": (10.0, 18.0, 26.0, 36.0, 48.0, 60.0, 66.0, 68.0), "flare": (0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), "dark_from": 2},
}
STYLES.update(SPIRIT2_STYLES)
WISP = {"Z": 10.5, "eye": 3.0, "socket": (3.45, 14), "shards": {"n": 8, "orbit": 6.0, "r": (1.9, 0.85, 0.2), "tilt": 24.0}, "halo": 10}
LANTERN = {"Z": 12.5, "globe": (3.3, 3.3, 4.1), "ribs": 8, "cap": ((0.0, 0.0, 4.0), (1.55, 1.55, 0.6)), "bottom": ((0.0, 0.0, -4.1), (1.35, 1.35, 0.5)),
           "loop": 1.0, "tassel": {"length": 4.2, "n": 4}}
VARIANTS.update({
    "wisp": {"parts": WISP, "mats": {"shard": "mirror_shard", "back": "mirror_shard_back", "socket": "wisp_socket", "sclera": "wisp_sclera",
                                     "iris": "wisp_iris", "pupil": "wisp_pupil"},
             "motion": {"idle": "orbit", "walk": "drift_orbit", "windup": "lens", "attack": "flash", "hurt": "jolt", "death": "shatter"}},
    "lantern": {"parts": LANTERN, "mats": {"paper": "lantern_paper", "cap": "lantern_cap", "tassel": "lantern_tassel", "wax": "wax"},
                "motion": {"idle": "sway_hang", "walk": "drift_hang", "windup": "flame_rise", "attack": "flare_burst", "hurt": "swing_back",
                           "death": "gutter_out"}},
})


def _shard_paint(m, centre, a, b, mat):
    """A mirror shard: a kite split into a lit facet and a shaded one along its length, its rim a white mirror glint."""
    def paint(q, n):
        rel = q - centre
        u = rel @ a
        v = rel @ b
        lit = v > 0.0
        names = np.full(len(q), mat, dtype=object)
        return names, np.where(lit, 1, -1).astype(np.int16)
    return paint


def _wisp(B, action: str, f: int, view: float) -> Pose:
    """M2, the mirror wisp: a great eye floating (a pale sclera, a violet iris and its dark pupil looking ahead, a dark socket
    ring round it, a faint violet halo), ringed by mirror-bright crystal shards orbiting it on a tilted ring; in its tell
    the shards swing round before the eye into a lens as the eye glows; it flashes (a burst of soul light ahead, the
    blow); struck, the shards jolt out; beaten, the eye cracks and everything shatters outward and fades."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lunge = B.pick("lunge", action, f)
    bob = B.pick("bob", action, f)
    tilt = B.pick("tilt", action, f)
    spin = B.pick("spin", action, f)
    lens = B.pick("lens", action, f)
    glow = B.pick("glow", action, f)
    scatter = B.pick("scatter", action, f)
    crack = B.pick("crack", action, f)
    burst = B.pick("burst", action, f)
    C = v3(lunge, 0.0, p.Z + bob)
    bm = rot("b", -tilt)
    dark = action == "death" and f >= st.get("dark_from", 99)
    R = p.eye
    # The eye: the sclera, the iris and pupil ahead, the socket ring round it (in the plane facing ahead).
    P.add(S(C, R, m.sclera, "eye"))
    if not dark:
        P.add(E(C + bm @ v3(R * 0.74, 0.0, 0.0), (0.7, R * 0.64, R * 0.64), m.iris, "iris", bm, line=False))
        P.add(E(C + bm @ v3(R * 0.9, 0.0, 0.0), (0.4, R * 0.3, R * 0.3 * (0.4 if st.get("squint") else 1.0)), m.pupil, "pupil", bm,
                line=False))
        P.eye(C + bm @ v3(R + 0.15, -0.5, 0.6), M.WISP_GLINT)
    else:
        P.add(E(C + bm @ v3(R * 0.82, 0.0, 0.0), (0.45, R * 0.5, R * 0.5), m.socket, "iris", bm, line=False))
    if crack > 0.0:
        for k in range(int(3 + 6 * crack)):
            ang = math.radians(k * 53.0 + 20.0)
            for t in (0.4, 0.7, 1.0):
                q = C + bm @ v3(R * math.sqrt(max(0.0, 1.0 - (t * 0.8) ** 2)), math.cos(ang) * R * t * 0.8, math.sin(ang) * R * t * 0.8)
                P.mark(q + bm @ v3(0.2, 0.0, 0.0), M.WISP_CRACK)
    sk, sn = p.socket
    for k in range(sn):
        ang = math.radians(k * 360.0 / sn)
        P.add(S(C + bm @ v3(-0.2, math.cos(ang) * sk, math.sin(ang) * sk), 0.55, m.socket, "socket", line=False))
    # The shards: orbiting on a ring tilted toward the camera, a kite each; in the lens they gather before the eye in a
    # ring facing ahead; scattering, they fly outward.
    sh = p.shards
    for k in range(sh.n):
        ang = math.radians(k * 360.0 / sh.n + spin)
        ring = rot("a", sh.tilt) @ v3(math.cos(ang) * sh.orbit, math.sin(ang) * sh.orbit, 0.0)
        lens_q = v3(R + 2.4, math.cos(ang) * 2.9, math.sin(ang) * 2.9)
        q = ring * (1.0 - lens) + lens_q * lens
        q = q * (1.0 + 1.6 * scatter) + v3(0.0, 0.0, -scatter * 6.0 * (k % 3) / 2.0 * (1.0 if action == "death" else 0.0))
        pos = C + bm @ q
        out = q / max(1e-6, float(np.linalg.norm(q)))
        # A shard's length stands up round the ring, leaning out (a crown of crystals), or points ahead in the lens; its flat
        # face toward the eye.
        a_ = (v3(0.0, 0.0, 1.0) * 0.85 + out * 0.45) * (1.0 - lens) + v3(1.0, 0.0, 0.0) * lens
        a_ = bm @ (a_ / max(1e-6, float(np.linalg.norm(a_))))
        b_ = np.cross(a_, v3(0.0, 0.0, 1.0))
        if float(np.linalg.norm(b_)) < 0.2:
            b_ = v3(0.0, 1.0, 0.0)
        b_ = b_ / float(np.linalg.norm(b_))
        c_ = np.cross(a_, b_)
        mm = np.stack([a_, b_, c_], axis=1) @ rot("a", 50.0 + k * 20.0 + spin * 0.5)
        back = float((pos - C) @ v3(1.0, 0.0, 0.0)) < -1.0
        mat = m.back if back else m.shard
        r = sh.r
        P.add(E(pos, (r[0] * (0.85 + 0.15 * (k % 3)), r[1], r[2]), mat, "shard%d" % k, mm, _shard_paint(m, pos, mm[:, 0], mm[:, 1], mat)))
        P.mark(pos + mm @ v3(r[0] * 0.7, 0.0, r[2] + 0.1), M.WISP_GLINT)
    # A faint violet halo round it, and its glow (in the tell) and the flash (the blow).
    for k in range(p.halo):
        ang = math.radians(k * 36.0 + f * 17.0)
        rr = R + 1.6 + (k % 2) * 0.6
        P.glow.append((C + v3(math.cos(ang) * rr * 0.5, math.sin(ang) * rr, math.cos(ang * 1.7) * rr * 0.6), M.GHOST_AURA))
    if glow >= 1.0 and not dark:
        for k in range(8):
            ang = math.radians(k * 45.0)
            P.glow.append((C + bm @ v3(R + 0.6, math.cos(ang) * 1.4, math.sin(ang) * 1.4), M.GHOST_GLOW_HI if k % 2 else M.GHOST_GLOW))
    if burst > 0.0:
        for k in range(14):
            ang = math.radians(k * 360.0 / 14)
            for t in range(3):
                d = 2.0 + burst * 3.0 + t * 1.2
                P.glow.append((C + bm @ v3(R + d, math.cos(ang) * (1.0 + burst * 1.4 + t * 0.4), math.sin(ang) * (1.0 + burst * 1.4 + t * 0.4)),
                               M.GHOST_GLOW_HI if t == 0 else M.GHOST_GLOW))
    if action == "death":
        P.dissolve = scatter * 0.9
        P.dissolve_col = M.GHOST_GLOW
    return P


def _lantern(B, action: str, f: int, view: float) -> Pose:
    """M2, the weeping lantern: a paper lantern floating, lit from inside by a violet soul flame (its silhouette dark
    through the paper), bamboo ribs down it, a sad face painted on its front (drooping brows, closed weeping eyes, a frown,
    tear streaks), a dark red cap and base, a hanging loop over it and a red tassel swaying under it, wax dripping off its
    rim and tears falling. In its tell the flame flares up out of its top; on the blow it throws a ring of soul fire round
    it; struck, it swings back; beaten, its paper crumples, the flame gutters out and it drops."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lunge = B.pick("lunge", action, f)
    bob = B.pick("bob", action, f)
    tilt = B.pick("tilt", action, f)
    flare = B.pick("flare", action, f)
    glow = B.pick("glow", action, f)
    burst = B.pick("burst", action, f)
    crumple = B.pick("crumple", action, f)
    drop = B.pick("drop", action, f)
    gx, gy, gz = p.globe
    z = (p.Z + bob) * (1.0 - drop) + drop * gz * 0.8
    C = v3(lunge, 0.0, z)
    bm = rot("b", -tilt)
    dark = action == "death" and f >= st.get("dark_from", 99)

    def paper(q, n):
        """The paper: lit from inside (a step lighter round its middle, a step darker toward the caps), the ribs dark down it,
        the flame's dark shape through it."""
        loc = (q - C) @ bm
        nl = n @ bm
        ang = np.arctan2(loc[:, 1], loc[:, 0])
        rib = (np.abs(((ang / math.tau * p.ribs) % 1.0) - 0.5) > 0.44)
        zr = loc[:, 2] / gz
        y, zz = loc[:, 1], loc[:, 2]
        flame = (np.abs(y) < 0.9 - 0.3 * zz) & (zz > -1.6) & (zz < 1.4) & (nl[:, 0] < 0.55) & (nl[:, 0] > -0.2)
        names = np.full(len(q), m.paper, dtype=object)
        bias = np.where(rib, -1, np.where(np.abs(zr) < 0.45, 1, np.where(np.abs(zr) > 0.8, -1, 0)))
        if not dark:
            bias = np.where(flame, bias - 1, bias)
        return names, bias.astype(np.int16)

    crush = 1.0 - 0.35 * crumple
    grad = (gx * crush, gy * (1.0 - 0.15 * crumple), gz * (1.0 - 0.25 * crumple))
    gm = bm @ rot("a", 20.0 * crumple)
    P.add(E(C, grad, m.paper, "globe", gm, paper))
    # The sad face painted on its front in ink: drooping brows, closed weeping eyes, a frown, tear streaks down the paper.
    if action != "death" or f < 5:
        ink = M.LANTERN_INK
        for s in (1, -1):
            for u, v in ((10.0, 34.0), (18.0, 31.0), (26.0, 29.0)):                 # the brows, raised at their inner ends
                P.mark(on(C, grad, gm, s * u, v), ink)
            for u, v in ((13.0, 15.0), (19.0, 18.0), (25.0, 18.0), (31.0, 15.0)):   # the closed eyes, arcs
                P.mark(on(C, grad, gm, s * u, v), ink)
            for v in (10.0, 4.0, -2.0, -8.0):                                        # tear streaks
                P.mark(on(C, grad, gm, s * (24.0 + 0.2 * v), v), M.LANTERN_TEAR)
        for u, v in ((0.0, -16.0), (6.0, -17.0), (-6.0, -17.0), (11.0, -20.0), (-11.0, -20.0)):   # the frown
            P.mark(on(C, grad, gm, u, v), ink)
    (ca, cr), (ba, br) = p.cap, p.bottom
    P.add(E(C + bm @ v3(ca), cr, m.cap, "cap", bm), E(C + bm @ v3(ba), br, m.cap, "base", bm))
    # The hanging loop over the cap.
    top = C + bm @ v3(0.0, 0.0, ca[2] + cr[2])
    lp = p.loop
    prev = top
    for k in range(1, 7):
        ang = math.radians(k * 30.0)
        q = top + bm @ v3(0.0, -lp + lp * math.cos(ang), lp * math.sin(ang) * 1.2)
        P.add(L(prev, q, 0.25, 0.25, m.cap, "loop", line=False))
        prev = q
    # The tassel under it, swaying.
    t = p.tassel
    sw = 0.7 * math.sin(f * 1.1) + (0.0 if action != "walk" else -0.9)
    base = C + bm @ v3(ba[0], 0.0, ba[2] - br[2])
    q0 = base
    for k in range(1, t.n + 1):
        q = base + v3(sw * 0.35 * k * (1.0 - drop), 0.0, -t.length * k / t.n * (1.0 - 0.8 * drop))
        last = k == t.n
        # A cord, a knot, and the tassel's fringe flaring at its end.
        P.add(L(q0, q, 0.45 if last else 0.24, 0.95 if last else 0.24, m.tassel, "tassel", line=last))
        if k == t.n - 1:
            P.add(S(q, 0.5, m.tassel, "tassel"))
        q0 = q
    # Wax dripping off the rim, tears falling from its eyes.
    for k in range(5):
        ang = math.radians(k * 72.0 + 15.0)
        P.mark(C + bm @ v3(math.cos(ang) * cr[0] * 0.9, math.sin(ang) * cr[1] * 0.9, ca[2] - cr[2] - 0.3), M.RAMPS[m.wax][3])
    if st.get("tears") and not dark:
        for s in (1, -1):
            u = ((f * 0.37 + (0.5 if s > 0 else 0.0)) % 1.0)
            P.fx.append((on(C, grad, gm, s * 26.0, -12.0) + v3(0.4, 0.0, -u * 6.0), M.LANTERN_TEAR))
    # The soul flame: a flicker over its cap always, flaring up out of its top in the tell.
    if not dark:
        hgt = 0.8 + 5.0 * flare
        nf = 8 + int(16 * flare)
        for k in range(nf):
            ph = (k * 1.7 + f * 2.3) % 6.28
            w_ = (0.5 + 0.9 * flare) * (1.0 - k / (nf + 4.0))
            q = top + v3(w_ * math.cos(ph), w_ * 1.2 * math.sin(ph * 1.3), 0.3 + hgt * (k / float(nf)))
            P.glow.append((q, M.SOUL_FLAME_CORE if k < 3 else (M.SOUL_FLAME if k % 3 else M.SOUL_FLAME_DEEP)))
    if glow >= 1.0 and not dark:
        for k in range(10):
            ang = math.radians(k * 36.0 + f * 11.0)
            P.glow.append((C + v3(math.cos(ang) * (gx + 1.2) * 0.6, math.sin(ang) * (gy + 1.2), math.sin(ang * 2.0) * 1.5), M.GHOST_AURA))
    if burst > 0.0:
        rr = 4.0 + burst * 4.0
        for k in range(24):
            ang = math.radians(k * 15.0)
            P.glow.append((v3(lunge + math.cos(ang) * rr, math.sin(ang) * rr * 1.1, 0.6 + (k % 2) * 0.8), M.SOUL_FLAME if k % 2 else M.SOUL_FLAME_CORE))
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (lunge, 0.0, z))
    return P
