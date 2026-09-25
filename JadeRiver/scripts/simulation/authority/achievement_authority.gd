class_name AchievementAuthority
extends Authority
## S34 · Achievement counters advance only from events; titles give +1% to one
## stat (applied once, through the StatBlock); emotes from the start and rewards.

func intents() -> Array:
	return ["set_title", "emote"]

func subscribe() -> void:
	var events := {}
	for a in ContentDB.all("achievements"): events[str(a.event)] = true
	for ev in events: GameEvents.subscribe(ev, _on_event.bind(ev), 80)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"set_title":
			var t := str(intent.get("title", ""))
			if t != "" and not c.cultivator.titles.has(t): return fail("not_earned")
			c.cultivator.active_title = t
			emit("title_changed", {"actor": c.id, "title": t})
			return ok()
		"emote":
			var e := str(intent.get("emote", ""))
			if not ContentDB.has_entry("emotes", e): return fail("unknown")
			if not emote_known(e): return fail("locked")
			emit("emote_played", {"actor": c.id, "emote": e})
			return ok()
	return fail("unknown_intent")

## Starting emotes are always known; the rest come from their achievement.
func emote_known(id: String) -> bool:
	var a := str(ContentDB.entry("emotes", id).get("achievement", ""))
	return a == "" or game.account.achievements.done.has(a)

func _on_event(p: Dictionary, ev: String) -> void:
	var c = game.active()
	if c == null: return
	var acc: AccountState = game.account
	for a in ContentDB.all("achievements"):
		if str(a.event) != ev or acc.achievements.done.has(a.id): continue
		var m: Dictionary = a.get("match", {})
		var matched := true
		for k in m:
			var v = p.get(k)
			if k == "realm_at_least":
				matched = matched and ProgressionRules.at_least(str(p.get("to", "mortal")), str(m[k]))
			elif k == "no_weapon":
				matched = matched and c.inventory.equipped.get("weapon") == null
			elif k == "all_valley_rooms":
				var total := 0
				var seen := 0
				for r in ContentDB.rooms:
					if ContentDB.rooms[r].get("zone") == "jade_river_valley" and not ContentDB.rooms[r].get("instanced", false):
						total += 1
						if acc.visited_rooms.has(r): seen += 1
				matched = matched and seen >= total and total > 0
			elif str(v) != str(m[k]):
				matched = false
		if not matched: continue
		var counters: Dictionary = acc.achievements.counters
		counters[a.id] = int(counters.get(a.id, 0)) + 1
		emit("achievement_progressed", {"actor": c.id, "id": a.id, "value": counters[a.id], "need": int(a.get("count", 1))})
		if int(counters[a.id]) >= int(a.get("count", 1)):
			acc.achievements.done[a.id] = true
			emit("achievement_unlocked", {"actor": c.id, "id": a.id, "name": str(a.get("name", a.id))})
			if a.has("title"): apply_title(c.id, str(a.title))
			game.apply_effects(c.id, a.get("rewards", []), "achievement:" + str(a.id))

func apply_title(actor_id: String, title: String) -> void:
	var c = game.character(actor_id)
	if c == null or c.cultivator.titles.has(title) or not ContentDB.has_entry("titles", title): return
	c.cultivator.titles.append(title)
	if c.cultivator.active_title == "": c.cultivator.active_title = title
	emit("title_changed", {"actor": actor_id, "title": title, "earned": true})
