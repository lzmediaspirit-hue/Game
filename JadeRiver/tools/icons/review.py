"""Review sheets for the icon build, drawn with the game's own kit art, fonts and sizes.

`family_sheets` writes, for one family module: the contact sheet (every icon in the 76 px page slot as the
game shows it, and beside it what the game draws at 48 and 32), the same at x2, and an in-context composite
(a bag grid of 76 px slots, the HUD technique ring at 48 and the item ring at 32, the attack ring at 64).
The helpers (nine-slice kit frames, the HUD ring, fonts) are shared with the style study (tools/icons/study).
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pix import rgb, mix

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(HERE, '..', '..'))
ART = os.path.join(PROJECT, 'art')

# UiKit tokens
INK = (7, 16, 21)
RIVER_NIGHT = (10, 32, 39)
DEEP_TEAL = (13, 48, 53)
BRONZE = (154, 106, 53)
GOLD = (229, 184, 76)
PALE_GOLD = (255, 230, 161)
PAPER = (232, 225, 207)
MIST = (175, 201, 209)
HOLLOW = (135, 148, 154)
SLOT = 76          # the page slot (page.gd Page.SLOT): a 64 px icon at 1:1, inset 6
RING_TECH, RING_ITEM, RING_ATTACK = 33, 26, 66     # hud.gd ring radii: techniques (48), item rings (32), attack (64)

with open(os.path.join(PROJECT, 'data', 'grades.json'), encoding='utf-8') as _f:
    GRADE_COL = {k: rgb(v) for k, v in json.load(_f)['grade_colors'].items()}

# ----------------------------------------------------------------------------- fonts and words
FONT_TEXT = os.path.join(ART, 'fonts', 'SourceSerif4.ttf')
FONT_DISPLAY = os.path.join(ART, 'fonts', 'CormorantGaramond.ttf')
_fonts = {}


def font(kind, size):
    key = (kind, size)
    if key not in _fonts:
        display = kind in ('title', 'display')
        f = ImageFont.truetype(FONT_DISPLAY if display else FONT_TEXT, size)
        f.set_variation_by_name('Bold' if display or kind == 'bold' else 'SemiBold')
        _fonts[key] = f
    return _fonts[key]


def text(d, xy, s, kind='text', size=16, col=PAPER, anchor='la', shadow=True, outline=False):
    f = font(kind, size)
    x, y = xy
    if outline:
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx * dx + dy * dy <= 4:
                    d.text((x + dx, y + dy), s, font=f, fill=INK, anchor=anchor)
    elif shadow:
        d.text((x, y + 2), s, font=f, fill=(0, 0, 0, 140), anchor=anchor)
        d.text((x + 1, y + 1), s, font=f, fill=(0, 0, 0, 115), anchor=anchor)
    d.text((x, y), s, font=f, fill=col, anchor=anchor)


def para(d, xy, s, width, kind='text', size=14, col=MIST, leading=None):
    """Word-wrapped paragraph; returns the y below it."""
    f = font(kind, size)
    lines, cur = [], ''
    for w in s.split(' '):
        trial = (cur + ' ' + w).strip()
        if d.textlength(trial, font=f) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    x, y = xy
    for ln in lines:
        text(d, (x, y), ln, kind, size, col)
        y += leading or int(size * 1.35)
    return y


# ----------------------------------------------------------------------------- kit frames
def kit(name):
    return Image.open(os.path.join(ART, 'ui', 'hd', name + '.png')).convert('RGBA')


def nine_slice(src, w, h, slice_px, border_px):
    """CSS border-image with `stretch`: corners scaled from slice_px to border_px, edges and centre stretched."""
    sw, sh = src.size
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sx, sy = (slice_px, slice_px) if isinstance(slice_px, int) else slice_px
    bx, by = (border_px, border_px) if isinstance(border_px, int) else border_px
    cx, cy = sw - 2 * sx, sh - 2 * sy
    iw, ih = max(0, w - 2 * bx), max(0, h - 2 * by)
    res = Image.Resampling.BOX if (sx > bx) else Image.Resampling.BILINEAR

    def put(box, dst):
        dw, dh = dst[2] - dst[0], dst[3] - dst[1]
        if dw > 0 and dh > 0:
            out.alpha_composite(src.crop(box).resize((dw, dh), res), (dst[0], dst[1]))
    put((0, 0, sx, sy), (0, 0, bx, by))
    put((sw - sx, 0, sw, sy), (w - bx, 0, w, by))
    put((0, sh - sy, sx, sh), (0, h - by, bx, h))
    put((sw - sx, sh - sy, sw, sh), (w - bx, h - by, w, h))
    put((sx, 0, sx + cx, sy), (bx, 0, bx + iw, by))
    put((sx, sh - sy, sx + cx, sh), (bx, h - by, bx + iw, h))
    put((0, sy, sx, sy + cy), (0, by, bx, by + ih))
    put((sw - sx, sy, sw, sy + cy), (w - bx, by, w, by + ih))
    put((sx, sy, sx + cx, sy + cy), (bx, by, bx + iw, by + ih))
    return out


def slot(size, state='normal'):
    return nine_slice(kit('slot__' + state), size, size, 24, 8)


def slot_glow(size):
    return nine_slice(kit('selected_slot_glow__normal'), size + 8, size + 8, 36, 12)


def minor_panel(w, h):
    return nine_slice(kit('minor_panel__normal'), w, h, 36, 12)


def major_window(w, h):
    return nine_slice(kit('major_window__normal'), w, h, 96, 32)


def plaque(w, h=60):
    return nine_slice(kit('title_plaque__normal'), w, h, (144, 78), (int(round(h * 0.923)), int(round(h * 0.5))))


def tab(w, selected=False):
    return nine_slice(kit('tab__selected' if selected else 'tab__normal'), w, 48, (48, 30), (16, 10))


def button2(w, h=48):
    return nine_slice(kit('button_secondary__normal'), w, h, (42, 36), (14, 12))


def qrim(size, col, inset=3, w=2):
    """page.gd: draw_rect(rect.grow(-3), colour, false, 2) - the quality / grade rim."""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([inset, inset, size - 1 - inset, size - 1 - inset], outline=col, width=w)
    return im


def with_alpha(img, a):
    arr = np.asarray(img, np.uint8).copy()
    arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def hud_ring(radius, active=False, gold=False, ss=4):
    """hud.gd ring(): the shadow, the gold rim disc, the jade disc, the inner jade arc and the highlight arc.
    Returns (image, pad): the ring's centre is at (pad, pad)."""
    r, pad = radius, 14
    n = int((r + pad) * 2 * ss)
    cx = cy = (r + pad) * ss
    yy, xx = np.mgrid[0:n, 0:n]
    X, Y = xx + 0.5 - cx, yy + 0.5 - cy
    D = np.sqrt(X * X + Y * Y) / ss
    out_rgb = np.zeros((n, n, 3), np.float32)
    out_a = np.zeros((n, n), np.float32)

    def over(col, a):
        nonlocal out_rgb, out_a
        a = np.clip(a, 0, 1).astype(np.float32)
        out_rgb = np.asarray(col, np.float32) * a[..., None] + out_rgb * (1 - a)[..., None]
        out_a = a + out_a * (1 - a)

    def disc(rad, top, bottom):
        Yd, Xd = (yy + 0.5 - cy) / ss, X / ss
        Dd = np.sqrt(Xd * Xd + Yd * Yd)
        t = np.clip((Yd / rad + 1) * 0.5, 0, 1)[..., None]
        over(np.array(rgb(top), np.float32) * (1 - t) + np.array(rgb(bottom), np.float32) * t, np.clip(rad - Dd + 0.5, 0, 1))
        over(np.broadcast_to(np.array(mix(bottom, top, 0.3), np.float32), (n, n, 3)), np.clip(1.0 - np.abs(Dd - rad), 0, 1) * 0.6)

    def arc(rad, width, col, alpha, a0=0.0, a1=2 * math.pi):
        ang = np.arctan2(Y, X) % (2 * math.pi)
        sel = (ang >= a0) & (ang <= a1) if a0 <= a1 else ((ang >= a0) | (ang <= a1))
        over(np.broadcast_to(np.array(rgb(col), np.float32), (n, n, 3)), np.clip(width / 2.0 - np.abs(D - rad) + 0.5, 0, 1) * alpha * sel)

    lit = active or gold
    Ds = np.sqrt((X / ss) ** 2 + ((yy + 0.5 - cy - 4 * ss) / ss) ** 2)
    over(np.zeros((n, n, 3), np.float32), np.clip(r + 4 - Ds + 0.5, 0, 1) * 0.42)
    if lit:
        for i in range(3):
            arc(r + 5 + i * 3, 3.0, '#E5B84C', 0.30 - i * 0.09)
    disc(r + 2.5, '#f0d08a' if lit else '#c6a262', '#7a5426' if lit else '#5c4424')
    disc(r, '#1d5157', '#061519')
    arc(r - 3.5, 1.5, (102, 214, 189), 0.30 if lit else 0.2)
    arc(r - 2.0, max(2.0, r * 0.07), (255, 255, 255), 0.12, math.pi * 1.15, math.pi * 1.85)
    m = n // ss
    pm = (out_rgb * out_a[..., None]).reshape(m, ss, m, ss, 3).mean(axis=(1, 3))
    a = out_a.reshape(m, ss, m, ss).mean(axis=(1, 3))
    arr = np.zeros((m, m, 4), np.uint8)
    arr[..., :3] = np.clip(np.where(a[..., None] > 1e-4, pm / np.maximum(a[..., None], 1e-4), 0) + 0.5, 0, 255).astype(np.uint8)
    arr[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA'), (r + pad)


def scale_nearest(img, size):
    return img.resize((size, size), Image.Resampling.NEAREST)


def scale_box(img, size):
    """Area-average downscale on premultiplied alpha (what a good filter gives)."""
    arr = np.asarray(img.convert('RGBA'), np.float32)
    a = arr[..., 3:4] / 255.0
    pm = Image.fromarray(np.concatenate([arr[..., :3] * a, arr[..., 3:4]], axis=2).astype(np.uint8), 'RGBA')
    sa = np.asarray(pm.resize((size, size), Image.Resampling.BOX if size < img.width else Image.Resampling.BICUBIC), np.float32)
    al = sa[..., 3:4] / 255.0
    rgb_ = np.where(al > 1e-3, sa[..., :3] / np.maximum(al, 1e-3), 0)
    return Image.fromarray(np.concatenate([np.clip(rgb_, 0, 255), sa[..., 3:4]], axis=2).astype(np.uint8), 'RGBA')


# ----------------------------------------------------------------------------- what the game draws
def fit(renders, target):
    """The icon as the game draws it in a `target` px box (SpriteCache.icon_fit): the render and whole-number
    scale giving the largest size that fits, the larger native render on a tie; the smallest at 1x if none fits.
    `renders`: {art px: image} (a legacy icon's 64 px PNG holds 32 art px)."""
    best = None
    for n in sorted(renders, reverse=True):
        k = target // n
        if k >= 1 and (best is None or n * k > best[0] * best[1]):
            best = (n, k)
    n, k = best or (min(renders), 1)
    return scale_nearest(renders[n], n * k)


def technique_ring_fit(renders):
    """hud.gd draw_skill_slot: an HD technique's native 48, or a legacy one's 32 art px at 2x (1x is lost in the ring)."""
    return renders[48] if 48 in renders else fit(renders, 64)


# The small families and where the game shows them: (label, the box of the second size shown, its label).
SMALL = {'status': ('the HUD status row: 24 at 1:1', 14, 'over an enemy: its native 12'),
         'markers': ('the world map: 24 at 1:1', 48, 'a large page: 24 at 2x')}


def family_sheets(name, icons, out_dir, grades=None, folder='items'):
    """Write the review sheets of family module `name` (in art/icons/<folder>).
    icons: [(id, renders {art px: image}, hd: bool)]."""
    os.makedirs(out_dir, exist_ok=True)
    if folder in SMALL:
        return small_sheets(name, icons, out_dir, folder)
    grades = grades or {}
    written = []
    n_hd = sum(1 for _, _, h in icons if h)
    head = '%s · %d icons · %d HD' % (name, len(icons), n_hd)
    middle = technique_ring_fit if folder == 'techniques' else (lambda r: fit(r, 48))
    CW, CH, COLS, PER = 192, 104, 6, 36
    for pi in range(0, len(icons), PER):
        page = icons[pi:pi + PER]
        rows = (len(page) + COLS - 1) // COLS
        im = Image.new('RGBA', (COLS * CW + 24, rows * CH + 64), DEEP_TEAL + (255,))
        d = ImageDraw.Draw(im)
        text(d, (12, 8), head + ('' if len(icons) <= PER else ' · page %d' % (pi // PER + 1)), 'display', 24, PALE_GOLD)
        text(d, (12, 38), 'the 76 px slot (64 at 1:1), then what the game draws %s and at 32; a legacy icon is its 32 art px '
             'at a whole-number scale' % ('in the technique ring' if folder == 'techniques' else 'at 48'), 'text', 13, MIST)
        for k, (ident, renders, is_hd) in enumerate(page):
            x, y = 12 + (k % COLS) * CW, 60 + (k // COLS) * CH
            im.alpha_composite(slot(SLOT), (x, y))
            im.alpha_composite(fit(renders, 64), (x + 6, y + 6))
            g = grades.get(ident)
            if g in GRADE_COL and g not in ('plain', 'common'):
                im.alpha_composite(qrim(SLOT, GRADE_COL[g]), (x, y))
            mid = middle(renders)
            im.alpha_composite(mid, (x + SLOT + 6, y))
            im.alpha_composite(fit(renders, 32), (x + SLOT + 12 + mid.width, y + 16))
            label = ident if len(ident) <= 22 else ident[:21] + '~'
            text(d, (x, y + SLOT + 3), label, 'text', 12, PAPER if is_hd else HOLLOW, shadow=False)
        base = os.path.join(out_dir, 'icons_%s_p%d' % (name, pi // PER + 1))
        im.save(base + '.png')
        im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST).save(base + '_x2.png')
        written += [base + '.png', base + '_x2.png']
    written.append(context_sheet(name, icons, out_dir, grades, folder))
    return written


def context_sheet(name, icons, out_dir, grades, folder):
    """The family in context: a Bag grid of 76 px slots, and the HUD rings the family appears in, at their real
    sizes (techniques: the technique ring; items and equipment: the item ring; HUD glyphs: a button ring and the
    attack ring)."""
    im = Image.new('RGBA', (1180, 360), RIVER_NIGHT + (255,))
    d = ImageDraw.Draw(im)
    text(d, (16, 10), '%s in context' % name, 'display', 24, PALE_GOLD)
    SL, GAP = SLOT, 6
    gx, gy = 16, 52
    gw, gh = 2 * 16 + 5 * SL + 4 * GAP, 2 * 16 + 3 * SL + 2 * GAP
    im.alpha_composite(minor_panel(gw, gh), (gx, gy))
    for k, (ident, renders, _) in enumerate(icons[:15]):
        x, y = gx + 16 + (k % 5) * (SL + GAP), gy + 16 + (k // 5) * (SL + GAP)
        im.alpha_composite(slot(SL, 'selected' if k == 0 else 'normal'), (x, y))
        im.alpha_composite(fit(renders, 64), (x + 6, y + 6))
        g = grades.get(ident)
        if g in GRADE_COL and g not in ('plain', 'common'):
            im.alpha_composite(qrim(SL, GRADE_COL[g]), (x, y))
        if k == 0:
            im.alpha_composite(slot_glow(SL), (x - 4, y - 4))
    rows = {'techniques': [('technique ring · native 48, legacy 32 at 2x', RING_TECH, technique_ring_fit, 7)],
            'hud': [('button ring · 32', RING_ITEM, lambda r: fit(r, 32), 7), ('attack ring · 64', RING_ATTACK, lambda r: fit(r, 64), 3)]
            }.get(folder, [('item ring · 32', RING_ITEM, lambda r: fit(r, 32), 8)])
    rx, y = gx + gw + 40, gy + 10
    for label, radius, draw, n in rows:
        ring, pad = hud_ring(radius, active=(radius == RING_ATTACK))
        text(d, (rx, y), label, 'text', 14, MIST)
        cy = y + 28 + radius
        for k, (ident, renders, _) in enumerate(icons[:n]):
            cx = rx + radius + 8 + k * (2 * radius + 24)
            im.alpha_composite(ring, (int(cx - pad), int(cy - pad)))
            g = draw(renders)
            im.alpha_composite(g, (cx - g.width // 2, cy - g.height // 2))
        y = cy + radius + 26
    path = os.path.join(out_dir, 'icons_%s_context.png' % name)
    im.save(path)
    return path


def small_sheets(name, icons, out_dir, folder):
    """The sheets of a small family (status icons, markers): every icon at the sizes the game shows it, on the HUD's
    night ground, the same at x2, and in context (the HUD's status row and an enemy's name, or the map's rows)."""
    first, box2, second = SMALL[folder]
    CW, CH, COLS = 196, 92, 6
    rows = (len(icons) + COLS - 1) // COLS
    im = Image.new('RGBA', (COLS * CW + 24, rows * CH + 64), DEEP_TEAL + (255,))
    d = ImageDraw.Draw(im)
    text(d, (12, 8), '%s · %d icons · %d HD' % (name, len(icons), sum(1 for _, _, h in icons if h)), 'display', 24, PALE_GOLD)
    text(d, (12, 38), '%s, then %s' % (first, second), 'text', 13, MIST)
    for k, (ident, renders, is_hd) in enumerate(icons):
        x, y = 12 + (k % COLS) * CW, 60 + (k // COLS) * CH
        im.alpha_composite(Image.new('RGBA', (CW - 12, 62), RIVER_NIGHT + (255,)), (x, y))
        im.alpha_composite(fit(renders, 24), (x + 12, y + 19))
        g = fit(renders, box2)
        im.alpha_composite(g, (x + 60 + (48 - g.width) // 2, y + 31 - g.height // 2))
        label = ident if len(ident) <= 24 else ident[:23] + '~'
        text(d, (x, y + 65), label, 'text', 12, PAPER if is_hd else HOLLOW, shadow=False)
    base = os.path.join(out_dir, 'icons_%s_p1' % name)
    im.save(base + '.png')
    im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST).save(base + '_x2.png')
    ctx = Image.new('RGBA', (1180, 250), RIVER_NIGHT + (255,))
    d = ImageDraw.Draw(ctx)
    text(d, (16, 10), '%s in context' % name, 'display', 24, PALE_GOLD)
    if folder == 'status':
        ctx.alpha_composite(minor_panel(760, 96), (16, 52))
        text(d, (34, 64), 'under the player panel: 24 px icons, 4 apart', 'text', 14, MIST)
        for k, (ident, renders, _) in enumerate(icons[:24]):
            ctx.alpha_composite(fit(renders, 24), (34 + k * 28, 100))
        text(d, (830, 120), 'Lv 103  Scarlet Kiln Disciple', 'bold', 17, (245, 138, 58), anchor='mm', outline=True)
        for k, (ident, renders, _) in enumerate(icons[:12]):
            ctx.alpha_composite(fit(renders, 14), (830 - 6 * 14 + k * 14, 90))
    else:
        ctx.alpha_composite(minor_panel(1140, 170), (16, 52))
        for k, (ident, renders, _) in enumerate(icons):
            x, y = 36 + (k % 4) * 280, 70 + (k // 4) * 30
            ctx.alpha_composite(fit(renders, 24), (x, y))
            text(d, (x + 29, y + 4), ident.replace('_', ' '), 'text', 14, PAPER)
    path = os.path.join(out_dir, 'icons_%s_context.png' % name)
    ctx.save(path)
    return [base + '.png', base + '_x2.png', path]
