class_name EquipPrompt
extends RefCounted
## The HUD's equip prompt: a piece picked up or received that is better than the one worn in its slot (an empty slot
## counts as worse), and that the character may wear now, is offered in a small card at the right of the screen for
## LIFE_S: its icon and name, the gain the Bag's card names first and Combat Power (StatRules.equip_change through
## InventoryPage.card_rows, so the two never disagree), an Equip button (the equip intent: the Inventory authority wears
## it) and a close ×. The card stands clear of the HUD's controls, the purse and the clear zone (RECT, held by the
## hud_suite), and only its two buttons take a tap, so a fight's input goes on round it. One at a time: the rest wait in
## turn, each judged again when its turn comes. It slides in from the edge, or with Reduce motion on appears in place.

const InventoryPage = preload("res://scripts/ui/pages/inventory_page.gd")
const CharacterPage = preload("res://scripts/ui/pages/character_page.gd")

## Under the purse and the auto-hunt toggle's row, left of the toggle, right of the clear zone, above ring 2's context.
const RECT := Rect2(904, 262, 284, 96)

## The item's name size on the card: 18, a step or more smaller when the name would not fit its 168 px whole (the
## prototype's QA: the first weapon read "Training Short Bl…").
static func name_size(item_name: String) -> int:
	var s := 18
	while s > 14 and UiKit.text_width(item_name, s) > 168.0: s -= 1
	return s
const LIFE_S := 10.0
const SLIDE_S := 0.25
const FADE_S := 0.3
## Pieces coming back from where the player put them are not news.
const SKIP_SOURCES := ["withdraw", "buyback"]

var queue: Array = []     # uids waiting their turn
var current := {}         # {uid, item, slot, quality, gain (a card row or {}), cp (the Combat Power row), t}

## An item_added payload: an equipment piece for a worn slot joins the queue (judged when its turn comes).
func offer(p: Dictionary) -> void:
	if int(p.get("uid", -1)) < 0 or str(p.get("source", "")) in SKIP_SOURCES: return
	if not str(ContentDB.item(str(p.get("item", ""))).get("slot", "")) in InventoryState.SLOTS: return
	if int(current.get("uid", -1)) == int(p.uid) or queue.has(int(p.uid)): return
	queue.append(int(p.uid))

## What the prompt would say of the piece `uid` in `c`'s bag: {} unless it is in the bag, `c` may wear it now, and its
## slot is empty or wearing it in place of the worn one raises Combat Power (`cp`, the Combat Power row while it rises).
static func judge(c, uid: int) -> Dictionary:
	var i := bag_index(c, uid)
	if i < 0: return {}
	var inst: Dictionary = c.inventory.bag[i]
	var def := ContentDB.item(str(inst.id))
	var slot := str(def.get("slot", ""))
	if not slot in InventoryState.SLOTS or def.get("type") != "equipment" or Game.inventory.wear_check(c, def) != "": return {}
	var rows := InventoryPage.card_rows(StatRules.equip_change(c, slot, inst))
	var cp: Dictionary = rows[-1]
	var empty: bool = c.inventory.equipped.get(slot) == null
	var rises := float(cp.after) > float(cp.before) + 0.5
	if not empty and not rises: return {}
	var gains: Array = rows.slice(0, -1).filter(func(rw): return float(rw.after) > float(rw.before))
	return {"uid": uid, "item": str(inst.id), "slot": slot, "quality": str(inst.get("quality", "common")), "gain": gains[0] if not gains.is_empty() else {},
		"cp": cp if rises else {}, "empty": empty, "t": 0.0}

static func bag_index(c, uid: int) -> int:
	for i in c.inventory.bag.size():
		var s = c.inventory.bag[i]
		if s != null and int(s.get("uid", -2)) == uid: return i
	return -1

## Time passes: the card shown ages and goes at LIFE_S, or at once when its piece is worn or gone; then the next waiting
## that is still better takes its place.
func tick(c, delta: float) -> void:
	if not current.is_empty():
		if bag_index(c, int(current.uid)) < 0: current = {}
		else:
			current.t = float(current.t) + delta
			if float(current.t) >= LIFE_S: current = {}
	while current.is_empty() and not queue.is_empty(): current = judge(c, int(queue.pop_front()))

func dismiss() -> void:
	current = {}

## The card where it stands now: sliding in from the right edge over SLIDE_S, unless `still` (Reduce motion).
func rect(still: bool) -> Rect2:
	if current.is_empty(): return Rect2()
	var k := 1.0 if still else clampf(float(current.t) / SLIDE_S, 0.0, 1.0)
	return Rect2(RECT.position + Vector2((1.0 - k * (2.0 - k)) * (1280.0 - RECT.position.x), 0.0), RECT.size)

## The two buttons' tap areas (48 px tall or more), where the card stands at rest.
static func equip_hit() -> Rect2:
	return Rect2(RECT.position + Vector2(186, 48), Vector2(92, 48))

static func close_hit() -> Rect2:
	return Rect2(RECT.position + Vector2(236, 0), Vector2(48, 48))

## "prompt:equip" or "prompt:close" for a tap on the card's buttons, else "" (the tap goes on to the HUD).
func role_at(p: Vector2) -> String:
	if current.is_empty(): return ""
	if equip_hit().has_point(p): return "prompt:equip"
	if close_hit().has_point(p): return "prompt:close"
	return ""

## Equip: the intent, with the piece's place in the bag now. The card goes once it is worn (tick sees it leave the bag).
func equip(c) -> Dictionary:
	var i := bag_index(c, int(current.get("uid", -1)))
	if i < 0: return {"ok": false}
	var r: Dictionary = Game.submit({"type": "equip", "index": i})
	if r.get("ok", false): current = {}
	return r

## The gain lines: the first stat the card names that rises, then Combat Power, each with its rise.
func gain_lines() -> Array:
	var out: Array = []
	for rw in [current.get("gain", {}), current.get("cp", {})]:
		if (rw as Dictionary).is_empty(): continue
		out.append("%s ▲ %s" % [Tx.t(InventoryPage.stat_key(str(rw.stat))), CharacterPage.stat_text(str(rw.stat), float(rw.after) - float(rw.before)).trim_prefix("+")])
	return out

## Test hook: rules_tests reads the gain lines as one.
func gain_text() -> String:
	return " · ".join(gain_lines())

func draw(ci: CanvasItem, still: bool) -> void:
	if current.is_empty(): return
	var r := rect(still)
	var a := clampf((LIFE_S - float(current.t)) / FADE_S, 0.0, 1.0)
	ci.draw_style_box(UiKit.style("toast"), r)
	var slot_word := Tx.t("ui.inventory." + str(current.slot)).to_lower()
	var head := Tx.t("hud.equip_prompt.empty" if current.get("empty", false) else "hud.equip_prompt.better") % slot_word
	SpriteCache.draw_icon(ci, Rect2(r.position + Vector2(12, 12), Vector2(40, 40)), str(current.item), Color(1, 1, 1, a))
	UiKit.draw_text(ci, UiKit.fit(head, 14, 168), r.position + Vector2(62, 26), 14, Color(UiKit.GOLD, a), HORIZONTAL_ALIGNMENT_LEFT, 168)
	var item_name := ContentDB.item_name(str(current.item))
	var ns := name_size(item_name)
	UiKit.draw_text(ci, UiKit.fit(item_name, ns, 168), r.position + Vector2(62, 48), ns,
		Color(UiKit.quality_color(str(current.quality)), a), HORIZONTAL_ALIGNMENT_LEFT, 168)
	var lines := gain_lines()
	for i in lines.size(): UiKit.draw_text(ci, UiKit.fit(str(lines[i]), 14, 172), r.position + Vector2(12, 70 + i * 17), 14, Color(UiKit.BRIGHT_JADE, a), HORIZONTAL_ALIGNMENT_LEFT, 172)
	var eq := Rect2(r.position + Vector2(190, 54), Vector2(84, 36))
	ci.draw_style_box(UiKit.style("button_primary"), eq)
	UiKit.draw_inked(ci, Tx.t("ui.inventory.equip"), eq.position + Vector2(0, 24), 16, Color(UiKit.PALE_GOLD, a), HORIZONTAL_ALIGNMENT_CENTER, eq.size.x)
	var x := r.position + Vector2(260, 24)
	for d in [Vector2(-7, -7), Vector2(7, -7)]: ci.draw_line(x + d, x - d, Color(UiKit.PAPER, a), 2.0)
	# The time left, a thin line draining along the foot.
	var left := clampf(1.0 - float(current.t) / LIFE_S, 0.0, 1.0)
	ci.draw_rect(Rect2(r.position + Vector2(10, r.size.y - 6), Vector2((r.size.x - 20) * left, 2)), Color(UiKit.PALE_GOLD, 0.7 * a))
