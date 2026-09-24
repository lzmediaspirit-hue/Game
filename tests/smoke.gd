# Scripted smoke run with screenshots.
#   xvfb-run -s "-screen 0 1600x900x24" godot --path . --rendering-driver opengl3 tests/smoke.tscn
# Writes PNGs to user://shots/ and prints a PASS/FAIL line per check.
extends Node

var main
var shots := "user://shots/"
var fails := 0


func check(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c:
		fails += 1


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(shots + name + ".png")


func hold(move: Vector2, n: int) -> void:
	for i in n:
		main.world.ctl.move = move
		await get_tree().physics_frame
	main.world.ctl.move = Vector2.ZERO


func goto_x(x: float, d := 40.0) -> void:
	var w = main.world
	for i in 600:
		var dx: float = x - w.pl.x
		var dd: float = d - w.pl.d
		if absf(dx) < 6 and absf(dd) < 4:
			break
		w.ctl.move = Vector2(clampf(dx / 20.0, -1, 1), clampf(dd / 10.0, -1, 1))
		await get_tree().physics_frame
	w.ctl.move = Vector2.ZERO


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(shots)
	Game.save_path = "user://smoke_save.json"
	if FileAccess.file_exists(Game.save_path):
		DirAccess.remove_absolute(Game.save_path)
	Game.load_save()
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await frames(10)
	Game.create_character(0, "Hurt render", "plum_bob", "river_traveler", "spear")
	main.title.show_slots()
	await frames(5)
	await shot("00_title")
	main.title.show_create(1)
	await frames(10)
	await shot("01_create")
	main.title.show_slots()
	main._enter(0)
	await frames(30)
	var w = main.world
	check(w.area_id == "jr_town", "entered town")
	await shot("02_town")
	# talk to Elder Wen
	await goto_x(262, 34)
	await frames(2)
	check(w.prompt.get("kind", "") == "npc", "prompt to talk: %s" % str(w.prompt.get("label", "")))
	w.ctl.interact = true
	await frames(5)
	check(main.menus.dlg.visible, "dialogue open")
	await shot("03_dialogue")
	main.menus._end_dialogue()
	check(Game.p.items.has("pick"), "got tools")
	# walk up the teahouse stairs onto the roof and harvest the roof dewleaf
	await goto_x(490, 12)
	await hold(Vector2(1, 0), 60)
	check(w.pl.h > 30, "climbed stairs onto roof, h=%.1f surf=%s" % [w.pl.h, w.pl.surf])
	await goto_x(700, 12)
	await frames(2)
	check(w.prompt.get("kind", "") == "node", "roof dewleaf prompt: %s" % str(w.prompt.get("label", "")))
	w.ctl.interact = true
	await frames(100)
	check(Game.p.items.get("herb", 0) > 0, "harvested dewleaf on roof")
	await shot("04_roof")
	# jump down off the open front edge
	await hold(Vector2(0, 1), 40)
	await frames(40)
	check(w.pl.h == 0.0, "dropped to ground")
	# menus
	for pg in ["hub", "cultivation", "inventory", "skills", "workshop", "map", "journal", "gathering"]:
		main.menus.stack.clear()
		main.menus.open(pg)
		await frames(4)
		await shot("10_" + pg)
	main.menus.close()
	await frames(4)
	# cultivation mode HUD
	main.hud.set_mode("cultivation")
	await frames(6)
	await shot("05_cultivation_mode")
	w.ctl.meditate = true
	await frames(260)
	check(Game.p.insight > 0, "meditation granted insight (%d)" % Game.p.insight)
	await shot("06_meditate")
	main.hud.set_mode("combat")
	# travel to the outskirts via the portal
	await goto_x(1470, 30)
	w.ctl.interact = true
	await frames(10)
	check(w.area_id == "outskirts", "portal to outskirts")
	await frames(20)
	await shot("07_outskirts")
	# fight the first raider
	var kills0: int = Game.p.stats.kills.get("raider", 0)
	for i in 900:
		var target = null
		for e in w.enemies:
			if e.alive and e.type == "raider":
				target = e
				break
		if target == null or Game.p.stats.kills.get("raider", 0) > kills0:
			break
		var dx: float = target.x - w.pl.x
		w.ctl.move = Vector2(clampf(dx / 20.0, -1, 1) if absf(dx) > 30 else 0.0, clampf((target.d - w.pl.d) / 8.0, -1, 1))
		if absf(dx) < 44 and absf(target.d - w.pl.d) < 10 and i % 6 == 0:
			w.pl.facing = 1 if dx > 0 else -1
			w.ctl.attack = true
		if i == 120:
			await shot("08_combat")
		if Game.p.hp < 30:
			Game.p.hp = 100
		await get_tree().physics_frame
	w.ctl.move = Vector2.ZERO
	check(Game.p.stats.kills.get("raider", 0) > kills0, "defeated a raider")
	check(Game.p.mastery.spear > 0, "spear mastery grew (%d)" % Game.p.mastery.spear)
	# bridge: climb stairs, walk on deck, then walk under it
	await goto_x(630, 18)
	await hold(Vector2(1, 0), 70)
	check(w.pl.surf == "bridge" or w.pl.h > 50, "on bridge (surf=%s h=%.0f)" % [w.pl.surf, w.pl.h])
	await goto_x(900, 12)
	await frames(2)
	await shot("09_bridge")
	check(w.prompt.get("kind", "") == "node", "bridge copper reachable from deck")
	# drop through
	w.ctl.move = Vector2(0, 1)
	w.ctl.jump = true
	await frames(2)
	w.ctl.move = Vector2.ZERO
	await frames(60)
	check(w.pl.h == 0.0, "dropped through bridge")
	await goto_x(900, 12)
	await frames(2)
	check(w.prompt.get("kind", "") != "node", "cannot harvest bridge copper from below")
	print("SMOKE DONE fails=%d" % fails)
	get_tree().quit(1 if fails else 0)
