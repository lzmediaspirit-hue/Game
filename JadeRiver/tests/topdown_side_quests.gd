extends "res://tests/prologue_run.gd"
## topdown_side_quests (audit 45 §6.5, E5: the quest engine; docs/architecture/quest_engine.md): a side quest the engine
## wrote from a spec that names only its giver, its step and its words, played on the height grid by a top-down
## character. Claws for the Grindstone (tools/content/quests/specs/valley_new.py): Apprentice Tao on Artisan Row wants
## five Ironclaw Mole claws. The engine derived where it leads (the Lower Pit, where the moles that drop the claws
## spawn), when it opens (the realm of the middle of the Lower Pit's band of Levels, Bone Forging 6) and what it pays
## (the band table at its tier). Test shortcuts carry a new character past chapter 2 (the story before it done, the
## prologue's systems) with a sturdy body (the fight is the room's, not the balance's); from there it is played through
## the World and Quest authorities:
##   1. at Bone Forging 5 Apprentice Tao does not offer it; at Bone Forging 6 he does, and it is taken;
##   2. its tracker leads to the Lower Pit, on the grid; the walk there from Artisan Row goes out by Stoneford Gate and
##      the quarry road, every room on the grid;
##   3. in the Lower Pit Ironclaw Moles are fought until five claws are in the bag, and the quest is ready;
##   4. back on Artisan Row it is handed in: the five claws are taken, and it pays what its row says, which is the band
##      table's at its tier: the side share of Bone Forging's need (+310 cultivation) and the band's 90 taels.
## Run headless:  godot --headless --path . res://tests/topdown_side_quests.tscn [-- --verbose]

const QUEST := "claws_for_the_grindstone"
const GIVER := "apprentice_tao"
const ROOMS := ["sf_market", "sf_gate", "sq_quarry_rim", "sq_lower_pit"]

var entered := {}   # room -> on the grid when entered

func _main() -> void:
	start_new("e5/")
	_past_chapter2()
	GameEvents.event.connect(_on_room)
	_offered()
	_to_the_pit()
	_the_claws()
	_handed_in()
	end_suite()

# ------------------------------------------------------------------ the shortcut past chapter 2
## The story's prologue and main quests of chapters 1 and 2 done, the prologue's systems and scenes, Bone Forging 5, a
## sturdy body (a test shortcut: the quest is about its room), on Artisan Row.
func _past_chapter2() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		if str(q.get("kind", "")) in ["prologue", "main"] and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 2)):
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("bone_forging_5")
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 400.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 9000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 200.0, "source": "test:sturdy"}])
	_whole()
	Game.world.load_room(c(), "sf_artisan_row", "east")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "sf_artisan_row" and Game.room_rt.topdown != null, "on Artisan Row, on the grid (room %s)" % room())

## A realm set outright (a test shortcut), its unlocks and the quests on offer evaluated.
func _realm(key: String) -> void:
	c().cultivator.realm_key = key
	c().cultivator.state = "cultivating"
	c().cultivator.qp = 0.0
	Unlocks.evaluate(c().id)
	Game.quest.refresh_offers()
	GameEvents.flush()
	_whole()

func _whole() -> void:
	Game.combat.refresh_stats(c().id)
	c().pools.hp = c().pools.max_hp

func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	if room() in ROOMS and not entered.has(room()): entered[room()] = Game.room_rt.topdown != null

# ------------------------------------------------------------------ 1: offered at the realm the engine derived
func _offers_it() -> bool:
	for ch in talk(GIVER).get("choices", []):
		if str(ch.get("accept", "")) == QUEST: return true
	return false

func _offered() -> void:
	var def: Dictionary = ContentDB.entry("quests", QUEST)
	var floor := ""
	for r in def.get("requires", {}).get("all", []):
		if str(r.get("kind", "")) == "realm_at_least": floor = str(r.realm)
	check(floor == "bone_forging_6" and str(def.get("target_room", "")) == "sq_lower_pit" and str(def.get("giver", "")) == GIVER,
		"the engine's row: Apprentice Tao's, leading to the Lower Pit, open from Bone Forging 6 (%s, %s)" % [floor, def.get("target_room", "")])
	check(not _offers_it(), "at Bone Forging 5 Apprentice Tao does not offer Claws for the Grindstone")
	_realm("bone_forging_6")
	check(_offers_it(), "at Bone Forging 6 he does")
	accept(GIVER, QUEST)

# ------------------------------------------------------------------ 2: to the Lower Pit, on the grid
func _leads(target: String) -> bool:
	for e in Game.quest.tracker(c()):
		if str(e.get("quest", "")) == QUEST: return str(e.get("target_room", "")) == target and TopdownRoom.has_layout(target)
	return false

func _to_the_pit() -> void:
	check(_leads("sq_lower_pit"), "its tracker leads to the Lower Pit, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	check(travel("sq_lower_pit") and Game.room_rt.topdown != null, "to the Lower Pit on the grid, by Stoneford Gate and the quarry road (room %s)" % room())
	var missed := ROOMS.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of the way was entered on the grid (%s; missed %s)" % [str(entered.keys()), str(missed)])

# ------------------------------------------------------------------ 3: the claws
func _the_claws() -> void:
	var fights := 0
	while c().inventory.count("mole_claw") < 5 and fights < 40:
		fight("ironclaw_mole", 1, 90.0)
		fights += 1
		_whole()
	GameEvents.flush()
	var stq: Dictionary = c().quests.active.get(QUEST, {})
	check(c().inventory.count("mole_claw") >= 5 and str(stq.get("state", "")) == "ready",
		"five Ironclaw Mole claws in the bag after %d fights, and the quest is ready (%d claws, %s)" % [fights, c().inventory.count("mole_claw"), stq.get("state", "-")])

# ------------------------------------------------------------------ 4: handed in, paid the band's
func _handed_in() -> void:
	check(travel("sf_artisan_row"), "back to Apprentice Tao on Artisan Row (room %s)" % room())
	var def: Dictionary = ContentDB.entry("quests", QUEST)
	var pay := 0
	for e in def.get("rewards", []):
		if str(e.get("kind", "")) == "grant_currency" and str(e.get("currency", "")) == "silver_tael": pay += int(e.get("amount", 0))
	var lv := int(ContentDB.realm(str(def.get("tier", ""))).get("level", 0))
	check(int(def.get("cultivation", 0)) == ProgressionRules.quest_cultivation("side", lv) and int(def.get("cultivation", 0)) == 310 and pay == 90,
		"its row pays the band table's at its tier %s: +%d cultivation (the side share of the stage), %d taels" % [def.get("tier", ""), int(def.get("cultivation", 0)), pay])
	var gained := {"qp": 0.0}
	var heard := func(n: String, p: Dictionary):
		if n == "progress_changed" and str(p.get("actor", "")) == str(c().id) and str(p.get("source", "")) == "quest": gained.qp += float(p.get("amount", 0.0))
	GameEvents.event.connect(heard)
	var claws: int = c().inventory.count("mole_claw")
	var taels: int = Game.economy.balance("silver_tael", c())
	hand_in(GIVER, QUEST)
	GameEvents.flush()
	GameEvents.event.disconnect(heard)
	check(c().inventory.count("mole_claw") == claws - 5, "the five claws are taken (%d left of %d)" % [c().inventory.count("mole_claw"), claws])
	check(int(gained.qp) == int(def.get("cultivation", 0)) and Game.economy.balance("silver_tael", c()) - taels == pay,
		"it pays +%d cultivation and %d taels (the row: +%d, %d)" % [int(gained.qp), Game.economy.balance("silver_tael", c()) - taels, int(def.get("cultivation", 0)), pay])
