#!/usr/bin/env python3
"""Icon style study: draws 12 icons in two candidate styles and composes the review sheets.

    python3 tools/icons/study/icon_study.py            # -> docs/mockups/icon_study/*.png

Sheets (all at real game sizes, on the dark panel colour):
  01_before_after.png   today | Style A | Style B in the HD slot frame, at 64 and at 48
  02_grade_ladder.png   the jian at Common, Spirit, Sage and Will in both styles; the empty-slot motif
  03_hud_rings.png      HUD glyphs and techniques in the HUD ring frames at their mockup sizes
  04_bag_A.png / 04_bag_B.png   a Bag page at 1280x720 with a 5x3 grid of slots filled with the study icons
  icons/                every rendered icon as a PNG (A_*.png, B_*.png, A48_*.png)

Deterministic: same code -> byte-identical output. Nothing here touches art/icons or the manifest.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))

import study_lib as L  # noqa: E402
import study_icons as I  # noqa: E402

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ART = os.path.join(PROJECT, 'art')
OUT = os.path.join(PROJECT, 'docs', 'mockups', 'icon_study')

# UiKit tokens
INK = (7, 16, 21)
RIVER_NIGHT = (10, 32, 39)
DEEP_TEAL = (13, 48, 53)
JADE = (44, 158, 143)
BRIGHT_JADE = (103, 214, 189)
BRONZE = (154, 106, 53)
GOLD = (229, 184, 76)
PALE_GOLD = (255, 230, 161)
PAPER = (232, 225, 207)
MIST = (175, 201, 209)
HOLLOW = (135, 148, 154)
RED = (228, 88, 88)

FONT_TEXT = os.path.join(ART, 'fonts', 'SourceSerif4.ttf')
FONT_DISPLAY = os.path.join(ART, 'fonts', 'CormorantGaramond.ttf')
_fonts = {}


def font(kind, size):
    key = (kind, size)
    if key in _fonts:
        return _fonts[key]
    if kind in ('title', 'display'):
        f = ImageFont.truetype(FONT_DISPLAY, size)
        f.set_variation_by_name('Bold')
    else:
        f = ImageFont.truetype(FONT_TEXT, size)
        f.set_variation_by_name('Bold' if kind == 'bold' else 'SemiBold')
    _fonts[key] = f
    return f


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
    words = s.split(' ')
    lines, cur = [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if d.textlength(trial, font=f) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    x, y = xy
    lh = leading or int(size * 1.35)
    for ln in lines:
        text(d, (x, y), ln, kind, size, col)
        y += lh
    return y


# ----------------------------------------------------------------------------- kit pieces
def kit(name):
    return Image.open(os.path.join(ART, 'ui', 'hd', name + '.png')).convert('RGBA')


def slot(size, state='normal'):
    return L.nine_slice(kit('slot__' + state), size, size, 24, 8)


def slot_glow(size):
    return L.nine_slice(kit('selected_slot_glow__normal'), size + 8, size + 8, 36, 12)


def minor_panel(w, h):
    return L.nine_slice(kit('minor_panel__normal'), w, h, 36, 12)


def major_window(w, h):
    return L.nine_slice(kit('major_window__normal'), w, h, 96, 32)


def plaque(w, h=60):
    return L.nine_slice(kit('title_plaque__normal'), w, h, (144, 78), (int(round(h * 0.923)), int(round(h * 0.5))))


def tab(w, selected=False):
    return L.nine_slice(kit('tab__selected' if selected else 'tab__normal'), w, 48, (48, 30), (16, 10))


def button2(w, h=48):
    return L.nine_slice(kit('button_secondary__normal'), w, h, (42, 36), (14, 12))


def today_icon(family, ident):
    return Image.open(os.path.join(ART, 'icons', family, ident + '.png')).convert('RGBA')


def empty_motif_today():
    return Image.open(os.path.join(ART, 'ui', 'slot_empty_motif__normal.png')).convert('RGBA')


def with_alpha(img, a):
    arr = np.asarray(img, np.uint8).copy()
    arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def qrim(size, col, inset=3, w=2):
    """page.gd: draw_rect(rect.grow(-3), colour, false, 2) - the quality / grade rim."""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([inset, inset, size - 1 - inset, size - 1 - inset], outline=col, width=w)
    return im


# ----------------------------------------------------------------------------- rendering the study icons
def render_all():
    icons = {}
    os.makedirs(os.path.join(OUT, 'icons'), exist_ok=True)

    def keep(key, img):
        icons[key] = img
        img.save(os.path.join(OUT, 'icons', key + '.png'), format='PNG', optimize=False, compress_level=9)

    for ident, fam, today, fn, kw, label in I.ITEMS:
        p = L.PixelPainter(64)
        fn(p, **kw)
        keep('A_' + ident, p.image())
        p = L.PixelPainter(64, 0.75)
        fn(p, **kw)
        keep('A48_' + ident, p.image())
        p = L.PaintedPainter(64, 4)
        fn(p, **kw)
        keep('B_' + ident, p.image())
    for g in I.LADDER:
        p = L.PixelPainter(64)
        I.jian(p, g)
        keep('A_jian_' + g, p.image())
        p = L.PaintedPainter(64, 4)
        I.jian(p, g)
        keep('B_jian_' + g, p.image())
    for ident, fam, today, fn, kw, label in I.HUD:
        p = L.PixelPainter(32)
        fn(p)
        keep('A_hud_' + ident, p.image())
        p = L.PaintedPainter(32, 4)
        fn(p)
        keep('B_hud_' + ident, p.image())
        p = L.PaintedPainter(32, 8)
        p.size = 64          # 32-px description rendered to a 64-px output (256 / 4)
        fn(p)
        keep('B64_hud_' + ident, p.image())
    p = L.PixelPainter(64)
    I.empty_motif(p)
    keep('A_empty', p.image())
    p = L.PaintedPainter(64, 4)
    I.empty_motif(p)
    keep('B_empty', p.image())
    return icons


# ----------------------------------------------------------------------------- sheet 1: before / after
def sheet_before_after(icons):
    rows = I.ITEMS
    TOP = 150
    W, H = 1040, TOP + 96 * len(rows) + 230
    im = Image.new('RGBA', (W, H), DEEP_TEAL + (255,))
    d = ImageDraw.Draw(im)
    text(d, (24, 18), 'Icon style study · before and after', 'title', 31, PALE_GOLD)
    para(d, (24, 60), 'In the HD kit slot on the panel colour. Today: the 64 px icon drawn at 52 px, as page.gd draws it (nearest). '
         'Style A and Style B: 64 art px at 1:1 in a 76 px slot. Right: the four at the HUD technique size, 48 px, in a 60 px slot: '
         "today (nearest), A box-filtered from 64, A re-rendered at 48 from the same description, B box-filtered from 64.", W - 48)
    cols = [('Today', '64 → 52', 64), ('Style A', 'HD pixel, 64', 76), ('Style B', 'painted, 64', 76)]
    x = 190
    heads = []
    for name, sub, size in cols:
        heads.append((x, name, size))
        text(d, (x + size // 2, TOP - 40), name, 'bold', 14, GOLD, anchor='ma')
        text(d, (x + size // 2, TOP - 22), sub, 'text', 13, MIST, anchor='ma')
        x += size + 22
    x48 = x + 10
    heads48 = [(x48 + k * 66, n) for k, n in enumerate(('Today', 'A ÷ box', 'A native', 'B ÷ box'))]
    text(d, (x48 + 132, TOP - 40), 'at 48 px (the HUD technique ring)', 'bold', 14, GOLD, anchor='ma')
    for hx, name in heads48:
        text(d, (hx + 30, TOP - 22), name, 'text', 13, MIST, anchor='ma')
    for r, (ident, fam, today, fn, kw, label) in enumerate(rows):
        y = TOP + r * 96
        text(d, (24, y + 26), label, 'text', 16, PAPER)
        text(d, (24, y + 48), fam, 'text', 13, HOLLOW)
        t_img = today_icon(fam, today)
        for hx, name, size in heads:
            fr = slot(size)
            im.alpha_composite(fr, (hx, y))
            if name == 'Today':
                ic = L.scale_nearest(t_img, 52)
                im.alpha_composite(ic, (hx + 6, y + 6))
            elif name.startswith('Style A'):
                im.alpha_composite(icons['A_' + ident], (hx + 6, y + 6))
            else:
                im.alpha_composite(icons['B_' + ident], (hx + 6, y + 6))
        # 48 px: in a 60 px slot (48 + 6 + 6)
        variants = [L.scale_nearest(t_img, 48), L.scale_box(icons['A_' + ident], 48), icons['A48_' + ident],
                    L.scale_box(icons['B_' + ident], 48)]
        for (hx, name), v in zip(heads48, variants):
            im.alpha_composite(slot(60), (hx, y + 8))
            im.alpha_composite(v, (hx + 6, y + 14))
    # the 64-px slot question
    y = TOP + len(rows) * 96 + 8
    d.line([(24, y), (W - 24, y)], fill=BRONZE, width=2)
    text(d, (24, y + 12), 'The 64 px slot: three ways to show a 64-px icon', 'display', 24, GOLD)
    yb = para(d, (24, y + 46), 'page.gd and the kit inset the icon 6 px, so a 64 px slot shows 52 px of icon. In each group: left, a 64 px slot with '
                            'the icon scaled to 52 (box filter); middle, a 76 px slot with the icon at 1:1; right, a 64 px slot with the icon at 1:1 '
                            'and inset 0 (the art keeps a 4 px margin, so the object overlaps the rim by 4 px).', W - 48, size=13)
    x = 24
    for k, (ident, fam) in enumerate((('iron_jian', 'equipment'), ('healing_pill', 'items'), ('star_lotus', 'items'))):
        for style in ('A', 'B'):
            ic = icons[style + '_' + ident]
            yy = yb + 16
            im.alpha_composite(slot(64), (x, yy))
            im.alpha_composite(L.scale_box(ic, 52), (x + 6, yy + 6))
            im.alpha_composite(slot(76), (x + 72, yy - 6))
            im.alpha_composite(ic, (x + 78, yy))
            im.alpha_composite(slot(64), (x + 156, yy))
            im.alpha_composite(ic, (x + 156, yy))
            text(d, (x + 110, yy + 78), style + ' · ' + ident.replace('_', ' '), 'text', 13, HOLLOW, anchor='ma')
            x += 236
            if x > W - 230:
                break
        if x > W - 230:
            break
    return im


# ----------------------------------------------------------------------------- sheet 2: the grade ladder
def sheet_grade_ladder(icons):
    W, H = 860, 740
    im = Image.new('RGBA', (W, H), DEEP_TEAL + (255,))
    d = ImageDraw.Draw(im)
    text(d, (24, 18), 'Grade ladder · the jian at Common, Spirit, Sage and Will', 'title', 31, PALE_GOLD)
    para(d, (24, 60), 'Grade changes the material, the fittings, the blade work and the glow: stepped bands in A, a soft outer and inner glow in B. '
         'The slot adds the grade rim (data/grades.json grade_colors), as page.gd draws the quality rim today. The 2x rows are for inspection only.', W - 48)
    names = {'common': 'Common · iron', 'spirit': 'Spirit · stormsteel', 'sage': 'Sage · sunsteel', 'will': 'Will · night steel'}
    for si, style in enumerate(('A', 'B')):
        y0 = 120 + si * 300
        text(d, (24, y0), 'Style A · HD pixel' if style == 'A' else 'Style B · painted', 'display', 24, GOLD)
        for k, g in enumerate(I.LADDER):
            x = 24 + k * 170
            ic = icons[style + '_jian_' + g]
            im.alpha_composite(slot(76), (x, y0 + 36))
            im.alpha_composite(ic, (x + 6, y0 + 42))
            if g != 'common':
                im.alpha_composite(qrim(76, tuple(int(I.GRADE_COL[g].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))), (x, y0 + 36))
            text(d, (x + 38, y0 + 116), names[g], 'text', 13, MIST, anchor='ma')
            big = ic.resize((128, 128), Image.Resampling.NEAREST if style == 'A' else Image.Resampling.BICUBIC)
            im.alpha_composite(big, (x - 26 + 38, y0 + 136 - 8))
        # the empty-slot motif
        x = 24 + 4 * 170 + 6
        text(d, (x + 38, y0 + 8), 'empty slot', 'text', 13, MIST, anchor='ma')
        im.alpha_composite(slot(76), (x, y0 + 36))
        im.alpha_composite(with_alpha(icons[style + '_empty'], 0.35), (x + 6, y0 + 42))
        text(d, (x + 38, y0 + 116), 'motif at 35%', 'text', 13, HOLLOW, anchor='ma')
        im.alpha_composite(slot(64), (x + 6, y0 + 140))
        im.alpha_composite(with_alpha(L.scale_nearest(empty_motif_today(), 48), 0.35), (x + 14, y0 + 148))
        text(d, (x + 38, y0 + 208), 'today (64)', 'text', 13, HOLLOW, anchor='ma')
    return im


# ----------------------------------------------------------------------------- sheet 3: HUD rings
def sheet_hud_rings(icons):
    W, H = 1040, 560
    im = Image.new('RGBA', (W, H), RIVER_NIGHT + (255,))
    d = ImageDraw.Draw(im)
    text(d, (24, 18), 'HUD rings · glyphs at their mockup sizes', 'title', 31, PALE_GOLD)
    text(d, (24, 60), 'Rings drawn as hud.gd ring() draws them: 132 (attack, 64 px glyph), 64 (techniques, 48 px), 52 (fan, items, 32 px). Today scales with nearest as the HUD does.',
         'text', 14, MIST)
    ring132, pad132 = L.hud_ring(66, active=True)
    ring132n, _ = L.hud_ring(66)
    ring64, pad64 = L.hud_ring(32)
    ring52, pad52 = L.hud_ring(26)
    ring52a, _ = L.hud_ring(26, active=True)

    def place(ring, pad, cx, cy, glyph):
        im.alpha_composite(ring, (cx - int(pad), cy - int(pad)))
        im.alpha_composite(glyph, (cx - glyph.width // 2, cy - glyph.height // 2))

    def cooldown(cx, cy, r, frac):
        ov = Image.new('RGBA', (r * 2 + 2, r * 2 + 2), (0, 0, 0, 0))
        dd = ImageDraw.Draw(ov)
        dd.pieslice([1, 1, r * 2, r * 2], -90, -90 + int(360 * frac), fill=(0, 0, 0, 150))
        im.alpha_composite(ov, (cx - r - 1, cy - r - 1))
        text(d, (cx, cy - 9), '3', 'bold', 18, PAPER, anchor='ma', outline=True)

    for si, style in enumerate(('Today', 'A', 'B')):
        y = 170 + si * 128
        text(d, (24, y - 12), {'Today': 'Today', 'A': 'Style A', 'B': 'Style B'}[style], 'display', 24, GOLD)
        if style == 'Today':
            g64 = L.scale_nearest(today_icon('hud', 'jian'), 64)
            g32 = today_icon('hud', 'jian')
            c32 = today_icon('hud', 'cultivate')
            t48a = L.scale_nearest(today_icon('techniques', 'ember_burst'), 48)
            t48b = L.scale_nearest(today_icon('techniques', 'jade_thrust'), 48)
            i32 = L.scale_nearest(today_icon('items', 'healing_pill'), 32)
        elif style == 'A':
            g64 = L.scale_nearest(icons['A_hud_jian'], 64)
            g32 = icons['A_hud_jian']
            c32 = icons['A_hud_cultivate']
            t48a = icons['A48_ember_burst']
            t48b = icons['A48_jade_thrust']
            i32 = L.scale_box(icons['A_healing_pill'], 32)
        else:
            g64 = icons['B64_hud_jian']
            g32 = icons['B_hud_jian']
            c32 = icons['B_hud_cultivate']
            t48a = L.scale_box(icons['B_ember_burst'], 48)
            t48b = L.scale_box(icons['B_jade_thrust'], 48)
            i32 = L.scale_box(icons['B_healing_pill'], 32)
        place(ring132 if style != 'Today' else ring132, pad132, 200, y + 40, g64)
        place(ring52, pad52, 320, y + 40, g32)
        place(ring52a, pad52, 400, y + 40, c32)
        place(ring64, pad64, 500, y + 40, t48a)
        place(ring64, pad64, 590, y + 40, t48b)
        cooldown(590, y + 40, 31, 0.6)
        place(ring52, pad52, 680, y + 40, i32)
        # captions, on two staggered lines so they do not collide
        if si == 2:
            for k, (cx, cap) in enumerate(((200, 'attack · ring 132, glyph 64'), (320, 'jian · 52 / 32'), (400, 'cultivate · 52 / 32, active'),
                                           (500, 'Ember Burst · 64 / 48'), (590, 'Jade Thrust · cooldown'), (680, 'healing pill · 52 / 32'))):
                text(d, (cx, y + 96 + (18 if k % 2 else 0)), cap, 'text', 13, MIST, anchor='ma')
    # 2x inspection of the 32 px glyphs
    x = 760
    text(d, (x, 150), '2x inspection', 'text', 13, HOLLOW)
    for si, style in enumerate(('Today', 'A', 'B')):
        y = 170 + si * 128
        for k, key in enumerate(('jian', 'cultivate')):
            if style == 'Today':
                g = today_icon('hud', key)
            else:
                g = icons[style + '_hud_' + key]
            big = g.resize((64, 64), Image.Resampling.NEAREST if style != 'B' else Image.Resampling.BICUBIC)
            disc = Image.new('RGBA', (76, 76), (0, 0, 0, 0))
            ImageDraw.Draw(disc).ellipse([0, 0, 75, 75], fill=(29, 81, 87, 255))
            im.alpha_composite(disc, (x + k * 90, y + 2))
            im.alpha_composite(big, (x + 6 + k * 90, y + 8))
    return im


# ----------------------------------------------------------------------------- sheet 4: the Bag page
def sheet_bag(icons, style):
    W, H = 1280, 720
    plate = Image.open(os.path.join(PROJECT, 'docs', 'mockups', 'assets', 'plate_herb_terraces.png')).convert('RGBA')
    im = plate.copy()
    dim = Image.new('RGBA', (W, H), (3, 8, 10, int(255 * 0.72)))
    im.alpha_composite(dim)
    d = ImageDraw.Draw(im)
    # the page frame, plaque, close button and tabs (kit/README.md layout)
    im.alpha_composite(major_window(1152, 656), (64, 32))
    im.alpha_composite(plaque(440, 60), (420, 42))
    text(d, (640, 48), 'Bag', 'title', 41, PALE_GOLD, anchor='ma')
    close = kit('close_button__normal').resize((52, 52), Image.Resampling.BOX)
    im.alpha_composite(close, (1146, 46))
    tx = 96
    for name, sel in (('Spirit Gourd', True), ('Key Items', False)):
        f = font('text', 20)
        tw = int(d.textlength(name, font=f)) + 40
        tw = max(118, tw)
        im.alpha_composite(tab(tw, sel), (tx, 116))
        text(d, (tx + tw // 2, 116 + 12), name, 'text', 20, PALE_GOLD if sel else PAPER, anchor='ma')
        tx += tw + 6
    # the grid panel: 5 x 3 slots of 76 px with 8 px gutters
    SLOT, GAP = 76, 8
    gx, gy = 92, 172
    gw = 2 * 16 + 5 * SLOT + 4 * GAP
    gh = 2 * 16 + 3 * SLOT + 2 * GAP
    im.alpha_composite(minor_panel(gw, gh), (gx, gy))
    grid = [('iron_jian', 1), ('wardens_handbell', 1), ('jadeiron_robe', 1), ('healing_pill', 6), ('sage_condensing_pill', 2),
            ('star_lotus', 38), ('driftglass', 83), ('jade_scale', 7), ('inner_art_manual', 1), ('jian_spirit', 1),
            ('jian_sage', 1), ('jian_will', 1), (None, 0), (None, 0), (None, 0)]
    selected = 'sage_condensing_pill'
    grade_of = {'iron_jian': 'common', 'jian_spirit': 'spirit', 'jian_sage': 'sage', 'jian_will': 'will', 'wardens_handbell': 'sage',
                'jadeiron_robe': 'earth', 'sage_condensing_pill': 'mystic', 'star_lotus': 'sage', 'driftglass': 'heaven',
                'jade_scale': 'earth', 'inner_art_manual': 'earth', 'healing_pill': 'common'}
    for k, (ident, count) in enumerate(grid):
        r, c = divmod(k, 5)
        x = gx + 16 + c * (SLOT + GAP)
        y = gy + 16 + r * (SLOT + GAP)
        state = 'selected' if ident == selected else 'normal'
        im.alpha_composite(slot(SLOT, state), (x, y))
        if ident is None:
            im.alpha_composite(with_alpha(icons[style + '_empty'], 0.35), (x + 6, y + 6))
            continue
        im.alpha_composite(icons[style + '_' + ident], (x + 6, y + 6))
        g = grade_of.get(ident, 'common')
        if g not in ('plain', 'common'):
            im.alpha_composite(qrim(SLOT, tuple(int(I.GRADE_COL[g].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))), (x, y))
        if count > 1:
            text(d, (x + SLOT - 6, y + SLOT - 22), str(count), 'bold', 16, PAPER, anchor='ra', outline=True)
        if ident == selected:
            im.alpha_composite(slot_glow(SLOT), (x - 4, y - 4))
    text(d, (gx + 16, gy + gh + 10), '12 / 15', 'text', 16, MIST)
    # the detail panel
    dx, dy = gx + gw + 20, 172
    dw, dh = 1188 - dx, gh
    im.alpha_composite(minor_panel(dw, dh), (dx, dy))
    im.alpha_composite(slot(SLOT, 'normal'), (dx + 20, dy + 20))
    im.alpha_composite(icons[style + '_' + selected], (dx + 26, dy + 26))
    im.alpha_composite(qrim(SLOT, (176, 124, 232)), (dx + 20, dy + 20))
    text(d, (dx + 112, dy + 18), 'Sage-condensing Pill', 'display', 26, PALE_GOLD)
    text(d, (dx + 112, dy + 52), 'Mystic · Pill · Sage realm', 'text', 16, (176, 124, 232))
    text(d, (dx + 112, dy + 80), 'Gathers the qi of the Sage realm into one point for the breakthrough.', 'text', 16, PAPER)
    text(d, (dx + 112, dy + 102), 'Breakthrough chance +12% for one attempt. Halo quality.', 'text', 16, PAPER)
    text(d, (dx + 20, dy + 120), 'Held 2 · Weight 0.1 · Sells for 1,450', 'text', 14, MIST)
    # a second row of facts and a Use button
    im.alpha_composite(button2(176, 52), (dx + dw - 196, dy + dh - 72))
    text(d, (dx + dw - 196 + 88, dy + dh - 72 + 12), 'Use', 'text', 22, PAPER, anchor='ma')
    # the equipped strip below the grid
    ex, ey = gx, gy + gh + 40
    ew, eh = gw, 2 * 16 + SLOT + 26
    im.alpha_composite(minor_panel(ew, eh), (ex, ey))
    text(d, (ex + 16, ey + 10), 'Equipped', 'display', 22, GOLD)
    for k, (ident, cap) in enumerate((('iron_jian', 'Weapon'), ('jadeiron_robe', 'Robe'), ('wardens_handbell', 'Off-hand'), (None, 'Gourd'), (None, 'Talisman'))):
        x = ex + 16 + k * (SLOT + GAP)
        y = ey + 40
        im.alpha_composite(slot(SLOT), (x, y))
        if ident:
            im.alpha_composite(icons[style + '_' + ident], (x + 6, y + 6))
            g = grade_of[ident]
            if g not in ('plain', 'common'):
                im.alpha_composite(qrim(SLOT, tuple(int(I.GRADE_COL[g].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))), (x, y))
        else:
            im.alpha_composite(with_alpha(icons[style + '_empty'], 0.35), (x + 6, y + 6))
        text(d, (x + SLOT // 2, y + SLOT + 4), cap, 'text', 14, MIST, anchor='ma')
    # a note strip in the detail panel's lower half: the same icons at the HUD's 48 and 32
    nx, ny = dx + 20, dy + dh + 40
    im.alpha_composite(minor_panel(dw, eh), (nx - 20, ny))
    text(d, (nx, ny + 10), 'On the HUD', 'display', 22, GOLD)
    ring64, pad64 = L.hud_ring(32)
    ring52, pad52 = L.hud_ring(26)
    cx = nx + 40
    for ident, size in (('ember_burst', 48), ('jade_thrust', 48), ('healing_pill', 32), ('sage_condensing_pill', 32)):
        ring, pad = (ring64, pad64) if size == 48 else (ring52, pad52)
        cy = ny + 40 + 38
        im.alpha_composite(ring, (cx - int(pad), cy - int(pad)))
        if style == 'A' and size == 48 and ('A48_' + ident) in icons:
            g = icons['A48_' + ident]
        else:
            g = L.scale_box(icons[style + '_' + ident], size)
        im.alpha_composite(g, (cx - size // 2, cy - size // 2))
        cx += 90
    para(d, (cx - 10, ny + 52), 'Techniques at 48 in the 64 ring, items at 32 in the 52 ring. '
         + ('A: techniques re-rendered at 48, items box-filtered.' if style == 'A' else 'B: both box-filtered from 64.'),
         nx + dw - 40 - (cx - 10), size=14)
    text(d, (96, 690), 'Icon style study · Style %s · Bag page, 5 x 3 grid of 76 px slots (64 px icons at 1:1)' % style, 'text', 14, HOLLOW)
    return im


def save(img, name):
    path = os.path.join(OUT, name)
    img.convert('RGBA').save(path, format='PNG', optimize=False, compress_level=9)
    print('wrote', os.path.relpath(path, PROJECT), img.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    icons = render_all()
    save(sheet_before_after(icons), '01_before_after.png')
    save(sheet_grade_ladder(icons), '02_grade_ladder.png')
    save(sheet_hud_rings(icons), '03_hud_rings.png')
    save(sheet_bag(icons, 'A'), '04_bag_A.png')
    save(sheet_bag(icons, 'B'), '04_bag_B.png')


if __name__ == '__main__':
    main()
