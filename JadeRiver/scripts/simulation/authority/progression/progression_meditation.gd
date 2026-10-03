class_name ProgressionMeditation
extends ProgressionPart
## ProgressionAuthority's part: meditation (S06) and what breaks it, its speed term by term (decision 45), seclusion
## and medicinal baths (S07, S44), the offline claim, and the guqin (S49).

# ------------------------------------------------------------------ meditation (S06)
func start_meditation(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "cultivate"): return fail("locked", {"text": Unlocks.locked_text("cultivate")})
	if c.cultivator.meditating: return ok()
	var st: ActorState = game.actor_state(c.id)
	if st != null and st.surface == null: return fail("airborne")
	if game.combat.is_busy(c.id): return fail("busy")
	if game.combat.is_stunned(c.id): return fail("stunned")
	if progression.channels.has(c.id) or progression.tribulations.has(c.id): return fail("breaking_through")
	c.cultivator.meditating = true
	c.cultivator.meditation_settle = float(ContentDB.curve("meditation.settle_s", 1.0))
	c.cultivator.meditation_spot = game.room_rt.room_id if game.room_rt else ""
	progression.sec_accum[c.id] = 0.0
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
	var place := density
	if spring: density *= float(ContentDB.curve("qi_spring_mult", 2))
	return {"density": density, "spring": spring, "stone": stone, "place": place}

func accumulation_bonus(c) -> float:
	var bonus = c.stats.value("accumulation_rate")
	if ProgressionRules.realm_index(game.account.highest_realm) - ProgressionRules.realm_index(c.cultivator.realm_key) >= 2:
		bonus = (1.0 + bonus) * float(ContentDB.curve("ancestral_guidance", 1.5)) - 1.0
	bonus += 0.02 * game.account.legacy.size()
	bonus += game.pets.resonance(c)
	bonus += game.companions.paired_bonus(c)
	bonus -= ProgressionRules.residue_penalty(c.cultivator)   # residue does not drain on its own (G1)
	return bonus

## Decision 45: meditation's speed here and now, term by term, for the Cultivation page: {rate (cultivation a minute),
## base (curves meditation_qp_per_min), mult (rate over base), factors: [{id, label, x}] that multiply base to rate,
## bonus: [{label, pct}] that add up to the Bonuses factor (x = 1 + their sum)}. The factors are ProgressionRules
## .meditation_rate's own, at this spot (rules_tests checks their product against it).
func speed_breakdown(c) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	var mc := meditation_context(c)
	var bonus := accumulation_bonus(c)
	var base := float(ContentDB.curve("meditation_qp_per_min", 60))
	var rate := ProgressionRules.meditation_rate(c, float(mc.density), bonus)
	var factors: Array = []
	var add := func(id: String, label: String, x: float) -> void: factors.append({"id": id, "label": label, "x": x})
	if cu.method_id == "":
		return {"rate": 0.0, "base": base, "mult": 0.0, "factors": [], "bonus": [], "no_method": true}
	var room_name := str(game.room_rt.def.get("name", "")) if game.room_rt else ""
	add.call("early", Tx.t("ui.cultivation.speed_early"), ProgressionRules.early_meditation(ProgressionRules.level(c)))
	add.call("place", Tx.t("ui.cultivation.speed_place") % room_name, float(mc.place))
	if mc.spring: add.call("spring", Tx.t("ui.cultivation.speed_spring"), float(ContentDB.curve("qi_spring_mult", 2)))
	add.call("method", Tx.t("ui.cultivation.speed_method") % ContentDB.name_of("methods", cu.method_id), ProgressionRules.method_rate(c))
	add.call("stability", Tx.t("ui.cultivation.speed_stability") % str(cu.stability).capitalize(), ProgressionRules.stability_factor(cu.stability))
	var rows: Array = []
	for m in c.stats.modifiers:
		if str(m.get("stat", "")) != "accumulation_rate" or absf(float(m.get("value", 0.0))) < 0.0001: continue
		rows.append({"label": bonus_source_label(str(m.get("source", ""))), "pct": float(m.value), "left": float(m.get("remaining", -1.0))})
	var own: float = c.stats.value("accumulation_rate")
	if ProgressionRules.realm_index(game.account.highest_realm) - ProgressionRules.realm_index(cu.realm_key) >= 2:
		rows.append({"label": Tx.t("ui.cultivation.speed_ancestral"), "pct": (1.0 + own) * (float(ContentDB.curve("ancestral_guidance", 1.5)) - 1.0)})
	if game.account.legacy.size() > 0: rows.append({"label": Tx.t("ui.cultivation.speed_legacy"), "pct": 0.02 * game.account.legacy.size()})
	var res: float = game.pets.resonance(c)
	if res > 0.0: rows.append({"label": Tx.t("ui.cultivation.speed_pet"), "pct": res})
	var pair: float = game.companions.paired_bonus(c)
	if pair > 0.0: rows.append({"label": Tx.t("ui.cultivation.speed_paired"), "pct": pair})
	var residue := ProgressionRules.residue_penalty(cu)
	if residue > 0.0: rows.append({"label": Tx.t("ui.cultivation.speed_residue"), "pct": -residue})
	if absf(bonus) > 0.0001: add.call("bonus", Tx.t("ui.cultivation.speed_bonus"), 1.0 + bonus)
	if cu.consolidation_penalty: add.call("consolidating", Tx.t("ui.cultivation.speed_consolidating"), 0.5)
	return {"rate": rate, "base": base, "mult": rate / base, "factors": factors, "bonus": rows}

## The name a cultivation-speed modifier shows under: its item (by the source its buff carries), title, vow or fate,
## the guqin, or the source itself.
static func bonus_source_label(source: String) -> String:
	var parts := source.split(":")
	match parts[0]:
		"title": return ContentDB.name_of("titles", parts[1]) if parts.size() > 1 else source
		"vow": return ContentDB.name_of("vows", parts[1]) if parts.size() > 1 else source
		"fate": return ContentDB.name_of("fates", parts[2]) if parts.size() > 2 else source
		"guqin": return ContentDB.item_name("guqin")
	for it in ContentDB.all("items"):
		for u in it.get("use", []):
			if str(u.get("kind", "")) == "add_modifier" and str(u.get("source", "")) == source: return str(it.get("name", source)) if source != "qi_incense" else Tx.t("ui.cultivation.speed_incense")
	return source.capitalize()

func meditation_second(c) -> void:
	var cu: CultivatorState = c.cultivator
	var mc := meditation_context(c)
	var mult := 2.0 if mc.spring else 1.0
	var regen: Dictionary = ContentDB.stat_const("regen_per_s", {})
	var m := float(regen.get("meditate_mult", 8))
	var gains := {}
	gains.hp = c.pools.max_hp * c.stats.value("hp_regen") * m * mult
	game.combat.apply_resource_change(c.id, "hp", gains.hp, "meditation")
	if c.pools.max_qi > 0:
		gains.qi = CombatAuthority.qi_regen_pool(c) * c.stats.value("qi_regen") * m * mult
		game.combat.apply_resource_change(c.id, "qi", gains.qi, "meditation")
	if c.pools.max_soul > 0:
		game.combat.apply_resource_change(c.id, "soul", c.pools.max_soul * c.stats.value("soul_regen") * m * mult, "meditation")
	if Unlocks.is_unlocked(c.id, "composure"):
		game.combat.apply_resource_change(c.id, "composure", 100.0 / float(ContentDB.stat_const("composure.meditate_full_s", 5)), "meditation")
	game.combat.apply_resource_change(c.id, "hollowing", -float(ContentDB.stat_const("hollowing.decay_per_min", 1)) * float(ContentDB.stat_const("hollowing.meditate_mult", 3)) / 60.0, "meditation")
	if Unlocks.is_unlocked(c.id, "cultivation"):
		var rate := ProgressionRules.meditation_rate(c, float(mc.density), accumulation_bonus(c))
		gains.qp = rate / 60.0
		progression.apply_progress(c.id, gains.qp, "meditation")
	if Unlocks.is_unlocked(c.id, "foundation") and cu.stability != "stable" and cu.stability != "solid":
		cu.stability_progress += 1.0
		if cu.stability_progress >= float(ContentDB.curve("stability_step_s", 120)):
			cu.stability_progress = 0.0
			progression.condition.step_stability(c, 1)
	if c.pools.max_qi > 0 and ProgressionRules.at_least(cu.realm_key, "cloud_stride_1"):
		progression.apply_purity(c.id, float(ContentDB.curve("purity_meditate_per_hour", 10)) / 3600.0)
	if c.pools.max_soul > 0:
		progression.apply_soul(c.id, float(ContentDB.curve("soul_meditate_per_hour", 10)) / 3600.0)
	if mc.stone != "":
		var site := float(ContentDB.stat_const("gates", {}).get("insight_site_mult", 2.0)) if StatRules.gate_flag(c, "insight_sites_double") else 1.0   # S10 Insight 50
		progression.apply_insight(c.id, mc.stone, float(ContentDB.curve("insight_stone_per_min", 20)) / 60.0 * mult * site, "insight_stone")
	if cu.heart_demon > 0.0:
		progression.apply_heart_demon(c.id, -float(ContentDB.stat_const("heart_demon", {}).get("meditate_drain_per_min", 0.2)) / 60.0, "meditation")   # -1 per 5 min (S48)
	if str(c.position.get("room", "")) == "cf_falls_pool" and Clock.time_of_day() == "night": progression.body.falls_pool_second(c)
	emit("meditation_tick", {"actor": c.id, "gains": gains, "spring": mc.spring, "paired": game.companions.paired_bonus(c) > 0.0})

func on_hit_landed(p: Dictionary) -> void:
	var c = game.character(str(p.get("target", "")))
	if c == null or int(p.get("amount", 0)) <= 0: return
	if c.cultivator.meditating:
		stop_meditation(c, "backlash")
		game.combat.apply_backlash(c.id)
		emit("qi_backlash", {"actor": c.id})
	if progression.channels.has(c.id):
		progression.channels.erase(c.id)
		progression.realms.fail_breakthrough(c, "interruption", Rng.stream(c.id, "breakthrough"))

# ------------------------------------------------------------------ seclusion (S07)
func enter_seclusion(c, focus: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "seclusion"): return fail("locked", {"text": Unlocks.locked_text("seclusion")})
	var allowed := {"accumulate": "seclusion", "temper_body": "seclusion", "heal": "seclusion", "contemplate": "insight_sites",
		"refine_qi": "refine_qi", "nourish_soul": "nourish_soul", "settle_foundation": "seclusion"}
	if not allowed.has(focus) or not Unlocks.is_unlocked(c.id, allowed[focus]): return fail("focus_locked")
	var room = game.room_rt.def if game.room_rt else {}
	var spot := str(room.get("id", ""))
	if not room.get("safe", false): spot = str(c.last_shrine.get("room", spot))
	c.seclusion = {"spot": spot, "focus": focus, "started_utc": Clock.now_utc(), "dao": progression.contemplate.get(c.id, ""),
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
	progression.apply_body_xp(c.id, xp, "bath")
	gains.body_xp = xp
	var cu: CultivatorState = c.cultivator
	var res := minf(cu.residue, float(b.get("residue", 0)) * f)
	if res > 0.0:
		progression.apply_residue(c.id, -res)
		gains.residue = res
	if str(cu.foundation.get("realm", "")) == ProgressionRules.great_realm(cu.realm_key):
		var drop := float(cu.foundation.get("total_qp", 0.0)) * float(b.get("share", 0.1)) * f
		gains.foundation = minf(drop, float(cu.foundation.get("pill_qp", 0.0)))
		cu.foundation.pill_qp = maxf(0.0, float(cu.foundation.get("pill_qp", 0.0)) - drop)
		emit("foundation_changed", {"actor": c.id, "share": ProgressionRules.foundation_share(cu)})
	progression.apply_toxicity(c.id, float(b.get("toxicity", 0)) * f)
	# The injury itself is dealt after the seclusion's natural healing, so an hour away does not mend it at once.
	if StatRules.grade_index(str(ContentDB.item(item_id).get("grade", "plain"))) - 1 > ProgressionRules.body_tier_index(cu):
		gains.injured = true
	# S48: a full soak the body could hold counts toward the body tier the bath belongs to.
	elif f >= 0.999:
		for t in ContentDB.all("body_tiers"):
			if str(t.get("bath", "")) == item_id and not str(t.id) in cu.body_baths:
				cu.body_baths.append(str(t.id))
				gains.body_bath = str(t.id)
		if gains.has("body_bath"): progression.body.check_body_tier(c)
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
			progression.apply_progress(c.id, qp, "offline")
			gains.qp = qp
			gains.bottleneck = c.cultivator.state == "bottleneck"
		"temper_body":
			var xp := float(ContentDB.curve("offline_temper_body_xp_per_min", 10)) * minutes
			progression.apply_body_xp(c.id, xp, "offline")
			gains.body_xp = xp
		"heal":
			progression.condition.tick_injuries(c, minutes * 60.0, 3.0)
			gains.healed = true
		"contemplate":
			var dao := str(c.seclusion.get("dao", ""))
			if dao != "":
				var ins := float(ContentDB.curve("contemplate_offline_per_min", 5)) * minutes
				progression.apply_insight(c.id, dao, ins, "contemplate")
				gains.insight = ins
		"refine_qi":
			var pp := float(ContentDB.curve("purity_offline_per_hour", 25)) * minutes / 60.0
			progression.apply_purity(c.id, pp)
			gains.purity = pp
		"nourish_soul":
			var sp := float(ContentDB.curve("soul_offline_per_hour", 20)) * minutes / 60.0
			progression.apply_soul(c.id, sp)
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
				progression.apply_residue(c.id, -res)
				gains.residue = res
	# Injuries also heal at their natural rate while away.
	if focus != "heal": progression.condition.tick_injuries(c, minutes * 60.0, 1.0)
	if focus == "bath" and gains.get("injured", false): progression.apply_injury(c.id, "body", 1)   # a bath too strong for the body (S44)
	c.seclusion = {}
	var result := {"gains": gains, "capped": span.capped, "hours": minutes / 60.0, "focus": focus}
	emit("offline_claimed", {"actor": c.id, "gains": gains, "capped": span.capped, "hours": minutes / 60.0, "focus": focus})
	return ok(result)

# ------------------------------------------------------------------ S49 leisure arts: the guqin
## The guqin: a short piece on seven strings (the page scores the playing, 0-1). The steadier the hand, the faster
## meditation runs for half an hour; then the fingers need as long to rest.
func play_guqin(c, score: float) -> Dictionary:
	if c.inventory.count("guqin") <= 0: return fail("no_guqin", {"text": Tx.t("sim.progression.no_guqin")})
	var g: Dictionary = ContentDB.config("chess").get("guqin", {})
	var now := Clock.now_utc()
	if float(c.cooldowns.get("guqin_until", 0.0)) > now: return fail("resting", {"text": Tx.t("sim.progression.guqin_resting") % Tx.span(float(c.cooldowns.guqin_until) - now)})
	score = clampf(score, 0.0, 1.0) if is_finite(score) else 0.0
	var bonus := float(g.get("base", 0.05)) + float(g.get("per_score", 0.10)) * score
	game.combat.apply_buff(c.id, {"stat": "accumulation_rate", "op": "flat", "value": bonus, "duration": float(g.get("duration_s", 1800)), "source": "guqin"}, "guqin")
	c.cooldowns["guqin_until"] = now + float(g.get("rest_s", 1800))
	emit("guqin_played", {"actor": c.id, "score": score, "bonus": bonus})
	return ok({"bonus": bonus})
