extends Node
## Screenshots and frame strips of the top-down prototype room (redesign Phase 1) for docs/redesign/phase1/: the square
## under the HUD, walking behind the house, jumping the pier's gap and the long jump, and standing on the low wall with
## the shadow in the air. It plays the real room through the HUD's own player fields on its own saves. `-- --phase4`:
## a top-down character's game, every room converted in Phase 4 and a quest talk (docs/redesign/phase4/); `-- --chapter2`:
## the rooms of chapter 2's stretch (Phase 4's second part) with their foes, into the same folder; `-- --tutorial-foes`:
## the tutorial rooms' eel, minnows, Old Snapper and mossback toads in their own figures, into it too. `-- --combat`:
## decision 38's combat feel in the game (docs/redesign/phase5/combat/). `-- --first-boss`: decision 45's first boss, its
## waking and the elders' rescue (docs/redesign/feedback/first_boss/). `-- --decision42` and `-- --decision42-route`:
## the prototype feedback's weave, sprint and auto-path (docs/redesign/feedback/combat/). `-- --quality
## --quality-tag=<before|after>`: decision 42's character drawn better, the same instants before and after the rollout
## (docs/redesign/feedback/character_quality/rollout/). `-- --people-scale --people-tag=<before|after>`: decision 43's
## people drawn bigger, the same instants before and after (docs/redesign/feedback/people_scale/). `-- --terrain
## <name>`: the Terrain v2 review views (docs/redesign/art_bible.md "Terrain v2"), the world alone at x2, into
## docs/redesign/terrain_v2/<name>/ (on saves of their own, so it can run beside another capture). `-- --light
## --light-tag=<before|after>`: decision 40's runtime light, the key rooms by day, at dusk and at night, into
## docs/redesign/terrain_v2/light/. `-- --life --life-tag=<before|after>`: decision 43's living world, into
## docs/redesign/feedback/living_world/. Every mode shoots at midday of the game's clock (TopdownLight.debug_hour)
## unless it names its hour.
## Needs a renderer:
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/topdown_capture.tscn

const OUT := "res://docs/redesign/phase1/"
## Phase 3's height test: where the bodies stand in td_review_heights (cells): the square, the stone terrace, the grass
## terrace, the roof built on the grid, the courtyard wall, the pier, the cliff top.
const HEIGHT_BODIES := [Vector2(11.5, 13.6), Vector2(9.5, 8.6), Vector2(6.5, 5.6), Vector2(5.5, 11.2), Vector2(16.0, 12.6),
	Vector2(22.9, 16.4), Vector2(4.5, 1.8)]
const SAVES := "user://topdown_capture_saves/"
var main
var w
var p
var m: TopdownMotor

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var saves := SAVES if not "--terrain" in OS.get_cmdline_user_args() else "user://terrain_capture_saves/"
	if "--night" in OS.get_cmdline_user_args(): saves = "user://night_capture_saves/"   # on its own saves, beside another capture
	if "--first-boss" in OS.get_cmdline_user_args(): saves = "user://first_boss_capture_saves/"
	if "--quality" in OS.get_cmdline_user_args(): saves = "user://quality_capture_saves/"
	if "--people-scale" in OS.get_cmdline_user_args(): saves = "user://people_scale_capture_saves/"
	if "--monsters" in OS.get_cmdline_user_args(): saves = "user://monsters_capture_saves/"
	if "--life" in OS.get_cmdline_user_args(): saves = "user://life_capture_saves/"
	if "--work-poses" in OS.get_cmdline_user_args(): saves = "user://work_poses_capture_saves/"
	if "--sand-snow" in OS.get_cmdline_user_args(): saves = "user://sand_snow_capture_saves/"
	DirAccess.make_dir_recursive_absolute(saves)
	for f in DirAccess.get_files_at(saves): DirAccess.remove_absolute(saves + f)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	TopdownLight.debug_hour = 0.375   # decision 40: every shot at midday, whatever the clock says
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(saves)
	Game.boot()
	Game.autosave_enabled = false
	if "--terrain" in OS.get_cmdline_user_args():
		await terrain_v2()
		return
	if "--phase4" in OS.get_cmdline_user_args():
		await phase4()
		return
	if "--story" in OS.get_cmdline_user_args():
		await story()
		return
	if "--night" in OS.get_cmdline_user_args():
		await hollow_night()
		return
	if "--first-boss" in OS.get_cmdline_user_args():
		await first_boss()
		return
	if "--chapter2" in OS.get_cmdline_user_args():
		await chapter2()
		return
	if "--light" in OS.get_cmdline_user_args():
		await light()
		return
	if "--life" in OS.get_cmdline_user_args():
		await life()
		return
	if "--work-poses" in OS.get_cmdline_user_args():
		await work_poses()
		return
	if "--sand-snow" in OS.get_cmdline_user_args():
		await sand_snow()
		return
	if "--tutorial-foes" in OS.get_cmdline_user_args():
		await tutorial_foes()
		return
	if "--decision42-route" in OS.get_cmdline_user_args():
		await decision42_route()
		return
	if "--quality" in OS.get_cmdline_user_args():
		await quality()
		return
	if "--people-scale" in OS.get_cmdline_user_args():
		await people_scale()
		return
	if "--monsters" in OS.get_cmdline_user_args():
		await monsters()
		return
	main.enter_topdown_proto(false)
	w = main.world
	p = w.player
	m = p.motor
	await frames(40)
	if "--phase2" in OS.get_cmdline_user_args():
		await phase2()
		return
	if "--phase3" in OS.get_cmdline_user_args():
		await phase3()
		return
	if "--drag-moves" in OS.get_cmdline_user_args():
		await drag_moves()
		return
	if "--combat" in OS.get_cmdline_user_args():
		await combat()
		return
	if "--decision42" in OS.get_cmdline_user_args():
		await decision42()
		return
	if "--character" in OS.get_cmdline_user_args():
		await character()
		return
	await shot("01_square")
	# Walking behind the house, west to east along the lane on its north side.
	var house: Dictionary = w.room.props.filter(func(q): return q.kind == "house")[0]
	var hc: Vector2i = house.cell
	await start(Vector2((hc.x - 1.5) * 32.0, (hc.y - 1) * 32.0 + 8.0))
	await strip("02_behind_house_strip", Vector2.RIGHT, 84, [], [], [0, 24, 42, 60, 84])
	await start(Vector2((hc.x + 3.5) * 32.0, (hc.y - 1) * 32.0 + 8.0))
	await shot("02_behind_house")
	# The pier: a running jump over the one-tile gap, then dash and Jump over the three tiles to the landing stage.
	await start(Vector2(19.5 * 32.0, 23.4 * 32.0))
	await strip("03_gap_strip", Vector2.DOWN, 40, [6], [], [0, 10, 18, 26, 40])
	await start(Vector2(20.2 * 32.0, 27.0 * 32.0))
	await strip("04_long_jump_strip", Vector2.RIGHT, 48, [8], [1], [0, 9, 20, 32, 48])
	# The low wall: a jump from the square onto it, the shadow left on the floor below, then standing on top.
	await start(Vector2(30.5 * 32.0, 19.6 * 32.0))
	await strip("05_upper_level_strip", Vector2.UP, 30, [2], [], [0, 8, 16, 24, 30])
	p.movement = Vector2.ZERO
	await frames(30)
	await shot("05_on_the_low_wall")
	print("topdown_capture: done")
	get_tree().quit()

## Phase 2 (`-- --phase2`, into docs/redesign/phase2/): a fight with three foes, a technique, the rooftop jump, the
## water's edge, and an aimed attack and an aimed technique with the HUD's thumb held on the button.
func phase2() -> void:
	var out := "res://docs/redesign/phase2/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var hud = main.hud
	var c = Game.active()
	var base := Vector2(22.5, 19.0) * 32.0
	# A fight with three foes: a crab, a rat and a boarlet round the player, the fight ring out.
	await arena(base, [["mudshell_crab", Vector2(-52, 10)], ["reedtail_rat", Vector2(46, -22)], ["wild_boarlet", Vector2(20, 44)]])
	for f in 40:
		c.pools.hp = c.pools.max_hp
		if f % 14 == 0: p.attack()
		await frames(1)
	await shot("01_fight_three_foes", out)
	# A technique: the rolling wave (a line) cast along the aim at two foes, as a strip.
	await arena(base, [["wild_boarlet", Vector2(90, 10)], ["mudshell_crab", Vector2(170, -6)]])
	c.pools.cooldowns.clear()
	p.aim_technique(1, Vector2.RIGHT)
	await strip("02_technique_strip", Vector2.ZERO, 36, [], [], [0, 8, 16, 24, 36], out)
	c.pools.cooldowns.clear()
	await arena(base, [["wild_boarlet", Vector2(100, 0)], ["mudshell_crab", Vector2(120, 30)]])
	p.aim_technique(2, Vector2.RIGHT, 0.55)
	await frames(18)
	await shot("02_technique", out)
	# The rooftop: from the terrace a jump onto the storehouse's roof, across it, and a jump off it down to the square.
	var sh: Dictionary = w.room.props.filter(func(q): return q.kind == "storehouse")[0]
	await arena((Vector2(sh.cell) + Vector2(1.5, -1.0)) * 32.0, [])
	await strip("03_rooftop_jump_strip", Vector2.DOWN, 96, [6, 60], [], [0, 14, 30, 50, 66, 96], out)
	# The water's edge: a walk stops at the bank.
	await arena(Vector2(10.5 * 32.0, 20.0 * 32.0), [])
	await strip("04_water_edge_strip", Vector2.DOWN, 60, [], [], [0, 20, 40, 60], out)
	# Aimed: Attack held and dragged toward a foe (it snaps), then a technique's circle dragged to a point.
	await arena(base, [["wild_boarlet", Vector2(70, -20)], ["reedtail_rat", Vector2(-60, 40)]])
	hud.set_state(true)
	hud.press(90, hud.attack_center)
	hud.drag(90, hud.attack_center + Vector2(80, -30))
	await frames(16)
	await shot("05_aimed_attack", out)
	hud.release(90)
	await frames(30)
	hud.press(91, hud.slots[2])
	hud.drag(91, hud.slots[2] + Vector2(70, -70))
	await frames(16)
	await shot("06_aimed_technique", out)
	hud.release(91)
	print("topdown_capture: phase 2 done")
	get_tree().quit()

## Phase 3 (`-- --phase3`, into docs/redesign/phase3/; docs/redesign/art_bible.md §12): Riverside Square as the game
## draws it. The world at the spawn camera (x2, and under the HUD), the whole room, the approved mock beside the loader
## before and after, the water's four frames, a fight with the new foes, and the height-levels test room in colour
## and by value alone.
func phase3() -> void:
	var out := "res://docs/redesign/phase3/"
	var hud = main.hud
	await start(w.room.spawn)
	for f in 20: await frames(1)   # the camera settles
	var world_x2 := await world_shot()
	world_x2.save_png(out + "08_ingame_square_x2.png")
	await shot("09_ingame_square_hud", out)
	await whole_room(out + "10_ingame_whole_room.png")
	var mock := Image.load_from_file(ProjectSettings.globalize_path(out + "01_square_mock_x2.png"))
	var before := Image.load_from_file(ProjectSettings.globalize_path(out + "07_ingame_square.png"))
	await panels(out + "11_before_after.png", [["The approved mock (Phase 3 art, the target)", mock], ["Before: the loader with the new tiles, no auto-tiles, rims or shadows", before],
		["After: in the game, the room redesigned, with bamboo, lotus pond and lanterns", world_x2]], 1)
	# The water's four frames round the pond and the pier, 250 ms apart, with the square cleared so nothing moves.
	await arena(w.room.spawn, [])
	var water: Array = []
	for f in 4:
		await get_tree().create_timer(0.25).timeout
		await RenderingServer.frame_post_draw
		var img: Image = w.viewport.get_texture().get_image()
		water.append(["frame %d" % f, img.get_region(Rect2i(100, 170, 300, 170))])
	await panels(out + "15_water_frames_x2.png", water, 2, 2)
	# A fight with the new foes: two crabs, a rat and a boarlet round the player, blows going in.
	var c = Game.active()
	var base := Vector2(22.5, 19.0) * 32.0
	await arena(base, [["mudshell_crab", Vector2(-120, 20)], ["reedtail_rat", Vector2(120, -50)], ["wild_boarlet", Vector2(70, 110)], ["mudshell_crab", Vector2(-40, -110)]])
	for f in 16:
		c.pools.hp = c.pools.max_hp
		if f == 6: p.aim_attack(Vector2.LEFT)
		await frames(1)
	await shot("13_fight_hud", out)
	# The same moment in the world alone, x4 round the player.
	await RenderingServer.frame_post_draw
	var vi: Image = w.viewport.get_texture().get_image()
	var at: Vector2i = Vector2i(p.screen - w.camera.position + Vector2(320, 180)) - Vector2i(160, 100)
	var fight := vi.get_region(Rect2i(at.clamp(Vector2i.ZERO, Vector2i(320, 180)), Vector2i(320, 180)))
	fight.resize(1280, 720, Image.INTERPOLATE_NEAREST)
	fight.save_png(out + "14_fight_x4.png")
	hud.visible = true
	await height_test(out + "06_height_levels_test.png")
	print("topdown_capture: phase 3 done")
	get_tree().quit()

## The world viewport alone (no HUD), x2.
func world_shot() -> Image:
	await RenderingServer.frame_post_draw
	var img: Image = w.viewport.get_texture().get_image()
	img.resize(img.get_width() * 2, img.get_height() * 2, Image.INTERPOLATE_NEAREST)
	return img

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
	bg.color = Color("071015")
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

## The height-levels readability test (art bible §5): the room td_review_heights (levels -1/2 to 4, a house built on the
## grid, a courtyard wall, stairs, a pier) drawn by the game, a body standing on each level, in colour and by value alone.
func height_test(path: String) -> void:
	var was: String = Game.active_id
	Game.active_id = ""   # the view alone: no character enters the review room
	var v := TopdownWorld.new()
	v.room_id = "td_review_heights"
	add_child(v)
	await frames(2)
	v.set_process(false)
	var size: Vector2 = v.room.art_size()
	var pad := 64
	v.container.stretch = false
	v.viewport.size = Vector2i(int(size.x), int(size.y) + pad)
	v.camera.position = Vector2(size.x * 0.5, (size.y - pad) * 0.5)
	v.player.motor.place(HEIGHT_BODIES[0] * 32.0)
	v.player.sync(0.0)
	v.shadow.sync()
	for spot in HEIGHT_BODIES.slice(1): v.sorted.add_child(StandIn.new(v, spot * 32.0))
	for f in 3: await frames(1)
	await RenderingServer.frame_post_draw
	var img: Image = v.viewport.get_texture().get_image()
	var grey := img.duplicate()
	for y in grey.get_height():
		for x in grey.get_width():
			var c: Color = grey.get_pixel(x, y)
			var l: float = c.r * 0.299 + c.g * 0.587 + c.b * 0.114
			grey.set_pixel(x, y, Color(l, l, l, c.a))
	await panels(path, [["In colour", img], ["By value alone", grey]], 2, 2)
	v.queue_free()
	Game.active_id = was
	await frames(1)

## A body standing on the grid for the height test: the player's own frame and shadow drawn at another spot, sorted
## like it.
class StandIn extends TopdownWorld.Sorted:
	var feet := Vector2.ZERO
	func _init(w, at: Vector2) -> void:
		super(w)
		var z: float = w.room.height_at(at)
		feet = TopdownWorld.to_screen(at, z).round()
		key(w.room.sort_key(at, z))
		position.x = feet.x
	func _draw() -> void:
		TopdownWorld.draw_blob(self, 0.0, feet.y - position.y, 8.0, 0.55)
		world.player.draw_body(self, Vector2(0, feet.y - position.y))

## Decision 35 (`-- --drag-moves`, into docs/redesign/drag_moves/): Attack's drag moves armed under the thumb, each with
## its mark on the button and on the ground: the finisher (a long drag), the Plunge (a drag down in the air) and its
## impact, and the guard (held still).
func drag_moves() -> void:
	var out := "res://docs/redesign/drag_moves/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var hud = main.hud
	var c = Game.active()
	var base := Vector2(22.5, 19.0) * 32.0
	await arena(base, [["wild_boarlet", Vector2(-56, -44)], ["reedtail_rat", Vector2(64, 36)]])
	hud.set_state(true)
	hud.press(90, hud.attack_center)
	hud.drag(90, hud.attack_center + Vector2(-100, -80))
	await frames(12)
	await shot("01_finisher_armed", out)
	hud.release(90)
	await frames(40)
	if not c.cultivator.secret_arts.has("plunge"): c.cultivator.secret_arts.append("plunge")
	await arena(base, [["wild_boarlet", Vector2(34, 12)], ["mudshell_crab", Vector2(-36, 18)]])
	hud.set_state(true)
	p.jump()
	await frames(5)
	hud.press(91, hud.attack_center)
	hud.drag(91, hud.attack_center + Vector2(0, 80))
	await frames(2)
	await shot("02_plunge_armed", out)
	hud.release(91)
	await frames(4)
	await shot("03_plunge_impact", out)
	await frames(40)
	await arena(base, [["wild_boarlet", Vector2(44, 0)]])
	hud.set_state(true)
	m.face(Vector2.RIGHT)
	hud.press(92, hud.attack_center)
	await frames(24)
	await shot("04_guard", out)
	hud.release(92)
	print("topdown_capture: drag moves done")
	get_tree().quit()

## Decision 38 (`-- --combat`, into docs/redesign/phase5/combat/): the combat feel in the game. A combo of each of a few
## weapon families as frame strips round the body (the smears in their directions, the impacts, the hit-stop's held
## frames, the knockback's hop), the dragged finisher, each slotted technique's form on the ground plane, the guard and a
## parry, and the Plunge's landing; each strip reads left to right like the frames of a GIF.
func combat() -> void:
	var out := "res://docs/redesign/phase5/combat/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var hud = main.hud
	var c = Game.active()
	var base := Vector2(22.5, 19.0) * 32.0
	hud.visible = false
	var sturdy := func(e: EnemyState) -> void:
		e.pools.max_hp = 1.0e12
		e.pools.hp = e.pools.max_hp
	for fam in ["jian", "fists", "spear", "heavy_sabre", "brush", "bell"]:
		c.inventory.equipped["weapon"] = null if fam == "fists" else LootRules.make_instance("training_" + fam, 1, "common", null, 900)
		Game.combat.refresh_stats(c.id)
		await arena(base, [["wild_boarlet", Vector2(46, 18)], ["mudshell_crab", Vector2(40, -24)]])
		for e in Game.room_rt.enemies.values(): sturdy.call(e)
		m.face(Vector2(1, 0.3))
		var tiles: Array = []
		for f in 64:
			if f in [0, 18, 36]: p.aim_attack(Vector2(1, 0.25))
			if f % 3 == 1 and tiles.size() < 16: tiles.append(await crop(192, 144))
			await get_tree().physics_frame
			await get_tree().process_frame
		sheet(out + "ingame_combo_%s.png" % fam, tiles, 8)
	c.inventory.equipped["weapon"] = LootRules.make_instance("training_jian", 1, "common", null, 901)
	Game.combat.refresh_stats(c.id)
	# The dragged finisher (the charged blow) and a dash attack, toward the camera and away from it.
	await arena(base, [["wild_boarlet", Vector2(0, 46)], ["wild_boarlet", Vector2(0, -52)]])
	for e in Game.room_rt.enemies.values(): sturdy.call(e)
	var tiles2: Array = []
	for f in 70:
		if f == 0: p.finisher(Vector2.DOWN)
		if f == 36: p.dodge()
		if f == 40: p.aim_attack(Vector2.UP)
		if f % 4 == 1 and tiles2.size() < 16: tiles2.append(await crop(192, 144))
		p.movement = Vector2.UP * 0.9 if f >= 34 and f < 40 else Vector2.ZERO
		await get_tree().physics_frame
		await get_tree().process_frame
	sheet(out + "ingame_finisher_and_dash_attack.png", tiles2, 8)
	# Each slotted technique (a flurry, a wave, a burst, a seeker) toward a different direction, at its contact, with the
	# bare hands the prototype's loadout is made for.
	c.inventory.equipped["weapon"] = null
	Game.combat.refresh_stats(c.id)
	var panels_img: Array = []
	var aims := [Vector2(1, 0.4), Vector2(0.2, 1), Vector2.ZERO, Vector2(-1, -0.3)]
	for slot in 4:
		await arena(base, [["wild_boarlet", Vector2(70, 20)], ["mudshell_crab", Vector2(-60, -30)], ["reedtail_rat", Vector2(10, 70)]])
		for e in Game.room_rt.enemies.values(): sturdy.call(e)
		c.pools.cooldowns.clear()
		c.pools.qi = c.pools.max_qi
		var d: Vector2 = aims[slot] if aims[slot] != Vector2.ZERO else Vector2.RIGHT
		p.aim_technique(slot, d.normalized(), 0.6)
		for f in 14: await frames(1)
		panels_img.append(await crop(480, 300))
	sheet(out + "ingame_techniques.png", panels_img, 2)
	# The guard's wall of qi, then a parry caught in its window; and the Plunge's landing.
	var marks: Array = []
	await arena(base, [["wild_boarlet", Vector2(40, 0)]])
	m.face(Vector2.RIGHT)
	Game.submit({"type": "guard_start"})
	await frames(6)
	marks.append(await crop(192, 144))
	var striker: EnemyState = Game.room_rt.enemies.values()[0]
	striker.aim = Vector2.LEFT
	Game.submit({"type": "guard_end"})
	Game.submit({"type": "guard_start"})
	Game.combat.enemy_strike(striker, striker.def.attacks[0])
	GameEvents.flush()
	await frames(2)
	marks.append(await crop(192, 144))
	Game.submit({"type": "guard_end"})
	if not c.cultivator.secret_arts.has("plunge"): c.cultivator.secret_arts.append("plunge")
	await arena(base, [["wild_boarlet", Vector2(34, 12)], ["mudshell_crab", Vector2(-36, 18)]])
	p.jump()
	await frames(6)
	p.plunge()
	for f in 5: await frames(1)
	marks.append(await crop(192, 144))
	await frames(4)
	marks.append(await crop(192, 144))
	sheet(out + "ingame_guard_parry_plunge.png", marks, 4)
	hud.visible = true
	print("topdown_capture: combat done")
	get_tree().quit()

## Decision 42 (`-- --decision42`, into docs/redesign/feedback/combat/): the weave in the prototype room, basic attack,
## technique, basic attack, each pressed early and cutting the last one's recovery once its blow has landed, as labelled
## frames round the body (every fifth frame, 1/12 s apart) for the bare hands and the jian; then the sprint (the stick
## pushed) and the light touch's walk as strips.
func decision42() -> void:
	var out := "res://docs/redesign/feedback/combat/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var hud = main.hud
	var c = Game.active()
	var base := Vector2(22.5, 19.0) * 32.0
	hud.visible = false
	for fam in ["fists", "jian"]:
		c.inventory.equipped["weapon"] = null if fam == "fists" else LootRules.make_instance("training_" + fam, 1, "common", null, 900)
		Game.combat.refresh_stats(c.id)
		await arena(base, [["wild_boarlet", Vector2(46, 12)], ["mudshell_crab", Vector2(54, -22)]])
		for e in Game.room_rt.enemies.values():
			e.pools.max_hp = 1.0e12
			e.pools.hp = e.pools.max_hp
		c.pools.cooldowns.clear()
		c.pools.qi = c.pools.max_qi
		Game.combat.actors.erase(c.id)   # a chain of its own, from the first step
		m.face(Vector2(1, 0.2))
		var tl: Dictionary = Game.combat.timeline(c.id)
		var tiles: Array = []
		var presses := 0
		var f0 := Engine.get_physics_frames()
		var last := -99
		while true:
			var f := Engine.get_physics_frames() - f0
			if f >= 112: break
			if presses == 0:
				p.aim_attack(Vector2(1, 0.2))
				presses = 1
			elif presses == 1 and f >= 3:
				p.aim_technique(0, Vector2(1, 0.2), 0.5)   # pressed in the step's anticipation: it waits for the cut
				presses = 2
			elif presses == 2 and str(tl.technique) != "":
				p.attack()   # pressed in the technique's wind-up: it waits for the technique's cut
				presses = 3
			if f - last >= 5 and tiles.size() < 20:
				last = f
				var now := "tech" if str(tl.technique) != "" else ("basic %d" % (int(tl.combo) + 1) if Game.combat.is_busy(c.id) else "rest")
				var ph := str({"anticipation": "wind-up", "active": "active", "recovery": "recovery"}.get(CombatFeel.phase_of(tl, c), ""))
				tiles.append(["%.2fs %s%s" % [f / 60.0, now, (" · " + ph) if ph != "" else ""], await crop(256, 160)])
			else:
				await get_tree().physics_frame
				await get_tree().process_frame
		await panels(out + "weave_%s.png" % fam, tiles, 4)
	c.inventory.equipped["weapon"] = null
	Game.combat.refresh_stats(c.id)
	# The sprint (the stick pushed: the run the sheets draw) and the light touch's careful walk, over the same second.
	await arena(base + Vector2(-140, -40), [])
	await strip("sprint_strip", Vector2.RIGHT, 48, [], [], [0, 12, 24, 36, 48], out)
	await arena(base + Vector2(-140, -40), [])
	await strip("walk_light_touch_strip", Vector2(0.5, 0), 48, [], [], [0, 12, 24, 36, 48], out)
	hud.visible = true
	print("topdown_capture: decision 42 done")
	get_tree().quit()

## Decision 42 (`-- --decision42-route`, into docs/redesign/feedback/combat/): auto-path's steering (TopdownRoute, as the
## Autopilot drives it) in Lotus Ferry village, round its trees, fences, hedges, rocks and lanterns at the sprint. The
## whole room with a tour drawn on it (from Home Lane to every way out and four of its people and things in turn, as
## topdown_suite's route test runs it): in gold the route the new steering runs, in red the old steering's (cell centre
## to cell centre by find_path); and frames of the body running the road to the east gate in the game.
func decision42_route() -> void:
	var out := "res://docs/redesign/feedback/combat/"
	await _topdown_game(out)
	await frames(360)
	main.hud.visible = false
	Game.world.load_room(Game.active(), "lf_village", "", (Vector2(9, 18) + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	await at_spot(Vector2(9, 18), 150)
	var start: Vector2 = m.pos
	var trails := [_tour_trail(w.room, start, false), _tour_trail(w.room, start, true)]
	var way: Dictionary = Game.room_rt.portal_def("east_gate")
	var goal := Vector2(float(way.at[0]), float(way.at[1]))
	var route := TopdownRoute.new(w.room)
	var tiles: Array = []
	for f in 1800:
		var axis := route.steer(m.pos, m.z, m.grounded, goal, 14.0)
		if axis == Vector2.INF: break
		if route.jump and m.grounded: p.jump()
		p.movement = axis
		if f % 40 == 20 and tiles.size() < 12: tiles.append(["%.2f s  %.0f u/s  %s" % [f / 60.0, m.vel.length(), p.pose], await crop(384, 288)])
		await get_tree().physics_frame
		await get_tree().process_frame
	p.movement = Vector2.ZERO
	for i in 2:
		var line := Line2D.new()
		line.points = trails[i]
		line.width = 2.0
		line.default_color = Color(0.9, 0.25, 0.2, 0.85) if i == 1 else Color(1.0, 0.84, 0.35, 1.0)
		line.z_index = 4000 - i
		w.viewport.add_child(line)
	await whole_room(out + "autopath_village_route.png")
	# A close-up (x2) of the village's east side: the trees by the houses, the lanterns at the jetty, the gate's stair.
	var whole := Image.load_from_file(ProjectSettings.globalize_path(out + "autopath_village_route.png"))
	var close := whole.get_region(Rect2i(660, 220, 500, 260))
	close.resize(1000, 520, Image.INTERPOLATE_NEAREST)
	close.save_png(out + "autopath_village_route_closeup.png")
	await panels(out + "autopath_village_frames.png", tiles, 4)
	main.hud.visible = true
	print("topdown_capture: decision 42 route done")
	get_tree().quit()

## The route tour's feet on the room (art px, lifted by height) for a bare motor from `start`: to every way out and four
## of the room's people and things in turn, steered by TopdownRoute, or (`old`) by the old grid steering: the next cell
## of find_path's way, its centre, the way popped as each cell is entered.
func _tour_trail(room: TopdownRoom, start: Vector2, old: bool) -> PackedVector2Array:
	var goals: Array = []
	for pid in room.def.get("portals", {}): goals.append([TopdownRoom.cell_point(room.def.portals[pid].at), 14.0])
	var places: Array = room.def.get("place", {}).keys()
	places.sort()
	for i in range(0, places.size(), maxi(1, ceili(places.size() / 4.0))): goals.append([TopdownRoom.cell_point(room.def.place[places[i]]), 10.0])
	var mo := TopdownMotor.new(room, start)
	var route := TopdownRoute.new(room)
	var out := PackedVector2Array()
	for g in goals:
		var target: Vector2 = g[0]
		if float(g[1]) == 10.0: target = room.spot_near(target, room.floor_at(target), mo.pos)
		var gp: Array = room.find_path(TopdownRoom.cell_of(mo.pos), TopdownRoom.cell_of(room.nearest_standable(target)), true, 100000)
		for f in 1200:
			var axis := Vector2.ZERO
			var hop := false
			if old:
				if mo.pos.distance_to(target) <= float(g[1]): break
				var cell := TopdownRoom.cell_of(mo.pos)
				while not gp.is_empty() and cell == gp[0]: gp.pop_front()
				var aim := target if gp.is_empty() else (Vector2(gp[0]) + Vector2(0.5, 0.5)) * TopdownRoom.TILE
				axis = (aim - mo.pos).normalized()
				hop = not gp.is_empty() and room.cell_floor(gp[0]) > mo.z + 8.0 and mo.grounded and f % 30 == 0
			else:
				axis = route.steer(mo.pos, mo.z, mo.grounded, target, float(g[1]))
				if axis == Vector2.INF: break
				hop = route.jump and mo.grounded and f % 30 == 0
			for sub in 2: mo.step(1.0 / 120.0, axis, hop and sub == 0)
			mo.drain()
			out.append(Vector2(mo.pos.x, mo.pos.y - mo.z) / TopdownRoom.ART)
	return out

## A crop of the screen (w x h screen px) round the body, at x2 of the world's art px.
func crop(cw: int, ch: int) -> Image:
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	var at: Vector2 = (p.screen - w.camera.position + Vector2(320, 180)) * 2.0 + Vector2(0, -30)
	return img.get_region(Rect2i(Vector2i(clampi(int(at.x) - cw / 2, 0, 1280 - cw), clampi(int(at.y) - ch / 2, 0, 720 - ch)), Vector2i(cw, ch)))

## Images in rows of `cols`, 4 px apart on the night ink, saved as one sheet.
func sheet(path: String, tiles: Array, cols: int) -> void:
	if tiles.is_empty(): return
	var tw: int = (tiles[0] as Image).get_width()
	var th: int = (tiles[0] as Image).get_height()
	var rows := ceili(tiles.size() / float(cols))
	var img := Image.create(cols * (tw + 4) - 4, rows * (th + 4) - 4, false, Image.FORMAT_RGBA8)
	img.fill(Color("071015"))
	for i in tiles.size(): img.blit_rect(tiles[i], Rect2i(0, 0, tw, th), Vector2i((i % cols) * (tw + 4), (i / cols) * (th + 4)))
	img.save_png(path)

## Phase 3, decision 32 (`-- --character`, into docs/redesign/phase3/character/): the real character in Riverside
## Square in the jian, with the tutorial's villagers standing about in their own outfits and a foe to fight; then a
## strip of the character walking, cutting and dashing.
func character() -> void:
	var out := "res://docs/redesign/phase3/character/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var hud = main.hud
	var c = Game.active()
	Game.inventory.apply_add(c.id, "training_jian", 1, "capture")
	Game.submit({"type": "equip", "index": c.inventory.first_index("training_jian")})
	var base := Vector2(22.5, 18.6) * 32.0
	for v in [["aunt_ping", Vector2(-150, -50), "se"], ["lu_boatman", Vector2(-104, 30), "e"], ["little_dou", Vector2(-40, -70), "s"],
			["old_ma", Vector2(190, -40), "w"], ["washer_mei", Vector2(-190, 36), "s"], ["uncle_guo", Vector2(150, 60), "nw"]]:
		w.add_villager(str(v[0]), base + (v[1] as Vector2), str(v[2]))
	await frames(300)   # the arrival's banners fade
	await arena(base, [["wild_boarlet", Vector2(84, 30)]])
	hud.set_state(true)
	m.face(Vector2.RIGHT)
	await frames(10)
	p.aim_attack(Vector2.RIGHT)
	await frames(8)
	await shot("07_ingame_square", out)
	# the same moment round the body, twice again (art px x4)
	var img: Image = Image.load_from_file(ProjectSettings.globalize_path(out + "07_ingame_square.png"))
	var at: Vector2 = (p.screen - w.camera.position + Vector2(320, 180)) * 2.0
	var r := Rect2i(Vector2i(clampi(int(at.x) - 240, 0, 1280 - 480), clampi(int(at.y) - 180, 0, 720 - 270)), Vector2i(480, 270))
	var crop := img.get_region(r)
	crop.resize(960, 540, Image.INTERPOLATE_NEAREST)
	crop.save_png(out + "07_ingame_closeup.png")
	await arena(base, [["wild_boarlet", Vector2(90, 0)]])
	m.face(Vector2.RIGHT)
	await frames(4)
	p.aim_attack(Vector2.RIGHT)
	await strip("07_ingame_strip", Vector2.ZERO, 34, [], [], [0, 5, 10, 16, 34], out)
	await strip("07_ingame_walk_strip", Vector2(0.7, 0.7).normalized(), 40, [], [22], [0, 8, 16, 24, 40], out)
	print("topdown_capture: character done")
	get_tree().quit()

## Phase 4 (`-- --phase4`, into docs/redesign/phase4/): a new top-down character's game (the title's hidden entry),
## each converted room under the real HUD at a spot that shows it, and a quest talk on the dialogue page over the grid.
const PHASE4 := [["01_fishers_hut", "lf_fishers_hut", Vector2(8, 7)], ["02_village_home_lane", "lf_village", Vector2(12, 18)],
	["03_village_square", "lf_village", Vector2(33, 21)], ["04_village_docks", "lf_village", Vector2(58, 26)],
	["05_old_ma_store", "lf_old_ma_store", Vector2(9, 7)], ["06_granny_liu_hut", "lf_granny_liu_hut", Vector2(9, 7)],
	["07_reed_shallows", "lf_reed_shallows", Vector2(40, 15)], ["08_village_night", "lf_village_night", Vector2(22, 20)],
	["09_lu_boat", "lf_lu_boat", Vector2(11, 7)], ["10_willow_path_east", "wp_east", Vector2(31, 13)],
	["11_willow_path_west", "wp_west", Vector2(40, 15)], ["12_stoneford_gate", "sf_gate", Vector2(30, 14)],
	["13_market_street", "sf_market", Vector2(24, 15)], ["14_artisan_row", "sf_artisan_row", Vector2(30, 15)],
	["15_fairground", "sf_fairground", Vector2(28, 16)]]

func phase4() -> void:
	var out := "res://docs/redesign/phase4/"
	await _topdown_game(out)
	# The Prologue as a new character plays it: waking in the hut, then out through its door (Morning Tide's step),
	# the village's three parts, and Lu's talk with A Quiet River to hand in, on the real dialogue page over the grid.
	await at_spot(Vector2(8, 7), 120)
	await shot("01_fishers_hut", out)
	Game.submit({"type": "use_portal", "portal": "exit", "crossing": true})
	await frames(120)   # the villagers' outfit sheets load on threads (they appear a moment after the room)
	for s in [["02_village_home_lane", Vector2(12, 18)], ["03_village_square", Vector2(33, 21)], ["04_village_docks", Vector2(58, 26)]]:
		await at_spot(s[1], 60)
		await shot(str(s[0]), out)
	await at_spot(Vector2(55, 28), 40)
	var r := Game.submit({"type": "interact", "object": "npc_lu_boatman"})
	if r.get("ok", false) and r.has("dialogue"): main.open_page("dialogue", {"convo": r.dialogue})
	await frames(90)
	await shot("16_quest_talk_lu", out)
	main.close_all_pages()
	# The other rooms, entered through the World authority at a spot that shows each.
	await room_shots(PHASE4.filter(func(q): return not str(q[1]) in ["lf_fishers_hut", "lf_village"]), out)
	print("topdown_capture: phase 4 done")
	get_tree().quit()

## Phase 4's second part (`-- --chapter2`, into docs/redesign/phase4/): the rooms of chapter 2's stretch, the Entry
## Trials, both sects' grounds and the Marsh Edge, each under the real HUD at a spot that shows it, with the foes that
## live there set round it ([def, offset in cells]) so their figures show.
const CHAPTER2 := [["17_trial_jade", "sf_trial_jade", Vector2(20, 13), [["trial_puppet", Vector2(6, 3)]]],
	["18_trial_cloud", "sf_trial_cloud", Vector2(18, 13), [["trial_puppet", Vector2(8, 3)]]],
	["19_jade_gate_street", "ja_gate_street", Vector2(24, 15), []], ["20_jade_gate_street_gate", "ja_gate_street", Vector2(10, 22), []],
	["21_jade_weapon_hall", "ja_weapon_hall", Vector2(12, 9), []], ["22_pavilion_rooftops", "ja_pavilion_rooftops", Vector2(26, 14), []],
	["23_east_terrace", "ja_east_terrace", Vector2(30, 14), []], ["24_herb_terraces", "ja_herb_terraces", Vector2(26, 16), []],
	["25_elder_hu_peak", "ja_elder_hu_peak", Vector2(20, 13), []], ["26_cloud_cliff_stair", "cm_cliff_stair", Vector2(26, 18), []],
	["27_sword_court", "cm_sword_court", Vector2(34, 15), []], ["28_cloud_weapon_hall", "cm_weapon_hall", Vector2(12, 9), []],
	["29_array_court", "cm_array_court", Vector2(30, 15), []], ["30_elder_sung_peak", "cm_elder_sung_peak", Vector2(20, 14), []],
	["31_marsh_edge", "rm_marsh_edge", Vector2(30, 14), [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)]]],
	["32_marsh_edge_west", "rm_marsh_edge", Vector2(12, 12), [["marsh_leech", Vector2(4, 4)], ["reed_frog", Vector2(-3, 3)]]]]

func chapter2() -> void:
	var out := "res://docs/redesign/phase4/"
	await _topdown_game(out)
	await frames(360)   # a new game's first notices come and go before the first shot
	await room_shots(CHAPTER2, out)
	print("topdown_capture: chapter 2 done")
	get_tree().quit()

## Decision 40, runtime light (`-- --light [--light-tag=before|after]`, into docs/redesign/terrain_v2/light/): the
## village square at midday, the village at night, Jade Gate Street, the Marsh Edge with its foes, the village square at
## dusk and at the clock's night, each under the real HUD, and the height-levels review room whole (x2). The clock is
## pinned (midday unless a scene names its hour) and the weather held clear, so a before and an after match.
const LIGHT := [["village_day", "lf_village", Vector2(33, 21), [], 0.375], ["village_night", "lf_village_night", Vector2(22, 20), [], 0.375],
	["jade_gate_street", "ja_gate_street", Vector2(24, 15), [], 0.375],
	["marsh_edge", "rm_marsh_edge", Vector2(30, 14), [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)]], 0.375],
	["village_lane", "lf_village", Vector2(12, 18), [], 0.375], ["village_dusk", "lf_village", Vector2(33, 21), [], 0.68],
	["village_clock_night", "lf_village", Vector2(33, 21), [], 0.87]]

func light() -> void:
	var out := "res://docs/redesign/terrain_v2/light/"
	var tag := "after"
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--light-tag="): tag = str(a).trim_prefix("--light-tag=")
	var day_s := Clock.game_day_s()
	Clock.simulate(600000.0 * day_s + 0.375 * day_s, 0)
	Game.calendar.debug_weather = "clear"
	await _topdown_game(out)
	await frames(360)   # a new game's first notices come and go before the first shot
	for s in LIGHT:
		Clock.simulate(600000.0 * day_s + float(s[4]) * day_s, 0)
		TopdownLight.debug_hour = float(s[4])
		await room_shots([[tag + "_" + str(s[0]), s[1], s[2], s[3]]], out)
		var atmo = main.world.get("atmosphere")
		if atmo != null:
			var n := {}
			for q in atmo.particles: n[q.kind] = int(n.get(q.kind, 0)) + 1
			print("light: %s at %.2f, %s, %d lights, air %s" % [s[0], float(s[4]), str(atmo.now.hour), atmo.lights.size(), str(n)])
	# The height-levels review room whole, x2, as the view draws it (the grade is inside the viewport).
	Clock.simulate(600000.0 * day_s + 0.375 * day_s, 0)
	TopdownLight.debug_hour = 0.375
	var was: String = Game.active_id
	Game.active_id = ""
	var v := TopdownWorld.new()
	v.room_id = "td_review_heights"
	add_child(v)
	await frames(2)
	v.set_process(false)
	var size: Vector2 = v.room.art_size()
	var pad := 64
	v.container.stretch = false
	v.viewport.size = Vector2i(int(size.x), int(size.y) + pad)
	v.camera.position = Vector2(size.x * 0.5, (size.y - pad) * 0.5)
	v.player.motor.place(HEIGHT_BODIES[0] * 32.0)
	v.player.sync(0.0)
	v.shadow.sync()
	for spot in HEIGHT_BODIES.slice(1): v.sorted.add_child(StandIn.new(v, spot * 32.0))
	for f in 3: await frames(1)
	await RenderingServer.frame_post_draw
	var img: Image = v.viewport.get_texture().get_image()
	img.resize(img.get_width() * 2, img.get_height() * 2, Image.INTERPOLATE_NEAREST)
	img.save_png(out + tag + "_heights.png")
	v.queue_free()
	Game.active_id = was
	print("topdown_capture: light done")
	get_tree().quit()

## Decision 43, the living world (`-- --life [--life-tag=before|after]`, into docs/redesign/feedback/living_world/<tag>/):
## the village's square, docks and Home Lane, a sect's street and court, the Herb Terraces, the Marsh Edge, a peak and the
## Cliff Stair at their edges, the market, four interiors, and the village and the marsh at the clock's night, each under
## the real HUD at the phone's 1280 x 720. The clock is pinned per shot and the weather held clear, so a before and an
## after match; the room plays a few seconds first, so its people are at work and its critters about.
const LIFE := [["01_village_square", "lf_village", Vector2(33, 21), 0.375], ["02_village_docks", "lf_village", Vector2(58, 28), 0.375],
	["03_village_lane", "lf_village", Vector2(12, 21), 0.375], ["04_sect_gate_street", "ja_gate_street", Vector2(30, 16), 0.375],
	["05_sect_sword_court", "cm_sword_court", Vector2(12, 14), 0.375], ["06_herb_terraces", "ja_herb_terraces", Vector2(20, 22), 0.375],
	["07_marsh_edge", "rm_marsh_edge", Vector2(10, 16), 0.375], ["08_peak_vista", "ja_elder_hu_peak", Vector2(24, 23), 0.375],
	["09_cliff_stair", "cm_cliff_stair", Vector2(28, 30), 0.375], ["10_market", "sf_market", Vector2(30, 16), 0.375],
	["11_interior_granny_liu", "lf_granny_liu_hut", Vector2(9, 9), 0.375], ["12_interior_fishers_hut", "lf_fishers_hut", Vector2(8, 9), 0.375],
	["13_interior_store", "lf_old_ma_store", Vector2(8, 9), 0.375], ["14_interior_weapon_hall", "ja_weapon_hall", Vector2(12, 10), 0.375],
	["15_village_night", "lf_village", Vector2(33, 21), 0.87], ["16_marsh_night", "rm_marsh_edge", Vector2(10, 16), 0.87],
	["17_village_story_night", "lf_village_night", Vector2(22, 20), 0.375]]

func life() -> void:
	var out := "res://docs/redesign/feedback/living_world/"
	var tag := "after"
	var only := ""
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--life-tag="): tag = str(a).trim_prefix("--life-tag=")
		if str(a).begins_with("--life-only="): only = str(a).trim_prefix("--life-only=")   # one shot while iterating
	out += tag + "/"
	var day_s := Clock.game_day_s()
	Clock.simulate(600000.0 * day_s + 0.375 * day_s, 0)
	Game.calendar.debug_weather = "clear"
	await _topdown_game(out)
	await frames(360)   # a new game's first notices come and go before the first shot
	for s in LIFE:
		if (only != "" and not str(s[0]).contains(only)) or "--life-skip-rooms" in OS.get_cmdline_user_args(): continue
		Clock.simulate(600000.0 * day_s + float(s[3]) * day_s, 0)
		TopdownLight.debug_hour = float(s[3])
		await room_shots([[str(s[0]), s[1], s[2]]], out)
	if "--life-detail" in OS.get_cmdline_user_args(): await life_details("res://docs/redesign/feedback/living_world/detail/", only)
	print("topdown_capture: life done")
	get_tree().quit()

## Decision 43's close-ups (`-- --life --life-detail`, into docs/redesign/feedback/living_world/detail/): each a quarter of
## the phone's screen round the thing, x2 (so one art px is four screen px): a flock pecking and the same flock taking
## off as the player walks up, the hens and the dog at the docks, fish and a dragonfly at the bank, frogs at the marsh's
## edge and one leaping, the grass parting round the player, the people at work, chimney smoke, incense and banners, the
## vistas, and the sun in an interior. The critters are set where the shot looks, so every close-up shows its kind.
const LIFE_DETAIL := [
	["01_sparrows_pecking", "lf_village", Vector2(35, 29), 0.375, "sparrows", Vector2(20, -30)],
	["02_sparrows_take_off", "lf_village", Vector2(35, 29), 0.375, "sparrows_flee", Vector2(20, -40)],
	["03_hens_and_dog", "lf_village", Vector2(47, 26), 0.375, "", Vector2(0, 0)],
	["04_fish_dragonfly", "lf_village", Vector2(24, 32), 0.375, "water", Vector2(0, 30)],
	["05_frogs", "rm_marsh_edge", Vector2(34, 21), 0.375, "frogs", Vector2(0, 10)],
	["06_butterflies", "ja_gate_street", Vector2(14, 23), 0.375, "butterflies", Vector2(0, 0)],
	["07_grass_parts", "lf_village", Vector2(5.5, 26.2), 0.375, "", Vector2(0, -10)],
	["08_work_carry_mend", "lf_village", Vector2(58, 25), 0.375, "", Vector2(10, 20)],
	["09_work_laundry_fish", "lf_village", Vector2(16, 30), 0.375, "", Vector2(0, 10)],
	["10_work_chop", "lf_village", Vector2(61, 20), 0.375, "", Vector2(20, -20)],
	["10b_chimney_smoke", "lf_village", Vector2(18, 8), 0.375, "", Vector2(0, 20)],
	["11_work_forms", "lf_village", Vector2(32, 24), 0.375, "", Vector2(-20, -10)],
	["12_work_sword_hammer", "ja_weapon_hall", Vector2(13, 9), 0.375, "", Vector2(10, -50)],
	["13_work_sweep", "ja_gate_street", Vector2(31, 18), 0.375, "", Vector2(-20, -20)],
	["14_interior_sun", "lf_fishers_hut", Vector2(9, 9), 0.375, "", Vector2(0, -60)],
	["15_interior_granny", "lf_granny_liu_hut", Vector2(9, 9), 0.375, "", Vector2(-40, -50)],
	["16_incense_banners", "ja_gate_street", Vector2(6, 16), 0.375, "", Vector2(0, -40)],
	["17_vista_peak", "ja_elder_hu_peak", Vector2(24, 25), 0.375, "", Vector2(0, 50)],
	["18_vista_north", "cm_sword_court", Vector2(30, 4), 0.375, "", Vector2(0, -60)],
	["19_vista_river", "lf_village", Vector2(30, 33), 0.375, "", Vector2(0, 60)],
	["20_lanterns_night", "lf_village", Vector2(64, 27), 0.87, "", Vector2(-40, -10)],
	["21_boat_on_the_river", "lf_lu_boat", Vector2(12, 8), 0.375, "", Vector2(0, 0)],
]

func life_details(out: String, only := "") -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var day_s := Clock.game_day_s()
	for s in LIFE_DETAIL:
		if only != "" and not str(s[0]).contains(only): continue
		Clock.simulate(600000.0 * day_s + float(s[3]) * day_s, 0)
		TopdownLight.debug_hour = float(s[3])
		Game.world.load_room(Game.active(), str(s[1]), "", (s[2] as Vector2 + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(10)
		await at_spot(s[2], 150)
		var life: TopdownLife = w.life
		var feet: Vector2 = p.motor.pos
		match str(s[4]):
			"sparrows", "sparrows_flee":
				for i in 4:
					var cr: TopdownLife.Critter = life._critter("sparrow", feet + Vector2(20 + i * 26, -110 - (i % 2) * 18))
					cr.state = "ground"
					cr.alpha = 1.0
					cr.face = -1 if i % 2 else 1
				await frames(20)
				if str(s[4]) == "sparrows_flee":
					p.movement = Vector2.UP * 0.6
					await frames(44)
					p.movement = Vector2.ZERO
			"water":
				for i in 3:
					var cr: TopdownLife.Critter = life._critter("fish", feet + Vector2(-40 + i * 50, 80 + i * 14))
					cr.floor = TopdownRoom.WATER_Z
					cr.alpha = 1.0
					cr.v = Vector2(12, 3)
					cr.anchor = cr.g
				var df: TopdownLife.Critter = life._critter("dragonfly", feet + Vector2(30, 60))
				df.anchor = df.g
				df.z = 9.0
				df.alpha = 1.0
				life._ring(feet + Vector2(-40, 80))
				await frames(12)
			"frogs":
				for i in 3:
					var cr: TopdownLife.Critter = life._critter("frog", feet + Vector2(-50 + i * 44, 18 + (i % 2) * 8))
					cr.state = "sit"
					cr.alpha = 1.0
					cr.water = Vector2.DOWN
				await frames(12)
			"butterflies":
				for i in 4:
					var cr: TopdownLife.Critter = life._critter("butterfly", feet + Vector2(-60 + i * 36, -20 + (i % 2) * 20))
					cr.anchor = cr.g
					cr.variant = ["white", "gold", "blue", "coral"][i]
					cr.z = 10.0
					cr.alpha = 1.0
				await frames(30)
		await shot_detail(str(s[0]), s[5], out)
	TopdownLight.debug_hour = 0.375

## Decision 44 (`-- --work-poses`, into docs/redesign/feedback/work_poses/): the people at work in their drawn work poses,
## each tool in the hands (close-ups a quarter of the screen round the worker, x2, the player standing off so they work
## on), the village and a sect's court at work (whole screens under the HUD), and the player using a place: opening the
## letter box, tending a garden bed, sitting on the mat, each shot mid-pose before its page opens.
const WORK_SHOTS := [
	["ingame_01_village_sweep", "lf_village", "npc_aunt_ping_lane", "work_sweep"], ["ingame_02_village_carry", "lf_village", "npc_shen_lian_npc", "work_carry"],
	["ingame_03_village_laundry", "lf_village", "npc_washer_mei", "work_hang"], ["ingame_04_village_fisher", "lf_village", "x_bank_fisher", "work_rod"],
	["ingame_05_village_woodcutter", "lf_village", "x_woodcutter", "work_chop"], ["ingame_06_village_net", "lf_village", "npc_fisher_wen", "work_mend"],
	["ingame_07_hut_cook", "lf_fishers_hut", "npc_aunt_ping", "work_stir"], ["ingame_08_hut_grind", "lf_granny_liu_hut", "npc_granny_liu", "work_grind"],
	["ingame_09_sect_smith", "ja_weapon_hall", "npc_jade_smith", "work_hammer"], ["ingame_10_sect_sweeper", "ja_gate_street", "x_ja_sweeper", "work_sweep"],
	["ingame_11_sect_herbs", "ja_herb_terraces", "npc_jade_gardener", "work_pick"], ["ingame_12_market_cook", "sf_market", "npc_auntie_rong", "work_stir"],
	["ingame_13_artisan_smith", "sf_artisan_row", "npc_smith_bao", "work_hammer"], ["ingame_14_marsh_fisher_cast", "rm_marsh_edge", "x_marsh_fisher", "work_cast"],
]
const WORK_WIDE := [["ingame_20_village_at_work", "lf_village", Vector2(55, 22)], ["ingame_21_sect_at_work", "ja_gate_street", Vector2(38, 20)],
	["ingame_22_weapon_hall_at_work", "ja_weapon_hall", Vector2(13, 10)]]

func work_poses() -> void:
	var out := "res://docs/redesign/feedback/work_poses/"
	var only := ""
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--work-only="): only = str(a).trim_prefix("--work-only=")
	var day_s := Clock.game_day_s()
	Clock.simulate(600000.0 * day_s + 0.375 * day_s, 0)
	Game.calendar.debug_weather = "clear"
	await _topdown_game(out)
	await frames(360)
	var c = Game.active()
	c.training_sect = {"id": "jade_sect", "rank": "outer", "contribution": 0}
	for s in WORK_SHOTS:
		if only != "" and not str(s[0]).contains(only): continue
		await _worker_shot(str(s[0]), str(s[1]), str(s[2]), str(s[3]), out)
	for s in WORK_WIDE:
		if only != "" and not str(s[0]).contains(only): continue
		Game.world.load_room(c, str(s[1]), "", (s[2] as Vector2 + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(10)
		await at_spot(s[2], 240)
		await shot(str(s[0]), out)
	# the places' systems opened for the character, their notices given time to go before the shots
	for s in ["mail", "cultivation", "herb_garden", "storage"]: Unlocks.force_unlock(c.id, s)
	await frames(420)
	for s in [["ingame_30_player_open_letter_box", "letter_box"], ["ingame_31_player_tend_bed", "garden_bed"], ["ingame_32_player_sit_mat", "meditation_mat"]]:
		if only != "" and not str(s[0]).contains(only): continue
		await _place_shot(str(s[0]), str(s[1]), out)
	print("topdown_capture: work poses done")
	get_tree().quit()

## A worker in its loop, the player standing four and a half tiles off (out of its notice) and the shot on the worker
## once it plays `action` (at its contact frame, or its second frame), or after half a minute whatever it does. A worker
## the story does not show yet is left out, and said so.
func _worker_shot(name: String, room: String, who: String, action: String, out: String) -> void:
	var life: Dictionary = TopdownLife.room_life(room)
	var home := Vector2.ZERO
	for e in life.get("extras", []):
		if str(e.id) == who: home = TopdownRoom.cell_point(e.spots[0])
	if home == Vector2.ZERO:
		var lay := TopdownRoom.load_room(room)
		home = TopdownRoom.cell_point(lay.def.place.get(who, [0, 0]))
	var far := home + Vector2(0, 4.5 * TopdownRoom.TILE)
	Game.world.load_room(Game.active(), room, "", far)
	GameEvents.flush()
	await frames(10)
	w = main.world
	p = w.player
	m = p.motor
	# out of the worker's notice (72 units): the first side of them the player can stand on well away (by a river bank
	# the south is water, and the nearest standable cell there would be at the worker's elbow)
	var stand: Vector2 = w.room.nearest_standable(far)
	for off in [Vector2(0, 4.5), Vector2(0, -4.5), Vector2(4.5, 0), Vector2(-4.5, 0), Vector2(3.5, 3.5), Vector2(-3.5, -3.5)]:
		var q: Vector2 = w.room.nearest_standable(home + off * TopdownRoom.TILE)
		if q.distance_to(home) > 100.0:
			stand = q
			break
	m.place(stand)
	m.dir = Vector2.UP
	w._settle_camera()
	await frames(60)
	var fig = null
	for f in w.life.workers:
		if is_instance_valid(f) and str(f.def.get("id", "")) == who: fig = f
	if fig == null or not fig.visible:
		print("topdown_capture: no worker ", who, " shown in ", room, " at this point of the story")
		return
	var want := TopdownFigure.hit_frame(action) if int(TopdownFigure.spec(action).hit) >= 0 else 1
	var got := false
	for i in 1800:
		if fig.work.action == action and fig.work.hold < 0 and (fig.work.walking or fig.work.frame() == want):
			got = true
			break
		await frames(1)
	if not got: print("topdown_capture: ", who, " did not play ", action, " in half a minute (", fig.work.action, ")")
	await RenderingServer.frame_post_draw
	await shot_detail(name, (fig.feet as Vector2) - p.screen + Vector2(0, 14), out)

## The player using a place of the table (the first of its kind the character reaches): stood on its user's cell, facing
## it, the context button pressed through the HUD, the shot mid-pose (before the page opens).
func _place_shot(name: String, kind: String, out: String) -> void:
	var row := {}
	for r in PlaceRules.all():
		if str(r.kind) == kind and row.is_empty(): row = r
	if row.is_empty(): return
	var at := PlaceRules.point(row)
	var stand := PlaceRules.stand_point(row)
	Game.world.load_room(Game.active(), str(row.room), "", stand)
	GameEvents.flush()
	await frames(10)
	w = main.world
	p = w.player
	m = p.motor
	# beside the thing, so the pose reads from the side (the user's cell may face it from the south, the back view); on
	# the mat itself, facing the camera, to sit on it
	var on_it := kind == "meditation_mat"
	for off in ([] if on_it else [Vector2(-1.0, 0.35), Vector2(1.0, 0.35)]):
		var q: Vector2 = w.room.nearest_standable(at + off * TopdownRoom.TILE)
		if q.distance_to(at + off * TopdownRoom.TILE) < 6.0:
			stand = q
			break
	if on_it: stand = w.room.nearest_standable(at)
	m.place(stand)
	var face := at - stand
	m.dir = Vector2.DOWN if on_it else (face.normalized() if face.length() > 1.0 else Vector2.UP)
	m.row = TopdownMotor.nearest_row(m.dir, m.row, TopdownMotor.ROW_ANGLES, 10.0)
	w._settle_camera()
	# the unlock tutorials' coach (the places' systems were opened for this capture) kept off the shot
	if is_instance_valid(main.coach):
		main.coach.visible = false
		main.coach.process_mode = Node.PROCESS_MODE_DISABLED
	await frames(90)
	var hud = main.hud
	hud._after_interact(Game.submit({"type": "interact", "object": str(row.object)}), str(row.object))
	await frames(int(hud.PLACE_POSE_S * 60.0 * 0.85))
	await shot_detail(name, Vector2(0, 0), out)
	hud.open_place_page()
	await frames(20)
	main.close_all_pages()
	await frames(10)

## A quarter of the screen round the player's feet (moved by `off` screen px), x2.
func shot_detail(name: String, off: Vector2, out: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	var c: Vector2 = (p.screen - w.camera.position + Vector2(320, 180)) * 2.0 + off * 2.0 + Vector2(0, -30)
	var r := Rect2i(Vector2i(clampi(int(c.x) - 320, 0, 640), clampi(int(c.y) - 180, 0, 360)), Vector2i(640, 360))
	var crop := img.get_region(r)
	crop.resize(1280, 720, Image.INTERPOLATE_NEAREST)
	crop.save_png(out + name + ".png")

## The tutorial rooms' other foes in their own figures (`-- --tutorial-foes`, into docs/redesign/phase4/): Lotus Ferry
## at night, the hollowed eel rising from the river (the night's own event) and hollow minnows swimming through the air
## at the player; Old Snapper on the Reed Shallows' flats (it comes only after five crab shells, so it is set there);
## the mossback toads on Willow Path West's pine ridge. Each is shot under the real HUD while they close in and fight,
## and x4 round the fight ([name, room, cell, foes [def, offset in cells], the close-up's centre from the body]).
const TUTORIAL_FOES := [["33_night_eel_minnows", "lf_village_night", Vector2(33, 32), [["hollow_minnow", Vector2(-3, -2)], ["hollow_minnow", Vector2(4, -3)]], Vector2(24, 24)],
	["35_reed_shallows_old_snapper", "lf_reed_shallows", Vector2(51, 17), [["old_snapper", Vector2(3, 2)]], Vector2(24, 12)],
	["37_willow_path_west_toads", "wp_west", Vector2(17, 7), [["mossback_toad", Vector2(-3, 1)], ["mossback_toad", Vector2(3, 0)]], Vector2(0, 0)]]

func tutorial_foes() -> void:
	var out := "res://docs/redesign/phase4/"
	for a in OS.get_cmdline_user_args():   # `--into=<dir>/`: into another folder (the prototype's QA took its own)
		if str(a).begins_with("--into="): out = str(a).trim_prefix("--into=")
	await _topdown_game(out)
	await frames(360)
	var n := 33
	for s in TUTORIAL_FOES:
		Game.world.load_room(Game.active(), str(s[1]), "", (s[2] as Vector2 + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(10)
		await at_spot(s[2], 60)
		for f in s[3]:
			var at: Vector2 = w.room.nearest_standable((s[2] + f[1] + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
			var e: EnemyState = Game.enemies.spawn_at(str(f[0]), at, 1)
			e.altitude = w.room.height_at(e.plane)
			e.threat[Game.active_id] = 1.0
		for i in 150:   # they close in and fight; the body is kept whole
			Game.active().pools.hp = Game.active().pools.max_hp
			await frames(1)
		await shot(str(s[0]), out)
		await RenderingServer.frame_post_draw
		var vi: Image = w.viewport.get_texture().get_image()
		var at: Vector2i = Vector2i(p.screen - w.camera.position + Vector2(320, 180) + (s[4] as Vector2)) - Vector2i(160, 90)
		var crop := vi.get_region(Rect2i(at.clamp(Vector2i.ZERO, Vector2i(320, 180)), Vector2i(320, 180)))
		crop.resize(1280, 720, Image.INTERPOLATE_NEAREST)
		crop.save_png(out + "%d_%s_x4.png" % [n + 1, str(s[0]).substr(3)])
		n += 2
	print("topdown_capture: tutorial foes done")
	get_tree().quit()

## Terrain v2 (decision 40, `-- --terrain <name>`): the same views before and after the tile work, the world alone at
## x2 (1280 x 720), into docs/redesign/terrain_v2/<name>/: Lotus Ferry's square and the Fisher's Hut's lane, the Jade Gate
## Street, the Marsh Edge, the Reed Shallows, the Cloud Sect's cliff stair and Elder Sung's peak (cliffs), Riverside
## Square at its spawn, and the height-levels review room whole.
const TERRAIN_VIEWS := [["01_village_square", "lf_village", Vector2(33, 21)], ["02_jade_gate_street", "ja_gate_street", Vector2(24, 15)],
	["03_marsh_edge", "rm_marsh_edge", Vector2(30, 14)], ["04_reed_shallows", "lf_reed_shallows", Vector2(40, 15)],
	["05_fishers_hut_lane", "lf_village", Vector2(12, 18)], ["08_cliff_stair", "cm_cliff_stair", Vector2(40, 10)],
	["09_elder_sung_peak", "cm_elder_sung_peak", Vector2(20, 10)]]
## Decision 40's third part (`-- --terrain foliage/<before|after>`): the same views, and these besides, into
## docs/redesign/terrain_v2/foliage/<name>/: the Willow Path, the Herb Terraces, the Pavilion Rooftops and the Sword
## Court in the world alone, and two fights under the HUD, so foes, names and rings are judged against the new cover.
const FOLIAGE_VIEWS := [["10_willow_path_east", "wp_east", Vector2(40, 12)], ["11_herb_terraces", "ja_herb_terraces", Vector2(20, 20)],
	["12_pavilion_rooftops", "ja_pavilion_rooftops", Vector2(22, 20)], ["13_willow_path_west", "wp_west", Vector2(26, 16)]]
const FOLIAGE_FIGHTS := [["14_fight_willow_path_hud", "wp_east", Vector2(20, 14), [["wild_boarlet", Vector2(3, 2)], ["wild_boarlet", Vector2(-4, 3)], ["reedtail_rat", Vector2(5, -1)]]],
	["15_fight_marsh_edge_hud", "rm_marsh_edge", Vector2(34, 15), [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)], ["reed_frog", Vector2(2, -2)]]]]

func terrain_v2() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--terrain")
	var name := str(args[i + 1]) if i + 1 < args.size() else "after"
	var foliage := name.begins_with("foliage/")
	var out := "res://docs/redesign/terrain_v2/%s/" % name
	await _topdown_game(out)
	await frames(360)   # a new game's first notices come and go before the first shot
	for s in TERRAIN_VIEWS + (FOLIAGE_VIEWS if foliage else []):
		Game.world.load_room(Game.active(), str(s[1]), "", (s[2] as Vector2 + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(10)
		await at_spot(s[2], 120)
		(await world_shot()).save_png(out + str(s[0]) + ".png")
	if foliage:
		await room_shots(FOLIAGE_FIGHTS, out)
		# Every room on the grid whole at 1 art px, into <name>/rooms/, to judge the foliage's framing room by room.
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out + "rooms/"))
		for f in DirAccess.get_files_at("res://data/topdown/"):
			var rid := f.get_basename()
			if not f.ends_with(".json") or not TopdownRoom.has_layout(rid): continue
			var lay = JSON.parse_string(FileAccess.get_file_as_string("res://data/topdown/" + f))
			if not (lay is Dictionary and lay.has("levels")): continue
			Game.world.load_room(Game.active(), rid, "", TopdownRoom.cell_point(lay.get("spawn", [1, 1])))
			GameEvents.flush()
			await frames(6)
			w = main.world
			await whole_room(out + "rooms/" + rid + ".png")
	# The views alone (no character enters them): Riverside Square at its spawn, and the height-levels room whole.
	var was: String = Game.active_id
	Game.active_id = ""
	main.hud.visible = false
	for s in [["06_riverside_square", "td_proto_square"], ["07_height_levels", "td_review_heights"]]:
		var v := TopdownWorld.new()
		v.room_id = str(s[1])
		add_child(v)
		await frames(2)
		w = v
		if str(s[1]) == "td_review_heights":
			v.set_process(false)
			v.camera.position = v.room.art_size() * 0.5 - Vector2(0, 24)
			v.player.motor.place(HEIGHT_BODIES[0] * 32.0)
			v.player.sync(0.0)
			v.shadow.sync()
			for spot in HEIGHT_BODIES.slice(1): v.sorted.add_child(StandIn.new(v, spot * 32.0))
		for f in 30: await frames(1)
		(await world_shot()).save_png(out + str(s[0]) + ".png")
		v.queue_free()
		await frames(2)
	Game.active_id = was
	# With both sets taken, each view's before and after side by side, into docs/redesign/terrain_v2/ (the foliage
	# part's into its own folder).
	var dir := "res://docs/redesign/terrain_v2/" + ("foliage/" if foliage else "")
	var views: Array = TERRAIN_VIEWS + [["06_riverside_square"], ["07_height_levels"]] + (FOLIAGE_VIEWS + FOLIAGE_FIGHTS if foliage else [])
	for s in views:
		var b := dir + "before/" + str(s[0]) + ".png"
		var a := dir + "after/" + str(s[0]) + ".png"
		if not (FileAccess.file_exists(b) and FileAccess.file_exists(a)): continue
		await panels(dir + str(s[0]) + "_before_after.png", [["Before", Image.load_from_file(ProjectSettings.globalize_path(b))],
			["After: " + ("foliage and decor" if foliage else "Terrain v2"), Image.load_from_file(ProjectSettings.globalize_path(a))]], 2)
	print("topdown_capture: terrain views done")
	get_tree().quit()

## Decision 44 (`-- --sand-snow --sand-snow-tag=<before|after>`): the sand and snow ground, into
## docs/redesign/feedback/sand_snow/<tag>/: every room they are painted in whole at 1 art px (rooms/), a view of each at
## x2 with the body standing on the new ground, and x4 close-ups of its transitions (closeups/). The after set adds the
## sampler (every transition side by side on a room of its own) and, with the before set there, the pairs (pairs/).
## Each view: [name, room, the body's cell, close-ups [cell x, cell y, level]].
const SAND_SNOW_VIEWS := [
	["01_lotus_ferry_bank", "lf_village", Vector2(12, 31), [[14, 32, 0], [23, 32, 0]]],
	["02_lotus_ferry_shore", "lf_village", Vector2(53, 31), [[56, 33, 0], [64, 32, 0]]],
	["03_reed_shallows_beach", "lf_reed_shallows", Vector2(38, 19), [[44, 21, 0], [27, 21, 0]]],
	["04_marsh_edge_spits", "rm_marsh_edge", Vector2(12, 21), [[12, 23, 0], [42, 22, 0]]],
	["05_willow_path_east_stream", "wp_east", Vector2(18, 18), [[18, 20, 0]]],
	["06_willow_path_west_pond", "wp_west", Vector2(22, 23), [[22, 24, 0]]],
	["07_elder_hu_peak", "ja_elder_hu_peak", Vector2(22, 10), [[22, 5, 3], [1, 6, 3]]],
	["08_cliff_stair_ledge", "cm_cliff_stair", Vector2(42, 10), [[48, 6, 4], [52, 8, 5]]],
	["09_elder_sung_peak", "cm_elder_sung_peak", Vector2(30, 12), [[37, 8, 4], [31, 4, 3]]],
]

func sand_snow() -> void:
	var tag := "after"
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--sand-snow-tag="): tag = str(a).trim_prefix("--sand-snow-tag=")
	var root := "res://docs/redesign/feedback/sand_snow/"
	var out := root + tag + "/"
	for d in ["rooms/", "closeups/"]: DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out + d))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(root + "pairs/"))
	var day_s := Clock.game_day_s()
	Clock.simulate(600000.0 * day_s + 0.375 * day_s, 0)
	Game.calendar.debug_weather = "clear"
	await _topdown_game(out)
	await frames(360)   # a new game's first notices come and go before the first shot
	var rooms := []
	for s in SAND_SNOW_VIEWS:
		Game.world.load_room(Game.active(), str(s[1]), "", (s[2] as Vector2 + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(10)
		await at_spot(s[2], 90)
		(await world_shot()).save_png(out + str(s[0]) + ".png")
		var k := 0
		for c in s[3]:
			k += 1
			await closeup(out + "closeups/%s_%d.png" % [str(s[0]), k], Vector2((float(c[0]) + 0.5) * 16.0, (float(c[1]) + 0.5 - float(c[2])) * 16.0))
		if not str(s[1]) in rooms:
			rooms.append(str(s[1]))
			await whole_room(out + "rooms/" + str(s[1]) + ".png")
	if tag == "after": await sand_snow_sampler(out)
	# With both sets taken, each view's before and after side by side.
	for s in SAND_SNOW_VIEWS:
		var names: Array = [str(s[0])]
		for k in range(1, (s[3] as Array).size() + 1): names.append("closeups/%s_%d" % [str(s[0]), k])
		for n in names:
			var b := root + "before/" + str(n) + ".png"
			var a := root + "after/" + str(n) + ".png"
			if not (FileAccess.file_exists(b) and FileAccess.file_exists(a)): continue
			await panels(root + "pairs/" + str(n).get_file() + "_before_after.png", [["Before", Image.load_from_file(ProjectSettings.globalize_path(b))],
				["After: sand and snow", Image.load_from_file(ProjectSettings.globalize_path(a))]], 2)
	print("topdown_capture: sand and snow done")
	get_tree().quit()

## A close-up x4 of the world viewport round `at` (art px on the screen plane: a cell's ground point lifted by its
## level), a quarter of the view (320 x 180 art px), so one art px is four px.
func closeup(path: String, at: Vector2) -> void:
	await RenderingServer.frame_post_draw
	var img: Image = w.viewport.get_texture().get_image()
	var c: Vector2 = w.viewport.get_canvas_transform() * at
	var r := Rect2i(Vector2i(clampi(int(c.x) - 160, 0, img.get_width() - 320), clampi(int(c.y) - 90, 0, img.get_height() - 180)), Vector2i(320, 180))
	var crop := img.get_region(r)
	crop.resize(1280, 720, Image.INTERPOLATE_NEAREST)
	crop.save_png(path)

## The sampler: every sand and snow transition on a room of its own, 40 x 22 cells (the phone's view), drawn by the
## game's own room view. West: meadow, a dirt path and a paved corner round a sand flat, its beach on the water and a
## jetty. East: a snow field on the meadow with a packed-snow path through it, granite and paving at its edges, and a
## rock shelf two levels up under snow on its east half, its face capped by the snow's lip. Whole at x2, and each
## quarter x4.
const SAMPLER_PAINT := [
	"gggggggddggggggggggggrrrrrrrrrrrrrrrrrrr",
	"gggggggddgggggpppppggrrrrrrrnnnnnnnnnnnn",
	"gggggggddgggggpppppggrrrrrrnnnnnnnnnnnnn",
	"gggggggddggggapppppggrrrrrrrnnnnnnnnnnnn",
	"ggggggaddaagaaapppgggggggggggggggggggggg",
	"ggggaaaddaaaaaaappggggggggggggggggkkgggg",
	"gggaaaaaaaaaaaaaaggggggnnnnnnnnnnkkngggg",
	"ggaaaaaaaaaaaaaaaaggggnnnnnnnnnnnkknnggg",
	"ggaaaaaaaaaaaaaaaggggnnnnnnnnnnnnkknnggg",
	"gggaaaaaaaaaaaaaggggnnnnnnnnnnnnkknnnggg",
	"ggggaaaaaaaaaaaggggnnnnnnnnnnnnnkknnnggg",
	"gggggaaaaaaaaagggggnnnnnnnnnnnnkknnnnggg",
	"ggggaaaaaaaaaaagggggnnnnnnnnnnnkknnnssss",
	"gggaaaaaaaaaaaaagggppnnnnnnnnnkknnnnssss",
	"aaaaaaaaaaaaaaaaaaaapppnnnnnnkknnnnnssss",
	"aaaaaaaaaaaaaaaaaaaapppppnnnkknnnnggssss",
	"aaaaaaaaaaaawwaaaaaapppppggkkgggggggssss",
	"~~~~~~~~~~~~ww~~~~~~pppppgkkggggggggggss",
	"~~~~~~~~~~~~ww~~~~~~ppppgkkggggggggggggg",
	"~~~~~~~~~~~~~~~~~~~~pppgkkgggggggggggggg",
	"~~~~~~~~~~~~~~~~~~~~pppgkkgggggggggggggg",
	"~~~~~~~~~~~~~~~~~~~~ppggkkgggggggggggggg",
]

func sand_snow_sampler(out: String) -> void:
	var levels: Array = []
	for y in SAMPLER_PAINT.size():
		var row := ""
		for x in str(SAMPLER_PAINT[y]).length():
			var ch := str(SAMPLER_PAINT[y])[x]
			row += "~" if ch == "~" else ("2" if y < 4 and x >= 21 else "0")
		levels.append(row)
	var d := {"id": "td_sand_snow_sampler", "name": "Sand and snow", "levels": levels, "paint": SAMPLER_PAINT, "stairs": [],
		"props": [{"kind": "reeds", "x": 5, "y": 16}, {"kind": "pine", "x": 38, "y": 9}, {"kind": "boulder", "x": 30, "y": 16}],
		"spawn": [9, 12]}
	var ts = JSON.parse_string(FileAccess.get_file_as_string(TopdownRoom.DIR + "proto_tileset.json"))
	var was: String = Game.active_id
	Game.active_id = ""
	main.hud.visible = false
	main.world.visible = false
	var v := TopdownWorld.new()
	v.preset = TopdownRoom.from_dict(d, ts)
	add_child(v)
	await frames(2)
	w = v
	v.set_process(false)
	v.camera.position = v.room.art_size() * 0.5 - Vector2(0, 8)
	for f in 30: await frames(1)
	(await world_shot()).save_png(out + "10_sampler.png")
	var k := 0
	for q in [Vector2(10, 5), Vector2(10, 16), Vector2(30, 3), Vector2(30, 14)]:
		k += 1
		await closeup(out + "closeups/10_sampler_%d.png" % k, (q + Vector2(0.5, 0.5)) * 16.0)
	v.queue_free()
	await frames(2)
	Game.active_id = was
	main.world.visible = true
	main.hud.visible = true

## A new top-down character's game (the title's hidden entry), once the pages' scripts have compiled on their loading
## threads from the title screen on (main._warm_pages), where a player spends those seconds: a villager's outfit sheets
## queue behind them, so the capture waits for them as the title would.
func _topdown_game(out: String) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	for i in 3600:
		if main.PAGES.values().all(func(q): return ResourceLoader.load_threaded_get_status(str(q)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS): break
		await get_tree().process_frame
	main.enter_topdown_tutorial(false)

## Each room of `list` ([name, room, cell, optional foes]) entered through the World authority, the body at the cell,
## the listed foes set round it and turned on the player, and a shot under the HUD.
func room_shots(list: Array, out: String) -> void:
	for s in list:
		Game.world.load_room(Game.active(), str(s[1]), "", (s[2] as Vector2 + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(10)
		await at_spot(s[2], 120)
		for f in (s[3] if s.size() > 3 else []):
			var at: Vector2 = w.room.nearest_standable((s[2] + f[1] + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
			var e: EnemyState = Game.enemies.spawn_at(str(f[0]), at, 1)
			e.altitude = w.room.height_at(e.plane)
		if s.size() > 3 and not (s[3] as Array).is_empty(): await frames(20)
		await shot(str(s[0]), out)

## Decision 39 (`-- --story`, into docs/redesign/phase5/story/): the staged scenes as a new top-down character meets
## them, played by the game's own SceneDirector: the opening (its title card, Aunt Ping walking over with the tea, the
## Bag's and the door's hand-offs), Home Lane at dawn (a boat on the river, the villagers talking, the kite), Lu's four
## errands, Granny's jar and the Quick-use prompt, the East Gate opening, the crabs on the flats, the Hollow Night's
## storm, Lu's boat and the first breakthrough, the thief in the market, the fair and the sect chosen. The story is
## moved on between them as the walk would (the quests' own talks), or set where a capture needs it.
func story() -> void:
	var out := "res://docs/redesign/phase5/story/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	for i in 3600:
		if main.PAGES.values().all(func(q): return ResourceLoader.load_threaded_get_status(str(q)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS): break
		await get_tree().process_frame
	main.enter_topdown_tutorial(false)
	var c = Game.active()
	# The opening: the title card over the dark, Aunt Ping's first line, her walk to the table and back (a strip), the
	# Bag's hand-off after the tea, and the door's.
	await scene_at("opening_dawn", "title", 1.6)
	await shot("01_opening_title", out)
	await scene_at("opening_dawn", "say", 1.2)
	await shot("02_opening_ping_wakes_you", out)
	await story_strip("03_opening_walk_strip", "opening_dawn", "move", 4, 14, out)
	await scene_at("opening_dawn", "handoff", 0.6)
	await shot("04_opening_bag_handoff", out)
	await scene_at("opening_dawn", "handoff", 0.8, "door")
	await shot("05_opening_door_handoff", out)
	# Home Lane at dawn, entered through the door.
	Game.submit({"type": "use_portal", "portal": "exit", "crossing": true})
	await frames(30)
	await scene_at("river_dawn", "camera", 2.2)
	await shot("06_dawn_boat_on_the_river", out)
	await scene_at("river_dawn", "say", 1.5, "Hush")
	await shot("07_dawn_villagers_talk", out)
	await scene_at("river_dawn", "say", 1.2, "kite")
	await shot("08_dawn_the_kite", out)
	# Lu's errands, after A Quiet River is handed in on his talk.
	await until_idle()
	await choose("npc_lu_boatman", "hand_in", "a_quiet_river")
	await scene_at("four_errands", "say", 0.8, "Hah")
	await shot("09_errands_guo_at_his_stump", out)
	await until_idle()
	# Granny's Remedy: the jar, the graze, the Bag and the Quick-use prompts.
	Game.submit({"type": "use_portal", "portal": "granny_door", "crossing": true})
	await frames(40)
	await choose("npc_granny_liu", "accept", "grannys_remedy")
	await scene_at("granny_jar", "say", 1.0, "clumsy")
	await shot("10_granny_the_jar_falls", out)
	await scene_at("granny_jar", "handoff", 0.8)
	await shot("11_granny_bag_handoff", out)
	Game.submit({"type": "set_quick_use", "item": "herbal_tea"})
	await scene_at("granny_jar", "handoff", 0.8, "Drink")
	await shot("12_granny_quick_use_handoff", out)
	Game.submit({"type": "use_quick"})
	await until_idle()
	# Crab Trouble: the lessons done, Guo opens the East Gate; the crabs have Washer Mei on the flats.
	for q in ["the_runaway_kite", "mas_delivery", "fists_first"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	Game.submit({"type": "use_portal", "portal": "exit", "crossing": true})
	await frames(30)
	Game.quest.apply_start(c.id, "crab_trouble")
	await scene_at("east_gate", "wait", 0.4)
	await shot("13_the_east_gate_opens", out)
	await until_idle()
	Game.submit({"type": "use_portal", "portal": "east_gate", "crossing": true})
	await frames(30)
	await scene_at("crabs_mei", "say", 1.2, "Shoo")
	await shot("14_crabs_mei_on_the_flats", out)
	await scene_at("crabs_mei", "handoff", 0.8)
	await shot("15_crabs_drive_one_off", out)
	# The night, set as the story has it after the evening on the river (leaving the flats ends the crabs' scene).
	for q in ["crab_trouble", "evening_on_the_river"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	Game.apply_effects(c.id, [{"kind": "set_flag", "flag": "night_active"}], "capture")
	Game.world.load_room(c, "lf_village_night", "")
	GameEvents.flush()
	await frames(20)
	await scene_at("hollow_rises", "title", 1.2)
	await shot("16_the_hollow_night", out)
	await scene_at("hollow_rises", "say", 1.2, "river")
	await shot("17_hollow_night_the_river_boils", out)
	await until_idle()
	# Lu's boat after the storm, and the first breakthrough.
	Game.apply_effects(c.id, [{"kind": "set_flag", "flag": "night_survived"}], "capture")
	c.quests.active.erase("the_hollow_night")
	c.quests.done["the_hollow_night"] = 1
	Game.world.load_room(c, "lf_lu_boat", "")
	GameEvents.flush()
	await frames(20)
	await scene_at("river_token", "say", 1.4, "gift")
	await shot("18_river_token_lu", out)
	await scene_at("river_token", "handoff", 0.8)
	await shot("19_river_token_meditate_handoff", out)
	Game.submit({"type": "start_meditation"})
	await until_idle()
	Game.submit({"type": "stop_meditation"})
	Game.apply_effects(c.id, [{"kind": "add_progress", "pct_of_need": 1.0}], "capture")
	Game.submit({"type": "report_page_opened", "page": "cultivation"})
	Game.submit({"type": "start_breakthrough", "support_items": []})
	await scene_at("first_breakthrough", "say", 0.3, "Bone Forging", 0, 3600, true)
	await shot("20_first_breakthrough", out)
	await until_idle()
	# Stoneford: the thief in the market, the fair, the sect chosen.
	c.quests.done["the_river_token"] = 1
	c.quests.active.erase("the_river_token")
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	await frames(20)
	await scene_at("market_thief", "say", 0.8, "purse")
	await shot("21_market_thief", out)
	await until_idle()
	Game.world.load_room(c, "sf_fairground", "")
	GameEvents.flush()
	await frames(20)
	await scene_at("fair_arrival", "title", 1.4)
	await shot("22_fair_title", out)
	await scene_at("fair_arrival", "say", 1.2, "Cloud Sect")
	await shot("23_fair_recruiters", out)
	await until_idle()
	main.scenes.queue.append("sect_chosen")
	await scene_at("sect_chosen", "say", 0.0, "Welcome")
	await frames(40)
	await shot("24_sect_chosen_portrait_box", out)
	main.close_all_pages()
	await scene_at("sect_chosen", "title", 1.4)
	await shot("25_sect_chosen", out)
	await until_idle()
	print("topdown_capture: story done")
	get_tree().quit()

## Decision 42 (`-- --night`, into docs/redesign/feedback/hollow_night/): the Hollow Night reworked as an action set
## piece, played in the game with its own director and moments by a character the story has brought there (the short
## blade, the straw hat, three teas): the storm and the river boiling, Dou among the minnows, the first strike's
## hand-off, a school cut down, a villager running for Aunt Ping's door, the grey spreading up the lane, the eel's
## entrance, its tell, its window ashore under the boss bar, the climax as Lu comes and his palm pins it, its fall,
## and the grey lifting.
func hollow_night() -> void:
	var out := "res://docs/redesign/feedback/hollow_night/"
	await _topdown_game(out)
	await frames(240)
	var c = Game.active()
	for q in ["morning_tide", "a_quiet_river", "the_runaway_kite", "mas_delivery", "grannys_remedy", "fists_first", "crab_trouble"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	Unlocks.evaluate(c.id)
	c.inventory.equipped["weapon"] = LootRules.make_instance("training_short_blade", 1, "common", null, 910)
	c.inventory.equipped["hat"] = LootRules.make_instance("plain_straw_hat", 1, "common", null, 911)
	Game.inventory.apply_add(c.id, "herbal_tea", 3, "capture")
	Game.combat.refresh_stats(c.id)
	Game.apply_effects(c.id, ContentDB.entry("quests", "evening_on_the_river").get("rewards", []), "capture")
	GameEvents.flush()
	await frames(20)
	w = main.world
	p = w.player
	m = p.motor
	# The body is kept whole all night (the shots are of the night, not of a fall).
	get_tree().physics_frame.connect(func(): if Game.active() != null and Game.active().pools.max_hp > 0.0: Game.active().pools.hp = Game.active().pools.max_hp)
	# The storm, the river boiling, Dou's cry among the minnows.
	await scene_at("hollow_rises", "title", 1.0)
	await shot("01_that_night_the_storm", out)
	await scene_at("hollow_rises", "camera", 0.15, "dou")
	await shot("02_the_river_boils", out)
	await scene_at("hollow_rises", "say", 1.4, "Grey fish")
	await shot("03_dou_among_the_minnows", out)
	await scene_at("hollow_rises", "say", 1.4, "lamp is lit")
	await shot("04_aunt_ping_at_her_door", out)
	await scene_at("hollow_rises", "handoff", 0.8)
	await shot("05_strike_the_minnows_handoff", out)
	# Old Ma's two minnows cut down (a school struck through), and Ma sent running for the hut.
	await _strike_at("npc_ma_night", "hollow_minnow", 2, out, "06_a_school_cut_down")
	await _send_in("npc_ma_night")
	await scene_at("night_ma_goes", "move", 1.4)
	await shot("07_old_ma_runs_for_the_hut", out)
	# Each run seen through before the next villager is sent in (as a player fighting the minnows on the way would).
	await until_idle()
	await _strike_at("npc_granny_night", "hollow_minnow", 2, out, "")
	await _send_in("npc_granny_night")
	await until_idle()
	await _strike_at("npc_dou_night", "hollow_minnow", 2, out, "")
	await _send_in("npc_dou_night")
	# The fight on the towpath off the square's west end, between the reeds (the eel glides to the player's stretch).
	m.place(w.room.nearest_standable(TopdownRoom.cell_point([19, 33])))
	# The grey spreading up the lane, and the eel's entrance (its boss card), whichever comes first.
	var got := {"lane": false, "card": false}
	for i in 3600:
		var r = main.scenes.run
		if not got.lane and r != null and str(r.id) == "grey_spreads" and r.begun and str(r.row.steps[r.i].get("text", "")).contains("The lane") and float(r.t) >= 1.2:
			await shot("08_the_grey_spreads_up_the_lane", out)
			got.lane = true
		var pl = main.moments.playing
		if not got.card and pl != null and str(pl.row.get("id", "")) == "boss_intro" and float(pl.st) >= 0.8:
			await shot("09_the_eel_rises", out)
			got.card = true
		if got.lane and got.card: break
		var near: EnemyState = _foe("hollow_minnow")
		if near != null and near.plane.distance_to(m.pos) < 50.0 and i % 12 == 0: p.aim_attack((near.plane - m.pos).normalized())
		await frames(1)
	if not got.card: print("  capture: the eel's card not caught")
	for i in 1200:
		if _foe("hollowed_eel") != null: break
		await frames(1)
	var eel: EnemyState = _foe("hollowed_eel")
	for e in Game.room_rt.living_enemies(): if e.def_id == "hollow_minnow": Game.enemies.release(e)
	Game.room_rt.event.waves = []
	await _eel_bank(eel)
	for i in 600:
		c.pools.hp = c.pools.max_hp
		if str(eel.ai.state) == "windup" and float(eel.ai.timer) < 0.6: break
		await frames(1)
	await shot("10_the_eel_rears_its_tell", out)
	var land: Vector2 = eel.ai.get("land", eel.plane)
	m.place(w.room.nearest_standable(land + Vector2(-eel.aim.y, eel.aim.x) * 72.0))
	for i in 600:
		if str(eel.ai.state) == "beached": break
		await frames(1)
	await _strike_eel(eel, 40)
	await shot("11_the_eel_ashore_its_window", out)
	# The climax: below half its HP it dives, Lu comes up the river and his palm pins it as its great lunge lands.
	eel.pools.hp = eel.pools.max_hp * 0.52
	for i in 900:
		c.pools.hp = c.pools.max_hp
		if str(eel.ai.state) == "beached": await _strike_eel(eel, 4)
		elif str(eel.ai.state) != "windup" and eel.plane.distance_to(m.pos) > 130.0: await _eel_bank(eel)
		if int(eel.ai.get("phase", -1)) >= 0: break
		await frames(1)
	await scene_at("lu_arrives", "say", 1.0, "Lu!", 0, 1200)
	await shot("12_the_climax_lu_comes", out)
	for i in 900:
		c.pools.hp = c.pools.max_hp
		var r = main.scenes.run
		if r != null and str(r.id) == "lu_arrives" and r.begun and str(r.row.steps[r.i].do) in ["fx", "sound", "shake", "say"] and int(r.i) > 10: break
		if str(eel.ai.state) == "windup" and eel.ai.get("land", Vector2.INF) != land:
			land = eel.ai.land
			m.place(w.room.nearest_standable(land + Vector2(-eel.aim.y, eel.aim.x) * 72.0))
		await frames(1)
	await frames(3)
	await shot("13_lus_palm_pins_the_eel", out)
	eel.pools.hp = minf(eel.pools.hp, 20.0)
	for i in 600:
		c.pools.hp = c.pools.max_hp
		if not eel.alive: break
		if str(eel.ai.state) in ["attack", "beached"]: await _strike_eel(eel, 2)
		await frames(1)
	await frames(60)
	await shot("14_the_eel_falls", out)
	await scene_at("grey_lifts", "say", 1.6, "held the bank", 0, 1800)
	await shot("15_the_grey_lifts_lu", out)
	await scene_at("grey_lifts", "say", 1.6, "teach it", 0, 900)
	await shot("16_the_palm_you_saw", out)
	await until_idle()
	await frames(90)
	await shot("17_on_lus_boat", out)
	print("topdown_capture: the Hollow Night done")
	get_tree().quit()

## Decision 45 (`-- --first-boss`, into docs/redesign/feedback/first_boss/): the first boss reworked, played in the
## game with its own director, moments, music and effects by a character the story has brought to the night (the short
## blade, the straw hat, three teas): its first phase ashore under the boss bar (its waking notch at 80%), the waking
## cut (the eel reared, the river boiling, the night's colours bruised), the second phase (its surge, the hatched bar,
## a blow glancing off its hide), the player overwhelmed under it, the elders' rescue (Granny Liu's Nine Seals, Old
## Ma's Thousand-Catty Palm, Lu's river dragon), its fall, the elders telling what cultivation is, and Lu's boat with
## the Cultivate button newly on the HUD. The shots are named after_NN_*; before_NN_* are the same moments of the
## night before the rework (the hollow_night capture of build 110).
func first_boss() -> void:
	var out := "res://docs/redesign/feedback/first_boss/"
	await _topdown_game(out)
	await frames(240)
	var c = Game.active()
	for q in ["morning_tide", "a_quiet_river", "the_runaway_kite", "mas_delivery", "grannys_remedy", "fists_first", "crab_trouble"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	Unlocks.evaluate(c.id)
	c.inventory.equipped["weapon"] = LootRules.make_instance("training_short_blade", 1, "common", null, 910)
	c.inventory.equipped["hat"] = LootRules.make_instance("plain_straw_hat", 1, "common", null, 911)
	Game.inventory.apply_add(c.id, "herbal_tea", 3, "capture")
	Game.combat.refresh_stats(c.id)
	Game.apply_effects(c.id, ContentDB.entry("quests", "evening_on_the_river").get("rewards", []), "capture")
	GameEvents.flush()
	await frames(20)
	w = main.world
	p = w.player
	m = p.motor
	# The fight's beats as they come, for the log (the shots are timed on the scenes' steps).
	var heard := {"glance": 0}
	GameEvents.event.connect(func(n: String, pl: Dictionary):
		if n == "hit_landed" and pl.get("glance", false): heard.glance = int(heard.glance) + 1
		if n in ["boss_phase", "boss_overwhelmed", "scene_started", "scene_ended"] or (n == "actor_defeated" and str(pl.get("def", "")) == "hollowed_eel"):
			print("  first boss: %.1f s %s %s" % [Game.sim_time, n, str(pl.get("scene", pl.get("action", pl.get("killer", ""))))]))
	# The villagers sent in at once, their scenes played through (the night's first beats are hollow_night's shots).
	var keep_whole := {"on": true}
	get_tree().physics_frame.connect(func(): if keep_whole.on and Game.active() != null and Game.active().pools.max_hp > 0.0: Game.active().pools.hp = Game.active().pools.max_hp)
	await scene_at("hollow_rises", "handoff", 0.2, "", 0, 3600)
	for f in ["ma_safe", "granny_safe", "dou_safe"]: Game.quest.apply_flag(c.id, f)
	GameEvents.flush()
	m.place(w.room.nearest_standable(TopdownRoom.cell_point([19, 32])))
	for i in 7200:
		if _foe("hollowed_eel") != null and main.scenes.run == null and not main.moments.screen_busy(): break
		var near: EnemyState = _foe("hollow_minnow")
		if near != null and near.plane.distance_to(m.pos) < 50.0 and i % 12 == 0: p.aim_attack((near.plane - m.pos).normalized())
		await frames(1)
	var eel: EnemyState = _foe("hollowed_eel")
	for e in Game.room_rt.living_enemies(): if e.def_id == "hollow_minnow": Game.enemies.release(e)
	Game.room_rt.event.waves = []
	# Phase 1: its window ashore under the boss bar, at 88% (the waking's notch at 80% ahead), once the villagers' own
	# scenes on the way to the hut have played (their balloons off the bar).
	var quiet := 0
	for i in 2400:
		quiet = quiet + 1 if main.scenes.run == null and main.scenes.queue.is_empty() else 0
		if quiet > 45: break
		await frames(1)
	await _eel_bank(eel)
	for i in 900:
		if str(eel.ai.state) == "beached": break
		if str(eel.ai.state) == "windup" and eel.ai.get("land", Vector2.INF) != Vector2.INF:
			var land: Vector2 = eel.ai.land
			m.place(w.room.nearest_standable(land + Vector2(-eel.aim.y, eel.aim.x) * 72.0))
		elif str(eel.ai.state) == "glide" and eel.plane.distance_to(m.pos) > 130.0: await _eel_bank(eel)
		await frames(1)
	eel.pools.hp = eel.pools.max_hp * 0.9
	await _strike_eel(eel, 24)
	await shot("after_01_phase_one_the_eel_ashore", out)
	# The waking: at 80% it throws itself back into the river and rises awake (the cut that holds the fight).
	eel.pools.hp = eel.pools.max_hp * 0.81
	await _strike_eel(eel, 30)
	if int(eel.ai.get("phase", -1)) < 0: eel.pools.hp = eel.pools.max_hp * 0.79
	await scene_at("eel_awakens", "wait", 0.3, "", 0, 2400)
	await shot("after_02_it_wakes_the_river_boils", out)
	await scene_at("eel_awakens", "say", 1.2, "boiling", 0, 2400)
	await shot("after_03_it_wakes_aunt_pings_warning", out)
	await scene_at("eel_awakens", "handoff", 0.4, "", 0, 2400)
	await shot("after_04_phase_two_stay_alive", out)
	# Phase 2: the surge rearing at the player, then a blow glancing off its hide under the hatched bar.
	for i in 900:
		if str(eel.ai.state) == "windup" and int(eel.ai.get("attack", 0)) == 1 and float(eel.ai.timer) < 0.3: break
		if str(eel.ai.state) == "glide" and eel.plane.distance_to(m.pos) > 200.0: await _eel_bank(eel)
		await frames(1)
	await shot("after_05_phase_two_the_surge", out)
	# Once the waking's prompt has gone (its hand-off over), at its next landing.
	for i in 900:
		if main.scenes.run == null and str(eel.ai.state) == "beached": break
		if str(eel.ai.state) == "glide" and eel.plane.distance_to(m.pos) > 200.0: await _eel_bank(eel)
		await frames(1)
	# In front of it (lower on the screen than its body), striking until a blow glances off its hide (at its floor).
	eel.pools.hp = eel.pools.max_hp * float(eel.ai.get("hp_floor", 0.72))
	m.place(w.room.nearest_standable(eel.plane + Vector2(-34, 12)))
	var glanced := int(heard.glance)
	for i in 120:
		if i % 10 == 0: p.aim_attack((eel.plane - m.pos).normalized())
		Game.active().pools.hp = Game.active().pools.max_hp
		await frames(1)
		if int(heard.glance) > glanced:
			await frames(8)
			break
	await shot("after_06_phase_two_its_hide_turns_the_blow", out)
	# Overwhelmed: the body let go; the eel's blows take it to the floor.
	keep_whole.on = false
	for i in 1800:
		if main.scenes.run != null and str(main.scenes.run.id) == "elders_come": break
		if str(eel.ai.state) == "glide" and eel.plane.distance_to(m.pos) > 200.0: await _eel_bank(eel)
		await frames(1)
	await scene_at("elders_come", "say", 1.2, "Get away", 0, 2400)
	await shot("after_07_overwhelmed_the_eel_looms", out)
	await scene_at("elders_come", "say", 1.0, "Old legs", 0, 2400)
	await shot("after_08_granny_liu_comes", out)
	await scene_at("elders_come", "say", 0.15, "Nine seals", 0, 2400)
	await shot("after_09_granny_lius_nine_seals", out)
	await scene_at("elders_come", "say", 1.2, "Thousand-Catty", 0, 2400)
	await shot("after_10_old_ma_comes", out)
	await scene_at("elders_come", "wait", 0.24, "", 1, 2400)
	await shot("after_11_old_mas_thousand_catty_palm", out)
	await scene_at("elders_come", "say", 1.2, "Back to the dark", 0, 2400)
	await shot("after_12_lu_comes_up_the_river", out)
	await scene_at("elders_come", "wait", 0.4, "", 2, 2400)
	await shot("after_13_lus_river_dragon_rises", out)
	await scene_at("elders_come", "wait", 0.08, "", 3, 2400)
	await shot("after_14_the_dragon_strikes", out)
	await scene_at("elders_come", "wait", 0.4, "", 3, 2400)
	await shot("after_15_the_eel_falls", out)
	await scene_at("grey_lifts", "say", 1.6, "cultivation, child", 0, 3600)
	await shot("after_16_what_you_saw_was_cultivation", out)
	await scene_at("grey_lifts", "say", 1.6, "you begin", 0, 2400)
	await shot("after_17_come_to_my_boat", out)
	await until_idle()
	for i in 1800:
		if Game.room_rt != null and Game.room_rt.room_id == "lf_lu_boat" and main.scenes.run != null and str(main.scenes.run.id) == "river_token": break
		await frames(1)
	await scene_at("river_token", "handoff", 0.8, "", 0, 2400)
	await shot("after_18_on_lus_boat_cultivate", out)
	print("topdown_capture: the first boss done")
	get_tree().quit()

func _foe(def_id: String) -> EnemyState:
	for e in Game.room_rt.living_enemies():
		if e.def_id == def_id and e.team == "enemy": return e
	return null

## Beside a villager, strike at their minnows until `n` fall (the body kept whole); a shot mid-fight when named.
func _strike_at(object: String, def_id: String, n: int, out: String, name: String) -> void:
	var o: Dictionary = Game.room_rt.object_def(object)
	if o.is_empty(): return
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	m.place(w.room.spot_near(at, float(o.get("alt", 0.0)), at + Vector2(-40, 30)))
	var down := 0
	var shot_taken := name == ""
	for i in 900:
		Game.active().pools.hp = Game.active().pools.max_hp
		var near: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.def_id == def_id and e.plane.distance_to(at) < 220.0 and (near == null or e.plane.distance_to(m.pos) < near.plane.distance_to(m.pos)): near = e
		if near == null: break
		if near.plane.distance_to(m.pos) > 44.0: m.place(w.room.nearest_standable(near.plane + (m.pos - near.plane).normalized() * 30.0))
		if i % 12 == 0: p.aim_attack((near.plane - m.pos).normalized())
		if not shot_taken and i % 12 == 7:
			await shot(name, out)
			shot_taken = true
		await frames(1)

## Talk to a villager and send them to the hut (the choice with the night's effects).
func _send_in(object: String) -> void:
	var o: Dictionary = Game.room_rt.object_def(object)
	if o.is_empty(): return
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	m.place(w.room.spot_near(at, float(o.get("alt", 0.0)), at + Vector2(0, 40)))
	await frames(4)
	var r := Game.submit({"type": "interact", "object": object})
	for ch in r.get("dialogue", {}).get("choices", []):
		if ch.has("effects"):
			Game.submit({"type": "choose_dialogue", "npc": str(o.get("npc", "")), "choice": ch})
			break
	main.close_all_pages()
	await frames(6)

## On the bank above the eel, where it can reach.
func _eel_bank(eel: EnemyState) -> void:
	m.place(w.room.nearest_standable(eel.plane + Vector2(0, -96)))
	await frames(2)

## Beside the eel ashore, striking for `n` frames' worth of taps.
func _strike_eel(eel: EnemyState, n: int) -> void:
	if eel.plane.distance_to(m.pos) > 44.0: m.place(w.room.nearest_standable(eel.plane + Vector2(-30 if m.pos.x <= eel.plane.x else 30, 0)))
	for i in n:
		if i % 10 == 0: p.aim_attack((eel.plane - m.pos).normalized())
		Game.active().pools.hp = Game.active().pools.max_hp
		await frames(1)

## Wait (at most `limit` frames) until the scene plays the step of kind `kind` whose text or prompt holds `has` (the
## `nth` such step), `after` seconds into it.
func scene_at(id: String, kind: String, after: float, has := "", nth := 0, limit := 900, close_pages := false) -> void:
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

## Wait until no scene holds the stage.
func until_idle(limit := 1800) -> void:
	for i in limit:
		if main.scenes.run == null and not main.scenes.busy(): return
		if main.scenes.run != null and str(main.scenes.run.mode) == "hand":
			return
		await frames(1)

## Talk to a person and pick the choice that takes or hands in a quest, as the dialogue page would.
func choose(object: String, key: String, quest: String) -> void:
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

## `n` shots `gap` frames apart from the step of `kind` on, side by side at half size.
func story_strip(name: String, id: String, kind: String, n: int, gap: int, dir: String) -> void:
	await scene_at(id, kind, 0.0)
	var tiles: Array = []
	for i in n:
		await RenderingServer.frame_post_draw
		var img := get_tree().root.get_texture().get_image()
		img.resize(640, 360, Image.INTERPOLATE_BILINEAR)
		tiles.append(img)
		await frames(gap)
	var strip_img := Image.create(640 * n + 4 * (n - 1), 360, false, Image.FORMAT_RGBA8)
	strip_img.fill(Color("071015"))
	for i in n:
		tiles[i].convert(Image.FORMAT_RGBA8)
		strip_img.blit_rect(tiles[i], Rect2i(0, 0, 640, 360), Vector2i(i * 644, 0))
	strip_img.save_png(dir + name + ".png")

## Stand at a cell of the room on view (its villagers' sheets load in while it waits `n` frames).
func at_spot(cell: Vector2, n: int) -> void:
	w = main.world
	p = w.player
	m = p.motor
	m.place((cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	m.dir = Vector2.DOWN
	w._settle_camera()
	await frames(n)

## An empty square round `at` with these foes ([def, offset]) turned on the player.
func arena(at: Vector2, foes: Array) -> void:
	Game.room_rt.enemies.clear()
	Game.room_rt.spawn_slots.clear()
	Game.room_rt.loot.clear()
	Game.combat.wounded.erase(Game.active_id)
	Game.active().pools.hp = Game.active().pools.max_hp
	main.close_all_pages()
	await start(at)
	for f in foes:
		var e: EnemyState = Game.enemies.spawn_at(str(f[0]), at + (f[1] as Vector2), 1)
		e.altitude = w.room.height_at(e.plane)
		e.threat[Game.active_id] = 1.0
	await frames(20)

func start(at: Vector2) -> void:
	m.place(at)
	m.dir = Vector2.DOWN
	w.cam = w._cam_target()
	await frames(30)

func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
	await get_tree().process_frame

func shot(name: String, dir := OUT) -> void:
	await RenderingServer.frame_post_draw
	get_tree().root.get_texture().get_image().save_png(dir + name + ".png")

## Hold the stick at `axis` for `n` physics frames, pressing Jump / Dodge on the listed ones, and keep a 384x288 crop
## round the body at each frame in `keep`, side by side.
func strip(name: String, axis: Vector2, n: int, jumps: Array, dashes: Array, keep: Array, dir := OUT) -> void:
	var tiles: Array = []
	for f in n + 1:
		if f in keep:
			await RenderingServer.frame_post_draw
			var img := get_tree().root.get_texture().get_image()
			var c: Vector2 = (p.screen - w.camera.position + Vector2(320, 180)) * 2.0 + Vector2(0, -40)
			var r := Rect2i(Vector2i(clampi(int(c.x) - 192, 0, 1280 - 384), clampi(int(c.y) - 144, 0, 720 - 288)), Vector2i(384, 288))
			tiles.append(img.get_region(r))
		if f == n: break
		p.movement = axis
		if f in jumps: p.jump()
		if f in dashes: p.dodge()
		await get_tree().physics_frame
		await get_tree().process_frame
	p.movement = Vector2.ZERO
	var out := Image.create(384 * tiles.size() + 4 * (tiles.size() - 1), 288, false, Image.FORMAT_RGBA8)
	out.fill(Color("071015"))
	for i in tiles.size(): out.blit_rect(tiles[i], Rect2i(0, 0, 384, 288), Vector2i(i * 388, 0))
	out.save_png(dir + name + ".png")

## Decision 42's rollout (`-- --quality --quality-tag=<before|after>`, into
## docs/redesign/feedback/character_quality/rollout/<tag>/): the figure drawn better at the same 38 px (art bible §13),
## shot at the same instants before and after the sheets are rebuilt, the world alone at x2 with the tree held still:
## the village square and Jade Gate Street with the player and the study's villagers staged round them
## (docs/redesign/feedback/character_quality.md), the story's gestures staged on the square, and a fight with the jian
## (the whole view on a cut, and frames of the combo round the body). `boxes.json` has where each body stands on the
## shots (x2 screen px), for tools/art/topdown/study_quality/rollout.py, which pairs the two.
const QUALITY_SCENES := [
	{"name": "01_village_square", "room": "lf_village", "spot": Vector2(33.5, 21.5), "player": ["idle", 0, "s"], "people": [
		["uncle_guo", Vector2(30.3, 22.1), "se", "idle"], ["washer_mei", Vector2(31.9, 24.3), "se", "idle"],
		["little_dou", Vector2(36.7, 22.7), "sw", "idle"], ["shen_lian_npc", Vector2(38.2, 20.3), "sw", "idle"]]},
	{"name": "02_jade_gate_street", "room": "ja_gate_street", "spot": Vector2(24.5, 15.6), "player": ["idle", 0, "s"], "people": [
		["jade_deacon", Vector2(21.2, 14.6), "se", "idle"], ["jade_disciple_b", Vector2(20.6, 17.2), "se", "idle"],
		["jade_steward", Vector2(26.4, 17.8), "sw", "idle"], ["jade_disciple_a", Vector2(28.0, 15.2), "sw", "idle"]]},
	# The story's gestures (decision 39): the player and Shen Lian salute, Guo kneels, Mei points the way, Dou starts back.
	{"name": "04_gestures", "room": "lf_village", "spot": Vector2(33.5, 21.5), "player": ["salute", 2, "se"], "people": [
		["uncle_guo", Vector2(31.2, 22.3), "se", "kneel"], ["washer_mei", Vector2(31.9, 24.3), "e", "point"],
		["little_dou", Vector2(36.2, 22.9), "sw", "startle"], ["shen_lian_npc", Vector2(35.6, 20.8), "sw", "salute"]]},
]
## The frame each gesture is held on for its shot: the bow over the fist, down on the knee, the arm out, the jolt.
const QUALITY_HOLD := {"idle": 0, "salute": 2, "kneel": 2, "point": 1, "startle": 1}

func quality() -> void:
	var tag := "after"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--quality-tag="): tag = a.substr(14)
	var out := "res://docs/redesign/feedback/character_quality/rollout/%s/" % tag
	process_mode = Node.PROCESS_MODE_ALWAYS          # this node runs while the game is held still; the game does not
	main.process_mode = Node.PROCESS_MODE_PAUSABLE
	await _topdown_game(out)
	await frames(360)
	main.hud.visible = false
	var boxes := {}
	for sc in QUALITY_SCENES:
		boxes[sc.name] = await _quality_scene(sc, out)
	boxes["03_fight"] = await _quality_fight(out)
	var f := FileAccess.open(ProjectSettings.globalize_path(out + "boxes.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(boxes, "  ", true))
	f.close()
	main.hud.visible = true
	print("topdown_capture: quality done")
	get_tree().quit()

## One staged shot: the room entered, the player at the spot in their pose, the listed people placed round them in
## theirs (anyone else in the room hidden), the tree held still, then the world alone at x2.
func _quality_scene(sc: Dictionary, out: String) -> Dictionary:
	get_tree().paused = false
	Game.world.load_room(Game.active(), str(sc.room), "", (sc.spot as Vector2) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	w = main.world
	p = w.player
	m = p.motor
	m.place((sc.spot as Vector2) * TopdownRoom.TILE)
	m.dir = Vector2.DOWN
	m.row = "s"
	w._settle_camera()
	await frames(120)
	var found := {}
	for id in w.figures:
		var fig = w.figures[id]
		if not (is_instance_valid(fig) and fig.art is TopdownPlaces.Person): continue
		var npc := str(fig.def.get("npc", ""))
		fig.visible = false
		fig.staged = true
		for pp in sc.people:
			if str(pp[0]) == npc and not found.has(npc): found[npc] = fig
	var staged: Array = []
	var made_here: Array = []
	for pp in sc.people:
		var npc := str(pp[0])
		var fig = found.get(npc)
		if fig == null:
			var made := TopdownPlaces.person(w.room, {"id": "quality_" + npc, "type": "npc", "npc": npc, "at": [0, 0]}, w.sorted, w.overlay, p)
			fig = made[1]
			fig.staged = true
			made_here.append(made)
		var at: Vector2 = (pp[1] as Vector2) * TopdownRoom.TILE
		fig.place(at, w.room.height_at(at))
		fig.visible = true
		var act := TopdownFigure.resolve(str(pp[3]))
		fig.art.rest = str(pp[2])
		fig.art.row = str(pp[2])
		fig.art.stand = act
		fig.art.action = act
		fig.art.t = (float(QUALITY_HOLD.get(act, 0)) + 0.5) / float(TopdownFigure.spec(act).fps)
		staged.append([npc, fig])
	await frames(30)
	get_tree().paused = true
	var pl: Array = sc.player
	p.pose = TopdownFigure.resolve(str(pl[0]))
	p.frame = int(pl[1])
	m.row = str(pl[2])
	p.queue_redraw()
	for s in staged: s[1].art.queue_redraw()
	await get_tree().process_frame
	await get_tree().process_frame
	(await world_shot()).save_png(ProjectSettings.globalize_path(out + sc.name + ".png"))
	var cam: Vector2 = w.camera.position
	var bx := {"player": _on_shot(p.screen, cam), "people": {}}
	for s in staged: bx.people[s[0]] = _on_shot(s[1].feet, cam)
	get_tree().paused = false
	for s in staged: s[1].visible = false
	# The people made for this shot only (not in the room) go with it, so they stand in no later room.
	for made in made_here:
		for n in made:
			if n is Node and is_instance_valid(n): n.queue_free()
	return bx

## Where a point of the world (art px) lands on a world shot (x2 screen px).
func _on_shot(pt: Vector2, cam: Vector2) -> Array:
	var v: Vector2 = (pt - cam + Vector2(TopdownWorld.VIEW) * 0.5) * 2.0
	return [v.x, v.y]

## A fight on the square with the jian, held still: two boarlets and a crab round the player, the three cuts of the combo
## played on the body frame by frame; the whole view on the rising cut's hit, and every frame round the body.
func _quality_fight(out: String) -> Dictionary:
	var c = Game.active()
	Game.inventory.apply_add(c.id, "training_jian", 1, "capture")
	Game.submit({"type": "equip", "index": c.inventory.first_index("training_jian")})
	var cell := Vector2(34.0, 21.0)
	Game.world.load_room(c, "lf_village", "", (cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	await at_spot(cell, 120)
	for id in w.figures:
		var fig = w.figures[id]
		if is_instance_valid(fig) and fig.art is TopdownPlaces.Person:
			fig.visible = false
			fig.staged = true
	Game.room_rt.enemies.clear()
	Game.room_rt.spawn_slots.clear()
	Game.room_rt.loot.clear()
	main.close_all_pages()
	await start(m.pos)
	for f in [["wild_boarlet", Vector2(50, 12)], ["mudshell_crab", Vector2(36, -36)], ["wild_boarlet", Vector2(-46, 20)]]:
		var e: EnemyState = Game.enemies.spawn_at(str(f[0]), m.pos + (f[1] as Vector2), 1)
		e.altitude = w.room.height_at(e.plane)
		e.facing = -1 if (f[1] as Vector2).x > 0 else 1
	await frames(4)
	# The fight held still: the three cuts played on the body frame by frame over the foes as they stand.
	get_tree().paused = true
	m.face(Vector2(1, 0.2))
	var tiles: Array = []
	var bx := {}
	for st in [["swing_1", 6], ["swing_2", 6], ["swing_3", 6]]:
		for i in int(st[1]):
			p.pose = str(st[0])
			p.frame = i
			p.queue_redraw()
			await get_tree().process_frame
			await get_tree().process_frame
			if st[0] == "swing_1" and i == 2:
				(await world_shot()).save_png(ProjectSettings.globalize_path(out + "03_fight.png"))
				bx = {"player": _on_shot(p.screen, w.camera.position), "people": {}}
			tiles.append(await crop(192, 144))
	sheet(out + "03_fight_combo.png", tiles, 6)
	get_tree().paused = false
	return bx

## Decision 43 (`-- --people-scale --people-tag=<before|after>`, into docs/redesign/feedback/people_scale/<tag>/): the
## people drawn about 1.2x bigger (art bible §5 and §13), shot at the same instants before and after the sheets are
## rebuilt. The story's opening in Aunt Ping's hut and the villagers on Home Lane at dawn as the staged scenes play them
## (the whole screen: the letterbox and the balloons over the heads); then, the world alone at x2 with the tree held
## still: the player at the hut's door beside a group of villagers, on the neighbour's roof, inside the hut at its
## door, and a fight with the jian among two boarlets and a crab (the whole view on a cut, and frames round the body).
const PEOPLE_SCENES := [
	{"name": "01_door_hut_people", "room": "lf_village", "spot": Vector2(8.3, 15.3), "player": ["idle", 0, "sw"], "people": [
		["aunt_ping", Vector2(10.3, 16.1), "sw", "idle"], ["washer_mei", Vector2(11.5, 15.4), "sw", "idle"],
		["little_dou", Vector2(10.9, 17.3), "sw", "idle"], ["uncle_guo", Vector2(12.6, 16.8), "sw", "idle"],
		["granny_liu", Vector2(15.2, 15.3), "sw", "idle"]]},
	{"name": "03_roof", "room": "lf_village", "spot": Vector2(18.0, 12.4), "player": ["idle", 0, "s"], "people": [
		["little_dou", Vector2(16.4, 15.4), "se", "point"], ["washer_mei", Vector2(20.2, 15.8), "sw", "idle"]]},
	{"name": "05_interior", "room": "lf_fishers_hut", "spot": Vector2(9.5, 10.8), "player": ["idle", 0, "se"], "people": [
		["aunt_ping", Vector2(6.0, 6.4), "se", "idle"]]},
]

func people_scale() -> void:
	var tag := "after"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--people-tag="): tag = a.substr(13)
	var out := "res://docs/redesign/feedback/people_scale/%s/" % tag
	process_mode = Node.PROCESS_MODE_ALWAYS          # this node runs while the game is held still; the game does not
	main.process_mode = Node.PROCESS_MODE_PAUSABLE
	await _topdown_game(out)
	# The staged scenes: Aunt Ping wakes you in the hut, and the villagers talk on Home Lane at dawn.
	await scene_at("opening_dawn", "say", 1.2)
	await shot("04_scene_hut", out)
	await scene_at("opening_dawn", "handoff", 0.8, "door")
	Game.submit({"type": "use_portal", "portal": "exit", "crossing": true})
	await frames(30)
	await scene_at("river_dawn", "say", 1.5, "Hush")
	await shot("06_scene_home_lane", out)
	await until_idle()
	main.hud.visible = false
	for sc in PEOPLE_SCENES:
		await _quality_scene(sc, out)
	await _quality_fight(out)
	var f := ProjectSettings.globalize_path(out)
	DirAccess.rename_absolute(f + "03_fight.png", f + "02_fight.png")
	DirAccess.rename_absolute(f + "03_fight_combo.png", f + "02_fight_combo.png")
	main.hud.visible = true
	print("topdown_capture: people scale done")
	get_tree().quit()

## Decision 43's monsters (`-- --monsters --monsters-tag=<before|after>`, into docs/redesign/feedback/monsters/<tag>/):
## every foe drawn for the grid staged round the player on the Reed Shallows' flats and held still, the world alone at
## x2 and the lineup at x4: each idle facing the camera (01), in its wind-up's tell turned to the player (02), on its
## strike's hit frame (03), struck (04), falling (05), and the elites beside a plain one (06); the hollowed eel on the
## Hollow Night's river (07); then live fights under the HUD (08-11): the Willow Path's boarlets and a rat, the Marsh
## Edge's hollowed boarlet, otter, frog and leech, the Reed Shallows' Old Snapper and crabs, and the Hollow Night's
## minnows round the player.
const MONSTER_SPOT := Vector2(51, 17)
## [def, offset from the player in cells, elite]
const MONSTER_LINEUP := [["old_snapper", Vector2(-8.5, -3.5), false], ["trial_puppet", Vector2(-4.0, -3.5), false],
	["mossback_toad", Vector2(-0.5, -3.5), false], ["reed_otter", Vector2(3.0, -3.5), false], ["hollowed_boarlet", Vector2(7.0, -3.5), false],
	["mudshell_crab", Vector2(-8.0, 0.5), false], ["reedtail_rat", Vector2(-5.0, 0.5), false], ["wild_boarlet", Vector2(3.0, 0.5), false],
	["reed_frog", Vector2(6.0, 0.5), false], ["marsh_leech", Vector2(8.5, 0.5), false], ["hollow_minnow", Vector2(-2.5, 0.5), false]]
const MONSTER_ELITES := [["wild_boarlet", Vector2(-7.0, -2.0), false], ["wild_boarlet", Vector2(-4.0, -2.0), true],
	["reed_frog", Vector2(-0.5, -2.0), false], ["reed_frog", Vector2(2.0, -2.0), true],
	["mudshell_crab", Vector2(5.0, -2.0), false], ["mudshell_crab", Vector2(8.0, -2.0), true],
	["mossback_toad", Vector2(-7.0, 1.5), false], ["mossback_toad", Vector2(-4.0, 1.5), true],
	["reedtail_rat", Vector2(3.0, 1.5), false], ["reedtail_rat", Vector2(5.5, 1.5), true], ["marsh_leech", Vector2(8.0, 1.5), true]]
const MONSTER_FIGHTS := [["08_fight_willow_path", "wp_east", Vector2(20, 14), [["wild_boarlet", Vector2(3, 2)], ["wild_boarlet", Vector2(-4, 3)], ["reedtail_rat", Vector2(5, -1)]]],
	["09_fight_marsh_edge", "rm_marsh_edge", Vector2(34, 15), [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)], ["reed_frog", Vector2(2, -2)], ["marsh_leech", Vector2(-3, -2)]]],
	["10_fight_reed_shallows", "lf_reed_shallows", Vector2(51, 17), [["old_snapper", Vector2(3, 2)], ["mudshell_crab", Vector2(-3, 1)], ["mudshell_crab", Vector2(-2, -3)]]],
	["11_fight_hollow_night", "lf_village_night", Vector2(33, 32), [["hollow_minnow", Vector2(-3, -2)], ["hollow_minnow", Vector2(4, -3)], ["hollow_minnow", Vector2(2, 3)]]]]

func monsters() -> void:
	var tag := "after"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--monsters-tag="): tag = a.substr(15)
	var out := "res://docs/redesign/feedback/monsters/%s/" % tag
	if "--monsters-polish" in OS.get_cmdline_user_args(): out = "res://docs/redesign/feedback/monsters/polish/%s/" % tag
	process_mode = Node.PROCESS_MODE_ALWAYS          # this node runs while the game is held still; the game does not
	main.process_mode = Node.PROCESS_MODE_PAUSABLE
	await _topdown_game(out)
	await frames(360)
	var c = Game.active()
	get_tree().physics_frame.connect(func(): if Game.active() != null and Game.active().pools.max_hp > 0.0: Game.active().pools.hp = Game.active().pools.max_hp)
	if "--monsters-polish" in OS.get_cmdline_user_args():
		await monsters_polish(out)
		print("topdown_capture: monsters polish done")
		get_tree().quit()
		return
	Game.world.load_room(c, "lf_reed_shallows", "", (MONSTER_SPOT + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	await at_spot(MONSTER_SPOT, 90)
	main.hud.visible = false
	var foes := await _monster_stage(MONSTER_LINEUP)
	for st in [["01_idle", "idle", 0, Vector2.DOWN], ["02_tells", "windup", -1, Vector2(1, 1)], ["03_strikes", "attack", 1, Vector2(1, 1)],
			["04_struck", "hurt", 0, Vector2(1, 1)]]:
		var d: Vector2 = st[3]
		for e in foes: _pose_foe(e, str(st[1]), d if e.plane.x <= m.pos.x else Vector2(-d.x, d.y), int(st[2]))
		await _monster_shot(str(st[0]), out)
	for e in foes:
		Game.combat._damage_enemy(e, e.pools.max_hp * 10.0, c.id, "physical", "none", false, {})
		_pose_foe(e, "death", Vector2.DOWN, -3)
	await _monster_shot("05_falling", out)
	foes = await _monster_stage(MONSTER_ELITES)
	for e in foes: _pose_foe(e, "idle", Vector2(1, 1), 0)
	await _monster_shot("06_elites", out)
	for e in foes: _pose_foe(e, "windup", Vector2(1, 1), -1)
	await _monster_shot("06_elites_tells", out)
	get_tree().paused = false
	# The hollowed eel on the night's river.
	Game.world.load_room(c, "lf_village_night", "", (Vector2(33, 32) + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	await at_spot(Vector2(33, 32), 120)
	var eel := _foe("hollowed_eel")
	if eel == null: eel = Game.enemies.spawn_at("hollowed_eel", Vector2(1500, 950), 2)   # as the night's event raises it
	if eel != null:
		var pc := TopdownRoom.cell_of(m.pos)   # in the river straight south of the square
		for dy in range(1, 24):
			if w.room.is_water(pc.x, pc.y + dy):
				eel.plane = (Vector2(pc.x, pc.y + dy + 1) + Vector2(0.5, 0.5)) * TopdownRoom.TILE
				break
		eel.altitude = w.room.height_at(eel.plane)
		eel.ai.state = "idle"
		eel.ai.timer = 99.0
	await frames(30)
	if eel != null:
		m.place(w.room.nearest_standable(eel.plane + Vector2(-40, -110)))
		w._settle_camera()
		await frames(30)
		get_tree().paused = true
		for st in [["07_eel_idle", "idle", 0], ["07_eel_tell", "windup", -1], ["07_eel_strike", "attack", 1]]:
			_pose_foe(eel, str(st[1]), (m.pos - eel.plane).normalized(), int(st[2]))
			await get_tree().process_frame
			await get_tree().process_frame
			(await world_shot()).save_png(ProjectSettings.globalize_path(out + str(st[0]) + ".png"))
		get_tree().paused = false
	main.hud.visible = true
	# Live fights under the HUD, the body kept whole.
	for s in MONSTER_FIGHTS:
		Game.world.load_room(c, str(s[1]), "", (s[2] as Vector2 + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(10)
		await at_spot(s[2], 60)
		for f in s[3]:
			var at: Vector2 = w.room.nearest_standable((s[2] + f[1] + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
			var e: EnemyState = Game.enemies.spawn_at(str(f[0]), at, 1)
			e.altitude = w.room.height_at(e.plane)
			e.threat[Game.active_id] = 1.0
		for i in 150: await frames(1)
		await shot(str(s[0]), out)
		await RenderingServer.frame_post_draw
		var vi: Image = w.viewport.get_texture().get_image()
		var at: Vector2i = Vector2i(p.screen - w.camera.position + Vector2(320, 180)) - Vector2i(160, 90)
		var crop := vi.get_region(Rect2i(at.clamp(Vector2i.ZERO, Vector2i(320, 180)), Vector2i(320, 180)))
		crop.resize(1280, 720, Image.INTERPOLATE_NEAREST)
		crop.save_png(ProjectSettings.globalize_path(out + str(s[0]) + "_x4.png"))
	print("topdown_capture: monsters done")
	get_tree().quit()

## Decision 44's foe polish (`-- --monsters --monsters-polish --monsters-tag=<before|after>`, into
## docs/redesign/feedback/monsters/polish/<tag>/): the four-legged foes (both boarlets and an elite, the rat, the otter,
## the toad and the crab) and the marsh leech and its elite staged round the player on the Reed Shallows' flats and held
## still, the world alone at x2 and the lineup at x4: facing the camera (S) idle, mid-stride, in the tell and on the hit
## (12-15), walking away (N) idle, mid-stride and in the tell (16-18), and three quarters (SE) idle and in the tell
## (19-20); then leeches looping on the bank beside a leech and an elite swimming in the river (21).
const POLISH_LINEUP := [["wild_boarlet", Vector2(-4.5, -2.2), false], ["hollowed_boarlet", Vector2(-1.5, -2.2), false],
	["wild_boarlet", Vector2(1.5, -2.2), true], ["reedtail_rat", Vector2(4.5, -2.2), false],
	["reed_otter", Vector2(-4.5, 1.0), false], ["mossback_toad", Vector2(-1.5, 1.0), false], ["mudshell_crab", Vector2(1.5, 1.0), false],
	["marsh_leech", Vector2(3.4, 1.0), false], ["marsh_leech", Vector2(5.2, 1.0), true]]

func monsters_polish(out: String) -> void:
	var c = Game.active()
	Game.world.load_room(c, "lf_reed_shallows", "", (MONSTER_SPOT + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	await at_spot(MONSTER_SPOT, 90)
	main.hud.visible = false
	var foes := await _monster_stage(POLISH_LINEUP)
	for st in [["12_head_on", "idle", 0, Vector2.DOWN], ["13_head_on_walk", "walk", 2, Vector2.DOWN],
			["14_head_on_tells", "windup", -1, Vector2.DOWN], ["15_head_on_strikes", "attack", 1, Vector2.DOWN],
			["16_tail_on", "idle", 0, Vector2.UP], ["17_tail_on_walk", "walk", 2, Vector2.UP], ["18_tail_on_tells", "windup", -1, Vector2.UP],
			["19_three_quarter", "idle", 0, Vector2(1, 1)], ["20_three_quarter_tells", "windup", -1, Vector2(1, 1)]]:
		for e in foes: _pose_foe(e, str(st[1]), st[3], int(st[2]))
		await _monster_shot(str(st[0]), out)
	# Leeches on the bank (looping, drawn up and stretched out) and in the river (swimming), the player between them.
	get_tree().paused = false
	var bank := MONSTER_SPOT + Vector2(0, 4.9)
	var leeches: Array = await _monster_stage([["marsh_leech", Vector2(-4.4, 4.6), false], ["marsh_leech", Vector2(-2.2, 5.0), false]])
	m.place((bank + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	w._settle_camera()
	get_tree().paused = false
	var river: Array = []
	for k in 2:
		river.append((MONSTER_SPOT + Vector2(1.6 + k * 2.6, 6.0 + k * 0.35) + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		var e: EnemyState = Game.enemies.spawn_at("marsh_leech", river[k], 1, {"elite": k == 1})
		e.ai.state = "idle"
		e.ai.timer = 99.0
		leeches.append(e)
	await frames(20)
	get_tree().paused = true
	for k in 2:   # held in the water (a body at the bank is walked back out of it while the game runs)
		leeches[2 + k].plane = river[k]
		leeches[2 + k].altitude = w.room.height_at(river[k])
	_pose_foe(leeches[0], "walk", Vector2(1, 0), 0)
	_pose_foe(leeches[1], "walk", Vector2(1, 0), 4)
	_pose_foe(leeches[2], "swim", Vector2(1, 0), 2)
	_pose_foe(leeches[3], "swim", Vector2(-1, 0), 5)
	await _monster_shot("21_leech_bank_and_river", out)
	get_tree().paused = false

## The lineup ([def, offset in cells, elite]) set round the player on the room's floor, the room's own foes and people
## cleared, each doing nothing until it is posed; the game is then held still.
func _monster_stage(list: Array) -> Array:
	get_tree().paused = false
	Game.room_rt.enemies.clear()
	Game.room_rt.spawn_slots.clear()
	Game.room_rt.loot.clear()
	for id in w.figures:
		var fig = w.figures[id]
		if is_instance_valid(fig) and fig.art is TopdownPlaces.Person:
			fig.visible = false
			fig.staged = true
	m.place((MONSTER_SPOT + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	m.dir = Vector2.DOWN
	m.row = "s"
	w._settle_camera()
	var out: Array = []
	for f in list:
		var at: Vector2 = w.room.nearest_standable((MONSTER_SPOT + (f[1] as Vector2) + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		var e: EnemyState = Game.enemies.spawn_at(str(f[0]), at, 1, {"elite": bool(f[2])})
		e.altitude = w.room.height_at(e.plane)
		e.ai.state = "idle"
		e.ai.timer = 99.0
		out.append(e)
	await frames(20)
	get_tree().paused = true
	return out

## A foe held on frame `i` of `act` (negative counts from the end), turned toward `dir`.
func _pose_foe(e: EnemyState, act: String, dir: Vector2, i: int) -> void:
	var fv = w.foe_views.get(e.uid)
	if fv == null or fv.art != null: return
	e.velocity = Vector2.ZERO
	e.aim = dir.normalized()
	e.flash = 0.0
	e.knockback = 0.0
	if e.alive: e.ai.state = {"hurt": "stagger", "windup": "windup", "attack": "attack"}.get(act, "aggro")
	e.action = act
	fv.state = str(e.ai.state)
	fv.facing = TopdownMotor.nearest_row(dir, "s", fv.FACINGS)
	fv.last = act
	var a: Dictionary = fv.acts.get(act, {})
	var n: int = (a.get("frames", {}).get("s", [[0, 0]]) as Array).size()
	fv.t = (float(posmod(i, n)) + 0.5) / float(a.get("fps", 6))
	fv.sync(0.0)

## The world alone at x2, and the lineup round the player at x4.
func _monster_shot(name: String, out: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := await world_shot()
	img.save_png(ProjectSettings.globalize_path(out + name + ".png"))
	var at := Vector2i((p.screen - w.camera.position + Vector2(320, 180)) * 2.0) - Vector2i(340, 230)
	var crop := img.get_region(Rect2i(at.clamp(Vector2i.ZERO, Vector2i(1280 - 680, 720 - 320)), Vector2i(680, 320)))
	crop.resize(1360, 640, Image.INTERPOLATE_NEAREST)
	crop.save_png(ProjectSettings.globalize_path(out + name + "_x4.png"))
