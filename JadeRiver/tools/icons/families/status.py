"""Status icons: 24 art px in Style A ("HD pixel"), shown 1:1 in the HUD's status row, with a native 12 px render for
the row over an enemy's name.

Colour language: injuries carry a red crack, cut into the silhouette as a notch; stability is one stepped foundation
that grows a tier at a time and changes colour (red -> yellow -> jade -> gold); debuffs use warm or sickly hues; buffs
add a green up-arrow; cultivation states use jade and gold. Colour never carries the meaning alone: every glyph has
its own silhouette (the foundation shows only the tiers it has, a buff is its object with the arrow).

Each icon is one drawing `draw(p)` in a 24 x 24 icon space (tools/icons/README.md, "HD drawing model"): parts painted
with `part` (a palette material with a lit edge and a shade edge, the painter's selective outline), details as decals,
one glint. A body stays inside x, y = 2 .. 22 so its outline never meets the canvas edge at 24 or at 12.
"""
import math

from pix import Frame
from palette import M, R, mat7
from registry import drawn
import shapes as S
from families.hud import XY, arrow_hd, ink_hd, star_hd
from families.pills import _spiral

FAM, GROUP = 'status', 'status'
ART = 24   # HD (Style A): every icon here is an HD drawing (tools/icons/README.md, "How to convert a family")


def icon(ident):
    return drawn(FAM, ident, GROUP)


# ============================================================================= HD (Style A, 24 icon space)
# Materials: the palette ramps as seven steps, matte so the small glyphs keep their colour at 12 px.
def matte(name):
    return mat7(R[name], 'matte')


RED, CRACK, GOLD, JADE, QI = matte('red'), matte('seal'), M('gold'), M('jade'), matte('qi')
BONE, HOLLOW, MIST, VIOLET, WOOD = matte('bone'), matte('hollow'), matte('mist'), matte('violet'), matte('wood')
VENOM, LEAF, FIRE, ICE, YELLOW = matte('venom'), matte('leaf'), matte('fire'), matte('ice'), matte('yellow')
STORM, SILVER, PAPER = matte('storm'), M('silver'), matte('porcelain')


def part(p, m, mat, base=0):
    """A part in `mat`: its colour, a 1-px lit edge and shade edge, the outline from the painter."""
    return p.part(m, mat, 'bevel', base=base, sep=True, hw=1, sw=1, rim=False)


def orb(p, cx, cy, r, mat, base=0):
    """A round part shaded as a sphere."""
    return p.part(p.c.circle(cx, cy, r), mat, 'sphere', base=base, sep=True, rim=False, cx=cx, cy=cy, rx=r, ry=r)


def tone(p, m, mat, lv):
    """A detail in one level of a material, on the painted pixels."""
    return p.decal(m, mat, lv)


def glint(p, x, y, mat, r=0.9):
    """The one highlight: the material's specular."""
    return p.decal(p.c.circle(x, y, r), mat, 3)


def crack(p, pts, w=1.6):
    """The injury's red crack: a notch cut into the silhouette where it starts, then a jagged red line."""
    c = p.c
    (x0, y0), (x1, y1) = pts[0], pts[1]
    p.erase(c.poly([(x0 - 1.6, y0 - 0.6), (x0 + 1.6, y0 - 0.6), (x1, y1)]) & c.a)
    p.line(pts, CRACK, 0, w)


def buff_arrow(p):
    """A buff's green up-arrow, at the upper right of its object."""
    part(p, arrow_hd(p.c, (18.6, 14.0), (18.6, 2.0), 1.7, 4.4, 5.0), LEAF, 1)


def lens(c, cx, cy, rx, ry):
    """An eye's almond: two arcs meeting at the corners."""
    d = (rx * rx - ry * ry) / (2.0 * ry)
    r = ry + d
    return c.circle(cx, cy + d, r) & c.circle(cx, cy - d, r)


# --------------------------------------------------------------------------- injuries: the red crack
@icon('injury_body')
def injury_body_hd(p):
    c = p.c
    fr = Frame((4.6, 19.4), 45.0)
    L = 20.8
    shaft = fr.prof(c, [(2.0, 1.9), (L - 2.0, 1.9)])
    knobs = c.empty()
    for t in (1.6, L - 1.6):
        for w in (-1.7, 1.7):
            knobs |= c.circle(*fr.P(t, w), 2.2)
    part(p, shaft | knobs, BONE)
    crack(p, [fr.P(11.0, -2.6), fr.P(10.0, -0.4), fr.P(11.6, 0.6), fr.P(10.6, 2.6)])
    glint(p, *fr.P(4.0, -2.0), BONE)


@icon('injury_meridian')
def injury_meridian_hd(p):
    c = p.c
    rp = lambda a, r: (12 + r * math.cos(math.radians(a)), 18.0 - r * math.sin(math.radians(a)))
    nodes = [rp(a, 8.0) for a in (165, 90, 15)]                 # the acupoints along it
    channel = c.arc(12, 18.0, 9.6, 3.2, 12, 168)
    for x, y in nodes:
        channel |= c.circle(x, y, 2.6)
    part(p, channel, QI)
    p.erase(c.sector(12, 18.0, 13.0, 44, 58))               # the channel broken
    p.line([rp(50, 6.6), rp(55, 7.8), rp(47, 9.0), rp(52, 9.8)], CRACK, 0, 1.4, only_on=False)   # the red crack across the gap
    for x, y in nodes:
        tone(p, c.circle(x, y, 1.0), QI, 2)
    glint(p, 5.6, 13.6, QI, 0.7)


@icon('injury_soul')
def injury_soul_hd(p):
    c = p.c
    orb(p, 12, 12.5, 9.2, VIOLET)
    tone(p, c.ring(12, 12.5, 5.6, 1.2), VIOLET, -1)                                 # the soul's inner ring
    crack(p, [(14.5, 3.4), (12.4, 8.0), (14.6, 11.4), (11.6, 15.4), (13.0, 19.0)])
    glint(p, 8.4, 8.6, VIOLET, 1.1)


# --------------------------------------------------------------------------- stability: the stepped foundation
TIERS = ((2.0, 22.0, 17.5, 21.5), (4.5, 19.5, 13.0, 17.5), (7.0, 17.0, 8.5, 13.0), (9.5, 14.5, 3.5, 8.5))   # x0, x1, y0, y1
STABILITY = {'stability_unstable': (1, RED), 'stability_settling': (2, YELLOW), 'stability_stable': (3, JADE),
             'stability_solid': (4, GOLD)}


def foundation_hd(p, tiers, mat):
    """The foundation built to `tiers` of its four: each tier a slab with its lit top; the unstable one is cracked,
    the solid one built to its capstone."""
    c = p.c
    for x0, x1, y0, y1 in TIERS[:tiers]:
        part(p, c.box(x0, y0, x1, y1), mat)
    if tiers == 1:
        p.erase(c.poly([(9.2, 17.0), (12.2, 17.0), (10.2, 19.6)]))
        p.line([(10.6, 18.0), (12.4, 19.4), (11.0, 21.6)], CRACK, 0, 1.4)
        p.erase(c.poly([(19.0, 22.0), (22.5, 22.0), (22.5, 19.5)]))                 # a corner fallen away
    x0, _, y0, _ = TIERS[tiers - 1]
    glint(p, x0 + 1.4, y0 + 1.2, mat, 0.7)


for _id, (_n, _mat) in STABILITY.items():
    icon(_id)(lambda p, n=_n, mat=_mat: foundation_hd(p, n, mat))


# --------------------------------------------------------------------------- body and pill states
@icon('toxicity')
def toxicity_hd(p):
    orb(p, 10.0, 14.5, 7.4, VENOM)                                                # the pill, gone sickly
    for x, y, r in ((17.6, 7.4, 2.6), (20.0, 2.6 + 1.2, 1.5)):
        part(p, p.c.circle(x, y, r), VIOLET)                                        # the bubbles rising off it
    tone(p, p.c.circle(12.0, 17.0, 1.4) | p.c.circle(7.6, 17.6, 0.9), VENOM, -2)
    glint(p, 7.4, 11.6, VENOM)


@icon('hollowing')
def hollowing_hd(p):
    c = p.c
    moon = c.circle(12, 12, 9.6) & ~c.circle(15.6, 9.6, 7.6)
    part(p, moon, HOLLOW)
    part(p, c.circle(15.4, 10.0, 1.8), MIST, 1)                                      # the mote left in the hollow
    glint(p, 5.4, 11.0, HOLLOW, 0.8)


@icon('composure')
def composure_hd(p):
    c = p.c
    part(p, S.drop(c, 12, 8.2, 3.3, 6.4), QI)
    for y, x0, x1 in ((13.2, 2.5, 21.5), (16.8, 5.0, 19.0), (20.2, 7.5, 16.5)):      # the still water under it
        part(p, c.rrect(x0, y, x1, y + 2.2, 1.0), JADE)
    glint(p, 10.8, 7.4, QI, 0.8)


@icon('meditating')
def meditating_hd(p):
    c = p.c
    part(p, c.arc(12, 11.0, 9.6, 1.8, 10, 170), GOLD)                                # the halo
    part(p, c.poly([(12, 9.5), (6.0, 18.0), (18.0, 18.0)]) | c.ellipse(12, 17.0, 6.6, 2.8), JADE)   # the seated figure
    part(p, c.circle(12, 7.6, 2.8), JADE)
    part(p, c.rrect(3.0, 18.2, 21.0, 21.8, 1.2), GOLD, -1)                           # the cushion
    glint(p, 11.0, 6.6, JADE, 0.7)


@icon('consolidating')
def consolidating_hd(p):
    c = p.c
    part(p, c.diamond(12, 12, 9.8, 9.8), GOLD)
    tone(p, c.diamond(12, 12, 5.8, 5.8) & ~c.diamond(12, 12, 4.2, 4.2), GOLD, -2)   # the settling rings
    part(p, c.diamond(12, 12, 2.8, 2.8), JADE, 1)                                    # the core
    glint(p, 8.0, 8.8, GOLD, 0.8)


@icon('bottleneck')
def bottleneck_hd(p):
    c = p.c
    part(p, c.circle(12, 15.8, 6.2) | c.box(9.6, 5.0, 14.4, 12.0), HOLLOW)          # the bottle and its neck
    part(p, c.rrect(8.6, 2.6, 15.4, 5.6, 1.0), HOLLOW, -1)                          # its lip
    part(p, c.rrect(2.2, 8.0, 21.8, 11.2, 1.0), RED)                                # the bar across the neck
    glint(p, 8.8, 14.0, HOLLOW)


@icon('heart_demon')
def heart_demon_hd(p):
    c = p.c
    horns = c.taper((7.2, 9.0), (3.0, 7.0), (3.4, 2.4), 2.6, 1.0) | c.taper((16.8, 9.0), (21.0, 7.0), (20.6, 2.4), 2.6, 1.0)
    part(p, horns, BONE, -1)
    part(p, c.ellipse(12, 13.8, 7.6, 7.8) & c.box(0, 0, 24, 21.2) | c.poly([(7.0, 19.0), (17.0, 19.0), (12.0, 22.0)]), RED)
    for sx in (-1, 1):                                                                 # the slanted eyes
        tone(p, c.poly([(12 + sx * 1.4, 12.6), (12 + sx * 5.4, 10.6), (12 + sx * 4.6, 13.8)]), YELLOW, 1)
    ink_hd(p, c.box(9.0, 16.6, 15.0, 18.0))                                           # the mouth
    tone(p, c.poly([(10.0, 16.6), (11.0, 16.6), (10.5, 18.4)]) | c.poly([(13.0, 16.6), (14.0, 16.6), (13.5, 18.4)]), BONE, 1)
    glint(p, 7.8, 9.8, RED, 0.8)


def head(c, x, y, a, L, W):
    """An arrowhead at (x, y) pointing `a` degrees (0 right, 90 up): `L` long, `W` to either side."""
    dx, dy = math.cos(math.radians(a)), -math.sin(math.radians(a))
    return c.poly([(x - dy * W, y + dx * W), (x + dx * L, y + dy * L), (x + dy * W, y - dx * W)])


@icon('qi_deviation')
def qi_deviation_hd(p):
    c = p.c
    r = 8.2
    at = lambda a: (12 + r * math.cos(math.radians(a)), 12 - r * math.sin(math.radians(a)))
    part(p, c.arc(12, 12, r + 1.4, 2.8, 105, 330) | head(c, *at(330), 60, 4.2, 3.4), QI)      # the circuit, running on
    part(p, c.arc(12, 12, r + 1.4, 2.8, 60, 105) | head(c, *at(62), -30, 4.2, 3.4), RED)     # the arm that turned back
    part(p, c.circle(12, 12, 2.4), QI, 1)
    glint(p, 5.4, 9.4, QI, 0.7)


@icon('sense_locked')
def sense_locked_hd(p):
    c = p.c
    part(p, lens(c, 12, 12, 10.0, 5.8), PAPER)
    part(p, c.circle(12, 12, 3.9), VIOLET)
    ink_hd(p, c.circle(12, 12, 1.6))
    part(p, c.rrect(10.6, 2.0, 13.4, 22.0, 1.0), VIOLET, -1)                        # the bolt shot through it
    glint(p, 6.2, 11.2, PAPER, 0.7)


@icon('poison_body')
def poison_body_hd(p):
    c = p.c
    part(p, c.circle(12, 5.4, 3.4), VENOM)                                            # the head
    part(p, c.rrect(3.0, 10.0, 21.0, 22.0, 3.6) & c.box(0, 0, 24, 21.6), VENOM)      # the shoulders
    tone(p, S.drop(c, 12, 17.4, 2.4, 4.8), VIOLET, 0)                                  # the poison it carries
    glint(p, 10.6, 4.2, VENOM, 0.8)


@icon('exhausted')
def exhausted_hd(p):
    c = p.c
    part(p, arrow_hd(c, (13.5, 3.0), (13.5, 21.5), 3.0, 7.6, 8.0), HOLLOW)            # the strength running out
    part(p, S.drop(c, 5.4, 9.0, 2.7, 5.4), QI)                                        # a bead of sweat
    glint(p, 12.2, 4.8, HOLLOW, 0.7)


@icon('spawn_protection')
def spawn_protection_hd(p):
    c = p.c
    part(p, c.ring(12, 12, 10.0, 1.8), GOLD)                                           # the ward's bubble
    part(p, c.poly([(7.4, 7.2), (16.6, 7.2), (16.6, 12.4), (12, 17.4), (7.4, 12.4)]), GOLD, 1)   # the charm in it
    tone(p, c.box(11.2, 8.2, 12.8, 15.2), GOLD, -2)
    glint(p, 5.4, 6.6, GOLD, 0.8)


# --------------------------------------------------------------------------- combat statuses
@icon('poison')
def poison_hd(p):
    c = p.c
    part(p, S.drop(c, 12, 14.2, 7.0, 12.2), VENOM)
    tone(p, c.circle(14.0, 16.0, 2.2) | c.circle(9.6, 18.4, 1.2), VENOM, -2)           # the bubbles in it
    glint(p, 8.8, 12.4, VENOM, 1.0)


@icon('burn')
def burn_hd(p):
    c = p.c
    part(p, S.flame(c, 12, 21.6, 16.0, 19.4, 0.6), FIRE)
    part(p, S.flame(c, 12, 20.6, 7.0, 9.6, 0.2), FIRE, 2)                             # the hot heart
    glint(p, 11.4, 16.4, FIRE, 0.7)


@icon('slow')
def slow_hd(p):
    c = p.c
    part(p, c.poly([(5.6, 4.4), (18.4, 4.4), (12.6, 12.0), (18.4, 19.6), (5.6, 19.6), (11.4, 12.0)]), ICE, -1)   # the glass
    tone(p, c.poly([(8.4, 6.8), (15.6, 6.8), (12.0, 10.8)]) | c.poly([(12.0, 15.2), (16.0, 18.4), (8.0, 18.4)]), YELLOW, 1)   # the sand
    for y in (2.0, 19.6):
        part(p, c.rrect(3.2, y, 20.8, y + 2.6, 1.0), WOOD)                            # the caps
    glint(p, 7.6, 6.0, ICE, 0.6)


@icon('stun')
def stun_hd(p):
    c = p.c
    part(p, c.ring(12, 17.2, 9.2, 2.2, ry=3.6), YELLOW, -1)                           # the daze circling
    for x, y, r in ((5.0, 8.6, 3.6), (12.0, 5.0, 4.6), (19.0, 8.6, 3.6)):
        part(p, star_hd(c, x, y, 4, r, r * 0.36), YELLOW, 1)
    glint(p, 12.0, 5.0, YELLOW, 0.6)


@icon('root')
def root_hd(p):
    c = p.c
    for end, mid, w in (((3.2, 21.0), (7.0, 13.6), 2.2), ((20.8, 21.0), (17.0, 13.6), 2.2), ((9.0, 22.0), (10.4, 16.0), 1.8),
                        ((15.2, 22.0), (13.8, 16.0), 1.8)):
        part(p, c.taper((12.0, 11.0), mid, end, 3.2, w * 0.5 + 0.4) & c.box(0, 0, 24, 21.6), WOOD)           # the roots gripping down
    part(p, c.rrect(8.6, 2.2, 15.4, 13.0, 1.2), WOOD)                                 # the stump
    tone(p, c.box(10.8, 3.4, 11.8, 11.6), WOOD, -2)
    glint(p, 9.8, 3.6, WOOD, 0.6)


@icon('bleed')
def bleed_hd(p):
    c = p.c
    part(p, c.rrect(2.4, 2.4, 21.6, 6.4, 1.8), RED, -1)                               # the wound
    for x, y, r in ((6.0, 11.6, 2.2), (12.4, 17.6, 2.8), (18.4, 12.6, 2.0)):
        part(p, S.drop(c, x, y, r, r * 2.4) | c.box(x - 0.9, 4.0, x + 0.9, y - r), RED)   # the drips running from it
    glint(p, 11.4, 16.6, RED, 0.7)


@icon('freeze')
def freeze_hd(p):
    c = p.c
    flake = c.empty()
    for k in range(6):
        fr = Frame((12, 12), 90 + 60 * k)
        flake |= fr.prof(c, [(0.0, 1.3), (9.8, 1.1)])
        for t in (5.4,):
            flake |= c.seg(*fr.P(t, 0), *fr.P(t + 2.8, 2.6), 1.4) | c.seg(*fr.P(t, 0), *fr.P(t + 2.8, -2.6), 1.4)
    part(p, flake, ICE)
    part(p, c.circle(12, 12, 2.4), ICE, 2)
    glint(p, 11.4, 11.4, ICE, 0.6)


@icon('shock')
def shock_hd(p):
    c = p.c
    part(p, c.poly([(15.0, 2.0), (5.2, 13.2), (11.0, 13.2), (8.4, 22.0), (18.8, 10.0), (12.8, 10.0), (16.6, 2.0)]), YELLOW, 1)
    glint(p, 14.2, 3.8, YELLOW, 0.6)


@icon('qi_seal')
def qi_seal_hd(p):
    c = p.c
    orb(p, 12, 12, 7.6, QI)
    part(p, c.seg(3.0, 3.0, 21.0, 21.0, 3.0) | c.seg(21.0, 3.0, 3.0, 21.0, 3.0), RED)   # the seal struck across it
    glint(p, 8.6, 12.0, QI, 0.8)


@icon('vulnerable')
def vulnerable_hd(p):
    c = p.c
    shield = c.poly([(3.2, 3.0), (20.8, 3.0), (20.8, 11.4), (12, 21.8), (3.2, 11.4)])
    split = c.poly([(12.6, 1.0), (10.8, 7.6), (13.4, 12.2), (11.0, 23.0), (0, 23.0), (0, 1.0)])
    part(p, shield & split, SILVER)
    part(p, (shield & ~split & ~c.poly([(12.6, 1.0), (14.2, 1.0), (12.2, 7.6), (14.8, 12.2), (12.6, 23.0), (11.0, 23.0),
                                         (13.4, 12.2), (10.8, 7.6)])), SILVER, -1)      # the half split away, a step darker
    glint(p, 5.4, 5.2, SILVER, 0.7)


@icon('confusion')
def confusion_hd(p):
    c = p.c
    part(p, c.polyline(_spiral(12, 12, 9.4, 0.9, 1.45, 48), 2.6), VIOLET)
    glint(p, 19.2, 9.4, VIOLET, 0.6)


@icon('fear')
def fear_hd(p):
    c = p.c
    X, Y = XY(c)
    hem = 19.6 + 1.8 * ((X * 0.5) % 2.0 < 1.0)                                       # the ragged hem
    ghost = (c.circle(12, 10.0, 8.4) | (c.box(3.6, 10.0, 20.4, 22.0) & (Y < hem)))
    part(p, ghost, PAPER)
    for x in (8.6, 15.4):
        ink_hd(p, c.ellipse(x, 9.4, 1.6, 2.2))                                         # the staring eyes
    ink_hd(p, c.ellipse(12, 15.0, 1.8, 2.4))                                           # the open mouth
    glint(p, 7.0, 5.6, PAPER, 0.7)


# --------------------------------------------------------------------------- buffs: the object and the green arrow
@icon('buff_attack')
def buff_attack_hd(p):
    c = p.c
    part(p, c.poly([(7.4, 3.0), (10.2, 6.0), (10.2, 15.0), (4.6, 15.0), (4.6, 6.0)]), SILVER)   # the blade
    tone(p, c.box(7.0, 5.4, 7.8, 14.6), SILVER, 2)
    part(p, c.rrect(1.8, 15.0, 13.0, 17.4, 0.8), GOLD)                                 # the guard
    part(p, c.box(6.2, 17.4, 8.6, 21.0), WOOD)                                         # the grip
    part(p, c.circle(7.4, 21.4, 1.5), GOLD)
    buff_arrow(p)


@icon('buff_defense')
def buff_defense_hd(p):
    c = p.c
    part(p, c.poly([(2.4, 6.0), (15.4, 6.0), (15.4, 13.0), (8.9, 21.6), (2.4, 13.0)]), STORM)
    tone(p, c.poly([(5.0, 8.2), (8.9, 8.2), (8.9, 17.6), (5.0, 12.6)]), STORM, 1)     # the lit half
    buff_arrow(p)
    glint(p, 4.6, 8.0, STORM, 0.6)


@icon('buff_speed')
def buff_speed_hd(p):
    c = p.c
    for x in (2.6, 8.8):                                                                # the chevrons running on
        part(p, c.poly([(x, 7.6), (x + 3.2, 7.6), (x + 7.6, 14.8), (x + 3.2, 22.0), (x, 22.0), (x + 4.4, 14.8)]), JADE, 1)
    buff_arrow(p)
    glint(p, 4.0, 8.8, JADE, 0.6)
