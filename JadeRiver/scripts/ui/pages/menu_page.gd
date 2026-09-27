extends Page
## Main hub (Part 9.6 · Core hub/menu pages). Locked entries stay visible, dimmed,
## and explain their unlock on tap.
## P5 (docs/page_identity.md row 4, mockup 03, approved): the sect's hall of hanging plaques. Five bays under their
## plaques between red-lacquered pillars, each entry a teal lacquer tablet hung on the bay's gold cord: its seal and
## glyph, its name, and a line when something waits there (the bottleneck, chests to claim, a letter's sender, who asks
## to join, the rank held, what opens a locked one); a vermilion ready seal, the Mail's count or a new mark in its
## corner. The character line and the purses stand on the hall's floor. The tablets settle with one sway as the page
## opens and a ready seal is pressed on; under Reduce motion the page only fades in.

const SectKit = preload("res://scripts/ui/pages/sect_kit.gd")

var ENTRIES := [
	["character", Tx.t("ui.menu.character"), "character", "character_menu"],
	["cultivation", Tx.t("ui.menu.cultivation"), "cultivation", "cultivation"],
	["techniques", Tx.t("ui.menu.techniques"), "techniques", "technique_slots_2"],
	["inventory", Tx.t("ui.menu.bag"), "bag", "bag"],
	["quests", Tx.t("ui.menu.quests"), "quest", "navigation"],
	["world_map", Tx.t("ui.menu.map"), "world_map", "world_menu"],
	["calendar", Tx.t("ui.menu.calendar"), "calendar", "world_menu"],
	["training_sect", Tx.t("ui.menu.sect"), "sect", "sect_choice"],
	["your_sect", Tx.t("ui.menu.your_sect"), "account", "your_sect"],
	["spirit_animals", Tx.t("ui.menu.spirit_animals"), "spirit_animals", "spirit_animals"],
	["companions", Tx.t("ui.menu.companions"), "characters", "companions"],
	["crafts", Tx.t("ui.menu.crafts"), "crafts", "herb_gathering"],
	["workshop", Tx.t("ui.menu.workshop"), "formation", "appraisal"],
	["characters", Tx.t("ui.menu.characters"), "characters", "idle_tasks"],
	["posts", Tx.t("ui.menu.roll_call"), "roll_call", "keeping_post"],   # S50 Keeping Post: the Roll-Call
	["works", Tx.t("ui.menu.works"), "works", "post_arts"],   # S50 V10d: the account web
	["codex", Tx.t("ui.menu.codex"), "codex", "codex"],   # Collection and Achievements are Codex tabs
	["mail", Tx.t("ui.menu.mail"), "mail", "mail"],
	["emotes", Tx.t("ui.menu.emotes"), "talk", ""],
	["settings", Tx.t("ui.menu.settings"), "settings", ""],
	["exit", Tx.t("ui.menu.save_exit"), "back", ""],
]

## The five bays of the hall (mockup 03), each [its plaque's string, the entries hung in it].
const BAYS := [["ui.menu.bay_self", ["character", "cultivation", "techniques", "inventory"]],
	["ui.menu.bay_world", ["quests", "world_map", "calendar", "codex"]],
	["ui.menu.bay_bonds", ["spirit_animals", "companions", "training_sect", "your_sect", "characters"]],
	["ui.menu.bay_works", ["crafts", "workshop", "posts", "works"]],
	["ui.menu.bay_system", ["mail", "emotes", "settings", "exit"]]]
## The hall inside the window: the lattice frieze along its top, the floor along its foot.
const HALL := Rect2(92, 108, 1096, 556)
const FRIEZE := 14.0
const FLOOR := 60.0
const BAY_W := 200.0
const BAY_PITCH := 220.0
const PLAQUE_H := 46.0
const TABLET_H := 64.0
const TABLET_PITCH := 80.0
const SEAL_S := 0.15   # a ready seal is pressed on over this long

func _init() -> void:
	title = Tx.t("ui.menu.menu")
	identity = Identity.new("river_lacquer", true, "plaque", "bays_of_hanging_tablets", 0.25)

func content_rect() -> Rect2:
	return HALL

func draw_surface(_r: Rect2) -> void:
	# The hall's lacquered wall, lit from above, with its lattice frieze and the floor's boards.
	vshade(HALL, UiKit.SURFACE.river_lacquer, UiKit.SURFACE.space.lerp(UiKit.INK, 0.3))
	glow(Rect2(HALL.get_center().x - 420, HALL.position.y - 160, 840, 360), Color(UiKit.GOLD, 0.10 * _halo()))
	ground(HALL, UiKit.SURFACE.river_lacquer)
	var fr := Rect2(HALL.position, Vector2(HALL.size.x, FRIEZE))
	PostKit.lattice(self, fr, Color(UiKit.BRIGHT_JADE, 0.08), 10.0)
	draw_rect(Rect2(fr.position.x, fr.end.y, fr.size.x, 2), Color(UiKit.BRONZE, 0.7))
	var fl := Rect2(HALL.position.x, HALL.end.y - FLOOR, HALL.size.x, FLOOR)
	vshade(fl, UiKit.JADE_SHADOW.lerp(UiKit.SURFACE.space, 0.7), UiKit.SURFACE.space.lerp(UiKit.INK, 0.4))
	draw_rect(Rect2(fl.position, Vector2(fl.size.x, 2)), Color(UiKit.BRONZE, 0.55))
	for x in range(int(fl.position.x) + 64, int(fl.end.x), 64): draw_rect(Rect2(x, fl.position.y + 2, 1, FLOOR - 2), Color(UiKit.MIST, 0.05))
	ground(fl, UiKit.JADE_SHADOW.lerp(UiKit.SURFACE.space, 0.7))
	draw_rect(HALL, Color(UiKit.BRONZE, 0.5), false, 1.0)
	# The red-lacquered pillars between the bays, a lantern's light at each capital.
	for i in range(1, BAYS.size()):
		var x := HALL.position.x + 8.0 + i * BAY_PITCH - (BAY_PITCH - BAY_W) * 0.5
		glow(Rect2(x - 30, HALL.position.y + 12, 60, 60), Color(UiKit.PALE_GOLD, 0.3 * _halo()))
		SectKit.pillar(self, Rect2(x - 5, HALL.position.y + FRIEZE, 10, HALL.size.y - FRIEZE - FLOOR))

func _bay_x(i: int) -> float:
	return HALL.position.x + 8.0 + i * BAY_PITCH

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var byid := {}
	for e in ENTRIES: byid[str(e[0])] = e
	var seals := ready_seals(ch)
	var k := unfold()
	for b in BAYS.size():
		var x := _bay_x(b)
		var ids: Array = BAYS[b][1]
		var top := HALL.position.y + 20.0
		# The cord down the bay, behind its tablets.
		var cord_end := top + PLAQUE_H + 16.0 + (ids.size() - 1) * TABLET_PITCH
		draw_line(Vector2(x + BAY_W * 0.5, top + PLAQUE_H), Vector2(x + BAY_W * 0.5, cord_end), Color(UiKit.INK, 0.6), 4.0)
		draw_line(Vector2(x + BAY_W * 0.5, top + PLAQUE_H), Vector2(x + BAY_W * 0.5, cord_end), UiKit.GOLD.lerp(UiKit.BRONZE, 0.5), 2.0)
		var plaque := Rect2(x, top, BAY_W, PLAQUE_H)
		face(plaque, "title_plaque")
		inked(Vector2(x, top + PLAQUE_H * 0.5 + 11), Tx.t(str(BAYS[b][0])), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, BAY_W)
		for j in ids.size():
			var r := Rect2(x, top + PLAQUE_H + 16.0 + j * TABLET_PITCH, BAY_W, TABLET_H)
			# One sway as the page opens: each tablet swings about its cord's knot above it, the lower ones a beat later.
			var sway := sin((k * 1.6 - j * 0.12) * PI * 2.0) * (1.0 - k) * 0.05 if k < 1.0 else 0.0
			var pivot := Vector2(r.get_center().x, r.position.y - 16.0)
			move(pivot - pivot.rotated(sway), sway)
			_tablet(ch, byid[ids[j]], r, seals)
			move()
	# The character line and the purses on the hall's floor.
	var y := HALL.end.y - 22.0
	text(Vector2(HALL.position.x + 24, y), str(ch.name), 20, UiKit.PAPER)
	text(Vector2(HALL.position.x + 32 + UiKit.text_width(str(ch.name), 20), y), "· %s" % ContentDB.realm_label(ch.cultivator.realm_key, ProgressionRules.level(ch)), 20, UiKit.MIST)
	var px := HALL.end.x - 24
	for cur in ["silver_tael", "spirit_stone", "contribution"]:
		if cur == "contribution" and str(ch.training_sect.get("id", "")) == "": continue
		var amt := Game.economy.balance(cur, ch)
		px -= UiKit.text_width(UiKit.fmt(amt), 18) + 54
		currency_pill(Vector2(px, y - 25), cur, amt)
		px -= 8

## One entry's tablet: the lacquer face, its seal with the glyph, the name and the line under it, and its corner mark.
func _tablet(ch, e: Array, r: Rect2, seals: Dictionary) -> void:
	var id := str(e[0])
	var locked: bool = e[3] != "" and not Unlocks.is_unlocked(ch.id, e[3])
	face(r, "minor_panel", "disabled" if locked else ("pressed" if _is_pressed("open", id) else "normal"))
	var sc := r.position + Vector2(29, 32)
	draw_circle(sc, 25.0, UiKit.INK, true, -1.0, true)
	draw_circle(sc, 24.0, UiKit.BRONZE if not locked else UiKit.HOLLOW.lerp(UiKit.INK, 0.4), true, -1.0, true)
	draw_circle(sc, 22.0, UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.45) if not locked else UiKit.SURFACE.stone.lerp(UiKit.INK, 0.5), true, -1.0, true)
	draw_circle(sc + Vector2(-5, -6), 11.0, Color(UiKit.JADE, 0.18 if not locked else 0.0), true, -1.0, true)
	icon_at(Rect2(sc - Vector2(16, 16), Vector2(32, 32)), str(e[2]), Color(1, 1, 1, 0.4) if locked else Color.WHITE)
	if locked: _lock_icon(sc + Vector2(8, 4))
	var line := Unlocks.locked_text(e[3]) if locked else line_of(ch, id)
	var nx := r.position.x + 60.0
	var nw := r.end.x - nx - 8.0
	var ns := 20
	while ns > 16 and UiKit.text_width(str(e[1]), ns) > nw: ns = UiKit.step_down(ns)
	if line == "":
		text(Vector2(nx, r.position.y + 39), str(e[1]), ns, UiKit.HOLLOW if locked else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, nw)
	else:
		text(Vector2(nx, r.position.y + 29), str(e[1]), ns, UiKit.HOLLOW if locked else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, nw)
		text(Vector2(nx, r.position.y + 50), line, 14, UiKit.HOLLOW if locked else (UiKit.PALE_GOLD if seals.has(id) else UiKit.MIST), HORIZONTAL_ALIGNMENT_LEFT, nw)
	var corner := Vector2(r.end.x - 4, r.position.y + 2)
	if not locked:
		if id == "mail" and Game.mail.unread(ch) > 0: UiKit.count_badge(self, corner, Game.mail.unread(ch))
		elif seals.has(id): UiKit.ready_seal(self, corner, lerpf(1.6, 1.0, unfold(SEAL_S)))
		elif id == "your_sect" and Game.sect.founded() and not (Game.sect.sect().get("candidates", []) as Array).is_empty(): UiKit.new_mark(self, corner + Vector2(-2, 4))
	region(r, "open", id, not locked, Unlocks.locked_text(e[3]) if locked else "")

## The entries where something waits to be done, each with its ready seal (the HUD's Menu button carries one while any
## does): the bottleneck reached (Cultivation), and the day's activity chests full and not yet opened (Quests).
static func ready_seals(ch) -> Dictionary:
	var out := {}
	if ch == null: return out
	if ch.cultivator.state == "bottleneck": out["cultivation"] = true
	if _chests(ch) > 0: out["quests"] = true
	return out

static func _chests(_ch) -> int:
	var n := 0
	for row in ContentDB.all("activity"):
		if Game.accounts.chest_ready(str(row.id)): n += 1
	return n

## The line under an entry's name: what waits there, or what it holds ("" for none).
static func line_of(ch, id: String) -> String:
	match id:
		"cultivation":
			if ch.cultivator.state == "bottleneck": return Tx.t("ui.menu.bottleneck")
		"techniques":
			var n := ProgressionRules.technique_slot_count(ch)
			if n > 0:
				var used := 0
				for s in (ch.cultivator.technique_slots as Array).slice(0, n):
					if s != null and str(s) != "": used += 1
				return Tx.t("ui.menu.slots_set") % [used, n]
		"quests":
			var chests := _chests(ch)
			if chests > 0: return Tx.plural("ui.menu.chests", chests) % chests
		"training_sect":
			if str(ch.training_sect.get("id", "")) != "": return ContentDB.rank_name(str(ch.training_sect.get("rank", "")))
		"your_sect":
			if Game.sect.founded():
				var cands: Array = Game.sect.sect().get("candidates", [])
				if not cands.is_empty(): return Tx.plural("ui.menu.ask_to_join", cands.size()) % (str(cands[0].get("name", "")) if cands.size() == 1 else str(cands.size()))
		"mail":
			var unread: Array = Game.mail.visible(ch).filter(func(m): return not m.get("read", false))
			if not unread.is_empty(): return Tx.t("ui.menu.mail_from") % str(unread.back().get("from", ""))
	return ""

func on_action(id: String, data) -> void:
	if id == "exit_yes":
		navigate.emit("_exit", {})
		return
	if id != "open": return
	if data == "exit":
		ask(Tx.t("ui.menu.save_and_return_to_character"), "exit_yes")
		return
	navigate.emit(str(data), {})

func on_event(name: String, _p: Dictionary) -> void:
	queue_redraw()
