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

## S48 body ladder (body_tiers.json): 0 for a mortal body, then 1 Copper, 2 Iron, 3 Jade, 4 Gold.
static func body_tier_index(cu) -> int:
	if str(cu.body_tier) == "mortal": return 0
	var list := ContentDB.all("body_tiers")
	for i in list.size():
		if str(list[i].id) == str(cu.body_tier): return i + 1
	return 0

## The next rung of the body ladder, or {} at the top.
static func next_body_tier(cu) -> Dictionary:
	var list := ContentDB.all("body_tiers")
	var i := body_tier_index(cu)
	return list[i] if i < list.size() else {}

## What the next rung still needs: {level, trial, bath} each true when done. A tier is reached with all three.
static func body_tier_needs(cu) -> Dictionary:
	var t := next_body_tier(cu)
	if t.is_empty(): return {}
	return {"tier": str(t.id), "level": int(cu.body_level) >= int(t.need), "trial": str(t.id) in cu.body_trials, "bath": str(t.id) in cu.body_baths}

## S48 Inner Arts: slots open with the realm (2 at Qi Unfurling 1, 3 at Heart Tempering 1, 4 at Spirit Awakening 1).
static func inner_art_slot_count(realm_key: String) -> int:
	var n := 0
	for row in ContentDB.config("inner_arts").get("slots", []):
		if at_least(realm_key, str(row[0])): n = int(row[1])
	return n

## S48: the stance held for the weapon in hand, or {} (a stance works only with its own family).
static func active_stance(c) -> Dictionary:
	var fam := str(StatRules.family(c).get("id", "fists"))
	var sid := str(c.cultivator.stances.get(fam, ""))
	var st := ContentDB.entry("stances", sid)
	return st if not st.is_empty() and str(st.get("family", "")) == fam else {}

## S48: the Inner Arts worn and working now (a weapon-linked art needs its weapon in hand).
static func active_inner_arts(c) -> Array:
	var out := []
	var fam := str(StatRules.family(c).get("id", "fists"))
	var n := inner_art_slot_count(c.cultivator.realm_key)
	for i in mini(n, c.cultivator.inner_arts.size()):
		var art := ContentDB.entry("inner_arts", str(c.cultivator.inner_arts[i]))
		if art.is_empty(): continue
		if str(art.get("family", "")) != "" and str(art.family) != fam: continue
		out.append(art)
	return out

## A number an active Inner Art or stance sets (sword_intent_max, reach_mult, backstab_crit, still_damage, parry_counter).
static func path_flag(c, key: String, fallback = null):
	for art in active_inner_arts(c):
		if (art.get("flags", {}) as Dictionary).has(key): return art.flags[key]
	var st := active_stance(c)
	if (st.get("flags", {}) as Dictionary).has(key): return st.flags[key]
	return fallback

## S48 technique grades: Common +0, Earth +10%, Heaven +20% to the base multiplier.
static func technique_grade_bonus(t: Dictionary) -> float:
	return float(ContentDB.stat_const("technique_grades", {}).get(str(t.get("grade", "common")), 0.0))

## S48 combos: the pair that `second` completes when `first` came within the window, or {}.
static func combo_for(first: String, second: String, since_s: float) -> Dictionary:
	if first == "" or since_s > float(ContentDB.config("combos").get("window_s", 1.0)): return {}
	for cb in ContentDB.all("combos"):
		if str(cb.first) == first and str(cb.second) == second: return cb
	return {}

## S48 heavenly tribulation: the row for a major breakthrough out of `from` ({} when none; the Heart Trial stays
## the set piece into Cloud Stride, so the first row is Cloud Stride 9).
static func tribulation_row(from: String) -> Dictionary:
	return ContentDB.entry("tribulations", from)

## Bolts in all: the row's bolts x waves, +1 per 25 heart demon and +1 per 100 sin, plus any a fate added.
static func tribulation_bolts(from: String, heart_demon: float, sin: int, extra := 0) -> int:
	var row := tribulation_row(from)
	if row.is_empty(): return 0
	var k := ContentDB.config("tribulations")
	return int(row.bolts) * int(row.get("waves", 1)) + int(floor(heart_demon / float(k.get("per_heart_demon", 25)))) \
		+ int(floor(float(sin) / float(k.get("per_sin", 100)))) + extra

## One bolt: 20% of max HP x (1 + sin / 500) x (1 + heart demon / 200); guarding halves it.
static func tribulation_damage(max_hp: float, sin: int, heart_demon: float, guarding: bool) -> float:
	var k := ContentDB.config("tribulations")
	var dmg := max_hp * float(k.get("damage_pct", 0.2)) * (1.0 + float(sin) / float(k.get("sin_div", 500))) * (1.0 + heart_demon / float(k.get("heart_div", 200)))
	return dmg * (float(k.get("guard", 0.5)) if guarding else 1.0)

## S48 Qi Deviation: a failed breakthrough at Severe risk, or with a Poor-compatibility method, deviates the Qi.
static func qi_deviates(risk: String, compatibility: String) -> bool:
	return risk == "severe" or compatibility == "poor"

## S48 fates: the cards this character may be offered now (available, requirements met).
static func fate_pool(ctx: Dictionary) -> Array:
	var out := []
	for f in ContentDB.all("fates"):
		if not f.get("available", true): continue
		if f.has("requires") and not RequirementRules.passes(f.requires, ctx): continue
		out.append(f)
	return out

## Draw `n` distinct cards by weight on the given stream.
static func draw_fates(pool: Array, n: int, rng: RandomNumberGenerator) -> Array:
	var left := pool.duplicate()
	var out := []
	while out.size() < n and not left.is_empty():
		var pick := Rng.weighted(rng, left)
		if pick.is_empty(): break
		out.append(str(pick.id))
		left.erase(pick)
	return out

## S48 named roots: the element affinities (revealed at Bone Forging 7) read as one root name.
## Returns "" while they are hidden, else heavenly, true, mixed, mutated or faint.
static func root_name(cu) -> String:
	var k: Dictionary = ContentDB.stat_const("roots", {})
	var counts_at := float(k.get("counts_at", 0.05))
	var values := {}
	for key in cu.aptitude:
		if not str(key).begins_with("element_"): continue
		var ap: Dictionary = cu.aptitude[key]
		if not ap.get("revealed", false): return ""
		values[str(key).trim_prefix("element_")] = float(ap.get("value", 0.0))
	if values.is_empty(): return ""
	var counting := 0
	var above := 0
	var best := ""
	for el in values:
		var v: float = values[el]
		if v >= counts_at - 0.0001: counting += 1
		if v > float(k.get("heavenly_above", 0.10)) + 0.0001: above += 1
		if best == "" or v > float(values[best]): best = el
	if best in k.get("mutated", ["thunder", "ice", "wind"]) and float(values[best]) >= counts_at - 0.0001: return "mutated"
	if above == 1: return "heavenly"
	if counting >= int(k.get("mixed_from", 4)): return "mixed"
	if counting >= int(k.get("true_from", 2)): return "true"
	return "faint"

## S48 Core Forging (Heart Tempering 9 -> Cloud Stride 1): the five preparation points and whether each is met.
## `room` is the room the breakthrough is taken in, `time_of_day` the clock's word, `pill_age_s` the seconds since
## the Heavenly Flame Pill (negative when never taken).
static func core_forging_points(c, room: Dictionary, time_of_day: String, pill_age_s: float) -> Array:
	var k: Dictionary = ContentDB.stat_const("core_forging", {})
	var cu = c.cultivator
	var m := method(cu.method_id)
	var aff := str(m.get("affinity", ""))
	var room_el := str(room.get("element", "none"))
	var vent := false
	for o in room.get("objects", []):
		if str(o.get("type", "")) == "earth_vent": vent = true
	var yy := str(m.get("yin_yang", ""))
	var hours: Array = k.get("yin_times" if yy == "yin" else "yang_times", [])
	return [
		{"id": "room_element", "met": aff != "" and (room_el == aff or (aff == "fire" and vent))},
		{"id": "hour", "met": yy != "" and time_of_day in hours},
		{"id": "composure", "met": c.pools.composure >= c.pools.get_max("composure") - 0.01},
		{"id": "residue", "met": cu.residue < 0.5},
		{"id": "flame_pill", "met": pill_age_s >= 0.0 and pill_age_s <= float(k.get("pill_window_s", 3600))},
	]

## The grade the core forms at: 9 minus the points that count (each met point counts on a roll under 80%),
## floor 5; a flawless Heaven's Cleansing is one more point, floor 4.
static func core_grade(points_counted: int, flawless: bool) -> int:
	var k: Dictionary = ContentDB.stat_const("core_forging", {})
	var grade := maxi(int(k.get("floor", 5)), int(k.get("start", 9)) - points_counted)
	if flawless: grade = maxi(int(k.get("flawless_floor", 4)), grade - 1)
	return grade

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
static func risk_index(soft_unmet: int, unstable: bool, injuries: int, supports: int, retreat: bool, extra := 0) -> int:
	var r := soft_unmet + (1 if unstable else 0) + injuries - supports - (1 if retreat else 0) + extra
	return clampi(r, 0, 3)

# ------------------------------------------------------------------ what pills cost over a life (gap report G1)
## The lifetime-resistance family of a pill, raw herb or beast core (S44 `family` field; "" = exempt).
static func pill_family(def: Dictionary) -> String:
	return str(def.get("family", ""))

## The resistance count of a family: every 5 doses add 1 (S44).
static func resistance_count(cu, family: String) -> int:
	var r = cu.pill_resistance.get(family, {})
	return int(r.get("count", 0)) if r is Dictionary else 0

## Lifetime pill resistance: a pill works at 1 / (1 + 0.25 x count) of its family (S44).
static func resistance_factor(cu, family: String) -> float:
	if family == "": return 1.0
	var step := float(ContentDB.stat_const("pill_life", {}).get("resistance_step", 0.25))
	return 1.0 / (1.0 + step * float(resistance_count(cu, family)))

## The great realm a realm key belongs to (qi_kindling_3 -> qi_kindling).
static func great_realm(realm_key: String) -> String:
	return str(ContentDB.realm(realm_key).get("realm", realm_key))

## Share of this major realm's Qi that came from pills and cores: pill_qp / total_qp (S44).
static func foundation_share(cu) -> float:
	var f: Dictionary = cu.foundation
	if str(f.get("realm", "")) != great_realm(cu.realm_key) or float(f.get("total_qp", 0.0)) <= 0.0: return 0.0
	return clampf(float(f.get("pill_qp", 0.0)) / float(f.total_qp), 0.0, 1.0)

static func foundation_hollow(cu) -> bool:
	return foundation_share(cu) > float(ContentDB.stat_const("pill_life", {}).get("hollow_share", 0.3))

## Accumulation lost to residue: -1% per 10, at most -10%.
static func residue_penalty(cu) -> float:
	var k: Dictionary = ContentDB.stat_const("pill_life", {})
	return minf(float(k.get("residue_cap_pct", 0.1)), floorf(cu.residue / float(k.get("residue_step", 10))) * float(k.get("residue_step_pct", 0.01)))

## Risk steps the heart demon adds at a major breakthrough (one per 25).
static func heart_demon_steps(cu) -> int:
	return int(floor(cu.heart_demon / float(ContentDB.stat_const("heart_demon", {}).get("step", 25))))

## Merit eases one major breakthrough in each great realm by a step (the ledger is the character's RelationsState).
static func merit_step(c) -> int:
	var need := int(ContentDB.config("karma").get("merit_step", 100))
	return 1 if c.relations.merit >= need and not c.relations.merit_used.has(great_realm(c.cultivator.realm_key)) else 0

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
