class_name ProgressionTechniques
extends ProgressionPart
## ProgressionAuthority's part: cultivation methods and switching them, meridians, techniques learned, slotted and
## mastered, the dual loadout's bars (S47), secret arts, and Inner Arts and stances (S48).

# ------------------------------------------------------------------ methods, meridians and techniques
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
	progression.apply_heart_demon(c.id, float(ContentDB.stat_const("heart_demon", {}).get("method_switch", 10)), "method_switch")
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

func apply_reset_meridians(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var total := 0
	for ch in c.cultivator.meridians:
		total += int(c.cultivator.meridians[ch])
		c.cultivator.meridians[ch] = 0
	c.cultivator.unspent_meridian_points += total
	emit("attributes_changed", {"actor": c.id, "reason": "reset"})

func apply_learn_technique(actor_id: String, tid: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("techniques", tid): return
	if c.cultivator.techniques_known.has(tid):
		# P13a: an art realised on its tree and then taught (a teacher, a quest, a manual) is taught now: its node's
		# Realisations come back (technique_plan §4.3).
		if c.cultivator.tree.realised.has(tid): c.cultivator.tree.realised.erase(tid)
		return
	c.cultivator.techniques_known.append(tid)
	if not c.cultivator.mastery.has(tid): c.cultivator.mastery[tid] = {"tier": 1, "points": 0.0}   # P13a: an art let go and realised again keeps its mastery
	emit("technique_learned", {"actor": c.id, "technique": tid})
	var slots := ProgressionRules.technique_slot_count(c)
	for i in slots:
		if c.cultivator.technique_slots[i] == null and TechniqueTreeRules.heavy_fits(c.cultivator.technique_slots, i, tid):
			c.cultivator.technique_slots[i] = tid
			emit("technique_equipped", {"actor": c.id, "technique": tid, "slot": i})
			break

func apply_learn_secret_art(actor_id: String, art: String) -> void:
	var c = game.character(actor_id)
	if c == null or c.cultivator.secret_arts.has(art): return
	c.cultivator.secret_arts.append(art)
	emit("secret_art_learned", {"actor": c.id, "art": art})

func equip_technique(c, slot: int, tid: String) -> Dictionary:
	var n := ProgressionRules.technique_slot_count(c)
	if slot < 0 or slot >= n: return fail("slot_locked")
	if tid != "" and not c.cultivator.techniques_known.has(tid): return fail("unknown_technique")
	# P13a (technique_plan §6.3): a heavy art, a keystone or a lost art, is one to a ring of four.
	if tid != "" and not TechniqueTreeRules.heavy_fits(c.cultivator.technique_slots, slot, tid): return fail("heavy_cap", {"text": Tx.t("sim.tree.heavy_cap")})
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

func on_technique_used(p: Dictionary) -> void:
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
	if dao != "" and dao != "none": progression.apply_insight(c.id, dao, 1.0, "tech:%s:%s" % [tid, str(p.get("target_def", ""))])

## S47 dual loadout: each weapon keeps its own technique bar. The bar in use is put away with the weapon, and the
## other weapon's bar comes out (the first swap starts it as a copy). No Dao tier is touched by a swap.
func on_loadout_swapped(p: Dictionary) -> void:
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
		if not ProgressionRules.stance_known(c, st): return fail("technique", {"text": Tx.t("sim.progression.stance_needs_technique") % ContentDB.name_of("techniques", str(st.technique))})
		c.cultivator.stances[family] = stance
	else:
		c.cultivator.stances.erase(family)
	emit("stance_changed", {"actor": c.id, "family": family, "stance": stance})
	return ok({"family": family, "stance": stance})
