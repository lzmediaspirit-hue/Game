class_name HerbRules
extends RefCounted
## S45 · Herb ages, ripening windows, seasons and the harvest tap. Pure functions of the node, the item and a UTC
## time; the World and Crafting authorities keep the state. Numbers live in garden.json and seasons.json.

## Seconds in one in-game day (48 real minutes).
static func day_s() -> float:
	return float(ContentDB.curve("time_of_day.day_minutes", 48)) * 60.0

## The in-game day index of a moment.
static func game_day(utc: float) -> int:
	return int(floor(utc / day_s()))

# ------------------------------------------------------------------ seasons
## The season turns with the weekly reset: four seasons of one real week each.
static func season_index(utc: float) -> int:
	return posmod(Clock.reset_week(utc), 4)

static func season(utc: float) -> String:
	var all: Array = ContentDB.all("seasons")
	return str(all[season_index(utc)].id) if all.size() == 4 else ""

## Seconds until the season changes (the next weekly reset).
static func season_left_s(utc: float) -> float:
	var week := Clock.reset_week(utc)
	var t := utc
	# The next reset is at most a week away; step by hours, then minutes (exact enough for a countdown).
	for step in [3600.0, 60.0]:
		while Clock.reset_week(t + step) == week: t += step
	return maxf(0.0, t - utc + 60.0)

## A node with a season flowers only in it; one without keeps its own time.
static func in_season(o: Dictionary, utc: float) -> bool:
	return str(o.get("season", "")) == "" or str(o.season) == season(utc)

# ------------------------------------------------------------------ ripening
## {ripe, seconds, window}: `seconds` is the time left while ripe, or until the next window opens; `window` is the
## in-game day the window is centred on (a guardian rises once per window). A node without `ripen` is always ripe.
static func ripen_state(o: Dictionary, utc: float) -> Dictionary:
	var r: Dictionary = o.get("ripen", {})
	if r.is_empty(): return {"ripe": true, "seconds": 0.0, "window": -1}
	var L := day_s()
	var frac := float(ContentDB.config("garden").get("phases", {}).get(str(r.get("phase", "dawn")), 0.0))
	var every := maxi(1, int(r.get("every_days", 1)))
	var off := posmod(int(r.get("offset", 0)), every)
	var half := float(r.get("minutes", 20)) * 30.0
	var base := int(floor((utc - frac * L) / L))          # the last day whose phase instant has passed
	var d_prev := base - posmod(base - off, every)        # the last window day at or before it
	var c_prev := d_prev * L + frac * L
	if utc - c_prev <= half: return {"ripe": true, "seconds": c_prev + half - utc, "window": d_prev}
	var d_next := d_prev + every
	var c_next := d_next * L + frac * L
	if utc >= c_next - half: return {"ripe": true, "seconds": c_next + half - utc, "window": d_next}
	return {"ripe": false, "seconds": c_next - half - utc, "window": d_next}

## When a picked rare node grows back: the end of the window it was picked in (or, picked early, of the window it
## was growing toward), so a node gives one herb a ripening.
static func regrow_at(o: Dictionary, utc: float) -> float:
	var st := ripen_state(o, utc)
	if st.ripe: return utc + float(st.seconds)
	return utc + float(st.seconds) + float(o.get("ripen", {}).get("minutes", 20)) * 60.0

# ------------------------------------------------------------------ ages
## The age steps as ints (JSON hands them over as floats).
static func ages() -> Array:
	var out: Array = []
	for a in ContentDB.config("garden").get("ages", [10, 100, 1000]): out.append(int(a))
	return out

static func item_age(item: String) -> int:
	return int(ContentDB.item(item).get("herb", {}).get("age", 10))

static func family(item: String) -> String:
	return str(ContentDB.item(item).get("herb", {}).get("family", ""))

## The same family `tiers` age steps younger (never below the youngest it has).
static func aged_down(item: String, tiers: int) -> String:
	var fam := family(item)
	if fam == "" or tiers <= 0: return item
	var steps := ages()
	var i := steps.find(item_age(item))
	var fams: Dictionary = ContentDB.config("garden").get("families", {}).get(fam, {})
	while tiers > 0 and i > 0:
		i -= 1
		tiers -= 1
		if fams.has(str(steps[i])): item = str(fams[str(steps[i])])
	return item

## The older members of a family, youngest first.
static func older_than(item: String) -> Array:
	var fam := family(item)
	var age := item_age(item)
	var out: Array = []
	var fams: Dictionary = ContentDB.config("garden").get("families", {}).get(fam, {})
	for a in ages():
		if int(a) > age and fams.has(str(a)): out.append(str(fams[str(a)]))
	return out

## Age tiers between two herbs of a family (0 if the same age).
static func tier_gap(younger: String, older: String) -> int:
	var steps := ages()
	return maxi(0, steps.find(item_age(older)) - steps.find(item_age(younger)))

# ------------------------------------------------------------------ the harvest tap
## The perfect window as a share of the ring, by gathering rank (12% Apprentice ... 28% Grandmaster).
static func tap_window(rank: String) -> float:
	return float(ContentDB.config("garden").get("harvest", {}).get("window", {}).get(rank, 0.12))

## `timing` is how far the ring had shrunk (0..1) when the tap landed; perfect inside the window around the target.
static func tap_perfect(timing: float, rank: String) -> bool:
	var h: Dictionary = ContentDB.config("garden").get("harvest", {})
	return timing >= 0.0 and absf(timing - float(h.get("target", 0.7))) <= tap_window(rank) * 0.5

## The seed a perfect harvest of this herb can drop ("" when its seeds come only from inheritances).
static func harvest_seed(item: String) -> String:
	var g := ContentDB.config("garden")
	var fam := family(item)
	if not fam in g.get("harvest_seeds", []): return ""
	return str(g.get("seeds", {}).get(fam, ""))
