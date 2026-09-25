extends Page
## A gift (S49): one a day for each person with favourite gifts. Pick something from the bag; what they love is
## worth a heart, what they like less, anything else a courtesy. What they told you they love or like is marked.

var npc := ""
var sel := -1

func _init() -> void:
	title = Tx.t("ui.gift.title")
	frame_rect = Rect2(150, 60, 980, 600)

func setup() -> void:
	npc = str(args.get("npc", args.get("tab", "")))   # --open-page=gift:npc passes it as the tab
	sel = -1

func draw_page() -> void:
	var ch = c()
	if ch == null or npc == "": return
	var id := Game.relations.aff_id(npc)
	var a: Dictionary = ch.relations.affinity.get(id, {})
	var known: Dictionary = a.get("known", {})
	var gifted_today := int(a.get("gift_day", -1)) == Clock.reset_day(Clock.now_utc())
	# Left: who, their hearts, what you know of them.
	var left := Rect2(content.position, Vector2(330, content.size.y))
	panel(left)
	var x := left.position.x + 22
	var y := left.position.y + 40
	heading(Vector2(x, y), ContentDB.name_of("npcs", id), left.size.x - 44)
	y += 34
	UiKit.draw_hearts(self, Vector2(x, y), ch.relations.hearts_of(id), 5, 12.0)
	y += 30
	var per := int(Game.relations.acfg().get("per_heart", 100))
	if ch.relations.hearts_of(id) < int(Game.relations.acfg().get("max_hearts", 5)):
		bar(Rect2(x, y, left.size.x - 44, 24), float(int(a.get("points", 0)) % per) / float(per), Color("e05a6e"), Tx.t("ui.gift.next_heart") % [int(a.get("points", 0)) % per, per])
	y += 44
	var loves: Array = []
	var likes: Array = []
	for it in known:
		if str(known[it]) == "loved": loves.append(ContentDB.item_name(str(it)))
		else: likes.append(ContentDB.item_name(str(it)))
	text(Vector2(x, y), Tx.t("ui.gift.loves"), 16, UiKit.MIST)
	y += 10
	y += para(Rect2(x, y, left.size.x - 44, 60), ", ".join(loves) if not loves.is_empty() else Tx.t("ui.gift.unknown"), 17, UiKit.PALE_GOLD if not loves.is_empty() else UiKit.HOLLOW, 2) + 22
	text(Vector2(x, y), Tx.t("ui.gift.likes"), 16, UiKit.MIST)
	y += 10
	y += para(Rect2(x, y, left.size.x - 44, 80), ", ".join(likes) if not likes.is_empty() else Tx.t("ui.gift.unknown"), 17, UiKit.PAPER if not likes.is_empty() else UiKit.HOLLOW, 3) + 16
	para(Rect2(x, left.end.y - 150, left.size.x - 44, 140), Tx.t("ui.gift.given_today") if gifted_today else Tx.t("ui.gift.rules"), 16,
		UiKit.PALE_GOLD if gifted_today else UiKit.MIST, 6)
	# Right: the bag's giftable things.
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(right)
	var slots: Array = []
	for i in ch.inventory.bag.size():
		var s = ch.inventory.bag[i]
		if s != null and RelationsAuthority.giftable(s): slots.append(i)
	if slots.is_empty():
		para(Rect2(right.position.x + 22, right.position.y + 30, right.size.x - 44, 80), Tx.t("ui.gift.nothing"), 18, UiKit.MIST)
		return
	var cell := 64.0
	var cols := int((right.size.x - 40) / (cell + 8))
	var grid := Rect2(right.position.x + 20, right.position.y + 18, right.size.x - 30, right.size.y - 110)
	list("gifts", grid, int(ceil(slots.size() / float(cols))), cell + 8, func(row: int, rr: Rect2):
		for k in cols:
			var j := row * cols + k
			if j >= slots.size(): break
			var bi: int = slots[j]
			var s: Dictionary = ch.inventory.bag[bi]
			var r := Rect2(rr.position.x + k * (cell + 8), rr.position.y, cell, cell)
			slot_box(r, str(s.id), int(s.get("count", 1)), str(s.get("quality", "")), "pick", bi, bi == sel)
			if known.has(str(s.id)): UiKit.draw_hearts(self, r.position + Vector2(r.size.x - 20, 12), 1 if str(known[str(s.id)]) == "loved" else 0, 1, 7.0)
	)
	var by := right.end.y - 76
	if sel >= 0 and sel < ch.inventory.bag.size() and ch.inventory.bag[sel] != null:
		text(Vector2(right.position.x + 22, by + 34), fit(ContentDB.item_name(str(ch.inventory.bag[sel].id)), 20, right.size.x - 280), 20, UiKit.PAPER)
	btn(Rect2(right.end.x - 230, by, 210, 56), Tx.t("ui.gift.give"), "give", sel, true, sel >= 0 and not gifted_today,
		Tx.t("ui.gift.given_today") if gifted_today else Tx.t("ui.gift.pick_first"), 20)

func on_action(id: String, data) -> void:
	match id:
		"pick": sel = int(data)
		"give":
			var r := submit({"type": "give_gift", "npc": npc, "index": int(data)})
			if r.get("ok", false):
				flash(Tx.t("ui.gift.reaction_" + str(r.reaction)) % ContentDB.name_of("npcs", Game.relations.aff_id(npc)))
				sel = -1
	queue_redraw()
