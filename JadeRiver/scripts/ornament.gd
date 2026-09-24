extends Control
## Menu-only ornament, drawn independently from interactive controls.
var creation=false
const GOLD=Color("c8ac73")
func _ready(): mouse_filter=Control.MOUSE_FILTER_IGNORE
func _draw():
	if creation:
		draw_set_transform(Vector2(306,549),0,Vector2(1,0.26))
		draw_circle(Vector2.ZERO,196,Color("263c43"))
		draw_arc(Vector2.ZERO,192,0,TAU,100,GOLD,4,true)
		draw_arc(Vector2.ZERO,171,0,TAU,100,Color("6a837a"),2,true)
		draw_set_transform(Vector2.ZERO)
		for x in [138,474]:
			draw_line(Vector2(x,543),Vector2(x,566),Color("66766b"),3)
	else:
		draw_line(Vector2(88,153),Vector2(475,153),Color("9b8e68"),1)
		draw_line(Vector2(804,153),Vector2(1192,153),Color("9b8e68"),1)
	for center in ([Vector2(307,602)] if creation else [Vector2(640,154)]):
		for offset in [-24,0,24]:
			var p=center+Vector2(offset,0)
			draw_polyline(PackedVector2Array([p+Vector2(0,-5),p+Vector2(5,0),p+Vector2(0,5),p+Vector2(-5,0),p+Vector2(0,-5)]),GOLD,1,true)
