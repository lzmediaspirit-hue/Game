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
	"herb_gathering": [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"]],
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
		"trace_talisman", "restore_relic", "mend_furnace"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"complete_node": return complete_node(c, str(intent.get("object", "")))
		"catch_fish": return catch_fish(c, str(intent.get("object", "")), intent.get("result", {}))
		"cook": return craft(c, str(intent.get("recipe", "")), maxi(1, int(intent.get("count", 1))), [], "cooking")
		"craft_step": return craft_step(c, str(intent.get("recipe", "")), str(intent.get("craft", "alchemy")), float(intent.get("offset", 1.0)),
			str(intent.get("fire", "charcoal")))
		"refine": return craft(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10), _take_steps(c, str(intent.get("recipe", ""))), "alchemy",
			str(intent.get("fire", "charcoal")), intent.get("substitute", {}) if intent.get("substitute", {}) is Dictionary else {})
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
	var channel = {"herb_patch": 1.5, "ore_vein": 2.4, "fishing_spot": 0.0, "star_sight": 3.0}[str(o.type)]
	pending[c.id] = {"object": str(o.id), "kind": str(o.type), "started": game.sim_time, "channel": channel}
	emit("node_action_started", {"actor": c.id, "object": o.id, "kind": o.type, "channel": channel})
	return ok({"channel": channel, "minigame": "fishing" if o.type == "fishing_spot" else "",
		"action": {"herb_patch": "gather", "ore_vein": "mine", "fishing_spot": "fish", "star_sight": "gather"}[str(o.type)]})

func complete_node(c, object_id: String) -> Dictionary:
	var p: Dictionary = pending.get(c.id, {})
	if p.is_empty() or str(p.object) != object_id: return fail("not_started")
	if game.sim_time - float(p.started) < float(p.channel) - 0.15: return fail("too_early")
	pending.erase(c.id)
	var rt: RoomRuntime = game.room_rt
	var o := rt.object_def(object_id)
	var st: Dictionary = rt.objects.get(object_id, {"state": "ready"})
	if st.get("state", "ready") != "ready": return fail("depleted")
	var craft: String = NODE_CRAFT[str(o.type)]
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
	var grade := str(r.get("grade", "plain"))
	if craft in ["alchemy", "smithing"] and StatRules.grade_index(grade) > StatRules.grade_index(grade_cap(c)): return Tx.t("sim.crafting.your_realm_cannot_refine_grade") % grade.capitalize()
	for inp in (inputs if not inputs.is_empty() else r.get("inputs", [])):
		if c.inventory.count(str(inp.item)) < int(inp.count) * count: return Tx.t("sim.crafting.missing") % ContentDB.item_name(str(inp.item))
	return ""

## One strike of the alchemy or forge mini-game: `offset` is how far from the band centre
## it landed (0 = dead centre). Scored here, so the craft uses only what Crafting measured.
func craft_step(c, recipe_id: String, craft_kind: String, offset: float, fire := "charcoal") -> Dictionary:
	if not craft_kind in ["alchemy", "smithing"] or not ContentDB.has_entry("recipes", recipe_id): return fail("bad_step")
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

func craft(c, recipe_id: String, count: int, scores: Array, craft_kind: String, fire := "charcoal", substitute: Dictionary = {}) -> Dictionary:
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
	var why := recipe_check(c, recipe_id, count, craft_kind, inputs)
	if why != "": return fail("cannot_craft", {"text": why})
	var r := ContentDB.entry("recipes", recipe_id)
	# Herbs that fight each other blow the furnace (S44): the batch is lost.
	if craft_kind == "alchemy":
		var clash := conflict_in(inputs)
		if not clash.is_empty(): return blast(c, recipe_id, inputs, count, clash)
	var rng := Rng.stream(c.id, "crafting")
	var quality := "common"
	if craft_kind in ["alchemy", "smithing", "talisman"]:
		var avg := quality_score(c, craft_kind, furnace, r, scores)
		var roll := avg + rng.randf_range(-0.08, 0.08)
		quality = "flawed" if roll < 0.35 else ("common" if roll < 0.6 else ("fine" if roll < 0.78 else ("superior" if roll < 0.9 else "perfect")))
		if craft_kind == "alchemy" and quality == "perfect": quality = _rare_pill_quality(c, scores, rng, rare_allowed(furnace, fire))
	for inp in inputs: game.inventory.apply_remove(c.id, str(inp.item), int(inp.count) * count, "craft:" + recipe_id)
	if craft_kind == "alchemy" and fire == "beast_fire": game.inventory.apply_remove(c.id, _core_to_burn(c), 1, "beast_fire")
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

func tick(_delta: float) -> void:
	pass
