class_name CraftingResearch
extends CraftingPart
## CraftingAuthority's part: ancient recipes, found a page at a time and Deduced (S44), and experiments with herbs,
## logged for the whole account.

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
	if held.size() >= int(r.get("fragments", 1)) and not crafting.knows(c, recipe):
		crafting.apply_learn_recipe(c.id, recipe)
		emit("recipe_deduced", {"actor": c.id, "recipe": recipe, "success": true, "whole": true})

func pages_held(c, recipe: String) -> int:
	return (c.crafting.get("recipe_fragments", {}).get(recipe, []) as Array).size()

## Deduce with pages missing (S44): 20% a page held + 10% a tier of the Alchemy Dao above the third, never above 95%.
func deduce_chance(c, recipe: String) -> float:
	var r := ContentDB.entry("recipes", recipe)
	var held := pages_held(c, recipe)
	if held >= int(r.get("fragments", 1)): return 1.0
	var tier := int(c.cultivator.daos.get("alchemy", {}).get("tier", 0))
	return minf(float(crafting.upkeep("deduce_cap", 0.95)), float(crafting.upkeep("deduce_per_page", 0.2)) * held + float(crafting.upkeep("deduce_per_tier", 0.1)) * maxi(0, tier - 3))

## Recipes with pages held and not yet known: the ancient ones the page offers to Deduce.
func ancient_in_progress(c) -> Array:
	var out: Array = []
	for rid in c.crafting.get("recipe_fragments", {}):
		if not crafting.knows(c, str(rid)) and ContentDB.has_entry("recipes", str(rid)): out.append(str(rid))
	return out

func deduce(c, recipe: String) -> Dictionary:
	var r := ContentDB.entry("recipes", recipe)
	if r.is_empty() or not r.has("fragments"): return fail("not_ancient")
	if crafting.knows(c, recipe): return fail("known")
	var held := pages_held(c, recipe)
	if held <= 0: return fail("no_pages", {"text": Tx.t("sim.crafting.no_pages")})
	if held < int(r.fragments):
		# Pages missing: the attempt costs one set of the recipe's ingredients, at a furnace.
		if not crafting.station_near(c, CraftingAuthority.STATIONS.get(str(r.craft), [])): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "furnace"})
		for inp in r.get("inputs", []):
			if c.inventory.count(str(inp.item)) < int(inp.count): return fail("materials", {"text": Tx.t("sim.crafting.missing") % ContentDB.item_name(str(inp.item))})
		for inp in r.get("inputs", []): game.inventory.apply_remove(c.id, str(inp.item), int(inp.count), "deduce:" + recipe)
	var chance := deduce_chance(c, recipe)
	var success := chance >= 1.0 or Rng.stream(c.id, "crafting").randf() < chance
	if success: crafting.apply_learn_recipe(c.id, recipe)
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
	if not crafting.station_near(c, CraftingAuthority.STATIONS.alchemy): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "furnace"})
	var key := experiment_key(picked)
	var seen := experiment_logged(key)
	if not seen.is_empty(): return fail("tried", {"text": Tx.t("sim.crafting.experiment_tried") % experiment_result_text(seen)})
	var inputs: Array = []
	for h in picked: inputs.append({"item": h, "count": 1})
	var clash := crafting.conflict_in(inputs)
	var entry := {"key": key, "herbs": picked, "by": c.id, "result": "murky"}
	if not clash.is_empty():
		entry.result = "blast"
		game.account.experiments.append(entry)
		emit("experiment_result", {"actor": c.id, "herbs": picked, "result": "blast"})
		return crafting.blast(c, "experiment", inputs, 1, clash)
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
		crafting.apply_learn_recipe(c.id, found)
	else:
		game.inventory.apply_add(c.id, "murky_pill", 1, "experiment")
	game.account.experiments.append(entry)
	crafting.add_xp(c, "alchemy", float(ContentDB.curve("profession_xp.craft_per_grade", 10)))
	emit("experiment_result", {"actor": c.id, "herbs": picked, "result": entry.result, "recipe": found})
	return ok({"result": entry.result, "recipe": found})

func experiment_result_text(e: Dictionary) -> String:
	var res := str(e.get("result", ""))
	if res.begins_with("learned:"): return ContentDB.name_of("recipes", res.trim_prefix("learned:"))
	return Tx.t("sim.crafting.experiment_" + res)
