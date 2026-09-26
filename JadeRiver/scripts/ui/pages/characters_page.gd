extends Page
## Characters (S23): every slot with realm and idle task; set this character's idle
## task; switch characters in a safe place.

var TASKS := [["seclusion", Tx.t("ui.characters.seclusion")], ["train", Tx.t("ui.characters.train")], ["hunt", Tx.t("ui.characters.hunt")], ["gather", Tx.t("ui.characters.gather")], ["rest", Tx.t("ui.characters.rest")]]

func _init() -> void:
	title = Tx.t("ui.characters.characters")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var r := Rect2(content.position.x, content.position.y, 700, content.size.y)
	panel(r)
	var slots: Array = []
	for i in range(1, Game.account.slots_unlocked + 1): slots.append(i)
	list("slots", r.grow(-10), slots.size(), 84, func(i: int, rr: Rect2):
		var slot := int(slots[i])
		var other = Game.character("c%d" % slot)
		panel(rr, "minor_panel", "selected" if other == ch else "normal")
		if other == null:
			text(rr.position + Vector2(20, 48), Tx.t("ui.characters.slot_empty_create_from_the") % slot, 19, UiKit.HOLLOW)
			return
		text(rr.position + Vector2(20, 34), str(other.name), 22, UiKit.PALE_GOLD if other == ch else UiKit.PAPER)
		text(rr.position + Vector2(20, 62), ContentDB.realm_label(other.cultivator.realm_key), 16, UiKit.MIST)
		var task := str(other.idle_task.get("task", "")) if other != ch else Tx.t("ui.characters.playing")
		text(rr.position + Vector2(300, 48), task.capitalize() if task != "" else Tx.t("ui.characters.idle_none"), 17, UiKit.BRIGHT_JADE)
		if other != ch: btn(Rect2(rr.end.x - 160, rr.position.y + 14, 140, 50), Tx.t("ui.characters.switch"), "switch", slot)
	)
	var right := Rect2(r.end.x + 20, content.position.y, content.end.x - r.end.x - 20, content.size.y)
	panel(right)
	heading(right.position + Vector2(20, 40), Tx.t("ui.characters.when_you_switch_away"), right.size.x - 40)
	para(Rect2(right.position + Vector2(20, 60), Vector2(right.size.x - 40, 90)), Tx.t("ui.characters.the_character_you_leave_keeps"), 17, UiKit.MIST)
	var cur := str(ch.idle_task.get("task", ""))
	var y := right.position.y + 160
	for tk in TASKS:
		var def := ContentDB.entry("idle_tasks", tk[0])
		var ok := not def.has("requires") or RequirementRules.passes(def.requires, Game.ctx(ch))
		var why := RequirementRules.first_failure_text(def.get("requires", {}), Game.ctx(ch))
		# S49: idle Hunt and Gather only where the room allows them.
		if ok and not Game.world.idle_allowed(str(ch.position.get("room", "")), str(tk[0])):
			ok = false
			why = Tx.t("sim.account.idle_room_" + str(tk[0]))
		btn(Rect2(right.position.x + 20, y, right.size.x - 40, 50), tk[1], "task", tk[0], cur == tk[0], ok, why)
		y += 58

func on_action(id: String, data) -> void:
	match id:
		"switch": navigate.emit("_switch", {"slot": int(data)})
		"task":
			if submit({"type": "set_idle_task", "task": {"task": str(data)}}).get("ok", false): flash(Tx.t("ui.characters.idle_task_set"))
