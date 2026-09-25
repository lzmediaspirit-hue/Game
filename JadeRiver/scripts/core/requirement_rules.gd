class_name RequirementRules
extends RefCounted
## Part 2 · The one Requirement format used by breakthroughs, unlocks, portals,
## objects, items, recipes, quests, idle tasks and buildings.
## requirement = {"all": [condition...]} or {"any": [...]}; each condition may add
## cause, hard (default true) and fix. `check` returns results the UI shows directly.
## ctx = {char: GameCharacter, account: AccountState, room: Dictionary}

static func check(req, ctx: Dictionary) -> Array:
	var results: Array = []
	if not (req is Dictionary) or req.is_empty(): return results
	var any_mode: bool = req.has("any")
	var conds: Array = req.get("any", req.get("all", []))
	for cond in conds:
		if not (cond is Dictionary): continue
		if cond.has("all") or cond.has("any"):
			var sub := check(cond, ctx)
			var ok := passes_results(sub, cond.has("any"))
			results.append({"ok": ok, "cause": str(cond.get("cause", "")), "hard": bool(cond.get("hard", true)), "text": "", "fix": str(cond.get("fix", ""))})
			continue
		results.append(evaluate(cond, ctx))
	if any_mode:
		var any_ok := false
		for r in results: any_ok = any_ok or r.ok
		for r in results: r["any_group_ok"] = any_ok
	return results

static func passes_results(results: Array, any_mode := false) -> bool:
	if results.is_empty(): return true
	if any_mode:
		for r in results:
			if r.ok: return true
		return false
	for r in results:
		if not r.ok: return false
	return true

## True when every condition holds (soft ones included).
static func passes(req, ctx: Dictionary) -> bool:
	if not (req is Dictionary) or req.is_empty(): return true
	return passes_results(check(req, ctx), req.has("any"))

## True when every HARD condition holds (soft ones only raise risk).
static func hard_ok(req, ctx: Dictionary) -> bool:
	if not (req is Dictionary) or req.is_empty(): return true
	var results := check(req, ctx)
	if req.has("any"): return passes_results(results, true)
	for r in results:
		if r.hard and not r.ok: return false
	return true

static func soft_unmet(results: Array) -> int:
	var n := 0
	for r in results:
		if not r.hard and not r.ok: n += 1
	return n

static func evaluate(cond: Dictionary, ctx: Dictionary) -> Dictionary:
	var c = ctx.get("char")
	var account = ctx.get("account")
	var room: Dictionary = ctx.get("room", {})
	var kind := str(cond.get("kind", ""))
	var ok := false
	var text := ""
	match kind:
		"realm_at_least":
			ok = c != null and ProgressionRules.at_least(c.cultivator.realm_key, str(cond.realm))
			text = Tx.t("req.reach") % ContentDB.name_of("realms", str(cond.realm))
		"realm_below":
			ok = c != null and not ProgressionRules.at_least(c.cultivator.realm_key, str(cond.realm))
			text = Tx.t("req.below") % ContentDB.name_of("realms", str(cond.realm))
		"level_at_least":
			ok = c != null and ProgressionRules.level(c) >= int(cond.level)
			text = Tx.t("req.level") % int(cond.level)
		"attribute_at_least":
			ok = c != null and c.stats.value(str(cond.attribute)) >= float(cond.value)
			text = "%s %d" % [str(cond.attribute).capitalize(), int(cond.value)]
		"body_level_at_least":
			ok = c != null and c.cultivator.body_level >= int(cond.value)
			text = Tx.t("req.body_level_now") % [int(cond.value), c.cultivator.body_level if c else 0]
		"body_tier_at_least":
			# S48 body ladder: Copper, Iron, Jade, Gold Body.
			var need_i := 1
			var tiers := ContentDB.all("body_tiers")
			for i in tiers.size():
				if str(tiers[i].id) == str(cond.tier): need_i = i + 1
			ok = c != null and ProgressionRules.body_tier_index(c.cultivator) >= need_i
			text = Tx.t("req.body_tier") % ContentDB.name_of("body_tiers", str(cond.tier))
		# S49 relations: never on a core realm requirement (data_validation holds that line).
		"alignment_at_least":
			ok = c != null and c.relations.alignment >= int(cond.value)
			text = Tx.t("req.alignment_at_least") % [_alignment_name(int(cond.value)), int(cond.value)]
		"alignment_at_most":
			ok = c != null and c.relations.alignment <= int(cond.value)
			text = Tx.t("req.alignment_at_most") % [_alignment_name(int(cond.value)), int(cond.value)]
		"merit_at_least":
			ok = c != null and c.relations.merit >= int(cond.value)
			text = Tx.t("req.merit_at_least") % int(cond.value)
		"fame_at_least":
			ok = c != null and c.relations.fame >= int(cond.value)
			text = Tx.t("req.fame_at_least") % int(cond.value)
		"soul_at_least":
			ok = c != null and c.pools.max_soul >= float(cond.value)
			text = Tx.t("req.soul_pool") % int(cond.value)
		"dao_tier_at_least":
			var best := 0
			if c != null:
				for d in c.cultivator.daos:
					if str(cond.dao) == "any" or d == str(cond.dao): best = maxi(best, int(c.cultivator.daos[d].get("tier", 0)))
			ok = best >= int(cond.tier)
			text = Tx.t("req.dao_at_tier") % [Tx.t("req.any") if str(cond.dao) == "any" else str(cond.dao).capitalize(), int(cond.tier)]
		"purity_at_least":
			ok = c != null and c.cultivator.energy_type in ["true_qi", "sage_qi", "law_qi", "monarch_qi", "heavenforce"] and c.cultivator.purity <= int(cond.grade)
			text = Tx.t("req.true_qi_purity_grade_or") % int(cond.grade)
		"qi_full":
			ok = c != null and c.pools.max_qi > 0 and c.pools.qi >= c.pools.max_qi - 0.5
			text = Tx.t("req.qi_reserve_full")
		"item_owned":
			var n = c.inventory.count_including_equipped(str(cond.item)) if c else 0
			ok = n >= int(cond.get("count", 1))
			text = Tx.t("req.have") % [ContentDB.item_name(str(cond.item)), int(cond.get("count", 1)), n]
		"quest_done":
			ok = c != null and c.quests.is_done(str(cond.quest))
			text = Tx.t("req.complete") % ContentDB.name_of("quests", str(cond.quest))
		"quest_active":
			ok = c != null and c.quests.is_active(str(cond.quest))
			text = Tx.t("req.on") % ContentDB.name_of("quests", str(cond.quest))
		"quest_accepted":
			ok = c != null and (c.quests.is_active(str(cond.quest)) or c.quests.is_done(str(cond.quest)))
			text = Tx.t("req.accept") % ContentDB.name_of("quests", str(cond.quest))
		"quest_not_done":
			ok = c != null and not c.quests.is_done(str(cond.quest))
			text = Tx.t("req.before") % ContentDB.name_of("quests", str(cond.quest))
		"flag_set":
			ok = c != null and c.quests.has_flag(str(cond.flag))
			text = str(cond.get("text", ContentDB.text("flag." + str(cond.flag))))
		"flag_not_set":
			ok = c != null and not c.quests.has_flag(str(cond.flag))
			text = str(cond.get("text", ""))
		"zone_supports":
			var zone := ContentDB.zone_of_room(str(room.get("id", c.position.room if c else "")))
			var ceiling := str(zone.get("ceiling", "world_genesis"))
			ok = ContentDB.realm_position(ceiling) >= ContentDB.realm_position(str(cond.realm))
			text = Tx.t("req.this_land_cannot_support") % ContentDB.name_of("realms", str(cond.realm)) if not ok else Tx.t("req.the_land_supports") % ContentDB.name_of("realms", str(cond.realm))
		"no_untreated_injury":
			ok = c != null and c.cultivator.injuries.is_empty()
			text = Tx.t("req.no_untreated_injury")
		"stability_at_least":
			var order: Array = ContentDB.curve("stability_order", ["unstable", "settling", "stable", "solid"])
			ok = c != null and order.find(c.cultivator.stability) >= order.find(str(cond.value))
			text = Tx.t("req.stability") % str(cond.value).capitalize()
		"unlock":
			ok = c != null and Unlocks.is_unlocked(c.id, str(cond.system))
			text = str(cond.get("text", Tx.t("req.requires") % str(cond.system).replace("_", " ")))
		"account_realm":
			ok = account != null and ProgressionRules.at_least(account.highest_realm, str(cond.realm))
			text = Tx.t("req.any_character_reaches") % ContentDB.name_of("realms", str(cond.realm))
		"sect_level":
			var need_lv := int(cond.get("value", cond.get("level", 1)))
			ok = account != null and int(account.sect.get("level", 0)) >= need_lv
			text = Tx.t("req.your_sect_reaches_level") % need_lv
		"sect_building_at_least":
			var bl := int(account.sect.get("buildings", {}).get(str(cond.building), 0)) if account != null else 0
			ok = bl >= int(cond.get("value", 1))
			text = Tx.t("req.level_2") % [ContentDB.name_of("sect_buildings", str(cond.building)), int(cond.get("value", 1))]
		"sect_founded":
			ok = account != null and not account.sect.is_empty()
			text = Tx.t("req.found_your_sect")
		"profession_rank":
			var ranks: Array = ContentDB.curve("profession_ranks", [])
			var have := str(c.professions.get(str(cond.craft), {}).get("rank", "")) if c else ""
			var hi := -1
			var need := -1
			for i in ranks.size():
				if ranks[i][0] == have: hi = i
				if ranks[i][0] == str(cond.rank): need = i
			ok = hi >= need and need >= 0 and have != ""
			text = "%s %s" % [str(cond.craft).capitalize(), str(cond.rank).capitalize()]
		"attunement_at_least":
			ok = c != null and float(c.cultivator.attunement.get(str(cond.zone), 0)) >= float(cond.value)
			text = Tx.t("req.attunement") % int(cond.value)
		"technique_tier_at_least":
			var best_t := 0
			if c != null:
				for t in c.cultivator.mastery:
					if str(cond.technique) == "any" or t == str(cond.technique): best_t = maxi(best_t, int(c.cultivator.mastery[t].get("tier", 0)))
			ok = best_t >= int(cond.tier)
			text = Tx.t("req.a_technique_at_mastery_tier") % [int(cond.tier), best_t]
		"presence_level_at_least", "law_affinity_at_least", "powers_refined_at_least":
			ok = false
			text = Tx.t("req.beyond_the_valley") % kind.replace("_", " ")
		"event_passed":
			ok = c != null and str(cond.event) in c.cultivator.events_passed
			text = Tx.t("req.pass") % ContentDB.text("event." + str(cond.event))
		"secret_art":
			# A secret art learned (Breath Control opens flooded ways, S09).
			ok = c != null and str(cond.art) in c.cultivator.secret_arts
			text = str(cond.get("text", Tx.t("req.learn_the_secret_art") % ContentDB.name_of("secret_arts", str(cond.art))))
		"method_learned":
			ok = c != null and c.cultivator.method_id != ""
			text = str(cond.get("text", Tx.t("req.learn_a_cultivation_method")))
		"method_supports":
			ok = c != null and method_supports_next(c)
			text = Tx.t("req.your_method_cannot_carry_you") if not ok else Tx.t("req.method_supports_the_next_realm")
		"room_safe":
			ok = bool(room.get("safe", false))
			text = Tx.t("req.a_safe_location")
		"room_type":
			ok = str(room.get("type", "")) == str(cond.value)
			text = Tx.t("req.in_a") % str(cond.value)
		"in_room":
			ok = str(room.get("id", "")) == str(cond.room)
			text = Tx.t("req.at") % ContentDB.name_of("rooms", str(cond.room))
		"currency_at_least":
			ok = account != null and int(account.currencies.get(str(cond.currency), 0)) >= int(cond.amount)
			text = "%d %s" % [int(cond.amount), ContentDB.text("currency." + str(cond.currency))]
		"training_sect":
			ok = c != null and str(c.training_sect.get("id", "")) == str(cond.sect)
			text = Tx.t("req.member_of_the") % ContentDB.name_of("sects", str(cond.sect))
		"has_training_sect":
			ok = (c != null and str(c.training_sect.get("id", "")) != "") == bool(cond.get("value", true))
			text = Tx.t("req.join_a_training_sect") if bool(cond.get("value", true)) else Tx.t("req.not_yet_in_a_training")
		"companion_owned":
			ok = c != null and (c.companions.get("roster", []) as Array).has(str(cond.companion)) == bool(cond.get("value", true))
			text = (Tx.t("req.travels_with_you") if bool(cond.get("value", true)) else Tx.t("req.has_not_joined_you")) % ContentDB.name_of("companions", str(cond.companion))
		"sect_rank_at_least":
			var ranks2: Array = ContentDB.config("sect_ranks").get("order", [])
			ok = c != null and ranks2.find(str(c.training_sect.get("rank", ""))) >= ranks2.find(str(cond.rank))
			text = Tx.t("req.sect_rank") % str(cond.rank).replace("_", " ").capitalize()
		"time_of_day":
			ok = Clock.time_of_day() in cond.get("phases", [])
			text = Tx.t("req.only_at") % ", ".join(cond.get("phases", []))
		"slots_unlocked_at_least":
			ok = account != null and account.slots_unlocked >= int(cond.value)
			text = Tx.t("req.character_slots") % int(cond.value)
		"skip_prologue":
			ok = c != null and c.skip_prologue
			text = Tx.t("req.skipped_the_prologue")
		"never":
			ok = false
			text = str(cond.get("text", Tx.t("req.coming_soon")))
		_:
			ok = false
			text = Tx.t("req.unknown_requirement") + kind
	if cond.has("text") and kind not in ["flag_set", "flag_not_set", "unlock", "never", "method_learned"]: text = str(cond.text)
	return {"ok": ok, "cause": str(cond.get("cause", "")), "hard": bool(cond.get("hard", true)), "text": text, "fix": str(cond.get("fix", "")), "kind": kind}

## The alignment word a value falls in (Demonic ... Righteous), for requirement text.
static func _alignment_name(v: int) -> String:
	for w in ContentDB.config("karma").get("alignment_words", []):
		if v <= int(w.get("max", 100)): return str(w.get("name", w.id))
	return ""

## A method's ceiling makes the next major breakthrough a material bottleneck (S08).
static func method_supports_next(c) -> bool:
	var m := ProgressionRules.method(c.cultivator.method_id)
	if m.is_empty(): return false
	var spec := ProgressionRules.breakthrough_spec(c.cultivator.realm_key)
	var target := str(spec.get("to", ContentDB.next_realm(c.cultivator.realm_key)))
	return ContentDB.realm_position(str(m.get("ceiling", "mortal"))) >= ContentDB.realm_position(target)

static func first_failure_text(req, ctx: Dictionary) -> String:
	for r in check(req, ctx):
		if not r.ok and r.hard: return r.text
	for r in check(req, ctx):
		if not r.ok: return r.text
	return ""
