extends Page
## Characters (S23): every slot with realm and idle task; set this character's idle
## task; switch characters in a safe place.
## P5 (docs/page_identity.md row 32): the sect's roster handscroll on the hall's timber wall between two red pillars.
## Every disciple of the account is painted standing in one procession along the scroll, unrolled from the left: the
## live figure at 2 px an art px, what they are about as a small sign at their feet, and a column of name, realm and
## task in ink; the one you play carries the red "playing" seal. An open slot is a blank stretch of paper ("a new
## disciple"); the tight roll at the right end is as thick as the slots still to come, the next gates on paper tags
## hung from it. A tap on a disciple chooses them: under the scroll, the one you play sets the task it keeps when you
## switch away, and another offers Switch. The scroll unrolls as the page opens; under Reduce motion it only fades in.

const SectKit = preload("res://scripts/ui/pages/sect_kit.gd")

var TASKS := [["seclusion", Tx.t("ui.characters.seclusion")], ["train", Tx.t("ui.characters.train")], ["hunt", Tx.t("ui.characters.hunt")], ["gather", Tx.t("ui.characters.gather")], ["rest", Tx.t("ui.characters.rest")]]
## Each task's sign at a figure's feet (a HUD glyph); a post shows its craft's.
const TASK_ICON := {"seclusion": "seclusion", "train": "fist", "hunt": "jian", "gather": "gather", "rest": "cultivate"}

const WALL := Rect2(64, 32, 1152, 656)
const ROD_X := 96.0
const PAPER_TOP := 128.0
const PAPER_H := 344.0
const STRETCH := 184.0      # one disciple's stretch of the scroll
const MARGIN := 20.0        # the paper before the first and after the last
const SHOWN := 5            # stretches unrolled at once; more are a turn of the scroll away
const FIG_SCALE := 1.0      # 2 screen px an art px
const TAGS := 3             # the gates hung from the roll
const TAG := Vector2(200, 48)
const BELOW := Rect2(104, 488, 856, 184)   # the chosen disciple's tasks and Switch, under the scroll

var chosen := -1            # the slot chosen on the scroll (the one you play at first)
var page_at := 0            # the first slot unrolled, when more than SHOWN are open
var figs := {}

func _init() -> void:
	title = Tx.t("ui.characters.characters")
	identity = Identity.new("wood_dark", false, "own", "handscroll_procession_roll", 0.35)

func setup() -> void:
	chosen = Game.account.active_slot if Game.account != null else 1
	page_at = clampi(chosen - SHOWN, 0, maxi(0, _slots() - SHOWN))

func _slots() -> int:
	return Game.account.slots_unlocked if Game.account != null else 1

func content_rect() -> Rect2:
	return Rect2(104, 128, 1080, 544)

func draw_surface(_r: Rect2) -> void:
	SectKit.timber(self, WALL)
	for x in [WALL.position.x + 8.0, WALL.end.x - 24.0]: SectKit.pillar(self, Rect2(x, WALL.position.y + 8, 16, WALL.size.y - 16))

func title_rect() -> Rect2:
	return Rect2(460, 52, 360, 56)

func draw_title_mount(r: Rect2) -> void:
	SectKit.title_board(self, r)

# ------------------------------------------------------------------ the scroll
## The paper unrolled: as long as the stretches shown, from the rod to the roll.
func paper_rect() -> Rect2:
	var n := mini(SHOWN, _slots())
	return Rect2(ROD_X + 12.0, PAPER_TOP, MARGIN * 2.0 + n * STRETCH, PAPER_H)

func stretch_rect(i: int) -> Rect2:
	var p := paper_rect()
	return Rect2(p.position.x + MARGIN + i * STRETCH, p.position.y + 24.0, STRETCH, p.size.y - 48.0)

## The roll's thickness: the slots still to come, each a turn of paper round it.
func roll_w() -> float:
	return 22.0 + 5.0 * float(AccountState.MAX_SLOTS - _slots())

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var live := {}
	var k := unfold()
	var p := paper_rect()
	var shown_w := p.size.x * k
	# The rod at the scroll's start, its knobs past the paper.
	var rod := Rect2(ROD_X, p.position.y - 12, 12, p.size.y + 24)
	rounded(rod.grow(1), 5.0, UiKit.INK)
	hshade(rod, UiKit.SURFACE.wood_dark, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.3))
	for y in [rod.position.y - 8.0, rod.end.y]: rounded(Rect2(rod.position.x - 2, y, 16, 8), 3.0, UiKit.GOLD.lerp(UiKit.BRONZE, 0.4))
	# The paper, and the roll at its unrolled end.
	var shown := Rect2(p.position, Vector2(maxf(24.0, shown_w), p.size.y))
	draw_rect(Rect2(shown.position + Vector2(0, 6), shown.size), Color(UiKit.INK, 0.35))
	face(shown, "handscroll")
	_roll(Rect2(shown.end.x, p.position.y - 8, roll_w(), p.size.y + 16), ch)
	var n := _slots()
	for i in mini(SHOWN, n - page_at):
		var slot := page_at + i + 1
		var sr := stretch_rect(i)
		var a := clampf((shown_w - (sr.get_center().x - p.position.x)) / 80.0, 0.0, 1.0)
		_stretch(ch, slot, sr, a, live, p.position.x + shown_w >= sr.end.x)
	if n > SHOWN:
		btn(Rect2(p.position.x, 72, 64, 48), "◀", "scroll", -1, false, page_at > 0, "", 20)
		btn(Rect2(p.end.x - 64, 72, 64, 48), "▶", "scroll", 1, false, page_at + SHOWN < n, "", 20)
	SectKit.hide_rest(figs, live if confirm.is_empty() else {})
	_below(ch)

## One disciple's stretch: the figure standing, their sign at their feet, their column in ink; the chosen one washed
## in gold. An open slot is blank paper waiting for a new disciple. Its words are written once the paper is unrolled past
## the whole stretch (`open`), so they always sit on the paper.
func _stretch(ch, slot: int, r: Rect2, a: float, live: Dictionary, open: bool) -> void:
	var other = Game.character("c%d" % slot)
	if slot == chosen:
		glow(Rect2(r.position.x + 10, r.position.y + 10, r.size.x - 20, r.size.y - 20), Color(UiKit.GOLD, 0.22 * a))
		draw_line(Vector2(r.position.x + 24, r.end.y - 6), Vector2(r.end.x - 24, r.end.y - 6), Color(UiKit.BRONZE, 0.8 * a), 2.0, true)
	var cx := r.get_center().x
	var feet := Vector2(cx - 6, r.position.y + 150)
	if other == null:
		var dash := Color(UiKit.PAPER_INK, 0.35 * a)
		draw_arc(feet + Vector2(0, -104), 13.0, 0.0, TAU, 24, dash, 2.0, true)
		PostKit.dashed(self, PackedVector2Array([feet + Vector2(-20, 0), feet + Vector2(-16, -86), feet + Vector2(16, -86), feet + Vector2(20, 0), feet + Vector2(-20, 0)]), dash, 6.0)
		if open:
			text(Vector2(r.position.x, r.position.y + 190), Tx.t("ui.characters.new_disciple"), 20, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
			para(Rect2(r.position.x + 16, r.position.y + 202, r.size.x - 32, 60), Tx.t("ui.characters.slot_empty_create_from_the") % slot, 14, RecordsKit.BROWN, 3)
		region(r, "choose", slot)
		return
	var fig := SectKit.figure(self, figs, str(other.id), InventoryAuthority.outfit_for(other), FIG_SCALE)
	SectKit.show(fig, feet, live, str(other.id), a, "idle" if other == ch else "meditate" if str(other.idle_task.get("task", "")) in ["seclusion", "rest"] else "idle")
	var sign := _sign(other)
	if sign != "" and other != ch: icon_at(Rect2(feet + Vector2(26, -32), Vector2(32, 32)), sign, Color(1, 1, 1, a))
	if open:
		text(Vector2(r.position.x + 8, r.position.y + 190), str(other.name), 22, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, r.size.x - 16, true)
		text(Vector2(r.position.x + 8, r.position.y + 216), ContentDB.realm_label(other.cultivator.realm_key, ProgressionRules.level(other)), 16, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_CENTER, r.size.x - 16)
		para(Rect2(r.position.x + 14, r.position.y + 228, r.size.x - 28, 44), Tx.t("ui.characters.playing") if other == ch else task_line(other), 16, RecordsKit.JADE_INK, 2)
		if other == ch: RecordsKit.stamp(self, Vector2(r.end.x - 32, r.position.y + 30), Tx.t("ui.characters.seal_playing"), 30.0)
	region(r, "choose", slot)

## The sign at a disciple's feet: their post's craft, else their idle task ("" for none).
func _sign(other) -> String:
	var post: Dictionary = Game.posts.post_of(other)
	if not post.is_empty(): return "guard" if str(post.get("kind", "")) == "vigil" else "craft_" + str(post.get("craft", ""))
	return str(TASK_ICON.get(str(other.idle_task.get("task", "")), ""))

## The tight roll at the paper's end, thick with the slots still to come; the next gates hang from it on paper tags.
func _roll(r: Rect2, _ch) -> void:
	draw_rect(Rect2(r.position + Vector2(4, 6), r.size), Color(UiKit.INK, 0.35))
	rounded(r.grow(1), r.size.x * 0.5, UiKit.INK)
	var paper := UiKit.SURFACE.scroll
	hshade(Rect2(r.position.x, r.position.y + 10, r.size.x * 0.5, r.size.y - 20), paper.lerp(UiKit.BRONZE, 0.35), paper.lerp(UiKit.PAPER, 0.4))
	hshade(Rect2(r.get_center().x, r.position.y + 10, r.size.x * 0.5, r.size.y - 20), paper.lerp(UiKit.PAPER, 0.4), paper.lerp(UiKit.BRONZE, 0.45))
	for band in [Rect2(r.position.x, r.position.y, r.size.x, 20), Rect2(r.position.x, r.end.y - 20, r.size.x, 20)]:
		rounded(band, 6.0, UiKit.SURFACE.silk)
		draw_rect(Rect2(band.position.x, band.end.y - 2 if band.position.y == r.position.y else band.position.y, band.size.x, 2), Color(UiKit.GOLD, 0.6))
	# A turn of paper for each slot still closed.
	var closed := AccountState.MAX_SLOTS - _slots()
	for i in closed: draw_line(Vector2(r.position.x + 11 + i * 5, r.position.y + 22), Vector2(r.position.x + 11 + i * 5, r.end.y - 22), Color(UiKit.BRONZE, 0.35), 1.0)
	# The gates: the next slots' tags, hung from the roll's foot on strings to the column at the right.
	var rules: Array = ContentDB.config("account_rules").get("slots", []).filter(func(rl): return int(rl.slot) > _slots()).slice(0, TAGS)
	var string := UiKit.SURFACE.hemp.lerp(UiKit.BRONZE, 0.5)
	for i in rules.size():
		var at := Vector2(WALL.end.x - 40 - TAG.x + 14 + i * 10, BELOW.position.y + i * (TAG.y + 8.0) + 7)
		draw_line(Vector2(r.get_center().x, r.end.y - 4), at, string, 1.5, true)
	var y := BELOW.position.y
	var shown := 0
	for rule in rules:
		var slot := int(rule.slot)
		var tr := Rect2(WALL.end.x - 40 - TAG.x, y, TAG.x, TAG.y)
		rounded(tr.grow(1), 4.0, UiKit.SURFACE.talisman_edge)
		rounded(tr, 3.0, UiKit.SURFACE.talisman)
		ground(tr, UiKit.SURFACE.talisman)
		draw_circle(tr.position + Vector2(14 + shown * 10, 7), 2.5, UiKit.SURFACE.peg_dark, true, -1.0, true)
		var why := RequirementRules.first_failure_text(rule.get("requires", {}), {"char": null, "account": Game.account, "room": {}})
		if why == "": why = Tx.t("shell.locked")
		text(tr.position + Vector2(40, 24), Tx.t("ui.characters.slot") % slot, 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, tr.size.x - 50)
		text(tr.position + Vector2(10, 42), why, 14, UiKit.BLOOD, HORIZONTAL_ALIGNMENT_LEFT, tr.size.x - 20)
		y += TAG.y + 8.0
		shown += 1
	if closed > shown and shown > 0:
		text(Vector2(WALL.end.x - 40 - TAG.x, y + 16), Tx.plural("ui.characters.more_slots", closed - shown) % (closed - shown), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, TAG.x)

# ------------------------------------------------------------------ under the scroll
## The chosen disciple: the one you play sets the task it keeps when you switch away; another offers Switch.
func _below(ch) -> void:
	var other = Game.character("c%d" % chosen)
	var r := BELOW
	if other == null:
		text(r.position + Vector2(0, 30), Tx.t("ui.characters.new_disciple"), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x, true)
		para(Rect2(r.position + Vector2(0, 44), Vector2(r.size.x, 60)), Tx.t("ui.characters.slot_empty_create_from_the") % chosen, 18, UiKit.MIST, 2)
		return
	if other != ch:
		text(r.position + Vector2(0, 30), str(other.name), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x, true)
		text(r.position + Vector2(0, 60), "%s · %s" % [ContentDB.realm_label(other.cultivator.realm_key, ProgressionRules.level(other)), task_line(other)], 18, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x)
		para(Rect2(r.position + Vector2(0, 74), Vector2(r.size.x - 260, 60)), Tx.t("ui.characters.switch_hint"), 16, UiKit.PAPER, 2)
		btn(Rect2(r.end.x - 240, r.position.y + 70, 240, BTN_H_MAIN), Tx.t("ui.characters.switch"), "switch", chosen, true)
		return
	heading(r.position + Vector2(0, 26), Tx.t("ui.characters.when_you_switch_away"), r.size.x)
	para(Rect2(r.position + Vector2(0, 40), Vector2(r.size.x, 50)), Tx.t("ui.characters.the_character_you_leave_keeps"), 16, UiKit.MIST, 2)
	var cur := str(ch.idle_task.get("task", ""))
	var w := (r.size.x - GAP * (TASKS.size() - 1)) / TASKS.size()
	for i in TASKS.size():
		var tk: Array = TASKS[i]
		var def := ContentDB.entry("idle_tasks", tk[0])
		var ok := not def.has("requires") or RequirementRules.passes(def.requires, Game.ctx(ch))
		var why := RequirementRules.first_failure_text(def.get("requires", {}), Game.ctx(ch))
		# S49: idle Hunt and Gather only where the room allows them.
		if ok and not Game.world.idle_allowed(str(ch.position.get("room", "")), str(tk[0])):
			ok = false
			why = Tx.t("sim.account.idle_room_" + str(tk[0]))
		btn(Rect2(r.position.x + i * (w + GAP), r.position.y + 104, w, BTN_H_STANDARD), tk[1], "task", tk[0], cur == tk[0], ok, why, 20, str(TASK_ICON[tk[0]]))

## What a character not being played does: its post, else its idle task. B20: Keeping Post (S50) moved hunting and
## gathering idlers to posts and clears idle_task, so a character at its post read "Idle: none".
func task_line(other) -> String:
	var post := post_line(other)
	if post != "": return post
	var task := str(other.idle_task.get("task", ""))
	for tk in TASKS:
		if tk[0] == task: return tk[1]
	return task.capitalize() if task != "" else Tx.t("ui.characters.idle_none")

## "Post: Delving at Willow Path West", "Vigil at Reed Marsh", or "" for a character keeping no post.
static func post_line(other) -> String:
	var post: Dictionary = Game.posts.post_of(other)
	if post.is_empty(): return ""
	var room := ContentDB.name_of("rooms", str(post.get("room", "")))
	if str(post.get("kind", "")) == "vigil": return Tx.t("ui.characters.vigil_at") % room
	return Tx.t("ui.characters.post_at") % [str(ContentDB.entry("posts", str(post.get("craft", ""))).get("short", "")), room]

func on_action(id: String, data) -> void:
	match id:
		"choose": chosen = int(data)
		"scroll": page_at = clampi(page_at + int(data), 0, maxi(0, _slots() - SHOWN))
		"switch": navigate.emit("_switch", {"slot": int(data)})
		"task":
			if submit({"type": "set_idle_task", "task": {"task": str(data)}}).get("ok", false): flash(Tx.t("ui.characters.idle_task_set"))
