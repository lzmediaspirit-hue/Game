extends Node
## Screenshots and frame strips of the top-down prototype room (redesign Phase 1) for docs/redesign/phase1/: the square
## under the HUD, walking behind the house, jumping the pier's gap and the long jump, and standing on the low wall with
## the shadow in the air. It plays the real room through the HUD's own player fields on its own saves.
## Needs a renderer:
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/topdown_capture.tscn

const OUT := "res://docs/redesign/phase1/"
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

func start(at: Vector2) -> void:
	m.place(at)
	m.dir = Vector2.DOWN
	w.cam = w._cam_target()
	await frames(30)

func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
	await get_tree().process_frame

func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_tree().root.get_texture().get_image().save_png(OUT + name + ".png")

## Hold the stick at `axis` for `n` physics frames, pressing Jump / Dodge on the listed ones, and keep a 384x288 crop
## round the body at each frame in `keep`, side by side.
func strip(name: String, axis: Vector2, n: int, jumps: Array, dashes: Array, keep: Array) -> void:
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
	out.save_png(OUT + name + ".png")
