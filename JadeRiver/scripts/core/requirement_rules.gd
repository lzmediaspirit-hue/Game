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
			text = "Reach %s" % ContentDB.name_of("realms", str(cond.realm))
		"realm_below":
			ok = c != null and not ProgressionRules.at_least(c.cultivator.realm_key, str(cond.realm))
			text = "Below %s" % ContentDB.name_of("realms", str(cond.realm))
		"level_at_least":
			ok = c != null and ProgressionRules.level(c) >= int(cond.level)
			text = "Level %d" % int(cond.level)
		"attribute_at_least":
			ok = c != null and c.stats.value(str(cond.attribute)) >= float(cond.value)
			text = "%s %d" % [str(cond.attribute).capitalize(), int(cond.value)]
		"body_level_at_least":
			ok = c != null and c.cultivator.body_level >= int(cond.value)
			text = "Body level %d (now %d)" % [int(cond.value), c.cultivator.body_level if c else 0]
		"soul_at_least":
			ok = c != null and c.pools.max_soul >= float(cond.value)
			text = "Soul pool %d" % int(cond.value)
		"dao_tier_at_least":
			var best := 0
			if c != null:
				for d in c.cultivator.daos:
					if str(cond.dao) == "any" or d == str(cond.dao): best = maxi(best, int(c.cultivator.daos[d].get("tier", 0)))
			ok = best >= int(cond.tier)
			text = "%s Dao at tier %d" % ["Any" if str(cond.dao) == "any" else str(cond.dao).capitalize(), int(cond.tier)]
		"purity_at_least":
			ok = c != null and c.cultivator.energy_type in ["true_qi", "sage_qi", "law_qi", "monarch_qi", "heavenforce"] and c.cultivator.purity <= int(cond.grade)
			text = "True Qi purity grade %d or better" % int(cond.grade)
		"qi_full":
			ok = c != null and c.pools.max_qi > 0 and c.pools.qi >= c.pools.max_qi - 0.5
			text = "QI reserve full"
		"item_owned":
			var n = c.inventory.count_including_equipped(str(cond.item)) if c else 0
			ok = n >= int(cond.get("count", 1))
			text = "%s ×%d (have %d)" % [ContentDB.item_name(str(cond.item)), int(cond.get("count", 1)), n]
		"quest_done":
			ok = c != null and c.quests.is_done(str(cond.quest))
			text = "Complete \"%s\"" % ContentDB.name_of("quests", str(cond.quest))
		"quest_active":
			ok = c != null and c.quests.is_active(str(cond.quest))
			text = "On \"%s\"" % ContentDB.name_of("quests", str(cond.quest))
		"quest_accepted":
			ok = c != null and (c.quests.is_active(str(cond.quest)) or c.quests.is_done(str(cond.quest)))
			text = "Accept \"%s\"" % ContentDB.name_of("quests", str(cond.quest))
		"quest_not_done":
			ok = c != null and not c.quests.is_done(str(cond.quest))
			text = "Before \"%s\"" % ContentDB.name_of("quests", str(cond.quest))
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
			text = "This land cannot support %s" % ContentDB.name_of("realms", str(cond.realm)) if not ok else "The land supports %s" % ContentDB.name_of("realms", str(cond.realm))
		"no_untreated_injury":
			ok = c != null and c.cultivator.injuries.is_empty()
			text = "No untreated injury"
		"stability_at_least":
			var order: Array = ContentDB.curve("stability_order", ["unstable", "settling", "stable", "solid"])
			ok = c != null and order.find(c.cultivator.stability) >= order.find(str(cond.value))
			text = "Stability %s" % str(cond.value).capitalize()
		"unlock":
			ok = c != null and Unlocks.is_unlocked(c.id, str(cond.system))
			text = str(cond.get("text", "Requires %s" % str(cond.system).replace("_", " ")))
		"account_realm":
			ok = account != null and ProgressionRules.at_least(account.highest_realm, str(cond.realm))
			text = "Any character reaches %s" % ContentDB.name_of("realms", str(cond.realm))
		"sect_level":
			var need_lv := int(cond.get("value", cond.get("level", 1)))
			ok = account != null and int(account.sect.get("level", 0)) >= need_lv
			text = "Your sect reaches level %d" % need_lv
		"sect_founded":
			ok = account != null and not account.sect.is_empty()
			text = "Found your sect"
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
			text = "Attunement %d" % int(cond.value)
		"technique_tier_at_least":
			var best_t := 0
			if c != null:
				for t in c.cultivator.mastery:
					if str(cond.technique) == "any" or t == str(cond.technique): best_t = maxi(best_t, int(c.cultivator.mastery[t].get("tier", 0)))
			ok = best_t >= int(cond.tier)
			text = "A technique at mastery tier %d (best %d)" % [int(cond.tier), best_t]
		"presence_level_at_least", "law_affinity_at_least", "powers_refined_at_least":
			ok = false
			text = "Beyond the valley (%s)" % kind.replace("_", " ")
		"event_passed":
			ok = c != null and str(cond.event) in c.cultivator.events_passed
			text = "Pass %s" % ContentDB.text("event." + str(cond.event))
		"method_learned":
			ok = c != null and c.cultivator.method_id != ""
			text = str(cond.get("text", "Learn a cultivation method"))
		"method_supports":
			ok = c != null and method_supports_next(c)
			text = "Your method cannot carry you further" if not ok else "Method supports the next realm"
		"room_safe":
			ok = bool(room.get("safe", false))
			text = "A safe location"
		"room_type":
			ok = str(room.get("type", "")) == str(cond.value)
			text = "In a %s" % str(cond.value)
		"in_room":
			ok = str(room.get("id", "")) == str(cond.room)
			text = "At %s" % ContentDB.name_of("rooms", str(cond.room))
		"currency_at_least":
			ok = account != null and int(account.currencies.get(str(cond.currency), 0)) >= int(cond.amount)
			text = "%d %s" % [int(cond.amount), ContentDB.text("currency." + str(cond.currency))]
		"training_sect":
			ok = c != null and str(c.training_sect.get("id", "")) == str(cond.sect)
			text = "Member of the %s" % ContentDB.name_of("sects", str(cond.sect))
		"has_training_sect":
			ok = (c != null and str(c.training_sect.get("id", "")) != "") == bool(cond.get("value", true))
			text = "Join a training sect" if bool(cond.get("value", true)) else "Not yet in a training sect"
		"companion_owned":
			ok = c != null and (c.companions.get("roster", []) as Array).has(str(cond.companion)) == bool(cond.get("value", true))
			text = ("%s travels with you" if bool(cond.get("value", true)) else "%s has not joined you") % ContentDB.name_of("companions", str(cond.companion))
		"sect_rank_at_least":
			var ranks2: Array = ContentDB.config("sect_ranks").get("order", [])
			ok = c != null and ranks2.find(str(c.training_sect.get("rank", ""))) >= ranks2.find(str(cond.rank))
			text = "Sect rank %s" % str(cond.rank).replace("_", " ").capitalize()
		"time_of_day":
			ok = Clock.time_of_day() in cond.get("phases", [])
			text = "Only at %s" % ", ".join(cond.get("phases", []))
		"slots_unlocked_at_least":
			ok = account != null and account.slots_unlocked >= int(cond.value)
			text = "%d character slots" % int(cond.value)
		"skip_prologue":
			ok = c != null and c.skip_prologue
			text = "Skipped the Prologue"
		"never":
			ok = false
			text = str(cond.get("text", "Coming soon"))
		_:
			ok = false
			text = "Unknown requirement: " + kind
	if cond.has("text") and kind not in ["flag_set", "flag_not_set", "unlock", "never", "method_learned"]: text = str(cond.text)
	return {"ok": ok, "cause": str(cond.get("cause", "")), "hard": bool(cond.get("hard", true)), "text": text, "fix": str(cond.get("fix", "")), "kind": kind}

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
