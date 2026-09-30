class_name TopdownAim
extends RefCounted
## Top-down redesign, Phase 2 (decisions 29 and 30; docs/research/alabaster_dawn_2_5d.md "Aiming and targeting"): the
## one place that says where a blow or a technique goes on the ground plane. The combat authority resolves hits with it
## and the HUD draws its aim previews with it, so what the player sees is what strikes.
##
## - Heights: a blow lands only when the target's feet are within the attacker's band (movement.json
##   topdown.combat.hit_band, air_band for a strike from the air): a foe a level up or down is out of reach of a
##   swing, a jump strike reaches down onto one, and a body in the air slips a ground blow.
## - Soft lock: a tap aims at the nearest foe in a cone round the facing (`cone_deg`, within `range`); a dragged aim
##   snaps to a foe within `snap_deg` of it and otherwise goes exactly where it was dragged.
## - Forms: a technique aims as a `line` (thrust, volley, wave, every projectile), a `cone` (sweep, arc, strike), a
##   circle at a `point` within its reach (burst, rain, pillar) or a circle round the caster (`self`: domain, ward).

static func cfg(key: String, fallback = 0.0):
	return ContentDB.movement("topdown.aim." + key, fallback)

static func band(air: bool) -> Array:
	return ContentDB.movement("topdown.combat.air_band" if air else "topdown.combat.hit_band", [-56, 12] if air else [-12, 12])

## Are the feet `dz` above (below, when negative) the attacker's within reach of its blow?
static func compatible(dz: float, air := false) -> bool:
	var b := band(air)
	return dz >= float(b[0]) and dz <= float(b[1])

## A technique's aim shape.
static func form_of(t: Dictionary) -> String:
	if t.has("projectile"): return "line"
	if str(t.get("damage_type", "")) in ["buff", "illusion", "stance"]: return "self"
	var form := str(t.get("form", (t.get("vfx", {}) as Dictionary).get("anim", "")))
	var forms: Dictionary = cfg("forms", {})
	for k in forms:
		if form in (forms[k] as Array): return str(k)
	return "self" if t.get("both_sides", false) else "cone"

## How far a technique reaches along its aim (a projectile's flight, else its hitbox) and its half width.
static func reach_of(t: Dictionary) -> float:
	if t.has("projectile"): return float((t.projectile as Dictionary).get("range", 400))
	return float((t.get("hitbox", {"x": [0, 80]}) as Dictionary).get("x", [0, 80])[1])

static func half_width_of(t: Dictionary) -> float:
	return float((t.get("hitbox", {}) as Dictionary).get("depth", 30))

## The ground point a `point` form lands on: along `aim` at `dist` (a drag's length, a foe's distance), within reach.
static func point_at(origin: Vector2, aim: Vector2, dist: float, reach: float) -> Vector2:
	return origin + aim.normalized() * clampf(dist, 0.0, reach)

## Does a body of radius `r` at `p` fall inside a `form` cast from `o` along the unit `aim` (`at`: a point form's
## centre)?
static func contains(form: String, o: Vector2, aim: Vector2, at: Vector2, reach: float, half_width: float, p: Vector2, r: float) -> bool:
	var d := p - o
	match form:
		"self": return d.length() <= reach + r
		"point": return at.distance_to(p) <= float(cfg("point_radius", 48)) + r
		"cone":
			if d.length() > reach + r: return false
			return d.length() <= r + 8.0 or absf(rad_to_deg(aim.angle_to(d))) <= float(cfg("cone_half_deg", 45))
		_:
			var f := d.dot(aim)
			return f >= -r and f <= reach + r and absf(d.cross(aim)) <= half_width + r

## The foe a tap or a drag aims at from `o` (feet at `z`) toward `aim`: the nearest living foe within `range` and
## `half_deg` of the aim whose feet are within reach of the blow's height band. null when none.
static func pick(foes: Array, o: Vector2, z: float, aim: Vector2, half_deg: float, range: float, air := false) -> EnemyState:
	var best: EnemyState = null
	var best_d := INF
	for e in foes:
		if e.team != "enemy" or e.hidden or not e.alive: continue
		if not compatible(e.altitude + e.hover - z, air): continue
		var d: Vector2 = e.plane - o
		var n := d.length()
		if n > range + e.half_width() or n >= best_d: continue
		if n > 1.0 and absf(rad_to_deg(aim.angle_to(d))) > half_deg: continue
		best = e
		best_d = n
	return best

## The soft lock of a tap: the nearest foe in the facing's cone.
static func soft_target(foes: Array, o: Vector2, z: float, facing: Vector2, air := false) -> EnemyState:
	return pick(foes, o, z, facing, float(cfg("cone_deg", 120)) * 0.5, float(cfg("range", 160)), air)

## A dragged aim: snapped onto a foe within `snap_deg` (and the form's reach, or the soft-lock range) when there is one.
static func snap(foes: Array, o: Vector2, z: float, aim: Vector2, reach: float, air := false) -> EnemyState:
	return pick(foes, o, z, aim, float(cfg("snap_deg", 15)), maxf(reach, float(cfg("range", 160))), air)
