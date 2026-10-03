"""Decision 43, the living world (docs/redesign/art_bible.md §14.13): the furnishings of the huts, the shop and the
sect halls, and the stations villagers work at outdoors, built into the prop sheet with the rest of the kit (props.py
merges PROPS). Each is drawn as a prop (§8): at art resolution in the §14 ramps, lit from the north-west (tops and west
faces lit, east ends and fronts a step down), outlined (§4), with a floor shadow of its own.

  interiors   a bed under a quilt, a clay stove with its wok and fire mouth, a tall cabinet of jars, rice sacks, a low
              tea table, a meditation mat, a stone mortar, a herb-drying rack, bolts of cloth, a big water jar and a
              forge hearth;
  sect halls  a library's shelf of scrolls and bound books, an alchemist's chest of little drawers, a folding screen
              painted with a landscape and a scholar's writing desk (the halls, libraries and retreats of E1's rooms);
  stations    a laundry line whose washing waves (four frames on the wind), a woodpile, a chopping block, a net rack, a
              wash tub, baskets of herbs and a basket of fish.

The kinds and their footprints are PROPS; the layouts place them through tools/data/topdown_life.py (`dress`), so the
rooms' own module keeps its lines. Every value is a coordinate hash or a constant: the build is byte-identical.
"""
from __future__ import annotations

from canvas import Img, h01
from palette import (BAMBOO, BRONZER, CLOUD, DARKWOOD, DIRT, GOLDR, JADE, LANTERN, LEAF, MOSS2, PAPER, PINE, PLASTER2,
                     RED, REED, STONE2, WATER2, WOOD, WOOD2, c)

INDIGO = [c("1B2140"), c("283463"), c("3A4C8A"), c("5B72B2"), c("8FA4D6")]
SACK = [c("5A4630"), c("7E6444"), c("A2855C"), c("C2A67A"), c("DCC59A")]
BRICK = [c("4A2324"), c("6E3430"), c("934A3C"), c("B4644A"), c("CC8660")]
SOOT = c("2A2430")


def _box(s: Img, x: int, y: int, w: int, d: int, h: int, top: list, front: list) -> None:
    """A block `w` wide, `d` deep, `h` tall whose top face's north-west corner is at (x, y): the top lit on its north and
    west rims, the front a step down with its east end shaded (the §14 sun)."""
    for j in range(d):
        for i in range(w):
            col = top[3]
            if j == 0 or i == 0:
                col = top[4]
            elif i == w - 1:
                col = top[2]
            s.put(x + i, y + j, col)
    for j in range(h):
        for i in range(w):
            col = front[2]
            if i == 0:
                col = front[3]
            elif i >= w - 2:
                col = front[1]
            if j == h - 1:
                col = front[1]
            s.put(x + i, y + d + j, col)


# ============================================================================================================ interiors
def bed(s: Img) -> None:
    """A bed of dark wood under an indigo quilt printed with pale flowers, a white pillow at its west end. Footprint
    2 x 1, 8 px high. 32 x 26; corner (0, 24)."""
    _box(s, 0, 0, 32, 16, 8, WOOD, DARKWOOD + [WOOD[3]])
    for j in range(2, 15):                                   # the quilt over the mattress
        for i in range(8, 31):
            col = INDIGO[2]
            if j == 2 or i == 8:
                col = INDIGO[3]
            elif j >= 13 or i >= 29:
                col = INDIGO[1]
            if (i * 3 + j * 5) % 11 == 0 and 3 < j < 12:
                col = INDIGO[4]
            s.put(i, j, col)
    for j in range(15, 19):                                  # its hem over the front
        for i in range(8, 31):
            s.put(i, j, INDIGO[1] if i < 29 else INDIGO[0])
    for j in range(3, 12):                                   # the pillow
        for i in range(2, 8):
            s.put(i, j, PAPER if j < 5 or i < 4 else PLASTER2[3])
    for x in (1, 30):                                        # legs
        s.rect(x, 22, 2, 2, DARKWOOD[1])
    s.outline()


def stove(s: Img) -> None:
    """A village stove of plastered clay: a black wok steaming in the west hole, a lidded pot in the east one, the fire
    mouth glowing in its front under a smudge of soot. Footprint 2 x 1, 14 px high. 32 x 32; corner (0, 30)."""
    _box(s, 0, 0, 32, 16, 14, PLASTER2, BRICK)
    for j in range(16, 18):
        for i in range(32):
            s.put(i, j, PLASTER2[2])
    s.ellipse(9, 7, 6.5, 4.5, SOOT)                           # the wok
    s.ellipse(9, 7, 5, 3.4, DARKWOOD[1], (DARKWOOD[3], DARKWOOD[0]))
    s.ellipse(9, 8, 3, 1.8, c("C8A060"))
    s.ellipse(23, 7, 5.5, 4, SOOT)                            # the lidded pot
    s.ellipse(23, 6.5, 4.5, 3, BRONZER[3], (BRONZER[5], BRONZER[1]))
    s.put(23, 5, BRONZER[5])
    for j in range(22, 29):                                   # the fire mouth
        for i in range(11, 21):
            if (j - 22) * 2 < (i - 10) * (21 - i) // 3 + 4:
                col = LANTERN[2] if j > 25 else LANTERN[1]
                if j > 26 and 13 < i < 18:
                    col = LANTERN[4]
                s.put(i, j, col)
    for i in range(11, 21):
        s.put(i, 21, SOOT)
    s.outline()


def cabinet(s: Img) -> None:
    """A tall cabinet of dark wood against the back wall, three shelves of jars, bottles and bundles behind its open
    front. Footprint 2 x 1 (it stands on the cell's north half). 32 x 48; corner (0, 46)."""
    _box(s, 0, 0, 32, 8, 30, WOOD, DARKWOOD + [WOOD[3]])
    for k, y in enumerate((10, 20, 30)):
        s.rect(2, y, 28, 7, DARKWOOD[0])
        s.hline(2, y + 7, 28, WOOD[4])
        for n in range(5):
            x = 3 + n * 6
            hgt = 3 + int(h01(n, k, 61) * 4)
            kind = int(h01(n, k, 62) * 4)
            col = [(JADE, c("1B6A5E")), (BRONZER[4], BRONZER[2]), (PAPER, PLASTER2[2]), (RED[3], RED[1])][kind]
            for j in range(hgt):
                for i in range(4):
                    if j == 0 and i in (0, 3):
                        continue
                    s.put(x + i, y + 7 - hgt + j, col[0] if i < 2 else col[1])
    s.outline()


def sacks(s: Img) -> None:
    """Two rice sacks of coarse hemp, tied at the neck, one leaning on the other. Footprint 1 x 1. 16 x 26; corner
    (0, 24)."""
    for cx, top, w in ((5, 6, 5.5), (11, 9, 5)):
        for j in range(top, 24):
            half = w if j > top + 3 else w - (top + 3 - j)
            for i in range(int(cx - half), int(cx + half) + 1):
                col = SACK[3]
                if i < cx - half + 2:
                    col = SACK[4]
                elif i > cx + half - 2:
                    col = SACK[2]
                if j > 21:
                    col = SACK[1]
                s.put(i, j, col)
        s.rect(cx - 1, top - 2, 3, 2, SACK[2])
        s.put(cx - 1, top - 3, SACK[3])
        s.put(cx + 1, top - 3, SACK[2])
        s.hline(int(cx - 2), top, 5, DIRT[2])
    s.put(5, 14, RED[3])
    s.put(6, 14, RED[3])
    s.outline()


def tea_table(s: Img) -> None:
    """A low table of red lacquer with a teapot and two cups on it. Footprint 2 x 1, 8 px high. 32 x 26; corner
    (0, 24)."""
    _box(s, 1, 2, 30, 14, 6, RED2_TOP, RED)
    for x in (2, 28):
        s.rect(x, 22, 2, 2, DARKWOOD[1])
    s.ellipse(12, 7, 3.5, 3, JADE, (c("7FD8C6"), c("1B6A5E")))   # the teapot
    s.put(15, 6, c("1B6A5E"))
    s.put(16, 5, c("1B6A5E"))
    s.put(12, 3, c("1B6A5E"))
    for x in (20, 24):
        s.rect(x, 8, 2, 2, PAPER)
        s.put(x + 1, 9, PLASTER2[2])
    s.outline()


RED2_TOP = [RED[0], RED[1], RED[2], RED[3], RED[4]]


def mat(s: Img) -> None:
    """A woven meditation mat with a round cushion on it (walk-through, flat). Footprint 2 x 1. 32 x 16; corner
    (0, 16)."""
    for j in range(2, 15):
        for i in range(2, 30):
            col = REED[3] if (i + j // 2) % 3 else REED[2]
            if j == 2 or i == 2:
                col = REED[4]
            s.put(i, j, col)
    s.ellipse(16, 8, 6, 4, RED[2], (RED[4], RED[1]))
    s.put(16, 8, GOLDR[2])


def mortar(s: Img) -> None:
    """A stone mortar with its pestle standing in it. Footprint 1 x 1. 16 x 18; corner (0, 16)."""
    s.ellipse(8, 12, 6, 4.5, STONE2[3], (STONE2[5], STONE2[1]))
    s.ellipse(8, 9.5, 5, 2.2, STONE2[4])
    s.ellipse(8, 9.5, 3.5, 1.4, STONE2[1])
    for j in range(2, 10):
        s.put(9 + (j < 5), j, WOOD[4] if j < 6 else WOOD[3])
    s.outline()


def drying_rack(s: Img) -> None:
    """A bamboo drying rack: two round woven trays of herbs on a frame, one above the other. Footprint 2 x 1. 32 x 30;
    corner (0, 28)."""
    for x in (2, 29):
        s.vline(x, 4, 24, BAMBOO[3])
        s.vline(x + 1, 4, 24, BAMBOO[2])
    for k, y in enumerate((5, 15)):
        s.ellipse(16, y + 3, 13, 3.6, REED[3], (REED[4], REED[2]))
        for n in range(14):
            i, j = 5 + int(h01(n, k, 71) * 22), y + 1 + int(h01(n, k, 72) * 4)
            s.put(i, j, [LEAF[4], LEAF[3], MOSS2[4], RED[2]][n % 4])
    s.outline()


def cloth_bolts(s: Img) -> None:
    """Bolts of cloth stacked on end: red, indigo and undyed, their rolled tops lit. Footprint 1 x 1. 16 x 24; corner
    (0, 22)."""
    for k, (x, top, col) in enumerate(((1, 6, RED), (6, 3, INDIGO), (11, 8, [SACK[1], SACK[2], SACK[3], SACK[4], PAPER]))):
        for j in range(top, 22):
            for i in range(5):
                cc = col[3] if i < 2 else col[2] if i < 4 else col[1]
                s.put(x + i, j, cc)
        s.hline(x, top, 5, col[4])
        s.put(x + 2, top + 1, col[1])
    s.outline()


def water_jar(s: Img) -> None:
    """A big glazed water jar with a wooden lid and a gourd ladle on it. Footprint 1 x 1. 16 x 22; corner (0, 20)."""
    s.ellipse(8, 13, 7, 7.5, c("5B3A2A"), (c("8A5A3A"), c("3A2418")))
    s.ellipse(6, 10, 2, 3, c("9C6A45"))
    s.ellipse(8, 6, 6, 2.2, WOOD[4], (WOOD[5], WOOD[2]))
    s.ellipse(9, 5, 2, 1.4, c("D8B060"))
    s.put(11, 5, c("B08840"))
    s.put(12, 4, c("B08840"))
    s.outline()


def forge(s: Img) -> None:
    """A sect smithy's forge hearth of brick, its bed of coals glowing, a leather bellows at its east end. Footprint
    2 x 1, 16 px high. 32 x 34; corner (0, 32)."""
    _box(s, 0, 0, 28, 16, 16, BRICK, BRICK)
    for j in range(3, 12):
        for i in range(4, 22):
            col = LANTERN[1] if (i + j) % 3 else LANTERN[2]
            if 6 < i < 18 and 5 < j < 10:
                col = LANTERN[3] if (i * j) % 4 else LANTERN[4]
            s.put(i, j, col)
    for j in range(8, 26):                                    # the bellows
        for i in range(27, 32):
            s.put(i, j, c("6B4A30") if i < 30 else c("4A3220"))
    s.hline(27, 8, 5, WOOD[4])
    s.outline()


# ============================================================================================================ stations
def laundry_line(s: Img, f: int = 0) -> None:
    """A laundry line between two bamboo posts, washing pegged along it that lifts on the wind: a white shirt, an
    indigo cloth and a red sash. Four frames. Footprint 3 x 1 (walk-through). 48 x 34; corner (0, 32)."""
    for x in (1, 45):
        s.vline(x, 2, 30, BAMBOO[3])
        s.vline(x + 1, 2, 30, BAMBOO[2])
        s.put(x, 2, BAMBOO[4])
    sag = [0, 1, 2, 2, 3, 3, 3, 3, 2, 2, 1, 0]
    for i in range(3, 45):
        y = 4 + sag[min(11, (i - 3) * 12 // 42)]
        s.put(i, y, DIRT[4])
    lift = (0, 1, 2, 1)[f]
    for k, (x0, w, hgt, ramp) in enumerate(((6, 9, 12, [PLASTER2[2], PLASTER2[3], PAPER]),
                                            (19, 10, 14, [INDIGO[1], INDIGO[2], INDIGO[3]]),
                                            (33, 7, 16, [RED[1], RED[2], RED[4]]))):
        top = 4 + sag[min(11, (x0 - 3) * 12 // 42)] + 1
        for j in range(hgt):
            sway = (j * lift) // 6 + (1 if (j > hgt - 4 and (f + k) % 2) else 0)
            for i in range(w):
                col = ramp[1]
                if i == 0:
                    col = ramp[2]
                elif i == w - 1:
                    col = ramp[0]
                if k == 0 and j < 3 and (i < 2 or i > w - 3):
                    col = ramp[2] if i < 2 else ramp[0]   # the shirt's sleeves
                if j == hgt - 1 and (i + f) % 2:
                    continue
                s.put(x0 + i + sway, top + j, col)
    s.outline()


def woodpile(s: Img) -> None:
    """A stack of split firewood, the end grain of the logs in rings on its front, lit on top. Footprint 2 x 1. 32 x 24;
    corner (0, 22)."""
    for row in range(3):
        for n in range(5 - (row == 2)):
            cx = 4 + n * 6 + (3 if row % 2 else 0)
            cy = 18 - row * 5
            s.ellipse(cx, cy, 3.2, 2.8, WOOD[3], (WOOD[5], WOOD[1]))
            s.put(cx, cy, WOOD[2])
            s.put(cx - 1, cy - 1, WOOD2[6])
    for i in range(1, 30):
        s.put(i, 4, WOOD[4] if i % 4 else WOOD[5])
    s.outline()


def chop_block(s: Img) -> None:
    """A chopping block, a squat round of trunk with its rings on top and a cleft in it, a split half-log lying against it
    and chips round its foot. Footprint 1 x 1. 16 x 16; corner (0, 14)."""
    s.ellipse(8, 12, 7, 3, WOOD[1])
    s.rect(2, 7, 12, 5, WOOD[3])
    s.vline(2, 7, 5, WOOD[4])
    s.vline(3, 7, 5, WOOD[4])
    s.vline(12, 7, 5, WOOD[2])
    s.vline(13, 7, 5, WOOD[2])
    for x in (5, 9):
        s.vline(x, 8, 4, WOOD[2])
    s.ellipse(8, 7, 6, 2.6, WOOD2[5], (WOOD2[6], WOOD2[4]))
    s.ellipse(8, 7, 3.5, 1.4, WOOD2[4])
    s.put(8, 7, WOOD2[3])
    s.hline(6, 6, 4, WOOD[2])                                  # the cleft
    s.rect(10, 11, 5, 2, WOOD2[5])                             # a split half-log against it
    s.hline(10, 11, 5, WOOD2[6])
    s.outline()
    for x, y in ((0, 14), (15, 13), (3, 15), (13, 15)):
        s.put(x, y, WOOD2[5])


def net_rack(s: Img) -> None:
    """A fishing net drying over a bamboo rack, red floats knotted in it. Footprint 2 x 1. 32 x 30; corner (0, 28)."""
    for x in (2, 28):
        for j in range(4, 28):
            s.put(x + (j - 4) // 12, j, BAMBOO[3])
    for i in range(2, 31):
        s.put(i, 4, BAMBOO[4])
    for i in range(3, 30):
        for j in range(5, 24):
            if (i + j) % 3 == 0 or (i - j) % 3 == 0:
                if j < 5 + 18 - abs(i - 16) // 3:
                    s.put(i, j, REED[3] if j < 14 else REED[2])
    for x, y in ((8, 12), (16, 16), (24, 11)):
        s.put(x, y, RED[3])
        s.put(x + 1, y, RED[4])
    s.outline()


def wash_tub(s: Img) -> None:
    """A wooden wash tub of water with cloth soaking in it and a washboard leaning in. Footprint 1 x 1. 16 x 16; corner
    (0, 14)."""
    s.ellipse(8, 10, 7, 4.5, WOOD[3], (WOOD[4], WOOD[1]))
    s.ellipse(8, 8.5, 6, 3, WATER2[4])
    s.ellipse(7, 8, 3, 1.4, WATER2[6])
    s.rect(9, 7, 4, 2, INDIGO[2])
    s.put(5, 9, PAPER)
    s.put(6, 9, PAPER)
    for j in range(2, 9):
        s.put(3, j, WOOD[5])
        s.put(4, j, WOOD[4] if j % 2 else WOOD[3])
    s.outline()


def herb_baskets(s: Img) -> None:
    """Two shallow baskets of picked herbs, one of greens and one of red roots. Footprint 1 x 1. 16 x 14; corner
    (0, 12)."""
    for cx, cy, load in ((5, 7, (LEAF[5], LEAF[3])), (11, 9, (RED[3], RED[1]))):
        s.ellipse(cx, cy + 1, 4.5, 2.5, REED[3], (REED[4], REED[2]))
        for n in range(6):
            s.put(cx - 2 + n % 4, cy - 1 + n // 4, load[n % 2])
    s.outline()


def fish_basket(s: Img) -> None:
    """A round basket of the morning's catch, silver fish heaped in it. Footprint 1 x 1. 16 x 14; corner (0, 12)."""
    s.ellipse(8, 8, 6.5, 4, REED[3], (REED[4], REED[2]))
    for n in range(7):
        x, y = 4 + (n * 3) % 8, 5 + n // 3
        s.put(x, y, STONE2[5])
        s.put(x + 1, y, STONE2[3])
    s.outline()


# ===================================================================================== the sect halls (R3, E1's rooms)
def scroll_shelf(s: Img) -> None:
    """A library's tall shelf of dark wood against the back wall: four rows of pigeonholes, rolled scrolls stacked in
    them (their paper ends, tied with coloured cords) and thread-bound books lying flat in indigo covers, a carved crest
    on its top. Footprint 2 x 1 (it stands on the cell's north half). 32 x 48; corner (0, 46)."""
    _box(s, 0, 2, 32, 6, 32, WOOD, DARKWOOD + [WOOD[3]])
    s.hline(3, 0, 26, DARKWOOD[2])                            # the crest along its top
    s.hline(2, 1, 28, DARKWOOD[3])
    for x in (3, 28):
        s.put(x, 0, GOLDR[1])
    ties = [RED[3], JADE, GOLDR[2], c("5B72B2")]
    for row, y in enumerate((9, 17, 25, 33)):
        for col, x in enumerate((2, 10, 17, 24)):
            s.rect(x, y, 6, 7, DARKWOOD[0])                    # the pigeonhole's dark back
            if h01(row, col, 81) < 0.3:                        # books lying flat, spines out
                for k in range(3):
                    yy = y + 6 - k * 2
                    s.hline(x, yy, 6, INDIGO[2] if k % 2 == 0 else INDIGO[1])
                    s.put(x + 5, yy, PAPER)
                continue
            for k, (dx, dy) in enumerate(((0, 4), (3, 4), (1, 2), (4, 2), (2, 0))):
                if k == 4 and h01(row, col, 82) < 0.5:
                    continue
                s.rect(x + dx, y + 1 + dy, 2, 2, PAPER if (k + row) % 3 else PLASTER2[3])
                s.put(x + dx + 1, y + 2 + dy, PLASTER2[2])
                s.put(x + dx, y + 1 + dy, ties[int(h01(row * 5 + k, col, 83) * 4) % 4])
        s.hline(2, y + 7, 28, WOOD[4])                         # the shelf's lit edge
    s.outline()


def apothecary(s: Img) -> None:
    """An alchemist's chest of little drawers, five by five, each with a brass ring and a paper label; a row of jars
    and a bronze censer on its top. Footprint 2 x 1 (on the cell's north half). 32 x 46; corner (0, 44)."""
    _box(s, 0, 8, 32, 6, 30, WOOD2, DARKWOOD + [WOOD2[3]])
    for r in range(5):
        for k in range(5):
            x, y = 2 + k * 6, 15 + r * 6
            s.rect(x, y, 5, 5, WOOD2[3] if (r + k) % 2 else WOOD2[4])
            s.hline(x, y, 5, WOOD2[5])
            s.put(x + 1, y + 1, PAPER)                         # the label
            s.put(x + 2, y + 1, PLASTER2[3])
            s.put(x + 2, y + 3, GOLDR[2])                      # the ring
    for i, (x, kind) in enumerate(((4, 0), (10, 1), (21, 0), (26, 1))):   # jars on its top
        col = (c("5B3A2A"), c("8A5A3A")) if kind == 0 else (JADE, c("7FD8C6"))
        s.ellipse(x, 8 - (i % 2), 2.5, 3, col[0], (col[1], c("2A1A12")))
        s.put(x, 4 - (i % 2), WOOD[4])
    s.ellipse(16, 7, 3, 2.5, BRONZER[3], (BRONZER[5], BRONZER[1]))   # the censer
    s.hline(15, 3, 3, BRONZER[4])
    s.outline()


def screen(s: Img) -> None:
    """A folding screen of four paper panels in a black lacquer frame, standing in a shallow zigzag, an ink landscape
    across them (far peaks in grey wash, a pine, a red seal). Footprint 2 x 1. 32 x 40; corner (0, 38)."""
    frame = (c("1C1418"), c("3A2A30"))
    for k in range(4):
        x0 = k * 8
        lit = k % 2 == 0
        s.rect(x0, 2, 8, 34, frame[1] if lit else frame[0])
        for j in range(4, 34):
            for i in range(x0 + 1, x0 + 7):
                s.put(i, j, PAPER if lit else PLASTER2[3])
        s.hline(x0, 2, 8, GOLDR[1] if lit else GOLDR[0])
        for x in (x0 + 1, x0 + 6):                             # its little feet
            s.put(x, 36, frame[0])
            s.put(x, 37, frame[0])
    for i in range(1, 31):                                     # the far peaks' wash, across the panels
        if i % 8 in (0, 7):
            continue
        top = 20 - int(6 * abs(((i * 0.23) % 2.0) - 1.0)) - (3 if 10 < i < 18 else 0)
        for j in range(top, 26):
            s.put(i, j, PLASTER2[1] if j < top + 2 else PLASTER2[2])
    for j in range(14, 30):                                    # a pine on the third panel
        s.put(19, j, DARKWOOD[1])
    for j, w in ((13, 3), (16, 5), (19, 4), (22, 5)):
        s.hline(19 - w // 2, j, w, PINE[2])
        s.hline(19 - w // 2, j + 1, w, PINE[1])
    s.rect(5, 8, 2, 2, RED[3])                                 # the seal
    s.outline()


def desk(s: Img) -> None:
    """A scholar's low writing desk of dark wood: a sheet of paper half written, the inkstone, a brush on its rest and
    a scroll rolled at the end. Footprint 2 x 1, 8 px high. 32 x 26; corner (0, 24)."""
    _box(s, 1, 2, 30, 14, 6, WOOD2, DARKWOOD + [WOOD2[3]])
    for x in (2, 28):
        s.rect(x, 22, 2, 2, DARKWOOD[1])
    s.rect(6, 4, 11, 9, PAPER)                                 # the sheet
    for j in (6, 8, 10):
        for i in range(8, 15):
            if h01(i, j, 91) < 0.6:
                s.put(i, j, c("2A2A30"))
    s.rect(19, 5, 5, 6, c("1C1C22"))                           # the inkstone
    s.rect(20, 6, 3, 2, c("3A3A48"))
    for k in range(6):                                         # the brush on its rest
        s.put(19 + k, 12 - k // 3, BAMBOO[3] if k < 5 else c("1C1C22"))
    s.rect(26, 4, 3, 9, PLASTER2[3])                           # a scroll rolled up
    s.vline(26, 4, 9, PAPER)
    s.put(27, 8, RED[3])
    s.outline()


# kind: (draw, w, h, footprint w, h, origin, solid, shadow [dx, dy, rx, ry]) as props.PROPS
PROPS = {
    "bed": (bed, 32, 26, 2, 1, [0, 24], True, [20, -2, 15, 3]),
    "stove": (stove, 32, 32, 2, 1, [0, 30], True, [20, -2, 15, 3]),
    "cabinet": (cabinet, 32, 48, 2, 1, [0, 46], True, [22, -8, 14, 3]),
    "sacks": (sacks, 16, 26, 1, 1, [0, 24], True, [10, -2, 7, 3]),
    "tea_table": (tea_table, 32, 26, 2, 1, [0, 24], True, [20, -2, 15, 3]),
    "mat": (mat, 32, 16, 2, 1, [0, 16], False, None),
    "mortar": (mortar, 16, 18, 1, 1, [0, 16], True, [10, -2, 6, 3]),
    "drying_rack": (drying_rack, 32, 30, 2, 1, [0, 28], True, [20, -2, 15, 3]),
    "cloth_bolts": (cloth_bolts, 16, 24, 1, 1, [0, 22], True, [10, -2, 7, 3]),
    "water_jar": (water_jar, 16, 22, 1, 1, [0, 20], True, [10, -2, 7, 3]),
    "forge": (forge, 32, 34, 2, 1, [0, 32], True, [20, -2, 15, 3]),
    "laundry_line": (laundry_line, 48, 34, 3, 1, [0, 32], False, [26, -2, 22, 2]),
    "woodpile": (woodpile, 32, 24, 2, 1, [0, 22], True, [20, -2, 15, 3]),
    "chop_block": (chop_block, 16, 16, 1, 1, [0, 14], True, [10, -2, 7, 3]),
    "net_rack": (net_rack, 32, 30, 2, 1, [0, 28], True, [20, -2, 15, 3]),
    "wash_tub": (wash_tub, 16, 16, 1, 1, [0, 14], True, [10, -2, 7, 3]),
    "herb_baskets": (herb_baskets, 16, 14, 1, 1, [0, 12], True, [10, -2, 7, 2]),
    "fish_basket": (fish_basket, 16, 14, 1, 1, [0, 12], True, [10, -2, 7, 2]),
    # R3: the sect halls' libraries, alchemy hall and retreats (E1's rooms)
    "scroll_shelf": (scroll_shelf, 32, 48, 2, 1, [0, 46], True, [22, -8, 14, 3]),
    "apothecary": (apothecary, 32, 46, 2, 1, [0, 44], True, [22, -8, 14, 3]),
    "screen": (screen, 32, 40, 2, 1, [0, 38], True, [17, -2, 15, 3]),
    "desk": (desk, 32, 26, 2, 1, [0, 24], True, [20, -2, 15, 3]),
}
# The washing lifts on the wind (the room view turns its frames faster in a gust, TopdownLife.WINDY).
ANIM = {"laundry_line": (4, 420)}


# ================================================================================================================== R5
# The story's rooms and the Tidebreak Front (E1's batch R5): the Nine Peaks' trial seats round the Presence Trial's
# circle, the bronze mirror of the Trial of Reflections, and the Hollow's drone hives on the grey fields past the
# Tidebreak Bastion. Each drawn as the kit's props are: the §14 ramps, lit from the north-west, outlined, a floor shadow.
from palette import HOLLOW  # noqa: E402

VIOLET = [c("221A3C"), c("3D3166"), c("5E4E96"), c("8A7AC4"), c("C2B6EC")]   # the Nine Peaks' lilac, the hive's glow
GLOW = c("F0E6FF")


def trial_seat(s: Img) -> None:
    """A seat of the Nine Peaks: a granite throne on a stepped dais, its tall back crowned in three points with a jade
    stone in the middle one, nine peaks carved in its panel, a lilac cushion on the seat, the arms squared off. Footprint
    2 x 1. 32 x 52; corner (0, 50)."""
    _box(s, 0, 40, 32, 4, 6, STONE2, STONE2)                       # the dais
    for i in range(6, 26):                                          # the back's crown: three points
        d = min(abs(i - 15.5), abs(i - 7.5) + 3, abs(i - 23.5) + 3)
        top = 2 + int(d * 0.9)
        for j in range(top, 31):
            col = STONE2[3]
            if i == 6 or j == top:
                col = STONE2[4]
            elif i >= 24:
                col = STONE2[2]
            s.put(i, j, col)
    s.rect(9, 11, 14, 17, STONE2[2])                                # the carved panel: peaks over a cloud
    s.hline(9, 11, 14, STONE2[1])
    for i in range(10, 22):
        top = 13 + int(min(abs(i - 15.5) * 1.6, abs(i - 11.5) * 1.6 + 4, abs(i - 19.5) * 1.6 + 3))
        for j in range(top, 24):
            s.put(i, j, STONE2[4] if i < 15 or j == top else STONE2[3])
    for i in range(10, 22):
        s.put(i, 24 + (i % 3 == 0), STONE2[5])                      # the cloud under them
        s.put(i, 25, STONE2[4])
    s.rect(15, 5, 2, 3, JADE)                                       # the jade stone
    s.put(15, 5, c("7FD8C6"))
    for x0 in (2, 26):                                              # the arms
        _box(s, x0, 24, 4, 3, 10, STONE2, STONE2)
    _box(s, 5, 31, 22, 6, 4, STONE2, STONE2)                        # the seat
    for j in range(32, 36):                                         # its cushion
        for i in range(7, 25):
            s.put(i, j, VIOLET[3] if j == 32 or i == 7 else VIOLET[1] if i >= 23 else VIOLET[2])
    s.hline(7, 36, 18, VIOLET[0])
    s.outline()


def bronze_mirror(s: Img) -> None:
    """The bronze mirror of the Trial of Reflections, as the side view has it: a great round mirror held in a curved frame
    of dark wood on a pedestal, gold finials on its crown and sides, its face pale silver-gold with two glints across it
    and a jade mist rising in its lower part. Footprint 2 x 1. 32 x 56; corner (0, 54)."""
    _box(s, 4, 46, 24, 3, 5, WOOD2, DARKWOOD + [WOOD2[3]])           # the pedestal
    s.rect(13, 38, 6, 8, DARKWOOD[2])                               # its stem
    s.vline(13, 38, 8, DARKWOOD[3])
    s.ellipse(16, 23, 14.5, 15.5, WOOD2[2], (WOOD2[4], DARKWOOD[1]))   # the frame
    s.ellipse(16, 23, 12, 13, BRONZER[2])
    for j in range(10, 37):                                         # the face
        for i in range(4, 29):
            dx, dy = (i + 0.5 - 16) / 11.0, (j + 0.5 - 23) / 12.0
            if dx * dx + dy * dy > 1.0:
                continue
            col = PAPER if dx + dy < -0.7 else GOLDR[3] if dx + dy < -0.1 else PLASTER2[3] if dx + dy < 0.6 else PLASTER2[2]
            if dy > 0.35:                                           # the jade mist in it
                col = c("9CCFB9") if dy < 0.6 else c("5FAE98") if dy < 0.85 else JADE
            if abs(dx - dy + 0.35) < 0.09 or abs(dx - dy - 0.15) < 0.05:   # two glints
                col = c("FFFDF4")
            s.put(i, j, col)
    for x, y in ((16, 6), (1, 23), (31, 23)):                       # the finials
        s.ellipse(x, y, 1.6, 1.6, GOLDR[2], (GOLDR[3], GOLDR[1]))
    s.put(16, 4, GOLDR[3])
    s.outline()


def drone_hive(s: Img) -> None:
    """A drone hive of the Hollow: a tall cone of grey papery stone laid in scalloped courses, cells glowing violet in
    it where the drones sleep, a skirt of broken stone round its foot. Footprint 2 x 1. 32 x 54; corner (0, 52)."""
    for j in range(2, 50):
        half = 2 + (j - 2) * 13.5 / 47.0
        course = (j - 2) % 6
        for i in range(int(16 - half), int(16 + half) + 1):
            u = (i + 0.5 - (16 - half)) / (2 * half + 1)
            col = HOLLOW[3] if u < 0.3 else HOLLOW[2] if u < 0.72 else HOLLOW[1]
            if course == 5:                                         # each course's shadowed lower edge, scalloped
                col = HOLLOW[1] if (i + j // 6) % 4 else HOLLOW[0]
            elif course == 0 and u < 0.5:
                col = HOLLOW[4]
            s.put(i, j, col)
    for k, (x, y) in enumerate(((15, 9), (12, 20), (19, 16), (17, 27), (10, 33), (21, 36), (14, 42), (24, 44), (7, 45))):
        for j in range(-2, 4):                                      # the glow round each cell on the stone
            for i in range(-2, 5):
                if (i - 1) ** 2 + (j - 0.5) ** 2 <= 7:
                    s.blend(x + i, y + j, VIOLET[3], 90)
        s.rect(x, y, 3, 2, VIOLET[1])                               # the cells, lit from within
        s.put(x + 1, y, GLOW if k % 3 == 0 else VIOLET[4])
        s.put(x, y + 1, VIOLET[3])
        s.put(x + 1, y + 1, VIOLET[4])
        s.put(x + 2, y + 1, VIOLET[3])
    for k in range(7):                                              # the broken stone at its foot
        x = 1 + k * 4 + int(h01(k, 1, 97) * 2)
        s.ellipse(x + 1.5, 50, 2.5, 1.8, HOLLOW[2], (HOLLOW[4], HOLLOW[0]))
    s.outline()


PROPS.update({
    "trial_seat": (trial_seat, 32, 52, 2, 1, [0, 50], True, [20, -2, 15, 3]),
    "bronze_mirror": (bronze_mirror, 32, 58, 2, 1, [0, 56], True, [17, -2, 15, 3]),
    "drone_hive": (drone_hive, 32, 54, 2, 1, [0, 52], True, [18, -2, 15, 4]),
})


# ================================================================================================================== R8
# The sky-sea zones of the late game (E1's batch R8): the Skyport Wreck's broken hulls, masts, anchor, ballista and
# armillary; Lanternfall Harbor's star lanterns, market stalls and quay crane; the Drifting Shoals' driftglass and star
# crystals; Blackmast Haven's black masts, cannons, powder kegs and black banners; the Wyrmnest Isles' rock spires,
# nests, skulls, ribs, bones and eggshells. Each drawn as the kit's props are: the §14 ramps, lit from the north-west,
# outlined, a floor shadow; a coordinate hash for every speck, so the build stays byte-identical.
import math  # noqa: E402

from palette import RED2, ROCK, SAND2, STONE2, TIMBER2, WOOD, WOOD2  # noqa: E402

IRON = [c("14141B"), c("23232D"), c("363643"), c("51515E"), c("777784")]          # black cast iron, cold lit edge
RUST = [c("4A2418"), c("7A3C20"), c("A85A2C")]
SAILBLACK = [c("110E15"), c("1E1823"), c("2E2534"), c("43384A"), c("5C5064")]     # the Blackmast sails, tarred silk
CANVAS = [c("5E5A54"), c("8A857A"), c("B6AF9F"), c("D8D1BE"), c("EEE8D6")]        # a sky ship's sailcloth, weathered
BONE = [c("5E5242"), c("8C7C62"), c("B9A786"), c("DCCDAA"), c("F3EAD2")]          # old bone, sun-bleached on top
GLASS = [c("26305C"), c("3A5894"), c("5F9DCC"), c("A3D9EA"), c("E6FAFF")]         # driftglass: deep blue to a glint
CRYSTAL = [c("2A2256"), c("473B8E"), c("7766CC"), c("B0A3EE"), c("EAE4FF")]       # a star crystal, violet to white
STARLIGHT = c("F4F8FF")
CLEAR_PX = (0, 0, 0, 0)


def _line(s: Img, x0: int, y0: int, x1: int, y1: int, col) -> None:
    """A 1 px line between two points (no anti-aliasing)."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for k in range(n + 1):
        s.put(x0 + round((x1 - x0) * k / n), y0 + round((y1 - y0) * k / n), col)


def _star(s: Img, x: int, y: int, col, glow=None) -> None:
    """A four-pointed star a pixel across its heart, its points a pixel long (a lit lamp's or a crystal's sparkle)."""
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        s.put(x + dx, y + dy, col)
    if glow is not None:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            s.put(x + dx, y + dy, glow)


# ------------------------------------------------------------------------------------------------- the Skyport Wreck
def hull_ribs(s: Img) -> None:
    """A sky ship's hull broken on the rock: its keel half sunk in the ground, the west half still planked in dark strakes
    up to a gunwale, the planks torn off the east half so its curved ribs stand bare, a jagged break between. Footprint
    3 x 1. 48 x 40; corner (0, 38)."""
    for x in range(1, 47):                                          # the keel along the ground
        s.put(x, 37, DARKWOOD[1])
        s.put(x, 36, DARKWOOD[2] if x % 6 else DARKWOOD[1])
        s.put(x, 35, DARKWOOD[3])
    for x in range(2, 25):                                          # the planked half: strakes over a curved belly
        top = 8 + int(abs(x - 13) * 0.35)
        broke = 25 - x <= 4 and h01(x, 1, 811) < 0.6
        for y in range(top + (6 if broke else 0), 35):
            k = (y - top) % 5
            col = TIMBER2[3] if k == 0 else TIMBER2[2] if k < 4 else TIMBER2[1]
            if x <= 3:
                col = TIMBER2[4] if k == 0 else TIMBER2[3]
            elif x >= 22:
                col = TIMBER2[1] if k else TIMBER2[2]
            s.put(x, y, col)
        if not broke:
            s.put(x, top, WOOD2[5])                                 # the gunwale's lit rail
            s.put(x, top + 1, WOOD2[3])
    for k, x in enumerate((27, 32, 37, 42, 46)):                    # the bare ribs, each a curved timber
        top = 6 + int(h01(k, 2, 812) * 10) + k
        for y in range(top, 35):
            bend = int(((35 - y) / 29.0) ** 2 * 4)
            s.put(x - bend, y, WOOD2[4] if y < top + 2 else WOOD2[3])
            s.put(x - bend + 1, y, WOOD2[2])
    for k in range(5):                                              # splinters at the break
        y = 12 + k * 5
        s.put(25 + k % 2, y, WOOD2[5])
        s.put(26, y + 1, WOOD2[4])
    for x in range(26, 47):                                         # the lower strakes still on the ribs
        if h01(x, 3, 813) < 0.75:
            s.put(x, 33, TIMBER2[2])
            s.put(x, 34, TIMBER2[1])
    s.outline()


def broken_mast(s: Img) -> None:
    """A sky ship's mast snapped off half its height, its yard fallen across it, a torn sail of weathered canvas hanging
    from the yard, a loose line trailing to the ground. Footprint 1 x 1. 24 x 64; corner (4, 62)."""
    s.ellipse(10, 60, 8, 2.5, DARKWOOD[1])
    for x in range(3, 21):                                          # the torn sail hanging from the yard, behind the mast
        top = 23 + (x - 1) * 12 // 21
        drop = 10 + int(h01(x, 1, 821) * 12) - abs(x - 11) // 2
        for y in range(top + 1, top + drop):
            k = (y - top) / float(drop)
            col = CANVAS[3] if k < 0.3 else CANVAS[2] if k < 0.7 else CANVAS[1]
            if x in (3, 4):
                col = CANVAS[4]
            s.put(x, y, col)
    for y in range(18, 61):                                         # the mast, its top torn in splinters
        s.rect(8, y, 5, 1, WOOD2[3])
        s.put(8, y, WOOD2[5])
        s.put(9, y, WOOD2[4])
        s.put(12, y, WOOD2[1])
    for i, dy in enumerate((0, -3, -1, -5, 0)):
        s.vline(8 + i, 18 + dy, -dy + 1, WOOD2[4] if i < 2 else WOOD2[2])
    for y in (30, 44):                                              # iron bands
        s.hline(8, y, 5, IRON[2])
        s.put(8, y, IRON[4])
    _line(s, 1, 22, 22, 34, DARKWOOD[3])                            # the yard fallen across it
    _line(s, 1, 23, 22, 35, DARKWOOD[1])
    for y in range(36, 61):                                         # a loose line to the ground
        s.put(19 + (y // 6) % 2, y, CANVAS[1])
    s.outline()


def starsea_anchor(s: Img) -> None:
    """The great iron anchor of a Starsea ship lying on its side: the ring at the west, the shank, the stock across it,
    the two flukes curling up at the east, rust in its joints, a length of chain. Footprint 2 x 1. 32 x 24; corner
    (0, 22)."""
    s.ellipse(4, 13, 3.5, 3.5, IRON[3])                              # the ring
    s.ellipse(4, 13, 1.6, 1.6, CLEAR_PX)
    s.rect(7, 12, 18, 3, IRON[2])                                   # the shank
    s.hline(7, 12, 18, IRON[4])
    s.hline(7, 14, 18, IRON[1])
    s.rect(9, 6, 3, 13, IRON[2])                                    # the stock
    s.vline(9, 6, 13, IRON[4])
    for k in range(9):                                              # the flukes
        s.put(24 + k // 2, 12 - k, IRON[3])
        s.put(25 + k // 2, 12 - k, IRON[1])
        s.put(24 + k // 2, 15 + k // 2, IRON[2])
        s.put(25 + k // 2, 15 + k // 2, IRON[1])
    for x, y in ((28, 3), (29, 3), (28, 4), (28, 19), (29, 19)):
        s.put(x, y, IRON[4])
    for x, y in ((12, 14), (23, 13), (10, 17), (24, 11)):
        s.put(x, y, RUST[1])
    for k in range(5):                                              # the chain
        s.ellipse(1.5 + k * 2.2, 19 + (k % 2), 1.2, 1.0, IRON[3] if k % 2 else IRON[2])
    s.outline()


def star_ballista(s: Img) -> None:
    """A star ballista on a timber trestle, aimed east: the stock, its great bow of laminated horn bent across the front,
    the string drawn back, and a bolt with a star-steel head that holds a cold light. Footprint 2 x 1. 32 x 34; corner
    (0, 32)."""
    for x0 in (8, 18):                                              # the trestle's legs
        _line(s, x0, 18, x0 - 4, 31, DARKWOOD[3])
        _line(s, x0 + 1, 18, x0 + 5, 31, DARKWOOD[2])
    s.rect(4, 30, 22, 2, DARKWOOD[1])
    s.rect(4, 13, 20, 5, WOOD2[3])                                  # the stock
    s.hline(4, 13, 20, WOOD2[5])
    s.hline(4, 17, 20, WOOD2[1])
    _line(s, 23, 2, 12, 14, PAPER)                                  # the string, drawn back
    _line(s, 12, 15, 23, 29, PLASTER2[2])
    for y in range(2, 30):                                          # the bow across its front
        x = 22 + int(abs(y - 15.5) ** 2 / 34.0)
        s.put(x, y, BRONZER[4] if y < 15 else BRONZER[3])
        s.put(x + 1, y, BRONZER[2])
    s.rect(9, 12, 19, 1, WOOD2[5])                                  # the bolt
    for k in range(4):
        s.put(27 + k, 12, STONE2[5] if k < 3 else STARLIGHT)
        s.put(27 + k // 2, 11, STONE2[4])
        s.put(27 + k // 2, 13, STONE2[3])
    _star(s, 30, 12, STARLIGHT)
    s.outline()


def armillary(s: Img) -> None:
    """A navigator's armillary sphere: bronze rings of the sky round a little star, on a turned post over a granite
    plinth. Footprint 1 x 1. 24 x 40; corner (4, 38)."""
    s.rect(5, 33, 14, 5, STONE2[3])
    s.hline(5, 33, 14, STONE2[5])
    s.hline(5, 37, 14, STONE2[1])
    s.rect(10, 22, 4, 11, BRONZER[3])
    s.vline(10, 22, 11, BRONZER[5])
    s.vline(13, 22, 11, BRONZER[1])
    for rx, ry, col in ((9.5, 9.5, BRONZER[4]), (9.5, 3.5, BRONZER[3]), (3.5, 9.5, BRONZER[2])):
        for k in range(120):                                        # each ring an ellipse's rim, its far half dark
            a = k * math.pi * 2 / 120
            x, y = 12 + rx * math.cos(a), 12 + ry * math.sin(a)
            s.put(int(round(x)), int(round(y)), col if math.sin(a) > -0.3 else BRONZER[1])
    _line(s, 4, 17, 20, 7, GOLDR[2])                                # the ecliptic band
    _star(s, 12, 12, GOLDR[3], GOLDR[1])
    s.outline()


# ---------------------------------------------------------------------------------------------- Lanternfall Harbor
def star_lantern(s: Img) -> None:
    """A star lantern of Lanternfall on its post: an indigo-lacquered post with a gilt crook, the six-sided lamp of glass
    hung from it, a starlight burning pale blue-white inside. Footprint 1 x 1. 16 x 48; corner (0, 46)."""
    s.rect(2, 43, 9, 3, STONE2[3])
    s.hline(2, 43, 9, STONE2[5])
    s.rect(5, 6, 3, 37, INDIGO[1])
    s.vline(5, 6, 37, INDIGO[3])
    s.vline(7, 6, 37, INDIGO[0])
    s.rect(4, 4, 5, 2, GOLDR[2])
    s.hline(8, 6, 4, GOLDR[2])                                       # the crook
    s.put(11, 7, GOLDR[1])
    s.put(11, 8, GOLDR[2])
    for j in range(10, 22):                                          # the lamp's glass, its glow
        half = 2 if j in (10, 21) else 3
        for i in range(11 - half, 11 + half + 1):
            col = GLASS[3] if abs(i - 11) < 2 and 12 < j < 20 else GLASS[2]
            if abs(i - 11) == half:
                col = GOLDR[1]
            s.put(i, j, col)
    s.hline(8, 9, 7, GOLDR[2])
    s.hline(8, 22, 7, GOLDR[1])
    s.put(11, 23, GOLDR[2])
    _star(s, 11, 15, STARLIGHT, GLASS[4])
    s.outline()


def market_stall(s: Img) -> None:
    """A Lanternfall market stall: a counter of boards under an awning striped in red and cream on two posts, paper
    lanterns hung from its rail, the wares on the counter: jars, bolts of silk, a tray of little star lamps. Footprint
    3 x 1. 48 x 40; corner (0, 38)."""
    for x in (3, 43):                                                # the posts
        s.rect(x, 6, 2, 26, DARKWOOD[3])
        s.vline(x, 6, 26, WOOD2[4])
    _box(s, 2, 24, 44, 6, 8, WOOD2, DARKWOOD + [WOOD2[3]])          # the counter
    for i in range(0, 48):                                           # the awning, scalloped
        stripe = (i // 6) % 2
        for j in range(2, 10):
            col = (RED2[3] if stripe else PLASTER2[4]) if j < 8 else (RED2[2] if stripe else PLASTER2[2])
            if j == 2:
                col = RED2[4] if stripe else PLASTER2[5]
            s.put(i, j, col)
        if i % 6 in (2, 3):
            s.put(i, 10, RED2[2] if stripe else PLASTER2[2])
    for k, x in enumerate((10, 23, 36)):                             # paper lanterns under the awning (a star lamp in the middle)
        lit = (GLASS[3], GLASS[4], GLASS[1]) if k == 1 else (LANTERN[3], LANTERN[4], LANTERN[1])
        s.put(x, 11, DARKWOOD[1])
        s.ellipse(x, 14.5, 2.6, 3, lit[0], (lit[1], lit[2]))
    for k in range(6):                                               # the wares
        x = 6 + k * 6
        kind = k % 3
        if kind == 0:
            s.rect(x, 20, 3, 5, JADE)
            s.put(x, 20, c("7FD8C6"))
        elif kind == 1:
            s.rect(x, 22, 5, 3, INDIGO[3] if k == 1 else RED2[3])
            s.hline(x, 22, 5, INDIGO[4] if k == 1 else RED2[5])
        else:
            for i in range(3):
                s.put(x + i * 2, 23, GLASS[3])
                s.put(x + i * 2, 24, GOLDR[1])
    s.outline()


def harbor_crane(s: Img) -> None:
    """A quay crane of timber: a braced post, its jib reaching out east over the water, a rope from its tip to a hook
    with a cargo net of crates. Footprint 2 x 1. 48 x 72; corner (4, 70)."""
    s.rect(4, 64, 26, 6, DARKWOOD[2])                                # the footing
    s.hline(4, 64, 26, WOOD2[4])
    _line(s, 5, 64, 10, 44, WOOD2[2])                                # braces
    _line(s, 26, 64, 13, 44, WOOD2[2])
    s.rect(9, 10, 5, 54, WOOD2[3])                                   # the post
    s.vline(9, 10, 54, WOOD2[5])
    s.vline(13, 10, 54, WOOD2[1])
    for k in range(3):                                               # the jib
        _line(s, 11, 14 + k, 45, 4 + k, WOOD2[4 - k])
    _line(s, 11, 30, 40, 7, DARKWOOD[3])                             # its stay
    s.rect(7, 22, 9, 6, DARKWOOD[2])                                 # the winch drum
    s.ellipse(11.5, 25, 3, 3, IRON[3], (IRON[4], IRON[1]))
    for y in range(8, 42):                                           # the rope down to the load
        s.put(44, y, CANVAS[2])
    s.put(43, 42, IRON[4])
    s.put(45, 42, IRON[3])
    for j in range(43, 54):                                          # the net of crates
        for i in range(37, 48):
            col = WOOD[4] if (i - 37) % 6 < 5 and (j - 43) % 6 < 5 else DARKWOOD[1]
            if (i + j) % 4 == 0:
                col = CANVAS[1]
            s.put(i, j, col)
    s.outline()


# ------------------------------------------------------------------------------------------------ the Drifting Shoals
def driftglass(s: Img) -> None:
    """A cluster of driftglass: three shards of sea-worn glass the starsea has set upright in the sand, blue to a cold
    glint, a ring of grit at their foot. Footprint 1 x 1. 16 x 22; corner (0, 20)."""
    s.ellipse(8, 19, 6.5, 2, SAND2[2])
    for cx, top, w, lean in ((5, 7, 2.5, -1), (10, 2, 3, 1), (13, 11, 2, 0)):
        for j in range(top, 19):
            half = max(0.6, w * (j - top + 2) / (19 - top + 2))
            off = lean * (19 - j) // 8
            for i in range(int(cx + off - half), int(cx + off + half) + 1):
                u = (i - (cx + off - half)) / (2 * half + 0.01)
                col = GLASS[3] if u < 0.35 else GLASS[2] if u < 0.75 else GLASS[1]
                if j == top:
                    col = GLASS[4]
                s.put(i, j, col)
    s.put(11, 4, STARLIGHT)
    s.put(4, 9, GLASS[4])
    s.outline()


def star_crystal(s: Img) -> None:
    """A star crystal grown out of the rock: a tall six-faced spire of violet glass with two smaller ones at its side,
    the light caught inside them, a stone foot. Footprint 1 x 1. 20 x 44; corner (2, 42)."""
    s.ellipse(10, 40, 8, 3, ROCK[3], (ROCK[5], ROCK[1]))
    for cx, top, half in ((10, 3, 3.6), (5, 22, 2.4), (15, 26, 2.2)):
        for j in range(top, 40):
            h = half if j > top + half * 2 else (j - top) / 2.0 + 0.5
            for i in range(int(cx - h), int(cx + h) + 1):
                u = (i - (cx - h)) / (2 * h + 0.01)
                col = CRYSTAL[3] if u < 0.3 else CRYSTAL[2] if u < 0.65 else CRYSTAL[1]
                s.put(i, j, col)
    s.vline(9, 8, 26, CRYSTAL[4])
    _star(s, 10, 16, STARLIGHT, CRYSTAL[4])
    s.put(4, 27, CRYSTAL[4])
    s.outline()


# --------------------------------------------------------------------------------------------------- Blackmast Haven
def black_mast(s: Img) -> None:
    """A mast of Blackmast Haven: a tarred pole over its step, a crow's nest, two yards with their sails of black silk
    hanging tattered, a bone-white star painted on the lower one, lines to the deck. Footprint 1 x 1. 40 x 88; corner
    (12, 86)."""
    _line(s, 2, 44, 15, 84, CANVAS[1])                               # the lines to the deck
    _line(s, 38, 44, 25, 84, CANVAS[1])
    s.rect(14, 82, 12, 4, DARKWOOD[2])                               # the step
    s.hline(14, 82, 12, WOOD2[3])
    for y in range(4, 83):                                           # the pole
        s.rect(18, y, 4, 1, SAILBLACK[2])
        s.put(18, y, SAILBLACK[4])
        s.put(21, y, SAILBLACK[0])
    s.rect(14, 10, 12, 4, DARKWOOD[2])                               # the crow's nest
    s.hline(14, 10, 12, WOOD2[3])
    s.put(20, 2, RED2[3])
    s.put(20, 3, RED2[2])

    def sail(top: int, half: int, depth: int, salt: int) -> None:
        s.rect(20 - half - 1, top, 2 * half + 3, 2, DARKWOOD[3])     # the yard
        s.hline(20 - half - 1, top, 2 * half + 3, WOOD2[4])
        for i in range(20 - half, 20 + half + 1):
            d = depth - int(abs(i - 20) * 0.25) - int(h01(i, salt, 851) * 4)
            for j in range(top + 2, top + 2 + d):
                u = (i - (20 - half)) / (2.0 * half)
                col = SAILBLACK[3] if u < 0.2 else SAILBLACK[2] if u < 0.7 else SAILBLACK[1]
                if (j - top) % 7 == 0:
                    col = SAILBLACK[1]
                s.put(i, j, col)
    sail(18, 13, 16, 1)
    sail(42, 18, 22, 2)
    for dx, dy in ((0, -3), (0, -2), (1, -1), (3, 0), (2, 0), (1, 1), (0, 3), (0, 2), (-1, 1), (-3, 0), (-2, 0), (-1, -1), (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        s.put(20 + dx, 53 + dy, BONE[4])                             # the white star on the lower sail
    s.outline()


def pirate_cannon(s: Img) -> None:
    """A Blackmast cannon of black iron on a red-brown carriage, aimed east: the barrel ringed at its muzzle and
    breech, the knob of its cascabel, two iron-shod wheels. Footprint 2 x 1. 32 x 24; corner (0, 22)."""
    _box(s, 3, 11, 20, 4, 5, RED2, [RED2[0], RED2[1], RED2[1], RED2[2]])     # the carriage
    for y in range(5, 12):                                           # the barrel
        w = 27 if y not in (5, 11) else 26
        for x in range(4, 4 + w):
            col = IRON[3] if y < 7 else IRON[2] if y < 10 else IRON[1]
            s.put(x, y, col)
    for x in (9, 26):                                                # its rings
        s.vline(x, 4, 9, IRON[4])
    s.rect(30, 4, 2, 9, IRON[2])                                     # the muzzle
    s.put(31, 8, c("06060A"))
    s.ellipse(3, 8, 1.8, 1.8, IRON[3])                               # the cascabel
    for wx in (7, 19):                                               # the wheels
        s.ellipse(wx, 18, 3.6, 3.6, IRON[2], (IRON[4], IRON[0]))
        s.ellipse(wx, 18, 1.4, 1.4, RED2[2])
    s.outline()


def powder_keg(s: Img) -> None:
    """A powder keg of the Blackmast gunners: tarred staves, a red band round its belly, a white cross daubed on it and a
    short fuse out of its bung. Footprint 1 x 1. 16 x 20; corner (0, 18)."""
    s.ellipse(8, 15, 6, 3.5, SAILBLACK[1])
    s.rect(2, 7, 12, 9, SAILBLACK[2])
    s.rect(2, 7, 2, 9, SAILBLACK[4])
    s.rect(12, 7, 2, 9, SAILBLACK[1])
    s.ellipse(8, 7, 6, 2.4, SAILBLACK[3])
    s.ellipse(8, 7, 3.5, 1.3, SAILBLACK[1])
    s.hline(2, 11, 12, RED2[3])
    s.hline(2, 12, 12, RED2[2])
    for k in range(3):
        s.put(6 + k, 13 + k // 2, PAPER)
        s.put(8 - k, 13 + k // 2, PAPER)
    s.put(9, 5, DIRT[3])
    s.put(10, 4, DIRT[4])
    s.put(11, 3, LANTERN[4])
    s.outline()


def pirate_banner(s: Img, f: int = 0) -> None:
    """A Blackmast banner on a tarred pole: a long black silk with a bone-white star over two crossed bones, its
    swallow tail stirring a pixel over four frames. Footprint 1 x 1. 16 x 60; corner (0, 58)."""
    sway = (0, 1, 1, 0)[f]
    s.rect(3, 54, 10, 4, STONE2[2])
    s.hline(3, 54, 10, STONE2[4])
    s.rect(5, 6, 2, 49, SAILBLACK[2])
    s.vline(5, 6, 49, SAILBLACK[4])
    s.rect(4, 3, 4, 3, BONE[3])
    s.rect(5, 7, 9, 2, DARKWOOD[2])
    s.hline(5, 7, 9, DARKWOOD[4])
    for j in range(9, 40):
        tail = sway if j > 30 else 0
        s.rect(7 + tail, j, 6, 1, SAILBLACK[2])
        s.put(7 + tail, j, SAILBLACK[4])
        s.put(12 + tail, j, SAILBLACK[0])
    for k in range(3):
        s.put(8 + k + sway, 40 + k, SAILBLACK[2])
        s.put(12 - k + sway, 40 + k, SAILBLACK[2])
    for dx, dy in ((0, -2), (0, -1), (-1, 0), (0, 0), (1, 0), (-2, 0), (2, 0), (0, 1), (-1, 2), (1, 2)):
        s.put(10 + dx, 16 + dy, BONE[4])                             # the star
    for k in range(5):                                               # the crossed bones
        s.put(8 + k, 22 + k, BONE[3])
        s.put(12 - k, 22 + k, BONE[3])
    s.outline()


# --------------------------------------------------------------------------------------------------- the Wyrmnest Isles
def rock_spire(s: Img) -> None:
    """A spire of the Wyrmnest Isles: a tall pinnacle of pale limestone in courses, lit on its west face, a nest of
    twigs lodged on its crown where a star-wyrm once slept. Footprint 1 x 1. 24 x 60; corner (4, 58)."""
    s.ellipse(12, 56, 10, 3, ROCK[2])
    for j in range(9, 57):
        t = (j - 9) / 47.0
        mid = 12 + int((1 - t) * 3)                                 # it leans a little east toward its crown
        wob = (h01(j // 4, 1, 862) - 0.5) * 2.2                     # its faces weathered unevenly, course by course
        lo = mid - (2.0 + t * 6.0 + wob)
        hi = mid + (1.5 + t * 5.5 - wob * 0.6)
        for i in range(int(lo), int(hi) + 1):
            u = (i - lo) / (hi - lo + 0.01)
            col = ROCK[5] if u < 0.22 else ROCK[4] if u < 0.5 else ROCK[3] if u < 0.78 else ROCK[2]
            if h01(i, j // 3, 863) < 0.06:
                col = ROCK[2]
            s.put(i, j, col)
        if j % 9 == 4:                                              # a ledge of its strata
            s.put(int(hi), j, ROCK[1])
            s.put(int(lo) + 1, j, ROCK[6])
    for k in range(5):                                              # cracks
        x = 10 + int(h01(k, 1, 861) * 5)
        y = 16 + k * 8
        s.put(x, y, ROCK[1])
        s.put(x + 1, y + 1, ROCK[1])
        s.put(x + 1, y + 2, ROCK[2])
    for i in range(10, 21):                                         # the old nest on its crown
        s.put(i, 8, WOOD[3] if i % 3 else WOOD[2])
        s.put(i, 9, WOOD[2])
    s.hline(11, 7, 9, WOOD[4])
    s.put(13, 6, BONE[4])
    s.put(17, 6, BONE[3])
    s.outline()


def wyrm_nest(s: Img) -> None:
    """A star-wyrm's nest: a wide ring of branches, driftwood and old bones woven together, its rim lit, the hollow
    inside lined with down, three pale eggs flecked with star-blue in it, one cracked open. Footprint 3 x 1. 48 x 28;
    corner (0, 26)."""
    s.ellipse(24, 16, 23, 10, WOOD[2])
    s.ellipse(24, 15, 22, 9, WOOD[3], (WOOD[5], WOOD[1]))
    for k in range(40):                                             # the woven sticks
        x = 3 + int(h01(k, 1, 871) * 42)
        y = 8 + int(h01(k, 2, 871) * 14)
        if s.get(x, y)[3]:
            for d in range(4):
                s.put(x + d, y + (d // 2) * (1 if k % 2 else -1), WOOD[4] if k % 3 else DARKWOOD[2])
    s.ellipse(24, 13, 15, 5.5, DARKWOOD[1])                         # the hollow
    s.ellipse(24, 13.5, 13, 4.5, CANVAS[2])
    for k, (x, y) in enumerate(((17, 12), (24, 11), (31, 13))):      # the eggs
        s.ellipse(x, y, 3.2, 4, BONE[4] if k != 2 else BONE[3], (STARLIGHT, BONE[2]))
        s.put(x - 1, y, GLASS[2])
        s.put(x + 1, y + 2, GLASS[2])
    for i in range(29, 34):                                         # one cracked open
        s.put(i, 10 + (i % 2), BONE[1])
    for x, y in ((6, 9), (40, 8), (44, 16)):                         # bones in the weave
        s.hline(x, y, 4, BONE[4])
        s.put(x, y - 1, BONE[3])
        s.put(x + 3, y + 1, BONE[3])
    s.outline()


def wyrm_skull(s: Img) -> None:
    """The skull of a star-wyrm long dead, lying on its jaw facing east: a long bleached snout, the dark socket of an
    eye, a row of teeth, a horn sweeping back over it. Footprint 2 x 1. 32 x 26; corner (0, 24)."""
    for i in range(2, 31):                                          # the skull's mass, tapering to the snout
        top = 9 + int(max(0, i - 12) * 0.32)
        bot = 22 - int(max(0, i - 22) * 0.4)
        for j in range(top, bot):
            u = (j - top) / float(max(1, bot - top))
            col = BONE[4] if u < 0.25 else BONE[3] if u < 0.6 else BONE[2]
            s.put(i, j, col)
    s.ellipse(12, 13, 2.6, 2.2, BONE[0])                            # the eye socket
    s.put(11, 12, c("1A1612"))
    s.ellipse(27, 14, 1.2, 0.9, BONE[1])                            # a nostril
    for i in range(14, 30, 3):                                      # the teeth
        s.put(i, 18, BONE[4])
        s.put(i, 19, BONE[3])
    s.hline(13, 17, 16, BONE[1])
    for k in range(14):                                             # the horn sweeping back
        x = 9 - k // 2
        y = 9 - int((k / 13.0) ** 0.8 * 7)
        s.put(x, y, BONE[3])
        s.put(x + 1, y, BONE[2])
        s.put(x, y + 1, BONE[2])
    s.outline()


def wyrm_ribs(s: Img) -> None:
    """The ribs of a star-wyrm half sunk in the rock: its spine a row of knuckled vertebrae, five ribs arching from it to
    the ground, shorter toward the tail. Footprint 3 x 1. 48 x 36; corner (0, 34)."""
    spine = [(3 + k * 7, 6 + k * 3) for k in range(6)]              # the spine, falling toward the tail
    for k, (x0, y0) in enumerate(spine):
        h = 33 - y0
        for j in range(y0 + 2, 34):                                 # each rib a bow from the spine down to the ground
            t = (j - y0 - 2) / float(h)
            dx = int(round(math.sin(t * math.pi) * (6 - k * 0.6)))  # swelling out, then in to the ground
            s.put(x0 + 3 + dx, j, BONE[3] if t < 0.45 else BONE[2])
            s.put(x0 + 4 + dx, j, BONE[1])
        s.put(x0 + 3, 33, BONE[2])
    for k in range(len(spine) - 1):                                 # the spine between the vertebrae
        _line(s, spine[k][0] + 3, spine[k][1] + 1, spine[k + 1][0] + 1, spine[k + 1][1] + 1, BONE[3])
        _line(s, spine[k][0] + 3, spine[k][1] + 2, spine[k + 1][0] + 1, spine[k + 1][1] + 2, BONE[1])
    for x0, y0 in spine:                                            # the vertebrae, knuckled
        s.rect(x0, y0, 5, 3, BONE[3])
        s.hline(x0, y0, 5, BONE[4])
        s.put(x0 + 2, y0 - 1, BONE[4])
    s.outline()


def bone_pile(s: Img) -> None:
    """Old bones scattered on the rock: two long bones crossed and a knuckle. Footprint 1 x 1, flat. 16 x 12; corner
    (0, 10)."""
    for k in range(10):
        s.put(2 + k, 3 + k // 2, BONE[3])
        s.put(2 + k, 4 + k // 2, BONE[1])
        s.put(13 - k, 4 + k // 3, BONE[4])
    for x, y in ((1, 2), (2, 2), (13, 3), (14, 4), (12, 8), (13, 8)):
        s.put(x, y, BONE[4])
    s.ellipse(5, 9, 1.5, 1.2, BONE[2])
    s.outline()


def eggshell(s: Img) -> None:
    """The broken shell of a star-wyrm's egg, fallen in two halves, flecked star-blue, its inside pale. Footprint 1 x 1,
    flat. 16 x 10; corner (0, 8)."""
    s.ellipse(5, 5, 4, 3, BONE[4], (STARLIGHT, BONE[2]))
    s.ellipse(5, 4.5, 2.6, 1.6, BONE[2])
    s.ellipse(11.5, 6, 3, 2.4, BONE[3], (BONE[4], BONE[1]))
    for x, y in ((3, 6), (7, 5), (12, 7)):
        s.put(x, y, GLASS[2])
    for i in range(2, 9):
        s.put(i, 3 + (i % 2), BONE[1])
    s.outline()


PROPS.update({
    # the Skyport Wreck
    "hull_ribs": (hull_ribs, 48, 40, 3, 1, [0, 38], True, [26, -2, 22, 3]),
    "broken_mast": (broken_mast, 24, 64, 1, 1, [4, 62], True, [12, -2, 10, 3]),
    "starsea_anchor": (starsea_anchor, 32, 24, 2, 1, [0, 22], True, [17, -2, 14, 3]),
    "star_ballista": (star_ballista, 32, 34, 2, 1, [0, 32], True, [17, -2, 14, 3]),
    "armillary": (armillary, 24, 40, 1, 1, [4, 38], True, [12, -2, 8, 3]),
    # Lanternfall Harbor
    "star_lantern": (star_lantern, 16, 48, 1, 1, [0, 46], True, [10, -2, 6, 3]),
    "market_stall": (market_stall, 48, 40, 3, 1, [0, 38], True, [26, -2, 22, 3]),
    "harbor_crane": (harbor_crane, 48, 72, 2, 1, [4, 70], True, [17, -2, 14, 3]),
    # the Drifting Shoals
    "driftglass": (driftglass, 16, 22, 1, 1, [0, 20], True, [9, -2, 6, 2]),
    "star_crystal": (star_crystal, 20, 44, 1, 1, [2, 42], True, [10, -2, 7, 3]),
    # Blackmast Haven
    "black_mast": (black_mast, 40, 88, 1, 1, [12, 86], True, [10, -2, 9, 3]),
    "pirate_cannon": (pirate_cannon, 32, 24, 2, 1, [0, 22], True, [17, -2, 14, 3]),
    "powder_keg": (powder_keg, 16, 20, 1, 1, [0, 18], True, [10, -2, 6, 3]),
    "pirate_banner": (pirate_banner, 16, 60, 1, 1, [0, 58], True, [10, -2, 6, 3]),
    # the Wyrmnest Isles
    "rock_spire": (rock_spire, 24, 60, 1, 1, [4, 58], True, [12, -2, 10, 3]),
    "wyrm_nest": (wyrm_nest, 48, 28, 3, 1, [0, 26], True, [26, -2, 22, 3]),
    "wyrm_skull": (wyrm_skull, 32, 26, 2, 1, [0, 24], True, [17, -2, 14, 3]),
    "wyrm_ribs": (wyrm_ribs, 48, 36, 3, 1, [0, 34], True, [26, -2, 22, 3]),
    "bone_pile": (bone_pile, 16, 12, 1, 1, [0, 10], False, None),
    "eggshell": (eggshell, 16, 10, 1, 1, [0, 8], False, None),
})
# The Blackmast banners stir on the wind as the sects' do.
ANIM.update({"pirate_banner": (4, 450)})
