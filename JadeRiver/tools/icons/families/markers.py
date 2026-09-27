"""Map and quest markers: 24 art px in Style A ("HD pixel"), shown 1:1 on the world map (its legend, the region
rows, the resource icons) and at 2x where a page asks for a large one.

Each marker is one drawing `draw(p)` in a 24 x 24 icon space, painted with the status family's small-glyph kit
(`status.part`, `orb`, `tone`, `glint`): one bold object in its own colour, and its own silhouette. A body stays
inside x, y = 2 .. 22 so its outline never meets the canvas edge.
"""
from pix import Frame
from registry import drawn
from families.hud import ink_hd, star_hd
from families.status import BONE, FIRE, GOLD, HOLLOW, ICE, JADE, LEAF, QI, RED, SILVER, STORM, WOOD, YELLOW, glint, matte, orb, part, tone

FAM, GROUP = 'markers', 'markers'
ART = 24   # HD (Style A): every marker here is an HD drawing (tools/icons/README.md, "How to convert a family")

STONE, SEA = matte('stone'), matte('sky')


def marker(ident):
    return drawn(FAM, ident, GROUP)


# ============================================================================= HD (Style A, 24 icon space)
def bang(c, cx, y0, y1):
    """An exclamation mark from y0 to y1: its stroke and its dot."""
    return c.poly([(cx - 1.7, y0), (cx + 1.7, y0), (cx + 0.9, y1 - 4.2), (cx - 0.9, y1 - 4.2)]) | c.circle(cx, y1 - 1.4, 1.5)


@marker('quest_main')
def quest_main_hd(p):
    c = p.c
    part(p, c.diamond(12, 12, 10.0, 10.0), GOLD)
    ink_hd(p, bang(c, 12, 5.6, 18.6))
    glint(p, 8.0, 9.4, GOLD, 0.8)


@marker('quest_side')
def quest_side_hd(p):
    c = p.c
    orb(p, 12, 12, 9.4, STORM)
    part(p, bang(c, 12, 5.0, 19.0), BONE, 1)
    glint(p, 7.0, 8.4, STORM, 0.8)


@marker('quest_ready')
def quest_ready_hd(p):
    c = p.c
    hook = c.arc(12, 8.6, 6.4, 3.0, -60, 180) | c.poly([(14.0, 12.4), (16.8, 13.8), (13.6, 16.6), (10.6, 16.6), (10.6, 14.6)])
    part(p, hook | c.circle(12.1, 20.2, 1.9), GOLD, 1)                                  # the question, ready to answer
    glint(p, 6.6, 7.2, GOLD, 0.7)


@marker('npc')
def npc_hd(p):
    c = p.c
    part(p, c.circle(12, 6.8, 4.6), BONE)                                               # the head
    part(p, c.rrect(3.0, 13.0, 21.0, 24.0, 4.2) & c.box(0, 0, 24, 21.6), BONE)          # the shoulders
    tone(p, c.poly([(9.6, 13.0), (14.4, 13.0), (12.0, 17.0)]), BONE, -2)               # the collar
    glint(p, 10.2, 5.0, BONE, 0.8)


@marker('vendor')
def vendor_hd(p):
    c = p.c
    hull = c.poly([(2.2, 9.0), (5.8, 8.0), (8.0, 12.2), (16.0, 12.2), (18.2, 8.0), (21.8, 9.0), (20.4, 16.0), (17.2, 19.6),
                   (6.8, 19.6), (3.6, 16.0)])
    part(p, hull, GOLD)                                                                  # the ingot's boat
    part(p, c.circle(12, 10.6, 4.8) & c.box(0, 0, 24, 14.0), GOLD, 1)                   # its raised middle
    glint(p, 10.4, 8.2, GOLD, 0.8)


@marker('healer')
def healer_hd(p):
    c = p.c
    part(p, c.circle(12, 16.2, 6.0) | c.circle(12, 8.4, 3.8), RED)                     # the medicine gourd
    part(p, c.rrect(10.4, 2.0, 13.6, 5.0, 0.8), WOOD)                                   # its stopper
    part(p, c.rrect(7.8, 10.6, 16.2, 12.6, 0.8), BONE, -1)                              # the cord at its waist
    tone(p, c.box(11.0, 13.8, 13.0, 20.2) | c.box(8.8, 16.0, 15.2, 18.0), BONE, 1)     # the healer's mark
    glint(p, 9.2, 7.6, RED, 0.7)


@marker('forge_marker')
def forge_marker_hd(p):
    c = p.c
    part(p, c.poly([(2.0, 10.4), (5.0, 8.4), (20.0, 8.4), (20.0, 12.6), (5.0, 12.6)]), SILVER)   # the anvil's face
    part(p, c.box(8.4, 12.6, 15.6, 16.6), SILVER, -1)
    part(p, c.rrect(5.0, 16.4, 19.0, 20.6, 0.8), SILVER)
    part(p, star_hd(c, 18.4, 4.6, 4, 3.2, 1.1), FIRE, 1)                               # a spark off the work
    glint(p, 6.0, 9.4, SILVER, 0.6)


@marker('shrine_marker')
def shrine_marker_hd(p):
    c = p.c
    part(p, c.box(5.6, 9.6, 18.4, 19.4), WOOD)                                           # the shrine
    ink_hd(p, c.box(9.0, 11.6, 15.0, 19.4))
    tone(p, c.circle(12.0, 15.0, 1.8), YELLOW, 1)                                        # the lamp inside
    part(p, c.poly([(12, 2.4), (2.0, 8.2), (2.0, 10.2), (22.0, 10.2), (22.0, 8.2)]), RED)   # the roof
    part(p, c.rrect(3.4, 19.2, 20.6, 21.8, 0.8), STONE)                                  # the step
    glint(p, 7.0, 7.4, RED, 0.6)


def gate_hd(p, mat):
    """A portal: its ring, the eddy turning inside, and its keystone."""
    c = p.c
    part(p, c.ring(12, 12, 9.8, 2.6), mat)
    tone(p, c.arc(12, 12, 5.6, 1.6, 20, 200), mat, 1)
    tone(p, c.arc(12, 12, 5.6, 1.6, 200, 20), mat, -1)
    glint(p, 6.4, 6.8, mat, 0.7)


@marker('portal_marker')
def portal_marker_hd(p):
    c = p.c
    part(p, c.circle(12, 12, 7.6), QI, -1)                                               # the open way
    gate_hd(p, QI)
    part(p, c.circle(12, 12, 2.0), QI, 2)


@marker('portal_sealed')
def portal_sealed_hd(p):
    c = p.c
    part(p, c.circle(12, 12, 7.6), HOLLOW, -2)                                           # the way shut
    gate_hd(p, HOLLOW)
    part(p, c.rrect(2.0, 10.2, 22.0, 13.8, 1.0), RED)                                    # the seal bar across it
    ink_hd(p, c.box(11.2, 10.8, 12.8, 13.2))


@marker('teleport_marker')
def teleport_marker_hd(p):
    c = p.c
    part(p, c.ellipse(12, 18.6, 9.4, 3.2), JADE, -1)                                     # the stone's base
    part(p, c.poly([(9.0, 18.4), (9.8, 6.0), (12.0, 2.4), (14.2, 6.0), (15.0, 18.4)]), JADE, 1)   # the standing stone
    tone(p, c.poly([(11.2, 8.0), (12.8, 8.0), (12.0, 14.4)]), JADE, -2)                  # its rune
    glint(p, 11.0, 5.6, JADE, 0.6)


@marker('elite_crown')
def elite_crown_hd(p):
    c = p.c
    band = c.box(3.4, 14.0, 20.6, 19.4)
    for (x0, xt, x1, yt) in ((2.4, 3.6, 8.6, 5.4), (7.4, 12.0, 16.6, 3.0), (15.4, 20.4, 21.6, 5.4)):
        band |= c.poly([(x0, 15.0), (xt, yt), (x1, 15.0)])
    part(p, band, GOLD)
    part(p, c.circle(12.0, 16.6, 1.8), RED, 1)                                            # the gem
    glint(p, 5.2, 15.6, GOLD, 0.7)


@marker('boss_skull')
def boss_skull_hd(p):
    c = p.c
    part(p, c.ellipse(12, 10.4, 8.8, 8.0) | c.rrect(7.0, 14.0, 17.0, 21.6, 1.6), BONE)
    for x in (8.2, 15.8):
        ink_hd(p, c.ellipse(x, 11.4, 2.4, 2.2))
        tone(p, c.circle(x, 11.4, 1.0), RED, 1)                                          # the eyes, lit red
    ink_hd(p, c.poly([(11.0, 16.6), (13.0, 16.6), (12.0, 14.6)]))
    for x in (9.6, 12.0, 14.4):
        ink_hd(p, c.box(x - 0.5, 18.8, x + 0.5, 21.6))                                    # the teeth
    glint(p, 6.4, 7.2, BONE, 0.8)


@marker('herb_marker')
def herb_marker_hd(p):
    c = p.c
    part(p, c.leaf(5.0, 19.0, 45, 18.0, 9.0, 0.05, tip_power=0.7), LEAF)
    fr = Frame((5.0, 19.0), 45.0)
    p.line([fr.P(1.4, 0.0), fr.P(14.0, 0.0)], LEAF, -2, 1.0)                              # the midrib
    part(p, c.taper((5.6, 18.4), (4.0, 20.0), (2.4, 21.8), 2.0, 1.4), LEAF, -1)           # the stem
    glint(p, 9.6, 10.6, LEAF, 0.7)


@marker('ore_marker')
def ore_marker_hd(p):
    c = p.c
    part(p, c.poly([(9.0, 16.0), (8.4, 7.6), (11.2, 2.2), (13.8, 7.6), (13.4, 16.0)]), ICE, 1)   # the crystal
    part(p, c.poly([(14.0, 16.0), (14.6, 10.4), (17.0, 7.4), (18.8, 10.6), (18.0, 16.0)]), ICE)
    part(p, c.ellipse(12, 20.6, 10.0, 5.2) & c.box(0, 0, 24, 21.8), STONE)                 # the rock it grows from
    glint(p, 10.6, 5.6, ICE, 0.6)


@marker('fish_marker')
def fish_marker_hd(p):
    c = p.c
    part(p, c.poly([(8.0, 12.0), (2.2, 6.6), (3.6, 12.0), (2.2, 17.4)]), SEA, -1)          # the tail
    body = c.ellipse(13.6, 12.0, 8.2, 5.4)
    part(p, body | c.poly([(10.0, 7.4), (13.4, 4.0), (16.4, 7.4)]), SEA)                   # the body and its fin
    ink_hd(p, c.circle(18.4, 10.8, 1.1))                                                     # the eye
    tone(p, c.arc(16.0, 12.0, 4.4, 1.0, 110, 250) & body, SEA, -2)                          # the gill
    glint(p, 11.0, 9.4, SEA, 0.7)


@marker('player_arrow')
def player_arrow_hd(p):
    c = p.c
    part(p, c.poly([(12, 2.0), (21.2, 21.4), (12, 16.4), (2.8, 21.4)]), JADE, 1)             # you, and the way you face
    tone(p, c.poly([(12, 5.4), (12, 15.2), (5.8, 18.8)]), JADE, 1)
    glint(p, 11.0, 6.8, JADE, 0.6)
