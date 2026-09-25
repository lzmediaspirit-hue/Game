extends Node
## Balance simulator (S38, Part 7): a rate-based bot plays the data to the end of Act I
## and reports hours to each realm. Each Level it spends an active minute as
## data/balance.json says (fighting at the right Level, meditating at the best spot it
## has reached, the rest travelling and crafting), hands in the quests that open at that
## Level and one daily mission per hour. Realm progress uses the real rules: kill QP and
## gap factors, the meditation rate of a real character with that realm's method,
## body-stage training, quest percentages. It fails when a realm lands more than ±15%
## off the Part 4 pacing table.
## Run headless:  godot --headless --path . res://tests/balance_sim.tscn

var checks := 0
var failures := 0

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var cfg := ContentDB.config("balance")
	check(not cfg.is_empty(), "balance.json is present")
	var c = _character()
	check(c != null, "a character to simulate")
	if c == null: return _finish()
	var quest_levels := _quest_levels()
	var hours := {}              # realm key -> hours when it is reached
	var t := float(cfg.get("prologue_hours", 0.5)) * 60.0   # active minutes
	var end_key := str(cfg.get("act_end", "heaven_glimpse_3"))
	var key := "bone_forging_1"
	while key != "":
		hours[key] = t / 60.0
		var r := ContentDB.realm(key)
		var lv := int(r.get("level", 0))
		var need := float(r.get("accumulate_needed", 100))
		var income := _income(c, cfg, key, lv)
		# Quests that open inside this stage pay a share of its need on hand-in.
		# Optional side quests are detours: they also cost active time the mixed session does not cover.
		var lump := 0.0
		var detour := 0.0
		for n in int(r.get("levels", 1)):
			for kind in quest_levels.get(lv + n, {}):
				lump += float(ContentDB.curve("quest_qp_pct.%s" % kind, 0.0)) * int(quest_levels[lv + n][kind])
				detour += float(cfg.get("quest_minutes", {}).get(kind, 0.0)) * int(quest_levels[lv + n][kind])
		var base_min := need / income
		# Daily missions: a share of the need per hour of play.
		var daily := float(ContentDB.curve("quest_qp_pct.daily", 0.05)) * float(cfg.get("dailies_per_hour", 1.0)) * base_min / 60.0
		var minutes := base_min * maxf(0.2, 1.0 - lump - daily)
		t += minutes + detour
		if key == end_key: break
		key = str(r.get("next", ""))
	hours["act_end"] = t / 60.0
	var tol := float(cfg.get("tolerance", 0.15))
	print("realm                  sim h   target h   ratio")
	var targets: Array = cfg.get("pacing", []).duplicate()
	targets.append(["act_end", float(cfg.get("act_end_hours", 65))])
	for row in targets:
		var k := str(row[0])
		var want := float(row[1])
		var got := float(hours.get(k, -1.0))
		var ratio := got / want if want > 0.0 else 0.0
		print("%-22s %6.1f   %8.1f   %5.2f" % [k, got, want, ratio])
		if k == "bone_forging_1": continue   # set by the Prologue, not by rates
		check(got > 0.0 and absf(ratio - 1.0) <= tol, "%s reached at %.1f h (target %.1f h ±%d%%)" % [k, got, want, int(tol * 100.0)])
	_currency(cfg)
	_finish()

## S39: a player can afford the next upgrade in their grade band after about 1–2 hours.
func _currency(cfg: Dictionary) -> void:
	for row in cfg.get("upgrades", []):
		var lv := int(row[0])
		var item := str(row[1])
		var rate := _taels_per_hour(cfg, lv)
		var price := LootRules.buy_price(item)
		var h := price / maxf(1.0, rate)
		print("Level %d: %d taels/h (spec about %d) · %s costs %d → %.1f h" % [lv, int(rate), int(row[2]), item, price, h])
		check(h >= float(cfg.get("afford_hours", [0.75, 2.5])[0]) and h <= float(cfg.get("afford_hours", [0.75, 2.5])[1]),
			"%s is affordable after %.1f h of play at Level %d" % [item, h, lv])

## Coins and loot sold at NPC prices from the monsters of this Level, plus daily mission pay.
func _taels_per_hour(cfg: Dictionary, lv: int) -> float:
	var rng := RandomNumberGenerator.new()
	rng.seed = 12345 + lv
	var foes: Array = ContentDB.all("enemies").filter(func(e):
		var r: Array = e.get("level", [0, 0])
		return str(e.get("role", "")) == "normal" and not e.get("passive", false) and lv >= int(r[0]) - 2 and lv <= int(r[r.size() - 1]) + 2)
	if foes.is_empty(): return 0.0
	var per_kill := 0.0
	var rolls := 200
	for e in foes:
		for i in rolls:
			var drop := LootRules.roll(str(e.get("loot", e.id)), rng, lv, 0.0, 0.0, {"no_equipment": true})
			per_kill += int(drop.coins)
			for it in drop.items: per_kill += LootRules.sell_price(str(it.item)) * int(it.count)
	per_kill /= float(rolls * foes.size())
	var kills_h := float(cfg.get("kills_per_min", 6)) * 60.0 * float(cfg.get("mix", {}).get("fight", 0.35))
	var dailies := float(cfg.get("dailies_per_hour", 1.0)) * (10 + lv * 3)
	return per_kill * kills_h + dailies

func _finish() -> void:
	print("balance_sim: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

## QP per active minute at this stage, from the real rules.
func _income(c, cfg: Dictionary, key: String, lv: int) -> float:
	var mix: Dictionary = cfg.get("mix", {})
	var major := str(ContentDB.realm(key).get("realm", key))
	c.cultivator.realm_key = key
	c.cultivator.method_id = str(cfg.get("method", {}).get(major, "riverbreath_fragment"))
	c.cultivator.stability = str(cfg.get("stability", "stable"))
	c.cultivator.consolidation_penalty = false
	var fight := float(cfg.get("kills_per_min", 6)) * ProgressionRules.kill_qp(lv, lv, "normal")
	var density := float(cfg.get("density", {}).get(major, 1.0))
	var sit := ProgressionRules.meditation_rate(c, density, 0.0)
	if ProgressionRules.is_body_stage(key): sit = maxf(sit, float(ContentDB.curve("training_qp_per_min", 40)))
	return float(mix.get("fight", 0.4)) * fight + float(mix.get("meditate", 0.3)) * sit

## Level -> {quest kind: count}: where each quest becomes available (its realm requirement,
## its chapter code such as "qk5", or the median of its numbered chapter).
func _quest_levels() -> Dictionary:
	var codes := {"bf": "bone_forging", "qk": "qi_kindling", "qu": "qi_unfurling", "ht": "heart_tempering", "cs": "cloud_stride",
		"sa": "spirit_awakening", "hg": "heaven_glimpse"}
	var placed := {}   # quest -> level
	var chapters := {} # numbered chapter -> [levels]
	for q in ContentDB.all("quests"):
		var lv := -1
		for r in q.get("requires", {}).get("all", []):
			if str(r.get("kind", "")) == "realm_at_least": lv = maxi(lv, int(ContentDB.realm(str(r.realm)).get("level", 0)))
		var ch := str(q.get("chapter", ""))
		if lv < 0 and ch.length() >= 3 and codes.has(ch.left(2)) and ch.substr(2).is_valid_int():
			lv = int(ContentDB.realm("%s_%s" % [codes[ch.left(2)], ch.substr(2)]).get("level", -1))
		if lv >= 0: placed[str(q.id)] = lv
		if ch.is_valid_int() and lv >= 0: chapters[ch] = chapters.get(ch, []) + [lv]
	var out := {}
	var loose: Array = []   # side stories with no realm anchor: spread evenly over the Act
	for q in ContentDB.all("quests"):
		var kind := str(q.get("qp", q.get("kind", "side")))
		if kind == "prologue": continue
		var lv2 := int(placed.get(str(q.id), -1))
		var ch2 := str(q.get("chapter", ""))
		if lv2 < 0 and chapters.has(ch2):
			var ls: Array = chapters[ch2].duplicate()
			ls.sort()
			lv2 = int(ls[ls.size() / 2])
		if lv2 < 0:
			loose.append(kind)
			continue
		_add(out, lv2, kind)
	var last := int(ContentDB.realm(str(ContentDB.config("balance").get("act_end", "heaven_glimpse_3"))).get("level", 57))
	for i in loose.size():
		_add(out, 1 + int(float(i + 1) * (last - 1) / float(loose.size() + 1)), str(loose[i]))
	return out

func _add(out: Dictionary, lv: int, kind: String) -> void:
	if not out.has(lv): out[lv] = {}
	out[lv][kind] = int(out[lv].get(kind, 0)) + 1

func _character():
	var folder := "user://balance_sim/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Clock.override_utc = 1767225600.0   # a fixed "now" and seed: the same character every run
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 2026
	Rng.restore("account", {}, 2026)
	Game.submit({"type": "create_character", "slot": 1, "name": "Balance", "appearance": {"hair": "topknot"}})
	Game.submit({"type": "enter_character", "slot": 1})
	return Game.active()
