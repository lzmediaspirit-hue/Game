class_name WorldRoomEvents
extends WorldPart
## WorldAuthority's part: room events (survival, S27 night): a timed event in the loaded room (set pieces, sect defence,
## trials, the lantern defence) with its waves and timed spawns, won or lost, and the way on after it.

## Room events remember every blow the player takes: a flawless Heaven's Cleansing burns off residue (G1).
func on_hit_during_event(p: Dictionary) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null or not rt.event.get("active", false) or str(p.get("target_kind", "")) != "player": return
	if int(p.get("amount", 0)) > 0: rt.event.hits_taken = int(rt.event.get("hits_taken", 0)) + 1

## Start a timed event in the loaded room (set pieces, sect defence).
func start_room_event(c, ev: Dictionary) -> void:
	if game.room_rt: start_event(c, game.room_rt, ev)

## What a survived rift leaves behind: a chest's roll at the rift's level, dropped at your feet (S49).
func apply_rift_reward(actor_id: String, loot: String, level: int) -> void:
	var c = game.character(actor_id)
	var st: ActorState = game.actor_state(actor_id)
	if c == null or st == null: return
	var drop := LootRules.roll(loot, Rng.stream(c.id, "loot"), level, c.stats.value("drop_rate"), c.stats.value("coin_find"))
	world.loot.drop_loot(c, drop, st.plane, 0.0, "rift")

func start_event(c, rt: RoomRuntime, ev: Dictionary) -> void:
	if ev.has("requires") and not RequirementRules.passes(ev.requires, game.ctx(c)): return
	# Decision 45: an event already won before a reload (`won_if`: the Hollow Night's eel slain, the way on not yet
	# taken) comes back won, its foes gone and its rewards kept: only its way on waits (the scene after it, then Lu's boat).
	if ev.has("won_if") and RequirementRules.passes(ev.won_if, game.ctx(c)):
		rt.event = ev.duplicate(true)
		rt.event.active = false
		rt.event.remaining = 0.0
		if ev.get("leave") is Dictionary:
			rt.event.leaving = _leave_after(rt, ev)
		return
	rt.event = ev.duplicate(true)
	rt.event.active = true
	rt.event.remaining = float(ev.get("duration", 60))
	# A voyage lasts as long as its vessel takes to cross (S18).
	if world.voyages.has(c.id) and str(ev.get("id", "")) == "starsea_crossing":
		rt.event.remaining = float(world.voyages[c.id].get("seconds", rt.event.remaining))
	rt.event.duration = rt.event.remaining
	rt.event.spawn_timer = 2.0
	# Several waves can run at once, each on its own timer; timed spawns arrive once, part-way through.
	var waves: Array = ev.get("waves", [ev.wave] if ev.has("wave") else [])
	rt.event.waves = waves.duplicate(true)
	rt.event.wave_timers = []
	for w in waves: rt.event.wave_timers.append(float(w.get("first_s", 2.0)))
	rt.event.timed_done = []
	# A timed spawn decided as the event begins (`from_start`, decision 45: the eel risen awake after a reload) comes
	# only if its `requires` holds then; one that waits on the story later is never it.
	var ts_rows: Array = ev.get("timed_spawns", [])
	for i in ts_rows.size():
		if ts_rows[i].get("from_start", false) and not RequirementRules.passes(ts_rows[i].get("requires", {}), game.ctx(c)): rt.event.timed_done.append(i)
	rt.event.hits_taken = 0
	rt.event.kills = 0         # kill_count events (S48 Iron Body trial)
	if ev.get("lantern") is Dictionary: rt.event.light = float(ev.lantern.get("light", 100.0))   # v1.2 the lantern defence
	rt.event.ground_s = 0.0    # the pole trial: seconds on the ground in a row
	emit("room_event_started", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "duration": rt.event.remaining})
	# A Temper trial clears the ground: the room's own foes withdraw and wait for it to end (S48).
	if ev.get("clear_room", false):
		for e in rt.living_enemies():
			if not e.summoned and e.team == "enemy": game.enemies.release(e)
	for sp in ev.get("fixed_spawns", []):
		if sp.has("unless") and RequirementRules.passes(sp.unless, game.ctx(c)): continue
		game.enemies.spawn_at(str(sp.enemy), Vector2(float(sp.at[0]), float(sp.at[1])), int(sp.get("level", -1)))
	# A wave whose `unless` holds does not run this time (decision 45: the river's minnows fled the awakened eel).
	for w in rt.event.waves.duplicate():
		if w.has("unless") and RequirementRules.passes(w.unless, game.ctx(c)):
			var wi: int = rt.event.waves.find(w)
			rt.event.waves.remove_at(wi)
			rt.event.wave_timers.remove_at(wi)
	# The Reflection brings your heart demons with it: one for every 25 on the meter (G1).
	var demons := ProgressionRules.heart_demon_steps(c.cultivator) if str(ev.get("heart_demons", "")) != "" else 0
	for i in demons:
		game.enemies.spawn_at(str(ev.heart_demons), Vector2(700.0 + 260.0 * i, 860.0), int(ev.get("level", -1)))
	if demons > 0: emit("room_event_wave", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "enemy": str(ev.heart_demons),
		"text": Tx.t("sim.world.heart_demons_rise") % demons})

func tick_event(c, rt: RoomRuntime, delta: float) -> void:
	var ev: Dictionary = rt.event
	ev.remaining = float(ev.remaining) - delta
	var rng := Rng.stream(c.id, "world")
	var elapsed := float(ev.duration) - float(ev.remaining)
	for i in (ev.waves as Array).size():
		var w: Dictionary = ev.waves[i]
		# A wave that waits on the story (`requires`: the Hollow Night's villagers in the hut) starts when it first holds,
		# and runs `for_s` from then.
		var since := _part_since(c, ev, "wave%d" % i, w, elapsed)
		if since < 0.0 or (w.has("for_s") and elapsed - since > float(w.for_s)): continue
		ev.wave_timers[i] = float(ev.wave_timers[i]) - delta
		if float(ev.wave_timers[i]) > 0.0: continue
		if w.has("until_s") and elapsed > float(w.until_s): continue   # its part of the event is over
		ev.wave_timers[i] = float(w.get("every_s", 4.0))
		var alive := 0
		for e in rt.living_enemies():
			if e.def_id == str(w.enemy) and (e.summoned or not ev.get("clear_room", false)): alive += 1
		if alive < int(w.get("max", 6)):
			var pts: Array = w.get("points", [[400, 800]])
			var p: Array = pts[rng.randi_range(0, pts.size() - 1)]
			var we: EnemyState = game.enemies.spawn_at(str(w.enemy), Vector2(float(p[0]), float(p[1])), event_level(c, w))
			# A wave that `hunt`s comes for the player wherever they stand (the Hollow Night's minnows up the bank and the lane).
			if we != null and w.get("hunt", false): we.threat[c.id] = 1.0
	var timed: Array = ev.get("timed_spawns", [])
	for i in timed.size():
		if i in ev.timed_done: continue
		# A timed spawn arrives `after_s` into the event; one that waits on the story, `delay_s` after its `requires` first
		# holds, and at `latest_s` whatever the story (the Hollow Night's eel, should the villagers never reach the hut).
		# One whose `unless` holds never comes (decision 45: the eel risen awake after a reload comes by its own row).
		if timed[i].has("unless") and RequirementRules.passes(timed[i].unless, game.ctx(c)):
			ev.timed_done.append(i)
			continue
		var ts := _part_since(c, ev, "timed%d" % i, timed[i], elapsed)
		var due := ts >= 0.0 and elapsed >= maxf(float(timed[i].get("after_s", 0.0)), ts + float(timed[i].get("delay_s", 0.0)))
		if not due and not (timed[i].has("latest_s") and elapsed >= float(timed[i].latest_s)): continue
		ev.timed_done.append(i)
		game.enemies.spawn_at(str(timed[i].enemy), Vector2(float(timed[i].at[0]), float(timed[i].at[1])), int(timed[i].get("level", -1)))
		emit("room_event_wave", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "enemy": str(timed[i].enemy),
			"text": str(timed[i].get("text", ""))})
	# v1.2 the lantern defence (the Hollow Tide battle): every foe near the lantern drains its light; standing beside it
	# without striking relights it. At no light the battle is lost; alive when the timer ends, it is won.
	if ev.get("lantern") is Dictionary and not ev.lantern.is_empty():
		if _tick_lantern(c, rt, ev, delta):
			end_event(c, rt, false, "lantern")
			return
	# S48 Temper trials: fall below the HP floor, or stand on the ground too long in the pole trial, and it is over.
	if float(ev.get("hp_floor", 0.0)) > 0.0 and c.pools.hp < c.pools.max_hp * float(ev.hp_floor):
		end_event(c, rt, false, "hp_floor")
		return
	if ev.has("ground_grace_s"):
		var st: ActorState = game.actor_state(c.id)
		var grounded := st != null and st.mode() == "ground" and st.surface != null and not st.surface.is_block and st.surface.stratum == "ground"
		ev.ground_s = float(ev.ground_s) + delta if grounded and elapsed > float(ev.get("ground_free_s", 5.0)) else 0.0
		if float(ev.ground_s) > float(ev.ground_grace_s):
			end_event(c, rt, false, "ground")
			return
	if float(ev.remaining) <= 0.0:
		# A kill-to-win event (a trial) that runs out of time is failed, not passed; one whose foe can also be outlasted
		# (`timeout_wins`: the Hollow Night, where Lu comes at its end) is won either way.
		if (ev.has("win_on_kill") or ev.has("kill_count")) and not ev.get("timeout_wins", false):
			end_event(c, rt, false, "time")
		else:
			end_event(c, rt, true, "time" if ev.get("timeout_wins", false) else "")

## When a part of an event (a wave, a timed spawn) that waits on the story opened: the event's elapsed seconds its
## `requires` first held at (0 without one), and -1 while it has not.
func _part_since(c, ev: Dictionary, key: String, part: Dictionary, elapsed: float) -> float:
	if not part.has("requires"): return 0.0
	var opened: Dictionary = ev.get("opened", {})
	if not opened.has(key):
		if not RequirementRules.passes(part.requires, game.ctx(c)): return -1.0
		opened[key] = elapsed
		ev.opened = opened
	return float(opened[key])

## A won event's way on (the Hollow Night's: to Lu's boat), `leave` {after_s, grid_after_s, requires, effects}: its
## effects once its requirement holds (the scene after the fight has played) or its seconds of the room's time have
## passed, whichever comes first. The room keeps it while the event's cut holds the game still.
func tick_leave(c, rt: RoomRuntime, delta: float) -> void:
	var lv: Dictionary = rt.event.get("leave", {})
	rt.event.leaving = float(rt.event.leaving) - delta
	if float(rt.event.leaving) > 0.0 and not (lv.has("requires") and RequirementRules.passes(lv.requires, game.ctx(c))): return
	rt.event.erase("leaving")
	# What the fight left on the ground goes with you (the eel's fang, its pearl and taels), gathered up as you leave.
	for l in rt.loot.duplicate(): world.loot.collect(c, l)
	game.apply_effects(c.id, lv.get("effects", []), "event:" + str(rt.event.get("id", "")) + ":leave")

## One step of the lantern's light (0-100): true when it has gone out.
func _tick_lantern(c, rt: RoomRuntime, ev: Dictionary, delta: float) -> bool:
	var ln: Dictionary = ev.lantern
	var o := rt.object_def(str(ln.get("object", "")))
	if o.is_empty(): return false
	var at_arr: Array = o.get("at", [0, 0])
	var at := Vector2(float(at_arr[0]), float(at_arr[1]))
	var near := 0
	for e in rt.living_enemies():
		if e.team == "enemy" and not e.hidden and e.plane.distance_to(at) <= float(ln.get("drain_radius", 180)): near += 1
	var light := float(ev.get("light", ln.get("light", 100.0)))
	light -= float(ln.get("drain_per_foe", 3.0)) * near * delta
	var st: ActorState = game.actor_state(c.id)
	var striking: bool = game.combat.is_busy(c.id)
	if st != null and near == 0 and not striking and st.plane.distance_to(at) <= float(ln.get("relight_radius", 120)):
		light += float(ln.get("relight", 4.0)) * delta
	light = clampf(light, 0.0, float(ln.get("light", 100.0)))
	var was := int(ceil(float(ev.get("light", 100.0)) / 10.0))
	ev.light = light
	if int(ceil(light / 10.0)) != was: emit("lantern_light", {"actor": c.id, "room": rt.room_id, "light": light, "near": near})
	return light <= 0.0

## The level a wave's foes come at: a number, or "player" for the character's own Level (the Temper trials).
func event_level(c, w: Dictionary) -> int:
	if str(w.get("level", "")) == "player":
		return clampi(ProgressionRules.level(c) + int(w.get("level_offset", 0)), int(w.get("level_min", 1)), int(w.get("level_max", 999)))
	return int(w.get("level", -1))

func end_event(c, rt: RoomRuntime, won: bool, reason := "") -> void:
	var ev: Dictionary = rt.event
	ev.active = false
	emit("room_event_completed" if won else "room_event_failed", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "reason": reason})
	for e in rt.living_enemies():
		if e.summoned: game.enemies.release(e)   # the rest scatter: no loot, no kill credit
	game.apply_effects(c.id, ev.get("on_complete" if won else "on_timeout", []), "event:" + str(ev.get("id", "")))
	if won and int(ev.get("hits_taken", 0)) == 0 and not ev.get("on_flawless", []).is_empty():
		emit("room_event_flawless", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", ""))})
		game.apply_effects(c.id, ev.on_flawless, "event:" + str(ev.get("id", "")) + ":flawless")
	if won and ev.get("leave") is Dictionary and game.room_rt == rt: ev.leaving = _leave_after(rt, ev)

## How long a won event's way on (`leave`) waits: on the height grid, where the scene after the fight plays (behind
## whatever moments the win brings), longer (`grid_after_s`); in the side view, which stages no scenes, `after_s`.
static func _leave_after(rt: RoomRuntime, ev: Dictionary) -> float:
	return float(ev.leave.get("grid_after_s" if not WorldAuthority.side_view(rt) else "after_s", ev.leave.get("after_s", 0.0)))

## A kill-to-win event ends the moment its foe falls.
func event_kill(p: Dictionary) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null or not rt.event.get("active", false): return
	if str(rt.event.get("win_on_kill", "")) != "" and str(p.get("def", "")) == str(rt.event.win_on_kill):
		var c = game.active()
		if c != null: end_event(c, rt, true)
		return
	# S48 Iron Body trial: so many of one foe in a single run.
	var kc: Dictionary = rt.event.get("kill_count", {})
	if not kc.is_empty() and (str(kc.get("enemy", "")) == "*" or str(p.get("def", "")) == str(kc.get("enemy", ""))) and str(p.get("victim_kind", "enemy")) == "enemy":
		rt.event.kills = int(rt.event.get("kills", 0)) + 1
		var c2 = game.active()
		if c2 != null: emit("room_event_wave", {"actor": c2.id, "room": rt.room_id, "event": str(rt.event.get("id", "")), "enemy": str(kc.enemy),
			"text": Tx.t("sim.world.trial_kills") % [int(rt.event.kills), int(kc.get("count", 1))]})
		if c2 != null and int(rt.event.kills) >= int(kc.get("count", 1)): end_event(c2, rt, true)
