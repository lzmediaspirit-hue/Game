"""R7, the room engine's Act II batch (docs/architecture/room_engine.md, "Nine Peaks to the Tomb of Sunscar (R7)"): the
pieces the dry country east of Nine Peaks is dressed with, drawn as props (art bible §8) in the §14 manner: lit from the
north-west (tops and west faces lit, east ends and fronts a step down), outlined (§4), a floor shadow of their own. They
join the prop sheet through furnish.py (its R7 block), so the layouts place them as any prop, and a biome's flora pools
(tools/content/rooms/biomes.py) name them.

  the canyons  a sandstone boulder banded in red strata, a wind-carved hoodoo with its cap rock, a string of prayer flags
               snapping on the wind (four frames, walk-through);
  the desert   a date palm, a clump of columnar cactus in flower, a tuft of dry scrub (walk-through), a bleached
               ribcage half sunk in the sand;
  the hold     an anvil on its oak stump, an iron brazier burning (four frames);
  the tomb     a sandstone sarcophagus, a sand king's statue, a bronze mirror on its stand, a spike trap's pressure plate
               (walk-through, flat), the Tomb King's sun throne;
  the peaks    a guardian lion of granite on its plinth (Nine Peaks' gate; the lions the side view had at the sects).

None of them is of the foliage kit: the desert's sand (decision 44, laid after the scatter) runs under every one, so a
palm stands in the sand, not on a tuft of meadow. Every value is a coordinate hash or a constant: the build is
byte-identical.
"""
from __future__ import annotations

import math

from canvas import Img, h01
from palette import BRONZER, DARKWOOD, GOLDR, JADE, LANTERN, PAPER, RED, STONE, WOOD, c

# The dry country's ramps, dark -> light, the dark end leaning violet as the §14 ramps do.
SANDSTONE = [c("3A1C24"), c("5E2A2A"), c("88402E"), c("A85A38"), c("C47A4A"), c("DC9C66"), c("F0C28E")]   # red rock
TOMBSTONE = [c("3E2E2E"), c("62483A"), c("8A6A4C"), c("AE8E64"), c("CCAE80"), c("E4CCA0"), c("F6E6C2")]   # dressed tomb stone
PALM = [c("1C2A22"), c("2A4028"), c("3C5A2E"), c("557638"), c("74934A"), c("9CB262"), c("C8D08A")]        # dusty fronds
PALMBARK = [c("2E1E1A"), c("4C3222"), c("6C4A2E"), c("8E663E"), c("AE8452"), c("CCA470")]
CACTUS = [c("12281E"), c("1C3E2A"), c("285834"), c("3A743E"), c("56904A"), c("80B260"), c("B4D488")]
SCRUB = [c("2E2A1E"), c("4A422A"), c("6A5E36"), c("8C7E46"), c("AE9E5E"), c("CCBE80")]
BONE = [c("5E5248"), c("8C7E6C"), c("B4A68E"), c("D4C8AE"), c("ECE4CE"), c("FBF6E6")]
IRON = [c("16161E"), c("262A34"), c("3A404C"), c("566070"), c("7C8796"), c("A8B2BC"), c("D2D8DC")]
FLAGS = [(c("2A4C9A"), c("4A72C4")), (c("D8D4C8"), c("F4F0E4")), (c("A8302C"), c("D24E3A")), (c("2E7A4A"), c("4EA060")),
         (c("D8A030"), c("F2C84E"))]                       # blue, white, red, green, gold: sky, cloud, fire, water, earth
BLOOM = [c("A83A62"), c("E06A8E"), c("F8B2C6")]


def _line(s: Img, x0: int, y0: int, x1: int, y1: int, col) -> None:
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for k in range(n + 1):
        s.put(x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n, col)


def _strata(s: Img, ramp: list, seed: int, x0: int = 0, y0: int = 0) -> None:
    """Bands of a sedimentary rock across what is already drawn: a darker parting every few rows that waves a little,
    and a lit grain here and there (the canyons' red layers)."""
    for y in range(y0, s.h):
        for x in range(x0, s.w):
            col = s.get(x, y)
            if col[3] == 0 or col in (ramp[0], ramp[5], ramp[6]):
                continue
            wave = int(h01(x // 5, y // 7, seed) * 2)
            if (y + wave) % 5 == 0:
                s.put(x, y, ramp[1] if col == ramp[2] else ramp[2])
            elif h01(x, y, seed + 1) < 0.05:
                s.put(x, y, ramp[5])


# ============================================================================================================ the canyons
def red_rock(s: Img) -> None:
    """A sandstone boulder of the canyons, footprint 1 x 1: two weathered lumps banded in red strata, lit on the upper
    left, a cleft between them and grit at its foot. 24 x 22; corner (4, 20)."""
    s.ellipse(12, 13, 10, 7.5, SANDSTONE[3], (SANDSTONE[5], SANDSTONE[1]))
    s.ellipse(8, 10, 6.5, 5.5, SANDSTONE[4], (SANDSTONE[6], SANDSTONE[2]))
    s.ellipse(16, 17, 6, 3, SANDSTONE[2])
    _strata(s, SANDSTONE, 701)
    for j in range(8, 18):                                     # the cleft
        s.put(13 + (j % 4 == 0), j, SANDSTONE[1])
    for k in range(5):                                         # grit at its foot
        s.put(3 + int(h01(k, 1, 702) * 18), 20, SANDSTONE[2])
    s.outline()


def hoodoo(s: Img) -> None:
    """A hoodoo the wind carved out of the canyon's floor, footprint 1 x 1: a broad red base, a neck worn thin by the
    gusts, a pale cap rock balanced on it; banded strata all the way up. 24 x 50; corner (4, 48)."""
    for j in range(8, 48):
        t = (j - 8) / 40.0
        half = 3.0 + 2.5 * abs(t - 0.45) * 2.2 + (3.0 if j > 40 else 0.0) + 1.2 * h01(0, j // 3, 711)
        cx = 12 + int(1.4 * (0.5 - t))                         # the neck leans a little downwind
        for i in range(int(cx - half), int(cx + half) + 1):
            k = 3
            if i <= cx - half + 1:
                k = 5
            elif i >= cx + half - 1:
                k = 1
            elif i < cx:
                k = 4
            s.put(i, j, SANDSTONE[k])
    s.ellipse(12, 7, 8.5, 4.5, TOMBSTONE[3], (TOMBSTONE[5], TOMBSTONE[1]))   # the cap rock, a harder pale stone
    s.ellipse(12, 6, 7, 3, TOMBSTONE[4])
    s.hline(6, 5, 8, TOMBSTONE[6])
    _strata(s, SANDSTONE, 712, 0, 12)
    s.ellipse(12, 46, 9, 2.5, SANDSTONE[2])
    s.outline()


def prayer_flags(s: Img, f: int = 0) -> None:
    """A string of prayer flags between two weathered poles, footprint 3 x 1 (walk-through): eleven little flags in the
    five colours snapping on the wind. Four frames (the room view turns them faster in a gust). 48 x 34; corner (0, 32)."""
    for x in (1, 45):
        s.vline(x, 1, 31, DARKWOOD[3])
        s.vline(x + 1, 1, 31, DARKWOOD[1])
        s.put(x, 1, DARKWOOD[4])
    sag = [0, 1, 2, 3, 3, 4, 4, 4, 3, 3, 2, 1]
    for i in range(3, 45):
        s.put(i, 3 + sag[min(11, (i - 3) * 12 // 42)], PAPER)
    for k in range(11):
        x0 = 4 + k * 4
        top = 3 + sag[min(11, (x0 - 3) * 12 // 42)] + 1
        dark, lit = FLAGS[k % 5]
        lift = (0, 1, 2, 1)[(f + k) % 4]                      # each flag a beat behind the one before it
        for j in range(6):
            sway = (j * lift) // 3
            for i in range(3):
                if j == 5 and (i + f + k) % 2:
                    continue
                s.put(x0 + i + sway, top + j, lit if i == 0 or j == 0 else dark)
    s.outline()


# ============================================================================================================ the desert
def palm(s: Img) -> None:
    """A date palm of the oases, footprint 1 x 1: a ringed trunk curving up out of the sand, a crown of seven fronds
    arching out and drooping (lit along their upper edges), a cluster of dates under it. 48 x 64; the trunk's footprint
    corner at (16, 62)."""
    for j in range(14, 62):                                    # the trunk, ringed, bowing east as it climbs
        t = (62 - j) / 48.0
        x = 21 + int(5 * t * t)
        s.rect(x, j, 5, 1, PALMBARK[2])
        s.put(x, j, PALMBARK[4])
        s.put(x + 1, j, PALMBARK[3])
        s.put(x + 4, j, PALMBARK[1])
        if j % 3 == 0:
            s.hline(x + 1, j, 3, PALMBARK[1])
    s.rect(18, 60, 11, 2, PALMBARK[1])
    s.put(18, 60, PALMBARK[3])
    cx, cy = 26, 15
    # The fronds, back ones first: (direction in degrees, east 0 and south 90; length; how far its tip droops).
    fronds = ((-100, 9, 2), (-140, 15, 7), (-45, 15, 7), (-172, 20, 15), (-8, 20, 15), (150, 17, 13), (32, 17, 13),
              (100, 9, 6))
    for k, (deg, ln, droop) in enumerate(fronds):
        a = math.radians(deg)
        dx, dy = math.cos(a), math.sin(a) * 0.7
        for n in range(ln + 1):
            t = n / float(ln)
            x = cx + dx * n
            y = cy + dy * n + droop * t * t                     # the frond arches out and droops toward its tip
            # its heading here, and the leaflets hanging off both sides of the rib (the upper ones lit)
            hx, hy = dx, dy + 2.0 * droop * t / ln
            nrm = math.hypot(hx, hy) or 1.0
            px, py = -hy / nrm, hx / nrm
            w = 3.2 * (1.0 - t) + 1.0
            for side in (-1, 1):
                for m in range(1, int(w) + 1):
                    lx = x + px * m * side
                    ly = y + py * m * side + m * 0.55              # leaflets hang
                    up = (py * side) < 0
                    col = PALM[5] if up else PALM[2]
                    if (n + m) % 3 == 0:
                        col = PALM[4] if up else PALM[1]
                    s.put(int(round(lx)), int(round(ly)), col)
            s.put(int(round(x)), int(round(y)), PALM[3])
            if n < ln * 0.75:
                s.put(int(round(x)), int(round(y)) - 1, PALM[6] if k % 2 else PALM[5])   # the sunlit rib
    s.ellipse(cx, cy, 3, 2.2, PALM[3], (PALM[5], PALM[1]))       # the heart of the crown
    for k in range(9):                                         # the dates
        x, y = 23 + int(h01(k, 1, 731) * 7), 18 + int(h01(k, 2, 731) * 4)
        s.put(x, y, c("8A3A1E") if k % 3 else c("C0602A"))
    s.outline()


def cactus(s: Img) -> None:
    """A clump of columnar cactus, footprint 1 x 1: a tall ribbed column and two shorter beside it, lit on the west,
    pale spines along the ribs, a pink flower on the tallest. 24 x 38; corner (4, 36)."""
    for cx, top, half in ((12, 4, 3), (6, 15, 2), (18, 11, 2)):
        for j in range(top, 36):
            for i in range(cx - half, cx + half + 1):
                k = 3
                if i == cx - half:
                    k = 5
                elif i == cx + half:
                    k = 1
                elif (i - cx + half) % 2 == 1:
                    k = 2 if i > cx else 4                     # the ribs
                if j == top and i in (cx - half, cx + half):
                    continue
                s.put(i, j, CACTUS[k])
            if (j - top) % 4 == 2:
                s.put(cx - half - 1, j, BONE[4])               # spines
                s.put(cx + half + 1, j + 1, BONE[3])
        s.hline(cx - half + 1, top, 2 * half - 1, CACTUS[6])
    s.rect(11, 1, 3, 3, BLOOM[1])
    s.put(11, 1, BLOOM[2])
    s.put(12, 2, GOLDR[2])
    s.ellipse(12, 36, 9, 1.5, CACTUS[1])
    s.outline()


def dry_scrub(s: Img) -> None:
    """A tuft of desert scrub, footprint 1 x 1 (walk-through): a round tangle of dry twigs fanning out of the sand, a few
    grey-green leaves still on them, lit on the north-west. 20 x 16; corner (2, 14)."""
    for k in range(16):
        a = math.pi * (1.05 + 0.9 * k / 15.0)
        r = 6.0 + h01(k, 1, 741) * 3.0
        x1, y1 = 10 + int(math.cos(a) * r * 1.05), 13 + int(math.sin(a) * r * 1.2)
        _line(s, 10, 14, x1, y1, SCRUB[3] if k % 3 else SCRUB[2])
        _line(s, (10 + x1) // 2, (14 + y1) // 2, x1 + (1 if k % 2 else -1), y1 - 1, SCRUB[2])
        s.put(x1, y1, SCRUB[5] if x1 < 10 else SCRUB[4])
    for k in range(18):
        x, y = 3 + int(h01(k, 3, 741) * 14), 2 + int(h01(k, 4, 741) * 10)
        if s.get(x, y)[3]:
            lit = x + y < 15
            s.put(x, y, PALM[5] if lit else PALM[3])
            s.put(x + 1, y, PALM[4] if lit else PALM[2])
    s.hline(6, 14, 9, SCRUB[1])
    s.outline()


def ribcage(s: Img) -> None:
    """The bleached ribs of something huge, half sunk in the sand, footprint 2 x 1: the spine along the ground and six
    ribs arching up out of it, lit on their west sides, the last one broken. 32 x 26; corner (0, 24)."""
    s.ellipse(16, 22, 15, 3, BONE[1])                          # the sand heaped round it
    for i in range(2, 30):                                      # the spine
        s.put(i, 20, BONE[3] if i % 3 else BONE[1])
        s.put(i, 19, BONE[4] if i % 3 else BONE[2])
    for k in range(6):
        x = 5 + k * 4
        hgt = 15 - abs(k - 2) * 2
        if k == 5:
            hgt = 6                                             # broken off
        for j in range(hgt):
            bow = int(3.5 * (1.0 - ((j - hgt / 2.0) / (hgt / 2.0)) ** 2)) if hgt > 2 else 0
            y = 19 - j
            s.put(x - bow, y, BONE[4] if j < hgt - 1 else BONE[5])
            s.put(x - bow + 1, y, BONE[2])
    s.outline()


def yurt(s: Img) -> None:
    """The oasis keeper's yurt, footprint 3 x 2: a round tent of white felt over a lattice, its domed roof belted with
    rope and its crown ring open to the sky, a red door hung on its south side, its skirt dusty from the sand. 48 x 44;
    corner (0, 42)."""
    felt = [c("6E6458"), c("9A8E7C"), c("C2B6A0"), c("DCD2BC"), c("F0E8D6"), c("FBF6EA")]
    s.ellipse(24, 38, 22, 5, felt[1])                          # the skirt's footing
    for j in range(20, 39):                                     # the wall: a drum of felt, lit west, shaded east
        for i in range(3, 45):
            dx = (i - 24) / 21.0
            k = 3 if dx < 0.4 else 2
            if dx < -0.75:
                k = 4
            elif dx > 0.8:
                k = 1
            if j > 35:
                k = max(0, k - 1)                               # sand-dusted at its foot
            s.put(i, j, felt[k])
    for i in range(3, 45, 4):                                   # the lattice showing through the felt
        s.vline(i, 22, 13, felt[2] if i < 30 else felt[1])
    s.ellipse(24, 19, 22, 11, felt[3], (felt[5], felt[1]))      # the domed roof
    s.ellipse(24, 17, 15, 7, felt[4])
    for j in range(9, 30):                                      # the rope belts over it
        for x0 in (12, 36):
            s.put(x0 + (j - 19) * (1 if x0 < 24 else -1) // 6, j, c("8A6A3E"))
    s.ellipse(24, 12, 4, 2.2, c("4A3424"), (c("8A6A3E"), c("2A1C14")))   # the crown ring
    s.rect(20, 26, 8, 12, RED[2])                               # the door hanging
    s.vline(20, 26, 12, RED[4])
    s.hline(20, 26, 8, GOLDR[2])
    for j in range(28, 38, 3):
        s.hline(21, j, 6, RED[1])
    s.outline()


# ============================================================================================================ the hold
def anvil(s: Img) -> None:
    """A smith's anvil on an oak stump, footprint 1 x 1: the iron face lit along its north edge, the horn to the west,
    the stump's rings and bark below. 16 x 22; corner (0, 20)."""
    s.ellipse(8, 18, 6, 3, WOOD[2])
    s.rect(2, 12, 12, 7, WOOD[3])
    s.vline(2, 12, 7, WOOD[5])
    s.vline(13, 12, 7, WOOD[1])
    s.ellipse(8, 12, 6, 2, WOOD[4])
    s.ellipse(8, 12, 3, 1, WOOD[2])
    s.rect(5, 7, 6, 4, IRON[3])                                 # the waist
    s.rect(2, 3, 13, 4, IRON[3])                                # the face and the heel
    s.hline(2, 3, 13, IRON[6])
    s.hline(3, 4, 11, IRON[4])
    s.rect(0, 4, 3, 2, IRON[4])                                 # the horn
    s.put(0, 5, IRON[2])
    s.vline(14, 3, 4, IRON[1])
    s.hline(4, 10, 8, IRON[1])
    s.outline()


def brazier(s: Img, f: int = 0) -> None:
    """An iron brazier on three legs, coals glowing in its bowl and a flame licking up out of it. Four frames of the
    flame. Footprint 1 x 1. 16 x 28; corner (0, 26)."""
    for x in (3, 8, 12):
        s.vline(x, 18, 8, IRON[2])
        s.put(x, 25, IRON[1])
    s.ellipse(8, 16, 7, 3.5, IRON[3], (IRON[5], IRON[1]))
    s.ellipse(8, 15, 5.5, 2, LANTERN[1])
    for k in range(5):
        s.put(4 + k * 2, 15, LANTERN[3] if (k + f) % 2 else LANTERN[2])
    lick = [(0, 0, 1, 0), (1, 0, 0, -1), (0, 1, 0, 0), (-1, 0, 1, 1)][f]
    for j in range(8):                                          # the flame, narrowing as it rises
        w = max(0, 3 - j // 3)
        x0 = 8 + lick[j % 4] - w
        for i in range(2 * w + 1):
            col = LANTERN[4] if j < 3 else LANTERN[3]
            if i == w and j < 5:
                col = LANTERN[5]
            s.put(x0 + i, 13 - j, col)
    s.outline()


def roots(s: Img) -> None:
    """The roots of the iron-root trees breaking out of the rock, footprint 2 x 1: three thick roots arching up out of
    the ground and diving back into it, their bark dark as old iron with a cold sheen along their backs, a few hair
    roots trailing. 32 x 24; corner (0, 22)."""
    bark = [c("1A1416"), c("2E2426"), c("463638"), c("5E4C4A"), c("7C6A64"), c("A6A2A4")]
    s.ellipse(16, 21, 15, 2.5, bark[1])
    for k, (x0, x1, top, th) in enumerate(((1, 20, 6, 4), (10, 30, 10, 3.5), (4, 14, 15, 3))):
        for i in range(x0, x1 + 1):
            t = (i - x0) / float(x1 - x0)
            y = 21 - (21 - top) * 4.0 * t * (1.0 - t)          # the arch, its feet in the ground
            for j in range(int(th) + 1):
                col = bark[3]
                if j == 0:
                    col = bark[5] if (i + k) % 3 else bark[4]  # the sheen along its back
                elif j == 1:
                    col = bark[4]
                elif j >= int(th):
                    col = bark[1]
                if h01(i, j, 791 + k) < 0.12:
                    col = bark[2]                               # the bark's cracks
                s.put(i, int(y) + j, col)
    for k in range(5):                                          # hair roots
        x = 3 + int(h01(k, 1, 792) * 26)
        for j in range(2 + k % 3):
            s.put(x + (j % 2), 19 + j, bark[2])
    s.outline()


# ============================================================================================================ the tomb
def sarcophagus(s: Img) -> None:
    """A sand king's sarcophagus, footprint 2 x 1: a long chest of dressed tomb stone, its lid carved with a sun disc in
    gold leaf between bands of glyphs, a step of plinth round its foot. 32 x 26; corner (0, 24)."""
    s.rect(0, 20, 32, 4, TOMBSTONE[2])                          # the plinth
    s.hline(0, 20, 32, TOMBSTONE[4])
    s.rect(2, 4, 28, 10, TOMBSTONE[4])                          # the lid
    s.hline(2, 4, 28, TOMBSTONE[6])
    s.vline(2, 4, 10, TOMBSTONE[5])
    s.vline(29, 4, 10, TOMBSTONE[2])
    s.rect(2, 14, 28, 6, TOMBSTONE[3])                          # the chest's front
    s.vline(2, 14, 6, TOMBSTONE[4])
    s.vline(29, 14, 6, TOMBSTONE[1])
    for i in range(4, 28, 3):                                   # the glyph bands
        s.put(i, 6, TOMBSTONE[2])
        s.put(i + 1, 11, TOMBSTONE[2])
        s.put(i, 16, TOMBSTONE[1])
        s.put(i + 1, 17, TOMBSTONE[5])
    s.ellipse(16, 8.5, 3.5, 2.5, GOLDR[2], (GOLDR[3], GOLDR[0]))
    for k, (dx, dy) in enumerate(((-6, 0), (6, 0), (-4, -2), (4, -2), (-4, 2), (4, 2))):
        s.put(16 + dx, 8 + dy, GOLDR[1 + k % 2])
    s.outline()


def king_statue(s: Img) -> None:
    """A sand king of old, standing on his plinth, footprint 1 x 1: a robe falling to his feet, broad sleeves, hands
    folded over a sun disc at his chest, a tall tiered crown, the stone worn by three thousand years of sand. 24 x 54;
    corner (4, 52)."""
    s.rect(2, 44, 20, 8, TOMBSTONE[2])                          # the plinth
    s.hline(2, 44, 20, TOMBSTONE[4])
    s.vline(2, 44, 8, TOMBSTONE[3])
    s.hline(3, 47, 18, TOMBSTONE[1])
    for j in range(20, 44):                                     # the robe, widening to the hem
        half = 5 + (j - 20) // 7
        for i in range(12 - half, 12 + half + 1):
            k = 4 if i < 12 - half + 2 else (2 if i > 12 + half - 2 else 3)
            if (i - 12) % 3 == 0 and j > 30:
                k -= 1                                          # its folds
            s.put(i, j, TOMBSTONE[k])
    for x0, k in ((4, 4), (16, 2)):                             # the broad sleeves
        s.rect(x0, 19, 4, 11, TOMBSTONE[k])
        s.hline(x0, 29, 4, TOMBSTONE[k - 1])
    s.rect(7, 17, 10, 4, TOMBSTONE[3])                          # the shoulders
    s.hline(6, 17, 12, TOMBSTONE[5])
    s.ellipse(12, 24, 3.6, 3.4, GOLDR[1], (GOLDR[2], GOLDR[0]))  # the sun disc, its gilding worn
    s.put(11, 23, GOLDR[3])
    s.rect(7, 22, 2, 5, TOMBSTONE[5])                           # the hands folded round it
    s.rect(15, 22, 2, 5, TOMBSTONE[2])
    s.ellipse(12, 12, 4.5, 4.5, TOMBSTONE[4], (TOMBSTONE[5], TOMBSTONE[2]))   # the head
    s.put(10, 12, TOMBSTONE[1])
    s.put(14, 12, TOMBSTONE[1])
    s.hline(11, 14, 3, TOMBSTONE[2])
    s.rect(10, 15, 5, 3, TOMBSTONE[3])                          # the beard, plaited
    s.put(12, 17, TOMBSTONE[2])
    for j in range(0, 9):                                       # the tall tiered crown
        half = 4 - j // 3
        s.hline(12 - half, j, 2 * half + 1, TOMBSTONE[4] if j % 3 else TOMBSTONE[5])
        s.put(12 - half, j, TOMBSTONE[5])
        s.put(12 + half, j, TOMBSTONE[2])
    s.hline(8, 8, 9, GOLDR[1])
    for k in range(7):                                          # the wear: pits and a crack
        x, y = 7 + int(h01(k, 1, 761) * 10), 20 + int(h01(k, 2, 761) * 22)
        s.put(x, y, TOMBSTONE[1])
    s.outline()


def bronze_mirror(s: Img) -> None:
    """A bronze mirror on its stand, footprint 1 x 1: the disc polished pale at its heart, green with age round the rim,
    a cloud-scroll frame on two dark-wood legs. 16 x 34; corner (0, 32)."""
    s.rect(2, 30, 12, 2, DARKWOOD[2])
    for x in (4, 11):
        s.vline(x, 18, 12, DARKWOOD[3])
        s.put(x, 18, DARKWOOD[4])
    s.ellipse(8, 11, 6.5, 7, BRONZER[3], (BRONZER[5], BRONZER[1]))
    s.ellipse(8, 11, 5, 5.5, c("3E7A66"))                       # the verdigris ring
    s.ellipse(8, 11, 4, 4.5, c("C8C4B0"), (c("F4F0E2"), c("8E8A7A")))   # the polished face
    s.put(6, 8, PAPER)
    s.put(7, 8, PAPER)
    s.put(6, 9, PAPER)
    s.put(8, 3, JADE)
    s.outline()


def spike_plate(s: Img) -> None:
    """A spike trap's pressure plate set in the floor, footprint 1 x 1 (walk-through, flat): a square of darker stone,
    nine holes, the bronze tips of the spikes glinting in three of them, grit gathered at its seams. 16 x 16; corner
    (0, 16)."""
    s.rect(1, 1, 14, 14, TOMBSTONE[2])
    s.hline(1, 1, 14, TOMBSTONE[1])
    s.vline(1, 1, 14, TOMBSTONE[1])
    s.hline(1, 14, 14, TOMBSTONE[4])
    s.vline(14, 1, 14, TOMBSTONE[3])
    for j in range(3):
        for i in range(3):
            x, y = 3 + i * 4, 3 + j * 4
            s.rect(x, y, 2, 2, TOMBSTONE[0])
            if (i * 3 + j) % 4 == 1:
                s.put(x, y, BRONZER[5])
    for k in range(6):
        s.put(1 + int(h01(k, 1, 771) * 14), 15, TOMBSTONE[5])


def sun_throne(s: Img) -> None:
    """The Tomb King's throne, footprint 3 x 1: a seat of dressed stone on a stepped dais, its back a great sun disc of
    gold and jade rayed in bronze, lions' heads on its arms. 48 x 52; corner (0, 50)."""
    s.rect(0, 44, 48, 6, TOMBSTONE[2])                          # the dais, two steps
    s.hline(0, 44, 48, TOMBSTONE[4])
    s.rect(4, 39, 40, 5, TOMBSTONE[3])
    s.hline(4, 39, 40, TOMBSTONE[5])
    for k in range(16):                                         # the rays
        a = math.pi * (1.0 + k / 15.0)
        _line(s, 24, 18, 24 + int(math.cos(a) * 20), 18 + int(math.sin(a) * 17), BRONZER[3 + k % 2])
    s.ellipse(24, 18, 12, 11, GOLDR[2], (GOLDR[3], GOLDR[0]))   # the sun disc
    s.ellipse(24, 18, 8, 7, GOLDR[1])
    s.ellipse(24, 18, 4.5, 4, JADE, (c("67D6BD"), c("15514F")))
    s.rect(12, 26, 24, 13, TOMBSTONE[3])                        # the seat's back and its seat
    s.hline(12, 26, 24, TOMBSTONE[5])
    s.rect(15, 31, 18, 3, TOMBSTONE[4])
    s.hline(15, 31, 18, TOMBSTONE[6])
    for x0, lit in ((8, True), (34, False)):                    # the arms, a lion's head on each
        s.rect(x0, 28, 6, 11, TOMBSTONE[4] if lit else TOMBSTONE[2])
        s.ellipse(x0 + 3, 27, 3.5, 3, GOLDR[1], (GOLDR[3], GOLDR[0]))
    s.outline()


# ============================================================================================================ the peaks
def guardian_lion(s: Img) -> None:
    """A guardian lion of grey granite on its plinth, footprint 1 x 1: seated, facing the road, its mane in tight curls,
    one forepaw on a ball. 24 x 34; corner (4, 32)."""
    s.rect(1, 25, 22, 7, STONE[2])                              # the plinth
    s.hline(1, 25, 22, STONE[5])
    s.vline(1, 25, 7, STONE[4])
    s.hline(2, 27, 20, STONE[1])
    s.ellipse(13, 19, 8, 6, STONE[3], (STONE[4], STONE[1]))     # the haunches
    for x in (8, 15):                                           # the forelegs
        s.rect(x, 15, 3, 10, STONE[4] if x == 8 else STONE[3])
        s.put(x, 24, STONE[5])
    s.ellipse(6, 22, 2.5, 2.5, STONE[4], (STONE[5], STONE[2]))   # the ball under its paw
    s.ellipse(12, 10, 8, 7, STONE[3], (STONE[5], STONE[1]))     # the mane
    for k in range(14):
        x, y = 5 + int(h01(k, 1, 781) * 14), 4 + int(h01(k, 2, 781) * 12)
        if s.get(x, y)[3]:
            s.put(x, y, STONE[2])
            s.put(x - 1, y - 1, STONE[5])
    s.ellipse(12, 11, 4.5, 4, STONE[4])                          # the face
    s.put(10, 10, STONE[1])
    s.put(14, 10, STONE[1])
    s.rect(11, 12, 3, 2, STONE[2])
    s.put(12, 14, RED[2])                                        # a trace of the red it was painted
    s.outline()


# kind: (draw, w, h, footprint w, h, origin, solid, shadow [dx, dy, rx, ry]) as props.PROPS
PROPS = {
    "red_rock": (red_rock, 24, 22, 1, 1, [4, 20], True, [12, -2, 9, 3]),
    "hoodoo": (hoodoo, 24, 50, 1, 1, [4, 48], True, [12, -2, 9, 3]),
    "prayer_flags": (prayer_flags, 48, 34, 3, 1, [0, 32], False, [26, -2, 22, 2]),
    "palm": (palm, 48, 64, 1, 1, [16, 62], True, [14, -2, 14, 5]),
    "cactus": (cactus, 24, 38, 1, 1, [4, 36], True, [10, -2, 8, 3]),
    "dry_scrub": (dry_scrub, 20, 16, 1, 1, [2, 14], False, None),
    "ribcage": (ribcage, 32, 26, 2, 1, [0, 24], True, [18, -2, 15, 3]),
    "yurt": (yurt, 48, 44, 3, 2, [0, 42], True, [26, -2, 22, 4]),
    "anvil": (anvil, 16, 22, 1, 1, [0, 20], True, [10, -2, 7, 3]),
    "brazier": (brazier, 16, 28, 1, 1, [0, 26], True, [10, -2, 7, 3]),
    "roots": (roots, 32, 24, 2, 1, [0, 22], True, [18, -2, 15, 3]),
    "sarcophagus": (sarcophagus, 32, 26, 2, 1, [0, 24], True, [20, -2, 15, 3]),
    "king_statue": (king_statue, 24, 54, 1, 1, [4, 52], True, [12, -2, 10, 3]),
    "bronze_mirror": (bronze_mirror, 16, 34, 1, 1, [0, 32], True, [10, -2, 7, 3]),
    "spike_plate": (spike_plate, 16, 16, 1, 1, [0, 16], False, None),
    "sun_throne": (sun_throne, 48, 52, 3, 1, [0, 50], True, [26, -2, 22, 3]),
    "guardian_lion": (guardian_lion, 24, 34, 1, 1, [4, 32], True, [12, -2, 10, 3]),
}
# The flags snap on the wind, faster in a gust (TopdownLife.WINDY, as the washing); the brazier's flame flickers.
ANIM = {"prayer_flags": (4, 380), "brazier": (4, 160)}
