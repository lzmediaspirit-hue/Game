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
var last_level: Dictionary = {}

func intents() -> Array:
	return ["start_meditation", "stop_meditation", "toggle_meditation", "start_breakthrough", "learn_method", "switch_method",
		"open_meridian", "reset_meridians", "equip_technique", "unequip_technique", "rank_up_technique", "set_contemplate",
		"enter_seclusion", "claim_offline", "use_treatment", "train_object"]

func subscribe() -> void:
	GameEvents.subscribe("hit_landed", _on_hit_landed, 30)
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 30)
	GameEvents.subscribe("player_gravely_wounded", _on_gravely_wounded, 30)
	GameEvents.subscribe("technique_used", _on_technique_used, 30)
	GameEvents.subscribe("object_hit", _on_object_hit, 30)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"start_meditation": return start_meditation(c)
		"stop_meditation": return stop_meditation(c, str(intent.get("reason", "moved")))
		"toggle_meditation": return stop_meditation(c, "tapped") if c.cultivator.meditating else start_meditation(c)
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
		"claim_offline": return claim_offline(c, float(intent.get("elapsed", 0.0)))
		"train_object": return fail("use_attack")
	return fail("unknown_intent")

# ------------------------------------------------------------------ meditation (S06)
func start_meditation(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "cultivate"): return fail("locked", {"text": Unlocks.locked_text("cultivate")})
	if c.cultivator.meditating: return ok()
	var st: ActorState = game.actor_state(c.id)
	if st != null and st.surface == null: return fail("airborne")
	if game.combat.is_busy(c.id): return fail("busy")
	if game.combat.is_stunned(c.id): return fail("stunned")
	if channels.has(c.id): return fail("breaking_through")
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
	if spring: density *= float(ContentDB.curve("qi_spring_mult", 2))
	return {"density": density, "spring": spring, "stone": stone}

func accumulation_bonus(c) -> float:
	var bonus = c.stats.value("accumulation_rate")
	if ProgressionRules.realm_index(game.account.highest_realm) - ProgressionRules.realm_index(c.cultivator.realm_key) >= 2:
		bonus = (1.0 + bonus) * float(ContentDB.curve("ancestral_guidance", 1.5)) - 1.0
	bonus += 0.02 * game.account.legacy.size()
	return bonus

func tick(delta: float) -> void:
	var c = game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	_tick_channel(c, delta)
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
		apply_insight(c.id, mc.stone, float(ContentDB.curve("insight_stone_per_min", 20)) / 60.0 * mult, "insight_stone")
	emit("meditation_tick", {"actor": c.id, "gains": gains, "spring": mc.spring})

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
	if cu.state == "bottleneck":
		var factor := float(ContentDB.curve("ceiling_stored_qi_mult", 0.25)) if at_zone_ceiling(c) else 1.0
		cu.stored_qi = minf(ProgressionRules.stored_qi_cap(c), cu.stored_qi + amount * factor)
	else:
		cu.qp += amount
		if cu.qp >= n:
			var surplus := cu.qp - n
			cu.qp = n
			if cu.state != "consolidating" or cu.consolidation_left <= 0.0: cu.state = "bottleneck"
			else: cu.state = "bottleneck"
			cu.stored_qi = minf(ProgressionRules.stored_qi_cap(c), cu.stored_qi + surplus)
			cu.bottleneck_seconds = 0.0
			emit("bottleneck_reached", {"actor": c.id, "realm_key": cu.realm_key, "major": ProgressionRules.is_major(cu.realm_key),
				"requirements": query_requirements(c)})
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": source, "amount": amount})
	var after_level := ProgressionRules.level(c)
	if after_level != before_level: _levels_gained(c, before_level, after_level)

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
			results.append({"ok": false, "hard": true, "cause": "environment", "text": "This land cannot support %s" % ContentDB.name_of("realms", to), "fix": "page:world_map", "kind": "zone_supports"})
			hard_ok = false
	var supports := 0
	var reasons: Array = []
	for item_id in support_items:
		var p: Dictionary = ContentDB.item(str(item_id)).get("pill", {})
		var sup: Dictionary = ContentDB.item(str(item_id)).get("support", {})
		if sup.is_empty() or c.inventory.count(str(item_id)) <= 0: continue
		if sup.has("event") and str(sup.event) != str(spec.get("event", "")): continue
		supports += 1
		reasons.append("%s lowers risk" % ContentDB.item_name(str(item_id)))
	var soft := RequirementRules.soft_unmet(results)
	if soft > 0: reasons.append("%d unmet soft requirement(s)" % soft)
	var unstable := cu.stability == "unstable"
	if unstable: reasons.append("Your foundation is Unstable")
	if not cu.injuries.is_empty(): reasons.append("%d untreated injury" % cu.injuries.size())
	var retreat := bool(game.room_rt.def.get("retreat", false)) if game.room_rt else false
	if retreat: reasons.append("Retreat room")
	var word := ProgressionRules.risk_word(ProgressionRules.risk_index(soft, unstable, cu.injuries.size(), mini(supports, 3), retreat)) if major else "none"
	var can := cu.state == "bottleneck" and hard_ok and cu.breakthrough_cooldown <= 0.0 and not channels.has(c.id)
	var blocked := ""
	if cu.state != "bottleneck": blocked = "Keep accumulating: %d%%" % int(cu.progress_fraction() * 100)
	elif cu.breakthrough_cooldown > 0.0: blocked = "Your mind needs rest (%ds)" % int(cu.breakthrough_cooldown)
	elif not hard_ok: blocked = "A hard requirement is unmet"
	return {"from": cu.realm_key, "to": to, "major": major, "results": results, "risk": word, "reasons": reasons,
		"success": ProgressionRules.success_chance(word) if major else 1.0, "can": can, "blocked": blocked,
		"event": str(spec.get("event", "")) if major else "", "zone_ok": zone_ok}

func start_breakthrough(c, support_items: Array) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "cultivation"): return fail("locked")
	if game.room_rt and game.room_rt.event.get("active", false): return fail("event_running")
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
	for item_id in support_items:
		if used.size() >= 3: break
		if ContentDB.item(str(item_id)).has("support") and c.inventory.count(str(item_id)) > 0:
			game.inventory.apply_remove(c.id, str(item_id), 1, "breakthrough_support")
			used.append(item_id)
	var unmet_causes: Array = []
	for r in q.results:
		if not r.ok: unmet_causes.append(r.cause)
	channels[c.id] = {"to": q.to, "risk": q.risk, "remaining": CHANNEL_S, "causes": unmet_causes, "used": used, "from": c.cultivator.realm_key}
	emit("breakthrough_started", {"actor": c.id, "from": c.cultivator.realm_key, "to": q.to, "risk": q.risk, "duration": CHANNEL_S})
	return ok({"result": "channeling", "risk": q.risk})

func _tick_channel(c, delta: float) -> void:
	if not channels.has(c.id): return
	var ch: Dictionary = channels[c.id]
	ch.remaining = float(ch.remaining) - delta
	if ch.remaining > 0.0: return
	channels.erase(c.id)
	var rng := Rng.stream(c.id, "breakthrough")
	# The Prologue's first step on Lu's boat is taught, not gambled (realm flag `guaranteed`).
	var guaranteed := bool(ProgressionRules.breakthrough_spec(str(ch.get("from", c.cultivator.realm_key))).get("guaranteed", false))
	if guaranteed or rng.randf() < ProgressionRules.success_chance(str(ch.risk)):
		_advance(c, str(ch.to), true)
	else:
		_fail_breakthrough(c, ProgressionRules.pick_failure(rng, ch.causes, c.cultivator.realm_key), rng)

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
	if major and energy == "true_qi" and ContentDB.realm(from).get("energy") != "true_qi": cu.purity = mini(cu.purity, 9)
	emit("breakthrough_succeeded", {"actor": c.id, "from": from, "to": to, "major": major})
	emit("realm_changed", {"actor": c.id, "from": from, "to": to, "major": major, "level": ProgressionRules.level(c)})
	var after_level := ProgressionRules.level(c)
	_levels_gained(c, before_level, after_level)
	_reveal_aptitudes(c)
	if cu.qp >= n and n > 0:
		cu.qp = n
		cu.state = "bottleneck"
		emit("bottleneck_reached", {"actor": c.id, "realm_key": to, "major": ProgressionRules.is_major(to), "requirements": query_requirements(c)})
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": "breakthrough", "amount": 0})

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
	if c == null or p.get("no_penalty", false): return
	var cu: CultivatorState = c.cultivator
	var loss := float(ContentDB.stat_const("death.progress_loss", 0.1))
	if cu.state != "bottleneck":
		cu.qp = maxf(0.0, cu.qp - cu.need() * loss)
	else:
		cu.stored_qi = maxf(0.0, cu.stored_qi - cu.need() * loss)
	# "May carry an injury" (S31): a coin flip, and defeats alone never push it past severity 2.
	var rng := Rng.stream(c.id, "combat")
	if rng.randf() < float(ContentDB.stat_const("death.injury_chance", 0.5)) and int(cu.injuries.get("body", {}).get("severity", 0)) < 2:
		apply_injury(c.id, "body", 1)
	if p.get("cause", "") == "soul": apply_injury(c.id, "soul", 1)
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
	if leveled: emit("body_level_changed", {"actor": c.id, "value": c.cultivator.body_level})

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

func apply_insight(actor_id: String, dao: String, amount: float, context: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("daos", dao): return
	if not Unlocks.is_unlocked(c.id, "dao_tree") and not context.begins_with("kill") and not Unlocks.is_unlocked(c.id, "weapon_dao"): return
	var mem: Dictionary = c.cultivator.insight_memory
	var window := float(ContentDB.curve("insight_repeat_window_s", 60))
	var key := context.get_slice(":", 0) + ":" + context.get_slice(":", 1) + ":" + context.get_slice(":", 2)
	if mem.has(key) and game.sim_time - float(mem[key]) < window: amount *= float(ContentDB.curve("insight_repeat_factor", 0.2))
	mem[key] = game.sim_time
	if mem.size() > 64: mem.clear()
	amount *= 1.0 + c.stats.value("insight_rate")
	var d: Dictionary = c.cultivator.daos.get(dao, {"tier": 0, "insight": 0.0})
	d.insight = float(d.insight) + amount
	var cap := int(ContentDB.entry("daos", dao).get("valley_cap", 6))
	var tier := mini(ProgressionRules.dao_tier_for(float(d.insight)), cap)
	var gained := tier > int(d.tier)
	d.tier = maxi(int(d.tier), tier)
	c.cultivator.daos[dao] = d
	emit("insight_gained", {"actor": c.id, "dao": dao, "amount": amount})
	if gained: emit("dao_tier_up", {"actor": c.id, "dao": dao, "tier": d.tier})

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
	emit("toxicity_changed", {"actor": c.id, "value": c.cultivator.toxicity})
	if amount > 0 and c.cultivator.toxicity > c.stats.value("toxicity_tolerance"):
		apply_injury(c.id, "meridian", 1)

func apply_stability(actor_id: String, word: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cultivator.stability = word
	emit("stability_changed", {"actor": c.id, "word": word})

func apply_learn_method(actor_id: String, method_id: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("methods", method_id): return
	if not c.cultivator.methods_known.has(method_id): c.cultivator.methods_known.append(method_id)
	if c.cultivator.method_id == "":
		c.cultivator.method_id = method_id
		emit("method_changed", {"actor": c.id, "method": method_id})
	emit("method_learned", {"actor": c.id, "method": method_id})

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
	if c.inventory.count("meridian_reversal_pill") <= 0: return fail("needs_pill", {"text": "Needs a Meridian Reversal Pill"})
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
	if not Unlocks.is_unlocked(c.id, "technique_slots_8"): return fail("locked", {"text": "Mastery beyond tier 3 opens at Qi Unfurling 6"})
	if float(m.points) < ProgressionRules.mastery_needed(int(m.tier)): return fail("need_practice", {"text": "Practise more"})
	if c.inventory.count("manual_page") <= 0: return fail("need_manual", {"text": "Needs a manual page"})
	game.inventory.apply_remove(c.id, "manual_page", 1, "rank_up")
	m.tier = int(m.tier) + 1
	m.points = 0.0
	emit("technique_mastery_up", {"actor": c.id, "technique": tid, "tier": m.tier})
	return ok()

# ------------------------------------------------------------------ seclusion (S07)
func enter_seclusion(c, focus: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "seclusion"): return fail("locked", {"text": Unlocks.locked_text("seclusion")})
	var allowed := {"accumulate": "seclusion", "temper_body": "seclusion", "heal": "seclusion", "contemplate": "insight_sites",
		"refine_qi": "refine_qi", "nourish_soul": "nourish_soul"}
	if not allowed.has(focus) or not Unlocks.is_unlocked(c.id, allowed[focus]): return fail("focus_locked")
	var room = game.room_rt.def if game.room_rt else {}
	var spot := str(room.get("id", ""))
	if not room.get("safe", false): spot = str(c.last_shrine.get("room", spot))
	c.seclusion = {"spot": spot, "focus": focus, "started_utc": Clock.now_utc(), "dao": contemplate.get(c.id, ""),
		"cap_h": seclusion_cap(room), "density": float(room.get("qi_density", 1.0))}
	emit("seclusion_entered", {"actor": c.id, "focus": focus, "spot": spot})
	return ok()

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
	# Injuries also heal at their natural rate while away.
	if focus != "heal": _tick_injuries(c, minutes * 60.0, 1.0)
	c.seclusion = {}
	var result := {"gains": gains, "capped": span.capped, "hours": minutes / 60.0, "focus": focus}
	emit("offline_claimed", {"actor": c.id, "gains": gains, "capped": span.capped, "hours": minutes / 60.0, "focus": focus})
	return ok(result)
