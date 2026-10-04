extends "res://tests/prologue_run.gd"
## Tutorial order (docs/tutorial_order.md): a brand-new character plays the Prologue and the start of Act I in the
## order a player who heads for the fighting first would take it (Uncle Guo's fists before Granny Liu's remedy, the race
## early, Old Ma before Granny), taking and handing in every quest on the real dialogue page. After every step, and on
## every tick of the simulation, the tutorial's invariants hold:
##   1. no room with hostile foes is within reach, or entered, before the HP bar and the foes' HP bars are on the HUD;
##   2. every foe in a fight shows its HP bar, and the player's HP bar shows (the first fight: the Reed Shallows' crabs
##      and Reedtail Rats);
##   3. every way into a building in the rooms within reach shows a door (TopdownRoom.entrance);
##   4. taking or handing in a quest closes the conversation (decision 42: even when the same person has the next quest
##      to give or take back);
##   5. what a quest's steps ask the player to press or open is on the HUD once the quest is taken, and the control is
##      drawn (the real HUD asked, at rest) while the step is open; the healing slot stays drawn while it holds something;
##   6. no room is left before the steps it holds you to are done: a quest whose step is to leave its room keeps its
##      ways shut (and says why) until it is taken and the steps before it are done; and no door is kept shut for a
##      menu lesson (Morning Tide is under way from waking, its door open);
##   7. the story's guidance (prologue_run.story_guidance): the tracker never empty, its targets real rooms the player
##      can walk to, between main quests its next one (who gives it and where, or the Level and where to hunt), and
##      right after the sect choice the membership recorded and the sect's first quest at the head of the tracker;
##   8. in a fight the attack button attacks, whatever the world offers in reach (the first fight is beside the Reed
##      Shallows' herbs): the offer waits in the context slot on ring 2 (HUD.attack_first);
##   9. after every step the tracker and the direction mark lead where the story really goes next (leads_to_next): a
##      quest under way, one to take now, a lesson on offer (at Bone Forging 3 the Weapon Hall, not the hunt for the next
##      Level), and only with none of these a hunting ground;
##  10. the weapon slot is open from the start (empty, not locked, a weapon wearable), and the first weapon, dropped by
##      the first kill in the Reed Shallows, is offered by the HUD's equip prompt;
##  11. chores after power (docs/research/player_motivation.md item 6, P3): no daily, idle or post system (an unlock
##      marked `obligation`) is open or on offer at any step of the walk;
##  12. a gentle early failure (P12): every fall in the walk costs nothing;
##  13. early surprises (item 7, P7): the first walk onto the Willow Path after the River Token meets a fortune card (the
##      Remnant Soul in a Ring), and as The Willow Path is done a Spirit Fruit ripens on Willow Path West, announced.
##  14. the first hour pays (research player_motivation P1, P2): the story's own quests and fights carry the character
##      to every realm the story waits on (Bone Forging 2 for chapter 2, 3 for the Weapon Hall) with no test shortcut;
##      on the play clock (prologue_run.play_s) something new comes at least every 3 minutes to minute 20 and every 5
##      to minute 60 (an item kind, gear worn, a technique, a realm step, a new foe beaten, a title, a choice, coin);
##      the first technique is taught at Bone Forging 1 and the second at the Weapon Hall. The timeline is printed.
##  15. decision 42 (the prototype APK's feedback): at rest, the fan open or closed, the HUD draws Attack and the
##      techniques as in a fight, each only once it is unlocked (Attack once it is on the HUD, a square for each art in a
##      slot once the techniques are, Jump and Dodge once theirs are), and nothing before; a person in reach has the
##      context's own button and never takes Attack's place.
## The steps are prologue_run's, in this order; prologue_run keeps its own (Granny first).
## Run headless:  godot --headless --path . res://tests/tutorial_order.tscn [-- --verbose] [--keep=<step>,...]
## --keep saves the character as it stands after the named steps (the labels below, e.g. "A Quiet River"), or at the
## points inside them prologue_run names ("Morning Tide teas", "Granny's Remedy taken", "Both recruiters met"), to
## user://tutorial_cp/<step>/, for screenshots from a brand-new character (main.gd --load=... --load-slot).
const PlayerStub = preload("res://tests/lib/player_stub.gd")

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
const CharacterPage = preload("res://scripts/ui/pages/character_page.gd")
## The HUD's own control for each element a step can name (its role in HUD.hit_targets): drawn, not only revealed.
const CONTROLS := {"hud:quick_use": "quick:0", "hud:jump": "jump", "hud:guard": "guard", "hud:bag": "icon:bag", "hud:menu": "icon:menu",
	"hud:map": "icon:map", "hud:cultivate": "meditate"}

const BuildingWays = preload("res://tests/lib/building_ways.gd")
var views := Node2D.new()     # the EnemyViews the watcher asks, never processed or drawn
var hud_probe: Control        # the real HUD, bound to the character through a stand-in player; asked, never drawn
var left_early: Array = []    # rooms left before the steps they hold you to were done
var offers_in_fight := {}     # context type -> ticks of a fight with it in reach (invariant 8)
var hijacked: Array = []      # fight ticks when an offer in reach took the attack button
var teasers: Array = []       # a locked resource node offered by the context button (never, since the prototype's polish)
var foe_views := {}           # enemy uid -> EnemyView, for the room the character is in
var watched_room := ""
var foes_seen := {}           # def id -> times a foe of that kind was seen in a fight
var bare: Array = []          # foes seen in a fight without their HP bar (or with the HP bar off the HUD)
var doors_seen := {}          # room id -> true once its ways into buildings were checked
var hostile_reached: Array = []
var novelty: Array = []       # [play seconds, kind, what]: the first-hour timeline (invariant 14)
var novel_seen := {}
var surprises: Array = []     # "fortune:<card>@<room>", "fruit@<room>": the early surprises met (invariant 13)
var falls: Array = []         # falls in the walk that cost something (invariant 12)

func _main() -> void:
	add_child(views)
	run()
	free_hud_probe()
	end_suite()

# ------------------------------------------------------------------ the walk
func run() -> void:
	start_new("saves/")
	tick_watch = _watch_fight
	GameEvents.event.connect(_on_event)
	GameEvents.event.connect(_on_novelty)
	watch_story()
	_bind_hud_probe()
	invariants("new character")
	_weapon_slot_open()
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
	step_crabs()
	_first_weapon_offered()
	if int(foes_seen.get("reedtail_rat", 0)) == 0 or offers_in_fight.is_empty(): _rats()
	check(int(foes_seen.get("reedtail_rat", 0)) > 0, "the Reed Shallows' Reedtail Rats were fought, their HP bars watched (%s)" % str(foes_seen))
	invariants("Crab Trouble")
	_wear_new_gear()
	step_evening()
	invariants("Evening on the River")
	step_night()
	invariants("The Hollow Night")
	step_river_token()
	invariants("The River Token")
	step_willow_path()
	invariants("The Willow Path")
	_early_surprises()
	step_fair()
	invariants("The Recruitment Fair")
	step_entry_trial()
	invariants("Entry Trial")
	step_fish_gutting_fists()
	invariants("Fish-Gutting Fists")
	step_chores()
	invariants("A Disciple's Chores")
	step_weapon_hall()
	invariants("The Weapon Hall")
	step_strange_tracks()
	invariants("Strange Tracks")
	first_hour()
	check(not hostile_reached.is_empty() and hostile_reached[0] == "lf_reed_shallows",
		"the first room with foes within reach is the Reed Shallows, with Crab Trouble (%s)" % str(hostile_reached.slice(0, 4)))
	walk_held("the walk")

## What the walk held to on every tick and every step (invariants 2, 6, 7, 8 and 12), over all of it so far.
func walk_held(label: String) -> void:
	check(bare.is_empty() and foes_seen.size() >= 4, "%s: every foe in every fight showed its HP bar beside the player's (%s; bare: %s)" % [label, str(foes_seen), str(bare.slice(0, 6))])
	check(left_early.is_empty(), "%s: no room was left before the steps it holds you to were done (%s)" % [label, str(left_early)])
	check(hijacked.is_empty() and not offers_in_fight.is_empty(),
		"%s: in every fight the attack button attacked, all in reach waiting in the ring-2 slot (%s; hijacked: %s)" % [label, str(offers_in_fight), str(hijacked)])
	check(teasers.is_empty(), "%s: no resource node the character cannot work yet took the context button (the shore's herbs before herb gathering; %s)" % [label, str(teasers.slice(0, 4))])
	check(guidance_steps >= c().quests.done.size() + c().quests.active.size(), "%s: the story's guidance was checked at every step (%d steps, %d quests)"
		% [label, guidance_steps, c().quests.done.size() + c().quests.active.size()])
	check(falls.is_empty(), "%s: every fall in the walk cost nothing, before Bone Forging 5 (%s)" % [label, str(falls)])

func free_hud_probe() -> void:
	hud_probe.player.free()
	hud_probe.free()

## The weapon slot is open from the start: a brand-new character fights bare-handed, the Character and Bag pages draw
## the slot empty, not locked, and a training weapon may be worn at once.
func _weapon_slot_open() -> void:
	check(c().inventory.equipped.get("weapon") == null and CharacterPage.locked_reason(c(), "weapon") == ""
		and Game.inventory.wear_check(c(), ContentDB.item("training_jian")) == "",
		"a new character's weapon slot is open and empty: bare fists, and a training weapon may be worn (%s)" % Game.inventory.wear_check(c(), ContentDB.item("training_jian")))

## The first weapon, picked up in the Reed Shallows, is offered by the HUD's equip prompt (better than the gauntlets).
func _first_weapon_offered() -> void:
	hud_probe.equip_prompt.tick(c(), 0.0)
	var cur: Dictionary = hud_probe.equip_prompt.current
	check(str(cur.get("slot", "")) == "weapon" and str(ContentDB.item(str(cur.get("item", ""))).get("family", "")) == str(LootRules.drop_cfg().starter.first_family)
		and not (cur.get("cp", {}) as Dictionary).is_empty(), "the first weapon is offered by the equip prompt, its Combat Power rise shown (%s)" % str(cur))

## Take the rats on as well as the crabs, beside the shore's herbs, as a player crossing the shallows does (the
## reported fight). An armed player can clear the crabs before any rat comes near a herb, so the walk waits by one.
func _rats() -> void:
	back_to("lf_reed_shallows")
	var herb := obj_at("herb_7")
	for i in 12:
		place(herb - Vector2(20, 0))
		if Game.room_rt.living_enemies().any(func(e): return e.def_id == "reedtail_rat" and e.plane.distance_to(herb) < 200.0): break
		step(5.0)
	fight("reedtail_rat", 1, 60.0)
	back_to("lf_village")

## A Disciple's Chores, a side errand now (research §3.3): two spots at the sect's gate (Gate Street, the Cliff Stair),
## and the third is the grey itself, with a cache under the flagstone.
func step_chores() -> void:
	check(travel(sect_at("gate")), "the sect's road opens after the Entry Trial (room %s)" % room())
	check(c().quests.offered.has("a_disciples_chores") or c().quests.is_active("a_disciples_chores"), "A Disciple's Chores offered")
	check(str(ContentDB.entry("quests", "a_disciples_chores").get("kind", "")) == "side", "A Disciple's Chores is a side errand, not the story")
	accept(sect_at("steward"), "a_disciples_chores")
	var spots: Array = Game.room_rt.def.get("objects", []).filter(func(o): return str(o.get("set_flag", "")).begins_with("swept_"))
	check(spots.size() == 3, "three spots to sweep at the gate (%d)" % spots.size())
	for o in spots:
		check(interact(str(o.id)).get("ok", false), "sweep %s" % o.id)
	hand_in(sect_at("steward"), "a_disciples_chores")
	check(c().inventory.count("spirit_stone_shard") >= 2, "the third spot's cache: two spirit stone shards")

## Chapter 2 (its floor Bone Forging 2, research §5 change 5) opens the moment the Weapon Hall is done: the mentor's
## note starts Strange Tracks, three grey patches in the Reed Marsh. Decision 42 (less walking in the sect stretch): the
## same moment the disciple's token opens the sect's transfer arrays (the Marsh Edge's watch post keyed to it), and
## the note is done at the third patch, where the River Token hums and The Humming Token begins on the spot: no walk
## back up the mentor's peak and down again.
func step_strange_tracks() -> void:
	check(str(ContentDB.config("quests").get("chapter_floors", {}).get("2", "")) == "bone_forging_2" and c().quests.is_active("strange_tracks"),
		"chapter 2's floor is Bone Forging 2, and Strange Tracks is under way the moment the Weapon Hall is done (realm %s)" % c().cultivator.realm_key)
	check(Unlocks.is_unlocked(c().id, "transfer_array") and c().quests.has_flag("array_array_marsh") and c().quests.has_flag("array_array_ja_gate"),
		"the Weapon Hall done, the token opens the sect's transfer arrays, the gate's and the Marsh Edge's watch post keyed to it")
	GameEvents.flush()
	var nx: Array = Game.quest.tracker(c())
	check(not nx.is_empty() and str(nx[0].get("quest", "")) == "strange_tracks" and str(nx[0].get("target_room", "")) == "rm_marsh_edge",
		"the tracker leads with Strange Tracks, to the Marsh Edge (%s)" % str(nx.slice(0, 1)))
	check(travel("rm_marsh_edge"), "the marsh path is open at Bone Forging 2 (room %s)" % room())
	check(fight("reed_frog", 1, 90.0, 0.35) == 1, "a Reed Frog beaten on the marsh path")
	var seen := 0
	for o in Game.room_rt.def.get("objects", []):
		if seen < 3 and str(o.get("type", "")) == "inspect" and Game.world.object_visible(c(), o) and interact(str(o.id)).get("ok", false): seen += 1
	check(seen == 3, "three grey patches inspected (%d)" % seen)
	GameEvents.flush()
	check(c().quests.is_done("strange_tracks") and c().quests.is_active("the_humming_token"),
		"Strange Tracks is done at the third patch and The Humming Token under way on the spot, no walk back to the mentor")
	nx = Game.quest.tracker(c())
	var token: Array = nx.filter(func(e): return str(e.get("quest", "")) == "the_humming_token")
	check(not token.is_empty() and str(token[0].get("target_room", "")) == room(), "the tracker keeps the player at the Marsh Edge for the grey boarlets (%s)" % str(token.slice(0, 1)))

## The gear Crab Trouble paid, worn from the Bag as the equip prompt offers it, and Ping's bone broth drunk (the body a
## few levels stronger for good, before the night and the Willow Path).
func _wear_new_gear() -> void:
	for id in ["plain_straw_hat"]:
		var i: int = c().inventory.first_index(id)
		if i >= 0: check(submit({"type": "equip", "index": i}).get("ok", false), "wear the %s" % id)
	var body: int = c().cultivator.body_level
	var broth: int = c().inventory.first_index("boar_bone_broth")
	check(broth >= 0 and submit({"type": "use_item", "index": broth, "confirm": true}).get("ok", false) and c().cultivator.body_level > body,
		"drink Crab Trouble's Boar Bone Broth: the body level rises for good (%d to %d)" % [body, c().cultivator.body_level])

## The Weapon Hall at Bone Forging 3: taken on the page, its rack, dummies and guard all on the HUD first; done, it
## teaches the first art of the family in hand (the second technique).
func step_weapon_hall() -> void:
	check(break_through("bone_forging_3"), "the story's own quests and fights carry the character to Bone Forging 3, no hunting (realm %s, %d%%)"
		% [c().cultivator.realm_key, int(100.0 * c().cultivator.progress_fraction())])
	# Chapter 2 (Strange Tracks) waits on the Weapon Hall: the tracker's Next and the direction mark lead there, not to
	# a hunting ground.
	GameEvents.flush()
	var nx: Array = Game.quest.tracker(c())
	var hall := Game.quest.npc_rooms(c(), QuestAuthority.own_npc(c(), ContentDB.entry("quests", "the_weapon_hall").get("giver_any", [])))
	check(not nx.is_empty() and str(nx[0].get("quest", "")) == "the_weapon_hall" and hall.has(str(nx[0].get("target_room", "")))
		and (room() == str(nx[0].target_room) or Game.world.guide_target(c()) == str(nx[0].target_room)),
		"at Bone Forging 3 the tracker's Next is The Weapon Hall and the mark leads to it (%s; mark %s)" % [str(nx.slice(0, 1)), Game.world.guide_target(c())])
	leads_to_next("Bone Forging 3")
	keep("Bone Forging 3")
	check(travel(sect_at("weapon_hall")), "the Weapon Hall admits a Bone Forging 3 disciple (room %s)" % room())
	var had_gauntlets: int = c().inventory.count_including_equipped("training_gauntlets")
	accept(sect_at("weapon_master"), "the_weapon_hall")
	# The rack hands out what the disciple lacks: the sect's own weapon (the jian, the staff) and the spear, never a
	# second pair of Uncle Guo's gauntlets (the prototype's polish).
	check(had_gauntlets >= 1 and c().inventory.count_including_equipped("training_gauntlets") == had_gauntlets
		and ["training_jian", "training_spear", "training_staff"].all(func(w): return c().inventory.count_including_equipped(w) == 1),
		"the Weapon Hall's rack hands out the jian, the spear and the staff, once each, and no second pair of gauntlets (%d gauntlets)" % c().inventory.count_including_equipped("training_gauntlets"))
	var jian: int = c().inventory.first_index("training_jian")
	check(jian >= 0 and submit({"type": "equip", "index": jian}).get("ok", false), "take the training jian from the rack")
	var dummies: Array = Game.room_rt.def.get("objects", []).filter(func(o): return str(o.get("type", "")) == "training_dummy")
	check(not dummies.is_empty(), "the Weapon Hall's dummies stand in it")
	if not dummies.is_empty(): hit_object(str(dummies[0].id), 5)
	submit({"type": "guard_start"})
	step(0.3)
	submit({"type": "guard_end"})
	hand_in(sect_at("weapon_master"), "the_weapon_hall")
	check(c().cultivator.techniques_known.has("cloudpiercing_stroke") and c().cultivator.technique_slots.has("cloudpiercing_stroke"),
		"the Weapon Hall teaches the jian's first art, slotted beside Flowing Palm (%s)" % str(c().cultivator.technique_slots))

## Chapter 1: Shen Lian's spar at the Fairground, the first thing the Entry Trial leads to (the chores are a side errand).
func step_fish_gutting_fists() -> void:
	check(travel("sf_fairground"), "back to the Fairground (room %s)" % room())
	accept("shen_lian", "fish_gutting_fists")
	var won := false
	for i in 3:
		won = spar_with(func(): return _spar_service("shen_lian"))
		if won: break
	check(won, "beat Shen Lian in a spar")
	GameEvents.flush()
	hand_in("shen_lian", "fish_gutting_fists")
	check(c().cultivator.state == "bottleneck" or ProgressionRules.at_least(c().cultivator.realm_key, "bone_forging_3"),
		"Fish-Gutting Fists fills Bone Forging 2 by itself: the Weapon Hall's realm needs no side errand (%d%%)" % int(100.0 * c().cultivator.progress_fraction()))

# ------------------------------------------------------------------ the first hour (invariant 14)
## Something new, on the play clock: an item kind, gear worn, a technique, a realm step, a new foe beaten, a title, the
## sect chosen, the first coin, a new place (a region entered the first time), a set piece begun. Each counts once.
func _on_novelty(n: String, p: Dictionary) -> void:
	if c() == null or (p.has("actor") and str(p.actor) != str(c().id)): return
	var what := ""
	match n:
		"item_added": what = "item:" + str(p.get("item", ""))
		"equipment_changed": what = "wear:" + str(p.get("new", ""))
		"technique_learned": what = "technique:" + str(p.get("technique", ""))
		"realm_changed": what = "realm:" + str(p.get("to", ""))
		"title_changed": what = "title:" + str(p.get("title", "")) if p.get("earned", false) else ""
		"sect_joined": what = "choice:sect"
		"currency_changed": what = "coin:" + str(p.get("currency", "")) if int(p.get("delta", 0)) > 0 else ""
		"actor_defeated": what = "foe:" + str(p.get("def", "")) if str(p.get("killer", "")) == str(c().id) else ""
		"room_entered": what = "place:" + str(ContentDB.room(str(p.get("room", ""))).get("region", ""))
		"room_event_started": what = "event:" + str(p.get("event", ""))
	if what == "" or novel_seen.has(what) or what == "wear:": return
	novel_seen[what] = true
	if n == "technique_learned" and not novelty.any(func(e): return str(e[1]) == "technique"):
		check(c().cultivator.realm_key == "bone_forging_1", "the first technique is taught at Bone Forging 1 (%s at %s)" % [what, c().cultivator.realm_key])
	novelty.append([play_s, what.get_slice(":", 0), what])

## Invariant 14: the gaps between new things on the play clock, and the timeline printed (docs/tutorial_order.md keeps it).
func first_hour() -> void:
	var worst20 := 0.0
	var worst60 := 0.0
	var last := 0.0
	var line := PackedStringArray()
	for e in novelty:
		var t := float(e[0])
		if t <= 20.0 * 60.0: worst20 = maxf(worst20, t - last)
		if t <= 60.0 * 60.0: worst60 = maxf(worst60, t - last)
		last = t
		line.append("%d:%02d %s" % [int(t) / 60, int(t) % 60, str(e[2])])
	print("first hour (play clock, %d new things in %.0f min): %s" % [novelty.size(), play_s / 60.0, ", ".join(line)])
	var techs := novelty.filter(func(e): return str(e[1]) == "technique")
	check(techs.size() >= 2, "two techniques in the first hour (%s)" % str(techs.map(func(e): return e[2])))
	check(worst20 <= 180.0, "something new at least every 3 minutes to minute 20 (longest gap %.1f min)" % (worst20 / 60.0))
	check(worst60 <= 300.0, "something new at least every 5 minutes to minute 60 (longest gap %.1f min)" % (worst60 / 60.0))
	check(play_s <= 75.0 * 60.0, "the walk from waking to the Weapon Hall's art fits the first hour and a bit (%.0f min)" % (play_s / 60.0))

# ------------------------------------------------------------------ the page
## Every quest is taken on the real dialogue page, which closes itself (decision 42: even when the same person has the
## next quest to give or take back).
func accept(npc: String, quest: String) -> void:
	check(_choose_on_page(npc, "accept", quest), "%s taken from %s on the dialogue page, and the talk closes itself" % [quest, npc])
	_needs_on_hud(quest)

func hand_in(npc: String, quest: String) -> void:
	check(_choose_on_page(npc, "hand_in", quest), "%s handed in to %s on the dialogue page, and the talk closes itself" % [quest, npc])

## Invariant 5: what the quest's steps ask for is on the HUD now that it is taken, its controls drawn.
func _needs_on_hud(quest: String) -> void:
	var need := _step_needs(quest, [])
	var missing := need.filter(func(el): return not Game.is_revealed(str(el)))
	check(missing.is_empty(), "%s: what its steps ask for is on the HUD when it is taken (missing %s)" % [quest, str(missing)])
	_controls_drawn(quest, need)

## What the steps of a quest ask the player to press or open (the elements of NEEDS, PAGE_NEEDS, SYSTEM_NEEDS and
## QUEST_NEEDS), of all its steps or, with `progress`, of those still to do.
func _step_needs(quest: String, progress: Array) -> Array:
	var need: Array = QUEST_NEEDS.get(quest, []).duplicate() if progress.is_empty() else []
	var objs: Array = ContentDB.entry("quests", quest).get("objectives", [])
	for i in objs.size():
		var o: Dictionary = objs[i]
		if not progress.is_empty() and int(progress[i]) >= int(o.get("count", 1)): continue
		need.append_array(NEEDS.get(str(o.kind), []))
		if str(o.kind) == "open_page": need.append(str(PAGE_NEEDS.get(str(o.get("page", "")), "page:" + str(o.get("page", "")))))
		if str(o.kind) == "use_system" and SYSTEM_NEEDS.has(str(o.get("system", ""))): need.append(str(SYSTEM_NEEDS[str(o.system)]))
		if str(o.kind) == "use_item" and str(o.get("item", "")) == str(c().inventory.quick_use): need.append("hud:quick_use")
	return need

## The controls of `need` are drawn on the real HUD at rest (the fan as the player leaves it), not only revealed.
func _controls_drawn(what: String, need: Array) -> void:
	hud_probe.set_state(false, hud_probe.fan_rest_open)
	var drawn: Array = hud_probe.hit_targets().map(func(tg): return str(tg.role))
	var hidden := need.filter(func(el): return CONTROLS.has(str(el)) and not drawn.has(str(CONTROLS[str(el)])))
	check(hidden.is_empty(), "%s: the controls its steps name are drawn on the HUD at rest (not drawn: %s; drawn: %s)" % [what, str(hidden), str(drawn)])

## The real HUD, bound to the character through a stand-in for the player (as the hud_suite binds it): asked what it
## draws, never processed or drawn itself.
func _bind_hud_probe() -> void:
	var stub_src: GDScript = PlayerStub   # the top-down player's shape (tests/lib/player_stub.gd)
	hud_probe = load("res://scripts/hud.gd").new()
	hud_probe.visible = false
	hud_probe.process_mode = Node.PROCESS_MODE_DISABLED
	add_child(hud_probe)
	hud_probe.player = stub_src.new()
	hud_probe.player.actor_id = str(Game.active_id)
	check(hud_probe.bound(), "the HUD probe is bound to the character")

## Invariant 6: a way out used while a quest whose step is to leave that room still holds it (not taken, or a step
## before the leaving one still to do).
func _left_early(p: Dictionary) -> void:
	var from := str(p.get("room", ""))
	for qid in c().quests.active.keys() + c().quests.offered.keys():
		var d: Dictionary = Game.quest.quest_def(c(), str(qid))
		var objs: Array = d.get("objectives", [])
		var leave := objs.map(func(o): return str(o.get("kind", ""))).find("use_portal")
		if str(d.get("target_room", "")) != from or leave < 0: continue
		var prog: Array = c().quests.active.get(qid, {}).get("progress", [])
		if prog.is_empty() or range(leave).any(func(j): return int(prog[j]) < int(objs[j].get("count", 1))): left_early.append("%s (%s)" % [from, qid])

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
## Invariant 9: the tracker leads where the story really goes next, the first of: a quest of the story under way (the
## room of its step); one to take now (its giver's room); a lesson (a guided quest) under way; a lesson on offer (its
## giver's room: the Weapon Hall at Bone Forging 3); else the Level the story waits on (a hunting ground). The tracker's
## lead and the direction mark go there.
func leads_to_next(label: String) -> void:
	if not Game.is_revealed("hud:quest_tracker") or Game.room_rt == null: return
	var here := room()
	var want := ""
	var why := ""
	for kinds in [QuestAuthority.STORY_KINDS, ["guided"]]:
		for q in c().quests.tracked:
			var d: Dictionary = Game.quest.quest_def(c(), str(q))
			var t := Game.quest.quest_target(c(), d, c().quests.active.get(q, {})) if c().quests.is_active(str(q)) else ""
			if str(d.get("kind", "")) in kinds and t != "" and t != here:
				want = t
				why = "%s under way" % q
				break
		if want != "": break
		if c().quests.active.keys().any(func(q): return str(Game.quest.quest_def(c(), str(q)).get("kind", "")) in kinds): return   # under way here
		for d in Game.quest.story_waiting(c(), kinds):
			if not Game.quest.can_offer(c(), d): continue
			var giver := QuestAuthority.own_npc(c(), d.get("giver_any", d.get("giver", "")))
			want = Game.quest.objective_room(c(), d, {"kind": "talk_to", "npc": giver}) if giver != "" else str(d.get("target_room", ""))
			why = "%s to take from %s" % [d.id, giver]
			break
		if want != "": break
	var mark := Game.world.guide_target(c())
	if want == "":
		check(mark == "" or str(ContentDB.room(mark).get("type", "")) == "field", "%s: with nothing to take, the tracker leads to a hunting ground for the Level (%s)" % [label, mark])
	elif want != here and not ContentDB.room(want).get("instanced", false):
		check(mark == want, "%s: the tracker leads where the story goes next, %s (%s; the mark leads to %s)" % [label, want, why, mark])

## Invariant 13, as The Willow Path is done: the fortune card met on the way in, and the Spirit Fruit ripe here.
func _early_surprises() -> void:
	check(surprises.size() >= 1 and str(surprises[0]).begins_with("fortune:remnant_ring@wp_"),
		"the first walk onto the Willow Path met the Remnant Soul in a Ring (%s)" % str(surprises))
	check(surprises.has("fruit@wp_west"), "a Spirit Fruit ripened on Willow Path West as The Willow Path was done (%s)" % str(surprises))
	var tree: Array = ContentDB.room("wp_west").get("objects", []).filter(func(o): return o.get("first", false))
	check(room() == "wp_west" and not tree.is_empty() and Game.world.object_visible(c(), tree[0]), "its tree stands in view on Willow Path West (room %s)" % room())
	keep("First Spirit Fruit")

## Invariant 11: no chore (an unlock marked `obligation`) is open or on offer before Qi Kindling 1.
func _no_chores(label: String) -> void:
	var open: Array = []
	for u in ContentDB.all("unlocks"):
		if u.get("obligation", false) and (Unlocks.is_unlocked(c().id, str(u.id)) or c().cultivator.offered.has(str(u.id))): open.append(str(u.id))
	check(open.is_empty(), "%s: no daily, idle or post system is open or on offer before Qi Kindling 1 (%s)" % [label, str(open)])

## Invariants 1 and 3 over every room within reach now.
func invariants(label: String) -> void:
	keep(label)
	leads_to_next(label)
	_no_chores(label)
	var reach := routes()
	for rid in reach:
		var rd: Dictionary = ContentDB.room(rid)
		if hostile(rd):
			if not hostile_reached.has(rid): hostile_reached.append(rid)
			check(Game.is_revealed("hud:hp_bar") and Game.is_revealed("hud:enemy_hp_bars"),
				"%s: %s has foes, and is within reach only once the HP bar and the foes' HP bars are on the HUD" % [label, rid])
		if doors_seen.has(rid): continue
		doors_seen[rid] = true
		# On the height grid every way into a building (tests/lib/building_ways.gd) stands in its building's doorway
		# (TopdownRoom.entrance).
		var grid: TopdownRoom = Game.world.grid_for(rid)
		for p in rd.get("portals", []):
			if not BuildingWays.into_building(p, rd): continue
			check(grid.entrance(str(p.id)) == "building", "%s: the way into a building %s:%s shows a door on the grid (%s)" % [label, rid, p.id, grid.entrance(str(p.id))])
	# Invariant 5, while the steps are open: the controls the steps still to do name are drawn; the healing slot stays
	# drawn, at rest too, while it holds something to drink (Granny's tea).
	var open: Array = []
	for qid in c().quests.active: open.append_array(_step_needs(str(qid), c().quests.active[qid].progress))
	if Game.is_revealed("hud:quick_use") and c().inventory.count(str(c().inventory.quick_use)) > 0: open.append("hud:quick_use")
	_controls_drawn(label, open)
	_rest_controls(label)

## Invariant 15 (decision 42): at rest Attack and the techniques are drawn as they are unlocked, and nothing before;
## what the world offers in reach has its own button.
func _rest_controls(label: String) -> void:
	var wrong: Array = []
	for open in [false, true]:
		hud_probe.set_state(false, open)
		hud_probe.context = {}
		var roles: Array = hud_probe.hit_targets().map(func(tg): return str(tg.role))
		var filled: int = range(4).filter(func(i): return hud_probe.slot_filled(i + hud_probe.skill_page * 4)).size()
		var want_skills: int = filled if Game.is_revealed("hud:skills") else 0
		if roles.has("attack") != Game.is_revealed("hud:attack"): wrong.append("attack (fan %s)" % open)
		if roles.count("skill") != want_skills: wrong.append("techniques %d of %d (fan %s)" % [roles.count("skill"), want_skills, open])
		for el in ["jump", "guard"]:
			if roles.has(el) != Game.is_revealed("hud:" + el): wrong.append("%s (fan %s)" % [el, open])
		hud_probe.context = {"type": "npc", "npc": "aunt_ping", "label": "Talk"}
		var with_ctx: Array = hud_probe.hit_targets().map(func(tg): return str(tg.role))
		if not with_ctx.has("context") or with_ctx.has("attack") != roles.has("attack") or with_ctx.count("skill") != roles.count("skill"): wrong.append("the context (fan %s)" % open)
		hud_probe.context = {}
	hud_probe.set_state(false, hud_probe.fan_rest_open)
	check(wrong.is_empty(), "%s: at rest Attack (%s) and the techniques are drawn as they are unlocked, nothing before, and a person in reach has its own button (%s)"
		% [label, "on" if Game.is_revealed("hud:attack") else "not yet", str(wrong)])

## Foes the room would set on the character now: a spawn that is not passive and whose condition holds, or an event's.
func hostile(rd: Dictionary) -> bool:
	for sp in rd.get("spawns", []):
		if ContentDB.entry("enemies", str(sp.enemy)).get("passive", false): continue
		if sp.has("requires") and not RequirementRules.passes(sp.requires, Game.ctx()): continue
		return true
	var ev: Dictionary = rd.get("event", {})
	return (ev.has("wave") or ev.has("fixed_spawns")) and RequirementRules.passes(ev.get("requires", {}), Game.ctx())

func _on_event(n: String, p: Dictionary) -> void:
	if n == "portal_used": _left_early(p)
	if n == "fortune_encounter": surprises.append("fortune:%s@%s" % [str(p.get("card", "")), str(p.get("room", ""))])
	if n == "treasure_birth_announced" and p.get("first", false): surprises.append("fruit@%s" % str(p.get("room", "")))
	if n == "player_gravely_wounded" and not p.get("no_penalty", false): falls.append("%s at %s" % [room(), c().cultivator.realm_key])
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
	_attack_holds()

## Invariant 8, on every tick of a fight: whatever the world offers where the player stands (the shore's herbs in the
## Reed Shallows, a pickup, a person, a door), the attack button attacks (HUD.attack_first), and the offer waits in the
## context slot on ring 2.
func _attack_holds() -> void:
	var rt: RoomRuntime = Game.room_rt
	var me: ActorState = Game.actor_state(c().id)
	if hud_probe == null or me == null or not Unlocks.is_unlocked(c().id, "attack") or not rt.living_enemies().any(func(e): return e.team == "enemy" and e.in_fight()): return
	var ctx: Dictionary = Game.world.query_context(c())
	if ctx.is_empty(): return
	var node: Dictionary = rt.object_def(str(ctx.get("object", ""))) if ctx.has("object") else {}
	if not node.is_empty() and WorldAuthority.resource_node(node) and not ctx.get("ok", true) and teasers.size() < 20:
		teasers.append("%s:%s" % [rt.room_id, str(node.id)])
	hud_probe.player.plane = me.plane
	hud_probe.context = ctx
	hud_probe.fight_override = null
	hud_probe.tick_fight(0.05)
	offers_in_fight[str(ctx.get("type", ""))] = int(offers_in_fight.get(str(ctx.get("type", "")), 0)) + 1
	var slot: bool = hud_probe.hit_targets().any(func(tg): return str(tg.role) == "context")
	if (not hud_probe.attack_first() or hud_probe.attack_glyph(c()) != str(StatRules.family(c()).get("hud_glyph", "fist")) or not slot) and hijacked.size() < 20:
		hijacked.append("%s:%s in %s" % [str(ctx.get("type", "")), str(ctx.get("object", ctx.get("portal", ""))), rt.room_id])
