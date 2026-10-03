class_name WorldTower
extends WorldPart
## WorldAuthority's part: the Trial Tower (S49 v1.0). Thirty floors at the Fairground (tower.json), all in one room:
## each floor is a room event with its own rule. The floors you have cleared are World state on the character; each can
## be swept once a day for its loot.

func tower_floor(f: int) -> Dictionary:
	return ContentDB.entry("tower", "floor_%d" % f)

func tower_cleared(c) -> int:
	return int(c.tower.get("cleared", 0))

func tower_swept_today(c, f: int) -> bool:
	return int(c.tower.get("swept", {}).get(str(f), -1)) == Clock.reset_day(Clock.now_utc())

## Climb a floor: the next one, or any you have cleared before. The trial starts in the tower room.
func climb_tower(c, f: int) -> Dictionary:
	var row := tower_floor(f)
	if row.is_empty(): return fail("no_floor")
	if f > tower_cleared(c) + 1: return fail("locked", {"text": Tx.t("sim.world.tower_locked") % (tower_cleared(c) + 1)})
	if game.room_rt != null and game.room_rt.event.get("active", false): return fail("busy", {"text": Tx.t("sim.world.tower_busy")})
	var room := str(ContentDB.config("tower").get("room", "sf_trial_tower"))
	if game.room_rt == null or game.room_rt.room_id != room:
		if game.room_rt != null and world.prototype_gate(c, game.room_rt.room_id, room): return fail("gate", {"text": Tx.t("sim.world.road_being_drawn")})
		var moved := world.load_room(c, room, "entry")
		if not moved.get("ok", false): return moved
	var lv := int(row.level)
	var foes: Array = row.get("foes", [])
	var points: Array = world.room_events.side_points([[900, 860], [1300, 820], [1700, 860], [2100, 840]])
	var ev := {"id": "tower_floor", "floor": f, "clear_room": true, "duration": float(row.get("time_s", 60)),
		"on_complete": [{"kind": "tower_clear", "floor": f}]}
	match str(row.kind):
		"clear", "swift":
			var n := int(row.get("count", 4))
			var spawns: Array = []
			for i in n: spawns.append({"enemy": str(foes[i % foes.size()]), "at": points[i % points.size()], "level": lv})
			ev.fixed_spawns = spawns
			ev.kill_count = {"enemy": "*", "count": n}
		"survive":
			var waves: Array = []
			for i in foes.size():
				waves.append({"enemy": str(foes[i]), "first_s": 2.0 + i * 3.0, "every_s": 5.0, "max": 2, "level": lv, "points": points})
			ev.waves = waves
		_:
			ev.fixed_spawns = [{"enemy": str(row.guardian), "at": world.room_events.side_points([[1600, 850]])[0], "level": int(row.get("guardian_level", lv + 4))},
				{"enemy": str(foes[0]), "at": points[0], "level": lv}, {"enemy": str(foes[foes.size() - 1]), "at": points[3], "level": lv}]
			ev.win_on_kill = str(row.guardian)
	world.start_room_event(c, ev)
	return ok({"floor": f})

## A floor cleared: its loot at your feet; the first time, Spirit Stones and the floor's first-clear rewards (P7b: the
## guardians of floors 15-30 leave a Day's Incense) as well, and the next floor opens.
func apply_tower_clear(actor_id: String, f: int) -> void:
	var c = game.character(actor_id)
	var st: ActorState = game.actor_state(actor_id)
	var row := tower_floor(f)
	if c == null or row.is_empty(): return
	var first := f > tower_cleared(c)
	if first: c.tower["cleared"] = f
	if st != null and game.room_rt != null:
		world.loot.drop_loot(c, LootRules.roll(str(row.loot), Rng.stream(c.id, "loot"), int(row.level), c.stats.value("drop_rate"), c.stats.value("coin_find")),
			st.plane, 0.0, "tower")
	if first: game.apply_effects(c.id, [{"kind": "grant_currency", "currency": "spirit_stone", "amount": int(row.get("stones", 2))}] + row.get("first", []), "tower")
	emit("tower_floor_cleared", {"actor": c.id, "floor": f, "first": first})

## Sweep: each floor you have cleared gives its loot once a day, straight to the bag, without the fight.
## floor -1 sweeps every cleared floor not yet swept today.
func sweep_tower(c, f := -1) -> Dictionary:
	var day := Clock.reset_day(Clock.now_utc())
	var swept: Dictionary = c.tower.get("swept", {})
	var done := 0
	for i in range(1, tower_cleared(c) + 1):
		if (f > 0 and i != f) or int(swept.get(str(i), -1)) == day: continue
		var row := tower_floor(i)
		var drop := LootRules.roll(str(row.loot), Rng.stream(c.id, "loot"), int(row.level), c.stats.value("drop_rate"), c.stats.value("coin_find"), {"no_equipment": true})
		var fx: Array = []
		for it in drop.get("items", []):
			if not ContentDB.item(str(it.item)).is_empty() and int(it.count) > 0: fx.append({"kind": "grant_item", "item": str(it.item), "count": int(it.count)})
		var silver := int(drop.get("coins", 0)) + int(ContentDB.config("tower").get("sweep_silver_per_floor", 15))
		fx.append({"kind": "grant_currency", "currency": "silver_tael", "amount": silver})
		game.apply_effects(c.id, fx, "tower_sweep")
		swept[str(i)] = day
		done += 1
	c.tower["swept"] = swept
	if done == 0: return fail("nothing", {"text": Tx.t("sim.world.tower_nothing")})
	emit("tower_swept", {"actor": c.id, "floors": done})
	return ok({"floors": done})
