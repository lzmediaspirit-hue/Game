class_name ComboRig
extends RefCounted
## Authoring recipes in the original 256px registration space. Every layer,
## including hair dyes and held equipment, uses the same deformation per frame.
## Source poses supply joint articulation; tracks add aim, weight and recovery.
const RECIPES={
	"swing_1":{"source":"swing","frames":[0,1,2,3,4,5,2,0],"aim":0.0,"lean":2.0,"crouch":0.0,"label":"Rising cut"},
	"swing_2":{"source":"swing","frames":[0,3,5,4,3,2,1,0],"aim":0.35,"lean":-4.0,"crouch":2.0,"label":"Return cut"},
	"swing_3":{"source":"swing","frames":[0,3,4,5,3,2,1,0],"aim":0.75,"lean":10.0,"crouch":6.0,"label":"Heavy descending cut"},
	"thrust_1":{"source":"attack","frames":[0,1,2,3,4,5,6,0],"aim":0.0,"lean":2.0,"crouch":0.0,"label":"Straight thrust"},
	"thrust_2":{"source":"attack","frames":[0,1,1,3,4,5,6,0],"aim":0.55,"lean":4.0,"crouch":8.0,"label":"Low thrust"},
	"thrust_3":{"source":"attack","frames":[0,1,2,3,4,5,6,0],"aim":-0.6,"lean":12.0,"crouch":-2.0,"label":"High lunging thrust"},
	"punch_1":{"source":"punch","frames":[0,1,2,3,4,5,0,0],"aim":0.0,"lean":0.0,"crouch":0.0,"label":"Lead jab"},
	"punch_2":{"source":"punch","frames":[0,6,7,8,9,10,0,0],"aim":0.15,"lean":6.0,"crouch":2.0,"label":"Rear cross"},
	"punch_3":{"source":"punch","frames":[0,6,7,8,9,10,0,0],"aim":-1.1,"lean":4.0,"crouch":-4.0,"label":"Rising uppercut"}
}
const WEIGHT=[0.0,0.3,0.65,1.0,1.0,0.75,0.3,0.0]
static func warp(point: Vector2,recipe: Dictionary,frame: int) -> Vector2:
	var weight=float(WEIGHT[frame])
	var upper=clampf((184.0-point.y)/32.0,0,1)
	return point+Vector2(float(recipe.lean)*upper,float(recipe.crouch)*upper+float(recipe.aim)*maxf(0,point.x-138)*upper)*weight
static func bake(source: Image,cell: int,recipe: Dictionary,weapon=false) -> Image:
	var result=Image.create(cell*8,cell*2,false,Image.FORMAT_RGBA8)
	var offset=Vector2.ONE*(cell-256)*0.5
	for frame in 8:
		var crop=source.get_region(Rect2i(int(recipe.frames[frame])*cell,cell,cell,cell))
		if weapon:
			var tracks=EquipmentRig.track(recipe.source,12)
			var grip: Array=tracks[int(recipe.frames[frame])]
			var anchor=Vector2(grip[0],grip[1])
			var target=warp(anchor,recipe,frame)+offset
			# Holstered weapons follow the hip during punches, not the striking fist.
			var angle=0.0 if recipe.source=="punch" else atan(float(recipe.aim)*float(WEIGHT[frame]))
			for y in range(0,cell,2):
				for x in range(0,cell,2):
					var sample=(Vector2(x+1,y+1)-target).rotated(-angle)+anchor+offset
					if not Rect2(0,0,cell,cell).has_point(sample): continue
					var color=crop.get_pixel(int(sample.x),int(sample.y))
					if color.a==0: continue
					result.fill_rect(Rect2i(frame*cell+x,cell+y,2,2),color)
					result.fill_rect(Rect2i(frame*cell+cell-x-2,y,2,2),color)
			continue
		var bounds=crop.get_used_rect().grow(2).intersection(Rect2i(0,0,cell,cell))
		# Forward-mapped 2px texels with vertical span fill retain the native pixel
		# grid and avoid cracks where the shared garment/body rig changes slope.
		for y in range(bounds.position.y/2*2,bounds.end.y,2):
			for x in range(bounds.position.x/2*2,bounds.end.x,2):
				var color=crop.get_pixel(x,y)
				if color.a==0: continue
				var p=(warp(Vector2(x,y)-offset,recipe,frame)+offset).snapped(Vector2(2,2))
				var q=(warp(Vector2(x,y+2)-offset,recipe,frame)+offset).snapped(Vector2(2,2))
				var height=maxi(2,int(q.y-p.y))
				var rect=Rect2i(int(p.x),int(p.y),2,height).intersection(Rect2i(0,0,cell,cell))
				if not rect.has_area(): continue
				result.fill_rect(Rect2i(rect.position+Vector2i(frame*cell,cell),rect.size),color)
				result.fill_rect(Rect2i(frame*cell+cell-rect.end.x,rect.position.y,rect.size.x,rect.size.y),color)
	return result
