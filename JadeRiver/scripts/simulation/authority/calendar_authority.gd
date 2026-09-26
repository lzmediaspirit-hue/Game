class_name CalendarAuthority
extends Authority
## S49 · The world calendar (account level): which world events are under way, which are coming, the season and
## the weather. The schedule itself is pure (CalendarRules: the account seed, its creation day and the clock); this
## authority announces the turns (started, ended, announced a day ahead, season, weather), runs the spatial rift,
## treasure births and the gathering trial, and shows the heavens' answer to a breakthrough (heavenly phenomena).

var clock := 0.0

func intents() -> Array:
	return ["challenge_rank"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"challenge_rank": return challenge_rank(c, str(intent.get("npc", "")))
	return fail("unknown_intent")

func subscribe() -> void:
	GameEvents.subscribe("node_gathered", _on_gathered, 90)
	GameEvents.subscribe("room_entered", _on_room_entered, 90)
	GameEvents.subscribe("breakthrough_succeeded", _on_breakthrough, 90)
	GameEvents.subscribe("tribulation_started", _on_tribulation, 90)
	GameEvents.subscribe("spar_ended", _on_rank_spar, 90)

func _on_room_entered(_p: Dictionary) -> void:
	var c = game.active()
	if c != null: game.combat.apply_weather(c.id, weather_here())

## What the weather here does to fishing (a longer reaction window in rain).
func fishing_bonus() -> float:
	return float(ContentDB.config("calendar").get("weather_effects", {}).get(weather_here(), {}).get("fishing_window", 0.0))

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

var debug_weather := ""   # debug tools: --weather=storm previews a sky

func weather_here() -> String:
	if game.room_rt == null: return "clear"
	if debug_weather != "" and str(game.room_rt.def.get("weather", "")) != "": return debug_weather
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
	var c = game.active()
	if c != null: _pay_trial(c)
	# The Heaven Ranking's seeded cultivators move on the calendar; a new order is announced.
	var order: Array = CalendarRules.rank_table(now, cal_seed(), origin()).map(func(r): return str(r.id))
	if cal.get("ranking", []) != order:
		var had_order: bool = cal.has("ranking")
		cal.ranking = order
		if had_order: emit("ranking_changed", {"order": order})
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
			if game.room_rt != null and str(game.room_rt.def.get("weather", "")) == str(region) and game.active() != null:
				game.combat.apply_weather(game.active_id, w)

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

# ------------------------------------------------------------------ treasure births (Part 8: the Spirit Fruit)
## Reach for the ripe fruit: two rival cultivators and its guardian stand in the way (the room's own beasts
## withdraw). Beat all three and the fruit is yours, once per birth.
func open_treasure(c) -> Dictionary:
	var rt = game.room_rt
	var ev := CalendarRules.event("treasure_birth")
	var occ: Dictionary = active_of("treasure_birth")
	if rt == null or occ.is_empty() or str(occ.room) != rt.room_id: return fail("gone", {"text": Tx.t("sim.calendar.fruit_gone")})
	if int(c.cooldowns.get("birth_k", -1)) == int(occ.k): return fail("taken", {"text": Tx.t("sim.calendar.fruit_taken")})
	if rt.event.get("active", false): return fail("busy")
	var top := 1
	for spec in rt.def.get("spawns", []):
		if not spec.get("boss", false): top = maxi(top, int((spec.get("level", [1]) as Array).back()))
	var lv := top + int(ev.get("level_bonus", 2))
	var tree_x := 800.0
	for o in rt.def.get("objects", []):
		if str(o.type) == "treasure_birth": tree_x = float(o.at[0])
	var spawns: Array = [{"enemy": str(ev.get("rivals", "rogue_cultivator")), "at": [clampf(tree_x - 320.0, 120.0, rt.width() - 120.0), 860], "level": lv},
		{"enemy": str(ev.get("rivals", "rogue_cultivator")), "at": [clampf(tree_x + 320.0, 120.0, rt.width() - 120.0), 860], "level": lv},
		{"enemy": str(ev.get("guardian", "fruit_guardian")), "at": [tree_x, 880], "level": lv}]
	game.world.start_room_event(c, {"id": "treasure_birth", "duration": 150.0, "clear_room": true, "fixed_spawns": spawns,
		"kill_count": {"enemy": "*", "count": spawns.size()}, "on_complete": [{"kind": "treasure_claim", "k": int(occ.k)}]})
	return ok({"birth": true})

## The rivals and the guardian are down: the fruit is yours.
func apply_treasure_claim(actor_id: String, k: int) -> void:
	var c = game.character(actor_id)
	if c == null or int(c.cooldowns.get("birth_k", -1)) == k: return
	c.cooldowns["birth_k"] = k
	var item := str(CalendarRules.event("treasure_birth").get("item", "spirit_fruit"))
	game.inventory.apply_add(c.id, item, 1, "treasure_birth")
	emit("treasure_claimed", {"actor": c.id, "item": item, "room": game.room_rt.room_id if game.room_rt else ""})

# ------------------------------------------------------------------ the gathering trial (Part 8)
## Every herb gathered on your sect's Herb Terraces while the trial runs counts: the Jade Sect's for its disciples,
## the Cloud Sect's for theirs. The sect weighs it against the other sect's gatherers (seeded scores) when the day ends.
func _on_gathered(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	var occ: Dictionary = active_of("gathering_trial")
	if c == null or occ.is_empty() or game.room_rt == null or game.room_rt.room_id != trial_room(c): return
	var gt: Dictionary = c.cooldowns.get("gtrial", {})
	if int(gt.get("k", -1)) != int(occ.k): gt = {"k": int(occ.k), "pts": 0, "paid": false, "room": trial_room(c)}
	gt.pts = int(gt.pts) + int(p.get("count", 1))
	c.cooldowns["gtrial"] = gt

## The terraces a character's trial is held on: its sect's own (a disciple of neither gathers on the event's room).
func trial_room(c) -> String:
	var ev := CalendarRules.event("gathering_trial")
	var sid := str(c.training_sect.get("id", "")) if c != null else ""
	return str(ev.get("sect_rooms", {}).get(sid, ev.get("room", "")))

## The other gatherers' scores for one trial on one terraces: the same for every device (seeded by the account, the
## trial and the terraces). The Jade terraces keep the draw they always had.
func trial_rivals(k: int, room := "") -> Array:
	var ev := CalendarRules.event("gathering_trial")
	var sc: Array = ev.get("rival_score", [6, 22])
	var own := room != "" and room != str(ev.get("room", ""))
	var r := CalendarRules.draw(cal_seed(), "gathering_trial:rivals" + (":" + room if own else ""), k)
	var out: Array = []
	for name in (ev.get("room_rivals", {}).get(room, ev.get("rivals", [])) if own else ev.get("rivals", [])):
		out.append({"name": str(name), "pts": r.randi_range(int(sc[0]), int(sc[1]))})
	return out

## Your place: 1 + how many rivals gathered more than you.
func trial_rank(c) -> int:
	var gt: Dictionary = c.cooldowns.get("gtrial", {})
	if gt.is_empty(): return 0
	var rank := 1
	for rv in trial_rivals(int(gt.k), str(gt.get("room", ""))):
		if int(rv.pts) > int(gt.pts): rank += 1
	return rank

## When the trial day has passed, the ranking pays once: the top three learn the Foundation Guard Pill.
func _pay_trial(c) -> void:
	var gt: Dictionary = c.cooldowns.get("gtrial", {})
	if gt.is_empty() or gt.get("paid", false) or int(gt.get("pts", 0)) <= 0: return
	var occ: Dictionary = active_of("gathering_trial")
	if not occ.is_empty() and int(occ.k) == int(gt.k): return
	gt.paid = true
	var rank := trial_rank(c)
	var rw: Dictionary = CalendarRules.event("gathering_trial").get("rewards", {}).get(str(rank), CalendarRules.event("gathering_trial").get("rewards", {}).get("rest", {}))
	var fx: Array = []
	if str(rw.get("learn", "")) != "": fx.append({"kind": "learn_recipe", "recipe": str(rw.learn)})
	if str(rw.get("item", "")) != "": fx.append({"kind": "grant_item", "item": str(rw.item), "count": int(rw.get("count", 1))})
	game.apply_effects(c.id, fx, "gathering_trial")
	emit("gathering_trial_ranked", {"actor": c.id, "rank": rank, "points": int(gt.pts), "of": trial_rivals(int(gt.k), str(gt.get("room", ""))).size() + 1,
		"room": str(gt.get("room", ""))})

# ------------------------------------------------------------------ heavenly phenomena (S49 v1.0)
## A major breakthrough gathers auspicious clouds over the room; a tribulation darkens it with lightning. Everyone in
## the room sees it: the people there congratulate you (and a jealous senior may not let it pass; Relations).
func _on_breakthrough(p: Dictionary) -> void:
	if p.get("major", false): _phenomenon(str(p.get("actor", "")), "cloud", str(p.get("to", "")))

func _on_tribulation(p: Dictionary) -> void:
	_phenomenon(str(p.get("actor", "")), "lightning", str(p.get("to", "")))

func _phenomenon(actor_id: String, kind: String, realm: String) -> void:
	var c = game.character(actor_id)
	if c == null or game.room_rt == null: return
	var people := 0
	for o in game.room_rt.def.get("objects", []):
		if str(o.type) == "npc" and game.world.object_visible(c, o): people += 1
	emit("heavenly_phenomenon", {"actor": actor_id, "kind": kind, "realm": realm, "room": game.room_rt.room_id, "people": people})

# ------------------------------------------------------------------ the Heaven Ranking (S49 v1.1)
## The valley's seeded cultivators (rankings.json) climb on the account calendar. You enter at the top eight by CP,
## or by reaching the Valley Tournament finals. Beat the one ranked directly above you in a spar and you hold their
## place (and everyone's below it) for the rest of the week.
func rank_week() -> int:
	return CalendarRules.rank_week(Clock.now_utc(), origin())

func rank_entered(c, table: Array = []) -> bool:
	if c == null: return false
	if table.is_empty(): table = CalendarRules.rank_table(Clock.now_utc(), cal_seed(), origin())
	var cfg := ContentDB.config("rankings")
	if c.quests.done.has(str(cfg.get("finals_quest", "the_valley_finals"))): return true
	var top := int(cfg.get("top", 8))
	return table.size() < top or StatRules.combat_power(c) >= int(table[mini(top - 1, table.size()) - 1].cp)

## The whole table with you in it (when you have entered): [{id, name, title, level, cp, player?}], strongest first.
func ranking(c) -> Array:
	var table := CalendarRules.rank_table(Clock.now_utc(), cal_seed(), origin())
	if not rank_entered(c, table): return table
	var mine := StatRules.combat_power(c)
	var beaten: Dictionary = c.cooldowns.get("rank_beaten", {})
	for r in table:
		if int(beaten.get(str(r.id), -1)) == rank_week(): mine = maxi(mine, int(r.cp) + 1)
	table.append({"id": "_player", "name": str(c.name), "title": "", "level": ProgressionRules.level(c), "cp": mine, "player": true})
	table.sort_custom(func(a, b): return int(a.cp) > int(b.cp) or (int(a.cp) == int(b.cp) and a.get("player", false)))
	return table

## The ranked cultivator directly above you ({} at the top, or before you have entered).
func rank_above(c) -> Dictionary:
	var table := ranking(c)
	for i in table.size():
		if table[i].get("player", false): return table[i - 1] if i > 0 else {}
	return {}

func challenge_rank(c, npc: String) -> Dictionary:
	var above := rank_above(c)
	if above.is_empty() or str(above.id) != npc: return fail("not_above", {"text": Tx.t("sim.calendar.rank_not_above")})
	if game.room_rt != null and game.room_rt.event.get("active", false): return fail("busy")
	c.cooldowns["rank_duel"] = npc
	return game.quest.start_spar(c, str(above.enemy), int(above.level))

func _on_rank_spar(p: Dictionary) -> void:
	var c = game.active()
	if c == null or str(c.cooldowns.get("rank_duel", "")) == "": return
	var npc := str(c.cooldowns.rank_duel)
	var row := ContentDB.entry("rankings", npc)
	if str(p.get("opponent", "")) != str(row.get("enemy", "")): return
	c.cooldowns.erase("rank_duel")
	if str(p.get("winner", "")) != "player": return
	var beaten: Dictionary = c.cooldowns.get("rank_beaten", {})
	beaten[npc] = rank_week()
	c.cooldowns["rank_beaten"] = beaten
	game.relations.apply_deed(c.id, str(ContentDB.config("rankings").get("climb_deed", "rank_climbed")))
	emit("ranking_changed", {"actor": c.id, "beaten": npc})
