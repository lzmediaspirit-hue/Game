"""R9, the room engine's last batch (docs/architecture/room_engine.md, "The star field's end (R9)"): the pieces the
Lantern Star Field's last zones are dressed with, drawn as props (art bible §8) in the §14 manner: lit from the
north-west (tops and west faces lit, east ends and fronts a step down), outlined (§4), a floor shadow of their own. They
join the prop sheet through furnish.py (its R9 block), so the layouts place them as any prop, and a biome's flora pools
(tools/content/rooms/biomes.py) name them. Each keeps the side view's own piece in mind (tools/props/defs_lantern.py):
the same materials, the same colours, redrawn for the 3/4 view.

  the Citadel     a Warden's bronze star lantern on its post, a fallen star in its bronze cage, a stern stone Warden
                  on his plinth, the Wardens' indigo banner with its gold star, a star ballista on its turntable, a
                  chart table under a star chart, a pressure pillar of the Presence Court (its glyphs lit violet);
  the Ruins       a chunk of ruin masonry floating over its rune ring, a clump of pale gold star crystals, a gravity
                  plate (a jade glyph set in the floor, walk-through and flat), a gravity golem's broken husk;
  the Reach       an Ashborn pyre, a war tent of dark hide, an Ashborn war banner, a bed of embers (walk-through), a
                  drift of ash (walk-through), a charred tree;
  the Deep        nebula coral, its buds lit pink, and a void crab's shell, cast up on the reef;
  the Heart       a wick pillar of the Wick Gate (fluted bronze, its flame on top) and a great bronze flame basin;
  the crossings   a skiff's mast, its sail furled on the yard and its stays to the deck.

Lit pieces (the lanterns, the cage, the basins, the pyres, the embers, the pillars' flames, the crystals, the plates,
the coral's buds) carry four frames: the flame licks, the star pulses, the glyphs breathe. None is of the foliage kit,
so a ground laid after the scatter runs under every one. Every value is a coordinate hash or a constant: the build is
byte-identical.
"""
from __future__ import annotations

import math

from canvas import Img, h01
from palette import BRONZER, DARKWOOD, GOLDR, JADE, LANTERN, PAPER, STONE, WOOD, c

# ---- the star field's ramps, dark -> light, the dark end leaning violet or teal as the §14 ramps do
INDIGO = [c("161A36"), c("232B57"), c("33407E"), c("4B5FA6"), c("7489C8"), c("A9B8E6")]        # the Wardens' cloth
VERD = [c("17393A"), c("245650"), c("38786A"), c("5A9E88"), c("8CC6AC")]                      # bronze's verdigris
STAR = [c("8A5A1E"), c("C88A2E"), c("F0BE4E"), c("FFE38A"), c("FFF6CC"), c("FFFFF4")]         # a fallen star's light
VIOLET = [c("1E1636"), c("352A5E"), c("54468E"), c("7D6CC0"), c("B2A4EA"), c("E6DEFF")]       # Presence, the void
QI = [c("0F3A44"), c("17606A"), c("26908E"), c("4AC2B4"), c("9AEADC"), c("E4FFF8")]           # jade light, the runes
CRYSTAL = [c("5E4A24"), c("947232"), c("C9A24E"), c("EACB7A"), c("FFEDB8"), c("FFFCEC")]      # star crystal
ASH = [c("18161C"), c("2A2629"), c("413B3B"), c("5E5752"), c("807870"), c("A69E92"), c("CCC6B8")]
CHAR = [c("100C10"), c("1E1719"), c("312624"), c("4A3830"), c("664C3C")]                # charred wood
EMBER = [c("4E1410"), c("8A2412"), c("C4421A"), c("EE7428"), c("FFAE44"), c("FFE490")]
HIDE = [c("201719"), c("33262A"), c("4A3634"), c("634A42"), c("806252"), c("9E7E66")]       # the Ashborn's tents
CORAL = [c("10283A"), c("174652"), c("216A6E"), c("349688"), c("5CC2A6"), c("A6E8D2")]        # nebula coral
BUD = [c("4E1C4E"), c("8E3478"), c("C858A6"), c("EE8ECA"), c("FFC8EA"), c("FFF0FA")]          # its buds
SHELLV = [c("241C34"), c("3E2E52"), c("5C4672"), c("7E6492"), c("A88EB4"), c("D6C6DC")]       # a void crab's shell
GOLEM = [c("1C2026"), c("2C333A"), c("434C52"), c("5E686C"), c("7E8A88"), c("A4ACA4")]       # a golem's stone
SAIL = [c("6A6252"), c("958C76"), c("BAB09A"), c("D8D0BA"), c("EEE8D6")]                     # sailcloth


def _line(s: Img, x0: int, y0: int, x1: int, y1: int, col) -> None:
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for k in range(n + 1):
        s.put(x0 + round((x1 - x0) * k / n), y0 + round((y1 - y0) * k / n), col)


def _halo(s: Img, cx: float, cy: float, r: float, col, a: int) -> None:
    """A soft disc of light laid over what is drawn (its own alpha kept), stepped in two rings: the glow a lit thing
    throws on its own frame."""
    for j in range(int(cy - r) - 1, int(cy + r) + 2):
        for i in range(int(cx - r) - 1, int(cx + r) + 2):
            d = math.hypot(i + 0.5 - cx, j + 0.5 - cy) / r
            if d <= 1.0:
                s.blend(i, j, col, a if d < 0.55 else a // 2)


def _plinth(s: Img, x: int, y: int, w: int, h: int, ramp: list) -> None:
    """A dressed plinth `w` wide, its top two rows lit, its front a step down, its east end in shade."""
    s.rect(x, y, w, h, ramp[2])
    s.hline(x, y, w, ramp[4])
    s.hline(x, y + 1, w, ramp[3])
    s.vline(x, y, h, ramp[3])
    s.vline(x + w - 1, y + 1, h - 1, ramp[1])
    s.hline(x, y + h - 1, w, ramp[1])


def _flame(s: Img, cx: int, by: int, w: int, h: int, f: int, pal=LANTERN) -> None:
    """A flame of a few tongues rising from row `by`, `w` px wide at its foot and `h` tall; its tongues lick a pixel
    either way frame by frame."""
    lick = ((0, 1, 0, -1), (1, 0, -1, 0), (0, -1, 0, 1), (-1, 0, 1, 0))[f % 4]
    for j in range(h):
        t = j / float(max(1, h - 1))
        half = max(0.0, (w / 2.0) * (1.0 - t * 0.85))
        sway = lick[(j // 2) % 4] * (t > 0.3)
        x0, x1 = int(round(cx - half + sway)), int(round(cx + half + sway))
        for i in range(x0, x1 + 1):
            u = abs(i + 0.5 - (cx + sway)) / max(0.5, half + 0.5)
            col = pal[5] if u < 0.35 and t < 0.55 else pal[4] if u < 0.6 else pal[3] if t < 0.7 else pal[2]
            s.put(i, by - j, col)
    for k in range(3):                                           # sparks over it
        x = cx + int((h01(k, f, 611) - 0.5) * w * 1.6)
        y = by - h - 1 - int(h01(k, f, 613) * 5)
        if h01(k, f, 617) < 0.7:
            s.put(x, y, pal[4])


# ============================================================================================================ the Citadel
def warden_lamp(s: Img, f: int = 0) -> None:
    """A Warden's street lantern, as Lanternfall's and the Citadel's: a bronze post on a granite foot, a six-sided lamp
    of glass panes under a small pagoda cap with a jade finial, a little fallen star burning inside; four frames of its
    pulse. Footprint 1 x 1. 16 x 44; corner (0, 42)."""
    _plinth(s, 3, 38, 10, 4, STONE)                              # the granite foot
    s.rect(7, 18, 3, 20, BRONZER[3])                             # the post
    s.vline(7, 18, 20, BRONZER[5])
    s.vline(9, 18, 20, BRONZER[1])
    for y in (24, 31):                                           # its collars
        s.hline(6, y, 5, BRONZER[4])
        s.hline(6, y + 1, 5, BRONZER[1])
    s.rect(4, 7, 9, 11, BRONZER[2])                              # the lamp's frame
    glow = (STAR[3], STAR[4], STAR[3], STAR[2])[f % 4]
    s.rect(5, 8, 7, 9, glow)                                     # its panes, lit from within
    s.vline(8, 8, 9, BRONZER[3])                                 # the mullion between two panes
    s.ellipse(8.5, 12.5, 2.2 + (f % 2) * 0.4, 2.2 + (f % 2) * 0.4, STAR[5])   # the star in it
    s.vline(5, 8, 9, STAR[5] if f % 2 == 0 else STAR[4])
    s.hline(4, 17, 9, BRONZER[1])
    s.rect(2, 5, 13, 2, VERD[2])                                 # the cap, verdigris over bronze
    s.hline(2, 5, 13, VERD[4])
    s.put(1, 4, VERD[3])
    s.put(15, 4, VERD[1])
    s.rect(5, 3, 7, 2, VERD[3])
    s.rect(8, 0, 1, 3, JADE)                                     # the finial
    s.put(8, 0, c("7FD8C6"))
    s.outline()
    _halo(s, 8.5, 12.5, 7.0, STAR[4], 46 + 14 * (f % 2))


def lantern_cage(s: Img, f: int = 0) -> None:
    """One of the Wardens' lantern stars: a fallen star held in an old bronze cage on a fluted pedestal, the cage's
    ribs drawn in over it to a pagoda crown with a jade finial, the star burning white-gold and throwing its rays through
    the ribs; four frames of its pulse. Footprint 2 x 1. 32 x 62; corner (0, 60)."""
    _plinth(s, 2, 53, 28, 7, STONE)                              # the dais stone
    _plinth(s, 7, 49, 18, 4, STONE)
    s.rect(13, 34, 6, 15, BRONZER[3])                            # the pedestal's fluted stem
    for x in (13, 15, 17):
        s.vline(x, 34, 15, BRONZER[4] if x == 13 else BRONZER[2])
    s.hline(11, 47, 10, BRONZER[4])
    s.hline(11, 48, 10, BRONZER[1])
    cx, cy = 16, 21
    pulse = (0, 1, 2, 1)[f % 4]
    gold = [c("3A2410"), c("5E3C16"), c("8A5C1E"), c("B8822C")]  # the cage's hollow, warmed by the star
    for j in range(9, 34):                                       # the hollow inside the ribs
        for i in range(5, 28):
            d = ((i + 0.5 - cx) / 10.5) ** 2 + ((j + 0.5 - cy) / 12.5) ** 2
            if d <= 1.0:
                r = math.hypot(i + 0.5 - cx, j + 0.5 - cy)
                s.put(i, j, gold[3] if r < 7 + pulse else gold[2] if r < 9.5 + pulse else gold[1] if d < 0.8 else gold[0])
    for k in range(8):                                           # the star's rays, long and short, inside the cage
        a = k * math.pi / 4
        n = (8 if k % 2 == 0 else 6) + pulse
        for r in range(3, n):
            s.put(int(round(cx + math.cos(a) * r)), int(round(cy + math.sin(a) * r)), STAR[4] if r < n - 2 else STAR[3])
    s.ellipse(cx, cy, 4.2 + pulse * 0.3, 4.2 + pulse * 0.3, STAR[4])   # the star
    s.ellipse(cx - 0.5, cy - 0.5, 2.4, 2.4, STAR[5])
    for i in (6, 9, 12, 20, 23, 26):                             # the cage's ribs, bowed round the star
        for j in range(9, 34):
            t = (j - 9) / 24.0
            x = int(round(cx + (i - cx) * math.sin(math.pi * (0.08 + 0.84 * t))))
            col = BRONZER[5] if i < 10 else BRONZER[4] if i < cx else BRONZER[3] if i < 24 else BRONZER[2]
            s.put(x, j, col)
    for y in (14, 28):                                           # its two hoops
        half = 10.5 * math.sin(math.pi * (0.08 + 0.84 * (y - 9) / 24.0))
        for i in range(int(cx - half), int(cx + half) + 1):
            s.put(i, y, BRONZER[4] if i < cx else BRONZER[2])
    s.hline(10, 33, 13, BRONZER[3])
    s.hline(10, 34, 13, BRONZER[1])
    s.rect(9, 6, 15, 3, VERD[2])                                 # the crown, verdigris
    s.hline(8, 6, 17, VERD[4])
    s.put(7, 5, VERD[3])
    s.put(25, 5, VERD[1])
    s.rect(12, 3, 9, 3, VERD[3])
    s.rect(16, 0, 1, 3, JADE)
    s.put(16, 0, c("7FD8C6"))
    s.outline()
    _halo(s, cx, cy, 15, STAR[4], 40 + 10 * pulse)


def warden_statue(s: Img) -> None:
    """A stern stone Star Warden on his plinth, footprint 1 x 1: helmed, a cloak falling from his shoulders to his feet,
    a star cut in his breastplate, his right hand on a glaive's haft and his left holding up a little lantern, moss in
    the folds of the old stone. 24 x 58; corner (4, 56)."""
    _plinth(s, 1, 47, 22, 9, STONE)
    s.hline(2, 51, 20, STONE[1])
    for j in range(22, 47):                                      # the cloak, widening to its hem
        half = 5 + (j - 22) // 6
        for i in range(12 - half, 12 + half + 1):
            k = 4 if i < 12 - half + 2 else (1 if i > 12 + half - 2 else 3)
            if (i - 12) % 3 == 1 and j > 32:
                k -= 1
            s.put(i, j, STONE[k])
    s.rect(8, 22, 8, 12, STONE[3])                               # the breastplate
    s.vline(8, 22, 12, STONE[5])
    s.vline(15, 22, 12, STONE[2])
    for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0), (0, 0), (-1, -1), (1, 1), (1, -1), (-1, 1)):   # the star cut in it
        s.put(12 + dx, 27 + dy, STONE[1] if dx or dy else STONE[5])
    s.rect(6, 19, 12, 4, STONE[4])                               # the shoulders, the pauldrons
    s.hline(5, 19, 14, STONE[5])
    s.ellipse(12, 13, 4.2, 4.6, STONE[3], (STONE[5], STONE[1]))  # the helm
    s.rect(9, 13, 7, 2, STONE[1])                                # its visor's slit
    s.hline(10, 13, 5, STONE[0])
    for j in range(4, 9):                                        # its crest
        s.put(12, j, STONE[4] if j % 2 else STONE[5])
    s.vline(20, 4, 44, DARKWOOD[2])                              # the glaive's haft, his hand on it
    s.vline(21, 6, 40, DARKWOOD[1])
    for j in range(0, 7):                                        # its blade
        s.put(20, j, STONE[5] if j < 3 else STONE[4])
        s.put(21, j + 1, STONE[3])
    s.put(19, 5, STONE[4])
    s.rect(18, 30, 3, 3, STONE[4])
    s.rect(2, 26, 3, 6, STONE[4])                                # the left arm up, the lantern in its hand
    s.rect(1, 31, 5, 5, BRONZER[2])
    s.rect(2, 32, 3, 3, STAR[3])
    s.put(2, 32, STAR[5])
    for k in range(9):                                           # moss in the folds
        x, y = 5 + int(h01(k, 1, 901) * 14), 34 + int(h01(k, 2, 901) * 12)
        if s.get(x, y)[3]:
            s.put(x, y, c("4E7A48") if k % 2 else c("6A9654"))
    s.outline()


def warden_banner(s: Img, f: int = 0) -> None:
    """The Star Wardens' banner on its pole, footprint 1 x 1: deep indigo cloth bordered in gold, a gold eight-rayed
    star in its middle, its tail stirring on the star wind (four frames, as the sects' banners). 16 x 62; corner
    (0, 60)."""
    _plinth(s, 3, 56, 10, 4, STONE)
    s.vline(3, 2, 54, DARKWOOD[3])                               # the pole
    s.vline(4, 2, 54, DARKWOOD[2])
    s.rect(2, 0, 4, 2, GOLDR[2])
    s.hline(3, 5, 12, GOLDR[1])                                  # the crossbar
    tail = (0, 1, 2, 1)[f % 4]
    for j in range(6, 46):
        w = 10 if j < 40 else 10 - (j - 40)
        shift = int(round(math.sin((j - 6) / 9.0 + f * 1.57) * 0.8)) if j > 30 else 0
        for i in range(5, 5 + max(2, w) + (tail if j > 38 else 0)):
            col = INDIGO[3] if i < 7 else INDIGO[1] if i > 12 else INDIGO[2]
            if j in (6, 7) or i == 5 or (i >= 4 + w and j < 40):
                col = GOLDR[2]
            s.put(i + shift, j, col)
    cx, cy = 10, 20
    for k in range(8):                                           # the star
        a = k * math.pi / 4
        n = 5 if k % 2 == 0 else 3
        for r in range(n):
            s.put(int(round(cx + math.cos(a) * r)), int(round(cy + math.sin(a) * r)), GOLDR[3] if r < 2 else GOLDR[2])
    s.put(cx, cy, GOLDR[4])
    for j in (30, 33):                                           # two gold rules under it
        s.hline(6, j, 6, GOLDR[1])
    s.outline()


def ballista(s: Img) -> None:
    """A star ballista of the Wall, footprint 2 x 1: a heavy bow of dark timber and bronze on a turntable, its string
    drawn back to the winch, a long bolt with a star-steel head laid in its groove, pointing out over the wall. 32 x 30;
    corner (0, 28)."""
    s.ellipse(16, 24, 14, 4.5, STONE[2], (STONE[4], STONE[1]))   # the turntable on its stone ring
    s.ellipse(16, 23, 11, 3.2, DARKWOOD[2])
    s.hline(6, 23, 20, DARKWOOD[3])
    s.rect(13, 13, 6, 10, DARKWOOD[2])                           # the post and the stock
    s.vline(13, 13, 10, DARKWOOD[4])
    s.rect(4, 12, 24, 3, WOOD[3])                                # the stock, long across the turntable
    s.hline(4, 12, 24, WOOD[5])
    s.hline(4, 14, 24, WOOD[1])
    for i in range(0, 13):                                       # the bow's two arms, swept back
        s.put(14 - i, 10 - int(i * 0.45), WOOD[4])
        s.put(14 - i, 11 - int(i * 0.45), DARKWOOD[1])
        s.put(18 + i, 10 - int(i * 0.45), WOOD[3])
        s.put(18 + i, 11 - int(i * 0.45), DARKWOOD[1])
    _line(s, 2, 5, 9, 12, PAPER)                                 # the string, drawn back
    _line(s, 30, 5, 23, 12, PAPER)
    s.rect(14, 8, 4, 3, BRONZER[3])                              # the bronze fittings and the winch
    s.rect(24, 15, 4, 4, BRONZER[2])
    s.put(24, 15, BRONZER[4])
    s.hline(1, 11, 28, DARKWOOD[3])                              # the bolt
    s.rect(0, 10, 3, 3, STONE[5])
    s.put(0, 11, STAR[4])
    s.outline()


def star_chart_table(s: Img) -> None:
    """A Warden's chart table, footprint 2 x 1: dark wood on turned legs, a star chart spread on it (pale paper, the
    constellations' points and lines in ink and gold), a brass dividers and a lens on it, a lamp at one corner. 32 x 28;
    corner (0, 26)."""
    for x in (2, 28):                                            # the legs
        s.rect(x, 16, 2, 10, DARKWOOD[2])
        s.vline(x, 16, 10, DARKWOOD[3])
    s.rect(0, 6, 32, 10, WOOD[2])                                # the top
    s.hline(0, 6, 32, WOOD[4])
    s.rect(0, 13, 32, 3, WOOD[1])
    s.hline(0, 15, 32, DARKWOOD[1])
    s.rect(3, 6, 24, 7, PAPER)                                   # the chart
    s.hline(3, 6, 24, c("F6F1E3"))
    s.vline(26, 6, 7, c("BDB39C"))
    stars = [(6, 8), (9, 10), (12, 8), (15, 9), (18, 11), (21, 8), (24, 10), (8, 11), (20, 7)]
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (4, 6), (3, 5)):
        _line(s, stars[a][0], stars[a][1], stars[b][0], stars[b][1], c("8A99B8"))
    for k, (x, y) in enumerate(stars):
        s.put(x, y, GOLDR[1] if k % 3 else INDIGO[2])
    _line(s, 11, 12, 15, 7, BRONZER[4])                          # the dividers
    _line(s, 15, 7, 18, 12, BRONZER[3])
    s.ellipse(23.5, 11, 1.8, 1.4, c("C8E4EC"), (c("F4FCFF"), BRONZER[2]))   # the lens
    s.rect(28, 2, 3, 4, BRONZER[3])                              # the lamp at its corner
    s.put(29, 3, STAR[4])
    s.outline()


def star_globe(s: Img) -> None:
    """The Observatory's armillary of the heavens, footprint 2 x 1: bronze rings of the sky's circles round a little
    gilt sun, tilted on their meridian ring in a four-legged stand of dark wood, the ecliptic's band picked out in gold.
    32 x 46; corner (0, 44)."""
    for x0, x1 in ((3, 9), (29, 23)):                            # the stand's legs, splayed
        _line(s, x0, 43, x1, 30, DARKWOOD[3] if x0 < 16 else DARKWOOD[2])
        _line(s, x0 + 1, 43, x1 + 1, 30, DARKWOOD[1])
    s.rect(8, 29, 16, 3, WOOD[3])                                # the horizon ring's wooden band
    s.hline(8, 29, 16, WOOD[5])
    s.hline(8, 31, 16, DARKWOOD[1])
    cx, cy = 16, 17
    for k, (rx, ry, tilt) in enumerate(((12, 12, 0.0), (12, 4, 0.35), (4, 12, 0.0), (12, 6, -0.6))):
        col = (BRONZER[4], GOLDR[2], BRONZER[3], BRONZER[2])[k]
        for t in range(160):
            a = t * math.pi * 2 / 160
            x, y = math.cos(a) * rx, math.sin(a) * ry
            x, y = x * math.cos(tilt) - y * math.sin(tilt), x * math.sin(tilt) + y * math.cos(tilt)
            s.put(int(round(cx + x)), int(round(cy + y)), col)
    s.ellipse(cx, cy, 2.6, 2.6, GOLDR[2], (GOLDR[4], GOLDR[1]))  # the sun at its heart
    s.vline(cx, 3, 28, BRONZER[1])                               # the polar axis
    s.put(cx, 3, GOLDR[3])
    s.outline()


def pressure_pillar(s: Img, f: int = 0) -> None:
    """A pressure pillar of the Presence Court, footprint 1 x 1: a square column of dark slate on a stepped foot, a
    capital of granite, a long panel down its face cut with glyphs that glow violet as a Presence presses on the court
    (four frames of their breath). 16 x 64; corner (0, 62)."""
    _plinth(s, 0, 56, 16, 6, STONE)
    _plinth(s, 2, 53, 12, 3, STONE)
    slate = [c("161826"), c("23263A"), c("343852"), c("4A506C")]
    s.rect(3, 9, 10, 44, slate[2])                               # the shaft
    s.vline(3, 9, 44, slate[3])
    s.vline(12, 9, 44, slate[0])
    s.rect(5, 12, 6, 38, slate[1])                               # the panel
    glow = VIOLET[(3, 4, 3, 2)[f % 4]]
    for j in range(13, 49):                                      # its glyphs, lit
        if j % 5 in (0, 3):
            continue
        for i in range(6, 10):
            if h01(i, j // 5, 977) < 0.55 or (j % 5 == 1 and i in (6, 9)):
                s.put(i, j, glow)
    s.vline(8, 13, 36, VIOLET[2])
    _plinth(s, 1, 4, 14, 5, STONE)                               # the capital
    s.rect(4, 0, 8, 4, STONE[3])
    s.hline(4, 0, 8, STONE[5])
    s.outline()
    _halo(s, 8, 30, 9, VIOLET[3], 22 + 12 * (f % 2))


# ============================================================================================================ the Ruins
def orbit_stone(s: Img, f: int = 0) -> None:
    """A piece of the first Wardens' temple that floats over its rune ring in the Orbit Ruins, as the side view's
    islands do, footprint 2 x 1: the ring a circle of jade glyphs cut in the floor, softly lit; well over it a little
    island of the temple, dressed masonry on top (a stub of wall, moss in its joints) on a cone of broken rock tapering
    down to a point; four frames of its slow bob (it rides up and down a pixel or two, its shadow on the ring breathing
    with it). 32 x 52; corner (0, 50)."""
    bob = (0, -1, -2, -1)[f % 4]
    for i in range(0, 32):                                       # the rune ring on the floor
        for j in range(38, 50):
            u, v = (i + 0.5 - 16) / 15.5, (j + 0.5 - 44) / 5.6
            d = u * u + v * v
            if 0.62 <= d <= 1.0:
                s.put(i, j, QI[2] if (i + j) % 5 else QI[3])
            elif 0.45 <= d < 0.62 and (i * 7 + j * 3) % 11 == 0:
                s.put(i, j, QI[1])
    for k in range(6):                                           # its glyph marks
        a = k * math.pi / 3 + 0.4
        s.put(int(16 + math.cos(a) * 13), int(44 + math.sin(a) * 4.6), QI[4])
    sh = 6 - (f % 4 in (1, 3)) - 2 * (f % 4 == 2)                # the island's shadow on the ring
    s.ellipse(16, 44, sh, 1.8, c("142A30"))
    rock = [c("201C2C"), c("332D40"), c("4A4458"), c("625C6E"), c("837C8A")]
    y0 = 2 + bob
    top = y0 + 12                                                # the island's flat top, its masonry on it
    for j in range(top, top + 22):                               # the rock cone under it, tapering to a point
        t = (j - top) / 21.0
        half = 13 * (1.0 - t) ** 1.3 + 0.5
        wob = (h01(j // 2, 1, 929) - 0.5) * 2.5 * (1.0 - t)
        for i in range(int(16 - half + wob), int(16 + half + wob) + 1):
            u = (i + 0.5 - (16 - half + wob)) / (2 * half + 1)
            col = rock[3] if u < 0.3 else rock[2] if u < 0.7 else rock[1]
            if h01(i, j, 931) < 0.12:
                col = rock[0] if u > 0.5 else rock[4]
            s.put(i, j, col)
    s.ellipse(16, top, 14, 3.2, STONE[3], (STONE[5], STONE[2]))  # the island's top, its paving
    for i in range(4, 29, 5):
        s.put(i, top, STONE[2])
    s.rect(6, y0 + 3, 10, 8, STONE[2])                           # a stub of the temple's wall on it
    s.rect(6, y0, 10, 3, STONE[4])
    s.hline(6, y0, 10, STONE[5])
    s.vline(6, y0, 11, STONE[4])
    s.vline(15, y0 + 1, 10, STONE[1])
    s.hline(7, y0 + 6, 8, STONE[1])
    s.vline(11, y0 + 3, 3, STONE[1])
    s.rect(19, y0 + 7, 4, 4, STONE[3])                           # a fallen block beside it
    s.hline(19, y0 + 7, 4, STONE[5])
    for k in range(9):                                           # moss in its joints and on the rock's lip
        x, y = 5 + int(h01(k, 1, 923) * 22), top - 1 + int(h01(k, 2, 923) * 3)
        s.put(x, y, c("4E8A4C") if k % 3 else c("7CB060"))
    s.outline()


def crystal_cluster(s: Img, f: int = 0) -> None:
    """A clump of star crystals grown out of a rock, footprint 1 x 1: long pale gold prisms, lit on their west faces,
    their tips white; a glint runs up one of them frame by frame. 24 x 34; corner (4, 32)."""
    s.ellipse(12, 29, 10, 3.6, c("3A3A44"), (c("5A5A66"), c("24242C")))   # the rock they grow from
    prisms = [(7, 27, 12, -0.25, 3), (12, 28, 24, 0.0, 4), (16, 27, 17, 0.3, 3), (19, 28, 9, 0.5, 2), (4, 28, 8, -0.5, 2)]
    for k, (bx, by, h, lean, w) in enumerate(prisms):
        for j in range(h):
            x0 = bx + int(round(lean * j)) - w // 2
            tip = j > h - 3
            for i in range(w if not tip else max(1, w - (j - (h - 3)))):
                col = CRYSTAL[4] if i == 0 else CRYSTAL[2] if i == w - 1 else CRYSTAL[3]
                if tip:
                    col = CRYSTAL[5]
                s.put(x0 + i + (1 if tip and j == h - 1 else 0), by - j, col)
        if k == f % 4:                                           # the glint running up
            g = int(h * (0.3 + 0.15 * (f % 4)))
            s.put(bx + int(round(lean * g)) - w // 2, by - g, CRYSTAL[5])
    s.outline()
    _halo(s, 12, 18, 10, CRYSTAL[4], 30)


def gravity_plate(s: Img, f: int = 0) -> None:
    """A gravity plate set in the floor where a jade switch lightens the air, footprint 1 x 1 (walk-through, flat): a
    square of dark stone with a ring of jade glyphs round an inner star, breathing frame by frame. 16 x 16; corner
    (0, 16)."""
    stone = [c("1E2430"), c("2C3442"), c("3E4858"), c("566274")]
    s.rect(1, 1, 14, 14, stone[2])
    s.hline(1, 1, 14, stone[1])
    s.vline(1, 1, 14, stone[1])
    s.hline(1, 14, 14, stone[3])
    s.vline(14, 1, 14, stone[3])
    lit = QI[(3, 4, 3, 2)[f % 4]]
    for i in range(2, 14):
        for j in range(2, 14):
            d = math.hypot(i + 0.5 - 8, j + 0.5 - 8)
            if 4.4 <= d <= 5.6 and (i + j) % 3:
                s.put(i, j, lit)
    for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0), (0, 0)):
        s.put(8 + dx, 8 + dy, QI[4] if dx or dy else QI[5])


def golem_husk(s: Img) -> None:
    """A gravity golem's husk, broken where it fell, footprint 2 x 1: the great stone torso on its side, a shoulder
    block and a fist beside it, the jade core in its chest gone dim, cracks through the stone. 32 x 28; corner (0, 26)."""
    s.ellipse(15, 18, 11, 7, GOLEM[3], (GOLEM[5], GOLEM[1]))     # the torso
    s.rect(8, 14, 14, 4, GOLEM[4])
    s.hline(8, 14, 14, GOLEM[5])
    s.ellipse(15, 18, 3, 2.6, QI[1], (QI[2], QI[0]))             # the dim core
    s.put(14, 17, QI[3])
    _line(s, 6, 16, 11, 22, GOLEM[1])                            # cracks
    _line(s, 19, 13, 23, 20, GOLEM[1])
    s.rect(24, 15, 7, 8, GOLEM[2])                               # the shoulder block
    s.hline(24, 15, 7, GOLEM[4])
    s.vline(24, 15, 8, GOLEM[3])
    s.rect(0, 19, 6, 6, GOLEM[3])                                # the fist
    s.hline(0, 19, 6, GOLEM[5])
    for x in (1, 3):
        s.vline(x, 20, 4, GOLEM[1])
    for k in range(6):                                           # rubble round it
        x = 2 + int(h01(k, 1, 941) * 28)
        s.put(x, 25, GOLEM[4])
        s.put(x + 1, 25, GOLEM[2])
    s.outline()


# ============================================================================================================ the Reach
def ash_pyre(s: Img, f: int = 0) -> None:
    """An Ashborn pyre, footprint 2 x 1: split logs stacked crosswise in narrowing tiers inside a ring of blackened
    stones, the fire roaring up out of it, embers glowing between the logs; four frames of the flames. 32 x 48; corner
    (0, 46)."""
    for k in range(9):                                           # the ring of stones
        a = math.pi * (0.05 + 0.9 * k / 8.0)
        x, y = 16 - math.cos(a) * 14, 41 + math.sin(a) * 3.5
        s.ellipse(x, y, 2.4, 1.8, ASH[3], (ASH[4], ASH[1]))
    for tier in range(4):                                        # the logs, crosswise, narrowing
        y = 40 - tier * 4
        half = 12 - tier * 2
        for i in range(16 - half, 16 + half):
            s.put(i, y, CHAR[3])
            s.put(i, y + 1, CHAR[2] if (i + tier) % 5 else EMBER[3])
            s.put(i, y + 2, CHAR[1])
        for x in (16 - half, 16 + half - 2):                     # the log ends
            s.rect(x, y, 2, 3, WOOD[3] if x < 16 else WOOD[2])
            s.put(x, y + 1, EMBER[4] if (tier + f) % 2 else EMBER[3])
    _flame(s, 16, 26, 16, 22, f, EMBER)
    _flame(s, 10, 30, 6, 10, f + 1, EMBER)
    _flame(s, 22, 30, 6, 11, f + 2, EMBER)
    s.outline()
    _halo(s, 16, 22, 14, EMBER[4], 30)


def cinder_tent(s: Img) -> None:
    """An Ashborn war tent on the Cinder Fields, footprint 4 x 2: a long ridge tent of dark stitched hide over a low
    frame, its flap tied open on a lit lamp, the red flame sigil daubed on its roof, stakes and guy-ropes down to the
    ground, a pennant at each end of the ridge. 64 x 58; corner (0, 56)."""
    back, ridge, eave, foot = 6, 18, 42, 54
    for i in range(4, 60):                                       # the back slope, lit, from its eave up to the ridge
        for j in range(back + (1 if i in (4, 59) else 0), ridge):
            col = HIDE[5] if j < back + 2 else HIDE[4]
            if (i - 4) % 9 == 0:
                col = HIDE[3]                                    # its seams
            s.put(i, j, col)
    s.hline(3, ridge, 58, c("B49276"))                           # the ridge pole's lit line
    for i in range(3, 61):                                       # the front slope, down toward the eave, in shade
        sag = int(round(1.5 * math.sin(math.pi * ((i - 3) % 14) / 14.0)))
        for j in range(ridge + 1, eave + sag):
            t = (j - ridge) / float(eave - ridge)
            col = HIDE[3] if t < 0.5 else HIDE[2]
            if (i - 3) % 14 == 0 or (i * 5 + j * 3) % 23 == 0:
                col = HIDE[1]                                    # its seams and stitching
            s.put(i, j, col)
        s.put(i, eave + sag, HIDE[1])
    for x0, d in ((3, -1), (60, 1)):                             # the gable ends, triangles of hide
        for k in range(6):
            s.vline(x0 + d * k, ridge + k * 3, eave - ridge - k * 3, HIDE[2] if d < 0 else HIDE[1])
    for j in range(eave + 1, foot):                              # the low front wall under the eave
        for i in range(5, 59):
            s.put(i, j, HIDE[2] if i > 9 else HIDE[3])
    s.hline(5, foot - 1, 54, HIDE[0])
    for j in range(eave - 6, foot):                              # the flap tied open on the dark inside
        half = int((j - (eave - 6)) * 0.45) + 1
        s.hline(32 - half, j, 2 * half, c("120C0E"))
    s.rect(30, foot - 6, 4, 3, EMBER[4])                         # the lamp in it
    s.put(31, foot - 6, EMBER[5])
    _line(s, 31, eave - 6, 24, foot - 1, HIDE[4])
    _line(s, 33, eave - 6, 40, foot - 1, HIDE[3])
    cx, cy = 32, 28                                              # the flame sigil
    for dx, h in ((-3, 6), (0, 9), (3, 6)):
        for j in range(h):
            s.put(cx + dx + (1 if j > h - 3 and dx < 0 else -1 if j > h - 3 and dx > 0 else 0), cy + 4 - j, EMBER[2])
    s.hline(cx - 4, cy + 5, 9, EMBER[1])
    for x in (2, 61):                                            # the pennants
        s.vline(x, 4, 12, DARKWOOD[2])
        for j in range(3):
            s.hline(x + (1 if x < 30 else -4), 4 + j, 4 - j, EMBER[3])
    for x in (0, 63):                                            # stakes and guy-ropes
        _line(s, x, 54, x + (6 if x < 30 else -6), 30, ASH[4])
        s.rect(x, 52, 1, 3, DARKWOOD[3])
    s.outline()


def ashborn_banner(s: Img, f: int = 0) -> None:
    """A tall Ashborn war banner, footprint 1 x 1: ash-grey cloth bordered in ember red, the red flame sigil in a
    ring on it, its ragged tail stirring on the hot wind (four frames). 16 x 62; corner (0, 60)."""
    s.ellipse(8, 58, 6, 2.2, ASH[2], (ASH[4], ASH[1]))           # a cairn at its foot
    s.vline(3, 2, 56, CHAR[3])                                   # the pole
    s.vline(4, 2, 56, CHAR[2])
    s.rect(2, 0, 4, 3, EMBER[3])
    s.hline(3, 5, 12, CHAR[3])
    tail = (0, 1, 2, 1)[f % 4]
    for j in range(6, 46):
        w = 10 if j < 38 else 10 - (j - 38) // 2
        shift = int(round(math.sin((j - 6) / 8.0 + f * 1.57) * 0.8)) if j > 28 else 0
        for i in range(5, 5 + w + (tail if j > 36 else 0)):
            col = ASH[5] if i < 7 else ASH[3] if i > 12 else ASH[4]
            if j in (6, 7) or i == 5 or (i >= 4 + w and j < 38):
                col = EMBER[2]
            if j > 40 and (i + j) % 4 == 0:
                continue                                         # the ragged tail
            s.put(i + shift, j, col)
    for i in range(6, 15):                                       # the ring round the sigil
        for j in range(13, 26):
            d = math.hypot(i + 0.5 - 10.5, j + 0.5 - 19)
            if 3.6 <= d <= 4.6:
                s.put(i, j, EMBER[2])
    for dx, h in ((-1, 3), (0, 5), (1, 3)):                      # the sigil
        for j in range(h):
            s.put(10 + dx, 21 - j, EMBER[3] if j < h - 1 else EMBER[4])
    s.outline()


def embers(s: Img, f: int = 0) -> None:
    """A bed of embers where a fire burned down on the plain, footprint 2 x 1 (walk-through, flat): a ring of black
    char and grey ash round a heart of coals glowing orange through it, charred sticks across it, the glow moving
    coal to coal frame by frame. 32 x 16; corner (0, 16)."""
    for i in range(32):
        for j in range(16):
            d = math.hypot((i + 0.5 - 16) / 14.5, (j + 0.5 - 8.5) / 6.5)
            if d > 1.0 or h01(i, j, 953) > 1.25 - d * 0.5:
                continue
            col = ASH[4] if d > 0.82 else CHAR[1] if d > 0.6 else CHAR[2] if d > 0.4 else EMBER[1]
            s.put(i, j, col)
    _line(s, 6, 11, 22, 6, CHAR[3])                              # charred sticks across it
    _line(s, 10, 5, 25, 11, CHAR[2])
    for k in range(14):                                          # the coals, glowing
        a, r = h01(k, 1, 957) * math.pi * 2, h01(k, 2, 957) ** 0.7
        x, y = int(16 + math.cos(a) * r * 8), int(8.5 + math.sin(a) * r * 3.5)
        hot = (k + f) % 4 == 0
        s.put(x, y, EMBER[5] if hot else EMBER[3] if k % 2 else EMBER[4])
        s.put(x + 1, y, EMBER[4] if hot else EMBER[2])
    s.outline()


def ash_drift(s: Img) -> None:
    """A drift of ash blown against the plain's stones, footprint 2 x 1 (walk-through, flat): a low mound of pale grey
    ash, lit along its windward crest and darker in its lee, the wind's ripples across it and a charred stick half
    buried. 32 x 16; corner (0, 16)."""
    for i in range(32):
        for j in range(16):
            u, v = (i + 0.5 - 16) / 15.5, (j + 0.5 - 9) / 6.2
            d = u * u + v * v
            if d > 1.0 or h01(i // 2, j, 961) > 1.5 - d:
                continue
            col = ASH[6] if v < -0.35 else ASH[5] if v < 0.25 else ASH[4] if v < 0.65 else ASH[3]
            if (i + int(j * 2.2)) % 9 == 0 and v > -0.35:
                col = ASH[4] if v < 0.25 else ASH[3]             # the wind's ripples
            s.put(i, j, col)
    _line(s, 20, 8, 26, 6, CHAR[2])
    s.outline()


def charred_tree(s: Img) -> None:
    """A tree the fires of the Reach burned to its bones, footprint 1 x 1: a black trunk split and splintered at the
    top, two stub branches, its bark crazed with glowing cracks where it still smoulders. 40 x 58; corner (12, 56)."""
    s.ellipse(20, 55, 8, 2.2, ASH[2])                            # ash round its foot
    for j in range(14, 55):                                      # the trunk, widening to the roots
        half = 2 + (j - 14) // 14 + (2 if j > 50 else 0)
        for i in range(20 - half, 20 + half + 1):
            col = CHAR[3] if i < 20 - half + 2 else CHAR[1] if i > 20 + half - 1 else CHAR[2]
            s.put(i, j, col)
    for k, (x, y) in enumerate(((19, 13), (21, 9), (18, 6), (22, 4))):   # its splintered top
        s.vline(x, y, 14 - y + 3, CHAR[3] if k % 2 else CHAR[2])
    _line(s, 18, 30, 8, 20, CHAR[2])                             # two stub branches
    _line(s, 18, 31, 9, 22, CHAR[1])
    _line(s, 22, 24, 32, 15, CHAR[2])
    _line(s, 30, 15, 31, 11, CHAR[2])
    for k in range(7):                                           # the cracks still glowing
        x, y = 18 + int(h01(k, 1, 967) * 5), 20 + int(h01(k, 2, 967) * 30)
        s.put(x, y, EMBER[3] if k % 2 else EMBER[2])
    s.outline()


# ============================================================================================================ the Deep
def nebula_coral(s: Img, f: int = 0) -> None:
    """Nebula coral on a reef stone, footprint 1 x 1: fans of teal fronds branching up and out, their buds lit pink,
    one bud after another brightening frame by frame. 24 x 36; corner (4, 34)."""
    s.ellipse(12, 31, 9, 3.4, c("2A2E44"), (c("464C68"), c("181A2A")))   # the reef stone
    branches = [((12, 30), (11, 18), (7, 8)), ((12, 30), (14, 17), (19, 7)), ((11, 26), (5, 19), (2, 12)),
                ((13, 26), (19, 21), (22, 14)), ((12, 22), (12, 12), (12, 3))]
    buds = []
    for k, (a, b, t) in enumerate(branches):
        _line(s, a[0], a[1], b[0], b[1], CORAL[3] if k % 2 else CORAL[4])
        _line(s, a[0] + 1, a[1], b[0] + 1, b[1], CORAL[2])
        _line(s, b[0], b[1], t[0], t[1], CORAL[4])
        _line(s, b[0], b[1], b[0] + (3 if k % 2 else -3), b[1] - 4, CORAL[3])
        buds += [t, (b[0] + (3 if k % 2 else -3), b[1] - 4)]
    for k, (x, y) in enumerate(buds):
        lit = k % 4 == f % 4
        s.ellipse(x + 0.5, y + 0.5, 1.6, 1.6, BUD[4] if lit else BUD[3])
        s.put(x, y, BUD[5] if lit else BUD[4])
    s.outline()
    for k, (x, y) in enumerate(buds):
        if k % 4 == f % 4:
            _halo(s, x + 0.5, y + 0.5, 4, BUD[4], 50)


def coral_tree(s: Img, f: int = 0) -> None:
    """A coral tree of the Nebula Deep, as the side view's islands grow them, footprint 1 x 1: a twisted dark trunk
    forking into branches, its crown in puffs of pink and of cyan light, one puff after another brightening frame by
    frame. 40 x 60; corner (12, 58)."""
    bark = [c("140F1E"), c("231A30"), c("372A44"), c("4E3E5A")]
    s.ellipse(20, 57, 7, 2, c("1E2236"))                         # the reef stone at its foot
    for j in range(26, 57):                                      # the trunk, leaning and twisting
        x = 19 + int(round(math.sin(j / 7.0) * 1.5))
        half = 1 + (j - 26) // 12
        for i in range(x - half, x + half + 1):
            s.put(i, j, bark[3] if i == x - half else bark[1] if i == x + half else bark[2])
    for (x0, y0, x1, y1) in ((19, 34, 8, 22), (20, 32, 31, 20), (19, 28, 14, 14), (20, 27, 26, 12), (19, 30, 20, 10)):
        _line(s, x0, y0, x1, y1, bark[2])
        _line(s, x0 + 1, y0, x1 + 1, y1, bark[1])
    puffs = [(8, 19, 6, 0), (15, 11, 6, 1), (24, 9, 7, 0), (32, 17, 6, 1), (20, 18, 6, 1), (11, 25, 4, 1), (29, 24, 4, 0),
             (19, 5, 4, 1)]
    for k, (x, y, r, cyan) in enumerate(puffs):                  # the crown's puffs, pink and cyan
        ramp = CORAL if cyan else BUD
        lit = k % 4 == f % 4
        for j in range(int(y - r) - 1, int(y + r) + 2):
            for i in range(int(x - r) - 1, int(x + r) + 2):
                d = math.hypot(i + 0.5 - x, (j + 0.5 - y) * 1.15)
                if d > r or h01(i, j, 991 + k) < (d / r) ** 3 * 0.8:
                    continue
                col = ramp[5 if lit and d < r * 0.45 else 4] if (i - x) + (j - y) < -r * 0.3 else ramp[3] if d < r * 0.7 else ramp[2]
                s.put(i, j, col)
    s.outline()
    for k, (x, y, r, cyan) in enumerate(puffs):
        if k % 4 == f % 4:
            _halo(s, x, y, r + 3, (CORAL if cyan else BUD)[4], 40)


def void_shell(s: Img) -> None:
    """A void crab's cast shell on the reef, footprint 2 x 1: a broad carapace of violet-grey plates, spined along its
    rim, a great claw lying beside it, the nebula's light caught in its pearly hollows. 32 x 26; corner (0, 24)."""
    s.ellipse(14, 15, 12, 7.5, SHELLV[3], (SHELLV[5], SHELLV[1]))   # the carapace
    s.ellipse(14, 14, 8.5, 4.5, SHELLV[4])
    for k in range(9):                                           # the spines round its rim
        a = math.pi * (1.05 + 0.9 * k / 8.0)
        x, y = 14 + math.cos(a) * 12.5, 15 + math.sin(a) * 8
        s.put(int(x), int(y) - 1, SHELLV[5] if k < 4 else SHELLV[3])
    for x in (9, 14, 19):                                        # its plates' seams
        _line(s, x, 9, x + (x - 14) // 3, 20, SHELLV[2])
    s.ellipse(12, 12, 2.5, 1.4, c("E8DCF6"))                     # the pearly glint
    s.ellipse(27, 19, 4.5, 3, SHELLV[3], (SHELLV[5], SHELLV[1]))   # the claw
    s.rect(26, 13, 2, 5, SHELLV[4])
    s.rect(29, 14, 2, 4, SHELLV[2])
    s.outline()


# ============================================================================================================ the Heart
def wick_pillar(s: Img, f: int = 0) -> None:
    """A wick pillar of the Lantern Heart, footprint 1 x 1: a tall fluted shaft of bronze ringed with gilt collars, a
    star set in a medallion halfway up, a cup at its crown where the first lantern's fire burns; four frames of the
    flame. 16 x 76; corner (0, 74)."""
    _plinth(s, 0, 67, 16, 7, STONE)
    s.rect(2, 62, 12, 5, BRONZER[3])
    s.hline(2, 62, 12, BRONZER[5])
    s.rect(4, 22, 8, 40, BRONZER[3])                             # the shaft, fluted
    for x in (4, 6, 8, 10):
        s.vline(x, 22, 40, BRONZER[5] if x == 4 else BRONZER[4] if x == 6 else BRONZER[2])
    s.vline(11, 22, 40, BRONZER[1])
    for y in (30, 46, 58):                                       # the gilt collars
        s.rect(3, y, 10, 2, GOLDR[2])
        s.hline(3, y, 10, GOLDR[3])
    s.ellipse(8, 38, 3, 3, GOLDR[2], (GOLDR[3], GOLDR[1]))       # the star medallion
    s.put(8, 38, STAR[5])
    for y in (34, 42):
        s.put(8, y, GOLDR[3])
    s.rect(1, 18, 14, 4, BRONZER[3])                             # the cup
    s.hline(1, 18, 14, BRONZER[5])
    s.hline(2, 21, 12, BRONZER[1])
    s.rect(2, 17, 12, 1, EMBER[4])
    _flame(s, 8, 17, 10, 16, f, LANTERN)
    s.outline()
    _halo(s, 8, 10, 9, STAR[3], 40)


def flame_basin(s: Img, f: int = 0) -> None:
    """A great bronze flame basin of the Hall of Burning Stars, footprint 2 x 1: a round-bellied cauldron on three lion
    feet, verdigris in its grooves, a gilt rim, the star-fire heaped in it and roaring up; four frames of the flames.
    32 x 46; corner (0, 44)."""
    for x in (5, 15, 25):                                        # the three feet
        s.rect(x, 38, 3, 6, BRONZER[2])
        s.hline(x - 1, 43, 5, BRONZER[3])
    s.ellipse(16, 30, 14, 9, BRONZER[3], (BRONZER[5], BRONZER[1]))   # the belly
    for k in range(7):                                           # its grooves, verdigris
        x = 5 + k * 4
        s.vline(x, 26, 9, VERD[2] if k % 2 else VERD[3])
    s.ellipse(16, 23, 14, 3.4, GOLDR[2], (GOLDR[3], GOLDR[1]))   # the gilt rim
    s.ellipse(16, 23, 11.5, 2.2, EMBER[3])
    for k in range(9):
        s.put(6 + k * 2 + (f % 2), 23, EMBER[5] if k % 3 == f % 3 else EMBER[4])
    _flame(s, 16, 22, 18, 20, f, LANTERN)
    _flame(s, 9, 23, 7, 9, f + 2, LANTERN)
    _flame(s, 23, 23, 7, 10, f + 1, LANTERN)
    s.outline()
    _halo(s, 16, 16, 14, STAR[3], 34)


# ============================================================================================================ the decks
def mast(s: Img) -> None:
    """A skiff's mast on its deck, footprint 1 x 1: a tall spar of dark wood stepped in a block, its yard crossing high
    with the sail furled along it, a lantern at the masthead, the stays running down to the deck either side. 48 x 92;
    corner (16, 90)."""
    s.rect(18, 84, 12, 6, WOOD[2])                               # the step block
    s.hline(18, 84, 12, WOOD[4])
    s.hline(18, 89, 12, DARKWOOD[1])
    for x0, x1 in ((2, 22), (46, 26)):                           # the stays
        _line(s, x0, 88, x1, 12, c("6A5A44"))
    s.rect(22, 6, 4, 80, WOOD[3])                                # the mast
    s.vline(22, 6, 80, WOOD[5])
    s.vline(25, 6, 80, WOOD[1])
    for y in (40, 64):
        s.hline(21, y, 6, DARKWOOD[1])
    s.rect(3, 20, 42, 3, DARKWOOD[3])                            # the yard
    s.hline(3, 20, 42, WOOD[4])
    for i in range(4, 45):                                       # the sail furled under it, bunched in its gaskets
        h = 5 + int(h01(i // 3, 1, 971) * 3)
        for j in range(23, 23 + h):
            s.put(i, j, SAIL[3] if j < 25 else SAIL[2] if i < 40 else SAIL[1])
        if i % 7 == 0:
            s.vline(i, 23, h, DARKWOOD[2])
    s.rect(21, 1, 6, 5, BRONZER[2])                              # the masthead lantern
    s.rect(22, 2, 4, 3, STAR[4])
    s.put(22, 2, STAR[5])
    s.outline()


# kind: (draw, w, h, footprint w, h, origin, solid, shadow [dx, dy, rx, ry]) as props.PROPS
PROPS = {
    "warden_lamp": (warden_lamp, 16, 44, 1, 1, [0, 42], True, [10, -2, 6, 3]),
    "lantern_cage": (lantern_cage, 32, 62, 2, 1, [0, 60], True, [20, -2, 15, 3]),
    "warden_statue": (warden_statue, 24, 58, 1, 1, [4, 56], True, [12, -2, 10, 3]),
    "warden_banner": (warden_banner, 16, 62, 1, 1, [0, 60], True, [10, -2, 6, 3]),
    "ballista": (ballista, 32, 30, 2, 1, [0, 28], True, [18, -2, 15, 3]),
    "star_chart_table": (star_chart_table, 32, 28, 2, 1, [0, 26], True, [20, -2, 15, 3]),
    "star_globe": (star_globe, 32, 46, 2, 1, [0, 44], True, [16, -2, 13, 3]),
    "pressure_pillar": (pressure_pillar, 16, 64, 1, 1, [0, 62], True, [10, -2, 7, 3]),
    "orbit_stone": (orbit_stone, 32, 52, 2, 1, [0, 50], True, None),
    "crystal_cluster": (crystal_cluster, 24, 34, 1, 1, [4, 32], True, [12, -2, 9, 3]),
    "gravity_plate": (gravity_plate, 16, 16, 1, 1, [0, 16], False, None),
    "golem_husk": (golem_husk, 32, 28, 2, 1, [0, 26], True, [18, -2, 15, 3]),
    "ash_pyre": (ash_pyre, 32, 48, 2, 1, [0, 46], True, [18, -2, 15, 3]),
    "cinder_tent": (cinder_tent, 64, 58, 4, 2, [0, 56], True, [34, -4, 30, 5]),
    "ashborn_banner": (ashborn_banner, 16, 62, 1, 1, [0, 60], True, [10, -2, 6, 3]),
    "embers": (embers, 32, 16, 2, 1, [0, 16], False, None),
    "ash_drift": (ash_drift, 32, 16, 2, 1, [0, 16], False, None),
    "charred_tree": (charred_tree, 40, 58, 1, 1, [12, 56], True, [14, -2, 12, 4]),
    "nebula_coral": (nebula_coral, 24, 36, 1, 1, [4, 34], True, [12, -2, 9, 3]),
    "coral_tree": (coral_tree, 40, 60, 1, 1, [12, 58], True, [14, -2, 13, 4]),
    "void_shell": (void_shell, 32, 26, 2, 1, [0, 24], True, [16, -2, 14, 3]),
    "wick_pillar": (wick_pillar, 16, 76, 1, 1, [0, 74], True, [10, -2, 7, 3]),
    "flame_basin": (flame_basin, 32, 46, 2, 1, [0, 44], True, [18, -2, 15, 3]),
    "mast": (mast, 48, 92, 1, 1, [16, 90], True, [8, -2, 10, 3]),
}
# The lit pieces' four frames: a flame licks (160 ms, as R7's brazier), a star or a glyph breathes slower, a banner
# stirs on the wind (the sects' banners' 450 ms), the floating stone bobs slowest.
ANIM = {"warden_lamp": (4, 400), "lantern_cage": (4, 320), "warden_banner": (4, 450), "pressure_pillar": (4, 380),
        "orbit_stone": (4, 600), "crystal_cluster": (4, 340), "gravity_plate": (4, 360), "ash_pyre": (4, 160),
        "ashborn_banner": (4, 450), "embers": (4, 300), "nebula_coral": (4, 420), "coral_tree": (4, 520), "wick_pillar": (4, 160),
        "flame_basin": (4, 160)}
