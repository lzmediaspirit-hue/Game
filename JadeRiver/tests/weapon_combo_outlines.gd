extends "res://tests/combo_visual.gd"
func run():
	await verify_outlines(root.get_node("Wardrobe"))
	quit()
