class_name CalendarAuthority
extends Authority
## S49 · The world calendar (account level): which world events are under way, which are coming, the season and
## the weather. The schedule itself is pure (CalendarRules: the account seed, its creation day and the clock); this
## authority announces the turns (started, ended, announced a day ahead, season, weather) and runs the spatial rift.

var clock := 0.0

func intents() -> Array:
	return []

func cal_seed() -> int:
	return int(game.account.rng_seed)

func origin() -> float:
	return float(game.account.created_utc)

func active_of(id: String) -> Dictionary:
	var ev := CalendarRules.event(id)
	return {} if ev.is_empty() else CalendarRules.active(ev, Clock.now_utc(), cal_seed(), origin())

func upcoming_of(id: String) -> Dictionary:
	var ev := CalendarRules.event(id)
	return {} if ev.is_empty() else CalendarRules.upcoming(ev, Clock.now_utc(), cal_seed(), origin())

func schedule() -> Array:
	return CalendarRules.schedule(Clock.now_utc(), cal_seed(), origin())

## A repeat run (a calendar boss or cache) is open now for this character.
func repeat_open(c, id: String) -> bool:
	var ev := CalendarRules.event(id)
	return not ev.is_empty() and c != null and CalendarRules.repeat_open(ev, Clock.now_utc(), cal_seed(), origin(), c.cultivator.realm_key)

func weather_here() -> String:
	if game.room_rt == null: return "clear"
	return CalendarRules.weather(str(game.room_rt.def.get("weather", "")), Clock.now_utc(), cal_seed())

func tick(delta: float) -> void:
	clock -= delta
	if clock > 0.0: return
	clock = 2.0
	# Seasons run from the account's first day (S49; saves from before it keep the old weekly count).
	HerbRules.origin_week = Clock.reset_week(origin()) if origin() > 0.0 else 0
	var cal: Dictionary = game.account.calendar
	for key in ["active", "told", "weather"]:
		if not cal.has(key): cal[key] = {}
	var now := Clock.now_utc()
	var notice := float(ContentDB.config("calendar").get("notice_h", 24)) * 3600.0
	for ev in CalendarRules.events():
		var id := str(ev.id)
		var occ: Dictionary = CalendarRules.active(ev, now, cal_seed(), origin())
		var was := int(cal.active.get(id, -1))
		if not occ.is_empty() and int(occ.k) != was:
			cal.active[id] = int(occ.k)
			emit("world_event_started", {"event": id, "k": int(occ.k), "room": str(occ.room), "ends": float(occ.end)})
		elif occ.is_empty() and was != -1:
			cal.active.erase(id)
			emit("world_event_ended", {"event": id, "k": was})
		var up := CalendarRules.upcoming(ev, now, cal_seed(), origin())
		if not up.is_empty() and float(up.start) > now and float(up.start) - now <= notice and int(cal.told.get(id, -1)) != int(up.k):
			cal.told[id] = int(up.k)
			emit("world_event_scheduled", {"event": id, "k": int(up.k), "room": str(up.room), "start": float(up.start)})
	var season := HerbRules.season(now)
	if str(cal.get("season", "")) != season:
		if cal.has("season"): emit("season_changed", {"season": season})
		cal.season = season
	for region in ContentDB.config("calendar").get("weather", {}):
		var w := CalendarRules.weather(str(region), now, cal_seed())
		if str(cal.weather.get(region, "")) != w:
			var had: bool = cal.weather.has(region)
			cal.weather[region] = w
			if had: emit("weather_changed", {"region": str(region), "weather": w})

# ------------------------------------------------------------------ the spatial rift
## Touch the tear: the room's own beasts pour out of it, the rift's levels stronger, for a minute. Once a rift per
## character; survive it and it leaves a chest's worth behind.
func open_rift(c) -> Dictionary:
	var rt = game.room_rt
	var ev := CalendarRules.event("spatial_rift")
	var occ: Dictionary = active_of("spatial_rift")
	if rt == null or occ.is_empty() or str(occ.room) != rt.room_id: return fail("no_rift", {"text": Tx.t("sim.calendar.rift_closed")})
	if int(c.cooldowns.get("rift_k", -1)) == int(occ.k): return fail("done", {"text": Tx.t("sim.calendar.rift_done")})
	if rt.event.get("active", false): return fail("busy")
	c.cooldowns["rift_k"] = int(occ.k)
	var bonus := int(ev.get("level_bonus", 3))
	var waves: Array = []
	var st: ActorState = game.actor_state(c.id)
	var x: float = st.plane.x if st else 800.0
	var i := 0
	for spec in rt.def.get("spawns", []):
		if spec.get("boss", false) or spec.get("field_boss", false) or spec.has("requires"): continue
		var lv: Array = spec.get("level", ContentDB.entry("enemies", str(spec.enemy)).get("level", [1, 1]))
		waves.append({"enemy": str(spec.enemy), "first_s": 2.0 + i * 8.0, "every_s": 5.0, "max": 3,
			"level": int(lv[lv.size() - 1]) + bonus, "points": [[clampf(x - 360.0, 120.0, rt.width() - 120.0), 860], [clampf(x + 360.0, 120.0, rt.width() - 120.0), 860]]})
		i += 1
		if i >= 3: break
	var top := 1
	for w in waves: top = maxi(top, int(w.level))
	game.world.start_room_event(c, {"id": "spatial_rift", "duration": 60.0, "waves": waves,
		"on_complete": [{"kind": "rift_reward", "loot": str(ev.get("loot", "chest_dungeon")), "level": top}]})
	emit("rift_opened", {"actor": c.id, "room": rt.room_id, "k": int(occ.k), "level": top})
	return ok({"rift": true})
