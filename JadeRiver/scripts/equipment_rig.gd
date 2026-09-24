class_name EquipmentRig
extends RefCounted
## Reviewed, pixel-registered hand/holster tracks in the native 256px body frame.
## Missing item poses are rendered from the original item artwork, never idle fallback.
const GRIPS={"sword":[132,154,-64],"spear":[134,156,-20],"dagger":[146,154,0],"staff":[114,166,-90],"bow":[134,154,-90]}
const SWING=[[132,156,-125],[130,168,-165],[146,158,-70],[154,148,15],[152,128,70],[152,128,60]]
const THRUST=[[134,156,-35],[138,156,-15],[142,156,0],[148,154,0],[160,148,0],[160,148,0],[154,150,0],[142,156,-20]]
static func track(action: String,frames: int) -> Array:
	if action=="swing": return SWING.duplicate(true)
	if action=="attack": return THRUST.duplicate(true)
	# The weapon is stowed behind the body for empty-handed strikes / non-bow gear
	# during a bow pose. It follows the hip rather than obstructing either fist.
	var result=[]
	for frame in frames: result.append([118,164+(2 if frame in [2,3,4,7,8,9] else 0),-120])
	return result
static func render_sheet(source: Image,source_cell: int,grip: Array,poses: Array) -> Image:
	var cell=384
	var result=Image.create(cell*poses.size(),cell*2,false,Image.FORMAT_RGBA8)
	var crop=source.get_region(Rect2i(0,source_cell,source_cell,source_cell))
	var occupied=crop.get_used_rect()
	var pivot=Vector2(grip[0],grip[1])+Vector2.ONE*(source_cell-256)*0.5
	for frame in poses.size():
		var pose: Array=poses[frame]
		var angle=deg_to_rad(float(pose[2])-float(grip[2]))
		var anchor=Vector2(pose[0],pose[1])+Vector2(64,64)
		var transform=Transform2D(angle,anchor)
		var box=Rect2()
		for corner in [occupied.position,occupied.end,Vector2i(occupied.end.x,occupied.position.y),Vector2i(occupied.position.x,occupied.end.y)]:
			var p=transform*(Vector2(corner)-pivot)
			box=Rect2(p,Vector2.ONE) if box.size==Vector2.ZERO else box.expand(p)
		box=box.grow(2).intersection(Rect2(0,0,cell,cell))
		for y in range(int(box.position.y)/2*2,int(ceil(box.end.y)),2):
			for x in range(int(box.position.x)/2*2,int(ceil(box.end.x)),2):
				var from=(Vector2(x+1,y+1)-anchor).rotated(-angle)+pivot
				if not Rect2(Vector2.ZERO,Vector2(source_cell,source_cell)).has_point(from): continue
				var color=crop.get_pixel(int(from.x),int(from.y))
				if color.a==0: continue
				result.fill_rect(Rect2i(frame*cell+x,cell+y,2,2),color)
				result.fill_rect(Rect2i(frame*cell+cell-x-2,y,2,2),color)
	return result
