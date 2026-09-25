extends Page
## Companions (S26): choose up to two active fellow disciples. S49: their hearts, gifts, a friendly duel at 3 hearts,
## sworn siblings at 4 and a Dao Companion at 5.

const Avatar = preload("res://scripts/avatar.gd")

var avatars: Dictionary = {}   # companion id -> Avatar portrait

func _init() -> void:
	title = Tx.t("ui.companions.companions")

func _portrait(cid: String, def: Dictionary) -> Node2D:
	if avatars.has(cid) and is_instance_valid(avatars[cid]): return avatars[cid]
	var a = Avatar.new()
	var o: Dictionary = def.get("outfit", {}).duplicate()
	for k in ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]:
		if not o.has(k): o[k] = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "boots"}.get(k, "none")
	if not o.has("hair_color"): o.hair_color = 0
	a.outfit = o
	a.scale = Vector2.ONE * 1.3
	a.facing = 1
	add_child(a)
	a.play("idle")
	avatars[cid] = a
	return a

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var roster: Array = ch.companions.get("roster", [])
	var active: Array = ch.companions.get("active", [])
	var r := Rect2(content.position, content.size)
	panel(r)
	if roster.is_empty():
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.companions.fellow_disciples_join_you_from"), 21, UiKit.MIST)
		return
	var dao := str(ch.relations.bonds.get("dao_companion", ""))
	var sworn: Array = ch.relations.bonds.get("sworn", [])
	var duel_h := int(Game.relations.acfg().get("duel_hearts", 3))
	var sworn_h := int(ContentDB.entry("bonds", "sworn").get("hearts", 4))
	var dao_h := int(ContentDB.entry("bonds", "dao_companion").get("hearts", 5))
	for i in roster.size():
		var cid := str(roster[i])
		var d := ContentDB.entry("companions", cid)
		var cr := Rect2(r.position.x + 20 + i * 270, r.position.y + 16, 250, r.size.y - 32)
		panel(cr, "minor_panel", "selected" if active.has(cid) else "normal")
		_portrait(cid, d).position = cr.position + Vector2(cr.size.x * 0.5, 196)
		text(cr.position + Vector2(0, 232), str(d.get("name", cid)), 24, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		text(cr.position + Vector2(0, 258), "%s · %s" % [str(d.get("role", "")).capitalize(), str(d.get("element", "")).capitalize()], 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		# S49: hearts, and the bond if one is sworn.
		var h: int = ch.relations.hearts_of(cid)
		UiKit.draw_hearts(self, Vector2(cr.get_center().x - 61, cr.position.y + 280), h, 5, 10.0)
		var tag := Tx.t("ui.companions.downed") if ch.companions.get("downed", {}).has(cid) else Tx.t("ui.companions.ready")
		if dao == cid: tag = Tx.t("ui.relations.bond_dao_companion")
		elif sworn.has(cid): tag = Tx.t("ui.companions.sworn")
		text(cr.position + Vector2(0, 314), tag, 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		var bx := cr.position.x + 14
		var bw := (cr.size.x - 28 - 8) / 2.0
		var y := cr.position.y + 330
		btn(Rect2(bx, y, bw, 46), Tx.t("ui.companions.gift"), "gift", cid, false, true, "", 17)
		btn(Rect2(bx + bw + 8, y, bw, 46), Tx.t("ui.companions.duel"), "duel", cid, false, h >= duel_h, Tx.t("ui.companions.need_hearts") % duel_h, 17)
		y += 54
		if dao == cid or sworn.has(cid):
			para(Rect2(bx, y + 2, cr.size.x - 28, 46), Tx.t("ui.companions.dao_note") if dao == cid else Tx.t("ui.companions.sworn_note"), 14, UiKit.MIST, 2)
		elif h >= dao_h and dao == "":
			btn(Rect2(bx, y, cr.size.x - 28, 46), Tx.t("ui.companions.ask_dao"), "bond", ["dao_companion", cid], true, true, "", 17)
		else:
			var full := sworn.size() >= int(ContentDB.entry("bonds", "sworn").get("max", 3))
			btn(Rect2(bx, y, cr.size.x - 28, 46), Tx.t("ui.companions.swear"), "bond", ["sworn", cid], false, h >= sworn_h and not full,
				Tx.t("ui.companions.sworn_full") if full else Tx.t("ui.companions.need_hearts") % sworn_h, 17)
		btn(Rect2(bx, cr.end.y - 60, cr.size.x - 28, 48), Tx.t("ui.companions.active") if active.has(cid) else Tx.t("ui.companions.bring_along"), "toggle", cid, active.has(cid))

func on_action(id: String, data) -> void:
	match id:
		"gift":
			navigate.emit("gift", {"npc": str(data)})
			return
		"duel":
			if submit({"type": "companion_duel", "companion": str(data)}).get("ok", false): close()
			return
		"bond":
			var r := submit({"type": "offer_bond", "kind": str(data[0]), "npc": str(data[1])})
			if not r.get("ok", false): queue_redraw()
			return
	if id != "toggle": return
	var active: Array = c().companions.get("active", []).duplicate()
	if active.has(data): active.erase(data)
	else:
		active.append(data)
		while active.size() > 2: active.pop_front()
	submit({"type": "set_active_companions", "ids": active})
