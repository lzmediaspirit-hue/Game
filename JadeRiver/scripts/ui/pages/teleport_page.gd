extends Page
## Teleport stones (S17): discovered stones cost a Spirit Stone shard each.

func _init() -> void:
	title = "Teleport Stones"
	modal = true
	frame_rect = Rect2(300, 110, 680, 500)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var stones: Array = ContentDB.all("teleport_stones")
	var y := content.position.y + 6
	text(Vector2(content.position.x, y + 20), "Shards: %d" % ch.inventory.count("spirit_stone_shard"), 19, UiKit.MIST)
	y += 36
	for s in stones:
		var known: bool = Game.account.teleports.has(str(s.id))
		var here: bool = Game.room_rt != null and Game.room_rt.room_id == str(s.room)
		var ok := known and not here and Unlocks.is_unlocked(ch.id, "teleport_stones")
		var why := "Not yet discovered" if not known else ("You are here" if here else Unlocks.locked_text("teleport_stones"))
		btn(Rect2(content.position.x, y, content.size.x, 58), "%s  ·  %d shard" % [str(s.name) if known else "Undiscovered", int(s.get("fee_shards", 1))], "go", str(s.id), false, ok, why)
		y += 66

func on_action(id: String, data) -> void:
	if id == "go":
		if submit({"type": "teleport", "stone": str(data)}).get("ok", false): close()
