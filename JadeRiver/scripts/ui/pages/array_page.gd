extends Page
## Decision 42 (the sect's transfer arrays; the prototype APK's feedback showed "where to" asked on the dialogue page
## beside an empty portrait): the array's own small travel picker, in the small standard window. The array's name on
## the plaque, the room it stands in and its line under it, then one button a destination its token knows, each with
## the far room's name and the array's rune ring (WorldAuthority.array_view: the nodes of its network the token has
## keyed, never one past the prototype's gate), in a list that scrolls should a network grow past three. A tap submits
## array_travel and the picker closes on the way; with no other array known yet, the line says so and the close button
## is the way back. It reads the World authority's view and submits intents only.

const ROW := 60.0
var node := ""

func _init() -> void:
	modal = true
	title = Tx.t("sim.world.array_speaker")
	frame_rect = WINDOW_SMALL

func setup() -> void:
	node = str(args.get("object", args.get("tab", "")))
	title = str(_view().get("name", title))

func _view() -> Dictionary:
	var ch = c()
	return Game.world.array_view(ch, node) if ch != null else {}

func draw_page() -> void:
	var v := _view()
	var x := content.position.x + 8.0
	var w := content.size.x - 16.0
	var y := content.position.y
	var dests: Array = v.get("destinations", [])
	if str(v.get("room_name", "")) != "": text(Vector2(x, y + 16), Tx.t("ui.array.at") % str(v.room_name), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w)
	para(Rect2(x, y + 26, w, 48), str(v.get("line", Tx.t("sim.world.array_alone"))), 16, UiKit.PAPER, 2)
	if dests.is_empty(): return
	text(Vector2(x, y + 92), Tx.t("ui.array.known"), 14, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, w)
	list("dests", Rect2(x, y + 100, w, content.end.y - y - 100), dests.size(), ROW + GAP, func(i: int, rr: Rect2):
		var r := Rect2(rr.position, Vector2(rr.size.x, ROW))
		btn(r, str(dests[i].name), "go", str(dests[i].id), false, true, "", 22)
		_rune_ring(Vector2(r.position.x + 34.0, r.get_center().y), 17.0, _is_pressed("go", str(dests[i].id))))

## The array's rune ring beside a destination: a jade disc in two rings and four runes.
func _rune_ring(c: Vector2, r: float, pressed: bool) -> void:
	if pressed: c += Vector2(1, 2)
	draw_circle(c, r + 1.0, UiKit.INK, true, -1.0, true)
	draw_circle(c, r, UiKit.JADE_SHADOW, true, -1.0, true)
	draw_arc(c, r - 2.0, 0.0, TAU, 32, UiKit.BRIGHT_JADE, 2.0, true)
	draw_arc(c, r * 0.5, 0.0, TAU, 24, Color(UiKit.BRIGHT_JADE, 0.8), 1.5, true)
	for k in 4:
		var d := Vector2.from_angle(TAU * k / 4.0 + PI / 4.0)
		draw_circle(c + d * (r * 0.76), 1.6, UiKit.PALE_GOLD, true, -1.0, true)
	draw_circle(c, 2.0, UiKit.PALE_GOLD, true, -1.0, true)

func on_action(id: String, data) -> void:
	if id == "go":
		if submit({"type": "array_travel", "from": node, "to": str(data)}).get("ok", false): close()
	queue_redraw()
