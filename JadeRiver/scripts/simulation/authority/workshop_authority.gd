class_name WorkshopAuthority
extends Authority
## S16 · The crafts that are not recipes at a station: appraisal, formations,
## healing, puppetry, research and teaching. Numbers come from professions.json
## and formations.json. Each use emits `system_used` so guided quests advance from
## events, never from UI code.
##
## State lives on the character under `crafting`: formations [{type, room, until_utc}],
## puppets [{blueprint, collected_utc}], healing {day, treated}, teaching {until_utc}.

func intents() -> Array:
	return ["appraise_item", "place_formation", "remove_formation", "treat_patient", "build_puppet", "collect_puppets",
		"restore_manual", "teach_disciple", "inscribe"]

func subscribe() -> void:
	GameEvents.subscribe("room_entered", _on_room_entered, 47)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"appraise_item": return appraise(c, int(intent.get("index", -1)))
		"place_formation": return place_formation(c, str(intent.get("formation", "")))
		"remove_formation": return remove_formation(c, int(intent.get("index", -1)))
		"treat_patient": return treat_patient(c)
		"build_puppet": return build_puppet(c, str(intent.get("blueprint", "")))
		"collect_puppets": return collect_puppets(c)
		"restore_manual": return restore_manual(c)
		"teach_disciple": return teach(c, int(intent.get("index", -1)), str(intent.get("dao", "")))
		"inscribe": return game.crafting.craft(c, str(intent.get("recipe", "")), maxi(1, int(intent.get("count", 1))), [], "formations")
	return fail("unknown_intent")

func prof(id: String) -> Dictionary:
	return ContentDB.entry("professions", id)

func _state(c, key: String, fallback):
	if not c.crafting.has(key): c.crafting[key] = fallback
	return c.crafting[key]

## True when one of `npcs` stands in the character's current room.
func npc_here(c, npcs: Array) -> bool:
	if game.room_rt == null: return false
	for o in game.room_rt.def.get("objects", []):
		if str(o.get("type", "")) == "npc" and str(o.get("npc", "")) in npcs: return true
	return false

func _weighted(rng: RandomNumberGenerator, rows: Array) -> Dictionary:
	var total := 0.0
	for r in rows: total += float(r.get("weight", 1))
	var roll := rng.randf() * total
	for r in rows:
		roll -= float(r.get("weight", 1))
		if roll <= 0.0: return r
	return rows.back() if not rows.is_empty() else {}

func _used(c, system: String, xp_craft := "", xp := 0.0) -> void:
	if xp_craft != "" and xp > 0.0: game.crafting.add_xp(c, xp_craft, xp)
	emit("system_used", {"actor": c.id, "system": system})

# ------------------------------------------------------------------ appraisal
func appraise(c, index: int) -> Dictionary:
	var p := prof("appraisal")
	if not Unlocks.is_unlocked(c.id, "appraisal"): return fail("locked", {"text": Unlocks.locked_text("appraisal")})
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var id := str(c.inventory.bag[index].id)
	if str(ContentDB.item(id).get("use_action", "")) != "appraise": return fail("not_appraisable")
	# Appraisal Eye (secret art, Qi Kindling 6) sees what a loupe would.
	if game.crafting.tool_power(c, "appraisal") <= 0.0 and not npc_here(c, ["elder_gu", "old_pan"]) and not "appraisal_eye" in c.cultivator.secret_arts:
		return fail("no_tool", {"text": Tx.t("sim.workshop.you_need_an_appraiser_loupe")})
	var r := _weighted(Rng.stream(c.id, "crafting"), p.get("results", []))
	if r.is_empty(): return fail("no_results")
	game.inventory.apply_remove_index(c.id, index, 1, "appraise")
	game.inventory.apply_add(c.id, str(r.item), int(r.get("count", 1)), "appraise")
	game.progression.apply_insight(c.id, "soul", float(p.get("insight_per_use", 0)), "appraise")
	_used(c, "appraise", "appraisal", float(p.get("xp_per_use", 0)))
	var name := ContentDB.item_name(str(r.item))
	log_line(c.id, Tx.t("sim.workshop.appraised") % name, "craft")
	return ok({"item": str(r.item), "count": int(r.get("count", 1)), "text": Tx.t("sim.workshop.it_is") % name})

# ------------------------------------------------------------------ formations (S16)
func active_formations(c) -> Array:
	var now := Clock.now_utc()
	var list: Array = _state(c, "formations", [])
	return list.filter(func(f): return f is Dictionary and float(f.get("until_utc", 0)) > now)

## Sum of one effect over the fuelled formations in the character's current room.
func formation_effect(c, key: String) -> float:
	if c == null: return 0.0
	var room := str(c.position.get("room", ""))
	var total := 0.0
	for f in active_formations(c):
		if str(f.get("room", "")) != room: continue
		total += float(ContentDB.entry("formations", str(f.type)).get("effect", {}).get(key, 0.0))
	return total

func place_formation(c, type: String) -> Dictionary:
	var bp := ContentDB.entry("formations", type)
	if bp.is_empty(): return fail("unknown_formation")
	var unlock := str(bp.get("unlock", "formations"))
	if not Unlocks.is_unlocked(c.id, unlock): return fail("locked", {"text": Unlocks.locked_text(unlock)})
	if game.crafting.tool_power(c, "formations") <= 0.0: return fail("no_tool", {"text": Tx.t("sim.workshop.you_need_a_formation_kit")})
	if game.room_rt == null or game.room_rt.def.get("type", "") == "interior": return fail("bad_room", {"text": Tx.t("sim.workshop.formations_need_open_ground")})
	var fuel := str(bp.get("fuel", "fuel_crystal_low"))
	var need := int(bp.get("nodes", 3)) * int(bp.get("fuel_per_node", 1))
	if c.inventory.count(fuel) < need: return fail("no_fuel", {"text": Tx.t("sim.workshop.needs") % [need, ContentDB.item_name(fuel)]})
	var room := str(c.position.get("room", ""))
	var live := active_formations(c)
	for f in live:
		if str(f.type) == type and str(f.room) == room: return fail("already_placed", {"text": Tx.t("sim.workshop.that_formation_already_stands_here")})
	if live.size() >= int(prof("formations").get("max_active", 2)): return fail("too_many", {"text": Tx.t("sim.workshop.you_can_keep_formations_at") % int(prof("formations").get("max_active", 2))})
	game.inventory.apply_remove(c.id, fuel, need, "formation")
	var hours := minf(float(bp.get("max_hours", 24)), float(need) * float(bp.get("hours_per_crystal", 1.0)))
	live.append({"type": type, "room": room, "until_utc": Clock.now_utc() + hours * 3600.0})
	c.crafting.formations = live
	_apply_room_buffs(c)
	emit("formation_placed", {"actor": c.id, "formation": type, "room": room, "hours": hours})
	_used(c, "formation_placed", "formations", float(prof("formations").get("xp_per_use", 0)))
	log_line(c.id, Tx.t("sim.workshop.placed_h_of_fuel") % [str(bp.get("name", type)), int(hours)], "craft")
	return ok({"hours": hours})

func remove_formation(c, index: int) -> Dictionary:
	var live := active_formations(c)
	if index < 0 or index >= live.size(): return fail("bad_index")
	live.remove_at(index)
	c.crafting.formations = live
	_apply_room_buffs(c)
	return ok()

func _on_room_entered(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", game.active_id)))
	if c != null: _apply_room_buffs(c)

## Protection formations are a stat modifier while the character stands in their room.
func _apply_room_buffs(c) -> void:
	var def_pct := formation_effect(c, "defense_pct")
	if def_pct > 0.0:
		c.stats.add_modifier({"stat": "physical_defense", "op": "pct_add", "value": def_pct, "duration": -1, "source": "formation:protection"})
	else:
		c.stats.remove_source("formation:protection")
	game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ healing (infirmary)
func treat_patient(c) -> Dictionary:
	var p := prof("healing")
	if not Unlocks.is_unlocked(c.id, "healing"): return fail("locked", {"text": Unlocks.locked_text("healing")})
	if not npc_here(c, p.get("npcs", [])): return fail("not_here", {"text": Tx.t("sim.workshop.patients_wait_in_the_sect")})
	if game.crafting.tool_power(c, "healing") <= 0.0: return fail("no_tool", {"text": Tx.t("sim.workshop.you_need_a_needle_case")})
	var day := Clock.reset_day(Clock.now_utc())
	var h: Dictionary = _state(c, "healing", {"day": day, "treated": 0})
	if int(h.get("day", -1)) != day:
		h.day = day
		h.treated = 0
	if int(h.treated) >= int(p.get("patients_per_day", 5)): return fail("no_patients", {"text": Tx.t("sim.workshop.no_more_patients_today")})
	var cost = c.pools.max_qi * float(p.get("qi_cost_pct", 0.15))
	if c.pools.qi < cost: return fail("no_qi", {"text": Tx.t("sim.workshop.not_enough_qi_to_guide")})
	game.combat.apply_resource_change(c.id, "qi", -cost, "healing")
	h.treated = int(h.treated) + 1
	var ailments: Array = p.get("ailments", [Tx.t("sim.workshop.an_injury")])
	var what := str(ailments[Rng.stream(c.id, "crafting").randi_range(0, ailments.size() - 1)])
	game.training.apply_contribution(c.id, int(p.get("contribution", 20)), "healing")
	game.progression.apply_insight(c.id, "life_death", 2.0, "healing")
	_used(c, "treat_patient", "healing", float(p.get("xp_per_use", 0)))
	log_line(c.id, Tx.t("sim.workshop.you_treated") % what, "craft")
	return ok({"text": Tx.t("sim.workshop.you_treated") % what, "left": int(p.get("patients_per_day", 5)) - int(h.treated)})

# ------------------------------------------------------------------ puppetry
func blueprint(id: String) -> Dictionary:
	for b in prof("puppetry").get("blueprints", []):
		if str(b.id) == id: return b
	return {}

func build_puppet(c, id: String) -> Dictionary:
	var p := prof("puppetry")
	if not Unlocks.is_unlocked(c.id, "puppetry"): return fail("locked", {"text": Unlocks.locked_text("puppetry")})
	if not npc_here(c, p.get("npcs", [])): return fail("not_here", {"text": Tx.t("sim.workshop.build_puppets_at_the_tinkerer")})
	var b := blueprint(id)
	if b.is_empty(): return fail("unknown_blueprint")
	var puppets: Array = _state(c, "puppets", [])
	if puppets.size() >= int(p.get("max_puppets", 2)): return fail("too_many", {"text": Tx.t("sim.workshop.you_can_run_puppets") % int(p.get("max_puppets", 2))})
	for inp in b.get("inputs", []):
		if c.inventory.count(str(inp.item)) < int(inp.count): return fail("materials", {"text": Tx.t("sim.workshop.needs") % [int(inp.count), ContentDB.item_name(str(inp.item))]})
	for inp in b.get("inputs", []): game.inventory.apply_remove(c.id, str(inp.item), int(inp.count), "puppet")
	puppets.append({"blueprint": id, "collected_utc": Clock.now_utc()})
	game.progression.apply_insight(c.id, "puppetry", 5.0, "puppet")
	_used(c, "puppet_built", "puppetry", float(p.get("xp_per_use", 0)))
	log_line(c.id, Tx.t("sim.workshop.built_it_sets_to_work") % str(b.get("name", id)), "craft")
	return ok()

## What the puppets have gathered since the last visit (capped per blueprint).
func puppet_yield(c) -> Array:
	var out: Dictionary = {}
	var now := Clock.now_utc()
	for pu in _state(c, "puppets", []):
		var b := blueprint(str(pu.blueprint))
		var hours := clampf((now - float(pu.get("collected_utc", now))) / 3600.0, 0.0, float(b.get("cap_hours", 8)))
		for y in b.get("yield", []):
			out[str(y.item)] = int(out.get(str(y.item), 0)) + int(floor(float(y.per_hour) * hours))
	var rows: Array = []
	for k in out:
		if int(out[k]) > 0: rows.append({"item": k, "count": int(out[k])})
	return rows

func collect_puppets(c) -> Dictionary:
	var rows := puppet_yield(c)
	if rows.is_empty(): return fail("nothing", {"text": Tx.t("sim.workshop.the_puppets_have_nothing_for")})
	for r in rows: game.inventory.apply_add(c.id, str(r.item), int(r.count), "puppet")
	for pu in _state(c, "puppets", []): pu.collected_utc = Clock.now_utc()
	emit("puppets_collected", {"actor": c.id, "items": rows})
	return ok({"items": rows})

# ------------------------------------------------------------------ research
func restore_manual(c) -> Dictionary:
	var p := prof("research")
	if not Unlocks.is_unlocked(c.id, "research"): return fail("locked", {"text": Unlocks.locked_text("research")})
	if not npc_here(c, p.get("npcs", [])): return fail("not_here", {"text": Tx.t("sim.workshop.restoration_needs_the_library_bench")})
	for inp in p.get("inputs", []):
		if c.inventory.count(str(inp.item)) < int(inp.count): return fail("materials", {"text": Tx.t("sim.workshop.needs") % [int(inp.count), ContentDB.item_name(str(inp.item))]})
	for inp in p.get("inputs", []): game.inventory.apply_remove(c.id, str(inp.item), int(inp.count), "research")
	var r := _weighted(Rng.stream(c.id, "crafting"), p.get("results", []))
	game.inventory.apply_add(c.id, str(r.item), int(r.get("count", 1)), "research")
	game.progression.apply_insight(c.id, str(p.get("insight_dao", "soul")), float(p.get("insight_per_use", 0)), "research")
	_used(c, "restore_manual", "research", float(p.get("xp_per_use", 0)))
	var name := ContentDB.item_name(str(r.item))
	log_line(c.id, Tx.t("sim.workshop.restored") % name, "craft")
	return ok({"item": str(r.item), "text": Tx.t("sim.workshop.the_pages_give_up") % name})

# ------------------------------------------------------------------ teaching
## Daos the character can teach (tier at or above `min_dao_tier`, Explanation).
func teachable_daos(c) -> Array:
	var min_tier := int(prof("teaching").get("min_dao_tier", 2))
	var out: Array = []
	for d in c.cultivator.daos:
		if int(c.cultivator.daos[d].get("tier", 0)) >= min_tier: out.append(str(d))
	return out

func teach(c, index: int, dao: String) -> Dictionary:
	var p := prof("teaching")
	if not Unlocks.is_unlocked(c.id, "teaching"): return fail("locked", {"text": Unlocks.locked_text("teaching")})
	if not game.sect.founded(): return fail("no_sect", {"text": Tx.t("sim.workshop.found_your_own_sect_first")})
	var ds: Array = game.account.sect.get("disciples", [])
	if index < 0 or index >= ds.size(): return fail("bad_index")
	var daos := teachable_daos(c)
	if daos.is_empty(): return fail("no_dao", {"text": Tx.t("sim.workshop.reach_explanation_in_a_dao")})
	if dao == "" or not dao in daos: dao = daos[0]
	var t: Dictionary = _state(c, "teaching", {"until_utc": 0.0})
	if Clock.now_utc() < float(t.get("until_utc", 0.0)): return fail("cooldown", {"text": Tx.t("sim.workshop.let_the_lesson_settle_first")})
	t.until_utc = Clock.now_utc() + float(p.get("cooldown_hours", 20)) * 3600.0
	var d: Dictionary = ds[index]
	d.level = mini(20, int(d.get("level", 1)) + int(p.get("disciple_levels", 2)))
	var known: Array = d.get("daos", [])
	if not dao in known: known.append(dao)
	d.daos = known
	game.progression.apply_insight(c.id, dao, float(p.get("insight_per_use", 0)), "teaching")
	game.sect.apply_prestige(int(p.get("prestige", 10)), "teaching")
	_used(c, "teach", "teaching", float(p.get("xp_per_use", 0)))
	log_line(c.id, Tx.t("sim.workshop.studies_the_dao_with_you") % [str(d.get("name", Tx.t("sim.workshop.your_disciple"))), ContentDB.name_of("daos", dao)], "craft")
	return ok({"dao": dao, "level": d.level})
