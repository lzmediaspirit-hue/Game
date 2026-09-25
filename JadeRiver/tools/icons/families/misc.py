"""Scrolls, pages, tokens, keys and miscellaneous goods.

Templates: paper page, closed scroll, open hand-scroll, hanging token (tablet or
disc with cord + tassel), sack, small jar.
"""
import math

from pix import Canvas, Ramp, dilate4, erode4, move
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'misc'


# ============================================================================ templates
def page(c, paper=None, x0=6, y0=3, x1=25, y1=28, fold=True, torn=False, cols=4, ink='#2B2A30'):
    paper = paper or R['paper']
    m = c.rect(x0, y0, x1, y1)
    if torn:
        for k, x in enumerate(range(x0, x1 + 1)):
            if k % 3 == 1:
                m &= ~c.rect(x, y1, x, y1)
            if k % 4 == 2:
                m &= ~c.rect(x, y1 - 1, x, y1)
    if fold:
        m &= ~c.poly([(x1 - 4.5, y0 - 1), (x1 + 1.5, y0 - 1), (x1 + 1.5, y0 + 5.5)])
    c.put(m, paper, 'bevel', base=3, hw=1, sw=1)
    if fold:
        f = c.poly([(x1 - 4.5, y0), (x1 - 4.5, y0 + 5), (x1 + 0.5, y0 + 5)])
        c.put(f, paper, 'flat', base=2, sep=True, sep_col=paper[1])
    # vertical text columns
    xs = [x1 - 3 - k * 3 for k in range(cols)]
    for k, x in enumerate(xs):
        top = y0 + 3 + (3 if k == 0 and fold else 0)
        L = (y1 - 3) - top - (k * 3) % 5
        for y in range(top, top + L):
            if (y + k) % 4 != 3:
                c.put(c.rect(x, y, x, y), ink, 'flat', only_on=True)
    return m


def closed_scroll(c, paper=None, cap=None, tie=None, a=(6, 25), b=(25, 6), w=8.0):
    paper = paper or R['paper']
    cap = cap or R['wood']
    tie = tie or R['red']
    body = c.seg(a[0], a[1], b[0], b[1], w)
    c.put(body, paper, 'ray', base=3)
    # paper edge spiral at the near end
    e = c.circle(b[0], b[1], w / 2.0 - 0.3)
    c.put(e, paper, 'flat', base=2, sep=True, sep_col=paper[1])
    c.put(c.circle(b[0] - 0.6, b[1] + 0.6, 1.3) & e, cap, 'flat', base=2)
    # roller knobs
    for (x, y) in (a,):
        k = c.circle(x - 1.5, y + 1.5, w / 2.0 - 1.2)
        c.put(k, cap, 'sphere', sep=True)
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    band = c.seg(mx - w / 2.0 + 0.8, my - w / 2.0 + 0.8, mx + w / 2.0 - 0.8, my + w / 2.0 - 0.8, 2.4) & body
    c.put(band, tie, 'flat', base=2)
    return body, (mx, my)


def hand_scroll(c, paper=None, roller=None, knob=None, y0=8, y1=24):
    paper = paper or R['paper']
    roller = roller or R['wood']
    knob = knob or R['jade']
    sheet = c.rect(6, y0 + 1, 25, y1 - 1)
    c.put(sheet, paper, 'bevel', base=3)
    for x in (4, 27):
        rod = c.rect(x - 2, y0 - 1, x + 1, y1 + 1)
        c.put(rod, roller, 'hgrad' if x < 16 else 'hgrad', base=2, sep=True)
        for y in (y0 - 3, y1 + 2):
            k = c.rect(x - 1, y, x, y + 1)
            c.put(k, knob, 'flat', base=3, sep=True)
    return sheet


def token(c, body, shape='tablet', cord=None, tassel=None, cx=16, top=7, bottom=26, w=8):
    cord = cord or R['red']
    tassel = tassel or cord
    loop = c.ring(cx, top - 2.5, 2.6, 1.1) & (c.Y < top)
    c.put(loop, cord, 'flat', base=2)
    bead = c.circle(cx, top - 5, 1.4)
    if shape == 'tablet':
        m = c.poly([(cx - w, top + 3), (cx - w + 3, top), (cx + w - 3, top), (cx + w, top + 3),
                    (cx + w, bottom - 2), (cx + w - 2, bottom), (cx - w + 2, bottom), (cx - w, bottom - 2)])
    else:
        r = (bottom - top) / 2.0
        m = c.circle(cx, top + r, r)
    # tassel hanging below
    tas = c.poly([(cx - 1.5, bottom), (cx + 1.5, bottom), (cx + 3, 31), (cx - 3, 31)])
    tas |= c.rect(int(cx) - 1, bottom - 1, int(cx), bottom + 1)
    c.put(tas, tassel, 'ray', base=2)
    c.put(c.rect(int(cx) - 2, bottom + 1, int(cx) + 1, bottom + 2), R['gold'], 'flat', base=2)
    c.put(m, body, 'ray', base=2, sep=True)
    inner = erode4(erode4(m))
    c.put(S.outline_only(inner), body[1], 'flat', out=body.out)
    c.put(bead, R['gold'], 'sphere', sep=True)
    return m, inner


def jar(c, body, lid=None, x=16, y0=10, y1=29, w=9):
    lid = lid or body
    m = c.ellipse(x, (y0 + y1) / 2.0 + 2, w, (y1 - y0) / 2.0 - 1) | c.rect(int(x - w * 0.55), y0, int(x + w * 0.55), y0 + 4)
    c.put(m, body, 'ray')
    rim = c.rect(int(x - w * 0.7), y0 - 1, int(x + w * 0.7), y0 + 1)
    c.put(rim, lid, 'ray', base=3, sep=True)
    return m


# ============================================================================ pages & scrolls
def manual_page():
    c = Canvas(32)
    page(c, cols=3)
    # small stance diagram in the lower left
    fig = c.circle(9.5, 17.5, 1.3) | c.bres(9, 19, 9, 23) | c.bres(7, 20, 12, 19) | c.bres(9, 23, 7, 26) | c.bres(9, 23, 12, 25)
    c.put(fig, R['jade'][1], 'flat', only_on=True)
    c.put(c.rect(8, 5, 11, 8), R['seal'], 'flat', base=2, only_on=True)
    c.put(c.rect(9, 6, 10, 7), R['seal'], 'flat', base=4, only_on=True)
    c.outline()
    return c


def lu_journal_page():
    c = Canvas(32)
    aged = Ramp(['#5A4A30', '#8E774E', '#C4AA78', '#DCC79A', '#F2E6C4'], '#261E12')
    # slightly rotated page drawn as polygon
    m = c.poly([(5, 6), (23, 3), (27, 26), (9, 29)])
    c.put(m, aged, 'bevel', base=3)
    for k in range(5):
        y = 9 + k * 3.6
        c.put(c.seg(8.5 + k * 0.3, y + 0.6, 22.5 + k * 0.4, y - 1.8, 1.0) & erode4(m), '#4A3A26', 'flat', only_on=True)
    # river sketch + stain
    c.put(S.bez_line(c, (10, 26), (15, 21), (24, 23)) & erode4(m), R['qi'][1], 'flat', only_on=True)
    c.put(c.ring(20, 12, 3, 1) & erode4(m), aged[1], 'flat', only_on=True)
    c.put(c.poly([(23, 3), (24, 8), (19, 8)]) & m, aged, 'flat', base=2)
    c.outline()
    return c


def riverbreath_scroll():
    c = Canvas(32)
    sheet = hand_scroll(c, knob=R['qi'])
    for k, y in enumerate((13, 17)):
        c.put(S.wave_line(c, 8, 23, y, 1, 7, phase=k * 2), R['qi'][1], 'flat', only_on=True)
    c.put(S.wave_line(c, 8, 23, 21, 1, 7, phase=4), R['qi'][2], 'flat', only_on=True)
    for x in (9, 12):
        c.put(c.rect(x, 10, x, 11), '#2B2A30', 'flat', only_on=True)
    c.put(c.rect(20, 9, 22, 11), R['seal'], 'flat', base=2, only_on=True)
    del sheet
    c.outline()
    return c


def recipe_scroll():
    c = Canvas(32)
    body, (mx, my) = closed_scroll(c, cap=R['darkwood'], tie=R['red'])
    # hanging tag with a pill mark
    tag = S.rounded_rect(c, 17, 18, 25, 28, 1)
    string = c.bres(int(mx) + 1, int(my) + 1, 20, 18)
    c.put(string, R['red'], 'flat', base=3)
    c.put(tag, R['talisman'], 'bevel', base=3, sep=True)
    c.put(c.circle(21, 23, 2.6), R['red'], 'sphere', base=2)
    c.px(20, 22, R['red'][4])
    c.outline()
    return c


# ============================================================================ tokens & keys
def river_token():
    c = Canvas(32)
    m, inner = token(c, R['jade'], 'tablet', cord=R['qi'], tassel=R['qi'])
    c.put(inner, R['deepjade'], 'flat', base=3)
    for k, y in enumerate((12, 16, 20)):
        w = S.wave_line(c, 10, 22, y, 1, 6, phase=k * 2) & inner
        c.put(w, R['jade'][4], 'flat', out=R['jade'].out)
        c.put(move(w, 0, 1) & inner & ~w, R['deepjade'][0], 'flat', out=R['jade'].out)
    c.outline()
    return c


def _sect_mark(c, cx, cy, ramp, clip):
    """Simple carved sect glyph: a mountain-over-river sigil."""
    mark = (c.bres(int(cx) - 4, int(cy) + 1, int(cx), int(cy) - 3) | c.bres(int(cx), int(cy) - 3, int(cx) + 4, int(cy) + 1)
            | c.bres(int(cx) - 2, int(cy) + 1, int(cx), int(cy) - 1) | c.bres(int(cx), int(cy) - 1, int(cx) + 2, int(cy) + 1)
            | c.rect(int(cx) - 4, int(cy) + 3, int(cx) + 4, int(cy) + 3))
    c.put(mark & clip, ramp, 'flat')


def jade_token():
    c = Canvas(32)
    m, inner = token(c, R['jade'], 'disc', cord=R['red'], top=7, bottom=26)
    hole = c.circle(16, 16.5, 2.2)
    c.put(c.ring(16, 16.5, 6.4, 1.2), R['jade'][4], 'flat', only_on=True)
    c.put(dilate4(hole) & ~hole, R['jade'][1], 'flat', only_on=True)
    c.erase(hole)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        c.put(c.circle(16 + math.cos(a) * 4.2, 16.5 + math.sin(a) * 4.2, 0.9), R['gold'], 'flat', base=3,
              only_on=True)
    c.outline()
    return c


def alliance_token():
    """The Nine Peaks Alliance token: a navy-jade disc with three gold summits."""
    c = Canvas(32)
    m, inner = token(c, R['navy'], 'disc', cord=R['gold'], top=7, bottom=26)
    peaks = c.poly([(10, 21), (13, 15), (15, 18), (16, 12), (18, 18), (19, 15), (22, 21)])
    c.put(peaks & inner, R['gold'], 'flat', base=4)
    c.put(c.ring(16, 16.5, 7.2, 0.9) & inner, R['gold'], 'flat', base=2, only_on=True)
    c.outline()
    c.glow('#E5B84C', (40,))
    return c


def ironroot_token():
    """An iron-hard sliver of root carved with the clan's mark."""
    c = Canvas(32)
    root = S.taper_curve(c, (8, 27), (14, 16), (24, 5), 6.0, 2.4)
    c.put(root, R['iron'], 'ray', base=2, sep=True)
    for (x, y) in ((12, 20), (16, 14), (20, 10)):
        c.put(c.rect(x, y, x + 1, y), R['gold'], 'flat', base=4)
    c.put(S.taper_curve(c, (12, 21), (9, 17), (6, 16), 2.0, 0.8), R['iron'], 'ray', base=1)
    c.outline()
    return c


def cloud_token():
    c = Canvas(32)
    m, inner = token(c, R['porcelain'], 'disc', cord=R['sky'], tassel=R['sky'], top=7, bottom=26)
    cl = c.ellipse(12.5, 18, 3.2, 2.6) | c.ellipse(17, 15.5, 4, 3.6) | c.ellipse(20.5, 18.5, 3, 2.4) | c.rect(11, 18, 22, 20)
    c.put(cl & inner, R['sky'], 'ray', base=2)
    c.put(c.arc(17, 15.5, 2.2, 1, 90, 300) & inner, R['sky'][4], 'flat', out=R['sky'].out)
    c.put(c.rect(12, 20, 21, 20) & inner, R['sky'][1], 'flat', out=R['sky'].out)
    c.outline()
    return c

def entry_token():
    c = Canvas(32)
    m, inner = token(c, R['bronze'], 'tablet', cord=R['red'], w=7)
    c.put(c.rect(13, 11, 18, 11) | c.rect(15, 11, 16, 21) | c.rect(12, 16, 19, 16) | c.rect(13, 21, 18, 21),
          R['bronze'][1], 'flat', only_on=True)
    c.put(c.rect(13, 12, 18, 12) & inner, R['bronze'][4], 'flat', only_on=True)
    c.outline()
    return c


def mudwater_key():
    c = Canvas(32)
    ramp = R['bronze']
    bow = c.ring(9.5, 9.5, 6, 2.4)
    c.put(bow, ramp, 'ray')
    shaft = c.seg(13, 13, 25, 25, 3.2)
    c.put(shaft, ramp, 'across', base=2, sep=True)
    bit = c.poly([(20, 25), (23, 22), (27, 26), (24, 29)]) | c.poly([(17, 22), (19, 20), (22, 23), (20, 25)])
    c.put(bit & ~shaft, ramp, 'ray', base=2, sep=True)
    c.erase(c.rect(22, 26, 22, 26) | c.rect(19, 23, 19, 23))
    mud = (c.ellipse(6, 13, 2.4, 1.6) | c.ellipse(18, 18, 2, 1.4) | c.ellipse(24, 23, 1.8, 1.2)) & c.a
    c.put(mud, R['mud'], 'flat', base=2)
    c.put(c.rect(5, 12, 5, 12) & c.a, R['mud'][4], 'flat')
    c.outline()
    return c


def siege_medal():
    c = Canvas(32)
    rib = c.poly([(9, 2), (15, 2), (17, 13), (13, 15)]) | c.poly([(17, 2), (23, 2), (19, 15), (15, 13)])
    c.put(rib, R['red'], 'ray', base=2)
    c.put(c.rect(15, 2, 16, 12) & rib, R['gold'], 'flat', base=3)
    med = c.circle(16, 21, 8.5)
    c.put(med, R['gold'], 'sphere', base=2, sep=True)
    c.put(S.outline_only(c.circle(16, 21, 6.5)), R['gold'][1], 'flat', out=R['gold'].out)
    # crossed spears
    sp = c.bres(12, 25, 20, 17) | c.bres(12, 17, 20, 25)
    c.put(sp, R['bronze'][0], 'flat', only_on=True)
    c.put(c.rect(19, 16, 21, 16) | c.rect(21, 16, 21, 18) | c.rect(11, 16, 13, 16) | c.rect(11, 16, 11, 18),
          R['bronze'][0], 'flat', only_on=True)
    c.outline()
    return c


def smuggler_ledger():
    c = Canvas(32)
    ramp = Ramp(['#1A1414', '#2E2222', '#4A3432', '#6E4E48', '#98746A'], '#0A0707')
    pages = c.poly([(9, 5), (27, 5), (27, 28), (9, 28)])
    c.put(pages, R['paper'], 'flat', base=2)
    for y in range(7, 28, 2):
        c.put(c.rect(26, y, 27, y), R['paper'][1], 'flat', only_on=True)
    cover = c.rect(5, 3, 25, 27)
    c.put(cover, ramp, 'bevel', base=2, sep=True)
    spine = c.rect(5, 3, 8, 27)
    c.put(spine, ramp, 'flat', base=1)
    for y in (6, 11, 16, 21, 25):
        c.put(c.rect(5, y, 8, y), R['hemp'], 'flat', base=3)
    lab = c.rect(13, 7, 21, 20)
    c.put(lab, R['paper'], 'bevel', base=2, sep=True)
    coin = c.circle(17, 13.5, 3.2)
    c.put(coin, R['gold'], 'sphere', base=2)
    c.put(c.rect(16, 12, 17, 14), R['ink'], 'flat', base=2)
    c.put(c.rect(14, 18, 20, 18), '#2B2A30', 'flat')
    c.outline()
    return c


# ============================================================================ goods
def old_net():
    c = Canvas(32)
    ramp = R['hemp']
    blob = c.ellipse(16, 18, 13, 10) | c.ellipse(12, 11, 7, 5)
    mesh = blob & (((c.xi + c.yi) % 5 == 0) | ((c.xi - c.yi) % 5 == 0))
    c.put(mesh, ramp, 'ray', base=2)
    rim = S.outline_only(blob) & (c.Y > 20)
    c.put(dilate4(rim) & blob, ramp, 'flat', base=1)
    floats = [(7, 23), (16, 28), (25, 22)]
    for (x, y) in floats:
        c.put(c.ellipse(x, y, 2.4, 1.8), R['cork'] if 'cork' in R else R['wood'], 'sphere', sep=True)
    c.put(c.ellipse(24.5, 9, 2.6, 2.6), R['mist'], 'sphere', sep=True)  # glass float
    c.outline()
    return c


def river_mud():
    c = Canvas(32)
    ramp = R['mud']
    pile = c.ellipse(16, 23, 13, 6.5) | c.ellipse(14, 17, 8, 6) | c.ellipse(19, 14, 5, 4.5)
    c.put(pile, ramp, 'sphere', base=2, cx=15, cy=15, rx=14, ry=12)
    for pts in ([(6, 23), (12, 21), (18, 24)], [(12, 16), (17, 15), (22, 17)]):
        c.put(c.bres_path(pts) & erode4(pile), ramp[1], 'flat', out=ramp.out)
    c.put(c.ellipse(13, 12.5, 2.4, 1.2) | c.ellipse(9, 19, 1.6, 0.9), ramp[4], 'flat')
    puddle = c.ellipse(24, 28, 6, 1.6) & ~pile
    c.put(puddle, R['qi'], 'flat', base=1)
    c.put(c.rect(22, 28, 24, 28) & puddle, R['qi'][3], 'flat')
    c.outline()
    return c


def cloth():
    c = Canvas(32)
    for k, (ramp, y) in enumerate(((R['hemp'], 20), (R['indigo'], 14), (R['jade'], 8))):
        slab = S.rounded_rect(c, 5 + k, y, 26 - k, y + 7, 2)
        c.put(slab, ramp, 'bevel', base=2, sep=True)
        fold = c.rect(6 + k, y + 3, 25 - k, y + 3)
        c.put(fold, ramp[1], 'flat', out=ramp.out)
        c.put(c.rect(7 + k, y + 1, 12 + k, y + 1), ramp[4], 'flat', out=ramp.out)
    tie = c.rect(15, 7, 17, 28) & c.a
    c.put(tie, R['straw'], 'flat', base=3)
    c.outline()
    return c


def _arrow(c, a, b, head=R['iron'], shaft=R['wood'], fletch=R['red']):
    s = c.seg(a[0], a[1], b[0], b[1], 1.6)
    c.put(s, shaft, 'flat', base=3)
    hx, hy = b
    hd = c.poly([(hx + 2.5, hy - 2.5), (hx - 2.5, hy - 0.5), (hx + 0.5, hy + 2.5)])
    c.put(hd, head, 'ray', base=3, sep=True)
    fx, fy = a
    fl = c.poly([(fx, fy), (fx - 0.5, fy - 4), (fx + 3.5, fy - 1)]) | c.poly([(fx, fy), (fx + 4, fy + 0.5), (fx + 1, fy - 3.5)])
    c.put(fl, fletch, 'ray', base=2, sep=True)


def arrows():
    c = Canvas(32)
    for (a, b, fl) in (((5, 22), (24, 3), R['red']), ((9, 27), (27, 9), R['paper']), ((4, 28), (22, 10), R['red'])):
        _arrow(c, a, b, fletch=fl)
    band = c.seg(11, 18, 16, 23, 2.4) & c.a
    c.put(band, R['straw'], 'flat', base=2)
    c.outline()
    return c


def bow_parts():
    c = Canvas(32)
    limb1 = S.taper_curve(c, (5, 27), (6, 9), (22, 4), 3.6, 2.0)
    limb2 = S.taper_curve(c, (10, 29), (26, 27), (28, 12), 3.2, 1.8)
    c.put(limb1, R['wood'], 'ray', base=2)
    c.put(limb2, R['wood'], 'ray', base=2, sep=True)
    for (x, y) in ((22, 4), (28, 12)):
        c.put(c.circle(x, y, 1.7), R['bone'], 'sphere', sep=True)
    grip = c.rect(4, 22, 7, 26) & limb1
    c.put(grip, R['leather'], 'flat', base=2)
    coil = c.ring(17, 17, 5, 1.2, 3.6) | c.ring(15.5, 18, 3.6, 1.1, 2.6)
    c.put(coil, R['paper'], 'flat', base=3, sep=True)
    c.put(c.bres(21, 19, 24, 23), R['paper'], 'flat', base=3)
    c.outline()
    return c

def prayer_beads():
    c = Canvas(32)
    n = 14
    for k in range(n):
        a = -math.pi / 2 + k * 2 * math.pi / n
        x, y = 16 + math.cos(a) * 10, 14 + math.sin(a) * 10
        ramp = R['jade'] if k == 0 else R['darkwood']
        c.put(c.circle(x, y, 2.3), ramp, 'sphere', sep=True)
    guru = c.circle(16, 25, 2.8)
    c.put(guru, R['jade'], 'sphere', sep=True)
    tas = c.poly([(14.5, 27), (17.5, 27), (19.5, 31), (12.5, 31)])
    c.put(tas, R['red'], 'ray', base=2, sep=True)
    c.outline()
    return c


def talisman_paper():
    c = Canvas(32)
    for k, (x, y) in enumerate(((13, 5), (9, 4), (5, 3))):
        m = c.poly([(x + 8, y), (x + 17, y + 3), (x + 10, y + 26), (x + 1, y + 23)])
        c.put(m, R['talisman'], 'bevel', base=3 - (1 if k < 2 else 0), sep=True)
    top = c.poly([(5 + 8, 3), (5 + 17, 3 + 3), (5 + 10, 3 + 26), (5 + 1, 3 + 23)])
    border = S.outline_only(erode4(erode4(top)))
    c.put(border, R['seal'], 'flat', base=2, only_on=True)
    c.outline()
    return c


def ink():
    c = Canvas(32)
    slab = S.rounded_rect(c, 3, 16, 24, 28, 2)
    c.put(move(slab, 0, 1) | slab, R['stone'], 'flat', base=1)
    c.put(slab, R['stone'], 'bevel', base=2)
    well = S.rounded_rect(c, 6, 18, 21, 25, 2)
    c.put(well, R['ink'], 'flat', base=0)
    c.put(c.rect(8, 19, 12, 19), R['ink'][3], 'flat')
    stick = c.poly([(17, 22), (23, 3), (29, 5), (22, 24)])
    c.put(stick, R['ink'], 'ray', base=2, sep=True)
    c.put(c.poly([(22, 8), (28, 10), (27, 13), (21, 11)]), R['gold'], 'flat', base=3)
    c.put(c.rect(19, 21, 21, 22) & stick, R['ink'][0], 'flat')
    c.outline()
    return c

def lantern_wick():
    c = Canvas(32)
    spool = c.rect(5, 12, 22, 25)
    ends = c.ellipse(5, 18.5, 2.4, 7.5) | c.ellipse(22, 18.5, 2.4, 7.5)
    c.put(spool, R['hemp'], 'vgrad', base=3)
    for x in range(7, 21, 2):
        c.put(c.bres(x, 13, x + 1, 24), R['hemp'][1], 'flat', only_on=True)
    c.put(ends, R['wood'], 'ray', base=2, sep=True)
    c.put(c.ellipse(22, 18.5, 1, 2.5), R['wood'][0], 'flat')
    end = S.bez_line(c, (21, 12), (26, 10), (26, 6), 1.8)
    c.put(end & ~ends, R['hemp'], 'flat', base=3, sep=True)
    c.put(c.rect(25, 5, 26, 6), R['ink'], 'flat', base=2)
    fl = S.flame(c, 25.5, 5.5, 4, 6, 0.4)
    c.put(fl & (c.Y < 5), R['fire'], 'vgrad', base=3, bands=((0.35, 1), (0.75, 0), (9, -1)))
    c.outline()
    return c

def rice():
    c = Canvas(32)
    sack = S.rounded_rect(c, 6, 9, 25, 29, 3) | c.poly([(8, 10), (10, 5), (21, 5), (23, 10)])
    c.put(sack, R['hemp'], 'ray')
    fold = c.rect(8, 9, 23, 10)
    c.put(fold, R['hemp'], 'flat', base=1)
    grains = c.ellipse(15.5, 6, 5.5, 2)
    c.put(grains, R['rice'], 'ray', base=3)
    # woven texture + small red maker's stamp
    for y in range(13, 28, 3):
        c.put(c.rect(8, y, 23, y) & erode4(sack) & ((c.xi + y) % 2 == 0), R['hemp'][1], 'flat', only_on=True)
    c.put(c.rect(18, 21, 21, 24), R['seal'], 'flat', base=2)
    c.put(c.rect(19, 22, 20, 23), R['seal'], 'flat', base=4)
    for (x, y) in ((13, 6), (17, 5), (15, 7)):
        c.put(c.rect(x, y, x, y), R['rice'][4], 'flat')
    heap = c.ellipse(26, 28, 4.5, 2) & (c.Y < 30)
    c.put(heap, R['rice'], 'ray', sep=True)
    c.outline()
    return c


def kite():
    c = Canvas(32)
    body = S.diamond(c, 14, 13, 10, 11.5)
    c.put(body, Ramp(['#6A2A2A', '#B04438', '#E86A4E', '#F7B07A', '#FFE3B8'], '#2A0E0E'), 'ray', base=2)
    # painted fish-face: eyes and cross spars
    spars = c.bres(14, 2, 14, 24) | c.bres(4, 13, 24, 13)
    c.put(spars, R['wood'][1], 'flat', only_on=True)
    for x in (10, 18):
        c.put(c.circle(x + 0.5, 10.5, 2), R['paper'], 'flat', base=4, only_on=True)
        c.put(c.rect(x, 10, x, 11), R['ink'], 'flat', base=0)
    c.put(c.rect(12, 17, 16, 17), R['ink'], 'flat', base=2, only_on=True)
    tail = S.bez_line(c, (14, 24), (18, 30), (27, 27))
    c.put(tail, R['paper'], 'flat', base=3)
    for (x, y) in ((17, 28), (23, 28)):
        bw = c.poly([(x - 2, y - 2), (x + 2, y + 2), (x + 2, y - 2), (x - 2, y + 2)])
        c.put(bw, R['jade'], 'flat', base=3)
    c.outline()
    return c


def _incense(ornate):
    c = Canvas(32)
    if not ornate:
        bowl = c.ellipse(16, 24, 10, 5) & (c.Y > 21)
        bowl |= c.ellipse(16, 22, 10, 2)
        c.put(bowl, R['bronze'], 'ray', sep=True)
        c.put(c.ellipse(16, 22, 8.5, 1.4), R['warmstone'], 'flat', base=3)
        for x in (13, 16, 19):
            st = c.rect(x, 9 + abs(x - 16), x, 21)
            c.put(st, R['red'], 'flat', base=2)
            c.put(c.rect(x, 9 + abs(x - 16), x, 9 + abs(x - 16)), R['fire'], 'flat', base=4)
        smoke = S.bez_line(c, (16, 8), (12, 5), (16, 3)) | S.bez_line(c, (13, 11), (9, 8), (11, 5))
        c.put(smoke, R['mist'], 'flat', base=3)
        c.put(c.rect(10, 29, 22, 29), R['bronze'], 'flat', base=1)
        c.outline()
    else:
        body = c.ellipse(16, 22, 10, 6)
        c.put(body, R['gold'], 'sphere', base=2)
        lid = c.ellipse(16, 16.5, 7.5, 3) | c.poly([(14, 16), (16, 11), (18, 16)])
        c.put(lid, R['gold'], 'ray', base=3, sep=True)
        for x in (8, 24):
            c.put(c.rect(x - 1, 26, x, 29), R['gold'], 'flat', base=1, sep=True)
        c.put(c.ring(16, 22, 7, 1, 3.5) & erode4(body), R['jade'], 'flat', base=3)
        smoke = (S.bez_line(c, (16, 10), (10, 8), (14, 4), 2.0) | S.bez_line(c, (15, 6), (21, 6), (22, 3), 1.6))
        c.put(smoke & ~c.a, R['violet'], 'flat', base=3)
        c.outline()
        c.glow('#9B78D1', (70,))
        S.sparkle(c, 26, 7, '#FFFFFF', R['gold'][3], 2)
        S.sparkle(c, 5, 12, '#FFFFFF', R['gold'][3], 1)
    return c


def restoration_ink():
    c = Canvas(32)
    m = jar(c, R['porcelain'], lid=R['jade'], x=14, y0=13, y1=29, w=9)
    c.put(c.ellipse(14, 12.5, 5, 1.2), R['jade'], 'flat', base=4)
    c.put(c.circle(14, 22, 3.5) & m, R['jade'], 'ray', base=2)
    c.put(c.circle(14, 22, 1.4) & m, R['jade'], 'flat', base=4)
    brush = c.seg(17, 13, 26, 3, 2.2)
    c.put(brush, R['bamboo'], 'across', base=2, sep=True)
    tip = c.poly([(15, 16), (15.5, 11.5), (19, 12.5)])
    c.put(tip, R['jade'], 'ray', base=3, sep=True)
    c.outline()
    return c


def fish_bait():
    c = Canvas(32)
    line = c.bres(19, 1, 19, 4)
    c.put(line, R['paper'], 'flat', base=3)
    eye = c.ring(19.5, 6, 2, 1.1)
    c.put(eye, R['iron'], 'flat', base=3)
    shank = c.rect(19, 8, 20, 20)
    hookb = c.arc(14.5, 20, 5.5, 2.2, 180, 360)
    barb = c.poly([(9, 21), (9, 14), (12, 18)])
    c.put(shank | hookb | barb, R['iron'], 'ray', base=3)
    worm = (S.taper_curve(c, (15, 14), (8, 10), (7, 17), 3.4, 3.0) |
            S.taper_curve(c, (7, 17), (6, 26), (15, 26), 3.4, 3.4) |
            S.taper_curve(c, (15, 26), (25, 27), (27, 21), 3.4, 2.0))
    c.put(worm & ~(shank | hookb), R['pink'], 'ray', base=2, sep=True)
    for (x, y) in ((8, 13), (7, 21), (11, 26), (19, 26), (24, 25)):
        c.put(c.rect(x, y, x, y) & worm, R['pink'][1], 'flat', only_on=True)
    c.outline()
    return c

def blank_plate():
    c = Canvas(32)
    m = S.rounded_rect(c, 4, 6, 27, 27, 3)
    side = move(m, 0, 2) & ~m
    c.put(side | m, R['jade'], 'flat', base=1)
    c.put(m, R['jade'], 'ray', base=3)
    c.put(S.outline_only(S.rounded_rect(c, 6, 8, 25, 25, 2)), R['jade'][1], 'flat', out=R['jade'].out)
    c.put(c.ring(15.5, 16.5, 6.5, 1), R['jade'][1], 'flat', out=R['jade'].out)
    c.put(c.ring(15.5, 16.5, 3.5, 1), R['jade'][4], 'flat', out=R['jade'].out)
    for (x, y) in ((8, 10), (23, 10), (8, 23), (23, 23)):
        c.put(c.rect(x, y, x, y), R['gold'], 'flat', base=3)
    c.outline()
    return c


def spirit_egg():
    c = Canvas(32)
    egg = c.ellipse(16, 17.5, 9.5, 12)
    c.put(egg, R['pearl'], 'sphere', base=2, cx=16, cy=17, rx=10, ry=12.5)
    for (x, y, r) in ((12, 11, 1.8), (20, 15, 2.2), (13, 21, 2.4), (20, 24, 1.6), (17, 8, 1.2)):
        c.put(c.circle(x, y, r) & erode4(egg), R['qi'], 'flat', base=2)
    crack = c.bres_path([(9, 18), (12, 16), (14, 19), (17, 16), (20, 19), (23, 17)])
    c.put(crack & erode4(egg), R['qi'], 'flat', base=4)
    nest = c.ellipse(16, 28, 11, 3) & ~egg
    c.put(nest, R['straw'], 'ray', base=2)
    c.outline()
    c.glow('#8AEBEE', (80,))
    return c


def drying_rack():
    c = Canvas(32)
    posts = c.rect(4, 5, 5, 29) | c.rect(26, 5, 27, 29)
    c.put(posts, R['bamboo'], 'hgrad', base=2)
    bar = c.rect(3, 6, 28, 7) | c.rect(4, 17, 27, 17)
    c.put(bar, R['bamboo'], 'vgrad', base=2, sep=True)
    for x in (4, 26):
        c.put(c.rect(x, 12, x + 1, 12) | c.rect(x, 22, x + 1, 22), R['bamboo'][1], 'flat', only_on=True)
    for k, (x, ramp) in enumerate(((10, R['leaf']), (16, R['moss']), (22, R['straw']))):
        st = c.rect(x, 8, x, 9)
        c.put(st, R['hemp'], 'flat', base=3)
        bunch = S.leaf(c, x + 0.5, 9.5, 270, 8.5, 5, 0.0)
        c.put(bunch, ramp, 'ray', base=2, sep=True)
    for x in (13, 19):
        c.put(S.leaf(c, x + 0.5, 18, 270, 7, 4, 0), R['ember'] if x == 13 else R['leaf'], 'ray', sep=True)
    feet = c.rect(2, 29, 7, 29) | c.rect(24, 29, 29, 29)
    c.put(feet, R['bamboo'], 'flat', base=1)
    c.outline()
    return c


# ============================================================================ natural treasures
def mindwell_lotus():
    """A soul-violet lotus over a jade pad, soul-light rising from its heart."""
    c = Canvas(32)
    pad = c.ellipse(16, 25, 13, 3.4)
    c.put(pad, R['jade'], 'ray')
    bx, by = 16, 23
    petals = [(bx - 1, by, 160, 10.5, 5.4, -0.12), (bx + 1, by, 20, 10.5, 5.4, 0.12),
              (bx - 1, by, 128, 12.5, 6.0, -0.06), (bx + 1, by, 52, 12.5, 6.0, 0.06), (bx, by + 0.5, 90, 15, 7.2, 0.0)]
    pr = R['violet']
    for (x, y, a, L, W, b) in petals:
        m = S.leaf(c, x, y, a, L, W, b, tip_power=0.7)
        c.put(m, pr, 'ray', base=3, sep=True, sep_col=pr[1])
        dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
        c.put(c.circle(x + dx * L * 0.9, y + dy * L * 0.9, L * 0.26) & m, pr, 'ray', base=4)
    c.put(c.ellipse(16, 21, 2.6, 1.4), R['gold'], 'flat', base=4)
    c.outline()
    c.glow('#9B78D1', (70,))
    S.sparkle(c, 16, 5, '#FFFFFF', R['violet'][3], 2)
    S.sparkle(c, 25, 11, '#FFFFFF', R['violet'][3], 1)
    return c


def evergreen_heart_seed():
    """A dark almond seed with a red heart-line pulse and the first green shoot."""
    c = Canvas(32)
    seed = c.ellipse(15, 19, 7.5, 9.5)
    c.put(seed, R['wood'], 'sphere', base=1)
    vein = S.bez_line(c, (15, 11), (12, 18), (15, 27), 1.2)
    c.put(vein & seed, R['red'], 'flat', base=3)
    c.put(c.circle(15, 19, 2.2) & seed, R['red'], 'sphere', base=3)
    shoot = S.bez_line(c, (16, 10), (18, 6), (21, 4), 1.4)
    c.put(shoot, R['leaf'], 'flat', base=3)
    c.put(S.leaf(c, 20.5, 4.5, 20, 6, 3, 0.1), R['leaf'], 'ray', base=3, sep=True)
    c.outline()
    c.glow('#D44B4E', (55,))
    return c


def evergreen_heart_fruit():
    """A heart-shaped crimson fruit on an evergreen sprig, glowing warm."""
    c = Canvas(32)
    heart = c.circle(11.5, 15, 6.2) | c.circle(20.5, 15, 6.2) | c.poly([(5.6, 17), (26.4, 17), (16, 28.5)])
    c.put(heart, R['red'], 'sphere', base=2)
    c.put(c.circle(10, 13, 1.6) & heart, R['red'], 'flat', base=4)
    stem = c.rect(16, 5, 16, 10)
    c.put(stem, R['wood'], 'flat', base=2)
    for a, L in ((150, 8), (35, 8), (110, 6)):
        c.put(S.leaf(c, 16, 7, a, L, 2.6, 0.0), R['leaf'], 'ray', base=2, sep=True)
    c.outline()
    c.glow('#F2B24C', (60,))
    S.sparkle(c, 24, 9, '#FFFFFF', R['gold'][3], 2)
    return c


for _id, _fn in (('manual_page', manual_page), ('riverbreath_scroll', riverbreath_scroll),
                 ('lu_journal_page', lu_journal_page), ('recipe_scroll', recipe_scroll),
                 ('river_token', river_token), ('jade_token', jade_token), ('cloud_token', cloud_token),
                 ('alliance_token', alliance_token), ('ironroot_token', ironroot_token),
                 ('mudwater_key', mudwater_key), ('entry_token', entry_token), ('siege_medal', siege_medal),
                 ('smuggler_ledger', smuggler_ledger), ('old_net', old_net), ('river_mud', river_mud),
                 ('cloth', cloth), ('arrows', arrows), ('bow_parts', bow_parts), ('prayer_beads', prayer_beads),
                 ('talisman_paper', talisman_paper), ('ink', ink), ('lantern_wick', lantern_wick), ('rice', rice),
                 ('kite', kite), ('calm_incense', lambda: _incense(False)),
                 ('myriad_year_calm_incense', lambda: _incense(True)), ('restoration_ink', restoration_ink),
                 ('fish_bait', fish_bait), ('blank_plate', blank_plate), ('spirit_egg', spirit_egg),
                 ('drying_rack', drying_rack), ('mindwell_lotus', mindwell_lotus),
                 ('evergreen_heart_seed', evergreen_heart_seed), ('evergreen_heart_fruit', evergreen_heart_fruit)):
    register(FAM, _id, _fn, GROUP)
