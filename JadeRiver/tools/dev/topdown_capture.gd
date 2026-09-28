extends Node
## Screenshots and frame strips of the top-down prototype room (redesign Phase 1) for docs/redesign/phase1/: the square
## under the HUD, walking behind the house, jumping the pier's gap and the long jump, and standing on the low wall with
## the shadow in the air. It plays the real room through the HUD's own player fields on its own saves.
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
	DirAccess.make_dir_recursive_absolute(SAVES)
	for f in DirAccess.get_files_at(SAVES): DirAccess.remove_absolute(SAVES + f)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(SAVES)
	Game.boot()
	Game.autosave_enabled = false
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
