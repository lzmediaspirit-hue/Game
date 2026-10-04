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

`jelly` (M4, the star jellyfish): no hood, strips or arms but a bell (`bell`: a translucent dome over a flat underside,
radial canals, a frill round its rim, a star glowing at its crown), trailing tentacles and oral arms that sway as it
drifts and pulses: see "the star jellyfish" below. Its styles: idle `pulse_drift`, walk `pulse_swim`, windup
`clench_glow`, attack `lash_sting`, hurt `dent_flicker`, death `deflate_sink`.
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
    if "bell" in B.parts:
        return _jelly(B, action, f, view)                # M4: the star jellyfish
    if "sail" in B.parts:
        return _kite(B, action, f, view)
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


# ================================================================================================= the star jellyfish (M4)
# A drifting jellyfish of starlight (`bell`): a translucent indigo-violet bell (a dome over a flat underside, radial canals,
# a glassy highlight arc) with a pale-gold star glowing in it, a magenta frill of scallops round its rim, two short magenta
# oral arms and four long pale tentacles with stars twinkling down them. Channels: `bob`, `lunge`, `tilt`, `pulse` (the
# bell contracting: taller and narrower, + ; relaxed, wider: -), `curl` (the tentacles curled up and forward, 0..1),
# `lash` (thrown forward in a stinging arc, 0..1), `trail` (streaming back), `star` (its light: 0 dark .. 2 flaring),
# `ring` (the double ring of star glow round it, its reach), `sting` (the spark burst at the tips), `sag` (deflating as it
# dies), `drop` (sunk to the floor), `squint`.
JELLY_STYLES = {
    "pulse_drift": {"pulse": (0.0, 0.25, 0.45, 0.3, 0.0, -0.2), "bob": (0.0, 0.3, 0.5, 0.4, 0.1, -0.2), "star": (1.0,) * 6},
    "pulse_swim": {"pulse": (0.0, 0.3, 0.5, 0.3, 0.0, -0.25, -0.35, -0.2), "bob": (0.0, 0.2, 0.5, 0.6, 0.4, 0.1, -0.1, -0.1),
                   "tilt": (-10.0,) * 8, "trail": (0.4, 0.6, 0.8, 0.7, 0.5, 0.4, 0.3, 0.3), "lunge": (0.0, 0.2, 0.5, 0.6, 0.5, 0.3, 0.1, 0.0),
                   "star": (1.0,) * 8},
    "clench_glow": {"pulse": (0.4, 0.8, 1.0, 1.0), "bob": (0.3, 0.6, 0.8, 0.8), "lunge": (-0.3, -0.6, -0.9, -1.0), "tilt": (6.0, 10.0, 12.0, 12.0),
                    "curl": (0.3, 0.6, 0.9, 1.0), "star": (1.4, 1.8, 2.0, 2.0), "ring": (0.4, 0.8, 1.0, 1.1)},
    "lash_sting": {"pulse": (-0.6, -0.5, -0.3, -0.1, 0.0, 0.0), "lunge": (0.4, 1.6, 1.6, 1.0, 0.4, 0.0), "tilt": (-10.0, -16.0, -12.0, -6.0, -2.0, 0.0),
                   "lash": (0.5, 1.0, 0.9, 0.6, 0.3, 0.1), "curl": (0.4, 0.0, 0.0, 0.0, 0.0, 0.0), "star": (2.0, 1.6, 1.2, 1.0, 1.0, 1.0),
                   "sting": (1, 2), "bob": (0.6, 0.2, 0.1, 0.0, 0.0, 0.0)},
    "dent_flicker": {"pulse": (-0.7, -0.3, 0.0), "lunge": (-2.0, -1.2, -0.4), "tilt": (16.0, 8.0, 2.0), "trail": (-0.6, -0.3, 0.0),
                     "star": (0.3, 0.7, 1.0), "squint": True},
    "deflate_sink": {"sag": (0.0, 0.15, 0.3, 0.5, 0.7, 0.85, 0.95, 1.0), "drop": (0.0, 0.1, 0.25, 0.45, 0.65, 0.8, 0.9, 1.0),
                     "star": (0.6, 0.4, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0), "tilt": (8.0, 12.0, 16.0, 18.0, 18.0, 18.0, 18.0, 18.0),
                     "dissolve": (0.0, 0.0, 0.0, 0.0, 0.15, 0.35, 0.6, 0.85)},
}
STYLES.update(JELLY_STYLES)
JELLY = {"Z": 12.0, "bell": {"r": (4.4, 4.4, 3.5), "cut": 0.3, "canals": 8}, "frill": 14,
         "tentacles": {"n": 4, "length": 10.0, "r": (0.5, 0.18), "segs": 9, "ring": 0.78},
         "arms": {"n": 2, "length": 5.5, "r": (0.75, 0.3), "segs": 6}}
VARIANTS["jelly"] = {"parts": JELLY, "mats": {"bell": "sj_bell", "frill": "sj_frill", "tentacle": "sj_tentacle"},
                     "motion": {"idle": "pulse_drift", "walk": "pulse_swim", "windup": "clench_glow", "attack": "lash_sting", "hurt": "dent_flicker",
                                "death": "deflate_sink"}}


def _strand(P, root, length, segs, r, mat, group, heading, wave, ph, side, line=True):
    """A hanging strand from `root`: it heads down (heading -90 degrees in the plane of `side`'s normal and up), turning by
    `heading(t)` (degrees at t along it), waving across by `wave` (its amplitude, growing toward its tip); returns its
    points."""
    pts = [np.asarray(root, float)]
    q = np.asarray(root, float)
    fwd, up = np.asarray(side[0], float), v3(0.0, 0.0, 1.0)
    across = np.asarray(side[1], float)
    step = length / segs
    for i in range(segs):
        t = (i + 0.5) / segs
        h = math.radians(heading(t))
        d = fwd * math.cos(h) + up * math.sin(h)
        q = q + d * step + across * (wave * math.cos(ph + t * 4.0) * step * 0.6 * t)
        pts.append(q.copy())
    for i in range(segs):
        r0 = r[0] + (r[1] - r[0]) * i / segs
        r1 = r[0] + (r[1] - r[0]) * (i + 1) / segs
        P.add(L(pts[i], pts[i + 1], r0, r1, mat, group, line=line, caps=i == 0 or i == segs - 1))
    return pts


def _jelly(B, action: str, f: int, view: float) -> Pose:
    """M4, the star jellyfish (see JELLY_STYLES): it drifts and pulses, its tentacles swaying; in its tell its bell
    clenches, its star flares and a double ring of star glow opens round it as its tentacles curl up and forward; it lashes
    them forward in a stinging arc (sparks bursting at their tips); struck, its bell dents and its star flickers; beaten,
    it deflates, its star gutters out and it sinks, fading."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lunge = B.pick("lunge", action, f)
    bob = B.pick("bob", action, f)
    tilt = B.pick("tilt", action, f)
    pulse = B.pick("pulse", action, f)
    curl = B.pick("curl", action, f)
    lash = B.pick("lash", action, f)
    trail = B.pick("trail", action, f)
    star = B.pick("star", action, f, 1.0)
    ring = B.pick("ring", action, f)
    sag = B.pick("sag", action, f)
    drop = B.pick("drop", action, f)
    bl = p.bell
    R, H = bl.r[0] * (1.0 - 0.14 * pulse + 0.2 * sag), bl.r[2] * (1.0 + 0.22 * pulse - 0.45 * sag)
    z = (p.Z + bob) * (1.0 - drop) + drop * (H * 0.5 + 0.6)
    C = v3(lunge, 0.0, z)
    bm = rot("b", -tilt)
    cut = -bl.cut * H

    def bell(q, n):
        """The bell: its canals a step dark down it, a glassy arc lit over its front, a step lit round its crown (the
        star's halo inside it), its lower rim a step dark."""
        loc = (q - C) @ bm
        ang = np.arctan2(loc[:, 1], loc[:, 0])
        canal = ((ang / math.tau * bl.canals) % 1.0) < 0.12
        zz = loc[:, 2] / H
        halo = (zz > 0.55) & (np.hypot(loc[:, 0], loc[:, 1]) < R * 0.55)
        arc = (np.abs(np.hypot(loc[:, 0] - R * 0.15, loc[:, 1] + R * 0.2) - R * 0.62) < 0.35) & (zz > 0.2) & (loc[:, 0] > 0.0)
        low = zz < 0.0
        bias = np.where(arc, 2, np.where(halo, 1, np.where(canal | low, -1, 0)))
        return np.full(len(q), m.bell, dtype=object), bias.astype(np.int16)

    P.add(E(C, (R, R, H), m.bell, "bell", bm, bell, clip=lambda qs, c_=C, b_=bm: ((qs - c_) @ b_)[:, 2] > cut))
    rr = R * math.sqrt(max(0.0, 1.0 - bl.cut ** 2))
    P.add(E(C + bm @ v3(0.0, 0.0, cut + 0.05), (rr * 0.97, rr * 0.97, 0.3), m.bell, "under", bm, line=False))
    # The frill: magenta scallops round the rim, swaying.
    for k in range(p.frill):
        ang = math.radians(k * 360.0 / p.frill + f * 6.0)
        q = C + bm @ v3(math.cos(ang) * rr * 0.98, math.sin(ang) * rr * 0.98, cut - 0.35 - 0.15 * math.sin(f + k))
        P.add(S(q, 0.75, m.frill, "frill", line=False))
    # The tentacles and the oral arms: hanging from under the bell, swaying; streaming back as it swims; curled up and
    # forward in the tell; lashed forward in the sting.
    fwd = bm @ v3(1.0, 0.0, 0.0)
    fwd = fwd / float(np.linalg.norm(fwd))
    left = v3(0.0, 1.0, 0.0)
    ph = f / 6.0 * math.tau if action == "idle" else f * 0.9
    tips = []
    tn = p.tentacles
    for k in range(tn.n):
        ang = math.radians(45.0 + k * 360.0 / tn.n)
        root = C + bm @ v3(math.cos(ang) * rr * tn.ring, math.sin(ang) * rr * tn.ring, cut - 0.2)
        front = math.cos(ang)

        def heading(t, front=front):
            h = -90.0 - 40.0 * trail * t + curl * (60.0 + 150.0 * t) * (0.7 + 0.3 * front) + lash * (95.0 * t ** 0.6)
            h -= sag * 20.0 * t
            return h

        ln = tn.length * (1.0 - 0.25 * curl) * (1.0 - 0.6 * drop * min(1.0, f / 4.0) if action == "death" else 1.0)
        pts = _strand(P, root, ln, tn.segs, tn.r, m.tentacle, "tentacle%d" % k, heading, 1.2 + 0.8 * (1.0 - curl),
                      ph + k * 1.6, (fwd, left))
        tips.append(pts[-1])
        if star > 0.2 and action != "death":
            for j in range(2, len(pts), 2):
                if (j + f + k) % 3 == 0:
                    P.glow.append((pts[j] + v3(0.0, 0.0, 0.2), M.STAR_W if (j + f) % 2 else M.STAR_G))
    am = p.arms
    for k in range(am.n):
        side = 1.0 if k else -1.0
        root = C + bm @ v3(0.3, side * 0.9, cut - 0.25)

        def heading(t, side=side):
            return -90.0 - 30.0 * trail * t + curl * 80.0 * t + lash * 50.0 * t

        _strand(P, root, am.length * (1.0 - 0.3 * sag), am.segs, am.r, m.frill, "arm%d" % k, heading, 2.2, ph * 1.2 + k * 2.0, (fwd, left),
                line=False)
    # The star in its bell: a pale-gold star of light over its crown's front, flaring in the tell (rays), dim when struck,
    # going out as it dies.
    sc = C + bm @ v3(R * 0.2, 0.0, H * 1.02)
    if star > 0.05:
        # Seen through the crown from every side: light laid over it, a centre and five points.
        P.eye(sc, M.STAR_W if star >= 1.0 else M.STAR_G)
        P.glow.append((sc, M.STAR_W if star >= 1.0 else M.STAR_G))
        g, o = (M.STAR_G, M.STAR_O) if star >= 0.6 else (M.STAR_DIM, M.STAR_DIM)
        for d, col in (((0.0, 0.45, 0.0), g), ((0.0, -0.45, 0.0), g), ((0.0, 0.0, 0.5), g), ((0.0, 0.0, -0.45), g),
                       ((0.0, 0.9, 0.1), o), ((0.0, -0.9, 0.1), o), ((0.0, 0.0, 1.0), o), ((0.0, 0.55, -0.8), o), ((0.0, -0.55, -0.8), o)):
            P.glow.append((sc + v3(*d), col))
        if star >= 1.5:
            for d in ((0.0, 1.5, 0.15), (0.0, -1.5, 0.15), (0.0, 0.0, 1.6), (0.0, 0.9, -1.3), (0.0, -0.9, -1.3)):
                P.glow.append((sc + v3(*d), M.STAR_W))
    # The double ring of star glow opening round it in the tell.
    if ring > 0.0:
        for j, (rad, col) in enumerate(((R + 1.6 + 2.4 * ring, M.GHOST_GLOW_HI), (R + 3.2 + 3.4 * ring, M.GHOST_GLOW))):
            n = 22 + 6 * j
            for k in range(n):
                ang = math.radians(k * 360.0 / n + f * 9.0 * (1 if j else -1))
                if (k + j) % 4 == 3:
                    continue
                P.glow.append((C + v3(math.cos(ang) * rad, math.sin(ang) * rad, math.sin(ang) * rad * 0.3 + 0.4), col))
    # The sting: sparks bursting at the tentacles' tips.
    if f in st.get("sting", ()):
        for tip in tips:
            for k in range(6):
                ang = math.radians(k * 60.0 + f * 25.0)
                rr2 = 0.9 + 0.7 * (f - 1)
                P.glow.append((tip + v3(math.cos(ang) * rr2, math.sin(ang) * rr2, 0.5 * math.sin(ang)), M.STAR_W if k % 2 else M.SPARK))
    d = B.pick("dissolve", action, f)
    if d > 0.0:
        P.dissolve = d
        P.dissolve_col = M.STAR_V
    return P

# ================================================================================================= the wind kite (M3)
# The wind kite (`sail`): a wind spirit that took the shape of a giant festival kite, flying flat over its shadow. A
# swallow-shaped sail of crimson silk in two halves either side of its spine (a little dihedral between them, so each
# half takes the light its own way), gold-rimmed along its trailing edges, a gold rib out to each wing tip, an ink cloud
# painted on each wing; its bamboo frame over it (the spine, the bowed cross spar, the leading-edge spars, a node where
# they cross); a gold bird-head prow (a hooked beak, a crimson crest, a jade eye on each side that glows); two crimson
# streamers banded in gold flowing from its tail's forks; wind trails off its wing tips.
#
# Channels: `lunge`, `rise`, `bob`, `pitch` (+ nose up), `roll` (+ banking to its left), `spin` (its turn about the
# vertical, degrees, as it spirals down), `flutter` (the streamers' wave), `trail` (0..1: the streamers pulled straight
# back), `dih` (the halves' dihedral, degrees; the death folds them up), `glow` (the eyes'), `spiral` (the wind spiral in
# at its prow, the tell), `crescent` (the wind crescent it slashes with, the blow), `streaks`, `tear` (0..1: slits torn in
# the silk), `snap` (0..1: its cross spar broken), `drop` (0..1: fallen to the floor), `fade`.
KITE_STYLES = {
    "kite_hover": {"bob": (0.0, 0.3, 0.5, 0.3, 0.0, -0.2), "roll": (2.0, 1.0, 0.0, -1.0, -2.0, 0.0), "flutter": (1.0,) * 6},
    "kite_glide": {"kind": "glide", "flutter": (1.3,) * 8, "pitch": (-4.0,) * 8, "trail": (0.3,) * 8},
    "kite_rear": {"pitch": (5.0, 9.0, 12.0, 13.0), "lunge": (-0.4, -0.9, -1.2, -1.3), "rise": (0.6, 1.2, 1.6, 1.7), "trail": (0.4, 0.7, 0.9, 1.0),
                  "glow": (0.5, 1.0, 1.5, 2.0), "spiral": (0.25, 0.5, 0.8, 1.0), "flutter": (0.8, 0.6, 0.4, 0.4), "dih": (10.0, 14.0, 16.0, 16.0)},
    "kite_dive": {"lunge": (2.6, 6.0, 6.6, 4.8, 2.4, 0.6), "rise": (-2.0, -6.0, -5.6, -3.4, -1.4, 0.0), "pitch": (-30.0, -10.0, 2.0, 6.0, 3.0, 0.0),
                  "trail": (1.0, 1.0, 0.8, 0.5, 0.3, 0.1), "crescent": (0.0, 1.0, 0.35, 0.0, 0.0, 0.0), "streaks": (1.0, 1.0, 0.5, 0.0, 0.0, 0.0),
                  "glow": (2.0, 1.0, 0.5, 0.0, 0.0, 0.0), "dih": (4.0, 2.0, 4.0, 6.0, 8.0, 8.0), "flutter": (0.6, 0.6, 1.0, 1.4, 1.2, 1.0)},
    "kite_tear": {"lunge": (-2.2, -1.2, -0.4), "roll": (16.0, 8.0, 2.0), "pitch": (14.0, 6.0, 0.0), "tear": (1.0, 0.8, 0.5),
                  "flutter": (2.2, 1.6, 1.2), "squint": True},
    "kite_crumple": {"snap": (0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0), "dih": (14.0, 30.0, 46.0, 58.0, 66.0, 70.0, 72.0, 72.0),
                     "drop": (0.0, 0.1, 0.25, 0.45, 0.65, 0.85, 1.0, 1.0), "spin": (0.0, 30.0, 70.0, 120.0, 165.0, 200.0, 220.0, 225.0),
                     "roll": (10.0, 18.0, 24.0, 20.0, 14.0, 10.0, 8.0, 8.0), "pitch": (10.0, 0.0, -10.0, -16.0, -18.0, -14.0, -10.0, -10.0),
                     "tear": (0.5, 0.7, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0), "flutter": (2.0, 2.0, 1.6, 1.2, 0.8, 0.4, 0.2, 0.2),
                     "fade": (0.0, 0.0, 0.0, 0.0, 0.2, 0.45, 0.7, 0.9), "dark_from": 2},
}
STYLES.update(KITE_STYLES)
# The sail's half outline (its left half, y >= 0; the right mirrors), from the side-view sheet's own (art px / 2.3): the
# nose, the leading edge bowed out through its control point to the swept wing tip, the trailing edge sweeping in through
# its control point to the tail's fork, the fork back in to the notch.
KITE = {
    "Z": 10.0,
    "sail": {"nose": (4.8, 0.0), "lead": (3.3, 5.4), "tip": (-2.6, 7.8), "trail": (-2.2, 3.3), "fork": (-7.0, 2.4), "notch": (-5.0, 0.0),
             "dih": 8.0, "rim": 0.5, "rib": 0.24, "cloud": ((1.3, 2.3), 1.2), "lift": 0.28},
    "frame": {"r": 0.2, "bow": 0.9},
    "head": {"at": (6.3, 0.0, 0.85), "r": (1.6, 1.15, 1.1), "eye": (0.55, 0.92, 0.3), "beak": 1.4, "crest": 2.4},
    "streamers": {"length": 11.0, "n": 7, "width": 0.75, "bands": 2.0},
    "trails": 3,
}
VARIANTS.update({
    "kite": {"parts": KITE, "mats": {"silk": "wk_silk", "gold": "wk_gold", "ink": "wk_ink", "bamboo": "wk_bamboo", "jade": "wk_jade"},
             "motion": {"idle": "kite_hover", "walk": "kite_glide", "windup": "kite_rear", "attack": "kite_dive", "hurt": "kite_tear",
                        "death": "kite_crumple"}},
})


def _bez(a, c, b, n):
    """n + 1 points along the quadratic curve from a through control c to b (a and b included)."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]))
    return out


def _inside(x, y, poly):
    """Which of the points (x, y) lie inside the polygon (a ray cast along +x)."""
    ins = np.zeros(len(x), dtype=bool)
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if y1 == y2:
            continue
        cross = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1)
        ins ^= cross
    return ins


def _seg_dist(x, y, a, b):
    """The points' distances to the segment a-b."""
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    t = np.clip(((x - ax) * dx + (y - ay) * dy) / max(1e-9, dx * dx + dy * dy), 0.0, 1.0)
    return np.hypot(x - ax - t * dx, y - ay - t * dy)


def _line_dist(x, y, pts):
    d = np.full(len(x), 99.0)
    for a, b in zip(pts, pts[1:]):
        d = np.minimum(d, _seg_dist(x, y, a, b))
    return d


# The slits torn in the silk when it is struck (in the left half's (x, y); the right half takes them shifted).
KITE_TEARS = (((-0.6, 2.6), (-2.2, 4.4)), ((0.4, 5.2), (-0.9, 6.3)), ((-4.6, 1.2), (-5.6, 2.0)))


def _kite(B, action: str, f: int, view: float) -> Pose:
    """M3, the wind kite (see KITE_STYLES): hovering flat over its shadow, its silk rippling and its streamers flowing; it
    glides banking; in its tell it rears nose-up, its streamers pulled straight back, the wind spiralling in at its prow
    and its jade eyes glowing; it dives steeply, slashing a wind crescent across the ground before it; struck, slits tear
    in its silk; beaten, its cross spar snaps, its halves fold up and it spirals down to the floor and fades."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    lunge = B.pick("lunge", action, f)
    rise = B.pick("rise", action, f)
    bob = B.pick("bob", action, f)
    pitch = B.pick("pitch", action, f)
    roll = B.pick("roll", action, f)
    spin = B.pick("spin", action, f)
    flutter = B.pick("flutter", action, f, 1.0)
    trail = B.pick("trail", action, f)
    glow = B.pick("glow", action, f)
    spiral = B.pick("spiral", action, f)
    crescent = B.pick("crescent", action, f)
    streaks = B.pick("streaks", action, f)
    tear = B.pick("tear", action, f)
    snap = B.pick("snap", action, f)
    drop = B.pick("drop", action, f)
    fade = B.pick("fade", action, f)
    sl = p.sail
    dih = B.pick("dih", action, f, sl.dih)
    ph = f / 6.0 * math.tau if action == "idle" else f * 1.1
    if st.get("kind") == "glide":
        ph = f / 8.0 * math.tau
        roll = 9.0 * math.sin(ph)
        bob = 0.4 * math.sin(ph * 2.0)
    z = (p.Z + rise + bob) * (1.0 - drop) + drop * 0.9
    C = v3(lunge, 0.0, z)
    bm = rot("c", spin) @ rot("a", roll) @ rot("b", pitch)
    at = lambda q: C + bm @ v3(q)
    dark = action == "death" and f >= st.get("dark_from", 99)
    nose, tip, fork, notch = sl.nose, sl.tip, sl.fork, sl.notch
    lead = _bez(nose, sl.lead, tip, 8)
    trl = _bez(tip, sl.trail, fork, 8)
    poly = lead + trl[1:] + [notch]
    xs = [q[0] for q in poly]
    ys = [q[1] for q in poly]
    cx, cy = (min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5
    rx, ry = (max(xs) - min(xs)) * 0.78, (max(ys) - min(ys)) * 0.82
    (ccx, ccy), cr = sl.cloud
    halves = {}
    for s in (1, -1):
        # A half: its own frame turned up about the spine by the dihedral (folding up as it dies, its broken spar letting the
        # half sag back).
        hm = bm @ rot("a", s * dih) @ rot("c", s * 14.0 * snap)
        halves[s] = hm

        def local(q, hm=hm, s=s):
            loc = (q - C) @ hm
            return loc[:, 0], loc[:, 1] * s

        def clip(q, local=local, s=s):
            x, y = local(q)
            keep = _inside(x, y, poly) & (y >= -0.05)
            if tear > 0.0:
                for k, (a, b) in enumerate(KITE_TEARS):
                    if k < 1 + int(tear * 2.5):
                        sh = 0.0 if s > 0 else 0.6
                        keep &= _seg_dist(x, y, (a[0] + sh, a[1]), (b[0] + sh, b[1])) > 0.3 + 0.16 * tear
            return keep

        def silk(q, n, local=local):
            x, y = local(q)
            rim = _line_dist(x, y, trl) < sl.rim
            rib = _seg_dist(x, y, (0.3, 0.0), tip) < sl.rib
            # The ink cloud: a puff of three lobes, a curl of silk showing in its middle, a lick of a tail behind it.
            curl = np.zeros(len(x), dtype=bool)
            for dx, dy, rr in ((0.0, 0.0, 0.62), (0.75, 0.3, 0.5), (-0.7, 0.25, 0.5), (0.05, 0.62, 0.45)):
                curl |= np.hypot(x - ccx - dx * cr, y - ccy - dy * cr) < rr * cr
            curl &= ~(np.abs(np.hypot(x - ccx, y - ccy - 0.15 * cr) - 0.3 * cr) < 0.12)
            curl |= _seg_dist(x, y, (ccx - cr * 0.9, ccy - cr * 0.1), (ccx - cr * 2.0, ccy - cr * 0.35)) < 0.24
            ripple = ((x * 0.8 - y * 0.35 + ph * 0.5) % 2.2 < 0.4) & (_line_dist(x, y, trl) < 2.2)
            names = np.where(rim | rib, m.gold, m.silk).astype(object)
            # The silk's own crimson facing up into the light (a step down), its ripples a step under that, the cloud painted
            # in the silk's deepest.
            bias = np.where(rim | rib, 0, np.where(curl, -3, np.where(ripple, -2, -1)))
            return names, bias.astype(np.int16)

        P.add(E(C + hm @ v3(cx, s * cy, 0.0), (rx, ry, sl.lift), m.silk, "sail%d" % s, hm, silk, clip))
    # The bamboo frame over the silk: the spine, the bowed cross spar (broken in two as it dies), the leading-edge spars, a
    # node where they cross.
    fr_ = p.frame
    up = 0.35
    P.add(L(at((nose[0] - 0.4, 0.0, up)), at((notch[0] + 0.3, 0.0, up)), fr_.r, fr_.r, m.bamboo, "spine"))
    for s in (1, -1):
        hm = halves[s]
        hp = lambda q, hm=hm: C + hm @ v3(q)
        mid = (fr_.bow * (1.0 - snap), 0.0, up)
        end = (tip[0] + 0.3, s * (tip[1] - 0.4), up)
        P.add(L(at(mid) + bm @ v3(-0.6 * snap, 0.0, 0.0), hp(end), fr_.r, fr_.r * 0.85, m.bamboo, "spar%d" % s))
        pts = [hp((q[0], s * q[1], up)) for q in lead[1::2]]
        for a_, b_ in zip(pts, pts[1:]):
            P.add(L(a_, b_, fr_.r * 0.85, fr_.r * 0.85, m.bamboo, "lead%d" % s, line=False))
    P.add(S(at((fr_.bow * (1.0 - snap), 0.0, up + 0.1)), 0.45, m.gold, "node", line=False))
    # The bird-head prow: a gold head on a short neck off the nose, its hooked beak, its crimson crest swept back, a jade
    # eye on each side (glowing in the tell, dimmed when struck, dark as it dies).
    hd = p.head
    hc = at(hd.at)
    hm = bm @ rot("b", 8.0)
    P.add(L(at((nose[0] - 0.6, 0.0, 0.2)), hc + hm @ v3(-0.6, 0.0, -0.3), 0.75, 0.7, m.gold, "neck"))
    P.add(E(hc, hd.r, m.gold, "head", hm))
    bq = hc + hm @ v3(hd.r[0] * 0.8, 0.0, -0.05)
    bt = bq + hm @ v3(hd.beak, 0.0, -0.35)
    P.add(L(bq, bt, 0.42, 0.2, m.gold, "beak"), L(bt, bt + hm @ v3(0.15, 0.0, -0.5), 0.2, 0.12, m.gold, "beak"))
    for j, (sd, ln) in enumerate(((0.0, 1.0), (0.45, 0.8), (-0.45, 0.8))):
        r0 = hc + hm @ v3(-0.1, sd * 0.5, hd.r[2] * 0.8)
        r1 = r0 + hm @ v3(-hd.crest * ln, sd * 1.3, 0.5 + 0.25 * math.sin(ph + j) * flutter * 0.4)
        P.add(L(r0, r1, 0.42, 0.18, m.silk, "crest", line=j == 0))
    ea, eb, ec = hd.eye
    for s in (1, -1):
        spot = hc + hm @ v3(ea, s * eb, ec)
        if dark:
            P.mark(spot, M.RAMPS[m.ink][2])
            continue
        if st.get("squint"):
            P.mark(spot, M.RAMPS[m.jade][2])
            continue
        P.eye(spot, M.WK_EYE)
        if glow >= 1.0:
            for dd in ((0.0, s * 0.5, 0.3), (0.3, s * 0.45, -0.2), (-0.3, s * 0.5, 0.0)):
                P.glow.append((spot + hm @ v3(*dd), M.WK_EYE_GLOW))
    # The streamers: a flat ribbon from each of the tail's forks, crimson banded in gold, flowing back in waves (pulled
    # straight back in its tell and the dive, thrashing when struck, dragging as it falls).
    sm = p.streamers
    for s in (1, -1):
        root = C + halves[s] @ v3(fork[0] + 0.3, s * (fork[1] - 0.2), 0.0)
        pts = [root]
        amp = (1.0 - 0.85 * trail) * flutter * 0.9
        for i in range(1, sm.n + 1):
            t = i / sm.n
            wave = math.sin(ph + t * 4.2 + (0.9 if s > 0 else 0.0)) * amp * (0.35 + t) * 1.3
            q = bm @ v3(-sm.length * t * (1.0 - 0.25 * drop), s * (0.6 * t) + wave, -1.2 * t * (1.0 - trail) + wave * 0.25)
            pts.append(root + q)
        for i in range(sm.n):
            a_, b_ = pts[i], pts[i + 1]
            seg = b_ - a_
            ln = float(np.linalg.norm(seg)) or 1e-6
            ax = seg / ln
            side = np.cross(v3(0.0, 0.0, 1.0), ax)
            side = side / (float(np.linalg.norm(side)) or 1.0)
            nrm = np.cross(ax, side)
            mm = np.stack([ax, side, nrm], axis=1)
            mid = (a_ + b_) * 0.5
            hl, hw = ln * 0.5 + 0.15, sm.width * 0.5 * (1.0 - 0.35 * i / sm.n)
            s0 = i * ln

            def clip(q, mid=mid, ax=ax, side=side, hl=hl, hw=hw, last=i == sm.n - 1):
                rel = q - mid
                u, v = rel @ ax, rel @ side
                keep = (np.abs(u) <= hl) & (np.abs(v) <= hw)
                if last:                                     # a swallow-tailed end
                    keep &= u <= hl - 0.7 * (1.0 - np.abs(v) / max(hw, 1e-6))
                return keep

            def band(q, n, mid=mid, ax=ax, hl=hl, s0=s0):
                u = (q - mid) @ ax + hl + s0
                gold = (u % sm.bands) < 0.55
                return np.where(gold, m.gold, m.silk).astype(object), np.zeros(len(q), dtype=np.int16)

            P.add(E(mid, (hl * 1.42, hw * 1.42, 0.16), m.silk, "streamer%d" % s, mm, band, clip))
    # The wind: trails off its wing tips as it flies, streaks behind its dive, the spiral in at its prow in the tell, the
    # crescent it slashes with.
    if not dark and action != "hurt":
        for s in (1, -1):
            base = C + halves[s] @ v3(tip[0] - 0.6, s * tip[1], 0.0)
            for k in range(p.trails):
                u = (k * 0.37 + f * 0.13) % 1.0
                for d in range(3):
                    q = base + bm @ v3(-1.6 - k * 1.7 - d * 0.7 - 2.0 * trail, s * (0.4 * math.sin(ph + k + d * 0.5) + 0.5 * k), 0.2 * d)
                    P.fx.append((q, M.WK_WIND if d < 2 and u < 0.7 else M.WK_WIND_DIM))
    if spiral > 0.0:
        # Two arms of wind winding in to a point before its beak (drawn in the ground's plane, so it reads from above).
        front = at((hd.at[0] + 2.6, 0.0, hd.at[2]))
        n = int(8 + 12 * spiral)
        for arm in (0.0, 180.0):
            for k in range(n):
                ang = math.radians(arm + k * 34.0 + f * 47.0)
                rr = (4.6 - k * 0.19) * (0.6 + 0.4 * spiral)
                q = front + v3(math.cos(ang) * rr * 0.8, math.sin(ang) * rr, 0.3 * math.sin(ang))
                P.glow.append((q, M.WK_CRESCENT if k > n - 4 else (M.WK_WIND if k % 3 else M.WK_WIND_DIM)))
    if crescent > 0.0:
        cc = v3(lunge + 2.0, 0.0, max(1.0, z - 1.0))
        for k in range(19):
            a = math.radians(-80.0 + k * (160.0 / 18.0))
            w_ = 1.0 - abs(k - 9) / 10.0
            for t in range(1 + int(2.5 * w_ * crescent + 0.5)):
                rr = 5.6 * (0.8 + 0.2 * crescent) - t * 0.55
                P.glow.append((cc + v3(math.cos(a) * rr, math.sin(a) * rr * 1.15, 0.0), M.WK_WIND if t else M.WK_CRESCENT))
    if streaks > 0.0:
        for j in range(4):
            yy = (j - 1.5) * 2.4
            for d in range(3):
                P.fx.append((C + bm @ v3(-6.0 - d * 1.4, yy, 1.2 + d * 0.8), M.WK_WIND if d < 2 else M.WK_WIND_DIM))
    if tear > 0.0 and action == "hurt":
        for k in range(5):                                   # torn shreds of silk fluttering off
            q = C + bm @ v3(-1.0 - k * 0.9, (k - 2) * 1.6, 1.2 + (k % 2) * 0.8 + f * 0.4)
            P.fx.append((q, M.RAMPS[m.silk][3]))
    if fade > 0.0:
        P.dissolve = fade
        P.dissolve_col = M.WK_WIND
    return P

