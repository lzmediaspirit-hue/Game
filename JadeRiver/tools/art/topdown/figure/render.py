"""Cast an item's solids for one pose into its three bands, shade and outline them, and colour the result.

An item's cast is palette-free (material ids and tones per pixel), so a dye or hair colour is only a new palette.
"""
from __future__ import annotations

import numpy as np

from . import raster
from .palettes import LINE, LINE_SOFT

BANDS = ("back", "mid", "head", "front")


class Look:
    """How an item's materials shade and outline: tone-4 highlights, fixed tones, ink edges, thresholds."""

    def __init__(self, highlight=(), flat=None, ink=(), thresholds=None, line_tone=None, glow=()):
        self.line_tone = dict(line_tone or {})
        self.glow = set(glow)
        self.highlight = set(highlight)
        self.flat = dict(flat or {})
        self.ink = set(ink)
        self.thresholds = dict(thresholds or {})


def cast(solids, caster: raster.Caster, look: Look, after=None) -> dict:
    """Solids into band layers, shaded. `after(layers)` may stamp decals before shading (the face)."""
    layers = {b: raster.Layer() for b in BANDS}
    for s in solids:
        caster.cast(layers[s.band], s)
    if after is not None:
        after(layers)
    hl = {caster.mid(m) for m in look.highlight}
    flat = {caster.mid(m): t for m, t in look.flat.items()}
    th = {caster.mid(m): v for m, v in look.thresholds.items()}
    for b in BANDS:
        raster.shade(layers[b], hl, flat, th)
    return layers


def edge(layers: dict, caster: raster.Caster, look: Look, figure_mask) -> None:
    """Outline each band. `figure_mask(band)` is the figure under that band's edge (for the inner lines)."""
    mode = {caster.mid(m): "ink" for m in look.ink}
    mode.update({caster.mid(m): "glow" for m in look.glow})
    for b in BANDS:
        raster.outline(layers[b], figure_mask(b), mode)


def colourize(layer: raster.Layer, mats: list, palette: dict, line_tone: dict | None = None) -> np.ndarray:
    """RGBA for a band layer: each material's ramp at its tone, edges in ink or the material's deepest tone."""
    Hh, Ww = layer.mat.shape
    out = np.zeros((Hh, Ww, 4), dtype=np.uint8)
    for mid, name in enumerate(mats):
        sel = layer.mat == mid
        if sel.any():
            rp = np.array(palette[name], dtype=np.uint8)
            out[sel] = rp[np.clip(layer.tone[sel], 0, len(rp) - 1)]
        inner = (layer.out == raster.OUT_INNER) & (layer.out_mat == mid)
        if inner.any():
            out[inner] = np.array(palette[name][(line_tone or {}).get(name, 0)], dtype=np.uint8)
    out[layer.out == raster.OUT_INK] = np.array(LINE, dtype=np.uint8)
    out[layer.out == raster.OUT_SOFT] = np.array(LINE_SOFT, dtype=np.uint8)
    return out
