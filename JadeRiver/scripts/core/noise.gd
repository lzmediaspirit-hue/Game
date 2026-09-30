class_name HashNoise
extends RefCounted
## Decision 45, phase 2 (S4, DUP-02): the game's one home for steady pseudo-random numbers, the same for the same inputs
## on every frame, run and machine. (HashNoise, since `Noise` is the engine's own class, FastNoiseLite's base.) Painted
## detail and scatter use them (a page's stars and boards, a hazard's sparks, an effect's jitter), and so do the
## top-down room's tiles, foliage and critters. They are never the game's Rng streams: nothing here draws from or moves
## a stream.
##
## Each function is the exact arithmetic of the copies it replaced, so every output is bit-identical to theirs
## (tests/shared_runtime_tests.gd compares them over a grid). Change none of the constants: terrain, foliage and
## critters are placed from them, and the tile builder (tools/art/topdown/canvas.py `h01`) must agree with `cell`.

## A steady number in [0, 1) for the pair (i, salt): the sin-hash. It replaced FxLayer._hash, HazardView._h,
## MapPage._rnd, BeastKit.noise and the Bag's _hash.
static func scatter(i: int, salt: int) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(salt) * 78.233) * 43758.5453, 1.0)

## A steady number in [0, 1) for the integer cell (x, y) under seed s: the integer hash the tile builder uses
## (tools/art/topdown/canvas.py `h01`). It was TopdownTerrain.h01.
static func cell(x: int, y: int, s: int) -> float:
	var n := (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
	n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
	return float((n ^ (n >> 16)) & 0xFFFF) / 65536.0

## Value noise over the plane from `cell` (smoothstep between lattice points), in [0, 1). It was TopdownTerrain.vnoise.
static func value(x: float, y: float, s: int) -> float:
	var x0 := floori(x)
	var y0 := floori(y)
	var tx := x - x0
	var ty := y - y0
	tx = tx * tx * (3.0 - 2.0 * tx)
	ty = ty * ty * (3.0 - 2.0 * ty)
	var a := lerpf(cell(x0, y0, s), cell(x0 + 1, y0, s), tx)
	var b := lerpf(cell(x0, y0 + 1, s), cell(x0 + 1, y0 + 1, s), tx)
	return lerpf(a, b, ty)
