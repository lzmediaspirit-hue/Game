"""P7b (docs/item_plan.md §2.9): icons for the banded bases added in P7b part 1, drawn with the existing family
functions and the grade kits in palette.py (they are redrawn with their families in the Style A pass):

- Sovereign (driftsteel, starsilk) and Will (lanternsteel, lanternsilk) armour, hats and gourds: each family drawn
  at Sage (or the hat at Spirit) and its kit swapped for the grade's;
- four furnaces. (The weapon ladders, the brush and the bell at every grade and the Sovereign and Will weapons, are
  HD drawings with their family now: `weapons.BUILDERS` x `weapons.GRADE_WORDS`; the pet gear ladders, collars,
  beast talismans and saddles, are with theirs: `beast_parts.PET_GEAR_HD`.)

`recolor` swaps whole material ramps (every shade and the outline) on a finished canvas, and a glow colour, so a
swapped icon keeps its drawing exactly.
"""
from pix import rgb
from palette import R, GRADES
from registry import register
from families import armour, treasures

ART = 32   # legacy, as the families these drawings come from

KIT_KEYS = ('metal', 'metal2', 'grip', 'wrap', 'accent', 'gem', 'cloth')


def recolor(c, pairs, glow=None):
    """Swap ramps on a finished canvas: each (source, target) pair maps every shade and the outline colour; the first
    pair naming a source wins. `glow` = (source colour, target colour or None to drop the glow)."""
    table = {}
    for src, dst in pairs:
        if src is None or dst is None:
            continue
        for a, b in list(zip(src.c, dst.c)) + [(src.out, dst.out)]:
            table.setdefault(tuple(a), tuple(b))
    swapped = c.rgb.copy()
    for a, b in table.items():
        hit = (c.rgb == a).all(axis=2) & (c.alpha == 255)
        swapped[hit] = b
    if glow is not None:
        halo = (c.rgb == rgb(glow[0])).all(axis=2) & (c.alpha < 255) & (c.alpha > 0)
        if glow[1] is None:
            c.alpha[halo] = 0
        else:
            swapped[halo] = rgb(glow[1])
    c.rgb = swapped
    return c


def kit_pairs(src_grade, dst_grade, keys=KIT_KEYS):
    src, dst = GRADES[src_grade], GRADES[dst_grade]
    return [(src[k], dst[k] or dst['accent']) for k in keys]


def regrade(draw, src_grade, dst_grade, extra=()):
    """An icon drawn at `src_grade`, its kit swapped for `dst_grade`'s."""
    def fn():
        c = draw()
        return recolor(c, list(extra) + kit_pairs(src_grade, dst_grade), (GRADES[src_grade]['glow'], GRADES[dst_grade]['glow']))
    return fn


# ------------------------------------------------------------------ Sovereign and Will armour, hats and gourds
for _word, _grade in (('starsilk', 'sovereign'), ('lanternsilk', 'will')):
    register('equipment', '%s_robe' % _word, (lambda g=_grade: armour.robe(g)), 'armour')
    register('equipment', '%s_trousers' % _word, (lambda g=_grade: armour.trousers(g)), 'armour')
    register('equipment', '%s_boots' % _word, (lambda g=_grade: armour.boots(g)), 'armour')


def _cloth_pairs(src, dst):
    a, b = armour.CLOTH[src], armour.CLOTH[dst]
    return [(a[k], b[k]) for k in ('cloth', 'trim', 'sash', 'gem')]


register('equipment', 'starsilk_hat', lambda: recolor(armour.sunsilk_hat(), _cloth_pairs('sage', 'sovereign'), ('#FFC870', GRADES['sovereign']['glow'])), 'armour')
register('equipment', 'lanternsilk_hat', lambda: recolor(armour.stormsilk_hat(), _cloth_pairs('spirit', 'will'), ('#7FD4FF', GRADES['will']['glow'])), 'armour')
register('equipment', 'driftglass_gourd', regrade(lambda: armour.gourd('sunsteel'), 'sage', 'sovereign'), 'gourds')
register('equipment', 'lantern_gourd', regrade(lambda: armour.gourd('sunsteel'), 'sage', 'will'), 'gourds')

# ------------------------------------------------------------------ the furnace ladder on through Acts II and III
for _id, _body, _trim, _jewel in (('stormsteel_furnace', R['storm'], R['silver'], R['cyan']), ('sunsteel_furnace', R['gold'], R['red'], R['ember']),
                                  ('driftsteel_furnace', R['cometiron'], R['driftteal'], R['driftglass']),
                                  ('lanternsteel_furnace', R['nightsteel'], R['gold'], R['starlight'])):
    register('items', _id, treasures._furnace(_body, _trim, _jewel), 'tools')
