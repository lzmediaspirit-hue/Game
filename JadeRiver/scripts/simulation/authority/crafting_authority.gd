class_name CraftingAuthority
extends Authority
## S15/S16/S33 · Recipes known, profession ranks, gathering and mining nodes,
## fishing, cooking, alchemy (five-screen mini-game scores), the forge and the
## auto-refine queue. One crafting framework: validate inputs, consume, roll quality
## with the `crafting` stream, grant output and profession XP, emit craft_completed.

var pending: Dictionary = {}   # actor -> {object, kind, started, channel}
var steps: Dictionary = {}     # actor -> {recipe, craft, scores}: the mini-game in progress

const NODE_CRAFT := {"herb_patch": "herb_gathering", "ore_vein": "mining", "fishing_spot": "fishing", "star_sight": "star_charting"}
const RANK_CAPS := {
	"herb_gathering": [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"], ["sage_sovereign_1", "grandmaster"]],
	"mining": [["qi_unfurling_1", "adept"], ["spirit_awakening_1", "expert"], ["sage_sovereign_1", "master"]],
	"cooking": [["qi_kindling_1", "adept"], ["heart_tempering_1", "expert"], ["heaven_glimpse_1", "master"]],
	"fishing": [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"]],
	"alchemy": [["qi_unfurling_1", "adept"], ["cloud_stride_1", "expert"], ["heaven_glimpse_1", "master"]],
	"smithing": [["qi_unfurling_1", "adept"], ["cloud_stride_1", "expert"], ["heaven_glimpse_1", "master"]],
	# S16: the Starsea crafts open at Sage 3 and rise with the Sovereign stages.
	"star_charting": [["sage_3", "adept"], ["sage_sovereign_1", "expert"], ["sage_sovereign_3", "master"]],
	"shipwright": [["sage_3", "adept"], ["sage_sovereign_1", "expert"], ["sage_sovereign_3", "master"]],
	# S47: Old Scribe Bai's brush, from Qi Kindling 6.
	"talisman": [["qi_kindling_6", "adept"], ["heart_tempering_1", "expert"], ["cloud_stride_1", "master"]],
}
## Stations and the verb each craft uses; the Starsea crafts take no mini-game.
const STATIONS := {"cooking": ["cooking_pot"], "alchemy": ["alchemy_furnace", "earth_vent"], "smithing": ["forge_anvil"],
	"star_charting": ["chart_table"], "shipwright": ["shipyard_slip"]}
const GRADE_CAP := [["qi_kindling_1", "common"], ["qi_unfurling_1", "earth"], ["cloud_stride_1", "heaven"], ["heaven_glimpse_1", "mystic"], ["sage_1", "spirit"],
	["sage_sovereign_1", "sage"]]

func intents() -> Array:
	return ["complete_node", "catch_fish", "cook", "craft_step", "refine", "queue_auto_refine", "collect_auto_refine", "forge", "enhance", "salvage_item",
		"salvage", "inherit_enhancement", "reroll_affixes", "choose_affixes", "lock_affix", "chart_route", "build_vessel", "absorb_flame",
		"trace_talisman", "restore_relic", "mend_furnace", "deduce_recipe", "start_experiment", "take_guild_exam", "accept_commission",
		"deliver_commission", "tribulation_shield", "catch_pill_soul"]

func subscribe() -> void:
	# S44 guild exams count what comes out of the furnace while the candle burns.
	GameEvents.subscribe("craft_completed", _on_craft_completed, 40)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"complete_node": return complete_node(c, str(intent.get("object", "")), float(intent.get("timing", -1.0)))
		"catch_fish": return catch_fish(c, str(intent.get("object", "")), intent.get("result", {}))
		"cook": return craft(c, str(intent.get("recipe", "")), maxi(1, int(intent.get("count", 1))), [], "cooking")
		"craft_step": return craft_step(c, str(intent.get("recipe", "")), str(intent.get("craft", "alchemy")), float(intent.get("offset", 1.0)),
			str(intent.get("fire", "charcoal")))
		"refine": return craft(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10), _take_steps(c, str(intent.get("recipe", ""))), "alchemy",
			str(intent.get("fire", "charcoal")), intent.get("substitute", {}) if intent.get("substitute", {}) is Dictionary else {}, bool(intent.get("live", false)))
		"tribulation_shield": return tribulation_shield(c, int(intent.get("bolt", -1)), float(intent.get("timing", 99.0)))
		"catch_pill_soul": return catch_pill_soul(c, float(intent.get("timing", 99.0)))
		"forge": return craft(c, str(intent.get("recipe", "")), 1, _take_steps(c, str(intent.get("recipe", ""))), "smithing")
		"queue_auto_refine": return queue_auto(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10))
		"absorb_flame": return absorb_flame(c, int(intent.get("index", -1)))
		"collect_auto_refine": return collect_auto(c)
		"enhance": return enhance(c, intent)
		"salvage_item": return salvage(c, [_uid_at(c, int(intent.get("index", -1)))])
		"salvage": return salvage(c, intent.get("items", []))
		"inherit_enhancement": return inherit(c, int(intent.get("from", -1)), int(intent.get("to", -1)))
		"reroll_affixes": return reroll(c, int(intent.get("uid", -1)))
		"choose_affixes": return choose_affixes(c, int(intent.get("uid", -1)), str(intent.get("keep", "new")) == "new")
		"lock_affix": return lock_affix(c, int(intent.get("uid", -1)), int(intent.get("affix", -1)))
		"trace_talisman": return trace_talisman(c, str(intent.get("recipe", "")), float(intent.get("score", 0.0)), bool(intent.get("broken", false)))
		"restore_relic": return restore_relic(c, int(intent.get("index", -1)))
		"mend_furnace": return mend_furnace(c, int(intent.get("uid", -1)))
		"deduce_recipe": return deduce(c, str(intent.get("recipe", "")))
		"start_experiment": return experiment(c, intent.get("herbs", []) if intent.get("herbs", []) is Array else [])
		"take_guild_exam": return take_exam(c, str(intent.get("craft", "alchemy")), str(intent.get("rank", "")))
		"accept_commission": return accept_commission(c, str(intent.get("id", "")))
		"deliver_commission": return deliver_commission(c, str(intent.get("id", "")), str(intent.get("pay", "taels")))
		"chart_route": return craft(c, str(intent.get("recipe", "")), 1, [], "star_charting")
		"build_vessel": return craft(c, str(intent.get("recipe", "")), 1, [], "shipwright")
	return fail("unknown_intent")

# ------------------------------------------------------------------ professions
func rank_of(c, craft: String) -> String:
	return str(c.professions.get(craft, {}).get("rank", "apprentice"))

func rank_index(rank: String) -> int:
	var ranks: Array = ContentDB.curve("profession_ranks", [])
	for i in ranks.size():
		if ranks[i][0] == rank: return i
	return 0

func rank_cap(c, craft: String) -> int:
	var cap := 0
	for row in RANK_CAPS.get(craft, [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"]]):
		if ProgressionRules.at_least(c.cultivator.realm_key, str(row[0])): cap = rank_index(str(row[1]))
	return cap

func add_xp(c, craft: String, xp: float) -> void:
	var p: Dictionary = c.professions.get(craft, {"rank": "apprentice", "xp": 0.0})
	p.xp = float(p.xp) + xp
	var ranks: Array = ContentDB.curve("profession_ranks", [])
	var idx := rank_index(str(p.rank))
	var cap := rank_cap(c, craft)
	while idx + 1 < ranks.size() and idx + 1 <= cap and float(p.xp) >= float(ranks[idx + 1][1]):
		idx += 1
		p.rank = ranks[idx][0]
		emit("profession_rank_up", {"actor": c.id, "craft": craft, "rank": p.rank})
	c.professions[craft] = p

func grade_cap(c) -> String:
	var g := "plain"
	for row in GRADE_CAP:
		if ProgressionRules.at_least(c.cultivator.realm_key, str(row[0])): g = str(row[1])
	return g

func tool_power(c, craft: String) -> float:
	var best := 0.0
	for s in c.inventory.bag:
		if s == null: continue
		var t: Dictionary = ContentDB.item(str(s.id)).get("tool", {})
		if str(t.get("craft", "")) == craft: best = maxf(best, float(t.get("power", 1.0)))
	for k in c.inventory.key_items:
		var t2: Dictionary = ContentDB.item(str(k.id)).get("tool", {})
		if str(t2.get("craft", "")) == craft: best = maxf(best, float(t2.get("power", 1.0)))
	return best

# ------------------------------------------------------------------ gathering, mining, fishing
func gather(c, o: Dictionary) -> Dictionary:
	var craft: String = NODE_CRAFT.get(str(o.type), "")
	if not Unlocks.is_unlocked(c.id, craft): return fail("locked", {"text": Unlocks.locked_text(craft)})
	if craft in ["mining", "fishing"] and tool_power(c, craft) <= 0.0: return fail("no_tool", {"text": Tx.t("sim.crafting.you_need_a") % {"mining": "pickaxe", "fishing": Tx.t("sim.crafting.fishing_rod")}[craft]})
	var need_rank := str(o.get("rank", "apprentice"))
	if rank_index(rank_of(c, craft)) < rank_index(need_rank): return fail("rank", {"text": Tx.t("sim.crafting.needs") % [craft.replace("_", " ").capitalize(), need_rank.capitalize()]})
	# S45: a ripe rare herb may have a keeper.
	var guard: String = game.world.herb_guard_text(c, o) if o.type == "herb_patch" else ""
	if guard != "": return fail("guarded", {"text": guard})
	var channel = {"herb_patch": 1.5, "ore_vein": 2.4, "fishing_spot": 0.0, "star_sight": 3.0}[str(o.type)]
	pending[c.id] = {"object": str(o.id), "kind": str(o.type), "started": game.sim_time, "channel": channel}
	emit("node_action_started", {"actor": c.id, "object": o.id, "kind": o.type, "channel": channel})
	var out := {"channel": channel, "minigame": "fishing" if o.type == "fishing_spot" else "",
		"action": {"herb_patch": "gather", "ore_vein": "mine", "fishing_spot": "fish", "star_sight": "gather"}[str(o.type)]}
	# S45 harvest tap: the hold ends in a shrinking ring; the window widens with gathering rank.
	if o.type == "herb_patch":
		var h: Dictionary = ContentDB.config("garden").get("harvest", {})
		out.tap = {"ring_s": float(h.get("ring_s", 1.0)), "target": float(h.get("target", 0.7)), "window": HerbRules.tap_window(rank_of(c, craft))}
		if o.has("ripen"): out.early = not bool(HerbRules.ripen_state(o, Clock.now_utc()).ripe)
	return ok(out)

## `timing` (S45 herbs): how far the harvest ring had shrunk when the tap landed, 0..1 (-1: no tap, a miss).
func complete_node(c, object_id: String, timing := -1.0) -> Dictionary:
	var p: Dictionary = pending.get(c.id, {})
	if p.is_empty() or str(p.object) != object_id: return fail("not_started")
	if game.sim_time - float(p.started) < float(p.channel) - 0.15: return fail("too_early")
	pending.erase(c.id)
	var rt: RoomRuntime = game.room_rt
	var o := rt.object_def(object_id)
	var st: Dictionary = rt.objects.get(object_id, {"state": "ready"})
	if st.get("state", "ready") != "ready": return fail("depleted")
	var craft: String = NODE_CRAFT[str(o.type)]
	if craft == "herb_gathering": return _harvest(c, o, timing)
	var rng := Rng.stream(c.id, "crafting")
	var y: Array = o.get("yield", [1, 2])
	var power := 1.0 if craft == "star_charting" else maxf(1.0, tool_power(c, "gathering" if craft == "herb_gathering" else "mining"))
	var count := rng.randi_range(int(y[0]), int(y[1]))
	if rng.randf() < (power - 1.0) * 0.5: count += 1
	if craft != "star_charting" and game.pets.gatherer_active(c.id) and rng.randf() < 0.25: count += 1
	var herb_bonus: float = game.pets.trait_bonus(c, "herb_yield") if craft == "herb_gathering" else 0.0
	if herb_bonus > 0.0 and rng.randf() < herb_bonus * count: count += 1
	var item := str(o.get("item", ""))
	game.inventory.apply_add(c.id, item, count, craft)
	game.world.apply_node_depleted(c, object_id, float(o.get("regrow_s", 300)))
	add_xp(c, craft, float(ContentDB.curve("profession_xp.%s" % {"mining": "mine", "star_charting": "observe"}.get(craft, "gather"), 5)))
	emit("node_gathered", {"actor": c.id, "object": object_id, "item": item, "count": count, "craft": craft})
	return ok({"item": item, "count": count})

## S45 harvest: a perfect tap keeps the herb's full age and may find a seed; a miss drops one age tier, and so does
## picking a rare herb before it ripens (never below ten years). A rare node grows back with its next ripening.
func _harvest(c, o: Dictionary, timing: float) -> Dictionary:
	var guard: String = game.world.herb_guard_text(c, o)
	if guard != "": return fail("guarded", {"text": guard})
	var rng := Rng.stream(c.id, "crafting")
	var object_id := str(o.id)
	var now := Clock.now_utc()
	var early: bool = o.has("ripen") and not bool(HerbRules.ripen_state(o, now).ripe)
	var perfect := HerbRules.tap_perfect(timing, rank_of(c, "herb_gathering"))
	var item := HerbRules.aged_down(str(o.get("item", "")), (1 if early else 0) + (0 if perfect else 1))
	var y: Array = o.get("yield", [1, 2])
	var power := maxf(1.0, tool_power(c, "gathering"))
	var count := rng.randi_range(int(y[0]), int(y[1]))
	if rng.randf() < (power - 1.0) * 0.5: count += 1
	if game.pets.gatherer_active(c.id) and rng.randf() < 0.25: count += 1
	var herb_bonus: float = game.pets.trait_bonus(c, "herb_yield")
	if herb_bonus > 0.0 and rng.randf() < herb_bonus * count: count += 1
	game.inventory.apply_add(c.id, item, count, "herb_gathering")
	var seed := ""
	if perfect:
		var seed_id := HerbRules.harvest_seed(item)
		var chance := float(o.get("seed_chance", ContentDB.config("garden").get("seed_chance", 0.1)))
		if seed_id != "" and Rng.stream(c.id, "crafting").randf() < chance:
			seed = seed_id
			game.inventory.apply_add(c.id, seed, 1, "herb_gathering")
	var regrow := float(o.get("regrow_s", 300))
	if o.has("ripen"): regrow = maxf(60.0, HerbRules.regrow_at(o, now) - now)
	game.world.apply_node_depleted(c, object_id, regrow)
	add_xp(c, "herb_gathering", float(ContentDB.curve("profession_xp.gather", 5)) * (1.5 if perfect else 1.0))
	emit("node_gathered", {"actor": c.id, "object": object_id, "item": item, "count": count, "craft": "herb_gathering"})
	emit("herb_harvested", {"actor": c.id, "object": object_id, "item": item, "age": HerbRules.item_age(item), "perfect": perfect, "early": early})
	if seed != "": emit("seed_found", {"actor": c.id, "seed": seed, "object": object_id})
	return ok({"item": item, "count": count, "perfect": perfect, "early": early, "age": HerbRules.item_age(item), "seed": seed})

## Fishing result from the mini-game (S33). The authority rolls the catch.
func catch_fish(c, object_id: String, result: Dictionary) -> Dictionary:
	var p: Dictionary = pending.get(c.id, {})
	if p.is_empty() or str(p.object) != object_id: return fail("not_started")
	pending.erase(c.id)
	var reaction := float(result.get("reaction_s", 9.9))
	var tension_ok := bool(result.get("tension_ok", false))
	var window: float = (0.6 + 0.1 * (tool_power(c, "fishing") - 1.0)) * (1.0 + game.pets.trait_bonus(c, "fish_chance"))
	if reaction > window or reaction < 0.05 or not tension_ok:
		emit("fish_escaped", {"actor": c.id})
		return ok({"caught": false})
	var o = game.room_rt.object_def(object_id)
	var tod := Clock.time_of_day()
	var table: Array = []
	for f in ContentDB.all("fish"):
		if not (str(o.get("spot", "")) in f.get("spots", [])) and not ("any" in f.get("spots", [])): continue
		if f.has("time") and not (tod in f.time): continue
		table.append(f)
	if table.is_empty(): return ok({"caught": false})
	var rng := Rng.stream(c.id, "fishing")
	var fish := Rng.weighted(rng, table)
	game.inventory.apply_add(c.id, str(fish.item), 1, "fishing")
	add_xp(c, "fishing", float(ContentDB.curve("profession_xp.fish", 8)))
	emit("fish_caught", {"actor": c.id, "fish": fish.item, "item": fish.item, "room": game.room_rt.room_id})
	return ok({"caught": true, "item": fish.item})

# ------------------------------------------------------------------ recipes
func apply_learn_recipe(actor_id: String, recipe: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("recipes", recipe): return
	if not c.crafting.recipes.has(recipe):
		c.crafting.recipes.append(recipe)
		game.account.recipes_seen[recipe] = true
		emit("recipe_learned", {"actor": actor_id, "recipe": recipe})

func knows(c, recipe: String) -> bool:
	var r := ContentDB.entry("recipes", recipe)
	return c.crafting.recipes.has(recipe) or r.get("default", false)

func station_near(c, types: Array) -> bool:
	var st: ActorState = game.actor_state(c.id)
	if game.room_rt == null: return false
	for o in game.room_rt.def.get("objects", []):
		if o.type in types:
			if st == null: return true
			var at: Array = o.get("at", [0, 0])
			if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) < 180.0: return true
	return false

func recipe_check(c, recipe_id: String, count: int, craft: String, inputs: Array = []) -> String:
	var r := ContentDB.entry("recipes", recipe_id)
	if r.is_empty() or str(r.craft) != craft: return Tx.t("sim.crafting.unknown_recipe")
	if not Unlocks.is_unlocked(c.id, craft): return Unlocks.locked_text(craft)
	if not knows(c, recipe_id): return Tx.t("sim.crafting.you_have_not_learned_this")
	var station: Array = STATIONS.get(craft, [])
	if not station.is_empty() and not station_near(c, station):
		return Tx.t("sim.crafting.you_need_a") % [Tx.t("sim.crafting.cooking_pot"), "furnace", "forge", Tx.t("sim.crafting.chart_table"),
			Tx.t("sim.crafting.slipway")][["cooking", "alchemy", "smithing", "star_charting", "shipwright"].find(craft)]
	# A vessel needs a smith's hand and a formation master's plates (S16).
	var ranks: Dictionary = r.get("requires_ranks", {})
	for rc in ranks:
		if rank_index(rank_of(c, str(rc))) < rank_index(str(ranks[rc])):
			return Tx.t("sim.crafting.needs") % [str(rc).replace("_", " ").capitalize(), str(ranks[rc]).capitalize()]
	if r.has("rank") and rank_index(rank_of(c, craft)) < rank_index(str(r.rank)):
		return Tx.t("sim.crafting.needs") % [craft.replace("_", " ").capitalize(), str(r.rank).capitalize()]
	if str(r.get("fire", "")) != "" and not str(r.fire) in fires_available(c): return Tx.t("sim.crafting.needs_fire") % Tx.t("ui.crafts.fire_" + str(r.fire))
	var grade := str(r.get("grade", "plain"))
	if craft in ["alchemy", "smithing"] and StatRules.grade_index(grade) > StatRules.grade_index(grade_cap(c)): return Tx.t("sim.crafting.your_realm_cannot_refine_grade") % grade.capitalize()
	for inp in with_aged(c, inputs if not inputs.is_empty() else r.get("inputs", []), count).inputs:
		if c.inventory.count(str(inp.item)) < int(inp.count): return Tx.t("sim.crafting.missing") % ContentDB.item_name(str(inp.item))
	return ""

## S45: when the herb a recipe calls for runs short, an older herb of its family stands in (a thousand-year root is
## never spent while ten-year roots are to hand). Returns {inputs: [{item, count}] as totals for the batch, tiers:
## the age tiers the oldest stand-in adds}. A shortfall nothing covers stays on the recipe's own herb.
func with_aged(c, inputs: Array, count: int) -> Dictionary:
	var out: Array = []
	var planned: Dictionary = {}
	var tiers := 0
	var free := func(id: String) -> int: return maxi(0, c.inventory.count(id) - int(planned.get(id, 0)))
	for inp in inputs:
		var id := str(inp.item)
		var need := int(inp.count) * count
		var rows: Array = []
		var own: int = mini(need, free.call(id))
		if own > 0: rows.append({"item": id, "count": own})
		var left := need - own
		var gap := 0
		for older in HerbRules.older_than(id):
			if left <= 0: break
			var more: int = mini(left, free.call(str(older)))
			if more <= 0: continue
			rows.append({"item": str(older), "count": more})
			gap = maxi(gap, HerbRules.tier_gap(id, str(older)))
			left -= more
		if left > 0:
			# Short even with stand-ins: ask for the whole amount of the recipe's own herb, so the check names it.
			out.append({"item": id, "count": need + int(planned.get(id, 0))})
			continue
		for row in rows:
			out.append(row)
			planned[row.item] = int(planned.get(row.item, 0)) + int(row.count)
		tiers = maxi(tiers, gap)
	return {"inputs": out, "tiers": tiers}

## One strike of the alchemy or forge mini-game: `offset` is how far from the band centre
## it landed (0 = dead centre). Scored here, so the craft uses only what Crafting measured.
func craft_step(c, recipe_id: String, craft_kind: String, offset: float, fire := "charcoal") -> Dictionary:
	if not craft_kind in ["alchemy", "smithing"] or not ContentDB.has_entry("recipes", recipe_id): return fail("bad_step")
	_settle_tribulation(c)
	var k: Dictionary = ContentDB.curve("craft_step", {})
	var session: Dictionary = steps.get(c.id, {})
	if str(session.get("recipe", "")) != recipe_id or (session.get("scores", []) as Array).size() >= steps_for(recipe_id):
		session = {"recipe": recipe_id, "craft": craft_kind, "scores": [], "fire": fire if craft_kind == "alchemy" and fire in fires_available(c) else "charcoal"}
	var tolerance := float(k.get("tolerance", 0.3)) * (band_mult(c, str(session.get("fire", "charcoal"))) if craft_kind == "alchemy" else 1.0)
	var score := clampf(1.0 - absf(offset) / tolerance, 0.0, 1.0)
	session.scores.append(score)
	steps[c.id] = session
	var grade := "perfect" if score >= float(k.get("perfect", 0.85)) else ("good" if score >= float(k.get("good", 0.5)) else "miss")
	emit("craft_step_result", {"actor": c.id, "recipe": recipe_id, "step": session.scores.size(), "score": score, "grade": grade})
	return ok({"score": score, "grade": grade, "step": session.scores.size()})

## How many strikes a recipe takes: a liquid has no Condensation (S44), so two.
func steps_for(recipe_id: String) -> int:
	var n := int(ContentDB.curve("craft_step", {}).get("steps", 3))
	return n - 1 if ContentDB.entry("recipes", recipe_id).get("liquid", false) else n

func _take_steps(c, recipe_id: String) -> Array:
	var session: Dictionary = steps.get(c.id, {})
	steps.erase(c.id)
	return session.get("scores", []) if str(session.get("recipe", "")) == recipe_id else []

func craft(c, recipe_id: String, count: int, scores: Array, craft_kind: String, fire := "charcoal", substitute: Dictionary = {}, live := false) -> Dictionary:
	_settle_tribulation(c)
	var furnace := furnace_of(c) if craft_kind == "alchemy" else {}
	# S44: an Alchemy Dao tier-5 substitute swaps one herb for another of the same nature and role.
	var inputs: Array = ContentDB.entry("recipes", recipe_id).get("inputs", [])
	if craft_kind == "alchemy" and not substitute.is_empty():
		var sw := substitute_check(c, recipe_id, str(substitute.get("from", "")), str(substitute.get("to", "")))
		if sw != "": return fail("substitute", {"text": sw})
		inputs = inputs_with(recipe_id, substitute)
	if craft_kind == "alchemy":
		# The furnace sets the batch (G1); the fire must be one you have here.
		if furnace.get("cracked", false): return fail("cracked", {"text": Tx.t("sim.crafting.furnace_cracked") % ContentDB.item_name(str(furnace.id))})
		if count > int(furnace.get("batch", 1)):
			return fail("batch", {"text": Tx.t("sim.crafting.furnace_batch") % [ContentDB.item_name(str(furnace.get("id", ""))), int(furnace.get("batch", 1))]})
		if not fire in fires_available(c): fire = "charcoal"
		# Some pills take only one fire (S48: the Heavenly Flame Pill).
		var need_fire := str(ContentDB.entry("recipes", recipe_id).get("fire", ""))
		if need_fire != "" and fire != need_fire:
			return fail("needs_fire", {"text": Tx.t("sim.crafting.needs_fire") % Tx.t("ui.crafts.fire_" + need_fire)})
	var why := recipe_check(c, recipe_id, count, craft_kind, inputs)
	if why != "": return fail("cannot_craft", {"text": why})
	var r := ContentDB.entry("recipes", recipe_id)
	# Herbs that fight each other blow the furnace (S44): the batch is lost.
	if craft_kind == "alchemy":
		var clash := conflict_in(inputs)
		if not clash.is_empty(): return blast(c, recipe_id, with_aged(c, inputs, count).inputs, 1, clash)
	var aged := with_aged(c, inputs, count)
	var rng := Rng.stream(c.id, "crafting")
	var quality := "common"
	if craft_kind in ["alchemy", "smithing", "talisman"]:
		var avg := quality_score(c, craft_kind, furnace, r, scores)
		avg += float(ContentDB.config("garden").get("age_quality", 0.04)) * int(aged.tiers)   # older herbs refine better (S45)
		var roll := avg + rng.randf_range(-0.08, 0.08)
		quality = "flawed" if roll < 0.35 else ("common" if roll < 0.6 else ("fine" if roll < 0.78 else ("superior" if roll < 0.9 else "perfect")))
		if craft_kind == "alchemy" and quality == "perfect": quality = _rare_pill_quality(c, scores, rng, rare_allowed(furnace, fire))
	for inp in aged.inputs: game.inventory.apply_remove(c.id, str(inp.item), int(inp.count), "craft:" + recipe_id)
	if craft_kind == "alchemy" and fire == "beast_fire": game.inventory.apply_remove(c.id, _core_to_burn(c), 1, "beast_fire")
	# S44 pill tribulation: a Heaven-grade (or better) pill that reaches Halo or Soul at the furnace must first come
	# through the bolts; its pills wait until it does (the page plays the screen; other callers keep the roll).
	if craft_kind == "alchemy" and live and quality in ["pill_halo", "pill_soul"] \
			and StatRules.grade_index(str(r.get("grade", "plain"))) >= StatRules.grade_index("heaven"):
		return begin_tribulation(c, recipe_id, count, quality, fire, furnace)
	return _grant(c, recipe_id, count, quality, fire, craft_kind, furnace)

## Hands over what a craft made: the outputs (a furnace's extra pill, a liquid to the Draught slot), XP and events.
func _grant(c, recipe_id: String, count: int, quality: String, fire: String, craft_kind: String, furnace: Dictionary) -> Dictionary:
	var r := ContentDB.entry("recipes", recipe_id)
	var rng := Rng.stream(c.id, "crafting")
	var produced := 0
	# Marks and a furnace's extra pill roll on their own stream, so the crafting stream's sequence
	# (quality, and every forged piece after it) is the same as before furnaces existed.
	var frng := Rng.stream(c.id, "furnace")
	var marks := _roll_marks(quality, frng) if craft_kind == "alchemy" else 0
	for out in r.get("outputs", []):
		var n := int(out.count) * count
		if craft_kind == "alchemy" and frng.randf() < float(furnace.get("yield", 0.0)): n += 1   # the furnace gives one more
		if craft_kind == "cooking" and rng.randf() < c.stats.value("insight") * 0.002: n += int(out.count)
		if craft_kind == "smithing" and ContentDB.is_equipment(str(out.item)):
			var def := ContentDB.item(str(out.item))
			for i in n:
				var inst := LootRules.make_instance(str(out.item), int(def.get("ilv", 1)), quality, Rng.stream(c.id, "affix"), c.inventory.next_uid)
				c.inventory.next_uid += 1
				game.inventory.apply_add_instance(c.id, inst, "forge")
		elif craft_kind == "alchemy" and ContentDB.item(str(out.item)).has("draught"):
			game.inventory.apply_draught(c.id, str(out.item), n, "craft")   # a liquid goes to the Draught slot (S44)
		elif craft_kind == "alchemy":
			game.inventory.apply_add(c.id, str(out.item), n, "craft", {"quality": quality, "marks": marks} if marks > 0 else {"quality": quality})
		elif craft_kind == "talisman" and ContentDB.has_entry("talismans", str(out.item)):
			game.inventory.apply_add(c.id, str(out.item), n, "craft", {"quality": quality})
		else:
			game.inventory.apply_add(c.id, str(out.item), n, "craft")
		produced += n
	var xp := float(ContentDB.curve("profession_xp.craft_per_grade", 10)) * (StatRules.grade_index(str(r.get("grade", "plain"))) + 1) * count
	if craft_kind == "cooking": xp = float(ContentDB.curve("profession_xp.cook", 6)) * count
	if r.has("xp"): xp = float(r.xp) * count   # star charts: 40 per route (S29)
	if quality in ["fine", "superior", "perfect", "pill_grain", "pill_halo", "pill_soul"]: xp *= 1.5
	add_xp(c, craft_kind, xp)
	if craft_kind == "alchemy": game.progression.apply_insight(c.id, "alchemy", 3.0 * count, "craft:" + recipe_id)
	if craft_kind == "smithing": game.progression.apply_insight(c.id, "refining", 3.0, "craft:" + recipe_id)
	emit("craft_completed", {"actor": c.id, "recipe": recipe_id, "craft": craft_kind, "quality": quality, "count": produced, "marks": marks, "fire": fire})
	if quality in ["pill_halo", "pill_soul"]: emit("pill_cloud", {"actor": c.id, "recipe": recipe_id, "quality": quality})
	return ok({"quality": quality, "count": produced, "marks": marks, "fire": fire})

# ------------------------------------------------------------------ herb nature, roles and conflicts (S44)
## How far a recipe's herbs move the Extraction band, in parts of the bar: +8% for each hot herb, -8% for each cold.
func nature_shift(recipe_id: String, substitute: Dictionary = {}) -> float:
	var step := float(upkeep("nature_shift", 0.08))
	var shift := 0.0
	for inp in inputs_with(recipe_id, substitute):
		match str(ContentDB.item(str(inp.item)).get("nature", "")):
			"hot": shift += step
			"cold": shift -= step
	return shift

## A recipe's inputs with one herb swapped (the substitute takes the same count and slot).
func inputs_with(recipe_id: String, substitute: Dictionary) -> Array:
	var out: Array = []
	for inp in ContentDB.entry("recipes", recipe_id).get("inputs", []):
		var e: Dictionary = inp.duplicate()
		if not substitute.is_empty() and str(inp.item) == str(substitute.get("from", "")): e.item = str(substitute.get("to", ""))
		out.append(e)
	return out

## The role of an input slot: recipe order gives Principal, Minister, Assistant, Envoy.
func role_of(recipe_id: String, item_id: String) -> String:
	var r := ContentDB.entry("recipes", recipe_id)
	var roles: Array = r.get("roles", [])
	var inputs: Array = r.get("inputs", [])
	for i in inputs.size():
		if str(inputs[i].item) == item_id and i < roles.size(): return str(roles[i])
	return ""

## Why this herb cannot stand in for that one ("" when it can): Alchemy Dao tier 5, same nature, a role it can fill.
func substitute_check(c, recipe_id: String, from: String, to: String) -> String:
	if int(c.cultivator.daos.get("alchemy", {}).get("tier", 0)) < int(upkeep("substitute_tier", 5)): return Tx.t("sim.crafting.substitute_tier")
	var role := role_of(recipe_id, from)
	var a := ContentDB.item(from)
	var b := ContentDB.item(to)
	if role == "" or str(b.get("type", "")) != "herb" or from == to: return Tx.t("sim.crafting.substitute_herb")
	if str(a.get("nature", "")) != str(b.get("nature", "")): return Tx.t("sim.crafting.substitute_nature") % str(a.get("nature", "")).capitalize()
	if not role in b.get("roles", []): return Tx.t("sim.crafting.substitute_role") % [ContentDB.item_name(to), Tx.t("ui.crafts.role_" + role)]
	return ""

## The herbs that could stand in for one input here (same nature and a role they can fill).
func substitutes_for(c, recipe_id: String, from: String) -> Array:
	var out: Array = []
	for it in ContentDB.all("items"):
		if str(it.get("type", "")) == "herb" and substitute_check(c, recipe_id, from, str(it.id)) == "": out.append(str(it.id))
	return out

## The first listed conflict among these inputs, or {}.
func conflict_in(inputs: Array) -> Dictionary:
	var have := {}
	for inp in inputs: have[str(inp.item)] = true
	for row in ContentDB.all("herb_conflicts"):
		var pair: Array = row.get("herbs", [])
		if pair.size() == 2 and have.has(str(pair[0])) and have.has(str(pair[1])): return row
	return {}

## A furnace blast (S44): the batch is lost, the furnace loses 10 durability, and the blast leaves a minor body
## injury (Progression reacts to furnace_blast). The pair is remembered, so the page can warn next time.
func blast(c, recipe_id: String, inputs: Array, count: int, clash: Dictionary) -> Dictionary:
	for inp in inputs: game.inventory.apply_remove(c.id, str(inp.item), int(inp.count) * count, "furnace_blast")
	var inst = c.inventory.furnace
	if inst != null: game.inventory.apply_durability(c.id, inst, int(inst.get("durability", 100)) - int(upkeep("blast_durability", 10)), "tool_furnace")
	var known: Array = c.crafting.get("known_conflicts", [])
	if not known.has(str(clash.id)): known.append(str(clash.id))
	c.crafting["known_conflicts"] = known
	emit("furnace_blast", {"actor": c.id, "recipe": recipe_id, "conflict": str(clash.id), "herbs": clash.get("herbs", []),
		"durability": int(inst.get("durability", 0)) if inst != null else 0})
	return fail("blast", {"text": Tx.t("sim.crafting.furnace_blast") % str(clash.get("text", ""))})

# ------------------------------------------------------------------ S44 pill tribulation and the Pill Soul's flight
var tribulations: Dictionary = {}   # actor -> the tribulation in progress {recipe, count, quality, fire, furnace, bolts[], blocked, answered, stage}

## 3 bolts, +2 for each grade above Heaven, at most 9, at times drawn from the crafting stream.
func begin_tribulation(c, recipe_id: String, count: int, quality: String, fire: String, furnace: Dictionary) -> Dictionary:
	var k: Dictionary = upkeep("tribulation", {})
	var above := StatRules.grade_index(str(ContentDB.entry("recipes", recipe_id).get("grade", "heaven"))) - StatRules.grade_index("heaven")
	var n := clampi(int(k.get("bolts", 3)) + int(k.get("per_grade", 2)) * above, 1, int(k.get("max", 9)))
	var rng := Rng.stream(c.id, "crafting")
	var times: Array = []
	var t := float(k.get("first_s", 1.2))
	for i in n:
		times.append(snappedf(t, 0.01))
		t += rng.randf_range(float(k.get("gap_min_s", 0.7)), float(k.get("gap_max_s", 1.3)))
	tribulations[c.id] = {"recipe": recipe_id, "count": count, "quality": quality, "fire": fire, "furnace": furnace.duplicate(),
		"bolts": times, "blocked": 0, "answered": 0, "stage": "bolts"}
	return ok({"pending": "tribulation", "bolts": times, "window": float(k.get("window_s", 0.22)), "quality": quality})

## One bolt: `timing` is how far from its strike the shield went up (seconds, either side); inside the window it holds.
func tribulation_shield(c, bolt: int, timing: float) -> Dictionary:
	var tr: Dictionary = tribulations.get(c.id, {})
	if tr.is_empty() or str(tr.stage) != "bolts": return fail("no_tribulation")
	if bolt != int(tr.answered): return fail("wrong_bolt")
	var k: Dictionary = upkeep("tribulation", {})
	var held := absf(timing) <= float(k.get("window_s", 0.22))
	tr.answered = int(tr.answered) + 1
	if held: tr.blocked = int(tr.blocked) + 1
	if int(tr.answered) < (tr.bolts as Array).size(): return ok({"held": held, "left": (tr.bolts as Array).size() - int(tr.answered)})
	# Every bolt answered: all held keeps the result (a 10% chance to rise a tier); one missed drops it to Perfect.
	var before := str(tr.quality)
	var after := before
	if int(tr.blocked) < (tr.bolts as Array).size(): after = "perfect"
	elif before == "pill_halo" and Rng.stream(c.id, "crafting").randf() < float(k.get("rise_chance", 0.1)): after = "pill_soul"
	tr.quality = after
	emit("pill_tribulation_result", {"actor": c.id, "recipe": str(tr.recipe), "bolts": (tr.bolts as Array).size(), "blocked": int(tr.blocked),
		"before": before, "after": after})
	if after == "pill_soul":
		# The Pill Soul flees the furnace: one tap as it passes the mark catches it.
		tr.stage = "soul"
		tr.catch_at = snappedf(Rng.stream(c.id, "crafting").randf_range(float(k.get("soul_min_s", 1.0)), float(k.get("soul_max_s", 1.6))), 0.01)
		return ok({"held": held, "left": 0, "pending": "soul", "catch_at": tr.catch_at, "window": float(k.get("soul_window_s", 0.2)), "quality": after})
	tribulations.erase(c.id)
	var res := _grant(c, str(tr.recipe), int(tr.count), after, str(tr.fire), "alchemy", tr.furnace)
	res.held = held
	res.left = 0
	return res

## The Pill Soul's flight: caught, it stays a Pill Soul; missed, it settles as a Pill Halo. The batch is never lost.
func catch_pill_soul(c, timing: float) -> Dictionary:
	var tr: Dictionary = tribulations.get(c.id, {})
	if tr.is_empty() or str(tr.stage) != "soul": return fail("no_soul")
	var caught := absf(timing) <= float(upkeep("tribulation", {}).get("soul_window_s", 0.2))
	var quality := "pill_soul" if caught else "pill_halo"
	tribulations.erase(c.id)
	emit("pill_soul_flight", {"actor": c.id, "recipe": str(tr.recipe), "caught": caught})
	var res := _grant(c, str(tr.recipe), int(tr.count), quality, str(tr.fire), "alchemy", tr.furnace)
	res.caught = caught
	return res

## A tribulation left unfinished (the page closed, another craft begun) settles as if every bolt that was not
## answered had struck, and a fleeing Soul got away.
func _settle_tribulation(c) -> void:
	var tr: Dictionary = tribulations.get(c.id, {})
	if tr.is_empty(): return
	if str(tr.stage) == "soul": catch_pill_soul(c, 99.0)
	else:
		while tribulations.has(c.id) and str(tribulations[c.id].get("stage", "")) == "bolts":
			tribulation_shield(c, int(tribulations[c.id].answered), 99.0)
		if tribulations.has(c.id): catch_pill_soul(c, 99.0)

## The quality score a craft rolls around: the strikes, the crafter, and the furnace (S44). The furnace's impurity
## filter takes out that share of what each strike missed; a furnace of the pill's own element adds 5%.
func quality_score(c, craft_kind: String, furnace: Dictionary, r: Dictionary, scores: Array) -> float:
	var filt := float(furnace.get("filter", 0.0))
	var total := 0.0
	for s in scores:
		var sc := clampf(float(s), 0.0, 1.0)
		total += sc + (1.0 - sc) * filt
	var avg := total / maxf(1.0, scores.size()) if not scores.is_empty() else 0.6 + 0.4 * filt
	avg += c.stats.value("crafting_control") * 0.2 + 0.05 * int(c.cultivator.daos.get("alchemy" if craft_kind == "alchemy" else "refining", {}).get("tier", 0))
	if str(furnace.get("element", "")) != "" and str(furnace.get("element", "")) == str(r.get("element", "")):
		avg += float(upkeep("furnace_affinity", 0.05))
	return avg

# ------------------------------------------------------------------ furnaces and fire (gap report G1)
## The furnace in the furnace slot (S44): {id, uid, band, batch, filter, yield, named, element, durability}.
## Enhancement steadies its heat, +1% band a level. A cracked furnace (durability 0) refines nothing until mended;
## without one you refine a single pill at a time.
func furnace_of(c) -> Dictionary:
	var none := {"id": "", "uid": -1, "band": 0.0, "batch": 1, "filter": 0.0, "yield": 0.0, "element": "", "durability": 0}
	var inst = c.inventory.furnace
	if inst == null: return none
	var f: Dictionary = ContentDB.item(str(inst.id)).get("furnace", {})
	if f.is_empty(): return none
	var out := f.duplicate()
	out.id = str(inst.id)
	out.uid = int(inst.get("uid", -1))
	out.durability = int(inst.get("durability", 100))
	out.band = float(f.get("band", 0.0)) + float(upkeep("furnace_band_per_level", 0.01)) * int(inst.get("enhance", 0))
	out.element = str(f.get("element", ""))
	if int(out.durability) <= 0:
		none.id = str(inst.id)
		none.uid = out.uid
		none.cracked = true
		return none
	return out

## Fires this character can light here: charcoal always; Earth Fire at a vent; Beast Fire with a core to burn;
## a Heavenly Flame once one is absorbed.
func fires_available(c) -> Array:
	var out := ["charcoal"]
	if station_near(c, ["earth_vent"]): out.append("earth_fire")
	if _core_to_burn(c) != "": out.append("beast_fire")
	if not (c.crafting.get("flames", []) as Array).is_empty(): out.append("heavenly_flame")
	return out

## How much wider the strike band is on this fire in this character's furnace.
func band_mult(c, fire: String) -> float:
	var fires: Dictionary = ContentDB.config("grades").get("pill", {}).get("fires", {})
	return 1.0 + float(fires.get(fire, {}).get("band", 0.0)) + float(furnace_of(c).get("band", 0.0))

## The rare qualities a perfect run can reach: the fire's, or all three in a named furnace.
func rare_allowed(furnace: Dictionary, fire: String) -> Array:
	if furnace.get("named", false): return ["pill_grain", "pill_halo", "pill_soul"]
	return ContentDB.config("grades").get("pill", {}).get("fires", {}).get(fire, {}).get("rare", [])

## The weakest beast core of rank 2 or more in the bag, to burn as Beast Fire (S44); a rank-1 core is too weak.
func _core_to_burn(c) -> String:
	var best := ""
	var best_rank := 99
	for s in c.inventory.bag:
		if s == null: continue
		var core: Dictionary = ContentDB.item(str(s.id)).get("core", {})
		var rank := int(core.get("rank", 1)) if not core.is_empty() else 0
		if rank >= int(upkeep("beast_fire_min_rank", 2)) and rank < best_rank:
			best = str(s.id)
			best_rank = rank
	return best

func _roll_marks(quality: String, rng: RandomNumberGenerator) -> int:
	var r: Array = ContentDB.config("grades").get("pill", {}).get("marks", {}).get("ranges", {}).get(quality, [0, 0])
	return rng.randi_range(int(r[0]), int(r[1]))

## Absorb a Heavenly Flame: it burns under every furnace from now on. A second copy gutters into Spirit Stones.
func absorb_flame(c, index: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var id := str(c.inventory.bag[index].id)
	if str(ContentDB.item(id).get("use_action", "")) != "absorb_flame": return fail("not_a_flame")
	var flames: Array = c.crafting.get("flames", [])
	game.inventory.apply_remove_index(c.id, index, 1, "absorb_flame")
	if flames.has(id):
		game.economy.apply_currency("spirit_stone", 20, "flame_gutters")
		return ok({"text": Tx.t("sim.crafting.flame_gutters") % ContentDB.item_name(id), "duplicate": true})
	flames.append(id)
	c.crafting["flames"] = flames
	if ContentDB.has_entry("codex", id): game.apply_effects(c.id, [{"kind": "codex", "entry": id}], "flame")
	emit("flame_absorbed", {"actor": c.id, "flame": id})
	emit("system_used", {"actor": c.id, "system": "absorb_flame"})
	return ok({"text": Tx.t("sim.crafting.flame_absorbed") % ContentDB.item_name(id)})

# ------------------------------------------------------------------ natural treasures
## The Evergreen Heart Tree: one per character, planted in rich earth; its first fruit comes a
## day later, then one each season. Pure query: where it grows and whether a fruit is ready.
func evergreen_state(c) -> Dictionary:
	var tree: Dictionary = c.crafting.get("evergreen", {})
	if tree.is_empty(): return {"planted": false}
	var cfg: Dictionary = ContentDB.stat_const("treasures", {})
	var season_s := float(cfg.get("season_days", 7)) * 86400.0
	var first_s := float(cfg.get("first_fruit_h", 24)) * 3600.0
	var age := Clock.now_utc() - float(tree.get("planted_utc", 0.0))
	var season := int(floor((age - first_s) / season_s)) if age >= first_s else -1
	var harvested := int(tree.get("harvested", -1))
	var ready := season > harvested
	var next_utc := float(tree.get("planted_utc", 0.0)) + first_s + (0.0 if season < 0 else float(harvested + 1) * season_s)
	return {"planted": true, "room": str(tree.get("room", "")), "object": str(tree.get("object", "")), "ready": ready,
		"season": season, "next_utc": next_utc}

## Interacting with rich earth: plant the seed, or pick the season's fruit from your tree.
func tend_treasure_plot(c, o: Dictionary) -> Dictionary:
	var here: String = game.room_rt.room_id if game.room_rt else ""
	var st := evergreen_state(c)
	if not st.planted:
		if c.inventory.count("evergreen_heart_seed") <= 0: return ok({"text": Tx.t("sim.crafting.rich_earth_waits")})
		game.inventory.apply_remove(c.id, "evergreen_heart_seed", 1, "plant")
		c.crafting["evergreen"] = {"room": here, "object": str(o.id), "planted_utc": Clock.now_utc(), "harvested": -1}
		emit("system_used", {"actor": c.id, "system": "plant_evergreen"})
		emit("treasure_planted", {"actor": c.id, "treasure": "evergreen_heart_tree", "room": here})
		return ok({"text": Tx.t("sim.crafting.you_plant_the_seed")})
	if str(st.room) != here or str(st.object) != str(o.id):
		return ok({"text": Tx.t("sim.crafting.your_tree_grows_in") % ContentDB.name_of("rooms", str(st.room))})
	if st.ready:
		game.inventory.apply_add(c.id, "evergreen_heart_fruit", 1, "evergreen")
		c.crafting.evergreen.harvested = int(st.season)
		emit("treasure_harvested", {"actor": c.id, "treasure": "evergreen_heart_tree", "item": "evergreen_heart_fruit"})
		return ok({"text": Tx.t("sim.crafting.you_pick_the_fruit")})
	var hours := maxf(1.0, ceilf((float(st.next_utc) - Clock.now_utc()) / 3600.0))
	return ok({"text": Tx.t("sim.crafting.next_fruit_in") % int(hours)})

## Pill Grain, Halo and Soul (S15): a perfect run (every strike perfect, from Heart Tempering 1)
## plus luck; a special furnace and the Alchemy Dao improve the odds.
func _rare_pill_quality(c, scores: Array, rng: RandomNumberGenerator, allowed: Array = ["pill_grain", "pill_halo", "pill_soul"]) -> String:
	var k: Dictionary = ContentDB.curve("craft_step", {})
	if scores.size() < int(k.get("steps", 3)) or not Unlocks.is_unlocked(c.id, "perfect_timing"): return "perfect"
	for sc in scores:
		if float(sc) < float(k.get("perfect", 0.85)): return "perfect"
	var rare: Dictionary = ContentDB.config("grades").get("pill", {}).get("rare", {})
	var boost := 1.0 + furnace_bonus(c) + 0.1 * int(c.cultivator.daos.get("alchemy", {}).get("tier", 0))
	var roll := rng.randf()
	var edge := 0.0
	for q in ["pill_soul", "pill_halo", "pill_grain"]:
		if not q in allowed: continue   # charcoal stops at Perfect (G1)
		edge += float(rare.get(q, 0.0)) * boost
		if roll < edge: return q
	return "perfect"

## The nearest alchemy furnace's bonus to rare pill qualities (sect halls keep better furnaces).
func furnace_bonus(c) -> float:
	var st: ActorState = game.actor_state(c.id)
	if game.room_rt == null: return 0.0
	var best := 0.0
	for o in game.room_rt.def.get("objects", []):
		if str(o.type) != "alchemy_furnace": continue
		var at: Array = o.get("at", [0, 0])
		if st == null or st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) < 180.0: best = maxf(best, float(o.get("furnace_bonus", 0.0)))
	return best

func queue_auto(c, recipe_id: String, count: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "auto_refine"): return fail("locked")
	if c.crafting.auto_queue.size() >= 5: return fail("queue_full")
	var why := recipe_check(c, recipe_id, count, "alchemy")
	if why != "": return fail("cannot_craft", {"text": why})
	if count > int(furnace_of(c).get("batch", 1)): return fail("batch", {"text": Tx.t("sim.crafting.furnace_batch") % [ContentDB.item_name(str(furnace_of(c).get("id", ""))), int(furnace_of(c).get("batch", 1))]})
	var r := ContentDB.entry("recipes", recipe_id)
	for inp in r.get("inputs", []): game.inventory.apply_remove(c.id, str(inp.item), int(inp.count) * count, "auto_refine")
	c.crafting.auto_queue.append({"recipe": recipe_id, "count": count, "done_utc": Clock.now_utc() + float(r.get("time_s", 300)) * count, "quality": "common"})
	emit("craft_started", {"actor": c.id, "recipe": recipe_id, "count": count})
	emit("system_used", {"actor": c.id, "system": "auto_refine_queued"})
	return ok()

func collect_auto(c) -> Dictionary:
	var got := 0
	for q in c.crafting.auto_queue.duplicate():
		if Clock.now_utc() >= float(q.done_utc):
			for out in ContentDB.entry("recipes", str(q.recipe)).get("outputs", []):
				game.inventory.apply_add(c.id, str(out.item), int(out.count) * int(q.count), "auto_refine")
			c.crafting.auto_queue.erase(q)
			got += 1
			# Auto-refine teaches a quarter of what refining by hand does (G1, matching S23's idle rule).
			var ar := ContentDB.entry("recipes", str(q.recipe))
			add_xp(c, "alchemy", float(ContentDB.curve("profession_xp.craft_per_grade", 10)) * (StatRules.grade_index(str(ar.get("grade", "plain"))) + 1) * int(q.count) * 0.25)
			emit("craft_completed", {"actor": c.id, "recipe": q.recipe, "craft": "alchemy", "quality": "common", "count": q.count, "auto": true})
	if got == 0: return fail("not_ready", {"text": Tx.t("sim.crafting.no_batch_is_finished_yet")})
	emit("system_used", {"actor": c.id, "system": "auto_refine_collected"})
	return ok({"batches": got})

# ------------------------------------------------------------------ gear upkeep (S14, S47)
func upkeep(key: String, fallback):
	return ContentDB.config("forge_upkeep").get(key, fallback)

## The salvage.json row for an item's grade: the metal it is forged and enhanced with, and what Salvage returns.
## Grades past the table use its last row.
func grade_row(item_id: String) -> Dictionary:
	var g := str(ContentDB.item(item_id).get("grade", "plain"))
	if ContentDB.has_entry("salvage", g): return ContentDB.entry("salvage", g)
	var rows: Array = ContentDB.all("salvage")
	return rows[-1] if not rows.is_empty() else {"metal": "copper_ore", "returns": []}

## An equipment instance by uid, whether worn or in the bag: {inst, slot, index}; {} when it is not there.
func locate(c, uid: int) -> Dictionary:
	if uid < 0: return {}
	for sl in c.inventory.equipped:
		var e = c.inventory.equipped[sl]
		if e != null and int(e.get("uid", -2)) == uid: return {"inst": e, "slot": str(sl), "index": -1}
	if c.inventory.furnace != null and int(c.inventory.furnace.get("uid", -2)) == uid: return {"inst": c.inventory.furnace, "slot": "tool_furnace", "index": -1}
	var i: int = c.inventory.find_uid(uid)
	if i >= 0 and c.inventory.bag[i] != null: return {"inst": c.inventory.bag[i], "slot": "", "index": i}
	return {}

func _uid_at(c, index: int) -> int:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return -1
	return int(c.inventory.bag[index].get("uid", -1))

## The chance an enhancement from the item's current level succeeds: sure up to +5, then 12% less a level,
## plus the item's pity (+5% for each failure since its last success) and any essence fed in.
func enhance_chance(inst: Dictionary, essence := 0) -> float:
	var lvl := int(inst.get("enhance", 0))
	if lvl < int(upkeep("risky_from", 5)): return 1.0
	var base := 1.0 - float(upkeep("fail_step", 0.12)) * (lvl - int(upkeep("risky_from", 5)) + 1)
	return clampf(base + float(inst.get("pity", 0.0)) + float(upkeep("essence_step", 0.025)) * essence, 0.0, 1.0)

## What an enhancement costs: {metal, count, taels, shards}.
func enhance_cost(inst: Dictionary) -> Dictionary:
	var lvl := int(inst.get("enhance", 0))
	var gi := StatRules.grade_index(str(ContentDB.item(str(inst.id)).get("grade", "plain")))
	return {"metal": str(grade_row(str(inst.id)).get("metal", "copper_ore")), "count": 2 * (lvl + 1), "taels": 20 * (lvl + 1) * (gi + 1),
		"shards": maxi(0, lvl - 4)}

## Why an enhancement cannot be paid for now ("" when it can): the metal, taels, shards and essence it needs.
func enhance_check(c, inst: Dictionary, essence := 0) -> String:
	if int(inst.get("enhance", 0)) >= 10: return Tx.t("ui.forge.max")
	var cost := enhance_cost(inst)
	if c.inventory.count(str(cost.metal)) < int(cost.count): return Tx.t("sim.crafting.needs_2") % [int(cost.count), ContentDB.item_name(str(cost.metal))]
	if game.economy.balance("silver_tael") < int(cost.taels): return Tx.t("ui.forge.taels") % int(cost.taels)
	if int(cost.shards) > 0 and c.inventory.count("spirit_stone_shard") < int(cost.shards): return Tx.t("sim.crafting.needs_spirit_stone_shards")
	if c.inventory.count("refining_essence") < essence: return Tx.t("sim.crafting.needs_2") % [essence, ContentDB.item_name("refining_essence")]
	return ""

## Why a reroll cannot be paid for now ("" when it can).
func reroll_check(c, inst: Dictionary) -> String:
	if (inst.get("affixes", []) as Array).is_empty(): return Tx.t("sim.crafting.no_affixes")
	var cost := reroll_cost(inst)
	if c.inventory.count("refining_essence") < int(cost.essence): return Tx.t("sim.crafting.needs_2") % [int(cost.essence), ContentDB.item_name("refining_essence")]
	if game.economy.balance("silver_tael") < int(cost.taels): return Tx.t("ui.forge.taels") % int(cost.taels)
	return ""

## Enhance (S14, S47): never destroys an item or takes a level. A failure spends the materials and adds 5% pity to
## the item, shown on it; a success clears the pity. Refining Essence (from Salvage) steadies an attempt, 2.5% each.
## The roll is on the affix stream, so it is deterministic per character.
func enhance(c, intent: Dictionary) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var at := locate(c, int(intent.get("uid", -1)))
	if at.is_empty():
		var slot := str(intent.get("slot", ""))
		var index := int(intent.get("index", -1))
		if slot != "" and c.inventory.equipped.get(slot) != null: at = {"inst": c.inventory.equipped[slot], "slot": slot, "index": -1}
		elif index >= 0 and index < c.inventory.bag.size() and c.inventory.bag[index] != null: at = {"inst": c.inventory.bag[index], "slot": "", "index": index}
	if at.is_empty() or not ContentDB.is_equipment(str(at.inst.id)): return fail("not_equipment")
	var inst: Dictionary = at.inst
	var lvl := int(inst.get("enhance", 0))
	if lvl >= 10: return fail("max")
	var cost := enhance_cost(inst)
	if c.inventory.count(str(cost.metal)) < int(cost.count): return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(cost.count), ContentDB.item_name(str(cost.metal))]})
	if game.economy.balance("silver_tael") < int(cost.taels): return fail("insufficient_funds")
	if int(cost.shards) > 0 and c.inventory.count("spirit_stone_shard") < int(cost.shards): return fail("materials", {"text": Tx.t("sim.crafting.needs_spirit_stone_shards")})
	var essence := clampi(int(intent.get("essence", 0)), 0, int(upkeep("essence_max", 4))) if lvl >= int(upkeep("risky_from", 5)) else 0
	if c.inventory.count("refining_essence") < essence: return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [essence, ContentDB.item_name("refining_essence")]})
	var chance := enhance_chance(inst, essence)
	game.inventory.apply_remove(c.id, str(cost.metal), int(cost.count), "enhance")
	game.economy.apply_currency("silver_tael", -int(cost.taels), "enhance")
	if int(cost.shards) > 0: game.inventory.apply_remove(c.id, "spirit_stone_shard", int(cost.shards), "enhance")
	if essence > 0: game.inventory.apply_remove(c.id, "refining_essence", essence, "enhance")
	var success := chance >= 1.0 or Rng.stream(c.id, "affix").randf() < chance
	if success:
		inst.pity = 0.0
		game.inventory.apply_enhance(c.id, inst, lvl + 1, str(at.slot))
	else:
		inst.pity = snappedf(float(inst.get("pity", 0.0)) + float(upkeep("pity_step", 0.05)), 0.001)
	emit("item_enhanced", {"actor": c.id, "item": inst.id, "level": int(inst.get("enhance", 0)), "success": success, "pity": float(inst.get("pity", 0.0))})
	emit("system_used", {"actor": c.id, "system": "enhance"})
	return ok({"success": success, "level": int(inst.get("enhance", 0)), "pity": float(inst.get("pity", 0.0)), "chance": chance})

## Inherit (S47): move an item's enhancement, less two levels, onto another piece for the same slot, for 2 Spirit
## Stones a level moved. The old piece goes back to +0; the new one keeps its own level if that is higher.
func inherit(c, from_uid: int, to_uid: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var a := locate(c, from_uid)
	var b := locate(c, to_uid)
	if a.is_empty() or b.is_empty() or from_uid == to_uid: return fail("not_equipment")
	var da := ContentDB.item(str(a.inst.id))
	var db := ContentDB.item(str(b.inst.id))
	if not ContentDB.is_equipment(str(a.inst.id)) or not ContentDB.is_equipment(str(b.inst.id)) or str(da.get("slot", "")) != str(db.get("slot", "")):
		return fail("wrong_slot", {"text": Tx.t("sim.crafting.inherit_same_slot")})
	var moved := int(a.inst.get("enhance", 0)) - int(upkeep("inherit_loss", 2))
	if moved <= int(b.inst.get("enhance", 0)): return fail("nothing_to_move", {"text": Tx.t("sim.crafting.inherit_nothing")})
	var stones := moved * int(upkeep("inherit_stones_per_level", 2))
	if game.economy.balance("spirit_stone") < stones: return fail("insufficient_funds", {"text": Tx.t("sim.crafting.inherit_stones") % stones})
	game.economy.apply_currency("spirit_stone", -stones, "inherit")
	game.inventory.apply_enhance(c.id, b.inst, moved, str(b.slot))
	game.inventory.apply_enhance(c.id, a.inst, 0, str(a.slot))
	a.inst.pity = 0.0
	emit("enhancement_inherited", {"actor": c.id, "item": b.inst.id, "from": a.inst.id, "levels": moved, "stones": stones})
	emit("system_used", {"actor": c.id, "system": "inherit"})
	return ok({"levels": moved, "stones": stones})

## What salvaging a set of bag items would return (locked, bound and worn pieces are never salvaged).
func salvage_preview(c, uids: Array) -> Dictionary:
	var returns := {}
	var items: Array = []
	for u in uids:
		var i: int = c.inventory.find_uid(int(u))
		if i < 0 or c.inventory.bag[i] == null: continue
		var inst: Dictionary = c.inventory.bag[i]
		if not ContentDB.is_equipment(str(inst.id)) or inst.get("bound", false) or c.inventory.locked.has(int(inst.get("uid", -1))): continue
		if not ContentDB.item(str(inst.id)).get("sell", true): continue   # a named piece (the Nine-Dragon Cauldron) is never broken up
		items.append(int(inst.uid))
		for r in grade_row(str(inst.id)).get("returns", []):
			returns[str(r.item)] = int(returns.get(str(r.item), 0)) + int(r.count)
	return {"items": items, "returns": returns}

## Salvage (S47): dismantle gear into its grade's metal and Refining Essence. Locked items are never touched.
func salvage(c, uids: Array) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var pv := salvage_preview(c, uids)
	if pv.items.is_empty(): return fail("cannot_salvage")
	var ids: Array = []
	for u in pv.items:
		var i: int = c.inventory.find_uid(int(u))
		ids.append(str(c.inventory.bag[i].id))
		game.inventory.apply_remove_index(c.id, i, 1, "salvage")
	for item_id in pv.returns: game.inventory.apply_add(c.id, str(item_id), int(pv.returns[item_id]), "salvage")
	emit("items_salvaged", {"actor": c.id, "items": ids, "returned": pv.returns})
	emit("system_used", {"actor": c.id, "system": "salvage"})
	return ok({"items": ids, "returned": pv.returns})

## What rerolling an item's affixes costs: {essence, taels}; a locked affix doubles it.
func reroll_cost(inst: Dictionary) -> Dictionary:
	var gi := StatRules.grade_index(str(ContentDB.item(str(inst.id)).get("grade", "plain")))
	var ess: Array = upkeep("reroll_essence", [1])
	var mult := int(upkeep("lock_mult", 2)) if int(inst.get("locked_affix", -1)) >= 0 else 1
	return {"essence": int(ess[mini(gi, ess.size() - 1)]) * mult, "taels": int(upkeep("reroll_taels", 60)) * (gi + 1) * mult}

## Reroll (S47 affix lock): every affix but the locked one is rolled again on the affix stream. The new roll waits
## beside the old one until you choose which to keep.
func reroll(c, uid: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var at := locate(c, uid)
	if at.is_empty() or not ContentDB.is_equipment(str(at.inst.id)): return fail("not_equipment")
	var inst: Dictionary = at.inst
	if (inst.get("affixes", []) as Array).is_empty(): return fail("no_affixes", {"text": Tx.t("sim.crafting.no_affixes")})
	var cost := reroll_cost(inst)
	if c.inventory.count("refining_essence") < int(cost.essence): return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(cost.essence), ContentDB.item_name("refining_essence")]})
	if game.economy.balance("silver_tael") < int(cost.taels): return fail("insufficient_funds")
	game.inventory.apply_remove(c.id, "refining_essence", int(cost.essence), "reroll")
	game.economy.apply_currency("silver_tael", -int(cost.taels), "reroll")
	var lock := int(inst.get("locked_affix", -1))
	var old: Array = inst.affixes
	var fresh: Array = []
	var taken: Array = []
	if lock >= 0 and lock < old.size(): taken.append(str(old[lock].id))
	var rng := Rng.stream(c.id, "affix")
	for i in old.size():
		if i == lock:
			fresh.append(old[i].duplicate())
			continue
		var a := LootRules.roll_affix(str(inst.id), int(inst.get("ilv", 1)), rng, taken)
		if a.is_empty(): a = old[i].duplicate()
		taken.append(str(a.id))
		fresh.append(a)
	inst.pending_affixes = fresh
	emit("affixes_rerolled", {"actor": c.id, "item": inst.id, "uid": uid, "old": old, "new": fresh})
	return ok({"old": old, "new": fresh, "cost": cost})

## Keep the new roll or the old one; either way the pending roll is gone.
func choose_affixes(c, uid: int, keep_new: bool) -> Dictionary:
	var at := locate(c, uid)
	if at.is_empty() or not at.inst.has("pending_affixes"): return fail("nothing_pending")
	if keep_new: game.inventory.apply_affixes(c.id, at.inst, at.inst.pending_affixes, str(at.slot))
	at.inst.erase("pending_affixes")
	return ok({"kept": "new" if keep_new else "old"})

## Lock one affix against the next rerolls (-1 unlocks).
func lock_affix(c, uid: int, affix: int) -> Dictionary:
	var at := locate(c, uid)
	if at.is_empty() or not ContentDB.is_equipment(str(at.inst.id)): return fail("not_equipment")
	if affix >= (at.inst.get("affixes", []) as Array).size(): return fail("no_affix")
	if affix < 0: at.inst.erase("locked_affix")
	else: at.inst.locked_affix = affix
	emit("affix_locked", {"actor": c.id, "item": at.inst.id, "affix": affix})
	return ok({"locked": affix})

# ------------------------------------------------------------------ talisman craft (S47)
## Write a talisman: the page traces the stroke path and sends how well it went (0..1, smoothness and pace). A
## broken stroke spoils the paper; otherwise the score sets the quality as a strike score does at the forge. Inks
## and spirit paper are made without tracing.
func trace_talisman(c, recipe_id: String, score: float, broken: bool) -> Dictionary:
	var r := ContentDB.entry("recipes", recipe_id)
	if r.is_empty() or str(r.get("craft", "")) != "talisman": return fail("unknown_recipe")
	var why := recipe_check(c, recipe_id, 1, "talisman")
	if why != "": return fail("cannot_craft", {"text": why})
	var out := str(r.outputs[0].item)
	if not r.get("traced", false): return craft(c, recipe_id, 1, [], "talisman")
	if broken:
		for inp in r.get("inputs", []):
			if "paper" in str(inp.item): game.inventory.apply_remove(c.id, str(inp.item), 1, "talisman_spoiled")
		emit("talisman_crafted", {"actor": c.id, "item": out, "quality": "", "spoiled": true})
		return fail("spoiled", {"text": Tx.t("sim.crafting.talisman_spoiled")})
	var res := craft(c, recipe_id, 1, [clampf(score, 0.0, 1.0)], "talisman")
	if res.get("ok", false): emit("talisman_crafted", {"actor": c.id, "item": out, "quality": str(res.quality), "spoiled": false})
	return res

## Restore a Shattered Relic at the forge (S47): Expert smithing, Cloudsteel and Refining Essence make it whole again,
## a relic with its spirit still asleep (bind it to wake it, S14).
func restore_relic(c, index: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var shard := str(c.inventory.bag[index].id)
	var target := str(ContentDB.item(shard).get("restores", ""))
	if target == "": return fail("not_a_relic")
	if not station_near(c, ["forge_anvil"]): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "forge"})
	if rank_index(rank_of(c, "smithing")) < rank_index("expert"): return fail("rank", {"text": Tx.t("sim.crafting.relic_needs_expert")})
	for need in [["cloudsteel_ore", 6], ["refining_essence", 6]]:
		if c.inventory.count(str(need[0])) < int(need[1]): return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(need[1]), ContentDB.item_name(str(need[0]))]})
	if game.economy.balance("silver_tael") < 3000: return fail("insufficient_funds")
	game.inventory.apply_remove(c.id, "cloudsteel_ore", 6, "restore_relic")
	game.inventory.apply_remove(c.id, "refining_essence", 6, "restore_relic")
	game.economy.apply_currency("silver_tael", -3000, "restore_relic")
	game.inventory.apply_remove_index(c.id, c.inventory.first_index(shard), 1, "restore_relic")
	var def := ContentDB.item(target)
	var inst := LootRules.make_instance(target, int(def.get("ilv", 1)), "fine", Rng.stream(c.id, "affix"), c.inventory.next_uid)
	c.inventory.next_uid += 1
	game.inventory.apply_add_instance(c.id, inst, "restore_relic")
	emit("relic_restored", {"actor": c.id, "item": target, "from": shard})
	emit("system_used", {"actor": c.id, "system": "restore_relic"})
	return ok({"item": target})

## Mend a furnace at the forge (S44): a blast costs it 10 durability, and at 0 it is cracked. Mending takes its grade's
## metal, two for each 10 durability lost, and brings it back to 100.
func mend_cost(inst: Dictionary) -> Dictionary:
	var lost := 100 - int(inst.get("durability", 100))
	return {"metal": str(grade_row(str(inst.id)).get("metal", "copper_ore")), "count": maxi(1, int(ceil(lost / 10.0)) * 2), "lost": lost}

func mend_furnace(c, uid: int) -> Dictionary:
	var at := locate(c, uid)
	if at.is_empty() and c.inventory.furnace != null: at = {"inst": c.inventory.furnace, "slot": "tool_furnace", "index": -1}
	if at.is_empty() or str(ContentDB.item(str(at.inst.id)).get("slot", "")) != "tool_furnace": return fail("not_a_furnace")
	var cost := mend_cost(at.inst)
	if int(cost.lost) <= 0: return fail("whole", {"text": Tx.t("sim.crafting.furnace_whole")})
	if not station_near(c, ["forge_anvil"]): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "forge"})
	if c.inventory.count(str(cost.metal)) < int(cost.count):
		return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(cost.count), ContentDB.item_name(str(cost.metal))]})
	game.inventory.apply_remove(c.id, str(cost.metal), int(cost.count), "mend_furnace")
	game.inventory.apply_durability(c.id, at.inst, 100, str(at.slot))
	emit("system_used", {"actor": c.id, "system": "mend_furnace"})
	return ok({"item": str(at.inst.id)})

# ------------------------------------------------------------------ S44 ancient recipes: pages and Deduce
## A page found (the effect `recipe_page`): kept in recipe_fragments; the last page of a set teaches the recipe.
func apply_recipe_page(actor_id: String, recipe: String, page: int) -> void:
	var c = game.character(actor_id)
	var r := ContentDB.entry("recipes", recipe)
	if c == null or r.is_empty(): return
	var frags: Dictionary = c.crafting.get("recipe_fragments", {})
	var held: Array = frags.get(recipe, [])
	if not held.has(page): held.append(page)
	frags[recipe] = held
	c.crafting["recipe_fragments"] = frags
	emit("recipe_page_found", {"actor": c.id, "recipe": recipe, "page": page, "held": held.size(), "total": int(r.get("fragments", 1))})
	if held.size() >= int(r.get("fragments", 1)) and not knows(c, recipe):
		apply_learn_recipe(c.id, recipe)
		emit("recipe_deduced", {"actor": c.id, "recipe": recipe, "success": true, "whole": true})

func pages_held(c, recipe: String) -> int:
	return (c.crafting.get("recipe_fragments", {}).get(recipe, []) as Array).size()

## Deduce with pages missing (S44): 20% a page held + 10% a tier of the Alchemy Dao above the third, never above 95%.
func deduce_chance(c, recipe: String) -> float:
	var r := ContentDB.entry("recipes", recipe)
	var held := pages_held(c, recipe)
	if held >= int(r.get("fragments", 1)): return 1.0
	var tier := int(c.cultivator.daos.get("alchemy", {}).get("tier", 0))
	return minf(float(upkeep("deduce_cap", 0.95)), float(upkeep("deduce_per_page", 0.2)) * held + float(upkeep("deduce_per_tier", 0.1)) * maxi(0, tier - 3))

## Recipes with pages held and not yet known: the ancient ones the page offers to Deduce.
func ancient_in_progress(c) -> Array:
	var out: Array = []
	for rid in c.crafting.get("recipe_fragments", {}):
		if not knows(c, str(rid)) and ContentDB.has_entry("recipes", str(rid)): out.append(str(rid))
	return out

func deduce(c, recipe: String) -> Dictionary:
	var r := ContentDB.entry("recipes", recipe)
	if r.is_empty() or not r.has("fragments"): return fail("not_ancient")
	if knows(c, recipe): return fail("known")
	var held := pages_held(c, recipe)
	if held <= 0: return fail("no_pages", {"text": Tx.t("sim.crafting.no_pages")})
	if held < int(r.fragments):
		# Pages missing: the attempt costs one set of the recipe's ingredients, at a furnace.
		if not station_near(c, STATIONS.get(str(r.craft), [])): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "furnace"})
		for inp in r.get("inputs", []):
			if c.inventory.count(str(inp.item)) < int(inp.count): return fail("materials", {"text": Tx.t("sim.crafting.missing") % ContentDB.item_name(str(inp.item))})
		for inp in r.get("inputs", []): game.inventory.apply_remove(c.id, str(inp.item), int(inp.count), "deduce:" + recipe)
	var chance := deduce_chance(c, recipe)
	var success := chance >= 1.0 or Rng.stream(c.id, "crafting").randf() < chance
	if success: apply_learn_recipe(c.id, recipe)
	emit("recipe_deduced", {"actor": c.id, "recipe": recipe, "success": success, "chance": chance})
	return ok({"success": success, "chance": chance})

# ------------------------------------------------------------------ S44 experimentation
static func experiment_key(herbs: Array) -> String:
	var h: Array = herbs.duplicate()
	h.sort()
	return "+".join(h)

func experiment_logged(key: String) -> Dictionary:
	for e in game.account.experiments:
		if str(e.get("key", "")) == key: return e
	return {}

## Put 2-4 herbs in (one of each): a hidden recipe of exactly those herbs is learned; anything else is a Murky Pill.
## Every mix is logged for the whole account, so nobody tries the same one twice. Herbs that fight blow the furnace.
func experiment(c, herbs: Array) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "experiments"): return fail("locked", {"text": Unlocks.locked_text("experiments")})
	var picked: Array = []
	for h in herbs:
		if not picked.has(str(h)): picked.append(str(h))
	if picked.size() < 2 or picked.size() > 4: return fail("herbs", {"text": Tx.t("sim.crafting.experiment_count")})
	for h in picked:
		if str(ContentDB.item(h).get("type", "")) != "herb": return fail("herbs", {"text": Tx.t("sim.crafting.experiment_herbs_only")})
		if c.inventory.count(h) < 1: return fail("materials", {"text": Tx.t("sim.crafting.missing") % ContentDB.item_name(h)})
	if not station_near(c, STATIONS.alchemy): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "furnace"})
	var key := experiment_key(picked)
	var seen := experiment_logged(key)
	if not seen.is_empty(): return fail("tried", {"text": Tx.t("sim.crafting.experiment_tried") % experiment_result_text(seen)})
	var inputs: Array = []
	for h in picked: inputs.append({"item": h, "count": 1})
	var clash := conflict_in(inputs)
	var entry := {"key": key, "herbs": picked, "by": c.id, "result": "murky"}
	if not clash.is_empty():
		entry.result = "blast"
		game.account.experiments.append(entry)
		emit("experiment_result", {"actor": c.id, "herbs": picked, "result": "blast"})
		return blast(c, "experiment", inputs, 1, clash)
	for h in picked: game.inventory.apply_remove(c.id, h, 1, "experiment")
	var found := ""
	for r in ContentDB.all("recipes"):
		if not r.get("hidden", false): continue
		var need: Array = []
		for inp in r.get("inputs", []): need.append(str(inp.item))
		if experiment_key(need) == key:
			found = str(r.id)
			break
	if found != "":
		entry.result = "learned:" + found
		apply_learn_recipe(c.id, found)
	else:
		game.inventory.apply_add(c.id, "murky_pill", 1, "experiment")
	game.account.experiments.append(entry)
	add_xp(c, "alchemy", float(ContentDB.curve("profession_xp.craft_per_grade", 10)))
	emit("experiment_result", {"actor": c.id, "herbs": picked, "result": entry.result, "recipe": found})
	return ok({"result": entry.result, "recipe": found})

func experiment_result_text(e: Dictionary) -> String:
	var res := str(e.get("result", ""))
	if res.begins_with("learned:"): return ContentDB.name_of("recipes", res.trim_prefix("learned:"))
	return Tx.t("sim.crafting.experiment_" + res)

# ------------------------------------------------------------------ S44 the Alchemist Guild
func guild_def(craft: String) -> Dictionary:
	for g in ContentDB.all("guilds"):
		if str(g.get("craft", "")) == craft: return g
	return {}

## Your rank in a craft's guild: "" (none), then the ranks in order.
func guild_rank(c, craft: String) -> String:
	return str(c.crafting.get("guild", {}).get(craft, ""))

func guild_rank_def(craft: String, rank: String) -> Dictionary:
	for rk in guild_def(craft).get("ranks", []):
		if str(rk.id) == rank: return rk
	return {}

## The next rank to sit for, or {} when there is none left.
func next_guild_rank(c, craft: String) -> Dictionary:
	var ranks: Array = guild_def(craft).get("ranks", [])
	var have := guild_rank(c, craft)
	for i in ranks.size():
		if have == "" and i == 0: return ranks[0]
		if str(ranks[i].id) == have and i + 1 < ranks.size(): return ranks[i + 1]
	return {}

static func quality_rank(q: String) -> int:
	var order := ["flawed", "common", "fine", "superior", "perfect", "pill_grain", "pill_halo", "pill_soul"]
	return order.find(q)

func take_exam(c, craft: String, rank: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "alchemist_guild"): return fail("locked", {"text": Unlocks.locked_text("alchemist_guild")})
	var nxt := next_guild_rank(c, craft)
	if nxt.is_empty() or (rank != "" and str(nxt.id) != rank): return fail("rank", {"text": Tx.t("sim.crafting.exam_not_yours")})
	if not c.crafting.get("guild_exam", {}).is_empty(): return fail("busy", {"text": Tx.t("sim.crafting.exam_running")})
	c.crafting["guild_exam"] = {"craft": craft, "rank": str(nxt.id), "started": game.sim_time, "made": 0}
	emit("guild_exam_started", {"actor": c.id, "craft": craft, "rank": str(nxt.id), "time_s": float(nxt.time_s)})
	return ok({"rank": str(nxt.id), "time_s": float(nxt.time_s)})

## Seconds left on the exam's candle (0 when none is burning).
func exam_left(c) -> float:
	var ex: Dictionary = c.crafting.get("guild_exam", {})
	if ex.is_empty(): return 0.0
	var rk := guild_rank_def(str(ex.craft), str(ex.rank))
	return maxf(0.0, float(rk.get("time_s", 0)) - (game.sim_time - float(ex.started)))

func _on_craft_completed(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	var ex: Dictionary = c.crafting.get("guild_exam", {})
	if ex.is_empty() or str(p.get("craft", "")) != str(ex.craft): return
	var rk := guild_rank_def(str(ex.craft), str(ex.rank))
	if str(p.get("recipe", "")) != str(rk.get("recipe", "")) or exam_left(c) <= 0.0: return
	if quality_rank(str(p.get("quality", ""))) < quality_rank(str(rk.get("quality", "common"))): return
	ex.made = int(ex.made) + int(p.get("count", 1))
	if int(ex.made) >= int(rk.get("count", 1)): _pass_exam(c, str(ex.craft), rk)

func _pass_exam(c, craft: String, rk: Dictionary) -> void:
	var guild: Dictionary = c.crafting.get("guild", {})
	guild[craft] = str(rk.id)
	c.crafting["guild"] = guild
	c.crafting["guild_exam"] = {}
	game.quest.apply_flag(c.id, str(rk.get("flag", "")))
	var fx: Array = [{"kind": "grant_title", "title": str(rk.get("title", ""))}]
	fx.append_array(rk.get("rewards", []))
	game.apply_effects(c.id, fx, "guild:" + craft)
	emit("guild_rank_changed", {"actor": c.id, "craft": craft, "rank": str(rk.id), "title": str(rk.get("title", ""))})

# ------------------------------------------------------------------ S44 commissions
## The day's number (commissions refresh each morning).
static func commission_day() -> int:
	return int(floor(Clock.now_utc() / 86400.0))

## A fifth of the zone's daily income target: Level x 60 taels an hour for three hours of play (S39).
func commission_cap(c) -> int:
	var k: Dictionary = guild_def("alchemy").get("commissions", {})
	return int(float(k.get("cap_share", 0.2)) * float(k.get("income_per_level_hour", 60)) * float(k.get("play_hours", 3)) * ProgressionRules.level(c))

func commission_paid_today(c) -> int:
	var cm: Dictionary = c.crafting.get("commission_state", {})
	return int(cm.get("paid", 0)) if int(cm.get("day", -1)) == commission_day() else 0

## Today's three orders, drawn from the pills this character knows how to refine (the guild's board).
func commissions(c) -> Array:
	var rank := guild_rank(c, "alchemy")
	if rank == "": return []
	var day := commission_day()
	var cm: Dictionary = c.crafting.get("commission_state", {})
	if int(cm.get("day", -1)) == day: return cm.get("orders", [])
	var k: Dictionary = guild_def("alchemy").get("commissions", {})
	var known: Array = []
	for r in ContentDB.all("recipes"):
		if str(r.craft) == "alchemy" and knows(c, str(r.id)) and ContentDB.item(str(r.outputs[0].item)).has("pill"): known.append(str(r.id))
	known.sort()
	var rng := Rng.stream(c.id, "commission")   # drawn once each morning; the orders are kept for the day
	var orders: Array = []
	var mult := float(guild_rank_def("alchemy", rank).get("pay_mult", 1.2))
	for i in int(k.get("per_day", 3)):
		if known.is_empty(): break
		var rid: String = known[rng.randi_range(0, known.size() - 1)]
		var item := str(ContentDB.entry("recipes", rid).outputs[0].item)
		var cnt: Array = k.get("count", [1, 3])
		var n := rng.randi_range(int(cnt[0]), int(cnt[1]))
		orders.append({"id": "c%d_%d" % [day, i], "item": item, "count": n, "quality": "common",
			"pay": int(round(LootRules.buy_price(item) * mult * n)), "accepted": false, "done": false})
	c.crafting["commission_state"] = {"day": day, "orders": orders, "paid": 0}
	return orders

func _order(c, id: String) -> Dictionary:
	for o in commissions(c):
		if str(o.id) == id: return o
	return {}

func accept_commission(c, id: String) -> Dictionary:
	var o := _order(c, id)
	if o.is_empty() or o.get("done", false): return fail("no_order")
	o.accepted = true
	return ok()

func deliver_commission(c, id: String, pay: String) -> Dictionary:
	var o := _order(c, id)
	if o.is_empty() or o.get("done", false): return fail("no_order")
	if not o.get("accepted", false): return fail("not_accepted", {"text": Tx.t("sim.crafting.commission_accept_first")})
	# Pills of the order's quality or better, from any stacks.
	var have := 0
	for s in c.inventory.bag:
		if s != null and str(s.id) == str(o.item) and quality_rank(str(s.get("quality", "common"))) >= quality_rank(str(o.quality)): have += int(s.count)
	if have < int(o.count): return fail("materials", {"text": Tx.t("sim.crafting.missing") % ContentDB.item_name(str(o.item))})
	var left := int(o.count)
	for i in c.inventory.bag.size():
		if left <= 0: break
		var s = c.inventory.bag[i]
		if s == null or str(s.id) != str(o.item) or quality_rank(str(s.get("quality", "common"))) < quality_rank(str(o.quality)): continue
		var take := mini(left, int(s.count))
		game.inventory.apply_remove_index(c.id, i, take, "commission")
		left -= take
	o.done = true
	var room := maxi(0, commission_cap(c) - commission_paid_today(c))
	var paid := mini(int(o.pay), room)
	var cm: Dictionary = c.crafting.get("commission_state", {})
	cm.paid = commission_paid_today(c) + paid
	var k: Dictionary = guild_def("alchemy").get("commissions", {})
	if pay == "contribution":
		var contrib := int(round(paid * float(k.get("contribution_per_tael", 0.1))))
		if contrib > 0: game.apply_effects(c.id, [{"kind": "add_contribution", "amount": contrib}], "commission")
	elif paid > 0:
		game.economy.apply_currency("silver_tael", paid, "commission")
	emit("commission_completed", {"actor": c.id, "id": id, "item": str(o.item), "count": int(o.count), "paid": paid, "pay": pay, "capped": paid < int(o.pay)})
	return ok({"paid": paid, "capped": paid < int(o.pay)})

func tick(_delta: float) -> void:
	# S44: a guild exam whose candle burns out fails.
	var ac = game.active()
	if ac != null and not ac.crafting.get("guild_exam", {}).is_empty() and exam_left(ac) <= 0.0:
		var ex: Dictionary = ac.crafting.guild_exam
		ac.crafting["guild_exam"] = {}
		emit("guild_exam_failed", {"actor": ac.id, "craft": str(ex.craft), "rank": str(ex.rank), "made": int(ex.made)})
	pass
