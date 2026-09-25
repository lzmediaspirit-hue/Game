"""Dune worm - a giant burrowing sand worm of the Sunscar Desert (the Worm Sea), Azure
Expanse (Earth).

View: side, facing right (cell 256, 128 art px).  It travels hidden under the sand and is
only seen when it surfaces to strike, so every frame shows it rising out of a sand mound
at the anchor (the mound is part of the body sprite and carries the ground contact).
Idle: the front third stands ~62 art px out of the mound (~1.25x the player); reared up
for the windup it stands ~98 art px (about twice the player).
Parts, back to front: back sand mound, the body tube (one spline: under the sand -> mouth)
built from overlapping dusky-ochre armour rings (each ring flares to a lip that overlaps
the next one toward the tail, dark sand crust packed in the seams, a raised light edge on
each lip), the pale ridged underbelly along one side, a row of tiny glassy sense pits on
the head plates (no eyes), the round lamprey mouth (armoured lip collar, deep red maw,
a ring of clear desert-glass teeth with a cyan glint, a smaller inner ring, dark throat),
then the front rim of the mound.  FX (own layers): sand pouring off the body, sand
bursts / grains / dust, the sand explosion of the strike, chipped plate shards.
Walk (rarely seen): the mouth end breaks the sand in front and the body loops out behind
it in two armoured arches that roll backward and sink while a new one rises.
Windup: rears up tall, mouth gaping to show the glass teeth, sand bursting around the
mound, the sense pits flare cyan (held).  Attack: lunges forward and down onto the target,
hit on frame 1 with a sand explosion.  Hurt: recoils, plates chip, sand bursts.
Death: topples forward, the rings go slack and it sinks back into the sand, leaving a
collapsing mound that fades.
"""
import math

import helpers_batch_b as hb
import pixel as px

SPEC = {
    "id": "dune_worm",
    "cell": 256,
    "anchor": [128, 224],
    "flying": False,
    "hit_frame": 1,
}

# ---- palette: dusky ochre armour, pale sand belly, dark sand crust, desert glass, red maw --
ARMOUR = px.material("dw_armour", "#f0cf8a", "#b9843f", "#7f5344", "#4d3246", outline="#1a0e17",
                     thresholds=(0.9, 0.55, 0.18))
BELLY = px.material("dw_belly", "#fff6dc", "#f2dcae", "#d4b28c", "#a8856f", outline="#1a0e17")
CRUST = px.material("dw_crust", "#8e6c54", "#664a44", "#4a3442", "#2e2032", outline="#120a12")
SAND = px.material("dw_sand", "#fff2c8", "#eccb8c", "#c69c6c", "#8e6a5c", outline="#3b2a2a",
                   thresholds=(0.86, 0.5, 0.18))
GLASS = px.material("dw_glass", "#ffffff", "#e2f6f3", "#9ed4d9", "#5a98ad", outline="#0e1b26")
MAW = px.material("dw_maw", "#e2646e", "#a8283e", "#6a1432", "#3a0822", outline="#14040c")
CYAN = px.rgb("#62e4f0")  # glass glint accent

# ---- body shapes ------------------------------------------------------------------------
# Spine keypoints (dx from the anchor, height above the ground), from under the sand to the
# mouth.  Every shape has the same count so poses can blend between them.
SHAPES = {
    "idle": ((-6, -16), (-6, 0), (-7, 16), (-4, 32), (4, 44), (15, 50), (25, 48)),
    "rear": ((-6, -16), (-6, 0), (-10, 20), (-16, 42), (-16, 63), (-8, 79), (5, 86)),
    "lunge": ((-6, -16), (-6, 0), (-5, 22), (0, 44), (12, 60), (27, 62), (39, 52)),
    "hit": ((-6, -16), (-6, 0), (-5, 22), (4, 40), (18, 47), (28, 38), (35, 19)),
    "hit2": ((-6, -16), (-6, 0), (-5, 21), (4, 37), (18, 42), (29, 30), (34, 7)),
    "hurt": ((-6, -16), (-6, 0), (-9, 16), (-12, 32), (-11, 46), (-4, 56), (4, 59)),
    "rear_pain": ((-6, -16), (-6, 0), (-9, 18), (-13, 36), (-12, 52), (-6, 64), (1, 70)),
    "topple": ((-6, -16), (-6, 0), (-2, 18), (8, 30), (22, 34), (34, 26), (42, 13)),
    "slump": ((-6, -16), (-6, 0), (0, 10), (12, 14), (26, 13), (38, 9), (46, 4)),
}

# ---- poses --------------------------------------------------------------------------------
# shape / to / t   body shape, optionally blended toward ``to`` by ``t``
# sway, ph         idle sway amplitude (px at the head) and phase
# mouth            0 (puckered) .. 1 (gaping)       glow  sense pits: 0 dim, 1 lit, 2 flaring
# sink             px the body has sunk into the sand   mound  mound size 0..1   slack  0..1
# burst            sand bursting around the mound (life)   blast  sand explosion at the mouth (life),
#                  blast_dx / blast_gap / blast_size  its offset from the mouth, mouth gap, scale
# pour             sand streaming off the overhanging rings
# chips            chipped plate shards (life)   crack  cracked plates 0..2   hit  impact spark
# walk             humps-through-the-sand walk cycle        fade  whole-frame opacity
DEFAULTS = dict(shape="idle", to=None, t=0.0, sway=0.0, ph=0.0, mouth=0.18, glow=0, sink=0.0, mound=1.0,
                slack=0.0, burst=None, blast=None, blast_size=1.0, blast_dx=3.0, blast_gap=6.0, chips=None,
                crack=0, hit=False, walk=False, fade=1.0, pour=True)

POSE = px.poses(DEFAULTS, {
    "idle": [  # the front third sways over the mound, sand streaming off the rings
        dict(ph=0.0, sway=2.0, mouth=0.3),
        dict(ph=1.57, sway=2.0, mouth=0.38),
        dict(ph=3.14, sway=2.0, mouth=0.3),
        dict(ph=4.71, sway=2.0, mouth=0.22),
    ],
    "walk": [dict(walk=True) for _ in range(6)],
    "windup": [  # rears up tall, the mouth gapes, sand bursts around the mound - held
        dict(to="rear", t=0.45, mouth=0.5, burst=0.2, glow=1),
        dict(to="rear", t=0.85, mouth=0.85, burst=0.55, glow=2),
        dict(shape="rear", mouth=1.0, burst=0.85, glow=2),
    ],
    "attack": [  # lunges forward and down; hit on frame 1 with a sand explosion
        dict(shape="lunge", mouth=1.0, glow=2, pour=False),
        dict(shape="hit", mouth=0.95, blast=0.3, blast_gap=22.0, hit=True, glow=2, pour=False),
        dict(shape="hit2", mouth=0.5, blast=0.62, blast_gap=10.0, glow=1, pour=False),
        dict(shape="idle", to="hit", t=0.35, mouth=0.3, blast=0.92),
    ],
    "hurt": [
        dict(shape="hurt", mouth=0.75, chips=0.3, crack=1, burst=0.25, pour=False),
        dict(to="hurt", t=0.5, mouth=0.45, chips=0.75, crack=1, burst=0.6),
    ],
    "death": [  # rears in pain, topples, the rings go slack, sinks; the mound collapses
        dict(shape="rear_pain", mouth=0.9, crack=1, slack=0.2, chips=0.4, pour=False),
        dict(shape="topple", mouth=0.6, crack=2, slack=0.5, blast=0.3, blast_size=0.8, pour=False),
        dict(shape="slump", mouth=0.3, crack=2, slack=1.0, blast=0.7, blast_size=0.8, mound=0.85),
        dict(shape="slump", sink=11, mouth=0.25, crack=2, slack=1.0, mound=0.6, fade=0.6),
        dict(shape="slump", sink=30, mouth=0.2, slack=1.0, mound=0.35, fade=0.3),
    ],
})

PLATE = 8.0  # armour ring length along the spine (art px)


# ---- geometry helpers ----------------------------------------------------------------------
def _keypoints(p):
    base = SHAPES[p.shape]
    if p.to:
        tgt = SHAPES[p.to]
        base = [(a[0] + (b[0] - a[0]) * p.t, a[1] + (b[1] - a[1]) * p.t) for a, b in zip(base, tgt)]
    n = len(base)
    out = []
    for i, (dx, h) in enumerate(base):
        u = max(0.0, (i - 1) / (n - 2))
        dx += p.sway * math.sin(p.ph + i * 0.7) * u
        h += p.sway * 0.35 * math.cos(p.ph) * u
        out.append((dx, h - p.sink))
    return out


def _side_normals(pts, smooth=3):
    """Unit normals on one fixed side of the path (the belly side): (-dy, dx) walking from
    the tail to the mouth.  Smoothed so the belly never flips."""
    n = len(pts)
    raw = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        raw.append((-dy / ln, dx / ln))
    out = []
    for i in range(n):
        sx = sum(raw[j][0] for j in range(max(0, i - smooth), min(n, i + smooth + 1)))
        sy = sum(raw[j][1] for j in range(max(0, i - smooth), min(n, i + smooth + 1)))
        ln = math.hypot(sx, sy) or 1.0
        out.append((sx / ln, sy / ln))
    return out


def _arc_from_tip(pts):
    s = [0.0] * len(pts)
    for i in range(len(pts) - 2, -1, -1):
        s[i] = s[i + 1] + math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
    return s


def _radii(s_arr, slack, off=0.0, rscale=1.0):
    """Tube radius per sample: thick body, a little slimmer at the head, each armour ring
    flaring to an overlapping lip toward the tail (the seams step in)."""
    out, phase = [], []
    lo = 0.86 - 0.06 * slack
    for s in s_arr:
        R = 10.6 + 1.6 * min(1.0, s / 55.0)
        if s < 3.0:  # mouth collar
            q = 1.0
        else:
            q = ((s - 3.0 + off) % PLATE) / PLATE
        phase.append(q)
        out.append(R * rscale * (lo + (1.03 - lo) * q))
    return out, phase


def _frame_of(pts, i, k=2):
    n = len(pts)
    a, b = pts[max(0, i - k)], pts[min(n - 1, i + k)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    return (dx / ln, dy / ln)


# ---- parts -------------------------------------------------------------------------------
def _tube(cv, pts, p, off=0.0, pits=True, rscale=1.0, sep=False):
    """The armoured body: tube, ring seams packed with crust, lip highlights, ridged belly,
    sense pits.  Returns (radii, normals, arc)."""
    s_arr = _arc_from_tip(pts)
    radii, q = _radii(s_arr, p.slack, off, rscale)
    nrm = _side_normals(pts)
    n = len(pts)
    cv.limb(pts, radii, ARMOUR, name="body", sep=sep)
    seam_w = 0.8 + 0.5 * p.slack

    def across(c, k0, k1, R, nv):
        return ((math.floor(c[0] + nv[0] * R * k0), math.floor(c[1] + nv[1] * R * k0)),
                (math.floor(c[0] + nv[0] * R * k1), math.floor(c[1] + nv[1] * R * k1)))

    k = 0
    for i in range(2, n - 1):
        if not q[i] < q[i + 1] - 0.3:  # a ring boundary sits between i (tail side) and i+1
            continue
        t = _frame_of(pts, i)
        R = radii[i + 1]
        c = pts[i]
        nv = nrm[i]
        # dark sand crust packed into the seam
        a = (c[0] - nv[0] * R * 1.2, c[1] - nv[1] * R * 1.2)
        b = (c[0] + nv[0] * R * 1.2, c[1] + nv[1] * R * 1.2)
        cv.limb([a, b], seam_w, CRUST, decal=True, clip="body", name="body")
        # the next ring tucks under this lip: one row of shade on its front edge
        sh = (c[0] - t[0] * (1.4 + seam_w), c[1] - t[1] * (1.4 + seam_w))
        cv.line(*across(sh, -1.1, 0.45, R, nv), ARMOUR.step(1), band=None, decal=True, clip="body", name="body")
        # raised lip catching the light, just head-ward of the seam
        lip = (pts[i + 1][0] + t[0] * 0.7, pts[i + 1][1] + t[1] * 0.7)
        cv.line(*across(lip, -1.1, 0.3, R, nv), ARMOUR.step(-1), band=None, decal=True, clip="body", name="body")
        if p.crack and (k % 2 == 0 or p.crack >= 2) and s_arr[i] > 8:
            m = (c[0] - nv[0] * R * 0.55 + t[0] * 3.0, c[1] - nv[1] * R * 0.55 + t[1] * 3.0)
            e = (m[0] + t[0] * 2.5 - nv[0] * 2.5, m[1] + t[1] * 2.5 - nv[1] * 2.5)
            st = (c[0] - nv[0] * R * 0.3, c[1] - nv[1] * R * 0.3)
            for u, v in ((st, m), (m, e)):
                cv.line((math.floor(u[0]), math.floor(u[1])), (math.floor(v[0]), math.floor(v[1])), CRUST.step(1),
                        band=None, decal=True, clip="body", name="body")
        k += 1
    # pale ridged underbelly along the belly side
    belly = hb.offset(pts, nrm, radii, 0.7)
    cv.limb(belly, [r * 0.34 for r in radii], BELLY, decal=True, clip="body", name="belly")
    for i in range(2, n - 3):
        if int((s_arr[i] + off) / 2.7) == int((s_arr[i + 1] + off) / 2.7) or s_arr[i] < 4:
            continue
        cv.line(*across(pts[i], 0.4, 1.05, radii[i], nrm[i]), BELLY.step(1), band=None, decal=True, clip="belly",
                name="belly")
    if pits:
        _pits(cv, pts, nrm, radii, s_arr, p.glow)
    return radii, nrm, s_arr


def _pits(cv, pts, nrm, radii, s_arr, glow):
    """Row of tiny glassy sense pits along the dorsal side of the head plates."""
    for s0 in (6.0, 9.5, 13.0, 16.5):
        i = min(range(len(pts)), key=lambda j: abs(s_arr[j] - s0))
        c = hb.offset([pts[i]], [nrm[i]], [radii[i]], -0.52)[0]
        x, y = math.floor(c[0]), math.floor(c[1])
        if not (0 <= y < cv.h and 0 <= x < cv.w and cv.filled[y, x]):
            continue
        top = CYAN if glow >= 2 else GLASS.light
        cv.pixel(x, y, top, name="eye", clip="body")
        cv.pixel(x, y + 1, CRUST.deep if glow == 0 else GLASS.deep, name="eye", clip="body")
        if glow >= 1:
            cv.pixel(x + 1, y, GLASS.shadow if glow == 1 else GLASS.light, name="eye", clip="body")


def _mouth(cv, tip, ang, R, open_):
    """Round lamprey mouth at the tip, turned a little toward the viewer: armoured lip
    collar, deep red maw, a ring of desert-glass teeth, a smaller inner ring, dark throat."""
    with cv.xform(px.translate(tip[0], tip[1]), px.rotate(ang)):
        rx = 2.4 + 4.6 * open_
        ry = R * (0.74 + 0.24 * open_)
        cx = -0.6 + rx * 0.35
        cv.ellipse(cx, 0.0, rx, ry, ARMOUR, name="lip", sep="deep")
        irx, iry = rx - 1.7, ry - 2.1
        if irx < 0.6:
            return
        mcx = cx + 0.5
        m, nx, ny, nz = cv.geom_ellipse(mcx, 0.0, irx, iry)
        cv.fill(m, MAW, normals=(-nx, -ny, nz), shade="soft", name="maw")  # concave: lit on the far wall
        cv.ellipse(mcx + irx * 0.2, 0.0, max(0.6, irx * 0.42), max(0.8, iry * 0.4), MAW, shade=3, name="maw")
        # outer ring of glass teeth pointing into the throat
        big = open_ > 0.4

        def ring(scale, count, length, width, rot, mat_shade):
            for k in range(count):
                th = 2 * math.pi * (k + rot) / count
                bx, by = mcx + irx * scale * math.cos(th), iry * scale * math.sin(th)
                tx_, ty_ = -irx * math.sin(th), iry * math.cos(th)  # ellipse tangent
                tl = math.hypot(tx_, ty_) or 1.0
                tx_, ty_ = tx_ / tl * width, ty_ / tl * width
                tip_ = (bx + (mcx - bx) * length, by * (1 - length))
                cv.polygon([(bx - tx_, by - ty_), (bx + tx_, by + ty_), tip_], GLASS, shade=mat_shade, name="tooth")

        ring(1.0, 9 if big else 7, 0.5 if big else 0.6, 1.45 if big else 0.95, 0.5, "soft")
        if open_ > 0.55:  # smaller inner ring
            ring(0.56, 6, 0.55, 1.0, 0.0, "two")
        glint = cv.tp((mcx - irx * 0.55, -iry * 0.62))
    cv.pixel(math.floor(glint[0]), math.floor(glint[1]), CYAN, name="tooth")


def _mound(cv, x, h, rx, name="mound", sep="deep", texture=True):
    """Sand heap resting on the ground: a flat-bottomed dome with wind ripples."""
    if h <= 0.4:
        return
    g = cv.ground
    cut = cv.mask_polygon([(x - rx - 3, g + 0.5), (x + rx + 3, g + 0.5), (x + rx + 3, g + 12), (x - rx - 3, g + 12)])
    cv.ellipse(x, g + 0.5, rx, h, SAND, name=name, minus=cut, sep=sep)
    if texture and h > 2.5:
        for k, (fx_, fy) in enumerate(((-0.55, 0.45), (0.2, 0.62), (0.55, 0.3), (-0.2, 0.2))):
            cx, cy = x + fx_ * rx, g + 0.5 - fy * h
            w = max(1.5, rx * 0.14)
            cv.line((math.floor(cx - w), math.floor(cy)), (math.floor(cx + w), math.floor(cy) - (k % 2)), SAND.step(1),
                    band=None, decal=True, clip=name, name=name)


# ---- FX ----------------------------------------------------------------------------------
def _clip_fx(fx):
    """FX never sink below the sand and never break the 2 px frame margin."""
    m = fx.filled & ((fx.Y > fx.ground + 0.5) | (fx.X < 3) | (fx.X > fx.w - 3) | (fx.Y < 3))
    if m.any():
        fx.fill(m, px.flat("#000000"), erase=True)


def _pour(fx, cv, pts, nrm, radii, s_arr, frame, sources=(8.0, 17.0, 27.0)):
    """Sand pouring off the overhanging rings: a thin stream from under a lip that breaks
    up into falling grain clusters (they travel down one spacing per 4 frames: loops)."""
    for k, s0 in enumerate(sources):
        i = min(range(len(pts)), key=lambda j: abs(s_arr[j] - s0))
        n = nrm[i]
        if n[1] < 0.45:
            continue
        x = math.floor(pts[i][0] + n[0] * radii[i] * 0.45)
        y = int(math.floor(pts[i][1]))
        while 0 <= y < cv.h and cv.filled[y, x]:
            y += 1
        y0, y1 = y, y
        while y1 < cv.gy - 2 and not cv.filled[y1 + 1, x]:
            y1 += 1
        span = y1 - y0
        if span < 4:
            continue
        L = min(span, 4 + ((k * 2 + frame) % 3) * 2)  # the unbroken stream flickers in length
        fx.pixels([(x, yy) for yy in range(y0, y0 + L)], SAND.light, name="pour")
        fx.pixels([(x + 1, yy) for yy in range(y0, y0 + max(2, L // 2))], SAND.shadow, name="pour")
        rest = span - L - 3
        if rest < 3:
            continue
        for j in range(3):
            d = (j * rest / 3.0 + frame * rest / 12.0 + k * 1.7) % rest
            yy = y0 + L + 2 + int(d)
            xx = x - (1 if (j + k) % 3 == 1 else 0)
            fx.pixels([(xx, yy), (xx, min(y1, yy + 1))], SAND.light if j % 2 == 0 else SAND.base, name="pour")


def _plume(fx, base, ang, length, t, r0, sag=0.5, name="sand", seed=0):
    """Sand plume thrown up from ``base`` at ``ang`` degrees along a ballistic arc: a
    tapering column of overlapping clumps that breaks into loose clumps at the top."""
    grow = min(1.0, 0.3 + t * 1.2)
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def at(u, wob):
        return (base[0] + c * length * u - s * wob,
                base[1] - s * length * u + length * sag * u * u * (0.3 + 0.7 * t) - c * wob)

    col = 0.6
    for j in range(5):  # the column
        u = (j + 1) / 5.0 * col * grow
        x, y = at(u, (px.hash01(seed, j, 11) - 0.5) * r0 * 0.5)
        fx.circle(x, y, max(0.9, r0 * (1.0 - 0.6 * u)), SAND, shade="soft", name=name)
    for j in range(2):  # loose clumps flying off its top
        u = (col + 0.2 * (j + 1)) * grow
        x, y = at(u, (px.hash01(seed, j, 17) - 0.5) * r0 * 1.2)
        fx.circle(x, y, max(0.8, r0 * (0.42 - 0.12 * j)), SAND, shade="soft", name=name)


def _burst(fx, x, t, size=1.0, seed=0):
    """Sand bursting up around the mound: geysers off both flanks, grains, dust."""
    g = fx.gy - 1
    grow = 0.4 + 0.6 * min(1.0, t * 1.3)
    for k, (dx, a, ln) in enumerate(((-19, 132, 17), (-14, 112, 24), (14, 70, 25), (20, 50, 18))):
        _plume(fx, (x + dx * size, g - 2.0), a, ln * size * grow, t, 2.4 * size, sag=0.12, seed=seed * 5 + k)
    hb.spray(fx, x - 15 * size, g - 3, t, size=1.0 * size, spread=0.9, mat=SAND, n=4, seed=seed)
    hb.spray(fx, x + 15 * size, g - 3, t, size=1.0 * size, spread=0.9, mat=SAND, n=4, seed=seed + 7)
    px.dust(fx, x - 22 * size, g, t, size=1.0 * size, direction=-1, mat=SAND)
    px.dust(fx, x + 22 * size, g, t, size=1.0 * size, direction=1, mat=SAND)
    _clip_fx(fx)


def _blast(fx, x, t, size=1.0, seed=3, gap=6.0):
    """Sand explosion where the strike lands: two fans of plumes (ahead of the mouth and
    behind it, ``gap`` apart so the mouth stays readable) that rise then rain back, grains,
    and a dust bank rolling out both ways."""
    g = fx.gy - 1
    fall = max(0.0, t - 0.5) * 2.0
    grow = min(1.0, 0.5 + t * 1.5) * (1.0 - 0.45 * fall)
    tt = 0.3 + 0.7 * t
    fans = [(x + gap / 2 + j * 2.6 * size, a, ln) for j, (a, ln) in enumerate(((86, 34), (68, 32), (48, 24), (28, 15)))]
    fans += [(x - gap / 2 - j * 2.6 * size, a, ln) for j, (a, ln) in enumerate(((96, 30), (116, 29), (138, 22),
                                                                                  (158, 14)))]
    for k, (bx, a, ln) in enumerate(fans):
        L = ln * size * grow
        c = math.cos(math.radians(a))
        if c > 0.05:  # keep the forward fan inside the frame
            L = min(L, (fx.w - 7 - bx) / c)
        if L > 2:
            _plume(fx, (bx, g - 2.0), a, L, tt, 3.3 * size, sag=0.2, name="blast", seed=seed * 7 + k)
    bank = min(1.0, 0.4 + t) * (1.0 - 0.35 * fall)
    x0, x1 = x - gap / 2 - 9 * size, x + gap / 2 + 8 * size
    for k in range(6):  # low bank of churned sand joining the plume roots
        bx = x0 + (x1 - x0) * k / 5.0
        r = size * (2.6 + 1.2 * px.hash01(seed, k, 5)) * bank
        fx.circle(bx, g - r + 0.5, r, SAND, shade="soft", name="blast")
    hb.spray(fx, x - gap / 2, g - 6, t, size=1.4 * size, spread=1.1, mat=SAND, n=5, seed=seed)
    px.dust(fx, x - gap / 2 - 12 * size, g, t, size=1.7 * size, direction=-1, mat=SAND)
    px.dust(fx, x + gap / 2 + 6 * size, g, t, size=1.2 * size, direction=1, mat=SAND)
    _clip_fx(fx)


def _chips(fx, pts, nrm, radii, s_arr, t):
    """Chipped plate shards flying off the struck front rings."""
    for k, s0 in enumerate((10.0, 20.0, 31.0)):
        i = min(range(len(pts)), key=lambda j: abs(s_arr[j] - s0))
        c = hb.offset([pts[i]], [nrm[i]], [radii[i]], -0.9)[0]
        vx, vy = -3.0 - 1.5 * k, -5.0 + k
        x = c[0] + vx * t * 2.0
        y = c[1] + (vy * t * 2.0 + 6.0 * t * t)
        r = 2.4 - 0.35 * k
        a = 40 * k + 200 * t
        tri = [px.polar((x, y), a, r * 1.4), px.polar((x, y), a + 130, r), px.polar((x, y), a + 230, r * 1.1)]
        fx.polygon(tri, ARMOUR, shade="two", name="chip")
    _clip_fx(fx)


# ---- walk: humps through the sand ----------------------------------------------------------
def _smooth(e0, e1, x):
    u = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return u * u * (3 - 2 * u)


def _walk(cv, frame):
    """Rarely seen: swimming under the sand.  The mouth end breaks the surface in front and
    the body loops out behind it in arches (thinner toward the tail) that roll backward and
    sink while a new one rises: one arch spacing per 6-frame cycle."""
    gx, g = cv.gx, cv.ground
    ph = frame / 6.0
    p = POSE("idle", 0)
    off = frame * PLATE / 3.0
    fx = cv.layer(above=True, outline=True)
    heaps = []
    for u in (ph + 1.0, ph):  # back arch first
        e = _smooth(0.0, 0.38, u) * (1.0 - _smooth(1.15, 1.8, u))
        if e <= 0.02:
            continue
        uu = min(u, 1.3)
        r, R = 11.5 - 1.5 * uu, 9.8 - 1.5 * uu
        cx = gx + 10.0 - 32.0 * u
        cy = g + 0.5 - 2.5 * e + (1.0 - e) * (r + R + 3.0)
        path = [(cx - r, cy + 14.0)] + [(cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))
                                        for a in range(180, -1, -6)] + [(cx + r, cy + 14.0)]
        pts = hb.resample(path, 1.0)
        _tube(cv, pts, p, off=off, pits=False, rscale=R / 11.0, sep="deep")
        depth = max(0.0, cy - (g + 0.5))
        half = math.sqrt(max(0.0, (r + R) ** 2 - depth * depth))
        heaps.append((cx - half + 3.0, e))
        heaps.append((cx + half - 3.0, e))
        if u < 0.6:  # the rising arch throws sand off both legs
            hb.spray(fx, cx - half + 1, cv.gy - 1, u / 0.6, size=0.8, spread=0.8, mat=SAND, n=3, seed=int(u * 12))
            hb.spray(fx, cx + half - 1, cv.gy - 1, u / 0.6, size=0.8, spread=0.8, mat=SAND, n=3, seed=int(u * 12) + 5)
    # the mouth end pushing up through the sand in front
    bob = math.sin(2 * math.pi * ph)
    head = hb.resample(hb.catmull([(gx + 19.0, g + 12.0), (gx + 25.0, g - 1.0), (gx + 34.0, g - 9.0 - bob),
                                   (gx + 39.0, g - 11.0 - bob)], 8), 1.0)
    radii, nrm, s_arr = _tube(cv, head, p, off=off, sep="deep")
    t = _frame_of(head, len(head) - 1, 3)
    _mouth(cv, head[-1], math.degrees(math.atan2(-t[1], t[0])), radii[-1], 0.28 + 0.06 * bob)
    m = cv.filled & (cv.Y > g + 0.5)
    cv.fill(m, px.flat("#000000"), erase=True)
    for x, e in heaps:
        _mound(cv, x, 3.6 * e, 6.5, texture=False)
    _mound(cv, gx + 26.0, 6.0, 12.0)  # bow wave around the surfacing mouth end
    _clip_fx(fx)


# ---- main --------------------------------------------------------------------------------
def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    gx, g = cv.gx, cv.ground
    if p.walk:
        _walk(cv, frame)
        return
    kp = _keypoints(p)
    world = [(gx + dx, g + 0.5 - h) for dx, h in kp]
    pts = hb.resample(hb.catmull(world, 10), 1.0)
    base_x = gx + kp[1][0]
    # back of the mound (behind the body)
    _mound(cv, gx - 2, 5.0 * p.mound, 22.0 * (0.6 + 0.4 * p.mound), name="mound_back", sep=False, texture=False)
    radii, nrm, s_arr = _tube(cv, pts, p)
    tip = pts[-1]
    t = _frame_of(pts, len(pts) - 1, 3)
    ang = math.degrees(math.atan2(-t[1], t[0]))
    _mouth(cv, tip, ang, radii[-1], p.mouth)
    # everything under the sand is hidden
    m = cv.filled & (cv.Y > g + 0.5)
    cv.fill(m, px.flat("#000000"), erase=True)
    # front rim of the mound, in front of the body
    _mound(cv, base_x + 1.0, 8.0 * p.mound, 17.0 * (0.7 + 0.3 * p.mound))
    if p.pour and p.sink < 20:
        pour = cv.layer(above=True, outline=False)
        _pour(pour, cv, pts, nrm, radii, s_arr, frame)
    if p.burst is not None:
        fx = cv.layer(above=True, outline=True)
        _burst(fx, base_x + 1.0, p.burst, size=1.0, seed=frame)
    if p.chips is not None:
        fx = cv.layer(above=True, outline=True)
        _chips(fx, pts, nrm, radii, s_arr, p.chips)
    if p.blast is not None:
        fx = cv.layer(above=True, outline=True)
        _blast(fx, min(tip[0] + p.blast_dx, cv.w - 26), p.blast, size=p.blast_size, seed=frame, gap=p.blast_gap)
    if p.hit:
        top = cv.layer(above=True, outline=False)
        px.impact(top, tip[0] + 9, tip[1] - 1, size=5, color=CYAN, core=GLASS.light)
