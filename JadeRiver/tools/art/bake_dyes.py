"""Garment dyes for the layered avatar (NPC variety; AGENTS.md rules 1 and 3).

Every shirt and trousers sheet, for every registered action, is recoloured into each
dye by a luminance ramp. Outline pixels, skin tones and gold trim keep their colour,
so each dyed sheet is pixel-identical in shape to the approved original: the same
frames, feet registration, hand grips and layer order in every pose and facing.

Output: art/dye/<sheet>__<dye>.png, and data/parts.json gains "_dyes" (order and
swatches) plus the dyed paths appended to each animation's "sheets" list in dye order
(sheets[0] stays the original). Deterministic; re-running rewrites identical files.

Run from JadeRiver/:  python3 tools/art/bake_dyes.py
Review:               python3 tools/art/bake_dyes.py --gallery <out.png>
"""
import colorsys
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PARTS = os.path.join(ROOT, "data", "parts.json")
OUT = os.path.join(ROOT, "art", "dye")
CATEGORIES = ["shirt", "pants"]

# Dark -> light ramps (4 stops), hue-shifted: shadows lean blue-green, lights warm.
DYES = {
    "jade":    ["#0d2f2c", "#155c52", "#2c9e8f", "#8fe0c8"],
    "cloud":   ["#2c3a4a", "#6f8599", "#c3d3dd", "#f2f5f2"],
    "earth":   ["#2a1a10", "#5a3a22", "#8c6a44", "#c9a878"],
    "ink":     ["#0b0d12", "#1d222c", "#353d4a", "#5f6878"],
    "crimson": ["#2a0b12", "#5e1624", "#9c2a36", "#dc6a5c"],
    "grey":    ["#23262a", "#4a5056", "#7d858a", "#b9c0c2"],
    "indigo":  ["#10143a", "#232f6e", "#3f55a8", "#8ea8e0"],
    "ochre":   ["#2e1e08", "#6b4a14", "#b0812a", "#ecc56a"],
    "rose":    ["#2e1020", "#6a2a44", "#b25a78", "#eeb0c0"],
    "white":   ["#4a4f55", "#9aa0a2", "#dcddd6", "#fbfaf2"],
}
ORDER = list(DYES.keys())


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


RAMPS = {k: np.stack([hexrgb(c) for c in v]) for k, v in DYES.items()}


def ramp_colour(ramp, t):
    """t in [0,1] -> colour along the 4-stop ramp (piecewise linear, then posterised)."""
    t = np.clip(t, 0.0, 1.0) * (len(ramp) - 1)
    i = np.clip(np.floor(t).astype(int), 0, len(ramp) - 2)
    f = (t - i)[..., None]
    c = ramp[i] * (1 - f) + ramp[i + 1] * f
    return np.round(c / 4.0) * 4.0   # keep a small, crisp palette


def recolour(img, dye):
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    rgb = a[..., :3] / 255.0
    alpha = a[..., 3]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # Hue in degrees.
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.zeros_like(mx)
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, hue)
    hue = np.where(mx == g, (b - r) / d + 2, hue)
    hue = np.where(mx == b, (r - g) / d + 4, hue)
    hue = hue * 60.0
    outline = (lum < 0.13) & (sat < 0.45)
    skin = (hue > 8) & (hue < 38) & (sat > 0.22) & (sat < 0.75) & (lum > 0.35)
    gold = (hue >= 38) & (hue < 62) & (sat > 0.45) & (lum > 0.35)
    keep = outline | skin | gold | (alpha < 1)
    # Normalise the garment's own luminance range into the ramp.
    cloth = ~keep
    if cloth.any():
        lo, hi = np.percentile(lum[cloth], 2), np.percentile(lum[cloth], 98)
    else:
        lo, hi = 0.0, 1.0
    t = (lum - lo) / max(1e-3, hi - lo)
    new = ramp_colour(RAMPS[dye], t)
    out = a.copy()
    out[..., :3] = np.where(cloth[..., None], new, a[..., :3])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def sheet_path(p):
    return os.path.join(ROOT, p.replace("art_v12/", "art/"))


def main():
    parts = json.load(open(PARTS))
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for cat in CATEGORIES:
        for item, spec in parts[cat].items():
            for layer in spec.get("layers", []):
                for action, anim in layer.get("animations", {}).items():
                    if not anim or anim.get("hidden") or not anim.get("sheets"):
                        continue
                    base = anim["sheets"][0]
                    src = Image.open(sheet_path(base))
                    dyed = []
                    for dye in ORDER:
                        name = os.path.splitext(os.path.basename(base))[0] + "__" + dye + ".png"
                        path = os.path.join(OUT, name)
                        recolour(src, dye).save(path, optimize=True)
                        dyed.append("res://art/dye/" + name)
                        made += 1
                    anim["sheets"] = [base] + dyed
    parts["_dyes"] = {"order": ["none"] + ORDER, "swatch": {k: v[2] for k, v in DYES.items()}, "categories": CATEGORIES}
    with open(PARTS, "w") as f:
        json.dump(parts, f, indent=2)
        f.write("\n")
    print("dyed sheets:", made)


def gallery(out):
    """Every dye on every shirt/trousers style, idle and walk frame 0, both facings."""
    parts = json.load(open(PARTS))
    body = [l for l in parts["body"]["light"]["layers"]]
    cell = 128
    styles = [("shirt", s) for s in parts["shirt"]] + [("pants", p) for p in parts["pants"]]
    W = (len(ORDER) + 1) * cell
    H = len(styles) * cell * 2
    sheet = Image.new("RGBA", (W, H), (80, 96, 96, 255))
    for row, (cat, item) in enumerate(styles):
        for col, dye in enumerate(["none"] + ORDER):
            for fi, action in enumerate(["idle", "walk"]):
                canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                for l in sorted(body, key=lambda l: l["z"]):
                    a = l["animations"].get(action, {})
                    if a.get("sheets"):
                        canvas.alpha_composite(Image.open(sheet_path(a["sheets"][0])).convert("RGBA").crop((0, 256, 256, 512)))
                for l in parts[cat][item]["layers"]:
                    a = l["animations"][action]
                    sh = a["sheets"][0] if col == 0 else a["sheets"][col]
                    p = sh if not sh.startswith("res://") else os.path.join(ROOT, sh[6:])
                    canvas.alpha_composite(Image.open(sheet_path(p) if not p.startswith(ROOT) else p).convert("RGBA").crop((0, 256, 256, 512)))
                tile = canvas.crop((64, 40, 192, 168))
                sheet.paste(tile, (col * cell, (row * 2 + fi) * cell), tile)
    sheet.save(out)
    print("gallery ->", out)


if __name__ == "__main__":
    if "--gallery" in sys.argv:
        gallery(sys.argv[sys.argv.index("--gallery") + 1])
    else:
        main()
