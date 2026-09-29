"""One frame of the study's figure: every item cast from one skeleton at one density (hifi.Grid), outlined against the
body, coloured per variant, and stacked as the game stacks its layers (figure/items.z_of)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from figure import raster  # noqa: E402
from figure.items import z_of  # noqa: E402
from figure.skeleton import Skeleton  # noqa: E402

import hifi  # noqa: E402
import looks  # noqa: E402

BANDS = hifi.BANDS
# One ellipsoid round the skull and the jaw (figure/body.py SKULL, JAW), in the head's frame: the face's shading form.
HEAD_AT = (0.4, 0.0, -0.9)
HEAD_R = (5.9, 6.1, 7.4)


def _cast_item(g, sk, it):
    caster = raster.Caster(it.mats)
    fines = {b: hifi.Fine(g) for b in BANDS}
    for s in it.cast(sk):
        hifi.cast(g, fines[s.band], s, caster)
    if it.cat == "body" and "head" in caster.parts:
        # The face as one form: the skull and the jaw shaded by one ellipsoid round both.
        hifi.smooth_normals(g, fines["head"], caster.parts["head"], sk.head + sk.Mh @ np.array(HEAD_AT), sk.Mh, HEAD_R)
    info = {m: it.mat_info(m) for m in caster.mats}
    weight = {caster.mid(m): float(v.get("weight", 1.0)) for m, v in info.items()}
    thin = {caster.mid(m) for m, v in info.items() if v.get("thin")}
    res = {b: hifi.resolve(g, fines[b], weight, thin) for b in BANDS}
    if it.cat == "body":
        looks.face(g, sk, res["head"], caster)
    info = {m: it.mat_info(m) for m in caster.mats}
    hi = {caster.mid(m) for m, v in info.items() if v.get("hi")}
    glossy = {caster.mid(m) for m, v in info.items() if v.get("glossy")}
    flat = {caster.mid(m): 3 for m in caster.mats if m in looks.FACE_COLS}
    th = {caster.mid(m): v["th"] for m, v in info.items() if v.get("th")}
    for b in BANDS:
        hifi.shade(g, res[b], hi, flat, glossy, th)
    if it.cat == "body" and "head" in caster.parts:
        # A face reads best nearly flat: its skin keeps to the base and the shadow step, with no rim or bounce across it.
        R = res["head"]
        face = (R.part == caster.parts["head"]) & (R.mat == caster.mid("skin"))
        R.tone = np.where(face, np.clip(R.tone, 2, 3), R.tone).astype(np.int8)
        R.rim &= ~face
        R.bounce &= ~face
        # The neck sits in the jaw's shade, one flat step, with a line of the core shadow along the jaw.
        if "neck" in caster.parts:
            neck = (R.part == caster.parts["neck"]) & (R.mat == caster.mid("skin"))
            hd = R.part == caster.parts["head"]
            by = np.zeros_like(hd)
            by[1:] |= hd[:-1]
            by[:, 1:] |= hd[:, :-1]
            by[:, :-1] |= hd[:, 1:]
            R.tone = np.where(neck, np.where(by, 1, 2), R.tone).astype(np.int8)
            R.rim &= ~neck
            R.bounce &= ~neck
    ink = {caster.mid(m) for m, v in info.items() if v.get("ink")}
    glow = {caster.mid(m) for m, v in info.items() if v.get("glow")}
    return res, caster, ink, glow


def cast_frame(g, pose: dict, facing: str, items: list) -> dict:
    """{item key: ({band: hifi.Res}, caster)} for one pose and facing: the body first, whose silhouette decides which of
    the other items' edges are inner lines."""
    sk = Skeleton(pose, facing)
    out = {}
    mask = np.zeros((g.H, g.W), dtype=bool)
    for it in [i for i in items if i.cat == "body"]:
        res, c, ink, glow = _cast_item(g, sk, it)
        for b in BANDS:
            mask |= res[b].mat >= 0
        own = {b: res[b].mat >= 0 for b in BANDS}
        for b in BANDS:
            hifi.outline(g, res[b], mask & ~own[b], ink, glow)
        out[it.key] = (res, c)
    for it in [i for i in items if i.cat != "body"]:
        res, c, ink, glow = _cast_item(g, sk, it)
        for b in BANDS:
            hifi.outline(g, res[b], mask, ink, glow)
        out[it.key] = (res, c)
    return out


def pal7(it, variant: str) -> dict:
    return {k: hifi.ramp7(v) for k, v in it.palette(variant).items() if v is not None}


def rgba(it, R, caster, variant: str, cache: dict | None = None) -> np.ndarray:
    key = (it.key, variant)
    if cache is not None and key in cache:
        p = cache[key]
    else:
        p = pal7(it, variant)
        if cache is not None:
            cache[key] = p
    return hifi.colourize(R, caster.mats, p, {"hair": 1, "cloth": 1, "skin": 2})


def compose(g, cast_result: dict, outfit: list, items: dict) -> Image.Image:
    """The figure stacked: `outfit` [(key, variant)]."""
    stack = []
    for key, var in outfit:
        it = items[key]
        res, c = cast_result[key]
        for b in BANDS:
            R = res[b]
            if (R.mat >= 0).any() or (R.out > 0).any():
                stack.append((z_of(it.cat, b), rgba(it, R, c, var)))
    stack.sort(key=lambda t: t[0])
    im = Image.new("RGBA", (g.W, g.H))
    for _, a in stack:
        im.alpha_composite(Image.fromarray(a, "RGBA"))
    return im
