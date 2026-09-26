class_name QuestAuthority
extends Authority
## S19 · Quests, objective progress, story flags, dialogue state and the Codex.
## Objectives advance ONLY from events (never from UI code). Lifecycle:
## hidden → offered → active → ready → completed.

## event name -> objective kinds it can advance
const EVENT_KINDS := {
	"npc_talked": ["talk_to"], "room_entered": ["reach_room"], "actor_defeated": ["kill"], "item_added": ["collect", "deliver"],
	"item_removed": ["collect", "deliver"], "item_used": ["use_item"], "realm_changed": ["reach_realm"], "spar_ended": ["win_spar"],
	"room_event_completed": ["survive_timer"], "flag_set": ["set_flag"], "object_interacted": ["interact_object"],
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
}

func intents() -> Array:
	return ["talk", "choose_dialogue", "accept_quest", "hand_in_quest", "track_quest", "abandon_quest", "report_page_opened"]

func subscribe() -> void:
	for ev in EVENT_KINDS:
		GameEvents.subscribe(ev, _on_event.bind(ev), 60)
	GameEvents.subscribe("unlock_offered", _on_unlock_offered, 60)
	GameEvents.subscribe("daily_reset", _on_daily_reset, 60)
	GameEvents.subscribe("weekly_reset", func(_p): start_weekly(false), 61)
	for ev in ["quest_completed", "realm_changed", "flag_set", "room_entered", "quest_accepted", "item_added", "character_created"]:
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
			c.quests.active.erase(q2)
			c.quests.tracked.erase(q2)
			emit("quest_abandoned", {"actor": c.id, "quest": q2})
			return ok()
		"report_page_opened":
			emit("page_opened", {"actor": c.id, "page": str(intent.get("page", ""))})
			return ok()
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
	var my_sect := str(c.training_sect.get("id", "")) if c else ""
	for npc in list:
		var ns := str(ContentDB.entry("npcs", str(npc)).get("sect", ""))
		if ns == "" or ns == my_sect: return str(npc)
	return str(list[0])

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
			return "main" if def3.get("marker", "blue") == "gold" else "side"
	return ""

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
			convo.choices = [{"text": Tx.t("sim.quest.hand_in") % def.get("name", q), "hand_in": q}]
			convo.quest = q
			return ok({"dialogue": convo})
	if n.has("tree") and ContentDB.dialogue.has(str(n.tree)):
		var tree: Dictionary = ContentDB.dialogue[str(n.tree)]
		var node_id := _tree_entry(c, tree)
		if node_id != "":
			return ok({"dialogue": _tree_node(c, npc, n, tree, node_id)})
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
		convo.lines = [lines[(c.quests.seen_dialogue.size() + game.tick_count) % lines.size()]]
	for s in n.get("services", []):
		var svc := str(s)
		if svc.begins_with("shop:"):
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
	convo.choices.append({"text": Tx.t("sim.quest.farewell"), "close": true})
	return ok({"dialogue": convo})

func _tree_entry(c, tree: Dictionary) -> String:
	for entry in tree.get("entries", []):
		if RequirementRules.passes(entry.get("requires", {}), game.ctx(c)): return str(entry.node)
	return ""

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
	if choice.has("accept"): return accept(c, str(choice.accept))
	if choice.has("hand_in"): return hand_in(c, str(choice.hand_in))
	if choice.has("next") and choice.get("tree", "") != "":
		var tree2: Dictionary = ContentDB.dialogue.get(str(choice.tree), {})
		return ok({"dialogue": _tree_node(c, npc, ContentDB.entry("npcs", npc), tree2, str(choice.next))})
	if choice.has("spar"): return start_spar(c, str(choice.spar))
	return ok()

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
	if c.quests.tracked.size() < 3 and def.get("kind", "") != "daily": c.quests.tracked.push_front(qid)
	while c.quests.tracked.size() > 3: c.quests.tracked.pop_back()
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
				if not bool(o.get("consume", true)): v = maxi(v, int(st.progress[i]))
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
	for i in def.get("objectives", []).size():
		var o: Dictionary = def.objectives[i]
		if o.kind in ["collect", "deliver"] and o.get("consume", o.kind == "deliver"):
			game.inventory.apply_remove(c.id, str(o.item), int(o.get("count", 1)), "quest:" + qid)
	c.quests.active.erase(qid)
	c.quests.tracked.erase(qid)
	c.quests.done[qid] = int(c.quests.done.get(qid, 0)) + 1
	var qp_kind := str(def.get("qp", {"main": "main", "guided": "guided", "side": "side", "daily": "daily"}.get(str(def.get("kind", "side")), "")))
	var pct := float(ContentDB.curve("quest_qp_pct.%s" % qp_kind, 0.0))
	if pct > 0.0 and Unlocks.is_unlocked(c.id, "cultivation"): game.progression.apply_progress(c.id, 0.0, "quest", pct)
	game.apply_effects(c.id, def.get("rewards", []), "quest:" + qid)
	emit("quest_completed", {"actor": c.id, "quest": qid, "name": str(def.get("name", qid)), "kind": str(def.get("kind", "side"))})
	if c.quests.daily.has(qid):
		c.quests.daily.erase(qid)
		if qid.begins_with("daily_"): emit("system_used", {"actor": c.id, "system": "daily_mission_done"})
	var nxt := str(def.get("next", ""))
	if nxt != "":
		var ndef := ContentDB.entry("quests", nxt)
		if not ndef.is_empty() and ndef.get("auto_accept", false) and can_offer(c, ndef): accept(c, nxt)
	return ok()

func _on_event(p: Dictionary, ev: String) -> void:
	var c = game.active()
	if c == null: return
	var actor := str(p.get("actor", p.get("killer", c.id)))
	if actor != c.id and not (ev == "actor_defeated" and game.companions.is_companion(actor)): return
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
			return 1 if str(o.enemy) == "any" or str(p.get("def", "")) == str(o.enemy) else 0
		"use_item": return 1 if str(o.get("item", "any")) in ["any", str(p.get("item", ""))] else 0
		"settle_post": return 1 if str(p.get("source", "post")) == "post" else 0
		"win_spar": return 1 if p.get("winner", "") == "player" and str(o.get("opponent", "any")) in ["any", str(p.get("opponent", ""))] else 0
		"survive_timer": return 1 if str(p.get("event", "")) == str(o.event) else 0
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

func tracker(c) -> Array:
	var out: Array = []
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
		# S49 auto-path: where the quest leads now (the hand-in NPC's room once it is ready).
		var target := WorldRules.npc_room(hand_in_npc(c, def)) if st.state == "ready" else str(def.get("target_room", ""))
		out.append({"quest": qid, "name": str(def.get("name", qid)), "kind": str(def.get("kind", "side")), "ready": st.state == "ready", "lines": lines,
			"target_room": target})
	return out

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
			return fail("cooldown", {"text": Tx.t("sim.quest.the_next_battle_comes_in") % maxi(1, int(ceil((until - Clock.now_utc()) / 3600.0)))})
		c.cooldowns["set_piece:" + event] = Clock.now_utc() + float(sp.repeatable.get("cooldown_h", 20)) * 3600.0
	emit("set_piece_started", {"actor": c.id, "event": event})
	if sp.has("room"):
		return game.world.load_room(c, str(sp.room), str(sp.get("portal", "")))
	if sp.has("room_event") and game.room_rt:
		game.world._start_event(c, game.room_rt, sp.room_event)
	return ok()

func start_spar_from_object(c, o: Dictionary) -> Dictionary:
	return start_spar(c, str(o.get("opponent", "sparring_disciple")))

## A spar at a set level (-1: the opponent's own; the sparring disciple always matches you).
func start_spar(c, opponent: String, level := -1) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	for e in game.room_rt.living_enemies():
		if e.def.get("spar", false): return fail("spar_running")
	var st: ActorState = game.actor_state(c.id)
	var at = st.plane + Vector2(160, 0) if st else Vector2(600, 800)
	at.x = clampf(at.x, 80, game.room_rt.width() - 80)
	var lvl := level
	if opponent == "sparring_disciple": lvl = maxi(1, ProgressionRules.level(c))
	game.enemies.start_spar(opponent, at, lvl)
	return ok({"spar": opponent})

## Timed quests (Race to the Tower) fail back to "offered" when their time runs out.
func tick(_delta: float) -> void:
	var c = game.active()
	if c == null: return
	for qid in c.quests.active.keys():
		var st: Dictionary = c.quests.active[qid]
		if st.has("deadline") and st.get("state") != "ready" and game.sim_time > float(st.deadline):
			var def := quest_def(c, qid)
			c.quests.active.erase(qid)
			c.quests.tracked.erase(qid)
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
		if str(qid).begins_with("weekly_") and qid != id:
			c.quests.active.erase(qid)
			c.quests.daily.erase(qid)
	if c.quests.daily.has(id) or c.quests.done.has(id): return
	var cfg := ContentDB.config("weekly_mission")
	var lv := ProgressionRules.level(c)
	c.quests.daily[id] = {"id": id, "name": str(cfg.get("name", Tx.t("sim.quest.sect_service"))), "kind": "daily", "complete_on": "any", "hand_in": "", "auto_complete": true,
		"objectives": [{"kind": "use_system", "system": "daily_mission_done", "count": int(cfg.get("dailies", 20)), "text": Tx.t("sim.quest.finish_daily_missions")},
			{"kind": "kill", "enemy": "any", "role": str(cfg.get("role", "field_boss")), "count": 1, "text": Tx.t("sim.quest.or_defeat_a_field_boss")}],
		"rewards": [{"kind": "add_contribution", "amount": int(cfg.get("contribution", 150))},
			{"kind": "grant_currency", "currency": "silver_tael", "amount": int(cfg.get("taels_base", 100)) + lv * int(cfg.get("taels_per_level", 10))}],
		"qp": "weekly"}
	accept(c, id)

func start_daily(force: bool) -> void:
	var c = game.active()
	if c == null or (not force and not Unlocks.is_unlocked(c.id, "daily_missions")): return
	for qid in c.quests.daily.keys():
		if not str(qid).begins_with("daily_"): continue   # the weekly mission keeps its week
		c.quests.active.erase(qid)
		c.quests.tracked.erase(qid)
		c.quests.daily.erase(qid)
	var rng := Rng.stream(c.id, "world")
	var templates: Array = ContentDB.all("mission_templates")
	var lv := ProgressionRules.level(c)
	var made := 0
	var guard := 0
	var picked := {}   # mission name -> true: the board never lists the same job twice
	while made < 5 and guard < 40 and not templates.is_empty():
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
		var id := "daily_%d_%d" % [Clock.reset_day(Clock.now_utc()), made]
		var obj: Dictionary = op.objective.duplicate(true)
		c.quests.daily[id] = {"id": id, "name": mname, "kind": "daily", "objectives": [obj],
			"hand_in": "", "rewards": [{"kind": "add_contribution", "amount": int(ContentDB.curve("contribution.daily", 20))},
			{"kind": "grant_currency", "currency": "silver_tael", "amount": 10 + lv * 3}], "qp": "daily", "auto_complete": true}
		made += 1
	for qid in c.quests.daily.keys(): accept(c, qid)   # a copy: accepting can auto-complete and erase
	emit("missions_refreshed", {"actor": c.id, "count": made})
