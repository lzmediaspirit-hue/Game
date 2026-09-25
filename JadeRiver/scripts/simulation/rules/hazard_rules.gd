class_name HazardRules
extends RefCounted
## S17 · Room hazards. Each runs a cycle (quiet tell → warning → active → cooldown) and is
## answered by one attribute (S10 world effects). The answer a room asks is k × (5 + its top
## Level): what that attribute is at that Level before any training. Pure functions.

const PHASES := ["tell", "warn", "active", "cooldown"]

static func need(h: Dictionary, room: Dictionary) -> int:
	var lv: Array = room.get("level_range", [0, 0])
	return int(round(float(h.get("k", 1.3)) * (5.0 + float(lv[1]))))

## 0 (unanswered) to 1 (answered).
static func answered(have: float, need_v: float) -> float:
	if need_v <= 0.0: return 1.0
	return clampf(have / need_v, 0.0, 1.0)

## Share of a push or status that gets through: all of it when unanswered, falling to half
## as the answer nears, none once it is met.
static func effect_scale(have: float, need_v: float) -> float:
	var f := answered(have, need_v)
	if f >= 1.0: return 0.0
	return 1.0 - float(ContentDB.stat_const("hazard.partial", 0.5)) * f

## A strike still hurts when answered, only less.
static func damage_scale(have: float, need_v: float) -> float:
	var f := answered(have, need_v)
	if f >= 1.0: return float(ContentDB.stat_const("hazard.answered_damage", 0.35))
	return 1.0 - float(ContentDB.stat_const("hazard.partial", 0.5)) * f

static func duration(h: Dictionary, phase: String) -> float:
	var cyc: Array = h.get("cycle", [2.0, 1.0, 1.0, 5.0])
	return float(cyc[PHASES.find(phase)])

static func next_phase(phase: String) -> String:
	return PHASES[(PHASES.find(phase) + 1) % PHASES.size()]

## The room areas a pool or flow hazard lives in.
static func areas(h: Dictionary, room: Dictionary) -> Array:
	var kinds: Array = h.get("areas", [])
	return room.get("areas", []).filter(func(a): return str(a.get("kind", "")) in kinds)

static func rect(a: Dictionary) -> Rect2:
	var r: Array = a.rect
	return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))

## What a room's hazards ask of a character, for the map and the room banner:
## [{id, name, stat, need, have, answered}].
static func summary(c, room: Dictionary) -> Array:
	var out: Array = []
	for hid in room.get("hazards", []):
		var h := ContentDB.entry("hazards", str(hid))
		if h.is_empty(): continue
		var n := need(h, room)
		var have: float = c.stats.value(str(h.answer)) if c != null else 0.0
		out.append({"id": str(hid), "name": str(h.get("name", hid)), "stat": str(h.answer), "need": n, "have": have, "answered": have >= n})
	return out
