extends Page
## Companions (S26): choose up to two active fellow disciples. S49: their hearts, gifts, a friendly duel at 3 hearts,
## sworn siblings at 4 and a Dao Companion at 5.
## P5 (docs/page_identity.md row 27, the Bonds family; no mockup, drawn from its row): moon gates in a whitewashed
## garden wall, a friend standing in each. The wall under its coping of jade tiles; each companion full-length in a round
## gate with the garden beyond; the two beside you with their lanterns lit over their gates; each friend's hearts tied
## as knots on the red thread along the wall beneath the gates; the chosen friend's actions under their gate. Choosing
## to bring a friend along lights their lantern (0.2 s); a new heart ties its knot (0.3 s); under Reduce motion the
## lantern is lit and the knot is tied.


const GATE_Y := 272.0        # the gates' centres
const GATE_R := 110.0
const THREAD_Y := 466.0
const COLUMN := 256.0        # the chosen friend's actions under their gate
const TOP_SCALE := 4          # decision 42: a friend as the game draws them (TopdownDoll), screen px an art px
const LIGHT_S := 0.2
const TIE_S := 0.3

var avatars: Dictionary = {}   # companion id -> the figure standing in its gate
var chosen := ""
var lit_at := {}               # companion id -> when their lantern was lit here
var tie_at := {}               # companion id -> when their newest knot was tied here
var hearts_seen := {}          # companion id -> hearts when last drawn

func _init() -> void:
	title = Tx.t("ui.companions.companions")
	identity = Identity.new("plaster", false, "own", "moon_gates_in_wall", 0.3)

func content_rect() -> Rect2:
	return Rect2(80, 100, 1120, 580)

func draw_surface(r: Rect2) -> void:
	BondsKit.wall(self, r)

func title_rect() -> Rect2:
	return Rect2(96, 38, 320, 48)

## The title on a red lacquer board set into the coping, framed in gold.
func draw_title_mount(r: Rect2) -> void:
	rounded(r.grow(3), 6.0, UiKit.INK)
	rounded(r.grow(1), 5.0, UiKit.GOLD)
	rounded(r, 4.0, UiKit.SURFACE.lacquer)

func _portrait(cid: String, def: Dictionary) -> Node2D:
	if avatars.has(cid) and is_instance_valid(avatars[cid]): return avatars[cid]
	# Decision 42: each friend as the game draws them, three-quarters toward the camera.
	var a := Figures.for_outfit(DialoguePageScript.full_outfit(def.get("outfit", {})), TOP_SCALE)
	a.set("facing", 1)
	add_child(a)
	a.play("idle")
	avatars[cid] = a
	return a

const DialoguePageScript = preload("res://scripts/ui/pages/dialogue_page.gd")

## Where gate `i` of `n` stands: evenly along the wall.
func _gate(i: int, n: int) -> Vector2:
	return Vector2(frame_rect.position.x + frame_rect.size.x * (i + 0.5) / float(n), GATE_Y)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var roster: Array = ch.companions.get("roster", [])
	var active: Array = ch.companions.get("active", [])
	# Decision 43: a tour's anchors (the moon gates, the red thread of hearts under them).
	tour_mark("gates", Rect2(frame_rect.position.x + 24, GATE_Y - GATE_R - 16, frame_rect.size.x - 48, GATE_R * 2.0 + 32))
	tour_mark("thread", Rect2(frame_rect.position.x + 24, THREAD_Y - 24, frame_rect.size.x - 48, 48))
	if roster.is_empty():
		for i in 3: _moon_gate(_gate(i, 3), false)
		para(Rect2(frame_rect.position.x + 200, 440, frame_rect.size.x - 400, 80), Tx.t("ui.companions.fellow_disciples_join_you_from"), 22, BondsKit.INK, 3)
		return
	if chosen == "" or not roster.has(chosen): chosen = str(active[0]) if not active.is_empty() else str(roster[0])
	var n := mini(roster.size(), 4)
	for i in n:
		var cid := str(roster[i])
		var d := ContentDB.entry("companions", cid)
		var at := _gate(i, n)
		_moon_gate(at, cid == chosen)
		_portrait(cid, d).position = at + Vector2(0, GATE_R - 16)
		var lit: bool = active.has(cid)
		var glow_k := 1.0 if UiKit.reduce_motion() else clampf((t - float(lit_at.get(cid, -INF))) / LIGHT_S, 0.0, 1.0)
		BondsKit.lantern(self, Vector2(at.x, 92), lit, glow_k if lit else 0.0)
		region(Rect2(at - Vector2(GATE_R, GATE_R), Vector2(GATE_R * 2.0, GATE_R * 2.0 + 72.0)), "pick", cid)
		text(Vector2(at.x - COLUMN * 0.5, 420), str(d.get("name", cid)), 26, BondsKit.INK, HORIZONTAL_ALIGNMENT_CENTER, COLUMN, true)
		text(Vector2(at.x - COLUMN * 0.5, 444), "%s · %s" % [str(d.get("role", "")).capitalize(), str(d.get("element", "")).capitalize()], 16, BondsKit.SOFT_INK,
			HORIZONTAL_ALIGNMENT_CENTER, COLUMN)
		_hearts(ch, cid, at)
		if cid == chosen: _actions(ch, cid, at, active)
		else: _state(ch, cid, at)

## A moon gate: the round opening through the wall with the garden beyond (sky, a far hedge, the lawn and bamboo at its
## sides), framed by a ring of grey stone set in the plaster and a threshold stone at its foot; the chosen one's ring
## is gilded.
func _moon_gate(c: Vector2, lit: bool) -> void:
	var r := GATE_R
	_disc_band(c, r, c.y - r, c.y + 14.0, UiKit.MIST.lerp(UiKit.PAPER, 0.4))
	_disc_band(c, r, c.y + 14.0, c.y + 44.0, UiKit.JADE_SHADOW.lerp(UiKit.MIST, 0.45))
	_disc_band(c, r, c.y + 44.0, c.y + r, UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.3))
	for dx in [-74.0, -60.0, 62.0, 78.0]:
		var top := c.y - sqrt(maxf(0.0, r * r - dx * dx)) + 10.0
		draw_line(Vector2(c.x + dx, top), Vector2(c.x + dx, c.y + 50.0), UiKit.JADE_SHADOW, 3.0, true)
		for k in 3:
			var ly := top + 18.0 + k * 22.0
			draw_line(Vector2(c.x + dx, ly), Vector2(c.x + dx + signf(dx) * 12.0, ly - 6.0), UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.4), 2.0, true)
	draw_arc(c, r + 7.0, 0.0, TAU, 72, UiKit.INK, 16.0, true)
	draw_arc(c, r + 7.0, 0.0, TAU, 72, UiKit.GOLD if lit else UiKit.SURFACE.stone.lerp(UiKit.PAPER, 0.45), 12.0, true)
	for k in 12:   # the ring's joints
		var dir := Vector2.from_angle(k * TAU / 12.0)
		draw_line(c + dir * (r + 1.5), c + dir * (r + 12.5), Color(UiKit.INK, 0.35), 1.5, true)
	rounded(Rect2(c.x - 50, c.y + r - 6, 100, 12), 3.0, UiKit.SURFACE.stone.lerp(UiKit.PAPER, 0.3))

## The part of the disc at `c` (radius `r`) between y0 and y1, filled.
func _disc_band(c: Vector2, r: float, y0: float, y1: float, col: Color) -> void:
	var left := PackedVector2Array()
	var right := PackedVector2Array()
	for i in 13:
		var y := lerpf(y0, y1, float(i) / 12.0)
		var half := sqrt(maxf(0.0, r * r - (y - c.y) * (y - c.y)))
		left.append(Vector2(c.x - half, y))
		right.append(Vector2(c.x + half, y))
	right.reverse()
	draw_colored_polygon(left + right, col)

## A friend's hearts as knots tied on the stretch of red thread under their gate, the newest tied as it comes.
func _hearts(ch, cid: String, at: Vector2) -> void:
	var h: int = ch.relations.hearts_of(cid)
	if hearts_seen.has(cid) and h > int(hearts_seen[cid]): tie_at[cid] = t
	hearts_seen[cid] = h
	var a := Vector2(at.x - COLUMN * 0.5, THREAD_Y)
	var b := Vector2(at.x + COLUMN * 0.5, THREAD_Y)
	var k := unfold()
	BondsKit.thread(self, a, a.lerp(b, k), BondsKit.THREAD, 8.0 * k)
	for x in [a, b]: draw_circle(x, 4.0, UiKit.BRONZE, true, -1.0, true)
	var top := int(Game.relations.acfg().get("max_hearts", 5))
	for i in top:
		var p := BondsKit.on_thread(a, b, 8.0, 0.2 + 0.6 * i / float(top - 1))
		if p.x > a.lerp(b, k).x: break
		var tie := 1.0
		if i == h - 1 and tie_at.has(cid) and not UiKit.reduce_motion(): tie = clampf((t - float(tie_at[cid])) / TIE_S, 0.0, 1.0)
		BondsKit.knot(self, p, i < h, tie)

## A friend who is not chosen: how they stand (ready, downed, or the bond they hold), under the thread.
func _state(ch, cid: String, at: Vector2) -> void:
	var s := _standing(ch, cid)
	text(Vector2(at.x - COLUMN * 0.5, 506), s[0], 16, s[1], HORIZONTAL_ALIGNMENT_CENTER, COLUMN)

func _standing(ch, cid: String) -> Array:
	if str(ch.relations.bonds.get("dao_companion", "")) == cid: return [Tx.t("ui.relations.bond_dao_companion"), UiKit.JADE_SHADOW]
	if (ch.relations.bonds.get("sworn", []) as Array).has(cid): return [Tx.t("ui.companions.sworn"), UiKit.JADE_SHADOW]
	if ch.companions.get("downed", {}).has(cid): return [Tx.t("ui.companions.downed"), UiKit.BLOOD]
	return [Tx.t("ui.companions.ready"), BondsKit.SOFT_INK]

## The chosen friend's actions under their gate: bring them along (or leave them), a gift, a friendly duel at three
## hearts, and the bond their hearts open (or what the bond gives, once sworn).
func _actions(ch, cid: String, at: Vector2, active: Array) -> void:
	var x := at.x - COLUMN * 0.5
	var y := 486.0
	var dao := str(ch.relations.bonds.get("dao_companion", ""))
	var sworn: Array = ch.relations.bonds.get("sworn", [])
	var h: int = ch.relations.hearts_of(cid)
	var duel_h := int(Game.relations.acfg().get("duel_hearts", 3))
	var sworn_h := int(ContentDB.entry("bonds", "sworn").get("hearts", 4))
	var dao_h := int(ContentDB.entry("bonds", "dao_companion").get("hearts", 5))
	var s := _standing(ch, cid)
	text(Vector2(x, y + 20), s[0], 16, s[1], HORIZONTAL_ALIGNMENT_CENTER, COLUMN)
	y += 30
	btn(Rect2(x, y, COLUMN, 48), Tx.t("ui.companions.active") if active.has(cid) else Tx.t("ui.companions.bring_along"), "toggle", cid, active.has(cid), true, "", 20)
	y += 56
	var bw := (COLUMN - 8.0) / 2.0
	btn(Rect2(x, y, bw, 48), Tx.t("ui.companions.gift"), "gift", cid, false, true, "", 18)
	btn(Rect2(x + bw + 8, y, bw, 48), Tx.t("ui.companions.duel"), "duel", cid, false, h >= duel_h, Tx.plural("ui.companions.need_hearts", duel_h) % duel_h, 18)
	y += 56
	if dao == cid or sworn.has(cid):
		para(Rect2(x, y, COLUMN, 44), Tx.t("ui.companions.dao_note") if dao == cid else Tx.t("ui.companions.sworn_note"), 14, BondsKit.INK, 2)
	elif h >= dao_h and dao == "":
		btn(Rect2(x, y, COLUMN, 48), Tx.t("ui.companions.ask_dao"), "bond", ["dao_companion", cid], true, true, "", 18)
	else:
		var full := sworn.size() >= int(ContentDB.entry("bonds", "sworn").get("max", 3))
		btn(Rect2(x, y, COLUMN, 48), Tx.t("ui.companions.swear"), "bond", ["sworn", cid], false, h >= sworn_h and not full,
			Tx.t("ui.companions.sworn_full") if full else Tx.plural("ui.companions.need_hearts", sworn_h) % sworn_h, 18)

func on_action(id: String, data) -> void:
	match id:
		"pick":
			chosen = str(data)
			return
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
	if submit({"type": "set_active_companions", "ids": active}).get("ok", false) and active.has(data): lit_at[str(data)] = t
