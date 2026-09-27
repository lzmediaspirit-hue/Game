extends Page
## Calendar (S49, under World): the season and the weather now, this week's Beast Tide, and every world event on
## the account calendar with when and where it next opens. The same save shows the same calendar on any device.
## P5 (docs/page_identity.md row 22, mockup 19, decision 22): the four seasons as a strip, the one now lit with its
## bar; the week as seven day columns from today with each world event laid on its day as a slip (gold under way,
## violet coming) and a red line at the hour now; the Beast Tide across the week; the chosen event with Go there
## (auto_path) and the valley's weather with what it changes. The page reads and travels only by auto_path.

const REGIONS := ["marsh", "gorge", "summit"]
const WEEK := Rect2(92, 260, 1096, 256)
const COL_X := 100.0
const COL_W := 154.0
const SLIP := Vector2(146, 40)
const ROW_Y := 314.0
const ROWS_H := 144.0      # three rows of slips, 48 apart
const TIDE := Rect2(104, 462, 1070, 40)

var chosen := ""           # "event_id:k", or "beast_tide"

func _init() -> void:
	title = Tx.t("ui.calendar.title")
	identity = Identity.new("river_lacquer", true, "plaque", "season_strip_week_grid", 0.3)

func content_rect() -> Rect2:
	return Rect2(92, 112, 1096, 552)

## The window stays the kit's own (mockup 19); words sit on its panels and slips, each named as drawn.
func draw_surface(r: Rect2) -> void:
	ground(r, UiKit.SURFACE[identity.surface])

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var now := Clock.now_utc()
	_seasons(now)
	var slips := _week(now)
	if chosen == "" or (chosen != "beast_tide" and not slips.any(func(o): return _key(o) == chosen)):
		chosen = _key(slips[0]) if not slips.is_empty() else "beast_tide"
		for o in slips:
			if now >= float(o.start):
				chosen = _key(o)
				break
	_draw_week(ch, now, slips)
	_chosen(ch, now, slips)
	_weather(now)

func _key(o: Dictionary) -> String:
	return "%s:%d" % [o.id, int(o.k)]

# ------------------------------------------------------------------ the four seasons, from the one now
func _seasons(now: float) -> void:
	var all: Array = ContentDB.all("seasons")
	var cur: int = all.map(func(s): return str(s.id)).find(HerbRules.season(now))
	var left := HerbRules.season_left_s(now)
	for i in all.size():
		var sd: Dictionary = all[(cur + i) % all.size()]
		var r := Rect2(92 + i * 276, 112, 268, 136)
		panel(r, "minor_panel", "selected" if i == 0 else "normal")
		text(r.position + Vector2(16, 34), str(sd.name), 26, UiKit.PALE_GOLD if i == 0 else (UiKit.PAPER if i == 1 else UiKit.MIST), HORIZONTAL_ALIGNMENT_LEFT, 130, true)
		var when := Tx.t("ui.calendar.left") % UiKit.span(left) if i == 0 else Tx.t("ui.calendar.slip_in") % UiKit.span(left + (i - 1) * 7.0 * 86400.0)
		text(Vector2(r.end.x - 136, r.position.y + 30), when, 14, UiKit.PALE_GOLD if i == 0 else UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 120)
		if i == 0: bar(Rect2(r.position.x + 16, r.position.y + 42, r.size.x - 32, 22), 1.0 - left / (7.0 * 86400.0), UiKit.GOLD)
		para(Rect2(r.position.x + 16, r.position.y + (74 if i == 0 else 46), r.size.x - 32, 80), str(sd.get("desc", "")), 14, UiKit.MIST if i < 2 else UiKit.HOLLOW, 3 if i == 0 else 4)

# ------------------------------------------------------------------ the week
## Every occurrence of every world event from today to a week on: [{id, k, start, end, room, day, row}].
func _week(now: float) -> Array:
	var today := CalendarRules.day_of(now)
	var out: Array = []
	for ev in CalendarRules.events():
		var o := CalendarRules.upcoming(ev, now, Game.calendar.cal_seed(), Game.calendar.origin())
		while not o.is_empty() and CalendarRules.day_of(float(o.start)) < today + 7:
			o["day"] = maxi(0, CalendarRules.day_of(float(o.start)) - today)
			out.append(o)
			o = CalendarRules.occurrence(ev, int(o.k) + 1, Game.calendar.cal_seed(), Game.calendar.origin())
	out.sort_custom(func(a, b): return float(a.start) < float(b.start))
	var used := {}
	for o in out:
		var row := 0
		while used.has("%d:%d" % [o.day, row]): row += 1
		used["%d:%d" % [o.day, row]] = true
		o["row"] = row
	return out

func _draw_week(ch, now: float, slips: Array) -> void:
	panel(WEEK)
	var today := CalendarRules.day_of(now)
	var rows := 3
	for o in slips: rows = maxi(rows, int(o.row) + 1)
	var pitch := ROWS_H / rows
	for d in 7:
		var x := COL_X + d * COL_W
		if d == 0: rounded(Rect2(x, 266, COL_W - 2, 246), 4.0, Color(UiKit.JADE, 0.12))
		else: draw_rect(Rect2(x - 1, 270, 1, 236), Color(UiKit.MIST, 0.14))
		text(Vector2(x, 290), Tx.t("ui.calendar.today") if d == 0 else Tx.t("ui.calendar.day_%d" % posmod(today + d + 3, 7)), 16, UiKit.PALE_GOLD if d == 0 else UiKit.PAPER,
			HORIZONTAL_ALIGNMENT_CENTER, COL_W - 2)
		if d == 0: text(Vector2(x, 308), Tx.t("ui.calendar.day_%d" % posmod(today + 3, 7)), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, COL_W - 2)
	# The hour now, a red line down today.
	var nx := roundf(COL_X + 1 + fposmod(now, 86400.0) / 86400.0 * (COL_W - 4))
	glow(Rect2(nx - 6, ROW_Y - 4, 14, 198), Color(UiKit.RED, 0.35 * _halo()))
	draw_rect(Rect2(nx, ROW_Y, 2, 194), UiKit.RED)
	# The slips drop onto their days as the page opens (a fade under Reduce motion).
	draw_set_transform(Vector2(0, -roundf((1.0 - unfold()) * 24.0)))
	for o in slips:
		var r := Rect2(COL_X + 4 + int(o.day) * COL_W, ROW_Y + int(o.row) * pitch, SLIP.x, minf(SLIP.y, pitch - 6.0))
		var live := now >= float(o.start)
		var ev := CalendarRules.event(str(o.id))
		var fill := UiKit.SURFACE.river_lacquer.lerp(UiKit.GOLD, 0.4) if live else UiKit.SURFACE.river_lacquer.lerp(UiKit.SOUL, 0.24)
		if live: glow(r.grow(8), Color(UiKit.GOLD, (0.3 + 0.1 * _pulse()) * _halo()))
		if _key(o) == chosen: rounded(r.grow(3), 8.0, UiKit.PALE_GOLD)
		rounded(r, 6.0, UiKit.GOLD if live else UiKit.SOUL.lerp(UiKit.PAPER, 0.3))
		rounded(r.grow(-2), 5.0, fill)
		ground(r, fill)
		var dur := float(o.end) - float(o.start)
		var sub := Tx.t("ui.calendar.left") % UiKit.span(float(o.end) - now) if live else \
			(Tx.t("ui.calendar.slip_lasts") % [UiKit.span(dur), UiKit.span(float(o.start) - now)] if dur < 6.0 * 3600.0 else Tx.t("ui.calendar.slip_in") % UiKit.span(float(o.start) - now))
		var tall := r.size.y >= 38.0
		var nm := str(ev.get("short", ev.get("name", o.id)))
		text(r.position + Vector2(10, 18 if tall else r.size.y * 0.5 + 6), nm, 16 if UiKit.text_width(nm, 16) <= r.size.x - 16 else 14, UiKit.PALE_GOLD if live else UiKit.PAPER,
			HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 16)
		if tall: text(r.position + Vector2(10, 35), sub, 14, UiKit.PAPER if live else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 20)
		region(r, "event", _key(o))
	draw_set_transform(Vector2.ZERO)
	# The Beast Tide across the week: waiting, or held.
	var tide_fill := UiKit.SURFACE.river_lacquer.lerp(UiKit.JADE, 0.18)
	if chosen == "beast_tide": rounded(TIDE.grow(3), 8.0, UiKit.PALE_GOLD)
	rounded(TIDE, 6.0, Color(UiKit.BRIGHT_JADE, 0.55))
	rounded(TIDE.grow(-2), 5.0, tide_fill)
	ground(TIDE, tide_fill)
	var due: bool = Game.world.tide_due(ch)
	text(TIDE.position + Vector2(10, 26), Tx.t("ui.calendar.tide"), 16, UiKit.BRIGHT_JADE)
	var tx := TIDE.position.x + 20 + UiKit.text_width(Tx.t("ui.calendar.tide"), 16)
	text(Vector2(tx, TIDE.position.y + 26), _tide_line(ch, due), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, TIDE.end.x - 10 - tx)
	region(TIDE, "event", "beast_tide")

func _tide_line(ch, due: bool) -> String:
	return Tx.t("ui.calendar.tide_due") if due else Tx.t("ui.calendar.tide_done") % UiKit.span(maxi(1, Game.world.tide_days_left(ch)) * 86400.0)

# ------------------------------------------------------------------ the chosen event, and the weather
func _chosen(ch, now: float, slips: Array) -> void:
	var r := Rect2(92, 524, 640, 140)
	panel(r)
	var o: Dictionary = {}
	for s in slips:
		if _key(s) == chosen: o = s
	var id := "beast_tide" if o.is_empty() else str(o.id)
	var ev := CalendarRules.event(id)
	var live := o.is_empty() or now >= float(o.start)
	var room := "sf_gate" if o.is_empty() else (Game.calendar.trial_room(ch) if id == "gathering_trial" else str(o.room))   # each sect's own terraces
	_blossom(r.position + Vector2(29, 27), live, 1.0)
	text(r.position + Vector2(52, 32), str(ev.get("name", id)), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 400)
	var when := "" if o.is_empty() else (Tx.t("ui.calendar.live") % UiKit.span(float(o.end) - now) if live else Tx.t("ui.calendar.in") % UiKit.span(float(o.start) - now))
	var line := " · ".join([when, ContentDB.name_of("rooms", room)].filter(func(s): return s != ""))
	text(r.position + Vector2(52, 56), line, 16, UiKit.BRIGHT_JADE if live and not o.is_empty() else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 400)
	# What it is, and what it means for you: the tide's week, the Terraces Trial's standing, a repeat run's realm cap.
	var extra := ""
	var extra_col := UiKit.BRIGHT_JADE
	if o.is_empty(): extra = _tide_line(ch, Game.world.tide_due(ch))
	elif id == "gathering_trial" and live:
		var gt: Dictionary = ch.cooldowns.get("gtrial", {})
		var pts := int(gt.get("pts", 0)) if int(gt.get("k", -1)) == int(o.k) else 0
		extra = Tx.plural("ui.calendar.trial_standing", pts) % [pts, Game.calendar.trial_rank(ch), Game.calendar.trial_rivals(int(o.k), room).size() + 1] if pts > 0 \
			else Tx.t("ui.calendar.trial_none") % ContentDB.name_of("rooms", room)
	elif str(ev.get("cap_below", "")) != "":
		var ok := not ProgressionRules.at_least(ch.cultivator.realm_key, str(ev.cap_below))
		extra = Tx.t("ui.calendar.cap_ok") if ok else Tx.t("ui.calendar.cap_past")
		extra_col = UiKit.BRIGHT_JADE if ok else UiKit.RED_TEXT
	var used := para(Rect2(r.position.x + 16, r.position.y + 70, 440, 44 if extra != "" else 64), str(ev.get("desc", "")), 14, UiKit.PAPER, 2 if extra != "" else 3)
	if extra != "": para(Rect2(r.position.x + 16, r.position.y + 72 + used, 440, 40), extra, 14, extra_col, 2)
	# Go there: auto_path to the event's room, and how many regions away it lies.
	var away := regions_away(ch, room)
	var b := Rect2(r.position.x + 468, r.position.y + 16, 156, 56)
	btn(b, Tx.t("ui.calendar.go_there"), "go", room, true, away > 0, go_reason(ch, room), 20)
	if away > 0: text(Vector2(b.position.x, b.end.y + 22), Tx.plural("ui.calendar.regions_away", away) % away, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, b.size.x)

func _weather(now: float) -> void:
	var r := Rect2(748, 524, 440, 140)
	panel(r)
	var head := Tx.t("ui.calendar.weather")
	text(r.position + Vector2(18, 32), head, 20, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, 240)
	var block := float(ContentDB.config("calendar").get("weather_block_h", 3)) * 3600.0
	var nx := r.position.x + 28 + minf(240.0, UiKit.text_width(head, 20))
	text(Vector2(nx, r.position.y + 31), Tx.t("ui.calendar.next_change") % UiKit.span((floorf(now / block) + 1.0) * block - now), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.end.x - 16 - nx)
	for i in REGIONS.size():
		var w := CalendarRules.weather(REGIONS[i], now, Game.calendar.cal_seed())
		var y := r.position.y + 64 + i * 30
		text(Vector2(r.position.x + 18, y), Tx.t("ui.calendar.region_" + REGIONS[i]), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 150)
		text(Vector2(r.position.x + 178, y), Tx.t("ui.calendar.weather_" + w), 16, UiKit.PALE_GOLD if w == "storm" else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 70)
		if ContentDB.strings.has("ui.calendar.effect_" + w):
			text(Vector2(r.position.x + 250, y), Tx.t("ui.calendar.effect_" + w), 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 266)

func on_action(id: String, data) -> void:
	match id:
		"event": chosen = str(data)
		"go":
			if submit({"type": "auto_path", "target": str(data)}).get("ok", false): close()
