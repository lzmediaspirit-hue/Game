extends Node
## The capture tool's shared steps (tools/dev/README.md, "Captures"). A row of shots.gd is a list of these, each
## `[name, args...]`, run by name as `s_<name>(args...)`: the ones that stand, move and press as a player would, the
## ones that set the story or the character, and the takes, which write a picture. A take's first argument is the
## picture's name: "*" is the row's own name, and "{tag}" (or any other `--key=value` of the command line) is filled in;
## a name may hold a folder ("closeups/*_1"). Everything a step does is what the one-off capture scripts did before
## decision 45 folded them here, call for call and frame for frame, so every picture comes out framed as it was.

const DAY_ANCHOR := 600000.0   ## the pinned clock's day (a day far from any calendar event)
const NIGHT_INK := Color("071015")

var main
var w       ## the room view the takes read (main's, or a view of the capture's own)
var p       ## its player
var m: TopdownMotor
var row := {}
var vars := {}
var docs := "res://docs/"     ## where the pictures go (--out-root=<dir> puts them elsewhere; docs stay the inputs)
var out_dir := ""             ## the set's folder under `docs`
var keep := {}                ## named lists of pictures a later take lays out as a sheet
var last_img: Image           ## the last whole window a take grabbed (a region of it can be cut without a new frame)
var boxes := {}               ## where the staged bodies stand on the shots (the quality set's boxes.json)
var whole_hook := {"on": false}

# ------------------------------------------------------------------------------------------------------ plumbing
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
	await get_tree().process_frame

func _bind() -> void:
	w = main.world
	p = w.player
	m = p.motor

## A picture's name: "*" the row's, {key} a variable of the command line.
func _name(tpl) -> String:
	var n := str(tpl if tpl != null and str(tpl) != "" else "*").replace("*", str(row.get("name", "")))
	for k in vars: n = n.replace("{%s}" % k, str(vars[k]))
	return n

## Where a picture is written, its folder made.
func _png(tpl, ext := ".png") -> String:
	var path: String = out_dir + _name(tpl) + ext
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	return path

## A file the capture reads (a mock, a before and an after): from the out root when it is there, else from docs/.
func _src(rel: String) -> String:
	if FileAccess.file_exists(docs + rel): return docs + rel
	return "res://docs/" + rel

## A point of the room (world units): a Vector2 as it is, or ["prop", kind, cells off its cell, units added],
## ["here", off] (from where the body stands), ["spawn"] (the room's spawn).
func _at(spec) -> Vector2:
	if spec is Vector2: return spec
	match str(spec[0]):
		"prop":
			var cell: Vector2i = w.room.props.filter(func(q): return q.kind == str(spec[1]))[0].cell
			return (Vector2(cell) + (spec[2] as Vector2)) * 32.0 + (spec[3] as Vector2 if spec.size() > 3 else Vector2.ZERO)
		"here": return w.player.motor.pos + (spec[1] as Vector2)
		"spawn": return w.room.spawn
	push_error("capture: no place %s" % str(spec))
	return Vector2.ZERO

func _c():
	return Game.active()

## The window's pixels per canvas pixel and the canvas's left bar (a 20:9 phone's 2400 x 1080 draws the 1280 x 720 canvas
## at 1.5, centred): a rectangle of the canvas on the window's image.
func _to_img(r: Rect2) -> Rect2i:
	var size := get_tree().root.get_texture().get_image().get_size()
	var k := float(size.y) / 720.0
	var off := Vector2((float(size.x) - 1280.0 * k) * 0.5, 0.0)
	return Rect2i(Vector2i((r.position * k + off).round()), Vector2i((r.size * k).round()))

func phone() -> bool:
	return get_tree().root.get_texture().get_image().get_size().x > 1280

# ------------------------------------------------------------------------------------------------------ stand, move
func s_frames(n: int) -> void:
	await frames(n)

## `n` single frames (a physics frame and a process frame each), as a loop of frames(1) waits them.
func s_tick(n: int) -> void:
	for i in n: await frames(1)

func s_process_frames(n: int) -> void:
	for i in n: await get_tree().process_frame

## Stand at a cell of the room on view, facing the camera (its villagers' sheets load in while it waits `n` frames).
func s_spot(cell: Vector2, n: int) -> void:
	_bind()
	m.place((cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	m.dir = Vector2.DOWN
	w._settle_camera()
	await frames(n)

## Stand at a point (see _at), the camera on it at once.
func s_start(at) -> void:
	m.place(_at(at))
	m.dir = Vector2.DOWN
	w.cam = w._cam_target()
	await frames(30)

## An empty square round `at` with these foes ([def, offset in units]) turned on the player.
func s_arena(at, foes: Array) -> void:
	var pos := _at(at)
	Game.room_rt.enemies.clear()
	Game.room_rt.spawn_slots.clear()
	Game.room_rt.loot.clear()
	Game.combat.wounded.erase(Game.active_id)
	_c().pools.hp = _c().pools.max_hp
	main.close_all_pages()
	await s_start(pos)
	for f in foes:
		var e: EnemyState = Game.enemies.spawn_at(str(f[0]), pos + (f[1] as Vector2), 1)
		e.altitude = w.room.height_at(e.plane)
		e.threat[Game.active_id] = 1.0
	await frames(20)

## Foes set round a cell ([def, offset in cells]), on the ground nearest; `turned` sets them on the player.
func s_foes(cell: Vector2, foes: Array, turned := false) -> void:
	for f in foes:
		var at: Vector2 = w.room.nearest_standable((cell + f[1] + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		var e: EnemyState = Game.enemies.spawn_at(str(f[0]), at, 1)
		e.altitude = w.room.height_at(e.plane)
		if turned: e.threat[Game.active_id] = 1.0

## Enter a room through the World authority (at `pos`, world units, when given; the portal's own spot otherwise).
func s_load(room: String, pos = null) -> void:
	if pos == null: Game.world.load_room(_c(), room, "")
	else: Game.world.load_room(_c(), room, "", _at(pos))
	GameEvents.flush()

func s_portal(portal: String) -> void:
	Game.submit({"type": "use_portal", "portal": portal, "crossing": true})

## Stand on the ground nearest a cell's point ([x, y]).
func s_stand_cell(cell: Array) -> void:
	m.place(w.room.nearest_standable(TopdownRoom.cell_point(cell)))

## Stand beside a person of the room on view, facing them, and settle the camera.
func s_beside(object: String) -> void:
	_bind()
	var o: Dictionary = Game.room_rt.object_def(object)
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	m.place(w.room.spot_near(at, float(o.get("alt", 0.0)), at + Vector2(0, 40)))
	m.dir = Vector2.UP
	w._settle_camera()
	await frames(30)

func s_face(dir: Vector2) -> void:
	m.face(dir)

func s_move(axis: Vector2) -> void:
	p.movement = axis

func s_stop() -> void:
	p.movement = Vector2.ZERO

# ------------------------------------------------------------------------------------------------------ act
func s_attack() -> void:
	p.attack()

func s_aim_attack(dir: Vector2) -> void:
	p.aim_attack(dir)

func s_aim_technique(slot: int, dir: Vector2, strength = null) -> void:
	if strength == null: p.aim_technique(slot, dir)
	else: p.aim_technique(slot, dir, strength)

func s_finisher(dir: Vector2) -> void:
	p.finisher(dir)

func s_jump() -> void:
	p.jump()

func s_dodge() -> void:
	p.dodge()

func s_plunge() -> void:
	p.plunge()

## The HUD's thumb: pressed, dragged (from an anchor, by `off`) and let go.
func _anchor(name: String) -> Vector2:
	if name.begins_with("slot"): return main.hud.slots[int(name.substr(4))]
	return main.hud.attack_center

func s_press(id: int, anchor: String) -> void:
	main.hud.press(id, _anchor(anchor))

func s_drag(id: int, anchor: String, off: Vector2) -> void:
	main.hud.drag(id, _anchor(anchor) + off)

func s_release(id: int) -> void:
	main.hud.release(id)

## `n` frames with the body kept whole, a plain attack every `every` frames from the first.
func s_fight(n: int, every := 0) -> void:
	for f in n:
		_c().pools.hp = _c().pools.max_hp
		if every > 0 and f % every == 0: p.attack()
		await frames(1)

## The body kept whole on every physics frame from here on (or no longer).
func s_keep_whole(on: bool) -> void:
	whole_hook.on = on
	if on and not get_tree().physics_frame.is_connected(_whole):
		get_tree().physics_frame.connect(_whole)

func _whole() -> void:
	if whole_hook.on and Game.active() != null and Game.active().pools.max_hp > 0.0: Game.active().pools.hp = Game.active().pools.max_hp

## `n` frames, the steps of `events` ({frame: [steps]}) run on their frame; with `grab` [every, at, most, w, h] a crop
## round the body kept into `into` on the frames where f % every == at; `move` [[from, to, axis]] holds the stick;
## `whole` keeps the body's HP full on every frame.
func s_timeline(n: int, events: Dictionary, opts := {}) -> void:
	for f in n:
		if opts.get("whole", false): _c().pools.hp = _c().pools.max_hp
		for st in events.get(f, []): await run_step(st)
		if opts.has("grab"):
			var g: Array = opts.grab
			var into: Array = keep.get_or_add(str(opts.get("into", "grab")), [])
			if f % int(g[0]) == int(g[1]) and into.size() < int(g[2]): into.append(await crop(int(g[3]), int(g[4])))
		if opts.has("move"):
			var axis := Vector2.ZERO
			for mv in opts.move:
				if f >= int(mv[0]) and f < int(mv[1]): axis = mv[2]
			p.movement = axis
		await get_tree().physics_frame
		await get_tree().process_frame

# ------------------------------------------------------------------------------------------------------ the character
func s_hp_full() -> void:
	_c().pools.hp = _c().pools.max_hp

func s_qi_full() -> void:
	_c().pools.qi = _c().pools.max_qi

## Qi just short of a technique's cost.
func s_qi_short(tech: String, less: float) -> void:
	_c().pools.qi = maxf(0.0, Game.combat.technique_cost(_c(), ContentDB.entry("techniques", tech)) - less)

func s_cooldowns_clear() -> void:
	_c().pools.cooldowns.clear()

func s_cooldown(key: String, secs: float) -> void:
	_c().pools.cooldowns[key] = secs

func s_cooldown_off(key: String) -> void:
	_c().pools.cooldowns.erase(key)

## A slot of the gear set to a fresh item (or emptied), without the stats refreshed.
func s_gear(slot: String, item, seed := 0) -> void:
	_c().inventory.equipped[slot] = null if item == null else LootRules.make_instance(str(item), 1, "common", null, seed)

func s_refresh() -> void:
	Game.combat.refresh_stats(_c().id)

## An item added to the Bag and equipped from it, as the Bag would.
func s_equip(item: String) -> void:
	Game.inventory.apply_add(_c().id, item, 1, "capture")
	Game.submit({"type": "equip", "index": _c().inventory.first_index(item)})

func s_give(item: String, n := 1) -> void:
	Game.inventory.apply_add(_c().id, item, n, "capture")

func s_secret_art(id: String) -> void:
	if not _c().cultivator.secret_arts.has(id): _c().cultivator.secret_arts.append(id)

func s_unlock(ids: Array) -> void:
	for u in ids: Unlocks.force_unlock(_c().id, str(u))

func s_unlocks_evaluate() -> void:
	Unlocks.evaluate(_c().id)

## A property of the character by its dotted path ("training_sect", "cultivator.realm_key", "inventory.quick").
func s_set(path: String, value) -> void:
	var parts := path.split(".")
	var o = _c()
	for i in parts.size() - 1: o = o.get(parts[i]) if o is Object else o[parts[i]]
	var v = value.duplicate(true) if value is Array or value is Dictionary else value
	if o is Object: o.set(parts[-1], v)
	else: o[parts[-1]] = v

## A property of the HUD ("fight_override", "visible", "fan_open").
func s_hud(prop: String, value) -> void:
	main.hud.set(prop, value)

func s_hud_state(on: bool) -> void:
	main.hud.set_state(on)

func s_clear_notices() -> void:
	main.hud.toasts = []
	main.hud.log_lines = []
	main.hud.pulses = {}
	main.hud.banner.t = 99.0

## The foes of the room made hard to kill.
func s_sturdy() -> void:
	for e in Game.room_rt.enemies.values():
		e.pools.max_hp = 1.0e12
		e.pools.hp = e.pools.max_hp

func s_clear_enemies() -> void:
	Game.room_rt.enemies.clear()

func s_submit(cmd: Dictionary) -> void:
	Game.submit(cmd.duplicate(true))

func s_flush() -> void:
	GameEvents.flush()

func s_effects(list: Array) -> void:
	Game.apply_effects(_c().id, list.duplicate(true), "capture")

func s_rewards(quest: String) -> void:
	Game.apply_effects(_c().id, ContentDB.entry("quests", quest).get("rewards", []), "capture")

## Quests marked done (and no longer active), as the walk would have left them.
func s_quests_done(ids: Array) -> void:
	for q in ids:
		_c().quests.active.erase(q)
		_c().quests.done[q] = 1

func s_quest_start(id: String) -> void:
	Game.quest.apply_start(_c().id, id)

func s_flag(flag: String) -> void:
	Game.quest.apply_flag(_c().id, flag)

func s_villagers(base: Vector2, list: Array) -> void:
	for v in list: w.add_villager(str(v[0]), base + (v[1] as Vector2), str(v[2]))

# ------------------------------------------------------------------------------------------------------ the clock
## The clock pinned at an hour of the day (0 to 1), and the light with it.
func s_hour(h: float) -> void:
	var day_s := Clock.game_day_s()
	Clock.simulate(DAY_ANCHOR * day_s + h * day_s, 0)
	TopdownLight.debug_hour = h

func s_weather(kind: String) -> void:
	Game.calendar.debug_weather = kind

# ------------------------------------------------------------------------------------------------------ pages, talk
func s_open_page(id: String, args := {}) -> void:
	main.open_page(id, args.duplicate(true))

func s_close_pages() -> void:
	main.close_all_pages()

## Talk to a person: their talk on the dialogue page.
func s_talk(object: String) -> void:
	var r := Game.submit({"type": "interact", "object": object})
	if r.has("dialogue"): main.open_page("dialogue", {"convo": r.dialogue})
	else: print("  capture: no talk with %s (%s)" % [object, str(r)])

## The talk on the dialogue page at its last line, written out.
func s_dialogue_end() -> void:
	var top = main.top_page()
	if top != null and top.page_id == "dialogue":
		top.line = maxi(0, top.lines().size() - 1)
		top.shown_chars = 9999.0

## The talk's first choice that takes a quest, chosen on its page.
func s_dialogue_accept() -> void:
	var dp = main.top_page()
	if dp == null or dp.page_id != "dialogue": return
	var choices: Array = dp.convo.get("choices", [])
	print("  capture: the talk offers %s" % str(choices.map(func(ch): return str(ch.get("accept", ch.get("text", ""))))))
	for i in choices.size():
		if choices[i].has("accept"):
			dp.on_action("choose", i)
			break

## Talk to a person and pick the choice that takes or hands in a quest, as the dialogue page would.
func s_choose(object: String, key: String, quest: String) -> void:
	var o: Dictionary = Game.room_rt.object_def(object)
	w = main.world
	w.player.motor.place(w.room.spot_near(Vector2(float(o.at[0]), float(o.at[1])), float(o.get("alt", 0.0)), Vector2(float(o.at[0]), float(o.at[1]) + 40)))
	await frames(4)
	var r := Game.submit({"type": "interact", "object": object})
	var npc := str(o.get("npc", ""))
	for ch in r.get("dialogue", {}).get("choices", []):
		if str(ch.get(key, "")) == quest:
			Game.submit({"type": "choose_dialogue", "npc": npc, "choice": ch})
			break
	await frames(6)

# ------------------------------------------------------------------------------------------------------ the story
## Wait (at most `limit` frames) until the scene plays the step of kind `kind` whose text or prompt holds `has` (the
## `nth` such step), `after` seconds into it.
func s_scene_at(id: String, kind: String, after: float, has := "", nth := 0, limit := 900, close_pages := false) -> void:
	for i in limit:
		if close_pages and not main.pages.is_empty(): main.close_all_pages()   # a page the story opens (a challenger's)
		var r = main.scenes.run
		if r != null and str(r.id) == id and r.begun and int(r.i) < (r.row.steps as Array).size():
			# The step itself (the nth of its kind holding `has`): at it `after` seconds in, or at once when it is past.
			var want := -1
			var seen := 0
			for k in (r.row.steps as Array).size():
				var s: Dictionary = r.row.steps[k]
				if str(s.do) == kind and (has == "" or (str(s.get("text", "")) + str(s.get("prompt", "")) + str(s.get("to", ""))).contains(has)):
					if seen == nth:
						want = k
						break
					seen += 1
			if want >= 0 and (int(r.i) > want or (int(r.i) == want and float(r.t) >= after)):
				if int(r.i) > want: print("  capture: %s %s %s passed (at step %d)" % [id, kind, has, int(r.i)])
				return
		await frames(1)
	var r = main.scenes.run
	print("  capture: %s %s %s not reached (run %s step %s %s)" % [id, kind, has, str(r.id) if r else "none", str(r.i) if r else "", str(r.row.steps[r.i].do) if r and r.i < r.row.steps.size() else ""])

## Wait until no scene holds the stage (or one waits on the player's hand).
func s_until_idle(limit := 1800) -> void:
	for i in limit:
		if main.scenes.run == null and not main.scenes.busy(): return
		if main.scenes.run != null and str(main.scenes.run.mode) == "hand":
			return
		await frames(1)

## Until the scene playing (live or cut) is over or waits on the player.
func s_until_quiet(limit := 900) -> void:
	for i in limit:
		var r = main.scenes.run
		if r == null or str(r.mode) == "hand": return
		await frames(1)

func s_queue_scene(id: String) -> void:
	main.scenes.queue.append(id)

## No staged scene holds the stage: every one is marked seen, and one playing is ended.
func s_no_scenes() -> void:
	var c = _c()
	for r in ContentDB.all("scenes"): c.quests.scenes[str(r.id)] = {"done": true}
	for i in 8:
		if main.scenes.run == null: break
		main.scenes._finish(true)
		await frames(2)
	main.close_all_pages()

# ------------------------------------------------------------------------------------------------------ takes
## The whole window (the HUD and all).
func s_shot(name = "*") -> void:
	await RenderingServer.frame_post_draw
	last_img = get_tree().root.get_texture().get_image()
	last_img.save_png(_png(name))

## The world viewport alone (no HUD), x2.
func world_shot() -> Image:
	await RenderingServer.frame_post_draw
	var img: Image = w.viewport.get_texture().get_image()
	img.resize(img.get_width() * 2, img.get_height() * 2, Image.INTERPOLATE_NEAREST)
	return img

func s_world(name = "*") -> void:
	(await world_shot()).save_png(_png(name))

## A rectangle of the window's canvas (a phone's window scaled to it), x`zoom` (the phone's own pixels kept as they
## are); `reuse` cuts it from the last whole window taken, at that same instant.
func s_region(name, r: Rect2, zoom := 1, reuse := false) -> void:
	if not reuse:
		await RenderingServer.frame_post_draw
		last_img = get_tree().root.get_texture().get_image()
	var img: Image = last_img.get_region(_to_img(r))
	if zoom != 1 and not phone(): img.resize(img.get_width() * zoom, img.get_height() * zoom, Image.INTERPOLATE_NEAREST)
	img.save_png(_png(name))

## A crop of the window round the body at x2 of the world's art px: `size` window px, the body's point placed `anchor`
## px in from the crop's corner (the crop kept inside the window), the point moved by `off` (x2) and lifted by `lift`;
## scaled by `zoom`. `reuse` cuts it from the last whole window taken.
func around(size: Vector2i, anchor: Vector2i, off := Vector2.ZERO, lift := -30.0, reuse := false) -> Image:
	var img: Image = last_img
	if not reuse:
		await RenderingServer.frame_post_draw
		img = get_tree().root.get_texture().get_image()
	var c: Vector2 = (p.screen - w.camera.position + Vector2(320, 180)) * 2.0 + off * 2.0 + Vector2(0, lift)
	return img.get_region(Rect2i(Vector2i(clampi(int(c.x) - anchor.x, 0, 1280 - size.x), clampi(int(c.y) - anchor.y, 0, 720 - size.y)), size))

## A crop of the screen (w x h screen px) round the body, at x2 of the world's art px.
func crop(cw: int, ch: int) -> Image:
	return await around(Vector2i(cw, ch), Vector2i(cw / 2, ch / 2))

## A quarter of the screen round the body's feet (moved by `off` screen px), x2.
func s_detail(name = "*", off := Vector2.ZERO) -> void:
	var img := await around(Vector2i(640, 360), Vector2i(320, 180), off)
	img.resize(1280, 720, Image.INTERPOLATE_NEAREST)
	img.save_png(_png(name))

## The last whole window round the body (the same instant), `size` px, doubled.
func s_closeup_last(name, size: Vector2i, anchor: Vector2i) -> void:
	var img := await around(size, anchor, Vector2.ZERO, 0.0, true)
	img.resize(size.x * 2, size.y * 2, Image.INTERPOLATE_NEAREST)
	img.save_png(_png(name))

## A crop round the body kept for a sheet.
func s_keep_crop(into: String, cw: int, ch: int) -> void:
	keep.get_or_add(into, []).append(await crop(cw, ch))

## Images in rows of `cols`, 4 px apart on the night ink, saved as one sheet.
func sheet(path: String, tiles: Array, cols: int) -> void:
	if tiles.is_empty(): return
	var tw: int = (tiles[0] as Image).get_width()
	var th: int = (tiles[0] as Image).get_height()
	var rows := ceili(tiles.size() / float(cols))
	var img := Image.create(cols * (tw + 4) - 4, rows * (th + 4) - 4, false, Image.FORMAT_RGBA8)
	img.fill(NIGHT_INK)
	for i in tiles.size(): img.blit_rect(tiles[i], Rect2i(0, 0, tw, th), Vector2i((i % cols) * (tw + 4), (i / cols) * (th + 4)))
	img.save_png(path)

func s_sheet(name, from: String, cols: int) -> void:
	sheet(_png(name), keep.get(from, []), cols)
	keep.erase(from)

## A quarter of the world viewport round the body (moved by `off` art px; its corner `corner` art px up and left of
## that point), x4.
func s_view_x4(name = "*", off := Vector2.ZERO, corner := Vector2i(160, 90)) -> void:
	await RenderingServer.frame_post_draw
	var vi: Image = w.viewport.get_texture().get_image()
	var at: Vector2i = Vector2i(p.screen - w.camera.position + Vector2(320, 180) + off) - corner
	var img := vi.get_region(Rect2i(at.clamp(Vector2i.ZERO, Vector2i(320, 180)), Vector2i(320, 180)))
	img.resize(1280, 720, Image.INTERPOLATE_NEAREST)
	img.save_png(_png(name))

## A close-up x4 of the world viewport round a point: [cell x, cell y, level] (the cell's ground point lifted by its
## level) or a Vector2 cell; a quarter of the view (320 x 180 art px), so one art px is four px.
func s_closeup(name, at) -> void:
	var pt: Vector2 = (at + Vector2(0.5, 0.5)) * 16.0 if at is Vector2 else Vector2((float(at[0]) + 0.5) * 16.0, (float(at[1]) + 0.5 - float(at[2])) * 16.0)
	await RenderingServer.frame_post_draw
	var img: Image = w.viewport.get_texture().get_image()
	var c: Vector2 = w.viewport.get_canvas_transform() * pt
	var r := Rect2i(Vector2i(clampi(int(c.x) - 160, 0, img.get_width() - 320), clampi(int(c.y) - 90, 0, img.get_height() - 180)), Vector2i(320, 180))
	var crop_img := img.get_region(r)
	crop_img.resize(1280, 720, Image.INTERPOLATE_NEAREST)
	crop_img.save_png(_png(name))

## The whole room at 1 art px: the world viewport grown to the room (plus the cliff rising over its first row) for a
## frame, the camera on the room's centre.
func whole_room(path: String) -> void:
	var size: Vector2 = w.room.art_size()
	var pad := 48
	w.set_process(false)
	w.container.stretch = false   # the viewport takes the room's size for a frame
	w.viewport.size = Vector2i(int(size.x), int(size.y) + pad)
	w.camera.position = Vector2(size.x * 0.5, (size.y - pad) * 0.5)
	w.camera.offset = Vector2.ZERO
	for f in 3: await frames(1)
	await RenderingServer.frame_post_draw
	w.viewport.get_texture().get_image().save_png(path)
	w.viewport.size = TopdownWorld.VIEW
	w.container.stretch = true
	w.set_process(true)
	await frames(2)

func s_whole_room(name = "*") -> void:
	await whole_room(_png(name))

## Images side by side (`cols` a row, each `k` times its size) under their titles, rendered in a viewport of their own.
func panels(path: String, items: Array, cols: int, k := 1) -> void:
	var gap := 12
	var title_h := 30
	var cw := 0
	var ch := 0
	for it in items:
		cw = maxi(cw, (it[1] as Image).get_width() * k)
		ch = maxi(ch, (it[1] as Image).get_height() * k)
	var rows := ceili(items.size() / float(cols))
	var vp := SubViewport.new()
	vp.size = Vector2i(cols * cw + (cols + 1) * gap, rows * (ch + title_h) + (rows + 1) * gap)
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(vp)
	var bg := ColorRect.new()
	bg.color = NIGHT_INK
	bg.size = Vector2(vp.size)
	vp.add_child(bg)
	for i in items.size():
		var at := Vector2(gap + (i % cols) * (cw + gap), gap + (i / cols) * (ch + title_h + gap))
		var label := Label.new()
		label.text = str(items[i][0])
		label.position = at
		label.add_theme_font_size_override("font_size", 18)
		label.add_theme_color_override("font_color", Color("E8E1CF"))
		vp.add_child(label)
		var img: Image = (items[i][1] as Image).duplicate()
		if k != 1: img.resize(img.get_width() * k, img.get_height() * k, Image.INTERPOLATE_NEAREST)
		var tr := TextureRect.new()
		tr.texture = ImageTexture.create_from_image(img)
		tr.position = at + Vector2(0, title_h)
		tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		vp.add_child(tr)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	vp.get_texture().get_image().save_png(path)
	vp.queue_free()

## Pictures side by side under their titles: [[title, picture of this set (a name) or of docs/ ("docs:<path>")]].
func s_panels(name, items: Array, cols: int, k := 1) -> void:
	var imgs: Array = []
	for it in items:
		var f := str(it[1])
		var path := _src(f.trim_prefix("docs:")) if f.begins_with("docs:") else out_dir + _name(f) + ".png"
		imgs.append([str(it[0]), Image.load_from_file(ProjectSettings.globalize_path(path))])
	await panels(_png(name), imgs, cols, k)

## Each view's before and after side by side, where both are there: `base` holds before/ and after/ (under docs/),
## the pairs go into `into` as <name>_before_after.png.
func s_pairs(base: String, into: String, names: Array, after_title: String) -> void:
	for n in names:
		var b := _src(base + "before/" + str(n) + ".png")
		var a := _src(base + "after/" + str(n) + ".png")
		if not (FileAccess.file_exists(b) and FileAccess.file_exists(a)): continue
		var path: String = docs + into + str(n).get_file() + "_before_after.png"
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
		await panels(path, [["Before", Image.load_from_file(ProjectSettings.globalize_path(b))],
			[after_title, Image.load_from_file(ProjectSettings.globalize_path(a))]], 2)

## Hold the stick at `axis` for `n` physics frames, pressing Jump / Dodge on the listed ones, and keep a 384x288 crop
## round the body at each frame in `keep_at`, side by side.
func s_strip(name, axis: Vector2, n: int, jumps: Array, dashes: Array, keep_at: Array) -> void:
	var tiles: Array = []
	for f in n + 1:
		if f in keep_at: tiles.append(await around(Vector2i(384, 288), Vector2i(192, 144), Vector2.ZERO, -40.0))
		if f == n: break
		p.movement = axis
		if f in jumps: p.jump()
		if f in dashes: p.dodge()
		await get_tree().physics_frame
		await get_tree().process_frame
	p.movement = Vector2.ZERO
	var img := Image.create(384 * tiles.size() + 4 * (tiles.size() - 1), 288, false, Image.FORMAT_RGBA8)
	img.fill(NIGHT_INK)
	for i in tiles.size(): img.blit_rect(tiles[i], Rect2i(0, 0, 384, 288), Vector2i(i * 388, 0))
	img.save_png(_png(name))

## `n` shots of the whole window `gap` frames apart from the step of `kind` of scene `id` on, side by side at half size.
func s_story_strip(name, id: String, kind: String, n: int, gap: int) -> void:
	await s_scene_at(id, kind, 0.0)
	var tiles: Array = []
	for i in n:
		await RenderingServer.frame_post_draw
		var img := get_tree().root.get_texture().get_image()
		img.resize(640, 360, Image.INTERPOLATE_BILINEAR)
		tiles.append(img)
		await frames(gap)
	var strip_img := Image.create(640 * n + 4 * (n - 1), 360, false, Image.FORMAT_RGBA8)
	strip_img.fill(NIGHT_INK)
	for i in n:
		tiles[i].convert(Image.FORMAT_RGBA8)
		strip_img.blit_rect(tiles[i], Rect2i(0, 0, 640, 360), Vector2i(i * 644, 0))
	strip_img.save_png(_png(name))

## Two pictures of this set side by side, 8 px apart on the night ink.
func s_pair_sheet(name, left: String, right: String) -> void:
	var a := Image.load_from_file(ProjectSettings.globalize_path(out_dir + _name(left) + ".png"))
	var b := Image.load_from_file(ProjectSettings.globalize_path(out_dir + _name(right) + ".png"))
	var img := Image.create(a.get_width() + b.get_width() + 8, a.get_height(), false, Image.FORMAT_RGBA8)
	img.fill(NIGHT_INK)
	img.blit_rect(a, Rect2i(Vector2i.ZERO, a.get_size()), Vector2i.ZERO)
	img.blit_rect(b, Rect2i(Vector2i.ZERO, b.get_size()), Vector2i(a.get_width() + 8, 0))
	img.save_png(_png(name))

## A piece of the window at an earlier picture of this set, cut and scaled (the route's close-up).
func s_cut(name, from: String, r: Rect2i, size: Vector2i) -> void:
	var img := Image.load_from_file(ProjectSettings.globalize_path(out_dir + _name(from) + ".png")).get_region(r)
	img.resize(size.x, size.y, Image.INTERPOLATE_NEAREST)
	img.save_png(_png(name))

## Where the staged bodies stand on the shots, for pairing a before and an after.
func s_boxes_json(name = "boxes") -> void:
	var f := FileAccess.open(ProjectSettings.globalize_path(_png(name, ".json")), FileAccess.WRITE)
	f.store_string(JSON.stringify(boxes, "  ", true))
	f.close()

# ------------------------------------------------------------------------------------------------------ running steps
## Run one step ([name, args...]), its string arguments filled in from the command line's variables.
func run_step(st: Array) -> Variant:
	var args: Array = []
	for a in st.slice(1): args.append(_fill(a))
	var fn := "s_" + str(st[0])
	if not has_method(fn):
		push_error("capture: no step %s" % str(st[0]))
		return null
	return await callv(fn, args)

## A whole-string "{key}" becomes the variable itself (a Vector2, a list); "{key}" inside a string, its text.
func _fill(a):
	if a is String and a.begins_with("{") and a.ends_with("}") and vars.has(a.substr(1, a.length() - 2)):
		return vars[a.substr(1, a.length() - 2)]
	if a is String and a.contains("{") and not a.contains("*"):
		var s: String = a
		for k in vars: s = s.replace("{%s}" % k, str(vars[k]))
		return s
	return a
