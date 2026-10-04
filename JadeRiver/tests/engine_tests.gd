extends "res://tests/lib/suite.gd"
## Engine tests (on the height grid since S12a retired the side view, whose World and player they drove): the looks the
## game names drawn by the top-down figure, the motor on a room of the world (TopdownMotor on Lotus Ferry's layout), the
## HUD's touches on the top-down player, the saves, and the character creator.
## A failed check is pushed as an error, and the summary reads "ENGINE_TESTS: passed/checks passed".
const Hud = preload("res://scripts/hud.gd")
const ROOM := "lf_village"
const CATS := ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]

func report_failure(what: String) -> void:
	push_error(what)
func summary_line() -> String:
	return "ENGINE_TESTS: %d/%d passed" % [checks - failures, checks]
func _main(): await run()

func run():
	looks()
	gauntlets()
	var grid := TopdownRoom.load_room(ROOM)
	check(grid.w > 0, "%s has its layout" % ROOM)
	walking(grid)
	stairs(grid)
	jumping(grid)
	solids(grid)
	sweeps(grid)
	await hud_touches()
	saves()
	creation()
	end_suite()

# ------------------------------------------------------------------ the looks
## Every look the catalogue names (data/parts.json: the creator's, the gear's, the people's) is drawn by the top-down
## figure (TopdownFigure.manifest), and every sheet it draws from is on disk.
func looks() -> void:
	var man := TopdownFigure.manifest()
	check(not man.is_empty(), "the top-down figure's manifest parses")
	for cat in CATS:
		for name in Wardrobe.parts.get(cat, {}):
			if str(name).begins_with("_") or str(name) == "none": continue
			var item: Dictionary = man.get("items", {}).get(cat, {}).get(str(name), {})
			check(not item.is_empty(), "the look %s:%s is drawn by the top-down figure" % [cat, name])
			for key in item.get("sheets", {}):
				var path := str(item.sheets[key])
				check(FileAccess.file_exists(path) or ResourceLoader.exists(path), "Asset exists: %s (%s:%s, %s)" % [path, cat, name, key])
	check(Wardrobe.validate({"hair": "invalid", "name": ""}).hair == "topknot", "Invalid appearance recovers")

## Every gauntlet wears a look the top-down figure draws, and the gauntlets' combo plays drawn actions.
func gauntlets() -> void:
	var man := TopdownFigure.manifest()
	var looks := {}
	for a in ContentDB.all("artifacts"):
		if str(a.get("family", "")) != "gauntlets": continue
		looks[str(a.get("appearance", ""))] = true
	check(looks.size() > 0 and not looks.has("none"), "gauntlets are drawn, not bare fists (%s)" % str(looks.keys()))
	for look in looks:
		check((man.items.get("weapon", {}) as Dictionary).has(look), "gauntlets %s are drawn by the top-down figure" % look)
	for step in ContentDB.entry("weapon_families", "gauntlets").get("combo", []):
		var act := TopdownFigure.resolve(str(step.action), "gauntlets")
		check((man.actions as Dictionary).has(act) and act != "idle", "the gauntlets' %s plays a drawn action (%s)" % [step.action, act])

# ------------------------------------------------------------------ the motor on a room of the world
## Held input for `seconds` at 60 frames a second.
func hold(m: TopdownMotor, axis: Vector2, seconds: float, jump_first := false) -> void:
	for i in int(ceil(seconds * 60.0)): m.step(1.0 / 60.0, axis, jump_first and i == 0)

## The body stands on a cell it may: inside the room, on no solid prop, its foot box clear.
func clear_stand(grid: TopdownRoom, m: TopdownMotor) -> bool:
	return m.pos.is_finite() and is_finite(m.z) and not m.blocked_at(m.pos) and grid.inside(TopdownRoom.cell_of(m.pos).x, TopdownRoom.cell_of(m.pos).y)

func walking(grid: TopdownRoom) -> void:
	var m := TopdownMotor.new(grid)
	var start := m.pos
	hold(m, Vector2.RIGHT, 1.0)
	check(m.pos.x > start.x + 100.0 and m.grounded and clear_stand(grid, m), "the body walks the street from where a character wakes (%s to %s)" % [str(start), str(m.pos.round())])
	m.place(grid.spawn)
	var a := m.pos
	hold(m, Vector2.RIGHT, 0.1)
	var unit := m.pos.distance_to(a)
	m.place(grid.spawn)
	hold(m, Vector2(99, 99), 0.1)
	check(m.pos.distance_to(a) <= unit + 0.5, "Oversized input cannot increase movement speed (%.1f, a full push %.1f)" % [m.pos.distance_to(a), unit])
	# The same input replayed moves two bodies the same way.
	var one := TopdownMotor.new(grid)
	var two := TopdownMotor.new(grid)
	for i in 240:
		var axis := Vector2(cos(i * 0.05), sin(i * 0.05))
		one.step(1.0 / 60.0, axis, i % 50 == 0)
		two.step(1.0 / 60.0, axis, i % 50 == 0)
	check(one.pos == two.pos and one.z == two.z and one.vel == two.vel, "Identical input replay produces identical motion (%s, %s)" % [str(one.pos), str(two.pos)])
	# A frame of any length steps in the motor's own substeps: the same walk lands in the same place.
	var paces := []
	for dt in [1.0 / 30.0, 1.0 / 60.0, 1.0 / 120.0]:
		var mm := TopdownMotor.new(grid)
		for i in int(round(1.0 / dt)): mm.step(dt, Vector2.RIGHT)
		paces.append(mm.pos)
	check(paces[0].distance_to(paces[1]) < 1.0 and paces[1].distance_to(paces[2]) < 1.0, "a walk at 30, 60 and 120 frames a second ends in the same place (%s)" % str(paces))

func stairs(grid: TopdownRoom) -> void:
	check(not grid.stairs.is_empty(), "%s has stairs" % ROOM)
	if grid.stairs.is_empty(): return
	var s: Dictionary = grid.stairs[0]
	var r: Rect2i = s.rect
	var foot := Vector2((r.position.x + r.size.x * 0.5) * TopdownRoom.TILE, (r.end.y + 0.6) * TopdownRoom.TILE)
	var m := TopdownMotor.new(grid, grid.nearest_standable(foot))
	var low := m.z
	var worst := 0.0
	var last := m.z
	for i in 120:
		m.step(1.0 / 60.0, Vector2.UP)
		worst = maxf(worst, absf(m.z - last))
		last = m.z
	check(m.z >= low + float(s.to - s.from) * TopdownRoom.LEVEL - 0.5 and m.grounded and worst <= TopdownRoom.LEVEL * 0.5,
		"Stairs connect the lower floor to the raised one, rising continuously (%.0f to %.0f, most %.1f a frame)" % [low, m.z, worst])
	worst = 0.0
	for i in 120:
		m.step(1.0 / 60.0, Vector2.DOWN)
		worst = maxf(worst, absf(m.z - last))
		last = m.z
	check(absf(m.z - low) < 0.5 and m.grounded and worst <= TopdownRoom.LEVEL * 0.5, "Stairs descend continuously to the lower floor (%.0f)" % m.z)

func jumping(grid: TopdownRoom) -> void:
	var m := TopdownMotor.new(grid)
	var still := 0.0
	var peaks := []
	for axis in [Vector2.ZERO, Vector2.UP, Vector2.DOWN]:
		m.place(grid.spawn)
		var base := m.z
		var top := base
		for i in 48:
			m.step(1.0 / 60.0, axis * 0.2, i == 0)
			top = maxf(top, m.z)
		peaks.append(snappedf(top - base, 0.5))
		if axis == Vector2.ZERO: still = top - base
	check(absf(still - m.apex()) < 2.0, "a jump rises to its apex (%.1f, the motor's %.1f)" % [still, m.apex()])
	check(peaks.all(func(p): return absf(float(p) - float(peaks[0])) < 1.0), "Jump height is independent of moving up or down the screen (%s)" % str(peaks))
	m.place(grid.spawn)
	hold(m, Vector2.ZERO, 1.0, true)
	check(m.grounded and absf(m.z - grid.floor_at(m.pos)) < 0.5, "a jump lands back on its floor")

## Every solid prop of the room stops a body pushed at it from each side, at any frame rate, and never lets it in.
func solids(grid: TopdownRoom) -> void:
	var tested := 0
	for p in grid.props:
		if not p.art.get("solid", true): continue
		var fp := Rect2(Vector2(p.cell) * TopdownRoom.TILE, Vector2(p.size) * TopdownRoom.TILE)
		for d in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
			var from: Vector2 = fp.get_center() - d * (maxf(fp.size.x, fp.size.y) * 0.5 + TopdownRoom.TILE * 1.5)
			var c := TopdownRoom.cell_of(from)
			if not grid.standable(c) or absf(grid.cell_floor(c) - float(p.level) * TopdownRoom.LEVEL) > 0.5: continue
			for dt in [1.0 / 30.0, 1.0 / 60.0, 0.2]:
				var m := TopdownMotor.new(grid, from)
				var inside := false
				var top := float(p.get("top", -1)) * TopdownRoom.LEVEL   # a prop with a standable top may be stood on
				for i in int(ceil(1.2 / dt)):
					m.step(dt, d)
					if Rect2(m.pos - m.half, m.half * 2.0).intersects(fp.grow(-0.5)) and (int(p.get("top", -1)) < 0 or m.z < top - 0.5): inside = true
				check(not inside, "Solid %s at %s stops a body pushed at it from the %s at dt %.3f" % [p.kind, str(p.cell), str(-d), dt])
			tested += 1
	check(tested >= 40, "%d pushes at %s's solid props" % [tested, ROOM])

## From standable cells across the room, eight directions held for four seconds keep the body finite, on its floor and
## out of every solid.
func sweeps(grid: TopdownRoom) -> void:
	var ok := true
	var swept := 0
	for y in range(1, grid.h - 1, 4):
		for x in range(1, grid.w - 1, 4):
			var c := Vector2i(x, y)
			if not grid.standable(c): continue
			for d in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN, Vector2(1, 1).normalized(), Vector2(-1, 1).normalized(), Vector2(1, -1).normalized(), Vector2(-1, -1).normalized()]:
				var m := TopdownMotor.new(grid, TopdownRoute.centre(c))
				for i in 240:
					m.step(1.0 / 60.0, d)
					if m.sink_t >= 0.0: continue   # a step into the water: the body is set back on its last safe spot
					ok = ok and m.pos.is_finite() and is_finite(m.z) and not m.blocked_at(m.pos) and (not m.grounded or absf(m.z - grid.floor_at(m.pos)) < 0.5 or m.ride != "")
				swept += 1
	check(ok and swept > 200, "All eight-direction sweeps keep finite, supported positions out of every solid (%d sweeps)" % swept)

# ------------------------------------------------------------------ the HUD's touches on the top-down player
func hud_touches() -> void:
	var was: String = Game.active_id
	Game.active_id = ""   # the prototype room's view alone, its own body
	var w := TopdownWorld.new()
	add_child(w)
	await get_tree().process_frame
	var p = w.player
	var hud = Hud.new()
	hud.player = p
	add_child(hud)
	hud.set_process(false)
	hud.press(1, Vector2(200, 500))
	hud.drag(1, Vector2(276, 500))
	check(p.joystick_engaged and p.movement.x == 1.0, "The joystick held right moves the body right (%s)" % str(p.movement))
	hud.press(2, hud.jump_center)
	check(p.movement.x == 1.0, "Multi-touch jump preserves movement")
	hud.release(2)
	check(p.movement.x == 1.0, "Action release preserves joystick")
	hud.release(1)
	check(p.movement == Vector2.ZERO and not p.joystick_engaged, "Release stops the body")
	hud.press(1, Vector2(200, 500))
	hud.drag(1, Vector2(205, 500))
	check(p.movement == Vector2.ZERO, "The joystick's dead zone holds the body still")
	hud.release(1)
	# The technique page turns (a swipe on a slot aims its art on the grid: the page turns by its own control).
	hud.scroll_skills(-1)
	check(hud.skill_page == 1 and hud.scroll_progress == 0, "A page turn starts a visible page transition")
	hud.advance_scroll(0.15)
	check(hud.scroll_progress > 0 and hud.scroll_progress < 1, "Skill scroll has intermediate frames")
	hud.advance_scroll(0.3)
	check(hud.scroll_progress == 1, "Skill scroll finishes")
	hud.scroll_skills(1)
	check(hud.skill_page == 0 and hud.scroll_direction == 1, "Turning back reverses the animation")
	hud.press(1, Vector2(200, 500))
	hud.drag(1, Vector2(276, 500))
	hud._notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(p.movement == Vector2.ZERO and hud.touches.is_empty(), "Focus loss clears held controls")
	hud.free()
	w.free()
	Game.active_id = was

# ------------------------------------------------------------------ saves
## Saves (Part 5 · format v3) use their own folder and never touch real player data.
func saves() -> void:
	var old_repo = Saves.repo
	Saves.use_folder(run_root() + "saves/")
	Saves.repo.wipe()
	var hero = GameCharacter.new()
	hero.slot = 2
	hero.id = "c2"
	hero.name = "Azure Disciple"
	hero.appearance = {"body": "light", "hair": "topknot", "hair_color": 4, "shirt": "cardigan", "pants": "loose", "shoes": "boots"}
	hero.position = {"room": "lf_village", "portal": "", "x": 1290.0, "y": 650.0, "facing": -1}
	hero.pools.hp = 78
	check(Saves.save_character(2, hero.snapshot()) == OK, "Character save succeeds")
	var loaded = Saves.load_character(2)
	var again = GameCharacter.new()
	again.restore(loaded)
	check(again.name == "Azure Disciple" and int(again.appearance.hair_color) == 4 and again.position.room == "lf_village" and is_equal_approx(float(again.position.x), 1290.0), "Appearance, dye and position round-trip")
	Saves.save_character(2, again.snapshot())
	check(JSON.stringify(Saves.load_character(2)) == JSON.stringify(loaded), "Save, load, save again is lossless")
	hero.name = "Second Save"
	Saves.save_character(2, hero.snapshot())
	var f = FileAccess.open(Saves.repo.character_path(2), FileAccess.WRITE)
	f.store_string("not a save")
	f.close()
	check(Saves.load_character(2).get("name", "") == "Azure Disciple" and Saves.recovered_files().has("char_2.json"), "Damaged save recovers from its backup")
	check(Saves.load_character(1).is_empty() and Saves.load_character(3).is_empty(), "Other slots remain independent")
	var legacy = Wardrobe.defaults()
	legacy.hair_color = 3
	legacy.erase("sect")
	var migrated = Saves.migrate_v2_slots([legacy, null, {"hair": "invalid", "name": "Old Friend"}])
	check(migrated.size() == 2 and int(migrated[0].appearance.hair_color) == 3 and migrated[0].migrated_v2, "Version 2 appearance slots migrate to v3 characters")
	check(migrated[1].appearance.hair == "topknot" and migrated[1].name == "Old Friend", "Invalid v2 appearance recovers to defaults")
	check(RepositoryLocal.new(Saves.repo.character_path(2) + "/").save_character(1, {"version": 3}) != OK, "Failed write reports an error")
	Saves.repo.wipe()
	Saves.repo = old_repo

# ------------------------------------------------------------------ the creator
func creation() -> void:
	var main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	main.preview_mode = true
	main.show_creation(0)
	check(main.dye_buttons.size() == 6, "Creation offers six hair dyes")
	check(main.preview is ShellScreens.TopdownPreview, "The creator previews the top-down figure")
	main.set_hair_dye(2)
	check(main.draft.hair_color == 2 and int(main.preview.outfit.hair_color) == 2, "Dye updates the live preview")
	var before = main.draft.hair
	main.cycle("hair", 1)
	check(main.draft.hair != before and main.draft.hair_color == 2 and str(main.preview.outfit.hair) == str(main.draft.hair), "Hair style changes preserve dye")
	var creator = main.creator
	var first_origin = creator.origin
	main.cycle("origin", 1)
	check(creator.origin != first_origin, "Origin choice works")
	main.show_selection()
	check(main.screen == "selection", "Cancel returns safely")
	main.free()
