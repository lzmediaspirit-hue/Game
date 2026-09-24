# Headless rules tests:  godot --headless --path . --script tests/test_rules.gd
extends SceneTree

const GameScript = preload("res://scripts/core/game.gd")
const S = preload("res://scripts/core/state.gd")
const R = preload("res://scripts/core/rules.gd")

var passed := 0
var failures := 0
var _cur := ""


func check(cond: bool, msg := "") -> void:
	if not cond:
		failures += 1
		push_error("FAIL [%s] %s" % [_cur, msg])
		print("    ✗ ", msg)


func fresh(path := "user://test_save.json") -> Node:
	for f in [path, path + ".backup-v3", path + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	var g: Node = GameScript.new()
	g.save_path = path
	g.rng.seed = 42
	g.load_save()
	return g


func test(name: String, fn: Callable) -> void:
	_cur = name
	var before := failures
	fn.call()
	if failures == before:
		passed += 1
		print("  ✓ ", name)
	else:
		print("  ✗ ", name)


func _init() -> void:
	print("Jade River rules")
	test("new disciple journey", t_journey)
	test("failed actions roll back", t_rollback)
	test("foundation trial gates", t_foundation)
	test("weapon mastery", t_mastery)
	test("commissions + shop", t_commission)
	test("shared storage", t_storage)
	test("v3 legacy migration", t_migration)
	test("future save untouched", t_future)
	test("assignment cap", t_assign)
	test("formation seal", t_seal)
	print("%d passed, %d failed checks" % [passed, failures])
	quit(1 if failures else 0)


func t_journey() -> void:
	var g := fresh()
	g.create_character(0, "Hurt render", "plum_bob", "river_traveler", "spear")
	g.select(0)
	var p: Dictionary = g.p
	check(R.objective(p).short == "Speak with Elder Wen", "objective")
	check(not g.perform("harvest", {"node_id": "x", "type": "dewleaf"}).ok, "no kit before Wen")
	var t: Dictionary = g.perform("talk", {"npc": "wen"})
	check(t.ok and t.lines.size() > 2, "intro")
	check(p.items.has("pick") and p.items.has("kit") and p.items.has("rod"), "tools")
	var n := 0
	while R.count(p, "herb") < 5 and n < 20:
		n += 1
		g.perform("harvest", {"node_id": "d%d" % n, "type": "dewleaf"})
	while R.count(p, "copper") < 2 and n < 40:
		n += 1
		g.perform("harvest", {"node_id": "c%d" % n, "type": "copper"})
	check(p.quests.ch1.step == 2, "advanced to raiders, step=%d" % p.quests.ch1.step)
	check(p.soul > 0, "discovery soul")
	for i in 5:
		g.perform("record_kill", {"type": "raider"})
	check(p.quests.ch1.step == 3, "after raiders")
	check(not g.perform("craft", {"id": "brew_mend", "station": "forge"}).ok, "wrong station")
	check(g.perform("craft", {"id": "brew_mend", "station": "furnace"}).ok, "brew")
	check(p.quests.ch1.step == 4, "after brew")
	check(p.level >= 2, "level 2, got %d" % p.level)
	check(not g.perform("meditate_cycle", {"safe": false}).ok, "unsafe")
	while p.insight < 30:
		g.perform("meditate_cycle", {"safe": true})
	var hp0: int = S.stats(p).max_hp
	check(g.perform("breakthrough", {"safe": true}).ok, "breakthrough")
	check(p.realm == 1 and S.stats(p).max_hp == hp0 + 20, "realm bonus")
	check(p.abilities.known.has("nova"), "nova learned")
	check(p.quests.ch1.step == 5, "boss step")
	g.perform("record_kill", {"type": "captain", "boss_id": "captain"})
	check(p.quests.ch1.step == 6, "return step")
	g.perform("talk", {"npc": "wen"})
	check(p.quests.ch1.state == "complete" and p.flags.get("ch1_done", false), "chapter done")
	check(R.count(p, "seal_fragment") == 1 and p.discovered.areas.get("lantern", false), "reward+unlock")
	check(p.quests.ch2.state == "active", "ch2 active")


func t_rollback() -> void:
	var g := fresh()
	g.create_character(0, "A", "plum_bob", "river_traveler", "spear")
	g.select(0)
	var before := JSON.stringify(g.p)
	var r: Dictionary = g.perform("craft", {"id": "smelt_bronze", "station": "forge"})
	check(not r.ok and "Copper" in r.err, "err names copper")
	check(JSON.stringify(g.p) == before, "unchanged")


func t_foundation() -> void:
	var g := fresh()
	g.create_character(0, "B", "plum_bob", "river_traveler", "spear")
	g.select(0)
	var p: Dictionary = g.p
	p.realm = 1; p.level = 4; p.insight = 120; p.essence = 100
	check(not g.perform("breakthrough", {"safe": true}).ok, "needs trial")
	check(not g.perform("check_trial", {"safe": true}).ok, "missing pill")
	g.perform("open_meridian"); g.perform("open_meridian")
	check(g.perform("open_meridian").ok, "3rd ok at QA")
	check(not g.perform("open_meridian").ok, "cap 4")
	p.items["foundation_pill"] = 1
	check(g.perform("check_trial", {"safe": true}).ok, "trial ok")
	check(g.perform("complete_trial").ok, "complete")
	check(p.realm == 2 and not p.items.has("foundation_pill") and p.insight == 20, "applied")


func t_mastery() -> void:
	var g := fresh()
	g.create_character(0, "C", "plum_bob", "river_traveler", "sword")
	g.select(0)
	var p: Dictionary = g.p
	p.items["steel_sword"] = 1
	p.items["training_spear"] = 1
	check(not g.perform("equip", {"id": "steel_sword"}).ok, "gated")
	for i in 60:
		g.perform("mastery_hit", {"family": "sword"})
	check(g.perform("equip", {"id": "steel_sword"}).ok, "equip at 60")
	check(g.perform("learn", {"id": "crescent"}).ok, "learn crescent")
	check(g.perform("equip", {"id": "training_spear"}).ok, "swap")
	g.perform("mastery_hit", {"family": "spear"})
	check(p.mastery.sword == 60 and p.mastery.spear == 1, "both kept")
	check(not g.perform("learn", {"id": "spear_thrust"}).ok, "spear gated")


func t_commission() -> void:
	var g := fresh()
	g.clock_override = 1790000000
	g.create_character(0, "D", "plum_bob", "river_traveler", "spear")
	g.select(0)
	var p: Dictionary = g.p
	p.items["herb"] = 40
	p.coins = 0
	for i in 3:
		check(g.perform("commission", {"town": "jr_town", "id": "c_dew"}).ok, "commission %d" % i)
	check(not g.perform("commission", {"town": "jr_town", "id": "c_dew"}).ok, "cap")
	check(p.coins == 90, "coins 90 got %d" % p.coins)
	check(not g.perform("buy", {"id": "lotus", "shop": "jr_town"}).ok, "not stocked")
	check(g.perform("buy", {"id": "mend_pill", "shop": "jr_town"}).ok and p.coins == 15, "markup")


func t_storage() -> void:
	var g := fresh()
	g.create_character(0, "E", "plum_bob", "river_traveler", "spear")
	g.create_character(1, "F", "plum_bob", "river_traveler", "spear")
	g.select(0)
	g.p.items["copper"] = 5
	check(g.perform("deposit", {"id": "copper", "n": 5}).ok and g.save.bank.copper == 5, "deposit")
	g.select(1)
	check(g.perform("withdraw", {"id": "copper", "n": 3}).ok, "withdraw")
	check(g.p.items.copper == 3 and g.save.bank.copper == 2, "counts")


func t_migration() -> void:
	var path := "user://test_legacy.json"
	var legacy := {"version": 3, "shared_storage": {"copper": 7}, "characters": [
		{"name": "Old Hand", "level": 6, "xp": 10, "realm_index": 2, "cultivation": 88, "mastery": {"sword": 5, "spear": 44},
		 "inventory": {"steel_spear": 1, "lotus": 3, "herb": 2}, "coins": 555, "weapon": "steel_spear", "hair": "topknot",
		 "outfit": "crimson_adept", "meridians": 3, "chapter": 1}, null, null]}
	for f in [path, path + ".backup-v3"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	var fa := FileAccess.open(path, FileAccess.WRITE)
	fa.store_string(JSON.stringify(legacy))
	fa.close()
	var g: Node = GameScript.new()
	g.save_path = path
	g.load_save()
	check("migrated" in g.notice, "notice")
	var p: Dictionary = g.save.slots[0]
	check(p.realm == 2 and p.insight == 88 and p.essence == 0, "realm/insight kept, not relabelled")
	check(p.equip.weapon == "steel_spear" and p.mastery.spear == 60, "weapon + credited mastery")
	check(p.meridians.size() == 3 and p.coins == 555, "meridians/coins")
	check(p.quests.ch1.state == "complete" and p.quests.ch2.state == "active", "campaign")
	check(int(g.save.bank.copper) == 7 and FileAccess.file_exists(path + ".backup-v3"), "bank + backup")
	var g2: Node = GameScript.new()
	g2.save_path = path
	g2.load_save()
	check(g2.notice == "", "no second migration")
	check(JSON.stringify(g2.save.slots[0].items) == JSON.stringify(p.items), "no duplicate grants")
	g.free(); g2.free()


func t_future() -> void:
	var path := "user://test_future.json"
	var text := JSON.stringify({"version": 99, "slots": []})
	var fa := FileAccess.open(path, FileAccess.WRITE)
	fa.store_string(text)
	fa.close()
	var g: Node = GameScript.new()
	g.save_path = path
	g.load_save()
	check(g.read_only, "read only")
	g.create_character(0, "X", "plum_bob", "river_traveler", "spear")
	check(FileAccess.get_file_as_string(path) == text, "untouched")
	g.free()


func t_assign() -> void:
	var g := fresh()
	g.clock_override = 1790000000
	g.create_character(0, "G", "plum_bob", "river_traveler", "spear")
	g.select(0)
	check(g.perform("assign", {"kind": "mining"}).ok, "assign")
	g.clock_override += 48 * 3600
	check(g.perform("collect_assignment").ok, "collect")
	check(R.count(g.p, "copper") == 40, "capped at 40")
	check(not g.perform("collect_assignment").ok, "no double claim")


func t_seal() -> void:
	var g := fresh()
	g.create_character(0, "H", "plum_bob", "river_traveler", "spear")
	g.select(0)
	check(not g.perform("seal_prime").ok, "needs shards")
	g.p.items["spirit_shard"] = 3
	check(g.perform("seal_prime").ok and g.perform("seal_prime").ok, "idempotent")
	check(R.count(g.p, "spirit_shard") == 1, "consumed once")
	check(g.perform("seal_complete").ok and g.p.flags.seal_repaired, "repaired")
