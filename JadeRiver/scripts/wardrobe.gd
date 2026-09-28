extends Node
## Version 2 stores appearance and per-slot world progress; version 1 migrates on read.
var parts: Dictionary={}
var slots: Array=[null,null,null]
var textures: Dictionary={}
var save_path="user://disciples.json"
const CATEGORIES=["hair","shirt","pants","shoes","weapon","hat","cape"]
func _ready():
	parts=JSON.parse_string(FileAccess.get_file_as_string("res://data/parts.json"))
	load_slots()
func defaults() -> Dictionary:
	return {"name":"New Disciple","body":"light","hair":"topknot","hair_color":0,"shirt":"cardigan","pants":"loose","shoes":"boots","weapon":"sword","sect":"Jade"}
func validate(value: Dictionary) -> Dictionary:
	var result=defaults()
	for key in result:
		match key:
			"name": result[key]=str(value.get(key,result[key])).strip_edges().left(24)
			"hair_color": result[key]=clampi(int(value.get(key,0)),0,5) if value.get(key,0) is float or value.get(key,0) is int else 0
			"sect": result[key]=value.get(key,"Jade") if value.get(key) in ["Jade","Cloud"] else "Jade"
			_:
				if parts.get(key,{}).has(value.get(key,"")): result[key]=value[key]
	if result.name.is_empty(): result.name="New Disciple"
	if value.get("progress") is Dictionary:
		var state=value.progress
		var clean: Dictionary={}
		for key in ["x","y","hp","qi","facing","skill_page","map_revision","map_seed","generator_version"]:
			var n=state.get(key)
			if (n is float or n is int) and is_finite(float(n)): clean[key]=n
		clean.surface=str(state.get("surface",""))
		clean.map_theme=str(state.get("map_theme",""))
		result.progress=clean
	return result
func read_save(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): return {}
	var parser=JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path))!=OK: return {}
	var data=parser.data
	if data is Dictionary and (data.get("version")==1 or data.get("version")==2) and data.get("slots") is Array: return data
	return {}
func load_slots():
	var data=read_save(save_path)
	if data.is_empty(): data=read_save(save_path+".bak")
	if data.is_empty(): return
	slots=[null,null,null]
	for i in mini(3,data.slots.size()):
		if data.slots[i] is Dictionary: slots[i]=validate(data.slots[i])
func texture(path: String) -> Texture2D:
	path=path.replace("art_v12/","res://art/")
	if not textures.has(path): textures[path]=load(path)
	return textures[path]
## A sheet loaded on a loading thread: null while it loads (asked for on the first call), then the sheet.
func texture_async(path: String) -> Texture2D:
	path=path.replace("art_v12/","res://art/")
	if textures.has(path): return textures[path]
	match ResourceLoader.load_threaded_get_status(path):
		ResourceLoader.THREAD_LOAD_LOADED:
			textures[path]=ResourceLoader.load_threaded_get(path)
			return textures[path]
		ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			if not ResourceLoader.exists(path) or ResourceLoader.load_threaded_request(path)!=OK: return texture(path)
		ResourceLoader.THREAD_LOAD_FAILED: return texture(path)
	return null
func attack_for(outfit: Dictionary) -> String:
	return parts._attack_by_weapon.get(outfit.get("weapon","none"),"punch")
