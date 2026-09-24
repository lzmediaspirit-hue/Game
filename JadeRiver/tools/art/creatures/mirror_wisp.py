"""Mirror wisp - a floating ring of mirror-bright crystal shards around a single eye (Soul).

View: side/front, facing right (the eye looks right).  ~30 art px tall on a 64 px art
canvas (cell 128).  Flying: the anchor is the eye.
Parts, back to front: back shards (darker, behind the eye), a faint violet halo, the eye
(dark socket ring, pale sclera, violet iris, pupil, glint), front shards.  Each shard is
a kite split into a lit and a shaded facet with a white mirror-glint edge.
Idle/walk: the shards orbit and bob; windup: the shards swing round and align into a
lens in front of the eye while it glows; attack: a soul-flash burst (hit on frame 1);
death: the eye cracks and everything shatters outward and fades.
"""
import math

import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "mirror_wisp",
    "cell": 128,
    "anchor": [64, 64],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette: pale violet / white mirror facets, deep violet shadows ------------------------
SHARD = px.material("mirror_shard", "#ffffff", "#ddd3f6", "#a58fd8", "#5f4b98", outline="#150f29")
SHARD_B = px.material("mirror_shard_back", "#c9bdec", "#9d88d0", "#7560ae", "#4a3a7c", outline="#150f29")
SOCKET = px.material("wisp_socket", "#8e76cc", "#5d489a", "#3e2f6e", "#281e4a", outline="#120c22")
SCLERA = px.material("wisp_sclera", "#ffffff", "#f1ecfb", "#cfc3ec", "#a592d4", outline="#120c22")
IRIS = px.rgb("#9b78d1")
IRIS_HI = px.rgb("#d9c6f5")
PUPIL = px.rgb("#1d1238")
FLASH = px.rgb("#f3ecff")
FLASH_V = px.rgb("#b69ae6")

N_SHARDS = 6

# ---- poses ------------------------------------------------------------------------------------
# bx, by   offset of the eye       spin  orbit phase (deg)     r  orbit radius scale
# align    0..1 shards swing into a lens in front of the eye (windup)
# look     pupil offset (dx, dy)   eye   open|glow|squeeze|dead|crack
# burst    soul-flash life (None = off)   scatter  shards flung outward (hurt / death)
# shatter  0..1 death: eye breaks into fragments       fade  opacity
DEFAULTS = dict(bx=0, by=0, spin=0.0, r=1.0, align=0.0, look=(1, 0), eye="open", burst=None, scatter=0.0,
                shatter=0.0, fade=1.0, halo=0)

POSE = px.poses(DEFAULTS, {
    "idle": [
        dict(spin=0, by=0, look=(1, 0)),
        dict(spin=12, by=-1, look=(1, 0)),
        dict(spin=24, by=-1, look=(0, 0)),
        dict(spin=36, by=0, look=(1, 1)),
    ],
    "walk": [  # drifts forward, the ring spins faster
        dict(spin=0, by=0, bx=0),
        dict(spin=10, by=-1, bx=1),
        dict(spin=20, by=-1, bx=1),
        dict(spin=30, by=0, bx=1),
        dict(spin=40, by=1, bx=0),
        dict(spin=50, by=1, bx=0),
    ],
    "windup": [  # the facets swing round into a lens in front of the eye, which glows - held
        dict(spin=20, align=0.35, eye="glow", look=(1, 0), halo=1),
        dict(spin=30, align=0.8, eye="glow", look=(1, 0), halo=2, bx=-1),
        dict(spin=34, align=1.0, eye="glow", look=(1, 0), halo=3, bx=-2),
    ],
    "attack": [  # soul flash: the lens fires a burst; hit on frame 1
        dict(spin=34, align=1.0, eye="glow", look=(1, 0), burst=0.2, bx=-2, halo=3),
        dict(spin=36, align=0.9, eye="glow", look=(1, 0), burst=0.55, bx=-3, r=1.05, halo=2),
        dict(spin=40, align=0.5, eye="open", look=(1, 0), burst=0.9, bx=-2),
        dict(spin=46, align=0.1, eye="open", look=(1, 0), bx=-1),
    ],
    "hurt": [
        dict(spin=10, eye="squeeze", scatter=0.35, bx=-3, by=-1),
        dict(spin=14, eye="squeeze", scatter=0.15, bx=-2),
    ],
    "death": [  # the eye cracks, then everything shatters outward and fades
        dict(spin=10, eye="crack", scatter=0.3, bx=-3, by=-1),
        dict(spin=20, eye="crack", scatter=0.8, shatter=0.3, bx=-3, by=1),
        dict(spin=30, eye="dead", scatter=1.1, shatter=0.6, bx=-2, by=3),
        dict(spin=40, eye="dead", scatter=1.3, shatter=0.85, bx=-2, by=3, fade=0.6),
        dict(spin=50, eye="dead", scatter=1.45, shatter=1.0, bx=-2, by=4, fade=0.3),
    ],
})


def _shard(cv, C, a, r_in, r_out, width, twist, mat, name):
    """A kite-shaped crystal shard pointing away from C along ``a``; the facet facing
    the upper-left light is lit, the other shaded, with a white glint edge."""
    inner = px.polar(C, a, r_in)
    outer = px.polar(C, a, r_out)
    mid = px.polar(C, a, r_in + (r_out - r_in) * 0.42)
    ax = a + twist
    s1 = px.polar(mid, ax + 90, width)
    s2 = px.polar(mid, ax - 90, width)
    # which side faces the light (upper-left = 135 deg)?
    def facing(deg):
        return math.cos(math.radians(deg - 135))
    lit, dark = (s1, s2) if facing(ax + 90) >= facing(ax - 90) else (s2, s1)
    cv.polygon([outer, lit, inner], mat, shade=0 if mat is SHARD else 1, name=name)
    cv.polygon([outer, dark, inner], mat, shade=2 if mat is SHARD else 3, name=name)
    if mat is SHARD:  # mirror glint along the lit edge
        q0, q1 = px.lerp_pt(outer, lit, 0.15), px.lerp_pt(outer, lit, 0.7)
        cv.line((math.floor(q0[0]), math.floor(q0[1])), (math.floor(q1[0]), math.floor(q1[1])), px.GLINT,
                decal=True, name=name)
    return outer


def _layout(p, C):
    """(angle, r_in, r_out, width, twist, depth) per shard, blending orbit -> lens."""
    out = []
    for i in range(N_SHARDS):
        base = p.spin + i * 360.0 / N_SHARDS + (9 if i % 2 else 0)
        rs = p.r * (1.0 + p.scatter * (0.55 + 0.3 * px.hash01(i, 3)))
        bob = 0.8 * math.sin(math.radians(p.spin * 6 + i * 70))
        r_in, r_out = 7.2 * rs + bob, (15.5 - 1.6 * (i % 3)) * rs + bob
        w = 3.3 - 0.5 * (i % 2)
        twist = p.scatter * 16 * (1 if i % 2 else -1)
        # orbit: y squashed a little so the ring reads as tilted
        ang = base
        depth = math.sin(math.radians(ang))  # >0 = front half (drawn over the eye)
        if p.align > 0:  # lens formation: stacked on an arc in front of the eye, all pointing right
            k = (i - (N_SHARDS - 1) / 2) / ((N_SHARDS - 1) / 2)
            lens_a = k * 58
            ang = ang + ((lens_a - ang + 180) % 360 - 180) * p.align
            depth = 1.0 if p.align > 0.5 else depth
        out.append((ang, r_in, r_out, w, twist, depth, i))
    return out


def _eye(cv, C, p):
    cv.ellipse(C[0], C[1], 6.4, 5.8, SOCKET, name="socket")
    if p.eye in ("squeeze",):
        cv.ellipse(C[0], C[1] + 0.4, 4.8, 1.8, SCLERA, shade="two", name="eye")
        cv.line((round(C[0]) - 4, round(C[1])), (round(C[0]) + 3, round(C[1])), PUPIL, name="eye")
        return
    cv.ellipse(C[0], C[1], 4.9, 4.5, SCLERA, name="eye")
    lx, ly = p.look
    if p.eye == "dead":
        hc.eye_stamp(cv, ["k.k", ".k.", "k.k"], round(C[0]) - 1 + lx, round(C[1]) - 2 + ly, {"k": PUPIL})
        return
    ix, iy = C[0] + lx * 1.0, C[1] + ly * 0.7
    cv.circle(ix, iy, 3.0, IRIS_HI if p.eye == "glow" else IRIS, shade="flat", name="eye")
    cv.circle(ix, iy, 1.7, IRIS if p.eye == "glow" else PUPIL, shade="flat", name="eye")
    cv.pixel(math.floor(ix) - 2, math.floor(iy) - 2, px.GLINT, name="eye")
    if p.eye == "crack":
        cv.line((round(C[0]) - 3, round(C[1]) - 3), (round(C[0]), round(C[1])), PUPIL, name="eye")
        cv.line((round(C[0]), round(C[1])), (round(C[0]) + 2, round(C[1]) + 3), PUPIL, name="eye")
        cv.line((round(C[0]), round(C[1])), (round(C[0]) + 4, round(C[1]) - 1), PUPIL, name="eye")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    C = (cv.gx + 0.5 + p.bx, cv.gy + 0.5 + p.by)
    shards = _layout(p, C)
    back = [s for s in shards if s[5] <= 0]
    front = [s for s in shards if s[5] > 0]
    halo = cv.layer(above=False, outline=False)
    if p.halo:  # soul glow behind the eye
        px.glow_ring(halo, C[0], C[1], 7.0 + p.halo, hc.SOUL_GLOW, thickness=1.0, inner=px.SOUL_VIOLET)
    for (a, ri, ro, w, tw, dep, i) in back:
        _shard(cv, C, a, ri, ro, w, tw, SHARD_B, "shard_b")
    if p.shatter < 0.5:
        _eye(cv, C, p)
    else:  # the eye has broken into three drifting fragments
        s = p.shatter
        for k, (da, ox, oy) in enumerate(((0, -3.0, -2.0), (120, 3.0, -1.0), (240, 0.0, 3.0))):
            q = (C[0] + ox * (1 + 2 * s), C[1] + oy * (1 + 2 * s) + s * 3)
            pts = [px.polar(q, da + 10 * s + j * 120, 3.4 - 1.4 * s) for j in range(3)]
            cv.polygon(pts, SCLERA if k != 1 else SOCKET, shade=1, name="frag")
    for (a, ri, ro, w, tw, dep, i) in front:
        _shard(cv, C, a, ri, ro, w, tw, SHARD, "shard")
    if p.shatter > 0:  # tiny glittering splinters
        fx = cv.layer(above=True, outline=False)
        for k in range(6):
            a = k * 60 + 20
            r = 12 + 6 * p.shatter + 2 * px.hash01(k)
            q = px.polar(C, a, r)
            q = (q[0], q[1] + p.shatter * 2)
            fx.line((math.floor(q[0]), math.floor(q[1])), (math.floor(q[0]) + 1, math.floor(q[1]) + 1),
                    px.GLINT if k % 2 else hc.SOUL_GLOW, name="splinter")
    if p.burst is not None:
        fx = cv.layer(above=True, outline=False)
        t = p.burst
        E = (C[0] + 6, C[1])
        ln = 8 + 18 * t
        for k, (da, sc) in enumerate(((0, 1.0), (22, 0.6), (-22, 0.6), (45, 0.4), (-45, 0.4))):
            q = px.polar(E, da, ln * sc)
            fx.line((round(E[0]), round(E[1])), (round(q[0]), round(q[1])), FLASH if k == 0 else FLASH_V,
                    name="flash")
        if t < 0.8:
            px.glow_ring(fx, E[0] + 4 + 10 * t, E[1], 2 + 5 * t, FLASH_V, thickness=1.0)
        if 0.3 < t < 0.7:
            px.impact(fx, E[0] + 12 + 6 * t, E[1], size=4, color=hc.SOUL_GLOW, core=FLASH)
