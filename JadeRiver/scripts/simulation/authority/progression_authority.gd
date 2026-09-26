class_name ProgressionAuthority
extends Authority
## S05–S10 · Owns the Realm track, stability, injuries, toxicity, body, soul,
## purity, Daos, methods, meridians, techniques (knowledge and mastery) and
## seclusion. Breakthroughs start only from the `start_breakthrough` intent —
## never from an offline, idle or automatic path.

const CHANNEL_S := 3.0
var channels: Dictionary = {}       # actor -> breakthrough in progress
var sec_accum: Dictionary = {}      # actor -> fractional second for per-second meditation ticks
var contemplate: Dictionary = {}    # actor -> dao id
var tribulations: Dictionary = {}   # actor -> heavenly tribulation under way (S48; not saved: leaving ends it)
var streaks: Dictionary = {}        # actor -> {n, t}: kills in a row (Blood Memory; Killing Intent grows from it)
var last_level: Dictionary = {}

func intents() -> Array:
	return ["start_meditation", "stop_meditation", "toggle_meditation", "start_breakthrough", "learn_method", "switch_method",
		"open_meridian", "reset_meridians", "equip_technique", "unequip_technique", "rank_up_technique", "set_contemplate",
		"enter_seclusion", "claim_offline", "use_treatment", "train_object", "attune_jade", "start_bath", "choose_fate", "equip_inner_art", "set_stance", "set_vow", "set_false_realm",
		"play_guqin", "solve_chess"]

func subscribe() -> void:
	GameEvents.subscribe("loadout_swapped", _on_loadout_swapped, 30)
	# S44: a pill whose effect is on loan (the Qi Flow Pill) pays it back when the buff wears off.
	GameEvents.subscribe("buff_expired", func(p): _on_buff_expired(p), 30)
	# S44: a furnace blast leaves a minor body injury.
	GameEvents.subscribe("furnace_blast", func(p): apply_injury(str(p.get("actor", "")), "body", 1), 30)
	GameEvents.subscribe("hit_landed", _on_hit_landed, 30)
	# S48 Ember Heart: every Fire pill refined counts.
	GameEvents.subscribe("craft_completed", _on_fire_pill, 30)
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 30)
	GameEvents.subscribe("player_gravely_wounded", _on_gravely_wounded, 30)
	GameEvents.subscribe("technique_used", _on_technique_used, 30)
	GameEvents.subscribe("object_hit", _on_object_hit, 30)
	GameEvents.subscribe("zone_entered", _on_zone_entered, 30)
	GameEvents.subscribe("room_entered", func(p): _refresh_attunement(game.character(str(p.get("actor", "")))), 30)
	GameEvents.subscribe("stats_changed", func(p): if "attunement_bonus" in p.get("changed_ids", []): _refresh_attunement(game.character(str(p.get("actor", "")))), 30)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"start_meditation": return start_meditation(c)
		"stop_meditation": return stop_meditation(c, str(intent.get("reason", "moved")))
		"toggle_meditation": return stop_meditation(c, "tapped") if c.cultivator.meditating else start_meditation(c)
		"play_guqin": return play_guqin(c, float(intent.get("score", 0.0)))
		"solve_chess": return solve_chess(c, str(intent.get("site", "")), str(intent.get("choice", "")))
		"start_breakthrough": return start_breakthrough(c, intent.get("support_items", []))
		"learn_method": return fail("taught_by_npc")
		"switch_method": return switch_method(c, str(intent.get("id", "")), bool(intent.get("use_conversion_pill", false)))
		"open_meridian": return open_meridian(c, str(intent.get("channel", "")))
		"reset_meridians": return reset_meridians(c)
		"equip_technique": return equip_technique(c, int(intent.get("slot", -1)), str(intent.get("id", "")))
		"unequip_technique": return equip_technique(c, int(intent.get("slot", -1)), "")
		"rank_up_technique": return rank_up_technique(c, str(intent.get("id", "")))
		"set_contemplate":
			if not Unlocks.is_unlocked(c.id, "insight_sites"): return fail("locked")
			contemplate[c.id] = str(intent.get("dao", ""))
			return ok()
		"enter_seclusion": return enter_seclusion(c, str(intent.get("focus", "accumulate")))
		"start_bath": return start_bath(c, str(intent.get("item", intent.get("recipe", ""))))
		"claim_offline": return claim_offline(c, float(intent.get("elapsed", 0.0)))
		"train_object": return fail("use_attack")
		"attune_jade": return attune_jade(c, str(intent.get("zone", "")), int(intent.get("index", -1)))
		"choose_fate": return choose_fate(c, str(intent.get("card", "")))
		"equip_inner_art": return equip_inner_art(c, int(intent.get("slot", -1)), str(intent.get("art", "")))
		"set_stance": return set_stance(c, str(intent.get("family", "")), str(intent.get("stance", "")))
		"set_vow": return set_vow(c, str(intent.get("vow", "")), bool(intent.get("on", true)))
		"set_false_realm": return set_false_realm(c, str(intent.get("realm", "")))
	return fail("unknown_intent")

# ------------------------------------------------------------------ meditation (S06)
func start_meditation(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "cultivate"): return fail("locked", {"text": Unlocks.locked_text("cultivate")})
	if c.cultivator.meditating: return ok()
	var st: ActorState = game.actor_state(c.id)
	if st != null and st.surface == null: return fail("airborne")
	if game.combat.is_busy(c.id): return fail("busy")
	if game.combat.is_stunned(c.id): return fail("stunned")
	if channels.has(c.id) or tribulations.has(c.id): return fail("breaking_through")
	c.cultivator.meditating = true
	c.cultivator.meditation_settle = float(ContentDB.curve("meditation.settle_s", 1.0))
	c.cultivator.meditation_spot = game.room_rt.room_id if game.room_rt else ""
	sec_accum[c.id] = 0.0
	emit("meditation_started", {"actor": c.id, "spot": c.cultivator.meditation_spot})
	return ok()

func stop_meditation(c, reason := "moved") -> Dictionary:
	if not c.cultivator.meditating: return ok()
	c.cultivator.meditating = false
	emit("meditation_stopped", {"actor": c.id, "reason": reason})
	return ok()

func meditation_context(c) -> Dictionary:
	var density := float(game.room_rt.def.get("qi_density", 1.0)) if game.room_rt else 1.0
	var spring := false
	var stone := ""
	var st: ActorState = game.actor_state(c.id)
	if game.room_rt and st:
		for o in game.room_rt.def.get("objects", []):
			var at: Array = o.get("at", [0, 0])
			if Vector2(float(at[0]), float(at[1])).distance_to(st.plane) > float(o.get("radius", 110)): continue
			if o.type == "qi_spring" and Unlocks.is_unlocked(c.id, "qi_springs"): spring = true
			if o.type == "insight_stone" and Unlocks.is_unlocked(c.id, "insight_sites"): stone = str(o.get("dao", "water"))
			if o.type == "gathering_formation": density += 0.5
	density += game.workshop.formation_effect(c, "qi_density")
	if spring: density *= float(ContentDB.curve("qi_spring_mult", 2))
	return {"density": density, "spring": spring, "stone": stone}

func accumulation_bonus(c) -> float:
	var bonus = c.stats.value("accumulation_rate")
	if ProgressionRules.realm_index(game.account.highest_realm) - ProgressionRules.realm_index(c.cultivator.realm_key) >= 2:
		bonus = (1.0 + bonus) * float(ContentDB.curve("ancestral_guidance", 1.5)) - 1.0
	bonus += 0.02 * game.account.legacy.size()
	bonus += game.pets.resonance(c)
	bonus += game.companions.paired_bonus(c)
	bonus -= ProgressionRules.residue_penalty(c.cultivator)   # residue does not drain on its own (G1)
	return bonus

func tick(delta: float) -> void:
	var c = game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	_tick_channel(c, delta)
	_tick_tribulation(c, delta)
	if cu.meditating:
		if cu.meditation_settle > 0.0:
			cu.meditation_settle -= delta
		else:
			sec_accum[c.id] = float(sec_accum.get(c.id, 0.0)) + delta
			while sec_accum[c.id] >= 1.0:
				sec_accum[c.id] -= 1.0
				_meditation_second(c)
	if cu.consolidation_left > 0.0:
		cu.consolidation_left = maxf(0.0, cu.consolidation_left - delta)
		if cu.consolidation_left <= 0.0:
			cu.consolidation_penalty = false
			if cu.state == "consolidating": cu.state = "accumulating"
			emit("consolidation_finished", {"actor": c.id})
	if cu.breakthrough_cooldown > 0.0: cu.breakthrough_cooldown = maxf(0.0, cu.breakthrough_cooldown - delta)
	if cu.epiphany_cooldown > 0.0: cu.epiphany_cooldown = maxf(0.0, cu.epiphany_cooldown - delta)   # two hours of play (S48)
	_tick_injuries(c, delta, 3.0 if cu.meditating else 1.0)
	if cu.toxicity > 0.0:
		var drain := float(ContentDB.stat_const("toxicity.drain_per_min", 1)) / 60.0 * delta
		if cu.meditating: drain *= float(ContentDB.stat_const("toxicity.meditate_drain_mult", 2))
		cu.toxicity = maxf(0.0, cu.toxicity - drain)
	if cu.state == "bottleneck":
		cu.bottleneck_seconds += delta
		var hint_s := float(ContentDB.curve("bottleneck_hint_minutes", 20)) * 60.0
		if cu.bottleneck_seconds >= hint_s and not c.quests.has_flag("hint_" + cu.realm_key):
			game.quest.apply_flag(c.id, "hint_" + cu.realm_key)
			game.mail.apply_send(c.id, "mentor_hint", [], {"realm": ContentDB.name_of("realms", cu.realm_key)})

func _meditation_second(c) -> void:
	var cu: CultivatorState = c.cultivator
	var mc := meditation_context(c)
	var mult := 2.0 if mc.spring else 1.0
	var regen: Dictionary = ContentDB.stat_const("regen_per_s", {})
	var m := float(regen.get("meditate_mult", 8))
	var gains := {}
	gains.hp = c.pools.max_hp * c.stats.value("hp_regen") * m * mult
	game.combat.apply_resource_change(c.id, "hp", gains.hp, "meditation")
	if c.pools.max_qi > 0:
		gains.qi = c.pools.max_qi * c.stats.value("qi_regen") * m * mult
		game.combat.apply_resource_change(c.id, "qi", gains.qi, "meditation")
	if c.pools.max_soul > 0:
		game.combat.apply_resource_change(c.id, "soul", c.pools.max_soul * c.stats.value("soul_regen") * m * mult, "meditation")
	if Unlocks.is_unlocked(c.id, "composure"):
		game.combat.apply_resource_change(c.id, "composure", 100.0 / float(ContentDB.stat_const("composure.meditate_full_s", 5)), "meditation")
	game.combat.apply_resource_change(c.id, "hollowing", -float(ContentDB.stat_const("hollowing.decay_per_min", 1)) * float(ContentDB.stat_const("hollowing.meditate_mult", 3)) / 60.0, "meditation")
	if Unlocks.is_unlocked(c.id, "cultivation"):
		var rate := ProgressionRules.meditation_rate(c, float(mc.density), accumulation_bonus(c))
		gains.qp = rate / 60.0
		apply_progress(c.id, gains.qp, "meditation")
	if Unlocks.is_unlocked(c.id, "foundation") and cu.stability != "stable" and cu.stability != "solid":
		cu.stability_progress += 1.0
		if cu.stability_progress >= float(ContentDB.curve("stability_step_s", 120)):
			cu.stability_progress = 0.0
			_step_stability(c, 1)
	if c.pools.max_qi > 0 and ProgressionRules.at_least(cu.realm_key, "cloud_stride_1"):
		apply_purity(c.id, float(ContentDB.curve("purity_meditate_per_hour", 10)) / 3600.0)
	if c.pools.max_soul > 0:
		apply_soul(c.id, float(ContentDB.curve("soul_meditate_per_hour", 10)) / 3600.0)
	if mc.stone != "":
		var site := float(ContentDB.stat_const("gates", {}).get("insight_site_mult", 2.0)) if StatRules.gate_flag(c, "insight_sites_double") else 1.0   # S10 Insight 50
		apply_insight(c.id, mc.stone, float(ContentDB.curve("insight_stone_per_min", 20)) / 60.0 * mult * site, "insight_stone")
	if cu.heart_demon > 0.0:
		apply_heart_demon(c.id, -float(ContentDB.stat_const("heart_demon", {}).get("meditate_drain_per_min", 0.2)) / 60.0, "meditation")   # -1 per 5 min (S48)
	if str(c.position.get("room", "")) == "cf_falls_pool" and Clock.time_of_day() == "night": _falls_pool_second(c)
	emit("meditation_tick", {"actor": c.id, "gains": gains, "spring": mc.spring, "paired": game.companions.paired_bonus(c) > 0.0})

func _step_stability(c, direction: int) -> void:
	var order: Array = ContentDB.curve("stability_order", ["unstable", "settling", "stable", "solid"])
	var i := order.find(c.cultivator.stability)
	var target := clampi(i + direction, 0, 2 if direction > 0 else order.size() - 1)
	if direction > 0 and i >= 2: return
	if target == i: return
	c.cultivator.stability = order[target]
	emit("stability_changed", {"actor": c.id, "word": c.cultivator.stability})

func _tick_injuries(c, delta: float, mult: float) -> void:
	var cu: CultivatorState = c.cultivator
	if cu.injuries.is_empty(): return
	if cu.stability == "unstable": mult /= float(ContentDB.curve("injuries.unstable_slow", 1.5))
	for kind in cu.injuries.keys():
		var inj: Dictionary = cu.injuries[kind]
		inj.time_left = float(inj.time_left) - delta * mult
		if inj.time_left <= 0.0:
			inj.severity = int(inj.severity) - 1
			if inj.severity <= 0:
				cu.injuries.erase(kind)
				emit("injury_healed", {"actor": c.id, "kind": kind, "severity": 0})
			else:
				inj.time_left = _heal_time(int(inj.severity))
				emit("injury_healed", {"actor": c.id, "kind": kind, "severity": inj.severity})

func _heal_time(severity: int) -> float:
	var times: Dictionary = ContentDB.curve("injuries.natural_heal_s", {})
	return float(times.get(["minor", "moderate", "severe"][clampi(severity - 1, 0, 2)], 600))

# ------------------------------------------------------------------ accumulation (S05)
## S18 attunement: jades plus small bonuses (character state, per zone) against what the room asks.
func attunement_required(room_id: String) -> float:
	var room := ContentDB.room(room_id)
	if room.has("attunement_required"): return float(room.attunement_required)
	if room.get("safe", false): return 0.0   # towns, camps and halls ask nothing of the blood
	var att = ContentDB.zone_of_room(room_id).get("attunement")
	return float((att.get("required", [0]) as Array)[0]) if att is Dictionary else 0.0

## The attunement the character brings to where they stand: jades (and permanent bonuses) for
## that zone, plus temporary bonuses such as a Storm Blood Pill.
func attunement_value(c, zone_id: String) -> float:
	if c == null or zone_id == "": return 0.0
	return float(c.cultivator.attunement.get(zone_id, 0.0)) + c.stats.value("attunement_bonus") + game.sect.outpost_attunement(zone_id)

func attunement_factors(c) -> Dictionary:
	var room_id := str(c.position.get("room", ""))
	var zone_id := str(ContentDB.zone_of_room(room_id).get("id", ""))
	return CombatRules.attunement_factors(attunement_value(c, zone_id), attunement_required(room_id))

var last_attune: Dictionary = {}   # actor -> "dealt|taken" last emitted, so rooms only re-emit on a change

func _emit_attunement(c) -> void:
	var room_id := str(c.position.get("room", ""))
	var zone_id := str(ContentDB.zone_of_room(room_id).get("id", ""))
	var f := attunement_factors(c)
	last_attune[c.id] = "%.3f|%.3f" % [f.dealt, f.taken]
	emit("attunement_changed", {"actor": c.id, "zone": zone_id, "value": attunement_value(c, zone_id),
		"required": attunement_required(room_id), "dealt": f.dealt, "taken": f.taken})

func _refresh_attunement(c) -> void:
	if c == null: return
	var f := attunement_factors(c)
	if str(last_attune.get(c.id, "1.000|1.000")) != "%.3f|%.3f" % [f.dealt, f.taken]: _emit_attunement(c)

func _on_zone_entered(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	_emit_attunement(c)

## S18: four attunement jades per zone, each levelled with that zone's shards. The zone's
## attunement total is the sum of its jades (times their value per level).
func jade_levels(c, zone_id: String) -> Array:
	var att = ContentDB.zone(zone_id).get("attunement")
	var n := int((att.get("jades", []) as Array).size()) if att is Dictionary else 0
	var levels: Array = (c.cultivator.attunement_jades.get(zone_id, []) as Array).duplicate()
	while levels.size() < n: levels.append(0)
	return levels

func jade_cost(zone_id: String, level: int) -> int:
	var att = ContentDB.zone(zone_id).get("attunement")
	var cost: Dictionary = att.get("cost", {}) if att is Dictionary else {}
	return int(cost.get("base", 1)) + int(cost.get("per_level", 1)) * level

func attune_jade(c, zone_id: String, index: int) -> Dictionary:
	var att = ContentDB.zone(zone_id).get("attunement")
	if not (att is Dictionary): return fail("no_attunement")
	if not Unlocks.is_unlocked(c.id, str(att.get("unlock", ""))): return fail("locked", {"text": Unlocks.locked_text(str(att.get("unlock", "")))})
	var levels := jade_levels(c, zone_id)
	if index < 0 or index >= levels.size(): return fail("bad_jade")
	var level := int(levels[index])
	if level >= int(att.get("jade_max", 15)): return fail("maxed", {"text": Tx.t("sim.progression.jade_at_its_peak")})
	var cost := jade_cost(zone_id, level)
	var shard := str(att.get("shard", ""))
	if c.inventory.count(shard) < cost:
		return fail("missing", {"text": Tx.t("sim.progression.jade_needs_shards") % [cost, ContentDB.item_name(shard)]})
	game.inventory.apply_remove(c.id, shard, cost, "attune")
	levels[index] = level + 1
	c.cultivator.attunement_jades[zone_id] = levels
	var total := 0.0
	for l in levels: total += float(l) * float(att.get("jade_value", 1.0))
	c.cultivator.attunement[zone_id] = total
	emit("system_used", {"actor": c.id, "system": "attune_jade"})
	_emit_attunement(c)
	return ok({"zone": zone_id, "index": index, "level": level + 1, "attunement": total})

## The bar is full (World adds zone_ceiling_reached when the land is the limit, S18).
func _bottleneck(c, realm: String) -> void:
	emit("bottleneck_reached", {"actor": c.id, "realm_key": realm, "major": ProgressionRules.is_major(realm), "requirements": query_requirements(c)})

func at_zone_ceiling(c) -> bool:
	var zone := ContentDB.zone_of_room(c.position.get("room", ""))
	return str(zone.get("ceiling", "")) == c.cultivator.realm_key

## Add Qi points from any source (meditation, kills, pills, quests, idle, offline).
func apply_progress(actor_id: String, amount: float, source: String, pct_of_need := 0.0) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var n := cu.need()
	amount += pct_of_need * n
	if amount <= 0.0 or n <= 0.0: return
	var before_level := ProgressionRules.level(c)
	_track_foundation(cu, amount, source)
	if cu.state == "bottleneck":
		var factor := float(ContentDB.curve("ceiling_stored_qi_mult", 0.25)) if at_zone_ceiling(c) else 1.0
		cu.stored_qi = minf(ProgressionRules.stored_qi_cap(c), cu.stored_qi + amount * factor)
	else:
		cu.qp += amount
		if cu.qp >= n:
			var surplus := cu.qp - n
			cu.qp = n
			cu.state = "bottleneck"
			cu.stored_qi = minf(ProgressionRules.stored_qi_cap(c), cu.stored_qi + surplus)
			cu.bottleneck_seconds = 0.0
			_bottleneck(c, cu.realm_key)
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": source, "amount": amount})
	var after_level := ProgressionRules.level(c)
	if after_level != before_level: _levels_gained(c, before_level, after_level)

## Foundation (G1): how much of this great realm's Qi came from pills, raw herbs and cores.
func _track_foundation(cu: CultivatorState, amount: float, source: String) -> void:
	var gr := ProgressionRules.great_realm(cu.realm_key)
	if str(cu.foundation.get("realm", "")) != gr: cu.foundation = {"realm": gr, "total_qp": 0.0, "pill_qp": 0.0}
	cu.foundation.total_qp = float(cu.foundation.total_qp) + amount
	# Qi from a pill of a resistance family, a raw herb or a beast core is not the cultivator's own (S44).
	if source.begins_with("item:"):
		var def := ContentDB.item(source.substr(5))
		if ProgressionRules.pill_family(def) != "" or def.has("core"):
			cu.foundation.pill_qp = float(cu.foundation.pill_qp) + amount
			emit("foundation_changed", {"actor": cu_owner(cu), "share": ProgressionRules.foundation_share(cu)})

## The character that owns a cultivator state (events carry the actor id).
func cu_owner(cu: CultivatorState) -> String:
	for c in game.characters.values():
		if c.cultivator == cu: return c.id
	return game.active_id

## One dose of a resistance family (S44): every 5 doses add 1 to its count.
func apply_pill_dose(actor_id: String, family: String) -> void:
	var c = game.character(actor_id)
	if c == null or family == "": return
	var r: Dictionary = c.cultivator.pill_resistance.get(family, {"count": 0, "doses": 0})
	r.doses = int(r.get("doses", 0)) + 1
	var per := int(ContentDB.stat_const("pill_life", {}).get("doses_per_count", 5))
	if int(r.doses) >= per:
		r.doses = int(r.doses) - per
		r.count = int(r.get("count", 0)) + 1
	c.cultivator.pill_resistance[family] = r
	emit("pill_resistance_changed", {"actor": c.id, "family": family, "count": int(r.count), "doses": int(r.doses)})

func _levels_gained(c, from_level: int, to_level: int) -> void:
	for lv in range(from_level + 1, to_level + 1):
		if lv > c.cultivator.meridian_levels_granted:
			c.cultivator.unspent_meridian_points += ProgressionRules.meridian_points_for_level(lv)
			c.cultivator.meridian_levels_granted = lv
	emit("level_changed", {"actor": c.id, "level": to_level})

func query_requirements(c) -> Array:
	var spec := ProgressionRules.breakthrough_spec(c.cultivator.realm_key)
	if spec.is_empty(): return []
	return RequirementRules.check(spec.get("requirements", {}), game.ctx(c))

## Breakthrough preview (query only): target, hard/soft results, risk word and reasons.
func query_breakthrough(c, support_items: Array = []) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	var spec := ProgressionRules.breakthrough_spec(cu.realm_key)
	var to := str(spec.get("to", ContentDB.next_realm(cu.realm_key)))
	var major := not spec.is_empty()
	var results: Array = RequirementRules.check(spec.get("requirements", {}), game.ctx(c)) if major else []
	var hard_ok := true
	for r in results:
		if r.hard and not r.ok: hard_ok = false
	var zone_ok := true
	if major:
		var zone := ContentDB.zone_of_room(c.position.get("room", ""))
		if not zone.is_empty() and ContentDB.realm_position(str(zone.get("ceiling", "world_genesis"))) < ContentDB.realm_position(to):
			zone_ok = false
			results.append({"ok": false, "hard": true, "cause": "environment", "text": Tx.t("sim.progression.this_land_cannot_support") % ContentDB.name_of("realms", to), "fix": "page:world_map", "kind": "zone_supports"})
			hard_ok = false
	var supports := 0
	var supports_used: Array = []   # only these are consumed and counted at the attempt
	var reasons: Array = []
	var failed := int(cu.support_failures.get(cu.realm_key, 0))
	var fail_limit := int(ContentDB.stat_const("pill_life", {}).get("support_fail_limit", 2))
	for item_id in support_items:
		var sup: Dictionary = ContentDB.item(str(item_id)).get("support", {})
		if sup.is_empty() or c.inventory.count(str(item_id)) <= 0: continue
		if sup.has("event") and str(sup.event) != str(spec.get("event", "")): continue
		# After two failed attempts at this breakthrough, support pills no longer answer it (S44).
		if failed >= fail_limit:
			reasons.append(Tx.t("sim.progression.support_spent") % ContentDB.item_name(str(item_id)))
			continue
		supports += 1
		supports_used.append(str(item_id))
		reasons.append(Tx.t("sim.progression.lowers_risk") % ContentDB.item_name(str(item_id)))
	# What the character's past adds (G1): a hollow foundation is an unmet soft requirement,
	# each 25 heart demon a step, and merit eases one breakthrough per great realm.
	var hollow := major and ProgressionRules.foundation_hollow(cu)
	if hollow:
		results.append({"ok": false, "hard": false, "cause": "structure", "kind": "foundation", "fix": "page:cultivation",
			"text": Tx.t("sim.progression.foundation_hollow") % int(round(ProgressionRules.foundation_share(cu) * 100.0))})
	var demon_steps := ProgressionRules.heart_demon_steps(cu) if major else 0
	if demon_steps > 0: reasons.append(Tx.t("sim.progression.heart_demons") % [int(cu.heart_demon), demon_steps])
	var merit := ProgressionRules.merit_step(c) if major else 0
	if merit > 0: reasons.append(Tx.t("sim.progression.merit_eases") % c.relations.merit)
	var soft := RequirementRules.soft_unmet(results)
	if soft > 0: reasons.append(Tx.t("sim.progression.unmet_soft_requirement") % soft)
	var unstable := cu.stability == "unstable"
	if unstable: reasons.append(Tx.t("sim.progression.your_foundation_is_unstable"))
	if not cu.injuries.is_empty(): reasons.append(Tx.t("sim.progression.untreated_injury") % cu.injuries.size())
	var retreat := bool(game.room_rt.def.get("retreat", false)) if game.room_rt else false
	if retreat: reasons.append(Tx.t("sim.progression.retreat_room"))
	var guarded = game.workshop.formation_effect(c, "breakthrough_risk_step") < 0.0
	if guarded: reasons.append(Tx.t("sim.progression.guard_formation"))
	# S49: a Dao Companion in the party holds the joint breakthrough-support slot.
	var held: int = game.relations.bond_support(c) if major else 0
	if held > 0: reasons.append(Tx.t("sim.progression.dao_companion_holds") % ContentDB.name_of("companions", str(c.relations.bonds.dao_companion)))
	var word := ProgressionRules.risk_word(ProgressionRules.risk_index(soft, unstable, cu.injuries.size(), mini(supports, 3) + (1 if guarded else 0) + held, retreat,
		demon_steps - merit)) if major else "none"
	var can := cu.state == "bottleneck" and hard_ok and cu.breakthrough_cooldown <= 0.0 and not channels.has(c.id)
	var blocked := ""
	if cu.state != "bottleneck": blocked = Tx.t("sim.progression.keep_accumulating") % int(cu.progress_fraction() * 100)
	elif cu.breakthrough_cooldown > 0.0: blocked = Tx.t("sim.progression.your_mind_needs_rest_ds") % int(cu.breakthrough_cooldown)
	elif not hard_ok: blocked = Tx.t("sim.progression.a_hard_requirement_is_unmet")
	return {"from": cu.realm_key, "to": to, "major": major, "results": results, "risk": word, "reasons": reasons,
		"success": ProgressionRules.success_chance(word) if major else 1.0, "can": can, "blocked": blocked,
		"event": str(spec.get("event", "")) if major else "", "zone_ok": zone_ok, "hollow": hollow, "heart_demon_steps": demon_steps, "merit": merit, "supports_used": supports_used}

func start_breakthrough(c, support_items: Array) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "cultivation"): return fail("locked")
	if game.room_rt and game.room_rt.event.get("active", false): return fail("event_running")
	if channels.has(c.id) or tribulations.has(c.id): return fail("breaking_through")
	var q := query_breakthrough(c, support_items)
	if not q.can: return fail("cannot", {"text": q.blocked, "query": q})
	stop_meditation(c, "breakthrough")
	if not q.major:
		_advance(c, str(q.to), false)
		return ok({"result": "success", "to": q.to})
	# Consume hard material items and support items at the attempt (S05).
	var spec := ProgressionRules.breakthrough_spec(c.cultivator.realm_key)
	for cond in spec.get("requirements", {}).get("all", []):
		if cond.get("kind") == "item_owned" and cond.get("consume", false) and c.inventory.count(str(cond.item)) >= int(cond.get("count", 1)):
			game.inventory.apply_remove(c.id, str(cond.item), int(cond.get("count", 1)), "breakthrough")
	var used: Array = []
	for item_id in q.get("supports_used", []):
		if used.size() >= 3: break
		if c.inventory.count(str(item_id)) > 0:
			game.inventory.apply_remove(c.id, str(item_id), 1, "breakthrough_support")
			used.append(item_id)
	var unmet_causes: Array = []
	for r in q.results:
		if not r.ok: unmet_causes.append(r.cause)
	var hd: Dictionary = ContentDB.stat_const("heart_demon", {})
	if used.size() >= int(hd.get("forced_supports", 2)): apply_heart_demon(c.id, float(hd.get("forced_breakthrough", 5)), "forced_breakthrough")
	if int(q.get("merit", 0)) > 0: game.relations.apply_merit_used(c.id, ProgressionRules.great_realm(c.cultivator.realm_key))
	var bonus := _spend_fate_next(c, "breakthrough_bonus")   # S48 Scar of Failure: the next attempt only
	channels[c.id] = {"to": q.to, "risk": q.risk, "remaining": CHANNEL_S, "causes": unmet_causes, "used": used, "from": c.cultivator.realm_key,
		"hollow": bool(q.get("hollow", false)), "bonus": bonus}
	emit("breakthrough_started", {"actor": c.id, "from": c.cultivator.realm_key, "to": q.to, "risk": q.risk, "duration": CHANNEL_S})
	return ok({"result": "channeling", "risk": q.risk})

func _tick_channel(c, delta: float) -> void:
	if not channels.has(c.id): return
	var ch: Dictionary = channels[c.id]
	ch.remaining = float(ch.remaining) - delta
	if ch.remaining > 0.0: return
	channels.erase(c.id)
	# S48: from Cloud Stride on, the heavens test a major breakthrough before it is settled.
	var from0 := str(ch.get("from", c.cultivator.realm_key))
	if not ProgressionRules.tribulation_row(from0).is_empty():
		_start_tribulation(c, ch)
		return
	_settle_breakthrough(c, ch)

## The roll that decides a major breakthrough, after the channel (and any tribulation) is through.
func _settle_breakthrough(c, ch: Dictionary) -> void:
	var rng := Rng.stream(c.id, "breakthrough")
	# The Prologue's first step on Lu's boat is taught, not gambled (realm flag `guaranteed`).
	var guaranteed := bool(ProgressionRules.breakthrough_spec(str(ch.get("from", c.cultivator.realm_key))).get("guaranteed", false))
	if guaranteed or rng.randf() < ProgressionRules.success_chance(str(ch.risk)) + float(ch.get("bonus", 0.0)):
		_advance(c, str(ch.to), true)
		if not guaranteed: _offer_fates(c)
	else:
		var from := str(ch.get("from", c.cultivator.realm_key))
		if not (ch.get("used", []) as Array).is_empty():
			c.cultivator.support_failures[from] = int(c.cultivator.support_failures.get(from, 0)) + 1
		# A hollow foundation gives way where it is weakest (G1).
		var failure := "weak_foundation" if ch.get("hollow", false) and ContentDB.has_entry("failures", "weak_foundation") \
			else ProgressionRules.pick_failure(rng, ch.causes, c.cultivator.realm_key)
		_fail_breakthrough(c, failure, rng)
		_maybe_deviate(c, str(ch.risk))

## S48 Qi Deviation: a failure at Severe risk, or on a Poor-compatibility method, sends the Qi astray for 10 minutes.
func _maybe_deviate(c, risk: String) -> void:
	if not ProgressionRules.qi_deviates(risk, ProgressionRules.method_compatibility(c, c.cultivator.method_id)): return
	game.combat.apply_status(c.id, "qi_deviation", float(ContentDB.stat_const("qi_deviation", {}).get("duration_s", 600)), 1.0)
	if not game.account.codex.has("qi_deviation"): game.quest.apply_codex("qi_deviation")
	emit("qi_deviation", {"actor": c.id, "risk": risk, "duration": float(ContentDB.stat_const("qi_deviation", {}).get("duration_s", 600))})

# ------------------------------------------------------------------ heavenly tribulation (S48)
## The cloud gathers over the room: bolts in turn, each telegraphed by a ring a second before it strikes where the
## ring was drawn. Timing comes from the breakthrough stream, the rings' places from the combat stream.
func _start_tribulation(c, ch: Dictionary) -> void:
	var cu: CultivatorState = c.cultivator
	var from := str(ch.get("from", cu.realm_key))
	var k := ContentDB.config("tribulations")
	var extra := int(_spend_fate_next(c, "tribulation_bolts"))
	var total := ProgressionRules.tribulation_bolts(from, cu.heart_demon, c.relations.sin, extra)
	var row := ProgressionRules.tribulation_row(from)
	var per_wave := int(row.bolts)
	var rng := Rng.stream(c.id, "breakthrough")
	var times: Array = []
	var at := float(k.get("first_s", 2.0))
	for i in total:
		if i > 0 and i % per_wave == 0 and i < int(row.bolts) * int(row.get("waves", 1)): at += float(k.get("wave_pause_s", 3.0))
		times.append(at)
		var gap: Array = k.get("gap_s", [0.7, 1.4])
		at += float(k.get("warn_s", 1.0)) + rng.randf_range(float(gap[0]), float(gap[1]))
	tribulations[c.id] = {"ch": ch, "times": times, "total": total, "index": 0, "t": 0.0, "warn": {}, "struck": 0, "absorbed": 0,
		"waves": int(row.get("waves", 1)), "per_wave": per_wave, "room": game.room_rt.room_id if game.room_rt else ""}
	if not game.account.codex.has("heavenly_tribulation"): game.quest.apply_codex("heavenly_tribulation")
	emit("tribulation_started", {"actor": c.id, "from": from, "to": str(ch.to), "bolts": total, "waves": int(row.get("waves", 1))})

func _tick_tribulation(c, delta: float) -> void:
	if not tribulations.has(c.id): return
	var tr: Dictionary = tribulations[c.id]
	var k := ContentDB.config("tribulations")
	# Leaving the room breaks the rite: the Qi scatters as though interrupted.
	if game.room_rt == null or game.room_rt.room_id != str(tr.room):
		_end_tribulation(c, false, "interruption")
		return
	tr.t = float(tr.t) + delta
	var warn_s := float(k.get("warn_s", 1.0))
	# The ring for the next bolt: drawn a second early, where the character stands (give or take).
	if int(tr.index) < int(tr.total) and (tr.warn as Dictionary).is_empty() and float(tr.t) >= float(tr.times[tr.index]):
		var st: ActorState = game.actor_state(c.id)
		var here: Vector2 = st.plane if st else Vector2(float(c.position.get("x", 600)), float(c.position.get("y", 860)))
		var rng := Rng.stream(c.id, "combat")
		var spread := float(k.get("spread", 60))
		var spot := here + Vector2(rng.randf_range(-spread, spread), rng.randf_range(-spread, spread) * 0.3)
		tr.warn = {"x": spot.x, "y": spot.y, "left": warn_s}
		emit("tribulation_bolt", {"actor": c.id, "index": int(tr.index), "total": int(tr.total), "phase": "warn", "x": spot.x, "y": spot.y, "warn_s": warn_s})
	if not (tr.warn as Dictionary).is_empty():
		tr.warn.left = float(tr.warn.left) - delta
		if float(tr.warn.left) <= 0.0:
			var spot2 := Vector2(float(tr.warn.x), float(tr.warn.y))
			tr.warn = {}
			var res: Dictionary = game.combat.apply_tribulation_strike(c, spot2, float(k.get("radius", 80)), float(k.get("depth", 45)))
			tr.index = int(tr.index) + 1
			if res.get("hit", false): tr.struck = int(tr.struck) + 1
			if res.get("absorbed", false): tr.absorbed = int(tr.absorbed) + 1
			emit("tribulation_bolt", {"actor": c.id, "index": int(tr.index) - 1, "total": int(tr.total), "phase": "strike", "x": spot2.x, "y": spot2.y,
				"hit": res.get("hit", false), "damage": float(res.get("damage", 0.0)), "absorbed": res.get("absorbed", false)})
			# Brought to nothing under the heavens: a breakthrough failure, not a grave wound.
			if res.get("lethal", false):
				_end_tribulation(c, false, "bodily_failure")
				return
	if int(tr.index) >= int(tr.total) and (tr.warn as Dictionary).is_empty():
		_end_tribulation(c, true, "")

func _end_tribulation(c, survived: bool, failure: String) -> void:
	var tr: Dictionary = tribulations[c.id]
	tribulations.erase(c.id)
	emit("tribulation_result", {"actor": c.id, "survived": survived, "struck": int(tr.struck), "absorbed": int(tr.absorbed), "bolts": int(tr.total),
		"failure": failure})
	var ch: Dictionary = tr.ch
	if survived:
		_settle_breakthrough(c, ch)
		return
	var rng := Rng.stream(c.id, "breakthrough")
	var from := str(ch.get("from", c.cultivator.realm_key))
	if not (ch.get("used", []) as Array).is_empty(): c.cultivator.support_failures[from] = int(c.cultivator.support_failures.get(from, 0)) + 1
	_fail_breakthrough(c, failure if ContentDB.has_entry("failures", failure) else "interruption", rng)
	_maybe_deviate(c, str(ch.risk))

func is_under_tribulation(actor_id: String) -> bool:
	return tribulations.has(actor_id)

## The tribulation as the HUD and the room draw it: bolts done and total, and the ring waiting to strike.
func tribulation_view(actor_id: String) -> Dictionary:
	if not tribulations.has(actor_id): return {}
	var tr: Dictionary = tribulations[actor_id]
	return {"index": int(tr.index), "total": int(tr.total), "warn": (tr.warn as Dictionary).duplicate(), "struck": int(tr.struck),
		"warn_s": float(ContentDB.config("tribulations").get("warn_s", 1.0)), "radius": float(ContentDB.config("tribulations").get("radius", 80))}

# ------------------------------------------------------------------ vows, the false realm, epiphany (S48)
## Take or let go of a vow. Taking one is free; letting it go breaks it (+15 heart demon).
func set_vow(c, vow: String, on: bool) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	if not ContentDB.has_entry("vows", vow): return fail("unknown_vow")
	if not Unlocks.is_unlocked(c.id, "vows"): return fail("locked", {"text": Unlocks.locked_text("vows")})
	if on:
		if vow in cu.vows: return ok()
		cu.vows.append(vow)
		emit("vow_taken", {"actor": c.id, "vow": vow})
		return ok({"vow": vow})
	if not vow in cu.vows: return ok()
	cu.vows.erase(vow)
	var cost := float(ContentDB.config("vows").get("break_heart_demon", 15))
	apply_heart_demon(c.id, cost, "vow_broken")
	emit("vow_broken", {"actor": c.id, "vow": vow, "heart_demon": cost})
	return ok({"vow": vow, "broken": true})

## A vow held that forbids this kind of act (fleeing_kill, burst_pill, presence, food_buff).
func vow_forbids(c, what: String) -> String:
	for v in c.cultivator.vows:
		if str(ContentDB.entry("vows", str(v)).get("forbids", "")) == what: return str(v)
	return ""

## Concealment's false realm: shown up to two great realms lower ("" shows the true realm).
func set_false_realm(c, realm: String) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	if realm == "":
		cu.false_realm = ""
		emit("false_realm_changed", {"actor": c.id, "realm": ""})
		return ok()
	if not "concealment" in cu.secret_arts: return fail("locked", {"text": Tx.t("sim.progression.false_realm_locked")})
	if ContentDB.realm(realm).is_empty() or not realm in false_realm_choices(c): return fail("too_far", {"text": Tx.t("sim.progression.false_realm_too_far")})
	cu.false_realm = realm
	emit("false_realm_changed", {"actor": c.id, "realm": realm})
	return ok({"realm": realm})

## The realms Concealment can show: the first stage of each great realm up to two below the true one.
func false_realm_choices(c) -> Array:
	var out := []
	var here := ProgressionRules.realm_index(c.cultivator.realm_key)
	var greats := []
	for key in ContentDB.realm_order:
		var g := ProgressionRules.great_realm(str(key))
		if not g in greats: greats.append(g)
	var mine := greats.find(ProgressionRules.great_realm(c.cultivator.realm_key))
	for gi in range(maxi(0, mine - int(ContentDB.stat_const("false_realm", {}).get("max_steps", 2))), mine):
		for key in ContentDB.realm_order:
			if ProgressionRules.great_realm(str(key)) == greats[gi] and ProgressionRules.realm_index(str(key)) < here:
				out.append(str(key))
				break
	return out

## The realm others see: the false one while Concealment holds it, else the true one.
func shown_realm(c) -> String:
	return c.cultivator.false_realm if c.cultivator.false_realm != "" else c.cultivator.realm_key

## Epiphany: a rare flash while insight comes in from Contemplate or a fight. Five times the insight for a minute,
## sometimes a free step of mastery; then two hours of play before the next.
func _roll_epiphany(c, context: String) -> void:
	var cu: CultivatorState = c.cultivator
	var k: Dictionary = ContentDB.stat_const("epiphany", {})
	if cu.epiphany_cooldown > 0.0 or not context.get_slice(":", 0) in k.get("contexts", []): return
	var rng := Rng.stream(c.id, "fortune")
	var chance: float = float(k.get("chance", 0.002)) * (1.0 + float(k.get("insight_weight", 0.01)) * c.stats.value("insight"))
	if rng.randf() >= chance: return
	trigger_epiphany(c, rng)

func trigger_epiphany(c, rng: RandomNumberGenerator) -> void:
	var cu: CultivatorState = c.cultivator
	var k: Dictionary = ContentDB.stat_const("epiphany", {})
	cu.epiphany_cooldown = float(k.get("cooldown_s", 7200))
	game.combat.apply_buff(c.id, {"stat": "insight_rate", "op": "flat", "value": float(k.get("insight_mult", 5.0)) - 1.0,
		"duration": float(k.get("buff_s", 60)), "source": "epiphany"}, "epiphany")
	var gift := ""
	if rng.randf() < float(k.get("mastery_chance", 0.25)):
		# The free "variant": the most-used technique takes a step of mastery for nothing.
		var best := ""
		for tid in cu.technique_use:
			if best == "" or int(cu.technique_use[tid]) > int(cu.technique_use[best]): best = str(tid)
		if best != "" and cu.mastery.has(best) and int(cu.mastery[best].get("tier", 1)) < 6:
			cu.mastery[best].tier = int(cu.mastery[best].get("tier", 1)) + 1
			cu.mastery[best].points = 0.0
			gift = best
			emit("technique_mastery_up", {"actor": c.id, "technique": best, "tier": int(cu.mastery[best].tier)})
	if not game.account.codex.has("epiphany"): game.quest.apply_codex("epiphany")
	emit("epiphany", {"actor": c.id, "technique": gift, "seconds": float(k.get("buff_s", 60))})

# ------------------------------------------------------------------ Inner Arts and stances (S48)
## Learn an Inner Art from its manual (a Mission Hall sells them).
func apply_learn_inner_art(actor_id: String, art: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("inner_arts", art) or art in c.cultivator.inner_arts_known: return
	c.cultivator.inner_arts_known.append(art)
	if not game.account.codex.has("inner_arts"): game.quest.apply_codex("inner_arts")
	emit("inner_art_learned", {"actor": c.id, "art": art})

## Wear a known Inner Art in a slot ("" empties it). An art sits in one slot at a time.
func equip_inner_art(c, slot: int, art: String) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	var n := ProgressionRules.inner_art_slot_count(cu.realm_key)
	if n <= 0: return fail("locked", {"text": Tx.t("sim.progression.inner_arts_locked")})
	if slot < 0 or slot >= n: return fail("slot_locked")
	if art != "" and not art in cu.inner_arts_known: return fail("unknown_art")
	while cu.inner_arts.size() < n: cu.inner_arts.append("")
	if art != "":
		for i in cu.inner_arts.size():
			if str(cu.inner_arts[i]) == art: cu.inner_arts[i] = ""
	cu.inner_arts[slot] = art
	emit("inner_art_equipped", {"actor": c.id, "slot": slot, "art": art})
	return ok({"slot": slot, "art": art})

## Hold a stance for a weapon family ("" lets it go). It works only with that weapon in hand.
func set_stance(c, family: String, stance: String) -> Dictionary:
	if not ContentDB.has_entry("weapon_families", family): return fail("unknown_family")
	if stance != "":
		var st := ContentDB.entry("stances", stance)
		if st.is_empty() or str(st.family) != family: return fail("wrong_stance")
		if not Unlocks.is_unlocked(c.id, "stances"): return fail("locked", {"text": Unlocks.locked_text("stances")})
		c.cultivator.stances[family] = stance
	else:
		c.cultivator.stances.erase(family)
	emit("stance_changed", {"actor": c.id, "family": family, "stance": stance})
	return ok({"family": family, "stance": stance})

# ------------------------------------------------------------------ breakthrough fates (S48)
## After a major breakthrough: three distinct cards from the deck, drawn on the breakthrough stream.
func _offer_fates(c) -> void:
	var pool := ProgressionRules.fate_pool(game.ctx(c))
	var cards := ProgressionRules.draw_fates(pool, int(ContentDB.config("fates").get("offer", 3)), Rng.stream(c.id, "breakthrough"))
	if cards.size() < 2: return
	c.cultivator.fate_offer = cards
	if not game.account.codex.has("fates"): game.quest.apply_codex("fates")
	emit("fate_offered", {"actor": c.id, "cards": cards})

## Choose one of the cards offered: its gift and its cost both apply now; some of either last the realm.
func choose_fate(c, card: String) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	if cu.fate_offer.is_empty(): return fail("no_offer")
	if not card in cu.fate_offer: return fail("not_offered")
	var f := ContentDB.entry("fates", card)
	var rec := {"id": card, "realm": ProgressionRules.great_realm(cu.realm_key)}
	if f.has("next"): rec.next = (f.next as Dictionary).duplicate()
	if "dao_echo" in f.get("flags", []): rec.dao = _strongest_dao(c)
	cu.fates.append(rec)
	cu.fate_offer = []
	game.apply_effects(c.id, f.get("effects", []), "fate:" + card)
	emit("fate_chosen", {"actor": c.id, "card": card})
	return ok({"card": card})

## A fate given outright (a quest, a relic, a fortune): as if chosen from an offer, without one.
func apply_grant_fate(actor_id: String, card: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("fates", card): return
	var saved: Array = c.cultivator.fate_offer.duplicate()
	c.cultivator.fate_offer = [card]
	choose_fate(c, card)
	c.cultivator.fate_offer = saved

## Another authority spends a fate's `next` (Fox Spirit's Favour: the next egg's purity).
func spend_fate_next(c, key: String) -> float:
	return _spend_fate_next(c, key)

## The fates still waiting on a `next` (a tribulation's extra bolts, a breakthrough's bonus): spent once, then gone.
func _spend_fate_next(c, key: String) -> float:
	var total := 0.0
	for rec in c.cultivator.fates:
		var nx: Dictionary = rec.get("next", {})
		if nx.has(key):
			total += float(nx[key])
			nx.erase(key)
	return total

## Hungry Dantian: every pill family's lifetime resistance rises by a count.
func apply_pill_resistance_all(actor_id: String, amount: int) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var fams := {}
	for it in ContentDB.all("items"):
		var fam := ProgressionRules.pill_family(it)
		if fam != "": fams[fam] = true
	for fam in fams:
		var pr: Dictionary = c.cultivator.pill_resistance.get(fam, {"count": 0, "doses": 0})
		pr.count = int(pr.get("count", 0)) + amount
		c.cultivator.pill_resistance[fam] = pr
		emit("pill_resistance_changed", {"actor": c.id, "family": fam, "count": int(pr.count), "doses": int(pr.get("doses", 0))})

## Debt of Heaven: purity one grade better (grade 1 is the purest).
func apply_purity_grade(actor_id: String, grades: int) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var before: int = c.cultivator.purity
	c.cultivator.purity = clampi(c.cultivator.purity - grades, 1, 9)
	if c.cultivator.purity != before: emit("purity_changed", {"actor": c.id, "grade": c.cultivator.purity})

## A fate flag held (reveal_hidden, streak_heart_demon, dao_echo).
func fate_flag(c, flag: String) -> bool:
	for rec in c.cultivator.fates:
		if flag in ContentDB.entry("fates", str(rec.get("id", ""))).get("flags", []): return true
	return false

func _strongest_dao(c) -> String:
	var best := ""
	var best_v := -1.0
	for d in c.cultivator.daos:
		var v := float(c.cultivator.daos[d].get("tier", 0)) * 1000000.0 + float(c.cultivator.daos[d].get("insight", 0.0))
		if v > best_v:
			best = str(d)
			best_v = v
	return best

func is_channeling(actor_id: String) -> bool:
	return channels.has(actor_id)

func _advance(c, to: String, major: bool) -> void:
	var cu: CultivatorState = c.cultivator
	var from := cu.realm_key
	var before_level := ProgressionRules.level(c)
	cu.realm_key = to
	var r := ContentDB.realm(to)
	var energy := str(r.get("energy", cu.energy_type))
	if energy != "none" and energy != "body": cu.energy_type = energy
	cu.state = "accumulating"
	cu.qp = 0.0
	cu.bottleneck_seconds = 0.0
	var n := cu.need()
	var carry := minf(cu.stored_qi, n)
	cu.stored_qi -= carry
	cu.qp = carry
	if major and float(r.get("consolidation_s", 0)) > 0.0:
		cu.state = "consolidating"
		cu.consolidation_left = float(r.consolidation_s)
		cu.consolidation_penalty = true
		cu.stability = "settling"
		cu.stability_progress = 0.0
		emit("stability_changed", {"actor": c.id, "word": cu.stability})
	if major and energy == "true_qi" and ContentDB.realm(from).get("energy") != "true_qi": _forge_core(c)
	if major:
		# Each major breakthrough: every resistance count drops by 1, then halves (S44).
		for fam in cu.pill_resistance.keys():
			var pr: Dictionary = cu.pill_resistance[fam]
			var before_count := int(pr.get("count", 0))
			pr.count = maxi(0, before_count - 1) / 2
			if int(pr.count) != before_count: emit("pill_resistance_changed", {"actor": c.id, "family": fam, "count": int(pr.count), "doses": int(pr.get("doses", 0))})
		cu.support_failures.erase(from)
		# The foundation share starts again with the new major realm.
		cu.foundation = {"realm": ProgressionRules.great_realm(to), "total_qp": 0.0, "pill_qp": 0.0}
		emit("foundation_changed", {"actor": c.id, "share": 0.0})
	emit("breakthrough_succeeded", {"actor": c.id, "from": from, "to": to, "major": major,
		"formation": "guard" if game.workshop.formation_effect(c, "breakthrough_risk_step") < 0.0 else ""})
	emit("realm_changed", {"actor": c.id, "from": from, "to": to, "major": major, "level": ProgressionRules.level(c)})
	var after_level := ProgressionRules.level(c)
	_levels_gained(c, before_level, after_level)
	_reveal_aptitudes(c)
	if cu.qp >= n and n > 0:
		cu.qp = n
		cu.state = "bottleneck"
		_bottleneck(c, to)
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": "breakthrough", "amount": 0})

## S48 Core Forging: the Heart Tempering 9 -> Cloud Stride 1 step sets the purity grade the core forms at. Each
## preparation point met counts on a roll under 80% (breakthrough stream); a flawless Cleansing is one more.
func _forge_core(c) -> void:
	var cu: CultivatorState = c.cultivator
	var k: Dictionary = ContentDB.stat_const("core_forging", {})
	var rng := Rng.stream(c.id, "breakthrough")
	var counted := 0
	var met := 0
	for pt in core_forging_points(c):
		if not pt.met: continue
		met += 1
		if rng.randf() < float(k.get("chance", 0.8)): counted += 1
	var flawless: bool = c.quests.has_flag("cleansing_flawless")
	var grade := ProgressionRules.core_grade(counted, flawless)
	cu.core_grade = grade
	cu.purity = grade
	cu.purity_points = 0.0
	if not game.account.codex.has("core_forging"): game.quest.apply_codex("core_forging")
	emit("core_graded", {"actor": c.id, "grade": grade, "met": met, "counted": counted, "flawless": flawless})

## The five Core Forging points as they stand now, in this room at this hour.
func core_forging_points(c) -> Array:
	var room: Dictionary = game.room_rt.def if game.room_rt else {}
	var pill := str(ContentDB.stat_const("core_forging", {}).get("pill", "heavenly_flame_pill"))
	var age: float = game.sim_time - float(c.cultivator.pill_memory[pill]) if c.cultivator.pill_memory.has(pill) else -1.0
	return ProgressionRules.core_forging_points(c, room, Clock.time_of_day(), age)

func _fail_breakthrough(c, failure_id: String, rng: RandomNumberGenerator) -> void:
	var cu: CultivatorState = c.cultivator
	var f := ContentDB.entry("failures", failure_id)
	var loss := ProgressionRules.failure_loss(rng, failure_id)
	cu.qp = maxf(0.0, cu.need() * (1.0 - loss))
	cu.state = "accumulating" if cu.qp < cu.need() else "bottleneck"
	var injuries: Array = []
	if f.has("injury"):
		apply_injury(c.id, str(f.injury.kind), int(f.injury.severity))
		injuries.append(f.injury.kind)
	if f.has("stability"):
		cu.stability = str(f.stability)
		emit("stability_changed", {"actor": c.id, "word": cu.stability})
	if f.has("cooldown_s"): cu.breakthrough_cooldown = float(f.cooldown_s)
	emit("breakthrough_failed", {"actor": c.id, "failure_id": failure_id, "losses": loss, "injuries": injuries,
		"recovery": str(f.get("recovery", ""))})
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": "failure", "amount": 0})

func _reveal_aptitudes(c) -> void:
	var cu: CultivatorState = c.cultivator
	var rules := [["physique", "bone_forging_4"], ["element_water", "bone_forging_7"], ["element_wood", "bone_forging_7"],
		["element_fire", "bone_forging_7"], ["element_earth", "bone_forging_7"], ["element_metal", "bone_forging_7"],
		["element_wind", "bone_forging_7"], ["spirit_aptitude", "spirit_awakening_1"]]
	for rule in rules:
		var ap: Dictionary = cu.aptitude.get(rule[0], {})
		if ap.is_empty() or ap.get("revealed", false): continue
		if ProgressionRules.at_least(cu.realm_key, rule[1]):
			ap.revealed = true
			emit("aptitude_revealed", {"actor": c.id, "aptitude": rule[0], "value": ap.value})

## Roll hidden aptitude values once at creation (each at most ±15%, S08).
func roll_aptitude(c) -> void:
	var rng := Rng.stream(c.id, "world")
	var nudge := str(ContentDB.entry("origins", c.cultivator.origin).get("element_nudge", ""))
	for key in ["physique", "element_water", "element_wood", "element_fire", "element_earth", "element_metal", "element_wind", "spirit_aptitude", "comprehension"]:
		var v := snappedf(rng.randf_range(-0.10, 0.10), 0.01)
		if key == "element_" + nudge: v = clampf(v + 0.05, -0.15, 0.15)
		c.cultivator.aptitude[key] = {"value": v, "revealed": false}

# ------------------------------------------------------------------ reactions
func _on_hit_landed(p: Dictionary) -> void:
	var c = game.character(str(p.get("target", "")))
	if c == null or int(p.get("amount", 0)) <= 0: return
	if c.cultivator.meditating:
		stop_meditation(c, "backlash")
		game.combat.apply_backlash(c.id)
		emit("qi_backlash", {"actor": c.id})
	if channels.has(c.id):
		var ch: Dictionary = channels[c.id]
		channels.erase(c.id)
		_fail_breakthrough(c, "interruption", Rng.stream(c.id, "breakthrough"))

func _on_actor_defeated(p: Dictionary) -> void:
	var c = game.character(str(p.get("killer", "")))
	if c == null or p.get("victim_kind", "") != "enemy": return
	_count_streak(c)
	var lv := int(p.get("level", 1))
	if Unlocks.is_unlocked(c.id, "kill_progress"):
		apply_progress(c.id, ProgressionRules.kill_qp(ProgressionRules.level(c), lv, str(p.get("role", "normal"))), "kill")
	if Unlocks.is_unlocked(c.id, "body_training"):
		apply_body_xp(c.id, ProgressionRules.kill_body_xp(lv), "kill")
	if Unlocks.is_unlocked(c.id, "weapon_dao"):
		var fam := StatRules.family(c)
		apply_insight(c.id, str(fam.get("dao", "fist")), 1.0, "kill:" + str(p.get("def", "")) + ":" + str(p.get("room", "")))

func _on_gravely_wounded(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	# Struck down by a foe while the heavens were testing you: the breakthrough fails with the body (S48).
	if tribulations.has(c.id): _end_tribulation(c, false, "bodily_failure")
	if p.get("no_penalty", false): return
	var cu: CultivatorState = c.cultivator
	var loss := float(ContentDB.stat_const("death.progress_loss", 0.1))
	# S48 nascent-soul escape: from Sage the soul flees to the shrine and only half as much is lost.
	var esc: Dictionary = ContentDB.stat_const("soul_escape", {})
	if ProgressionRules.at_least(cu.realm_key, str(esc.get("from", "sage_1"))):
		loss = float(esc.get("progress_loss", 0.05))
		emit("soul_escaped", {"actor": c.id, "loss": loss})
	if cu.state != "bottleneck":
		cu.qp = maxf(0.0, cu.qp - cu.need() * loss)
	else:
		cu.stored_qi = maxf(0.0, cu.stored_qi - cu.need() * loss)
	# "May carry an injury" (S31): a coin flip, and defeats alone never push it past severity 2.
	var rng := Rng.stream(c.id, "combat")
	if rng.randf() < float(ContentDB.stat_const("death.injury_chance", 0.5)) and int(cu.injuries.get("body", {}).get("severity", 0)) < 2:
		apply_injury(c.id, "body", 1)
	if p.get("cause", "") == "soul": apply_injury(c.id, "soul", 1)
	apply_heart_demon(c.id, float(ContentDB.stat_const("heart_demon", {}).get("death", 3)), "defeat")
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": "wounded", "amount": 0})

func _on_technique_used(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	var tid := str(p.get("technique", ""))
	var tdef := ContentDB.entry("techniques", tid)
	if tdef.is_empty(): return
	var hits := maxi(1, int(p.get("hits", 1)))
	c.cultivator.technique_use[tid] = int(c.cultivator.technique_use.get(tid, 0)) + 1
	var m: Dictionary = c.cultivator.mastery.get(tid, {"tier": 1, "points": 0.0})
	var max_by_use := 3
	if int(m.tier) < max_by_use:
		m.points = float(m.points) + hits * (1.0 + c.stats.value("mastery_gain"))
		while int(m.tier) < max_by_use and float(m.points) >= ProgressionRules.mastery_needed(int(m.tier)):
			m.points = float(m.points) - ProgressionRules.mastery_needed(int(m.tier))
			m.tier = int(m.tier) + 1
			emit("technique_mastery_up", {"actor": c.id, "technique": tid, "tier": m.tier})
	else:
		m.points = minf(float(m.points) + hits, ProgressionRules.mastery_needed(int(m.tier)))
	c.cultivator.mastery[tid] = m
	var dao := str(tdef.get("dao", ""))
	if dao != "" and dao != "none": apply_insight(c.id, dao, 1.0, "tech:%s:%s" % [tid, str(p.get("target_def", ""))])

func _on_object_hit(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	var type := str(p.get("type", ""))
	if type in ["training_stump", "training_dummy"] and Unlocks.is_unlocked(c.id, "body_training"):
		var per_hit := 1.0 / 60.0 / 1.4
		if ProgressionRules.is_body_stage(c.cultivator.realm_key) and Unlocks.is_unlocked(c.id, "cultivation"):
			apply_progress(c.id, float(ContentDB.curve("training_qp_per_min", 40)) * per_hit, "training")
		apply_body_xp(c.id, float(ContentDB.curve("training_body_xp_per_min", 20)) * per_hit, "training")
	elif type == "lifting_stone" and Unlocks.is_unlocked(c.id, "body_training"):
		if ProgressionRules.is_body_stage(c.cultivator.realm_key) and Unlocks.is_unlocked(c.id, "cultivation"):
			apply_progress(c.id, float(ContentDB.curve("training_qp_per_min", 40)) * 3.0 / 60.0, "training")
		apply_body_xp(c.id, float(ContentDB.curve("training_body_xp_per_min", 20)) * 4.5 / 60.0, "training")

# ------------------------------------------------------------------ apply_* commands
func apply_body_xp(actor_id: String, xp: float, _source: String) -> void:
	var c = game.character(actor_id)
	if c == null or xp <= 0.0: return
	var growth := float(ProgressionRules.method(c.cultivator.method_id).get("body_growth", 0.0))
	c.cultivator.body_xp += xp * (1.0 + growth)
	var leveled := false
	while c.cultivator.body_xp >= ProgressionRules.body_xp_needed(c.cultivator.body_level):
		c.cultivator.body_xp -= ProgressionRules.body_xp_needed(c.cultivator.body_level)
		c.cultivator.body_level += 1
		leveled = true
	if leveled:
		emit("body_level_changed", {"actor": c.id, "value": c.cultivator.body_level})
		_check_body_tier(c)

# ------------------------------------------------------------------ the body ladder and physiques (S48)
## A Temper trial passed (the trial event's on_complete). The tier opens once its bath is taken too.
func pass_body_trial(actor_id: String, tier: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("body_tiers", tier): return
	if not tier in c.cultivator.body_trials: c.cultivator.body_trials.append(tier)
	emit("body_trial_passed", {"actor": c.id, "tier": tier, "bath": str(ContentDB.entry("body_tiers", tier).get("bath", ""))})
	_check_body_tier(c)

## The next rung opens when the body level, the trial and the bath are all there; one rung at a time.
func _check_body_tier(c) -> void:
	var cu: CultivatorState = c.cultivator
	for _i in 4:
		var need := ProgressionRules.body_tier_needs(cu)
		if need.is_empty() or not (need.level and need.trial and need.bath): return
		var t := ContentDB.entry("body_tiers", str(need.tier))
		cu.body_tier = str(t.id)
		for rid in t.get("teaches", []): game.apply_effects(c.id, [{"kind": "learn_recipe", "recipe": str(rid)}], "body_tier")
		if not game.account.codex.has("body_ladder"): game.quest.apply_codex("body_ladder")
		emit("body_tier_reached", {"actor": c.id, "tier": cu.body_tier, "name": str(t.get("name", ""))})
		# Stone Marrow: Copper Body before Qi Unfurling 3.
		var early := ContentDB.entry("physiques", "stone_marrow")
		if cu.body_tier == "copper" and not early.is_empty() and not ProgressionRules.at_least(cu.realm_key, str(early.get("before", "qi_unfurling_3"))):
			awaken_physique(c.id, "stone_marrow")

## A physique, earned by a deed: it stays for life, gift and drawback both.
func awaken_physique(actor_id: String, physique: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("physiques", physique) or physique in c.cultivator.physiques: return
	c.cultivator.physiques.append(physique)
	if not game.account.codex.has("physiques"): game.quest.apply_codex("physiques")
	emit("physique_awakened", {"actor": c.id, "physique": physique, "name": ContentDB.name_of("physiques", physique)})

## Lifetime counters (S48 physiques read them): add, then awaken any physique whose count is reached.
func add_lifetime(c, key: String, amount: float) -> void:
	if c == null or amount <= 0.0: return
	var v := float(c.cultivator.lifetime_stats.get(key, 0.0)) + amount
	c.cultivator.lifetime_stats[key] = v
	for ph in ContentDB.all("physiques"):
		if str(ph.get("earned", "")) == key and ph.has("count") and v >= float(ph.count): awaken_physique(c.id, str(ph.id))

## Yin Vessel: a night counts once the character has sat through a minute of it at the Falls Pool.
func _falls_pool_second(c) -> void:
	var ls: Dictionary = c.cultivator.lifetime_stats
	var night := int(Clock.now_utc() / (float(ContentDB.curve("time_of_day.day_minutes", 48)) * 60.0))
	if int(ls.get("falls_pool_night", -1)) != night:
		ls["falls_pool_night"] = night
		ls["falls_pool_s"] = 0.0
	if float(ls.falls_pool_s) >= 60.0: return
	ls["falls_pool_s"] = float(ls.falls_pool_s) + 1.0
	if float(ls.falls_pool_s) >= 60.0: add_lifetime(c, "falls_pool_nights", 1.0)

## Kills in a row, each within 10 s of the last. Blood Memory (a fate) feeds the heart demon at every 10.
func _count_streak(c) -> void:
	var k: Dictionary = ContentDB.config("fates").get("streak", {})
	var sk: Dictionary = streaks.get(c.id, {"n": 0, "t": -999.0})
	sk.n = int(sk.n) + 1 if game.sim_time - float(sk.t) <= float(k.get("window_s", 10.0)) else 1
	sk.t = game.sim_time
	streaks[c.id] = sk
	if int(sk.n) % int(k.get("kills", 10)) == 0 and fate_flag(c, "streak_heart_demon"): apply_heart_demon(c.id, 1.0, "blood_memory")

## Ember Heart: every Fire pill refined counts, by the pill.
func _on_fire_pill(p: Dictionary) -> void:
	if str(p.get("craft", "")) != "alchemy" or str(ContentDB.entry("recipes", str(p.get("recipe", ""))).get("element", "")) != "fire": return
	add_lifetime(game.character(str(p.get("actor", ""))), "fire_pills", float(p.get("count", 0)))

## Cloud Lung: the ground covered gliding or flying, in metres.
func add_air_distance(actor_id: String, px: float) -> void:
	var c = game.character(actor_id)
	if c == null or px <= 0.0: return
	add_lifetime(c, "air_metres", px / float(ContentDB.stat_const("body_path", {}).get("air_metre_px", 50)))

func apply_soul(actor_id: String, amount: float) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var before := int(c.cultivator.soul_cultivation / 10.0)
	c.cultivator.soul_cultivation = maxf(0.0, c.cultivator.soul_cultivation + amount)
	if int(c.cultivator.soul_cultivation / 10.0) != before: emit("soul_changed", {"actor": c.id, "value": c.cultivator.soul_cultivation})

func apply_purity(actor_id: String, points: float) -> void:
	var c = game.character(actor_id)
	if c == null or c.cultivator.purity <= 1: return
	c.cultivator.purity_points += points
	var per := float(ContentDB.curve("purity_points_per_grade", 100))
	while c.cultivator.purity_points >= per and c.cultivator.purity > 1:
		c.cultivator.purity_points -= per
		c.cultivator.purity -= 1
		emit("purity_changed", {"actor": c.id, "value": c.cultivator.purity})

## S49 lifespan as flavour: a longevity treasure adds years to the span the realm grants (display only).
func apply_longevity(actor_id: String, years: int) -> void:
	var c = game.character(actor_id)
	if c == null or years == 0: return
	c.cultivator.longevity += years

func apply_insight(actor_id: String, dao: String, amount: float, context: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("daos", dao): return
	if not Unlocks.is_unlocked(c.id, "dao_tree") and not context.begins_with("kill") and not Unlocks.is_unlocked(c.id, "weapon_dao"): return
	# A teacher's lesson is measured out exactly (apply_open_dao); everything else is damped when repeated and
	# goes through the insight rate.
	if not context.begins_with("teacher:"):
		var mem: Dictionary = c.cultivator.insight_memory
		var window := float(ContentDB.curve("insight_repeat_window_s", 60))
		var key := context.get_slice(":", 0) + ":" + context.get_slice(":", 1) + ":" + context.get_slice(":", 2)
		if mem.has(key) and game.sim_time - float(mem[key]) < window: amount *= float(ContentDB.curve("insight_repeat_factor", 0.2))
		mem[key] = game.sim_time
		if mem.size() > 64: mem.clear()
		amount *= 1.0 + c.stats.value("insight_rate") + game.relations.insight_share(c)   # S49: a Dao Companion beside you
		# S48 Dao Echo: the chosen Dao learns faster and every other Dao slower.
		for rec in c.cultivator.fates:
			if rec.has("dao") and str(rec.dao) != "": amount *= 1.2 if str(rec.dao) == dao else 0.9
	# A rare Dao grows only after a teacher has opened it (apply_open_dao).
	if str(ContentDB.entry("daos", dao).get("family", "")) == "rare" and not c.cultivator.daos.has(dao): return
	var d: Dictionary = c.cultivator.daos.get(dao, {"tier": 0, "insight": 0.0})
	d.insight = float(d.insight) + amount
	# A Dao deepens as far as the land's Laws allow: its valley cap, or the cap of the zone you stand in.
	var ddef := ContentDB.entry("daos", dao)
	var zone_id := str(ContentDB.room_zone.get(str(c.position.get("room", "")), ""))
	var cap := maxi(int(ddef.get("valley_cap", 6)), int(ddef.get("zone_caps", {}).get(zone_id, 0)))
	var tier := mini(ProgressionRules.dao_tier_for(float(d.insight)), cap)
	var gained := tier > int(d.tier)
	d.tier = maxi(int(d.tier), tier)
	c.cultivator.daos[dao] = d
	if context != "epiphany": _roll_epiphany(c, context)
	emit("insight_gained", {"actor": c.id, "dao": dao, "amount": amount})
	if gained:
		emit("dao_tier_up", {"actor": c.id, "dao": dao, "tier": d.tier})
		# A tier can teach a technique (S47: Sword Dao tier 3 teaches Sword Release).
		var effects: Array = ddef.get("effects", [])
		for ti in mini(int(d.tier), effects.size()):
			if effects[ti] is Dictionary and effects[ti].has("learn_technique"): apply_learn_technique(c.id, str(effects[ti].learn_technique))

## A teacher of the Expanse opens a rare Dao: the first tier's insight comes with the lesson.
func apply_open_dao(actor_id: String, dao: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("daos", dao) or c.cultivator.daos.has(dao): return
	c.cultivator.daos[dao] = {"tier": 0, "insight": 0.0}
	var first: Array = ContentDB.curve("dao_tiers", [100])
	# A teacher opens the Dao at tier 1: exactly the first tier's insight, untouched by the insight rate or a
	# Dao Echo fate (S48), with a hair's margin.
	apply_insight(actor_id, dao, float(first[0]) + 0.01, "teacher:" + dao)

func _on_buff_expired(p: Dictionary) -> void:
	var then: Array = ContentDB.item(str(p.get("source", ""))).get("then", [])
	if not then.is_empty(): game.apply_effects(str(p.get("actor", "")), then, "then:" + str(p.source))

func apply_injury(actor_id: String, kind: String, severity: int) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("injuries", kind): return
	var inj: Dictionary = c.cultivator.injuries.get(kind, {"severity": 0, "time_left": 0.0})
	inj.severity = clampi(int(inj.severity) + severity, 1, 3)
	inj.time_left = _heal_time(int(inj.severity))
	c.cultivator.injuries[kind] = inj
	emit("injury_added", {"actor": c.id, "kind": kind, "severity": inj.severity})

func apply_cure_injury(actor_id: String, kind: String, max_severity: int) -> void:
	var c = game.character(actor_id)
	if c == null or not c.cultivator.injuries.has(kind): return
	var inj: Dictionary = c.cultivator.injuries[kind]
	if int(inj.severity) <= max_severity:
		c.cultivator.injuries.erase(kind)
		emit("injury_healed", {"actor": c.id, "kind": kind, "severity": 0})
	else:
		inj.severity = int(inj.severity) - max_severity
		emit("injury_healed", {"actor": c.id, "kind": kind, "severity": inj.severity})

func apply_toxicity(actor_id: String, amount: float) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cultivator.toxicity = maxf(0.0, c.cultivator.toxicity + amount)
	if amount > 0.0: apply_residue(c.id, amount * float(ContentDB.stat_const("pill_life", {}).get("residue_share", 0.05)))
	emit("toxicity_changed", {"actor": c.id, "value": c.cultivator.toxicity})
	if amount > 0 and c.cultivator.toxicity > c.stats.value("toxicity_tolerance"):
		apply_injury(c.id, "meridian", 1)

## Residue (G1): the part of toxicity that never drains on its own. Negative amounts clear it.
func apply_residue(actor_id: String, amount: float) -> void:
	var c = game.character(actor_id)
	if c == null or amount == 0.0: return
	c.cultivator.residue = maxf(0.0, c.cultivator.residue + amount)
	emit("residue_changed", {"actor": c.id, "value": c.cultivator.residue})

## The heart-demon meter (G1), 0-100.
func apply_heart_demon(actor_id: String, amount: float, source: String) -> void:
	var c = game.character(actor_id)
	if c == null or amount == 0.0: return
	# S48: some physiques (Hollow-Touched) make every gain larger.
	if amount > 0.0:
		for pid in c.cultivator.physiques: amount *= float(ContentDB.entry("physiques", str(pid)).get("heart_demon_mult", 1.0))
	var before := int(ProgressionRules.heart_demon_steps(c.cultivator))
	c.cultivator.heart_demon = clampf(c.cultivator.heart_demon + amount, 0.0, 100.0)
	if amount > 0.0 and not game.account.codex.has("heart_demons"): game.quest.apply_codex("heart_demons")
	emit("heart_demon_changed", {"actor": c.id, "value": c.cultivator.heart_demon, "delta": amount, "source": source,
		"step_crossed": ProgressionRules.heart_demon_steps(c.cultivator) != before})

## The Sovereign Settling Pill: what is left of this stage's consolidation ends on the next tick.
func apply_settle(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null or c.cultivator.consolidation_left <= 0.0: return
	c.cultivator.consolidation_left = 0.001

## Set the stability word (Scar of Failure starts a realm Unstable, S48).
func apply_stability(actor_id: String, word: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cultivator.stability = word
	c.cultivator.stability_progress = 0.0
	emit("stability_changed", {"actor": c.id, "word": word})

func apply_learn_method(actor_id: String, method_id: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("methods", method_id): return
	if not c.cultivator.methods_known.has(method_id): c.cultivator.methods_known.append(method_id)
	var current := ContentDB.entry("methods", c.cultivator.method_id)
	var fresh := ContentDB.entry("methods", method_id)
	# A fragment (Lu's Riverbreath) is replaced by a full scripture at no cost (S08 switching applies to real methods).
	var upgrade := bool(current.get("fragment", false)) and not bool(fresh.get("fragment", false)) \
		and ContentDB.realm_position(str(fresh.get("ceiling", ""))) > ContentDB.realm_position(str(current.get("ceiling", "")))
	if c.cultivator.method_id == "" or upgrade:
		c.cultivator.method_id = method_id
		emit("method_changed", {"actor": c.id, "method": method_id, "cost": 0.0})
		if upgrade: log_line(c.id, Tx.t("sim.progression.replaces") % [str(fresh.get("name", ContentDB.name_of("methods", method_id))), ContentDB.name_of("methods", str(current.id))], "progress")
	emit("method_learned", {"actor": c.id, "method": method_id})

## S47 dual loadout: each weapon keeps its own technique bar. The bar in use is put away with the weapon, and the
## other weapon's bar comes out (the first swap starts it as a copy). No Dao tier is touched by a swap.
func _on_loadout_swapped(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	var now := str(p.get("active", "a"))
	var was := "a" if now == "b" else "b"
	c.cultivator.technique_bars[was] = c.cultivator.technique_slots.duplicate()
	if c.cultivator.technique_bars.has(now):
		var bar: Array = c.cultivator.technique_bars[now]
		for i in mini(bar.size(), c.cultivator.technique_slots.size()):
			var tid = bar[i]
			c.cultivator.technique_slots[i] = tid if tid != null and c.cultivator.techniques_known.has(str(tid)) else null

func apply_learn_technique(actor_id: String, tid: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("techniques", tid): return
	if c.cultivator.techniques_known.has(tid): return
	c.cultivator.techniques_known.append(tid)
	c.cultivator.mastery[tid] = {"tier": 1, "points": 0.0}
	emit("technique_learned", {"actor": c.id, "technique": tid})
	var slots := ProgressionRules.technique_slot_count(c)
	for i in slots:
		if c.cultivator.technique_slots[i] == null:
			c.cultivator.technique_slots[i] = tid
			emit("technique_equipped", {"actor": c.id, "technique": tid, "slot": i})
			break

func apply_learn_secret_art(actor_id: String, art: String) -> void:
	var c = game.character(actor_id)
	if c == null or c.cultivator.secret_arts.has(art): return
	c.cultivator.secret_arts.append(art)
	emit("secret_art_learned", {"actor": c.id, "art": art})

func apply_event_passed(actor_id: String, event: String) -> void:
	var c = game.character(actor_id)
	if c == null or event in c.cultivator.events_passed: return
	c.cultivator.events_passed.append(event)
	emit("event_passed", {"actor": c.id, "event": event})

func apply_reset_meridians(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var total := 0
	for ch in c.cultivator.meridians:
		total += int(c.cultivator.meridians[ch])
		c.cultivator.meridians[ch] = 0
	c.cultivator.unspent_meridian_points += total
	emit("attributes_changed", {"actor": c.id, "reason": "reset"})

# ------------------------------------------------------------------ intents
func switch_method(c, method_id: String, use_pill: bool) -> Dictionary:
	if not c.cultivator.methods_known.has(method_id): return fail("unknown_method")
	if method_id == c.cultivator.method_id: return fail("already_active")
	var conf: Dictionary = ContentDB.curve("method_switch", {})
	var factor := 1.0
	if use_pill:
		if c.inventory.count("method_conversion_pill") <= 0: return fail("no_pill")
		game.inventory.apply_remove(c.id, "method_conversion_pill", 1, "method_switch")
		factor = float(conf.get("pill_factor", 0.5))
	var cost = c.cultivator.qp * float(conf.get("progress_cost", 0.3)) * factor
	if c.cultivator.state == "bottleneck":
		c.cultivator.state = "accumulating"
	c.cultivator.qp = maxf(0.0, c.cultivator.qp - cost)
	c.cultivator.method_id = method_id
	c.cultivator.stability = "unstable"
	apply_heart_demon(c.id, float(ContentDB.stat_const("heart_demon", {}).get("method_switch", 10)), "method_switch")
	emit("stability_changed", {"actor": c.id, "word": "unstable"})
	emit("method_changed", {"actor": c.id, "method": method_id, "cost": cost})
	emit("progress_changed", {"actor": c.id, "progress": c.cultivator.progress_fraction(), "stored": c.cultivator.stored_qi, "source": "method_switch", "amount": -cost})
	return ok({"cost": cost})

func method_switch_preview(c, use_pill: bool) -> float:
	var conf: Dictionary = ContentDB.curve("method_switch", {})
	return c.cultivator.qp * float(conf.get("progress_cost", 0.3)) * (float(conf.get("pill_factor", 0.5)) if use_pill else 1.0)

func open_meridian(c, channel: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "foundation"): return fail("locked")
	if not c.cultivator.meridians.has(channel): return fail("bad_channel")
	if c.cultivator.unspent_meridian_points <= 0: return fail("no_points")
	c.cultivator.unspent_meridian_points -= 1
	c.cultivator.meridians[channel] = int(c.cultivator.meridians[channel]) + 1
	var v := int(c.cultivator.meridians[channel])
	if v in [25, 50, 100]: emit("meridian_gate_opened", {"actor": c.id, "channel": channel, "points": v})
	emit("attributes_changed", {"actor": c.id, "channel": channel})
	return ok()

func reset_meridians(c) -> Dictionary:
	if not ProgressionRules.at_least(c.cultivator.realm_key, "qi_unfurling_1"):
		apply_reset_meridians(c.id)
		return ok({"free": true})
	if c.inventory.count("meridian_reversal_pill") <= 0: return fail("needs_pill", {"text": Tx.t("sim.progression.needs_a_meridian_reversal_pill")})
	game.inventory.apply_remove(c.id, "meridian_reversal_pill", 1, "meridian_reset")
	apply_reset_meridians(c.id)
	return ok()

func equip_technique(c, slot: int, tid: String) -> Dictionary:
	var n := ProgressionRules.technique_slot_count(c)
	if slot < 0 or slot >= n: return fail("slot_locked")
	if tid != "" and not c.cultivator.techniques_known.has(tid): return fail("unknown_technique")
	if tid != "":
		for i in c.cultivator.technique_slots.size():
			if c.cultivator.technique_slots[i] == tid: c.cultivator.technique_slots[i] = null
	c.cultivator.technique_slots[slot] = tid if tid != "" else null
	emit("technique_equipped", {"actor": c.id, "technique": tid, "slot": slot})
	return ok()

func rank_up_technique(c, tid: String) -> Dictionary:
	var m: Dictionary = c.cultivator.mastery.get(tid, {})
	if m.is_empty(): return fail("unknown_technique")
	if int(m.tier) < 3 or int(m.tier) >= 6: return fail("not_by_manual")
	if not Unlocks.is_unlocked(c.id, "technique_slots_8"): return fail("locked", {"text": Tx.t("sim.progression.mastery_beyond_tier_3_opens")})
	if float(m.points) < ProgressionRules.mastery_needed(int(m.tier)): return fail("need_practice", {"text": Tx.t("sim.progression.practise_more")})
	if c.inventory.count("manual_page") <= 0: return fail("need_manual", {"text": Tx.t("sim.progression.needs_a_manual_page")})
	game.inventory.apply_remove(c.id, "manual_page", 1, "rank_up")
	m.tier = int(m.tier) + 1
	m.points = 0.0
	emit("technique_mastery_up", {"actor": c.id, "technique": tid, "tier": m.tier})
	return ok()

# ------------------------------------------------------------------ natural treasures
## The Nine-Bough Jade Tree answers only a mind stuck at an Understanding bottleneck, once per
## realm stage: a large share of the strongest Dao's gap to its next tier.
func consult_jade_tree(c) -> Dictionary:
	var stuck := false
	if c.cultivator.state == "bottleneck":
		for r in query_requirements(c):
			if not r.ok and str(r.cause) == "understanding": stuck = true
	if not stuck: return ok({"text": Tx.t("sim.progression.the_jade_leaves_are_still")})
	if str(c.cultivator.treasure_uses.get("nine_bough_jade_tree", "")) == c.cultivator.realm_key:
		return ok({"text": Tx.t("sim.progression.the_tree_has_answered")})
	var dao := ""
	var best := -1.0
	for d in c.cultivator.daos:
		if float(c.cultivator.daos[d].get("insight", 0.0)) > best:
			best = float(c.cultivator.daos[d].get("insight", 0.0))
			dao = str(d)
	if dao == "": dao = "sword"
	var tiers: Array = ContentDB.curve("dao_tiers", [100, 300, 800, 2000, 5000, 12000])
	var tier := int(c.cultivator.daos.get(dao, {}).get("tier", 0))
	var gap := float(tiers[mini(tier, tiers.size() - 1)]) - maxf(0.0, best)
	var cfg: Dictionary = ContentDB.stat_const("treasures", {})
	var amount := maxf(float(cfg.get("jade_tree_min_insight", 500)), gap * float(cfg.get("jade_tree_share", 0.75)))
	apply_insight(c.id, dao, amount, "nine_bough_jade_tree")
	c.cultivator.treasure_uses["nine_bough_jade_tree"] = c.cultivator.realm_key
	emit("natural_treasure_used", {"actor": c.id, "treasure": "nine_bough_jade_tree", "dao": dao, "amount": amount})
	return ok({"text": Tx.t("sim.progression.the_tree_answers") % ContentDB.name_of("daos", dao), "dao": dao, "amount": amount})

# ------------------------------------------------------------------ seclusion (S07)
func enter_seclusion(c, focus: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "seclusion"): return fail("locked", {"text": Unlocks.locked_text("seclusion")})
	var allowed := {"accumulate": "seclusion", "temper_body": "seclusion", "heal": "seclusion", "contemplate": "insight_sites",
		"refine_qi": "refine_qi", "nourish_soul": "nourish_soul", "settle_foundation": "seclusion"}
	if not allowed.has(focus) or not Unlocks.is_unlocked(c.id, allowed[focus]): return fail("focus_locked")
	var room = game.room_rt.def if game.room_rt else {}
	var spot := str(room.get("id", ""))
	if not room.get("safe", false): spot = str(c.last_shrine.get("room", spot))
	c.seclusion = {"spot": spot, "focus": focus, "started_utc": Clock.now_utc(), "dao": contemplate.get(c.id, ""),
		"cap_h": seclusion_cap(room), "density": float(room.get("qi_density", 1.0))}
	emit("seclusion_entered", {"actor": c.id, "focus": focus, "spot": spot})
	return ok()

## A medicinal bath (S44): at a Bath station it takes the seclusion slot. The bath is poured now; what it gives
## comes when you claim the seclusion (a full hour gives it all).
func start_bath(c, item_id: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "medicinal_bath"): return fail("locked", {"text": Unlocks.locked_text("medicinal_bath")})
	var def := ContentDB.item(item_id)
	if not def.has("bath") or c.inventory.count(item_id) < 1: return fail("no_bath", {"text": Tx.t("sim.progression.no_bath")})
	if not game.crafting.station_near(c, ["bath_station"]): return fail("no_station", {"text": Tx.t("sim.progression.bath_station")})
	game.inventory.apply_remove(c.id, item_id, 1, "bath")
	var room = game.room_rt.def if game.room_rt else {}
	c.seclusion = {"spot": str(room.get("id", "")), "focus": "bath", "bath": item_id, "started_utc": Clock.now_utc(),
		"cap_h": seclusion_cap(room), "density": float(room.get("qi_density", 1.0))}
	emit("seclusion_entered", {"actor": c.id, "focus": "bath", "spot": str(room.get("id", ""))})
	return ok({"item": item_id})

## What a bath gives for the minutes soaked: body XP, residue, the foundation's pill share, its toxicity. A bath of a
## grade beyond your body (the body tier before the one it prepares) injures the body.
func _bath_gains(c, item_id: String, minutes: float) -> Dictionary:
	var b: Dictionary = ContentDB.item(item_id).get("bath", {})
	var f := clampf(minutes / (60.0 * float(b.get("hours", 1.0))), 0.0, 1.0)
	var gains := {}
	if f <= 0.0: return gains
	var xp := float(b.get("body_xp", 0)) * f
	apply_body_xp(c.id, xp, "bath")
	gains.body_xp = xp
	var cu: CultivatorState = c.cultivator
	var res := minf(cu.residue, float(b.get("residue", 0)) * f)
	if res > 0.0:
		apply_residue(c.id, -res)
		gains.residue = res
	if str(cu.foundation.get("realm", "")) == ProgressionRules.great_realm(cu.realm_key):
		var drop := float(cu.foundation.get("total_qp", 0.0)) * float(b.get("share", 0.1)) * f
		gains.foundation = minf(drop, float(cu.foundation.get("pill_qp", 0.0)))
		cu.foundation.pill_qp = maxf(0.0, float(cu.foundation.get("pill_qp", 0.0)) - drop)
		emit("foundation_changed", {"actor": c.id, "share": ProgressionRules.foundation_share(cu)})
	apply_toxicity(c.id, float(b.get("toxicity", 0)) * f)
	# The injury itself is dealt after the seclusion's natural healing, so an hour away does not mend it at once.
	if StatRules.grade_index(str(ContentDB.item(item_id).get("grade", "plain"))) - 1 > ProgressionRules.body_tier_index(cu):
		gains.injured = true
	# S48: a full soak the body could hold counts toward the body tier the bath belongs to.
	elif f >= 0.999:
		for t in ContentDB.all("body_tiers"):
			if str(t.get("bath", "")) == item_id and not str(t.id) in cu.body_baths:
				cu.body_baths.append(str(t.id))
				gains.body_bath = str(t.id)
		if gains.has("body_bath"): _check_body_tier(c)
	return gains

func seclusion_cap(room: Dictionary) -> float:
	if room.get("gathering_formation", false): return float(ContentDB.curve("formation_cap_h", 24))
	if room.get("retreat", false): return float(ContentDB.curve("retreat_cap_h", 16))
	return float(ContentDB.curve("offline_cap_h", 12))

## Offline gains for the playing character (S07). Never breaks through.
func claim_offline(c, elapsed_s: float) -> Dictionary:
	if c.seclusion.is_empty() or elapsed_s <= 0.0: return ok({"gains": {}, "capped": false, "hours": 0.0})
	var focus := str(c.seclusion.get("focus", "accumulate"))
	var span := ProgressionRules.offline_minutes(elapsed_s, float(c.seclusion.get("cap_h", 12)))
	var minutes := float(span.minutes)
	var factor := float(ContentDB.curve("offline_factor", 0.1))
	var gains := {}
	match focus:
		"accumulate":
			var rate := ProgressionRules.meditation_rate(c, float(c.seclusion.get("density", 1.0)), accumulation_bonus(c))
			var qp := rate * factor * minutes
			var before_state = c.cultivator.state
			apply_progress(c.id, qp, "offline")
			gains.qp = qp
			gains.bottleneck = c.cultivator.state == "bottleneck"
		"temper_body":
			var xp := float(ContentDB.curve("offline_temper_body_xp_per_min", 10)) * minutes
			apply_body_xp(c.id, xp, "offline")
			gains.body_xp = xp
		"heal":
			_tick_injuries(c, minutes * 60.0, 3.0)
			gains.healed = true
		"contemplate":
			var dao := str(c.seclusion.get("dao", ""))
			if dao != "":
				var ins := float(ContentDB.curve("contemplate_offline_per_min", 5)) * minutes
				apply_insight(c.id, dao, ins, "contemplate")
				gains.insight = ins
		"refine_qi":
			var pp := float(ContentDB.curve("purity_offline_per_hour", 25)) * minutes / 60.0
			apply_purity(c.id, pp)
			gains.purity = pp
		"nourish_soul":
			var sp := float(ContentDB.curve("soul_offline_per_hour", 20)) * minutes / 60.0
			apply_soul(c.id, sp)
			gains.soul = sp
		"bath":
			gains = _bath_gains(c, str(c.seclusion.get("bath", "")), minutes)
		"settle_foundation":
			# G1: sit with what the pills gave you until it is your own; the residue burns off with it.
			var k: Dictionary = ContentDB.stat_const("pill_life", {})
			var cu2: CultivatorState = c.cultivator
			# S44: the share falls 5 points an hour and 5 residue burns off; no progress is made.
			if str(cu2.foundation.get("realm", "")) == ProgressionRules.great_realm(cu2.realm_key):
				var drop := float(cu2.foundation.get("total_qp", 0.0)) * float(k.get("settle_share_per_h", 0.05)) * minutes / 60.0
				gains.foundation = minf(drop, float(cu2.foundation.get("pill_qp", 0.0)))
				cu2.foundation.pill_qp = maxf(0.0, float(cu2.foundation.get("pill_qp", 0.0)) - drop)
				emit("foundation_changed", {"actor": c.id, "share": ProgressionRules.foundation_share(cu2)})
			var res := minf(cu2.residue, float(k.get("settle_residue_per_h", 5)) * minutes / 60.0)
			if res > 0.0:
				apply_residue(c.id, -res)
				gains.residue = res
	# Injuries also heal at their natural rate while away.
	if focus != "heal": _tick_injuries(c, minutes * 60.0, 1.0)
	if focus == "bath" and gains.get("injured", false): apply_injury(c.id, "body", 1)   # a bath too strong for the body (S44)
	c.seclusion = {}
	var result := {"gains": gains, "capped": span.capped, "hours": minutes / 60.0, "focus": focus}
	emit("offline_claimed", {"actor": c.id, "gains": gains, "capped": span.capped, "hours": minutes / 60.0, "focus": focus})
	return ok(result)

# ------------------------------------------------------------------ S49 leisure arts: the guqin and chess
## The guqin: a short piece on seven strings (the page scores the playing, 0-1). The steadier the hand, the faster
## meditation runs for half an hour; then the fingers need as long to rest.
func play_guqin(c, score: float) -> Dictionary:
	if c.inventory.count("guqin") <= 0: return fail("no_guqin", {"text": Tx.t("sim.progression.no_guqin")})
	var g: Dictionary = ContentDB.config("chess").get("guqin", {})
	var now := Clock.now_utc()
	if float(c.cooldowns.get("guqin_until", 0.0)) > now: return fail("resting", {"text": Tx.t("sim.progression.guqin_resting") % int(ceil((float(c.cooldowns.guqin_until) - now) / 60.0))})
	score = clampf(score, 0.0, 1.0) if is_finite(score) else 0.0
	var bonus := float(g.get("base", 0.05)) + float(g.get("per_score", 0.10)) * score
	game.combat.apply_buff(c.id, {"stat": "accumulation_rate", "op": "flat", "value": bonus, "duration": float(g.get("duration_s", 1800)), "source": "guqin"}, "guqin")
	c.cooldowns["guqin_until"] = now + float(g.get("rest_s", 1800))
	emit("guqin_played", {"actor": c.id, "score": score, "bonus": bonus})
	return ok({"bonus": bonus})

## An insight site's chess problem today (chess.json), the same on every device.
func chess_of(site: String) -> Dictionary:
	var all: Array = ContentDB.all("chess")
	if all.is_empty(): return {}
	var r := Rng.keyed(int(game.account.rng_seed), "chess:%s:%d" % [site, Clock.reset_day(Clock.now_utc())])
	return all[r.randi_range(0, all.size() - 1)]

func chess_open(c, site: String) -> bool:
	return int(c.cooldowns.get("chess:" + site, -1)) != Clock.reset_day(Clock.now_utc())

## One answer a day at each site: the right point gives insight into your deepest Dao.
func solve_chess(c, site: String, choice: String) -> Dictionary:
	var pz := chess_of(site)
	if pz.is_empty() or site == "": return fail("no_problem")
	if not chess_open(c, site): return fail("done", {"text": Tx.t("sim.progression.chess_done")})
	c.cooldowns["chess:" + site] = Clock.reset_day(Clock.now_utc())
	var right := choice == str(pz.answer)
	if right: apply_insight_best(c.id, float(ContentDB.config("chess").get("insight", 30)), "chess")
	emit("chess_solved", {"actor": c.id, "puzzle": str(pz.id), "site": site, "right": right})
	return ok({"right": right, "answer": str(pz.answer)})

## Insight into the Dao you know best (or, before any Dao, a little realm progress): the hermit's chess problem, and
## the insight sites' problems.
func apply_insight_best(actor_id: String, amount: float, context := "fortune") -> void:
	var c = game.character(actor_id)
	if c == null: return
	var best := ""
	var top := -1.0
	for dao in c.cultivator.daos:
		var v := float(c.cultivator.daos[dao].get("insight", 0.0)) + 1000.0 * int(c.cultivator.daos[dao].get("tier", 0))
		if v > top:
			top = v
			best = str(dao)
	if best != "" and Unlocks.is_unlocked(c.id, "dao_tree"): apply_insight(c.id, best, amount, context + ":chess:" + str(Clock.reset_day(Clock.now_utc())))
	else: apply_progress(c.id, 0.0, context, 0.02)
