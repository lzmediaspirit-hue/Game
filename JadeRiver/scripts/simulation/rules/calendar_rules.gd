class_name CalendarRules
extends RefCounted
## S49 · The world calendar, pure: every world event's occurrences come from the account seed, the account's
## creation day and the UTC clock, so two devices with the same save see the same calendar.
## Events repeat every N days (from an offset), or once a week on a UTC weekday, and last some hours. A seeded
## draw picks the room and the hour where the event allows it.

const DAY := 86400.0

## The events that follow the calendar's own rhythm (the Beast Tide keeps the weekly reset).
static func events() -> Array:
	return ContentDB.all("calendar").filter(func(e): return not e.get("weekly_reset", false))

static func event(id: String) -> Dictionary:
	return ContentDB.entry("calendar", id)

## The UTC midnight a day index starts at.
static func day_start(day: int) -> float:
	return day * DAY

static func day_of(utc: float) -> int:
	return int(floor(utc / DAY))

## A draw that depends only on the seed, the event and the occurrence (never on play history).
static func draw(seed: int, id: String, k: int) -> RandomNumberGenerator:
	return Rng.keyed(seed, "calendar:%s:%d" % [id, k])

## Occurrence k of an event: {id, k, start, end, room}. Weekly events run on their UTC weekday (0 = Monday).
static func occurrence(ev: Dictionary, k: int, seed: int, origin_utc: float) -> Dictionary:
	var id := str(ev.get("id", ""))
	var r := draw(seed, id, k)
	var start := 0.0
	if ev.has("weekday"):
		# Day 0 (1970-01-01) was a Thursday: weekday 3 when Monday is 0.
		var first := day_of(origin_utc)
		first += posmod(int(ev.weekday) - posmod(first + 3, 7), 7)
		start = day_start(first + 7 * k)
	else:
		start = day_start(day_of(origin_utc) + int(ev.get("offset_days", 0)) + k * int(ev.get("every_days", 7)))
	var hours: Array = ev.get("hours", [])
	if not hours.is_empty(): start += float(hours[r.randi_range(0, hours.size() - 1)]) * 3600.0
	var rooms: Array = ev.get("rooms", [])
	var room := str(ev.get("room", ""))
	if not rooms.is_empty(): room = str(rooms[r.randi_range(0, rooms.size() - 1)])
	return {"id": id, "k": k, "start": start, "end": start + float(ev.get("duration_h", 24)) * 3600.0, "room": room}

static func period_s(ev: Dictionary) -> float:
	return 7.0 * DAY if ev.has("weekday") else float(ev.get("every_days", 7)) * DAY

## The occurrence under way at utc, or {}.
static func active(ev: Dictionary, utc: float, seed: int, origin_utc: float) -> Dictionary:
	var k := int(floor((utc - day_start(day_of(origin_utc))) / period_s(ev)))
	for kk in [k, k - 1]:
		if kk < 0: continue
		var o := occurrence(ev, kk, seed, origin_utc)
		if utc >= float(o.start) and utc < float(o.end): return o
	return {}

## The next occurrence that has not ended (the current one if under way).
static func upcoming(ev: Dictionary, utc: float, seed: int, origin_utc: float) -> Dictionary:
	var k := maxi(0, int(floor((utc - day_start(day_of(origin_utc))) / period_s(ev))) - 1)
	for i in 4:
		var o := occurrence(ev, k + i, seed, origin_utc)
		if float(o.end) > utc: return o
	return {}

## Every event's next occurrence, soonest first (the Calendar page).
static func schedule(utc: float, seed: int, origin_utc: float) -> Array:
	var out: Array = []
	for ev in events():
		var o := upcoming(ev, utc, seed, origin_utc)
		if not o.is_empty(): out.append(o)
	out.sort_custom(func(a, b): return float(a.start) < float(b.start))
	return out

## A repeat run is allowed only while the event is open and at or below its realm cap. First visits and story
## entries never ask (they are not behind the cycle).
static func repeat_open(ev: Dictionary, utc: float, seed: int, origin_utc: float, realm_key: String) -> bool:
	if active(ev, utc, seed, origin_utc).is_empty(): return false
	var cap := str(ev.get("cap_below", ""))
	return cap == "" or not ProgressionRules.at_least(realm_key, cap)

## Weather in a region for a three-hour block: a seeded pick from the region's table (never gating).
static func weather(region: String, utc: float, seed: int) -> String:
	var table: Dictionary = ContentDB.config("calendar").get("weather", {}).get(region, {})
	if table.is_empty(): return "clear"
	var block_h := float(ContentDB.config("calendar").get("weather_block_h", 3))
	var block := int(floor(utc / (block_h * 3600.0)))
	var r := draw(seed, "weather:" + region, block)
	var total := 0.0
	for w in table: total += float(table[w])
	var roll := r.randf() * total
	for w in table:
		roll -= float(table[w])
		if roll <= 0.0: return str(w)
	return "clear"

# ------------------------------------------------------------------ the Heaven Ranking (S49 v1.1)
## Weeks since the account's first week (0 on saves from before the calendar).
static func rank_week(now: float, origin_utc: float) -> int:
	return 0 if origin_utc <= 0.0 else maxi(0, Clock.reset_week(now) - Clock.reset_week(origin_utc))

## A seeded cultivator's Level this week: they climb a little every week, to their ceiling.
static func rank_level(seed_row: Dictionary, week: int) -> int:
	return mini(int(seed_row.get("cap", 99)), int(float(seed_row.get("level", 1)) + floorf(float(seed_row.get("per_week", 1.0)) * week)))

## Their CP this week: the room formula (20 + 18 x Level) times their talent, with a seeded wobble.
static func rank_cp(seed_row: Dictionary, week: int, seed: int) -> int:
	var cfg := ContentDB.config("rankings")
	var ref: Array = cfg.get("ref_cp", [20, 18])
	var wobble := float(cfg.get("wobble", 0.04)) * (2.0 * Rng.keyed(seed, "rank:%s:%d" % [str(seed_row.id), week]).randf() - 1.0)
	return int(round((float(ref[0]) + float(ref[1]) * rank_level(seed_row, week)) * float(seed_row.get("talent", 1.0)) * (1.0 + wobble)))

## The seeded cultivators this week, strongest first: [{id, name, title, level, cp, enemy}]. The same on every device.
static func rank_table(now: float, seed: int, origin_utc: float) -> Array:
	var week := rank_week(now, origin_utc)
	var rows: Array = []
	for r in ContentDB.all("rankings"):
		rows.append({"id": str(r.id), "name": str(r.name), "title": str(r.get("title", "")), "level": rank_level(r, week),
			"cp": rank_cp(r, week, seed), "enemy": str(r.get("enemy", ""))})
	rows.sort_custom(func(a, b): return int(a.cp) > int(b.cp) or (int(a.cp) == int(b.cp) and str(a.id) < str(b.id)))
	return rows
