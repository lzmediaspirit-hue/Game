extends Node2D
## One shared atlas split into far/near layers so the actor passes between posts.
const ART=preload("res://art/environment/room-gate.png")
var spec: Dictionary
func _ready():
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var size=ART.get_size()
	var scale_factor=400.0/size.y
	for near in [false,true]:
		var sprite=Sprite2D.new()
		sprite.texture=ART
		sprite.region_enabled=true
		var split=floorf(size.x*0.5)
		sprite.region_rect=Rect2(Vector2(split if near else 0,0),Vector2(size.x-split if near else split,size.y))
		sprite.centered=false
		sprite.position=Vector2(float(spec.x)-size.x*scale_factor*0.5+(split*scale_factor if near else 0),530)
		sprite.scale=Vector2.ONE*scale_factor
		sprite.z_index=2408 if near else 2340
		add_child(sprite)
