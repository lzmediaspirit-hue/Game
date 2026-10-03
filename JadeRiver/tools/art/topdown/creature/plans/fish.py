"""The fish plan (audit 45 §6.2), from the hollow minnow (`minnow`); the greyfin (`greyfin`, E2's first new species) is
its pool-dwelling kind.

A body of two ellipsoids (the trunk and the head) bent against its tail (`swish`: the tail's swing, the head turning
against it), a tail segment and a forked tail of two lobes, a ragged dorsal fin of plates, pectoral fins that flap, an
eye in a dark socket, a mouth and a jaw that drops in the gape; and the options a species adds: the Hollow's strands
trailing as its wake.

  body   the trunk's and the head's radii and where the head sits; the tail segment and the lobes' size and spread
  fins   the dorsal plates (along it, height), the pectoral fins' place and size
  eye    the socket and the eye's colour (the Hollow's empty white), closed or dulled when struck or beaten
  wake   the Hollow's strands from the tail (a minnow's), how long they trail per action
  M1 (the jade carp): `Z` (it rides at the water line, its belly on the ground), `barbels` (whiskers trailing from the
         mouth's corners), a `gold` material tipping the fins and the lobes, ringing the eye (`eye.ring`)

The motion styles (STYLES): idle `hang`, walk `swish`, windup `curl_c`, attack `dart`, hurt `jerk_roll`, death
`belly_up_mist`. The channels: `dart` (along the way it goes), `bob` (up), `swish` (the tail's swing, degrees),
`nose` (pitch), `gape`, `stretch` (along its length), `roll` and `mist` (the death's coming apart).

  pool   (the greyfin) a puddle of its own drawn flat round its feet, the fish under its surface but for its back and
         its tall torn fin, its dark shape showing through; ripples, a cruising wake, the water thrown up
Its styles: idle `circle`, walk `cruise`, windup `sink_rise`, attack `leap_bite`, hurt `thrash`, death `flop_mist`;
channels `depth` (under the surface, + up), `dart`, `side`, `nose`, `swish`, `gape`, `roll`, `splash`, `rings`, `mist`.
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..motion import wave
from ..sculpt import E, Pose, chain, rot, v3

STYLES = {
    "hang": {"bob": (0.0, -0.4, -0.7, -0.6, -0.3, 0.0), "swish": (8.0, 14.0, 8.0, -4.0, -10.0, -2.0), "flap": True, "trail": "wave"},
    "swish": {"kind": "swim", "bob_amp": 0.3, "swish_amp": 28.0, "flap": True, "trail": "wave"},
    "curl_c": {"dart": (-0.8, -1.6, -2.4, -2.8), "swish": (26.0, 42.0, 54.0, 58.0), "nose": (6.0, 10.0, 12.0, 14.0),
               "gape": (0.4, 0.8, 1.0, 1.1), "stretch": (1.0, 0.98, 0.96, 0.95), "flap": True, "trail": 3.6},
    "dart": {"dart": (3.4, 6.0, 6.6, 5.4, 3.2, 1.2), "swish": (-20.0, -6.0, 10.0, 18.0, 10.0, 4.0), "nose": (-4.0, -8.0, -6.0, -2.0, 0.0, 0.0),
             "gape": (1.0, 0.0, 0.0, 0.3, 0.2, 0.0), "stretch": (1.18, 1.06, 0.94, 1.0, 1.0, 1.0), "trail": 7.0, "glint": 1},
    "jerk_roll": {"dart": (-2.6, -1.6, -0.6), "swish": (24.0, 10.0, 2.0), "nose": (14.0, 6.0, 0.0), "stretch": (0.86, 1.0, 1.0),
                  "roll": (28.0, 14.0, 4.0), "trail": 3.4, "dull": True},
    "belly_up_mist": {"bob": (0.0, -0.5, -1.0, -1.4, -1.8, -2.2, -2.6, -3.0), "swish": (20.0, 30.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                      "gape": (0.6, 0.8, 0.6, 0.4, 0.4, 0.4, 0.4, 0.4),
                      "roll": (60.0, 120.0, 170.0, 178.0, 180.0, 180.0, 180.0, 180.0),
                      "mist": (0.0, 0.0, 0.2, 0.42, 0.62, 0.8, 0.94, 1.0), "trail": 4.0, "dull": True, "wake_until": 3},
}

MINNOW = {
    "trunk": ((0.0, 0.0, 0.0), (4.4, 1.9, 2.4)), "head": ((3.2, 0.0, 0.1), (2.4, 1.75, 2.0)),
    "tail": {"pivot": -3.2, "seg": ((-1.5, 0.0, 0.0), (2.2, 1.0, 1.4)), "lobe": (-4.1, 0.95, (2.0, 0.35, 0.85), 38.0)},
    "dorsal": {"plates": ((-1.4, 1.0), (-0.3, 1.5), (0.8, 1.1), (1.7, 0.6)), "base": 2.1, "r": (0.6, 0.3)},
    "pecs": {"at": (1.6, 1.6, -0.8), "r": (1.3, 1.0, 0.3)},
    "eye": {"socket": (3.2, 0.0, 0.1), "rim": (1.0, 1.35, 0.9), "at": (1.3, 1.3, 0.6), "colour": "HOLLOW_EYE"},
    "mouth": (5.5, 0.0, -0.3),
    "jaw": {"at": (3.9, 0.0, -1.2), "drop": 0.4, "r": (1.5, 1.0, 0.45), "turn": 30.0, "corner": (5.1, 0.0, -0.8)},
    "glints": ((6.8, 0.0, 0.4), (7.4, 0.0, 0.9), (6.3, 0.0, 1.0)),
    "wake": {"strands": 2, "trail": 5.0},
    "mist": True,
}
LURKER_STYLES = {
    # The pool-dweller's channels: `depth` (the body's middle under the surface, + up), `dart`, `side` (across), `nose`,
    # `swish`, `gape`, `roll`, `splash` (a crown of water thrown up: 1 leaving, 2 falling back in), `rings` (how far the
    # ripples have spread), `mist`.
    "circle": {"depth": (-2.1, -2.0, -1.9, -2.0, -2.1, -2.2), "swish": (10.0, 16.0, 8.0, -6.0, -12.0, -4.0), "rings": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)},
    "cruise": {"kind": "cruise", "depth": (-1.9,) * 8, "swish_amp": 24.0, "wake": True},
    "sink_rise": {"depth": (-2.6, -3.0, -1.2, -0.4), "nose": (-6.0, -10.0, 26.0, 34.0), "gape": (0.0, 0.0, 0.6, 1.0),
                  "swish": (20.0, 34.0, 10.0, 0.0), "dart": (-0.4, -0.8, -0.4, 0.0), "bubbles": (0, 1), "rings": (0.0, 0.3, 0.6, 0.9),
                  "glare": (2, 3)},
    "leap_bite": {"depth": (1.2, 7.4, 5.6, -0.2, -2.0, -2.1), "dart": (1.4, 4.8, 5.4, 2.8, 0.8, 0.2), "nose": (38.0, 2.0, -30.0, -58.0, -12.0, 0.0),
                  "gape": (1.0, 0.1, 0.0, 0.0, 0.0, 0.0), "swish": (-20.0, 8.0, 22.0, 14.0, 6.0, 0.0), "splash": (1.0, 0.0, 0.0, 2.0, 0.0, 0.0),
                  "rings": (0.2, 0.5, 0.8, 0.1, 0.4, 0.7), "glint": 1},
    "thrash": {"depth": (-0.4, -1.0, -1.7), "nose": (22.0, 8.0, 0.0), "swish": (40.0, -24.0, 8.0), "roll": (24.0, -12.0, 0.0),
               "gape": (0.5, 0.2, 0.0), "splash": (1.0, 0.0, 0.0), "rings": (0.3, 0.6, 0.9), "dull": True},
    "flop_mist": {"depth": (-0.2, 2.2, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0), "dart": (0.6, 3.0, 4.2, 4.4, 4.4, 4.4, 4.4, 4.4),
                  "side": (0.0, 1.6, 2.6, 2.8, 2.8, 2.8, 2.8, 2.8), "nose": (20.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                  "swish": (30.0, -20.0, 18.0, -8.0, 4.0, 0.0, 0.0, 0.0), "roll": (10.0, 60.0, 90.0, 90.0, 90.0, 90.0, 90.0, 90.0),
                  "gape": (0.6, 0.4, 0.8, 0.3, 0.6, 0.2, 0.2, 0.2), "mist": (0.0, 0.0, 0.0, 0.1, 0.3, 0.55, 0.8, 0.95),
                  "splash": (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), "rings": (0.3, 0.6, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0), "dull": True},
}
STYLES.update(LURKER_STYLES)

GREYFIN = {
    "pool": {"at": (-0.8, 0.0), "r": (11.6, 7.2), "rim": 0.8},
    "trunk": ((0.0, 0.0, 0.0), (5.6, 2.3, 2.7)), "head": ((4.2, 0.0, 0.1), (3.0, 2.1, 2.4)),
    "tail": {"pivot": -4.0, "seg": ((-1.8, 0.0, 0.0), (2.6, 1.15, 1.6)), "lobe": (-5.0, 1.1, (2.4, 0.4, 1.0), 40.0)},
    "dorsal": {"plates": ((-2.0, 1.2), (-1.0, 2.6), (0.0, 3.6), (0.9, 2.6), (1.6, 1.3)), "base": 2.2, "r": (0.7, 0.32)},
    "pecs": {"at": (2.0, 1.9, -0.9), "r": (1.5, 1.1, 0.3)},
    "eye": {"socket": (4.2, 0.0, 0.1), "rim": (1.4, 1.5, 0.9), "at": (1.7, 1.45, 0.6), "colour": "HOLLOW_EYE"},
    "mouth": (7.0, 0.0, -0.4),
    "jaw": {"at": (5.0, 0.0, -1.3), "drop": 0.5, "r": (1.9, 1.3, 0.5), "turn": 34.0, "corner": (6.4, 0.0, -0.9)},
    "teeth": ((5.6, 6.2, 6.8), 1.0),
    "gills": ((2.2, 1.9, 0.6), (2.0, 2.1, -0.2), (1.9, 2.0, -0.9)),
    "glints": ((8.6, 0.0, 0.4), (9.2, 0.0, 1.0), (8.1, 0.0, 1.2)),
}
VARIANTS = {
    "greyfin": {"parts": GREYFIN, "mats": {"skin": "minnow", "back": "minnow_back", "belly": "minnow_belly", "fin": "minnow_fin"},
                "motion": {"idle": "circle", "walk": "cruise", "windup": "sink_rise", "attack": "leap_bite", "hurt": "thrash",
                           "death": "flop_mist"}},
    "minnow": {"parts": MINNOW, "mats": {"skin": "minnow", "back": "minnow_back", "belly": "minnow_belly", "fin": "minnow_fin"},
               "motion": {"idle": "hang", "walk": "swish", "windup": "curl_c", "attack": "dart", "hurt": "jerk_roll",
                          "death": "belly_up_mist"}},
}


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    if "pool" in B.parts:
        return _lurker(B, action, f)
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    dart = B.pick("dart", action, f)
    bob = B.pick("bob", action, f)
    swim = st.get("kind") == "swim"
    if swim:
        bob = st.bob_amp * wave(action, f)
    swish = B.pick("swish", action, f)
    if swim:
        swish = st.swish_amp * math.sin(f / 8.0 * math.tau)
    nose = B.pick("nose", action, f)
    gape = B.pick("gape", action, f)
    flap = -10.0 - 20.0 * max(0.0, math.sin(f * 1.3)) if st.get("flap") else 0.0
    body_m = rot("b", nose) @ rot("c", -swish * 0.25)        # the head turns against the tail
    C = v3(dart, 0.0, bob + p.get("Z", 0.0))
    at = lambda q: C + body_m @ v3(q)

    def fish(q, n):
        """A dark back, a pale belly, rows of scales (a step lit every other half-row) and the lateral line."""
        nz = n[:, 2]
        back = nz > 0.5
        belly = nz < -0.35
        scale = ((np.floor((q[:, 0] - C[0]) * 0.9) + np.floor((q[:, 2] + 3.0) * 1.2)) % 2 == 0) & ~back & ~belly
        lateral = np.abs(q[:, 2] - C[2] - 0.2) < 0.25
        names = np.where(back, m.back, np.where(belly, m.belly, m.skin)).astype(object)
        return names, np.where(lateral, -1, np.where(scale, 1, 0)).astype(np.int16)

    P.add(E(at(p.trunk[0]), p.trunk[1], m.skin, "body", body_m, fish),
          E(at(p.head[0]), p.head[1], m.skin, "body", body_m, fish))
    t = p.tail
    tm = body_m @ rot("c", swish)
    piv = at((t.pivot, 0.0, 0.0))
    P.add(E(piv + tm @ v3(t.seg[0]), t.seg[1], m.skin, "body", tm, fish))
    la, lc, lr, lspread = t.lobe
    gold = m.get("gold")
    for s in (1, -1):   # the forked tail: an upper and a lower lobe
        lm = tm @ rot("b", -s * lspread)
        P.add(E(piv + tm @ v3(la, 0.0, s * lc), lr, m.fin, "tail", lm))
        if gold:
            P.mark(piv + tm @ v3(la, 0.0, s * lc) + lm @ v3(-lr[0] * 0.9, 0.0, 0.0), M.RAMPS[gold][3])
    d = p.dorsal
    for a, h in d.plates:   # the ragged dorsal fin
        P.add(E(at((a, 0.0, d.base + h * 0.5)), (d.r[0], d.r[1], h), m.fin, "dorsal", body_m))
        if gold:
            P.mark(at((a, 0.0, d.base + h * 1.4)), M.RAMPS[gold][3])
    e = p.eye
    for s in (1, -1):
        P.add(E(at((p.pecs.at[0], s * p.pecs.at[1], p.pecs.at[2])), p.pecs.r, m.fin, "pec%d" % s, body_m @ rot("a", s * flap)))
        sock = at(e.socket)
        P.mark(sock + body_m @ v3(e.rim[0], s * e.rim[1], e.rim[2]), M.RAMPS[gold][2] if gold and e.get("ring") else M.RAMPS[m.back][0])
        P.mark(sock + body_m @ v3(e.at[0], s * e.at[1], e.at[2]), M.RAMPS[m.back][0] if st.get("dull") else getattr(M, e.colour))
        if p.get("barbels"):
            # Whiskers from the mouth's corners, trailing back and down, swaying.
            ba, bb, bc = p.barbels
            sway = 0.5 * wave(action, f, 0.3 if s > 0 else 0.8) if action in ("idle", "walk") else 0.2
            root = at((ba, s * bb, bc))
            pts = [root, root + body_m @ v3(-1.0, s * 0.6, -0.6 + sway * 0.4), root + body_m @ v3(-2.2, s * 1.0 + sway * 0.3, -1.2 + sway)]
            P.add(chain(pts, 0.32, 0.22, gold or m.fin, "barbel%d" % s, line=False))
    P.mark(at(p.mouth), M.FISH_MOUTH)
    j = p.jaw
    if gape > 0.1:
        P.add(E(at((j.at[0], j.at[1], j.at[2] - gape * j.drop)), j.r, m.belly, "jaw", body_m @ rot("b", -j.turn * gape)))
        P.mark(at(j.corner), M.FISH_MOUTH)
    if action == "attack" and f == st.get("glint", -1):
        for g in p.glints:
            P.glow.append((at(g), M.GLINT))
    # The wake: grey strands trailing from the tail and rising, waving as it swims (thin in the dart).
    w = p.get("wake")
    if w:
        trail = st.get("trail", 4.0)
        if trail == "wave":
            trail = w.trail + 0.6 * wave(action, f)
        wv = 0.7 * wave(action, f) if action in ("idle", "walk") else 0.3
        if f < st.get("wake_until", 99):
            for s in (1, -1):
                root = piv + tm @ v3(-5.6, s * 0.4, 0.3)
                back = tm @ v3(-1.0, 0.0, 0.0)
                pts = [root, root + back * trail * 0.35 + v3(0.0, s * 0.7 + wv, 0.3), root + back * trail * 0.7 + v3(0.0, s * 0.5 - wv, 0.8),
                       root + back * trail + v3(0.0, s * 1.2 + wv * 0.5, 1.4)]
                P.add(chain(pts, 0.45, 0.3, "strand", "strand%d" % s, line=False))
    roll = B.pick("roll", action, f)
    if roll:
        P.m = rot("a", roll)
    sa = B.pick("stretch", action, f, 1.0)
    if sa != 1.0:
        P.squash(sa, 1.0 / math.sqrt(sa), 1.0 / math.sqrt(sa), (dart, 0.0, bob))
    if p.get("mist") and B.has("mist", action):
        P.dissolve = B.pick("mist", action, f)
        P.dissolve_col = M.MOTE
        for k in range(int(4 + f * 1.5)):
            ang = math.radians(k * 47.0 + f * 23.0)
            rr = 1.5 + f * 1.1 + (k % 3) * 0.7
            if f >= 2:
                P.fx.append((v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.6, 0.4 + f * 0.9 + (k % 4) * 0.8), M.MOTE if k % 2 else M.MOTE_DIM))
    return P


# ================================================================================================= the pool-dweller
def _lurker(B, action: str, f: int) -> Pose:
    """A fish that lives in a puddle of its own (the greyfin): the puddle is part of it (drawn round its feet, flat on the
    ground; the room view moves it with the fish), the fish under its surface but for its back and its tall torn dorsal
    fin cutting it, its dark shape showing through, ripples spreading from the fin and a wake behind it as it cruises.
    Its tell: it sinks, then its head breaks the surface, jaws gaping on their teeth; it leaps out to bite (the hit at its
    leap's height) and falls back in, the water thrown up as it leaves and as it lands; struck, it thrashes half out;
    beaten, it flops out onto the bank and comes apart into the Hollow's grey mist."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    depth = B.pick("depth", action, f, -2.0)
    dart = B.pick("dart", action, f)
    side = B.pick("side", action, f)
    nose = B.pick("nose", action, f)
    gape = B.pick("gape", action, f)
    roll = B.pick("roll", action, f)
    swish = B.pick("swish", action, f)
    rings = B.pick("rings", action, f)
    if st.get("kind") == "cruise":
        swish = st.swish_amp * math.sin(f / 8.0 * math.tau)
        rings = (f % 4) / 4.0
    yaw = -swish * 0.25
    body_m = rot("c", yaw) @ rot("b", nose) @ rot("a", roll)       # the head turns against the tail
    C = v3(dart, side, depth)
    at = lambda q: C + body_m @ v3(q)
    P.water = 0.0
    under = lambda q: q[:, 2] > 0.02                                # the water's surface: only what is above it is drawn

    def fish(q, n):
        """A dark back, a pale belly, rows of scales (a step lit every other half-row) and the lateral line."""
        loc = (q - C) @ body_m
        nz = (n @ body_m)[:, 2]
        back = nz > 0.5
        belly = nz < -0.35
        scale = ((np.floor(loc[:, 0] * 0.9) + np.floor((loc[:, 2] + 3.0) * 1.2)) % 2 == 0) & ~back & ~belly
        lateral = np.abs(loc[:, 2] - 0.2) < 0.25
        names = np.where(back, m.back, np.where(belly, m.belly, m.skin)).astype(object)
        return names, np.where(lateral, -1, np.where(scale, 1, 0)).astype(np.int16)

    P.add(E(at(p.trunk[0]), p.trunk[1], m.skin, "body", body_m, fish, under),
          E(at(p.head[0]), p.head[1], m.skin, "body", body_m, fish, under))
    t = p.tail
    tm = body_m @ rot("c", swish)
    piv = at((t.pivot, 0.0, 0.0))
    P.add(E(piv + tm @ v3(t.seg[0]), t.seg[1], m.skin, "body", tm, fish, under))
    la, lc, lr, lspread = t.lobe
    for s in (1, -1):   # the forked tail: an upper and a lower lobe
        P.add(E(piv + tm @ v3(la, 0.0, s * lc), lr, m.fin, "tail", tm @ rot("b", -s * lspread), clip=under))
    d = p.dorsal
    for a, h in d.plates:   # the tall torn dorsal fin, a shark's sail
        P.add(E(at((a, 0.0, d.base + h * 0.5)), (d.r[0], d.r[1], h), m.fin, "dorsal", body_m, clip=under))
    e = p.eye
    dull = st.get("dull", False)
    for s in (1, -1):
        P.add(E(at((p.pecs.at[0], s * p.pecs.at[1], p.pecs.at[2])), p.pecs.r, m.fin, "pec%d" % s, body_m @ rot("a", s * -20.0), clip=under))
        sock = at(e.socket)
        P.mark(sock + body_m @ v3(e.rim[0], s * e.rim[1], e.rim[2]), M.RAMPS[m.back][0])
        eye = sock + body_m @ v3(e.at[0], s * e.at[1], e.at[2])
        (P.mark if dull else P.eye)(eye, M.RAMPS[m.back][0] if dull else getattr(M, e.colour))
        if f in st.get("glare", ()):
            P.mark(eye + body_m @ v3(0.0, s * 0.35, 0.35), M.EYE_HALO)
        for g in p.gills:      # the gill arc behind the head
            P.mark(at((g[0], s * g[1], g[2])), M.RAMPS[m.back][0])
    P.mark(at(p.mouth), M.FISH_MOUTH)
    j = p.jaw
    if gape > 0.1:
        jm = body_m @ rot("b", -j.turn * gape)
        P.add(E(at((j.at[0], j.at[1], j.at[2] - gape * j.drop)), j.r, m.belly, "jaw", jm, clip=under))
        P.mark(at(j.corner), M.FISH_MOUTH)
        if gape > 0.3:
            xs, half = p.teeth
            for x in xs:
                for s in (1, -1):
                    P.mark(at((x, s * half, -0.9)), M.FISH_TOOTH)
                    P.mark(at((x - 0.3, s * half * 0.9, -1.4 - gape * 0.5)), M.FISH_TOOTH)
    if action == "attack" and f == st.get("glint", -1):
        for g in p.glints:
            P.glow.append((at(g), M.GLINT))
    # The water thrown up: a crown of drops where it leaves the pool (1) or falls back in (2).
    sp = B.pick("splash", action, f)
    if sp:
        cx, cy = (p.pool.at[0] + 1.5, 0.0) if sp == 1.0 else (dart + 2.0, side)
        for k in range(18):
            ang = math.radians(k * 20.0 + f * 9.0)
            rr = 3.2 + (k % 3) * 0.6
            lift = 1.2 + 1.8 * (0.5 + 0.5 * math.sin(ang * 3.0 + f))
            P.fx.append((v3(cx + math.cos(ang) * rr, cy + math.sin(ang) * rr * 0.8, lift), M.SPLASH if k % 2 else M.FOAM))
            if k % 3 == 0:
                P.fx.append((v3(cx + math.cos(ang) * rr * 0.6, cy + math.sin(ang) * rr * 0.5, lift + 1.6), M.SPLASH_DIM))
    for k in range(4 if f in st.get("bubbles", ()) else 0):
        P.fx.append((v3(dart + 1.0 - k * 1.6, side + (k % 2) * 1.2 - 0.6, 0.15), M.FOAM if k % 2 else M.SPLASH_DIM))
    mist = B.pick("mist", action, f)
    if mist:
        P.dissolve = mist
        P.dissolve_col = M.MOTE
        for k in range(int(3 + f)):
            ang = math.radians(k * 47.0 + f * 23.0)
            rr = 1.5 + (k % 3) * 1.1
            P.fx.append((C + v3(math.cos(ang) * rr, math.sin(ang) * rr * 0.6, 1.0 + f * 0.7 + (k % 4) * 0.8), M.MOTE if k % 2 else M.MOTE_DIM))
    P.water_fx = _pool(p, C, yaw, depth, rings, st.get("kind") == "cruise", f)
    return P


def _pool(p, C, yaw: float, depth: float, rings: float, wake: bool, f: int):
    """The puddle round it, flat on the ground: its dark edge and pale rim, the fish's dark shape under the surface,
    ripples spreading from where the fin cuts it, a V of wake behind the fin as it cruises."""
    pa = p.pool.at[0]
    rx, ry = p.pool.r
    rim = p.pool.rim
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    (ta, _, _), (tra, trb, _) = p.trunk
    (ha, _, _), (hra, hrb, _) = p.head
    fin_a = C[0] + cy * 0.0
    fin_b = C[1]
    shade = depth < 0.6

    def water(a, b):
        u = ((a - pa) / rx) ** 2 + (b / ry) ** 2
        if u > 1.0:
            return None
        if u > 1.0 - 0.9 / min(rx, ry) * 1.2:
            return M.PUDDLE_EDGE
        if u > 1.0 - rim * 2.0 / min(rx, ry):
            return M.PUDDLE_RIM
        da, db = a - C[0], b - C[1]
        fa, fb = da * cy + db * sy, -da * sy + db * cy      # into the fish's own frame
        if shade and (((fa - ta) / tra) ** 2 + (fb / trb) ** 2 < 1.0 or ((fa - ha) / hra) ** 2 + (fb / hrb) ** 2 < 1.0
                      or ((fa + 6.0) / 2.4) ** 2 + (fb / 1.3) ** 2 < 1.0):
            return M.PUDDLE_DEEP
        dr = math.hypot(a - fin_a, b - fin_b)
        r = 2.8 + 3.4 * rings
        if abs(dr - r) < 0.3 and u < 0.7:
            return M.PUDDLE_RIPPLE
        if wake and fa < -1.0 and abs(abs(fb) - (-fa - 1.0) * 0.5) < 0.3:
            return M.PUDDLE_RIPPLE
        return M.PUDDLE

    return water
