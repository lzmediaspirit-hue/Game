class_name TechniquePicture
extends RefCounted
## Decision 42 ("I want the skills icon to look like the attached image", docs/redesign/feedback/skill_icon_reference.png):
## an art's picture, one look wherever it shows (the Techniques tree's cards and its reading, the HUD's technique
## buttons, the Techniques page's loadout bar). A square of deep starry ground in the art's element's ink; the character
## large in the art's pose, drawn in that one ink (the top-down figure, TopdownFigure, at a whole scale; the side view's
## Avatar only for a classic side-view character); a few marks of the art's form round it in the same ink (a palm's
## crescents, a ward's dome, a domain's ring, a pillar's springs, a seal's square); the frame; and a small rank badge
## (the art's mastery tier) when the character knows it. A card shows the figure from the head to about the ankles, the
## reading whole on its floor. A button's size (under 60 px: the HUD's, the loadout bar's) has its own pass, so it reads
## at a glance: the head and shoulders facing the camera (the face always shows), lifted well clear of a calm dark
## ground with no stars and no rim, and one bold mark of the form beside the face. docs/ui_style_guide.md §8.4,
## "Technique pictures".
##
## No frame waits on a picture. Each is a cell of an atlas sheet (a SubViewport, SHEET px square, a grid of cells of one
## size) that the GPU draws: the ground, its stars and the form's marks are painted as lightness at the figure's art
## pixel on a worker thread (_paint_images); the main thread only makes their two small textures and the cell's canvas
## item, a few a frame within BUDGET_US, and the cell draws them and the figure's layers through the ink shader
## (technique_picture_ink.gdshader: a pixel's lightness picks a colour on the element's ramp). A caller draws its cell's
## region of the sheet over the element's plain ground, which shows until the cell is painted, so a caller that keeps
## its drawing (the Techniques tree's tiles) need not draw again for it. Cells are kept by their look (the art, the
## outfit, the pose, the size); when every sheet is full, the least used one starts again and `generation` moves on, so
## a caller that keeps its drawing draws again.
##
## States read over any picture: the cooldown's ink sweep with its seconds; short of Qi, the picture dimmed and a Qi
## strip along its foot filled as far as the pool reaches the cost; closed (the weapon in hand cannot use it), a slate
## frame, the picture dim and a lock in the corner. A locked art on the tree is `muted`: its picture in a grey ink.

const Avatar = preload("res://scripts/avatar.gd")
const INK_SHADER = preload("res://scripts/presentation/technique_picture_ink.gdshader")
const SHEET := 512                ## an atlas sheet's side, px
const MAX_SHEETS := 10            ## sheets kept at most (a full set starts its least used one again)
const BUDGET_US := 1500           ## main-thread µs a frame for starting and finishing pictures (a start always fits one)
const STARTS_A_FRAME := 6         ## pictures begun a frame at most (each hands its painting to a worker thread)
## The forms an art cast from a sitting (its action meditate_burst, or none) is pictured seated for, as the reference
## draws them (a ward's dome, a domain's springs, a chorus's notes); the rest cast standing, the hand seal toward its foe.
const SEATED := ["ward", "domain", "chorus", "pillar", "rain", "release"]
## The forms whose marks stand before the hand: the figure stands back a little to leave them room.
const AHEAD := ["strike", "flurry", "echo", "thrust", "arc", "counter", "return", "seal", "seeker", "snare", "swarm", "volley", "wave", "lunge"]
## The side view's figure (a classic character), in art px from its feet (its sheets are drawn at x2).
const SIDE_BOX := Rect2(-12, -48, 26, 48)
## The modulates that tell the ink shader how to read what is drawn: a painted image's lightness as it is (red 0); the
## figure's layers are drawn white (their lightness pressed toward the dark); its rim with green 0 (the light).
const PAINTED := Color(0, 1, 1, 1)
const RIM_INK := Color(1, 0, 1, 1)
const RIM := [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]
## The figure's tone in the ink shader, [cut, base, gain, rim]: a pixel's lightness l becomes base + gain * l (below
## `cut`, an outline pixel, it stays l), its rim `rim`. A card presses the figure toward the dark on a mid ground; a
## button (SMALL px and under) lifts it well clear of its dark ground, so it reads at a glance.
const TONE_KEYS := ["cut", "base", "gain", "rim"]
const CARD_TONE := [0.0, -0.182, 1.3, 0.9]
const SMALL_TONE := [0.13, 0.1, 1.1, 1.0]
const SMALL := 59                 ## a picture this many px across or fewer is a button's: its upper body, its own tone
const HEAD_X := 0.42              ## where a button's head stands across it (its mark has the right side)

static var _holder: Node
static var _sheets: Array = []        # [{vp, tex, s, side, cols, slots: [key or ""], used}]
static var _cells: Dictionary = {}    # key -> {key, sheet, slot, rect, spec, state, task, node, back, front}
static var _pending: Array = []       # keys still being painted or waiting on the figure's sheets
static var _figs: Dictionary = {}     # "t|<outfit>" -> TopdownFigure; "s|<outfit>" -> Avatar (a classic character)
static var _mats: Dictionary = {}     # ramp key -> ShaderMaterial
static var _ramps: Dictionary = {}    # ramp key -> [deep, mid, light]
static var _boxes: Dictionary = {}    # radius|colour -> StyleBoxFlat
static var _looks: Dictionary = {}    # outfit hash|family -> [family, the outfit the art is pictured in] (art_look)
static var _frame := -1               # the frame the budget below is for
static var _spent_us := 0
static var _started := 0
## Moves on when a sheet starts again: a caller that keeps its drawing (the Techniques tree's tiles) draws again.
static var generation := 0
## Tests (perf): the most main-thread µs one picture's start, finish or paint took, and one frame's pictures in all.
static var build_us_max := 0
static var build_worst := ""           ## which piece took build_us_max
static var frame_us_max := 0
## Tests: each picture drawn, [{id, rect, where, figure, top, facing, frame, k, size, scale, rank, muted}] (null: off).
static var draw_log = null

# ------------------------------------------------------------------ drawing a picture
## Technique `tid`'s picture filling `r`, its frame included. `who` is the character (the pose its weapon family casts
## the art in, whether it plays the top-down game, its rank in the art), `outfit` its look; `frame` the frame's colour,
## `k` the picture's brightness (a closed or short art is dimmed), `a` the opacity (a page turn's fade); `muted` a grey
## ink (a locked art on the tree); `rank` the badge's number (-1: the art's mastery tier when `who` knows it, 0: none).
## `where` names the caller in the draw log. True once its cell is in a sheet (drawn as it is painted, with no draw
## again); false while it waits its turn (the plain ground stands in: draw again later).
static func draw(ci: CanvasItem, r: Rect2, tid: String, who, outfit: Dictionary, frame := UiKit.BRIGHT_JADE, k := 1.0, a := 1.0, where := "", muted := false, rank := -1) -> bool:
	r = Rect2(r.position.round(), r.size.round())
	var t := ContentDB.entry("techniques", tid)
	rounded(ci, r, 5.0, Color(UiKit.INK, a))
	rounded(ci, r.grow(-1.0), 4.0, Color(frame, a))
	var p := r.grow(-3.0)
	rounded(ci, p, 3.0, Color(UiKit.INK, a))
	if t.is_empty():   # an art no longer in the book: the empty frame
		if draw_log != null: draw_log.append({"id": tid, "rect": r, "where": where, "figure": false, "top": false, "frame": frame, "k": k})
		return true
	var s := int(minf(p.size.x, p.size.y))
	var sq := Rect2((p.position + (p.size - Vector2(s, s)) * 0.5).round(), Vector2(s, s))
	var ramp := _ramp(str(t.get("element", "none")), muted)
	var dim := Color(k, k, k, a)
	# The element's plain ground, under the cell until it is painted.
	var top_c: Color = ramp[0].lerp(ramp[1], 0.7) * dim
	var foot_c: Color = ramp[0].lerp(ramp[1], 0.4) * dim
	ci.draw_polygon(PackedVector2Array([sq.position, Vector2(sq.end.x, sq.position.y), sq.end, Vector2(sq.position.x, sq.end.y)]), PackedColorArray([top_c, top_c, foot_c, foot_c]))
	var look := _look(tid, t, who, outfit, s, muted)
	var cell := _cell_for(tid, t, look, s, muted)
	if not cell.is_empty():
		cell.sheet.used = Engine.get_process_frames()
		ci.draw_texture_rect_region(cell.sheet.tex, sq, cell.rect, dim)
	if rank < 0: rank = _rank(who, tid)
	if rank > 0: _badge(ci, sq, rank, a)
	if draw_log != null:
		draw_log.append({"id": tid, "rect": r, "where": where, "figure": not cell.is_empty() and str(cell.state) == "ready",
			"top": bool(look[1]), "facing": str(look[2][1]), "frame": frame, "k": k, "size": s,
			"scale": int(cell.spec.k) if not cell.is_empty() else 0, "rank": rank, "muted": muted})
	return not cell.is_empty()

## True once `tid`'s picture for `who` wearing `outfit`, `size` px across inside its frame, is painted, figure and all.
static func painted(tid: String, who, outfit: Dictionary, size: int, muted := false) -> bool:
	var t := ContentDB.entry("techniques", tid)
	return not t.is_empty() and str(_cells.get(_look(tid, t, who, outfit, size, muted)[0], {}).get("state", "")) == "ready"

## The top-down pose an art is pictured in, [action, facing, frame]: the pose a fight casts it in with the family it is
## pictured with (TechniquePreview.top_pose: a jian art's cut, the bow's draw, the flute at the lips, the free hand's
## palm, the hand seal), but seated for an art cast from a sitting whose form rests round the body (SEATED). Facing so
## the move reads: a weapon's blow held on the frame it lands in profile toward the right (E: the blade, the draw); the
## bare hand's three-quarters toward the camera and the right just after it lands (SE: the face over the hand still
## out, where at the landing the head turns away); the hand seal on its frame toward the camera (S: the face over the
## joined hands); a stance or a sitting on its first frame, three-quarters (SE; a sitting faces the camera). At a
## button's size (`small`) every pose faces the camera (S) on the frame before its blow lands, the hands and the blade
## gathered under the face (at the landing a punch turns the head, and a plunge's leap bows it: it keeps its first
## frame), so the face always shows and the back of the head never fills the button.
static func top_pose(t: Dictionary, who, fam := {}, small := false) -> Array:
	var raw = t.get("action")
	var act := ""
	if (raw == null or str(raw) in ["", "null", "meditate_burst", "meditate"]) and str(t.get("vfx", {}).get("anim", "")) in SEATED:
		act = "meditate"
	else:
		act = TechniquePreview.top_pose(t, who, fam)
	if small: return [act, "s", 0 if act in ["idle", "meditate", "kneel", "salute", "plunge"] else maxi(1, TopdownFigure.hit_frame(act)) - 1]
	if act in ["idle", "meditate", "kneel", "salute"]: return [act, "se", 0]
	var hit := maxi(1, TopdownFigure.hit_frame(act))
	if act == "cast": return [act, "s", hit]
	if str(fam.get("id", "fists")) in ["fists", "gauntlets"]:   # the bare hand: the face over the follow-through
		return [act, "se", mini(hit + 1, int(TopdownFigure.spec(act).frames) - 1)]
	return [act, "e", hit]

## The weapon family an art is pictured with and the look the figure wears for it, [family, outfit]: the art's own
## family (the free hand's for an art of any hand), holding the character's weapon when it is of that family, else the
## family's own look (none for the free hand: a palm is a palm, whatever is in the other hand).
static func art_look(t: Dictionary, outfit: Dictionary) -> Array:
	var fid := str(t.get("family", "any"))
	if fid == "any" or not ContentDB.has_entry("weapon_families", fid): fid = "fists"
	var key := "%d|%s" % [hash(outfit), fid]
	if not _looks.has(key):
		var fam := ContentDB.entry("weapon_families", fid)
		var o := outfit
		if CombatFeel.family_of_look(str(outfit.get("weapon", "none"))) != fid:
			o = outfit.duplicate()
			var app: Array = fam.get("appearance", [])
			o.weapon = str(app[0]) if not app.is_empty() else "none"
		if _looks.size() >= 64: _looks.clear()
		_looks[key] = [fam, o]
	return _looks[key]

## The rank shown on `tid`'s badge: its mastery tier when `who` knows it, else none.
static func _rank(who, tid: String) -> int:
	if who == null or not who.cultivator.techniques_known.has(tid): return 0
	return int(who.cultivator.mastery.get(tid, {}).get("tier", 1))

## The rank badge: a small ink diamond ringed in pale gold with the rank in it, in the lower right corner of a card (the
## reference), the upper right of a button (its lower right holds the lock and the Qi strip).
static func _badge(ci: CanvasItem, p: Rect2, rank: int, a: float) -> void:
	var big := p.size.x >= 60.0
	var h := 9.0 if big else 6.0
	var c := (Vector2(p.end.x, p.end.y) if big else Vector2(p.end.x, p.position.y + h * 1.1)) - Vector2(h * 0.6, h * 0.6 if big else 0.0)
	var pts := PackedVector2Array([c + Vector2(0, -h - 1), c + Vector2(h + 1, 0), c + Vector2(0, h + 1), c + Vector2(-h - 1, 0)])
	ci.draw_colored_polygon(pts, Color(UiKit.INK, a))
	pts = PackedVector2Array([c + Vector2(0, -h), c + Vector2(h, 0), c + Vector2(0, h), c + Vector2(-h, 0), c + Vector2(0, -h)])
	ci.draw_colored_polygon(pts.slice(0, 4), Color(UiKit.JADE_SHADOW, a))
	ci.draw_polyline(pts, Color(UiKit.BRIGHT_JADE, a), 1.5, true)
	var fs := 13 if big else 11
	UiKit.draw_text(ci, str(rank), Vector2(c.x - 10.0, c.y + fs * 0.36), fs, Color(UiKit.PALE_GOLD, a), HORIZONTAL_ALIGNMENT_CENTER, 20.0, false)

# ------------------------------------------------------------------ the cells
## What a picture is kept by, [key, top, pose]: the art, the look, which figure draws it (top-down or the side view's),
## its pose [action, facing, frame], the size and the ink.
## For a top-down character the figure wears the art's look (art_look); a classic side-view character keeps its own, in
## the pose its side view casts the art in. [key, top, pose, outfit].
static func _look(tid: String, t: Dictionary, who, outfit: Dictionary, s: int, muted: bool) -> Array:
	var top := TopdownDoll.shown(who)
	var pose: Array = [TechniquePreview.pose_of(t, who, outfit), "e", 0]
	var o := outfit
	if top:
		var al := art_look(t, outfit)
		o = al[1]
		pose = top_pose(t, who, al[0], s <= SMALL)
	return ["%s|%d|%s|%s,%s,%d|%d|%d" % [tid, hash(o), "t" if top else "s", pose[0], pose[1], pose[2], s, int(muted)], top, pose, o]

## `tid`'s cell for this look and size: kept, or begun now when the frame's budget allows ({} when it must wait).
static func _cell_for(tid: String, t: Dictionary, look: Array, s: int, muted: bool) -> Dictionary:
	var key: String = look[0]
	var top: bool = look[1]
	var pose: Array = look[2]
	var worn: Dictionary = look[3]
	var cell: Dictionary = _cells.get(key, {})
	if not cell.is_empty(): return cell
	_budget_frame()
	if _started >= STARTS_A_FRAME or (_started > 0 and _spent_us >= BUDGET_US): return {}
	var t0 := Time.get_ticks_usec()
	var at := _slot(s)
	if at.is_empty(): return {}
	var sheet: Dictionary = at[0]
	var slot: int = at[1]
	var fig = _figure(worn, top)
	var kb := _scale_for(s)
	var K: int = kb[0]
	var w := ceili(float(s) / K)
	var box: Rect2 = fig.bounds(str(pose[0]), str(pose[1]), int(pose[2])) if top else SIDE_BOX
	if box.size.x <= 0.0: box = SIDE_BOX
	var form := str(t.get("vfx", {}).get("anim", ""))
	var bare: Rect2 = fig.bounds(str(pose[0]), str(pose[1]), int(pose[2]), "body") if top and bool(kb[1]) else Rect2()
	var feet := _place(box, w, bool(kb[1]), form, bare)
	var spec := {"w": w, "k": K, "s": s, "bust": kb[1], "feet": feet, "body": Rect2(Vector2(feet) + box.position, box.size), "form": form,
		"seated": str(pose[0]) == "meditate", "seed": hash(tid), "top": top, "action": str(pose[0]), "row": str(pose[1]), "at": int(pose[2]),
		"fig": _fig_key(worn, top), "mat": _material(str(t.get("element", "none")), muted, s <= SMALL), "bare": Rect2(Vector2(feet) + bare.position, bare.size)}
	var cols: int = sheet.cols
	cell = {"key": key, "sheet": sheet, "slot": slot, "rect": Rect2(Vector2(slot % cols, slot / cols) * s, Vector2(s, s)), "spec": spec, "state": "painting",
		"out": {}}
	cell.task = WorkerThreadPool.add_task(_paint_images.bind(spec, cell.out), false, "technique picture")
	sheet.slots[slot] = key
	_cells[key] = cell
	_pending.append(key)
	_host().set_process(true)
	_started += 1
	_spend(t0, "start " + key)
	return cell

## [scale, bust] for a picture `s` px across: the whole scale that fills it with the figure, and whether it is framed
## from the head down (a button's size shows the upper body).
static func _scale_for(s: int) -> Array:
	if s >= 120: return [3, false]
	if s >= 60: return [2, false]
	return [2, true]

## Where the figure's feet stand in a cell `w` art px across (its box `box` from the feet): its middle a little left of
## the cell's when its form's marks stand before the hand, never its left edge (the body's side of a blow) cut; its feet
## on the ground line when it fits, else its head just under the top and its feet cut. A button's upper body (`bust`,
## `bare` the bare body's box from the feet) puts the crown of the head under the top (a topknot or a hat may be cut)
## and the head a little left of the middle (HEAD_X), so the shoulders and the hands' work show under the face and the
## form's mark has the right side.
static func _place(box: Rect2, w: int, bust: bool, form: String, bare := Rect2()) -> Vector2i:
	if bust and bare.has_area():
		return Vector2i(int(roundf(w * HEAD_X - bare.get_center().x)), int(2.0 - bare.position.y))
	var fx := roundf(w * 0.5 - box.get_center().x - (roundf(w * 0.06) if form in AHEAD else 0.0))
	fx = maxf(fx, 1.0 - box.position.x) if box.size.x > w - 2.0 else clampf(fx, 1.0 - box.position.x, w - 1.0 - box.end.x)
	var fy := 2.0 - box.position.y
	if not bust and box.size.y + 4.0 <= w: fy = w - 2.0 - box.end.y
	return Vector2i(int(fx), int(fy))

## A free cell for pictures `s` px across: a sheet of that size with room, a new sheet, or the least used sheet (not one
## drawn this frame) started again ([] when none may be).
static func _slot(s: int) -> Array:
	for sh in _sheets:
		if int(sh.s) == s:
			var i: int = (sh.slots as Array).find("")
			if i >= 0: return [sh, i]
	if _sheets.size() < MAX_SHEETS:
		var sh := _new_sheet(s)
		_sheets.append(sh)
		return [sh, 0]
	var now := Engine.get_process_frames()
	var old = null
	for sh in _sheets:
		if int(sh.used) < now and (old == null or int(sh.used) < int(old.used)): old = sh
	if old == null: return []
	_restart_sheet(old, s)
	return [old, 0]

static func _new_sheet(s: int) -> Dictionary:
	var side := maxi(SHEET, s)
	var vp := SubViewport.new()
	vp.size = Vector2i(side, side)
	vp.transparent_bg = true
	vp.disable_3d = true
	vp.gui_disable_input = true
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	vp.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	_host().add_child(vp)
	var cols := side / s
	var slots: Array = []
	slots.resize(cols * cols)
	slots.fill("")
	return {"vp": vp, "tex": vp.get_texture(), "s": s, "side": side, "cols": cols, "slots": slots, "used": Engine.get_process_frames()}

## A sheet given up for pictures `s` px across: its cells forgotten (their canvas items gone), `generation` moved on.
static func _restart_sheet(sh: Dictionary, s: int) -> void:
	for key in sh.slots:
		if str(key) == "": continue
		var cell: Dictionary = _cells.get(key, {})
		if cell.is_empty(): continue
		if str(cell.state) == "painting": WorkerThreadPool.wait_for_task_completion(int(cell.task))
		if is_instance_valid(cell.get("node")): cell.node.queue_free()
		_cells.erase(key)
		_pending.erase(key)
	var cols := int(sh.side) / s
	var slots: Array = []
	slots.resize(cols * cols)
	slots.fill("")
	sh.s = s
	sh.cols = cols
	sh.slots = slots
	sh.vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	generation += 1

## The frame's budget, started again on a new frame.
static func _budget_frame() -> void:
	var f := Engine.get_process_frames()
	if f == _frame: return
	_frame = f
	_spent_us = 0
	_started = 0

static func _spend(t0: int, what := "") -> void:
	_budget_frame()
	var us := Time.get_ticks_usec() - t0
	_spent_us += us
	if us > build_us_max: build_worst = what
	build_us_max = maxi(build_us_max, us)
	frame_us_max = maxi(frame_us_max, _spent_us)

## The node that holds the sheets and finishes the cells (made once, under the tree's root; it runs while anything is
## pending, paused or not).
static func _host() -> Node:
	if not is_instance_valid(_holder):
		_holder = Host.new()
		_holder.name = "TechniquePictures"
		_holder.process_mode = Node.PROCESS_MODE_ALWAYS
		(Engine.get_main_loop() as SceneTree).root.add_child(_holder)
		_sheets.clear()
		_cells.clear()
		_pending.clear()
		_figs.clear()
	return _holder

class Host extends Node:
	func _process(_delta: float) -> void:
		TechniquePicture._tend()
	## Back from the background (a phone's GL context may have been let go): every sheet is drawn again.
	func _notification(what: int) -> void:
		if what in [NOTIFICATION_APPLICATION_RESUMED, NOTIFICATION_APPLICATION_FOCUS_IN]:
			for sh in TechniquePicture._sheets: sh.vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	## Leaving the tree (the game quits): the workers waited for and every kept picture, figure and ink let go, before
	## the rendering server closes.
	func _exit_tree() -> void:
		TechniquePicture._release()

static func _release() -> void:
	for key in _pending:
		var cell: Dictionary = _cells.get(key, {})
		if str(cell.get("state", "")) == "painting": WorkerThreadPool.wait_for_task_completion(int(cell.task))
	_pending.clear()
	_cells.clear()
	_sheets.clear()
	_figs.clear()
	_mats.clear()
	_looks.clear()

## A cell's canvas item in its sheet: it draws its painted ground, the figure and the marks through the ink.
class Cell extends Node2D:
	var cell: Dictionary
	func _draw() -> void:
		TechniquePicture._draw_cell(self, cell)

## Each frame while anything is pending: a painted cell (its worker done) gets its textures and its canvas item, within
## the frame's budget; a cell whose figure's sheets are in draws again with it. A sheet that changed is drawn again.
static func _tend() -> void:
	_budget_frame()
	var dirty := {}
	for key in _pending.duplicate():
		var cell: Dictionary = _cells.get(key, {})
		if cell.is_empty():
			_pending.erase(key)
			continue
		if str(cell.state) == "painting":
			if _spent_us >= BUDGET_US or not WorkerThreadPool.is_task_completed(int(cell.task)): continue
			var t0 := Time.get_ticks_usec()
			WorkerThreadPool.wait_for_task_completion(int(cell.task))
			var sp: Dictionary = cell.spec
			cell.back = ImageTexture.create_from_image(cell.out.back)
			cell.front = ImageTexture.create_from_image(cell.out.front)
			cell.out = {}
			var node := Cell.new()
			node.cell = cell
			node.position = cell.rect.position
			node.material = sp.mat
			cell.sheet.vp.add_child(node)
			RenderingServer.canvas_item_set_custom_rect(node.get_canvas_item(), true, Rect2(Vector2.ZERO, cell.rect.size))
			RenderingServer.canvas_item_set_clip(node.get_canvas_item(), true)
			cell.node = node
			cell.state = "figure"
			dirty[cell.sheet.vp] = true
			_spend(t0, "finish " + str(key))
		if str(cell.state) == "figure" and _figure_in(cell.spec):
			cell.node.queue_redraw()
			cell.state = "ready"
			dirty[cell.sheet.vp] = true
			_pending.erase(key)
	for vp in dirty: vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	if _pending.is_empty(): _holder.set_process(false)

## A cell's drawing (in its sheet, from its top left): the painted ground and back marks, the figure at its scale (its
## sheets once they are in) over its light rim (its silhouette an art pixel out each way), the front marks; all through
## the ink.
static func _draw_cell(node: Node2D, cell: Dictionary) -> void:
	var t0 := Time.get_ticks_usec()
	var sp: Dictionary = cell.spec
	var s := float(sp.s)
	var K := float(sp.k)
	var src := Rect2(0, 0, s / K, s / K)
	var dst := Rect2(0, 0, s, s)
	node.draw_texture_rect_region(cell.back, dst, src, PAINTED)
	if _figure_in(sp):
		var feet := Vector2(sp.feet) * K
		var f = _figs[sp.fig]
		if not bool(sp.top):
			f.play(str(sp.action))
			f.elapsed = 0.3
			f.facing = 1
		for d in ([Vector2.ZERO] if bool(sp.bust) else RIM + [Vector2.ZERO]):   # a button's figure has no rim: its own dark outline on the dark ground
			var tint := RIM_INK if d != Vector2.ZERO else Color.WHITE
			if bool(sp.top): (f as TopdownFigure).draw(node, feet + d * K, str(sp.action), str(sp.row), int(sp.at), tint, K, dst)
			else: f.draw_on(node, feet + d * K, K * 0.5, tint)
	node.draw_texture_rect_region(cell.front, dst, src, PAINTED)
	_spend(t0, "paint " + str(cell.key))

# ------------------------------------------------------------------ the figure and the ink
static func _fig_key(outfit: Dictionary, top: bool) -> String:
	return ("t|" if top else "s|") + str(hash(outfit))

## The figure a look is drawn with: a TopdownFigure (its sheets loading on threads) for a top-down character, the side
## view's Avatar (lazy too, kept under the host) for a classic one. Kept by the look.
static func _figure(outfit: Dictionary, top: bool):
	var fk := _fig_key(outfit, top)
	if not _figs.has(fk):
		if top:
			_figs[fk] = TopdownFigure.wearing(outfit, true)
		else:
			var av = Avatar.new()
			av.outfit = outfit.duplicate()
			av.lazy_sheets = true
			av.externally_timed = true
			av.visible = false
			av.process_mode = Node.PROCESS_MODE_DISABLED
			_host().add_child(av)
			_figs[fk] = av
	return _figs[fk]

static func _figure_in(sp: Dictionary) -> bool:
	var f = _figs.get(sp.fig)
	if f == null: return false
	if bool(sp.top): return (f as TopdownFigure).loaded()
	f.play(str(sp.action))
	f.refresh_entries()
	return not (f.entries as Array).is_empty()

## An element's ramp [deep, mid, light] (a pixel's lightness 0, 0.4 and 1): its colour darkened for the ground, lightened
## for the figure's light; grey for a muted (locked) picture.
static func _ramp(el: String, muted: bool) -> Array:
	var key := el + ("|muted" if muted else "")
	if not _ramps.has(key):
		var ec := SpriteCache.element_color(el)
		var r: Array = [ec.darkened(0.9), ec.darkened(0.55), ec.lightened(0.55)]
		if muted: r = [Color("080a0b"), Color("2e3437"), Color("a3abae")]
		_ramps[key] = r
	return _ramps[key]

## The ink's material for an element (`muted`: the grey ramp) and a picture's tone: a card's (`small` false) presses the
## figure toward the dark on the mid ground; a button's (`small`, under 60 px) lifts it a long way over its dark ground,
## the figure's outline pixels kept dark and its rim at the light's end, so it reads at a glance at a thumb's size.
static func _material(el: String, muted: bool, small := false) -> ShaderMaterial:
	var key := el + ("|muted" if muted else "") + ("|small" if small else "")
	if not _mats.has(key):
		var r := _ramp(el, muted)
		var m := ShaderMaterial.new()
		m.shader = INK_SHADER
		m.set_shader_parameter("deep", r[0])
		m.set_shader_parameter("mid", r[1])
		m.set_shader_parameter("light", r[2])
		var tone: Array = SMALL_TONE if small else CARD_TONE
		for i in TONE_KEYS.size(): m.set_shader_parameter(TONE_KEYS[i], tone[i])
		_mats[key] = m
	return _mats[key]

# ------------------------------------------------------------------ painting (on a worker thread)
## A cell's ground and marks, painted as lightness at the figure's art pixel (the ink's 0 deep, 0.4 mid, 1 light) into
## out.back (opaque: the mid ground lighter round the body and darker to its edges, its stars, a card's floor under the
## feet, and the marks behind the figure) and out.front (the marks before it). A mark is light with a dark outline, as
## the reference draws them. Runs on a worker thread: it reads `spec` and writes only `out` and its own images.
static func _paint_images(spec: Dictionary, out: Dictionary) -> void:
	if bool(spec.bust):
		_paint_small(spec, out)
		return
	var w: int = spec.w
	var body: Rect2 = spec.body
	var mid := Vector2(body.get_center().x, body.position.y + body.size.y * 0.45)
	var floor_y := int(body.end.y) - 1 if not bool(spec.bust) else w + 1
	var half := (w - 1) * 0.5
	var back := Image.create(w, w, false, Image.FORMAT_RGBA8)
	for y in w:
		var base := lerpf(0.34, 0.27, float(y) / maxf(1.0, w - 1.0))
		for x in w:
			var v := 0.0
			if y > floor_y: v = 0.2
			elif y == floor_y: v = 0.5
			else:
				var g := maxf(0.0, 1.0 - Vector2(x, y).distance_to(mid) / (w * 0.6))
				var e := maxf(absf(x - half), absf(y - half)) / (w * 0.5)
				v = base + 0.28 * g * g - 0.14 * maxf(0.0, e - 0.55) / 0.45
			back.set_pixel(x, y, Color(v, v, v))
	var rng := RandomNumberGenerator.new()
	rng.seed = int(spec.seed)
	for i in int(w * w / 55.0):
		var at := Vector2(rng.randi_range(0, w - 1), rng.randi_range(0, maxi(0, mini(w, floor_y - 2) - 1)))
		_dot(back, at, rng.randf_range(0.62, 0.95))
	for i in (1 if w < 30 else 2):
		_sparkle(back, Vector2(rng.randi_range(2, w - 3), rng.randi_range(2, int(w * 0.45))), 1.0)
	if floor_y < w - 2:   # a few strokes on the floor, as the reference's stage
		for i in 3:
			var y := rng.randi_range(floor_y + 2, w - 1)
			var x := rng.randi_range(1, w - 6)
			_line(back, Vector2(x, y), Vector2(x + rng.randi_range(2, 4), y), 0.34)
	var marks := Image.create(w, w, false, Image.FORMAT_RGBA8)
	var front := Image.create(w, w, false, Image.FORMAT_RGBA8)
	_marks(marks, front, spec, rng)
	_outline(marks)
	_outline(front)
	back.blend_rect(marks, Rect2i(0, 0, w, w), Vector2i.ZERO)
	out.back = back
	out.front = front

## A button's picture (the readability pass): a calm, dark ground, a smooth fall from its top to its foot with a soft
## light behind the head and no stars, so the lifted figure stands clear of it; and one bold, simple mark of the form
## on the right side (_marks_small), light in a dark outline, clear of the face and of the rank badge's corner.
static func _paint_small(spec: Dictionary, out: Dictionary) -> void:
	var w: int = spec.w
	var bare: Rect2 = spec.bare
	var head := Vector2(bare.get_center().x, bare.position.y + 7.0)
	var back := Image.create(w, w, false, Image.FORMAT_RGBA8)
	for y in w:
		var base := lerpf(0.17, 0.09, float(y) / maxf(1.0, w - 1.0))
		for x in w:
			var g := maxf(0.0, 1.0 - Vector2(x, y).distance_to(head) / (w * 0.6))
			var v := base + 0.06 * g * g
			back.set_pixel(x, y, Color(v, v, v))
	var front := Image.create(w, w, false, Image.FORMAT_RGBA8)
	_marks_small(front, spec)
	_outline(front)
	out.back = back
	out.front = front

## A button's mark of the form, bold and simple, centred on `m` (the right side, level with the face) and `r` across:
## a palm's crescents, a flurry's three, an echo's rings, a counter's shield, a thrust's arrow, a lunge's chevrons, a
## volley's darts, a seeker's orb, an arc's bolt, a blink's star, a swarm's motes, a return's circling arrow, a ward's
## dome over the head, a domain's ring and a pillar's springs at the foot, a rain's drops, a release's rays, a burst's
## star, a seal's square, a snare's loop, a chorus's note, a wave's ripples, a sweep's arc, a plunge's falling arrow.
static func _marks_small(img: Image, spec: Dictionary) -> void:
	var w := float(spec.w)
	var bare: Rect2 = spec.bare
	var m := Vector2(roundf(w - w * 0.2), roundf(w * 0.46))
	var r := maxf(3.0, roundf(w * 0.17))
	match str(spec.form):
		"flurry":
			for j in [-1, 0, 1]: _crescent(img, m + Vector2(-r + absf(j) * 2.0 - 1.0, j * (r + 1.0)), r * 0.7 + 1.0, 1.0)
		"echo":
			for i in 3: _arc(img, m - Vector2(r + 1.0, 0), 1.0 + i * (r * 0.6 + 0.5), 1.0 + i * (r * 0.6 + 0.5), -1.1, 1.1, 1.0)
		"counter":
			_arc(img, m + Vector2(r, 0), r + 1.0, r + 1.0, PI - 1.2, PI + 1.2, 1.0)
			_arc(img, m + Vector2(r + 1.0, 0), r + 1.0, r + 1.0, PI - 0.7, PI + 0.7, 1.0)
		"thrust":
			_line(img, m - Vector2(r + 1.0, 0), m + Vector2(r, 0), 1.0)
			_line(img, m + Vector2(r - 2.0, -2), m + Vector2(r, 0), 1.0)
			_line(img, m + Vector2(r - 2.0, 2), m + Vector2(r, 0), 1.0)
		"lunge":
			for i in 2:
				var c := m + Vector2(-2.0 + i * 3.0, 0)
				_line(img, c + Vector2(-1, -r + 1.0), c + Vector2(r * 0.6, 0), 1.0)
				_line(img, c + Vector2(r * 0.6, 0), c + Vector2(-1, r - 1.0), 1.0)
		"volley":
			for j in [-1, 0, 1]:
				var y: float = m.y + float(j) * (r * 0.7 + 1.0)
				_line(img, Vector2(m.x - r + 1.0, y), Vector2(m.x + r - 1.0, y), 1.0)
				_dot(img, Vector2(m.x + r - 2.0, y - 1.0), 1.0)
				_dot(img, Vector2(m.x + r - 2.0, y + 1.0), 1.0)
		"seeker":
			for d in [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1), Vector2(1, 1), Vector2(-1, 0), Vector2(0, -1), Vector2(2, 0), Vector2(0, 2)]:
				_dot(img, m + Vector2(1, -1) + d, 1.0)
			_arc(img, m + Vector2(-r * 0.5, r * 0.5), r * 0.8, r * 0.8, PI * 0.5, PI * 1.1, 1.0)
		"arc":
			var pts := [m + Vector2(1, -r - 1.0), m + Vector2(-2, -1), m + Vector2(2, 0), m + Vector2(-1, r + 1.0)]
			for i in pts.size() - 1: _line(img, pts[i], pts[i + 1], 1.0)
		"blink":
			_line(img, m - Vector2(0, r + 1.0), m + Vector2(0, r + 1.0), 1.0)
			_line(img, m - Vector2(r + 1.0, 0), m + Vector2(r + 1.0, 0), 1.0)
			_sparkle(img, m, 1.0)
		"swarm":
			for d in [Vector2(-2, -3), Vector2(2, -2), Vector2(-1, 1), Vector2(3, 2), Vector2(0, 4)]: _sparkle(img, m + d, 1.0)
		"return":
			_arc(img, m, r, r, -PI * 0.1, PI * 1.45, 1.0)
			var tip := m + Vector2.from_angle(-PI * 0.1) * r
			_line(img, tip, tip + Vector2(-2, -1), 1.0)
			_line(img, tip, tip + Vector2(0, 2), 1.0)
		"ward":
			var c := Vector2(roundf(bare.get_center().x), roundf(bare.position.y + 12.0))
			_arc(img, c, bare.size.x * 0.5 + 3.0, 13.0, PI, TAU, 1.0)
		"domain":
			_arc(img, Vector2(w * 0.5, w - 3.0), w * 0.44, 2.0, 0.0, TAU, 1.0)
			_sparkle(img, Vector2(w * 0.5 + w * 0.3, w - 3.0), 1.0)
		"pillar":
			for x in [2.0, w - 3.0]:
				_line(img, Vector2(x, w - 1.0), Vector2(x, w * 0.4), 1.0)
				_line(img, Vector2(x + 1.0, w - 1.0), Vector2(x + 1.0, w * 0.4), 1.0)
				_sparkle(img, Vector2(x, w * 0.4 - 2.0), 1.0)
		"rain":
			for d in [Vector2(-2, -3), Vector2(2, -1), Vector2(-1, 2), Vector2(3, 4)]:
				_line(img, m + d, m + d + Vector2(-1, 2), 1.0)
		"release":
			for ang in [-PI * 0.5, -PI * 0.3, -PI * 0.1]:
				var d := Vector2.from_angle(ang)
				_line(img, m + Vector2(-2, 3) + d * 2.0, m + Vector2(-2, 3) + d * (r + 3.0), 1.0)
		"burst":
			for i in 8:
				var d := Vector2.from_angle(TAU * i / 8.0)
				_line(img, m + d * 1.5, m + d * (r + (1.0 if i % 2 == 0 else 0.0)), 1.0)
		"seal":
			var o := (m - Vector2(r, r)).round()
			_rect(img, Rect2(o, Vector2(r * 2.0, r * 2.0)), 1.0)
			_line(img, o + Vector2(r, 2), o + Vector2(r, r * 2.0 - 2.0), 1.0)
			_line(img, o + Vector2(2, r), o + Vector2(r * 2.0 - 2.0, r), 1.0)
		"snare":
			_arc(img, m, r, r, 0.0, TAU, 1.0)
			_line(img, m + Vector2(-r - 1.0, r), m + Vector2(-r * 0.6, r * 0.6), 1.0)
		"chorus":
			for d in [Vector2(-1, 1), Vector2(0, 1), Vector2(-1, 2), Vector2(0, 2), Vector2(1, 2), Vector2(-1, 3), Vector2(0, 3)]: _dot(img, m + d, 1.0)
			_line(img, m + Vector2(1, 2), m + Vector2(1, -r - 1.0), 1.0)
			_line(img, m + Vector2(1, -r - 1.0), m + Vector2(r * 0.8 + 1.0, -r * 0.4), 1.0)
		"wave":
			for j in 2:
				var x := m.x - r - 1.0
				while x <= m.x + r + 1.0:
					_dot(img, Vector2(x, m.y + j * 3.0 + sin(x * 1.1) * 1.2), 1.0)
					x += 1.0
		"sweep":
			_arc(img, Vector2(w * 0.5, w * 0.62), w * 0.42, w * 0.22, 0.25, PI - 0.25, 1.0)
		"plunge":
			_line(img, m - Vector2(0, r + 1.0), m + Vector2(0, r), 1.0)
			_line(img, m + Vector2(-2, r - 2.0), m + Vector2(0, r), 1.0)
			_line(img, m + Vector2(2, r - 2.0), m + Vector2(0, r), 1.0)
		_:   # a strike: the palm's two crescents
			_crescent(img, m - Vector2(r + 1.0, 0), r + 1.0, 1.0)
			_crescent(img, m - Vector2(r - 2.0, 0), r + 1.0, 1.0)

## A dark outline round every mark of `img` (a transparent layer): each empty pixel beside one drawn goes dark.
static func _outline(img: Image) -> void:
	var w := img.get_width()
	var h := img.get_height()
	var edge: Array = []
	for y in h:
		for x in w:
			if img.get_pixel(x, y).a > 0.0: continue
			for d in RIM:
				var nx := x + int(d.x)
				var ny := y + int(d.y)
				if nx >= 0 and ny >= 0 and nx < w and ny < h and img.get_pixel(nx, ny).a > 0.5:
					edge.append(Vector2i(x, y))
					break
	for p in edge: img.set_pixel(p.x, p.y, Color(0.02, 0.02, 0.02, 1.0))

## The form's marks round the figure (docs/ui_style_guide.md, "Technique pictures"): `hand` just before the body at the
## chest, `chest` the body's middle, `ground` its feet (the cell's foot for a button's upper body).
static func _marks(back: Image, front: Image, spec: Dictionary, rng: RandomNumberGenerator) -> void:
	var w := float(spec.w)
	var u := maxf(1.0, roundf(w / 12.0))
	var b: Rect2 = spec.body
	var hand := Vector2(b.end.x + 1.0, b.position.y + b.size.y * 0.3)
	if bool(spec.seated): hand = Vector2(b.end.x + 1.0, b.position.y + b.size.y * 0.45)
	var chest := Vector2(roundf(b.get_center().x), b.position.y + b.size.y * 0.4)
	var ground := minf(float(spec.feet.y), w - 2.0)
	var head := b.position.y
	match str(spec.form):
		"flurry":   # blow on blow: the palm's crescents, the second pair high and low, and a spark
			_crescent(front, hand - Vector2(u, 0), u + 1.0, 1.0)
			for j in [-1, 1]: _crescent(front, hand + Vector2(1.0, j * (u + 1.0)), u + 1.0, 0.9)
			_sparkle(front, hand + Vector2(u * 2.0 + 2.0, -u * 2.0), 1.0)
		"echo":
			for i in 3: _arc(front, hand - Vector2(u, 0), u * (i + 1) + 1.0, u * (i + 1) + 1.0, -1.25, 1.25, [1.0, 0.8, 0.6][i], 2 if i == 2 else 1)
		"thrust":
			_line(front, hand, Vector2(w - 1.0, hand.y), 1.0)
			for j in [-1, 1]: _line(front, hand + Vector2(u, j * u), Vector2(w - 1.0 - u, hand.y + j * u), 0.7)
			_line(front, Vector2(w - 1.0 - u, hand.y - u), Vector2(w - 1.0, hand.y), 1.0)
			_line(front, Vector2(w - 1.0 - u, hand.y + u), Vector2(w - 1.0, hand.y), 1.0)
		"lunge":
			for y in [chest.y - u, chest.y + u * 0.5, ground - u * 2.0]:
				_line(back, Vector2(b.position.x - 1.0, y), Vector2(maxf(0.0, b.position.x - 1.0 - u * 3.0), y), 0.8)
			for i in 2:
				var at := hand + Vector2(i * (u + 1.0), 0)
				_line(front, at + Vector2(0, -u), at + Vector2(u, 0), 1.0 - i * 0.25)
				_line(front, at + Vector2(u, 0), at + Vector2(0, u), 1.0 - i * 0.25)
		"arc":
			var pts := [hand, hand + Vector2(u, -u - 1.0), hand + Vector2(u * 2.0, u), hand + Vector2(u * 3.0, -u), hand + Vector2(u * 4.0, u * 0.5)]
			for i in pts.size() - 1: _line(front, pts[i], pts[i + 1], 1.0)
			_sparkle(front, pts[-1] + Vector2(1, 0), 1.0)
		"blink":
			for i in 2:
				var x := b.position.x - 1.0 - i * u
				var y := b.position.y + 2.0
				while y < ground:
					_dot(back, Vector2(x, y), 0.75 - i * 0.2)
					y += 2.0
			_sparkle(front, hand + Vector2(u, -u), 1.0)
		"burst":
			for i in 10:
				var d := Vector2.from_angle(TAU * i / 10.0 + 0.3)
				var r0 := maxf(b.size.x * 0.5, u * 2.0)
				_line(back, chest + d * r0, chest + d * (r0 + u * 2.0), 1.0)
				_line(back, chest + d * (r0 + u * 2.0), chest + d * (r0 + u * 3.5), 0.7)
		"chorus":
			_note(front, Vector2(b.position.x - u * 1.5, head + u * 2.5), u, 1.0)
			_note(front, Vector2(b.end.x + u, head + u * 1.5), u, 0.9)
			_arc(back, chest, b.size.x * 0.5 + u * 1.5, b.size.y * 0.35, -0.7, 0.7, 0.85)
			_arc(back, chest, b.size.x * 0.5 + u * 1.5, b.size.y * 0.35, PI - 0.7, PI + 0.7, 0.85)
		"counter":
			_arc(front, hand - Vector2(u, 0), u * 2.5, u * 2.5, -1.2, 1.2, 1.0, 2)
			_sparkle(front, hand + Vector2(u * 2.0, -u * 2.0), 1.0)
		"domain":
			var rx := w * 0.44
			var ry := maxf(2.0, roundf(w * 0.11))
			var c := Vector2(chest.x, ground - ry * 0.5)
			_arc(back, c, rx, ry, PI, TAU, 0.8)
			_arc(front, c, rx, ry, 0.0, PI, 1.0)
			for ang in [0.35, 1.3, 2.3, 4.0, 5.4]: _sparkle(back if ang > PI else front, c + Vector2(cos(ang) * rx, sin(ang) * ry), 1.0)
		"pillar":
			var xs := [b.position.x - u * 3.0, b.position.x - u * 1.2, b.end.x + u * 1.2, b.end.x + u * 3.0]
			for i in xs.size():
				var h: float = w * float([0.4, 0.55, 0.5, 0.35][i])
				var x := roundf(float(xs[i]))
				for dx in maxi(1, int(u * 0.7)):
					_line(back, Vector2(x + dx, ground), Vector2(x + dx, ground - h), 0.85)
				_dot(back, Vector2(x, ground - h - 1.0), 1.0)
				_dot(back, Vector2(x - 1.0, ground - h - 2.0), 0.8)
				_dot(back, Vector2(x + 1.0, ground - h - 2.0), 0.8)
		"plunge":
			for i in 2:
				var y := head - u * (1.5 + i * 1.5)
				_line(back, Vector2(chest.x - u, y - u), Vector2(chest.x, y), 1.0 - i * 0.25)
				_line(back, Vector2(chest.x, y), Vector2(chest.x + u, y - u), 1.0 - i * 0.25)
			_arc(front, Vector2(chest.x, ground), w * 0.35, maxf(2.0, u), 0.0, PI, 1.0)
		"rain":
			for i in int(w / 4.0):
				var at := Vector2(rng.randi_range(1, int(w) - 2), rng.randi_range(1, int(w * 0.6)))
				_line(back, at, at + Vector2(-1, 2), 0.85)
		"release":
			for ang in [-PI / 2.0, -PI / 2.0 - 0.4, -PI / 2.0 + 0.4, -PI / 2.0 - 0.8, -PI / 2.0 + 0.8]:
				var d := Vector2.from_angle(ang)
				var top := Vector2(chest.x, head + u)
				_line(back, top + d * u * 2.0, top + d * w * 0.5, 0.9)
		"return":
			var c := hand + Vector2(u * 1.5, 0)
			_arc(front, c, u * 2.0, u * 2.5, -2.4, 2.0, 1.0)
			var tip := c + Vector2(cos(2.0) * u * 2.0, sin(2.0) * u * 2.5)
			_line(front, tip, tip + Vector2(u, 0), 1.0)
			_line(front, tip, tip + Vector2(0, -u), 1.0)
		"seal":
			var side := u * 3.0
			var o := Vector2(minf(hand.x + u * 0.5, w - side - 1.0), hand.y - side * 0.5).round()
			_rect(front, Rect2(o, Vector2(side, side)), 1.0)
			_rect(front, Rect2(o + Vector2(2, 2), Vector2(side - 4.0, side - 4.0)), 0.7)
			_line(front, o + Vector2(side * 0.5, 3), o + Vector2(side * 0.5, side - 3.0), 1.0)
		"seeker":
			var x := hand.x
			while x < w - u * 1.5:
				_dot(front, Vector2(x, hand.y + sin((x - hand.x) / maxf(1.0, u)) * u), 0.8)
				x += 1.0
			_sparkle(front, Vector2(w - u * 1.5, hand.y + sin((w - u * 1.5 - hand.x) / maxf(1.0, u)) * u), 1.0)
		"snare":
			var c := hand + Vector2(u * 2.5, 0)
			_arc(front, c, u * 1.5, u * 1.5, 0.0, TAU, 1.0)
			var x := hand.x
			while x < c.x - u * 1.5:
				_dot(front, Vector2(x, hand.y), 0.8)
				x += 2.0
			_arc(back, chest, b.size.x * 0.5 + u, u, 0.0, TAU, 0.6)
		"swarm":
			for i in 6:
				var at := Vector2(rng.randf_range(hand.x, w - 2.0), rng.randf_range(b.position.y + 1.0, ground - 2.0))
				_line(front, at, at + Vector2(1, 0), 1.0)
				_dot(front, at - Vector2(1, 0), 0.6)
		"sweep":
			var c := Vector2(chest.x, chest.y + u)
			_arc(front, c, w * 0.42, maxf(2.0, w * 0.14), 0.2, PI - 0.2, 1.0, 2)
			_arc(back, c, w * 0.42, maxf(2.0, w * 0.14), PI + 0.3, TAU - 0.3, 0.7)
		"volley":
			for j in [-1, 0, 1]:
				var y: float = hand.y + float(j) * (u + 1.0)
				var end := hand.x + u * 3.0 - absf(j) * u
				_line(front, Vector2(hand.x, y), Vector2(end, y), 0.85)
				_line(front, Vector2(end - 1.0, y - 1.0), Vector2(end, y), 1.0)
				_line(front, Vector2(end - 1.0, y + 1.0), Vector2(end, y), 1.0)
		"ward":
			var c := Vector2(chest.x, ground)
			var rx := b.size.x * 0.5 + u * 2.0
			var ry := ground - b.position.y + u * 1.5
			_arc(back, c, rx, ry, PI, TAU, 0.95)
			_arc(back, c, rx - u, ry - u, PI + 0.3, TAU - 0.3, 0.6)
			_line(front, Vector2(c.x - rx - 1.0, ground), Vector2(c.x - rx + u * 2.0, ground), 0.8)
			_line(front, Vector2(c.x + rx - u * 2.0, ground), Vector2(c.x + rx + 1.0, ground), 0.8)
		"wave":
			for j in 2:
				var base := ground - u * (1.0 + j * 2.0)
				var x := hand.x - u
				while x < w - 1.0:
					_dot(front, Vector2(x, base + sin(x * 0.9 + j) * u * 0.7), 1.0 - j * 0.25)
					x += 1.0
		_:   # a strike: the palm's crescents ahead of it, as the reference's Flowing Palm
			for i in 3: _crescent(front, hand + Vector2(i * (u + 1.0) - u, 0), u + 1.0 + i, 1.0 - i * 0.1)

static func _dot(img: Image, at: Vector2, v: float) -> void:
	var x := int(roundf(at.x))
	var y := int(roundf(at.y))
	if x < 0 or y < 0 or x >= img.get_width() or y >= img.get_height(): return
	img.set_pixel(x, y, Color(v, v, v, 1.0))

static func _line(img: Image, a: Vector2, b: Vector2, v: float) -> void:
	var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
	for i in n + 1: _dot(img, a.lerp(b, float(i) / maxf(1.0, n)), v)

## An elliptic arc from angle `a0` to `a1` (radians, y down); every `gap`-th pixel only when gap > 1.
static func _arc(img: Image, c: Vector2, rx: float, ry: float, a0: float, a1: float, v: float, gap := 1) -> void:
	var n := int(maxf(rx, ry) * absf(a1 - a0) * 1.4) + 2
	for i in n + 1:
		if gap > 1 and i % gap != 0: continue
		var ang := lerpf(a0, a1, float(i) / n)
		_dot(img, c + Vector2(cos(ang) * rx, sin(ang) * ry), v)

static func _rect(img: Image, r: Rect2, v: float) -> void:
	_line(img, r.position, Vector2(r.end.x, r.position.y), v)
	_line(img, Vector2(r.end.x, r.position.y), r.end, v)
	_line(img, r.end, Vector2(r.position.x, r.end.y), v)
	_line(img, Vector2(r.position.x, r.end.y), r.position, v)

## A crescent ")" of radius `r` round `c`: thin at its horns, two pixels thick at its middle.
static func _crescent(img: Image, c: Vector2, r: float, v: float) -> void:
	_arc(img, c, r, r, -1.1, 1.1, v)
	_arc(img, c, r - 1.0, r - 1.0, -0.6, 0.6, v)

## A star's sparkle: a plus of five pixels.
static func _sparkle(img: Image, at: Vector2, v: float) -> void:
	_dot(img, at, v)
	for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]: _dot(img, at + d, v * 0.8)

## A music note: a head of four pixels, a stem up and its flag.
static func _note(img: Image, at: Vector2, u: float, v: float) -> void:
	for d in [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1), Vector2(1, 1)]: _dot(img, at + d, v)
	_line(img, at + Vector2(1, 0), at + Vector2(1, -u * 2.0 - 1.0), v)
	_line(img, at + Vector2(1, -u * 2.0 - 1.0), at + Vector2(u + 1.0, -u * 1.5), v)

# ------------------------------------------------------------------ states over a picture
## The cooldown over a picture in `r`: an ink sweep over the `frac` still to wait, from the top round, cut to the
## picture, its edge a pale gold hand; the seconds left in the middle.
static func draw_cooldown(ci: CanvasItem, r: Rect2, frac: float, seconds: float, a := 1.0) -> void:
	var p := r.grow(-3.0)
	var f := clampf(frac, 0.0, 1.0)
	if f > 0.02:
		var c := p.get_center()
		var reach := p.size.length()
		var pie := PackedVector2Array([c])
		for i in 33: pie.append(c + Vector2.from_angle(-PI / 2.0 + TAU * f * (i / 32.0)) * reach)
		var box := PackedVector2Array([p.position, Vector2(p.end.x, p.position.y), p.end, Vector2(p.position.x, p.end.y)])
		for poly in Geometry2D.intersect_polygons(pie, box): ci.draw_colored_polygon(poly, Color(UiKit.INK, 0.72 * a))
		var hand := Vector2.from_angle(-PI / 2.0 + TAU * f)
		var half := p.size * 0.5
		ci.draw_line(c, c + hand * minf(half.x / maxf(0.001, absf(hand.x)), half.y / maxf(0.001, absf(hand.y))), Color(UiKit.PALE_GOLD, 0.85 * a), 1.5)
	UiKit.draw_outlined(ci, str(int(ceil(seconds))), Vector2(r.get_center().x - 20.0, r.get_center().y + 8.0), 22, Color(UiKit.PAPER, a), HORIZONTAL_ALIGNMENT_CENTER, 40)
	if draw_log != null: draw_log.append({"state": "cooldown", "rect": r, "frac": f})

## Short of Qi: a strip along the picture's foot, the pool's reach toward the cost in Qi blue on an ink trough.
static func draw_qi_short(ci: CanvasItem, r: Rect2, frac: float, a := 1.0) -> void:
	var p := r.grow(-3.0)
	var strip := Rect2(p.position.x + 2.0, p.end.y - 7.0, p.size.x - 4.0, 5.0)
	ci.draw_rect(strip.grow(1.0), Color(UiKit.INK, a))
	ci.draw_rect(Rect2(strip.position, Vector2(strip.size.x * clampf(frac, 0.0, 1.0), strip.size.y)), Color(UiKit.QI, a))
	if draw_log != null: draw_log.append({"state": "qi", "rect": r, "frac": clampf(frac, 0.0, 1.0)})

## Closed: a lock in the lower right corner, bronze on an ink plate.
static func draw_lock(ci: CanvasItem, r: Rect2, a := 1.0) -> void:
	if draw_log != null: draw_log.append({"state": "lock", "rect": r})
	var at := r.end - Vector2(19, 21)
	rounded(ci, Rect2(at - Vector2(3, 3), Vector2(20, 22)), 4.0, Color(UiKit.INK, 0.85 * a))
	ci.draw_arc(at + Vector2(7, 7), 4.5, PI, TAU, 10, Color(UiKit.BRONZE, a), 2.5)
	ci.draw_rect(Rect2(at + Vector2(0, 7), Vector2(14, 10)), Color(UiKit.BRONZE, a))
	ci.draw_rect(Rect2(at + Vector2(6, 10), Vector2(2, 4)), Color(UiKit.INK, a))

static func rounded(ci: CanvasItem, rect: Rect2, radius: float, col: Color) -> void:
	var key := "%d|%s" % [int(radius), col.to_html()]
	if not _boxes.has(key):
		var sb := StyleBoxFlat.new()
		sb.bg_color = col
		sb.set_corner_radius_all(int(radius))
		sb.anti_aliasing = true
		if _boxes.size() > 256: _boxes.clear()
		_boxes[key] = sb
	ci.draw_style_box(_boxes[key], rect)
