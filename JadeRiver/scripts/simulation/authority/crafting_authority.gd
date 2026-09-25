class_name CraftingAuthority
extends Authority
## S15/S16/S33 · Recipes known, profession ranks, gathering and mining nodes,
## fishing, cooking, alchemy (five-screen mini-game scores), the forge and the
## auto-refine queue. One crafting framework: validate inputs, consume, roll quality
## with the `crafting` stream, grant output and profession XP, emit craft_completed.

var pending: Dictionary = {}   # actor -> {object, kind, started, channel}

const NODE_CRAFT := {"herb_patch": "herb_gathering", "ore_vein": "mining", "fishing_spot": "fishing"}
const RANK_CAPS := {
	"herb_gathering": [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"]],
	"mining": [["qi_unfurling_1", "adept"], ["spirit_awakening_1", "expert"], ["sage_sovereign_1", "master"]],
	"cooking": [["qi_kindling_1", "adept"], ["heart_tempering_1", "expert"], ["heaven_glimpse_1", "master"]],
	"fishing": [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"]],
	"alchemy": [["qi_unfurling_1", "adept"], ["cloud_stride_1", "expert"], ["heaven_glimpse_1", "master"]],
	"smithing": [["qi_unfurling_1", "adept"], ["cloud_stride_1", "expert"], ["heaven_glimpse_1", "master"]],
}
const GRADE_CAP := [["qi_kindling_1", "common"], ["qi_unfurling_1", "earth"], ["cloud_stride_1", "heaven"], ["heaven_glimpse_1", "mystic"]]

func intents() -> Array:
	return ["complete_node", "catch_fish", "cook", "refine", "queue_auto_refine", "collect_auto_refine", "forge", "enhance", "salvage_item"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"complete_node": return complete_node(c, str(intent.get("object", "")))
		"catch_fish": return catch_fish(c, str(intent.get("object", "")), intent.get("result", {}))
		"cook": return craft(c, str(intent.get("recipe", "")), maxi(1, int(intent.get("count", 1))), [], "cooking")
		"refine": return craft(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10), intent.get("scores", []), "alchemy")
		"forge": return craft(c, str(intent.get("recipe", "")), 1, intent.get("scores", []), "smithing")
		"queue_auto_refine": return queue_auto(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10))
		"collect_auto_refine": return collect_auto(c)
		"enhance": return enhance(c, int(intent.get("index", -1)), str(intent.get("slot", "")))
		"salvage_item": return salvage(c, int(intent.get("index", -1)))
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
	var tool_craft = {"herb_gathering": "gathering", "mining": "mining", "fishing": "fishing"}[craft]
	if craft != "herb_gathering" and tool_power(c, tool_craft) <= 0.0: return fail("no_tool", {"text": "You need a %s" % {"mining": "pickaxe", "fishing": "fishing rod"}[craft]})
	var need_rank := str(o.get("rank", "apprentice"))
	if rank_index(rank_of(c, craft)) < rank_index(need_rank): return fail("rank", {"text": "Needs %s %s" % [craft.replace("_", " ").capitalize(), need_rank.capitalize()]})
	var channel = {"herb_patch": 1.5, "ore_vein": 2.4, "fishing_spot": 0.0}[str(o.type)]
	pending[c.id] = {"object": str(o.id), "kind": str(o.type), "started": game.sim_time, "channel": channel}
	emit("node_action_started", {"actor": c.id, "object": o.id, "kind": o.type, "channel": channel})
	return ok({"channel": channel, "minigame": "fishing" if o.type == "fishing_spot" else "", "action": {"herb_patch": "gather", "ore_vein": "mine", "fishing_spot": "fish"}[str(o.type)]})

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
	var power := maxf(1.0, tool_power(c, "gathering" if craft == "herb_gathering" else "mining"))
	var count := rng.randi_range(int(y[0]), int(y[1]))
	if rng.randf() < (power - 1.0) * 0.5: count += 1
	if game.pets.gatherer_active(c.id) and rng.randf() < 0.25: count += 1
	var item := str(o.get("item", ""))
	game.inventory.apply_add(c.id, item, count, craft)
	st.state = "depleted"
	st.timer = float(o.get("regrow_s", 300))
	rt.objects[object_id] = st
	var mem: Dictionary = c.rooms.get(rt.room_id, {"nodes": {}, "opened": {}, "broken": {}})
	mem.nodes[object_id] = Clock.now_utc() + float(st.timer)
	c.rooms[rt.room_id] = mem
	add_xp(c, craft, float(ContentDB.curve("profession_xp.%s" % ("mine" if craft == "mining" else "gather"), 5)))
	emit("node_gathered", {"actor": c.id, "object": object_id, "item": item, "count": count, "craft": craft})
	emit("node_depleted", {"room": rt.room_id, "object": object_id})
	return ok({"item": item, "count": count})

## Fishing result from the mini-game (S33). The authority rolls the catch.
func catch_fish(c, object_id: String, result: Dictionary) -> Dictionary:
	var p: Dictionary = pending.get(c.id, {})
	if p.is_empty() or str(p.object) != object_id: return fail("not_started")
	pending.erase(c.id)
	var reaction := float(result.get("reaction_s", 9.9))
	var tension_ok := bool(result.get("tension_ok", false))
	if reaction > 0.6 + 0.1 * (tool_power(c, "fishing") - 1.0) or reaction < 0.05 or not tension_ok:
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

func recipe_check(c, recipe_id: String, count: int, craft: String) -> String:
	var r := ContentDB.entry("recipes", recipe_id)
	if r.is_empty() or str(r.craft) != craft: return "Unknown recipe"
	if not Unlocks.is_unlocked(c.id, craft): return Unlocks.locked_text(craft)
	if not knows(c, recipe_id): return "You have not learned this recipe"
	var station = {"cooking": ["cooking_pot"], "alchemy": ["alchemy_furnace"], "smithing": ["forge_anvil"]}.get(craft, [])
	if not station.is_empty() and not station_near(c, station): return "You need a %s" % ["cooking pot", "furnace", "forge"][["cooking", "alchemy", "smithing"].find(craft)]
	var grade := str(r.get("grade", "plain"))
	if craft in ["alchemy", "smithing"] and StatRules.grade_index(grade) > StatRules.grade_index(grade_cap(c)): return "Your realm cannot refine %s grade yet" % grade.capitalize()
	for inp in r.get("inputs", []):
		if c.inventory.count(str(inp.item)) < int(inp.count) * count: return "Missing %s" % ContentDB.item_name(str(inp.item))
	return ""

func craft(c, recipe_id: String, count: int, scores: Array, craft_kind: String) -> Dictionary:
	var why := recipe_check(c, recipe_id, count, craft_kind)
	if why != "": return fail("cannot_craft", {"text": why})
	var r := ContentDB.entry("recipes", recipe_id)
	var rng := Rng.stream(c.id, "crafting")
	var quality := "common"
	if craft_kind in ["alchemy", "smithing"]:
		var total := 0.0
		for s in scores: total += clampf(float(s), 0.0, 1.0)
		var avg := total / maxf(1.0, scores.size()) if not scores.is_empty() else 0.6
		avg += c.stats.value("crafting_control") * 0.2 + 0.05 * int(c.cultivator.daos.get("alchemy" if craft_kind == "alchemy" else "refining", {}).get("tier", 0))
		var roll := avg + rng.randf_range(-0.08, 0.08)
		quality = "flawed" if roll < 0.35 else ("common" if roll < 0.6 else ("fine" if roll < 0.78 else ("superior" if roll < 0.9 else "perfect")))
	for inp in r.get("inputs", []): game.inventory.apply_remove(c.id, str(inp.item), int(inp.count) * count, "craft:" + recipe_id)
	var produced := 0
	for out in r.get("outputs", []):
		var n := int(out.count) * count
		if craft_kind == "cooking" and rng.randf() < c.stats.value("insight") * 0.002: n += int(out.count)
		if craft_kind == "smithing" and ContentDB.is_equipment(str(out.item)):
			var def := ContentDB.item(str(out.item))
			for i in n:
				var inst := LootRules.make_instance(str(out.item), int(def.get("ilv", 1)), quality, Rng.stream(c.id, "affix"), c.inventory.next_uid)
				c.inventory.next_uid += 1
				game.inventory.apply_add_instance(c.id, inst, "forge")
		elif craft_kind == "alchemy" and quality == "flawed":
			game.inventory.apply_add(c.id, str(out.item), maxi(1, n / 2), "craft")
		else:
			game.inventory.apply_add(c.id, str(out.item), n, "craft")
		produced += n
	var xp := float(ContentDB.curve("profession_xp.craft_per_grade", 10)) * (StatRules.grade_index(str(r.get("grade", "plain"))) + 1) * count
	if craft_kind == "cooking": xp = float(ContentDB.curve("profession_xp.cook", 6)) * count
	if quality in ["fine", "superior", "perfect"]: xp *= 1.5
	add_xp(c, craft_kind, xp)
	if craft_kind == "alchemy": game.progression.apply_insight(c.id, "alchemy", 3.0 * count, "craft:" + recipe_id)
	if craft_kind == "smithing": game.progression.apply_insight(c.id, "refining", 3.0, "craft:" + recipe_id)
	emit("craft_completed", {"actor": c.id, "recipe": recipe_id, "craft": craft_kind, "quality": quality, "count": produced})
	return ok({"quality": quality, "count": produced})

func queue_auto(c, recipe_id: String, count: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "auto_refine"): return fail("locked")
	if c.crafting.auto_queue.size() >= 5: return fail("queue_full")
	var why := recipe_check(c, recipe_id, count, "alchemy")
	if why != "": return fail("cannot_craft", {"text": why})
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
			emit("craft_completed", {"actor": c.id, "recipe": q.recipe, "craft": "alchemy", "quality": "common", "count": q.count, "auto": true})
	if got == 0: return fail("not_ready", {"text": "No batch is finished yet."})
	emit("system_used", {"actor": c.id, "system": "auto_refine_collected"})
	return ok({"batches": got})

func enhance(c, index: int, slot: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var inst = c.inventory.equipped.get(slot) if slot != "" else (c.inventory.bag[index] if index >= 0 and index < c.inventory.bag.size() else null)
	if inst == null or not ContentDB.is_equipment(str(inst.id)): return fail("not_equipment")
	var lvl := int(inst.get("enhance", 0))
	if lvl >= 10: return fail("max")
	var def := ContentDB.item(str(inst.id))
	var metal = {"plain": "copper_ore", "common": "copper_ore", "earth": "jadeiron", "heaven": "cloudsteel_ore", "mystic": "mystic_ore"}.get(str(def.get("grade", "plain")), "copper_ore")
	var need := 2 * (lvl + 1)
	if c.inventory.count(metal) < need: return fail("materials", {"text": "Needs %d %s" % [need, ContentDB.item_name(metal)]})
	var taels := 20 * (lvl + 1) * (StatRules.grade_index(str(def.get("grade", "plain"))) + 1)
	if game.economy.balance("silver_tael") < taels: return fail("insufficient_funds")
	if lvl >= 5 and c.inventory.count("spirit_stone_shard") < lvl - 4: return fail("materials", {"text": "Needs Spirit Stone shards"})
	game.inventory.apply_remove(c.id, metal, need, "enhance")
	game.economy.apply_currency("silver_tael", -taels, "enhance")
	var success := true
	if lvl >= 5:
		game.inventory.apply_remove(c.id, "spirit_stone_shard", lvl - 4, "enhance")
		success = Rng.stream(c.id, "crafting").randf() < 1.0 - 0.12 * (lvl - 4)
	if success:
		inst.enhance = lvl + 1
		if slot != "": emit("equipment_changed", {"actor": c.id, "slot": slot, "old": inst.id, "new": inst.id})
	emit("item_enhanced", {"actor": c.id, "item": inst.id, "level": int(inst.get("enhance", 0)), "success": success})
	return ok({"success": success, "level": int(inst.get("enhance", 0))})

func salvage(c, index: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var inst: Dictionary = c.inventory.bag[index]
	if not ContentDB.is_equipment(str(inst.id)) or inst.get("bound", false) or c.inventory.locked.has(int(inst.get("uid", -1))): return fail("cannot_salvage")
	var def := ContentDB.item(str(inst.id))
	var metal = {"plain": "copper_ore", "common": "copper_ore", "earth": "jadeiron", "heaven": "cloudsteel_ore", "mystic": "mystic_ore"}.get(str(def.get("grade", "plain")), "copper_ore")
	game.inventory.apply_remove_index(c.id, index, 1, "salvage")
	var n := maxi(1, int(round(6 * Rng.stream(c.id, "crafting").randf_range(0.2, 0.35))))
	game.inventory.apply_add(c.id, metal, n, "salvage")
	emit("item_salvaged", {"actor": c.id, "item": inst.id, "returned": n})
	return ok({"returned": n})

func tick(_delta: float) -> void:
	pass
