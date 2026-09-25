extends Page
## Teleport stones (S17): discovered stones cost a Spirit Stone shard each.

func _init() -> void:
	title = Tx.t("ui.teleport.teleport_stones")
	modal = true
	frame_rect = Rect2(300, 110, 680, 500)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var stones: Array = ContentDB.all("teleport_stones")
	var y := content.position.y + 6
	var gap := minf(66.0, (content.size.y - 42.0) / maxf(1.0, stones.size()))
	text(Vector2(content.position.x, y + 20), Tx.t("ui.teleport.shards") % ch.inventory.count("spirit_stone_shard"), 19, UiKit.MIST)
	y += 36
	for s in stones:
		var known: bool = Game.account.teleports.has(str(s.id))
		var here: bool = Game.room_rt != null and Game.room_rt.room_id == str(s.room)
		var ok := known and not here and Unlocks.is_unlocked(ch.id, "teleport_stones")
		var why := Tx.t("ui.teleport.not_yet_discovered") if not known else (Tx.t("ui.teleport.you_are_here") if here else Unlocks.locked_text("teleport_stones"))
		btn(Rect2(content.position.x, y, content.size.x, gap - 8.0), Tx.t("ui.teleport.shard") % [str(s.name) if known else Tx.t("ui.teleport.undiscovered"), Game.world.teleport_fee(str(s.id), Game.active())], "go", str(s.id), false, ok, why)
		y += gap

func on_action(id: String, data) -> void:
	if id == "go":
		if submit({"type": "teleport", "stone": str(data)}).get("ok", false): close()
