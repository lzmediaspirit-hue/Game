extends Node
## The suite base (audit 45, DUP-07; tests/README.md): what every suite scene tools/run_tests.sh runs shares.
##   - `check(ok, what)` counts a check; a failure counts and prints "FAIL: <what>" (`report_failure`), and with
##     --verbose a suite that sets `echo_passes` prints "ok: <what>" for a pass;
##   - `end_suite()` prints the summary line run_tests.sh reads ("<suite>: N checks, M failures", `summary_line`), then
##     quits cleanly: it frees what the suite made (its own children and anything it left under the tree's root), lets
##     the game's worker tasks finish, removes the run's own folder (`run_root`), and exits 1 on a failure, else 0;
##   - the Max Tester guard: a suite never plays the Max Tester's save. It will not start in the Max Test build or with
##     the flags that make or open it (--max-character, --unlock-all); until it picks a save folder of its own, the
##     saves stand in the run's own folder, never the player's (user://, where the Max Tester lives); and it fails if
##     it ends on the player's saves or with the Max Tester loaded.
## A suite extends this script, puts its body in `_main()` (called deferred from `_ready`) and ends with `end_suite()`.

## The flags of main.gd that make or open the Max Tester (the Max Test build has the custom feature "max_test").
const MAX_TESTER_FLAGS := ["--max-character", "--unlock-all"]
## The player's own save folder (RepositoryLocal's default), where the Max Tester lives on a machine that made one.
const PLAYER_SAVES := "user://"

var checks := 0
var failures := 0
## --verbose on the command line (godot ... -- --verbose): suites print more of what they do.
var verbose := false
## With --verbose, print "ok: <what>" for each check that passes (the story walks and the tutorials set it).
var echo_passes := false
var _root_before: Array = []   # the tree root's children when the suite started: anything else there it made

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		report_failure(what)
	elif echo_passes and verbose:
		print("ok: ", what)

## How a failed check is told (engine_tests pushes an error instead).
func report_failure(what: String) -> void:
	print("FAIL: ", what)

## The line run_tests.sh reads for the suite's count.
func summary_line() -> String:
	return "%s: %d checks, %d failures" % [suite_name(), checks, failures]

## The suite's name: its script's file name (a suite that extends another reports under its own).
func suite_name() -> String:
	return str(get_script().resource_path).get_file().get_basename()

func _ready() -> void:
	verbose = "--verbose" in OS.get_cmdline_user_args()
	var why := _max_tester_at_start()
	if why != "":
		print("FAIL: the Max Tester guard: ", why)
		get_tree().quit(2)
		return
	Saves.use_folder(run_root() + "boot/")
	_root_before = get_tree().root.get_children()
	call_deferred("_main")

## The suite's body (each suite overrides it and ends with end_suite()).
func _main() -> void:
	end_suite()

## Print the summary and quit cleanly with the result (1 on a failure, or when the Max Tester guard trips, else 0).
func end_suite() -> void:
	print(summary_line())
	var why := _max_tester_at_end()
	if why != "": print("FAIL: the Max Tester guard: ", why)
	await _tear_down()
	get_tree().quit(1 if failures > 0 or why != "" else 0)

## Quit cleanly with `code` and no summary (a suite that cannot run, such as valley_run with no checkpoint to resume).
func stop(code: int) -> void:
	await _tear_down()
	get_tree().quit(code)

# ------------------------------------------------------------------ the run's own folder
## This run's own folder under user:// (other runs of a suite, in other checkouts too, share user://).
func run_root() -> String:
	return "user://test_runs/%s_%d/" % [suite_name(), OS.get_process_id()]

func _remove_tree(dir: String) -> void:
	if not DirAccess.dir_exists_absolute(dir): return
	for d in DirAccess.get_directories_at(dir): _remove_tree(dir + d + "/")
	for f in DirAccess.get_files_at(dir): DirAccess.remove_absolute(dir + f)
	DirAccess.remove_absolute(dir)

# ------------------------------------------------------------------ timing on a shared machine
## A suite that times the game's own work (perf_tests; rules_tests' technique pictures, preview and living world; the
## coach's cost in tutorials) reads the game's own clock, and may ask for its share of a CPU while it times: the test
## machine is shared, and other processes hold its CPUs for seconds at a time (perf_tests, "measuring on a shared
## machine", has the numbers).
const SCHEDSTAT := "/proc/thread-self/schedstat"
const MAIN_NICE := -10
var _schedstat := -1   # 1 where the system counts the run queue per thread, 0 where not, -1 before it is asked

## µs on the game's own clock: the wall clock less the time the main thread stood in the run queue, ready to run while
## other processes held every CPU (Linux counts it per thread; elsewhere this is the wall clock).
func now_us() -> int:
	return Time.get_ticks_usec() - queued_us()

## µs the main thread has stood in the run queue since it started (0 where the system does not count it). The file is
## read afresh each time: a kept one does not move on.
func queued_us() -> int:
	if _schedstat < 0: _schedstat = 1 if FileAccess.file_exists(SCHEDSTAT) else 0
	if _schedstat == 0: return 0
	var f := FileAccess.open(SCHEDSTAT, FileAccess.READ)
	if f == null: return 0
	var parts := f.get_line().split(" ")
	return int(parts[1]) / 1000 if parts.size() >= 2 else 0

## What `now_us` leaves out, for a suite's report.
func clock_name() -> String:
	return "the run queue left out" if queued_us() > 0 or _schedstat == 1 else "the wall clock"

## The main thread asks the system for a larger share of a CPU while the suite times: on Linux, where it may (as root,
## or with CAP_SYS_NICE), its own thread's niceness goes to MAIN_NICE (renice -p on the process id names the main thread
## alone). With five times as many busy threads as CPUs the main thread ran a tenth of the time, in short slices each
## begun with caches other processes had filled, and its own work took twice as long on the CPU: no clock takes that
## out. Elsewhere, or where it may not, nothing changes. Returns what it did, for the suite's report.
func ask_for_cpu() -> String:
	if not OS.has_feature("linux"): return "the usual share of a CPU"
	if OS.execute("renice", ["-n", str(MAIN_NICE), "-p", str(OS.get_process_id())], [], true) == 0:
		return "the main thread at niceness %d" % MAIN_NICE
	return "the usual share of a CPU (renice refused)"

## Back to the usual share once the timing is done.
func usual_cpu() -> void:
	if OS.has_feature("linux"): OS.execute("renice", ["-n", "0", "-p", str(OS.get_process_id())], [], true)

# ------------------------------------------------------------------ the clean quit
## Free what the suite made and let the game's workers finish before the engine quits: a worker task left unclaimed
## kept its function past its script's end, and the engine crashed as it quit (a clean summary, then signal 6 or 11).
func _tear_down() -> void:
	for n in get_children(): n.queue_free()
	for n in get_tree().root.get_children():
		if n != self and not n in _root_before: n.queue_free()
	# Freed at the end of this frame; their exits (a page's preview claims its reading, the pictures' host waits for
	# its painters) run then.
	await get_tree().process_frame
	await get_tree().process_frame
	TechniquePreview.TopFoe.settle()
	TechniquePicture._release()
	_remove_tree(run_root())

# ------------------------------------------------------------------ the Max Tester guard
func _max_tester_at_start() -> String:
	if OS.has_feature("max_test"): return "this is the Max Test build"
	for flag in MAX_TESTER_FLAGS:
		if flag in OS.get_cmdline_user_args(): return "run with %s" % flag
	return ""

func _max_tester_at_end() -> String:
	if Saves.repo.root == PLAYER_SAVES: return "the suite ended on the player's own saves (%s)" % PLAYER_SAVES
	var name := Tx.t("main.max_tester")
	for id in Game.characters:
		if str(Game.characters[id].name) == name: return "the Max Tester (%s) was loaded" % id
	return ""
