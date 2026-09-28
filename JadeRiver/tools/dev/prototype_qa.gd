extends Node
## The prototype's QA playthrough (docs/redesign/prototype_qa.md): a new player on a phone-sized screen (1280x720, the
## HUD's touch controls) plays from the title: new game, the creator, the staged opening, the whole tutorial, the sect
## choice, chapter 2's rooms, and on to the prototype's gate. Everything goes through the game's own input: touches on
## the title, the creator, the pages and the HUD (the stick, Attack, the context, Jump, Dodge, Quick-use, the Bag, the
## tracker's go button) and a thumb's taps through the staged scenes' lines. Where the driver cannot find its way on
## foot (a running jump across a gap, which its path search does not plan) it says so in its log and puts the body
## there (a driver's limit, not the game's). A screenshot at every step, and a log (qa_log.json) of what each shows.
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/prototype_qa.tscn \
##     -- --out=<dir> [--sect=jade|cloud] [--keep=<dir>] [--keep-at=<step>] [--from=<dir> --start=<step>] [--until=<step>]
## --keep saves the game into <dir> before the step --keep-at names (by default the sect's choice, both recruiters met);
## --from resumes a kept game (Continue on the title) and --start runs on from that step (the second sect's run:
## --from=<kept> --start=sect_choice --sect=cloud). On saves of its own, never the player's or a test's.

const SAVES := "user://prototype_qa_saves/"
const STICK := Vector2(240, 540)
var main
var out := "user://prototype_qa/"
var sect := "jade"
var keep_dir := ""
var from_dir := ""
var n := 0
var notes: Array = []
var finds: Array = []
var t0 := 0

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--out="): out = str(a).trim_prefix("--out=")
		if str(a).begins_with("--sect="): sect = str(a).trim_prefix("--sect=")
		if str(a).begins_with("--keep="): keep_dir = str(a).trim_prefix("--keep=")
		if str(a).begins_with("--from="): from_dir = str(a).trim_prefix("--from=")
	if not out.ends_with("/"): out += "/"
	DirAccess.make_dir_recursive_absolute(out)
	t0 = Time.get_ticks_msec()
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await frames(2)
	DirAccess.make_dir_recursive_absolute(SAVES)
	for f in DirAccess.get_files_at(SAVES): DirAccess.remove_absolute(SAVES + f)
	if from_dir != "":
		for f in DirAccess.get_files_at(from_dir): DirAccess.copy_absolute(from_dir.path_join(f), SAVES + f)
	Saves.use_folder(SAVES)
	Game.boot()
	GameEvents.event.connect(_on_event)
	for i in 3600:   # the pages' scripts warm on their thread from the title, as a player waits there
		if main.pages_warm(): break
		await get_tree().process_frame
	main.show_title()
	await frames(20)
	var until := ""
	var start := "opening"
	var keep_at := "sect_choice"
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--until="): until = str(a).trim_prefix("--until=")
		if str(a).begins_with("--start="): start = str(a).trim_prefix("--start=")
		if str(a).begins_with("--keep-at="): keep_at = str(a).trim_prefix("--keep-at=")
	if from_dir != "": await resume()
	var on := false
	for step in STEPS:
		if step == start: on = true
		if not on: continue
		if step == keep_at and keep_dir != "": keep()
		say("step %s" % step)
		await call(step)
		if step == until: break
	finish()

## The walk's steps in order; --start=<step> with --from=<saves> resumes at one, --keep-at=<step> keeps the saves there.
const STEPS := ["opening", "p_quiet_river", "p_fists", "p_race", "p_kite", "p_ma", "p_granny", "p_crabs", "p_night", "p_willow",
	"fair", "sect_choice", "chapter2", "to_the_gate"]

## The game saved as it stands, into keep_dir (a checkpoint the next run starts from).
func keep() -> void:
	Game.save_all()
	DirAccess.make_dir_recursive_absolute(keep_dir)
	for f in DirAccess.get_files_at(SAVES): DirAccess.copy_absolute(SAVES + f, keep_dir.path_join(f))
	say("kept the game in %s" % keep_dir)

func finish() -> void:
	stick(Vector2.ZERO)
	var f := FileAccess.open(out + "qa_log.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"shots": notes, "finds": finds, "minutes": (Time.get_ticks_msec() - t0) / 60000.0}, "  "))
	f.close()
	print("QA done: %d shots, %d finds, %.1f min" % [n, finds.size(), (Time.get_ticks_msec() - t0) / 60000.0])
	get_tree().quit()

# ------------------------------------------------------------------ record
## The game's own clock (its physics ticks), so a slow machine's run waits as long in play as a fast one's.
func now_ms() -> int:
	return int(Engine.get_physics_frames() * 1000 / maxi(1, Engine.physics_ticks_per_second))

func frames(k: int) -> void:
	for i in k: await get_tree().process_frame

func wait_s(s: float) -> void:
	var start := now_ms()
	while now_ms() - start < s * 1000.0: await get_tree().process_frame

func shot(name: String, note := "") -> void:
	await RenderingServer.frame_post_draw
	n += 1
	var file := "%03d_%s.png" % [n, name]
	get_tree().root.get_texture().get_image().save_png(out + file)
	var under := _labels_under_hud()
	notes.append({"shot": file, "room": room(), "note": note, "tracker": _tracker_text(), "labels_under_hud": under})
	print("QA shot %s (%s) %s" % [file, room(), note])
	if not under.is_empty(): print("QA labels under the HUD in %s: %s" % [file, ", ".join(under)])

## The world's labels as placed this frame that still sit under a HUD control or panel (more than a sliver), by id.
func _labels_under_hud() -> Array:
	var out: Array = []
	if not is_instance_valid(main.world) or not main.world is TopdownWorld or not is_instance_valid(main.hud) or main.hud.scene_lock: return out
	var laid: Dictionary = main.world.layout_labels()
	var huds: Array = main.hud.obstacle_rects()
	for it in laid.get("items", []):
		var r := Rect2((it.rect as Rect2).position + laid.offsets.get(it.id, Vector2.ZERO), (it.rect as Rect2).size)
		for o in huds:
			var i := r.intersection(o)
			if i.size.x > 4.0 and i.size.y > 4.0:
				out.append("%s %s under %s" % [str(it.id), str(r), str(o)])
				break
	return out

## Something a player would hit, noted with the shot that shows it.
func find(what: String, name := "find") -> void:
	await shot(name, "FIND: " + what)
	finds.append({"shot": "%03d_%s.png" % [n, name], "what": what, "room": room()})
	print("QA FIND: ", what)

func say(s: String) -> void:
	print("QA: ", s)

func _tracker_text() -> String:
	var c = Game.active()
	if c == null or not Game.in_world: return ""
	var parts: Array = []
	for e in Game.quest.tracker(c):
		parts.append("%s [%s] %s" % [str(e.name), str(e.get("target_room", "")), " / ".join((e.lines as Array).map(func(l): return str(l.text)))])
	return " | ".join(parts)

func room() -> String:
	return Game.room_rt.room_id if Game.room_rt != null and Game.in_world else main.screen if main else ""

func c():
	return Game.active()

# ------------------------------------------------------------------ touches
func touch(p: Vector2, down: bool, idx := 0) -> void:
	var e := InputEventScreenTouch.new()
	e.index = idx
	e.position = p
	e.pressed = down
	Input.parse_input_event(e)

func drag_to(p: Vector2, idx: int) -> void:
	var e := InputEventScreenDrag.new()
	e.index = idx
	e.position = p
	Input.parse_input_event(e)

## A finger's tap: down, two frames, up (index 0 also reaches the pages as a mouse click, as on a phone).
func tap(p: Vector2, idx := 0, hold := 2) -> void:
	touch(p, true, idx)
	await frames(hold)
	touch(p, false, idx)
	await frames(3)

var stick_down := false
## The thumb on the joystick: pushed along `dir` (zero lets go).
func stick(dir: Vector2) -> void:
	if dir.length() < 0.01:
		if stick_down:
			touch(STICK, false, 1)
			stick_down = false
		return
	# The HUD lets go of every touch when a page or a cut takes the screen: the thumb goes down again.
	if stick_down and is_instance_valid(main.hud) and int(main.hud.joystick_id) != 1:
		touch(STICK, false, 1)
		stick_down = false
	if not stick_down:
		touch(STICK, true, 1)
		stick_down = true
	drag_to(STICK + dir.normalized() * 70.0, 1)

func hud():
	return main.hud

## A HUD control's centre by its role, INF when it is not drawn.
func role(r: String) -> Vector2:
	if not is_instance_valid(main.hud): return Vector2.INF
	for tg in main.hud.hit_targets():
		if str(tg.role) == r: return tg.center
	return Vector2.INF

func tap_role(r: String) -> bool:
	var p := role(r)
	if p == Vector2.INF: return false
	await tap(p, 2)
	return true

func player():
	return main.world.player if is_instance_valid(main.world) and main.world is TopdownWorld else null

func me() -> Vector2:
	return player().motor.pos if player() != null else Vector2.ZERO

func top_page() -> Page:
	return main.top_page()

func page_open(id: String) -> Page:
	for p in main.pages:
		if p.page_id == id: return p
	return null

## Tap a page's region by id (and data), as a finger on it.
func tap_region(p: Page, id: String, data = null) -> bool:
	if p == null: return false
	for r in p._regions:
		if str(r.id) == id and (data == null or r.data == data):
			await tap((r.rect as Rect2).get_center())
			return true
	return false

func close_pages() -> void:
	for i in 6:
		var p := top_page()
		if p == null: return
		if not await tap_region(p, "_close"): p.close()
		await frames(6)

# ------------------------------------------------------------------ the stage
## While a staged scene's cut holds the stage, a thumb taps through its lines (about a second a line); it stops at a
## hand-off (the player's turn), a live part, or the scene's end.
func settle(limit := 120.0) -> void:
	var start := now_ms()
	var last_tap := 0
	var staged := false
	while (now_ms() - start) < limit * 1000.0:
		if main.scenes == null: return
		var r = main.scenes.run
		if r != null: staged = true
		if (r == null and not main.scenes.busy()) or (r != null and str(r.mode) in ["hand", "live"]):
			if staged: await wait_s(1.0)   # the HUD and the names fade back in over the stage
			return
		if now_ms() - last_tap > 1100 and top_page() == null:
			last_tap = now_ms()
			await tap(Vector2(640, 380))
		elif top_page() != null and str(top_page().page_id) == "dialogue":
			await dialogue_through()
		else:
			await frames(1)
	say("a scene still held the stage after %d s" % int(limit))

func scene_step() -> String:
	var r = main.scenes.run if main.scenes != null else null
	if r == null: return ""
	return "%s:%s:%s" % [str(r.id), str(r.mode), str(r.row.steps[r.i].get("prompt", r.row.steps[r.i].get("do", ""))) if int(r.i) < (r.row.steps as Array).size() else "end"]

# ------------------------------------------------------------------ walking
## Walk on foot to a point of the room (the grid's own path: walking, stairs, drops, a hop a level up, Jump pressed
## where it climbs), as a thumb on the stick. False, with a note, when the way does not come (a gap to jump at a run,
## a wall) within `limit` seconds.
func walk_to(goal: Vector2, near := 16.0, limit := 30.0, place_if_stuck := true) -> bool:
	if main.scenes != null and main.scenes.in_cut(): await settle()   # a cut holds the body still
	if player() == null: return false
	var grid: TopdownRoom = main.world.room
	var can_jump := Game.is_revealed("hud:jump")   # no hop before the Jump button is the player's (The Runaway Kite)
	var rid := room()
	var start := now_ms()
	var path: Array = []
	var goal_cell := Vector2i(-999, -999)
	var hop_ms := 0
	var last := me()
	var still_ms := now_ms()
	var spot := grid.nearest_standable(goal)
	while now_ms() - start < limit * 1000.0:
		if room() != rid or player() == null:
			stick(Vector2.ZERO)
			return true
		var here := me()
		if here.distance_to(spot) <= near and absf(player().motor.z - grid.floor_at(spot)) <= 8.0: break
		if main.scenes != null and main.scenes.in_cut():   # a scene took the stage mid-walk: watch it, then go on
			stick(Vector2.ZERO)
			await settle()
			still_ms = now_ms()
			path = []
			continue
		if is_instance_valid(main.hud) and main.hud.moment_lock:   # a moment's card holds the controls a moment
			await frames(2)
			still_ms = now_ms()
			continue
		if top_page() != null:   # a page the world opened (a moment's card, the equip prompt's Bag): read it and close it
			await shot("page_during_walk", "a page opened while walking: %s" % str(top_page().page_id))
			await close_pages()
		var cell := TopdownRoom.cell_of(here)
		var tc := TopdownRoom.cell_of(spot)
		if tc != goal_cell or path.is_empty() or cell.distance_to(path[0]) > 1.5:
			goal_cell = tc
			path = grid.find_path(cell, tc, can_jump)
			# The grid's search asks for a hop up a long stair's steps; the body walks up them without one.
			if path.is_empty() and not can_jump: path = grid.find_path(cell, tc, true)
		while not path.is_empty() and cell == path[0]: path.pop_front()
		var aim := spot
		if not path.is_empty():
			aim = (Vector2(path[0]) + Vector2(0.5, 0.5)) * TopdownRoom.TILE
			if grid.cell_floor(path[0]) > player().motor.z + 8.0 and now_ms() - hop_ms > 500 and player().motor.grounded:
				hop_ms = now_ms()
				var jp := role("jump")
				if jp != Vector2.INF:
					touch(jp, true, 2)
					await frames(2)
					touch(jp, false, 2)
		stick(aim - here)
		await frames(1)
		if here.distance_to(last) > 3.0:
			last = here
			still_ms = now_ms()
		elif now_ms() - still_ms > 1500 and now_ms() - still_ms < 1600:
			path = []   # stuck a moment: find the way again, and hop
			var jp2 := role("jump")
			if jp2 != Vector2.INF:
				touch(jp2, true, 2)
				await frames(2)
				touch(jp2, false, 2)
		elif now_ms() - still_ms > 4000:
			break
	stick(Vector2.ZERO)
	await frames(2)
	if me().distance_to(spot) <= near + 8.0: return true
	var cell2 := TopdownRoom.cell_of(me())
	say("walk to %s (cell %s, floor %.0f) in %s did not arrive: at %s (cell %s, z %.0f), path %s" % [str(spot), str(TopdownRoom.cell_of(spot)), grid.floor_at(spot),
		rid, str(me()), str(cell2), player().motor.z, str(grid.find_path(cell2, TopdownRoom.cell_of(spot), can_jump).slice(0, 6))])
	if place_if_stuck and player() != null:
		player().motor.place(spot)
		main.world._settle_camera()
		await frames(4)
	return false

## Turn to face a point, as a thumb nudges the stick toward it.
func face(at: Vector2) -> void:
	var d := at - me()
	if d.length() < 1.0: return
	stick(d)
	await frames(3)
	stick(Vector2.ZERO)
	await frames(3)

## Hit a training stump, a dummy or a jar `times` times, as a thumb taps Attack facing it.
func hit(id: String, times: int) -> void:
	var o: Dictionary = Game.room_rt.object_def(id)
	if o.is_empty(): return
	await stand_by(o)
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	for k in times:
		await face(at)
		await tap(main.hud.attack_center, 5, 2)
		await frames(24)

## Walk out through a way: to it, then the stick along its direction until the next room is in.
func go(portal: String, limit := 30.0) -> bool:
	if Game.room_rt == null: return false
	var p: Dictionary = Game.room_rt.portal_def(portal)
	if p.is_empty():
		say("no way %s in %s" % [portal, room()])
		return false
	var rid := room()
	var at := Vector2(float(p.at[0]), float(p.at[1]))
	var dir := Vector2(float(p.dir[0]), float(p.dir[1])) if p.has("dir") else Vector2.DOWN
	await walk_to(at - dir * 20.0, 14.0, limit)
	for i in 150:
		if room() != rid: break
		stick(dir)
		await frames(1)
	stick(Vector2.ZERO)
	await frames(20)
	if room() == rid: say("the way %s in %s did not take me (state %s)" % [portal, rid, str(Game.world.portal_state(c(), p))])
	return room() != rid

## To another room on foot, way by way along the route the World authority finds.
func travel(target: String) -> bool:
	for hop in 12:
		if room() == target: return true
		var r: Array = Game.world.route(c(), room(), target)
		if r.is_empty():
			say("no route from %s to %s" % [room(), target])
			return false
		if not await go(str(r[0].portal)): return false
		await settle()
	return room() == target

func npc_object(npc: String) -> Dictionary:
	for o in Game.room_rt.def.get("objects", []):
		if str(o.get("type", "")) == "npc" and str(o.get("npc", "")) == npc and Game.world.object_visible(c(), o): return o
	return {}

## Stand beside a thing of the room (a person, a pickup, a shrine).
func stand_by(o: Dictionary) -> void:
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	var room: TopdownRoom = main.world.room
	# The spot on the thing's side toward the body, as a player walks up to it; the nearest spot to it when that one is
	# out of its reach (a kite on a roof: `radius` 70).
	var spot: Vector2 = room.spot_near(at, float(o.get("alt", 0.0)), me())
	if spot.distance_to(at) > float(o.get("radius", 110)) - 12.0: spot = room.spot_near(at, float(o.get("alt", 0.0)), at + (me() - at).limit_length(8.0))
	await walk_to(spot, 10.0)

## Use what the context offers where the body stands: the context's own slot in a fight, else Attack at rest.
func use_context(only_type := "") -> bool:
	await frames(3)
	if main.world.context.is_empty(): return false
	# The context can change under the thumb (a drop picked up by walking over it leaves the herb beside it).
	if only_type != "" and str(main.world.context.get("type", "")) != only_type and not main.world.context.has("uid"): return false
	var slot := role("context")
	await tap(slot if slot != Vector2.INF else main.hud.attack_center)
	await frames(8)
	return true

func interact(id: String) -> bool:
	var o: Dictionary = Game.room_rt.object_def(id)
	if o.is_empty():
		say("no %s in %s" % [id, room()])
		return false
	await stand_by(o)
	await frames(4)
	var ctx: Dictionary = main.world.context
	if str(ctx.get("object", "")) != id:
		say("the context offers %s, not %s" % [str(ctx), id])
	return await use_context()

# ------------------------------------------------------------------ talking
## Walk to a person and talk (the context button), and read the talk through: its lines tapped on, and the choice
## that has `key` (accept, hand_in, effects) = `value` tapped when it shows. True when that choice was made.
func talk(npc: String, key := "", value := "", name := "") -> bool:
	var o := npc_object(npc)
	if o.is_empty():
		say("no %s in %s" % [npc, room()])
		return false
	await stand_by(o)
	await frames(6)
	if not await use_context():
		say("nothing offered beside %s" % npc)
		return false
	for i in 30:
		if page_open("dialogue") != null: break
		await frames(2)
	if page_open("dialogue") == null:
		say("no talk opened with %s (context %s)" % [npc, str(main.world.context)])
		return false
	if name != "": await shot(name, "talking to %s" % npc)
	return await dialogue_through(key, value)

func dialogue_through(key := "", value := "") -> bool:
	var chosen := false
	for i in 80:
		var dp = page_open("dialogue")
		if dp == null: return chosen or key == ""
		var choices: Array = dp.convo.get("choices", [])
		if dp.at_end() and dp.shown_chars >= dp.current().length() and not choices.is_empty():
			var pick := -1
			for k in choices.size():
				var ch: Dictionary = choices[k]
				if key != "" and ch.has(key) and (value == "" or str(ch.get(key)) == value or str(ch.get("text", "")).contains(value)): pick = k
			if pick < 0 and not chosen:
				# Nothing asked of this talk: the farewell (the last choice), as a player leaves it.
				pick = choices.size() - 1
				if key != "": say("no %s=%s among %s" % [key, value, str(choices.map(func(ch): return str(ch.get("text", ""))))])
			elif pick >= 0: chosen = true
			if not await tap_region(dp, "choose", pick): dp._choose(pick)
			await frames(10)
			if key == "" or chosen:
				# After the choice the talk may go on (the same person's next quest): read it and leave it.
				if page_open("dialogue") != null and not chosen: continue
			continue
		if not await tap_region(dp, "advance"): await tap(Vector2(640, 600))
		await frames(4)
	return chosen

# ------------------------------------------------------------------ fighting
var kills := {}
func _on_event(nm: String, p: Dictionary) -> void:
	if nm == "actor_defeated" and str(p.get("victim_kind", "")) == "enemy": kills[str(p.get("def", ""))] = int(kills.get(str(p.get("def", "")), 0)) + 1
	if nm == "script_error" or nm == "error": say("event error %s" % str(p))

## Fight `count` of a foe as a thumb does: walk up to the nearest, tap Attack (its soft lock aims), a technique now and
## then, Dodge when it winds up, and the tea from Quick-use when low. Returns the kills.
func fight(def_id: String, count: int, limit := 90.0, name := "") -> int:
	var before := int(kills.get(def_id, 0))
	var start := now_ms()
	var shot_taken := false
	var last_tech := 0
	while int(kills.get(def_id, 0)) - before < count and now_ms() - start < limit * 1000.0:
		if top_page() != null:
			await shot("page_in_fight", "a page opened in a fight: %s" % str(top_page().page_id))
			if str(top_page().page_id) == "revival": await tap_region(top_page(), "choose", "shrine")
			await close_pages()
		if Game.combat.is_wounded(c().id):
			await frames(30)
			continue
		var target: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.team != "enemy" or e.def.get("passive", false): continue
			if e.def_id != def_id and not e.in_fight(): continue
			if target == null or e.plane.distance_to(me()) < target.plane.distance_to(me()): target = e
		if target == null:
			await frames(20)
			continue
		var d: float = target.plane.distance_to(me())
		if d > 44.0:
			var stand: Vector2 = target.plane - (target.plane - me()).normalized() * 30.0
			stick(stand - me())
			await frames(2)
			continue
		stick(Vector2.ZERO)
		if not shot_taken and name != "":
			shot_taken = true
			await shot(name, "fighting %s" % def_id)
		# A player reads the tell: every wind-up is dodged away from (Evade), once it is on the HUD.
		if str(target.ai.get("state", "")) == "windup" and role("guard") != Vector2.INF:
			var away: Vector2 = (me() - target.plane).normalized()
			stick(away)
			await tap(role("guard"), 3, 2)
			stick(Vector2.ZERO)
			continue
		if c().pools.hp < c().pools.max_hp * 0.35 and role("quick") != Vector2.INF and c().inventory.count(str(c().inventory.quick_use)) > 0:
			await tap(role("quick"), 3, 2)
		elif c().pools.hp < c().pools.max_hp * 0.3:
			# Nothing left to drink: back off out of the fight and let the body mend, as a player would.
			var back_t := now_ms()
			while now_ms() - back_t < 6000 and c().pools.hp < c().pools.max_hp * 0.8:
				var chaser: Vector2 = target.plane if target.alive else me()
				stick((me() - chaser).normalized() if me().distance_to(chaser) < 360.0 else Vector2.ZERO)
				await frames(6)
			stick(Vector2.ZERO)
			continue
		if now_ms() - last_tech > 2500 and role("skill") != Vector2.INF:
			last_tech = now_ms()
			await tap(role("skill"), 4, 2)
		else:
			await tap(main.hud.attack_center, 5, 2)
		await frames(6)
	stick(Vector2.ZERO)
	await pick_up_all()
	return int(kills.get(def_id, 0)) - before

## Walk over every drop in reach and take it (the context's Pick up, or the auto pick-up).
func pick_up_all() -> void:
	for i in 12:
		if Game.room_rt == null or Game.room_rt.loot.is_empty(): return
		var near: Dictionary = {}
		for l in Game.room_rt.loot:
			if near.is_empty() or Vector2(float(l.x), float(l.y)).distance_to(me()) < Vector2(float(near.x), float(near.y)).distance_to(me()): near = l
		var at := Vector2(float(near.x), float(near.y))
		if at.distance_to(me()) > 400.0: return
		await walk_to(at, 10.0, 6.0, false)
		await frames(10)
		if Game.room_rt.loot.has(near):
			if str(main.world.context.get("type", "")) == "pickup" or main.world.context.has("uid"): await use_context("pickup")
			else: Game.submit({"type": "pick_up", "uid": int(near.uid)})
		await frames(4)

# ------------------------------------------------------------------ the checks a player's eye makes
## The Bag: what it holds, seen on its page (the tea, the gear), and the character's figure wearing what is worn.
func look_in_bag(name: String, want: Array) -> void:
	await close_pages()
	if not await tap_role("icon:bag"):
		main.open_page("inventory", {})
	await frames(20)
	await shot(name, "the Bag: %s" % ", ".join(want))
	var bag := page_open("inventory")
	for id in want:
		if c().inventory.count_including_equipped(str(id)) <= 0: await find("%s is not in the Bag or worn" % str(id), "missing_" + str(id))
	if bag == null: await find("the Bag did not open from its HUD icon", "bag_closed")
	await close_pages()

# ------------------------------------------------------------------ the opening and the Prologue
func opening() -> void:
	await shot("title", "the title screen")
	await tap(Vector2(640, 452))   # Begin
	await frames(20)
	if main.screen != "creation": await find("Begin did not open the creator (screen %s)" % main.screen, "no_creator")
	await shot("creator", "the character creator")
	var cr = main.creator
	cr.name_field.text = "Lin Yue"
	await tap(Vector2(1030, 676))   # Begin
	for i in 240:
		if main.screen == "world" and is_instance_valid(main.world): break
		await frames(1)
	var ch = c()
	if ch == null or ch.view != "topdown": await find("the new game is not a top-down one (view %s)" % (str(ch.view) if ch else "none"), "not_topdown")
	await wait_s(1.0)
	await shot("opening_title", "the opening: %s" % scene_step())
	await wait_s(3.0)
	await shot("opening_ping", "Aunt Ping wakes you: %s" % scene_step())
	await settle()
	await shot("opening_bag_handoff", "the Bag's hand-off: %s" % scene_step())
	if not await tap_role("icon:bag"): await find("the Bag's icon is not on the HUD at its hand-off", "no_bag_icon")
	await frames(20)
	await shot("opening_bag", "the Bag with Aunt Ping's tea")
	if c().inventory.count("herbal_tea") < 1: await find("Aunt Ping's tea is not in the Bag", "no_tea")
	await close_pages()
	await settle()
	await shot("opening_door_handoff", "the door's hand-off: %s" % scene_step())
	await interact("tea_table")
	await shot("hut_second_cup", "the second cup taken (tea %d)" % c().inventory.count("herbal_tea"))
	await talk("aunt_ping", "", "", "talk_aunt_ping")
	await go("exit")
	await wait_s(0.5)
	await shot("home_lane_dawn", "Home Lane at dawn: %s" % scene_step())
	await settle()
	await shot("home_lane_after_scene", "after the dawn scene")

func p_quiet_river() -> void:
	var here := room()
	# A Quiet River: the tracker's go button walks to Lu.
	var go_btn: Array = main.hud.tracker_paths
	await shot("tracker_quiet_river", "the tracker after stepping out (%d go buttons)" % go_btn.size())
	if not go_btn.is_empty():
		await tap((go_btn[0].rect as Rect2).get_center())
		for i in 900:
			if Game.world.auto_path_target(c()) == "" or room() != here: break
			await frames(1)
	await talk("lu_boatman", "hand_in", "a_quiet_river", "lu_quiet_river")
	await settle()
	await shot("four_errands", "Lu's four errands")

func p_fists() -> void:
	# Fists First.
	await talk("uncle_guo", "accept", "fists_first", "guo_fists")
	await settle()
	await shot("fists_handoff", "Guo's hand-off: %s" % scene_step())
	await hit("stump_guo", 6)
	await shot("fists_stump", "the stump punched (%s)" % _tracker_text())
	await hit("dummy_guo", 4)
	await shot("fists_dummy", "the dummy hit (%s)" % _tracker_text())
	await talk("uncle_guo", "hand_in", "fists_first")
	await settle()
	await shot("gauntlets_worn", "Guo's training gauntlets, worn (weapon %s)" % str(c().inventory.equipped.get("weapon", {}).get("id", "none") if c().inventory.equipped.get("weapon") else "none"))
	if c().inventory.equipped.get("weapon") == null or str(c().inventory.equipped.weapon.id) != "training_gauntlets":
		await find("Fists First's training gauntlets are not worn", "no_gauntlets")
	await look_in_bag("bag_gauntlets", ["herbal_tea", "training_gauntlets"])

func p_race() -> void:
	# Race to the Tower (optional): the bell up the long stair.
	if await talk("shen_lian_npc", "accept", "race_to_the_tower", "race_accept"):
		await settle()
		await interact("tower_bell")
		await shot("race_bell", "the tower bell (race %s)" % ("done" if not c().quests.is_active("race_to_the_tower") else "on"))
		await talk("shen_lian_npc", "hand_in", "race_to_the_tower")

func p_kite() -> void:
	# The Runaway Kite: the crates, the hall's roof, a jump to the inn's.
	await talk("little_dou", "accept", "the_runaway_kite", "dou_kite")
	await settle()
	await interact("kite")
	await shot("kite", "the kite (have %d)" % c().inventory.count("kite"))
	await talk("little_dou", "hand_in", "the_runaway_kite")

func p_ma() -> void:
	# Ma's Delivery.
	await go("store_door")
	await settle()
	await talk("old_ma", "accept", "mas_delivery", "ma_delivery")
	await interact("old_net_floor")
	await sell_net()
	await talk("old_ma", "hand_in", "mas_delivery")
	await go("exit")

func p_granny() -> void:
	# Granny's Remedy: the jar, the tea into Quick-use, drunk, the shrine.
	await go("granny_door")
	await settle()
	await talk("granny_liu", "accept", "grannys_remedy", "granny_accept")
	await settle()
	await shot("granny_quick_handoff", "Granny's hand-off: %s" % scene_step())
	await tea_to_quick()
	await settle()
	await shot("granny_drink_handoff", "drink: %s (quick slot %s)" % [scene_step(), str(role("quick"))])
	if role("quick") == Vector2.INF: await find("the Quick-use slot is not drawn while Granny's Remedy asks for it", "no_quick_slot")
	else: await tap(role("quick"), 3, 2)
	await frames(30)
	await shot("tea_drunk", "the tea drunk (HP %d/%d)" % [int(c().pools.hp), int(c().pools.max_hp)])
	await settle()
	await interact("shrine_granny")
	await talk("granny_liu", "hand_in", "grannys_remedy")
	await go("exit")
	await settle()

func p_crabs() -> void:
	# Crab Trouble.
	await talk("uncle_guo", "accept", "crab_trouble", "crab_accept")
	await settle()
	await shot("east_gate", "the East Gate: %s" % scene_step())
	await go("east_gate")
	await settle()
	await shot("reed_shallows", "the Reed Shallows: %s" % scene_step())
	await settle()
	var got := 0
	for i in 8:
		if c().inventory.count("crab_shell") >= 3: break
		got += await fight("mudshell_crab", 1, 40.0, "crab_fight" if i == 0 else "")
		if i == 0:
			await wait_s(1.0)
			await shot("first_weapon", "the first kill's drop: equip prompt %s" % str(main.hud.equip_prompt.current))
			await equip_from_prompt()
	await fight("old_snapper", 1, 90.0, "old_snapper")
	await shot("after_snapper", "Old Snapper beaten")
	await travel("lf_village")
	await talk("uncle_guo", "hand_in", "crab_trouble")
	await settle()
	for id in ["plain_straw_hat", "straw_sandals"]: await equip_from_bag(id)
	await shot("hat_sandals_worn", "the Plain Straw Hat and Straw Sandals worn")
	await look_in_bag("bag_after_crabs", ["training_short_blade", "plain_straw_hat", "straw_sandals"])

func p_night() -> void:
	# Evening on the River, the Hollow Night, the River Token.
	await talk("lu_boatman", "accept", "evening_on_the_river", "evening")
	await settle()
	await talk("aunt_ping")
	await settle()
	await talk("lu_boatman")
	await settle()
	await wait_s(1.0)
	await shot("night", "the Hollow Night: %s" % scene_step())
	await settle()
	for npc in ["little_dou", "granny_liu", "old_ma"]:
		await talk(npc, "effects", "")
		await settle()
	await shot("night_guided", "the villagers guided (flags %s)" % str(["dou_safe", "granny_safe", "ma_safe"].map(func(f): return c().quests.has_flag(f))))
	var refuge: Dictionary = Game.room_rt.object_def("hut_refuge")
	if not refuge.is_empty(): await stand_by(refuge)
	var night_t := now_ms()
	var night_shot := false
	while room() == "lf_village_night" and now_ms() - night_t < 120000:
		var foe_near := Game.room_rt.living_enemies().filter(func(e): return e.team == "enemy" and e.plane.distance_to(me()) < 120.0)
		if not foe_near.is_empty(): await tap(main.hud.attack_center, 5, 2)
		if not night_shot and now_ms() - night_t > 20000:
			night_shot = true
			await shot("night_hold", "holding out at the hut")
		await frames(6)
	await settle()
	await wait_s(1.0)
	await shot("lu_boat", "Lu's boat: %s" % scene_step())
	await settle()
	await first_breakthrough()
	await talk("lu_boatman", "hand_in", "the_river_token", "river_token")
	await settle()
	await shot("flowing_palm", "Flowing Palm slotted (%s)" % str(c().cultivator.technique_slots.slice(0, 2)))

func p_willow() -> void:
	# The Willow Path.
	await go("deck")
	await settle()
	await go("west_gate")
	await settle()
	await shot("willow_east", "Willow Path East: %s" % scene_step())
	await go("west")
	await settle()
	await interact("shrine_wp")
	for i in 8:
		if not c().quests.is_active("the_willow_path"): break
		await fight("wild_boarlet", 1, 60.0, "boarlets" if i == 0 else "")
	await shot("willow_done", "The Willow Path (done %s)" % str(c().quests.is_done("the_willow_path")))

func sell_net() -> void:
	await talk("old_ma", "shop", "")
	await frames(20)
	var shop := page_open("shop")
	await shot("shop", "Old Ma's shop")
	if shop == null:
		await find("Old Ma's shop did not open from her talk", "no_shop")
		var idx: int = c().inventory.first_index("old_net")
		if idx >= 0: Game.submit({"type": "sell", "index": idx, "count": 1})
		return
	var idx2: int = c().inventory.first_index("old_net")
	if idx2 >= 0: Game.submit({"type": "sell", "index": idx2, "count": 1})   # the shop's sell row (its layout is the page's)
	await close_pages()

## Granny's hand-off: the Bag, the tea, "Quick-use" on its card.
func tea_to_quick() -> void:
	if not await tap_role("icon:bag"): main.open_page("inventory", {})
	await frames(20)
	var bag := page_open("inventory")
	var i: int = c().inventory.first_index("herbal_tea")
	if bag != null and i >= 0:
		await tap_region(bag, "bag", i)
		await frames(10)
		await shot("bag_tea_card", "the tea's card in the Bag")
		if not await tap_region(bag, "quick"):
			await find("the tea's card has no Quick-use button", "no_quick_button")
			Game.submit({"type": "set_quick_use", "item": "herbal_tea"})
	await close_pages()

func equip_from_prompt() -> void:
	var cur: Dictionary = main.hud.equip_prompt.current
	if cur.is_empty():
		var any: bool = c().inventory.bag.any(func(s): return s != null and str(s.id) == "training_short_blade")
		if any: await find("the first weapon dropped but no equip prompt offers it", "no_equip_prompt")
		return
	var r: Rect2 = EquipPrompt.RECT
	for p in [r.position + Vector2(r.size.x * 0.3, r.size.y - 30), r.get_center()]:
		if main.hud.role_at(p) == "prompt:equip":
			await tap(p)
			break
	await frames(20)
	if not main.hud.equip_prompt.current.is_empty(): main.hud.equip_prompt.equip(c())
	await frames(10)
	await shot("first_weapon_worn", "the equip prompt taken (weapon %s)" % str(c().inventory.equipped.get("weapon", {}).get("id", "none") if c().inventory.equipped.get("weapon") else "none"))

func equip_from_bag(id: String) -> void:
	var i: int = c().inventory.first_index(id)
	if i < 0: return
	if not await tap_role("icon:bag"): main.open_page("inventory", {})
	await frames(20)
	var bag := page_open("inventory")
	if bag != null:
		await tap_region(bag, "bag", i)
		await frames(8)
		if not await tap_region(bag, "equip"): Game.submit({"type": "equip", "index": i})
	await close_pages()

## Lu's boat: meditate (the Cultivate button), the bar full, the Cultivation page and the breakthrough.
func first_breakthrough() -> void:
	var spring: Dictionary = Game.room_rt.object_def("boat_spring")
	if not spring.is_empty(): await stand_by(spring)
	if not await tap_role("meditate"): Game.submit({"type": "start_meditation"})
	await wait_s(2.0)
	await shot("meditating", "meditating on the deck (%d%%)" % int(100.0 * c().cultivator.progress_fraction()))
	var start := now_ms()
	while c().cultivator.state != "bottleneck" and now_ms() - start < 90000: await frames(10)
	await settle()
	if c().cultivator.meditating: await tap_role("meditate")
	await frames(20)
	await tap(Vector2(640, 712))   # the progress bar along the foot opens Cultivation
	await frames(30)
	if page_open("cultivation") == null:
		await find("a tap on the progress bar did not open the Cultivation page", "no_cultivation_page")
		main.open_page("cultivation", {})
		await frames(30)
	await shot("cultivation_page", "the Cultivation page at the bottleneck")
	var cp := page_open("cultivation")
	if cp != null and await tap_region(cp, "breakthrough"):
		await frames(40)
		await shot("breakthrough_page", "the breakthrough page")
		var bp := page_open("breakthrough")
		if bp == null or not await tap_region(bp, "go"): Game.submit({"type": "start_breakthrough", "support_items": []})
	else:
		Game.submit({"type": "start_breakthrough", "support_items": []})
	await wait_s(5.0)
	await shot("breakthrough", "the first breakthrough (%s)" % c().cultivator.realm_key)
	await close_pages()
	await settle()

# ------------------------------------------------------------------ the fair and the sect
const SECTS := {"jade": {"id": "jade_sect", "recruiter": "recruiter_qing_lan", "trial": "trial_jade", "gate": "ja_gate_street",
	"steward": "jade_steward", "weapon_hall": "ja_weapon_hall", "master": "jade_weapon_master", "mentor": "elder_hu", "peak": "ja_elder_hu_peak"},
	"cloud": {"id": "cloud_sect", "recruiter": "recruiter_mo_yun", "trial": "trial_cloud", "gate": "cm_cliff_stair",
	"steward": "cloud_steward", "weapon_hall": "cm_weapon_hall", "master": "cloud_weapon_master", "mentor": "elder_sung", "peak": "cm_elder_sung_peak"}}

func s(k: String) -> String:
	return str(SECTS[sect][k])

## A kept game resumed from the title: Continue, the character, into the world where it was saved.
func resume() -> void:
	await shot("title_continue", "the title with a saved game")
	await tap(Vector2(640, 452))   # Continue
	await frames(20)
	await shot("selection", "character selection")
	if main.screen == "selection": main.shell.enter.emit(1)
	for i in 240:
		if main.screen == "world" and is_instance_valid(main.world): break
		await frames(1)
	await wait_s(1.0)
	await settle()
	await shot("resumed", "resumed in %s" % room())

func fair() -> void:
	await travel("sf_fairground")
	await settle()
	await shot("fairground", "the Fairground: %s" % scene_step())
	await settle()
	await talk("recruiter_qing_lan", "accept", "the_recruitment_fair", "qing_lan")
	await talk("recruiter_mo_yun", "", "", "mo_yun")
	await settle()

func sect_choice() -> void:
	await talk(s("recruiter"), "effects", "Join", "join_%s" % sect)
	await settle()
	await shot("sect_chosen", "the %s chosen: %s" % [sect, scene_step()])
	await settle()
	await shot("entry_trial_tracker", "the Entry Trial leads the tracker")
	# The Entry Trial.
	await go(s("trial"))
	await settle()
	await shot("trial_room", "the %s trial ground" % sect)
	await interact("trial_bell")
	await wait_s(1.5)
	await fight("trial_puppet", 1, 90.0, "trial_puppet")
	await settle()
	await shot("trial_done", "the Entry Trial (done %s, realm %s)" % [str(c().quests.is_done("entry_trial")), c().cultivator.realm_key])
	await travel("sf_fairground")
	await settle()
	# Fish-Gutting Fists: Shen Lian's spar.
	await talk("shen_lian", "accept", "fish_gutting_fists", "shen_lian")
	await talk("shen_lian", "spar", "")
	await wait_s(1.0)
	var start := now_ms()
	while c().quests.is_active("fish_gutting_fists") and now_ms() - start < 90000:
		var foe = null
		for e in Game.room_rt.living_enemies():
			if e.def.get("spar", false): foe = e
		if foe == null:
			await frames(10)
			if Game.room_rt.living_enemies().all(func(e): return not e.def.get("spar", false)) and str(c().quests.active.get("fish_gutting_fists", {}).get("state", "")) == "ready": break
			continue
		if foe.plane.distance_to(me()) > 44.0:
			stick(foe.plane - me())
			await frames(2)
			continue
		stick(Vector2.ZERO)
		await tap(main.hud.attack_center, 5, 2)
		await frames(6)
	stick(Vector2.ZERO)
	await shot("spar", "Shen Lian's spar")
	await talk("shen_lian", "hand_in", "fish_gutting_fists")
	await settle()

func chapter2() -> void:
	# A Disciple's Chores at the sect's gate.
	await travel(s("gate"))
	await settle()
	await shot("sect_gate", "the %s's gate" % sect)
	if await talk(s("steward"), "accept", "a_disciples_chores", "steward"):
		for o in Game.room_rt.def.get("objects", []).filter(func(q): return str(q.get("set_flag", "")).begins_with("swept_")):
			await interact(str(o.id))
		await talk(s("steward"), "hand_in", "a_disciples_chores")
	# The Weapon Hall.
	var bt := now_ms()
	while not ProgressionRules.at_least(c().cultivator.realm_key, "bone_forging_3") and now_ms() - bt < 20000:
		if c().cultivator.state == "bottleneck": Game.submit({"type": "start_breakthrough", "support_items": []})
		await wait_s(2.0)
	await shot("tracker_weapon_hall", "the tracker at Bone Forging 3")
	await travel(s("weapon_hall"))
	await settle()
	await talk(s("master"), "accept", "the_weapon_hall", "weapon_master")
	var jian: int = c().inventory.first_index("training_jian")
	if jian >= 0: Game.submit({"type": "equip", "index": jian})
	var dummies: Array = Game.room_rt.def.get("objects", []).filter(func(o): return str(o.get("type", "")) == "training_dummy")
	if not dummies.is_empty(): await hit(str(dummies[0].id), 6)
	if role("guard") != Vector2.INF:
		touch(role("guard"), true, 3)
		await wait_s(0.6)
		touch(role("guard"), false, 3)
	await shot("jian_guard", "the training jian in hand, guarding")
	await talk(s("master"), "hand_in", "the_weapon_hall")
	await settle()
	# Strange Tracks and The Humming Token.
	await travel("rm_marsh_edge")
	await settle()
	await shot("marsh_edge", "the Marsh Edge")
	await fight("reed_frog", 1, 60.0, "frog")
	for o in Game.room_rt.def.get("objects", []).filter(func(q): return str(q.get("type", "")) == "inspect"):
		if Game.world.object_visible(c(), o): await interact(str(o.id))
	await travel(s("peak"))
	await settle()
	await talk(s("mentor"), "hand_in", "strange_tracks", "mentor")
	await settle()
	await talk(s("mentor"), "accept", "the_humming_token")
	await travel("rm_marsh_edge")
	await fight("hollowed_boarlet", 5, 150.0, "hollowed_boarlets")
	await travel(s("peak"))
	await talk(s("mentor"), "hand_in", "the_humming_token")
	await settle()
	await shot("humming_token_done", "The Humming Token done")

func to_the_gate() -> void:
	await travel("sf_artisan_row")
	await talk("mei_qing", "accept", "mei_qings_errand", "mei_qing")
	await shot("tracker_mei_qing", "Mei Qing's errand on the tracker")
	await travel("rm_marsh_edge")
	for i in 20:
		if c().inventory.count("willow_moss") >= 5: break
		await fight("reed_frog", 1, 40.0)
	for i in 20:
		if c().inventory.count("grey_hide") >= 3: break
		await fight("hollowed_boarlet", 1, 40.0)
	# The prototype's gate on the road east to the Grey Pools.
	var east: Dictionary = Game.room_rt.portal_def("east")
	await walk_to(Vector2(float(east.at[0]), float(east.at[1])) - Vector2(80, 0), 16.0)
	await shot("gate_approach", "the road east, closed by the prototype's gate")
	await walk_to(Vector2(float(east.at[0]), float(east.at[1])) - Vector2(24, 0), 12.0)
	for i in 40:
		stick(Vector2.RIGHT)
		await frames(1)
	stick(Vector2.ZERO)
	await shot("gate_touch", "walked into the gate (room %s)" % room())
	if room() != "rm_marsh_edge": await find("the gate let the body through into %s" % room(), "gate_open")
	await travel("sf_artisan_row")
	await talk("mei_qing", "hand_in", "mei_qings_errand")
	await settle()
	await travel(s("peak"))
	await talk(s("mentor"))
	await settle()
	await shot("tracker_after_grey", "the tracker after Grey at the Edges")
	# The wait for Bone Forging 7 is a hunt; the driver takes the realm's shortcut (a debug step, noted), then plays The
	# First Current at the Lotus Ferry spring.
	for i in 60:
		if ProgressionRules.at_least(c().cultivator.realm_key, "bone_forging_7"): break
		if c().cultivator.state == "bottleneck": Game.submit({"type": "start_breakthrough", "support_items": []})
		else: Game.progression.apply_progress(c().id, 0.0, "qa_shortcut", 1.0)
		await frames(20)
	say("QA shortcut: realm set to %s for The First Current" % c().cultivator.realm_key)
	await travel("lf_village")
	await talk("lu_boatman", "accept", "the_first_current", "first_current")
	var spring: Array = Game.room_rt.def.get("objects", []).filter(func(o): return str(o.get("type", "")) == "qi_spring")
	if not spring.is_empty(): await stand_by(spring[0])
	await tap_role("meditate")
	await wait_s(34.0)
	await tap_role("meditate")
	await talk("lu_boatman", "hand_in", "the_first_current")
	await settle()
	await shot("tracker_after_first_current", "the tracker after The First Current")
	main.open_page("quests", {})
	await frames(30)
	await shot("quests_page_end", "the Quests page at the prototype's end")
	await close_pages()
