"""A reference renderer for top-down rooms: draws a room from its `topdown` data (docs/redesign_top_down_plan.md,
"As built: Phase 1") with the atlas, the auto-tile rules and the light overlays of the art bible.

It draws in the Phase 1 view's order (topdown_world.gd): water 8 px low, the ground floor, then one list sorted by
key (raised rows at their south edge, stairs at the flight's south edge, props at the footprint's south edge + 0.5,
bodies at their ground y), and adds what the loader does not do yet: shore and path auto-tiles, rims, contact shade,
cast shade and prop shadows. It is the rule book in code for the loader work of Phase 4, and it renders the review
images in docs/redesign/phase3/.
"""
from __future__ import annotations

from PIL import Image

from canvas import T, Img
from palette import NIGHT, SHADE, alpha

WATER = -1
# The paint table, in the manifest's schema (TopdownWorld.top_tile / face_tile read it): the tops a mark draws (the
# Phase 1-2 loader picks between the first two per cell, this renderer among all), its face kind, and `keep_face` for a
# mark whose face stays its own over water (a pier's pilings).
PAINT = {
    "g": {"top": ["grass_a", "grass_b", "grass_a", "grass_c", "grass_d"], "face": "earth"},
    "f": {"top": ["grass_flowers"], "face": "earth"},
    "d": {"top": ["dirt", "dirt_b"], "face": "earth"},
    "p": {"top": ["paving_a", "paving_b", "paving_a", "paving_c", "paving_b", "paving_a", "paving_d"], "face": "pave"},
    "s": {"top": ["stone_top", "stone_top", "stone_top_b"], "face": "stone"},
    "w": {"top": ["wood", "wood_b"], "face": "wood", "keep_face": True},
    "r": {"top": ["rock", "rock_b"], "face": "rock"},
    "t": {"top": ["roof_top", "roof_top_b"], "face": "roof"},
    "l": {"top": ["wall_top"], "face": "wall"},
}
GRASSY = "gf"
UNDER = {"d": "grass_dirt", "p": "grass_paving"}


class Room:
    def __init__(self, d: dict):
        self.levels = [[WATER if ch == "~" else int(ch) for ch in row] for row in d["levels"]]
        self.paint = [list(row) for row in d["paint"]]
        self.h, self.w = len(self.levels), len(self.levels[0])
        self.stairs = [dict(s) for s in d.get("stairs", [])]
        self.props = [dict(p) for p in d.get("props", [])]

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def lv(self, x: int, y: int, out: int = 99) -> int:
        return self.levels[y][x] if self.inside(x, y) else out

    def pt(self, x: int, y: int) -> str:
        return self.paint[y][x] if self.inside(x, y) else ""

    def stair_at(self, x: int, y: int):
        for s in self.stairs:
            if s["x"] <= x < s["x"] + s["w"] and s["y"] <= y < s["y"] + s["h"]:
                return s
        return None

    def edge_level(self, x: int, y: int) -> int:
        """The level the cell shows at the edge north of it (a stair's height where it meets it)."""
        if not self.inside(x, y):
            return 99
        s = self.stair_at(x, y)
        if s is not None:
            k = (s["y"] + s["h"] - y) / s["h"]
            return int(s["from"] + (s["to"] - s["from"]) * k + 0.01)
        return self.levels[y][x]


class Atlas:
    def __init__(self, sheet: Img, at: dict, auto: dict, props_sheet: Img, props: dict):
        self.sheet, self.at, self.auto, self.psheet, self.props = sheet, at, auto, props_sheet, props
        self._cache: dict = {}

    def tile(self, name: str, h: int | None = None) -> Image.Image:
        key = (name, h)
        if key not in self._cache:
            x, y, w, hh = self.at[name]
            self._cache[key] = self.sheet.img.crop((x, y, x + w, y + (h or hh)))
        return self._cache[key]

    def prop(self, kind: str) -> Image.Image:
        x, y, w, h = self.props[kind]["rect"]
        return self.psheet.img.crop((x, y, x + w, y + h))


def top_name(room: Room, x: int, y: int) -> str:
    """The top tile of a cell (art bible §6). Grass creeps over the edge of a path or paving on the same level: a path
    cell's corner is grass when any cell sharing that corner is grass. Otherwise a fixed per-cell variant."""
    p = room.pt(x, y)
    lvl = room.lv(x, y)
    if p in UNDER:
        corners = []
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            g = 0
            for ox in (dx - 1, dx):
                for oy in (dy - 1, dy):
                    if room.pt(x + ox, y + oy) in GRASSY and room.lv(x + ox, y + oy) == lvl:
                        g = 1
            corners.append(g)
        if any(corners):
            return room_auto[UNDER[p]]["".join(map(str, corners))]
    names = PAINT.get(p, PAINT["g"])["top"]
    return names[(x * 7 + y * 13 + (x * y) % 5) % len(names)]


room_auto: dict = {}


def face_name(room: Room, x: int, y: int, first: bool, over_water: bool) -> str:
    paint = PAINT.get(room.pt(x, y), {})
    kind = paint.get("face", "stone")
    if over_water and not paint.get("keep_face", False):
        kind = "bank"
    if kind == "roof" and not first:
        return "roof_face" if (x % 3) else "plaster_face_window"
    return kind + ("_face_top" if first else "_face")


def shore_sides(room: Room, x: int, y: int) -> int:
    bits = 0
    for bit, (dx, dy) in ((1, (0, -1)), (2, (1, 0)), (4, (0, 1)), (8, (-1, 0))):
        if room.inside(x + dx, y + dy) and room.lv(x + dx, y + dy) != WATER:
            bits |= bit
    return bits


def render(d: dict, atlas: Atlas, frame: int = 0, bodies: list | None = None, dressing: list | None = None,
           figure=None, pad: int = 0) -> Img:
    """The whole room at art resolution, `pad` art px taller at the top so raised levels on the north rows show.
    `bodies` are (cell x, cell y as floats, facing, anim, frame) standing on the
    floor under them, drawn by `figure(facing, anim, frame) -> (image, feet)`; `dressing` adds props for a review without touching the room's data."""
    global room_auto
    room_auto = atlas.auto
    room = Room(d)
    if dressing:
        room.props += dressing
    W, H = room.w * T, room.h * T
    out = Shifted(W, H + pad, pad)

    def blit(name: str, x: int, y: int, h: int | None = None) -> None:
        out.paste(atlas.tile(name, h), x, y)

    # Water, 8 px under the ground.
    for y in range(room.h):
        for x in range(room.w):
            if room.lv(x, y) == WATER:
                blit(atlas.auto["shore"]["%02d" % shore_sides(room, x, y)][frame], x * T, y * T + 8)

    def overlays(x: int, y: int, l: int, oy: int) -> None:
        if room.edge_level(x - 1, y) < l:
            blit("rim_w", x * T, oy)
        if room.edge_level(x + 1, y) < l:
            blit("rim_e", x * T, oy)
        if room.inside(x, y - 1) and room.lv(x, y - 1) < l and room.stair_at(x, y - 1) is None:
            blit("rim_n", x * T, oy)
        if room.lv(x, y - 1, -9) > l and room.stair_at(x, y - 1) is None:
            blit("ao_n", x * T, oy)
        if room.lv(x - 1, y, -9) > l and room.lv(x - 1, y, -9) != 99:
            blit("shade_w", x * T, oy)

    # The ground floor and its bank faces over water.
    for y in range(room.h):
        for x in range(room.w):
            if room.lv(x, y) != 0 or room.stair_at(x, y) is not None:
                continue
            blit(top_name(room, x, y), x * T, y * T)
            overlays(x, y, 0, y * T)
            if room.edge_level(x, y + 1) == WATER:
                blit(face_name(room, x, y, True, True), x * T, (y + 1) * T, 8)

    items = []   # (key, order, draw)
    for y in range(room.h):
        if any(room.lv(x, y) > 0 and room.stair_at(x, y) is None for x in range(room.w)):
            items.append(((y + 1) * T, 0, ("row", y)))
    for s in room.stairs:
        items.append(((s["y"] + s["h"]) * T, 1, ("stairs", s)))
    for p in room.props:
        fw, fh = atlas.props[p["kind"]]["footprint"]
        items.append(((p["y"] + fh) * T + 0.5, 2, ("prop", p)))
    for b in bodies or []:
        bx, by = b[0], b[1]
        cx, cy = int(bx), int(by)
        key = by * T
        if room.lv(cx, cy) > 0:
            key = max(key, (cy + 1) * T + 0.25)
        items.append((key, 3, ("body", b)))
    items.sort(key=lambda it: (it[0], it[1]))

    for _key, _o, (kind, obj) in items:
        if kind == "row":
            y = obj
            for x in range(room.w):
                l = room.lv(x, y)
                if l <= 0 or room.stair_at(x, y) is not None:
                    continue
                blit(top_name(room, x, y), x * T, (y - l) * T)
                overlays(x, y, l, (y - l) * T)
                south = min(l, room.edge_level(x, y + 1))
                for k in range(l - south):
                    water = south + k + 1 == 0
                    blit(face_name(room, x, y, k == 0, water), x * T, (y + 1 - l + k) * T, 8 if water else None)
                    # A face's ends: lit where it turns the west corner, shaded at the east.
                    fy = (y + 1 - l + k) * T
                    hh = 8 if water else T
                    if room.edge_level(x - 1, y) < l - k:
                        for j in range(hh):
                            out.blend(x * T, fy + j, (255, 240, 200), 70)
                    if room.edge_level(x + 1, y) < l - k:
                        for j in range(hh):
                            out.blend(x * T + 15, fy + j, SHADE, 120)
        elif kind == "stairs":
            s = obj
            top = s["y"] * T - s["to"] * T
            foot = (s["y"] + s["h"]) * T - s["from"] * T
            yy = top
            while yy < foot:
                for x in range(s["w"]):
                    blit("stairs", (s["x"] + x) * T, yy, min(8, foot - yy))
                yy += 8
            for j in range(top, foot):   # granite cheeks
                x0, x1 = s["x"] * T, (s["x"] + s["w"]) * T - 1
                out.blend(x0, j, (255, 240, 200), 90)
                out.blend(x0 + 1, j, (255, 240, 200), 30)
                out.blend(x1, j, SHADE, 150)
                out.blend(x1 - 1, j, SHADE, 60)
        elif kind == "prop":
            p = obj
            art = atlas.props[p["kind"]]
            fw, fh = art["footprint"]
            cx, cy = p["x"], p["y"]
            lvl = room.lv(cx, cy + fh - 1)
            ground = 8 if lvl < 0 else -lvl * T
            south = (cy + fh) * T
            if art.get("shadow"):
                dx, dy, rx, ry = art["shadow"]
                sx, sy = cx * T + dx, south + ground + dy
                shadow_ellipse(out, sx, sy, rx, ry)
            ox, oy = art["origin"]
            out.paste(atlas.prop(p["kind"]), cx * T - ox, south + ground - oy)
        elif kind == "body":
            bx, by, facing, anim, f = obj
            cx, cy = int(bx), int(by)
            lvl = max(0, room.lv(cx, cy))
            fx, fy = int(bx * T), int(by * T) - lvl * T
            shadow_ellipse(out, fx, fy, 7, 2.5)
            if figure is not None:
                cell, foot = figure(facing, anim, f)
                out.paste(cell, fx - foot[0], fy - foot[1])
    return out


class Shifted(Img):
    """The output canvas: everything is drawn `dy` px lower, so tops raised above the room's first row still show."""

    def __init__(self, w: int, h: int, dy: int):
        super().__init__(w, h, NIGHT)
        self.dy = dy

    def blend(self, x: int, y: int, col, a: int) -> None:
        super().blend(x, y + self.dy, col, a)

    def paste(self, src, x: int, y: int) -> None:
        super().paste(src, x, y + self.dy)


def shadow_ellipse(out: Img, cx: float, cy: float, rx: float, ry: float) -> None:
    """A soft floor shadow: a translucent deep-teal ellipse, denser in its core (no blur: two stepped rings)."""
    for j in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for i in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = (i + 0.5 - cx) / rx, (j + 0.5 - cy) / ry
            d = dx * dx + dy * dy
            if d <= 1.0:
                out.blend(i, j, SHADE, 60 if d > 0.5 else 105)


__all__ = ["Room", "Atlas", "render", "top_name", "face_name", "shore_sides", "alpha"]
