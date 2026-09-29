"""Cast an item's solids for one pose into its four bands, resolve, shade and outline them, and colour the result
(decision 42: the figure drawn better at the same 38 px; raster.py has the rules).

An item's cast is palette-free (material ids, tones, rim, bounce and outline codes per pixel), so a dye or hair colour
is only a new palette. Colour turns every five-step ramp (deep, shadow, base, light, highlight) into seven (`ramp7`)
leaning toward the art bible's sun and shadow (§14.2); light (a cut's smear, a ring of sound, a bow's string, wet ink:
a `glow` material) keeps its own colours, flat, with no ink round it.
"""
from __future__ import annotations

import numpy as np

from . import raster

BANDS = ("back", "mid", "head", "front")

SUN = np.array((0xFF, 0xE9, 0xA6), float)       # art bible §14.2
SHADOW = np.array((0x24, 0x1F, 0x4F), float)
SKY = np.array((0x9C, 0xC8, 0xD2), float)       # the bright floor and sky a shaded edge turns toward
INK = np.array((0x0E, 0x1A, 0x1E), float)       # §4's ink-teal

RIM_WARM = 0.3                                  # a rim pixel's colour, this far toward SUN
# A five-step tone (the sets' `flat` and `line_tone`, written for the five-step ramps) as a step of the seven.
STEP7 = (0, 2, 3, 4, 6)
# The inner line: a step of the seven by the five-step `line_tone` (0, the default, is the core shadow).
INNER7 = (1, 2, 3, 4, 6)

# How each material shades, by name (a set's Look may override one: `mats`):
#   hi      may reach step 5 (light)          glossy  step 6 (a sheen or a glint, from paint or the rim)
#   weight  its vote in a pixel (thin trim votes extra, so a gold collar keeps an unbroken line)
#   thin    solid from a quarter of a pixel (trim, a blade, a shaft)
#   line    solid from a quarter of a pixel unless it is the fainter side of a line its neighbour holds: a line about a
#           pixel wide stays unbroken and one pixel wide (a bow's limbs, a shaft; every `glow` material is one: strings,
#           ripples, rings, ink, a cut's smear)
#   th      its own four thresholds of mean N.L (faces are lit nearly flat; hair turns late)
#   rim     how far the rim warms toward the sun (RIM_WARM; bare steel keeps cool)
MATS = {
    "skin": {"hi": True, "th": (-0.55, -0.2, 0.36, 0.72)},
    "hair": {"hi": True, "glossy": True, "th": (-0.05, 0.38, 0.74, 0.95)},
    "ribbon": {"hi": True, "glossy": True, "weight": 1.6},
    "pin": {"hi": True, "glossy": True, "weight": 0.9},
    "cloth": {"hi": True},
    "panel": {"hi": True},
    "trim": {"hi": True, "glossy": True, "weight": 1.5, "thin": True},
    "belt": {"hi": True, "weight": 1.3},
    "accent": {"hi": True, "weight": 1.6},
    "wrap": {"hi": True, "weight": 1.3},
    "sole": {"hi": True},
    "top": {"hi": True},
    "plate": {"hi": True, "glossy": True, "rim": 0.08},
    "cape": {"hi": True, "rim": 0.1},      # a sheet trailing flat catches the rim all over: a faint one keeps its colour
    "straw": {"hi": True},
    "band": {"hi": True, "weight": 1.3},
    "stud": {"hi": True, "glossy": True, "weight": 1.6, "thin": True},
    "jade": {"hi": True, "glossy": True},
    "veil": {"hi": True},
    "steel": {"hi": True, "glossy": True, "rim": 0.08},
    "bronze": {"hi": True, "glossy": True, "weight": 1.3},
    "blade": {"hi": True, "glossy": True, "thin": True},
    "gold": {"hi": True, "glossy": True, "weight": 2.0, "thin": True},
    "hilt": {"weight": 1.5, "thin": True},
    "shaft": {"hi": True, "line": True},
    "cord": {"line": True},
    "limb": {"hi": True, "glossy": True, "line": True},
    "ear": {"line": True},
    "grip": {"weight": 1.5, "line": True},
    "head": {"hi": True, "glossy": True, "line": True},
    "fletch": {"line": True},
    "bamboo": {"hi": True, "line": True},
    "joint": {"weight": 1.5, "line": True},
    "node": {"weight": 1.5, "line": True},
    "hole": {"weight": 1.5, "line": True},
    "lacquer": {"hi": True, "glossy": True, "line": True},
    "tuft": {"hi": True, "line": True},
    "tip": {"line": True},
    "tassel": {"hi": True, "line": True},
    "rib": {"weight": 1.3, "line": True},
    "fan_ink": {"weight": 1.3},
    "paper": {"hi": True},
    "wood": {"line": True},
    "rim": {"weight": 1.3},
}
# A weapon's pale cutting edge (`edge` in a weapon's palette; a garment's `edge` is its darker cloth).
BLADE_EDGE = {"edge": {"hi": True, "glossy": True, "thin": True, "weight": 1.8}}


class Look:
    """How an item's materials shade and outline. `highlight`: materials allowed the light step (more than MATS
    gives); `flat`: a fixed five-step tone; `ink`: an edge over the figure stays an outer line; `glow`: light, drawn
    flat in its own colours with no ink; `line_tone`: the five-step tone of an inner line (a glow's edge: an index of its
    own palette); `thresholds`: a material's own four thresholds of mean N.L; `mats`: per-material overrides of MATS."""

    def __init__(self, highlight=(), flat=None, ink=(), thresholds=None, line_tone=None, glow=(), mats=None):
        self.line_tone = dict(line_tone or {})
        self.glow = set(glow)
        self.highlight = set(highlight)
        self.flat = dict(flat or {})
        self.ink = set(ink)
        self.thresholds = dict(thresholds or {})
        self.mats = dict(mats or {})

    def info(self, name: str) -> dict:
        d = dict(MATS.get(name, {}))
        d.update(self.mats.get(name, {}))
        if name in self.highlight:
            d["hi"] = True
        if name in self.thresholds:
            d["th"] = tuple(self.thresholds[name])
        return d


def cast(solids, caster: raster.Caster, look: Look, after_resolve=None, after_shade=None, smooth=None) -> dict:
    """Solids into band layers, resolved and shaded. `smooth(fines)` may smooth normals before resolving (the head),
    `after_resolve(layers)` stamp decals before shading (the face), `after_shade(layers)` adjust tones (the face's
    flat light)."""
    fines = {b: raster.Fine() for b in BANDS}
    for s in solids:
        caster.cast(fines[s.band], s)
    if smooth is not None:
        smooth(fines)
    info = {m: look.info(m) for m in caster.mats}
    weight = {caster.mid(m): float(v.get("weight", 1.0)) for m, v in info.items()}
    thin = {caster.mid(m) for m, v in info.items() if v.get("thin")}
    line = {caster.mid(m) for m, v in info.items() if v.get("line") or m in look.glow}
    layers = {b: raster.resolve(fines[b], weight, thin, line) for b in BANDS}
    del fines
    if after_resolve is not None:
        after_resolve(layers)
    info = {m: look.info(m) for m in caster.mats}
    hi = {caster.mid(m) for m, v in info.items() if v.get("hi")}
    glossy = {caster.mid(m) for m, v in info.items() if v.get("glossy")}
    th = {caster.mid(m): v["th"] for m, v in info.items() if v.get("th")}
    flat = {caster.mid(m): (t if m in look.glow else STEP7[t]) for m, t in look.flat.items()}
    for b in BANDS:
        raster.shade(layers[b], hi, flat, glossy, th)
    if after_shade is not None:
        after_shade(layers)
    return layers


def edge(layers: dict, caster: raster.Caster, look: Look, figure_mask) -> None:
    """Outline each band. `figure_mask(band)` is the figure under that band's edge (for the inner lines)."""
    ink = {caster.mid(m) for m in look.ink}
    glow = {caster.mid(m) for m in look.glow}
    for b in BANDS:
        raster.outline(layers[b], figure_mask(b), ink, glow)


# ------------------------------------------------------------------ colour
def _mix(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def ramp7(r5) -> np.ndarray:
    """A five-step ramp (deep, shadow, base, light, highlight) as seven steps, the dark end toward SHADOW, the light
    toward SUN: 0 deep (lines, contact), 1 core shadow (new), 2 shadow, 3 base, 4 light, 5 bright (new), 6 highlight.
    Every step stays a clear step from its neighbours."""
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


class Paint:
    """An item's palette for one variant, ready to colour its layers: a seven-step ramp per lit material, its own
    colours (RGBA) per glow material, and the tone of each material's inner line."""

    def __init__(self, mats: list, palette: dict, look: Look):
        self.mats = list(mats)
        self.ramp = {}
        self.glow = {}
        self.inner = {}
        self.rim = {}
        for name in self.mats:
            p = palette.get(name)
            if p is None:
                continue
            if name in look.glow:
                self.glow[name] = np.array([tuple(c) + (255,) * (4 - len(c)) for c in p], dtype=np.uint8)
                self.inner[name] = int(look.line_tone.get(name, 0))
            else:
                self.ramp[name] = ramp7(p)
                self.inner[name] = INNER7[int(look.line_tone.get(name, 0))]
                self.rim[name] = float(look.info(name).get("rim", RIM_WARM))


def colourize(layer, mats: list, paint: Paint) -> np.ndarray:
    """RGBA for a band layer: each material's ramp at its tone (the rim warmed toward SUN, the bounce cooled toward
    SKY), a glow in its own colours; the outline as a tint of the material it bounds (render's module doc)."""
    Hh, Ww = layer.mat.shape
    rgb = np.zeros((Hh, Ww, 3), float)
    a = np.zeros((Hh, Ww), float)
    for mid, name in enumerate(mats):
        sel = layer.mat == mid
        o = layer.out_mat == mid
        if name in paint.glow:
            gp = paint.glow[name]
            if sel.any():
                c = gp[np.clip(layer.tone[sel], 0, len(gp) - 1)]
                rgb[sel] = c[:, :3]
                a[sel] = c[:, 3] / 255.0
            if o.any():
                c = gp[min(paint.inner[name], len(gp) - 1)]
                rgb[o] = c[:3]
                a[o] = c[3] / 255.0
            continue
        rp = paint.ramp.get(name)
        if rp is None:
            continue
        if sel.any():
            c = rp[np.clip(layer.tone[sel], 0, 6)]
            c = np.where(layer.rim[sel][:, None], _mix(c, SUN, paint.rim[name]), c)
            c = np.where(layer.bounce[sel][:, None], _mix(c, SKY, 0.12), c)
            rgb[sel] = c
            a[sel] = 1.0
        if not o.any():
            continue
        dark = _mix(_mix(rp[0], INK, 0.45), (0, 0, 0), 0.1)
        lit = _mix(rp[1], rp[2], 0.3)
        rgb[o & ((layer.out == raster.OUT_INK) | (layer.out == raster.OUT_AA))] = dark
        rgb[o & (layer.out == raster.OUT_SOFT)] = lit
        rgb[o & (layer.out == raster.OUT_INNER)] = rp[paint.inner[name]]
        a[o] = 1.0
    a = a * np.where(layer.out > 0, layer.alpha / 255.0, 1.0)
    out = np.zeros((Hh, Ww, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a * 255), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return out
