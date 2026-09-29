extends "res://tests/prologue_run.gd"
## hollow_night (decision 42: "The Hollow Night feels boring with no action, also there is a bug that I can't kill the
## monsters"; docs/redesign/story_staging.md "The Hollow Night"): the night's set piece on the height grid, as a new
## top-down character meets it, through the real authorities and the real combat.
##   1. the kill bug: each of the night's foes (a Hollow Minnow, the Hollowed Eel) falls to the player's basic attack
##      and, on its own, to a technique, in lf_village_night on the grid. The minnows skim inside the blow's height band
##      (they hovered 40-56 over the floor, out of every blow's band, and their own darts out of the player's), a tap's
##      soft lock finds them, and their darts reach the player; the eel is unhurt in the river (out of the band, and
##      invulnerable there) and open to blows once it lies ashore after its lunge;
##   2. the night played by a careful new player at the story's Level (a Mortal in the kit the story has handed out:
##      the first crab's short blade, the straw hat, three teas): the minnows about each villager, the three sent to
##      Aunt Ping's door (each runs there), the grey spreading up the lane, the eel rising (its card), its climax below
##      half its HP (Lu comes, his palm), its fall to the player, the grey lifting, and Lu's boat; two to four minutes of
##      the night's own time, every staged scene of it played to its end, the rewards in the bag (the eel's fang, a river
##      pearl, taels, the title), never a fall;
##   3. held until Lu comes: a player who sends the villagers in and keeps to the lamplight at Aunt Ping's door is let
##      be by the minnows, and the night is won when its time runs out (the eel driven off, no fang), on to the boat;
##   4. a fall in the night wakes the player at Aunt Ping's door, in the night, and the night begins again (never in the
##      day village with the night unfinished).
## Run headless:  godot --headless --path . res://tests/hollow_night.tscn [-- --verbose]

const NIGHT := "lf_village_night"
const KIT_WEAPON := "training_short_blade"
var beats: Array = []   # [sim seconds into the night, what]

func _main() -> void:
	create_extra = {"view": "topdown"}
	scene_director = SceneDirector.new()
	scene_director.pages_override = false
	add_child(scene_director)
	scene_director.set_process(false)
	tick_watch = func():
		scene_director.advance(0.05)
		settle_scenes()
	start_new("saves/")
	_kill_each_foe()
	_the_night_played()
	_held_until_lu()
	_a_fall_in_the_night()
	if is_instance_valid(scene_director): scene_director.free()
	print("hollow_night: %d checks, %d failures" % [checks, failures])
	end_suite()

## The staged scenes play out on the director's clock around each step, as topdown_tutorial plays them.
func submit(i: Dictionary) -> Dictionary:
	settle_scenes()
	var r := super(i)
	settle_scenes()
	return r

# ------------------------------------------------------------------ the story's character at the night
## The character as the story brings it to the night: the prologue's lessons and Crab Trouble done (their HUD revealed),
## the first crab's short blade in hand and the straw hat on, three teas; then the evening on the river's own effects
## (Aunt Ping's congee, the night falling). `arts`: Flowing Palm slotted too (a technique, for the kill test only).
func _to_the_night(arts := false) -> void:
	var ch = c()
	Game.combat.wounded.erase(ch.id)
	Unlocks.grant_prologue(ch.id)
	for q in ["morning_tide", "a_quiet_river", "the_runaway_kite", "mas_delivery", "grannys_remedy", "fists_first", "crab_trouble",
			"evening_on_the_river", "the_hollow_night", "the_river_token"]:
		ch.quests.active.erase(q)
		ch.quests.offered.erase(q)
		if q in ["the_hollow_night", "the_river_token"]: ch.quests.done.erase(q)
		else: ch.quests.done[q] = 1
	for f in ["night_active", "night_survived", "dou_safe", "granny_safe", "ma_safe", "grey_spread", "lu_on_the_bank", "first_defeat:hollowed_eel:hollow_eel_fang"]:
		ch.quests.flags.erase(f)
	ch.cultivator.titles.erase("ferry_guardian")
	ch.quests.scenes.clear()
	ch.inventory.equipped["weapon"] = LootRules.make_instance(KIT_WEAPON, int(ContentDB.item(KIT_WEAPON).get("ilv", 1)), "common", null, ch.inventory.take_uid())
	ch.inventory.equipped["hat"] = LootRules.make_instance("plain_straw_hat", int(ContentDB.item("plain_straw_hat").get("ilv", 1)), "common", null, ch.inventory.take_uid())
	for i in ch.inventory.bag.size():
		if ch.inventory.bag[i] != null and str(ch.inventory.bag[i].id) in ["herbal_tea", "hollow_eel_fang", "pearl", "tiny_hollow_shard"]: ch.inventory.bag[i] = null
	Game.inventory.apply_add(ch.id, "herbal_tea", 3, "hollow_night")
	ch.cultivator.techniques_known.erase("flowing_palm")
	for i in ch.cultivator.technique_slots.size(): ch.cultivator.technique_slots[i] = null
	if arts:
		Unlocks.force_unlock(ch.id, "technique_slots_2")
		Game.progression.apply_learn_technique(ch.id, "flowing_palm")
		ch.cultivator.technique_slots[0] = "flowing_palm"
	ch.pools.statuses.clear()
	ch.pools.cooldowns.clear()
	StatRules.rebuild(ch)
	scene_director.queue.clear()
	Game.apply_effects(ch.id, ContentDB.entry("quests", "evening_on_the_river").get("rewards", []), "hollow_night")
	GameEvents.flush()
	place(Vector2(float(ch.position.x), float(ch.position.y)))

# ------------------------------------------------------------------ 1: the kill bug
## Each night foe falls to a basic attack, and to a technique alone, on the grid.
func _kill_each_foe() -> void:
	for how in ["basic", "technique"]:
		for def_id in ["hollow_minnow", "hollowed_eel"]:
			_to_the_night(how == "technique")
			check(room() == NIGHT and Game.room_rt.topdown != null and Game.room_rt.event.get("active", false),
				"the night falls on the grid, its event under way (%s, %s)" % [room(), str(Game.room_rt.event.get("id", ""))])
			# The foe alone, the event's waves and the eel's rising held back.
			for e in Game.room_rt.living_enemies(): Game.room_rt.enemies.erase(e.uid)
			Game.room_rt.event.waves = []
			Game.room_rt.event.timed_spawns = []
			var grid: TopdownRoom = Game.room_rt.topdown
			place(TopdownRoom.cell_point([30, 33]))
			var e: EnemyState
			if def_id == "hollow_minnow":
				e = Game.enemies.spawn_at(def_id, grid.nearest_standable(st.plane + Vector2(40, 0)), 1)
				_minnow_in_reach(e, how)
			else:
				e = Game.enemies.spawn_at(def_id, TopdownRoom.cell_point([30, 36.5]), 2)
				_eel_in_the_river(e)
				# A technique alone waits out its cooldown between casts: the eel comes to it already hurt.
				if how == "technique": e.pools.hp = e.pools.max_hp * 0.3
			var killed := _strike_until_down(e, how, 150.0)
			check(killed, "%s: the %s falls to the player's %s on the grid (HP %d/%d)" % [how, ContentDB.name_of("enemies", def_id), "basic attack" if how == "basic" else "technique alone",
				int(e.pools.hp), int(e.pools.max_hp)])

## A minnow on the grid skims inside the blow's height band, a tap's soft lock finds it, and its dart reaches the player.
func _minnow_in_reach(e: EnemyState, how: String) -> void:
	var dz: Array = []
	var darts := {"n": 0}
	var hit := func(n: String, p: Dictionary):
		if n == "hit_landed" and str(p.get("attacker", "")) == str(e.uid) and str(p.get("target", "")) == str(c().id): darts.n = int(darts.n) + 1
	GameEvents.event.connect(hit)
	c().pools.statuses.clear()   # past the moment of spawn protection a room gives on arrival
	e.ai.state = "aggro"
	for i in 100:
		step(0.05)
		dz.append(e.altitude + e.hover - st.altitude)
		if st.plane.distance_to(e.plane) > 36.0: place(e.plane + Vector2(-28, 0))
	GameEvents.event.disconnect(hit)
	var in_band := dz.all(func(z): return TopdownAim.compatible(float(z)))
	check(in_band, "the minnow skims inside the blow's height band on the grid, its feet %.0f..%.0f over the player's (band %s)" % [dz.min(), dz.max(), str(TopdownAim.band(false))])
	var lock := TopdownAim.soft_target(Game.room_rt.living_enemies(), st.plane, st.altitude, (e.plane - st.plane).normalized())
	check(lock == e, "a tap's soft lock finds the minnow beside the player (%s)" % str(lock.def_id if lock else "none"))
	if how == "basic": check(int(darts.n) > 0, "the minnow's dart reaches the player on the grid (%d darts landed in 5 s)" % int(darts.n))

## The eel in the river is unhurt: out of the blow's band and the soft lock, and invulnerable there.
func _eel_in_the_river(e: EnemyState) -> void:
	step(0.3)
	var lock := TopdownAim.soft_target(Game.room_rt.living_enemies(), st.plane, st.altitude, (e.plane - st.plane).normalized())
	var hp := e.pools.hp
	Game.combat._player_hits_enemy(c(), Game.combat.player_view(c()), e, {"damage_type": "physical", "element": "none", "mult": [1.0, 1.0], "range": [1.0, 1.0]}, 1)
	check(lock == null and e.invulnerable and not TopdownAim.compatible(e.altitude + e.hover - st.altitude) and e.pools.hp == hp,
		"the eel gliding in the river is out of every blow's band and the soft lock, and unhurt there (feet %.0f, lock %s, HP %d -> %d)"
		% [e.altitude + e.hover - st.altitude, str(lock.def_id if lock else "none"), int(hp), int(e.pools.hp)])

## Strike `e` until it falls, as a player who reads the eel's tell: out of its line when it rears, beside it while it
## lies ashore (the eel's window), on the bank above it while it glides; a minnow is met where it is. `how`: the basic
## attack only, or the technique only. True when it fell to the player.
func _strike_until_down(e: EnemyState, how: String, limit_s: float) -> bool:
	var down := {"by": ""}
	var heard := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("victim", "")) == str(e.uid): down.by = str(p.get("killer", ""))
	GameEvents.event.connect(heard)
	var t := 0.0
	var dodged := Vector2.INF
	var shore := {"lock": false, "band": false}
	while e.alive and t < limit_s and not Game.combat.is_wounded(c().id):
		var s := str(e.ai.get("state", ""))
		var eel := e.def_id == "hollowed_eel"
		if eel and s == "windup":
			var land: Vector2 = e.ai.get("land", e.plane)
			if land != dodged:
				place(land + Vector2(-e.aim.y, e.aim.x) * 72.0)
				dodged = land
		elif not eel or s in ["attack", "beached"]:
			if st.plane.distance_to(e.plane) > 40.0: place(e.plane + Vector2(-30.0 if st.plane.x <= e.plane.x else 30.0, 0))
			if eel and s == "beached" and not shore.lock:
				shore.lock = TopdownAim.soft_target(Game.room_rt.living_enemies(), st.plane, st.altitude, (e.plane - st.plane).normalized()) == e
				shore.band = not e.invulnerable and TopdownAim.compatible(e.altitude + e.hover - st.altitude)
			var aim := aim_at(e.plane)
			var facing := 1 if e.plane.x >= st.plane.x else -1
			if how == "technique": submit({"type": "use_technique", "slot": 0, "facing": facing, "aim": aim})
			else: submit({"type": "basic_attack", "facing": facing, "aim": aim})
		elif st.plane.distance_to(e.plane) > 120.0:
			place(Game.room_rt.topdown.nearest_standable(e.plane + Vector2(0, -96)))
		if c().pools.hp < c().pools.max_hp * 0.4 and c().inventory.count("herbal_tea") > 0:
			submit({"type": "use_item", "index": c().inventory.first_index("herbal_tea"), "confirm": true})
		step(0.2)
		t += 0.2
	GameEvents.event.disconnect(heard)
	if e.def_id == "hollowed_eel":
		check(shore.lock and shore.band, "ashore after its lunge the eel is open: inside the blow's band, not invulnerable, and a tap's soft lock finds it (%s)" % str(shore))
	if verbose: print("  %s by %s: %s after %.1f s, HP %d/%d" % [e.def_id, how, "down" if not e.alive else "standing", t, int(c().pools.hp), int(c().pools.max_hp)])
	return down.by == str(c().id)

# ------------------------------------------------------------------ 2: the night played through
func _the_night_played() -> void:
	_to_the_night()
	var ch = c()
	var t0 := Game.sim_time
	var p0 := play_s
	var taels0: int = Game.economy.balance("silver_tael", ch)
	var hp_low := {"v": 1.0, "fell": false}
	beats.clear()
	var log_beat := func(n: String, p: Dictionary):
		var what := ""
		match n:
			"actor_defeated":
				if str(p.get("def", "")) == "hollowed_eel": what = "eel down by " + ("player" if str(p.get("killer", "")) == str(ch.id) else str(p.get("killer", "")))
				elif str(p.get("def", "")) == "hollow_minnow" and not beats.any(func(b): return str(b[1]) == "first minnow"): what = "first minnow"
			"flag_set": if str(p.get("flag", "")) in ["dou_safe", "granny_safe", "ma_safe", "night_survived"]: what = str(p.flag)
			"enemy_aggro": if str(p.get("def", "")) == "hollowed_eel": what = "eel rises"
			"boss_phase": if str(p.get("action", "")) == "climax": what = "climax"
			"room_event_completed": what = "night won (%s)" % str(p.get("reason", ""))
			"scene_ended": what = "scene " + str(p.get("scene", ""))
			"room_entered": what = "room " + str(p.get("room", ""))
			"player_gravely_wounded": hp_low.fell = true
		if what != "": beats.append([Game.sim_time - t0, what])
	GameEvents.event.connect(log_beat)
	var watch := func():
		scene_director.advance(0.05)
		settle_scenes()
		hp_low.v = minf(float(hp_low.v), c().pools.hp / c().pools.max_hp) if room() == NIGHT else float(hp_low.v)
	tick_watch = watch
	settle_scenes()
	step_night()
	GameEvents.event.disconnect(log_beat)
	var took := play_s - p0
	var order: Array = beats.map(func(b): return str(b[1]))
	print("the night (%.0f s on the play clock, %.0f s of the simulation): %s" % [took, Game.sim_time - t0, ", ".join(beats.map(func(b): return "%d s %s" % [int(b[0]), b[1]]))])
	# The play clock (prologue_run.play_s): the simulated seconds, the walking between the spots stood at, the lines read
	# and the cuts watched; a floor for a focused player, as the first hour's pacing reads it.
	check(took >= 120.0 and took <= 240.0, "the Hollow Night lasts two to four minutes on the play clock (%.0f s)" % took)
	var want := ["first minnow", "eel rises", "climax", "eel down by player", "night won ()", "scene grey_lifts", "night_survived", "room lf_lu_boat"]
	var at := -1
	var in_order := true
	for w in want:
		var i: int = order.find(w, at + 1)
		if i < 0: in_order = false
		at = maxi(at, i)
	check(in_order, "its beats come in order: %s (%s)" % [", ".join(want), ", ".join(order)])
	for v in ["dou_safe", "granny_safe", "ma_safe"]:
		check(order.find(v) >= 0 and order.find(v) < order.find("eel rises"), "%s before the eel rises" % v)
	var played := {}
	for f in scene_director.finished: played[str(f.scene)] = not f.skipped
	var scenes := ["hollow_rises", "night_ma_goes", "night_granny_goes", "night_dou_runs", "grey_spreads", "eel_rises", "lu_arrives", "grey_lifts"]
	var missed := scenes.filter(func(s): return not played.get(s, false))
	check(missed.is_empty(), "every staged scene of the night played to its end (missed %s)" % str(missed))
	check(not hp_low.fell and float(hp_low.v) >= 0.25, "a careful new player comes through it without a fall, HP never under a quarter (%d%%)" % int(100.0 * float(hp_low.v)))
	check(ch.inventory.count("hollow_eel_fang") == 1 and ch.inventory.count("pearl") >= 1, "the eel's first defeat leaves its fang (a rare find) and a river pearl (fang %d, pearl %d)"
		% [ch.inventory.count("hollow_eel_fang"), ch.inventory.count("pearl")])
	check(ch.cultivator.titles.has("ferry_guardian"), "the night held earns the title Guardian of Lotus Ferry")
	check(Game.economy.balance("silver_tael", ch) > taels0, "the eel's hoard pays in taels (%d -> %d)" % [taels0, Game.economy.balance("silver_tael", ch)])
	check(ch.inventory.count("tiny_hollow_shard") >= 1, "the minnows leave grey slivers behind (%d Tiny Hollow Shards)" % ch.inventory.count("tiny_hollow_shard"))
	check(room() == "lf_lu_boat" and ch.quests.is_done("the_hollow_night") and ch.quests.is_active("the_river_token"), "on to Lu's boat: The River Token under way (%s)" % room())
	# The night leaves nothing held: on the boat the first meditation fills the bar, as The River Token asks.
	place(obj_at("boat_spring") + Vector2(0, -10))
	var med := submit({"type": "start_meditation"})
	var m := 0.0
	while ch.cultivator.state != "bottleneck" and m < 120.0:
		step(1.0)
		m += 1.0
	check(ch.cultivator.state == "bottleneck", "after the night the boat's meditation fills the bar (%s; %.0f s; paused %s, cut %s, %.0f%%)" % [str(med), m, str(Game.paused),
		str(scene_director.in_cut()), 100.0 * ch.cultivator.progress_fraction()])
	submit({"type": "stop_meditation"})
	tick_watch = func():
		scene_director.advance(0.05)
		settle_scenes()

# ------------------------------------------------------------------ 3: held until Lu comes
func _held_until_lu() -> void:
	_to_the_night()
	var ch = c()
	for npc in ["old_ma", "granny_liu", "little_dou"]: talk_choose(npc, "effects")
	var refuge := obj_at("hut_refuge")
	place(refuge + Vector2(0, 24))
	var hp0: float = ch.pools.hp
	var how := {"reason": "-", "eel": false}
	var heard := func(n: String, p: Dictionary):
		if n == "room_event_completed": how.reason = str(p.get("reason", ""))
		if n == "enemy_spawned" and str(p.get("def", "")) == "hollowed_eel": how.eel = true
	GameEvents.event.connect(heard)
	var t := 0.0
	while room() == NIGHT and t < 260.0:
		step(0.5)
		t += 0.5
	GameEvents.event.disconnect(heard)
	check(how.eel and how.reason == "time", "held until Lu comes: the eel rose, and the night is won when its time runs out (%s)" % str(how))
	check(ch.pools.hp >= hp0, "in the lamplight at Aunt Ping's door the grey minnows let the player be (HP %d -> %d)" % [int(hp0), int(ch.pools.hp)])
	check(ch.inventory.count("hollow_eel_fang") == 0 and room() == "lf_lu_boat" and ch.quests.is_done("the_hollow_night"),
		"the eel driven off leaves no fang, and the night goes on to Lu's boat (%s)" % room())

# ------------------------------------------------------------------ 4: a fall in the night
func _a_fall_in_the_night() -> void:
	_to_the_night()
	var ch = c()
	for e in Game.room_rt.living_enemies(): Game.room_rt.enemies.erase(e.uid)
	var grid: TopdownRoom = Game.room_rt.topdown
	place(TopdownRoom.cell_point([30, 30]))
	ch.pools.hp = 1.0
	var m: EnemyState = Game.enemies.spawn_at("hollow_minnow", grid.nearest_standable(st.plane + Vector2(30, 0)), 1)
	m.ai.state = "aggro"
	var t := 0.0
	while not Game.combat.is_wounded(ch.id) and t < 20.0:
		step(0.1)
		t += 0.1
	check(Game.combat.is_wounded(ch.id), "a minnow's dart can down a player at 1 HP")
	submit({"type": "choose_revival", "where": "shrine"})
	GameEvents.flush()
	var at := Vector2(float(ch.position.x), float(ch.position.y))
	check(room() == NIGHT and at.distance_to(obj_at("hut_refuge")) < 96.0 and Game.room_rt.event.get("active", false) and ch.pools.hp >= ch.pools.max_hp * 0.99,
		"a fall in the night wakes the player whole at Aunt Ping's door, in the night, and the night begins again (%s at %s)" % [room(), str(at)])
