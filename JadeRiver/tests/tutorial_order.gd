extends "res://tests/prologue_run.gd"
## Tutorial order (docs/tutorial_order.md): a brand-new character plays the Prologue and the start of Act I in the
## order a player who heads for the fighting first would take it (Uncle Guo's fists before Granny Liu's remedy, the race
## early, Old Ma before Granny), taking and handing in every quest on the real dialogue page. After every step, and on
## every tick of the simulation, the tutorial's invariants hold:
##   1. no room with hostile foes is within reach, or entered, before the HP bar and the foes' HP bars are on the HUD;
##   2. every foe in a fight shows its HP bar, and the player's HP bar shows (the first fight: the Reed Shallows' crabs
##      and Reedtail Rats);
##   3. every way into a building in the rooms within reach shows a door (PortalView.entrance);
##   4. taking a quest closes the conversation, unless the same person has the next quest to give or take back;
##   5. what a quest's steps ask the player to press or open is on the HUD once the quest is taken.
## The steps are prologue_run's, in this order; prologue_run keeps its own (Granny first).
## Run headless:  godot --headless --path . res://tests/tutorial_order.tscn [-- --verbose] [--keep=<step>,...]
## --keep saves the character as it stands after the named steps (the labels below, e.g. "A Quiet River") to
## user://tutorial_cp/<step>/, for screenshots from a brand-new character (main.gd --load=... --load-slot).

## What each kind of step asks the player to press or open (invariant 5). A page or a system named by the step is
## looked up in PAGE_NEEDS and SYSTEM_NEEDS; QUEST_NEEDS adds what a step's kind does not say.
const NEEDS := {"collect": ["hud:context"], "talk_to": ["hud:context"], "use_portal": ["hud:context"], "deliver": ["hud:context"],
	"interact_object": ["hud:context"], "set_flag": ["hud:context"], "hit_object": ["hud:attack"],
	"kill": ["hud:attack", "hud:hp_bar", "hud:enemy_hp_bars"], "survive_timer": ["hud:attack", "hud:hp_bar", "hud:enemy_hp_bars"],
	"sell_item": ["hud:currency"], "buy_item": ["hud:currency"], "meditate_seconds": ["hud:cultivate"],
	"breakthrough": ["hud:cultivate", "hud:progress_bar"], "equip_slot": ["page:equipment"]}
const PAGE_NEEDS := {"inventory": "hud:bag", "cultivation": "page:cultivation"}
const SYSTEM_NEEDS := {"set_quick_use": "hud:quick_use", "guard": "hud:guard"}
const QUEST_NEEDS := {"the_runaway_kite": ["hud:jump"], "the_recruitment_fair": ["page:training_sect"]}

var views := Node2D.new()     # the EnemyViews the watcher asks, never processed or drawn
var foe_views := {}           # enemy uid -> EnemyView, for the room the character is in
var watched_room := ""
var foes_seen := {}           # def id -> times a foe of that kind was seen in a fight
var bare: Array = []          # foes seen in a fight without their HP bar (or with the HP bar off the HUD)
var doors_seen := {}          # room id -> true once its ways into buildings were checked
var hostile_reached: Array = []

func _main() -> void:
	add_child(views)
	run()
	print("tutorial_order: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ the walk
func run() -> void:
	start_new("user://test_saves_tutorial/")
	tick_watch = _watch_fight
	GameEvents.event.connect(_on_event)
	invariants("new character")
	step_morning_tide()
	invariants("Morning Tide")
	_no_trade_before_the_lesson()
	step_quiet_river()
	invariants("A Quiet River")
	step_fists()   # a player who goes to Guo first
	check(not Game.is_revealed("hud:hp_bar"), "Fists First alone does not put the HP bar on the HUD (Granny's Remedy does)")
	check(not routes().has("lf_reed_shallows"), "the Reed Shallows are out of reach after Fists First, before Granny's Remedy")
	invariants("Fists First")
	step_race()
	invariants("Race to the Tower")
	step_kite()
	invariants("The Runaway Kite")
	step_ma()
	_trade_after_the_lesson()
	invariants("Ma's Delivery")
	step_granny()
	invariants("Granny's Remedy")
	step_return()
	invariants("A Quiet River (Return)")
	step_crabs()
	if int(foes_seen.get("reedtail_rat", 0)) == 0: _rats()
	check(int(foes_seen.get("reedtail_rat", 0)) > 0, "the Reed Shallows' Reedtail Rats were fought, their HP bars watched (%s)" % str(foes_seen))
	invariants("Crab Trouble")
	step_evening()
	invariants("Evening on the River")
	step_night()
	invariants("The Hollow Night")
	step_river_token()
	invariants("The River Token")
	step_willow_path()
	invariants("The Willow Path")
	step_fair()
	invariants("The Recruitment Fair")
	step_grind_bf2()
	step_entry_trial()
	invariants("Entry Trial")
	step_chores()
	invariants("A Disciple's Chores")
	step_weapon_hall()
	invariants("The Weapon Hall")
	check(bare.is_empty() and foes_seen.size() >= 4, "every foe in every fight showed its HP bar beside the player's (%s; bare: %s)" % [str(foes_seen), str(bare.slice(0, 6))])
	check(not hostile_reached.is_empty() and hostile_reached[0] == "lf_reed_shallows",
		"the first room with foes within reach is the Reed Shallows, with Crab Trouble (%s)" % str(hostile_reached.slice(0, 4)))

## Take the rats on as well as the crabs, as a player crossing the shallows does (the reported fight).
func _rats() -> void:
	back_to("lf_reed_shallows")
	fight("reedtail_rat", 1, 60.0)
	back_to("lf_village")

## Chapter 1: sweep the three spots on Gate Street for the steward.
func step_chores() -> void:
	check(travel("ja_gate_street"), "the Jade Sect's road opens after the Entry Trial (room %s)" % room())
	check(c().quests.offered.has("a_disciples_chores") or c().quests.is_active("a_disciples_chores"), "A Disciple's Chores offered")
	accept("jade_steward", "a_disciples_chores")
	for i in 3:
		check(interact("sweep_ja_%d" % i).get("ok", false), "sweep spot %d" % i)
	hand_in("jade_steward", "a_disciples_chores")

## The Weapon Hall at Bone Forging 3: taken on the page, its rack, dummies and guard all on the HUD first.
func step_weapon_hall() -> void:
	var tries := 0
	while not ProgressionRules.at_least(c().cultivator.realm_key, "bone_forging_3") and tries < 12:
		if c().cultivator.state == "bottleneck":
			submit({"type": "start_breakthrough", "support_items": []})
			step(4.0)
		else:
			Game.progression.apply_progress(c().id, 0.0, "test_shortcut", 1.0)   # test shortcut: the Bone Forging 2 grind
			step(1.0)
		tries += 1
	check(ProgressionRules.at_least(c().cultivator.realm_key, "bone_forging_3"), "Bone Forging 3 (realm %s)" % c().cultivator.realm_key)
	check(travel("ja_weapon_hall"), "the Weapon Hall admits a Bone Forging 3 disciple (room %s)" % room())
	accept("jade_weapon_master", "the_weapon_hall")

# ------------------------------------------------------------------ the page
## Every quest is taken on the real dialogue page, which closes itself (or goes on to the same person's next quest).
func accept(npc: String, quest: String) -> void:
	check(_choose_on_page(npc, "accept", quest), "%s taken from %s on the dialogue page, and the talk closes itself (or goes on to their next quest)" % [quest, npc])
	_needs_on_hud(quest)

func hand_in(npc: String, quest: String) -> void:
	check(_choose_on_page(npc, "hand_in", quest), "%s handed in to %s on the dialogue page, and the talk closes itself (or goes on to their next quest)" % [quest, npc])

## Invariant 5: what the quest's steps ask for is on the HUD now that it is taken.
func _needs_on_hud(quest: String) -> void:
	var need: Array = QUEST_NEEDS.get(quest, []).duplicate()
	for o in ContentDB.entry("quests", quest).get("objectives", []):
		need.append_array(NEEDS.get(str(o.kind), []))
		if str(o.kind) == "open_page": need.append(str(PAGE_NEEDS.get(str(o.get("page", "")), "page:" + str(o.get("page", "")))))
		if str(o.kind) == "use_system" and SYSTEM_NEEDS.has(str(o.get("system", ""))): need.append(str(SYSTEM_NEEDS[str(o.system)]))
	var missing := need.filter(func(el): return not Game.is_revealed(str(el)))
	check(missing.is_empty(), "%s: what its steps ask for is on the HUD when it is taken (missing %s)" % [quest, str(missing)])

## Old Ma's Trade waits for Coins and Shops (the purse is not on the HUD before it): nothing to buy before the lesson.
func _no_trade_before_the_lesson() -> void:
	check(go("store_door") and room() == "lf_old_ma_store", "Old Ma's store can be entered from the start")
	var d: Dictionary = talk("old_ma")
	check(not (d.get("choices", []) as Array).any(func(ch): return ch.has("shop")), "no Trade with Old Ma before Ma's Delivery (%s)" % str(d.get("choices", [])))
	check(go("exit"), "back out of the store")

## ... and it opens with the lesson.
func _trade_after_the_lesson() -> void:
	check(go("store_door"), "back into Old Ma's store")
	var d: Dictionary = talk("old_ma")
	check((d.get("choices", []) as Array).any(func(ch): return ch.has("shop")), "Trade with Old Ma once Ma's Delivery is done (%s)" % str(d.get("choices", [])))
	check(go("exit"), "back out of the store")

# ------------------------------------------------------------------ the invariants
## Invariants 1 and 3 over every room within reach now.
func invariants(label: String) -> void:
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--keep=") and label in str(a).trim_prefix("--keep=").split(","):
			Game.save_all()
			_copy_dir(Saves.repo.root, "user://tutorial_cp/%s/" % label.to_lower().replace(" ", "_").replace("'", ""))
	var reach := routes()
	for rid in reach:
		var rd: Dictionary = ContentDB.room(rid)
		if hostile(rd):
			if not hostile_reached.has(rid): hostile_reached.append(rid)
			check(Game.is_revealed("hud:hp_bar") and Game.is_revealed("hud:enemy_hp_bars"),
				"%s: %s has foes, and is within reach only once the HP bar and the foes' HP bars are on the HUD" % [label, rid])
		if doors_seen.has(rid): continue
		doors_seen[rid] = true
		for p in rd.get("portals", []):
			if p.get("facade", false) or not PortalView.building_front(p, rd).is_empty():
				check(PortalView.entrance(p, rd) in ["building", "decor"], "%s: the way into a building %s:%s shows a door" % [label, rid, p.id])

## Foes the room would set on the character now: a spawn that is not passive and whose condition holds, or an event's.
func hostile(rd: Dictionary) -> bool:
	for sp in rd.get("spawns", []):
		if ContentDB.entry("enemies", str(sp.enemy)).get("passive", false): continue
		if sp.has("requires") and not RequirementRules.passes(sp.requires, Game.ctx()): continue
		return true
	var ev: Dictionary = rd.get("event", {})
	return (ev.has("wave") or ev.has("fixed_spawns")) and RequirementRules.passes(ev.get("requires", {}), Game.ctx())

func _on_event(n: String, p: Dictionary) -> void:
	if n != "room_entered": return
	if hostile(ContentDB.room(str(p.get("room", "")))):
		check(Game.is_revealed("hud:hp_bar") and Game.is_revealed("hud:enemy_hp_bars"), "entering %s, a room with foes, the HP bars are on the HUD" % str(p.room))

## Invariant 2, on every tick: each foe in a fight (the real EnemyView asked, kept in step with it) shows its HP bar,
## and so does the player.
func _watch_fight() -> void:
	var rt: RoomRuntime = Game.room_rt
	if rt == null: return
	if rt.room_id != watched_room:
		for v in foe_views.values(): v.free()
		foe_views.clear()
		watched_room = rt.room_id
	for e in rt.living_enemies():
		if e.team != "enemy" or not e.in_fight(): continue
		var v: EnemyView = foe_views.get(e.uid)
		if v == null:
			v = EnemyView.new()
			v.setup(e)
			v.set_process(false)
			views.add_child(v)
			foe_views[e.uid] = v
			foes_seen[e.def_id] = int(foes_seen.get(e.def_id, 0)) + 1
		v.sync(e, 0.05)
		if (not v.shows_hp_bar(e) or not Game.is_revealed("hud:hp_bar")) and bare.size() < 40: bare.append("%s in %s" % [e.def_id, rt.room_id])
