class_name TutorialRules
extends RefCounted
## Decision 43 · unlock tutorials (docs/redesign/tutorials.md): the rules over data/tutorials.json that the Tutorial
## authority, the coach and the pages share. An entry teaches one system or page:
##   - its trigger: an unlock, the first of a resource (foundation points, Realisations), the first item of a kind, the
##     first bottleneck, or only the page's first opening;
##   - its guidance chain, from the HUD button (or a place in the world) to the page, the tab and the element to use;
##   - its tour of the page: a few steps, each an anchor the page names (Page.tour_rect, HUD.tour_rect), a line of at
##     most two lines on a phone, and an optional "try it" that moves the step on when done.
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

## The tours a page shows on a tab, in the order they are offered: the one for that tab first, then the page's own.
static func tours_for(page_id: String, tab := "") -> Array:
	var exact: Array = []
	var whole: Array = []
	if page_id == "": return exact
	for e in entries():
		if (e.get("tour", []) as Array).is_empty() or not same_page(str(e.get("page", "")), page_id): continue
		var et := str(e.get("tab", ""))
		if et != "" and et == tab: exact.append(str(e.id))
		elif et == "": whole.append(str(e.id))
	return exact + whole

## The tour the page's "?" plays again: the first of tours_for ("" for none).
static func tour_for(page_id: String, tab := "") -> String:
	var all := tours_for(page_id, tab)
	return str(all[0]) if not all.is_empty() else ""

## The HUD's tours (an entry on page "hud": a control the HUD shows, taught where it stands).
static func hud_entry(e: Dictionary) -> bool:
	return str(e.get("page", "")) == "hud"

# ------------------------------------------------------------------ triggers
## A points pool's count for the character (tutorials.json "points": id -> [authority, getter], as the HUD's badges
## read it).
static func points(c, id: String) -> int:
	var row: Array = ContentDB.config("tutorials").get("points", {}).get(id, [])
	if c == null or row.size() < 2 or Game.get(str(row[0])) == null: return 0
	return int(Game.get(str(row[0])).call(str(row[1]), c))

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
