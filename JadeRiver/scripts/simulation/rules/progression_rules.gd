class_name ProgressionRules
extends RefCounted
## S03/S05/S06/S07/S29 · Pure progression formulas. No side effects, no clock,
## no randomness except through an explicit RNG argument.

static func realm(key: String) -> Dictionary:
	return ContentDB.realm(key)

## Level from the realm ladder. Orders give +1 Level at the start, 33% and 66%;
## Inner Heaven ranks give +1 at each fifth (S03).
static func level_for(key: String, progress: float) -> int:
	var r := realm(key)
	var levels := int(r.get("levels", 1))
	var base := int(r.get("level", 0))
	if levels <= 1: return base
	return base + clampi(int(floor(clampf(progress, 0.0, 0.9999) * levels)), 0, levels - 1)

static func level(c) -> int:
	return level_for(c.cultivator.realm_key, c.cultivator.progress_fraction())

static func realm_index(key: String) -> int:
	return int(realm(key).get("realm_index", 0))

static func realm_index_for_level(lv: int) -> int:
	return realm_index(ContentDB.realm_key_for_level(lv))

static func at_least(key: String, target: String) -> bool:
	return ContentDB.realm_position(key) >= ContentDB.realm_position(target)

## Body stages (Mortal to Bone Forging 6) grow mainly by training; meditation gives ×0.3.
static func is_body_stage(key: String) -> bool:
	return ContentDB.realm_position(key) <= ContentDB.realm_position(str(ContentDB.curve("body_stage_until", "bone_forging_6")))

static func stability_factor(word: String) -> float:
	return float(ContentDB.curve("stability_factor.%s" % word, 1.0))

static func method(id: String) -> Dictionary:
	return ContentDB.entry("methods", id)

## Compatibility word between a method's affinity and the character's aptitude (S08).
static func method_compatibility(c, method_id: String) -> String:
	var m := method(method_id)
	var aff := str(m.get("affinity", ""))
	var apt: Dictionary = c.cultivator.aptitude.get("element_" + aff, {})
	var value := float(apt.get("value", 0.0))
	if value >= 0.05: return "excellent"
	if value <= -0.05: return "poor"
	return "good"

static func method_rate(c) -> float:
	var m := method(c.cultivator.method_id)
	if m.is_empty(): return 0.0
	var rate := float(m.get("rate", 1.0))
	match method_compatibility(c, c.cultivator.method_id):
		"excellent": rate *= 1.1
		"poor": rate *= 0.85
	return rate

## Meditation accumulation in QP per minute (S05, S29).
static func meditation_rate(c, qi_density: float, bonus: float) -> float:
	if c.cultivator.method_id == "": return 0.0
	var rate := float(ContentDB.curve("meditation_qp_per_min", 60)) * qi_density * method_rate(c) * stability_factor(c.cultivator.stability)
	rate *= 1.0 + bonus
	if is_body_stage(c.cultivator.realm_key): rate *= float(ContentDB.curve("meditation_body_stage_factor", 0.3))
	if c.cultivator.consolidation_penalty: rate *= 0.5
	return rate

## QP granted by a kill (S13 gap factor, S29 kill yield).
static func kill_qp(player_level: int, enemy_level: int, role: String) -> float:
	var base := float(ContentDB.curve("kill_qp", 22)) * float(ContentDB.curve("kill_role_mult.%s" % role, 1))
	return base * gap_factor(enemy_level - player_level)

static func gap_factor(diff: int) -> float:
	for row in ContentDB.stat_const("kill_gap_factor", []):
		if diff >= int(row.min_diff): return float(row.mult)
	return 0.1

static func body_xp_needed(body_level: int) -> float:
	return float(ContentDB.curve("body_xp_per_level", 40)) * body_level

static func kill_body_xp(enemy_level: int) -> float:
	return float(ContentDB.curve("kill_body_xp", 1)) + floor(enemy_level / 5.0) * float(ContentDB.curve("kill_body_xp_per_5_levels", 1))

static func mastery_needed(tier: int) -> float:
	return float(ContentDB.curve("mastery_points", 100)) * pow(2.0, tier - 1)

static func dao_tier_for(insight: float) -> int:
	var tiers: Array = ContentDB.curve("dao_tiers", [])
	var tier := 0
	for i in tiers.size():
		if insight >= float(tiers[i]): tier = i + 1
	return tier

static func stored_qi_cap(c) -> float:
	return c.cultivator.need() * float(ContentDB.curve("stored_qi_cap_stages", 1.0))

## Where the realm's major breakthrough spec lives (on the key before the next realm).
static func breakthrough_spec(key: String) -> Dictionary:
	return realm(key).get("major_breakthrough", {})

static func is_major(key: String) -> bool:
	return not breakthrough_spec(key).is_empty()

## Risk word index from counts (S05): +1 per unmet soft, +1 unstable, +1 per untreated
## injury, -1 per support item, -1 in a retreat room; floor Low, ceiling Severe.
static func risk_index(soft_unmet: int, unstable: bool, injuries: int, supports: int, retreat: bool) -> int:
	var r := soft_unmet + (1 if unstable else 0) + injuries - supports - (1 if retreat else 0)
	return clampi(r, 0, 3)

static func risk_word(index: int) -> String:
	var words: Array = ContentDB.curve("risk_words", ["low", "moderate", "high", "severe"])
	return str(words[clampi(index, 0, words.size() - 1)])

static func success_chance(word: String) -> float:
	return float(ContentDB.curve("risk_success.%s" % word, 0.5))

## Choose a failure from the unmet requirement causes (or energy instability).
static func pick_failure(rng: RandomNumberGenerator, unmet_causes: Array, realm_key: String) -> String:
	var candidates: Array = []
	for f in ContentDB.all("failures"):
		if f.id == "interruption": continue
		if f.has("from_realm") and not at_least(realm_key, str(f.from_realm)): continue
		var cause := str(f.cause)
		if cause in unmet_causes or (cause == "structure_body" and "structure" in unmet_causes):
			candidates.append(f.id)
	if candidates.is_empty(): return "energy_instability"
	return candidates[rng.randi_range(0, candidates.size() - 1)]

static func failure_loss(rng: RandomNumberGenerator, failure_id: String) -> float:
	var f := ContentDB.entry("failures", failure_id)
	var loss: Array = f.get("loss", [0.1, 0.3])
	return rng.randf_range(float(loss[0]), float(loss[1]))

## Offline seclusion gains (S07): meditation rate × 0.1 × minutes, capped.
static func offline_minutes(elapsed_s: float, cap_h: float) -> Dictionary:
	var minutes := elapsed_s / 60.0
	var cap := cap_h * 60.0
	return {"minutes": minf(minutes, cap), "capped": minutes > cap}

static func meridian_points_for_level(lv: int) -> int:
	var pts := 0
	for row in ContentDB.stat_const("meridian_points_per_level", []):
		if lv >= int(row.from_level): pts = int(row.points)
	return pts

static func energy_multiplier(energy: String, purity: int) -> float:
	var e := float(ContentDB.stat_const("energy_multiplier.%s" % energy, 1.0))
	if energy == "true_qi": e *= 1.0 + float(ContentDB.stat_const("purity_bonus_per_grade", 0.025)) * (9 - purity)
	return e

static func technique_slot_count(c) -> int:
	var n := 0
	for rule in [["technique_slots_2", 2], ["technique_slots_4", 4], ["technique_page_2", 6], ["technique_slots_8", 8]]:
		if Unlocks.is_unlocked(c.id, rule[0]): n = rule[1]
	return n
