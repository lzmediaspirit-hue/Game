"""P7b (docs/item_plan.md §2.9): icons for the banded bases added in P7b part 1, drawn with the existing family
functions and the grade kits in palette.py (they are redrawn with their families in the Style A pass; the Sovereign
and Will armour, hats and gourds have moved to families/armour.py with its conversion):

- the brush and the bell at every grade: the Bastion's Sage brush and bell, their materials swapped for each grade's;
- Sovereign (driftsteel) and Will (lanternsteel) weapons: each family drawn at Sage and its kit swapped for the grade's;
- the pet gear ladders (collars, beast talismans, saddles) from the three S46 pieces, and four furnaces.

`recolor` swaps whole material ramps (every shade and the outline) on a finished canvas, and a glow colour, so a
swapped icon keeps its drawing exactly.
"""
from pix import rgb
from palette import R, GRADES
from registry import register
from families import beast_parts, treasures, weapons

ART = 32   # legacy, as the families these drawings come from

GRADE_WORDS = weapons.GRADE_WORDS + [('driftsteel', 'sovereign'), ('lanternsteel', 'will')]
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


# ------------------------------------------------------------------ weapons: Sovereign and Will in the nine families
for _fam, _build in weapons.BUILDERS.items():
    for _word, _grade in (('driftsteel', 'sovereign'), ('lanternsteel', 'will')):
        register('equipment', '%s_%s' % (_word, _fam), regrade(lambda b=_build: b('sage'), 'sage', _grade), 'weapons')

# ------------------------------------------------------------------ the brush and the bell at every grade
for _word, _grade in GRADE_WORDS:
    _bronze = () if _grade == 'plain' else ((R['bronze'], GRADES[_grade]['metal']),)
    register('equipment', '%s_brush' % _word, regrade(lambda: weapons._v12d_brush(False), 'sage', _grade), 'weapons')
    register('equipment', '%s_bell' % _word, regrade(lambda: weapons._v12d_bell(False), 'sage', _grade, _bronze), 'weapons')

# ------------------------------------------------------------------ pet gear ladders (the S46 pieces, per grade)
PET_GEAR = {  # slot word -> (drawing, its grade, (source ramp, kit key) pairs)
    'collar': (beast_parts.bone_collar, 'common', ((R['leather'], 'grip'), (R['hemp'], 'accent'), (R['bone'], 'metal'))),
    'beast_talisman': (beast_parts.scale_talisman, 'earth', ((R['scale_green'], 'metal'), (R['jade'], 'gem'))),
    'saddle': (beast_parts.reed_saddle, 'common', ((R['straw'], 'cloth'), (R['leather'], 'grip'), (R['hemp'], 'wrap'), (R['bronze'], 'accent'))),
}
_first = {'collar': 'earth', 'beast_talisman': 'common', 'saddle': 'earth'}
_grades = [g for _, g in GRADE_WORDS]
for _slot, (_draw, _own, _swap) in PET_GEAR.items():
    for _word, _grade in GRADE_WORDS[_grades.index(_first[_slot]):]:
        if _grade == _own:
            continue
        _kit = GRADES[_grade]

        def _pet(d=_draw, sw=_swap, kit=_kit):
            c = recolor(d(), [(src, kit[k] or kit['accent']) for src, k in sw], ('#8FE8C0', kit['glow'] or '#8FE8C0'))
            if kit['glow'] and not (c.alpha[(c.alpha > 0) & (c.alpha < 255)]).any():
                c.glow(kit['glow'], (95, 40))
            return c
        register('items', '%s_%s' % (_word, _slot), _pet, 'beast_parts')

# ------------------------------------------------------------------ the furnace ladder on through Acts II and III
for _id, _body, _trim, _jewel in (('stormsteel_furnace', R['storm'], R['silver'], R['cyan']), ('sunsteel_furnace', R['gold'], R['red'], R['ember']),
                                  ('driftsteel_furnace', R['cometiron'], R['driftteal'], R['driftglass']),
                                  ('lanternsteel_furnace', R['nightsteel'], R['gold'], R['starlight'])):
    register('items', _id, treasures._furnace(_body, _trim, _jewel), 'tools')
