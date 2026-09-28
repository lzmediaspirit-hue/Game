class_name QuestAuthority
extends Authority
## S19 · Quests, objective progress, story flags, dialogue state and the Codex.
## Objectives advance ONLY from events (never from UI code). Lifecycle:
## hidden → offered → active → ready → completed.

## event name -> objective kinds it can advance
const EVENT_KINDS := {
	"npc_talked": ["talk_to"], "room_entered": ["reach_room"], "actor_defeated": ["kill"], "item_added": ["collect", "deliver"],
	"item_removed": ["collect", "deliver"], "item_used": ["use_item"], "realm_changed": ["reach_realm"], "spar_ended": ["win_spar"],
	"room_event_completed": ["survive_timer"], "flag_set": ["set_flag"], "object_interacted": ["interact_object"], "foe_judged": ["judge_foe"],
	"object_hit": ["hit_object"], "node_gathered": ["gather_node"], "fish_caught": ["catch_fish"], "craft_completed": ["craft"],
	"meditation_tick": ["meditate_seconds"], "technique_used": ["use_technique"], "body_level_changed": ["reach_body_level"],
	"equipment_changed": ["equip_slot"], "hit_dodged": ["dodge_attacks"], "technique_learned": ["learn_technique"],
	"technique_mastery_up": ["reach_mastery"], "breakthrough_succeeded": ["breakthrough"], "item_bought": ["buy_item"],
	"item_sold": ["sell_item"], "page_opened": ["open_page"], "system_used": ["use_system"], "teleported": ["teleport"],
	"seclusion_entered": ["enter_seclusion"], "companion_joined": ["choose_companion"], "pet_bonded": ["bond_pet"],
	"sect_joined": ["join_sect"], "dodged": ["use_system"], "attack_started": ["use_system"], "event_passed": ["pass_event"],
	"loot_picked": ["use_system"], "portal_used": ["use_portal"], "bottleneck_viewed": ["open_page"], "qp_milestone": ["reach_progress"],
	"sect_rank_changed": ["reach_rank"], "mail_read": ["read_mail"], "quick_use_changed": ["use_system"], "pill_used": ["use_item"],
	"art_used": ["use_system"],   # S43 movement arts (double jump, Wall-Step, glide...) count as the system of that name
	"presence_leveled": ["reach_presence"],   # S28 v1.2: a Presence trained to a level
	"post_settled": ["settle_post"],   # S50 V10: a character's post settled on its return
	"egg_hatched": ["hatch_egg"],   # v1.2 Phase D: the star-wyrm egg hatched
}

func intents() -> Array:
	return ["talk", "choose_dialogue", "accept_quest", "hand_in_quest", "track_quest", "abandon_quest", "report_page_opened",
		"scene_begin", "scene_mark", "scene_end"]

func subscribe() -> void:
	for ev in EVENT_KINDS:
		GameEvents.subscribe(ev, _on_event.bind(ev), 60)
	GameEvents.subscribe("unlock_offered", _on_unlock_offered, 60)
	GameEvents.subscribe("daily_reset", _on_daily_reset, 60)
	GameEvents.subscribe("weekly_reset", func(_p): start_weekly(false), 61)
	for ev in ["quest_completed", "realm_changed", "flag_set", "room_entered", "quest_accepted", "item_added", "character_created", "presence_leveled"]:
		GameEvents.subscribe(ev, _refresh_offers, 65)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"talk": return talk(c, str(intent.get("npc", "")))
		"choose_dialogue": return choose(c, str(intent.get("npc", "")), intent.get("choice", {}))
		"accept_quest": return accept(c, str(intent.get("quest", "")))
		"hand_in_quest": return hand_in(c, str(intent.get("quest", "")))
		"track_quest":
			var q := str(intent.get("quest", ""))
			if not c.quests.is_active(q): return fail("not_active")
			if c.quests.tracked.has(q): c.quests.tracked.erase(q)
			else:
				c.quests.tracked.push_front(q)
				while c.quests.tracked.size() > 3: c.quests.tracked.pop_back()
			emit("tracker_changed", {"actor": c.id})
			return ok()
		"abandon_quest":
			var q2 := str(intent.get("quest", ""))
			var def := quest_def(c, q2)
			if def.get("kind", "") in ["main", "guided", "prologue"]: return fail("cannot_abandon")
			apply_drop(c.id, q2, false)
			emit("quest_abandoned", {"actor": c.id, "quest": q2})
			return ok()
		"report_page_opened":
			emit("page_opened", {"actor": c.id, "page": str(intent.get("page", ""))})
			return ok()
		"scene_begin": return scene_begin(c, str(intent.get("scene", "")))
		"scene_mark": return scene_mark(c, str(intent.get("scene", "")), int(intent.get("step", -1)))
		"scene_end": return scene_end(c, str(intent.get("scene", "")), bool(intent.get("skipped", false)))
	return fail("unknown_intent")

## Quest roles may name one NPC or a list (the mentor is Elder Hu or Elder Sung by sect).
static func npc_in(value, npc: String) -> bool:
	if value is Array: return npc in value
	return str(value) == npc

func is_giver(def: Dictionary, npc: String) -> bool:
	return npc_in(def.get("giver_any", def.get("giver", "")), npc)

func is_hand_in(def: Dictionary, npc: String) -> bool:
	if def.has("hand_in_any"): return npc_in(def.hand_in_any, npc)
	return str(def.get("hand_in", def.get("giver", ""))) == npc

## The hand-in NPC this character should visit (sect roles resolve to the player's own sect).
func hand_in_npc(c, def: Dictionary) -> String:
	var list: Array = def.get("hand_in_any", [])
	if list.is_empty(): return str(def.get("hand_in", def.get("giver", "")))
	return own_npc(c, list)

## One NPC of a role given as an id or a list: the character's own sect's when the role has one in each sect.
static func own_npc(c, value) -> String:
	var list: Array = value if value is Array else [value]
	var my_sect := str(c.training_sect.get("id", "")) if c else ""
	for npc in list:
		var ns := str(ContentDB.entry("npcs", str(npc)).get("sect", ""))
		if ns == "" or ns == my_sect: return str(npc)
	return str(list[0]) if not list.is_empty() else ""

## The rooms where an NPC stands shown to this character now (a placement can wait on a quest or a flag), its own
## sect's grounds first.
func npc_rooms(c, npc: String) -> Array:
	var sect := str(c.training_sect.get("id", "")) if c else ""
	var own: Array = []
	var other: Array = []
	for rid in WorldRules.rooms_with("npc=" + npc):
		var room := ContentDB.room(str(rid))
		if not room.get("objects", []).any(func(o): return str(o.get("npc", "")) == npc and game.world.object_visible(c, o)): continue
		(own if str(room.get("sect", sect)) == sect else other).append(str(rid))
	return own + other

## Where an objective is done (M20): the rooms that hold what it asks for (the room it names, the NPC it sends you to,
## the foe, the object that sets its flag, the rite that starts its event, the node, pickup or foe's quest drop that
## gives its item, the hunting grounds a realm is climbed in), [] when it can be done anywhere.
func objective_places(c, o: Dictionary) -> Array:
	if o.has("room"): return [str(o.room)]
	match str(o.get("kind", "")):
		"reach_realm": return hunt_rooms(c).map(func(f): return f[0])
		"talk_to", "deliver": return npc_rooms(c, own_npc(c, o.get("npc_any", o.get("npc", ""))))
		"kill", "judge_foe": return WorldRules.rooms_with("enemy=" + str(o.enemy))
		# A sect chore's spot is set by either sect's flag (`alt_flag`, the Cloud Sect's).
		"set_flag": return WorldRules.rooms_with("set_flag=" + str(o.flag)) + (WorldRules.rooms_with("set_flag=" + str(o.alt_flag)) if o.has("alt_flag") else [])
		"pass_event", "survive_timer": return WorldRules.event_rooms(str(o.event))
		"win_spar":
			if not o.has("opponent"): return WorldRules.rooms_with("type=spar_post")
			return npc_rooms(c, str(o.opponent)) + WorldRules.rooms_with("opponent=" + str(o.opponent))
		"collect", "gather_node": return _item_places(c, str(o.item), str(o.kind) == "collect") + WorldRules.rooms_with("drop=" + str(o.item))
		"catch_fish": return WorldRules.rooms_with("type=fishing_spot")
		# One object by its id (Race to the Tower's bell), or any of a type.
		"hit_object", "interact_object": return WorldRules.rooms_with("id=" + str(o.object) if o.has("object") else "type=" + str(o.get("type", "")))
	return []

## Where an item a step asks for can be taken by this character now: the rooms whose nodes or pickups of it it may
## take (a herb patch waits on herb gathering, Bone Forging 4). With none, for a collect step, the rooms whose foes
## drop it (Mei Qing's willow moss from the Marsh Edge's reed frogs, before the herbs open): the tracker never sends
## the player to herbs they cannot pick. Kept per item while the character's unlocks and realm stand.
var _places_cache := {}
func _item_places(c, item: String, foes: bool) -> Array:
	var key := "%s|%s|%d|%d|%s|%s" % [c.id if c else "", item, c.cultivator.unlocked.size() if c else 0, c.quests.flags.size() if c else 0,
		c.cultivator.realm_key if c else "", str(foes)]
	if _places_cache.has(key): return _places_cache[key]
	var ctx: Dictionary = game.ctx(c) if c != null else {}
	var out: Array = WorldRules.rooms_with("item=" + item).filter(func(rid): return ContentDB.room(str(rid)).get("objects", []).any(func(ob):
		return str(ob.get("item", "")) == item and (c == null or (game.world.object_visible(c, ob) and (not ob.has("requires") or RequirementRules.passes(ob.requires, ctx))))))
	if out.is_empty() and foes:
		for rid in ContentDB.rooms:
			for sp in ContentDB.room(str(rid)).get("spawns", []):
				var e := ContentDB.entry("enemies", str(sp.get("enemy", "")))
				if not out.has(str(rid)) and LootRules.drops_item(str(e.get("loot", e.get("id", ""))), item): out.append(str(rid))
	if _places_cache.size() > 64: _places_cache.clear()
	_places_cache[key] = out
	return out

var _hops_cache: Dictionary = {}

## The room the direction mark leads to for an objective: the quest's own target when the objective can be done there
## or anywhere; else, of its places a way leads into (not a story instance entered by its event), the nearest the
## character can walk to now, its own sect's first.
func objective_room(c, def: Dictionary, o: Dictionary) -> String:
	var target := sect_room(c, def)
	var places := objective_places(c, o)
	if places.is_empty() or target in places: return target
	# Standing in the instanced room the step is done in (the Siege of Two Sects, entered by its rite, its way out held
	# until it is won): the step leads here, not back to the street the rite was begun in.
	var here := str(c.position.get("room", "")) if c else ""
	if here in places and ContentDB.room(here).get("instanced", false): return here
	var my_sect := str(c.training_sect.get("id", "")) if c else ""
	var hops := _hops(c)
	var best := target
	var best_score := INF
	for rid in places:
		if WorldRules.rooms_with("to=" + str(rid)).is_empty() and WorldRules.rooms_with("hidden_to=" + str(rid)).is_empty(): continue
		var score := float(hops.get(str(rid), 1000)) + (0.5 if str(ContentDB.room(str(rid)).get("sect", my_sect)) != my_sect else 0.0)
		if score < best_score:
			best = str(rid)
			best_score = score
	return best

## Rooms by the ways between them and where the character stands, through the ways open to it (kept a few seconds,
## like the direction mark, for this room and this much of the story).
func _hops(c) -> Dictionary:
	var here := str(c.position.get("room", "")) if c else ""
	var key := "%s|%s|%s|%d|%d" % [c.id if c else "", here, c.cultivator.realm_key if c else "", c.quests.done.size() if c else 0, c.quests.flags.size() if c else 0]
	if str(_hops_cache.get("key", "")) != key or Clock.now_utc() - float(_hops_cache.get("at", 0.0)) > 5.0:
		_hops_cache = {"key": key, "at": Clock.now_utc(), "hops": WorldRules.hops(here, func(room_id: String, p: Dictionary) -> bool: return game.world.portal_open(c, room_id, p))}
	return _hops_cache.hops

## Where the direction mark leads for a quest under way: the room of its first open objective still to do, or where
## its hand-in NPC stands now once it is ready.
func quest_target(c, def: Dictionary, st: Dictionary) -> String:
	if st.get("state", "") == "ready":
		var back := npc_rooms(c, hand_in_npc(c, def))
		return str(back[0]) if not back.is_empty() else ""
	var i := step_now(c, def, st)
	return objective_room(c, def, def.objectives[i]) if i >= 0 else sect_room(c, def)

## A quest's own room for this character: its `target_room`, or, for a sect role's quest (given by either sect's
## steward or weapon master, `giver_any`) whose room is the other sect's grounds, the room of the character's own giver
## (a Cloud disciple's chores are on the Cliff Stair, its Weapon Hall the Cloud Sect's).
func sect_room(c, def: Dictionary) -> String:
	var target := str(def.get("target_room", ""))
	var my_sect := str(c.training_sect.get("id", "")) if c else ""
	var room_sect := str(ContentDB.room(target).get("sect", ""))
	if my_sect == "" or room_sect == "" or room_sect == my_sect or not def.has("giver_any"): return target
	var own := npc_rooms(c, own_npc(c, def.giver_any))
	return str(own[0]) if not own.is_empty() else target

## What keeps the character in a room: a quest whose step is to leave its room (a `use_portal` step, e.g. Morning
## Tide's "Step outside") holds that room's ways shut, while it is on offer ("Talk to Aunt Ping") and then until the
## steps before it are done, and names the first still to do ("Open your Bag"; "Pick up Herbal Tea  1/3"). "" when
## nothing holds the character here.
func room_hold(c, room_id: String) -> String:
	if c == null: return ""
	for qid in c.quests.active.keys() + c.quests.offered.keys():
		var def := quest_def(c, qid)
		var objs: Array = def.get("objectives", [])
		var leave := objs.map(func(o): return str(o.get("kind", ""))).find("use_portal")
		if str(def.get("target_room", "")) != room_id or leave < 0: continue
		var st: Dictionary = c.quests.active.get(qid, {})
		if st.is_empty():
			if can_offer(c, def): return Tx.t("sim.quest.next_from") % ContentDB.name_of("npcs", own_npc(c, def.get("giver_any", def.get("giver", ""))))
			continue
		for j in leave:
			var need := int(objs[j].get("count", 1))
			if int(st.progress[j]) < need: return str(objs[j].get("text", "")) + ("  %d/%d" % [int(st.progress[j]), need] if need > 1 else "")
	return ""

## Does a step still to do of a quest under way ask for this: a system (`use_system`, "set_quick_use") or an item to use
## (`use_item`, "herbal_tea")? The HUD shows the control it names while it does, at rest too.
func asks_for(c, kind: String, what: String) -> bool:
	if c == null or what == "": return false
	return _any_open_step(c, func(o: Dictionary) -> bool: return str(o.get("kind", "")) == kind and str(o.get("system", o.get("item", ""))) == what)

## Does a step still to do of a quest under way ask for this foe in this room: a kill step, or a collect or deliver
## step whose item its loot drops? Its spawn points then come back at their quick pace (EnemyAuthority.return_s), so a
## kill-count or shell-gathering quest always has foes to fight.
func hunts(c, enemy: String, room: String, role := "") -> bool:
	if c == null or enemy == "": return false
	var p := {"def": enemy, "room": room, "role": role}
	var table := str(ContentDB.entry("enemies", enemy).get("loot", enemy))
	return _any_open_step(c, func(o: Dictionary) -> bool:
		match str(o.get("kind", "")):
			"kill": return _match(c, o, p, "actor_defeated") > 0
			"collect", "deliver": return c.inventory.count(str(o.get("item", ""))) < int(o.get("count", 1)) and LootRules.drops_item(table, str(o.get("item", "")))
		return false)

## Whether any open step still to do of a quest under way passes `pred` (the step's objective).
func _any_open_step(c, pred: Callable) -> bool:
	for qid in c.quests.active:
		var def := quest_def(c, qid)
		var st: Dictionary = c.quests.active[qid]
		for i in def.get("objectives", []).size():
			var o: Dictionary = def.objectives[i]
			if int(st.progress[i]) < int(o.get("count", 1)) and _objective_open(c, def, st, i) and pred.call(o): return true
	return false

## The objective a quest under way is at: its first open one still to do (-1 when none is).
func step_now(c, def: Dictionary, st: Dictionary) -> int:
	for i in def.get("objectives", []).size():
		if _objective_open(c, def, st, i) and int(st.progress[i]) < int(def.objectives[i].get("count", 1)): return i
	return -1

## Where to hunt for Levels (the realm steps' marks, the story's Level waits, P12's gap): the fields whose foes suit the
## character's Level (it lies within their range; failing that, the toughest ones it has outgrown), toughest first:
## [[room, lowest Level, highest Level]].
var _hunt_cache := {}
func hunt_rooms(c) -> Array:
	var lv := ProgressionRules.level(c)
	# Decision 41: a top-down character hunts only on the grid (the rooms past the prototype's gate are closed to it).
	var key = lv if not (c != null and str(c.view) == "topdown") else "td%d" % lv
	if _hunt_cache.has(key): return _hunt_cache[key]
	var fit: Array = []
	var outgrown: Array = []
	for rid in ContentDB.rooms:
		var room: Dictionary = ContentDB.room(rid)
		var lr: Array = room.get("level_range", [0, 0])
		if str(room.get("type", "")) != "field" or lr.size() < 2 or lv < int(lr[0]) or past_gate(c, str(rid)): continue
		(fit if lv <= int(lr[1]) else outgrown).append([str(rid), int(lr[0]), int(lr[1])])
	var toughest := func(a, b): return int(a[2]) > int(b[2]) or (int(a[2]) == int(b[2]) and str(a[0]) < str(b[0]))
	fit.sort_custom(toughest)
	outgrown.sort_custom(toughest)
	_hunt_cache[key] = fit if not fit.is_empty() else outgrown.slice(0, 2)
	return _hunt_cache[key]

func quest_def(c, id: String) -> Dictionary:
	var d := ContentDB.entry("quests", id)
	if d.is_empty() and c != null and c.quests.daily.has(id): d = c.quests.daily[id]
	if d.is_empty() and c != null and c.quests.active.has(id): d = c.quests.active[id].get("def", {})
	# Finished generated missions keep no definition: name them by their kind.
	if d.is_empty() and id.begins_with("weekly_"): d = {"id": id, "kind": "weekly", "name": str(ContentDB.config("weekly_mission").get("name", id))}
	if d.is_empty() and id.begins_with("daily_"): d = {"id": id, "kind": "daily", "name": Tx.t("sim.quest.daily_sect_mission")}
	if d.is_empty() and id.begins_with("mortal_"): d = {"id": id, "kind": "mortal", "name": Tx.t("sim.quest.county_job")}
	return d

# ------------------------------------------------------------------ offers and markers
func can_offer(c, def: Dictionary) -> bool:
	var id := str(def.id)
	if c.quests.is_active(id) or (c.quests.is_done(id) and not def.get("repeatable", false)): return false
	if def.get("offered_by_unlock", false) and not c.quests.offered.has(id): return false
	if def.has("requires") and not RequirementRules.passes(def.requires, game.ctx(c)): return false
	return true

func _refresh_offers(_p := {}) -> void:
	var c = game.active()
	if c == null: return
	for def in ContentDB.all("quests"):
		var id := str(def.id)
		if c.quests.offered.has(id) and (c.quests.is_active(id) or c.quests.is_done(id)): c.quests.offered.erase(id)
		if def.get("auto_accept", false) and can_offer(c, def):
			accept(c, id)
		elif can_offer(c, def) and not c.quests.offered.has(id):
			c.quests.offered[id] = true
			emit("quest_offered", {"actor": c.id, "quest": id, "giver": str(def.get("giver", ""))})

func _on_unlock_offered(p: Dictionary) -> void:
	var c = game.character(str(p.actor))
	var qid := str(p.get("quest", ""))
	if c == null or qid == "": return
	var def := ContentDB.entry("quests", qid)
	if def.is_empty(): return
	c.quests.offered[qid] = true
	emit("quest_offered", {"actor": c.id, "quest": qid, "giver": str(def.get("giver", ""))})
	if def.get("auto_accept", false): accept(c, qid)

## "!" gold (main), "!" blue (side/guided), "?" ready, "" none.
func npc_marker(c, npc: String) -> String:
	if c == null: return ""
	for q in c.quests.active:
		var st: Dictionary = c.quests.active[q]
		var def := quest_def(c, q)
		if st.get("state") == "ready" and is_hand_in(def, npc): return "ready"
	for q in c.quests.active:
		var def2 := quest_def(c, q)
		var st2: Dictionary = c.quests.active[q]
		for i in def2.get("objectives", []).size():
			var o: Dictionary = def2.objectives[i]
			if o.kind == "talk_to" and npc_in(o.get("npc_any", o.npc), npc) and int(st2.progress[i]) < int(o.get("count", 1)) and _objective_open(c, def2, st2, i): return "talk"
	for q in c.quests.offered:
		var def3 := ContentDB.entry("quests", q)
		if is_giver(def3, npc) and can_offer(c, def3):
			if def3.get("marker", "blue") == "gold": return "main"
			return "again" if helped(c, npc) else "side"   # a new quest from someone you have already helped
	# A quest of theirs under way: the grey bubble of three dots.
	for q in c.quests.active:
		var def4 := quest_def(c, q)
		if is_hand_in(def4, npc) or is_giver(def4, npc): return "progress"
	return ""

## Has this character finished a quest given by this NPC?
func helped(c, npc: String) -> bool:
	for q in c.quests.done:
		var d := ContentDB.entry("quests", str(q))
		if not d.is_empty() and str(d.get("kind", "")) != "daily" and is_giver(d, npc): return true
	return false

## Markers that ask the player to come over (the grey "in progress" bubble does not).
static func marker_calls(marker: String) -> bool:
	return marker in ["main", "side", "again", "ready", "talk"]

## Objectives with an "after" index open only once the earlier objective is done.
func _objective_open(_c, def: Dictionary, st: Dictionary, i: int) -> bool:
	var o: Dictionary = def.objectives[i]
	if def.get("sequential", false):
		for j in i:
			if int(st.progress[j]) < int(def.objectives[j].get("count", 1)): return false
	if o.has("after"):
		var j2 := int(o.after)
		if int(st.progress[j2]) < int(def.objectives[j2].get("count", 1)): return false
	return true

# ------------------------------------------------------------------ dialogue
## Build the conversation for an NPC: hand-in first, then talk objectives, then offers, then default lines.
func talk(c, npc: String) -> Dictionary:
	var n := ContentDB.entry("npcs", npc)
	if n.is_empty(): return fail("unknown_npc")
	emit("npc_talked", {"actor": c.id, "npc": npc})
	if n.has("on_talk"): game.apply_effects(c.id, n.on_talk, "talk:" + npc)
	GameEvents.flush()
	var convo := {"npc": npc, "speaker": str(n.get("name", npc)), "portrait": n.get("outfit", {}), "lines": [], "choices": []}
	for q in c.quests.active:
		var def := quest_def(c, q)
		if c.quests.active[q].get("state") == "ready" and is_hand_in(def, npc):
			convo.lines = def.get("complete_text", [Tx.t("sim.quest.well_done")]).duplicate()
			var gives := handover(def)
			var label: String = Tx.t("sim.quest.hand_in") % def.get("name", q)
			if not gives.is_empty(): label = Tx.t("sim.quest.hand_in_giving") % [def.get("name", q), handover_text(gives)]
			convo.choices = [{"text": label, "hand_in": q}]
			convo.quest = q
			return ok({"dialogue": convo})
	if n.has("tree") and ContentDB.dialogue.has(str(n.tree)):
		var tree: Dictionary = ContentDB.dialogue[str(n.tree)]
		var node_id := _tree_entry(c, tree)
		if node_id != "":
			var said := _tree_node(c, npc, n, tree, node_id)
			var asides := _asides(c, n)
			if not asides.is_empty():
				var said_choices: Array = said.choices
				var at: int = said_choices.size() - (1 if not said_choices.is_empty() and bool(said_choices.back().get("close", false)) else 0)
				for i in asides.size(): said_choices.insert(at + i, asides[i])
			return ok({"dialogue": said})
	# Every quest this NPC can offer, story first (main, guided, side); the first one speaks.
	var offers: Array = []
	for q in c.quests.offered:
		var def2 := ContentDB.entry("quests", q)
		if is_giver(def2, npc) and can_offer(c, def2) and not def2.get("auto_accept", false): offers.append(q)
	if not offers.is_empty():
		var rank := {"prologue": 0, "main": 1, "guided": 2, "side": 3}
		offers.sort_custom(func(a, b): return int(rank.get(str(ContentDB.entry("quests", a).get("kind", "side")), 4)) < int(rank.get(str(ContentDB.entry("quests", b).get("kind", "side")), 4)))
		var first := ContentDB.entry("quests", offers[0])
		convo.lines = first.get("offer_text", [Tx.t("sim.quest.i_have_a_task_for")]).duplicate()
		for q2 in offers.slice(0, 3):
			convo.choices.append({"text": Tx.t("sim.quest.accept") % ContentDB.entry("quests", q2).get("name", q2), "accept": q2})
		convo.choices.append_array(_asides(c, n))
		convo.choices.append({"text": Tx.t("sim.quest.not_now"), "close": true})
		convo.quest = offers[0]
		return ok({"dialogue": convo})
	for q in c.quests.active:
		var def3 := quest_def(c, q)
		if is_giver(def3, npc) and def3.has("progress_text"):
			convo.lines = def3.progress_text.duplicate()
			break
	if convo.lines.is_empty():
		var lines: Array = n.get("lines", ["..."])
		# A false realm (S48 Concealment) changes how people talk to you.
		if c.cultivator.false_realm != "" and not (n.get("concealed_lines", []) as Array).is_empty(): lines = n.concealed_lines
		convo.lines = [lines[game.tick_count % lines.size()]]
	for s in n.get("services", []):
		var svc := str(s)
		if svc.begins_with("shop:"):
			# Trade waits for Coins and Shops (Ma's Delivery): buying needs it, and the purse is not on the HUD before it.
			if not Unlocks.is_unlocked(c.id, "shop"): continue
			var shop := ContentDB.entry("shops", svc.trim_prefix("shop:"))
			if shop.is_empty() or (shop.has("requires") and not RequirementRules.passes(shop.requires, game.ctx(c))): continue
			var shops_n := (n.get("services", []) as Array).filter(func(x): return str(x).begins_with("shop:")).size()
			convo.choices.append({"text": Tx.t("sim.quest.trade") if shops_n <= 1 else str(shop.get("name", Tx.t("sim.quest.trade"))), "shop": svc.trim_prefix("shop:")})
		elif svc == "storage" and Unlocks.is_unlocked(c.id, "storage"):
			convo.choices.append({"text": Tx.t("sim.quest.storage"), "page": "storage"})
		elif svc == "missions" and Unlocks.is_unlocked(c.id, "daily_missions"):
			convo.choices.append({"text": Tx.t("sim.quest.missions"), "page": "training_sect"})
		elif svc.begins_with("page:"):
			var gate := str(n.get("service_unlocks", {}).get(svc, ""))
			if gate != "" and not Unlocks.is_unlocked(c.id, gate): continue
			convo.choices.append({"text": str(n.get("service_labels", {}).get(svc, Tx.t("sim.quest.open"))), "page": svc.trim_prefix("page:")})
		elif svc.begins_with("spar:") and Unlocks.is_unlocked(c.id, "attack"):
			convo.choices.append({"text": Tx.t("sim.quest.spar"), "spar": svc.trim_prefix("spar:")})
	# S49: people with favourite gifts take one a day.
	if not n.get("gifts", {}).is_empty():
		convo.hearts = c.relations.hearts_of(npc)
		if convo.choices.size() < 4: convo.choices.append({"text": Tx.t("sim.quest.give_gift"), "page": "gift", "args": {"npc": npc}})
	convo.choices.append_array(_asides(c, n))
	convo.choices.append({"text": Tx.t("sim.quest.farewell"), "close": true})
	return ok({"dialogue": convo})

func _tree_entry(c, tree: Dictionary) -> String:
	for entry in tree.get("entries", []):
		if entry.get("aside", false): continue
		if RequirementRules.passes(entry.get("requires", {}), game.ctx(c)): return str(entry.node)
	return ""

## P13a: an aside of the NPC's tree (a master's last lesson, technique_plan §5.2) waits as one more choice beside what
## the NPC already says, never in place of a quest's offer; it opens its node, and says nothing before its time.
func _asides(c, n: Dictionary) -> Array:
	var tree: Dictionary = ContentDB.dialogue.get(str(n.get("tree", "")), {})
	var out: Array = []
	for entry in tree.get("entries", []):
		if entry.get("aside", false) and RequirementRules.passes(entry.get("requires", {}), game.ctx(c)):
			out.append({"text": str(entry.get("text", "...")), "tree": str(tree.get("id", n.tree)), "next": str(entry.node)})
	return out

func _tree_node(c, npc: String, n: Dictionary, tree: Dictionary, node_id: String) -> Dictionary:
	var node: Dictionary = tree.nodes.get(node_id, {})
	var choices: Array = []
	for ch in node.get("choices", [{"text": Tx.t("sim.quest.continue"), "close": true}]):
		if ch.has("requires") and not RequirementRules.passes(ch.requires, game.ctx(c)): continue
		var cc: Dictionary = ch.duplicate(true)
		cc.tree = tree.get("id", "")
		cc.node = node_id
		choices.append(cc)
	return {"npc": npc, "speaker": str(node.get("speaker_name", n.get("name", npc))), "portrait": n.get("outfit", {}),
		"lines": node.get("lines", []).duplicate(), "choices": choices, "tree": str(n.tree)}

func choose(c, npc: String, choice: Dictionary) -> Dictionary:
	if choice.has("effects") and choice.get("tree", "") != "":
		# Validate the choice exists in data before applying its effects.
		var tree: Dictionary = ContentDB.dialogue.get(str(choice.tree), {})
		var node: Dictionary = tree.get("nodes", {}).get(str(choice.get("node", "")), {})
		var found := false
		for ch in node.get("choices", []):
			if str(ch.get("text", "")) == str(choice.get("text", "")):
				found = true
				if ch.has("requires") and not RequirementRules.passes(ch.requires, game.ctx(c)): return fail("not_allowed")
				game.apply_effects(c.id, ch.get("effects", []), "dialogue:" + npc)
		if not found: return fail("bad_choice")
	if choice.has("accept"): return _then(c, npc, accept(c, str(choice.accept)))
	if choice.has("hand_in"): return _then(c, npc, hand_in(c, str(choice.hand_in)))
	if choice.has("next") and choice.get("tree", "") != "":
		var tree2: Dictionary = ContentDB.dialogue.get(str(choice.tree), {})
		return ok({"dialogue": _tree_node(c, npc, ContentDB.entry("npcs", npc), tree2, str(choice.next))})
	if choice.has("spar"): return start_spar(c, str(choice.spar), -1, npc)
	return ok()

## M17 · After a quest is taken or handed in, the conversation ends there (nobody taps "Farewell"), unless the same
## person has another quest to offer or to take back now: then it goes on to that (`dialogue`). They are spoken to
## again either way, as a player tapping them again would (a talk objective about them counts).
func _then(c, npc: String, r: Dictionary) -> Dictionary:
	if not r.get("ok", false) or npc == "" or ContentDB.entry("npcs", npc).is_empty(): return r
	var again: Dictionary = talk(c, npc).get("dialogue", {})
	if again.has("quest"): r.dialogue = again
	return r

# ------------------------------------------------------------------ lifecycle
func accept(c, qid: String) -> Dictionary:
	var def := quest_def(c, qid)
	if def.is_empty(): return fail("unknown_quest")
	if c.quests.is_active(qid): return ok()
	if not can_offer(c, def) and not c.quests.offered.has(qid) and not c.quests.daily.has(qid): return fail("not_offered")
	var progress: Array = []
	for o in def.get("objectives", []): progress.append(0)
	c.quests.active[qid] = {"state": "active", "progress": progress, "accepted_tick": game.tick_count}
	if def.has("time_limit_s"): c.quests.active[qid].deadline = game.sim_time + float(def.time_limit_s)
	if c.quests.daily.has(qid): c.quests.active[qid].def = def
	c.quests.offered.erase(qid)
	# The story's quests and its lessons are always tracked, at the top (a side quest waits for room); a full tracker lets
	# the oldest side quest go first, then the oldest lesson, the main story last.
	var keep := func(t) -> int:
		var k := str(quest_def(c, str(t)).get("kind", ""))
		return 2 if k in STORY_KINDS else (1 if k == "guided" else 0)
	if def.get("kind", "") != "daily" and (int(keep.call(qid)) > 0 or c.quests.tracked.size() < 3): c.quests.tracked.push_front(qid)
	while c.quests.tracked.size() > 3:
		var drop: int = c.quests.tracked.size() - 1
		for k in range(c.quests.tracked.size() - 1, -1, -1):
			if int(keep.call(c.quests.tracked[k])) < int(keep.call(c.quests.tracked[drop])): drop = k
		c.quests.tracked.remove_at(drop)
	emit("quest_accepted", {"actor": c.id, "quest": qid, "name": str(def.get("name", qid)), "kind": str(def.get("kind", "side"))})
	game.apply_effects(c.id, def.get("on_accept", []), "quest:" + qid)
	_recount(c, qid)
	return ok({"quest": qid})

## Items active quests still need: item id -> quest id (quest drops, S32).
func item_needs(c) -> Dictionary:
	var out := {}
	for qid in c.quests.active:
		var def := quest_def(c, qid)
		for o in def.get("objectives", []):
			if str(o.get("kind", "")) in ["collect", "deliver"] and c.inventory.count(str(o.get("item", ""))) < int(o.get("count", 1)):
				out[str(o.item)] = str(qid)
	return out

## Objectives that mirror state (collect, reach_realm...) are recomputed, not incremented.
func _recount(c, qid: String) -> void:
	var def := quest_def(c, qid)
	var st: Dictionary = c.quests.active.get(qid, {})
	if st.is_empty(): return
	var changed := false
	for i in def.get("objectives", []).size():
		var o: Dictionary = def.objectives[i]
		var v := int(st.progress[i])
		match str(o.kind):
			"collect", "deliver":
				v = mini(c.inventory.count(str(o.item)), int(o.get("count", 1)))
				if not hands_over(o): v = maxi(v, int(st.progress[i]))   # count-only: once shown, it stays met
			"reach_realm": v = 1 if ProgressionRules.at_least(c.cultivator.realm_key, str(o.realm)) else 0
			"reach_body_level": v = mini(c.cultivator.body_level, int(o.get("count", 1)))
			"set_flag": v = 1 if c.quests.has_flag(str(o.flag)) or (o.has("alt_flag") and c.quests.has_flag(str(o.alt_flag))) else 0
			"learn_technique": v = 1 if (str(o.get("technique", "any")) == "any" and not c.cultivator.techniques_known.is_empty()) or c.cultivator.techniques_known.has(str(o.get("technique", ""))) else v
			"join_sect": v = 1 if str(c.training_sect.get("id", "")) != "" else 0
			"reach_rank":
				var ranks: Array = ContentDB.config("sect_ranks").get("order", [])
				v = 1 if ranks.find(str(c.training_sect.get("rank", ""))) >= ranks.find(str(o.rank)) else 0
			"pass_event": v = 1 if str(o.event) in c.cultivator.events_passed else v
			"reach_mastery":
				var best := 0
				for t in c.cultivator.mastery: best = maxi(best, int(c.cultivator.mastery[t].get("tier", 0)))
				v = 1 if best >= int(o.get("tier", 1)) else 0
			"equip_slot": v = 1 if c.inventory.equipped.get(str(o.slot)) != null else v
			"reach_presence": v = 1 if game.field.presence_level(c) >= int(o.get("level", 1)) else 0
		if v != int(st.progress[i]):
			st.progress[i] = v
			changed = true
	if changed: emit("objective_progressed", {"actor": c.id, "quest": qid})
	_check_ready(c, qid)

func _check_ready(c, qid: String) -> void:
	var def := quest_def(c, qid)
	var st: Dictionary = c.quests.active.get(qid, {})
	if st.is_empty(): return
	var any_one: bool = str(def.get("complete_on", "all")) == "any"   # e.g. the weekly: one path or the other
	var all_done := not any_one
	for i in def.get("objectives", []).size():
		var met := int(st.progress[i]) >= int(def.objectives[i].get("count", 1))
		if any_one and met: all_done = true
		elif not any_one and not met: all_done = false
	if all_done and st.state != "ready":
		st.state = "ready"
		emit("quest_ready", {"actor": c.id, "quest": qid})
		if str(def.get("hand_in", "x")) == "" or def.get("auto_complete", false): hand_in(c, qid)
	elif not all_done and st.state == "ready":
		st.state = "active"

func hand_in(c, qid: String) -> Dictionary:
	var def := quest_def(c, qid)
	var st: Dictionary = c.quests.active.get(qid, {})
	if st.is_empty() or st.get("state") != "ready": return fail("not_ready")
	# Everything asked for is checked before anything is taken, so the items and the reward go together or not at all.
	var gives := handover(def)
	for g in gives:
		var have: int = c.inventory.count(str(g.item))   # the bag and quest pouch; what is worn never counts
		if have >= int(g.count): continue
		var iname := ContentDB.item_name(str(g.item))
		if c.inventory.count_including_equipped(str(g.item)) >= int(g.count): return fail("item_worn", {"text": Tx.t("sim.quest.take_off_first") % iname})
		return fail("missing_items", {"text": Tx.t("sim.quest.still_need") % item_count_text(int(g.count) - have, str(g.item))})
	c.quests.active.erase(qid)
	for g in gives: game.inventory.apply_remove(c.id, str(g.item), int(g.count), "quest:" + qid)
	c.quests.tracked.erase(qid)
	c.quests.done[qid] = int(c.quests.done.get(qid, 0)) + 1
	var qp_kind := str(def.get("qp", {"main": "main", "guided": "guided", "side": "side", "daily": "daily"}.get(str(def.get("kind", "side")), "")))
	var pct := float(ContentDB.curve("quest_qp_pct.%s" % qp_kind, 0.0))
	if pct > 0.0 and Unlocks.is_unlocked(c.id, "cultivation"): game.progression.apply_progress(c.id, 0.0, "quest", pct)
	game.apply_effects(c.id, def.get("rewards", []), "quest:" + qid)
	emit("quest_completed", {"actor": c.id, "quest": qid, "name": str(def.get("name", qid)), "kind": str(def.get("kind", "side")),
		"gave": handover_text(gives)})
	if c.quests.daily.has(qid):
		c.quests.daily.erase(qid)
		if qid.begins_with("daily_"): emit("system_used", {"actor": c.id, "system": "daily_mission_done"})
	var nxt := str(def.get("next", ""))
	if nxt != "":
		var ndef := ContentDB.entry("quests", nxt)
		if not ndef.is_empty() and ndef.get("auto_accept", false) and can_offer(c, ndef): accept(c, nxt)
	return ok({"gave": gives})

## Items a quest asks for are handed over when it is turned in, or only counted (proof you gathered them, or a later
## craft step's ingredients). The data marks each collect objective (`consume`); a deliver always hands over.
static func hands_over(o: Dictionary) -> bool:
	return str(o.get("kind", "")) in ["collect", "deliver"] and bool(o.get("consume", str(o.get("kind", "")) == "deliver"))

## What turning a quest in takes: [{item, count}], one row per item (two objectives asking for the same item add up).
static func handover(def: Dictionary) -> Array:
	var out: Array = []
	var row := {}
	for o in def.get("objectives", []):
		if not hands_over(o): continue
		var id := str(o.item)
		if not row.has(id):
			row[id] = {"item": id, "count": 0}
			out.append(row[id])
		row[id].count += int(o.get("count", 1))
	return out

## "5 Willow Moss" (the one form for a single item: "1 Kite").
static func item_count_text(n: int, item: String) -> String:
	return Tx.t("sim.quest.item_count") % [n, ContentDB.item_name(item)]

## "5 Willow Moss, 3 Copper Ore"; "" when nothing is handed over.
static func handover_text(gives: Array) -> String:
	return ", ".join(PackedStringArray(gives.map(func(g): return item_count_text(int(g.count), str(g.item)))))

func _on_event(p: Dictionary, ev: String) -> void:
	var c = game.active()
	if c == null: return
	var actor := str(p.get("actor", p.get("killer", c.id)))
	if actor != c.id: return
	for qid in c.quests.active.keys():
		var def := quest_def(c, qid)
		var st: Dictionary = c.quests.active[qid]
		var changed := false
		for i in def.get("objectives", []).size():
			var o: Dictionary = def.objectives[i]
			if not (str(o.kind) in EVENT_KINDS[ev]): continue
			if not _objective_open(c, def, st, i): continue
			var need := int(o.get("count", 1))
			var v := int(st.progress[i])
			if o.kind in ["collect", "deliver", "reach_realm", "reach_body_level", "set_flag", "join_sect", "reach_rank", "reach_mastery", "equip_slot", "reach_presence"]:
				continue
			if v >= need: continue
			var inc := _match(c, o, p, ev)
			if inc > 0:
				st.progress[i] = mini(need, v + inc)
				changed = true
		if changed:
			emit("objective_progressed", {"actor": c.id, "quest": qid})
		_recount(c, qid)

func _match(c, o: Dictionary, p: Dictionary, ev: String) -> int:
	match str(o.kind):
		"talk_to": return 1 if npc_in(o.get("npc_any", o.npc), str(p.get("npc", ""))) else 0
		"reach_room": return 1 if str(p.get("room", "")) == str(o.room) else 0
		"kill":
			if o.has("room") and str(p.get("room", "")) != str(o.room): return 0
			if o.has("role"): return 1 if str(p.get("role", "")) == str(o.role) else 0
			if o.get("elite", false) and not p.get("elite", false): return 0   # the herd's elite, not any of its kind
			return 1 if str(o.enemy) == "any" or str(p.get("def", "")) == str(o.enemy) else 0
		"use_item": return 1 if str(o.get("item", "any")) in ["any", str(p.get("item", ""))] else 0
		"settle_post": return 1 if str(p.get("source", "post")) in ["post", "incense"] else 0   # this character's own incense counts (P5)
		"win_spar": return 1 if p.get("winner", "") == "player" and str(o.get("opponent", "any")) in ["any", str(p.get("opponent", ""))] else 0
		"survive_timer": return 1 if str(p.get("event", "")) == str(o.event) else 0
		"judge_foe": return 1 if str(p.get("def", "")) == str(o.enemy) else 0
		"hatch_egg": return 1 if str(o.get("species", "any")) in ["any", str(p.get("species", ""))] else 0   # v1.2: spared or finished, the choice is made
		"interact_object":
			if o.has("object") and str(p.get("object", "")) != str(o.object): return 0
			if o.has("type") and str(p.get("type", "")) != str(o.type): return 0
			return 1
		"hit_object": return 1 if str(p.get("type", "")) == str(o.get("type", "training_stump")) else 0
		"gather_node", "mine_node": return int(p.get("count", 1)) if str(o.get("item", "any")) in ["any", str(p.get("item", ""))] and str(o.get("craft", "")) in ["", str(p.get("craft", ""))] else 0
		"catch_fish": return 1 if str(o.get("item", "any")) in ["any", str(p.get("item", ""))] else 0
		"craft": return int(p.get("count", 1)) if str(o.get("recipe", "any")) in ["any", str(p.get("recipe", ""))] and str(o.get("craft", "")) in ["", str(p.get("craft", ""))] else 0
		"meditate_seconds":
			if o.has("near") and not p.get("spring", false) and str(o.near) == "qi_spring": return 0
			if o.has("near") and not p.get("paired", false) and str(o.near) == "companion": return 0
			return 1
		"use_technique":
			if o.has("technique") and str(o.technique) != "any" and str(p.get("technique", "")) != str(o.technique): return 0
			if o.get("ranged", false) and not ContentDB.entry("techniques", str(p.get("technique", ""))).has("projectile") and not (ContentDB.entry("techniques", str(p.get("technique", ""))).get("hitbox", {}).get("x", [0, 0])[1] >= 200): return 0
			return 1
		"dodge_attacks": return 1
		"learn_technique": return 1 if str(o.get("technique", "any")) in ["any", str(p.get("technique", ""))] else 0
		"breakthrough": return 1 if str(o.get("formation", "")) in ["", str(p.get("formation", ""))] else 0
		"buy_item": return int(p.get("count", 1)) if str(o.get("item", "any")) in ["any", str(p.get("item", ""))] else 0
		"sell_item": return int(p.get("count", 1)) if str(o.get("item", "any")) in ["any", str(p.get("item", ""))] else 0
		"open_page": return 1 if str(p.get("page", "")) == str(o.page) else 0
		"use_system":
			if ev == "dodged": return 1 if str(o.system) == "dodge" else 0
			if ev == "attack_started": return 1 if str(o.system) == "attack" and not p.get("enemy", false) else 0
			if ev == "loot_picked": return 1 if str(o.system) == "pick_up" else 0
			if ev == "quick_use_changed": return 1 if str(o.system) == "set_quick_use" else 0
			if ev == "art_used": return 1 if str(o.system) == str(p.get("art", "")) else 0
			return 1 if str(p.get("system", "")) == str(o.system) else 0
		"teleport": return 1
		"enter_seclusion": return 1 if str(o.get("focus", "any")) in ["any", str(p.get("focus", ""))] else 0
		"choose_companion": return 1
		"bond_pet": return 1
		"pass_event": return 1 if str(p.get("event", "")) == str(o.event) else 0
		"use_portal": return 0 if o.get("hidden", false) and not p.get("hidden", false) else 1
		"read_mail": return 1
	return 0

# ------------------------------------------------------------------ apply commands
func apply_flag(actor_id: String, flag: String) -> void:
	var c = game.character(actor_id)
	if c == null or c.quests.has_flag(flag): return
	c.quests.flags[flag] = true
	emit("flag_set", {"actor": actor_id, "flag": flag})

func apply_clear_flag(actor_id: String, flag: String) -> void:
	var c = game.character(actor_id)
	if c == null or not c.quests.has_flag(flag): return
	c.quests.flags.erase(flag)
	emit("flag_cleared", {"actor": actor_id, "flag": flag})

## Take a quest off a character's lists (active and tracked; `generated` also forgets a generated quest's definition)
## without completing it: abandoned, timed out, or replaced by the next day's board.
func apply_drop(actor_id: String, qid: String, generated := true) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.quests.active.erase(qid)
	c.quests.tracked.erase(qid)
	if generated: c.quests.daily.erase(qid)

## A generated quest (a daily mission, the weekly, a county job) is written to the character's list, ready to accept.
func apply_generated(actor_id: String, def: Dictionary) -> void:
	var c = game.character(actor_id)
	if c != null: c.quests.daily[str(def.id)] = def

func apply_start(actor_id: String, qid: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.quests.offered[qid] = true
	accept(c, qid)

func apply_offer(actor_id: String, qid: String) -> void:
	var c = game.character(actor_id)
	if c == null or c.quests.is_active(qid) or c.quests.is_done(qid): return
	c.quests.offered[qid] = true
	emit("quest_offered", {"actor": actor_id, "quest": qid, "giver": str(ContentDB.entry("quests", qid).get("giver", ""))})

func apply_codex(entry: String) -> void:
	if game.account.codex.has(entry): return
	game.account.codex[entry] = true
	emit("codex_entry_unlocked", {"entry": entry})

func needs_item(c, item: String) -> bool:
	for qid in c.quests.active:
		var def := quest_def(c, qid)
		for o in def.get("objectives", []):
			if o.kind in ["collect", "deliver"] and str(o.item) == item and c.inventory.count(item) < int(o.get("count", 1)): return true
	return false

## Objectives for the tracker: [{quest, name, lines: [{text, have, need, done}]}].
## The objectives of an active quest that moved past `since` (progress as last shown): the HUD toasts these while
## the tracker is still hidden, so the prologue's steps ("Pick up Herbal Tea 2/3") are never silent.
func steps_forward(c, qid: String, since: Array) -> Array:
	var st: Dictionary = c.quests.active.get(qid, {})
	if st.is_empty(): return []
	var objs: Array = quest_def(c, qid).get("objectives", [])
	var out: Array = []
	for i in mini(objs.size(), (st.progress as Array).size()):
		var v := int(st.progress[i])
		if v <= (int(since[i]) if i < since.size() else 0): continue
		var need := int(objs[i].get("count", 1))
		out.append({"text": str(objs[i].get("text", "")), "have": mini(v, need), "need": need, "done": v >= need})
	return out

## The tracker (P5a's plate, the P1 direction mark and the map read it): between main quests the story's "next" entry
## first (story_next), then each tracked quest with its objectives, [{quest, name, kind, ready, hunt, lines: [{text,
## have, need, done}], target_room}]. `hunt` marks a target that is a hunting ground (a realm to climb).
func tracker(c) -> Array:
	var out: Array = []
	var nxt := story_next(c)
	if not nxt.is_empty(): out.append(nxt)
	for qid in c.quests.tracked:
		var def := quest_def(c, qid)
		var st: Dictionary = c.quests.active.get(qid, {})
		if st.is_empty(): continue
		var lines: Array = []
		for i in def.get("objectives", []).size():
			var o: Dictionary = def.objectives[i]
			if not _objective_open(c, def, st, i) and int(st.progress[i]) == 0: continue
			lines.append({"text": str(o.get("text", o.kind)), "have": int(st.progress[i]), "need": int(o.get("count", 1)),
				"done": int(st.progress[i]) >= int(o.get("count", 1))})
		if st.state == "ready":
			var npc_name := ContentDB.name_of("npcs", hand_in_npc(c, def))
			lines = [{"text": Tx.t("sim.quest.return_to") % npc_name, "have": 0, "need": 1, "done": false}]
		var at := step_now(c, def, st) if st.state != "ready" else -1
		# S49 auto-path: where the quest leads now (its current objective's room, the hand-in NPC's once it is ready).
		var goal := quest_target(c, def, st)
		var gate := past_gate(c, goal)
		# Decision 41: a quest whose step lies past the prototype's gate keeps its steps and leads nowhere, saying so.
		if gate: lines.append({"text": Tx.t("sim.world.road_being_drawn"), "have": 0, "need": 1, "done": false})
		out.append({"quest": qid, "name": str(def.get("name", qid)), "kind": str(def.get("kind", "side")), "ready": st.state == "ready", "lines": lines,
			"target_room": "" if gate else goal, "hunt": at >= 0 and str(def.objectives[at].get("kind", "")) == "reach_realm", "gate": gate})
	return out

## Decision 41, the end of the prototype: a room with no top-down layout yet is past the gate for a top-down
## character (WorldAuthority.prototype_gate closes every way into one), and never where its tracker leads.
static func past_gate(c, room_id: String) -> bool:
	return c != null and str(c.view) == "topdown" and room_id != "" and not TopdownRoom.has_layout(room_id)

## A quest of the story that is played past the gate: its own room, or every room its giver stands in, is.
func beyond_prototype(c, d: Dictionary) -> bool:
	if c == null or str(c.view) != "topdown" or d.is_empty(): return false
	if past_gate(c, sect_room(c, d)): return true
	var giver := own_npc(c, d.get("giver_any", d.get("giver", "")))
	var rooms: Array = npc_rooms(c, giver) if giver != "" else []
	return not rooms.is_empty() and rooms.all(func(r): return past_gate(c, str(r)))

## The tracker's entry at the end of the prototype, in place of a Next entry that would lead past the gate: the tale
## rests here, the road beyond is still being drawn, and the prototype ends here. It leads nowhere (no mark, no Go).
func prototype_end() -> Dictionary:
	return {"quest": "", "name": Tx.t("sim.quest.tale_rests"), "kind": "next", "ready": false, "hunt": false, "gate": true, "target_room": "",
		"lines": [{"text": Tx.t("sim.world.road_being_drawn"), "have": 0, "need": 1, "done": false},
			{"text": Tx.t("sim.quest.tale_rests_end"), "have": 0, "need": 1, "done": false}]}

## The kinds of quest the story is told in, and the tracker's "next" entry that stands for its next quest: the direction
## mark, the tracker and the map lead with them (P1: the main story first).
const STORY_KINDS := ["main", "prologue"]
static func leads(kind: String) -> bool:
	return kind in STORY_KINDS or kind == "next"

## The story's quests that wait next, in story order (chapter, then data order): of `kinds`, not done, not taken, and
## every quest of those kinds they name to follow done (one that follows a lesson, as Strange Tracks follows the Weapon
## Hall, waits next: _story_step follows it to the lesson).
func story_waiting(c, kinds: Array) -> Array:
	var keyed: Array = []
	var all_q: Array = ContentDB.all("quests")
	for i in all_q.size():
		var dq: Dictionary = all_q[i]
		if not str(dq.get("kind", "")) in kinds: continue
		var chap := str(dq.get("chapter", ""))
		keyed.append([(int(chap) if chap.is_valid_int() else 0) * 1000 + i, dq])
	keyed.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	var out: Array = []
	for kd in keyed:
		var d: Dictionary = kd[1]
		if c.quests.is_done(str(d.id)) or c.quests.is_active(str(d.id)) or d.get("hidden", false): continue
		var waits := true
		for r in d.get("requires", {}).get("all", []):
			if str(r.get("kind", "")) == "quest_done" and not c.quests.is_done(str(r.get("quest", ""))) \
				and str(ContentDB.entry("quests", str(r.get("quest", ""))).get("kind", "")) in kinds: waits = false
		if waits: out.append(d)
	return out

## The next main quest the story waits on (story order: chapter, then data order): not done, not taken, and every
## quest it follows done. {} when none waits.
func next_main(c) -> Dictionary:
	var waiting := story_waiting(c, ["main"])
	return waiting[0] if not waiting.is_empty() else {}

## Between main quests, the tracker's "next" entry (never a blank tracker): who gives the next quest of the story and
## where, or what it still waits on and where to get it, a Level and the hunting ground for it, another quest first (its
## giver), a condition (where its giver stands). The quests waiting next are followed back through what holds each (its
## requirements, its unlock's trigger); the one to take now comes first, then the lowest realm. {} while a quest of the
## story, or one it waits on, is under way, and once the built story is done. Kept a moment, like the direction mark.
var _story_cache := {}
func story_next(c) -> Dictionary:
	if c == null: return {}
	var key := "%s|%s|%s|%d|%d|%d|%d|%d|%d|%s" % [c.id, str(c.position.get("room", "")), c.cultivator.realm_key, ProgressionRules.level(c),
		c.quests.done.size(), c.quests.active.size(), c.quests.offered.size(), c.quests.flags.size(), c.cultivator.unlocked.size(),
		str(c.training_sect.get("id", ""))]
	if str(_story_cache.get("key", "")) != key or Clock.now_utc() - float(_story_cache.get("at", 0.0)) > 2.0:
		_story_cache = {"key": key, "at": Clock.now_utc(), "entry": _story_next(c)}
	return _story_cache.entry

func _story_next(c) -> Dictionary:
	var lesson := false   # a lesson of the story (a guided quest: the Weapon Hall) under way
	for q in c.quests.active:
		var kind := str(quest_def(c, q).get("kind", ""))
		if kind in STORY_KINDS: return {}
		if kind == "guided": lesson = true
	var best := {}
	for d in story_waiting(c, STORY_KINDS):
		var s := _story_step(c, d, 0)
		if s.get("active", false): return {}
		if not s.is_empty() and (best.is_empty() or [int(s.rank), int(s.get("realm_at", 0))] < [int(best.rank), int(best.get("realm_at", 0))]): best = s
	# Decision 41: the story's next step is played past the prototype's gate. A lesson on offer inside the prototype still
	# comes first; with none, the prototype's tale rests here.
	var gated := not best.is_empty() and beyond_prototype(c, ContentDB.entry("quests", str(best.quest)))
	# With no quest of the story to take now, the lesson its realm opens comes before the Level the story waits on next
	# (at Bone Forging 3 the Weapon Hall, not the hunt for Bone Forging 4): under way, it leads the tracker itself; on
	# offer, it is the next step, from its giver (never one past the gate).
	if best.is_empty() or int(best.rank) > 0 or gated:
		if lesson: return {}
		for d in story_waiting(c, ["guided"]):
			if c.quests.offered.has(str(d.id)) and not beyond_prototype(c, d):
				best = {"quest": str(d.id), "rank": 0}
				gated = false
				break
	if gated: return prototype_end()
	if best.is_empty(): return {}
	var d := ContentDB.entry("quests", str(best.quest))
	var line := ""
	var room := ""
	var more: Array = []
	if best.has("realm"):
		line = Tx.t("sim.quest.next_level") % [int(ContentDB.realm(str(best.realm)).get("level", 0)), ContentDB.name_of("realms", str(best.realm))]
		room = objective_room(c, {}, {"kind": "reach_realm", "realm": best.realm})
		# Research player_motivation §3.6: a Level the story waits on is never only a hunt. A lesson or side quest on
		# offer closes part of it too; with none, meditation and body training do.
		more.append({"text": _floor_other_way(c), "have": 0, "need": 1, "done": false})
		# At a bottleneck the next thing to do is the breakthrough, not a hunt (the prototype's QA: "Hunt at Willow Path
		# West" while the bar said "breakthrough ready"). A Level one breakthrough away is only that: no hunt, no Go.
		if str(c.cultivator.state) == "bottleneck":
			var cur := str(c.cultivator.realm_key)
			var next_one: bool = ContentDB.realm_position(str(best.realm)) == ContentDB.realm_position(cur) + 1
			var major: bool = cur.rsplit("_", true, 1)[0] != str(ContentDB.realm_key_for_level(ProgressionRules.level(c) + 1)).rsplit("_", true, 1)[0]
			var now := {"text": Tx.t("hud.bottleneck_reached_see_the_cultivation" if major else "hud.bottleneck_tap_cultivate_to_break"), "have": 0, "need": 1, "done": false}
			more = [now] if next_one else [now] + more
			if next_one: room = ""
	else:
		# Where the giver stands now, the nearest the character can walk to (Lu on the docks, not in his boat).
		var giver := own_npc(c, d.get("giver_any", d.get("giver", "")))
		room = objective_room(c, d, {"kind": "talk_to", "npc": giver}) if giver != "" else str(d.get("target_room", ""))
		line = str(best.get("text", ""))
		if line == "": line = Tx.t("sim.quest.next_from") % ContentDB.name_of("npcs", giver)
	if past_gate(c, room): return prototype_end()
	return {"quest": str(best.quest), "name": Tx.t("sim.quest.next") % str(d.get("name", best.quest)), "kind": "next", "ready": false,
		"hunt": best.has("realm") and room != "", "lines": [{"text": line, "have": 0, "need": 1, "done": false}] + more, "target_room": room}

## The other way to close a Level the story waits on (the Next entry's second line): a lesson or side quest on offer
## (its name and giver), else meditation and body training.
func _floor_other_way(c) -> String:
	for kind in ["guided", "side"]:
		for q in c.quests.offered:
			var d := ContentDB.entry("quests", str(q))
			if str(d.get("kind", "")) == kind and can_offer(c, d):
				return Tx.t("sim.quest.next_or_quest") % [str(d.get("name", q)), ContentDB.name_of("npcs", own_npc(c, d.get("giver_any", d.get("giver", ""))))]
	return Tx.t("sim.quest.next_or_train")

## What holds a quest of the story back, followed to what can be done now: {active} when it (or the quest it waits on)
## is under way; {quest, rank 0} a quest to take now; {quest, rank 2, realm, realm_at} a realm to reach first; {quest,
## rank 3, text} another condition.
func _story_step(c, d: Dictionary, depth: int) -> Dictionary:
	var id := str(d.id)
	if c.quests.is_active(id): return {"active": true}
	if depth > 8 or c.quests.is_done(id): return {}
	var ctx: Dictionary = game.ctx(c)
	var unmet := RequirementRules.unmet(d.get("requires", {}), ctx)
	if unmet.is_empty() and d.get("offered_by_unlock", false) and not c.quests.offered.has(id):
		for u in ContentDB.all("unlocks"):
			if str(u.get("quest", "")) == id: unmet += RequirementRules.unmet(u.get("trigger", {}), ctx)
	if unmet.is_empty(): return {"quest": id, "rank": 0}
	var cond: Dictionary = unmet[0].get("cond", {})
	match str(unmet[0].get("kind", "")):
		"quest_done", "quest_accepted", "quest_active":
			var sub := ContentDB.entry("quests", str(cond.get("quest", "")))
			if not sub.is_empty(): return _story_step(c, sub, depth + 1)
		"realm_at_least":
			return {"quest": id, "rank": 2, "realm": str(cond.realm), "realm_at": ContentDB.realm_position(str(cond.realm))}
	return {"quest": id, "rank": 3, "text": str(unmet[0].get("text", ""))}

## P12 (research §6.6): when the next main quest waits on its chapter's Level floor, the gap and the fastest ways to
## close it: {quest, name, realm, level, have, fields: [[room, lo, hi]], side, dailies, post}. {} when no floor holds it.
func floor_gap(c) -> Dictionary:
	var d := next_main(c)
	var floor := ""
	for r in d.get("requires", {}).get("all", []):
		if str(r.get("kind", "")) == "realm_at_least" and not ProgressionRules.at_least(c.cultivator.realm_key, str(r.realm)): floor = str(r.realm)
	if floor == "": return {}
	var side := 0
	for q in ContentDB.all("quests"):
		if str(q.get("kind", "")) == "side" and can_offer(c, q): side += 1
	return {"quest": str(d.id), "name": str(d.get("name", d.id)), "realm": floor, "level": int(ContentDB.realm(floor).get("level", 0)), "have": ProgressionRules.level(c),
		"fields": hunt_rooms(c).slice(0, 2), "side": side, "dailies": c.quests.daily.size(), "post": Unlocks.is_unlocked(c.id, "keeping_post")}

# ------------------------------------------------------------------ staged scenes (decision 39)
## What a staged scene may change through its checkpoints (data/scenes.json `mark` and `handoff` steps): a story flag,
## a graze (HP lowered, never under SCENE_HP_FLOOR of the most), a heal.
const SCENE_EFFECTS := ["set_flag", "clear_flag", "restore_resource", "heal"]
const SCENE_HP_FLOOR := 0.4

## A staged scene (played by the presentation's SceneDirector) begins: it is this character's to see (in its room, its
## requirement met, not seen before) and its progress is kept on the character, so a scene cut short by quitting
## resumes at its last checkpoint (`at`). The scene only asks; what it changes, this authority changes.
func scene_begin(c, id: String) -> Dictionary:
	var sc := ContentDB.entry("scenes", id)
	if sc.is_empty(): return fail("unknown_scene")
	var st: Dictionary = c.quests.scenes.get(id, {})
	if st.get("done", false) and not sc.get("repeat", false): return fail("seen")
	if game.room_rt == null or game.room_rt.room_id != str(sc.room): return fail("wrong_room")
	if not st.has("at"):
		if not RequirementRules.passes(sc.get("requires", {}), game.ctx(c)): return fail("not_ready")
		c.quests.scenes[id] = {"at": 0, "applied": []}
	var at := int(c.quests.scenes[id].at)
	emit("scene_started", {"actor": c.id, "scene": id, "at": at})
	return ok({"at": at})

## A scene passes a checkpoint (a `mark` or a `handoff` step): it resumes from here, and the step's effects are applied
## once, whatever happens to the scene after.
func scene_mark(c, id: String, step: int) -> Dictionary:
	var st: Dictionary = c.quests.scenes.get(id, {})
	var steps: Array = ContentDB.entry("scenes", id).get("steps", [])
	if not st.has("at"): return fail("not_playing")
	if step < 0 or step >= steps.size() or not str(steps[step].get("do", "")) in ["mark", "handoff"]: return fail("not_a_checkpoint")
	st.at = maxi(int(st.at), step)
	var applied: Array = st.applied
	if not applied.has(step) and not (steps[step].get("effects", []) as Array).is_empty():
		applied.append(step)
		game.apply_effects(c.id, _scene_effects(c, steps[step].effects), "scene:" + id)
	emit("scene_marked", {"actor": c.id, "scene": id, "step": step})
	return ok()

## A scene's own effects: the kinds it may use only, and a graze held above the floor.
func _scene_effects(c, list: Array) -> Array:
	var out: Array = []
	for e in list:
		if not str(e.get("kind", "")) in SCENE_EFFECTS: continue
		if str(e.kind) == "restore_resource":
			var most: float = c.pools.get_max("hp")
			var lose := minf(-float(e.get("pct", 0.0)) * most, c.pools.hp - SCENE_HP_FLOOR * most)
			if str(e.get("pool", "")) == "hp" and lose > 0.0: out.append({"kind": "restore_resource", "pool": "hp", "amount": -lose})
			continue
		out.append(e)
	return out

## The scene is over, played out or skipped: seen, it never plays again (unless it is a `repeat` one).
func scene_end(c, id: String, skipped: bool) -> Dictionary:
	if not c.quests.scenes.has(id): return fail("not_playing")
	c.quests.scenes[id] = {"done": true, "skipped": skipped}
	emit("scene_ended", {"actor": c.id, "scene": id, "skipped": skipped})
	return ok()

# ------------------------------------------------------------------ set pieces, spars, dailies
func start_set_piece(c, event: String) -> Dictionary:
	var sp := ContentDB.entry("set_pieces", event)
	if sp.is_empty(): return fail("unknown_event")
	if sp.has("requires") and not RequirementRules.passes(sp.requires, game.ctx(c)):
		return fail("not_ready", {"text": RequirementRules.first_failure_text(sp.requires, game.ctx(c))})
	if event in c.cultivator.events_passed and not sp.has("repeatable"):
		return fail("already_passed", {"text": Tx.t("sim.quest.you_have_already_passed_this")})
	# A repeatable set piece (the sect war, S25) can be fought again once its cooldown has run.
	if sp.has("repeatable"):
		var until := float(c.cooldowns.get("set_piece:" + event, 0.0))
		if Clock.now_utc() < until:
			return fail("cooldown", {"text": Tx.t("sim.quest.the_next_battle_comes_in") % Tx.span(until - Clock.now_utc())})
		c.cooldowns["set_piece:" + event] = Clock.now_utc() + float(sp.repeatable.get("cooldown_h", 20)) * 3600.0
	emit("set_piece_started", {"actor": c.id, "event": event})
	if sp.has("room"):
		return game.world.load_room(c, str(sp.room), str(sp.get("portal", "")))
	if sp.has("room_event") and game.room_rt:
		game.world._start_event(c, game.room_rt, sp.room_event)
	return ok()

func start_spar_from_object(c, o: Dictionary) -> Dictionary:
	return start_spar(c, str(o.get("opponent", "sparring_disciple")))

## A spar at a set level (-1: the opponent's own; an opponent whose `spar_level` is "match", the sparring disciples and
## Shen Lian, always matches you: a spar is a lesson). Asked of a person (`npc`, the talk's Spar), that person is the
## one who fights: the partner steps out from where they stand, and they are hidden while the spar goes on
## (WorldAuthority.object_visible), so there is one of them on the screen, not two (the prototype's QA saw two Shen Lians).
func start_spar(c, opponent: String, level := -1, npc := "") -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	for e in game.room_rt.living_enemies():
		if e.def.get("spar", false): return fail("spar_running")
	var st: ActorState = game.actor_state(c.id)
	var at = st.plane + Vector2(160, 0) if st else Vector2(600, 800)
	var person := {}
	if npc != "":
		for o in game.room_rt.def.get("objects", []):
			if str(o.get("type", "")) == "npc" and str(o.get("npc", "")) == npc and game.world.object_visible(c, o): person = o
	if not person.is_empty(): at = Vector2(float(person.at[0]), float(person.at[1]))
	at.x = clampf(at.x, 80, game.room_rt.width() - 80)
	# On the height grid the partner steps up on the player's own floor, never into a wall or the water.
	if game.room_rt.topdown != null and st != null: at = game.room_rt.topdown.place_near(at, st.altitude)
	var lvl := level
	if str(ContentDB.entry("enemies", opponent).get("spar_level", "")) == "match": lvl = maxi(1, ProgressionRules.level(c))
	var e: EnemyState = game.enemies.start_spar(opponent, at, lvl)
	if e != null and not person.is_empty(): e.ai["partner"] = str(person.get("npc", ""))
	return ok({"spar": opponent})

## Timed quests (Race to the Tower) fail back to "offered" when their time runs out.
func tick(_delta: float) -> void:
	var c = game.active()
	if c == null: return
	for qid in c.quests.active.keys():
		var st: Dictionary = c.quests.active[qid]
		if st.has("deadline") and st.get("state") != "ready" and game.sim_time > float(st.deadline):
			var def := quest_def(c, qid)
			apply_drop(c.id, qid, false)
			c.quests.offered[qid] = true
			emit("quest_failed", {"actor": c.id, "quest": qid, "name": str(def.get("name", qid)), "text": str(def.get("fail_text", Tx.t("sim.quest.time_up")))})

func _on_daily_reset(_p: Dictionary) -> void:
	start_daily(false)

## S20 weekly mission: Sect Service, finished by 20 daily missions or one field boss.
func start_weekly(force: bool) -> void:
	var c = game.active()
	if c == null or (not force and not Unlocks.is_unlocked(c.id, "daily_missions")): return
	var week := Clock.reset_week(Clock.now_utc())
	var id := "weekly_%d" % week
	for qid in c.quests.daily.keys():
		if str(qid).begins_with("weekly_") and qid != id: apply_drop(c.id, qid)
	if c.quests.daily.has(id) or c.quests.done.has(id): return
	var cfg := ContentDB.config("weekly_mission")
	var lv := ProgressionRules.level(c)
	apply_generated(c.id, {"id": id, "name": str(cfg.get("name", Tx.t("sim.quest.sect_service"))), "kind": "daily", "complete_on": "any", "hand_in": "", "auto_complete": true,
		"objectives": [{"kind": "use_system", "system": "daily_mission_done", "count": int(cfg.get("dailies", 20)), "text": Tx.t("sim.quest.finish_daily_missions")},
			{"kind": "kill", "enemy": "any", "role": str(cfg.get("role", "field_boss")), "count": 1, "text": Tx.t("sim.quest.or_defeat_a_field_boss")}],
		"rewards": [{"kind": "add_contribution", "amount": int(cfg.get("contribution", 150))},
			{"kind": "grant_currency", "currency": "silver_tael", "amount": int(cfg.get("taels_base", 100)) + lv * int(cfg.get("taels_per_level", 10))}],
		"qp": "weekly"})
	accept(c, id)

## The sect board at the daily reset (or when Earning Your Keep opens it). Missed days bank (account_rules.bank, P4):
## unfinished missions stay on the board, and each day since the board last filled adds its day's missions, until
## the board holds `days` days' worth. A day away costs nothing; there is no streak to break.
func start_daily(force: bool) -> void:
	var c = game.active()
	if c == null or (not force and not Unlocks.is_unlocked(c.id, "daily_missions")): return
	var today := Clock.reset_day(Clock.now_utc())
	var bank := CalendarRules.bank()
	var per_day := int(bank.get("missions_per_day", 5))
	var owed := maxi(1, CalendarRules.days_banked(int(c.quests.board_day), today))
	if int(c.quests.board_day) == today and not force: return
	c.quests.board_day = today
	var kept: int = c.quests.daily.keys().filter(func(q): return str(q).begins_with("daily_")).size()   # the weekly keeps its week
	var space: int = per_day * int(bank.get("days", 3)) - kept
	var made := 0
	for day in range(today - owed + 1, today + 1):
		made += _fill_board(c, day, mini(per_day, space - made))
	for qid in c.quests.daily.keys(): accept(c, qid)   # a copy: accepting can auto-complete and erase
	emit("missions_refreshed", {"actor": c.id, "count": made})

## Up to `count` missions for reset day `day`, each a different job, ids daily_<day>_<n> (a day already on the board or
## done keeps its own). Returns how many were added.
func _fill_board(c, day: int, count: int) -> int:
	var rng := Rng.stream(c.id, "world")
	var templates: Array = ContentDB.all("mission_templates")
	var lv := ProgressionRules.level(c)
	var made := 0
	var n := 0
	var guard := 0
	var picked := {}   # mission name -> true: the board never lists the same job twice in a day
	while made < count and guard < 40 and not templates.is_empty():
		guard += 1
		var tpl: Dictionary = templates[rng.randi_range(0, templates.size() - 1)]
		if tpl.has("requires") and not RequirementRules.passes(tpl.requires, game.ctx(c)): continue
		var options: Array = tpl.get("options", [])
		var fit: Array = options.filter(func(op): return lv >= int(op.get("min_level", 0)) and lv <= int(op.get("max_level", 999)))
		if fit.is_empty(): continue
		var op: Dictionary = fit[rng.randi_range(0, fit.size() - 1)]
		var mname := str(op.get("name", tpl.get("name", Tx.t("sim.quest.sect_mission"))))
		if picked.has(mname): continue
		picked[mname] = true
		var id := "daily_%d_%d" % [day, n]
		n += 1
		if c.quests.daily.has(id) or c.quests.done.has(id): continue
		var obj: Dictionary = op.objective.duplicate(true)
		apply_generated(c.id, {"id": id, "name": mname, "kind": "daily", "objectives": [obj],
			"hand_in": "", "rewards": [{"kind": "add_contribution", "amount": int(ContentDB.curve("contribution.daily", 20))},
			{"kind": "grant_currency", "currency": "silver_tael", "amount": 10 + lv * 3}], "qp": "daily", "auto_complete": true})
		made += 1
	return made
