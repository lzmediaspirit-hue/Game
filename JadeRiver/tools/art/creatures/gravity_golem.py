"""Gravity golem - a construct of dark basalt blocks held together by gravity alone (Earth/Space).

View: three-quarter, facing right (the lit left plane of each big block is its near flank,
the darker right plane its front).  ~52 art px tall to the crown of the hunched head,
~46 px across the fists, on a 96 px art canvas (cell 192).  Not flying.
Every body part is a separate chamfered basalt block floating a few pixels from its
neighbours, and each block is ringed by a faint indigo gravity ripple (a dim ring with
bright dashes that travel from frame to frame), so the gaps read as glowing bonds.  Blocks
are lit per face (faces turned to the upper-left light get a pale edge, faces turned away a
dark one), so a rotated or falling block stays lit correctly.
Parts, back to front: back half of the orbiting stone ring, far shoulder / forearm / fist,
far shin and foot, pelvis, near shin and foot, torso (near flank and front plane, columnar
seams, the violet singularity eye in the chest), hunched faceless head with a visor groove,
near shoulder / forearm / fist, front half of the ring (pale stone with star notches).
Idle: the blocks bob out of step with each other while the ring turns.  Walk: heavy steps
with a dust puff on each footfall; the head, shoulders and fists lag a frame behind the
torso.  Windup: both arms hauled overhead, the singularity swells and dark lines and pebbles
spiral into it (held).  Attack: a double-fist slam in front; a shockwave ring races out along
the ground on frame 1.  Hurt: the blocks jolt apart and the singularity pinches.  Death: the
gravity fails, the blocks drop and scatter into a heap that fades.
"""
import math
from types import SimpleNamespace

import numpy as np

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "gravity_golem",
    "cell": 192,
    "anchor": [96, 168],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: cool basalt, a paler ring stone, violet singularity, indigo gravity -------------
BASALT = px.material("gg_basalt", "#9994b2", "#65607f", "#46415f", "#2d2943", outline="#0b0916")
RING = px.material("gg_ring", "#e2dbea", "#aca5c0", "#777094", "#4d476b", outline="#110e1f")
SING = px.material("gg_sing", "#f3e4ff", "#b27cff", "#7444d4", "#351a70", outline="#0d0620")
CORE = px.rgb("#07030f")
DEAD = px.rgb("#57536b")
RIP = px.rgb("#6a62e0")
RIP_DIM = px.rgb("#37328a")
PULL_DARK = px.rgb("#30257a")
PULL_LIGHT = px.rgb("#a184ff")
STAR = px.rgb("#ffe6a1")
SHOCK = px.material("gg_shock", "#fbf6ff", "#c4b2ff", "#8a74ea", "#5646b4", outline="#1a1240")

# ---- rest layout: block centres (dx from the anchor X, dy from the ground edge B = gy - 1) ------
FOOT_N = (-5.5, -2.5, 12, 5)
FOOT_F = (9.0, -2.5, 10, 5)
SHIN_N = (-6.5, -12.5, 8, 9)
SHIN_F = (8.0, -12.5, 7, 9)
PELVIS = (1.0, -23.0, 17, 6)
TORSO = (0.5, -37.5)  # centre; the polygon is TORSO_POLY around it (rows B-46 .. B-29)
TORSO_POLY = [(-10.0, -8.5), (10.0, -8.5), (11.5, -6.5), (9.5, 7.5), (8.0, 8.5), (-6.5, 8.5), (-8.0, 7.0),
              (-11.5, -6.5)]
FLANK = [(-12.0, -9.0), (-4.0, -9.0), (-2.5, 9.0), (-12.0, 9.0)]  # the lit near flank of the torso
HEAD = (6.0, -48.5, 10, 9)
HEAD_POLY = [(-4.0, -4.0), (3.0, -4.5), (5.2, -2.6), (6.2, -0.8), (4.6, 0.2), (4.8, 3.2), (3.4, 4.2), (-3.6, 4.2),
             (-5.0, 2.8), (-5.0, -2.6)]  # a jutting brow over a recessed visor, a square jaw
SH_N = (-15.5, -43.0, 11, 11)
SH_F = (16.5, -43.5, 9, 9)
SING_AT = (4.0, -1.5)  # singularity, relative to the torso centre
RING_C = (0.5, -32.5)
RING_R = (12.5, 3.4)
FIST_N = (11, 10)
FIST_F = (10, 9)
ARM_EXT = (5.5, 12.0, 5.0)  # shoulder half extent, forearm length, fist half extent

# ---- poses ----------------------------------------------------------------------------------
# bx, by    torso group offset         lean   torso lean (deg, - = forward)
# lag       (dx, dy) extra offset of the head / shoulders / fists (they trail the torso)
# fn, ff    near / far fist centre (dx from X, dy from B)
# feet      (dx, lift) near, far       bob  idle bob on    ring  orbit phase (deg)   tilt  ring tilt
# sing      singularity radius 2..4 or "dead"   squeeze  pinched to a slit (hurt)   flicker
# pull      windup: lines spiralling into the chest 0..3   spread  blocks pushed apart (px)
# shock     shockwave life (None = off)   hit  impact spark   dust  (side, life) footfall dust
# fall      0..1 blocks dropping (death)  pile  heap of blocks   fade  opacity   rip  ripples on
DEFAULTS = dict(bx=0, by=0, lean=0, lag=(0, 0), fn=(-19.5, -13.0), ff=(20.5, -13.5), feet=((0, 0), (0, 0)),
                bob=False, ring=0.0, tilt=-8.0, sing=2, squeeze=False, flicker=False, pull=0, spread=0.0,
                shock=None, hit=False, dust=None, fall=0.0, pile=False, fade=1.0, rip=True)

POSE = px.poses(DEFAULTS, {
    "idle": [  # the blocks bob out of step, the ring turns 15 deg a frame (60 deg = one segment)
        dict(bob=True, ring=0),
        dict(bob=True, ring=15),
        dict(bob=True, ring=30),
        dict(bob=True, ring=45),
    ],
    "walk": [  # heavy steps; the head, shoulders and fists lag one frame behind the torso
        dict(feet=((3, 0), (-3, 0)), by=1, lag=(1, -1), fn=(-21.5, -13), ff=(22.0, -13.5), ring=0, dust=(-1, 0.15)),
        dict(feet=((2, 0), (-1, 3)), bx=1, lag=(-1, 1), fn=(-20.5, -13), ff=(21.0, -13.5), ring=10),
        dict(feet=((0, 0), (1, 2)), bx=1, by=-1, fn=(-18.5, -14), ff=(19.5, -14.5), ring=20),
        dict(feet=((-3, 0), (3, 0)), by=1, lag=(1, -1), fn=(-17.5, -13), ff=(19.0, -13.5), ring=30, dust=(1, 0.15)),
        dict(feet=((-1, 3), (2, 0)), bx=1, lag=(-1, 1), fn=(-18.0, -13), ff=(20.0, -13.5), ring=40),
        dict(feet=((1, 2), (0, 0)), bx=1, by=-1, fn=(-20.0, -14), ff=(21.5, -14.5), ring=50),
    ],
    "windup": [  # arms hauled overhead, the singularity swells and pulls - held on the last frame
        dict(fn=(-23.0, -38.0), ff=(24.0, -39.0), lean=3, sing=3, pull=1, ring=8, bx=-1),
        dict(fn=(-9.0, -60.0), ff=(9.0, -61.0), lean=6, sing=4, pull=2, ring=14, bx=-2, by=1, lag=(-1, 0)),
        dict(fn=(-6.0, -63.0), ff=(7.0, -64.0), lean=8, sing=4, pull=3, ring=18, bx=-3, by=1, lag=(-1, 0)),
    ],
    "attack": [  # fists come over the top and slam down in front: shockwave on frame 1
        dict(fn=(10.0, -61.0), ff=(16.0, -61.0), lean=-4, sing=3, ring=24, lag=(-1, 0)),
        dict(fn=(17.0, -5.0), ff=(25.0, -4.5), lean=-16, sing=2, ring=30, bx=5, by=3, shock=0.25, hit=True),
        dict(fn=(17.0, -5.0), ff=(25.0, -4.5), lean=-14, sing=2, ring=36, bx=5, by=3, shock=0.7),
        dict(fn=(-12.0, -18.0), ff=(23.0, -16.0), lean=-6, sing=2, ring=42, bx=2, by=1, lag=(1, 0)),
    ],
    "hurt": [  # the blocks jolt apart, the singularity pinches
        dict(bx=-3, by=-1, lean=6, spread=2.6, squeeze=True, flicker=True, fn=(-23.0, -16.0), ff=(22.0, -17.0),
             ring=10, tilt=-14),
        dict(bx=-1, lean=3, spread=1.0, squeeze=True, fn=(-21.0, -14.0), ff=(21.0, -15.0), ring=16, tilt=-11),
    ],
    "death": [  # gravity fails: jolt apart, drop, scatter into a heap, fade
        dict(bx=-2, by=-2, lean=5, spread=4.0, sing="dead", flicker=True, fn=(-24.0, -18.0), ff=(24.0, -19.0),
             ring=10, tilt=-16),
        dict(bx=-2, lean=-6, spread=4.5, sing="dead", fall=0.6, fn=(-24.0, -12.0), ff=(24.0, -12.0), ring=10,
             tilt=-22, rip=False),
        dict(pile=True, dust=0.35),
        dict(pile=True, fade=0.6),
        dict(pile=True, fade=0.3),
    ],
})

IDLE_BOB = (0, -1, -1, 0)
BOB_PHASE = {"shin_n": 0, "shin_f": 2, "pelvis": 1, "torso": 0, "head": 1, "sh_n": 3, "sh_f": 1, "fa_n": 2,
             "fa_f": 0, "fist_n": 3, "fist_f": 1}
LIGHT2 = np.array([-0.62, -0.78]) / math.hypot(0.62, 0.78)
BLOCKS = ("foot_n", "foot_f", "shin_n", "shin_f", "pelvis", "torso", "head", "sh_n", "sh_f", "fa_n", "fa_f",
          "fist_n", "fist_f")


# ---- geometry -----------------------------------------------------------------------------------
def _block(cv, c, w, h, ang, mat=BASALT, name="blk", far=False, sep=None, cut=(1.3, 1.3, 1.3, 1.3), poly=None,
           lit_edge=2.0, dark_edge=1.6):
    """A chamfered stone block centred at ``c`` rotated ``ang`` deg (CCW), lit per face:
    faces turned to the light get a pale edge (the top reads as a lit top plane), faces
    turned away a dark one.  ``cut`` = chamfer of the (tl, tr, br, bl) corners.  ``poly``
    replaces the rectangle by any clockwise polygon (local points around ``c``)."""
    x0, x1, y0, y1 = c[0] - w / 2, c[0] + w / 2, c[1] - h / 2, c[1] + h / 2
    if poly is None:
        a, b, d, e = cut
        pts = [(x0 + a, y0), (x1 - b, y0), (x1, y0 + b), (x1, y1 - d), (x1 - d, y1), (x0 + e, y1), (x0, y1 - e),
               (x0, y0 + a)]
    else:
        pts = [(c[0] + q[0], c[1] + q[1]) for q in poly]
    with cv.xform(px.rotate(ang, c)):
        mask = cv.mask_polygon(pts)
        M = cv.M.copy()
    if not mask.any():
        return mask
    Mi = np.linalg.inv(M)
    u = Mi[0, 0] * cv.X + Mi[0, 1] * cv.Y + Mi[0, 2]
    v = Mi[1, 0] * cv.X + Mi[1, 1] * cv.Y + Mi[1, 2]
    faces = []
    n = len(pts)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        ln = math.hypot(ex, ey)
        if ln < 1e-6:
            continue
        nx, ny = ey / ln, -ex / ln  # outward normal of a clockwise-on-screen polygon
        faces.append(((nx, ny), -((u - ax) * nx + (v - ay) * ny)))
    D = np.stack([f[1] for f in faces])
    idx = np.argmin(D, axis=0)
    dmin = np.min(D, axis=0)
    fb, fw = [], []
    for (nl, _) in faces:
        ns = M[:2, :2] @ np.array(nl, float)
        ns = ns / (np.linalg.norm(ns) + 1e-9)
        lit = float(ns @ LIGHT2)
        if lit > 0.3:
            fb.append(0)
            fw.append(lit_edge if lit > 0.8 else 1.2)
        elif lit < -0.72:
            fb.append(3)
            fw.append(dark_edge)
        elif lit < -0.25:
            fb.append(2)
            fw.append(dark_edge)
        else:
            fb.append(1)
            fw.append(0.0)
    fb, fw = np.array(fb, np.int8), np.array(fw)
    band = np.where(dmin < fw[idx], fb[idx], 1).astype(np.int8)
    if far:
        band = np.clip(band + 1, 1, 3).astype(np.int8)
    band = np.where(mask, band, -1).astype(np.int8)
    cv._commit(mask, band, mat, name=name, sep=sep)
    return mask


def _seam(cv, pts, name, col=None):
    for a, b in zip(pts, pts[1:]):
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), col or BASALT.deep,
                band=None, decal=True, clip=name, name=name)


def _along(path, s):
    """Point and unit direction at arc length ``s`` along a poly-line."""
    for i, (a, b) in enumerate(zip(path, path[1:])):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        if s <= ln or i == len(path) - 2:
            t = s / ln if ln > 1e-9 else 0.0
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
        s -= ln
    return path[-1], (0.0, 1.0)


def _forearm(S, F, bend):
    """Forearm block (centre, angle) strung between shoulder S and fist F: the gaps stretch
    when the fist is far, the arm bends at an invisible elbow when it is near."""
    e_sh, e_fa, e_fi = ARM_EXT
    natural = e_sh + e_fa + e_fi + 2 * 3.2
    D = math.hypot(F[0] - S[0], F[1] - S[1])
    path = [S, px.ik2(S, F, natural / 2, natural / 2, bend), F] if D < natural else [S, F]
    Lp = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
    g = (Lp - (e_sh + e_fa + e_fi)) / 2
    c, (ux, uy) = _along(path, e_sh + g + e_fa / 2)
    return c, math.degrees(math.atan2(ux, uy))


# ---- the singularity --------------------------------------------------------------------------
def _singularity(cv, c, p, frame):
    """Violet accretion ring around a black core, sunk in a dark socket on the chest."""
    x, y = math.floor(c[0]), math.floor(c[1])
    cx, cy = x + 0.5, y + 0.5
    d = np.hypot(cv.X - cx, cv.Y - cy)
    tor = cv.mask_of("torso")
    if p.sing == "dead":
        sock = (d <= 2.6) & tor
        cv._commit(sock, np.where(sock, 3, -1).astype(np.int8), BASALT, name="torso")
        ring = (d <= 1.6) & tor
        cv._commit(ring, np.where(ring, 1, -1).astype(np.int8), px.flat(DEAD), name="sing")
        cv.pixel(x, y, CORE, name="sing")
        return
    if p.squeeze:  # pinched to a flickering slit
        sock = (np.abs(cv.Y - cy) <= 1.2) & (np.abs(cv.X - cx) <= 3.2) & tor
        cv._commit(sock, np.where(sock, 3, -1).astype(np.int8), BASALT, name="torso")
        cv.line((x - 2, y), (x + 2, y), SING.base, name="sing")
        cv.pixel(x, y, SING.light if p.flicker else CORE, name="sing")
        return
    r = float(p.sing)
    sock = (d <= r + 1.2) & tor
    cv._commit(sock, np.where(sock, 3, -1).astype(np.int8), SING, name="sing")
    ring = d <= r + 0.35
    ang = np.arctan2(cv.Y - cy, cv.X - cx)
    band = np.where(ang < -1.2, 0, 1)  # the upper-left of the ring catches the light
    band = np.where((ang > 0.4) & (ang < 2.6), 2, band)
    cv._commit(ring, np.where(ring, band, -1).astype(np.int8), SING, name="sing")
    core = d <= max(0.7, r - 1.05)
    cv._commit(core, np.where(core, 1, -1).astype(np.int8), px.flat(CORE), name="sing")
    if r >= 3:  # a bright mote whirling round the rim
        a = math.radians(frame * 70 + 30)
        q = (math.floor(cx + math.cos(a) * (r - 0.6)), math.floor(cy - math.sin(a) * (r - 0.6)))
        cv.pixel(q[0], q[1], SING.light, name="sing")


# ---- the orbiting ring -------------------------------------------------------------------------
def _ring(cv, C, ph, tilt, front, spread=0.0, drop=0.0):
    """Six curved stone segments on a tilted ellipse (40 deg each, 20 deg gaps).  ``front``
    draws the near half (sin > 0), otherwise the far half, darker."""
    R, r = RING_R[0] + spread * 1.5, RING_R[1]
    for k in range(6):
        a0 = ph + k * 60.0
        segs, pts, cur = [], [], None
        for i in range(9):
            th = math.radians(a0 + i * 5.0)
            fr = math.sin(th) > -0.08
            q = (C[0] + R * math.cos(th), C[1] + r * math.sin(th) + drop * (1 + math.sin(th)) * 0.5)
            q = px.rot_pt(q, tilt, C)
            if cur is not None and fr != cur:
                segs.append((cur, pts))
                pts = [pts[-1]]
            cur = fr
            pts.append(q)
        segs.append((cur, pts))
        for fr, pts in segs:
            if fr != front or len(pts) < 2:
                continue
            cv.limb(pts, 1.3, RING, shade="two" if front else "dark", name="ring")
            if front and len(pts) >= 6:  # a pale-gold star notch on each near stone
                m = pts[len(pts) // 2]
                cv.pixel(math.floor(m[0]), math.floor(m[1]), STAR, decal=True, clip="ring", name="ring")


# ---- ripples, FX -------------------------------------------------------------------------------
def _ripples(cv, frame):
    """Faint indigo gravity ripples: a broken, dashed ring 1 px outside each block's outline
    (the dashes travel from frame to frame) and a solid glowing bond where the rings of two
    neighbouring blocks meet in the gap between them."""
    lay = cv.layer(above=False, outline=False)
    occupied = px.dilate(cv.filled)
    xi, yi = cv.X.astype(int), cv.Y.astype(int)
    dash = ((xi + 2 * yi + frame) % 5) < 3
    count = np.zeros(cv.filled.shape, np.int16)
    rings = np.zeros(cv.filled.shape, bool)
    for n in BLOCKS:
        m = cv.mask_of(n)
        if not m.any():
            continue
        d2 = px.dilate(px.dilate(m))
        count += d2
        rings |= d2 & ~px.dilate(m)
    free = ~occupied
    bond = free & (count >= 2)
    outer = free & rings & dash & ~bond
    lay._commit(bond, np.where(bond, 1, -1).astype(np.int8), px.flat(RIP), name="rip")
    lay._commit(outer, np.where(outer, 1, -1).astype(np.int8), px.flat(RIP_DIM), name="rip")


def _pull(fx, c, p, frame):
    """Windup tell: dark and violet lines spiralling into the singularity, pebbles pulled in."""
    n = 1 + p.pull
    for j in range(n):
        a0 = 40 + j * (360 / n) + frame * 20
        hc.spiral(fx, c, 17 - p.pull, 5.0, a0, -160, PULL_DARK if j % 2 == 0 else PULL_LIGHT, name="pull")
    for j, (a, r) in enumerate(((200, 21), (330, 20), (110, 22))[:p.pull]):
        q = px.polar(c, a - frame * 15, r - 3 * p.pull)
        fx.rect(math.floor(q[0]), math.floor(q[1]), 2, 2, BASALT, shade="soft", name="pebble")


def _shockwave(back, front, c, t):
    """A flat ring of force racing out along the ground from the slam point (the far half
    behind the fists, the near half in front), with shock streaks thrown up at its rim."""
    rx, ry = 16 + 9 * t, 4.0 + 1.4 * t
    w = 3.0 if t < 0.5 else 1.5
    for lay, near in ((back, False), (front, True)):
        X, Y = lay.X, lay.Y
        d = ((X - c[0]) / rx) ** 2 + ((Y - c[1]) / ry) ** 2
        inner = ((X - c[0]) / max(1.0, rx - w)) ** 2 + ((Y - c[1]) / max(0.8, ry - w * 0.45)) ** 2
        band = (d <= 1.0) & (inner > 1.0) & ((Y >= c[1]) if near else (Y < c[1]))
        tone = np.where(Y < c[1] - 0.5, 0, 1) if t < 0.5 else np.full(X.shape, 2)
        lay._commit(band, np.where(band, tone, -1).astype(np.int8), SHOCK, name="shock")
    if t < 0.5:  # streaks thrown up at both rims
        for sx in (-1, 1):
            x = math.floor(c[0] + sx * (rx - 1))
            front.line((x, math.floor(c[1]) - 3), (x + sx, math.floor(c[1]) - 6), SHOCK.light, name="shock")
            front.line((x - sx * 3, math.floor(c[1]) - 4), (x - sx * 3, math.floor(c[1]) - 7), SHOCK.base,
                       name="shock")


# ---- draw ---------------------------------------------------------------------------------------
def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    if p.pile:
        _pile(cv, p, frame)
        return
    X, B = cv.gx, cv.gy - 1
    pivot = (X + PELVIS[0] + p.bx, B + PELVIS[1] + p.by)
    core = (X + 1.0, B - 32.0)

    def bob(name, c):
        dy = IDLE_BOB[(frame + BOB_PHASE.get(name, 0)) % 4] if p.bob else 0
        return (c[0], c[1] + dy)

    def spread(c, k=1.0):
        if p.spread <= 0:
            return c
        vx, vy = c[0] - core[0], c[1] - core[1]
        ln = math.hypot(vx, vy) or 1.0
        s = p.spread * k * (0.6 + 0.4 * min(1.0, ln / 20.0))
        return (c[0] + vx / ln * s, c[1] + vy / ln * s)

    def fall(c, hh):
        return (c[0], c[1] + (B - hh - c[1]) * p.fall) if p.fall > 0 else c

    def body_pt(dx, dy):
        return px.rot_pt((X + dx + p.bx, B + dy + p.by), p.lean, pivot)

    def place(name, c, hh, lagged=False):
        c = bob(name, c)
        if lagged:
            c = (c[0] + p.lag[0], c[1] + p.lag[1])
        return fall(spread(c), hh)

    # --- rig ---
    feet = [(X + s[0] + p.feet[i][0], B + s[1] - p.feet[i][1]) for i, s in enumerate((FOOT_N, FOOT_F))]
    foot_n = (spread(feet[0], 0.4)[0], feet[0][1])
    foot_f = (spread(feet[1], 0.4)[0], feet[1][1])
    rise = max(0, p.by)
    shin_n = place("shin_n", (feet[0][0] - 1 + p.bx * 0.5, B + SHIN_N[1] - p.feet[0][1] + rise), 4.5)
    shin_f = place("shin_f", (feet[1][0] - 1 + p.bx * 0.5, B + SHIN_F[1] - p.feet[1][1] + rise), 4.5)
    pelvis = place("pelvis", (X + PELVIS[0] + p.bx, B + PELVIS[1] + p.by), 3)
    torso_c = place("torso", body_pt(*TORSO), 8.5)
    head_c = place("head", body_pt(HEAD[0], HEAD[1]), 4, lagged=True)
    sh_n = place("sh_n", body_pt(SH_N[0], SH_N[1]), 5.5, lagged=True)
    sh_f = place("sh_f", body_pt(SH_F[0], SH_F[1]), 4.5, lagged=True)
    fist_n = place("fist_n", (X + p.fn[0], B + p.fn[1]), FIST_N[1] / 2, lagged=True)
    fist_f = place("fist_f", (X + p.ff[0], B + p.ff[1]), FIST_F[1] / 2, lagged=True)
    raised = p.fn[1] < -30
    fa_n, a_n = _forearm((sh_n[0], sh_n[1] + 1), fist_n, 1 if raised else -1)
    fa_f, a_f = _forearm((sh_f[0], sh_f[1] + 1), fist_f, -1 if raised else 1)
    fa_n, fa_f = bob("fa_n", fa_n), bob("fa_f", fa_f)
    ring_c = bob("torso", body_pt(*RING_C))
    tilt = p.tilt + p.lean * 0.6
    lean = p.lean

    # --- back to front ---
    _ring(cv, ring_c, p.ring, tilt, front=False, spread=p.spread, drop=p.fall * 14)
    _block(cv, sh_f, SH_F[2], SH_F[3], lean, name="sh_f", far=True, cut=(2.2, 2.2, 1.5, 1.5))
    _block(cv, fa_f, 6, ARM_EXT[1] - 1, a_f, name="fa_f", far=True)
    _block(cv, fist_f, FIST_F[0], FIST_F[1], 0, name="fist_f", far=True, cut=(2.0, 2.5, 1.5, 1.5))
    _block(cv, foot_f, FOOT_F[2], FOOT_F[3], 0, name="foot_f", far=True, cut=(1.3, 2.0, 0.6, 0.6))
    _block(cv, shin_f, SHIN_F[2], SHIN_F[3], 0, name="shin_f", far=True)
    _block(cv, pelvis, PELVIS[2], PELVIS[3], lean * 0.5, name="pelvis", cut=(1.8, 1.8, 2.2, 2.2))
    _block(cv, foot_n, FOOT_N[2], FOOT_N[3], 0, name="foot_n", cut=(1.3, 2.2, 0.6, 0.6))
    _block(cv, shin_n, SHIN_N[2], SHIN_N[3], 0, name="shin_n")
    _block(cv, torso_c, 0, 0, lean, name="torso", poly=TORSO_POLY)
    tx, ty = torso_c
    with cv.xform(px.rotate(lean, torso_c)):
        flank = cv.mask_polygon([(tx + a, ty + b) for a, b in FLANK])
        seams = [[cv.tp((tx + a, ty + b)) for a, b in s] for s in
                 (((-4.0, -8.5), (-2.5, 8.5)),  # flank / front edge
                  ((3.5, -8.5), (3.0, -5.5)), ((8.0, 1.5), (7.0, 6.5)),  # column joints on the front
                  ((-9.0, -1.0), (-6.5, 0.5), (-5.5, 4.5)))]
        sing_c = cv.tp((tx + SING_AT[0], ty + SING_AT[1]))
    tor = cv.mask_of("torso") & flank
    fl_band = np.where(tor, np.where(cv.band == 2, 1, 0), -1).astype(np.int8)
    fl_band = np.where(tor & (cv.band == 3), 2, fl_band).astype(np.int8)
    cv._commit(tor, fl_band, BASALT, name="torso")
    for s in seams:
        _seam(cv, s, "torso", BASALT.shadow if s is seams[0] else None)
    _singularity(cv, sing_c, p, frame)
    # hunched faceless head: lit near cheek, visor groove across the front plane
    _block(cv, head_c, 0, 0, lean * 1.2, name="head", sep=True, poly=HEAD_POLY)
    with cv.xform(px.rotate(lean * 1.2, head_c)):
        hx, hy = head_c
        vis = [cv.tp(q) for q in ((hx + 0.5, hy + 0.5), (hx + 4.5, hy + 0.5))]
        cheek = [cv.tp(q) for q in ((hx - 1.5, hy - 3.5), (hx - 1.5, hy + 3.5))]
    _seam(cv, vis, "head")
    _seam(cv, cheek, "head", BASALT.shadow)
    _block(cv, sh_n, SH_N[2], SH_N[3], lean, name="sh_n", sep=True, cut=(2.6, 2.6, 1.6, 2.0))
    _seam(cv, [(sh_n[0] - 1.5, sh_n[1] - 2.5), (sh_n[0] + 0.5, sh_n[1] + 0.5), (sh_n[0] - 0.5, sh_n[1] + 3.5)],
          "sh_n")
    _block(cv, fa_n, 7, ARM_EXT[1], a_n, name="fa_n", sep=True)
    _block(cv, fist_n, FIST_N[0], FIST_N[1], 0, name="fist_n", sep=True, cut=(2.2, 2.8, 1.6, 1.6))
    fx_, fy_ = fist_n
    _seam(cv, [(fx_ + 1.0, fy_ - 4.0), (fx_ + 1.0, fy_ - 0.5)], "fist_n")  # knuckle split
    _ring(cv, ring_c, p.ring, tilt, front=True, spread=p.spread, drop=p.fall * 14)

    if p.rip and not (p.flicker and action == "death"):
        _ripples(cv, frame)

    # --- FX ---
    if p.pull:
        _pull(cv.layer(above=True, outline=False), (math.floor(sing_c[0]) + 0.5, math.floor(sing_c[1]) + 0.5), p,
              frame)
    if p.dust is not None:
        side, t = p.dust
        fxl = cv.layer(above=True, outline=True)
        fxp = foot_n if side < 0 else foot_f
        px.dust(fxl, fxp[0] - 7, cv.gy - 1, t, size=0.8, direction=-1)
        px.dust(fxl, fxp[0] + 7, cv.gy - 1, t, size=0.7, direction=1)
    if p.shock is not None:
        back = cv.layer(above=False, outline=True)
        front = cv.layer(above=True, outline=True)
        mid = (fist_n[0] + 3.5, cv.gy - 2.0)
        _shockwave(back, front, mid, p.shock)
        if p.hit:
            top = cv.layer(above=True, outline=False)
            px.impact(top, fist_n[0] + 4, fist_n[1] - 8, size=5, color=SHOCK.light, core=px.GLINT)
            chips = cv.layer(above=True, outline=True)
            for (dx, dy) in ((-9.0, -12.0), (13.0, -14.0), (17.0, -8.0), (-13.0, -6.0)):
                chips.rect(math.floor(mid[0] + dx), math.floor(mid[1] + dy), 2, 2, BASALT, shade="soft", name="chip")
        else:
            fxl = cv.layer(above=True, outline=True)
            px.dust(fxl, mid[0] - 12, cv.gy - 1, 0.6, size=0.9, direction=-1)
            px.dust(fxl, mid[0] + 12, cv.gy - 1, 0.6, size=0.8, direction=1)
    if action == "hurt" and frame == 0:  # basalt chips knocked off
        fxl = cv.layer(above=True, outline=True)
        for (dx, dy) in ((13.0, -54.0), (18.0, -49.0), (-24.0, -56.0)):
            fxl.rect(X + dx, B + dy, 2, 2, BASALT, shade="soft", name="chip")
    if action == "death" and frame == 0:  # the singularity sputters out in violet sparks
        fxl = cv.layer(above=True, outline=False)
        hc.sparks(fxl, sing_c[0], sing_c[1], 0.6, n=5, radius=9, colors=(SING.light, SING.base), seed=3)


def _pile(cv, p, frame):
    """A heap of fallen basalt blocks; the ring lies broken, the dead singularity stares up."""
    cv.snap_ground = True
    X, B = cv.gx, cv.gy - 1
    dead = SimpleNamespace(**dict(vars(p), sing="dead", squeeze=False))
    blocks = [  # (dx, centre height above the ground edge, w, h, ang, name, far, cut)
        (14.0, 2.5, 10, 5, 0, "foot_f", True, (1.3, 2.0, 0.6, 0.6)),
        (-21.0, 4.5, 10, 9, 12, "fist_f", True, (2.0, 2.5, 1.5, 1.5)),
        (24.0, 3.0, 6, 11, 82, "fa_f", True, (1.3,) * 4),
        (-9.0, 2.5, 12, 5, 0, "foot_n", False, (1.3, 2.2, 0.6, 0.6)),
        (5.0, 4.0, 8, 9, 78, "shin_n", False, (1.3,) * 4),
        (-29.0, 3.5, 7, 12, -70, "fa_n", False, (1.3,) * 4),
        (17.0, 5.0, 11, 10, -14, "fist_n", False, (2.2, 2.8, 1.6, 1.6)),
    ]
    for (dx, hgt, w, h, a, n, far, cut) in blocks:
        _block(cv, (X + dx, B - hgt), w, h, a, name=n, far=far, cut=cut, sep="deep")
    cv.limb([(X - 34.0, B - 1.5), (X - 31.0, B - 3.0), (X - 28.0, B - 3.5), (X - 25.0, B - 3.0)], 1.3, RING,
            shade="two", name="ring", under=True)
    cv.limb([(X + 29.0, B - 1.5), (X + 31.5, B - 2.5), (X + 34.0, B - 2.5)], 1.3, RING, shade="two", name="ring",
            under=True)
    # the torso tipped over on the heap, its singularity dead
    T = (X - 3.0, B - 10.5)
    _block(cv, T, 0, 0, -74, name="torso", poly=TORSO_POLY, sep="deep")
    with cv.xform(px.rotate(-74, T)):
        sc = cv.tp((T[0] + SING_AT[0], T[1] + SING_AT[1]))
        seam = [cv.tp((T[0] + a, T[1] + b)) for a, b in ((-4.0, -8.5), (-2.5, 8.5))]
    _seam(cv, seam, "torso", BASALT.shadow)
    _singularity(cv, sc, dead, frame)
    _block(cv, (X - 17.0, B - 13.5), 11, 11, 24, name="sh_n", cut=(2.6, 2.6, 1.6, 2.0), sep="deep")
    _block(cv, (X + 9.0, B - 12.0), 17, 6, -8, name="pelvis", cut=(1.8, 1.8, 2.2, 2.2), sep="deep")
    _block(cv, (X + 14.0, B - 19.0), 0, 0, -30, name="head", poly=HEAD_POLY, sep="deep")
    if p.dust is not None:
        off = hc.snap_offset(cv)
        fxl = cv.layer(above=True, outline=True)
        px.dust(fxl, X - 24, cv.gy - 1 - off, p.dust, size=1.1, direction=-1)
        px.dust(fxl, X + 26, cv.gy - 1 - off, p.dust, size=1.0, direction=1)
