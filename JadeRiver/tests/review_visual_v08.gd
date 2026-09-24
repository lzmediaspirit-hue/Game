extends "res://tests/movement_visual_v07.gd"
func shot(label: String):
	main.world.player.sync_visual()
	main.world.camera.position=main.world.camera_target()
	main.world.update_occlusion()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../previews/v08-"+label+".png")
