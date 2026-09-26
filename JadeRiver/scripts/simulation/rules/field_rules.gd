class_name FieldRules
extends RefCounted
## S28 · Field powers (v1.2): Presence from Will Manifest, the Sphere from Sphere Lord. Pure functions over the
## numbers in stats.json "presence". Pressure and Will are measured on the same scale as the S10 answers: what an
## attribute is at a Level before training, 5 + Level, times the power's own factors.

## Will of a foe: 5 + its Level, raised for elites and bosses (the role's factor).
static func enemy_will(level: int, role: String, elite := false) -> float:
	var k: Dictionary = ContentDB.stat_const("presence.role_will", {})
	var r := float(k.get("boss", 1.3)) if role in ["field_boss", "dungeon_boss", "story_boss"] else float(k.get("normal", 1.0))
	if elite: r = maxf(r, float(k.get("elite", 1.15)))
	return (5.0 + float(level)) * r

## Pressure of a Presence at `presence_level` held by a Level-`level` bearer, plus any Pressure from gear and titles.
## A foe's Presence carries its role's factor as well.
static func pressure(level: int, presence_level: int, bonus := 0.0, role_factor := 1.0) -> float:
	if presence_level <= 0: return 0.0
	var per := float(ContentDB.stat_const("presence.per_level", 0.06))
	return (5.0 + float(level)) * (1.0 + per * float(presence_level)) * role_factor + bonus

## How far a Presence reaches on the ground plane.
static func radius(presence_level: int) -> float:
	var p: Dictionary = ContentDB.stat_const("presence", {})
	return float(p.get("radius_base", 220)) + float(p.get("radius_per_level", 12)) * float(presence_level)

## The Presence level reached with `xp` (1-10).
static func level_for(xp: float) -> int:
	var steps: Array = ContentDB.stat_const("presence.xp_levels", [0])
	var lv := 1
	for i in steps.size():
		if xp >= float(steps[i]): lv = i + 1
	return clampi(lv, 1, steps.size())

## S12 Pressure contest between two Presences that meet (S28). A bearer's own Presence stands with its Will:
## whoever presses harder than the other side's max(Will, Pressure) takes away output and speed by the
## Pressure rule; the other is not pressed. The boundary sits where the two push to a standstill, as a
## share of the distance from A to B. Returns {loss_a, loss_b, boundary}.
static func clash(pressure_a: float, will_a: float, pressure_b: float, will_b: float) -> Dictionary:
	var hold_a := maxf(will_a, pressure_a)
	var hold_b := maxf(will_b, pressure_b)
	var total := pressure_a + pressure_b
	return {"loss_a": CombatRules.pressure_loss(pressure_b, hold_a), "loss_b": CombatRules.pressure_loss(pressure_a, hold_b),
		"boundary": pressure_a / total if total > 0.0 else 0.5}

# ------------------------------------------------------------------ the Sphere (Sphere Lord 1)
## Reach of a Sphere drawn on a Dao at `tier` (tier 6, Original Application, reaches further).
static func sphere_radius(tier: int) -> float:
	var k: Dictionary = ContentDB.stat_const("sphere", {})
	return float(k.get("radius_base", 160)) + float(k.get("radius_per_tier", 20)) * float(tier) + (float(k.get("tier6_radius", 40)) if tier >= 6 else 0.0)

## Power of a Sphere: 5 + Level, raised by its Dao's tier (and again at tier 6), times a foe's role factor.
static func sphere_power(level: int, tier: int, role_factor := 1.0, bonus := 0.0) -> float:
	if tier <= 0: return 0.0
	var k: Dictionary = ContentDB.stat_const("sphere", {})
	var m := 1.0 + float(k.get("power_per_tier", 0.08)) * float(tier) + (float(k.get("tier6_power", 0.1)) if tier >= 6 else 0.0)
	return (5.0 + float(level)) * m * role_factor + bonus

## What a Sphere of `element` does, with the room's terrain adding its own (frost on water, flame on grass).
static func sphere_effects(element: String, terrain: Array) -> Dictionary:
	var row: Dictionary = ContentDB.stat_const("sphere", {}).get("elements", {}).get(element, {})
	var out := row.duplicate()
	out.erase("terrain")
	for t in terrain:
		var extra: Dictionary = row.get("terrain", {}).get(str(t), {})
		for k in extra: out[k] = extra[k]
	return out

## A technique fed by the ground (S12 step 7): the ground's element is its own, or generates it (Wood feeds Fire).
static func feeds(ground: String, element: String) -> bool:
	if ground == "" or element == "" or element == "none": return false
	var g := CombatRules.parent_element(ground)
	var e := CombatRules.parent_element(element)
	if g == e: return true
	var cyc: Array = ContentDB.config("elements").get("generating", [])
	var i := cyc.find(g)
	return i >= 0 and str(cyc[(i + 1) % cyc.size()]) == e
