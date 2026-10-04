"""Armour, the cape, the soul talisman and the spirit gourds (HD, Style A) at 64 art px, shown 1:1 in the 76 px
slot, with a native @32 render for the small slots and the HUD item ring.

Every icon is one drawing `draw(p)` in a 64 x 64 icon space (tools/icons/README.md, "HD drawing model"), the object
inside the 4-px margin; the same description renders at 64 and at 32. Each piece is shown as it is worn: its cut and
its dye are read from the item's row in data/artifacts.json (the `appearance` the layered avatar draws from
data/parts.json, and the garment dye of tools/art/topdown/figure/palettes.py, palette `dye_*`), so the icon in the slot is the
piece on the figure beside it: a straw douli, a jade circlet, a tied silk band, a gold crown with its jade pin or a
veiled hat; a sleeveless vest, a scoop-necked tunic, an open sect robe with crossed lapels, a cloud tunic with its
pale V or a scholar's buttoned coat; loose, straight, martial (shins wrapped), cuffed or scholar trousers; leather
boots with a pale cuff, folded greaves or low cloth shoes. Cloth carries its folds, plates their rivets and sheen,
lacquer its wet shine.

The grade is the kit (palette.kit, Plain to Sphere) and never the colour alone: the trim of the cuffs, hem and collar
(TRIM), the fittings (buckles, pins, buttons, tips), the plates and greaves in the grade's metal, the gem at the
sash, band or strap, and the grade's own mark (WORK: jadeiron plates and scales at Earth, cloud scrolls at Heaven,
gold lines at Mystic, a lightning stitch at Spirit, desert-glass beads at Sage, driftglass studs with a teal stitch
at Sovereign, star dots with a gold stitch at Will, pearls with rose gold at Sphere), with the aura from Mystic up as
stepped glow bands. The gourds (GOURDS) are the same ladder in a gourd: body, bands, stopper, gem and mark.
"""
import json
import math
import os

from pix import erode4
from palette import GRADE_ORDER, M, TEX, kit
from registry import hd, register
import shapes as S

FAM = 'equipment'
ART = 64   # HD (tools/icons/README.md, "How to convert a family")
PROJECT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
SLOTS = ('hat', 'robe', 'trousers', 'boots', 'cape', 'talisman', 'gourd')


def rows():
    """(id, slot, grade, appearance, dye) for every armour, cape, talisman and gourd icon: the artifacts whose icon
    is their own (a set or named piece that borrows a base's icon is drawn once, as that base)."""
    with open(os.path.join(PROJECT, 'data', 'artifacts.json'), encoding='utf-8') as f:
        entries = json.load(f)['entries']
    out = []
    for e in entries:
        if e.get('slot') in SLOTS and str(e.get('icon', e['id'])) == str(e['id']):
            out.append((str(e['id']), str(e['slot']), str(e.get('grade', 'common')), str(e.get('appearance', 'none')), str(e.get('dye', '')) or None))
    return out


# ----------------------------------------------------------------------------- the grade kit for armour
# The trim of cuffs, hem, collar, cuffs and straps by grade: straw on hemp, a dark facing on cotton, then the jade,
# sky, gold, silver, jade, driftteal, gold and rose-gold embroidery of the kits.
TRIM = {'plain': 'straw', 'common': 'dye_ink', 'earth': 'jade', 'heaven': 'sky', 'mystic': 'gold', 'spirit': 'silver', 'sage': 'jade',
        'sovereign': 'driftteal', 'will': 'gold', 'sphere': 'rosegold'}
# The grade's own mark on cloth, leather and metal (work_hd).
WORK = {'plain': None, 'common': None, 'earth': 'plates', 'heaven': 'clouds', 'mystic': 'lines', 'spirit': 'lightning', 'sage': 'beads',
        'sovereign': 'studs', 'will': 'stars', 'sphere': 'pearls'}


def kit_hd(grade):
    """The armour kit of a grade: metal (plates, greaves, the crown's pin ends), fit (buckles, pins, buttons, tips),
    sash (the sash and waistband), trim (TRIM), gem (None below Earth), work (WORK) and glow ((colour, strength) from
    Mystic up, else None)."""
    k = kit(grade)
    return dict(metal=k['blade'], fit=k['guard'], sash=k['wrap'], trim=M(TRIM[grade]), gem=k['gem'], work=WORK[grade], glow=k['glow'], grade=grade)


def cloth_mat(dye, grade):
    """The dyed cloth of a robe or trousers: hemp and cotton are cloth, Heaven and above silk (a stronger rim light)."""
    return M('dye_' + (dye or 'grey'), 'silk' if GRADE_ORDER.index(grade) >= GRADE_ORDER.index('heaven') else 'cloth')


def tex_of(mat):
    return TEX.get(mat.kind)


def mirror(pts):
    return [(64.0 - x, y) for x, y in pts]


def lmask(p, pts, w=1.0):
    """The mask of a stroke through icon-space points, as `PixelPainter.line` draws it (1-px Bresenham at 1:1)."""
    c = p.c
    if w <= 1.0 and p.s == 1.0:
        return c.bres_path([(int(math.floor(x)), int(math.floor(y))) for x, y in pts])
    return c.polyline(pts, w)


# ----------------------------------------------------------------------------- the shared marks
def curl(c, x, y, r=2.4):
    """A cloud scroll: a curl open at the lower left and a tail running right."""
    return c.arc(x, y, r, 1.2, 300, 200) | c.box(x + 0.6, y + r - 1.2, x + r * 2.6, y + r)


def zigzag(x, y0, y1, amp=1.4, n=6):
    return [(x + (amp if i % 2 else -amp), y0 + (y1 - y0) * i / float(n)) for i in range(n + 1)]


def stud(p, area, x, y, mat, r=1.4, lv=0):
    """A round stud or bead on `area`: the gem's tone with a highlight at its upper left."""
    c = p.c
    p.decal(c.circle(x, y, r) & area, mat, lv)
    p.decal(c.circle(x - r * 0.35, y - r * 0.35, max(0.5, r * 0.4)) & area, mat, 3)


def work_hd(p, k, area, spots=(), lines=()):
    """The grade's mark on `area` (cloth, leather or a plate): `spots` take the curls, beads, studs, stars or pearls;
    `lines` [(p0, p1), ...] the gold lines, the lightning or the stitch. Earth's plates are placed by each template."""
    c = p.c
    w = k['work']
    if w == 'clouds':
        for (x, y) in spots:
            p.decal(curl(c, x, y) & area, k['trim'], 0)
    elif w == 'lines':
        for (a, b) in lines:
            p.decal(lmask(p, [a, b], 1.0) & area, k['fit'], 0)
            p.decal(lmask(p, [(a[0] + 2, a[1]), (b[0] + 2, b[1])], 1.0) & area, k['fit'], -2)
    elif w == 'lightning':
        for (a, b) in lines:
            p.decal(lmask(p, zigzag(a[0], a[1], b[1]), 1.2) & area, k['gem'], 2)
    elif w == 'beads':
        for (x, y) in spots:
            stud(p, area, x, y, k['gem'], 1.5, 1)
        for (a, b) in lines:
            p.decal(lmask(p, [a, b], 1.0) & area, k['trim'], 1)
    elif w == 'studs':
        for (a, b) in lines:
            p.decal(lmask(p, [a, b], 1.0) & area, k['trim'], 1)
        for (x, y) in spots:
            stud(p, area, x, y, k['gem'], 1.6, 0)
    elif w == 'stars':
        for (a, b) in lines:
            p.decal(lmask(p, [a, b], 1.0) & area, k['fit'], 1)
        for i, (x, y) in enumerate(spots):
            p.decal(c.circle(x, y, 1.0) & area, k['gem'], 2)
            if i == 0:
                p.decal(c.pts([(math.floor(x) + dx, math.floor(y) + dy) for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0))]) & area, k['gem'], 3)
    elif w == 'pearls':
        for (a, b) in lines:
            p.decal(lmask(p, [a, b], 1.0) & area, k['fit'], 1)
        for (x, y) in spots:
            stud(p, area, x, y, k['gem'], 1.5, 1)


def plate_hd(p, k, x0, y0, x1, y1, r=2.5, rivets=True):
    """A plate in the grade's metal: bevelled, a dark seam line and a row of rivets (Earth's jadeiron plates)."""
    c = p.c
    m = c.rrect(x0, y0, x1, y1, r)
    p.part(m, k['metal'], 'bevel', base=0, sep=True, hw=2, sw=2, tex='metal')
    p.decal(lmask(p, [(x0 + 2, (y0 + y1) / 2.0), (x1 - 2, (y0 + y1) / 2.0)], 1.0) & m, k['metal'], -2)
    if rivets:
        x = x0 + 3
        while x < x1 - 1.5:
            p.decal(c.circle(x, y0 + 3, 0.7), k['metal'], 2)
            x += 4
    return m


def scales_hd(p, k, area, x0, y0, x1, y1):
    """Rows of overlapping scales in the grade's metal across `area`."""
    c = p.c
    rows_ = c.empty()
    y = y0
    row = 0
    while y < y1:
        x = x0 + (2 if row % 2 else 0)
        while x < x1:
            rows_ |= c.arc(x + 2, y + 1.5, 2.0, 0.9, 180, 360)
            x += 4
        y += 3
        row += 1
    p.decal(rows_ & c.box(x0, y0, x1, y1) & area, k['metal'], 1)


def gem_hd(p, k, x, y, r, alt=None):
    """The grade's gem as a diamond cabochon at (x, y), or, below Earth, `alt` (a knot in the sash) when given."""
    c = p.c
    if k['gem'] is not None:
        p.part(c.diamond(x, y, r, r), k['gem'], 'ray', base=1, sep=True, spec=(x - r * 0.3, y - r * 0.35))
    elif alt is not None:
        p.part(c.circle(x, y, r * 0.7), alt, 'sphere', base=1, sep=True, rim=False)


def finish(p, k):
    if k['glow']:
        p.glow(*k['glow'])


# ============================================================================= robes
def collar_hd(p, cut, body, cloth, k, hem):
    """The neck and the front of a robe by its cut: crossed lapels over a paper under-collar (the sect robe), a round
    neck band with a buttoned placket (the disciple tunic), a deep V faced in the cloth's light tone (the cloud tunic),
    a wide turned collar over a line of buttons and a front slit (the scholar coat), or a crossed vest front."""
    c = p.c
    trim, ttex = k['trim'], tex_of(k['trim'])
    if cut == 'cardigan':
        p.part(c.poly([(26, 9), (38, 9), (32, 19)]), M('paper'), 'flat', base=0, sep=True, rim=False)
        p.part(c.polyline([(39, 10), (33, 18)], 4.2) & body, trim, 'ray_soft', base=-1, sep=True, tex=ttex, rim=False)
        p.part(c.polyline([(25, 10), (39, 29)], 4.6) & body, trim, 'ray_soft', base=0, sep=True, tex=ttex, rim=False)
    elif cut == 'disciple':
        p.part((c.ellipse(32, 9.5, 9.5, 6) & ~c.ellipse(32, 9, 6.2, 3.8)) & body, trim, 'ray_soft', base=0, sep=True, tex=ttex, rim=False)
        p.decal(lmask(p, [(32, 15), (32, 29)], 1.0) & body, cloth, -2)
        for y in (18.5, 23.5):
            p.part(c.circle(32.5, y, 1.2), k['fit'], 'sphere', base=1, sep=False)
    elif cut == 'vneck':
        v = (c.polyline([(23.5, 9), (32, 27)], 3.8) | c.polyline([(40.5, 9), (32, 27)], 3.8)) & body
        p.part(v, cloth, 'flat', base=3, sep=True, rim=False)
        p.decal(lmask(p, [(32, 27), (32, 29)], 1.0) & body, cloth, -2)
    elif cut == 'scholar':
        col = (c.poly([(21, 9), (32, 9), (32, 21), (23, 15)]) | c.poly([(32, 9), (43, 9), (41, 15), (32, 21)])) & body
        p.part(col, cloth, 'ray_soft', base=2, sep=True, rim=False)
        p.decal(lmask(p, [(32, 21), (32, 29)], 1.0) & body, cloth, -2)
        p.decal(lmask(p, [(32, 35), (32, hem - 4)], 1.0) & body, cloth, -2)
        for y in (23.5, 27.5):
            p.part(c.circle(32.5, y, 1.2), k['fit'], 'sphere', base=1, sep=False)
    elif cut == 'sleeveless':
        p.part(c.polyline([(38, 10), (30, 20)], 3.0) & body, trim, 'flat', base=-1, sep=True, rim=False)
        p.part(c.polyline([(26, 10), (38, 29)], 3.4) & body, trim, 'flat', base=0, sep=True, rim=False)


def robe_hd(p, cut, dye, grade):
    """A robe laid flat: the sleeves (none on the vest), the body, the cut's neck and front, the sash with its knot and
    hanging ties, the trim at the cuffs and hem, the skirt's folds, then the grade's plates, mark, gem and glow."""
    c = p.c
    k = kit_hd(grade)
    cloth = cloth_mat(dye, grade)
    trim, ttex = k['trim'], tex_of(k['trim'])
    sleeves = cut != 'sleeveless'
    hem = 57.0 if cut in ('scholar', 'cardigan') else 55.0 if sleeves else 53.0
    if sleeves:
        body = c.poly([(21, 9), (43, 9), (45, 28), (51, hem), (13, hem), (19, 28)])
        sl = c.poly([(21, 11), (9, 17), (4, 43), (17, 45), (21, 29)])
        sr = c.poly([(43, 11), (55, 17), (60, 43), (47, 45), (43, 29)])
        p.part(sl, cloth, 'ray', base=-1, sep=False, tex='cloth', axis=100.0, rim=False)
        p.part(sr, cloth, 'ray', base=-1, sep=False, tex='cloth', axis=80.0, rim=False)
    else:
        body = c.poly([(19, 10), (45, 10), (47, 30), (50, hem), (14, hem), (17, 30)]) & ~c.ellipse(17, 19, 4.6, 9.5) & ~c.ellipse(47, 19, 4.6, 9.5)
        sl = sr = c.empty()
    p.part(body, cloth, 'ray', base=0, sep=True, tex='cloth', axis=90.0, rim=False)
    if sleeves:
        for s in (sl, sr):
            p.part(s & c.box(0, 39, 64, 64), trim, 'ray_soft', base=0, sep=True, tex=ttex, rim=False)
    else:
        arm = (c.ellipse(17, 19, 6.6, 11.4) | c.ellipse(47, 19, 6.6, 11.4)) & body
        p.part(arm, trim, 'flat', base=0, sep=True, rim=False)
    collar_hd(p, cut, body, cloth, k, hem)
    # the sash, its ties, the hem, the skirt folds
    p.part(c.box(18, 29, 46, 34.5) & body, k['sash'], 'vgrad', base=0, sep=True, tex=tex_of(k['sash']), rim=False)
    p.part(c.polyline([(24, 34), (23.5, 46)], 2.0) | c.polyline([(28, 34), (28.5, 44)], 2.0), k['sash'], 'flat', base=1, sep=True, rim=False)
    p.part(body & c.box(0, hem - 3.5, 64, 64), trim, 'ray_soft', base=0, sep=True, tex=ttex, rim=False)
    for x0, x1 in ((34, 34), (42, 44)):
        p.decal(lmask(p, [(x0, 35.5), (x1, hem - 4)], 1.0) & body, cloth, -1)
        p.decal(lmask(p, [(x0 + 1, 35.5), (x1 + 1, hem - 4)], 1.0) & body, cloth, 1)
    skirt = body & c.box(0, 35, 64, hem - 4)
    if k['work'] == 'plates':
        # shoulder plates with a rivet line, scales across the chest
        for (x0, x1) in ((5, 19), (45, 59)):
            plate_hd(p, k, x0, 12, x1, 23)
        scales_hd(p, k, body & ~c.box(18, 29, 46, 35), 21, 18, 43, 28)
    work_hd(p, k, skirt | sl | sr, spots=[(38, 42), (25, 50), (47, 36), (17, 36)],
            lines=[((21.5, 36), (19, hem - 5)), ((42.5, 36), (45, hem - 5))])
    gem_hd(p, k, 32, 31.6, 3.4, alt=k['sash'])
    finish(p, k)


# ============================================================================= trousers
# The left leg laid flat by cut; the right leg is its mirror. The legs meet at the inner seam.
LEGS = {
    'straight': [(16, 13), (31.5, 13), (31.5, 56), (15, 56), (12.5, 33)],
    'loose': [(16, 13), (31.5, 13), (31.5, 49), (30, 55), (11, 55), (5, 42), (9, 25)],
    'martial': [(16, 13), (31.5, 13), (31.5, 56), (19, 56), (11.5, 35)],
    'cuffed': [(16, 13), (31.5, 13), (31.5, 56), (15, 56), (12, 31)],
    'scholar': [(16, 13), (31.5, 13), (31.5, 57), (13, 57), (12, 31)],
}


def trousers_hd(p, cut, dye, grade):
    """Trousers laid flat: the two legs of the cut with their crease, the waistband and its tie, the cut's hems (an
    ankle band, three wrapped cuffs, crossed shin ties, a pleat and a deep hem), then the grade's knee plates, mark,
    gem and glow."""
    c = p.c
    k = kit_hd(grade)
    cloth = cloth_mat(dye, grade)
    trim, ttex = k['trim'], tex_of(k['trim'])
    L, R = c.poly(LEGS[cut]), c.poly(mirror(LEGS[cut]))
    p.part(R, cloth, 'ray', base=0, sep=False, tex='cloth', axis=88.0, rim=False)
    p.part(L, cloth, 'ray', base=0, sep=True, tex='cloth', axis=92.0, rim=False)
    legs = L | R
    for x, dx in ((22, -1.5), (42, 1.5)):
        p.decal(lmask(p, [(x, 19), (x + dx, 50)], 1.0) & legs, cloth, -1)
        p.decal(lmask(p, [(x + 1, 19), (x + 1 + dx, 50)], 1.0) & legs, cloth, 1)
    # the waistband and its hanging tie
    p.part(c.box(14, 8, 50, 14), k['sash'], 'vgrad', base=0, sep=True, tex=tex_of(k['sash']), rim=False)
    p.part(c.polyline([(30, 14), (28.5, 24)], 2.0) | c.polyline([(34, 14), (35.5, 22)], 2.0), k['sash'], 'flat', base=1, sep=True, rim=False)
    # the cut's hems
    if cut == 'loose':
        p.part(c.box(0, 50, 64, 55) & legs, trim, 'ray_soft', base=0, sep=True, tex=ttex, rim=False)
    elif cut == 'cuffed':
        for i, y in enumerate((44.0, 48.4, 52.8)):
            p.part(c.box(0, y, 64, y + 3.2) & legs, trim, 'flat', base=(1 if i % 2 else 0), sep=True, rim=False)
    elif cut == 'martial':
        for x0, x1 in ((19, 31), (33, 45)):
            wrap = (c.polyline([(x0, 40), (x1, 46)], 1.6) | c.polyline([(x1, 40), (x0, 46)], 1.6) | c.polyline([(x0, 46), (x1, 52)], 1.6)
                    | c.polyline([(x1, 46), (x0, 52)], 1.6)) & legs
            p.part(wrap, trim, 'flat', base=0, sep=True, rim=False)
        p.part(c.box(0, 52.5, 64, 56) & legs, trim, 'flat', base=1, sep=True, rim=False)
    elif cut == 'scholar':
        p.part(c.box(0, 52.5, 64, 57) & legs, trim, 'ray_soft', base=0, sep=True, tex=ttex, rim=False)
        for x in (22, 42):
            p.decal(lmask(p, [(x, 19), (x, 51)], 1.0) & legs, cloth, -2)
    else:
        p.part(c.box(0, 53, 64, 56) & legs, trim, 'flat', base=0, sep=True, rim=False)
    if k['work'] == 'plates':
        for (x0, x1) in ((15.5, 29.5), (34.5, 48.5)):
            plate_hd(p, k, x0, 29, x1, 40)
    work_hd(p, k, legs & c.box(0, 16, 64, 43), spots=[(20, 36), (44, 40), (25, 24)], lines=[((18.5, 18), (16, 44)), ((45.5, 18), (48, 44))])
    gem_hd(p, k, 32, 11, 2.8, alt=k['sash'])
    finish(p, k)


# ============================================================================= boots
def boot_hd(p, k, cut, dx, dy, base, front):
    """One boot of a pair, offset by (dx, dy): a leather boot with a straw cuff and a strap, folded greaves (a navy
    shaft under a grey fold with a shin plate in the grade's metal), or a low cloth shoe with an ankle opening. The
    front boot takes the grade's mark, buckle and gem."""
    c = p.c

    def P(pts):
        return c.poly([(x + dx, y + dy) for x, y in pts])
    sole = P([(12, 44), (52, 42), (53, 48), (12, 49)])
    if cut == 'slippers':
        shaft = c.empty()
        foot = P([(12, 35), (20, 27), (32, 25), (44, 30), (50, 38), (51, 45), (13, 46)])
    else:
        shaft = P([(16, 12), (30, 12), (31, 36), (16, 38)])
        foot = P([(16, 34), (31, 30), (46, 36), (51, 44), (16, 46)])
    body = shaft | foot
    plain = k['grade'] == 'plain'
    leather = M('straw') if plain and cut == 'slippers' else M('navy') if cut == 'folded' else M('leather')
    p.part(sole, M('darkwood'), 'flat', base=base, sep=True, rim=False)
    p.part(body, leather, 'ray', base=base, sep=True, tex=('cloth' if leather.kind in ('cloth', 'silk', 'matte') else None), axis=100.0, rim=cut == 'folded')
    if cut == 'boots':
        cuff = shaft & c.box(0, 12 + dy, 64, 18 + dy)
        p.part(cuff, M('straw'), 'ray_soft', base=base + 1, sep=True, rim=False)
        strap = shaft & c.box(0, 26 + dy, 64, 30 + dy)
        p.part(strap, k['trim'], 'flat', base=base, sep=True, rim=False)
        if front:
            p.part(c.rrect(21 + dx, 25 + dy, 27 + dx, 31 + dy, 1.0), k['fit'], 'bevel', base=1, sep=True, hw=1, sw=1)
    elif cut == 'folded':
        fold = shaft & c.box(0, 12 + dy, 64, 20 + dy)
        for x in range(17, 31, 4):
            fold |= c.circle(x + 1.5 + dx, 20 + dy, 1.8) & shaft
        p.part(fold, M('hollow'), 'ray_soft', base=base + 1, sep=True, rim=False)
        if front:
            m = c.rrect(19 + dx, 22 + dy, 28 + dx, 35 + dy, 2.0)
            p.part(m, k['metal'], 'bevel', base=0, sep=True, hw=2, sw=2, tex='metal')
            p.decal(lmask(p, [(23.5 + dx, 24 + dy), (23.5 + dx, 33 + dy)], 1.0) & m, k['metal'], -2)
    else:
        mouth = c.ellipse(31 + dx, 29 + dy, 9.5, 3.6) & foot
        p.part(mouth, M('ink'), 'flat', base=1, sep=True, rim=False)
        edge = (c.ellipse(31 + dx, 29 + dy, 11.5, 5.2) & ~c.ellipse(31 + dx, 29 + dy, 9.5, 3.6)) & foot
        p.part(edge, M('hemp') if plain else k['trim'], 'flat', base=base, sep=True, rim=False)
        if plain:
            for y in (37, 41):
                p.decal(lmask(p, [(14 + dx, y + dy), (50 + dx, y + dy - 2)], 1.0) & foot, leather, -1)
            p.part(c.polyline([(22 + dx, 36 + dy), (34 + dx, 31 + dy), (46 + dx, 37 + dy)], 1.8) & foot, M('hemp'), 'flat', base=base + 1, sep=True, rim=False)
    if front:
        area = body & ~sole
        if cut == 'folded':
            gem_hd(p, k, 23.5 + dx, 28.5 + dy, 2.4)
            work_hd(p, k, area & ~c.rrect(19 + dx, 22 + dy, 28 + dx, 35 + dy, 2.0), spots=[(40 + dx, 41 + dy), (22 + dx, 42 + dy)],
                    lines=[((42 + dx, 36 + dy), (46 + dx, 43 + dy))])
        elif cut == 'boots':
            gem_hd(p, k, 24 + dx, 28 + dy, 2.0)
            work_hd(p, k, area & ~c.box(0, 25 + dy, 64, 31 + dy), spots=[(23.5 + dx, 21 + dy), (40 + dx, 41 + dy), (24 + dx, 41 + dy)],
                    lines=[((19 + dx, 19 + dy), (19 + dx, 36 + dy)), ((40 + dx, 36 + dy), (46 + dx, 43 + dy))])
        else:
            gem_hd(p, k, 31 + dx, 35 + dy, 2.2)
            work_hd(p, k, area, spots=[(20 + dx, 38 + dy), (43 + dx, 40 + dy)], lines=[((16 + dx, 40 + dy), (48 + dx, 41 + dy))])


def boots_hd(p, cut, grade):
    k = kit_hd(grade)
    boot_hd(p, k, cut, -5, -6, -1, False)
    boot_hd(p, k, cut, 3, 2, 0, True)
    finish(p, k)


# ============================================================================= hats
def straw_hat_hd(p, grade):
    """The douli: a straw cone with its radial ribs over a wide brim, the teal band at its base and the chin cord.
    Plain: coarse ribs, a frayed brim edge and a hemp cord. Common (the bamboo hat): a tight weave, a lacquered rim,
    a peak and an ink cord with a bronze bead."""
    c = p.c
    k = kit_hd(grade)
    straw = M('straw')
    plain = grade == 'plain'
    p.part(c.ellipse(32, 42.5, 28.5, 6), straw, 'flat', base=-2, sep=False, rim=False)
    cone = c.poly([(4, 41), (32, 11), (60, 41)]) | c.ellipse(32, 40.5, 29, 4.8)
    if plain:
        for x in range(6, 60, 5):
            cone &= ~c.circle(x, 44.8, 1.4)
    p.part(cone, straw, 'ray', base=0, sep=True, rim=False)
    inner = erode4(cone)
    step = 4.6 if plain else 3.2
    kx = -6.0
    while kx <= 6.0:
        p.decal(lmask(p, [(32, 13), (32 + kx * step, 42)], 1.0) & inner, straw, -1 if int(kx) % 2 else 1)
        kx += 1.0
    if not plain:
        for y in (22, 28, 34):
            p.decal(lmask(p, [(32 - (y - 11) * 0.93, y), (32 + (y - 11) * 0.93, y)], 1.0) & inner, straw, -1)
        rim = c.ellipse(32, 40.5, 29, 4.8) & ~c.ellipse(32, 40.5, 27, 3.4)
        p.part(rim & c.box(0, 40.5, 64, 64), M('ink'), 'flat', base=1, sep=True, rim=False)
        p.part(c.circle(32, 11.5, 2.4), M('darkwood'), 'sphere', base=0, sep=True)
    else:
        p.part(c.circle(32, 12, 2.0), straw, 'sphere', base=1, sep=True, rim=False)
    band = cone & c.box(0, 35, 64, 39.2) & ~c.box(0, 38, 64, 39.2)
    p.part(band, M('deepjade', 'silk'), 'flat', base=0, sep=True, rim=False)
    p.decal(band & c.box(0, 35, 64, 36), M('deepjade'), 1)
    cord = M('hemp') if plain else M('ink')
    for pts in (((17, 45), (24, 53), (31, 57)), ((47, 45), (40, 53), (33, 57))):
        p.part(c.taper(pts[0], pts[1], pts[2], 1.8, 1.4) & ~cone, cord, 'flat', base=1 if plain else 2, sep=True, rim=False)
    p.part(c.circle(32, 57, 2.0), k['fit'] if not plain else cord, 'sphere', base=1, sep=True)


def headband_hd(p, grade):
    """The jade circlet: a teal silk band with a front plate in the grade's metal set with its gem, side fittings and a
    silk tail. Earth: a jadeiron plate with a jade cabochon; Mystic: mistjade, gold, a violet gem and the glow."""
    c = p.c
    k = kit_hd(grade)
    silk = M('deepjade', 'silk')
    tail = c.taper((50, 26), (58, 38), (53, 55), 3.6, 2.0) | c.taper((49, 27), (52, 40), (46, 56), 3.0, 1.6)
    p.part(tail, silk, 'ray_soft', base=-1, sep=False, tex='cloth', axis=95.0, rim=False)
    for (x, y) in ((53, 55), (46, 56)):
        p.part(c.circle(x, y, 2.0), k['fit'], 'sphere', base=1, sep=True)
    band = c.ellipse(32, 30, 24, 12) & ~c.ellipse(32, 29, 19, 7)
    p.part(band, silk, 'ray', base=0, sep=True, tex='cloth', axis=0.0, rim=False)
    p.decal(band & c.box(0, 0, 64, 24), silk, -1)
    for x in (9, 55):
        p.part(c.rrect(x - 2.5, 27, x + 2.5, 33, 1.0), k['fit'], 'bevel', base=0, sep=True, hw=1, sw=1)
    plate = plate_hd(p, k, 24, 33, 40, 43, 2.5, rivets=False)
    work_hd(p, k, plate, spots=[(27.5, 35.5), (36.5, 35.5)], lines=[((26, 41.5), (38, 41.5))])
    gem_hd(p, k, 32, 38, 3.2)
    finish(p, k)


def tied_hd(p, grade):
    """The silk band: a teal ribbon tied at the side, its two tails hanging with the grade's tips, the gem at the
    front. Heaven: silver tips and a Qi stone with cloud scrolls; Sovereign: driftteal, driftglass and the glow."""
    c = p.c
    k = kit_hd(grade)
    silk = M('deepjade', 'silk')
    t1 = c.taper((52, 25), (59.5, 40), (52, 57), 5.0, 3.0)
    t2 = c.taper((50, 26), (48.5, 42), (41, 58), 4.4, 2.6)
    p.part(t1 | t2, silk, 'ray_soft', base=-1, sep=False, tex='cloth', axis=95.0, rim=False)
    for (x, y) in ((52, 56), (42, 57)):
        p.part(c.rrect(x - 2.6, y - 2.8, x + 2.6, y + 2.8, 1.0), k['fit'], 'bevel', base=0, sep=True, hw=1, sw=1, tex='metal')
    band = c.ellipse(32, 26, 25.5, 11.5) & ~c.ellipse(32, 25, 20, 6.2)
    p.part(band, silk, 'ray', base=0, sep=True, tex='cloth', axis=0.0, rim=False)
    p.decal(band & c.box(0, 0, 64, 21), silk, -1)
    p.part(c.circle(52, 23, 4.4), silk, 'sphere', base=1, sep=True, rim=False)
    front = band & c.box(0, 28, 64, 64)
    work_hd(p, k, front, spots=[(19, 32), (45, 32)], lines=[((13, 34.5), (51, 34.5))])
    gem_hd(p, k, 32, 33, 3.2)
    finish(p, k)


def guan_hd(p, grade):
    """The crown: a gold guan with open slots and a flared base over the hair bun, the jade pin through it with the
    grade's fittings at its ends, the gem at the front. Spirit: silver ends, a cyan spark and a lightning stitch;
    Will: a starlight stone and star dots, each with its glow."""
    c = p.c
    k = kit_hd(grade)
    gold, jade = M('gold'), M('jade')
    p.part(c.ellipse(32, 46, 15, 8), M('ink'), 'ray', base=0, sep=False, rim=False)
    crown = c.rrect(20, 18, 44, 44, 3.0) | c.ellipse(32, 19, 12, 6)
    p.part(crown, gold, 'ray', base=0, sep=True, tex='metal')
    p.part(c.box(18, 38, 46, 44), k['fit'], 'bevel', base=1, sep=True, hw=1, sw=2, tex='metal')
    # the open slots show the silk cap inside, in the grade's colour
    for x in (24.5, 32, 39.5):
        p.part(c.box(x - 1.4, 24, x + 1.4, 35) & crown, k['metal'], 'vgrad', base=-1, sep=True, rim=False)
    pin = c.rrect(6, 28.2, 58, 32.2, 1.6)
    p.part(pin, jade, 'ray', base=0, sep=True, tex='jade')
    for x in (7.5, 56.5):
        p.part(c.circle(x, 30.2, 2.6), k['fit'], 'sphere', base=1, sep=True)
    work_hd(p, k, (crown & ~pin) | c.box(18, 38, 46, 44), spots=[(28, 40.5), (36, 40.5), (32, 15)], lines=[((20, 41), (44, 41))])
    gem_hd(p, k, 32, 22, 3.0)
    p.sparkle(24.5, 20.5, 1)
    finish(p, k)


def weimao_hd(p, grade):
    """The veiled hat: a black lacquered crown with a red band on a wide brim edged in the grade's metal, a sheer grey
    veil falling from the brim to the shoulders; Sage's ember gem, desert-glass beads and glow."""
    c = p.c
    k = kit_hd(grade)
    ink, red, veil = M('ink'), M('red'), M('hollow')
    v = c.box(9, 24, 55, 55)
    for x in range(9, 56, 6):
        v &= ~c.circle(x + 3, 56.2, 2.2)
    p.part(v, veil, 'vgrad', base=0, sep=False, tex='cloth', axis=90.0, rim=False)
    for x in range(14, 54, 6):
        p.decal(lmask(p, [(x, 27), (x + (1 if x < 32 else -1), 53)], 1.0) & v, veil, -1)
    brim = c.ellipse(32, 24, 26, 5.6)
    p.part(brim, ink, 'ray_soft', base=0, sep=True)
    p.part(brim & ~c.ellipse(32, 23.6, 24, 4.2), k['metal'], 'flat', base=0, sep=True, tex='metal')
    crown = c.ellipse(32, 16.5, 12.5, 8.5) & c.box(0, 0, 64, 24)
    p.part(crown, ink, 'sphere', base=1, sep=True, cx=29, cy=13, rx=15, ry=11)
    p.part(crown & c.box(0, 18, 64, 22), red, 'flat', base=0, sep=True, rim=False)
    work_hd(p, k, brim | crown, spots=[(14, 26.5), (24, 28.4), (40, 28.4), (50, 26.5)], lines=[((12, 20), (52, 20))])
    gem_hd(p, k, 32, 20, 2.6)
    finish(p, k)


HATS = {'straw': straw_hat_hd, 'headband': headband_hd, 'tied': tied_hd, 'guan': guan_hd, 'weimao': weimao_hd}


# ============================================================================= cape and talisman
def cape_hd(p):
    """The sect mantle as worn (teal silk, an olive lining, gold trim), fastened by a mistjade collar and a gold clasp
    set with a violet stone, with the Mystic glow."""
    c = p.c
    k = kit_hd('mystic')
    cloth, lining = M('deepjade', 'silk'), M('moss')
    body = c.poly([(15, 8), (32, 12), (46, 10), (56, 18), (59, 36), (55, 50), (46, 58), (30, 56), (15, 58), (7, 44), (10, 24)])
    p.part(body, cloth, 'ray', base=0, sep=False, tex='cloth', axis=95.0, rim=False)
    lin = c.poly([(46, 10), (56, 18), (59, 36), (55, 50), (48, 32), (46, 18)]) & body
    p.part(lin, lining, 'ray', base=0, sep=True, tex='cloth', axis=100.0, rim=False)
    for a, b in (((18, 16), (14, 54)), ((26, 16), (28, 55)), ((36, 16), (40, 52))):
        pts = S.curve_pts(a, ((a[0] + b[0]) / 2.0 + 2, (a[1] + b[1]) / 2.0), b, 12)
        p.decal(lmask(p, pts, 1.0) & body & ~lin, cloth, -1)
        p.decal(lmask(p, [(x + 1, y) for x, y in pts], 1.0) & body & ~lin, cloth, 1)
    hem = (body & ~erode4(erode4(body)) & c.box(0, 50, 64, 64)) | (lin & ~erode4(erode4(lin)) & body & ~c.box(44, 8, 64, 12))
    p.decal(hem, k['fit'], 0)
    p.part(c.poly([(9, 5), (27, 7), (25, 14), (11, 13)]), M('mistjade_m'), 'ray', base=0, sep=True, tex='jade')
    p.part(c.circle(18, 10.5, 4.6), k['fit'], 'sphere', base=0, sep=True, tex='metal')
    p.part(c.circle(18, 10.5, 2.2), k['gem'], 'sphere', base=1, sep=True, spec=(17.2, 9.7))
    finish(p, k)


def cloud_talisman_hd(p):
    """The soul talisman: a paper strip with its cinnabar script and seal under a jade clip with a gold ring, the Qi
    seeping from it as a faint glow."""
    c = p.c
    paper = c.rrect(20, 14, 44, 58, 1.6)
    p.part(paper, M('paper'), 'bevel', base=0, sep=False, hw=1, sw=1, tex='paper', rim=False)
    for y in (18, 53):
        p.decal(c.box(22, y, 42, y + 1.6) & paper, M('qi'), -1)
    ink = M('navy')
    script = c.box(31, 22, 33.2, 44) | c.polyline([(25, 26), (31, 31)], 1.4) | c.polyline([(39, 26), (33, 31)], 1.4) | c.box(25, 37, 39, 39)
    p.decal(script & paper, ink, -1)
    seal = c.rrect(27, 45, 37, 52, 1.0)
    p.part(seal, M('seal'), 'flat', base=-1, sep=True, rim=False)
    p.decal((c.box(31, 46.5, 33, 50.5) | c.box(29, 47.8, 35, 49.4)) & seal, M('seal'), 2)
    clip = c.rrect(18, 5.5, 46, 16.5, 3.0)
    p.part(clip, M('jade'), 'ray', base=0, sep=True, tex='jade')
    p.decal(c.box(21, 11, 43, 12) & clip, M('jade'), -2)
    p.part(c.circle(32, 9.5, 2.6), M('gold'), 'sphere', base=0, sep=True)
    p.glow('#8AEBEE', 0.55)


# ============================================================================= gourds
# The spirit gourd ladder: the body, the collar and waist band, the stopper, the gem and its mark by grade.
GOURDS = {
    'starter_gourd': dict(body=M('straw'), band=M('hemp'), stop=M('wood'), gem=None, mark='cord', grade='plain'),
    'bamboo_gourd': dict(body=M('bamboo'), band=M('bamboo'), stop=M('wood'), gem=None, mark='nodes', grade='common'),
    'jadeiron_gourd': dict(body=M('jadeiron'), band=M('iron'), stop=M('jade'), gem=M('jade'), mark='hoops', grade='earth'),
    'cloud_gourd': dict(body=M('porcelain'), band=M('sky'), stop=M('silver'), gem=M('qi', 'gem'), mark='clouds', grade='heaven'),
    'mistjade_gourd': dict(body=M('mistjade'), band=M('gold'), stop=M('gold'), gem=M('violet'), mark='hoops', grade='mystic'),
    'stormsteel_gourd': dict(body=M('storm'), band=M('silver'), stop=M('cyan'), gem=M('cyan'), mark='lightning', grade='spirit'),
    'sunsteel_gourd': dict(body=M('gold'), band=M('red'), stop=M('jade'), gem=M('ember'), mark='beads', grade='sage'),
    'driftglass_gourd': dict(body=M('driftglass'), band=M('cometiron'), stop=M('driftteal'), gem=M('driftteal'), mark='studs', grade='sovereign'),
    'lantern_gourd': dict(body=M('nightsteel'), band=M('gold'), stop=M('starlight'), gem=M('starlight'), mark='stars', grade='will'),
}


def gourd_hd(p, g):
    """A spirit gourd: two bulbs and a waist, the collar and stopper at the mouth, the band or cord tied at the waist,
    the grade's mark on the lower bulb (a tassel, bamboo nodes, hoops with a cabochon, cloud scrolls, a lightning
    stitch, beads, studs or star dots) and its glow."""
    c = p.c
    k = kit_hd(g['grade'])
    body, band, btex = g['body'], g['band'], tex_of(g['body'])
    lower = c.ellipse(32, 42, 17, 15) | c.poly([(25, 26), (39, 26), (42, 33), (22, 33)])
    upper = c.ellipse(32, 20.5, 10.6, 9.6)
    p.part(lower, body, 'sphere', base=0, sep=False, cx=29, cy=39, rx=21, ry=18, tex=btex)
    p.part(upper, body, 'sphere', base=0, sep=True, cx=30, cy=19, rx=12.5, ry=11.5, tex=btex)
    bulb = lower | upper
    p.part(c.box(27, 9.5, 37, 12.6), band, 'vgrad', base=1, sep=True, tex=tex_of(band))
    p.part(c.rrect(29, 4.6, 35, 10.2, 1.2), g['stop'], 'ray', base=0, sep=True, tex=tex_of(g['stop']))
    p.part(c.ellipse(32, 5.4, 3.8, 1.6), g['stop'], 'flat', base=1, sep=True)
    waist = c.box(10, 29, 54, 32.8) & bulb
    p.part(waist, band, 'flat', base=0, sep=True, tex=tex_of(band), rim=False)
    p.part(c.circle(24, 31, 2.6), band, 'sphere', base=1, sep=True, rim=False)
    mark = g['mark']
    if mark == 'cord':
        tas = c.taper((23, 33), (17, 40), (16, 48), 2.4, 1.4)
        p.part(tas & ~lower, band, 'ray_soft', base=0, sep=True, rim=False)
        p.part(c.circle(16, 49.5, 1.8), M('red'), 'sphere', base=0, sep=True)
    elif mark == 'nodes':
        for y in (40, 49):
            p.decal(c.box(14, y, 50, y + 1.2) & lower & erode4(lower), body, -2)
            p.decal(c.box(14, y + 1.2, 50, y + 2.4) & lower & erode4(lower), body, 2)
        leaf = c.leaf(40, 30, 35, 14, 5.5, 0.05)
        p.part(leaf, M('leaf'), 'ray', base=0, sep=True, rim=False)
        p.decal(lmask(p, [(41, 29), (50, 22)], 1.0) & leaf, M('leaf'), 2)
    else:
        for y in (38.5, 48.5):
            p.part(c.box(12, y, 52, y + 2.4) & lower, band, 'flat', base=1 if y < 40 else 0, sep=True, tex=tex_of(band), rim=False)
        area = lower & ~c.box(0, 38.5, 64, 40.9) & ~c.box(0, 48.5, 64, 50.9) & ~c.box(0, 29, 64, 33)
        if mark == 'hoops':
            gem_hd(p, dict(k, gem=g['gem']), 32, 44.5, 3.2)
        elif mark == 'clouds':
            for (x, y) in ((20, 42.5), (37, 52), (36, 34.5)):
                p.decal(curl(c, x, y, 2.4) & area, band, -1)
            tas = c.taper((44, 33), (50, 40), (48, 47), 2.6, 1.4)
            p.part(tas & ~lower, band, 'ray_soft', base=0, sep=True, rim=False)
        else:
            work_hd(p, dict(k, gem=g['gem']), area, spots=[(22, 44), (42, 44), (32, 54.5), (20, 20)], lines=[((32, 41.5), (32, 47.5))])
            if mark != 'lightning':
                gem_hd(p, dict(k, gem=g['gem']), 32, 44.5, 3.0)
            else:
                p.part(c.circle(32, 44.5, 2.4), g['gem'], 'sphere', base=1, sep=True, spec=(31.2, 43.6))
    p.sparkle(24.5, 15.5, 0)
    finish(p, k)


# ============================================================================= registration, from the data
def make_hd(slot, appearance, dye, grade, ident):
    if slot == 'robe':
        return lambda p: robe_hd(p, appearance, dye, grade)
    if slot == 'trousers':
        return lambda p: trousers_hd(p, appearance, dye, grade)
    if slot == 'boots':
        return lambda p: boots_hd(p, appearance, grade)
    if slot == 'hat':
        return lambda p: HATS[appearance](p, grade)
    if slot == 'cape':
        return cape_hd
    if slot == 'talisman':
        return cloud_talisman_hd
    if slot == 'gourd':
        return lambda p: gourd_hd(p, GOURDS[ident])
    raise ValueError('armour.py: no template for slot %s (%s)' % (slot, ident))


ROWS = rows()
for _id, _slot, _grade, _look, _dye in ROWS:
    _draw = make_hd(_slot, _look, _dye, _grade, _id)
    register(FAM, _id, _draw, 'gourds' if _slot == 'gourd' else 'armour')
    hd(_id, _draw)
