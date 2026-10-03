"""The squatting, hopping plan (audit 45 §6.2), from the reed frog (`frog`) and the mossback toad (`toad`).

A broad body sitting on folded hind legs, tilted on the hop (`tilt`), squashed and stretched (`sq`) as it crouches,
leaps and lands; eyes set high on the head; a throat sac that puffs (`puff`); short front legs propping the chest. The
hop is written per frame as channels: `hop` (the body's height over its rest), `ahead` (where it is along the way it
goes), `tilt` (nose up), `sq` (the squash along its height) and `stretch` (the hind legs, 0 folded .. 1 trailing).

  legs   spring   the hind legs fold at its sides and stretch out straight as it leaps (the frog)
         squat    thick hind legs folded wide at its sides, trailing only in the air (the toad)
  eyes   bead     a gold eye with a pupil mark and a glint (the frog)
         lidded   a slit-pupilled eye under a heavy lid that narrows in the tell (the toad)
  back   the toad's glands, moss tufts and fiddlehead ferns (options)
  tongue the toad's lash: a long tongue to its full reach on the hit, a glint at its tip

The motion styles (STYLES): idle `gulp`, `breathe`; walk `hop`, `heavy_hop`; windup `crouch_puff`, `rock_back`;
attack `leap_kick`, `tongue_lash`; hurt `knock_flat`, `squash`; death `flip_back`, `flop_back`.
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..motion import h01v, headon, wave
from ..sculpt import E, L, Pose, S, chain, rot, v3
from .kit import shut


def _hop(rows):
    """A hand module's HOP rows (hop, ahead, tilt, sq, stretch) as the plan's channels."""
    return {k: tuple(r[i] for r in rows) for i, k in enumerate(("hop", "ahead", "tilt", "sq", "stretch"))}


STYLES = {
    # idle
    "gulp": {"puff": (0.0, 0.25, 0.5, 0.25, 0.0, 0.1), "breathe": 0.02},
    "breathe": {"sq": (1.0, 1.02, 1.04, 1.03, 1.01, 1.0), "puff": (0.0, 0.15, 0.3, 0.2, 0.1, 0.0), "sway": 0.7},
    # walk
    "hop": dict(_hop(((0.0, -1.2, 0.0, 0.84, 0.0), (0.4, -1.0, 8.0, 1.08, 0.4), (2.2, -0.4, 16.0, 1.14, 1.0), (3.2, 0.2, 10.0, 1.06, 1.0),
                      (2.6, 0.8, -4.0, 1.0, 0.8), (1.0, 1.2, -10.0, 1.0, 0.4), (0.0, 1.2, -4.0, 0.82, 0.0), (0.0, 0.0, 0.0, 0.94, 0.0))),
                dust=(6, 7)),
    "heavy_hop": {"hop": (0.0, 0.4, 1.8, 2.8, 2.4, 1.0, 0.0, 0.0), "ahead": (-0.8, -0.8, -0.2, 0.4, 0.8, 1.0, 0.8, 0.0),
                  "sq": (0.86, 0.94, 1.06, 1.04, 1.0, 0.96, 0.84, 0.94), "tilt": (0.0, 6.0, 12.0, 6.0, -4.0, -8.0, -2.0, 0.0), "sway": 0.7},
    # windup
    "crouch_puff": dict(_hop(((-0.4, -0.2, 4.0, 0.94, 0.0), (-0.9, -0.5, 8.0, 0.88, 0.0), (-1.3, -0.8, 11.0, 0.84, 0.0),
                              (-1.5, -0.9, 12.0, 0.82, 0.0))), puff=(0.35, 0.7, 1.0, 1.15), coil=True),
    "rock_back": {"ahead": (-0.4, -0.8, -1.0, -1.1), "sq": (0.98, 1.02, 1.05, 1.06), "tilt": (-6.0, -12.0, -16.0, -18.0),
                  "puff": (0.4, 0.8, 1.1, 1.25), "sway": 0.4, "stand": 0.25, "glare": 2, "maw": 2},
    # attack
    "leap_kick": dict(_hop(((2.6, 2.6, 16.0, 1.2, 1.0), (4.0, 5.4, 4.0, 1.1, 1.0), (1.2, 6.4, -8.0, 0.92, 0.6), (0.0, 6.6, -4.0, 0.8, 0.0),
                            (0.0, 6.4, 0.0, 0.96, 0.0), (0.0, 6.2, 0.0, 1.0, 0.0))), puff=(0.4, 0.2, 0.1, 0.0, 0.0, 0.0), dust=(2, 3)),
    "tongue_lash": {"sq": (1.02, 0.96, 0.98, 1.02, 1.0, 1.0), "tilt": (6.0, 8.0, 6.0, 2.0, 0.0, 0.0), "puff": (0.2, 0.0, 0.0, 0.1, 0.5, 0.2),
                    "reach": (7.0, 15.0, 11.0, 5.0, 0.0, 0.0), "maw": 4},
    # hurt
    "knock_flat": dict(_hop(((0.4, -2.4, -10.0, 0.82, 0.3), (0.2, -1.6, -4.0, 1.04, 0.1), (0.0, -0.6, 0.0, 1.0, 0.0))), puff=(0.0, 0.0, 0.0)),
    "squash": {"ahead": (-2.0, -1.2, -0.4), "sq": (0.8, 1.04, 1.0), "tilt": (-8.0, -3.0, 0.0), "puff": (0.0, 0.1, 0.0)},
    # death
    "flip_back": dict(_hop(((1.4, -0.6, 14.0, 1.1, 0.6), (2.4, -1.0, 20.0, 1.0, 0.8), (1.6, -1.2, 10.0, 1.0, 0.9), (0.6, -1.2, 0.0, 1.0, 1.0),
                            (0.0, -1.2, 0.0, 0.9, 1.0), (0.0, -1.2, 0.0, 1.0, 1.0), (0.0, -1.2, 0.0, 1.0, 1.0), (0.0, -1.2, 0.0, 1.0, 1.0))),
                      roll=(10.0, 50.0, 110.0, 160.0, 178.0, 174.0, 178.0, 178.0), land=(3.0, 0.4)),
    "flop_back": {"hop": (0.8, 1.6, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0), "roll": (10.0, 40.0, 100.0, 150.0, 176.0, 172.0, 176.0, 176.0),
                  "land": (4.0, 0.6), "droop": 0.35},
}

FROG = {
    "Z": 4.6, "back": -0.6,
    "body": [{"at": (0.0, 0.0, 0.0), "r": (5.4, 4.2, 3.2)}, {"at": (4.4, 0.0, 0.6), "r": (3.3, 3.8, 2.5)}],
    "skin": {"kind": "stripe", "belly": -0.35, "stripe": (2.9, 3.6), "spots": ((-1.8, 1.2, 0.7), (0.6, -1.6, 0.6), (-3.4, -0.6, 0.6),
                                                                               (1.8, 1.4, 0.5), (-0.6, 0.2, 0.5))},
    "throat": {"at": (5.6, 0.0, -1.7), "r": (1.8, 2.5, 1.1), "puff": (0.4, 1.2, 1.4, 1.5)},
    "eyes": {"kind": "bead", "at": (5.0, 2.2, 2.7), "r": 1.55, "pupil": ((1.2, 0.5, 0.6), (1.3, 0.3, 0.2)), "glint": (0.4, 0.1, 1.4),
             "shut": {"hurt": 0, "death": 4}, "mouth": (7.2, 1.4, -0.2)},
    "legs": {"kind": "spring", "hip": (-3.8, 3.4, -1.0), "folded": ((0.0, 5.2, 2.0), (-3.4, 5.4, 0.6)),
             "straight": ((-7.0, 3.8, -1.4), (-10.2, 3.6, -2.2)), "thigh": ((0.8, 0.0, 0.0), (3.0, 1.8, 1.9)),
             "r": ((1.6, 1.25), (1.15, 0.85)), "foot": ((-0.9, 1.0), (2.0, 1.4, 0.5)),
             "arm": {"shoulder": (3.6, 2.4, -1.2), "hand": (4.4, 3.0), "reach": 2.4, "r": (0.9, 0.75), "paw": (1.1, 1.0, 0.45)}},
}
TOAD = {
    "Z": 4.4, "back": -1.0,
    "body": [{"at": (0.0, 0.0, 0.0), "r": (6.8, 6.4, 3.9)}, {"at": (5.0, 0.0, 0.4), "r": (4.0, 5.5, 2.7)},
             {"at": (7.9, 0.0, -0.3), "r": (2.0, 4.0, 1.7), "flat": True, "puff": 0.6}],
    "skin": {"kind": "moss"},
    "glands": {"at": (2.4, 3.8, 2.9), "r": (2.4, 1.4, 1.0)},
    "moss": ((-4.4, 0.8, 3.2), (0.6, 2.8, 3.2), (-1.6, -3.0, 3.2), (-5.4, -1.8, 2.3)),
    "ferns": ((-2.4, 1.8), (-0.2, -1.2), (-4.6, -0.4)),
    "eyes": {"kind": "lidded", "at": ((5.4, -0.4), (2.9, 0.3), (2.5, 1.0)), "r": 1.75, "shut": {"hurt": 0, "death": 3}},
    "throat": {"at": (6.3, 0.0, -2.4), "r": (1.8, 3.0, 1.2), "puff": (0.0, 1.3, 1.6, 1.4), "cheeks": True},
    "legs": {"kind": "squat"},
    "tongue": {"mouth": (9.2, 0.0, -0.8)},
}
VARIANTS = {
    "frog": {"parts": FROG, "mats": {"skin": "frog", "belly": "frog_belly", "stripe": "frog_stripe", "sac": "frog_sac", "eye": "frog_eye",
                                     "foot": "frog_belly"},
             "motion": {"idle": "gulp", "walk": "hop", "windup": "crouch_puff", "attack": "leap_kick", "hurt": "knock_flat",
                        "death": "flip_back"}},
    "toad": {"parts": TOAD, "mats": {"skin": "toad", "belly": "toad_belly", "moss": "toad_moss", "fern": "toad_fern", "sac": "toad_sac",
                                     "eye": "toad_eye", "leg": "toad_leg", "tongue": "tongue", "maw": "maw"},
             "motion": {"idle": "breathe", "walk": "heavy_hop", "windup": "rock_back", "attack": "tongue_lash", "hurt": "squash",
                        "death": "flop_back"}},
}


class _F:
    pass


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    P = Pose()
    p = B.parts
    c = _F()
    c.action, c.f = action, f
    # Head-on (decision 44): walking away a toad's golden eyes rise over the moss of its back and its folded hind legs
    # spread at its sides, so a toad's back reads and not a mound of moss.
    c.fr, c.bk = headon(view)
    st = B.style(action)
    c.hop = B.pick("hop", action, f)
    c.ahead = B.pick("ahead", action, f)
    c.tilt = B.pick("tilt", action, f)
    c.sq = B.pick("sq", action, f, 1.0)
    c.stretch = B.pick("stretch", action, f)
    if action == "idle" and "breathe" in st:
        c.sq = 1.0 + st.breathe * wave(action, f)
    c.puff = B.pick("puff", action, f)
    c.z = p.Z * c.sq + c.hop
    c.tm = rot("b", c.tilt)
    c.C = v3(c.ahead + p.back, 0.0, c.z)
    C, tm = c.C, c.tm
    c.at = lambda q: C + tm @ v3(q)
    c.paint = _skin(B, c)
    _body(P, B, c)
    if p.skin.kind == "stripe":
        _throat(P, B, c)
        for s in (1, -1):
            _eye_bead(P, B, c, s)
            _legs_spring(P, B, c, s)
    else:
        _back(P, B, c)
        for s in (1, -1):
            _eye_lidded(P, B, c, s)
        _throat(P, B, c)
        _legs_squat(P, B, c)
        _tongue(P, B, c)
    if f in st.get("dust", ()):
        for k in range(4):
            ang = math.radians(k * 90.0 + 45.0)
            P.fx.append((v3(c.ahead + math.cos(ang) * 5.6, math.sin(ang) * 5.0, 0.3), M.DUST_DIM))
    roll = B.pick("roll", action, f)
    if roll:
        z = c.z
        land, lift = st.land
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, z)
        P.shift = v3(-turned[0], -turned[1], z - turned[2] - (z - land) * (1.0 if roll > 90 else math.sin(math.radians(roll))) + (lift if roll > 150 else 0.0))
    return P


def _skin(B, c):
    sk, m = B.parts.skin, B.mats
    C, tm = c.C, c.tm
    if sk.kind == "stripe":
        def skin(q, n):
            """The pale belly underneath; a stripe down each flank; darker spots over the back."""
            loc = (q - C) @ tm
            nz = (n @ tm)[:, 2]
            b = np.abs(loc[:, 1])
            belly = nz < sk.belly
            stripe = (b > sk.stripe[0]) & (b < sk.stripe[1]) & (nz > -0.15) & (nz < 0.6)
            spot = np.zeros(len(b), dtype=bool)
            for pa, pb, r in sk.spots:
                spot |= (loc[:, 0] - pa) ** 2 + (loc[:, 1] - pb) ** 2 < r * r
            names = np.where(belly, m.belly, np.where(stripe, m.stripe, m.skin)).astype(object)
            return names, np.where(spot & ~belly & ~stripe & (nz > 0.3), -1, 0).astype(np.int16)
        return skin

    def hide(q, n):
        """The cream belly underneath; the moss over the back behind the head, its edge ragged; warts a step lit."""
        loc = (q - C) @ tm
        nl = n @ tm
        belly = nl[:, 2] < -0.4
        edge = 0.4 + 0.28 * h01v(np.floor(loc[:, 0] * 1.5 + 30), np.floor(loc[:, 1] * 1.5 + 30), 11)
        moss = (loc[:, 0] < 3.0) & (nl[:, 2] > edge) & ~belly
        wart = (h01v(np.floor(loc[:, 0] * 1.1 + 50), np.floor(loc[:, 1] * 1.1 + 50), 3) > 0.84) & ~moss & ~belly
        names = np.where(belly, m.belly, np.where(moss, m.moss, m.skin)).astype(object)
        return names, np.where(wart, 1, 0).astype(np.int16)
    return hide


def _body(P, B, c) -> None:
    sq, at = c.sq, c.at
    for i, piece in enumerate(B.parts.body):
        rx, ry, rz = piece.r
        r = (rx, ry + c.puff * piece.puff, rz) if piece.get("flat") else (rx, ry, rz * sq)
        P.add(E(c.C if i == 0 else at(piece.at), r, B.mats.skin, "body", c.tm, c.paint))


def _throat(P, B, c) -> None:
    """The throat sac, pale, puffing out under the chin (big in the tell); the toad's cheeks bulge with it."""
    t, m, puff, at = B.parts.throat, B.mats, c.puff, c.at
    k = t.puff
    P.add(E(at((t.at[0], t.at[1], t.at[2] - puff * k[0])), (t.r[0] + puff * k[1], t.r[1] + puff * k[2], t.r[2] + puff * k[3]),
            m.sac, "throat", c.tm))
    if t.get("cheeks") and puff > 0.3:
        for s in (1, -1):
            P.add(E(at((5.4, s * 4.4, -0.4)), (1.4 + puff, 1.0 + puff * 0.9, 1.1 + puff * 0.8), m.sac, "cheek%d" % s, c.tm))


def _eye_bead(P, B, c, s: int) -> None:
    """A gold eye set high, a pupil and a glint (shut when struck or beaten), and the mouth's corner under it."""
    e, m, at, tm, a, f = B.parts.eyes, B.mats, c.at, c.tm, c.action, c.f
    eye = at((e.at[0], s * e.at[1], e.at[2] * c.sq))
    P.add(S(eye, e.r, m.eye, "eye%d" % s))
    closed = shut(e, a, f)
    (pa, pb, pc), (qa, qb, qc) = e.pupil
    (P.mark if closed else P.eye)(eye + tm @ v3(pa, s * pb, pc), M.RAMPS[m.skin][1] if closed else M.INKY)
    P.mark(eye + tm @ v3(qa, s * qb, qc), M.RAMPS[m.skin][1] if closed else M.INKY)
    if not closed:
        P.mark(eye + tm @ v3(e.glint[0], s * e.glint[1], e.glint[2]), M.GLINT)
    P.mark(at((e.mouth[0], s * e.mouth[1], e.mouth[2])), M.RAMPS[m.skin][0])


def _legs_spring(P, B, c, s: int) -> None:
    """Hind legs folded at the sides (thigh forward, shin back, the long foot flat), trailing straight in a leap; front
    legs short props under the chest, reaching ahead in a leap; coiled tighter in the tell."""
    g, m, at = B.parts.legs, B.mats, c.at
    ahead, z, stretch, hop = c.ahead, c.z, c.stretch, c.hop
    hip = v3(ahead + g.hip[0], s * g.hip[1], z + g.hip[2])
    (fk, ff) = g.folded
    (sk, sf) = g.straight
    folded = (v3(ahead + fk[0], s * fk[1], fk[2]), v3(ahead + ff[0], s * ff[1], ff[2]))
    straight = (v3(ahead + sk[0], s * sk[1], z + sk[2]), v3(ahead + sf[0], s * sf[1], z + sf[2]))
    knee = folded[0] + (straight[0] - folded[0]) * stretch
    foot = folded[1] + (straight[1] - folded[1]) * stretch
    if B.style(c.action).get("coil"):
        knee = knee + v3(0.4, s * 0.4, -0.3 * c.f)
    P.add(E(hip + v3(g.thigh[0]), g.thigh[1], m.skin, "hind%d" % s, rot("c", s * 20.0), c.paint),
          L(hip, knee, g.r[0][0], g.r[0][1], m.skin, "hind%d" % s), L(knee, foot, g.r[1][0], g.r[1][1], m.skin, "hind%d" % s),
          E(foot + v3(g.foot[0][0] if stretch > 0.5 else g.foot[0][1], 0.0, 0.0), g.foot[1], m.foot, "hind%d" % s))
    arm = g.arm
    reach = arm.reach * stretch
    shoulder = at((arm.shoulder[0], s * arm.shoulder[1], arm.shoulder[2]))
    hand = v3(ahead + arm.hand[0] + reach, s * arm.hand[1], 0.6 + (hop * 0.6 if stretch > 0.5 else 0.0))
    P.add(L(shoulder, hand, arm.r[0], arm.r[1], m.skin, "arm%d" % s), E(hand, arm.paw, m.foot, "arm%d" % s))


def _back(P, B, c) -> None:
    """The toad's back: parotoid glands, moss tufts breaking the line, and three fiddlehead ferns curling up out of it,
    swaying (up in the tell, drooping in death)."""
    p, m, a, f, at, sq = B.parts, B.mats, c.action, c.f, c.at, c.sq
    st = B.style(a)
    g = p.glands
    for s in (1, -1):
        P.add(E(at((g.at[0], s * g.at[1], g.at[2] * sq)), g.r, m.skin, "gland%d" % s, c.tm, line=False))
    sway = st.sway * wave(a, f) if a in ("idle", "walk") else st.get("sway", 0.0)
    stand = 1.0 + (st.stand * f / 3.0 if "stand" in st else 0.0) - (st.droop * min(1.0, f / 4.0) if "droop" in st else 0.0)
    for q in p.moss:
        P.add(E(at((q[0], q[1], q[2] * sq)), (1.3, 1.2, 0.9), m.moss, "moss", c.tm, line=False))
    for k, (a0, b0) in enumerate(p.ferns):
        sv = sway * (1.0 if k % 2 else -1.0)
        h0 = 3.6 * sq
        pts = [(a0, b0, h0), (a0 - 0.4, b0 + sv * 0.3, h0 + 2.0 * stand), (a0 - 0.1, b0 + sv * 0.6, h0 + 3.8 * stand),
               (a0 + 1.0, b0 + sv * 0.8, h0 + 4.6 * stand), (a0 + 1.7, b0 + sv * 0.8, h0 + 3.8 * stand), (a0 + 1.0, b0 + sv * 0.7, h0 + 3.1 * stand)]
        P.add(chain([at(q) for q in pts], 0.7, 0.55, m.fern, "fern%d" % k, line=False))


def _eye_lidded(P, B, c, s: int) -> None:
    """A golden eye on top of the head, a black slit in it, a heavy lid (lower in the tell's glare); the wide
    down-turned mouth under it."""
    e, m, a, f, at, tm, sq, bk = B.parts.eyes, B.mats, c.action, c.f, c.at, c.tm, c.sq, c.bk
    (ea, eab), (eb, ebb), (ec, ecb) = e.at
    eye = at((ea + eab * bk, s * (eb + ebb * bk), ec * sq + ecb * bk))
    P.add(S(eye, e.r, m.eye, "eye%d" % s))
    closed = shut(e, a, f)
    if not closed:
        P.eye(eye + tm @ v3(1.6, s * 0.4, 0.5), M.INKY)
        P.mark(eye + tm @ v3(1.3, s * 0.5, 1.0), M.INKY)
        P.mark(eye + tm @ v3(0.8, s * 0.3, 1.5), M.GLINT)
    glare = B.style(a).get("glare")
    lid = 1.0 if closed else (0.6 if glare is not None and f >= glare else 0.25)
    P.add(E(eye + tm @ v3(-0.2, 0.0, 0.5 + 0.7 * (1 - lid)), (1.9, 1.8, 0.9), m.skin, "lid%d" % s, tm, line=False))
    for u in (38.0, 58.0, 78.0):
        q = math.radians(s * u)
        P.mark(at((7.9 + 2.2 * math.cos(math.radians(-16)) * math.cos(q), 4.2 * math.sin(q), -0.3 + 1.9 * math.sin(math.radians(-16)))), M.TOAD_MOUTH)


def _legs_squat(P, B, c) -> None:
    """The thick hind legs folded at its sides, trailing in a hop; short front legs propping the chest."""
    m, at, ahead, z, hop, bk = B.mats, c.at, c.ahead, c.z, c.hop, c.bk
    air = hop > 1.2
    for s in (1, -1):
        if air:
            hip, knee, foot = v3(ahead - 4.2, s * 3.8, z - 1.0), v3(ahead - 7.4, s * 4.8, z - 1.8), v3(ahead - 10.2, s * 4.4, z - 2.4)
        else:
            hip, knee = v3(ahead - 4.0, s * 4.6, z - 1.6), v3(ahead + 0.4, s * (6.8 + 1.4 * bk), 2.2)
            foot = v3(ahead - 3.0 - 0.6 * bk, s * (7.0 + 1.6 * bk), 0.6)
        P.add(E(hip + v3(0.6, 0.0, 0.0), (3.2, 2.2, 2.3), m.skin, "hind%d" % s, rot("c", s * 20.0), c.paint),
              L(hip, knee, 1.8, 1.4, m.leg, "hind%d" % s), L(knee, foot, 1.3, 1.0, m.leg, "hind%d" % s),
              E(foot + v3(-0.8 if air else 1.0, 0.0, 0.0), (2.1, 1.5, 0.55), m.leg, "hind%d" % s))
        hand = v3(ahead + 5.4 + (1.8 if air else 0.0), s * 4.8, 0.6 + (hop * 0.5 if air else 0.0))
        P.add(L(at((3.8, s * 3.6, -2.2)), hand, 1.25, 1.0, m.leg, "arm%d" % s), E(hand, (1.3, 1.1, 0.5), m.leg, "arm%d" % s))


def _tongue(P, B, c) -> None:
    """The mouth opens on its dark maw (from the tell's `maw` frame, through the lash); the tongue lashes out to its
    full reach on the hit, a glint at its sticky tip."""
    m, a, f, at = B.mats, c.action, c.f, c.at
    st = B.style(a)
    mouth = at(B.parts.tongue.mouth)
    if a == "windup" and f >= st.get("maw", 99) or a == "attack" and f < st.get("maw", 0):
        P.add(E(mouth + v3(-0.3, 0.0, -0.2), (1.0, 2.6, 0.7), m.maw, "maw", c.tm))
    reach = B.pick("reach", a, f)
    if reach > 0:
        tip = v3(mouth[0] + reach, 0.0, max(2.4, mouth[2] - reach * 0.06))
        mid = (mouth + tip) * 0.5 + v3(0.0, 0.0, 0.6 if f in (0, 2) else 0.2)
        P.add(chain([mouth, mid, tip], 0.95, 0.8, m.tongue, "tongue"), S(tip, 1.55, m.tongue, "tongue"))
        if f == 1:
            for d in ((1.9, 0.0, 1.6), (2.5, 0.0, 2.2), (1.3, 0.0, 2.2), (1.9, 0.0, 2.8)):
                P.glow.append((tip + v3(*d), M.GLINT))
