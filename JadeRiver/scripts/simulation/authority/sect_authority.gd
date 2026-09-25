class_name SectAuthority
extends Authority
## S25 · Your own sect (account-wide): name, emblem, level, Prestige, buildings,
## a build queue whose timers run offline, NPC disciples and expeditions.

var timer := 0.0

func intents() -> Array:
	return ["found_sect", "upgrade_building", "recruit_disciple", "send_expedition", "collect_expedition", "start_defence", "repair_building"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	match str(intent.type):
		"found_sect": return found(c, str(intent.get("name", "")), intent.get("emblem", [0, 0]))
		"upgrade_building": return upgrade(c, str(intent.get("building", "")))
		"recruit_disciple": return recruit(int(intent.get("index", 0)))
		"send_expedition": return send_expedition(str(intent.get("region", "")), int(intent.get("hours", 1)), intent.get("disciples", []))
		"collect_expedition": return collect_expedition(c, int(intent.get("index", 0)))
		"start_defence": return start_defence(c)
		"repair_building": return repair(c, str(intent.get("building", "")))
	return fail("unknown_intent")

func sect() -> Dictionary:
	return game.account.sect

func founded() -> bool:
	return not sect().is_empty()

func level_building(id: String) -> int:
	return int(sect().get("buildings", {}).get(id, 0))

## A building's `output` numbers (sect_buildings.json), scaled down while it is damaged.
func output(id: String, key: String, fallback = 0.0):
	return ContentDB.entry("sect_buildings", id).get("output", {}).get(key, fallback)

func output_mult(id: String) -> float:
	return float(ContentDB.config("defence").get("damaged_output", 0.5)) if sect().get("damaged", {}).has(id) else 1.0

func idle_cap_bonus() -> float:
	var lv := level_building("meditation_pavilion")
	var hours := 0.0
	for step in output("meditation_pavilion", "idle_cap_hours", []):
		if lv >= int(step[0]): hours = float(step[1])
	return hours * output_mult("meditation_pavilion")

func idle_rate_bonus(task: String) -> float:
	if task != "seclusion": return 0.0
	return float(output("meditation_pavilion", "idle_rate_per_level")) * level_building("meditation_pavilion") * output_mult("meditation_pavilion")

func treasury_bonus() -> int:
	return int(float(output("treasury", "taels_per_level")) * level_building("treasury") * output_mult("treasury"))

func disciple_cap() -> int:
	return int(output("guest_house", "disciples_base", 2)) + int(output("guest_house", "disciples_per_level", 1)) * level_building("guest_house")

func found(c, name: String, emblem) -> Dictionary:
	if c == null or not Unlocks.is_unlocked(c.id, "your_sect"): return fail("locked")
	if founded(): return fail("already_founded")
	name = name.strip_edges().left(24)
	if name == "": return fail("bad_name", {"text": Tx.t("sim.sect.name_your_sect")})
	game.account.sect = {"name": name, "emblem": emblem, "level": 1, "prestige": 0, "buildings": {"sect_hall": 1}, "queue": [],
		"disciples": [], "candidates": [], "expeditions": [], "candidate_day": -1}
	emit("sect_founded", {"name": name})
	emit("system_used", {"actor": c.id, "system": "found_sect"})
	emit("sect_level_changed", {"level": 1})
	_refresh_candidates()
	return ok()

func building_cost(id: String, next_level: int) -> Dictionary:
	var b := ContentDB.entry("sect_buildings", id)
	var base := float(b.get("base_cost", 500))
	var taels := int(round(base * pow(2.2, next_level - 1)))
	var mats: Dictionary = {}
	if next_level <= 2: mats[str(b.get("material", "copper_ore"))] = int(b.get("material_count", 20)) * next_level
	else: mats[{3: "riverstone", 4: "jadeiron", 5: "jadeiron"}.get(next_level, "jadeiron")] = 10 * next_level
	var hours := minf(24.0, pow(2.0, next_level - 1))
	return {"silver_tael": taels, "materials": mats, "seconds": hours * 3600.0}

func upgrade(c, id: String) -> Dictionary:
	if not founded(): return fail("no_sect")
	var b := ContentDB.entry("sect_buildings", id)
	if b.is_empty(): return fail("unknown_building")
	if int(sect().level) < int(b.get("sect_level", 1)): return fail("sect_level", {"text": Tx.t("sim.sect.needs_sect_level") % int(b.get("sect_level", 1))})
	var max_parallel := 2 if int(sect().level) >= 8 else 1
	if sect().queue.size() >= max_parallel: return fail("queue_busy", {"text": Tx.t("sim.sect.builders_are_busy")})
	var next := level_building(id) + 1
	if next > int(b.get("max_level", 5)): return fail("max_level")
	var cost := building_cost(id, next)
	if game.economy.balance("silver_tael") < int(cost.silver_tael): return fail("insufficient_funds")
	for m in cost.materials:
		if c.inventory.count(m) < int(cost.materials[m]): return fail("materials", {"text": Tx.t("sim.sect.needs") % [int(cost.materials[m]), ContentDB.item_name(m)]})
	game.economy.apply_currency("silver_tael", -int(cost.silver_tael), "sect_build")
	for m2 in cost.materials: game.inventory.apply_remove(c.id, m2, int(cost.materials[m2]), "sect_build")
	sect().queue.append({"building": id, "level": next, "done_utc": Clock.now_utc() + float(cost.seconds)})
	emit("building_started", {"building": id, "level": next})
	return ok()

func apply_prestige(amount: int, source: String) -> void:
	if not founded(): return
	sect().prestige = int(sect().prestige) + amount
	emit("prestige_gained", {"amount": amount, "source": source})
	var lv := int(sect().level)
	var base := float(ContentDB.curve("prestige.base", 200))
	var power := float(ContentDB.curve("prestige.pow", 1.8))
	while lv < 20 and float(sect().prestige) >= base * pow(lv + 1, power):
		lv += 1
	if lv != int(sect().level):
		sect().level = lv
		emit("sect_level_changed", {"level": lv})

func _refresh_candidates() -> void:
	var day := Clock.reset_day(Clock.now_utc())
	if int(sect().get("candidate_day", -1)) == day: return
	sect().candidate_day = day
	var rng := Rng.stream("account", "sect")
	var traits: Array = ContentDB.config("disciples").get("traits", ["green_thumb"])
	var names: Array = ContentDB.config("disciples").get("names", [Tx.t("sim.sect.wei")])
	var cands: Array = []
	for i in 3:
		cands.append({"name": names[rng.randi_range(0, names.size() - 1)], "strength": rng.randi_range(1, 5), "spirit": rng.randi_range(1, 5),
			"craft": rng.randi_range(1, 5), "trait": traits[rng.randi_range(0, traits.size() - 1)], "level": 1})
	sect().candidates = cands

func recruit(index: int) -> Dictionary:
	if not founded(): return fail("no_sect")
	if sect().disciples.size() >= disciple_cap(): return fail("full", {"text": Tx.t("sim.sect.build_more_guest_house_rooms")})
	var cands: Array = sect().get("candidates", [])
	if index < 0 or index >= cands.size(): return fail("bad_index")
	sect().disciples.append(cands[index])
	cands.remove_at(index)
	emit("disciple_recruited", {})
	emit("system_used", {"actor": game.active_id, "system": "recruit"})
	return ok()

func send_expedition(region: String, hours: int, disciples: Array) -> Dictionary:
	if not founded(): return fail("no_sect")
	var ex := ContentDB.entry("expeditions", region)
	if ex.is_empty() or not hours in ex.get("hours", [1, 4, 8]): return fail("bad_expedition")
	if disciples.is_empty() or disciples.size() > 4: return fail("bad_party")
	var busy := {}
	for e in sect().expeditions:
		for d in e.disciples: busy[int(d)] = true
	for d in disciples:
		if busy.has(int(d)) or int(d) >= sect().disciples.size(): return fail("busy")
	sect().expeditions.append({"region": region, "hours": hours, "disciples": disciples.duplicate(), "done_utc": Clock.now_utc() + hours * 3600.0})
	emit("expedition_sent", {"region": region})
	return ok()

func collect_expedition(c, index: int) -> Dictionary:
	var list: Array = sect().get("expeditions", [])
	if index < 0 or index >= list.size(): return fail("bad_index")
	var e: Dictionary = list[index]
	if Clock.now_utc() < float(e.done_utc): return fail("not_back")
	var ex := ContentDB.entry("expeditions", str(e.region))
	var rng := Rng.stream("account", "sect")
	var danger := int(ex.get("danger_level", 1))
	var best := 0
	for d in e.disciples: best = maxi(best, int(sect().disciples[int(d)].get("level", 1)))
	var chance := minf(0.95, 0.5 + 0.1 * (best - danger))
	var success := rng.randf() < chance
	var rewards: Array = []
	if success and c != null:
		for r in ex.get("rewards", []):
			var n := int(r.get("per_hour", 1)) * int(e.hours)
			game.inventory.apply_add(c.id, str(r.item), n, "expedition")
			rewards.append({"item": r.item, "count": n})
		game.economy.apply_currency("silver_tael", 30 * int(e.hours), "expedition")
		apply_prestige(5 * int(e.hours), "expedition")
	for d in e.disciples: sect().disciples[int(d)].level = mini(20, int(sect().disciples[int(d)].get("level", 1)) + 1)
	list.remove_at(index)
	emit("expedition_returned", {"region": e.region, "success": success, "rewards": rewards})
	return ok({"success": success, "rewards": rewards})

func tick(delta: float) -> void:
	timer += delta
	if timer < 2.0 or not founded(): return
	timer = 0.0
	_refresh_candidates()
	var now := Clock.now_utc()
	for q in sect().queue.duplicate():
		if now >= float(q.done_utc):
			sect().buildings[str(q.building)] = int(q.level)
			sect().queue.erase(q)
			emit("building_upgraded", {"building": q.building, "level": q.level})
			apply_prestige(int(ContentDB.config("sect_levels").get("prestige_building", 20)), "building")

# ------------------------------------------------------------------ defence events (S25)
## A raid can be fought when one is due (sect level 6+, every 2-3 days) or when the
## "Walls of the Vale" lesson asks for the first one.
func defence_due(c) -> bool:
	if not founded(): return false
	if c != null and c.quests.active.has("walls_of_the_vale"): return true
	var cfg := ContentDB.config("defence")
	return int(sect().level) >= int(cfg.get("from_level", 6)) and Clock.now_utc() >= float(sect().get("next_defence_utc", 0.0))

func start_defence(c) -> Dictionary:
	if c == null or not founded(): return fail("no_sect")
	if not defence_due(c): return fail("not_due", {"text": Tx.t("sim.sect.no_raid_is_coming_yet")})
	var cfg := ContentDB.config("defence")
	if game.room_rt == null or game.room_rt.room_id != str(cfg.get("room", "hv_sect_grounds")):
		return fail("wrong_room", {"text": Tx.t("sim.sect.meet_the_raiders_in_the")})
	if game.room_rt.event.get("active", false): return fail("event_running")
	var waves: Array = cfg.get("waves", [])
	var tier := clampi(int(sect().get("defences_won", 0)) / 2, 0, waves.size() - 1)
	var wave: Dictionary = waves[tier].duplicate(true)
	wave["points"] = cfg.get("points", [[400, 860]])
	var ev := {"id": "sect_defence", "duration": float(cfg.get("duration", 60)), "wave": wave,
		"on_complete": [{"kind": "sect_defence_result", "won": true}]}
	game.world.start_room_event(c, ev)
	emit("defence_warning", {"started": true})
	return ok()

func apply_defence_result(actor_id: String, won: bool) -> void:
	if not founded(): return
	var cfg := ContentDB.config("defence")
	var days: Array = cfg.get("interval_days", [2, 3])
	sect().next_defence_utc = Clock.now_utc() + Rng.stream("account", "sect").randf_range(float(days[0]), float(days[1])) * 86400.0
	if won:
		sect().defences_won = int(sect().get("defences_won", 0)) + 1
		game.economy.apply_currency("silver_tael", int(cfg.get("taels_win", 200)), "defence")
		apply_prestige(int(cfg.get("prestige_win", 40)), "defence")
		emit("system_used", {"actor": actor_id, "system": "defence_won"})
	else:
		var built: Array = sect().get("buildings", {}).keys()
		if not built.is_empty():
			var hit := str(built[Rng.stream("account", "sect").randi_range(0, built.size() - 1)])
			var damaged: Dictionary = sect().get("damaged", {})
			damaged[hit] = true
			sect().damaged = damaged
			emit("building_damaged", {"actor": actor_id, "building": hit, "output": float(cfg.get("damaged_output", 0.5))})
	emit("defence_result", {"won": won})

func repair(c, id: String) -> Dictionary:
	var damaged: Dictionary = sect().get("damaged", {})
	if not damaged.has(id): return fail("not_damaged")
	var cost := int(building_cost(id, maxi(1, level_building(id))).silver_tael * float(ContentDB.config("defence").get("repair_cost_fraction", 0.25)))
	if game.economy.balance("silver_tael") < cost: return fail("insufficient_funds")
	game.economy.apply_currency("silver_tael", -cost, "repair")
	damaged.erase(id)
	emit("building_repaired", {"building": id})
	return ok()
