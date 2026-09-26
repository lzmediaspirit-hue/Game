class_name CraftingAuthority
extends Authority
## S15/S16/S33 · Recipes known, profession ranks, gathering and mining nodes,
## fishing, cooking, alchemy (five-screen mini-game scores), the forge and the
## auto-refine queue. One crafting framework: validate inputs, consume, roll quality
## with the `crafting` stream, grant output and profession XP, emit craft_completed.

var pending: Dictionary = {}   # actor -> {object, kind, started, channel}
var steps: Dictionary = {}     # actor -> {recipe, craft, scores}: the mini-game in progress
var refines: Dictionary = {}   # actor -> the five-screen refine in progress (V9e2): see start_refine

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
	return ["complete_node", "catch_fish", "cook", "craft_step", "refine", "start_refine", "refine_input", "cancel_refine", "queue_auto_refine",
		"collect_auto_refine", "forge", "enhance", "salvage_item",
		"salvage", "inherit_enhancement", "reroll_affixes", "choose_affixes", "lock_affix", "chart_route", "build_vessel", "absorb_flame",
		"trace_talisman", "restore_relic", "awaken_weapon", "mend_furnace", "deduce_recipe", "start_experiment", "take_guild_exam", "accept_commission",
		"deliver_commission", "tribulation_shield", "catch_pill_soul", "plant_seed", "water_bed", "harvest_bed", "apply_spirit_soil", "use_dew",
		"transplant", "start_rack", "collect_racks"]

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
		"start_refine": return start_refine(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10), str(intent.get("fire", "charcoal")),
			str(intent.get("array", "")), intent.get("substitute", {}) if intent.get("substitute", {}) is Dictionary else {})
		"refine_input": return refine_input(c, str(intent.get("step", "")), intent.get("value", {}) if intent.get("value", {}) is Dictionary else {})
		"cancel_refine": return cancel_refine(c)
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
		"awaken_weapon": return awaken_weapon(c, intent)
		"mend_furnace": return mend_furnace(c, int(intent.get("uid", -1)))
		"deduce_recipe": return deduce(c, str(intent.get("recipe", "")))
		"start_experiment": return experiment(c, intent.get("herbs", []) if intent.get("herbs", []) is Array else [])
		"take_guild_exam": return take_exam(c, str(intent.get("craft", "alchemy")), str(intent.get("rank", "")))
		"accept_commission": return accept_commission(c, str(intent.get("id", "")))
		"deliver_commission": return deliver_commission(c, str(intent.get("id", "")), str(intent.get("pay", "taels")))
		"plant_seed": return plant_seed(c, str(intent.get("bed", "")), str(intent.get("seed", "")))
		"water_bed": return water_bed(c, str(intent.get("bed", "")))
		"harvest_bed": return harvest_bed(c, str(intent.get("bed", "")))
		"apply_spirit_soil": return apply_spirit_soil(c, str(intent.get("bed", "")))
		"use_dew": return use_dew(c, str(intent.get("bed", "")))
		"transplant": return transplant(c, str(intent.get("object", "")))
		"start_rack": return start_rack(c, str(intent.get("kind", "")), str(intent.get("herb", "")), int(intent.get("count", 1)))
		"collect_racks": return collect_racks(c)
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

# ------------------------------------------------------------------ S45 garden beds
## Beds are room objects; each character keeps its own record of every bed it tends, keyed "room:object":
## {herb, progress (0..1), updated (utc), grow_s, soil}. Growth is settled from the clock, so it runs offline.
func beds(c) -> Dictionary:
	if not (c.crafting.get("garden") is Dictionary): c.crafting["garden"] = {}
	return c.crafting.garden

func bed_def(key: String) -> Dictionary:
	var room := key.get_slice(":", 0)
	for o in ContentDB.room(room).get("objects", []):
		if str(o.get("id", "")) == key.get_slice(":", 1) and str(o.get("type", "")) == "garden_bed": return o
	return {}

func bed_record(c, key: String) -> Dictionary:
	var b := beds(c)
	if not b.has(key): b[key] = {"herb": "", "progress": 0.0, "updated": 0.0, "grow_s": 1.0, "soil": 0}
	return b[key]

## Low / Mid / High: the bed's own grade plus the Spirit Soil worked into it.
func bed_grade(c, key: String) -> String:
	var grades: Array = ContentDB.config("garden").get("field_grades", ["low", "mid", "high"])
	var i := grades.find(str(bed_def(key).get("field_grade", "low"))) + int(bed_record(c, key).get("soil", 0))
	return str(grades[clampi(i, 0, grades.size() - 1)])

## Can this bed hold a herb of this grade?
func bed_holds(c, key: String, herb: String) -> bool:
	var cap := str(ContentDB.config("garden").get("field_cap", {}).get(bed_grade(c, key), "earth"))
	return StatRules.grade_index(str(ContentDB.item(herb).get("grade", "plain"))) <= StatRules.grade_index(cap)

## A room's Qi speeds its beds by half its bonus.
func bed_speed(key: String) -> float:
	var qi := float(ContentDB.room(key.get_slice(":", 0)).get("qi", 1.0))
	return maxf(0.25, 1.0 + (qi - 1.0) * float(ContentDB.config("garden").get("qi_growth", 0.5)))

func settle_bed(c, key: String) -> Dictionary:
	var rec := bed_record(c, key)
	var now := Clock.now_utc()
	if str(rec.herb) != "" and float(rec.updated) > 0.0:
		var el := Clock.elapsed_since(float(rec.updated))
		if el.valid: rec.progress = minf(1.0, float(rec.progress) + float(el.elapsed) * bed_speed(key) / maxf(1.0, float(rec.grow_s)))
	rec.updated = now
	return rec

## What the Garden page shows for a bed.
func bed_view(c, key: String) -> Dictionary:
	var rec := settle_bed(c, key)
	var left := (1.0 - float(rec.progress)) * float(rec.grow_s) / bed_speed(key) if str(rec.herb) != "" else 0.0
	return {"key": key, "herb": str(rec.herb), "age": HerbRules.item_age(str(rec.herb)) if str(rec.herb) != "" else 0, "progress": float(rec.progress),
		"seconds": left, "ready": str(rec.herb) != "" and float(rec.progress) >= 1.0, "grade": bed_grade(c, key), "soil": int(rec.get("soil", 0))}

## The beds a character can tend in a room.
func room_beds(c, room_id: String) -> Array:
	var out: Array = []
	for o in ContentDB.room(room_id).get("objects", []):
		if str(o.get("type", "")) == "garden_bed" and game.world.object_visible(c, o) and (not o.has("requires") or RequirementRules.passes(o.requires, game.ctx(c))):
			out.append(room_id + ":" + str(o.id))
	return out

func _bed_check(c, key: String) -> String:
	if not Unlocks.is_unlocked(c.id, "herb_garden"): return Unlocks.locked_text("herb_garden")
	if bed_def(key).is_empty(): return Tx.t("sim.crafting.no_such_bed")
	if game.room_rt == null or game.room_rt.room_id != key.get_slice(":", 0): return Tx.t("sim.crafting.bed_elsewhere")
	return ""

func plant_seed(c, key: String, seed: String) -> Dictionary:
	var why := _bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var fam := str(ContentDB.item(seed).get("seed", {}).get("family", ""))
	if fam == "" or c.inventory.count(seed) <= 0: return fail("no_seed")
	var rec := settle_bed(c, key)
	if str(rec.herb) != "": return fail("planted", {"text": Tx.t("sim.crafting.bed_taken")})
	var herb := str(ContentDB.config("garden").get("families", {}).get(fam, {}).get("10", ""))
	if not bed_holds(c, key, herb): return fail("soil", {"text": Tx.t("sim.crafting.soil_too_poor") % ContentDB.item_name(herb)})
	game.inventory.apply_remove(c.id, seed, 1, "garden")
	rec.herb = herb
	rec.progress = 0.0
	rec.grow_s = float(ContentDB.config("garden").get("grow_hours", {}).get(fam, 4)) * 3600.0
	rec.updated = Clock.now_utc()
	rec.raid_day = Clock.reset_day(Clock.now_utc())
	emit("herb_planted", {"actor": c.id, "bed": key, "herb": herb})
	emit("system_used", {"actor": c.id, "system": "plant_seed"})
	return ok({"herb": herb})

## Bottled spring water hurries the herb in a bed by a quarter of its growth.
func water_bed(c, key: String) -> Dictionary:
	var why := _bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var rec := settle_bed(c, key)
	if str(rec.herb) == "" or float(rec.progress) >= 1.0: return fail("nothing_to_water")
	if c.inventory.count("spring_water") <= 0: return fail("no_water", {"text": Tx.t("sim.crafting.no_spring_water")})
	game.inventory.apply_remove(c.id, "spring_water", 1, "garden")
	rec.progress = minf(1.0, float(rec.progress) + float(ContentDB.config("garden").get("water", {}).get("growth", 0.25)))
	emit("bed_watered", {"actor": c.id, "bed": key, "progress": float(rec.progress)})
	return ok({"progress": float(rec.progress)})

func harvest_bed(c, key: String) -> Dictionary:
	var why := _bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var rec := settle_bed(c, key)
	if str(rec.herb) == "" or float(rec.progress) < 1.0: return fail("not_ready")
	var herb := str(rec.herb)
	var g := ContentDB.config("garden")
	var rng := Rng.stream(c.id, "garden")
	var y: Array = g.get("bed_yield", {}).get("young" if HerbRules.item_age(herb) <= 10 else "aged", [1, 1])
	var count := rng.randi_range(int(y[0]), int(y[1]))
	game.inventory.apply_add(c.id, herb, count, "garden")
	var seed := str(g.get("seeds", {}).get(HerbRules.family(herb), ""))
	if seed != "" and HerbRules.item_age(herb) <= 10 and rng.randf() < float(g.get("seed_back", 0.2)):
		game.inventory.apply_add(c.id, seed, 1, "garden")
		emit("seed_found", {"actor": c.id, "seed": seed, "object": key})
	else:
		seed = ""
	rec.herb = ""
	rec.progress = 0.0
	add_xp(c, "herb_gathering", float(ContentDB.curve("profession_xp.gather", 5)))
	emit("herb_harvested", {"actor": c.id, "object": key, "item": herb, "age": HerbRules.item_age(herb), "perfect": false, "early": false, "bed": true})
	return ok({"item": herb, "count": count, "seed": seed})

## Spirit Soil raises a bed's field grade one step, for good.
func apply_spirit_soil(c, key: String) -> Dictionary:
	var why := _bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	if c.inventory.count("spirit_soil") <= 0: return fail("no_soil")
	var grades: Array = ContentDB.config("garden").get("field_grades", ["low", "mid", "high"])
	if bed_grade(c, key) == str(grades.back()): return fail("max", {"text": Tx.t("sim.crafting.bed_at_best")})
	game.inventory.apply_remove(c.id, "spirit_soil", 1, "garden")
	var rec := bed_record(c, key)
	rec.soil = int(rec.get("soil", 0)) + 1
	emit("bed_enriched", {"actor": c.id, "bed": key, "grade": bed_grade(c, key)})
	return ok({"grade": bed_grade(c, key)})

# ------------------------------------------------------------------ the Verdant Dew Vial and spring water
## One dew a day, offline too, up to the vial's three. {dew, cap, next_s, has}
func dew_state(c) -> Dictionary:
	var k: Dictionary = ContentDB.config("garden").get("dew", {})
	var has := tool_power(c, "garden_dew") > 0.0
	if not (c.crafting.get("dew") is Dictionary): c.crafting["dew"] = {"count": 0, "last": 0.0}
	var d: Dictionary = c.crafting.dew
	var every := float(k.get("every_s", 86400))
	var cap := int(k.get("cap", 3))
	if not has: return {"dew": 0, "cap": cap, "next_s": 0.0, "has": false}
	var now := Clock.now_utc()
	if float(d.last) <= 0.0: d.last = now
	var el := Clock.elapsed_since(float(d.last))
	if not el.valid: d.last = now
	var n := int(floor(float(el.elapsed) / every)) if el.valid else 0
	if n > 0:
		d.count = mini(cap, int(d.count) + n)
		d.last = float(d.last) + n * every
	if int(d.count) >= cap: d.last = now   # a full vial doesn't bank time toward the next drop
	return {"dew": int(d.count), "cap": cap, "next_s": maxf(0.0, float(d.last) + every - now), "has": true}

## A drop of dew ages the herb in a bed one tier, as far as the land's Qi allows (a thousand years in the valley).
func use_dew(c, key: String) -> Dictionary:
	var why := _bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var ds := dew_state(c)
	if int(ds.dew) <= 0: return fail("no_dew", {"text": Tx.t("sim.crafting.no_dew")})
	var rec := settle_bed(c, key)
	if str(rec.herb) == "": return fail("empty")
	var older: Array = HerbRules.older_than(str(rec.herb))
	var cap_age := int(ContentDB.config("garden").get("dew", {}).get("valley_age_cap", 1000))
	if older.is_empty() or HerbRules.item_age(str(older[0])) > cap_age: return fail("age_cap", {"text": Tx.t("sim.crafting.dew_age_cap")})
	if not bed_holds(c, key, str(older[0])): return fail("soil", {"text": Tx.t("sim.crafting.soil_too_poor") % ContentDB.item_name(str(older[0]))})
	c.crafting.dew.count = int(c.crafting.dew.count) - 1
	var was := str(rec.herb)
	rec.herb = str(older[0])
	emit("herb_aged", {"actor": c.id, "bed": key, "from": was, "herb": str(rec.herb), "age": HerbRules.item_age(str(rec.herb))})
	return ok({"herb": str(rec.herb)})

## A Qi spring gives three bottles a reset day (S45).
func bottle_spring_water(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "herb_garden"): return fail("locked")
	var per := int(ContentDB.config("garden").get("water", {}).get("per_day", 3))
	var day := Clock.reset_day(Clock.now_utc())
	if not (c.crafting.get("spring") is Dictionary) or int(c.crafting.spring.get("day", -1)) != day: c.crafting["spring"] = {"day": day, "count": 0}
	if int(c.crafting.spring.count) >= per: return fail("spent", {"text": Tx.t("sim.crafting.spring_spent")})
	game.inventory.apply_add(c.id, "spring_water", 1, "spring")
	c.crafting.spring.count = int(c.crafting.spring.count) + 1
	var left := per - int(c.crafting.spring.count)
	emit("spring_bottled", {"actor": c.id, "left": left})
	return ok({"text": Tx.t("sim.crafting.spring_bottled") % left, "left": left})

# ------------------------------------------------------------------ processing racks (S45)
## Herbs on the drying rack: [{kind, herb, count, done}]. They finish on the clock, offline too.
func racks(c) -> Array:
	if not (c.crafting.get("racks") is Array): c.crafting["racks"] = []
	return c.crafting.racks

func start_rack(c, kind: String, herb: String, count: int) -> Dictionary:
	var g: Dictionary = ContentDB.config("garden").get("racks", {})
	var rk: Dictionary = g.get(kind, {}) if g.get(kind) is Dictionary else {}
	if rk.is_empty(): return fail("unknown_rack")
	if tool_power(c, "alchemy") <= 0.0: return fail("no_rack", {"text": Tx.t("sim.crafting.need_drying_rack")})
	if racks(c).size() >= int(g.get("slots", 2)): return fail("racks_full", {"text": Tx.t("sim.crafting.racks_full")})
	if str(ContentDB.item(herb).get("type", "")) != "herb": return fail("not_herb")
	count = clampi(count, 1, int(g.get("max", 10)))
	if game.inventory.count_prep(c, herb, "") < count: return fail("too_few", {"text": Tx.t("sim.crafting.rack_too_few") % ContentDB.item_name(herb)})
	var jars := 0
	if rk.has("needs"):
		jars = int(ceil(count / float(rk.get("per", 5))))
		if c.inventory.count(str(rk.needs)) < jars: return fail("needs", {"text": Tx.t("sim.crafting.rack_needs") % [jars, ContentDB.item_name(str(rk.needs))]})
		game.inventory.apply_remove(c.id, str(rk.needs), jars, "rack")
	game.inventory.take_ranked(c.id, herb, count, "rack", func(st): return (0 if str(st.get("prep", "")) == "" else 2) + (1 if st.get("unappraised", false) else 0))
	var job := {"kind": kind, "herb": herb, "count": count, "done": Clock.now_utc() + float(rk.get("hours", 1)) * 3600.0}
	racks(c).append(job)
	emit("rack_started", {"actor": c.id, "kind": kind, "herb": herb, "count": count, "seconds": float(job.done) - Clock.now_utc()})
	return ok({"done": float(job.done)})

## Takes every finished rack's herbs off: they come back marked steamed or wine-soaked.
func collect_racks(c) -> Dictionary:
	var now := Clock.now_utc()
	var got := 0
	for job in racks(c).duplicate():
		if float(job.done) > now: continue
		game.inventory.apply_add(c.id, str(job.herb), int(job.count), "rack", {"prep": str(job.kind)})
		racks(c).erase(job)
		got += int(job.count)
		emit("rack_collected", {"actor": c.id, "kind": str(job.kind), "herb": str(job.herb), "count": int(job.count)})
	if got == 0: return fail("nothing_ready")
	return ok({"count": got})

# ------------------------------------------------------------------ garden raids (S45)
## Once a reset day, an unguarded planted bed may be raided while you are away: pests halve its growth, a thief takes
## the herb. Checked when you come back (enter the world, or a room). Returns the raids.
func check_raids(c) -> Array:
	var g: Dictionary = ContentDB.config("garden").get("raids", {})
	var now := Clock.now_utc()
	var today := Clock.reset_day(now)
	var out: Array = []
	for key in beds(c).keys():
		var rec: Dictionary = beds(c)[key]
		if str(rec.get("herb", "")) == "": continue
		var last := int(rec.get("raid_day", -1))
		rec.raid_day = today
		if last < 0 or today <= last: continue
		var rng := Rng.stream(c.id, "garden")
		for d in range(last + 1, mini(today, last + int(g.get("max_days", 14))) + 1):
			if _bed_guarded(c, str(key), d): continue
			if rng.randf() >= float(g.get("chance", 0.08)): continue
			settle_bed(c, str(key))
			var thief := rng.randf() < float(g.get("thief_share", 0.5))
			var herb := str(rec.herb)
			if thief: rec.herb = ""
			else: rec.progress = float(rec.progress) * 0.5
			out.append({"bed": str(key), "kind": "thief" if thief else "pests", "herb": herb})
			emit("garden_raided", {"actor": c.id, "bed": str(key), "kind": "thief" if thief else "pests", "herb": herb})
			game.mail.apply_send(c.id, "garden_raid_" + ("thief" if thief else "pests"), [], {"herb": ContentDB.item_name(herb),
				"place": str(ContentDB.room(str(key).get_slice(":", 0)).get("name", ""))})
			if thief: break
	return out

## A pet on Guard duty, or a Protection or Concealment formation burning in the bed's room that day, keeps raiders off.
func _bed_guarded(c, key: String, day: int) -> bool:
	if not game.pets.guard_pet(c).is_empty(): return true
	var guards: Array = ContentDB.config("garden").get("raids", {}).get("guards", [])
	var day_start := day * 86400.0 - Clock.tz_offset_s() + float(ContentDB.curve("resets.daily_hour", 4)) * 3600.0
	for f in _state_formations(c):
		if str(f.get("type", "")) in guards and str(f.get("room", "")) == key.get_slice(":", 0) and float(f.get("until_utc", 0.0)) >= day_start: return true
	return false

func _state_formations(c) -> Array:
	var list = c.crafting.get("formations", [])
	return list if list is Array else []

# ------------------------------------------------------------------ transplanting (S45)
## Can this character dig up a rare herb? A Spirit Spade and Expert gathering.
func can_transplant(c) -> bool:
	var need := str(ContentDB.config("garden").get("transplant", {}).get("rank", "expert"))
	return tool_power(c, "transplant") > 0.0 and rank_index(rank_of(c, "herb_gathering")) >= rank_index(need)

## The odds it dies on the way: 25% at Expert, 5% less per rank above.
func transplant_death(c) -> float:
	var t: Dictionary = ContentDB.config("garden").get("transplant", {})
	var above := rank_index(rank_of(c, "herb_gathering")) - rank_index(str(t.get("rank", "expert")))
	return maxf(0.0, float(t.get("death", 0.25)) - float(t.get("per_rank", 0.05)) * maxi(0, above))

## Dig a rare herb up whole and move it, at its age, to the first free bed that can hold it (grown and ready).
## Picked before it ripens it is a tier younger, as a pick would be. Either way the node is spent until its next
## ripening.
func transplant(c, object_id: String) -> Dictionary:
	var rt: RoomRuntime = game.room_rt
	if rt == null: return fail("no_room")
	var o := rt.object_def(object_id)
	if o.is_empty() or str(o.get("type", "")) != "herb_patch" or not o.has("ripen"): return fail("not_rare")
	if not can_transplant(c): return fail("cannot", {"text": Tx.t("sim.crafting.transplant_needs")})
	var avail: Dictionary = game.world.object_available(c, o)
	if not avail.ok: return fail("unavailable", {"text": str(avail.get("text", ""))})
	var guard: String = game.world.herb_guard_text(c, o)
	if guard != "": return fail("guarded", {"text": guard})
	var now := Clock.now_utc()
	var herb := HerbRules.aged_down(str(o.item), 0 if bool(HerbRules.ripen_state(o, now).ripe) else 1)
	var target := ""
	for key in beds(c).keys() + _known_bed_keys(c):
		if str(settle_bed(c, str(key)).herb) == "" and bed_holds(c, str(key), herb):
			target = str(key)
			break
	if target == "": return fail("no_bed", {"text": Tx.t("sim.crafting.no_free_bed") % ContentDB.item_name(herb)})
	game.world.apply_node_depleted(c, object_id, maxf(60.0, HerbRules.regrow_at(o, now) - now))
	var died := Rng.stream(c.id, "garden").randf() < transplant_death(c)
	if not died:
		var rec := bed_record(c, target)
		rec.herb = herb
		rec.progress = 1.0
		rec.grow_s = float(ContentDB.config("garden").get("grow_hours", {}).get(HerbRules.family(herb), 4)) * 3600.0
		rec.updated = now
		rec.raid_day = Clock.reset_day(now)
	emit("transplant_result", {"actor": c.id, "object": object_id, "herb": herb, "ok": not died, "bed": target})
	return ok({"herb": herb, "survived": not died, "bed": target})

## Every bed the character can use, in rooms it has been to (a transplant looks for room in any of them).
func _known_bed_keys(c) -> Array:
	var out: Array = []
	for rid in ContentDB.rooms:
		if not game.account.visited_rooms.has(rid): continue
		for key in room_beds(c, str(rid)):
			if not out.has(key): out.append(key)
	return out

## Fishing result from the mini-game (S33). The authority rolls the catch.
func catch_fish(c, object_id: String, result: Dictionary) -> Dictionary:
	var p: Dictionary = pending.get(c.id, {})
	if p.is_empty() or str(p.object) != object_id: return fail("not_started")
	pending.erase(c.id)
	var reaction := float(result.get("reaction_s", 9.9))
	var tension_ok := bool(result.get("tension_ok", false))
	var window: float = (0.6 + 0.1 * (tool_power(c, "fishing") - 1.0)) * (1.0 + game.pets.trait_bonus(c, "fish_chance") + game.calendar.fishing_bonus())
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

# ------------------------------------------------------------------ the five-screen furnace (S15, S44)
## The page walks the first two screens on its own: Ingredients (the recipe, the batch, what Spirit Sense tells of the
## herbs) and the Furnace (the fire and the array under it). Lighting the furnace starts the refine here, which draws the
## plan the next three screens are played from: Extraction (each herb held in a swaying heat band while its impurities
## are tapped away), Fusion (the essences merged in the recipe's order, the array turned at each mark) and Condensation
## (a ring closing on the pill). The page sends what the hand did (refine_input) and this scores it within range. A
## scorched herb is lost (early mistakes waste ingredients); a cracked pill loses the whole batch. The pill tribulation
## (Heaven grade and up) is the sixth screen.
func furnace_game() -> Dictionary:
	return upkeep("furnace_game", {})

func refine_session(c) -> Dictionary:
	return refines.get(c.id, {})

## The array that answers a recipe's principal herb: Still Water under a hot one, Rising Flame under a cold one; "" when
## the principal is neither and either array serves.
func suited_array(recipe_id: String, substitute: Dictionary = {}) -> String:
	var principal := _principal(ContentDB.entry("recipes", recipe_id), inputs_with(recipe_id, substitute))
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
	return minf(float(k.get("band_max", 0.5)), float(k.get("band", 0.2)) * band_mult(c, fire) * (1.0 + c.stats.value("crafting_control"))
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
		for row in with_aged(c, [inp], count).inputs:
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
	var furnace := furnace_of(c)
	if furnace.get("cracked", false): return Tx.t("sim.crafting.furnace_cracked") % ContentDB.item_name(str(furnace.id))
	if count > int(furnace.get("batch", 1)):
		return Tx.t("sim.crafting.furnace_batch") % [ContentDB.item_name(str(furnace.get("id", ""))), int(furnace.get("batch", 1))]
	var need_fire := str(r.get("fire", ""))
	if need_fire != "" and fire != need_fire: return Tx.t("sim.crafting.needs_fire") % Tx.t("ui.crafts.fire_" + need_fire)
	if not substitute.is_empty():
		var sw := substitute_check(c, recipe_id, str(substitute.get("from", "")), str(substitute.get("to", "")))
		if sw != "": return sw
	return recipe_check(c, recipe_id, count, "alchemy", inputs_with(recipe_id, substitute))

## Lighting the furnace (screen 2 done): checks the refine, then draws its plan on the furnace_plan stream (the
## quality roll's own stream is untouched). A refine already burning is put out first; its herbs in the fire are lost.
func start_refine(c, recipe_id: String, count: int, fire: String, array: String, substitute: Dictionary = {}) -> Dictionary:
	_settle_tribulation(c)
	if refines.has(c.id): cancel_refine(c)
	if not fire in fires_available(c): fire = "charcoal"
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
		var shift := float(upkeep("nature_shift", 0.08))
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
	refines[c.id] = {"recipe": recipe_id, "count": count, "fire": fire, "array": array, "substitute": substitute.duplicate(), "herbs": herbs,
		"order": order, "marks": marks, "liquid": bool(r.get("liquid", false)), "stage": "extraction", "at": 0, "extraction": [], "fusion": 0.0}
	emit("craft_started", {"actor": c.id, "recipe": recipe_id, "craft": "alchemy", "count": count})
	return ok({"plan": (refines[c.id] as Dictionary).duplicate(true)})

static func _role_rank(roles: Array, i: int) -> int:
	var at := ["principal", "minister", "assistant", "envoy"].find(str(roles[i]) if i < roles.size() else "")
	return at if at >= 0 else 9

## One screen's result from the page. Extraction: {herb, held (the share of the time the heat stayed in the band),
## taps (impurities struck)}. Fusion: {order (the herbs as merged), marks (how far off each turn of the array was, as a
## share of the bar)}. Condensation: {offset (seconds from the ring meeting the pill; early is negative)}.
func refine_input(c, step: String, value: Dictionary) -> Dictionary:
	var s: Dictionary = refines.get(c.id, {})
	if s.is_empty(): return fail("no_refine")
	if step != str(s.stage): return fail("wrong_step")
	match step:
		"extraction": return _extract(c, s, value)
		"fusion": return _fuse(c, s, value)
		"condensation": return _condense(c, s, value)
	return fail("wrong_step")

static func _step_grade(score: float) -> String:
	var k: Dictionary = ContentDB.curve("craft_step", {})
	return "perfect" if score >= float(k.get("perfect", 0.85)) else ("good" if score >= float(k.get("good", 0.5)) else "miss")

## The bag rows one herb of the batch takes (an older stand-in included), and whether they are all there.
func _herb_rows(c, herb: Dictionary) -> Dictionary:
	var rows: Array = with_aged(c, [{"item": str(herb.item), "count": int(herb.count)}], 1).inputs
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
	var grade := _step_grade(score)
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
		refines.erase(c.id)
		return blast(c, str(s.recipe), with_aged(c, inputs, int(s.count)).inputs, 1, clash)
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
	var grade := _step_grade(score)
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
		refines.erase(c.id)
		var lost := _lose_rows(c, with_aged(c, inputs_with(str(s.recipe), s.substitute), int(s.count)).inputs, "refine_cracked")
		emit("craft_step_result", {"actor": c.id, "recipe": str(s.recipe), "step": 3, "score": 0.0, "grade": "cracked"})
		return ok({"score": 0.0, "grade": "cracked", "cracked": true, "lost": lost, "text": Tx.t("sim.crafting.pill_cracked")})
	var score := 1.0
	if off < -perfect: score = clampf(1.0 - (-off - perfect) / maxf(0.01, float(k.get("early_span", 0.7))), float(k.get("weak_floor", 0.2)), 1.0)
	elif off > perfect: score = clampf(1.0 - 0.5 * (off - perfect) / maxf(0.01, late - perfect), 0.0, 1.0)
	var grade := _step_grade(score)
	emit("craft_step_result", {"actor": c.id, "recipe": str(s.recipe), "step": 3, "score": score, "grade": grade})
	return _finish(c, s, [score], grade, score)

## The last screen is done: the pills are rolled from the three screens' scores (Extraction the mean of its herbs).
func _finish(c, s: Dictionary, last: Array, grade: String, score: float) -> Dictionary:
	refines.erase(c.id)
	var ext := 0.0
	for x in s.extraction: ext += float(x)
	ext /= maxf(1.0, (s.extraction as Array).size())
	var scores: Array = [ext]
	if not s.liquid: scores.append(float(s.fusion))
	scores.append_array(last)
	var res := craft(c, str(s.recipe), int(s.count), scores, "alchemy", str(s.fire), s.substitute, true)
	res.step_score = score
	res.grade = grade
	res.scores = scores
	return res

## Putting out the fire mid-refine: the herbs already in it are lost; the rest stay in the bag.
func cancel_refine(c) -> Dictionary:
	var s: Dictionary = refines.get(c.id, {})
	if s.is_empty(): return fail("no_refine")
	refines.erase(c.id)
	var lost: Array = []
	for i in mini(int(s.at), (s.herbs as Array).size()):
		lost.append_array(_lose_rows(c, _herb_rows(c, s.herbs[i]).rows, "refine_abandoned"))
	return ok({"lost": lost})

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
		if craft_kind == "alchemy": c.cooldowns.erase("grain_blessing")   # the Hundred-Year Wine blesses one batch (S49)
	var used := _consume(c, recipe_id, aged.inputs, _principal(r, inputs))
	# S45: an unappraised fake herb in the batch spoils the pill more often than not.
	if craft_kind == "alchemy" and used.fake and Rng.stream(c.id, "garden").randf() < float(ContentDB.config("garden").get("fakes", {}).get("flawed", 0.6)):
		quality = "flawed"
	if craft_kind == "alchemy" and fire == "beast_fire": game.inventory.apply_remove(c.id, _core_to_burn(c), 1, "beast_fire")
	# S44 pill tribulation: a Heaven-grade (or better) pill that reaches Halo or Soul at the furnace must first come
	# through the bolts; its pills wait until it does (the page plays the screen; other callers keep the roll).
	if craft_kind == "alchemy" and live and quality in ["pill_halo", "pill_soul"] \
			and StatRules.grade_index(str(r.get("grade", "plain"))) >= StatRules.grade_index("heaven"):
		return begin_tribulation(c, recipe_id, count, quality, fire, furnace, str(used.prep))
	return _grant(c, recipe_id, count, quality, fire, craft_kind, furnace, str(used.prep))

## The recipe's principal herb: the input its roles mark principal, else its first herb.
func _principal(r: Dictionary, inputs: Array) -> String:
	var roles: Array = r.get("roles", [])
	var i := roles.find("principal")
	if i >= 0 and i < inputs.size(): return str(inputs[i].item)
	for inp in inputs:
		if str(ContentDB.item(str(inp.item)).get("type", "")) == "herb": return str(inp.item)
	return ""

## Takes a craft's inputs from the bag (S45). The principal herb comes from a steamed or wine-soaked stack when there
## is enough of one, and then the pills carry that prep; other herbs are taken plain first and sealed stacks last.
## Returns {prep, fake}.
func _consume(c, recipe_id: String, rows: Array, principal: String) -> Dictionary:
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
func _grant(c, recipe_id: String, count: int, quality: String, fire: String, craft_kind: String, furnace: Dictionary, prep := "") -> Dictionary:
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
func begin_tribulation(c, recipe_id: String, count: int, quality: String, fire: String, furnace: Dictionary, prep := "") -> Dictionary:
	var k: Dictionary = upkeep("tribulation", {})
	var above := StatRules.grade_index(str(ContentDB.entry("recipes", recipe_id).get("grade", "heaven"))) - StatRules.grade_index("heaven")
	var n := clampi(int(k.get("bolts", 3)) + int(k.get("per_grade", 2)) * above, 1, int(k.get("max", 9)))
	var rng := Rng.stream(c.id, "crafting")
	var times: Array = []
	var t := float(k.get("first_s", 1.2))
	for i in n:
		times.append(snappedf(t, 0.01))
		t += rng.randf_range(float(k.get("gap_min_s", 0.7)), float(k.get("gap_max_s", 1.3)))
	tribulations[c.id] = {"recipe": recipe_id, "count": count, "quality": quality, "fire": fire, "furnace": furnace.duplicate(), "prep": prep,
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
	var res := _grant(c, str(tr.recipe), int(tr.count), after, str(tr.fire), "alchemy", tr.furnace, str(tr.get("prep", "")))
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
	var res := _grant(c, str(tr.recipe), int(tr.count), quality, str(tr.fire), "alchemy", tr.furnace, str(tr.get("prep", "")))
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
	var cost := reroll_cost(inst, c)
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
		# S47 weapon awakening: a Heaven-grade (or better) weapon at +10 is ready to be woken.
		if lvl + 1 >= 10 and awaken_grade_ok(str(inst.id)): game.quest.apply_flag(c.id, "forged_plus10")
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

## What rerolling an item's affixes costs: {essence, taels}; a locked affix doubles it. S10 Insight 25: one reroll a
## week is free ({free: true}).
func reroll_cost(inst: Dictionary, c = null) -> Dictionary:
	if c != null and free_reroll_ready(c): return {"essence": 0, "taels": 0, "free": true}
	var gi := StatRules.grade_index(str(ContentDB.item(str(inst.id)).get("grade", "plain")))
	var ess: Array = upkeep("reroll_essence", [1])
	var mult := int(upkeep("lock_mult", 2)) if int(inst.get("locked_affix", -1)) >= 0 else 1
	return {"essence": int(ess[mini(gi, ess.size() - 1)]) * mult, "taels": int(upkeep("reroll_taels", 60)) * (gi + 1) * mult}

func free_reroll_ready(c) -> bool:
	return StatRules.gate_flag(c, "extra_reroll") and int(c.cooldowns.get("free_reroll_wk", -1)) != Clock.reset_week(Clock.now_utc())

## Reroll (S47 affix lock): every affix but the locked one is rolled again on the affix stream. The new roll waits
## beside the old one until you choose which to keep.
func reroll(c, uid: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var at := locate(c, uid)
	if at.is_empty() or not ContentDB.is_equipment(str(at.inst.id)): return fail("not_equipment")
	var inst: Dictionary = at.inst
	if (inst.get("affixes", []) as Array).is_empty(): return fail("no_affixes", {"text": Tx.t("sim.crafting.no_affixes")})
	var cost := reroll_cost(inst, c)
	if c.inventory.count("refining_essence") < int(cost.essence): return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(cost.essence), ContentDB.item_name("refining_essence")]})
	if game.economy.balance("silver_tael") < int(cost.taels): return fail("insufficient_funds")
	if cost.get("free", false): c.cooldowns["free_reroll_wk"] = Clock.reset_week(Clock.now_utc())
	if int(cost.essence) > 0: game.inventory.apply_remove(c.id, "refining_essence", int(cost.essence), "reroll")
	if int(cost.taels) > 0: game.economy.apply_currency("silver_tael", -int(cost.taels), "reroll")
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

## S47 weapon awakening (v1.1): a weapon of Heaven grade or better, forged to +10, wakes at a forge with a Weapon Soul
## Crystal for one whose Dao of that weapon has reached Explanation (tier 4). It glows, and strikes on its own every so
## many blows: its family's skill, or a legend's own.
static func awaken_grade_ok(item_id: String) -> bool:
	var def := ContentDB.item(item_id)
	return str(def.get("slot", "")) == "weapon" and StatRules.grade_index(str(def.get("grade", "plain"))) >= StatRules.grade_index("heaven")

static func awakened_skill(item_id: String) -> Dictionary:
	var def := ContentDB.item(item_id)
	if def.has("legend"): return def.legend.get("skill", {})
	return ContentDB.entry("weapon_families", str(def.get("family", ""))).get("awakened", {})

## Why a piece cannot be awakened now ("" when it can).
func awaken_check(c, inst: Dictionary) -> String:
	if inst.is_empty() or not awaken_grade_ok(str(inst.id)): return Tx.t("sim.crafting.awaken_grade")
	if inst.get("awakened", false): return Tx.t("sim.crafting.awaken_done")
	if awakened_skill(str(inst.id)).is_empty(): return Tx.t("sim.crafting.awaken_grade")
	if int(inst.get("enhance", 0)) < 10: return Tx.t("sim.crafting.awaken_plus10")
	var dao := str(ContentDB.entry("weapon_families", str(ContentDB.item(str(inst.id)).get("family", ""))).get("dao", ""))
	if int(c.cultivator.daos.get(dao, {}).get("tier", 0)) < 4: return Tx.t("sim.crafting.awaken_dao") % ContentDB.name_of("daos", dao)
	if c.inventory.count("weapon_soul_crystal") <= 0: return Tx.t("sim.crafting.awaken_crystal")
	if not station_near(c, ["forge_anvil"]): return Tx.t("sim.crafting.you_need_a") % "forge"
	return ""

func awaken_weapon(c, intent: Dictionary) -> Dictionary:
	var at := locate(c, int(intent.get("uid", -1)))
	if at.is_empty():
		var slot := str(intent.get("slot", ""))
		var index := int(intent.get("index", -1))
		if slot != "" and c.inventory.equipped.get(slot) != null: at = {"inst": c.inventory.equipped[slot], "slot": slot, "index": -1}
		elif index >= 0 and index < c.inventory.bag.size() and c.inventory.bag[index] != null: at = {"inst": c.inventory.bag[index], "slot": "", "index": index}
	if at.is_empty(): return fail("not_equipment")
	var inst: Dictionary = at.inst
	var why := awaken_check(c, inst)
	if why != "": return fail("cannot", {"text": why})
	game.inventory.apply_remove(c.id, "weapon_soul_crystal", 1, "awaken")
	inst.awakened = true
	var sk := awakened_skill(str(inst.id))
	game.quest.apply_flag(c.id, "awakened:" + str(inst.id))
	emit("weapon_awakened", {"actor": c.id, "item": str(inst.id), "skill": str(sk.get("name", "")), "legend": ContentDB.item(str(inst.id)).has("legend")})
	emit("system_used", {"actor": c.id, "system": "awaken_weapon"})
	return ok({"skill": str(sk.get("name", ""))})

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

# ------------------------------------------------------------------ S44/S49 the guilds
## The three profession associations (guilds.json): the Alchemist Guild (S44), the Forge Guild and the Formation Guild
## (S49). Each keys its exams, commissions and shop by the craft it certifies.
func guild_def(craft: String) -> Dictionary:
	for g in ContentDB.all("guilds"):
		if str(g.get("craft", "")) == craft: return g
	return {}

## The guilds whose gate this character has opened, in data order.
func guilds_open(c) -> Array:
	var out: Array = []
	for g in ContentDB.all("guilds"):
		if Unlocks.is_unlocked(c.id, str(g.get("unlock", ""))): out.append(g)
	return out

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

## Why a rank's exam cannot be sat here and now ("" when it can): its realm, then its hall. The Master exams are sat
## at Cloudgate Port.
func exam_block(c, rk: Dictionary) -> String:
	if rk.has("requires") and not RequirementRules.passes(rk.requires, game.ctx(c)): return RequirementRules.first_failure_text(rk.requires, game.ctx(c))
	var hall := str(rk.get("hall", ""))
	if hall != "" and (game.room_rt == null or game.room_rt.room_id != hall): return Tx.t("sim.crafting.exam_hall") % ContentDB.name_of("rooms", hall)
	return ""

## Whether a finished craft counts toward a rank's exam: its own recipe, or (the Forge Guild) any recipe of at least
## the rank's grade whose piece fits the rank's slot.
static func exam_counts(rk: Dictionary, recipe_id: String) -> bool:
	if rk.has("recipe"): return recipe_id == str(rk.recipe)
	var r := ContentDB.entry("recipes", recipe_id)
	if r.is_empty() or StatRules.grade_index(str(r.get("grade", "plain"))) < StatRules.grade_index(str(rk.get("grade", "plain"))): return false
	var slot := str(rk.get("slot", ""))
	return slot == "" or str(ContentDB.item(str(r.outputs[0].item)).get("slot", "")) == slot

func take_exam(c, craft: String, rank: String) -> Dictionary:
	var g := guild_def(craft)
	var gate := str(g.get("unlock", "alchemist_guild"))
	if g.is_empty() or not Unlocks.is_unlocked(c.id, gate): return fail("locked", {"text": Unlocks.locked_text(gate)})
	var nxt := next_guild_rank(c, craft)
	if nxt.is_empty() or (rank != "" and str(nxt.id) != rank): return fail("rank", {"text": Tx.t("sim.crafting.exam_not_yours")})
	var why := exam_block(c, nxt)
	if why != "": return fail("not_here", {"text": why})
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

## A furnace, anvil or etching that finishes while the candle burns counts (the auto-refine queue never does).
func _on_craft_completed(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or p.get("auto", false): return
	var ex: Dictionary = c.crafting.get("guild_exam", {})
	if ex.is_empty() or str(p.get("craft", "")) != str(ex.craft): return
	var rk := guild_rank_def(str(ex.craft), str(ex.rank))
	if not exam_counts(rk, str(p.get("recipe", ""))) or exam_left(c) <= 0.0: return
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

# ------------------------------------------------------------------ S44/S49 commissions
## The day's number (commissions refresh each morning).
static func commission_day() -> int:
	return int(floor(Clock.now_utc() / 86400.0))

## Where a guild's board keeps its day (the Alchemist Guild's keeps its first key, so old saves carry on).
static func _board_key(craft: String) -> String:
	return "commission_state" if craft == "alchemy" else "commission_state_" + craft

## A fifth of the zone's daily income target, per guild: Level x 60 taels an hour for three hours of play (S39).
func commission_cap(c, craft := "alchemy") -> int:
	var k: Dictionary = guild_def(craft).get("commissions", {})
	return int(float(k.get("cap_share", 0.2)) * float(k.get("income_per_level_hour", 60)) * float(k.get("play_hours", 3)) * ProgressionRules.level(c))

func commission_paid_today(c, craft := "alchemy") -> int:
	var cm: Dictionary = c.crafting.get(_board_key(craft), {})
	return int(cm.get("paid", 0)) if int(cm.get("day", -1)) == commission_day() else 0

## What a guild takes orders for: pills for the Alchemist Guild, worn pieces for the Forge Guild, plates for the Formation Guild.
func _orderable(craft: String, item: String) -> bool:
	match craft:
		"alchemy": return ContentDB.item(item).has("pill")
		"smithing": return ContentDB.is_equipment(item)
	return true

## Today's three orders on a guild's board, drawn from what this character knows how to make.
func commissions(c, craft := "alchemy") -> Array:
	var rank := guild_rank(c, craft)
	if rank == "": return []
	var day := commission_day()
	var key := _board_key(craft)
	var cm: Dictionary = c.crafting.get(key, {})
	if int(cm.get("day", -1)) == day: return cm.get("orders", [])
	var k: Dictionary = guild_def(craft).get("commissions", {})
	var known: Array = []
	for r in ContentDB.all("recipes"):
		if str(r.craft) == craft and knows(c, str(r.id)) and _orderable(craft, str(r.outputs[0].item)): known.append(str(r.id))
	known.sort()
	var rng := Rng.stream(c.id, "commission" if craft == "alchemy" else "commission_" + craft)   # drawn once each morning
	var orders: Array = []
	var mult := float(guild_rank_def(craft, rank).get("pay_mult", 1.2))
	var prefix := "c" if craft == "alchemy" else craft + "_"
	for i in int(k.get("per_day", 3)):
		if known.is_empty(): break
		var rid: String = known[rng.randi_range(0, known.size() - 1)]
		var item := str(ContentDB.entry("recipes", rid).outputs[0].item)
		var cnt: Array = k.get("count", [1, 3])
		var n := rng.randi_range(int(cnt[0]), int(cnt[1]))
		orders.append({"id": "%s%d_%d" % [prefix, day, i], "item": item, "count": n, "quality": "common",
			"pay": int(round(LootRules.buy_price(item) * mult * n)), "accepted": false, "done": false})
	c.crafting[key] = {"day": day, "orders": orders, "paid": 0}
	return orders

## An order on any open board: {order, craft}, or {} when there is none.
func _order(c, id: String) -> Dictionary:
	for g in ContentDB.all("guilds"):
		for o in commissions(c, str(g.craft)):
			if str(o.id) == id: return {"order": o, "craft": str(g.craft)}
	return {}

func accept_commission(c, id: String) -> Dictionary:
	var found := _order(c, id)
	if found.is_empty() or found.order.get("done", false): return fail("no_order")
	found.order.accepted = true
	return ok()

func deliver_commission(c, id: String, pay: String) -> Dictionary:
	var found := _order(c, id)
	if found.is_empty() or found.order.get("done", false): return fail("no_order")
	var o: Dictionary = found.order
	var craft: String = found.craft
	if not o.get("accepted", false): return fail("not_accepted", {"text": Tx.t("sim.crafting.commission_accept_first")})
	# Pieces or pills of the order's quality or better, from any stacks.
	var have := 0
	for s in c.inventory.bag:
		if s != null and str(s.id) == str(o.item) and quality_rank(str(s.get("quality", "common"))) >= quality_rank(str(o.quality)): have += int(s.get("count", 1))
	if have < int(o.count): return fail("materials", {"text": Tx.t("sim.crafting.missing") % ContentDB.item_name(str(o.item))})
	var left := int(o.count)
	for i in c.inventory.bag.size():
		if left <= 0: break
		var s = c.inventory.bag[i]
		if s == null or str(s.id) != str(o.item) or quality_rank(str(s.get("quality", "common"))) < quality_rank(str(o.quality)): continue
		var take := mini(left, int(s.get("count", 1)))
		game.inventory.apply_remove_index(c.id, i, take, "commission")
		left -= take
	o.done = true
	var room := maxi(0, commission_cap(c, craft) - commission_paid_today(c, craft))
	var paid := mini(int(o.pay), room)
	var cm: Dictionary = c.crafting.get(_board_key(craft), {})
	cm.paid = commission_paid_today(c, craft) + paid
	var k: Dictionary = guild_def(craft).get("commissions", {})
	if pay == "contribution":
		var contrib := int(round(paid * float(k.get("contribution_per_tael", 0.1))))
		if contrib > 0: game.apply_effects(c.id, [{"kind": "add_contribution", "amount": contrib}], "commission")
	elif paid > 0:
		game.economy.apply_currency("silver_tael", paid, "commission")
	emit("commission_completed", {"actor": c.id, "id": id, "craft": craft, "item": str(o.item), "count": int(o.count), "paid": paid, "pay": pay,
		"capped": paid < int(o.pay)})
	return ok({"paid": paid, "capped": paid < int(o.pay)})

func tick(_delta: float) -> void:
	# S44: a guild exam whose candle burns out fails.
	var ac = game.active()
	if ac != null and not ac.crafting.get("guild_exam", {}).is_empty() and exam_left(ac) <= 0.0:
		var ex: Dictionary = ac.crafting.guild_exam
		ac.crafting["guild_exam"] = {}
		emit("guild_exam_failed", {"actor": ac.id, "craft": str(ex.craft), "rank": str(ex.rank), "made": int(ex.made)})
	pass
