extends Control
## Game shell (S35): boot → title → character selection → creator → world.
## Hosts the backdrop, the room world, the HUD and a stack of pages. It only
## routes intents and signals; every rule lives behind `Game.submit`.

const World = preload("res://scripts/world.gd")
const Hud = preload("res://scripts/hud.gd")
const Backdrop = preload("res://scripts/backdrop.gd")

const PAGES := {
	"menu": "res://scripts/ui/pages/menu_page.gd",
	"inventory": "res://scripts/ui/pages/inventory_page.gd",
	"character": "res://scripts/ui/pages/character_page.gd",
	"cultivation": "res://scripts/ui/pages/cultivation_page.gd",
	"breakthrough": "res://scripts/ui/pages/breakthrough_page.gd",
	"techniques": "res://scripts/ui/pages/techniques_page.gd",
	"quests": "res://scripts/ui/pages/quest_page.gd",
	"world_map": "res://scripts/ui/pages/map_page.gd",
	"codex": "res://scripts/ui/pages/codex_page.gd",
	"collection": "res://scripts/ui/pages/codex_page.gd",
	"seasons": "res://scripts/ui/pages/codex_page.gd",
	"mail": "res://scripts/ui/pages/mail_page.gd",
	"shop": "res://scripts/ui/pages/shop_page.gd",
	"storage": "res://scripts/ui/pages/storage_page.gd",
	"characters": "res://scripts/ui/pages/characters_page.gd",
	"settings": "res://scripts/ui/pages/settings_page.gd",
	"dialogue": "res://scripts/ui/pages/dialogue_page.gd",
	"welcome": "res://scripts/ui/pages/welcome_page.gd",
	"revival": "res://scripts/ui/pages/revival_page.gd",
	"teleport": "res://scripts/ui/pages/teleport_page.gd",
	"emotes": "res://scripts/ui/pages/emotes_page.gd",
	"credits": "res://scripts/ui/pages/credits_page.gd",
	"notice_board": "res://scripts/ui/pages/notice_page.gd",
	"training_sect": "res://scripts/ui/pages/training_sect_page.gd",
	"your_sect": "res://scripts/ui/pages/your_sect_page.gd",
	"spirit_animals": "res://scripts/ui/pages/pets_page.gd",
	"companions": "res://scripts/ui/pages/companions_page.gd",
	"crafts": "res://scripts/ui/pages/crafts_page.gd",
	"cooking": "res://scripts/ui/pages/crafts_page.gd",
	"alchemy": "res://scripts/ui/pages/crafts_page.gd",
	"forge": "res://scripts/ui/pages/crafts_page.gd",
	"formations": "res://scripts/ui/pages/workshop_page.gd",
	"workshop": "res://scripts/ui/pages/workshop_page.gd",
	"talisman": "res://scripts/ui/pages/crafts_page.gd",
	"guild": "res://scripts/ui/pages/crafts_page.gd",
	"arrays": "res://scripts/ui/pages/crafts_page.gd",
	"charts": "res://scripts/ui/pages/crafts_page.gd",
	"vessels": "res://scripts/ui/pages/crafts_page.gd",
	"garden": "res://scripts/ui/pages/garden_page.gd",
	"core_exchange": "res://scripts/ui/pages/core_exchange_page.gd",
	"fishing": "res://scripts/ui/pages/fishing_page.gd",
	"seclusion": "res://scripts/ui/pages/cultivation_page.gd",
	"heart": "res://scripts/ui/pages/cultivation_page.gd",
	"body": "res://scripts/ui/pages/cultivation_page.gd",
	"fates": "res://scripts/ui/pages/fates_page.gd",
	"library": "res://scripts/ui/pages/shop_page.gd",
	"exchange": "res://scripts/ui/pages/exchange_page.gd",
	"auction": "res://scripts/ui/pages/auction_page.gd",
	"achievements": "res://scripts/ui/pages/codex_page.gd",
}

var backdrop: Control
var world: Node2D
var hud: Control
var hud_layer: CanvasLayer
var page_layer: CanvasLayer
var shell_layer: CanvasLayer
var fade_rect: ColorRect
var fade := 0.0
var screen := "title"
var shell: Page
var pages: Array = []
var preview_mode := false
var boot_report: Dictionary = {}
var creator: Page

# Creator access kept for the engine checks.
var draft: Dictionary:
	get: return creator.draft if creator else {}
var preview:
	get: return creator.preview if creator else null
var dye_buttons: Array:
	get: return creator.dye_buttons if creator else []

func _ready() -> void:
	get_tree().auto_accept_quit = false
	get_tree().quit_on_go_back = false
	get_tree().root.go_back_requested.connect(_on_back)
	get_tree().root.close_requested.connect(save_and_quit)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var background_layer := CanvasLayer.new()
	background_layer.layer = -10
	add_child(background_layer)
	backdrop = Backdrop.new()
	background_layer.add_child(backdrop)
	hud_layer = CanvasLayer.new()
	hud_layer.name = "MobileHUD"
	hud_layer.layer = 5
	add_child(hud_layer)
	page_layer = CanvasLayer.new()
	page_layer.layer = 20
	add_child(page_layer)
	shell_layer = CanvasLayer.new()
	shell_layer.layer = 15
	add_child(shell_layer)
	var fade_layer := CanvasLayer.new()
	fade_layer.layer = 30
	add_child(fade_layer)
	fade_rect = ColorRect.new()
	fade_rect.color = Color(0, 0, 0, 0)
	fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fade_layer.add_child(fade_rect)
	GameEvents.event.connect(_on_game_event)
	_warm_pages()
	var user_args := OS.get_cmdline_user_args()
	preview_mode = not user_args.is_empty()
	if "--test-saves" in user_args or preview_mode: Saves.use_folder("user://preview_saves/")
	for a in user_args:
		# Debug tools (S38): play from a copy of any save folder, e.g. a valley_run checkpoint.
		if str(a).begins_with("--load="):
			var src := str(a).trim_prefix("--load=")
			if not src.ends_with("/"): src += "/"
			DirAccess.make_dir_recursive_absolute("user://loaded_copy/")
			for f in DirAccess.get_files_at("user://loaded_copy/"): DirAccess.remove_absolute("user://loaded_copy/" + f)
			for f in DirAccess.get_files_at(src): DirAccess.copy_absolute(src + f, "user://loaded_copy/" + f)
			Saves.use_folder("user://loaded_copy/")
	if "--log-events" in user_args:
		GameEvents.event.connect(func(n: String, p: Dictionary): if n not in ["resource_changed", "meditation_tick"]: print("[event] ", n, " ", p))
	boot_report = Game.boot()
	Audio.music("title")
	show_title()
	if not boot_report.get("recovered", []).is_empty():
		shell.flash(Tx.t("main.a_damaged_save_was_restored"))
	_handle_preview_args(user_args)

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_game_event): GameEvents.event.disconnect(_on_game_event)

func _handle_preview_args(user_args: Array) -> void:
	if "--preview-selection" in user_args: show_selection()
	if "--preview-create" in user_args: show_creation(1)
	var room := ""
	for a in user_args:
		if str(a).begins_with("--room="): room = str(a).trim_prefix("--room=")
	if "--load-slot" in user_args:
		enter_world(1)
	elif "--preview-world" in user_args or room != "":
		if Game.character("c1") == null:
			Game.submit({"type": "create_character", "slot": 1, "name": Tx.t("main.preview"), "appearance": {"hair": "topknot", "shirt": "disciple"}})
		if room != "":
			var ch = Game.character("c1")
			ch.position = {"room": room, "portal": "", "x": 0.0, "y": 0.0, "surface": "", "facing": 1}
			for a in user_args:
				# Debug tools (S38): --at=x,y starts the preview at a point in the room.
				if str(a).begins_with("--at="):
					var xy := str(a).trim_prefix("--at=").split(",")
					ch.position.x = float(xy[0])
					ch.position.y = float(xy[1]) if xy.size() > 1 else 840.0
			if "--unlock-all" in user_args: Unlocks.debug_force_all = true
			if "--debug-sect" in user_args:
				# Debug tools (S38): a founded sect with every building at level 1, for previews.
				var b := {}
				for row in ContentDB.all("sect_buildings"): b[str(row.id)] = 1
				Game.account.sect = {"name": Tx.t("main.preview_sect"), "emblem": [0, 0], "level": 6, "prestige": 0, "buildings": b, "queue": [],
					"disciples": [], "candidates": [], "expeditions": [], "candidate_day": -1}
		enter_world(1)
	var shot := screen
	for a in user_args:
		if str(a).begins_with("--pet=") and Game.active() != null:
			# Debug tools (S38): --pet=species[:stage[:purity[:hearts]]] grants an animal and makes it active (S46 previews).
			var pa := str(a).trim_prefix("--pet=").split(":")
			Game.pets.apply_grant(Game.active().id, pa[0])
			var np: Dictionary = Game.active().pets[Game.active().pets.size() - 1]
			if pa.size() > 1: np.stage = pa[1]
			if pa.size() > 2: Game.pets.add_purity(Game.active(), np, int(pa[2]) - int(np.purity))
			if pa.size() > 3: np.bond = float(pa[3])
			Game.active().active_pet = str(np.uid)
		if str(a).begins_with("--egg=") and Game.active() != null:
			# Debug tools (S38): --egg=species puts a warming egg in the nest (S46 incubation previews).
			Game.active().eggs.append({"species": str(a).trim_prefix("--egg="), "hatch_utc": Clock.now_utc() + 7200.0})
		if str(a).begins_with("--give=") and Game.active() != null:
			# Debug tools (S38): --give=item[:count[:quality]] puts items in the bag for previews.
			var g := str(a).trim_prefix("--give=").split(":")
			if ContentDB.item(g[0]).has("draught"): Game.inventory.apply_draught(Game.active().id, g[0], int(g[1]) if g.size() > 1 else 1, "debug")
			else: Game.inventory.apply_add(Game.active().id, g[0], int(g[1]) if g.size() > 1 else 1, "debug", {"quality": g[2]} if g.size() > 2 else {})
		if str(a).begins_with("--learn=") and Game.active() != null:
			# Debug tools (S38): --learn=craft learns every recipe of one craft, for previews of its page.
			if str(a) == "--learn=inner_arts":
				for ia in ContentDB.all("inner_arts"): Game.progression.apply_learn_inner_art(Game.active().id, str(ia.id))
				Game.submit({"type": "equip_inner_art", "slot": 0, "art": "iron_shirt"})
				Game.submit({"type": "equip_inner_art", "slot": 1, "art": "sword_heart"})
			var learn: Array = []
			for r in ContentDB.all("recipes"):
				if str(r.get("craft", "")) == str(a).trim_prefix("--learn="): learn.append({"kind": "learn_recipe", "recipe": str(r.id)})
			Game.apply_effects(Game.active().id, learn, "debug")
		if str(a).begins_with("--realm=") and Game.active() != null:
			# Debug tools (S38): preview at a realm; every aptitude shows.
			var rc0 = Game.active()
			rc0.cultivator.realm_key = str(a).trim_prefix("--realm=")
			for k in rc0.cultivator.aptitude: rc0.cultivator.aptitude[k].revealed = true
			Game.combat.refresh_stats(rc0.id)
		if str(a).begins_with("--body=") and Game.active() != null:
			# Debug tools (S38): --body=level[:tier[:trials]] sets the body ladder for previews (S48).
			var bd := str(a).trim_prefix("--body=").split(":")
			var bc = Game.active()
			bc.cultivator.body_level = int(bd[0])
			if bd.size() > 1: bc.cultivator.body_tier = bd[1]
			if bd.size() > 2:
				for tr in bd[2].split(","): bc.cultivator.body_trials.append(tr)
			Game.combat.refresh_stats(bc.id)
		if str(a).begins_with("--physique=") and Game.active() != null:
			for ph in str(a).trim_prefix("--physique=").split(","): Game.progression.awaken_physique(Game.active().id, ph)
		if str(a).begins_with("--false-realm=") and Game.active() != null:
			# Debug tools (S38): preview Concealment's false realm (S48).
			if not "concealment" in Game.active().cultivator.secret_arts: Game.active().cultivator.secret_arts.append("concealment")
			Game.submit({"type": "set_false_realm", "realm": str(a).trim_prefix("--false-realm=")})
		if str(a).begins_with("--vessel=") and Game.active() != null:
			# Debug tools (S38): preview a flight vessel (G2); pair it with --fly.
			var vid := str(a).trim_prefix("--vessel=")
			Game.inventory.apply_add(Game.active().id, vid, 1, "debug")
			Game.submit({"type": "choose_vessel", "item": vid})
	for a in user_args:
		if str(a).begins_with("--open-page="):
			await get_tree().create_timer(0.8).timeout
			var spec := str(a).trim_prefix("--open-page=").split(":")
			open_page(spec[0], {"tab": spec[1]} if spec.size() > 1 else {})
		if str(a).begins_with("--talk="):
			await get_tree().create_timer(0.8).timeout
			var r := Game.submit({"type": "talk", "npc": str(a).trim_prefix("--talk=")})
			if r.get("ok", false) and r.has("dialogue"): open_page("dialogue", {"convo": r.dialogue})
		if str(a).begins_with("--shot="): shot = str(a).trim_prefix("--shot=")
		if str(a) == "--offer-fates" and Game.active() != null:
			# Debug tools (S38): a fate offer for previews of the picker (S48).
			Game.active().cultivator.fate_offer = ["thunder_tempered", "lucky_star", "scar_of_failure"]
		if str(a) == "--tribulation" and Game.active() != null:
			# Debug tools (S38): a heavenly tribulation over the preview room (S48); the capture waits for a ring.
			await get_tree().create_timer(0.8).timeout
			Game.progression._start_tribulation(Game.active(), {"to": "spirit_awakening_1", "risk": "low", "from": "cloud_stride_9", "used": [], "causes": []})
			await get_tree().create_timer(2.6).timeout
		if str(a).begins_with("--set-piece="):
			# Debug tools (S38): start a set piece's room event in the preview room (the S48 Temper trials).
			await get_tree().create_timer(0.8).timeout
			var sp := ContentDB.entry("set_pieces", str(a).trim_prefix("--set-piece="))
			if sp.has("room_event") and Game.room_rt: Game.world.start_room_event(Game.active(), sp.room_event)
			await get_tree().create_timer(2.5).timeout
	if "--ride" in user_args and is_instance_valid(world):
		# Debug tools (S38): preview riding a mount (grants a Jade Crane when there is no mountable animal).
		await get_tree().create_timer(0.3).timeout
		var rc = Game.active()
		var mount_uid := ""
		for pt in rc.pets:
			if Game.pets.mountable(pt): mount_uid = str(pt.uid)
		if mount_uid == "":
			Game.pets.apply_grant(rc.id, "jade_crane")
			mount_uid = str(rc.pets[rc.pets.size() - 1].uid)
		Game.submit({"type": "set_active_pet", "pet": mount_uid})
		Game.submit({"type": "set_pet_role", "pet": mount_uid, "role": "mount"})
	if "--fly" in user_args and is_instance_valid(world):
		# Debug tools (S38): preview flight with a filled QI pool.
		await get_tree().create_timer(0.5).timeout
		var fc = Game.active()
		fc.pools.max_qi = maxf(fc.pools.max_qi, 400.0)
		fc.pools.qi = fc.pools.max_qi
		world.player.take_off()
		world.player.fly_up = true
		await get_tree().create_timer(0.9).timeout
		world.player.fly_up = false
	for a in user_args:
		if str(a).begins_with("--herb-ripe=") and Game.room_rt:
			# Debug tools (S38): move the clock to a rare herb's next ripening, in its season (S45).
			var ho: Dictionary = Game.room_rt.object_def(str(a).trim_prefix("--herb-ripe="))
			for i in 40:
				if ho.is_empty(): break
				var hs := HerbRules.ripen_state(ho, Clock.now_utc())
				if HerbRules.in_season(ho, Clock.now_utc()) and hs.ripe: break
				Clock.debug_offset_s += 604800.0 if not HerbRules.in_season(ho, Clock.now_utc()) else float(hs.seconds) + 120.0
	if "--garden-preview" in user_args and Game.room_rt:
		# Debug tools (S38): fill this room's garden beds to show every state (S45).
		var gc = Game.active()
		var keys: Array = Game.crafting.room_beds(gc, Game.room_rt.room_id)
		var fill := [["willow_moss", 0.45, 0], ["cloudtop_orchid", 0.8, 1], ["riverreed_ginseng_100", 1.0, 0]]
		for i in mini(keys.size(), fill.size()):
			var rec: Dictionary = Game.crafting.bed_record(gc, str(keys[i]))
			rec.herb = str(fill[i][0])
			rec.progress = float(fill[i][1])
			rec.soil = int(fill[i][2])
			rec.grow_s = 8.0 * 3600.0
			rec.updated = Clock.now_utc()
		for it in [["spring_water", 2], ["spirit_soil", 1], ["verdant_dew_vial", 1], ["willow_moss_seed", 3], ["ember_pepper_seed", 2]]:
			Game.inventory.apply_add(gc.id, str(it[0]), int(it[1]), "debug")
		gc.crafting["dew"] = {"count": 2, "last": Clock.now_utc() - 3600.0}
		Game.inventory.apply_add(gc.id, "drying_rack", 1, "debug")
		Game.inventory.apply_add(gc.id, "mist_lotus", 6, "debug")
		Game.inventory.apply_add(gc.id, "riverreed_ginseng_10", 4, "debug")
		Game.inventory.apply_add(gc.id, "rice_wine", 1, "debug")
		gc.crafting["racks"] = [{"kind": "steamed", "herb": "mist_lotus", "count": 5, "done": Clock.now_utc() + 1400.0}]
	if "--tap-preview" in user_args and is_instance_valid(hud):
		# Debug tools (S38): hold the harvest ring part-way through its shrink (S45).
		await get_tree().create_timer(1.0).timeout
		hud.tapping = {"object": "preview", "t": 660.0, "ring": 1000.0, "target": 0.7, "window": 0.16}
	if "--capture" in user_args:
		await get_tree().create_timer(2.5).timeout
		for a in user_args:
			# Debug tools (S38): --hazard=phase[:fraction] holds the room's hazards in one state.
			if str(a).begins_with("--hazard="):
				var hz := str(a).trim_prefix("--hazard=").split(":")
				Game.world.debug_hazard_phase(hz[0], float(hz[1]) if hz.size() > 1 else 0.5)
				await get_tree().create_timer(0.1).timeout
		await RenderingServer.frame_post_draw
		get_tree().root.get_texture().get_image().save_png("res://../" + (shot if shot != "" else screen) + "-preview.png")
		get_tree().quit()

# ------------------------------------------------------------------ shell screens
func _set_shell(p: Page) -> void:
	if is_instance_valid(shell):
		shell_layer.remove_child(shell)
		shell.queue_free()
	shell = p
	if p != null:
		shell_layer.add_child(p)

func show_title() -> void:
	screen = "title"
	creator = null
	var p := ShellScreens.TitleScreen.new()
	p.chosen.connect(_on_title)
	_set_shell(p)
	p.open({})

func _on_title(action: String) -> void:
	match action:
		"start":
			if Game.characters.is_empty(): show_creation(1)
			else: show_selection()
		"settings": open_page("settings", {})
		"credits": open_page("credits", {})
		"quit": save_and_quit()

func show_selection() -> void:
	screen = "selection"
	creator = null
	var p := ShellScreens.SelectionScreen.new()
	p.enter.connect(enter_world)
	p.create.connect(show_creation)
	p.back.connect(show_title)
	_set_shell(p)
	p.open({})

func show_creation(slot: int) -> void:
	screen = "creation"
	var p := ShellScreens.CreatorScreen.new()
	p.created.connect(func(s: int): enter_world(s))
	p.cancelled.connect(_on_creator_cancel)
	_set_shell(p)
	p.open({"slot": maxi(1, slot)})
	creator = p

func _on_creator_cancel() -> void:
	if Game.characters.is_empty(): show_title()
	else: show_selection()

func set_hair_dye(i: int) -> void:
	if creator: creator.set_hair_dye(i)

func cycle(category: String, direction: int) -> void:
	if creator: creator.cycle(category, direction)

# ------------------------------------------------------------------ world
func enter_world(slot: int) -> void:
	var r := Game.submit({"type": "enter_character", "slot": slot})
	if not r.get("ok", false):
		if shell: shell.flash(Tx.t("main.could_not_enter") % str(r.get("reason", "")))
		return
	var r2 := Game.submit({"type": "enter_world"})
	if not r2.get("ok", false):
		if shell: shell.flash(Tx.t("main.the_world_could_not_load") % str(r2.get("reason", "")))
		return
	_set_shell(null)
	creator = null
	screen = "world"
	_mount_world()
	fade = 1.0
	var welcome: Dictionary = r.get("welcome", {})
	if not welcome.get("gains", {}).is_empty(): open_page("welcome", welcome)

func _mount_world() -> void:
	_unmount_world()
	Game.in_world = true
	world = World.new()
	world.room_mode = true
	add_child(world)
	backdrop.world = world
	hud = Hud.new()
	hud.player = world.player
	hud.world = world
	hud.skill_page = int(Game.active().skill_page)
	hud.open_page.connect(open_page)
	hud.dialogue_requested.connect(func(convo: Dictionary): open_page("dialogue", {"convo": convo}))
	hud.fishing_requested.connect(func(obj: String): open_page("fishing", {"object": obj}))
	hud_layer.add_child(hud)

func _unmount_world() -> void:
	close_all_pages()
	if is_instance_valid(hud):
		hud_layer.remove_child(hud)
		hud.queue_free()
	hud = null
	if is_instance_valid(world):
		remove_child(world)
		world.queue_free()
	world = null
	backdrop.world = null
	Game.in_world = false

func return_to_selection() -> void:
	if screen == "world":
		Game.submit({"type": "app_paused"})
		Game.save_all()
		_unmount_world()
	show_selection()

func save_and_quit() -> void:
	if screen == "world":
		Game.submit({"type": "app_paused"})
	Game.save_all()
	get_tree().quit()

# ------------------------------------------------------------------ pages
func open_page(id: String, a: Dictionary) -> void:
	if id == "_harvest":
		# S45: "Pick it" at a rare herb hands back to the HUD's hold-and-tap harvest.
		if is_instance_valid(hud): hud.begin_harvest(str(a.get("object", "")))
		return
	if id == "_exit":
		return_to_selection()
		return
	if id == "_import":
		# S40: replace the saves with an export (the current files are saved first and kept as .bak).
		Game.save_all()
		if screen == "world": _unmount_world()
		close_all_pages()
		var err := Saves.import_bundle(str(a.get("path", "")))
		Game.boot()
		show_selection()
		if err != OK: push_warning("import failed: %s" % err)
		return
	if id == "_switch":
		var r := Game.submit({"type": "switch_character", "slot": int(a.get("slot", 1))})
		if not r.get("ok", false):
			if top_page(): top_page().flash(str(r.get("text", Tx.t("main.cannot_switch_here"))))
			return
		Game.submit({"type": "enter_world"})
		_mount_world()
		fade = 1.0
		if not r.get("welcome", {}).get("gains", {}).is_empty(): open_page("welcome", r.welcome)
		return
	var path := str(PAGES.get(id, ""))
	if path == "" or not ResourceLoader.exists(path):
		if is_instance_valid(hud): hud.add_log(Tx.t("main.coming_in_a_later_update"), UiKit.MIST)
		return
	# Opening the same page again just brings it to the front with new args.
	for p in pages:
		if p.page_id == id:
			p.open(a)
			return
	var page: Page = _page_script(path).new()
	page.page_id = id
	page.closed.connect(close_page)
	page.navigate.connect(func(to: String, b: Dictionary): open_page(to, b))
	page_layer.add_child(page)
	page.open(a)
	pages.append(page)
	if is_instance_valid(hud): hud.set_blocked(true)
	if Game.active():
		Game.submit({"type": "report_page_opened", "page": id})

## Page scripts compile in a background thread from the title screen on, so the first time a page opens it does
## not stall a frame compiling itself (S40 performance: a page opens within 0.15 s).
var _page_scripts: Dictionary = {}

func _warm_pages() -> void:
	for path in PAGES.values():
		if ResourceLoader.exists(str(path)): ResourceLoader.load_threaded_request(str(path))

func _page_script(path: String) -> Script:
	if _page_scripts.has(path): return _page_scripts[path]
	var scr: Script = null
	var status := ResourceLoader.load_threaded_get_status(path)
	if status == ResourceLoader.THREAD_LOAD_LOADED or status == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		scr = ResourceLoader.load_threaded_get(path) as Script
	if scr == null: scr = load(path) as Script
	_page_scripts[path] = scr
	return scr

func close_page(page: Page) -> void:
	pages.erase(page)
	if is_instance_valid(page):
		page_layer.remove_child(page)
		page.queue_free()
	if pages.is_empty() and is_instance_valid(hud): hud.set_blocked(false)

func close_all_pages() -> void:
	for p in pages.duplicate(): close_page(p)

func top_page() -> Page:
	return pages.back() if not pages.is_empty() else null

# ------------------------------------------------------------------ events and lifecycle
func _on_game_event(name: String, p: Dictionary) -> void:
	match name:
		"room_left": fade = 1.0
		"fell_out": if str(p.get("actor", "")) == Game.active_id: fade = maxf(fade, 0.85)   # S43: a short fade on recovery
		"room_entered":
			fade = maxf(fade, 0.9)
			close_all_pages()
		"player_gravely_wounded":
			if screen == "world": open_page("revival", p)
		"shop_opened":
			open_page("shop", p)

func _process(delta: float) -> void:
	if fade > 0.0:
		fade = maxf(0.0, fade - delta / 0.35)
		fade_rect.color = Color(0, 0, 0, fade)

func _on_back() -> void:
	var top := top_page()
	if top:
		top.close()
		return
	match screen:
		"world":
			if Game.is_revealed("hud:menu"): open_page("menu", {})
		"creation": show_selection() if not Game.characters.is_empty() else show_title()
		"selection": show_title()

func _unhandled_key_input(event: InputEvent) -> void:
	if event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		_on_back()

func _notification(what: int) -> void:
	if not is_inside_tree() or not Game.booted: return
	match what:
		NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT:
			if screen == "world": Game.submit({"type": "app_paused"})
			Game.save_all()
		NOTIFICATION_APPLICATION_RESUMED:
			if screen == "world":
				var r := Game.submit({"type": "app_resumed"})
				if not r.get("welcome", {}).get("gains", {}).is_empty(): open_page("welcome", r.welcome)
		NOTIFICATION_WM_CLOSE_REQUEST:
			save_and_quit()
