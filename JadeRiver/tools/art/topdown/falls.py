"""R2 (docs/architecture/room_engine.md, "The Drowned Shrine and Whitewater Gorge"): a waterfall for the prop kit,
drawn at art resolution, lit from the upper left.

`waterfall`: a fall three cells wide pouring over a cliff four levels high into the water at its foot. It stands on the
water cells under the cliff (its footprint, 3 x 1; nothing stands there), its sprite rising over the cliff's face to
the lip it curls over: the lip a band of pale water bending over the edge, the sheet below it streaked with falling
water (each column its own streaks, a little faster in the middle, darker at the sheet's sides where it thins), and at
its foot a churn of foam and spray over the pool. Four frames: the streaks fall a quarter of their period each frame,
the spray rises and settles, so the fall runs on the water's clock.
"""
from __future__ import annotations

from canvas import Img, h01
from palette import FOAM2, WATER2, alpha

W, H = 48, 100
FOOT = 98        # the footprint's south-west corner in the sprite (the pool's south edge under the fall)
LIP = 2          # the lip's first row: the cliff's top edge (four levels over the pool's row, 16 px a level)
SHEET = (4, 44)  # the sheet's columns (x0, x1)
POOL = 84        # where the sheet meets the pool


def waterfall(s: Img, f: int = 0) -> None:
    """The waterfall in frame `f` (see the module's docstring)."""
    for y in range(LIP, POOL):
        fan = (y - LIP) // 30                      # the sheet spreads a px each side as it falls
        x0, x1 = SHEET[0] - fan, SHEET[1] + fan
        for x in range(x0, x1):
            edge = min(x - x0, x1 - 1 - x)
            period = 12 + int(h01(x, 1, 41) * 9)
            length = 4 + int(h01(x, 2, 41) * 6)
            speed = period // 4 + (1 if edge > 8 else 0)
            phase = int(h01(x, 3, 41) * period)
            top = LIP + (1 if edge < 2 else 0)
            if y < top:
                continue
            base = WATER2[5] if edge > 6 else WATER2[4] if edge > 1 else WATER2[3]
            if y < LIP + 4:   # the lip: pale water bending over the edge, its crest lit
                base = FOAM2 if y == top and edge > 1 else WATER2[7] if y == top + 1 else WATER2[6]
            elif (y - phase - f * speed) % period < length:
                k = h01(x, (y - f * speed) // period, 43)
                base = FOAM2 if edge > 5 and k < 0.3 else WATER2[7] if k < 0.75 else WATER2[6]
            elif edge == 0:
                base = WATER2[2]
            s.put(x, y, base)
    # The churn at its foot: foam over the pool, brighter in the middle, ragged at its ends.
    for y in range(POOL - 3, FOOT - 2):
        for x in range(0, W):
            cx, cy = W / 2.0, POOL + 3.0
            d = ((x + 0.5 - cx) / 24.0) ** 2 + ((y + 0.5 - cy) / 8.0) ** 2
            r = h01(x, y + f, 45)
            if d < 0.45 or (d < 1.0 and r < 0.6 - (d - 0.45)):
                s.put(x, y, FOAM2 if r < 0.55 or d < 0.2 else WATER2[7])
            elif d < 1.3 and r < 0.18:
                s.put(x, y, alpha(FOAM2, 150))
    # The spray: drops thrown up from the churn, rising one frame and falling the next.
    for k in range(14):
        x = 2 + int(h01(k, f, 46) * (W - 4))
        y = POOL - 2 - int(h01(k, f + 7, 46) * 9)
        s.put(x, y, alpha(FOAM2, 210))
        if k % 3 == 0:
            s.put(x + 1, y + 1, alpha(FOAM2, 120))


# kind: (draw, w, h, footprint w, h, origin, solid, shadow) as tools/art/topdown/props.py's PROPS
PROPS = {"waterfall": (waterfall, W, H, 3, 1, [0, FOOT], False, None)}
ANIM = {"waterfall": (4, 250)}   # on the water's clock
