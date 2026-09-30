extends "res://tools/dev/capture/capture_steps.gd"
## The capture tool's scripted steps: the ones that are more than a row can say (a stage a set starts from, a loop that
## waits on the game, a fight played to a beat, a room staged and held still). Each is ported from the one-off script
## that first took its pictures (see the set's doc line in shots.gd), call for call, so the pictures are framed as they
## were. A new picture should not need one: a row of plain steps is the rule.

const HEIGHT_BODIES := [Vector2(11.5, 13.6), Vector2(9.5, 8.6), Vector2(6.5, 5.6), Vector2(5.5, 11.2), Vector2(16.0, 12.6),
	Vector2(22.9, 16.4), Vector2(4.5, 1.8)]   ## where the bodies stand in td_review_heights (cells): each level once
const MONSTER_SPOT := Vector2(51, 17)       ## the Reed Shallows' flats, where the foes are lined up

var eel: EnemyState
var land := Vector2.ZERO
var heard := {"glance": 0}

# ------------------------------------------------------------------------------------------------------ stages
## The prototype room (Riverside Square) as the redesign's first phases played it.
func s_proto() -> void:
	main.enter_topdown_proto(false)
	_bind()
	await frames(40)

## A new top-down character's game (the title's hidden entry), once the pages' scripts have compiled on their loading
## threads from the title screen on (main._warm_pages), where a player spends those seconds: a villager's outfit sheets
## queue behind them, so the capture waits for them as the title would.
func s_new_game() -> void:
	for i in 3600:
		if main.PAGES.values().all(func(q): return ResourceLoader.load_threaded_get_status(str(q)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS): break
		await get_tree().process_frame
	main.enter_topdown_tutorial(false)

func s_bind() -> void:
	_bind()

## This node runs while the game is held still; the game does not.
func s_pausable() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	main.process_mode = Node.PROCESS_MODE_PAUSABLE

func s_paused(on: bool) -> void:
	get_tree().paused = on

## The character past the Weapon Hall, at Bone Forging 7 (its Qi pool open, so the Qi cue shows), with a jian and four
## arts slotted (one cooling in a fight, one short of Qi, one ready, a spear art the jian cannot use); Aunt Ping has two
## quests to give.
const WEAPON_HALL_ARTS := ["flowing_palm", "cloudpiercing_stroke", "still_water_focus", "jade_thrust"]
const WEAPON_HALL_UNLOCKS := ["move", "bag", "navigation", "jump", "shop", "quick_use", "attack", "loot", "menu", "cultivate",
	"cultivation", "technique_slots_2", "technique_slots_4", "world_menu", "mail", "guard", "qi_pool", "character_menu", "equipment",
	"town_hub"]
func s_weapon_hall() -> void:
	var c = _c()
	for u in WEAPON_HALL_UNLOCKS: Unlocks.force_unlock(c.id, u)
	for q in ["morning_tide", "a_quiet_river", "the_runaway_kite"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	c.cultivator.realm_key = "bone_forging_7"
	for a in WEAPON_HALL_ARTS:
		if not c.cultivator.techniques_known.has(a): c.cultivator.techniques_known.append(a)
	c.cultivator.technique_slots = WEAPON_HALL_ARTS + [null, null, null, null]
	for wid in ["training_jian", "iron_jian"]:
		if c.inventory.equipped.get("weapon") != null: break
		Game.inventory.apply_add(c.id, wid, 1, "capture")
		Game.submit({"type": "equip", "index": c.inventory.first_index(wid)})
	Game.inventory.apply_add(c.id, "herbal_tea", 3, "capture")
	c.inventory.quick_use = "herbal_tea"
	for it in [["willow_moss", 6], ["riverfish_soup", 2], ["copper_ore", 4], ["reed_fiber", 5]]:
		if not ContentDB.item(str(it[0])).is_empty(): Game.inventory.apply_add(c.id, str(it[0]), int(it[1]), "capture")
	Game.combat.refresh_stats(c.id)
	c.pools.qi = c.pools.max_qi
	Game.quest._refresh_offers()
	c.quests.offered["aunt_pings_broth"] = true
	GameEvents.flush()
	print("  capture: %s, weapon %s, Qi %d, slots %d" % [c.cultivator.realm_key, str(c.inventory.equipped.get("weapon", {}).get("id", "none") if c.inventory.equipped.get("weapon") != null else "none"),
		int(c.pools.max_qi), ProgressionRules.technique_slot_count(c)])

func s_companion(id: String) -> void:
	Game.companions.apply_add(Game.active_id, id)

func s_learn_method(id: String) -> void:
	Game.progression.apply_learn_method(_c().id, id)
	_c().cultivator.method_id = id

## A top-down character of its own for the places' review, in Lotus Ferry's village with the story's scenes seen, the
## systems opened by the debug unlock, a letter, notices not read and things in the storehouse.
const PLACES_OPEN := ["mail", "notice_board", "storage", "alchemy", "auto_refine", "herb_garden", "teleport_stones", "cooking",
	"world_menu", "qi_springs", "seclusion", "smithing"]
const PLACES_STOCK := [{"id": "herbal_tea", "count": 6}, {"id": "riverfish_soup", "count": 2}, {"id": "spirit_stone_shard", "count": 9},
	{"id": "boar_bone_broth", "count": 1}, {"id": "willow_moss", "count": 12}, {"id": "herb_sickle", "count": 1}, {"id": "old_pickaxe", "count": 1},
	{"id": "bamboo_rod", "count": 1}, {"id": "clay_pot", "count": 1}, {"id": "reed_net", "count": 1}, {"id": "healing_pill", "count": 3},
	{"id": "qi_pill", "count": 2}, {"id": "herbal_tea", "count": 1}, {"id": "riverfish_soup", "count": 1}, {"id": "willow_moss", "count": 1},
	{"id": "spirit_stone_shard", "count": 1}, {"id": "healing_pill", "count": 1}, {"id": "qi_pill", "count": 1}]
func s_places_stage() -> void:
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
	for s in PLACES_OPEN: Unlocks.force_unlock(c.id, s)
	GameEvents.flush()
	await frames(30)
	main.hud.toasts.clear()   # the unlocks' notices would stand over the square's places
	main.hud.log_lines.clear()
	Game.mail.apply_send(c.id, "places_review", [], {})
	Game.account.storage["items"] = PLACES_STOCK.duplicate(true)

## A copy of one of topdown_tutorial's checkpoints (run it with `-- --keep="The Weapon Hall,The Weapon Hall (Cloud)"`)
## booted as the game, the character entered on the grid.
func s_checkpoint(cp: String, saves: String) -> void:
	var src := "user://tutorial_cp/%s/" % cp
	DirAccess.make_dir_recursive_absolute(saves)
	for f in DirAccess.get_files_at(saves): DirAccess.remove_absolute(saves + f)
	for f in DirAccess.get_files_at(src): DirAccess.copy_absolute(src + f, saves + f)
	main.close_all_pages()
	Saves.use_folder(saves)
	Game.boot()
	Game.autosave_enabled = false
	for i in 3600:
		if main.PAGES.values().all(func(q): return ResourceLoader.load_threaded_get_status(str(q)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS): break
		await get_tree().process_frame
	main.enter_topdown_tutorial(false)
	await frames(30)
	var c = _c()
	print("  capture %s: %s in %s, strange_tracks %s" % [cp, str(c.id) if c else "?", Game.room_rt.room_id if Game.room_rt else "?", str(c.quests.is_active("strange_tracks"))])

# ------------------------------------------------------------------------------------------------------ the review room
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

## The height-levels review room (td_review_heights: levels -1/2 to 4, a house built on the grid, a courtyard wall,
## stairs, a pier) drawn by the game's view with no character in it, a body standing on each level. `mode`:
##   "panels" the room whole in colour and by value alone, x2, side by side (the readability test, art bible §5);
##   "x2"     the room whole, x2 (the light's review);
##   "view"   the phone's view of it (the camera on its middle), x2 (the terrain's review).
func s_heights(name, mode: String) -> void:
	var was: String = Game.active_id
	Game.active_id = ""   # the view alone: no character enters the review room
	if mode == "view": main.hud.visible = false
	var v := TopdownWorld.new()
	v.room_id = "td_review_heights"
	add_child(v)
	await frames(2)
	if mode == "view":
		w = v
		v.set_process(false)
		v.camera.position = v.room.art_size() * 0.5 - Vector2(0, 24)
	else:
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
	if mode == "view":
		for f in 30: await frames(1)
		(await world_shot()).save_png(_png(name))
		v.queue_free()
		await frames(2)
		Game.active_id = was
		return
	for f in 3: await frames(1)
	await RenderingServer.frame_post_draw
	var img: Image = v.viewport.get_texture().get_image()
	if mode == "x2":
		img.resize(img.get_width() * 2, img.get_height() * 2, Image.INTERPOLATE_NEAREST)
		img.save_png(_png(name))
		v.queue_free()
		Game.active_id = was
		return
	var grey := img.duplicate()
	for y in grey.get_height():
		for x in grey.get_width():
			var c: Color = grey.get_pixel(x, y)
			var l: float = c.r * 0.299 + c.g * 0.587 + c.b * 0.114
			grey.set_pixel(x, y, Color(l, l, l, c.a))
	await panels(_png(name), [["In colour", img], ["By value alone", grey]], 2, 2)
	v.queue_free()
	Game.active_id = was
	await frames(1)

## A room's view alone (no character enters it) at its spawn, the world x2.
func s_view_alone(name, room: String) -> void:
	var was: String = Game.active_id
	Game.active_id = ""
	main.hud.visible = false
	var v := TopdownWorld.new()
	v.room_id = room
	add_child(v)
	await frames(2)
	w = v
	for f in 30: await frames(1)
	(await world_shot()).save_png(_png(name))
	v.queue_free()
	await frames(2)
	Game.active_id = was

## Every room on the grid whole at 1 art px, into `dir` (to judge the foliage's framing room by room).
func s_rooms_whole(dir: String) -> void:
	for f in DirAccess.get_files_at("res://data/topdown/"):
		var rid := f.get_basename()
		if not f.ends_with(".json") or not TopdownRoom.has_layout(rid): continue
		var lay = JSON.parse_string(FileAccess.get_file_as_string("res://data/topdown/" + f))
		if not (lay is Dictionary and lay.has("levels")): continue
		Game.world.load_room(_c(), rid, "", TopdownRoom.cell_point(lay.get("spawn", [1, 1])))
		GameEvents.flush()
		await frames(6)
		w = main.world
		await whole_room(_png(dir + rid))

## The sand and snow sampler: every transition on a room of its own (`paint`, 40 x 22 cells, the phone's view), drawn by
## the game's own room view: whole at x2, and each quarter x4 (into closeups/).
func s_sampler(name, paint: Array, closeups: String) -> void:
	var levels: Array = []
	for y in paint.size():
		var line := ""
		for x in str(paint[y]).length():
			var ch := str(paint[y])[x]
			line += "~" if ch == "~" else ("2" if y < 4 and x >= 21 else "0")
		levels.append(line)
	var d := {"id": "td_sand_snow_sampler", "name": "Sand and snow", "levels": levels, "paint": paint.duplicate(), "stairs": [],
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
	(await world_shot()).save_png(_png(name))
	var k := 0
	for q in [Vector2(10, 5), Vector2(10, 16), Vector2(30, 3), Vector2(30, 14)]:
		k += 1
		await s_closeup(closeups + "_%d" % k, q)
	v.queue_free()
	await frames(2)
	Game.active_id = was
	main.world.visible = true
	main.hud.visible = true

# ------------------------------------------------------------------------------------------------------ phase 3
## The water's four frames round the pond and the pier, 250 ms apart, with the square cleared so nothing moves.
func s_water_frames(name = "*") -> void:
	await s_arena(["spawn"], [])
	var water: Array = []
	for f in 4:
		await get_tree().create_timer(0.25).timeout
		await RenderingServer.frame_post_draw
		var img: Image = w.viewport.get_texture().get_image()
		water.append(["frame %d" % f, img.get_region(Rect2i(100, 170, 300, 170))])
	await panels(_png(name), water, 2, 2)

# ------------------------------------------------------------------------------------------------------ decision 42
## The weave: basic attack, technique, basic attack, each pressed early and cutting the last one's recovery once its
## blow has landed, as labelled frames round the body (every fifth frame, 1/12 s apart).
func s_weave(name = "*") -> void:
	var c = _c()
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
	await panels(_png(name), tiles, 4)

## A chain of its own for the character, from the first step.
func s_fresh_chain() -> void:
	Game.combat.actors.erase(_c().id)

## Auto-path's steering (TopdownRoute, as the Autopilot drives it) in the room on view from where the body stands: the
## whole room with a tour drawn on it (to every way out and four of its people and things in turn, as topdown_suite's
## route test runs it): in gold the route the new steering runs, in red the old steering's (cell centre to cell centre
## by find_path); and frames of the body running the road to the way `goal_portal` in the game.
func s_route(name, frames_name, goal_portal: String) -> void:
	var start: Vector2 = m.pos
	var trails := [_tour_trail(w.room, start, false), _tour_trail(w.room, start, true)]
	var way: Dictionary = Game.room_rt.portal_def(goal_portal)
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
	await whole_room(_png(name))
	await panels(_png(frames_name), tiles, 4)

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

## The guard's wall of qi, then a parry caught in its window: the guard raised, the first foe's blow struck into it.
func s_parry() -> void:
	var striker: EnemyState = Game.room_rt.enemies.values()[0]
	striker.aim = Vector2.LEFT
	Game.submit({"type": "guard_end"})
	Game.submit({"type": "guard_start"})
	Game.combat.enemy_strike(striker, striker.def.attacks[0])
	GameEvents.flush()

# ------------------------------------------------------------------------------------------------------ decision 43, the living world
## Critters set where a close-up looks, so it shows its kind: "sparrows" pecking (and "sparrows_flee" as the player
## walks up), "water" (fish, a dragonfly, a ring), "frogs" at the edge, "butterflies".
func s_critters(kind: String) -> void:
	var life: TopdownLife = w.life
	var feet: Vector2 = p.motor.pos
	match kind:
		"sparrows", "sparrows_flee":
			for i in 4:
				var cr: TopdownLife.Critter = life._critter("sparrow", feet + Vector2(20 + i * 26, -110 - (i % 2) * 18))
				cr.state = "ground"
				cr.alpha = 1.0
				cr.face = -1 if i % 2 else 1
			await frames(20)
			if kind == "sparrows_flee":
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

## What the atmosphere shows (for the light's review log).
func s_log_light() -> void:
	var atmo = main.world.get("atmosphere")
	if atmo == null: return
	var n := {}
	for q in atmo.particles: n[q.kind] = int(n.get(q.kind, 0)) + 1
	print("  light: %s at %.2f, %s, %d lights, air %s" % [_name("*"), TopdownLight.debug_hour, str(atmo.now.hour), atmo.lights.size(), str(n)])

# ------------------------------------------------------------------------------------------------------ decision 44, work and places
## A worker in its loop, the player standing four and a half tiles off (out of its notice) and the shot on the worker
## once it plays `action` (at its contact frame, or its second frame), or after half a minute whatever it does. A worker
## the story does not show yet is left out, and said so.
func s_worker(name, room: String, who: String, action: String) -> void:
	var life: Dictionary = TopdownLife.room_life(room)
	var home := Vector2.ZERO
	for e in life.get("extras", []):
		if str(e.id) == who: home = TopdownRoom.cell_point(e.spots[0])
	if home == Vector2.ZERO:
		var lay := TopdownRoom.load_room(room)
		home = TopdownRoom.cell_point(lay.def.place.get(who, [0, 0]))
	var far := home + Vector2(0, 4.5 * TopdownRoom.TILE)
	Game.world.load_room(_c(), room, "", far)
	GameEvents.flush()
	await frames(10)
	_bind()
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
		print("  capture: no worker ", who, " shown in ", room, " at this point of the story")
		return
	var want := TopdownFigure.hit_frame(action) if int(TopdownFigure.spec(action).hit) >= 0 else 1
	var got := false
	for i in 1800:
		if fig.work.action == action and fig.work.hold < 0 and (fig.work.walking or fig.work.frame() == want):
			got = true
			break
		await frames(1)
	if not got: print("  capture: ", who, " did not play ", action, " in half a minute (", fig.work.action, ")")
	await RenderingServer.frame_post_draw
	await s_detail(name, (fig.feet as Vector2) - p.screen + Vector2(0, 14))

## The player using a place of the table (the first of its kind the character reaches): stood on its user's cell, facing
## it, the context button pressed through the HUD, the shot mid-pose (before the page opens).
func s_place_use(name, kind: String) -> void:
	var r0 := {}
	for r in PlaceRules.all():
		if str(r.kind) == kind and r0.is_empty(): r0 = r
	if r0.is_empty(): return
	var at := PlaceRules.point(r0)
	var stand := PlaceRules.stand_point(r0)
	Game.world.load_room(_c(), str(r0.room), "", stand)
	GameEvents.flush()
	await frames(10)
	_bind()
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
	hud._after_interact(Game.submit({"type": "interact", "object": str(r0.object)}), str(r0.object))
	await frames(int(hud.PLACE_POSE_S * 60.0 * 0.85))
	await s_detail(name, Vector2(0, 0))
	hud.open_place_page()
	await frames(20)
	main.close_all_pages()
	await frames(10)

## Stand the body at a cell of a room (entered through the World authority when it is not the one on view), the
## notices cleared, and let the view settle.
func s_place_at(room: String, cell: Vector2, n: int) -> void:
	if Game.room_rt == null or Game.room_rt.room_id != room:
		Game.world.load_room(_c(), room, "", (cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		GameEvents.flush()
		await frames(20)
	_bind()
	w.player.motor.place((cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	w.player.motor.dir = Vector2.DOWN
	w._settle_camera()
	main.hud.toasts.clear()
	await frames(n)

## The world alone (no HUD, no names) round a cell: `size` screen px about it, doubled.
func s_cell_detail(name, cell: Vector2, size: Vector2) -> void:
	main.hud.visible = false
	w.overlay.visible = false
	await frames(2)
	var art := (cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE / TopdownRoom.ART
	var at: Vector2 = (art - w.camera.position + Vector2(TopdownRoom.VIEW) * 0.5) * 2.0
	var r := Rect2i(Vector2i((at - size * 0.5).round()), Vector2i(size))
	r.position.x = clampi(r.position.x, 0, 1280 - r.size.x)
	r.position.y = clampi(r.position.y, 0, 720 - r.size.y)
	await s_region(name, Rect2(r), 2)
	main.hud.visible = true
	w.overlay.visible = true

## The places' state: the letters read or one sent, the boards read, the storehouse full or empty, the notices seen
## forgotten, a furnace batch due in `secs` (or none), the Herb Terraces' beds (one ripe, one growing, one bare).
func s_mail_read() -> void:
	for mm in Game.account.mail: mm["read"] = true

func s_mail_send(template: String) -> void:
	Game.mail.apply_send(_c().id, template, [], {})

func s_read_board() -> void:
	PlaceRules.read_board(Game, _c())

func s_storage(full: bool) -> void:
	Game.account.storage["items"] = PLACES_STOCK.duplicate(true) if full else []

func s_seen_forgotten() -> void:
	for f in _c().quests.flags.keys():
		if str(f).begins_with(PlaceRules.SEEN): _c().quests.flags.erase(f)

func s_furnace(secs) -> void:
	_c().crafting["auto_queue"] = [] if secs == null else [{"recipe": "healing_pill", "count": 2, "done_utc": Clock.now_utc() + float(secs), "quality": "common"}]

func s_beds() -> void:
	var c = _c()
	var fams: Dictionary = ContentDB.config("garden").get("families", {})
	var herb := str(fams[fams.keys()[0]].get("10", "")) if not fams.is_empty() else ""
	for b in [["bed_0", 1.0], ["bed_1", 0.45]]:
		var rec: Dictionary = Game.crafting.bed_record(c, "ja_herb_terraces:" + str(b[0]))
		rec.herb = herb
		rec.progress = float(b[1])
		rec.updated = Clock.now_utc()
		rec.grow_s = 360000.0

## An action on the page on top (the Menu's "open", a card's "card_travel", a tree's "node"), as a tap would send it.
func s_page_action(action: String, arg = null) -> void:
	var pg = main.pages.back() if not main.pages.is_empty() else null
	if pg != null: pg.on_action(action, arg)

## A property of the page on top, redrawn ("sel", "speed_open"); `bag_item` picks the Bag's first stack of an item.
func s_page_set(prop: String, value) -> void:
	var pg = main.top_page()
	pg.set(prop, value.duplicate(true) if value is Dictionary else value)
	pg.queue_redraw()

func s_bag_select(item: String) -> void:
	await s_page_set("sel", {"bag": _c().inventory.first_index(item)})

## Until the walk auto-path started ends (at most half a minute).
func s_travel_wait() -> void:
	for i in 1800:
		await get_tree().physics_frame
		if Game.world.auto_path_target(_c()) == "": break

## The array of the room tapped: where it asks to go (the travel picker), or its talk.
func s_array_tap(object: String, mode := "picker") -> void:
	var r := Game.submit({"type": "interact", "object": object})
	if mode == "dialogue":
		main.open_page("dialogue", {"convo": r.get("dialogue", {})})
	elif mode == "sect":
		main.open_page(str(r.get("open_page", "transfer_array")), r.get("page_args", {"object": object}))   # the travel picker
	elif r.has("open_page"):
		var pa := {"object": object}
		pa.merge(r.get("page_args", {}), true)
		main.open_page(str(r.open_page), pa)
	elif r.has("dialogue"):
		main.open_page("dialogue", {"convo": r.dialogue})
	else:
		print("  capture: the array did not ask (%s)" % str(r))

# ------------------------------------------------------------------------------------------------------ decision 42/43, staged and held still
## One staged shot: the room entered, the player at the spot in their pose, the listed people placed round them in
## theirs (anyone else in the room hidden), the tree held still, then the world alone at x2. Where each body stands on
## the shot goes into boxes.json.
const STAGED_HOLD := {"idle": 0, "salute": 2, "kneel": 2, "point": 1, "startle": 1}   ## the frame each gesture is held on
func s_staged(name, sc: Dictionary) -> void:
	get_tree().paused = false
	Game.world.load_room(_c(), str(sc.room), "", (sc.spot as Vector2) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	_bind()
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
		fig.art.t = (float(STAGED_HOLD.get(act, 0)) + 0.5) / float(TopdownFigure.spec(act).fps)
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
	(await world_shot()).save_png(ProjectSettings.globalize_path(_png(name)))
	var cam: Vector2 = w.camera.position
	var bx := {"player": _on_shot(p.screen, cam), "people": {}}
	for s in staged: bx.people[s[0]] = _on_shot(s[1].feet, cam)
	get_tree().paused = false
	for s in staged: s[1].visible = false
	# The people made for this shot only (not in the room) go with it, so they stand in no later room.
	for made in made_here:
		for n in made:
			if n is Node and is_instance_valid(n): n.queue_free()
	boxes[_name(name)] = bx

## Where a point of the world (art px) lands on a world shot (x2 screen px).
func _on_shot(pt: Vector2, cam: Vector2) -> Array:
	var v: Vector2 = (pt - cam + Vector2(TopdownWorld.VIEW) * 0.5) * 2.0
	return [v.x, v.y]

## A fight on the square with the jian, held still: two boarlets and a crab round the player, the three cuts of the combo
## played on the body frame by frame; the whole view on the rising cut's hit (`name`), and every frame round the body
## (`name`_combo).
func s_staged_fight(name = "*") -> void:
	var c = _c()
	Game.inventory.apply_add(c.id, "training_jian", 1, "capture")
	Game.submit({"type": "equip", "index": c.inventory.first_index("training_jian")})
	var cell := Vector2(34.0, 21.0)
	Game.world.load_room(c, "lf_village", "", (cell + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
	GameEvents.flush()
	await frames(10)
	await s_spot(cell, 120)
	for id in w.figures:
		var fig = w.figures[id]
		if is_instance_valid(fig) and fig.art is TopdownPlaces.Person:
			fig.visible = false
			fig.staged = true
	Game.room_rt.enemies.clear()
	Game.room_rt.spawn_slots.clear()
	Game.room_rt.loot.clear()
	main.close_all_pages()
	await s_start(m.pos)
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
				(await world_shot()).save_png(ProjectSettings.globalize_path(_png(name)))
				bx = {"player": _on_shot(p.screen, w.camera.position), "people": {}}
			tiles.append(await crop(192, 144))
	sheet(_png(str(name) + "_combo"), tiles, 6)
	get_tree().paused = false
	boxes[_name(name)] = bx

## A lineup ([def, offset from MONSTER_SPOT in cells, elite]) set round the player on the room's floor, the room's own
## foes and people cleared, each doing nothing until it is posed; the game is then held still.
var lineup: Array = []
func s_lineup(list: Array) -> void:
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
	lineup = []
	for f in list:
		var at: Vector2 = w.room.nearest_standable((MONSTER_SPOT + (f[1] as Vector2) + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		var e: EnemyState = Game.enemies.spawn_at(str(f[0]), at, 1, {"elite": bool(f[2])})
		e.altitude = w.room.height_at(e.plane)
		e.ai.state = "idle"
		e.ai.timer = 99.0
		lineup.append(e)
	await frames(20)
	get_tree().paused = true

## The lineup posed: each foe held on frame `i` of `act` (negative counts from the end), turned toward `dir` (mirrored
## for the foes right of the player, with `mirror`).
func s_pose_lineup(act: String, i: int, dir: Vector2, mirror := false) -> void:
	for e in lineup: _pose_foe(e, act, dir if not mirror or e.plane.x <= m.pos.x else Vector2(-dir.x, dir.y), i)

## The lineup struck down, each held on its fall.
func s_fell_lineup() -> void:
	for e in lineup:
		Game.combat._damage_enemy(e, e.pools.max_hp * 10.0, _c().id, "physical", "none", false, {})
		_pose_foe(e, "death", Vector2.DOWN, -3)

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
func s_lineup_shot(name = "*") -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := await world_shot()
	img.save_png(ProjectSettings.globalize_path(_png(name)))
	var at := Vector2i((p.screen - w.camera.position + Vector2(320, 180)) * 2.0) - Vector2i(340, 230)
	var crop_img := img.get_region(Rect2i(at.clamp(Vector2i.ZERO, Vector2i(1280 - 680, 720 - 320)), Vector2i(680, 320)))
	crop_img.resize(1360, 640, Image.INTERPOLATE_NEAREST)
	crop_img.save_png(ProjectSettings.globalize_path(_png(str(name) + "_x4")))

## The hollowed eel on the night's river (raised as the night's event raises it, if it is not up), idle below the
## player on the bank.
func s_eel_on_river() -> void:
	eel = _foe("hollowed_eel")
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

## The eel held on frame `i` of `act`, turned to the player, the world alone at x2.
func s_eel_pose_shot(name, act: String, i: int) -> void:
	if eel == null: return
	_pose_foe(eel, act, (m.pos - eel.plane).normalized(), i)
	await get_tree().process_frame
	await get_tree().process_frame
	(await world_shot()).save_png(ProjectSettings.globalize_path(_png(name)))

## Leeches on the bank (looping, drawn up and stretched out) and in the river (swimming), the player between them,
## held still.
func s_leeches() -> void:
	get_tree().paused = false
	var bank := MONSTER_SPOT + Vector2(0, 4.9)
	await s_lineup([["marsh_leech", Vector2(-4.4, 4.6), false], ["marsh_leech", Vector2(-2.2, 5.0), false]])
	var leeches: Array = lineup
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

# ------------------------------------------------------------------------------------------------------ the Hollow Night and the first boss
func _foe(def_id: String) -> EnemyState:
	for e in Game.room_rt.living_enemies():
		if e.def_id == def_id and e.team == "enemy": return e
	return null

## Beside a villager, strike at their foes of `def_id` until `n` fall (the body kept whole); a shot mid-fight when named.
func s_strike_at(object: String, def_id: String, n: int, name := "") -> void:
	var o: Dictionary = Game.room_rt.object_def(object)
	if o.is_empty(): return
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	m.place(w.room.spot_near(at, float(o.get("alt", 0.0)), at + Vector2(-40, 30)))
	var shot_taken := name == ""
	for i in 900:
		_c().pools.hp = _c().pools.max_hp
		var near: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.def_id == def_id and e.plane.distance_to(at) < 220.0 and (near == null or e.plane.distance_to(m.pos) < near.plane.distance_to(m.pos)): near = e
		if near == null: break
		if near.plane.distance_to(m.pos) > 44.0: m.place(w.room.nearest_standable(near.plane + (m.pos - near.plane).normalized() * 30.0))
		if i % 12 == 0: p.aim_attack((near.plane - m.pos).normalized())
		if not shot_taken and i % 12 == 7:
			await s_shot(name)
			shot_taken = true
		await frames(1)

## Talk to a villager and send them to the hut (the choice with the night's effects).
func s_send_in(object: String) -> void:
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

## Striking at the minnows that come near, until the grey spreads up the lane (`lane`) and the eel's boss card shows
## (`card`), each shot as it comes.
func s_lane_and_card(lane, card) -> void:
	var got := {"lane": false, "card": false}
	for i in 3600:
		var r = main.scenes.run
		if not got.lane and r != null and str(r.id) == "grey_spreads" and r.begun and str(r.row.steps[r.i].get("text", "")).contains("The lane") and float(r.t) >= 1.2:
			await s_shot(lane)
			got.lane = true
		var pl = main.moments.playing
		if not got.card and pl != null and str(pl.row.get("id", "")) == "boss_intro" and float(pl.st) >= 0.8:
			await s_shot(card)
			got.card = true
		if got.lane and got.card: break
		var near: EnemyState = _foe("hollow_minnow")
		if near != null and near.plane.distance_to(m.pos) < 50.0 and i % 12 == 0: p.aim_attack((near.plane - m.pos).normalized())
		await frames(1)
	if not got.card: print("  capture: the eel's card not caught")

## The eel once it is up (waiting at most `limit` frames), its minnows and its waves let go.
func s_eel_found(limit := 1200) -> void:
	for i in limit:
		if _foe("hollowed_eel") != null: break
		await frames(1)
	eel = _foe("hollowed_eel")
	for e in Game.room_rt.living_enemies(): if e.def_id == "hollow_minnow": Game.enemies.release(e)
	Game.room_rt.event.waves = []

## On the bank above the eel, where it can reach.
func s_eel_bank() -> void:
	m.place(w.room.nearest_standable(eel.plane + Vector2(0, -96)))
	await frames(2)

## Beside the eel ashore, striking for `n` frames' worth of taps.
func s_eel_strike(n: int) -> void:
	if eel.plane.distance_to(m.pos) > 44.0: m.place(w.room.nearest_standable(eel.plane + Vector2(-30 if m.pos.x <= eel.plane.x else 30, 0)))
	for i in n:
		if i % 10 == 0: p.aim_attack((eel.plane - m.pos).normalized())
		_c().pools.hp = _c().pools.max_hp
		await frames(1)

func s_eel_hp(frac: float) -> void:
	eel.pools.hp = eel.pools.max_hp * frac

## The Hollow Night: the eel rearing, its tell.
func s_eel_tell() -> void:
	for i in 600:
		_c().pools.hp = _c().pools.max_hp
		if str(eel.ai.state) == "windup" and float(eel.ai.timer) < 0.6: break
		await frames(1)

## Beside where it lands, until it is ashore.
func s_eel_landing() -> void:
	land = eel.ai.get("land", eel.plane)
	m.place(w.room.nearest_standable(land + Vector2(-eel.aim.y, eel.aim.x) * 72.0))
	for i in 600:
		if str(eel.ai.state) == "beached": break
		await frames(1)

## The climax: below half its HP it dives, Lu comes up the river.
func s_eel_climax() -> void:
	eel.pools.hp = eel.pools.max_hp * 0.52
	for i in 900:
		_c().pools.hp = _c().pools.max_hp
		if str(eel.ai.state) == "beached": await s_eel_strike(4)
		elif str(eel.ai.state) != "windup" and eel.plane.distance_to(m.pos) > 130.0: await s_eel_bank()
		if int(eel.ai.get("phase", -1)) >= 0: break
		await frames(1)

## Lu's palm pins the eel as its great lunge lands.
func s_eel_pinned() -> void:
	for i in 900:
		_c().pools.hp = _c().pools.max_hp
		var r = main.scenes.run
		if r != null and str(r.id) == "lu_arrives" and r.begun and str(r.row.steps[r.i].do) in ["fx", "sound", "shake", "say"] and int(r.i) > 10: break
		if str(eel.ai.state) == "windup" and eel.ai.get("land", Vector2.INF) != land:
			land = eel.ai.land
			m.place(w.room.nearest_standable(land + Vector2(-eel.aim.y, eel.aim.x) * 72.0))
		await frames(1)

## Its fall: struck down wherever it comes ashore.
func s_eel_down() -> void:
	eel.pools.hp = minf(eel.pools.hp, 20.0)
	for i in 600:
		_c().pools.hp = _c().pools.max_hp
		if not eel.alive: break
		if str(eel.ai.state) in ["attack", "beached"]: await s_eel_strike(2)
		await frames(1)

## The first boss's beats as they come, for the log; a blow glancing off its hide counted.
func s_boss_listen() -> void:
	GameEvents.event.connect(func(n: String, pl: Dictionary):
		if n == "hit_landed" and pl.get("glance", false): heard.glance = int(heard.glance) + 1
		if n in ["boss_phase", "boss_overwhelmed", "scene_started", "scene_ended"] or (n == "actor_defeated" and str(pl.get("def", "")) == "hollowed_eel"):
			print("  first boss: %.1f s %s %s" % [Game.sim_time, n, str(pl.get("scene", pl.get("action", pl.get("killer", ""))))]))

## The minnows struck as they come, until the eel is up and no scene or moment holds the screen.
func s_boss_minnows() -> void:
	for i in 7200:
		if _foe("hollowed_eel") != null and main.scenes.run == null and not main.moments.screen_busy(): break
		var near: EnemyState = _foe("hollow_minnow")
		if near != null and near.plane.distance_to(m.pos) < 50.0 and i % 12 == 0: p.aim_attack((near.plane - m.pos).normalized())
		await frames(1)

## Phase 1: once the villagers' own scenes on the way to the hut have played (their balloons off the bar), on the bank
## until the eel comes ashore.
func s_boss_ashore() -> void:
	var quiet := 0
	for i in 2400:
		quiet = quiet + 1 if main.scenes.run == null and main.scenes.queue.is_empty() else 0
		if quiet > 45: break
		await frames(1)
	await s_eel_bank()
	for i in 900:
		if str(eel.ai.state) == "beached": break
		if str(eel.ai.state) == "windup" and eel.ai.get("land", Vector2.INF) != Vector2.INF:
			var at: Vector2 = eel.ai.land
			m.place(w.room.nearest_standable(at + Vector2(-eel.aim.y, eel.aim.x) * 72.0))
		elif str(eel.ai.state) == "glide" and eel.plane.distance_to(m.pos) > 130.0: await s_eel_bank()
		await frames(1)

## The waking: at 80% it throws itself back into the river and rises awake (the cut that holds the fight).
func s_boss_wake() -> void:
	eel.pools.hp = eel.pools.max_hp * 0.81
	await s_eel_strike(30)
	if int(eel.ai.get("phase", -1)) < 0: eel.pools.hp = eel.pools.max_hp * 0.79

## Phase 2: until the surge rears at the player (`surge`), or until its next landing once the scene is over.
func s_boss_wait(what: String) -> void:
	for i in 900:
		if what == "surge" and str(eel.ai.state) == "windup" and int(eel.ai.get("attack", 0)) == 1 and float(eel.ai.timer) < 0.3: break
		if what == "landing" and main.scenes.run == null and str(eel.ai.state) == "beached": break
		if str(eel.ai.state) == "glide" and eel.plane.distance_to(m.pos) > 200.0: await s_eel_bank()
		await frames(1)

## In front of it (lower on the screen than its body), striking until a blow glances off its hide (at its floor).
func s_boss_glance() -> void:
	eel.pools.hp = eel.pools.max_hp * float(eel.ai.get("hp_floor", 0.72))
	m.place(w.room.nearest_standable(eel.plane + Vector2(-34, 12)))
	var glanced := int(heard.glance)
	for i in 120:
		if i % 10 == 0: p.aim_attack((eel.plane - m.pos).normalized())
		_c().pools.hp = _c().pools.max_hp
		await frames(1)
		if int(heard.glance) > glanced:
			await frames(8)
			break

## Overwhelmed: the body let go; the eel's blows take it to the floor, until the elders come.
func s_boss_overwhelmed() -> void:
	whole_hook.on = false
	for i in 1800:
		if main.scenes.run != null and str(main.scenes.run.id) == "elders_come": break
		if str(eel.ai.state) == "glide" and eel.plane.distance_to(m.pos) > 200.0: await s_eel_bank()
		await frames(1)

## Until Lu's boat is on view with its scene playing.
func s_boss_to_the_boat() -> void:
	for i in 1800:
		if Game.room_rt != null and Game.room_rt.room_id == "lf_lu_boat" and main.scenes.run != null and str(main.scenes.run.id) == "river_token": break
		await frames(1)

# ------------------------------------------------------------------------------------------------------ the sect's stretch
## Out of the Weapon Hall to the sect's gate (the steward stops you there and shows the transfer array).
func s_to_gate(gate: String) -> void:
	if Game.room_rt.room_id != gate:
		Game.submit({"type": "use_portal", "portal": "exit", "crossing": true})
		await frames(20)
	if Game.room_rt.room_id != gate:
		Game.submit({"type": "use_portal", "portal": "west", "crossing": true})
		await frames(20)

## Through a way of this room into the next, as the walk would (the next room's live scene begins on arrival).
func s_walk_to(room_id: String, portal: String) -> void:
	if Game.room_rt.room_id == room_id: return
	Game.submit({"type": "use_portal", "portal": portal, "crossing": true})
	await frames(24)

## The three grey patches of the marsh touched in turn (at the third the token hums, and the boarlets rise).
func s_grey_patches() -> void:
	for id in ["grey_patch_0", "grey_patch_1", "grey_patch_2"]:
		var o: Dictionary = Game.room_rt.object_def(id)
		w.player.motor.place(w.room.spot_near(Vector2(float(o.at[0]), float(o.at[1])), 0.0, Vector2(float(o.at[0]) - 30, float(o.at[1]))))
		await frames(4)
		Game.submit({"type": "interact", "object": id})
		main.close_all_pages()
		await frames(4)

## A quest's first count set (the fifth boarlet down, set, not fought) and its readiness checked.
func s_quest_count(quest: String, n: int) -> void:
	var st: Dictionary = _c().quests.active.get(quest, {})
	if not st.is_empty():
		st.progress[0] = n
		Game.quest._check_ready(_c(), quest)
	GameEvents.flush()

func s_clear_spawns() -> void:
	Game.room_rt.enemies.clear()
	Game.room_rt.spawn_slots.clear()

## Back by an array, said if it refuses.
func s_array_travel(from: String, to: String) -> void:
	var r := Game.submit({"type": "array_travel", "from": from, "to": to})
	if not r.get("ok", false): print("  capture: the array %s refused: %s" % [from, str(r)])

## The mentor's report at the top: beside them, their talk.
func s_report_to(object: String) -> void:
	var e: Dictionary = Game.room_rt.object_def(object)
	w.player.motor.place(w.room.spot_near(Vector2(float(e.at[0]), float(e.at[1])), float(e.get("alt", 0.0)), Vector2(float(e.at[0]) - 40, float(e.at[1]) + 20)))
	await frames(6)
	Game.submit({"type": "interact", "object": object})
	main.close_all_pages()

# ------------------------------------------------------------------------------------------------------ the tutorials' coach
## Every scene seen, the Prologue's systems open and every tutorial but the three shown counted as known, in the
## village by the lane.
const TUTORIAL_UNLOCKS := ["move", "bag", "navigation", "jump", "shop", "quick_use", "attack", "loot", "menu", "cultivate",
	"cultivation", "codex", "equipment", "weapons", "technique_slots_2", "foundation"]
func s_tutorial_stage() -> void:
	var c = _c()
	for r in ContentDB.all("scenes"): c.quests.scenes[str(r.id)] = {"done": true}
	for i in 8:
		if main.scenes.run == null: break
		main.scenes._finish(true)
		await frames(2)
	for e in TutorialRules.entries():
		if str(e.id) in ["foundation", "techniques", "quests"]: continue
		c.tutorials.guided[str(e.id)] = 1
		c.tutorials.seen[str(e.id)] = 1
	c.tutorials.guided["quests"] = 1   # the Quests page's tour on its opening, not its guide
	for u in TUTORIAL_UNLOCKS: Unlocks.force_unlock(c.id, u)
	for q in ["morning_tide", "a_quiet_river"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	Game.world.load_room(c, "lf_village", "", Vector2.ZERO)
	GameEvents.flush()
	main.close_all_pages()
	await frames(40)
	main.hud.fight_override = false

## The coach's card as it shows: the notices cleared, a moment, the whole window, and the coach's state in the log.
## `late` keeps the pools full first (the late powers' lessons, shown at rest).
func s_snap(name = "*", late := false) -> void:
	if late:
		_c().pools.qi = _c().pools.max_qi
		_c().pools.soul = _c().pools.max_soul
	s_clear_notices()
	await frames(12)
	await s_shot(name)
	var st: Dictionary = main.coach.state()
	print("  capture: %s %s %s step %d at %s: %s" % [_name(name), st.mode, st.entry, int(st.step), str(st.rect), str(st.line)])

## Each step of a tour, one snap each ({n}: `first` on, {k}: 1 on), Next after each (the last, Done), `wait` frames.
func s_tour(id: String, pattern: String, first := 1, wait := 6, late := false) -> void:
	var n: int = (TutorialRules.entry(id).tour as Array).size()
	for i in n:
		await s_snap(pattern.replace("{n}", str(first + i)).replace("{k}", str(i + 1)), late)
		main.coach.press("next")
		await frames(wait)

func s_coach(button: String) -> void:
	main.coach.press(button)

## The character's first foundation points: at `realm`, its levels counted as gained.
func s_levels_gained(realm: String) -> void:
	var c = _c()
	c.cultivator.realm_key = realm
	Game.progression._levels_gained(c, 0, ProgressionRules.level(c))
	GameEvents.flush()

## The tab of the page on top chosen by its id.
func s_page_tab(id: String) -> void:
	var cp: Page = main.top_page()
	for i in cp.tabs.size():
		if str(cp.tabs[i].id) == id: cp.tab = i
	cp.queue_redraw()

## The late HUD powers' lessons (decision 44): every lesson known, the queue empty, the character with Flowing Palm
## slotted, at Heart Tempering 1 and an iron jian in hand, the new technique's moment passed.
func s_late_stage() -> void:
	var c = _c()
	for e in TutorialRules.entries():
		c.tutorials.guided[str(e.id)] = 1
		c.tutorials.seen[str(e.id)] = 1
	c.tutorials.queue = []
	for u in ["qi_pool", "guard", "technique_slots_2", "attack", "jump"]: Unlocks.force_unlock(c.id, u)
	Game.progression.apply_learn_technique(c.id, "flowing_palm")
	c.cultivator.technique_slots[0] = "flowing_palm"
	c.cultivator.realm_key = "heart_tempering_1"
	StatRules.rebuild(c, Game.account)
	Game.inventory.apply_add(c.id, "iron_jian", 2, "capture")
	Game.submit({"type": "equip", "index": c.inventory.first_index("iron_jian")})
	GameEvents.flush()
	await frames(240)   # the new technique's moment passes
	main.hud.equip_prompt.dismiss()

## The late power `id`'s lesson unseen and the character at `realm`, its pools full, at rest; then `unlocks` opened.
func s_late_open(id: String, realm: String, unlocks: Array) -> void:
	var c = _c()
	for k in ["guided", "seen", "at"]: c.tutorials[k].erase(id)
	c.tutorials.queue.erase(id)
	c.cultivator.realm_key = realm
	StatRules.rebuild(c, Game.account)
	c.pools.hp = c.pools.max_hp
	c.pools.qi = c.pools.max_qi
	c.pools.soul = c.pools.max_soul
	main.hud.fight_override = false
	for u in unlocks: Unlocks.force_unlock(c.id, str(u))
	GameEvents.flush()
	await frames(20)

## The Bag's stack of an item tapped (its card shown).
func s_bag_tap(item: String) -> void:
	var bp: Page = main.top_page()
	bp.on_action("bag", _c().inventory.first_index(item))
	bp.queue_redraw()

func s_hud_call(method: String) -> void:
	main.hud.call(method)

## Every tour known (the unlock tutorials' coach keeps off the shots), and every guide the forced unlocks queued put off
## at once (one Later at a time would leave the next a moment's rest and bring it back on the shot, decision 45).
func s_know_all() -> void:
	Game.tutorials._know_all(_c())

func s_guides_off() -> void:
	var c = _c()
	for id in (c.tutorials.get("queue", []) as Array).duplicate():
		Game.submit({"type": "tutorial_done", "id": str(id), "stage": "guide", "skipped": true})

## The coach kept off the shots: every tour known, the queue empty, a card on show put off (Later).
func s_coach_off() -> void:
	var c = _c()
	Game.tutorials._know_all(c)
	if c.tutorials.has("queue"): c.tutorials.queue.clear()
	for i in 6:
		if main.get("coach") == null or not bool(main.coach.visible): break
		main.coach.press("later")
		await frames(10)
	if main.get("coach") != null: main.coach.visible = false

# ------------------------------------------------------------------------------------------------------ the HUD's buttons
## One technique button (Flowing Palm, slot 0) through its cooldown: most of it left, half, a little, then the instant it
## is ready and a few frames on (the ready flash), each x3 side by side, the Qi full.
func s_cooldown_strip(name = "*") -> void:
	var c = _c()
	c.pools.qi = c.pools.max_qi
	var cd := float(ContentDB.entry("techniques", "flowing_palm").get("cooldown_s", 5))
	var tiles: Array = []
	var box := Rect2(main.hud.slots[0] - Vector2(44, 44), Vector2(88, 88))
	for left in [0.9, 0.5, 0.15, 0.02]:
		c.pools.cooldowns["tech:flowing_palm"] = cd * left
		await frames(1)
		c.pools.cooldowns["tech:flowing_palm"] = cd * left
		await RenderingServer.frame_post_draw
		tiles.append(get_tree().root.get_texture().get_image().get_region(_to_img(box)))
	c.pools.cooldowns.erase("tech:flowing_palm")
	for n in [1, 3, 3]:
		await frames(n)
		await RenderingServer.frame_post_draw
		tiles.append(get_tree().root.get_texture().get_image().get_region(_to_img(box)))
	var tw: int = tiles[0].get_width()
	var th: int = tiles[0].get_height()
	var strip_img := Image.create(tw * tiles.size() + 2 * (tiles.size() - 1), th, false, Image.FORMAT_RGBA8)
	strip_img.fill(NIGHT_INK)
	for i in tiles.size(): strip_img.blit_rect(tiles[i], Rect2i(Vector2i.ZERO, Vector2i(tw, th)), Vector2i(i * (tw + 2), 0))
	if not phone(): strip_img.resize(strip_img.get_width() * 3, strip_img.get_height() * 3, Image.INTERPOLATE_NEAREST)
	strip_img.save_png(_png(name))

func s_log_quick_slots() -> void:
	print("  capture: quick slots %s" % str(main.hud.hit_targets().filter(func(tg): return str(tg.role).begins_with("quick:")).map(func(tg): return [tg.role, tg.center])))

func s_log_bag() -> void:
	var c = _c()
	print("  capture: bag %d / %d spaces" % [c.inventory.bag.size() - c.inventory.free_slots(), c.inventory.capacity()])

func s_log_speed() -> void:
	var sp: Dictionary = Game.progression.speed_breakdown(_c())
	print("  capture: speed %.0f a minute, x%.2f: %s" % [float(sp.rate), float(sp.mult), str(sp.factors.map(func(f): return [f.label, snappedf(float(f.x), 0.01)]))])

## An item of the Bag used (its cooldown let go first).
func s_use_item(item: String) -> void:
	var c = _c()
	c.pools.cooldowns.erase("item:utility")
	Game.submit({"type": "use_item", "index": c.inventory.first_index(item), "confirm": true})

## A basic jian hit on the boarlet ahead, then a full charge (asked for mid-step, it comes next), each shot round the
## player at x2 while its number rises (`basic`, `charged`): the charged one bigger and named ("Charged ×2.3").
func s_charged(basic_name: String, charged_name: String) -> void:
	var c = _c()
	var foe: EnemyState = Game.room_rt.enemies.values()[0]
	foe.pools.max_hp = 1e7
	foe.pools.hp = 1e7
	Game.enemies.stagger(foe, 60.0)   # it stands for the shots
	# No crits for the comparison: a crit's gold number would stand for a different thing.
	c.stats.add_modifier({"stat": "crit_chance", "op": "flat", "value": -1.0, "source": "capture_no_crit"})
	Game.combat.refresh_stats(c.id)
	c.pools.cooldowns.clear()
	await s_coach_off()
	s_clear_notices()
	var basic: Dictionary = await _hit_and_shoot(func(): p.aim_attack(Vector2.RIGHT, true), false, basic_name)
	await frames(90)   # its number gone
	var charged: Dictionary = await _hit_and_shoot(func(): p.finisher(Vector2.RIGHT, 1.0), true, charged_name)
	print("  capture: basic hit %d, charged hit %d (x%.2f; its charge x%.2f)" % [int(basic.get("amount", 0)), int(charged.get("amount", 0)),
		float(charged.get("amount", 0)) / maxf(1.0, float(basic.get("amount", 0))), float(charged.get("charge", 0.0))])

## Strike with `strike`, wait for its hit (and, charged, its words), let the number rise half a second, and shoot round the
## player at x2 as `name`. Returns the hit_landed payload.
func _hit_and_shoot(strike: Callable, charged: bool, name: String) -> Dictionary:
	var got := {"p": {}}
	var listen := func(n: String, pl: Dictionary):
		if n == "hit_landed" and str(pl.get("source", "")) == "basic" and got.p.is_empty(): got.p = pl
	GameEvents.event.connect(listen)
	strike.call()
	for i in 90:
		await frames(1)
		if not got.p.is_empty() and (not charged or _charged_shown()): break
	GameEvents.event.disconnect(listen)
	await frames(30)
	await s_detail(name, Vector2(32, -40))
	return got.p

func _charged_shown() -> bool:
	for e in main.world.effects.fx:
		if str(e.get("text", "")).begins_with(Tx.t("world_view.charged").get_slice("%", 0)): return true
	return false
