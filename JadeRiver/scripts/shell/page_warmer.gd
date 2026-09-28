class_name PageWarmer
extends RefCounted
## Page scripts compile on a loading thread from the title screen on, so the first time a page opens it does not stall a
## frame compiling itself (S40 performance: a page opens within 0.15 s). They go one at a time, the next asked for once
## the one before is in (`tick`, each frame). While a script compiles, every other load waits for it (the engine takes
## its loading queue in turn): the fifty page scripts asked for at once held up every sheet a room's people needed for
## seconds after launch, so villagers appeared late while the menus loaded (redesign Phase 4). One at a time, a room's
## art waits at most for the page in hand, and the whole set takes about as long as the burst did.

var queue: Array = []   ## page scripts still to ask for
var current := ""       ## the one compiling now ("" when none)

func _init(paths: Array) -> void:
	queue = paths.map(func(p): return str(p)).filter(func(p): return ResourceLoader.exists(p))

## Ask for the next page script once the one before is in. False when every one has been asked for and is in.
func tick() -> bool:
	if current != "" and ResourceLoader.load_threaded_get_status(current) == ResourceLoader.THREAD_LOAD_IN_PROGRESS: return true
	current = ""
	while not queue.is_empty():
		var p := str(queue.pop_front())
		if ResourceLoader.load_threaded_get_status(p) != ResourceLoader.THREAD_LOAD_INVALID_RESOURCE: continue   # asked for already
		if ResourceLoader.load_threaded_request(p) == OK:
			current = p
			return true
	return false
