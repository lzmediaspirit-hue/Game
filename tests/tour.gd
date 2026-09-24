# Walks every area end to end, fighting whatever is in reach, including each boss.
extends Node

var main


func _ready() -> void:
	Game.save_path = "user://tour_save.json"
	if FileAccess.file_exists(Game.save_path):
		DirAccess.remove_absolute(Game.save_path)
	Game.load_save()
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	for i in 5:
		await get_tree().physics_frame
	Game.create_character(0, "Tourist", "silver_tail", "cloud_scholar", "spear")
	main._enter(0)
	var p: Dictionary = Game.p
	p.flags["ch1_done"] = true
	p.flags["ch2_done"] = true
	p.level = 10
	p.realm = 2
	p.cls = "spear_warden"
	for id in ["spear_thrust", "long_thrust", "dragon_art", "nova", "mend"]:
		p.abilities.known.append(id)
	p.abilities.slots = ["dragon_art", "nova", "mend"]
	p.mastery.spear = 120
	var w = main.world
	for area in ["jr_town", "outskirts", "lantern", "bamboo", "cloudrest", "monastery"]:
		w.load_area(area, 40, 40)
		var W: float = w.W
		var kills := 0
		for f in 9000:
			if w.pl.x > W - 60:
				break
			var target = null
			for e in w.enemies:
				if e.alive and absf(e.x - w.pl.x) < 90:
					target = e
					break
			if target != null:
				var dx: float = target.x - w.pl.x
				w.ctl.move = Vector2(clampf(dx / 20.0, -1, 1) if absf(dx) > 34 else 0.0, clampf((target.d - w.pl.d) / 8.0, -1, 1))
				if absf(dx) < 60 and f % 5 == 0:
					w.pl.facing = 1 if dx > 0 else -1
					w.ctl.attack = true
				if f % 97 == 0:
					w.ctl.arts[f % 3] = true
				if absf(target.h - w.pl.h) > 14:
					w.pl.x += 2   # different level: walk on
			else:
				w.ctl.move = Vector2(1, 0.3 * sin(f * 0.02))
				if f % 150 == 0:
					w.ctl.jump = true
			if p.hp < 80:
				p.hp = 400
			p.qi = 100
			if w.pl.state == "dead":
				w.revive("here")
			await get_tree().physics_frame
		for e in w.enemies:
			if not e.alive:
				kills += 1
		print("TOUR %s reached x=%d/%d kills=%d boss=%s" % [area, int(w.pl.x), int(W), kills, str(w.boss == null or not w.boss.alive)])
	print("TOUR DONE")
	get_tree().quit()
