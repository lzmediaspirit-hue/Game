extends Page
## Gravely wounded (S31, Part 9.11 · Revival): return to the last shrine, or revive
## here when allowed (talisman or the Prologue's free recovery).

func _init() -> void:
	title = Tx.t("ui.revival.gravely_wounded")
	modal = true
	frame_rect = Rect2(300, 110, 680, 500)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	draw_rect(Rect2(0, 0, 1280, 720), Color(0.3, 0.02, 0.02, 0.12))
	var y := content.position.y
	var prologue: bool = not Unlocks.is_unlocked(ch.id, "kill_progress")
	var loss_text := Tx.t("ui.revival.no_penalty_in_the_prologue") if prologue else Tx.t("ui.revival.you_lose_10_of_this")
	# S48 nascent-soul escape: from Sage the soul flees to the shrine and half as much is lost.
	if not prologue and ProgressionRules.at_least(ch.cultivator.realm_key, str(ContentDB.stat_const("soul_escape", {}).get("from", "sage_1"))):
		loss_text = Tx.t("ui.revival.soul_escape")
	para(Rect2(content.position.x + 10, y + 6, content.size.x - 20, 80), Tx.t("ui.revival.your_vision_greys") + loss_text, 21, UiKit.PAPER)
	var shrine := str(ch.last_shrine.get("room", ""))
	var where := ContentDB.name_of("rooms", shrine) if shrine != "" else ContentDB.name_of("rooms", str(ch.last_town if ch.last_town != "" else "lf_village"))
	btn(Rect2(content.position.x + 40, y + 110, content.size.x - 80, 62), Tx.t("ui.revival.return_to") % where, "choose", "shrine", true)
	var here: Dictionary = Game.combat.revive_here_allowed(ch)
	btn(Rect2(content.position.x + 40, y + 186, content.size.x - 80, 58), str(here.get("label", Tx.t("ui.revival.revive_here"))), "choose", "here", false,
		bool(here.get("ok", false)), str(here.get("text", "")))
	var note_y := y + 272
	if not bool(here.get("ok", false)) and str(here.get("text", "")) != "":
		text(Vector2(content.position.x, note_y), str(here.text), 18, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, content.size.x)
		note_y += 30
	# A natural treasure: an Evergreen Heart fruit lifts you here, whole.
	var fruits: int = ch.inventory.count("evergreen_heart_fruit")
	if fruits > 0:
		var fruit: Dictionary = Game.combat.fruit_revival_allowed(ch)
		btn(Rect2(content.position.x + 40, note_y, content.size.x - 80, 58), Tx.t("ui.revival.eat_an_evergreen_heart_fruit") % fruits, "choose", "fruit", false,
			bool(fruit.get("ok", false)), str(fruit.get("text", "")))

func on_action(id: String, data) -> void:
	if id == "choose":
		var r := submit({"type": "choose_revival", "where": str(data)})
		if r.get("ok", false): closed.emit(self)

func close() -> void:
	# Revival must be chosen; the close button returns to the shrine.
	on_action("choose", "shrine")
