class_name LootView
extends Node2D
## Ground loot (S32, Part 9.7): items bounce, glow by quality and show a short
## label; Fine and better always show a beam. Auto-pickup is the World authority's.
## P6 moments: a boss's or a chest's drop can fly out in a fountain first (`launch`).

var uid := 0
var t := 0.0
var item := ""
var coins := 0
var quality := "common"
var count := 1
var fly := {}   # the loot fountain: {from (offset from its place), flight, apex, burst, chime}; t runs from -(wait + flight) to 0
var beam := {}  # a rare find's beam (P6 rare_drop): {height, width, hz}, until it is picked up
var ground := Vector2.ZERO   # where it lies on the plane (its position is lifted by its height)

func setup(entry: Dictionary) -> void:
	uid = int(entry.uid)
	item = str(entry.item)
	coins = int(entry.coins)
	count = int(entry.count)
	quality = str(entry.get("quality", "common"))
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ground = Vector2(float(entry.x), float(entry.y))
	position = Vector2(float(entry.x), float(entry.y) - float(entry.get("alt", 0.0)))
	z_index = 1500 + int(float(entry.y))

## P6 loot fountain: leave the drop point after `delay` and land on this spot after `flight` s, `apex` px up, then
## bounce as ever; `chime` sounds as it lands. A burst of coins flies as six.
func launch(from: Vector2, delay: float, apex: float, flight: float, chime := "") -> void:
	fly = {"from": from - position, "flight": flight, "apex": apex, "burst": coins > 0, "chime": chime}
	t = -(delay + flight)

func _process(delta: float) -> void:
	if t < 0.0 and t + delta >= 0.0 and str(fly.get("chime", "")) != "": Audio.play(str(fly.chime))
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
	if t < 0.0:
		_draw_flight()
		return
	var bounce := 0.0
	if t < 0.5: bounce = -absf(sin(t * TAU)) * 36.0 * (1.0 - t * 2.0)
	var y := bounce + sin(t * 2.5) * 2.0 - 6.0
	var col := UiKit.quality_color(quality) if coins == 0 else UiKit.PALE_GOLD
	var fine := quality in ["fine", "superior", "perfect", "relic"]
	if not beam.is_empty():
		# A rare find is seen from across the room: a tall column in its colour, breathing slowly.
		var bc := MomentRules.item_color({"item": item, "quality": quality})
		var pulse := 0.75 + 0.25 * sin(TAU * float(beam.hz) * t)
		var bw := float(beam.width)
		for i in 3:
			draw_rect(Rect2(-bw * 0.5 * (3 - i) / 3.0, -float(beam.height) + y, bw * (3 - i) / 3.0, float(beam.height) - 10.0), Color(bc, (0.14 + 0.1 * i) * pulse))
	elif fine:
		for i in 3:
			draw_rect(Rect2(-3 + i, -120 + y, 6 - i * 2, 110), Color(col, 0.12 + 0.05 * i))
	draw_set_transform(Vector2(0, 0), 0.0, Vector2(1, 0.3))
	draw_circle(Vector2.ZERO, 12, Color(0, 0, 0, 0.3))
	draw_set_transform(Vector2.ZERO)
	if SpriteCache.draw_icon(self, Rect2(-16, roundf(-30 + y), 32, 32), "coin" if coins > 0 else item) == Rect2():
		draw_circle(Vector2(0, -14 + y), 8, col)
	var c = Game.active()
	var st: ActorState = Game.actor_state(c.id) if c else null
	if st and (fine or st.plane.distance_to(ground) < 160.0):
		var text := (Tx.plural("view.taels", coins) % coins) if coins > 0 else ContentDB.item_name(item) + (" ×%d" % count if count > 1 else "")
		UiKit.draw_outlined(self, text, Vector2(-120, -40 + y), 16, col, HORIZONTAL_ALIGNMENT_CENTER, 240)

## In the fountain: nothing before it leaves, then the icon on its arc (a coin burst as six coins closing into one).
func _draw_flight() -> void:
	var u := 1.0 + t / float(fly.flight)
	if u < 0.0: return
	var at: Vector2 = Vector2(fly.from) * (1.0 - u) + Vector2(0, -4.0 * float(fly.apex) * u * (1.0 - u) - 20.0)
	for i in (6 if fly.burst else 1):
		var spread := Vector2.from_angle(TAU * i / 6.0) * 26.0 * (1.0 - u) if fly.burst else Vector2.ZERO
		SpriteCache.draw_icon(self, Rect2((at + spread - Vector2(16, 16)).round(), Vector2(32, 32)), "coin" if coins > 0 else item)
