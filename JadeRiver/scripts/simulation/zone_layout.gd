class_name ZoneLayout
extends RefCounted
## Compile authored districts into shared rendering and collision geometry.
## Building footprints derive from roof bounds, never independent magic rectangles.
static func compile(authored: Dictionary) -> Dictionary:
	var data=authored.duplicate(true)
	var retained=[]
	for item in data.objects:
		if item.get("surface","")!="": continue
		retained.append(item)
	for surface in data.surfaces:
		if surface.kind=="balcony":
			var r=surface.rect
			for side in [4,r[2]-8]:
				retained.append({"id":surface.id+"_post_"+str(side),"art":"none","height":surface.height,
					"footprint":[r[0]+side,r[1]+r[3]-4,6,4],"radius":2})
		if surface.kind!="roof": continue
		var r=surface.rect
		retained.append({"id":surface.id+"_body","art":"none","surface":surface.id,
			"support_shape":surface.id if surface.has("support_mask") else "",
			"front_y":r[1]+r[3],"footprint":[r[0],r[1],r[2],r[3]],
			"height":surface.height,"radius":0,
			"occlusion":[r[0],r[1]-surface.height,r[2],r[3]+surface.height]})
	# Low obstacles are solid volumes with support tops, so descending onto one
	# lands on it instead of teleporting the actor to a nearby free tile.
	for item in retained:
		if (item.get("height",999)>80 and not item.get("standable",false)) or item.get("art","")=="none": continue
		data.surfaces.append({"id":item.id+"_top","rect":item.footprint,
			"height":item.height,"kind":"support","stratum":"platform","open_edges":true})
	data.objects=retained
	for gate in data.get("gates",[]):
		for post in [[-100,826,54,18],[20,898,80,20]]:
			data.objects.append({"id":str(gate.id)+"_post_"+str(post[0]),"art":"none","footprint":[float(gate.x)+post[0],post[1],post[2],post[3]],"height":240,"radius":0})
	return data
