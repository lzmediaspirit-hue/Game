extends Node
## S02 · The single answer to "is this system available to this character?".
## Gate = trigger + quest: when the trigger holds, the quest is offered; accepting
## the quest unlocks the system (and grants its tools through the entry's effects).
## Entries without a quest unlock as soon as the trigger holds. Every system asks
## `Unlocks.is_unlocked(actor, id)`; nothing checks realms for availability.

var debug_force_all := false

func _char(actor_id: String):
	return Game.character(actor_id) if Game else null

func is_unlocked(actor_id: String, system: String) -> bool:
	if debug_force_all: return true
	var c = _char(actor_id)
	if c == null: return false
	if c.cultivator.unlocked.has(system): return true
	var entry := ContentDB.entry("unlocks", system)
	if entry.get("scope", "character") == "account" and Game.account.unlocks.has(system): return true
	return false

func is_revealed(actor_id: String, element: String) -> bool:
	if debug_force_all: return true
	var c = _char(actor_id)
	if c == null: return false
	return c.cultivator.revealed.has(element)

func locked_text(system: String) -> String:
	var entry := ContentDB.entry("unlocks", system)
	if entry.has("locked_text"): return str(entry.locked_text)
	var r := RequirementRules.first_failure_text(entry.get("trigger", {}), {"char": Game.active(), "account": Game.account})
	return r if r != "" else "Not yet available"

## Re-evaluate every entry for one character (called once at the end of an event pass).
func evaluate(actor_id: String) -> void:
	var c = _char(actor_id)
	if c == null: return
	var ctx := {"char": c, "account": Game.account, "room": ContentDB.room(c.position.get("room", ""))}
	var changed := true
	var guard := 0
	while changed and guard < 8:
		changed = false
		guard += 1
		for entry in ContentDB.all("unlocks"):
			var id: String = entry.id
			if c.cultivator.unlocked.has(id): continue
			var account_scope: bool = entry.get("scope", "character") == "account"
			if account_scope and Game.account.unlocks.has(id):
				_apply_unlock(c, entry, false)
				changed = true
				continue
			if not RequirementRules.passes(entry.get("trigger", {}), ctx): continue
			var quest := str(entry.get("quest", ""))
			if quest != "" and not (c.quests.is_active(quest) or c.quests.is_done(quest)):
				if not c.cultivator.offered.has(id):
					c.cultivator.offered[id] = quest
					GameEvents.emit_event("unlock_offered", {"actor": c.id, "system": id, "quest": quest})
				continue
			_apply_unlock(c, entry, true)
			if account_scope: Game.account.unlocks[id] = true
			changed = true

func _apply_unlock(c, entry: Dictionary, apply_effects: bool) -> void:
	var id: String = entry.id
	c.cultivator.unlocked[id] = true
	c.cultivator.offered.erase(id)
	for r in entry.get("reveals", []):
		if not c.cultivator.revealed.has(r):
			c.cultivator.revealed[r] = true
			GameEvents.emit_event("hud_element_revealed", {"actor": c.id, "element": r, "system": id})
	GameEvents.emit_event("system_unlocked", {"actor": c.id, "system": id, "toast": entry.get("toast", true),
		"label": str(entry.get("label", ContentDB.text("unlock." + id)))})
	if apply_effects and not entry.get("effects", []).is_empty():
		Game.apply_effects(c.id, entry.effects, "unlock:" + id)

## Skipped Prologue: every Prologue entry unlocks together (S02).
func grant_prologue(actor_id: String) -> void:
	var c = _char(actor_id)
	if c == null: return
	for entry in ContentDB.all("unlocks"):
		if entry.get("prologue", false) and not c.cultivator.unlocked.has(entry.id):
			_apply_unlock(c, entry, false)

func force_unlock(actor_id: String, system: String) -> bool:
	if not OS.is_debug_build(): return false
	var c = _char(actor_id)
	var entry := ContentDB.entry("unlocks", system)
	if c == null or entry.is_empty(): return false
	_apply_unlock(c, entry, true)
	return true
