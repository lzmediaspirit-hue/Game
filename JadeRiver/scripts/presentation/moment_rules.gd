class_name MomentRules
extends RefCounted
## The pure half of the moments system (docs/moments_design.md §3.4, §5): the matchers a row's `when` may use, the
## rare-drop rule, the text and colour sources of data/moments.json, and the closed lists data_validation checks the
## file against. Static and side-free: it reads data and the payload it is handed, and writes nothing.

## Matchers with a rule of their own; any other key of `when` tests the payload key of that name for equality.
const MATCHERS := ["actor", "target", "role_in", "first_in_room", "chapter_end", "rare", "source_in", "level_mod"]
## Every layer kind and where it plays: under or over the HUD (drawn by MomentView), through the HUD, or in the world.
const LAYER_KINDS := {"dim": "under", "vignette": "under", "flash": "under", "letterbox": "under",
	"band": "over", "strip": "over", "card": "over", "stats": "over", "chip": "over", "seal": "over", "stamps": "over", "subtitle": "over",
	"toast": "hud", "caption": "hud",
	"fx": "world", "text": "world", "shake": "world", "camera": "world", "sound": "world", "buzz": "world", "bark": "world",
	"fountain": "world", "beam": "world"}
const ANCHORS := ["actor", "enemy", "pet", "drop", "item", "camera"]
const SHAPES := ["strike", "wave", "ring", "rain", "pillar", "domain", "bolt"]
const STYLES := ["square", "ink", "ring", "ember", "shard"]

static var _tokens: Dictionary = {}

static func cfg() -> Dictionary:
	return ContentDB.config("moments")

## True when every matcher of `when` holds for payload `p`. `ctx`: `active` (the active character's id) and `seen`
## (the enemy uids already met in this room, for first_in_room).
static func matches(when: Dictionary, p: Dictionary, ctx: Dictionary) -> bool:
	for k in when:
		var want = when[k]
		var ok := true
		match str(k):
			"actor", "target": ok = str(p.get(k, "")) == str(ctx.get("active", ""))
			"role_in": ok = str(ContentDB.entry("enemies", str(p.get("def", p.get("enemy", "")))).get("role", "")) in want
			"first_in_room": ok = bool(want) != (ctx.get("seen", {}) as Dictionary).has(int(p.get("enemy", 0)))
			"chapter_end": ok = bool(want) == (cfg().get("chapter_ends", {}) as Dictionary).has(str(p.get("quest", "")))
			"rare": ok = bool(want) == (p.get("items", []) as Array).any(func(i): return is_rare(i))
			"source_in": ok = str(p.get("source", "")) in want
			"level_mod": ok = int(p.get("level", 0)) % maxi(1, int(want)) == 0
			_: ok = p.get(k) == want
		if not ok: return false
	return true

## A rare find (§3.4): a Perfect or Relic piece, a legend piece, a spirit animal's book, a treasure, or one of the named
## drops (a boss's unique drop, a first-defeat reward, a set piece, a legendary chain's piece). Coins never.
static func is_rare(i: Dictionary) -> bool:
	if int(i.get("coins", 0)) > 0: return false
	var r: Dictionary = cfg().get("rare", {})
	var id := str(i.get("item", ""))
	return str(i.get("quality", "")) in r.get("qualities", []) or str(ContentDB.item(id).get("type", "")) in r.get("types", []) \
		or (r.get("items", {}) as Dictionary).has(id)

## A loot entry's colour: its quality's, or for a common piece its item's grade (§6 rule 4).
static func item_color(i: Dictionary) -> Color:
	var q := str(i.get("quality", "common"))
	return UiKit.quality_color(q) if q != "common" else UiKit.grade_color(str(ContentDB.item(str(i.get("item", ""))).get("grade", "common")))

## A reference inside a row: "payload.<key>"; "slot.<path>" into what the view keeps for the play (an absorbed event's
## payload by its slot, `last.<event>` the last payload of an event, `now` and `before` the stat snapshots); "item.<field>"
## (the payload item's data); or a plain value.
static func value(ref, p: Dictionary, slots := {}):
	if not (ref is String): return ref
	if ref.begins_with("payload."): return p.get(ref.trim_prefix("payload."), "")
	if ref.begins_with("slot."):
		var node = slots
		for part in ref.trim_prefix("slot.").split("."):
			if node is Array: node = node[0] if not node.is_empty() else {}
			node = (node as Dictionary).get(part, 0) if node is Dictionary else 0
		return node
	if ref.begins_with("item."): return ContentDB.item(str(p.get("item", ""))).get(ref.trim_prefix("item."), "")
	if ref.begins_with("enemy."):   # the payload's enemy as the room has it (a boss's level), read only
		var e = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
		return e.get(ref.trim_prefix("enemy.")) if e != null else 0
	return ref

## A payload value as a key part: a whole number read back from JSON (2.0) is "2".
static func id_of(v) -> String:
	return str(int(v)) if v is float and v == floorf(v) else str(v)

## A text source (§3.4) as the words the player reads; "" when it names nothing, or when its `if_slot` is empty.
static func text(src, p: Dictionary, slots := {}) -> String:
	if not (src is Dictionary): return str(value(src, p, slots))
	if src.is_empty() or (src.has("if_slot") and not slots.has(str(src.if_slot))) or (src.has("if") and not p.get(str(src.if), false)): return ""
	if src.has("first"):   # the first source that says something (a boss's epithet, else its level)
		for s in src.first:
			var t := text(s, p, slots)
			if t != "": return t
		return ""
	var v = value(src.values()[0], p, slots)
	if src.has("key"):   # with `plural`, the count that picks the key's "_one" twin (Tx.plural)
		var k := str(src.key) + (id_of(value(src.suffix, p, slots)) if src.has("suffix") else "")
		var s := Tx.plural(k, int(value(src.plural, p, slots))) if src.has("plural") else Tx.t(k)
		var args: Array = (src.get("args", []) as Array).map(func(a): return text(a, p, slots) if a is Dictionary else value(a, p, slots))
		return s % args if not args.is_empty() else s
	if src.has("realm"): return ContentDB.realm_label(str(v))
	if src.has("realm_great"): return Tx.t("realm_great." + ProgressionRules.great_realm(str(v)))
	if src.has("transition"):
		return Tx.t("moment.transition") % [Tx.t("realm." + str(value(src.transition[0], p, slots))), Tx.t("realm." + str(value(src.transition[1], p, slots)))]
	if src.has("stage"): return str(int(ContentDB.realm(str(v)).get("sub", 0)))
	if src.has("name_of"): return ContentDB.name_of(str(src.name_of), str(value(src.id, p, slots)))
	if src.has("item"): return ContentDB.item_name(str(v))
	if src.has("craft"): return Tx.t("craft." + str(v))
	if src.has("boss"):
		var k := "boss.%s.%s" % [str(value(src.id, p, slots)), str(src.boss)]
		return Tx.t(k) if ContentDB.strings.has(k) else ""
	if src.has("field_of"):   # one line of a data row: a Dao's tier line ({"field_of": "daos", "field": "tiers", "at": tier})
		var f = ContentDB.entry(str(src.field_of), str(value(src.id, p, slots))).get(str(src.field), "")
		if f is Array: f = f[clampi(int(value(src.get("at", 1), p, slots)) - 1, 0, f.size() - 1)] if not f.is_empty() else ""
		return str(f)
	if src.has("affixes_of"):   # a title's bonus, as the Character page writes it
		return ", ".join(ContentDB.entry(str(src.affixes_of), str(value(src.id, p, slots))).get("modifiers", []).map(func(m): return UiKit.affix_text(m)))
	if src.has("chapter_of"):   # the chapter a main quest closes, or the Prologue
		var ch := str(cfg().get("chapter_ends", {}).get(str(v), ""))
		return "" if ch == "" else (Tx.t("moment.story.prologue") if ch == "prologue" else Tx.t("moment.story.chapter") % ch)
	if src.has("pet"):   # the active character's spirit animal by uid
		var c = Game.active()
		for pt in (c.pets if c else []):
			if str(pt.uid) == str(v): return str(pt.name)
		return ""
	if src.has("pet_form"):   # the form it grew into: its branch, else its stage's name
		var branch := str(value(src.get("branch", ""), p, slots))
		if branch != "": return branch
		for s in ContentDB.config("pet_growth").get("stages", []):
			if str(s.id) == str(v): return str(s.get("name", ""))
		return ""
	return str(v)   # {"payload": "payload.name"}: a value that is already player text

## A colour (§3.4, §6): a UiKit token name, or element:, grade:, quality: or dao: with an id or a reference (a Dao takes
## its element's colour, or its family's from moments.json dao_colours).
static func color(spec, p := {}, slots := {}) -> Color:
	var s := str(spec)
	var id := str(value(s.get_slice(":", 1), p, slots))
	if s.begins_with("element:"): return SpriteCache.element_color(id)
	if s.begins_with("grade:"): return UiKit.grade_color(id)
	if s.begins_with("quality:"): return UiKit.quality_color(id)
	if s.begins_with("dao:"):
		var fam := str(ContentDB.entry("daos", id).get("family", ""))
		var by_family = cfg().get("dao_colours", {}).get(fam)
		return SpriteCache.element_color(id) if fam == "element" else (color(by_family) if by_family != null else UiKit.PALE_GOLD)
	return tokens().get(s, UiKit.PAPER)

## One row of the escalation curve (§5.2), tier 1 to 7.
static func tier(n: int) -> Dictionary:
	var t: Array = cfg().get("vfx_tiers", [])
	return t[clampi(n, 1, t.size()) - 1] if not t.is_empty() else {}

## The curve's row for a hit's or a cast's source: "tech:<id>" its technique's tier; "ally:tech:<id>" one tier below
## (a companion's or a spirit animal's technique stays under the player's own); anything else tier 1 (a basic blow,
## and an ally's own blow, "ally:<uid>").
static func tier_numbers(source: String) -> Dictionary:
	var ally := source.begins_with("ally:")
	var id := source.trim_prefix("ally:")
	var n := int(ContentDB.entry("techniques", id.trim_prefix("tech:")).get("vfx", {}).get("tier", 1)) if id.begins_with("tech:") else 1
	return tier(maxi(1, n - (1 if ally else 0)))

## A hit spark's style (§5.6): the weapon family's, else Soul's ring, else the element's, else squares.
static func particle_style(family: String, element: String, dtype := "") -> String:
	var p: Dictionary = cfg().get("particles", {})
	var s := str(p.get("families", {}).get(family, ""))
	if s == "" and dtype == "soul": s = "ring"
	return s if s != "" else str(p.get("elements", {}).get(element, p.get("default", "square")))

## A shake's amplitude in px (§4.6): none with Screen shake off or Reduce motion on, else `amp`, or s × shake_amp_per_s.
static func shake_amp(s: float, amp := -1.0) -> float:
	var st: Dictionary = Game.account.settings
	if not st.get("screen_shake", true) or st.get("reduce_motion", false): return 0.0
	return amp if amp >= 0.0 else s * float(cfg().get("settings", {}).get("shake_amp_per_s", 16))

## A particle count under the settings: Reduce motion thins it to tier 1's sparks, Battery saver to tier 2's.
static func particle_count(n: int) -> int:
	var st: Dictionary = Game.account.settings
	if st.get("reduce_motion", false): return mini(n, int(tier(1).get("spark_count", n)))
	if st.get("battery_saver", false): return mini(n, int(tier(2).get("spark_count", n)))
	return n

## The character's aura (moments.json `auras`, research player_motivation §5 change 10): the tier of the highest row whose
## realm it has reached, 0 before Bone Forging 1. `aura(tier)` is that row.
static func aura_tier(c) -> int:
	var n := 0
	var rows: Array = cfg().get("auras", [])
	for i in rows.size():
		if ProgressionRules.at_least(c.cultivator.realm_key, str(rows[i].realm)): n = i + 1
	return n

static func aura(n: int) -> Dictionary:
	var rows: Array = cfg().get("auras", [])
	return rows[n - 1] if n >= 1 and n <= rows.size() else {}

## UiKit's colour tokens by name, the only colours a row may name.
static func tokens() -> Dictionary:
	if _tokens.is_empty():
		var consts: Dictionary = load("res://scripts/ui/ui_kit.gd").get_script_constant_map()
		for k in consts:
			if consts[k] is Color: _tokens[k] = consts[k]
	return _tokens
