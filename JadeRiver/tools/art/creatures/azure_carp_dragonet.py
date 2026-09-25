"""Azure carp dragonet - a carp halfway through the Dragon Gate, hovering over Mirrorwater (Water).

View: side, facing right, flying (cell 192, anchor at the body centre).  ~60 art px from the
tail fork to the snout, ~35 px tall from the belly fins to the antler tips (the player is ~50).
In legend a carp that leaps the Dragon Gate becomes a dragon; this one is halfway there: a
deep azure carp body (silver-white belly, gold-tipped fins, a fish's forked tail) whose front
has stretched into a slender rising neck carrying a small dragon head (two short antler
horns, long flowing whiskers, a frilled fin mane along the neck, a glowing pearl eye).  It
swims through the air above a faint turning ring of water and mist, dripping from its tail.
Parts, back to front: mist ring + tail drips (FX), far pectoral fin (dark), long carp dorsal
fin, forked caudal fin, low fins, body tube on a curved spine that rises into the neck (silver
belly, scale arcs), near pectoral fin, head group (far antler, golden fin mane, cheek fin,
jaw + mouth, skull, near antler, brow), pearl eye, whiskers, FX (gathering orb, spit, splash).
Idle: floating undulation, whiskers drifting.  Walk: swims through the air in a travelling
S-wave.  Windup: coils the neck back, jaws open, a water orb gathers in front of the mouth
(held).  Attack: gulps the orb tight, then lunges and spits it in a burst of water (hit frame
1).  Hurt: recoil.  Death: a last jolt, drops nose-first out of the air, flops onto the lake
(everything below the surface hidden, splash and ripple), lies still and fades.
"""
import math

import numpy as np

import pixel as px

SPEC = {
    "id": "azure_carp_dragonet",
    "cell": 192,
    "anchor": [96, 96],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette (6 ramps): azure scales, silver-white belly (also the pearl antlers), pale cyan
# fins with gold tips, water orb, mouth; accents: pearl eye, cyan glow ------------------------
SCALE = px.material("acd_scale", "#9fe2ee", "#46acdf", "#2b70b2", "#2d3a80", outline="#090d22",
                    thresholds=(0.9, 0.52, 0.16))
BELLY = px.material("acd_belly", "#ffffff", "#eef4fa", "#c3d0ea", "#8391c4", outline="#0c0f26")
FIN = px.material("acd_fin", "#f2ffff", "#b4f0f6", "#62b8d6", "#2e5e9a", outline="#0a1328")
GOLD = px.material("acd_gold", "#fff3b4", "#f1c253", "#c08a34", "#7c5628", outline="#1c1206")
ORB = px.material("acd_orb", "#ffffff", "#c4f6ff", "#62cbea", "#2f86c2", outline="#0f2c4c")
MOUTH = px.material("acd_mouth", "#f4909e", "#c24c68", "#7c2a4c", "#461832", outline="#15060e")
PEARL = px.rgb("#f6fbff")
PEARL_SH = px.rgb("#b4cdf2")
PUPIL = px.rgb("#1b2a5c")
GLOW = px.rgb("#8af2ff")
SILVER = (0, 1, 1, 2)  # belly band remap: light, base, base, shadow (stays silver-white)

TAU = 2 * math.pi

# ---- poses --------------------------------------------------------------------------------
# bx, by   body-centre offset from the anchor      ang  pitch (deg, + = nose up)
# k        curvature (deg / px, + arches head and tail down, - curls them up)
# amp, ph  travelling-wave amplitude (deg) and phase (rad) of the swimming undulation
# lift     neck rise (deg / px along the neck; the head is turned back to face forward)
# head     extra head pitch        jaw  gape 0..1     eye  open|angry|squeeze|dead
# fl       tail-fin flick (deg)    pec  pectoral paddle (deg)     wh  whisker / mane drift phase
# wa       whisker sweep (deg, head-local): the whiskers start forward-down and turn by this
# orb      water orb gathered in front of the mouth 0..1 (None = off)
# spit     spit life 0..1 (None = off)       hit  impact spark      streak  lunge speed lines
# ring     mist ring on/off      drip  tail drip phase
# water    lake surface below the body centre (death: everything under it is hidden)
# splash   landing splash / ripple life     fade  opacity
DEFAULTS = dict(bx=0.0, by=0.0, ang=0.0, k=0.3, amp=12.0, ph=0.0, lift=7.5, head=0.0, jaw=0.1, eye="open",
                fl=0.0, pec=0.0, wh=0.0, wa=-40.0, orb=None, spit=None, hit=False, streak=False, ring=1,
                drip=0.0, water=None, splash=None, fade=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # floating: a slow wave rolls along the body, whiskers and fins drifting
        dict(ph=0.0, by=0, pec=0, wh=0.0, drip=0.0),
        dict(ph=TAU * 0.25, by=-1, pec=10, wh=TAU * 0.25, drip=0.25, jaw=0.2),
        dict(ph=TAU * 0.5, by=-1, pec=16, wh=TAU * 0.5, drip=0.5),
        dict(ph=TAU * 0.75, by=0, pec=8, wh=TAU * 0.75, drip=0.75, jaw=0.2),
    ],
    "walk": [  # swimming through the air: a strong S-wave travels from head to tail
        dict(ph=0.0, amp=30, by=0, pec=-10, wh=0.0, drip=0.0, ang=-3, lift=6.5, wa=-40),
        dict(ph=TAU / 6, amp=30, by=-1, pec=6, wh=TAU / 6, drip=1 / 6, ang=-3, lift=6.5, wa=-40),
        dict(ph=TAU * 2 / 6, amp=30, by=-1, pec=18, wh=TAU * 2 / 6, drip=2 / 6, ang=-3, lift=6.5, wa=-40),
        dict(ph=TAU * 3 / 6, amp=30, by=0, pec=8, wh=TAU * 3 / 6, drip=3 / 6, ang=-3, lift=6.5, wa=-40),
        dict(ph=TAU * 4 / 6, amp=30, by=1, pec=-6, wh=TAU * 4 / 6, drip=4 / 6, ang=-3, lift=6.5, wa=-40),
        dict(ph=TAU * 5 / 6, amp=30, by=1, pec=-14, wh=TAU * 5 / 6, drip=5 / 6, ang=-3, lift=6.5, wa=-40),
    ],
    "windup": [  # coils the neck back into an S, jaws open, the lake water gathers into an orb - held
        dict(bx=-2, ang=6, k=-0.6, amp=6, ph=1.0, lift=6.0, jaw=0.5, eye="angry", orb=0.3, fl=-8, pec=14, wh=0.6, wa=-40),
        dict(bx=-4, ang=9, k=-1.4, amp=4, ph=1.2, lift=7.0, head=-4, jaw=0.85, eye="angry", orb=0.7, fl=-16,
             pec=22, wh=1.0, wa=-30),
        dict(bx=-5, ang=10, k=-1.8, amp=3, ph=1.3, lift=7.5, head=-6, jaw=1.0, eye="angry", orb=1.0, fl=-20,
             pec=24, wh=1.2, wa=-25),
    ],
    "attack": [  # the lunge: the orb is spat on frame 1 in a burst of water, then it recovers
        dict(bx=-8, ang=-2, k=0.8, amp=8, ph=3.0, lift=3.5, head=6, jaw=1.0, eye="angry", orb=0.6, fl=14,
             pec=-12, wh=2.0, streak=True, wa=-80),
        dict(bx=-4, ang=-4, k=1.0, amp=10, ph=3.4, lift=1.0, head=4, jaw=1.0, eye="angry", spit=0.3, hit=True,
             fl=20, pec=-18, wh=2.4, streak=True, wa=-85),
        dict(bx=-5, ang=-2, k=0.8, amp=12, ph=3.8, lift=2.5, head=2, jaw=0.6, eye="angry", spit=0.65, fl=8,
             pec=-4, wh=2.8, wa=-75),
        dict(bx=-4, ang=0, k=0.5, amp=12, ph=4.4, lift=4.0, jaw=0.2, spit=0.95, fl=0, pec=6, wh=3.2),
    ],
    "hurt": [
        dict(bx=-4, by=-1, ang=12, k=1.6, amp=4, ph=1.0, lift=6.5, head=12, jaw=0.7, eye="squeeze", fl=-18,
             pec=26, wh=1.0, wa=40),
        dict(bx=-3, by=0, ang=6, k=1.0, amp=8, ph=1.6, lift=5.5, head=6, jaw=0.3, eye="squeeze", fl=-6, pec=12,
             wh=1.6, wa=10),
    ],
    "death": [  # a last jolt, then it drops out of the air, flops onto the lake, lies still and fades
        dict(bx=-3, by=-1, ang=14, k=1.8, amp=4, ph=1.0, lift=7.0, head=14, jaw=0.9, eye="squeeze", fl=-22,
             pec=28, wh=1.0, wa=40),
        dict(bx=-3, by=8, ang=-30, k=1.2, amp=6, ph=2.0, lift=1.0, head=-6, jaw=0.6, eye="dead", fl=18, pec=-20,
             wh=2.0, ring=0, wa=-200),
        dict(bx=-2, by=20, ang=-2, k=1.2, amp=4, ph=2.4, lift=3.0, head=-2, jaw=0.5, eye="dead", fl=16, pec=-30,
             wh=2.6, ring=0, water=5.0, splash=0.3, wa=-20),
        dict(bx=-2, by=21, ang=-2, k=0.9, amp=0, lift=2.4, head=-3, jaw=0.4, eye="dead", fl=6, pec=-30, wh=3.0,
             ring=0, water=5.0, splash=0.75, fade=0.6, wa=-20),
        dict(bx=-2, by=21, ang=-2, k=0.9, amp=0, lift=2.4, head=-3, jaw=0.4, eye="dead", fl=6, pec=-30, wh=3.0,
             ring=0, water=5.0, splash=1.0, fade=0.3, wa=-20),
    ],
})

L_TAIL, L_HEAD = 18.0, 17.0  # spine length behind / in front of the body centre
NECK_S = 7.0  # arc length where the neck starts to rise out of the carp body
WN = TAU / 36.0  # undulation wave number (rad / px)


# ---- spine ----------------------------------------------------------------------------------
def _theta(s, p):
    """Tangent angle (deg) of the spine at arc length s (tail negative, neck positive)."""
    u = (s + L_TAIL) / (L_TAIL + L_HEAD)  # 0 tail base .. 1 back of the head
    env = 0.2 + 0.8 * (1.0 - u) ** 1.3  # the swing grows toward the tail
    return p.ang - p.k * s + p.amp * env * math.sin(p.ph + s * WN) + p.lift * max(0.0, s - NECK_S)


def _spine(M, p):
    """Spine points (one per px of arc length) from the tail base to the back of the head."""
    fwd, back = [M], []
    step = 0.25
    for sign, out in ((1, fwd), (-1, back)):
        x, y = M
        s = 0.0
        n = int((L_HEAD if sign > 0 else L_TAIL) / step)
        for i in range(n):
            th = math.radians(_theta(s + sign * step * 0.5, p))
            x += math.cos(th) * step * sign
            y -= math.sin(th) * step * sign
            s += sign * step
            if (i + 1) % 4 == 0:
                out.append((x, y))
    return back[::-1] + fwd


def _radius(s):
    """Half-depth at arc length s: slim tail base, deep carp body, shoulders, slender neck."""
    if s < 0.0:
        u = (s + L_TAIL) / L_TAIL
        return 2.3 + (7.6 - 2.3) * (3 * u * u - 2 * u * u * u)
    if s < NECK_S:
        u = s / NECK_S
        return 7.6 - (7.6 - 4.8) * (0.5 - 0.5 * math.cos(math.pi * u))
    return 4.8 - 0.9 * (s - NECK_S) / (L_HEAD - NECK_S)


def _frame(pts, i):
    """Tangent (toward the head) and dorsal normal at sample i."""
    a = pts[max(0, i - 1)]
    b = pts[min(len(pts) - 1, i + 1)]
    tx, ty = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(tx, ty) or 1.0
    tx, ty = tx / ln, ty / ln
    return (tx, ty), (ty, -tx)


def _at(pts, radii, s, side, k=1.0):
    """Point on the body edge at arc length s, side +1 dorsal / -1 belly (k = fraction of r)."""
    i = min(len(pts) - 1, max(0, int(round(s + L_TAIL))))
    (tx, ty), (dx, dy) = _frame(pts, i)
    r = radii[i] * k
    return (pts[i][0] + dx * r * side, pts[i][1] + dy * r * side), (tx, ty), (dx, dy)


def _ipt(q):
    return (math.floor(q[0]), math.floor(q[1]))


# ---- fins -----------------------------------------------------------------------------------
def _fin(cv, base0, base1, tip, name, sep=False, gold=0.45, shade="soft", rays=(0.35, 0.7)):
    cv.polygon([base0, tip, base1], FIN, shade=shade, name=name, sep=sep)
    cv.polygon([px.lerp_pt(base0, tip, 1 - gold), tip, px.lerp_pt(base1, tip, 1 - gold)], GOLD, shade=shade,
               decal=True, clip=name, name=name)
    for f in rays:
        b = px.lerp_pt(base0, base1, f)
        e = px.lerp_pt(b, tip, 0.72)
        cv.line(_ipt(b), _ipt(e), FIN.shadow, band=None, decal=True, clip=name, name=name)


def _pectoral(cv, pts, radii, p, far):
    """Broad, wing-like pectoral fin at the shoulder that paddles the air."""
    nm = "pec_far" if far else "pec"
    pa, (tx, ty), dn = _at(pts, radii, 3.5 if far else 2.5, -1, 0.1 if far else 0.4)
    root = (pa[0] + dn[0] * (1.5 if far else 0.0), pa[1] + dn[1] * (1.5 if far else 0.0))
    back = math.degrees(math.atan2(ty, -tx))  # pointing back along the body
    a = back + 30 + p.pec * (0.7 if far else 1.0)  # down-back, paddling
    ln = 7.5 if far else 9.5
    tip = px.polar(root, a, ln)
    b0 = px.polar(root, a + 90, 1.8)
    b1 = px.polar(root, a - 90, 2.2)
    trail = px.polar(px.lerp_pt(root, tip, 0.55), a + 70, 1.6)
    shade = "dark" if far else "soft"
    cv.polygon([b0, trail, tip, b1], FIN, shade=shade, name=nm, sep=False if far else "deep")
    cv.polygon([px.lerp_pt(b0, tip, 0.55), px.lerp_pt(trail, tip, 0.2), tip, px.lerp_pt(b1, tip, 0.55)], GOLD,
               shade=shade, decal=True, clip=nm, name=nm)
    for f in (0.3, 0.7):
        b = px.lerp_pt(b0, b1, f)
        cv.line(_ipt(b), _ipt(px.lerp_pt(b, tip, 0.7)), FIN.deep if far else FIN.shadow, band=None, decal=True,
                clip=nm, name=nm)


def _mane(cv, p):
    """Frilled fin mane (head-local): flame-shaped lobes rooted along the back of the skull and
    the top of the neck, flowing up and back over the shoulders."""
    lobes = ((-8.5, -1.5, 156, 8.0), (-5.6, -3.6, 146, 9.5), (-2.4, -5.2, 134, 10.0))
    for j, (rx, ry, a, ln) in enumerate(lobes):
        a += 6.0 * math.sin(p.wh + j * 1.2)
        root = (rx, ry)
        tip = px.polar(root, a, ln)
        front = px.polar(root, a - 26, ln * 0.6)
        hollow = px.polar(root, a + 16, ln * 0.5)
        poly = [px.polar(root, a - 90, 1.8), front, tip, hollow, px.polar(root, a + 90, 1.8)]
        cv.polygon(poly, FIN, shade="soft", name="mane", sep="deep")
        cv.polygon([px.lerp_pt(poly[0], front, 0.7), front, tip, hollow, px.lerp_pt(poly[4], hollow, 0.8)], GOLD,
                   shade="soft", decal=True, clip="mane", name="mane")
        cv.line(_ipt(root), _ipt(px.lerp_pt(root, tip, 0.7)), FIN.shadow, band=None, decal=True, clip="mane",
                name="mane")


def _body(cv, M, p):
    pts = _spine(M, p)
    n = len(pts)
    radii = [_radius(i - L_TAIL) for i in range(n)]
    tail = pts[0]
    (tx, ty), (dx, dy) = _frame(pts, 0)
    back_a = math.degrees(math.atan2(ty, -tx))  # direction pointing out behind the tail
    _pectoral(cv, pts, radii, p, far=True)
    # carp dorsal fin: long and low along the back, tallest at its front ray
    edge = [_at(pts, radii, sd, 1, 0.75)[0] for sd in (0.0, -13.5)]
    rays = []
    for sd, h, lean in ((-1.0, 5.2, 1.6), (-4.5, 4.0, 1.8), (-8.0, 3.2, 1.8), (-11.5, 2.4, 1.6)):
        q, (ux, uy), dn = _at(pts, radii, sd, 1)
        rays.append((q, (q[0] + dn[0] * h - ux * lean, q[1] + dn[1] * h - uy * lean)))
    cv.polygon([edge[0]] + [r[1] for r in rays] + [edge[1]], FIN, shade="soft", name="dorsal")
    cv.polygon([px.lerp_pt(rays[0][0], rays[0][1], 0.55), rays[0][1], rays[1][1], rays[2][1], rays[3][1],
                px.lerp_pt(rays[3][0], rays[3][1], 0.6)], GOLD, shade="soft", decal=True, clip="dorsal",
               name="dorsal")
    for q, e in rays[1:]:
        cv.line(_ipt(q), _ipt(px.lerp_pt(q, e, 0.8)), FIN.shadow, band=None, decal=True, clip="dorsal",
                name="dorsal")
    # forked caudal fin (the fish's tail it still has)
    tips = []
    for sgn, ln in ((1, 13.0), (-1, 12.0)):
        a = back_a + sgn * 36 + p.fl
        tip = px.polar(tail, a, ln)
        mid = px.polar(tail, back_a + p.fl + sgn * 5, 5.6)
        root_a = (tail[0] + dx * 2.8 * sgn, tail[1] + dy * 2.8 * sgn)
        outer = px.polar(px.lerp_pt(root_a, tip, 0.45), a + sgn * 90, 2.6)
        cv.polygon([root_a, outer, tip, mid], FIN, shade="soft", name="tailfin")
        cv.polygon([px.lerp_pt(outer, tip, 0.35), tip, px.lerp_pt(mid, tip, 0.45)], GOLD, shade="soft",
                   decal=True, clip="tailfin", name="tailfin")
        for f in (0.3, 0.7):
            b = px.lerp_pt(root_a, mid, f)
            cv.line(_ipt(b), _ipt(px.lerp_pt(b, tip, 0.75)), FIN.shadow, band=None, decal=True, clip="tailfin",
                    name="tailfin")
        tips.append(tip)
    # anal + pelvic fins under the belly
    for s0, s1, h in ((-13.0, -8.5, 3.4), (-5.0, -1.0, 3.6)):
        a0, _, bn = _at(pts, radii, s0, -1)
        a1 = _at(pts, radii, s1, -1)[0]
        tip = (a0[0] - bn[0] * h - (a1[0] - a0[0]) * 0.4, a0[1] - bn[1] * h - (a1[1] - a0[1]) * 0.4)
        _fin(cv, (a0[0] + bn[0] * 2, a0[1] + bn[1] * 2), (a1[0] + bn[0] * 2, a1[1] + bn[1] * 2), tip, "lowfin",
             gold=0.5)
    # body tube
    cv.limb(pts, radii, SCALE, name="body", sep="deep")
    # silver-white belly running up the throat
    belly = [(q[0] - fr[1][0] * r * 0.78, q[1] - fr[1][1] * r * 0.78)
             for q, r, fr in ((pts[i], radii[i], _frame(pts, i)) for i in range(n))]
    cv.limb(belly, [r * 0.52 for r in radii], BELLY, shade=SILVER, decal=True, clip="body", name="body")
    # scale arcs: staggered rows over the flank, the free edge curving toward the tail
    for i in range(4, int(L_TAIL + NECK_S) - 1, 4):
        (ux, uy), (vx, vy) = _frame(pts, i)
        a = math.degrees(math.atan2(-uy, ux))
        for j, f in enumerate((0.5, 0.1)):
            sh = 2 if j else 0
            q = (pts[i][0] + vx * radii[i] * f + ux * sh, pts[i][1] + vy * radii[i] * f + uy * sh)
            with cv.xform(px.rotate(a, q)):
                cv.stamp([".k", "k.", "k.", ".k"], math.floor(q[0]), math.floor(q[1]) - 2, {"k": SCALE.step(1)},
                         name="body", decal=True, clip="body")
    return pts, radii, tips


# ---- head -----------------------------------------------------------------------------------
def _antler(cv, root, a, ln, far):
    """Short dragon antler: a curved main beam bending back with one forward tine."""
    mid = px.polar(root, a, ln * 0.5)
    tip = px.polar(mid, a + 32, ln * 0.55)
    fork = px.lerp_pt(root, mid, 0.85)
    tine = px.polar(fork, a - 50, ln * 0.36)
    shade = "dark" if far else "soft"
    nm = "horn_far" if far else "horn"
    sep = False if far else "deep"
    cv.limb([fork, tine], [0.8, 0.45], BELLY, shade=shade, name=nm, sep=sep)
    cv.limb([root, mid, tip], [1.2, 0.9, 0.45], BELLY, shade=shade, name=nm, sep=sep)


def _head(cv, N, ang, p):
    """Small dragon head in a local frame (x forward, y down); N = back of the skull."""
    out = {}
    with cv.xform(px.translate(N[0], N[1]), px.rotate(ang)):
        _antler(cv, (-1.4, -5.6), 108, 10.0, far=True)
        _mane(cv, p)
        # cheek fin fanning back from behind the jaw, like a dragon's ear
        for k, (a, ln) in enumerate(((150, 6.0), (174, 7.0), (198, 5.5))):
            root = (-0.5, -1.5)
            a += 6 * math.sin(p.wh + k)
            tip = px.polar(root, a, ln)
            mid = px.polar(root, a + 12, ln * 0.6)
            cv.polygon([px.polar(root, a + 90, 1.4), mid, tip, px.polar(root, a - 90, 1.4)], FIN, shade="soft",
                       name="cheek", sep="deep")
            cv.polygon([px.lerp_pt(root, tip, 0.6), px.lerp_pt(mid, tip, 0.4), tip], GOLD, shade="soft",
                       decal=True, clip="cheek", name="cheek")
        jaw_rot = -30 * p.jaw
        if p.jaw > 0.12:  # mouth lining
            with cv.xform(px.rotate(jaw_rot * 0.5, (1.0, 1.2))):
                cv.polygon([(-0.5, 0.4), (14.2, 0.2), (13.6, 2.6), (1.0, 3.8)], MOUTH, shade="two", name="mouth")
        with cv.xform(px.rotate(jaw_rot, (1.0, 1.2))):
            cv.polygon([(-2.5, 0.8), (13.6, 0.8), (14.2, 2.2), (11.0, 3.6), (4.0, 4.6), (-1.5, 3.8)], SCALE,
                       shade="two", name="jaw", sep="deep")
            cv.polygon([(1.0, 3.2), (13.5, 2.0), (11.0, 3.8), (3.0, 5.0)], BELLY, shade=SILVER, decal=True,
                       clip="jaw", name="jaw")
            if p.jaw > 0.12:  # lower fang
                cv.polygon([(10.6, 1.0), (12.0, 1.0), (11.2, -0.8)], BELLY, shade="flatlight", name="tooth")
        skull = [(-3.5, -3.5), (-1.5, -5.8), (2.0, -7.0), (5.5, -6.6), (7.4, -5.0), (8.4, -3.8), (11.0, -3.8),
                 (12.8, -4.8), (14.6, -4.4), (15.4, -2.6), (15.2, -0.6), (13.8, 0.8), (5.0, 1.4), (0.0, 2.6),
                 (-3.0, 3.0), (-4.2, 0.0)]
        cv.polygon(skull, SCALE, name="head", sep="deep")
        # pale upper lip at the muzzle, nostril, snout ridge
        cv.polygon([(10.0, -0.4), (15.0, -1.4), (15.4, -0.4), (13.8, 0.8), (10.0, 1.2)], BELLY, shade=SILVER,
                   decal=True, clip="head", name="head")
        if p.jaw > 0.12:  # upper fang hanging over the gape
            cv.polygon([(12.4, 0.6), (13.8, 0.6), (13.2, 2.6)], BELLY, shade="flatlight", name="tooth")
        cv.pixels([(13, -4), (14, -4)], SCALE.deep, name="nostril")
        cv.line((9, -3), (11, -3), SCALE.step(1), band=None, decal=True, clip="head", name="head")
        _antler(cv, (0.8, -6.4), 98, 11.0, far=False)
        # heavy brow ridge over the eye
        brow = [(1.6, -6.2), (4.8, -6.8), (7.8, -5.0)]
        if p.eye == "angry":
            brow = [(1.6, -7.0), (4.8, -6.0), (8.0, -4.0)]
        cv.limb(brow, [1.2, 1.2, 0.7], SCALE, shade="two", name="brow", sep="deep")
        out["eye"] = cv.tp((4.6, -3.8))
        out["whiskers"] = [[cv.tp(q) for q in w] for w in _whisker_paths(p)]
        out["mouth"] = cv.tp((15.8, 1.2 + 2.2 * p.jaw))
        out["fwd"] = cv.tp((1.0, 0.0))
        out["o"] = cv.tp((0.0, 0.0))
    return out


def _eye(cv, at, state):
    """Glowing pearl eye: pearl white with a dark pupil; the rim glows cyan when enraged."""
    ex, ey = math.floor(at[0]), math.floor(at[1])
    if state in ("open", "angry"):
        rim = GLOW if state == "angry" else PEARL_SH
        cv.stamp([".pp.", "pgWp", "pWkp", ".pp."], ex - 1, ey - 1, {"p": rim, "g": px.GLINT, "W": PEARL, "k": PUPIL},
                 name="eye")
    elif state == "squeeze":
        cv.stamp(["kk..", "..kk", "kk.."], ex - 1, ey - 1, {"k": px.INK}, name="eye")
    else:
        cv.stamp(["k.k", ".k.", "k.k"], ex - 1, ey - 1, {"k": px.INK}, name="eye")


def _whisker_paths(p):
    """Two long whiskers from the upper lip (head-local): they drop from the lip and stream
    back under the throat in a lazy wave."""
    paths = []
    for k, (ln, a0, sweep) in enumerate(((24.0, -130.0, 1.0), (13.0, -98.0, 0.4))):
        root = (14.6 - 2.0 * k, 0.6 + 0.8 * k)
        q = root
        pts = [q]
        n = 12
        for i in range(n):
            u = (i + 0.5) / n
            a = a0 + p.wa * sweep * (3 * u * u - 2 * u * u * u) + 12.0 * math.sin(p.wh + i * 0.8 + k * 1.7) * u
            q = px.polar(q, a, ln / n)
            pts.append(q)
        paths.append(pts)
    return paths


def _whiskers(cv, paths, water_y=1e9):
    """Draw whisker paths (canvas coords) unoutlined, so they stay whisker-fine."""
    wl = cv.layer(above=True, outline=False)
    for pts in paths:
        for a_, b_ in zip(pts, pts[1:]):
            if max(a_[1], b_[1]) >= water_y - 1:  # under the lake surface: hidden
                break
            wl.line(_ipt(a_), _ipt(b_), GOLD.light, name="whisker")
            wl.line((math.floor(a_[0]), math.floor(a_[1]) + 1), (math.floor(b_[0]), math.floor(b_[1]) + 1),
                    GOLD.shadow, name="whisker", under=True)


# ---- FX -------------------------------------------------------------------------------------
def _mist_ring(cv, cx, cy, frame):
    """Faint dashed ring of water and mist hovering beneath the body, slowly turning."""
    back = cv.layer(above=False, outline=False)
    rx, ry = 13.0, 2.6
    u = (back.X - cx) / rx
    v = (back.Y - cy) / ry
    d = np.sqrt(u * u + v * v)
    ring = np.abs(d - 1.0) * min(rx, ry) <= 0.55
    ang = (np.degrees(np.arctan2(v, u)) + frame * 17.0) % 72.0
    ring &= ang < 50.0
    top = ring & (back.Y < cy)
    back.fill(top, px.flat(ORB.deep), shade="flat", name="ring")
    back.fill(ring & ~top, px.flat(ORB.shadow), shade="flat", name="ring")


def _drop(fx, x, y, name="drop"):
    fx.stamp(["l", "b"], math.floor(x), math.floor(y), {"l": ORB.light, "b": ORB.shadow}, name=name)


def _drips(cv, tips, phase):
    fx = cv.layer(above=False, outline=True)
    for k, tip in enumerate(tips):
        u = (phase + k * 0.5) % 1.0
        _drop(fx, tip[0] + 0.5 - k, tip[1] + 2.5 + u * 8.0)


def _orb(cv, mouth, fwd, t, frame):
    """The lake water gathering into a glowing orb in front of the open jaws."""
    fx = cv.layer(above=True, outline=True)
    R = 1.6 + 3.4 * t
    c = (mouth[0] + fwd[0] * (R + 1.5), mouth[1] + fwd[1] * (R + 1.5) - 1.5)
    glow = cv.layer(above=True, outline=False)
    px.glow_ring(glow, c[0], c[1], R + 2.4, GLOW, thickness=1.0)
    fx.circle(c[0], c[1], R, ORB, shade="soft", name="orb")
    fx.circle(c[0] - R * 0.35, c[1] - R * 0.35, max(0.7, R * 0.3), px.flat(ORB.light), name="orb")
    for k in range(int(2 + 4 * t)):  # droplets spiralling in toward the orb
        a = k * 72.0 + frame * 40.0
        rr = R + 4.5 + 2.0 * ((k + frame) % 3)
        q = px.polar(c, a, rr)
        _drop(fx, q[0], q[1])
    return c


def _spit(cv, mouth, t, hit):
    """The orb shot out of the jaws: the water ball with its wake, a fan of spray bursting
    from the jaws, then the spray falling away."""
    fx = cv.layer(above=True, outline=True)
    m = (mouth[0] + 1.0, mouth[1])
    if t < 0.5:
        c = (m[0] + 9.0, m[1] - 0.5)
        streak = cv.layer(above=False, outline=False)
        for dy, ln in ((-3, 6), (0, 9), (3, 6)):
            streak.line((math.floor(c[0] - 4), math.floor(c[1] + dy)), (math.floor(c[0] - 4 - ln), math.floor(c[1] + dy)),
                        GLOW if dy == 0 else px.MIST_BLUE, name="streak")
        glow = cv.layer(above=True, outline=False)
        px.glow_ring(glow, c[0], c[1], 6.4, GLOW, thickness=1.0)
        fx.limb([m, c], [1.0, 2.6], ORB, shade="soft", name="wake")
        fx.circle(c[0], c[1], 4.4, ORB, shade="soft", name="orb")
        fx.circle(c[0] - 1.5, c[1] - 1.6, 1.3, px.flat(ORB.light), name="orb")
        if hit:
            top = cv.layer(above=True, outline=False)
            px.impact(top, c[0] + 7, c[1], size=3, color=GLOW, core=px.GLINT)
    for i, (a, v) in enumerate(((50, 1.0), (28, 1.2), (-26, 1.2), (-48, 1.0), (72, 0.8), (-70, 0.8))):
        d = (4.0 + 8.0 * t) * v
        q = px.polar(m, a, d)
        q = (q[0], q[1] + 7.0 * t * t)
        if t > 0.8 and i % 2:
            continue
        fx.circle(q[0], q[1], max(0.8, 1.4 - 0.7 * t), ORB, shade="soft", name="spray")


def _landing(cv, cx, y, t, x0, x1):
    """It slaps down onto the lake: splash crowns at both ends and a spreading ripple."""
    back = cv.layer(above=False, outline=True)
    front = cv.layer(above=True, outline=True)
    w = (x1 - x0) / 2.0 + 3.0 + 4.0 * t
    flat = (back.X * 0, back.X * 0 - 1.0, back.X * 0 + 0.5)
    ring = back.mask_ellipse(cx, y, w, 2.6) & ~back.mask_ellipse(cx, y - 0.4, w - 1.8, 1.6)
    back.fill(ring, ORB, normals=flat, shade="soft", name="ripple")
    lip = front.mask_ellipse(cx, y, w, 2.6) & ~front.mask_ellipse(cx, y - 0.4, w - 1.8, 1.6) & (front.Y > y + 0.5)
    front.fill(lip, ORB, normals=flat, shade="soft", name="ripple")
    if t < 0.95:
        px.splash(front, x0 - 2, y, t, size=1.3, mat=ORB)
        px.splash(front, x1 + 3, y, min(1.0, t + 0.15), size=1.1, mat=ORB)


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C0 = (cv.gx, cv.gy)
    M = (C0[0] - 2 + p.bx, C0[1] + 5 + p.by)  # carp body centre; the whole figure centres on the anchor
    pts, radii, tips = _body(cv, M, p)
    (tx, ty), _ = _frame(pts, len(pts) - 1)
    neck = pts[-1]
    # the neck rises; the head turns back down to look ahead
    hang = math.degrees(math.atan2(-ty, tx)) - 0.85 * p.lift * (L_HEAD - NECK_S) + p.head
    _pectoral(cv, pts, radii, p, far=False)
    H = _head(cv, (neck[0] - 0.5, neck[1] - 0.3), hang, p)
    _eye(cv, H["eye"], p.eye)
    water_y = 1e9
    if p.water is not None:  # flopped onto the lake: everything below the surface is hidden
        water_y = math.floor(M[1] + p.water)
        xs = np.nonzero(cv.filled[water_y - 1])[0]
        x0, x1 = (xs.min(), xs.max()) if len(xs) else (M[0] - 10, M[0] + 10)
        cv.rect(0, water_y, cv.w, cv.h - water_y, SCALE, erase=True)
        _landing(cv, (x0 + x1) / 2.0, water_y, p.splash, x0, x1)
    _whiskers(cv, H["whiskers"], water_y)
    if p.ring:
        _mist_ring(cv, M[0] + 2, C0[1] + 20, frame)
        _drips(cv, tips[1:], p.drip)
    fwd = (H["fwd"][0] - H["o"][0], H["fwd"][1] - H["o"][1])
    if p.orb is not None:
        _orb(cv, H["mouth"], fwd, p.orb, frame)
    if p.spit is not None:
        _spit(cv, H["mouth"], p.spit, p.hit)
    if p.streak:
        back = cv.layer(above=False, outline=False)
        px.speed_lines(back, M[0] - 22, M[1] - 3, length=7, count=3, spacing=4, color=px.MIST_BLUE)
