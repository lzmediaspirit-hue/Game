extends Node
## Event contract (Part 7 · Quality gates): every event in the Part 4 catalogue
## (data/event_contract.json, built by tools/data/contract.py) is emitted only by
## the scripts of its system, and something reacts to it — a subscriber, a HUD or
## page handler, an achievement or quest rule — unless the contract says the
## reactor reads state every frame instead. Strings: no player-facing text is
## written in the player-facing scripts; it comes from data/strings via Tx.t(key).
## Forbidden patterns: gameplay code takes randomness from named Rng streams and
## time from Clock.
## Run headless:  godot --headless --path . res://tests/contract_tests.tscn

var checks := 0
var failures := 0
var sources: Dictionary = {}   # script name (no extension) -> Array of lines

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	_read_scripts("res://scripts/")
	var contract: Dictionary = ContentDB.config("event_contract").get("events", {})
	check(contract.size() >= 100, "the contract lists the catalogue (%d events)" % contract.size())
	var data_text := _data_text()
	var emit_re := RegEx.create_from_string("\\bemit(_event)?\\(")
	for ev in contract:
		var row: Dictionary = contract[ev]
		var owners: Array = row.get("files", [])
		var q := "\"%s\"" % ev
		var owned := false
		var foreign: Array = []
		var consumed := false
		for name in sources:
			var mine: bool = name in owners
			var lines: Array = sources[name]
			for i in lines.size():
				var line: String = lines[i]
				if not line.contains(q): continue
				var emits := emit_re.search(line) != null
				if mine: owned = true
				if emits and not mine: foreign.append("%s:%d" % [name, i + 1])
				# An owner choosing between event names (`x := "a" if … else "b"`) is not a reaction.
				if not emits and not (mine and line.contains(" if ") and line.contains(":=")): consumed = true
		check(owned, "%s is emitted by %s (%s)" % [ev, row.get("system", "?"), ", ".join(owners)])
		check(foreign.is_empty(), "%s is emitted only by %s, not %s" % [ev, row.get("system", "?"), ", ".join(foreign)])
		var by_data := data_text.contains("\"event\": " + q)
		check(consumed or by_data or row.has("polled"), "%s has a reactor" % ev)
	_declared_payloads(contract)
	_fx_kinds()
	_moments_read_only()
	_strings_gate()
	_format_words_gate()
	_durations_and_plurals()
	_forbidden_patterns()
	_pages_read_only()
	_scripts_compile()
	_export_filters()
	_version_one_place()
	_controls_line()
	print("contract_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

## P4 (docs/ui_style_guide.md §4): durations are written in one style, by Tx.span (UiKit.span on the pages): no string
## but the span's own keys and the countdown clock's prints a count straight before a unit of time, except a few that
## state a rule's fixed length in prose. And every string that prints a count before a countable noun has its "_one"
## twin (Tx.plural), or is a count of a total ("%d of %d fights left"), where the noun is the total's.
const DURATION_PROSE := ["hud.beast_tide_started_sub", "hud.route_hint", "ui.tower.rule_clear", "ui.tower.rule_guardian",
	"ui.tower.rule_survive", "ui.tower.rule_swift", "ui.cultivation.choose_what_to_cultivate_while", "ui.codex.ripens"]
const COUNT_OF_TOTAL := ["hud.route_finished", "hud.tribulation_survived", "sim.sect.mine_yours_line", "ui.arena.fights_left", "moment.tribulation.struck",
	"ui.codex.of_entries_discovered", "ui.crafts.pages_held", "ui.guild.cap_line", "ui.guqin.playing", "ui.pets.swarm_pop",
	"ui.quest.activity_points", "ui.settings.characters_slots", "ui.your_sect.mine_yours",
	# Not a noun after the count ("%d answers it", "%d merit eases"), and a list of three counts in one line.
	"hud.hazard", "ui.cultivation.merit_not_ready", "hud.pets_fused_sub"]

func _durations_and_plurals() -> void:
	var unit := RegEx.create_from_string("%[0-9]*d\\s*(more\\s+)?(s|m|h|d|min|mins|minutes?|hours?|days?|seconds?)\\b")
	var counted := RegEx.create_from_string("%d\\s+(?:[A-Za-z\\-]+\\s+){0,2}([A-Za-z][a-z]+s)\\b")
	var own: Array = []
	var single: Array = []
	for key in ContentDB.strings:
		var k := str(key)
		var v := str(ContentDB.strings[key])
		if unit.search(v) != null and not k.begins_with("ui.span_") and k != "ui.clock_days" and not k in DURATION_PROSE and not k.trim_suffix("_one") in DURATION_PROSE:
			own.append(k)
		if not k.ends_with("_one") and counted.search(v) != null and not ContentDB.strings.has(k + "_one") and not k in COUNT_OF_TOTAL:
			single.append(k)
	check(own.is_empty(), "P4: every duration is written by the span, none in a string of its own (%d: %s)" % [own.size(), str(own.slice(0, 8))])
	check(single.is_empty(), "P4: every counted plural has its _one twin, or counts a total (%d: %s)" % [single.size(), str(single.slice(0, 8))])
	check(Tx.span(90) == Tx.t("ui.span_m") % 2 and Tx.span(7200) == Tx.t("ui.span_h") % 2 and Tx.span(3 * 86400) == Tx.t("ui.span_d") % 3
		and Tx.span(3 * 86400 + 7200) == Tx.t("ui.span_dh") % [3, 2] and UiKit.span(45) == Tx.span(45), "P4: Tx.span writes a whole hour or day without its zero")
	check(UiKit.short(9999) == "9,999" and UiKit.short(18234) == "18.2K" and UiKit.short(123456) == "123K" and UiKit.short(999960) == "1.00M"
		and UiKit.short(1250000) == "1.25M" and UiKit.short(-18234) == "-18.2K" and UiKit.is_numeric("18.2K"), "P4: numbers over the world shorten to three figures from 10,000")

func _read_scripts(dir: String) -> void:
	for sub in DirAccess.get_directories_at(dir): _read_scripts(dir + sub + "/")
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".gd"):
			sources[f.get_basename()] = FileAccess.get_file_as_string(dir + f).split("\n")

## P6: every emit site of an event whose payload the contract declares names each declared key in its dict literal
## (the emit line and its continuation lines); a key ending in "?" is optional.
func _declared_payloads(contract: Dictionary) -> void:
	var missing: Array = []
	var sites := 0
	for ev in contract:
		var keys: Array = contract[ev].get("payload", [])
		if keys.is_empty(): continue
		var call := RegEx.create_from_string("\\bemit(_event)?\\(\"%s\"" % ev)
		for name in sources:
			var lines: Array = sources[name]
			for i in lines.size():
				if call.search(lines[i]) == null: continue
				sites += 1
				var body := ""
				var depth := 0
				for j in range(i, mini(i + 8, lines.size())):
					body += str(lines[j])
					depth += str(lines[j]).count("(") - str(lines[j]).count(")")
					if depth <= 0: break
				for k in keys:
					if not str(k).ends_with("?") and not body.contains("\"%s\":" % k): missing.append("%s:%d %s.%s" % [name, i + 1, ev, k])
	check(sites >= 25 and missing.is_empty(), "every emit site names its event's declared payload keys (%d sites) %s" % [sites, str(missing)])

## P6: FxLayer.KINDS and the arms of fx_layer.gd's _draw match list the same kinds (moments.json names only KINDS).
func _fx_kinds() -> void:
	var arms: Array = []
	var in_draw := false
	var arm := RegEx.create_from_string("^\\t{3}\"([a-z_]+)\":")
	for line in sources.get("fx_layer", []):
		if str(line).begins_with("func "): in_draw = str(line).begins_with("func _draw()")
		var m := arm.search(str(line)) if in_draw else null
		if m: arms.append(m.get_string(1))
	arms.sort()
	var kinds: Array = FxLayer.KINDS.duplicate()
	kinds.sort()
	check(arms == kinds, "FxLayer.KINDS lists every kind _draw draws (%s against %s)" % [str(kinds), str(arms)])

## P6 presentation only: the moments scripts call nothing that changes the simulation and assign to no Game member.
func _moments_read_only() -> void:
	var bad := RegEx.create_from_string("Game\\.submit\\(|\\bemit\\(|emit_event\\(|GameEvents\\.subscribe\\(|\\.apply_\\w+\\(|\\bRng\\.|\\bClock\\.|\\bGame\\.[\\w.\\[\\]\"]*\\s*[-+*/]?=(?!=)")
	var found: Array = []
	for name in ["moment_view", "moment_rules"]:
		var lines: Array = sources.get(name, [])
		check(not lines.is_empty(), "%s.gd exists" % name)
		for i in lines.size():
			if not str(lines[i]).strip_edges().begins_with("#") and bad.search(str(lines[i])) != null: found.append("%s:%d" % [name, i + 1])
	check(found.is_empty(), "the moments scripts never write game state %s" % str(found))

## Data rules that react to events (achievements, quest objectives) name them as "event": "…".
func _data_text() -> String:
	var out := ""
	for f in DirAccess.get_files_at("res://data/"):
		if f.ends_with(".json") and f != "event_contract.json": out += FileAccess.get_file_as_string("res://data/" + f)
	return out

# ------------------------------------------------------------------ strings (Part 7)
## The same rules as tools/dev/extract_strings.py: a literal that reads like text is not
## allowed in the player-facing scripts unless it is an id, a technical token, a key,
## a comparison, a membership list, a const, a signature default or debug output.
const STRING_SCOPE := ["res://scripts/ui/", "res://scripts/hud.gd", "res://scripts/shell/", "res://scripts/main.gd", "res://scripts/world.gd",
	"res://scripts/player.gd", "res://scripts/presentation/enemy_view.gd", "res://scripts/presentation/loot_view.gd",
	"res://scripts/presentation/portal_view.gd", "res://scripts/presentation/npc_view.gd", "res://scripts/presentation/moment_view.gd",
	"res://scripts/presentation/moment_rules.gd", "res://scripts/presentation/fx_layer.gd", "res://scripts/simulation/authority/",
	"res://scripts/core/requirement_rules.gd", "res://scripts/core/unlock_service.gd"]
const TECH := ["UI", "SFX", "Music", "Ambience", "Master", "MobileHUD", "Room", "HUD"]

func _strings_gate() -> void:
	var lit := RegEx.create_from_string("(?<![&^\\w])\"((?:[^\"\\\\]|\\\\.)*)\"")
	var in_list := RegEx.create_from_string("\\bin\\s*\\[[^\\]]*\\]")
	var skip := RegEx.create_from_string("^\\s*(#|(static\\s+)?func\\s|const\\s)|\\b(print|prints|printerr|push_warning|push_error|assert)\\(")
	var found: Array = []
	for path in _scope_files():
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in lines.size():
			var line: String = lines[i]
			if skip.search(line) != null: continue
			var lists: Array = []
			for m in in_list.search_all(line): lists.append([m.get_start(), m.get_end()])
			for m in lit.search_all(line):
				var s := m.get_string(1)
				if not _reads_as_text(s): continue
				if lists.any(func(r): return m.get_start() >= r[0] and m.get_start() < r[1]): continue
				var after := line.substr(m.get_end()).strip_edges(true, false)
				var before := line.substr(0, m.get_start()).strip_edges(false, true)
				if after.begins_with(":") and not after.begins_with(":="): continue
				if before.ends_with("==") or before.ends_with("!=") or after.begins_with("==") or after.begins_with("!="): continue
				found.append("%s:%d %s" % [path.get_file(), i + 1, s])
	for f in found.slice(0, 20): print("  text in code: ", f)
	check(found.is_empty(), "no player-facing text in the scripts (%d found; move it with tools/dev/extract_strings.py)" % found.size())

## B8: a lone lowercase word reads like an id, so the gate above lets it through. But one chosen as a value inside
## the arguments of a text format is a word the player reads ("ready" if … else …, {"silver_tael": "taels"}[…]), and
## so is a number format with a unit ("%dm").
func _format_words_gate() -> void:
	var lit := RegEx.create_from_string("(?<![&^\\w])\"((?:[^\"\\\\]|\\\\.)*)\"")
	var word := RegEx.create_from_string("^[a-z][a-z0-9_.\\-]*$")
	var unit := RegEx.create_from_string("^%[-+0 #]*\\d*(\\.\\d+)?[dsf] ?[a-z]{1,3}\\.?$")
	var fmt := RegEx.create_from_string("(Tx\\.t\\([^)]*\\)|\"[^\"]*%[^\"]*\")\\s*%\\s*")
	var skip := RegEx.create_from_string("^\\s*(#|(static\\s+)?func\\s|const\\s)|\\b(print|prints|printerr|push_warning|push_error|assert)\\(")
	var found: Array = []
	for path in _scope_files():
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in lines.size():
			var line: String = lines[i]
			if skip.search(line) != null: continue
			# The arguments of each format whose pattern is text (a Tx string, or a literal with a space or a word).
			var spans: Array = []
			for fm in fmt.search_all(line):
				var pattern := fm.get_string(1)
				if pattern.begins_with("\"") and not (pattern.contains(" ") or _reads_as_text(pattern.substr(1, pattern.length() - 2))): continue
				spans.append([fm.get_end(), _operand_end(line, fm.get_end())])
			for m in lit.search_all(line):
				var s := m.get_string(1)
				if unit.search(s) != null:
					found.append("%s:%d %s" % [path.get_file(), i + 1, s])
					continue
				if word.search(s) == null or not spans.any(func(sp): return m.get_start() >= sp[0] and m.get_start() < sp[1]): continue
				var after := line.substr(m.get_end()).strip_edges(true, false)
				var before := line.substr(0, m.get_start()).strip_edges(false, true)
				if after.begins_with("if ") or before.ends_with("else") or before.ends_with(":"): found.append("%s:%d %s" % [path.get_file(), i + 1, s])
	for f in found.slice(0, 20): print("  word in a text format: ", f)
	check(found.is_empty(), "B8: no word the player reads is picked in code inside a text format (%d found)" % found.size())

## Where the operand starting at `i` ends: a bracketed group with its [..] or .name(..) chain, or a term up to a comma.
func _operand_end(line: String, i: int) -> int:
	var depth := 0
	var in_str := false
	var j := i
	while j < line.length():
		var ch := line[j]
		if in_str:
			if ch == "\\":
				j += 2
				continue
			if ch == "\"": in_str = false
		elif ch == "\"": in_str = true
		elif ch in ["(", "[", "{"]: depth += 1
		elif ch in [")", "]", "}"]:
			if depth == 0: return j
			depth -= 1
			if depth == 0 and (j + 1 >= line.length() or not line[j + 1] in ["[", "."]): return j + 1
		elif ch == "," and depth == 0: return j
		j += 1
	return j

func _reads_as_text(s: String) -> bool:
	var raw := s.replace("\\n", "\n").replace("\\\"", "\"")
	if raw.strip_edges() in TECH or raw.strip_edges() == "": return false
	if raw.begins_with("res:") or raw.begins_with("user:") or raw.begins_with("--") or raw.begins_with("#"): return false
	if raw.contains("/") and not raw.contains(" "): return false
	if RegEx.create_from_string("^[a-z0-9_.:%\\-]+$").search(raw) != null: return false
	if RegEx.create_from_string("[A-Za-z]{2,}").search(raw) == null: return false
	return raw.strip_edges().contains(" ") or RegEx.create_from_string("^[A-Z]").search(raw.strip_edges()) != null

func _scope_files() -> Array:
	var out: Array = []
	for p in STRING_SCOPE:
		if str(p).ends_with("/"):
			for sub in _walk(str(p)): out.append(sub)
		else:
			out.append(p)
	return out

func _walk(dir: String) -> Array:
	var out: Array = []
	for sub in DirAccess.get_directories_at(dir): out.append_array(_walk(dir + sub + "/"))
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".gd"): out.append(dir + f)
	return out

# ------------------------------------------------------------------ forbidden patterns (Part 7)
## Seeded generators that are allowed: the stream service itself, the map layout (seeded by the
## room's map seed), the daily shop rotation (seeded by day and account seed) and the enemy
## authority's placeholder, which is swapped for the character's "world" stream on room entry.
const RNG_OK := ["rng_service.gd", "map_generator.gd", "economy_authority.gd", "enemy_authority.gd"]

func _forbidden_patterns() -> void:
	var raw_rng := RegEx.create_from_string("(?<![.\\w])(randi|randf|randf_range|randi_range|randfn)\\(|RandomNumberGenerator\\.new\\(")
	var clock := RegEx.create_from_string("\\bTime\\.get_|\\bOS\\.get_(unix|ticks|datetime|date|time)")
	var bad_rng: Array = []
	var bad_clock: Array = []
	for path in _walk("res://scripts/simulation/") + _walk("res://scripts/core/"):
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in lines.size():
			var line: String = lines[i]
			if line.strip_edges().begins_with("#"): continue
			if raw_rng.search(line) != null and not path.get_file() in RNG_OK: bad_rng.append("%s:%d" % [path.get_file(), i + 1])
			if clock.search(line) != null and path.get_file() != "clock_service.gd": bad_clock.append("%s:%d" % [path.get_file(), i + 1])
	check(bad_rng.is_empty(), "gameplay randomness comes from named Rng streams %s" % str(bad_rng))
	check(bad_clock.is_empty(), "gameplay time comes from Clock %s" % str(bad_clock))

# ------------------------------------------------------------------ pages draw, authorities write (page.gd)
## The pages, the HUD and the shell send intents: they never write a character's or the account's state, call an
## authority's apply_* command, settle a record or fill one in. A write found here belongs in its authority, behind an intent.
func _pages_read_only() -> void:
	var state := "\\.(inventory|cultivator|pools|quests|relations|crafting|posts|pets|companions|cooldowns|training_sect|professions|swarm|tower|rooms)\\b"
	var write := "[\\w.\\[\\]\"]*\\s*([-+*/]?=(?!=)|\\.(append|erase|clear|merge|push_back|push_front|remove_at|pop_back|pop_front|resize|sort)\\()"
	var re := RegEx.create_from_string("(" + state + write + ")|(Game\\.account" + write + ")|(Game\\.[a-z_]+\\.(apply_\\w+|\\w*settle\\w*|ensure_fields)\\()")
	var found: Array = []
	for path in _walk("res://scripts/ui/") + ["res://scripts/hud.gd"] + _walk("res://scripts/shell/"):
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in lines.size():
			if lines[i].strip_edges().begins_with("#"): continue
			if re.search(lines[i]) != null: found.append("%s:%d" % [path.get_file(), i + 1])
	check(found.is_empty(), "pages, the HUD and the shell never write game state %s" % str(found))

## Every script under scripts/ parses and compiles (a page with a type error only fails when
## the player opens it, so load them all here).
func _scripts_compile() -> void:
	var broken: Array = []
	for path in _walk("res://scripts/"):
		if not str(path).ends_with(".gd"): continue
		var sc = load(str(path))
		if sc == null or not (sc as GDScript).can_instantiate(): broken.append(str(path))
	check(broken.is_empty(), "every script compiles %s" % str(broken))

## B23: Settings > Controls names every letter key the HUD answers in play, and no hold that the keyboard does not do
## (it promised "C … hold for the Cultivation page" and left out E, P, V, G, H, O and R).
func _controls_line() -> void:
	var line := Tx.t("ui.settings.keyboard_arrows_wasd_move_space")
	var src := FileAccess.get_file_as_string("res://scripts/hud.gd").split("\n")
	var start := -1
	for i in src.size():
		if src[i].contains("var kc: int = event.physical_keycode"): start = i
	var keys := {}
	var branch := RegEx.create_from_string("^\\t+(KEY_[A-Z](, KEY_[A-Z])*):")
	for i in range(start + 1, src.size()):
		if src[i].begins_with("func "): break
		var m := branch.search(src[i])
		if m:
			for k in m.get_string(1).split(","): keys[k.strip_edges().trim_prefix("KEY_")] = true
	var missing: Array = keys.keys().filter(func(k): return RegEx.create_from_string("(^|[ ·(])%s( |\u00a0|$)" % k).search(line) == null)
	check(start >= 0 and keys.size() >= 15 and missing.is_empty() and not line.contains("hold for"), "the controls line names every key the HUD answers (missing %s)" % str(missing))

## B9: the version lives in one place, project.godot's application/config/version: the title screen reads it, every
## export preset leaves version/name empty so the build takes it too, and no string spells a version (the title said
## "v1.0" on the 1.2 build).
func _version_one_place() -> void:
	var v := str(ProjectSettings.get_setting("application/config/version", ""))
	check(RegEx.create_from_string("^\\d+\\.\\d+").search(v) != null, "project.godot names the version (%s)" % v)
	var cfg := ConfigFile.new()
	var named: Array = []
	if cfg.load("res://export_presets.cfg") == OK:
		for sec in cfg.get_sections():
			if cfg.has_section_key(sec, "version/name") and str(cfg.get_value(sec, "version/name", "")) != "": named.append(sec)
	check(named.is_empty(), "every export preset takes its version name from project.godot %s" % str(named))
	var spelled: Array = []
	var ver := RegEx.create_from_string("\\bv\\d+\\.\\d+")
	for key in ContentDB.strings:
		if ver.search(str(ContentDB.strings[key])) != null: spelled.append(key)
	check(spelled.is_empty(), "no string spells a version %s" % str(spelled))

## No export preset leaves out a file the scripts load: an excluded resource ships only as a missing
## path, and every draw that needs it fails on the phone (Pixelify Sans was left out this way until 1.0.2).
func _export_filters() -> void:
	var cfg := ConfigFile.new()
	if cfg.load("res://export_presets.cfg") != OK:
		check(false, "export_presets.cfg reads")
		return
	var path_re := RegEx.create_from_string("\"res://([^\"]+)\"")
	var used := {}
	for path in _walk("res://scripts/"):
		for m in path_re.search_all(FileAccess.get_file_as_string(path)): used[m.get_string(1)] = true
	var lost: Array = []
	for sec in cfg.get_sections():
		if not cfg.has_section_key(sec, "exclude_filter"): continue
		for pat in str(cfg.get_value(sec, "exclude_filter", "")).split(",", false):
			for u in used:
				if str(u).matchn(pat.strip_edges()) and FileAccess.file_exists("res://" + str(u)): lost.append("%s: %s" % [cfg.get_value(sec, "name", sec), u])
	check(lost.is_empty(), "no export preset leaves out a file the scripts load %s" % str(lost))
