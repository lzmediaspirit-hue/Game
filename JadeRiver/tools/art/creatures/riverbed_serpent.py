"""Riverbed serpent - FIELD BOSS: a giant jade dragon-eel rising out of the river (Water).

View: side, facing right (cell 256, 128 art px).  ~110 art px of body stands above the water.
Flying (the body floats): the anchor is the waterline centre, everything below the surface is
cut away and foam / spray rings the base.
Parts, back to front: a far coil arching out of the water (shadowed), the main S-curved body
(jade tube, gold belly scutes, scale arcs, fin crest with gold spines), the head group (gill
frill, swept-back horns, long upper jaw + hinged lower jaw with fangs, heavy brow over a
glowing gold eye, long flowing whiskers), FX (base foam, ripples, gathered water orb, splash).
Idle: slow coil sway.  Walk: undulating S.  Windup: rears back, jaws gape, river water
spirals up into a swelling orb (long, clear tell; held).  Attack: massive lunging bite
(hit frame 1) with a splash.  Hurt: recoil.  Death: sinks beneath the water.
"""
import math

import pixel as px
import helpers_batch_b as hb

SPEC = {
    "id": "riverbed_serpent",
    "cell": 256,
    "anchor": [128, 236],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: jade scales, gold belly, cyan fins, bone-gold horns ----------------------------
SCALE = px.material("rs_scale", "#96f0c8", "#2fa982", "#1b7466", "#114a4c", outline="#051613",
                    thresholds=(0.9, 0.5, 0.14))
FAR = px.material("rs_far", "#56b894", "#237d68", "#175654", "#0f3a3e", outline="#04110f")
BELLY = px.material("rs_belly", "#fff2ac", "#e5b84c", "#b07e30", "#6e4a22", outline="#1a1206")
FIN = px.material("rs_fin", "#d2fff2", "#6fdcc2", "#2c9e8f", "#15514f", outline="#051613")
HORN = px.material("rs_horn", "#fff6d2", "#e8d49c", "#b09c6a", "#6e6040", outline="#171208")
MOUTH = px.material("rs_mouth", "#e0707a", "#a83a4c", "#6e2034", "#401222", outline="#140608")
TOOTH = px.material("rs_tooth", "#ffffff", "#f0ead6", "#bcb49c", "#7c7462", outline="#140608")
GOLD = px.material("rs_gold", "#fff2ac", "#e5b84c", "#b07e30", "#6e4a22", outline="#1a1206")
FOAM = px.material("rs_foam", "#ffffff", "#e6fbf6", "#a8e4dc", "#5cb4b4", outline="#15414f")
WATER = px.WATER_FX
EYE_CORE = px.rgb("#fffbe0")
EYE_GLOW = px.rgb("#ffd24a")
EYE_RING = px.rgb("#e0801e")

# ---- poses --------------------------------------------------------------------------------
# ph       sway / undulation phase     sway  sway amplitude (px)    wave  travelling wave (walk)
# rear     0..1 rear back (windup)     lunge 0..1 bite lunge (attack)     sink  px sunk (death)
# ang      head angle (deg, + = nose up)   jaw  0..1 gape   eye  open|angry|squeeze|dead
# orb      gathered water orb 0..1 (None = off)   splash  splash life   hit  impact
# hump     far coil phase    fade  opacity
DEFAULTS = dict(ph=0.0, sway=1.5, wave=0.0, rear=0.0, lunge=0.0, sink=0.0, ang=-6, jaw=0.15, eye="open", orb=None,
                splash=None, hit=False, hump=0.0, fade=1.0, foam=0.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # slow coil sway, whiskers drifting
        dict(ph=0.0, foam=0.0),
        dict(ph=1.57, foam=0.25, jaw=0.2),
        dict(ph=3.14, foam=0.5, ang=-4),
        dict(ph=4.71, foam=0.75, jaw=0.2),
    ],
    "walk": [  # undulating: a wave rolls up the body, the far coil rolls along
        dict(ph=0.0, wave=1.0, hump=0.0, foam=0.0),
        dict(ph=1.05, wave=1.0, hump=1.05, foam=0.17),
        dict(ph=2.1, wave=1.0, hump=2.1, foam=0.33),
        dict(ph=3.14, wave=1.0, hump=3.14, foam=0.5),
        dict(ph=4.19, wave=1.0, hump=4.19, foam=0.67),
        dict(ph=5.24, wave=1.0, hump=5.24, foam=0.83),
    ],
    "windup": [  # rears back, jaws gape, the river spirals up into a swelling orb - held
        dict(rear=0.45, ang=8, jaw=0.5, eye="angry", orb=0.3, sway=0.6, foam=0.2),
        dict(rear=0.85, ang=16, jaw=0.9, eye="angry", orb=0.7, sway=0.4, foam=0.5),
        dict(rear=1.0, ang=18, jaw=1.0, eye="angry", orb=1.0, sway=0.3, foam=0.8),
    ],
    "attack": [  # the lunge: jaws wide, snap on frame 1 at full reach, splash, pull back
        dict(lunge=0.55, ang=-18, jaw=1.0, eye="angry", sway=0.0, splash=0.15),
        dict(lunge=1.0, ang=-26, jaw=0.15, eye="angry", sway=0.0, hit=True, splash=0.45),
        dict(lunge=0.8, ang=-20, jaw=0.35, eye="angry", sway=0.0, splash=0.75),
        dict(lunge=0.3, ang=-10, jaw=0.2, sway=0.5, foam=0.5),
    ],
    "hurt": [
        dict(rear=0.55, ang=26, jaw=0.7, eye="squeeze", sway=0.0, ph=1.0, foam=0.3),
        dict(rear=0.3, ang=10, jaw=0.4, eye="squeeze", sway=0.5, ph=1.6, foam=0.6),
    ],
    "death": [  # a last roar, then it slumps and sinks beneath the river
        dict(rear=0.6, ang=34, jaw=1.0, eye="squeeze", sway=0.0, foam=0.3),
        dict(lunge=0.35, sink=22, ang=-30, jaw=0.6, eye="dead", sway=0.0, splash=0.2),
        dict(lunge=0.45, sink=58, ang=-36, jaw=0.5, eye="dead", sway=0.0, splash=0.55),
        dict(lunge=0.5, sink=86, ang=-40, jaw=0.4, eye="dead", sway=0.0, splash=0.85, fade=0.6),
        dict(lunge=0.5, sink=112, ang=-40, jaw=0.4, eye="dead", sway=0.0, fade=0.3),
    ],
})

# main S-curve keypoints: (dx from the anchor, height above the waterline), water -> head base
BODY_KP = ((-6.0, -8.0), (-5.0, 10.0), (-15.0, 33.0), (-9.0, 58.0), (2.0, 76.0), (10.0, 86.0))


def _keypoints(p):
    kp = []
    n = len(BODY_KP) - 1
    for i, (dx, h) in enumerate(BODY_KP):
        u = i / n
        dx += p.sway * math.sin(p.ph + i * 0.9) * u
        if p.wave:
            dx += 3.0 * math.sin(p.ph * 1.0 - i * 1.2) * (0.3 + 0.7 * u)
        dx -= p.rear * u * u * 14.0
        h += p.rear * u * 5.0
        dx += p.lunge * (u ** 1.5) * 17.0
        h -= p.lunge * u * u * 30.0
        h -= p.sink
        kp.append((dx, h))
    return kp


def _radius(t):
    """Body radius along the path: t = 0 under the water .. 1 at the head base."""
    return 10.0 - 3.6 * t


def _crest(cv, pts, radii, nrm, i0, i1, name="crest", mat=FIN, scale=1.0):
    """Spiky fin crest along the back (the side opposite the belly) between samples i0..i1."""
    base, top = [], []
    for j, i in enumerate(range(i0, i1)):
        r = radii[i]
        u = (i - i0) / max(1, i1 - i0)
        h = (3.0 + 4.0 * math.sin(math.pi * u)) * scale * (1.0 if j % 3 == 0 else 0.6)
        bx, by = pts[i][0] - nrm[i][0] * (r - 1.5), pts[i][1] - nrm[i][1] * (r - 1.5)
        base.append((bx, by))
        top.append((pts[i][0] - nrm[i][0] * (r + h), pts[i][1] - nrm[i][1] * (r + h)))
    if len(base) < 2:
        return
    cv.polygon(base + top[::-1], mat, shade="soft", name=name)
    for k in range(0, len(top), 3):  # gold spines
        cv.line((math.floor(base[k][0]), math.floor(base[k][1])), (math.floor(top[k][0]), math.floor(top[k][1])),
                GOLD.shadow if mat is FIN else FAR.deep, band=None, decal=True, clip=name, name=name)


def _body(cv, pts, name="body", mat=SCALE, far=False):
    n = len(pts)
    radii = [_radius(i / (n - 1)) for i in range(n)]
    nrm = hb.belly_normals(pts, toward=(1.0, 0.6))
    _crest(cv, pts, radii, nrm, 2, n - 3, name=name + "_crest", mat=FIN if not far else FAR)
    cv.limb(pts, radii, mat, shade="full" if not far else "nolight", name=name)
    if far:
        return radii, nrm
    # gold belly scutes on the front of the S
    belly = hb.offset(pts, nrm, radii, 0.62)
    cv.limb(belly, [r * 0.55 for r in radii], BELLY, shade="two", decal=True, clip=name, name=name)
    for i in range(2, n - 2, 3):
        a = hb.offset([pts[i]], [nrm[i]], [radii[i]], 0.2)[0]
        b = hb.offset([pts[i]], [nrm[i]], [radii[i]], 1.0)[0]
        cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])), BELLY.step(1), band=None,
                decal=True, clip=name, name=name)
    # scale arcs over the jade flank: staggered rows, one tone darker than the surface
    for i in range(3, n - 3, 4):
        (tx, ty) = (pts[min(n - 1, i + 1)][0] - pts[i - 1][0], pts[min(n - 1, i + 1)][1] - pts[i - 1][1])
        a = math.degrees(math.atan2(-ty, tx))
        for j, f in enumerate((-0.55, -0.15)):
            off = 2.0 if (i // 4 + j) % 2 else 0.0
            ln = math.hypot(tx, ty) or 1.0
            q = (pts[i][0] + nrm[i][0] * radii[i] * f + tx / ln * off, pts[i][1] + nrm[i][1] * radii[i] * f + ty / ln * off)
            with cv.xform(px.rotate(a + 90, q)):
                cv.stamp(["k.k", ".k."], math.floor(q[0]) - 1, math.floor(q[1]), {"k": SCALE.step(1)}, name=name,
                         decal=True, clip=name)
    return radii, nrm


def _head(cv, Hb, ang, p):
    """Dragon-eel head in a local frame (x forward, y down), Hb = back of the skull."""
    HS = 1.3  # head scale
    with cv.xform(px.translate(Hb[0], Hb[1]), px.rotate(ang), px.scale(HS, HS)):
        # gill frill fanning back from behind the jaw
        for k, (a, ln) in enumerate(((150, 9.0), (175, 10.5), (200, 9.5), (222, 7.5))):
            root = (-1.0, 0.5)
            tip = px.polar(root, a, ln)
            mid = px.polar(root, a - 8, ln * 0.55)
            cv.polygon([px.polar(root, a + 90, 1.6), mid, tip, px.polar(root, a - 90, 1.6)], FIN, shade="soft",
                       name="frill", sep="deep")
            cv.line((math.floor(root[0]), math.floor(root[1])), (math.floor(tip[0]), math.floor(tip[1])),
                    GOLD.shadow, band=None, decal=True, clip="frill", name="frill")
        # swept-back horns
        for (r0, r1, ln, w) in (((4.0, -7.0), 150, 14.0, 1.6), ((8.0, -7.5), 140, 11.0, 1.3)):
            mid = px.polar(r0, r1 - 10, ln * 0.55)
            tip = px.polar(mid, r1 + 15, ln * 0.5)
            cv.limb([r0, mid, tip], [w, w * 0.8, 0.5], HORN, shade="soft", name="horn", sep="deep")
        jaw_rot = -34 * p.jaw
        # mouth lining + lower jaw + lower fangs
        if p.jaw > 0.08:
            with cv.xform(px.rotate(jaw_rot * 0.5, (2.0, 2.5))):
                cv.polygon([(-1.0, 1.5), (23.0, 2.0), (22.0, 4.5), (0.0, 5.5)], MOUTH, shade="two", name="mouth")
        with cv.xform(px.rotate(jaw_rot, (2.0, 2.5))):
            cv.polygon([(-2.0, 2.0), (22.5, 2.6), (23.5, 4.6), (15.0, 7.2), (3.0, 8.4), (-3.0, 5.4)], SCALE,
                       shade="two", name="jaw", sep="deep")
            cv.polygon([(2.0, 6.4), (21.0, 3.8), (15.0, 7.4), (3.0, 8.8)], BELLY, shade="two", decal=True, clip="jaw",
                       name="jaw")
            if p.jaw > 0.08:
                for x in range(6, 22, 4):
                    cv.polygon([(x - 0.8, 2.8), (x + 0.8, 2.8), (x, 0.4)], TOOTH, shade="flat", name="tooth")
        # upper jaw / skull
        skull = [(-3.0, -6.0), (4.0, -8.6), (12.0, -7.6), (20.0, -4.8), (26.5, -2.4), (27.8, 0.6), (25.0, 2.4),
                 (8.0, 2.8), (-2.0, 4.0), (-4.5, 0.0)]
        cv.polygon(skull, SCALE, name="head", sep="deep")
        cv.polygon([(8.0, 1.0), (25.5, 0.6), (25.0, 2.4), (8.0, 2.8)], BELLY, shade="two", decal=True, clip="head",
                   name="head")
        if p.jaw > 0.08:  # upper fangs hanging over the gape
            for x in range(8, 24, 4):
                cv.polygon([(x - 0.9, 2.2), (x + 0.9, 2.2), (x, 4.8 if x in (8, 20) else 3.8)], TOOTH, shade="flat",
                           name="tooth")
        # nostril, scale ridges along the snout
        cv.pixels([(25, -2), (24, -2)], SCALE.deep, name="nostril")
        for x in (14, 18):
            cv.line((x, -6), (x + 2, -4), SCALE.step(1), band=None, decal=True, clip="head", name="head")
        # heavy brow ridge over the glowing eye
        brow = [(5.0, -8.8), (10.0, -8.4), (15.5, -6.2)]
        if p.eye == "angry":
            brow = [(5.0, -9.6), (10.0, -7.8), (15.5, -4.6)]
        mouth_pt = cv.tp((24.0, 3.0 + 3.0 * p.jaw))
        whisker_root = cv.tp((24.5, 1.8))
        jaw_front = cv.tp((27.0, 3.0))
        eye_at = cv.tp((10.0, -5.0))
    # the eye is stamped unscaled (crisp), then the brow sits over it
    with cv.xform(px.translate(math.floor(eye_at[0]), math.floor(eye_at[1])), px.rotate(ang)):
        ex, ey = -1, -1
        if p.eye in ("open", "angry"):
            cv.stamp([".rrr.", "rWYYr", "rYYkr", ".rrr."], ex, ey, {"r": EYE_RING, "Y": EYE_GLOW, "W": EYE_CORE,
                                                                  "k": px.INK}, name="eye")
        elif p.eye == "squeeze":
            cv.stamp(["rr...", "..YYr", "rr..."], ex, ey, {"r": EYE_RING, "Y": EYE_GLOW}, name="eye")
        else:
            cv.stamp(["k...k", ".k.k.", "..k..", ".k.k."], ex, ey - 1, {"k": px.INK}, name="eye")
    with cv.xform(px.translate(Hb[0], Hb[1]), px.rotate(ang), px.scale(HS, HS)):
        cv.limb(brow, [1.6, 1.4, 0.9], SCALE, shade="two", name="brow", sep="deep")
    return mouth_pt, whisker_root, jaw_front


def _whiskers(cv, root, ang, p, water_y=1e9):
    """Two long, thin barbels streaming back from the upper lip in a lazy wave
    (unoutlined, so they stay whisker-fine against the body)."""
    wl = cv.layer(above=True, outline=False)
    for k, (ln, drop) in enumerate(((36.0, 1.0), (26.0, 0.8))):
        pts = [root]
        a = ang - 135 - 14 * k
        q = root
        for s in range(10):
            a -= 4.0 * drop - 9 * math.sin(p.ph + s * 0.7 + k * 1.3)
            q = px.polar(q, a, ln / 10)
            pts.append(q)
        for a_, b_ in zip(pts, pts[1:]):
            if max(a_[1], b_[1]) >= water_y - 1:  # under the surface: hidden
                break
            wl.line((math.floor(a_[0]), math.floor(a_[1])), (math.floor(b_[0]), math.floor(b_[1])), GOLD.light,
                    name="whisker")
            wl.line((math.floor(a_[0]), math.floor(a_[1]) + 1), (math.floor(b_[0]), math.floor(b_[1]) + 1), GOLD.shadow,
                    name="whisker", under=True)


def _far_coil(cv, gx, gy, p):
    """A second coil arching out of the water behind, rolling with the undulation."""
    x0 = gx - 44 + 3 * math.sin(p.hump)
    h = 16 + 3 * math.cos(p.hump) - p.sink * 0.3
    kp = [(x0, gy + 6), (x0 + 4, gy - h * 0.7), (x0 + 11, gy - h), (x0 + 18, gy - h * 0.7), (x0 + 22, gy + 6)]
    pts = hb.resample(hb.catmull(kp, 6), 1.2)
    n = len(pts)
    radii = [6.5] * n
    nrm = hb.belly_normals(pts, toward=(0.0, 1.0))
    _crest(cv, pts, radii, nrm, 3, n - 3, name="far_crest", mat=FAR, scale=0.8)
    cv.limb(pts, radii, FAR, shade="nolight", name="far")


def _foam(cv, cx, gy, t, w=14.0):
    """Churning foam where the body breaks the surface."""
    for k in range(7):
        u = k / 6.0
        x = cx - w + 2 * w * u
        bob = math.sin(t * 6.283 + k * 1.9)
        r = 1.6 + 0.9 * (1 - abs(u - 0.5) * 2) + 0.4 * bob
        cv.circle(x, gy - 1.0 - r * 0.6 - 0.8 * max(0.0, bob), r, FOAM, shade="soft", name="foam")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    gx, gy = cv.gx, cv.gy  # the waterline centre
    _far_coil(cv, gx, gy, p)
    kp = _keypoints(p)
    world = [(gx + dx, gy - h) for dx, h in kp]
    pts = hb.resample(hb.catmull(world, 8), 1.4)
    _body(cv, pts)
    Hb = world[-1]
    mouth, wroot, jaw_front = _head(cv, (Hb[0] - 1.0, Hb[1] + 1.0), p.ang, p)
    _whiskers(cv, wroot, p.ang, p, water_y=gy)
    # the river hides everything below its surface
    cv.rect(0, gy + 1, cv.w, cv.h - gy - 1, SCALE, erase=True)
    base_x = pts[0][0] if pts[0][1] <= gy else next((q[0] for q in pts if q[1] <= gy + 0.5), gx)
    fx = cv.layer(above=True, outline=True)
    back = cv.layer(above=False, outline=True)
    hb.ripple(back, gx - 4, gy + 0.5, 24.0, WATER)
    if p.sink < 100:
        _foam(fx, base_x, gy + 0.5, p.foam + frame * 0.13, w=13.0 + p.sink * 0.1)
        _foam(fx, gx - 33 + 3 * math.sin(p.hump), gy + 0.5, p.foam + 0.4, w=9.0)
    if p.orb is not None:  # the river spirals up into a swelling orb between the jaws
        o = p.orb
        orb_c = (mouth[0] + 3.0, mouth[1] - 1.0)
        R = 2.0 + 4.5 * o
        fx.circle(orb_c[0], orb_c[1], R, WATER, shade="soft", name="orb")
        fx.circle(orb_c[0] - R * 0.3, orb_c[1] - R * 0.3, max(0.8, R * 0.35), FOAM, shade="flatlight", name="orb")
        for k in range(int(3 + 5 * o)):  # droplets streaming up from the river toward the orb
            u = ((k * 0.17 + frame * 0.11) % 1.0)
            sx = base_x + 18 + 6 * math.sin(u * 7 + k)
            sy = gy - 2
            q = px.lerp_pt((sx, sy), orb_c, u)
            q = (q[0] + 5 * math.sin(u * 9 + k) * (1 - u), q[1])
            fx.circle(q[0], q[1], 1.0, WATER, shade="soft", name="drop")
        ring = cv.layer(above=False, outline=False)
        px.glow_ring(ring, orb_c[0], orb_c[1], R + 3.0, px.QI_CYAN, thickness=1.0)
    if p.splash is not None:
        px.splash(fx, base_x + 8, gy + 0.5, p.splash, size=1.8)
        px.splash(fx, base_x - 10, gy + 0.5, min(1.0, p.splash + 0.2), size=1.3)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, jaw_front[0] - 1, jaw_front[1], size=5)
    if p.sink >= 100:  # only rings and bubbles remain
        for k, (dx, r) in enumerate(((-2.0, 1.4), (4.0, 1.0), (1.0, 0.8))):
            fx.circle(base_x + dx, gy - 3 - k * 3, r, FOAM, shade="soft", name="bubble")
