extends Node
## Rules, replay and offline suites (Part 7 · Quality gates).
##   Rules:   each formula at its sample values (monster pools, damage steps, gap
##            factors, mastery, risk, offline caps).
##   Replay:  same seed plus same intents gives the same state.
##   Offline: caps, a backward clock, bottlenecks hold, no breakthrough while away.
## Run headless:  godot --headless --path . res://tests/rules_tests.tscn

var checks := 0
var failures := 0

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func near(a: float, b: float, eps := 0.01) -> bool:
	return absf(a - b) <= eps * maxf(1.0, absf(b))

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	rules_suite()
	replay_suite()
	offline_suite()
	print("rules_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ formulas
func rules_suite() -> void:
	# S13: HP_mob = (30 + 15L + 1.1L^2) x role; the spec's own check is 290 HP at Level 10.
	var normal := StatRules.mob_stats({"role": "normal"}, 10)
	check(near(normal.max_hp, 290.0), "normal monster at Level 10 has 290 HP (%.1f)" % normal.max_hp)
	check(near(normal.attack, 37.0), "normal monster attack at Level 10 is 37 (%.1f)" % normal.attack)
	var elite := StatRules.mob_stats({"role": "normal"}, 10, true)
	check(near(elite.max_hp, 290.0 * 6.0) and near(elite.attack, 37.0 * 1.5), "elites are 6x HP and 1.5x attack")
	var boss := StatRules.mob_stats({"role": "dungeon_boss"}, 18)
	check(near(boss.max_hp, (30.0 + 15.0 * 18 + 1.1 * 18 * 18) * 80.0), "dungeon bosses are 80x HP")
	check(near(StatRules.mob_stats({"role": "normal", "hp_mult": 0.5}, 10).max_hp, 145.0), "hp_mult scales one monster")
	# S13 kill progress gap factors: 5+ above x1.2, within 4 x1.0, 5-9 below x0.5, 10+ below x0.1.
	check(near(ProgressionRules.gap_factor(6), 1.2), "5+ levels above: x1.2")
	check(near(ProgressionRules.gap_factor(0), 1.0) and near(ProgressionRules.gap_factor(-4), 1.0), "within 4 levels: x1.0")
	check(near(ProgressionRules.gap_factor(-6), 0.5), "5-9 below: x0.5")
	check(near(ProgressionRules.gap_factor(-12), 0.1), "10+ below: x0.1")
	# S12 combat steps
	check(near(CombatRules.hit_chance(100.0, 0.0), 1.0), "hit chance caps at 100%")
	check(CombatRules.hit_chance(100.0, 1000.0) >= 0.55, "hit chance never below the floor")
	var dr := CombatRules.defence_reduction(1e9, 1, 0.0)
	check(dr <= 0.75 + 1e-6, "defence reduction caps at 75%% (%.3f)" % dr)
	check(CombatRules.defence_reduction(100.0, 10, 0.4) < CombatRules.defence_reduction(100.0, 10, 0.0), "penetration lowers defence")
	check(CombatRules.realm_gap_factor(3, 1) > 1.0 and CombatRules.realm_gap_factor(1, 3) < 1.0, "realm gap favours the higher realm")
	check(near(CombatRules.realm_gap_factor(2, 2), 1.0), "same realm: no gap factor")
	# S09 mastery doubles per tier; S05 risk words
	check(near(ProgressionRules.mastery_needed(1), 100.0) and near(ProgressionRules.mastery_needed(3), 400.0), "mastery 100 / 200 / 400")
	check(ProgressionRules.risk_index(0, false, 0, 0, false) == 0 and ProgressionRules.risk_index(5, true, 3, 0, false) == 3, "risk index clamps 0..3")
	check(ProgressionRules.risk_index(1, false, 0, 1, false) == 0, "a support cancels one unmet soft requirement")
	check(ProgressionRules.success_chance("low") > ProgressionRules.success_chance("severe"), "lower risk, better odds")
	# S07 offline window
	var span := ProgressionRules.offline_minutes(20.0 * 3600.0, 12.0)
	check(near(span.minutes, 720.0) and span.capped, "offline caps at 12 hours")
	check(near(ProgressionRules.offline_minutes(3600.0, 12.0).minutes, 60.0), "an hour away is an hour")
	# Body XP grows linearly per level (S29)
	check(ProgressionRules.body_xp_needed(5) > ProgressionRules.body_xp_needed(1), "body levels get dearer")

# ------------------------------------------------------------------ replay
## Two runs from the same seed with the same intents must end in the same state.
func _run_once(folder: String) -> String:
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Clock.override_utc = 1767225600.0   # fixed "now"
	Clock.debug_offset_s = 0.0
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 12345
	Rng.restore("account", {}, 12345)
	Game.submit({"type": "create_character", "slot": 1, "name": "Replay", "appearance": {"hair": "topknot"}})
	Game.submit({"type": "enter_character", "slot": 1})
	var c = Game.active()
	Rng.restore(c.id, {}, 777)
	Game.submit({"type": "enter_world"})
	var st := ActorState.new()
	Game.bind_movement(c.id, st)
	st.surface = Game.room_rt.geometry.surfaces[0]
	st.plane = Vector2(330, 780)
	# A fixed script of intents and ticks.
	for i in 400:
		if i % 20 == 0: Game.submit({"type": "basic_attack", "facing": 1})
		if i == 100: Game.submit({"type": "start_meditation"})
		if i == 300: Game.submit({"type": "stop_meditation"})
		Game.tick(0.05)
	var snap: Dictionary = c.snapshot()
	snap.erase("last_active_utc")
	return JSON.stringify(snap)

func replay_suite() -> void:
	var a := _run_once("user://replay_a/")
	var b := _run_once("user://replay_b/")
	check(a == b, "same seed and intents replay to the same character state")
	check(a.length() > 200, "replay produced a real snapshot")

# ------------------------------------------------------------------ offline
func offline_suite() -> void:
	var c = Game.active()
	if c == null:
		check(false, "offline suite needs a character")
		return
	var cu = c.cultivator
	# Seclusion is locked before Bone Forging 7: pretend we are there for the rule checks.
	cu.realm_key = "bone_forging_7"
	Game.progression.apply_learn_method(c.id, "riverbreath_fragment")
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	var before: float = cu.qp
	var r := Game.progression.claim_offline(c, -3600.0)
	check(r.get("ok", false) and near(cu.qp, before), "a backward clock gains nothing")
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	var r12: Dictionary = Game.progression.claim_offline(c, 12.0 * 3600.0)
	var gained_12: float = cu.qp - before
	cu.qp = before
	cu.state = "accumulating"
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	Game.progression.claim_offline(c, 48.0 * 3600.0)
	var gained_48: float = cu.qp - before
	check(gained_12 > 0.0, "offline seclusion accumulates progress (%.1f)" % gained_12)
	check(near(gained_48, gained_12, 0.02) or cu.state == "bottleneck", "offline gains stop at the 12-hour cap")
	# Offline never breaks through: fill to the bottleneck and claim a long absence.
	cu.qp = cu.need() * 0.99
	cu.state = "accumulating"
	var realm_before: String = cu.realm_key
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	Game.progression.claim_offline(c, 12.0 * 3600.0)
	check(cu.realm_key == realm_before, "offline progress never breaks through")
	check(cu.state == "bottleneck" or cu.qp <= cu.need(), "a full bar waits at the bottleneck")
	# Offline factor: realm progress while away is 10% of the meditation rate.
	var rate := ProgressionRules.meditation_rate(c, 1.0, Game.progression.accumulation_bonus(c))
	check(near(float(r12.get("gains", {}).get("qp", 0.0)), rate * float(ContentDB.curve("offline_factor", 0.1)) * 720.0, 0.05), "offline factor 0.1 of the meditation rate")
	Clock.override_utc = -1.0
