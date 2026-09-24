# Shared x / depth / height movement model over walkable surfaces (ground, decks, bridges, stairs).
# Surfaces are bounded top faces: x0..x1, d0..d1, height h0→h1 along x. Solid surfaces are walls
# below their top; non-solid (bridges) can be walked under. Draw order never decides collision.
class_name Physics
extends RefCounted

const STEP := 7.0        # max step up/down while walking
const GRAVITY := 0.32
const JUMP_V := 5.7
const DEPTH_MAX := 78.0


static func surf_h(s: Dictionary, x: float) -> float:
	if s.h0 == s.h1:
		return s.h0
	var t := clampf((x - s.x0) / maxf(1.0, s.x1 - s.x0), 0.0, 1.0)
	return lerpf(s.h0, s.h1, t)


static func inside(s: Dictionary, x: float, d: float) -> bool:
	return x >= s.x0 and x <= s.x1 and d >= s.d0 and d <= s.d1


# Highest surface whose top is at or below `h` at (x, d).
static func support(surfs: Array, x: float, d: float, h: float, ignore := "") -> Dictionary:
	var best: Dictionary = {}
	var bh := -INF
	for s in surfs:
		if s.id == ignore or not inside(s, x, d):
			continue
		var sh := surf_h(s, x)
		if sh <= h + 0.5 and sh > bh:
			best = s
			bh = sh
	return best


static func blocked_by_wall(surfs: Array, x: float, d: float, foot: float) -> bool:
	for s in surfs:
		if s.solid and inside(s, x, d) and surf_h(s, x) > foot + STEP:
			return true
	return false


# Grounded walking: returns true if the body moved. May start a fall off an open edge.
static func walk(b, surfs: Array, dx: float, dd: float, level_w: float) -> bool:
	var moved := _try_walk(b, surfs, dx, dd, level_w)
	if not moved and dx != 0.0 and dd != 0.0:
		moved = _try_walk(b, surfs, dx, 0.0, level_w) or _try_walk(b, surfs, 0.0, dd, level_w)
	return moved


static func _try_walk(b, surfs: Array, dx: float, dd: float, level_w: float) -> bool:
	var nx := clampf(b.x + dx, 6.0, level_w - 6.0)
	var nd := clampf(b.d + dd, 0.0, DEPTH_MAX)
	if nx == b.x and nd == b.d:
		return false
	if blocked_by_wall(surfs, nx, nd, b.h):
		return false
	# continue on a surface within step range
	var best: Dictionary = {}
	var bh := -INF
	for s in surfs:
		if s.id == b.ignore or not inside(s, nx, nd):
			continue
		var sh := surf_h(s, nx)
		if absf(sh - b.h) <= STEP and sh > bh:
			best = s
			bh = sh
	if not best.is_empty():
		b.x = nx
		b.d = nd
		b.h = bh
		b.surf = best.id
		return true
	# leaving the current surface: rails block, open edges let you fall
	var cur := _by_id(surfs, b.surf)
	if not cur.is_empty():
		var r: Dictionary = cur.rails
		if (nd < cur.d0 and r.back) or (nd > cur.d1 and r.front) or (nx < cur.x0 and r.left) or (nx > cur.x1 and r.right):
			return false
	b.x = nx
	b.d = nd
	b.grounded = false
	b.vz = 0.0
	return true


# Airborne steering: blocked only by solid walls above the feet.
static func air_move(b, surfs: Array, dx: float, dd: float, level_w: float) -> void:
	var nx := clampf(b.x + dx, 6.0, level_w - 6.0)
	var nd := clampf(b.d + dd, 0.0, DEPTH_MAX)
	for s in surfs:
		if s.solid and inside(s, nx, nd) and surf_h(s, nx) > b.h + 0.5:
			if inside(s, nx, b.d) and not inside(s, b.x, nd):
				nx = b.x
			elif inside(s, b.x, nd) and not inside(s, nx, b.d):
				nd = b.d
			else:
				nx = b.x
				nd = b.d
	b.x = nx
	b.d = nd


# Gravity + landing on the highest eligible top face crossed while descending.
static func fall(b, surfs: Array) -> bool:
	var prev: float = b.h
	b.vz -= GRAVITY
	var nh: float = b.h + b.vz
	if b.vz <= 0.0:
		var best: Dictionary = {}
		var bh := -INF
		for s in surfs:
			if s.id == b.ignore or not inside(s, b.x, b.d):
				continue
			var sh := surf_h(s, b.x)
			if sh <= prev + 0.01 and sh >= nh - 0.01 and sh > bh:
				best = s
				bh = sh
		if not best.is_empty():
			b.h = bh
			b.vz = 0.0
			b.grounded = true
			b.surf = best.id
			return true
	b.h = nh
	return false


static func _by_id(surfs: Array, id: String) -> Dictionary:
	for s in surfs:
		if s.id == id:
			return s
	return {}


static func shadow_h(surfs: Array, x: float, d: float, h: float, ignore := "") -> float:
	var s := support(surfs, x, d, h, ignore)
	return 0.0 if s.is_empty() else surf_h(s, x)
