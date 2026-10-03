"""The fish plan (audit 45 §6.2), from the hollow minnow (`minnow`).

A body of two ellipsoids (the trunk and the head) bent against its tail (`swish`: the tail's swing, the head turning
against it), a tail segment and a forked tail of two lobes, a ragged dorsal fin of plates, pectoral fins that flap, an
eye in a dark socket, a mouth and a jaw that drops in the gape; and the options a species adds: the Hollow's strands
trailing as its wake.

  body   the trunk's and the head's radii and where the head sits; the tail segment and the lobes' size and spread
  fins   the dorsal plates (along it, height), the pectoral fins' place and size
  eye    the socket and the eye's colour (the Hollow's empty white), closed or dulled when struck or beaten
  wake   the Hollow's strands from the tail (a minnow's), how long they trail per action

The motion styles (STYLES): idle `hang`, walk `swish`, windup `curl_c`, attack `dart`, hurt `jerk_roll`, death
`belly_up_mist`. The channels: `dart` (along the way it goes), `bob` (up), `swish` (the tail's swing, degrees),
`nose` (pitch), `gape`, `stretch` (along its length), `roll` and `mist` (the death's coming apart).
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
VARIANTS = {
    "minnow": {"parts": MINNOW, "mats": {"skin": "minnow", "back": "minnow_back", "belly": "minnow_belly", "fin": "minnow_fin"},
               "motion": {"idle": "hang", "walk": "swish", "windup": "curl_c", "attack": "dart", "hurt": "jerk_roll",
                          "death": "belly_up_mist"}},
}


def pose(B, action: str, f: int) -> Pose:
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
    C = v3(dart, 0.0, bob)
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
    for s in (1, -1):   # the forked tail: an upper and a lower lobe
        P.add(E(piv + tm @ v3(la, 0.0, s * lc), lr, m.fin, "tail", tm @ rot("b", -s * lspread)))
    d = p.dorsal
    for a, h in d.plates:   # the ragged dorsal fin
        P.add(E(at((a, 0.0, d.base + h * 0.5)), (d.r[0], d.r[1], h), m.fin, "dorsal", body_m))
    e = p.eye
    for s in (1, -1):
        P.add(E(at((p.pecs.at[0], s * p.pecs.at[1], p.pecs.at[2])), p.pecs.r, m.fin, "pec%d" % s, body_m @ rot("a", s * flap)))
        sock = at(e.socket)
        P.mark(sock + body_m @ v3(e.rim[0], s * e.rim[1], e.rim[2]), M.RAMPS[m.back][0])
        P.mark(sock + body_m @ v3(e.at[0], s * e.at[1], e.at[2]), M.RAMPS[m.back][0] if st.get("dull") else getattr(M, e.colour))
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
