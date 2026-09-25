extends Page
## Credits (S40 · Legal): the LPC character-art authors and licences as their licences
## require, the fonts (SIL OFL) and the engine. The LPC list is read from data/LPC-CREDITS.txt.

var lines: Array = []

func _init() -> void:
	title = Tx.t("ui.credits.credits")
	modal = true
	frame_rect = Rect2(120, 60, 1040, 600)

func setup() -> void:
	lines = [[Tx.t("ui.credits.engine"), UiKit.PAPER], [Tx.t("ui.credits.everything_else"), UiKit.PAPER], ["", UiKit.MIST],
		[Tx.t("ui.credits.fonts"), UiKit.GOLD], [Tx.t("ui.credits.fonts_body"), UiKit.PAPER], ["", UiKit.MIST],
		[Tx.t("ui.credits.art"), UiKit.GOLD]]
	var f := FileAccess.open("res://data/LPC-CREDITS.txt", FileAccess.READ)
	if f == null: return
	while not f.eof_reached():
		var line := f.get_line()
		# Asset paths read as headings; licence and link lines stay quiet.
		var heading := line.contains("/") and not line.begins_with("http") and not line.contains(" ")
		var col: Color = UiKit.BRIGHT_JADE if heading else (UiKit.MIST if line.begins_with("http") else UiKit.PAPER)
		for part in _wrap_credit(line, 112): lines.append([part, col])

## Split a long line at spaces so every author and licence stays readable (no truncation).
func _wrap_credit(line: String, width: int) -> Array:
	if line.length() <= width: return [line]
	var out: Array = []
	var cur := ""
	for word in line.split(" "):
		if cur != "" and cur.length() + 1 + word.length() > width:
			out.append(cur)
			cur = "    " + word
		else:
			cur = word if cur == "" else cur + " " + word
	if cur != "": out.append(cur)
	return out

func draw_page() -> void:
	var r := Rect2(content.position, content.size)
	panel(r)
	list("credits", r.grow(-14), lines.size(), 24, func(i: int, rr: Rect2):
		text(rr.position + Vector2(8, 18), str(lines[i][0]), 15, lines[i][1])
	)
