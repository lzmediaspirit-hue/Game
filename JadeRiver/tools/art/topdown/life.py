"""Decision 43, the living world (docs/redesign/art_bible.md §14.13): the small moving things of a room on the grid,
drawn at art resolution under the one sun of §14 (lit from the north-west, shade to the south-east, nothing shaded
black), for tools/art/topdown/build_life.py to pack into art/topdown/life.png:

  critters   sparrows (stand, peck, hop, fly), butterflies in four colours, a dragonfly, a fish's shadow, a frog, hens,
             a cat and a dog, each facing east (the room view mirrors them for west), frames side by side;
  rings      a ripple spreading on the water (a fish rising, a frog's plop, a float);
  puffs      smoke and steam in four sizes, neutral pale grey the view tints (chimney smoke, incense, a cook fire);
  tools      what a villager at work holds: a broom, a shoulder pole with its two baskets (seen from the side and end
             on), a laundry basket;
  hangings   what hangs on an interior's back wall: a lattice window that lets the sun in, nets, bundles of herbs, a
             scroll, a hall's plaque, a shelf of jars, a string of drying fish;
  vistas     the land past a room's edge, each a strip that tiles across (tools/art/topdown/build_life.py packs them in
             art/topdown/vista.png): far karst peaks and nearer ones, a sea of cloud, the valley's hills, the marsh's
             horizon, and the river going on.

Critters and tools carry the prop outline (§4) where they are big enough to need it (hens, the cat and dog, the tools);
insects, fish shadows, puffs and rings have none. Every value comes from a coordinate hash: the build is byte-identical.
"""
from __future__ import annotations

import math

from canvas import Img, h01, vnoise
from palette import (BAMBOO, BRONZER, CLOUD, DARKWOOD, DIRT, GOLDR, JADE, LANTERN, LEAF, LINE, MIST, MOSS2, PAPER,
                     PINE, PLASTER, RED, REED, ROCK2, STONE2, WATER2, WOOD, WOOD2, alpha, c)

CLEARC = (0, 0, 0, 0)


def pix(rows: list, legend: dict, outline: bool = False) -> Img:
    """A sprite from rows of characters: each character's colour from `legend` ('.' is clear)."""
    h = len(rows)
    w = max(len(r) for r in rows)
    pad = 1 if outline else 0
    s = Img(w + pad * 2, h + pad * 2)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != "." and ch != " ":
                s.put(i + pad, j + pad, legend[ch])
    if outline:
        s.outline()
    return s


def strip(frames: list) -> Img:
    """Frames side by side, each in a cell as big as the largest, their feet on the cell's bottom row."""
    w = max(f.w for f in frames)
    h = max(f.h for f in frames)
    out = Img(w * len(frames), h)
    for k, f in enumerate(frames):
        out.paste(f, k * w + (w - f.w) // 2, h - f.h)
    return out


# ============================================================================================================ birds
SPARROW = {"C": DARKWOOD[2], "c": WOOD[3], "E": LINE, "K": GOLDR[0], "M": WOOD[3], "D": WOOD[2], "L": WOOD[5],
           "W": PAPER, "w": PLASTER[2], "T": DARKWOOD[1], "F": DARKWOOD[1]}


def sparrow() -> dict:
    """A tree sparrow facing east: a chestnut cap, a pale cheek, a streaked brown back lit on top. 9 x 7 cells."""
    stand = [".....cC..", "....cCEK.", ".LLMMCw..", "TDMMDww..", ".DDDww...", "...F.F...", "........."]
    stand2 = [".....cC..", "....cCEK.", ".LLMMCw..", "TDMMDww..", "TDDDww...", "...F.F...", "........."]
    peck = [".........", ".LLMM....", "TDMMDcC..", ".DDDwCEK.", "...wwF...", "...F.....", "........."]
    peck2 = [".........", ".LLMM....", "TDMMDcC..", ".DDDwCE..", "...wwFK..", "...F.....", "........."]
    hop = [".....cC..", "....cCEK.", ".LLMMCw..", "TDMMDww..", ".DDDww...", "...FF....", "........."]
    fly_up = ["..LL.....", "..MLL....", ".TMMDcC..", "TDMMCcEK.", "..Dwww...", ".........", "........."]
    fly_mid = [".........", ".........", ".TLMDcC..", "TDMMMcEK.", "..DwMM...", ".........", "........."]
    fly_down = [".........", ".........", ".TMMDcC..", "TDMMCcEK.", "..DwMD...", "...DL....", "....L...."]
    g = SPARROW
    return {"stand": [pix(stand, g), pix(stand2, g)], "peck": [pix(peck, g), pix(peck2, g)], "hop": [pix(hop, g)],
            "fly": [pix(fly_up, g), pix(fly_mid, g), pix(fly_down, g), pix(fly_mid, g)]}


# ============================================================================================================ insects
def butterfly(col: str) -> list:
    """A butterfly seen from above, four frames of a wingbeat (open, half, edge on, half). 7 x 5."""
    ramps = {"white": (PAPER, PLASTER[2]), "gold": (GOLDR[3], GOLDR[1]), "blue": (CLOUD[3], CLOUD[1]),
             "coral": (LANTERN[4], LANTERN[2])}
    a, b = ramps[col]
    g = {"A": a, "a": b, "B": DARKWOOD[1]}
    opn = [".AA.AA.", "AaaBaaA", ".AaBaA.", "..A.A.."]
    half = ["..A.A..", ".AaBaA.", "..aBa..", "...B..."]
    edge = ["...A...", "...B...", "...B...", "...B..."]
    return [pix(opn, g), pix(half, g), pix(edge, g), pix(half, g)]


def dragonfly() -> list:
    """A dragonfly from above facing east: a long jade body, big eyes, four glassy wings in two frames of their blur."""
    g = {"W": alpha(PAPER, 150), "w": alpha(MIST, 110), "B": JADE, "b": WATER2[3], "E": WATER2[6]}
    f0 = ["..W...W..", "..wW.Ww..", "bbBBBBBBE", "..wW.Ww..", "..W...W.."]
    f1 = [".........", ".wWW.WWw.", "bbBBBBBBE", ".wWW.WWw.", "........."]
    return [pix(f0, g), pix(f1, g)]


# ============================================================================================================ water
def fish() -> list:
    """A fish's shadow in the water seen from above, facing east: dark teal, a lit line down its back, three frames of
    its tail. 11 x 5."""
    g = {"S": alpha(WATER2[0], 150), "s": alpha(WATER2[0], 110), "L": alpha(WATER2[4], 150)}
    f0 = ["..sSSSs....", "sSSLLLSSs..", "..sSSSs....", "..........."]
    f0 = ["s..sSSSs...", "ssSSLLLSSs.", "s..sSSSs..."]
    f1 = [".s.sSSSs...", "ssSSLLLSSs.", "s..sSSSs..."]
    f2 = ["s..sSSSs...", "ssSSLLLSSs.", ".s.sSSSs..."]
    return [pix(f0, g), pix(f1, g), pix(f2, g)]


def rings() -> list:
    """A ripple spreading on the water: four frames of a widening, fading ellipse (the foam's colour). 15 x 7."""
    out = []
    for k, (rx, ry, a) in enumerate(((2.0, 1.0, 230), (3.6, 1.7, 190), (5.2, 2.4, 140), (6.8, 3.0, 90))):
        s = Img(15, 7)
        cx, cy = 7.0, 3.0
        for j in range(7):
            for i in range(15):
                u, v = (i + 0.5 - (cx + 0.5)) / rx, (j + 0.5 - (cy + 0.5)) / ry
                d = math.sqrt(u * u + v * v)
                if abs(d - 1.0) < 0.3 / max(1.0, rx * 0.35):
                    lit = i + j < cx + cy + 1
                    s.put(i, j, alpha(c("E9FBF1") if lit else WATER2[6], a if lit else int(a * 0.7)))
        out.append(s)
    return out


def frog() -> dict:
    """A marsh frog facing east: a mossy back lit on top, a pale throat that puffs as it calls, golden eyes; sitting
    (two frames, the throat in and out) and leaping (two). 9 x 7."""
    g = {"G": MOSS2[4], "g": MOSS2[3], "d": MOSS2[2], "L": MOSS2[5], "E": GOLDR[2], "e": LINE, "Y": c("D8D0A0"),
         "y": c("E8E2B8")}
    sit = [".....LE..", "...LLGeG.", ".LGGGGGgY", "dGgGGgYY.", ".dd.dd..."]
    call = [".....LE..", "...LLGeG.", ".LGGGGGgy", "dGgGGgyyy", ".dd.ddyy."]
    leap = ["......LE.", "....LLGeG", "..LGGGGgY", "ddGgggY..", "d........"]
    land = [".........", "....LLE..", ".LGGGGeG.", "dGgGGgGgY", "dd.dd...."]
    return {"sit": [pix(sit, g, True), pix(call, g, True)], "leap": [pix(leap, g, True), pix(land, g, True)]}


# ============================================================================================================ village animals
def hen(brown: bool = False) -> dict:
    """A village hen facing east: a white (or russet) body lit from the north-west, a red comb and wattle, a gold beak
    and legs; standing, pecking, walking and flapping in a run. 12 x 12."""
    if brown:
        body = {"W": WOOD[4], "w": WOOD[3], "s": WOOD[2], "T": DARKWOOD[2]}
    else:
        body = {"W": PAPER, "w": PLASTER[2], "s": PLASTER[1], "T": PLASTER[1]}
    g = dict(body, R=RED[3], r=RED[2], K=GOLDR[2], E=LINE, F=GOLDR[1])
    stand = ["........R...", ".......RRW..", ".......WEWK.", "......WWWr..", "T....WWWW...", "TTWWWWWWWW..",
             ".TWWWwwwWW..", "..wWwwwws...", "...sssss....", "....F..F....", "....F..F...."]
    stand2 = ["........R...", ".......RRW..", ".......WEWK.", "......WWWr..", ".T...WWWW...", "TTWWWWWWWW..",
              ".TWWWwwwWW..", "..wWwwwws...", "...sssss....", "....F..F....", "....F..F...."]
    peck = ["............", "............", "............", ".T..........", "TTWWWWWW....", ".TWWWwwwWR..",
            "..wWwwwwWWRW", "...sssssWEWK", "....F..F.r..", "....F..F....", "....F..F...."]
    walk = ["........R...", ".......RRW..", ".......WEWK.", "......WWWr..", "T....WWWW...", "TTWWWWWWWW..",
            ".TWWWwwwWW..", "..wWwwwws...", "...sssss....", "...F...F....", "..F.....F..."]
    flap = [".....W......", "....WWW.R...", "...WWwWRRW..", "..WWw..WEWK.", "T.....WWWr..", "TTWWWWWWW...",
            ".TWWWwwwW...", "..wWwwws....", "...sssss....", "...F....F...", "..F......F.."]
    o = True
    return {"stand": [pix(stand, g, o), pix(stand2, g, o)], "peck": [pix(peck, g, o), pix(stand, g, o)],
            "walk": [pix(walk, g, o), pix(stand, g, o)], "flap": [pix(flap, g, o), pix(walk, g, o)]}


def cat() -> dict:
    """A grey tabby facing east: sitting with its tail curled and flicking, walking (four frames), and asleep in a curl
    that breathes. 14 x 11."""
    g = {"G": STONE2[4], "g": STONE2[3], "d": STONE2[2], "L": STONE2[5], "E": GOLDR[3], "e": LINE, "P": c("E7A0BE"),
         "W": PAPER}
    sit = ["..........L.L.", "..........GLG.", ".........GEgE.", ".........gGPG.", "........gGWW..", ".......gGGg...",
           "......gGgGg...", ".dd...gGgGg...", "..dd..gdgdg...", "...ddgggggg...", "......W..W...."]
    sit2 = ["..........L.L.", "..........GLG.", ".........GEgE.", ".........gGPG.", "........gGWW..", ".......gGGg...",
            "......gGgGg...", "......gGgGg...", "......gdgdg...", "..ddddgggggg..", "......W..W...."]
    walk0 = ["..............", "...........LL.", "..........GLGG", "d.........GEgP", ".d.LGGGGGgGGW.", "..dGgGgGgGgGW.",
             "...dgdgdgdgg..", "...g.d...g.d..", "...W..W..W..W."]
    walk1 = ["..............", "...........LL.", "d.........GLGG", ".d........GEgP", "..dLGGGGGgGGW.", "...GgGgGgGgGW.",
             "...dgdgdgdgg..", "....gd....gd..", "....WW....WW.."]
    sleep = ["..............", "..............", "..............", "....LLGGGL....", "..LGgGgGgGGL..", ".dGgGgGgGgEGL.",
             ".dggdgdgdggGWd", "..dddgggggddd."]
    sleep2 = ["..............", "..............", "..............", "..............", "...LLGGGGLL...", ".dLGgGgGgGEGL.",
              ".dggdgdgdggGWd", "..dddgggggddd."]
    o = True
    return {"sit": [pix(sit, g, o), pix(sit2, g, o)], "walk": [pix(walk0, g, o), pix(walk1, g, o)],
            "sleep": [pix(sleep, g, o), pix(sleep2, g, o)]}


def dog() -> dict:
    """A tan village dog facing east: lying with its head up, sitting and wagging, trotting (two frames). 16 x 12."""
    g = {"T": WOOD2[5], "t": WOOD2[4], "d": WOOD2[3], "L": WOOD2[6], "E": LINE, "N": DARKWOOD[1], "W": c("F0E4C8")}
    lie = ["................", "...........LL...", "..........LTTd..", "..........TETTN.", ".t.......tTTTW..",
           "..t.LTTTTTTTWW..", "...tTtTtTtTtW...", "...ddddddddd....", "..WW.......WW..."]
    lie2 = ["................", "...........LL...", "..........LTTd..", "..........TETTN.", "t........tTTTW..",
            ".tt.LTTTTTTTWW..", "...tTtTtTtTtW...", "...ddddddddd....", "..WW.......WW..."]
    sit = ["..........LL....", ".........LTTd...", ".........TETTN..", "........tTTTW...", "t......tTTTW....",
           ".t....tTTTtW....", "..t..tTTtTtW....", "...dtTTtTttd....", "....dddddd......", "....WW..WW......"]
    sit2 = ["..........LL....", ".........LTTd...", ".........TETTN..", "........tTTTW...", ".......tTTTW....",
            ".t....tTTTtW....", "t.t..tTTtTtW....", "...dtTTtTttd....", "....dddddd......", "....WW..WW......"]
    trot0 = ["................", "............LL..", "...........LTTd.", ".t.........TETTN", "..tLTTTTTTtTTTW.",
             "...tTtTtTtTtTW..", "...ddddddddddd..", "...d.d.....d.d..", "..W...W...W...W."]
    trot1 = ["................", "............LL..", "t..........LTTd.", ".t.........TETTN", "..tLTTTTTTtTTTW.",
             "...tTtTtTtTtTW..", "...ddddddddddd..", "....dd.....dd...", "....WW.....WW..."]
    o = True
    return {"lie": [pix(lie, g, o), pix(lie2, g, o)], "sit": [pix(sit, g, o), pix(sit2, g, o)],
            "trot": [pix(trot0, g, o), pix(trot1, g, o)]}


# ============================================================================================================ puffs
def puff(r: float) -> Img:
    """A round puff of smoke or steam, lit on its north-west rim and shaded on the south-east, in a neutral pale grey
    the view tints and fades. A 1 px checker thins its rim, so it is soft on the pixel grid."""
    n = int(math.ceil(r * 2)) + 2
    s = Img(n, n)
    cx = cy = n / 2.0
    for j in range(n):
        for i in range(n):
            u, v = (i + 0.5 - cx) / r, (j + 0.5 - cy) / (r * 0.9)
            d = u * u + v * v
            if d > 1.0:
                continue
            if d > 0.72 and (i + j) % 2 == 1:
                continue
            k = u + v
            col = (238, 240, 236) if k < -0.55 else (214, 220, 222) if k < 0.35 else (178, 190, 198)
            s.put(i, j, col + (255,))
    return s


# ============================================================================================================ tools
TOOL = {"S": BAMBOO[4], "s": BAMBOO[3], "d": BAMBOO[2], "B": REED[4], "b": REED[3], "r": REED[2], "W": WOOD[4],
        "w": WOOD[2], "K": DARKWOOD[2], "k": DARKWOOD[1], "L": WOOD[5]}


def broom() -> list:
    """A bamboo broom held at a slant, its twig head swept left, centre and right across the ground: three frames.
    Its handle's top is at the sprite's (6, 0), where the hands hold it; the head rests on the bottom row."""
    head_l = ["......S.", "......s.", ".....S..", ".....s..", "....S...", "....s...", "...Ss...", "..bBBb..",
              ".bBbBBr.", "bBrBbr..", "b.r.b.r."]
    head_c = ["......S.", "......s.", ".....S..", ".....s..", ".....S..", ".....s..", "....Ss..", "...bBBb.",
              "..bBbBBr", "..BrBbr.", ".b.r.b.r"]
    head_r = ["......S.", "......s.", "......S.", "......s.", "......S.", "......s.", ".....Ss.", "....bBBb",
              "...bBbBB", "...BrBbr", "..b.r.b."]
    return [pix(head_l, TOOL, True), pix(head_c, TOOL, True), pix(head_r, TOOL, True)]


def _basket(s: Img, x: int, y: int, full: str = "rice") -> None:
    """A round woven basket 7 wide and 5 tall at (x, y), its load heaped in it."""
    load = {"rice": (PAPER, PLASTER[2]), "fish": (STONE2[5], STONE2[3]), "greens": (LEAF[5], LEAF[3]),
            "wood": (WOOD[4], WOOD[2])}[full]
    for i in range(1, 6):
        s.put(x + i, y, load[0] if i < 4 else load[1])
    for i in range(7):
        for j in range(1, 5):
            if (i in (0, 6) and j == 4):
                continue
            col = REED[4] if i < 2 else REED[3] if i < 5 else REED[2]
            if (i + j) % 2 == 0 and 0 < i < 6:
                col = REED[2] if col != REED[2] else REED[1]
            s.put(x + i, y + j, col)


def pole_side() -> Img:
    """A shoulder pole carried along the way one walks, seen from the side (a carrier facing east or west): the bamboo
    pole bowing a pixel under its load, a rope from each end to a basket of rice. 30 x 17; the shoulder at (15, 0)."""
    s = Img(30, 17)
    for i in range(30):
        y = 1 if 4 < i < 26 else 0
        s.put(i, y, BAMBOO[4])
        s.put(i, y + 1, BAMBOO[2])
    for x in (2, 27):
        for j in range(2, 10):
            s.put(x, j, DIRT[4] if j % 2 else DIRT[3])
    _basket(s, 0, 10, "rice")
    _basket(s, 23, 10, "greens")
    s.outline()
    return s


def pole_end() -> list:
    """The same pole end on (a carrier facing the camera or away): the back basket that shows over the shoulder and the
    front one hanging before the knees. Two sprites, 9 x 8 each; the front basket's rope top at (4, 0)."""
    back = Img(9, 8)
    for j in range(0, 3):
        back.put(4, j, BAMBOO[3])
    _basket(back, 1, 3, "greens")
    back.outline()
    front = Img(9, 8)
    for j in range(0, 3):
        front.put(4, j, DIRT[4] if j % 2 else DIRT[3])
    _basket(front, 1, 3, "rice")
    front.outline()
    return [back, front]


def laundry_basket() -> Img:
    """A wide washing basket heaped with wet cloth (white and indigo), set on the ground. 11 x 6."""
    s = Img(11, 6)
    for i in range(1, 10):
        s.put(i, 0, PAPER if i % 3 else CLOUD[2])
        s.put(i, 1, PLASTER[2] if i % 3 else CLOUD[1])
    for i in range(11):
        for j in range(2, 6):
            if i in (0, 10) and j == 5:
                continue
            col = REED[4] if i < 3 else REED[3] if i < 8 else REED[2]
            if (i + j) % 2 == 0 and 0 < i < 10:
                col = REED[2]
            s.put(i, j, col)
    s.outline()
    return s


# ============================================================================================================ hangings
def window() -> Img:
    """A lattice window in the back wall: a dark timber frame round a grid of paper panes glowing with the day. 16 x 13."""
    s = Img(16, 13)
    s.rect(0, 0, 16, 13, DARKWOOD[1])
    s.rect(1, 1, 14, 11, c("F4E6C0"))
    for x in range(1, 15):
        for y in range(1, 12):
            if x % 3 == 0 or y % 3 == 0:
                s.put(x, y, WOOD[2] if (x + y) % 2 else WOOD[3])
    s.hline(1, 1, 14, c("FFF6DA"))
    s.hline(0, 12, 16, DARKWOOD[2])
    s.hline(0, 0, 16, WOOD[3])
    return s


def nets() -> Img:
    """A fishing net hung in swags from two pegs, a float or two tied in it. 22 x 13."""
    s = Img(22, 13)
    for x in (1, 20):
        s.put(x, 0, DARKWOOD[2])
        s.put(x, 1, DARKWOOD[1])
    for i in range(22):
        sag = int(round(4 * math.sin(math.pi * i / 21)))
        for k in range(0, 9):
            y = 1 + sag + k
            if y < 13 and (i + k) % 3 == 0:
                s.put(i, y, REED[3] if k < 4 else REED[2])
            if y < 13 and (i - k) % 3 == 0 and k < 8:
                s.put(i, y, REED[4] if k < 3 else REED[3])
    for x, y in ((6, 6), (15, 7)):
        s.put(x, y, RED[3])
        s.put(x + 1, y, RED[4])
    return s


def herbs() -> Img:
    """Bundles of herbs drying head down from a cord: green, grey-green and a dark red root. 20 x 11."""
    s = Img(20, 11)
    s.hline(0, 0, 20, DIRT[3])
    for k, x in enumerate((2, 7, 12, 16)):
        cols = [(LEAF[4], LEAF[2]), (MOSS2[4], MOSS2[2]), (RED[2], RED[1]), (LEAF[5], LEAF[3])][k]
        s.vline(x, 1, 2, DIRT[4])
        s.put(x, 3, DIRT[2])
        n = 7 + (k % 2) * 2
        for j in range(n):
            half = min(j, 3) // 1 * 0.6 + 0.5
            for i in range(-int(half), int(half) + 1):
                col = cols[0] if i <= 0 else cols[1]
                if (i + j) % 3 == 2:
                    col = cols[1]
                s.put(x + i, 4 + j, col)
    return s


def scroll() -> Img:
    """A hanging scroll: a silk border round pale paper with a few ink strokes, a dark roller below. 8 x 16."""
    s = Img(8, 16)
    s.hline(1, 0, 6, DARKWOOD[2])
    s.rect(0, 1, 8, 13, CLOUD[1])
    s.rect(1, 2, 6, 11, c("EDE3C8"))
    for y in (4, 5, 7, 9, 10):
        s.put(3 + (y % 2), y, LINE)
    s.put(4, 11, RED[3])
    s.hline(0, 14, 8, DARKWOOD[1])
    s.hline(1, 15, 6, DARKWOOD[2])
    return s


def plaque() -> Img:
    """A hall's name plaque: a gold frame round a dark jade board. 24 x 8."""
    s = Img(24, 8)
    s.rect(0, 0, 24, 8, GOLDR[1])
    s.hline(0, 0, 24, GOLDR[3])
    s.rect(2, 2, 20, 4, c("123A34"))
    for x in (6, 10, 14, 18):
        s.put(x, 3, GOLDR[2])
        s.put(x, 4, GOLDR[1])
    return s


def shelf() -> Img:
    """A wall shelf of pots and jars: glazed jade, brown earthenware and a white one, on a plank lit on its top. 26 x 13."""
    s = Img(26, 13)
    s.rect(0, 10, 26, 2, WOOD[3])
    s.hline(0, 10, 26, WOOD[5])
    s.hline(0, 12, 26, DARKWOOD[1])
    for x0, w, h, col in ((1, 5, 8, (JADE, c("1B6A5E"))), (7, 4, 6, (WOOD[4], WOOD[2])), (12, 6, 9, (BRONZER[4], BRONZER[2])),
                          (19, 3, 5, (PAPER, PLASTER[2])), (22, 4, 7, (JADE, c("1B6A5E")))):
        for j in range(h):
            for i in range(w):
                edge = (j == 0 and i in (0, w - 1))
                if edge:
                    continue
                s.put(x0 + i, 10 - h + j, col[0] if i < w // 2 + (1 if j < 2 else 0) else col[1])
        s.put(x0 + 1, 10 - h + 1, c("F2F7F0") if col[0] != PAPER else PLASTER[1])
    return s


def drying_fish() -> Img:
    """A string of small fish drying on a cord: silver bodies lit on top, dark tails. 22 x 9."""
    s = Img(22, 9)
    s.hline(0, 0, 22, DIRT[3])
    for x in (2, 7, 12, 17):
        s.put(x + 1, 1, DIRT[4])
        for j in range(2, 8):
            w = 1 if j in (2, 7) else 2
            for i in range(w):
                s.put(x + i, j, STONE2[5] if i == 0 else STONE2[3])
        s.put(x, 8, STONE2[2])
        s.put(x + 1, 8, STONE2[2])
    return s


def ribbon_banner() -> Img:
    """A small silk hanging with a sect's knot on it (a hall's back wall): red with a gold cord. 10 x 18."""
    s = Img(10, 18)
    s.hline(0, 0, 10, GOLDR[2])
    s.rect(1, 1, 8, 15, RED[2])
    s.vline(1, 1, 15, RED[4])
    s.vline(8, 1, 15, RED[1])
    for y, x in ((5, 4), (6, 3), (6, 5), (7, 4), (8, 4), (9, 3), (9, 5)):
        s.put(x + 1, y, GOLDR[3])
    for x in (2, 4, 6):
        s.put(x + 1, 16, GOLDR[2])
        s.put(x + 1, 17, GOLDR[1])
    return s


# ============================================================================================================ vistas
def _mix(a: tuple, b: tuple, k: float) -> tuple:
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3)) + (255,)


def _ridge(x: int, w: int, seed: int, base: float, amp: float, n: int = 3, period: int = 0) -> float:
    """A ridge line's height at column x: a sum of periodic value noise (period w so the strip tiles), peaked."""
    y = 0.0
    total = 0.0
    for o in range(n):
        cx = max(4, (w // (3 * (2 ** o))))
        v = vnoise(x, 0, seed + o * 17, cx, 1, w)
        y += (v ** 1.6) * (0.55 ** o)
        total += 0.55 ** o
    return base - amp * y / total


def _pillars(w: int, h: int, seed: int, n: int, tall: tuple, wide: tuple) -> list:
    """A skyline of karst pillars across a strip `w` wide that tiles: n domed columns at hashed places, each steep-sided
    with a rounded top. Returns per column the top row and which peak made it and where on it (-1 west .. 1 east)."""
    peaks_ = []
    for k in range(n):
        cx = h01(k, 1, seed) * w
        ww = wide[0] + h01(k, 2, seed) * (wide[1] - wide[0])
        hh = tall[0] + h01(k, 3, seed) * (tall[1] - tall[0])
        peaks_.append((cx, ww, hh))
    out = []
    for x in range(w):
        best = (h + 0.0, -1, 0.0)
        for k, (cx, ww, hh) in enumerate(peaks_):
            for off in (-w, 0, w):
                dx = (x + 0.5 - cx - off) / ww
                if abs(dx) >= 1.0:
                    continue
                top = h - hh * (1.0 - dx * dx) ** 0.45 + 3.0 * vnoise(x, k, seed + 5, 3, 1, w) * (1.0 - abs(dx))
                if top < best[0]:
                    best = (top, k, dx)
        out.append(best)
    return out


def _paint_pillars(img: Img, cols: list, lit: tuple, body: tuple, shade: tuple, haze: tuple, seed: int,
                   fade: float, pines: bool = False) -> None:
    """Paint a pillar skyline: each column lit on its west flank and at its crown, shaded on its east flank, split by
    fissures, lost in the haze toward its foot."""
    for x, (top, k, dx) in enumerate(cols):
        t0 = int(top)
        for y in range(max(0, t0), img.h):
            depth = y - top
            col = body
            if dx < -0.45:
                col = lit
            elif dx > 0.35:
                col = shade
            if depth < 2 and dx < 0.35:
                col = lit
            if k >= 0 and h01(x, k, seed) < 0.1 and depth > 5:
                col = _mix(col, shade, 0.7)
            if k >= 0 and int(y + h01(x // 3, k, seed + 1) * 9) % 13 == 0 and depth > 8:
                col = _mix(col, shade, 0.35)
            img.put(x, y, _mix(col, haze, min(1.0, (y - top) / max(1.0, (img.h - top)) * fade)))
        if pines and k >= 0 and h01(x, 7, seed) < 0.22 and abs(dx) < 0.7 and 1 <= t0 < img.h:
            for j in range(3):
                for i in range(-1, 2):
                    if abs(i) + j < 3:
                        img.put((x + i) % img.w, t0 - 2 + j, PINE[4] if i < 0 else PINE[2] if i > 0 else PINE[3])


def peaks(w: int = 320) -> list:
    """Karst pillars past a sect's edge in layers that tile across, lit from the north-west: each column's west flank
    catches the sun and its east side falls into the blue-violet shade; the farther, the paler and the more lost in the
    mist; pines cling to the nearer crowns. Returns [far (w x 96), mid (w x 84), sea (w x 40)]."""
    far = Img(w, 96)
    _paint_pillars(far, _pillars(w, 96, 311, 11, (40, 92), (10, 22)), c("D6E3E4"), c("B3C8D0"), c("97AFC0"),
                   c("D8E5E8"), 312, 1.0)
    mid = Img(w, 84)
    _paint_pillars(mid, _pillars(w, 84, 733, 8, (34, 80), (12, 26)), c("A9BFB6"), c("7E9AA0"), c("5E7888"),
                   c("C4D6DA"), 734, 1.1, True)
    sea = Img(w, 40)
    for x in range(w):
        crest = 6 + 5 * vnoise(x, 0, 555, 24, 1, w) + 3 * vnoise(x, 0, 556, 8, 1, w)
        for y in range(40):
            if y < crest:
                continue
            d = y - crest
            col = c("F4F7F2") if d < 2 else c("E2EBEA") if d < 6 else c("D2DFE2")
            if d < 1 and (x + y) % 2:
                continue
            sea.put(x, y, col)
    return [far, mid, sea]


def hills(w: int = 320) -> list:
    """The valley's hills past a room's north edge (two layers that tile across): soft blue-green ranges, the nearer
    greener with a line of trees, lit from the north-west. [far (w x 56), near (w x 44)]."""
    far = Img(w, 56)
    hts = [_ridge(x, w, 911, 55.0, 38.0, 3) for x in range(w)]
    for x in range(w):
        top = int(hts[x])
        slope = hts[(x + 1) % w] - hts[x - 1]
        for y in range(max(0, top), 56):
            k = (y - top) / 56.0
            col = c("9FB9B8") if slope > 0.6 else c("86A2A6") if slope < -0.6 else c("93AFB0")
            if y - top < 1:
                col = c("B8CDC6")
            far.put(x, y, _mix(col, c("C3D6D6"), min(1.0, k)))
    near = Img(w, 44)
    hts = [_ridge(x, w, 977, 43.0, 26.0, 3) for x in range(w)]
    for x in range(w):
        top = int(hts[x])
        slope = hts[(x + 1) % w] - hts[x - 1]
        for y in range(max(0, top), 44):
            k = (y - top) / 44.0
            col = c("5E8C6A") if slope > 0.5 else c("456F5C") if slope < -0.5 else c("527D62")
            if y - top < 1:
                col = c("7EA877")
            near.put(x, y, _mix(col, c("9CB9AE"), min(1.0, k * 0.8)))
        if h01(x, 3, 978) < 0.3:
            for j in range(4):
                for i in range(-1, 2):
                    if abs(i) * 2 + j < 5:
                        near.put((x + i) % w, top - 3 + j, LEAF[3] if i <= 0 else LEAF[2])
    return [far, near]


def marsh_horizon(w: int = 320) -> list:
    """The marsh going on past its north edge: a far line of willows and alders in the haze, their crowns rounded and
    lit on the west, and reed beds in bands. [trees (w x 30), reeds (w x 26)]."""
    trees = Img(w, 30)
    crowns = [(h01(k, 1, 431) * w, 5 + h01(k, 2, 431) * 7, 8 + h01(k, 3, 431) * 12) for k in range(34)]
    for x in range(w):
        top, side = 30.0, 0.0
        for cx, r, hh in crowns:
            for off in (-w, 0, w):
                dx = (x + 0.5 - cx - off) / r
                if abs(dx) < 1.0:
                    t = 30 - hh + r * (1.0 - (1.0 - dx * dx) ** 0.5) * 1.4 + 2.0 * vnoise(x, 0, 432, 3, 1, w)
                    if t < top:
                        top, side = t, dx
        for y in range(max(0, int(top)), 30):
            col = c("98B0A6") if side < -0.3 else c("7C958E") if side > 0.3 else c("8AA39A")
            if y - top < 1.5 and side < 0.3:
                col = c("B2C4B8")
            trees.put(x, y, _mix(col, c("B9CBC8"), (y - top) / 34.0))
    reeds = Img(w, 26)
    for x in range(w):
        top = 26 - int(8 + 9 * vnoise(x, 0, 441, 6, 1, w))
        for y in range(max(0, top), 26):
            col = REED[3] if x % 3 else REED[2]
            if (x * 7 + y) % 5 == 0:
                col = REED[4]
            reeds.put(x, y, _mix(col, c("A7B8A8"), max(0.0, 0.5 - (y - top) / 40.0)))
    return [trees, reeds]


def river_on(w: int = 320) -> list:
    """The river going on past a room's south edge and its far bank: a strip of water with glints over a low green bank
    and far hills. [bank (w x 36)]."""
    bank = Img(w, 36)
    for x in range(w):
        edge = 8 + int(3 * vnoise(x, 0, 821, 12, 1, w))
        for y in range(36):
            if y < edge:
                col = WATER2[3] if (x // 3 + y) % 7 else WATER2[4]
                if h01(x, y, 822) < 0.02:
                    col = WATER2[6]
            elif y < edge + 1:
                col = c("E9FBF1")
            elif y < edge + 3:
                col = c("6F9377")
            else:
                col = c("5E8C6A") if (x + y) % 4 else c("527D62")
                col = _mix(col, c("9CB9AE"), (y - edge) / 60.0)
            bank.put(x, y, col)
    return [bank]
