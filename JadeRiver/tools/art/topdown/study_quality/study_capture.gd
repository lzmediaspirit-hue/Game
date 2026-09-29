extends Node
## Decision 42's character-quality study: the village square and Jade Gate Street with the player and four villagers,
## shot in the game with its own compositor (TopdownFigure) four ways, the same instant each time (the tree paused):
##   A  today's sheets (art/topdown/character/), untouched;
##   B, D  the study's sheets (tools/art/topdown/study_quality/build_study.py), drawn by TopdownFigure as they are;
##   C  the study's sheets at twice the density, drawn by StudyFigure (TopdownFigure at half scale) into the world
##      viewport rendered at 1280x720, the camera at zoom 2, so the tiles stay two screen px to the art px.
## Then the player's run and rising cut, frame by frame in S and SE, cut round the body. Everything lands in
## `--out` (default: tools/art/topdown/study_quality/build/shots/) for compose.py. The game's files are not touched:
## the study's index is set as TopdownFigure's manifest and its sheets put into Wardrobe's texture cache for the
## shots, then the game's own manifest is restored.
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . \
##       res://tools/art/topdown/study_quality/study_capture.tscn -- [--build=<dir>] [--out=<dir>] [--only=A,B]

const StudyFigure := preload("res://tools/art/topdown/study_quality/study_figure.gd")
const SAVES := "user://study_quality_saves/"
const PLAYER := {"body": "light", "hair": "topknot", "hair_color": 0, "shirt": "disciple", "pants": "loose",
	"shoes": "slippers", "hat": "none", "cape": "none", "weapon": "sword"}
## Each scene: the room, the player's cell, and the villagers [npc, cell, row] staged round the player.
const SCENES := [
	{"name": "01_village_square", "room": "lf_village", "spot": Vector2(33.5, 21.5), "people": [
		["uncle_guo", Vector2(30.3, 22.1), "se"], ["washer_mei", Vector2(31.9, 24.3), "se"],
		["little_dou", Vector2(36.7, 22.7), "sw"], ["shen_lian_npc", Vector2(38.2, 20.3), "sw"]]},
	{"name": "02_jade_gate_street", "room": "ja_gate_street", "spot": Vector2(24.5, 15.6), "people": [
		["jade_deacon", Vector2(21.2, 14.6), "se"], ["jade_disciple_b", Vector2(20.6, 17.2), "se"],
		["jade_steward", Vector2(26.4, 17.8), "sw"], ["jade_disciple_a", Vector2(28.0, 15.2), "sw"]]},
]
const STRIPS := [["run", 8], ["swing_1", 6]]
var main
var w
var build_dir := ""
var out := ""
var only: Array = ["A", "B", "C", "D"]
var studies: Dictionary = {}     ## option -> its index, as TopdownFigure.manifest() would hold it
var game_man: Dictionary = {}
var staged: Array = []           ## [npc, Figure] of the scene on view
var boxes: Dictionary = {}

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	call_deferred("_main")

func _main() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--build="): build_dir = a.substr(8)
		elif a.begins_with("--out="): out = a.substr(6)
		elif a.begins_with("--only="): only = Array(a.substr(7).split(","))
	if build_dir == "": build_dir = ProjectSettings.globalize_path("res://tools/art/topdown/study_quality/build/")
	if not build_dir.ends_with("/"): build_dir += "/"
	if out == "": out = build_dir + "shots/"
	if not out.ends_with("/"): out += "/"
	DirAccess.make_dir_recursive_absolute(out)
	DirAccess.make_dir_recursive_absolute(SAVES)
	for f in DirAccess.get_files_at(SAVES): DirAccess.remove_absolute(SAVES + f)
	TopdownLight.debug_hour = 0.375   # midday, as every review shot
	main = load("res://scenes/main.tscn").instantiate()
	main.process_mode = Node.PROCESS_MODE_PAUSABLE   # this node runs while the game is held still; the game does not
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(SAVES)
	Game.boot()
	Game.autosave_enabled = false
	game_man = TopdownFigure.manifest().duplicate()
	for opt in ["B", "C", "D"]:
		if opt in only: _load_study(opt)
	for i in 3600:
		if main.PAGES.values().all(func(q): return ResourceLoader.load_threaded_get_status(str(q)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS): break
		await get_tree().process_frame
	main.enter_topdown_tutorial(false)
	await frames(360)
	for sc in SCENES:
		await scene(sc)
	TopdownFigure._man = game_man
	var f := FileAccess.open(out + "boxes.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(boxes, "  ", true))
	f.close()
	print("study_capture: done")
	get_tree().quit()

## An option's index and sheets from the build folder: the rects as the compositor wants them, each sheet into
## Wardrobe's cache under the name the index gives it.
func _load_study(opt: String) -> void:
	var dir := build_dir + opt + "/"
	var d = JSON.parse_string(FileAccess.get_file_as_string(dir + "index.json"))
	if not d is Dictionary:
		push_error("study_capture: no index in " + dir)
		return
	d.sets = {"study": []}
	d.stale_sets = []
	for cat in d.items:
		for name in d.items[cat]:
			var it: Dictionary = d.items[cat][name]
			it.set = "study"
			for sec in it.sections: sec.rects = PackedInt32Array(sec.rects)
			d.sets.study.append("%s:%s" % [cat, name])
	for fn in DirAccess.get_files_at(dir):
		if not fn.ends_with(".png"): continue
		var img := Image.load_from_file(dir + fn)
		Wardrobe.textures["res://study_quality/%s/%s" % [opt, fn]] = ImageTexture.create_from_image(img)
	studies[opt] = d

## One scene: the room entered, the player at the spot facing south, the villagers staged round them (anyone else in
## the room hidden), the tree paused, then each option dressed on the same instant and shot.
func scene(sc: Dictionary) -> void:
	get_tree().paused = false
	Game.world.load_room(Game.active(), str(sc.room), "", (sc.spot as Vector2) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	w = main.world
	var p = w.player
	p.motor.place((sc.spot as Vector2) * TopdownRoom.TILE)
	p.motor.dir = Vector2.DOWN
	p.motor.row = "s"
	w._settle_camera()
	await frames(120)
	staged.clear()
	var found := {}
	for id in w.figures:
		var fig = w.figures[id]
		if not (is_instance_valid(fig) and fig.art is TopdownPlaces.Person): continue
		var npc := str(fig.def.get("npc", ""))
		fig.visible = false
		fig.staged = true
		for pp in sc.people:
			if str(pp[0]) == npc and not found.has(npc): found[npc] = fig
	for pp in sc.people:
		var npc := str(pp[0])
		var fig = found.get(npc)
		if fig == null:
			var made := TopdownPlaces.person(w.room, {"id": "study_" + npc, "type": "npc", "npc": npc, "at": [0, 0]}, w.sorted, w.overlay, p)
			fig = made[1]
			fig.staged = true
		var at: Vector2 = (pp[1] as Vector2) * TopdownRoom.TILE
		fig.place(at, w.room.height_at(at))
		fig.visible = true
		fig.art.rest = str(pp[2])
		fig.art.row = str(pp[2])
		fig.art.action = "idle"
		fig.art.stand = "idle"
		fig.art.t = 0.0
		staged.append([npc, fig])
	await frames(30)
	get_tree().paused = true
	p.pose = "idle"
	p.frame = 0
	var cam: Vector2 = w.camera.position
	var bx := {"camera": [cam.x, cam.y], "player": [p.screen.x, p.screen.y], "people": {}}
	for s in staged: bx.people[s[0]] = [s[1].feet.x, s[1].feet.y]
	boxes[sc.name] = bx
	for opt in ["A", "B", "C", "D"]:
		if not opt in only: continue
		if opt != "A" and not studies.has(opt): continue
		await dress(opt)
		(await world_shot()).save_png(out + "%s_%s.png" % [sc.name, opt])
		if sc.name == str(SCENES[0].name):
			await strips(opt)
	await dress("A")
	get_tree().paused = false

## Everyone on view in the option's sheets (A: the game's own).
func dress(opt: String) -> void:
	var dense := opt == "C"
	TopdownFigure._man = game_man if opt == "A" else studies[opt]
	var p = w.player
	p.figure = _figure(PLAYER, dense)
	for s in staged:
		s[1].art.figure = _figure(TopdownFigure.DialoguePage.full_outfit(ContentDB.entry("npcs", str(s[0])).get("outfit", {})), dense)
		s[1].art.queue_redraw()
	_view(dense)
	p.queue_redraw()
	await frames(3)

func _figure(o: Dictionary, dense: bool) -> TopdownFigure:
	if not dense: return TopdownFigure.wearing(o)
	var f = StudyFigure.new()
	f.density = 2.0
	f.set_outfit(o)
	return f

## The world viewport at the art resolution (x2 by its container), or for C at the screen's with the camera at zoom 2.
func _view(dense: bool) -> void:
	if dense:
		w.container.stretch = false
		w.viewport.size = Vector2i(TopdownWorld.VIEW * 2)
		w.camera.zoom = Vector2(2, 2)
	else:
		w.container.stretch = false
		w.viewport.size = TopdownWorld.VIEW
		w.container.stretch = true
		w.camera.zoom = Vector2.ONE

## The world on view at 1280x720 (A, B, D: the 640x360 view doubled, nearest; C: as drawn). The view as drawn is
## kept too (`raw_`), for the phone's own scale.
func world_shot() -> Image:
	await RenderingServer.frame_post_draw
	var img: Image = w.viewport.get_texture().get_image()
	if img.get_width() < 1280: img.resize(img.get_width() * 2, img.get_height() * 2, Image.INTERPOLATE_NEAREST)
	return img

## The player's run and rising cut in S and SE, the villagers stepped out, each frame cut 240x260 round the feet at
## 1280x720.
func strips(opt: String) -> void:
	var p = w.player
	for s in staged: s[1].visible = false      # the body alone on the paving
	for st in STRIPS:
		for row in ["s", "se"]:
			for i in int(st[1]):
				p.pose = str(st[0])
				p.frame = i
				p.motor.row = row
				p.queue_redraw()
				await frames(2)
				var img := await world_shot()
				var c: Vector2 = (p.screen - w.camera.position) * 2.0 + Vector2(640, 360)
				var r := Rect2i(Vector2i(int(c.x) - 120, int(c.y) - 200), Vector2i(240, 260))
				img.get_region(r).save_png(out + "strip_%s_%s_%s_%d.png" % [opt, st[0], row, i])
	p.pose = "idle"
	p.frame = 0
	p.motor.row = "s"
	p.queue_redraw()
	for s in staged: s[1].visible = true

func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
