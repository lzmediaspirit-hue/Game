extends Page
## Your own sect (S25): found it, build and upgrade, recruit NPC disciples and send
## expeditions. Timers run offline. S49 territory: the spirit-stone mines your sect holds or could take.
## P5 (docs/page_identity.md row 24, mockup 11): the courtyard under construction. The Courtyard tab is the Sect
## Grounds as they stand, drawn from the room's own backdrop and props: every building where the room places it, the
## raised ones solid and the rest as dashed bronze scaffolds, each tagged (its level, "to raise", or the sect level it
## waits for); your disciples in the yard and the day's candidates at the gate. Under it the sect's level with its
## prestige and the stops ahead (what each opens), then three cards: the building tapped (what it gives, what the next
## level costs, Build), the disciples (rooms, the candidates, Recruit) and what lies beyond the walls (Expeditions and
## Territory, one tap each). A building being raised fills its scaffold from the ground up; the disciples idle.

const SectKit = preload("res://scripts/ui/pages/sect_kit.gd")
const MapPage = preload("res://scripts/ui/pages/map_page.gd")

const ROOM := "hv_sect_grounds"
## The courtyard's painting inside the window, and how the room maps into it: across by one scale, and the floor's
## depth band (the room's y from DEPTH_BACK to DEPTH_FRONT) pressed into the painting's lowest DEPTH_PX.
const PANO := Rect2(92, 172, 1096, 224)
const DEPTH_BACK := 640.0
const DEPTH_FRONT := 900.0
const DEPTH_PX := 58.0
const HORIZON := 70.0      # the courtyard's back wall line, above the painting's foot
const LAYER_K := 0.5       # the backdrop's layers, halved
const CARD_Y := 470.0
const CARD_H := 194.0
const RAISE_S := 0.3       # a building begun fills its scaffold over this long
const GATE_X := 330.0      # where the day's candidates wait, inside the gate (room px)
const GATE_Y := 700.0

var name_field: LineEdit
var picked := "treasury"   # the building on the card
var cand := 0              # the candidate at the gate Recruit takes
var figs := {}
var raised_at := {}        # building id -> page time its raising began (its scaffold fills)

func _init() -> void:
	title = Tx.t("ui.your_sect.your_sect")
	tabs = [{"id": "hall", "label": Tx.t("ui.your_sect.courtyard")}, {"id": "expeditions", "label": Tx.t("ui.your_sect.expeditions")},
		{"id": "territory", "label": Tx.t("ui.your_sect.territory")}]
	identity = Identity.new("river_lacquer", true, "plaque", "courtyard_panorama_cards", 0.3)

func setup() -> void:
	if not Game.sect.founded():
		name_field = LineEdit.new()
		name_field.max_length = 20
		name_field.placeholder_text = Tx.t("ui.your_sect.sect_name")
		name_field.size = Vector2(400, 48)
		name_field.add_theme_font_override("font", UiKit.text_font())
		name_field.add_theme_font_size_override("font_size", 22)
		name_field.add_theme_stylebox_override("normal", UiKit.style("slot"))
		add_child(name_field)
	# The card opens on the first building that can be raised now, else the Sect Hall.
	picked = "sect_hall"
	if Game.sect.founded():
		for b in ContentDB.all("sect_buildings"):
			if Game.sect.level_building(str(b.id)) == 0 and int(Game.sect.sect().level) >= int(b.get("sect_level", 1)):
				picked = str(b.id)
				break

func draw_surface(r: Rect2) -> void:
	draw_rect(r.grow(-INSET * 0.5), Color(UiKit.SURFACE.river_lacquer, 0.6))
	ground(r, UiKit.SURFACE.river_lacquer)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var live := {}
	var r := Rect2(content.position, content.size)
	var s: Dictionary = Game.sect.sect()
	if s.is_empty():
		_courtyard(ch, {}, live)
		_founding(ch)
	else:
		match str(tabs[tab].id):
			"hall":
				_name_line(s)
				_courtyard(ch, s, live)
				_levels(s)
				_building_card(ch, s, Rect2(92, CARD_Y, 368, CARD_H))
				_disciples_card(s, Rect2(472, CARD_Y, 372, CARD_H))
				_beyond(s, Rect2(856, CARD_Y, 332, CARD_H))
			"expeditions":
				panel(r)
				text(r.position + Vector2(30, 44), Tx.t("ui.your_sect.level_prestige") % [str(s.name), int(s.level), UiKit.fmt(int(s.prestige))], 22, UiKit.PALE_GOLD)
				_draw_expeditions(r, s)
			"territory":
				panel(r)
				text(r.position + Vector2(30, 44), Tx.t("ui.your_sect.level_prestige") % [str(s.name), int(s.level), UiKit.fmt(int(s.prestige))], 22, UiKit.PALE_GOLD)
				_draw_territory(r, s)
	SectKit.hide_rest(figs, live if confirm.is_empty() else {})

## The sect's name and where it stands, at the right of the tabs.
func _name_line(s: Dictionary) -> void:
	var rid := str(ContentDB.room(ROOM).get("region", ""))
	var where := ContentDB.name_of("rooms", ROOM)
	for z in ContentDB.all("zones"):
		for rg in z.get("regions", []):
			if str(rg.get("id", "")) == rid: where = str(rg.get("name", where))
	var tail := " · %s" % where
	var right := PANO.end.x
	text(Vector2(right - UiKit.text_width(tail, 18), 144), tail, 18, UiKit.MIST)
	text(Vector2(right - UiKit.text_width(tail, 18) - 420, 144), str(s.name), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 420)

# ------------------------------------------------------------------ the courtyard
static func _k() -> float:
	return PANO.size.x / 2560.0

static func _x(x: float) -> float:
	return PANO.position.x + x * _k()

static func _foot(y: float) -> float:
	return PANO.end.y - 12.0 - (DEPTH_FRONT - clampf(y, DEPTH_BACK, DEPTH_FRONT)) * DEPTH_PX / (DEPTH_FRONT - DEPTH_BACK)

## Draw `tex` at `dst`, the part of it inside the painting only (its source cut to match).
func _blit(tex: Texture2D, dst: Rect2, modulate := Color.WHITE, src := Rect2()) -> void:
	if tex == null: return
	if src.size == Vector2.ZERO: src = Rect2(Vector2.ZERO, tex.get_size())
	var cut := dst.intersection(PANO)
	if cut.size.x <= 0.0 or cut.size.y <= 0.0: return
	var sx := src.size.x / dst.size.x
	var sy := src.size.y / dst.size.y
	draw_texture_rect_region(tex, cut, Rect2(src.position + (cut.position - dst.position) * Vector2(sx, sy), cut.size * Vector2(sx, sy)), modulate)

## Every building's props in the room: building id -> [{at, prop}] (the Sect Hall's pagoda and gate, the Treasury's
## storehouse, the terrace beds...).
static func placements() -> Dictionary:
	var out := {}
	for o in ContentDB.room(ROOM).get("objects", []):
		var bid := ""
		for cond in o.get("visible_if", {}).get("all", []):
			if str(cond.get("kind", "")) == "sect_building_at_least": bid = str(cond.building)
		if bid == "" or str(o.get("prop", "")) == "": continue
		if not out.has(bid): out[bid] = []
		out[bid].append({"at": Vector2(float(o.at[0]), float(o.at[1])), "prop": str(o.prop)})
	return out

## Where a prop stands in the painting.
static func prop_rect(prop: String, at: Vector2) -> Rect2:
	var e := SpriteCache.prop(prop)
	if e.is_empty(): return Rect2()
	var k := _k()
	return Rect2((Vector2(_x(at.x), _foot(at.y)) - Vector2(float(e.anchor[0]), float(e.anchor[1])) * k).round(), (Vector2(float(e.frame[0]), float(e.frame[1])) * k).round())

func _courtyard(ch, s: Dictionary, live: Dictionary) -> void:
	# The sky and the backdrop's layers, halved and tiled, behind the courtyard's wall.
	var bd: Dictionary = ContentDB.config("backdrops").get(str(ContentDB.room(ROOM).get("backdrop", "sect_jade")), {})
	var horizon := PANO.end.y - HORIZON
	vshade(Rect2(PANO.position, Vector2(PANO.size.x, horizon - PANO.position.y)), Color(str(bd.get("sky", UiKit.MIST.to_html()))), Color(str(bd.get("horizon", UiKit.PAPER.to_html()))))
	var layers: Array = bd.get("layers", [])
	for li in range(1, layers.size()):
		var l: Dictionary = layers[li]
		var tex := SectKit.scaled(SpriteCache.tex(str(l.file)), Rect2i(), LAYER_K)
		if tex == null: continue
		var w := tex.get_width()
		var bottom := horizon + (float(l.get("bottom", 720)) - 720.0) * 0.25 + 6.0
		var x := PANO.position.x - fmod(float(li) * 173.0, float(w))
		while x < PANO.end.x:
			_blit(tex, Rect2(x, bottom - tex.get_height(), w, tex.get_height()))
			x += w
	# The courtyard's stone floor, its paving lines receding.
	var yard := Rect2(PANO.position.x, horizon, PANO.size.x, PANO.end.y - horizon)
	vshade(yard, UiKit.SURFACE.stone.lerp(UiKit.SURFACE.sand, 0.35), UiKit.SURFACE.stone.lerp(UiKit.SURFACE.sand, 0.15))
	for i in 5:
		var y := horizon + 6.0 + i * i * 2.6
		draw_line(Vector2(yard.position.x, y), Vector2(yard.end.x, y), Color(UiKit.INK, 0.12), 1.0)
	draw_rect(Rect2(yard.position.x, horizon - 3, yard.size.x, 4), Color(UiKit.SURFACE.stone.lerp(UiKit.INK, 0.3), 0.9))
	# The buildings: raised ones solid, the rest as scaffolds where the room will place them.
	var place := placements()
	var now := Clock.now_utc()
	var tags: Array = []
	var ids: Array = ContentDB.all("sect_buildings").map(func(b): return str(b.id))
	for bid in ids:
		if not place.has(bid): continue
		var lv: int = Game.sect.level_building(bid) if not s.is_empty() else 0
		var q := _queued(s, bid)
		var fill := 1.0 if lv > 0 else 0.0
		if lv == 0 and not q.is_empty():
			var secs := float(Game.sect.building_cost(bid, int(q.level)).seconds)
			fill = clampf(1.0 - (float(q.done_utc) - now) / maxf(1.0, secs), 0.0, 1.0)
			if raised_at.has(bid): fill = minf(fill, (t - float(raised_at[bid])) / RAISE_S)
		var top := Rect2()
		for pl in place[bid]:
			var pr := prop_rect(str(pl.prop), pl.at)
			if pr.size == Vector2.ZERO: continue
			top = pr if top.size == Vector2.ZERO or pr.size.y > top.size.y else top
			_building(str(pl.prop), pr, fill, bid == picked)
			region(pr.intersection(PANO), "pick", bid)
		if top.size != Vector2.ZERO: tags.append({"id": bid, "rect": top, "lv": lv, "queued": not q.is_empty()})
	_tags(s, tags, _figures(s, live))

## The build in progress for `bid`, or {}.
static func _queued(s: Dictionary, bid: String) -> Dictionary:
	for q in s.get("queue", []):
		if str(q.building) == bid: return q
	return {}

## One prop: solid as far up as it is built (`fill`, 1 when raised), the rest a dashed bronze scaffold; the building on
## the card ringed in pale gold.
func _building(prop: String, pr: Rect2, fill: float, chosen: bool) -> void:
	var e := SpriteCache.prop(prop)
	var tex := SectKit.scaled(SpriteCache.tex(str(e.file)), Rect2i(0, 0, int(e.frame[0]), int(e.frame[1])), _k())
	var used := SectKit.used_rect(tex)
	var body := Rect2(pr.position + used.position, used.size) if used.size != Vector2.ZERO else pr
	if chosen:
		glow(body.grow(14), Color(UiKit.PALE_GOLD, 0.45 * _halo()))
	if fill < 1.0:
		# The building as it will stand, pale, inside its scaffold's dashed bronze outline.
		_blit(tex, pr, Color(1, 1, 1, 0.3))
		var sc := body.intersection(PANO.grow(-2))
		PostKit.dashed(self, PackedVector2Array([sc.position, Vector2(sc.end.x, sc.position.y), sc.end, Vector2(sc.position.x, sc.end.y), sc.position]), Color(UiKit.BRONZE, 0.8), 6.0)
	if fill > 0.0 and tex != null:
		var h := pr.size.y * fill
		_blit(tex, Rect2(pr.position.x, pr.end.y - h, pr.size.x, h), Color.WHITE, Rect2(0, tex.get_height() * (1.0 - fill), tex.get_width(), tex.get_height() * fill))
	if chosen:
		var ring := body.grow(4).intersection(PANO.grow(-2))
		PostKit.dashed(self, PackedVector2Array([ring.position, Vector2(ring.end.x, ring.position.y), ring.end, Vector2(ring.position.x, ring.end.y), ring.position]), UiKit.PALE_GOLD, 7.0)

## The tags over the buildings, placed by the World map's layout pass so none touches another: a raised one's level, one
## that can be raised now, or the sect level one waits for (with its lock).
func _tags(s: Dictionary, tags: Array, blocked: Array) -> void:
	var items: Array = []
	var words := {}
	for tg in tags:
		var b := ContentDB.entry("sect_buildings", str(tg.id))
		var need := int(b.get("sect_level", 1))
		var lvl := int(s.get("level", 0))
		var w := ""
		var kind := "lock"
		if bool(s.get("damaged", {}).get(str(tg.id), false)):
			w = Tx.t("ui.your_sect.tag_damaged") % str(b.name)
			kind = "hurt"
		elif int(tg.lv) > 0:
			w = Tx.t("ui.your_sect.tag_level") % [str(b.name), int(tg.lv)]
			kind = "built"
		elif bool(tg.queued):
			w = Tx.t("ui.your_sect.tag_raising") % str(b.name)
			kind = "can"
		elif not s.is_empty() and lvl >= need:
			w = Tx.t("ui.your_sect.tag_to_raise") % str(b.name)
			kind = "can"
		else:
			w = "%s  %d" % [str(b.name), need]
		var size := Vector2(UiKit.text_width(w, 14) + 18.0 + (14.0 if kind == "lock" else 0.0), 22)
		var top: Rect2 = tg.rect
		# A tag with no room at full length says the building's name alone.
		items.append({"id": str(tg.id), "at": Vector2(top.get_center().x, maxf(top.position.y + 4.0, PANO.position.y + 12.0)), "r": 2.0,
			"sizes": [size, Vector2(UiKit.text_width(str(b.name), 14) + 18.0, 22)], "ways": ["t", "ul", "ur", "b", "l", "r"]})
		words[str(tg.id)] = [w, kind, str(b.name)]
	var got := MapPage.place(items, blocked, PANO.grow(-4))
	var a := unfold()
	for id in got:
		var r: Rect2 = got[id].rect
		r.position.y -= (1.0 - a) * 8.0
		var kind := str(words[id][1])
		var edge: Color = {"built": UiKit.GOLD, "can": UiKit.BRIGHT_JADE, "hurt": UiKit.RED_TEXT}.get(kind, Color(UiKit.BRONZE, 0.6))
		rounded(r.grow(1), 7.0, edge)
		rounded(r, 6.0, UiKit.INK.lerp(UiKit.SURFACE.space, 0.4))
		ground(r, UiKit.INK.lerp(UiKit.SURFACE.space, 0.4))
		var col: Color = {"built": UiKit.PALE_GOLD, "can": UiKit.BRIGHT_JADE, "hurt": UiKit.RED_TEXT}.get(kind, UiKit.HOLLOW)
		var w := str(words[id][0]) if int(got[id].size) == 0 else str(words[id][2])
		if kind == "lock" and int(got[id].size) == 0:
			var name := w.left(w.rfind("  "))
			text(r.position + Vector2(9, 16), name, 14, col)
			var lx := r.position.x + 9.0 + UiKit.text_width(name, 14) + 4.0
			_lock_icon(Vector2(lx, r.position.y + 2), 0.85)
			text(Vector2(lx + 14, r.position.y + 16), w.substr(w.rfind("  ") + 2), 14, col)
		else:
			text(r.position + Vector2(9, 16), w, 14, col)
		region(r, "pick", id)

## Your disciples in the yard (those at home: not away on an expedition, not guarding a mine), and the day's candidates at
## the gate with how many ask to join. A tap on a candidate makes them the one Recruit takes. Returns where they and
## their words stand, so no tag is placed over them.
func _figures(s: Dictionary, live: Dictionary) -> Array:
	var taken: Array = []
	if s.is_empty(): return taken
	var busy := Game.sect.guarding()
	var ds: Array = s.get("disciples", [])
	var home := 0
	for i in ds.size():
		if busy.has(i) or Game.sect._on_expedition(i): continue
		var x := 760.0 + home * 80.0
		var feet := Vector2(_x(x), _foot(740.0 + (home % 2) * 50.0))
		var key := "d%d" % i
		SectKit.show(SectKit.figure(self, figs, key, SectKit.disciple_outfit(str(ds[i].get("name", ""))), 0.5), feet, live, key, 1.0, "idle", 1 if home % 2 == 0 else -1)
		inked(feet + Vector2(-40, 18), str(ds[i].get("name", "")), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 80, false)
		taken.append(Rect2(feet - Vector2(20, 46), Vector2(40, 68)))
		home += 1
	var cands: Array = s.get("candidates", [])
	for i in cands.size():
		var feet := Vector2(_x(GATE_X + i * 60.0), _foot(GATE_Y))
		var key := "c%d_%s" % [i, str(cands[i].get("name", ""))]
		SectKit.show(SectKit.figure(self, figs, key, SectKit.disciple_outfit(str(cands[i].get("name", "")) + "*"), 0.5), feet, live, key, 1.0 if i == cand else 0.8, "idle", -1)
		if i == cand: draw_arc(feet + Vector2(0, -2), 14.0, 0.0, TAU, 20, Color(UiKit.BRIGHT_JADE, 0.8), 2.0, true)
		region(Rect2(feet - Vector2(16, 40), Vector2(32, 44)), "cand", i)
		taken.append(Rect2(feet - Vector2(18, 46), Vector2(36, 52)))
	if not cands.is_empty():
		var at := Vector2(_x(GATE_X + cands.size() * 60.0) - 8, _foot(GATE_Y) - 8)
		var words := Tx.plural("ui.your_sect.ask_to_join", cands.size()) % cands.size()
		UiKit.new_mark(self, at + Vector2(0, -6))
		inked(at + Vector2(12, 0), words, 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, -1, false)
		taken.append(Rect2(at + Vector2(-8, -16), Vector2(UiKit.text_width(words, 14) + 24, 22)))
	return taken

# ------------------------------------------------------------------ the sect's level
## The sect level and prestige, the bar to three levels ahead with a stop at each, and what each stop opens.
func _levels(s: Dictionary) -> void:
	var lvl := int(s.level)
	var y := PANO.end.y + 8.0
	text(Vector2(PANO.position.x + 2, y + 18), Tx.t("ui.your_sect.level_line") % [lvl, UiKit.fmt(int(s.prestige))], 16, UiKit.PAPER)
	text(Vector2(PANO.position.x + 2, y + 42), Tx.t("ui.your_sect.prestige_each") % int(ContentDB.config("sect_levels").get("prestige_building", 20)), 14, UiKit.MIST)
	var bar_r := Rect2(300, y, PANO.end.x - 300, 24)
	var stops: Array = []
	for L in range(lvl + 1, mini(lvl + 4, 21)): stops.append(L)
	if stops.is_empty():
		bar(bar_r, 1.0, UiKit.JADE)
		return
	var lo := 0.0 if lvl <= 1 else Game.sect.prestige_for(lvl)
	var hi := Game.sect.prestige_for(int(stops.back()))
	var span := maxf(1.0, hi - lo)
	bar(bar_r, (float(s.prestige) - lo) / span, UiKit.JADE)
	var inner := bar_r.grow_individual(-6, 0, -6, 0)
	var prev_x := PANO.position.x + 200.0
	for i in stops.size():
		var L: int = stops[i]
		var at := Game.sect.prestige_for(L)
		var x := inner.position.x + inner.size.x * (at - lo) / span
		var d := 7.0
		var c := Vector2(x, bar_r.position.y + 2)
		draw_colored_polygon(PackedVector2Array([c + Vector2(0, -d), c + Vector2(d, 0), c + Vector2(0, d), c + Vector2(-d, 0)]), UiKit.INK)
		draw_colored_polygon(PackedVector2Array([c + Vector2(0, -d + 2), c + Vector2(d - 2, 0), c + Vector2(0, d - 2), c + Vector2(-d + 2, 0)]), UiKit.PALE_GOLD if i == 0 else UiKit.MIST)
		var opens: Array = ContentDB.all("sect_buildings").filter(func(b): return int(b.get("sect_level", 1)) == L).map(func(b): return str(b.name))
		var words := Tx.t("ui.your_sect.stop") % [L, UiKit.fmt(ceili(at))] + (": " + ", ".join(opens) if not opens.is_empty() else "")
		var last := i == stops.size() - 1
		var room := x - prev_x - 12.0
		var ww := minf(UiKit.text_width(words, 14), room)
		var lx := x - ww if last else clampf(x - ww * 0.5, prev_x + 12.0, x + 100.0)
		text(Vector2(lx, y + 42), words, 14, UiKit.PALE_GOLD if i == 0 else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, ww)
		prev_x = lx + ww

# ------------------------------------------------------------------ the cards
## The building on the card: what it gives, its level, what the next level costs and whether it can be raised now.
func _building_card(ch, s: Dictionary, r: Rect2) -> void:
	panel(r)
	var b := ContentDB.entry("sect_buildings", picked)
	var lv := Game.sect.level_building(picked)
	var top := int(b.get("max_level", 5))
	var q := _queued(s, picked)
	var hurt: bool = s.get("damaged", {}).has(picked)
	text(r.position + Vector2(16, 30), str(b.get("name", picked)), 22, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 180, true)
	var status := Tx.t("ui.your_sect.not_raised") % int(b.get("sect_level", 1)) if lv == 0 else Tx.t("ui.your_sect.level_of") % [lv, top]
	if not q.is_empty(): status = Tx.t("ui.your_sect.raising_left") % UiKit.span(float(q.done_utc) - Clock.now_utc())
	text(Vector2(r.position.x + 16, r.position.y + 28), status, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 32)
	para(Rect2(r.position + Vector2(16, 40), Vector2(r.size.x - 32, 44)), Tx.t("ui.your_sect.damaged_in_a_raid_output") if hurt else _effect(picked, lv), 16, UiKit.RED_TEXT if hurt else UiKit.PAPER, 2)
	var by := r.end.y - 56.0
	if hurt:
		btn(Rect2(r.position.x + 16, by, 150, BTN_H), Tx.t("ui.your_sect.repair"), "repair", picked, true)
	elif lv < top:
		var cost: Dictionary = Game.sect.building_cost(picked, lv + 1)
		var x := r.position.x + 16.0
		var cy := r.position.y + 86.0
		icon_at(Rect2(x, cy, 32, 32), "coin")
		text(Vector2(x + 36, cy + 23), UiKit.fmt(int(cost.get("silver_tael", 0))), 18, UiKit.PAPER)
		x += 44.0 + UiKit.text_width(UiKit.fmt(int(cost.get("silver_tael", 0))), 18) + 12.0
		var short := ""
		for m in cost.get("materials", {}):
			var need := int(cost.materials[m])
			icon_at(Rect2(x, cy, 32, 32), str(m))
			var mw := "%d %s" % [need, ContentDB.item_name(str(m))]
			text(Vector2(x + 36, cy + 23), mw, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, r.end.x - x - 110)
			x += 36.0 + minf(UiKit.text_width(mw, 16), r.end.x - x - 110) + 10.0
			var have := Game.inventory.count_owned(ch, str(m))
			if have < need: short = Tx.t("ui.your_sect.short") % [ContentDB.item_name(str(m)), have, need]
		text(Vector2(r.position.x + 16, cy + 23), UiKit.span(float(cost.get("seconds", 0))), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 32)
		if short != "": text(Vector2(r.position.x + 16, cy + 48), short, 14, UiKit.WARNING, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 32)
		var why: Dictionary = Game.sect.upgrade_check(ch, picked)
		var reason := str(why.get("text", str(why.get("reason", "")).replace("_", " ").capitalize()))
		btn(Rect2(r.position.x + 16, by, 150, BTN_H), Tx.t("ui.your_sect.build") if lv == 0 else Tx.t("ui.your_sect.upgrade"), "upgrade", picked, true, why.is_empty(), reason)
	else:
		text(Vector2(r.position.x + 16, r.position.y + 118), Tx.t("ui.your_sect.at_its_highest"), 16, UiKit.MIST)
	if picked == "treasury":
		btn(Rect2(r.end.x - 192, by, 176, BTN_H), Tx.t("ui.your_sect.open_storage"), "storage", null, false, Unlocks.is_unlocked(ch.id, "storage"), Unlocks.locked_text("storage"), 18)

## What a building gives at level `lv` (and the next), from its output in sect_buildings.json.
func _effect(id: String, lv: int) -> String:
	match id:
		"treasury":
			return Tx.t("ui.your_sect.fx_treasury") % [Game.accounts.storage_size(), int(Game.sect.output("treasury", "storage_slots_per_level"))]
		"guest_house":
			return Tx.t("ui.your_sect.fx_guest_house") % [Game.sect.disciple_cap(), int(Game.sect.output("guest_house", "disciples_per_level", 1))]
		"meditation_pavilion":
			return Tx.t("ui.your_sect.fx_pavilion") % int(round(float(Game.sect.output("meditation_pavilion", "idle_rate_per_level")) * 100.0))
		"expanse_outpost":
			return Tx.t("ui.your_sect.fx_outpost") % float(Game.sect.output("expanse_outpost", "attunement_per_level"))
		"mirror_of_echoes":
			return Tx.t("ui.your_sect.fx_mirror")
	var needs: Array = ContentDB.all("expeditions").filter(func(e): return str(e.get("requires_building", "")) == id).map(func(e): return str(e.name))
	if not needs.is_empty(): return Tx.t("ui.your_sect.fx_expeditions") % ", ".join(needs)
	return Tx.t("ui.your_sect.fx_prestige") % int(ContentDB.config("sect_levels").get("prestige_building", 20)) if lv == 0 else Tx.t("ui.your_sect.fx_stands")

## The disciples: how many rooms are full, each disciple, the candidates at the gate and Recruit.
func _disciples_card(s: Dictionary, r: Rect2) -> void:
	panel(r)
	var ds: Array = s.get("disciples", [])
	text(r.position + Vector2(16, 30), Tx.t("ui.your_sect.disciples"), 22, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, 200, true)
	text(Vector2(r.position.x + 16, r.position.y + 28), Tx.t("ui.your_sect.rooms") % [ds.size(), Game.sect.disciple_cap()], 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 32)
	var busy := Game.sect.guarding()
	list("ds", Rect2(r.position.x + 12, r.position.y + 38, r.size.x - 24, 80), ds.size(), 40, func(i: int, rr: Rect2):
		var d: Dictionary = ds[i]
		var cc := rr.position + Vector2(16, rr.size.y * 0.5)
		draw_circle(cc, 15.0, UiKit.BRONZE, true, -1.0, true)
		draw_circle(cc, 13.0, UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.4), true, -1.0, true)
		text(cc + Vector2(-15, 6), str(d.get("name", "?")).left(1), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 30)
		var away := Tx.t("ui.your_sect.away_expedition") if Game.sect._on_expedition(i) else (Tx.t("ui.your_sect.away_guard") if busy.has(i) else "")
		text(rr.position + Vector2(40, 16), Tx.t("ui.your_sect.lv") % [str(d.get("name", "")), int(d.get("level", 1)), _traits(d)], 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 44)
		text(rr.position + Vector2(40, 34), away if away != "" else Tx.t("ui.your_sect.stats") % [int(d.get("strength", 1)), int(d.get("spirit", 1)), int(d.get("craft", 1))], 14,
			UiKit.BRIGHT_JADE if away != "" else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 44)
	)
	if ds.is_empty(): text(r.position + Vector2(16, 70), Tx.t("ui.your_sect.no_disciples"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 32)
	var cands: Array = s.get("candidates", [])
	var full := ds.size() >= Game.sect.disciple_cap()
	var by := r.end.y - 56.0
	if cands.is_empty():
		text(Vector2(r.position.x + 16, by + 30), Tx.t("ui.your_sect.no_candidates"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 180)
	else:
		cand = clampi(cand, 0, cands.size() - 1)
		var names := ", ".join(cands.map(func(cd): return str(cd.get("name", ""))))
		text(Vector2(r.position.x + 16, by - 4), Tx.t("ui.your_sect.at_the_gate") % names, 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 32)
		var cd: Dictionary = cands[cand]
		text(Vector2(r.position.x + 16, by + 20), "%s · %s" % [str(cd.get("name", "")), _traits(cd)], 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 164)
		text(Vector2(r.position.x + 16, by + 40), Tx.t("ui.your_sect.stats") % [int(cd.get("strength", 1)), int(cd.get("spirit", 1)), int(cd.get("craft", 1))],
			14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 164)
	btn(Rect2(r.end.x - 136, by + 4, 120, BTN_H), Tx.t("ui.your_sect.recruit"), "recruit", cand, true, not full and not cands.is_empty(),
		Tx.t("sim.sect.build_more_guest_house_rooms") if full else Tx.t("ui.your_sect.no_candidates"))

## Beyond the walls: Expeditions and Territory, one tap each, and what the builders are about.
func _beyond(s: Dictionary, r: Rect2) -> void:
	text(r.position + Vector2(2, 16), Tx.t("ui.your_sect.beyond_the_walls"), 14, UiKit.GOLD)
	var out: Array = s.get("expeditions", [])
	var back := out.filter(func(ex): return float(ex.done_utc) <= Clock.now_utc()).size()
	var open := ContentDB.all("expeditions").filter(func(e): return not e.has("requires_building") or Game.sect.level_building(str(e.requires_building)) > 0).size()
	var ex_line := (Tx.t("ui.your_sect.out_back") % [out.size(), back] if not out.is_empty() else Tx.t("ui.your_sect.none_out")) + " · " + Tx.t("ui.your_sect.regions_open") % [open, ContentDB.all("expeditions").size()]
	var held: Array = Game.sect.mines().keys().filter(func(m): return Game.sect.holds(str(m)))
	var tr_line := Tx.t("ui.your_sect.mines_line") % [held.size(), Game.sect.mine_cap()] + (" · " + ContentDB.name_of("territory", str(held[0])) if not held.is_empty() else "")
	var rows := [["expeditions", "world_map", Tx.t("ui.your_sect.expeditions"), ex_line], ["territory", "mine", Tx.t("ui.your_sect.territory"), tr_line]]
	for i in rows.size():
		var rr := Rect2(r.position.x, r.position.y + 24 + i * 60, r.size.x, 52)
		face(rr, "minor_panel", "pressed" if _is_pressed("go_tab", rows[i][0]) else "normal")
		icon_at(Rect2(rr.position + Vector2(10, 10), Vector2(32, 32)), str(rows[i][1]))
		text(rr.position + Vector2(52, 23), str(rows[i][2]), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 84)
		text(rr.position + Vector2(52, 43), str(rows[i][3]), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 84)
		text(Vector2(rr.end.x - 26, rr.position.y + 32), "▶", 14, UiKit.MIST)
		region(rr, "go_tab", rows[i][0])
	var q: Array = s.get("queue", [])
	var build_line := Tx.t("ui.your_sect.builders_free")
	if not q.is_empty():
		build_line = Tx.t("ui.your_sect.builders_on") % [ContentDB.name_of("sect_buildings", str(q[0].building)), int(q[0].level), UiKit.span(float(q[0].done_utc) - Clock.now_utc())]
	para(Rect2(r.position.x + 2, r.position.y + 150, r.size.x - 4, 44), build_line, 14, UiKit.MIST, 2)

## Not yet founded: the empty grounds above, and the name and Found below them.
func _founding(ch) -> void:
	var r := Rect2(92, CARD_Y - 60, 1096, CARD_H + 60)
	panel(r)
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 60)), Tx.t("ui.your_sect.the_hidden_vale_beyond_crane"), 22)
	# The name field and Found sit under the words, placed from the content (P4: never in screen coordinates).
	if is_instance_valid(name_field): name_field.position = Vector2(r.position.x + 24, r.position.y + 120)
	btn(Rect2(r.position.x + 440, r.position.y + 116, 200, BTN_H_STANDARD), Tx.t("ui.your_sect.found"), "found", null, true, Unlocks.is_unlocked(ch.id, "your_sect"), Unlocks.locked_text("your_sect"))

# ------------------------------------------------------------------ Expeditions and Territory
## B4: one scrolling list, the running expeditions (and their Collect) first, then the regions to send to.
func _draw_expeditions(r: Rect2, s: Dictionary) -> void:
	var exs: Array = ContentDB.all("expeditions")
	var out: Array = s.get("expeditions", [])
	list("expeditions", Rect2(r.position + Vector2(10, 64), r.size - Vector2(20, 74)), out.size() + exs.size(), 56, func(i: int, rr: Rect2):
		if i < out.size():
			var ex: Dictionary = out[i]
			var left := int(float(ex.done_utc) - Clock.now_utc())
			text(Vector2(rr.position.x + 20, rr.position.y + 32), "%s: %s" % [ContentDB.name_of("expeditions", str(ex.region)), Tx.t("ui.your_sect.back") if left <= 0 else Tx.t("ui.your_sect.dm_left") % UiKit.span(left)], 18, UiKit.MIST)
			if left <= 0: btn(Rect2(rr.end.x - 180, rr.position.y + 2, 160, 48), Tx.t("ui.your_sect.collect"), "collect", i, true)
			return
		var e: Dictionary = exs[i - out.size()]
		text(Vector2(rr.position.x + 20, rr.position.y + 32), Tx.t("ui.your_sect.danger") % [str(e.name), int(e.danger_level)], 18)
		var x := rr.end.x - 10
		for h in e.get("hours", []):
			x -= 100
			btn(Rect2(x, rr.position.y + 2, 90, 48), UiKit.span(float(h) * 3600.0), "send", [str(e.id), int(h)])
	)

## S49 territory: every mine, who holds it, what waits in its carts, and when its old holder comes back.
func _draw_territory(r: Rect2, s: Dictionary) -> void:
	text(Vector2(r.position.x, r.position.y + 44), Tx.t("ui.your_sect.mines_held") % [Game.sect.mines().size(), Game.sect.mine_cap()], 18, UiKit.MIST,
		HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 30)
	var ms: Array = ContentDB.all("territory")
	var now := Clock.now_utc()
	var cap_h := float(ContentDB.config("territory").get("cap_hours", 24))
	var max_guards := int(ContentDB.config("territory").get("contest", {}).get("max_guards", 3))
	list("mines", Rect2(r.position + Vector2(10, 64), r.size - Vector2(20, 74)), ms.size(), 104, func(i: int, rr: Rect2):
		var m: Dictionary = ms[i]
		var id := str(m.id)
		var mine: bool = Game.sect.holds(id)
		var st: Dictionary = Game.sect.mines().get(id, {})
		var contested := bool(st.get("contested", false))
		panel(rr, "minor_panel", "selected" if contested else "normal")
		# The banner that flies over it: yours, or the holder's.
		var rv: Dictionary = Game.sect.rival(str(m.sect))
		var banner := "banner_your_sect" if mine else str(rv.get("banner", ""))
		var e := SpriteCache.prop(banner)
		var tx: Texture2D = SpriteCache.tex(str(e.get("file", ""))) if not e.is_empty() else null
		if tx: draw_texture_rect_region(tx, Rect2(rr.position + Vector2(14, 8), Vector2(48, 88)), Rect2(0, 4, 48, 88))
		var x0 := rr.position.x + 80
		text(Vector2(x0, rr.position.y + 28), str(m.name), 22, UiKit.PALE_GOLD if mine else UiKit.PAPER)
		var rate := Tx.t("ui.your_sect.rate_one") if int(m.rate) == 1 else Tx.t("ui.your_sect.rate") % int(m.rate)
		text(Vector2(x0, rr.position.y + 50), Tx.t("ui.your_sect.mine_meta") % [ContentDB.name_of("rooms", str(m.room)), int(m.level), rate,
			int(m.get("sect_level", 1))], 16, UiKit.MIST)
		if mine:
			var cap := int(cap_h * float(m.rate))
			var stored := Game.sect.mine_stored(id, now)
			text(Vector2(x0, rr.position.y + 74), Tx.t("ui.your_sect.mine_yours") % [stored, cap], 18, UiKit.BRIGHT_JADE)
			var when := Tx.t("ui.your_sect.mine_contested") % [str(rv.get("name", "")), UiKit.span(float(st.until) - now)] if contested \
				else Tx.t("ui.your_sect.mine_next") % UiKit.span(float(st.get("contest", now)) - now)
			text(Vector2(x0 + 250, rr.position.y + 74), when, 16, UiKit.RED_TEXT if contested else UiKit.MIST)
			var gs: Array = st.get("guards", [])
			var names: Array = gs.map(func(d): return str(s.disciples[int(d)].get("name", "")) if int(d) < s.disciples.size() else "")
			text(Vector2(x0, rr.position.y + 95), Tx.t("ui.your_sect.mine_guards") % [", ".join(names) if not names.is_empty() else Tx.t("ui.your_sect.no_guards"),
				int(round(Game.sect.guard_chance(id) * 100.0))], 14, UiKit.MIST)
			btn(Rect2(rr.end.x - 170, rr.position.y + 8, 150, 42), Tx.t("ui.your_sect.collect"), "mine_collect", id, stored > 0, stored > 0)
			var free := _free_disciple()
			if gs.size() < max_guards:
				btn(Rect2(rr.end.x - 330, rr.position.y + 8, 150, 42), Tx.t("ui.your_sect.post_guard"), "mine_guard", [id, free], false, free >= 0,
					Tx.t("ui.your_sect.no_free_disciple"))
			if not gs.is_empty():
				btn(Rect2(rr.end.x - 330, rr.position.y + 56, 150, 42), Tx.t("ui.your_sect.recall_guard"), "mine_guard", [id, int(gs[gs.size() - 1])])
			if contested: btn(Rect2(rr.end.x - 170, rr.position.y + 56, 150, 42), Tx.t("ui.your_sect.go"), "mine_go", str(m.room), true)
		else:
			text(Vector2(x0, rr.position.y + 74), Tx.t("ui.your_sect.mine_held_by") % str(rv.get("name", "")), 18, Color(str(rv.get("color", "#AFC9D1"))).lightened(0.35))
			para(Rect2(x0, rr.position.y + 80, rr.size.x - 300, 22), str(rv.get("desc", "")), 14, UiKit.MIST, 1)
			var why: String = Game.sect.assault_block(c(), id)
			btn(Rect2(rr.end.x - 170, rr.position.y + 8, 150, 42), Tx.t("ui.your_sect.go"), "mine_go", str(m.room), why == "", true)
			if why != "": text(Vector2(rr.end.x - 360, rr.position.y + 74), why, 14, UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_RIGHT, 340)
	)

## The first disciple free to stand guard (not away on an expedition, not guarding another mine), or -1.
func _free_disciple() -> int:
	var busy := Game.sect.guarding()
	var ds: Array = Game.sect.sect().get("disciples", [])
	for i in ds.size():
		if busy.has(i) or Game.sect._on_expedition(i): continue
		return i
	return -1

## Disciples carry one trait id (older saves may hold a list).
func _traits(d: Dictionary) -> String:
	var tr = d.get("trait", d.get("traits", []))
	var ids: Array = tr if tr is Array else [tr]
	return ", ".join(ids.map(func(t): return str(t).replace("_", " ").capitalize()))

func on_event(name: String, p: Dictionary) -> void:
	if name == "building_started": raised_at[str(p.get("building", ""))] = t
	queue_redraw()

func on_action(id: String, data) -> void:
	match id:
		"found":
			if name_field and submit({"type": "found_sect", "name": name_field.text.strip_edges()}).get("ok", false):
				name_field.queue_free()
				name_field = null
				setup()
		"pick": picked = str(data)
		"cand": cand = int(data)
		"go_tab":
			for i in tabs.size():
				if str(tabs[i].id) == str(data): tab = i
			scroll.clear()
		"storage": navigate.emit("storage", {})
		"upgrade": submit({"type": "upgrade_building", "building": str(data)})
		"repair": submit({"type": "repair_building", "building": str(data)})
		"recruit": submit({"type": "recruit_disciple", "index": int(data)})
		"send":
			# Up to two disciples who are home: not away on another expedition, not guarding a mine.
			var busy := Game.sect.guarding()
			var ids: Array = []
			for i in Game.sect.sect().get("disciples", []).size():
				if ids.size() < 2 and not busy.has(i) and not Game.sect._on_expedition(i): ids.append(i)
			submit({"type": "send_expedition", "region": str(data[0]), "hours": int(data[1]), "disciples": ids})
		"collect": submit({"type": "collect_expedition", "index": int(data)})
		"mine_collect": submit({"type": "collect_mine", "mine": str(data)})
		"mine_guard": submit({"type": "guard_mine", "mine": str(data[0]), "index": int(data[1])})
		"mine_go":
			if submit({"type": "auto_path", "target": str(data)}).get("ok", false): close()
