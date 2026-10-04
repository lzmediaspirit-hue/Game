class_name WalkSurface
extends RefCounted
## A walkable rectangle of a room's geometry (ZoneGeometry): on the grid the stand-in ground the size of the room
## (TopdownRoom.geometry_def), which an ActorState stands on while the motor is grounded; a foe's surface_id names it.
## Its height may rise along x or y. (The side view's edges, masks, moving and crumbling decks and landing lanes went
## with the side view in S12a.)
var id: String
var bounds: Rect2
var base: float
var rise: float
var rise_axis: String
var kind: String
var stratum: String
func _init(data: Dictionary):
	id=data.id
	var r=data.rect
	bounds=Rect2(r[0],r[1],r[2],r[3])
	base=data.get("height",0.0)
	rise=data.get("rise",0.0)
	rise_axis=data.get("rise_axis","x")
	kind=data.get("kind","stone")
	stratum=data.get("stratum","platform")
func height_at(point: Vector2) -> float:
	var t=(point.y-bounds.position.y)/bounds.size.y if rise_axis=="y" else (point.x-bounds.position.x)/bounds.size.x
	return base+rise*clampf(t,0,1)
func contains(point: Vector2) -> bool:
	return bounds.has_point(point)
