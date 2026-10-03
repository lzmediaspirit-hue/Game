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

# R7: the dry country east of Nine Peaks, the Ironroot hold and the Tomb of Sunscar (E1's rooms): the canyons' rock and
# prayer flags, the desert's palms, cactus, scrub and bones, the hold's anvil and brazier, the tomb's sarcophagi,
# statues, mirrors, traps and throne, the peaks' guardian lions (tools/art/topdown/arid.py), into the sheet with these.
import arid as _ARID  # noqa: E402

PROPS.update(_ARID.PROPS)
ANIM.update(_ARID.ANIM)

# R9: the star field's end (E1's last batch): the Citadel's lanterns, caged star, statues, banners, ballistae, chart
# tables and pressure pillars, the Orbit Ruins' floating stones, crystals, gravity plates and golem husks, the Ashen
# Reach's pyres, tents, banners, embers, ash and charred trees, the Nebula Deep's coral and shells, the Lantern Heart's
# wick pillars and flame basins, and the crossings' masts (tools/art/topdown/starfield.py), into the sheet with these.
import starfield as _STAR  # noqa: E402

PROPS.update(_STAR.PROPS)
ANIM.update(_STAR.ANIM)
