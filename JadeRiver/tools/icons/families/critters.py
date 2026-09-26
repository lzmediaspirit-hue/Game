"""Critters (V10c · Keeping Post, the snaring craft): small spirit animals caught in snares, drawn as specimens
that fill the icon the way the fish and insects do. Soft bodies are built from a spine of overlapping discs
(`_cr_spine`), so each animal keeps a bold, single silhouette at 1x."""
import math

from pix import Canvas, Ramp, erode4
from palette import R
from registry import register
import shapes as S

FAM, GROUP = 'items', 'critters'

CR_FROG = Ramp(['#0C3E24', '#16663A', '#2FA253', '#6CD877', '#C8F7A8'], '#05190E')
CR_FROGBELLY = Ramp(['#5E6A2A', '#96A846', '#CCDB7E', '#E8F2B0', '#FBFFE2'], '#232A0E')
CR_HARE = Ramp(['#56616A', '#8A969E', '#C2CBD0', '#E4EAEC', '#FFFFFF'], '#1E262C')
CR_FERRET = Ramp(['#2E1A0E', '#553219', '#835128', '#B17A42', '#D8A868'], '#140B05')
CR_CREAM = Ramp(['#6E5E44', '#A8946E', '#DCC9A0', '#F2E6C8', '#FFFBEC'], '#2A2319')
CR_TAN = Ramp(['#5A3E1E', '#8E6532', '#C49552', '#E4BE7E', '#F8E2B2'], '#24170A')
CR_QUILL = Ramp(['#191A44', '#2E3276', '#4E56B0', '#8490E2', '#C8D0FF'], '#0A0A22')
CR_SNOW = Ramp(['#5C7082', '#93A8B8', '#D0DEE6', '#EEF5F8', '#FFFFFF'], '#1C2833')
CR_OCHRE = Ramp(['#5C3212', '#94541C', '#CE8A34', '#EDB660', '#FFE0A0'], '#261205')
CR_MIDNIGHT = Ramp(['#0A0F2A', '#16204C', '#243480', '#3C54B0', '#7690DC'], '#04060F')
CR_PELT = Ramp(['#6A6280', '#A69EBE', '#DCD6EE', '#F4F0FA', '#FFFFFF'], '#25202F')
CR_SPARK = ('#FFFFFF', '#9FE8FF')
CR_NOSE = '#E88C94'


def _cr_spine(c, pts, radii, k=6):
    """Union of discs along a polyline: soft animal bodies, necks and tails."""
    m = c.empty()
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r0, r1 = radii[i], radii[i + 1]
        for j in range(k + 1):
            t = j / float(k)
            m |= c.circle(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t)
    return m


def _cr_eye(c, x, y, iris, pupil='#071015', w=2, h=2):
    """A small eye: iris block, dark pupil column, a white catch-light at the top left."""
    c.put(c.rect(x, y, x + w - 1, y + h - 1), iris, 'flat', out=pupil)
    c.put(c.rect(x + w - 1, y, x + w - 1, y + h - 1), pupil, 'flat', out=pupil)
    c.px(x, y, '#FFFFFF', out=pupil)


def _cr_halo(c, mask, col, alphas=(110, 50)):
    from families.beast_parts import halo
    halo(c, mask, col, alphas)


# ============================================================================ specimens
def jade_frog():
    """A squat jade-green frog seen from the front: bulging gold eyes, pale belly, folded hind legs."""
    c = Canvas(32)
    # hind legs folded at the sides, webbed feet splayed at the bottom
    for s in (1, -1):
        thigh = c.ellipse(16 + 9.5 * s, 21.5, 4.6, 5.4)
        c.put(thigh, CR_FROG, 'ray', base=2)
        foot = c.poly([(16 + 8 * s, 26), (16 + 14.4 * s, 27.2), (16 + 14.6 * s, 29.6), (16 + 7 * s, 29.6)])
        c.put(foot, CR_FROG, 'ray', base=2 if s < 0 else 1, sep=True)
        for dx in (10.5, 12.8):
            c.put(c.rect(int(16 + dx * s), 29, int(16 + dx * s), 29) & foot, CR_FROG, 'flat', base=0)
    body = c.ellipse(16, 20.5, 9.2, 7.6)
    c.put(body, CR_FROG, 'sphere', base=2, sep=True)
    head = c.ellipse(16, 14.5, 9.6, 5.8)
    c.put(head, CR_FROG, 'sphere', base=2, cx=13, cy=12, rx=12, ry=9)
    belly = c.ellipse(16, 23.2, 5.6, 4.6) & body
    c.put(belly, CR_FROGBELLY, 'ray', base=3)
    # front legs and three-toed hands
    for s in (1, -1):
        arm = c.seg(16 + 5.6 * s, 22, 16 + 6.6 * s, 27.5, 2.6)
        c.put(arm, CR_FROG, 'across', base=3 if s < 0 else 2, sep=True)
        hand = c.rect(int(16 + 5.2 * s) - 1, 28, int(16 + 5.2 * s) + 2, 29)
        c.put(hand, CR_FROG, 'flat', base=2, sep=True)
    # wide smiling mouth
    mouth = S.bez_line(c, (9, 16), (16, 19.5), (23, 16))
    c.put(mouth & head, CR_FROG, 'flat', base=0)
    c.pxs([(14, 13), (17, 13)], CR_FROG[0], out=CR_FROG.out)
    # back spots
    c.pxs([(9, 19), (23, 19), (8, 22)], CR_FROG[1], out=CR_FROG.out)
    # bulging gold eyes
    for s in (1, -1):
        ex = 16 + 5.8 * s
        eye = c.circle(ex, 9.6, 3.3)
        c.put(eye, CR_FROG, 'sphere', base=3, sep=True)
        ball = c.circle(ex, 9.4, 2.3)
        c.put(ball, R['gold'], 'sphere', base=2, sep=True, sep_col=CR_FROG[0])
        c.put(c.rect(int(ex) - 1, 9, int(ex), 9), R['ink'][0], 'flat', out=CR_FROG.out)
        c.px(int(ex) - 1, 8, '#FFFFFF', out=CR_FROG.out)
    c.outline()
    return c


def mist_hare():
    """A pale grey-white hare sitting in profile, long ears raised, their tips fading into misty blue."""
    c = Canvas(32)
    # far ear, then the body, near ear on top
    far = S.leaf(c, 19, 11, 106, 9.4, 3.6, bend=0.05)
    c.put(far, CR_HARE, 'ray', base=1)
    c.put(far & (c.Y < 6), R['ice'], 'flat', base=1)
    haunch = c.ellipse(11.5, 21.5, 8.2, 7.4)
    chest = c.ellipse(18, 19, 5.6, 6.4)
    body = haunch | chest
    c.put(body, CR_HARE, 'sphere', base=2, cx=12, cy=17, rx=12, ry=10)
    # hind foot along the ground, front paws
    foot = c.ellipse(13, 28, 6.8, 1.9)
    c.put(foot, CR_HARE, 'ray', base=2, sep=True)
    paw = c.seg(20.5, 23, 21, 28, 2.4)
    c.put(paw, CR_HARE, 'across', base=3, sep=True)
    c.put(c.rect(20, 28, 22, 28), CR_HARE, 'flat', base=3)
    haunch_line = c.arc(11.5, 21, 5.2, 1.0, 20, 150) & erode4(haunch)
    c.put(haunch_line, CR_HARE, 'flat', base=1)
    tail = c.circle(3.6, 21, 2.2)
    c.put(tail, CR_HARE, 'sphere', base=3, sep=True)
    head = c.ellipse(22.6, 13.2, 5.4, 4.2) | c.ellipse(26, 14.5, 2.6, 2.4)
    c.put(head, CR_HARE, 'sphere', base=2, sep=True, cx=21, cy=11, rx=7, ry=6)
    near = S.leaf(c, 20.5, 11.5, 98, 9.6, 4.0, bend=-0.08)
    c.put(near, CR_HARE, 'ray', base=3, sep=True)
    c.put(S.midrib(c, 20.5, 11.5, 98, 9.6, -0.08, 0.6) & erode4(near) & (c.Y > 5.5), R['pink'], 'flat', base=3)
    tips = (near | far) & (c.Y < 6)
    c.put(tips & near, R['ice'], 'flat', base=2)
    c.put(tips & near & (c.X < 20), R['ice'], 'flat', base=3)
    _cr_eye(c, 23, 12, R['ink'][3])
    c.px(28, 14, CR_NOSE, out=CR_HARE.out)
    c.put(c.bres(26, 16, 27, 16), CR_HARE, 'flat', base=0)
    c.outline()
    _cr_halo(c, tips, '#AFC9D1', (110, 45))
    return c


def reed_ferret():
    """A slim brown ferret loping through reeds: long low body, cream belly and throat, a dark masked face."""
    c = Canvas(32)
    # reed stalks behind it: a cattail on the left, a bent blade on the right
    c.put(c.seg(6, 30, 7, 3, 1.2) | c.seg(28, 30, 27, 5, 1.2), R['bamboo'], 'flat', base=2)
    c.put(c.ellipse(7, 7, 1.5, 3.6), R['wood'], 'ray', base=2)
    c.put(S.leaf(c, 6.5, 24, 148, 8, 2.4, bend=0.1), R['bamboo'], 'ray', base=3)
    c.put(S.leaf(c, 27.5, 10, 150, 7, 2.2, bend=-0.12), R['bamboo'], 'ray', base=3)
    far_legs = c.seg(11, 24, 9.5, 28.5, 2.0) | c.seg(21.5, 23, 23, 28, 2.0)
    c.put(far_legs, CR_FERRET, 'flat', base=0)
    spine = [(2.5, 27.5), (6, 25.5), (10, 23), (15, 20.6), (20, 20.8), (23.5, 18.5)]
    body = _cr_spine(c, spine, [0.8, 1.6, 3.4, 3.6, 3.3, 2.6])
    c.put(body, CR_FERRET, 'ray', base=2, sep=True)
    belly = body & (c.Y > 22.6) & (c.X > 11) & (c.X < 24)
    c.put(belly, CR_CREAM, 'ray', base=2)
    c.put(body & (c.X < 4.5), CR_FERRET, 'flat', base=0)
    near_legs = c.seg(12.5, 24, 13.5, 28.5, 2.2) | c.seg(20, 23, 19, 28.5, 2.2)
    c.put(near_legs, CR_FERRET, 'across', base=2, sep=True)
    c.put(c.rect(13, 28, 15, 28) | c.rect(18, 28, 20, 28), CR_FERRET, 'flat', base=1)
    head = c.ellipse(25.2, 16.2, 3.6, 2.8) | c.poly([(26, 14), (30.2, 17), (26, 18.6)])
    c.put(head, CR_FERRET, 'ray', base=3, sep=True)
    c.put(c.poly([(24, 17.4), (30.2, 17.2), (27, 19.2), (23.5, 19.4)]) & head, CR_CREAM, 'flat', base=3)
    ear = c.circle(23.2, 13.6, 1.4)
    c.put(ear, CR_FERRET, 'flat', base=2, sep=True)
    c.put(c.rect(25, 15, 27, 16) & head, CR_FERRET, 'flat', base=0)
    c.px(26, 15, '#0B0706', out=CR_FERRET.out)
    c.px(25, 15, '#FFFFFF', out=CR_FERRET.out)
    c.px(29, 17, R['ink'][1], out=CR_FERRET.out)
    c.outline()
    return c


def cloud_marmot():
    """A plump marmot standing up on its haunches: tan back, white face and belly, a cloud-puff tail."""
    c = Canvas(32)
    # cloud-puff tail behind, to the right
    puff = c.circle(25.4, 22.5, 3.8) | c.circle(27, 18, 2.9) | c.circle(23.8, 26.4, 3.0) | c.circle(28, 22.8, 2.4)
    c.put(puff, R['cloud'], 'sphere', base=3, cx=24, cy=20, rx=6, ry=8)
    c.put(c.arc(25.8, 22.2, 1.8, 1.0, 30, 260) & puff, R['cloud'], 'flat', base=1)
    body = c.ellipse(15.5, 20.5, 8.4, 9.0)
    c.put(body, CR_TAN, 'sphere', base=2, sep=True, cx=13, cy=17, rx=11, ry=12)
    belly = c.ellipse(15.5, 22, 5.2, 6.8) & body
    c.put(belly, R['cloud'], 'ray', base=3)
    feet = c.ellipse(11.5, 29, 3, 1.6) | c.ellipse(19.5, 29, 3, 1.6)
    c.put(feet, CR_TAN, 'ray', base=2, sep=True)
    head = c.ellipse(15.5, 10.2, 6.4, 5.4)
    c.put(head, CR_TAN, 'sphere', base=2, sep=True, cx=13.5, cy=8, rx=8, ry=7)
    for s in (1, -1):
        ear = c.circle(15.5 + 4.8 * s, 5.8, 1.6)
        c.put(ear, CR_TAN, 'flat', base=1 if s > 0 else 3, sep=True)
    face = (c.ellipse(15.5, 12.2, 4.0, 2.8) | c.ellipse(15.5, 9.4, 1.6, 2.4)) & head
    c.put(face, R['cloud'], 'ray', base=3)
    for s in (1, -1):
        _cr_eye(c, int(15.5 + 3.0 * s) - (1 if s < 0 else 0), 9, R['ink'][2], w=1, h=2)
    c.put(c.rect(15, 12, 16, 12), R['ink'][1], 'flat', out=CR_TAN.out)
    c.put(c.rect(15, 14, 16, 14), '#FFFFFF', 'flat', out=CR_TAN.out)
    # paws held together at the chest
    paws = c.ellipse(13.5, 17.5, 2.2, 1.7) | c.ellipse(17.5, 17.5, 2.2, 1.7)
    c.put(paws, CR_TAN, 'ray', base=3, sep=True)
    c.pxs([(13, 18), (17, 18)], CR_TAN[1], out=CR_TAN.out)
    c.outline()
    return c


def thunder_hedgehog():
    """A hedgehog in profile under a dome of blue-violet quills, each tipped with a spark."""
    c = Canvas(32)
    cx, cy = 14.5, 22.5
    pts, tips = [], []
    n = 17
    for i in range(n + 1):
        a = math.radians(188 - i * (196 / n))
        r = 13.2 if i % 2 == 0 else 9.6
        x, y = cx + math.cos(a) * r * 1.02, cy - math.sin(a) * r * 1.0
        pts.append((x, y))
        if i % 2 == 0 and 1 <= i <= n - 1:
            tips.append((int(math.floor(x)), int(math.floor(y))))
    quills = c.poly(pts + [(cx + 11, cy + 4), (cx - 12, cy + 4)]) & (c.Y < 27)
    c.put(quills, CR_QUILL, 'ray', base=2)
    # quill lines radiating from the body
    for i in range(1, n, 2):
        a = math.radians(188 - i * (196 / n) - 5)
        c.put(c.bres(int(cx + math.cos(a) * 4), int(cy - math.sin(a) * 4),
                     int(cx + math.cos(a) * 10), int(cy - math.sin(a) * 10)) & erode4(quills), CR_QUILL, 'flat',
              base=1)
    face = c.ellipse(24.5, 23, 4.6, 3.8) | c.poly([(25, 20.5), (30.5, 24.2), (25, 26.5)])
    c.put(face, R['sand'], 'ray', base=3, sep=True, sep_col=CR_QUILL[0])
    c.put(c.rect(29, 23, 30, 24), R['ink'][1], 'flat', out=R['sand'].out)
    c.px(25, 22, R['ink'][0], out=R['sand'].out)
    c.px(26, 22, R['ink'][0], out=R['sand'].out)
    c.px(25, 21, '#FFFFFF', out=R['sand'].out)
    feet = c.rect(9, 27, 11, 28) | c.rect(21, 27, 23, 28)
    c.put(feet, R['sand'], 'flat', base=1, sep=True)
    # sparks on the quill tips
    for (x, y) in tips:
        c.put(c.rect(x, y, x, y) & quills, CR_SPARK[1], 'flat', out=CR_QUILL.out)
    c.outline()
    S.sparkle(c, 15, 4, CR_SPARK[0], CR_SPARK[1], 2)
    S.sparkle(c, 4, 10, CR_SPARK[0], CR_SPARK[1], 1)
    _cr_halo(c, c.pts([(x, y) for (x, y) in tips]), '#9FE8FF', (90,))
    return c


def frost_stoat():
    """A white winter stoat standing up like a sentry: slim S-shaped body, black tail tip, ice-blue eyes."""
    c = Canvas(32)
    tail = _cr_spine(c, [(13, 27), (19, 28.4), (24, 27.2), (27.5, 23.5)], [1.8, 1.8, 1.7, 1.7])
    c.put(tail, CR_SNOW, 'ray', base=2)
    c.put(tail & (c.X > 24.2), R['ink'], 'ray', base=3)
    haunch = c.ellipse(11.5, 24, 4.6, 4.8)
    spine = [(12, 24), (13.5, 19), (16, 14.5), (17.5, 11)]
    body = _cr_spine(c, spine, [4.2, 3.8, 3.1, 2.7]) | haunch
    c.put(body, CR_SNOW, 'sphere', base=2, sep=True, cx=11, cy=15, rx=9, ry=13)
    # the pale belly line and the hind leg's crease
    c.put(c.bres_path([(16, 17), (15, 21), (15, 24)]) & erode4(body), CR_SNOW, 'flat', base=4)
    c.put(c.arc(11.5, 24.5, 3.4, 1.0, 20, 140) & erode4(body), CR_SNOW, 'flat', base=1)
    feet = c.ellipse(11, 29, 3.4, 1.5) | c.ellipse(16.2, 29, 2.2, 1.4)
    c.put(feet, CR_SNOW, 'ray', base=2, sep=True)
    # forepaws tucked against the chest
    paws = c.seg(18.5, 15.5, 20.2, 18.2, 2.0)
    c.put(paws, CR_SNOW, 'ray', base=3, sep=True)
    c.px(20, 19, CR_SNOW[1], out=CR_SNOW.out)
    head = c.ellipse(18, 8.4, 3.8, 3.1) | c.poly([(18.5, 6.2), (24.4, 9.0), (18.5, 11)])
    c.put(head, CR_SNOW, 'sphere', base=3, sep=True, cx=17, cy=7, rx=6, ry=5)
    ear = c.circle(15.4, 5.6, 1.6)
    c.put(ear, CR_SNOW, 'flat', base=2, sep=True)
    c.px(15, 5, R['pink'][2], out=CR_SNOW.out)
    c.put(c.rect(19, 7, 20, 8), R['ice'], 'flat', base=2, out=CR_SNOW.out)
    c.put(c.rect(20, 7, 20, 8), R['ice'][0], 'flat', out=CR_SNOW.out)
    c.px(19, 7, '#FFFFFF', out=CR_SNOW.out)
    c.px(23, 9, R['ink'][1], out=CR_SNOW.out)
    c.put(c.bres(21, 11, 23, 10), CR_SNOW, 'flat', base=1)
    c.outline()
    S.sparkle(c, 27, 5, '#FFFFFF', R['ice'][3], 2)
    S.sparkle(c, 6, 11, '#FFFFFF', R['ice'][3], 1)
    return c


def sand_fox():
    """A small ochre desert fox sitting three-quarter on, huge ears up, its brush tail curled round its feet."""
    c = Canvas(32)
    tail = _cr_spine(c, [(22, 22.5), (25.5, 25), (22, 28), (13, 28.2)], [2.4, 2.6, 2.4, 1.9])
    c.put(tail, CR_OCHRE, 'ray', base=2)
    c.put(tail & (c.X < 14.5), CR_CREAM, 'ray', base=3)
    body = c.ellipse(17, 22.5, 6.4, 6.4)
    c.put(body, CR_OCHRE, 'sphere', base=2, sep=True, cx=15, cy=18, rx=9, ry=10)
    chest = c.ellipse(15, 22, 3.4, 5.0) & body
    c.put(chest, CR_CREAM, 'ray', base=3)
    legs = c.seg(13, 22.5, 12.5, 28, 2.4) | c.seg(17, 23.5, 17, 28, 2.4)
    c.put(legs, CR_OCHRE, 'across', base=3, sep=True)
    c.put(c.rect(11, 28, 18, 28) & legs, CR_CREAM, 'flat', base=3)
    for (bx, ang) in ((10.5, 118), (18.5, 66)):
        ear = S.leaf(c, bx, 11.5, ang, 9.0, 6.4, tip_power=0.55)
        c.put(ear, CR_OCHRE, 'ray', base=3 if ang > 90 else 2, sep=True)
        inner = S.leaf(c, bx + (0.4 if ang > 90 else -0.4), 11.5, ang, 6.8, 3.2, tip_power=0.55)
        c.put(inner & erode4(ear), R['pink'], 'flat', base=2)
    head = c.ellipse(14.5, 14.0, 5.6, 4.4) | c.poly([(11.5, 14.8), (14.5, 19.8), (17.5, 14.8)])
    c.put(head, CR_OCHRE, 'sphere', base=2, sep=True, cx=12.5, cy=12, rx=7, ry=6)
    muzzle = c.poly([(11.8, 15.8), (14.5, 19.8), (17.2, 15.8), (14.5, 14.6)])
    c.put(muzzle & head, CR_CREAM, 'ray', base=3)
    c.put(c.rect(14, 18, 15, 18), R['ink'][1], 'flat', out=CR_OCHRE.out)
    for x in (11, 16):
        _cr_eye(c, x, 14, R['ink'][2], w=2, h=1)
    c.outline()
    return c


def star_gecko():
    """A midnight-blue gecko seen from above, splayed toes and a curling tail, gold star spots glowing faintly."""
    c = Canvas(32)
    legs = c.empty()
    for (a, b, t) in (((19, 11), (24.5, 7.5), (26, 4.5)), ((15, 11), (9.5, 8.5), (7, 5)),
                      ((17.5, 19.5), (23.5, 21), (26.5, 18.5)), ((13.5, 20.5), (9, 24), (9.5, 27.5))):
        legs |= c.polyline([a, b, t], 2.0)
        for (dx, dy) in ((-1.4, -0.6), (1.4, -0.6), (0, 1.4), (0.6, -1.5)):
            legs |= c.circle(t[0] + dx, t[1] + dy, 0.9)
    c.put(legs, CR_MIDNIGHT, 'ray', base=2)
    tail = S.taper_curve(c, (15.5, 21), (12, 30), (4.5, 25.5), 3.6, 1.2)
    tail |= S.taper_curve(c, (4.5, 25.5), (1.8, 21.5), (5.2, 19.8), 1.2, 0.8, k=8)
    c.put(tail, CR_MIDNIGHT, 'ray', base=2, sep=True)
    body = _cr_spine(c, [(17.5, 7.5), (17, 11), (16.5, 16), (16, 21)], [2.6, 2.4, 3.4, 2.4])
    c.put(body, CR_MIDNIGHT, 'ray', base=3, sep=True)
    head = c.ellipse(18, 5.8, 3.4, 3.0)
    c.put(head, CR_MIDNIGHT, 'sphere', base=3, sep=True)
    for x in (15, 20):
        c.put(c.rect(x, 5, x, 5), R['gold'], 'flat', base=3, out=CR_MIDNIGHT.out)
    # gold star spots along the back and tail
    spots = [(16, 10), (18, 13), (15, 15), (17, 18), (14, 23), (10, 26), (6, 24)]
    for (x, y) in spots:
        c.put(c.rect(x, y, x, y), R['starlight'], 'flat', base=4, out=CR_MIDNIGHT.out)
    for (x, y) in spots[:4]:
        c.put(S.star4(c, x, y, 1) & ~c.rect(x, y, x, y) & erode4(body), R['gold'], 'flat', base=2,
              out=CR_MIDNIGHT.out)
    c.outline()
    c.glow('#F3E3A6', (60,))
    S.sparkle(c, 27, 12, '#FFFFFF', R['starlight'][3], 1)
    return c


def radiant_pelt():
    """A pearly pelt folded in half, leg flaps and tail poking out, an iridescent sheen and a few sparkles."""
    c = Canvas(32)
    # leg flaps and the tail poking out of the fold (the stretched hides' pointed flaps, tucked away)
    flaps = (c.poly([(6.5, 10.5), (1.6, 5.8), (5.5, 17.5)]) | c.poly([(25.5, 17.5), (30.4, 24.6), (25, 24)]) |
             c.poly([(7, 24), (3.2, 30.2), (13, 25)]) | c.poly([(18, 25), (21.5, 30.4), (23.5, 25)]))
    c.put(flaps, CR_PELT, 'ray', base=3)
    # the folded bundle with softly notched fur edges, its folded edge rolled over at the top
    body = S.rounded_rect(c, 5, 8, 26, 25, 3)
    body &= ~((c.xi == 5) & (c.yi % 3 == 0)) & ~((c.xi == 26) & (c.yi % 3 == 1)) & ~((c.yi == 25) & (c.xi % 3 == 0))
    c.put(body, CR_PELT, 'ray', base=3, sep=True)
    roll = S.rounded_rect(c, 5, 8, 26, 12, 2)
    c.put(roll, CR_PELT, 'ray', base=3, sep=True, sep_col=CR_PELT[1])
    c.put(c.rect(7, 9, 23, 9) & roll, CR_PELT, 'flat', base=4)
    # fur tufts
    for (x, y) in ((9, 16), (18, 15), (13, 21), (21, 21), (8, 23)):
        c.put(c.bres(x, y, x + 2, y - 1), CR_PELT, 'flat', base=1, only_on=True)
        c.put(c.bres(x, y - 1, x + 1, y - 1), CR_PELT, 'flat', base=4, only_on=True)
    # iridescent sheen: one soft rose-cyan-gold gradient band sweeping across the fur
    inner = erode4(body)
    for (col, off) in (('#F2C4DC', 0), ('#C4ECF6', 2), ('#F8E4A6', 4)):
        c.put(c.diag(-40, 40, 25 + off, 26 + off) & inner & ~roll, col, 'flat', out=CR_PELT.out)
    c.put(c.diag(-40, 40, 17, 18) & erode4(roll), '#C4ECF6', 'flat', out=CR_PELT.out)
    c.put(c.diag(-40, 40, 19, 20) & erode4(roll), '#F8E4A6', 'flat', out=CR_PELT.out)
    c.outline()
    c.glow('#F2E7FF', (60,))
    S.sparkle(c, 27, 4, '#FFFFFF', R['pearl'][3], 2)
    S.sparkle(c, 29, 13, '#FFFFFF', R['lotuspink'][3], 1)
    S.sparkle(c, 21, 17, '#FFFFFF', R['ice'][3], 1)
    return c


for _cr_id, _cr_fn in (('jade_frog', jade_frog), ('mist_hare', mist_hare), ('reed_ferret', reed_ferret),
                       ('cloud_marmot', cloud_marmot), ('thunder_hedgehog', thunder_hedgehog),
                       ('frost_stoat', frost_stoat), ('sand_fox', sand_fox), ('star_gecko', star_gecko),
                       ('radiant_pelt', radiant_pelt)):
    register(FAM, _cr_id, _cr_fn, GROUP)
