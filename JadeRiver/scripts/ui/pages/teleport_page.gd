extends Page
## Teleport stones (S17): discovered stones cost a Spirit Stone shard each.

func _init() -> void:
	title = Tx.t("ui.teleport.teleport_stones")
	modal = true
	frame_rect = Rect2(300, 72, 680, 576)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var stones: Array = ContentDB.all("teleport_stones")
	var y := content.position.y + 6
	text(Vector2(content.position.x, y + 20), Tx.t("ui.teleport.shards") % ch.inventory.count("spirit_stone_shard"), 20, UiKit.MIST)
	y += 36
	# B7: full-height buttons in a scrolling list, however many stones there are (they were squeezed to 27 px).
	list("stones", Rect2(content.position.x, y, content.size.x, content.end.y - y), stones.size(), 58, func(i: int, rr: Rect2):
		var s: Dictionary = stones[i]
		var known: bool = Game.account.teleports.has(str(s.id))
		var here: bool = Game.room_rt != null and Game.room_rt.room_id == str(s.room)
		var ok := known and not here and Unlocks.is_unlocked(ch.id, "teleport_stones")
		var why := Tx.t("ui.teleport.not_yet_discovered") if not known else (Tx.t("ui.teleport.you_are_here") if here else Unlocks.locked_text("teleport_stones"))
		var fee: int = Game.world.teleport_fee(str(s.id), Game.active())
		btn(rr, Tx.plural("ui.teleport.shard", fee) % [str(s.name) if known else Tx.t("ui.teleport.undiscovered"), fee], "go", str(s.id), false, ok, why)
	)

func on_action(id: String, data) -> void:
	if id == "go":
		if submit({"type": "teleport", "stone": str(data)}).get("ok", false): close()
