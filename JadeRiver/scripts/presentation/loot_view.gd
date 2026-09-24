class_name LootView
extends Node2D
## Ground loot (S32, Part 9.7): items bounce, glow by quality and show a short
## label; Fine and better always show a beam. Auto-pickup is the World authority's.

var uid := 0
var t := 0.0
var item := ""
var coins := 0
var quality := "common"
var count := 1

func setup(entry: Dictionary) -> void:
	uid = int(entry.uid)
	item = str(entry.item)
	coins = int(entry.coins)
	count = int(entry.count)
	quality = str(entry.get("quality", "common"))
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	position = Vector2(float(entry.x), float(entry.y) - float(entry.get("alt", 0.0)))
	z_index = 1500 + int(float(entry.y))

func _process(delta: float) -> void:
	t += delta
	var rt: RoomRuntime = Game.room_rt
	var alive := false
	if rt:
		for l in rt.loot:
			if int(l.uid) == uid:
				alive = true
				count = int(l.count)
				break
	if not alive:
		queue_free()
		return
	queue_redraw()

func _draw() -> void:
	var bounce := 0.0
	if t < 0.5: bounce = -absf(sin(t * TAU)) * 36.0 * (1.0 - t * 2.0)
	var y := bounce + sin(t * 2.5) * 2.0 - 6.0
	var col := UiKit.quality_color(quality) if coins == 0 else UiKit.PALE_GOLD
	var fine := quality in ["fine", "superior", "perfect", "relic"]
	if fine:
		for i in 3:
			draw_rect(Rect2(-3 + i, -120 + y, 6 - i * 2, 110), Color(col, 0.12 + 0.05 * i))
	draw_set_transform(Vector2(0, 0), 0.0, Vector2(1, 0.3))
	draw_circle(Vector2.ZERO, 12, Color(0, 0, 0, 0.3))
	draw_set_transform(Vector2.ZERO)
	var ic: Texture2D = SpriteCache.icon("coin" if coins > 0 else item)
	if ic:
		draw_texture_rect(ic, Rect2(-16, -30 + y, 32, 32), false)
	else:
		draw_circle(Vector2(0, -14 + y), 8, col)
	var c = Game.active()
	var st: ActorState = Game.actor_state(c.id) if c else null
	if st and (fine or st.plane.distance_to(Vector2(position.x, position.y)) < 160.0):
		var text := ("%d taels" % coins) if coins > 0 else ContentDB.item_name(item) + (" ×%d" % count if count > 1 else "")
		UiKit.draw_outlined(self, text, Vector2(-100, -40 + y), 14, col, HORIZONTAL_ALIGNMENT_CENTER, 200)
