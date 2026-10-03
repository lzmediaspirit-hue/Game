"""The shelled plan (audit 45 §6.2), from Old Snapper (`snapper`): a domed shell over a rim and a plastron, a head that
reaches out of it, legs splayed from under it, and what a species carries besides.

  shell  the dome, the rim and the plastron (their sizes), the dome's paint (`moss`: moss in patches over plates whose
         seams show under it), and the options laid on it: knobbed keels, a serrated back edge, barnacles, river weed
  head   `beaked`: a thick neck, a big head, a pale hooked beak and a jaw that gapes, glowing eyes; pulled in when struck
  legs   `pillar`: thick scaled legs in diagonal pairs, pads and talons; tucked when struck, pawing on its back
  tail   `saw`: a tapering tail with a row of saw plates
  claw   `crusher`: a great claw on one side (an arm, a palm, a fixed finger and a moving dactyl), held low, raised in the
         tell, slammed down on the blow in a burst of water and mud

The motion styles (STYLES): idle `breathe_snap`, walk `lumber`, windup `rear_crusher`, attack `slam_crusher`, hurt
`pull_in`, death `roll_plastron`. Channels: lunge, rear (the shell's pitch), sink, neck (how far the head is out),
hpitch, gape, crusher (elbow, palm, pitch, yaw, open), roll, curl (legs), tuck (legs), splash.
"""
from __future__ import annotations

import math

import numpy as np

from .. import mats as M
from ..motion import gait, h01v, headon, wave
from ..sculpt import E, L, Pose, S, chain, rot, v3

STYLES = {
    "breathe_snap": {"breathe": (0.0, 0.25, 0.4, 0.35, 0.15, 0.0), "gape": (0.0, 0.0, 0.12, 0.2, 0.05, 0.0),
                     "snap": (0.3, 0.45, 0.65, 0.55, 0.35, 0.3), "sway_amp": 0.8, "bob_amp": 0.25, "wag_amp": 0.5},
    "lumber": {"kind": "lumber", "rock_amp": 3.2, "sway_amp": 1.0, "bob_step": 0.4, "swing": 0.8, "wag_amp": 1.0},
    "rear_crusher": {"lunge": (-0.4, -0.8, -1.2, -1.4), "rear": (3.0, 6.0, 8.0, 9.0), "neck": (1.1, 1.15, 1.2, 1.2),
                     "hpitch": (6.0, 12.0, 16.0, 18.0), "gape": (0.3, 0.5, 0.7, 0.8),
                     "crusher": (((8.6, -11.4, 3.6), (9.4, -10.6, 9.0), 50.0, -10.0, 0.6), ((8.2, -11.2, 5.6), (8.8, -10.4, 13.0), 72.0, -10.0, 0.8),
                                 ((7.8, -11.0, 7.2), (8.0, -10.2, 16.0), 88.0, -10.0, 1.0), ((7.6, -11.0, 7.6), (7.8, -10.2, 17.0), 92.0, -10.0, 1.0))},
    "slam_crusher": {"lunge": (0.4, 1.6, 1.8, 1.4, 0.8, 0.3), "rear": (4.0, -3.0, -2.0, -0.6, 0.4, 0.2), "sink": (0.0, 0.8, 0.6, 0.2, 0.0, 0.0),
                     "hpitch": (6.0, -14.0, -12.0, -6.0, -2.0, 0.0), "gape": (0.8, 0.2, 0.3, 0.2, 0.1, 0.0),
                     "crusher": (((10.2, -11.0, 5.0), (13.6, -10.2, 9.0), 40.0, -8.0, 0.8), ((10.8, -10.4, -1.8), (14.6, -8.8, -3.4), -14.0, -6.0, 0.0),
                                 ((10.8, -10.4, -1.9), (14.6, -8.8, -3.5), -16.0, -6.0, 0.0), ((10.6, -10.6, -1.4), (14.0, -9.2, -2.6), -8.0, -8.0, 0.1),
                                 ((10.2, -10.8, -1.0), (13.4, -9.6, -0.8), 6.0, -10.0, 0.25), ((10.0, -11.0, -1.1), (13.2, -10.0, 0.4), 18.0, -10.0, 0.35)),
                     "splash": (0.0, 1.0, 1.6, 2.0, 0.0, 0.0), "squash": {1: (1.03, 1.03, 0.93)}},
    "pull_in": {"lunge": (-1.8, -1.0, -0.3), "rear": (-2.0, 0.0, 0.0), "sink": (0.6, 0.3, 0.0), "neck": (0.15, 0.45, 0.8),
                "gape": (0.5, 0.2, 0.0), "curl": (0.0, 0.0, 0.0), "tuck": (0.6, 0.35, 0.1), "shut": True,
                "crusher": (((8.8, -10.8, -1.4), (11.4, -10.8, -1.6), 4.0, -14.0, 0.3), ((9.2, -10.8, -1.3), (12.2, -10.6, -0.8), 10.0, -12.0, 0.3),
                            ((9.8, -11.0, -1.2), (13.0, -10.2, 0.2), 18.0, -10.0, 0.35))},
    "roll_plastron": {"rear": (4.0, -2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), "sink": (0.0, 1.0, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4),
                      "neck": (1.0, 0.8, 0.6, 0.5, 0.4, 0.4, 0.4, 0.4), "hpitch": (10.0, -6.0, -12.0, -14.0, -14.0, -14.0, -14.0, -14.0),
                      "gape": (0.6, 0.5, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3),
                      "crusher": (((9.8, -11.0, 1.0), (12.4, -10.4, 4.0), 30.0, -12.0, 0.6),) + (((9.6, -11.0, -2.4), (11.6, -11.0, -2.6), -8.0, -20.0, 0.5),) * 7,
                      "roll": (0.0, 0.0, 30.0, 80.0, 130.0, 172.0, 176.0, 174.0), "curl": (0.0, 0.1, 0.3, 0.6, 0.8, 1.0, 0.8, 1.0),
                      "shut_from": 5, "paw": (4, 6), "edge": (10.0, 6.4)},
}

SNAPPER = {
    "Z": 6.6,
    "shell": {"rim": ((0.0, 0.0, -2.6), (12.0, 10.4, 2.2)), "plastron": ((0.4, 0.0, -3.6), (10.2, 8.6, 1.9)),
              "dome": ((0.0, 0.0, -0.8), (11.0, 9.4, 5.8)), "paint": "moss",
              "keels": ((0.0, (-6.8, -3.6, -0.4, 2.8, 5.8)), (4.3, (-5.0, -1.6, 1.8)), (-4.3, (-5.0, -1.6, 1.8))),
              "serrate": (144.0, 162.0, 180.0, 198.0, 216.0),
              "barnacles": ((32.0, 30.0), (52.0, 10.0), (-38.0, 25.0), (76.0, 35.0), (-72.0, 15.0), (112.0, 25.0), (-110.0, 20.0)),
              "on_rim": (12.2, 10.6, 2.4), "weed": (-4.2, 0.8, 5.0)},
    "head": {"kind": "beaked", "neck": ((7.2, 0.0, -1.4), (10.4, 3.6, -0.9), (2.6, 2.8)), "skull": (4.0, 3.5, 3.1),
             "scales": (4.2, 3.7, 3.3),
             "beak": ((3.6, 0.0, -0.4), (2.0, 2.3, 2.0)), "shut_from": 5},
    "legs": {"kind": "pillar", "at": ((5.6, 8.4), (5.6, -8.4), (-6.0, 8.0), (-6.0, -8.0)), "lift": 1.4, "stride": 1.6},
    "tail": {"kind": "saw", "root": (-9.8, 0.0, -2.6), "tip": (-18.4, 1.2), "r": (2.0, 0.7)},
    "claw": {"kind": "crusher", "rest": ((10.0, -11.0, -1.2), (13.2, -10.0, 0.6), 22.0, -10.0), "root": (6.8, -7.6, -1.6)},
}
BEETLE_STYLES = {
    "twitch": {"antennae": (0.0, 0.6, 1.0, 0.2, -0.6, -0.2), "bob": (0.0, 0.05, 0.1, 0.1, 0.05, 0.0)},
    "tripod": {"kind": "tripod", "rock_amp": 2.5, "bob_step": 0.25},
    "curl_up": {"lunge": (-0.3, -0.7, -0.9, -1.0), "pitch": (-6.0, -10.0, -6.0, 0.0), "ball": (0.18, 0.5, 0.85, 1.0),
                "spin": (0.0, 0.0, -14.0, -26.0), "antennae": (0.6, 0.2, -0.4, -0.8), "dust": (2, 3)},
    "roll_charge": {"lunge": (3.4, 6.2, 6.8, 5.8, 3.2, 1.0), "ball": (1.0, 1.0, 1.0, 0.75, 0.35, 0.0),
                    "spin": (120.0, 250.0, 320.0, 350.0, 360.0, 360.0), "squash": {1: (0.9, 1.04, 1.08)}, "dust": (0, 1, 2),
                    "streaks": (0, 1), "spark": 1},
    "jolt": {"lunge": (-2.4, -1.4, -0.4), "pitch": (16.0, 6.0, 0.0), "splay": (1.0, 0.5, 0.0), "antennae": (-1.0, 0.4, 0.0),
             "squash": {0: (0.9, 1.0, 1.08), 1: (1.04, 1.0, 0.97)}},
    "flip_legs": {"lunge": (-0.4, -0.6, -0.6, -0.6, -0.6, -0.6, -0.6, -0.6), "pitch": (12.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                  "roll": (8.0, 40.0, 100.0, 150.0, 176.0, 172.0, 178.0, 176.0), "curl": (0.0, 0.1, 0.3, 0.6, 0.8, 1.0, 0.85, 1.0),
                  "paw": (4, 6), "edge": (6.0, 3.0), "shut_from": 4},
}
STYLES.update(BEETLE_STYLES)

BEETLE = {
    "Z": 2.9,
    "shell": {"kind": "beetle", "elytra": ((-1.4, 0.0, 0.3), (6.2, 4.9, 2.9)), "pronotum": ((4.1, 0.0, 0.2), (2.5, 4.0, 2.4)),
              "under": ((0.2, 0.0, -0.9), (6.2, 3.9, 1.4)), "ball": 4.6, "seams": (-4.2, -1.2, 1.6), "lichen": 0.74,
              "specks": 9, "lumps": ((-5.4, 1.6, 1.1), (-2.8, 2.6, 1.3), (-0.2, 2.3, 1.2), (-4.0, -2.2, 1.2), (-1.4, -2.9, 1.1),
                                     (0.8, -1.6, 1.0), (-2.4, 0.9, 0.9), (-6.6, -0.6, 0.9))},
    "head": {"kind": "horned", "at": (6.6, 0.0, -0.3), "r": (1.8, 2.1, 1.5), "lift": 26.0,
             "horn": ((0.9, 0.0, 0.7), (2.2, 0.0, 1.6), (2.9, 0.0, 3.0), (2.5, 0.0, 4.1)), "horn_r": (1.05, 0.35),
             "eyes": (1.0, 1.8, 0.3), "antennae": ((1.3, 1.0, 0.4), (2.6, 2.1, 1.1), (3.3, 3.0, 1.2)), "club": 0.5},
    "legs": {"kind": "jointed", "at": (2.8, 0.2, -2.6), "hip": (3.0, -0.8), "knee": (5.4, 0.5), "foot": (6.7, 0.3),
             "lean": (2.2, 0.3, -2.2), "r": ((0.62, 0.52), (0.5, 0.28)), "lift": 1.2, "stride": 1.4},
}
VARIANTS = {
    "snapper": {"parts": SNAPPER, "mats": {"shell": "snap_shell", "moss": "snap_moss", "moss_lit": "snap_moss_lit", "skin": "snap_skin",
                                           "belly": "snap_belly", "beak": "snap_beak", "claw": "crusher", "tip": "crusher_tip",
                                           "weed": "weed", "eye": "snap_eye", "maw": "maw"},
                "motion": {"idle": "breathe_snap", "walk": "lumber", "windup": "rear_crusher", "attack": "slam_crusher",
                           "hurt": "pull_in", "death": "roll_plastron"}},
    "beetle": {"parts": BEETLE, "mats": {"rock": "beetle_rock", "pronotum": "beetle_pronotum", "lichen": "beetle_lichen",
                                         "chitin": "beetle_chitin", "horn": "beetle_horn"},
               "motion": {"idle": "twitch", "walk": "tripod", "windup": "curl_up", "attack": "roll_charge", "hurt": "jolt",
                          "death": "flip_legs"}},
}


class _F:
    pass


def pose(B, action: str, f: int, view: float = 48.0) -> Pose:
    if B.parts.shell.get("kind") == "beetle":
        return _beetle(B, action, f, view)
    P = Pose()
    p = B.parts
    st = B.style(action)
    c = _F()
    c.action, c.f, c.st = action, f, st
    c.lunge = B.pick("lunge", action, f)
    c.rock = st.rock_amp * math.sin(f / 8.0 * math.tau) if st.get("kind") == "lumber" else 0.0
    breathe = B.pick("breathe", action, f)
    rear = B.pick("rear", action, f)
    c.z = p.Z + breathe * 0.4 - B.pick("sink", action, f)
    c.C = v3(c.lunge, 0.0, c.z)
    c.bm = rot("a", c.rock) @ rot("b", rear)
    C, bm = c.C, c.bm
    c.at = lambda q: C + bm @ v3(q)
    _shell(P, B, c)
    {"beaked": _head_beaked}[p.head.kind](P, B, c)
    {"pillar": _legs_pillar}[p.legs.kind](P, B, c)
    if "tail" in p:
        {"saw": _tail_saw}[p.tail.kind](P, B, c)
    if "claw" in p:
        {"crusher": _crusher}[p.claw.kind](P, B, c)
    roll = B.pick("roll", action, f)
    if roll:
        edge, back = st.edge
        z = c.z
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, z)
        r = math.sin(math.radians(roll))
        h = z + (edge - z) * r if roll <= 90.0 else back + (edge - back) * r
        P.shift = v3(-turned[0], -turned[1], h - turned[2])
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (c.lunge, 0.0, 0.0))
    return P


# ------------------------------------------------------------------------------------------------ the shell
def _shell(P, B, c) -> None:
    """The dome, the rim and the plastron; the keels, the serrated back edge, barnacles on the rim, river weed."""
    p, m = B.parts, B.mats
    sh = p.shell
    C, bm, at = c.C, c.bm, c.at
    a_, f = c.action, c.f

    def local(q, n):
        return (q - C) @ bm, n @ bm

    def seams(a, b):
        """The seams between the shell's plates: a row of five down the spine, four a side beside it."""
        ring = np.abs(np.abs(b) - 3.9) < 0.45
        rows = np.where(np.abs(b) < 3.9, np.min(np.abs(a[:, None] - np.array([-5.0, -1.4, 2.2, 5.6])[None, :]), axis=1),
                        np.min(np.abs(a[:, None] - np.array([-3.2, 0.6, 4.2])[None, :]), axis=1)) < 0.45
        return ring | rows

    def carapace(q, n):
        """Moss over the dome's top in patches, lighter blotches in it and the plates' seams faint under it; the dark
        green plates on the flanks, their seams a step darker; the pale plastron underneath."""
        loc, ln = local(q, n)
        a, b = loc[:, 0], loc[:, 1]
        seam = seams(a, b)
        belly = ln[:, 2] < -0.25
        edge = 0.7 - 0.16 * h01v(np.floor(a * 1.2 + 40), np.floor(b * 1.2 + 40), 3)
        moss = (ln[:, 2] > edge) & ~belly
        lit = moss & (h01v(np.floor(a * 0.9 + 40), np.floor(b * 0.9 + 40), 5) > 0.72)
        names = np.where(belly, m.belly, np.where(lit, m.moss_lit, np.where(moss, m.moss, m.shell))).astype(object)
        return names, np.where(seam & ~belly, -1, 0).astype(np.int16)

    rim_c, rim_r = at(sh.rim[0]), sh.rim[1]

    def rim(q, n):
        loc, ln = local(q, n)
        belly = ln[:, 2] < -0.35
        seam = (np.degrees(np.arctan2(loc[:, 1] / rim_r[1], loc[:, 0] / rim_r[0])) % 30.0) < 5.0
        return np.where(belly, m.belly, m.shell).astype(object), np.where(seam & ~belly, -1, 0).astype(np.int16)

    def plastron(q, n):
        loc, _ = local(q, n)
        seam = (np.abs(loc[:, 1]) < 0.45) | (np.min(np.abs(loc[:, 0][:, None] - np.array([-4.2, 0.2, 4.4])[None, :]), axis=1) < 0.45)
        return np.full(len(q), m.belly, dtype=object), np.where(seam, -1, 0).astype(np.int16)

    (da, db, dc), (ra, rb, rc) = sh.dome
    P.add(E(rim_c, rim_r, m.shell, "shell", bm, rim),
          E(at(sh.plastron[0]), sh.plastron[1], m.belly, "shell", bm, plastron),
          E(at(sh.dome[0]), sh.dome[1], m.shell, "shell", bm, carapace))
    # Three keels of knobs along the dome, and the serrated back edge.
    for b0, row in sh.keels:
        for a0 in row:
            top = dc + rc * math.sqrt(max(0.0, 1.0 - (a0 / ra) ** 2 - (b0 / rb) ** 2))
            P.add(E(at((a0, b0, top - 0.1)), (1.4, 1.0, 1.0), m.shell, "keel", bm, carapace, line=False))
    rz = rim_c
    for ang in sh.serrate:
        P.add(E(at((rim_r[0] * math.cos(math.radians(ang)), rim_r[1] * math.sin(math.radians(ang)), sh.rim[0][2])), (1.4, 1.4, 1.0), m.shell, "shell", bm))
    for u, v in sh.barnacles:
        for du, dv, col in ((0.0, 0.0, M.BARNACLE), (4.0, -12.0, M.BARNACLE_SHADE)):
            cu, su = math.cos(math.radians(u + du)), math.sin(math.radians(u + du))
            cv, sv = math.cos(math.radians(v + dv)), math.sin(math.radians(v + dv))
            P.mark(rz + bm @ v3(sh.on_rim[0] * cv * cu, sh.on_rim[1] * cv * su, sh.on_rim[2] * sv), col)
    # River weed trailing from the back edge, stirring as it moves.
    sway = c.st.sway_amp * wave(a_, f) if "sway_amp" in c.st else 0.3
    for k, b0 in enumerate(sh.weed):
        root = at((-11.2 + abs(b0) * 0.2, b0, -2.4))
        tip = v3(c.lunge - 15.0 - k * 0.6, b0 * 1.1 + sway * (1.0 if k % 2 else -1.0), 0.8)
        midp = (root + tip) * 0.5 + v3(0.0, sway * 0.6, -0.4)
        P.add(chain([root, midp, tip], 0.65, 0.45, m.weed, "weed%d" % k, line=False))


# ------------------------------------------------------------------------------------------------ the head
def _head_beaked(P, B, c) -> None:
    """The head on its thick neck: pulled into the shell when struck, dropped when beaten; a pale hooked beak, the jaw
    gaping on the maw, amber eyes that glow."""
    h, m, st = B.parts.head, B.mats, c.st
    a, f, at, bm = c.action, c.f, c.at, c.bm
    neck = B.pick("neck", a, f, 1.0)
    bob = st.bob_amp * wave(a, f) if "bob_amp" in st else (st.bob_step * abs(math.sin(f / 8.0 * math.tau)) if "bob_step" in st else 0.0)
    hm = bm @ rot("b", B.pick("hpitch", a, f))
    (n0, (ha, hreach, hz), (r0, r1)) = h.neck
    hc = at((ha + hreach * neck, 0.0, hz + bob))
    gape = B.pick("gape", a, f)
    P.add(L(at(n0), hc, r0, r1, m.skin, "neck"),
          E(hc, h.skull, m.skin, "head", hm))
    beak = hc + hm @ v3(h.beak[0])
    P.add(E(beak, h.beak[1], m.beak, "head", hm))
    P.mark(beak + hm @ v3(2.1, 0.0, -0.8), M.HOOK)
    if gape > 0.05:
        jm = hm @ rot("b", -gape * 35.0)
        hinge = hc + hm @ v3(0.6, 0.0, -1.7)
        P.add(E(hinge + jm @ v3(2.8, 0.0, -0.3), (2.7, 2.3, 0.9), m.beak, "jaw", jm))
        if gape > 0.3:
            P.add(E(hinge + hm @ v3(2.6, 0.0, 0.1), (1.8, 1.6, 0.5), m.maw, "maw", hm, line=False))
    for s in (1, -1):
        eye = hc + hm @ v3(1.8, s * 3.0, 1.1)
        closed = st.get("shut", False) or a == "death" and f >= h.shut_from
        P.mark(eye, M.RAMPS[m.skin][0] if closed else M.RAMPS[m.eye][3])
        if not closed:
            P.mark(eye + hm @ v3(0.4, 0.0, 0.5), M.RAMPS[m.eye][4])
            P.mark(hc + hm @ v3(2.5, s * 2.7, 1.2), M.INKY)
        P.mark(hc + hm @ v3(1.2, s * 2.6, 2.4), M.RAMPS[m.skin][0])
    sk = h.scales     # scales on the head: a mark just proud of the skull (its radii and a little more)
    for u, v in ((150.0, 50.0), (-140.0, 40.0), (180.0, 70.0), (110.0, 60.0)):
        cu, su = math.cos(math.radians(u)), math.sin(math.radians(u))
        cv, sv = math.cos(math.radians(v)), math.sin(math.radians(v))
        P.mark(hc + hm @ v3(sk[0] * cv * cu, sk[1] * cv * su, sk[2] * sv), M.RAMPS[m.skin][1])


# ------------------------------------------------------------------------------------------------ legs and tail
def _legs_pillar(P, B, c) -> None:
    """Thick, splayed legs stepping in diagonal pairs; tucked when struck, curled when it lies on its back, pawing."""
    g, m, st = B.parts.legs, B.mats, c.st
    a_, f, at, lunge = c.action, c.f, c.at, c.lunge
    curl = B.pick("curl", a_, f)
    tuck = B.pick("tuck", a_, f)
    paw = st.get("paw")
    for k, (a, b) in enumerate(g.at):
        up, stride = gait(a_, f, 0.0 if k in (0, 3) else 0.5, g.lift, g.stride)
        hip = at((a * 0.85, b * 0.78, -2.8))
        out = 1.0 - 0.4 * curl - 0.3 * tuck
        paw_wave = 0.6 * math.sin(f * 1.7 + k) * (1.0 if paw is not None and paw[0] <= f <= paw[1] else 0.0)
        foot = v3(lunge + a * (0.9 + 0.1 * out) + stride, b * (0.78 + 0.34 * out), 1.1 + up + curl * 3.4 + paw_wave)
        pad = foot + v3(0.8 if a > 0 else -0.5, 0.0, -0.2)
        P.add(L(hip, foot, 2.4, 2.1, m.skin, "leg%d" % k), E(pad, (2.4, 2.1, 1.1), m.skin, "leg%d" % k))
        if a > 0:
            for u in (-28.0, 0.0, 28.0):
                P.mark(pad + v3(2.6 * math.cos(math.radians(u)), 2.2 * math.sin(math.radians(u)), 0.3), M.TALON)
        for t in (0.35, 0.65):
            P.mark(hip + (foot - hip) * t + v3(0.0, 0.0, 2.2), M.RAMPS[m.skin][1])


def _tail_saw(P, B, c) -> None:
    """The saw-backed tail, wagging."""
    t, m, st = B.parts.tail, B.mats, c.st
    wag = st.wag_amp * wave(c.action, c.f) if "wag_amp" in st else 0.0
    root, tip = c.at(t.root), v3(c.lunge + t.tip[0], wag * 2.0, t.tip[1])
    P.add(L(root, tip, t.r[0], t.r[1], m.skin, "tail"))
    for u in (0.25, 0.45, 0.65, 0.82):
        q = root + (tip - root) * u
        P.add(E(q + v3(0.0, 0.0, 2.0 - 1.3 * u + 0.1), (0.8, 0.5, 0.7), m.skin, "saw", line=False))


# ------------------------------------------------------------------------------------------------ the crusher
def _crusher(P, B, c) -> None:
    """The crusher on its right: held low before it and working while idle, raised high over its head in the tell
    (gaping), slammed down before it on the strike in a burst of water and mud, drawn in when struck."""
    cl, m, st = B.parts.claw, B.mats, c.st
    a, f, at, bm = c.action, c.f, c.at, c.bm
    if B.has("crusher", a):
        elbow, palm, pitch, yaw, open_ = B.pick("crusher", a, f)
    else:
        swing = st.swing * wave(a, f) if "swing" in st else 0.0
        snap = B.pick("snap", a, f) if B.has("snap", a) else 0.35
        (e0, (pa, pb, pc), pitch, yaw) = cl.rest
        elbow, palm, open_ = e0, (pa + swing, pb, pc), snap
    cm = bm @ rot("c", yaw) @ rot("b", pitch)
    el, pc = at(elbow), at(palm)
    P.add(L(at(cl.root), el, 2.0, 2.1, m.claw, "claw"), L(el, pc, 2.1, 2.4, m.claw, "claw"),
          E(pc, (4.5, 3.2, 3.6), m.claw, "claw", cm),
          E(pc + cm @ v3(4.6, 0.3, -1.4), (2.6, 1.7, 1.4), m.claw, "claw", cm),
          E(pc + cm @ v3(7.2, 0.3, -1.0), (1.7, 1.25, 1.05), m.tip, "claw", cm))
    dm = cm @ rot("b", open_ * 50.0)
    hinge = pc + cm @ v3(2.0, 0.0, 1.4)
    P.add(E(hinge + dm @ v3(3.1, -0.2, 0.6), (2.7, 1.6, 1.35), m.claw, "dactyl", dm),
          E(hinge + dm @ v3(5.8, -0.2, 0.7), (1.7, 1.25, 1.05), m.tip, "dactyl", dm))
    for t in (3.4, 4.6, 5.8):
        P.mark(pc + cm @ v3(t, 0.3, -0.05), M.CLAW_TOOTH)
    P.mark(pc + cm @ v3(0.0, 0.0, 3.5), M.RAMPS[m.claw][4])
    sp = B.pick("splash", a, f)
    if sp > 0:
        imp = pc + cm @ v3(4.2, 0.0, 0.0)
        rr, hh = 3.4 + 2.0 * sp, 1.8 + 2.0 * sp
        white = (0xEE, 0xF8, 0xF4, 255)
        mud = (0x5A, 0x4A, 0x30, 200)
        for k in range(30):
            ang = math.radians(k * 12.0 + sp * 7.0)
            ca, sa = math.cos(ang), math.sin(ang) * 0.9
            lift = hh * (0.5 + 0.5 * math.sin(ang * 3.0 + sp))
            # The crown of water thrown up, the wet ring on the ground outside it, the mud churned inside it.
            P.fx.append((v3(imp[0] + ca * rr, imp[1] + sa * rr, 0.3 + lift), white if k % 2 else M.SPLASH))
            P.fx.append((v3(imp[0] + ca * rr, imp[1] + sa * rr, 0.3 + lift * 0.5), M.SPLASH_DIM))
            P.fx.append((v3(imp[0] + ca * (rr + 1.3), imp[1] + sa * (rr + 1.3), 0.0), M.SPLASH if k % 2 else M.DUST))
            if k % 3:
                P.fx.append((v3(imp[0] + ca * (rr - 1.3), imp[1] + sa * (rr - 1.3), 0.1), mud))
        for d in ((0.0, 0.0, 4.0), (1.2, 1.0, 3.0), (-1.0, -1.2, 3.4), (0.4, -0.6, 5.2), (-0.6, 0.8, 6.0), (1.6, -1.4, 4.6),
                  (-1.8, 0.4, 5.4), (0.8, 1.8, 6.4)):
            P.fx.append((v3(imp[0], imp[1], hh * 0.9) + v3(*d) * v3(1.0, 1.0, 0.6 + 0.3 * sp), white))


# ================================================================================================= the beetle
def _lerp(a, b, t):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * t


def _beetle(B, action: str, f: int, view: float = 48.0) -> Pose:
    """A rock beetle (E2): a squat carapace of rocky plates (two elytra and the pronotum before them, ochre lichen and
    pale flecks on the stone, a seam down the middle), dark chitin underneath, a small dark head with a curved ochre horn,
    amber eyes and clubbed antennae, and six jointed legs that walk in tripods. `ball` (0..1) curls it up into a stone
    ball, its legs, head and horn folded against its belly; `spin` rolls the ball forward (the plates, the belly and the
    folded legs turn with it, so the roll reads frame to frame)."""
    P = Pose()
    p, m = B.parts, B.mats
    st = B.style(action)
    sh = p.shell
    seed = int(B.opts.get("seed", 0))
    lunge = B.pick("lunge", action, f)
    pitch = B.pick("pitch", action, f)
    ball = B.pick("ball", action, f)
    spin = B.pick("spin", action, f)
    bob = B.pick("bob", action, f)
    rock = 0.0
    if st.get("kind") == "tripod":
        rock = st.rock_amp * math.sin(f / 8.0 * math.tau)
        bob = st.bob_step * abs(math.sin(f / 8.0 * 2.0 * math.tau))
    R = sh.ball
    z = p.Z + (R - p.Z) * ball + bob
    C = v3(lunge, 0.0, z)
    bm = rot("a", rock) @ rot("b", pitch - spin)
    at = lambda q: C + bm @ v3(q)

    def stone(q, n):
        """The carapace: rocky plates (a seam down the middle between the elytra, seams across them, cracks), ochre lichen
        in patches, pale flecks; dark chitin where it turns under."""
        loc = (q - C) @ bm
        nl = n @ bm
        a, b = loc[:, 0], loc[:, 1]
        under = nl[:, 2] < -0.35
        suture = (np.abs(b) < 0.32) & (a < 2.0 + 2.0 * ball) & (nl[:, 2] > 0.2)
        across = np.min(np.abs(a[:, None] - np.array(sh.seams)[None, :]), axis=1) < 0.28
        crack = h01v(np.floor(a * 1.4 + 70), np.floor(b * 1.4 + 70), seed % 97 + 7) > 0.9
        lichen = (h01v(np.floor(a * 0.55 + 90), np.floor(b * 0.55 + 90), seed % 89 + 3) > sh.lichen) & (nl[:, 2] > 0.1)
        fleck = h01v(np.floor(a * 2.6 + 30), np.floor(b * 2.6 + 30), seed % 83 + 5) > 0.93
        names = np.where(under, m.chitin, np.where(lichen, m.lichen, m.rock)).astype(object)
        bias = np.where(under, 0, np.where(suture | across, -2, np.where(crack, -1, np.where(fleck & ~lichen, 2, 0)))).astype(np.int16)
        return names, bias

    def plate(q, n):
        loc = (q - C) @ bm
        nl = n @ bm
        under = nl[:, 2] < -0.35
        rim = (np.abs(loc[:, 0] - sh.pronotum[0][0]) > sh.pronotum[1][0] * 0.78) & ~under
        fleck = h01v(np.floor(loc[:, 0] * 2.6 + 50), np.floor(loc[:, 1] * 2.6 + 50), seed % 79 + 11) > 0.95
        return (np.where(under, m.chitin, m.pronotum).astype(object),
                np.where(rim, -1, np.where(fleck & ~under, 2, 0)).astype(np.int16))

    def chitin(q, n):
        """The underside: dark chitin in bands across it (the belly's plates, which show when it lies on its back)."""
        loc = (q - C) @ bm
        nl = n @ bm
        band = (loc[:, 0] + 8.0) % 1.5 < 0.32
        return np.full(len(q), m.chitin, dtype=object), np.where(band, -1, np.where(nl[:, 2] > 0.6, 1, 0)).astype(np.int16)

    # The body: the chitin underside, the elytra, the pronotum; balled up, a sphere with its belly patch on one side.
    ec, er = sh.elytra
    pc, pr = sh.pronotum
    uc, ur = sh.under
    P.add(E(at(_lerp(uc, (0.2, 0.0, -R * 0.38), ball)), _lerp(ur, (R * 0.8, R * 0.76, R * 0.7), ball), m.chitin, "under", bm, chitin),
          E(at(_lerp(ec, (0.0, 0.0, 0.0), ball)), _lerp(er, (R, R, R), ball), m.rock, "body", bm, stone),
          E(at(_lerp(pc, (R * 0.6, 0.0, R * 0.28), ball)), _lerp(pr, (R * 0.44, R * 0.82, R * 0.72), ball), m.pronotum, "pronotum", bm, plate))
    cen = _lerp(ec, (0.0, 0.0, 0.0), ball)
    rr = _lerp(er, (R, R, R), ball) + 0.15
    # Rocky lumps along the plates, breaking the dome's line so it reads as stone, not an egg.
    for a0, b0, lr in sh.get("lumps", ()):
        u, v = (a0 - ec[0]) / er[0], b0 / er[1]
        w = math.sqrt(max(0.0, 1.0 - u * u - v * v))
        q = cen + np.array((u, v, w)) * (rr - 0.15 - lr * 0.35)
        P.add(E(at(q), (lr * 1.3, lr, lr * 0.75), m.rock, "lump", bm, stone, line=False))
    # Pale flecks of stone and lichen on the carapace (placed by its seed, so each kind keeps its own), where they show.
    for k in range(sh.specks):
        on_u = math.radians((seed % 360 + k * 137.0) % 360.0)
        on_v = math.radians(25.0 + (k * 23 + seed % 31) % 50)
        q = np.array((math.cos(on_v) * math.cos(on_u), math.sin(on_u) * math.cos(on_v), math.sin(on_v)))
        P.mark(at(cen + rr * q), M.SPECK if k % 3 else M.RAMPS[m.lichen][4])
    _beetle_head(P, B, (action, f, at, bm, ball, R, st, headon(view)[0]))
    _beetle_legs(P, B, (action, f, at, bm, ball, R, lunge, z, st))
    # Dust as it curls and rolls, the ball's speed streaks, the spark of its hit.
    if f in st.get("dust", ()):
        for k in range(6):
            ang = math.radians(k * 60.0 + f * 25.0)
            r = R * 0.9 + (k % 3) * 0.7
            P.fx.append((v3(lunge - R * 0.6 + math.cos(ang) * r * 0.5, math.sin(ang) * r, 0.3 + (k % 2) * 0.6),
                         M.DUST if k % 2 else M.DUST_DIM))
    if f in st.get("streaks", ()):
        for k in range(4):
            y = (k - 1.5) * 1.8
            for d in range(3):
                P.fx.append((v3(lunge - R - 2.0 - d * 1.2 - k % 2, y, z + (k % 2) * 0.8), M.DUST_DIM if d else M.DUST))
    if action == "attack" and f == st.get("spark", -1):
        tip = C + v3(R + 1.2, 0.0, 0.4)
        for d in ((0.0, 0.0, 0.0), (0.0, 0.0, 1.2), (0.0, 0.0, -1.0), (0.0, 1.1, 0.0), (0.0, -1.1, 0.0), (0.9, 0.0, 0.0)):
            P.glow.append((tip + v3(*d), M.GLINT))
    roll = B.pick("roll", action, f)
    if roll:
        edge, back = st.edge
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, z)
        r = math.sin(math.radians(roll))
        h = z + (edge - z) * r if roll <= 90.0 else back + (edge - back) * r   # over its edge onto its back
        P.shift = v3(-turned[0], -turned[1], h - turned[2])
    sq = st.get("squash", {}).get(f)
    if sq is not None:
        P.squash(sq[0], sq[1], sq[2], (lunge, 0.0, 0.0))
    return P


def _beetle_head(P, B, c) -> None:
    """The small dark head under the pronotum's lip, its curved ochre horn sweeping up and back, amber eyes, clubbed
    antennae feeling about; tucked against the belly in the ball."""
    action, f, at, bm, ball, R, st, fr = c
    h, m = B.parts.head, B.mats
    hc = at(_lerp(h.at, (R * 0.55, 0.0, -R * 0.78), ball))
    hm = bm @ rot("b", h.lift * fr * (1.0 - ball) - 150.0 * ball)
    s_ = 1.0 - 0.25 * ball
    P.add(E(hc, tuple(x * s_ for x in h.r), m.chitin, "head", hm))
    pts = [hc + hm @ (v3(q) * (s_ - 0.35 * ball)) for q in h.horn]
    r0, r1 = h.horn_r
    n = len(pts) - 1.0
    P.add(*[L(pts[i], pts[i + 1], r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n, m.horn, "horn", caps=i == 0)
            for i in range(len(pts) - 1)])
    dead = action == "death" and f >= st.get("shut_from", 99)
    tw = B.pick("antennae", action, f)
    for s in (1, -1):
        ea, eb, ec = h.eyes
        P.mark(hc + hm @ v3(ea, s * eb, ec), M.RAMPS[m.chitin][1] if dead else M.BEETLE_EYE)
        if not dead:
            P.mark(hc + hm @ v3(ea + 0.3, s * (eb - 0.2), ec + 0.5), M.GLINT)
        if ball < 0.6:
            a0, a1, a2 = h.antennae
            sway = tw * (0.9 if s > 0 else -0.6)
            q = [hc + hm @ v3(a0[0], s * a0[1], a0[2]), hc + hm @ v3(a1[0], s * a1[1] + sway * 0.5, a1[2] + 0.3 * tw),
                 hc + hm @ v3(a2[0] - 0.3 * abs(tw), s * a2[1] + sway, a2[2] + 0.5 * tw)]
            P.add(chain(q, 0.3, 0.22, m.chitin, "antenna%d" % s, line=False), S(q[-1], h.club, m.chitin, "antenna%d" % s))


def _beetle_legs(P, B, c) -> None:
    """Six jointed legs, knees up and out, walking in tripods (fore and hind on one side with the middle of the other);
    splayed when struck, folded flat against the belly in the ball, curled and pawing on its back."""
    action, f, at, bm, ball, R, lunge, z, st = c
    g, m = B.parts.legs, B.mats
    curl = B.pick("curl", action, f)
    splay = B.pick("splay", action, f)
    paw = st.get("paw")
    for s in (1, -1):
        for k, a0 in enumerate(g.at):
            lift, stride = gait(action, f, 0.5 if (k + (s > 0)) % 2 else 0.0, g.lift, g.stride)
            lean = g.lean[k]
            wig = 0.6 * math.sin(f * 1.9 + k + s) if paw is not None and paw[0] <= f <= paw[1] else 0.0
            hip = at((a0 * (1.0 - 0.5 * ball), s * g.hip[0] * (1.0 - 0.35 * ball), g.hip[1] - R * 0.2 * ball))
            knee = v3(lunge + a0 + lean * 0.5 + stride * 0.5, s * (g.knee[0] + 0.8 * splay), z + g.knee[1] + lift * 0.5 + 0.6 * splay)
            foot = v3(lunge + a0 + lean + stride, s * (g.foot[0] + 1.2 * splay), g.foot[1] + lift)
            if curl > 0.0:      # drawn in under the belly, so on its back they stick up off it, pawing the air
                knee = _lerp(knee, at((a0 * 0.8 + lean * 0.3, s * 4.4, -2.4 - wig * 0.3)), curl)
                foot = _lerp(foot, at((a0 * 0.6 + lean * 0.5 + wig * 0.5, s * (2.6 + wig * 0.4), -4.2 - wig)), curl)
            if ball > 0.0:
                knee = _lerp(knee, at((a0 * 0.45 + 0.4, s * R * 0.62, -R * 0.62)), ball)
                foot = _lerp(foot, at((a0 * 0.3 + 1.0, s * R * 0.3, -R * 0.84)), ball)
            r = g.r
            P.add(L(hip, knee, r[0][0], r[0][1], m.chitin, "leg%d%d" % (s, k)), L(knee, foot, r[1][0], r[1][1], m.chitin, "leg%d%d" % (s, k)))
