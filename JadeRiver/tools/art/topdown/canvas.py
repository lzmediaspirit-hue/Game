"""Small raster helpers shared by the top-down tile, prop and review builders.

Everything is integer pixel work on RGBA PIL images at native art resolution (1 art px = 1 px of the 640x360 world
viewport). Noise comes from a coordinate hash, never from a random generator, so every build is byte-identical.
"""
from __future__ import annotations

import os
import sys

from PIL import Image

from palette import CLEAR, LINE, LINE_SOFT

T = 16
# h01(x, y, s): a hash of integer coordinates to [0, 1). vnoise(i, j, seed, cx=4, cy=None, period=T): value noise on a
# lattice of cx x cy px that repeats every `period` px, so a tile built from it tiles.
# The coordinate hash and the tileable noise are the one pixel library's (tools/lib/pix.py, audit 45): the same code, one copy.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from lib.pix import h01, vnoise  # noqa: E402,F401


class Img:
    """An RGBA image with clipped pixel writes and a few shape helpers."""

    def __init__(self, w: int, h: int, fill=CLEAR):
        self.img = Image.new("RGBA", (w, h), fill)
        self.px = self.img.load()
        self.w, self.h = w, h

    @staticmethod
    def wrap(img: Image.Image) -> "Img":
        o = Img.__new__(Img)
        o.img, o.px, o.w, o.h = img, img.load(), img.width, img.height
        return o

    def put(self, x: int, y: int, col) -> None:
        if col is not None and 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = col

    def get(self, x: int, y: int):
        return self.px[x, y] if 0 <= x < self.w and 0 <= y < self.h else CLEAR

    def blend(self, x: int, y: int, col, a: int) -> None:
        """Lay `col` over the pixel at opacity a/255 (keeps the pixel's own alpha)."""
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        r, g, b, pa = self.px[x, y]
        if pa == 0:
            return
        k = a / 255.0
        self.px[x, y] = (round(r + (col[0] - r) * k), round(g + (col[1] - g) * k), round(b + (col[2] - b) * k), pa)

    def rect(self, x: int, y: int, w: int, h: int, col) -> None:
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.put(i, j, col)

    def hline(self, x: int, y: int, w: int, col) -> None:
        self.rect(x, y, w, 1, col)

    def vline(self, x: int, y: int, h: int, col) -> None:
        self.rect(x, y, 1, h, col)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, col, shade=None) -> None:
        """A filled ellipse; with `shade` = (lit, dark) it lights the upper-left rim and darkens the lower-right."""
        for j in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for i in range(int(cx - rx) - 1, int(cx + rx) + 2):
                dx, dy = (i + 0.5 - cx) / rx, (j + 0.5 - cy) / ry
                d = dx * dx + dy * dy
                if d > 1.0:
                    continue
                c = col
                if shade is not None:
                    if d > 0.55 and dx + dy < -0.5:
                        c = shade[0]
                    elif d > 0.45 and dx + dy > 0.6:
                        c = shade[1]
                self.put(i, j, c)

    def paste(self, src: "Img | Image.Image", x: int, y: int) -> None:
        im = src.img if isinstance(src, Img) else src
        self.img.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 else self._paste_clip(im, x, y)

    def _paste_clip(self, im: Image.Image, x: int, y: int) -> None:
        l, t = max(0, -x), max(0, -y)
        if l >= im.width or t >= im.height:
            return
        self.img.alpha_composite(im.crop((l, t, im.width, im.height)), (x + l, y + t))

    def outline(self, x0: int = 0, y0: int = 0, w: int | None = None, h: int | None = None) -> None:
        """The prop outline (art bible §4): a 1 px line on transparent pixels next to the shape. Pixels whose shape lies
        to their lower right (the lit, upper-left side) take the softer line; the rest take the dark ink-teal."""
        w = self.w - x0 if w is None else w
        h = self.h - y0 if h is None else h
        solid = [[self.px[x0 + i, y0 + j][3] > 0 for i in range(w)] for j in range(h)]

        def s(i: int, j: int) -> bool:
            return 0 <= i < w and 0 <= j < h and solid[j][i]

        for j in range(h):
            for i in range(w):
                if solid[j][i]:
                    continue
                right, down, left, up = s(i + 1, j), s(i, j + 1), s(i - 1, j), s(i, j - 1)
                if not (right or down or left or up):
                    continue
                lit = (right or down) and not (left or up)
                self.put(x0 + i, y0 + j, LINE_SOFT if lit else LINE)

    def save(self, path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(path, optimize=False)


def tile() -> Img:
    return Img(T, T)
