"""Insects (V10 · Keeping Post, the netting craft): specimens seen from above or three-quarter, filling the
icon the way the fish do. Parts are laid out in a body frame (u along the body towards the head, v across it)
so a specimen can sit on the diagonal."""
import math

from pix import Canvas, Ramp, erode4
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'insects'

IN_GLOWTAIL = Ramp(['#40560E', '#7A9A18', '#BEE03A', '#E8FF86', '#FBFFD6'], '#18220A')
IN_BLACKSHELL = Ramp(['#121010', '#221D19', '#382F27', '#584C3E', '#86775F'], '#060504')
IN_CICADA = Ramp(['#20200F', '#3A3A1A', '#5E5E2C', '#8A884C', '#BAB67E'], '#0C0C05')
IN_CLEARWING = Ramp(['#5E7C86', '#8EAAB2', '#BCD4D8', '#E0F0F0', '#FFFFFF'], '#223238')
IN_SCARAB = Ramp(['#0C3226', '#16553C', '#2A8A5A', '#5CC486', '#C8F4B4'], '#051710')
IN_CREAM = Ramp(['#6A5C44', '#A49274', '#D8C8A4', '#F0E6CC', '#FFFBEE'], '#28221A')
IN_MANTIS = Ramp(['#1A1846', '#2E2C78', '#4A4EAA', '#7C82D6', '#BEC4F4'], '#090820')
IN_FROST = Ramp(['#1C4460', '#32769A', '#62B2D6', '#A8E2F2', '#EEFCFF'], '#0A1C2A')
IN_LOCUST = Ramp(['#4A140E', '#861E14', '#C8401E', '#EE7A32', '#FFC070'], '#200604')
IN_MIDNIGHT = Ramp(['#0A0E26', '#141C44', '#223070', '#3A4EA0', '#6E86D0'], '#04060F')
IN_SPARK = ('#FFFFFF', '#9FE8FF')


class Body:
    """Body frame: u along the body (towards the head), v across it (to the body's left)."""

    def __init__(self, c, cx, cy, angle):
        a = math.radians(angle)
        self.c = c
        self.cx, self.cy = cx, cy
        self.d = (math.cos(a), -math.sin(a))
        self.n = (-math.sin(a), -math.cos(a))
        dx, dy = c.X - cx, c.Y - cy
        self.U = dx * self.d[0] + dy * self.d[1]
        self.V = dx * self.n[0] + dy * self.n[1]

    def p(self, u, v):
        return (self.cx + u * self.d[0] + v * self.n[0], self.cy + u * self.d[1] + v * self.n[1])

    def ip(self, u, v):
        x, y = self.p(u, v)
        return (int(math.floor(x)), int(math.floor(y)))

    def ell(self, u0, v0, a, b, rot=0.0):
        """Ellipse in body coordinates; rot turns its long axis from u towards v (degrees)."""
        du, dv = self.U - u0, self.V - v0
        r = math.radians(rot)
        s = du * math.cos(r) + dv * math.sin(r)
        t = -du * math.sin(r) + dv * math.cos(r)
        return (s / a) ** 2 + (t / b) ** 2 <= 1.0

    def poly(self, pts):
        return self.c.poly([self.p(u, v) for (u, v) in pts])

    def line(self, pts, w=1.0):
        """Leg / antenna: a 1-px pixel path (w <= 1) or a thick polyline."""
        if w <= 1.0:
            return self.c.bres_path([self.ip(u, v) for (u, v) in pts])
        return self.c.polyline([self.p(u, v) for (u, v) in pts], w)

    def pair(self, pts, w=1.0):
        """A leg and its mirror on the other side of the body."""
        return self.line(pts, w) | self.line([(u, -v) for (u, v) in pts], w)


def _halo(c, mask, col, alphas=(110, 50)):
    from families.beast_parts import halo
    halo(c, mask, col, alphas)


# ============================================================================ specimens
def glowfly():
    """A firefly from above: a rose shield, near-black wing cases parted over a glowing yellow-green tail."""
    c = Canvas(32)
    B = Body(c, 15.5, 16.5, 58)
    legs = B.pair([(4.5, 2), (6.5, 6.5), (8.5, 8.5)]) | B.pair([(2, 2.5), (1.5, 7.5), (-1, 9.5)]) | \
        B.pair([(-0.5, 2.5), (-4.5, 7), (-7.5, 8)])
    c.put(legs, IN_BLACKSHELL, 'flat', base=1)
    ant = B.pair([(10.5, 0.8), (13, 2.5), (14.2, 5)])
    c.put(ant, IN_BLACKSHELL, 'flat', base=2)
    tail = B.ell(-6.5, 0, 6.5, 4.0)
    c.put(tail, IN_GLOWTAIL, 'sphere', base=2)
    c.put(tail & (((B.U + 20).astype(int) % 3) == 0) & (B.U > -10), IN_GLOWTAIL, 'flat', base=1)
    left = B.ell(0.5, 2.5, 7.0, 2.9, -8)
    right = B.ell(0.5, -2.5, 7.0, 2.9, 8)
    for m in (left, right):
        c.put(m, IN_BLACKSHELL, 'ray', base=2, sep=True)
    c.put(S.outline_only(left) & (B.V > 4.2), IN_BLACKSHELL[4], 'flat', out=IN_BLACKSHELL.out)
    c.put(S.outline_only(right) & (B.V < -4.2), IN_BLACKSHELL[3], 'flat', out=IN_BLACKSHELL.out)
    shield = B.ell(7.4, 0, 2.8, 3.9)
    c.put(shield, R['salmon'], 'sphere', base=2, sep=True)
    c.put(B.ell(7.6, 0, 1.2, 1.2) & shield, IN_BLACKSHELL, 'flat', base=1)
    head = B.ell(10.0, 0, 1.6, 2.0)
    c.put(head, IN_BLACKSHELL, 'sphere', base=2, sep=True)
    c.outline()
    _halo(c, tail, '#DFFF6A', (120, 55))
    S.sparkle(c, *B.ip(-10.5, 5.5), '#FBFFD6', IN_GLOWTAIL[3], 1)
    return c


def reed_cicada():
    """A cicada from above: broad brown-green head and thorax, clear dark-veined wings folded past its tail."""
    c = Canvas(32)
    B = Body(c, 16, 15.5, 90)
    legs = B.pair([(6, 4), (7.5, 7.5), (9.5, 8.5)]) | B.pair([(3.5, 4), (2.5, 8), (0.5, 9.5)])
    c.put(legs, IN_CICADA, 'flat', base=1)
    body = B.ell(-2.5, 0, 7.5, 3.4)
    c.put(body, IN_CICADA, 'ray', base=2)
    # clear forewings: a dark leading edge, pale glassy cells, the abdomen showing through
    wpts = [(5.5, 2.0), (3.5, 6.8), (-1.5, 8.4), (-8, 7.2), (-13.2, 3.6), (-14.2, 0.8), (-6, 0.3), (1, 0.8)]
    wl = B.poly(wpts)
    wr = B.poly([(u, -v) for (u, v) in wpts])
    for m, lit in ((wr, 2), (wl, 3)):
        c.put(m, IN_CLEARWING, 'flat', base=lit, sep=True, sep_col=IN_CICADA[0])
        c.put(m & body, IN_CICADA, 'flat', base=3)
    veins = c.empty()
    for s in (1, -1):
        veins |= B.line([(4.5, 2.4 * s), (2.5, 6.6 * s), (-2, 8.0 * s), (-8, 6.8 * s)])   # leading edge
        veins |= B.line([(3.5, 2.6 * s), (-3, 4.6 * s), (-9, 4.4 * s), (-12.5, 2.2 * s)])
        veins |= B.line([(-3, 4.6 * s), (-4, 7.8 * s)]) | B.line([(-9, 4.4 * s), (-10, 6.2 * s)])
        veins |= B.line([(-6, 2.8 * s), (-6, 4.6 * s)])
    c.put(veins & (wl | wr), IN_CICADA, 'flat', base=0)
    thorax = B.ell(5.8, 0, 3.4, 4.8)
    c.put(thorax, IN_CICADA, 'sphere', base=2, sep=True)
    c.put(B.line([(7.5, -1.5), (4.5, 0), (7.5, 1.5)]) & thorax, R['moss'], 'flat', base=4)
    head = B.ell(9.8, 0, 1.9, 5.2)
    c.put(head, IN_CICADA, 'ray', base=3, sep=True)
    for s in (1, -1):
        c.put(B.ell(10.0, 4.9 * s, 1.5, 1.5), R['ink'], 'sphere', base=3, sep=True)
    c.put(B.ell(11.2, 0, 0.9, 1.4), IN_CICADA, 'flat', base=4)
    c.outline()
    return c


def jade_scarab():
    """A jade scarab from above: toothed head, broad shield and domed wing cases with a metallic sheen."""
    c = Canvas(32)
    B = Body(c, 16, 16.5, 90)
    legs = B.pair([(6, 5), (8, 9), (11.5, 10)], 1.6) | B.pair([(1, 6), (0, 10.5), (-3, 12)], 1.4) | \
        B.pair([(-4, 5.5), (-8, 10), (-12, 10.5)], 1.4)
    c.put(legs, IN_SCARAB, 'flat', base=1)
    for (u, v) in ((8, 8.5), (9.8, 9.4), (0.2, 9.6), (-1.6, 10.9), (-7, 9.4), (-9.6, 10.2)):
        for s in (1, -1):
            x, y = B.ip(u, v * s)
            c.px(x, y + 1 if s > 0 else y - 1, IN_SCARAB[2], IN_SCARAB.out)
    elytra = B.ell(-3.5, 0, 9.8, 8.2)
    c.put(elytra, IN_SCARAB, 'sphere', base=2)
    c.put(B.line([(4, 0), (-12.5, 0)]) & elytra, IN_SCARAB, 'flat', base=0)
    for vv in (3.5, -3.5):
        c.put(B.line([(3.5, vv), (-10, vv * 0.85)]) & erode4(elytra), IN_SCARAB, 'flat', base=1)
    pron = B.ell(6.2, 0, 3.8, 7.0) & (B.U > 3)
    c.put(pron, IN_SCARAB, 'sphere', base=2, sep=True, sep_col=IN_SCARAB[0])
    head = B.poly([(8.5, 4.4), (11.2, 4.2), (12.2, 2.2), (11.4, 0.8), (12.4, 0), (11.4, -0.8), (12.2, -2.2),
                   (11.2, -4.2), (8.5, -4.4)])
    c.put(head, IN_SCARAB, 'ray', base=2, sep=True, sep_col=IN_SCARAB[0])
    # metallic sheen: bright mint streaks and a warm gold-green glint on the lit side
    c.put(B.line([(1, 4.8), (-3, 6.2), (-8, 5.5)]) & erode4(elytra), IN_SCARAB[4], 'flat', out=IN_SCARAB.out)
    c.put(B.line([(1, -2.4), (-4, -2.2)]) & elytra, IN_SCARAB[3], 'flat', out=IN_SCARAB.out)
    c.put(B.line([(7.5, 3.5), (6.5, 1.5)]) & pron, '#D8F29A', 'flat', out=IN_SCARAB.out)
    c.put(B.line([(10.5, 2.5), (10.5, 1.5)]) & head, IN_SCARAB[4], 'flat', out=IN_SCARAB.out)
    c.outline()
    S.sparkle(c, *B.ip(-1, 9.5), '#FFFFFF', IN_SCARAB[4], 1)
    return c


def silk_moth():
    """A silk moth with its wings spread: pale cream wings, a soft white body and feathery antennae."""
    c = Canvas(32)
    B = Body(c, 16, 17, 90)
    fw = [(5, 1.5), (8, 6.5), (9.8, 12.2), (8.2, 14.4), (3, 13), (-1.2, 9.5), (-2, 1.5)]
    fore_l = B.poly(fw)
    hind_l = B.ell(-4.5, 6.4, 5.8, 5.4, -20)
    fore_r = B.poly([(u, -v) for (u, v) in fw])
    hind_r = B.ell(-4.5, -6.4, 5.8, 5.4, 20)
    for m, base in ((hind_l, 2), (hind_r, 2)):
        c.put(m, IN_CREAM, 'ray', base=base)
    for m in (fore_l, fore_r):
        c.put(m, IN_CREAM, 'ray', base=3, sep=True, sep_col=IN_CREAM[1])
    # faint wing markings: a wavy band on the forewings, a small eyespot on the hind wings
    band = B.line([(7, 3), (4.5, 6), (5, 9.5), (2.5, 12.5)]) | B.line([(7, -3), (4.5, -6), (5, -9.5), (2.5, -12.5)])
    c.put(band & (fore_l | fore_r), IN_CREAM, 'flat', base=1)
    for s in (1, -1):
        c.put(B.ell(-5, 6.5 * s, 1.3, 1.3), R['bronze'], 'flat', base=2)
        c.put(B.ell(-5, 6.5 * s, 0.6, 0.6), IN_CREAM, 'flat', base=4)
    c.put(S.outline_only(hind_l | hind_r) & (B.U < -7), IN_CREAM, 'flat', base=1)
    body = B.ell(-1.5, 0, 8.0, 2.4)
    c.put(body, R['pearl'], 'ray', base=3, sep=True, sep_col=IN_CREAM[1])
    c.put(body & (((B.U + 30).astype(int) % 2) == 0) & (B.U < -2) & (B.V > -1), R['pearl'], 'flat', base=2)
    thorax = B.ell(4.8, 0, 2.6, 2.6)
    c.put(thorax, R['pearl'], 'sphere', base=3, sep=True, sep_col=IN_CREAM[1])
    head = B.ell(7.6, 0, 1.5, 1.8)
    c.put(head, R['pearl'], 'sphere', base=2, sep=True, sep_col=IN_CREAM[1])
    # feathery (comb) antennae: two small plumes fanning out from the head
    for s in (1, -1):
        plume = B.ell(11.0, 4.0 * s, 3.4, 1.5, 52 * s)
        c.put(plume, R['bronze'], 'flat', base=3, sep=True)
        comb = plume & ((((B.U * 0.6 - B.V * s * 0.8) * 1.6).astype(int) % 2) == 0)
        c.put(comb, R['bronze'], 'flat', base=1)
        c.put(B.line([(8.4, 0.8 * s), (10.8, 3.8 * s), (13.2, 7.0 * s)]), R['bronze'], 'flat', base=0)
    c.outline()
    return c


def thunder_mantis():
    """A blue-violet mantis in three-quarter view, forelegs raised, a spark crackling between its claws."""
    c = Canvas(32)
    ramp = IN_MANTIS
    # far-side walking legs first (darker), then the body, then the near legs
    far = c.bres_path([(14, 21), (17, 24), (18, 29)]) | c.bres_path([(9, 23), (11, 27), (10, 29)])
    c.put(far, ramp, 'flat', base=1)
    B = Body(c, 9.0, 23.0, 25)
    abdomen = B.ell(-0.5, 0, 7.6, 3.3)
    c.put(abdomen, ramp, 'ray', base=2)
    c.put(abdomen & (((B.U + 20).astype(int) % 3) == 0) & (B.V < 1.2), ramp, 'flat', base=1)
    wings = B.ell(0.8, 1.7, 7.4, 1.9)
    c.put(wings, R['violet'], 'ray', base=3, sep=True, sep_col=ramp[0])
    c.put(B.line([(7, 1.9), (-5.5, 2.0)]) & wings, R['violet'], 'flat', base=4)
    neck = c.seg(15, 19.5, 17.5, 10, 2.6)
    c.put(neck, ramp, 'across', base=2, sep=True)
    head = c.poly([(13.6, 6.6), (19.6, 5.4), (17.8, 10.2), (16.2, 10.4)])
    c.put(head, ramp, 'ray', base=3, sep=True)
    for (x, y) in ((13, 6), (19, 5)):
        c.put(c.rect(x, y - 1, x + 1, y), R['qi'], 'flat', base=3, sep=True, sep_col=ramp[0])
    ant = c.bres_path([(15, 4), (13, 1), (9, 2)]) | c.bres_path([(17, 4), (19, 1)])
    c.put(ant & ~c.a, ramp, 'flat', base=3)
    near = c.bres_path([(16, 19), (20, 23), (21, 29)]) | c.bres_path([(7, 25), (5, 28), (3, 29)])
    c.put(near, ramp, 'flat', base=3)
    # raptorial forelegs: coxa forward and down, spined femur raised high, tibia hooked over at the top
    for (dx, dy, base) in ((1.6, 0.6, 2), (0, 0, 3)):
        coxa = c.seg(17.5 + dx, 12.5 + dy, 21.5 + dx, 15.5 + dy, 2.2)
        femur = c.seg(21.5 + dx, 15.5 + dy, 24.5 + dx, 8 + dy, 2.2)
        tibia = c.seg(24.5 + dx, 8 + dy, 23 + dx, 5 + dy, 1.4)
        c.put(coxa | femur | tibia, ramp, 'ray', base=base, sep=True)
    c.pxs([(22, 12), (23, 10)], ramp[4], out=ramp.out)
    c.outline()
    spark = c.pts([(26, 3), (27, 4), (26, 5), (27, 6), (28, 5), (25, 4), (27, 2)])
    c.put(spark & ~c.a, IN_SPARK[1], 'flat', out='#0B2A3A')
    S.sparkle(c, 26, 4, IN_SPARK[0], IN_SPARK[1], 2)
    _halo(c, c.rect(24, 2, 28, 6), '#9FE8FF', (110, 45))
    return c


def frost_cricket():
    """An ice-blue cricket in side view: long sweeping antennae, frost-white legs, the big hind leg cocked."""
    c = Canvas(32)
    body, legs = IN_FROST, R['cloud']
    far = c.bres_path([(19, 21), (19, 25), (17, 28)])
    c.put(far, legs, 'flat', base=1)
    abdomen = c.ellipse(11, 20, 8.5, 4.4)
    c.put(abdomen, body, 'ray', base=2)
    c.put(abdomen & (c.xi % 3 == 0) & (c.Y > 20.5), body, 'flat', base=1)
    wing = c.poly([(18, 15.2), (5, 16.2), (2.8, 18.8), (9, 19.6), (18.5, 18.2)])
    c.put(wing, body, 'ray', base=3, sep=True)
    c.put(c.bres_path([(16, 16), (5, 17)]) & wing, body, 'flat', base=1)
    thorax = c.ellipse(21, 18, 4.2, 3.9)
    c.put(thorax, body, 'sphere', base=2, sep=True)
    head = c.ellipse(26, 17.5, 3.3, 3.6)
    c.put(head, body, 'sphere', base=3, sep=True)
    c.put(c.rect(26, 15, 27, 16), R['ink'], 'flat', base=1, sep=True, sep_col=body[0])
    c.px(26, 15, '#FFFFFF')
    c.put(c.bres_path([(28, 20), (29, 22)]), body, 'flat', base=1)
    # near legs: front, middle, and the thick hind femur with its long spined tibia
    near = c.bres_path([(25, 21), (27, 25), (29, 27)]) | c.bres_path([(21, 21), (22, 25), (24, 28)])
    c.put(near, legs, 'flat', base=3)
    femur = c.seg(15, 20.5, 8, 10.5, 3.4)
    c.put(femur, legs, 'ray', base=3, sep=True, sep_col=body[0])
    c.put(c.bres_path([(14, 19), (9, 12)]) & femur, legs, 'flat', base=1)
    tibia = c.bres_path([(7, 10), (5, 19), (3, 28)])
    c.put(tibia, legs, 'flat', base=4)
    c.pxs([(4, 21), (4, 24)], legs[2], out=legs.out)
    ant = S.bez_line(c, (26, 14), (24, 2), (13, 3)) | S.bez_line(c, (25, 14), (21, 5), (11, 7))
    c.put(ant & ~c.a, body, 'flat', base=3)
    c.outline()
    S.sparkle(c, 29, 9, '#FFFFFF', R['ice'][3], 1)
    S.sparkle(c, 4, 4, '#FFFFFF', R['ice'][3], 1)
    return c


def ember_locust():
    """A red-orange locust in flight, seen from above: long forewings, fanned hind wings with ember-bright edges."""
    c = Canvas(32)
    B = Body(c, 15.5, 16.5, 52)
    fan_pts = [(4, 1.5), (3.5, 8), (0.5, 12.8), (-4.5, 13.2), (-8.5, 9.5), (-9, 1.5)]
    for s in (1, -1):
        fan = B.poly([(u, v * s) for (u, v) in fan_pts])
        c.put(fan, R['fire'], 'ray', base=3)
        edge = S.outline_only(fan) & (B.V * s > 3.5)
        c.put(edge, R['fire'], 'flat', base=4)
        for (u, v) in ((0.5, 12.8), (-4.5, 13.2), (-8.5, 9.5)):
            c.put(B.line([(3, 1.8 * s), (u * 0.85, v * 0.85 * s)]) & fan, IN_LOCUST, 'flat', base=1)
    for s in (1, -1):
        fore = B.poly([(6, 1.2 * s), (8.5, 3.4 * s), (4.5, 12.4 * s), (1.8, 13.6 * s), (0.8, 11 * s), (2.5, 1.5 * s)])
        c.put(fore, IN_LOCUST, 'ray', base=2, sep=True)
        c.put(S.outline_only(fore) & (B.U > 3.2) & (B.V * s > 1.8), R['fire'], 'flat', base=4, out=IN_LOCUST.out)
        c.put(B.line([(6, 2.2 * s), (2.5, 11.5 * s)]) & fore, IN_LOCUST, 'flat', base=1)
    abdomen = B.ell(-6.5, 0, 6.2, 1.9)
    c.put(abdomen, IN_LOCUST, 'ray', base=2, sep=True)
    c.put(abdomen & (((B.U + 30).astype(int) % 2) == 0), IN_LOCUST, 'flat', base=1)
    thorax = B.ell(5.5, 0, 3.4, 2.6)
    c.put(thorax, IN_LOCUST, 'sphere', base=2, sep=True)
    head = B.ell(9.4, 0, 2.0, 2.2)
    c.put(head, IN_LOCUST, 'sphere', base=3, sep=True)
    for s in (1, -1):
        c.put(B.ell(9.6, 1.6 * s, 0.9, 0.9), R['ink'], 'flat', base=2)
    ant = B.pair([(10.8, 1), (12.4, 2), (13.6, 4.2)])
    c.put(ant & ~c.a, IN_LOCUST, 'flat', base=1)
    legs = B.pair([(7.5, 2.4), (9, 4.5)]) | B.pair([(-1, 1.6), (-3.5, 3.2), (-9.5, 3.4)])
    c.put(legs & ~c.a, IN_LOCUST, 'flat', base=1)
    c.outline()
    return c


def starwing_mote():
    """A tiny star-sea fly: a midnight-blue body under four pointed wings of gold star-dust, glowing softly."""
    c = Canvas(32)
    B = Body(c, 16, 16.5, 90)
    wings = c.empty()
    for s in (1, -1):
        fore = B.poly([(2.5, 1 * s), (8.5, 7.5 * s), (13, 12.5 * s), (5, 11.5 * s), (0, 4 * s)])
        hind = B.poly([(-0.5, 1 * s), (-2.5, 7 * s), (-9.5, 12 * s), (-6, 5 * s), (-3, 1 * s)])
        for m, base in ((hind, 1), (fore, 2)):
            c.put(m, R['gold'], 'ray', base=base, sep=True, sep_col=R['gold'][0])
            wings |= m
    dust = wings & ((((c.xi * 3 + c.yi * 5) % 7) == 0) | (((c.xi * 5 + c.yi * 2) % 11) == 0))
    for s in (1, -1):
        c.put(B.line([(2, 1.5 * s), (11, 11 * s)]) & wings, R['gold'], 'flat', base=0)
    c.put(erode4(wings) & dust, '#FFFDF4', 'flat', out=R['gold'].out)
    body = B.ell(-2.5, 0, 6.0, 1.9)
    c.put(body, IN_MIDNIGHT, 'ray', base=2, sep=True)
    c.put(body & (((B.U + 30).astype(int) % 2) == 0), IN_MIDNIGHT, 'flat', base=3)
    thorax = B.ell(3.2, 0, 2.5, 2.4)
    c.put(thorax, IN_MIDNIGHT, 'sphere', base=2, sep=True)
    head = B.ell(6.2, 0, 1.8, 2.3)
    c.put(head, IN_MIDNIGHT, 'sphere', base=2, sep=True)
    for s in (1, -1):
        x, y = B.ip(6.6, 1.3 * s)
        c.px(x, y, R['gold'][3], IN_MIDNIGHT.out)
    ant = B.pair([(7.8, 0.8), (10, 2.4)])
    c.put(ant & ~c.a, IN_MIDNIGHT, 'flat', base=3)
    tail = B.ell(-8.8, 0, 1.1, 1.1)
    c.put(tail, R['starlight'], 'flat', base=4)
    c.outline()
    c.glow('#F3E3A6', (80, 35))
    S.sparkle(c, *B.ip(-9.5, 0), '#FFFFFF', R['starlight'][3], 1)
    S.sparkle(c, 27, 4, '#FFFFFF', R['starlight'][3], 1)
    return c


for _in_id, _in_fn in (('glowfly', glowfly), ('reed_cicada', reed_cicada), ('jade_scarab', jade_scarab),
                       ('silk_moth', silk_moth), ('thunder_mantis', thunder_mantis),
                       ('frost_cricket', frost_cricket), ('ember_locust', ember_locust),
                       ('starwing_mote', starwing_mote)):
    register(FAM, _in_id, _in_fn, GROUP)
