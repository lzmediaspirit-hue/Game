extends Node2D
## One arrow per bow release. Range is deterministic and independent of frame rate.
var plane=Vector2.ZERO
var altitude=0.0
var direction=1
var speed=620.0
var max_distance=480.0
var travelled=0.0
var zone: ZoneGeometry
func _ready():
	add_to_group("arrows")
	position=Vector2(plane.x,plane.y-altitude)
	queue_redraw()
func _physics_process(delta): advance(delta)
func advance(delta: float):
	if not is_finite(delta) or delta<=0 or is_queued_for_deletion(): return
	var distance=minf(speed*delta,max_distance-travelled)
	while distance>0.001:
		var step=minf(distance,4)
		var next=plane+Vector2(direction*step,0)
		if zone and zone.blocks_at(next,altitude,"ground"):
			queue_free()
			return
		plane=next
		travelled+=step
		distance-=step
	position=Vector2(plane.x,plane.y-altitude).snapped(Vector2(2,2))
	if travelled>=max_distance: queue_free()
func _draw():
	draw_line(Vector2(-direction*18,0),Vector2(direction*12,0),Color("d6b779"),2,false)
	draw_colored_polygon(PackedVector2Array([Vector2(direction*18,0),Vector2(direction*8,-4),Vector2(direction*8,4)]),Color("d9e3cb"))
	draw_line(Vector2(-direction*18,-4),Vector2(-direction*10,0),Color("b8cbb7"),2,false)
	draw_line(Vector2(-direction*18,4),Vector2(-direction*10,0),Color("b8cbb7"),2,false)
