extends Page
## Training sect (S20): rank, contribution, promotion trials, missions and the sect shop.

func _init() -> void:
	title = Tx.t("ui.training_sect.sect")

func setup() -> void:
	var ch = c()
	var joined: bool = ch != null and str(ch.training_sect.get("id", "")) != ""
	var role_ok: bool = joined and RequirementRules.passes({"all": [{"kind": "sect_rank_at_least", "rank": str(ContentDB.config("sect_roles").get("role_rank", "outer_disciple"))}]}, Game.ctx(ch))
	tabs = [{"id": "rank", "label": Tx.t("ui.training_sect.rank_tab")},
		{"id": "role", "label": Tx.t("ui.training_sect.role_tab"), "locked": "" if role_ok else Tx.t("sim.training_sect.role_rank")}]

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	if str(tabs[tab].id) == "role":
		_role(ch)
		return
	var ts: Dictionary = ch.training_sect
	var r := Rect2(content.position, content.size)
	panel(r)
	if str(ts.get("id", "")) == "":
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.training_sect.you_are_unaffiliated_the_jade"), 22, UiKit.PAPER)
		return
	var sect := ContentDB.entry("sects", str(ts.id))
	text(r.position + Vector2(30, 50), str(sect.get("full_name", sect.get("name", ""))), 32, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	var ranks: Dictionary = ContentDB.config("sect_ranks")
	var rank_name := str(ts.get("rank", "")).replace("_", " ").capitalize()
	text(r.position + Vector2(30, 90), Tx.t("ui.training_sect.rank") % rank_name, 22)
	currency_pill(r.position + Vector2(30, 110), "contribution", int(ts.get("contribution", 0)))
	# S48 the Blood path lowers the sect's regard; below zero the Mission Hall lends no manuals.
	var regard := int(ts.get("reputation", {}).get(str(ts.id), 0))
	text(r.position + Vector2(330, 140), Tx.t("ui.training_sect.regard") % regard, 20, UiKit.PAPER if regard >= 0 else UiKit.RED)
	var order: Array = ranks.get("order", [])
	var i := order.find(str(ts.get("rank", "")))
	var y := r.position.y + 180
	for j in order.size():
		var rk: Dictionary = ranks.ranks[j]
		var done := j <= i
		text(Vector2(r.position.x + 30, y), ("◆ " if done else "◇ ") + str(rk.name), 20, UiKit.GOLD if done else UiKit.MIST)
		if j == i + 1:
			var ok := RequirementRules.passes(rk.get("requires", {}), Game.ctx(ch))
			text(Vector2(r.position.x + 300, y), RequirementRules.first_failure_text(rk.get("requires", {}), Game.ctx(ch)) if not ok else Tx.t("ui.training_sect.ready"), 17, UiKit.PAPER if ok else UiKit.MIST)
			btn(Rect2(r.position.x + 640, y - 30, 220, 46), Tx.t("ui.training_sect.promotion_trial"), "promote", null, true, ok, Tx.t("ui.training_sect.not_yet"))
		y += 40
	btn(Rect2(r.end.x - 260, r.end.y - 76, 230, 56), Tx.t("ui.training_sect.sect_shop"), "shop", null, false, Unlocks.is_unlocked(ch.id, "contribution_shop"), Unlocks.locked_text("contribution_shop"))
	btn(Rect2(r.end.x - 520, r.end.y - 76, 230, 56), Tx.t("ui.training_sect.missions"), "missions")

## S48 sect role variants: the signature line's damage or support variant, and the sect tree bought with contribution.
func _role(ch) -> void:
	var ts: Dictionary = ch.training_sect
	var sid := str(ts.get("id", ""))
	var roles := ContentDB.entry("sect_roles", sid)
	var cfg: Dictionary = ContentDB.config("sect_roles")
	var r := Rect2(content.position, content.size)
	if roles.is_empty():
		panel(r)
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.training_sect.you_are_unaffiliated_the_jade"), 22, UiKit.PAPER)
		return
	var left := Rect2(r.position, Vector2(470, r.size.y))
	panel(left)
	var names: Array = []
	for tid in roles.get("signature", []): names.append(ContentDB.name_of("techniques", str(tid)))
	para(Rect2(left.position + Vector2(20, 14), Vector2(left.size.x - 40, 50)), Tx.t("ui.training_sect.signature_line") % ", ".join(names), 17, UiKit.PALE_GOLD, 2)
	var role := str(ts.get("role", ""))
	var y := left.position.y + 70
	for key in ["damage", "support"]:
		var v: Dictionary = roles.get("variants", {}).get(key, {})
		var vr := Rect2(left.position.x + 16, y, left.size.x - 32, 150)
		var mine: bool = role == str(key)
		panel(vr, "minor_panel", "selected" if mine else "normal")
		text(vr.position + Vector2(16, 30), "%s · %s" % [Tx.t("ui.training_sect." + key), str(v.get("name", ""))], 20, UiKit.GOLD if mine else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
		para(Rect2(vr.position + Vector2(16, 42), Vector2(vr.size.x - 32, 60)), str(v.get("desc", "")), 15, UiKit.MIST, 3)
		btn(Rect2(vr.end.x - 150, vr.end.y - 50, 136, 40), Tx.t("ui.training_sect.chosen") if mine else Tx.t("ui.training_sect.choose"), "role", key, not mine, not mine, "", 16)
		y += 162
	var note := Tx.t("ui.training_sect.switch_cost") % int(cfg.get("switch_cost", 50)) if role != "" else ""
	var sup := int(round((Game.combat.sect_support_mult(ch) - 1.0) * 100.0))
	if sup > 0: note += ("  " if note != "" else "") + Tx.t("ui.training_sect.support_scaling") % sup
	para(Rect2(left.position.x + 20, y, left.size.x - 40, 44), note, 15, UiKit.MIST, 2)
	# The tree: three branches of five nodes, bought in order.
	var right := Rect2(left.end.x + 14, r.position.y, r.size.x - left.size.x - 14, r.size.y)
	panel(right)
	text(right.position + Vector2(20, 34), Tx.t("ui.training_sect.tree"), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	currency_pill(right.position + Vector2(right.size.x - 210, 8), "contribution", int(ts.get("contribution", 0)))
	var branches: Array = cfg.get("tree", {}).get("branches", [])
	var tree: Dictionary = ts.get("tree", {})
	var colw := (right.size.x - 40 - 16 * (branches.size() - 1)) / float(maxi(1, branches.size()))
	for bi in branches.size():
		var b: Dictionary = branches[bi]
		var x := right.position.x + 20 + bi * (colw + 16)
		text(Vector2(x, right.position.y + 76), str(b.get("name", {}).get(sid, b.id)), 18, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, colw, true)
		var lvl := int(tree.get(str(b.id), 0))
		var nodes: Array = b.get("nodes", [])
		var nh := (right.end.y - right.position.y - 104) / float(maxi(1, nodes.size()))
		for ni in nodes.size():
			var nd: Dictionary = nodes[ni]
			var nr := Rect2(x, right.position.y + 90 + ni * nh, colw, nh - 8)
			var owned := ni < lvl
			panel(nr, "minor_panel", "selected" if owned else "normal")
			para(Rect2(nr.position + Vector2(10, 4), Vector2(nr.size.x - 20, nr.size.y - 30)), str(nd.get("desc", "")), 14, UiKit.PAPER if owned else UiKit.MIST, 2)
			if owned:
				text(nr.position + Vector2(10, nr.size.y - 12), "✓", 18, UiKit.BRIGHT_JADE)
			elif ni == lvl:
				var why := ""
				if nd.has("rank") and not RequirementRules.passes({"all": [{"kind": "sect_rank_at_least", "rank": str(nd.rank)}]}, Game.ctx(ch)):
					why = Tx.t("req.sect_rank") % str(nd.rank).replace("_", " ").capitalize()
				elif int(ts.get("contribution", 0)) < int(nd.get("cost", 0)): why = Tx.t("sim.training_sect.not_enough_contribution") % int(nd.get("cost", 0))
				btn(Rect2(nr.end.x - 86, nr.end.y - 32, 78, 28), Tx.t("ui.training_sect.buy") % int(nd.get("cost", 0)), "node", str(b.id), true, why == "", why, 14)

func on_action(id: String, _data) -> void:
	match id:
		"role": submit({"type": "set_sect_role", "role": str(_data)})
		"node": submit({"type": "buy_sect_node", "branch": str(_data)})
		"promote": submit({"type": "take_promotion_trial"})
		"shop": navigate.emit("shop", {"shop": str(c().training_sect.get("id", "jade_sect"))})
		"missions": navigate.emit("notice_board", {})
