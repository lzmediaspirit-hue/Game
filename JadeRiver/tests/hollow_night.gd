extends "res://tests/prologue_run.gd"
## hollow_night (decision 42: "The Hollow Night feels boring with no action, also there is a bug that I can't kill the
## monsters"; decision 45: "the boss should start phase 2 at 80% HP and become super strong so the player can't defend
## it. Then a cut scene where the elders of the village save the player"; docs/redesign/story_staging.md "The Hollow
## Night" and "The first boss"): the night's set piece on the height grid, as a new top-down character meets it,
## through the real authorities, the real combat and a headless director playing its scenes.
##   1. the kill bug: a Hollow Minnow falls to the player's basic attack and, on its own, to a technique, in
##      lf_village_night on the grid (it skims inside the blow's height band, a tap's soft lock finds it, its darts reach
##      the player); the Hollowed Eel is unhurt in the river (out of the band, and invulnerable there), open to blows
##      once it lies ashore after its lunge, and the player's blows alone (the basic attack, or a technique) drive it to
##      its waking at four fifths of its HP;
##   2. the first boss cannot be won and cannot kill: awake, its hide holds its HP at its floor under a blow of a billion,
##      a burn and a technique; no blow takes the player under 30% of their HP, and the one that reaches it ends the
##      fight; its surge passes a guard and a parry and takes its share whatever the player wears; the fight ends in
##      the player overwhelmed (the eel looming, the player held down) and, with no scene on the stage, the elders
##      slay it in the simulation;
##   3. the night played by a careful new player at the story's Level (a Mortal in the kit the story has handed out:
##      the first crab's short blade, the straw hat, three teas): the minnows about each villager, the three sent to
##      Aunt Ping's door, the grey spreading up the lane, the eel rising (its card), its first phase won by the
##      player's blows, its waking at 80% (its scene), the player overwhelmed, the elders' rescue (its scene, in which
##      the eel dies), the grey lifting (its scene) and Lu's boat, where cultivation opens after (its unlock and the
##      page's tutorial); three to five minutes of the night's own time, every staged scene of it played to its end,
##      the rewards in the bag (the eel's fang, a river pearl, taels, the title), never a fall;
##   4. no soft-lock, whatever the player does: one who keeps to the lamplight and never strikes the eel still meets
##      its waking (its clock) and is overwhelmed (the river rises), and the elders still come; a fall in its first
##      phase wakes the player at Aunt Ping's door and the night begins again, and ends in the rescue all the same;
##   5. a reload mid-fight: in its second phase the eel rises again at once, awake, with no minnows, and the elders
##      come; in the rescue cut short, it plays again whole when the eel has them down again, and slays it; after the
##      eel is slain, the night comes back won and its last scene plays, on to Lu's boat.
## Run headless:  godot --headless --path . res://tests/hollow_night.tscn [-- --verbose]

const NIGHT := "lf_village_night"
const KIT_WEAPON := "training_short_blade"
const EEL := "hollowed_eel"
var beats: Array = []   # [sim seconds into the night, what]

func _main() -> void:
	create_extra = {"view": "topdown"}
	_new_director()
	tick_watch = func():
		scene_director.advance(0.05)
		settle_scenes()
	start_new("saves/")
	_kill_each_foe()
	_cannot_be_won()
	_the_night_played()
	_flees_to_the_lamplight()
	_a_fall_in_the_night()
	_the_waking_takes_the_stage()
	_reload_awake()
	_reload_in_the_rescue()
	_reload_after_the_kill()
	if is_instance_valid(scene_director): scene_director.free()
	Game.pause(false)
	end_suite()

func _new_director() -> void:
	scene_director = SceneDirector.new()
	scene_director.pages_override = false
	add_child(scene_director)
	scene_director.set_process(false)

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
	Game.pause(false)
	Game.combat.wounded.erase(ch.id)
	Unlocks.grant_prologue(ch.id)
	# What the night itself opens (night_survived: Cultivate, the Cultivation page, the breakthrough, the Codex) is shut
	# again, its HUD hidden and its tutorials not yet due: the night opens them.
	for entry in ContentDB.all("unlocks"):
		if JSON.stringify(entry.get("trigger", {})).contains("night_survived"):
			ch.cultivator.unlocked.erase(entry.id)
			for r in entry.get("reveals", []): ch.cultivator.revealed.erase(r)
			var tut: Dictionary = Game.tutorials.state(ch)
			for k in ["queue"]: (tut[k] as Array).erase(entry.id)
			for k in ["seen", "guided", "at"]: (tut[k] as Dictionary).erase(entry.id)
	for q in ["morning_tide", "a_quiet_river", "the_runaway_kite", "mas_delivery", "grannys_remedy", "fists_first", "crab_trouble",
			"evening_on_the_river", "the_hollow_night", "the_river_token"]:
		ch.quests.active.erase(q)
		ch.quests.offered.erase(q)
		if q in ["the_hollow_night", "the_river_token"]: ch.quests.done.erase(q)
		else: ch.quests.done[q] = 1
	for f in ["night_active", "night_survived", "dou_safe", "granny_safe", "ma_safe", "grey_spread", "lu_on_the_bank", "first_defeat:hollowed_eel:hollow_eel_fang",
			"eel_awakened", "eel_overwhelmed", "night_held"]:
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

## The villagers already in (their flags, as the talks set them): the eel rises 14 s on.
func _villagers_in() -> void:
	for f in ["dou_safe", "granny_safe", "ma_safe"]: Game.quest.apply_flag(c().id, f)
	GameEvents.flush()

## The night's eel, once it has risen (at most `limit` s of the simulation).
func _await_eel(limit := 40.0) -> EnemyState:
	var t := 0.0
	while _night_foe(EEL) == null and t < limit and room() == NIGHT:
		step(0.25)
		t += 0.25
	return _night_foe(EEL)

## The foe alone in the night: its minnows gone, the event's waves and its eel's rising held back.
func _alone() -> void:
	for e in Game.room_rt.living_enemies(): Game.room_rt.enemies.erase(e.uid)
	Game.room_rt.event.waves = []
	Game.room_rt.event.timed_spawns = []

# ------------------------------------------------------------------ 1: the kill bug, and the eel's first phase
## Each night foe on the grid: a minnow falls to a basic attack and to a technique alone; the eel is struck down to
## its waking by each.
func _kill_each_foe() -> void:
	for how in ["basic", "technique"]:
		for def_id in ["hollow_minnow", EEL]:
			_to_the_night(how == "technique")
			check(room() == NIGHT and Game.room_rt.topdown != null and Game.room_rt.event.get("active", false),
				"the night falls on the grid, its event under way (%s, %s)" % [room(), str(Game.room_rt.event.get("id", ""))])
			_alone()
			var grid: TopdownRoom = Game.room_rt.topdown
			place(TopdownRoom.cell_point([30, 33]))
			var e: EnemyState
			if def_id == "hollow_minnow":
				e = Game.enemies.spawn_at(def_id, grid.nearest_standable(st.plane + Vector2(40, 0)), 1)
				_minnow_in_reach(e, how)
				var killed := _strike_until_down(e, how, 150.0)
				check(killed, "%s: the Hollow Minnow falls to the player's %s on the grid (HP %d/%d)" % [how, "basic attack" if how == "basic" else "technique alone",
					int(e.pools.hp), int(e.pools.max_hp)])
			else:
				e = Game.enemies.spawn_at(def_id, TopdownRoom.cell_point([30, 36.5]), 2)
				_eel_in_the_river(e)
				# A technique alone waits out its cooldown between casts: the eel comes to it already hurt.
				if how == "technique": e.pools.hp = e.pools.max_hp * 0.86
				var woke := _strike_until_down(e, how, 150.0)
				check(woke, "%s: the player's %s drives the Hollowed Eel to its waking at four fifths of its HP (HP %d/%d, phase %d)" % [how,
					"basic attack" if how == "basic" else "technique alone", int(e.pools.hp), int(e.pools.max_hp), int(e.ai.get("phase", -1))])

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
	Game.combat.player_hits_enemy(c(), Game.combat.player_view(c()), e, {"damage_type": "physical", "element": "none", "mult": [1.0, 1.0], "range": [1.0, 1.0]}, 1)
	check(lock == null and e.invulnerable and not TopdownAim.compatible(e.altitude + e.hover - st.altitude) and e.pools.hp == hp,
		"the eel gliding in the river is out of every blow's band and the soft lock, and unhurt there (feet %.0f, lock %s, HP %d -> %d)"
		% [e.altitude + e.hover - st.altitude, str(lock.def_id if lock else "none"), int(hp), int(e.pools.hp)])

## Strike `e` until it falls (a minnow) or wakes (the eel), as a player who reads the eel's tell: out of its line when
## it rears, beside it while it lies ashore (the eel's window), on the bank above it while it glides; a minnow is met
## where it is. `how`: the basic attack only, or the technique only. True when it fell to the player (a minnow), or
## woke by the player's blows at 80% of its HP, not on its clock (the eel).
func _strike_until_down(e: EnemyState, how: String, limit_s: float) -> bool:
	var down := {"by": "", "woke": false, "at": 1.0}
	var heard := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("victim", "")) == str(e.uid): down.by = str(p.get("killer", ""))
		if n == "boss_phase" and str(p.get("action", "")) == "awaken" and int(p.get("enemy", 0)) == e.uid:
			down.woke = true
			down.at = e.pools.hp / e.pools.max_hp
	GameEvents.event.connect(heard)
	var t := 0.0
	var dodged := Vector2.INF
	var shore := {"lock": false, "band": false}
	var eel := e.def_id == EEL
	while e.alive and not (eel and down.woke) and t < limit_s and not Game.combat.is_wounded(c().id):
		var s := str(e.ai.get("state", ""))
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
	if eel:
		check(shore.lock and shore.band, "ashore after its lunge the eel is open: inside the blow's band, not invulnerable, and a tap's soft lock finds it (%s)" % str(shore))
	if verbose: print("  %s by %s: %s after %.1f s, HP %d/%d" % [e.def_id, how, "down" if not e.alive else ("woke" if down.woke else "standing"), t, int(c().pools.hp), int(c().pools.max_hp)])
	if eel: return bool(down.woke) and float(down.at) <= 0.8 + 0.01 and float(down.at) >= 0.5 and t < float(e.def.phases[0].after_s)
	return down.by == str(c().id)

# ------------------------------------------------------------------ 2: it cannot be won, and it cannot kill
## Awake, the eel's hide holds whatever strikes it; its blows pass a guard and a parry; none takes the player under the
## floor, and the one that reaches it ends the fight: the player overwhelmed, held down, the eel looming. With no scene
## on the stage (the director stood down here) the elders slay it in the simulation.
func _cannot_be_won() -> void:
	_to_the_night()
	_alone()
	var ch = c()
	tick_watch = Callable()   # no scene plays in this part
	place(TopdownRoom.cell_point([30, 32]))
	var e: EnemyState = Game.enemies.spawn_at(EEL, TopdownRoom.cell_point([30, 36.5]), 2)
	var aw: Dictionary = e.def.eel.awake
	var heard := {"overwhelmed": 0, "parried": 0, "killer": "", "glances": 0}
	var hook := func(n: String, p: Dictionary):
		if n == "boss_overwhelmed": heard.overwhelmed = int(heard.overwhelmed) + 1
		if n == "parried": heard.parried = int(heard.parried) + 1
		if n == "actor_defeated" and int(str(p.get("victim", "0"))) == e.uid: heard.killer = str(p.get("killer", ""))
		if n == "hit_landed" and str(p.get("target", "")) == str(e.uid) and p.get("glance", false): heard.glances = int(heard.glances) + 1
	GameEvents.event.connect(hook)
	step(0.5)   # its first sight of the player
	e.pools.hp = e.pools.max_hp * 0.79
	var t := 0.0
	while str(e.ai.get("state", "")) != "glide" and t < 5.0:
		step(0.1)
		t += 0.1
	check(e.ai.get("awake_begun", false) and ch.quests.has_flag("eel_awakened") and Game.room_rt.living_enemies().all(func(x): return x.def_id == EEL),
		"at 79%% of its HP the eel wakes (its flag kept), the river cleared of every minnow (%s, %.1f s)" % [str(e.ai.state), t])
	var floor_hp: float = e.pools.max_hp * float(aw.hp_floor)
	Game.combat.damage_enemy(e, 1.0e9, ch.id, "physical", "none", true, {"source": ""})
	var after_blow := e.pools.hp
	Game.combat.damage_enemy(e, e.pools.max_hp, ch.id, "dot", "burn", false, {})
	Game.combat.apply_slay("", "nobody")
	GameEvents.flush()
	check(e.alive and after_blow >= floor_hp - 0.5 and e.pools.hp >= floor_hp - 0.5 and int(heard.glances) >= 2,
		"awake, its hide holds: a blow of a billion and a burn leave it at its floor, alive (%d / %d HP, floor %d; %d told as glancing)" % [int(after_blow), int(e.pools.max_hp), int(floor_hp), int(heard.glances)])
	# A technique of any size, as the combat resolves one, glances off too (the eel ashore, open to blows).
	var tech := {"damage_type": "qi", "element": "water", "mult": [1.0e6, 1.0e6], "range": [1.0, 1.0], "source": "tech:flowing_palm"}
	e.invulnerable = false
	Game.combat.player_hits_enemy(ch, Game.combat.player_view(ch), e, tech, 1)
	check(e.alive and e.pools.hp >= floor_hp - 0.5, "a technique a million times over leaves it at its floor too (%d HP)" % int(e.pools.hp))
	# Its surge passes a guard begun in the parry window, and takes its share of the player's HP whatever they wear.
	var surge: Dictionary = e.def.attacks[1]
	var tl: Dictionary = Game.combat.timeline(ch.id)
	ch.pools.hp = ch.pools.max_hp
	ch.pools.invulnerable = 0.0
	ch.pools.statuses.clear()
	tl.guard = true
	tl.guard_t = 0.0
	var hp0: float = ch.pools.hp
	var pv := Game.combat.player_view(ch)
	Game.combat.enemy_hits_player(e, ch, Game.combat.enemy_view(e), pv, surge)
	tl.guard = false
	var took: float = hp0 - ch.pools.hp
	check(surge.get("unblockable", false) and int(heard.parried) == 0 and absf(took - ch.pools.max_hp * float(surge.hp_share)) < 1.0,
		"its surge passes a guard in the parry window and takes its share of the player's HP (%d of %d, %d%%)" % [int(took), int(ch.pools.max_hp), int(round(100.0 * took / ch.pools.max_hp))])
	# No blow takes the player under the floor: a blow of a billion leaves them at it, standing, and ends the fight.
	Game.combat.damage_player(ch, 1.0e9, str(e.uid), "physical", {}, false, e)
	var at_floor: float = ch.pools.hp / ch.pools.max_hp
	step(0.2)
	check(not Game.combat.is_wounded(ch.id) and absf(at_floor - float(aw.overwhelm_hp)) < 0.01,
		"no blow takes the player under %d%% of their HP while it is awake: a blow of a billion leaves them there, standing (%d%%)" % [int(100.0 * float(aw.overwhelm_hp)), int(round(100.0 * at_floor))])
	check(int(heard.overwhelmed) == 1 and str(e.ai.state) == "looming" and ch.quests.has_flag("eel_overwhelmed") and Game.combat.is_stunned(ch.id),
		"the blow that reaches the floor ends the fight: the player overwhelmed and held down, the eel looming over them (%s, %d)" % [str(e.ai.state), int(heard.overwhelmed)])
	# No scene here: the elders slay it in the simulation after rescue_s.
	t = 0.0
	while e.alive and t < float(aw.rescue_s) + 2.0:
		step(0.5)
		t += 0.5
	check(not e.alive and str(heard.killer) == "elders" and not Game.combat.is_stunned(ch.id),
		"with no scene on the stage the elders slay it in the simulation after %.0f s, and the player gets up (%s after %.1f s)" % [float(aw.rescue_s), str(heard.killer), t])
	GameEvents.event.disconnect(hook)
	step(0.5)
	tick_watch = func():
		scene_director.advance(0.05)
		settle_scenes()

# ------------------------------------------------------------------ 3: the night played through
func _the_night_played() -> void:
	_to_the_night()
	var ch = c()
	var t0 := Game.sim_time
	var p0 := play_s
	var taels0: int = Game.economy.balance("silver_tael", ch)
	var hp_low := {"v": 1.0, "fell": false, "phase2": 1.0, "eel2": 1.0, "in_scene": "", "teas": -1, "used": 0}
	beats.clear()
	var log_beat := func(n: String, p: Dictionary):
		var what := ""
		match n:
			"actor_defeated":
				if str(p.get("def", "")) == EEL:
					what = "eel down by " + ("player" if str(p.get("killer", "")) == str(ch.id) else str(p.get("killer", "")))
					hp_low.in_scene = str(scene_director.run.id) if scene_director.run != null else ""
				elif str(p.get("def", "")) == "hollow_minnow" and not beats.any(func(b): return str(b[1]) == "first minnow"): what = "first minnow"
			"flag_set": if str(p.get("flag", "")) in ["dou_safe", "granny_safe", "ma_safe", "night_survived"]: what = str(p.flag)
			"enemy_aggro": if str(p.get("def", "")) == EEL and not beats.any(func(b): return str(b[1]) == "eel rises"): what = "eel rises"
			"boss_phase":
				if str(p.get("action", "")) == "awaken":
					what = "eel wakes"
					hp_low.teas = ch.inventory.count("herbal_tea") + ch.inventory.count("healing_pill")
			"item_used":
				var e2 := _night_foe(EEL)
				if e2 != null and e2.ai.get("awake_begun", false): hp_low.used = int(hp_low.used) + 1
			"boss_overwhelmed": what = "overwhelmed"
			"room_event_completed": what = "night won (%s)" % str(p.get("reason", ""))
			"scene_ended": what = "scene " + str(p.get("scene", ""))
			"room_entered": what = "room " + str(p.get("room", ""))
			"system_unlocked": if str(p.get("system", "")) in ["cultivate", "cultivation"]: what = "unlock " + str(p.system)
			"player_gravely_wounded": hp_low.fell = true
		if what != "": beats.append([Game.sim_time - t0, what])
	GameEvents.event.connect(log_beat)
	var watch := func():
		scene_director.advance(0.05)
		settle_scenes()
		if room() == NIGHT:
			hp_low.v = minf(float(hp_low.v), c().pools.hp / c().pools.max_hp)
			var e := _night_foe(EEL)
			if e != null and e.ai.get("awake_begun", false):
				hp_low.phase2 = minf(float(hp_low.phase2), c().pools.hp / c().pools.max_hp)
				hp_low.eel2 = minf(float(hp_low.eel2), e.pools.hp / e.pools.max_hp)
	tick_watch = watch
	settle_scenes()
	step_night()
	GameEvents.event.disconnect(log_beat)
	var took := play_s - p0
	var order: Array = beats.map(func(b): return str(b[1]))
	print("the night (%.0f s on the play clock, %.0f s of the simulation): %s" % [took, Game.sim_time - t0, ", ".join(beats.map(func(b): return "%d s %s" % [int(b[0]), b[1]]))])
	# The play clock (prologue_run.play_s): the simulated seconds, the walking between the spots stood at, the lines read
	# and the cuts watched; a floor for a focused player, as the first hour's pacing reads it.
	check(took >= 150.0 and took <= 330.0, "the Hollow Night lasts three to five minutes on the play clock (%.0f s)" % took)
	var want := ["first minnow", "eel rises", "eel wakes", "scene eel_awakens", "overwhelmed", "eel down by elders", "night won ()", "scene elders_come",
		"scene grey_lifts", "night_survived", "room lf_lu_boat", "unlock cultivation"]
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
	var scenes := ["hollow_rises", "night_ma_goes", "night_granny_goes", "night_dou_runs", "grey_spreads", "eel_rises", "eel_awakens", "elders_come", "grey_lifts"]
	var missed := scenes.filter(func(s): return not played.get(s, false))
	check(missed.is_empty(), "every staged scene of the night played to its end (missed %s)" % str(missed))
	check(str(hp_low.in_scene) == "elders_come", "the eel dies in the elders' scene, by its checkpoint (%s)" % str(hp_low.in_scene))
	var arts: Array = scene_director.logged.filter(func(l): return str(l.scene) == "elders_come" and str(l.do) in ["art", "hitstop", "shake", "sound", "say", "spawn"])
	check(arts.filter(func(l): return str(l.do) == "art").size() == 3 and arts.filter(func(l): return str(l.do) == "hitstop").size() >= 3,
		"the rescue stages three elders' arts with their hit-stops, shakes, sounds and lines (%d steps)" % arts.size())
	check(float(hp_low.eel2) >= float(ContentDB.entry("enemies", EEL).eel.awake.hp_floor) - 0.005 and float(hp_low.phase2) >= float(ContentDB.entry("enemies", EEL).eel.awake.overwhelm_hp) - 0.005,
		"awake it cannot be won and cannot kill: its HP never under %d%% (%d%%), the player's never under %d%% (%d%%)" % [int(100.0 * float(ContentDB.entry("enemies", EEL).eel.awake.hp_floor)),
		int(100.0 * float(hp_low.eel2)), int(100.0 * float(ContentDB.entry("enemies", EEL).eel.awake.overwhelm_hp)), int(100.0 * float(hp_low.phase2))])
	check(not hp_low.fell and float(hp_low.v) >= 0.25, "a careful new player comes through it without a fall, HP never under a quarter (%d%%)" % int(100.0 * float(hp_low.v)))
	var teas_now: int = ch.inventory.count("herbal_tea") + ch.inventory.count("healing_pill")
	check(int(hp_low.teas) >= 0 and teas_now >= int(hp_low.teas),
		"nothing is lost to the fight that cannot be won: what was drunk against the awakened eel is given back (%d used; %d at its waking, %d after)" % [int(hp_low.used), int(hp_low.teas), teas_now])
	check(ch.inventory.count("hollow_eel_fang") == 1 and ch.inventory.count("pearl") >= 1, "the eel's first defeat leaves its fang (a rare find) and a river pearl, whoever slew it (fang %d, pearl %d)"
		% [ch.inventory.count("hollow_eel_fang"), ch.inventory.count("pearl")])
	check(ch.cultivator.titles.has("ferry_guardian"), "the night held earns the title Guardian of Lotus Ferry")
	check(Game.economy.balance("silver_tael", ch) > taels0, "the eel's hoard pays in taels (%d -> %d)" % [taels0, Game.economy.balance("silver_tael", ch)])
	check(ch.inventory.count("tiny_hollow_shard") >= 1, "the minnows leave grey slivers behind (%d Tiny Hollow Shards)" % ch.inventory.count("tiny_hollow_shard"))
	check(room() == "lf_lu_boat" and ch.quests.is_done("the_hollow_night") and ch.quests.is_active("the_river_token"), "on to Lu's boat: The River Token under way (%s)" % room())
	# Cultivation opens after the night, in the story's order: its unlocks and the Cultivation page's tutorial queued.
	check(Unlocks.is_unlocked(ch.id, "cultivate") and Unlocks.is_unlocked(ch.id, "cultivation") and Game.is_revealed("hud:cultivate")
		and order.find("unlock cultivation") > order.find("night_survived"),
		"cultivation opens after the night: Cultivate and the Cultivation page unlocked once night_survived is set")
	var tut: Dictionary = Game.tutorials.state(ch)
	check((tut.queue as Array).has("cultivation") or (tut.seen as Dictionary).has("cultivation") or (tut.guided as Dictionary).has("cultivation"),
		"the Cultivation page's unlock tutorial is due (%s)" % str(tut.queue))
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

# ------------------------------------------------------------------ 4: no soft-lock
## The villagers sent in, the player keeps to the lamplight at Aunt Ping's door and never strikes the eel: it wakes on
## its clock, the river rises over the bank at the end of its awake time, and the elders come all the same.
func _flees_to_the_lamplight() -> void:
	_to_the_night()
	var ch = c()
	for npc in ["old_ma", "granny_liu", "little_dou"]: talk_choose(npc, "effects")
	var refuge := obj_at("hut_refuge")
	place(refuge + Vector2(0, 24))
	var how := {"reason": "-", "eel": false, "killer": "", "woke_at": -1.0, "fell": false}
	var heard := func(n: String, p: Dictionary):
		if n == "room_event_completed": how.reason = str(p.get("reason", ""))
		if n == "enemy_spawned" and str(p.get("def", "")) == EEL: how.eel = true
		if n == "actor_defeated" and str(p.get("def", "")) == EEL: how.killer = str(p.get("killer", ""))
		if n == "boss_phase" and str(p.get("action", "")) == "awaken":
			var e := _night_foe(EEL)
			how.woke_at = e.pools.hp / e.pools.max_hp if e != null else -1.0
		if n == "player_gravely_wounded": how.fell = true
	GameEvents.event.connect(heard)
	var t := 0.0
	while room() == NIGHT and t < 300.0:
		# Back to the lamplight whenever a blow has knocked the player off it.
		if not Game.combat.is_stunned(ch.id) and st.plane.distance_to(refuge) > 40.0: place(refuge + Vector2(0, 24))
		step(0.5)
		t += 0.5
	GameEvents.event.disconnect(heard)
	check(how.eel and float(how.woke_at) > 0.99 and str(how.killer) == "elders" and str(how.reason) == "" and not how.fell,
		"one who keeps to the lamplight and never strikes it: the eel still wakes (at %d%% of its HP, on its clock), has them down, and the elders slay it (%s)"
		% [int(100.0 * float(how.woke_at)), str(how)])
	check(room() == "lf_lu_boat" and ch.quests.is_done("the_hollow_night") and ch.quests.has_flag("night_survived"), "and the night goes on to Lu's boat (%s after %.0f s)" % [room(), t])

## A fall in the eel's first phase wakes the player at Aunt Ping's door, in the night, and the night begins again; it
## ends in the rescue and the boat all the same.
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
	place(at)
	_villagers_in()
	var eel := _await_eel()
	var r := fight_eel(240.0) if eel != null else {}
	var w := 0.0
	while room() == NIGHT and w < 60.0:
		step(0.5)
		w += 0.5
	check(eel != null and str(r.get("slain_by", "")) == "elders" and room() == "lf_lu_boat", "after the fall the night still ends in the elders' rescue and Lu's boat (%s, %s)" % [str(r), room()])

# ------------------------------------------------------------------ 5: a reload mid-fight
## Save, and come back from the save: the director too (as the game does on a restart).
func _reload() -> void:
	Game.pause(false)
	Game.save_all()
	if is_instance_valid(scene_director): scene_director.free()
	Game.boot()
	Game.autosave_enabled = false
	var ok: bool = Game.submit({"type": "enter_character", "slot": 1}).get("ok", false) and Game.submit({"type": "enter_world"}).get("ok", false)
	check(ok, "the character comes back from its save")
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	_new_director()
	tick_watch = func():
		scene_director.advance(0.05)
		settle_scenes()

## To the eel's waking, the villagers in, with its scene played: the eel awake and gliding again.
func _to_the_waking() -> EnemyState:
	_to_the_night()
	_villagers_in()
	place(TopdownRoom.cell_point([30, 32]))
	var e := _await_eel()
	if e == null: return null
	step(0.5)
	e.pools.hp = e.pools.max_hp * 0.79
	var t := 0.0
	while not (e.ai.get("awake_begun", false) and str(e.ai.get("state", "")) == "glide") and t < 20.0:
		step(0.1)
		t += 0.1
	return e

## The waking is the fight's own moment: its cut takes the stage from a villager's run still playing live, at once.
func _the_waking_takes_the_stage() -> void:
	_to_the_night()
	tick_watch = Callable()   # the stage driven by hand here
	_alone()
	_villagers_in()
	var t := 0.0
	while t < 5.0 and not (scene_director.run != null and bool(scene_director.run.row.get("live", false))):
		scene_director.advance(0.05)
		step(0.05)
		t += 0.05
	var live_one := str(scene_director.run.id) if scene_director.run != null else ""
	place(TopdownRoom.cell_point([30, 32]))
	var e: EnemyState = Game.enemies.spawn_at(EEL, TopdownRoom.cell_point([30, 36.5]), 2)
	step(0.3)
	e.pools.hp = e.pools.max_hp * 0.79
	step(0.1)
	var waited := 0.0
	while waited < 1.0 and not (scene_director.run != null and str(scene_director.run.id) == "eel_awakens"):
		scene_director.advance(0.05)
		waited += 0.05
	check(live_one != "" and scene_director.run != null and str(scene_director.run.id) == "eel_awakens",
		"the waking's cut takes the stage from %s still playing live, in %.2f s" % [live_one, waited])
	settle_scenes()
	tick_watch = func():
		scene_director.advance(0.05)
		settle_scenes()

## Reloaded in the eel's second phase: it rises again at once, awake, with no minnows, and the elders still come.
func _reload_awake() -> void:
	var e := _to_the_waking()
	check(e != null and c().quests.has_flag("eel_awakened"), "the eel woken before the reload")
	_reload()
	var minnows := Game.room_rt.living_enemies().filter(func(x): return x.def_id == "hollow_minnow").size()
	var t := 0.0
	var eel: EnemyState = null
	while t < 8.0:
		eel = _night_foe(EEL)
		if eel != null and eel.ai.get("awake_begun", false): break
		step(0.25)
		t += 0.25
	check(room() == NIGHT and minnows == 0 and eel != null and eel.ai.get("awake_begun", false),
		"after a reload in its second phase the eel rises again at once, awake (%.1f s), with no minnows (%d)" % [t, minnows])
	var r := fight_eel(120.0)
	var w := 0.0
	while room() == NIGHT and w < 60.0:
		step(0.5)
		w += 0.5
	check(str(r.get("slain_by", "")) == "elders" and room() == "lf_lu_boat" and c().quests.has_flag("night_survived"),
		"and it still has the player down, the elders slay it, and the night goes on to Lu's boat (%s, %s)" % [str(r.get("slain_by", "")), room()])

## Reloaded in the rescue, cut short before its checkpoint: not taken up at the reload; it plays again whole when the
## eel has the player down again, and slays it.
func _reload_in_the_rescue() -> void:
	var e := _to_the_waking()
	check(e != null, "the eel woken before the rescue")
	var ch = c()
	Game.combat.damage_player(ch, 1.0e9, str(e.uid) if e != null else "", "physical", {}, false, e)
	# The stage driven by hand here, so the rescue can be caught part-way (settle_scenes would play it to its end).
	tick_watch = Callable()
	var t := 0.0
	while t < 20.0 and not (scene_director.run != null and str(scene_director.run.id) == "elders_come" and int(scene_director.run.i) >= 12):
		scene_director.advance(0.05)
		if not scene_director.in_cut(): step(0.05)
		t += 0.05
	var mid: bool = scene_director.run != null and str(scene_director.run.id) == "elders_come" and e != null and e.alive
	check(mid, "the rescue begun, the eel still alive at its step %s" % str(scene_director.run.i if scene_director.run else -1))
	_reload()
	scene_director.poll()
	check(scene_director.run == null or str(scene_director.run.id) != "elders_come", "a rescue cut short is not taken up at the reload, with no eel there yet")
	var slain := {"by": "", "scene": ""}
	var hook := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("def", "")) == EEL:
			slain.by = str(p.get("killer", ""))
			slain.scene = str(scene_director.run.id) if scene_director.run != null else ""
	GameEvents.event.connect(hook)
	var r := fight_eel(120.0)
	var w := 0.0
	while room() == NIGHT and w < 60.0:
		step(0.5)
		w += 0.5
	GameEvents.event.disconnect(hook)
	check(str(slain.by) == "elders" and str(slain.scene) == "elders_come" and room() == "lf_lu_boat",
		"the eel has the player down again at once, the rescue plays whole and slays it, on to Lu's boat (%s in %s, %s; %s)" % [str(slain.by), str(slain.scene), room(), str(r)])

## Reloaded after the eel is slain, before the boat: the night comes back won, no eel, its last scene plays, on to the boat.
func _reload_after_the_kill() -> void:
	var e := _to_the_waking()
	var ch = c()
	Game.combat.damage_player(ch, 1.0e9, str(e.uid) if e != null else "", "physical", {}, false, e)
	tick_watch = Callable()
	var t := 0.0
	while t < 90.0 and not (ch.quests.has_flag("night_held") and scene_director.run != null and str(scene_director.run.id) == "grey_lifts"):
		scene_director.advance(0.05)
		if not scene_director.in_cut(): step(0.05)
		t += 0.05
	check(ch.quests.has_flag("night_held") and scene_director.run != null and str(scene_director.run.id) == "grey_lifts", "the eel slain and the grey lifting before the reload")
	_reload()
	check(room() == NIGHT and not Game.room_rt.event.get("active", false) and _night_foe(EEL) == null and Game.room_rt.living_enemies().is_empty(),
		"after a reload the night comes back won: no eel, no minnows (%s)" % str(Game.room_rt.event.get("active", false)))
	var w := 0.0
	while room() == NIGHT and w < 60.0:
		step(0.5)
		w += 0.5
	check(room() == "lf_lu_boat" and c().quests.has_flag("night_survived") and c().quests.scenes.get("grey_lifts", {}).get("done", false),
		"its last scene plays and the night goes on to Lu's boat (%s)" % room())
