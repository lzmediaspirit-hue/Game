extends Page
## Gravely wounded (S31, Part 9.11 · Revival): return to the last shrine, or revive
## here when allowed (talisman or the Prologue's free recovery).

func _init() -> void:
	title = Tx.t("ui.revival.gravely_wounded")
	modal = true
	frame_rect = Rect2(300, 150, 680, 420)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	draw_rect(Rect2(0, 0, 1280, 720), Color(0.3, 0.02, 0.02, 0.12))
	var y := content.position.y
	var prologue: bool = not Unlocks.is_unlocked(ch.id, "kill_progress")
	var loss_text := Tx.t("ui.revival.no_penalty_in_the_prologue") if prologue else Tx.t("ui.revival.you_lose_10_of_this")
	para(Rect2(content.position.x + 10, y + 6, content.size.x - 20, 80), Tx.t("ui.revival.your_vision_greys") + loss_text, 21, UiKit.PAPER)
	var shrine := str(ch.last_shrine.get("room", ""))
	var where := ContentDB.name_of("rooms", shrine) if shrine != "" else ContentDB.name_of("rooms", str(ch.last_town if ch.last_town != "" else "lf_village"))
	btn(Rect2(content.position.x + 40, y + 110, content.size.x - 80, 62), Tx.t("ui.revival.return_to") % where, "choose", "shrine", true)
	var here: Dictionary = Game.combat.revive_here_allowed(ch)
	btn(Rect2(content.position.x + 40, y + 186, content.size.x - 80, 58), str(here.get("label", Tx.t("ui.revival.revive_here"))), "choose", "here", false,
		bool(here.get("ok", false)), str(here.get("text", "")))
	if not bool(here.get("ok", false)) and str(here.get("text", "")) != "":
		text(Vector2(content.position.x, y + 272), str(here.text), 18, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, content.size.x)

func on_action(id: String, data) -> void:
	if id == "choose":
		var r := submit({"type": "choose_revival", "where": str(data)})
		if r.get("ok", false): closed.emit(self)

func close() -> void:
	# Revival must be chosen; the close button returns to the shrine.
	on_action("choose", "shrine")
