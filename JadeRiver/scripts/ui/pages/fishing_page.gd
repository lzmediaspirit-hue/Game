extends Page
## Fishing (S33): cast, wait for the bite, strike within the window, then keep the
## line's tension in the band while the fish fights. The authority rolls the catch.

var object_id := ""
var phase := "cast"   # cast | wait | bite | fight | done
var timer := 0.0
var bite_at := 0.0
var reaction := 9.9
var tension := 0.5
var hold := false
var fish_pull := 0.0
var in_band_time := 0.0
var result := ""

func _init() -> void:
	title = Tx.t("ui.fishing.fishing")
	modal = true
	frame_rect = Rect2(340, 150, 600, 420)

func setup() -> void:
	object_id = str(args.get("object", ""))
	phase = "wait"
	timer = 0.0
	bite_at = Rng.stream(c().id, "minigame").randf_range(1.5, 4.0) if c() else 2.5

func _process(delta: float) -> void:
	super._process(delta)
	timer += delta
	match phase:
		"wait":
			if timer >= bite_at:
				phase = "bite"
				timer = 0.0
				Audio.play("fish_bite", "SFX")
		"bite":
			if timer > 1.2:
				_finish(9.9, false)
		"fight":
			fish_pull = sin(timer * 3.1) * 0.35 + sin(timer * 7.3) * 0.15
			tension += (0.55 if hold else -0.45) * delta + fish_pull * delta
			tension = clampf(tension, 0.0, 1.0)
			if tension > 0.35 and tension < 0.75: in_band_time += delta
			if tension >= 1.0 or tension <= 0.0: _finish(reaction, false)
			elif timer >= 3.5: _finish(reaction, in_band_time > 2.0)

func _finish(react: float, tension_ok: bool) -> void:
	phase = "done"
	var r := Game.submit({"type": "catch_fish", "object": object_id, "result": {"reaction_s": react, "tension_ok": tension_ok}})
	result = (Tx.t("ui.fishing.caught_a") % ContentDB.item_name(str(r.item))) if r.get("caught", false) else Tx.t("ui.fishing.it_got_away")

func draw_page() -> void:
	var r := content
	match phase:
		"wait": text(r.position + Vector2(0, 120), Tx.t("ui.fishing.waiting_for_a_bite"), 26, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		"bite":
			text(r.position + Vector2(0, 120), Tx.t("ui.fishing.bite_strike_now"), 34, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, true)
		"fight":
			text(r.position + Vector2(0, 60), Tx.t("ui.fishing.hold_to_reel_keep_the"), 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
			var bar_r := Rect2(r.position.x + 40, r.position.y + 110, r.size.x - 80, 40)
			draw_rect(bar_r, Color(0.05, 0.08, 0.09))
			draw_rect(Rect2(bar_r.position.x + bar_r.size.x * 0.35, bar_r.position.y, bar_r.size.x * 0.4, bar_r.size.y), Color(UiKit.JADE, 0.6))
			draw_rect(Rect2(bar_r.position.x + bar_r.size.x * tension - 4, bar_r.position.y - 8, 8, bar_r.size.y + 16), UiKit.PAPER)
			bar(Rect2(r.position.x + 40, r.position.y + 170, r.size.x - 80, 26), timer / 3.5, UiKit.GOLD)
		"done":
			text(r.position + Vector2(0, 120), result, 28, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, true)
			btn(Rect2(r.get_center().x - 220, r.end.y - 70, 200, 56), Tx.t("ui.fishing.again"), "again", null, true)
			btn(Rect2(r.get_center().x + 20, r.end.y - 70, 200, 56), Tx.t("ui.fishing.done"), "done")
	if phase in ["bite", "fight"]:
		region(Rect2(r.position, Vector2(r.size.x, r.size.y - 10)), "tap")

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and phase == "fight":
		hold = event.pressed
	super._gui_input(event)

func on_action(id: String, _data) -> void:
	match id:
		"tap":
			if phase == "bite":
				reaction = timer
				phase = "fight"
				timer = 0.0
				tension = 0.5
				in_band_time = 0.0
		"again":
			var r := Game.submit({"type": "interact", "object": object_id})
			if r.get("ok", false): setup()
			else: flash(str(r.get("text", Tx.t("ui.fishing.cannot_fish_here"))))
		"done": close()
