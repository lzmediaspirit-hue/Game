extends Page
## Chess at an insight site (S49 leisure arts): today's problem on a 9x9 board of Go, four lettered points and one
## answer. The right point gives insight into your deepest Dao; either way the site's problem rests until tomorrow.

var site := ""
var answer: Dictionary = {}   # the result of this visit's answer: {ok, right, answer, choice}

func _init() -> void:
	title = Tx.t("ui.chess.title")

func setup() -> void:
	site = str(args.get("site", args.get("tab", "")))

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var pz: Dictionary = Game.progression.chess_of(site)
	if pz.is_empty(): return
	var side := content.size.y
	var left := Rect2(content.position, Vector2(side, side))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(left)
	panel(right)
	# The board: warm wood, a nine-line grid, the star points, the stones and the lettered points.
	var n := int(ContentDB.config("chess").get("size", 9))
	var wood := left.grow(-22)
	draw_rect(wood, Color("c99a58"))
	draw_rect(wood.grow(-4), Color("d8ad6c"))
	var grid := wood.grow(-34)
	var cell := grid.size.x / float(n - 1)
	var line_col := Color("4a3218")
	for i in n:
		draw_line(grid.position + Vector2(i * cell, 0), grid.position + Vector2(i * cell, grid.size.y), line_col, 2.0)
		draw_line(grid.position + Vector2(0, i * cell), grid.position + Vector2(grid.size.x, i * cell), line_col, 2.0)
	for sp in [[2, 2], [6, 2], [4, 4], [2, 6], [6, 6]]:
		draw_circle(grid.position + Vector2(sp[0], sp[1]) * cell, 5.0, line_col)
	var at := func(p: Array) -> Vector2: return grid.position + Vector2(float(p[0]), float(p[1])) * cell
	for p in pz.get("black", []):
		draw_circle(at.call(p) + Vector2(2, 3), cell * 0.44, Color(0, 0, 0, 0.3))
		draw_circle(at.call(p), cell * 0.44, Color("1c1b20"))
		draw_circle(at.call(p) + Vector2(-cell * 0.14, -cell * 0.14), cell * 0.1, Color(1, 1, 1, 0.18))
	for p in pz.get("white", []):
		draw_circle(at.call(p) + Vector2(2, 3), cell * 0.44, Color(0, 0, 0, 0.25))
		draw_circle(at.call(p), cell * 0.44, Color("6f6a5e"))
		draw_circle(at.call(p), cell * 0.41, Color("f1ece0"))
	var opts: Dictionary = pz.get("options", {})
	for letter in opts:
		var pt: Vector2 = at.call(opts[letter])
		var col := UiKit.GOLD
		if not answer.is_empty():
			if str(letter) == str(answer.get("answer", "")): col = UiKit.BRIGHT_JADE
			elif str(letter) == str(answer.get("choice", "")): col = UiKit.RED
		draw_circle(pt, cell * 0.34, Color(0.08, 0.1, 0.1, 0.85))
		draw_arc(pt, cell * 0.34, 0, TAU, 32, col, 3.0)
		text(Vector2(pt.x - 20, pt.y + 8), str(letter), 22, col, HORIZONTAL_ALIGNMENT_CENTER, 40)
	# Right: the problem, the four answers, and the verdict.
	var x := right.position.x + 24
	var y := right.position.y + 40
	heading(Vector2(x, y), str(pz.get("name", "")), right.size.x - 48)
	y += 18
	y += para(Rect2(x, y, right.size.x - 48, 80), str(pz.get("question", "")), 19, UiKit.PAPER, 3) + 12
	para(Rect2(x, y, right.size.x - 48, 60), Tx.t("ui.chess.note"), 15, UiKit.MIST, 3)
	var open: bool = Game.progression.chess_open(ch, site)
	var bw := (right.size.x - 48 - 12) / 2.0
	var i := 0
	for letter in ["A", "B", "C", "D"]:
		var br := Rect2(x + (i % 2) * (bw + 12), right.end.y - 210 + (i / 2) * 66, bw, 56)
		btn(br, Tx.t("ui.chess.play_at") % letter, "pick", letter, false, open, Tx.t("sim.progression.chess_done"), 20)
		i += 1
	if not answer.is_empty():
		var right_ans: bool = answer.get("right", false)
		para(Rect2(x, right.end.y - 72, right.size.x - 48, 60), Tx.t("ui.chess.right") if right_ans else Tx.t("ui.chess.wrong") % str(answer.get("answer", "")), 18,
			UiKit.BRIGHT_JADE if right_ans else UiKit.MIST, 2)
	elif not open:
		para(Rect2(x, right.end.y - 72, right.size.x - 48, 60), Tx.t("sim.progression.chess_done"), 17, UiKit.MIST, 2)

func on_action(id: String, data) -> void:
	if id == "pick":
		answer = submit({"type": "solve_chess", "site": site, "choice": str(data)})
		answer["choice"] = str(data)
	queue_redraw()
