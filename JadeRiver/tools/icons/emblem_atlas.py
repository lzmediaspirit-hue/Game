"""P13a · The technique emblem atlas (docs/technique_plan.md §3.9, §7; decision: composed at run time from one atlas).

Today's 66 emblems stay baked PNGs. Every other art (the generated ones, the keystones, the Dao and Lost Arts) is
composed in the game by SpriteCache from the layers written here, with the same parts the composer draws
(families/techniques.py): the element's DISC under the grade's or kind's RIM (a base, finished by the painter), the
form's MARK with the family's weapon inset, the path's STAMP and the lost art's TEAR.

A mark is drawn once for every element: it is painted in key colours (KEY_MARK, KEY_STEEL, each seven levels and an
outline) and the game swaps each key for the element's own level (or the path's), so ~250 marks serve 3,000 arts. The
atlas holds each layer at 64, 48 and 32 art px, one PNG a size (art/icons/emblems/), and data/emblem_atlas.json says
where each layer sits and holds the palettes. The build is deterministic: the same code writes the same bytes.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

from palette import Mat, mat7
from pix import PixelPainter, Ramp
from families import techniques as T

PROJECT = T.PROJECT
OUT_DIR = os.path.join(PROJECT, 'art', 'icons', 'emblems')
INDEX = os.path.join(PROJECT, 'data', 'emblem_atlas.json')
SIZES = (64, 48, 32)
COLS = 24
KEY_MARK = Mat([(251, 10 + 20 * i, 247) for i in range(7)], out=(251, 170, 247), kind='light')
KEY_STEEL = Mat([(9, 10 + 20 * i, 251) for i in range(7)], out=(9, 170, 251), kind='metal')
# A keystone draws its template's mark; its kin group's first weapon stands in the inset (Body and Voice: the palm).
TEMPLATE_MARK = {'constructs': 'form:swarm', 'field': 'form:domain', 'finisher': 'form:pillar', 'procession': 'form:chorus',
                 'avatar': 'hand:avatar', 'mirror': 'hand:double'}
KIN_FAMILY = {'voice': 'any', 'edges': 'jian', 'reach': 'spear', 'distance': 'bow'}


def spec(row):
    """The layers of a row's emblem (SpriteCache.emblem_spec reads the same tables from the index)."""
    element = T.ELEMENT_OF.get(row['element'], row['element'])
    kind = row.get('kind', '')
    rim = {'keystone': 'keystone', 'dao': 'dao'}.get(kind, row.get('grade', 'common'))
    mark = 'form:' + row['form'] if row.get('form') in T.FORMS else TEMPLATE_MARK[row['template']]
    fam = KIN_FAMILY[row['kin']] if kind == 'keystone' else row.get('family', 'any')
    return {'base': 'base:%s:%s%s' % (element, rim, ':torn' if kind == 'lost' else ''),
            'mark': '%s:%s' % (mark, 'any' if mark.startswith('hand:') else fam),
            'stamp': 'stamp:' + row['path'] if row.get('path') and kind not in ('keystone', 'dao') else ''}


def _rgba(p):
    c = p.c
    arr = np.zeros((c.h, c.w, 4), np.uint8)
    arr[..., :3] = c.rgb
    arr[..., 3] = c.alpha
    arr[c.alpha == 0] = 0
    return arr


def render_base(key, n):
    _, element, rim, *torn = key.split(':')
    p = PixelPainter(64, n / 64.0)
    T.disc_hd(p, element, rim if rim in T.RIMS else 'common', rim if rim in T.KINDS else None)
    if torn:
        T.tear_rim(p)
    return np.asarray(p.image())


def render_mark(key, n):
    kind, name, fam = key.split(':')
    p = PixelPainter(64, n / 64.0)
    inner, _, _ = T.disc_hd(p, 'water')
    before = _rgba(p)
    x = T.Ctx(p, inner, KEY_MARK, KEY_STEEL, fam)
    (T.HAND[name] if kind == 'hand' else T.FORMS[name])(x)
    after = _rgba(p)
    changed = np.any(after != before, axis=2)
    out = np.zeros_like(after)
    out[changed] = after[changed]
    out[changed, 3] = 255
    return out


def render_stamp(key, n):
    path = key.split(':')[1]
    p = PixelPainter(64, n / 64.0)
    T.disc_hd(p, 'water')
    T.STAMPS[path](p, mat7(Ramp(T.PATHS[path]['stamp'], '#05080B'), 'matte'))
    full, base = np.asarray(p.image()), render_base('base:water:common', n)
    changed = np.any(full != base, axis=2)
    out = np.zeros_like(full)
    out[changed] = full[changed]
    return out


def render_tear(n):
    p = PixelPainter(64, n / 64.0)
    T.disc_hd(p, 'water')
    before = p.c.alpha.copy()
    T.tear_rim(p)
    out = np.zeros((p.c.h, p.c.w, 4), np.uint8)
    out[(before > 0) & (p.c.alpha == 0)] = (255, 255, 255, 255)
    return out


def _hex(c):
    return '#%02x%02x%02x' % tuple(int(v) for v in c[:3])


def palettes():
    """What each key becomes: an element's mark and steel levels (and the path marks'), each with its outline."""
    out = {'key_mark': [_hex(c) for c in KEY_MARK.c] + [_hex(KEY_MARK.out)], 'key_steel': [_hex(c) for c in KEY_STEEL.c] + [_hex(KEY_STEEL.out)]}
    for el, (disc_c, mark_c, steel_c) in T.DISCS.items():
        mk = mat7(Ramp(mark_c, disc_c[0]), 'light')
        st = mat7(Ramp(steel_c, disc_c[0]), 'metal')
        out[el] = {'mark': [_hex(c) for c in mk.c] + [_hex(mk.out)], 'steel': [_hex(c) for c in st.c] + [_hex(st.out)]}
    for path, v in T.PATHS.items():
        if v['mark']:
            out['path:' + path] = [_hex(c) for c in mat7(Ramp(v['mark'], '#000000'), 'light').c]
    return out


def build():
    """Write the atlas PNGs and data/emblem_atlas.json for every art that is not one of today's baked emblems."""
    sys.path.insert(0, os.path.join(PROJECT, 'tools', 'data'))
    import technique_gen
    rows = [r for r in technique_gen.load_rows() if r.get('icon') != r['id']]
    layers = set()
    for r in rows:
        s = spec(r)
        layers |= {s['base'], s['mark']} | ({s['stamp']} if s['stamp'] else set())
    names = sorted(layers) + ['tear']
    cells = {nm: [i % COLS, i // COLS] for i, nm in enumerate(names)}
    os.makedirs(OUT_DIR, exist_ok=True)
    files = {}
    for n in SIZES:
        sheet = np.zeros((((len(names) + COLS - 1) // COLS) * n, COLS * n, 4), np.uint8)
        for nm in names:
            kind = nm.split(':')[0]
            img = render_tear(n) if nm == 'tear' else {'base': render_base, 'form': render_mark, 'hand': render_mark, 'stamp': render_stamp}[kind](nm, n)
            cx, cy = cells[nm]
            sheet[cy * n:(cy + 1) * n, cx * n:(cx + 1) * n] = img
        path = os.path.join(OUT_DIR, 'emblem_atlas_%d.png' % n)
        Image.fromarray(sheet, 'RGBA').save(path, format='PNG', optimize=False, compress_level=9)
        files[str(n)] = 'res://art/icons/emblems/emblem_atlas_%d.png' % n
    index = {'schema_version': 1, 'sizes': list(SIZES), 'files': files, 'cells': cells, 'palettes': palettes(),
             'templates': TEMPLATE_MARK, 'kin_family': KIN_FAMILY, 'element_of': T.ELEMENT_OF}
    with open(INDEX, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, indent=1, sort_keys=True)
        f.write('\n')
    return len(rows), len(names)
