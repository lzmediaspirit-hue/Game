extends Page
## Companions (S26): choose up to two active fellow disciples.

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
	for i in roster.size():
		var cid := str(roster[i])
		var d := ContentDB.entry("companions", cid)
		var cr := Rect2(r.position.x + 20 + i * 270, r.position.y + 20, 250, 404)
		panel(cr, "minor_panel", "selected" if active.has(cid) else "normal")
		_portrait(cid, d).position = cr.position + Vector2(cr.size.x * 0.5, 220)
		text(cr.position + Vector2(0, 250), str(d.get("name", cid)), 24, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		text(cr.position + Vector2(0, 278), "%s · %s" % [str(d.get("role", "")).capitalize(), str(d.get("element", "")).capitalize()], 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		var bond := float(ch.companions.get("bond", {}).get(cid, 0.0))
		text(cr.position + Vector2(0, 300), Tx.t("ui.companions.bond") % [int(bond), Tx.t("ui.companions.downed") if ch.companions.get("downed", {}).has(cid) else Tx.t("ui.companions.ready")], 15, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		btn(Rect2(cr.position.x + 30, cr.end.y - 64, 190, 50), Tx.t("ui.companions.active") if active.has(cid) else Tx.t("ui.companions.bring_along"), "toggle", cid, active.has(cid))

func on_action(id: String, data) -> void:
	if id != "toggle": return
	var active: Array = c().companions.get("active", []).duplicate()
	if active.has(data): active.erase(data)
	else:
		active.append(data)
		while active.size() > 2: active.pop_front()
	submit({"type": "set_active_companions", "ids": active})
