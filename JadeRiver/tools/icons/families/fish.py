"""Fish: one side-view template (body profile, forked tail, fins, eye, pattern)
driven by per-species parameters. The eel uses its own serpentine body."""
import math

import numpy as np

from pix import Canvas, Ramp, erode4, move
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'fish'


class Frame:
    """Fish-local coordinates: u along the body (head +), v up."""

    def __init__(self, cx, cy, angle):
        a = math.radians(angle)
        self.cx, self.cy = cx, cy
        self.d = (math.cos(a), -math.sin(a))
        self.n = (-math.sin(a), -math.cos(a))

    def p(self, u, v):
        return (self.cx + u * self.d[0] + v * self.n[0], self.cy + u * self.d[1] + v * self.n[1])

    def uv(self, c):
        dx, dy = c.X - self.cx, c.Y - self.cy
        return dx * self.d[0] + dy * self.d[1], dx * self.n[0] + dy * self.n[1]


def fish(c, L=24, H=10, angle=15, cx=None, cy=None, body=None, belly=None, fin=None,
         pattern=None, pat_ramp=None, tail=7, dorsal=(0.0, 0.35, 0.6), barbels=False, hook=False,
         eye_col='#071015', spiny=False, low_fins=True):
    body = body or R['silver']
    belly = belly or R['paper']
    if cx is None:  # centre the full nose-to-tail length on the canvas
        cx = 15.5 + tail * 0.5 * math.cos(math.radians(angle))
    if cy is None:
        cy = 16.0 - tail * 0.5 * math.sin(math.radians(angle))
    fin = fin or body
    F = Frame(cx, cy, angle)
    hl = L / 2.0
    top, bot = [], []
    k = 24
    for i in range(k + 1):
        t = i / float(k)
        u = -hl + t * L
        f = 0.2 + 0.8 * math.sin(math.pi * min(1.0, t ** 0.85)) ** 0.55
        if t > 0.86:
            f *= math.sqrt(max(0.0, (1.0 - t) / 0.14)) * 0.85 + 0.15
        top.append(F.p(u, H / 2.0 * f))
        bot.append(F.p(u, -H / 2.0 * f * (0.86 if not hook else 0.8)))
    bodym = c.poly(top + bot[::-1])
    # fins (drawn first, behind the body)
    d0, d1, dh = dorsal
    dors = c.poly([F.p(-hl * 0.1 + d0 * L - L * 0.12, H * 0.38), F.p(d0 * L - L * 0.02, H * (0.5 + dh)),
                   F.p(d0 * L + L * 0.16, H * 0.42)])
    if spiny:
        for s in range(3):
            uu = d0 * L - L * 0.08 + s * L * 0.08
            dors |= c.seg(*F.p(uu, H * 0.4), *F.p(uu + 0.5, H * (0.5 + dh) + 0.8), 1.0)
    anal = c.poly([F.p(-hl * 0.45, -H * 0.36), F.p(-hl * 0.3, -H * 0.72), F.p(-hl * 0.05, -H * 0.4)])
    pelv = c.poly([F.p(hl * 0.12, -H * 0.4), F.p(hl * 0.2, -H * 0.78), F.p(hl * 0.38, -H * 0.42)])
    tailm = c.poly([F.p(-hl + 1.5, H * 0.12), F.p(-hl - tail, H * 0.62), F.p(-hl - tail * 0.55, 0),
                    F.p(-hl - tail, -H * 0.62), F.p(-hl + 1.5, -H * 0.12)])
    for m in ((dors, anal, pelv, tailm) if low_fins else (dors, tailm)):
        c.put(m, fin, 'ray', base=2)
    # fin rays
    for m in (tailm, dors):
        u, v = F.uv(c)
        rays = m & (np.round(v * 1.0) % 2 == 0) & erode4(m)
        c.put(rays, fin[1], 'flat', out=fin.out)
    c.put(bodym, body, 'ray', sep=True, sep_col=fin.out)
    u, v = F.uv(c)
    bel = bodym & (v < -H * 0.08)
    c.put(bel, belly, 'ray', base=3)
    c.put(bodym & (v < -H * 0.08) & (v >= -H * 0.08 - 1.0), body[1], 'flat', out=body.out)
    # pattern
    pr = pat_ramp or body
    inner = erode4(bodym)
    if pattern == 'bars':
        bars = inner & (v > -H * 0.2) & (np.floor((u + hl) / 3.0) % 2 == 1) & (u < hl * 0.45) & (u > -hl * 0.7)
        c.put(bars, pr[1], 'flat', out=body.out)
    elif pattern == 'spots':
        for (su, sv) in ((-6, 2), (-2, 3), (2, 2.4), (-4, 0.5), (0, 1), (4, 3), (-8, 1.2), (6, 1.5)):
            x, y = F.p(su, sv)
            c.put(c.rect(int(x), int(y), int(x), int(y)) & inner, pr[1], 'flat', out=body.out)
    elif pattern == 'stripe':
        st = inner & (np.abs(v - H * 0.02) < 0.8) & (u < hl * 0.55)
        c.put(st, pr[1], 'flat', out=body.out)
    elif pattern == 'scales':
        sc = inner & (v > -H * 0.1) & ((np.floor(u / 2.5) + np.floor(v / 2.2)) % 2 == 0) & (u < hl * 0.45)
        c.put(sc, body[3], 'flat', out=body.out)
    elif pattern == 'band':
        st = inner & (np.abs(v + H * 0.02) < 1.2) & (u < hl * 0.6)
        c.put(st, pr, 'flat', base=3, out=body.out)
    # gill arc + eye
    gx, gy = F.p(hl * 0.52, 0)
    gill = c.arc(gx - 3 * F.d[0], gy - 3 * F.d[1], 3.2, 1.0, -60 - 15, 60 - 15) & inner
    c.put(gill, body[1], 'flat', out=body.out)
    ex, ey = F.p(hl * 0.72, H * 0.1)
    eye = c.circle(ex, ey, 1.25)
    c.put(eye, eye_col, 'flat')
    c.px(int(ex - 0.2), int(ey - 0.8), '#FFFFFF')
    if barbels:
        bx, by = F.p(hl - 1.5, -H * 0.15)
        c.put(S.bez_line(c, (bx, by), (bx + 0.5, by + 2.5), (bx - 2, by + 4)), R['gold'][3], 'flat', out=R['gold'].out)
    if hook:
        jx, jy = F.p(hl + 0.8, -H * 0.05)
        c.put(c.circle(jx, jy, 1.2), body, 'flat', base=2)
    return bodym, F


def river_minnow():
    c = Canvas(32)
    fish(c, L=13, H=5, angle=18, cx=12, cy=8.5, body=R['silver'], belly=R['pearl'], fin=R['hollow'],
         pattern=None, tail=4, dorsal=(0.0, 0.3, 0.3))
    fish(c, L=20, H=8, angle=18, cx=17, cy=20.5, body=R['silver'], belly=R['pearl'], fin=R['hollow'],
         pattern='stripe', pat_ramp=R['stone'], tail=5.5)
    c.outline()
    return c


def reed_perch():
    c = Canvas(32)
    body = Ramp(['#1E3418', '#35562A', '#5E8A3E', '#9EBE5E', '#DDEBA0'], '#0C1609')
    fish(c, L=21, H=12, angle=14, body=body, belly=R['straw'], fin=R['ember'], pattern='bars', tail=5.5,
         dorsal=(-0.05, 0.35, 0.45), spiny=True)
    c.outline()
    return c


def jade_carp_fish():
    c = Canvas(32)
    fish(c, L=21, H=12, angle=16, body=R['jade'], belly=R['paper'], fin=R['gold'], pattern='scales', tail=5.5,
         barbels=True, dorsal=(-0.05, 0.4, 0.35))
    c.outline()
    return c


def mist_trout():
    c = Canvas(32)
    body = Ramp(['#2C4A58', '#4E7486', '#88AEBC', '#C6DEE2', '#F4FCFC'], '#101C22')
    fish(c, L=22, H=10, angle=12, body=body, belly=R['pearl'], fin=R['mist'], pattern='spots',
         pat_ramp=R['navy'], tail=5.5)
    band = Frame(15.5 + 2.75 * math.cos(math.radians(12)), 16.0 - 2.75 * math.sin(math.radians(12)), 12)
    u, v = band.uv(c)
    st = erode4(c.a) & (abs(v + 0.3) < 0.8) & (u < 6) & (u > -10)
    c.put(st, R['lotuspink'], 'flat', base=2, only_on=True)
    c.outline()
    return c


def rapids_salmon():
    c = Canvas(32)
    fish(c, L=21, H=10.5, angle=30, cx=18, cy=14.5, body=R['salmon'], belly=R['bone'], fin=R['flesh'],
         pattern='spots', pat_ramp=R['flesh'], tail=5, hook=True)
    # splash droplets
    for (x, y, r) in ((5, 26, 1.6), (9, 29, 1.2), (4.5, 21.5, 1.1)):
        c.put(c.circle(x, y, r), R['qi'], 'flat', base=3)
    c.outline()
    return c


def moon_carp():
    c = Canvas(32)
    body = Ramp(['#4A5870', '#7A8AA6', '#BAC6DA', '#E6ECF6', '#FFFFFF'], '#161C26')
    bm, F = fish(c, L=21, H=12, angle=16, body=body, belly=R['pearl'], fin=R['mist'], pattern=None, tail=5.5,
                 barbels=True, dorsal=(-0.05, 0.4, 0.35))
    mx, my = F.p(-2, 1)
    moon = c.circle(mx, my, 3.2) & ~c.circle(mx + 1.4, my - 1.0, 2.6)
    c.put(moon & erode4(bm), R['gold'], 'flat', base=3)
    c.outline()
    c.glow('#D9EBEF', (70,))
    return c


def river_eel():
    c = Canvas(32)
    ramp = R['eel']
    pts = S.curve_pts((4, 26), (8, 10), (16, 16), 14) + S.curve_pts((16, 16), (24, 22), (27, 6), 14)[1:]
    m = c.empty()
    n = len(pts)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        t = i / float(n - 1)
        w = 1.6 + 3.6 * min(1.0, t * 1.6) if t < 0.93 else 4.4
        m |= c.seg(a[0], a[1], b[0], b[1], w)
    head = c.ellipse(26.5, 6.5, 2.8, 3.2)
    m |= head
    # dorsal fin ribbon
    fin = c.empty()
    for (a, b) in zip(pts[2:-4], pts[3:-3]):
        fin |= c.seg(a[0] - 1.6, a[1] - 1.2, b[0] - 1.6, b[1] - 1.2, 1.2)
    c.put(fin & ~m, R['moss'], 'flat', base=3)
    c.put(m, ramp, 'ray')
    belly = m & ~move(m, -1, -1) & ~move(m, 0, -1)
    c.put(belly & ~head, R['straw'], 'flat', base=3)
    c.put(c.circle(27, 5.5, 1.0), R['gold'], 'flat', base=3)
    c.px(27, 5, '#071015')
    c.outline()
    return c


register(FAM, 'river_minnow', river_minnow, GROUP)
register(FAM, 'reed_perch', reed_perch, GROUP)
register(FAM, 'jade_carp_fish', jade_carp_fish, GROUP)
register(FAM, 'river_eel', river_eel, GROUP)
register(FAM, 'mist_trout', mist_trout, GROUP)
register(FAM, 'rapids_salmon', rapids_salmon, GROUP)
register(FAM, 'moon_carp', moon_carp, GROUP)
