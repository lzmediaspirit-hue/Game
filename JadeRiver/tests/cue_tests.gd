extends "res://tests/lib/suite.gd"
## Decision 45, phase 2 (E6): the cue table's own checks (data/cues.json, tools/data/cues.py, docs/architecture/cues.md).
##   1. every row against the game: its event is one the game emits (the event contract, or an emit of that name in
##      scripts/), its sounds are in the sound bank, its effects are FxLayer's kinds (or its label and parry), its
##      anchors and handlers are WorldShared's, its colours are UiKit tokens or hex, its string keys exist; no row
##      follows one of its event's rows that holds always;
##   2. Cues' conditions: a key the payload leaves out holds false, 0 or ""; a list is one of its values; "gt"; "@";
##   3. every row played once through WorldShared.play on a stub host, with a payload its `when` holds for: it is the
##      row the table picks, and each of its effects, sounds and shakes happens; an event the table does not answer
##      is left to the view.
##   4. (S6) the HUD's rows (`to: "hud"`): each step a log line with its colour or a toast with one of the HUD's styles;
##      no event both a row and an arm of HudNotices.handle; the HUD's conditions and text sources; every row played
##      once through the HUD's own _on_event: it is the row the table picks, and it writes its lines and toasts.
## Run headless:  godot --headless --path . res://tests/cue_tests.tscn

var main: Node

func _main() -> void:
	var folder := run_root() + "saves/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	Unlocks.debug_force_all = true
	Game.submit({"type": "create_character", "slot": 1, "name": "Cue", "appearance": {"hair": "topknot"}})
	main.enter_world(1)
	for i in 3: await get_tree().process_frame
	_rows()
	_conditions()
	_play_every_row()
	_hud_rows()
	_hud_conditions()
	_play_every_hud_row()
	main.return_to_selection()
	await get_tree().process_frame
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	end_suite()

# ------------------------------------------------------------------ 1. the rows against the game
func _rows() -> void:
	var rows: Array = ContentDB.all("cues")
	check(rows.size() >= 50, "data/cues.json has its rows (%d)" % rows.size())
	var contract: Dictionary = ContentDB.config("event_contract").get("events", {})
	var emitted := _emitted()
	var bad := {"event": [], "sound": [], "fx": [], "at": [], "call": [], "color": [], "key": [], "to": [], "order": []}
	var called := {}
	var open := {}
	for r in rows:
		var id := str(r.get("id", "?"))
		var ev := str(r.get("event", ""))
		if not str(r.get("to", "")) in ["world", "hud"]: bad.to.append(id)
		if not contract.has(ev) and not emitted.has(ev): bad.event.append("%s (%s)" % [id, ev])
		var k := "%s:%s" % [r.get("to", ""), ev]
		if open.has(k): bad.order.append(id)
		if (r.get("when", {}) as Dictionary).is_empty(): open[k] = true
		for s in r.get("do", []):
			if s.has("sound") and not SoundBank.has_sound(str(Audio.SFX_ALIAS.get(str(s.sound), str(s.sound)))): bad.sound.append("%s (%s)" % [id, s.sound])
			if s.has("fx"):
				if not (str(s.fx) in FxLayer.KINDS or str(s.fx) in WorldShared.FX_CALLS): bad.fx.append("%s (%s)" % [id, s.fx])
				if not str(s.get("at", "feet")) in WorldShared.ANCHORS: bad.at.append("%s (%s)" % [id, s.at])
			if s.has("call"):
				called[str(s.call)] = true
				if not str(s.call) in WorldShared.HANDLERS: bad["call"].append("%s (%s)" % [id, s.call])
			_colours(s.get("color"), id, bad.color)
			_keys(s, id, bad.key)
	check(bad.to.is_empty(), "every row is played by the world or the HUD (%s)" % [bad.to])
	check(bad.event.is_empty(), "every row's event is one the game emits (%s)" % [bad.event])
	check(bad.sound.is_empty(), "every row's sound is in the sound bank (%s)" % [bad.sound])
	check(bad.fx.is_empty(), "every row's effect is one of FxLayer's (%s)" % [bad.fx])
	check(bad.at.is_empty(), "every effect's anchor is one of WorldShared's (%s)" % [bad.at])
	check(bad["call"].is_empty(), "every handler a row calls is one of WorldShared's (%s)" % [bad.call])
	check(called.size() == WorldShared.HANDLERS.size(), "every handler of WorldShared is called by a row (%s of %s)" % [called.keys(), WorldShared.HANDLERS])
	check(bad.color.is_empty(), "every colour is a UiKit token, hex or an array's (%s)" % [bad.color])
	check(bad.key.is_empty(), "every string key a row names exists (%s)" % [bad.key])
	check(bad.order.is_empty(), "no row follows one of its event's that always holds (%s)" % [bad.order])

## Every event name a script emits by name (a line that calls emit or emit_event with it quoted).
func _emitted() -> Dictionary:
	var out := {}
	var emit_re := RegEx.create_from_string("\\bemit(_event)?\\(")
	var q := RegEx.create_from_string("\"([a-z0-9_]+)\"")
	for path in _scripts("res://scripts/"):
		for line in FileAccess.get_file_as_string(path).split("\n"):
			if emit_re.search(line) == null: continue
			for m in q.search_all(line): out[m.get_string(1)] = true
	return out

func _scripts(dir: String) -> Array:
	var out: Array = []
	for f in DirAccess.get_files_at(dir):
		if str(f).ends_with(".gd"): out.append(dir + f)
	for d in DirAccess.get_directories_at(dir): out.append_array(_scripts(dir + d + "/"))
	return out

func _colours(spec, id: String, bad: Array) -> void:
	if spec == null: return
	if spec is Dictionary:
		_colours(spec.get("then"), id, bad)
		_colours(spec.get("else"), id, bad)
	elif spec is Array:
		if spec.size() == 2: _colours(spec[0], id, bad)
		elif spec.size() < 3: bad.append("%s (%s)" % [id, spec])
	else:
		var s := str(spec)
		var ok := Color.html_is_valid(s) if s.begins_with("#") else (s.begins_with("array:") or MomentRules.tokens().has(s))
		if not ok: bad.append("%s (%s)" % [id, s])

## A key with a `suffix` (S6: "ui.relations.align_" and the payload's word) needs a string that begins with it.
func _keys(node, id: String, bad: Array) -> void:
	if node is Dictionary:
		if node.has("key") and node.has("suffix"):
			if not ContentDB.strings.keys().any(func(k): return str(k).begins_with(str(node.key))): bad.append("%s (%s…)" % [id, node.key])
		elif node.has("key") and not ContentDB.strings.has(str(node.key)): bad.append("%s (%s)" % [id, node.key])
		for v in node.values(): _keys(v, id, bad)
	elif node is Array:
		for v in node: _keys(v, id, bad)

# ------------------------------------------------------------------ 2. the conditions
func _conditions() -> void:
	var me := Game.active_id
	check(Cues.holds({"amount": 0}, {}) and not Cues.holds({"amount": 0}, {"amount": 3}), "a number the payload leaves out holds 0")
	check(not Cues.holds({"answered": true}, {}) and Cues.holds({"answered": false}, {}) and Cues.holds({"answered": true}, {"answered": true}), "a flag the payload leaves out holds false")
	check(Cues.holds({"kind": ["a", "b"]}, {"kind": "b"}) and not Cues.holds({"kind": ["a", "b"]}, {"kind": "c"}) and not Cues.holds({"kind": ["a"]}, {}), "a list holds for one of its values")
	check(Cues.holds({"coins": {"gt": 0}}, {"coins": 5}) and not Cues.holds({"coins": {"gt": 0}}, {"coins": 0}) and not Cues.holds({"coins": {"gt": 0}}, {}), "gt holds for more")
	check(Cues.holds({"actor": "active"}, {"actor": me}) and not Cues.holds({"actor": "active"}, {"actor": me + "x"}) and not Cues.holds({"actor": "active"}, {}), "actor active is the active character")
	check(Cues.holds({"@active": true}, {}) and Cues.holds({"@pools.max_hp": {"gt": 0}}, {}) and not Cues.holds({"@no_such.path": 1}, {}), "@ reads the active character")
	check(Cues.value({"if": {"ring": {"gt": 0}}, "then": "payload.ring", "else": 60}, {"ring": 12.5}) == 12.5
		and float(Cues.value({"if": {"ring": {"gt": 0}}, "then": "payload.ring", "else": 60}, {})) == 60.0, "a value's if picks its branch")
	check(Cues.color(["BRIGHT_JADE", 0.5]) == Color(UiKit.BRIGHT_JADE, 0.5) and Cues.color("#ff9a5a") == Color("ff9a5a")
		and Cues.color("array:payload.kind", {"kind": "killing"}) == FxLayer.ARRAY_COLOURS.killing and Cues.color("array:payload.kind", {}) == FxLayer.ARRAY_COLOURS.guard,
		"colours: a token with its alpha, hex, an array's engraving (the guard's by default)")
	var first := Cues.pick("world", "loot_picked", {"coins": 3})
	var second := Cues.pick("world", "loot_picked", {"item": "x"})
	check(str(first.get("id", "")) == "world.loot_picked.coins" and str(second.get("id", "")) == "world.loot_picked.item", "the first row that holds plays (%s, %s)" % [first.get("id"), second.get("id")])

# ------------------------------------------------------------------ 3. every row played
class Host:
	var fx: FxLayer
	var combat_fx: CombatFx
	var object_views := {}
	var npc_views := {}
	var enemy_views := {}
	var portal_views: Array = []
	var shakes: Array = []
	var loot := Node2D.new()
	var transfer_cooldown := 0.0
	func fx_layer() -> FxLayer: return fx
	func feet() -> Vector2: return Vector2(100, 200)
	func facing() -> int: return 1
	func add_shake(s: float, _amp := -1.0) -> void: shakes.append(s)
	func loot_parent() -> Node2D: return loot

class View:
	var position := Vector2(300, 150)
	var hit_flash := 0.0

func _play_every_row() -> void:
	var c = Game.active()
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", Vector2(float(c.position.get("x", 400.0)), float(c.position.get("y", 800.0))) + Vector2(60, 10), 1)
	check(foe != null, "a foe stands in the room for the rows over a foe")
	var host := Host.new()
	host.fx = FxLayer.new()
	host.combat_fx = CombatFx.new(host.fx, host)
	host.object_views = {"o1": View.new()}
	var base := {"actor": Game.active_id, "x": 200.0, "y": 150.0, "alt": 20.0, "radius": 100.0, "enemy": foe.uid if foe else 0, "object": "o1",
		"items": [], "effects": [], "gains": {}, "hazard": "fog", "emote": "wave", "treasure": "bronze_bell", "line": "-", "target": "1"}
	var played := 0
	var wrong: Array = []
	var world_rows: Array = ContentDB.all("cues").filter(func(r): return str(r.get("to", "")) == "world")
	for r in world_rows:
		var p := base.duplicate(true)
		var undo := {}
		for k in r.get("when", {}):
			var want = r.when[k]
			if str(k).begins_with("@"):
				if want is Dictionary and want.has("gt"): undo[k] = _set_active(str(k), float(want.gt) + 1.0)
				continue
			if str(k) in ["actor", "target"] and str(want) == "active": p[k] = Game.active_id
			elif want is Array: p[k] = want[0]
			elif want is Dictionary: p[k] = float(want.get("gt", 0)) + 1.0
			else: p[k] = want
		var picked := Cues.pick("world", str(r.event), p)
		host.fx.fx.clear()
		host.shakes.clear()
		Audio.last_start.clear()
		for v in Audio.voices: v.stop()
		var h0: int = Audio.history.size()
		var ok := WorldShared.play(host, str(r.event), p)
		var want_fx := 0
		var want_sounds := 0
		var want_shakes := 0
		var calls := false
		for s in r.do:
			if s.has("fx"): want_fx += 2 if str(s.fx) == "parry" else 1
			if s.has("sound"): want_sounds += 1
			if s.has("shake"): want_shakes += 1
			if s.has("call"): calls = true
		var got_fx := host.fx.fx.size()
		var got_sounds: int = Audio.history.size() - h0
		var fine: bool = ok and str(picked.get("id", "")) == str(r.id)
		fine = fine and (got_fx >= want_fx if calls else got_fx == want_fx) and (got_sounds >= want_sounds if calls else got_sounds == want_sounds)
		fine = fine and (host.shakes.size() >= want_shakes if calls else host.shakes.size() == want_shakes)
		if not fine: wrong.append("%s (picked %s; fx %d/%d, sounds %d/%d, shakes %d/%d)" % [r.id, picked.get("id", "none"), got_fx, want_fx, got_sounds, want_sounds, host.shakes.size(), want_shakes])
		for k in undo: _set_active(str(k), undo[k])
		played += 1
	check(played == world_rows.size() and wrong.is_empty(), "every row plays as it is written, once each (%d rows; %s)" % [played, wrong])
	check(host.object_views.o1.hit_flash > 0.0, "a thing struck flashes")
	check(not WorldShared.play(host, "resource_changed", {"actor": Game.active_id}), "an event the table does not answer is left to the view")

## Set a value of the active character by its "@" path; returns the value it had.
func _set_active(key: String, v):
	var parts := key.trim_prefix("@").split(".")
	var node = Game.active()
	for i in parts.size() - 1: node = node.get(parts[i])
	var last := parts[parts.size() - 1]
	var was = node.get(last)
	node.set(last, v)
	return was

# ------------------------------------------------------------------ 4. the HUD's rows (S6)
const TOAST_STYLES := ["unlock", "gold", "quest", "danger"]

## Each step of a HUD row is a log line with its colour or a toast with one of the HUD's styles; an event the table
## answers for the HUD is no arm of HudNotices.handle as well (it would never be reached).
func _hud_rows() -> void:
	var rows: Array = ContentDB.all("cues").filter(func(r): return str(r.get("to", "")) == "hud")
	check(rows.size() >= 200, "the HUD's notices are rows of the table (%d)" % rows.size())
	var bad: Array = []
	for r in rows:
		for s in r.get("do", []):
			var log_ok: bool = s.has("log") and s.has("color") and not s.has("toast")
			var toast_ok: bool = s.has("toast") and str(s.get("style", "")) in TOAST_STYLES and not s.has("log")
			if not (log_ok or toast_ok): bad.append("%s (%s)" % [r.id, s])
	check(bad.is_empty(), "every step of a HUD row is a log line with its colour or a toast in one of the HUD's styles (%s)" % [bad])
	var arms := {}
	var arm := RegEx.create_from_string("^\\t\\t(\"[a-z0-9_]+\"(, \"[a-z0-9_]+\")*):")
	var q := RegEx.create_from_string("\"([a-z0-9_]+)\"")
	for line in FileAccess.get_file_as_string("res://scripts/hud/hud_notices.gd").split("\n"):
		var m := arm.search(line)
		if m == null: continue
		for e in q.search_all(m.get_string(1)): arms[e.get_string(1)] = true
	var both: Array = rows.filter(func(r): return arms.has(str(r.event))).map(func(r): return str(r.id))
	check(arms.size() >= 40 and both.is_empty(), "no event is both a HUD row and an arm of HudNotices.handle (%d arms; %s)" % [arms.size(), both])

## The conditions and the text sources the HUD's rows add to Cues.
func _hud_conditions() -> void:
	check(Cues.holds({"reason": {"not": "recalled"}}, {}) and Cues.holds({"reason": {"not": "recalled"}}, {"reason": "time"})
		and not Cues.holds({"reason": {"not": "recalled"}}, {"reason": "recalled"}) and not Cues.holds({"text": {"not": ""}}, {}),
		"not holds for anything else (a payload that leaves the key out holds \"\")")
	check(Cues.holds({"delta": {"lt": 0}}, {"delta": -2}) and not Cues.holds({"delta": {"lt": 0}}, {}) and Cues.holds({"rank": {"le": 3}}, {"rank": 3})
		and Cues.holds({"stacks": {"ge": 10}}, {"stacks": 10}) and not Cues.holds({"stacks": {"ge": 10}}, {"stacks": 9}), "lt, le and ge compare numbers")
	check(Cues.holds({"@revealed": "hud:system_log"}, {}) == Game.is_revealed("hud:system_log") and Cues.holds({"@unlocked": "mail"}, {}) == Unlocks.is_unlocked(Game.active_id, "mail"),
		"@revealed and @unlocked ask the active character")
	var p := {"n": 3, "secs": 90.0, "items": ["a", "b"], "word": "STABLE", "id": "wood_root", "silver": 12500, "bonus": 0.256, "kind": "cloud"}
	check(Cues.arg({"int": "payload.secs"}, p) == 90 and Cues.arg({"int": {"payload": "gone", "or": 11}}, p) == 11 and Cues.arg({"int": "payload.bonus", "times": 100.0}, p) == 25
		and Cues.arg({"round": "payload.bonus", "times": 100.0}, p) == 26 and Cues.arg({"neg": "payload.n"}, p) == -3 and Cues.arg({"count": "payload.items"}, p) == 2
		and Cues.arg({"count": "payload.gone"}, p) == 0, "the numbers an argument makes (int, round, neg, count)")
	check(Cues.arg({"span": "payload.secs"}, p) == UiKit.span(90.0) and Cues.arg({"fmt": "payload.silver"}, p) == UiKit.fmt(12500) and Cues.arg({"title": "payload.id"}, p) == "Wood Root"
		and Cues.arg({"lower": "payload.word"}, p) == "stable" and Cues.arg({"pet_name": "payload.gone"}, p) == Tx.t("hud.your_spirit_animal"),
		"the words an argument makes (span, fmt, title, lower, a pet's name)")
	check(Cues.text({"join": [{"key": "hud.codex"}, "payload.word"]}, p) == Tx.t("hud.codex") + "STABLE" and Cues.text({"key": "hud.phenomenon_", "suffix": "payload.kind"}, p) == Tx.t("hud.phenomenon_cloud")
		and Cues.text({"key": "hud.sword_swarm", "args": [{"int": "payload.n"}], "plural": {"int": "payload.n"}}, p) == Tx.plural("hud.sword_swarm", 3) % 3,
		"a text joins texts, ends a key in a value and counts a plural")

## Every HUD row played once through the HUD's own _on_event, with a payload its `when` holds for: it is the row the
## table picks, and the HUD writes its log lines and toasts as the row says.
func _play_every_hud_row() -> void:
	var hud = main.hud
	check(hud != null and hud.bound(), "the HUD is bound to the character")
	if hud == null or not hud.bound(): return
	# A finished route, a grudge with a value, a rank off the podium: a later row's payload is not caught by an earlier
	# row's default. A line of words and a treasure for the rows that say them.
	var base := {"finished": true, "value": 5, "rank": 5, "text": "A line.", "treasure": "mindwell_lotus"}
	var played := 0
	var wrong: Array = []
	for r in ContentDB.all("cues").filter(func(r): return str(r.get("to", "")) == "hud"):
		var p := base.duplicate(true)
		for k in r.get("when", {}):
			var want = r.when[k]
			if str(k).begins_with("@"): continue   # every system is unlocked and revealed here
			if str(k) in ["actor", "target"] and str(want) == "active": p[k] = Game.active_id
			elif want is Array: p[k] = want[0]
			elif want is Dictionary:
				if want.has("not"): p[k] = (str(want["not"]) + "x") if want["not"] is String else (not want["not"] if want["not"] is bool else float(want["not"]) + 1.0)
				elif want.has("gt"): p[k] = float(want.gt) + 1.0
				elif want.has("lt"): p[k] = float(want.lt) - 1.0
				else: p[k] = float(want.get("ge", want.get("le", 0)))
			else: p[k] = want
		hud.log_lines = []
		hud.toasts = []
		var picked := Cues.pick("hud", str(r.event), p)
		hud._on_event(str(r.event), p)
		var logs: Array = r.do.filter(func(s): return s.has("log"))
		var toasts: Array = r.do.filter(func(s): return s.has("toast"))
		var fine: bool = str(picked.get("id", "")) == str(r.id) and hud.log_lines.size() == logs.size() and hud.toasts.size() == toasts.size()
		for i in mini(logs.size(), hud.log_lines.size()):
			fine = fine and str(hud.log_lines[i].text) == Cues.text(logs[i]["log"], p) and str(hud.log_lines[i].text) != "" and hud.log_lines[i].color == Cues.color(logs[i]["color"], p)
		for i in mini(toasts.size(), hud.toasts.size()):
			fine = fine and str(hud.toasts[i].text) == Cues.text(toasts[i].toast, p) and str(hud.toasts[i].text) != "" and str(hud.toasts[i].kind) == str(toasts[i].style)
		if not fine: wrong.append("%s (picked %s; log %d/%d, toasts %d/%d)" % [r.id, picked.get("id", "none"), hud.log_lines.size(), logs.size(), hud.toasts.size(), toasts.size()])
		played += 1
	hud.log_lines = []
	hud.toasts = []
	check(played >= 200 and wrong.is_empty(), "every HUD row plays as it is written, once each, through the HUD (%d rows; %s)" % [played, wrong.slice(0, 8)])
