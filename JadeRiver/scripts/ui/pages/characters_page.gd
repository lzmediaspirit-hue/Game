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
	list("slots", r.grow(-10), slots.size(), 88, func(i: int, rr: Rect2):
		var slot := int(slots[i])
		var other = Game.character("c%d" % slot)
		panel(rr, "minor_panel")   # the one you play is marked by a gold ◆, not the selection glow (P4 §6)
		if other == null:
			text(rr.position + Vector2(20, 48), Tx.t("ui.characters.slot_empty_create_from_the") % slot, 20, UiKit.HOLLOW)
			return
		if other == ch: text(rr.position + Vector2(20, 33), "◆", 18, UiKit.GOLD)
		text(rr.position + Vector2(42 if other == ch else 20, 34), str(other.name), 22, UiKit.PALE_GOLD if other == ch else UiKit.PAPER)
		text(rr.position + Vector2(20, 62), ContentDB.realm_label(other.cultivator.realm_key, ProgressionRules.level(other)), 16, UiKit.MIST)
		text(rr.position + Vector2(300, 48), task_line(other) if other != ch else Tx.t("ui.characters.playing"), 18, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT,
			rr.size.x - 300 - (170 if other != ch else 20))
		if other != ch: btn(Rect2(rr.end.x - 160, rr.position.y + 14, 140, 50), Tx.t("ui.characters.switch"), "switch", slot)
	)
	var right := Rect2(r.end.x + 20, content.position.y, content.end.x - r.end.x - 20, content.size.y)
	panel(right)
	heading(right.position + Vector2(20, 40), Tx.t("ui.characters.when_you_switch_away"), right.size.x - 40)
	para(Rect2(right.position + Vector2(20, 60), Vector2(right.size.x - 40, 90)), Tx.t("ui.characters.the_character_you_leave_keeps"), 18, UiKit.MIST)
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

## What a character not being played does: its post, else its idle task. B20: Keeping Post (S50) moved hunting and
## gathering idlers to posts and clears idle_task, so a character at its post read "Idle: none".
func task_line(other) -> String:
	var post := post_line(other)
	if post != "": return post
	var task := str(other.idle_task.get("task", ""))
	for tk in TASKS:
		if tk[0] == task: return tk[1]
	return task.capitalize() if task != "" else Tx.t("ui.characters.idle_none")

## "Post: Delving at Willow Path West", "Vigil at Reed Marsh", or "" for a character keeping no post.
static func post_line(other) -> String:
	var post: Dictionary = Game.posts.post_of(other)
	if post.is_empty(): return ""
	var room := ContentDB.name_of("rooms", str(post.get("room", "")))
	if str(post.get("kind", "")) == "vigil": return Tx.t("ui.characters.vigil_at") % room
	return Tx.t("ui.characters.post_at") % [str(ContentDB.entry("posts", str(post.get("craft", ""))).get("short", "")), room]

func on_action(id: String, data) -> void:
	match id:
		"switch": navigate.emit("_switch", {"slot": int(data)})
		"task":
			if submit({"type": "set_idle_task", "task": {"task": str(data)}}).get("ok", false): flash(Tx.t("ui.characters.idle_task_set"))
