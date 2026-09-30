extends Node
## Balance simulator (S38, Part 7): a rate-based bot plays the data to the end of Act I
## and reports hours to each realm. Each Level it spends an active minute as
## data/balance.json says (fighting at the right Level, meditating at the best spot it
## has reached, the rest travelling and crafting), hands in the quests pitched at that
## Level and one daily mission per hour. Realm progress uses the real rules: kill QP and
## gap factors, the meditation rate of a real character with that realm's method (with
## decision 45's early current), body-stage training, and each quest's fixed cultivation
## at its own tier (decision 45: quests.json `tier` and `cultivation`). It fails when a
## realm lands more than ±15% off the Part 4 pacing table.
## Run headless:  godot --headless --path . res://tests/balance_sim.tscn

var checks := 0
var failures := 0

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var cfg := ContentDB.config("balance")
	check(not cfg.is_empty(), "balance.json is present")
	var c = _character()
	check(c != null, "a character to simulate")
	if c == null: return _finish()
	var quest_levels := _quest_levels()
	var hours := {}              # realm key -> hours when it is reached
	var t := float(cfg.get("prologue_hours", 0.5)) * 60.0   # active minutes
	var end_key := str(cfg.get("act_end", "heaven_glimpse_3"))
	var sim_end := str(cfg.get("sim_end", end_key))
	var key := "bone_forging_1"
	while key != "":
		hours[key] = t / 60.0
		var r := ContentDB.realm(key)
		var lv := int(r.get("level", 0))
		var need := float(r.get("accumulate_needed", 100))
		var income := _income(c, cfg, key, lv)
		# Quests pitched inside this stage pay their fixed cultivation on hand-in (decision 45).
		# Optional side quests are detours: they also cost active time the mixed session does not cover.
		var lump := 0.0
		var detour := 0.0
		for n in int(r.get("levels", 1)):
			for row in quest_levels.get(lv + n, []):
				lump += float(row[1])
				detour += float(cfg.get("quest_minutes", {}).get(str(row[0]), 0.0))
		var base_min := need / income
		# Daily missions: the fixed cultivation of a mission posted at this Level, `dailies_per_hour` of them an hour.
		var daily := float(ProgressionRules.quest_cultivation("daily", lv)) * float(cfg.get("dailies_per_hour", 1.0)) / 60.0
		# At least a fifth of every stage is gathered by play, however many quests land in it.
		var minutes := maxf(0.2 * base_min, (need - lump) / (income + daily))
		t += minutes + detour
		if key == end_key: hours["act_end"] = t / 60.0
		if key == sim_end: break
		key = str(r.get("next", ""))
	var tol := float(cfg.get("tolerance", 0.15))
	print("realm                  sim h   target h   ratio")
	var targets: Array = cfg.get("pacing", []).duplicate()
	targets.append(["act_end", float(cfg.get("act_end_hours", 65))])
	for row in targets:
		var k := str(row[0])
		var want := float(row[1])
		var got := float(hours.get(k, -1.0))
		var ratio := got / want if want > 0.0 else 0.0
		print("%-22s %6.1f   %8.1f   %5.2f" % [k, got, want, ratio])
		if k == "bone_forging_1": continue   # set by the Prologue, not by rates
		check(got > 0.0 and absf(ratio - 1.0) <= tol, "%s reached at %.1f h (target %.1f h ±%d%%)" % [k, got, want, int(tol * 100.0)])
	_currency(cfg)
	_drops(cfg)
	_posts()
	_account_month()
	_par_checks(c, cfg, hours)
	_story_fight_bands(hours)
	_story_rooms_agree(hours)
	_story_duels(c)
	_starter_checks(c, cfg)
	_technique_checks(c, cfg)
	_codex_seals(c)
	_finish()

# ------------------------------------------------------------------ story fights against the par character
## Research player_motivation P1: every fight the story asks for in the first 5 hours (a kill step of a prologue, main
## or guided quest offered at a realm the sim reaches by then) is against foes whose Levels sit in the full-credit band
## of the kill gap (stats.json kill_gap_factor: -4 to +4 of the character) around the par character at that step: the
## Level of the realm the quest is offered at, followed back through what it waits on. The foes are the kill step's
## spawns in its room (the step's own, else the quest's target room, else every room that spawns them).
func _story_fight_bands(hours: Dictionary) -> void:
	var gap: Array = ContentDB.stat_const("kill_gap_factor", [])
	var hi_d := int(gap[0].min_diff) - 1
	var lo_d := int(gap[1].min_diff)
	var max_h := 5.0
	var memo := {}
	var bad: Array = []
	var seen := 0
	for q in ContentDB.all("quests"):
		if not str(q.get("kind", "")) in ["prologue", "main", "guided"]: continue
		var rk := _offer_realm(q, memo, 0)
		if rk != "mortal" and (not hours.has(rk) or float(hours[rk]) > max_h): continue
		var lv := int(ContentDB.realm(rk).get("level", 0))
		for o in q.get("objectives", []):
			if str(o.get("kind", "")) != "kill" or str(o.get("enemy", "any")) == "any": continue
			var rooms: Array = [str(o.room)] if o.has("room") else []
			if rooms.is_empty() and _spawn_levels(str(q.get("target_room", "")), str(o.enemy)).size() > 0: rooms = [str(q.target_room)]
			if rooms.is_empty(): rooms = ContentDB.rooms.keys().filter(func(r): return _spawn_levels(str(r), str(o.enemy)).size() > 0)
			for r in rooms:
				for band in _spawn_levels(str(r), str(o.enemy)):
					seen += 1
					if int(band[0]) < lv + lo_d or int(band[1]) > lv + hi_d:
						var p := StatRules.par(lv)
						bad.append("%s: %s Lv %d-%d in %s at %s (Level %d; par attack %d, HP %d)" % [q.id, o.enemy, int(band[0]), int(band[1]), r, rk, lv,
							int(p.get("attack", 0)), int(p.get("max_hp", 0))])
	print("story fights in the first %.0f h: %d spawn bands checked against the par Level" % [max_h, seen])
	check(seen >= 8 and bad.is_empty(), "every story fight of the first %.0f hours is within %d..%+d Levels of the par character at its step (%s)" % [max_h, lo_d, hi_d, "; ".join(bad)])

## The prototype's polish: the field a story quest sends the player into (its target, a room on the height grid) is not
## over the Level the story brings them there at (the realm the quest is offered at): its band starts at that Level or
## under, and tops out no more than two over. The Marsh Edge's reed frogs were Level 4-6 when Strange Tracks sends a Bone
## Forging 3 (Level 3) disciple there; its band is 3-5 now, and The Humming Token's grey boarlets there are Level 3-4
## (the earlier fix's 4-5 took two charging together to a tenth of the player's HP; _story_fight_bands holds either way).
func _story_rooms_agree(hours: Dictionary) -> void:
	var memo := {}
	var off: Array = []
	var seen := 0
	for q in ContentDB.all("quests"):
		if not str(q.get("kind", "")) in ["prologue", "main", "guided"]: continue
		var rid := str(q.get("target_room", ""))
		var room := ContentDB.room(rid)
		if rid == "" or str(room.get("type", "")) != "field" or not TopdownRoom.has_layout(rid): continue
		var rk := _offer_realm(q, memo, 0)
		if rk != "mortal" and (not hours.has(rk) or float(hours[rk]) > 5.0): continue
		var lv := maxi(1, int(ContentDB.realm(rk).get("level", 0)))
		var lr: Array = room.get("level_range", [0, 0])
		seen += 1
		if int(lr[0]) > lv or int(lr[-1]) > lv + 2: off.append("%s sends Level %d (%s) to %s, Levels %d-%d" % [q.id, lv, rk, rid, int(lr[0]), int(lr[-1])])
	check(seen >= 5 and off.is_empty(), "story rooms: no field the story sends the player into is over the Level the story brings them there at (%d quests; %s)" % [seen, "; ".join(off)])

# ------------------------------------------------------------------ the story's fights, won at the story's Level
## The prototype's polish (docs/redesign/prototype_qa.md): a new player following the story is not downed again and
## again. Each fight the prototype's story asks for is fought through the real Combat, on the room's own height grid,
## by a character at the Level the story brings them there, in the gear it has handed them by then (the starting kit,
## Crab Trouble's hat, the first crab's short blade; at the Marsh Edge the Weapon Hall's jian and its art), on fixed
## seeds. `trade`: standing and trading blows, never stepping out of a wind-up (a new player's thumb); `careful`: a
## step aside at every wind-up (what the lessons teach). A tea is drunk at a third of HP when `teas` allows.
##   - The herd's elite boarlet (The Willow Path, Level 1): won trading blows with the short blade, HP to spare; with
##     Guo's gauntlets alone, won by a careful player with the story's teas. It downed the QA player one to four times.
##   - The Entry Trial's puppet (Level 2): won trading blows (it guards from the front and is open while it strikes).
##   - Shen Lian's spar (Level 2): won trading blows. He spars at the player's Level (a Level-4 double beat the QA's
##     Level-2 player).
##   - The Marsh Edge (Level 3): its reed frogs and leeches at the top of their band and The Humming Token's grey
##     boarlets, each won trading blows with HP to spare; its elite frog (on the lookout, optional) by a careful player.
## Then the kill steps in their rooms as they stand, the room's other foes joining as its rules have them (_room_fight):
## the Willow Path's five boarlets and The Humming Token's five grey boarlets, won every time, HP never under 40%.
const DUEL_SEEDS := [11, 22, 33, 44]
const TAP_S := 0.35      ## a thumb's tap on Attack (or a technique), about three a second
const WALK_UPS := 150.0  ## the body's walk on the grid, units a second (movement.json topdown.walk)
func _story_duels(c) -> void:
	var was_view: String = c.view
	c.view = "topdown"
	Game.autosave_enabled = false
	if not Game.in_world: Game.submit({"type": "enter_world"})
	Unlocks.grant_prologue(c.id)
	Unlocks.force_unlock(c.id, "technique_slots_2")
	var boar := _spawn_level("wp_west", "wild_boarlet", true)
	var cases := [
		["the herd's elite boarlet, the short blade, trading blows", 1, "training_short_blade", "common", "wp_west", "wild_boarlet", boar, true, "trade", 3, 4, 0.4],
		["the herd's elite boarlet, Guo's gauntlets alone, careful", 1, "training_gauntlets", "flawed", "wp_west", "wild_boarlet", boar, true, "careful", 3, 3, 0.0],
		["the Entry Trial's puppet, the short blade, trading blows", 2, "training_short_blade", "common", "sf_trial_jade", "trial_puppet", _spawn_level("sf_trial_jade", "trial_puppet", false), false, "trade", 3, 4, 0.3],
		["Shen Lian's spar, trading blows", 2, "training_short_blade", "common", "sf_fairground", "shen_lian", -1, false, "trade", 0, 4, 0.4],
		["a Marsh Edge reed frog, trading blows", 3, "training_jian", "common", "rm_marsh_edge", "reed_frog", _spawn_level("rm_marsh_edge", "reed_frog", false), false, "trade", 0, 4, 0.5],
		["a Marsh Edge leech, trading blows", 3, "training_jian", "common", "rm_marsh_edge", "marsh_leech", _spawn_level("rm_marsh_edge", "marsh_leech", false), false, "trade", 0, 4, 0.5],
		["a grey boarlet of The Humming Token, trading blows", 3, "training_jian", "common", "rm_marsh_edge", "hollowed_boarlet", _spawn_level("rm_marsh_edge", "hollowed_boarlet", false), false, "trade", 0, 4, 0.5],
		["the Marsh Edge's elite frog, careful", 3, "training_jian", "common", "rm_marsh_edge", "reed_frog", _spawn_level("rm_marsh_edge", "reed_frog", true), true, "careful", 3, 4, 0.2]]
	for k in cases:
		var won := 0
		var lowest := 1.0
		for seed in DUEL_SEEDS:
			_story_character(c, int(k[1]), str(k[2]), str(k[3]), int(k[9]))
			var r := _duel(c, str(k[4]), str(k[5]), int(k[6]), bool(k[7]), str(k[8]), seed)
			if r.won: won += 1
			lowest = minf(lowest, float(r.low))
		print("story duel: %s (Level %d against Level %d): won %d of %d, lowest HP %d%%" % [k[0], int(k[1]), int(k[6]), won, DUEL_SEEDS.size(), int(100.0 * lowest)])
		check(won >= int(k[10]) and (won < DUEL_SEEDS.size() or lowest >= float(k[11])),
			"story duel: %s at the story's Level %d against Level %d is won %d of %d times (at least %d), HP never under %d%% (%d%%)" % [k[0], int(k[1]), int(k[6]), won,
			DUEL_SEEDS.size(), int(k[10]), int(100.0 * float(k[11])), int(100.0 * lowest)])
	# The kill steps in their rooms as they stand, the room's other foes about: the Willow Path's herd (Level 1) and The
	# Humming Token's grey boarlets among the marsh's frogs and leeches (Level 3), each with three teas. At Level 4-5 the
	# grey boarlets, two charging together, took the player to 9% of its HP (and the QA player fell there): 3-4 now.
	var steps := [["the Willow Path's five boarlets and then its elite", 1, "training_short_blade", "wp_west", "wild_boarlet", 5, "the_willow_path", true],
		["The Humming Token's five grey boarlets", 3, "training_jian", "rm_marsh_edge", "hollowed_boarlet", 5, "the_humming_token", false]]
	for k in steps:
		var won := 0
		var lowest := 1.0
		for seed in DUEL_SEEDS:
			_story_character(c, int(k[1]), str(k[2]), "common", 3)
			var r := _room_fight(c, str(k[3]), str(k[4]), int(k[5]), str(k[6]), seed, bool(k[7]))
			if r.won: won += 1
			lowest = minf(lowest, float(r.low))
		print("story room fight: %s at Level %d: won %d of %d, lowest HP %d%%" % [k[0], int(k[1]), won, DUEL_SEEDS.size(), int(100.0 * lowest)])
		check(won == DUEL_SEEDS.size() and lowest >= 0.4, "story room fight: %s at the story's Level %d, the room's other foes about, won every time with HP never under 40%% (%d of %d; lowest HP %d%%)" % [k[0],
			int(k[1]), won, DUEL_SEEDS.size(), int(100.0 * lowest)])
	# Decision 42: the Hollow Night, the tutorial's first real danger, played whole in its room at the story's Level (a
	# Mortal, Level 0, before Flowing Palm): the minnows about the villagers, the three sent in, the lane's schools, then
	# the Hollowed eel until it falls. `careful`: out of the eel's line when it rears (what Aunt Ping and the scenes
	# teach), with the first crab's short blade or Guo's gauntlets alone; `trade`: a thumb that never steps aside, with
	# the short blade. Each with the story's three teas; the eel must fall to the player every time, HP to spare.
	var nights := [["the Hollow Night, the short blade, careful", "training_short_blade", "common", "careful", 0.5],
		["the Hollow Night, Guo's gauntlets alone, careful", "training_gauntlets", "flawed", "careful", 0.1],
		["the Hollow Night, the short blade, trading blows", "training_short_blade", "common", "trade", 0.35]]
	for k in nights:
		var won := 0
		var lowest := 1.0
		var longest := 0.0
		for seed in DUEL_SEEDS:
			_story_character(c, 0, str(k[1]), str(k[2]), 3, false)
			var r := _night_fight(c, seed, str(k[3]))
			if r.won: won += 1
			lowest = minf(lowest, float(r.low))
			longest = maxf(longest, float(r.t))
		print("story night: %s (Level 0): won %d of %d, lowest HP %d%%, the longest night %.0f s" % [k[0], won, DUEL_SEEDS.size(), int(100.0 * lowest), longest])
		check(won == DUEL_SEEDS.size() and lowest >= float(k[4]), "story night: %s at the story's Level 0, won every time (the eel falls to the player) with HP never under %d%% (%d of %d; lowest HP %d%%)"
			% [k[0], int(100.0 * float(k[4])), won, DUEL_SEEDS.size(), int(100.0 * lowest)])
	c.view = was_view

## The Hollow Night whole on `seed` (world.py lf_village_night, its event): the villagers nearest first, each one's
## minnows fought and the villager sent in (their flag, as the talk sets it), then whatever is in the fight nearest,
## the eel as `mode` has it (EnemyAuthority._eel: `careful` steps out of its line while it rears, `trade` never does),
## at a thumb's pace, walking the grid, a tea at a third of HP, until the night is won or the player falls:
## {won: the eel fell to the player, low, t: the night's seconds}.
func _night_fight(c, seed: int, mode: String) -> Dictionary:
	Rng.forget(c.id)
	Rng.ensure(c.id, seed)
	Game.enemies.rng.seed = seed
	for f in ["night_survived", "dou_safe", "granny_safe", "ma_safe", "grey_spread", "lu_on_the_bank"]: c.quests.flags.erase(f)
	c.quests.flags["night_active"] = true
	Game.world.load_room(c, "lf_village_night", "")
	GameEvents.flush()
	var grid: TopdownRoom = Game.room_rt.topdown
	var st := ActorState.new()
	Game.bind_movement(c.id, st)
	st.plane = grid.nearest_standable(Vector2(float(c.position.x), float(c.position.y)))
	st.altitude = grid.floor_at(st.plane)
	var tally := {"eel": false, "done": false}
	var hook := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("def", "")) == "hollowed_eel" and str(p.get("killer", "")) == str(c.id): tally.eel = true
		if n == "room_event_completed" and str(p.get("event", "")) == "hollow_night": tally.done = true
	GameEvents.event.connect(hook)
	var walk_to := func(goal: Vector2) -> void:
		var path: Array = grid.find_path(TopdownRoom.cell_of(st.plane), TopdownRoom.cell_of(goal), true)
		var to: Vector2 = TopdownRoom.cell_point([path[1].x, path[1].y]) if path.size() > 2 else goal
		var v: Vector2 = to - st.plane
		st.plane = grid.nearest_standable(st.plane + v.normalized() * minf(v.length(), WALK_UPS * TAP_S))
		st.altitude = grid.floor_at(st.plane)
	var low := 1.0
	var t := 0.0
	var dodged := Vector2.INF
	var villagers := [["old_ma", "ma_safe"], ["granny_liu", "granny_safe"], ["little_dou", "dou_safe"]]
	while t < 300.0 and not tally.done:
		GameEvents.flush()
		low = minf(low, c.pools.hp / c.pools.max_hp)
		if Game.combat.is_wounded(c.id): break
		var eel: EnemyState = null
		var near: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.team != "enemy": continue
			if e.def_id == "hollowed_eel": eel = e
			elif e.in_fight() and e.plane.distance_to(st.plane) < 200.0 and (near == null or e.plane.distance_to(st.plane) < near.plane.distance_to(st.plane)): near = e
		var todo: Array = villagers.filter(func(v): return not c.quests.has_flag(str(v[1])))
		var step_s := TAP_S
		if eel != null and mode == "careful" and str(eel.ai.state) == "windup" and eel.ai.get("land", Vector2.INF) != dodged:
			# Out of its line, at a walk: the step across its aim a thumb makes in the tell.
			var land: Vector2 = eel.ai.land
			st.plane = grid.nearest_standable(land + Vector2(-eel.aim.y, eel.aim.x) * 72.0)
			st.altitude = grid.floor_at(st.plane)
			dodged = land
			step_s = 0.45
		elif near != null or (eel != null and str(eel.ai.state) in ["attack", "beached"]):
			var tgt: EnemyState = eel if near == null else near
			var gap: Vector2 = tgt.plane - st.plane
			if gap.length() > 40.0: walk_to.call(tgt.plane)
			else:
				var aim: Vector2 = gap.normalized() if gap.length() > 0.5 else Vector2.RIGHT
				Game.submit({"type": "basic_attack", "facing": 1 if gap.x >= 0.0 else -1, "aim": aim})
		elif not todo.is_empty():
			var o: Dictionary = {}
			for ob in Game.room_rt.def.get("objects", []): if str(ob.get("npc", "")) == str(todo[0][0]) and str(ob.get("type", "")) == "npc": o = ob
			var at := Vector2(float(o.at[0]), float(o.at[1]))
			if st.plane.distance_to(at) > 48.0: walk_to.call(at)
			else: Game.quest.apply_flag(c.id, str(todo[0][1]))   # the talk: sent to Aunt Ping's door
		elif eel != null:
			# The bank above it, within its reach.
			var bank := grid.nearest_standable(eel.plane + Vector2(0, -96))
			if st.plane.distance_to(bank) > 24.0: walk_to.call(bank)
		if c.pools.hp < c.pools.max_hp * 0.35 and c.inventory.count("herbal_tea") > 0:
			Game.submit({"type": "use_item", "index": c.inventory.first_index("herbal_tea"), "confirm": true})
		var k := 0.0
		while k < step_s:
			Game.tick(0.05)
			k += 0.05
		t += step_s
	GameEvents.event.disconnect(hook)
	var out := {"won": bool(tally.eel), "low": low if bool(tally.eel) else 0.0, "t": t}
	if OS.get_cmdline_user_args().has("--duels"):
		print("  night %s seed %d: %s; me %d/%d, teas left %d" % [mode, seed, str(out), int(c.pools.hp), int(c.pools.max_hp), c.inventory.count("herbal_tea")])
	Game.room_rt.enemies.clear()
	return out

## The Level of a room's spawn of `enemy` (its elite, or the top of its band).
func _spawn_level(room: String, enemy: String, elite: bool) -> int:
	for sp in ContentDB.room(room).get("spawns", []):
		if str(sp.get("enemy", "")) == enemy and bool(sp.get("elite", false)) == elite and not sp.get("wild_pet", false):
			var l = sp.get("level", ContentDB.entry("enemies", enemy).get("level", [1, 1]))
			return int(l[-1]) if l is Array else int(l)
	return -1

## The sim's character as the story has it at Level `lv`: the realm's start, no meridians, Dao or tree yet, the starting
## kit with Crab Trouble's hat, `weapon` in hand, Flowing Palm slotted (`palm`; before the boat, as at the Hollow Night,
## none) and at Bone Forging 3 the Weapon Hall's art for the weapon, `teas` Herbal Teas in the Bag, whole.
func _story_character(c, lv: int, weapon: String, quality: String, teas: int, palm := true) -> void:
	var cu = c.cultivator
	cu.realm_key = ContentDB.realm_key_for_level(lv)
	cu.qp = 0.0
	cu.energy_type = str(ContentDB.realm(cu.realm_key).get("energy", "none"))
	cu.meridians = {}
	cu.daos = {}
	cu.tree = {"v": 1, "realised": {}, "resets": {}, "pity": {}}
	cu.body_level = 0
	c.set_meta("extra_modifiers", [])
	for slot in c.inventory.equipped.keys(): c.inventory.equipped[slot] = null
	for id in AccountAuthority.STARTING_KIT + ["plain_straw_hat"]:
		c.inventory.equipped[str(ContentDB.item(id).slot)] = LootRules.make_instance(id, int(ContentDB.item(id).get("ilv", 1)), "common", null, c.inventory.take_uid())
	c.inventory.equipped["weapon"] = LootRules.make_instance(weapon, 1 if quality == "flawed" else int(ContentDB.item(weapon).get("ilv", 1)), quality, null, c.inventory.take_uid())
	var arts := ["flowing_palm"] if palm else []
	if not palm: cu.techniques_known.erase("flowing_palm")
	if lv >= 3:
		var fam := str(ContentDB.item(weapon).get("family", "fists"))
		for q in ContentDB.all("quests"):
			if str(q.id) != "the_weapon_hall": continue
			for e in q.get("rewards", []):
				if str(e.get("kind", "")) == "learn_technique_for_weapon": arts.append(str(e.options.get(fam, "")))
	for t in arts:
		if t != "": Game.progression.apply_learn_technique(c.id, t)
	for i in cu.technique_slots.size(): cu.technique_slots[i] = arts[i] if i < arts.size() and str(arts[i]) != "" else null
	for i in c.inventory.bag.size():
		if c.inventory.bag[i] != null and str(c.inventory.bag[i].id) == "herbal_tea": c.inventory.bag[i] = null
	if teas > 0: Game.inventory.apply_add(c.id, "herbal_tea", teas, "balance_sim")
	# Whole, and fresh: no fall, injury, status or cooldown carried over from the fight before.
	Game.combat.wounded.erase(c.id)
	Game.combat.spar.erase(c.id)
	cu.injuries = {}
	c.pools.statuses.clear()
	c.pools.cooldowns.clear()
	c.pools.alive = true
	StatRules.rebuild(c)
	c.pools.hp = c.pools.max_hp

## A kill step in its room as the room stands (every spawn there, the step's own waiting on its quest, joining the fight
## as the room's rules have them), on `seed`: from the first spawn of `enemy`, the nearest foe at the player first, else
## the next of `enemy`, trading blows at a thumb's pace (walking the grid's paths), a tea at a third of HP, until
## `count` of `enemy` are down (and then, `then_elite`, the room's elite of it: The Willow Path's last step) or the
## player falls: {won, low, t}.
func _room_fight(c, room: String, enemy: String, count: int, quest: String, seed: int, then_elite := false) -> Dictionary:
	var had: bool = c.quests.active.has(quest)
	if not had:
		var progress: Array = []
		for o in ContentDB.entry("quests", quest).get("objectives", []): progress.append(0)
		c.quests.active[quest] = {"state": "active", "progress": progress, "accepted_tick": 0}
	Rng.forget(c.id)
	Rng.ensure(c.id, seed)
	Game.enemies.rng.seed = seed
	# Each seed is a fresh visit: the room forgets the kills of the seed before (the elite slain there would stay away
	# for its respawn, and the step would wait on it).
	if c.rooms.has(room): c.rooms[room].erase("slain")
	Game.world.load_room(c, room, "")
	GameEvents.flush()
	var grid: TopdownRoom = Game.room_rt.topdown
	var st := ActorState.new()
	Game.bind_movement(c.id, st)
	var start := Vector2.ZERO
	for sl in Game.room_rt.spawn_slots:
		if str(sl.spec.get("enemy", "")) == enemy and not sl.spec.get("elite", false) and start == Vector2.ZERO: start = sl.point
	st.plane = grid.nearest_standable(start - Vector2(0, 64))
	st.altitude = grid.floor_at(st.plane)
	st.velocity = Vector2.ZERO
	var tally := {"kills": 0, "elite": false, "hurt": {}}
	var hook := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("def", "")) == enemy:
			if bool(p.get("elite", false)): tally.elite = true
			else: tally.kills = int(tally.kills) + 1
		if n == "hit_landed" and str(p.get("target_kind", "")) == "player" and str(p.get("attacker", "")).is_valid_int():
			var att = Game.room_rt.enemies.get(int(str(p.attacker)))
			var key := "%s Lv %d" % [att.def_id, att.level] if att != null else "?"
			tally.hurt[key] = int(tally.hurt.get(key, 0)) + int(p.get("amount", 0))
	GameEvents.event.connect(hook)
	var low := 1.0
	var out := {"won": false, "low": 0.0, "t": 0.0}
	var t := 0.0
	while t < 300.0:
		GameEvents.flush()
		low = minf(low, c.pools.hp / c.pools.max_hp)
		if Game.combat.is_wounded(c.id):
			out = {"won": false, "low": 0.0, "t": t}
			break
		var herd_done := int(tally.kills) >= count
		if herd_done and (not then_elite or bool(tally.elite)):
			out = {"won": true, "low": low, "t": t}
			break
		var target: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.team != "enemy" or not e.in_fight() or e.plane.distance_to(st.plane) > 200.0: continue
			if target == null or e.plane.distance_to(st.plane) < target.plane.distance_to(st.plane): target = e
		if target == null:
			for e in Game.room_rt.living_enemies():
				if e.team != "enemy" or e.def_id != enemy or (then_elite and e.elite != herd_done): continue
				if target == null or e.plane.distance_to(st.plane) < target.plane.distance_to(st.plane): target = e
		if target != null:
			var gap: Vector2 = target.plane - st.plane
			if gap.length() > 40.0:
				# The grid's own paths (the marsh's boardwalks over its channels), a tap's walk along them.
				var path: Array = grid.find_path(TopdownRoom.cell_of(st.plane), TopdownRoom.cell_of(target.plane), true)
				var goal: Vector2 = TopdownRoom.cell_point([path[0].x, path[0].y]) if path.size() > 1 else target.plane
				var step_v: Vector2 = goal - st.plane
				st.plane = grid.nearest_standable(st.plane + step_v.normalized() * minf(step_v.length(), WALK_UPS * TAP_S))
				st.altitude = grid.floor_at(st.plane)
			else:
				var aim: Vector2 = gap.normalized() if gap.length() > 0.5 else Vector2.RIGHT
				var facing := 1 if gap.x >= 0.0 else -1
				for i in ProgressionRules.technique_slot_count(c):
					if c.cultivator.technique_slots[i] != null and Game.submit({"type": "use_technique", "slot": i, "facing": facing, "aim": aim}).get("ok", false): break
				Game.submit({"type": "basic_attack", "facing": facing, "aim": aim})
				if c.pools.hp < c.pools.max_hp * 0.35 and c.inventory.count("herbal_tea") > 0:
					Game.submit({"type": "use_item", "index": c.inventory.first_index("herbal_tea"), "confirm": true})
		var k := 0.0
		while k < TAP_S:
			Game.tick(0.05)
			k += 0.05
		t += TAP_S
	GameEvents.event.disconnect(hook)
	if OS.get_cmdline_user_args().has("--duels"):
		print("  room fight %s in %s seed %d: %s after %.1f s, %d down (the elite %s); me %d/%d, teas left %d; hurt by %s" % [enemy, room, seed, str(out), t,
			int(tally.kills), str(tally.elite), int(c.pools.hp), int(c.pools.max_hp), c.inventory.count("herbal_tea"), str(tally.hurt)])
	if not had: c.quests.active.erase(quest)
	Game.room_rt.enemies.clear()
	return out

## One fight in `room` against `enemy` at Level `lv` (a spar opponent through the spar's own start), on `seed`:
## {won, low: the lowest HP share it came to}.
func _duel(c, room: String, enemy: String, lv: int, elite: bool, mode: String, seed: int) -> Dictionary:
	Game.world.load_room(c, room, "")
	GameEvents.flush()
	var grid: TopdownRoom = Game.room_rt.topdown
	var home := Vector2.ZERO
	for sl in Game.room_rt.spawn_slots:
		if str(sl.spec.get("enemy", "")) == enemy and bool(sl.spec.get("elite", false)) == elite: home = sl.point
	Game.room_rt.spawn_slots.clear()
	Game.room_rt.enemies.clear()
	Rng.forget(c.id)
	Rng.ensure(c.id, seed)
	Game.enemies.rng.seed = seed
	var st := ActorState.new()
	Game.bind_movement(c.id, st)
	var put := func(p: Vector2, alt: float) -> void:
		st.plane = grid.nearest_standable(p) if grid != null else p
		st.altitude = grid.floor_at(st.plane) if grid != null else alt
		st.surface = null
		st.velocity = Vector2.ZERO
	if home == Vector2.ZERO:
		var npc: Dictionary = {}
		for o in Game.room_rt.def.get("objects", []): if str(o.get("npc", "")) == enemy: npc = o
		home = Vector2(float(npc.at[0]), float(npc.at[1])) if not npc.is_empty() else Vector2(float(Game.room_rt.def.get("spawn_point", [600, 800])[0]), 600.0)
	put.call(home - Vector2(110, 0), 0.0)
	var spar := {"winner": ""}
	var hook := func(n: String, p: Dictionary): if n == "spar_ended": spar.winner = str(p.get("winner", ""))
	GameEvents.event.connect(hook)
	var e: EnemyState = null
	if ContentDB.entry("enemies", enemy).get("spar", false):
		Game.quest.start_spar(c, enemy, lv, enemy)
		for x in Game.room_rt.living_enemies(): e = x
	else:
		var at: Vector2 = grid.place_near(home, st.altitude) if grid != null else home
		e = Game.enemies.spawn_at(enemy, at, lv, {"elite": elite})
	GameEvents.flush()
	e.ai.state = "aggro"
	var low := 1.0
	var out := {"won": false, "low": 0.0}
	var t := 0.0
	while t < 150.0:
		GameEvents.flush()
		low = minf(low, c.pools.hp / c.pools.max_hp)
		if spar.winner != "":
			out = {"won": spar.winner == "player", "low": low}
			break
		if Game.combat.is_wounded(c.id):
			out = {"won": false, "low": 0.0}
			break
		if not e.alive:
			out = {"won": true, "low": low}
			break
		# A thumb's pace: the body walks (WALK_UPS), a tap every TAP_S, a tea at a third of HP when there is one.
		var step_s := TAP_S
		var gap: Vector2 = e.plane - st.plane
		if mode == "careful" and str(e.ai.get("state", "")) == "windup":
			# A step out of the lane of the wind-up, as the lessons teach, at walking pace.
			var lane: Vector2 = e.aim if e.aim.length() > 0.1 else -gap.normalized()
			var side := Vector2(-lane.y, lane.x)
			if side.dot(st.plane - e.plane) < 0.0: side = -side
			put.call(st.plane + side * WALK_UPS * 0.45, st.altitude)
			step_s = 0.45
		elif gap.length() > 40.0:
			put.call(st.plane + gap.normalized() * minf(gap.length() - 30.0, WALK_UPS * TAP_S), st.altitude)
		else:
			var aim: Vector2 = gap.normalized() if gap.length() > 0.5 else Vector2.RIGHT
			var facing := 1 if gap.x >= 0.0 else -1
			for i in ProgressionRules.technique_slot_count(c):
				if c.cultivator.technique_slots[i] != null and Game.submit({"type": "use_technique", "slot": i, "facing": facing, "aim": aim}).get("ok", false): break
			Game.submit({"type": "basic_attack", "facing": facing, "aim": aim})
			if c.pools.hp < c.pools.max_hp * 0.35 and c.inventory.count("herbal_tea") > 0:
				Game.submit({"type": "use_item", "index": c.inventory.first_index("herbal_tea"), "confirm": true})
		var k := 0.0
		while k < step_s:
			Game.tick(0.05)
			k += 0.05
		t += step_s
	GameEvents.event.disconnect(hook)
	if OS.get_cmdline_user_args().has("--duels"):
		print("  duel %s Lv %d seed %d: %s after %.1f s; me %d/%d atk %.1f wounded %s; foe %s hp %d/%d at %s me at %s" % [enemy, lv, seed, str(out), t, int(c.pools.hp),
			int(c.pools.max_hp), c.stats.value("physical_attack"), Game.combat.is_wounded(c.id), e.def_id, int(e.pools.hp), int(e.pools.max_hp), str(e.plane), str(st.plane)])
	Game.room_rt.enemies.clear()
	return out

## The realm a story quest is offered at: the highest realm among its requirements, its unlock's trigger and those of
## every quest it waits on (and the quest whose `next` it is), all the way back.
func _offer_realm(q: Dictionary, memo: Dictionary, depth: int) -> String:
	var id := str(q.id)
	if memo.has(id): return str(memo[id])
	var best := "mortal"
	if depth > 30: return best
	var conds: Array = q.get("requires", {}).get("all", []).duplicate()
	for u in ContentDB.all("unlocks"):
		if str(u.get("quest", "")) == id: conds.append_array(u.get("trigger", {}).get("all", []))
	var before: Array = []
	for k in conds:
		match str(k.get("kind", "")):
			"realm_at_least": if ContentDB.realm_position(str(k.realm)) > ContentDB.realm_position(best): best = str(k.realm)
			"quest_done", "quest_accepted", "quest_active": before.append(str(k.quest))
	for p in ContentDB.all("quests"):
		if str(p.get("next", "")) == id: before.append(str(p.id))
	for b in before:
		var r := _offer_realm(ContentDB.entry("quests", b), memo, depth + 1) if ContentDB.has_entry("quests", b) else "mortal"
		if ContentDB.realm_position(r) > ContentDB.realm_position(best): best = r
	memo[id] = best
	return best

## The Level bands [lo, hi] of a room's spawns of `enemy` (a wild pet to tame aside).
func _spawn_levels(room: String, enemy: String) -> Array:
	var out: Array = []
	for sp in ContentDB.room(room).get("spawns", []):
		if str(sp.get("enemy", "")) == enemy and not sp.get("wild_pet", false):
			var l = sp.get("level", [1, 1])
			out.append([int(l[0]), int(l[-1])] if l is Array else [int(l), int(l)])
	return out

# ------------------------------------------------------------------ P12 the par character (research §6.1, §6.7)
## The par character (StatRules.par) built with the real rules at Level `lv` on the sim's character: its realm, the
## meridians spread over the five channels, the Sword Dao, a jian and four armour pieces `weapon_lag` Levels behind at
## par quality and enhancement (the weapon with its attack affix), and the sets' damage% and the crit affixes as
## modifiers of their own. The same schedule the par table was built from (stats.json `par`).
func _par_character(c, lv: int) -> void:
	var cu = c.cultivator
	cu.realm_key = ContentDB.realm_key_for_level(lv)
	var r := ContentDB.realm(cu.realm_key)
	cu.qp = cu.need() * (float(lv - int(r.level)) + 0.5) / maxf(1.0, float(r.get("levels", 1)))
	cu.energy_type = str(r.get("energy", "none"))
	cu.purity = int(ContentDB.stat_const("par.purity", 9))
	cu.method_id = ""
	cu.body_level = 0
	cu.aptitude = {}   # a neutral root and physique
	var chans: Array = ContentDB.stat_const("par.channels", [])
	var pts := 0
	for l in range(1, lv + 1): pts += ProgressionRules.meridian_points_for_level(l)
	cu.meridians = {}
	for i in chans.size(): cu.meridians[str(chans[i])] = pts / chans.size() + (1 if i < pts % chans.size() else 0)
	cu.daos = {"sword": {"insight": 0.0, "tier": int(StatRules.par_step("dao", lv))}}
	cu.tree = {"v": 1, "realised": _par_route(lv), "resets": {}, "pity": {}}   # P13a: its Realisations along its route
	var ilv := maxi(1, lv - int(ContentDB.stat_const("par.weapon_lag", 3)))
	var quality := str(StatRules.par_step("quality", lv))
	var enhance := mini(int(ContentDB.stat_const("par.enhance_max", 10)), lv / int(ContentDB.stat_const("par.enhance_every", 12)))
	for slot in c.inventory.equipped.keys(): c.inventory.equipped[slot] = null
	for slot in ["weapon", "robe", "trousers", "boots", "hat"]:
		var base := _par_base(slot, ilv)
		if base == "": continue
		var inst := {"id": base, "uid": 900000 + lv * 10 + c.inventory.equipped.size(), "count": 1, "ilv": ilv, "quality": quality, "enhance": enhance}
		if slot == "weapon": inst["affixes"] = [{"id": "attack_pct", "stat": "physical_attack", "op": "pct_add", "value": float(StatRules.par_step("attack_pct", lv))}]
		c.inventory.equipped[slot] = inst
	var crit: Array = StatRules.par_step("crit", lv)
	c.set_meta("extra_modifiers", [{"stat": "damage_pct", "op": "flat", "value": float(StatRules.par_step("damage_pct", lv)), "source": "par:sets"},
		{"stat": "crit_chance", "op": "flat", "value": float(crit[0]), "source": "par:crit"},
		{"stat": "crit_damage", "op": "flat", "value": float(crit[1]), "source": "par:crit"}])
	StatRules.rebuild(c)

## Starter gear (grades.json drop.starter): no weapon of the first rooms is a power spike. At each Level of their foes,
## the par character holding Fists First's gauntlets, the first weapon (its affix rolled, the best of 60) or the best
## starter weapon a foe of that Level drops has a sheet attack within par_tolerance of the par character's own.
func _starter_checks(c, cfg: Dictionary) -> void:
	var tol := float(cfg.get("par_tolerance", [0.15, 0.20])[0])
	var st: Dictionary = LootRules.drop_cfg().get("starter", {})
	var gift: Dictionary = (ContentDB.entry("quests", "fists_first").get("rewards", []) as Array).filter(func(e): return str(e.get("kind", "")) == "grant_equipment")[0]
	var rng := RandomNumberGenerator.new()
	for lv in [1, 2, 3]:
		_par_character(c, lv)
		var par_atk: float = c.stats.value("physical_attack")
		var held := {"gauntlets": LootRules.make_instance(str(gift.item), int(gift.ilv), str(gift.quality), null, 1)}
		for i in 60:
			rng.seed = 100 + i
			held["first %d" % i] = LootRules.make_drop(rng, {"level": lv, "min_quality": str(st.first_quality), "starter": true, "family": str(st.first_family), "first": true}, 0.0, true, 2)
			for fam in st.get("families", []):
				held["%s %d" % [fam, i]] = LootRules.make_drop(rng, {"level": lv, "min_quality": "superior", "starter": true, "family": str(fam)}, 0.0, true, 3)
		var top := 0.0
		var top_of := ""
		for k in held:
			c.inventory.equipped["weapon"] = held[k]
			StatRules.rebuild(c)
			if c.stats.value("physical_attack") > top:
				top = c.stats.value("physical_attack")
				top_of = "%s (%s %s)" % [k, held[k].id, held[k].quality]
		print("starter Level %d: par attack %.1f, best starter weapon %.1f, %s" % [lv, par_atk, top, top_of])
		check(top <= par_atk * (1.0 + tol), "starter gear: at Level %d the best first-room weapon's attack %.1f is within %d%% of par's %.1f (%s)" % [lv, top, int(tol * 100), par_atk, top_of])

## Decision 27 (research §6.4: no bucket fed from outside its table): every Codex seal's gift together stays inside
## the budget account_rules.json sets for each stat, gives no offence stat, and moves the par character's Combat
## Power at Levels 30, 99 and 165 by no more than `par_cp_max`, all through the real stat rules.
func _codex_seals(c) -> void:
	var rules: Dictionary = ContentDB.config("account_rules").get("collection_seals", {})
	var budget: Dictionary = rules.get("budget", {})
	var group := {}
	for s in ContentDB.stat_const("stats", []): group[str(s.id)] = str(s.get("group", ""))
	var sums := {}
	var all := AccountState.new()
	for page in rules.get("pages", {}):
		for seal in rules.pages[page]:
			all.collection_seals["%s:%d" % [page, int(seal.seal)]] = true
			for m in seal.get("modifiers", []): sums[str(m.stat)] = float(sums.get(str(m.stat), 0.0)) + float(m.value)
	for stat in sums:
		check(budget.has(stat) and float(sums[stat]) <= float(budget.get(stat, 0.0)) + 0.0001 and str(group.get(stat, "")) != "offense",
			"codex seals: %s +%.0f%% over the book (budget %.0f%%, group %s)" % [stat, 100.0 * float(sums[stat]), 100.0 * float(budget.get(stat, 0.0)), str(group.get(stat, "?"))])
	for lv in [30, 99, 165]:
		_par_character(c, lv)
		var cp0 := float(StatRules.combat_power(c))
		StatRules.rebuild(c, all)
		var gain := float(StatRules.combat_power(c)) / maxf(1.0, cp0) - 1.0
		print("codex seals: Level %d par Combat Power %d, with every seal %+.2f%%" % [lv, int(cp0), 100.0 * gain])
		check(gain >= 0.0 and gain <= float(rules.get("par_cp_max", 0.03)), "codex seals: every seal claimed moves Level %d par Combat Power by %.2f%% (at most %.0f%%)" % [lv, 100.0 * gain, 100.0 * float(rules.get("par_cp_max", 0.03))])

## The banded base of a slot (the jian for the weapon) with the highest item Level at or under `ilv`, else the lowest.
func _par_base(slot: String, ilv: int) -> String:
	var best := ""
	var best_lv := -1
	var low := ""
	var low_lv := 9999
	for a in ContentDB.all("artifacts"):
		if str(a.get("slot", "")) != slot or not LootRules.is_banded(a): continue
		if slot == "weapon" and str(a.get("family", "")) != str(ContentDB.stat_const("par.family", "jian")): continue
		var al := int(a.get("ilv", 1))
		if al <= ilv and al > best_lv:
			best = str(a.id)
			best_lv = al
		if al < low_lv:
			low = str(a.id)
			low_lv = al
	return best if best != "" else low

## Average blows of the par character against a normal foe of its own Level (never missing, crits out unless `crits`):
## the basic combo's mean stroke and the par main art.
func _par_hits(c, lv: int, crits := false) -> Dictionary:
	var pv := CombatRules.fighter(c)
	if not crits: pv.crit_chance = -10.0
	var foe := CombatRules.foe(StatRules.mob_stats({"role": "normal"}, lv), lv, "wood")   # a foe whose element neither resists nor is struck by the blow
	var fam := StatRules.family(c)
	var combo := 0.0
	for st in fam.get("combo", []): combo += float(st.get("mult", 1.0)) / float((fam.combo as Array).size())
	var art := float(StatRules.par_step("art", lv))
	var dao := ProgressionRules.effective_dao_tier(c, str(fam.get("dao", "")))
	var basic := {"damage_type": "physical", "element": "none", "mult": [combo, combo], "range": fam.get("range", [0.9, 1.1]), "dao_tier": dao, "never_miss": true}
	var tech := {"damage_type": str(ContentDB.stat_const("par.art_type", "qi")), "element": "none", "mult": [art, art], "range": fam.get("range", [0.9, 1.1]),
		"dao_tier": dao, "mastery_tier": int(StatRules.par_step("mastery", lv)) - 1, "never_miss": true,
		"tree_pct": float(TechniqueTreeRules.passives(c, {"element": "none", "family": str(ContentDB.stat_const("par.family", "jian"))}).damage)}
	var rng := RandomNumberGenerator.new()
	rng.seed = 4242 + lv
	var out := {"basic": 0.0, "technique": 0.0}
	for i in 800:
		out.basic += float(CombatRules.resolve(pv, foe, basic, rng).amount) / 800.0
		out.technique += float(CombatRules.resolve(pv, foe, tech, rng).amount) / 800.0
	return out

func _par_checks(c, cfg: Dictionary, hours: Dictionary) -> void:
	var targets: Dictionary = cfg.get("par_targets", {})
	var tol: Array = cfg.get("par_tolerance", [0.15, 0.20])
	check(not targets.is_empty() and not StatRules.par(99).is_empty(), "the par table and its targets are present")
	print("par   Level   basic (target)        technique (target)    crit tech   max HP    table basic")
	for key in targets:
		var lv := int(key)
		_par_character(c, lv)
		var h := _par_hits(c, lv)
		var want: Array = targets[key]
		var row := StatRules.par(lv)
		print("par   %5d %9d (%9d) %11d (%10d) %11d %9d %9d" % [lv, int(h.basic), int(want[0]), int(h.technique), int(want[1]),
			int(h.technique * c.stats.value("crit_damage")), int(c.stats.value("max_hp")), int(row.get("basic", 0))])
		# 1 par_hit: the real rules against the research's targets, and against the table the monsters are set from.
		check(absf(h.basic / float(want[0]) - 1.0) <= float(tol[0]), "par_hit: Level %d basic %d against %d (±%d%%)" % [lv, int(h.basic), int(want[0]), int(float(tol[0]) * 100)])
		check(absf(h.technique / float(want[1]) - 1.0) <= float(tol[1]), "par_hit: Level %d technique %d against %d (±%d%%)" % [lv, int(h.technique), int(want[1]), int(float(tol[1]) * 100)])
		check(absf(h.basic / maxf(1.0, float(row.get("basic", 0))) - 1.0) <= 0.05, "par_hit: Level %d, the rules' basic %d and the par table's %d agree (±5%%)" % [lv, int(h.basic), int(row.get("basic", 0))])
		# 2 ttk: a normal foe of the Level falls to 3-4.5 par blows (under Level 20 the table keeps today's floor: at most
		# 5); an elite to 18-27.
		var foe := StatRules.mob_stats({"role": "normal"}, lv)
		var hits := float(foe.max_hp) / maxf(1.0, h.basic)
		var elite_hits := float(StatRules.mob_stats({"role": "normal"}, lv, true).max_hp) / maxf(1.0, h.basic)
		if lv >= 20: check(hits >= 3.0 and hits <= 4.5 and elite_hits >= 18.0 and elite_hits <= 27.0, "ttk: Level %d, a normal foe in %.1f par blows, an elite in %.1f" % [lv, hits, elite_hits])
		else: check(hits <= 5.0, "ttk: Level %d, a normal foe in %.1f par blows (today's floor below Level 20)" % [lv, hits])
		# 3 blow: a normal foe's plain blow takes 4-8% of par HP (6-10% under Level 20), a boss's 12-18% (two to three
		# normal blows, so 16-24% under Level 20).
		var normal_share := _blow_share(c, lv, "normal")
		var boss_share := _blow_share(c, lv, "dungeon_boss")
		var band: Array = [0.06, 0.10] if lv < 20 else [0.04, 0.08]
		var boss_band: Array = [0.16, 0.24] if lv < 20 else [0.12, 0.18]
		if lv >= int(ContentDB.stat_const("par.from_level", 10)):
			check(normal_share >= float(band[0]) and normal_share <= float(band[1]) and boss_share >= float(boss_band[0]) and boss_share <= float(boss_band[1]),
				"blow: Level %d, a normal foe's blow takes %.1f%% of par HP, a boss's %.1f%%" % [lv, 100.0 * normal_share, 100.0 * boss_share])
	# 4 boss_par: every boss with a par time has the par character's DPS times it.
	var bosses := 0
	for e in ContentDB.all("enemies"):
		if not e.has("par_s"): continue
		var blv := int((e.get("level", [1]) as Array)[0])
		var secs := float(StatRules.mob_stats(e, blv).max_hp) / maxf(1.0, float(StatRules.par(blv).dps))
		bosses += 1
		check(secs >= 0.8 * float(e.par_s) and secs <= 1.25 * float(e.par_s), "boss_par: %s falls in %.0f s of par DPS (par %d s)" % [e.id, secs, int(e.par_s)])
	check(bosses >= 12, "boss_par: the twelve bosses of the research carry a par time (%d)" % bosses)
	# 5 smooth and 6 realm_step, from the par table. Bone Forging keeps today's numbers and Qi Kindling 1 its first
	# x1.30 step, so the Level-by-Level rise is checked from Level 11.
	var majors := {}
	for r in ContentDB.all("realms"):
		if r.get("major", false): majors[int(r.level)] = str(r.realm)
	var rough: Array = []
	for lv in range(11, 201):
		var g := float(StatRules.par(lv).basic) / maxf(1.0, float(StatRules.par(lv - 1).basic))
		if g < 1.02 or g > (1.30 if majors.has(lv) else 1.25): rough.append("%d x%.3f" % [lv, g])
	check(rough.is_empty(), "smooth: the par basic hit rises 2-25%% a Level, under 30%% at a major (%s)" % ", ".join(rough))
	var steps: Array = []
	for lv in majors:
		if lv <= 10: continue
		var advanced := str(majors[lv]) in ["half_heaven_monarch", "dao_sigil", "heavens_threshold", "inner_heaven"]
		var a := float(StatRules.par(lv).attack) / float(StatRules.par(lv - 1).attack)
		var ok := (a >= 1.10 and a <= 1.30) if advanced else (a >= 1.15 and a <= 1.30)
		if not ok: steps.append("%d x%.3f" % [lv, a])
	var first := StatRules.might_at(10) / StatRules.might_at(9)
	check(steps.is_empty() and first >= 1.15 and first <= 1.30, "realm_step: each major raises par attack 15-30%% (the advanced states 10-30%%; Qi Kindling 1's Might x%.2f) %s" % [first, ", ".join(steps)])
	# 7 cp_rec: every room's recommended CP is within ±20% of par CP at its middle Level.
	var off: Array = []
	for rid in ContentDB.rooms:
		var room: Dictionary = ContentDB.rooms[rid]
		var lr: Array = room.get("level_range", [0, 0])
		if int(room.get("recommended_cp", 0)) <= 0: continue
		var par_cp := float(StatRules.par((int(lr[0]) + int(lr[lr.size() - 1])) / 2).cp)
		if absf(float(room.recommended_cp) / par_cp - 1.0) > 0.2: off.append(str(rid))
	check(off.is_empty(), "cp_rec: rooms' recommended CP follows the par CP (%s)" % ", ".join(off))
	# 8 digits: every par figure prints in five characters or fewer.
	var long: Array = []
	for lv in range(0, 201):
		var p := StatRules.par(lv)
		for k in ["attack", "max_hp", "basic", "technique", "technique_crit", "dps", "cp"]:
			if UiKit.short(float(p.get(k, 0))).length() > 5: long.append("%d %s %s" % [lv, k, UiKit.short(float(p.get(k, 0)))])
	check(long.is_empty(), "digits: every par figure prints in five characters or fewer (%s)" % ", ".join(long.slice(0, 5)))
	# 9 chapter_floor: each chapter's floor sits between 4 Levels under where the previous chapter ends (the floors it
	# asks and the breakthroughs its quests lead to) and one great realm past it.
	var floors: Dictionary = ContentDB.config("quests").get("chapter_floors", {})
	var ends := {}
	for q in ContentDB.all("quests"):
		if str(q.get("kind", "")) != "main": continue
		var at := 0
		for r in q.get("requires", {}).get("all", []):
			if str(r.get("kind", "")) == "realm_at_least": at = maxi(at, int(ContentDB.realm(str(r.realm)).get("level", 0)))
		for o in q.get("objectives", []):
			if str(o.get("kind", "")) == "reach_realm": at = maxi(at, int(ContentDB.realm(str(o.realm)).get("level", 0)))
		ends[str(q.get("chapter", ""))] = maxi(int(ends.get(str(q.get("chapter", "")), 0)), at)
	var gaps: Array = []
	var bad_floor: Array = []
	for ch in range(2, 23):
		var f := int(ContentDB.realm(str(floors.get(str(ch), "mortal"))).get("level", 0))
		var e := int(ends.get(str(ch - 1), 0))
		if f > e: gaps.append("%d:+%d" % [ch, f - e])
		if f < e - int(cfg.get("floor_below", 4)) or f > e + int(cfg.get("floor_wait", 9)): bad_floor.append(str(ch))
	print("chapter floors past the previous chapter's end (chapter:+Levels): ", ", ".join(gaps))
	check(floors.size() == 21 and bad_floor.is_empty(), "chapter_floor: every chapter opens within its bounds of where the last one ended (%s)" % ", ".join(bad_floor))
	# 10 pacing: hours to the end of Act III, against the research's two estimates until the user sets a target.
	var end_h := float(hours.get(str(cfg.get("sim_end", "")), -1.0))
	var pace: Array = cfg.get("pacing_band", [140, 235])
	print("pacing: Sphere Lord 3 at %.0f h (the research's estimates %d-%d h; the user sets the target)" % [end_h, int(pace[0]), int(pace[1])])
	check(end_h >= float(pace[0]) * 0.85 and end_h <= float(pace[1]) * 1.15, "pacing: Sphere Lord 3 in %.0f h" % end_h)

# ------------------------------------------------------------------ P13a techniques at scale (technique_plan §6)
## The par character's Realisations placed along its main family's route in the Formless tree (§6.2): a passage a ring
## up to the band's ring, and at each act's last ring its notable and its kin group's keystone (the keystones of Acts
## I-III so far). Set as the design stands, the later acts' rings as if built (stats.py's par table: TG.par_tree).
func _par_route(lv: int) -> Dictionary:
	var T = TechniqueTreeRules
	var fam := str(ContentDB.stat_const("par.family", "jian"))
	var out := {}
	for r in range(1, T.ring_at_level(lv) + 1):
		out[T.passage("formless", fam, r)] = true
		if T.is_edge(r):
			out[T.notable("formless", fam, T.act_of(r))] = true
			var ks: String = T.keystone_at("formless", T.kin_of(fam), T.act_of(r))
			if ks != "": out[ks] = true
	return out

## §6.1 the line a par character's main art meets (technique hit over basic hit, balance.json technique_line) and §6.2
## the trees' share: inside its cap at every Level, on techniques only, and a tree full of nodes adds no more.
func _technique_checks(c, cfg: Dictionary) -> void:
	var line: Dictionary = cfg.get("technique_line", {})
	var tol := float(cfg.get("technique_line_tolerance", 0.15))
	var T = TechniqueTreeRules
	var fam := str(ContentDB.stat_const("par.family", "jian"))
	check(line.size() >= 12, "the technique line is present (%d Levels)" % line.size())
	print("technique line   Level   art x   tree %   technique / basic   line   off")
	var off: Array = []
	for key in line:
		var lv := int(key)
		_par_character(c, lv)
		var h := _par_hits(c, lv)
		var ratio: float = h.technique / maxf(1.0, h.basic)
		var want := float(line[key])
		var tree := float(T.passives(c, {"element": "none", "family": fam}).damage)
		print("technique line %7d %7.3f %7.1f %12.2f %13.2f %+5.0f%%" % [lv, float(StatRules.par_step("art", lv)), tree * 100.0, ratio, want, (ratio / want - 1.0) * 100.0])
		if absf(ratio / want - 1.0) > tol: off.append("%d: %.2f against %.2f" % [lv, ratio, want])
		check(tree <= T.tree_cap(lv) + 0.0001, "tree: Level %d, the par route adds %.1f%%, inside the cap of %.1f%%" % [lv, tree * 100.0, T.tree_cap(lv) * 100.0])
	check(off.is_empty(), "technique_line: the par main art over the basic blow lands on the plan's line within ±%d%% (%s)" % [int(tol * 100), ", ".join(off)])
	# The trees feed techniques' damage bucket only, and a whole sector realised adds no more than the cap.
	for lv in [60, 99, 165]:
		_par_character(c, lv)
		var with_tree := _par_hits(c, lv)
		var cu = c.cultivator
		cu.tree.realised = {}
		var bare := _par_hits(c, lv)
		check(near_eq(with_tree.basic, bare.basic) and with_tree.technique > bare.technique, "tree: Level %d, the route raises the art (%d to %d), never the basic blow" % [lv, int(bare.technique), int(with_tree.technique)])
		for nid in T.nodes_of("formless"):
			var n := T.node(nid)
			if str(n.get("family", "")) == fam or str(n.get("kin", "")) == T.kin_of(fam): cu.tree.realised[nid] = true
		check(absf(float(T.passives(c, {"element": "none", "family": fam}).damage) - T.tree_cap(lv)) < 0.0001,
			"tree: Level %d, a whole sector realised adds its cap and no more (%.1f%%)" % [lv, T.tree_cap(lv) * 100.0])

func near_eq(a: float, b: float) -> bool:
	return absf(a - b) <= maxf(1.0, absf(b) * 0.0001)

## A same-Level foe's plain blow on the par character (averaged, crits in), as a share of its max HP.
func _blow_share(c, lv: int, role: String) -> float:
	var foe := CombatRules.foe(StatRules.mob_stats({"role": role}, lv), lv, "wood")
	var pv := CombatRules.fighter(c)
	var rng := RandomNumberGenerator.new()
	rng.seed = 777 + lv
	var sum := 0.0
	for i in 400: sum += float(CombatRules.resolve(foe, pv, {"damage_type": "physical", "element": "none", "mult": [1.0, 1.0], "never_miss": true}, rng).amount)
	return sum / 400.0 / maxf(1.0, c.stats.value("max_hp"))

## S39: a player can afford the next upgrade in their grade band after about 1–2 hours.
func _currency(cfg: Dictionary) -> void:
	for row in cfg.get("upgrades", []):
		var lv := int(row[0])
		var item := str(row[1])
		var rate := _taels_per_hour(cfg, lv)
		var price := LootRules.buy_price(item)
		var h := price / maxf(1.0, rate)
		print("Level %d: %d taels/h (spec about %d) · %s costs %d → %.1f h" % [lv, int(rate), int(row[2]), item, price, h])
		check(h >= float(cfg.get("afford_hours", [0.75, 2.5])[0]) and h <= float(cfg.get("afford_hours", [0.75, 2.5])[1]),
			"%s is affordable after %.1f h of play at Level %d" % [item, h, lv])

## Coins and loot sold at NPC prices from the monsters of this Level, plus daily mission pay.
func _taels_per_hour(cfg: Dictionary, lv: int) -> float:
	var rng := RandomNumberGenerator.new()
	rng.seed = 12345 + lv
	var foes: Array = ContentDB.all("enemies").filter(func(e):
		var r: Array = e.get("level", [0, 0])
		return str(e.get("role", "")) == "normal" and not e.get("passive", false) and lv >= int(r[0]) - 2 and lv <= int(r[r.size() - 1]) + 2)
	if foes.is_empty(): return 0.0
	var per_kill := 0.0
	var rolls := 200
	for e in foes:
		for i in rolls:
			var drop := LootRules.roll(str(e.get("loot", e.id)), rng, lv, 0.0, 0.0, {"no_equipment": true})
			per_kill += int(drop.coins)
			for it in drop.items: per_kill += LootRules.sell_price(str(it.item)) * int(it.count)
	per_kill /= float(rolls * foes.size())
	var kills_h := float(cfg.get("kills_per_min", 6)) * 60.0 * float(cfg.get("mix", {}).get("fight", 0.35))
	var dailies := float(cfg.get("dailies_per_hour", 1.0)) * (10 + lv * 3)
	return per_kill * kills_h + dailies

## P7b (item_plan §4.4): what an hour of hunting drops. Each hunting room of a field region is hunted
## `hours_per_region` hours at `kills_per_hour`: its elite slots `elite_kills_per_slot` kills an hour each, or fewer when
## one respawns slower (at most `elite_share_cap` of the kills), the rest the room's normals by their spawn counts; every
## kill rolls the real LootRules (the elite extra roll too) for a character wielding each archetype's first family in
## turn. A region's rates are its rooms' mean. Reports pieces, Fine or better, Superior or better and Perfect an hour per
## grade and zone tier (a region counts for the grade most of its pieces are) and checks them against balance.json
## `drops`, with the usable share per archetype, the region floor, the named pieces and Act III's grades. Each archetype
## set's slowest drop piece must fall within `set_hours` of its band's hunting hours.
func _drops(cfg: Dictionary) -> void:
	var dc: Dictionary = cfg.get("drops", {})
	check(not dc.is_empty(), "balance.json has its drops block")
	if dc.is_empty(): return
	var gear := ContentDB.config("gear")
	var arch: Dictionary = gear.get("archetypes", {})
	var wielders: Array = []
	for a in arch:
		if not (arch[a].families as Array).is_empty(): wielders.append(str(a))
	var order: Array = ContentDB.config("grades").get("quality_order", [])
	var hours := float(dc.get("hours_per_region", 20))
	var kph := float(dc.get("kills_per_hour", 360))
	var regions := _hunting_regions()
	var groups := {}      # "grade·tier" -> [per-region rates]
	var usable := {}      # archetype -> [usable, pieces]
	var species_kph := {} # "species" / "species*" (as an elite) -> best kills an hour in one region
	var bad: Array = []
	var act3 := {}
	var low_regions: Array = []
	var per_region := {}  # region -> {rates: [room rates], grades: {grade: pieces}, tier}
	var names := regions.keys()
	names.sort()
	for ri in names.size():
		var reg: Dictionary = regions[names[ri]]
		var rng := RandomNumberGenerator.new()
		rng.seed = 12345 + ri
		var slots_kph := 0.0
		for sl in reg.elites: slots_kph += float(sl.weight)
		var elite_kph := minf(slots_kph, kph * float(dc.get("elite_share_cap", 0.33)))
		var normal_kph := kph - elite_kph
		var total_w := 0.0
		for sl in reg.normals: total_w += float(sl.weight)
		for sl in reg.normals: species_kph[str(sl.def)] = maxf(float(species_kph.get(str(sl.def), 0.0)), normal_kph * float(sl.weight) / total_w)
		for sl in reg.elites: species_kph[str(sl.def) + "*"] = maxf(float(species_kph.get(str(sl.def) + "*", 0.0)), elite_kph * float(sl.weight) / slots_kph)
		var n_elite := int(round(hours * elite_kph))
		var kills := n_elite + int(round(hours * normal_kph))
		var t := {"pieces": 0.0, "fine_up": 0.0, "superior_up": 0.0, "perfect": 0.0}
		var grades := {}
		for k in kills:
			var elite := k < n_elite
			var sl: Dictionary = LootRules.RngService_weighted(rng, reg.elites if elite else reg.normals)
			var def := ContentDB.entry("enemies", str(sl.def))
			var lv := rng.randi_range(int(sl.lo), int(sl.hi))
			var who: String = wielders[k % wielders.size()]
			var drop := LootRules.roll(str(def.get("loot", sl.def)), rng, lv, 0.0, 0.0, {"elite": elite})
			if elite and str(def.get("role", "normal")) == "normal":
				var ex: Dictionary = LootRules.drop_cfg().get("elite_extra", {})
				if rng.randf() < float(ex.get("chance", 0.0)): drop.equipment.append({"level": lv, "min_quality": str(ex.get("min_quality", "common"))})
			for spec in drop.equipment:
				if spec.has("item"): continue   # a named row's piece: the chase, not the flow
				var inst := LootRules.make_drop(rng, spec, 0.0, true, 0, str(arch[who].families[0]))
				if inst.is_empty(): continue
				var pd := ContentDB.item(str(inst.id))
				if not LootRules.is_banded(pd): bad.append(str(inst.id))
				var q := order.find(str(inst.quality))
				t.pieces += 1.0
				if q >= order.find("fine"): t.fine_up += 1.0
				if q >= order.find("superior"): t.superior_up += 1.0
				if q >= order.find("perfect"): t.perfect += 1.0
				grades[str(pd.grade)] = int(grades.get(str(pd.grade), 0)) + 1
				var u: Array = usable.get(who, [0, 0])
				u[1] += 1
				if str(pd.slot) != "weapon" or str(pd.get("family", "")) in arch[who].families: u[0] += 1
				usable[who] = u
		for key in t: t[key] = float(t[key]) / hours
		var pr: Dictionary = per_region.get(str(reg.region), {"rates": [], "grades": {}, "tier": int(reg.tier)})
		pr.rates.append(t)
		for g in grades: pr.grades[g] = int(pr.grades.get(g, 0)) + int(grades[g])
		per_region[str(reg.region)] = pr
		if int(reg.tier) == 3:
			for g in grades: act3[g] = true
	for region in per_region:
		var pr: Dictionary = per_region[region]
		var t := {}
		for key in ["pieces", "fine_up", "superior_up", "perfect"]:
			var sum := 0.0
			for rt in pr.rates: sum += float(rt[key])
			t[key] = sum / (pr.rates as Array).size()
		var top := ""
		for g in pr.grades:
			if top == "" or int(pr.grades[g]) > int(pr.grades[top]): top = str(g)
		if top == "": continue
		var group := "%s · %d" % [top, int(pr.tier)]
		if not groups.has(group): groups[group] = []
		groups[group].append(t)
		if float(t.pieces) < float(dc.get("region_floor", 3.0)): low_regions.append("%s %.1f" % [region, float(t.pieces)])
	# The report and the checks.
	var targets: Dictionary = dc.get("targets", {})
	print("grade · tier       regions  pieces/h  fine+/h  superior+/h  perfect/h")
	var keys := groups.keys()
	keys.sort_custom(func(a, b): return StatRules.grade_index(str(a).split(" · ")[0]) * 10 + int(str(a).split(" · ")[1]) < StatRules.grade_index(str(b).split(" · ")[0]) * 10 + int(str(b).split(" · ")[1]))
	for gk in keys:
		var mean := {}
		for key in targets:
			var sum := 0.0
			for t in groups[gk]: sum += float(t[key])
			mean[key] = sum / groups[gk].size()
		print("%-18s %7d  %8.2f  %7.2f  %11.3f  %9.3f" % [gk, groups[gk].size(), mean.get("pieces", 0), mean.get("fine_up", 0), mean.get("superior_up", 0), mean.get("perfect", 0)])
		for key in targets:
			var want := float(targets[key][0])
			var tol := float(targets[key][1])
			check(absf(float(mean[key]) / want - 1.0) <= tol, "%s: %s %.3f an hour of hunting (target %.2f ±%d%%)" % [gk, key, float(mean[key]), want, int(tol * 100)])
	var all_pieces := 0.0
	var n_regions := 0
	for gk2 in groups:
		for t in groups[gk2]:
			all_pieces += float(t.pieces)
			n_regions += 1
	print("all %d field regions: %.2f pieces an hour of hunting" % [n_regions, all_pieces / maxf(1.0, n_regions)])
	check(low_regions.is_empty(), "every field region drops at least %.0f pieces an hour (%s)" % [float(dc.get("region_floor", 3.0)), ", ".join(low_regions)])
	var span: Array = dc.get("usable_share", [0.6, 0.85])
	for who in usable:
		var share := float(usable[who][0]) / maxf(1.0, float(usable[who][1]))
		print("  %s: %.0f%% of the pieces fit" % [who, share * 100.0])
		check(share >= float(span[0]) and share <= float(span[1]), "%s: %.2f of drops are usable (%.2f-%.2f)" % [who, share, float(span[0]), float(span[1])])
	check(bad.is_empty(), "no named, set, relic, legend or imitation piece from the random roll (%s)" % str(bad.slice(0, 4)))
	check(act3.has("sovereign") and act3.has("will"), "Act III's regions drop Sovereign and Will gear (%s)" % str(act3.keys()))
	# Each archetype set's slowest drop piece, in hours of focused hunting, against its band's hunting hours.
	var fight := float(cfg.get("mix", {}).get("fight", 0.35))
	var band_hours: Dictionary = dc.get("band_hours", {})
	var set_span: Array = dc.get("set_hours", [0.3, 0.8])
	var checked := 0
	for st in ContentDB.all("sets"):
		if str(st.get("archetype", "general")) == "general": continue
		var grade := str(ContentDB.item(str(st.pieces[0])).get("grade", ""))
		if not band_hours.has(grade): continue   # past Spirit: the Act III simulation gives those bands their hours
		var slowest := 0.0
		for pid in st.pieces:
			var rate := _piece_rate(str(pid), species_kph)
			if rate >= 0.0: slowest = maxf(slowest, 1.0 / maxf(rate, 0.0001) if rate > 0.0 else 1e9)
		var share := slowest / (float(band_hours[grade]) * fight)
		checked += 1
		check(share >= float(set_span[0]) and share <= float(set_span[1]), "set %s: its slowest piece takes %.1f h of hunting, %.2f of the %s band's (%.2f-%.2f)" % [
			st.id, slowest, share, grade, float(set_span[0]), float(set_span[1])])
	print("  archetype sets timed: %d" % checked)

## The hunting rooms: every room that is not safe or instanced and holds ordinary foes, with its normal spawns
## (weighted by their counts) and its elite slots (weighted by their kills an hour), their Levels, its region and zone
## tier. Bosses, events, trials and the passive wild animals are not hunted.
func _hunting_regions() -> Dictionary:
	var out := {}
	var per_slot := float(ContentDB.config("balance").get("drops", {}).get("elite_kills_per_slot", 20))
	for rid in ContentDB.rooms:
		var room: Dictionary = ContentDB.room(rid)
		if room.get("safe", false) or room.get("instanced", false): continue
		for sp in room.get("spawns", []):
			var def := ContentDB.entry("enemies", str(sp.get("enemy", "")))
			var role := str(def.get("role", ""))
			if not role in ["normal", "elite"] or def.get("passive", false) or sp.get("boss", false): continue
			if not out.has(rid): out[rid] = {"normals": [], "elites": [], "tier": int(ContentDB.zone_of_room(rid).get("tier", 1)), "region": str(room.get("region", rid))}
			var lv = sp.get("level", def.get("level", [1, 1]))
			var band: Array = lv if lv is Array else [lv, lv]
			var elite: bool = sp.get("elite", false) or role == "elite"
			var weight: float = minf(per_slot, 3600.0 / maxf(1.0, float(sp.get("respawn_s", 180)))) if elite else float(sp.get("max", 1))
			out[rid]["elites" if elite else "normals"].append({"def": str(def.id), "lo": int(band[0]), "hi": int(band.back()), "weight": weight})
	for r in out.keys():
		if (out[r].normals as Array).is_empty(): out.erase(r)   # a lone elite in a vault is not a hunting ground
	return out

## A set piece's drops an hour at its best source (named rows: every kill of the species; elite_named: its elite
## slots), or -1 when a shop, a craft, a quest or the tower hands it out (it costs no hunting).
func _piece_rate(pid: String, species_kph: Dictionary) -> float:
	var best := -2.0
	for e in ContentDB.all("enemies"):
		var t := ContentDB.entry("loot_tables", str(e.get("loot", e.id)))
		for key in ["named", "elite_named"]:
			for r in t.get(key, []):
				if str(r.item) != pid: continue
				var k := float(species_kph.get(str(e.id) + ("*" if key == "elite_named" else ""), 0.0))
				if key == "named": k += float(species_kph.get(str(e.id) + "*", 0.0))
				best = maxf(best, float(r.chance) * k)
	return -1.0 if best < -1.0 else best
## S50 Keeping Post (docs/idle_gathering_design.md §8): the calibration targets from the real formulas and node data.
func _posts() -> void:
	var nodes: Dictionary = ContentDB.config("posts").get("nodes", {})
	var chance := func(fin: float, item: String) -> float: return float(PostRules.yield_of(fin, float(nodes[item].toughness)).chance)
	var f0 := PostRules.finesse(6.0, 10.0, 1)
	var r0 := PostRules.rates(f0, [{"item": "copper_ore", "toughness": nodes.copper_ore.toughness, "exp": nodes.copper_ore.exp, "weight": 1.0}], 3.0, PostRules.diligence("craft"))
	check(float(r0.items.copper_ore) >= 70.0 and float(r0.items.copper_ore) <= 100.0, "a new delver's copper post: %.0f an hour (70-100)" % float(r0.items.copper_ore))
	var fv := PostRules.finesse(13.0, 70.0, 25)
	check(absf(chance.call(fv, "jadeiron") - 0.5) <= 0.1 and absf(chance.call(fv, "spirit_stone_shard") - 0.4) <= 0.1,
		"valley end: jadeiron %.0f%%, spirit stone shard %.0f%% (about 50 and 40)" % [100.0 * chance.call(fv, "jadeiron"), 100.0 * chance.call(fv, "spirit_stone_shard")])
	var fe := PostRules.finesse(24.0, 115.0, 42, 0.0, [8.0])
	check(chance.call(fe, "stormsteel_ore") >= 0.3, "the Expanse: stormsteel %.0f%% (at least 30)" % (100.0 * chance.call(fe, "stormsteel_ore")))
	var fl := PostRules.finesse(35.0, 150.0, 55, 0.0, [16.0])
	check(chance.call(fl, "driftglass") >= 0.3, "Act III: driftglass %.0f%% before the account web (at least 30)" % (100.0 * chance.call(fl, "driftglass")))
	var rv := PostRules.rates(fv, [{"item": "jadeiron", "toughness": nodes.jadeiron.toughness, "exp": 30.0, "weight": 1.0}], 4.0, PostRules.diligence("craft"))
	var satchel := PostRules.capacity(PostRules.compartment_cap(4)) / float(rv.items.jadeiron)
	check(satchel >= 10.0 and satchel <= 16.0, "a Satchel pouch holds %.1f h of a valley-end post (10-16)" % satchel)
	check(PostRules.capacity(PostRules.compartment_cap(0)) / float(r0.items.copper_ore) <= 1.0, "an unsewn pouch fills within the hour")

## V10d3 (docs/idle_gathering_design.md §6, §9): thirty days of twelve characters at their posts, 20 hours a day,
## the account web bought greedily from the Storehouse and a day's silver of active play: Post Arts (Dreaming
## Artisan, then Steady Hand), craft seals, Guardian Steles, the Favour of the Guilds, the Cinnabar line and two
## plain flags over half the posts. Reports Diligence, what the web multiplies Finesse by, levels and salts.
func _account_month() -> void:
	var cfg: Dictionary = ContentDB.config("posts")
	var nodes: Dictionary = cfg.get("nodes", {})
	var crafts := ["delving", "foraging", "angling", "netting"]
	var tools := {"delving": [13.0, 4.0], "foraging": [14.0, 4.0], "angling": [19.0, 4.0], "netting": [20.0, 5.0]}   # tier 3
	var attr := 60.0
	var ladders := {}
	for cr in crafts: ladders[cr] = []
	for id in nodes:
		var n: Dictionary = nodes[id]
		if ladders.has(str(n.get("craft", ""))) and not n.get("side", false): ladders[str(n.craft)].append(str(id))
	for cr in crafts: ladders[cr].sort_custom(func(a, b): return int(nodes[a].gate) < int(nodes[b].gate))
	var arts_def := {}
	for a in cfg.get("post_arts", []): arts_def[str(a.id)] = a
	var seal_of := {}
	for sd in cfg.get("seals", []):
		if str(sd.get("craft", "")) in crafts: seal_of[str(sd.craft)] = sd
	var chars: Array = []
	# Three characters to a craft, each a rung below the last: the account's goods span the ladder seals and steles climb.
	for i in 12: chars.append({"craft": crafts[i % 4], "rung": i / 4, "xp": 0.0, "arts": {"dreaming_artisan": 0, "steady_hand": 0}, "flag": i < 6})
	var store := {}
	var seals := {}
	var steles := {}
	var web := {"guilds": false, "flag": -1}   # a Dictionary: lambdas capture locals by value
	var taels := 0.0
	var line := {"rank": 1, "fire": 0, "refined": 0}
	var st: Dictionary = cfg.get("steles", {})
	var flag_plain: Dictionary = cfg.get("flags", {}).get("kinds", {}).get("plain", {})
	var dil_of := func(ch: Dictionary) -> float:
		var a: Dictionary = arts_def.dreaming_artisan
		var src := PostRules.curve("decay", float(a.x1), float(a.x2), float(ch.arts.dreaming_artisan)) + (3.0 if web.guilds else 0.0)
		if ch.flag and int(web.flag) >= 0: src += float(flag_plain.base) + float(flag_plain.per_level) * int(web.flag)
		return PostRules.diligence("craft", src)
	var fin_of := func(ch: Dictionary, web: bool) -> float:
		var lv := PostRules.level_for(float(ch.xp))
		var t: Array = tools[ch.craft]
		if not web: return PostRules.finesse(float(t[0]), attr, lv)
		var sh: Dictionary = arts_def.steady_hand
		var groups: Array = [PostRules.curve("decay", float(sh.x1), float(sh.x2), float(ch.arts.steady_hand))]
		var flat := 3.0 * mini(int(seals.get(ch.craft, 0)), lv)
		return PostRules.finesse(float(t[0]), attr, lv, flat, groups, float(steles.get(ch.craft, 0)) * float(st.get("power_per_level", 0.3)))
	var rows := {}
	for day in range(1, 31):
		taels += 15000.0
		for ch in chars:
			var lv := PostRules.level_for(float(ch.xp))
			var fin: float = fin_of.call(ch, true)
			var best := 0
			var lad: Array = ladders[ch.craft]
			for k in lad.size():
				if int(nodes[lad[k]].gate) <= lv and float(PostRules.yield_of(fin, float(nodes[lad[k]].toughness)).chance) >= 0.3: best = k
			var pick := str(lad[maxi(0, best - int(ch.rung))])
			var n: Dictionary = nodes[pick]
			var r := PostRules.rates(fin, [{"item": pick, "toughness": float(n.toughness), "exp": float(n.exp), "weight": 1.0}], float(tools[ch.craft][1]), dil_of.call(ch))
			store[pick] = float(store.get(pick, 0.0)) + float(r.items[pick]) * 20.0
			ch.xp = float(ch.xp) + float(r.exp_h) * 20.0
			# Post Arts: a point every two levels (the character knows four crafts), Dreaming Artisan to 40 first.
			var pts := PostRules.art_points(PostRules.level_for(float(ch.xp)) + 3) - int(ch.arts.dreaming_artisan) - int(ch.arts.steady_hand)
			while pts > 0:
				if int(ch.arts.dreaming_artisan) < 40: ch.arts.dreaming_artisan += 1
				else: ch.arts.steady_hand += 1
				pts -= 1
		# The Cinnabar line from day 3: 96 cycles a day as far as copper and moss last; refined each evening.
		if day >= 3:
			var rk := int(line.rank)
			var cyc := 96
			cyc = mini(cyc, int(float(store.get("copper_ore", 0.0)) / PostRules.calcination_cost(rk, 3)))
			cyc = mini(cyc, int(float(store.get("willow_moss", 0.0)) / PostRules.calcination_cost(rk, 2)))
			store["copper_ore"] = float(store.get("copper_ore", 0.0)) - cyc * PostRules.calcination_cost(rk, 3)
			store["willow_moss"] = float(store.get("willow_moss", 0.0)) - cyc * PostRules.calcination_cost(rk, 2)
			var salts := cyc * PostRules.calcination_fire(rk)
			store["cinnabar_salt"] = float(store.get("cinnabar_salt", 0.0)) + salts
			line.refined = int(line.refined) + salts
			while int(line.refined) >= PostRules.calcination_rank_need(int(line.rank)):
				line.refined = int(line.refined) - PostRules.calcination_rank_need(int(line.rank))
				line.rank = int(line.rank) + 1
		# Seals: as deep as the Storehouse pays (salts past 10), keeping half of each good.
		for cr in crafts:
			var sd: Dictionary = seal_of[cr]
			while int(seals.get(cr, 0)) < int(sd.max):
				var cost := PostRules.seal_cost(int(seals.get(cr, 0)), sd.ladder)
				if float(store.get(str(cost.item), 0.0)) < 2.0 * int(cost.count): break
				if cost.has("salt") and float(store.get(str(cost.salt), 0.0)) < int(cost.salt_count): break
				store[str(cost.item)] = float(store[str(cost.item)]) - int(cost.count)
				if cost.has("salt"): store[str(cost.salt)] = float(store[str(cost.salt)]) - int(cost.salt_count)
				seals[cr] = int(seals.get(cr, 0)) + 1
		# Steles with a third of the day's silver, cheapest first.
		var budget := 5000.0
		for k in 40:
			var best := ""
			for cr in crafts:
				if best == "" or int(steles.get(cr, 0)) < int(steles.get(best, 0)): best = cr
			var sc := PostRules.stele_cost(int(steles.get(best, 0)))
			if float(sc.taels) > budget or float(store.get(str(sc.item), 0.0)) < int(sc.count) or int(steles.get(best, 0)) >= int(st.get("max", 40)): break
			budget -= float(sc.taels)
			taels -= float(sc.taels)
			store[str(sc.item)] = float(store[str(sc.item)]) - int(sc.count)
			steles[best] = int(steles.get(best, 0)) + 1
		if not web.guilds and taels >= 6000.0 and float(store.get("jadeiron", 0.0)) >= 300.0 and float(store.get("reed_cicada", 0.0)) >= 200.0:
			web.guilds = true
			taels -= 6000.0
			store["jadeiron"] = float(store.jadeiron) - 300.0
			store["reed_cicada"] = float(store.reed_cicada) - 200.0
		if day >= 10:
			if int(web.flag) < 0: web.flag = 0
			var fc := PostRules.flag_cost(int(web.flag))
			while int(web.flag) < 20 and float(store.get(str(fc.salt), 0.0)) >= 2.0 * int(fc.salt_count):
				store[str(fc.salt)] = float(store[str(fc.salt)]) - 2.0 * int(fc.salt_count)
				web.flag = int(web.flag) + 1
				fc = PostRules.flag_cost(int(web.flag))
		if day in [1, 10, 20, 30]:
			var dsum := 0.0
			var mult := 0.0
			var lvs := 0
			for ch in chars:
				dsum += float(dil_of.call(ch))
				mult += (float(fin_of.call(ch, true)) - 12.0) / (float(fin_of.call(ch, false)) - 12.0)
				lvs += PostRules.level_for(float(ch.xp))
			rows[day] = {"dil": dsum / 12.0, "mult": mult / 12.0, "level": lvs / 12.0}
			print("  day %d: Craft Diligence %.0f%%, web Finesse x%.2f, craft level %.1f, seals %s, steles %s, line rank %d, flag %d, guilds %s" % [day,
				100.0 * dsum / 12.0, mult / 12.0, lvs / 12.0, str(seals.values()), str(steles.values()), int(line.rank), int(web.flag), str(web.guilds)])
	check(absf(PostRules.diligence("craft") - 0.52) < 0.001, "a new account's posts work at 52%")
	check(float(rows[30].dil) >= 0.6 and float(rows[30].dil) <= 0.8, "day 30: Craft Diligence %.0f%% (60-80 from arts, the Guilds and flags alone)" % (100.0 * float(rows[30].dil)))
	check(float(rows[10].mult) > 1.3 and float(rows[30].mult) >= float(rows[10].mult), "the web's Finesse keeps growing (x%.2f at day 10, x%.2f at day 30)" % [float(rows[10].mult), float(rows[30].mult)])
	check(float(rows[30].mult) >= 1.5 and float(rows[30].mult) <= 2.5, "day 30: the account web multiplies Finesse by %.2f (1.5-2.5 in the first month; 2-4 later)" % float(rows[30].mult))
	check(int(line.rank) >= 3, "a month of the Cinnabar line reaches rank %d (opening the Verdigris line)" % int(line.rank))

func _finish() -> void:
	print("balance_sim: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

## QP per active minute at this stage, from the real rules.
func _income(c, cfg: Dictionary, key: String, lv: int) -> float:
	var mix: Dictionary = cfg.get("mix", {})
	var major := str(ContentDB.realm(key).get("realm", key))
	c.cultivator.realm_key = key
	c.cultivator.method_id = str(cfg.get("method", {}).get(major, "riverbreath_fragment"))
	c.cultivator.stability = str(cfg.get("stability", "stable"))
	c.cultivator.consolidation_penalty = false
	var fight := float(cfg.get("kills_per_min", 6)) * ProgressionRules.kill_qp(lv, lv, "normal")
	var density := float(cfg.get("density", {}).get(major, 1.0))
	var sit := ProgressionRules.meditation_rate(c, density, 0.0)
	if ProgressionRules.is_body_stage(key): sit = maxf(sit, float(ContentDB.curve("training_qp_per_min", 40)))
	return float(mix.get("fight", 0.4)) * fight + float(mix.get("meditate", 0.3)) * sit

## Level -> [[quest kind, cultivation], ...]: each quest at its own tier (decision 45: quests.json `tier`, the Level
## story.py pitches it at, from its realm floor, chapter, the unlock that offers it, the quests it follows, its foes)
## with the fixed cultivation it pays on hand-in (its `cultivation` and any add_progress reward).
func _quest_levels() -> Dictionary:
	var out := {}
	for q in ContentDB.all("quests"):
		var kind := str(q.get("qp", q.get("kind", "side")))
		if kind == "prologue": continue
		var lv := int(ContentDB.realm(str(q.get("tier", "mortal"))).get("level", 0))
		var gain := float(q.get("cultivation", 0))
		for rw in q.get("rewards", []):
			if str(rw.get("kind", "")) == "add_progress": gain += float(rw.get("amount", 0))
		if not out.has(lv): out[lv] = []
		out[lv].append([kind, gain])
	return out

func _character():
	var folder := "user://balance_sim/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Clock.override_utc = 1767225600.0   # a fixed "now" and seed: the same character every run
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 2026
	Rng.restore("account", {}, 2026)
	Game.submit({"type": "create_character", "slot": 1, "name": "Balance", "appearance": {"hair": "topknot"}})
	Game.submit({"type": "enter_character", "slot": 1})
	return Game.active()
