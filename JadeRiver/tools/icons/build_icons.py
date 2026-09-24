#!/usr/bin/env python3
"""Build every Jade River icon, the icon manifest and (optionally) contact sheets.

    python3 tools/icons/build_icons.py                      # all icons + manifest
    python3 tools/icons/build_icons.py --review-dir /tmp/r  # + contact sheets
    python3 tools/icons/build_icons.py --only jade          # ids containing 'jade'

Output is deterministic: same code -> byte-identical PNGs and manifest.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from registry import FAMILY_SIZE, ORDER, REGISTRY  # noqa: E402
import families  # noqa: E402,F401  (registers every icon)

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..'))
ICON_DIR = os.path.join(PROJECT, 'art', 'icons')
MANIFEST = os.path.join(PROJECT, 'data', 'icon_manifest.json')
SCALE = 2


def render(ident):
    entry = REGISTRY[ident]
    canvas = entry['fn']()
    size = FAMILY_SIZE[entry['family']]
    if (canvas.w, canvas.h) != (size, size):
        raise ValueError('%s: canvas %dx%d, expected %d' % (ident, canvas.w, canvas.h, size))
    body = getattr(canvas, 'body', canvas.a)
    if body[0, :].any() or body[-1, :].any() or body[:, 0].any() or body[:, -1].any():
        print('WARNING %s: artwork touches the canvas edge (outline clipped)' % ident)
    img = canvas.image(SCALE)
    return img


def save_png(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format='PNG', optimize=False, compress_level=9)


def contact_sheets(images, review_dir):
    os.makedirs(review_dir, exist_ok=True)
    font = ImageFont.load_default()
    by_family = {}
    for ident in ORDER:
        if ident in images:
            by_family.setdefault(REGISTRY[ident]['family'], []).append(ident)
    written = []
    slot_bg, slot_border = (13, 48, 53, 255), (44, 158, 143, 255)
    for fam, ids in by_family.items():
        px = FAMILY_SIZE[fam] * SCALE
        cols = 10 if px >= 64 else 14
        per_page = cols * (6 if px >= 64 else 8)
        cell_w = max(px + 16, 84)
        cell_h = px + 16 + 14
        pages = [ids[i:i + per_page] for i in range(0, len(ids), per_page)]
        for pi, page in enumerate(pages):
            rows = (len(page) + cols - 1) // cols
            sheet = Image.new('RGBA', (cols * cell_w + 8, rows * cell_h + 8), (7, 16, 21, 255))
            d = ImageDraw.Draw(sheet)
            for k, ident in enumerate(page):
                cx = 4 + (k % cols) * cell_w
                cy = 4 + (k // cols) * cell_h
                sx = cx + (cell_w - (px + 8)) // 2
                d.rectangle([sx, cy, sx + px + 7, cy + px + 7], fill=slot_bg, outline=slot_border)
                sheet.alpha_composite(images[ident], (sx + 4, cy + 4))
                label = ident if len(ident) <= 15 else ident[:14] + '~'
                tw = d.textlength(label, font=font)
                d.text((cx + (cell_w - tw) / 2, cy + px + 9), label, fill=(207, 198, 174, 255), font=font)
            base = os.path.join(review_dir, 'icons_%s_p%d' % (fam, pi + 1))
            sheet.save(base + '.png')
            big = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
            big.save(base + '_x2.png')
            written += [base + '.png', base + '_x2.png']
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--only', help='substring filter on ids (skips manifest + stale cleanup)')
    ap.add_argument('--review-dir', default=os.environ.get('JR_ICON_REVIEW_DIR'),
                    help='write contact sheets here (optional)')
    args = ap.parse_args()

    ids = sorted(REGISTRY)
    if args.only:
        ids = [i for i in ids if args.only in i or REGISTRY[i]['family'] == args.only
               or REGISTRY[i]['group'] == args.only]
    images = {}
    for ident in ids:
        img = render(ident)
        fam = REGISTRY[ident]['family']
        save_png(img, os.path.join(ICON_DIR, fam, ident + '.png'))
        images[ident] = img

    if not args.only:
        # remove stale icons that are no longer registered
        for fam in FAMILY_SIZE:
            d = os.path.join(ICON_DIR, fam)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if fn.endswith('.png') and fn[:-4] not in REGISTRY:
                    os.remove(os.path.join(d, fn))
                    if os.path.exists(os.path.join(d, fn + '.import')):
                        os.remove(os.path.join(d, fn + '.import'))
        manifest = {i: 'res://art/icons/%s/%s.png' % (REGISTRY[i]['family'], i) for i in sorted(REGISTRY)}
        with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write('\n')

    counts = {}
    for i in ids:
        counts[REGISTRY[i]['family']] = counts.get(REGISTRY[i]['family'], 0) + 1
    print('icons written:', sum(counts.values()), dict(sorted(counts.items())))
    if args.review_dir:
        for p in contact_sheets(images, args.review_dir):
            print('sheet', p)


if __name__ == '__main__':
    main()
