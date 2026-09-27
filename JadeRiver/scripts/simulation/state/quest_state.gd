class_name QuestState
extends RefCounted
## S19 · Quests, story flags and dialogue state of one character. Objectives
## advance only from events, through the Quest authority.

var active: Dictionary = {}     # quest id -> {state: active|ready, progress: [int], accepted_tick}
var done: Dictionary = {}       # quest id -> completion count
var tracked: Array = []         # up to 3 quest ids
var flags: Dictionary = {}      # flag -> true
var offered: Dictionary = {}    # quest id -> true (visible "!" markers)
var daily: Dictionary = {}      # generated daily missions {id: def}
var board_day := -1             # the reset day the sect board last filled (missed days bank: QuestAuthority.start_daily)

func is_done(id: String) -> bool:
	return done.has(id)

func is_active(id: String) -> bool:
	return active.has(id)

func has_flag(flag: String) -> bool:
	return flags.has(flag)

func snapshot() -> Dictionary:
	return {"active": active.duplicate(true), "done": done.duplicate(), "tracked": tracked.duplicate(),
		"flags": flags.keys(), "offered": offered.keys(), "daily": daily.duplicate(true), "board_day": board_day}

func restore(d: Dictionary) -> void:
	active = {}
	for q in d.get("active", {}):
		if ContentDB.has_entry("quests", q) or d.active[q].has("def"):
			active[q] = d.active[q].duplicate(true)
	done = {}
	var dv = d.get("done", {})
	if dv is Array:
		for q in dv: done[q] = 1
	elif dv is Dictionary:
		done = dv.duplicate()
	tracked = []
	for q in d.get("tracked", []):
		if active.has(q) and tracked.size() < 3: tracked.append(q)
	flags.clear()
	for f in d.get("flags", []): flags[str(f)] = true
	offered.clear()
	for q in d.get("offered", []): offered[str(q)] = true
	daily = d.get("daily", {}).duplicate(true)
	board_day = int(d.get("board_day", -1))
