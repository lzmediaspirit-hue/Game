extends Page
## Calendar (S49, under World): the season and the weather now, this week's Beast Tide, and every world event on
## the account calendar with when and where it next opens. The same save shows the same calendar on any device.

const REGIONS := ["marsh", "gorge", "summit"]

func _init() -> void:
	title = Tx.t("ui.calendar.title")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var now := Clock.now_utc()
	var left := Rect2(content.position, Vector2(400, content.size.y))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(left)
	panel(right)
	# Left: the season, the weather, the Beast Tide.
	var x := left.position.x + 22
	var y := left.position.y + 40
	heading(Vector2(x, y), Tx.t("ui.calendar.season"), left.size.x - 44)
	var season := HerbRules.season(now)
	y += 50
	text(Vector2(x, y), ContentDB.name_of("seasons", season), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	text(Vector2(left.end.x - 22 - 200, y), Tx.t("ui.calendar.left") % _span(HerbRules.season_left_s(now)), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 200)
	y += 16
	y += para(Rect2(x, y, left.size.x - 44, 70), str(ContentDB.entry("seasons", season).get("desc", "")), 16, UiKit.PAPER, 3) + 18
	heading(Vector2(x, y + 20), Tx.t("ui.calendar.weather"), left.size.x - 44)
	y += 44
	for region in REGIONS:
		var w := CalendarRules.weather(region, now, Game.calendar.cal_seed())
		text(Vector2(x, y + 18), Tx.t("ui.calendar.region_" + region), 18, UiKit.MIST)
		text(Vector2(left.end.x - 22 - 200, y + 18), Tx.t("ui.calendar.weather_" + w), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 200)
		y += 28
	y += 14
	heading(Vector2(x, y + 20), Tx.t("ui.calendar.tide"), left.size.x - 44)
	y += 50
	var due: bool = Game.world.tide_due(ch)
	para(Rect2(x, y - 16, left.size.x - 44, 70), Tx.t("ui.calendar.tide_due") if due else Tx.t("ui.calendar.tide_done") % maxi(1, Game.world.tide_days_left(ch)), 17,
		UiKit.BRIGHT_JADE if due else UiKit.MIST, 3)
	# Right: every world event, soonest first.
	x = right.position.x + 22
	heading(Vector2(x, right.position.y + 40), Tx.t("ui.calendar.events"), right.size.x - 44)
	var rows: Array = Game.calendar.schedule()
	list("events", Rect2(x, right.position.y + 60, right.size.x - 34, right.size.y - 70), rows.size(), 128, func(i: int, rr: Rect2):
		var o: Dictionary = rows[i]
		var ev := CalendarRules.event(str(o.id))
		var live := now >= float(o.start)
		panel(rr, "minor_panel", "selected" if live else "normal")
		text(rr.position + Vector2(16, 30), fit(str(ev.get("name", o.id)), 20, rr.size.x - 260), 20, UiKit.PALE_GOLD if live else UiKit.PAPER)
		var when := Tx.t("ui.calendar.live") % _span(float(o.end) - now) if live else Tx.t("ui.calendar.in") % _span(float(o.start) - now)
		text(Vector2(rr.end.x - 16 - 240, rr.position.y + 30), when, 17, UiKit.BRIGHT_JADE if live else UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 240)
		text(rr.position + Vector2(16, 54), ContentDB.name_of("rooms", str(o.room)) if str(o.room) != "" else "", 15, UiKit.MIST)
		para(Rect2(rr.position.x + 16, rr.position.y + 62, rr.size.x - 32, 44), str(ev.get("desc", "")), 15, UiKit.PAPER, 2)
		if str(ev.get("cap_below", "")) != "":
			var ok := not ProgressionRules.at_least(ch.cultivator.realm_key, str(ev.cap_below))
			text(Vector2(rr.end.x - 16 - 320, rr.position.y + 54), Tx.t("ui.calendar.cap_ok") if ok else Tx.t("ui.calendar.cap_past"), 14,
				UiKit.BRIGHT_JADE if ok else UiKit.RED, HORIZONTAL_ALIGNMENT_RIGHT, 320)
	)

## "2 d 4 h", "3 h 20 m" or "12 m".
func _span(s: float) -> String:
	var m := int(ceil(maxf(0.0, s) / 60.0))
	if m >= 1440: return Tx.t("ui.calendar.span_dh") % [m / 1440, (m % 1440) / 60]
	if m >= 60: return Tx.t("ui.calendar.span_hm") % [m / 60, m % 60]
	return Tx.t("ui.calendar.span_m") % maxi(1, m)
