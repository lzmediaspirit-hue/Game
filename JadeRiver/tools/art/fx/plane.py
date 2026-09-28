"""The top-down ground plane for the FX sheets (decision 38): how a point on the floor, at a height over it, lands on
an FX canvas in the world's 1:1 oblique 3/4 view (docs/redesign_top_down_plan.md §1.1: screen = (x, y - z), a floor
top is a square, a height is drawn straight up).

A drawer works in the effect's own frame: `f` forward along its direction, `l` to its right (clockwise on screen), `h`
up. Plane turns that frame to one of the five drawn directions (DIRS: E, SE, S, NE, N, as the body's sheets draw them)
and projects it, so every direction is rasterised on its own pixel grid, never a rotated sprite. The west three mirror
the east three (MIRROR), as the body and the foes do.
"""
from __future__ import annotations

import math

from fxpix import HAZE, STROKE_BANDS, Canvas

# The five drawn directions and their angle on the floor (radians, y down: E 0, S +90 degrees). W, SW and NW mirror.
DIRS = ["e", "se", "s", "ne", "n"]
ANGLE = {"e": 0.0, "se": math.pi / 4, "s": math.pi / 2, "ne": -math.pi / 4, "n": -math.pi / 2}
MIRROR = {"w": "e", "sw": "se", "nw": "ne"}


class Plane:
    """The effect's frame on a canvas: its anchor (a point on the floor) at (ax, ay), facing `d` (one of DIRS)."""

    def __init__(self, cv: Canvas, ax: float, ay: float, d: str = "e"):
        self.cv = cv
        self.ax, self.ay = ax, ay
        self.th = ANGLE[d]
        self.c, self.s = math.cos(self.th), math.sin(self.th)

    # ---------------------------------------------------------------- projection
    def pt(self, f: float, l: float = 0.0, h: float = 0.0) -> tuple:
        """Canvas point of forward `f`, right `l`, height `h`."""
        return (self.ax + f * self.c - l * self.s, self.ay + f * self.s + l * self.c - h)

    def ground_dir(self, f: float, l: float) -> tuple:
        """A direction on the floor, turned into canvas axes (for particles and normals)."""
        return (f * self.c - l * self.s, f * self.s + l * self.c)

    def ang(self, a: float) -> float:
        """A floor angle measured from the forward (clockwise positive) as a canvas angle."""
        return self.th + a

    # ---------------------------------------------------------------- 3D paths
    def arc(self, r: float, a0: float, a1: float, h: float = 0.0, tilt: float = 0.0, n: int = 16, f0: float = 0.0,
            l0: float = 0.0, lift: float = 0.0) -> list:
        """Points of an arc of radius r round (f0, l0) at height h, from angle a0 to a1 (0 = forward, clockwise), its
        plane tipped by `tilt` round the forward axis: the right side rises by sin(tilt) (a rising cut), the arc stands
        upright at tilt = pi/2 (an overhead chop). `lift` raises the arc's far end (a scoop)."""
        out = []
        for i in range(n):
            u = i / max(1, n - 1)
            a = a0 + (a1 - a0) * u
            f, l = r * math.cos(a), r * math.sin(a)
            out.append(self.pt(f0 + f, l0 + l * math.cos(tilt), h + l * math.sin(tilt) + lift * u))
        return out

    def line(self, f0: float, f1: float, l: float = 0.0, h: float = 0.0, n: int = 8, h1: float | None = None) -> list:
        h1 = h if h1 is None else h1
        return [self.pt(f0 + (f1 - f0) * i / max(1, n - 1), l, h + (h1 - h) * i / max(1, n - 1)) for i in range(n)]

    # ---------------------------------------------------------------- strokes
    def stroke(self, pts: list, w0: float, w1: float, table=STROKE_BANDS, mode: str = "over") -> None:
        if len(pts) >= 2:
            self.cv.stroke_poly(pts, w0, w1, table, mode)

    def sweep_haze(self, pts: list, centre: tuple, width: float, mode: str = "under") -> None:
        """The swept band behind a fast stroke: the polygon between the path and the path pulled `width` toward the
        centre, in the half-there haze (the smear of a blade's passage)."""
        if len(pts) < 2:
            return
        cx, cy = centre
        inner = []
        for x, y in pts:
            dx, dy = cx - x, cy - y
            d = math.hypot(dx, dy) or 1.0
            k = min(width, d) / d
            inner.append((x + dx * k, y + dy * k))
        self.cv.paint(self.cv.mask_polygon(pts + inner[::-1]), HAZE, mode)

    def ring(self, r: float, w: float, idx: int, h: float = 0.0, f0: float = 0.0, l0: float = 0.0, a0: float = 0.0,
             a1: float = 2 * math.pi) -> None:
        """A ring on the floor (a circle on screen: the floor is not squashed) round (f0, l0) at height h."""
        x, y = self.pt(f0, l0, h)
        if a1 - a0 >= 2 * math.pi - 1e-6:
            self.cv.ring(x, y, r, w, idx)
        else:
            self.cv.ring(x, y, r, w, idx, a0=self.ang(a0), a1=self.ang(a1))

    def outward(self, pts: list, centre: tuple) -> list:
        """Sample points with their outward unit normal from `centre` (for elements.dress_edge and fling)."""
        out = []
        cx, cy = centre
        for x, y in pts:
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) or 1.0
            out.append((x, y, dx / d, dy / d))
        return out

    def side(self, pts: list, sign: float = 1.0) -> list:
        """Sample points with the normal to the right (sign 1) or left (-1) of the direction of travel along them."""
        out = []
        for i, (x, y) in enumerate(pts):
            x2, y2 = pts[min(i + 1, len(pts) - 1)]
            x1, y1 = pts[max(i - 1, 0)]
            dx, dy = x2 - x1, y2 - y1
            d = math.hypot(dx, dy) or 1.0
            out.append((x, y, -dy / d * sign, dx / d * sign))
        return out
