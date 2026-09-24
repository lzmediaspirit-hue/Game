extends Page
## Characters (S23): every slot with realm and idle task; set this character's idle
## task; switch characters in a safe place.

const TASKS := [["seclusion", "Seclusion"], ["train", "Train"], ["hunt", "Hunt"], ["gather", "Gather"], ["rest", "Rest"]]

func _init() -> void:
	title = "Characters"

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
			text(rr.position + Vector2(20, 48), "Slot %d · empty (create from the title screen)" % slot, 19, UiKit.HOLLOW)
			return
		text(rr.position + Vector2(20, 34), str(other.name), 22, UiKit.PALE_GOLD if other == ch else UiKit.PAPER)
		text(rr.position + Vector2(20, 62), ContentDB.realm_label(other.cultivator.realm_key), 16, UiKit.MIST)
		var task := str(other.idle_task.get("task", "")) if other != ch else "Playing"
		text(rr.position + Vector2(300, 48), task.capitalize() if task != "" else "Idle: none", 17, UiKit.BRIGHT_JADE)
		if other != ch: btn(Rect2(rr.end.x - 160, rr.position.y + 14, 140, 50), "Switch", "switch", slot)
	)
	var right := Rect2(r.end.x + 20, content.position.y, content.end.x - r.end.x - 20, content.size.y)
	panel(right)
	heading(right.position + Vector2(20, 40), "When you switch away", right.size.x - 40)
	para(Rect2(right.position + Vector2(20, 60), Vector2(right.size.x - 40, 90)), "The character you leave keeps working at 10% of active play, up to 12 hours. Choose its task:", 17, UiKit.MIST)
	var cur := str(ch.idle_task.get("task", ""))
	var y := right.position.y + 160
	for tk in TASKS:
		var def := ContentDB.entry("idle_tasks", tk[0])
		var ok := not def.has("requires") or RequirementRules.passes(def.requires, Game.ctx(ch))
		btn(Rect2(right.position.x + 20, y, right.size.x - 40, 50), tk[1], "task", tk[0], cur == tk[0], ok, RequirementRules.first_failure_text(def.get("requires", {}), Game.ctx(ch)))
		y += 58

func on_action(id: String, data) -> void:
	match id:
		"switch": navigate.emit("_switch", {"slot": int(data)})
		"task":
			if submit({"type": "set_idle_task", "task": {"task": str(data)}}).get("ok", false): flash("Idle task set.")
