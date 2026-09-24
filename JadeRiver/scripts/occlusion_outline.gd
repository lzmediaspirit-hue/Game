class_name OcclusionOutline
extends Node2D
## The contour follows the composited animation and equipped layers.
var source: Node2D
var poses: Dictionary={}
var sheets: Dictionary={}
var pose: Texture2D
func _ready():
	z_index=4090
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var shader=Shader.new()
	shader.code="""shader_type canvas_item;
render_mode unshaded;
void fragment() {
 vec2 p=TEXTURE_PIXEL_SIZE*2.0;
 float a=texture(TEXTURE,UV).a;
 float edge=max(max(texture(TEXTURE,UV+vec2(p.x,0)).a,texture(TEXTURE,UV-vec2(p.x,0)).a),max(texture(TEXTURE,UV+vec2(0,p.y)).a,texture(TEXTURE,UV-vec2(0,p.y)).a));
 COLOR=vec4(0.66,1.0,0.88,max(0.0,edge-a)*0.85);
}"""
	var mat=ShaderMaterial.new()
	mat.shader=shader
	material=mat
func sync():
	position=source.position
	if not visible: return
	var avatar=source.avatar
	avatar.refresh_entries()
	var frame=avatar.pose_frame()
	var key=str(avatar.outfit)+avatar.action+str(frame)+str(avatar.facing)+str(avatar.hide_bow_arrow)
	if not poses.has(key):
		var composite=Image.create(512,512,false,Image.FORMAT_RGBA8)
		for entry in avatar.entries:
			if avatar.hide_bow_arrow and avatar.action=="bow" and entry.held_arrow: continue
			var tex: Texture2D=entry.texture
			var path=tex.resource_path
			if not sheets.has(path): sheets[path]=tex.get_image()
			var cell=int(entry.cell)
			var frames=maxi(1,tex.get_width()/cell)
			var row=0 if avatar.facing<0 else 1
			var offset=int((cell-256)*0.5)
			composite.blend_rect(sheets[path],Rect2i((frame%frames)*cell,row*cell,cell,cell),Vector2i(128-offset,110-offset))
		if poses.size()>96: poses.clear()
		poses[key]=ImageTexture.create_from_image(composite)
	pose=poses[key]
	queue_redraw()
func _draw():
	if pose:
		var bob=-8+sin(source.avatar.elapsed*TAU/2.8)*3 if source.avatar.action=="meditate" else 0.0
		draw_texture(pose,Vector2(-256,-300+bob))
