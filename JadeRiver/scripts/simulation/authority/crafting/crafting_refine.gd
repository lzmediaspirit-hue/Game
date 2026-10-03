class_name CraftingRefine
extends CraftingPart
## CraftingAuthority's part: the five-screen furnace (S15, S44): the plan drawn when the fire is lit, the Extraction,
## Fusion and Condensation screens, and the herbs' natures, roles, stand-ins and conflicts (a furnace blast).

# ------------------------------------------------------------------ the five-screen furnace (S15, S44)
## The page walks the first two screens on its own: Ingredients (the recipe, the batch, what Spirit Sense tells of the
## herbs) and the Furnace (the fire and the array under it). Lighting the furnace starts the refine here, which draws the
## plan the next three screens are played from: Extraction (each herb held in a swaying heat band while its impurities
## are tapped away), Fusion (the essences merged in the recipe's order, the array turned at each mark) and Condensation
## (a ring closing on the pill). The page sends what the hand did (refine_input) and this scores it within range. A
## scorched herb is lost (early mistakes waste ingredients); a cracked pill loses the whole batch. The pill tribulation
## (Heaven grade and up) is the sixth screen.
func furnace_game() -> Dictionary:
	return crafting.upkeep("furnace_game", {})

func refine_session(c) -> Dictionary:
	return crafting.refines.get(c.id, {})

## The array that answers a recipe's principal herb: Still Water under a hot one, Rising Flame under a cold one; "" when
## the principal is neither and either array serves.
func suited_array(recipe_id: String, substitute: Dictionary = {}) -> String:
	var principal := crafting.recipes.principal_of(ContentDB.entry("recipes", recipe_id), inputs_with(recipe_id, substitute))
	match str(ContentDB.item(principal).get("nature", "")):
		"hot": return "water"
		"cold": return "flame"
	return ""

## How the array under the furnace changes every heat band: wider under the suited array, narrower under the other.
func array_mult(recipe_id: String, array: String, substitute: Dictionary = {}) -> float:
	var want := suited_array(recipe_id, substitute)
	if want == "": return 1.0
	var k: Dictionary = furnace_game().get("array", {})
	return float(k.get("suited", 1.15)) if array == want else float(k.get("unsuited", 0.85))

## The width of each heat band, as a share of the gauge: the fire and furnace (band_mult), Crafting control and the array.
func heat_band(c, fire: String, recipe_id: String, array: String, substitute: Dictionary = {}) -> float:
	var k: Dictionary = furnace_game().get("extraction", {})
	return minf(float(k.get("band_max", 0.5)), float(k.get("band", 0.2)) * crafting.band_mult(c, fire) * (1.0 + c.stats.value("crafting_control"))
		* array_mult(recipe_id, array, substitute))

## How many of a herb's impurities show plainly; the rest are faint. Crafting perception shows more of them (S15).
func impurities_seen(c, n: int) -> int:
	var k: Dictionary = furnace_game().get("extraction", {})
	return mini(n, int(k.get("seen_base", 1)) + int(floor(c.stats.value("crafting_perception") / maxf(0.001, float(k.get("seen_per_perception", 0.03))))))

## What Spirit Sense shows of a batch's herbs (S15: inspect quality): each herb the batch would take (an older stand-in
## included), its age, and how many sealed (unappraised) roots it would have to use. Crafting perception of 4% or more
## also tells the dyed fakes among them (-1 when it cannot).
func sense_herbs(c, recipe_id: String, count: int, substitute: Dictionary = {}) -> Array:
	var out: Array = []
	var see: bool = c.stats.value("crafting_perception") >= float(furnace_game().get("sense_fakes", 0.04))
	for inp in inputs_with(recipe_id, substitute):
		for row in crafting.with_aged(c, [inp], count).inputs:
			var item := str(row.item)
			if str(ContentDB.item(item).get("type", "")) != "herb": continue
			var plain := 0
			var sealed := 0
			var fakes := 0
			for st in c.inventory.bag:
				if st == null or str(st.id) != item: continue
				if st.get("unappraised", false):
					sealed += int(st.get("count", 1))
					if st.get("fake", false): fakes += int(st.get("count", 1))
				else: plain += int(st.get("count", 1))
			var from_sealed := clampi(int(row.count) - plain, 0, sealed)
			out.append({"item": item, "for": str(inp.item), "age": HerbRules.item_age(item), "sealed": from_sealed,
				"fakes": mini(fakes, from_sealed) if see else -1})
	return out

## Why a refine cannot be lit ("" when it can): the checks craft() makes before it rolls.
func refine_block(c, recipe_id: String, count: int, fire: String, substitute: Dictionary = {}) -> String:
	var r := ContentDB.entry("recipes", recipe_id)
	if r.is_empty() or str(r.get("craft", "")) != "alchemy": return Tx.t("sim.crafting.unknown_recipe")
	var furnace := crafting.furnace_of(c)
	if furnace.get("cracked", false): return Tx.t("sim.crafting.furnace_cracked") % ContentDB.item_name(str(furnace.id))
	if count > int(furnace.get("batch", 1)):
		return Tx.plural("sim.crafting.furnace_batch", int(furnace.get("batch", 1))) % [ContentDB.item_name(str(furnace.get("id", ""))), int(furnace.get("batch", 1))]
	var need_fire := str(r.get("fire", ""))
	if need_fire != "" and fire != need_fire: return Tx.t("sim.crafting.needs_fire") % Tx.t("ui.crafts.fire_" + need_fire)
	if not substitute.is_empty():
		var sw := substitute_check(c, recipe_id, str(substitute.get("from", "")), str(substitute.get("to", "")))
		if sw != "": return sw
	return crafting.recipe_check(c, recipe_id, count, "alchemy", inputs_with(recipe_id, substitute))

## Lighting the furnace (screen 2 done): checks the refine, then draws its plan on the furnace_plan stream (the
## quality roll's own stream is untouched). A refine already burning is put out first; its herbs in the fire are lost.
func start_refine(c, recipe_id: String, count: int, fire: String, array: String, substitute: Dictionary = {}) -> Dictionary:
	crafting.furnaces.settle_tribulation(c)
	if crafting.refines.has(c.id): cancel_refine(c)
	if not fire in crafting.fires_available(c): fire = "charcoal"
	var why := refine_block(c, recipe_id, count, fire, substitute)
	if why != "": return fail("cannot_craft", {"text": why})
	if not array in ["water", "flame"]: array = "water"
	var r := ContentDB.entry("recipes", recipe_id)
	var k: Dictionary = furnace_game()
	var ke: Dictionary = k.get("extraction", {})
	var rng := Rng.stream(c.id, "furnace_plan")
	var width := heat_band(c, fire, recipe_id, array, substitute)
	var secs := float(ke.get("seconds", 5.0))
	var imp: Array = ke.get("impurities", [1, 3])
	var period: Array = ke.get("period_s", [2.6, 3.8])
	var inputs := inputs_with(recipe_id, substitute)
	var roles: Array = r.get("roles", [])
	var herbs: Array = []
	for i in inputs.size():
		var item := str(inputs[i].item)
		# Hot herbs raise their band up the gauge and cold ones lower it (S44); the sway keeps it on the gauge.
		var nature := str(ContentDB.item(item).get("nature", ""))
		var shift := float(crafting.upkeep("nature_shift", 0.08))
		var centre := 0.5 + (shift if nature == "hot" else (-shift if nature == "cold" else 0.0))
		var sway := clampf(float(ke.get("sway", 0.16)), 0.0, minf(centre, 1.0 - centre) - width * 0.5 - 0.02)
		var n := rng.randi_range(int(imp[0]), int(imp[1]))
		var seen := impurities_seen(c, n)
		var faint_at: Array = []
		for j in n: faint_at.append(j)
		for j in range(n - 1, 0, -1):
			var m := rng.randi_range(0, j)
			var tmp = faint_at[j]
			faint_at[j] = faint_at[m]
			faint_at[m] = tmp
		var specks: Array = []
		for j in n:
			specks.append({"t": snappedf(secs * (0.1 + 0.72 * (j + rng.randf()) / n), 0.01), "x": snappedf(rng.randf_range(0.22, 0.78), 0.01),
				"y": snappedf(rng.randf_range(0.3, 0.75), 0.01), "faint": faint_at.find(j) >= seen})
		herbs.append({"item": item, "role": str(roles[i]) if i < roles.size() else "", "nature": nature, "count": int(inputs[i].count) * count,
			"centre": centre, "sway": sway, "period": snappedf(rng.randf_range(float(period[0]), float(period[1])), 0.01),
			"phase": snappedf(rng.randf_range(0.0, TAU), 0.01), "width": width, "specks": specks})
	# The recipe's order: Principal, Minister, Assistant, Envoy (a slot without a role comes last, in listed order).
	var order: Array = []
	for i in inputs.size(): order.append(i)
	order.sort_custom(func(a, b): return _role_rank(roles, a) * 10 + a < _role_rank(roles, b) * 10 + b)
	var kf: Dictionary = k.get("fusion", {})
	var nm: Array = kf.get("marks", [2, 3])
	var marks: Array = []
	var count_marks := rng.randi_range(int(nm[0]), int(nm[1]))
	for m in count_marks: marks.append(snappedf(0.18 + (m + rng.randf_range(0.2, 0.8)) * 0.72 / count_marks, 0.01))
	crafting.refines[c.id] = {"recipe": recipe_id, "count": count, "fire": fire, "array": array, "substitute": substitute.duplicate(), "herbs": herbs,
		"order": order, "marks": marks, "liquid": bool(r.get("liquid", false)), "stage": "extraction", "at": 0, "extraction": [], "fusion": 0.0}
	emit("craft_started", {"actor": c.id, "recipe": recipe_id, "craft": "alchemy", "count": count})
	return ok({"plan": (crafting.refines[c.id] as Dictionary).duplicate(true)})

static func _role_rank(roles: Array, i: int) -> int:
	var at := ["principal", "minister", "assistant", "envoy"].find(str(roles[i]) if i < roles.size() else "")
	return at if at >= 0 else 9

## One screen's result from the page. Extraction: {herb, held (the share of the time the heat stayed in the band),
## taps (impurities struck)}. Fusion: {order (the herbs as merged), marks (how far off each turn of the array was, as a
## share of the bar)}. Condensation: {offset (seconds from the ring meeting the pill; early is negative)}.
func refine_input(c, step: String, value: Dictionary) -> Dictionary:
	var s: Dictionary = crafting.refines.get(c.id, {})
	if s.is_empty(): return fail("no_refine")
	if step != str(s.stage): return fail("wrong_step")
	match step:
		"extraction": return _extract(c, s, value)
		"fusion": return _fuse(c, s, value)
		"condensation": return _condense(c, s, value)
	return fail("wrong_step")

static func step_grade(score: float) -> String:
	var k: Dictionary = ContentDB.curve("craft_step", {})
	return "perfect" if score >= float(k.get("perfect", 0.85)) else ("good" if score >= float(k.get("good", 0.5)) else "miss")

## The bag rows one herb of the batch takes (an older stand-in included), and whether they are all there.
func _herb_rows(c, herb: Dictionary) -> Dictionary:
	var rows: Array = crafting.with_aged(c, [{"item": str(herb.item), "count": int(herb.count)}], 1).inputs
	var have := true
	for row in rows:
		if c.inventory.count(str(row.item)) < int(row.count): have = false
	return {"rows": rows, "have": have}

func _lose_rows(c, rows: Array, source: String) -> Array:
	var lost: Array = []
	for row in rows:
		var n := mini(int(row.count), c.inventory.count(str(row.item)))
		if n <= 0: continue
		if str(ContentDB.item(str(row.item)).get("type", "")) == "herb":
			game.inventory.take_ranked(c.id, str(row.item), n, source, func(st): return 1 if st.get("unappraised", false) else 0)
		else: game.inventory.apply_remove(c.id, str(row.item), n, source)
		lost.append({"item": str(row.item), "count": n})
	return lost

func _extract(c, s: Dictionary, value: Dictionary) -> Dictionary:
	var i := int(value.get("herb", -1))
	if i != int(s.at): return fail("wrong_herb")
	var herb: Dictionary = s.herbs[i]
	var hr := _herb_rows(c, herb)
	if not hr.have: return fail("cannot_craft", {"text": Tx.t("sim.crafting.missing") % ContentDB.item_name(str(herb.item))})
	var k: Dictionary = furnace_game().get("extraction", {})
	var held := clampf(float(value.get("held", 0.0)), 0.0, 1.0)
	var n := (herb.specks as Array).size()
	var taps := clampi(int(value.get("taps", 0)), 0, n)
	var scorch := float(k.get("scorch", 0.35))
	if held < scorch:
		# Early mistakes waste ingredients: this herb is ash. The refine waits for another of it, or is put out.
		_lose_rows(c, hr.rows, "refine_scorched")
		emit("craft_step_result", {"actor": c.id, "recipe": str(s.recipe), "step": 1, "herb": str(herb.item), "score": 0.0, "grade": "scorched"})
		return ok({"score": 0.0, "grade": "scorched", "scorched": true, "retry": _herb_rows(c, herb).have,
			"text": Tx.t("sim.crafting.herb_scorched") % ContentDB.item_name(str(herb.item))})
	var hold := clampf((held - scorch) / maxf(0.01, float(k.get("hold_full", 0.9)) - scorch), 0.0, 1.0)
	var w := float(k.get("impurity_weight", 0.25)) if n > 0 else 0.0
	var score := hold * (1.0 - w) + (float(taps) / n if n > 0 else 0.0) * w
	(s.extraction as Array).append(score)
	s.at = i + 1
	if int(s.at) >= (s.herbs as Array).size(): s.stage = "fusion"
	var grade := step_grade(score)
	emit("craft_step_result", {"actor": c.id, "recipe": str(s.recipe), "step": 1, "herb": str(herb.item), "score": score, "grade": grade})
	return ok({"score": score, "grade": grade, "stage": str(s.stage)})

func _fuse(c, s: Dictionary, value: Dictionary) -> Dictionary:
	var n := (s.herbs as Array).size()
	var order: Array = value.get("order", []) if value.get("order", []) is Array else []
	var seen := {}
	for o in order:
		var oi := int(o)
		if oi < 0 or oi >= n or seen.has(oi): return fail("bad_input")
		seen[oi] = true
	if seen.size() != n: return fail("bad_input")
	# Herbs that fight each other blow the furnace as they merge (S44): the batch is lost.
	var inputs := inputs_with(str(s.recipe), s.substitute)
	var clash := conflict_in(inputs)
	if not clash.is_empty():
		crafting.refines.erase(c.id)
		return blast(c, str(s.recipe), crafting.with_aged(c, inputs, int(s.count)).inputs, 1, clash)
	var right := 0
	for j in n:
		if int(order[j]) == int(s.order[j]): right += 1
	var k: Dictionary = furnace_game().get("fusion", {})
	var marks: Array = s.marks
	var offs: Array = value.get("marks", []) if value.get("marks", []) is Array else []
	var turned := 0.0
	for m in marks.size():
		var off := absf(float(offs[m])) if m < offs.size() else 99.0
		turned += clampf(1.0 - off / maxf(0.01, float(k.get("window", 0.1))), 0.0, 1.0)
	var ow := float(k.get("order_weight", 0.6))
	var score := ow * float(right) / maxf(1.0, n) + (1.0 - ow) * (turned / marks.size() if not marks.is_empty() else 1.0)
	s.fusion = score
	var grade := step_grade(score)
	emit("craft_step_result", {"actor": c.id, "recipe": str(s.recipe), "step": 2, "score": score, "grade": grade})
	# A liquid has no Condensation (S44): it is done when the essences are one.
	if s.liquid: return _finish(c, s, [score], grade, score)
	s.stage = "condensation"
	return ok({"score": score, "grade": grade, "stage": "condensation", "in_order": right == n})

func _condense(c, s: Dictionary, value: Dictionary) -> Dictionary:
	var k: Dictionary = furnace_game().get("condensation", {})
	var off := float(value.get("offset", 99.0))
	var perfect := float(k.get("perfect", 0.08))
	var late := float(k.get("late", 0.2))
	if off > late:
		# Late mistakes ruin the batch: the pill cracks and everything in the furnace is lost.
		crafting.refines.erase(c.id)
		var lost := _lose_rows(c, crafting.with_aged(c, inputs_with(str(s.recipe), s.substitute), int(s.count)).inputs, "refine_cracked")
		emit("craft_step_result", {"actor": c.id, "recipe": str(s.recipe), "step": 3, "score": 0.0, "grade": "cracked"})
		return ok({"score": 0.0, "grade": "cracked", "cracked": true, "lost": lost, "text": Tx.t("sim.crafting.pill_cracked")})
	var score := 1.0
	if off < -perfect: score = clampf(1.0 - (-off - perfect) / maxf(0.01, float(k.get("early_span", 0.7))), float(k.get("weak_floor", 0.2)), 1.0)
	elif off > perfect: score = clampf(1.0 - 0.5 * (off - perfect) / maxf(0.01, late - perfect), 0.0, 1.0)
	var grade := step_grade(score)
	emit("craft_step_result", {"actor": c.id, "recipe": str(s.recipe), "step": 3, "score": score, "grade": grade})
	return _finish(c, s, [score], grade, score)

## The last screen is done: the pills are rolled from the three screens' scores (Extraction the mean of its herbs).
func _finish(c, s: Dictionary, last: Array, grade: String, score: float) -> Dictionary:
	crafting.refines.erase(c.id)
	var ext := 0.0
	for x in s.extraction: ext += float(x)
	ext /= maxf(1.0, (s.extraction as Array).size())
	var scores: Array = [ext]
	if not s.liquid: scores.append(float(s.fusion))
	scores.append_array(last)
	var res := crafting.craft(c, str(s.recipe), int(s.count), scores, "alchemy", str(s.fire), s.substitute, true)
	res.step_score = score
	res.grade = grade
	res.scores = scores
	return res

## Putting out the fire mid-refine: the herbs already in it are lost; the rest stay in the bag.
func cancel_refine(c) -> Dictionary:
	var s: Dictionary = crafting.refines.get(c.id, {})
	if s.is_empty(): return fail("no_refine")
	crafting.refines.erase(c.id)
	var lost: Array = []
	for i in mini(int(s.at), (s.herbs as Array).size()):
		lost.append_array(_lose_rows(c, _herb_rows(c, s.herbs[i]).rows, "refine_abandoned"))
	return ok({"lost": lost})

# ------------------------------------------------------------------ herb nature, roles and conflicts (S44)
## How far a recipe's herbs move the Extraction band, in parts of the bar: +8% for each hot herb, -8% for each cold.
func nature_shift(recipe_id: String, substitute: Dictionary = {}) -> float:
	var step := float(crafting.upkeep("nature_shift", 0.08))
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
	if int(c.cultivator.daos.get("alchemy", {}).get("tier", 0)) < int(crafting.upkeep("substitute_tier", 5)): return Tx.t("sim.crafting.substitute_tier")
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
	if inst != null: game.inventory.apply_durability(c.id, inst, int(inst.get("durability", 100)) - int(crafting.upkeep("blast_durability", 10)), "tool_furnace")
	var known: Array = c.crafting.get("known_conflicts", [])
	if not known.has(str(clash.id)): known.append(str(clash.id))
	c.crafting["known_conflicts"] = known
	emit("furnace_blast", {"actor": c.id, "recipe": recipe_id, "conflict": str(clash.id), "herbs": clash.get("herbs", []),
		"durability": int(inst.get("durability", 0)) if inst != null else 0})
	return fail("blast", {"text": Tx.t("sim.crafting.furnace_blast") % str(clash.get("text", ""))})
