extends SceneTree
## Dev helper: load every script under res://scripts and res://tools so parse errors
## in files the main scene does not reach still surface. Run headless.

var ran := false

func _process(_delta: float) -> bool:
	if ran: return false
	ran = true
	var bad := 0
	for dir in ["res://scripts", "res://tests"]:
		for path in _walk(dir):
			var s = load(path)
			if s == null:
				bad += 1
				print("FAILED ", path)
	print("check_scripts done, failures: ", bad)
	quit(1 if bad > 0 else 0)
	return false

func _walk(dir: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(dir)
	if d == null: return out
	for f in d.get_files():
		if f.ends_with(".gd"): out.append(dir + "/" + f)
	for sub in d.get_directories():
		out += _walk(dir + "/" + sub)
	return out
