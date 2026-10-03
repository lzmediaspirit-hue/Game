extends "res://tools/dev/capture/capture_scripted.gd"
## The capture tool (tools/dev/README.md, "Captures"): the review pictures the game takes of itself, one set a run, from
## the registry in shots.gd. It plays the real game (main.tscn) on saves of its own and needs a renderer:
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . \
##     res://tools/dev/capture/capture.tscn -- <set> [--tag=before|after] [--only=<text>] [--out-root=<dir>] [--<flag>]
## --tag (and any --key=value) fills "{key}" in the set's folder and names; --only takes only the named rows whose name
## holds the text (the rows between still play); --out-root writes the pictures under <dir> instead of docs/ (the
## inputs a set reads, a mock or a before, still come from docs/ when <dir> has none); a bare --<flag> turns on the rows
## gated on it ("if": "detail").
##   godot --headless --path . res://tools/dev/capture/capture.tscn -- --list   the sets, what each is for, its rows
##   godot --headless --path . res://tools/dev/capture/capture.tscn -- --lint   every row's steps known, their arguments
##                                                                              counted (no game is played)

const Shots := preload("res://tools/dev/capture/shots.gd")

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var set_name := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			vars[kv[0]] = kv[1] if kv.size() > 1 else true
		elif set_name == "":
			set_name = a
	var sets: Dictionary = Shots.sets()
	if vars.has("lint"):
		get_tree().quit(lint(sets))
		return
	if vars.has("list") or not sets.has(set_name):
		if set_name != "" and not vars.has("list"): print("capture: no set %s" % set_name)
		for k in sets:
			print("%-18s %3d rows  %s  (docs/%s)" % [k, (sets[k].rows as Array).filter(func(r): return r.has("name")).size(), sets[k].doc, sets[k].out])
		get_tree().quit(0 if vars.has("list") else 1)
		return
	var s: Dictionary = sets[set_name]
	for k in s.get("vars", {}):
		if not vars.has(k): vars[k] = s.vars[k]
	if vars.has("out-root"): docs = str(vars["out-root"]).trim_suffix("/") + "/"
	out_dir = docs + _fill(str(s.out))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out_dir))
	if s.get("clean", false):
		for f in DirAccess.get_files_at(ProjectSettings.globalize_path(out_dir)):
			if f.ends_with(".png"): DirAccess.remove_absolute(ProjectSettings.globalize_path(out_dir) + f)
	var saves := "user://capture_%s/" % set_name
	if s.get("boot", true):
		DirAccess.make_dir_recursive_absolute(saves)
		for f in DirAccess.get_files_at(saves): DirAccess.remove_absolute(saves + f)
	TopdownLight.debug_hour = 0.375   # every set at midday of the game's clock, unless a row names its hour
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	if s.get("boot", true):
		Saves.use_folder(saves)
		Game.boot()
		Game.autosave_enabled = false
	vars["sfx"] = "_phone" if phone() else ""
	for st in s.get("stage", []): await run_step(st)
	for variant in s.get("each", [{}]):
		for k in variant: vars[k] = variant[k]
		for r in s.rows: await run_row(r, s)
	print("capture: %s done, %s" % [set_name, ProjectSettings.globalize_path(out_dir)])
	get_tree().quit()

## One row: its gate, its hour, the room and the spot, the foes and their fight, its steps, its pictures, its after.
func run_row(r: Dictionary, s: Dictionary) -> void:
	if r.has("if") and not _gate(str(r["if"])): return
	var named := r.has("name")
	if named and vars.has("only") and not _name(str(r.name)).contains(str(vars.only)): return
	row = r
	if r.has("hour"): s_hour(float(r.hour))
	if r.has("room"):
		await s_load(str(r.room), ((r.cell as Vector2) + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		await frames(10)
	if r.has("cell"): await s_spot(_fill(r.cell), int(r.get("wait", s.get("wait", 120))))
	if not (r.get("foes", []) as Array).is_empty():
		s_foes(r.cell, r.foes, bool(r.get("turned", false)))
		var fight = r.get("fight", null)
		if fight == null: await frames(20)
		elif fight is Array and not fight[1]: await s_tick(int(fight[0]))
		else: await s_fight(int(fight[0] if fight is Array else fight))
	for st in r.get("do", []): await run_step(st)
	if named:
		for st in r.get("take", s.get("take", [["shot"]])): await run_step(st)
	for st in r.get("then", []): await run_step(st)

## A row's gate: a flag of the command line ("detail"), "key=value" of its variables, "phone" (a window wider than the
## 1280 x 720 canvas), each negated by a leading "!".
func _gate(g: String) -> bool:
	if g.begins_with("!"): return not _gate(g.substr(1))
	if g == "phone": return phone()
	if "=" in g:
		var kv := g.split("=", true, 1)
		return str(vars.get(kv[0], "")) == kv[1]
	return vars.has(g)

## Every step of every set known, with a count of arguments its function takes; the number of problems as the exit code.
func lint(sets: Dictionary) -> int:
	var arity := {}
	for md in get_method_list():
		if str(md.name).begins_with("s_"): arity[str(md.name).substr(2)] = [(md.args as Array).size() - (md.default_args as Array).size(), (md.args as Array).size()]
	var bad := 0
	var n := 0
	for k in sets:
		var s: Dictionary = sets[k]
		for key in ["doc", "out", "rows"]:
			if not s.has(key):
				print("capture lint: %s has no %s" % [k, key])
				bad += 1
		var lists: Array = [["stage", s.get("stage", [])], ["take", s.get("take", [])]]
		for r in s.get("rows", []):
			n += 1
			for key in r:
				if not key in ["name", "if", "hour", "room", "cell", "wait", "foes", "turned", "fight", "do", "take", "then"]:
					print("capture lint: %s %s: no row key %s" % [k, r.get("name", "(steps)"), key])
					bad += 1
			if r.has("room") and not r.has("cell"):
				print("capture lint: %s %s: a room with no cell" % [k, r.get("name", "")])
				bad += 1
			for key in ["do", "take", "then"]: lists.append([str(r.get("name", "(steps)")) + " " + key, r.get(key, [])])
		for pair in lists:
			for st in pair[1]:
				var name := str(st[0])
				var got: int = (st as Array).size() - 1
				if not arity.has(name):
					print("capture lint: %s %s: no step %s" % [k, pair[0], name])
					bad += 1
				elif got < int(arity[name][0]) or got > int(arity[name][1]):
					print("capture lint: %s %s: %s takes %d to %d arguments, given %d" % [k, pair[0], name, arity[name][0], arity[name][1], got])
					bad += 1
				# The steps a timeline plays on its frames.
				if name == "timeline" and got >= 2:
					for f in st[2]:
						for sub in st[2][f]:
							if not arity.has(str(sub[0])):
								print("capture lint: %s %s: no step %s in a timeline" % [k, pair[0], str(sub[0])])
								bad += 1
	print("capture lint: %d sets, %d rows, %d steps known, %d problems" % [sets.size(), n, arity.size(), bad])
	return 1 if bad > 0 else 0
