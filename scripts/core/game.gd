# Autoload "Game": owns the save, the active disciple and the single command boundary.
extends Node

const S = preload("res://scripts/core/state.gd")
const R = preload("res://scripts/core/rules.gd")

signal changed(action: String, result: Dictionary)
signal failed(action: String, err: String)
signal event(kind: String, data: Dictionary)

var save_path := "user://jaderiver_save.json"
var save: Dictionary = {}
var slot := -1
var notice := ""
var read_only := false
var rng := RandomNumberGenerator.new()
var clock_override := -1  # tests
var _dirty := false
var _save_timer := 0.0


func _ready() -> void:
	rng.randomize()
	load_save()


func now() -> int:
	return clock_override if clock_override >= 0 else int(Time.get_unix_time_from_system())


var p: Dictionary:
	get:
		return save.slots[slot] if slot >= 0 and save.slots[slot] is Dictionary else {}

var settings: Dictionary:
	get:
		return save.settings


func load_save() -> void:
	notice = ""
	read_only = false
	if not FileAccess.file_exists(save_path):
		save = S.new_save()
		return
	var text := FileAccess.get_file_as_string(save_path)
	var raw = JSON.parse_string(text)
	var res := S.migrate(raw)
	if res.get("future", false):
		save = S.new_save()
		read_only = true
		notice = "This save was made by a newer version of Jade River. It was left untouched; this session will not overwrite it."
	elif res.get("error", false) or not res.has("save"):
		_write(save_path + ".corrupt-%d" % now(), text)
		save = S.new_save()
		notice = "The save could not be read; it was backed up and a new one started."
	else:
		save = res.save
		if res.migrated:
			_write(save_path + ".backup-v%d" % int(raw.get("version", 0)), text)
			notice = "Save migrated from version %d. A backup was kept." % int(raw.get("version", 0))
			save_now()


func create_character(i: int, name: String, hair: String, clothes: String, weapon: String) -> void:
	save.slots[i] = S.new_profile(name, hair, clothes, weapon)
	save_now()


func delete_character(i: int) -> void:
	save.slots[i] = null
	if slot == i:
		slot = -1
	save_now()


func select(i: int) -> void:
	slot = i
	save.last_slot = i
	var s := S.stats(p)
	if int(p.hp) <= 0:
		p.hp = s.max_hp
	if int(p.qi) < 0:
		p.qi = s.max_qi
	save_now()


# The command boundary. Snapshot → run → commit or roll back.
func perform(action: String, args := {}) -> Dictionary:
	if p.is_empty():
		return {"ok": false, "err": "No disciple selected."}
	var snap_p: Dictionary = p.duplicate(true)
	var snap_bank: Dictionary = save.bank.duplicate(true)
	var ctx := {"p": p, "bank": save.bank, "now": now(), "rng": rng, "events": []}
	var res: Dictionary = R.run(action, ctx, args)
	if not res.get("ok", false):
		_restore(p, snap_p)
		_restore(save.bank, snap_bank)
		failed.emit(action, res.get("err", "Nothing happened."))
		return res
	for e in ctx.events:
		event.emit(e[0], e[1])
	changed.emit(action, res)
	_dirty = true
	return res


static func _restore(target: Dictionary, snap: Dictionary) -> void:
	target.clear()
	target.merge(snap)


func _process(delta: float) -> void:
	if _dirty:
		_save_timer += delta
		if _save_timer > 1.0:
			save_now()


func save_now() -> void:
	_dirty = false
	_save_timer = 0.0
	if read_only:
		return
	var tmp := save_path + ".tmp"
	if _write(tmp, JSON.stringify(save)):
		DirAccess.rename_absolute(tmp, save_path)


func _write(path: String, text: String) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(text)
	f.close()
	return true


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_PAUSED:
		if slot >= 0 and _dirty:
			save_now()
