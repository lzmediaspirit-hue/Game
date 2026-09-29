extends Page
## Quest log (S19): every quest under way or on offer, today's missions and the day's round, and the quests done. Track
## up to three; abandon side quests and missions; Go walks to where the chosen quest leads (auto_path).
## P5 (docs/page_identity.md row 6, mockup 12 v2): the sect's mission board, paper slips pinned to dark timber. The
## story's slip at the top left under a red head (the tracker's Next entry between chapters, with what the story waits
## on); the side quests near you; today's missions as a row of small slips; the day's chests on a red cord; the other
## side quests stacked under their nameboards (the companions', each zone's), a tap spreading a stack across the board.
## The chosen slip is taken down and held large at the right with its route, its steps, its rewards, Go and Track.
## Done is the second tab: the finished slips, stamped. The page reads only and sends intents.

const BOARD := Rect2(64, 32, 1152, 656)
const READ := Rect2(836, 110, 354, 556)      # the slip being read
const SLIP := Vector2(170, 66)               # a small slip on the board
const PITCH := 180.0                         # small slips side by side
const COLS := 4                              # small slips in a row
const SPREAD_ROWS := 4                       # rows of a spread stack
const DONE_ROWS := 6                         # rows of finished slips a sheet
const MAIN_KINDS := ["main", "prologue", "guided"]

var sel := ""            # the quest id being read ("next" for the story's Next entry)
var spread := ""         # the group spread across the board ("" for the board as pinned)
var sheet := 0           # which sheet of a spread stack, or of the finished slips
var lifted_at := -1.0    # when the chosen slip was taken down
var _board := {}         # the grouping, kept while the quests stay the same

func _init() -> void:
	title = Tx.t("ui.quest.quests")
	tabs = [{"id": "current", "label": Tx.t("ui.quest.tab_current")}, {"id": "done", "label": Tx.t("ui.quest.done")}]
	identity = Identity.new("wood_dark", false, "own", "board_pinned_slips_reading_slip", 0.25)

func content_rect() -> Rect2:
	return Rect2(88, 104, 1112, 568)

func draw_surface(r: Rect2) -> void:
	RecordsKit.timber(self, r, UiKit.SURFACE.wood_dark)

func title_rect() -> Rect2:
	return Rect2(520, 24, 240, 58)

## The title is carved on a header plank nailed to the board's top rail.
func draw_title_mount(r: Rect2) -> void:
	rounded(r.grow(2), 5.0, UiKit.INK)
	vshade(r, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.3), UiKit.SURFACE.wood.lerp(UiKit.INK, 0.2))
	draw_rect(r.grow(-2), UiKit.BRONZE, false, 2.0)
	for x in [r.position.x + 14, r.end.x - 14]: RecordsKit.pin(self, Vector2(x, r.position.y + 14), true)

func tab_rects() -> Array:
	return [Rect2(96, 46, 130, 48), Rect2(234, 46, 150, 48)]

## The tabs are paper index slips pinned at the board's top left; the open one bright, the other faded into the wood.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	var open := state == "selected"
	if open:
		RecordsKit.slip(self, r)
		RecordsKit.pin(self, r.position + Vector2(r.size.x * 0.5, 6))
	else:
		var faded := UiKit.SURFACE.wood_dark.lerp(UiKit.SURFACE.scroll, 0.55)
		rounded(Rect2(r.position + Vector2(0, 4), r.size - Vector2(0, 4)), 2.0, faded)
		ground(r, faded)
	var words := str(tabs[i].label)
	var count := ""
	if str(tabs[i].id) == "done" and c() != null: count = UiKit.fmt(_done_ids(c()).size())
	var w := UiKit.text_width(words, 20) + (UiKit.text_width(count, 16) + 8.0 if count != "" else 0.0)
	var x := r.get_center().x - w * 0.5
	text(Vector2(x, r.position.y + 33), words, 20, RecordsKit.INK)
	if count != "": text(Vector2(x + w - UiKit.text_width(count, 16), r.position.y + 33), count, 16, RecordsKit.INK)

# ------------------------------------------------------------------ what is on the board
## The quests of a group: the story's (under way or on offer), the side quests by where their giver stands, today's
## missions. {story: [ids], near: [ids], near_zone, missions: [ids], groups: [{id, label, ids, regions}]}.
func board(ch) -> Dictionary:
	var key := "%d|%d|%d|%d|%s|%d" % [ch.quests.active.size(), ch.quests.offered.size(), ch.quests.done.size(), ch.quests.daily.size(),
		str(ch.position.get("room", "")), ch.quests.tracked.size()]
	if str(_board.get("key", "")) == key: return _board
	var here_zone := str(ContentDB.room(str(ch.position.get("room", ""))).get("zone", ""))
	var story: Array = []
	var missions: Array = []
	var side: Array = []
	for q in ch.quests.active:
		var k := str(Game.quest.quest_def(ch, q).get("kind", "side"))
		if k in MAIN_KINDS: story.append(str(q))
		elif k in ["daily", "mortal"]: missions.append(str(q))
		else: side.append(str(q))
	for q in ch.quests.daily:
		if not missions.has(str(q)) and not ch.quests.is_done(str(q)): missions.append(str(q))
	for q in ch.quests.offered:
		var d := ContentDB.entry("quests", q)
		if ch.quests.is_active(q) or d.is_empty() or not Game.quest.can_offer(ch, d): continue
		(story if str(d.get("kind", "side")) in MAIN_KINDS else side).append(str(q))
	# The tracked story quest leads, then any under way, then those on offer.
	story.sort_custom(func(a, b): return _story_rank(ch, a) < _story_rank(ch, b))
	var companions := {}
	for e in ContentDB.all("companions"):
		companions[str(e.id)] = true
		companions[str(e.get("outfit_npc", e.id))] = true
	var near: Array = []
	var by: Dictionary = {}    # group id -> {id, label, ids, regions}
	for q in side:
		var d := Game.quest.quest_def(ch, q)
		var giver := QuestAuthority.own_npc(ch, d.get("giver_any", d.get("giver", "")))
		var room := _home(ch, d, giver)
		var zone := str(ContentDB.room(room).get("zone", ""))
		if zone == here_zone and zone != "" and not companions.has(giver):
			near.append(q)
			continue
		var gid := "companions" if companions.has(giver) else ("zone:" + zone if zone != "" else "elsewhere")
		if not by.has(gid):
			by[gid] = {"id": gid, "ids": [], "regions": {},
				"label": Tx.t("ui.quest.companions") if gid == "companions" else (str(ContentDB.entry("zones", zone).get("name", zone)) if zone != "" else Tx.t("ui.quest.elsewhere"))}
		by[gid].ids.append(q)
		var rg := _region_name(room)
		if rg != "": by[gid].regions[rg] = int(by[gid].regions.get(rg, 0)) + 1
	var groups: Array = by.values()
	groups.sort_custom(func(a, b): return [0 if a.id == "companions" else 1, -a.ids.size()] < [0 if b.id == "companions" else 1, -b.ids.size()])
	_board = {"key": key, "story": story, "near": near, "near_zone": str(ContentDB.entry("zones", here_zone).get("name", here_zone)), "missions": missions, "groups": groups}
	return _board

func _story_rank(ch, q: String) -> int:
	return (0 if ch.quests.tracked.has(q) else 1) + (0 if ch.quests.is_active(q) else 2)

## Where a quest's giver stands (the nearest of their rooms), else where it leads.
func _home(ch, d: Dictionary, giver: String) -> String:
	var rooms: Array = Game.quest.npc_rooms(ch, giver) if giver != "" else []
	return str(rooms[0]) if not rooms.is_empty() else str(d.get("target_room", ""))

func _region_name(room: String) -> String:
	var rd := ContentDB.room(room)
	for rg in ContentDB.entry("zones", str(rd.get("zone", ""))).get("regions", []):
		if str(rg.get("id", "")) == str(rd.get("region", "")): return str(rg.get("name", ""))
	return ""

## The story's Next entry of the tracker between chapters (QuestAuthority.story_next), {} while a story quest is on.
func _next(ch) -> Dictionary:
	return Game.quest.story_next(ch)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var b := board(ch)
	if sel == "" or (sel != "next" and not ch.quests.is_active(sel) and not ch.quests.offered.has(sel) and not ch.quests.is_done(sel)) \
		or (sel == "next" and _next(ch).is_empty()):
		sel = _first(ch, b)
	# The slips are pinned as the page opens: they settle onto the board from a little above.
	move(Vector2(0, -roundf((1.0 - unfold()) * 16.0)))
	if str(tabs[tab].id) == "done": _done(ch)
	else:
		_story(ch, b)
		if spread != "": _spread(ch, b)
		else:
			_near(ch, b)
			_missions(ch, b)
			_round(ch)
			_stacks(ch, b)
	move()
	_reading(ch)

func _first(ch, b: Dictionary) -> String:
	if str(tabs[tab].id) == "done":
		var done := _done_ids(ch)
		return str(done[0]) if not done.is_empty() else ""
	if not b.story.is_empty() and ch.quests.is_active(str(b.story[0])): return str(b.story[0])
	if not _next(ch).is_empty(): return "next"
	for g in [b.story, b.near, b.missions]:
		if not g.is_empty(): return str(g[0])
	for g in b.groups:
		if not g.ids.is_empty(): return str(g.ids[0])
	return ""

## A small slip on the board: its name and one line under it (the giver, a mission's count), a mark before the name
## (! on offer, ? to hand in, ◆ tracked), and a stack of `more` slips under it that spreads its group.
func _small(ch, r: Rect2, q: String, stack := 0, group := "", stamped := false) -> void:
	var tilt := float(int(r.position.x + r.position.y) % 5 - 2)
	for k in mini(stack, 2):
		rounded(Rect2(r.position + Vector2(8 + k * 6, 4 + k * 3 + tilt), r.size), 2.0, RecordsKit.PAPER_LIT.lerp(UiKit.SURFACE.wood_dark, 0.25 + 0.1 * k))
	RecordsKit.slip(self, r, q == sel)
	RecordsKit.pin(self, Vector2(r.get_center().x, r.position.y + 7))
	var d := Game.quest.quest_def(ch, q)
	var mark := _mark(ch, q)
	var x := r.position.x + 10
	if mark != "":
		text(Vector2(x, r.position.y + 32), mark, 16, RecordsKit.RED_INK if mark != "◆" else RecordsKit.JADE_INK)
		x += UiKit.text_width(mark, 16) + 6
	var nm := str(d.get("name", q))
	var room := 40.0 if stamped else 0.0   # a finished slip's stamp sits at its right
	text(Vector2(x, r.position.y + 32), nm, 16 if UiKit.text_width(nm, 16) <= r.end.x - 8 - x - room else 14, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, r.end.x - 8 - x - room)
	var sub := _sub(ch, q, d)
	if stack > 0: sub = Tx.t("ui.quest.and_more") % stack if sub == "" else sub + " · " + Tx.t("ui.quest.and_more") % stack
	text(Vector2(r.position.x + 10, r.position.y + 54), sub, 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 20 - room)
	if stamped: RecordsKit.stamp(self, r.end - Vector2(24, 26), "", 14.0)
	if stack > 0: region(r, "spread", group)
	else: region(r, "sel", q)

func _mark(ch, q: String) -> String:
	if ch.quests.is_done(q): return ""
	if not ch.quests.is_active(q): return "!"
	if str(ch.quests.active[q].get("state", "")) == "ready": return "?"
	return "◆" if ch.quests.tracked.has(q) else ""

## The line under a slip's name: a mission's count, a side quest's giver, who to return to.
func _sub(ch, q: String, d: Dictionary) -> String:
	var st: Dictionary = ch.quests.active.get(q, {})
	var objs: Array = d.get("objectives", [])
	if str(d.get("kind", "")) in ["daily", "mortal"] and not objs.is_empty():
		var have := int(st.get("progress", [0])[0]) if not st.is_empty() else 0
		return "%s %s" % [str(objs[0].get("kind", "")).replace("_node", "").replace("_", " "), "%d / %d" % [mini(have, int(objs[0].get("count", 1))), int(objs[0].get("count", 1))]]
	if not st.is_empty() and str(st.get("state", "")) == "ready": return Tx.t("sim.quest.return_to") % ContentDB.name_of("npcs", Game.quest.hand_in_npc(ch, d))
	return ContentDB.name_of("npcs", QuestAuthority.own_npc(ch, d.get("giver_any", d.get("giver", ""))))

## The story's slip at the top left: the tracked story quest (its chapter, the step and where it leads), else the
## tracker's Next entry, else the story quest on offer.
func _story(ch, b: Dictionary) -> void:
	var r := Rect2(96, 116, 318, 100)
	tour_mark("story", r)   # decision 43: a tour's anchor
	var q := ""
	if not b.story.is_empty() and ch.quests.is_active(str(b.story[0])): q = str(b.story[0])
	var nx := _next(ch) if q == "" else {}
	if q == "" and nx.is_empty() and not b.story.is_empty(): q = str(b.story[0])
	if q == "" and nx.is_empty():
		RecordsKit.slip(self, r)
		text(r.position + Vector2(12, 56), Tx.t("ui.quest.story_rests"), 16, RecordsKit.FADED, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24)
		return
	var id := q if q != "" else "next"
	RecordsKit.slip(self, r, sel == id)
	var d := Game.quest.quest_def(ch, q) if q != "" else ContentDB.entry("quests", str(nx.quest))
	if q == "" and nx.get("gate", false): d = {"name": str(nx.name)}   # decision 41: the prototype's tale rests here
	RecordsKit.head(self, Rect2(r.position + Vector2(0, 4), Vector2(r.size.x, 26)), UiKit.BLOOD, _head(ch, q, d, true) if q != "" else Tx.t("ui.quest.head_next"))
	RecordsKit.pin(self, Vector2(r.end.x - 18, r.position.y + 10), true)
	var nm := str(d.get("name", q))
	text(r.position + Vector2(12, 62), nm, 22, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24, true)
	var line := ""
	if q == "": line = str(nx.lines[0].text) if not (nx.get("lines", []) as Array).is_empty() else ""
	elif ch.quests.is_active(q): line = _step_line(ch, q, d)
	else: line = Tx.t("ui.quest.ask") % ContentDB.name_of("npcs", QuestAuthority.own_npc(ch, d.get("giver_any", d.get("giver", ""))))
	text(r.position + Vector2(12, 88), line, 14, RecordsKit.JADE_INK, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24)
	region(r, "sel", id)

## "◆ tracked · step 1 of 2 · to the Arrival Quay", or who to return to.
func _step_line(ch, q: String, d: Dictionary) -> String:
	var st: Dictionary = ch.quests.active.get(q, {})
	if str(st.get("state", "")) == "ready": return Tx.t("sim.quest.return_to") % ContentDB.name_of("npcs", Game.quest.hand_in_npc(ch, d))
	var n: int = (d.get("objectives", []) as Array).size()
	var at := Game.quest.step_now(ch, d, st) + 1
	var to := str(ContentDB.room(Game.quest.quest_target(ch, d, st)).get("name", ""))
	var s := Tx.t("ui.quest.step") % [clampi(at, 1, maxi(1, n)), maxi(1, n)]
	if to != "": s += " · " + Tx.t("ui.quest.to") % to
	return ("◆ " + Tx.t("ui.quest.tracked") + " · " if ch.quests.tracked.has(q) else "") + s

## What a slip's head says: the story's chapter, a lesson, a side quest's zone, a mission, a finished quest.
func _head(ch, q: String, d: Dictionary, board_slip := false) -> String:
	if ch.quests.is_done(q) and str(tabs[tab].id) == "done": return Tx.t("ui.quest.head_done")
	var k := str(d.get("kind", "side"))
	var s := ""
	match k:
		"main": s = Tx.t("ui.quest.head_main") % str(d.get("chapter", "")) if str(d.get("chapter", "")) != "" else Tx.t("ui.quest.main")
		"prologue": s = Tx.t("ui.quest.head_prologue")
		"guided": s = Tx.t("ui.quest.head_lesson")
		"daily", "mortal": s = Tx.t("ui.quest.head_mission")
		_: s = Tx.t("ui.quest.head_side")
	if not ch.quests.is_active(q) and not ch.quests.is_done(q): s = Tx.t("ui.quest.head_offered") % s
	elif board_slip and k in MAIN_KINDS: s += " · " + Tx.t("ui.quest.the_story")
	return s

func _head_col(d: Dictionary) -> Color:
	var k := str(d.get("kind", "side"))
	if k in MAIN_KINDS: return UiKit.BLOOD
	if k in ["daily", "mortal"]: return RecordsKit.NEXT_INK
	return UiKit.JADE_SHADOW

## Near you: the side quests whose givers stand in this zone, two slips (the second a stack when there are more).
func _near(ch, b: Dictionary) -> void:
	var ids: Array = b.near
	var p := RecordsKit.plank(self, Vector2(440, 112), Tx.t("ui.quest.near_you") % str(b.near_zone), str(ids.size()))
	if ids.is_empty():
		text(Vector2(448, p.end.y + 34), Tx.t("ui.quest.nothing_near"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 360)
		return
	_row(ch, ids, Vector2(448, 156), 2, "near", 180.0)

## A row of up to `n` small slips; past `n` the last one is a stack that spreads its group.
func _row(ch, ids: Array, at: Vector2, n: int, group: String, pitch := PITCH) -> void:
	for i in mini(n, ids.size()):
		var more := ids.size() - n if i == n - 1 and ids.size() > n else 0
		_small(ch, Rect2(at + Vector2(i * pitch, (i % 2) * 2), SLIP if pitch >= PITCH else Vector2(pitch - 8, SLIP.y)), str(ids[i]), more, group)

## Today's missions: a row of four slips, the fourth a stack when the board holds more (missed days bank).
func _missions(ch, b: Dictionary) -> void:
	var ids: Array = b.missions
	var done := ids.filter(func(q): return ch.quests.is_active(str(q)) and str(ch.quests.active[str(q)].get("state", "")) == "ready").size()
	RecordsKit.plank(self, Vector2(96, 238), Tx.t("ui.quest.missions"), "%d / %d" % [done, ids.size()] if not ids.is_empty() else "")
	if ids.is_empty():
		var why := Tx.t("ui.notice.missions_open_at_qi_kindling") if not Unlocks.is_unlocked(ch.id, "daily_missions") else Tx.t("ui.notice.all_of_today_missions_are")
		para(Rect2(96, 290, 700, 50), why, 16, UiKit.MIST, 2)
		return
	_row(ch, ids, Vector2(96, 282), COLS, "missions")

## The day's round: the day's points along a red cord, a chest charm hung at each stop (lit when it can be opened, ticked
## once opened), shared by every character. It opens with the Activity Chests.
func _round(ch) -> void:
	if not Unlocks.is_unlocked(ch.id, "activity_chests"): return
	var a: Dictionary = Game.accounts.activity()
	var pts := int(a.get("points", 0))
	var tiers: Array = ContentDB.all("activity")
	var top := int(tiers.back().points) if not tiers.is_empty() else 100
	RecordsKit.plank(self, Vector2(96, 372), Tx.t("ui.quest.round"), "%d / %d" % [mini(pts, top), top])
	var nxt: Dictionary = {}
	for tr in tiers:
		if pts < int(tr.points):
			nxt = tr
			break
	var note := Tx.t("ui.quest.round_next") % [int(nxt.points), _reward_short(nxt.get("rewards", []))] if not nxt.is_empty() else Tx.t("ui.quest.round_full")
	text(Vector2(344, 396), note, 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 464)
	# The cord sags between its ends; the part filled is bright red, a bead at the points now.
	var x0 := 100.0
	var x1 := 804.0
	var cord := func(f: float) -> Vector2: return Vector2(lerpf(x0, x1, f), 432.0 + 16.0 * 4.0 * f * (1.0 - f))
	var pts_line := PackedVector2Array()
	for i in 33: pts_line.append(cord.call(i / 32.0))
	draw_polyline(pts_line, UiKit.INK, 7.0, true)
	draw_polyline(pts_line, UiKit.BLOOD.lerp(UiKit.INK, 0.5), 4.0, true)
	var frac := clampf(float(pts) / float(top), 0.0, 1.0)
	var lit := PackedVector2Array()
	for i in int(frac * 32.0) + 1: lit.append(cord.call(i / 32.0))
	lit.append(cord.call(frac))
	if lit.size() > 1: draw_polyline(lit, UiKit.RED, 4.0, true)
	draw_circle(cord.call(frac), 6.0, UiKit.INK, true, -1.0, true)
	draw_circle(cord.call(frac), 4.5, UiKit.PALE_GOLD, true, -1.0, true)
	var ready_n := 0
	for tr in tiers:
		var f := float(tr.points) / float(top)
		var at: Vector2 = cord.call(f)
		var ready: bool = Game.accounts.chest_ready(str(tr.id))   # today's, or one banked from a day away
		var claimed: bool = (a.get("claimed", []) as Array).has(str(tr.id)) and not ready
		if ready: ready_n += 1
		var box := Rect2(clampf(at.x - 26, 96, 756), 452, 52, 48)
		draw_line(at, Vector2(box.get_center().x, box.position.y), UiKit.INK, 3.0)
		if ready: glow(box.grow(10), Color(UiKit.GOLD, (0.4 + 0.12 * _pulse()) * _halo()))
		rounded(box.grow(1), 6.0, UiKit.INK)
		vshade(box, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.2), UiKit.SURFACE.wood.lerp(UiKit.INK, 0.2))
		draw_rect(box.grow(-2), UiKit.GOLD if ready or claimed else UiKit.BRONZE, false, 1.5)
		icon_at(Rect2(box.get_center() - Vector2(16, 16), Vector2(32, 32)), "open", Color.WHITE if ready or claimed else Color(UiKit.HOLLOW, 0.8))
		if claimed:
			draw_circle(box.position + Vector2(box.size.x, 4), 12.0, UiKit.INK, true, -1.0, true)
			draw_circle(box.position + Vector2(box.size.x, 4), 10.0, UiKit.BLOOD, true, -1.0, true)
			ground(Rect2(box.position + Vector2(box.size.x - 10, -6), Vector2(20, 20)), UiKit.BLOOD)
			text(Vector2(box.end.x - 10, box.position.y + 10), "✓", 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 20)
		region(box, "chest", str(tr.id), ready, Tx.plural("ui.quest.chest_locked", int(tr.points)) % int(tr.points) if not claimed else Tx.t("ui.quest.chest_claimed"))
		text(Vector2(box.position.x, 520), str(int(tr.points)), 14, UiKit.PALE_GOLD if pts >= int(tr.points) else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, box.size.x)
	var lead := Tx.plural("ui.quest.round_ready", ready_n) % ready_n if ready_n > 0 else ""
	if lead != "": para(Rect2(100, 462, 110, 44), lead, 14, UiKit.BRIGHT_JADE, 2)

## A reward list in short: "15 Spirit Stones, 2 Spirit Jade".
func _reward_short(rewards: Array) -> String:
	var parts: Array = []
	for r in rewards:
		if str(r.get("kind", "")) == "grant_currency": parts.append("%s %s" % [UiKit.fmt(int(r.amount)), currency_name(str(r.currency))])
		elif str(r.get("kind", "")) == "grant_item": parts.append("%d %s" % [int(r.get("count", 1)), ContentDB.item_name(str(r.item))])
	return ", ".join(parts)

## The other side quests stacked under their nameboards (the companions', each zone's); a tap spreads a stack.
func _stacks(ch, b: Dictionary) -> void:
	var groups: Array = b.groups
	var y := 534.0 if Unlocks.is_unlocked(ch.id, "activity_chests") else 380.0
	var n := mini(groups.size(), COLS)
	for i in n:
		var g: Dictionary = groups[i]
		var x := 96.0 + i * PITCH
		var label := str(g.label)
		var count: int = g.ids.size()
		var gid := str(g.id)
		if i == COLS - 1 and groups.size() > COLS:   # the rest share the last stack
			label = Tx.t("ui.quest.elsewhere")
			gid = "more"
			for k in range(COLS, groups.size()): count += groups[k].ids.size()
		RecordsKit.plank(self, Vector2(x, y), fit(label, 16, SLIP.x - 40 - UiKit.text_width(str(count), 16)), str(count))
		_small(ch, Rect2(Vector2(x, y + 46), SLIP), str(g.ids[0]), count - 1, gid)
	if n > 0 and n <= 2:
		# Beside two stacks, where the largest one's quests stand, region by region.
		var big: Dictionary = groups[n - 1]
		var parts: Array = []
		for rg in big.regions: parts.append("%s %d" % [rg, int(big.regions[rg])])
		var bx := 96.0 + n * PITCH
		para(Rect2(bx, y + 44, 800 - bx, 60), " · ".join(parts), 14, UiKit.MIST, 3)
		text(Vector2(bx, y + 118), Tx.t("ui.quest.spread_hint"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 800 - bx)
	elif groups.is_empty() and b.near.is_empty():
		text(Vector2(96, y + 30), Tx.t("ui.quest.no_side"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 700)

## A stack spread across the board: its slips in rows of four, a sheet at a time, and the way back.
func _spread(ch, b: Dictionary) -> void:
	var ids: Array = []
	var label := ""
	match spread:
		"near":
			ids = b.near
			label = Tx.t("ui.quest.near_you") % str(b.near_zone)
		"missions":
			ids = b.missions
			label = Tx.t("ui.quest.missions")
		_:
			for g in b.groups:
				if str(g.id) == spread or (spread == "more" and b.groups.find(g) >= COLS - 1):
					ids.append_array(g.ids)
					label = str(g.label)
	if ids.is_empty():
		spread = ""
		return
	RecordsKit.plank(self, Vector2(96, 238), label, str(ids.size()))
	btn(Rect2(560, 232, 240, 48), Tx.t("ui.quest.back"), "spread", "")
	var per := COLS * SPREAD_ROWS
	var sheets := int(ceil(ids.size() / float(per)))
	sheet = clampi(sheet, 0, sheets - 1)
	for i in range(sheet * per, mini(ids.size(), (sheet + 1) * per)):
		var k := i - sheet * per
		_small(ch, Rect2(Vector2(96 + (k % COLS) * PITCH, 290 + (k / COLS) * 88), SLIP), str(ids[i]))
	_sheets(sheets, Vector2(96, 640 - 8))

## Page arrows under a spread or the finished slips, with which sheet this is.
func _sheets(sheets: int, at: Vector2) -> void:
	if sheets <= 1: return
	btn(Rect2(at.x + 250, at.y - 4, 56, 48), "‹", "sheet", sheet - 1, false, sheet > 0, "", 22)
	text(Vector2(at.x + 314, at.y + 26), "%d / %d" % [sheet + 1, sheets], 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 80)
	btn(Rect2(at.x + 402, at.y - 4, 56, 48), "›", "sheet", sheet + 1, false, sheet < sheets - 1, "", 22)

## Done: the finished slips, newest first, stamped; four across and six down a sheet.
func _done_ids(ch) -> Array:
	var out: Array = []
	for q in ch.quests.done: out.append(str(q))
	out.reverse()
	return out.filter(func(q): return not Game.quest.quest_def(ch, q).is_empty())

func _done(ch) -> void:
	var ids := _done_ids(ch)
	if ids.is_empty():
		text(Vector2(96, 160), Tx.t("ui.quest.nothing_done"), 18, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 700)
		return
	var per := COLS * DONE_ROWS
	var sheets := int(ceil(ids.size() / float(per)))
	sheet = clampi(sheet, 0, sheets - 1)
	for i in range(sheet * per, mini(ids.size(), (sheet + 1) * per)):
		var k := i - sheet * per
		var r := Rect2(Vector2(96 + (k % COLS) * PITCH, 112 + (k / COLS) * 80), Vector2(SLIP.x, 72))
		_small(ch, r, str(ids[i]), 0, "", true)
	_sheets(sheets, Vector2(96, 640))

# ------------------------------------------------------------------ the slip being read
func _reading(ch) -> void:
	if sel == "": return
	var r := READ
	tour_mark("read", r)
	var lift := 1.0 if lifted_at < 0.0 or UiKit.reduce_motion() else clampf((t - lifted_at) / 0.2, 0.0, 1.0)
	move(Vector2(-(1.0 - lift) * 48.0, (1.0 - lift) * 20.0))
	rounded(Rect2(r.position + Vector2(10, 14), r.size - Vector2(4, 4)), 4.0, Color(UiKit.INK, 0.45))
	RecordsKit.slip(self, r)
	var nx := _next(ch) if sel == "next" else {}
	var q := str(nx.get("quest", "")) if sel == "next" else sel
	var d := ContentDB.entry("quests", q) if sel == "next" else Game.quest.quest_def(ch, q)
	if sel == "next" and nx.get("gate", false): d = {"name": str(nx.name)}   # decision 41: the prototype's tale rests here
	var active: bool = sel != "next" and ch.quests.is_active(q)
	var st: Dictionary = ch.quests.active.get(q, {}) if active else {}
	var x := r.position.x + 16
	var w := r.size.x - 32
	RecordsKit.head(self, Rect2(r.position + Vector2(0, 4), Vector2(r.size.x, 32)), _head_col(d), Tx.t("ui.quest.head_next") if sel == "next" else _head(ch, q, d), 16)
	RecordsKit.pin(self, Vector2(r.position.x + r.size.x * 0.5, r.position.y + 10), true)
	var nm := str(d.get("name", q))
	text(Vector2(x, r.position.y + 72), nm, 30 if UiKit.text_width(nm, 30, true) <= w else 26, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, w, true)
	var giver := Game.quest.hand_in_npc(ch, d) if d.has("hand_in_any") else QuestAuthority.own_npc(ch, d.get("giver_any", d.get("giver", "")))
	var home := _home(ch, d, giver) if giver != "" else ""
	var from := ""
	if giver != "": from = Tx.t("ui.quest.from_at") % [ContentDB.name_of("npcs", giver), str(ContentDB.room(home).get("name", ""))] if home != "" else Tx.t("ui.quest.from") % ContentDB.name_of("npcs", giver)
	var y := r.position.y + 96
	if from != "": text(Vector2(x, y), from, 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, w)
	# Where it leads: here, and the room its step (or its giver, or the Next entry) is in.
	var goal := ""
	if sel == "next": goal = str(nx.get("target_room", ""))
	elif active: goal = Game.quest.quest_target(ch, d, st)
	elif not ch.quests.is_done(q): goal = home
	var here := str(ch.position.get("room", ""))
	y += 12
	if goal != "" and not ch.quests.is_done(q):
		_route_line(ch, Rect2(x, y, w, 72), here, goal)
		y += 84
	# What it says, its steps, and what it gives.
	if sel == "next":
		y += para(Rect2(x, y, w, 200), _next_text(ch, nx), 16, RecordsKit.INK, 8) + 8
	else:
		var said: Array = d.get("progress_text", []) if active and not (d.get("progress_text", []) as Array).is_empty() else d.get("offer_text", [])
		if not said.is_empty(): y += para(Rect2(x, y, w, 88), str(said[0]), 16, RecordsKit.INK, 4) + 6
		y = _steps(ch, q, d, st, Rect2(x, y, w, 0))
		y = _rewards(d, Rect2(x, y + 4, w, 590 - y))
	# Go walks there; Track, Untrack and Abandon.
	if ch.quests.is_done(q) and sel != "next":
		RecordsKit.stamp(self, Vector2(r.end.x - 70, r.end.y - 70), Tx.t("ui.quest.stamp_done"), 36.0)
	else:
		var by := r.end.y - 64
		var abandon := active and str(d.get("kind", "")) in ["side", "daily", "mortal"]
		var gw := 110.0 if abandon else 156.0
		# Decision 41: nowhere past the prototype's gate to go, and the button says why.
		var gated: bool = QuestAuthority.past_gate(ch, goal) or (sel == "next" and nx.get("gate", false))
		btn(Rect2(x, by, gw, 52), Tx.t("ui.quest.go"), "go", goal, true, regions_away(ch, goal) > 0 and not gated,
			Tx.t("sim.world.road_being_drawn") if gated else go_reason(ch, goal), 22)
		if active:
			btn(Rect2(x + gw + 8, by + 2, (w - gw - 8) if not abandon else 100.0, 48), Tx.t("ui.quest.untrack") if ch.quests.tracked.has(q) else Tx.t("ui.quest.track"), "track", q, false, true, "", 20)
		if abandon: btn(Rect2(r.end.x - 16 - 96, by + 2, 96, 48), Tx.t("ui.quest.abandon"), "abandon", q, false, true, "", 18)
	move()

## The route across the slip: you are here (jade) to where it leads (gold), dotted, and how many regions away.
func _route_line(ch, r: Rect2, here: String, goal: String) -> void:
	var a := r.position + Vector2(12, 24)
	var b := Vector2(r.end.x - 12, r.position.y + 24)
	var prev := a
	for i in range(1, 25):
		var f := i / 24.0
		var p := a.lerp(b, f) + Vector2(0, sin(f * TAU) * 10.0)
		if i % 2 == 1: draw_line(prev, p, RecordsKit.INK, 2.5, true)
		prev = p
	for e in [[a, UiKit.JADE], [b, UiKit.GOLD]]:
		draw_circle(e[0], 10.0, RecordsKit.INK, true, -1.0, true)
		draw_circle(e[0], 7.5, e[1], true, -1.0, true)
	var away := regions_away(ch, goal)
	var mid := Tx.t("ui.quest.here") if here == goal else (Tx.plural("ui.calendar.regions_away", away) % away if away > 0 else Tx.t("ui.quest.no_way"))
	text(Vector2(r.get_center().x - 70, r.position.y + 52), mid, 14, RecordsKit.JADE_INK, HORIZONTAL_ALIGNMENT_CENTER, 140)
	text(Vector2(r.position.x, r.position.y + 52), Tx.t("ui.quest.you_are_here"), 14, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, 100)
	text(Vector2(r.position.x, r.position.y + 70), str(ContentDB.room(here).get("name", "")), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, 110)
	text(Vector2(r.end.x - 120, r.position.y + 52), str(ContentDB.room(goal).get("name", "")), 14, RecordsKit.INK, HORIZONTAL_ALIGNMENT_RIGHT, 120)
	text(Vector2(r.end.x - 120, r.position.y + 70), _region_name(goal), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_RIGHT, 120)

## The steps: ➤ the one now, ✓ those done, ○ those after. Returns the y under them.
func _steps(ch, q: String, d: Dictionary, st: Dictionary, r: Rect2) -> float:
	var y := r.position.y
	var objs: Array = d.get("objectives", [])
	var now := Game.quest.step_now(ch, d, st) if not st.is_empty() else -1
	for i in objs.size():
		if y > 520.0: break
		var o: Dictionary = objs[i]
		var have := int(st.get("progress", [])[i]) if not st.is_empty() else (int(o.get("count", 1)) if ch.quests.is_done(q) else 0)
		var need := int(o.get("count", 1))
		var done := have >= need
		var mark := "✓" if done else ("➤" if i == now else "○")
		text(Vector2(r.position.x, y + 16), mark, 14, RecordsKit.JADE_INK if done else (RecordsKit.RED_INK if i == now else RecordsKit.BROWN))
		var words := str(o.get("text", o.kind)) + (" (%d / %d)" % [mini(have, need), need] if need > 1 else "")
		y += para(Rect2(r.position.x + 22, y, r.size.x - 22, 42), words, 14, RecordsKit.JADE_INK if done else RecordsKit.INK, 2) + 2
	return y + 6

## Rewards: currencies and items with their icons, what is learned or earned, and the story's next quest.
func _rewards(d: Dictionary, r: Rect2) -> float:
	var y := r.position.y
	var lines: Array = []   # [icon, words]
	for rw in d.get("rewards", []):
		match str(rw.get("kind", "")):
			"grant_currency": lines.append([currency_icon(str(rw.currency)), "%s %s" % [UiKit.fmt(int(rw.amount)), currency_name(str(rw.currency))]])
			"grant_item": lines.append([str(rw.item), "%d %s" % [int(rw.get("count", 1)), ContentDB.item_name(str(rw.item))]])
	for s in _reward_lines(d): lines.append(["", str(s)])
	if str(d.get("next", "")) != "" and ContentDB.has_entry("quests", str(d.next)):
		lines.append(["", Tx.t("ui.quest.then_story") % ContentDB.name_of("quests", str(d.next))])
	if lines.is_empty() or r.size.y < 40: return y
	text(Vector2(r.position.x, y + 14), Tx.t("ui.quest.rewards"), 14, RecordsKit.RED_INK)
	y += 20
	for ln in lines:
		if y + 22 > r.end.y: break
		var tx := r.position.x
		if str(ln[0]) != "":
			icon_at(Rect2(tx, y, 32, 32), str(ln[0]))
			tx += 38
		text(Vector2(tx, y + 22), str(ln[1]), 14, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, r.end.x - tx)
		y += 32 if str(ln[0]) != "" else 22
	return y

## Rewards that are not items: what is learned or earned, and the realm-progress share (S29).
func _reward_lines(d: Dictionary) -> Array:
	var out: Array = []
	for r in d.get("rewards", []):
		match str(r.get("kind", "")):
			"learn_technique": out.append(Tx.t("ui.quest.reward_technique") % ContentDB.name_of("techniques", str(r.technique)))
			"learn_recipe": out.append(Tx.t("ui.quest.reward_recipe") % ContentDB.name_of("recipes", str(r.recipe)))
			"learn_method": out.append(Tx.t("ui.quest.reward_method") % ContentDB.name_of("methods", str(r.method)))
			"learn_secret_art": out.append(Tx.t("ui.quest.reward_secret_art") % ContentDB.name_of("secret_arts", str(r.art)))
			"grant_title": out.append(Tx.t("ui.quest.reward_title") % ContentDB.name_of("titles", str(r.title)))
			"sect_rank": out.append(Tx.t("ui.quest.reward_rank") % ContentDB.rank_name(str(r.rank)))
			"add_contribution": out.append(Tx.t("ui.quest.reward_contribution") % int(r.amount))
			"deed":
				var dd := ContentDB.entry("karma", str(r.deed))
				if int(dd.get("merit", 0)) > 0: out.append(Tx.t("ui.quest.reward_merit") % int(dd.merit))
				if int(dd.get("fame", 0)) > 0: out.append(Tx.t("ui.quest.reward_fame") % int(dd.fame))
	var pct := float(ContentDB.curve("quest_qp_pct.%s" % str(d.get("qp", d.get("kind", "side"))), 0.0))
	if pct > 0.0: out.append(Tx.t("ui.quest.reward_progress") % int(round(pct * 100.0)))
	return out

## Between chapters, what the story waits for: the Next entry's lines (who gives it and where, or the Level it waits on
## and the other way to close it), and held by a chapter's Level floor (P12) the gap and the fastest ways to close it.
func _next_text(ch, nx: Dictionary) -> String:
	var body := "\n".join((nx.get("lines", []) as Array).map(func(l): return str(l.text)))
	var gap: Dictionary = Game.quest.floor_gap(ch)
	if not gap.is_empty() and str(gap.quest) == str(nx.get("quest", "")):
		body += "\n" + Tx.t("ui.quest.opens_at") % [ContentDB.name_of("realms", str(gap.realm)), int(gap.level), int(gap.have)] + "\n" + Tx.t("ui.quest.gap_ways")
		for f in gap.fields: body += "\n· " + Tx.t("ui.quest.gap_field") % [str(ContentDB.room(str(f[0])).get("name", f[0])), int(f[1]), int(f[2])]
		if int(gap.side) > 0: body += "\n· " + Tx.plural("ui.quest.gap_side", int(gap.side)) % int(gap.side)
		if int(gap.dailies) > 0: body += "\n· " + Tx.t("ui.quest.gap_dailies")
		if gap.post: body += "\n· " + Tx.t("ui.quest.gap_post")
	return body

func on_action(id: String, data) -> void:
	match id:
		"chest": submit({"type": "claim_activity_chest", "tier": str(data)})
		"sel":
			if str(data) != sel: lifted_at = t
			sel = str(data)
		"spread":
			spread = str(data)
			sheet = 0
		"sheet": sheet = int(data)
		"_tab":
			sel = ""
			spread = ""
			sheet = 0
		"go":
			if submit({"type": "auto_path", "target": str(data)}).get("ok", false): close()
		"track": submit({"type": "track_quest", "quest": str(data)})
		"abandon": ask(Tx.t("ui.quest.abandon_this_quest_you_can"), "abandon_yes", data, true)
		"abandon_yes":
			if submit({"type": "abandon_quest", "quest": str(data)}).get("ok", false): sel = ""
