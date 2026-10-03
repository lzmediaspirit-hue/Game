class_name WorldNests
extends WorldPart
## WorldAuthority's part: the Beast Kings' nests, the Beast Tide and the Beast Trial Grove (S46).

## When a fallen King's nest closes again (0 when it is closed).
func nest_closes(king: String) -> float:
	return float(game.account.rooms.get("king_nests", {}).get(king, 0.0))

func nest_flag(king: String) -> String:
	return "king_nest:%s:%d" % [king, int(nest_closes(king))]

func tide_cfg() -> Dictionary:
	return ContentDB.config("expeditions").get("beast_tide", {})

## The Beast Tide comes once a real week: due when this character has not stood against this week's tide.
func tide_due(c) -> bool:
	return int(c.cooldowns.get("beast_tide_week", -1)) != Clock.reset_week(Clock.now_utc())

func tide_days_left(c) -> int:
	var now := Clock.now_utc()
	var d := 0
	while d < 8 and Clock.reset_week(now + d * 86400.0) == Clock.reset_week(now): d += 1
	return d

## Ring the gate's gong: three waves of beasts, their Level following yours (S25 room-event waves).
func start_beast_tide(c) -> Dictionary:
	var cfg := tide_cfg()
	if game.room_rt == null or game.room_rt.room_id != str(cfg.get("room", "sf_gate")): return fail("not_here")
	if not tide_due(c): return fail("not_due", {"text": Tx.t("sim.world.tide_not_due") % Tx.span(maxi(1, tide_days_left(c)) * 86400.0)})
	if game.room_rt.event.get("active", false): return fail("busy")
	var ev := {"id": "beast_tide", "duration": float(cfg.get("duration", 90)), "waves": cfg.get("waves", []),
		"on_complete": [{"kind": "beast_tide_result", "won": true}]}
	world.events.start_event(c, game.room_rt, ev)
	emit("beast_tide_started", {"actor": c.id, "room": game.room_rt.room_id, "week": Clock.reset_week(Clock.now_utc()),
		"duration": float(cfg.get("duration", 90))})
	return ok({"event": "beast_tide"})

## S46 Beast Trial Grove: once a day the animals fight ten beasts (their Level following yours) while you rally them.
func start_beast_trial(c) -> Dictionary:
	var cfg: Dictionary = ContentDB.config("beast_arena").get("grove", {})
	if game.room_rt == null or game.room_rt.room_id != str(cfg.get("room", "sf_beast_grove")): return fail("not_here")
	var today := Clock.reset_day(Clock.now_utc())
	if int(c.cooldowns.get("grove_day", -1)) == today: return fail("done", {"text": Tx.t("sim.world.grove_done")})
	if game.pets.party(c).is_empty(): return fail("no_pet", {"text": Tx.t("sim.pet.no_active")})
	if game.room_rt.event.get("active", false): return fail("busy")
	c.cooldowns["grove_day"] = today
	var waves: Array = []
	for w in cfg.get("waves", []):
		var w2: Dictionary = (w as Dictionary).duplicate()
		w2.level = "player"
		w2.level_offset = int(cfg.get("level_offset", -2))
		w2.level_min = int(cfg.get("level_min", 10))
		w2.level_max = int(cfg.get("level_max", 60))
		waves.append(w2)
	var ev := {"id": "beast_trial", "pet_trial": true, "duration": float(cfg.get("duration", 150)), "waves": waves,
		"kill_count": {"enemy": "*", "count": int(cfg.get("count", 10))},
		"on_complete": [{"kind": "beast_trial_result", "won": true}], "on_timeout": [{"kind": "beast_trial_result", "won": false}]}
	world.events.start_event(c, game.room_rt, ev)
	return ok({"event": "beast_trial"})

## The Grove's reward: the Guardian Spirit book the first time, then one draw from the pool.
func apply_trial_result(actor_id: String, won: bool) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var cfg: Dictionary = ContentDB.config("beast_arena").get("grove", {})
	var item := ""
	if won:
		if not c.quests.has_flag("grove_first_clear"):
			game.quest.apply_flag(c.id, "grove_first_clear")
			item = str(cfg.get("first", ""))
		else:
			var pool: Array = cfg.get("pool", [])
			var pick := LootRules.RngService_weighted(Rng.stream(c.id, "world"), pool)
			item = str(pick.get("item", ""))
		if item != "": game.inventory.apply_add(c.id, item, 1, "beast_trial")
	emit("beast_trial_result", {"actor": c.id, "won": won, "item": item})

## Held the gate: this week's tide is spent; cores of your rank, an egg (the Cloud Stag's once, from Cloud Stride 1)
## and Spirit Soil.
func apply_tide_result(actor_id: String, won: bool) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cooldowns["beast_tide_week"] = Clock.reset_week(Clock.now_utc())
	var rw: Dictionary = tide_cfg().get("rewards", {})
	var got: Array = []
	if won:
		var rng := Rng.stream(c.id, "world")
		var els: Array = ["fire", "water", "wood", "earth", "wind", "thunder"]
		var tier := "low" if ProgressionRules.level(c) < 28 else ("mid" if ProgressionRules.level(c) < 46 else "high")
		for i in int(rw.get("cores", 3)):
			var core := "%s_core_%s" % [els[rng.randi_range(0, els.size() - 1)], tier]
			game.inventory.apply_add(c.id, core, 1, "beast_tide")
			got.append(core)
		var egg := str(rw.get("egg", "spirit_egg"))
		if ProgressionRules.at_least(c.cultivator.realm_key, str(rw.get("stag_realm", "cloud_stride_1"))) and not c.quests.has_flag("tide_stag_egg"):
			egg = str(rw.get("stag_egg", "cloud_stag_egg"))
			game.quest.apply_flag(c.id, "tide_stag_egg")
		game.inventory.apply_add(c.id, egg, 1, "beast_tide")
		got.append(egg)
		game.inventory.apply_add(c.id, "spirit_soil", int(rw.get("soil", 1)), "beast_tide")
		got.append("spirit_soil")
	emit("beast_tide_result", {"actor": c.id, "won": won, "items": got})
