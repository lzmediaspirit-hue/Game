#!/usr/bin/env python3
"""Technique node-card pictures and detail illustrations for the Techniques page mockups (roadmap decision 18).

The page draws each art of a tree as an illustrated card: a square picture of the art in action. A picture is a
scene composed from what the game already has, never a new pose:

- the ground: the element's disc colours from the emblem composer (`families.techniques.DISCS`) as banded light
  behind the figure, over the element's own ground (a still waterline for Water, loam for Wood, and so on);
- the figure: Tester's own sprite layers in the pose the art's form borrows (`docs/technique_plan.md` §3.2), composed
  exactly as `scripts/avatar.gd` draws them (`tools/dev/render_mockups.py`), drawn as a silhouette with the Style A
  light (a pale top-left edge, the cool rim on the lower right);
- the verb: the form's own shapes from the emblem grammar (the Flurry's three slashes, the Ward's shelter, the
  Burst's star, the Seal's square print, the Chorus's canopy, the Blink's shade, the Lunge's chevrons, the Domain's
  ring with its corners) redrawn large round the figure in the element's mark material, or the path's when the art
  is a path art (`PATHS`), through the same Style A painter (keyline, seven-step shading, selective outline).

Scenes are described once in a 72-unit square and rendered natively: 72 px for a node card (the sprite at half size,
reduced by 2 x 2 majority, so it stays hard-edged) and 144 px for the detail panel (the sprite at 1:1). A locked
node's picture is the same scene drained to the page's slate, so nothing new is drawn for it.

    python3 tools/icons/study/technique_cards.py     # -> docs/mockups/assets/techcard_<id>.png (72), techart_<id>.png (144)
                                                     #    emblemA_<id>.png, emblemA48_<id>.png for the new arts,
                                                     #    and techcard_sealed.png, the one face of every lost art not yet found

Deterministic: two runs give byte-identical PNGs. Nothing in art/, data/ or the icon manifest is touched.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.normpath(os.path.join(HERE, '..'))
PROJECT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, ICONS)
sys.path.insert(0, os.path.join(PROJECT, 'tools', 'dev'))

from pix import PixelPainter, Ramp, dilate4, move  # noqa: E402
from palette import M, mat7, mix, rgb  # noqa: E402
import families  # noqa: E402,F401
from families.techniques import DISCS, PATHS, emblem  # noqa: E402
import render_mockups as rm  # noqa: E402

OUT = os.path.join(PROJECT, 'docs', 'mockups', 'assets')
SCENE = 72
# Tester at ls6_end (docs/mockups/assets/fig_tester_ls6_idle.png); the free hand's arts are drawn with the hand empty
OUTFIT = {"body": "light", "cape": "none", "hair": "topknot", "hair_color": 0, "hat": "guan", "pants": "martial",
          "pants_dye": "cloud", "shirt": "scholar", "shirt_dye": "ochre", "shoes": "folded", "weapon": "none"}
FEET = (192, 254)   # the avatar origin in render_mockups' 384 canvas


# ----------------------------------------------------------------------------- the figure
def sprite_rgba(action, frame, weapon='none', facing=1, s=1):
    """The figure as RGBA in a (384 * s / 2) canvas with the feet at FEET * s / 2: at s = 2 the sprite itself, at
    s = 1 the sprite reduced by 2 x 2 blocks (a block is on when at least two of its four pixels are, and takes the
    mean colour of those), so it stays hard-edged."""
    im = np.array(rm.compose(dict(OUTFIT, weapon=weapon), action, frame, facing)).astype(np.float32)
    if s == 2:
        return im
    b = im.reshape(192, 2, 192, 2, 4)
    on = (b[..., 3] > 0).astype(np.float32)
    cnt = on.sum(axis=(1, 3))
    col = (b[..., :3] * on[..., None]).sum(axis=(1, 3)) / np.maximum(cnt, 1)[..., None]
    out = np.zeros((192, 192, 4), np.float32)
    out[..., :3] = col
    out[..., 3] = np.where(cnt >= 2, 255, 0)
    return out


def shade_figure(sprite, tone):
    """The figure in the element's duotone: the sprite's own light and shade mapped to five steps from ink to the
    element's light, with a pale edge where the light comes from (up, left) and the cool rim on the lower right
    (Style A rule 5), and a one-pixel halo of the element's light so it parts from a dark ground."""
    mask = sprite[..., 3] > 0
    lum = sprite[..., 0] * 0.3 + sprite[..., 1] * 0.55 + sprite[..., 2] * 0.15
    ramp = [rgb(c) for c in tone['ramp']]
    idx = np.digitize(lum, tone.get('cuts', (46, 92, 140, 196)))
    out = np.zeros(sprite.shape[:2] + (4,), np.uint8)
    for k, c in enumerate(ramp):
        out[mask & (idx == k)] = c + (255,)
    up = np.zeros_like(mask)
    up[1:, :] = mask[:-1, :]
    left = np.zeros_like(mask)
    left[:, 1:] = mask[:, :-1]
    down = np.zeros_like(mask)
    down[:-1, :] = mask[1:, :]
    right = np.zeros_like(mask)
    right[:, :-1] = mask[:, 1:]
    lit = mask & (~up | ~left)
    rim = mask & ~lit & (~down | ~right)
    out[rim] = rgb(tone['rim']) + (255,)
    out[lit] = rgb(tone['edge']) + (255,)
    halo = dilate4(mask) & ~mask
    out[halo] = rgb(tone['halo']) + (tone.get('halo_a', 150),)
    return out


def paste(dst, src, x, y):
    """Alpha-composite RGBA array `src` onto `dst` with its top-left at (x, y); clipped."""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    a = s[..., 3:4] / 255.0
    out = d.copy()
    out[..., :3] = s[..., :3] * a + d[..., :3] * (1 - a)
    out[..., 3:4] = 255.0 * (a + d[..., 3:4] / 255.0 * (1 - a))
    dst[y0:y1, x0:x1] = out.astype(np.uint8)


def figure(img, s, action, frame, fx, fy, tone, weapon='none', facing=1, alpha=1.0, flip=False):
    """Place the figure with its feet at scene point (fx, fy)."""
    spr = sprite_rgba(action, frame, weapon, facing, s)
    if flip:
        spr = spr[:, ::-1]
    mask = spr[..., 3] > 0
    fig = shade_figure(spr, tone)
    if alpha < 1.0:
        fig[..., 3] = (fig[..., 3].astype(np.float32) * alpha).astype(np.uint8)
    ox, oy = FEET[0] * s // 2, FEET[1] * s // 2
    if flip:
        ox = mask.shape[1] - 1 - ox
    paste(img, fig, int(round(fx * s)) - ox, int(round(fy * s)) - oy)


# ----------------------------------------------------------------------------- the ground
def ground(element, s, horizon=62.0, light=(36.0, 34.0), kind='water'):
    """The scene's ground: banded light from the element's disc ramp round `light`, and the element's floor below
    `horizon` (a waterline with ripples, loam, a stone floor)."""
    n = SCENE * s
    disc = [np.array(rgb(c), np.float32) for c in DISCS[element][0]]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / s + 0.5 / s
    d = np.hypot((xx - light[0]) / 1.15, yy - light[1])
    img = np.zeros((n, n, 4), np.uint8)
    band = np.select([d < 13, d < 22, d < 32, d < 44], [3, 2, 1, 0], -1)
    cols = {3: mix(DISCS[element][0][2], DISCS[element][0][3], 0.35), 2: DISCS[element][0][2],
            1: mix(DISCS[element][0][1], DISCS[element][0][2], 0.5), 0: DISCS[element][0][1], -1: DISCS[element][0][0]}
    for k, c in cols.items():
        img[band == k] = rgb(c) + (255,)
    # a few pale motes in the air, placed by a fixed hash of the unit grid
    gx, gy = np.floor(xx).astype(int), np.floor(yy).astype(int)
    motes = (((gx * 73856093) ^ (gy * 19349663)) % 97 == 0) & (yy < horizon - 4) & (d > 16)
    img[motes] = rgb(DISCS[element][1][2]) + (255,)
    below = yy >= horizon
    floor = DISCS[element][0]
    if kind == 'water':
        img[below] = rgb(mix(floor[0], floor[1], 0.55)) + (255,)
        img[below & (yy >= horizon + 4)] = rgb(floor[0]) + (255,)
        img[(yy >= horizon) & (yy < horizon + 1.0 / s + 0.01)] = rgb(DISCS[element][1][2]) + (255,)
        # reflections: broken pale dashes under the light
        for (y0, x0, x1) in ((horizon + 2.5, light[0] - 14, light[0] - 6), (horizon + 2.5, light[0] + 4, light[0] + 16),
                             (horizon + 5.5, light[0] - 8, light[0] + 8), (horizon + 8.5, light[0] - 20, light[0] - 12),
                             (horizon + 8.5, light[0] + 10, light[0] + 22)):
            m = (yy >= y0) & (yy < y0 + 1.0) & (xx >= x0) & (xx < x1)
            img[m] = rgb(DISCS[element][0][2]) + (255,)
    elif kind == 'loam':
        img[below] = rgb(mix(floor[0], '#2a1c10', 0.5)) + (255,)
        img[(yy >= horizon) & (yy < horizon + 1.0)] = rgb(DISCS[element][0][3]) + (255,)
        tufts = below & (((gx * 5 + gy * 11) % 9) == 0) & (yy < horizon + 3)
        img[tufts] = rgb(DISCS[element][0][2]) + (255,)
    else:   # a stone floor
        img[below] = rgb(mix(floor[0], '#101820', 0.4)) + (255,)
        img[(yy >= horizon) & (yy < horizon + 1.0)] = rgb(DISCS[element][0][3]) + (255,)
        seams = below & ((gx % 12) == 0)
        img[seams] = rgb(floor[0]) + (255,)
    return img


# ----------------------------------------------------------------------------- the verbs, redrawn large
def mk_mat(element, path=None, ramp=None):
    disc_c, mark_c, _ = DISCS[element]
    if ramp is not None:
        return mat7(Ramp(ramp, disc_c[0]), 'light')
    tint = PATHS[path]['mark'] if path else None
    return mat7(Ramp(tint or mark_c, disc_c[0]), 'light')


def keyed(p, m, mat, base=0, mode='ray', **kw):
    """A keylined part (the emblem grammar's mark rule: the dark keyline, a pixel wider on the lower right)."""
    ring = dilate4(m) & ~m
    p.decal(ring | (move(ring, 1, 1) & ~m), mat.out, 0, only_on=False)
    return p.part(m, mat, mode, base=base, sep=False, rim=False, **kw)


def flat(p, m, mat, lv=1):
    return p.part(m, mat, 'flat', base=lv, sep=False, rim=False)


def v_flurry(p, mat, hand):
    """The Flurry: three quick crescents (the emblem's Arc, small) stacked ahead of the striking palm, spray beyond."""
    c = p.c
    hx, hy = hand
    for i, (dx, dy, r) in enumerate(((9, -13, 5.6), (15, -1, 6.4), (9, 11, 5.6))):
        cx, cy = hx + dx, hy + dy
        m = c.circle(cx, cy, r) & ~c.circle(cx - 2.6, cy, r * 0.98) & c.box(cx - 1, 0, SCENE, SCENE)
        keyed(p, m, mat, 1 - (i == 1))
    for (x, y, r) in ((hx + 25, hy - 3, 1.3), (hx + 23, hy + 8, 1.0), (hx + 21, hy - 13, 1.0)):
        flat(p, c.circle(x, y, r), mat, 2)


def v_ward_back(p, mat, cx, base_y):
    """The Ward's shelter: a dome of still water over the seated figure."""
    c = p.c
    dome = c.arc(cx, base_y, 27, 2.6, 0, 180, ry=40)
    keyed(p, dome, mat, 0)
    p.decal(c.arc(cx, base_y, 25.6, 1.0, 105, 160, ry=38.6) & dome, mat, 2)


def v_ward_front(p, mat, cx, base_y):
    c = p.c
    keyed(p, c.ring(cx, base_y + 1.5, 24, 1.6, ry=3.2) & c.box(0, base_y + 1.5, SCENE, SCENE), mat, 0)
    for (x, y) in ((cx - 17, base_y - 20), (cx + 18, base_y - 26), (cx - 6, base_y - 34)):
        flat(p, c.diamond(x, y, 1.4), mat, 2)


def v_burst_back(p, mat, cx, cy, r=30):
    """The Burst: the emblem's sixteen-point star, grown round the caster."""
    c = p.c
    pts = []
    for k in range(16):
        a = k * math.pi / 8 + 0.2
        rr = r if k % 2 == 0 else r * 0.46
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.92))
    star = c.poly(pts)
    keyed(p, star, mat, -1)
    p.part(c.circle(cx, cy, r * 0.42), mat, 'sphere', base=1, sep=False, rim=False)


def v_splash_front(p, mat, cx, base_y, spread=22):
    """Water thrown up from the ground at both sides."""
    c = p.c
    for s_ in (-1, 1):
        x = cx + s_ * spread
        keyed(p, c.taper((x, base_y + 1), (x + s_ * 3, base_y - 7), (x + s_ * 8, base_y - 11), 3.2, 1.0), mat, 0)
        flat(p, c.circle(x + s_ * 10, base_y - 15, 1.3), mat, 2)
    keyed(p, c.ring(cx, base_y + 1.5, spread + 2, 1.4, ry=3.0) & c.box(0, base_y + 1.5, SCENE, SCENE), mat, 1)


def v_blink_lines(p, mat, x0, x1, ys):
    c = p.c
    for i, y in enumerate(ys):
        flat(p, c.seg(x0 + 3 * (i % 2), y, x1 - 2 * (i % 2), y, 1.4), mat, 1 - (i % 2))


def v_kingfisher(p, mat, x, y):
    """The step's wake: a kingfisher-blue streak skimming the water from the shade to the arrival, a glint ahead."""
    c = p.c
    keyed(p, c.taper((x - 34, y + 1), (x - 16, y), (x, y - 2), 0.8, 2.6), mat, 0)
    p.part(c.circle(x + 1.5, y - 2, 1.8), mat, 'sphere', base=2, sep=False, rim=False)
    p.sparkle(x + 5, y - 8, 1, '#ffffff')


def v_chorus_back(p, mat, cx, base_y):
    """The Chorus: one song's canopy over the seated singer, a note either side."""
    c = p.c
    keyed(p, c.arc(cx, base_y - 4, 28, 3.0, 18, 162, ry=34), mat, 1)
    keyed(p, c.arc(cx, base_y - 4, 20, 2.4, 26, 154, ry=25), mat, 0)
    for (x, y) in ((cx - 25, base_y - 30), (cx + 24, base_y - 36)):
        note = c.ellipse(x, y, 2.6, 2.0) | c.seg(x + 2.0, y, x + 2.0, y - 8, 1.4) | c.seg(x + 2.0, y - 8, x + 5.0, y - 6, 1.4)
        keyed(p, note, mat, 1)


def v_lotus_front(p, mat, cx, base_y, w=1.0):
    """A lotus opened under the seated figure."""
    c = p.c
    for (a, ln, lv) in ((180, 16, 0), (0, 16, 0), (155, 14, 1), (25, 14, 1), (125, 11, 1), (55, 11, 1)):
        keyed(p, c.leaf(cx, base_y + 1, a, ln * w, 6.2 * w, 0.0, tip_power=0.8), mat, lv)


def v_seal(p, mat, x, y, size=22):
    """The Seal: the square print pressed ahead of the palm, its border and the ring it closes, script strokes."""
    c = p.c
    sq = c.rrect(x, y, x + size, y + size, 2.0)
    keyed(p, sq, mat, 0)
    b = 2.6
    p.decal(sq & ~c.rrect(x + b, y + b, x + size - b, y + size - b, 1.5), mat, -3)
    cx, cy = x + size / 2.0, y + size / 2.0
    p.decal(c.ring(cx, cy, size * 0.26, 1.8) | c.seg(cx, cy - size * 0.36, cx, cy + size * 0.36, 1.4), mat, -3)
    for (gx, gy, gw) in ((x - 5, y + 4, 3), (x - 7, y + 10, 4), (x - 5, y + 16, 3)):
        flat(p, c.seg(gx, gy, gx + gw, gy, 1.2), mat, 1)


def v_eddy(p, mat, cx, cy, r=9):
    """A small eddy turning behind the print."""
    c = p.c
    pts = []
    for k in range(40):
        t = k / 39.0
        rr, a = r - t * (r - 1.5), t * 3.2 * math.pi
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.8))
    m = c.empty()
    for a_, b_ in zip(pts, pts[1:]):
        m |= c.seg(a_[0], a_[1], b_[0], b_[1], 1.6)
    flat(p, m, mat, 0)


def v_chevrons(p, mat, x, y, n=2, h=14):
    """The Lunge's chevrons driving forward, dust behind."""
    c = p.c
    for k in range(n):
        dx = x + 9 * k
        keyed(p, c.polyline([(dx, y - h), (dx + 9, y), (dx, y + h)], 3.4), mat, k)


def v_drops(p, mat, pts):
    c = p.c
    for (x, y) in pts:
        keyed(p, c.circle(x, y + 1, 1.7) | c.poly([(x - 1.3, y + 0.6), (x + 1.3, y + 0.6), (x, y - 2.6)]), mat, 1)


def v_domain_ring(p, mat, cx, base_y, rx=30, ry=6.5, front=False):
    """The Domain's ring laid on the ground round the caster, a corner mark at each quarter (the emblem's field)."""
    c = p.c
    ring = c.ring(cx, base_y, rx, 1.8, ry=ry)
    half = c.box(0, base_y, SCENE, SCENE) if front else c.box(0, 0, SCENE, base_y)
    keyed(p, ring & half, mat, -1 if not front else 0)
    for (px, py) in (((cx - rx, base_y), (cx + rx, base_y)) if not front else ((cx, base_y + ry),)):
        keyed(p, c.rrect(px - 2.2, py - 2.2, px + 2.2, py + 2.2, 0.6), mat, 1)


def v_spring(p, mat, x, base_y, h, w=3.6):
    """A spring rising from the ground: a column narrowing upward, spray at its head."""
    c = p.c
    col = c.taper((x, base_y), (x + 0.6, base_y - h * 0.55), (x, base_y - h), w, w * 0.45)
    head = c.circle(x, base_y - h - 1.2, w * 0.62)
    keyed(p, col | head, mat, 0)
    p.decal(c.seg(x - w * 0.18, base_y - 2, x - w * 0.18, base_y - h + 2, 1.0) & col, mat, 2)
    for s_ in (-1, 1):
        flat(p, c.circle(x + s_ * (w + 1.6), base_y - h + 1.5, 1.0), mat, 2)
        flat(p, c.circle(x + s_ * (w + 3.2), base_y - h + 6, 0.9), mat, 1)


WAVE = [(-16, 0), (-11, -3), (-6, -7.5), (-2, -11), (2, -13.5), (6, -13.8), (9.5, -12), (11.5, -9), (11.8, -6),
        (10.2, -5.2), (8.6, -7.2), (6.4, -8.2), (4, -7.2), (2.6, -4.6), (2.2, 0)]


def v_wave_ring(p, mat, cx, base_y, spread=21):
    """Two crests breaking outward from the caster, their lips curling over (the Rising Tide strikes both sides)."""
    c = p.c
    for s_ in (-1, 1):
        x = cx + s_ * spread
        crest = c.poly([(x + s_ * dx, base_y + dy) for dx, dy in WAVE])
        keyed(p, crest | c.box(x - 16, base_y - 1.5, x + 16, base_y + 1), mat, 0)
        foam = c.poly([(x + s_ * dx, base_y + dy) for dx, dy in WAVE[3:8]] + [(x + s_ * 8.5, base_y - 10.5), (x + s_ * 2, base_y - 11.4)])
        p.decal(foam & crest, mat, 2)
        flat(p, c.circle(x + s_ * 14, base_y - 12, 1.2), mat, 2)


def v_reeds_rain(p, mat, xs, top, ln):
    """Reed shafts falling on the ground (the Rain), the nearest ones longest."""
    c = p.c
    for i, x in enumerate(xs):
        t = top + (i % 3) * 4
        L = ln - (i % 2) * 5
        keyed(p, c.taper((x + 5, t), (x + 2.5, t + L / 2.0), (x, t + L), 1.0, 2.4), mat, i % 2)
        flat(p, c.seg(x - 0.6, t + L + 1.5, x + 1.2, t + L - 1.0, 1.2), mat, 2)


def v_halo(p, mat, cx, cy, r=10):
    c = p.c
    keyed(p, c.ring(cx, cy, r, 1.8), mat, 1)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        flat(p, c.circle(cx + (r + 3.2) * math.cos(a), cy - (r + 3.2) * math.sin(a), 0.9), mat, 2)


# ----------------------------------------------------------------------------- the scenes
TONES = {
    'water': dict(ramp=['#050e14', '#0c2a38', '#1a5068', '#3f8ea6', '#a6e2ee'], edge='#c8f0f6', rim='#2e8aa6',
                  halo='#62bcd0', halo_a=110),
    'wood': dict(ramp=['#06100a', '#12301c', '#245a34', '#5a9a5a', '#c6ec9e'], edge='#e0f8c0', rim='#2e8248',
                 halo='#5eb06a', halo_a=110),
    'fire': dict(ramp=['#120604', '#3a120c', '#7a2a14', '#c8602a', '#ffd89a'], edge='#fff0c0', rim='#b0401e',
                 halo='#e27436', halo_a=110),
    'jade': dict(ramp=['#050e14', '#10302e', '#1e5a52', '#4aa290', '#f2e2a8'], edge='#fff4c8', rim='#2c9e8f',
                 halo='#e5b84c', halo_a=120),
}


def scene(key, s):
    """Render scene `key` at scale s (1: the 72 px card, 2: the 144 px detail illustration); an RGBA array."""
    sc = SCENES[key]
    el = sc['element']
    img = ground(el, s, sc.get('horizon', 62.0), sc.get('light', (36.0, 34.0)), sc.get('floor', 'water'))
    mat = mk_mat(el, sc.get('path'), sc.get('ramp'))
    tone = TONES[sc.get('tone', el if el in TONES else 'water')]
    back = PixelPainter(SCENE, s)
    front = PixelPainter(SCENE, s)
    sc['draw'](back, front, mat, s, img, tone)
    b = np.array(back.image())
    paste(img, b, 0, 0)
    for f in sc['figs']:
        figure(img, s, f['action'], f['frame'], f['x'], f['y'], tone, f.get('weapon', 'none'), 1,
               f.get('alpha', 1.0), f.get('flip', False))
    fr = np.array(front.image())
    paste(img, fr, 0, 0)
    return img


def _flowing_palm(back, front, mat, s, img, tone):
    v_flurry(front, mat, (41, 36))
    v_drops(back, mat, ((12, 30), (8, 44)))


def _still_water_focus(back, front, mat, s, img, tone):
    v_ward_back(back, mat, 36, 62)
    v_ward_front(front, mat, 36, 62)


def _deep_pool_bloom(back, front, mat, s, img, tone):
    v_burst_back(back, mat, 36, 36, 31)
    v_splash_front(front, mat, 36, 62, 23)


def _kingfisher_step(back, front, mat, s, img, tone):
    v_blink_lines(back, mat, 22, 40, (30, 36, 42, 48))
    v_kingfisher(front, mat, 62, 58)


def _lotus_dew_hymn(back, front, mat, s, img, tone):
    v_chorus_back(back, mat, 36, 62)
    v_lotus_front(front, mat, 36, 62)


def _upright_eddy_seal(back, front, mat, s, img, tone):
    v_eddy(back, mat, 55, 30, 12)
    v_seal(front, mat, 44, 17, 22)


def _crimson_undertow_rush(back, front, mat, s, img, tone):
    v_chevrons(back, mat, 5, 38, 2, 13)
    v_drops(front, mat, ((63, 30), (66, 42), (60, 50)))


def _hundred_springs_rising(back, front, mat, s, img, tone):
    v_domain_ring(back, mat, 36, 61)
    v_spring(back, mat, 21, 60, 30, 3.6)
    v_spring(back, mat, 51, 60, 36, 3.6)
    v_spring(back, mat, 36, 58, 44, 3.0)
    v_domain_ring(front, mat, 36, 61, front=True)
    v_spring(front, mat, 9, 66, 22, 4.2)
    v_spring(front, mat, 63, 66, 26, 4.2)
    front.sparkle(36, 11, 1, '#ffe6a1')
    front.sparkle(15, 24, 1, '#ffe6a1')


def _rising_tide(back, front, mat, s, img, tone):
    v_wave_ring(back, mat, 36, 62, 22)
    v_drops(front, mat, ((10, 38), (62, 34), (58, 44)))


def _rain_of_reeds(back, front, mat, s, img, tone):
    v_reeds_rain(back, mat, (40, 48, 56, 64, 44, 60), 6, 22)


def _ember_burst(back, front, mat, s, img, tone):
    v_burst_back(back, mat, 36, 38, 30)
    for (x, y) in ((10, 20), (62, 18), (58, 52), (14, 54)):
        flat(front, front.c.diamond(x, y, 1.6), mat, 2)


def _lotus_mind(back, front, mat, s, img, tone):
    v_halo(back, mat, 35, 30, 12)
    v_lotus_front(front, mat, 36, 62, 1.1)


def _still_pool(back, front, mat, s, img, tone):
    pass


SCENES = {
    # the Water tree's free hand, Act I (docs/technique_plan.md §4, the Water keystones §3.7)
    'flowing_palm': dict(element='water', draw=_flowing_palm, light=(30, 32),
                         figs=[dict(action='punch', frame=3, x=24, y=64)]),
    'still_water_focus': dict(element='water', draw=_still_water_focus,
                              figs=[dict(action='meditate', frame=0, x=36, y=66)]),
    'deep_pool_bloom': dict(element='water', draw=_deep_pool_bloom,
                            figs=[dict(action='punch_3', frame=3, x=34, y=64)]),
    'kingfisher_step': dict(element='water', draw=_kingfisher_step, light=(44, 34),
                            figs=[dict(action='thrust_3', frame=4, x=14, y=64, alpha=0.35),
                                  dict(action='thrust_3', frame=5, x=44, y=64)]),
    'lotus_dew_hymn': dict(element='water', path='buddhist', draw=_lotus_dew_hymn,
                           figs=[dict(action='meditate', frame=0, x=36, y=64)]),
    'upright_eddy_seal': dict(element='water', path='confucian', draw=_upright_eddy_seal, light=(40, 32),
                              figs=[dict(action='punch_2', frame=3, x=22, y=64)]),
    'crimson_undertow_rush': dict(element='water', path='blood', draw=_crimson_undertow_rush, light=(42, 34),
                                  figs=[dict(action='thrust_3', frame=5, x=40, y=64)]),
    'hundred_springs_rising': dict(element='water', draw=_hundred_springs_rising, light=(36, 30),
                                   figs=[dict(action='meditate', frame=0, x=36, y=62)]),
    # Lost Arts found by Tester at ls6_end (Act I)
    'rising_tide': dict(element='water', draw=_rising_tide,
                        figs=[dict(action='punch_3', frame=4, x=36, y=64)]),
    'rain_of_reeds': dict(element='wood', floor='loam', draw=_rain_of_reeds, light=(30, 34),
                          figs=[dict(action='bow', frame=8, x=22, y=64, weapon='bow')]),
    'ember_burst': dict(element='fire', floor='stone', draw=_ember_burst, light=(36, 38),
                        figs=[dict(action='punch_3', frame=3, x=34, y=64)]),
    'lotus_mind': dict(element='water', tone='jade', ramp=['#9A6A20', '#D09A3A', '#FFE28C', '#FFF7D8', '#FFFFFF'],
                       draw=_lotus_mind, light=(36, 32), figs=[dict(action='meditate', frame=0, x=36, y=62)]),
}


def sealed_card(s=1):
    """A lost art not yet found (roadmap decision 19): one featureless face for all of them, so nothing tells one from
    another. Dark lacquer with a raised border, a gold cord tied across it and the red wax seal on the knot."""
    n = SCENE * s
    img = np.zeros((n, n, 4), np.uint8)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / s + 0.5 / s
    d = np.hypot(xx - 36, (yy - 36) * 1.1)
    img[...] = rgb('#0a1a1e') + (255,)
    img[d < 30] = rgb('#0d2226') + (255,)
    img[d < 18] = rgb('#10292d') + (255,)
    edge = (xx < 3) | (xx > 69) | (yy < 3) | (yy > 69)
    img[edge] = rgb('#16393a') + (255,)
    inner = ((xx >= 3) & (xx < 4)) | ((yy >= 3) & (yy < 4))
    img[inner & ~edge & (xx < 69) & (yy < 69)] = rgb('#24544f') + (255,)
    p = PixelPainter(SCENE, s)
    c = p.c
    gold, red = M('gold'), M('seal')
    cord = c.seg(0, 38, 72, 34, 2.2) | c.seg(34, 0, 38, 72, 2.2)
    p.part(cord, gold, 'flat', base=-1, sep=False, rim=False)
    p.decal(c.seg(0, 37.4, 72, 33.4, 0.8) | c.seg(33.4, 0, 37.4, 72, 0.8), gold, 1)
    for a in (205, 245):
        r = math.radians(a)
        loop = c.ring(36 + 7 * math.cos(r), 36 - 7 * math.sin(r), 4.2, 1.8)
        p.part(loop, gold, 'flat', base=0, sep=True, rim=False)
    wax = c.circle(36, 36, 9.6)
    for k in range(9):
        a = math.radians(k * 40 + 10)
        wax |= c.circle(36 + 9.4 * math.cos(a), 36 + 9.4 * math.sin(a), 2.2)
    p.part(wax, red, 'sphere', base=0, sep=True, cx=33, cy=33, rx=12, ry=12)
    p.decal(c.ring(36, 36, 6.2, 1.2), red, -2)
    p.decal(c.arc(36, 36, 3.4, 1.3, 30, 300), red, -2)
    p.sparkle(31, 30, 1, '#ffd0b8')
    paste(img, np.array(p.image()), 0, 0)
    return img


def drain(img, amount=0.82, dim=0.62):
    """A locked node's picture: the same scene drained towards the page's slate."""
    a = img.astype(np.float32)
    lum = a[..., 0] * 0.3 + a[..., 1] * 0.55 + a[..., 2] * 0.15
    slate = np.stack([lum * 0.92, lum * 1.0, lum * 1.04], -1)
    a[..., :3] = (a[..., :3] * (1 - amount) + slate * amount) * dim
    return np.clip(a, 0, 255).astype(np.uint8)


LOCKED = {'kingfisher_step', 'lotus_dew_hymn', 'crimson_undertow_rush'}


# The emblems of the arts the mockups name that have no row yet (docs/technique_plan.md §3.9), by the composer
EMBLEMS = [
    ('deep_pool_bloom', emblem('water', 'burst', 'any', 'heaven')),
    ('kingfisher_step', emblem('water', 'blink', 'any', 'mystic')),
    ('lotus_dew_hymn', emblem('water', 'chorus', 'any', 'earth', path='buddhist')),
    ('upright_eddy_seal', emblem('water', 'seal', 'any', 'heaven', path='confucian')),
    ('crimson_undertow_rush', emblem('water', 'lunge', 'any', 'mystic', path='blood')),
    ('hundred_springs_rising', emblem('water', 'domain', 'any', 'mystic', kind='keystone')),
]


def save(arr, name):
    path = os.path.join(OUT, name)
    Image.fromarray(arr, 'RGBA').save(path, format='PNG', optimize=False, compress_level=9)
    print(os.path.relpath(path, PROJECT))


def main(keys=None):
    os.makedirs(OUT, exist_ok=True)
    if not keys or 'sealed' in keys:
        save(sealed_card(1), 'techcard_sealed.png')
    for ident, draw in EMBLEMS:
        if keys and ident not in keys:
            continue
        for tag, scale in (('emblemA_', 1.0), ('emblemA48_', 0.75)):
            p = PixelPainter(64, scale)
            draw(p)
            p.image().save(os.path.join(OUT, tag + ident + '.png'), format='PNG', optimize=False, compress_level=9)
            print(os.path.relpath(os.path.join(OUT, tag + ident + '.png'), PROJECT))
    for key in [k for k in (keys or SCENES) if k in SCENES]:
        card = scene(key, 1)
        art = scene(key, 2)
        save(drain(card) if key in LOCKED else card, 'techcard_%s.png' % key)
        save(art, 'techart_%s.png' % key)


if __name__ == '__main__':
    main(sys.argv[1:] or None)
