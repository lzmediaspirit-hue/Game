# Modal pages: systems hub, Character, Cultivation, Inventory, Skills, Gathering, Workshop,
# Journal, World Map, Settings, Shop, Storage, Commissions, Shrine, dialogue and defeat.
# Pages read state and invoke Game.perform — they never change coins or ranks directly.
extends Control

const C = preload("res://scripts/data/content.gd")
const S = preload("res://scripts/core/state.gd")
const R = preload("res://scripts/core/rules.gd")

signal closed
signal to_title

var world
var hud
var stack: Array = []           # [[page, args]]
var tabs := {}                  # remembered tab per page
var sel := {}                   # remembered selection per page
var dim: ColorRect
var frame: PanelContainer
var header_title: Label
var coins_l: Label
var back_btn: Button
var body: Control
var dlg: PanelContainer         # dialogue box (bottom)
var dlg_lines: Array = []
var dlg_i := 0
var dlg_menu: Array = []
var dlg_npc := ""
var dlg_label: Label
var dlg_name: Label
var dlg_buttons: HBoxContainer

const TITLES := {"hub": "Jade River", "character": "Character", "cultivation": "Cultivation", "inventory": "Inventory", "skills": "Skills",
	"gathering": "Gathering", "workshop": "Workshop", "journal": "Journal", "map": "World Map", "settings": "Settings", "shop": "Merchant",
	"storage": "Shared Storage", "board": "Commissions", "shrine": "Shrine", "rest": "Rest Shrine", "death": "Defeated", "class": "Choose a Discipline", "dao": "Choose a Principle"}


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	dim = ColorRect.new()
	dim.color = Color(0, 0.02, 0.03, 0.62)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.visible = false
	dim.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and not stack.is_empty() and stack[-1][0] == "hub":
			close())
	add_child(dim)
	frame = UI.panel(UI.PANEL, UI.GOLD, 16)
	frame.visible = false
	add_child(frame)
	var v := UI.vbox(10)
	frame.add_child(v)
	var head := UI.hbox(12)
	v.add_child(head)
	back_btn = UI.button("‹  Back", back, 20, "normal", 110)
	head.add_child(back_btn)
	header_title = UI.title("", 36)
	UI.expand(header_title)
	head.add_child(header_title)
	var ch := UI.hbox(6)
	ch.add_child(UI.icon(Icons.get_icon("coin"), 28))
	coins_l = UI.label("", 20, UI.CREAM)
	ch.add_child(coins_l)
	head.add_child(ch)
	var close_b := UI.button("✕", close, 24, "gold", 56)
	head.add_child(close_b)
	v.add_child(UI.sep_line())
	body = MarginContainer.new()
	UI.expand(body, true, true)
	v.add_child(body)
	_build_dialogue()


func is_open() -> bool:
	return frame.visible or dlg.visible


func open(page: String, args := {}) -> void:
	if stack.is_empty() or stack[-1][0] != page:
		stack.append([page, args])
	else:
		stack[-1] = [page, args]
	_render()


func replace(page: String, args := {}) -> void:
	if not stack.is_empty():
		stack.pop_back()
	open(page, args)


func refresh() -> void:
	if not stack.is_empty():
		_render()


func back() -> void:
	stack.pop_back()
	if stack.is_empty():
		close()
	else:
		_render()


func close() -> void:
	stack.clear()
	frame.visible = false
	dim.visible = dlg.visible
	if world:
		world.paused = dlg.visible
	closed.emit()


func _render() -> void:
	var page: String = stack[-1][0]
	var args: Dictionary = stack[-1][1]
	dim.visible = true
	frame.visible = true
	if world:
		world.paused = true
		world.ctl.reset()
	header_title.text = TITLES.get(page, page).to_upper() if page != "hub" else "JADE RIVER · SYSTEMS"
	back_btn.visible = stack.size() > 1
	coins_l.text = _fmt(int(Game.p.coins))
	UI.clear(body)
	var W := get_viewport_rect().size.x
	var H := get_viewport_rect().size.y
	var fw := minf(W - 40, 1500.0)
	var fh := H - 40
	if page in ["death", "class", "dao"]:
		fw = minf(W - 40, 960.0)
		fh = minf(H - 40, 560.0)
	frame.position = Vector2((W - fw) / 2, (H - fh) / 2)
	frame.size = Vector2(fw, fh)
	frame.custom_minimum_size = Vector2(fw, fh)
	call("_page_" + page, args)


static func _fmt(n: int) -> String:
	var s := str(n)
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out


func _toast(r: Dictionary) -> void:
	if hud == null:
		return
	if r.ok:
		if r.get("msg", "") != "":
			hud.toast(r.msg, "ok")
	else:
		hud.toast(r.err, "err")
	for l in r.get("lines", []):
		hud.toast(l, "quest")


func _act(action: String, args := {}) -> Dictionary:
	var r := Game.perform(action, args)
	_toast(r)
	refresh()
	return r


func _tabs(page: String, names: Array, labels: Array) -> String:
	var cur: String = tabs.get(page, names[0])
	if not names.has(cur):
		cur = names[0]
	var row := UI.hbox(8)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	for i in names.size():
		var n: String = names[i]
		row.add_child(UI.button(labels[i], func():
			tabs[page] = n
			refresh(), 19, "tab_on" if n == cur else "tab", 150))
	_col().add_child(row)
	return cur


var _col_node: VBoxContainer


func _col() -> VBoxContainer:
	if _col_node == null or not is_instance_valid(_col_node) or _col_node.get_parent() != body:
		_col_node = UI.vbox(10)
		UI.expand(_col_node, true, true)
		body.add_child(_col_node)
	return _col_node


func _req_row(ok: bool, text: String, have: String, hint := "") -> Control:
	var h := UI.hbox(8)
	h.add_child(UI.label("✔" if ok else "✘", 20, UI.GREEN if ok else UI.RED))
	var l := UI.label(text, 18, UI.CREAM)
	UI.expand(l)
	h.add_child(l)
	h.add_child(UI.label(have, 18, UI.GREEN if ok else UI.RED))
	if hint != "" and not ok:
		var v := UI.vbox(0)
		v.add_child(h)
		v.add_child(UI.label("   " + hint, 14, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
		return v
	return h


# ================================================================ hub
func _page_hub(_a: Dictionary) -> void:
	var col := _col()
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 18)
	grid.add_theme_constant_override("v_separation", 18)
	UI.expand(grid, true, true)
	col.add_child(grid)
	var tiles := [["character", "Character", "equipment & stats"], ["cultivate", "Cultivation", "realms & meditation"], ["gather", "Gathering", "mining, fishing & herbs"],
		["anvil", "Workshop", "smithing, pills & alchemy"], ["book", "Skills", "weapon mastery & arts"], ["journal", "Journal", "story & guide"]]
	var pages := ["character", "cultivation", "gathering", "workshop", "skills", "journal"]
	for i in 6:
		var t: Array = tiles[i]
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(260, 180)
		UI.expand(b, true, true)
		var pg: String = pages[i]
		b.pressed.connect(func(): open(pg))
		var v := UI.vbox(2)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		var ic := UI.icon(Icons.get_icon(t[0]), 96)
		v.add_child(ic)
		v.add_child(UI.title(t[1], 28))
		v.add_child(UI.label(t[2], 16, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER))
		b.add_child(v)
		grid.add_child(b)
	var bar := UI.hbox(14)
	var p: Dictionary = Game.p
	bar.add_child(UI.label("%s  ·  %s  ·  Lv %d" % [p.name, S.realm_name(p), p.level], 20))
	bar.add_child(UI.spacer(0, 0, true))
	var ob := R.objective(p)
	bar.add_child(UI.label("Current: " + ob.text, 18, Color("#ffe08a")))
	bar.add_child(UI.button("World Map", func(): open("map"), 18))
	bar.add_child(UI.button("Settings", func(): open("settings"), 18))
	col.add_child(bar)


# ================================================================ character
func _page_character(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var tab := _tabs("character", ["overview", "appearance"], ["Overview", "Appearance"])
	var row := UI.hbox(20)
	UI.expand(row, true, true)
	_col().add_child(row)
	var left := UI.sub_panel(14)
	var lv := UI.vbox(8)
	left.add_child(lv)
	var big := UI.icon(Sprites.humanoid(Sprites.player_look(p), "idle", 0).tex, 230)
	lv.add_child(big)
	lv.add_child(UI.title(p.name, 28))
	lv.add_child(UI.label("%s · Level %d" % [S.realm_name(p), p.level], 19, UI.CREAM, HORIZONTAL_ALIGNMENT_CENTER))
	row.add_child(left)
	var right := UI.sub_panel(16)
	UI.expand(right, true, true)
	row.add_child(right)
	var rv := UI.vbox(10)
	right.add_child(rv)
	if tab == "overview":
		var st := S.stats(p)
		var grid := GridContainer.new()
		grid.columns = 4
		grid.add_theme_constant_override("h_separation", 26)
		for e in [["class", "Attack", st.atk], ["shield", "Defense", st.def], ["potion_red", "Max HP", st.max_hp], ["art", "Max Qi", st.max_qi],
				["insight", "Insight", p.insight], ["essence", "Qi Essence", p.essence], ["meridian", "Meridians", "%d/6" % p.meridians.size()], ["realm", "Soul", p.soul]]:
			var h := UI.hbox(6)
			h.add_child(UI.icon(Icons.get_icon(e[0]), 32))
			h.add_child(UI.label("%s  %s" % [e[1], str(e[2])], 19))
			grid.add_child(h)
		rv.add_child(grid)
		rv.add_child(UI.label("XP %d / %d toward level %d" % [p.xp, S.xp_to_next(p.level), p.level + 1], 17, UI.DIM))
		rv.add_child(UI.bar(float(p.xp) / S.xp_to_next(p.level), UI.GOLD, 420, 12))
		rv.add_child(UI.sep_line())
		var w: Dictionary = C.ITEMS[p.equip.weapon]
		rv.add_child(UI.label("Weapon: %s (+%d attack)   Sword mastery %d · Spear mastery %d" % [w.name, w.atk, p.mastery.sword, p.mastery.spear], 18))
		var cls_t: String = C.CLASSES[p.cls].name + " — " + C.CLASSES[p.cls].desc if p.cls != null else "No discipline yet — Elder Wen teaches the three disciplines after your first lessons."
		rv.add_child(UI.label("Discipline: " + cls_t, 17, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
		if p.dao is Dictionary:
			rv.add_child(UI.label("Dao: %s — comprehension %d" % [C.DAOS[p.dao.id].name, p.dao.xp], 17, Color("#9fdcff")))
		var eq := UI.hbox(10)
		for slot in ["hat", "gourd"]:
			var id = p.equip[slot]
			eq.add_child(UI.label("%s: %s" % [S.cap(slot), C.ITEMS[id].name if id != null else "—"], 17, UI.DIM))
		rv.add_child(eq)
		rv.add_child(UI.label("Robe, hat and gourd are cosmetic. Manage gear in the Inventory.", 15, UI.DIM))
		rv.add_child(UI.button("Open Inventory", func(): open("inventory"), 18))
	else:
		rv.add_child(UI.label("Hair", 22, UI.GOLD))
		var hr := UI.hbox(10)
		for hdef in C.HAIR:
			var look := Sprites.player_look(p)
			look.hair = hdef.id
			look.hairColor = Sprites.HAIR_COLORS[hdef.id]
			var hid: String = hdef.id
			var b := UI.icon_button(Sprites.humanoid(look, "idle", 0).tex, hdef.name, func():
				p.look.hair = hid
				Game.save_now()
				refresh(), 90, 16)
			if p.look.hair == hid:
				b.add_theme_stylebox_override("normal", UI.box(UI.PANEL3, UI.GOLD, 3, 6, 8))
			hr.add_child(b)
		rv.add_child(hr)
		rv.add_child(UI.label("Clothes", 22, UI.GOLD))
		var cr := UI.hbox(10)
		for cdef in C.CLOTHES:
			var look2 := Sprites.player_look(p)
			look2.main = cdef.main
			look2.trim = cdef.trim
			look2.under = cdef.under
			look2.sash = cdef.sash
			var cid: String = cdef.id
			var b2 := UI.icon_button(Sprites.humanoid(look2, "idle", 0).tex, cdef.name, func():
				p.look.clothes = cid
				Game.save_now()
				refresh(), 90, 16)
			if p.look.clothes == cid:
				b2.add_theme_stylebox_override("normal", UI.box(UI.PANEL3, UI.GOLD, 3, 6, 8))
			cr.add_child(b2)
		rv.add_child(cr)
		rv.add_child(UI.label("Appearance is cosmetic and free to change.", 15, UI.DIM))


# ================================================================ cultivation
func _page_cultivation(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var tab := _tabs("cultivation", ["realm", "meridians", "body", "soul", "dao"], ["Realm", "Meridians", "Body", "Soul", "Dao"])
	var row := UI.hbox(18)
	UI.expand(row, true, true)
	_col().add_child(row)
	# realm ladder
	var ladder := UI.sub_panel(10)
	var lv := UI.vbox(6)
	ladder.add_child(lv)
	for i in range(C.REALMS.size() - 1, -1, -1):
		var r: Dictionary = C.REALMS[i]
		var cur: bool = i == p.realm
		var pnl := UI.panel(Color("#16302a") if cur else Color("#0b1c1c"), UI.GOLD if cur else Color("#2f4a44"), 8)
		var h := UI.hbox(8)
		h.add_child(UI.icon(Icons.get_icon("realm" if i <= p.realm else "lock"), 36))
		var vv := UI.vbox(0)
		vv.add_child(UI.label(r.name, 19, UI.GOLD if cur else (UI.CREAM if i < p.realm else UI.DIM)))
		vv.add_child(UI.label("Current Realm" if cur else ("Attained" if i < p.realm else "Locked"), 14, UI.DIM))
		h.add_child(vv)
		pnl.add_child(h)
		pnl.custom_minimum_size.x = 230
		lv.add_child(pnl)
	row.add_child(ladder)
	var mid := UI.sub_panel(16)
	UI.expand(mid, true, true)
	row.add_child(mid)
	var mv := UI.vbox(10)
	mid.add_child(mv)
	var br = R.breakthrough_reqs(p)
	var safe: bool = world != null and world.is_safe_spot()
	match tab:
		"realm":
			var top := UI.hbox(16)
			var fig := UI.icon(Sprites.humanoid(Sprites.player_look(p), "sit", 0).tex, 150)
			top.add_child(fig)
			var sv := UI.vbox(6)
			sv.add_child(UI.label("Insight  %d" % p.insight, 22, Color("#9fdcff")))
			sv.add_child(UI.label("Qi essence  %d" % p.essence, 20, Color("#8fe8ff")))
			sv.add_child(UI.label("Meridians  %d/6" % p.meridians.size(), 20, UI.JADE))
			sv.add_child(UI.label("Insight gates breakthroughs; Qi essence opens meridians and tempers the body. Your Qi bar is separate and refills.", 15, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
			UI.expand(sv)
			top.add_child(sv)
			mv.add_child(top)
			var medrow := UI.hbox(10)
			medrow.add_child(UI.button("Meditate", func():
				close()
				hud.set_mode("cultivation")
				world.ctl.meditate = true, 22, "jade", 200))
			medrow.add_child(UI.label("Safe here — meditation cycles grant insight and essence." if safe else "Return to a sanctuary or a field shrine with no enemies near to meditate.", 16, UI.GREEN if safe else Color("#ffb080"), HORIZONTAL_ALIGNMENT_LEFT, true))
			mv.add_child(medrow)
			mv.add_child(UI.sep_line())
			if br == null:
				mv.add_child(UI.label("You stand at the peak of the known realms.", 20, UI.GOLD))
			else:
				mv.add_child(UI.title("Next: " + br.realm.name, 28))
				for q in br.list:
					mv.add_child(_req_row(q.ok, q.label, "%d/%d" % [q.have, q.need], q.hint))
				mv.add_child(UI.label("Benefit: +%d HP, +%d Qi, +%d attack · 2 more meridians accessible%s" % [C.REALM_BONUS.hp, C.REALM_BONUS.qi, C.REALM_BONUS.atk, " · a short Inner Sea trial" if br.realm.trial else ""], 16, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
				var all_ok := true
				for q in br.list:
					all_ok = all_ok and q.ok
				var bb := UI.button("BREAKTHROUGH" if not br.realm.trial else "BEGIN TRIAL", func():
					if br.realm.trial:
						close()
						world.start_trial()
					else:
						var r2 := _act("breakthrough", {"safe": world.is_safe_spot()})
						if r2.ok and world:
							world._ring(world.pl.x, world.pl.d, world.pl.h, UI.GOLD, 40), 24, "gold", 300)
				bb.disabled = not all_ok or not safe
				mv.add_child(bb)
				if not safe:
					mv.add_child(UI.label("Breakthroughs happen at a safe shrine.", 15, UI.DIM))
				mv.add_child(UI.label("Failure never costs a realm or an item — recover and retry.", 15, UI.DIM))
		"meridians":
			var capn := S.meridian_cap(p.realm)
			mv.add_child(UI.label("Open channels with Qi essence (have %d). Your realm allows %d open meridians." % [p.essence, capn], 18, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
			for i in C.MERIDIANS.size():
				var m: Dictionary = C.MERIDIANS[i]
				var opened: bool = i < p.meridians.size()
				var h2 := UI.hbox(10)
				h2.add_child(UI.icon(Icons.get_icon("meridian"), 34))
				var bonus := []
				for k in m.bonus:
					bonus.append("+%d %s" % [m.bonus[k], {"hp": "HP", "qi": "Qi", "atk": "attack", "def": "defense"}[k]])
				var l := UI.label("%s — %s" % [m.name, ", ".join(bonus)], 19, UI.JADE if opened else UI.CREAM)
				UI.expand(l)
				h2.add_child(l)
				if opened:
					h2.add_child(UI.label("Open", 18, UI.GREEN))
				elif i == p.meridians.size():
					var b := UI.button("Open · %d essence" % m.cost, func(): _act("open_meridian"), 17, "jade")
					b.disabled = i >= capn or p.essence < int(m.cost)
					h2.add_child(b)
					if i >= capn:
						h2.add_child(UI.label("Needs next realm", 15, UI.DIM))
				else:
					h2.add_child(UI.label("%d essence" % m.cost, 16, UI.DIM))
				mv.add_child(h2)
		"body":
			mv.add_child(UI.label("Body tempering: combat materials + Qi essence. Bounded bonuses — never required for a basic attack.", 17, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
			for b in C.BODY_BRANCHES:
				var rk := int(p.body[b.id])
				var h3 := UI.hbox(10)
				var v3 := UI.vbox(0)
				v3.add_child(UI.label("%s  %d/%d" % [b.name, rk, b.max], 20, UI.GOLD))
				v3.add_child(UI.label("%s per rank. %s" % [b.per, b.desc], 15, UI.DIM))
				UI.expand(v3)
				h3.add_child(v3)
				if rk < int(b.max):
					var bid: String = b.id
					var bt := UI.button("Temper · %d hide, %d essence" % [rk + 1, 12 * (rk + 1)], func(): _act("temper_body", {"branch": bid}), 16, "jade")
					bt.disabled = R.count(p, "hide") < rk + 1 or p.essence < 12 * (rk + 1)
					h3.add_child(bt)
				mv.add_child(h3)
			mv.add_child(UI.label("Beast Hide: Bamboo Wolves in Whispering Bamboo; Black Wind Wolves at the monastery.", 15, UI.DIM))
		"soul":
			mv.add_child(UI.label("Soul points: %d  — earned by discovering resource sites and chapter secrets." % p.soul, 19))
			for m in C.SOUL_MILESTONES:
				mv.add_child(_req_row(p.soul >= int(m.at), "%s — %s" % [m.name, m.desc], "%d/%d" % [mini(p.soul, m.at), m.at]))
		"dao":
			if p.dao is Dictionary:
				var d: Dictionary = C.DAOS[p.dao.id]
				mv.add_child(UI.title(d.name, 26))
				mv.add_child(UI.label(d.desc, 18, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
				var rank := 0
				for i in d.ranks.size():
					if p.dao.xp >= int(d.ranks[i]):
						rank = i
				mv.add_child(UI.label("Comprehension %d (rank %d) — grows each time an art strikes." % [p.dao.xp, rank], 17, Color("#9fdcff")))
			else:
				mv.add_child(UI.label("Keeper Tao of Cloudrest Court teaches the first two principles in Chapter III.", 18, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
				for id in C.DAOS:
					mv.add_child(UI.label("%s — %s" % [C.DAOS[id].name, C.DAOS[id].desc], 16, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))


# ================================================================ inventory
func _page_inventory(a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var row := UI.hbox(16)
	UI.expand(row, true, true)
	_col().add_child(row)
	# character column
	var left := UI.sub_panel(12)
	var lv := UI.vbox(8)
	left.add_child(lv)
	lv.add_child(UI.label("Character", 22, UI.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	var eqr := UI.hbox(10)
	var slots := UI.vbox(8)
	for slot in ["weapon", "hat", "gourd"]:
		var id = p.equip[slot]
		var b := UI.icon_button(Icons.item(id) if id != null else Icons.get_icon("lock"), S.cap(slot), func():
			if id != null:
				sel["inventory"] = id
				refresh(), 64, 15)
		slots.add_child(b)
	eqr.add_child(slots)
	eqr.add_child(UI.icon(Sprites.humanoid(Sprites.player_look(p), "idle", 0).tex, 180))
	lv.add_child(eqr)
	var st := S.stats(p)
	for e in [["class", "Attack", st.atk], ["shield", "Defense", st.def], ["potion_red", "HP", st.max_hp], ["art", "Qi", st.max_qi]]:
		var h := UI.hbox(8)
		h.add_child(UI.icon(Icons.get_icon(e[0]), 26))
		var l := UI.label(e[1], 18)
		UI.expand(l)
		h.add_child(l)
		h.add_child(UI.label(str(e[2]), 18))
		lv.add_child(h)
	row.add_child(left)
	# details
	var mid := UI.sub_panel(12)
	mid.custom_minimum_size.x = 340
	var mv := UI.vbox(8)
	mid.add_child(mv)
	mv.add_child(UI.label("Item Details", 22, UI.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	var selected: String = sel.get("inventory", "")
	if selected == "" or not p.items.has(selected):
		selected = ""
		for id in p.items:
			selected = id
			break
	if selected != "":
		var d: Dictionary = C.ITEMS[selected]
		mv.add_child(UI.icon(Icons.item(selected), 110))
		mv.add_child(UI.title(d.name, 26))
		mv.add_child(UI.label("Owned: %d" % R.count(p, selected), 18, UI.CREAM, HORIZONTAL_ALIGNMENT_CENTER))
		mv.add_child(UI.sep_line())
		mv.add_child(UI.label(d.desc, 17, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
		if d.has("source"):
			mv.add_child(UI.label("Source: " + d.source, 16, Color("#ffe08a"), HORIZONTAL_ALIGNMENT_LEFT, true))
		if d.kind == "weapon":
			var need := int(d.rank) * 20
			var cur_w: Dictionary = C.ITEMS[p.equip.weapon]
			mv.add_child(UI.label("Attack +%d (equipped: +%d) · needs %s Mastery %d%s" % [d.atk, cur_w.atk, S.cap(d.family), need, (" + " + C.REALMS[d.realm].name) if d.has("realm") else ""], 16, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
		var acts := UI.vbox(6)
		if d.kind in ["weapon", "cosmetic"]:
			var eq_now: bool = p.equip.values().has(selected)
			if not (d.kind == "weapon" and eq_now):
				acts.add_child(UI.button("Unequip" if eq_now else "Equip", func(): _act("equip", {"id": selected}), 18, "jade"))
		if d.kind in ["pill", "crystal"] and selected != "foundation_pill":
			acts.add_child(UI.button("Absorb" if d.kind == "crystal" else "Use", func(): _act("use", {"id": selected}), 18, "jade"))
		if d.kind == "pill":
			var qs := UI.hbox(6)
			for i in 2:
				qs.add_child(UI.button("Quickslot %d" % (i + 1), func():
					p.quickslots[i] = selected
					refresh(), 15))
			acts.add_child(qs)
		if d.kind != "quest" and not (d.kind == "tool" and int(d.value) == 0):
			acts.add_child(UI.button("Sell 1  (+%d)" % maxi(1, int(d.value) / 2), func(): _confirm_sell(selected), 18, "gold"))
		acts.add_child(UI.button("View Source", func():
			sel["map_resource"] = selected
			open("map"), 16))
		mv.add_child(acts)
	else:
		mv.add_child(UI.label("Your bag is empty.", 18, UI.DIM))
	row.add_child(mid)
	# bag
	var right := UI.sub_panel(12)
	UI.expand(right, true, true)
	var rv := UI.vbox(8)
	right.add_child(rv)
	rv.add_child(UI.label("Items", 22, UI.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	var tab: String = tabs.get("inventory", "all")
	var tr := UI.hbox(6)
	for t in [["all", "All"], ["equipment", "Equipment"], ["materials", "Materials"], ["pills", "Pills"], ["quest", "Quest"]]:
		var tn: String = t[0]
		tr.add_child(UI.button(t[1], func():
			tabs["inventory"] = tn
			refresh(), 16, "tab_on" if tn == tab else "tab"))
	rv.add_child(tr)
	var grid := GridContainer.new()
	grid.columns = 6
	for id in p.items:
		var d2: Dictionary = C.ITEMS[id]
		if not _tab_match(tab, d2):
			continue
		var iid: String = id
		var b2 := UI.icon_button(Icons.item(id), str(p.items[id]), func():
			sel["inventory"] = iid
			refresh(), 70, 15)
		if iid == selected:
			b2.add_theme_stylebox_override("normal", UI.box(UI.PANEL3, UI.GOLD, 3, 6, 6))
		grid.add_child(b2)
	rv.add_child(UI.scroll(grid, 300))
	row.add_child(right)


static func _tab_match(tab: String, d: Dictionary) -> bool:
	match tab:
		"equipment": return d.kind in ["weapon", "cosmetic", "tool"]
		"materials": return d.kind in ["material", "crystal"]
		"pills": return d.kind == "pill"
		"quest": return d.kind == "quest"
	return true


func _confirm_sell(id: String) -> void:
	var p: Dictionary = Game.p
	var d: Dictionary = C.ITEMS[id]
	var risky: bool = p.equip.values().has(id) or int(d.value) >= 100 or d.kind == "weapon"
	if not risky:
		_act("sell", {"id": id, "n": 1})
		return
	var cd := ConfirmationDialog.new()
	cd.dialog_text = "Sell %s for %d coins?" % [d.name, maxi(1, int(d.value) / 2)]
	cd.confirmed.connect(func(): _act("sell", {"id": id, "n": 1}))
	add_child(cd)
	cd.popup_centered()


# ================================================================ skills
func _page_skills(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var tab := _tabs("skills", ["weapon", "combat", "professions"], ["Weapon Mastery", "Combat", "Professions"])
	var row := UI.hbox(16)
	UI.expand(row, true, true)
	_col().add_child(row)
	if tab == "weapon":
		var fam: String = sel.get("skills_family", S.stats(p).family)
		var left := UI.sub_panel(10)
		var lv := UI.vbox(8)
		left.add_child(lv)
		lv.add_child(UI.label("Weapon Mastery", 20, UI.JADE, HORIZONTAL_ALIGNMENT_CENTER))
		for f in ["sword", "spear"]:
			var ff: String = f
			var m := int(p.mastery[f])
			var nxt := (m / 20 + 1) * 20
			var b := UI.icon_button(Icons.get_icon(f), "%s  %d / %d" % [S.cap(f), m, nxt], func():
				sel["skills_family"] = ff
				refresh(), 90, 17)
			if ff == fam:
				b.add_theme_stylebox_override("normal", UI.box(UI.PANEL3, UI.GOLD, 3, 6, 8))
			lv.add_child(b)
		lv.add_child(UI.label("Mastery grows with each\nmeaningful hit using that\nweapon family.", 14, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER))
		row.add_child(left)
		var tree := UI.sub_panel(12)
		UI.expand(tree, true, true)
		var tv := UI.vbox(12)
		tree.add_child(tv)
		tv.add_child(UI.title(C.WEAPON_TREES[fam].name, 26))
		var chosen: String = sel.get("skill", "")
		for tier in C.WEAPON_TREES[fam].nodes:
			var tr := UI.hbox(24)
			tr.alignment = BoxContainer.ALIGNMENT_CENTER
			for id in tier:
				var known: bool = p.abilities.known.has(id)
				var sid: String = id
				var nb := UI.icon_button(Icons.ability(id), C.ABILITIES[id].name + ("\nLearned" if known else ("\nAvailable" if S.can_learn(p, id) else "\nLocked")), func():
					sel["skill"] = sid
					refresh(), 84, 16)
				nb.modulate = Color.WHITE if known or S.can_learn(p, id) else Color(0.6, 0.6, 0.6)
				if sid == chosen:
					nb.add_theme_stylebox_override("normal", UI.box(UI.PANEL3, UI.GOLD, 3, 6, 8))
				tr.add_child(nb)
			tv.add_child(tr)
			tv.add_child(UI.label("↓", 20, UI.JADE, HORIZONTAL_ALIGNMENT_CENTER))
		tv.get_child(tv.get_child_count() - 1).queue_free()
		row.add_child(tree)
		if chosen == "" or not C.ABILITIES.has(chosen) or C.ABILITIES[chosen].get("family", "") != fam:
			chosen = C.WEAPON_TREES[fam].nodes[0][0]
		row.add_child(_skill_detail(chosen))
	elif tab == "combat":
		var lst := UI.sub_panel(12)
		UI.expand(lst, true, true)
		var lv2 := UI.vbox(8)
		lst.add_child(lv2)
		lv2.add_child(UI.label("Equipped arts (field hotbar)", 20, UI.GOLD))
		var hb := UI.hbox(12)
		hb.add_child(UI.icon_button(Icons.get_icon("step"), "Step (always)", Callable(), 76, 15))
		for i in 3:
			var id = p.abilities.slots[i]
			var slot_i := i
			hb.add_child(UI.icon_button(Icons.ability(id) if id != null else Icons.get_icon("lock"), (C.ABILITIES[id].name if id != null else "Empty") + "\nSlot %d" % (i + 1), func():
				Game.perform("slot", {"slot": slot_i, "id": null})
				refresh(), 76, 15))
		lv2.add_child(hb)
		lv2.add_child(UI.label("Tap a slot to clear it. Tap a known art below, then a slot number to equip it.", 15, UI.DIM))
		lv2.add_child(UI.sep_line())
		for src in ["universal", "realm", "class", "weapon"]:
			var any := false
			for id in C.ABILITIES:
				var a: Dictionary = C.ABILITIES[id]
				if a.source != src:
					continue
				any = true
				var h := UI.hbox(10)
				h.add_child(UI.icon(Icons.ability(id), 40))
				var known: bool = p.abilities.known.has(id)
				var reqs := S.ability_reqs(p, id)
				var rq := []
				for r in reqs:
					if not r.ok:
						rq.append(r.label)
				var desc := "%s  [%s] — %s  (Qi %d · %ss)" % [a.name, src.capitalize() + ((" · " + a.family) if a.has("family") else ""), a.desc, a.qi, str(a.cd)]
				var l := UI.label(desc + ("" if known or rq.is_empty() else "  — needs " + ", ".join(rq)), 16, UI.CREAM if known else UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true)
				UI.expand(l)
				h.add_child(l)
				if known and id != "step":
					for i in 3:
						var aid: String = id
						var si := i
						h.add_child(UI.button(str(i + 1), func():
							Game.perform("slot", {"slot": si, "id": aid})
							refresh(), 16, "tab_on" if p.abilities.slots[i] == id else "tab", 44))
				elif not known and S.can_learn(p, id):
					var lid: String = id
					h.add_child(UI.button("Learn", func(): _act("learn", {"id": lid}), 16, "gold"))
				lv2.add_child(h)
		row.add_child(UI.scroll(lst, 400))
	else:
		var pv := UI.sub_panel(14)
		UI.expand(pv, true, true)
		var v := UI.vbox(10)
		pv.add_child(v)
		for prof in C.PROFESSIONS:
			var xp := int(p.prof[prof])
			var lv3 := S.prof_level(xp)
			var nxt: int = C.PROF_XP[mini(lv3 + 1, C.PROF_XP.size() - 1)]
			var h2 := UI.hbox(12)
			h2.add_child(UI.icon(Icons.get_icon({"mining": "pick", "herbalism": "herb", "fishing": "rod", "smithing": "anvil", "alchemy": "potion"}[prof]), 44))
			var vv := UI.vbox(2)
			vv.add_child(UI.label("%s  Lv %d" % [C.PROFESSIONS[prof].name, lv3], 20, UI.GOLD))
			vv.add_child(UI.bar(float(xp - C.PROF_XP[lv3]) / maxf(1, nxt - C.PROF_XP[lv3]), UI.JADE, 360, 10))
			vv.add_child(UI.label("%d / %d XP — gathering or crafting raises it; higher tiers open new nodes and recipes." % [xp, nxt], 14, UI.DIM))
			h2.add_child(vv)
			v.add_child(h2)
		row.add_child(pv)


func _skill_detail(id: String) -> Control:
	var p: Dictionary = Game.p
	var a: Dictionary = C.ABILITIES[id]
	var d := UI.sub_panel(14)
	d.custom_minimum_size.x = 360
	var v := UI.vbox(8)
	d.add_child(v)
	v.add_child(UI.title(a.name, 26))
	v.add_child(UI.icon(Icons.ability(id), 110))
	v.add_child(UI.label(a.desc, 17, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
	v.add_child(UI.sep_line())
	v.add_child(UI.label("Prerequisites", 19, UI.GOLD))
	for r in S.ability_reqs(p, id):
		v.add_child(_req_row(r.ok, r.label, "%d/%d" % [r.have, r.need]))
	v.add_child(UI.label("Qi cost %d · cooldown %ss · shape: %s" % [a.qi, str(a.cd), a.shape], 16, Color("#8fe8ff")))
	var known: bool = p.abilities.known.has(id)
	if known:
		v.add_child(UI.label("Learned — slot it on the Combat tab.", 16, UI.GREEN))
	else:
		var b := UI.button("Learn", func(): _act("learn", {"id": id}), 22, "gold")
		b.disabled = not S.can_learn(p, id)
		v.add_child(b)
		if b.disabled:
			v.add_child(UI.label("Prerequisites not met", 15, UI.RED, HORIZONTAL_ALIGNMENT_CENTER))
	v.add_child(UI.label("“Discipline flows. The river endures.”", 15, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER))
	return d


# ================================================================ gathering
func _page_gathering(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var tab := _tabs("gathering", ["mining", "herbalism", "fishing", "beast"], ["Mining", "Herbalism", "Fishing", "Beast Materials"])
	var row := UI.hbox(16)
	UI.expand(row, true, true)
	_col().add_child(row)
	var lst := UI.sub_panel(12)
	UI.expand(lst, true, true)
	var v := UI.vbox(8)
	lst.add_child(v)
	if tab == "beast":
		v.add_child(UI.label("Beast parts drop from monsters — never from a menu.", 18))
		for e in C.ENEMIES:
			var ed: Dictionary = C.ENEMIES[e]
			if ed.drops.is_empty():
				continue
			var parts := []
			for dr in ed.drops:
				parts.append("%s %d%%" % [C.ITEMS[dr[0]].name, int(float(dr[1]) * 100)])
			v.add_child(UI.label("%s — %s" % [ed.name, ", ".join(parts)], 16, UI.CREAM))
	else:
		var lv := S.prof_lv(p, tab)
		v.add_child(UI.label("%s Lv %d · tool: %s" % [C.PROFESSIONS[tab].name, lv, "ready" if R.has_tool(p, {"mining": "mining", "herbalism": "herbalism", "fishing": "fishing"}[tab]) else "none — Elder Wen provides one"], 20, UI.GOLD))
		for aid in C.MAP_AREAS:
			var ar: Dictionary = C.AREAS[aid]
			for n in ar.nodes:
				var nd: Dictionary = C.NODE_TYPES[n.type]
				if nd.prof != tab:
					continue
				var disc: bool = p.discovered.nodes.has(n.id)
				var h := UI.hbox(10)
				h.add_child(UI.icon(Icons.item(nd.item), 36))
				var where: String = ar.name + (" · raised deck" if n.has("surface") else "")
				var l := UI.label("%s — %s%s" % [nd.name if disc else "Undiscovered site", where, "" if lv >= int(nd.lv) else "  (needs Lv %d)" % nd.lv], 17, UI.CREAM if disc else UI.DIM)
				UI.expand(l)
				h.add_child(l)
				var target: String = aid
				h.add_child(UI.button("Track", func():
					p.tracked = target
					hud.toast("Tracking %s — follow the world route." % C.AREAS[target].name, "info"), 15))
				v.add_child(h)
	row.add_child(UI.scroll(lst, 400))
	# assignment panel
	var asg := UI.sub_panel(14)
	asg.custom_minimum_size.x = 380
	var av := UI.vbox(8)
	asg.add_child(av)
	av.add_child(UI.label("Assignments", 22, UI.GOLD))
	av.add_child(UI.label("A slower, capped (8 h) job that continues while you are away. One at a time.", 15, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
	if p.assignment != null:
		var y := R.assignment_yield(p, Game.now())
		av.add_child(UI.label("%s — %d min elapsed" % [R.ASSIGN[p.assignment.kind].name, y.minutes], 18))
		av.add_child(UI.button("Collect", func(): _act("collect_assignment"), 20, "gold"))
	else:
		for k in R.ASSIGN:
			var kk: String = k
			var b := UI.button(R.ASSIGN[k].name, func(): _act("assign", {"kind": kk}), 17, "jade")
			av.add_child(b)
			av.add_child(UI.label(R.ASSIGN[k].desc, 14, UI.DIM))
	row.add_child(asg)


# ================================================================ workshop
func _page_workshop(a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var station: String = a.get("station", "")
	if station == "forge":
		tabs["workshop"] = "smithing"
	elif station == "furnace" and tabs.get("workshop", "") == "smithing":
		tabs["workshop"] = "pills"
	elif station == "research":
		tabs["workshop"] = "research"
	var tab := _tabs("workshop", ["smithing", "pills", "research"], ["Smithing", "Pill Crafting", "Alchemy Research"])
	var sub := UI.label("Craft tools, weapons and supplies for the road ahead." + ("" if station != "" else "  (Recipes are readable anywhere — craft at a town Forge or Furnace.)"), 16, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER)
	_col().add_child(sub)
	var row := UI.hbox(16)
	UI.expand(row, true, true)
	_col().add_child(row)
	if tab == "research":
		var rv := UI.sub_panel(14)
		UI.expand(rv, true, true)
		var v := UI.vbox(10)
		rv.add_child(v)
		v.add_child(UI.label("Permanent doctrines, studied at a Research Desk.", 18))
		for r in C.RESEARCH:
			var h := UI.hbox(10)
			var cost := []
			for k in r.cost:
				cost.append("%d %s (%d)" % [r.cost[k], C.ITEMS[k].name, R.count(p, k)])
			var l := UI.label("%s — %s\nCost: %s, %d coins" % [r.name, r.desc, ", ".join(cost), r.coins], 17, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true)
			UI.expand(l)
			h.add_child(l)
			if p.research.get(r.id, false):
				h.add_child(UI.label("Learned", 18, UI.GREEN))
			else:
				var rid: String = r.id
				var b := UI.button("Research", func(): _act("research", {"id": rid}), 17, "gold")
				b.disabled = station != "research"
				h.add_child(b)
			v.add_child(h)
		row.add_child(rv)
		return
	var st_need := "forge" if tab == "smithing" else "furnace"
	var recipes := []
	for r in C.RECIPES:
		if r.tab == tab:
			recipes.append(r)
	var chosen: String = sel.get("recipe_" + tab, recipes[0].id)
	var lst := UI.sub_panel(10)
	lst.custom_minimum_size.x = 340
	var lv := UI.vbox(6)
	lst.add_child(lv)
	for r in recipes:
		var rid: String = r.id
		var out_id: String = r["out"].keys()[0]
		var ok_lv := S.prof_lv(p, r.skill) >= int(r.lv)
		var b := UI.icon_button(Icons.item(out_id), "", func():
			sel["recipe_" + tab] = rid
			refresh(), 44, 16)
		b.text = "  " + r.name + ("" if ok_lv else "   🔒 Lv %d" % r.lv)
		b.icon_alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.vertical_icon_alignment = VERTICAL_ALIGNMENT_CENTER
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(320, 56)
		if rid == chosen:
			b.add_theme_stylebox_override("normal", UI.box(Color("#2a2410"), UI.GOLD, 3, 6, 8))
		lv.add_child(b)
	row.add_child(UI.scroll(lst, 380))
	# station art
	var art := UI.sub_panel(8)
	UI.expand(art, true, true)
	var av := UI.vbox(6)
	art.add_child(av)
	av.add_child(UI.icon(Props.station(st_need).tex, 260))
	av.add_child(UI.label(("At the %s." % ("Forge" if st_need == "forge" else "Alchemy Furnace")) if station == st_need else "Visit a town %s to craft." % ("Forge" if st_need == "forge" else "Alchemy Furnace"), 17, UI.GREEN if station == st_need else UI.DIM, HORIZONTAL_ALIGNMENT_CENTER))
	var prog := UI.hbox(8)
	prog.alignment = BoxContainer.ALIGNMENT_CENTER
	var chain := [["copper", "Mine Copper"], ["bronze_ingot", "Smelt Bronze"], ["bronze_spear", "Forge Weapon"]] if tab == "smithing" else [["herb", "Gather Herbs"], ["mend_pill", "Brew Pills"], ["foundation_pill", "Break Through"]]
	for i in chain.size():
		var cv := UI.vbox(0)
		cv.add_child(UI.icon(Icons.item(chain[i][0]), 44))
		cv.add_child(UI.label(chain[i][1], 14, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER))
		prog.add_child(cv)
		if i < chain.size() - 1:
			prog.add_child(UI.label("→", 26, UI.JADE))
	av.add_child(prog)
	row.add_child(art)
	# details
	var r: Dictionary = R.find_recipe(chosen)
	if r.is_empty():
		r = recipes[0]
	var dp := UI.sub_panel(14)
	dp.custom_minimum_size.x = 400
	var dv := UI.vbox(8)
	dp.add_child(dv)
	dv.add_child(UI.label(r.name, 24, UI.GOLD))
	dv.add_child(UI.label(r.desc, 16, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
	dv.add_child(UI.label("Required Materials", 18, UI.JADE))
	var all_ok := true
	for k in r["in"]:
		var have := R.count(p, k)
		var need := int(r["in"][k])
		all_ok = all_ok and have >= need
		var h2 := UI.hbox(8)
		h2.add_child(UI.icon(Icons.item(k), 40))
		var vv := UI.vbox(0)
		vv.add_child(UI.label(C.ITEMS[k].name, 18))
		vv.add_child(UI.label("Source: " + str(C.ITEMS[k].get("source", "crafted")), 13, UI.DIM))
		UI.expand(vv)
		h2.add_child(vv)
		h2.add_child(UI.label("%d / %d" % [have, need], 20, UI.GREEN if have >= need else UI.RED))
		dv.add_child(h2)
	dv.add_child(UI.label("Result", 18, UI.JADE))
	for k in r["out"]:
		var h3 := UI.hbox(8)
		h3.add_child(UI.icon(Icons.item(k), 40))
		var rl := UI.label("%s ×%d — %s" % [C.ITEMS[k].name, r["out"][k], C.ITEMS[k].desc], 15, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true)
		UI.expand(rl)
		h3.add_child(rl)
		dv.add_child(h3)
	var lvok := S.prof_lv(p, r.skill) >= int(r.lv)
	dv.add_child(_req_row(lvok, "%s Lv %d" % [S.cap(r.skill), r.lv], "Lv %d" % S.prof_lv(p, r.skill)))
	var b2 := UI.button("CRAFT", func(): _act("craft", {"id": r.id, "station": station}), 24, "gold")
	b2.disabled = station != st_need or not all_ok or not lvok
	dv.add_child(b2)
	var b3 := UI.button("Craft ×5", func(): _act("craft", {"id": r.id, "station": station, "times": 5}), 17)
	b3.disabled = b2.disabled
	dv.add_child(b3)
	row.add_child(dp)


# ================================================================ journal
func _page_journal(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var tab := _tabs("journal", ["story", "commissions", "guidance", "lore"], ["Story", "Commissions", "Guidance", "Lore"])
	var pnl := UI.sub_panel(16)
	UI.expand(pnl, true, true)
	var v := UI.vbox(10)
	pnl.add_child(v)
	_col().add_child(UI.scroll(pnl, 400))
	match tab:
		"story":
			for ch in C.CHAPTERS:
				var q: Dictionary = p.quests[ch.id]
				v.add_child(UI.title("Chapter %s · %s" % [ch.num, ch.name], 26))
				if q.state == "unoffered":
					v.add_child(UI.label("Not yet begun. " + C.NPCS[ch.mentor].name + " awaits in " + C.AREAS[C.NPCS[ch.mentor].area].name + ".", 17, UI.DIM))
					continue
				for i in ch.steps.size():
					var s: Dictionary = ch.steps[i]
					var done: bool = q.state == "complete" or i < int(q.step)
					var cur: bool = q.state == "active" and i == int(q.step)
					if not done and not cur:
						v.add_child(UI.label("   ○ " + s.short, 16, UI.DIM))
						continue
					var txt: String = s.text
					if cur:
						var pr := R.step_progress(p, ch, i)
						if s.type in ["kill", "craft", "have"]:
							txt += "  (%d/%d)" % [pr.have, pr.need]
					v.add_child(UI.label(("   ✔ " if done else "   ◆ ") + txt, 18, UI.GREEN if done else Color("#ffe08a"), HORIZONTAL_ALIGNMENT_LEFT, true))
		"commissions":
			v.add_child(UI.label("Posted on town notice boards. Each can be completed %d times per day." % C.COMMISSION_DAILY_CAP, 17, UI.DIM))
			for town in C.COMMISSIONS:
				v.add_child(UI.label(C.AREAS[town].name, 20, UI.GOLD))
				for c in C.COMMISSIONS[town]:
					var cnt := int(p.commissions.counts.get(c.id, 0)) if p.commissions.day == R.today(Game.now()) else 0
					v.add_child(UI.label("   %s — %d coins, %d XP  (%d/%d today)" % [c.text, c.reward.coins, c.reward.xp, cnt, C.COMMISSION_DAILY_CAP], 16))
		"guidance":
			for g in C.GUIDANCE:
				v.add_child(UI.label("• " + g, 18, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
			v.add_child(UI.label("Keyboard: WASD/arrows move · Space jump · J attack · K step · L guard · 1/2/3 arts · F interact · Q/R pills · Tab mode · M map · Esc menu", 16, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
		"lore":
			for l in C.LORE:
				v.add_child(UI.label(l.title, 21, UI.GOLD))
				v.add_child(UI.label(l.text, 17, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))


# ================================================================ world map
func area_unlocked(id: String) -> bool:
	var ar: Dictionary = C.AREAS[id]
	return not ar.has("unlock") or Game.p.flags.get(ar.unlock, false)


func _page_map(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var overlay: String = tabs.get("map", "areas")
	var selected: String = sel.get("map", world.area_id if world and C.AREAS[world.area_id].has("mapPos") else "jr_town")
	var res_focus: String = sel.get("map_resource", "")
	var row := UI.hbox(16)
	UI.expand(row, true, true)
	_col().add_child(row)
	var mapbox := AspectRatioContainer.new()
	mapbox.ratio = 480.0 / 270.0
	UI.expand(mapbox, true, true)
	row.add_child(mapbox)
	var holder := Control.new()
	holder.clip_contents = true
	mapbox.add_child(holder)
	var tex := TextureRect.new()
	tex.texture = WorldMapArt.texture()
	tex.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tex.stretch_mode = TextureRect.STRETCH_SCALE
	tex.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	holder.add_child(tex)
	var routes := MapRoutes.new()
	routes.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	holder.add_child(routes)
	var here: String = world.area_id if world else ""
	for aid in C.MAP_AREAS:
		var ar: Dictionary = C.AREAS[aid]
		var unlocked := area_unlocked(aid)
		var dot := MapDot.new()
		dot.area = aid
		dot.state = "current" if aid == here else ("tracked" if p.tracked == aid else ("available" if unlocked else "locked"))
		dot.town = ar.type == "town"
		dot.selected = aid == selected
		dot.label = ar.name
		dot.norm = Vector2(ar.mapPos[0], ar.mapPos[1])
		if overlay == "resources":
			dot.res = []
			for n in ar.nodes:
				if p.discovered.nodes.has(n.id):
					var item: String = C.NODE_TYPES[n.type].item
					if not dot.res.has(item):
						dot.res.append(item)
			if res_focus != "" and ar.resources.has(res_focus):
				dot.highlight = true
		if overlay == "objectives":
			var ob := R.objective(p)
			if ob.chapter != null and C.NPCS[ob.chapter.mentor].area == aid:
				dot.highlight = true
		var target: String = aid
		dot.pressed.connect(func():
			sel["map"] = target
			refresh())
		holder.add_child(dot)
	# details panel
	var dp := UI.sub_panel(14)
	dp.custom_minimum_size.x = 360
	var dv := UI.vbox(8)
	dp.add_child(dv)
	var ar2: Dictionary = C.AREAS[selected]
	dv.add_child(UI.title(ar2.name, 26))
	dv.add_child(UI.label("%s · %s" % ["Town (safe)" if ar2.type == "town" else "Field", ar2.lv], 18, UI.CREAM, HORIZONTAL_ALIGNMENT_CENTER))
	dv.add_child(UI.sep_line())
	var unlocked2 := area_unlocked(selected)
	if not unlocked2:
		dv.add_child(UI.label("🔒 " + ("Complete Chapter I (River Outskirts) and speak with Elder Wen." if ar2.unlock == "ch1_done" else "Complete Chapter II (Whispering Bamboo) and speak with Archivist Suyin."), 17, Color("#ffb080"), HORIZONTAL_ALIGNMENT_LEFT, true))
	if ar2.has("mentor"):
		dv.add_child(UI.label("Mentor: " + C.NPCS[ar2.mentor].name + " · Forge · Furnace · Storage · Shrine", 15, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
	var disc_items := []
	for n in ar2.nodes:
		if p.discovered.nodes.has(n.id):
			var it: String = C.NODE_TYPES[n.type].item
			if not disc_items.has(it):
				disc_items.append(it)
	dv.add_child(UI.label("Discovered gatherables", 17, UI.JADE))
	var ir := HFlowContainer.new()
	for it in disc_items:
		var iv := UI.vbox(0)
		iv.add_child(UI.icon(Icons.item(it), 44))
		iv.add_child(UI.label(C.ITEMS[it].name, 13, UI.CREAM, HORIZONTAL_ALIGNMENT_CENTER))
		ir.add_child(iv)
	if disc_items.is_empty():
		ir.add_child(UI.label("None yet — explore to discover sites.", 15, UI.DIM))
	dv.add_child(ir)
	if not ar2.monsters.is_empty():
		dv.add_child(UI.label("Monsters: " + ", ".join(ar2.monsters), 15, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
	dv.add_child(UI.spacer(0, 0, true))
	var tb := UI.button("Track Route" if p.tracked != selected else "Tracking ✔", func():
		p.tracked = selected
		refresh(), 22, "jade")
	tb.disabled = not unlocked2
	dv.add_child(tb)
	var can_travel: bool = world != null and world.near_safe_travel() and unlocked2 and selected != here and (ar2.type == "town" or p.flags.get("rest_" + selected, false))
	var trb := UI.button("Travel", func():
		close()
		world.travel_to(selected), 20, "gold")
	trb.disabled = not can_travel
	dv.add_child(trb)
	dv.add_child(UI.label("Travel works from a safe shrine to an unlocked town or an activated field shrine. Otherwise, follow the portals.", 13, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
	row.add_child(dp)
	# overlay tabs + legend
	var bottom := UI.hbox(10)
	for t in [["areas", "Areas", "map"], ["resources", "Resources", "ore"], ["objectives", "Objectives", "quest"]]:
		var tn: String = t[0]
		var b := UI.button(t[1], func():
			tabs["map"] = tn
			refresh(), 18, "tab_on" if tn == overlay else "tab", 150)
		bottom.add_child(b)
	bottom.add_child(UI.spacer(20, 0, true))
	for lg in [[UI.JADE, "Available"], [UI.GOLD, "Current / tracked"], [Color("#5a5e5a"), "Locked"]]:
		var sw := ColorRect.new()
		sw.color = lg[0]
		sw.custom_minimum_size = Vector2(18, 18)
		bottom.add_child(sw)
		bottom.add_child(UI.label(lg[1], 16, UI.CREAM))
	bottom.add_child(UI.label("· · ·  Route", 16, UI.CREAM))
	_col().add_child(bottom)


class MapRoutes extends Control:
	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var C2 = preload("res://scripts/data/content.gd")
		var order: Array = C2.MAP_AREAS
		for i in order.size() - 1:
			var a: Array = C2.AREAS[order[i]].mapPos
			var b: Array = C2.AREAS[order[i + 1]].mapPos
			var pa := Vector2(a[0], a[1]) * size
			var pb := Vector2(b[0], b[1]) * size
			var n := int(pa.distance_to(pb) / 12)
			for k in n:
				draw_circle(pa.lerp(pb, float(k) / n), 3, Color(1, 0.95, 0.8, 0.85))


class MapDot extends Button:
	var area := ""
	var state := "available"
	var town := false
	var selected := false
	var label := ""
	var norm := Vector2.ZERO
	var res: Array = []
	var highlight := false

	func _ready() -> void:
		flat = true
		focus_mode = Control.FOCUS_NONE
		custom_minimum_size = Vector2(210, 64)
		size = custom_minimum_size

	func _process(_d: float) -> void:
		var par := get_parent() as Control
		position = norm * par.size - Vector2(size.x / 2, 20)
		queue_redraw()

	func _draw() -> void:
		var c := Vector2(size.x / 2, 20)
		var col: Color = {"current": UI.GOLD, "tracked": UI.GOLD, "available": UI.JADE, "locked": Color("#5a5e5a")}[state]
		var t := Time.get_ticks_msec() / 1000.0
		if state == "current":
			draw_arc(c, 20 + sin(t * 3) * 3, 0, TAU, 32, Color(col, 0.7), 3)
		if highlight:
			draw_arc(c, 26, 0, TAU, 32, Color("#ffffff"), 2)
		if selected:
			draw_arc(c, 23, 0, TAU, 32, Color("#fff2c0"), 2)
		draw_circle(c, 15, Color(0, 0, 0, 0.6))
		if town:
			draw_colored_polygon(PackedVector2Array([c + Vector2(-13, 4), c + Vector2(0, -12), c + Vector2(13, 4)]), col)
			draw_rect(Rect2(c + Vector2(-8, 3), Vector2(16, 8)), col.darkened(0.3))
		else:
			draw_circle(c, 11, col)
			draw_circle(c, 5, col.lightened(0.5))
		if state == "locked":
			var li := Icons.get_icon("lock")
			draw_texture_rect(li, Rect2(c - Vector2(10, 10), Vector2(20, 20)), false)
		var fnt := UI.font()
		var w := size.x
		draw_rect(Rect2(8, 38, w - 16, 24), Color(0.05, 0.08, 0.09, 0.85))
		draw_rect(Rect2(8, 38, w - 16, 24), Color("#8a8e8a"), false, 1)
		draw_string(fnt, Vector2(8, 56), label, HORIZONTAL_ALIGNMENT_CENTER, w - 16, 15, UI.CREAM)
		for i in res.size():
			draw_texture_rect(Icons.item(res[i]), Rect2(Vector2(w / 2 + 16 + i * 18, 2), Vector2(18, 18)), false)


# ================================================================ settings
func _page_settings(_a: Dictionary) -> void:
	var s: Dictionary = Game.settings
	var pnl := UI.sub_panel(18)
	UI.expand(pnl, true, true)
	var v := UI.vbox(14)
	pnl.add_child(v)
	_col().add_child(pnl)
	var toggle := func(key: String, text: String) -> void:
		var h := UI.hbox(10)
		var l := UI.label(text, 20)
		UI.expand(l)
		h.add_child(l)
		h.add_child(UI.button("On" if s[key] else "Off", func():
			s[key] = not s[key]
			Game.save_now()
			refresh(), 18, "tab_on" if s[key] else "tab", 100))
		v.add_child(h)
	toggle.call("left_handed", "Left-handed controls (stick right, actions left)")
	toggle.call("show_stick", "Show joystick anchor when idle")
	toggle.call("reduce_fx", "Reduce screen shake")
	var hs := UI.hbox(10)
	var l2 := UI.label("Touch button size: %d%%" % int(float(s.button_scale) * 100), 20)
	UI.expand(l2)
	hs.add_child(l2)
	for sc in [0.85, 1.0, 1.15, 1.3]:
		var scv: float = sc
		hs.add_child(UI.button("%d%%" % int(sc * 100), func():
			s.button_scale = scv
			Game.save_now()
			refresh(), 17, "tab_on" if absf(float(s.button_scale) - sc) < 0.01 else "tab", 80))
	v.add_child(hs)
	v.add_child(UI.sep_line())
	var h2 := UI.hbox(12)
	h2.add_child(UI.button("Save now", func():
		Game.save_now()
		hud.toast("Saved.", "ok"), 20))
	h2.add_child(UI.button("Switch disciple", func():
		Game.save_now()
		close()
		to_title.emit(), 20, "gold"))
	v.add_child(h2)
	v.add_child(UI.label("Jade River: The Broken Seal · v%s · offline single-player build · local save %s" % [ProjectSettings.get_setting("application/config/version"), Game.save_path], 14, UI.DIM, HORIZONTAL_ALIGNMENT_LEFT, true))


# ================================================================ stations
func _page_shop(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var shop: String = C.AREAS[world.area_id].get("shop", "jr_town")
	var row := UI.hbox(16)
	UI.expand(row, true, true)
	_col().add_child(row)
	var buy := UI.sub_panel(12)
	UI.expand(buy, true, true)
	var bv := UI.vbox(8)
	buy.add_child(bv)
	bv.add_child(UI.label("For sale — emergency supplies at a premium", 20, UI.GOLD))
	for id in C.SHOPS[shop]:
		var h := UI.hbox(10)
		h.add_child(UI.icon(Icons.item(id), 40))
		var l := UI.label("%s — %s" % [C.ITEMS[id].name, C.ITEMS[id].desc], 16, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true)
		UI.expand(l)
		h.add_child(l)
		var iid: String = id
		var b := UI.button("Buy · %d" % R.buy_price(id), func(): _act("buy", {"id": iid, "shop": shop}), 16, "gold")
		b.disabled = p.coins < R.buy_price(id)
		h.add_child(b)
		bv.add_child(h)
	row.add_child(UI.scroll(buy, 400))
	var sell := UI.sub_panel(12)
	sell.custom_minimum_size.x = 420
	var sv := UI.vbox(8)
	sell.add_child(sv)
	sv.add_child(UI.label("Sell from your bag (half value)", 20, UI.GOLD))
	for id in p.items:
		var d: Dictionary = C.ITEMS[id]
		if d.kind == "quest" or (d.kind == "tool" and int(d.value) == 0):
			continue
		var h2 := UI.hbox(8)
		h2.add_child(UI.icon(Icons.item(id), 34))
		var l2 := UI.label("%s ×%d" % [d.name, p.items[id]], 16)
		UI.expand(l2)
		h2.add_child(l2)
		var sid: String = id
		h2.add_child(UI.button("Sell · %d" % maxi(1, int(d.value) / 2), func(): _confirm_sell(sid), 15))
		sv.add_child(h2)
	row.add_child(UI.scroll(sell, 400))


func _page_storage(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var row := UI.hbox(16)
	UI.expand(row, true, true)
	_col().add_child(row)
	for side in ["bag", "bank"]:
		var pnl := UI.sub_panel(12)
		UI.expand(pnl, true, true)
		var v := UI.vbox(6)
		pnl.add_child(v)
		v.add_child(UI.label("Your bag" if side == "bag" else "Shared storage (all three disciples)", 20, UI.GOLD))
		var src: Dictionary = p.items if side == "bag" else Game.save.bank
		for id in src:
			var d: Dictionary = C.ITEMS[id]
			if side == "bag" and (d.kind == "quest" or d.kind == "tool"):
				continue
			var h := UI.hbox(8)
			h.add_child(UI.icon(Icons.item(id), 34))
			var l := UI.label("%s ×%d" % [d.name, src[id]], 16)
			UI.expand(l)
			h.add_child(l)
			var iid: String = id
			var n := int(src[id])
			if side == "bag":
				h.add_child(UI.button("Deposit 1", func(): _act("deposit", {"id": iid, "n": 1}), 15))
				h.add_child(UI.button("All", func(): _act("deposit", {"id": iid, "n": n}), 15))
			else:
				h.add_child(UI.button("Take 1", func(): _act("withdraw", {"id": iid, "n": 1}), 15))
				h.add_child(UI.button("All", func(): _act("withdraw", {"id": iid, "n": n}), 15))
			v.add_child(h)
		row.add_child(UI.scroll(pnl, 400))


func _page_board(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var town: String = world.area_id
	var pnl := UI.sub_panel(16)
	UI.expand(pnl, true, true)
	var v := UI.vbox(10)
	pnl.add_child(v)
	_col().add_child(pnl)
	v.add_child(UI.label("Repeatable commissions — capped at %d per day each." % C.COMMISSION_DAILY_CAP, 18, UI.DIM))
	for c in C.COMMISSIONS.get(town, []):
		var h := UI.hbox(12)
		var cnt := int(p.commissions.counts.get(c.id, 0)) if p.commissions.day == R.today(Game.now()) else 0
		var status := ""
		if c.has("kill"):
			var type: String = c.kill.keys()[0]
			if p.commissions.active.has(c.id):
				status = "  — progress %d/%d" % [int(p.stats.kills.get(type, 0)) - int(p.commissions.active[c.id]), c.kill[type]]
		else:
			var parts := []
			for k in c.give:
				parts.append("%d/%d %s" % [R.count(p, k), c.give[k], C.ITEMS[k].name])
			status = "  — " + ", ".join(parts)
		var l := UI.label("%s%s\nReward: %d coins, %d XP · %d/%d today" % [c.text, status, c.reward.coins, c.reward.xp, cnt, C.COMMISSION_DAILY_CAP], 17, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true)
		UI.expand(l)
		h.add_child(l)
		var cid: String = c.id
		var label := "Deliver" if c.has("give") else ("Claim" if p.commissions.active.has(c.id) else "Accept")
		var b := UI.button(label, func(): _act("commission", {"town": town, "id": cid}), 18, "gold")
		b.disabled = cnt >= C.COMMISSION_DAILY_CAP
		h.add_child(b)
		v.add_child(h)


func _page_shrine(_a: Dictionary) -> void:
	_shrine_common(true)


func _page_rest(_a: Dictionary) -> void:
	_shrine_common(false)


func _shrine_common(town: bool) -> void:
	var p: Dictionary = Game.p
	var pnl := UI.sub_panel(16)
	UI.expand(pnl, true, true)
	var v := UI.vbox(12)
	pnl.add_child(v)
	_col().add_child(pnl)
	v.add_child(UI.label(("A sanctuary shrine. Safe for meditation, breakthroughs, travel and assignments." if town else "A roadside shrine — now a safe travel point. Meditate here when no enemies are near."), 18, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true))
	var h := UI.hbox(12)
	h.add_child(UI.button("Meditate", func():
		close()
		hud.set_mode("cultivation")
		world.ctl.meditate = true, 20, "jade", 180))
	h.add_child(UI.button("Cultivation", func(): open("cultivation"), 20))
	h.add_child(UI.button("World Map · Travel", func(): open("map"), 20))
	if town:
		h.add_child(UI.button("Assignments", func():
			tabs["gathering"] = "mining"
			open("gathering"), 20))
	v.add_child(h)
	var br = R.breakthrough_reqs(p)
	if br != null:
		var ready := true
		for q in br.list:
			ready = ready and q.ok
		v.add_child(UI.label(("Your Qi is ready for %s!" % br.realm.name) if ready else "Next realm: %s — see the Cultivation page for what is missing." % br.realm.name, 18, UI.GOLD if ready else UI.DIM))


# ================================================================ defeat / class / dao
func _page_death(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	back_btn.visible = false
	var v := UI.vbox(14)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	UI.expand(v, true, true)
	_col().add_child(v)
	v.add_child(UI.label("You fall — but equipment, XP, realm and materials are kept.", 20, UI.CREAM, HORIZONTAL_ALIGNMENT_CENTER, true))
	var cost := R.revive_cost(p)
	var b1 := UI.button("Revive at the sanctuary (free)", func():
		close()
		world.revive("sanctuary"), 22, "jade")
	v.add_child(b1)
	var b2 := UI.button("Revive here · %d coins" % cost, func():
		close()
		world.revive("here"), 22, "gold")
	b2.disabled = p.coins < cost
	v.add_child(b2)


func _page_class(_a: Dictionary) -> void:
	var p: Dictionary = Game.p
	var v := UI.vbox(12)
	UI.expand(v, true, true)
	_col().add_child(v)
	v.add_child(UI.label("Disciplines grant bonuses, never exclusive weapons." + ("" if p.cls == null else " Retraining costs %d coins." % C.CLASS_RETRAIN_FEE), 17, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER, true))
	for id in C.CLASSES:
		var cd: Dictionary = C.CLASSES[id]
		var h := UI.hbox(12)
		var l := UI.label("%s — %s" % [cd.name, cd.desc], 18, UI.GOLD if p.cls == id else UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true)
		UI.expand(l)
		h.add_child(l)
		var cid: String = id
		var b := UI.button("Current" if p.cls == id else "Choose", func():
			var r := _act("choose_class", {"cls": cid})
			if r.ok:
				close(), 18, "gold")
		b.disabled = p.cls == id
		h.add_child(b)
		v.add_child(h)


func _page_dao(_a: Dictionary) -> void:
	var v := UI.vbox(12)
	UI.expand(v, true, true)
	_col().add_child(v)
	for id in C.DAOS:
		var d: Dictionary = C.DAOS[id]
		var h := UI.hbox(12)
		var l := UI.label("%s\n%s" % [d.name, d.desc], 18, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true)
		UI.expand(l)
		h.add_child(l)
		var did: String = id
		h.add_child(UI.button("Follow", func():
			var r := _act("choose_dao", {"id": did})
			if r.ok:
				close(), 18, "gold"))
		v.add_child(h)


# ================================================================ dialogue box
func _build_dialogue() -> void:
	dlg = UI.panel(Color("#0d2020"), UI.GOLD, 16)
	dlg.visible = false
	add_child(dlg)
	var v := UI.vbox(8)
	dlg.add_child(v)
	dlg_name = UI.label("", 22, UI.GOLD)
	v.add_child(dlg_name)
	dlg_label = UI.label("", 20, UI.CREAM, HORIZONTAL_ALIGNMENT_LEFT, true)
	dlg_label.custom_minimum_size = Vector2(700, 80)
	v.add_child(dlg_label)
	dlg_buttons = UI.hbox(10)
	dlg_buttons.alignment = BoxContainer.ALIGNMENT_END
	v.add_child(dlg_buttons)


func show_dialogue(npc: String, lines: Array, menu: Array) -> void:
	dlg_npc = npc
	dlg_lines = lines
	dlg_menu = menu
	dlg_i = 0
	dlg.visible = true
	dim.visible = true
	if world:
		world.paused = true
		world.ctl.reset()
	_dlg_render()


func _dlg_render() -> void:
	var W := get_viewport_rect().size.x
	var H := get_viewport_rect().size.y
	dlg.position = Vector2(W * 0.5 - 460, H - 250)
	dlg.custom_minimum_size = Vector2(920, 200)
	dlg.size = Vector2(920, 200)
	var line: String = dlg_lines[dlg_i] if dlg_i < dlg_lines.size() else ""
	var nm := ""
	var sp := line.find(": ")
	if sp > 0 and sp < 24:
		nm = line.substr(0, sp)
		line = line.substr(sp + 2)
	dlg_name.text = nm if nm != "" else (C.NPCS[dlg_npc].name if C.NPCS.has(dlg_npc) else "")
	dlg_label.text = line
	UI.clear(dlg_buttons)
	var last := dlg_i >= dlg_lines.size() - 1
	if last:
		for m in dlg_menu:
			var mm: String = m
			dlg_buttons.add_child(UI.button("Choose discipline" if m == "class" else "Choose a Dao", func():
				_end_dialogue()
				open(mm), 18, "jade"))
	dlg_buttons.add_child(UI.button("Continue ›" if not last else "Close", func():
		if last:
			_end_dialogue()
		else:
			dlg_i += 1
			_dlg_render(), 18, "gold", 150))


func _end_dialogue() -> void:
	dlg.visible = false
	dim.visible = frame.visible
	if world and not frame.visible:
		world.paused = false
