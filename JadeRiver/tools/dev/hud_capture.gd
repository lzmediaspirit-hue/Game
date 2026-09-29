extends "res://tools/dev/topdown_capture.gd"
## Decision 42 (the prototype APK's feedback): the HUD and the pages the feedback named, before and after, into
## docs/redesign/feedback/hud/<tag>_*.png. A top-down character at the Weapon Hall's stage (its unlocks, a jian in hand,
## four techniques slotted: one cooling, one short of Qi, one ready and a spear art the jian cannot use), on the capture's
## own saves: the HUD at rest beside a person (the context), in a fight, the Techniques page and its loadout bar (a crop
## at x2), Old Ma's shop beside the Bag, and Aunt Ping's offer on the dialogue page, then the screen once it is taken
## (she has a second quest to give, which kept the talk open before decision 42).
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/hud_capture.tscn \
##     -- --tag=<before|after>

const FEEDBACK := "res://docs/redesign/feedback/hud/"
const HUD_SAVES := "user://hud_capture_saves/"
const ARTS := ["flowing_palm", "cloudpiercing_stroke", "still_water_focus", "jade_thrust"]
const UNLOCKS := ["move", "bag", "navigation", "jump", "shop", "quick_use", "attack", "loot", "menu", "cultivate", "cultivation",
	"technique_slots_2", "technique_slots_4", "world_menu", "mail", "guard", "qi_pool", "character_menu", "equipment", "town_hub"]
var tag := "after"

func _main() -> void:
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--tag="): tag = str(a).trim_prefix("--tag=")
	DirAccess.make_dir_recursive_absolute(HUD_SAVES)
	for f in DirAccess.get_files_at(HUD_SAVES): DirAccess.remove_absolute(HUD_SAVES + f)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FEEDBACK))
	TopdownLight.debug_hour = 0.375
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(HUD_SAVES)
	Game.boot()
	Game.autosave_enabled = false
	await _topdown_game(FEEDBACK)
	await frames(30)
	await _no_scenes()
	_weapon_hall_stage()
	Game.world.load_room(Game.active(), "lf_village", "", Vector2.ZERO)
	GameEvents.flush()
	await frames(20)
	await _no_scenes()
	if "--round" in OS.get_cmdline_user_args():
		await _round()
		print("hud_capture: %s round done" % tag)
		get_tree().quit()
		return
	await _rest()
	await _fight()
	await _techniques()
	await _shop()
	await _quest()
	print("hud_capture: %s done" % tag)
	get_tree().quit()

## No staged scene holds the stage: every one is marked seen, and one playing is ended.
func _no_scenes() -> void:
	var c = Game.active()
	for row in ContentDB.all("scenes"): c.quests.scenes[str(row.id)] = {"done": true}
	for i in 8:
		if main.scenes.run == null: break
		main.scenes._finish(true)
		await frames(2)
	main.close_all_pages()

## The character past the Weapon Hall, at Bone Forging 7 (its Qi pool open, so the Qi cue shows), with the capture's
## loadout; Aunt Ping has two quests to give.
func _weapon_hall_stage() -> void:
	var c = Game.active()
	for u in UNLOCKS: Unlocks.force_unlock(c.id, u)
	for q in ["morning_tide", "a_quiet_river", "the_runaway_kite"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	c.cultivator.realm_key = "bone_forging_7"
	for a in ARTS:
		if not c.cultivator.techniques_known.has(a): c.cultivator.techniques_known.append(a)
	c.cultivator.technique_slots = ARTS + [null, null, null, null]
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
	print("hud_capture: %s, weapon %s, Qi %d, slots %d" % [c.cultivator.realm_key, str(c.inventory.equipped.get("weapon", {}).get("id", "none") if c.inventory.equipped.get("weapon") != null else "none"),
		int(c.pools.max_qi), ProgressionRules.technique_slot_count(c)])

func _clear_notices() -> void:
	main.hud.toasts = []
	main.hud.log_lines = []
	main.hud.pulses = {}
	main.hud.banner.t = 99.0

## At rest beside Lu at the docks: the context (Talk) and the techniques.
func _rest() -> void:
	await _beside("npc_lu_boatman")
	main.hud.fight_override = false
	await frames(90)   # the pictures' stills are composed one a frame
	_clear_notices()
	await frames(4)
	await shot("%s_hud_rest" % tag, FEEDBACK)

## In a fight on the square: Flowing Palm cooling, Cloudpiercing Stroke short of Qi, Jade Thrust closed (a spear art).
func _fight() -> void:
	var c = Game.active()
	main.hud.fight_override = true
	await arena(w.player.motor.pos + Vector2(0, 40), [["wild_boarlet", Vector2(150, -30)], ["wild_boarlet", Vector2(190, 60)]])
	c.pools.cooldowns["tech:flowing_palm"] = 2.4
	c.pools.qi = maxf(0.0, Game.combat.technique_cost(c, ContentDB.entry("techniques", "cloudpiercing_stroke")) - 4.0)
	await frames(30)
	_clear_notices()
	c.pools.cooldowns["tech:flowing_palm"] = 2.4
	await frames(2)
	await shot("%s_hud_fight" % tag, FEEDBACK)
	Game.room_rt.enemies.clear()
	c.pools.cooldowns.erase("tech:flowing_palm")
	c.pools.qi = c.pools.max_qi
	main.hud.fight_override = null

## The Techniques page, and its loadout bar cropped at x2.
func _techniques() -> void:
	main.open_page("techniques", {})
	await frames(240)
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	img.save_png(FEEDBACK + "%s_techniques.png" % tag)
	var bar := img.get_region(Rect2i(0, 648, 660, 72))
	bar.resize(1320, 144, Image.INTERPOLATE_NEAREST)
	bar.save_png(FEEDBACK + "%s_loadout_bar.png" % tag)
	main.close_all_pages()
	await frames(10)

## Old Ma's shop beside the Bag.
func _shop() -> void:
	main.open_page("shop", {"shop": "old_ma", "npc": "old_ma"})
	await frames(90)
	await shot("%s_shop" % tag, FEEDBACK)
	main.close_all_pages()
	await frames(10)

## Aunt Ping's offer in the lane (two quests of hers on offer), then the screen once the first is taken.
func _quest() -> void:
	await _beside("npc_aunt_ping_lane")
	_clear_notices()
	var r := Game.submit({"type": "interact", "object": "npc_aunt_ping_lane"})
	if not r.has("dialogue"):
		print("hud_capture: no talk with Aunt Ping (%s)" % str(r))
		return
	main.open_page("dialogue", {"convo": r.dialogue})
	await frames(20)
	var dp = main.top_page()
	dp.line = maxi(0, dp.lines().size() - 1)
	dp.shown_chars = 9999.0
	await frames(30)
	await shot("%s_quest_offer" % tag, FEEDBACK)
	var choices: Array = dp.convo.get("choices", [])
	print("hud_capture: Aunt Ping offers %s" % str(choices.map(func(ch): return str(ch.get("accept", ch.get("text", ""))))))
	for i in choices.size():
		if choices[i].has("accept"):
			dp.on_action("choose", i)
			break
	await frames(40)
	var top = main.top_page()
	if top != null and top.page_id == "dialogue":
		top.line = maxi(0, top.lines().size() - 1)
		top.shown_chars = 9999.0
	_clear_notices()
	await frames(20)
	await shot("%s_quest_accepted" % tag, FEEDBACK)
	print("hud_capture: after the accept the talk is %s" % ("open" if top != null and top.page_id == "dialogue" else "closed"))
	main.close_all_pages()

## Stand beside a person of the room on view, facing them, and settle the camera.
func _beside(object: String) -> void:
	w = main.world
	p = w.player
	m = p.motor
	var o: Dictionary = Game.room_rt.object_def(object)
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	m.place(w.room.spot_near(at, float(o.get("alt", 0.0)), at + Vector2(0, 40)))
	m.dir = Vector2.UP
	w._settle_camera()
	await frames(30)

## Decision 43 (`-- --round`): the technique buttons, round and a little bigger, into
## docs/redesign/feedback/hud/<tag>_round_*.png: the HUD at rest beside Lu and in a fight (Flowing Palm cooling,
## Cloudpiercing Stroke short of Qi, Jade Thrust closed by the jian, Still Water Focus ready), the right thumb's cluster
## cropped at x2, and one button through its cooldown's turn to the ready flash (x3). Run once at 1280x720 and once at a
## 20:9 phone's 2400x1080 (`--resolution 2400x1080`: the `_phone` shots, the cluster at the phone's own pixels).
func _round() -> void:
	var img_size := get_tree().root.get_texture().get_image().get_size()
	var phone := img_size.x > 1280
	var sfx := "_phone" if phone else ""
	var k := float(img_size.y) / 720.0
	var off := Vector2((float(img_size.x) - 1280.0 * k) * 0.5, 0.0)
	var to_img := func(r: Rect2) -> Rect2i: return Rect2i(Vector2i((r.position * k + off).round()), Vector2i((r.size * k).round()))
	var c = Game.active()
	await _beside("npc_lu_boatman")
	main.hud.fight_override = false
	await frames(90)   # the pictures' stills are composed one a frame
	_clear_notices()
	await frames(4)
	await shot("%s_round_rest%s" % [tag, sfx], FEEDBACK)
	main.hud.fight_override = true
	await arena(w.player.motor.pos + Vector2(0, 40), [["wild_boarlet", Vector2(150, -30)], ["wild_boarlet", Vector2(190, 60)]])
	c.pools.qi = maxf(0.0, Game.combat.technique_cost(c, ContentDB.entry("techniques", "cloudpiercing_stroke")) - 4.0)
	c.pools.cooldowns["tech:flowing_palm"] = 2.4
	await frames(30)
	_clear_notices()
	c.pools.cooldowns["tech:flowing_palm"] = 2.4
	await frames(2)
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	img.save_png(FEEDBACK + "%s_round_fight%s.png" % [tag, sfx])
	var cluster: Image = img.get_region(to_img.call(Rect2(900, 380, 380, 340)))
	if not phone: cluster.resize(cluster.get_width() * 2, cluster.get_height() * 2, Image.INTERPOLATE_NEAREST)
	cluster.save_png(FEEDBACK + "%s_round_cluster%s.png" % [tag, sfx])
	# One button (Flowing Palm, slot 0) through its cooldown: most of it left, half, a little, then the instant it is
	# ready and a few frames on (the ready flash), each x3 side by side, the Qi full.
	c.pools.qi = c.pools.max_qi
	var cd := float(ContentDB.entry("techniques", "flowing_palm").get("cooldown_s", 5))
	var tiles: Array = []
	var box := Rect2(main.hud.slots[0] - Vector2(44, 44), Vector2(88, 88))
	for left in [0.9, 0.5, 0.15, 0.02]:
		c.pools.cooldowns["tech:flowing_palm"] = cd * left
		await frames(1)
		c.pools.cooldowns["tech:flowing_palm"] = cd * left
		await RenderingServer.frame_post_draw
		tiles.append(get_tree().root.get_texture().get_image().get_region(to_img.call(box)))
	c.pools.cooldowns.erase("tech:flowing_palm")
	for n in [1, 3, 3]:
		await frames(n)
		await RenderingServer.frame_post_draw
		tiles.append(get_tree().root.get_texture().get_image().get_region(to_img.call(box)))
	var tw: int = tiles[0].get_width()
	var th: int = tiles[0].get_height()
	var strip_img := Image.create(tw * tiles.size() + 2 * (tiles.size() - 1), th, false, Image.FORMAT_RGBA8)
	strip_img.fill(Color("071015"))
	for i in tiles.size(): strip_img.blit_rect(tiles[i], Rect2i(Vector2i.ZERO, Vector2i(tw, th)), Vector2i(i * (tw + 2), 0))
	if not phone: strip_img.resize(strip_img.get_width() * 3, strip_img.get_height() * 3, Image.INTERPOLATE_NEAREST)
	strip_img.save_png(FEEDBACK + "%s_round_cooldown%s.png" % [tag, sfx])
	Game.room_rt.enemies.clear()
	c.pools.qi = c.pools.max_qi
	main.hud.fight_override = null
