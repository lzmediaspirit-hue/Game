"""A foe's sculpture and its picture: the pose model the species draw with, and the character's renderer turned on it
(decision 43: the foes brought up to the characters' quality; art bible §13 has the renderer's rules, §8 the foes').

A creature is posed as a small sculpture in its own frame (a forward, b to its left, c up, in art px at size 1):
ellipsoids, spheres and tapered limbs, each with a material and a group, and optionally a paint (a pattern that picks
the material and a tone bias per sample, in the creature's frame, so a stripe or a plate stays on the body as it rolls
over) and a clip. Marks (eyes, nostrils, tusks) are single pixels on the surface where it shows; loose points (a
splash, dust, motes) and glow (a ring of Qi, a glint) are laid on after the outline and take none.

The picture is cast by the character's own rasteriser (figure/raster.py) and coloured by its renderer
(figure/render.py), so a foe gets everything the figure does: 4 x 4 samples a pixel, the seven-step ramps leaning
toward the art bible's sun and shadow (§14.2), the warm rim, the cool bounce and the contact shade, the tinted outline
a step lighter on the lit side, and half-alpha stair corners. What differs is kept here:

  - The camera. A foe is seen from 35 degrees above the ground (the figure from 22), so a back, a shell or a crest
    reads. The sculpture is tilted by the difference before it is cast, which is the same picture through the higher
    camera, and the sun keeps its place against the view.
  - The inner line. A foe is one cast (the figure is cast in bands). Where a part stands in front of another (a leg
    over the belly, a claw over the shell, the head over the shoulders) the pixel behind its edge takes the nearer
    part's core shadow: the figure's lighter inner line, found by depth.
  - The elite. A darker ramp (toward the §14 shadow), gold eyes and a broken ring of pale gold Qi round the outline,
    with motes rising off it (`Look.elite`).

No randomness: a rebuild is byte-identical.
"""
from __future__ import annotations

import math

import numpy as np

from figure import geom, raster, render

ELEV = 35.0                                              # degrees: the foes' camera over the ground
TILT = math.degrees(geom.ELEV) - ELEV                     # the sculpture's tilt onto the figure's camera
RX = geom.rot((1.0, 0.0, 0.0), TILT)
# The creature's feet on the working canvas (raster.W x raster.H): room over them for the puppet's crown and the
# snapper's raised crusher, under them for the eel's water.
FOOT = (raster.W // 2, raster.H - 40)
INNER_DEPTH = 1.6                                        # figure units: a nearer part's edge over another casts a line

IDENT = np.eye(3)


def rot(axis: str, deg: float) -> np.ndarray:
    """A rotation about the creature's a (roll: positive lifts its left side), b (pitch: positive lifts the nose) or c
    (yaw: positive turns a toward b)."""
    t = math.radians(deg)
    co, si = math.cos(t), math.sin(t)
    if axis == "c":
        return np.array([[co, -si, 0.0], [si, co, 0.0], [0.0, 0.0, 1.0]])
    if axis == "b":
        return np.array([[co, 0.0, -si], [0.0, 1.0, 0.0], [si, 0.0, co]])
    return np.array([[1.0, 0.0, 0.0], [0.0, co, -si], [0.0, si, co]])


def v3(*a) -> np.ndarray:
    return np.array(a[0] if len(a) == 1 else a, dtype=float)


def lerp(a, b, t):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * t


class Part:
    """A solid of the sculpture. kind `ell` (at, radii along m's columns), `sph` (at, r) or `limb` (a tapered cone
    from p0 to p1, radii r0 to r1, capped by spheres). `paint(q, n) -> (names, bias)` gets the hit points and normals
    in the creature's frame; `clip(q)` keeps the hits it returns True for. `line`: whether its edge over another part
    draws an inner line."""

    def __init__(self, kind, mat, group, paint=None, clip=None, line=True, **geo):
        self.kind, self.mat, self.group, self.paint, self.clip, self.line = kind, mat, group, paint, clip, line
        self.geo = {k: (np.asarray(v, float) if k in ("at", "radii", "m", "p0", "p1") else v) for k, v in geo.items()}


def E(at, radii, mat, group, m=None, paint=None, clip=None, line=True) -> Part:
    return Part("ell", mat, group, paint, clip, line, at=at, radii=radii, m=IDENT if m is None else m)


def S(at, r, mat, group, paint=None, clip=None, line=True) -> Part:
    return Part("sph", mat, group, paint, clip, line, at=at, r=float(r))


def L(p0, p1, r0, r1, mat, group, paint=None, clip=None, line=True, caps=True) -> Part:
    return Part("limb", mat, group, paint, clip, line, p0=p0, p1=p1, r0=float(r0), r1=float(r1), caps=caps)


def chain(pts, r0: float, r1: float, mat, group, **kw) -> list:
    """Limbs through the points `pts` (a leg, a stalk, a tail), the radius tapering r0 to r1 along them."""
    out = []
    n = len(pts) - 1
    for i in range(n):
        out.append(L(pts[i], pts[i + 1], r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n, mat, group, **kw))
    return out


class Pose:
    """A posed creature: its parts, marks and loose points in its own frame, and the body transform (a roll or a lift
    for a fall: `m`, `shift`), all at size 1; `k` is the size the sheet draws it at."""

    def __init__(self):
        self.k = 1.0
        self.parts: list = []
        self.marks: list = []     # (point, rgba): a pixel on the surface where it shows
        self.fx: list = []        # (point, rgba): loose, after the outline, only where nothing is drawn
        self.glow: list = []      # (point, rgba): light, after the outline, over anything
        self.m = IDENT
        self.shift = np.zeros(3)
        self.water = None         # a creature in the water: the surface's height in the world (art px from the feet)
        self.water_fx = None      # water_fx(a, b) -> rgba or None: the surface round it, in its frame (a, b at size 1)
        self.dissolve = 0.0       # 0..1: the share of its pixels gone to motes (a death coming apart)
        self.dissolve_col = None  # the motes' colour

    def add(self, *parts) -> None:
        for p in parts:
            if isinstance(p, (list, tuple)):
                self.parts += list(p)
            else:
                self.parts.append(p)

    def mark(self, at, col) -> None:
        self.marks.append((np.asarray(at, float), col))

    def squash(self, sa: float, sb: float, sc: float, pivot=(0.0, 0.0, 0.0)) -> None:
        """Squash and stretch about `pivot` (the feet, or the point that stays put): every part, mark and point scaled
        along a, b and c. A part turned off the axes keeps its axes (re-squared) and takes the scale along each."""
        s = np.array((sa, sb, sc), float)
        pv = np.asarray(pivot, float)

        def pt(p):
            return pv + (np.asarray(p, float) - pv) * s

        for p in self.parts:
            g = p.geo
            if p.kind == "ell":
                g["at"] = pt(g["at"])
                ax = g["m"] * s[:, None]
                lens = np.linalg.norm(ax, axis=0)
                g["radii"] = g["radii"] * lens
                q, _ = np.linalg.qr(ax / lens)
                g["m"] = q * np.sign(np.diag(q.T @ (ax / lens)))[None, :]
            elif p.kind == "sph":
                g["at"] = pt(g["at"])
                g["r"] = g["r"] * float(np.cbrt(sa * sb * sc))
            else:
                d = np.asarray(g["p1"]) - np.asarray(g["p0"])
                dn = d / max(1e-9, float(np.linalg.norm(d)))
                across = float(np.sqrt(max(1e-9, (sa * sb * sc) / max(1e-9, float(np.linalg.norm(dn * s))))))
                g["p0"], g["p1"] = pt(g["p0"]), pt(g["p1"])
                g["r0"], g["r1"] = g["r0"] * across, g["r1"] * across
        self.marks = [(pt(a), c) for a, c in self.marks]
        self.fx = [(pt(a), c) for a, c in self.fx]
        self.glow = [(pt(a), c) for a, c in self.glow]


# ================================================================================================= looks
class Look:
    """How a species' materials take the light (render.Look's material table: hi, glossy, thin, line, weight, th, rim),
    and its palette (material -> five-step ramp); `elite` darkens the ramps toward the §14 shadow, keeping `accents`
    (eyes, a claw's jade) as they are."""

    def __init__(self, palette: dict, mats: dict | None = None, accents=(), glow=()):
        self.palette = dict(palette)
        self.mats = dict(mats or {})
        self.accents = set(accents)
        self.glow = set(glow)

    def elite(self) -> "Look":
        out = Look({}, self.mats, self.accents, self.glow)
        for name, r in self.palette.items():
            if name in self.accents or name in self.glow:
                out.palette[name] = r
                continue
            out.palette[name] = [_darken(c, 0.30 - 0.03 * i) for i, c in enumerate(r)]
        return out


def _darken(c, t: float) -> tuple:
    """A colour toward the §14 shadow and a little deeper: the elite's ramp."""
    sh = render.SHADOW
    return tuple(int(round(c[i] * (1 - t) + sh[i] * t * 0.8)) for i in range(3)) + (255,)


# ================================================================================================= the picture
class View:
    """One facing's transforms: creature point -> raster world (the figure's camera) and back."""

    def __init__(self, P: Pose, yaw_deg: float):
        y = math.radians(yaw_deg)
        self.fwd = np.array((math.cos(y), math.sin(y), 0.0))
        self.left = np.array((math.sin(y), -math.cos(y), 0.0))
        yaw = np.stack([self.fwd, self.left, np.array((0.0, 0.0, 1.0))], axis=1)
        self.k = P.k
        self.s = P.k / geom.SCALE
        self.Q = RX @ yaw @ P.m
        self.yaw = yaw
        # The feet at FOOT on the canvas: the world origin moved off the raster's anchor along the screen.
        off = geom.SCR_R * ((FOOT[0] - raster.AX) / geom.SCALE) + geom.SCR_D * ((FOOT[1] - raster.AY) / geom.SCALE)
        self.off = off
        self.b = self.s * (RX @ yaw @ np.asarray(P.shift, float)) + off
        self.A = self.s * self.Q
        self.shift = np.asarray(P.shift, float)
        self.Pm = P.m

    def r(self, p) -> np.ndarray:
        return self.A @ np.asarray(p, float) + self.b

    def pixel(self, p) -> tuple:
        q = self.r(p)
        return (int(math.floor(float(q @ geom.SCR_R) * geom.SCALE + raster.AX)),
                int(math.floor(float(q @ geom.SCR_D) * geom.SCALE + raster.AY)), float(q @ geom.TOWARD))

    def world_z(self, q: np.ndarray) -> np.ndarray:
        """Heights in the world (art px over the feet) of creature points (N x 3)."""
        return self.k * (q @ self.Pm.T + self.shift)[:, 2]


def _solids(P: Pose, V: View) -> list:
    frame = (V.b, V.Q / V.s)
    out = []
    for p in P.parts:
        g = p.geo
        kw = {"part": p.group}
        if p.paint is not None:
            fn = p.paint

            def paint(loc, W, n, fn=fn):
                names, bias = fn(loc, n @ V.Q)
                return names, bias
            kw["paint"] = paint
        if p.clip is not None:
            cf = p.clip
            kw["clip"] = lambda loc, cf=cf: cf(loc)
        if "paint" in kw or "clip" in kw:
            kw["frame"] = frame
        if p.kind == "ell":
            out.append(raster.ellipsoid(V.r(g["at"]), V.Q @ g["m"], g["radii"] * V.s, p.mat, **kw))
        elif p.kind == "sph":
            out.append(raster.sphere(V.r(g["at"]), g["r"] * V.s, p.mat, **kw))
        else:
            a, b = V.r(g["p0"]), V.r(g["p1"])
            if float(np.linalg.norm(b - a)) < 1e-6:
                out.append(raster.sphere(a, max(g["r0"], g["r1"]) * V.s, p.mat, **kw))
                continue
            out.append(raster.cone(a, b, g["r0"] * V.s, g["r1"] * V.s, p.mat, **kw))
            if g.get("caps", True):
                out.append(raster.sphere(a, g["r0"] * V.s, p.mat, **kw))
                out.append(raster.sphere(b, g["r1"] * V.s, p.mat, **kw))
    return out


def picture(P: Pose, yaw_deg: float, look: Look, elite: bool = False, frame_no: int = 0, aura: bool = False) -> np.ndarray:
    """The posed creature seen facing `yaw_deg` on the ground (east 0, south 90): RGBA on the working canvas, its feet
    on FOOT. An elite takes the darker ramp and the ring of Qi; `aura` gives the ring alone (a boss in its own
    colours)."""
    V = View(P, yaw_deg)
    lk = look.elite() if elite else look
    rlook = render.Look(mats=lk.mats, glow=lk.glow)
    caster = raster.Caster([])
    fine = raster.Fine()
    for s in _solids(P, V):
        caster.cast(fine, s)
    info = {m: rlook.info(m) for m in caster.mats}
    weight = {caster.mid(m): float(v.get("weight", 1.0)) for m, v in info.items()}
    thin = {caster.mid(m) for m, v in info.items() if v.get("thin")}
    line = {caster.mid(m) for m, v in info.items() if v.get("line") or m in rlook.glow}
    layer = raster.resolve(fine, weight, thin, line)
    del fine
    hi = {caster.mid(m) for m, v in info.items() if v.get("hi")}
    glossy = {caster.mid(m) for m, v in info.items() if v.get("glossy")}
    th = {caster.mid(m): v["th"] for m, v in info.items() if v.get("th")}
    raster.shade(layer, hi, {}, glossy, th)
    inner = _inner(layer, caster, P)
    glow_ids = {caster.mid(m) for m in rlook.glow}
    raster.outline(layer, np.zeros(layer.mat.shape, dtype=bool), set(), glow_ids)
    paint = render.Paint(caster.mats, lk.palette, rlook)
    rgba = render.colourize(layer, caster.mats, paint).copy()
    # The inner lines: the nearer part's core shadow on the pixel behind its edge.
    for mid, name in enumerate(caster.mats):
        sel = inner == mid
        if sel.any() and name in paint.ramp:
            rgba[sel, :3] = paint.ramp[name][paint.inner[name]]
    # Marks on the surface where it shows.
    on = layer.mat >= 0
    for at, col in P.marks:
        i, j, d = V.pixel(at)
        if 0 <= i < raster.W and 0 <= j < raster.H and on[j, i] and d >= layer.depth[j, i] - 1.0:
            rgba[j, i] = _rgba(col)
    if P.dissolve > 0.0:
        _dissolve(rgba, P, frame_no)
    for at, col in P.fx:
        i, j, _ = V.pixel(at)
        if 0 <= i < raster.W and 0 <= j < raster.H and rgba[j, i, 3] == 0:
            rgba[j, i] = _rgba(col)
    if P.water is not None and P.water_fx is not None:
        _water(rgba, P, V)
    for at, col in P.glow:
        i, j, _ = V.pixel(at)
        if 0 <= i < raster.W and 0 <= j < raster.H:
            rgba[j, i] = _over(rgba[j, i], _rgba(col))
    if elite or aura:
        _aura(rgba, frame_no)
    return rgba


def _rgba(col) -> np.ndarray:
    c = tuple(col)
    return np.array(c + (255,) * (4 - len(c)), dtype=np.uint8)


def _over(dst: np.ndarray, src: np.ndarray) -> np.ndarray:
    a = src[3] / 255.0
    if dst[3] == 0:
        return src.copy()
    out = dst.astype(float)
    out[:3] = out[:3] * (1 - a) + src[:3].astype(float) * a
    out[3] = max(float(dst[3]), float(src[3]))
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def _inner(layer, caster, P: Pose) -> np.ndarray:
    """Per pixel, the material of a nearer part whose edge lies beside it (its inner line), else -1."""
    lines = {caster.pid(p.group) for p in P.parts if p.line}
    on = layer.mat >= 0
    Hh, Ww = on.shape
    out = np.full((Hh, Ww), -1, dtype=np.int16)
    pad_p = np.full((Hh + 2, Ww + 2), -1, dtype=np.int16)
    pad_p[1:-1, 1:-1] = layer.part
    pad_d = np.full((Hh + 2, Ww + 2), -np.inf)
    pad_d[1:-1, 1:-1] = layer.depth
    pad_m = np.full((Hh + 2, Ww + 2), -1, dtype=np.int16)
    pad_m[1:-1, 1:-1] = layer.mat
    ids = np.array(sorted(lines), dtype=np.int16) if lines else np.zeros(0, dtype=np.int16)
    for dy, dx in ((-1, 0), (0, -1), (0, 1), (1, 0)):
        qp = pad_p[1 + dy:Hh + 1 + dy, 1 + dx:Ww + 1 + dx]
        qd = pad_d[1 + dy:Hh + 1 + dy, 1 + dx:Ww + 1 + dx]
        qm = pad_m[1 + dy:Hh + 1 + dy, 1 + dx:Ww + 1 + dx]
        near = on & (qp >= 0) & (qp != layer.part) & (qd > layer.depth + INNER_DEPTH) & np.isin(qp, ids)
        out = np.where((out < 0) & near, qm, out)
    return out


def _dissolve(rgba: np.ndarray, P: Pose, f: int) -> None:
    """A body coming apart into motes: its pixels go by a hash, the highest first, a few left as bright motes."""
    a = rgba[..., 3] > 0
    if not a.any():
        return
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    span = max(1, bot - top)
    h = ((xs * 73856093) ^ (ys * 19349663) ^ 0x5bd1e995) % 1000 / 1000.0
    height = (bot - ys) / span
    gone = h * 0.55 + height * 0.45 < P.dissolve * 1.15
    rgba[ys[gone], xs[gone]] = 0
    if P.dissolve_col is None:
        return
    col = _rgba(P.dissolve_col)
    for n in np.nonzero(gone & (h > 0.9))[0]:
        yy = int(ys[n] - 2 - (h[n] - 0.9) * 60.0 * P.dissolve)
        if 0 <= yy < rgba.shape[0] and rgba[yy, xs[n], 3] == 0:
            rgba[yy, xs[n]] = col


def _water(rgba: np.ndarray, P: Pose, V: View) -> None:
    """The surface round a creature in the water, where nothing else is drawn: each pixel's ray meets the water's plane
    (world height P.water), and water_fx colours that point by where it lies in the creature's frame."""
    Hh, Ww = rgba.shape[:2]
    jj, ii = np.nonzero(rgba[..., 3] == 0)
    px = (ii + 0.5 - raster.AX) / geom.SCALE
    py = (jj + 0.5 - raster.AY) / geom.SCALE
    B = px[:, None] * geom.SCR_R[None, :] + py[:, None] * geom.SCR_D[None, :] - V.off[None, :]
    # The world point (before the tilt, at the creature's size) along the ray B + t TOWARD, back through RX.
    Wb = (B @ RX) * geom.SCALE
    Wt = (geom.TOWARD @ RX) * geom.SCALE
    t = (P.water - Wb[:, 2]) / Wt[2]
    hit = Wb + t[:, None] * Wt[None, :]
    a = (hit @ V.fwd) / V.k
    b = (hit @ V.left) / V.k
    for n in range(len(ii)):
        col = P.water_fx(float(a[n]), float(b[n]))
        if col is not None:
            rgba[jj[n], ii[n]] = _rgba(col)


def _aura(rgba: np.ndarray, f: int) -> None:
    """The elite's mark: a broken ring of pale gold Qi round its outline, flickering frame by frame, and motes rising
    off its back."""
    a = rgba[..., 3] > 0
    Hh, Ww = a.shape
    pad = np.zeros((Hh + 2, Ww + 2), dtype=bool)
    pad[1:-1, 1:-1] = a
    ring = ~a & (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:])
    ys, xs = np.nonzero(ring)
    if len(ys) == 0:
        return
    h = ((xs * 2654435761 + ys * 40503 + f * 97) % 997) / 997.0
    top = ys.min()
    keep = h > 0.42
    for y, x, hv in zip(ys[keep], xs[keep], h[keep]):
        up = (y - top) / max(1, (ys.max() - top))
        alpha = int(150 - 70 * up) if hv > 0.8 else int(95 - 40 * up)
        rgba[y, x] = (255, 226, 140, max(40, alpha))
    # Motes: a few specks of gold rising over it, a step higher each frame.
    ay, ax = np.nonzero(a)
    cx = int(round(ax.mean()))
    w = max(4, int((ax.max() - ax.min()) * 0.4))
    for k in range(4):
        x = cx - w + (k * 2 * w) // 3 + (k * 7 + f * 3) % 3
        y = int(ay.min()) - 1 - ((f * 2 + k * 5) % 9)
        if 0 <= x < Ww and 0 <= y < Hh and rgba[y, x, 3] == 0:
            rgba[y, x] = (255, 236, 170, 200 if k % 2 else 150)
