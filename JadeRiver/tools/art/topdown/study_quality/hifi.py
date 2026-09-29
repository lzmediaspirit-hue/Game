"""The study's rasteriser (decision 42): the Phase 3 doll (figure/) drawn with more care, at any density.

What changes against figure/raster.py (which stays as it is, for the game):

  - Coverage. Each pixel is cast at `ss` x `ss` samples. The pixel takes the material most of its samples hit (thin
    detail such as trim and the blade counts extra, so it keeps an unbroken line), is solid from half coverage (thin
    parts from a quarter), and is shaded by the mean light over its samples, so tone edges follow the form instead of
    the pixel centres' noise.
  - Ramps. Every five-step ramp becomes seven (`ramp7`): a core shadow between the deep step and the shadow, a bright
    step between the light and the highlight. The dark steps lean toward the §14 shadow's blue-violet (`SHADOW`), the
    light ones toward its sun (`SUN`), so a form turns in hue as well as value.
  - Light. Five lit steps from the sun in the north-west (a material may set its own, as the faces do), a warm rim
    where a form's edge turns toward the sun, a cool bounce where its shaded edge turns down toward the bright floor,
    and a contact shade under and beside every nearer part (two px deep at double density).
  - Outlines. Selective: an outer edge takes a dark tint of the material it bounds (deepest on the shaded lower-right,
    a step lighter on the lit upper-left), never flat black; an inner edge, where a part overlaps the body, takes the
    part's own core shadow. Stair-steps are anti-aliased within the pixel style: a half-alpha pixel where the true
    edge crosses a stair's inner corner, a softer one at a convex tip, never a blur.

Everything is nearest-neighbour and deterministic.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))      # tools/art/topdown

from figure import raster  # noqa: E402
from figure.geom import LIGHT, SCR_D, SCR_R, TOWARD  # noqa: E402
from figure.raster import _intersect  # noqa: E402

SUN = np.array((0xFF, 0xE9, 0xA6), float)       # art bible §14.2
SHADOW = np.array((0x24, 0x1F, 0x4F), float)
SKY = np.array((0x9C, 0xC8, 0xD2), float)       # the bright floor and sky a shaded edge turns toward
INK = np.array((0x0E, 0x1A, 0x1E), float)       # §4's ink-teal

OUT_NONE, OUT_INK, OUT_SOFT, OUT_INNER, OUT_AA = 0, 1, 2, 3, 4
BANDS = ("back", "mid", "head", "front")


class Grid:
    """A drawing density: `scale` art px per figure unit (0.92: the world's, 38 px tall), the working canvas and the
    feet on it, and `ss` samples per pixel on a side."""

    def __init__(self, scale: float, W: int, H: int, AX: int, AY: int, ss: int):
        self.scale, self.W, self.H, self.AX, self.AY, self.ss = scale, W, H, AX, AY, ss
        self.k = scale / 0.92            # the figure's size against the game's (1 for B, 2 for C)
        self.face = "b"                  # the face's glyph set (looks.FACES)

    def project(self, p) -> tuple:
        p = np.asarray(p, float)
        return float(p @ SCR_R) * self.scale, float(p @ SCR_D) * self.scale


# ------------------------------------------------------------------ ramps
def _mix(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def ramp7(r5) -> np.ndarray:
    """A figure ramp (deep, shadow, base, light, highlight) as seven steps, dark end toward SHADOW, light toward SUN:
    0 deep (lines, contact), 1 core shadow (new), 2 shadow, 3 base, 4 light, 5 bright (new), 6 highlight. Every step
    stays a clear step from its neighbours."""
    r = [np.asarray(c[:3], float) for c in r5]
    out = [
        _mix(_mix(r[0], SHADOW, 0.3), (0, 0, 0), 0.15),
        _mix(_mix(r[0], r[1], 0.45), SHADOW, 0.22),
        _mix(r[1], SHADOW, 0.12),
        r[2],
        _mix(r[3], SUN, 0.06),
        _mix(_mix(r[3], r[4], 0.55), SUN, 0.14),
        _mix(r[4], SUN, 0.24),
    ]
    return np.clip(np.round(np.stack(out)), 0, 255)


# ------------------------------------------------------------------ casting
class Fine:
    """One band cast at the fine grid: per sample the nearest solid's depth, material, part, paint bias and normal."""

    def __init__(self, g: Grid):
        FH, FW = g.H * g.ss, g.W * g.ss
        self.depth = np.full((FH, FW), -np.inf)
        self.mat = np.full((FH, FW), -1, dtype=np.int16)
        self.part = np.full((FH, FW), -1, dtype=np.int16)
        self.bias = np.zeros((FH, FW), dtype=np.float32)
        self.nrm = np.zeros((FH, FW, 3), dtype=np.float32)


def cast(g: Grid, fine: Fine, s, caster: raster.Caster) -> None:
    """raster.Caster.cast at the fine grid (the same solids, clips and paint)."""
    S = g.scale * g.ss
    FAX, FAY = g.AX * g.ss, g.AY * g.ss
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
    fine.depth[ys[win], xs[win]] = t[win]
    if names is None:
        fine.mat[ys[win], xs[win]] = caster.mid(s.mat)
        fine.bias[ys[win], xs[win]] = s.bias
    else:
        ids = np.array([caster.mid(nm) for nm in names], dtype=np.int16)
        fine.mat[ys[win], xs[win]] = ids[win]
        fine.bias[ys[win], xs[win]] = np.asarray(bias, dtype=np.float32)[win] + s.bias
    fine.part[ys[win], xs[win]] = caster.pid(s.part or s.mat)
    fine.nrm[ys[win], xs[win]] = n[win]


def smooth_normals(g: Grid, fine: Fine, part_id: int, centre, M, radii) -> None:
    """Shade a part as one smooth form: its samples take the normal of one ellipsoid (`centre`, axes `M`, `radii`)
    at the point they hit, so the seam where two solids meet (the skull and the jaw) does not crease the shading."""
    sel = fine.part == part_id
    if not sel.any():
        return
    S = g.scale * g.ss
    jj, ii = np.nonzero(sel)
    px = (ii + 0.5 - g.AX * g.ss) / S
    py = (jj + 0.5 - g.AY * g.ss) / S
    P = px[:, None] * SCR_R[None, :] + py[:, None] * SCR_D[None, :] + fine.depth[jj, ii][:, None] * TOWARD[None, :]
    loc = ((P - np.asarray(centre, float)) @ np.asarray(M, float)) / np.asarray(radii, float)
    n = (loc / np.asarray(radii, float)) @ np.asarray(M, float).T
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    fine.nrm[jj, ii] = n


# ------------------------------------------------------------------ resolving the samples
class Res:
    """One band at the pixel grid: material, part, tone, flags and outline."""

    def __init__(self, g: Grid):
        H, W = g.H, g.W
        self.mat = np.full((H, W), -1, dtype=np.int16)
        self.part = np.full((H, W), -1, dtype=np.int16)
        self.cov = np.zeros((H, W), dtype=np.float32)
        self.s = np.zeros((H, W), dtype=np.float32)          # mean N.L
        self.bias = np.zeros((H, W), dtype=np.float32)
        self.depth = np.full((H, W), -np.inf)
        self.rim = np.zeros((H, W), dtype=bool)
        self.bounce = np.zeros((H, W), dtype=bool)
        self.tone = np.zeros((H, W), dtype=np.int8)
        self.out = np.zeros((H, W), dtype=np.int8)
        self.out_mat = np.full((H, W), -1, dtype=np.int16)
        self.alpha = np.ones((H, W), dtype=np.float32)        # < 1 only on anti-aliasing pixels
        self.near = np.zeros((H, W), dtype=np.float32)       # how much of the pixel lies within 1 px of the form


def _blocks(a: np.ndarray, g: Grid) -> np.ndarray:
    ss = g.ss
    if a.ndim == 2:
        return a.reshape(g.H, ss, g.W, ss).swapaxes(1, 2).reshape(g.H, g.W, ss * ss)
    return a.reshape(g.H, ss, g.W, ss, a.shape[2]).swapaxes(1, 2).reshape(g.H, g.W, ss * ss, a.shape[2])


def _dilate_fine(on: np.ndarray, r: int) -> np.ndarray:
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


def resolve(g: Grid, fine: Fine, weight: dict, thin: set) -> Res:
    """The samples of a band as pixels (module doc: coverage)."""
    R = Res(g)
    mat = _blocks(fine.mat, g)
    hit = mat >= 0
    R.cov = hit.mean(-1).astype(np.float32)
    ids = np.unique(fine.mat[fine.mat >= 0])
    grown = _dilate_fine(fine.mat >= 0, g.ss)
    R.near = _blocks(grown, g).mean(-1).astype(np.float32)
    if ids.size == 0:
        return R
    counts = np.stack([(mat == m).sum(-1) * float(weight.get(int(m), 1.0)) for m in ids], -1)
    best = ids[np.argmax(counts, -1)].astype(np.int16)
    thr = np.where(np.isin(best, np.array(sorted(thin), dtype=np.int16)), 0.24, 0.5)
    on = (R.cov >= thr) & (R.cov > 0)
    best = np.where(on, best, -1).astype(np.int16)
    sel = (mat == best[..., None]) & on[..., None]
    k = np.maximum(sel.sum(-1), 1)
    nrm = _blocks(fine.nrm, g)
    nl = nrm @ LIGHT
    nv = nrm @ TOWARD
    R.s = ((nl * sel).sum(-1) / k).astype(np.float32)
    R.bias = ((_blocks(fine.bias, g) * sel).sum(-1) / k).astype(np.float32)
    R.depth = np.where(sel, _blocks(fine.depth, g), -np.inf).max(-1)
    edge = (1.0 - nv) > 0.62
    R.rim = (((edge & (nl > 0.12)) & sel).sum(-1) / k) > 0.3
    R.bounce = (((edge & (nl < -0.15) & (nrm[..., 2] < 0.25)) & sel).sum(-1) / k) > 0.4
    part = _blocks(fine.part, g)
    pids = np.unique(fine.part[fine.part >= 0])
    pc = np.stack([((part == p) & sel).sum(-1) for p in pids], -1)
    R.part = np.where(on, pids[np.argmax(pc, -1)], -1).astype(np.int16)
    R.mat = best
    return R


# ------------------------------------------------------------------ shading
THRESH = (-0.4, 0.0, 0.34, 0.66)       # mean N.L -> lit steps 1..5


def shade(g: Grid, R: Res, hi: set, flat: dict, glossy: set, th: dict | None = None) -> None:
    """Tones 1-5 from the light and the paint's bias, the contact shade, the rim and bounce, and 6 only from paint
    (a sheen or a glint) on a material allowed a highlight."""
    m = R.mat
    on = m >= 0
    tone = np.ones(m.shape, dtype=np.int16)
    for t in THRESH:
        tone += (R.s >= t)
    for mid, ths in (th or {}).items():
        sel = m == mid
        if sel.any():
            tt = np.ones(m.shape, dtype=np.int16)
            for t in ths:
                tt += (R.s >= t)
            tone = np.where(sel, tt, tone)
    tone += np.round(R.bias).astype(np.int16)
    # Contact shade: under a nearer part of another piece, as deep as the density (1 px at 38 px, 2 at 76); and beside
    # one (an arm against the trunk, one leg against the other): a line of shade where the nearer part stands off.
    reach = max(1, int(round(g.k)))
    contact = np.zeros(m.shape, dtype=bool)
    for d in range(1, reach + 1):
        up_part = np.full_like(R.part, -1)
        up_part[d:] = R.part[:-d]
        up_depth = np.full_like(R.depth, -np.inf)
        up_depth[d:] = R.depth[:-d]
        contact |= on & (up_part >= 0) & (up_part != R.part) & (up_depth > R.depth + 1.2)
    side = np.zeros(m.shape, dtype=bool)
    for dx in (-1, 1):
        nb_part = np.full_like(R.part, -1)
        nb_depth = np.full_like(R.depth, -np.inf)
        if dx > 0:
            nb_part[:, dx:], nb_depth[:, dx:] = R.part[:, :-dx], R.depth[:, :-dx]
        else:
            nb_part[:, :dx], nb_depth[:, :dx] = R.part[:, -dx:], R.depth[:, -dx:]
        side |= on & (nb_part >= 0) & (nb_part != R.part) & (nb_depth > R.depth + 1.5)
    contact |= side
    tone -= contact.astype(np.int16)
    # The rim: a warm step up where the form turns to the sun at its edge; the bounce: a cool one on the shaded edge.
    tone += (R.rim & ~contact & (tone < 5)).astype(np.int16)
    tone += (R.bounce & ~contact & (tone <= 2)).astype(np.int16)
    is_hi = np.isin(m, np.array(sorted(hi), dtype=np.int16))
    is_gl = np.isin(m, np.array(sorted(glossy), dtype=np.int16))
    top = np.where(is_gl, 6, np.where(is_hi, 5, 4))
    tone = np.clip(tone, 1, top)
    for mid, ft in flat.items():
        tone = np.where(m == mid, ft, tone)
    tone = raster._clean(m, tone)
    R.tone = np.where(on, tone, 0).astype(np.int8)
    R.rim &= on & ~contact
    R.bounce &= on & ~contact


# ------------------------------------------------------------------ outlines
def outline(g: Grid, R: Res, inner_mask: np.ndarray, ink_mats: set, glow_mats: set, aa: bool = True) -> None:
    """The selective outline (module doc). Codes: OUT_INK (shaded side), OUT_SOFT (lit side), OUT_INNER (over the
    body), OUT_AA (a stair's corner, half alpha)."""
    on = R.mat >= 0
    Hh, Ww = on.shape
    pad = np.zeros((Hh + 2, Ww + 2), dtype=bool)
    pad[1:-1, 1:-1] = on
    left, right, up, down = pad[1:-1, 0:-2], pad[1:-1, 2:], pad[0:-2, 1:-1], pad[2:, 1:-1]
    ul, ur, dl, dr = pad[0:-2, 0:-2], pad[0:-2, 2:], pad[2:, 0:-2], pad[2:, 2:]
    edge = ~on & (left | right | up | down)
    diag = ~on & ~edge & (ul | ur | dl | dr)
    shaded = left | up | ul
    code = np.where(shaded, OUT_INK, OUT_SOFT).astype(np.int8)
    padm = np.full((Hh + 2, Ww + 2), -1, dtype=np.int16)
    padm[1:-1, 1:-1] = R.mat
    nm = np.full((Hh, Ww), -1, dtype=np.int16)
    for sl in ((slice(2, None), slice(1, -1)), (slice(1, -1), slice(2, None)), (slice(1, -1), slice(0, -2)),
               (slice(0, -2), slice(1, -1)), (slice(2, None), slice(2, None)), (slice(2, None), slice(0, -2)),
               (slice(0, -2), slice(2, None)), (slice(0, -2), slice(0, -2))):
        cand = padm[sl]
        nm = np.where((nm < 0) & (cand >= 0), cand, nm)
    inner = edge & inner_mask
    if ink_mats:
        inner &= ~np.isin(nm, np.array(sorted(ink_mats), dtype=np.int16))
    if glow_mats:
        inner |= edge & np.isin(nm, np.array(sorted(glow_mats), dtype=np.int16))
    code = np.where(inner, OUT_INNER, code)
    out = np.where(edge, code, OUT_NONE).astype(np.int8)
    alpha = np.ones((Hh, Ww), dtype=np.float32)
    if aa:
        # A stair's inner corner: a pixel touching the form only at a corner, most of it within a pixel of the true
        # edge, takes the outline at half alpha (not over the body, where the layer under it shows).
        corner = diag & (R.near >= 0.5) & ~inner_mask
        glow = np.isin(nm, np.array(sorted(glow_mats), dtype=np.int16)) if glow_mats else np.zeros_like(corner)
        corner &= ~glow
        out = np.where(corner, OUT_AA, out).astype(np.int8)
        alpha = np.where(corner, 0.5, alpha).astype(np.float32)
        # A convex tip whose pixel lies mostly beyond a pixel from the true edge: its outline softens.
        tip = edge & ~inner_mask & (R.near < 0.4)
        alpha = np.where(tip, 0.6, alpha).astype(np.float32)
    R.out = out
    R.out_mat = np.where(out > 0, nm, -1).astype(np.int16)
    R.alpha = alpha


# ------------------------------------------------------------------ colour
def colourize(R: Res, mats: list, pal7: dict, inner_tone: dict | None = None, soft_line: bool = True) -> np.ndarray:
    """RGBA for a band: each material's seven-step ramp at its tone (the rim warmed toward SUN, the bounce cooled toward
    SKY); the outline as the material it bounds, tinted."""
    Hh, Ww = R.mat.shape
    rgb = np.zeros((Hh, Ww, 3), float)
    a = np.zeros((Hh, Ww), float)
    inner_tone = inner_tone or {}
    for mid, name in enumerate(mats):
        rp = pal7.get(name)
        if rp is None:
            continue
        sel = R.mat == mid
        if sel.any():
            c = rp[np.clip(R.tone[sel], 0, 6)]
            rim = R.rim[sel][:, None]
            bnc = R.bounce[sel][:, None]
            c = np.where(rim, _mix(c, SUN, 0.3), c)
            c = np.where(bnc, _mix(c, SKY, 0.12), c)
            rgb[sel] = c
            a[sel] = 1.0
        o = R.out_mat == mid
        if not o.any():
            continue
        ink = o & (R.out == OUT_INK)
        soft = o & (R.out == OUT_SOFT)
        inn = o & (R.out == OUT_INNER)
        aa = o & (R.out == OUT_AA)
        dark = _mix(_mix(rp[0], INK, 0.45), (0, 0, 0), 0.1)
        lit = _mix(rp[1], rp[2], 0.3) if soft_line else dark
        rgb[ink] = dark
        rgb[soft] = lit
        rgb[aa] = dark
        rgb[inn] = rp[int(inner_tone.get(name, 1))]
        a[ink | soft | inn | aa] = 1.0
    a = a * np.where(R.out > 0, R.alpha, 1.0)
    out = np.zeros((Hh, Ww, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a * 255), 0, 255).astype(np.uint8)
    return out
