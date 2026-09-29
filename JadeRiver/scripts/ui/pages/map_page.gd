extends Page
## World map (S18, Part 9.6), P5 as the framed painting of the zone (docs/page_identity.md row 7; mockups 16 and
## 16_resources; decisions 11, 17 and 25). The zone's landscape fills the screen inside a lacquered frame: the valley is
## the painting of tools/ui/build_valley_map.py, and a zone with no painting yet is drawn from tokens in the same manner
## (islands in a sea of cloud; dark isles under the star field's lanterns). Every area is a glowing node where zones.json
## places it (jade if you may walk in, gold where you stand, a padlock if locked) on dotted routes along the rooms'
## portals, the chosen area's way lit gold. The tracked quest's lantern, the world events' blossoms and the paths above
## mark their areas; a plate names each area, no more. One layout pass places every mark and plate
## so none touches another, a node or the frame's furniture (decision 17). The card at the right shows the chosen area
## (its picture, band, the quest and event there, its rooms with hazards, paths above and bosses), where each herb, ore
## and fish is found (Resources), or the tracked quests and events (Objectives), each with Track Route. The zone tags
## hang from the top rail with the Heaven Ranking beside them. The page only reads, and travels by auto_path.

const PAINT := Rect2(0, 0, 1280, 640)
## Where a region's `map` [0..1] lands: build_valley_map.py's MAP_RECT (24, 34, 424, 276) art px, drawn x2.
const MAP := Rect2(48, 68, 848, 552)
const EDGE := 17.0                      # the frame's width
const FOOT := 636.0                     # the foot band's top
const CARD := Rect2(920, 84, 336, 556)
const PIC := Rect2(40, 12, 256, 144)    # the area's picture, in the card
const BANNER := Rect2(66, 84, 56, 132)
## Zones with a painting of their own: zone -> the stem of art/ui/maps/<stem>_map.png and <stem>_<region>.png.
const PAINTED := {"jade_river_valley": "valley"}
const STARRY := ["lantern_star_field"]
const NODE_R := {"here": 11.0, "open": 9.0, "locked": 13.0}
const PLATE_TEXT := 16                  # a plate's name
const RING := 7.0                       # the chosen node's ring, outside its disc
const TOUCH := 2.0                      # nothing on the painting comes nearer another than this
const LEADER := 14.0                    # each step farther out a mark or plate may stand, on a leader
const VIEWS := ["areas", "resources", "objectives", "places"]
const VIEW_ICON := {"areas": "world_map", "resources": "craft_foraging", "objectives": "quest", "places": "shop"}
## The gathering kinds: object type -> [its name, its marker, the craft whose rank it asks].
const KINDS := {"herb_patch": ["ui.map.herbs", "herb_marker", "herb_gathering"], "ore_vein": ["ui.map.ores", "ore_marker", "mining"],
	"fishing_spot": ["ui.map.fish", "fish_marker", "fishing"]}
const RANKS := ["apprentice", "adept", "expert", "master"]
## A region's kind, by the type most of its rooms have; any other is the wilds.
const TYPE_KIND := {"town": "town", "home": "town", "interior": "town", "rest": "town", "sect": "sect", "dungeon": "dungeon",
	"secret": "dungeon", "boss_arena": "dungeon", "trial": "dungeon"}
## The places tried round a pin: below, above, right, left, then the corners. A place on a side also slides along it,
## SLIDE px a step (while half the box and half its pin still face each other, so it stays beside its pin), and each is
## tried a LEADER step and two out.
const PLATE_WAYS := ["b", "t", "r", "l", "dr", "dl", "ur", "ul"]
const SLIDES := [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6, 7, -7, 8, -8]
const SLIDE := 6.0
const MARK_WAYS := {"lantern": ["r", "ur", "dr", "l", "ul", "dl", "t", "b"], "blossom": ["l", "ul", "dl", "r", "ur", "dr", "t", "b"],
	"wind": ["ur", "ul", "t", "r", "l", "dr", "dl", "b"], "res": ["r", "l", "ur", "ul", "dr", "dl", "t", "b"], "place": ["r", "l", "ur", "ul", "dr", "dl", "t", "b"]}
## The legend along the foot for each view, and the width of each key's glyph.
const LEGEND := {"areas": ["available", "here", "locked", "route", "tracked", "event"], "resources": ["available", "here", "holds", "locked", "route"],
	"objectives": ["tracked", "event", "here", "locked", "route"], "places": ["available", "here", "place", "locked", "route"]}
const LEGEND_W := {"route": 26.0, "locked": 12.0, "tracked": 12.0}
const MARK_SIZE := {"lantern": Vector2(22, 30), "blossom": Vector2(22, 22), "wind": Vector2(40, 24), "res": Vector2(44, 44), "place": Vector2(44, 44)}
## The frame's cloud-scroll corner (72 px, drawn at the top left and mirrored): cubic curves in its own px.
const CURLS := [[Vector2(14, 58), Vector2(14, 34), Vector2(34, 14), Vector2(58, 14)], [Vector2(20, 44), Vector2(20, 34), Vector2(26, 28), Vector2(34, 28)],
	[Vector2(34, 28), Vector2(40, 28), Vector2(42, 32), Vector2(40, 36)], [Vector2(40, 36), Vector2(38, 40), Vector2(32, 38), Vector2(34, 34)],
	[Vector2(40, 22), Vector2(46, 20), Vector2(52, 22), Vector2(54, 26)], [Vector2(18, 50), Vector2(16, 56), Vector2(18, 62), Vector2(22, 64)]]

var sel := ""                  # the chosen area (a region id)
var zone_id := "jade_river_valley"
var view := "areas"
var res_kind := "herb_patch"
var res_item := ""
var goal := ""                 # the chosen objective: a quest id, or "@" and an event id
## Decision 43, the Places view: the kind of place chosen (data/places.json `kind`) and the place itself (its id), the
## one its card names and its Go there walks to.
var place_kind := "notice_board"
var place_id := ""
var chosen_at := -10.0         # when the chosen area changed: its way lights dot by dot
## The last layout pass (drawn from, and read by the tests): {plates: {rid: {rect, far, way, name}}, marks: {id: {rect, kind,
## live}}, pins: [Rect2], keep: [Rect2], bounds: Rect2, hidden: [the areas whose plate found no place]}.
var layout := {}
var _layout_key := ""
var _cache := {}
static var _zones := {}
static var _shade: GradientTexture2D

func _init() -> void:
	title = Tx.t("ui.map.jade_river_valley")
	frame_rect = WINDOW_SCREEN
	identity = Identity.new("soil", false, "own", "painting_framed_card_right", 0.25)

func setup() -> void:
	var ch = c()
	if ch == null: return
	var here_zone := str(ContentDB.zone_of_room(str(ch.position.get("room", ""))).get("id", ""))
	if here_zone != "": zone_id = here_zone
	# A tag per zone, a locked one for a zone not yet set foot in; the Heaven Ranking beside them (S49).
	tabs = []
	for z in ContentDB.all("zones"):
		var tb := {"id": str(z.id), "label": str(z.get("name", z.id))}
		if str(z.id) != "jade_river_valley" and str(z.id) != here_zone and not _zone_seen(str(z.id)): tb.locked = Tx.t("ui.map.zone_locked") % tb.label
		tabs.append(tb)
	tabs.append({"id": "ranking", "label": Tx.t("ui.map.ranking")})
	for i in tabs.size():
		if str(tabs[i].id) == zone_id: tab = i
	var v := str(args.get("view", args.get("tab", "")))
	if v in VIEWS: view = v
	# A place named (a tap on its mark on the minimap, decision 43): the Places view on it.
	var pl := PlaceRules.get_place(str(args.get("place", "")))
	if not pl.is_empty():
		view = "places"
		place_kind = str(pl.kind)
		place_id = str(pl.id)
	elif str(args.get("kind", "")) != "": place_kind = str(args.kind)
	sel = ""
	_sync_tab()

func _process(delta: float) -> void:
	super._process(delta)
	_sync_tab()

## The tab names the zone (or the Heaven Ranking); a zone newly shown chooses where you stand, else its first known area.
func _sync_tab() -> void:
	if tabs.is_empty(): return
	var id := str(tabs[tab].id)
	title = Tx.t("ui.map.ranking_title") if id == "ranking" else str(tabs[tab].label)
	if id == "ranking" or (id == zone_id and sel != ""): return
	zone_id = id
	var z := _zone(zone_id)
	var ch = c()
	sel = str(z.node_of.get(str(ch.position.get("room", "")), "")) if ch != null else ""
	for rid in z.order:
		if sel == "" and visited(rid): sel = rid
	if sel == "" and not z.order.is_empty(): sel = z.order[0]
	chosen_at = t

func _ranking() -> bool:
	return not tabs.is_empty() and str(tabs[tab].id) == "ranking"

func _zone_seen(zid: String) -> bool:
	for id in ContentDB.zone(zid).get("rooms", []):
		if Game.account.visited_rooms.has(str(id)): return true
	return false

func regions() -> Array:
	return ContentDB.zone(zone_id).get("regions", []).filter(func(r): return not r.get("hidden", false))

func region_rooms(rid: String) -> Array:
	return _zone(zone_id).rooms.get(rid, [])

func visited(rid: String) -> bool:
	return region_rooms(rid).any(func(id): return Game.account.visited_rooms.has(id))

func _region(rid: String) -> Dictionary:
	for r in regions():
		if str(r.id) == rid: return r
	return {}

# ------------------------------------------------------------------ the zone as the painting places it
## A zone as the painting draws it (built once): its placed regions in data order, each one's anchor, its rooms, the
## node every room of the zone shows at, and the links between neighbouring areas. The rule for what the painting does
## not place: a room whose region is hidden (a story instance, somewhere unmapped) shows at the nearest placed room's
## area by portals, else the zone's first; a region without a `map` position stands at the mean of its placed
## neighbours, moved clear of every other node.
static func _zone(zid: String) -> Dictionary:
	if _zones.has(zid): return _zones[zid]
	var zd := ContentDB.zone(zid)
	var order: Array = []
	var rooms := {}
	for r in zd.get("regions", []):
		if r.get("hidden", false): continue
		order.append(str(r.id))
		rooms[str(r.id)] = []
	var ids: Array = []
	for id in ContentDB.rooms:
		var rd: Dictionary = ContentDB.rooms[id]
		if str(rd.get("zone", "")) != zid: continue
		ids.append(str(id))
		if rooms.has(str(rd.get("region", ""))) and not rd.get("instanced", false): rooms[str(rd.region)].append(str(id))
	ids.sort()
	for rid in rooms: rooms[rid].sort()
	var node_of := {}
	for id in ids:
		if rooms.has(str(ContentDB.room(id).get("region", ""))): node_of[id] = str(ContentDB.room(id).region)
	var first := str(ContentDB.room(str(zd.get("start_room", ""))).get("region", ""))
	if not rooms.has(first): first = str(order[0]) if not order.is_empty() else ""
	var placed := node_of.duplicate()
	for id in ids:
		if not node_of.has(id): node_of[id] = _nearest(id, placed, first)
	var links: Array = []
	for id in ids:
		for p in ContentDB.room(id).get("portals", []):
			var to := str(p.get("to", ""))
			if not node_of.has(to) or node_of[to] == node_of[id]: continue
			var pair := [node_of[id], node_of[to]]
			pair.sort()
			if not pair in links: links.append(pair)
	var anchor := {}
	var area := _map_rect(zid)
	for r in zd.get("regions", []):
		if rooms.has(str(r.id)) and r.has("map"): anchor[str(r.id)] = area.position + Vector2(float(r.map[0]), float(r.map[1])) * area.size
	for rid in order:
		if anchor.has(rid): continue
		var near: Array = links.filter(func(l): return rid in l).map(func(l): return l[0] if l[1] == rid else l[1]).filter(func(n): return anchor.has(n))
		var p := area.get_center()
		if not near.is_empty():
			p = Vector2.ZERO
			for n in near: p += anchor[n] / float(near.size())
		for k in 80:
			var q := p + Vector2.from_angle(k * 2.4) * (k * 6.0)
			if area.has_point(q) and anchor.values().all(func(o): return o.distance_to(q) >= 56.0):
				p = q
				break
		anchor[rid] = p
	_zones[zid] = {"order": order, "rooms": rooms, "node_of": node_of, "links": links, "anchor": anchor}
	return _zones[zid]

## Where a region's `map` [0..1] lands: on a painting, its build script's map rect; on a zone drawn from tokens, the open
## painting clear of the title plate, the pennant and the card.
static func _map_rect(zid: String) -> Rect2:
	return MAP if PAINTED.has(zid) else Rect2(160, 112, 720, 496)

## The area of the nearest room (by portals, within its zone) that the painting places; `fallback` when none is reached.
static func _nearest(room_id: String, placed: Dictionary, fallback: String) -> String:
	var seen := {room_id: true}
	var queue: Array = [room_id]
	var head := 0
	while head < queue.size():
		var at: String = queue[head]
		head += 1
		if placed.has(at): return placed[at]
		for p in WorldRules.ways_out(at):
			var to := str(p.get("to", ""))
			if to != "" and not seen.has(to) and ContentDB.room_zone.get(to, "") == ContentDB.room_zone.get(room_id, ""):
				seen[to] = true
				queue.append(to)
	return fallback

## The areas you may walk into now: every area with a room you have been to, and each one a portal open to you leads
## to from one of those rooms.
func _reach(ch, z: Dictionary) -> Dictionary:
	var key := "reach|%s|%d|%s|%d" % [zone_id, Game.account.visited_rooms.size(), ch.cultivator.realm_key, ch.quests.done.size()]
	if _cache.has(key): return _cache[key]
	var out := {}
	for id in z.node_of:
		if not Game.account.visited_rooms.has(id): continue
		out[z.node_of[id]] = true
		for p in ContentDB.room(id).get("portals", []):
			var to := str(p.get("to", ""))
			if z.node_of.has(to) and Game.world.portal_open(ch, id, p): out[z.node_of[to]] = true
	_cache[key] = out
	return out

## The way from where you stand to area `rid` (or to `room` in it) by the portals open to you: {room: the first of its
## rooms reached, path: the areas on the way, the first where you stand}; {} when there is none, or you are there.
func _route(ch, rid: String, room := "") -> Dictionary:
	var from := str(ch.position.get("room", ""))
	var key := "route|%s|%s|%s|%d|%d" % [from, rid, room, Game.account.visited_rooms.size(), ch.quests.done.size()]
	if _cache.has(key): return _cache[key]
	if _cache.size() > 300: _cache.clear()
	var z := _zone(zone_id)
	var best: Array = []
	var target := ""
	for id in ([room] if room != "" else z.rooms.get(rid, [])):
		var way: Array = Game.world.route(ch, from, str(id))
		if not way.is_empty() and (best.is_empty() or way.size() < best.size()):
			best = way
			target = str(id)
	var out := {}
	if not best.is_empty():
		var path: Array = [str(z.node_of.get(from, ""))]
		for s in best:
			var n := str(z.node_of.get(str(s.to), ""))
			if n != "" and n != str(path.back()): path.append(n)
		out = {"room": target, "path": path}
	_cache[key] = out
	return out

## Where each herb, ore and fish of the zone is found (built once a zone): {kind: {item: {at: {rid: [[room, n]]}, rank,
## regrow}}}, from its rooms' patches, veins and spots (Game.posts.outputs_of names what each gives).
func _res() -> Dictionary:
	var z := _zone(zone_id)
	if z.has("res"): return z.res
	var out := {}
	for k in KINDS: out[k] = {}
	for id in z.node_of:
		for o in ContentDB.room(id).get("objects", []):
			var k := str(o.get("type", ""))
			if not out.has(k): continue
			for g in Game.posts.outputs_of(o):
				var e: Dictionary = out[k].get(str(g.item), {"at": {}, "rank": "", "regrow": 0.0})
				var spots: Array = e.at.get(z.node_of[id], [])
				var row: Array = spots.filter(func(s): return s[0] == id)
				if row.is_empty(): spots.append([id, 1])
				else: row[0][1] += 1
				e.at[z.node_of[id]] = spots
				var rk := str(o.get("rank", ""))
				if rk != "" and (e.rank == "" or RANKS.find(rk) < RANKS.find(str(e.rank))): e.rank = rk
				var rg := float(o.get("regrow_s", 0.0))
				if rg > 0.0 and (float(e.regrow) <= 0.0 or rg < float(e.regrow)): e.regrow = rg
				out[k][str(g.item)] = e
	z.res = out
	return out

## A resource is known once you have reached an area that holds it (the rest are greyed: in areas not yet reached).
func _known(e: Dictionary) -> bool:
	return e.at.keys().any(func(rid): return visited(rid))

## The kind's resources, known first, then by the rank they ask and their names.
func _res_list(kind: String) -> Array:
	var all: Dictionary = _res()[kind]
	var ids: Array = all.keys()
	ids.sort_custom(func(a, b):
		var ka := _known(all[a])
		var kb := _known(all[b])
		if ka != kb: return ka
		var ra := RANKS.find(str(all[a].rank))
		var rb := RANKS.find(str(all[b].rank))
		if ra != rb: return ra < rb
		return ContentDB.item_name(a) < ContentDB.item_name(b))
	return ids

# ------------------------------------------------------------------ what the painting shows now
## Each area's state (here, open or locked), the chosen area's way, the quests and events on the map, the resource the
## Resources card holds, and which nodes wear the ring.
func _model(ch) -> Dictionary:
	var z := _zone(zone_id)
	var here := str(z.node_of.get(str(ch.position.get("room", "")), ""))
	var reach := _reach(ch, z)
	var state := {}
	for rid in z.order:
		state[rid] = "here" if rid == here else ("open" if reach.has(rid) and not _region(rid).get("planned", false) else "locked")
	var events := {}
	var now := Clock.now_utc()
	for o in Game.calendar.schedule():
		var rid := str(z.node_of.get(str(o.room), ""))
		if rid == "": continue
		if not events.has(rid): events[rid] = []
		events[rid].append(o.merged({"live": now >= float(o.start)}))
	var quests: Array = Game.quest.tracker(ch)
	var lanterns := {}
	var guide: String = Game.world.guide_target(ch)
	for q in quests:
		var rid := str(z.node_of.get(str(q.target_room), ""))
		if rid != "" and (view == "objectives" or str(q.target_room) == guide): lanterns[rid] = true
	# Decision 43: a tutorial leading to a place lights its area's lantern too.
	var taught := str(z.node_of.get(Game.tutorials.goal_of(ch), ""))
	if taught != "": lanterns[taught] = true
	var m := {"z": z, "here": here, "state": state, "events": events, "quests": quests, "lanterns": lanterns, "rings": {}}
	if view == "resources":
		var list := _res_list(res_kind)
		if not res_item in list: res_item = str(list[0]) if not list.is_empty() and _known(_res()[res_kind][list[0]]) else ""
		m.res = _res()[res_kind].get(res_item, {})
		for rid in m.res.get("at", {}): m.rings[rid] = true
		var near := ""
		var best := 1 << 30
		for rid in m.rings:
			var way := _route(ch, rid)
			var n: int = 0 if rid == here else (way.path.size() if not way.is_empty() else 1 << 20)
			if n < best:
				best = n
				near = rid
		m.near = near if near != "" else here
		m.route = _route(ch, near) if near != "" else {}
	elif view == "places":
		# Decision 43: every area that holds a place of the chosen kind wears the ring and its mark; the chosen place
		# (the one named, else the nearest by the ways open to you, the room you stand in first) has the way lit.
		var at := _places_of(ch, place_kind)
		m.places_at = at
		for rid in at: m.rings[rid] = true
		var here_room := str(ch.position.get("room", ""))
		var chosen := {}
		var best := 1 << 30
		for rid in at:
			for r in at[rid]:
				var n: int = 0 if str(r.room) == here_room else (_route(ch, rid, str(r.room)).get("path", []).size() if not _route(ch, rid, str(r.room)).is_empty() else 1 << 20)
				if str(r.id) == place_id: n = -1
				if n < best:
					best = n
					chosen = r
		m.place = chosen
		if not chosen.is_empty():
			place_id = str(chosen.id)
			sel = str(m.z.node_of.get(str(chosen.room), sel))
		m.route = {} if chosen.is_empty() or str(chosen.room) == here_room else _route(ch, sel, str(chosen.room))
	elif view == "objectives":
		m.objectives = _objectives(ch, m)
		var o: Dictionary = {}
		for it in m.objectives:
			if o.is_empty() or str(it.id) == goal: o = it
		m.goal = o
		if not o.is_empty() and str(o.rid) != "": sel = str(o.rid)
		m.route = _route(ch, sel, str(o.room)) if str(o.get("room", "")) != "" else {}
		m.rings[sel] = true
	else:
		m.route = {} if sel == here else _route(ch, sel)
		m.rings[sel] = true
	return m

## The Objectives card's rows: the tracked quests, then the zone's world events, each with where it leads.
func _objectives(ch, m: Dictionary) -> Array:
	var out: Array = []
	for q in m.quests:
		var line: Dictionary = q.lines[0] if not q.lines.is_empty() else {}
		out.append({"id": str(q.quest), "event": false, "name": str(q.name), "line": str(line.get("text", "")),
			"count": "%d / %d" % [int(line.have), int(line.need)] if int(line.get("need", 1)) > 1 else "", "room": str(q.target_room),
			"rid": str(m.z.node_of.get(str(q.target_room), "")), "main": QuestAuthority.leads(str(q.kind))})
	for rid in m.events:
		for o in m.events[rid]:
			var ev := CalendarRules.event(str(o.id))
			var left := float(o.end) - Clock.now_utc() if o.live else float(o.start) - Clock.now_utc()
			out.append({"id": "@" + str(o.id), "event": true, "live": o.live, "name": str(ev.get("name", o.id)), "room": str(o.room), "rid": rid,
				"line": (Tx.t("ui.map.under_way") if o.live else Tx.t("ui.map.begins_in")) % UiKit.span(left), "count": ""})
	return out

# ------------------------------------------------------------------ the frame's own surface
func content_rect() -> Rect2:
	return Rect2(176, 104, 928, 512) if _ranking() else Rect2(EDGE, EDGE, 1280 - EDGE * 2.0, FOOT - EDGE)

## The painting of the zone under its vignette, the foot band, the lacquered frame and the sect's pennant.
func draw_surface(_r: Rect2) -> void:
	var z := _zone(zone_id)
	var art := SpriteCache.tex("res://art/ui/maps/%s_map.png" % PAINTED[zone_id]) if PAINTED.has(zone_id) else null
	if art != null: draw_texture_rect(art, PAINT, false)
	else: _paint_tokens(PAINT, z)
	if _shade == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.55, 1.0])
		g.colors = PackedColorArray([Color(UiKit.INK, 0.0), Color(UiKit.INK, 0.0), Color(UiKit.INK, 0.55)])
		_shade = GradientTexture2D.new()
		_shade.gradient = g
		_shade.fill = GradientTexture2D.FILL_RADIAL
		_shade.fill_from = Vector2(0.5, 0.55)
		_shade.fill_to = Vector2(1.25, 0.55)
	draw_texture_rect(_shade, PAINT, false)
	if _ranking(): draw_rect(PAINT, Color(UiKit.INK, 0.5))
	_vgrad(Rect2(0, FOOT, 1280, 720 - FOOT), UiKit.SURFACE.soil.darkened(0.4), UiKit.SURFACE.soil.darkened(0.58))
	ground(Rect2(0, FOOT, 1280, 720 - FOOT), UiKit.SURFACE.soil.darkened(0.4))
	_frame()
	_banner()

## The lacquered frame round the whole screen: timber, a bronze fillet, a gold line and a pale inner edge, a shadow
## falling inward, and a bronze cloud-scroll at each corner.
func _frame() -> void:
	var full := Rect2(Vector2.ZERO, Vector2(1280, 720))
	for i in 6: draw_rect(full.grow(-EDGE - 2.0 - i * 4.0), Color(UiKit.INK, 0.4 * (1.0 - i / 6.0)), false, 4.0)
	for band in [[0.0, 3.0, UiKit.SURFACE.wood_dark], [3.0, 4.0, Color(UiKit.PALE_GOLD, 0.18)], [4.0, 12.0, UiKit.SURFACE.soil.darkened(0.15)],
			[12.0, 14.0, UiKit.BRONZE.darkened(0.3)], [14.0, 16.0, UiKit.SURFACE.gourd], [16.0, 17.0, Color(UiKit.PALE_GOLD, 0.45)]]:
		draw_rect(full.grow(-(float(band[0]) + float(band[1])) * 0.5), band[2], false, float(band[1]) - float(band[0]))
	for corner in [[Vector2.ZERO, Vector2(1, 1)], [Vector2(1280, 0), Vector2(-1, 1)], [Vector2(0, 720), Vector2(1, -1)], [Vector2(1280, 720), Vector2(-1, -1)]]:
		for cv in CURLS:
			var pts := _cubic(cv.map(func(p): return corner[0] + p * corner[1]))
			draw_polyline(pts, UiKit.SURFACE.gourd, 3.0, true)
		draw_circle(corner[0] + Vector2(16, 16) * corner[1], 5.5, UiKit.INK, true, -1.0, true)
		draw_circle(corner[0] + Vector2(16, 16) * corner[1], 4.0, UiKit.GOLD, true, -1.0, true)

## The sect's pennant hung at the upper left: a red cloth on a gilt rod, a gold border, the jade-leaf emblem, two tassels.
func _banner() -> void:
	var o := BANNER.position
	draw_rect(Rect2(o + Vector2(-8, 2), Vector2(72, 6)), Color(UiKit.INK, 0.5))
	draw_rect(Rect2(o + Vector2(-8, 0), Vector2(72, 6)), UiKit.SURFACE.gourd)
	draw_rect(Rect2(o + Vector2(-8, 0), Vector2(72, 2)), UiKit.GOLD)
	var dark := UiKit.BLOOD.darkened(0.35)
	var lit := UiKit.BLOOD.lerp(UiKit.RED, 0.2)
	draw_polygon(PackedVector2Array([o + Vector2(0, 6), o + Vector2(28, 6), o + Vector2(28, 118), o + Vector2(0, 102)]), PackedColorArray([dark, lit, lit, dark]))
	draw_polygon(PackedVector2Array([o + Vector2(28, 6), o + Vector2(56, 6), o + Vector2(56, 102), o + Vector2(28, 118)]), PackedColorArray([lit, dark, dark, lit]))
	draw_rect(Rect2(o + Vector2(6, 12), Vector2(44, 88)), Color(UiKit.PALE_GOLD, 0.45), false, 1.0)
	var e := o + Vector2(10, 34)
	draw_arc(e + Vector2(18, 18), 15.0, 0.0, TAU, 40, UiKit.PALE_GOLD, 2.0, true)
	for leaf in [[Vector2(18, 8), Vector2(22, 12), Vector2(22, 18), Vector2(18, 22), Vector2(14, 18), Vector2(14, 12)],
			[Vector2(9, 14), Vector2(14, 14), Vector2(18, 18), Vector2(18, 22), Vector2(13, 22), Vector2(9, 18)],
			[Vector2(27, 14), Vector2(22, 14), Vector2(18, 18), Vector2(18, 22), Vector2(23, 22), Vector2(27, 18)]]:
		var pts := _cubic([e + leaf[0], e + leaf[1], e + leaf[2], e + leaf[3]]) + _cubic([e + leaf[3], e + leaf[4], e + leaf[5], e + leaf[0]])
		draw_colored_polygon(pts, UiKit.BRIGHT_JADE)
		draw_polyline(pts + PackedVector2Array([pts[0]]), UiKit.INK, 1.0, true)
	draw_polyline(_cubic([e + Vector2(11, 26), e + Vector2(15, 28.5), e + Vector2(21, 28.5), e + Vector2(25, 26)]), UiKit.PALE_GOLD, 2.0, true)
	for x in [10.0, 42.0]:
		draw_rect(Rect2(o + Vector2(x, 117), Vector2(4, 16)), Color(UiKit.INK, 0.5))
		draw_rect(Rect2(o + Vector2(x, 116), Vector2(4, 16)), UiKit.GOLD)

## A cubic curve through four points as a polyline.
static func _cubic(p: Array, n := 12) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n + 1:
		var s := i / float(n)
		var u := 1.0 - s
		out.append(p[0] * u * u * u + p[1] * 3.0 * u * u * s + p[2] * 3.0 * u * s * s + p[3] * s * s * s)
	return out

## A rect filled top to bottom from `top` to `foot`.
func _vgrad(r: Rect2, top: Color, foot: Color) -> void:
	draw_polygon(PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]), PackedColorArray([top, top, foot, foot]))

## The title plate: dark timber in a bronze edge, the map glyph, and "World map" over the zone's name.
func title_rect() -> Rect2:
	return Rect2(80, 44, minf(UiKit.text_width(title, UiKit.D_DISPLAY, true), 300.0) + 24.0, 32)

func _plate_rect() -> Rect2:
	return Rect2(30, 26, title_rect().end.x + 10.0 - 30.0, 56)

func draw_title_mount(r: Rect2) -> void:
	var p := _plate_rect()
	draw_rect(Rect2(p.position + Vector2(0, 4), p.size), Color(UiKit.INK, 0.45))
	draw_rect(p.grow(1), UiKit.INK)
	draw_rect(p, UiKit.BRONZE)
	_vgrad(p.grow(-2), UiKit.SURFACE.wood_dark, UiKit.SURFACE.soil.darkened(0.15))
	draw_rect(p.grow(-2), Color(UiKit.PALE_GOLD, 0.25), false, 1.0)
	ground(p, UiKit.SURFACE.wood_dark)
	icon_at(Rect2(p.position.x + 16, p.get_center().y - 16, 32, 32), "world_map")
	text(Vector2(r.position.x + 12, p.position.y + 18), Tx.t("ui.map.caption").to_upper(), 14, UiKit.MIST)

## The zone tags hang from the top rail after the title plate, each as wide as its name; the gaps close up to keep them
## clear of the close button.
func tab_rects() -> Array:
	var out: Array = []
	var x0 := _plate_rect().end.x + 26.0
	var room := frame_rect.end.x - 72.0 - 16.0 - x0
	var ws: Array = _tag_widths(_tag_size())
	var total: float = ws.reduce(func(a, b): return a + b, 0.0)
	var gap := clampf((room - total) / maxf(1.0, ws.size() - 1.0), 4.0, 12.0)
	var k := minf(1.0, (room - gap * (ws.size() - 1)) / maxf(1.0, total))
	var x := x0
	for w in ws:
		out.append(Rect2(roundf(x), 26, roundf(w * k), 48))
		x += w * k + gap
	return out

## Each tag's width for its name at `size`, and the size the names take: 18, or 16 when they would not all fit.
func _tag_widths(size: int) -> Array:
	return tabs.map(func(tb): return UiKit.text_width(str(tb.label), size) + 28.0 + (20.0 if tb.has("locked") else 0.0))

func _tag_size() -> int:
	var room := frame_rect.end.x - 72.0 - 16.0 - (_plate_rect().end.x + 26.0) - 12.0 * (tabs.size() - 1)
	return 18 if float(_tag_widths(18).reduce(func(a, b): return a + b, 0.0)) <= room else 16

func draw_tab(r: Rect2, i: int, state: String) -> void:
	draw_line(Vector2(r.get_center().x, 12), Vector2(r.get_center().x, r.position.y), UiKit.SURFACE.gourd, 2.0)
	_timber(r, state == "selected")
	var ts := _tag_size()
	text(r.position + Vector2(14, 24 + ts * 0.35), str(tabs[i].label), ts, UiKit.PALE_GOLD if state == "selected" else (UiKit.HOLLOW if state == "disabled" else UiKit.PAPER),
		HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28.0 - (18.0 if state == "disabled" else 0.0))

## A tag or tablet of dark timber in a bronze edge; lit, it is jade in a gold edge.
func _timber(r: Rect2, lit: bool) -> void:
	draw_rect(Rect2(r.position + Vector2(0, 3), r.size), Color(UiKit.INK, 0.4))
	draw_rect(r.grow(1), UiKit.INK)
	draw_rect(r, UiKit.SURFACE.gourd if lit else UiKit.BRONZE.darkened(0.3))
	var top: Color = UiKit.JADE_SHADOW if lit else UiKit.SURFACE.soil
	_vgrad(r.grow(-2), top, UiKit.SURFACE.cloth if lit else UiKit.SURFACE.soil.darkened(0.4))
	draw_rect(r.grow(-2), Color(UiKit.BRIGHT_JADE, 0.35) if lit else Color(UiKit.PALE_GOLD, 0.12), false, 1.0)
	ground(r, top)

# ------------------------------------------------------------------ the painting's areas
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	if _ranking():
		_draw_ranking(ch)
		return
	var m := _model(ch)
	tour_mark("map", MAP)   # decision 43: a tour's anchors
	tour_mark("card", CARD)
	_draw_routes(m)
	var placed := _place(ch, m)
	for rid in m.z.order:
		var p: Vector2 = m.z.anchor[rid]
		_node(p, str(m.state[rid]), m.rings.has(rid))
	for id in placed.marks:
		var mk: Dictionary = placed.marks[id]
		match str(mk.kind):
			"lantern": _lantern(mk.rect.get_center(), 1.0)
			"blossom": _blossom(mk.rect.get_center(), mk.live, 1.0)
			"wind": _wind(mk.rect.position + Vector2(4, 14))
			"res": _res_disc(mk.rect.get_center(), res_item)
			"place":
				# Decision 43: the kind's icon in a gold ring beside each area that holds one; a tap offers the walk there.
				var prid := str(id).get_slice(":", 1)
				_res_disc(mk.rect.get_center(), str(PlaceRules.kinds().get(place_kind, {}).get("icon", "")))
				region(mk.rect, "place_at", prid)
	for rid in placed.plates:
		var pl: Dictionary = placed.plates[rid]
		if int(pl.far) > 0 or str(pl.way).length() == 2: _leader(m.z.anchor[rid], float(NODE_R[m.state[rid]]), pl.rect)
		_plate(pl.rect, str(pl.name), m.state[rid] == "locked")
		region(pl.rect, "sel", rid)
	for rid in m.z.order: region(Rect2(m.z.anchor[rid] - Vector2(30, 30), Vector2(60, 60)), "sel", rid)
	# The card slides in from the frame's edge as the page opens.
	var dx := (1.0 - unfold(0.2)) * (1280.0 - CARD.position.x)
	draw_set_transform(Vector2(dx, 0))
	_card_face(CARD)
	match view:
		"resources": _card_resources(ch, m, CARD)
		"objectives": _card_objectives(ch, m, CARD)
		"places": _card_places(ch, m, CARD)
		_: _card_area(ch, m, CARD)
	draw_set_transform(Vector2.ZERO)
	_draw_foot()

## The routes between neighbouring areas as dotted lines, pale where both ends are open and dim into a locked one; the
## way to the chosen area lit gold, dot by dot from where you stand.
func _draw_routes(m: Dictionary) -> void:
	for l in m.z.links:
		var open: bool = m.state[l[0]] != "locked" and m.state[l[1]] != "locked"
		for p in _dots(m, l[0], l[1], 10.0 if open else 9.0):
			draw_circle(p, 2.0 if open else 1.5, Color(UiKit.PAPER.lerp(UiKit.PALE_GOLD, 0.6), 0.8) if open else Color(UiKit.PAPER, 0.3), true, -1.0, true)
	var path: Array = m.route.get("path", []).filter(func(rid): return rid != "")
	var dots: Array = []
	for i in range(1, path.size()): dots.append_array(_dots(m, path[i - 1], path[i], 10.0))
	var lit := 1.0 if UiKit.reduce_motion() else clampf((t - chosen_at) / 0.3, 0.0, 1.0) * dots.size()
	for i in dots.size():
		var a := clampf(lit - i, 0.0, 1.0)
		draw_circle(dots[i], 5.0, Color(UiKit.GOLD, 0.45 * a * _halo()), true, -1.0, true)
		draw_circle(dots[i], 2.5, Color(UiKit.PALE_GOLD, a), true, -1.0, true)

## The dots of a route from area `a` to area `b`, spaced `step` apart, starting and ending clear of both nodes.
func _dots(m: Dictionary, a: String, b: String, step: float) -> Array:
	var pa: Vector2 = m.z.anchor[a]
	var pb: Vector2 = m.z.anchor[b]
	var dir := (pb - pa).normalized()
	var from := pa + dir * (float(NODE_R[m.state[a]]) + 5.0)
	var span := (pb - dir * (float(NODE_R[m.state[b]]) + 5.0) - from).length()
	var out: Array = []
	var n := int(span / step)
	for i in n + 1: out.append(from + dir * (span - n * step) * 0.5 + dir * step * i)
	return out

## An area's node: a glowing jade orb where you may walk, a gold one where you stand, a dark disc with a padlock where
## the way is shut; the chosen one (or, on Resources, each that holds the chosen thing) wears a pale gold ring.
func _node(p: Vector2, state: String, ring: bool) -> void:
	var r: float = NODE_R[state]
	if ring:
		glow(Rect2(p - Vector2.ONE * (r + 20), Vector2.ONE * (r + 20) * 2.0), Color(UiKit.PALE_GOLD, 0.5 * _halo()))
		draw_arc(p, r + RING, 0.0, TAU, 48, Color(UiKit.INK, 0.7), 4.0, true)
		draw_arc(p, r + RING, 0.0, TAU, 48, UiKit.PALE_GOLD, 2.0, true)
	if state == "locked":
		draw_circle(p, r + 3.0, Color(UiKit.MIST, 0.25), true, -1.0, true)
		draw_circle(p, r + 2.0, UiKit.INK, true, -1.0, true)
		draw_circle(p, r, UiKit.SURFACE.stone.darkened(0.35), true, -1.0, true)
		draw_circle(p - Vector2(2, 3), r * 0.55, UiKit.SURFACE.stone.darkened(0.1), true, -1.0, true)
		_lock_icon(p - Vector2(6, 9))
		return
	var tones: Array = [UiKit.BRONZE, UiKit.GOLD, UiKit.PALE_GOLD, UiKit.PAPER] if state == "here" else [UiKit.JADE_SHADOW, UiKit.JADE, UiKit.BRIGHT_JADE, UiKit.PAPER.lerp(UiKit.BRIGHT_JADE, 0.3)]
	glow(Rect2(p - Vector2.ONE * (r + 14), Vector2.ONE * (r + 14) * 2.0), Color(tones[2], 0.45 * _halo()))
	draw_circle(p, r + 4.0, Color(tones[2], 0.55), true, -1.0, true)
	draw_circle(p, r + 2.0, UiKit.INK, true, -1.0, true)
	for i in 4: draw_circle(p + Vector2(-0.2, -0.3) * r * i * 0.45, r * (1.0 - i * 0.22), tones[i], true, -1.0, true)

## The tracked quest's lantern (a paper lantern, red at its rim, lit gold).
func _lantern(c: Vector2, k: float) -> void:
	var s := Vector2(22, 30) * k
	var r := Rect2(c - s * 0.5 + Vector2(0, 2) * k, s - Vector2(0, 4) * k)
	glow(r.grow(12.0 * k), Color(UiKit.GOLD, (0.45 + 0.1 * _pulse()) * _halo()))
	rounded(r.grow(2.0 * k), 9.0 * k, UiKit.INK)
	rounded(r, 8.0 * k, UiKit.BLOOD)
	rounded(r.grow(-3.0 * k), 6.0 * k, UiKit.GOLD)
	draw_circle(r.get_center() - Vector2(0, 2) * k, 4.0 * k, UiKit.PALE_GOLD, true, -1.0, true)
	draw_rect(Rect2(c + Vector2(-5, -s.y * 0.5 / k - 1) * k, Vector2(10, 5) * k), UiKit.INK)

## The faint wind glyph of a path above your arts now open (S43): three drifting strokes and a curl, from `p`.
func _wind(p: Vector2) -> void:
	var col: Color = UiKit.SURFACE.wind
	for i in 3:
		var pts := PackedVector2Array()
		for k in 9: pts.append(Vector2(p.x + k * 3.0 + i * 3.0, p.y - 8.0 + i * 8.0 + sin(k * 0.8 + i) * 2.0))
		draw_polyline(pts, UiKit.INK, 4.0, true)
		draw_polyline(pts, UiKit.PAPER.lerp(col, 0.5), 2.0, true)
	draw_arc(p + Vector2(31, -6), 4.0, PI * 0.5, PI * 2.0, 10, UiKit.PAPER.lerp(col, 0.5), 2.0, true)

## The chosen resource's disc beside an area that holds it: its icon in a gold ring.
func _res_disc(c: Vector2, item: String) -> void:
	glow(Rect2(c - Vector2.ONE * 34.0, Vector2.ONE * 68.0), Color(UiKit.GOLD, 0.4 * _halo()))
	draw_circle(c, 22.0, Color(UiKit.INK, 0.85), true, -1.0, true)
	draw_arc(c, 21.0, 0.0, TAU, 48, UiKit.GOLD, 2.0, true)
	icon_at(Rect2(c - Vector2(16, 16), Vector2(32, 32)), item)

## A short leader from a node's edge to a plate that stands off it.
func _leader(at: Vector2, r: float, rect: Rect2) -> void:
	var to := Vector2(clampf(at.x, rect.position.x, rect.end.x), clampf(at.y, rect.position.y, rect.end.y))
	var from := at + (to - at).normalized() * (r + 3.0)
	draw_line(from, to, Color(UiKit.INK, 0.6), 3.0, true)
	draw_line(from, to, Color(UiKit.PALE_GOLD, 0.7), 1.5, true)

# ------------------------------------------------------------------ plates and the layout pass (decision 17)
## What an area's plate says: its name alone, dim while locked (the band, the field boss and what grows there are on
## the card). A locked area beside none you know has no plate, its padlock alone: "".
func _plate_name(m: Dictionary, rid: String) -> String:
	if m.state[rid] == "locked" and not visited(rid) and not m.z.links.any(func(l): return rid in l and visited(l[0] if l[1] == rid else l[1])): return ""
	return str(_region(rid).name)

## The field bosses in `rooms`: [{name, when: "ready" or the time till it rises, ready}].
func _bosses(rooms: Array) -> Array:
	var out: Array = []
	for id in rooms:
		for sp in ContentDB.room(id).get("spawns", []):
			if not sp.get("field_boss", false): continue
			var left := int(float(Game.account.rooms.get("field_boss_timers", {}).get(str(sp.enemy), 0.0)) - Clock.now_utc())
			out.append({"name": ContentDB.name_of("enemies", str(sp.enemy)), "when": Tx.t("ui.map.boss_ready") if left <= 0 else UiKit.span(left), "ready": left <= 0})
	return out

## An area's level band: "Lv 21–27", or "Safe".
func _band(reg: Dictionary) -> String:
	var lv: Array = reg.get("levels", [0, 0])
	if int(lv[1]) == 0: return Tx.t("ui.map.safe")
	return Tx.t("ui.map.lv_at") % int(lv[0]) if int(lv[0]) == int(lv[1]) else Tx.t("ui.map.lv") % [int(lv[0]), int(lv[1])]

## The size of a plate round a name.
static func _plate_size(name: String) -> Vector2:
	return Vector2(ceilf(UiKit.text_width(name, PLATE_TEXT, true) + 20.0), ceilf(UiKit.size_for(name, PLATE_TEXT, true) * 1.12 + 7.0))

## The marks and plates of this view, placed by the one pass: marks first beside their nodes, then the plates of the
## area you stand in, the chosen one and the rest (open before locked), each in reading order. Kept while nothing that
## decides it changes.
func _place(ch, m: Dictionary) -> Dictionary:
	var z: Dictionary = m.z
	var pins: Array = []
	# A node's pin reaches to its halo (or its ring's outer edge, when it wears one).
	var reach := func(rid: String) -> float: return float(NODE_R[m.state[rid]]) + (RING + 2.0 if m.rings.has(rid) else 4.0)
	for rid in z.order: pins.append(Rect2(z.anchor[rid] - Vector2.ONE * reach.call(rid), Vector2.ONE * reach.call(rid) * 2.0))
	var keep: Array = [_plate_rect().grow(4), Rect2(BANNER.position - Vector2(10, 0), BANNER.size + Vector2(20, 4)), CARD.grow(8),
		Rect2(frame_rect.end.x - 72, frame_rect.position.y + 16, 52, 52)]
	for r in tab_rects(): keep.append(Rect2(r.position.x, 0, r.size.x, r.end.y + 4))
	var marks: Array = []
	var plates: Array = []
	var known_paths := _paths_open(ch)
	for rid in z.order:
		var p: Vector2 = z.anchor[rid]
		var r: float = reach.call(rid)
		var kinds: Array = []
		if view == "resources":
			if m.rings.has(rid): kinds.append("res")
		elif view == "places":
			if m.rings.has(rid): kinds.append("place")
		else:
			if m.lanterns.has(rid): kinds.append("lantern")
			if m.events.has(rid): kinds.append("blossom")
			if visited(rid) and known_paths.keys().any(func(id): return z.node_of[id] == rid): kinds.append("wind")
		for k in kinds: marks.append({"id": "%s:%s" % [k, rid], "kind": k, "at": p, "r": r, "sizes": [MARK_SIZE[k]], "ways": MARK_WAYS[k],
			"live": k == "blossom" and m.events[rid].any(func(o): return o.live)})
		var name := _plate_name(m, rid)
		if name == "": continue
		var rank := 0 if m.state[rid] == "here" else (1 if rid == sel else (2 if m.state[rid] == "open" else 3))
		plates.append({"id": rid, "at": p, "r": r, "sizes": [_plate_size(name)], "ways": PLATE_WAYS, "name": name, "rank": rank})
	plates.sort_custom(func(a, b): return a.rank < b.rank if a.rank != b.rank else (a.at.y < b.at.y if a.at.y != b.at.y else a.at.x < b.at.x))
	var bounds := Rect2(EDGE + 3.0, EDGE + 3.0, CARD.position.x - 8.0 - EDGE - 3.0, FOOT - 3.0 - EDGE - 3.0)
	var key := str([zone_id, view, sel, res_item, place_kind, UiKit.text_scale(), m.state, m.rings.keys(), marks.map(func(x): return x.id), plates.map(func(x): return [x.id, x.name])])
	if key != _layout_key:
		_layout_key = key
		var got := place(marks, pins + keep, bounds)
		var mark_rects: Array = got.values().map(func(g): return g.rect)
		var got_plates := place(plates, pins + keep + mark_rects, bounds)
		layout = {"plates": {}, "marks": {}, "pins": pins, "keep": keep, "bounds": bounds, "hidden": []}
		for it in marks:
			if got.has(it.id): layout.marks[it.id] = {"rect": got[it.id].rect, "kind": it.kind, "live": it.live}
		for it in plates:
			if not got_plates.has(it.id):
				layout.hidden.append(it.id)
				continue
			var g: Dictionary = got_plates[it.id]
			layout.plates[it.id] = {"rect": g.rect, "far": g.far, "way": g.way, "name": it.name}
	return layout

## The one layout pass (decision 17). Each item takes the first place round its pin (its `ways`, each slid along its side
## a step at a time, at the pin and then one and two LEADER steps out) that lies inside `bounds` and keeps TOUCH clear of
## every rect in `blocked` and every item placed before it; one that finds none tries its smaller sizes, if it has
## any. Items that found no room, or only a smaller size, go first on another pass (four at most), and the
## pass that left out and cut the least is kept; one that still fits nowhere is left out (its node answers a tap and the
## card names it). So nothing placed ever touches.
## items: [{id, at, r, sizes: [Vector2], ways: [String]}] -> {id: {rect, size, far, way}}.
static func place(items: Array, blocked: Array, bounds: Rect2) -> Dictionary:
	var order := items.duplicate()
	var best := {}
	var best_cost := INF
	for attempt in 4:
		var taken := blocked.duplicate()
		var out := {}
		var missed: Array = []
		for it in order:
			var got := _first_spot(it, taken, bounds)
			if got.is_empty() or int(got.size) > 0: missed.append(it.id)
			if got.is_empty(): continue
			out[it.id] = got
			taken.append(got.rect)
		var cost := 0.0
		for it in items: cost += float(out[it.id].size) if out.has(it.id) else 1000.0
		if cost < best_cost:
			best = out
			best_cost = cost
		if missed.is_empty(): break
		order = order.filter(func(it): return it.id in missed) + order.filter(func(it): return not it.id in missed)
	return best

static func _first_spot(it: Dictionary, taken: Array, bounds: Rect2) -> Dictionary:
	for si in it.sizes.size():
		for far in 3:
			for k in SLIDES:
				for w in it.ways:
					if k != 0 and str(w).length() == 2: continue
					var rr := spot(it.at, float(it.r), it.sizes[si], str(w), far, k * SLIDE)
					if rr.has_area() and bounds.encloses(rr) and _clear(rr, taken): return {"rect": rr, "size": si, "far": far, "way": str(w)}
	return {}

## True when `r` keeps TOUCH clear of every rect in `taken`.
static func _clear(r: Rect2, taken: Array) -> bool:
	var g := r.grow(TOUCH)
	for o in taken:
		if g.intersects(o): return false
	return true

## Where a box of `size` stands `way` of a pin of radius `r` at `at`, `far` LEADER steps out and slid `slide` px along
## its side; an empty rect past the slide's limit.
static func spot(at: Vector2, r: float, size: Vector2, way: String, far: int, slide := 0.0) -> Rect2:
	var d := r + TOUCH + 1.0 + far * LEADER
	if absf(slide) > ((size.y if way in ["r", "l"] else size.x) + r) * 0.5 - 4.0: return Rect2()
	var p := Vector2.ZERO
	match way:
		"b": p = Vector2(at.x - size.x * 0.5 + slide, at.y + d)
		"t": p = Vector2(at.x - size.x * 0.5 + slide, at.y - d - size.y)
		"r": p = Vector2(at.x + d, at.y - size.y * 0.5 + slide)
		"l": p = Vector2(at.x - d - size.x, at.y - size.y * 0.5 + slide)
		"dr": p = at + Vector2(d, d) * 0.72
		"dl": p = at + Vector2(-d, d) * 0.72 - Vector2(size.x, 0)
		"ur": p = at + Vector2(d, -d) * 0.72 - Vector2(0, size.y)
		"ul": p = at + Vector2(-d, -d) * 0.72 - size
	return Rect2(p.round(), size)

## A name plate: ink laid over the painting in a fine gold edge, the name centred on it (dim while the area is locked).
func _plate(r: Rect2, name: String, dim: bool) -> void:
	rounded(r.grow(1), 7.0, Color(UiKit.GOLD, 0.35))
	rounded(r, 6.0, Color(UiKit.INK, 0.9))
	# The words are measured on the plate over the painting's brightest (its snow and foam).
	ground(r, UiKit.INK.lerp(Color.WHITE, 0.1))
	var base := r.get_center().y + 0.5 + float(UiKit.size_for(name, PLATE_TEXT, true)) * 0.36
	text(Vector2(r.position.x, base), name, PLATE_TEXT, UiKit.HOLLOW if dim else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, true)

## The rooms of the zone with a path above your arts now open that you have not stood on (S43): {room: [the arts]}.
func _paths_open(ch) -> Dictionary:
	var out := {}
	var z := _zone(zone_id)
	for e in ContentDB.all("paths_above"):
		if z.node_of.has(str(e.room)) and not Game.account.paths_above.has(str(e.id)) and _art_known(ch, str(e.art)):
			out[str(e.room)] = out.get(str(e.room), []) + [str(e.art_name)]
	return out

func _art_known(ch, art: String) -> bool:
	return Game.combat.knows_art(ch, art) or Unlocks.is_unlocked(ch.id, art)

# ------------------------------------------------------------------ the card
## The card of lacquer at the right (and the ranking's board): a dark face in a bronze edge with a fine double line.
func _card_face(r: Rect2) -> void:
	draw_rect(Rect2(r.position + Vector2(0, 6), r.size), Color(UiKit.INK, 0.45))
	draw_rect(r.grow(3), UiKit.INK)
	draw_rect(r.grow(2), UiKit.BRONZE)
	_vgrad(r, _lacquer(), UiKit.SURFACE.soil.darkened(0.55))
	draw_rect(r.grow(-1), Color(UiKit.PALE_GOLD, 0.22), false, 1.0)
	draw_rect(r.grow(-7), Color(UiKit.BRONZE, 0.6), false, 1.0)
	ground(r, _lacquer())

func _lacquer() -> Color:
	return UiKit.SURFACE.soil.darkened(0.35)

## The area's own picture in a bronze frame, what can be gathered there in discs on its corner.
func _pic(r: Rect2, rid: String, badges: Array) -> void:
	draw_rect(r.grow(7), Color(UiKit.BRONZE, 0.6))
	draw_rect(r.grow(6), UiKit.SURFACE.soil.darkened(0.2))
	draw_rect(r.grow(3), UiKit.INK)
	draw_rect(r.grow(2), UiKit.SURFACE.gourd)
	var art := SpriteCache.tex("res://art/ui/maps/%s_%s.png" % [PAINTED[zone_id], rid]) if PAINTED.has(zone_id) else null
	if art != null: draw_texture_rect(art, r, false)
	else:
		_sky(r)
		_isle(r.get_center() + Vector2(0, -26), 1.6, rid)
	for i in 5: draw_rect(r.grow(-i * 3.0 - 1.5), Color(UiKit.INK, 0.14 - i * 0.025), false, 3.0)
	var x := r.end.x - 26.0
	for item in badges.slice(0, 4):
		var c := Vector2(x, r.end.y)
		draw_circle(c, 22.0, UiKit.INK, true, -1.0, true)
		draw_circle(c, 21.0, UiKit.SURFACE.gourd, true, -1.0, true)
		draw_circle(c, 19.0, Color(UiKit.INK, 0.92), true, -1.0, true)
		icon_at(Rect2(c - Vector2(16, 16), Vector2(32, 32)), str(item))
		x -= 46.0

## A chip on the card: words on a pill of jade (of gold, for the level band); returns its width.
func _chip(p: Vector2, s: String, gold: bool) -> float:
	var w := UiKit.text_width(s, 14, true) + 20.0
	var r := Rect2(p, Vector2(w, 24))
	var fill := _lacquer().lerp(UiKit.GOLD if gold else UiKit.JADE, 0.16)
	rounded(r, 12.0, Color(UiKit.GOLD if gold else UiKit.BRIGHT_JADE, 0.6))
	rounded(r.grow(-1), 11.0, fill)
	ground(r, fill)
	text(p + Vector2(0, 17), s, 14, UiKit.PALE_GOLD if gold else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, w, true)
	return w

## A row or cell on the card: a sunk jade field in a bronze line; the chosen one lit, in a gold line.
func _cell(r: Rect2, on: bool) -> void:
	var fill := _lacquer().lerp(UiKit.JADE, 0.22) if on else _lacquer().lerp(UiKit.DEEP_TEAL, 0.5)
	rounded(r, 6.0, Color(UiKit.GOLD, 0.7) if on else Color(UiKit.BRONZE, 0.45))
	rounded(r.grow(-1), 5.0, fill)
	ground(r, fill)

## A bronze rule fading in at its two ends.
func _divider(x: float, y: float, w: float) -> void:
	for s in [[0.0, 0.12, 0.0, 1.0], [0.12, 0.88, 1.0, 1.0], [0.88, 1.0, 1.0, 0.0]]:
		var a := Color(UiKit.BRONZE, float(s[2]))
		var b := Color(UiKit.BRONZE, float(s[3]))
		var r := Rect2(x + w * float(s[0]), y, w * (float(s[1]) - float(s[0])), 2)
		draw_polygon(PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]), PackedColorArray([a, b, b, a]))

## Track Route at the card's foot: the way there walked by auto-path, and how many areas it crosses.
func _track(r: Rect2, route: Dictionary, why: String) -> void:
	var b := Rect2(r.position.x + 14, r.end.y - 60, r.size.x - 28, 48)
	var ok := not route.is_empty()
	btn(b, "", "track", str(route.get("room", "")), true, ok, why)
	var a := Tx.t("ui.map.track_route")
	var n := maxi(1, route.path.filter(func(x): return x != "").size() - 1) if ok else 0
	var tail := (Tx.plural("ui.map.areas_n", n) % n) if ok else ""
	var wa := UiKit.text_width(a, 22)
	var wt := UiKit.text_width(tail, 16) + 10.0 if ok else 0.0
	var x0 := roundf(b.get_center().x - (wa + wt) * 0.5)
	inked(Vector2(x0, b.position.y + 32), a, 22, UiKit.PALE_GOLD if ok else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, -1.0, false)
	if ok: inked(Vector2(x0 + wa + 10.0, b.position.y + 31), tail, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, -1.0, false)

## Why Track Route is shut: you are there, or no way open to you leads there.
func _why(m: Dictionary, rid: String) -> String:
	return Tx.t("sim.world.auto_path_here") if rid == m.here and rid != "" else Tx.t("sim.world.auto_path_none")

## Areas: the chosen area's picture and what grows there, its name and band against your Level, what it asks of you
## (Act II's attunement), the tracked quest that leads there with Walk there, its world events, its rooms (you, the
## quest's room, seen, unknown) with their hazards, paths above and field bosses, and Track Route.
func _card_area(ch, m: Dictionary, r: Rect2) -> void:
	var reg := _region(sel)
	if reg.is_empty(): return
	var st := str(m.state[sel])
	var named := st != "locked" or _plate_name(m, sel) != ""
	var grows: Array = []
	for k in KINDS:
		for item in _res()[k]:
			if _res()[k][item].at.has(sel) and not item in grows: grows.append(item)
	_pic(Rect2(r.position + PIC.position, PIC.size), sel, grows if visited(sel) else [])
	var x := r.position.x + 20.0
	var w := r.size.x - 40.0
	text(Vector2(x, r.position.y + 194), str(reg.name) if named else Tx.t("ui.map.unexplored"), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w, true)
	var cx := x + _chip(Vector2(x, r.position.y + 206), Tx.t("ui.map.kind_band") % [Tx.t("ui.map.kind_" + _kind(sel)), _band(reg)], true) + 8.0
	if st == "here": _chip(Vector2(cx, r.position.y + 206), Tx.t("ui.map.you_are_here"), false)
	elif st == "locked": _chip(Vector2(cx, r.position.y + 206), Tx.t("ui.map.locked"), false)
	elif int(reg.get("levels", [0, 0])[1]) > 0: _chip(Vector2(cx, r.position.y + 206), Tx.t("ui.map.you_are_lv") % ProgressionRules.level(ch), false)
	_divider(x, r.position.y + 240, w)
	var y := r.position.y + 248
	var att = ContentDB.zone(zone_id).get("attunement")
	if att is Dictionary and reg.has("attunement"):
		var here_zone := str(ContentDB.zone_of_room(str(ch.position.get("room", ""))).get("id", "")) == zone_id
		var have: float = Game.progression.attunement_value(ch, zone_id) if here_zone else float(ch.cultivator.attunement.get(zone_id, 0.0))
		text(Vector2(x, y + 16), Tx.t("ui.map.attunement_need") % [str(att.get("name", "")), int(reg.attunement), int(have)], 16,
			UiKit.BRIGHT_JADE if have >= float(reg.attunement) else UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_LEFT, w)
		y += 26
	if reg.get("planned", false):
		para(Rect2(x, y + 4, w, 80), Tx.t("ui.map.way_not_open"), 16, UiKit.MIST)
		return
	for q in m.quests:
		if str(m.z.node_of.get(str(q.target_room), "")) != sel: continue
		_lantern(Vector2(x + 5, y + 24), 0.66)
		var line: Dictionary = q.lines[0] if not q.lines.is_empty() else {}
		var there := str(q.target_room) == str(ch.position.get("room", ""))
		var walk := not there and not _route(ch, sel, str(q.target_room)).is_empty()
		# The button as narrow as its label (and a shut one's lock) allows, so the quest's line has the rest.
		var bw := UiKit.text_width(Tx.t("ui.map.walk_there"), 14) + (24.0 if walk else 48.0)
		var room := r.end.x - 10.0 - bw - 6.0 - (x + 16.0)
		text(Vector2(x + 16, y + 20), str(q.name), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, room, true)
		text(Vector2(x + 16, y + 40), str(line.get("text", "")), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, room)
		btn(Rect2(r.end.x - 10 - bw, y, bw, 48), Tx.t("ui.map.walk_there"), "walk", str(q.target_room), false, walk,
			Tx.t("sim.world.auto_path_here") if there else Tx.t("sim.world.auto_path_none"), 14)
		y += 56
		break
	for o in m.events.get(sel, []):
		var ev := CalendarRules.event(str(o.id))
		_blossom(Vector2(x + 11, y + 16), o.live, 1.0)
		text(Vector2(x + 30, y + 16), str(ev.get("name", o.id)), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, w - 30)
		text(Vector2(x + 30, y + 35), (Tx.t("ui.map.under_way") if o.live else Tx.t("ui.map.begins_in")) % UiKit.span(float(o.end if o.live else o.start) - Clock.now_utc()),
			14, UiKit.BRIGHT_JADE if o.live else UiKit.SOUL_TEXT, HORIZONTAL_ALIGNMENT_LEFT, w - 30)
		y += 46
	# The rooms: a row each, what it holds for you on the same line when it fits, else on its own lines under it.
	var rooms := region_rooms(sel)
	var seen := rooms.filter(func(id): return Game.account.visited_rooms.has(id))
	var here_room := str(ch.position.get("room", ""))
	var goal_room: String = Game.world.guide_target(ch)
	var lbl := Tx.t("ui.map.rooms")
	text(Vector2(x, y + 14), lbl, 14, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true)
	text(Vector2(x + UiKit.text_width(lbl, 14, true) + 6, y + 14), Tx.t("ui.map.rooms_seen") % [seen.size(), rooms.size()], 14, UiKit.MIST)
	y += 22
	var rows: Array = []
	var paths := _paths_open(ch)
	# You and the quest's room first, then the rooms seen, then the unknown.
	rooms = rooms.duplicate()
	rooms.sort_custom(func(a, b):
		var ka := 0 if a == here_room or a == goal_room else (1 if Game.account.visited_rooms.has(a) else 2)
		var kb := 0 if b == here_room or b == goal_room else (1 if Game.account.visited_rooms.has(b) else 2)
		return ka < kb if ka != kb else a < b)
	for id in rooms:
		var known: bool = Game.account.visited_rooms.has(id)
		var room := ContentDB.room(id)
		var mark := "▶" if id == here_room else ("◆" if id == goal_room else ("·" if known else "?"))
		var extra: Array = []
		for hz in HazardRules.summary(ch, room):
			extra.append([Tx.t("ui.map.hazard") % [str(hz.name), Tx.t("ui.cultivation." + str(hz.stat))], UiKit.BRIGHT_JADE if hz.answered else UiKit.PALE_GOLD])
		if known:
			for art in paths.get(id, []): extra.append([Tx.t("ui.map.path_above") % art, UiKit.MIST])
			if Unlocks.is_unlocked(ch.id, "field_boss_timers"):
				for b in _bosses([id]): extra.append([Tx.t("ui.map.boss") % str(b.when), UiKit.RED_TEXT])
		var name := str(room.get("name", id)) if known or id == goal_room else Tx.t("ui.map.unknown")
		var col := UiKit.PALE_GOLD if id == here_room or id == goal_room else (UiKit.PAPER if known else UiKit.HOLLOW)
		var mcol := UiKit.GOLD if id == here_room or id == goal_room else (UiKit.MIST if known else UiKit.HOLLOW)
		var used := 22.0 + UiKit.text_width(name, 16) + 8.0
		var tail: Array = []
		for ex in extra:
			var ew := UiKit.text_width(str(ex[0]), 14) + 8.0
			if tail.size() == extra.find(ex) and used + ew <= w: tail.append(ex)
			used += ew
		rows.append({"mark": mark, "mcol": mcol, "name": name, "col": col, "tail": tail})
		for ex in extra.slice(tail.size()): rows.append({"mark": "", "name": "", "tail": [ex]})
	var foot := r.end.y - 64.0
	list("rooms", Rect2(x, y, w + 8.0, maxf(24.0, floorf((foot - y) / 24.0) * 24.0)), rows.size(), 24, func(i: int, rr: Rect2):
		var row: Dictionary = rows[i]
		var tx := rr.position.x
		if str(row.mark) != "":
			text(Vector2(tx, rr.position.y + 16), str(row.mark), 16, row.mcol, HORIZONTAL_ALIGNMENT_CENTER, 18)
			text(Vector2(tx + 22, rr.position.y + 16), str(row.name), 16, row.col, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 22)
			tx += 22.0 + UiKit.text_width(str(row.name), 16) + 8.0
		else:
			tx += 22.0
		for ex in row.tail:
			text(Vector2(tx, rr.position.y + 16), str(ex[0]), 14, ex[1], HORIZONTAL_ALIGNMENT_LEFT, rr.end.x - tx)
			tx += UiKit.text_width(str(ex[0]), 14) + 8.0)
	_track(r, m.route, _why(m, sel))

## A region's kind for its chip, by the type most of its rooms have.
func _kind(rid: String) -> String:
	var n := {}
	for id in region_rooms(rid):
		var k := str(TYPE_KIND.get(str(ContentDB.room(id).get("type", "")), "field"))
		n[k] = int(n.get(k, 0)) + 1
	var best := "field"
	for k in n:
		if int(n[k]) > int(n.get(best, 0)): best = k
	return best

## Resources: where each herb, ore and fish is found. The picture of the nearest area that holds the chosen one, the
## three kinds, the kind's things (those in areas not yet reached greyed), the chosen thing's rank, rooms and regrowth,
## the quest that asks for it, and Track Route to the nearest area that holds it.
func _card_resources(ch, m: Dictionary, r: Rect2) -> void:
	var near := str(m.get("near", ""))
	_pic(Rect2(r.position + PIC.position, PIC.size), near if near != "" else sel, [res_item] if res_item != "" else [])
	var x := r.position.x + 20.0
	var w := r.size.x - 40.0
	var kw := (w - 12.0) / 3.0
	var i := 0
	for k in KINDS:
		var kr := Rect2(roundf(x + i * (kw + 6.0)), r.position.y + 166, roundf(kw), 48)
		_cell(kr, k == res_kind)
		var label := Tx.t(KINDS[k][0])
		var gw := 30.0 + UiKit.text_width(label, 16, true)
		icon_at(Rect2(kr.get_center().x - gw * 0.5, kr.position.y + 12, 24, 24), str(KINDS[k][1]))
		text(Vector2(kr.get_center().x - gw * 0.5 + 30, kr.position.y + 30), label, 16, UiKit.PALE_GOLD if k == res_kind else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true)
		region(kr, "kind", k)
		i += 1
	var items := _res_list(res_kind)
	var y := r.position.y + 222
	if items.is_empty():
		para(Rect2(x, y + 4, w, 60), Tx.t("ui.map.none_here") % Tx.t(KINDS[res_kind][0]).to_lower(), 16, UiKit.MIST)
		return
	var shown := mini(3, ceili(items.size() / 2.0))
	var cw := (w - 6.0) / 2.0
	list("res", Rect2(x, y, w + 8.0, shown * 48.0), ceili(items.size() / 2.0), 48, func(ri: int, rr: Rect2):
		for j in 2:
			if ri * 2 + j >= items.size(): break
			var id: String = items[ri * 2 + j]
			var known := _known(_res()[res_kind][id])
			var cr := Rect2(rr.position.x + j * (cw + 6.0), rr.position.y, cw, rr.size.y)
			_cell(cr, id == res_item)
			icon_at(Rect2(cr.position.x + 6, cr.get_center().y - 16, 32, 32), id, Color.WHITE if known else Color(UiKit.HOLLOW, 0.7))
			text(Vector2(cr.position.x + 42, cr.get_center().y + 5), ContentDB.item_name(id), 14, UiKit.PALE_GOLD if id == res_item else (UiKit.PAPER if known else UiKit.HOLLOW),
				HORIZONTAL_ALIGNMENT_LEFT, cr.size.x - 46, true)
			region(cr, "res", id))
	y += shown * 48.0 + 2.0
	_divider(x, y, w)
	var e: Dictionary = m.get("res", {})
	if not e.is_empty():
		var name := ContentDB.item_name(res_item)
		text(Vector2(x, y + 22), name, 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w, true)
		var rk := str(e.rank)
		var sub := Tx.t("ui.map.gather_rank") % [Tx.t("ui.map.rank_" + rk) if rk != "" else "", Tx.t("craft." + str(KINDS[res_kind][2]))] if rk != "" else Tx.t("craft." + str(KINDS[res_kind][2]))
		text(Vector2(x + UiKit.text_width(name, 18, true) + 8, y + 22), "· " + sub, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w - UiKit.text_width(name, 18, true) - 8)
		var runs: Array = []
		for rid in e.at:
			var most: Array = (e.at[rid] as Array).duplicate()
			most.sort_custom(func(a, b): return int(a[1]) > int(b[1]) if int(a[1]) != int(b[1]) else str(a[0]) < str(b[0]))
			var spots: Array = most.map(func(s): return Tx.t("ui.map.spot") % [ContentDB.name_of("rooms", str(s[0])), int(s[1])])
			runs.append([Tx.t("ui.map.at_area") % str(_region(rid).get("name", rid)), UiKit.BRIGHT_JADE])
			runs.append([", ".join(spots) + ".", UiKit.PAPER])
		if float(e.regrow) > 0.0: runs.append([Tx.t("ui.map.regrows") % UiKit.span(float(e.regrow)), UiKit.PAPER])
		y += 28.0
		y += rich(Rect2(x, y, w, 40), runs, 14) + 4.0
		for q in _asking(ch, res_item).slice(0, 1 if y + 44.0 <= r.end.y - 62.0 else 0):
			var qr := Rect2(x, y, w, 44)
			_cell(qr, false)
			icon_at(Rect2(qr.position.x + 8, qr.get_center().y - 16, 32, 32), "quest")
			text(Vector2(qr.position.x + 48, qr.position.y + 19), str(q.name), 14, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, qr.size.x - 56, true)
			text(Vector2(qr.position.x + 48, qr.position.y + 37), str(q.line), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, qr.size.x - 56)
	_track(r, m.route, _why(m, near))

## The active quests (a daily mission among them) that ask for `item` and are not done: [{name, line}].
func _asking(ch, item: String) -> Array:
	var out: Array = []
	for qid in ch.quests.active:
		var st: Dictionary = ch.quests.active[qid]
		var def: Dictionary = Game.quest.quest_def(ch, str(qid))
		var objs: Array = def.get("objectives", [])
		for i in objs.size():
			var o: Dictionary = objs[i]
			if str(o.get("item", "")) != item or int(st.progress[i]) >= int(o.get("count", 1)): continue
			var nm := str(def.get("name", qid)) + (Tx.t("ui.map.daily") if str(def.get("kind", "")) == "daily" else "")
			out.append({"name": nm, "line": "%s %d / %d" % [str(o.get("text", "")), int(st.progress[i]), int(o.get("count", 1))]})
	return out

## Objectives: the tracked quests and the zone's world events, a row each; the chosen one's area in the picture, lit on
## the map with its way, and Track Route there.
func _card_objectives(ch, m: Dictionary, r: Rect2) -> void:
	var g: Dictionary = m.goal
	_pic(Rect2(r.position + PIC.position, PIC.size), str(g.get("rid", sel)) if str(g.get("rid", "")) != "" else sel, [])
	var x := r.position.x + 20.0
	var w := r.size.x - 40.0
	text(Vector2(x, r.position.y + 190), Tx.t("ui.map.objectives"), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w, true)
	var y := r.position.y + 204
	var objs: Array = m.objectives
	if objs.is_empty():
		para(Rect2(x, y + 8, w, 100), Tx.t("ui.map.no_objectives"), 16, UiKit.MIST)
		return
	list("objectives", Rect2(x, y, w + 8.0, floorf((r.end.y - 68.0 - y) / 56.0) * 56.0), objs.size(), 56, func(i: int, rr: Rect2):
		var o: Dictionary = objs[i]
		_cell(rr, str(o.id) == str(g.get("id", "")))
		if o.event: _blossom(Vector2(rr.position.x + 18, rr.get_center().y), o.live, 1.0)
		else: _lantern(Vector2(rr.position.x + 18, rr.get_center().y), 0.66 if o.main else 0.55)
		var where := str(_region(str(o.rid)).get("name", "")) if str(o.rid) != "" else ContentDB.name_of("rooms", str(o.room))
		text(Vector2(rr.position.x + 38, rr.position.y + 21), str(o.name), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 46, true)
		text(Vector2(rr.position.x + 38, rr.position.y + 41), " · ".join([str(o.line) + ((" " + str(o.count)) if str(o.count) != "" else ""), where].filter(func(s): return s.strip_edges() != "")),
			14, UiKit.BRIGHT_JADE if o.event and o.live else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 46)
		region(rr, "goal", str(o.id)))
	_track(r, m.route, _why(m, str(g.get("rid", ""))))

# ------------------------------------------------------------------ decision 43: the places
## The zone's places of a kind, by area: {rid: [rows]} (data/places.json). A sect's places show once it is the
## character's sect.
func _places_of(ch, kind: String) -> Dictionary:
	var key := "places|%s|%s|%s|%d" % [zone_id, kind, str(ch.training_sect.get("id", "")), ch.quests.flags.size()]
	if _cache.has(key): return _cache[key]
	var z := _zone(zone_id)
	var out := {}
	for r in PlaceRules.all():
		if str(r.kind) != kind: continue
		var rid := str(z.node_of.get(str(r.room), ""))
		var sect := str(r.get("sect", ""))
		if rid == "" or (sect != "" and sect != str(ch.training_sect.get("id", ""))) or not PlaceRules.visible(ch, r): continue
		if not out.has(rid): out[rid] = []
		out[rid].append(r)
	_cache[key] = out
	return out

## The kinds of place this zone holds for the character, in the table's order.
func _place_kinds(ch) -> Array:
	return PlaceRules.kind_order().filter(func(k): return not _places_of(ch, str(k)).is_empty())

## Places: where each of the game's systems lives in the world (docs/redesign/systems_as_places.md). The chosen place's
## area in the picture, the kinds of place (a notice board, a stall, the storehouse, a letter box...) to choose from, the
## chosen place's name and room, what it shows now (its papers, a letter waiting, the beds ripe), how it opens (only
## there, there and from the Menu, or there first and from anywhere later) and Go there: auto-path through the rooms to
## the spot its user stands on.
func _card_places(ch, m: Dictionary, r: Rect2) -> void:
	var pl: Dictionary = m.get("place", {})
	var rid := str(m.z.node_of.get(str(pl.get("room", "")), sel)) if not pl.is_empty() else sel
	_pic(Rect2(r.position + PIC.position, PIC.size), rid, [])
	var x := r.position.x + 20.0
	var w := r.size.x - 40.0
	var kinds := _place_kinds(ch)
	if not place_kind in kinds and not kinds.is_empty(): place_kind = str(kinds[0])
	var cw := (w - 6.0) / 2.0
	var rows := ceili(kinds.size() / 2.0)
	var y := r.position.y + 166
	list("place_kinds", Rect2(x, y, w + 8.0, minf(rows, 5) * 40.0), rows, 40, func(ri: int, rr: Rect2):
		for j in 2:
			if ri * 2 + j >= kinds.size(): break
			var k := str(kinds[ri * 2 + j])
			var cr := Rect2(rr.position.x + j * (cw + 6.0), rr.position.y, cw, rr.size.y - 4.0)
			_cell(cr, k == place_kind)
			icon_at(Rect2(cr.position.x + 6, cr.get_center().y - 12, 24, 24), str(PlaceRules.kinds().get(k, {}).get("icon", "")))
			text(Vector2(cr.position.x + 36, cr.get_center().y + 5), PlaceRules.kind_name(k), 14, UiKit.PALE_GOLD if k == place_kind else UiKit.PAPER,
				HORIZONTAL_ALIGNMENT_LEFT, cr.size.x - 40, true)
			region(cr, "pkind", k))
	y += minf(rows, 5) * 40.0 + 4.0
	_divider(x, y, w)
	if pl.is_empty():
		para(Rect2(x, y + 8, w, 60), Tx.t("ui.map.no_places"), 16, UiKit.MIST)
		return
	var here := str(pl.room) == str(ch.position.get("room", ""))
	text(Vector2(x, y + 24), str(pl.name).substr(0, 1).to_upper() + str(pl.name).substr(1), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w, true)
	var st := PlaceRules.state(ch, pl)
	var runs: Array = [[Tx.t("ui.map.place_rooms") % ContentDB.name_of("rooms", str(pl.room)) + ". ", UiKit.BRIGHT_JADE]]
	var open := str(pl.system) == "shrines" or Unlocks.is_unlocked(ch.id, str(pl.system))
	if not open: runs.append([Tx.t("ui.place.locked") + ". ", UiKit.MIST])
	elif str(st.get("text", "")) != "": runs.append([str(st.text) + (" · " + Tx.t("ui.place.state_new") if int(st.get("new", 0)) > 0 and str(st.state) == "papers" else "") + ". ", UiKit.GOLD if bool(st.get("on", false)) else UiKit.PAPER])
	runs.append([Tx.t("ui.place.rule_" + str(pl.rule)) + ".", UiKit.MIST])
	y += 30.0
	rich(Rect2(x, y, w, 60), runs, 14)
	# Go there: the walk through the rooms (or, standing in its room, across it) to the spot its user stands on.
	var b := Rect2(r.position.x + 14, r.end.y - 60, r.size.x - 28, 48)
	var ok: bool = here or not (m.route as Dictionary).is_empty()
	btn(b, "", "go_place", str(pl.id), true, ok, Tx.t("sim.world.auto_path_none"))
	var a := Tx.t("ui.place.walk") if here else Tx.t("ui.map.go_there")
	var tail := "" if here or not ok else Tx.plural("ui.map.areas_n", maxi(1, m.route.path.filter(func(q): return q != "").size() - 1)) % maxi(1, m.route.path.filter(func(q): return q != "").size() - 1)
	var wa := UiKit.text_width(a, 22)
	var wt := UiKit.text_width(tail, 16) + 10.0 if tail != "" else 0.0
	var x0 := roundf(b.get_center().x - (wa + wt) * 0.5)
	inked(Vector2(x0, b.position.y + 32), a, 22, UiKit.PALE_GOLD if ok else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, -1.0, false)
	if tail != "": inked(Vector2(x0 + wa + 10.0, b.position.y + 31), tail, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, -1.0, false)

# ------------------------------------------------------------------ the foot: the three views and the legend
func _draw_foot() -> void:
	var x := 48.0
	for v in VIEWS:
		var label := Tx.t("ui.map." + v)
		var tr := Rect2(x, 652, 12.0 + 32.0 + 10.0 + UiKit.text_width(label, 18) + 18.0, 52)
		_timber(tr, v == view)
		icon_at(Rect2(tr.position.x + 12, tr.position.y + 10, 32, 32), str(VIEW_ICON[v]))
		text(Vector2(tr.position.x + 54, tr.position.y + 33), label, 18, UiKit.PALE_GOLD if v == view else UiKit.PAPER)
		region(tr, "view", v)
		x = tr.end.x + 8.0
	var keys: Array = LEGEND[view]
	# The legend on one line after the tablets, or on two when the words are large.
	var widths: Array = keys.map(func(k): return float(LEGEND_W.get(k, 16.0)) + 6.0 + UiKit.text_width(Tx.t("ui.map.legend_" + k), 14))
	var room := 1280.0 - EDGE - 12.0 - (x + 20.0)
	var lines := 1 if float(widths.reduce(func(a, b): return a + b, 0.0)) + 16.0 * (keys.size() - 1) <= room else 2
	var per := ceili(keys.size() / float(lines))
	for li in lines:
		var part := keys.slice(li * per, (li + 1) * per)
		var pw: Array = widths.slice(li * per, (li + 1) * per)
		var gap := clampf((room - float(pw.reduce(func(a, b): return a + b, 0.0))) / maxf(1.0, part.size() - 1.0), 8.0, 16.0)
		var lx := x + 20.0
		var ly := 678.0 if lines == 1 else 667.0 + li * 22.0
		for j in part.size():
			var gw := float(LEGEND_W.get(part[j], 16.0))
			_legend_glyph(str(part[j]), Vector2(lx + gw * 0.5, ly))
			text(Vector2(lx + gw + 6.0, ly + 5), Tx.t("ui.map.legend_" + part[j]), 14, UiKit.MIST)
			lx += float(pw[j]) + gap

func _legend_glyph(k: String, c: Vector2) -> void:
	match k:
		"available", "here":
			var col := UiKit.BRIGHT_JADE if k == "available" else UiKit.GOLD
			glow(Rect2(c - Vector2(8, 8), Vector2(16, 16)), Color(col, 0.6 * _halo()))
			draw_circle(c, 6.0, UiKit.INK, true, -1.0, true)
			draw_circle(c, 4.5, col, true, -1.0, true)
		"locked": _lock_icon(c - Vector2(6, 8))
		"route":
			for i in 4: draw_circle(c + Vector2(-12 + i * 8, 0), 1.8, UiKit.PALE_GOLD, true, -1.0, true)
		"tracked": _lantern(c, 0.55)
		"place":
			draw_circle(c, 7.0, Color(UiKit.INK, 0.85), true, -1.0, true)
			draw_arc(c, 7.0, 0.0, TAU, 20, UiKit.GOLD, 1.5, true)
		"event": _blossom(c, true, 0.7)
		"holds":
			draw_arc(c, 6.5, 0.0, TAU, 24, UiKit.INK, 4.0, true)
			draw_arc(c, 6.5, 0.0, TAU, 24, UiKit.PALE_GOLD, 2.0, true)

# ------------------------------------------------------------------ zones not yet painted, drawn from tokens
## A zone with no painting yet, in the painting's manner (seen from above at an angle, lit from the upper left): the
## Expanse's far ranges over a sea of cloud banks that swell toward the viewer, with the sky showing through their gaps;
## the star field's night with the star river across it, stars thick in the river and lanterns adrift below. Each area
## is an isle under its node.
func _paint_tokens(r: Rect2, z: Dictionary) -> void:
	_sky(r)
	if zone_id in STARRY:
		var river := func(f: float) -> Vector2: return Vector2(r.size.x * (1.1 * f - 0.05), r.size.y * (0.92 - 0.78 * f) + 36.0 * sin(f * 5.0))
		for i in 28: glow(Rect2(river.call(i / 27.0) - Vector2(130, 70), Vector2(260, 140)), Color(UiKit.SOUL if i % 2 == 0 else UiKit.QI, 0.08))
		for i in 320:
			var p: Vector2 = river.call(_rnd(i, 1)) + Vector2(_rnd(i, 2) - 0.5, _rnd(i, 3) - 0.5) * 150.0 if i < 140 \
				else Vector2(_rnd(i, 2) * r.size.x, _rnd(i, 3) * r.size.y)
			var s := 2.0 if _rnd(i, 4) > 0.86 else 1.0
			draw_rect(Rect2(p.round(), Vector2(s, s)), Color(UiKit.PALE_GOLD if _rnd(i, 5) > 0.6 else UiKit.PAPER, 0.3 + 0.6 * _rnd(i, 6)))
		for i in 16:
			var p := Vector2(_rnd(i, 7) * r.size.x, _rnd(i, 8) * r.size.y * 0.8).round()
			for d in [Vector2(4, 0), Vector2(0, 4)]: draw_line(p - d, p + d, Color(UiKit.PALE_GOLD, 0.8), 1.0)
		for i in 40:
			var p := Vector2(_rnd(i, 9) * r.size.x, r.size.y * (0.45 + 0.5 * _rnd(i, 10)))
			glow(Rect2(p - Vector2(9, 9), Vector2(18, 18)), Color(UiKit.GOLD, 0.35))
			draw_circle(p, 1.5, UiKit.PALE_GOLD, true, -1.0, true)
	else:
		for layer in 2:
			var base := 176.0 + layer * 34.0
			var pts := PackedVector2Array([Vector2(0, base + 40)])
			for i in 27: pts.append(Vector2(i * 50.0 - 25.0 * layer, base - (8.0 if i % 2 else 44.0 + 46.0 * _rnd(i, 11 + layer)) * (1.0 - 0.35 * layer)))
			pts.append(Vector2(1280, base + 40))
			draw_colored_polygon(pts, [UiKit.MIST.lerp(UiKit.SKY, 0.4).lerp(UiKit.PAPER, 0.35), UiKit.SURFACE.stone.lerp(UiKit.MIST, 0.6)][layer])
		var shade := UiKit.MIST.lerp(UiKit.SKY, 0.4)
		var body := UiKit.PAPER.lerp(UiKit.MIST, 0.25)
		for row in 10:
			var f := row / 9.0
			var y := 200.0 + 430.0 * pow(f, 1.2)
			var rad := 12.0 + 30.0 * f
			var x := -rad * 2.0 * _rnd(row, 12)
			var i := 0
			while x < r.size.x + rad:
				if _rnd(row * 53 + i, 13) < 0.8:
					var s := rad * (0.8 + 0.5 * _rnd(row * 31 + i, 14))
					var c := Vector2(x, y + rad * 0.3 * sin(i * 1.7 + row))
					draw_circle(c + Vector2(0, s * 0.35), s, shade, true, -1.0, true)
					draw_circle(c, s, body, true, -1.0, true)
					draw_circle(c + Vector2(-s, -s) * 0.3, s * 0.55, UiKit.PAPER, true, -1.0, true)
				x += rad * (1.1 + 0.7 * _rnd(row * 17 + i, 15))
				i += 1
	for rid in z.order: _isle(z.anchor[rid], 1.0, rid)

## A steady pseudo-random number in [0, 1) for a painted detail (never the game's Rng streams).
static func _rnd(a: int, b: int) -> float:
	return fposmod(sin(a * 12.9898 + b * 78.233) * 43758.5453, 1.0)

## The zone's sky over `r`: the Expanse's pale blue, or the star field's night.
func _sky(r: Rect2) -> void:
	if zone_id in STARRY: _vgrad(r, UiKit.SURFACE.sky_top, UiKit.SURFACE.sky_bottom.lerp(UiKit.SURFACE.water, 0.35))
	else: _vgrad(r, UiKit.PAPER.lerp(UiKit.SKY, 0.35), UiKit.SKY.lerp(UiKit.DEEP_TEAL, 0.3))

## An area as an isle adrift under its node, at scale `k`: grass on top with trees, the rock tapering beneath with its
## lit face to the left, cloud at its waist (a lantern's glow under the stars), and a hall for a town or a sect.
func _isle(p: Vector2, k: float, rid: String) -> void:
	var night := zone_id in STARRY
	var hsh := absi(rid.hash())
	var w := (44.0 + hsh % 12) * k
	var h := 14.0 * k
	var c := p + Vector2(0, 4) * k
	var stone: Color = UiKit.SURFACE.stone.darkened(0.35) if night else UiKit.SURFACE.stone.lerp(UiKit.MIST, 0.3)
	var rock := PackedVector2Array([c + Vector2(-w, 0), c + Vector2(w, 0), c + Vector2(w * 0.7, h * 1.2), c + Vector2(w * 0.3, h * 2.4),
		c + Vector2(w * 0.05, h * 3.4), c + Vector2(-w * 0.25, h * 2.2), c + Vector2(-w * 0.7, h * 1.1)])
	draw_colored_polygon(rock, stone)
	draw_colored_polygon(PackedVector2Array([rock[0], rock[6], rock[5], rock[4], c + Vector2(-w * 0.1, h * 0.5)]), stone.lightened(0.18))
	var top := PackedVector2Array()
	for i in 28: top.append(c + Vector2(cos(i * TAU / 28.0) * w, sin(i * TAU / 28.0) * h * 0.6))
	var grass := UiKit.JADE_SHADOW.darkened(0.25) if night else UiKit.JADE.lerp(UiKit.GOLD, 0.3)
	draw_colored_polygon(top, grass.darkened(0.2))
	draw_colored_polygon(_shrunk(top, c, 0.88, Vector2(-2, -2) * k), grass)
	for i in 6:
		var tp := c + Vector2((_rnd(hsh % 997, i) - 0.5) * w * 1.5, (_rnd(hsh % 991, i + 9) - 0.5) * h * 0.7)
		draw_circle(tp + Vector2(1, 2) * k, 4.5 * k, Color(UiKit.INK, 0.35), true, -1.0, true)
		draw_circle(tp, 4.2 * k, UiKit.JADE_SHADOW.darkened(0.2) if night else UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.4), true, -1.0, true)
		draw_circle(tp - Vector2(1.2, 1.2) * k, 2.0 * k, UiKit.JADE_SHADOW if night else UiKit.JADE.lerp(UiKit.GOLD, 0.2), true, -1.0, true)
	if _kind(rid) in ["town", "sect"]:
		var hb := c + Vector2(w * 0.35, -h * 0.1)
		draw_rect(Rect2(hb + Vector2(-8, -9) * k, Vector2(16, 9) * k), UiKit.PAPER.lerp(UiKit.BRONZE, 0.3))
		draw_colored_polygon(PackedVector2Array([hb + Vector2(-12, -9) * k, hb + Vector2(12, -9) * k, hb + Vector2(7, -15) * k, hb + Vector2(-7, -15) * k]),
			UiKit.JADE_SHADOW if night else UiKit.SURFACE.lacquer)
	if night:
		for i in 2:
			var lp := c + Vector2((-0.45 + 0.8 * i) * w, h * (0.9 + 0.8 * i))
			glow(Rect2(lp - Vector2.ONE * 16.0 * k, Vector2.ONE * 32.0 * k), Color(UiKit.GOLD, 0.55))
			draw_circle(lp, 2.2 * k, UiKit.PALE_GOLD, true, -1.0, true)
	else:
		for i in 3:
			var cp := c + Vector2((-0.5 + 0.5 * i) * w * 0.9, h * 1.4)
			draw_circle(cp + Vector2(0, 3) * k, 9.0 * k, UiKit.MIST.lerp(UiKit.SKY, 0.4), true, -1.0, true)
			draw_circle(cp, 9.0 * k, UiKit.PAPER.lerp(UiKit.MIST, 0.2), true, -1.0, true)

## `pts` drawn in toward `c` by `k` and moved by `off`.
static func _shrunk(pts: PackedVector2Array, c: Vector2, k: float, off: Vector2) -> PackedVector2Array:
	var out := PackedVector2Array()
	for q in pts: out.append(c + (q - c) * k + off)
	return out

# ------------------------------------------------------------------ taps
func on_action(id: String, data) -> void:
	match id:
		"sel", "place_at":
			# Decision 43: on Places, a tap on an area (or its mark) that holds the chosen kind chooses its place, whose card
			# offers the walk there.
			var ch = c()
			var at: Array = _places_of(ch, place_kind).get(str(data), []) if view == "places" and ch != null else []
			if not at.is_empty():
				if str(at[0].id) != place_id: chosen_at = t
				place_id = str(at[0].id)
				sel = str(data)
				return
			# A tap on an area shows its card, whichever view was open.
			if str(data) != sel or view != "areas": chosen_at = t
			sel = str(data)
			goal = ""
			view = "areas"
		"pkind":
			place_kind = str(data)
			place_id = ""
			chosen_at = t
		"go_place":
			if submit({"type": "auto_path", "target": "", "place": str(data)}).get("ok", false): close()
		"view":
			view = str(data)
			chosen_at = t
		"kind":
			res_kind = str(data)
			res_item = ""
			chosen_at = t
		"res":
			res_item = str(data)
			chosen_at = t
		"goal":
			goal = str(data)
			chosen_at = t
		"walk", "track":
			if submit({"type": "auto_path", "target": str(data)}).get("ok", false): close()
		"challenge":
			if submit({"type": "challenge_rank", "npc": str(data)}).get("ok", false): close()

# ------------------------------------------------------------------ the Heaven Ranking (S49 v1.1)
## The valley's seeded cultivators, strongest first, with you among them once you have entered, on a lacquer board over
## the dimmed painting. The one directly above you can be challenged; beat them and you hold their place for the week.
func _draw_ranking(ch) -> void:
	var r := Rect2(content.position, content.size)
	_card_face(r.grow(16))
	var x := r.position.x + 28
	var cols := [x + 12, x + 64, r.end.x - 470, r.end.x - 340, r.end.x - 196]
	heading(Vector2(x, r.position.y + 40), Tx.t("ui.map.ranking_week") % (Game.calendar.rank_week() + 1), cols[2] - x - 40)
	text(Vector2(cols[2], r.position.y + 40), Tx.t("ui.map.rank_level"), 16, UiKit.MIST)
	text(Vector2(cols[3], r.position.y + 40), Tx.t("ui.map.rank_cp"), 16, UiKit.MIST)
	var now := Clock.now_utc()
	var table: Array = Game.calendar.ranking(ch)
	var prev: Array = CalendarRules.rank_table(now - 604800.0, Game.calendar.cal_seed(), Game.calendar.origin()).map(func(o): return str(o.id))
	var above := Game.calendar.rank_above(ch)
	var y := r.position.y + 62
	var npc_i := 0
	for i in table.size():
		var o: Dictionary = table[i]
		var me: bool = o.get("player", false)
		var rr := Rect2(x, y, r.size.x - 56, 48)
		# P4 (§6): your row is a mark, not a selection: the normal panel, a gold ◆ and your name in pale gold.
		panel(rr, "minor_panel")
		text(Vector2(cols[0], y + 32), "%d" % (i + 1), 22, UiKit.GOLD if i < 3 else UiKit.PAPER)
		var nx: float = cols[1] + (22.0 if me else 0.0)
		if me: text(Vector2(cols[1], y + 22), "◆", 18, UiKit.GOLD)
		text(Vector2(nx, y + 22), fit(str(o.name), 20, cols[2] - nx - 20), 20, UiKit.PALE_GOLD if me else UiKit.PAPER)
		if str(o.get("title", "")) != "": text(Vector2(cols[1], y + 40), fit(str(o.title), 14, cols[2] - cols[1] - 20), 14, UiKit.MIST)
		text(Vector2(cols[2], y + 31), "%d" % int(o.level), 18, UiKit.PAPER)
		text(Vector2(cols[3], y + 31), UiKit.fmt(int(o.cp)), 18, UiKit.PAPER)
		if not me:
			var was := prev.find(str(o.id))
			if was >= 0 and was != npc_i: text(Vector2(cols[3] + 86, y + 31), "▲" if was > npc_i else "▼", 16, UiKit.BRIGHT_JADE if was > npc_i else UiKit.RED_TEXT)
			npc_i += 1
		if not above.is_empty() and str(above.id) == str(o.id):
			btn(Rect2(cols[4], y + 6, rr.end.x - cols[4] - 8, 36), Tx.t("ui.map.rank_challenge"), "challenge", str(o.id), true, true, "", 18)
		y += 52
	if not table.any(func(o): return o.get("player", false)):
		var low := int(table.back().cp) if not table.is_empty() else 0
		para(Rect2(x, y + 2, r.size.x - 56, 50), Tx.t("ui.map.rank_enter") % [UiKit.fmt(low), UiKit.fmt(StatRules.combat_power(ch))], 18, UiKit.MIST, 2)
