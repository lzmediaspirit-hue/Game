extends Page
## Character (S10, S11, S18, S34): overview, stats with Combat Power, aptitude, titles and attunement.

const Avatar = preload("res://scripts/avatar.gd")
var STATS := [["max_hp", Tx.t("ui.character.max_hp")], ["max_qi", Tx.t("ui.character.max_qi")], ["max_soul", Tx.t("ui.character.max_soul")], ["physical_attack", Tx.t("ui.character.physical_attack")],
	["qi_attack", Tx.t("ui.character.qi_attack")], ["physical_defense", Tx.t("ui.character.physical_defence")], ["qi_resistance", Tx.t("ui.character.qi_resistance")], ["accuracy", Tx.t("ui.character.accuracy")],
	["evasion", Tx.t("ui.character.evasion")], ["crit_chance", Tx.t("ui.character.critical_chance")], ["crit_damage", Tx.t("ui.character.critical_damage")], ["attack_speed", Tx.t("ui.character.attack_speed")],
	["move_speed", Tx.t("ui.character.move_speed")], ["hp_regen", Tx.t("ui.character.hp_regen")], ["qi_regen", Tx.t("ui.character.qi_regen")], ["drop_rate", Tx.t("ui.character.drop_rate")]]

var doll: Node2D

func _init() -> void:
	title = Tx.t("ui.character.character")
	tabs = [{"id": "overview", "label": Tx.t("ui.character.overview")}, {"id": "stats", "label": Tx.t("ui.character.stats")}, {"id": "aptitude", "label": Tx.t("ui.character.aptitude")}, {"id": "titles", "label": Tx.t("ui.character.titles")}, {"id": "attunement", "label": Tx.t("ui.character.attunement")},
		{"id": "wardrobe", "label": Tx.t("ui.character.wardrobe")}]

func setup() -> void:
	doll = Avatar.new()
	doll.outfit = InventoryAuthority.outfit_for(c())
	doll.position = Vector2(300, 520)
	doll.scale = Vector2.ONE * 2.4
	add_child(doll)

func _process(delta: float) -> void:
	super._process(delta)
	if is_instance_valid(doll):
		doll.visible = str(tabs[tab].id) in ["overview", "wardrobe"]
		doll.position = Vector2(300, 520) if str(tabs[tab].id) == "overview" else Vector2(200, 540)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var r := Rect2(content.position, content.size)
	panel(r)
	match str(tabs[tab].id):
		"overview":
			var x := r.position.x + 480
			text(Vector2(x, r.position.y + 50), str(ch.name), 34, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
			var true_realm := ContentDB.realm_label(ch.cultivator.realm_key)
			text(Vector2(x, r.position.y + 86), true_realm, 20, UiKit.GOLD)
			if ch.cultivator.false_realm != "":
				text(Vector2(x + UiKit.text_width(true_realm, 20) + 12, r.position.y + 86), Tx.t("ui.character.shown_as") % ContentDB.realm_label(ch.cultivator.false_realm), 15, UiKit.MIST)
			var sect_id := str(ch.training_sect.get("id", ""))
			text(Vector2(x, r.position.y + 116), (ContentDB.name_of("sects", sect_id) + " · " + str(ch.training_sect.get("rank", "")).replace("_", " ").capitalize()) if sect_id != "" else Tx.t("ui.character.unaffiliated"), 18, UiKit.MIST)
			text(Vector2(x, r.position.y + 150), Tx.t("ui.character.origin") % ContentDB.name_of("origins", ch.cultivator.origin), 18, UiKit.MIST)
			text(Vector2(x, r.position.y + 210), Tx.t("ui.character.combat_power"), 20, UiKit.MIST)
			text(Vector2(x, r.position.y + 256), UiKit.fmt(StatRules.combat_power(ch)), 44, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
			# S49: the Relations page (karma, bonds, grudges, Fame) lives under Character.
			var rb := Rect2(r.end.x - 250, r.position.y + 196, 220, 52)
			btn(rb, Tx.t("ui.character.relations"), "relations", null, false, true, "", 20)
			text(Vector2(rb.position.x, rb.end.y + 22), fit(Tx.t("ui.relations.fame_" + str(Game.relations.fame_tier(ch).get("id", "unknown"))) + "  ·  " +
				Tx.t("ui.relations.align_" + Game.relations.alignment_word(ch)), 15, rb.size.x), 15, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, rb.size.x)
			if ch.cultivator.active_title != "": text(Vector2(x, r.position.y + 300), Tx.t("ui.character.title") % ContentDB.name_of("titles", ch.cultivator.active_title), 19, UiKit.BRIGHT_JADE)
			_vitals(ch, Rect2(x, r.position.y + 322, r.end.x - x - 30, r.end.y - r.position.y - 340))
			_party(ch, Rect2(r.position.x + 30, r.end.y - 80, 420, 70))
		"stats":
			for i in STATS.size():
				var s: Array = STATS[i]
				var col := i / 8
				var row := i % 8
				var v = ch.stats.value(s[0])
				var shown := UiKit.fmt(v) if absf(v) >= 10.0 or s[0] in ["max_hp", "max_qi", "max_soul"] else ("%.1f%%" % (v * 100.0) if s[0] in ["crit_chance", "crit_damage", "drop_rate"] else "%.2f" % v)
				text(Vector2(r.position.x + 40 + col * 520, r.position.y + 50 + row * 48), s[1], 20, UiKit.MIST)
				text(Vector2(r.position.x + 40 + col * 520, r.position.y + 50 + row * 48), shown, 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 440)
		"aptitude": _aptitude(ch, r)
		"titles":
			var titles: Array = ch.cultivator.titles
			if titles.is_empty(): text(r.position + Vector2(0, 80), Tx.t("ui.character.earn_titles_from_achievements_and"), 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
			for i in titles.size():
				var tid := str(titles[i])
				var tr := Rect2(r.position.x + 30, r.position.y + 20 + i * 64, 600, 56)
				btn(tr, ContentDB.name_of("titles", tid), "title", tid, ch.cultivator.active_title == tid)
				var bonus: Array = []
				for m in ContentDB.entry("titles", tid).get("modifiers", []): bonus.append(UiKit.affix_text(m))
				text(Vector2(tr.end.x + 24, tr.position.y + 36), ", ".join(bonus), 18, UiKit.BRIGHT_JADE if ch.cultivator.active_title == tid else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.end.x - tr.end.x - 48)
		"attunement": _attunement(ch, r)
		"wardrobe": _wardrobe(ch, r)

## S47 wardrobe: for each slot, any look you have ever worn can stand in for the piece's own.
const WARDROBE_SLOTS := [["robe", "shirt"], ["trousers", "pants"], ["boots", "shoes"], ["hat", "hat"], ["weapon", "weapon"]]
func _wardrobe(ch, r: Rect2) -> void:
	if not Unlocks.is_unlocked(ch.id, "wardrobe"):
		para(Rect2(r.position.x + 380, r.position.y + 40, r.size.x - 420, 200), Unlocks.locked_text("wardrobe"), 20, UiKit.HOLLOW)
		return
	var x := r.position.x + 380
	var y := r.position.y + 34
	text(Vector2(x, y), Tx.t("ui.character.wardrobe_help"), 17, UiKit.MIST)
	y += 22
	for pair in WARDROBE_SLOTS:
		var slot: String = pair[0]
		var cat: String = pair[1]
		var looks: Array = []
		for k in Game.account.wardrobe_unlocked:
			if str(k).begins_with(cat + ":"): looks.append(str(k).get_slice(":", 1))
		looks.sort()
		var cur := str(ch.inventory.appearance_override.get(slot, ""))
		text(Vector2(x, y + 34), Tx.t("ui.character.wardrobe_" + slot), 18, UiKit.PALE_GOLD)
		var bx := x + 130.0
		btn(Rect2(bx, y + 8, 120, 40), Tx.t("ui.character.own_look"), "look", [slot, ""], cur == "", true, "", 15)
		bx += 128
		for lk in looks:
			if bx + 120 > r.end.x - 20: break
			btn(Rect2(bx, y + 8, 120, 40), str(lk).replace("_", " ").capitalize(), "look", [slot, lk], cur == lk, true, "", 15)
			bx += 128
		y += 58

## S18 attunement: the four jades of the zone you stand in (or the first zone that asks for
## attunement), what raising each costs, and how the total compares with each region's need.
func _attunement(ch, r: Rect2) -> void:
	var here := str(ContentDB.zone_of_room(str(ch.position.get("room", ""))).get("id", ""))
	var zone_id := ""
	for z in ContentDB.all("zones"):
		if z.get("attunement") is Dictionary and (zone_id == "" or str(z.id) == here): zone_id = str(z.id)
	if zone_id == "":
		para(r.grow(-40), Tx.t("ui.character.no_attunement_yet"), 20, UiKit.HOLLOW)
		return
	var zone := ContentDB.zone(zone_id)
	var att: Dictionary = zone.attunement
	var x := r.position.x + 36
	heading(Vector2(x, r.position.y + 48), "%s · %s" % [str(att.get("name", "")), str(zone.get("name", ""))], r.size.x - 72)
	var total: float = Game.progression.attunement_value(ch, zone_id) if here == zone_id else float(ch.cultivator.attunement.get(zone_id, 0.0))
	var line := Tx.t("ui.character.attunement_total") % int(total)
	if here == zone_id:
		var need: float = Game.progression.attunement_required(str(ch.position.get("room", "")))
		var f: Dictionary = Game.progression.attunement_factors(ch)
		line += "   " + Tx.t("ui.character.attunement_here") % [int(need), int(round(float(f.dealt) * 100.0)), int(round(float(f.taken) * 100.0))]
	text(Vector2(x, r.position.y + 84), fit(line, 19, r.size.x - 72), 19, UiKit.MIST)
	var unlocked := Unlocks.is_unlocked(ch.id, str(att.get("unlock", "")))
	var shard := str(att.get("shard", ""))
	icon_at(Rect2(r.end.x - 250, r.position.y + 26, 36, 36), shard)
	text(Vector2(r.end.x - 206, r.position.y + 52), "%s × %s" % [ContentDB.item_name(shard), UiKit.fmt(ch.inventory.count(shard))], 18, UiKit.PALE_GOLD)
	var levels: Array = Game.progression.jade_levels(ch, zone_id)
	var jades: Array = att.get("jades", [])
	var cw := (r.size.x - 72 - 3 * 16) / 4.0
	for i in jades.size():
		var jr := Rect2(x + i * (cw + 16), r.position.y + 104, cw, 236)
		panel(jr, "minor_panel")
		icon_at(Rect2(jr.position.x + (cw - 88) / 2.0, jr.position.y + 12, 88, 88), "ward_" + str(jades[i].id))
		text(Vector2(jr.position.x, jr.position.y + 128), str(jades[i].name), 19, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cw)
		var lv := int(levels[i]) if i < levels.size() else 0
		var top := int(att.get("jade_max", 15))
		bar(Rect2(jr.position.x + 14, jr.position.y + 142, cw - 28, 20), float(lv) / maxf(1.0, top), UiKit.QI, Tx.t("ui.character.jade_level") % [lv, top])
		if lv >= top:
			text(Vector2(jr.position.x, jr.position.y + 204), Tx.t("ui.character.jade_full"), 17, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_CENTER, cw)
		else:
			var cost: int = Game.progression.jade_cost(zone_id, lv)
			var can: bool = unlocked and ch.inventory.count(shard) >= cost
			btn(Rect2(jr.position.x + 14, jr.position.y + 174, cw - 28, 48), Tx.t("ui.character.raise_jade") % cost, "attune", [zone_id, i], false, can,
				Unlocks.locked_text(str(att.get("unlock", ""))) if not unlocked else Tx.t("ui.character.needs_more_shards"), 17)
	# What each region asks for, ticked when the total meets it.
	var y := r.position.y + 366
	text(Vector2(x, y), Tx.t("ui.character.regions_ask"), 18, UiKit.GOLD)
	y += 4
	var col := 0
	for reg in zone.get("regions", []):
		if not reg.has("attunement"): continue
		var met := total >= float(reg.attunement)
		var at := Vector2(x + col * ((r.size.x - 72) / 2.0), y + 30)
		text(at, fit(("✓ " if met else "· ") + "%s  %d" % [str(reg.name), int(reg.attunement)], 17, (r.size.x - 72) / 2.0 - 12), 17, UiKit.BRIGHT_JADE if met else UiKit.MIST)
		col += 1
		if col == 2:
			col = 0
			y += 26

## Pools (QI and Soul only once the character has them), four headline stats and who travels along.
func _vitals(ch, r: Rect2) -> void:
	var y := r.position.y
	var pools := [["hp", ch.pools.hp, ch.pools.max_hp, UiKit.RED, Tx.t("ui.character.hp_bar")]]
	if ch.pools.max_qi > 0.0: pools.append(["qi", ch.pools.qi, ch.pools.max_qi, UiKit.QI, Tx.t("ui.character.qi_bar")])
	if ch.pools.max_soul > 0.0: pools.append(["soul", ch.pools.soul, ch.pools.max_soul, UiKit.SOUL, Tx.t("ui.character.soul_bar")])
	for p in pools:
		bar(Rect2(r.position.x, y, r.size.x, 24), float(p[1]) / maxf(1.0, float(p[2])), p[3], p[4] % [int(p[1]), int(p[2])])
		y += 30
	y += 4
	var picks := [["physical_attack", Tx.t("ui.character.physical_attack")], ["qi_attack", Tx.t("ui.character.qi_attack")],
		["physical_defense", Tx.t("ui.character.physical_defence")], ["move_speed", Tx.t("ui.character.move_speed")]]
	var cw := r.size.x / 2.0
	for i in picks.size():
		var at := Vector2(r.position.x + (i % 2) * cw, y + (i / 2) * 30 + 20)
		text(at, str(picks[i][1]), 18, UiKit.MIST)
		text(at, UiKit.fmt(ch.stats.value(str(picks[i][0]))), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, cw - 24)

## Who travels along: the active spirit animal and companions, under the portrait.
func _party(ch, r: Rect2) -> void:
	var pet: Dictionary = Game.pets.active_pet(ch)
	var mates: Array = (ch.companions.get("active", []) as Array).map(func(cid): return ContentDB.name_of("companions", str(cid)))
	if not pet.is_empty(): text(Vector2(r.position.x, r.position.y + 20), fit(Tx.t("ui.character.spirit_animal") % str(pet.name), 17, r.size.x), 17, UiKit.BRIGHT_JADE)
	if not mates.is_empty(): text(Vector2(r.position.x, r.position.y + 48), fit(Tx.t("ui.character.companions") % ", ".join(mates), 17, r.size.x), 17, UiKit.BRIGHT_JADE)

func on_action(id: String, data) -> void:
	if id == "relations": navigate.emit("relations", {})
	if id == "title": submit({"type": "set_title", "title": str(data)})
	if id == "attune": submit({"type": "attune_jade", "zone": str(data[0]), "index": int(data[1])})
	if id == "look":
		submit({"type": "set_appearance", "slot": str(data[0]), "look": str(data[1])})
		if is_instance_valid(doll): doll.outfit = InventoryAuthority.outfit_for(c())

## Aptitude (S08, S48): the hidden rolls as they are revealed, the root they name, and the physiques earned.
func _aptitude(ch, r: Rect2) -> void:
	var cu: CultivatorState = ch.cultivator
	var left := Rect2(r.position.x, r.position.y, 560, r.size.y)
	var right := Rect2(left.end.x + 20, r.position.y, r.end.x - left.end.x - 20, r.size.y)
	panel(left)
	panel(right)
	var x := left.position.x + 24
	var y := left.position.y + 20
	var root := ProgressionRules.root_name(cu)
	if root != "":
		text(Vector2(x, y + 30), Tx.t("ui.character.root." + root), 28, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, left.size.x - 48, true)
		y += 40
		y += para(Rect2(x, y, left.size.x - 48, 60), Tx.t("ui.character.root_desc." + root), 16, UiKit.MIST, 2) + 10
	else:
		text(Vector2(x, y + 30), Tx.t("ui.character.root_hidden"), 20, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, left.size.x - 48)
		y += 52
	var reveal := {"physique": "bone_forging_4", "spirit_aptitude": "spirit_awakening_1", "comprehension": ""}
	var order: Array = []
	for k in ["physique", "spirit_aptitude", "comprehension"]:
		if cu.aptitude.has(k): order.append(k)
	var elements: Array = []
	for k in cu.aptitude:
		if str(k).begins_with("element_"): elements.append(str(k))
	elements.sort()
	order.append_array(elements)
	for k in order:
		var a: Dictionary = cu.aptitude[k]
		var key := str(k)
		var label := Tx.t("ui.character.apt." + key) if not key.begins_with("element_") else Tx.t("ui.character.apt_element") % key.trim_prefix("element_").capitalize()
		text(Vector2(x, y + 24), label, 19, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 260)
		if a.get("revealed", false):
			var v := float(a.get("value", 0.0))
			text(Vector2(x + 280, y + 24), "%s%d%%" % ["+" if v >= 0.0 else "-", int(round(absf(v) * 100))], 19, UiKit.BRIGHT_JADE if v > 0.0 else (UiKit.RED if v < 0.0 else UiKit.PAPER))
		else:
			var at := str(reveal.get(key, "bone_forging_7"))
			text(Vector2(x + 280, y + 24), Tx.t("ui.character.apt_hidden_at") % ContentDB.name_of("realms", at) if at != "" else Tx.t("ui.character.unknown_revealed_as_you_grow"), 16, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, left.size.x - 330)
		y += 34
	# Physiques: earned by deeds; the ones not yet earned say how.
	var rx := right.position.x + 24
	var ry := right.position.y + 44
	heading(Vector2(rx, ry), Tx.t("ui.character.physiques"), right.size.x - 48)
	ry += 16
	for ph in ContentDB.all("physiques"):
		if str(ph.get("milestone", "")) != "" and not str(ph.id) in cu.physiques: continue
		var have := str(ph.id) in cu.physiques
		text(Vector2(rx, ry + 26), str(ph.get("name", "")), 20, UiKit.PALE_GOLD if have else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 48)
		if have:
			var gift := str(ph.get("gift_text", ""))
			text(Vector2(rx, ry + 48), gift, 15, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 48)
			var gw := UiKit.text_width(gift + "  ", 15)
			text(Vector2(rx + gw, ry + 48), str(ph.get("drawback_text", "")), 15, Color("e07a7a"), HORIZONTAL_ALIGNMENT_LEFT, maxf(40.0, right.size.x - 48 - gw))
		else:
			var prog := ""
			if ph.has("count"): prog = "  (%s / %s)" % [UiKit.fmt(float(cu.lifetime_stats.get(str(ph.earned), 0.0))), UiKit.fmt(float(ph.count))]
			text(Vector2(rx, ry + 48), str(ph.get("earned_text", "")) + prog, 15, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 48)
		ry += 62
