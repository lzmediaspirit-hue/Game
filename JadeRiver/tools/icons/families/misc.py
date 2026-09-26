"""Scrolls, pages, tokens, keys and miscellaneous goods.

Templates: paper page, closed scroll, open hand-scroll, hanging token (tablet or
disc with cord + tassel), sack, small jar.
"""
import math

from pix import Canvas, Ramp, dilate4, erode4, move, rgb
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


def aunt_pings_ladle():
    """A wooden soup ladle: a deep round bowl and a long handle with a hanging loop."""
    c = Canvas(32)
    wood = R['wood']
    handle = c.seg(8, 6, 19, 20, 2.6)
    c.put(handle, wood, 'ray', base=2)
    c.put(c.ring(7.5, 5.5, 2.4, 1.2), wood, 'flat', base=1)
    bowl = c.ellipse(21, 23, 7.5, 5.5)
    c.put(bowl, wood, 'sphere', base=2, cx=19, cy=21, rx=8, ry=6)
    c.put(c.ellipse(21, 21.5, 5.4, 2.6), wood[0], 'flat')
    c.put(c.ellipse(19.5, 21, 2.2, 0.9), R['mist'][2] if 'mist' in R else '#DDE8EE', 'flat')
    c.outline()
    return c


def tinkerers_gear():
    """A small brass gear: a toothed ring round a hub, with a bent pin through it."""
    import math
    c = Canvas(32)
    brass = R['bronze']
    body = c.ellipse(16, 16, 9.5, 9.5)
    for k in range(10):
        a = k * math.pi / 5
        body = body | c.ellipse(16 + 11 * math.cos(a), 16 + 11 * math.sin(a), 2.2, 2.2)
    hole = c.ellipse(16, 16, 3.2, 3.2)
    c.put(body & ~hole, brass, 'sphere', base=2, cx=13, cy=12, rx=12, ry=12)
    c.put(c.ring(16, 16, 5.6, 1.0), brass[1], 'flat')
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        c.put(c.ellipse(16 + 7.6 * math.cos(a), 16 + 7.6 * math.sin(a), 1.3, 1.3), brass[0], 'flat')
    c.put(c.seg(10, 25, 22, 7, 1.4), R['iron'], 'ray', base=1)
    c.outline()
    return c


def sealed_storage_pouch():
    """A rogue's storage pouch: a plump cloth bag, its drawstring tied, a red seal slip pasted across the knot."""
    c = Canvas(32)
    cloth = R['hemp']
    bag = c.ellipse(16, 21, 10, 8.5) | c.poly([(10, 14), (22, 14), (20, 10), (12, 10)])
    c.put(bag, cloth, 'sphere', base=2, cx=13, cy=17, rx=11, ry=10)
    c.put(c.ellipse(16, 10, 5.5, 2.2), cloth[1], 'flat')
    c.put(c.seg(11, 12, 21, 12, 1.4), R['wood'], 'ray', base=1)
    c.put(c.seg(21, 12, 25, 16, 1.1), R['wood'], 'ray', base=1)
    slip = c.rect(14, 9, 18, 21)
    c.put(slip, R['seal'], 'flat', base=2)
    c.put(c.rect(15, 12, 17, 13) | c.rect(15, 16, 17, 17), R['paper'][4] if 'paper' in R else '#F4E8C8', 'flat')
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


def _egg(shell, spots, glow, crack=True, wisps=False):
    """A spirit egg on straw, in its own colours (S46: the Beast King's nest egg, the Cloud Stag's egg)."""
    def build():
        c = Canvas(32)
        egg = c.ellipse(16, 17.5, 9.5, 12)
        c.put(egg, shell, 'sphere', base=2, cx=16, cy=17, rx=10, ry=12.5)
        for (x, y, r) in ((12, 11, 1.8), (20, 15, 2.2), (13, 21, 2.4), (20, 24, 1.6), (17, 8, 1.2)):
            c.put(c.circle(x, y, r) & erode4(egg), spots, 'flat', base=2)
        if crack:
            path = c.bres_path([(9, 18), (12, 16), (14, 19), (17, 16), (20, 19), (23, 17)])
            c.put(path & erode4(egg), spots, 'flat', base=4)
        if wisps:
            for (x0, y0, x1, y1) in ((5, 12, 9, 10), (23, 8, 27, 6), (24, 20, 28, 19)):
                c.put(c.seg(x0, y0, x1, y1, 0.8), R['cloud'], 'flat', base=4)
        nest = c.ellipse(16, 28, 11, 3) & ~egg
        c.put(nest, R['straw'], 'ray', base=2)
        c.outline()
        c.glow(glow, (80,))
        return c
    return build


def _beast_bag(cloth, trim, mark):
    """A Spirit Beast Bag: a plump drawstring pouch with a paw sewn on it; the cloth tells its grade (S46)."""
    def build():
        c = Canvas(32)
        bag = c.ellipse(16, 20, 10.5, 9) | c.poly([(9, 13), (23, 13), (21, 9), (11, 9)])
        c.put(bag, cloth, 'sphere', base=2, cx=13, cy=16, rx=12, ry=11)
        c.put(c.ellipse(16, 9, 5.5, 2.2), cloth[1], 'flat')
        c.put(c.seg(10, 11, 22, 11, 1.4), trim, 'ray', base=2)
        c.put(c.seg(22, 11, 26, 15, 1.0), trim, 'ray', base=2)
        c.put(c.circle(26, 16, 1.2), trim, 'flat', base=3)
        inner = erode4(bag)
        c.put(c.poly([(12.5, 25), (19.5, 25), (18, 21), (14, 21)]) & inner, mark, 'flat', base=3)   # the paw's pad
        for dx, dy in ((-4.6, 19.6), (-1.7, 17.4), (1.7, 17.4), (4.6, 19.6)):
            c.put(c.ellipse(16 + dx, dy, 1.3, 1.6) & inner, mark, 'flat', base=3)
        c.outline()
        return c
    return build


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


def spirit_fruit():
    """S49 treasure births: a pale jade peach with a blush of gold, two leaves, a halo of Qi."""
    c = Canvas(32)
    body = c.circle(16, 18, 8.4) | c.poly([(10, 14), (22, 14), (16, 6.5)])
    c.put(body, R['jade'], 'sphere', base=3)
    c.put(c.circle(19.5, 20, 4.2) & body, R['gold'], 'sphere', base=3)
    c.put(c.circle(12.5, 15, 1.7) & body, R['jade'], 'flat', base=5)
    stem = c.rect(16, 4, 16, 8)
    c.put(stem, R['wood'], 'flat', base=2)
    for a, L in ((155, 8), (30, 7)):
        c.put(S.leaf(c, 16, 6, a, L, 2.6, 0.0), R['leaf'], 'ray', base=2, sep=True)
    c.outline()
    c.glow('#9FE8C8', (60,))
    S.sparkle(c, 25, 10, '#FFFFFF', R['gold'][3], 2)
    return c


def hundred_year_wine():
    """S49 fortune deck: a jar dug out from under the roots, black with age and furred with moss, its seal still whole."""
    c = Canvas(32)
    jar = c.ellipse(16, 20, 9.5, 9) | c.rect(12, 9, 20, 13)
    c.put(jar, R['mud'], 'sphere', base=2, sep=True)
    c.put(c.ellipse(16, 8, 5, 2.4), R['darkwood'], 'sphere', base=2, sep=True)
    c.put(c.rect(11, 12, 21, 13) & jar, R['gold'], 'flat', base=3)
    for (x, y, r) in ((10, 22, 2.6), (21, 26, 2.2), (13, 27, 1.6)):
        c.put(c.circle(x, y, r) & jar, R['moss'], 'flat', base=2)
    c.put(c.rect(14, 17, 18, 22) & jar, R['seal'], 'flat', base=3)
    c.outline()
    c.glow('#E8C27A', (50,))
    return c


def longevity_peach():
    """S49 lifespan: the peach of long life, pointed at the tip, rose-blushed, sitting on two leaves."""
    c = Canvas(32)
    body = c.circle(16, 19, 8.8) | c.poly([(8.5, 16), (23.5, 16), (16.5, 5.5)])
    c.put(body, R['lotuspink'], 'sphere', base=3)
    c.put(c.circle(19, 13, 6.5) & body, R['red'], 'sphere', base=2)
    c.put(c.circle(12, 24, 5) & body, R['rice'], 'sphere', base=3)
    c.put(c.bres(16, 7, 13, 26) & body, R['pink'], 'flat', base=1)
    for a, L in ((200, 9), (340, 9)):
        c.put(S.leaf(c, 16, 27, a, L, 3.0, 0.0), R['leaf'], 'ray', base=2, sep=True)
    c.outline()
    c.glow('#F7C9D0', (50,))
    return c


def thousand_year_lingzhi():
    """S49 lifespan: a lingzhi of a thousand years, seen from the side: a lacquered red-brown dome ringed like an old
    tree, a pale growing edge, and a short dark stem set off-centre in moss."""
    c = Canvas(32)
    stem = c.poly([(17, 16), (20, 16), (19.5, 28), (16.5, 28)])
    c.put(stem, R['darkwood'], 'ray', base=2, sep=True)
    cap = c.ellipse(15, 16, 13, 9) & c.rect(0, 0, 31, 17)
    c.put(cap, R['red'], 'sphere', base=1, sep=True)
    c.put(cap & ~c.ellipse(15, 16.5, 11.6, 7.8), R['sand'], 'flat', base=3)
    for r in (4.0, 7.5):
        c.put(c.ring(15, 17, r, 1.0, ry=r * 0.7) & cap & c.rect(0, 0, 31, 15), R['darkwood'], 'flat', base=3)
    c.put(c.ellipse(18, 28.5, 7, 1.6), R['moss'], 'flat', base=2)
    c.outline()
    c.glow('#F2B35C', (55,))
    S.sparkle(c, 26, 6, '#FFFFFF', R['gold'][3], 2)
    return c

def guqin():
    """S49 leisure arts: a seven-string guqin lying on the diagonal: a broad dark-lacquered board with a waisted end,
    pale silk strings, a row of jade studs and a red tassel."""
    c = Canvas(32)
    body = c.poly([(1, 21), (19, 3), (29, 13), (11, 31)]) & ~c.poly([(20, 25), (25, 20), (29, 24), (24, 29)])
    c.put(body, R['darkwood'], 'ray', base=2, sep=True)
    top = c.poly([(4, 21), (19, 6), (26, 13), (11, 28)])
    c.put(top & body, R['wood'], 'flat', base=2)
    for k in range(5):
        o = k * 1.6
        c.put(c.bres(int(5 + o), int(20 + o), int(18 + o), int(7 + o)), R['rice'], 'flat', base=4)
    for i in range(5):
        c.put(c.circle(7 + i * 3, 25 - i * 3, 0.8), R['jade'], 'flat', base=4)
    c.put(c.bres(21, 4, 24, 1), R['red'], 'flat', base=3)
    c.put(c.circle(24.5, 1.8, 1.4), R['red'], 'sphere', base=2)
    c.outline()
    return c

for _id, _fn in (('manual_page', manual_page), ('riverbreath_scroll', riverbreath_scroll),
                 ('lu_journal_page', lu_journal_page), ('recipe_scroll', recipe_scroll),
                 ('river_token', river_token), ('jade_token', jade_token), ('cloud_token', cloud_token),
                 ('alliance_token', alliance_token), ('ironroot_token', ironroot_token),
                 ('mudwater_key', mudwater_key), ('entry_token', entry_token), ('siege_medal', siege_medal),
                 ('smuggler_ledger', smuggler_ledger), ('old_net', old_net), ('river_mud', river_mud),
                 ('aunt_pings_ladle', aunt_pings_ladle), ('tinkerers_gear', tinkerers_gear), ('sealed_storage_pouch', sealed_storage_pouch),
                 ('cloth', cloth), ('arrows', arrows), ('bow_parts', bow_parts), ('prayer_beads', prayer_beads),
                 ('talisman_paper', talisman_paper), ('ink', ink), ('lantern_wick', lantern_wick), ('rice', rice),
                 ('kite', kite), ('calm_incense', lambda: _incense(False)),
                 ('myriad_year_calm_incense', lambda: _incense(True)), ('restoration_ink', restoration_ink),
                 ('fish_bait', fish_bait), ('blank_plate', blank_plate), ('spirit_egg', spirit_egg),
                 ('rare_spirit_egg', _egg(R['gold'], R['red'], '#FFD27A')), ('cloud_stag_egg', _egg(R['cloud'], R['sky'], '#DDF0FF', crack=False, wisps=True)),
                 ('beast_bag_reed', _beast_bag(R['straw'], R['bamboo'], R['darkwood'])), ('beast_bag_hide', _beast_bag(R['leather'], R['hemp'], R['bone'])),
                 ('beast_bag_cloud', _beast_bag(R['cloud'], R['sky'], R['jade'])), ('beast_bag_mist', _beast_bag(R['deepjade'], R['jade'], R['pearl'])),
                 ('beast_bag_star', _beast_bag(R['violetsilk'], R['gold'], R['gold'])),
                 ('drying_rack', drying_rack), ('mindwell_lotus', mindwell_lotus),
                 ('evergreen_heart_seed', evergreen_heart_seed), ('evergreen_heart_fruit', evergreen_heart_fruit),
                 ('spirit_fruit', spirit_fruit), ('hundred_year_wine', hundred_year_wine),
                 ('longevity_peach', longevity_peach), ('thousand_year_lingzhi', thousand_year_lingzhi), ('guqin', guqin)):
    register(FAM, _id, _fn, GROUP)


# ============================================================================ S44 new forms: oils, a draught, baths, incense
def _oil(liquid):
    def draw():
        from families.beast_parts import vial
        c = Canvas(32)
        vial(c, liquid, cork=R['red'], shape='tall', level=0.72, x=13)
        # a cloth wiping rag tied round the neck: oils are rubbed on the blade
        rag = c.poly([(17, 9), (25, 12), (23, 16), (16, 12)])
        c.put(rag, R['hemp'], 'ray', base=2, sep=True)
        c.outline()
        return c
    return draw


def riverreed_draught():
    c = Canvas(32)
    bowl = c.ellipse(16, 22, 11, 6) & (c.Y > 20)
    bowl |= c.ellipse(16, 20, 11, 2.2)
    c.put(bowl, R['porcelain'], 'ray', sep=True)
    c.put(c.ellipse(16, 20, 9.5, 1.6), R['tea'], 'flat', base=3)
    c.put(c.rect(11, 20, 14, 20), R['tea'], 'flat', base=4)
    c.put(c.rect(11, 28, 21, 29), R['porcelain'], 'flat', base=1)
    root = S.bez_line(c, (20, 19), (24, 13), (22, 8), 1.6)
    c.put(root, R['straw'], 'flat', base=3)
    steam = S.bez_line(c, (13, 17), (10, 13), (13, 9)) | S.bez_line(c, (17, 16), (15, 12), (17, 7))
    c.put(steam & ~c.a, R['mist'], 'flat', base=3)
    c.outline()
    return c


def _bath(ribbon, herb):
    def draw():
        c = Canvas(32)
        bundle = c.ellipse(16, 20, 10, 8) | c.poly([(10, 14), (13, 9), (19, 9), (22, 14)])
        c.put(bundle, R['hemp'], 'ray', base=2)
        for (a, b) in (((12, 10), (9, 3)), ((16, 9), (16, 2)), ((20, 10), (24, 4))):
            c.put(S.bez_line(c, a, ((a[0] + b[0]) / 2 - 1, (a[1] + b[1]) / 2), b, 1.5), herb, 'flat', base=3)
        band = c.rect(6, 15, 26, 17) & bundle
        c.put(band, ribbon, 'flat', base=3, sep=True)
        c.put(c.rect(14, 15, 17, 17), ribbon, 'flat', base=4)
        c.outline()
        return c
    return draw


def calm_heart_incense():
    c = Canvas(32)
    bowl = c.ellipse(16, 24, 10, 5) & (c.Y > 21)
    bowl |= c.ellipse(16, 22, 10, 2)
    c.put(bowl, R['jade'], 'ray', sep=True)
    c.put(c.ellipse(16, 22, 8.5, 1.4), R['warmstone'], 'flat', base=3)
    for x in (14, 18):
        st = c.rect(x, 10 + abs(x - 16), x, 21)
        c.put(st, R['plum'], 'flat', base=2)
        c.put(c.rect(x, 10 + abs(x - 16), x, 10 + abs(x - 16)), R['fire'], 'flat', base=4)
    beads = c.ring(16, 23, 11.5, 1.2, 4) & (c.Y > 24)
    c.put(beads, R['wood'], 'flat', base=3)
    smoke = S.bez_line(c, (14, 9), (10, 6), (14, 3)) | S.bez_line(c, (18, 9), (22, 6), (19, 2))
    c.put(smoke, R['lotuspink'], 'flat', base=3)
    c.outline()
    return c


for _id, _fn in (('viper_oil', _oil(R['venom'])), ('ember_oil', _oil(R['ember'])), ('riverreed_draught', riverreed_draught),
                 ('copper_body_bath', _bath(R['copper'], R['moss'])), ('marrow_washing_bath', _bath(R['bone'], R['lotuspink'])),
                 ('jade_marrow_bath', _bath(R['jade'], R['mist'])), ('golden_body_bath', _bath(R['gold'], R['fire'])),
                 ('calm_heart_incense', calm_heart_incense)):
    register(FAM, _id, _fn, GROUP)


# ============================================================================ Act II · Sunscar Desert
SUN_GLOW = '#FFC870'


def sun_crown_fragment():
    """One gold ray broken from the Tomb King's sun crown, a jade bead set at its root."""
    c = Canvas(32)
    a = math.radians(60)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx  # across the ray, towards the shaded side
    bx, by = 11.0, 21.5

    def P(across, along):
        return (bx + px * across + dx * along, by + py * across + dy * along)

    # jagged stump where the ray snapped off the crown band
    stump = c.poly([P(-5, -0.5), P(5, -0.5), P(4.6, -5.5), P(2.0, -3.8), P(-0.2, -6.5), P(-2.6, -4.2), P(-4.8, -5.2)])
    c.put(stump, R['gold'], 'ray', base=2)
    c.put(stump & ~move(stump, 0, -2) & ~move(stump, 1, -1), R['gold'][1], 'flat', out=R['gold'].out)
    # the ray: a slender spike with a lit and a shaded face and a bright ridge
    tip = P(0, 22.5)
    bl, br, ml, mr = P(-3.6, 0), P(3.6, 0), P(-2.4, 8), P(2.4, 8)
    ray = c.poly([bl, ml, tip, mr, br])
    c.put(ray, R['gold'], 'flat', base=2, sep=True)
    c.put(c.poly([bl, ml, tip, (bx, by)]) & ray, R['gold'], 'flat', base=3)
    c.put(c.poly([(bx, by), tip, mr, br]) & ray, R['gold'], 'flat', base=1)
    r0, r1 = P(0, 5), P(0, 19.5)
    c.put(c.bres(int(r0[0]), int(r0[1]), int(r1[0]), int(r1[1])) & erode4(ray), R['gold'], 'flat', base=4)
    # jade bead in a round gold bezel at the root
    bez = c.circle(bx, by, 3.4)
    c.put(bez, R['gold'], 'sphere', base=2, sep=True)
    bead = c.circle(bx, by, 2.2)
    c.put(bead, R['jade'], 'sphere', base=2)
    c.put(c.rect(int(bx) - 1, int(by) - 1, int(bx) - 1, int(by) - 1), R['jade'][4], 'flat')
    c.outline()
    c.glow(SUN_GLOW, (90, 40))
    S.sparkle(c, int(tip[0]) + 3, int(tip[1]) + 3, '#FFFFFF', R['gold'][3], 1)
    return c


def _sun_seal(c, cx, cy, rd, rc, clip=None, rays=12, glyph=True):
    """The Sunscar sun seal: gold rays, gold disc, jade inlay ring, engraved field, jade centre with a sun glyph."""
    gold, jade = R['gold'], R['jade']
    sph = dict(cx=cx - 1, cy=cy - 1, rx=rd + 2, ry=rd + 2)
    rm = c.empty()
    for k in range(rays):
        a = math.radians(k * 360.0 / rays + 90)
        L = rd + (rd * 0.45 if k % 2 == 0 else rd * 0.25)
        da = math.pi / rays * 0.8
        rm |= c.poly([(cx + math.cos(a - da) * (rd - 0.5), cy - math.sin(a - da) * (rd - 0.5)),
                      (cx + math.cos(a) * L, cy - math.sin(a) * L),
                      (cx + math.cos(a + da) * (rd - 0.5), cy - math.sin(a + da) * (rd - 0.5))])
    c.put(rm, gold, 'ray', base=3, clip=clip)
    disc = c.circle(cx, cy, rd)
    c.put(disc, gold, 'sphere', base=2, sep=True, clip=clip, **sph)
    ro = rd - 1.1
    w = max(1.3, rd * 0.13)
    inlay = c.ring(cx, cy, ro, w)
    c.put(inlay, jade, 'flat', base=2, clip=clip)
    c.put(inlay & c.sector(cx, cy, rd, 95, 200), jade, 'flat', base=3, clip=clip)
    c.put(inlay & c.sector(cx, cy, rd, 280, 350), jade, 'flat', base=1, clip=clip)
    for k in range(rays):
        a = math.radians(k * 360.0 / rays + 90)
        r0, r1 = rc + 1.0, ro - w - 0.6
        ln = c.bres(int(cx + math.cos(a) * r0), int(cy - math.sin(a) * r0),
                    int(cx + math.cos(a) * r1), int(cy - math.sin(a) * r1))
        c.put(ln & disc & ~inlay, gold[0], 'flat', out=gold.out, clip=clip)
    centre = c.circle(cx, cy, rc)
    c.put(centre, jade, 'sphere', base=2, sep=True, clip=clip, cx=cx - 0.5, cy=cy - 0.5, rx=rc + 1, ry=rc + 1)
    if glyph:
        sun = c.ring(cx, cy, rc * 0.62, 1.0) | c.circle(cx, cy, 0.8)
        c.put(sun & centre, gold, 'flat', base=3, clip=clip)
    return disc | rm


def sun_seal_shard():
    """A wedge snapped from the sun seal: about a third of the disc, from the jade heart to the rayed rim."""
    c = Canvas(32)
    cx, cy, rd = 8.5, 22.5, 13.0
    pts = [(cx - 0.6, cy + 0.8)]
    for k, rr in enumerate((3.5, 6.5, 9.5, 12.5, 15.5, 19.5)):
        a = math.radians(-14 + (2.4 if k % 2 else -2.4) * (1 if k < 4 else 0))
        pts.append((cx + math.cos(a) * rr, cy - math.sin(a) * rr))
    for t in range(-14, 106, 6):
        a = math.radians(t)
        pts.append((cx + math.cos(a) * 20, cy - math.sin(a) * 20))
    for k, rr in enumerate((19.5, 15.5, 12.5, 9.5, 6.5, 3.5)):
        a = math.radians(104 + (2.4 if k % 2 else -2.4) * (1 if k > 1 else 0))
        pts.append((cx + math.cos(a) * rr, cy - math.sin(a) * rr))
    clip = c.poly(pts)
    side = (move(clip, 1, 2) | move(clip, 0, 1)) & ~clip & dilate4(c.circle(cx, cy, rd))
    c.put(side, R['gold'], 'flat', base=1)
    _sun_seal(c, cx, cy, rd, 4.6, clip=clip, glyph=False)
    c.outline()
    c.glow(SUN_GLOW, (50,))
    return c


def sunscar_seal():
    """The Tomb King's sun seal, whole: a rayed gold disc with a jade heart."""
    c = Canvas(32)
    _sun_seal(c, 16, 16, 9.5, 4.4)
    c.put(c.ellipse(11.5, 11.5, 1.8, 1.0), R['gold'][4], 'flat', only_on=True)
    c.outline()
    c.glow(SUN_GLOW, (110, 45))
    S.sparkle(c, 26, 5, '#FFFFFF', R['gold'][3], 2)
    return c


for _id, _fn in (('sun_crown_fragment', sun_crown_fragment), ('sun_seal_shard', sun_seal_shard),
                 ('sunscar_seal', sunscar_seal)):
    register(FAM, _id, _fn, GROUP)


# ============================================================================ Act II · Starsea
STARPAPER = Ramp(['#4A5664', '#8793A3', '#C6CFDA', '#E6EBF0', '#FFFDF4'], '#19202A')
SKY_INK = Ramp(['#0C0E26', '#191D46', '#2A3070', '#4652A0', '#8290D4'], '#050616')
QI_MIST = Ramp(['#1B5A6E', '#2F86A0', '#58B6CC', '#94DBE6', '#D6F6FA'], '#0B2530')
LACQUER = Ramp(['#07080B', '#121419', '#22262F', '#3C4250', '#7D879C'], '#020203')
STAR_GLOW = '#BFD8FF'
WARD_GLOW = '#8AEBEE'


def _faint(c, mask, col, al):
    """Semi-transparent pixels on empty canvas only (a ward ring behind the object)."""
    free = mask & (c.alpha == 0)
    c.rgb[free] = rgb(col)
    c.alpha[free] = al


def _star(c, x, y, core='#FFFDF4', arm=None):
    """A small star: bright core pixel with four dimmer arms."""
    arm = arm or SKY_INK[4]
    c.put(S.star4(c, x, y, 1) & ~c.rect(x, y, x, y), arm, 'flat', out=SKY_INK.out, only_on=True)
    c.put(c.rect(x, y, x, y), core, 'flat', out=SKY_INK.out, only_on=True)


# ---------------------------------------------------------------------------- star reading
def star_reading():
    """A slip of pale star-paper: a constellation in sky ink, one star caught in a sighting ring."""
    c = Canvas(32)
    cx, cy, a, k = 16.5, 16.5, math.radians(22), 0.009  # k: how much both ends lift
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    u = (c.X - cx) * dx + (c.Y - cy) * dy
    v = (c.X - cx) * px + (c.Y - cy) * py
    bow = -k * u * u

    def P(uu, vv):
        vv -= k * uu * uu
        return (int(round(cx + uu * dx + vv * px - 0.5)), int(round(cy + uu * dy + vv * py - 0.5)))

    strip = (u >= -12.5) & (u <= 12.5) & (abs(v - bow) <= 4.8)
    c.put(strip, STARPAPER, 'bevel', base=3)
    # the far end rolls over into a small curl
    roll = strip & (u > 9.0)
    c.put(roll, STARPAPER, 'flat', base=2, sep=True, sep_col=STARPAPER[1])
    c.put(roll & (u <= 10.2), STARPAPER, 'flat', base=4)
    c.put(roll & (u > 11.6), STARPAPER, 'flat', base=1)
    # the near corner curls up too, showing the back of the slip
    ear = strip & c.poly([P(-12.6, 4.9), P(-9.4, 4.9), P(-12.6, 1.8)])
    c.put(ear, STARPAPER, 'flat', base=2, sep=True, sep_col=STARPAPER[1])
    # constellation joined by fine lines, stars in sky ink
    stars = [P(-8.8, 1.6), P(-4.4, -2.2), P(0.4, 1.6), P(5.2, -1.8)]
    body = strip & ~roll & ~ear
    c.put(c.bres_path(stars) & body, SKY_INK[4], 'flat', out=STARPAPER.out)
    for (x, y) in stars:
        _star(c, x, y, core=SKY_INK[0], arm=SKY_INK[2])
    # sighting ring around the third star
    sx, sy = stars[2]
    c.put(c.ring(sx + 0.5, sy + 0.5, 3.5, 1.0) & body, R['seal'], 'flat', base=2)
    c.outline()
    c.glow(STAR_GLOW, (45,))
    return c


# ---------------------------------------------------------------------------- sky ink
def sky_ink():
    """A squat glass pot of sky ink: deep indigo flecked with star-dust, corked under a silver cap."""
    c = Canvas(32)
    glass = R['mist']
    body = S.rounded_rect(c, 4, 17, 27, 28, 4) | c.ellipse(15.5, 17.5, 9.5, 3.4)
    neck = c.rect(11, 12, 20, 16)
    c.put(body | neck, glass, 'ray', base=2)
    ink = erode4(body) & (c.Y > 16)
    c.put(ink, SKY_INK, 'sphere', base=2, cx=13, cy=20, rx=13, ry=9)
    c.put(ink & ~move(ink, 0, 1), SKY_INK, 'flat', base=4)
    c.pxs([(9, 21), (19, 20), (12, 25), (22, 25), (17, 26), (24, 21)], '#FFFDF4')
    c.pxs([(11, 22), (21, 23), (7, 24)], R['gold'][3])
    S.sparkle(c, 16, 22, '#FFFFFF', SKY_INK[4], 1)
    c.put(c.rect(5, 20, 5, 24) | c.rect(6, 18, 6, 18), '#F4FBFB', 'flat')
    lip = c.rect(10, 11, 21, 12)
    c.put(lip, glass, 'vgrad', base=3, sep=True)
    cork = c.rect(12, 8, 19, 10)
    c.put(cork, R['wood'], 'ray', base=3, sep=True)
    cap = c.rect(11, 6, 20, 8) | c.rect(13, 5, 18, 5)
    c.put(cap, R['silver'], 'ray', base=2, sep=True)
    c.put(c.rect(15, 4, 16, 4), R['cyan'], 'flat', base=3)
    # an ink run down the shoulder
    drip = c.rect(20, 13, 21, 14) | c.rect(21, 15, 22, 17) | c.rect(22, 18, 22, 19)
    c.put(drip, SKY_INK, 'flat', base=1)
    c.put(c.rect(21, 15, 21, 16), SKY_INK, 'flat', base=3)
    c.outline()
    c.glow('#9FB4FF', (55,))
    return c


# ---------------------------------------------------------------------------- ledger
def ledger_page():
    """One page torn from the Black Ledger: columns of entries, stitch holes, a dark-red seal smudge."""
    c = Canvas(32)
    paper = R['paper']
    torn = [(10, 29), (8.5, 26.5), (10, 24), (8, 21.5), (9.5, 18.5), (7.5, 16), (9, 13), (7, 10.5), (8.5, 8),
            (7, 5.5)]
    m = c.poly([(24, 3), (27.5, 26)] + torn)
    c.put(m, paper, 'bevel', base=3)
    edge = S.outline_only(m) & (c.X < 12)
    c.put(edge, paper[4], 'flat', out=paper.out)
    for (x, y) in ((11, 8), (11, 14), (12, 20), (13, 26)):
        c.put(c.rect(x, y, x, y) & m, paper[0], 'flat', out=paper.out)
    # vertical columns of entries, leaning with the page
    for k, x0 in enumerate((22, 19, 16, 13)):
        y_top = 6 + (3 if k % 2 else 1)
        y_bot = 25 - (k * 3) % 5
        for y in range(y_top, y_bot):
            if (y + k) % 4 == 3:
                continue
            x = int(round(x0 + (y - 4) * 0.14))
            c.put(c.rect(x, y, x, y) & erode4(m), '#2B2A30', 'flat')
    c.put(c.bres(12, 6, 23, 5) & erode4(m), R['seal'][1], 'flat', out=paper.out)
    # a smudged square seal: the stamp, and the smear dragged out of it
    seal = c.poly([(19, 19), (24.5, 18.5), (25, 24), (19.5, 24.5)])
    smear = c.poly([(19.3, 21), (19.6, 24.4), (17, 25.6), (16.6, 24.2)])
    c.put(smear & erode4(m), R['seal'], 'flat', base=1)
    c.put(seal & erode4(m), R['seal'], 'flat', base=1)
    c.put(S.outline_only(erode4(seal)) & erode4(m), R['seal'], 'flat', base=2)
    c.put(c.rect(21, 21, 22, 21) | c.rect(22, 22, 22, 22), R['seal'], 'flat', base=0)
    c.outline()
    return c


def black_ledger():
    """Elder Gu's Black Ledger, stitched back together: black lacquer, a thick page block, a red cord."""
    c = Canvas(32)
    back = c.rect(7, 7, 27, 28)
    c.put(back, LACQUER, 'flat', base=1)
    pages = c.rect(6, 6, 26, 27)
    c.put(pages, R['paper'], 'flat', base=2, sep=True, sep_col=R['paper'][0])
    for y in range(8, 27, 2):
        c.put(c.rect(24, y, 26, y) & pages, R['paper'][1], 'flat', only_on=True)
    for x in range(8, 26, 2):
        c.put(c.rect(x, 25, x, 27) & pages, R['paper'][1], 'flat', only_on=True)
    # loose pages working out of the block
    loose = (c.poly([(23, 9), (29.5, 10.5), (29, 13), (23, 12)]) | c.poly([(23, 20), (29, 22.5), (28, 24.5), (23, 22)])
             | c.poly([(10, 26), (17, 26.5), (16.5, 29.5), (9.5, 29)]))
    c.put(loose & ~c.a, R['paper'], 'flat', base=3, sep=True, sep_col=R['paper'][0])
    cover = c.rect(4, 4, 23, 24)
    c.put(cover, LACQUER, 'bevel', base=2, sep=True)
    c.put(c.rect(4, 4, 6, 24), LACQUER, 'flat', base=1)
    for y in (6, 10, 14, 18, 22):
        c.put(c.rect(4, y, 6, y), R['bone'], 'flat', base=2)
    # lacquer gloss
    c.put(c.bres(9, 21, 12, 18) | c.bres(20, 9, 21, 8), LACQUER, 'flat', base=3)
    # the split across the cover, sewn shut with cross stitches
    crack = c.bres_path([(17, 4), (15, 7), (18, 10), (15, 13)])
    c.put(move(crack, -1, 0) & ~crack & c.rect(7, 4, 23, 24), LACQUER, 'flat', base=3)
    c.put(crack, LACQUER, 'flat', base=0)
    for (x, y) in ((16, 6), (16, 11)):
        st = c.pts([(x - 1, y - 1), (x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x, y)])
        c.put(st, R['hemp'], 'flat', base=3)
    # gold corner caps on the open side
    for pts in ([(20, 4), (23.9, 4), (23.9, 8)], [(23.9, 20.5), (23.9, 24.9), (20, 24.9)]):
        c.put(c.poly(pts), R['gold'], 'flat', base=3, sep=True)
    # red cord round the book, knotted, the ends hanging free
    cord = c.rect(4, 16, 26, 17)
    c.put(cord, R['red'], 'flat', base=2)
    c.put(c.rect(4, 16, 26, 16), R['red'], 'flat', base=3)
    ends = S.bez_line(c, (18, 18), (20, 23), (24, 27)) | S.bez_line(c, (17, 18), (15, 24), (17, 29))
    c.put(ends, R['red'], 'flat', base=2)
    knot = c.circle(17.5, 16.5, 2.0)
    c.put(knot, R['red'], 'sphere', sep=True)
    c.put(c.rect(4, 4, 5, 4) | c.rect(4, 5, 4, 5), LACQUER[4], 'flat')
    c.outline()
    return c


# ---------------------------------------------------------------------------- star charts
def _star_chart(end, cord):
    """Half-open star chart: an indigo sky with a dotted route between stars, rolled up on the right."""
    c = Canvas(32)
    sheet = c.rect(4, 7, 22, 25)
    c.put(sheet, STARPAPER, 'bevel', base=3)
    field = c.rect(5, 9, 21, 23)
    c.put(field, SKY_INK, 'vgrad', base=2, bands=((0.3, 0), (0.7, -1), (9, -1)))
    # free edge curling up on the left
    c.put(c.rect(3, 6, 4, 26), STARPAPER, 'hgrad', base=3, sep=True, sep_col=STARPAPER[1])
    # the rolled part
    roll = c.rect(21, 4, 27, 28)
    c.put(roll, STARPAPER, 'hgrad', base=2, sep=True, sep_col=STARPAPER[0],
          bands=((0.25, 0), (0.5, 1), (0.8, 0), (9, -1)))
    cap = c.ellipse(24.5, 4.5, 3.4, 1.8)
    c.put(cap, STARPAPER, 'flat', base=3, sep=True, sep_col=STARPAPER[1])
    c.put(c.ellipse(24.5, 4.5, 1.6, 0.8), STARPAPER, 'flat', base=1)
    if end == 'wreck':
        route = [(7, 21), (11, 18), (15, 20), (18, 16)]
        ex, ey, into = 13, 12, (15, 14)
    else:
        route = [(7, 21), (10, 17), (14, 19), (13, 14)]
        ex, ey, into = 17, 12, (16, 13)
    pts = route + [into]
    dots = c.empty()
    for a, b in zip(pts, pts[1:]):
        dots |= c.bres(a[0], a[1], b[0], b[1])
    c.put(dots & ((c.xi + c.yi) % 2 == 0) & field, R['gold'], 'flat', base=3)
    for (x, y) in route:
        _star(c, x, y)
    if end == 'wreck':
        # a broken ship: hull snapped in a V, the mast knocked askew
        ship = ['.....#..',
                '......#.',
                '....#...',
                '#...#..#',
                '####.###',
                '.###.##.']
        m = c.from_rows(ship, ex - 4, ey - 3)
        c.put(m, R['bone'], 'flat', base=3)
        c.put(m & (c.yi >= ey + 1), R['bone'], 'flat', base=2)
    else:
        # a cluster of warm lanterns hanging in the dark
        for (x, y) in ((ex - 3, ey), (ex, ey - 2), (ex + 2, ey + 1), (ex - 1, ey + 3)):
            c.put(c.rect(x, y - 1, x, y - 1), SKY_INK[3], 'flat')
            c.put(c.rect(x - 1, y, x, y + 1), R['fire'], 'flat', base=2)
            c.put(c.rect(x - 1, y, x - 1, y), R['fire'], 'flat', base=4)
    # cord tied round the roll, one end hanging with a bead
    band = c.rect(21, 15, 27, 16)
    c.put(band, cord, 'flat', base=2)
    c.put(c.rect(21, 15, 27, 15), cord, 'flat', base=3)
    tail = S.bez_line(c, (27, 16), (29.5, 20), (28.5, 25))
    c.put(tail & ~roll, cord, 'flat', base=2)
    c.put(c.circle(28.5, 26.5, 1.4), cord, 'sphere', base=2, sep=True)
    c.outline()
    return c


# ---------------------------------------------------------------------------- vessels
def _batten_sail(c, pts, cloth, batten, n):
    """Junk sail: n battens split it into panels; each panel bellies (light at the top, shaded below)."""
    sail = c.poly(pts)
    c.put(sail, cloth, 'flat', base=2, sep=True)
    ys = c.yi[sail]
    y0, y1 = ys.min(), ys.max()
    rows = [int(round(y0 + (y1 - y0) * k / (n + 1.0))) for k in range(1, n + 1)]
    edges = [y0 - 1] + rows + [y1 + 1]
    for a, b in zip(edges, edges[1:]):
        panel = sail & (c.yi > a) & (c.yi < b)
        c.put(panel, cloth, 'vgrad', base=3, bands=((0.4, 1), (0.75, 0), (9, -1)))
    for y in rows:
        c.put(sail & (c.yi == y), batten, 'flat', base=1)
    return sail


def cloud_skiff():
    """The player's cloud skiff: a low jade-banded hull with a painted eye, a mat canopy, one batten sail,
    a jade ward-lantern hung from a crook at the bow, and a cushion of Qi mist under the keel."""
    from families.beast_parts import halo
    c = Canvas(32)
    mist = c.ellipse(9.5, 26.5, 4.2, 2.2) | c.ellipse(15.5, 27.2, 5, 2.3) | c.ellipse(21.5, 26.5, 4.2, 2.2)
    c.put(mist, QI_MIST, 'ray', base=3)
    mast = c.rect(14, 2, 14, 19)
    c.put(mast, R['wood'], 'flat', base=3)
    _batten_sail(c, [(8.5, 5), (17, 3.5), (20.5, 8.5), (21.8, 18), (9.5, 18)], R['hemp'], R['darkwood'], 4)
    c.put(c.poly([(14.5, 2), (18.5, 2.8), (14.5, 4)]) & ~c.a, R['jade'], 'flat', base=3)
    # woven-mat canopy over the stern
    can = c.ellipse(7.5, 18.5, 3.6, 3.2) & (c.Y < 18.5)
    c.put(can, R['straw'], 'ray', base=2, sep=True)
    c.put(can & (c.xi % 2 == 0) & erode4(can), R['straw'][1], 'flat', out=R['straw'].out)
    hull = c.poly([(3.5, 16.5), (8, 19), (23, 19), (27, 16), (25.5, 21.5), (21, 25), (9, 25), (6, 22)])
    c.put(hull, R['wood'], 'ray', base=2, sep=True)
    c.put(c.rect(4, 19, 26, 19) & hull, R['wood'], 'flat', base=4)
    band = c.rect(5, 20, 26, 20) & hull
    c.put(band, R['jade'], 'flat', base=1)
    c.put(band & (c.xi % 4 == 1), R['gold'], 'flat', base=3)
    # the painted eye on the bow
    c.put(c.rect(21, 22, 23, 23) | c.rect(20, 23, 20, 23), R['paper'], 'flat', base=4)
    c.put(c.rect(22, 22, 22, 23), R['ink'], 'flat', base=0)
    # the ward-lantern on its crook
    crook = c.bres_path([(25, 16), (25, 11), (26, 9), (28, 9)])
    c.put(crook, R['wood'], 'flat', base=3)
    lan = c.rect(27, 11, 28, 13)
    c.put(lan, R['jade'], 'flat', base=4, sep=True)
    c.put(c.rect(27, 10, 28, 10) | c.rect(27, 14, 28, 14), R['bronze'], 'flat', base=3)
    c.outline()
    halo(c, lan, '#67D6BD', (110,))
    return c


def storm_sloop():
    """A two-sail storm sloop: long dark hull on a comet-iron keel, two batten sails, a formation-ward ring."""
    c = Canvas(32)
    mast1, mast2 = c.bres(11, 19, 9, 5), c.bres(20, 19, 17, 4)
    c.put(mast1 | mast2, R['darkwood'], 'flat', base=3)
    _batten_sail(c, [(4.5, 7.5), (10, 5.5), (12.5, 11), (13.5, 18), (5.5, 18)], R['sky'], R['storm'], 3)
    _batten_sail(c, [(13, 5.5), (18, 3.5), (23.5, 8.5), (26.5, 18), (14.5, 18)], R['sky'], R['storm'], 4)
    pen = c.poly([(17, 3), (22, 3.6), (17, 5)])
    c.put(pen & ~c.a, R['cyan'], 'flat', base=3)
    hull = c.poly([(3, 17), (6, 19), (26, 19), (29.5, 16.5), (26.5, 22), (7.5, 22), (4.5, 20)])
    c.put(hull, R['navy'], 'ray', base=2, sep=True)
    c.put(c.rect(3, 19, 29, 19) & hull, R['gold'], 'flat', base=3)
    keel = c.poly([(6, 22), (27.5, 22), (25, 24), (9, 24)])
    c.put(keel, R['cometiron'], 'ray', base=3, sep=True)
    c.outline()
    ring = c.ring(16, 20.5, 13.9, 1.0, 5.2)
    _faint(c, ring, WARD_GLOW, 140)
    nodes = c.pts([(2, 20), (29, 20), (8, 25), (23, 25)])
    _faint(c, dilate4(nodes) & ring | nodes, R['cyan'][4], 230)
    c.glow(WARD_GLOW, (45,))
    return c


# ---------------------------------------------------------------------------- elder tokens
def _elder_token(body, cord, face):
    """An Elder's token: the sect disc with a gold rim, a gold crest mark and an elder's knot tassel."""
    c = Canvas(32)
    cx, cy, r = 16, 15.0, 9.0
    loop = c.ring(cx, 3.8, 2.3, 1.1) & (c.Y < 6)
    c.put(loop, cord, 'flat', base=2)
    disc = c.circle(cx, cy, r)
    # elder's knot and tassel below the disc
    knot = S.diamond(c, cx, 25.4, 2.9, 2.7) | c.circle(cx - 3, 25.4, 1.3) | c.circle(cx + 3, 25.4, 1.3)
    c.put(knot, cord, 'ray', base=2)
    c.put(knot & ((c.xi + c.yi) % 2 == 0) & erode4(knot), cord, 'flat', base=1)
    tas = c.poly([(cx - 1.5, 28), (cx + 1.5, 28), (cx + 3, 31), (cx - 3, 31)])
    c.put(tas, cord, 'ray', base=2, sep=True)
    c.put(c.rect(cx - 2, 27, cx + 1, 28), R['gold'], 'flat', base=3, sep=True)
    c.put(disc, body, 'ray', base=2, sep=True)
    rim = c.ring(cx, cy, r, 1.5)
    c.put(rim, R['gold'], 'ray', base=2)
    inner = erode4(erode4(disc))
    face(c, cx, cy, inner)
    # the elder's mark: a small gold crown crest where the cord meets the disc
    crest = c.from_rows(['#.##.#', '######', '.####.'], cx - 3, 5)
    c.put(crest, R['gold'], 'vgrad', base=3, sep=True)
    bead = c.circle(cx, 1.8, 1.2)
    c.put(bead, R['gold'], 'sphere', sep=True)
    c.outline()
    c.glow('#E5B84C', (45,))
    return c


def _jade_face(c, cx, cy, inner):
    hole = c.circle(cx, cy, 2.2)
    c.put(c.ring(cx, cy, 5.8, 1.2), R['jade'][4], 'flat', only_on=True, clip=inner)
    c.put(dilate4(hole) & ~hole, R['jade'][1], 'flat', only_on=True)
    c.erase(hole)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        c.put(c.circle(cx + math.cos(a) * 4.0, cy + math.sin(a) * 4.0, 0.9), R['gold'], 'flat', base=3, only_on=True)


def _cloud_face(c, cx, cy, inner):
    oy = cy - 16.5
    cl = (c.ellipse(12.5, 18 + oy, 3.2, 2.6) | c.ellipse(17, 15.5 + oy, 4, 3.6) | c.ellipse(20.5, 18.5 + oy, 3, 2.4)
          | c.rect(11, int(18 + oy), 22, int(20 + oy)))
    c.put(cl & inner, R['sky'], 'ray', base=2)
    c.put(c.arc(17, 15.5 + oy, 2.2, 1, 90, 300) & inner, R['sky'][4], 'flat', out=R['sky'].out)


def jade_elder_token():
    return _elder_token(R['jade'], R['red'], _jade_face)


def cloud_elder_token():
    return _elder_token(R['porcelain'], R['sky'], _cloud_face)


for _id, _fn in (('star_reading', star_reading), ('sky_ink', sky_ink), ('ledger_page', ledger_page),
                 ('black_ledger', black_ledger), ('star_chart_wreck', lambda: _star_chart('wreck', R['jade'])),
                 ('star_chart_lantern', lambda: _star_chart('lantern', R['gold'])),
                 ('cloud_skiff', cloud_skiff), ('storm_sloop', storm_sloop),
                 ('jade_elder_token', jade_elder_token), ('cloud_elder_token', cloud_elder_token)):
    register(FAM, _id, _fn, GROUP)
