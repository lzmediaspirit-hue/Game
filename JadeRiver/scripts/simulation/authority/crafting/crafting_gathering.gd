class_name CraftingGathering
extends CraftingPart
## CraftingAuthority's part: gathering, mining, star-sight and insect nodes (S33), the harvest tap on a herb (S45) and
## fishing's catch.

# ------------------------------------------------------------------ gathering, mining, fishing
func gather(c, o: Dictionary) -> Dictionary:
	var craft: String = CraftingAuthority.NODE_CRAFT.get(str(o.type), "")
	if not Unlocks.is_unlocked(c.id, craft): return fail("locked", {"text": Unlocks.locked_text(craft)})
	if craft in ["mining", "fishing"] and crafting.tool_power(c, craft) <= 0.0: return fail("no_tool", {"text": Tx.t("sim.crafting.you_need_a") % {"mining": Tx.t("sim.crafting.pickaxe"), "fishing": Tx.t("sim.crafting.fishing_rod")}[craft]})
	var need_rank := str(o.get("rank", "apprentice"))
	if crafting.rank_index(crafting.rank_of(c, craft)) < crafting.rank_index(need_rank): return fail("rank", {"text": Tx.t("sim.crafting.needs") % [craft.replace("_", " ").capitalize(), need_rank.capitalize()]})
	# S45: a ripe rare herb may have a keeper.
	var guard: String = game.world.herb_guard_text(c, o) if o.type == "herb_patch" else ""
	if guard != "": return fail("guarded", {"text": guard})
	var channel = {"herb_patch": 1.5, "ore_vein": 2.4, "fishing_spot": 0.0, "star_sight": 3.0, "insect_swarm": 1.2}[str(o.type)]
	crafting.pending[c.id] = {"object": str(o.id), "kind": str(o.type), "started": game.sim_time, "channel": channel}
	emit("node_action_started", {"actor": c.id, "object": o.id, "kind": o.type, "channel": channel})
	var out := {"channel": channel, "minigame": "fishing" if o.type == "fishing_spot" else "",
		"action": {"herb_patch": "gather", "ore_vein": "mine", "fishing_spot": "fish", "star_sight": "gather", "insect_swarm": "gather"}[str(o.type)]}
	# S45 harvest tap: the hold ends in a shrinking ring; the window widens with gathering rank.
	if o.type == "herb_patch":
		var h: Dictionary = ContentDB.config("garden").get("harvest", {})
		out.tap = {"ring_s": float(h.get("ring_s", 1.0)), "target": float(h.get("target", 0.7)), "window": HerbRules.tap_window(crafting.rank_of(c, craft))}
		if o.has("ripen"): out.early = not bool(HerbRules.ripen_state(o, Clock.now_utc()).ripe)
	return ok(out)

## `timing` (S45 herbs): how far the harvest ring had shrunk when the tap landed, 0..1 (-1: no tap, a miss).
func complete_node(c, object_id: String, timing := -1.0) -> Dictionary:
	var p: Dictionary = crafting.pending.get(c.id, {})
	if p.is_empty() or str(p.object) != object_id: return fail("not_started")
	if game.sim_time - float(p.started) < float(p.channel) - 0.15: return fail("too_early")
	crafting.pending.erase(c.id)
	var rt: RoomRuntime = game.room_rt
	var o := rt.object_def(object_id)
	var st: Dictionary = rt.objects.get(object_id, {"state": "ready"})
	if st.get("state", "ready") != "ready": return fail("depleted")
	var craft: String = CraftingAuthority.NODE_CRAFT[str(o.type)]
	if craft == "herb_gathering": return _harvest(c, o, timing)
	var rng := Rng.stream(c.id, "crafting")
	var power := 1.0 if craft == "star_charting" else maxf(1.0, crafting.tool_power(c, {"herb_gathering": "gathering", "insect_netting": "insect_netting"}.get(craft, "mining")))
	var count := _node_yield(c, o, rng, power, craft != "star_charting")
	var item := str(o.get("item", ""))
	if o.has("outputs"): item = str(Rng.weighted(rng, o.outputs).get("item", item))   # V10: a swarm's insects by weight
	game.inventory.apply_add(c.id, item, count, craft)
	game.world.apply_node_depleted(c, object_id, float(o.get("regrow_s", 300)))
	crafting.add_xp(c, craft, float(ContentDB.curve("profession_xp.%s" % {"mining": "mine", "star_charting": "observe"}.get(craft, "gather"), 5)))
	game.posts.apply_hand_harvest(c.id, item, count)   # S50: the hand trains the post craft too
	emit("node_gathered", {"actor": c.id, "object": object_id, "item": item, "count": count, "craft": craft})
	return ok({"item": item, "count": count})

## A node's haul: its yield roll, one more on a better tool's chance, and one more on a gathering animal's (none under
## the stars).
func _node_yield(c, o: Dictionary, rng: RandomNumberGenerator, power: float, animal: bool) -> int:
	var y: Array = o.get("yield", [1, 2])
	var count := rng.randi_range(int(y[0]), int(y[1]))
	if rng.randf() < (power - 1.0) * 0.5: count += 1
	if animal and game.pets.gatherer_active(c.id) and rng.randf() < 0.25: count += 1
	return count

## S45 harvest: a perfect tap keeps the herb's full age and may find a seed; a miss drops one age tier, and so does
## picking a rare herb before it ripens (never below ten years). A rare node grows back with its next ripening.
func _harvest(c, o: Dictionary, timing: float) -> Dictionary:
	var guard: String = game.world.herb_guard_text(c, o)
	if guard != "": return fail("guarded", {"text": guard})
	var rng := Rng.stream(c.id, "crafting")
	var object_id := str(o.id)
	var now := Clock.now_utc()
	var early: bool = o.has("ripen") and not bool(HerbRules.ripen_state(o, now).ripe)
	var perfect := HerbRules.tap_perfect(timing, crafting.rank_of(c, "herb_gathering"))
	var item := HerbRules.aged_down(str(o.get("item", "")), (1 if early else 0) + (0 if perfect else 1))
	var count := _node_yield(c, o, rng, maxf(1.0, crafting.tool_power(c, "gathering")), true)
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
	crafting.add_xp(c, "herb_gathering", float(ContentDB.curve("profession_xp.gather", 5)) * (1.5 if perfect else 1.0))
	game.posts.apply_hand_harvest(c.id, item, count)
	emit("node_gathered", {"actor": c.id, "object": object_id, "item": item, "count": count, "craft": "herb_gathering"})
	emit("herb_harvested", {"actor": c.id, "object": object_id, "item": item, "age": HerbRules.item_age(item), "perfect": perfect, "early": early})
	if seed != "": emit("seed_found", {"actor": c.id, "seed": seed, "object": object_id})
	return ok({"item": item, "count": count, "perfect": perfect, "early": early, "age": HerbRules.item_age(item), "seed": seed})

## Fishing result from the mini-game (S33). The authority rolls the catch.
func catch_fish(c, object_id: String, result: Dictionary) -> Dictionary:
	var p: Dictionary = crafting.pending.get(c.id, {})
	if p.is_empty() or str(p.object) != object_id: return fail("not_started")
	crafting.pending.erase(c.id)
	var reaction := float(result.get("reaction_s", 9.9))
	var tension_ok := bool(result.get("tension_ok", false))
	var window: float = (0.6 + 0.1 * (crafting.tool_power(c, "fishing") - 1.0)) * (1.0 + game.pets.trait_bonus(c, "fish_chance") + game.calendar.fishing_bonus())
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
	crafting.add_xp(c, "fishing", float(ContentDB.curve("profession_xp.fish", 8)))
	game.posts.apply_hand_harvest(c.id, str(fish.item), 1)
	emit("fish_caught", {"actor": c.id, "fish": fish.item, "item": fish.item, "room": game.room_rt.room_id})
	return ok({"caught": true, "item": fish.item})
