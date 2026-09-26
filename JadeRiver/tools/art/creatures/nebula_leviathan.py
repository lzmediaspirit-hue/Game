"""Nebula leviathan - FIELD BOSS of the Lantern Star Field (level 99): a colossal sky-whale-
serpent that swims the star sea between the drifting islands (Space).

View: side, facing right, flying (cell 256, 128 art px; anchor at the body centre).  ~96 art px
from the curled tail to the snout and ~100 px tall with its veils: the biggest thing in the
game (the player is ~45).  A vast whale head (domed crown, arched baleen mouth, bulging pleated
lower jaw, small ancient eyes) carries a serpent body that sweeps down and back and curls up
into a veiled tail, all inside the frame.  The head sits a little right of centre so the void
breath has room in front of the snout.
Rig: a Catmull-Rom spine through six control points (tail tip -> neck) with a travelling
wave; the head is drawn in its own frame at the neck (``head`` tilts it, ``jaw`` opens it).
Parts, back to front: star lines spiralling in (windup, FX behind), the far pectoral veil, the
tail veils and the long dorsal veil inside the curl (translucent violet with teal and magenta
edges, fine rays), the serpent body (deep indigo hide, pale star-white belly with throat
pleats, teal and magenta nebula bands along the flank), constellations of glowing points joined
by faint lines, the near pectoral veil, then the head: lower jaw, dome and rostrum as one form,
the arched mouth with its ivory baleen fringe, wrinkles round a small gold eye; FX in front.
Idle: a slow majestic drift, the veils ripple, the constellation lights pulse.  Walk: glides
forward, a long wave rolling down the body and the veils streaming back.  Windup: rears its
head back, the mouth gapes, a violet-black void gathers inside it while star lines spiral in
(held).  Attack: lunges and breathes the void on frame 1 - a wide cone of darkness full of
stars ending in a big burst.  Hurt: recoils, the lights flicker.  Death: it dims, the
constellation lights go out one by one, it sinks and fades.
"""
import math

import numpy as np

import helpers_batch_a as ha
import helpers_batch_c as hc
import pixel as px

SPEC = {
    "id": "nebula_leviathan",
    "cell": 256,
    "anchor": [120, 128],
    "flying": True,
    "hit_frame": 1,
}

# ---- palette (7 ramps): indigo hide, star-white belly, nebula teal, nebula magenta, veil
# membrane, ivory baleen, a dimmed hide for death; accents: star gold, void violet -------------
HIDE = px.material("nlev_hide", "#7486d6", "#3d4298", "#2a2b6c", "#1c1a48", outline="#07061a",
                   thresholds=(0.9, 0.55, 0.2))
BELLY = px.material("nlev_belly", "#f4f0ff", "#cbc4ee", "#9a92ca", "#6c64a2", outline="#0b0922")
TEAL = px.material("nlev_teal", "#94f0dc", "#36b2aa", "#257c8a", "#1e506e", outline="#06121c",
                   thresholds=(0.9, 0.55, 0.2))
MAG = px.material("nlev_mag", "#ffaade", "#cb52a0", "#8b3289", "#502668", outline="#14071d",
                  thresholds=(0.9, 0.55, 0.2))
VEIL = px.material("nlev_veil", "#e2d8ff", "#7466c4", "#5a4ea6", "#3e3584", outline="#0c0a26")
BALEEN = px.material("nlev_baleen", "#fff4d0", "#e6d29a", "#b69a6a", "#7a6448", outline="#1c1408")
DIM = px.material("nlev_dim", "#4a5094", "#2c2e6a", "#211f50", "#16143a", outline="#05040f")
VEIL_RAY = px.rgb("#a293ea")
MOUTH = px.rgb("#1a0c2a")
STAR_W = px.rgb("#ffffff")
STAR_G = px.rgb("#ffe6a1")
STAR_C = px.rgb("#b8f4ff")
STAR_OFF = px.rgb("#4a4f8e")
CLINE = px.rgb("#6f7fd0")  # faint constellation lines (one step above the hide)
EYE_G = px.rgb("#ffd66a")
EYE_K = px.rgb("#1a1030")
VOID_K = px.rgb("#10081c")
VOID_D = px.rgb("#35165a")
VOID_M = px.rgb("#8b52d8")
VOID_L = px.rgb("#e8dcff")

TAU = 2 * math.pi

# ---- poses ------------------------------------------------------------------------------------
# bx, by   whole-body offset       rot  whole-body pitch (deg about the neck, + = nose up)
# wave     (amplitude px, phase) travelling wave along the body
# curl     extra curl of the tail (px the tail control points move in toward the neck)
# head     head tilt (deg, + = rear back / nose up)   jaw  gape 0..1     eye  open|angry|squeeze|closed
# veil     veil ripple phase    stream  veils swept back 0..1 (gliding)
# pulse    constellation pulse step    lights  fraction of constellation lights still lit
# flicker  lights flicker (hurt)   orb  void gathering in the mouth 0..1   spiral  star lines 0..3
# breath   void breath (None | 1 hit | 0.5 dissipating)   dim  hide dimmed (death)   fade  opacity
DEFAULTS = dict(bx=0.0, by=0.0, rot=0.0, wave=(1.2, 0.0), curl=0.0, head=0.0, jaw=0.0, eye="open", veil=0.0,
                stream=0.0, pulse=0, lights=1.0, flicker=False, orb=0.0, spiral=0, breath=None, dim=False,
                fade=1.0)

POSE = px.poses(DEFAULTS, {
    "idle": [  # a slow majestic drift: veils ripple, the constellations pulse
        dict(wave=(1.2, 0.0), veil=0.0, pulse=0),
        dict(wave=(1.2, TAU / 4), veil=1.0, pulse=1, by=-1),
        dict(wave=(1.2, TAU / 2), veil=2.0, pulse=2, by=-1, head=1),
        dict(wave=(1.2, TAU * 3 / 4), veil=3.0, pulse=3, head=1),
    ],
    "walk": [  # glides forward: a long wave rolls down the body, the veils stream back
        dict(wave=(2.6, 0.0), veil=0.0, stream=1.0, rot=-2, pulse=0),
        dict(wave=(2.6, TAU / 6), veil=1.0, stream=1.0, rot=-2, by=-1, pulse=0),
        dict(wave=(2.6, TAU * 2 / 6), veil=2.0, stream=1.0, rot=-3, by=-1, pulse=1),
        dict(wave=(2.6, TAU * 3 / 6), veil=3.0, stream=1.0, rot=-3, pulse=1),
        dict(wave=(2.6, TAU * 4 / 6), veil=4.0, stream=1.0, rot=-2, by=1, pulse=2),
        dict(wave=(2.6, TAU * 5 / 6), veil=5.0, stream=1.0, rot=-2, by=1, pulse=2),
    ],
    "windup": [  # rears the head back, the mouth gapes, the void gathers, star lines spiral in - held
        dict(bx=-2, rot=2, curl=2.0, head=8, jaw=0.4, eye="angry", veil=1.0, orb=0.35, spiral=1, pulse=1),
        dict(bx=-4, by=-1, rot=4, curl=4.0, head=15, jaw=0.8, eye="angry", veil=2.0, orb=0.7, spiral=2, pulse=2),
        dict(bx=-5, by=-2, rot=5, curl=5.0, head=19, jaw=1.0, eye="angry", veil=2.5, orb=1.0, spiral=3, pulse=3),
    ],
    "attack": [  # lunges and breathes the void (hit on frame 1), the burst dissipates, it recovers
        dict(bx=-3, rot=2, curl=3.0, head=6, jaw=1.0, eye="angry", veil=3.0, stream=0.4, orb=1.0),
        dict(bx=1, rot=-1, head=-2, jaw=0.85, eye="angry", veil=4.0, stream=1.0, breath=1.0),
        dict(bx=1, rot=-1, head=-1, jaw=0.6, eye="angry", veil=5.0, stream=0.6, breath=0.5),
        dict(bx=0, head=0, jaw=0.2, veil=6.0, stream=0.2),
    ],
    "hurt": [  # recoils, the constellation lights flicker
        dict(bx=-4, by=-2, rot=6, curl=2.0, head=14, jaw=0.5, eye="squeeze", veil=2.0, flicker=True),
        dict(bx=-2, by=-1, rot=3, curl=1.0, head=6, jaw=0.2, eye="squeeze", veil=3.0, flicker=True, pulse=1),
    ],
    "death": [  # it dims, the lights go out one by one, it sinks and fades
        dict(bx=-3, by=-1, rot=5, curl=1.0, head=12, jaw=0.6, eye="squeeze", veil=2.0, lights=0.8, flicker=True),
        dict(bx=-2, by=2, rot=-2, head=-6, jaw=0.4, eye="closed", veil=2.6, lights=0.55, dim=True),
        dict(bx=-2, by=4, rot=-5, head=-10, jaw=0.3, eye="closed", veil=3.0, lights=0.3, dim=True, wave=(0.6, 0.0)),
        dict(bx=-2, by=6, rot=-7, head=-12, jaw=0.3, eye="closed", veil=3.3, lights=0.1, dim=True,
             wave=(0.4, 0.0), fade=0.6),
        dict(bx=-2, by=8, rot=-8, head=-12, jaw=0.3, eye="closed", veil=3.5, lights=0.0, dim=True,
             wave=(0.3, 0.0), fade=0.3),
    ],
})

# spine control points from the anchor O (tail tip -> neck) and the head centre offset
CTRL = ((-36.0, -34.0), (-45.0, -18.0), (-43.0, 0.0), (-31.0, 13.0), (-13.0, 17.0), (2.0, 8.0))
HEAD = (12.0, -1.0)
HS = 1.3  # head scale: the head is drawn at 1.3x its local measurements
# body radius along the spine, t = 0 tail tip .. 1 neck
PROFILE = ((0.0, 1.6), (0.12, 3.4), (0.3, 6.0), (0.55, 9.5), (0.8, 12.0), (1.0, 13.0))
# constellations on the flank: lists of (t, v) with v across the body (-1 belly .. +1 back)
CONSTELLATIONS = (
    ((0.36, 0.1), (0.41, -0.25), (0.46, 0.05), (0.5, -0.3)),
    ((0.58, 0.3), (0.63, -0.05), (0.68, 0.25), (0.7, -0.35), (0.75, 0.0)),
    ((0.82, 0.35), (0.87, 0.05), (0.92, 0.4), (0.95, -0.05)),
    ((0.16, 0.2), (0.22, -0.2), (0.27, 0.15)),
)
HEAD_STARS = ((-4.0, -9.0), (2.0, -11.0), (8.0, -8.0))  # a small crown constellation on the head


def _radius(t):
    for (t0, r0), (t1, r1) in zip(PROFILE, PROFILE[1:]):
        if t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return PROFILE[-1][1]


def _spine(O, p):
    """Dense spine points, tail tip -> neck, in canvas space (before the whole-body pitch)."""
    ctrl = []
    n = len(CTRL)
    neck = CTRL[-1]
    for i, (x, y) in enumerate(CTRL):
        k = (n - 1 - i) / (n - 1)  # 1 at the tail, 0 at the neck
        cx = x + (neck[0] - x) * 0.06 * p.curl * k
        cy = y + (neck[1] - y) * 0.06 * p.curl * k
        ctrl.append((O[0] + cx, O[1] + cy))
    pts = ha.catmull(ctrl, per=12)
    amp, ph = p.wave
    out = []
    for k, q in enumerate(pts):
        t = k / (len(pts) - 1)
        nx, ny = ha.normal_at(pts, k)
        s = amp * math.sin(ph + t * 9.0) * (1.0 - t) ** 0.8
        out.append((q[0] + nx * s, q[1] + ny * s))
    return out


def _at(sp, ns, rs, k, v):
    return (sp[k][0] + ns[k][0] * rs[k] * v, sp[k][1] + ns[k][1] * rs[k] * v)


# ---- veils --------------------------------------------------------------------------------------
def _veil(cv, root_a, root_b, tip_dir, length, width, p, key, mat=VEIL, shade="two", name="veil",
          edge=None, sep=False):
    """A long flowing veil fin from the root edge a..b, trailing ``length`` px along ``tip_dir``
    (deg), rippling with ``p.veil``: membrane, fine rays and a coloured free edge."""
    n = 10
    a = math.radians(tip_dir)
    dx, dy = math.cos(a), -math.sin(a)
    nx, ny = -dy, dx
    lead, trail = [], []
    for i in range(n + 1):
        s = i / n
        wob = math.sin(p.veil * 1.2 + s * 5.0 + key) * (0.5 + 2.4 * s)
        w = width * (1.0 - 0.75 * s) + 0.6
        cx = root_a[0] + (root_b[0] - root_a[0]) * 0.5 + dx * length * s + nx * wob
        cy = root_a[1] + (root_b[1] - root_a[1]) * 0.5 + dy * length * s + ny * wob
        lead.append((cx - nx * w * (1 - s * 0.3) if i else root_a[0], cy - ny * w * (1 - s * 0.3) if i else root_a[1]))
        trail.append((cx + nx * w if i else root_b[0], cy + ny * w if i else root_b[1]))
    poly = lead + trail[::-1]
    cv.polygon(poly, mat, shade=shade, name=name, sep=sep)
    # fine rays fanning from the root
    for j in (0.25, 0.5, 0.75):
        r0 = px.lerp_pt(lead[1], trail[1], j)
        r1 = px.lerp_pt(lead[n - 1], trail[n - 1], j)
        mid = px.lerp_pt(lead[n // 2], trail[n // 2], j)
        for u, v in ((r0, mid), (mid, r1)):
            cv.line((math.floor(u[0]), math.floor(u[1])), (math.floor(v[0]), math.floor(v[1])), VEIL_RAY,
                    decal=True, clip=name, name=name)
    if edge is not None:  # the free trailing edge glows teal or magenta
        e = [trail[i] for i in range(2, n + 1)] + [lead[n]]
        cv.limb([px.lerp_pt(q, c, 0.12) for q, c in zip(e, [px.lerp_pt(lead[i], trail[i], 0.5)
                                                            for i in range(2, n + 1)] + [lead[n]])],
                0.7, edge, shade="two", decal=True, clip=name, name=name)
    return poly


def _dorsal(cv, sp, rs, ns, p):
    """The long dorsal veil rising along the back (inside the curl), rippling."""
    n = len(sp)
    k0, k1 = int(n * 0.2), int(n * 0.86)
    outer, inner = [], []
    for k in range(k0, k1 + 1, 2):
        t = (k - k0) / (k1 - k0)
        env = math.sin(math.pi * t) ** 0.7
        h = (4.0 + 7.5 * env) * (1.0 + 0.12 * math.sin(p.veil * 1.3 + t * 11.0))
        h -= 1.8 * p.stream * t
        nx, ny = ns[k]
        outer.append((sp[k][0] + nx * (rs[k] + h), sp[k][1] + ny * (rs[k] + h)))
        inner.append((sp[k][0] + nx * (rs[k] - 2.0), sp[k][1] + ny * (rs[k] - 2.0)))
    cv.polygon(outer + inner[::-1], VEIL, shade="two", name="dorsal")
    for j in range(2, len(outer) - 1, 4):  # rays
        a, b = inner[j], outer[max(0, j - 2)]
        u, v = px.lerp_pt(a, b, 0.4), px.lerp_pt(a, b, 0.9)
        cv.line((math.floor(u[0]), math.floor(u[1])), (math.floor(v[0]), math.floor(v[1])), VEIL_RAY, decal=True,
                clip="dorsal", name="dorsal")
    edge = cv.mask_of("dorsal") & ~px.erode(cv.mask_of("dorsal"))
    far = np.zeros_like(edge)
    for q in outer:
        far |= cv.mask_ellipse(q[0], q[1], 1.8, 1.8)
    edge &= far
    cv._commit(edge, np.where(edge, 0, -1).astype(np.int8), px.flat(MAG.light, outline=VEIL.outline), name="dorsal")


# ---- body ---------------------------------------------------------------------------------------
def _body(cv, sp, ts, rs, ns, p, hide):
    idx = list(range(len(sp)))
    cv.limb([sp[k] for k in idx], [rs[k] for k in idx], hide, name="body")
    n = len(sp)
    # pale star-white belly along the outside of the curl, with throat pleats toward the front
    bel = [k for k in range(n) if 0.12 <= ts[k]]
    pts = [_at(sp, ns, rs, k, -0.72) for k in bel[::3]]
    rad = [max(0.8, rs[k] * 0.42) for k in bel[::3]]
    cv.limb(pts, rad, BELLY if not p.dim else DIM.step(-1), shade="two", decal=True, clip="body", name="body")
    for v in (-0.52, -0.72, -0.9):  # pleat grooves
        seg = [_at(sp, ns, rs, k, v) for k in range(int(n * 0.66), n, 3)]
        for a, b in zip(seg, seg[1:]):
            cv.line((math.floor(a[0]), math.floor(a[1])), (math.floor(b[0]), math.floor(b[1])),
                    BELLY.shadow if not p.dim else DIM.deep, decal=True, clip="body", name="body")
    if p.dim:
        return
    # nebula bands drifting along the flank: teal low on the flank, magenta toward the back
    for mat, v0, th, t0, t1, f in ((TEAL, -0.1, 0.24, 0.22, 0.98, 7.0), (MAG, 0.42, 0.2, 0.3, 0.9, 9.0)):
        ks = [k for k in range(n) if t0 <= ts[k] <= t1][::3]
        pts, rad = [], []
        for j, k in enumerate(ks):
            s = j / max(1, len(ks) - 1)
            wob = 0.14 * math.sin(s * f + v0 * 3.0)
            pts.append(_at(sp, ns, rs, k, v0 + wob))
            rad.append(max(0.7, rs[k] * th * (0.55 + 0.45 * math.sin(math.pi * s)) *
                           (0.75 + 0.25 * math.sin(s * f * 1.7 + 1.0))))
        cv.limb(pts, rad, mat, decal=True, clip="body", name="body")


def _constellations(cv, sp, ts, rs, ns, p, frame):
    """Glowing points joined by faint lines.  ``lights`` < 1 puts them out one by one."""
    n = len(sp)
    for ci, cons in enumerate(CONSTELLATIONS):
        pts = []
        for (t, v) in cons:
            k = min(n - 1, int(round(t * (n - 1))))
            x, y = _at(sp, ns, rs, k, v)
            pts.append((math.floor(x), math.floor(y)))
        for a, b in zip(pts, pts[1:]):
            cv.line(a, b, CLINE if not p.dim else DIM.light, decal=True, clip="body", name="body")
        for j, (x, y) in enumerate(pts):
            lit = px.hash01("nlev_out", ci, j) < p.lights
            if p.flicker and frame % 2 == 1 and (ci + j) % 3 != 0:
                lit = False  # the lights stutter out ...
            if not lit:
                cv.pixel(x, y, STAR_OFF, decal=True, clip="body", name="body")
                continue
            big = (ci + j + p.pulse) % 3 == 0 or (p.flicker and frame % 2 == 0)  # ... and flare back
            if big:
                cv.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], STAR_G, decal=True, clip="body",
                          name="body")
            cv.pixel(x, y, STAR_W, decal=True, clip="body", name="body")


# ---- head ---------------------------------------------------------------------------------------
def _head(cv, H, deg, p, hide, frame):
    """Whale head in its own frame: lower jaw, dome + rostrum, arched baleen mouth, eye, and the
    void gathering in the gape.  Returns (orb centre, eye point, snout tip, crown star points)."""
    X, Y = H

    def L(x, y):
        return (X + x, Y + y)

    belly = BELLY if not p.dim else DIM.step(-1)
    with cv.xform(px.rotate(deg, H), px.scale(HS, HS, H)):
        hinge = L(-11.0, 5.5)
        ja = -34.0 * p.jaw
        with cv.xform(px.rotate(ja, hinge)):
            jaw = cv.union(cv.geom_ellipse(X + 3.0, Y + 8.5, 15.5, 7.2),
                           cv.geom_limb([L(4.0, 8.0), L(14.0, 7.5), L(19.5, 5.8)], [6.5, 5.0, 3.0]),
                           weights=[1.0, 0.8])
            cv.draw_geom(jaw, hide, shade="nolight", name="jaw")
            # pale pleated throat along the bottom of the jaw
            cv.ellipse(X + 2.0, Y + 12.5, 15.0, 4.0, belly, shade="two", decal=True, clip="jaw", name="jaw")
            for j in range(3):
                y = Y + 11.5 + j * 1.8
                a0, a1 = cv.tp((X - 9 + j * 2, y)), cv.tp((X + 14 - j * 2, y - 0.5))
                cv.line((math.floor(a0[0]), math.floor(a0[1])), (math.floor(a1[0]), math.floor(a1[1])),
                        belly.shadow, decal=True, clip="jaw", name="jaw")
            lo_lip = [cv.tp(L(19.0, 4.8)), cv.tp(L(8.0, 4.4)), cv.tp(L(-4.0, 5.2))]
        skull = cv.union(cv.geom_ellipse(X - 2.0, Y - 2.0, 16.5, 12.5),
                         cv.geom_limb([L(3.0, -4.0), L(13.0, -1.0), L(20.5, 3.4)], [10.0, 7.0, 3.6]),
                         weights=[1.0, 0.8])
        # the arched mouth line: low under the eye, high over the middle, down to the snout tip
        arch = [L(-11.0, 5.5), L(-5.0, 2.6), L(3.0, 1.2), L(11.0, 1.6), L(17.0, 3.0), L(21.0, 4.2)]
        # the skull ends at the mouth line: below it is the lower jaw (or the gape)
        cut = cv.mask_polygon(arch + [L(24.0, 8.0), L(24.0, 20.0), L(-12.0, 20.0)])
        cv.draw_geom(skull, hide, name="skull", minus=cut)
        if not p.dim:  # a band of teal nebula across the crown, magenta over the brow
            cv.ellipse(X - 5.0, Y - 8.0, 11.0, 2.4, TEAL, angle=-8, decal=True, clip="skull", name="skull")
            cv.ellipse(X + 5.0, Y - 5.5, 7.0, 1.6, MAG, angle=-18, decal=True, clip="skull", name="skull")
        up_lip = [cv.tp(q) for q in arch]
        orb_c = cv.tp(L(19.5, 6.5 + 4.0 * p.jaw))
        if p.jaw > 0.12:
            if p.orb > 0:  # the void swells in the gape, behind the jaws and out past the lips
                _orb(cv, orb_c, p.orb, frame)
            with cv.xform(np.linalg.inv(cv.M)):
                cv.polygon(up_lip + lo_lip, px.flat(VOID_K), under=True, name="mouth")
            # the baleen curtain hanging from the upper jaw into the gape
            _fringe(cv, up_lip[1:], lambda x, j: 2 + int(round(2.5 * p.jaw * (0.6 + 0.4 * math.sin(j * 0.9)))),
                    clip="mouth")
        else:  # the closed mouth: the ivory baleen fringe under the arched upper lip
            _fringe(cv, up_lip, lambda x, j: 2 + (1 if px.hash01("nlev_fr", j) > 0.6 else 0), clip=["skull", "jaw"])
            for a0, a1 in zip(up_lip, up_lip[1:]):
                cv.line((math.floor(a0[0]), math.floor(a0[1])), (math.floor(a1[0]), math.floor(a1[1])), MOUTH,
                        decal=True, clip=["skull", "jaw"], name="skull")
        # wrinkles round the small ancient eye
        for pts in (((-14.0, -1.5), (-10.5, -3.6), (-6.0, -3.4)), ((-13.0, 2.2), (-10.0, 3.6), (-6.5, 3.2)),
                    ((-15.5, 0.4), (-13.8, -0.4))):
            q = [cv.tp(L(*a0)) for a0 in pts]
            for a0, a1 in zip(q, q[1:]):
                cv.line((math.floor(a0[0]), math.floor(a0[1])), (math.floor(a1[0]), math.floor(a1[1])), hide.deep,
                        decal=True, clip="skull", name="skull")
        eye_at = cv.tp(L(-11.0, -0.8))
        snout = cv.tp(L(21.5, 4.0))
        crown = [cv.tp(L(*q)) for q in HEAD_STARS]
    return orb_c, eye_at, snout, crown


def _fringe(cv, lip, length, clip):
    """Ivory baleen strands hanging straight down from the lip polyline (canvas points): one
    strand per pixel column, alternating tones, ragged ends."""
    xs = [q[0] for q in lip]
    ys = [q[1] for q in lip]
    order = np.argsort(xs)
    xs, ys = np.array(xs)[order], np.array(ys)[order]
    cols = [(BALEEN.light, BALEEN.base), (BALEEN.base, BALEEN.shadow)]
    with cv.xform(np.linalg.inv(cv.M)):  # canvas space: the strands hang straight down
        for j, x in enumerate(range(int(math.ceil(xs[0])), int(math.floor(xs[-1])) + 1)):
            y0 = int(math.floor(np.interp(x + 0.5, xs, ys))) + 1
            ln = length(x, j)
            for i in range(ln):
                c = cols[j % 2][0 if i < ln - 1 else 1]
                cv.pixel(x, y0 + i, c, decal=True, clip=clip, name="baleen")


def _arch_y(Y, x):
    """Height of the arched mouth line at head-local x."""
    xs = (-11.0, -5.0, 3.0, 11.0, 17.0, 21.0)
    ys = (5.5, 2.6, 1.2, 1.6, 3.0, 4.2)
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if x <= x1:
            return Y + y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return Y + ys[-1]


def _eye(cv, E, p):
    x, y = math.floor(E[0]) - 1, math.floor(E[1]) - 1
    if p.eye == "closed":
        cv.stamp(["kkk"], x, y + 1, {"k": HIDE.deep}, name="eye")
        return
    if p.eye == "squeeze":
        cv.stamp(["k..", ".kk", "k.."], x, y, {"k": EYE_K}, name="eye")
        return
    cv.stamp(["gyk", "yyy"], x, y, {"g": STAR_W, "y": EYE_G, "k": EYE_K}, name="eye")
    if p.eye == "angry":  # a heavy brow fold drops toward the snout
        cv.pixels([(x - 2, y - 2), (x - 1, y - 2), (x, y - 1), (x + 1, y - 1), (x + 2, y - 1), (x + 3, y)], HIDE.deep,
                  name="brow")


# ---- FX -------------------------------------------------------------------------------------------
def _orb(cv, c, level, frame):
    """The void gathering in the open mouth: a black core in a violet ring with a bright rim,
    drawn only where the canvas is still empty (behind the jaws, out past the lips)."""
    r = 2.5 + 4.0 * level
    d = np.hypot(cv.X - c[0], cv.Y - c[1])
    free = ~cv.filled
    layers = ((r + 1.3, VOID_M), (r, VOID_D), (max(1.0, r - 1.8), VOID_K))
    for rr, col in layers:
        m = (d <= rr) & free
        cv._commit(m, np.where(m, 1, -1).astype(np.int8), px.flat(col, outline=VOID_K), name="orb")
    rim = (np.abs(d - (r + 1.0)) <= 0.5) & (cv.X - c[0] + cv.Y - c[1] < -1.0) & free
    cv._commit(rim, np.where(rim, 1, -1).astype(np.int8), px.flat(VOID_L, outline=VOID_K), name="orb")
    if level > 0.5:  # a few captured stars glinting in the dark
        for k, (dx, dy) in enumerate(((-1.5, 1.0), (2.0, -1.0), (0.5, 2.2))):
            if (k + frame) % 3 != 2:
                q = (math.floor(c[0] + dx * level * 1.4), math.floor(c[1] + dy * level * 1.4))
                cv.pixel(q[0], q[1], STAR_W, clip="orb", name="orb")


def _spirals(fx, c, level, frame):
    """Star lines spiralling in toward the mouth."""
    for j in range(2 + level):
        a0 = 40 + j * (360 / (2 + level)) + frame * 20
        r0 = 23.0
        r1 = 7.0 + (3 - level)
        col = (STAR_C, STAR_G, VOID_L, STAR_C, STAR_G)[j]
        hc.spiral(fx, c, r0, r1, a0, -260, col, name="spiral", step=3.0)
        head = px.polar(c, a0 - 260, r1)
        fx.pixels([(math.floor(head[0]), math.floor(head[1])), (math.floor(head[0]) + 1, math.floor(head[1]))],
                  STAR_W, name="spiral")


def _breath(fx, top, M, deg, life, frame):
    """The void breath: a wide cone of darkness from the mouth full of swept stars, rimmed in
    violet with bright edges, ending in a big starburst.  ``life`` 0.5 = the dissipating cloud."""
    x0, y0 = M
    ln = 123.0 - x0  # the cone runs out to the frame edge
    if life >= 1.0:
        with fx.xform(px.rotate(deg, M)):
            def P(u, v):
                return (x0 + u, y0 + v)
            outer = [P(-2, -5), P(6, -10), P(ln * 0.55, -19), P(ln - 5, -24), P(ln, -14), P(ln + 1, 0), P(ln, 14),
                     P(ln - 5, 24), P(ln * 0.55, 19), P(6, 10), P(-2, 5)]
            fx.polygon(outer, px.flat(VOID_M), name="breath")
            mid = [P(0, -3.5), P(8, -7.5), P(ln * 0.55, -15.5), P(ln - 6, -20), P(ln - 1.5, -11), P(ln - 0.5, 0),
                   P(ln - 1.5, 11), P(ln - 6, 20), P(ln * 0.55, 15.5), P(8, 7.5), P(0, 3.5)]
            fx.polygon(mid, px.flat(VOID_D), name="breath")
            core = [P(1, -2), P(10, -4.5), P(ln * 0.55, -10), P(ln - 7, -12), P(ln - 3, 0), P(ln - 7, 12),
                    P(ln * 0.55, 10), P(10, 4.5), P(1, 2)]
            fx.polygon(core, px.flat(VOID_K), name="breath")
            # bright edges streaming along the rim
            for sgn in (-1, 1):
                for (u0, v0), (u1, v1) in (((8, 8.8), (ln * 0.5, 17.2)), ((ln * 0.5, 17.2), (ln - 6, 22.4))):
                    q0, q1 = fx.tp(P(u0, sgn * v0)), fx.tp(P(u1, sgn * v1))
                    with fx.xform(np.linalg.inv(fx.M)):
                        fx.line((math.floor(q0[0]), math.floor(q0[1])), (math.floor(q1[0]), math.floor(q1[1])), VOID_L,
                                name="breath")
            stars = []
            for k in range(12):  # stars swept along in the darkness
                u = (k + 0.5) / 12
                v = (px.hash01("nlev_br", k) - 0.5) * (6 + 30 * u)
                stars.append(fx.tp(P(6 + (ln - 12) * u, v)))
            burst = fx.tp(P(ln - 8, 0))
        for k, (x, y) in enumerate(stars):
            fx.pixel(math.floor(x), math.floor(y), STAR_W if k % 3 else STAR_G, name="breath")
        # the starburst where it lands
        bx, by = burst
        ring = np.abs(np.hypot(top.X - bx, top.Y - by) - 7.0) <= 0.5
        ring &= top.X < 125.5
        top._commit(ring, np.where(ring, 1, -1).astype(np.int8), px.flat(VOID_L), name="burst")
        for a in range(0, 360, 30):
            r1 = 14.0 if a % 60 == 0 else 10.5
            p1 = px.polar((bx, by), a, r1)
            while p1[0] > 125.0 and r1 > 5.0:
                r1 -= 1.0
                p1 = px.polar((bx, by), a, r1)
            p0 = px.polar((bx, by), a, 8.5)
            top.line((math.floor(p0[0]), math.floor(p0[1])), (math.floor(p1[0]), math.floor(p1[1])),
                     VOID_L if a % 60 == 0 else STAR_C, name="burst")
        top.circle(bx, by, 2.2, px.flat(VOID_L), name="burst")
        px.impact(top, bx, by, size=3, color=STAR_W, core=STAR_W)
    else:  # dissipating: billowing violet-black smoke full of loose stars
        for k in range(6):
            u = (k + 0.5) / 6
            cx = x0 + 4 + (ln - 10) * u
            cy = y0 + math.sin(k * 2.1 + frame) * (3.0 + 6.0 * u)
            r = 2.5 + 3.5 * u
            fx.circle(cx, cy, r + 1.0, px.flat(VOID_M), name="breath")
            fx.circle(cx, cy, r, px.flat(VOID_D), name="breath")
            fx.circle(cx - 0.8, cy - 0.8, max(0.8, r - 2.0), px.flat(VOID_K), name="breath")
        for k in range(8):
            x = x0 + 6 + k * (ln - 10) / 8
            y = y0 + (px.hash01("nlev_br2", k) - 0.5) * 26
            fx.pixels([(math.floor(x), math.floor(y)), (math.floor(x) + 1, math.floor(y))],
                      STAR_W if k % 2 else VOID_L, name="breath")


def draw(cv: px.Canvas, action: str, frame: int) -> None:
    p = POSE(action, frame)
    cv.opacity = p.fade
    hide = DIM if p.dim else HIDE
    O = (cv.gx + p.bx, cv.gy + p.by)
    neck = (O[0] + CTRL[-1][0], O[1] + CTRL[-1][1])
    back = cv.layer(above=False, outline=False)
    with cv.xform(px.rotate(p.rot, neck)):
        sp = [cv.tp(q) for q in _spine(O, p)]
        H = cv.tp((O[0] + HEAD[0], O[1] + HEAD[1]))
    n = len(sp)
    ts = [k / (n - 1) for k in range(n)]
    rs = [_radius(t) for t in ts]
    ns = [ha.normal_at(sp, k) for k in range(n)]
    # ---- veils behind the body: far pectoral, tail veils ----
    kp = int(n * 0.84)
    pa, pb = _at(sp, ns, rs, kp, -0.55), _at(sp, ns, rs, kp - 10, -0.7)
    _veil(cv, pa, pb, 232 + 8 * p.stream, 26 - 2 * p.stream, 5.5, p, 1.3, shade="dark", name="farveil")
    t_dir = math.degrees(math.atan2(-(sp[0][1] - sp[4][1]), sp[0][0] - sp[4][0]))
    ta, tb = _at(sp, ns, rs, 3, 1.0), _at(sp, ns, rs, 3, -1.0)
    _veil(cv, ta, tb, t_dir + 30 - 10 * p.stream, 20, 4.5, p, 0.0, name="tailveil", edge=TEAL)
    _veil(cv, ta, tb, t_dir - 25 - 6 * p.stream, 24, 5.0, p, 2.2, name="tailveil2", edge=MAG)
    _dorsal(cv, sp, rs, ns, p)
    # ---- body ----
    _body(cv, sp, ts, rs, ns, p, hide)
    _constellations(cv, sp, ts, rs, ns, p, frame)
    # ---- near pectoral veil, hanging from under the front body ----
    kp = int(n * 0.9)
    pa, pb = _at(sp, ns, rs, kp, -0.35), _at(sp, ns, rs, kp - 12, -0.6)
    _veil(cv, pa, pb, 238 + 10 * p.stream, 34 - 3 * p.stream, 7.0, p, 0.7, name="pecveil", edge=TEAL, sep="deep")
    # ---- head ----
    hdeg = p.rot + p.head
    mouth_c, eye_at, _snout, crown = _head(cv, H, hdeg, p, hide, frame)
    _eye(cv, eye_at, p)
    # a small crown constellation on the head
    lit_crown = p.lights > 0.2 and not (p.flicker and frame % 2 == 0)
    cr = [(math.floor(q[0]), math.floor(q[1])) for q in crown]
    for a, b in zip(cr, cr[1:]):
        cv.line(a, b, CLINE if not p.dim else DIM.light, decal=True, clip="skull", name="skull")
    for j, (x, y) in enumerate(cr):
        if lit_crown and px.hash01("nlev_cr", j) < p.lights:
            if (j + p.pulse) % 2 == 0:
                cv.pixels([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], STAR_G, decal=True, clip="skull",
                          name="skull")
            cv.pixel(x, y, STAR_W, decal=True, clip="skull", name="skull")
        else:
            cv.pixel(x, y, STAR_OFF, decal=True, clip="skull", name="skull")

    # ---- FX ----
    if p.spiral:
        _spirals(back, mouth_c, p.spiral, frame)
    if p.breath is not None:
        fx = cv.layer(above=True, outline=False)
        top = cv.layer(above=True, outline=False)
        _breath(fx, top, mouth_c, hdeg * 0.5, p.breath, frame)
