class_name CraftingRecipes
extends CraftingPart
## CraftingAuthority's part: the recipes known and the check before a craft, older herbs standing in, the strikes of the
## forge's and the simple furnace's mini-game, the craft itself (its quality roll, what it takes and what it gives), the
## auto-refine queue and tracing a talisman (S47).

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

## `anywhere` (decision 43): the station rule is lifted (the Crafts queue once its remote access is earned).
func recipe_check(c, recipe_id: String, count: int, craft: String, inputs: Array = [], anywhere := false) -> String:
	var r := ContentDB.entry("recipes", recipe_id)
	if r.is_empty() or str(r.craft) != craft: return Tx.t("sim.crafting.unknown_recipe")
	if not Unlocks.is_unlocked(c.id, craft): return Unlocks.locked_text(craft)
	if not knows(c, recipe_id): return Tx.t("sim.crafting.you_have_not_learned_this")
	var station: Array = CraftingAuthority.STATIONS.get(craft, [])
	if not station.is_empty() and not anywhere and not crafting.station_near(c, station):
		return Tx.t("sim.crafting.you_need_a") % [Tx.t("sim.crafting.cooking_pot"), "furnace", "forge", Tx.t("sim.crafting.chart_table"),
			Tx.t("sim.crafting.slipway")][["cooking", "alchemy", "smithing", "star_charting", "shipwright"].find(craft)]
	# A vessel needs a smith's hand and a formation master's plates (S16).
	var ranks: Dictionary = r.get("requires_ranks", {})
	for rc in ranks:
		if crafting.rank_index(crafting.rank_of(c, str(rc))) < crafting.rank_index(str(ranks[rc])):
			return Tx.t("sim.crafting.needs") % [str(rc).replace("_", " ").capitalize(), str(ranks[rc]).capitalize()]
	if r.has("rank") and crafting.rank_index(crafting.rank_of(c, craft)) < crafting.rank_index(str(r.rank)):
		return Tx.t("sim.crafting.needs") % [craft.replace("_", " ").capitalize(), str(r.rank).capitalize()]
	if str(r.get("fire", "")) != "" and not str(r.fire) in crafting.fires_available(c): return Tx.t("sim.crafting.needs_fire") % Tx.t("ui.crafts.fire_" + str(r.fire))
	var grade := str(r.get("grade", "plain"))
	if craft in ["alchemy", "smithing"] and StatRules.grade_index(grade) > StatRules.grade_index(crafting.grade_cap(c)): return Tx.t("sim.crafting.your_realm_cannot_refine_grade") % grade.capitalize()
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
	crafting.furnaces.settle_tribulation(c)
	var k: Dictionary = ContentDB.curve("craft_step", {})
	var session: Dictionary = crafting.steps.get(c.id, {})
	if str(session.get("recipe", "")) != recipe_id or (session.get("scores", []) as Array).size() >= steps_for(recipe_id):
		session = {"recipe": recipe_id, "craft": craft_kind, "scores": [], "fire": fire if craft_kind == "alchemy" and fire in crafting.fires_available(c) else "charcoal"}
	var tolerance := float(k.get("tolerance", 0.3)) * (crafting.band_mult(c, str(session.get("fire", "charcoal"))) if craft_kind == "alchemy" else 1.0)
	var score := clampf(1.0 - absf(offset) / tolerance, 0.0, 1.0)
	session.scores.append(score)
	crafting.steps[c.id] = session
	var grade := CraftingRefine.step_grade(score)
	emit("craft_step_result", {"actor": c.id, "recipe": recipe_id, "step": session.scores.size(), "score": score, "grade": grade})
	return ok({"score": score, "grade": grade, "step": session.scores.size()})

## How many strikes a recipe takes: a liquid has no Condensation (S44), so two.
func steps_for(recipe_id: String) -> int:
	var n := int(ContentDB.curve("craft_step", {}).get("steps", 3))
	return n - 1 if ContentDB.entry("recipes", recipe_id).get("liquid", false) else n

func take_steps(c, recipe_id: String) -> Array:
	var session: Dictionary = crafting.steps.get(c.id, {})
	crafting.steps.erase(c.id)
	return session.get("scores", []) if str(session.get("recipe", "")) == recipe_id else []

func craft(c, recipe_id: String, count: int, scores: Array, craft_kind: String, fire := "charcoal", substitute: Dictionary = {}, live := false) -> Dictionary:
	crafting.furnaces.settle_tribulation(c)
	var furnace := crafting.furnace_of(c) if craft_kind == "alchemy" else {}
	# S44: an Alchemy Dao tier-5 substitute swaps one herb for another of the same nature and role.
	var inputs: Array = ContentDB.entry("recipes", recipe_id).get("inputs", [])
	if craft_kind == "alchemy" and not substitute.is_empty():
		var sw := crafting.substitute_check(c, recipe_id, str(substitute.get("from", "")), str(substitute.get("to", "")))
		if sw != "": return fail("substitute", {"text": sw})
		inputs = crafting.inputs_with(recipe_id, substitute)
	if craft_kind == "alchemy":
		# The furnace sets the batch (G1); the fire must be one you have here.
		if furnace.get("cracked", false): return fail("cracked", {"text": Tx.t("sim.crafting.furnace_cracked") % ContentDB.item_name(str(furnace.id))})
		if count > int(furnace.get("batch", 1)):
			return fail("batch", {"text": Tx.plural("sim.crafting.furnace_batch", int(furnace.get("batch", 1))) % [ContentDB.item_name(str(furnace.get("id", ""))), int(furnace.get("batch", 1))]})
		if not fire in crafting.fires_available(c): fire = "charcoal"
		# Some pills take only one fire (S48: the Heavenly Flame Pill).
		var need_fire := str(ContentDB.entry("recipes", recipe_id).get("fire", ""))
		if need_fire != "" and fire != need_fire:
			return fail("needs_fire", {"text": Tx.t("sim.crafting.needs_fire") % Tx.t("ui.crafts.fire_" + need_fire)})
	var why := recipe_check(c, recipe_id, count, craft_kind, inputs)
	if why != "": return fail("cannot_craft", {"text": why})
	var r := ContentDB.entry("recipes", recipe_id)
	# Herbs that fight each other blow the furnace (S44): the batch is lost.
	if craft_kind == "alchemy":
		var clash := crafting.conflict_in(inputs)
		if not clash.is_empty(): return crafting.blast(c, recipe_id, with_aged(c, inputs, count).inputs, 1, clash)
	var aged := with_aged(c, inputs, count)
	var rng := Rng.stream(c.id, "crafting")
	var quality := "common"
	if craft_kind in ["alchemy", "smithing", "talisman"]:
		var avg := quality_score(c, craft_kind, furnace, r, scores)
		avg += float(ContentDB.config("garden").get("age_quality", 0.04)) * int(aged.tiers)   # older herbs refine better (S45)
		var roll := avg + rng.randf_range(-0.08, 0.08)
		quality = "flawed" if roll < 0.35 else ("common" if roll < 0.6 else ("fine" if roll < 0.78 else ("superior" if roll < 0.9 else "perfect")))
		if craft_kind == "alchemy" and quality == "perfect": quality = crafting.furnaces.rare_pill_quality(c, scores, rng, crafting.rare_allowed(furnace, fire))
		if craft_kind == "alchemy": c.cooldowns.erase("grain_blessing")   # the Hundred-Year Wine blesses one batch (S49)
	var used := consume(c, recipe_id, aged.inputs, principal_of(r, inputs))
	# S45: an unappraised fake herb in the batch spoils the pill more often than not.
	if craft_kind == "alchemy" and used.fake and Rng.stream(c.id, "garden").randf() < float(ContentDB.config("garden").get("fakes", {}).get("flawed", 0.6)):
		quality = "flawed"
	if craft_kind == "alchemy" and fire == "beast_fire": game.inventory.apply_remove(c.id, crafting.furnaces.core_to_burn(c), 1, "beast_fire")
	# S44 pill tribulation: a Heaven-grade (or better) pill that reaches Halo or Soul at the furnace must first come
	# through the bolts; its pills wait until it does (the page plays the screen; other callers keep the roll).
	if craft_kind == "alchemy" and live and quality in ["pill_halo", "pill_soul"] \
			and StatRules.grade_index(str(r.get("grade", "plain"))) >= StatRules.grade_index("heaven"):
		return crafting.begin_tribulation(c, recipe_id, count, quality, fire, furnace, str(used.prep))
	return grant(c, recipe_id, count, quality, fire, craft_kind, furnace, str(used.prep))

## The recipe's principal herb: the input its roles mark principal, else its first herb.
func principal_of(r: Dictionary, inputs: Array) -> String:
	var roles: Array = r.get("roles", [])
	var i := roles.find("principal")
	if i >= 0 and i < inputs.size(): return str(inputs[i].item)
	for inp in inputs:
		if str(ContentDB.item(str(inp.item)).get("type", "")) == "herb": return str(inp.item)
	return ""

## Takes a craft's inputs from the bag (S45). The principal herb comes from a steamed or wine-soaked stack when there
## is enough of one, and then the pills carry that prep; other herbs are taken plain first and sealed stacks last.
## Returns {prep, fake}.
func consume(c, recipe_id: String, rows: Array, principal: String) -> Dictionary:
	var out := {"prep": "", "fake": false}
	for row in rows:
		var item := str(row.item)
		var n := int(row.count)
		if str(ContentDB.item(item).get("type", "")) != "herb":
			game.inventory.apply_remove(c.id, item, n, "craft:" + recipe_id)
			continue
		var want := ""
		if item == principal:
			for kind in ContentDB.config("garden").get("racks", {}).keys():
				if ContentDB.config("garden").racks[kind] is Dictionary and game.inventory.count_prep(c, item, str(kind)) >= n:
					want = str(kind)
					break
		var taken: Array = game.inventory.take_ranked(c.id, item, n, "craft:" + recipe_id,
			func(st): return (0 if str(st.get("prep", "")) == want else 2) + (1 if st.get("unappraised", false) else 0))
		for tk in taken:
			if tk.fake: out.fake = true
		if item == principal and want != "": out.prep = want
	return out

## Hands over what a craft made: the outputs (a furnace's extra pill, a liquid to the Draught slot), XP and events.
func grant(c, recipe_id: String, count: int, quality: String, fire: String, craft_kind: String, furnace: Dictionary, prep := "") -> Dictionary:
	var r := ContentDB.entry("recipes", recipe_id)
	var rng := Rng.stream(c.id, "crafting")
	var produced := 0
	# Marks and a furnace's extra pill roll on their own stream, so the crafting stream's sequence
	# (quality, and every forged piece after it) is the same as before furnaces existed.
	var frng := Rng.stream(c.id, "furnace")
	var marks := crafting.furnaces.roll_marks(quality, frng) if craft_kind == "alchemy" else 0
	for out in r.get("outputs", []):
		var n := int(out.count) * count
		if craft_kind == "alchemy" and frng.randf() < float(furnace.get("yield", 0.0)): n += 1   # the furnace gives one more
		if craft_kind == "cooking" and rng.randf() < c.stats.value("insight") * 0.002: n += int(out.count)
		if craft_kind == "smithing" and ContentDB.is_equipment(str(out.item)):
			var def := ContentDB.item(str(out.item))
			for i in n:
				var inst := LootRules.make_instance(str(out.item), int(def.get("ilv", 1)), quality, Rng.stream(c.id, "affix"), c.inventory.take_uid())
				game.inventory.apply_add_instance(c.id, inst, "forge")
		elif craft_kind == "alchemy" and ContentDB.item(str(out.item)).has("draught"):
			game.inventory.apply_draught(c.id, str(out.item), n, "craft")   # a liquid goes to the Draught slot (S44)
		elif craft_kind == "alchemy":
			game.inventory.apply_add(c.id, str(out.item), n, "craft", {"quality": quality, "marks": marks, "prep": prep})
		elif craft_kind == "talisman" and ContentDB.has_entry("talismans", str(out.item)):
			game.inventory.apply_add(c.id, str(out.item), n, "craft", {"quality": quality})
		else:
			game.inventory.apply_add(c.id, str(out.item), n, "craft")
		produced += n
	var xp := float(ContentDB.curve("profession_xp.craft_per_grade", 10)) * (StatRules.grade_index(str(r.get("grade", "plain"))) + 1) * count
	if craft_kind == "cooking": xp = float(ContentDB.curve("profession_xp.cook", 6)) * count
	if r.has("xp"): xp = float(r.xp) * count   # star charts: 40 per route (S29)
	if quality in ["fine", "superior", "perfect", "pill_grain", "pill_halo", "pill_soul"]: xp *= 1.5
	crafting.add_xp(c, craft_kind, xp)
	if craft_kind == "alchemy": game.progression.apply_insight(c.id, "alchemy", 3.0 * count, "craft:" + recipe_id)
	if craft_kind == "smithing": game.progression.apply_insight(c.id, "refining", 3.0, "craft:" + recipe_id)
	emit("craft_completed", {"actor": c.id, "recipe": recipe_id, "craft": craft_kind, "quality": quality, "count": produced, "marks": marks, "fire": fire})
	if quality in ["pill_halo", "pill_soul"]: emit("pill_cloud", {"actor": c.id, "recipe": recipe_id, "quality": quality})
	return ok({"quality": quality, "count": produced, "marks": marks, "fire": fire})

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
		avg += float(crafting.upkeep("furnace_affinity", 0.05))
	return avg

func queue_auto(c, recipe_id: String, count: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "auto_refine"): return fail("locked")
	if c.crafting.auto_queue.size() >= 5: return fail("queue_full")
	# Decision 43 (systems as places): the queue is filled at a furnace, and from anywhere once its remote access is
	# earned (a first batch queued at one, then Qi Unfurling: PlaceRules.remote_open).
	var at_furnace := crafting.station_near(c, CraftingAuthority.STATIONS.alchemy)
	var why := recipe_check(c, recipe_id, count, "alchemy", [], not at_furnace and PlaceRules.remote_open(c, "alchemy"))
	if why != "": return fail("cannot_craft", {"text": why})
	if at_furnace: PlaceRules.note_use(game, c, "alchemy")
	if count > int(crafting.furnace_of(c).get("batch", 1)): return fail("batch", {"text": Tx.plural("sim.crafting.furnace_batch", int(crafting.furnace_of(c).get("batch", 1))) % [ContentDB.item_name(str(crafting.furnace_of(c).get("id", ""))), int(crafting.furnace_of(c).get("batch", 1))]})
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
			crafting.add_xp(c, "alchemy", float(ContentDB.curve("profession_xp.craft_per_grade", 10)) * (StatRules.grade_index(str(ar.get("grade", "plain"))) + 1) * int(q.count) * 0.25)
			emit("craft_completed", {"actor": c.id, "recipe": q.recipe, "craft": "alchemy", "quality": "common", "count": q.count, "auto": true})
	if got == 0: return fail("not_ready", {"text": Tx.t("sim.crafting.no_batch_is_finished_yet")})
	emit("system_used", {"actor": c.id, "system": "auto_refine_collected"})
	return ok({"batches": got})

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
