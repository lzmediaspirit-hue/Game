"""One frame of every item: cast from one skeleton, outlined against the body, and composed for review."""
from __future__ import annotations

import numpy as np
from PIL import Image

from . import body as B
from . import raster
from .items import z_of
from .render import BANDS, cast, colourize, edge
from .skeleton import Skeleton


def cast_all(p: dict, facing: str, items: list) -> dict:
    """{item key: (band layers, caster)} for one pose and facing. The body is cast first; its silhouette decides which
    of the other items' edges fall inside the figure (a darker tone of their own) and which outside (ink)."""
    sk = Skeleton(p, facing)
    out = {}
    body = [it for it in items if it.cat == "body"]
    rest = [it for it in items if it.cat != "body"]
    mask = np.zeros((raster.H, raster.W), dtype=bool)
    for it in body:
        cb = raster.Caster(it.mats)
        lb = cast(it.cast(sk), cb, it.look, after=lambda L, cb=cb: B.face(sk, L["head"], cb))
        for b in BANDS:
            mask |= lb[b].mat >= 0
        own = {b: lb[b].mat >= 0 for b in BANDS}
        edge(lb, cb, it.look, lambda b: mask & ~own[b])
        out[it.key] = (lb, cb)
    for it in rest:
        c = raster.Caster(it.mats)
        L = cast(it.cast(sk), c, it.look)
        edge(L, c, it.look, lambda b: mask)
        out[it.key] = (L, c)
    return out


def compose(cast_result: dict, outfit: list) -> Image.Image:
    """The figure as the game stacks it: `outfit` is [(item, variant)]."""
    stack = []
    for it, var in outfit:
        L, c = cast_result[it.key]
        for b in BANDS:
            if (L[b].mat >= 0).any() or (L[b].out > 0).any():
                stack.append((z_of(it.cat, b), colourize(L[b], c.mats, it.palettes[var], it.look.line_tone)))
    stack.sort(key=lambda t: t[0])
    im = Image.new("RGBA", (raster.W, raster.H))
    for _, a in stack:
        im.alpha_composite(Image.fromarray(a, "RGBA"))
    return im
