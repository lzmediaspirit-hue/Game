extends "res://tests/prologue_run.gd"
## story_scenes (decision 39, docs/redesign/story_staging.md): the staged scenes of data/scenes.json and the
## SceneDirector that plays them in the rooms on the height grid. tests/topdown_tutorial.gd plays every scene of the
## tutorial walk to its end, the walk's own deeds doing what the hand-offs ask; this suite holds:
##   1. every scene's script validates (SceneRules.problems): its room on the grid, its people, props and targets real,
##      every walk with a way on foot, known steps, poses, emotes, sounds, effects, doors and labels, events of the
##      contract, and its staged time within 10-40 s;
##   2. the opening in the character's own view (a live TopdownWorld and a drawn director): it begins at waking, Aunt
##      Ping's figure walks, the cut holds the simulation still and gives it back at the hand-off, a checkpoint is
##      kept on the character; in Home Lane a boat sails past on the river (a prop brought on) and the people walk;
##   3. save-safe: a scene cut short by quitting resumes after a reload at its last checkpoint, its people where the
##      script had put them; played out, it is seen and never plays again;
##   4. a hold skips a cut to its next hand-off, and what the skipped part asked for still happens (Granny's graze);
##   5. Reduce motion: the camera cuts instead of panning; a fight breaks a cut into a live part, the controls back;
##   6. decision 42: a talk closes once a quest is taken or handed in, even with another to give, and a talk that itself
##      finishes a quest closes at its last line; a scene the quest starts plays once it is closed.
## Run headless:  godot --headless --path . res://tests/story_scenes.tscn [-- --verbose]

func _main() -> void:
	_every_scene_validates()
	start_new("saves/")
	_the_opening_in_view()
	_resumes_after_a_reload()
	_reduce_motion_and_fights()
	_skip_keeps_the_checkpoints()
	_talks_close()
	if is_instance_valid(scene_director): scene_director.free()
	Game.pause(false)
	end_suite()

# ------------------------------------------------------------------ 1
func _every_scene_validates() -> void:
	var rows := ContentDB.all("scenes")
	check(rows.size() >= 12, "the story is staged: %d scenes" % rows.size())
	var total := 0.0
	var each := PackedStringArray()
	for row in rows:
		var p := SceneRules.problems(row)
		check(p.is_empty(), "%s validates (%s)" % [row.id, str(p.slice(0, 4))])
		var grid := TopdownRoom.load_room(str(row.room))
		var s := SceneRules.length(row, grid.merge_def(ContentDB.room(str(row.room))), grid)
		total += s
		each.append("%s %.1f" % [row.id, s])
	check(rows.any(func(r): return (r.steps as Array).any(func(s): return str(s.do) == "handoff")), "the scenes hand the controls to the player")
	# Every hand-off's prompt plate is whole on the screen, even by a control at its right edge (the prototype's QA: the
	# Bag's "Open your Bag: put Herbal Tea in Quick-use" ran off it).
	var cut_off: Array = []
	for row in rows:
		for s in row.steps:
			if str(s.do) != "handoff": continue
			for x in [1120.0, 1270.0, 10.0]:
				var px := SceneStage.prompt_x(str(s.prompt), x)
				var half := UiKit.text_width(str(s.prompt), 18, true) * 0.5 + 10.0
				if px - half < 0.0 or px + half > 1280.0: cut_off.append("%s: %s" % [row.id, s.prompt])
	check(cut_off.is_empty(), "every hand-off's prompt stands whole on the screen, by a control at either edge too (%s)" % str(cut_off.slice(0, 3)))
	# A hand-off that ends on an item used (Granny's tea) keeps the controls and the HUD up, and waits before the next
	# line, so the item's effect shows: its number over the head and its line in the log (the prototype's QA, and the
	# user's "tea effects not shown").
	var hidden_use: Array = []
	for row in rows:
		var steps: Array = row.steps
		for i in steps.size():
			var s: Dictionary = steps[i]
			if str(s.do) != "handoff" or not (s.get("until", []) as Array).any(func(u): return str(u.get("event", "")) == "item_used"): continue
			var next: Dictionary = steps[i + 1] if i + 1 < steps.size() else {}
			if str(s.get("then", "cut")) != "live" or (not next.is_empty() and not (str(next.do) == "wait" and float(next.get("s", 0.0)) >= 1.0)):
				hidden_use.append("%s: %s" % [row.id, s.prompt])
	check(hidden_use.is_empty(), "a hand-off that ends on an item used keeps the HUD up and lets its effect show (%s)" % str(hidden_use))
	# A balloon out of a cut keeps off the HUD's panels: aside of the player panel, or below it (the prototype's QA:
	# Washer Mei's thanks covered the HP bar).
	var panel := Rect2(16, 16, 360, 104)
	var tracker := Rect2(14, 172, 342, 76)
	var inside := Rect2(24, 24, 1232, 672)
	var moved := SceneStage.clear_of_hud(Rect2(30, 60, 300, 60), [panel, tracker], inside)
	var crowded := SceneStage.clear_of_hud(Rect2(30, 60, 1200, 60), [panel, tracker], inside)
	check(not moved.intersects(panel) and not moved.intersects(tracker) and inside.encloses(moved) and not crowded.intersects(panel),
		"a speech balloon out of a cut moves clear of the HUD's panels (%s; a wide one %s)" % [str(moved), str(crowded)])
	print("staged (s): %s; %d scenes, %.0f s in all" % [", ".join(each), rows.size(), total])

# ------------------------------------------------------------------ 2
func _director(view: TopdownWorld = null) -> SceneDirector:
	if is_instance_valid(scene_director): scene_director.free()
	scene_director = SceneDirector.new()
	scene_director.headless = view == null
	scene_director.world = view
	scene_director.pages_override = false
	scene_director.fight_override = false
	add_child(scene_director)
	scene_director.set_process(false)
	return scene_director

func _live_view() -> TopdownWorld:
	var w := TopdownWorld.new()
	w.live = true
	w.sim_frozen = true
	add_child(w)
	return w

## Run the director (and the view's frames) for `s` seconds.
func _run(s: float, w: TopdownWorld = null) -> void:
	var t := 0.0
	while t < s:
		scene_director.advance(0.05)
		if w: w._process(0.05)
		t += 0.05

func _to_step(kind: String, limit := 60.0) -> bool:
	var t := 0.0
	while scene_director.run != null and t < limit:
		var st: Dictionary = scene_director.run.row.steps[scene_director.run.i] if scene_director.run.i < (scene_director.run.row.steps as Array).size() else {}
		if str(st.get("do", "")) == kind and scene_director.run.begun: return true
		scene_director.advance(0.05)
		t += 0.05
	return false

func _the_opening_in_view() -> void:
	var w := _live_view()
	var d := _director(w)
	d.poll()
	check(d.run != null and str(d.run.id) == "opening_dawn", "the opening begins as the character wakes in the Fisher's Hut (%s)" % str(d.run.id if d.run else "none"))
	check(d.in_cut() and Game.paused, "the opening's cut holds the simulation still")
	var ping: Dictionary = d.run.actors.get("ping", {})
	check(is_instance_valid(ping.get("fig")) and is_instance_valid(ping.get("label")) and ping.fig == w.figures.get("npc_aunt_ping") and ping.fig.staged,
		"Aunt Ping's own figure and label play her part, the figure staged (the scene turns her and says what she does)")
	var home: Vector2 = ping.fig.position
	check(_to_step("handoff"), "the opening reaches its first hand-off")
	check(ping.fig.position != home and ping.pos.distance_to(SceneRules.point([5, 5])) < 1.0, "Aunt Ping walked across the hut (figure at %s)" % str(ping.fig.position))
	check(not d.in_cut() and not Game.paused and str(d.run.mode) == "hand", "at a hand-off the simulation runs and the controls are the player's")
	var mark := int(d.run.i)
	check(int(c().quests.scenes.get("opening_dawn", {}).get("at", -1)) == mark, "the hand-off is a checkpoint kept on the character (%s)" % str(c().quests.scenes.get("opening_dawn", {})))
	check(_to_step("say") and d.in_cut(), "the Bag's hand-off ends by itself in time, and the cut goes on")
	w.free()
	if st != null: Game.bind_movement(Game.active_id, st)
	scene_director.world = null
	scene_director.headless = true

# ------------------------------------------------------------------ 3
func _resumes_after_a_reload() -> void:
	check(_to_step("handoff") and str(scene_director.run.row.steps[scene_director.run.i].prompt).contains("door"), "the opening's last hand-off: walk to the door")
	var at := int(scene_director.run.i)
	Game.pause(false)
	Game.save_all()
	scene_director.free()
	Game.boot()
	Game.autosave_enabled = false
	check(submit({"type": "enter_character", "slot": 1}).ok and submit({"type": "enter_world"}).ok, "the character comes back from its save")
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	var d := _director()
	d.poll()
	check(d.run != null and str(d.run.id) == "opening_dawn" and int(d.run.i) == at and str(d.run.mode) == "hand",
		"the opening resumes at its last checkpoint after a reload (step %s of %d)" % [str(d.run.i if d.run else -1), at])
	check(d.run != null and (d.run.actors.ping.pos as Vector2).distance_to(SceneRules.point([5, 5])) < 1.0, "Aunt Ping stands where the script had put her")
	check(go("exit") and room() == "lf_village", "out through the door")
	d.advance(0.05)
	check(d.finished.any(func(f): return str(f.scene) == "opening_dawn" and not f.skipped), "walking out ends the opening, played out (%s)" % str(d.finished))
	check(c().quests.scenes.get("opening_dawn", {}).get("done", false), "the opening is seen")
	settle_scenes()
	check(d.finished.any(func(f): return str(f.scene) == "river_dawn" and not f.skipped), "Home Lane at dawn plays headless to its end (%s)" % str(d.finished))
	var boat := d.logged.filter(func(e): return str(e.scene) == "river_dawn" and str(e.do) == "move")
	check(boat.size() >= 3, "a boat sails past and the villagers walk (%d walks)" % boat.size())
	check(go("hut_door") and room() == "lf_fishers_hut", "back into the hut")
	d.poll()
	check(d.run == null, "a scene seen never plays again")
	check(go("exit") and room() == "lf_village", "and out again")

# ------------------------------------------------------------------ 4
func _skip_keeps_the_checkpoints() -> void:
	check(go("granny_door") and room() == "lf_granny_liu_hut", "into Granny Liu's hut")
	var d: SceneDirector = scene_director
	accept("granny_liu", "grannys_remedy")
	d.poll()
	check(d.run != null and str(d.run.id) == "granny_jar" and d.in_cut(), "taking Granny's Remedy stages the falling jar")
	var hp: float = c().pools.hp
	d.input(_press(true))
	d.advance(0.5)
	check(d.in_cut(), "a short hold does not skip")
	d.advance(0.4)
	check(d.run != null and str(d.run.mode) == "hand" and str(d.run.row.steps[d.run.i].do) == "handoff", "a hold skips the cut to its next hand-off")
	d.input(_press(false))
	check(c().pools.hp < hp - 1.0 and c().pools.hp >= 0.4 * c().pools.max_hp, "the graze the skipped cut asked for still lands (HP %d -> %d)" % [int(hp), int(c().pools.hp)])
	check(submit({"type": "set_quick_use", "item": "herbal_tea"}).get("ok", false), "the tea into Quick-use")
	d.advance(0.05)
	check(d.run != null and str(d.run.row.steps[d.run.i].get("at", "")) == "hud:quick:0", "the next hand-off points at the first Quick-use slot")
	var q := submit({"type": "use_quick"})
	if not q.get("ok", false) and q.get("reason", "") == "confirm": submit({"type": "use_item", "index": c().inventory.first_index("herbal_tea"), "confirm": true})
	settle_scenes()
	check(d.finished.any(func(f): return str(f.scene) == "granny_jar"), "Granny's scene ends once the tea is drunk (%s)" % str(d.finished))

func _press(down: bool) -> InputEventMouseButton:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = down
	return e

# ------------------------------------------------------------------ 5
func _reduce_motion_and_fights() -> void:
	var d: SceneDirector = scene_director
	d.reduce_override = true
	hand_in("lu_boatman", "a_quiet_river")
	d.poll()
	check(d.run != null and str(d.run.id) == "four_errands", "Lu's four errands take the stage")
	var t := 0.0
	while d.run != null and not d.logged.any(func(e): return str(e.scene) == "four_errands" and str(e.do) == "camera") and t < 20.0:
		d.advance(0.05)
		t += 0.05
	check(d.run != null and str(d.run.cam.get("to", "")) == "guo", "the errands' camera turns to Uncle Guo")
	check(d.run != null and float(d.run.cam.s) == 0.0 and d.cam_now().distance_to(d.where("guo")) < 1.0, "under Reduce motion the camera cuts to its target, no pan")
	d.fight_override = true
	d.advance(0.05)
	check(d.run != null and str(d.run.mode) == "live" and not Game.paused, "a fight breaks into a cut: the scene goes on live, the controls back")
	d.fight_override = false
	d.reduce_override = null
	settle_scenes()
	check(d.run == null, "the errands play out")

# ------------------------------------------------------------------ 6
## Decision 42 (the prototype APK's feedback: "conversation with NPC should close after getting / completing the
## quest"), in the top-down game on the real dialogue page: taking a quest closes the talk even when the person has a
## second to give (talking again offers it), and so does handing one in while another waits; a scene the quest starts
## plays once the talk is closed (Uncle Guo's Fists First); and a talk that itself finishes a quest (Evening on the
## River's last step is talking to Lu) closes at its last line's tap, with only Farewell or a service left to choose.
func _talks_close() -> void:
	var d: SceneDirector = scene_director
	settle_scenes()
	if room() != "lf_village": go("exit")
	check(room() == "lf_village", "back in the village (%s)" % room())
	# Aunt Ping in the lane with two quests to give: her ladle, and her broth.
	c().quests.done["the_runaway_kite"] = 1
	c().quests.offered["aunt_pings_broth"] = true
	Game.quest.refresh_offers()
	var first: Dictionary = interact(str(npc_object("aunt_ping").get("id", ""))).get("dialogue", {})
	var offered: Array = (first.get("choices", []) as Array).filter(func(ch): return ch.has("accept")).map(func(ch): return str(ch.accept))
	check(offered.has("the_lost_ladle") and offered.has("aunt_pings_broth"), "Aunt Ping has two quests to give (%s)" % str(offered))
	check(_choose_on_page("aunt_ping", "accept", "the_lost_ladle") and c().quests.offered.has("aunt_pings_broth"),
		"decision 42: taking one of her two quests closes the talk; the other waits for the next talk")
	# The ladle ready to hand in, her broth still to give: handing it in closes the talk too.
	var ladle: Dictionary = Game.quest.quest_def(c(), "the_lost_ladle")
	for g in QuestAuthority.handover(ladle): Game.inventory.apply_add(c().id, str(g.item), int(g.count), "test")
	var st_l: Dictionary = c().quests.active.get("the_lost_ladle", {})
	st_l.progress = (ladle.get("objectives", []) as Array).map(func(o): return int(o.get("count", 1)))
	st_l.state = "ready"
	check(_choose_on_page("aunt_ping", "hand_in", "the_lost_ladle") and c().quests.offered.has("aunt_pings_broth"),
		"decision 42: handing a quest in closes the talk though she has another to give")
	check(_choose_on_page("aunt_ping", "accept", "aunt_pings_broth"), "talking to her again offers the other, and taking it closes the talk")
	# A scene the quest starts plays once the talk is closed.
	var seen_before: bool = c().quests.scenes.get("guo_fists", {}).get("done", false)
	check(_choose_on_page("uncle_guo", "accept", "fists_first"), "Fists First taken from Uncle Guo on the page, and the talk closes")
	d.poll()
	check(seen_before or (d.run != null and str(d.run.id) == "guo_fists"), "the scene Fists First starts plays once the talk is closed (%s)" % str(d.run.id if d.run else "none"))
	settle_scenes()
	# A talk that itself finishes a quest: Evening on the River's steps are talking to Aunt Ping and then to Lu.
	c().quests.offered["evening_on_the_river"] = true
	check(Game.quest.accept(c(), "evening_on_the_river").get("ok", false), "Evening on the River under way")
	interact(str(npc_object("aunt_ping").get("id", "")))
	var lu: Dictionary = interact(str(npc_object("lu_boatman").get("id", ""))).get("dialogue", {})
	var on := _page(lu)
	var light: bool = on.page.ends_on_tap()
	if not on.closed: on.page.on_action("advance", null)
	check(c().quests.is_done("evening_on_the_river") and lu.get("quest_moved", false) and light and on.closed,
		"decision 42: the talk that finished Evening on the River closes at its last line's tap (quest_moved %s, choices %s)"
		% [str(lu.get("quest_moved", false)), str((lu.get("choices", []) as Array).map(func(ch): return str(ch.get("text", ""))))])
	on.page.queue_free()
	settle_scenes()
