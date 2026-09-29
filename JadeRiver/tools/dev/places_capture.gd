extends Node
## Decision 43, systems as places (docs/redesign/systems_as_places.md, "As built"): the review shots, into
## docs/redesign/feedback/places/. Each place in the world with its state, under the HUD and, for the detail, the world
## alone cropped round it and doubled (nearest): the notice board's papers and its gold "!", the letter box's ribbon and
## flag, the Storehouse's sacks, Proprietor Fang's stall, the meditation mat's Qi mist, the courier post, the smoking
## furnace and its ready wisp, the ripe beds; the same corner quiet; the minimap's marks; the world map's Places view;
## the Menu's Storage entry ("At the Storehouse") with its place card; and the walk the card's Travel button starts,
## arrived. A top-down character of its own on saves of its own (never the Max Tester's), the story's staged scenes
## marked seen, the systems opened by the debug unlock.
## Needs a renderer:
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/places_capture.tscn

const OUT := "res://docs/redesign/feedback/places/"
const SAVES := "user://places_capture_saves/"
const OPEN := ["mail", "notice_board", "storage", "alchemy", "auto_refine", "herb_garden", "teleport_stones", "cooking", "world_menu",
	"qi_springs", "seclusion", "smithing"]
var main
var w

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	DirAccess.make_dir_recursive_absolute(SAVES)
	for f in DirAccess.get_files_at(SAVES): DirAccess.remove_absolute(SAVES + f)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for f in DirAccess.get_files_at(ProjectSettings.globalize_path(OUT)):
		if f.ends_with(".png"): DirAccess.remove_absolute(ProjectSettings.globalize_path(OUT) + f)
	TopdownLight.debug_hour = 0.375
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(SAVES)
	Game.boot()
	Game.autosave_enabled = false
	Game.calendar.debug_weather = "clear"
	for i in 3600:
		if main.PAGES.values().all(func(q): return ResourceLoader.load_threaded_get_status(str(q)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS): break
		await get_tree().process_frame
	Game.submit({"type": "create_character", "slot": 1, "name": "Lin Places", "appearance": {"hair": "topknot"}, "view": "topdown"})
	var c = Game.character("c1")
	for sc in ContentDB.all("scenes"): c.quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	c.quests.flags["prologue_done"] = true   # the village's notice board goes up once the prologue is done
	c.cultivator.realm_key = "qi_kindling_5"
	c.training_sect = {"id": "jade_sect", "rank": "outer", "contribution": 0}
	c.position = {"room": "lf_village", "portal": "", "x": 35.5 * 32.0, "y": 19.5 * 32.0, "facing": 1}
	for rid in ["lf_village", "lf_fishers_hut", "wp_east", "wp_west", "sf_gate", "sf_market", "sf_artisan_row", "sf_fairground", "ja_gate_street",
		"ja_herb_terraces"]:
		Game.account.visited_rooms[rid] = true
	main.enter_world(1)
	await frames(240)
	c = Game.active()
	Unlocks.grant_prologue(c.id)   # the HUD whole: the minimap, the tracker, the Menu
	for s in OPEN: Unlocks.force_unlock(c.id, s)
	GameEvents.flush()
	await frames(30)
	main.hud.toasts.clear()   # the unlocks' notices would stand over the square's places
	main.hud.log_lines.clear()
	# What waits: a letter, notices not read, things in the storehouse.
	Game.mail.apply_send(c.id, "places_review", [], {})
	var stock := [{"id": "herbal_tea", "count": 6}, {"id": "riverfish_soup", "count": 2}, {"id": "spirit_stone_shard", "count": 9},
		{"id": "boar_bone_broth", "count": 1}, {"id": "willow_moss", "count": 12}, {"id": "herb_sickle", "count": 1}, {"id": "old_pickaxe", "count": 1},
		{"id": "bamboo_rod", "count": 1}, {"id": "clay_pot", "count": 1}, {"id": "reed_net", "count": 1}, {"id": "healing_pill", "count": 3},
		{"id": "qi_pill", "count": 2}, {"id": "herbal_tea", "count": 1}, {"id": "riverfish_soup", "count": 1}, {"id": "willow_moss", "count": 1},
		{"id": "spirit_stone_shard", "count": 1}, {"id": "healing_pill", "count": 1}, {"id": "qi_pill", "count": 1}]
	Game.account.storage["items"] = stock.duplicate(true)
	# Lotus Ferry, the first home: its services round the square (shrine, letter box, notice board, the Storehouse).
	await at("lf_village", Vector2(35, 19), 120)
	await shot("01_lotus_ferry_services")
	await detail("02_lotus_ferry_services_detail", Vector2(38.5, 13.5), Vector2(520, 200))
	# The same corner quiet: the letter read, the board read, the storehouse emptied.
	for m in Game.account.mail: m["read"] = true
	PlaceRules.read_board(Game, c)
	Game.account.storage["items"] = []
	await frames(40)
	await detail("03_lotus_ferry_services_quiet", Vector2(38.5, 13.5), Vector2(520, 200))
	Game.account.storage["items"] = stock.duplicate(true)
	Game.mail.apply_send(c.id, "places_review", [], {})
	# The meditation mat by the spring, its Qi mist over it.
	await at("lf_village", Vector2(28, 26), 90)
	await shot("04_meditation_mat_by_the_spring")
	await detail("05_meditation_mat_detail", Vector2(25, 26.5), Vector2(220, 130))
	# The minimap's marks, cropped and tripled; a letter waits (the gold spark on the letter box).
	await at("lf_village", Vector2(35, 19), 30)
	await crop("06_minimap_marks", Rect2i(1024, 8, 248, 156), 3)
	# Market Street: Proprietor Fang's stall, the notice board (a new notice: its "!"), the Market Storehouse; the
	# courier post and the teleport stone.
	for f in c.quests.flags.keys():
		if str(f).begins_with(PlaceRules.SEEN): c.quests.flags.erase(f)
	await at("sf_market", Vector2(19, 17), 90)
	await shot("07_market_stall_board_storehouse")
	await detail("08_market_stall_detail", Vector2(15.5, 12), Vector2(360, 200))
	await at("sf_market", Vector2(44, 17), 60)
	await detail("09_market_courier_post_teleport_stone", Vector2(35, 18), Vector2(420, 190))
	# Walking up to a place: the body in front of the notice board, the board behind it (never over its head).
	await at("sf_market", Vector2(20, 14), 40)
	await detail("10_walked_up_to_the_board", Vector2(20, 12.5), Vector2(220, 170))
	# The Artisan Row furnace: smoke while a batch is in it, a jade wisp once one is ready.
	c.crafting["auto_queue"] = [{"recipe": "healing_pill", "count": 2, "done_utc": Clock.now_utc() + 900.0, "quality": "common"}]
	await at("sf_artisan_row", Vector2(47, 15), 90)
	await detail("11_artisan_row_furnace_working", Vector2(52, 9.5), Vector2(220, 200))
	c.crafting["auto_queue"] = [{"recipe": "healing_pill", "count": 2, "done_utc": Clock.now_utc() - 5.0, "quality": "common"}]
	await frames(60)
	await detail("12_artisan_row_furnace_ready", Vector2(52, 9.5), Vector2(220, 200))
	c.crafting["auto_queue"] = []
	# The Herb Terraces: one bed ripe (its glints), one growing, one bare.
	var fams: Dictionary = ContentDB.config("garden").get("families", {})
	var herb := str(fams[fams.keys()[0]].get("10", "")) if not fams.is_empty() else ""
	for b in [["bed_0", 1.0], ["bed_1", 0.45]]:
		var rec: Dictionary = Game.crafting.bed_record(c, "ja_herb_terraces:" + str(b[0]))
		rec.herb = herb
		rec.progress = float(b[1])
		rec.updated = Clock.now_utc()
		rec.grow_s = 360000.0
	await at("ja_herb_terraces", Vector2(21, 16), 90)
	await detail("13_herb_terraces_beds", Vector2(20, 15.5), Vector2(420, 220))
	# The world map's Places view: the notice boards, then the storehouses with the chosen one's card.
	await at("lf_village", Vector2(12, 20), 30)
	main.open_page("world_map", {"view": "places", "kind": "notice_board"})
	await frames(90)
	await shot("14_world_map_places_boards")
	main.close_all_pages()
	await frames(10)
	main.open_page("world_map", {"place": "lf_storehouse"})
	await frames(90)
	await shot("15_world_map_places_storehouse")
	main.close_all_pages()
	await frames(10)
	# The Menu: Storage and the Garden say where they live; the place card offers the walk.
	main.open_page("menu", {})
	await frames(90)
	await shot("16_menu_storage_at_the_storehouse")
	var menu = main.pages.back() if not main.pages.is_empty() else null
	if menu != null: menu.on_action("open", "storage")
	await frames(40)
	await shot("17_menu_place_card")
	# Travel: the walk from Home Lane to the storehouse, arrived and facing it.
	if menu != null: menu.on_action("card_travel", "lf_storehouse")
	for i in 1800:
		await get_tree().physics_frame
		if Game.world.auto_path_target(c) == "": break
	await frames(30)
	await shot("18_travel_arrived_at_the_storehouse")
	# From another area the card's button is Travel there (the Market's teleport stone is a place-only system).
	await at("sf_market", Vector2(30, 17), 30)
	main.open_page("menu", {})
	await frames(60)
	menu = main.pages.back() if not main.pages.is_empty() else null
	if menu != null: menu.on_action("open", "storage")
	await frames(40)
	await shot("19_menu_place_card_from_another_area")
	main.close_all_pages()
	print("places_capture: done, %s" % ProjectSettings.globalize_path(OUT))
	get_tree().quit()

## Stand the body at a cell of a room (entered through the World authority) and let the view settle.
func at(room: String, cell: Vector2, n: int) -> void:
	if Game.room_rt == null or Game.room_rt.room_id != room:
		Game.world.load_room(Game.active(), room, "", (cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(20)
	w = main.world
	w.player.motor.place((cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	w.player.motor.dir = Vector2.DOWN
	w._settle_camera()
	main.hud.toasts.clear()
	await frames(n)

func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
	await get_tree().process_frame

func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_tree().root.get_texture().get_image().save_png(OUT + name + ".png")

func crop(name: String, r: Rect2i, k: int) -> void:
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image().get_region(r)
	img.resize(r.size.x * k, r.size.y * k, Image.INTERPOLATE_NEAREST)
	img.save_png(OUT + name + ".png")

## The world alone (no HUD, no names) round a cell: `size` screen px about it, doubled.
func detail(name: String, cell: Vector2, size: Vector2) -> void:
	main.hud.visible = false
	w.overlay.visible = false
	await frames(2)
	var art := (cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE / TopdownRoom.ART
	var at: Vector2 = (art - w.camera.position + Vector2(TopdownRoom.VIEW) * 0.5) * 2.0
	var r := Rect2i(Vector2i((at - size * 0.5).round()), Vector2i(size))
	r.position.x = clampi(r.position.x, 0, 1280 - r.size.x)
	r.position.y = clampi(r.position.y, 0, 720 - r.size.y)
	await crop(name, r, 2)
	main.hud.visible = true
	w.overlay.visible = true
