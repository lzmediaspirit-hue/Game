class_name SceneryProp
extends Node2D
const ATLAS=preload("res://art/environment/wuxia-props-v4.png")
var spec: Dictionary
func _ready():
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var p=spec.position
	position=Vector2(p[0],p[1])
	z_index=1500+int(spec.get("front_y",p[1]))
	queue_redraw()
func _draw():
	var cell=int(spec.cell)
	# Explicit regions: the painted atlas is not a uniform grid.
	var regions=[Rect2(0,0,380,475),Rect2(380,0,420,475),Rect2(800,0,575,475),Rect2(1375,0,399,475),Rect2(0,480,360,407),Rect2(380,480,420,407),Rect2(800,480,565,407),Rect2(1365,480,409,407)]
	var source: Rect2=regions[cell]
	var cell_size=source.size
	var size_data=spec.get("size",[cell_size.x,cell_size.y])
	var size=Vector2(size_data[0],size_data[1])
	draw_texture_rect_region(ATLAS,Rect2(-size.x*0.5,-size.y,size.x,size.y),source)
