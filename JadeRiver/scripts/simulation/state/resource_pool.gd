class_name ResourcePool
extends RefCounted
## Combat's ResourcePool (Part 2 owner table): HP, QI, Soul, Composure and Hollowing
## current values, status effects, cooldowns and combat timers for one actor.
## Maximums come from the actor's StatBlock; a pool with max 0 does not exist yet
## (no QI before Bone Forging 7, no Soul before Spirit Awakening 1).

var hp := 50.0
var qi := 0.0
var soul := 0.0
var composure := 100.0
var hollowing := 0.0
var max_hp := 50.0
var max_qi := 0.0
var max_soul := 0.0
var shield := 0.0
var statuses: Array = []          # [{id, remaining, power, source, tick_s}]
var steadfast: Dictionary = {}    # status id -> remaining immunity (bosses)
var cooldowns: Dictionary = {}    # key -> remaining seconds
var since_hit := 999.0            # seconds since the last damaging hit
var since_composure_use := 999.0
var invulnerable := 0.0
var alive := true

func set_max(pool: String, value: float) -> void:
	value = maxf(0.0, value)
	match pool:
		"hp":
			if max_hp > 0: hp = hp * value / max_hp if hp >= max_hp - 0.001 else minf(hp, value)
			max_hp = value
			hp = minf(hp, max_hp)
		"qi":
			var was_full := qi >= max_qi - 0.001 and max_qi > 0
			max_qi = value
			qi = max_qi if was_full else minf(qi, max_qi)
		"soul":
			var soul_full := soul >= max_soul - 0.001 and max_soul > 0
			max_soul = value
			soul = max_soul if soul_full else minf(soul, max_soul)

func get_value(pool: String) -> float:
	match pool:
		"hp": return hp
		"qi": return qi
		"soul": return soul
		"composure": return composure
		"hollowing": return hollowing
	return 0.0

func get_max(pool: String) -> float:
	match pool:
		"hp": return max_hp
		"qi": return max_qi
		"soul": return max_soul
		"composure": return 100.0
		"hollowing": return 100.0
	return 0.0

func set_value(pool: String, value: float) -> void:
	match pool:
		"hp": hp = clampf(value, 0.0, max_hp)
		"qi": qi = clampf(value, 0.0, max_qi)
		"soul": soul = clampf(value, 0.0, max_soul)
		"composure": composure = clampf(value, 0.0, 100.0)
		"hollowing": hollowing = clampf(value, 0.0, 100.0)

func has_status(id: String) -> bool:
	for s in statuses:
		if s.id == id: return true
	return false

func status(id: String) -> Dictionary:
	for s in statuses:
		if s.id == id: return s
	return {}

func blocked(action: String) -> bool:
	for s in statuses:
		if action in ContentDB.entry("status_effects", s.id).get("blocks", []): return true
	return false

func cooldown(key: String) -> float:
	return float(cooldowns.get(key, 0.0))

func snapshot() -> Dictionary:
	return {"hp": hp, "qi": qi, "soul": soul, "composure": composure, "hollowing": hollowing}

func restore(d: Dictionary) -> void:
	hp = float(d.get("hp", hp))
	qi = float(d.get("qi", qi))
	soul = float(d.get("soul", soul))
	composure = float(d.get("composure", 100.0))
	hollowing = float(d.get("hollowing", 0.0))
