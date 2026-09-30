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
	# The Weapon Hall's stage has the realm without the method a real Bone Forging 7 disciple learnt on Lu's boat.
	Game.progression.apply_learn_method(c.id, "riverbreath_fragment")
	c.cultivator.method_id = "riverbreath_fragment"
	Unlocks.force_unlock(c.id, "qi_springs")   # Bone Forging 7's own
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

## The unlock tutorials' coach keeps off the shots: every tour known, the queue empty, a card on show put off (Later).
func _coach_off() -> void:
	var c = Game.active()
	Game.tutorials._know_all(c)
	if c.tutorials.has("queue"): c.tutorials.queue.clear()
	for i in 6:
		if main.get("coach") == null or not bool(main.coach.visible): break
		main.coach.press("later")
		await frames(10)
	if main.get("coach") != null: main.coach.visible = false

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
	await _coach_off()
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
	await _coach_off()
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
	await _coach_off()
	await shot("cultivation_overview", PROG)
	var pg = main.top_page()
	pg.speed_open = true
	pg.queue_redraw()
	await frames(20)
	await _coach_off()
	await shot("cultivation_speed", PROG)
	var sp: Dictionary = Game.progression.speed_breakdown(c)
	print("progression_capture: speed %.0f a minute, x%.2f: %s" % [float(sp.rate), float(sp.mult), str(sp.factors.map(func(f): return [f.label, snappedf(float(f.x), 0.01)]))])
	main.close_all_pages()
	await frames(10)

## A basic jian hit on the left boarlet, then a full charge on the right one (asked for mid-step, it comes next), shot
## while both numbers rise: the charged one bigger and named ("Charged ×2.3"). A crop round the player at x2.
func _charged_text() -> void:
	var c = Game.active()
	await at_spot(Vector2(33, 21), 30)   # the village square, open ground
	await arena(m.pos, [["wild_boarlet", Vector2(64, 0)]])
	var foe: EnemyState = Game.room_rt.enemies.values()[0]
	foe.pools.max_hp = 1e7
	foe.pools.hp = 1e7
	Game.enemies.stagger(foe, 60.0)   # it stands for the shots
	# No crits for the comparison: a crit's gold number would stand for a different thing.
	c.stats.add_modifier({"stat": "crit_chance", "op": "flat", "value": -1.0, "source": "capture_no_crit"})
	Game.combat.refresh_stats(c.id)
	c.pools.cooldowns.clear()
	await _coach_off()
	_clear_notices()
	# A basic first step, its number shot once it has risen clear of the blow.
	var basic: Dictionary = await _hit_and_shoot(func(): p.aim_attack(Vector2.RIGHT, true), false, "combat_basic")
	await frames(90)   # its number gone
	var charged: Dictionary = await _hit_and_shoot(func(): p.finisher(Vector2.RIGHT, 1.0), true, "combat_charged")
	# The two side by side: the basic hit at the left, the charged one at the right.
	var a := Image.load_from_file(ProjectSettings.globalize_path(PROG + "combat_basic.png"))
	var b := Image.load_from_file(ProjectSettings.globalize_path(PROG + "combat_charged.png"))
	var sheet := Image.create(a.get_width() + b.get_width() + 8, a.get_height(), false, Image.FORMAT_RGBA8)
	sheet.fill(Color("071015"))
	sheet.blit_rect(a, Rect2i(Vector2i.ZERO, a.get_size()), Vector2i.ZERO)
	sheet.blit_rect(b, Rect2i(Vector2i.ZERO, b.get_size()), Vector2i(a.get_width() + 8, 0))
	sheet.save_png(PROG + "combat_basic_vs_charged.png")
	print("progression_capture: basic hit %d, charged hit %d (x%.2f; its charge x%.2f)" % [int(basic.get("amount", 0)), int(charged.get("amount", 0)),
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
	await shot_detail(name, Vector2(32, -40), PROG)
	return got.p

func _charged_shown() -> bool:
	for e in main.world.effects.fx:
		if str(e.get("text", "")).begins_with(Tx.t("world_view.charged").get_slice("%", 0)): return true
	return false
