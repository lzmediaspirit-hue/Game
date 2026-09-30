"""Decision 44 (docs/redesign/art_bible.md "Sand and snow"): the sand and snow ground, drawn to Terrain v2's rules
(terrain2.py) and lit by its sun, high in the north-west.

  - **Sand** (paint mark `a`): pale river sand, one 64 px pattern of fine grain with wind ripples in broken rows of
    short crests (a lit north slope, a px of lee shade), a few pebbles and shell chips, and flat stretches between them
    so a footprint or a body reads on it. Its decals: shells, a snail shell, pebbles, a heron's and a crab's tracks,
    crab holes with their pellets, bleached driftwood, a line of wrack, a tuft of dune grass. It darkens to damp sand
    where it meets the water (the `wet` tint over the corners that touch water) and shows through the shallows
    (`beach_fx`, the water's shore in sand). Grass creeps over it with the meadow's own positional overlay; it creeps
    over paths and paving with its own (`creep_over`), a thin drift lit on the sunny side with loose grains beyond it.
    Its face is a beach running into the water at its top, then a low bank of soft strata.
  - **Snow** (`n` fresh, `k` packed): fresh snow an even sunlit white with a faint cool grain, small wind crescents,
    a few buried stones and a sparse sparkle; packed snow two steps down, trodden into prints, glazed in streaks, a
    speck of earth now and then. Each creeps with its own pixels: packed snow over grass, dirt, granite, paving and
    rock, fresh snow over all of those and over packed snow: a lip lit on its sunny side, its front in cold shade, a
    two-step `SHADOW` on the ground below and east of it (lighter under packed snow), and a dusting of flakes past the
    edge. Their face is the karst cliff with the snow's lip hanging over it (lumps lit on top, their undersides cold,
    icicles), snow on its ledges where the rock had moss.

Everything comes from a coordinate hash, never a random generator, so the build is byte-identical.
"""
from __future__ import annotations

import math

from canvas import T, Img, h01
from palette import (DIRT2, GRASS2, MOSS2, REED, ROCK2, SAND2, SHADOW, SHELL, SNOW2, SUN, WATER2, WET, WOOD2, alpha)
from terrain2 import (M, P, _drip, _face_pattern, _shadow_px, cast_shadow, corner_field, d_stones, d_tuft, face_tiles,
                      fbm, hp, mix, pn, rock_face_tex, shore_fx, tint_colour)

# The damp sand's tint over the corners by the water (TopdownTerrain draws it through the tint masks).
WET_TINT = tint_colour(WET, 104)


# ============================================================================================================ sand
RIPPLES = 11   # ripple crests per 64 px down the pattern


def sand_macro(seed: int = 1301) -> Img:
    """Pale river sand, 64 x 64 and periodic: step 4 with a fine grain of steps 3 and 5 (a quartz glint now and then),
    wind ripples running roughly east-west in broken patches (the north slope lit, a px of lee shade under the crest),
    a few pebbles lit from the north-west and chips of shell. Nothing bigger than a pebble, so the period never shows;
    the shells, tracks and holes are decals."""
    img = Img(P, P)
    for y in range(P):
        for x in range(P):
            k = 4
            n = fbm(x, y, seed, (8, 4, 2), (0.35, 0.4, 0.25))
            if n > 0.68:
                k = 5 if hp(x, y, seed + 9) < 0.45 else 4
            elif n < 0.3:
                k = 3 if hp(x, y, seed + 10) < 0.3 else 4
            g = hp(x, y, seed + 1)
            if g < 0.04:
                k = 3
            elif g > 0.985:
                k = 5 if k < 5 else 6
            img.put(x, y, SAND2[k])
    # The ripples: rows of short crests (a lit px on the sunny north slope over a px of lee shade), each a stroke of
    # 4-13 px that sways a px up and down, broken by gaps, and only where a patch noise lets them lie.
    for r in range(RIPPLES):
        y0 = (r * P) // RIPPLES
        x = int(h01(r, 0, seed + 20) * 8)
        end = x + P
        while x < end:
            ln = 4 + int(h01(x, r, seed + 21) * 10)
            gap = 2 + int(h01(x, r, seed + 22) * 5)
            dy = int(h01(x, r, seed + 23) * 2)
            for i in range(ln):
                X = (x + i) % P
                Y = (y0 + dy + round(math.sin((X + r * 7) * 2 * math.pi / 32) * 1.2)) % P
                if pn(X, Y, seed + 4, 16) < 0.4:
                    continue
                tip = i in (0, ln - 1)
                img.put(X, Y, SAND2[5])
                if not tip:
                    img.put(X, (Y + 1) % P, SAND2[3])
            x += ln + gap
    for gy in range(4):
        for gx in range(4):
            if h01(gx, gy, seed + 6) < 0.45:
                continue
            x, y = gx * 16 + 2 + int(h01(gx, gy, seed + 7) * 12), gy * 16 + 2 + int(h01(gx, gy, seed + 8) * 12)
            if h01(gx, gy, seed + 11) < 0.35:     # a chip of shell
                img.put(x % P, y % P, SHELL[3])
                img.put((x + 1) % P, y % P, SHELL[2])
                img.put((x + 1) % P, (y + 1) % P, SAND2[2])
            else:                                  # a pebble
                img.put(x % P, y % P, ROCK2[5])
                img.put((x + 1) % P, y % P, ROCK2[4])
                img.put(x % P, (y + 1) % P, ROCK2[3])
                img.put((x + 1) % P, (y + 1) % P, ROCK2[2])
                img.put((x + 2) % P, (y + 1) % P, SAND2[2])
                img.put((x + 1) % P, (y + 2) % P, SAND2[3])
    return img


def d_shells(seed: int, n: int = 2) -> Img:
    """Fan shells washed up: each a small fan lit on its north-west ribs, a pink shade to the south-east, its hinge
    dark, with a hint of shadow."""
    t = Img(T, T)
    placed = []
    for k in range(n * 4):
        if len(placed) >= n:
            break
        x, y = 2 + int(h01(k, 1, seed) * 10), 2 + int(h01(k, 2, seed) * 10)
        if any(abs(x - a) < 5 and abs(y - b) < 4 for a, b in placed):
            continue
        placed.append((x, y))
        flip = h01(k, 3, seed) < 0.5
        rows = ([".LL.", "LMMS", ".SH."] if not flip else ["LL.", "LMS", ".SH"])
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    t.put(x + i, y + j, {"L": SHELL[3], "M": SHELL[2], "S": SHELL[1], "H": SHELL[0]}[ch])
    cast_shadow(t, ((1, 1, 70), (0, 1, 50), (1, 0, 30)))
    return t


def d_snail(seed: int) -> Img:
    """A snail's empty shell: a tight whorl lit on the north-west, its mouth dark."""
    t = Img(T, T)
    x, y = 3 + int(h01(1, 1, seed) * 9), 3 + int(h01(1, 2, seed) * 9)
    for (i, j), c in (((1, 0), SHELL[3]), ((2, 0), SHELL[2]), ((0, 1), SHELL[3]), ((1, 1), SHELL[1]), ((2, 1), SHELL[2]),
                      ((1, 2), SHELL[2]), ((2, 2), SHELL[0]), ((3, 1), SHELL[1])):
        t.put(x + i, y + j, c)
    cast_shadow(t, ((1, 1, 70), (0, 1, 50), (1, 0, 34)))
    return t


def d_tracks(seed: int, bird: bool = True) -> Img:
    """A line of prints pressed into the sand, crossing the tile on a slant: a heron's three toes, or a crab's
    scuttle (paired dots). A print is a hollow: its north wall in shade, its south lip catching the light."""
    t = Img(T, T)
    dx = 1 if h01(2, 1, seed) < 0.5 else -1
    x, y = (2 if dx > 0 else 12), 2 + int(h01(2, 2, seed) * 3)
    for s in range(4 if bird else 6):
        if bird:
            px, py = x + (s % 2) * 2 * dx, y
            for i, j in ((0, 0), (-1, -1), (1, -1), (0, -2)):
                t.put(px + i, py + j, SAND2[2])
            t.put(px, py + 1, SAND2[5])
            x += 3 * dx
            y += 3
        else:
            for i in (0, 2):
                t.put(x + i, y, SAND2[2])
                t.put(x + i, y + 1, SAND2[5])
            x += 2 * dx
            y += 2
    return t


def d_crab_hole(seed: int) -> Img:
    """A crab's burrow: a dark hole (its north wall in shade, the south rim lit) with the sand pellets it has thrown
    out scattered round it."""
    t = Img(T, T)
    x, y = 5 + int(h01(3, 1, seed) * 5), 5 + int(h01(3, 2, seed) * 5)
    t.put(x, y, SAND2[0])
    t.put(x + 1, y, SAND2[1])
    t.put(x, y - 1, SAND2[2])
    t.put(x + 1, y - 1, SAND2[3])
    t.put(x, y + 1, SAND2[5])
    t.put(x + 1, y + 1, SAND2[6])
    for k in range(5 + int(h01(3, 3, seed) * 4)):
        a = h01(k, 4, seed) * 6.283
        r = 2.5 + h01(k, 5, seed) * 3.0
        px, py = x + round(math.cos(a) * r), y + round(math.sin(a) * r * 0.8)
        if 1 <= px < T - 1 and 1 <= py < T - 1 and t.get(px, py)[3] == 0:
            t.put(px, py, SAND2[5])
            _shadow_px(t, px + 1, py + 1, 50)
    return t


def d_driftwood(seed: int) -> Img:
    """A stick of driftwood bleached by the river: pale grey-brown, lit along its top, a knot, its shadow under it."""
    t = Img(T, T)
    x, y = 2 + int(h01(4, 1, seed) * 4), 5 + int(h01(4, 2, seed) * 6)
    ln = 7 + int(h01(4, 3, seed) * 4)
    pale = mix(WOOD2[5], SAND2[5], 0.55)
    for s in range(ln):
        yy = y + (s * 2) // ln
        t.put(x + s, yy, pale if s % 4 else mix(WOOD2[4], SAND2[4], 0.4))
        t.put(x + s, yy + 1, mix(WOOD2[3], SAND2[3], 0.35))
    t.put(x + ln // 2, y - 1, pale)
    cast_shadow(t, ((0, 1, 80), (1, 1, 60), (1, 2, 30)))
    return t


def d_wrack(seed: int) -> Img:
    """The line of wrack a high water leaves: bits of dead reed and weed in a loose curve, a shell chip in it."""
    t = Img(T, T)
    y0 = 4 + int(h01(5, 1, seed) * 7)
    for x in range(2, T - 2):
        if h01(x, 2, seed) < 0.3:
            continue
        y = y0 + round(math.sin(x * 0.55 + h01(5, 3, seed) * 6) * 1.5)
        c = (REED[1], REED[2], MOSS2[1], REED[3])[int(h01(x, 4, seed) * 4)]
        t.put(x, y, c)
        if h01(x, 5, seed) < 0.3:
            t.put(x, y - 1, REED[2])
    t.put(4 + int(h01(5, 6, seed) * 8), y0 + 1, SHELL[3])
    cast_shadow(t, ((1, 1, 60), (0, 1, 40)))
    return t


def sand_decals() -> list:
    """The sand's decal set, in a fixed order."""
    return [d_shells(1400, 2), d_shells(1401, 1), d_shells(1402, 3), d_snail(1403), d_stones(1404, 2),
            d_stones(1405, 3, SAND2), d_stones(1406, 1, ROCK2, True), d_tracks(1407), d_tracks(1408), d_tracks(1409, False),
            d_crab_hole(1410), d_crab_hole(1411), d_driftwood(1412), d_wrack(1413), d_wrack(1414), d_tuft(1415)]


def sand_face_tex(seed: int = 1321) -> Img:
    """A low sand bank, 64 x 32: soft strata that wave a little in the sand's middle steps (a face stays under 0.65 of
    its top), thin partings a step darker, damp and darker toward its foot, pebbles and a shell set in it."""
    tex = Img(P, 32)
    for y in range(32):
        for x in range(P):
            w = pn(x, y, seed, 16, P, 32) * 3 + pn(x, y, seed + 1, 8, P, 32) * 1.5
            band = int((y + w) // 4)
            k = 3 if band % 3 == 0 else 2
            if (y + w) % 4 < 0.8:
                k = 1
            g = hp(x, y, seed + 2, P, 32)
            if g < 0.06:
                k -= 1
            elif g > 0.96:
                k += 1
            col = SAND2[max(0, min(4, k))]
            col = mix(col, WET, 0.08 + 0.016 * (y % 16))
            tex.put(x, y, col)
    for n in range(10):
        x, y = int(h01(n, 1, seed + 3) * P), int(h01(n, 2, seed + 3) * 32)
        shell = h01(n, 3, seed + 3) < 0.3
        tex.put(x, y, SHELL[2] if shell else ROCK2[4])
        tex.put((x + 1) % P, y, SHELL[1] if shell else ROCK2[3])
        tex.put(x, (y + 1) % 32, SAND2[0])
    return tex


def sand_faces(seed: int = 1321) -> tuple:
    """The sand's face: its first row opens as a beach running down into the water (the room view shows its top 8 px
    over the water): the top's warm rim, dry sand, then sand darkening as it dampens, a glistening swash line and the
    wet sand under the first film of water, each row's edge wandering a px so it never reads as a curb. Below, where a
    sand bank stands over a floor, the strata go on (a crumbling lip, then the soft layers)."""
    pat = _face_pattern(sand_face_tex(seed))
    _drip(pat, SAND2, SAND2, seed + 50, 2, False, 2, 0.35)
    rows = [mix(SAND2[6], SUN, 0.3), SAND2[5], SAND2[4], mix(SAND2[4], WET, 0.22), mix(SAND2[3], WET, 0.3),
            mix(SAND2[3], WET, 0.4), mix(SAND2[2], WATER2[3], 0.3), mix(SAND2[2], WATER2[3], 0.5)]
    for x in range(P):
        off = (1 if hp(x // 3, 0, seed + 70, P, 16) < 0.3 else 0) - (1 if hp(x // 2, 1, seed + 70, P, 16) < 0.2 else 0)
        for y in range(8):
            k = max(0, min(7, y - off)) if y > 1 else y
            col = rows[k]
            if k == 5 and hp(x, y, seed + 71, P, 16) < 0.35:
                col = mix(WATER2[6], SAND2[4], 0.45)          # the swash line glistens
            elif 2 <= k <= 4 and hp(x, y, seed + 72, P, 16) < 0.05:
                col = SAND2[2] if hp(x, y, seed + 73, P, 16) < 0.6 else SHELL[2]
            pat.put(x, y, col)
    return face_tiles(pat)


def beach_fx(sides: int, frame: int) -> Img:
    """The shore of a water cell by sand: as the river's shore (terrain2.shore_fx), but the shallows show the sand
    through the water on every side, and a low beach casts next to no shadow on it."""
    return shore_fx(sides, frame, beach=True)


# ============================================================================================================ snow
def snow_macro(seed: int = 1501) -> Img:
    """Fresh snow, 64 x 64 and periodic: an even sunlit white (step 5) with a faint grain of cool pixels, broad soft
    swells a step lit where they face the north-west, and small wind crescents on a jittered grid, each a lit lip over a
    px or two of blue lee shade to its south-east; a few stones under the snow, each a low mound lit on top with its blue
    shadow; a sparse sparkle of single glints, a few warmed by the sun. No shaded area bigger than a crescent, so the
    field stays calm and never shows its period."""
    img = Img(P, P)
    for y in range(P):
        for x in range(P):
            k = 5
            g = hp(x, y, seed + 2)
            if g < 0.035:
                k = 4
            col = SNOW2[k]
            if g > 0.994:
                col = SNOW2[6] if hp(x, y, seed + 7) < 0.7 else mix(SNOW2[6], SUN, 0.5)
            img.put(x, y, col)
    # the glints: a grain catching the sun, its facet's shade a px to the south-east so it reads on the white
    for y in range(P):
        for x in range(P):
            if hp(x, y, seed + 2) > 0.994:
                img.put((x + 1) % P, (y + 1) % P, SNOW2[4])
    for gy in range(P // 8):
        for gx in range(P // 8):
            if h01(gx, gy, seed + 3) < 0.6:
                continue
            x0 = gx * 8 + int(h01(gx, gy, seed + 4) * 6)
            y0 = gy * 8 + int(h01(gx, gy, seed + 5) * 6)
            w = 3 + int(h01(gx, gy, seed + 6) * 3)
            bend = -1 if h01(gx, gy, seed + 8) < 0.3 else 1 if h01(gx, gy, seed + 8) > 0.7 else 0
            for i in range(w):
                X = (x0 + i) % P
                Y = y0 + (bend if (i == 0 and bend < 0) or (i == w - 1 and bend > 0) else 0)
                if 0 < i < w - 1:
                    img.put(X, Y % P, SNOW2[6])
                img.put(X, (Y + 1) % P, SNOW2[4])
    for gy in range(4):
        for gx in range(4):
            if h01(gx, gy, seed + 13) < 0.7:
                continue
            cx, cy = gx * 16 + 4 + int(h01(gx, gy, seed + 14) * 8), gy * 16 + 4 + int(h01(gx, gy, seed + 15) * 8)
            rx = 2 + int(h01(gx, gy, seed + 16) * 2)
            for j in range(-2, 3):
                for i in range(-rx - 1, rx + 2):
                    d = (i / (rx + 0.5)) ** 2 + (j / 1.8) ** 2
                    X, Y = (cx + i) % P, (cy + j) % P
                    if d <= 1.0:
                        img.put(X, Y, SNOW2[6] if (j < 0 and i <= 0) else SNOW2[5] if j <= 0 else SNOW2[4])
                    elif d <= 1.7 and j >= 1 and i > -rx:
                        img.put(X, Y, SNOW2[4] if i < rx else SNOW2[3])
    return img


def snowpack_macro(seed: int = 1601) -> Img:
    """Packed snow, 64 x 64: trodden two steps down the ramp (step 4, a little of 3 and 5 in soft mottling), trails of
    prints pressed into it (pairs of hollows, each with its north end in shade and its south lip lit) crossing the
    pattern and wrapping, a few loose prints between them, streaks glazed to ice that catch the sun, and a speck of
    earth kicked up now and then."""
    img = Img(P, P)
    for y in range(P):
        for x in range(P):
            k = 4
            h = hp(x, y, seed + 1)
            if h < 0.06:
                k = 3
            elif h > 0.95:
                k = 5
            g = hp(x, y, seed + 2)
            col = SNOW2[k]
            if g < 0.003:
                col = mix(SNOW2[3], DIRT2[3], 0.5)
            img.put(x, y, col)

    def printed(x: int, y: int) -> None:
        for (i, j), c in (((0, 0), SNOW2[3]), ((1, 0), SNOW2[3]), ((0, 1), SNOW2[3]), ((1, 1), SNOW2[4]),
                          ((0, 2), SNOW2[5]), ((1, 2), SNOW2[5])):
            img.put((x + i) % P, (y + j) % P, c)

    for tr in range(3):
        x = int(h01(tr, 1, seed + 3) * P)
        dx = (h01(tr, 2, seed + 3) - 0.5) * 0.5
        for st in range(P // 5):
            y = st * 5
            side = 2 if st % 2 else -1
            printed(int(x + dx * y) + side, y + int(h01(st, tr, seed + 4) * 2))
    for n in range(10):
        printed(int(h01(n, 5, seed + 3) * P), int(h01(n, 6, seed + 3) * P))
    for n in range(5):
        x, y = int(h01(n, 1, seed + 6) * P), int(h01(n, 2, seed + 6) * P)
        for s in range(3 + int(h01(n, 3, seed + 6) * 4)):
            img.put((x + s) % P, y, SNOW2[6] if s % 3 else mix(SNOW2[6], SUN, 0.3))
    return img


def d_snow_stalks(seed: int) -> Img:
    """Dry grass stalks poking up through the snow: straw-pale blades lit on top, each with a cold shadow and a small
    hollow melted round its foot."""
    t = Img(T, T)
    for k in range(2 + int(h01(1, 1, seed) * 2)):
        x, y = 3 + int(h01(k, 2, seed) * 9), 6 + int(h01(k, 3, seed) * 7)
        for s in range(2 + int(h01(k, 4, seed) * 3)):
            lean = 1 if (s > 1 and h01(k, 5, seed) < 0.5) else 0
            t.put(x + lean, y - s, REED[4] if s == 0 else REED[3] if s % 2 else REED[4])
        t.put(x - 1, y + 1, SNOW2[3])
        t.put(x, y + 1, SNOW2[4])
        _shadow_px(t, x + 1, y, 70)
        _shadow_px(t, x + 1, y + 1, 50)
    return t


def d_snow_tracks(seed: int, hare: bool = False) -> Img:
    """Prints in the snow crossing the tile: a bird's three toes, or a hare's bounding four (two long, two small); each
    a hollow, its north wall in cold shade and its south lip lit."""
    t = Img(T, T)
    x, y = 3 + int(h01(2, 1, seed) * 3), 2 + int(h01(2, 2, seed) * 2)
    for s in range(3 if hare else 4):
        if hare:
            for i, j in ((0, 0), (0, 1), (3, 0), (3, 1), (1, 3), (2, 4)):
                t.put(x + i, y + j, SNOW2[3])
            t.put(x, y + 2, SNOW2[6])
            t.put(x + 3, y + 2, SNOW2[6])
            x += 3
            y += 4
        else:
            for i, j in ((0, 0), (-1, -1), (1, -1), (0, -2)):
                t.put(x + i + 1, y + j + 2, SNOW2[3])
            t.put(x + 1, y + 3, SNOW2[6])
            x += 3
            y += 3
    return t


def d_snow_mound(seed: int) -> Img:
    """A buried stone or tussock: a round mound lit on its north-west, cold on its south-east, its blue shadow on the
    snow; now and then the stone's dark shows at its lee."""
    t = Img(T, T)
    rx, ry = 2.5 + h01(3, 1, seed) * 2.0, 1.8 + h01(3, 2, seed) * 1.0
    cx, cy = 3 + rx + h01(3, 3, seed) * (9 - 2 * rx), 3 + ry + h01(3, 4, seed) * (9 - 2 * ry)
    pts = []
    for j in range(T):
        for i in range(T):
            dx, dy = (i + 0.5 - cx) / rx, (j + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0 and 1 <= i < T - 1 and 1 <= j < T - 1:
                pts.append((i, j, dx, dy))
    for i, j, dx, dy in pts:
        c = SNOW2[5]
        if dx + dy < -0.55:
            c = SNOW2[6]
        elif dx + dy > 0.7:
            c = SNOW2[4]
        t.put(i, j, c)
    if h01(3, 5, seed) < 0.5 and pts:
        i, j, _, _ = max(pts, key=lambda q: q[2] + q[3])
        t.put(i, j, ROCK2[2])
    cast_shadow(t, ((1, 1, 90), (0, 1, 70), (1, 0, 40), (2, 1, 40)))
    return t


def d_twig_snow(seed: int) -> Img:
    """A dark twig lying on the snow, a line of snow along its top."""
    t = Img(T, T)
    x, y = 3 + int(h01(4, 1, seed) * 5), 5 + int(h01(4, 2, seed) * 7)
    for s in range(6 + int(h01(4, 3, seed) * 3)):
        yy = y + s // 4
        t.put(x + s, yy, WOOD2[2] if s % 3 else WOOD2[1])
        if s % 2 == 0:
            t.put(x + s, yy - 1, SNOW2[6])
    t.put(x + 3, y + 1, WOOD2[2])
    cast_shadow(t, ((1, 1, 70), (0, 1, 50)))
    return t


def d_sparkle(seed: int, n: int = 2) -> Img:
    """The snow's sparkle where the sun catches a crystal: a few tiny four-point glints (a warm white heart, cool arms)
    and single bright grains between them."""
    t = Img(T, T)
    for k in range(n):
        x, y = 3 + int(h01(k, 1, seed) * 10), 3 + int(h01(k, 2, seed) * 10)
        t.put(x, y, mix(SNOW2[6], SUN, 0.4))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t.put(x + dx, y + dy, SNOW2[6])
        t.put(x + 1, y + 1, SNOW2[4])
    for k in range(3):
        x, y = 1 + int(h01(k, 3, seed) * 14), 1 + int(h01(k, 4, seed) * 14)
        if t.get(x, y)[3] == 0:
            t.put(x, y, SNOW2[6])
    return t


def snow_decals() -> list:
    return [d_snow_stalks(1700), d_snow_stalks(1701), d_snow_stalks(1702), d_snow_tracks(1703), d_snow_tracks(1704, True),
            d_snow_mound(1705), d_snow_mound(1706), d_snow_mound(1707), d_twig_snow(1708), d_sparkle(1709, 1),
            d_sparkle(1710, 2), d_sparkle(1711, 1)]


def snowpack_decals() -> list:
    return [d_snow_tracks(1720), d_snow_tracks(1721, True), d_stones(1722, 2, DIRT2), d_stones(1723, 1, ROCK2),
            d_twig_snow(1724)]


def snow_faces(seed: int = 901) -> tuple:
    """The karst cliff (terrain2.rock_face_tex, so a snowy face joins a bare one column for column) with snow on its
    ledges where the bare rock has moss, the snow's lip over its first row (lumps lit on top and cold underneath, their
    contact shadow), and icicles hanging from the lip."""
    tex = rock_face_tex(seed)
    swap = {MOSS2[5]: SNOW2[6], MOSS2[4]: SNOW2[5], MOSS2[3]: SNOW2[4], MOSS2[2]: SNOW2[3]}
    for y in range(tex.h):
        for x in range(tex.w):
            c = tex.get(x, y)
            if c in swap:
                tex.put(x, y, swap[c])
    pat = _face_pattern(tex)
    _drip(pat, SNOW2, SNOW2, seed + 60, 4, False, 2, 0.08)
    for x in range(P):
        low = max((y for y in range(2, 9) if pat.get(x, y) in (SNOW2[2], SNOW2[3], SNOW2[4], SNOW2[5])), default=0)
        if low and hp(x, 7, seed + 61, P, 16) < 0.14:
            n = 2 + int(hp(x, 8, seed + 61, P, 16) * 4)
            for s in range(1, n + 1):
                pat.put(x, low + s, SNOW2[6] if s == n else SNOW2[5] if s < n - 1 else SNOW2[4])
    return face_tiles(pat)


def face_join(top: Img, side: str, col: int, seed: int = 1801) -> Img:
    """A face's first row (`top`, its tile at column `col` of the 64 px pattern) running into the neighbouring cell's
    face from its `side` ('w': it enters at the west edge): the face's own pixels up to a boundary that wanders 2-7 px
    in from the edge, down the rows in soft lobes, so where the grassy bank meets a beach (or a beach the embankment,
    or the snow's lip the bare rock's) the lip changes at no straight seam."""
    t = Img(T, T)
    for j in range(T):
        n = pn(col * T + (0 if side == "w" else T // 2), j, seed, 4, P, T)
        b = 2 + int(n * 6)
        for i in range(T):
            if (i < b) if side == "w" else (i >= T - b):
                t.put(i, j, top.get(i, j))
    return t


# ====================================================================================================== creeping
def lumps(x: int, y: int, seed: int, cell: int = 8, r: float = 4.5) -> float:
    """Round lumps, periodic in 64 px: 1 at a jittered site (one to each 8 x 8 block), falling to 0 at `r` px from it.
    Added to a creeping edge's field it bulges the edge round each site, so the edge runs in soft lobes rather than
    the long straight runs a value noise leaves where it flattens out."""
    n = P // cell
    a0, b0 = x // cell, y // cell
    best = 99.0
    for db in (-1, 0, 1):
        for da in (-1, 0, 1):
            a, b = a0 + da, b0 + db
            sx = a * cell + h01(a % n, b % n, seed) * cell
            sy = b * cell + h01(a % n, b % n, seed + 1) * cell
            best = min(best, math.hypot(x + 0.5 - sx, y + 0.5 - sy))
    return max(0.0, 1.0 - best / r)


def creep_over(kind: str, corners: tuple, pos: tuple, mac: Img, seed: int) -> Img:
    """Sand, snow or packed snow over its neighbour on the same level, per corner case and place in the 64 px pattern
    (as the grass overlay): the material's own pattern where the corner field, noise periodic in 64 px and round lumps
    say so. Sand is a thin drift about a third of the way in: its sunny edge a step lit, its lee a step down, loose
    grains past it, the faintest shadow. Snow has body, half the way in: its sunny edge glints (packed snow's is a step
    lit), its front is in cold shade with a two-step `SHADOW` on the ground below and east of it (lighter under packed
    snow, which is trodden low), and a dusting of flakes lies past the edge."""
    ox, oy = pos[0] * T, pos[1] * T
    snow = kind in ("snow", "snowpack")
    packed = kind == "snowpack"
    amp = 1.2 if snow else 1.5
    cells, wts = ((16, 8, 4), (0.42, 0.34, 0.24)) if snow else ((16, 8, 4), (0.42, 0.36, 0.22))
    bump = 0.34 if snow else 0.3           # the lobes along the edge: round for snow, lower for sand
    R = range(-4, T + 4)
    cov = {}
    for j in R:
        for i in R:
            n = fbm(ox + i, oy + j, seed, cells, wts)
            f = corner_field(corners, i, j) + amp * (n - 0.5) + bump * (lumps(ox + i, oy + j, seed + 7) - 0.3)
            cov[(i, j)] = f > (0.5 if snow else 0.58)     # sand drifts a third of the way in; snow half

    def near(i: int, j: int, d: int) -> bool:
        return any(cov.get((i + a, j + b), False) for a in range(-d, d + 1) for b in range(-d, d + 1))

    ramp = SNOW2 if snow else SAND2
    t = Img(T, T)
    for j in range(T):
        for i in range(T):
            X, Y = ox + i, oy + j
            if cov[(i, j)]:
                col = mac.get(X % P, Y % P)
                if not cov[(i, j - 1)] or not cov[(i - 1, j)]:
                    col = ramp[6] if snow and not packed else ramp[5]
                elif not cov[(i, j + 1)]:
                    col = ramp[3]
                elif not cov[(i + 1, j)] or (snow and not cov[(i, j + 2)]):
                    col = ramp[4] if snow else ramp[3]
                t.put(i, j, col)
                continue
            h = hp(X, Y, seed + 1)
            if near(i, j, 1) and h < (0.2 if snow else 0.24):
                t.put(i, j, ramp[5] if snow else ramp[4])
                continue
            if near(i, j, 2) and h < (0.07 if snow else 0.08):
                t.put(i, j, ramp[5] if snow else ramp[4])
                continue
            a = 0
            if snow:                           # packed snow is trodden low: its shadow is the lighter
                if cov[(i, j - 1)]:
                    a = 64 if packed else 104
                elif cov[(i, j - 2)]:
                    a = 32 if packed else 52
                if cov[(i - 1, j)] or cov[(i - 1, j - 1)]:
                    a = max(a, 40 if packed else 64)
            elif cov[(i, j - 1)]:
                a = 36
            if a:
                t.put(i, j, alpha(SHADOW, a))
    return t
