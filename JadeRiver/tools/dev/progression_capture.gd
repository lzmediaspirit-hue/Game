extends "res://tools/dev/hud_capture.gd"
## Decision 45 (after build 110, the progression numbers): the review shots, into docs/redesign/feedback/progression/.
## A top-down character at the Weapon Hall's stage (hud_capture's: Bone Forging 7, a jian, four arts), on the capture's
## own saves (never the Max Tester's), with three things in the three quick slots:
##   hud_quick_rest, hud_quick_fight, hud_quick_cluster   the HUD with its three quick slots at rest and in a fight, and
##                                                          the thumb's cluster at x2 (the phone's own pixels at 2400x1080)
##   bag_50                                                  the Bag at 50 spaces, a pill chosen: its Quick 1-3 buttons
##   cultivation_overview, cultivation_speed                 the Cultivation page's speed line, and its list of terms and
##                                                          ways (Qi-Gathering Incense burning)
##   combat_basic_vs_charged                                 a basic jian hit and a full charge's in the combat text, x2
## Run once at 1280x720 and once at a 20:9 phone's 2400x1080 (`--resolution 2400x1080`: the HUD shots end `_phone`):
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/progression_capture.tscn
##   xvfb-run -a -s "-screen 0 2400x1080x24" godot --rendering-driver opengl3 --path . res://tools/dev/progression_capture.tscn \
##     --resolution 2400x1080

const PROG := "res://docs/redesign/feedback/progression/"
const PROG_SAVES := "user://progression_capture_saves/"
const QUICK := ["herbal_tea", "healing_pill", "qi_gathering_incense"]

func _main() -> void:
	DirAccess.make_dir_recursive_absolute(PROG_SAVES)
	for f in DirAccess.get_files_at(PROG_SAVES): DirAccess.remove_absolute(PROG_SAVES + f)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PROG))
	TopdownLight.debug_hour = 0.375
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(PROG_SAVES)
	Game.boot()
	Game.autosave_enabled = false
	await _topdown_game(PROG)
	await frames(30)
	await _no_scenes()
	_weapon_hall_stage()
	var c = Game.active()
	for it in [["healing_pill", 2], ["qi_gathering_incense", 3], ["rice_ball", 4], ["riverreed_ginseng_10", 2], ["qi_gathering_pill", 1]]:
		Game.inventory.apply_add(c.id, str(it[0]), int(it[1]), "capture")
	c.inventory.quick = QUICK.duplicate()
	Game.tutorials._know_all(c)   # the unlock tutorials' coach keeps off the shots
	Game.world.load_room(c, "lf_village", "", Vector2.ZERO)
	GameEvents.flush()
	await frames(20)
	await _no_scenes()
	var img_size := get_tree().root.get_texture().get_image().get_size()
	var phone := img_size.x > 1280
	await _quick_hud(phone)
	if not phone:
		await _bag()
		await _cultivation()
		await _charged_text()
	print("progression_capture: done (%s)" % ("phone" if phone else "1280x720"))
	get_tree().quit()

func _coach_off() -> void:
	for i in 6:
		if main.get("coach") == null or not bool(main.coach.visible): break
		main.coach.press("later")
		await frames(10)

## The HUD with its three quick slots: at rest beside Lu (the Talk button on ring 2 too) and in a fight on the square,
## and the right thumb's cluster.
func _quick_hud(phone: bool) -> void:
	var img_size := get_tree().root.get_texture().get_image().get_size()
	var sfx := "_phone" if phone else ""
	var k := float(img_size.y) / 720.0
	var off := Vector2((float(img_size.x) - 1280.0 * k) * 0.5, 0.0)
	await _beside("npc_lu_boatman")
	main.hud.fight_override = false
	await frames(90)
	await _coach_off()
	_clear_notices()
	await frames(4)
	await shot("hud_quick_rest%s" % sfx, PROG)
	main.hud.fight_override = true
	await arena(w.player.motor.pos + Vector2(0, 40), [["wild_boarlet", Vector2(150, -30)], ["wild_boarlet", Vector2(190, 60)]])
	await frames(30)
	_clear_notices()
	await frames(2)
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	img.save_png(PROG + "hud_quick_fight%s.png" % sfx)
	var box := Rect2(880, 300, 400, 420)
	var cluster: Image = img.get_region(Rect2i(Vector2i((box.position * k + off).round()), Vector2i((box.size * k).round())))
	if not phone: cluster.resize(cluster.get_width() * 2, cluster.get_height() * 2, Image.INTERPOLATE_NEAREST)
	cluster.save_png(PROG + "hud_quick_cluster%s.png" % sfx)
	print("progression_capture: quick slots %s" % str(main.hud.hit_targets().filter(func(tg): return str(tg.role).begins_with("quick:")).map(func(tg): return [tg.role, tg.center])))
	Game.room_rt.enemies.clear()
	main.hud.fight_override = null
	await frames(10)

## The Bag at 50 spaces, a Healing Pill chosen so its card shows the three Quick buttons.
func _bag() -> void:
	var c = Game.active()
	main.open_page("inventory", {})
	await frames(60)
	var pg = main.top_page()
	pg.sel = {"bag": c.inventory.first_index("healing_pill")}
	pg.queue_redraw()
	await frames(40)
	await shot("bag_50", PROG)
	print("progression_capture: bag %d / %d spaces" % [c.inventory.bag.size() - c.inventory.free_slots(), c.inventory.capacity()])
	main.close_all_pages()
	await frames(10)

## The Cultivation page: the speed line on the Overview, then its list (Qi-Gathering Incense burning).
func _cultivation() -> void:
	var c = Game.active()
	c.pools.cooldowns.erase("item:utility")
	Game.submit({"type": "use_item", "index": c.inventory.first_index("qi_gathering_incense"), "confirm": true})
	main.open_page("cultivation", {})
	await frames(90)
	await shot("cultivation_overview", PROG)
	var pg = main.top_page()
	pg.speed_open = true
	pg.queue_redraw()
	await frames(20)
	await shot("cultivation_speed", PROG)
	var sp: Dictionary = Game.progression.speed_breakdown(c)
	print("progression_capture: speed %.0f a minute, x%.2f: %s" % [float(sp.rate), float(sp.mult), str(sp.factors.map(func(f): return [f.label, snappedf(float(f.x), 0.01)]))])
	main.close_all_pages()
	await frames(10)

## A basic jian hit on the left boarlet, then a full charge on the right one (asked for mid-step, it comes next), shot
## while both numbers rise: the charged one bigger and named ("Charged ×2.3"). A crop round the player at x2.
func _charged_text() -> void:
	var c = Game.active()
	await arena(w.player.motor.pos + Vector2(0, 40), [["wild_boarlet", Vector2(-56, 0)], ["wild_boarlet", Vector2(56, 0)]])
	for e in Game.room_rt.enemies.values():
		e.pools.max_hp = 1e7
		e.pools.hp = 1e7
	c.pools.cooldowns.clear()
	_clear_notices()
	p.aim_attack(Vector2.LEFT, true)
	await frames(6)
	p.finisher(Vector2.RIGHT, 1.0)
	for i in 70:
		await frames(1)
		if _charged_shown(): break
	await frames(4)
	await shot_detail("combat_basic_vs_charged", Vector2(0, -20), PROG)

func _charged_shown() -> bool:
	for e in main.world.effects.fx:
		if str(e.get("text", "")).begins_with(Tx.t("world_view.charged").get_slice("%", 0)): return true
	return false
