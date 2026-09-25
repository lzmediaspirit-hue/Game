extends Page
## Shared storage (S23): account-wide chest, 40 slots plus the Treasury bonus.

func _init() -> void:
	title = Tx.t("ui.storage.storage")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var items: Array = Game.account.storage.get("items", [])
	var bag: Array = ch.inventory.bag
	var left := Rect2(content.position.x, content.position.y, content.size.x * 0.5 - 10, content.size.y)
	var right := Rect2(left.end.x + 20, content.position.y, left.size.x, content.size.y)
	panel(left)
	panel(right)
	text(left.position + Vector2(20, 34), Tx.t("ui.storage.your_gourd_tap_to_store"), 20, UiKit.GOLD)
	text(right.position + Vector2(20, 34), Tx.t("ui.storage.shared_storage_tap_to_take") % [items.size(), Game.accounts.storage_size()], 20, UiKit.GOLD)
	_grid(Rect2(left.position + Vector2(10, 50), left.size - Vector2(20, 60)), "bag", bag.size(), func(i): return bag[i], "deposit")
	_grid(Rect2(right.position + Vector2(10, 50), right.size - Vector2(20, 60)), "store", items.size(), func(i): return items[i], "withdraw")

func _grid(r: Rect2, area: String, n: int, getter: Callable, action: String) -> void:
	var cols := 7
	list(area, r, int(ceil(n / float(cols))), 70, func(row: int, rr: Rect2):
		for col in cols:
			var i := row * cols + col
			if i >= n: break
			var s = getter.call(i)
			var sr := Rect2(rr.position.x + col * 72, rr.position.y, 64, 64)
			if s == null: draw_style_box(UiKit.style("slot"), sr)
			else: slot_box(sr, str(s.id), int(s.get("count", 1)), str(s.get("quality", "")), action, i)
	)

func on_action(id: String, data) -> void:
	match id:
		"deposit": submit({"type": "deposit", "index": int(data), "count": 999})
		"withdraw": submit({"type": "withdraw", "index": int(data)})
