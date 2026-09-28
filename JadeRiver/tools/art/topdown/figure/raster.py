"""Ray-cast solids into a layer at 1 art px per pixel, cel-shade them and outline them.

A layer (one item's band in one frame) holds, per pixel, the nearest solid's material, tone and part. Solids are
spheres, ellipsoids and tapered elliptic cones (limbs, sleeves, trouser legs, skirts), each with an optional clip and
paint in its own frame, so a belt, a collar or a cuff is a region of the garment wherever the pose puts it.
Colour comes last (palettes.colourize), so one cast serves every dye.
"""
from __future__ import annotations

import numpy as np

from .geom import LIGHT, SCALE, SCR_D, SCR_R, TOWARD

W, H = 128, 112          # the working canvas
AX, AY = 64, 80          # the feet (the anchor) on it

# Tones: 0 deep, 1 shadow, 2 base, 3 light, 4 highlight. The light gives 1-4 (N.L thresholds between them); the deep
# tone is kept for contact shade (under a nearer part) and edges.
THRESH = (0.0, 0.42, 0.86)

OUT_NONE, OUT_INK, OUT_SOFT, OUT_INNER = 0, 1, 2, 3


class Solid:
    """One primitive. kind: sphere (c, r), ellipsoid (c, M, radii), cone (c, M, length, a0, a1, k: the elliptic ratio
    of the cross-section's second axis). `mat` is a material name, or `paint(local, world, normal) -> (names, bias)`
    decides it per pixel in the solid's frame (`frame` = (origin, M), M's columns its axes in the world). `clip(local)`
    keeps the hits it returns True for. `part` groups solids for the contact shade; `band` is back, mid or front."""

    def __init__(self, kind, mat, band="mid", part="", paint=None, frame=None, clip=None, bias=0, **geo):
        self.kind = kind
        self.mat = mat
        self.band = band
        self.part = part
        self.paint = paint
        self.frame = frame
        self.clip = clip
        self.bias = bias
        self.geo = geo

    def bound(self):
        g = self.geo
        if self.kind == "sphere":
            return g["c"], g["r"]
        if self.kind == "ellipsoid":
            return g["c"], float(max(g["radii"]))
        mid = g["c"] + g["M"][:, 2] * g["length"] * 0.5
        rad = max(g["a0"], g["a1"]) * max(1.0, g.get("k", 1.0))
        return mid, float(np.hypot(g["length"] * 0.5, rad))


def sphere(c, r, mat, **kw) -> Solid:
    return Solid("sphere", mat, c=np.asarray(c, float), r=float(r), **kw)


def ellipsoid(c, M, radii, mat, **kw) -> Solid:
    return Solid("ellipsoid", mat, c=np.asarray(c, float), M=np.asarray(M, float), radii=np.asarray(radii, float), **kw)


def cone(p0, p1, a0, a1, mat, k=1.0, side=None, **kw) -> Solid:
    """A tapered cone from p0 (radius a0) to p1 (radius a1); `side` orients the elliptic cross-section's first axis."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    ax = p1 - p0
    L = float(np.linalg.norm(ax))
    w = ax / max(L, 1e-9)
    s = np.asarray(side if side is not None else (1.0, 0.0, 0.0), float)
    x = s - w * float(s @ w)
    if float(np.linalg.norm(x)) < 1e-6:
        x = np.cross(w, np.array([0.0, 1.0, 0.0]))
        if float(np.linalg.norm(x)) < 1e-6:
            x = np.cross(w, np.array([1.0, 0.0, 0.0]))
    x = x / np.linalg.norm(x)
    y = np.cross(w, x)
    return Solid("cone", mat, c=p0, M=np.stack([x, y, w], axis=1), length=L, a0=float(a0), a1=float(a1), k=float(k), **kw)


def limb(p0, p1, r0, r1, mat, caps=True, **kw) -> list:
    """A rounded limb: a cone and a sphere at each end."""
    out = [cone(p0, p1, r0, r1, mat, **kw)]
    if caps:
        out.append(sphere(p0, r0, mat, **kw))
        out.append(sphere(p1, r1, mat, **kw))
    return out


class Layer:
    """One band of one item in one frame: per-pixel depth, material, tone, part and normal."""

    def __init__(self):
        self.depth = np.full((H, W), -np.inf)
        self.mat = np.full((H, W), -1, dtype=np.int16)
        self.part = np.full((H, W), -1, dtype=np.int16)
        self.bias = np.zeros((H, W), dtype=np.int8)
        self.nrm = np.zeros((H, W, 3))
        self.tone = np.zeros((H, W), dtype=np.int8)
        self.out = np.zeros((H, W), dtype=np.int8)       # outline code
        self.out_mat = np.full((H, W), -1, dtype=np.int16)  # the material an inner outline darkens

    def opaque(self) -> np.ndarray:
        return self.mat >= 0

    def empty(self) -> bool:
        return not bool((self.mat >= 0).any()) and not bool((self.out > 0).any())


class Caster:
    """Casts solids into layers. Material names map to small ids through `mats` (shared by every layer of an item)."""

    def __init__(self, mats: list):
        self.mats = list(mats)
        self.ids = {m: i for i, m in enumerate(self.mats)}
        self.parts: dict = {}

    def mid(self, name: str) -> int:
        if name not in self.ids:
            self.ids[name] = len(self.mats)
            self.mats.append(name)
        return self.ids[name]

    def pid(self, name: str) -> int:
        if name not in self.parts:
            self.parts[name] = len(self.parts)
        return self.parts[name]

    def cast(self, layer: Layer, s: Solid) -> None:
        c, rad = s.bound()
        rad *= SCALE
        sx, sy = float(c @ SCR_R) * SCALE, float(c @ SCR_D) * SCALE
        x0 = max(0, int(np.floor(sx - rad - 1)) + AX)
        x1 = min(W, int(np.ceil(sx + rad + 1)) + AX + 1)
        y0 = max(0, int(np.floor(sy - rad - 1)) + AY)
        y1 = min(H, int(np.ceil(sy + rad + 1)) + AY + 1)
        if x0 >= x1 or y0 >= y1:
            return
        jj, ii = np.mgrid[y0:y1, x0:x1]
        px = (ii + 0.5 - AX).ravel() / SCALE
        py = (jj + 0.5 - AY).ravel() / SCALE
        B = px[:, None] * SCR_R[None, :] + py[:, None] * SCR_D[None, :]
        t, n, ok = _intersect(s, B)
        if not ok.any():
            return
        P = B + np.where(ok, t, 0.0)[:, None] * TOWARD[None, :]
        if s.clip is not None or s.paint is not None:
            if s.frame is not None:
                o, M = s.frame
            else:
                o, M = s.geo["c"], s.geo.get("M", np.eye(3))
            loc = (P - o) @ M
        if s.clip is not None:
            ok &= s.clip(loc)
        if s.paint is not None:
            names, bias = s.paint(loc, P, n)
        else:
            names, bias = None, None
        ys = jj.ravel()
        xs = ii.ravel()
        cur = layer.depth[ys, xs]
        win = ok & (t > cur)
        if not win.any():
            return
        layer.depth[ys[win], xs[win]] = t[win]
        if names is None:
            layer.mat[ys[win], xs[win]] = self.mid(s.mat)
            layer.bias[ys[win], xs[win]] = s.bias
        else:
            ids = np.array([self.mid(nm) for nm in names], dtype=np.int16)
            layer.mat[ys[win], xs[win]] = ids[win]
            layer.bias[ys[win], xs[win]] = (np.asarray(bias, dtype=np.int16)[win] + s.bias).astype(np.int8)
        layer.part[ys[win], xs[win]] = self.pid(s.part or s.mat)
        layer.nrm[ys[win], xs[win]] = n[win]


def _intersect(s: Solid, B: np.ndarray):
    """The hit nearest the camera for rays B + t*TOWARD: (t, world normal, hit mask)."""
    g = s.geo
    N = B.shape[0]
    if s.kind == "sphere":
        oc = B - g["c"]
        b = oc @ TOWARD
        cc = np.einsum("ij,ij->i", oc, oc) - g["r"] ** 2
        disc = b * b - cc
        ok = disc >= 0
        t = -b + np.sqrt(np.maximum(disc, 0))
        P = B + t[:, None] * TOWARD
        n = (P - g["c"]) / g["r"]
        return np.where(ok, t, -np.inf), np.nan_to_num(n), ok
    if s.kind == "ellipsoid":
        M, r = g["M"], g["radii"]
        o = ((B - g["c"]) @ M) / r
        d = (TOWARD @ M) / r
        qa = float(d @ d)
        qb = 2 * (o @ d)
        qc = np.einsum("ij,ij->i", o, o) - 1
        disc = qb * qb - 4 * qa * qc
        ok = disc >= 0
        t = (-qb + np.sqrt(np.maximum(disc, 0))) / (2 * qa)
        loc = o + t[:, None] * d
        n = (loc / r) @ M.T
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        return np.where(ok, t, -np.inf), np.nan_to_num(n), ok
    # Tapered elliptic cone: x^2 + (y/k)^2 = (a0 + s w)^2 for w in [0, L].
    M, L, a0, a1, k = g["M"], g["length"], g["a0"], g["a1"], g["k"]
    sl = (a1 - a0) / max(L, 1e-9)
    o = (B - g["c"]) @ M
    d = TOWARD @ M
    ik2 = 1.0 / (k * k)
    A = d[0] ** 2 + d[1] ** 2 * ik2 - sl * sl * d[2] ** 2
    rr = a0 + sl * o[:, 2]
    Bq = 2 * (o[:, 0] * d[0] + o[:, 1] * d[1] * ik2 - sl * d[2] * rr)
    C = o[:, 0] ** 2 + o[:, 1] ** 2 * ik2 - rr ** 2
    t = np.full(N, -np.inf)
    ok = np.zeros(N, dtype=bool)
    if abs(A) < 1e-9:
        return t, np.zeros((N, 3)), ok
    disc = Bq * Bq - 4 * A * C
    good = disc >= 0
    sq = np.sqrt(np.maximum(disc, 0))
    r1 = (-Bq + sq) / (2 * A)
    r2 = (-Bq - sq) / (2 * A)
    hi = np.maximum(r1, r2)
    lo = np.minimum(r1, r2)
    for cand in (hi, lo):
        w = o[:, 2] + cand * d[2]
        rad = a0 + sl * w
        take = good & ~ok & (w >= 0) & (w <= L) & (rad > 0)
        t = np.where(take, cand, t)
        ok |= take
    tt = np.where(ok, t, 0.0)
    loc = o + tt[:, None] * d
    rad = a0 + sl * loc[:, 2]
    gn = np.stack([loc[:, 0], loc[:, 1] * ik2, -sl * rad], axis=1)
    n = gn @ M.T
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    return t, n, ok


def shade(layer: Layer, highlight: set, flat: dict, thresholds: dict | None = None) -> None:
    """Tones from the light, the solids' bias and a contact shade under anything nearer that belongs to another part.
    `highlight` holds the material ids allowed tone 4; `flat` maps a material id to a fixed tone."""
    m = layer.mat
    on = m >= 0
    s = layer.nrm @ LIGHT
    tone = np.ones(m.shape, dtype=np.int16)
    for th in THRESH:
        tone += (s >= th)
    if thresholds:
        for mid, th in thresholds.items():
            sel = m == mid
            if sel.any():
                tt = np.ones(m.shape, dtype=np.int16)
                for x in th:
                    tt += (s >= x)
                tone = np.where(sel, tt, tone)
    tone += layer.bias
    # Contact shade: the pixel under a nearer solid of another part sits in its shadow.
    up_part = np.full_like(layer.part, -1)
    up_part[1:] = layer.part[:-1]
    up_depth = np.full_like(layer.depth, -np.inf)
    up_depth[1:] = layer.depth[:-1]
    contact = on & (up_part >= 0) & (up_part != layer.part) & (up_depth > layer.depth + 1.2)
    tone -= contact.astype(np.int16)
    hl = np.zeros(m.shape, dtype=bool)
    for mid in highlight:
        hl |= m == mid
    tone = np.where(hl, np.clip(tone, 0, 4), np.clip(tone, 0, 3))
    for mid, ft in flat.items():
        tone = np.where(m == mid, ft, tone)
    tone = _clean(m, tone)
    layer.tone = np.where(on, tone, 0).astype(np.int8)


def _clean(m: np.ndarray, tone: np.ndarray) -> np.ndarray:
    """Remove orphan tone pixels: a pixel whose same-material neighbours all share one other tone takes it."""
    t = tone.copy()
    Hh, Ww = m.shape
    pad_m = np.full((Hh + 2, Ww + 2), -1, dtype=m.dtype)
    pad_m[1:-1, 1:-1] = m
    pad_t = np.full((Hh + 2, Ww + 2), -9, dtype=t.dtype)
    pad_t[1:-1, 1:-1] = t
    nbr = []
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nm = pad_m[1 + dy:Hh + 1 + dy, 1 + dx:Ww + 1 + dx]
        nt = pad_t[1 + dy:Hh + 1 + dy, 1 + dx:Ww + 1 + dx]
        nbr.append((nm == m, nt))
    same_cnt = sum(a.astype(int) for a, _ in nbr)
    match_cnt = sum((a & (b == t)).astype(int) for a, b in nbr)
    orphan = (m >= 0) & (same_cnt >= 3) & (match_cnt <= 1)
    if orphan.any():
        # the most common neighbour tone
        cand = np.stack([np.where(a, b, -9) for a, b in nbr], axis=0)
        best = t.copy()
        best_n = np.zeros_like(t)
        for k in range(4):
            v = cand[k]
            n = sum((cand[j] == v).astype(np.int16) for j in range(4))
            better = (v >= 0) & (n > best_n)
            best = np.where(better, v, best)
            best_n = np.where(better, n, best_n)
        t = np.where(orphan & (best_n >= 3), best, t)
    return t


def outline(layer: Layer, inner_mask: np.ndarray, line_mode: dict) -> None:
    """A 1 px outline round the layer's pixels: ink on the shaded (lower-right) side and a softer ink on the lit side
    outside the figure; over the figure (`inner_mask`) the edge takes the material's deepest tone instead, unless the
    material's `line_mode` says ink."""
    on = layer.mat >= 0
    Hh, Ww = on.shape
    pad = np.zeros((Hh + 2, Ww + 2), dtype=bool)
    pad[1:-1, 1:-1] = on
    left = pad[1:-1, 0:-2]
    right = pad[1:-1, 2:]
    up = pad[0:-2, 1:-1]
    down = pad[2:, 1:-1]
    edge = ~on & (left | right | up | down)
    shaded = left | up
    code = np.where(shaded, OUT_INK, OUT_SOFT).astype(np.int8)
    # the material next to the edge (for an inner line): prefer the one above, then left, right, below
    padm = np.full((Hh + 2, Ww + 2), -1, dtype=np.int16)
    padm[1:-1, 1:-1] = layer.mat
    nm = np.full((Hh, Ww), -1, dtype=np.int16)
    for sl in ((slice(2, None), slice(1, -1)), (slice(1, -1), slice(2, None)), (slice(1, -1), slice(0, -2)), (slice(0, -2), slice(1, -1))):
        cand = padm[sl]
        nm = np.where((nm < 0) & (cand >= 0), cand, nm)
    inner = edge & inner_mask
    if line_mode:
        ink_ids = np.array([k for k, v in line_mode.items() if v == "ink"], dtype=np.int16)
        if ink_ids.size:
            inner &= ~np.isin(nm, ink_ids)
        glow_ids = np.array([k for k, v in line_mode.items() if v == "glow"], dtype=np.int16)
        if glow_ids.size:
            inner |= edge & np.isin(nm, glow_ids)     # light has no ink: its edge is its own deeper tone
    code = np.where(inner, OUT_INNER, code)
    layer.out = np.where(edge, code, OUT_NONE).astype(np.int8)
    layer.out_mat = np.where(edge, nm, -1).astype(np.int16)
