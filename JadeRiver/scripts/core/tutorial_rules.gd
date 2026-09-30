class_name TutorialRules
extends RefCounted
## Decision 43 · unlock tutorials (docs/redesign/tutorials.md): the rules over data/tutorials.json that the Tutorial
## authority, the coach and the pages share. An entry teaches one system or page:
##   - its trigger: an unlock, the first of a resource (foundation points, Realisations), the first item of a kind, the
##     first bottleneck, or only the page's first opening;
##   - its guidance chain, from the HUD button (or a place in the world) to the page, the tab and the element to use;
##   - its tour of the page: a few steps, each an anchor the page names (Page.tour_rect, HUD.tour_rect), a line of at
##     most two lines on a phone, and an optional "try it" that moves the step on when done.
## Decision 44: a late HUD power (Spirit Sense, the Presence, the Sphere, treasures, the weapon swap) has a guide as well:
## the hand on its control, whose tap plays its tour there, then the way to the page that manages it (lesson_step).
## Nothing here changes state; the Tutorial authority keeps each character's progress.

static func entries() -> Array:
	return ContentDB.all("tutorials")

static func entry(id: String) -> Dictionary:
	return ContentDB.entry("tutorials", id)

## The script a page id opens (main.gd PAGES, as tutorials.json records it): page ids that share one are one page.
static func page_script(page_id: String) -> String:
	return str(ContentDB.config("tutorials").get("page_scripts", {}).get(page_id, page_id))

static func same_page(a: String, b: String) -> bool:
	return a != "" and b != "" and page_script(a) == page_script(b)

static var _tours_of: Dictionary = {}   ## "page|tab" -> tours_for's list, for the entries as loaded (_tours_src)
static var _tours_src: Array = []

## The tours a page shows on a tab, in the order they are offered: the one for that tab first, then the page's own.
## Worked out once a page and tab (decision 45: every open page asked it twice a frame, its "?" and the coach, going
## through every entry each time); the list is shared, not to be changed.
static func tours_for(page_id: String, tab := "") -> Array:
	var all := entries()
	if not is_same(all, _tours_src):
		_tours_src = all
		_tours_of = {}
	var key := page_id + "|" + tab
	if _tours_of.has(key): return _tours_of[key]
	var exact: Array = []
	var whole: Array = []
	if page_id != "":
		for e in all:
			if (e.get("tour", []) as Array).is_empty() or not same_page(str(e.get("page", "")), page_id): continue
			var et := str(e.get("tab", ""))
			if et != "" and et == tab: exact.append(str(e.id))
			elif et == "": whole.append(str(e.id))
	_tours_of[key] = exact + whole
	return _tours_of[key]

## The tour the page's "?" plays again: the first of tours_for ("" for none).
static func tour_for(page_id: String, tab := "") -> String:
	var all := tours_for(page_id, tab)
	return str(all[0]) if not all.is_empty() else ""

## The HUD's tours (an entry on page "hud": a control the HUD shows, taught where it stands).
static func hud_entry(e: Dictionary) -> bool:
	return str(e.get("page", "")) == "hud"

## The tutorials record's version now (tutorials.json): a character's record older than an entry's `since` counts what
## it already has of that entry's system as known (decision 44 brought the late HUD powers at 2).
static func version() -> int:
	var all := entries()
	if not is_same(all, _version_src):
		_version_src = all
		_version = int(ContentDB.config("tutorials").get("version", 1))
	return _version

static var _version_src: Array = []
static var _version := 1

# ------------------------------------------------------------------ a HUD power's lesson (decision 44)
## Where a HUD entry's tour stands in its guide: the index of its control step (the hand on the power's own button,
## whose tap plays the tour), or -1 when the tour comes first (a control the play screen at rest does not show).
static func tour_at(e: Dictionary) -> int:
	var chain: Array = e.get("chain", [])
	for i in chain.size():
		if (chain[i] as Dictionary).get("tour", false): return i
	return -1

## A HUD entry whose guide goes on after its tour, to the page or tab that manages the power (the Sphere's Dao tab).
static func guide_after_tour(e: Dictionary) -> bool:
	return hud_entry(e) and tour_at(e) < (e.get("chain", []) as Array).size() - 1

## A HUD entry's guide step for what is on screen, its chain split at the control step (tour_at): before the tour is
## `toured`, the way to the control (the Bag, to set a spare weapon) and the control itself once the HUD shows it
## (`control_on`: its anchor, or the fan that holds it, found); after, the way on to the page that manages the power.
## Within that part, the last step whose place shows, as chain_step. -1 when none shows.
static func lesson_step(e: Dictionary, top_page: String, top_tab: String, toured: bool, control_on: bool) -> int:
	var chain: Array = e.get("chain", [])
	var at := tour_at(e)
	var lo := at + 1 if toured else 0
	var hi := chain.size() - 1 if toured else at
	for i in range(hi, lo - 1, -1):
		if i == at and not control_on: continue
		var st: Dictionary = chain[i]
		match str(st.get("at", "")):
			"hud", "place":
				if top_page == "": return i
			"page":
				if same_page(top_page, str(st.get("page", ""))) and (str(st.get("tab", "")) == "" or str(st.tab) == top_tab): return i
	return -1

## Where a HUD entry's guide ends, its tour seen: its last step's page, on the tab that step opens ("tab:dao") or names;
## [] when the guide ends on the HUD or on an element to use.
static func chain_goal(e: Dictionary) -> Array:
	var chain: Array = e.get("chain", [])
	if chain.is_empty(): return []
	var st: Dictionary = chain.back()
	if str(st.get("at", "")) != "page" or st.get("element", false): return []
	var tab := str(st.get("tab", ""))
	if str(st.get("anchor", "")).begins_with("tab:"): tab = str(st.anchor).trim_prefix("tab:")
	return [str(st.get("page", "")), tab]

# ------------------------------------------------------------------ triggers
## A points pool's count for the character (tutorials.json "points": id -> [authority, getter], as the HUD's badges
## read it).
static func points(c, id: String) -> int:
	return count(c, ContentDB.config("tutorials").get("points", {}).get(id, []))

## A points pool's count by the [authority, getter] pair that names it (tutorials.json "points", the HUD's
## POINT_SYSTEMS), through `counter`'s table: a name read from data is never called as a method (audit 45, BUG-06).
## 0 for a pair the table does not know.
static func count(c, pair: Array) -> int:
	var f := counter(pair)
	return int(f.call(c)) if c != null and f.is_valid() else 0

## The getter of each points pool, by its [authority, getter] pair. Each is named in code, so a renamed getter fails to
## compile; contract_tests holds every pair the data and the HUD name to a row here. An empty Callable for any other.
static func counter(pair: Array) -> Callable:
	if pair.size() != 2: return Callable()
	match "%s.%s" % pair:
		"progression.meridian_points_free": return Game.progression.meridian_points_free
		"progression.realisations_free": return Game.progression.realisations_free
		"posts.bench_points_free": return Game.posts.bench_points_free
		"posts.art_points_free": return Game.posts.art_points_free
	return Callable()

## Whether an entry's trigger holds for the character now: its unlock open (when it names one) and its kind's condition.
## A page's first opening ("page") is the coach's to see, never a trigger here.
static func triggered(c, e: Dictionary) -> bool:
	if c == null: return false
	var tr: Dictionary = e.get("trigger", {})
	var gate := str(tr.get("unlock", ""))
	if gate != "" and not Unlocks.is_unlocked(c.id, gate): return false
	match str(tr.get("kind", "")):
		"unlock": return gate != ""
		"points": return points(c, str(tr.get("points", ""))) > 0
		"item":
			var kind := str(tr.get("bag_kind", ""))
			for s in c.inventory.bag:
				if s != null and InventoryAuthority.bag_kind(str(s.id)) == kind: return true
			return false
		"bottleneck": return c.cultivator.state == "bottleneck"
		"technique":
			for s in c.cultivator.technique_slots:
				if s != null and str(s) != "": return true
			return false
	return false

# ------------------------------------------------------------------ the guidance chain
## The step of an entry's guidance chain the player stands at, from what is on screen (the top page and its tab, or
## none): the last step whose place shows. A "hud" or "place" step shows with no page open; a "page" step with its page
## on top, on its tab when it names one. -1 while another page is open.
static func chain_step(e: Dictionary, top_page: String, top_tab: String) -> int:
	var chain: Array = e.get("chain", [])
	for i in range(chain.size() - 1, -1, -1):
		var st: Dictionary = chain[i]
		match str(st.get("at", "")):
			"hud", "place":
				if top_page == "": return i
			"page":
				if same_page(top_page, str(st.get("page", ""))) and (str(st.get("tab", "")) == "" or str(st.tab) == top_tab): return i
	return -1

## Whether the chain has reached its page (and tab): its last step is the entry's own page.
static func chain_home(e: Dictionary, top_page: String, top_tab: String) -> bool:
	var chain: Array = e.get("chain", [])
	return not chain.is_empty() and chain_step(e, top_page, top_tab) == chain.size() - 1 and str((chain.back() as Dictionary).get("at", "")) == "page"

## A place of the world a guidance step leads to (data/places.json, the systems-as-places table: {id, system, page,
## room, object, stand, name, verb, ...}): the row of that id, or, for a system (or a page) of that name that lives at
## places, the one a walk there leads the character to (PlaceRules.home: its own sect's, the home one, the nearest);
## {} when the table has none.
static func place(id: String, c = null) -> Dictionary:
	if not ContentDB.lists.has("places"): return {}
	var row := ContentDB.entry("places", id)
	if row.is_empty() and c != null: row = PlaceRules.home(c, PlaceRules.system_of(id))
	return row

static var _spots: Dictionary = {}

## Every thing of the world a place step's `match` names, [room, object]: {object_type}, {opens} the page an object
## opens, {npc_service} a person whose services hold it ("shop" any shop, "page:pouches" that one).
static func place_spots(st: Dictionary) -> Array:
	var m: Dictionary = st.get("match", {})
	var key := JSON.stringify(m)
	if _spots.has(key): return _spots[key]
	var out: Array = []
	var ids: Array = ContentDB.rooms.keys()
	ids.sort()
	for rid in ids:
		for o in ContentDB.room(str(rid)).get("objects", []):
			if _matches(o, m): out.append([str(rid), str(o.get("id", ""))])
	_spots[key] = out
	return out

static func _matches(o: Dictionary, m: Dictionary) -> bool:
	if m.has("object_type"): return str(o.get("type", "")) == str(m.object_type)
	if m.has("opens"): return str(o.get("open_page", "")) == str(m.opens)
	if m.has("npc_service") and str(o.get("type", "")) == "npc":
		var want := str(m.npc_service)
		for s in ContentDB.entry("npcs", str(o.get("npc", ""))).get("services", []):
			if str(s) == want or str(s).begins_with(want + ":"): return true
	return false

## Where a place step leads the character now: data/places.json's row for its place when the table has one, else the
## nearest thing its `match` names by the ways open to the character ({room, object, name}; {} when none is reached).
static func place_for(c, st: Dictionary) -> Dictionary:
	if c == null: return {}
	var here := str(c.position.get("room", ""))
	var row := place(str(st.get("place", "")), c)
	# The table's place, when it is there for the character (the village's board goes up after the prologue) and a way
	# open to it leads there.
	if not row.is_empty() and str(row.get("room", "")) != "" and PlaceRules.visible(c, row) \
			and (str(row.room) == here or not Game.world.route(c, here, str(row.room)).is_empty()):
		var nm := str(row.get("name", ""))
		return {"room": str(row.room), "object": str(row.get("object", "")), "place": str(row.get("id", "")),
			"name": "%s · %s" % [nm.substr(0, 1).to_upper() + nm.substr(1), ContentDB.name_of("rooms", str(row.room))] if nm != "" else spot_name(str(row.room), str(row.get("object", "")))}
	var best := {}
	var best_n := 1 << 30
	for sp in place_spots(st):
		var n := 0
		if str(sp[0]) != here:
			var way: Array = Game.world.route(c, here, str(sp[0]))
			if way.is_empty(): continue
			n = way.size()
		if n < best_n:
			best_n = n
			best = {"room": str(sp[0]), "object": str(sp[1]), "name": spot_name(str(sp[0]), str(sp[1]))}
	return best

## A thing's name as the world shows it: its own, or its person's, and the room it stands in.
static func spot_name(room: String, obj: String) -> String:
	var rd := ContentDB.room(room)
	for o in rd.get("objects", []):
		if str(o.get("id", "")) != obj: continue
		var nm := str(o.get("name", ""))
		if nm == "" and str(o.get("type", "")) == "npc": nm = ContentDB.name_of("npcs", str(o.get("npc", "")))
		if nm == "": break
		return "%s · %s" % [nm, str(rd.get("name", room))]
	return str(rd.get("name", room))
