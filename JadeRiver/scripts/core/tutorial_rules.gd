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

## A place of the world a guidance step leads to (data/places.json, the systems-as-places table: {room, object, page,
## verb}); {} while that table or the row is not there.
static func place(id: String) -> Dictionary:
	return ContentDB.entry("places", id) if ContentDB.lists.has("places") else {}
