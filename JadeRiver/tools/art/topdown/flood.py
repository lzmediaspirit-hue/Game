"""R2 (docs/architecture/room_engine.md, "The Drowned Shrine and Whitewater Gorge"): shallow water lying over a floor a
body wades through, drawn to Terrain v2's rules (terrain2.py) and lit by its sun, high in the north-west.

The paint marks that flood (`q` flagstones under the water, the Drowned Shrine's halls; `h` a river's pebbled bed, the
Serpent's Shallows and the grottoes) draw their own floor, then this overlay over it: clear water a few fingers deep, the floor showing
through, tinted blue-green and darker where a slow noise says it lies deeper, with a few lit ripple dashes and a glint.
Where the flooded floor meets dry floor its edge wanders in soft lobes (noise periodic in 64 px and round lumps, as
sand creeps), the water's edge a px lit on the sunny side, a px of pale water on the other, and a damp line on the dry
floor beyond it. Per corner case (TL TR BL BR, 1 = every cell round the corner flooded or open water) and place in the
64 px pattern, as the grass overlay; TopdownTerrain lays it over a flooded cell's top.

Everything comes from a coordinate hash, never a random generator, so the build is byte-identical.
"""
from __future__ import annotations

from canvas import T, Img
from palette import FOAM2, SHADOW, WATER2, alpha
from sand_snow import lumps
from terrain2 import corner_field, fbm, hp

SEED = 1701


def flood_over(corners: tuple, pos: tuple, seed: int = SEED) -> Img:
    """The water over a flooded floor for one corner case and place (see the module's docstring)."""
    ox, oy = pos[0] * T, pos[1] * T
    full = corners == (1, 1, 1, 1)
    R = range(-3, T + 3)
    cov = {}
    for j in R:
        for i in R:
            if full:
                cov[(i, j)] = True
                continue
            n = fbm(ox + i, oy + j, seed, (16, 8), (0.6, 0.4))
            f = corner_field(corners, i, j) + 1.1 * (n - 0.5) + 0.3 * (lumps(ox + i, oy + j, seed + 7) - 0.3)
            cov[(i, j)] = f > 0.55
    t = Img(T, T)
    for j in range(T):
        for i in range(T):
            X, Y = ox + i, oy + j
            if cov[(i, j)]:
                # The water's edge: lit where the dry floor lies north or west of it, pale on the other sides.
                if not cov[(i, j - 1)] or not cov[(i - 1, j)]:
                    t.put(i, j, alpha(FOAM2, 170))
                    continue
                if not cov[(i, j + 1)] or not cov[(i + 1, j)]:
                    t.put(i, j, alpha(WATER2[6], 150))
                    continue
                if not cov[(i, j - 2)] or not cov[(i - 2, j)]:
                    t.put(i, j, alpha(WATER2[5], 120))
                    continue
                # The body of the water: its tint, deeper where a slow noise lies low, and a lit ripple now and then
                # (short east-west dashes, as on the open water) and a rare glint.
                d = fbm(X, Y, seed + 3, (32, 16), (0.6, 0.4))
                col, a = (WATER2[4], 112) if d > 0.42 else (WATER2[3], 128)
                if d > 0.62:
                    col, a = WATER2[5], 100
                if hp(X // 4, Y, seed + 5, 16, 64) < 0.03 and hp(X, Y, seed + 6) < 0.85:
                    col, a = WATER2[6], 150
                elif hp(X, Y, seed + 8) < 0.006:
                    col, a = FOAM2, 190
                t.put(i, j, alpha(col, a))
                continue
            # The dry floor by the water: a damp line along it.
            if cov[(i, j + 1)] or cov[(i + 1, j)] or cov[(i - 1, j)] or cov[(i, j - 1)]:
                t.put(i, j, alpha(SHADOW, 56))
    return t
