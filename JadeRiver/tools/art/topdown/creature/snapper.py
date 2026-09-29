"""Old Snapper, the Reed Shallows' old elite: an ancient river snapping turtle, drawn half again the size of the other
foes for its boss presence. A high domed shell grown over with moss along three knobbed keels, its dark green flanks
seamed into plates, a serrated back edge with barnacles on the rim and river weed trailing behind; a big khaki head with
a pale hooked beak and amber eyes that glow; thick scaled legs with talons and a saw-backed tail; and on its right the
great red crusher claw with dark tips, as on its side-view sheet. It breathes heavily and works the pincer while idle,
lumbers on diagonal pairs of legs with its shell rocking. Its tell: it rears its front up and raises the crusher high
over its head, gaping, the pincer wide. It slams the crusher down before it in a burst of water and mud, the whole
shell jolting with the blow, and drags the claw back; struck, it pulls its head into its shell; beaten, it rolls onto
its plated plastron, its legs pawing slower and slower.
"""
from __future__ import annotations

import math

import numpy as np

from . import mats as M
from .motion import gait, h01v, pick, wave
from .sculpt import E, L, Pose, S, chain, rot, v3

Z = 6.6

LUNGE = {"windup": (-0.4, -0.8, -1.2, -1.4), "attack": (0.4, 1.6, 1.8, 1.4, 0.8, 0.3), "hurt": (-1.8, -1.0, -0.3)}
REAR = {"windup": (3.0, 6.0, 8.0, 9.0), "attack": (4.0, -3.0, -2.0, -0.6, 0.4, 0.2), "hurt": (-2.0, 0.0, 0.0),
        "death": (4.0, -2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)}
SINK = {"attack": (0.0, 0.8, 0.6, 0.2, 0.0, 0.0), "death": (0.0, 1.0, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4), "hurt": (0.6, 0.3, 0.0)}
NECK = {"hurt": (0.15, 0.45, 0.8), "death": (1.0, 0.8, 0.6, 0.5, 0.4, 0.4, 0.4, 0.4), "windup": (1.1, 1.15, 1.2, 1.2)}
HPITCH = {"windup": (6.0, 12.0, 16.0, 18.0), "attack": (6.0, -14.0, -12.0, -6.0, -2.0, 0.0), "death": (10.0, -6.0, -12.0, -14.0, -14.0, -14.0, -14.0, -14.0)}
GAPE = {"idle": (0.0, 0.0, 0.12, 0.2, 0.05, 0.0), "windup": (0.3, 0.5, 0.7, 0.8), "attack": (0.8, 0.2, 0.3, 0.2, 0.1, 0.0),
        "hurt": (0.5, 0.2, 0.0), "death": (0.6, 0.5, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3)}
# The crusher: elbow and palm (in the shell's frame), its pitch and yaw, and how open the pincer is.
CRUSHER = {"windup": (((8.6, -11.4, 3.6), (9.4, -10.6, 9.0), 50.0, -10.0, 0.6), ((8.2, -11.2, 5.6), (8.8, -10.4, 13.0), 72.0, -10.0, 0.8),
                      ((7.8, -11.0, 7.2), (8.0, -10.2, 16.0), 88.0, -10.0, 1.0), ((7.6, -11.0, 7.6), (7.8, -10.2, 17.0), 92.0, -10.0, 1.0)),
           "attack": (((10.2, -11.0, 5.0), (13.6, -10.2, 9.0), 40.0, -8.0, 0.8), ((10.8, -10.4, -1.8), (14.6, -8.8, -3.4), -14.0, -6.0, 0.0),
                      ((10.8, -10.4, -1.9), (14.6, -8.8, -3.5), -16.0, -6.0, 0.0), ((10.6, -10.6, -1.4), (14.0, -9.2, -2.6), -8.0, -8.0, 0.1),
                      ((10.2, -10.8, -1.0), (13.4, -9.6, -0.8), 6.0, -10.0, 0.25), ((10.0, -11.0, -1.1), (13.2, -10.0, 0.4), 18.0, -10.0, 0.35)),
           "hurt": (((8.8, -10.8, -1.4), (11.4, -10.8, -1.6), 4.0, -14.0, 0.3), ((9.2, -10.8, -1.3), (12.2, -10.6, -0.8), 10.0, -12.0, 0.3),
                    ((9.8, -11.0, -1.2), (13.0, -10.2, 0.2), 18.0, -10.0, 0.35)),
           "death": (((9.8, -11.0, 1.0), (12.4, -10.4, 4.0), 30.0, -12.0, 0.6),) + (((9.6, -11.0, -2.4), (11.6, -11.0, -2.6), -8.0, -20.0, 0.5),) * 7}
ROLL = {"death": (0.0, 0.0, 30.0, 80.0, 130.0, 172.0, 176.0, 174.0)}
CURL = {"death": (0.0, 0.1, 0.3, 0.6, 0.8, 1.0, 0.8, 1.0), "hurt": (0.0, 0.0, 0.0)}
TUCK = {"hurt": (0.6, 0.35, 0.1)}
SPLASH = {"attack": (0.0, 1.0, 1.6, 2.0, 0.0, 0.0)}


def snapper(action: str, f: int) -> Pose:
    P = Pose()
    lunge = pick(LUNGE, action, f)
    rock = 3.2 * math.sin(f / 8.0 * math.tau) if action == "walk" else 0.0
    breathe = (0.0, 0.25, 0.4, 0.35, 0.15, 0.0)[f] if action == "idle" else 0.0
    rear = pick(REAR, action, f)
    z = Z + breathe * 0.4 - pick(SINK, action, f)
    C = v3(lunge, 0.0, z)
    bm = rot("a", rock) @ rot("b", rear)
    at = lambda p: C + bm @ v3(p)

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
        names = np.where(belly, "snap_belly", np.where(lit, "snap_moss_lit", np.where(moss, "snap_moss", "snap_shell"))).astype(object)
        return names, np.where(seam & ~belly, -1, 0).astype(np.int16)

    def rim(q, n):
        loc, ln = local(q, n)
        belly = ln[:, 2] < -0.35
        seam = (np.degrees(np.arctan2(loc[:, 1] / 10.4, loc[:, 0] / 12.0)) % 30.0) < 5.0
        return np.where(belly, "snap_belly", "snap_shell").astype(object), np.where(seam & ~belly, -1, 0).astype(np.int16)

    def plastron(q, n):
        loc, _ = local(q, n)
        seam = (np.abs(loc[:, 1]) < 0.45) | (np.min(np.abs(loc[:, 0][:, None] - np.array([-4.2, 0.2, 4.4])[None, :]), axis=1) < 0.45)
        return np.full(len(q), "snap_belly", dtype=object), np.where(seam, -1, 0).astype(np.int16)

    rim_c, rim_r = at((0.0, 0.0, -2.6)), (12.0, 10.4, 2.2)
    P.add(E(rim_c, rim_r, "snap_shell", "shell", bm, rim),
          E(at((0.4, 0.0, -3.6)), (10.2, 8.6, 1.9), "snap_belly", "shell", bm, plastron),
          E(at((0.0, 0.0, -0.8)), (11.0, 9.4, 5.8), "snap_shell", "shell", bm, carapace))
    # Three keels of knobs along the dome, and the serrated back edge.
    for b0, row in ((0.0, (-6.8, -3.6, -0.4, 2.8, 5.8)), (4.3, (-5.0, -1.6, 1.8)), (-4.3, (-5.0, -1.6, 1.8))):
        for a0 in row:
            top = -0.8 + 5.8 * math.sqrt(max(0.0, 1.0 - (a0 / 11.0) ** 2 - (b0 / 9.4) ** 2))
            P.add(E(at((a0, b0, top - 0.1)), (1.4, 1.0, 1.0), "snap_shell", "keel", bm, carapace, line=False))
    for ang in (144.0, 162.0, 180.0, 198.0, 216.0):
        P.add(E(at((12.0 * math.cos(math.radians(ang)), 10.4 * math.sin(math.radians(ang)), -2.6)), (1.4, 1.4, 1.0), "snap_shell", "shell", bm))
    for u, v in ((32.0, 30.0), (52.0, 10.0), (-38.0, 25.0), (76.0, 35.0), (-72.0, 15.0), (112.0, 25.0), (-110.0, 20.0)):
        for du, dv, col in ((0.0, 0.0, M.BARNACLE), (4.0, -12.0, M.BARNACLE_SHADE)):
            cu, su = math.cos(math.radians(u + du)), math.sin(math.radians(u + du))
            cv, sv = math.cos(math.radians(v + dv)), math.sin(math.radians(v + dv))
            P.mark(rim_c + bm @ v3(12.2 * cv * cu, 10.6 * cv * su, 2.4 * sv), col)
    # River weed trailing from the back edge, stirring as it moves.
    sway = {"idle": 0.8 * wave(action, f), "walk": 1.0 * wave(action, f)}.get(action, 0.3)
    for k, b0 in enumerate((-4.2, 0.8, 5.0)):
        root = at((-11.2 + abs(b0) * 0.2, b0, -2.4))
        tip = v3(lunge - 15.0 - k * 0.6, b0 * 1.1 + sway * (1.0 if k % 2 else -1.0), 0.8)
        midp = (root + tip) * 0.5 + v3(0.0, sway * 0.6, -0.4)
        P.add(chain([root, midp, tip], 0.65, 0.45, "weed", "weed%d" % k, line=False))
    # The head on its thick neck: pulled into the shell when struck, dropped when beaten.
    neck = pick(NECK, action, f, 1.0)
    bob = {"idle": 0.25 * wave(action, f), "walk": 0.4 * abs(math.sin(f / 8.0 * math.tau))}.get(action, 0.0)
    hm = bm @ rot("b", pick(HPITCH, action, f))
    hc = at((10.4 + 3.6 * neck, 0.0, -0.9 + bob))
    gape = pick(GAPE, action, f)
    P.add(L(at((7.2, 0.0, -1.4)), hc, 2.6, 2.8, "snap_skin", "neck"),
          E(hc, (4.0, 3.5, 3.1), "snap_skin", "head", hm))
    beak = hc + hm @ v3(3.6, 0.0, -0.4)
    P.add(E(beak, (2.0, 2.3, 2.0), "snap_beak", "head", hm))
    P.mark(beak + hm @ v3(2.1, 0.0, -0.8), M.HOOK)
    if gape > 0.05:
        jm = hm @ rot("b", -gape * 35.0)
        hinge = hc + hm @ v3(0.6, 0.0, -1.7)
        P.add(E(hinge + jm @ v3(2.8, 0.0, -0.3), (2.7, 2.3, 0.9), "snap_beak", "jaw", jm))
        if gape > 0.3:
            P.add(E(hinge + hm @ v3(2.6, 0.0, 0.1), (1.8, 1.6, 0.5), "maw", "maw", hm, line=False))
    for s in (1, -1):
        eye = hc + hm @ v3(1.8, s * 3.0, 1.1)
        shut = action == "hurt" or action == "death" and f >= 5
        P.mark(eye, M.RAMPS["snap_skin"][0] if shut else M.RAMPS["snap_eye"][3])
        if not shut:
            P.mark(eye + hm @ v3(0.4, 0.0, 0.5), M.RAMPS["snap_eye"][4])
            P.mark(hc + hm @ v3(2.5, s * 2.7, 1.2), M.INKY)
        P.mark(hc + hm @ v3(1.2, s * 2.6, 2.4), M.RAMPS["snap_skin"][0])
    for u, v in ((150.0, 50.0), (-140.0, 40.0), (180.0, 70.0), (110.0, 60.0)):
        cu, su = math.cos(math.radians(u)), math.sin(math.radians(u))
        cv, sv = math.cos(math.radians(v)), math.sin(math.radians(v))
        P.mark(hc + hm @ v3(4.2 * cv * cu, 3.7 * cv * su, 3.3 * sv), M.RAMPS["snap_skin"][1])
    # Legs: thick, splayed, stepping in diagonal pairs; tucked when struck, curled when it lies on its back.
    curl = pick(CURL, action, f)
    tuck = pick(TUCK, action, f)
    for k, (a, b) in enumerate(((5.6, 8.4), (5.6, -8.4), (-6.0, 8.0), (-6.0, -8.0))):
        up, stride = gait(action, f, 0.0 if k in (0, 3) else 0.5, 1.4, 1.6)
        hip = at((a * 0.85, b * 0.78, -2.8))
        out = 1.0 - 0.4 * curl - 0.3 * tuck
        paw_wave = 0.6 * math.sin(f * 1.7 + k) * (1.0 if action == "death" and 4 <= f <= 6 else 0.0)
        foot = v3(lunge + a * (0.9 + 0.1 * out) + stride, b * (0.78 + 0.34 * out), 1.1 + up + curl * 3.4 + paw_wave)
        pad = foot + v3(0.8 if a > 0 else -0.5, 0.0, -0.2)
        P.add(L(hip, foot, 2.4, 2.1, "snap_skin", "leg%d" % k), E(pad, (2.4, 2.1, 1.1), "snap_skin", "leg%d" % k))
        if a > 0:
            for u in (-28.0, 0.0, 28.0):
                P.mark(pad + v3(2.6 * math.cos(math.radians(u)), 2.2 * math.sin(math.radians(u)), 0.3), M.TALON)
        for t in (0.35, 0.65):
            P.mark(hip + (foot - hip) * t + v3(0.0, 0.0, 2.2), M.RAMPS["snap_skin"][1])
    # The saw-backed tail.
    wag = {"idle": 0.5 * wave(action, f), "walk": 1.0 * wave(action, f)}.get(action, 0.0)
    root, tip = at((-9.8, 0.0, -2.6)), v3(lunge - 18.4, wag * 2.0, 1.2)
    P.add(L(root, tip, 2.0, 0.7, "snap_skin", "tail"))
    for u in (0.25, 0.45, 0.65, 0.82):
        p = root + (tip - root) * u
        P.add(E(p + v3(0.0, 0.0, 2.0 - 1.3 * u + 0.1), (0.8, 0.5, 0.7), "snap_skin", "saw", line=False))
    # The crusher on its right: held low before it and working while idle, raised high over its head in the tell
    # (gaping), slammed down before it on the strike, drawn in when struck.
    if action in CRUSHER:
        elbow, palm, pitch, yaw, open_ = pick(CRUSHER, action, f)
    else:
        swing = 0.8 * wave(action, f) if action == "walk" else 0.0
        snap = (0.3, 0.45, 0.65, 0.55, 0.35, 0.3)[f] if action == "idle" else 0.35
        elbow, palm, pitch, yaw, open_ = (10.0, -11.0, -1.2), (13.2 + swing, -10.0, 0.6), 22.0, -10.0, snap
    cm = bm @ rot("c", yaw) @ rot("b", pitch)
    el, pc = at(elbow), at(palm)
    P.add(L(at((6.8, -7.6, -1.6)), el, 2.0, 2.1, "crusher", "claw"), L(el, pc, 2.1, 2.4, "crusher", "claw"),
          E(pc, (4.5, 3.2, 3.6), "crusher", "claw", cm),
          E(pc + cm @ v3(4.6, 0.3, -1.4), (2.6, 1.7, 1.4), "crusher", "claw", cm),
          E(pc + cm @ v3(7.2, 0.3, -1.0), (1.7, 1.25, 1.05), "crusher_tip", "claw", cm))
    dm = cm @ rot("b", open_ * 50.0)
    hinge = pc + cm @ v3(2.0, 0.0, 1.4)
    P.add(E(hinge + dm @ v3(3.1, -0.2, 0.6), (2.7, 1.6, 1.35), "crusher", "dactyl", dm),
          E(hinge + dm @ v3(5.8, -0.2, 0.7), (1.7, 1.25, 1.05), "crusher_tip", "dactyl", dm))
    for t in (3.4, 4.6, 5.8):
        P.mark(pc + cm @ v3(t, 0.3, -0.05), M.CLAW_TOOTH)
    P.mark(pc + cm @ v3(0.0, 0.0, 3.5), M.RAMPS["crusher"][4])
    sp = pick(SPLASH, action, f)
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
    roll = pick(ROLL, action, f)
    if roll:
        P.m = rot("a", roll)
        turned = P.m @ v3(0.0, 0.0, z)
        r = math.sin(math.radians(roll))
        h = z + (10.0 - z) * r if roll <= 90.0 else 6.4 + (10.0 - 6.4) * r
        P.shift = v3(-turned[0], -turned[1], h - turned[2])
    if action == "attack" and f == 1:
        P.squash(1.03, 1.03, 0.93, (lunge, 0.0, 0.0))
    return P
