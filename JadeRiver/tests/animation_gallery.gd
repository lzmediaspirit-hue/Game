extends Node2D
const Avatar=preload("res://scripts/avatar.gd")
## Each action with its usual weapon (left) and with the gauntlets on both hands (right).
func _ready():
	var actions=["idle","walk","jump","attack","swing","bow","punch","meditate"]
	for i in actions.size():
		for side in 2:
			var a=Avatar.new()
			a.outfit=Wardrobe.defaults()
			a.outfit.weapon="bow" if actions[i]=="bow" else ("spear" if actions[i]=="attack" else ("none" if actions[i]=="punch" else "sword"))
			if side==1: a.outfit.weapon="gauntlets"
			a.action=actions[i]
			a.position=Vector2(160+(i%4)*320+(side*2-1)*72,280+int(i/4)*340)
			a.scale=Vector2.ONE*1.9
			add_child(a)
		var label=Label.new()
		label.text=actions[i]+"   | gauntlets"
		label.position=Vector2(160+(i%4)*320-60,280+int(i/4)*340+20)
		add_child(label)
	await get_tree().create_timer(0.35).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://../animation-preview.png")
	get_tree().quit()
