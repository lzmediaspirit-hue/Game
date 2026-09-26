extends Page
## The guqin (S49 leisure arts): a short piece on the zither. Notes glide along five strings toward the bridge on the
## left; pluck each string as its note reaches the bridge (tap the string's peg, or keys 1-5). The steadier the
## playing, the faster meditation runs for half an hour (Progression scores it and applies the calm).

const PERFECT := 0.10
const GOOD := 0.22
const SPEED := 340.0          # how fast a note glides toward the bridge (px per second)

var notes: Array = []         # [{lane, at, hit: "" | perfect | good | miss}]
var playing := false
var clock := 0.0
var result: Dictionary = {}
var lanes := 5
var flashes: Array = []       # [{lane, t, kind}] a pluck's flash at the bridge

func _init() -> void:
	title = Tx.t("ui.guqin.title")

func setup() -> void:
	if str(args.get("tab", "")) == "play": _start()   # debug tools: --open-page=guqin:play

func _cfg() -> Dictionary:
	return ContentDB.config("chess").get("guqin", {})

func _start() -> void:
	var g := _cfg()
	lanes = int(g.get("lanes", 5))
	var tempo := float(g.get("tempo", 0.75))
	var r := Rng.keyed(int(Clock.now_utc()), "guqin")   # a new piece each time it is played
	notes = []
	var at := 2.0
	for i in int(g.get("notes", 16)):
		notes.append({"lane": r.randi_range(0, lanes - 1), "at": at, "hit": ""})
		at += tempo * (0.5 if r.randf() < 0.25 else 1.0)
	clock = 0.0
	result = {}
	flashes = []
	playing = true

func _process(delta: float) -> void:
	super._process(delta)
	for f in flashes: f.t = float(f.t) + delta
	flashes = flashes.filter(func(f): return float(f.t) < 0.35)
	if not playing: return
	clock += delta
	for nt in notes:
		if nt.hit == "" and clock - float(nt.at) > GOOD: nt.hit = "miss"
	if notes.all(func(nt): return nt.hit != ""): _finish()

func pluck(lane: int) -> void:
	if not playing or lane < 0 or lane >= lanes: return
	Audio.ui("ui_tap")
	var best = null
	var bd := 99.0
	for nt in notes:
		if nt.hit != "" or int(nt.lane) != lane: continue
		var d := absf(clock - float(nt.at))
		if d < bd:
			bd = d
			best = nt
	if best == null or bd > GOOD:
		flashes.append({"lane": lane, "t": 0.0, "kind": "miss"})
		return
	best.hit = "perfect" if bd <= PERFECT else "good"
	flashes.append({"lane": lane, "t": 0.0, "kind": str(best.hit)})

func _finish() -> void:
	playing = false
	var p := notes.filter(func(nt): return nt.hit == "perfect").size()
	var g := notes.filter(func(nt): return nt.hit == "good").size()
	var score := (p + 0.6 * g) / float(maxi(1, notes.size()))
	result = submit({"type": "play_guqin", "score": score})
	result["score"] = score
	result["perfect"] = p
	result["good"] = g
	result["missed"] = notes.size() - p - g

## The zither's body and strings.
func _body() -> Rect2:
	return Rect2(content.position.x + 20, content.position.y + 70, content.size.x - 40, 300)

func _peg(lane: int) -> Rect2:
	var b := _body()
	var gap := b.size.y / float(lanes + 1)
	return Rect2(b.position.x + 8, b.position.y + gap * (lane + 1) - 26, 52, 52)

func _string_y(lane: int) -> float:
	var b := _body()
	return b.position.y + b.size.y / float(lanes + 1) * (lane + 1)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var r := Rect2(content.position, content.size)
	panel(r)
	text(Vector2(r.position.x + 28, r.position.y + 44), Tx.t("ui.guqin.how"), 18, UiKit.MIST)
	# The instrument: a long lacquered body, five silk strings, the bridge near the pegs.
	var b := _body()
	draw_rect(b, Color("3b2416"))
	draw_rect(b.grow(-6), Color("5a3620"))
	var bridge_x := b.position.x + 110.0
	draw_rect(Rect2(bridge_x - 3, b.position.y + 14, 6, b.size.y - 28), Color("d8c08a"))
	for lane in lanes:
		var y := _string_y(lane)
		draw_line(Vector2(bridge_x, y), Vector2(b.end.x - 16, y), Color("efe3c2"), 2.0)
		var peg := _peg(lane)
		draw_circle(peg.get_center(), 24, Color("1b1410"))
		draw_circle(peg.get_center(), 21, Color("b8894a"))
		text(Vector2(peg.position.x, peg.position.y + 34), str(lane + 1), 20, UiKit.INK, HORIZONTAL_ALIGNMENT_CENTER, peg.size.x)
	for f in flashes:
		var fy := _string_y(int(f.lane))
		var col := UiKit.GOLD if f.kind == "perfect" else (UiKit.BRIGHT_JADE if f.kind == "good" else UiKit.RED)
		draw_circle(Vector2(bridge_x, fy), 18.0 + 30.0 * float(f.t), Color(col, 0.6 * (1.0 - float(f.t) / 0.35)))
	# The notes, gliding toward the bridge.
	for nt in notes:
		if nt.hit in ["perfect", "good"]: continue
		var x := bridge_x + (float(nt.at) - clock) * SPEED
		if x > b.end.x - 10 or x < b.position.x: continue
		var y2 := _string_y(int(nt.lane))
		draw_circle(Vector2(x, y2), 13, Color("12352d"))
		draw_circle(Vector2(x, y2), 10, UiKit.HOLLOW if nt.hit == "miss" else UiKit.BRIGHT_JADE)
	# Below: start, the score, or why the hands must rest.
	var y := b.end.y + 40
	var x0 := r.position.x + 28
	if playing:
		var hits := notes.filter(func(nt): return nt.hit in ["perfect", "good"]).size()
		text(Vector2(x0, y), Tx.t("ui.guqin.playing") % [hits, notes.size()], 20, UiKit.PALE_GOLD)
		return
	if not result.is_empty():
		if result.get("ok", false):
			text(Vector2(x0, y), Tx.t("ui.guqin.result") % [int(result.perfect), int(result.good), int(result.missed)], 20, UiKit.PALE_GOLD)
			text(Vector2(x0, y + 30), Tx.t("ui.guqin.calm") % int(round(float(result.get("bonus", 0.0)) * 100.0)), 18, UiKit.BRIGHT_JADE)
		else:
			text(Vector2(x0, y), str(result.get("text", "")), 18, UiKit.MIST)
		return
	var until := float(ch.cooldowns.get("guqin_until", 0.0)) - Clock.now_utc()
	var rest := until > 0.0
	if rest: text(Vector2(x0, y), Tx.t("ui.guqin.rest") % int(ceil(until / 60.0)), 18, UiKit.MIST)
	else: text(Vector2(x0, y), Tx.t("ui.guqin.ready"), 18, UiKit.PAPER)
	btn(Rect2(r.end.x - 28 - 240, r.end.y - 84, 240, 60), Tx.t("ui.guqin.play"), "play", null, true, not rest and ch.inventory.count("guqin") > 0,
		Tx.t("ui.guqin.resting") if rest else Tx.t("sim.progression.no_guqin"))

func on_action(id: String, _data) -> void:
	if id == "play": _start()
	queue_redraw()

## A pluck lands on the press, not the release: the timing is the game.
func _gui_input(event: InputEvent) -> void:
	if playing and event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		for lane in lanes:
			if _peg(lane).grow(10).has_point(event.position) or absf(event.position.y - _string_y(lane)) < 20.0 and _body().has_point(event.position):
				pluck(lane)
				accept_event()
				return
	super._gui_input(event)

func _unhandled_key_input(event: InputEvent) -> void:
	if playing and event.pressed and not event.echo and event.keycode >= KEY_1 and event.keycode < KEY_1 + lanes:
		pluck(event.keycode - KEY_1)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)
