#!/usr/bin/env python3
"""Build every Jade River icon, the icon manifest and (optionally) review sheets.

    python3 tools/icons/build_icons.py                                  # all icons + manifest
    python3 tools/icons/build_icons.py --only pills --review-dir /tmp/r # one family + its review sheets
    python3 tools/icons/build_icons.py --only jade                      # ids containing 'jade'
    python3 tools/icons/build_icons.py --preview-hd                     # HD drawings in the game (never commit)

A legacy family (its module's ART is the folder's legacy size) builds its canvases at x2. An HD family (ART = 64,
or 32 for HUD glyphs) builds its HD drawings at 1:1 plus the native renders in registry.VARIANTS as
`<id>@<px>.png`; the manifest lists them as `<id>@<px>` (the 1:1 icon too), so the game knows an icon's art size.
`--review-dir` also renders the HD drawings of families not yet flipped, into the sheets only.

Output is deterministic: same code -> byte-identical PNGs and manifest.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pix import PixelPainter  # noqa: E402
from registry import FAMILY_SIZE, HD, HD_SIZE, ORDER, REGISTRY, VARIANTS, is_hd, module_name  # noqa: E402
import families  # noqa: E402,F401  (registers every icon)
import review  # noqa: E402

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..'))
ICON_DIR = os.path.join(PROJECT, 'art', 'icons')
MANIFEST = os.path.join(PROJECT, 'data', 'icon_manifest.json')
SCALE = 2


def render(ident):
    """The legacy icon: its canvas at x2."""
    entry = REGISTRY[ident]
    canvas = entry['fn']()
    size = FAMILY_SIZE[entry['family']]
    if (canvas.w, canvas.h) != (size, size):
        raise ValueError('%s: canvas %dx%d, expected %d' % (ident, canvas.w, canvas.h, size))
    body = getattr(canvas, 'body', canvas.a)
    if body[0, :].any() or body[-1, :].any() or body[:, 0].any() or body[:, -1].any():
        print('WARNING %s: artwork touches the canvas edge (outline clipped)' % ident)
    return canvas.image(SCALE)


def render_hd(ident):
    """The HD icon's renders {art px: image}: its size at 1:1 and the family's native variants."""
    if ident not in HD:
        raise ValueError('%s: family %s is HD (ART = %d) but this icon has no HD drawing' % (ident, module_name(ident), HD_SIZE[REGISTRY[ident]['family']]))
    fam = REGISTRY[ident]['family']
    size = HD_SIZE[fam]
    out = {}
    for n in (size,) + VARIANTS[fam]:
        p = PixelPainter(size, n / float(size))
        HD[ident](p)
        a = p.c.a
        if a[0, :].any() or a[-1, :].any() or a[:, 0].any() or a[:, -1].any():
            print('WARNING %s@%d: artwork touches the canvas edge (outline clipped)' % (ident, n))
        out[n] = p.image()
    return out


def save_png(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format='PNG', optimize=False, compress_level=9)


def selected(ident, only):
    """--only: a family module, folder or group by name, else a substring of the ids."""
    if not only:
        return True
    names = {n for i, e in REGISTRY.items() for n in (e['family'], e['group'], module_name(i))}
    e = REGISTRY[ident]
    return only in (e['family'], e['group'], module_name(ident)) if only in names else only in ident


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--only', help='a family module, folder, group or id substring (skips manifest + stale cleanup)')
    ap.add_argument('--review-dir', default=os.environ.get('JR_ICON_REVIEW_DIR'),
                    help='write review sheets here (optional)')
    ap.add_argument('--preview-hd', action='store_true',
                    help='build every icon that has an HD drawing as HD, whatever its family ART says, to look at an '
                         'unfinished family in the game; never commit this output (rebuild without it)')
    args = ap.parse_args()
    if args.preview_hd:
        print('PREVIEW BUILD: HD drawings of unfinished families are built; do not commit art/icons or the manifest')
    for ident in HD:
        if ident not in REGISTRY:
            raise ValueError('HD drawing for unregistered icon %s' % ident)

    ids = [i for i in sorted(REGISTRY) if selected(i, args.only)]
    manifest = {}
    shown = {}      # id -> ({art px: image}, hd) for the review sheets
    for ident in ids:
        fam = REGISTRY[ident]['family']
        base = os.path.join(ICON_DIR, fam, ident)
        res = 'res://art/icons/%s/%s' % (fam, ident)
        if is_hd(ident) or (args.preview_hd and ident in HD):
            renders = render_hd(ident)
            size = HD_SIZE[fam]
            for n, img in renders.items():
                save_png(img, base + ('.png' if n == size else '@%d.png' % n))
                manifest['%s@%d' % (ident, n)] = res + ('.png' if n == size else '@%d.png' % n)
            shown[ident] = (renders, True)
        else:
            img = render(ident)
            save_png(img, base + '.png')
            shown[ident] = ({FAMILY_SIZE[fam]: img}, False)
            if args.review_dir and ident in HD:
                shown[ident] = (render_hd(ident), True)
        manifest[ident] = res + '.png'

    if not args.only:
        # remove stale icons and renders that are no longer built
        built = {os.path.basename(p) for p in manifest.values()}
        for fam in FAMILY_SIZE:
            d = os.path.join(ICON_DIR, fam)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if fn.endswith('.png') and fn not in built:
                    os.remove(os.path.join(d, fn))
                    if os.path.exists(os.path.join(d, fn + '.import')):
                        os.remove(os.path.join(d, fn + '.import'))
        with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write('\n')
        # P13a: every other technique's emblem is composed in the game from the atlas's layers (technique_plan §3.9).
        import emblem_atlas
        arts, layers = emblem_atlas.build()
        print('emblem atlas: %d arts composed from %d layers at %s px' % (arts, layers, '/'.join(str(n) for n in emblem_atlas.SIZES)))

    counts = {}
    for i in ids:
        key = REGISTRY[i]['family'] + (' HD' if i + '@%d' % HD_SIZE.get(REGISTRY[i]['family'], 0) in manifest else '')
        counts[key] = counts.get(key, 0) + 1
    print('icons written:', len(ids), dict(sorted(counts.items())))
    if args.review_dir:
        grades = review_grades()
        by_module = {}
        for ident in ORDER:
            if ident in shown:
                by_module.setdefault(module_name(ident), []).append((ident,) + shown[ident])
        for name, icons in by_module.items():
            for p in review.family_sheets(name, icons, args.review_dir, grades, REGISTRY[icons[0][0]]['family']):
                print('sheet', p)


def review_grades():
    """id -> grade from the game data, for the grade rims on the review sheets."""
    out = {}
    for table in ('items', 'techniques'):
        path = os.path.join(PROJECT, 'data', table + '.json')
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                for e in json.load(f).get('entries', []):
                    out[str(e.get('icon', e.get('id')))] = e.get('grade', 'common')
                    out.setdefault(str(e.get('id')), e.get('grade', 'common'))
    return out


if __name__ == '__main__':
    main()
