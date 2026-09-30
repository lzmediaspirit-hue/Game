"""The terrain tiles by their Phase 3 names: floor tops, wall faces, stairs, water frames, auto-tile transitions and
light overlays, each a 16 x 16 `Img`.

Since Terrain v2 (decision 40) every one of these is drawn by `terrain2.py`: a top is one tile of its material's macro
pattern (with a decal where its kind asks for one), a face is the first tile of its face pattern, a water frame is
the water pattern's first tile with its shore overlay, a transition is the path under the positional grass overlay.
The names, sizes and meanings stay those of the Phase 3 contract (the TileSet, the manifest's `paint` table and the
Phase 1 loader), so nothing that reads them changes; the room view draws the v2 sets themselves (TopdownTerrain).
The rules are in docs/redesign/art_bible.md.
"""
from __future__ import annotations

from functools import lru_cache

import sand_snow as ss
import terrain2 as t2
from canvas import T, Img
from palette import CLEAR, PAVE2, STONE2

CORNER_KEYS = t2.CORNER_KEYS


def corner_name(corners: tuple) -> str:
    return t2.key(corners)


def composite(base: Img, *over: Img) -> Img:
    out = Img(base.w, base.h)
    out.img.alpha_composite(base.img)
    for o in over:
        out.img.alpha_composite(o.img)
    return out


# The patterns, built once per build (they are pure functions of their seeds).
@lru_cache(maxsize=None)
def macro(kind: str) -> tuple:
    """A material's macro pattern cut into its tiles, row-major: (tiles, width in tiles, height in tiles)."""
    if kind == "grass":
        img, w, h = t2.grass_macro(), t2.M, t2.M
    elif kind == "dirt":
        img, w, h = t2.dirt_macro(), t2.M, t2.M
    elif kind == "pave":
        img, w, h = t2.paving_macro(), t2.PAVE_P // T, t2.PAVE_P // T
    elif kind == "stone":
        img, w, h = t2.stone_macro(), t2.M, t2.M
    elif kind == "rock":
        img, w, h = t2.rock_macro(), t2.M, t2.M
    elif kind == "wood":
        img, w, h = t2.wood_macro(), t2.M, t2.M
    elif kind == "roof":
        img, w, h = t2.roof_macro(), t2.M, t2.M
    elif kind == "wall":
        img, w, h = t2.wall_top_row(), t2.M, 1
    elif kind in ("sand", "snow", "snowpack"):
        img, w, h = macro_img(kind), t2.M, t2.M
    else:
        raise KeyError(kind)
    return tuple(t2.cut(img, w, h)), w, h


@lru_cache(maxsize=None)
def macro_img(kind: str) -> Img:
    """The whole pattern (for the house props' roofs, and the overlays that lay a material's own pixels)."""
    return {"roof": t2.roof_macro, "grass": t2.grass_macro, "sand": ss.sand_macro, "snow": ss.snow_macro,
            "snowpack": ss.snowpack_macro}[kind]()


@lru_cache(maxsize=None)
def face_set(kind: str) -> tuple:
    """(first-row tiles, body tiles) of a face kind."""
    fn = {"rock": t2.rock_faces, "earth": t2.earth_faces, "stone": t2.stone_faces, "bank": t2.bank_faces,
          "wood": t2.wood_faces, "wall": t2.wall_faces, "pave": lambda: t2.stone_faces(925, PAVE2),
          "sand": ss.sand_faces, "snow": ss.snow_faces}[kind]
    tops, body = fn()
    return tuple(tops), tuple(body)


@lru_cache(maxsize=None)
def decal_sets() -> dict:
    return {**t2.decals(), "sand": ss.sand_decals(), "snow": ss.snow_decals(), "snowpack": ss.snowpack_decals()}


def _m(kind: str, i: int) -> Img:
    tiles, w, h = macro(kind)
    return tiles[i % len(tiles)]


# ============================================================================================================ tops
def grass(seed: int, kind: str = "plain") -> Img:
    """A meadow tile: the grass pattern at a place picked by `seed`, with a clump (lush), clover, flowers or a puddle
    (marsh) laid on it."""
    base = _m("grass", seed * 5)
    d = decal_sets()
    over = {"plain": [], "lush": [d["grass"][0]], "clover": [d["grass"][8]], "flowers": [d["flowers"][seed % 6]],
            "marsh": [d["marsh"][seed % 4]]}[kind]
    return composite(base, *over)


def dirt(seed: int) -> Img:
    return composite(_m("dirt", seed * 3), *([decal_sets()["dirt"][seed % 3]] if seed % 2 else []))


def paving(seed: int, kind: str = "a") -> Img:
    """Flagstones: the paving pattern at a place picked by `seed` (kind m: with moss)."""
    base = _m("pave", seed * 9)
    return composite(base, decal_sets()["pave"][1]) if kind == "m" else base


def stone_top(seed: int, cracked: bool = False) -> Img:
    base = _m("stone", seed)
    return composite(base, decal_sets()["stone"][2]) if cracked else base


def rock_top(seed: int) -> Img:
    return _m("rock", seed * 3)


def sand(seed: int) -> Img:
    """Sand: the sand pattern at a place picked by `seed`, now and then with a shell or a track laid on it."""
    return composite(_m("sand", seed * 7), *([decal_sets()["sand"][seed % 8]] if seed % 3 == 0 else []))


def snow(seed: int, packed: bool = False) -> Img:
    return _m("snowpack" if packed else "snow", seed * 5)


def wood_deck(seed: int) -> Img:
    return _m("wood", seed)


def roof_top(seed: int) -> Img:
    return _m("roof", seed)


def wall_top(seed: int) -> Img:
    return _m("wall", seed)


# =========================================================================================================== faces
def _face(kind: str, first: bool) -> Img:
    tops, body = face_set(kind)
    return tops[0] if first else body[0]


def earth_face(seed: int, first: bool) -> Img:
    return _face("earth", first)


def stone_face(seed: int, first: bool, top=STONE2) -> Img:
    return _face("pave" if top is not STONE2 else "stone", first)


def rock_face(seed: int, first: bool) -> Img:
    return _face("rock", first)


def bank_face(seed: int, first: bool) -> Img:
    return _face("bank", first)


def wood_face(seed: int, first: bool) -> Img:
    return _face("wood", first)


def wall_face(seed: int, first: bool) -> Img:
    return _face("wall", first)


def eave_face(seed: int) -> Img:
    return t2.eave_face(seed)


def plaster_face(seed: int, kind: str = "plain", plinth: bool = True) -> Img:
    return t2.plaster_face(seed, kind, plinth)


def stairs() -> Img:
    return t2.stairs()


# =========================================================================================================== water
@lru_cache(maxsize=None)
def water_frames() -> tuple:
    """The water pattern's tiles per frame: ((16 tiles of frame 0), ... frame 3)."""
    return tuple(tuple(t2.cut(t2.water_macro(f))) for f in range(4))


@lru_cache(maxsize=None)
def shore_overlay(sides: int, frame: int) -> Img:
    return t2.shore_fx(sides, frame)


def water(frame: int, sides: int = 0) -> Img:
    """The Jade River, one of four frames (250 ms): the water pattern's first tile with, for a shore cell, its shore
    overlay (bit 1 N, 2 E, 4 S, 8 W = land)."""
    base = water_frames()[frame][0]
    return composite(base, shore_overlay(sides, frame)) if sides else composite(base)


# ===================================================================================================== transitions
@lru_cache(maxsize=None)
def grass_over(corners: tuple, pos: tuple = (0, 0)) -> Img:
    """The positional grass overlay for a corner case (see terrain2.grass_over)."""
    return t2.grass_over(corners, pos, macro_img("grass"))


@lru_cache(maxsize=None)
def creep_over(kind: str, corners: tuple, pos: tuple = (0, 0)) -> Img:
    """Sand or snow over its neighbour, positional (see sand_snow.creep_over)."""
    return ss.creep_over(kind, corners, pos, macro_img(kind), {"sand": 520, "snow": 540, "snowpack": 560}[kind])


@lru_cache(maxsize=None)
def beach_overlay(sides: int, frame: int) -> Img:
    return ss.beach_fx(sides, frame)


def blend_corners(under: Img, corners: tuple) -> Img:
    """A corner-matched transition tile for the TileSet: `under` (a path or paving) with grass over the corners
    marked 1, as the grass pattern's first place draws it."""
    if corners == (1, 1, 1, 1):
        return composite(_m("grass", 0))
    if corners == (0, 0, 0, 0):
        return composite(under)
    return composite(under, grass_over(corners))


# ======================================================================================================== overlays
def overlay(kind: str) -> Img:
    return t2.overlay(kind)


__all__ = ["grass", "dirt", "paving", "sand", "snow", "creep_over", "beach_overlay", "stone_top", "rock_top", "wood_deck", "roof_top", "wall_top", "earth_face",
           "stone_face", "rock_face", "bank_face", "wood_face", "eave_face", "plaster_face", "wall_face", "stairs",
           "water", "blend_corners", "overlay", "CORNER_KEYS", "corner_name", "composite", "CLEAR", "macro",
           "face_set", "decal_sets", "water_frames", "shore_overlay", "grass_over", "T"]
