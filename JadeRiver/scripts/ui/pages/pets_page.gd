extends Page
## Spirit animals (S22): roster, active animal, role, bond and feeding; growth, breeding, fusion, pet gear and the eggs
## (S46); the Copperjaw swarm (v1.2 Phase D).
## P5 (docs/page_identity.md row 16, mockup 10; the Beasts family, §2): the bestiary. The kit's window keeps its plaque
## and tabs (Stable, Swarm). Down the left, the animals beside you on their posts and the stable, one stall a row with
## its animal looking out; in the middle the chosen animal's leaf, a paper sheet between two rollers, with the animal
## stood on its straw, its level and bond as hearts, its growth as stepping stones with the next stage's gates, its
## bloodline with the stops at 50 and 90, its skills and traits; the leaf's foot turns its lower half to Grow, Feed,
## Teach, Breed or Fuse. At the right, the tack wall: care (out or at rest, beside you, carried; the roles), gear, the
## nest and the swarm. A chosen animal walks out onto its leaf (0.4 s). The page submits intents only.

const LEAF := Rect2(376, 176, 496, 484)    # the paper, inside its rollers
const LX := 394.0                          # the leaf's writing column
const LW := 462.0
const RX := 888.0                          # the tack wall
const RW := 300.0
const WALK_S := 0.4
const VIEWS := ["grow", "feed", "teach", "breed", "fuse"]

var sel := ""
var view := ""            # the leaf's lower half: "" its record, or one of VIEWS, or "gear" (a piece to wear)
var support: Array = []   # breakthrough support items picked (S46)
var chose_t := -1.0       # when the shown animal was chosen (it walks out onto its leaf)
var name_edit: LineEdit   # renaming the selected animal

func _init() -> void:
	title = Tx.t("ui.pets.spirit_animals")
	tabs = [{"id": "stable", "label": Tx.t("ui.pets.tab_stable")}]
	identity = Identity.new("river_lacquer", true, "plaque", "stall_column_leaf_tack_wall", 0.3)

func setup() -> void:
	_add_swarm_tab(c())

## v1.2 Phase D: the Copperjaw swarm gets its own tab once its box is in hand.
func _add_swarm_tab(ch) -> void:
	if ch != null and Unlocks.is_unlocked(ch.id, "beetle_swarm") and not tabs.any(func(tb): return str(tb.id) == "swarm"):
		tabs.append({"id": "swarm", "label": Tx.t("ui.pets.tab_swarm")})

func content_rect() -> Rect2:
	return Rect2(92, 176, 1096, 488)

## The window stays the kit's own (mockup 10); words sit on its panels, the leaf and the slots, each named as drawn.
func draw_surface(r: Rect2) -> void:
	ground(r, UiKit.SURFACE[identity.surface])

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	_add_swarm_tab(ch)
	if str(tabs[tab].id) == "swarm":
		_swarm_tab(ch, content)
		return
	# Open on the active animal (or the first one) instead of an empty leaf.
	if not ch.pets.is_empty() and not ch.pets.any(func(p): return str(p.uid) == sel):
		sel = ch.active_pet if ch.active_pet != "" else str(ch.pets[0].uid)
	var pet := {}
	for p in ch.pets:
		if str(p.uid) == sel: pet = Game.pets.filled(p)
	_command_line(ch)
	_posts(ch, pet)
	_stable(ch)
	_leaf(ch, pet)
	_tack(ch, pet)

## A heading of the tack wall or the stable: gold capitals, and its count after it in mist.
func _section(at: Vector2, words: String, after := "") -> void:
	var s := words.to_upper()
	text(at, s, 14, UiKit.GOLD)
	if after != "": text(at + Vector2(UiKit.text_width(s, 14) + 6, 0), "· " + after, 14, UiKit.MIST)

## Across from the tabs: how many your Soul commands, and when it commands more.
func _command_line(ch) -> void:
	var cap: int = Game.pets.command_capacity(ch)
	var line := Tx.t("ui.pets.capacity_full") % cap
	for step in ContentDB.config("pet_growth").get("command", []):
		if int(step.get("count", 1)) > cap:
			line = Tx.t("ui.pets.command_next") % [int(step.count), ContentDB.name_of("realms", str(step.realm))]
			break
	text(Vector2(700, 146), line, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 488)

# ------------------------------------------------------------------ the posts and the stable
func _posts(ch, pet: Dictionary) -> void:
	var party: Array = Game.pets.party(ch)
	var cap: int = Game.pets.command_capacity(ch)
	var steps: Array = ContentDB.config("pet_growth").get("command", [])
	var posts := 1
	for step in steps: posts = maxi(posts, int(step.get("count", 1)))
	_section(Vector2(94, 190), Tx.t("ui.pets.beside_you"), Tx.t("ui.pets.of_posts") % [party.size(), cap])
	for i in mini(posts, 3):
		var r := Rect2(92 + i * 84, 196, SLOT, SLOT)
		if i < party.size():
			var p: Dictionary = party[i]
			draw_style_box(UiKit.style("slot", "selected" if str(p.uid) == sel else "normal"), r)
			creature_at(r.grow(-8), _art(p), "idle")
			if str(p.uid) == sel: draw_style_box(UiKit.style("selected_slot_glow"), r.grow(4))
			region(r, "sel", str(p.uid))
			continue
		draw_style_box(UiKit.style("slot", "normal" if i < cap else "disabled"), r)
		if i >= cap:
			_lock_icon(r.get_center() - Vector2(9, 12), 1.5)
			var opens := ""
			for step in steps:
				if int(step.get("count", 1)) > i:
					opens = Tx.t("ui.pets.post_opens") % ContentDB.name_of("realms", str(step.realm))
					break
			region(r, "post", null, false, opens)
			continue
		# An open post: the chosen animal steps up to it (out, if none is; beside you, if one is).
		draw_arc(r.get_center(), 18.0, 0.0, TAU, 28, Color(UiKit.MIST, 0.35), 2.0, true)
		if pet.is_empty():
			region(r, "post", null, false, Tx.t("ui.pets.no_spirit_animals_yet_hermit"))
		elif ch.active_pet == "":
			region(r, "active", sel, not Game.pets.mount_only(pet), Tx.t("sim.pet.mount_only") % str(pet.name))
		else:
			var why := ""
			if ch.active_pet == sel or ch.party_pets.has(sel): why = Tx.t("ui.pets.already_beside") % str(pet.name)
			elif str(pet.get("role", "")) in ["guard", "mount"] or Game.pets.mount_only(pet): why = Tx.t("sim.pet.party_busy") % str(pet.name)
			region(r, "party", true, why == "", why)
	var out: Dictionary = Game.pets.active_pet(ch)
	text(Vector2(94, 290), fit(Tx.t("ui.pets.is_out") % str(out.name) if not out.is_empty() else Tx.t("ui.pets.none_out"), 14, 150), 14,
		UiKit.BRIGHT_JADE if not out.is_empty() else UiKit.MIST)
	var open := maxi(0, cap - party.size())
	if open > 0: text(Vector2(250, 290), Tx.plural("ui.pets.posts_open", open) % open, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 106)

## The stable: a stall a row, the animal looking out over its door, its name board, and a red mark on a wounded one.
func _stable(ch) -> void:
	_section(Vector2(94, 318), Tx.t("ui.pets.the_stable"), Tx.plural("ui.pets.stable_count", ch.pets.size()) % ch.pets.size())
	var area := Rect2(92, 324, 264 + GUTTER, 336)
	if ch.pets.is_empty(): return   # the leaf says where the first one comes from
	list("pets", area, ch.pets.size(), 56, func(i: int, rr: Rect2):
		var p: Dictionary = ch.pets[i]
		var chosen := str(p.uid) == sel
		panel(rr, "minor_panel", "selected" if chosen else "normal")
		if chosen: draw_rect(Rect2(rr.position.x, rr.position.y + 2, 3, rr.size.y - 4), UiKit.GOLD)
		# The stall's half-door under the animal's head: a low timber rail it looks out over.
		draw_rect(Rect2(rr.position.x + 6, rr.end.y - 14, 76, 10), UiKit.SURFACE.wood)
		draw_rect(Rect2(rr.position.x + 6, rr.end.y - 14, 76, 2), UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.4))
		creature_at(Rect2(rr.position.x + 6, rr.position.y + 2, 76, 40), _art(p), "idle")
		text(rr.position + Vector2(88, 22), fit(str(p.name), 16, rr.size.x - 112), 16, UiKit.PAPER)
		text(rr.position + Vector2(88, 44), fit(_stall_line(ch, p), 14, rr.size.x - 96), 14, UiKit.MIST)
		if p.get("wounded", false):
			draw_circle(Vector2(rr.end.x - 14, rr.position.y + 14), 7.0, UiKit.INK, true, -1.0, true)
			draw_circle(Vector2(rr.end.x - 14, rr.position.y + 14), 5.5, UiKit.RED, true, -1.0, true)
		elif p.get("locked", false):
			_lock_icon(Vector2(rr.end.x - 20, rr.position.y + 4))
		region(rr, "sel", str(p.uid))
	)

func _stall_line(ch, p: Dictionary) -> String:
	var sp := ContentDB.entry("pets", str(p.species))
	var s := Tx.t("ui.pets.stall_line") % [int(p.level), Tx.t("ui.pets.role_" + str(p.get("role", "combat"))), ContentDB.name_of("elements", str(sp.get("element", "")))]
	if PetAuthority.is_construct(p): s = Tx.t("ui.pets.stall_line_construct") % int(p.level)
	if ch.pet_bag.has(str(p.uid)): s += " · " + Tx.t("ui.pets.in_bag")
	return s

# ------------------------------------------------------------------ the leaf
func _leaf(ch, pet: Dictionary) -> void:
	face(LEAF.grow_individual(8, 6, 8, 6), "bestiary_leaf")
	if pet.is_empty():
		para(Rect2(LX, LEAF.position.y + 30, LW, 120), Tx.t("ui.pets.no_spirit_animals_yet_hermit"), 18, RecordsKit.BROWN)
		return
	var sp := ContentDB.entry("pets", str(pet.species))
	var construct: bool = PetAuthority.is_construct(pet)
	# The name (tap to rename) and the level, the lock at the corner.
	var top := LEAF.position.y
	if name_edit != null and name_edit.visible:
		name_edit.position = Vector2(LX, top + 6)
		name_edit.size = Vector2(250, 44)
		btn(Rect2(LX + 258, top + 4, 96, 48), Tx.t("ui.pets.save_name"), "rename_ok", null, true, true, "", 18)
	else:
		var nw := minf(UiKit.text_width(str(pet.name), 26, true), 300.0)
		text(Vector2(LX, top + 36), str(pet.name), 26, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, 300, true)
		for k in int(nw / 6.0):   # a dotted line under the name: it can be written anew
			draw_rect(Rect2(LX + k * 6, top + 42, 3, 1), Color(RecordsKit.BROWN, 0.6))
		region(Rect2(LX - 4, top + 2, nw + 12, 48), "rename")
	text(Vector2(LX + 250, top + 34), Tx.t("ui.pets.lv_short") % int(pet.level), 22, RecordsKit.JADE_INK, HORIZONTAL_ALIGNMENT_RIGHT, 176, true)
	var lock := Rect2(LEAF.end.x - 50, top + 4, 48, 48)
	if pet.get("locked", false): _lock_icon(lock.get_center() - Vector2(9, 13), 1.5)
	else:   # an open padlock, faint: a tap locks it against fusion
		var lc := lock.get_center()
		draw_rect(Rect2(lc + Vector2(-9, -2), Vector2(18, 13)), Color(RecordsKit.BROWN, 0.6), false, 2.0)
		draw_arc(lc + Vector2(-4, -3), 6.0, PI, TAU, 10, Color(RecordsKit.BROWN, 0.6), 2.0, true)
	region(lock, "lock", sel)
	text(Vector2(LX, top + 62), fit(_kind_line(pet, sp, construct), 16, LW), 16, RecordsKit.BROWN)
	# The animal stood on its straw; chosen, it walks out onto the leaf.
	var stage := Rect2(LX, top + 72, 228, 118)
	BeastKit.straw(self, Rect2(stage.position.x + 8, stage.end.y - 30, stage.size.x - 16, 26), int(str(pet.uid).hash() % 97))
	var k := unfold(WALK_S) if chose_t < 0.0 else clampf((t - chose_t) / WALK_S, 0.0, 1.0)
	if UiKit.reduce_motion(): k = 1.0
	var form_tint: Dictionary = Game.pets.form_of(pet)
	var tint := Color.WHITE.lerp(Color(str(form_tint.get("tint", "#ffffff"))), 0.5) if not form_tint.is_empty() else Color.WHITE
	if UiKit.reduce_motion() and chose_t >= 0.0: tint.a = clampf((t - chose_t) / UiKit.MOTION_FADE_S, 0.0, 1.0)
	creature_at(Rect2(stage.position + Vector2(-(1.0 - k) * 150.0, 0), stage.size - Vector2(0, 12)), _art(pet), "walk" if k < 1.0 or ch.active_pet == sel else "idle", tint)
	_bars(ch, pet, construct)
	if construct:
		_construct_leaf(pet, sp)
		return
	match view:
		"grow": _grow_view(ch, pet)
		"feed": _feed_view(ch, pet, sp)
		"teach": _teach_view(ch, pet)
		"gear": _gear_view(ch)
		"breed": _breed_view(ch, pet)
		"fuse": _fuse_view(ch, pet)
		_: _record(ch, pet, sp)
	_leaf_foot(ch, pet)

func _kind_line(pet: Dictionary, sp: Dictionary, construct: bool) -> String:
	if construct: return "%s · %s" % [str(sp.get("name", "")), Tx.t("ui.pets.construct_kind")]
	var branch := str(pet.get("branch", ""))
	var stage_name := str(Game.pets.stage_def(str(pet.get("stage", "hatchling"))).get("name", Tx.t("ui.pets.hatchling")))
	var parts := [ContentDB.name_of("elements", str(sp.get("element", ""))), branch if branch != "" else stage_name,
		str(Game.pets.rarity_def(str(pet.get("rarity", "common"))).get("name", "")), Tx.t("ui.pets.role_" + str(pet.get("role", "combat"))),
		Tx.t("ui.pets.contract_" + str(pet.get("contract", "master")))]
	if pet.get("variant", false): parts.append(Tx.t("ui.pets.variant"))
	return " · ".join(parts.filter(func(s): return str(s) != ""))

## Beside the animal: its level, its bond as ten hearts (none for a construct) and a Grievous Wound.
func _bars(ch, pet: Dictionary, construct: bool) -> void:
	var x := LX + 242
	var w := LEAF.end.x - 16 - x
	var y := LEAF.position.y + 88
	var need := float(ContentDB.curve("pet_xp.base", 20)) * pow(int(pet.level), float(ContentDB.curve("pet_xp.per_level_pow", 1.5)))
	text(Vector2(x, y), Tx.t("ui.pets.level_word"), 14, RecordsKit.BROWN)
	text(Vector2(x, y), "%s / %s" % [UiKit.fmt(int(pet.get("xp", 0.0))), UiKit.fmt(int(need))], 14, RecordsKit.INK, HORIZONTAL_ALIGNMENT_RIGHT, w)
	BeastKit.paper_bar(self, Rect2(x, y + 8, w, 14), float(pet.get("xp", 0.0)) / need, UiKit.JADE)
	y += 46
	if construct:
		para(Rect2(x, y - 14, w, 60), Tx.t("ui.pets.construct_line"), 14, RecordsKit.BROWN)
	else:
		var bond := float(pet.get("bond", 0.0))
		text(Vector2(x, y), Tx.t("ui.pets.bond_hearts") % bond, 14, RecordsKit.BROWN)
		for i in 10:
			var hc := Vector2(x + 8 + i * 21, y + 16)
			draw_circle(hc, 8.0, UiKit.BLOOD.lerp(UiKit.INK, 0.3) if bond > i else UiKit.BRONZE, true, -1.0, true)
			draw_circle(hc, 6.5, UiKit.SURFACE.scroll_edge, true, -1.0, true)
			var part := clampf(bond - i, 0.0, 1.0)
			if part >= 1.0: draw_circle(hc, 6.5, UiKit.BLOOD, true, -1.0, true)
			elif part > 0.0: draw_rect(Rect2(hc.x - 6.5, hc.y - 4, 13.0 * part, 8), UiKit.BLOOD)
	if pet.get("wounded", false):
		para(Rect2(x, y + 28, w, 44), Tx.t("ui.pets.wounded_short"), 14, RecordsKit.RED_INK, 2)
	elif Game.pets.care_mult(pet) < 1.0:
		para(Rect2(x, y + 28, w, 44), Tx.t("ui.pets.hungry"), 14, RecordsKit.RED_INK, 2)

## The record: growth as stepping stones, the bloodline with its stops, the skills and the traits.
func _record(ch, pet: Dictionary, sp: Dictionary) -> void:
	var y := LEAF.position.y + 212
	text(Vector2(LX, y), Tx.t("ui.pets.growth_word"), 18, RecordsKit.INK)
	var stages: Array = ContentDB.config("pet_growth").get("stages", [])
	var cur: int = Game.pets.stage_index(str(pet.get("stage", "hatchling")))
	var primordial: bool = sp.get("primordial", false)
	var step := LW / float(maxi(1, stages.size()))
	var sy := y + 20
	var x0 := LX + step * 0.5
	draw_line(Vector2(x0, sy), Vector2(x0 + step * (stages.size() - 1), sy), Color(UiKit.BRONZE, 0.8), 2.0, true)
	if cur > 0: draw_line(Vector2(x0, sy), Vector2(x0 + step * cur, sy), UiKit.JADE, 4.0, true)
	for i in stages.size():
		var c := Vector2(x0 + step * i, sy)
		var far: bool = stages[i].get("primordial_only", false) and not primordial
		draw_circle(c, 13.0, UiKit.JADE_SHADOW if i <= cur else (UiKit.GOLD if i == cur + 1 else Color(UiKit.BRONZE, 0.45 if far else 1.0)), true, -1.0, true)
		draw_circle(c, 11.0, UiKit.JADE if i <= cur else UiKit.SURFACE.scroll.lerp(UiKit.PAPER, 0.5 if i == cur + 1 else 0.0), true, -1.0, true)
		if i <= cur: draw_circle(c + Vector2(-3, -3), 3.5, Color(UiKit.BRIGHT_JADE, 0.8), true, -1.0, true)
		var nm := str(stages[i].get("name", ""))
		if i == 2 and cur >= 2 and str(pet.get("branch", "")) != "": nm = str(pet.branch)
		text(Vector2(c.x - step * 0.5, sy + 30), fit(nm, 14, step - 2), 14,
			RecordsKit.INK if i == cur else (RecordsKit.NEXT_INK if i == cur + 1 else (RecordsKit.FADED if far else RecordsKit.BROWN)), HORIZONTAL_ALIGNMENT_CENTER, step)
	var nx: Dictionary = Game.pets.next_stage(pet)
	y = sy + 52
	if nx.is_empty():
		text(Vector2(LX, y), Tx.t("ui.pets.fully_grown_for_this_land"), 14, RecordsKit.BROWN)
	else:
		var runs: Array = [[str(nx.get("name", "")) + ":", RecordsKit.INK]]
		for g in Game.pets.evolve_gates(ch, pet):
			runs.append([("✓ " if g.ok else "") + str(g.text) + " ·", RecordsKit.JADE_INK if g.ok else RecordsKit.RED_INK])
		runs[-1][0] = str(runs[-1][0]).trim_suffix(" ·")
		rich(Rect2(LX, y - 14, LW, 18), runs, 14)
		text(Vector2(LX, y + 18), fit(_opens_line(pet, nx), 14, LW), 14, RecordsKit.BROWN)
	# The bloodline, with its stops at the skill and the form.
	var g2: Dictionary = ContentDB.config("pet_growth").get("awakening", {})
	var at_skill := int(g2.get("skill_at", 50))
	var at_form := int(g2.get("form_at", 90))
	var purity := int(pet.get("purity", 0))
	var skill_name := str(sp.get("bloodline_skill", {}).get("name", ""))
	var form_name := str(sp.get("form_change", {}).get("name", ""))
	y += 42
	text(Vector2(LX, y), Tx.t("ui.pets.purity") % purity, 18, RecordsKit.INK)
	var nxt := ""
	if purity < at_skill and skill_name != "": nxt = Tx.t("ui.pets.purity_next") % [at_skill, skill_name]
	elif purity < at_form and form_name != "": nxt = Tx.t("ui.pets.purity_next") % [at_form, form_name]
	if nxt != "": text(Vector2(LX + 220, y), fit(nxt, 14, LW - 220), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_RIGHT, LW - 220)
	BeastKit.paper_bar(self, Rect2(LX, y + 18, LW, 14), purity / 100.0, UiKit.QI.lerp(UiKit.PAPER, 0.25), [at_skill / 100.0, at_form / 100.0])
	# Each stop's words under it: the form's at the right end, the skill's centred on its stop in the room left.
	var form_s := fit("%d · %s" % [at_form, form_name], 14, 200) if form_name != "" else ""
	var fw := UiKit.text_width(form_s, 14) if form_s != "" else 0.0
	if form_s != "": text(Vector2(LX + LW - fw, y + 50), form_s, 14, RecordsKit.BROWN)
	var sx := LX + LW * at_skill / 100.0
	var skill_s := fit(Tx.t("ui.pets.stop_skill") % at_skill, 14, 220)
	var sw := UiKit.text_width(skill_s, 14)
	text(Vector2(minf(sx - sw * 0.5, LX + LW - fw - 14.0 - sw), y + 50), skill_s, 14, RecordsKit.BROWN)
	# The skills as chips, the traits and learned skills under them.
	y += 74
	text(Vector2(LX, y), Tx.t("ui.pets.skills_word"), 16, RecordsKit.INK)
	var cx := LX + UiKit.text_width(Tx.t("ui.pets.skills_word"), 16) + 10
	for s in sp.get("skills", []):
		var w := UiKit.text_width(str(s), 14) + 20
		if cx + w > LX + LW: break
		_chip(Rect2(cx, y - 18, w, 26), str(s))
		cx += w + 6
	var shown: Array = Game.pets.revealed_traits(pet).map(func(tr): return ContentDB.name_of("pet_traits", str(tr)))
	while shown.size() < int(ContentDB.config("pet_growth").get("traits_per_pet", 3)): shown.append("?")
	var learned: Array = pet.get("learned_skills", [])
	var slots: int = Game.pets.skill_slots(pet)
	var learned_s := Tx.t("ui.pets.learned") % [learned.size(), slots] if slots > 0 else Tx.t("ui.pets.no_slots")
	text(Vector2(LX, y + 22), fit(Tx.t("ui.pets.traits") + " · ".join(shown) + "  ·  " + learned_s, 14, LW), 14, RecordsKit.BROWN)

## A skill on the leaf: a jade-tinted pill with its name in ink.
func _chip(r: Rect2, words: String, lit := true) -> void:
	rounded(r.grow(1), r.size.y * 0.5, UiKit.JADE_SHADOW.lerp(UiKit.SURFACE.scroll, 0.4))
	rounded(r, r.size.y * 0.5, UiKit.SURFACE.scroll.lerp(UiKit.JADE, 0.16) if lit else UiKit.SURFACE.scroll)
	ground(r, UiKit.SURFACE.scroll.lerp(UiKit.JADE, 0.16) if lit else UiKit.SURFACE.scroll)
	text(Vector2(r.position.x, r.position.y + r.size.y * 0.5 + 5), words, 14, RecordsKit.JADE_INK if lit else RecordsKit.FADED, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

## What the next stage opens, from the data: a trait shown, the aptitude read, skill slots, the line chosen.
func _opens_line(pet: Dictionary, nx: Dictionary) -> String:
	var parts: Array = []
	var apt: bool = not Game.pets.aptitude_known(pet) and Game.pets.stage_index(str(nx.id)) >= Game.pets.stage_index("juvenile")
	var trait_: bool = nx.get("reveal_trait", false)
	if apt and trait_: parts.append(Tx.t("ui.pets.opens_aptitude_trait"))
	elif apt: parts.append(Tx.t("ui.pets.opens_aptitude"))
	elif trait_: parts.append(Tx.t("ui.pets.opens_trait"))
	var more := int(ContentDB.config("pet_growth").get("skill_slots", {}).get(str(nx.id), 0)) - Game.pets.skill_slots(pet)
	if more > 0: parts.append(Tx.plural("ui.pets.opens_slots", more) % more)
	if nx.get("branch", false): parts.append(Tx.t("ui.pets.opens_branch"))
	if parts.is_empty(): parts.append(Tx.t("ui.pets.opens_share") % int(round(float(nx.get("inherit", 0.2)) * 100.0)))
	if parts.size() > 1: return Tx.t("ui.pets.opens") % (Tx.t("ui.pets.opens_and") % [", ".join(parts.slice(0, -1)), parts[-1]])
	return Tx.t("ui.pets.opens") % parts[0]

## The leaf's foot: Grow (lit when the next stage is ready), Feed, Teach, Breed and Fuse turn its lower half.
func _leaf_foot(ch, pet: Dictionary) -> void:
	var w := (LW - 4 * GAP) / 5.0
	var y := LEAF.end.y - 54
	var ready: bool = Game.pets.can_evolve(ch, pet) and not pet.get("wounded", false)
	var partners: Array = Game.pets.breed_partners(ch, pet)
	for i in VIEWS.size():
		var v: String = VIEWS[i]
		var r := Rect2(LX + i * (w + GAP), y, w, BTN_H)
		var ok := true
		var why := ""
		if v == "breed" and partners.is_empty():
			ok = false
			why = Tx.t("ui.pets.breed_none")
		if v == "fuse" and ch.pets.size() < 2:
			ok = false
			why = Tx.t("ui.pets.fuse_none")
		btn(r, Tx.t("ui.pets.view_" + v), "view", v, v == "grow" and ready, ok, why, 16)
		if view == v: draw_rect(Rect2(r.position.x + 10, r.end.y + 2, r.size.x - 20, 3), UiKit.GOLD)

## Grow: the next stage's gates, what it gives, and Evolve (or the two lines at Adult, or a breakthrough from Awakened
## with its support); the contract and core, aptitude and resonance.
func _grow_view(ch, pet: Dictionary) -> void:
	var y := LEAF.position.y + 212
	var g: Dictionary = ContentDB.config("pet_growth")
	var apt_line := Tx.t("ui.pets.aptitude_hidden")
	if Game.pets.aptitude_known(pet):
		var apt: Dictionary = pet.get("aptitude", {})
		apt_line = Tx.t("ui.pets.growth_apt") % [float(pet.get("growth", 1.0)), float(apt.get("hp", 1.0)), float(apt.get("attack", 1.0)),
			float(apt.get("defence", 1.0)), float(apt.get("speed", 1.0))]
	text(Vector2(LX, y), fit(apt_line, 14, LW), 14, RecordsKit.BROWN)
	var bond_line := Tx.t("ui.pets.contract_" + str(pet.get("contract", "master")))
	var core: Dictionary = Game.pets.core_grade_def(str(pet.get("core_grade", "")))
	if not core.is_empty(): bond_line += "  ·  " + Tx.t("ui.pets.core") % [str(core.get("name", "")), int(round(float(core.get("bonus", 0.0)) * 100.0))]
	var res := Game.pets.resonance(ch) if Game.pets.party(ch).any(func(q): return str(q.uid) == sel) else 0.0
	if res > 0.0: bond_line += "  ·  " + Tx.t("ui.pets.resonance") % int(round(res * 100.0))
	var ctr := ""
	if Game.pets.equal_contract_open(ch, pet): ctr = "equal"
	elif str(pet.get("contract", "master")) == "master" and ch.inventory.count(str(g.get("contracts", {}).get("blood", {}).get("item", ""))) > 0: ctr = "blood"
	text(Vector2(LX, y + 22), fit(bond_line, 14, LW - (196 if ctr != "" else 0)), 14, RecordsKit.INK)
	if ctr != "": btn(Rect2(LX + LW - 188, y + 2, 188, BTN_H), Tx.t("ui.pets.contract_btn_" + ctr), "contract", ctr, ctr == "equal", true, "", 16)
	y += 58
	var nx: Dictionary = Game.pets.next_stage(pet)
	if nx.is_empty():
		para(Rect2(LX, y - 14, LW, 40), Tx.t("ui.pets.fully_grown_for_this_land"), 16, RecordsKit.BROWN)
		return
	text(Vector2(LX, y), Tx.t("ui.pets.next") % str(nx.get("name", "")), 18, RecordsKit.INK)
	for gate in Game.pets.evolve_gates(ch, pet):
		y += 20
		text(Vector2(LX + 12, y), ("✓ " if gate.ok else "· ") + str(gate.text), 14, RecordsKit.JADE_INK if gate.ok else RecordsKit.RED_INK)
	var ready: bool = Game.pets.can_evolve(ch, pet)
	var from := Game.pets.stage_index(str(g.get("breakthrough", {}).get("from", "awakened")))
	y += 14
	if Game.pets.stage_index(str(nx.id)) >= from:
		# A breakthrough: its chance, the support to put in (tap to toggle), then Break Through.
		support = support.filter(func(it): return ch.inventory.count(str(it)) > 0)
		var chance: float = Game.pets.breakthrough_chance(ch, pet, support)
		text(Vector2(LX, y + 14), Tx.t("ui.pets.breakthrough") % [str(nx.get("name", "")), int(round(chance * 100.0))], 16, RecordsKit.INK)
		var sx := LX
		for it in _support_items(ch, pet):
			if sx + 48 > LX + LW - 190: break
			slot_box(Rect2(sx, y + 24, 48, 48), str(it), ch.inventory.count(str(it)), "", "support", str(it), support.has(it))
			sx += 54
		var go: bool = ready and not pet.get("wounded", false)
		btn(Rect2(LX + LW - 180, y + 24, 180, BTN_H), Tx.t("ui.pets.break_through"), "breakthrough", null, go, go, Tx.t("ui.pets.not_ready_yet"), 18)
	elif nx.get("branch", false):
		var branches: Array = ContentDB.entry("pets", str(pet.species)).get("branches", [])
		var bw := (LW - GAP * maxf(0.0, branches.size() - 1.0)) / maxf(1.0, branches.size())
		for i in branches.size():
			btn(Rect2(LX + i * (bw + GAP), y + 4, bw, BTN_H), str(branches[i]), "evolve", str(branches[i]), ready, ready, Tx.t("ui.pets.not_ready_yet"), 18)
	else:
		btn(Rect2(LX, y + 4, 220, BTN_H), Tx.t("ui.pets.evolve"), "evolve", "", true, ready, Tx.t("ui.pets.not_ready_yet"), 20)

## Feed: its favourite foods and its own element's cores that you carry, a tap to feed or to devour.
func _feed_view(ch, pet: Dictionary, sp: Dictionary) -> void:
	var y := LEAF.position.y + 212
	text(Vector2(LX, y), fit(Tx.t("ui.pets.favourite_foods") + ", ".join((sp.get("favourite_foods", []) as Array).map(func(f): return ContentDB.item_name(str(f)))), 16, LW), 16, RecordsKit.INK)
	text(Vector2(LX, y + 22), Tx.t("ui.pets.hungry") if Game.pets.care_mult(pet) < 1.0 else Tx.t("ui.pets.fed_today"), 14,
		RecordsKit.RED_INK if Game.pets.care_mult(pet) < 1.0 else RecordsKit.JADE_INK)
	var foods: Array = (sp.get("favourite_foods", []) as Array).filter(func(f): return ch.inventory.count(str(f)) > 0)
	for f in ["roast_fish", "ember_pepper_broth"]:
		if ch.inventory.count(f) > 0 and not foods.has(f): foods.append(f)
	var cores: Array = _own_cores(ch, sp)
	if foods.is_empty() and cores.is_empty():
		para(Rect2(LX, y + 36, LW, 60), Tx.t("ui.pets.no_food"), 16, RecordsKit.BROWN)
		return
	text(Vector2(LX, y + 46), Tx.t("ui.pets.tap_food_to_feed"), 14, RecordsKit.BROWN)
	# The foods, then (S46) the cores of the animal's own element to devour for growth: five a row, two rows.
	var things: Array = foods.map(func(f): return ["feed", str(f)]) + cores.map(func(cid): return ["devour", str(cid)])
	for i in mini(things.size(), 10):
		var r := Rect2(LX + (i % 5) * (SLOT + GAP), y + 54 + int(i / 5) * (SLOT + 4), SLOT, SLOT)
		slot_box(r, str(things[i][1]), ch.inventory.count(str(things[i][1])), "", str(things[i][0]), str(things[i][1]))

## Teach: the learned skills in their slots, and the skill books in the bag (tap to teach).
func _teach_view(ch, pet: Dictionary) -> void:
	var y := LEAF.position.y + 212
	var slots: int = Game.pets.skill_slots(pet)
	var learned: Array = pet.get("learned_skills", [])
	text(Vector2(LX, y), Tx.t("ui.pets.learned") % [learned.size(), slots], 16, RecordsKit.INK)
	if slots == 0: text(Vector2(LX + 200, y), fit(Tx.t("ui.pets.no_slots"), 14, LW - 200), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_RIGHT, LW - 200)
	var cw := (LW - 3 * GAP) / 4.0
	for i in slots:
		_chip(Rect2(LX + (i % 4) * (cw + GAP), y + 12 + int(i / 4) * 32, cw, 26),
			fit(ContentDB.name_of("pet_skill_books", str(learned[i])) if i < learned.size() else "—", 14, cw - 12), i < learned.size())
	var books: Array = []
	for st in ch.inventory.bag:
		if st != null and ContentDB.item(str(st.id)).has("pet_book") and not books.has(str(st.id)): books.append(str(st.id))
	y += 64
	if books.is_empty():
		para(Rect2(LX, y - 12, LW, 40), Tx.t("ui.pets.no_books"), 16, RecordsKit.BROWN)
		return
	text(Vector2(LX, y), Tx.t("ui.pets.tap_book"), 14, RecordsKit.BROWN)
	var x := LX
	for b in books:
		if x + SLOT > LX + LW: break
		slot_box(Rect2(x, y + 8, SLOT, SLOT), str(b), ch.inventory.count(str(b)), "", "teach", str(b))
		x += SLOT + GAP

## Gear from the bag: every piece of pet gear you carry, a tap to put it on.
func _gear_view(ch) -> void:
	var y := LEAF.position.y + 212
	var gear: Array = _bag_gear(ch)
	text(Vector2(LX, y), Tx.t("ui.pets.tap_gear"), 16, RecordsKit.INK)
	var x := LX
	var row := 0
	for i in gear:
		if x + SLOT > LX + LW:
			x = LX
			row += 1
			if row > 1: break
		slot_box(Rect2(x, y + 12 + row * (SLOT + GAP), SLOT, SLOT), str(ch.inventory.bag[i].id), 0, str(ch.inventory.bag[i].get("quality", "")), "equip", i)
		x += SLOT + GAP

func _bag_gear(ch) -> Array:
	var out: Array = []
	for i in ch.inventory.bag.size():
		var st = ch.inventory.bag[i]
		if st != null and ContentDB.item(str(st.id)).has("pet_gear"): out.append(i)
	return out

## Breeding (S22): two Adults of one family; the gate that is closed, or a button per partner.
func _breed_view(ch, pet: Dictionary) -> void:
	var y := LEAF.position.y + 212
	text(Vector2(LX, y), Tx.t("ui.pets.breed_with"), 18, RecordsKit.INK)
	var why: String = Game.pets.breeding_blocked(ch)
	if why != "":
		para(Rect2(LX, y + 10, LW, 60), why, 16, RecordsKit.BROWN, 3)
		return
	var partners: Array = Game.pets.breed_partners(ch, pet)
	var bw := (LW - GAP) / 2.0
	for i in mini(partners.size(), 4):
		btn(Rect2(LX + (i % 2) * (bw + GAP), y + 14 + int(i / 2) * 56, bw, BTN_H), str(partners[i].name), "breed", str(partners[i].uid), false, true, "", 18)

## Fusion: every other animal, with Fuse (locked ones cannot be); only at the Beast Hall or the Beast Pavilion.
func _fuse_view(ch, pet: Dictionary) -> void:
	var top := LEAF.position.y + 196
	para(Rect2(LX, top, LW, 60), Tx.t("ui.pets.fuse_help") % str(pet.name), 14, RecordsKit.BROWN, 3)
	var others: Array = ch.pets.filter(func(o): return str(o.uid) != sel)
	var where: String = Game.pets.fusion_blocked(ch, pet, others[0]) if not others.is_empty() else ""
	var at_hall: bool = where != Tx.t("sim.pet.fuse_where")
	if not at_hall: text(Vector2(LX, top + 70), fit(where, 14, LW), 14, RecordsKit.RED_INK)
	list("fuse", Rect2(LX, top + 80, LW + GUTTER, 128), others.size(), 64, func(i: int, rr: Rect2):
		var o: Dictionary = others[i]
		panel(rr, "minor_panel")
		creature_at(Rect2(rr.position + Vector2(6, 6), Vector2(56, 48)), _art(o))
		text(rr.position + Vector2(70, 24), fit(str(o.name), 16, rr.size.x - 220), 16)
		text(rr.position + Vector2(70, 46), fit(Tx.t("ui.pets.fuse_row") % [ContentDB.name_of("pets", str(o.species)), int(o.get("level", 1)), int(o.get("purity", 0))], 14, rr.size.x - 220), 14, UiKit.MIST)
		var locked: bool = o.get("locked", false)
		btn(Rect2(rr.end.x - 136, rr.position.y + 6, 128, BTN_H), Tx.t("ui.pets.fuse_btn"), "fuse", str(o.uid), false, at_hall and not locked,
			Tx.t("ui.pets.locked_pet") if locked else where, 18)
	)

## S48 a combat puppet: its strikes and how it is kept. Nothing to feed or grow.
func _construct_leaf(pet: Dictionary, sp: Dictionary) -> void:
	var y := LEAF.position.y + 212
	text(Vector2(LX, y), fit(Tx.t("ui.pets.skills") + ", ".join(sp.get("skills", [])), 16, LW), 16, RecordsKit.INK)
	var h := para(Rect2(LX, y + 12, LW, 90), Tx.t("ui.pets.construct_care"), 16, RecordsKit.BROWN)
	para(Rect2(LX, y + 24 + h, LW, 60), Tx.t("ui.pets.construct_repair"), 16, RecordsKit.BROWN)
	if pet.get("wounded", false): text(Vector2(LX, LEAF.end.y - 24), fit(Tx.t("ui.workshop.puppet_wounded"), 16, LW), 16, RecordsKit.RED_INK)

# ------------------------------------------------------------------ the tack wall
func _tack(ch, pet: Dictionary) -> void:
	if not pet.is_empty(): _care(ch, pet)
	_nest(ch)
	_swarm_chip(ch)

## Care: out or at rest, beside you, carried in the Spirit Beast Bag; the roles; its nature; then its gear.
func _care(ch, pet: Dictionary) -> void:
	_section(Vector2(RX + 2, 190), Tx.t("ui.pets.care"))
	var construct: bool = PetAuthority.is_construct(pet)
	var only_mount: bool = Game.pets.mount_only(pet)
	var cap: int = Game.pets.command_capacity(ch)
	var bw := (RW - 2 * GAP) / 3.0
	var y := 196.0
	if not only_mount:
		btn(Rect2(RX, y, bw, BTN_H), Tx.t("ui.pets.set_active") if ch.active_pet != sel else Tx.t("ui.pets.rest"), "active", sel, false, true, "", 18)
	if cap > 1 and ch.active_pet != sel:
		var beside: bool = ch.party_pets.has(sel)
		var room_left: bool = beside or Game.pets.party(ch).size() < cap
		btn(Rect2(RX + bw + GAP, y, bw, BTN_H), Tx.t("ui.pets.send_home") if beside else Tx.t("ui.pets.beside"), "party", not beside, false, room_left,
			Tx.t("ui.pets.capacity_full") % cap, 18)
	var bag_cap: int = Game.pets.bag_capacity(ch)
	if ch.active_pet != sel and not only_mount and ch.mount_pet != sel and not construct:
		var carried: bool = ch.pet_bag.has(sel)
		btn(Rect2(RX + 2.0 * (bw + GAP), y, bw, BTN_H), (Tx.t("ui.pets.unpack") if carried else Tx.t("ui.pets.carry")) + (" %d / %d" % [ch.pet_bag.size(), bag_cap] if bag_cap > 0 else ""),
			"carry", not carried, false, carried or (bag_cap > 0 and ch.pet_bag.size() < bag_cap), Tx.t("ui.pets.no_bag") if bag_cap <= 0 else Tx.t("ui.pets.bag_full") % bag_cap, 16)
	if construct:
		para(Rect2(RX, 262, RW, 100), Tx.t("ui.pets.construct_care"), 14, UiKit.MIST)
		return
	var roles := ["combat", "gatherer", "cultivation"]
	if Game.pets.mountable(pet): roles.append("mount")
	if Unlocks.is_unlocked(ch.id, "herb_garden"): roles.append("guard")   # S45: watches the garden while you are away
	if only_mount: roles = ["mount"]   # S46: a mount-only animal only carries you
	var per := 2 if roles.size() <= 4 else 3
	var rw := (RW - GAP * (per - 1)) / per
	for i in roles.size():
		var role: String = roles[i]
		btn(Rect2(RX + (i % per) * (rw + GAP), 252 + int(i / per) * 52, rw, BTN_H), Tx.t("ui.pets.role_" + role), "role", role, str(pet.role) == role, true, "", 18)
	var nature := str(ContentDB.entry("pets", str(pet.species)).get("strength_role", ""))
	if nature != "":
		var line := Tx.t("ui.pets.nature") % Tx.t("ui.pets.nature_" + nature)
		text(Vector2(RX + 2, 370), fit(line, 14, RW - 60), 14, UiKit.MIST)
		if Game.pets.role_match(pet) > 0.0:
			text(Vector2(RX + 8 + minf(UiKit.text_width(line, 14), RW - 60), 370), "+%d%%" % int(round(Game.pets.role_match(pet) * 100.0)), 14, UiKit.BRIGHT_JADE)
	# Gear: a worn piece comes off with a tap; an empty place shows the bag's pet gear on the leaf.
	_section(Vector2(RX + 2, 396), Tx.t("ui.pets.gear"))
	var has_gear := not _bag_gear(ch).is_empty()
	var x := RX
	for slot in ContentDB.config("pet_growth").get("gear", {}).get("slots", []):
		var r := Rect2(x, 402, SLOT, SLOT)
		var inst = pet.get("equipment", {}).get(str(slot))
		if inst is Dictionary:
			slot_box(r, str(inst.id), 0, str(inst.get("quality", "")), "unequip", str(slot))
			if int(inst.get("enhance", 0)) > 0: UiKit.draw_outlined(self, "+%d" % int(inst.enhance), r.position + Vector2(4, 18), 14, UiKit.PALE_GOLD)
		else:
			slot_box(r, "", 0, "", "", null, view == "gear")
			draw_arc(r.get_center(), 14.0, 0.0, TAU, 24, Color(UiKit.MIST, 0.3 if has_gear else 0.15), 2.0, true)
			region(r, "view", "gear", has_gear, Tx.t("ui.pets.no_gear"))
		text(Vector2(x - 4, 494), Tx.t("ui.pets.gear_" + str(slot)), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, SLOT + 8)   # B21: its slot's pitch
		x += SLOT + GAP

## The nest: the egg warming with its time or its Hatch, and what can be put into it (S46); or where an egg comes from.
func _nest(ch) -> void:
	_section(Vector2(RX + 2, 518), Tx.t("ui.pets.nest"), Tx.t("ui.pets.the_eggs"))
	var r := Rect2(RX, 526, SLOT, SLOT)
	var tx := RX + SLOT + 12
	var tw := RW - SLOT - 12
	if ch.eggs.is_empty():
		slot_box(r, "")
		icon_at(r.grow(-6), "spirit_egg", Color(1, 1, 1, 0.35))
		text(Vector2(tx, 544), Tx.t("ui.pets.no_egg"), 16, UiKit.PAPER)
		para(Rect2(tx, 550, tw, 48), Tx.t("ui.pets.egg_where"), 14, UiKit.MIST, 2)
		return
	var egg: Dictionary = ch.eggs[0]
	slot_box(r, "spirit_egg", 0, str(egg.get("rarity", "")) if egg.get("bred", false) else "")
	var left_s := float(egg.hatch_utc) - Clock.now_utc()
	if left_s <= 0.0:
		btn(Rect2(tx, 540, tw, BTN_H), Tx.t("ui.pets.hatch"), "hatch", 0, true)
		return
	text(Vector2(tx, 544), fit(Tx.t("ui.pets.hatches_in") % UiKit.span(left_s), 16, tw), 16, UiKit.PAPER)
	# S46 incubation input: your blood, a core to steer the element, essence blood to reroll a trait.
	var used: Array = egg.get("inputs", [])
	var core := _steering_core(ch, egg)
	var reroll_item := str(ContentDB.config("pet_growth").get("incubation", {}).get("reroll_item", ""))
	var opts := [["blood", "", not used.has("blood") and float(ch.cooldowns.get("essence_blood", 0.0)) <= Clock.now_utc()],
		["element", core, not used.has("element") and core != "" and not egg.get("bred", false)],
		["reroll", "", not used.has("reroll") and ch.inventory.count(reroll_item) > 0]]
	var bw := (tw - 2 * 6.0) / 3.0
	for k in opts.size():
		var o: Array = opts[k]
		btn(Rect2(tx + k * (bw + 6), 554, bw, BTN_H), Tx.t("ui.pets.egg_short_" + str(o[0])) + (" ✓" if used.has(str(o[0])) else ""),
			"infuse", [0, str(o[0]), str(o[1])], false, bool(o[2]), Tx.t("ui.pets.egg_" + str(o[0]) + "_why"), 14)

## The swarm at the foot of the tack wall: its count and food, a tap to its tab.
func _swarm_chip(ch) -> void:
	var at := -1
	for i in tabs.size():
		if str(tabs[i].id) == "swarm": at = i
	if at < 0 or not ch.eggs.is_empty(): return
	var sw: Dictionary = Game.pets.swarm_of(ch)
	var r := Rect2(RX, 606, RW, 56)
	panel(r)
	slot_box(Rect2(r.position + Vector2(10, 6), Vector2(SLOT_SMALL, SLOT_SMALL)), "copperjaw_box")
	text(r.position + Vector2(64, 24), fit(Tx.t("ui.pets.swarm_title"), 16, RW - 100), 16, UiKit.PALE_GOLD)
	text(r.position + Vector2(64, 46), fit(Tx.t("ui.pets.swarm_chip") % [UiKit.fmt(int(sw.get("pop", 0.0))), UiKit.fmt(int(Game.pets.swarm_cfg().get("max_pop", 5000))),
		UiKit.span(float(sw.get("food", 0)) * 3600.0)], 14, RW - 100), 14, UiKit.MIST)
	draw_colored_polygon(PackedVector2Array([r.end - Vector2(28, 36), r.end - Vector2(16, 28), r.end - Vector2(28, 20)]), UiKit.MIST)
	region(r, "_tab", at)

# ------------------------------------------------------------------ helpers
## Cores of the animal's own element in the gourd.
func _own_cores(ch, sp: Dictionary) -> Array:
	var cores: Array = []
	for st in ch.inventory.bag:
		if st == null: continue
		var cd: Dictionary = ContentDB.item(str(st.id)).get("core", {})
		if cd.has("tier") and str(cd.element) == str(sp.get("element", "")) and not cores.has(str(st.id)): cores.append(str(st.id))
	return cores

## Items that can support a breakthrough: its own element's cores and essence blood.
func _support_items(ch, pet: Dictionary) -> Array:
	var out: Array = _own_cores(ch, ContentDB.entry("pets", str(pet.species)))
	for it in ContentDB.config("pet_growth").get("breakthrough", {}).get("support", {}):
		if ContentDB.has_entry("items", str(it)) and ch.inventory.count(str(it)) > 0: out.append(str(it))
	return out

## The first core in the bag whose element some other egg answers (to steer this one).
func _steering_core(ch, egg: Dictionary) -> String:
	var own := str(ContentDB.entry("pets", str(egg.get("species", ""))).get("element", ""))
	var els := {}
	for r in ContentDB.config("eggs").get("species", []): els[str(ContentDB.entry("pets", str(r.species)).get("element", ""))] = true
	for st in ch.inventory.bag:
		if st == null: continue
		var el := str(ContentDB.item(str(st.id)).get("core", {}).get("element", ""))
		if el != "" and el != own and els.has(el): return str(st.id)
	return ""

func _sel_name() -> String:
	for o in c().pets:
		if str(o.uid) == sel: return str(o.name)
	return ""

func _art(p: Dictionary) -> String:
	return str(ContentDB.entry("pets", str(p.species)).get("art", p.species))

## v1.2 Phase D: the Copperjaw swarm: its population, food and Queen, and the ores you carry to feed it. The stage on
## the right shows the swarm on the wing from its creature sheet (stats.swarm.art; the Queen's sheet once she has risen).
func _swarm_tab(ch, r: Rect2) -> void:
	panel(r)
	var sw: Dictionary = Game.pets.swarm_of(ch)
	var k: Dictionary = Game.pets.swarm_cfg()
	var queen := bool(sw.get("queen", false))
	var stage := Rect2(r.end.x - 254, r.position.y + 18, 230, 170)
	draw_style_box(UiKit.style("slot"), stage)
	creature_at(stage.grow_individual(-10, -10, -10, -16), Game.pets.swarm_art(ch), "walk")
	var colw := stage.position.x - r.position.x - 48   # the left column, beside the stage
	heading(r.position + Vector2(24, 44), Tx.t("ui.pets.swarm_title"), colw)
	var pop := float(sw.get("pop", 0.0))
	bar(Rect2(r.position.x + 24, r.position.y + 70, colw, 28), log(1.0 + pop) / log(1.0 + float(k.get("max_pop", 5000))), UiKit.GOLD,
		Tx.t("ui.pets.swarm_pop") % [int(pop), int(k.get("max_pop", 5000))])
	var lines: Array = [Tx.t("ui.pets.swarm_food") % UiKit.span(float(sw.get("food", 0)) * 3600.0),
		Tx.t("ui.pets.swarm_bite") % int(round(100.0 * PetRules.swarm_bite(pop, queen, false, k)))]
	if queen: lines.append(Tx.t("ui.pets.swarm_queen"))
	for i in lines.size():
		text(r.position + Vector2(24, 128 + i * 26), fit(lines[i], 18, colw), 18, UiKit.PALE_GOLD if i == 2 else UiKit.PAPER)
	para(Rect2(r.position.x + 24, r.position.y + 204, r.size.x - 48, 60), Tx.t("ui.pets.swarm_help"), 16, UiKit.MIST)
	var ores: Array = []
	for id in k.get("ore_food", {}):
		if ch.inventory.count(str(id)) > 0: ores.append(str(id))
	if ores.is_empty():
		text(r.position + Vector2(24, 300), Tx.t("ui.pets.swarm_no_ore"), 18, UiKit.MIST)
		return
	list("swarm_ore", Rect2(r.position.x + 20, r.position.y + 272, r.size.x - 40, r.size.y - 288), ores.size(), 56, func(i: int, rr: Rect2):
		var id: String = ores[i]
		panel(rr, "minor_panel")
		icon_at(Rect2(rr.position + Vector2(8, 6), Vector2(44, 44)), id)
		text(rr.position + Vector2(64, 34), fit("%s ×%d · %s" % [ContentDB.item_name(id), ch.inventory.count(id),
			Tx.t("ui.pets.swarm_food_each") % UiKit.span(float(k.ore_food[id]) * 3600.0)], 18, rr.size.x - 300), 18)
		btn(Rect2(rr.end.x - 226, rr.position.y + 2, 104, BTN_H), Tx.t("ui.pets.swarm_feed_one"), "swarm_feed", [id, 1], false, true, "", 16)
		btn(Rect2(rr.end.x - 114, rr.position.y + 2, 104, BTN_H), Tx.t("ui.pets.swarm_feed_all"), "swarm_feed", [id, ch.inventory.count(id)], false, true, "", 16)
	)

func on_action(id: String, data) -> void:
	match id:
		"swarm_feed": submit({"type": "feed_swarm", "item": str(data[0]), "count": int(data[1])})
		"sel":
			if str(data) != sel:
				chose_t = t
				view = ""
				support = []
			sel = str(data)
			if name_edit != null: name_edit.visible = false
		"view": view = "" if view == str(data) else str(data)
		"role": submit({"type": "set_pet_role", "pet": sel, "role": str(data)})
		"active": submit({"type": "set_active_pet", "pet": "" if c().active_pet == sel else sel})
		"feed": submit({"type": "feed_pet", "pet": sel, "item": str(data)})
		"devour":
			var dv := submit({"type": "devour_core", "pet": sel, "item": str(data)})
			if dv.get("ok", false): flash(Tx.t("ui.pets.devoured") % int(dv.xp))
		"lock": submit({"type": "lock_pet", "pet": str(data)})
		"evolve": submit({"type": "evolve_pet", "pet": sel, "branch": str(data)})
		"breed": submit({"type": "breed", "a": sel, "b": str(data)})
		"hatch": submit({"type": "hatch_egg", "index": int(data)})
		"party": submit({"type": "set_party", "pet": sel, "on": bool(data)})
		"carry": submit({"type": "set_pet_bag", "pet": sel, "on": bool(data)})
		"rename":
			if name_edit == null:
				name_edit = LineEdit.new()
				name_edit.max_length = 16
				name_edit.add_theme_font_override("font", UiKit.text_font())
				name_edit.add_theme_font_size_override("font_size", 20)
				name_edit.add_theme_stylebox_override("normal", UiKit.style("slot"))
				add_child(name_edit)
			name_edit.text = _sel_name()
			name_edit.visible = true
			name_edit.grab_focus()
		"rename_ok":
			if name_edit != null:
				submit({"type": "rename_pet", "pet": sel, "name": name_edit.text})
				name_edit.visible = false
		"contract": submit({"type": "offer_contract", "pet": sel, "kind": str(data)})
		"infuse": submit({"type": "incubate_input", "egg": int(data[0]), "kind": str(data[1]), "item": str(data[2])})
		"teach": submit({"type": "learn_skill_book", "pet": sel, "book": str(data)})
		"equip":
			if submit({"type": "equip_pet", "pet": sel, "index": int(data)}).get("ok", false) and _bag_gear(c()).is_empty(): view = ""
		"unequip": submit({"type": "unequip_pet", "pet": sel, "slot": str(data)})
		"support":
			if support.has(data): support.erase(data)
			elif support.size() < int(ContentDB.config("pet_growth").get("breakthrough", {}).get("max_support", 3)): support.append(data)
		"breakthrough":
			var bt := submit({"type": "pet_breakthrough", "pet": sel, "support": support})
			support = []
			if bt.get("ok", false): flash(Tx.t("ui.pets.broke_through") if bt.get("success", false) else Tx.t("ui.pets.break_failed"))
		"fuse":
			var fp: Dictionary = {}
			for o in c().pets:
				if str(o.uid) == str(data): fp = o
			ask(Tx.t("sim.pet.fuse_confirm") % [str(fp.get("name", "")), _sel_name()], "fuse_yes", data, true)
		"fuse_yes":
			if submit({"type": "fuse_pets", "keep": sel, "sacrifice": str(data), "confirm": true}).get("ok", false): view = ""
