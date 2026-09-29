"""Ray-cast solids into a layer, cast at SS x SS samples a pixel, and resolve, shade and outline them (decision 42: the
figure drawn better at the same 38 px).

A layer (one item's band in one frame) holds, per pixel, the material most of its samples hit, its tone, part and
outline. Solids are spheres, ellipsoids and tapered elliptic cones (limbs, sleeves, trouser legs, skirts), each with an
optional clip and paint in its own frame, so a belt, a collar or a cuff is a region of the garment wherever the pose
puts it. Colour comes last (render.colourize), so one cast serves every dye.

  - Coverage. Each pixel is cast at SS x SS samples (`Fine`). The pixel takes the material most of its samples hit
    (thin detail such as trim and a blade votes extra, so it keeps an unbroken line), is solid from half coverage (thin
    materials from a quarter), and is shaded by the mean light over its samples, so a tone edge follows the form, not
    the noise of pixel centres (`resolve`).
  - Light (`shade`). Five lit steps of a seven-step ramp (render.ramp7) from the sun in the north-west (a material may
    set its own thresholds, as the skin and hair do), a warm rim where a form's edge turns toward the sun, a cool
    bounce where its shaded edge turns down toward the bright floor, and a contact shade under and beside every nearer
    part (an arm against the trunk, one leg against the other). The top two steps are for materials allowed a light
    (`hi`) and a sheen or glint (`glossy`).
  - Outlines (`outline`). Selective: an outer edge takes a dark tint of the material it bounds (render.colourize),
    deepest on the shaded lower-right and a step lighter on the lit upper-left; an inner edge, where a part overlaps
    the body, takes the part's own core shadow. Stair-steps are anti-aliased within the pixel style: a half-alpha pixel
    where the true edge crosses a stair's inner corner, a softer one at a convex tip. There is no blur.

Everything is nearest-neighbour and deterministic.
"""
from __future__ import annotations

import numpy as np

from .geom import LIGHT, SCALE, SCR_D, SCR_R, TOWARD

W, H = 128, 112          # the working canvas
AX, AY = 64, 80          # the feet (the anchor) on it
SS = 4                   # samples per pixel on a side

# Mean N.L at each lit step: below the first, step 1 (the core shadow); from the last, step 5 (bright).
THRESH = (-0.4, 0.0, 0.34, 0.66)

OUT_NONE, OUT_INK, OUT_SOFT, OUT_INNER, OUT_AA = 0, 1, 2, 3, 4


class Solid:
    """One primitive. kind: sphere (c, r), ellipsoid (c, M, radii), cone (c, M, length, a0, a1, k: the elliptic ratio
    of the cross-section's second axis). `mat` is a material name, or `paint(local, world, normal) -> (names, bias)`
    decides it per sample in the solid's frame (`frame` = (origin, M), M's columns its axes in the world). `clip(local)`
    keeps the hits it returns True for. `part` groups solids for the contact shade; `band` is back, mid, head or
    front."""

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


class Fine:
    """One band cast at the sample grid: per sample the nearest solid's depth, material, part, paint bias and normal,
    and the box of samples anything was cast into."""

    def __init__(self):
        FH, FW = H * SS, W * SS
        self.depth = np.full((FH, FW), -np.inf)
        self.mat = np.full((FH, FW), -1, dtype=np.int16)
        self.part = np.full((FH, FW), -1, dtype=np.int16)
        self.bias = np.zeros((FH, FW), dtype=np.float32)
        self.nrm = np.zeros((FH, FW, 3), dtype=np.float32)
        self.box = None          # (y0, y1, x0, x1) in samples

    def grow(self, y0, y1, x0, x1) -> None:
        b = self.box
        self.box = (y0, y1, x0, x1) if b is None else (min(b[0], y0), max(b[1], y1), min(b[2], x0), max(b[3], x1))


class Layer:
    """One band of one item in one frame at the pixel grid: material, part, coverage, light, tone and outline."""

    def __init__(self):
        self.mat = np.full((H, W), -1, dtype=np.int16)
        self.part = np.full((H, W), -1, dtype=np.int16)
        self.s = np.zeros((H, W), dtype=np.float32)          # the mean N.L over the pixel's samples of its material
        self.bias = np.zeros((H, W), dtype=np.float32)       # the mean paint bias over them
        self.depth = np.full((H, W), -np.inf)
        self.near = np.zeros((H, W), dtype=np.float32)       # how much of the pixel lies within a pixel of the form
        self.rim = np.zeros((H, W), dtype=bool)
        self.bounce = np.zeros((H, W), dtype=bool)
        self.tone = np.zeros((H, W), dtype=np.int8)          # 0..6 (render.ramp7)
        self.out = np.zeros((H, W), dtype=np.int8)           # outline code
        self.out_mat = np.full((H, W), -1, dtype=np.int16)   # the material an outline bounds
        self.alpha = np.full((H, W), 255, dtype=np.uint8)    # < 255 only on an anti-aliasing outline pixel

    def opaque(self) -> np.ndarray:
        return self.mat >= 0

    def empty(self) -> bool:
        return not bool((self.mat >= 0).any()) and not bool((self.out > 0).any())


class Caster:
    """Casts solids into a band's samples. Material names map to small ids through `mats` (shared by every layer of an
    item)."""

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

    def cast(self, fine: Fine, s: Solid) -> None:
        S = SCALE * SS
        FAX, FAY = AX * SS, AY * SS
        FH, FW = fine.mat.shape
        c, rad = s.bound()
        rad *= S
        sx, sy = float(c @ SCR_R) * S, float(c @ SCR_D) * S
        x0 = max(0, int(np.floor(sx - rad - 1)) + FAX)
        x1 = min(FW, int(np.ceil(sx + rad + 1)) + FAX + 1)
        y0 = max(0, int(np.floor(sy - rad - 1)) + FAY)
        y1 = min(FH, int(np.ceil(sy + rad + 1)) + FAY + 1)
        if x0 >= x1 or y0 >= y1:
            return
        jj, ii = np.mgrid[y0:y1, x0:x1]
        px = (ii + 0.5 - FAX).ravel() / S
        py = (jj + 0.5 - FAY).ravel() / S
        B = px[:, None] * SCR_R[None, :] + py[:, None] * SCR_D[None, :]
        t, n, ok = _intersect(s, B)
        if not ok.any():
            return
        P = B + np.where(ok, t, 0.0)[:, None] * TOWARD[None, :]
        if s.clip is not None or s.paint is not None:
            o, M = s.frame if s.frame is not None else (s.geo["c"], s.geo.get("M", np.eye(3)))
            loc = (P - o) @ M
        if s.clip is not None:
            ok &= s.clip(loc)
        names, bias = s.paint(loc, P, n) if s.paint is not None else (None, None)
        ys, xs = jj.ravel(), ii.ravel()
        win = ok & (t > fine.depth[ys, xs])
        if not win.any():
            return
        yw, xw = ys[win], xs[win]
        fine.depth[yw, xw] = t[win]
        if names is None:
            fine.mat[yw, xw] = self.mid(s.mat)
            fine.bias[yw, xw] = s.bias
        else:
            names = np.asarray(names, dtype=object)[win]
            uniq = sorted(set(names.tolist()))
            ids = np.zeros(len(names), dtype=np.int16)
            for nm in uniq:
                ids[names == nm] = self.mid(nm)
            fine.mat[yw, xw] = ids
            fine.bias[yw, xw] = np.asarray(bias, dtype=np.float32)[win] + s.bias
        fine.part[yw, xw] = self.pid(s.part or s.mat)
        fine.nrm[yw, xw] = n[win]
        fine.grow(int(yw.min()), int(yw.max()) + 1, int(xw.min()), int(xw.max()) + 1)


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


def smooth_normals(fine: Fine, part_id: int, centre, M, radii) -> None:
    """Shade a part as one smooth form: its samples take the normal of one ellipsoid (`centre`, axes `M`, `radii`) at
    the point they hit, so the seam where two solids meet (the skull and the jaw) does not crease the shading."""
    sel = fine.part == part_id
    if not sel.any():
        return
    S = SCALE * SS
    jj, ii = np.nonzero(sel)
    px = (ii + 0.5 - AX * SS) / S
    py = (jj + 0.5 - AY * SS) / S
    P = px[:, None] * SCR_R[None, :] + py[:, None] * SCR_D[None, :] + fine.depth[jj, ii][:, None] * TOWARD[None, :]
    M = np.asarray(M, float)
    r = np.asarray(radii, float)
    loc = ((P - np.asarray(centre, float)) @ M) / r
    n = (loc / r) @ M.T
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    fine.nrm[jj, ii] = n


# ------------------------------------------------------------------ resolving the samples
def _blocks(a: np.ndarray) -> np.ndarray:
    """(h*SS, w*SS[, c]) samples as (h, w, SS*SS[, c]) per pixel."""
    h, w = a.shape[0] // SS, a.shape[1] // SS
    if a.ndim == 2:
        return a.reshape(h, SS, w, SS).swapaxes(1, 2).reshape(h, w, SS * SS)
    return a.reshape(h, SS, w, SS, a.shape[2]).swapaxes(1, 2).reshape(h, w, SS * SS, a.shape[2])


def _dilate(on: np.ndarray, r: int) -> np.ndarray:
    """A boolean mask grown by a disc of radius r (in samples)."""
    Hh, Ww = on.shape
    pad = np.zeros((Hh + 2 * r, Ww + 2 * r), dtype=bool)
    pad[r:r + Hh, r:r + Ww] = on
    out = np.zeros_like(on)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= pad[r + dy:r + dy + Hh, r + dx:r + dx + Ww]
    return out


def resolve(fine: Fine, weight: dict, thin: set, line: set = frozenset()) -> Layer:
    """A band's samples as pixels (the module doc: coverage). `weight` {material id: its vote}; `thin` the material ids
    solid from a quarter of a pixel; `line` those solid from a quarter of a pixel too unless the pixel is the fainter
    side of a line its neighbour holds, so a line about a pixel wide (a string, a ripple, a stroke of ink, a sheet of
    light seen edge on) stays unbroken and one pixel wide, two only where it straddles two pixels evenly. The work is
    cut to the box the band was cast into, two pixels round."""
    L = Layer()
    if fine.box is None:
        return L
    y0 = max(0, fine.box[0] // SS - 2)
    y1 = min(H, -(-fine.box[1] // SS) + 2)
    x0 = max(0, fine.box[2] // SS - 2)
    x1 = min(W, -(-fine.box[3] // SS) + 2)
    fy, fx = slice(y0 * SS, y1 * SS), slice(x0 * SS, x1 * SS)
    fmat = fine.mat[fy, fx]
    mat = _blocks(fmat)
    hit = mat >= 0
    cov = hit.mean(-1)
    L.near[y0:y1, x0:x1] = _blocks(_dilate(fmat >= 0, SS)).mean(-1)
    ids = np.unique(fmat[fmat >= 0])
    if ids.size == 0:
        return L
    counts = np.stack([(mat == m).sum(-1) * float(weight.get(int(m), 1.0)) for m in ids], -1)
    best = ids[np.argmax(counts, -1)].astype(np.int16)
    thr = np.where(np.isin(best, np.array(sorted(thin), dtype=np.int16)), 0.24, 0.5)
    on = (cov >= thr) & (cov > 0)
    if line:
        # A line's pixel from a quarter covered, unless it is the fainter edge of a line that a neighbour holds: a
        # neighbour more covered on one side and next to nothing on the other.
        cand = np.isin(best, np.array(sorted(line), dtype=np.int16)) & (cov >= 0.24) & (cov < 0.5)
        pad = np.pad(cov, 1)
        lf, rt, up, dn = pad[1:-1, :-2], pad[1:-1, 2:], pad[:-2, 1:-1], pad[2:, 1:-1]
        edge = ((lf > cov) & (rt < 0.24)) | ((rt > cov) & (lf < 0.24)) | ((up > cov) & (dn < 0.24)) | \
               ((dn > cov) & (up < 0.24))
        on |= cand & ~edge
    best = np.where(on, best, -1).astype(np.int16)
    sel = (mat == best[..., None]) & on[..., None]
    k = np.maximum(sel.sum(-1), 1)
    nrm = _blocks(fine.nrm[fy, fx])
    nl = nrm @ LIGHT
    nv = nrm @ TOWARD
    L.s[y0:y1, x0:x1] = (nl * sel).sum(-1) / k
    L.bias[y0:y1, x0:x1] = (_blocks(fine.bias[fy, fx]) * sel).sum(-1) / k
    L.depth[y0:y1, x0:x1] = np.where(sel, _blocks(fine.depth[fy, fx]), -np.inf).max(-1)
    edge = (1.0 - nv) > 0.62
    L.rim[y0:y1, x0:x1] = (((edge & (nl > 0.12)) & sel).sum(-1) / k) > 0.3
    L.bounce[y0:y1, x0:x1] = (((edge & (nl < -0.15) & (nrm[..., 2] < 0.25)) & sel).sum(-1) / k) > 0.4
    part = _blocks(fine.part[fy, fx])
    pids = np.unique(fine.part[fy, fx][fine.part[fy, fx] >= 0])
    pc = np.stack([((part == p) & sel).sum(-1) for p in pids], -1)
    L.part[y0:y1, x0:x1] = np.where(on, pids[np.argmax(pc, -1)], -1)
    L.mat[y0:y1, x0:x1] = best
    return L


# ------------------------------------------------------------------ shading
def shade(layer: Layer, hi: set, flat: dict, glossy: set, th: dict | None = None) -> None:
    """Tones 1-5 from the light and the paint's bias, the contact shade, the rim and bounce; 5 only on a material
    allowed a light (`hi`), 6 only on one allowed a sheen or a glint (`glossy`). `flat` maps a material id to a fixed
    tone; `th` a material id to its own four thresholds."""
    m = layer.mat
    on = m >= 0
    tone = np.ones(m.shape, dtype=np.int16)
    for t in THRESH:
        tone += (layer.s >= t)
    for mid, ths in (th or {}).items():
        sel = m == mid
        if sel.any():
            tt = np.ones(m.shape, dtype=np.int16)
            for t in ths:
                tt += (layer.s >= t)
            tone = np.where(sel, tt, tone)
    tone += np.round(layer.bias).astype(np.int16)
    # Contact shade: under a nearer part of another piece (a pixel deep), and beside one (an arm against the trunk,
    # one leg against the other): a line of shade where the nearer part stands off.
    up_part = np.full_like(layer.part, -1)
    up_part[1:] = layer.part[:-1]
    up_depth = np.full_like(layer.depth, -np.inf)
    up_depth[1:] = layer.depth[:-1]
    contact = on & (up_part >= 0) & (up_part != layer.part) & (up_depth > layer.depth + 1.2)
    for dx in (-1, 1):
        nb_part = np.full_like(layer.part, -1)
        nb_depth = np.full_like(layer.depth, -np.inf)
        if dx > 0:
            nb_part[:, dx:], nb_depth[:, dx:] = layer.part[:, :-dx], layer.depth[:, :-dx]
        else:
            nb_part[:, :dx], nb_depth[:, :dx] = layer.part[:, -dx:], layer.depth[:, -dx:]
        contact |= on & (nb_part >= 0) & (nb_part != layer.part) & (nb_depth > layer.depth + 1.5)
    tone -= contact.astype(np.int16)
    # The rim: a warm step up where the form turns to the sun at its edge; the bounce: a cool one on the shaded edge.
    tone += (layer.rim & ~contact & (tone < 5)).astype(np.int16)
    tone += (layer.bounce & ~contact & (tone <= 2)).astype(np.int16)
    is_hi = np.isin(m, np.array(sorted(hi), dtype=np.int16))
    is_gl = np.isin(m, np.array(sorted(glossy), dtype=np.int16))
    top = np.where(is_gl, 6, np.where(is_hi, 5, 4))
    tone = np.clip(tone, 1, top)
    fixed = np.zeros(m.shape, dtype=bool)
    for mid, ft in flat.items():
        sel = m == mid
        tone = np.where(sel, ft, tone)
        fixed |= sel
    tone = _clean(m, tone)
    layer.tone = np.where(on, tone, 0).astype(np.int8)
    layer.rim &= on & ~contact & ~fixed
    layer.bounce &= on & ~contact & ~fixed


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


# ------------------------------------------------------------------ outlines
def outline(layer: Layer, inner_mask: np.ndarray, ink: set, glow: set, aa: bool = True) -> None:
    """The selective outline (the module doc). Codes: OUT_INK (the shaded side), OUT_SOFT (the lit side), OUT_INNER
    (over the figure, `inner_mask`: the part's own core shadow), OUT_AA (a stair's corner, half alpha). An `ink`
    material's edge over the figure stays an outer line; a `glow` material's edge is always its own tone (light has no
    ink)."""
    on = layer.mat >= 0
    Hh, Ww = on.shape
    pad = np.zeros((Hh + 2, Ww + 2), dtype=bool)
    pad[1:-1, 1:-1] = on
    left, right, up, down = pad[1:-1, 0:-2], pad[1:-1, 2:], pad[0:-2, 1:-1], pad[2:, 1:-1]
    ul, ur, dl, dr = pad[0:-2, 0:-2], pad[0:-2, 2:], pad[2:, 0:-2], pad[2:, 2:]
    edge = ~on & (left | right | up | down)
    diag = ~on & ~edge & (ul | ur | dl | dr)
    shaded = left | up | ul
    code = np.where(shaded, OUT_INK, OUT_SOFT).astype(np.int8)
    # the material the edge bounds: below, right, left, above first, then the corners
    padm = np.full((Hh + 2, Ww + 2), -1, dtype=np.int16)
    padm[1:-1, 1:-1] = layer.mat
    nm = np.full((Hh, Ww), -1, dtype=np.int16)
    for sl in ((slice(2, None), slice(1, -1)), (slice(1, -1), slice(2, None)), (slice(1, -1), slice(0, -2)),
               (slice(0, -2), slice(1, -1)), (slice(2, None), slice(2, None)), (slice(2, None), slice(0, -2)),
               (slice(0, -2), slice(2, None)), (slice(0, -2), slice(0, -2))):
        cand = padm[sl]
        nm = np.where((nm < 0) & (cand >= 0), cand, nm)
    inner = edge & inner_mask
    if ink:
        inner &= ~np.isin(nm, np.array(sorted(ink), dtype=np.int16))
    is_glow = np.isin(nm, np.array(sorted(glow), dtype=np.int16)) if glow else np.zeros((Hh, Ww), dtype=bool)
    inner |= edge & is_glow
    code = np.where(inner, OUT_INNER, code)
    out = np.where(edge, code, OUT_NONE).astype(np.int8)
    alpha = np.full((Hh, Ww), 255, dtype=np.uint8)
    if aa:
        # A stair's inner corner: a pixel touching the form only at a corner, most of it within a pixel of the true
        # edge, takes the outline at half alpha (not over the figure, where the layer under it shows).
        corner = diag & (layer.near >= 0.5) & ~inner_mask & ~is_glow
        out = np.where(corner, OUT_AA, out).astype(np.int8)
        alpha = np.where(corner, 128, alpha).astype(np.uint8)
        # A convex tip whose pixel lies mostly beyond a pixel from the true edge: its outline softens.
        tip = edge & ~inner & ~inner_mask & (layer.near < 0.4)
        alpha = np.where(tip, 153, alpha).astype(np.uint8)
    layer.out = out
    layer.out_mat = np.where(out > 0, nm, -1).astype(np.int16)
    layer.alpha = alpha
