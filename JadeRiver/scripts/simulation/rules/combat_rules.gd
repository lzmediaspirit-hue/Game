class_name CombatRules
extends RefCounted
## S12 · One damage pipeline for everyone, in the order of the build prompt:
## damage = roll × E × (1+D) × (1+P_el) × C_el × Z × A × R × K × (1−DR) × (1−Res_el) × S
## Combatants are plain dictionaries ("views") built by the Combat authority.

static func hit_chance(accuracy: float, evasion: float) -> float:
	var h: Dictionary = ContentDB.stat_const("hit", {})
	if accuracy <= 0.0: return float(h.get("floor", 0.55))
	return clampf(float(h.get("base", 1.1)) - float(h.get("k", 0.35)) * evasion / accuracy, float(h.get("floor", 0.55)), float(h.get("cap", 1.0)))

static func parent_element(el: String) -> String:
	return str(ContentDB.config("elements").get("parent", {}).get(el, el))

static func element_factor(att_el: String, def_el: String) -> float:
	var conf := ContentDB.config("elements")
	var a := parent_element(att_el)
	var d := parent_element(def_el)
	if (a == "yin" and d == "yang") or (a == "yang" and d == "yin"): return float(conf.get("yin_yang", 1.3))
	var over: Dictionary = conf.get("overcomes", {})
	if over.get(a, "") == d: return float(conf.get("cycle_advantage", 1.3))
	if over.get(d, "") == a: return float(conf.get("cycle_disadvantage", 0.75))
	return 1.0

## S18 attunement: how much of your power reaches a zone's foes, and how much more theirs hurts.
static func attunement_factors(attunement: float, required: float) -> Dictionary:
	if required <= 0.0: return {"dealt": 1.0, "taken": 1.0}
	var k: Dictionary = ContentDB.stat_const("attunement", {})
	var ratio := maxf(0.0, attunement) / required
	return {"dealt": minf(float(k.get("cap", 1.1)), float(k.get("floor", 0.3)) + float(k.get("slope", 0.7)) * ratio),
		"taken": 1.0 + maxf(0.0, 1.0 - ratio)}

static func realm_gap_factor(att_realm: int, def_realm: int) -> float:
	var g: Dictionary = ContentDB.stat_const("realm_gap", {})
	var diff := att_realm - def_realm
	if diff > 0: return 1.0 + minf(float(g.get("up_cap", 1.0)), float(g.get("up_per_realm", 0.25)) * diff)
	if diff < 0: return 1.0 - minf(float(g.get("down_max_reduction", 0.6)), float(g.get("down_per_realm", 0.2)) * -diff)
	return 1.0

static func defence_reduction(defence: float, attacker_level: int, penetration: float) -> float:
	var d: Dictionary = ContentDB.stat_const("defence", {})
	var def := maxf(0.0, defence * (1.0 - clampf(penetration, 0.0, 0.4)))
	return minf(float(d.get("cap", 0.75)), def / (def + float(d.get("k_flat", 100)) + float(d.get("k_level", 15)) * attacker_level))

static func crit_chance(attacker: Dictionary, defender: Dictionary) -> float:
	var c: Dictionary = ContentDB.stat_const("crit", {})
	var v := float(attacker.get("crit_chance", 0.05)) + float(attacker.get("crit_bonus", 0.0)) - float(defender.get("tenacity", 0.0)) / float(c.get("tenacity_divisor", 4))
	return clampf(v, 0.0, float(c.get("cap", 0.75)))

## Resolve one hit. `attack` = {damage_type, element, mult:[lo,hi], range:[lo,hi], dao_tier,
## mastery_tier, situation, ignore_armor, ignore_resistance, penetration_bonus, backstab}.
static func resolve(attacker: Dictionary, defender: Dictionary, attack: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var dtype := str(attack.get("damage_type", "physical"))
	var element := str(attack.get("element", attacker.get("element", "none")))
	var result := {"miss": false, "amount": 0, "crit": false, "type": dtype, "element": element}
	# 1 Hit check
	if not attack.get("never_miss", false) and rng.randf() > hit_chance(float(attacker.get("accuracy", 10)), float(defender.get("evasion", 0))):
		result.miss = true
		return result
	# 2 Roll
	var stat = {"physical": "physical_attack", "qi": "qi_attack", "soul": "soul_attack"}.get(dtype, "physical_attack")
	var base_attack := float(attacker.get(stat, attacker.get("physical_attack", 1.0)))
	var rng_range: Array = attack.get("range", [0.9, 1.1])
	var mult: Array = attack.get("mult", [1.0, 1.0])
	var lo := float(rng_range[0]) * float(mult[0])
	var hi := float(rng_range[1]) * float(mult[1])
	var dmg := base_attack * rng.randf_range(lo, maxf(lo, hi))
	# 3 Energy E (physical at half strength)
	var e := float(attacker.get("energy_mult", 1.0))
	dmg *= e if dtype != "physical" else 1.0 + (e - 1.0) * 0.5
	# 4 Dao and mastery D
	var st: Dictionary = ContentDB.stat_const("technique_cost", {})
	dmg *= 1.0 + float(st.get("dao_damage_per_tier", 0.05)) * int(attack.get("dao_tier", 0)) + float(st.get("mastery_damage_per_tier", 0.08)) * int(attack.get("mastery_tier", 0))
	# 5 Elemental power
	dmg *= 1.0 + float(attacker.get("elemental_power", 0.0)) + float(attacker.get("element_power_" + parent_element(element), 0.0))
	# 6 Element cycle
	dmg *= element_factor(element, str(defender.get("element", "none")))
	# 7 Zone Z (room element match); 8 Attunement A
	if attack.get("room_element", "") != "" and parent_element(element) == parent_element(str(attack.room_element)): dmg *= 1.1
	dmg *= float(attack.get("attunement", 1.0))
	# 9 Realm gap
	dmg *= realm_gap_factor(int(attacker.get("realm_index", 0)), int(defender.get("realm_index", 0)))
	# 10 Critical
	if rng.randf() < crit_chance(attacker, defender):
		result.crit = true
		dmg *= clampf(float(attacker.get("crit_damage", 1.5)), 1.0, float(ContentDB.stat_const("crit.damage_cap", 3.0)))
	# 11 Defence
	if not attack.get("ignore_armor", false):
		var def_stat = {"physical": "physical_defense", "qi": "qi_resistance", "soul": "soul_defense"}.get(dtype, "physical_defense")
		var pen := float(attacker.get("penetration", 0.0)) + float(attack.get("penetration_bonus", 0.0)) + float(attack.get("ignore_resistance", 0.0))
		# S47 v1.1: armour broken by a heavy sabre lets every blow through a quarter of it.
		if defender.get("sundered", false): pen += float(ContentDB.entry("status_effects", "sundered").get("pierce_defence", 0.25))
		dmg *= 1.0 - defence_reduction(float(defender.get(def_stat, 0.0)), int(attacker.get("level", 1)), pen)
	# 12 Elemental resistance
	var res := float(defender.get("resist_" + parent_element(element), 0.0))
	dmg *= 1.0 - clampf(res, 0.0, 0.75)
	# 13 Situation S (vulnerable, shock, guard, backstab, perfect timing, formations)
	dmg *= float(attack.get("situation", 1.0))
	if defender.get("vulnerable", false): dmg *= 1.0 + float(ContentDB.stat_const("combat.vulnerable", 0.2))
	if defender.get("shocked", false): dmg *= 1.0 + float(ContentDB.stat_const("combat.shock", 0.2))
	if float(defender.get("guarding", 0.0)) > 0.0: dmg *= 1.0 - clampf(float(defender.guarding), 0.0, 0.8)
	result.amount = maxi(1, int(round(dmg)))
	return result

## Status application (S12): chance × (1 − Tenacity), duration × (1 − Tenacity/2).
static func status_roll(spec: Dictionary, defender: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var ten := clampf(float(defender.get("tenacity", 0.0)), 0.0, 0.6)
	var chance := float(spec.get("chance", 1.0)) * (1.0 - ten)
	if rng.randf() >= chance: return {}
	return {"id": str(spec.id), "remaining": float(spec.get("duration_s", 1.0)) * (1.0 - ten * float(ContentDB.stat_const("combat.status_duration_tenacity", 0.5))),
		"power": float(spec.get("power", 0.0))}

## Badge colour by realm gap to the player (S13): grey, green, white, orange, red.
static func badge_color(player_realm: int, enemy_realm: int, player_level: int, enemy_level: int) -> String:
	var realm_diff := enemy_realm - player_realm
	if realm_diff <= -2: return "grey"
	if realm_diff >= 2: return "red"
	var lv := enemy_level - player_level
	if lv >= 5: return "orange"
	if lv <= -5: return "green"
	return "white"

## S12 Pressure contest: when Pressure exceeds the target's Will, the target is slowed and loses output by
## min(50%, 25% x (Pressure / Will - 1)); 0 when it holds. S46 bloodline suppression reads the same rule.
static func pressure_loss(pressure: float, will: float) -> float:
	if will <= 0.0 or pressure <= will: return 0.0
	return minf(0.5, 0.25 * (pressure / will - 1.0))
