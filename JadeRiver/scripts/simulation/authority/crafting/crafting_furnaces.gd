class_name CraftingFurnaces
extends CraftingPart
## CraftingAuthority's part: the furnace in the furnace slot, the fires a character can light, Beast Fire's cores and
## the Heavenly Flames, the rare pill qualities (Grain, Halo, Soul) and the pill tribulation with the Pill Soul's
## flight (S44).

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
	out.band = float(f.get("band", 0.0)) + float(crafting.upkeep("furnace_band_per_level", 0.01)) * int(inst.get("enhance", 0))
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
	if crafting.station_near(c, ["earth_vent"]): out.append("earth_fire")
	if core_to_burn(c) != "": out.append("beast_fire")
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
func core_to_burn(c) -> String:
	var best := ""
	var best_rank := 99
	for s in c.inventory.bag:
		if s == null: continue
		var core: Dictionary = ContentDB.item(str(s.id)).get("core", {})
		var rank := int(core.get("rank", 1)) if not core.is_empty() else 0
		if rank >= int(crafting.upkeep("beast_fire_min_rank", 2)) and rank < best_rank:
			best = str(s.id)
			best_rank = rank
	return best

func roll_marks(quality: String, rng: RandomNumberGenerator) -> int:
	var r: Array = ContentDB.config("grades").get("pill", {}).get("marks", {}).get("ranges", {}).get(quality, [0, 0])
	return rng.randi_range(int(r[0]), int(r[1]))

## Absorb a Heavenly Flame: it burns under every furnace from now on. A second copy gutters into Spirit Stones.
func absorb_flame(c, index: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var id := str(c.inventory.bag[index].id)
	if str(ContentDB.item(id).get("use_action", "")) != "absorb_flame": return fail("not_a_flame")
	game.inventory.apply_remove_index(c.id, index, 1, "absorb_flame")
	return _absorb(c, id)

## A flame given outright (an effect: a boss's heart-fire, a secret realm's reward) is absorbed the same way.
func apply_absorb_flame(actor_id: String, id: String) -> void:
	var c = game.character(actor_id)
	if c != null and str(ContentDB.item(id).get("use_action", "")) == "absorb_flame": _absorb(c, id)

func _absorb(c, id: String) -> Dictionary:
	var flames: Array = c.crafting.get("flames", [])
	if flames.has(id):
		game.economy.apply_currency("spirit_stone", 20, "flame_gutters")
		return ok({"text": Tx.t("sim.crafting.flame_gutters") % ContentDB.item_name(id), "duplicate": true})
	flames.append(id)
	c.crafting["flames"] = flames
	if ContentDB.has_entry("codex", id): game.apply_effects(c.id, [{"kind": "codex", "entry": id}], "flame")
	emit("flame_absorbed", {"actor": c.id, "flame": id})
	emit("system_used", {"actor": c.id, "system": "absorb_flame"})
	return ok({"text": Tx.t("sim.crafting.flame_absorbed") % ContentDB.item_name(id)})

## Pill Grain, Halo and Soul (S15): a perfect run (every strike perfect, from Heart Tempering 1)
## plus luck; a special furnace and the Alchemy Dao improve the odds.
func rare_pill_quality(c, scores: Array, rng: RandomNumberGenerator, allowed: Array = ["pill_grain", "pill_halo", "pill_soul"]) -> String:
	var k: Dictionary = ContentDB.curve("craft_step", {})
	if scores.size() < int(k.get("steps", 3)) or not Unlocks.is_unlocked(c.id, "perfect_timing"): return "perfect"
	for sc in scores:
		if float(sc) < float(k.get("perfect", 0.85)): return "perfect"
	var rare: Dictionary = ContentDB.config("grades").get("pill", {}).get("rare", {})
	var boost := 1.0 + furnace_bonus(c) + 0.1 * int(c.cultivator.daos.get("alchemy", {}).get("tier", 0))
	var blessing := float(c.cooldowns.get("grain_blessing", 0.0))   # S49: the Hundred-Year Wine poured over the furnace
	var roll := rng.randf()
	var edge := 0.0
	for q in ["pill_soul", "pill_halo", "pill_grain"]:
		if not q in allowed: continue   # charcoal stops at Perfect (G1)
		edge += float(rare.get(q, 0.0)) * boost + (blessing if q == "pill_grain" else 0.0)
		if roll < edge: return q
	return "perfect"

## S49 fortune: the Hundred-Year Wine poured over the furnace. The next alchemy batch that comes out Perfect has this
## much more chance to be Grain (the blessing goes with that batch, whatever it makes).
func apply_grain_blessing(actor_id: String, value: float) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cooldowns["grain_blessing"] = value if value >= 0.0 else float(ContentDB.config("fortune_deck").get("wine_grain", 0.25))

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

# ------------------------------------------------------------------ S44 pill tribulation and the Pill Soul's flight
## 3 bolts, +2 for each grade above Heaven, at most 9, at times drawn from the crafting stream.
func begin_tribulation(c, recipe_id: String, count: int, quality: String, fire: String, furnace: Dictionary, prep := "") -> Dictionary:
	var k: Dictionary = crafting.upkeep("tribulation", {})
	var above := StatRules.grade_index(str(ContentDB.entry("recipes", recipe_id).get("grade", "heaven"))) - StatRules.grade_index("heaven")
	var n := clampi(int(k.get("bolts", 3)) + int(k.get("per_grade", 2)) * above, 1, int(k.get("max", 9)))
	var rng := Rng.stream(c.id, "crafting")
	var times: Array = []
	var t := float(k.get("first_s", 1.2))
	for i in n:
		times.append(snappedf(t, 0.01))
		t += rng.randf_range(float(k.get("gap_min_s", 0.7)), float(k.get("gap_max_s", 1.3)))
	crafting.tribulations[c.id] = {"recipe": recipe_id, "count": count, "quality": quality, "fire": fire, "furnace": furnace.duplicate(), "prep": prep,
		"bolts": times, "blocked": 0, "answered": 0, "stage": "bolts"}
	return ok({"pending": "tribulation", "bolts": times, "window": float(k.get("window_s", 0.22)), "quality": quality})

## One bolt: `timing` is how far from its strike the shield went up (seconds, either side); inside the window it holds.
func tribulation_shield(c, bolt: int, timing: float) -> Dictionary:
	var tr: Dictionary = crafting.tribulations.get(c.id, {})
	if tr.is_empty() or str(tr.stage) != "bolts": return fail("no_tribulation")
	if bolt != int(tr.answered): return fail("wrong_bolt")
	var k: Dictionary = crafting.upkeep("tribulation", {})
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
	crafting.tribulations.erase(c.id)
	var res := crafting.recipes.grant(c, str(tr.recipe), int(tr.count), after, str(tr.fire), "alchemy", tr.furnace, str(tr.get("prep", "")))
	res.held = held
	res.left = 0
	return res

## The Pill Soul's flight: caught, it stays a Pill Soul; missed, it settles as a Pill Halo. The batch is never lost.
func catch_pill_soul(c, timing: float) -> Dictionary:
	var tr: Dictionary = crafting.tribulations.get(c.id, {})
	if tr.is_empty() or str(tr.stage) != "soul": return fail("no_soul")
	var caught := absf(timing) <= float(crafting.upkeep("tribulation", {}).get("soul_window_s", 0.2))
	var quality := "pill_soul" if caught else "pill_halo"
	crafting.tribulations.erase(c.id)
	emit("pill_soul_flight", {"actor": c.id, "recipe": str(tr.recipe), "caught": caught})
	var res := crafting.recipes.grant(c, str(tr.recipe), int(tr.count), quality, str(tr.fire), "alchemy", tr.furnace, str(tr.get("prep", "")))
	res.caught = caught
	return res

## A tribulation left unfinished (the page closed, another craft begun) settles as if every bolt that was not
## answered had struck, and a fleeing Soul got away.
func settle_tribulation(c) -> void:
	var tr: Dictionary = crafting.tribulations.get(c.id, {})
	if tr.is_empty(): return
	if str(tr.stage) == "soul": catch_pill_soul(c, 99.0)
	else:
		while crafting.tribulations.has(c.id) and str(crafting.tribulations[c.id].get("stage", "")) == "bolts":
			tribulation_shield(c, int(crafting.tribulations[c.id].answered), 99.0)
		if crafting.tribulations.has(c.id): catch_pill_soul(c, 99.0)
