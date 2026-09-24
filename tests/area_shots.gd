# Screenshots of every area: xvfb-run godot --path . --rendering-driver opengl3 tests/area_shots.tscn
extends Node

func _ready() -> void:
	Game.save_path = "user://shots_save.json"
	if FileAccess.file_exists(Game.save_path):
		DirAccess.remove_absolute(Game.save_path)
	Game.load_save()
	var main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().physics_frame
	Game.create_character(0, "Painter", "windswept", "jade_sentinel", "sword")
	main._enter(0)
	Game.p.flags["ch1_done"] = true
	Game.p.flags["ch2_done"] = true
	DirAccess.make_dir_recursive_absolute("user://shots/")
	for spot in [["lantern", 400], ["bamboo", 760], ["bamboo", 2300], ["cloudrest", 700], ["monastery", 820], ["monastery", 2800]]:
		main.world.load_area(spot[0], spot[1], 50)
		for i in 40:
			await get_tree().physics_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("user://shots/area_%s_%d.png" % [spot[0], spot[1]])
	get_tree().quit()
