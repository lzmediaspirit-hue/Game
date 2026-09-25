extends Page
## Emote wheel (S34): the starting emotes and the ones earned from achievements, laid out
## around a circle. Locked emotes stay visible and name their achievement.

func _init() -> void:
	title = Tx.t("ui.emotes.emotes")
	modal = true
	frame_rect = Rect2(340, 90, 600, 540)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var rows: Array = ContentDB.all("emotes")
	var center := content.get_center() + Vector2(0, 8)
	var radius := minf(content.size.x, content.size.y) * 0.36
	draw_arc(center, radius, 0.0, TAU, 64, Color(UiKit.JADE, 0.35), 2.0)
	draw_circle(center, 40.0, Color(UiKit.DEEP_TEAL, 0.9))
	icon_at(Rect2(center - Vector2(24, 24), Vector2(48, 48)), "talk")
	for i in rows.size():
		var e: Dictionary = rows[i]
		var ang := -PI / 2.0 + TAU * float(i) / float(rows.size())
		var at := center + Vector2.from_angle(ang) * radius
		var known: bool = Game.achievements.emote_known(str(e.id))
		var why := ""
		if not known: why = Tx.t("ui.emotes.earned_from") % ContentDB.name_of("achievements", str(e.get("achievement", "")))
		btn(Rect2(at - Vector2(78, 28), Vector2(156, 56)), str(e.name), "emote", str(e.id), false, known, why, 18)

func on_action(id: String, data) -> void:
	if id == "emote":
		submit({"type": "emote", "emote": str(data)})
		close()
