class_name WalkSurface
extends RefCounted
var id: String
var bounds: Rect2
var base: float
var rise: float
var rise_axis: String
var kind: String
var stratum: String
var open_edges: bool
var visual_variant: int
var support_mask: Array=[]
const FOOT_CONTACT=Vector2(9,12)
func _init(data: Dictionary):
	id=data.id
	visual_variant=int(data.get("visual_variant",0))
	support_mask=data.get("support_mask",[])
	var r=data.rect
	bounds=Rect2(r[0],r[1],r[2],r[3])
	base=data.get("height",0.0)
	rise=data.get("rise",0.0)
	rise_axis=data.get("rise_axis","x")
	kind=data.get("kind","stone")
	stratum=data.get("stratum","platform")
	open_edges=data.get("open_edges",true)
func height_at(point: Vector2) -> float:
	var t=(point.y-bounds.position.y)/bounds.size.y if rise_axis=="y" else (point.x-bounds.position.x)/bounds.size.x
	return base+rise*clampf(t,0,1)
func contains(point: Vector2) -> bool:
	if not bounds.has_point(point): return false
	if support_mask.is_empty(): return true
	var uv=(point-bounds.position)/bounds.size
	var row: String=support_mask[mini(int(uv.y*support_mask.size()),support_mask.size()-1)]
	return row[mini(int(uv.x*row.length()),row.length()-1)]=="1"
func projected_front() -> float:
	return bounds.end.y-height_at(bounds.end)
func contact_point(point: Vector2,reach=FOOT_CONTACT) -> Vector2:
	# A foot has area. Catch nearby visible support, but return a point ON the
	# original silhouette so saves, shadows and the standing sprite stay aligned.
	if contains(point): return point
	var missing=Vector2(INF,INF)
	if stratum!="platform" or not bounds.grow(maxf(reach.x,reach.y)).has_point(point): return missing
	if support_mask.is_empty():
		var p=point.clamp(bounds.position+Vector2.ONE*0.05,bounds.end-Vector2.ONE*0.05)
		return p if ((p-point)/reach).length_squared()<=1 else missing
	var rows=support_mask.size()
	var columns=str(support_mask[0]).length()
	var cell=bounds.size/Vector2(columns,rows)
	var first=((point-reach-bounds.position)/cell).floor().max(Vector2.ZERO)
	var last=((point+reach-bounds.position)/cell).floor().min(Vector2(columns-1,rows-1))
	var best=missing
	var distance=1.000001
	for y in range(int(first.y),int(last.y)+1):
		var row: String=support_mask[y]
		for x in range(int(first.x),int(last.x)+1):
			if row[x]!="1": continue
			var corner=bounds.position+Vector2(x,y)*cell
			var p=point.clamp(corner+Vector2.ONE*0.05,corner+cell-Vector2.ONE*0.05)
			if point.x>=corner.x and point.x<corner.x+cell.x: p.x=point.x
			if point.y>=corner.y and point.y<corner.y+cell.y: p.y=point.y
			var d=((p-point)/reach).length_squared()
			if d<distance:
				best=p
				distance=d
	return best
func follow_walk(next: Vector2,velocity: Vector2) -> Vector2:
	if kind not in ["tree_branch","cloud","rock_ledge"] or contains(next): return next
	# Narrow, depthless platforms guide ordinary sideways walking over their
	# uneven contour. Pure depth movement and real horizontal ends remain open.
	if absf(velocity.x)<0.0001 or absf(velocity.y)>absf(velocity.x)+0.0001: return next
	var support=contact_point(next,Vector2(0.01,FOOT_CONTACT.y))
	return support if support.is_finite() else next
func landing_lane(x: float) -> float:
	# A stable foot lane inside visible support, never across transparent pixels.
	if x<bounds.position.x+3 or x>=bounds.end.x-3: return INF
	var best=INF
	var distance=INF
	for row in 24:
		var y=bounds.position.y+(row+0.5)*bounds.size.y/24.0
		var point=Vector2(x,y)
		if not contains(point) or not contains(point+Vector2(0,3)) or not contains(point-Vector2(0,3)): continue
		if absf(y-bounds.get_center().y)<distance:
			best=y
			distance=absf(y-bounds.get_center().y)
	return best
func nearest_supported(point: Vector2) -> Vector2:
	if contains(point): return point
	if support_mask.is_empty(): return point.clamp(bounds.position+Vector2.ONE,bounds.end-Vector2.ONE)
	var best=bounds.get_center()
	var distance=INF
	for y in support_mask.size():
		var row: String=support_mask[y]
		for x in row.length():
			if row[x]!="1": continue
			var p=bounds.position+Vector2((x+0.5)/row.length(),(y+0.5)/support_mask.size())*bounds.size
			if p.distance_squared_to(point)<distance:
				best=p
				distance=p.distance_squared_to(point)
	return best
