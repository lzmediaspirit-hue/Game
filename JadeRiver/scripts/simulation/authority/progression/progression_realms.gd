class_name ProgressionRealms
extends ProgressionPart
## ProgressionAuthority's part: Qi progress and the bottleneck (S05), the foundation's pill share (G1), levels and
## meridian points, breakthroughs from the preview to the roll (S05, S48), Qi Deviation, Core Forging, failures, the
## aptitudes, and what a kill or a grave wound does to progress.

# ------------------------------------------------------------------ accumulation (S05)
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
	if after_level != before_level: levels_gained(c, before_level, after_level)

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

func levels_gained(c, from_level: int, to_level: int) -> void:
	for lv in range(from_level + 1, to_level + 1):
		if lv > c.cultivator.meridian_levels_granted:
			c.cultivator.unspent_meridian_points += ProgressionRules.meridian_points_for_level(lv)
			c.cultivator.meridian_levels_granted = lv
	emit("level_changed", {"actor": c.id, "level": to_level})

# ------------------------------------------------------------------ breakthroughs (S05, S48)
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
	var can := cu.state == "bottleneck" and hard_ok and cu.breakthrough_cooldown <= 0.0 and not progression.channels.has(c.id)
	var blocked := ""
	if cu.state != "bottleneck": blocked = Tx.t("sim.progression.keep_accumulating") % int(cu.progress_fraction() * 100)
	elif cu.breakthrough_cooldown > 0.0: blocked = Tx.t("sim.progression.your_mind_needs_rest_ds") % Tx.span(cu.breakthrough_cooldown)
	elif not hard_ok: blocked = Tx.t("sim.progression.a_hard_requirement_is_unmet")
	return {"from": cu.realm_key, "to": to, "major": major, "results": results, "risk": word, "reasons": reasons,
		"success": ProgressionRules.success_chance(word) if major else 1.0, "can": can, "blocked": blocked,
		"event": str(spec.event) if major and spec.get("event") != null else "", "zone_ok": zone_ok, "hollow": hollow, "heart_demon_steps": demon_steps, "merit": merit, "supports_used": supports_used}

func start_breakthrough(c, support_items: Array) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "cultivation"): return fail("locked")
	if game.room_rt and game.room_rt.event.get("active", false): return fail("event_running")
	if progression.channels.has(c.id) or progression.tribulations.has(c.id): return fail("breaking_through")
	var q := query_breakthrough(c, support_items)
	if not q.can: return fail("cannot", {"text": q.blocked, "query": q})
	progression.stop_meditation(c, "breakthrough")
	if not q.major:
		advance(c, str(q.to), false)
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
	if used.size() >= int(hd.get("forced_supports", 2)): progression.apply_heart_demon(c.id, float(hd.get("forced_breakthrough", 5)), "forced_breakthrough")
	if int(q.get("merit", 0)) > 0: game.relations.apply_merit_used(c.id, ProgressionRules.great_realm(c.cultivator.realm_key))
	var bonus := progression.spend_fate_next(c, "breakthrough_bonus")   # S48 Scar of Failure: the next attempt only
	progression.channels[c.id] = {"to": q.to, "risk": q.risk, "remaining": ProgressionAuthority.CHANNEL_S, "causes": unmet_causes, "used": used, "from": c.cultivator.realm_key,
		"hollow": bool(q.get("hollow", false)), "bonus": bonus}
	emit("breakthrough_started", {"actor": c.id, "from": c.cultivator.realm_key, "to": q.to, "risk": q.risk, "duration": ProgressionAuthority.CHANNEL_S})
	return ok({"result": "channeling", "risk": q.risk})

func tick_channel(c, delta: float) -> void:
	if not progression.channels.has(c.id): return
	var ch: Dictionary = progression.channels[c.id]
	ch.remaining = float(ch.remaining) - delta
	if ch.remaining > 0.0: return
	progression.channels.erase(c.id)
	# S48: from Cloud Stride on, the heavens test a major breakthrough before it is settled.
	var from0 := str(ch.get("from", c.cultivator.realm_key))
	if not ProgressionRules.tribulation_row(from0).is_empty():
		progression.tribulation.start_tribulation(c, ch)
		return
	settle_breakthrough(c, ch)

## The roll that decides a major breakthrough, after the channel (and any tribulation) is through.
func settle_breakthrough(c, ch: Dictionary) -> void:
	var rng := Rng.stream(c.id, "breakthrough")
	# The Prologue's first step on Lu's boat is taught, not gambled (realm flag `guaranteed`).
	var guaranteed := bool(ProgressionRules.breakthrough_spec(str(ch.get("from", c.cultivator.realm_key))).get("guaranteed", false))
	if guaranteed or rng.randf() < ProgressionRules.success_chance(str(ch.risk)) + float(ch.get("bonus", 0.0)):
		advance(c, str(ch.to), true)
		if not guaranteed: progression.fates.offer_fates(c)
	else:
		var from := str(ch.get("from", c.cultivator.realm_key))
		if not (ch.get("used", []) as Array).is_empty():
			c.cultivator.support_failures[from] = int(c.cultivator.support_failures.get(from, 0)) + 1
		# A hollow foundation gives way where it is weakest (G1).
		var failure := "weak_foundation" if ch.get("hollow", false) and ContentDB.has_entry("failures", "weak_foundation") \
			else ProgressionRules.pick_failure(rng, ch.causes, c.cultivator.realm_key)
		fail_breakthrough(c, failure, rng)
		maybe_deviate(c, str(ch.risk))

## S48 Qi Deviation: a failure at Severe risk, or on a Poor-compatibility method, sends the Qi astray for 10 minutes.
func maybe_deviate(c, risk: String) -> void:
	if not ProgressionRules.qi_deviates(risk, ProgressionRules.method_compatibility(c, c.cultivator.method_id)): return
	game.combat.apply_status(c.id, "qi_deviation", float(ContentDB.stat_const("qi_deviation", {}).get("duration_s", 600)), 1.0)
	if not game.account.codex.has("qi_deviation"): game.quest.apply_codex("qi_deviation")
	emit("qi_deviation", {"actor": c.id, "risk": risk, "duration": float(ContentDB.stat_const("qi_deviation", {}).get("duration_s", 600))})

func is_channeling(actor_id: String) -> bool:
	return progression.channels.has(actor_id)

func advance(c, to: String, major: bool) -> void:
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
	if major and energy == "true_qi" and ContentDB.realm(from).get("energy") != "true_qi": forge_core(c)
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
	levels_gained(c, before_level, after_level)
	_reveal_aptitudes(c)
	if cu.qp >= n and n > 0:
		cu.qp = n
		cu.state = "bottleneck"
		_bottleneck(c, to)
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": "breakthrough", "amount": 0})

## S48 Core Forging: the Heart Tempering 9 -> Cloud Stride 1 step sets the purity grade the core forms at. Each
## preparation point met counts on a roll under 80% (breakthrough stream); a flawless Cleansing is one more.
func forge_core(c) -> void:
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

func fail_breakthrough(c, failure_id: String, rng: RandomNumberGenerator) -> void:
	var cu: CultivatorState = c.cultivator
	var f := ContentDB.entry("failures", failure_id)
	var loss := ProgressionRules.failure_loss(rng, failure_id)
	cu.qp = maxf(0.0, cu.need() * (1.0 - loss))
	cu.state = "accumulating" if cu.qp < cu.need() else "bottleneck"
	var injuries: Array = []
	if f.has("injury"):
		progression.apply_injury(c.id, str(f.injury.kind), int(f.injury.severity))
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

func apply_event_passed(actor_id: String, event: String) -> void:
	var c = game.character(actor_id)
	if c == null or event in c.cultivator.events_passed: return
	c.cultivator.events_passed.append(event)
	emit("event_passed", {"actor": c.id, "event": event})

# ------------------------------------------------------------------ reactions
func on_actor_defeated(p: Dictionary) -> void:
	var c = game.character(str(p.get("killer", "")))
	if c == null or p.get("victim_kind", "") != "enemy": return
	progression.body.count_streak(c)
	var lv := int(p.get("level", 1))
	if Unlocks.is_unlocked(c.id, "kill_progress"):
		apply_progress(c.id, ProgressionRules.kill_qp(ProgressionRules.level(c), lv, str(p.get("role", "normal"))), "kill")
	if Unlocks.is_unlocked(c.id, "body_training"):
		progression.apply_body_xp(c.id, ProgressionRules.kill_body_xp(lv), "kill")
	if Unlocks.is_unlocked(c.id, "weapon_dao"):
		var fam := StatRules.family(c)
		progression.apply_insight(c.id, str(fam.get("dao", "fist")), 1.0, "kill:" + str(p.get("def", "")) + ":" + str(p.get("room", "")))

func on_gravely_wounded(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	# Struck down by a foe while the heavens were testing you: the breakthrough fails with the body (S48).
	if progression.tribulations.has(c.id): progression.tribulation.end_tribulation(c, false, "bodily_failure")
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
		progression.apply_injury(c.id, "body", 1)
	if p.get("cause", "") == "soul": progression.apply_injury(c.id, "soul", 1)
	progression.apply_heart_demon(c.id, float(ContentDB.stat_const("heart_demon", {}).get("death", 3)), "defeat")
	emit("progress_changed", {"actor": c.id, "progress": cu.progress_fraction(), "stored": cu.stored_qi, "source": "wounded", "amount": 0})
