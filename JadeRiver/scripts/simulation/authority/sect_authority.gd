class_name SectAuthority
extends Authority
## S25 · Your own sect (account-wide): name, emblem, level, Prestige, buildings,
## a build queue whose timers run offline, NPC disciples and expeditions.

var timer := 0.0

func intents() -> Array:
	return ["found_sect", "upgrade_building", "recruit_disciple", "send_expedition", "collect_expedition", "start_defence", "repair_building",
		"assault_mine", "defend_mine", "collect_mine", "guard_mine"]

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
		"assault_mine": return assault_mine(c, str(intent.get("mine", "")))
		"defend_mine": return defend_mine(c, str(intent.get("mine", "")))
		"collect_mine": return collect_mine(c, str(intent.get("mine", "")))
		"guard_mine": return guard_mine(str(intent.get("mine", "")), int(intent.get("index", -1)))
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

## S18: a zone outpost adds to every member's attunement in its zone.
func outpost_attunement(zone_id: String) -> float:
	if not founded(): return 0.0
	var b := ContentDB.entry("sect_buildings", "expanse_outpost")
	if str(b.get("output", {}).get("zone", "")) != zone_id: return 0.0
	return float(output("expanse_outpost", "attunement_per_level")) * level_building("expanse_outpost") * output_mult("expanse_outpost")

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
	var need_realm := str(b.get("output", {}).get("requires_realm", ""))
	if need_realm != "" and not ProgressionRules.at_least(game.account.highest_realm, need_realm):
		return fail("realm", {"text": Tx.t("sim.sect.needs_a_member_at") % ContentDB.name_of("realms", need_realm)})
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
	# (JSON numbers are floats: compare the hours as whole numbers.)
	if ex.is_empty() or not (ex.get("hours", [1, 4, 8]) as Array).any(func(h): return int(h) == hours): return fail("bad_expedition")
	if ex.has("requires_building") and level_building(str(ex.requires_building)) <= 0:
		return fail("needs_building", {"text": Tx.t("sim.sect.needs_building") % ContentDB.name_of("sect_buildings", str(ex.requires_building))})
	if disciples.is_empty() or disciples.size() > 4: return fail("bad_party")
	var busy := guarding()
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
		# Each reward row gives its count for every hour away; some need a long trip, some are a chance; coins are silver.
		var silver := 0
		for r in ex.get("rewards", []):
			if int(e.hours) < int(r.get("min_hours", 0)): continue
			if r.has("chance") and rng.randf() >= float(r.chance): continue
			if r.has("coins"):
				silver += int(r.coins) * int(e.hours)
				continue
			var n := int(r.get("count", r.get("per_hour", 1))) * int(e.hours)
			game.inventory.apply_add(c.id, str(r.item), n, "expedition")
			rewards.append({"item": r.item, "count": n})
		game.economy.apply_currency("silver_tael", maxi(silver, 30 * int(e.hours)), "expedition")
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
	_tick_mines(now)
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

# ------------------------------------------------------------------ territory and spirit mines (S49 v1.1)
## Spirit-stone mines in field rooms (territory.json), each held by a rival sect until your sect takes it: a room event
## at the mine, its guards and warden (the S25 defence waves turned to offence). A mine you hold fills its carts by the
## hour, up to a day's worth. Every two to four days (seeded) the old holder comes back: hold the mine in person within
## the window, or your guards (disciples you post there) hold it or lose it by chance. Account state:
## sect.mines {id: {collected, contest, contested, until, guards: [disciple index], n}}.
func tcfg() -> Dictionary:
	return ContentDB.config("territory")

func mine_def(id: String) -> Dictionary:
	return ContentDB.entry("territory", id)

func rival(id: String) -> Dictionary:
	for r in tcfg().get("sects", []):
		if str(r.id) == id: return r
	return {}

func mines() -> Dictionary:
	return sect().get("mines", {}) if founded() else {}

func holds(id: String) -> bool:
	return mines().has(id)

## Who flies their banner over a mine: your sect's name, or the rival that holds it.
func mine_holder(id: String) -> String:
	return str(sect().name) if holds(id) else str(rival(str(mine_def(id).get("sect", ""))).get("name", ""))

## How many mines your sect can hold: one, and one more at every third sect level.
func mine_cap() -> int:
	if not founded(): return 0
	return int(tcfg().get("mines_base", 1)) + int(sect().level) / maxi(1, int(tcfg().get("mines_per_levels", 3)))

## Spirit Stones waiting in a mine's carts: its rate for every hour since the last collection, up to a day's worth.
func mine_stored(id: String, now := -1.0) -> int:
	if not holds(id): return 0
	if now < 0.0: now = Clock.now_utc()
	var hours := clampf((now - float(mines()[id].get("collected", now))) / 3600.0, 0.0, float(tcfg().get("cap_hours", 24)))
	return int(floor(hours * float(mine_def(id).get("rate", 1))))

## The disciples posted as guards at every mine (disciple index -> mine).
func guarding() -> Dictionary:
	var out := {}
	for id in mines():
		for d in mines()[id].get("guards", []): out[int(d)] = str(id)
	return out

func _on_expedition(index: int) -> bool:
	for e in sect().get("expeditions", []):
		for d in e.disciples:
			if int(d) == index: return true
	return false

## Why your sect cannot take a mine now (an empty text when it can).
func assault_block(c, id: String) -> String:
	var m := mine_def(id)
	if m.is_empty(): return Tx.t("sim.sect.mine_unknown")
	if not founded(): return Tx.t("sim.sect.mine_no_sect")
	if holds(id): return Tx.t("sim.sect.mine_yours")
	if int(sect().level) < int(m.get("sect_level", 1)): return Tx.t("sim.sect.needs_sect_level") % int(m.get("sect_level", 1))
	if mines().size() >= mine_cap(): return Tx.t("sim.sect.mine_cap") % mine_cap()
	if c == null: return Tx.t("sim.sect.mine_unknown")
	return ""

func _at_mine(id: String) -> bool:
	return game.room_rt != null and game.room_rt.room_id == str(mine_def(id).get("room", ""))

## Take a mine: its guards stand at the vein and more come while they fall; the warden must fall inside the time.
func assault_mine(c, id: String) -> Dictionary:
	var why := assault_block(c, id)
	if why != "": return fail("blocked", {"text": why})
	if not _at_mine(id): return fail("wrong_room", {"text": Tx.t("sim.sect.mine_go_there") % ContentDB.name_of("rooms", str(mine_def(id).room))})
	if game.room_rt.event.get("active", false): return fail("busy")
	var m := mine_def(id)
	var rv := rival(str(m.sect))
	var a: Dictionary = tcfg().get("assault", {})
	var at: Array = m.get("at", [1200, 860])
	var x := float(at[0])
	var lv := int(m.level)
	var pts := [[x - 260.0, 840.0], [x + 260.0, 880.0], [x - 120.0, 900.0], [x + 140.0, 820.0]]
	var spawns: Array = []
	for i in int(a.get("guards", 3)):
		spawns.append({"enemy": str(rv.disciple), "at": pts[i % pts.size()], "level": lv})
	spawns.append({"enemy": str(rv.warden), "at": [x + 60.0, 860.0], "level": lv + int(a.get("warden_bonus", 3))})
	var ev := {"id": "mine_assault", "mine": id, "duration": float(a.get("duration", 120)), "fixed_spawns": spawns,
		"waves": [{"enemy": str(rv.disciple), "first_s": float(a.get("every_s", 6)), "every_s": float(a.get("every_s", 6)),
			"max": int(a.get("max", 3)), "level": lv, "points": pts}],
		"win_on_kill": str(rv.warden),
		"on_complete": [{"kind": "mine_assault_result", "mine": id, "won": true}],
		"on_timeout": [{"kind": "mine_assault_result", "mine": id, "won": false}]}
	game.world.start_room_event(c, ev)
	return ok({"event": "mine_assault"})

## The warden fell: the mine is yours, its carts empty, and the old holder starts counting the days.
func apply_mine_assault(actor_id: String, id: String, won: bool) -> void:
	if not won or not founded() or holds(id) or mine_def(id).is_empty(): return
	var now := Clock.now_utc()
	var all := mines()
	all[id] = {"collected": now, "contest": _next_contest(id, 0, now), "contested": false, "until": 0.0, "guards": [], "n": 0}
	sect().mines = all
	apply_prestige(int(tcfg().get("assault", {}).get("prestige", 30)), "mine")
	emit("mine_claimed", {"actor": actor_id, "mine": id, "sect": str(mine_def(id).sect)})

## When the old holder comes back next: seeded by the account, the mine and how many times it has come before.
func _next_contest(id: String, n: int, from: float) -> float:
	var days: Array = tcfg().get("contest", {}).get("interval_days", [2, 4])
	var rng := Rng.keyed(int(game.account.rng_seed), "mine:%s:%d" % [id, n])
	return from + rng.randf_range(float(days[0]), float(days[1])) * 86400.0

## Hold a contested mine in person: survive the old holder's waves (their warden joins part-way).
func defend_mine(c, id: String) -> Dictionary:
	if not holds(id): return fail("not_yours", {"text": Tx.t("sim.sect.mine_not_yours")})
	if not bool(mines()[id].get("contested", false)): return fail("quiet", {"text": Tx.t("sim.sect.mine_quiet")})
	if not _at_mine(id): return fail("wrong_room", {"text": Tx.t("sim.sect.mine_go_there") % ContentDB.name_of("rooms", str(mine_def(id).room))})
	if game.room_rt.event.get("active", false): return fail("busy")
	var m := mine_def(id)
	var rv := rival(str(m.sect))
	var k: Dictionary = tcfg().get("contest", {})
	var x := float((m.get("at", [1200, 860]) as Array)[0])
	var pts := [[x - 420.0, 840.0], [x + 420.0, 880.0], [x - 300.0, 900.0], [x + 320.0, 820.0]]
	var ev := {"id": "mine_defence", "mine": id, "duration": float(k.get("duration", 60)),
		"waves": [{"enemy": str(rv.disciple), "first_s": 2.0, "every_s": float(k.get("every_s", 5)), "max": int(k.get("max", 4)),
			"level": int(m.level), "points": pts}],
		"timed_spawns": [{"enemy": str(rv.warden), "after_s": float(k.get("warden_after_s", 20)), "at": [x + 380.0, 860.0],
			"level": int(m.level) + int(tcfg().get("assault", {}).get("warden_bonus", 3)), "text": Tx.t("sim.sect.mine_warden_comes") % ContentDB.name_of("enemies", str(rv.warden))}],
		"on_complete": [{"kind": "mine_defence_result", "mine": id, "won": true}]}
	game.world.start_room_event(c, ev)
	return ok({"event": "mine_defence"})

func apply_mine_defence(actor_id: String, id: String, won: bool) -> void:
	if not won or not holds(id) or not bool(mines()[id].get("contested", false)): return
	_hold(id, "you", actor_id)

## The mine holds: prestige, and the old holder's next visit is set.
func _hold(id: String, by: String, actor_id := "") -> void:
	var m: Dictionary = mines()[id]
	# The guards decide it when the window closes (perhaps while you were away); the next visit counts from then.
	var from := float(m.get("until", Clock.now_utc())) if by == "guards" else Clock.now_utc()
	m.n = int(m.get("n", 0)) + 1
	m.contested = false
	m.until = 0.0
	m.contest = _next_contest(id, int(m.n), from)
	apply_prestige(int(tcfg().get("contest", {}).get("prestige", 20)), "mine")
	emit("mine_defended", {"actor": actor_id, "mine": id, "sect": str(mine_def(id).sect), "by": by})

## Collect the carts: Spirit Stones, and Prestige for the sect.
func collect_mine(c, id: String) -> Dictionary:
	if not holds(id): return fail("not_yours", {"text": Tx.t("sim.sect.mine_not_yours")})
	var now := Clock.now_utc()
	var n := mine_stored(id, now)
	if n <= 0: return fail("empty", {"text": Tx.t("sim.sect.mine_empty")})
	# Only whole stones leave the carts: the part-hour stays behind.
	var rate := maxf(0.001, float(mine_def(id).get("rate", 1)))
	var m: Dictionary = mines()[id]
	m.collected = maxf(float(m.get("collected", now)), now - float(tcfg().get("cap_hours", 24)) * 3600.0) + n / rate * 3600.0
	game.economy.apply_currency("spirit_stone", n, "mine")
	apply_prestige(n * int(tcfg().get("prestige_per_stone", 1)), "mine")
	emit("mine_collected", {"actor": c.id if c != null else "", "mine": id, "stones": n})
	return ok({"stones": n})

## Post a disciple at a mine as a guard, or call one home (up to three; not one who is away on an expedition).
func guard_mine(id: String, index: int) -> Dictionary:
	if not holds(id): return fail("not_yours", {"text": Tx.t("sim.sect.mine_not_yours")})
	var ds: Array = sect().get("disciples", [])
	if index < 0 or index >= ds.size(): return fail("bad_index")
	var guards: Array = mines()[id].get("guards", [])
	if index in guards:
		guards.erase(index)
	else:
		var elsewhere := str(guarding().get(index, ""))
		if elsewhere != "": return fail("busy", {"text": Tx.t("sim.sect.mine_guard_elsewhere") % ContentDB.name_of("territory", elsewhere)})
		if _on_expedition(index): return fail("busy", {"text": Tx.t("sim.sect.mine_guard_away")})
		if guards.size() >= int(tcfg().get("contest", {}).get("max_guards", 3)): return fail("full", {"text": Tx.t("sim.sect.mine_guards_full")})
		guards.append(index)
	mines()[id].guards = guards
	return ok({"guards": guards.size()})

## The chance your guards hold a mine you did not come back to defend.
func guard_chance(id: String) -> float:
	var k: Dictionary = tcfg().get("contest", {})
	var p := float(k.get("base", 0.3))
	for d in mines().get(id, {}).get("guards", []):
		var dd: Dictionary = sect().disciples[int(d)] if int(d) < sect().disciples.size() else {}
		p += float(k.get("per_guard", 0.15)) + float(k.get("per_guard_level", 0.01)) * int(dd.get("level", 1))
	return clampf(p, 0.0, 0.95)

## The old holders' timers (they run offline too): a contest opens, and when its window closes the guards decide it.
func _tick_mines(now: float) -> void:
	var window := float(tcfg().get("contest", {}).get("window_h", 12)) * 3600.0
	for id in mines().keys():
		var m: Dictionary = mines()[id]
		for _i in 16:   # several contests may have come and gone while you were away
			if not bool(m.get("contested", false)):
				if now < float(m.get("contest", INF)): break
				m.contested = true
				m.until = float(m.contest) + window
				emit("mine_contested", {"mine": str(id), "sect": str(mine_def(str(id)).sect), "until": float(m.until)})
			if now < float(m.until): break
			var rng := Rng.keyed(int(game.account.rng_seed), "mine_hold:%s:%d" % [str(id), int(m.get("n", 0))])
			if rng.randf() < guard_chance(str(id)):
				_hold(str(id), "guards")
			else:
				_lose(str(id), float(m.until))
				break

## The old holder takes the mine back, and what was in the carts with it; the guards come home.
func _lose(id: String, at: float) -> void:
	var stones := mine_stored(id, at)
	mines().erase(id)
	emit("mine_lost", {"mine": id, "sect": str(mine_def(id).sect), "stones": stones})

## What the vein says when you walk up to it: who holds it, and what you can do here.
func mine_dialogue(c, id: String) -> Dictionary:
	var m := mine_def(id)
	if m.is_empty(): return fail("unknown_mine")
	var lines: Array = [str(m.get("desc", ""))]
	var choices: Array = []
	if holds(id):
		var st: Dictionary = mines()[id]
		var cap := int(float(tcfg().get("cap_hours", 24)) * float(m.get("rate", 1)))
		lines.append(Tx.t("sim.sect.mine_yours_line") % [str(sect().name), mine_stored(id), cap])
		if bool(st.get("contested", false)):
			var left := maxi(1, int(ceil((float(st.until) - Clock.now_utc()) / 3600.0)))
			lines.append(Tx.t("sim.sect.mine_contested_line") % [mine_holder_rival(id), left])
			choices.append({"text": Tx.t("sim.sect.mine_defend"), "intent": {"type": "defend_mine", "mine": id}})
		if mine_stored(id) > 0: choices.append({"text": Tx.t("sim.sect.mine_collect") % mine_stored(id), "intent": {"type": "collect_mine", "mine": id}})
	else:
		lines.append(Tx.t("sim.sect.mine_held_line") % [mine_holder(id), int(m.level)])
		var why := assault_block(c, id)
		if why != "": lines.append(why)
		else: choices.append({"text": Tx.t("sim.sect.mine_take"), "intent": {"type": "assault_mine", "mine": id}})
	if founded(): choices.append({"text": Tx.t("sim.sect.mine_territory"), "page": "your_sect", "args": {"tab": "territory"}})
	choices.append({"text": Tx.t("sim.world.leave_it"), "close": true})
	return ok({"dialogue": {"npc": "", "speaker": str(m.name), "portrait": {}, "lines": lines, "choices": choices}})

## The rival sect that held (and wants back) a mine.
func mine_holder_rival(id: String) -> String:
	return str(rival(str(mine_def(id).get("sect", ""))).get("name", ""))
