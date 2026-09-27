"""HUD glyphs: 32 art px in Style A ("HD pixel"), a pale-gold face with an ink outline, shown 1:1 in the button
rings and at 2x in the attack ring and on the menu tiles.

Each glyph is one drawing `draw(p)` in a 32 x 32 icon space (tools/icons/README.md, "HD drawing model"): its face is
`face_hd` (a lit edge, a warm shade edge), its details ink or warm marks on that face, and it has one highlight.
The weapons of the attack button share the `DIAG` frame and the shaft, blade and grip builders; the button glyphs
share the book, bust, arrow and chest templates. A glyph's body stays inside x, y = 2 .. 30 so its outline never
meets the canvas edge.
"""
import math

import numpy as np

from pix import Frame, Ramp, erode4
from palette import mat7
from registry import drawn

FAM, GROUP = 'hud', 'hud'
ART = 32   # HD (Style A): every glyph here is an HD drawing (tools/icons/README.md, "How to convert a family")
INK = '#071015'


def glyph(ident):
    """Register HUD glyph `ident`: its HD drawing is the icon."""
    return drawn(FAM, ident, GROUP)


# ============================================================================= HD (Style A, 32 icon space)
# Today's language one step richer: a pale-gold face with a lit edge and a warm shade edge, one highlight, the ink
# outline from the painter. Every glyph is described once in a 32 x 32 icon space, its body inside x, y = 2 .. 30
# so the outline never meets the canvas edge; the game draws it 1:1 in a button ring and at 2x in the attack ring
# and on the menu tiles. Light from the top left; no rim light on gold glyphs.
GOLD_HD = mat7(Ramp(['#6E4A1C', '#9A6A35', '#E5B84C', '#FFE6A1', '#FFF6D6'], INK), 'gold')
DIAG = Frame((3.0, 29.0), 45.0)     # the diagonal every weapon lies on, lower left to upper right


def face_hd(p, m, base=1):
    """A pale-gold face (base 1): a lit edge, a warm shade edge and the ink outline; base 0 is a warm-gold part."""
    return p.part(m, GOLD_HD, 'bevel', base=base, sep=True, hw=1, sw=1, rim=False)


def warm_hd(p, m):
    return face_hd(p, m, 0)


def ink_hd(p, m):
    """An engraved ink detail on the face."""
    return p.decal(m, INK)


def mark_hd(p, m, lv=0):
    """A warm-gold (lv 0) or bronze (lv -1) detail on the face."""
    return p.decal(m, GOLD_HD, lv)


def glint_hd(p, x, y, r=1.0):
    """The one highlight."""
    return p.decal(p.c.circle(x, y, r), GOLD_HD, 3)


def XY(c):
    """Pixel centres in icon space."""
    return c.X / c.s, c.Y / c.s


def star_hd(c, cx, cy, n, r_out, r_in, turn=0.0):
    """An n-point star, the first point up (`turn` degrees clockwise)."""
    pts = []
    for k in range(2 * n):
        a = math.radians(90.0 - turn - 180.0 * k / n)
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return c.poly(pts)


def tilted_ring(c, cx, cy, rx, ry, angle, w):
    """A tilted ellipse ring (its major axis `angle` degrees up from the right) and the half of it nearer the viewer."""
    X, Y = XY(c)
    a = math.radians(angle)
    dx, dy = X - cx, Y - cy
    u = dx * math.cos(a) - dy * math.sin(a)
    v = dx * math.sin(a) + dy * math.cos(a)
    outer = (u / rx) ** 2 + (v / ry) ** 2 <= 1.0
    inner = (u / max(0.01, rx - w)) ** 2 + (v / max(0.01, ry - w)) ** 2 <= 1.0
    ring = outer & ~inner
    return ring, ring & (v > 0)


def wave_hd(c, x0, x1, y, amp, period, w, phase=0.0):
    """A wavy line from x0 to x1 about y."""
    pts = [(x, y + amp * math.sin((x - x0 + phase) / period * 2 * math.pi)) for x in np.linspace(x0, x1, 25)]
    return c.polyline(pts, w)


# --------------------------------------------------------------------------- weapon builders on the diagonal
def shaft_hd(p, fr, t0, t1, hw, base=1):
    """A round shaft along the frame (a spear, a staff, a flute)."""
    m = fr.prof(p.c, [(t0, hw), (t1, hw)])
    return p.cylinder(fr, m, hw, GOLD_HD, base=base, sep=True, rim=False)


def blade_hd(p, fr, t0, t1, hw, tip):
    """A blade with its lit face, ridge and shade face: half-width `hw` from t0, the point from `tip` to t1."""
    m = fr.prof(p.c, [(t0, hw), (tip, hw), (t1, 0.0)])

    def half(t):
        return np.where(t > tip, np.clip(hw * (t1 - t) / (t1 - tip), 0, hw), hw)
    return p.cylinder(fr, m, half, GOLD_HD, base=1, ridge=True, sep=True, rim=False)


def grip_hd(p, fr, t0, t1, hw, wrap=True):
    """A grip with its bronze wrap every other 2 px."""
    c = p.c
    g = face_hd(p, fr.prof(c, [(t0, hw), (t1, hw)]))
    if wrap:
        t = fr.along(c)[0]
        mark_hd(p, g & (np.floor((t - t0) / 2.0).astype(int) % 2 == 0) & erode4(g), -1)
    return g


@glyph('fist')
def fist_hd(p):
    c = p.c
    knuckles = c.empty()
    for x in (10.2, 14.6, 19.0, 23.4):
        knuckles |= c.circle(x, 9.4, 2.5)
    face_hd(p, c.rrect(7, 9, 25, 22, 3) | knuckles)
    for x in (12.4, 16.8, 21.2):                                          # the fingers
        ink_hd(p, c.box(x - 0.5, 10.5, x + 0.5, 15))
    face_hd(p, c.rrect(7, 15, 18.5, 21.5, 2.5))                           # the thumb across
    face_hd(p, c.box(11, 21.5, 22, 29))                                    # the wrist
    glint_hd(p, 10.4, 8.6)


@glyph('jian')
def jian_hd(p):
    c, fr = p.c, DIAG
    grip_hd(p, fr, 2.5, 8.5, 2.1)
    face_hd(p, c.circle(*fr.P(2.0, 0.0), 2.5))                              # the pommel
    blade_hd(p, fr, 11.0, 36.5, 3.1, 29.5)
    face_hd(p, fr.prof(c, [(8.0, 2.6), (9.0, 6.0), (11.0, 6.4), (12.5, 3.0)]))   # the guard
    glint_hd(p, *fr.P(10.2, 0.0))


@glyph('spear')
def spear_hd(p):
    c, fr = p.c, DIAG
    shaft_hd(p, fr, 1.0, 26.0, 1.4)
    blade_hd(p, fr, 24.5, 36.5, 3.0, 30.5)                                  # the leaf head
    face_hd(p, fr.prof(c, [(22.8, 2.4), (25.4, 2.4)]))                     # the collar
    x, y = fr.P(24.0, 1.9)
    for dx, dy in ((0.2, 4.6), (2.0, 3.6)):                                 # the tassel under it
        warm_hd(p, c.seg(x, y, x + dx, y + dy, 1.3))
    glint_hd(p, *fr.P(28.5, -0.9))


@glyph('short_blade')
def short_blade_hd(p):
    c, fr = p.c, DIAG
    grip_hd(p, fr, 3.0, 10.0, 2.0)
    face_hd(p, c.circle(*fr.P(2.6, 0.0), 2.2))
    blade_hd(p, fr, 12.0, 34.0, 3.6, 26.0)
    face_hd(p, fr.prof(c, [(9.8, 2.3), (10.6, 4.6), (12.2, 4.6), (13.0, 2.6)]))   # a short guard
    glint_hd(p, *fr.P(11.4, 0.0))


@glyph('staff')
def staff_hd(p):
    c, fr = p.c, DIAG
    shaft_hd(p, fr, 2.0, 33.0, 1.9)
    face_hd(p, c.circle(*fr.P(33.8, 0.0), 3.1))                             # the knob
    for t in (6.0, 10.0, 27.0):                                             # the bindings
        mark_hd(p, fr.prof(c, [(t - 0.8, 1.9), (t + 0.8, 1.9)]), -1)
    face_hd(p, fr.prof(c, [(1.0, 2.4), (4.0, 2.4)]))                       # the ferrule
    glint_hd(p, *fr.P(34.6, -1.0))


@glyph('bow')
def bow_hd(p):
    c = p.c
    face_hd(p, c.ring(20.5, 16, 15.5, 3.0, ry=13.6) & c.box(0, 0, 13.0, 32))   # the stave
    warm_hd(p, c.seg(12.4, 3.4, 12.4, 28.6, 1.3))                             # the string
    face_hd(p, c.box(10, 14.9, 24, 17.3) | c.poly([(10, 12.5), (14, 16.1), (10, 19.7)]))   # the arrow and its nock
    face_hd(p, c.poly([(23, 11.8), (29.6, 16.1), (23, 20.4)]))               # its head
    glint_hd(p, 7.6, 6.2)


@glyph('sabre')
def sabre_hd(p):
    c, fr = p.c, DIAG
    grip_hd(p, fr, 2.5, 9.0, 2.0)
    face_hd(p, c.ring(*fr.P(1.6, 0.0), 2.4, 1.3))                           # the ring pommel
    ts = [11.0, 20.0, 28.0, 33.0, 35.5]
    spine = [-1.4, -1.9, -2.4, -2.8, -3.2]
    edge = [2.4, 3.4, 4.2, 3.2, -3.2]
    blade = c.poly([fr.P(t, w) for t, w in zip(ts, spine)] + [fr.P(t, w) for t, w in zip(ts[::-1], edge[::-1])])
    t, w = fr.along(c)
    ws, we = np.interp(t, ts, spine), np.interp(t, ts, edge)
    f = (w - ws) / np.maximum(we - ws, 0.2)
    p.part(blade, GOLD_HD, 'field', base=1, field=f, bands=((0.5, 1), (0.64, 2), (0.82, 0), (9, -1)), sep=True, rim=False)
    face_hd(p, fr.prof(c, [(9.2, 2.2), (10.0, 5.2), (11.4, 5.2), (12.0, 2.6)]))   # the disc guard
    glint_hd(p, *fr.P(10.6, 0.0))


@glyph('fan')
def fan_hd(p):
    c = p.c
    px, py, r = 16.0, 29.5, 20.0
    leaf = c.sector(px, py, r, 45, 135) & ~c.circle(px, py, 8.5)
    sticks = c.sector(px, py, 9.5, 45, 135)
    face_hd(p, leaf)
    lines = c.empty()
    for k in range(9):
        a = math.radians(45 + 90 * k / 8.0)
        lines |= c.seg(px, py, px + r * math.cos(a), py - r * math.sin(a), 1.0)
    mark_hd(p, lines & erode4(leaf), -1)                                    # the ribs through the leaf
    face_hd(p, sticks)
    ink_hd(p, lines & erode4(sticks))                                        # the sticks under it
    ink_hd(p, c.circle(px, py - 1.8, 1.1))                                   # the rivet
    glint_hd(p, 8.2, 14.4)


@glyph('flute')
def flute_hd(p):
    c, fr = p.c, DIAG
    shaft_hd(p, fr, 1.5, 35.0, 1.8)
    for t in (20.0, 24.0, 28.0, 33.0):                                      # the finger holes and the blow hole
        ink_hd(p, c.circle(*fr.P(t, 0.0), 0.75))
    for t in (6.5, 11.5):                                                    # the bindings
        mark_hd(p, fr.prof(c, [(t - 0.8, 1.8), (t + 0.8, 1.8)]), -1)
    glint_hd(p, *fr.P(15.5, -0.9), r=0.8)


@glyph('brush')
def brush_hd(p):
    c, fr = p.c, DIAG
    shaft = fr.prof(c, [(13.0, 2.3), (35.5, 2.3)])
    p.cylinder(fr, shaft, 2.3, GOLD_HD, base=1, sep=True, rim=False)
    for t in (20.0, 27.0):                                                   # the bamboo joints
        mark_hd(p, shaft & fr.prof(c, [(t - 0.6, 2.3), (t + 0.6, 2.3)]) & erode4(shaft), -1)
    face_hd(p, fr.prof(c, [(11.0, 2.9), (13.5, 2.9)]))                      # the collar
    tuft = face_hd(p, fr.prof(c, [(1.0, 0.0), (5.0, 1.8), (11.5, 2.6)]))
    ink_hd(p, tuft & (fr.along(c)[0] < 4.5))                                 # the inked tip
    glint_hd(p, *fr.P(30.0, -1.0))


@glyph('bell')
def bell_hd(p):
    c = p.c
    up = Frame((16.0, 30.0), 90.0)
    body = c.poly([(9.5, 13.5), (22.5, 13.5), (25.5, 24.5), (6.5, 24.5)]) | c.ellipse(16, 13.5, 6.5, 5.0)
    p.cylinder(up, body, lambda t: np.interp(t, [5.5, 16.5, 21.5], [9.5, 6.5, 0.5]), GOLD_HD, base=1, sep=True, rim=False)
    face_hd(p, c.box(14.6, 5.5, 17.4, 10) | c.circle(16, 4.4, 2.1))         # the handle and knob
    face_hd(p, c.rrect(5.5, 24.2, 26.5, 27.4, 1.2))                          # the lip
    face_hd(p, c.circle(16, 28.2, 1.6))                                      # the clapper
    glint_hd(p, 12.2, 11.4)


# --------------------------------------------------------------------------- templates for the button glyphs
def book_hd(p, deco=None):
    """A closed book: the cover, a warm spine band, and `deco(p)` on the page."""
    c = p.c
    face_hd(p, c.rrect(5, 5, 27, 27, 1.5))
    mark_hd(p, c.box(5, 5, 9.5, 27))
    ink_hd(p, c.box(9.5, 5, 10.5, 27))
    if deco:
        deco(p)
    glint_hd(p, 7.0, 7.0)


def bust_hd(p, cx, head_y, head_r, body):
    """A figure: a head with a hair bun over the shoulders `body`."""
    c = p.c
    face_hd(p, c.circle(cx, head_y - head_r - 0.4, head_r * 0.42))          # the bun
    face_hd(p, c.circle(cx, head_y, head_r))
    face_hd(p, body)


def arrow_hd(c, tail, head, hw, ah, al):
    """An arrow from `tail` to `head` (icon points): a shaft of half-width `hw`, a head `al` long and `ah` wide."""
    fr = Frame(tail, math.degrees(math.atan2(-(head[1] - tail[1]), head[0] - tail[0])))
    L = math.hypot(head[0] - tail[0], head[1] - tail[1])
    return c.poly([fr.P(0, -hw), fr.P(L - al, -hw), fr.P(L - al, -ah), fr.P(L, 0), fr.P(L - al, ah), fr.P(L - al, hw), fr.P(0, hw)])


def chest_hd(p, opened):
    """A chest with a keyhole on its lock plate: shut, or `opened` with the lid up and the dark inside showing."""
    c = p.c
    if opened:
        face_hd(p, c.rrect(5.5, 3, 26.5, 9, 2))                               # the lid, standing up
        face_hd(p, c.box(4.5, 11.5, 27.5, 28))
        ink_hd(p, c.box(6.5, 12, 25.5, 15))                                    # the inside
    else:
        face_hd(p, c.rrect(4.5, 5, 27.5, 12.5, 3))
        face_hd(p, c.box(4.5, 14, 27.5, 28))
    for x in (7.5, 22.5):                                                     # the bands
        mark_hd(p, c.box(x, 15.5, x + 2, 27.5))
    face_hd(p, c.box(13, 15, 19, 21))                                         # the lock plate
    ink_hd(p, c.circle(16, 17.3, 1.2) | c.box(15.3, 17.5, 16.7, 20))
    glint_hd(p, 7.0, 4.8 if opened else 6.8)


@glyph('talk')
def talk_hd(p):
    c = p.c
    face_hd(p, c.rrect(4, 6, 28, 21, 4) | c.poly([(9, 19), (9, 26.5), (16, 19)]))
    for x in (11, 16, 21):
        ink_hd(p, c.circle(x, 13.5, 1.3))
    glint_hd(p, 7.2, 8.4)


@glyph('gather')
def gather_hd(p):
    c = p.c
    leaf = c.leaf(8.5, 23.5, 45, 21, 12.5, 0.05, tip_power=0.7)
    face_hd(p, leaf)
    fr = Frame((8.5, 23.5), 45.0)
    p.line([fr.P(1.0, 0.0), fr.P(17.0, 0.0)], INK, 0, 1.0)                    # the midrib
    for t in (6.0, 10.0, 14.0):                                                # the veins
        for s in (-1, 1):
            p.line([fr.P(t, 0.0), fr.P(t + 3.0, s * 3.2)], GOLD_HD, -1, 1.0)
    warm_hd(p, c.taper((8.5, 23.5), (6.5, 26.5), (3.5, 29.5), 2.2, 1.4))      # the stem
    glint_hd(p, 14.4, 12.2)


@glyph('mine')
def mine_hd(p):
    c = p.c
    head = c.ellipse(16, 16.5, 13.5, 11) & ~c.ellipse(16, 19.5, 12.4, 10.8) & c.box(0, 0, 32, 14.5)
    face_hd(p, c.box(14.5, 8, 17.5, 29.5) | c.box(13.5, 26.5, 18.5, 29.5))    # the handle and its ferrule
    face_hd(p, head)
    mark_hd(p, c.box(14.5, 10.5, 17.5, 13.5), -1)                              # the lashing
    glint_hd(p, 9.0, 8.0)


@glyph('open')
def open_hd(p):
    chest_hd(p, True)


@glyph('storage')
def storage_hd(p):
    chest_hd(p, False)


@glyph('enter')
def enter_hd(p):
    c = p.c
    face_hd(p, c.box(17, 3, 29, 29) & ~c.box(19.8, 5.8, 26.2, 29))            # the doorway
    face_hd(p, arrow_hd(c, (3, 16), (23, 16), 1.8, 6.0, 6.5))
    glint_hd(p, 18.4, 4.4, 0.8)


@glyph('fish')
def fish_hd(p):
    c = p.c
    face_hd(p, c.poly([(9, 16), (2.8, 10.4), (3.6, 12.8), (5.2, 16), (3.6, 19.2), (2.8, 21.6)]))   # the tail
    body = c.ellipse(17.5, 16, 10, 6.3)
    face_hd(p, body | c.poly([(12, 10.5), (16, 6.8), (20, 10.5)]))            # the body and dorsal fin
    ink_hd(p, c.arc(22.5, 16, 5.5, 1.0, 110, 250) & body)                     # the gill
    ink_hd(p, c.circle(23.4, 14.2, 1.2))                                       # the eye
    glint_hd(p, 13.0, 12.6)


@glyph('cook')
def cook_hd(p):
    c = p.c
    for x, ph in ((10.0, 0.0), (16.0, 2.0), (22.0, 4.0)):                       # the steam
        pts = [(x + 1.3 * math.sin((y + ph) / 3.2), y) for y in np.linspace(3.5, 12.5, 12)]
        face_hd(p, c.polyline(pts, 1.4))
    face_hd(p, c.ellipse(16, 18, 10.5, 9.5) & c.box(0, 18, 32, 28))           # the bowl
    face_hd(p, c.rrect(4, 15, 28, 18.8, 1.4))                                  # its rim
    glint_hd(p, 7.4, 20.6)


@glyph('cultivate')
def cultivate_hd(p):
    c = p.c
    petals = [c.leaf(16 + dx, 25.0, a, L, W, 0.0, tip_power=0.75)
              for (a, L, W, dx) in ((90, 19.0, 8.0, 0.0), (60, 16.5, 6.6, 2.5), (120, 16.5, 6.6, -2.5), (35, 12.0, 5.4, 5.0), (145, 12.0, 5.4, -5.0))]
    for i in (3, 4, 1, 2, 0):
        face_hd(p, petals[i])
    face_hd(p, c.ellipse(16, 25.5, 12.5, 4.2) & c.box(0, 23.5, 32, 30), 0)     # the pad
    glint_hd(p, 15.2, 10.5, 1.4)
    for pts in (((16, 13.5), (16, 22.5)), ((13, 14.5), (12, 22.5)), ((19, 14.5), (20, 22.5))):
        p.line(pts, GOLD_HD, -1, 1.0)


@glyph('jump')
def jump_hd(p):
    c = p.c
    face_hd(p, arrow_hd(c, (16, 19.5), (16, 3), 2.2, 8.0, 9.0))
    face_hd(p, (c.circle(11, 26, 4.6) | c.circle(21, 26, 4.6) | c.box(6.5, 25.5, 25.5, 29)) & c.box(0, 0, 32, 29))   # the ground
    glint_hd(p, 14.2, 6.6)


@glyph('sense')
def sense_hd(p):
    c = p.c
    lid = c.leaf(3, 16, 0, 26, 17.5) & ~c.leaf(5, 16, 0, 22, 12.5)
    face_hd(p, lid)
    face_hd(p, c.circle(16, 16, 5.3))                                          # the iris
    ink_hd(p, c.circle(16, 16, 2.4))                                           # the pupil
    glint_hd(p, 14.4, 14.2, 0.8)


@glyph('presence')
def presence_hd(p):
    c = p.c
    outer = c.empty()
    for a in (0, 90, 180, 270):
        outer |= c.arc(16, 16, 13.5, 2.3, a + 10, a + 80)                     # four waves of pressure
    face_hd(p, outer)
    face_hd(p, c.ring(16, 16, 8.6, 2.0))
    face_hd(p, c.circle(16, 13.4, 2.1) | (c.ellipse(16, 18.6, 3.6, 2.4) & c.box(0, 16.3, 32, 32)))   # the figure
    glint_hd(p, 15.2, 12.8, 0.6)


@glyph('sphere')
def sphere_hd(p):
    c = p.c
    ring, front = tilted_ring(c, 16, 17, 13.5, 4.6, 22, 2.0)
    face_hd(p, ring & ~front)
    p.part(c.circle(16, 15.5, 7.8), GOLD_HD, 'sphere', base=1, sep=True, rim=False, cx=16, cy=15.5, rx=7.8, ry=7.8)
    face_hd(p, front)
    glint_hd(p, 13.0, 12.4, 1.2)


@glyph('quick_use')
def quick_use_hd(p):
    c = p.c
    face_hd(p, c.circle(16, 21, 8.4) | c.poly([(12.4, 13), (19.6, 13), (23.5, 18), (8.5, 18)]))   # the flask
    face_hd(p, c.box(14.2, 6.5, 17.8, 13.5))                                    # the neck
    face_hd(p, c.ellipse(16, 10.8, 4.6, 1.9))                                   # the collar
    face_hd(p, c.circle(16, 5.0, 2.2))                                          # the stopper
    ink_hd(p, c.box(11.5, 21.5, 20.5, 23.2))                                    # the label
    glint_hd(p, 11.8, 17.2, 1.2)


@glyph('pet')
def pet_hd(p):
    c = p.c
    for x, y in ((6.5, 12.0), (12.3, 7.4), (19.7, 7.4), (25.5, 12.0)):
        face_hd(p, c.circle(x, y, 2.9))
    face_hd(p, c.ellipse(16, 20.5, 8.6, 6.4))
    glint_hd(p, 11.4, 16.6)


@glyph('guard')
def guard_hd(p):
    c = p.c
    shield = c.poly([(5, 4.5), (27, 4.5), (27, 15), (16, 29), (5, 15)]) | c.rrect(5, 4.5, 27, 14, 2.5)
    face_hd(p, shield)
    mark_hd(p, c.box(14.5, 5.5, 17.5, 26.5))                                    # the stripe
    mark_hd(p, c.ring(16, 15, 9.5, 1.2) & erode4(shield), 0)
    glint_hd(p, 8.6, 7.6)


@glyph('dodge')
def dodge_hd(p):
    c = p.c
    face_hd(p, c.poly([(13, 4), (17.5, 4), (28.5, 16), (17.5, 28), (13, 28), (24, 16)]))
    for y0, x1 in ((8, 11.5), (14.5, 15), (21, 11.5)):                         # the dash lines
        face_hd(p, c.box(3, y0, x1, y0 + 3))
    glint_hd(p, 15.2, 5.6, 0.8)


@glyph('menu')
def menu_hd(p):
    c = p.c
    for y in (5.0, 13.75, 22.5):
        face_hd(p, c.rrect(4, y, 28, y + 4.5, 1.0))
    glint_hd(p, 6.4, 6.6, 0.8)


@glyph('bag')
def bag_hd(p):
    c = p.c
    face_hd(p, c.circle(16, 21, 9.0) | c.poly([(12.5, 11.5), (19.5, 11.5), (24.5, 18), (7.5, 18)]))   # the pouch
    face_hd(p, c.poly([(9.5, 3.5), (22.5, 3.5), (19.8, 9.5), (12.2, 9.5)]))     # the gathered mouth
    face_hd(p, c.rrect(10.5, 9, 21.5, 12.6, 1.2))                               # the cord
    ink_hd(p, c.circle(16, 10.8, 0.9))
    glint_hd(p, 11.4, 17.0, 1.3)


@glyph('map')
def map_hd(p):
    c = p.c
    face_hd(p, c.poly([(3, 5.5), (11, 8.5), (11, 26.5), (3, 23.5)]))
    face_hd(p, c.poly([(11, 8.5), (21, 5.5), (21, 23.5), (11, 26.5)]))
    face_hd(p, c.poly([(21, 5.5), (29, 8.5), (29, 26.5), (21, 23.5)]))
    p.line([(6, 20), (9, 15), (14, 17), (18, 11), (26, 12)], INK, 0, 1.0)        # the route
    ink_hd(p, c.circle(26, 12, 1.2))
    glint_hd(p, 5.0, 8.4, 0.8)


@glyph('mail')
def mail_hd(p):
    c = p.c
    env = face_hd(p, c.rrect(3, 7, 29, 25, 1.5))
    mark_hd(p, c.poly([(3, 7), (29, 7), (16, 18.5)]) & erode4(env))             # the flap
    p.line([(4, 8), (16, 18), (28, 8)], INK, 0, 1.0)
    glint_hd(p, 5.6, 21.4, 0.8)


@glyph('quest')
def quest_hd(p):
    c = p.c
    face_hd(p, c.box(6, 6, 26, 26))
    face_hd(p, c.rrect(3.5, 4, 28.5, 8.2, 1.5))                                  # the rollers
    face_hd(p, c.rrect(3.5, 23.8, 28.5, 28, 1.5))
    for y, L in ((11.0, 14), (14.5, 10), (18.0, 13), (21.5, 8)):
        ink_hd(p, c.box(9, y, 9 + L, y + 1.4))
    glint_hd(p, 5.6, 5.4, 0.8)


@glyph('close')
def close_hd(p):
    c = p.c
    face_hd(p, c.seg(5.5, 5.5, 26.5, 26.5, 4.6) | c.seg(26.5, 5.5, 5.5, 26.5, 4.6))
    glint_hd(p, 6.4, 6.4, 0.8)


@glyph('back')
def back_hd(p):
    c = p.c
    face_hd(p, arrow_hd(c, (29, 16), (3, 16), 3.2, 10.5, 12.0))
    glint_hd(p, 9.6, 12.4)


@glyph('lock')
def lock_hd(p):
    c = p.c
    face_hd(p, (c.ring(16, 11.5, 6.5, 2.6) & c.box(0, 0, 32, 11.5)) | c.box(9.5, 11, 12.1, 14.5) | c.box(19.9, 11, 22.5, 14.5))   # the shackle
    face_hd(p, c.rrect(6.5, 14, 25.5, 28.5, 2))
    ink_hd(p, c.circle(16, 19.5, 1.9) | c.box(15.2, 19.5, 16.8, 24.5))          # the keyhole
    glint_hd(p, 9.2, 16.6)


@glyph('coin')
def coin_hd(p):
    c = p.c
    hull = c.poly([(2.5, 11), (7.0, 9.5), (10, 15.5), (22, 15.5), (25, 9.5), (29.5, 11), (28, 20), (24.5, 25.5), (7.5, 25.5), (4, 20)])
    face_hd(p, hull)                                                              # the boat of the ingot
    face_hd(p, c.circle(16, 13.5, 6.5) & c.box(0, 0, 32, 18.5))                # its raised middle
    glint_hd(p, 13.2, 10.4, 1.3)


@glyph('spirit_stone')
def spirit_stone_hd(p):
    c = p.c
    face_hd(p, c.poly([(8.5, 5), (23.5, 5), (29.5, 12.5), (16, 29), (2.5, 12.5)]))
    p.line([(3.5, 12.5), (28.5, 12.5)], INK, 0, 1.0)                              # the girdle
    for pts in (((8.5, 5.5), (12, 12.5)), ((23.5, 5.5), (20, 12.5)), ((12, 13), (16, 28)), ((20, 13), (16, 28))):
        p.line(pts, INK, 0, 1.0)
    glint_hd(p, 10.0, 8.6, 1.2)


@glyph('contribution')
def contribution_hd(p):
    c = p.c
    face_hd(p, c.poly([(10.5, 3), (21.5, 3), (19.5, 13.5), (12.5, 13.5)]))         # the ribbon
    ink_hd(p, c.box(15.4, 3, 16.6, 12))
    face_hd(p, c.circle(16, 20.5, 8.6))                                           # the medal
    ink_hd(p, c.ring(16, 20.5, 5.4, 1.2))
    ink_hd(p, c.circle(16, 20.5, 1.6))
    glint_hd(p, 11.6, 16.4)


@glyph('settings')
def settings_hd(p):
    c = p.c
    gear = c.ring(16, 16, 10.0, 6.5)
    for k in range(8):
        fr = Frame((16, 16), k * 45.0)
        gear |= c.poly([fr.P(6, -2.3), fr.P(13.2, -1.7), fr.P(13.2, 1.7), fr.P(6, 2.3)])
    face_hd(p, gear)
    glint_hd(p, 9.8, 9.8)


@glyph('codex')
def codex_hd(p):
    def lines(p):
        for y in (11.5, 16.5, 21.5):
            ink_hd(p, p.c.box(13, y, 23, y + 1.4))
    book_hd(p, lines)


@glyph('gathering_log')
def gathering_log_hd(p):
    def leaf(p):
        c = p.c
        mark_hd(p, c.leaf(13.5, 23, 50, 12.5, 6.5))
        fr = Frame((13.5, 23), 50.0)
        p.line([fr.P(1, 0), fr.P(10, 0)], INK, 0, 1.0)
    book_hd(p, leaf)


@glyph('character')
def character_hd(p):
    c = p.c
    bust_hd(p, 16, 10.5, 5.0, c.rrect(5, 18.5, 27, 30, 5) & c.box(0, 0, 32, 29.5))
    glint_hd(p, 13.6, 8.0)


@glyph('characters')
def characters_hd(p):
    c = p.c
    for cx, x0, x1 in ((9.5, 2.5, 15.5), (22.5, 16.5, 29.5)):
        bust_hd(p, cx, 10.5, 3.9, c.rrect(x0, 17, x1, 30, 4) & c.box(0, 0, 32, 29.5))
    glint_hd(p, 7.6, 8.4, 0.8)


@glyph('cultivation')
def cultivation_hd(p):
    c = p.c
    face_hd(p, c.arc(16, 15.5, 12.5, 2.4, 0, 180))                                # the halo
    face_hd(p, c.poly([(16, 14), (9, 24.5), (23, 24.5)]) | c.ellipse(16, 22.5, 6.8, 3.2))   # the seated figure
    face_hd(p, c.circle(16, 12.2, 3.1))
    face_hd(p, c.rrect(4.5, 24.5, 27.5, 29, 1.5))                                 # the cushion
    glint_hd(p, 14.6, 10.8, 0.8)


@glyph('techniques')
def techniques_hd(p):
    c = p.c
    fr = Frame((5.5, 27.0), 45.0)
    paper = fr.prof(c, [(4.0, 4.2), (29.5, 4.2)])
    face_hd(p, paper)
    for t, w0, w1 in ((11.5, -2.4, 1.2), (15.5, -1.0, 2.6), (19.5, -2.6, 0.4), (23.5, -0.6, 2.2)):   # a line of writing
        a, b = fr.P(t, w0), fr.P(t, w1)
        ink_hd(p, c.seg(a[0], a[1], b[0], b[1], 1.5) & erode4(paper))
    roll = fr.prof(c, [(1.0, 4.3), (6.5, 4.3)])
    p.cylinder(fr, roll, 4.3, GOLD_HD, base=1, sep=True, rim=False)                # the rolled end
    ink_hd(p, c.circle(*fr.P(3.7, 0.0), 1.0))
    glint_hd(p, *fr.P(27.0, -1.4))


@glyph('crafts')
def crafts_hd(p):
    c = p.c
    body = face_hd(p, c.poly([(5, 13), (27, 13), (24, 27.5), (8, 27.5)]))
    X, Y = XY(c)
    mark_hd(p, body & erode4(body) & ((np.floor(X / 3.0) + np.floor(Y / 3.0)).astype(int) % 2 == 0), -1)   # the weave
    face_hd(p, c.rrect(3.5, 11.5, 28.5, 14.8, 1.2))                                # the rim
    face_hd(p, c.arc(16, 12.5, 9.5, 2.4, 15, 165))                                 # the handle
    glint_hd(p, 6.6, 12.8, 0.8)


@glyph('sect')
def sect_hd(p):
    c = p.c
    face_hd(p, c.poly([(16, 3), (4.5, 10.5), (2.5, 8.5), (2.5, 12), (29.5, 12), (29.5, 8.5), (27.5, 10.5)]))   # the roof
    face_hd(p, c.rrect(4, 12, 28, 14.5, 0.8))
    for x0 in (7.0, 14.2, 21.5):
        face_hd(p, c.box(x0, 14.5, x0 + 3.5, 26))                                 # the columns
    face_hd(p, c.box(3.5, 26, 28.5, 29.5))
    glint_hd(p, 15.0, 5.2, 0.8)


@glyph('account')
def account_hd(p):
    c = p.c
    face_hd(p, c.ring(16, 5.5, 3.0, 1.6))                                          # the loop
    face_hd(p, c.rrect(6, 8, 26, 29, 4))                                           # the plaque
    ink_hd(p, c.diamond(16, 16, 5.0, 5.0) & ~c.diamond(16, 16, 2.4, 2.4))        # the emblem
    ink_hd(p, c.box(10, 23, 22, 24.4) | c.box(10, 26, 22, 27.4))
    glint_hd(p, 9.0, 10.6)


@glyph('shop')
def shop_hd(p):
    c = p.c
    awning = c.box(3, 4, 29, 10)
    for k in range(6):
        awning |= c.circle(5.17 + k * 4.33, 10, 2.2)
    face_hd(p, awning)
    X = XY(c)[0]
    mark_hd(p, awning & erode4(awning) & (np.floor((X - 3.0) / 4.33).astype(int) % 2 == 1))   # the stripes
    face_hd(p, c.box(5, 12, 8.5, 29) | c.box(23.5, 12, 27, 29))                    # the posts
    face_hd(p, c.box(10.5, 19, 21.5, 29))                                         # the counter
    ink_hd(p, c.box(12.5, 21, 19.5, 22.4))
    glint_hd(p, 5.6, 5.8, 0.8)


@glyph('achievements')
def achievements_hd(p):
    c = p.c
    for x in (6.5, 25.5):
        face_hd(p, c.ring(x, 10.5, 4.0, 2.2))                                       # the handles
    face_hd(p, c.poly([(7, 4.5), (25, 4.5), (23, 16), (9, 16)]) | c.ellipse(16, 15.5, 7, 4))
    face_hd(p, c.box(13.8, 19, 18.2, 24.5))                                        # the stem
    face_hd(p, c.rrect(8.5, 24.5, 23.5, 29, 1.5))                                  # the foot
    mark_hd(p, star_hd(c, 16, 10.5, 5, 3.4, 1.5))
    glint_hd(p, 9.6, 6.6)


@glyph('alchemy')
def alchemy_hd(p):
    c = p.c
    face_hd(p, (c.ellipse(16, 8.5, 7, 4) & c.box(0, 0, 32, 9)) | c.circle(16, 5.0, 1.9))   # the lid and knob
    for x in (7.5, 22.0):
        face_hd(p, c.box(x, 23, x + 2.6, 29.5))                                   # the legs
    face_hd(p, c.box(14.6, 24, 17.4, 29.5))
    face_hd(p, c.circle(16, 17.5, 9.5))                                            # the furnace
    face_hd(p, c.ellipse(16, 9.5, 11.5, 2.4))                                      # the rim
    for k, y in enumerate((14.5, 17.5, 20.5)):                                     # the trigram for fire
        if k == 1:
            ink_hd(p, c.box(11.5, y, 14.6, y + 1.4) | c.box(17.4, y, 20.5, y + 1.4))
        else:
            ink_hd(p, c.box(11.5, y, 20.5, y + 1.4))
    glint_hd(p, 9.6, 13.2)


@glyph('forge')
def forge_hd(p):
    c = p.c
    face_hd(p, c.poly([(2.5, 19.5), (5.5, 17.5), (28.5, 17.5), (28.5, 22), (5.5, 22)]))   # the anvil
    face_hd(p, c.box(11, 22, 21, 25.5))
    face_hd(p, c.rrect(6, 25.5, 26, 29.5, 1.0))
    face_hd(p, c.seg(11.5, 6.5, 27, 13.0, 2.6))                                    # the hammer
    face_hd(p, c.rrect(3.5, 3.5, 13.5, 9.5, 1.2))
    glint_hd(p, 5.6, 5.4, 0.8)


@glyph('formation')
def formation_hd(p):
    c = p.c
    face_hd(p, c.ring(16, 16, 13.5, 2.3))
    face_hd(p, c.diamond(16, 16, 8.0, 8.0) & ~c.diamond(16, 16, 5.4, 5.4))
    face_hd(p, c.circle(16, 16, 2.0))
    glint_hd(p, 8.4, 7.2, 0.8)


@glyph('collection')
def collection_hd(p):
    c = p.c
    for x0, y0 in ((4, 4), (17.5, 4), (4, 17.5), (17.5, 17.5)):
        face_hd(p, c.rrect(x0, y0, x0 + 10.5, y0 + 10.5, 1.5))
        mark_hd(p, c.circle(x0 + 5.25, y0 + 5.25, 1.7))
    glint_hd(p, 6.0, 6.0, 0.8)


@glyph('world_map')
def world_map_hd(p):
    c = p.c
    face_hd(p, star_hd(c, 16, 16, 4, 9.5, 3.4, 45))
    face_hd(p, star_hd(c, 16, 16, 4, 13.6, 3.8))
    ink_hd(p, c.ring(16, 16, 3.0, 1.2))
    glint_hd(p, 15.0, 5.6, 0.8)


@glyph('calendar')
def calendar_hd(p):
    c = p.c
    face_hd(p, c.rrect(4, 6.5, 28, 28, 1.5))
    face_hd(p, c.box(4, 6.5, 28, 11.5), 0)                                          # the header
    for x in (9.5, 22.5):
        face_hd(p, c.box(x - 1.2, 3.5, x + 1.2, 9.5))                                # the binding pins
    for x in (9, 15.5, 22):
        for y in (14.5, 19, 23.5):
            ink_hd(p, c.box(x - 1.2, y - 0.9, x + 1.2, y + 0.9))
    mark_hd(p, c.circle(22, 19, 2.4) & ~c.circle(22, 19, 1.4))                     # today
    glint_hd(p, 6.4, 13.4, 0.8)


@glyph('spirit_animals')
def spirit_animals_hd(p):
    c = p.c
    ears = c.poly([(4, 4), (11.5, 5.5), (7, 15)]) | c.poly([(28, 4), (20.5, 5.5), (25, 15)])
    face_hd(p, ears)
    face_hd(p, c.ellipse(16, 17.5, 10.5, 9.5))
    for x in (11.5, 20.5):
        ink_hd(p, c.ellipse(x, 15.5, 1.6, 1.3))                                     # the eyes
    ink_hd(p, c.poly([(14, 21.5), (18, 21.5), (16, 23.8)]))                          # the nose
    glint_hd(p, 10.0, 11.4)


@glyph('breakthrough')
def breakthrough_hd(p):
    c = p.c
    face_hd(p, c.poly([(3, 15.5), (10, 15.5), (9, 17.5), (10.5, 19), (9.5, 20.5), (3, 20.5)]))     # the broken bar
    face_hd(p, c.poly([(29, 15.5), (22, 15.5), (23, 17.5), (21.5, 19), (22.5, 20.5), (29, 20.5)]))
    face_hd(p, arrow_hd(c, (16, 29), (16, 3), 2.5, 9.0, 10.0))
    glint_hd(p, 14.2, 6.6)


@glyph('seclusion')
def seclusion_hd(p):
    c = p.c
    outer = (c.circle(16, 17, 13.5) | c.box(2.5, 17, 29.5, 29.5)) & c.box(0, 0, 32, 29.5)
    inner = (c.circle(16, 18.5, 9.0) | c.box(7, 18.5, 25, 30))
    face_hd(p, outer & ~inner)                                                        # the cave mouth
    face_hd(p, c.circle(16, 20.5, 2.6))                                               # the one inside
    face_hd(p, c.ellipse(16, 26.5, 5.2, 3.4) & c.box(0, 0, 32, 29.5))
    glint_hd(p, 8.0, 8.6)


@glyph('meridian')
def meridian_hd(p):
    c = p.c
    face_hd(p, c.circle(16, 6.2, 3.5))
    face_hd(p, c.box(3, 12, 29, 15.5) | c.poly([(8.5, 11.5), (23.5, 11.5), (21.5, 24), (10.5, 24)]))   # arms and body
    face_hd(p, c.box(10.5, 24, 15, 29.5) | c.box(17, 24, 21.5, 29.5))                # the legs
    ink_hd(p, c.box(15.5, 12.5, 16.5, 23))                                            # the channel
    for y in (14.5, 18.5, 22.0):
        ink_hd(p, c.circle(16, y, 1.3))
    glint_hd(p, 14.6, 4.8, 0.8)


@glyph('dao')
def dao_hd(p):
    c = p.c
    X, Y = XY(c)
    cx, cy, r = 16.0, 16.0, 12.5
    disc = face_hd(p, c.circle(cx, cy, r))
    top, bot = c.circle(cx, cy - r / 2, r / 2), c.circle(cx, cy + r / 2, r / 2)
    yin = disc & (((X > cx) & ~bot) | top)
    ink_hd(p, yin)
    ink_hd(p, c.circle(cx, cy + r / 2, 2.2))
    mark_hd(p, c.circle(cx, cy - r / 2, 2.2), 1)
    glint_hd(p, 10.6, 21.4)


@glyph('post')
def post_hd(p):
    c = p.c
    face_hd(p, c.ellipse(10.5, 30, 8.5, 5.0) & c.box(0, 0, 32, 29.5))                  # the mound
    face_hd(p, c.box(6.5, 3, 9.5, 27))                                                 # the pole
    flag = face_hd(p, c.poly([(9.5, 4), (27, 4), (23.5, 9.5), (27, 15), (9.5, 15)]))
    mark_hd(p, c.box(9.5, 4, 13.2, 15) & erode4(flag))                                 # the hoist
    glint_hd(p, 7.4, 4.6, 0.8)


@glyph('roll_call')
def roll_call_hd(p):
    c = p.c
    face_hd(p, c.box(6, 5, 26, 27))
    for x0 in (3.0, 26.0):
        warm_hd(p, c.rrect(x0, 3, x0 + 3.0, 29, 1.0))                                  # the rails
    for y in (9.5, 15.0, 20.5):
        ink_hd(p, c.box(9, y, 12.5, y + 1.6) | c.box(14.5, y, 23, y + 1.6))
    glint_hd(p, 8.0, 7.0, 0.8)


@glyph('storehouse')
def storehouse_hd(p):
    c = p.c
    face_hd(p, c.box(5, 12, 27, 24))
    face_hd(p, c.poly([(16, 3), (2.5, 12.5), (29.5, 12.5)]))                            # the roof
    ink_hd(p, c.box(7, 14, 25, 16))                                                    # the loft
    ink_hd(p, c.box(13.5, 18, 18.5, 24))                                               # the door
    for x0 in (5.0, 23.0):
        face_hd(p, c.box(x0, 24, x0 + 4, 27.5) | c.box(x0 - 1.5, 27.5, x0 + 5.5, 29.5))  # the stilts
    glint_hd(p, 15.0, 5.4, 0.8)


@glyph('craft_delving')
def craft_delving_hd(p):
    c = p.c
    head = c.ellipse(16, 14, 12.5, 10) & ~c.ellipse(16, 17, 11.4, 9.8) & c.box(0, 0, 32, 12.5)
    face_hd(p, c.box(14.6, 6, 17.4, 24))
    face_hd(p, head)
    face_hd(p, c.ellipse(16, 30.5, 12.5, 9) & c.box(0, 0, 32, 29.5))                    # the ore
    for x, y in ((10.5, 26.5), (17.5, 24.5), (22.5, 27.0)):
        ink_hd(p, c.circle(x, y, 1.1))
    glint_hd(p, 9.0, 6.4, 0.8)


@glyph('craft_foraging')
def craft_foraging_hd(p):
    c = p.c
    face_hd(p, c.poly([(9.5, 12), (16.5, 12), (17.5, 27.5), (8.5, 27.5)]))               # the stem
    cap = face_hd(p, c.ellipse(13, 12.5, 11, 8.5) & c.box(0, 0, 32, 13.5))
    for x, y in ((8, 8.5), (14, 6), (18.5, 10)):
        mark_hd(p, c.circle(x, y, 1.5) & erode4(cap))
    face_hd(p, c.leaf(29, 29, 122, 14, 6.5))
    fr = Frame((29, 29), 122.0)
    p.line([fr.P(1.0, 0), fr.P(11.0, 0)], INK, 0, 1.0)
    glint_hd(p, 7.0, 10.6)


@glyph('craft_angling')
def craft_angling_hd(p):
    c = p.c
    face_hd(p, c.box(13.8, 3, 15.4, 14.5))                                              # the line
    face_hd(p, c.arc(19.5, 14.5, 5.0, 2.6, 180, 15) | c.poly([(23.2, 14.2), (25.8, 9.8), (21.4, 11.6)]))   # the hook
    for y in (23.5, 27.5):
        face_hd(p, wave_hd(c, 4, 28, y, 1.0, 8.0, 1.6))
    glint_hd(p, 17.0, 17.6, 0.7)


@glyph('craft_netting')
def craft_netting_hd(p):
    c = p.c
    face_hd(p, c.seg(12, 19, 4.0, 28.0, 2.6))                                           # the handle
    net = face_hd(p, c.circle(18.5, 12.5, 9.5))
    X, Y = XY(c)
    mesh = ((np.floor(X + Y) % 3 == 0) | (np.floor(X - Y) % 3 == 0)) & erode4(erode4(net))
    ink_hd(p, mesh)
    face_hd(p, c.ring(18.5, 12.5, 9.5, 1.8))                                            # the rim
    glint_hd(p, 12.2, 7.4, 0.8)


@glyph('craft_snaring')
def craft_snaring_hd(p):
    c = p.c
    face_hd(p, c.seg(10.0, 6.0, 3.5, 3.0, 2.2))                                          # the rope
    face_hd(p, c.ring(17, 9.5, 7.5, 2.2, ry=6.0))                                        # the loop
    mark_hd(p, c.circle(10.5, 6.0, 1.6), -1)                                             # the knot
    for x in (12.5, 19.5):
        face_hd(p, c.ellipse(x, 20.0, 1.9, 4.2))                                        # the ears
    face_hd(p, c.ellipse(16, 25.5, 6.2, 3.9))
    for x in (13.8, 18.2):
        ink_hd(p, c.circle(x, 25.0, 1.0))
    glint_hd(p, 13.4, 5.4, 0.8)


@glyph('craft_rites')
def craft_rites_hd(p):
    c = p.c
    face_hd(p, c.box(15, 8, 28, 27.5) | c.ellipse(21.5, 8.5, 6.5, 4.8))                 # the stele
    face_hd(p, c.rrect(13.5, 26.5, 29.5, 29.5, 0.8))
    for y in (9.5, 13.5, 17.5, 21.5):
        ink_hd(p, c.box(20.4, y, 22.6, y + 2.4))
    warm_hd(p, c.seg(8.5, 29.0, 6.5, 12.0, 1.6))                                        # the incense stick
    face_hd(p, c.polyline([(6.4, 10.5), (5.2, 8.0), (7.0, 5.5), (5.8, 3.0)], 1.2))       # its smoke
    glint_hd(p, 6.6, 11.6, 0.8)


@glyph('bench')
def bench_hd(p):
    c = p.c
    face_hd(p, c.box(2.5, 14, 29.5, 18))                                                 # the top
    for x0 in (4.0, 24.0):
        face_hd(p, c.box(x0, 18, x0 + 4, 29.5))
    face_hd(p, c.box(4, 23, 28, 25.5))                                                   # the shelf
    warm_hd(p, c.box(6, 8.2, 20, 10.8))                                                  # the mallet
    face_hd(p, c.rrect(19.5, 5, 27.5, 13.5, 1.0))
    glint_hd(p, 4.4, 15.2, 0.8)


@glyph('works')
def works_hd(p):
    c = p.c
    face_hd(p, c.circle(16, 6.2, 3.8) | c.box(14, 8, 18, 13.5))                          # the knob and neck
    face_hd(p, c.rrect(6, 13, 26, 29, 1.5))                                              # the block
    face_hd(p, c.box(6, 13, 26, 15.8), 0)
    ink_hd(p, c.box(8.5, 17, 23.5, 27.5))                                                # the seal face
    mark_hd(p, c.box(11, 18.5, 21, 20.5) | c.box(15, 20.5, 17, 24) | c.box(11, 24, 21, 26), 1)   # the character for work
    glint_hd(p, 14.2, 4.6)


# --------------------------------------------------------------------------- points-to-spend badges (by the HP panel)
# One small badge a point system (the HUD's POINT_SYSTEMS table): a plate in the system's own colour and shape, its
# symbol in pale gold on it, and the gold "+" knob at the top right that every badge shares. Colour, shape and symbol
# each tell them apart, so none relies on colour alone. The plate sits lower left so the knob overlaps its corner.
def _plate_mat(cols):
    return mat7(Ramp(cols, INK), 'matte')


PLATE_HD = {
    'jade': _plate_mat(['#0E3B31', '#17604D', '#23876A', '#45B08D', '#8FDDBE']),
    'violet': _plate_mat(['#2C1A4A', '#46307A', '#6446A6', '#8D6FCF', '#C3B0EE']),
    'bronze': _plate_mat(['#3E2410', '#6A3F1C', '#98612E', '#C28A4A', '#E8BD82']),
    'crimson': _plate_mat(['#3F1016', '#6C1C26', '#9A2B36', '#C65059', '#EE9A9C']),
}
PLATE_C = (14.0, 18.0)     # the plate's centre
PLATE_R = 11.5             # and its half-size


def _hexagon(c, cx, cy, r):
    return c.poly([(cx + r * math.cos(math.radians(30 + 60 * k)), cy + r * math.sin(math.radians(30 + 60 * k))) for k in range(6)])


PLATE_SHAPE = {
    'circle': lambda c, x, y, r: c.circle(x, y, r),
    'diamond': lambda c, x, y, r: c.diamond(x, y, r + 1.5),
    'square': lambda c, x, y, r: c.rrect(x - r + 1, y - r + 1, x + r - 1, y + r - 1, 2.5),
    'hexagon': lambda c, x, y, r: _hexagon(c, x, y, r + 0.5),
}


def _sym_meridian(p, x, y):
    """A meridian: a channel winding down through three lit points."""
    c = p.c
    face_hd(p, c.polyline([(x - 2.5, y - 6.0), (x + 1.5, y - 2.5), (x - 1.5, y + 2.5), (x + 2.5, y + 6.0)], 1.4))
    for dx, dy in ((-2.5, -6.0), (0.0, 0.0), (2.5, 6.0)):
        face_hd(p, c.circle(x + dx, y + dy, 2.1))


def _sym_realisation(p, x, y):
    """A Realisation: the five-point star of an insight."""
    face_hd(p, star_hd(p.c, x, y + 0.8, 5, 7.6, 3.2))


def _sym_bench(p, x, y):
    """The bench's hammer."""
    c = p.c
    warm_hd(p, c.seg(x - 5.5, y + 6.0, x + 2.0, y - 1.5, 1.7))                          # the handle
    hx, hy, d, n = x + 2.2, y - 1.8, (0.707, -0.707), (0.707, 0.707)
    face_hd(p, c.poly([(hx + a * 6.0 * n[0] + b * 2.6 * d[0], hy + a * 6.0 * n[1] + b * 2.6 * d[1])
                       for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]))                  # the head across it


def _sym_post_art(p, x, y):
    """A Post Art: a scroll on its two rollers."""
    c = p.c
    face_hd(p, c.box(x - 4.5, y - 5.0, x + 4.5, y + 5.0))
    for yy in (y - 5.5, y + 5.5):
        warm_hd(p, c.rrect(x - 6.5, yy - 1.3, x + 6.5, yy + 1.3, 1.0))
    for yy in (y - 2.0, y + 1.0):
        ink_hd(p, c.box(x - 2.8, yy, x + 2.8, yy + 1.0))


def points_badge_hd(p, plate, shape, symbol):
    c = p.c
    x, y = PLATE_C
    p.part(PLATE_SHAPE[shape](c, x, y, PLATE_R), PLATE_HD[plate], 'bevel', base=0, sep=True, hw=1, sw=1, rim=False)
    symbol(p, x, y)
    face_hd(p, c.circle(24.5, 7.5, 5.6))                                                 # the "+" knob
    ink_hd(p, c.box(21.6, 6.8, 27.4, 8.2) | c.box(23.8, 4.6, 25.2, 10.4))
    glint_hd(p, 22.4, 5.0, 0.7)


# id, plate colour, plate shape, symbol: a row a point system, as the HUD's POINT_SYSTEMS lists them.
POINT_BADGES = (
    ('points_meridian', 'jade', 'circle', _sym_meridian),
    ('points_realisation', 'violet', 'diamond', _sym_realisation),
    ('points_bench', 'bronze', 'square', _sym_bench),
    ('points_post_art', 'crimson', 'hexagon', _sym_post_art),
)
for _id, _plate, _shape, _sym in POINT_BADGES:
    glyph(_id)(lambda p, _plate=_plate, _shape=_shape, _sym=_sym: points_badge_hd(p, _plate, _shape, _sym))
