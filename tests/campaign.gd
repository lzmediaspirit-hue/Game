# Campaign-path checks in the real scene (boss arena, trial, seal, travel, defeat):
#   xvfb-run godot --path . --rendering-driver opengl3 tests/campaign.tscn   (or --headless)
extends Node

var main
var fails := 0


func check(c: bool, msg: String) -> void:
	print(("PASS " if c else "FAIL ") + msg)
	if not c:
		fails += 1


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func goto_x(x: float, d := 40.0, limit := 900) -> void:
	var w = main.world
	for i in limit:
		var dx: float = x - w.pl.x
		var dd: float = d - w.pl.d
		if absf(dx) < 6 and absf(dd) < 4:
			break
		w.ctl.move = Vector2(clampf(dx / 20.0, -1, 1), clampf(dd / 10.0, -1, 1))
		await get_tree().physics_frame
	w.ctl.move = Vector2.ZERO


func fight(target, limit := 2400) -> bool:
	var w = main.world
	for i in limit:
		if not target.alive:
			w.ctl.move = Vector2.ZERO
			return true
		var dx: float = target.x - w.pl.x
		var dd: float = target.d - w.pl.d
		w.ctl.move = Vector2(clampf(dx / 20.0, -1, 1) if absf(dx) > 34 else 0.0, clampf(dd / 8.0, -1, 1))
		if absf(dx) < 46 and absf(dd) < 10 and i % 5 == 0:
			w.pl.facing = 1 if dx > 0 else -1
			w.ctl.attack = true
		if Game.p.hp < 40:
			Game.p.hp = 400
		await get_tree().physics_frame
	w.ctl.move = Vector2.ZERO
	return not target.alive


func _ready() -> void:
	Game.save_path = "user://campaign_save.json"
	if FileAccess.file_exists(Game.save_path):
		DirAccess.remove_absolute(Game.save_path)
	Game.load_save()
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await frames(5)
	Game.create_character(0, "Tester", "topknot", "crimson_adept", "sword")
	main._enter(0)
	await frames(10)
	var w = main.world
	var p: Dictionary = Game.p
	Game.perform("talk", {"npc": "wen"})
	# strong disciple for a quick run
	p.level = 6
	p.items["herb"] = 6
	p.items["copper"] = 4
	Game.perform("quest_tick")
	check(p.quests.ch1.step == 2, "gather step done by holding items")
	# craft at the furnace station
	main._on_station("furnace")
	await frames(3)
	check(main.menus.frame.visible, "workshop opened at furnace")
	var r: Dictionary = Game.perform("craft", {"id": "brew_mend", "station": "furnace"})
	check(r.ok, "brewed at furnace")
	main.menus.close()
	# sword art learning
	for i in 20:
		Game.perform("mastery_hit", {"family": "sword"})
	check(Game.perform("learn", {"id": "crescent"}).ok, "learned Crescent Slash")
	check(p.abilities.slots[0] == "crescent", "auto-slotted art")
	# to the outskirts, kill raiders for the quest
	w.load_area("outskirts", 300, 40)
	await frames(5)
	var raiders := 0
	for e in w.enemies:
		if e.type == "raider" and e.surf == "ground" and raiders < 5:
			if await fight(e):
				raiders += 1
	for e in w.enemies:
		if raiders >= 5:
			break
		if e.type == "raider" and e.alive:
			w.pl.x = e.x - 30
			w.pl.d = e.d
			w.pl.h = e.h
			w.pl.surf = e.surf
			if await fight(e):
				raiders += 1
	check(raiders >= 5, "defeated 5 raiders (%d)" % raiders)
	Game.perform("quest_tick")
	check(p.quests.ch1.step >= 4, "raider + craft steps complete (step %d)" % p.quests.ch1.step)
	# art use in combat
	p.qi = 50
	w.ctl.arts[0] = true
	await frames(20)
	check(w.art_cd.has("crescent") or p.qi < 50, "used Crescent Slash in the field")
	# breakthrough at the field shrine
	w.pl.x = 1290
	w.pl.d = 20
	w.pl.h = 0
	w.pl.surf = "ground"
	for e in w.enemies:
		if absf(e.x - 1290) < 200:
			e.alive = false
	await frames(3)
	check(w.is_safe_spot(), "field shrine is safe with no enemies near")
	p.insight = 40
	r = Game.perform("breakthrough", {"safe": w.is_safe_spot()})
	check(r.ok and p.realm == 1, "Qi Awakening breakthrough")
	# boss arena
	w.pl.x = 2240
	w.pl.d = 40
	await goto_x(2330, 40)
	await frames(10)
	check(w.arena_locked, "arena locks when entering")
	check(await fight(w.boss, 4000), "defeated the Black River Captain")
	check(p.bosses.get("captain", false), "boss flag saved")
	check(not w.arena_locked, "arena unlocked after boss")
	# portal east now locked until Wen
	await goto_x(2670, 30)
	w.ctl.interact = true
	await frames(5)
	check(w.area_id == "outskirts", "Lantern Haven portal locked before reporting")
	w.load_area("jr_town", 260, 34)
	Game.perform("talk", {"npc": "wen"})
	check(p.flags.get("ch1_done", false), "chapter I complete")
	# travel from the shrine via world map
	w.pl.x = 130
	await frames(2)
	check(w.near_safe_travel(), "town shrine allows travel")
	w.travel_to("lantern")
	await frames(5)
	check(w.area_id == "lantern", "travelled to Lantern Haven")
	Game.perform("talk", {"npc": "suyin"})
	check(p.quests.ch2.step == 1, "chapter II started")
	# seal puzzle in bamboo
	p.items["iron"] = 3
	p.items["lotus"] = 4
	p.items["spirit_shard"] = 3
	Game.perform("quest_tick")
	w.load_area("bamboo", 2190, 14)
	for e in w.enemies:
		e.alive = false
		e.spawn.respawn = false
	await frames(3)
	w._seal_altar()
	main.menus._end_dialogue()
	check(p.flags.get("seal_primed", false), "altar primed with shards")
	var wrong: Dictionary = w.runes[1]
	w._touch_rune(wrong)
	check(w.seal_progress == 0, "wrong rune resets")
	for id in w.A.runeOrder:
		for rn in w.runes:
			if rn.id == id:
				w._touch_rune(rn)
	check(p.flags.get("seal_repaired", false), "seal repaired in order")
	check(p.quests.ch2.step == 3, "chapter II at Foundation step")
	# Foundation trial
	p.level = 6
	p.insight = 150
	p.essence = 100
	Game.perform("open_meridian")
	Game.perform("open_meridian")
	p.items["foundation_pill"] = 1
	w.load_area("bamboo", 1150, 20)
	for e in w.enemies:
		e.alive = false
		e.spawn.respawn = false
	await frames(3)
	w.start_trial()
	await frames(5)
	check(w.area_id == "trial", "entered the Inner Sea trial")
	for k in 3000:
		if w.area_id != "trial":
			break
		for e in w.enemies:
			if e.alive:
				w._hit_enemy(e, 999, 1, false)
		await get_tree().physics_frame
	await frames(10)
	check(p.realm == 2, "Foundation after trial (realm %d)" % p.realm)
	check(w.area_id == "bamboo", "returned from trial")
	# defeat and revival
	Game.p.hp = 5
	w.pl.inv = 0
	w.damage_player(50, w.pl.x + 10)
	await frames(3)
	check(w.pl.state == "dead", "player defeated")
	check(main.menus.frame.visible, "defeat dialog shown")
	var coins: int = p.coins
	main.menus.close()
	w.revive("here")
	check(w.pl.state == "idle" and p.coins < coins, "revived on site for coins")
	print("CAMPAIGN DONE fails=%d" % fails)
	get_tree().quit(1 if fails else 0)
