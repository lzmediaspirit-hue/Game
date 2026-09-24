extends SceneTree
var main
func _initialize(): call_deferred("run")
func shot(label: String):
	main.world.player.sync_visual()
	main.world.camera.position=main.world.camera_target()
	main.world.update_occlusion()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../previews/v06-"+label+".png")
func run():
	var stage=load("res://scenes/pixel_stage.tscn").instantiate()
	root.add_child(stage)
	main=stage.get_node("GameViewport/JadeRiver")
	main.preview_mode=true
	await process_frame
	main.enter_world(root.get_node("Wardrobe").defaults())
	for theme in WorldCatalog.REGIONS:
		main.change_region(theme,7,1)
		var world=main.world
		world.set_process(false)
		world.player.set_physics_process(false)
		world.player.plane=Vector2(1450,850)
		await shot(theme+"-ground")
		world.player.plane=Vector2(4440,850)
		await shot(theme+"-ascent-base")
		var platform=world.by_id("ascent_03")
		world.player.surface=platform
		world.player.plane=platform.bounds.get_center()
		world.player.altitude=platform.base
		await shot(theme+"-branches")
		platform=world.by_id("cloud_03")
		if platform:
			world.player.surface=platform
			world.player.plane=platform.bounds.get_center()
			world.player.altitude=platform.base
			await shot(theme+"-clouds")
	print("GENERATED_VISUALS: captured all regions")
	quit()
