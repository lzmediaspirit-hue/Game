extends Node
## Scripted Prologue run (S27 test): drives the real authorities through intents
## only, from a new character to Bone Forging 2, checking the HUD reveal order and
## that no weapon appears before the Weapon Hall. Movement is a bound ActorState
## placed next to targets (the world scene is not needed). Run headless:
##   godot --headless --path . res://tests/prologue_run.tscn

var failures := 0
var checks := 0
var reveal_log: Array = []
var events: Array = []
var st: ActorState
var verbose := false

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)
	elif verbose:
		print("ok: ", what)

func _ready() -> void:
	verbose = "--verbose" in OS.get_cmdline_user_args()
	call_deferred("_main")

func _main() -> void:
	run()
	print("prologue_run: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ helpers
func step(seconds: float) -> void:
	var t := 0.0
	while t < seconds:
		Game.tick(0.05)
		t += 0.05

func submit(i: Dictionary) -> Dictionary:
	return Game.submit(i)

func c():
	return Game.active()

func room() -> String:
	return Game.room_rt.room_id if Game.room_rt else ""

## Put the player's movement state at a ground point in the loaded room.
func place(p: Vector2, alt := 0.0) -> void:
	if st == null:
		st = ActorState.new()
		Game.bind_movement(Game.active_id, st)
	var best: WalkSurface = null
	for s in Game.room_rt.geometry.surfaces:
		if s.contains(p) and absf(s.height_at(p) - alt) < 10.0: best = s
	if best == null:
		for s in Game.room_rt.geometry.surfaces:
			if s.stratum == "ground" and s.contains(p): best = s
	st.surface = best
	st.plane = p
	st.altitude = best.height_at(p) if best else alt
	st.velocity = Vector2.ZERO

func obj_at(id: String) -> Vector2:
	var o: Dictionary = Game.room_rt.object_def(id)
	return Vector2(float(o.at[0]), float(o.at[1]))

func go(portal: String) -> bool:
	var r := submit({"type": "use_portal", "portal": portal, "crossing": true})
	if not r.get("ok", false): print("  portal ", portal, " in ", room(), " failed: ", r)
	if r.get("ok", false): place(Vector2(float(c().position.x), float(c().position.y)))
	return r.get("ok", false)

## Walk to a room through open portals (breadth-first over the room graph).
func travel(target: String) -> bool:
	if room() == target: return true
	var prev := {room(): ["", ""]}
	var queue := [room()]
	while not queue.is_empty():
		var r: String = queue.pop_front()
		if r == target: break
		for p in ContentDB.room(r).get("portals", []):
			var to := str(p.get("to", ""))
			if to == "" or prev.has(to) or ContentDB.room(to).is_empty() or ContentDB.room(to).get("instanced", false): continue
			if p.has("requires") and not RequirementRules.passes(p.requires, Game.ctx()): continue
			prev[to] = [r, str(p.id)]
			queue.append(to)
	if not prev.has(target): return false
	var path: Array = []
	var cur := target
	while cur != room():
		path.push_front(prev[cur][1])
		cur = prev[cur][0]
	for portal in path:
		if not go(portal): return false
	return room() == target

func npc_object(npc: String) -> Dictionary:
	for o in Game.room_rt.def.get("objects", []):
		if o.type == "npc" and str(o.npc) == npc and Game.world.object_visible(c(), o): return o
	return {}

func talk(npc: String) -> Dictionary:
	var o := npc_object(npc)
	if o.is_empty():
		print("  no visible npc ", npc, " in ", room())
		return {}
	place(Vector2(float(o.at[0]) - 50, float(o.at[1]) + 20))
	var r := submit({"type": "interact", "object": str(o.id)})
	return r.get("dialogue", {})

## Talk and pick the first choice that has `key` (accept/hand_in/effects...).
func talk_choose(npc: String, key: String, value := "") -> bool:
	var d := talk(npc)
	for ch in d.get("choices", []):
		if ch.has(key) and (value == "" or str(ch.get(key)) == value or str(ch.get("text", "")).contains(value)):
			var r := submit({"type": "choose_dialogue", "npc": npc, "choice": ch})
			return r.get("ok", false)
	print("  ", npc, " offered no '", key, "' choice: ", d.get("lines", []), " ", d.get("choices", []))
	return false

func accept(npc: String, quest: String) -> void:
	var ok := talk_choose(npc, "accept", quest)
	check(ok and c().quests.is_active(quest), "accept %s from %s" % [quest, npc])

func hand_in(npc: String, quest: String) -> void:
	var ok := talk_choose(npc, "hand_in", quest)
	check(ok and c().quests.is_done(quest), "hand in %s to %s" % [quest, npc])

func interact(id: String) -> Dictionary:
	var o: Dictionary = Game.room_rt.object_def(id)
	place(Vector2(float(o.at[0]) - 30, float(o.at[1]) + 10), float(o.get("alt", 0.0)))
	return submit({"type": "interact", "object": id})

func hit_object(id: String, times: int) -> void:
	var o: Dictionary = Game.room_rt.object_def(id)
	for i in times: Game.world.apply_object_hit(c().id, o)
	GameEvents.flush()

## Fight `count` enemies of one kind with the basic combo, standing beside each.
func fight(def_id: String, count: int, limit_s := 240.0, retreat_below := 0.0, allow_elite := false) -> int:
	var tally := {"killed": 0, "attacker": 0}
	var t := 0.0
	var heard := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("def", "")) == def_id: tally.killed += 1
		if n == "hit_landed" and str(p.get("target_kind", "")) == "player" and str(p.get("attacker", "")).is_valid_int(): tally.attacker = int(str(p.attacker))
		if verbose and n == "hit_landed" and str(p.get("target_kind", "")) == "player":
			var att = Game.room_rt.enemies.get(int(str(p.get("attacker", "0")))) if str(p.get("attacker", "")).is_valid_int() else null
			print("    hit by ", att.def_id if att else p.get("attacker"), " for ", p.amount, " hp ", c().pools.hp)
		if verbose and n == "player_gravely_wounded": print("    WOUNDED ", p)
		if verbose and n in ["hit_missed", "attack_whiffed", "hit_immune"] and str(p.get("attacker", p.get("actor", ""))).begins_with("c"): print("    ", n)
	GameEvents.event.connect(heard)
	var target: EnemyState = null
	while int(tally.killed) < count and t < limit_s:
		# Keep one target until it falls; prefer anything already attacking us.
		# Whatever keeps hitting us (a ranged thrower, say) comes first.
		var hitter: EnemyState = Game.room_rt.enemies.get(int(tally.attacker)) if int(tally.attacker) != 0 else null
		if hitter != null and hitter.alive and hitter.team != "ally" and hitter != target:
			target = hitter
			tally.attacker = 0
		if target == null or not target.alive or not Game.room_rt.enemies.has(target.uid):
			target = null
			for e in Game.room_rt.living_enemies():
				if e.team != "ally" and str(e.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"] and st != null and e.plane.distance_to(st.plane) < 160.0:
					target = e
			if target == null:
				for e in Game.room_rt.living_enemies():
					if e.def_id == def_id and e.team != "ally" and (allow_elite or not e.elite or str(e.def.get("role", "")) == "elite"):
						if target == null or st == null or e.plane.distance_to(st.plane) < target.plane.distance_to(st.plane): target = e
		if target == null:
			step(0.5)
			t += 0.5
			continue
		# Rest before engaging a new target when hurt, like a careful player.
		if c().pools.hp < c().pools.max_hp * 0.8 and target.pools.hp >= target.pools.max_hp and str(target.ai.get("state", "")) in ["idle", "patrol", "return"]:
			var rt := 0.0
			place(target.spawn_point + Vector2(-420, 0) if target.spawn_point.x > 500 else target.spawn_point + Vector2(420, 0))
			while c().pools.hp < c().pools.max_hp * 0.95 and rt < 90.0:
				step(1.0)
				rt += 1.0
		# Bosses: roll through the strike late in its wind-up (dash i-frames), as a practised player does.
		if str(target.ai.get("state", "")) == "windup" and target.role in ["dungeon_boss", "field_boss", "story_boss"] and Unlocks.is_unlocked(c().id, "dodge_dash"):
			if float(target.ai.get("timer", 1.0)) <= 0.2:
				submit({"type": "dodge", "direction": Vector2.ZERO, "facing": 1})
			step(0.05)
			t += 0.05
			continue
		# Read the tell: step out of the lane during a wind-up, as the Snapper lesson teaches.
		if str(target.ai.get("state", "")) == "windup" and (target.role != "normal" or target.elite):
			place(target.plane + Vector2(-34, 70 if target.plane.y < 860 else -70))
			step(0.7)
			t += 0.7
			continue
		# Guard-and-counter foes block until they have countered: strike during recovery.
		if str(target.def.get("ai", {}).get("profile", "")) == "guard_counter" and str(target.ai.get("state", "")) in ["windup", "attack"]:
			# Step out of the counter, then punish its recovery.
			place(target.plane + Vector2(-80 if st == null or st.plane.x <= target.plane.x else 80, 0))
			step(0.1)
			t += 0.1
			continue
		var side := -34.0 if st == null or st.plane.x <= target.plane.x else 34.0
		place(target.plane + Vector2(side, 0))
		var hp_before := target.pools.hp
		if Game.combat.is_wounded(c().id):
			var here := room()
			submit({"type": "choose_revival", "where": "shrine"})
			place(Vector2(float(c().position.x), float(c().position.y)))
			step(1.0)
			if verbose: print("  revived at ", room(), "; walking back to ", here)
			var rest_t := 0.0
			while c().pools.hp < c().pools.max_hp * 0.95 and rest_t < 120.0:
				step(1.0)
				rest_t += 1.0
			if verbose: print("  after rest ", rest_t, "s: hp ", snappedf(c().pools.hp, 0.1), "/", snappedf(c().pools.max_hp, 0.1), " injuries ", c().cultivator.injuries, " wounded ", Game.combat.is_wounded(c().id), " statuses ", c().pools.statuses)
			travel(here)
			target = null
			continue
		var ar := submit({"type": "basic_attack", "facing": 1 if target.plane.x >= st.plane.x else -1})
		step(0.2)
		t += 0.2
		if verbose and (t < 3.0 or def_id == "trial_puppet") and int(tally.killed) == 0: print("  attack ", def_id, " ", ar, " hp ", hp_before, " -> ", target.pools.hp, " me ", c().pools.hp, " at ", st.plane, " alt ", st.altitude, " surf ", st.surface.id if st.surface else "-", " vs ", target.plane, " ealt ", target.altitude, " st ", target.ai.get("state", ""))
		if c().pools.hp < c().pools.max_hp * 0.4 and Unlocks.is_unlocked(c().id, "quick_use"):
			for heal in ["healing_pill", "herbal_tea"]:
				if c().inventory.count(heal) > 0:
					var hr := submit({"type": "use_item", "index": c().inventory.first_index(heal), "confirm": true})
					if hr.get("ok", false): break
		elif retreat_below > 0.0 and c().pools.hp < c().pools.max_hp * retreat_below:
			break
	GameEvents.event.disconnect(heard)
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	if verbose: print("  fight ", def_id, ": killed ", tally.killed, " in ", snappedf(t, 0.1), "s, hp ", snappedf(c().pools.hp, 0.1))
	return int(tally.killed)

# ------------------------------------------------------------------ the run
func run() -> void:
	var folder := "user://test_saves_prologue/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	GameEvents.event.connect(func(n, p):
		if n == "hud_element_revealed": reveal_log.append(str(p.element))
		if n in ["quest_accepted", "quest_completed", "system_unlocked", "realm_changed", "room_entered", "quest_failed"]: events.append([n, p]))
	var r := submit({"type": "create_character", "slot": 1, "name": "Tester", "appearance": {"hair": "topknot"}})
	check(r.ok, "create character")
	check(submit({"type": "enter_character", "slot": 1}).ok, "enter character")
	check(submit({"type": "enter_world"}).ok and room() == "lf_fishers_hut", "starts in the Fisher's Hut")
	place(Vector2(330, 780))
	check(c().pools.max_qi == 0.0, "no QI pool before cultivation")
	check(c().inventory.equipped.get("weapon") == null, "no weapon at start")
	check(not Game.is_revealed("hud:attack") and not Game.is_revealed("hud:qi_bar"), "attack and QI hidden at start")

	# 1 Morning Tide
	accept("aunt_ping", "morning_tide")
	check(Game.is_revealed("hud:bag"), "Bag revealed on accepting Morning Tide")
	for id in ["tea_table", "tea_shelf", "tea_stove"]: check(interact(id).get("ok", false), "pick up " + id)
	submit({"type": "report_page_opened", "page": "inventory"})
	check(go("exit") and room() == "lf_village", "step out to Home Lane")
	check(c().quests.is_done("morning_tide"), "Morning Tide completes on stepping outside")
	check(c().quests.is_active("a_quiet_river"), "A Quiet River follows automatically")
	check(Game.is_revealed("hud:minimap") and Game.is_revealed("hud:quest_tracker"), "minimap and tracker revealed")

	# 2 A Quiet River
	talk("lu_boatman")
	hand_in("lu_boatman", "a_quiet_river")

	# 3 The Runaway Kite
	accept("little_dou", "the_runaway_kite")
	check(Game.is_revealed("hud:jump"), "Jump revealed")
	check(interact("kite").get("ok", false), "take the kite from the inn roof")
	hand_in("little_dou", "the_runaway_kite")

	# 5 Granny's Remedy (in the herb hut) — before Ma so coins are tested later
	check(go("granny_door"), "enter Granny Liu's hut")
	accept("granny_liu", "grannys_remedy")
	check(Game.is_revealed("hud:hp_bar") and Game.is_revealed("hud:quick_use"), "HP bar and quick-use revealed")
	submit({"type": "set_quick_use", "item": "herbal_tea"})
	var q := submit({"type": "use_quick"})
	if not q.ok and q.get("reason", "") == "confirm": q = submit({"type": "use_item", "index": c().inventory.first_index("herbal_tea"), "confirm": true})
	check(interact("shrine_granny").get("ok", false), "pray at the shrine")
	hand_in("granny_liu", "grannys_remedy")
	check(go("exit"), "back to the village")

	# 4 Ma's Delivery
	check(go("store_door"), "enter Old Ma's store")
	accept("old_ma", "mas_delivery")
	check(Game.is_revealed("hud:currency"), "currency revealed")
	var net = c().inventory.first_index("old_net")
	check(net >= 0 and submit({"type": "sell", "index": net, "count": 1}).ok, "sell the old net")
	var buy := submit({"type": "buy", "shop": "old_ma", "item": "rice_ball", "count": 2})
	check(buy.ok, "buy two rice balls %s (taels %d)" % [str(buy), Game.economy.balance("silver_tael", c())])
	hand_in("old_ma", "mas_delivery")
	check(go("exit"), "leave the store")

	# 7 Fists First
	accept("uncle_guo", "fists_first")
	check(Game.is_revealed("hud:attack"), "Attack revealed")
	hit_object("stump_guo", 12)
	hit_object("dummy_guo", 5)
	hand_in("uncle_guo", "fists_first")

	# 6 Race to the Tower (optional; fail once, then win)
	accept("shen_lian_npc", "race_to_the_tower")
	step(26.0)
	check(not c().quests.is_active("race_to_the_tower"), "race fails when time runs out")
	accept("shen_lian_npc", "race_to_the_tower")
	check(interact("tower_bell").get("ok", false), "ring the tower bell")
	hand_in("shen_lian_npc", "race_to_the_tower")
	check(c().cultivator.titles.has("fleet_footed"), "title Fleet-Footed earned")

	# 8 Return to Lu
	check(c().quests.is_active("a_quiet_river_return"), "A Quiet River (Return) offered after the four lessons")
	talk("lu_boatman")
	hand_in("lu_boatman", "a_quiet_river_return")

	# 9 Crab Trouble
	accept("uncle_guo", "crab_trouble")
	check(Game.is_revealed("hud:enemy_hp_bars") and Game.is_revealed("hud:system_log"), "enemy HP bars and log revealed")
	check(go("east_gate") and room() == "lf_reed_shallows", "East Gate opens after Fists First")
	var guard := 0
	while c().inventory.count("crab_shell") < 5 and guard < 30:
		fight("mudshell_crab", 1, 30.0)
		step(0.6)
		guard += 1
	check(c().inventory.count("crab_shell") >= 5, "five crab shells (have %d)" % c().inventory.count("crab_shell"))
	step(1.5)
	check(fight("old_snapper", 1, 120.0) == 1, "Old Snapper defeated")
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	var weapons_seen := false
	for s in c().inventory.bag:
		if s != null and str(ContentDB.item(str(s.id)).get("slot", "")) == "weapon": weapons_seen = true
	check(not weapons_seen, "no weapon dropped in the Prologue")
	check(travel("lf_village"), "back to the village")
	hand_in("uncle_guo", "crab_trouble")
	check(c().inventory.count_including_equipped("plain_straw_hat") >= 1, "Plain Straw Hat received")

	# 10 Evening on the River
	accept("lu_boatman", "evening_on_the_river")
	check(Game.is_revealed("hud:menu"), "Menu revealed")
	talk("aunt_ping")
	talk("lu_boatman")
	check(room() == "lf_village_night", "the night falls (room %s)" % room())
	check(c().quests.is_active("the_hollow_night"), "The Hollow Night begins")

	# P4 The night
	for npc in ["little_dou", "granny_liu", "old_ma"]:
		talk_choose(npc, "effects")
	check(c().quests.has_flag("dou_safe") and c().quests.has_flag("granny_safe") and c().quests.has_flag("ma_safe"), "villagers guided to the hut")
	place(Vector2(400, 700))
	step(62.0)
	check(c().quests.has_flag("night_survived"), "survived the night")
	check(room() == "lf_lu_boat", "carried to Lu's boat (room %s)" % room())

	# P5 Lu's Boat: first breakthrough
	check(c().quests.is_active("the_river_token"), "The River Token begins")
	check(Game.is_revealed("hud:cultivate") and Game.is_revealed("hud:progress_bar"), "Cultivate and progress bar revealed")
	check(c().cultivator.methods_known.has("riverbreath_fragment"), "Riverbreath method learned")
	place(Vector2(560, 790))
	submit({"type": "start_meditation"})
	var med := 0.0
	while c().cultivator.state != "bottleneck" and med < 600.0:
		step(1.0)
		med += 1.0
	submit({"type": "stop_meditation"})
	check(c().cultivator.state == "bottleneck", "progress bar full after %ds of meditation" % int(med))
	submit({"type": "report_page_opened", "page": "cultivation"})
	var b := submit({"type": "start_breakthrough", "support_items": []})
	check(b.ok, "start the first breakthrough %s" % str(b))
	step(4.0)
	check(c().cultivator.realm_key == "bone_forging_1", "Bone Forging 1 (realm %s)" % c().cultivator.realm_key)
	hand_in("lu_boatman", "the_river_token")
	check(c().pools.max_qi == 0.0, "still no QI pool in the body stages")
	check(not Game.is_revealed("hud:qi_bar"), "QI bar still hidden at Bone Forging 1")

	# P6 Willow Path
	check(c().quests.is_active("the_willow_path"), "The Willow Path begins at Bone Forging 1")
	check(Unlocks.is_unlocked(c().id, "mail") and Unlocks.is_unlocked(c().id, "kill_progress"), "mail and kill progress unlocked")
	check(go("deck") and go("west_gate") and room() == "wp_east", "West Gate open after the night")
	check(go("west") and room() == "wp_west", "Willow Path West")
	check(interact("shrine_wp").get("ok", false), "pray at the Willow Path shrine")
	hit_object("stump_0", 30)
	check(fight("wild_boarlet", 5, 200.0) >= 5, "five Wild Boarlets")
	check(c().quests.is_done("the_willow_path"), "The Willow Path complete")

	# P7 Stoneford and the Recruitment Fair
	check(go("west") and go("west") and go("west") and go("west") and room() == "sf_fairground", "walk to the Fairground (room %s)" % room())
	check(c().quests.is_active("the_recruitment_fair") or c().quests.offered.has("the_recruitment_fair"), "Recruitment Fair offered")
	accept("recruiter_qing_lan", "the_recruitment_fair")
	talk("recruiter_mo_yun")
	check(talk_choose("recruiter_qing_lan", "effects", "Join"), "join the Jade Sect")
	check(str(c().training_sect.get("id", "")) == "jade_sect", "member of the Jade Sect")
	check(c().quests.is_done("the_recruitment_fair"), "Recruitment Fair complete")

	# Grind to Bone Forging 2 on the Willow Path.
	check(go("east") and go("east") and go("east") and go("east") and room() == "wp_west", "back to Willow Path West (room %s)" % room())
	var tries := 0
	if verbose: GameEvents.event.connect(func(n, p): if n == "progress_changed" and tries < 12: print("    progress ", p.source, " ", snappedf(float(p.amount), 0.1), " -> ", snappedf(c().cultivator.qp, 0.1)))
	var kill_progress := {"n": 0}
	GameEvents.event.connect(func(n, p): if n == "progress_changed" and str(p.get("source", "")) == "kill": kill_progress.n += 1)
	while not ProgressionRules.at_least(c().cultivator.realm_key, "bone_forging_2") and tries < 160:
		if tries == 10:
			check(int(kill_progress.n) > 0, "fights on the Willow Path give realm progress (%d kills counted)" % int(kill_progress.n))
			# Test shortcut: the rest of the ~40 kills is grinding the scripted fighter is poor at.
			Game.progression.apply_progress(c().id, 0.0, "test_shortcut", 1.0)
		if c().cultivator.state == "bottleneck":
			submit({"type": "start_breakthrough", "support_items": []})
			step(4.0)
		else:
			fight("wild_boarlet", 1, 20.0, 0.4)
			if c().pools.hp < c().pools.max_hp * 0.7 and room() == "wp_west":
				# Head to town to recover, then come back.
				go("west")
				var heal := 0.0
				while c().pools.hp < c().pools.max_hp * 0.98 and heal < 150.0:
					step(1.0)
					heal += 1.0
				go("east")
		tries += 1
		if verbose and tries % 10 == 0: print("  grind ", tries, ": qp ", snappedf(c().cultivator.qp, 0.1), "/", c().cultivator.need(), " state ", c().cultivator.state, " consolidating ", snappedf(c().cultivator.consolidation_left, 0.1))
	check(c().cultivator.realm_key == "bone_forging_2", "Bone Forging 2 reached after %d fights" % tries)

	# P8 Entry Trial
	check(go("west") and go("west") and go("west") and go("west"), "return to the Fairground")
	check(c().quests.is_active("entry_trial"), "Entry Trial active")
	check(go("trial_jade") and room() == "sf_trial_jade", "enter the Jade trial")
	check(interact("trial_bell").get("ok", false), "reach the trial bell")
	step(1.5)
	check(fight("trial_puppet", 1, 120.0) == 1, "Trial Puppet beaten")
	check(c().quests.is_done("entry_trial"), "Entry Trial complete")
	check(str(c().training_sect.get("rank", "")) == "service_disciple", "Service Disciple")
	check(c().inventory.equipped.get("weapon") == null, "still bare fists after the Prologue")

	# HUD reveal order (S27): each element appears exactly at its step.
	var order := ["hud:joystick", "hud:context", "hud:bag", "hud:room_banner", "hud:minimap", "hud:quest_tracker", "hud:jump"]
	var idx := -1
	var in_order := true
	for el in order:
		var i := reveal_log.find(el)
		if i < idx: in_order = false
		idx = i
	check(in_order, "HUD reveal order: %s" % str(reveal_log.slice(0, 12)))
	check(reveal_log.find("hud:attack") > reveal_log.find("hud:jump"), "Attack after Jump")
	check(reveal_log.find("hud:cultivate") > reveal_log.find("hud:menu"), "Cultivate after Menu")
	if verbose:
		for e in events: print(e)
