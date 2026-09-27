"""Pills: one vessel template per grade + pill + effect-mark label.

Grade changes the vessel form and trim (never only colour):
  Common  - squat earthenware jar, bronze lip/band, red cloth stopper
  Earth   - white porcelain pear bottle, jade neck/shoulder/foot trims, jade stopper
  Heaven  - pale-blue meiping vase, silver bands, silver cloud lid
  Mystic  - violet round censer-bottle on a gold foot, gold lid + finial, faint glow
The paper label carries the effect mark (glyphs.MARKS); the pill sits in front.
"""
from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R, M
from registry import hd, register
import glyphs
import shapes as S

FAM, GROUP = 'items', 'pills'
ART = 32   # legacy; 64 once every icon here has an HD drawing (tools/icons/README.md, "How to convert a family")

PORCELAIN = Ramp(['#5C6A6E', '#98AAAC', '#D6E0DC', '#F2F6F0', '#FFFFFF'], '#1C2426')
SKYWARE = Ramp(['#2E4E68', '#5A84A4', '#98C0DA', '#D0E8F4', '#F6FCFF'], '#10202C')
TIDE_WATER = Ramp(['#08323A', '#10545E', '#228C90', '#6CCEC6', '#CCF6EE'], '#031418')  # Act III · Lantern Star Field


def _label(c, cx, cy, mark, ink):
    w, h = glyphs.size(mark)
    x0, y0 = int(round(cx - w / 2.0)), int(round(cy - h / 2.0))
    lab = S.rounded_rect(c, x0 - 1, y0 - 1, x0 + w, y0 + h, 1)
    c.put(lab, R['paper'], 'bevel', base=3, sep=True, sep_col=R['paper'][0])
    c.put(c.from_rows(glyphs.MARKS[mark], x0, y0), ink, 'flat')


def vessel_common(c):
    body = c.ellipse(13, 19.5, 10.5, 9.5)
    neck = c.rect(9, 8, 16, 12)
    c.put(body | neck, R['clay'], 'sphere', base=2, cx=12, cy=17, rx=12, ry=12)
    c.put(c.rect(3, 12, 23, 13) & body, R['bronze'], 'flat', base=3)
    c.put(c.rect(3, 13, 23, 13) & body, R['bronze'], 'flat', base=1)
    lip = c.rect(8, 7, 17, 8)
    c.put(lip, R['bronze'], 'vgrad', base=3, sep=True)
    cap = c.ellipse(12.5, 5, 4.8, 2.8)
    c.put(cap, R['red'], 'ray', base=2, sep=True)
    c.put(c.rect(9, 6, 16, 6) & cap, R['straw'], 'flat', base=3)
    return (13, 20)


def vessel_earth(c):
    body = c.ellipse(13, 20.5, 10, 8.5)
    neck = c.poly([(9, 13.5), (17, 13.5), (15, 7), (11, 7)])
    foot = c.rect(8, 28, 18, 29)
    c.put(foot, R['jade'], 'ray', base=2)
    c.put(body | neck, PORCELAIN, 'sphere', base=2, cx=12, cy=17, rx=12, ry=13, sep=True)
    c.put(c.rect(10, 8, 16, 9), R['jade'], 'flat', base=2)
    sh = (c.ellipse(13, 20.5, 10, 8.5) & ~c.ellipse(13, 22.5, 10, 8.5)) & (c.Y < 17)
    c.put(sh, R['jade'], 'flat', base=3)
    stop = c.rect(10, 3, 15, 6) | c.rect(11, 2, 14, 2)
    c.put(stop, R['jade'], 'ray', base=3, sep=True)
    return (13, 20.5)


def vessel_heaven(c):
    body = c.poly([(9, 10), (17, 10), (21.5, 13), (22, 17), (19.5, 24), (17, 28), (9, 28), (6.5, 24), (4, 17), (4.5, 13)])
    c.put(body, SKYWARE, 'sphere', base=2, cx=12, cy=16, rx=12, ry=14)
    c.put(c.rect(4, 13, 22, 13) & body, R['silver'], 'flat', base=4)
    foot = c.rect(8, 27, 18, 29)
    c.put(foot, R['silver'], 'ray', base=3, sep=True)
    neck = c.rect(10, 7, 16, 10)
    c.put(neck, SKYWARE, 'hgrad', base=2, sep=True)
    lid = c.ellipse(10.5, 6, 3, 2) | c.ellipse(15.5, 6, 3, 2) | c.ellipse(13, 4.5, 3.2, 2.4)
    c.put(lid, R['silver'], 'ray', base=3, sep=True)
    c.put(c.rect(13, 1, 13, 2), R['silver'], 'flat', base=4)
    return (13, 19)


def vessel_mystic(c):
    foot = c.poly([(7, 29), (9, 25), (17, 25), (19, 29)])
    c.put(foot, R['gold'], 'ray', base=2)
    body = c.ellipse(13, 18.5, 10.5, 8.5)
    c.put(body, R['mistjade'], 'sphere', base=2, cx=12, cy=16, rx=12, ry=11, sep=True)
    for y in (11, 25):
        c.put(c.rect(4, y, 22, y) & body, R['gold'], 'flat', base=3)
    lid = c.ellipse(13, 9.5, 7.5, 3) & (c.Y < 11)
    c.put(lid | c.rect(6, 9, 20, 10), R['gold'], 'ray', base=3, sep=True)
    fin = S.diamond(c, 13, 5, 2.2, 3)
    c.put(fin, R['violet'], 'ray', base=3, sep=True)
    for x in (3, 23):
        c.put(c.ring(x, 16, 2.2, 1), R['gold'], 'flat', base=3)
    return (13, 18.5)


VESSELS = {'common': vessel_common, 'earth': vessel_earth, 'heaven': vessel_heaven, 'mystic': vessel_mystic}


def pill(c, x, y, r, ramp, grade):
    m = c.circle(x, y, r)
    c.put(m, ramp, 'sphere', base=2, sep=True)
    if grade == 'earth':
        c.put(c.arc(x, y, r - 1.2, 1, 200, 340) & m, ramp[1], 'flat', out=ramp.out)
    elif grade == 'heaven':
        c.put(c.arc(x, y + 0.5, r - 1.5, 1, 20, 160) & m, '#FFFFFF', 'flat')
    elif grade == 'mystic':
        c.put(c.ring(x, y, r - 1.3, 1) & m & (c.Y > y), R['gold'], 'flat', base=3)
    c.put(c.rect(int(x - r * 0.45), int(y - r * 0.5), int(x - r * 0.45), int(y - r * 0.5)), ramp[4], 'flat')


def make_pill(grade, mark, pill_ramp, ink=None):
    def build():
        c = Canvas(32)
        lx, ly = VESSELS[grade](c)
        _label(c, lx, ly, mark, ink or pill_ramp[1])
        pill(c, 25, 25, 4.6, pill_ramp, grade)
        c.outline()
        if grade == 'mystic':
            c.glow('#B18DE2', (110, 45))
        return c
    return build


PILLS = [
    ('healing_pill', 'common', 'heart', R['red'], None),
    ('qi_restoration_pill', 'common', 'spiral', R['qi'], None),
    ('qi_gathering_pill', 'common', 'spiral_up', R['cyan'], None),
    ('bone_strengthening_pill', 'common', 'bone', R['bone'], R['earth'][1]),
    ('purging_pill', 'common', 'drop_leaf', R['tea'], None),
    ('viper_antidote', 'common', 'leaf', R['leaf'], None),
    ('tiger_blood_pill', 'common', 'flame', R['ember'], None),
    ('cleansing_pill', 'common', 'gate_cloud', R['pearl'], R['navy'][2]),
    ('foundation_guard_pill', 'earth', 'gate', R['gold'], R['gold'][0]),
    ('clear_mind_pill', 'earth', 'lamp', R['sky'], R['navy'][2]),
    ('meridian_reversal_pill', 'earth', 'arrows_loop', R['qi'], None),
    ('method_conversion_pill', 'earth', 'arrows', R['violet'], None),
    ('qi_refining_pill', 'earth', 'spiral', R['jade'], R['qi'][1]),
    ('soul_soothing_pill', 'heaven', 'eye', R['violet'], None),
    ('mind_lake_opening_pill', 'heaven', 'eye_gate', R['storm'], R['navy'][2]),
    ('sage_condensing_pill', 'mystic', 'knot', R['gold'], R['plum'][2]),
    ('storm_blood_pill', 'mystic', 'bolt', R['storm'], R['navy'][2]),
    ('sovereign_settling_pill', 'mystic', 'gate', R['sand'], R['clay'][1]),
    ('will_tempering_pill', 'mystic', 'eye', R['violet'], R['navy'][2]),
    ('law_condensing_pill', 'mystic', 'law', R['storm'], R['plum'][2]),
    ('law_touching_pill', 'mystic', 'eye_gate', R['silver'], R['plum'][2]),
    ('monarch_condensing_pill', 'mystic', 'crown', R['gold'], R['red'][1]),
    ('sigil_anchor_pill', 'mystic', 'anchor', R['red'], R['plum'][2]),
    # S44 / Part 8 new forms.
    ('qi_flow_pill', 'earth', 'spiral_up', R['jade'], R['qi'][1]),
    ('murky_pill', 'common', 'drop_leaf', R['mud'], R['earth'][1]),
    ('viper_smoke_pill', 'common', 'leaf', R['venom'], R['navy'][2]),
    ('sunfire_pill', 'common', 'flame', R['fire'], R['red'][1]),
    ('stillwater_pill', 'earth', 'drop_leaf', R['sky'], R['navy'][2]),
    ('cloudstep_pill', 'heaven', 'arrows', R['cloud'], R['navy'][2]),
    # S48 Core Forging: refined only over a Heavenly Flame.
    ('heavenly_flame_pill', 'earth', 'flame', R['gold'], R['red'][1]),
    # S46: a pet's medicine.
    ('beast_revival_pill', 'earth', 'heart', R['leaf'], R['earth'][1]),
    ('beast_marrow_washing_pill', 'earth', 'bone', R['pearl'], R['earth'][1]),
    # Act III · Lantern Star Field
    ('tide_cleansing_pill', 'mystic', 'knot', TIDE_WATER, TIDE_WATER[1]),
]

for _id, _grade, _mark, _ramp, _ink in PILLS:
    register(FAM, _id, make_pill(_grade, _mark, _ramp, _ink), GROUP)


# ============================================================================= HD (Style A, 64 icon space)
# A pill icon is the grade's vessel, a paper label with the effect mark, and the pill in front (lower right).
def jar_hd(p):
    """Common: a squat earthenware jar with a bronze band and lip, a red cloth stopper tied with straw."""
    c = p.c
    bronze, red = M('bronze'), M('red')
    body = c.ellipse(26, 39, 21, 19) | c.box(18, 16, 34, 26)
    p.part(body, M('clay'), 'sphere', base=0, sep=False, cx=23, cy=34, rx=25, ry=25, tex='clay')
    p.part(c.box(5, 24, 47, 28) & body, bronze, 'vgrad', base=0, sep=True, tex='metal')
    p.part(c.box(15, 14, 37, 18), bronze, 'vgrad', base=1, sep=True, tex='metal')
    cap = c.ellipse(25.5, 10, 9.8, 5.6)
    p.part(cap, red, 'ray', base=0, sep=True, rim=False)
    p.part(c.box(17, 12, 34, 14) & cap, M('straw'), 'flat', base=0, sep=True, rim=False)
    p.line([(20, 7), (27, 6), (32, 8)], red, -1, 1.0)
    return (16, 31, 36, 49)


def censer_hd(p):
    """Mystic: a round mistjade censer-bottle on a gold foot, gold bands, lid, handles and a violet finial."""
    c = p.c
    gold = M('gold')
    p.part(c.poly([(13, 58), (18, 50), (34, 50), (39, 58)]), gold, 'ray', base=0, sep=False, tex='metal')
    body = c.ellipse(26, 36.5, 21, 17.5)
    p.part(body, M('mistjade'), 'sphere', base=0, sep=True, cx=23, cy=31, rx=25, ry=22, tex='glass')
    for y in (21.5, 49.5):
        p.part(c.box(4, y, 48, y + 1.8) & body, gold, 'flat', base=1, sep=True, rim=False)
    p.part((c.ellipse(26, 19, 15, 6.2) & c.box(0, 0, 64, 22)) | c.box(11, 18, 41, 21), gold, 'ray', base=1, sep=True, tex='metal')
    p.part(c.diamond(26, 10, 4.4, 6.4), M('violet'), 'ray', base=1, sep=True, spec=(24.6, 7.6))
    for x in (5.5, 46.5):
        p.part(c.ring(x, 32, 4.6, 2.1), gold, 'ray_soft', base=1, sep=True)
    return (17, 28, 35, 45)


VESSELS_HD = {'common': jar_hd, 'mystic': censer_hd}


def heart_hd(p, lab, cx, cy, ink, lv):
    c = p.c
    x, y, r = cx, cy - 1, 4.2
    heart = c.circle(x - r * 0.55, y - r * 0.2, r * 0.6) | c.circle(x + r * 0.55, y - r * 0.2, r * 0.6) | \
        c.poly([(x - r * 1.1, y), (x + r * 1.1, y), (x, y + r * 1.15)])
    p.decal(heart & lab, ink, lv)
    p.decal(c.circle(cx - 2.4, cy - 1.8, 1.0) & lab, ink, lv + 2)


def knot_hd(p, lab, cx, cy, ink, lv):
    p.decal((p.c.ring(cx - 3, cy, 3.8, 1.7) | p.c.ring(cx + 3, cy, 3.8, 1.7)) & lab, ink, lv)


MARKS_HD = {'heart': heart_hd, 'knot': knot_hd}


def make_pill_hd(grade, mark, pill, ink):
    """grade: a VESSELS_HD key; mark: a MARKS_HD key; pill: its material name; ink: (material name, level)."""
    def draw(p):
        c = p.c
        x0, y0, x1, y1 = VESSELS_HD[grade](p)
        lab = c.rrect(x0, y0, x1, y1, 1.5)
        p.part(lab, M('paper'), 'bevel', base=0, sep=True, hw=1, sw=1, tex='paper', rim=False)
        MARKS_HD[mark](p, lab, (x0 + x1) / 2.0, (y0 + y1) / 2.0, M(ink[0]), ink[1])
        mat = M(pill)
        m = c.circle(50, 50, 9.6)
        p.part(m, mat, 'sphere', base=0, sep=True, spec=(46.5, 46.5), tex='metal' if mat.kind in ('metal', 'gold') else None)
        if grade == 'mystic':
            p.decal(c.ring(50, 50, 6.8, 1.4) & c.box(0, 50, 64, 64) & m, mat, -2)
            p.glow('#B18DE2', 1.0)
    return draw


for _id, _grade, _mark, _pill, _ink in (('healing_pill', 'common', 'heart', 'red', ('red', 0)),
                                        ('sage_condensing_pill', 'mystic', 'knot', 'gold', ('plum', -1))):
    hd(_id, make_pill_hd(_grade, _mark, _pill, _ink))
