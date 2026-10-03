extends Control
## Game shell (S35): boot → title → character selection → creator → world.
## Hosts the backdrop, the room world, the HUD and a stack of pages. It only
## routes intents and signals; every rule lives behind `Game.submit`.
## The pages it opens are in the page registry (scripts/shell/page_registry.gd); the preview and debug flags of the
## command line are in scripts/dev/debug_args.gd, loaded only when the game starts with arguments
## (docs/architecture/shell.md).

const World = preload("res://scripts/world.gd")   # side view
const Hud = preload("res://scripts/hud.gd")
const Backdrop = preload("res://scripts/backdrop.gd")
const TopdownWorldScript = preload("res://scripts/topdown/topdown_world.gd")
const PageRegistry = preload("res://scripts/shell/page_registry.gd")
const DEBUG_ARGS := "res://scripts/dev/debug_args.gd"
## The top-down prototype (redesign Phase 1) from the title screen plays on its own saves, never the player's.
const PROTO_SAVES := "user://topdown_proto_saves/"
## The top-down game (redesign Phase 4) from the title screen plays on saves of its own.
const TOPDOWN_SAVES := "user://topdown_saves/"

## The page table: page id -> the script that draws it. Its home is the registry; the tests and tools read it here.
const PAGES := PageRegistry.PAGES

var backdrop: Control
var world: Node2D
var hud: Control
var moments: MomentView
var scenes: SceneDirector   ## decision 39: the staged scenes, played in the rooms on the height grid
var coach: TutorialCoach    ## decision 43: the unlock tutorials' guides and tours (docs/redesign/tutorials.md)
var hud_layer: CanvasLayer
var page_layer: CanvasLayer
var shell_layer: CanvasLayer
var fade_rect: ColorRect
var fade := 0.0
var screen := "title"
var shell: Page
var pages: Array = []
var preview_mode := false       ## started with arguments: the preview saves, and the flags (debug_args) read
var creator: Page
var topdown := false            ## the world mounted is the top-down prototype room (redesign Phase 1)
var proto_isolated := false     ## opened from the title screen on PROTO_SAVES; leaving it restores the player's saves
var _proto_force_was := false
var _saves_before := "user://"  ## the saves set aside while the top-down game or the prototype runs on its own
var _debug_args: RefCounted = null   ## the flags' run (it waits on timers, so the shell keeps it)

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
	_add_backdrop()
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
	# Decision 43: the tutorial coach over the HUD and the pages, under the fade.
	var coach_layer := CanvasLayer.new()
	coach_layer.layer = 25
	add_child(coach_layer)
	coach = TutorialCoach.new()
	coach.main = self
	coach_layer.add_child(coach)
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
	# The preview and debug flags: only with arguments after "--", which a player's game never has.
	var user_args := OS.get_cmdline_user_args()
	preview_mode = not user_args.is_empty()
	if preview_mode:
		_debug_args = load(DEBUG_ARGS).new(self, user_args)
		_debug_args.before_boot()
	var boot_report := Game.boot()
	# The Max Test APK (custom feature "max_test"; --max-character in the editor): every way open, every system
	# unlocked, and on first launch a ready-made character at the top of this build.
	if OS.has_feature("max_test") or "--max-character" in user_args:
		Unlocks.debug_force_all = true
		Game.world.debug_open_ways = true
		if Game.characters.is_empty(): Game.accounts.create_max_character(1, Tx.t("main.max_tester"))
	Audio.music("title")
	show_title()
	if not boot_report.get("recovered", []).is_empty():
		shell.flash(Tx.t("main.a_damaged_save_was_restored"))
	if _debug_args: _debug_args.run()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_game_event): GameEvents.event.disconnect(_on_game_event)

# ------------------------------------------------------------------ shell screens
## A page or shell screen put away: hidden now and freed at the frame's end. Taken out of the tree at once while the
## tap that closed it was still being handled, the viewport asked the removed page whether it could process that tap
## ("Condition !is_inside_tree()" in the log at every close; the prototype's QA).
static func _put_away(p: Control) -> void:
	p.hide()
	p.queue_free()

func _set_shell(p: Page) -> void:
	if is_instance_valid(shell): _put_away(shell)
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
		"topdown_proto": enter_topdown_tutorial(true)
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
	_add_world_view()
	hud = Hud.new()
	hud.player = world.player
	hud.world = world
	hud.skill_page = int(Game.active().skill_page)
	hud.open_page.connect(open_page)
	hud.dialogue_requested.connect(func(convo: Dictionary): open_page("dialogue", {"convo": convo}))
	hud.fishing_requested.connect(func(obj: String): open_page("fishing", {"object": obj}))
	hud.coach = coach
	hud_layer.add_child(hud)
	if topdown:   # no moments in the prototype room (no side-view rig to play them on); the fan starts folded
		hud.fan_open = false
		hud.fan_rest_open = false
		return
	_warm_techniques()
	# P6 moments live only while the world is mounted: events raised while a save loads or offline gains settle never play.
	moments = MomentView.new()
	moments.world = world
	moments.hud = hud
	hud.moments = moments
	add_child(moments)
	scenes = SceneDirector.new()
	scenes.headless = false
	scenes.world = world
	scenes.hud = hud
	scenes.moments = moments
	hud.scenes = scenes
	add_child(scenes)

## The view of the room the character stands in: the prototype square, a room of the world on the height grid (the
## top-down view, redesign Phase 4), or the side view.
func _add_world_view() -> void:
	if topdown:
		world = TopdownWorldScript.new()
	elif Game.room_rt != null and Game.room_rt.topdown != null:
		world = TopdownWorldScript.new()
		world.live = true
	else:
		world = _side_view()   # side view
	add_child(world)
	_backdrop_follows_world()   # side view

func _unmount_world() -> void:
	close_all_pages()
	if is_instance_valid(scenes):
		remove_child(scenes)
		scenes.queue_free()
	scenes = null
	if is_instance_valid(moments):
		remove_child(moments)
		moments.queue_free()
	moments = null
	if is_instance_valid(hud):
		hud_layer.remove_child(hud)
		hud.queue_free()
	hud = null
	if is_instance_valid(world):
		remove_child(world)
		world.queue_free()
	world = null
	backdrop.world = null   # side view
	Game.in_world = false

## Redesign Phase 4: the game in the top-down world, from the title screen's hidden entry (five taps on the version) or
## --topdown-tutorial. It plays on saves of its own (the player's are saved, set aside and restored on leaving it):
## its character is a real one, made new for the top-down world the first time (the Prologue from the Fisher's Hut),
## then continued where it was saved.
func enter_topdown_tutorial(isolated := true) -> void:
	_proto_force_was = Unlocks.debug_force_all
	if isolated:
		Game.save_all()
		_saves_before = Saves.repo.root
		Saves.use_folder(TOPDOWN_SAVES)
		Game.boot()
		proto_isolated = true
	if Game.character("c1") == null:
		Game.submit({"type": "create_character", "slot": 1, "name": Tx.t("sim.account.disciple"), "appearance": {"hair": "topknot"}, "view": "topdown"})
	enter_world(1)

## Redesign Phase 1: the top-down prototype room under the real HUD, on a stand-in character (--topdown-proto: the
## preview saves; `isolated`: saves of its own, the player's untouched).
func enter_topdown_proto(isolated: bool) -> void:
	if isolated:
		Game.save_all()
		_saves_before = Saves.repo.root
		Saves.use_folder(PROTO_SAVES)
		Game.boot()
		proto_isolated = true
	_proto_force_was = Unlocks.debug_force_all
	Unlocks.debug_force_all = true
	if Game.character("c1") == null:
		Game.submit({"type": "create_character", "slot": 1, "name": Tx.t("main.preview"), "appearance": {"hair": "topknot", "shirt": "disciple"}, "skip_prologue": true})
	topdown = true
	enter_world(1)

func _leave_topdown_proto() -> void:
	topdown = false
	Unlocks.debug_force_all = _proto_force_was
	if proto_isolated:
		proto_isolated = false
		Saves.use_folder(_saves_before)
		Game.boot()

func return_to_selection() -> void:
	if topdown:
		if screen == "world": _unmount_world()
		_leave_topdown_proto()
		show_title()
		return
	if proto_isolated:   # the top-down game from the title: saved on its own saves, then back to the player's
		if screen == "world":
			Game.submit({"type": "app_paused"})
			Game.save_all()
			_unmount_world()
		_leave_topdown_proto()
		show_title()
		return
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
## A page by its id (scripts/shell/page_registry.gd), or one of the shell's own actions (_shell_action).
func open_page(id: String, a: Dictionary) -> void:
	if _shell_action(id, a): return
	var path := PageRegistry.script_of(id)
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

## The ids a page or a dialogue choice navigates to that are no page: the shell answers them itself. False for any
## other id.
func _shell_action(id: String, a: Dictionary) -> bool:
	match id:
		"_harvest":
			# S45: "Pick it" at a rare herb hands back to the HUD's hold-and-tap harvest.
			if is_instance_valid(hud): hud.begin_harvest(str(a.get("object", "")))
		"_exit":
			# The Menu's Save & Exit.
			return_to_selection()
		"_tour":
			# Decision 43: a page's "?" plays its tour again.
			if is_instance_valid(coach): coach.replay_tour(str(a.get("page", "")), str(a.get("tab", "")))
		"_import":
			# Settings' restore from an export.
			_import_saves(str(a.get("path", "")))
		"_switch":
			# The Characters page and the Roll-Call.
			_switch_character(int(a.get("slot", 1)))
		_:
			return false
	return true

## S40: replace the saves with an export (the current files are saved first and kept as .bak).
func _import_saves(path: String) -> void:
	Game.save_all()
	if screen == "world": _unmount_world()
	close_all_pages()
	var err := Saves.import_bundle(path)
	Game.boot()
	show_selection()
	if err != OK: push_warning("import failed: %s" % err)

## Another character of the account, played from where it stands.
func _switch_character(slot: int) -> void:
	var r := Game.submit({"type": "switch_character", "slot": slot})
	if not r.get("ok", false):
		if top_page(): top_page().flash(str(r.get("text", Tx.t("main.cannot_switch_here"))))
		return
	Game.submit({"type": "enter_world"})
	_mount_world()
	fade = 1.0
	if not r.get("welcome", {}).get("gains", {}).is_empty(): open_page("welcome", r.welcome)

## The technique trees' index and the Techniques page's tree for the tab it would open on, built as the world mounts and
## as a room is entered (under their fades), not on the page's first opening or a fight's first cast (perf_tests: every
## page opens in under 0.15 s). Both are kept once built, so this is nearly free after the first time; the page's tree
## waits for the page's script to be in from its loading thread (never waiting on it here).
func _warm_techniques() -> void:
	TechniqueTreeRules.home("")
	var tp := PageRegistry.script_of("techniques")
	if _page_scripts.has(tp) or ResourceLoader.load_threaded_get_status(tp) == ResourceLoader.THREAD_LOAD_LOADED:
		_page_script(tp).warm(Game.active())

## Page scripts compile in a background thread from the title screen on, so the first time a page opens it does
## not stall a frame compiling itself (S40 performance: a page opens within 0.15 s). One at a time (PageWarmer, ticked
## in _process), so a room's people never wait behind the whole set.
var _page_scripts: Dictionary = {}
var _page_warmer: PageWarmer = null

func _warm_pages() -> void:
	_page_warmer = PageWarmer.new(PageRegistry.scripts())
	_page_warmer.tick()

## True once every page script has been asked for and is in.
## Test hook: perf_tests and the tools/dev walks wait on it.
func pages_warm() -> bool:
	return _page_warmer == null

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
	if is_instance_valid(page): _put_away(page)
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
			if screen == "world" and Game.room_rt != null: _swap_world_view()   # side view
			if screen == "world" and not topdown: _warm_techniques()
		"player_gravely_wounded":
			if screen == "world": open_page("revival", p)
		"shop_opened":
			open_page("shop", p)

func _process(delta: float) -> void:
	if _page_warmer != null and not _page_warmer.tick(): _page_warmer = null
	if fade > 0.0:
		fade = maxf(0.0, fade - delta / 0.35)
		fade_rect.color = Color(0, 0, 0, fade)

func _on_back() -> void:
	# Decision 45: Back while a tutorial tour dims the screen skips the tour, not the page under it.
	if is_instance_valid(coach) and coach.back(): return
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

# ------------------------------------------------------------------ side view (retiring)
## Decision 45: the side view goes once every room is top-down (docs/architecture/audit_45.md §2.4). What the shell does
## for it is here, and its calls elsewhere in this file are marked "side view": the World preload, _add_world_view's
## last branch and its backdrop line, _unmount_world's backdrop line and _on_game_event's swap. The backdrop is also
## the title screens' sky, so it stays until they have one of their own.

## The river backdrop behind everything (the title screens', and the side view's sky, scrolled with its camera).
func _add_backdrop() -> void:
	var background_layer := CanvasLayer.new()
	background_layer.layer = -10
	add_child(background_layer)
	backdrop = Backdrop.new()
	background_layer.add_child(backdrop)

## The side view of the character's room.
func _side_view() -> Node2D:
	var w := World.new()
	w.room_mode = true
	return w

## The backdrop follows the side view and is hidden under the top-down one, which draws its own ground.
func _backdrop_follows_world() -> void:
	var side: bool = world is World
	backdrop.world = world if side else null
	backdrop.visible = side

## A room entered in the other view (a top-down character walking from a room on the grid into one still side-view, or
## back): the world view is swapped under the same HUD, pages and moments.
func _swap_world_view() -> void:
	if not is_instance_valid(world) or topdown: return
	if (world is World) == (Game.room_rt.topdown == null): return
	remove_child(world)
	world.queue_free()
	_add_world_view()
	if is_instance_valid(hud):
		hud.player = world.player
		hud.world = world
	if is_instance_valid(moments): moments.world = world
	if is_instance_valid(scenes): scenes.world = world
