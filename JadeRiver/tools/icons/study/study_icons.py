"""The study's icons. Their descriptions are the HD drawings of the real families (families/*.py, registry.HD);
either painter renders them. Only the empty-slot motif, which is UI art, is described here.

Items, equipment and techniques are described in a 64-px space (object inside a 4-px margin, glows may use
it); HUD glyphs in a 32-px space.
"""
from __future__ import annotations

from pix import Ramp, erode4
from palette import mat7
from registry import HD
import families  # noqa: F401  (registers every icon and its HD drawing)
from families.weapons import jian_hd


def empty_motif(p):
    """The empty-slot motif: a 64-px cloud seal (two curls on a base line) in jade shadow, shown at 35%."""
    c = p.c
    col = mat7(Ramp(['#0F3D3B', '#15514F', '#1E6A66', '#2C9E8F', '#67D6BD'], '#082322'), 'matte')
    m = c.arc(27, 34, 11, 3.2, 0, 300) | c.arc(27, 34, 6, 3.0, 20, 250) | c.arc(43, 38, 6.5, 3.0, 300, 210) | c.box(14, 46, 52, 49.5)
    if getattr(p, 'style', 'A') == 'A':
        p.part(m, col, 'flat', base=0, sep=False, rim=False)
        p.decal(m & ~erode4(m) & (c.Y < 30 * p.s), col, 1)
    else:
        p.shadow = False
        p.contour = 0.2
        p.part(m, col, 'ray', base=0, sep=False, rim=False, bevel=1.6)
    return p


def _draw(ident, **kw):
    return lambda p: HD[ident](p, **kw) or p


ITEMS = [
    # id, family, today's icon id, draw fn, kwargs, label
    ('iron_jian', 'equipment', 'iron_jian', _draw('iron_jian'), {}, 'Iron jian'),
    ('wardens_handbell', 'equipment', 'wardens_handbell', _draw('wardens_handbell'), {}, "Warden's hand-bell"),
    ('jadeiron_robe', 'equipment', 'jadeiron_robe', _draw('jadeiron_robe'), {}, 'Jadeiron robe'),
    ('healing_pill', 'items', 'healing_pill', _draw('healing_pill'), {}, 'Healing pill'),
    ('sage_condensing_pill', 'items', 'sage_condensing_pill', _draw('sage_condensing_pill'), {}, 'Sage-condensing pill'),
    ('star_lotus', 'items', 'star_lotus', _draw('star_lotus'), {}, 'Star lotus'),
    ('driftglass', 'items', 'driftglass', _draw('driftglass'), {}, 'Driftglass'),
    ('jade_scale', 'items', 'jade_scale', _draw('jade_scale'), {}, 'Jade scale'),
    ('inner_art_manual', 'items', 'inner_art_manual', _draw('inner_art_manual'), {}, 'Inner-art manual'),
    ('ember_burst', 'techniques', 'ember_burst', _draw('ember_burst'), {}, 'Ember Burst'),
    ('jade_thrust', 'techniques', 'jade_thrust', _draw('jade_thrust'), {}, 'Jade Thrust'),
]
HUD = [
    ('jian', 'hud', 'jian', _draw('jian'), {}, 'Attack (jian)'),
    ('cultivate', 'hud', 'cultivate', _draw('cultivate'), {}, 'Cultivate (lotus)'),
]
LADDER = ['common', 'spirit', 'sage', 'will']


def jian(p, grade):
    jian_hd(p, grade)
    return p
