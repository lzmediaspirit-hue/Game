"""Bake art/environment/ground-extra.png: two painted ground cells to sit beside ground-v6.png.

    python3 tools/art/bake_ground.py [--preview out.png]

  rock  natural mountain ground: weathered slabs with cracks, grit, pebbles and grass tufts
        (cliffs, gorges, the quarry, the misty slopes)
  snow  packed snow over rock, soft drifts and a few exposed stones (the Summit Ridge)

Same cell size (627 px) and painterly treatment as the main atlas: light from the upper
left, soft value noise, no hard pixel noise. Deterministic: a rebuild is byte-identical.
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "art", "environment", "ground-extra.png")
CELL = 627


def _box(a, r, axis):
    """Periodic box blur of radius r along one axis (the texture tiles)."""
    if r < 1:
        return a
    out = np.zeros_like(a)
    for k in range(-r, r + 1):
        out += np.roll(a, k, axis=axis)
    return out / (2 * r + 1)


def value_noise(shape, scale, seed):
    """Smooth, seamlessly tiling noise in [0, 1], all in float: a coarse periodic random grid,
    bilinearly upsampled with wrap-around, then three periodic box blurs."""
    rng = np.random.default_rng(seed)
    h, w = shape
    gh, gw = max(2, int(round(h / scale))), max(2, int(round(w / scale)))
    grid = rng.random((gh, gw))
    ys = np.arange(h) * gh / h
    xs = np.arange(w) * gw / w
    y0, x0 = ys.astype(int), xs.astype(int)
    y1, x1 = (y0 + 1) % gh, (x0 + 1) % gw
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    a = (grid[y0][:, x0] * (1 - fy) * (1 - fx) + grid[y1][:, x0] * fy * (1 - fx)
         + grid[y0][:, x1] * (1 - fy) * fx + grid[y1][:, x1] * fy * fx)
    r = max(1, int(scale * 0.3))
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    lo, hi = a.min(), a.max()
    return ((a - lo) / max(1e-9, hi - lo)).astype(np.float32)


def wrapped(fn, img, rng_state, cx, cy, *args, **kw):
    """Draw a shape and its copies across the cell edges, so the texture tiles seamlessly."""
    for dy in (-CELL, 0, CELL):
        for dx in (-CELL, 0, CELL):
            rng = np.random.default_rng(rng_state)   # the same shape in every copy
            fn(img, rng, cx + dx, cy + dy, *args, **kw)


def fbm(shape, base, octaves, seed):
    out = np.zeros(shape, np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        out += amp * value_noise(shape, base / (2 ** o), seed + o * 17)
        total += amp
        amp *= 0.5
    return out / total


def worley(shape, count, seed):
    """F1, F2 distances and the nearest cell id for jittered points (tiled 3x3 for clean edges)."""
    rng = np.random.default_rng(seed)
    h, w = shape
    pts = rng.random((count, 2)) * [w, h]
    tiles = np.concatenate([pts + [dx * w, dy * h] for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
    ids = np.tile(np.arange(count), 9)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f1 = np.full(shape, 1e9, np.float32)
    f2 = np.full(shape, 1e9, np.float32)
    cid = np.zeros(shape, np.int32)
    for (px, py), i in zip(tiles, ids):
        if px < -w * 0.35 or px > w * 1.35 or py < -h * 0.35 or py > h * 1.35:
            continue
        d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        cid = np.where(closer, i, cid)
        f1 = np.where(closer, d, f1)
    return f1, f2, cid


def shade(height):
    """Lambert-ish light from the upper left on a (tiling) height field."""
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5
    light = -(gx * 0.7 + gy * 0.7)
    return np.clip(light * 6.0, -1.0, 1.0)


def mix(a, b, t):
    t = np.clip(t, 0.0, 1.0)[..., None]
    return a * (1 - t) + b * t


def blobs(img, rng, count, rmin, rmax, colors, shadow=0.35):
    """Pebbles: small shaded ellipses with a soft shadow to the lower right."""
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for _ in range(count):
        cx, cy = rng.random() * w, rng.random() * h
        rx = rmin + rng.random() * (rmax - rmin)
        ry = rx * (0.55 + rng.random() * 0.3)
        col = np.array(colors[rng.integers(len(colors))], np.float32)
        for ox in (-w, 0, w):
            for oy in (-h, 0, h):
                _blob(img, xx, yy, cx + ox, cy + oy, rx, ry, col, shadow)


def _blob(img, xx, yy, cx, cy, rx, ry, col, shadow):
        h, w, _ = img.shape
        x0, x1 = int(max(0, cx - rx - 6)), int(min(w, cx + rx + 6))
        y0, y1 = int(max(0, cy - ry - 6)), int(min(h, cy + ry + 6))
        if x1 <= x0 or y1 <= y0:
            return
        sx, sy = xx[y0:y1, x0:x1], yy[y0:y1, x0:x1]
        sh = ((sx - cx - 3) / rx) ** 2 + ((sy - cy - 3) / ry) ** 2 <= 1.0
        img[y0:y1, x0:x1][sh] *= 1.0 - shadow
        e = ((sx - cx) / rx) ** 2 + ((sy - cy) / ry) ** 2
        m = e <= 1.0
        lit = np.clip(1.0 - (((sx - cx + rx * 0.35) / rx) ** 2 + ((sy - cy + ry * 0.35) / ry) ** 2), 0, 1)
        stone = col * (0.78 + 0.45 * lit[..., None])
        img[y0:y1, x0:x1][m] = stone[m]


def tufts(img, rng, count, colors):
    """Short grass blades in clumps, drawn as thin tapered strokes."""
    h, w, _ = img.shape
    for _ in range(count):
        cx, cy = rng.random() * w, rng.random() * h
        for _b in range(int(4 + rng.random() * 6)):
            ang = -np.pi / 2 + (rng.random() - 0.5) * 1.3
            ln = 7 + rng.random() * 11
            col = np.array(colors[rng.integers(len(colors))], np.float32)
            bx = cx + (rng.random() - 0.5) * 8
            for s in range(int(ln)):
                t = s / ln
                x = int(bx + np.cos(ang) * s) % w
                y = int(cy + np.sin(ang) * s) % h
                img[y, x] = col * (0.8 + 0.4 * t)
                if t < 0.5: img[y, (x + 1) % w] = col * (0.8 + 0.4 * t)


def boulder(img, rng, cx, cy, r, col, snowcap=False):
    """An irregular rock: noisy outline, lit from the upper left, a crack, a soft shadow."""
    h, w, _ = img.shape
    x0, x1 = int(max(0, cx - r * 1.6)), int(min(w, cx + r * 1.6))
    y0, y1 = int(max(0, cy - r * 1.3)), int(min(h, cy + r * 1.3))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    ang = np.arctan2(yy - cy, xx - cx)
    phase = rng.random(3) * 6.28
    wob = 1.0 + 0.16 * np.sin(3 * ang + phase[0]) + 0.1 * np.sin(5 * ang + phase[1]) + 0.06 * np.sin(9 * ang + phase[2])
    rx, ry = r * 1.25, r * 0.8
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) / wob
    sd = np.sqrt(((xx - cx - r * 0.25) / rx) ** 2 + ((yy - cy - r * 0.3) / ry) ** 2) / wob
    region = img[y0:y1, x0:x1]
    region[sd <= 1.05] *= 0.62
    m = d <= 1.0
    lit = np.clip(1.0 - np.sqrt(((xx - cx + rx * 0.4) / rx) ** 2 + ((yy - cy + ry * 0.45) / ry) ** 2), 0, 1)
    face = np.array(col, np.float32) * (0.62 + 0.62 * lit[..., None])
    rim = np.clip((d - 0.86) * 7.0, 0, 1)[..., None]
    face = face * (1 - rim * 0.45)
    if snowcap:
        cap = (yy < cy - ry * 0.15 + 0.2 * r * np.sin(xx * 0.3)) & m
        face[cap] = np.array([236, 242, 248], np.float32) * (0.9 + 0.1 * lit[cap][..., None])
    region[m] = face[m]
    # one hairline crack, gently bent
    a = rng.random() * 3.14
    bend = (rng.random() - 0.5) * 0.6
    seen = set()
    for tt in np.linspace(-0.6, 0.6, int(r * 6)):
        x = int(round(cx + np.cos(a + bend * tt) * tt * r))
        y = int(round(cy + np.sin(a + bend * tt) * tt * r * 0.7))
        if (x, y) in seen or not (y0 <= y < y1 and x0 <= x < x1) or d[y - y0, x - x0] >= 0.85:
            continue
        seen.add((x, y))
        img[y, x] *= 0.6


def rock():
    shape = (CELL, CELL)
    rng = np.random.default_rng(11)
    soil_a = np.array([122, 110, 94], np.float32)
    soil_b = np.array([98, 94, 88], np.float32)
    img = mix(np.broadcast_to(soil_a, shape + (3,)).copy(), soil_b, fbm(shape, 90, 3, 3))
    img *= (0.84 + 0.32 * fbm(shape, 10, 3, 21))[..., None]
    light = shade(fbm(shape, 45, 3, 5) * 30.0)
    img *= (1.0 + 0.12 * light)[..., None]
    moss = np.clip((fbm(shape, 80, 3, 44) - 0.62) * 4.0, 0, 1)
    img = mix(img, np.array([96, 112, 72], np.float32), moss * 0.5)
    blobs(img, rng, 260, 1.5, 3.5, [[140, 130, 114], [112, 106, 98], [86, 82, 78]], shadow=0.25)
    for _ in range(26):
        col = [[128, 120, 108], [112, 108, 102], [136, 126, 110], [104, 100, 96]][rng.integers(4)]
        wrapped(boulder, img, int(rng.integers(1 << 30)), rng.random() * CELL, rng.random() * CELL, 10 + rng.random() * 26, col)
    blobs(img, rng, 70, 3, 7, [[138, 128, 112], [120, 114, 104], [150, 140, 122]])
    tufts(img, rng, 22, [[104, 128, 72], [86, 110, 60], [128, 142, 84]])
    return np.clip(img, 0, 255)


def snow():
    shape = (CELL, CELL)
    rng = np.random.default_rng(23)
    drift = fbm(shape, 120, 4, 8)
    light = shade(drift * 36.0)
    base = np.array([228, 234, 240], np.float32)
    shadow_col = np.array([180, 196, 218], np.float32)
    img = mix(np.broadcast_to(base, shape + (3,)).copy(), shadow_col, np.clip(0.3 - light * 0.7, 0, 1))
    img *= (0.975 + 0.05 * fbm(shape, 16, 2, 9))[..., None]
    for _ in range(9):
        wrapped(boulder, img, int(rng.integers(1 << 30)), rng.random() * CELL, rng.random() * CELL, 12 + rng.random() * 20, [100, 104, 114], snowcap=True)
    blobs(img, rng, 26, 2, 4, [[112, 116, 124], [96, 100, 110]], shadow=0.12)
    sparkle = rng.random(shape) > 0.9992
    img[sparkle] = [255, 255, 255]
    return np.clip(img, 0, 255)


def main():
    atlas = np.zeros((CELL, CELL * 2, 3), np.float32)
    atlas[:, :CELL] = rock()
    atlas[:, CELL:] = snow()
    Image.fromarray(atlas.astype(np.uint8), "RGB").save(OUT, optimize=False)
    print("wrote", os.path.relpath(OUT, ROOT))
    if "--preview" in sys.argv:
        p = sys.argv[sys.argv.index("--preview") + 1]
        Image.fromarray(atlas.astype(np.uint8), "RGB").save(p)


if __name__ == "__main__":
    main()
