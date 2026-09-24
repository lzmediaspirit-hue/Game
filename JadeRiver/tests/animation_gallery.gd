extends Node2D
const Avatar=preload("res://scripts/avatar.gd")
func _ready():
	var actions=["idle","walk","jump","attack","swing","bow","punch","meditate"]
	for i in actions.size():
		var a=Avatar.new()
		a.outfit=Wardrobe.defaults()
		a.outfit.weapon="bow" if actions[i]=="bow" else ("spear" if actions[i]=="attack" else ("none" if actions[i]=="punch" else "sword"))
		a.action=actions[i]
		a.position=Vector2(160+(i%4)*320,280+int(i/4)*340)
		a.scale=Vector2.ONE*2.1
		add_child(a)
		var label=Label.new()
		label.text=actions[i]
		label.position=a.position+Vector2(-30,20)
		add_child(label)
	await get_tree().create_timer(0.35).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://../animation-preview.png")
	get_tree().quit()
