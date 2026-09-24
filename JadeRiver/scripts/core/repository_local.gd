class_name RepositoryLocal
extends RefCounted
## Local JSON repository (Part 2 · Persistence). Every write goes to a temp file,
## the previous file is kept as `.bak`, then the temp file replaces it. A server
## repository with the same four functions replaces this at v2.0.

var root := "user://"
var last_recovered: Array = []   # files restored from .bak (the shell tells the player)

func _init(folder := "user://") -> void:
	root = folder

func account_path() -> String: return root + "account.json"
func character_path(slot: int) -> String: return root + "char_%d.json" % slot

func read(path: String) -> Dictionary:
	var data := _read_one(path)
	if data.is_empty() and FileAccess.file_exists(path + ".bak"):
		data = _read_one(path + ".bak")
		if not data.is_empty(): last_recovered.append(path.get_file())
	return data

func _read_one(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): return {}
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path)) != OK: return {}
	return parser.data if parser.data is Dictionary and parser.data.has("version") else {}

func write(path: String, data: Dictionary) -> Error:
	DirAccess.make_dir_recursive_absolute(root)
	var tmp := path + ".tmp"
	var file := FileAccess.open(tmp, FileAccess.WRITE)
	if file == null: return FileAccess.get_open_error()
	file.store_string(JSON.stringify(data, "\t"))
	file.flush()
	var err := file.get_error()
	file.close()
	if err != OK: return err
	if not _read_one(path).is_empty():
		err = DirAccess.copy_absolute(path, path + ".bak")
		if err != OK: return err
	return DirAccess.rename_absolute(tmp, path)

func load_account() -> Dictionary: return read(account_path())
func save_account(data: Dictionary) -> Error: return write(account_path(), data)
func load_character(slot: int) -> Dictionary: return read(character_path(slot))
func save_character(slot: int, data: Dictionary) -> Error: return write(character_path(slot), data)

func delete_character(slot: int) -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(character_path(slot) + suffix): DirAccess.remove_absolute(character_path(slot) + suffix)

func wipe() -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(account_path() + suffix): DirAccess.remove_absolute(account_path() + suffix)
	for slot in range(1, 13): delete_character(slot)
