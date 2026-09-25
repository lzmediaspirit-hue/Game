"""Beast materials: templates for feathers, scales, hides, fangs, claws, shells,
vials, pouches and shards, each with species parameters."""
import math

from pix import Canvas, Ramp, dilate4, dilate8, erode4, move, rgb
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'beast_parts'


# ============================================================================ templates
def feather(c, vane, shaft='#F4EEDC', tip=None, tip_frac=0.0, base_col=None, width=9.0,
            notches=((0.55, 1), (0.35, -1)), p0=(6, 27), p1=(13, 12), p2=(27, 4)):
    """Diagonal feather, quill at bottom-left, tip at top-right."""
    pts = S.curve_pts(p0, p1, p2, 24)
    vm = c.empty()
    n = len(pts)
    for i in range(3, n - 1):
        t = i / float(n - 1)
        hw = width / 2.0 * math.sin(math.pi * min(1.0, (t - 0.1) / 0.92) ** 0.85) if t > 0.1 else 0.0
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        vm |= c.seg(x0, y0, x1, y1, max(0.5, 2 * hw))
    # notches in the vane edges
    for (t, side) in notches:
        i = int(t * (n - 1))
        x, y = pts[i]
        dx, dy = pts[i + 1][0] - x, pts[i + 1][1] - y
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L * side, dx / L * side
        cut = c.seg(x + px * 2.2, y + py * 2.2, x + px * 6 - dx / L * 2.5, y + py * 6 - dy / L * 2.5, 1.2)
        vm &= ~cut
    c.put(vm, vane, 'ray')
    if tip is not None:
        tx, ty = pts[int((1 - tip_frac) * (n - 1))]
        tipm = vm & (((c.X - tx) * (p2[0] - p0[0]) + (c.Y - ty) * (p2[1] - p0[1])) > 0)
        c.put(tipm, tip, 'ray')
    if base_col is not None:
        bx, by = pts[int(0.3 * (n - 1))]
        bm = vm & (((c.X - bx) * (p2[0] - p0[0]) + (c.Y - by) * (p2[1] - p0[1])) < 0)
        c.put(bm, base_col, 'ray')
    # barbs
    for k in range(5, n - 4, 3):
        x, y = pts[k]
        c.put(c.bres(int(x), int(y), int(x - 3), int(y - 1)) & erode4(vm), vane[1] if isinstance(vane, Ramp) else vane,
              'flat', out=None)
    shaft_m = c.empty()
    ip = [(int(x), int(y)) for x, y in pts[:-2]]
    for a, b in zip(ip, ip[1:]):
        shaft_m |= c.bres(a[0], a[1], b[0], b[1])
    c.put(shaft_m, shaft, 'flat')
    return vm


def scale_shape(c, cx, cy, w, h, ramp, ridges=2, point=False):
    """Reptile / dragon scale: shield outline (or diamond when point=True)."""
    def shield(sx, sy, hw, hh):
        top = sy - hh
        return c.poly([(sx - hw, top + hh * 0.18), (sx - hw * 0.5, top), (sx, top + hh * 0.12), (sx + hw * 0.5, top),
                       (sx + hw, top + hh * 0.18), (sx + hw * 0.92, sy + hh * 0.35), (sx, sy + hh),
                       (sx - hw * 0.92, sy + hh * 0.35)])
    if point:
        m = S.diamond(c, cx, cy, w / 2.0, h / 2.0)
    else:
        m = shield(cx, cy, w / 2.0, h / 2.0)
    c.put(m, ramp, 'ray', sep=True)
    for k in range(1, ridges + 1):
        f = 1.0 - k * 0.3
        if point:
            r = S.outline_only(S.diamond(c, cx, cy + h * 0.1 * k, w / 2.0 * f, h / 2.0 * f)) & m
        else:
            inner = shield(cx, cy + h * 0.1 * k, w / 2.0 * f, h / 2.0 * f)
            r = S.outline_only(inner) & ~(c.Y < cy - h * 0.2 + h * 0.1 * k) & m
        c.put(r, ramp[1], 'flat', out=ramp.out)
    return m


def hide(c, ramp, bristle=None, thorns=None, pale_marks=None):
    """Stretched pelt (top view): body + four leg flaps + neck + tail."""
    body = c.ellipse(16, 16.5, 9.5, 10.5)
    legs = (c.poly([(9, 8), (3, 4), (5, 11), (9, 13)]) | c.poly([(23, 8), (29, 4), (27, 11), (23, 13)]) |
            c.poly([(8, 21), (3, 27), (7, 27), (11, 24)]) | c.poly([(24, 21), (29, 27), (25, 27), (21, 24)]))
    neck = c.poly([(12, 7), (13, 2), (19, 2), (20, 7)])
    tail = c.poly([(15, 26), (16, 30), (17, 26)])
    m = body | legs | neck | tail
    c.put(m, ramp, 'ray')
    # fur tufts
    for (x, y) in ((11, 13), (19, 12), (14, 19), (21, 19), (10, 20), (17, 24)):
        c.put(c.bres(x, y, x + 2, y - 1), ramp[1], 'flat', only_on=True)
        c.put(c.bres(x, y - 1, x + 1, y - 1), ramp[3], 'flat', only_on=True)
    if bristle is not None:
        sp = c.rect(15, 4, 16, 24) & m
        c.put(sp, bristle, 'flat', base=1, only_on=True)
        for y in range(5, 24, 3):
            c.put(c.rect(14, y, 17, y), bristle, 'flat', base=0, only_on=True)
    if pale_marks is not None:
        for (x, y, r) in pale_marks:
            c.put(c.ellipse(x, y, r, r * 0.6) & erode4(m), ramp, 'flat', base=4)
    if thorns is not None:
        spots = [(8, 15), (7, 19), (24, 15), (25, 19), (12, 26), (20, 26), (16, 10), (12, 13), (20, 13)]
        for (x, y) in spots:
            th = c.poly([(x - 1.2, y + 1), (x + 0.5, y - 3), (x + 1.4, y + 1)])
            c.put(th, thorns, 'ray', base=3, sep=True)
    return m


def fang(c, p0, p1, p2, w0, ramp, root_col=None):
    m = S.taper_curve(c, p0, p1, p2, w0, 0.8)
    c.put(m, ramp, 'ray', base=3)
    if root_col is not None:
        rm = c.circle(p0[0], p0[1], w0 * 0.55) & m
        c.put(rm, root_col, 'ray', base=2)
    return m


def vial(c, liquid, glass=None, cork=None, shape='round', level=0.55, x=16):
    glass = glass or R['mist']
    cork = cork or R['wood']
    if shape == 'round':
        body = c.circle(x, 21, 8.5)
        neck = c.rect(x - 3, 7, x + 2, 14)
    else:
        body = S.rounded_rect(c, x - 6, 11, x + 5, 29, 2)
        neck = c.rect(x - 3, 6, x + 2, 11)
    lip = c.rect(x - 4, 7, x + 3, 8)
    c.put(body | neck, glass, 'ray', base=2)
    ys = [y for y in range(32) if body[y].any()]
    top = min(ys) + (max(ys) - min(ys)) * (1 - level)
    liq = erode4(body) & (c.Y > top)
    c.put(liq, liquid, 'ray', base=2)
    c.put(liq & ~move(liq, 0, 1), liquid, 'flat', base=4)  # surface line
    # glass glints
    hx = x - 5 if shape == 'round' else x - 4
    c.put(c.rect(hx, 17 if shape == 'round' else 13, hx, 21 if shape == 'round' else 18), '#F4FBFB', 'flat')
    c.put(c.rect(hx + 1, 15 if shape == 'round' else 12, hx + 1, 15 if shape == 'round' else 12), '#F4FBFB', 'flat')
    c.put(lip, glass, 'flat', base=3, sep=True)
    ck = c.rect(x - 2, 3, x + 1, 6)
    c.put(ck, cork, 'ray', sep=True)
    return body


def pouch(c, bag, dust, glints=None):
    body = c.ellipse(14, 21, 10, 8.5) | c.poly([(9, 15), (11, 11), (17, 11), (19, 15)])
    c.put(body, bag, 'ray')
    c.put(S.bez_line(c, (8, 19), (10, 24), (13, 27)) & erode4(body), bag[1], 'flat', out=bag.out)
    c.put(S.bez_line(c, (19, 16), (21, 19), (22, 23)) & erode4(body), bag[1], 'flat', out=bag.out)
    frill = c.poly([(8, 11), (9, 6), (12, 8), (14, 5), (16, 8), (19, 6), (20, 11)])
    c.put(frill, bag, 'ray', base=3, sep=True)
    c.put(c.ellipse(14, 8.5, 3.5, 1.5) & frill, dust, 'ray', base=2)
    tie = c.rect(9, 11, 19, 12)
    c.put(tie, R['straw'], 'ray', sep=True)
    cord = S.bez_line(c, (19, 12), (23, 12), (22, 16))
    c.put(cord, R['straw'], 'flat', base=3)
    # spill heap in front
    heap = (c.ellipse(24, 27.5, 6.5, 3.5) | c.ellipse(21, 28.5, 5, 2.2)) & (c.Y < 30)
    c.put(heap, dust, 'ray', sep=True)
    if glints:
        c.pxs(glints, dust[4])
    return body


def shard(c, pts, ramp, facet=None):
    m = c.poly(pts)
    c.put(m, ramp, 'ray', sep=True)
    if facet:
        c.put(c.poly(facet) & m, ramp, 'flat', base=3)
    return m


# ============================================================================ icons
def ore_dust():
    c = Canvas(32)
    pouch(c, R['hemp'], R['warmstone'], glints=[(22, 26), (26, 27), (13, 8)])
    c.pxs([(21, 27), (25, 26)], R['copper'][3])
    c.outline()
    return c


def mirror_dust():
    c = Canvas(32)
    pouch(c, R['indigo'], R['silver'], glints=[(22, 26), (26, 27), (13, 8), (15, 8)])
    S.sparkle(c, 27, 21, '#FFFFFF', R['silver'][3], 2)
    S.sparkle(c, 5, 7, '#FFFFFF', R['silver'][3], 1)
    c.outline()
    return c


def crab_shell():
    c = Canvas(32)
    ramp = R['red']
    shell = c.ellipse(16, 18, 13, 9) & (c.Y > 10)
    shell |= c.ellipse(16, 13, 12, 5)
    for x in (4, 7, 25, 28):
        shell |= c.poly([(x - 1.5, 14), (x - 3 if x < 16 else x + 3, 10.5), (x + 1.5, 13)])
    c.put(shell, R['flesh'], 'ray')
    c.put(c.ellipse(16, 16, 8, 5), R['flesh'], 'ray', base=3)
    # carapace grooves
    for pts in ([(10, 13), (13, 17), (12, 23)], [(22, 13), (19, 17), (20, 23)], [(13, 17), (19, 17)]):
        c.put(c.bres_path(pts) & erode4(shell), R['flesh'][1], 'flat', only_on=True)
    for (x, y) in ((9, 20), (23, 20), (16, 22), (12, 12), (20, 12)):
        c.put(c.circle(x, y, 1.2), R['flesh'][4], 'flat', only_on=True)
    # eyes on stalks
    for x in (12, 20):
        c.put(c.rect(x, 5, x + 1, 8), R['flesh'], 'flat', base=2, sep=True)
        c.put(c.circle(x + 1, 5, 1.6), R['ink'], 'flat', base=3, sep=True)
    del ramp
    c.outline()
    return c


def beetle_shell():
    c = Canvas(32)
    ramp = Ramp(['#101B26', '#1B3440', '#2A5A5E', '#4E9A8A', '#B8F0D2'], '#050A0E')
    left = c.ellipse(12, 17, 7.5, 12.5) & (c.X < 16)
    right = c.ellipse(20, 17, 7.5, 12.5) & (c.X >= 16)
    pron = c.ellipse(16, 6.5, 6.5, 3.5)
    c.put(pron, ramp, 'sphere', base=2)
    c.put(left, ramp, 'sphere', base=2, sep=True, cx=12, cy=15, rx=8, ry=13)
    c.put(right, ramp, 'sphere', base=2, sep=True, cx=19, cy=15, rx=8, ry=13)
    c.put(c.rect(15, 6, 16, 29) & (left | right), ramp[0], 'flat')
    # iridescent sheen streaks
    c.put(S.bez_line(c, (9, 9), (7, 16), (9, 24)) & left, R['violet'][3], 'flat', out=ramp.out)
    c.put(S.bez_line(c, (19, 10), (18, 16), (19, 22)) & right, ramp[4], 'flat', out=ramp.out)
    c.outline()
    return c


def tortoise_plate():
    c = Canvas(32)
    ramp = R['earth']
    dome = c.ellipse(16, 18, 13.5, 11)
    c.put(dome, ramp, 'sphere', base=2)
    rim = c.ring(16, 18, 13.5, 1.6, 11)
    c.put(rim, R['warmstone'], 'flat', base=2)
    # hex scutes
    hexes = [(16, 12), (10, 16), (22, 16), (16, 20), (10, 23), (22, 23)]
    for (x, y) in hexes:
        h = c.poly([(x - 2.5, y - 3), (x + 2.5, y - 3), (x + 4, y), (x + 2.5, y + 3), (x - 2.5, y + 3), (x - 4, y)])
        c.put(S.outline_only(h) & erode4(dome), ramp[0], 'flat', out=ramp.out)
        c.put(c.rect(x - 1, y - 1, x, y - 1) & erode4(dome), ramp[3], 'flat', out=ramp.out)
    c.outline()
    return c


def tide_shell():
    c = Canvas(32)
    ramp = Ramp(['#2B4A58', '#4C7E8C', '#8CC3C6', '#D2EEE6', '#FFFFFF'], '#0F1E24')
    fan = c.sector(16, 25, 14, 22, 158) | c.ellipse(16, 25, 5, 3)
    fan &= c.ellipse(16, 22, 15, 14)
    c.put(fan, ramp, 'ray', base=2)
    for a in range(30, 160, 16):
        r = math.radians(a)
        c.put(c.bres(16, 24, int(16 + math.cos(r) * 13), int(24 - math.sin(r) * 12)) & erode4(fan), ramp[1], 'flat',
              out=ramp.out)
    for a in range(38, 160, 16):
        r = math.radians(a)
        c.put(c.bres(15, 22, int(15 + math.cos(r) * 11), int(22 - math.sin(r) * 10)) & erode4(fan), ramp[3],
              'flat', out=ramp.out)
    hinge = c.poly([(10, 27), (22, 27), (20, 30), (12, 30)])
    c.put(hinge, R['lotuspink'], 'ray', base=2, sep=True)
    c.outline()
    return c


def pearl():
    c = Canvas(32)
    # half shell cradle
    cup = c.ellipse(16, 22, 13, 7) & (c.Y > 21)
    c.put(cup, Ramp(['#3E4A5C', '#6A7A92', '#A9B5C8', '#D8E0EC', '#FFFFFF'], '#141A24'), 'ray')
    inner = c.ellipse(16, 22, 11, 4.5)
    c.put(inner, R['lotuspink'], 'ray', base=3)
    p = c.circle(16, 17, 7.5)
    c.put(p, R['pearl'], 'sphere', base=2, sep=True)
    c.put(c.ellipse(13.5, 14, 2, 1.4), '#FFFFFF', 'flat')
    c.put(c.arc(16, 17, 6.5, 1, 290, 340), R['lotuspink'][3], 'flat', only_on=True)
    c.outline()
    S.sparkle(c, 26, 8, '#FFFFFF', R['pearl'][3], 2)
    return c


def _scale(kind):
    c = Canvas(32)
    if kind == 'jade':
        scale_shape(c, 16, 16, 24, 26, R['jade'], ridges=2)
        c.put(c.rect(8, 9, 9, 13) | c.rect(10, 8, 11, 8), R['jade'][4], 'flat', only_on=True)
        c.outline()
        c.glow('#67D6BD', (80,))
    elif kind == 'lizard':
        ramp = Ramp(['#2A2A14', '#4A4A22', '#7A7436', '#AEA35A', '#DCD39A'], '#12120A')
        scale_shape(c, 10, 11, 14, 16, ramp, ridges=1)
        scale_shape(c, 22, 11, 14, 16, ramp, ridges=1)
        scale_shape(c, 16, 19, 18, 20, ramp, ridges=2)
        c.put(c.rect(9, 12, 10, 14), ramp[4], 'flat', only_on=True)
        c.outline()
    else:
        ramp = Ramp(['#0E2418', '#1A4029', '#2E6A42', '#5BA06A', '#A8D6A0'], '#06120A')
        scale_shape(c, 16, 16, 22, 28, ramp, ridges=2, point=True)
        c.put(S.diamond(c, 16, 16, 3, 5) & erode4(c.a), R['violet'], 'flat', base=3)
        c.put(c.bres(11, 12, 15, 5), ramp[4], 'flat', only_on=True)
        c.outline()
    return c


def _feather(kind):
    c = Canvas(32)
    if kind == 'vulture':
        feather(c, R['fur'], shaft='#E8DCC0', tip=R['bone'], tip_frac=0.22, width=10)
    elif kind == 'cloud':
        feather(c, R['cloud'], shaft='#FFFFFF', tip=R['sky'], tip_frac=0.12, width=11,
                notches=((0.6, 1), (0.45, -1), (0.3, 1)))
    elif kind == 'storm':
        feather(c, R['storm'], shaft='#E0F2FF', tip=R['navy'], tip_frac=0.25, width=10)
        bolt = c.bres_path([(20, 13), (16, 17), (20, 17), (15, 22)])
        c.put(dilate4(bolt) & c.a & ~bolt, R['navy'][1], 'flat', only_on=True)
        c.put(bolt, R['yellow'], 'flat', base=3)
    else:  # roc
        feather(c, R['broth'], shaft='#FFF1C8', tip=R['ember'], tip_frac=0.3, width=12,
                p0=(5, 28), p1=(12, 12), p2=(28, 3))
        eye = c.ellipse(20, 10, 3.2, 2.6) & c.a
        c.put(eye, R['navy'], 'flat', base=2)
        c.put(c.ellipse(20, 10, 1.6, 1.3) & eye, R['gold'], 'flat', base=3)
    c.outline()
    return c


def _hide(kind):
    c = Canvas(32)
    if kind == 'boar':
        hide(c, R['fur'], bristle=R['darkwood'])
    elif kind == 'thorn':
        hide(c, R['toad'], thorns=R['bone'])
    elif kind == 'grey':
        hide(c, R['greyfur'], pale_marks=((12, 15, 2.5), (20, 20, 2)))
        scar = c.bres_path([(18, 11), (22, 15)])
        c.put(scar, R['greyfur'][0], 'flat', only_on=True)
    else:  # mist pelt
        hide(c, Ramp(['#3A5664', '#61838F', '#9CBBC4', '#D2E6EA', '#F8FFFF'], '#15242B'),
             pale_marks=((13, 14, 2.5), (19, 19, 2.5), (14, 22, 1.8)))
        for (x0, y0) in ((2, 16), (24, 25)):
            w = S.wave_line(c, x0, x0 + 6, y0, 1, 6)
            c.put(w, R['mist'], 'flat', base=4)
    c.outline()
    return c


def ape_fur():
    c = Canvas(32)
    ramp = Ramp(['#2A1A12', '#4A2E1E', '#6E4A30', '#9A7048', '#C69E70'], '#120A06')
    ends = [(5, 27), (8, 30), (12, 28), (16, 30.5), (20, 28), (24, 30), (27, 26)]
    m = c.ellipse(16, 13, 7, 6)
    for (ex, ey) in ends:
        sx = 16 + (ex - 16) * 0.4
        m |= S.taper_curve(c, (sx, 12), (sx + (ex - sx) * 0.3 + 1, 20), (ex, ey), 4.0, 1.4)
    tuft = S.taper_curve(c, (16, 9), (13, 4), (9, 3), 4, 1.2) | S.taper_curve(c, (17, 9), (20, 4), (24, 3.5), 3.5, 1.2)
    c.put(m | tuft, ramp, 'ray')
    for (ex, ey) in ends[1:-1]:
        c.put(S.bez_line(c, (16 + (ex - 16) * 0.3, 15), (16 + (ex - 16) * 0.55, 21), (ex, ey - 1.5)) & erode4(m),
              ramp[1], 'flat', out=ramp.out)
    for (ex, ey) in ends[:3]:
        c.put(S.bez_line(c, (14 + (ex - 16) * 0.2, 13), (13 + (ex - 16) * 0.4, 19), (ex + 1, ey - 4)) & erode4(m),
              ramp[3], 'flat', out=ramp.out)
    band = c.ellipse(16, 11, 6.5, 2.2)
    c.put(band, R['red'], 'ray', sep=True)
    c.outline()
    return c


def _fang(kind):
    c = Canvas(32)
    if kind == 'viper':
        fang(c, (9, 6), (24, 8), (22, 26), 5.5, R['bone'], root_col=R['flesh'])
        d = S.drop(c, 20.5, 28.5, 1.8, 4.5)
        c.put(d, R['venom'], 'ray', base=3, sep=True)
        fang(c, (6, 10), (15, 12), (14, 22), 3.2, R['bone'])
    else:
        cord = S.bez_line(c, (3, 6), (16, 16), (29, 6), 1.3)
        c.put(cord, R['leather'], 'flat', base=3)
        fang(c, (16, 12), (18, 20), (14, 29), 7.0, R['bone'])
        c.put(c.ellipse(16, 12, 3.8, 2.2), R['leather'], 'ray', sep=True)
        fang(c, (8, 10), (10, 15), (8, 19), 3.4, R['bone'])
        fang(c, (24, 10), (25, 15), (23, 19), 3.4, R['bone'])
    c.outline()
    return c


def mole_claw():
    c = Canvas(32)
    paw = c.ellipse(11, 19, 8, 7)
    arm = c.poly([(2, 24), (5, 16), (10, 18), (8, 28)])
    c.put(arm | paw, R['fur'], 'ray')
    c.put(c.ellipse(11, 20, 5, 4) & paw, R['flesh'], 'ray', base=3)
    for (y, L) in ((12.5, 12), (18, 14), (23.5, 12)):
        cl = S.taper_curve(c, (16, y), (22 + L * 0.3, y - 3), (16 + L, y + 3), 4.6, 1.0)
        c.put(cl, R['bone'], 'ray', base=3, sep=True)
    c.outline()
    return c


def snapper_claw():
    c = Canvas(32)
    ramp = Ramp(['#122A2A', '#1E4644', '#326E62', '#5EA08A', '#A8D8C0'], '#081414')
    wrist = c.poly([(3, 29), (4, 22), (10, 19), (13, 24), (8, 30)])
    c.put(wrist, ramp, 'ray')
    palm = c.ellipse(15, 17, 8, 7)
    c.put(palm, ramp, 'sphere', sep=True)
    upper = S.taper_curve(c, (17, 12), (24, 3), (29, 10), 6.0, 1.4)
    lower = S.taper_curve(c, (20, 19), (27, 19), (29, 14), 5.0, 1.2)
    c.put(upper, ramp, 'ray', base=2, sep=True)
    c.put(lower, ramp, 'ray', base=1, sep=True)
    for (x, y) in ((24, 7), (26, 9), (25, 17)):
        c.put(c.rect(x, y, x, y), R['bone'][3], 'flat', only_on=True)
    for (x, y) in ((12, 14), (15, 19), (10, 25)):
        c.put(c.circle(x, y, 1.1), ramp[4], 'flat', only_on=True)
    c.outline()
    return c


def rat_tail():
    c = Canvas(32)
    ramp = R['pink']
    t = S.taper_curve(c, (8, 25), (28, 31), (25, 13), 5.4, 2.4)
    t |= S.taper_curve(c, (25, 13), (22, 2), (11, 8), 2.6, 1.0)
    c.put(t, ramp, 'ray', base=2)
    for k in range(6):
        x = 9 + k * 3
        c.put(c.bres(x, 22, x - 1, 28) & erode4(t), ramp[1], 'flat', out=ramp.out)
    stump = c.ellipse(6.5, 24.5, 3.5, 3.8)
    c.put(stump, R['greyfur'], 'ray', sep=True)
    c.outline()
    return c


def tough_meat():
    c = Canvas(32)
    slab = c.poly([(4, 16), (8, 9), (17, 6), (26, 8), (29, 15), (26, 24), (15, 27), (6, 24)])
    c.put(slab, R['flesh'], 'ray')
    top = c.poly([(8, 10), (17, 7), (25, 9), (21, 14), (11, 15)])
    c.put(top, R['flesh'], 'flat', base=3)
    fat = S.bez_line(c, (6, 18), (15, 13), (26, 17), 1.6) | S.bez_line(c, (10, 22), (17, 19), (23, 22), 1.2)
    c.put(fat & erode4(slab), R['bone'], 'flat', base=3)
    rind = c.poly([(6, 24), (15, 27), (26, 24), (26, 26), (15, 29), (6, 26)])
    c.put(rind, R['bone'], 'ray', base=2, sep=True)
    c.outline()
    return c


def frog_leg():
    c = Canvas(32)
    ramp = R['toad']
    web = c.poly([(23, 21), (16.5, 29.5), (23.5, 31), (30, 26.5)])
    c.put(web, ramp, 'ray', base=2)
    for a in (238, 275, 312):
        toe = S.leaf(c, 23, 21, a, 10, 2.4, 0)
        c.put(toe, ramp, 'ray', base=3, sep=True, sep_col=ramp[0])
    shin = S.taper_curve(c, (14, 14), (23, 12), (23, 21), 5.6, 3.6)
    c.put(shin, ramp, 'ray', base=2, sep=True)
    thigh = c.ellipse(11, 11, 8, 6)
    c.put(thigh, ramp, 'ray', base=2, sep=True)
    c.put(c.ellipse(10, 13.5, 5, 2.2) & thigh, R['flesh'], 'flat', base=4)
    for (x, y) in ((8, 8), (13, 7), (21, 15), (15, 10)):
        c.put(c.circle(x, y, 1), ramp[1], 'flat', only_on=True)
    bone = c.seg(4, 6.5, 6, 8.5, 2.4) | c.circle(3.2, 6.8, 1.6) | c.circle(4.4, 5.2, 1.6)
    c.put(bone, R['bone'], 'ray', base=3, sep=True)
    c.outline()
    return c


def toad_oil():
    c = Canvas(32)
    vial(c, R['oil'], shape='round', level=0.6)
    c.put(c.ellipse(17, 22, 3, 2) & c.a, R['toad'], 'flat', base=3)
    c.outline()
    return c


def leech_oil():
    c = Canvas(32)
    vial(c, Ramp(['#2A0E14', '#4E1622', '#7A2432', '#A84A4A', '#D48A7A'], '#12050A'), shape='tall', level=0.7)
    c.outline()
    return c


def venom_sac():
    c = Canvas(32)
    sac = c.ellipse(15, 19, 10.5, 9.5) | c.ellipse(19, 11, 5, 4)
    c.put(sac, R['plum'], 'sphere', base=2, cx=15, cy=18, rx=12, ry=11)
    inner = c.ellipse(14, 21, 6.5, 5.5)
    c.put(inner, R['venom'], 'sphere', base=3)
    for pts in ([(8, 14), (10, 19), (8, 24)], [(22, 16), (20, 21), (22, 25)], [(17, 11), (15, 15)]):
        c.put(c.bres_path(pts) & erode4(sac) & ~inner, R['plum'][4], 'flat', out=R['plum'].out)
    duct = S.taper_curve(c, (21, 9), (24, 4), (28, 5), 3.6, 2.4)
    c.put(duct, R['pink'], 'ray', base=2, sep=True)
    c.put(c.ellipse(10.5, 13.5, 2.2, 1.6), R['plum'][4], 'flat', only_on=True)
    d = S.drop(c, 23.5, 28, 1.8, 4.5)
    c.put(d, R['venom'], 'ray', base=3, sep=True)
    c.outline()
    return c


def moss_item():
    c = Canvas(32)
    ramp = R['moss']
    stone = c.ellipse(16, 23, 13, 6.5)
    c.put(stone, R['stone'], 'ray')
    blob = c.ellipse(10, 17, 6, 5) | c.ellipse(18, 14, 7, 6.5) | c.ellipse(24, 19, 5.5, 4.5) | c.ellipse(15, 20, 10, 4)
    c.put(blob, ramp, 'ray', sep=True)
    for (x, y) in ((10, 14), (17, 10), (23, 16), (13, 18), (20, 17)):
        c.put(c.rect(x, y, x + 1, y), ramp[4], 'flat', only_on=True)
    for (x, y) in ((12, 19), (21, 21), (8, 20)):
        c.put(c.rect(x, y, x + 1, y), ramp[1], 'flat', only_on=True)
    # spore stalks
    for (x, h) in ((14, 6), (20, 5), (25, 4)):
        c.put(c.rect(x, 12 - h + 4, x, 12), ramp[3], 'flat', out=ramp.out)
        c.put(c.rect(x, 12 - h + 3, x, 12 - h + 3), R['straw'][3], 'flat', out=ramp.out)
    c.outline()
    return c


def bamboo_shoot():
    c = Canvas(32)
    sheath = R['sand']
    body = c.poly([(8, 28), (9, 20), (12, 12), (16, 3), (20, 12), (23, 20), (24, 28)])
    c.put(body, sheath, 'ray')
    # overlapping sheath edges (chevrons), alternating sides
    for k, y in enumerate((24, 19, 14, 9)):
        if k % 2 == 0:
            edge = c.bres(7, y + 5, 23 - k, y - 1)
        else:
            edge = c.bres(25, y + 5, 9 + k, y - 1)
        c.put(edge & body, sheath[0], 'flat', out=sheath.out)
        c.put(move(edge, 0, 1) & body, sheath[3], 'flat', out=sheath.out)
    for (x, y) in ((12, 22), (19, 17), (14, 13), (18, 25), (11, 26)):
        c.put(c.rect(x, y, x + 1, y), sheath[1], 'flat', only_on=True)
    tip = c.poly([(13, 9), (16, 1), (19, 9), (16, 7)])
    c.put(tip, R['bamboo'], 'ray', base=3, sep=True)
    c.put(c.poly([(11, 12), (9, 6), (14, 10)]), R['bamboo'], 'ray', base=2, sep=True)
    base = c.ellipse(16, 28.5, 9, 2)
    c.put(base, R['earth'], 'ray', sep=True)
    c.outline()
    return c


def soul_wax():
    c = Canvas(32)
    lump = c.ellipse(16, 22, 11, 6.5) | c.ellipse(13, 17, 6, 4.5) | c.ellipse(20, 18, 5, 4)
    c.put(lump, R['wax'], 'ray')
    drips = c.rect(8, 24, 9, 27) | c.rect(22, 25, 23, 28) | c.rect(15, 26, 16, 28)
    c.put(drips, R['wax'], 'ray', base=2)
    c.put(c.ellipse(12, 16, 2.4, 1.4), R['wax'][4], 'flat', only_on=True)
    wisp = S.flame(c, 17, 13, 5, 10, -1.0)
    c.put(wisp, R['violet'], 'vgrad', base=3, bands=((0.35, 1), (0.7, 0), (9, -1)), sep=True)
    c.put(c.ellipse(17, 10, 1, 1.6), '#FFFFFF', 'flat')
    c.outline()
    c.glow('#9B78D1', (70,))
    return c


def hollow_antler():
    c = Canvas(32)
    ramp = R['hollow']
    main = S.taper_curve(c, (7, 28), (5, 13), (21, 3), 5.2, 2.0)
    t1 = S.taper_curve(c, (7, 20), (13, 16), (15, 10), 3.8, 1.6)
    t3 = S.taper_curve(c, (12, 8), (22, 12), (28, 9), 3.6, 1.6)
    t4 = S.taper_curve(c, (7, 25), (15, 26), (20, 21), 3.6, 1.6)
    t2 = S.taper_curve(c, (17, 18), (22, 18), (25, 15), 2.6, 1.4) & c.empty()
    m = main | t1 | t2 | t3 | t4
    c.put(m, ramp, 'ray', base=3)
    burr = c.ellipse(7.5, 27.5, 3.5, 2)
    c.put(burr, ramp, 'ray', base=1, sep=True)
    for (x, y) in ((6, 22), (7, 15), (12, 8)):
        c.put(c.rect(x, y, x, y + 1), ramp[1], 'flat', only_on=True)
    c.outline()
    return c


def _hollow_shard(big):
    c = Canvas(32)
    ramp = R['hollow']
    if big:
        shard(c, [(8, 28), (6, 17), (11, 5), (16, 2), (18, 12), (15, 22), (13, 29)], ramp,
              facet=[(7, 17), (11, 6), (15, 4), (13, 16)])
        shard(c, [(15, 28), (18, 15), (24, 8), (27, 16), (22, 28)], ramp, facet=[(18, 16), (24, 9), (23, 18)])
        c.put(c.ellipse(20.5, 20, 1.4, 2) & c.a, '#FFFFFF', 'flat')
        c.put(c.ellipse(12, 14, 1.2, 1.8) & c.a, '#FFFFFF', 'flat')
    else:
        shard(c, [(11, 26), (10, 17), (15, 9), (21, 13), (20, 23), (15, 28)], ramp,
              facet=[(11, 17), (15, 10), (18, 14), (14, 19)])
        c.put(c.ellipse(16, 19, 1.3, 1.8) & c.a, '#FFFFFF', 'flat')
    c.outline()
    c.glow('#EEF3F2', (70,) if not big else (90, 40))
    return c


# ============================================================================ Azure Expanse (Act II)
def spark_pelt():
    c = Canvas(32)
    hide(c, R['yellow'], pale_marks=((12, 15, 2.2), (19, 20, 2)))
    stripe = c.bres_path([(6, 12), (14, 10), (22, 12), (27, 16)])
    c.put(stripe, R['navy'], 'flat', base=2, only_on=True)
    c.outline()
    S.sparkle(c, 25, 7, '#FFFFFF', R['cyan'][3], 2)
    return c


def thunder_horn():
    c = Canvas(32)
    fang(c, (8, 27), (14, 12), (24, 4), 8.0, R['bone'], root_col=R['storm'])
    arc = c.bres_path([(20, 8), (23, 12), (21, 14), (25, 18)])
    c.put(arc, R['cyan'], 'flat', base=4)
    c.outline()
    c.glow('#7FD4FF', (60,))
    return c


def storm_shard():
    c = Canvas(32)
    shard(c, [(11, 28), (8, 17), (13, 6), (18, 3), (22, 13), (19, 24), (15, 29)], R['storm'],
          facet=[(9, 17), (13, 7), (17, 5), (15, 17)])
    bolt = c.bres_path([(16, 8), (13, 15), (18, 16), (14, 24)])
    c.put(bolt & c.a, '#F4FBFF', 'flat')
    c.outline()
    c.glow('#7FD4FF', (90, 40))
    return c


register(FAM, 'spark_pelt', spark_pelt, GROUP)
register(FAM, 'thunder_horn', thunder_horn, GROUP)
register(FAM, 'storm_shard', storm_shard, GROUP)
register(FAM, 'ore_dust', ore_dust, GROUP)
register(FAM, 'crab_shell', crab_shell, GROUP)
register(FAM, 'rat_tail', rat_tail, GROUP)
register(FAM, 'boar_hide', lambda: _hide('boar'), GROUP)
register(FAM, 'tough_meat', tough_meat, GROUP)
register(FAM, 'toad_oil', toad_oil, GROUP)
register(FAM, 'moss', moss_item, GROUP)
register(FAM, 'beetle_shell', beetle_shell, GROUP)
register(FAM, 'tortoise_plate', tortoise_plate, GROUP)
register(FAM, 'mole_claw', mole_claw, GROUP)
register(FAM, 'frog_leg', frog_leg, GROUP)
register(FAM, 'leech_oil', leech_oil, GROUP)
register(FAM, 'bamboo_shoot', bamboo_shoot, GROUP)
register(FAM, 'viper_fang', lambda: _fang('viper'), GROUP)
register(FAM, 'venom_sac', venom_sac, GROUP)
register(FAM, 'thorn_hide', lambda: _hide('thorn'), GROUP)
register(FAM, 'hound_fang', lambda: _fang('hound'), GROUP)
register(FAM, 'jade_scale', lambda: _scale('jade'), GROUP)
register(FAM, 'tide_shell', tide_shell, GROUP)
register(FAM, 'pearl', pearl, GROUP)
register(FAM, 'lizard_scale', lambda: _scale('lizard'), GROUP)
register(FAM, 'serpent_scale', lambda: _scale('serpent'), GROUP)
register(FAM, 'vulture_plume', lambda: _feather('vulture'), GROUP)
register(FAM, 'cloud_feather', lambda: _feather('cloud'), GROUP)
register(FAM, 'storm_feather', lambda: _feather('storm'), GROUP)
register(FAM, 'ape_fur', ape_fur, GROUP)
register(FAM, 'mist_pelt', lambda: _hide('mist'), GROUP)
register(FAM, 'mirror_dust', mirror_dust, GROUP)
register(FAM, 'soul_wax', soul_wax, GROUP)
register(FAM, 'hollow_antler', hollow_antler, GROUP)
register(FAM, 'roc_feather', lambda: _feather('roc'), GROUP)
register(FAM, 'snapper_claw', snapper_claw, GROUP)
register(FAM, 'tiny_hollow_shard', lambda: _hollow_shard(False), GROUP)
register(FAM, 'hollow_shard', lambda: _hollow_shard(True), GROUP)
register(FAM, 'grey_hide', lambda: _hide('grey'), GROUP)


# ----------------------------------------------------------------------------- Act II · Rimefrost and Mirrorwater
ICE_RAMP = Ramp(['#2C4C6E', '#4A78A2', '#7FB0D6', '#B8DCF2', '#E8F7FF'], '#10202E')
SNOWFUR = Ramp(['#6E7F96', '#9AAABE', '#C6D2DE', '#E6EDF3', '#FFFFFF'], '#222C38')
AZURE = Ramp(['#123A5E', '#1E6190', '#3A93C4', '#7CC8E8', '#D2F2FF'], '#061828')


def rime_fang():
    c = Canvas(32)
    fang(c, (8, 27), (14, 12), (24, 4), 8.0, ICE_RAMP, root_col=R['bone'])
    for (x, y) in ((20, 10), (16, 16), (12, 22)):
        c.put(c.rect(x, y, x, y), '#FFFFFF', 'flat')
    c.outline()
    c.glow('#9FD8FF', (60,))
    return c


def snow_ape_hide():
    c = Canvas(32)
    hide(c, SNOWFUR, bristle=R['mist'], pale_marks=((12, 15, 2.5), (20, 19, 2.2)))
    for (x, y) in ((10, 11), (22, 13), (15, 22)):
        c.put(c.rect(x, y, x + 1, y), ICE_RAMP[3], 'flat', only_on=True)
    c.outline()
    return c


def dragonet_scale():
    c = Canvas(32)
    scale_shape(c, 10, 11, 14, 16, AZURE, ridges=1)
    scale_shape(c, 22, 11, 14, 16, AZURE, ridges=1)
    scale_shape(c, 16, 19, 18, 20, AZURE, ridges=2)
    c.put(c.rect(15, 14, 17, 14), R['gold'][4], 'flat')
    c.outline()
    c.glow('#7CC8E8', (50,))
    return c


def mirror_eye():
    c = Canvas(32)
    ball = c.ellipse(16, 16, 11, 11)
    c.put(ball, Ramp(['#6C6A8E', '#A5A6C4', '#D6D8EA', '#F1F2FA', '#FFFFFF'], '#1E1C30'), 'sphere', base=2, cx=12, cy=12, rx=14, ry=14)
    iris = c.ellipse(17, 16, 5.5, 5.5)
    c.put(iris, Ramp(['#2B1B52', '#46307E', '#7556AB', '#A687E0', '#D6C4FF'], '#10081E'), 'ray', base=2)
    c.put(c.ellipse(17, 16, 2.2, 3.4), '#07060E', 'flat')
    c.put(c.ellipse(12, 11, 2.4, 1.6), '#FFFFFF', 'flat')
    c.outline()
    c.glow('#B18DE2', (110, 45))
    return c


register(FAM, 'rime_fang', rime_fang, GROUP)
register(FAM, 'snow_ape_hide', snow_ape_hide, GROUP)
register(FAM, 'dragonet_scale', dragonet_scale, GROUP)
register(FAM, 'mirror_eye', mirror_eye, GROUP)


def harpy_plume():
    c = Canvas(32)
    feather(c, R['broth'], shaft='#F4E4C8', tip=R['darkwood'], tip_frac=0.2, width=11,
            notches=((0.6, 1), (0.42, -1), (0.28, 1)), p0=(5, 28), p1=(12, 12), p2=(28, 3))
    for k in range(4):
        t = 0.35 + k * 0.14
        x, y = 5 + (28 - 5) * t, 28 + (3 - 28) * t
        c.put(c.seg(x - 3, y + 2, x + 3, y - 2, 1.0) & c.a, R['darkwood'][1], 'flat', only_on=True)
    c.outline()
    return c


def kite_silk():
    c = Canvas(32)
    silk = c.poly([(6, 8), (26, 5), (24, 22), (8, 26)])
    c.put(silk, R['red'], 'ray', base=2, sep=True)
    for (x0, y0, x1, y1) in ((6, 8, 24, 22), (26, 5, 8, 26)):
        c.put(c.seg(x0, y0, x1, y1, 1.0) & silk, R['bamboo'][3], 'flat')
    cl = c.ellipse(13, 15, 3, 2) | c.ellipse(17, 13, 3.5, 2.6) | c.ellipse(20, 15.5, 2.5, 1.8)
    c.put(cl & silk, R['ink'], 'flat', base=1)
    c.put(c.bres_path([(8, 26), (5, 29), (9, 30)]), R['gold'][4], 'flat')
    c.outline()
    return c


register(FAM, 'harpy_plume', harpy_plume, GROUP)
register(FAM, 'kite_silk', kite_silk, GROUP)


# ----------------------------------------------------------------------------- Act II · Sunscar Desert
SANDGOLD = Ramp(['#4A3216', '#84602A', '#C39A4E', '#E6C77E', '#FFF1C2'], '#1F1407')
VENOM_AMBER = Ramp(['#6A300A', '#B25E12', '#EE9A26', '#FFC957', '#FFF3B0'], '#2A1204')
DESERT_GLASS = Ramp(['#35606E', '#5E98A8', '#9ED4DC', '#D8F4F2', '#FFFFFF'], '#10262E')


def halo(c, mask, col, alphas=(110, 50)):
    """Stepped glow bands around one part only (call after c.outline())."""
    cur = dilate4(mask) & (c.alpha > 0)
    for al in alphas:
        ring = dilate8(cur) & ~cur
        free = ring & (c.alpha == 0)
        c.rgb[free] = rgb(col)
        c.alpha[free] = al
        cur |= ring


def _barrel(c, pts, w_joint, w_max):
    """Articulated segment along a point run: narrow at both joints, bulging in the middle."""
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L, dx / L
        hw = (w_joint + (w_max - w_joint) * math.sin(math.pi * i / (n - 1.0)) ** 0.6) / 2.0
        left.append((x + px * hw, y + py * hw))
        right.append((x - px * hw, y - py * hw))
    return c.poly(left + right[::-1])


def scorpion_stinger():
    """The last tail segments of a Sandstorm Scorpion: sand-gold plates, a bulb and an amber-venom barb."""
    c = Canvas(32)
    pts = S.curve_pts((6.5, 27.5), (4.5, 12), (14, 9), 30)
    for (i0, i1, wm) in ((0, 11, 7.6), (10, 20, 7.4), (19, 29, 7.0)):
        seg = _barrel(c, pts[i0:i1 + 1], 4.4, wm)
        c.put(seg, SANDGOLD, 'ray', base=2, sep=True)
        mid = pts[(i0 + i1) // 2]
        nxt = pts[(i0 + i1) // 2 + 1]
        dx, dy = nxt[0] - mid[0], nxt[1] - mid[1]
        L = math.hypot(dx, dy) or 1.0
        for off, col in ((1.7, SANDGOLD[4]), (-1.3, SANDGOLD[1])):
            kx, ky = mid[0] + dy / L * off, mid[1] - dx / L * off
            c.put(c.seg(kx - dx / L * 1.8, ky - dy / L * 1.8, kx + dx / L * 1.8, ky + dy / L * 1.8, 1.0) & erode4(seg),
                  col, 'flat', out=SANDGOLD.out)
    # telson: a pear-shaped bulb that tapers into one hooked thorn
    bulb = c.ellipse(17.5, 9.5, 5.0, 4.6)
    thorn = S.taper_curve(c, (18, 9.5), (29.5, 8), (24.5, 22.5), 9.0, 0.8, 24)
    c.put(bulb | thorn, SANDGOLD, 'sphere', base=2, sep=True, cx=19, cy=9, rx=9, ry=8)
    tip = thorn & (c.Y > 12.5) & (c.X > 21)
    c.put(tip, Ramp(['#3E200C', '#703E16', '#A8662A', '#D4954A', '#F4C77E'], '#1A0C04'), 'ray', base=2)
    c.put(c.ellipse(16.5, 7.5, 2.2, 1.0) & bulb, SANDGOLD[4], 'flat')
    c.put(S.bez_line(c, (21, 7), (25, 6.5), (26, 10)) & erode4(thorn), SANDGOLD[3], 'flat', out=SANDGOLD.out)
    bead = S.drop(c, 24.3, 26.0, 1.9, 4.0)
    c.put(bead, VENOM_AMBER, 'ray', base=3, sep=True)
    c.put(c.rect(23, 25, 23, 25), VENOM_AMBER[4], 'flat')
    c.outline()
    halo(c, bead, '#FFB844', (110, 45))
    return c


def worm_glass_tooth():
    """A Dune Worm's tooth of clear desert glass, an amber thread at its core and sand at the root."""
    c = Canvas(32)
    m = fang(c, (22, 26), (25, 9), (7, 5), 8.5, DESERT_GLASS, root_col=None)
    # refraction line on the shadow side and a faint amber thread at the core
    c.put(S.bez_line(c, (23, 23), (24.5, 12), (15, 7.5)) & erode4(m) & ~erode4(erode4(m)) & (c.X > 17),
          DESERT_GLASS[1], 'flat', out=DESERT_GLASS.out)
    core = S.taper_curve(c, (21.5, 24), (22.5, 11), (11, 7), 1.8, 0.8) & erode4(erode4(m))
    c.put(core, VENOM_AMBER, 'flat', base=3)
    crust = c.ellipse(22, 26.8, 4.2, 2.3) | c.ellipse(18, 28.2, 2.8, 1.3) | c.ellipse(25.5, 28.3, 2.6, 1.3)
    c.put(crust, R['sand'], 'ray', base=3, sep=True)
    c.pxs([(20, 26), (23, 27), (17, 28), (25, 28)], R['sand'][1])
    c.pxs([(21, 25), (16, 27)], R['sand'][4])
    c.put(c.rect(18, 12, 18, 16) | c.rect(17, 10, 17, 10), '#FFFFFF', 'flat')
    c.outline()
    c.glow('#BFF2F0', (50,))
    S.sparkle(c, 24, 4, '#FFFFFF', DESERT_GLASS[3], 1)
    return c


register(FAM, 'scorpion_stinger', scorpion_stinger, GROUP)
register(FAM, 'worm_glass_tooth', worm_glass_tooth, GROUP)

