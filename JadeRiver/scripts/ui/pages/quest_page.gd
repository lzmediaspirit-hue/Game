extends Page
## Quest log (S19): Main, Side, Daily, Done. Track up to three; abandon side quests.

var sel := ""

func _init() -> void:
	title = "Quests"
	tabs = [{"id": "main", "label": "Main"}, {"id": "side", "label": "Side"}, {"id": "daily", "label": "Daily"}, {"id": "done", "label": "Done"}]

func ids_for(ch, which: String) -> Array:
	var out: Array = []
	if which == "done":
		for q in ch.quests.done: out.append(q)
		out.reverse()
		return out
	for q in ch.quests.active:
		var k := str(Game.quest.quest_def(ch, q).get("kind", "side"))
		var group := "main" if k in ["main", "prologue", "guided"] else ("daily" if k == "daily" else "side")
		if group == which: out.append(q)
	if which in ["main", "side"]:
		for q in ch.quests.offered:
			var d := ContentDB.entry("quests", q)
			var k2 := str(d.get("kind", "side"))
			var g2 := "main" if k2 in ["main", "prologue", "guided"] else "side"
			if g2 == which and not ch.quests.is_active(q) and Game.quest.can_offer(ch, d): out.append(q)
	return out

## Between chapters the Main tab says what the story is waiting for.
func _next_chapter(ch, left: Rect2) -> void:
	var keyed: Array = []   # [chapter * 1000 + data order, quest]: story order, stable within a chapter
	var all_q: Array = ContentDB.all("quests")
	for i in all_q.size():
		var dq: Dictionary = all_q[i]
		if str(dq.get("kind", "")) != "main": continue
		var chap := str(dq.get("chapter", ""))
		keyed.append([(int(chap) if chap.is_valid_int() else 0) * 1000 + i, dq])
	keyed.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	for kd in keyed:
		var d: Dictionary = kd[1]
		var q := str(d.id)
		if ch.quests.done.has(q) or ch.quests.is_active(q) or d.get("hidden", false): continue
		var waits := true
		for r in d.get("requires", {}).get("all", []):
			if str(r.get("kind", "")) == "quest_done" and not ch.quests.done.has(str(r.get("quest", ""))): waits = false
		if not waits: continue
		var why := RequirementRules.first_failure_text(d.get("requires", {}), Game.ctx(ch))
		var body := "Next in the story: %s" % str(d.get("name", q))
		if why != "": body += "\n" + why
		else: body += "\nThe river will call when it is time."
		para(Rect2(left.position + Vector2(24, 100), Vector2(left.size.x - 48, 120)), body, 18, UiKit.MIST)
		return

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var ids := ids_for(ch, str(tabs[tab].id))
	var left := Rect2(content.position.x, content.position.y, 440, content.size.y)
	panel(left)
	if ids.is_empty():
		text(left.position + Vector2(0, 70), "Nothing here yet.", 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, left.size.x)
		if str(tabs[tab].id) == "main": _next_chapter(ch, left)
	list("q", left.grow(-10), ids.size(), 62, func(i: int, rr: Rect2):
		var q := str(ids[i])
		var d := Game.quest.quest_def(ch, q)
		var active: bool = ch.quests.is_active(q)
		var ready: bool = active and ch.quests.active[q].get("state") == "ready"
		panel(rr, "minor_panel", "selected" if sel == q else "normal")
		var mark := "?" if ready else ("!" if not active and str(tabs[tab].id) != "done" else "")
		text(rr.position + Vector2(14, 38), mark, 26, UiKit.GOLD)
		text(rr.position + Vector2(40, 38), str(d.get("name", q)), 20, UiKit.PAPER if active or str(tabs[tab].id) == "done" else UiKit.MIST)
		if ch.quests.tracked.has(q): text(rr.position + Vector2(0, 38), "◆", 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, rr.size.x - 14)
		region(rr, "sel", q)
	)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	if sel == "" and not ids.is_empty(): sel = str(ids[0])
	if sel == "": return
	var d2 := Game.quest.quest_def(ch, sel)
	heading(right.position + Vector2(24, 44), str(d2.get("name", sel)), right.size.x - 48)
	var y := right.position.y + 70
	var giver := Game.quest.hand_in_npc(ch, d2) if d2.has("hand_in_any") else str(d2.get("giver", ""))
	if giver != "": text(Vector2(right.position.x + 24, y + 18), "From %s" % ContentDB.name_of("npcs", giver), 17, UiKit.MIST)
	y += 30
	var offer: Array = d2.get("offer_text", [])
	if not offer.is_empty(): y += para(Rect2(right.position.x + 24, y, right.size.x - 48, 110), str(offer[0]), 18, UiKit.PAPER, 4) + 10
	var st: Dictionary = ch.quests.active.get(sel, {})
	for i in d2.get("objectives", []).size():
		var o: Dictionary = d2.objectives[i]
		var have := int(st.get("progress", [])[i]) if not st.is_empty() else (int(o.get("count", 1)) if ch.quests.is_done(sel) else 0)
		var need := int(o.get("count", 1))
		var done := have >= need
		text(Vector2(right.position.x + 24, y + 22), ("✓ " if done else "○ ") + str(o.get("text", o.kind)) + (" (%d/%d)" % [have, need] if need > 1 else ""), 18, UiKit.BRIGHT_JADE if done else UiKit.PAPER)
		y += 28
	y += 12
	var rewards: Array = d2.get("rewards", [])
	if not rewards.is_empty():
		text(Vector2(right.position.x + 24, y + 20), "Rewards", 19, UiKit.GOLD)
		var x := right.position.x + 24
		for r in rewards:
			if r.get("kind", "") == "grant_item":
				slot_box(Rect2(x, y + 30, 52, 52), str(r.item), int(r.get("count", 1)))
				x += 58
			elif r.get("kind", "") == "grant_currency":
				x += currency_pill(Vector2(x, y + 40), str(r.currency), int(r.amount)) + 8
	if ch.quests.is_active(sel):
		btn(Rect2(right.position.x + 24, right.end.y - 70, 200, 52), "Untrack" if ch.quests.tracked.has(sel) else "Track", "track", sel)
		if str(d2.get("kind", "")) in ["side", "daily"]:
			btn(Rect2(right.end.x - 224, right.end.y - 70, 200, 52), "Abandon", "abandon", sel)

func on_action(id: String, data) -> void:
	match id:
		"sel": sel = str(data)
		"_tab": sel = ""
		"track": submit({"type": "track_quest", "quest": str(data)})
		"abandon": ask("Abandon this quest? You can take it again later.", "abandon_yes", data, true)
		"abandon_yes": submit({"type": "abandon_quest", "quest": str(data)})
