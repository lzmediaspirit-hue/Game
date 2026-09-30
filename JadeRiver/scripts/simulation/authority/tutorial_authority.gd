class_name TutorialAuthority
extends Authority
## Decision 43 · unlock tutorials (docs/redesign/tutorials.md): every newly unlocked system teaches itself. This authority
## keeps each character's progress through data/tutorials.json in the character's `tutorials`:
##   - seen: the tours played through or skipped (a page's first opening plays its tour once);
##   - guided: the guides done or skipped (never queued again);
##   - queue: the guides whose trigger held, waiting in turn (priority, then arrival), so two unlocks never collide;
##   - at: the step each tour in progress stands at, so a reload resumes it.
## A guide is queued the first time its trigger holds (TutorialRules.triggered). A character saved before the tutorials
## (or one that skipped the Prologue) counts what it already has as known, so an old save gets no flood of lessons; so
## does one saved before a later batch of them (the record's `v` older than an entry's `since`: decision 44's late HUD
## powers). A HUD power's guide goes on after its tour to the page that manages it (TutorialRules.guide_after_tour).
## The coach (scripts/ui/tutorial_coach.gd) shows them and reports each step through the intents; it alone decides when
## (never in a fight, a staged scene or a talk). Nothing is queued while every system is forced open (debug tools).

const POLL_S := 0.5
## Decision 45: the poll looks again only at the passing states (the points to spend, a thing in the bag, a bottleneck, a
## technique slotted) every POLL_S; every guide, the unlocks' too, once in FULL_POLLS (the events answer an unlock at
## once). Looking at all seventy every half second cost a third of a millisecond on a desktop, a hitch on a phone.
const PASSING := ["points", "item", "bottleneck", "technique"]
const FULL_POLLS := 10
## The guides an event can bring (the rest wait for the poll): a system opened brings any.
const KINDS_OF := {"item_added": ["item"], "bottleneck_reached": ["bottleneck"], "level_changed": ["points", "technique"]}
var _poll := 0.0
var _polls := 0
## actor -> the room a guide's "go to the place" step leads to while the coach shows it (not saved): the direction mark
## and the World map's lantern lead there first (WorldAuthority.guide_target).
var goals: Dictionary = {}

func intents() -> Array:
	return ["tutorial_step", "tutorial_done", "tutorial_replay", "tutorial_goal"]

func subscribe() -> void:
	# A system opened or a thing found is answered in the same pass, not at the next poll.
	for ev in ["system_unlocked", "item_added", "bottleneck_reached", "level_changed"]:
		var kinds: Array = KINDS_OF.get(ev, [])
		GameEvents.subscribe(ev, func(p): _on_change(p, kinds), 90)
	GameEvents.subscribe("character_created", func(p): _on_created(p), 90)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	var st := state(c)
	match str(intent.type):
		"tutorial_step":
			var tour := str(intent.get("tour", ""))
			if TutorialRules.entry(tour).is_empty(): return fail("unknown_tour")
			st.at[tour] = maxi(0, int(intent.get("step", 0)))
			return ok()
		"tutorial_done":
			var id := str(intent.get("id", ""))
			if TutorialRules.entry(id).is_empty(): return fail("unknown_tour")
			if str(intent.get("stage", "tour")) == "guide":
				st.guided[id] = 2 if intent.get("skipped", false) else 1
				st.queue.erase(id)
			else:
				st.seen[id] = 2 if intent.get("skipped", false) else 1
				st.at.erase(id)
				# A tour seen needs no guide to it any more (a HUD power's goes on to the page that manages it).
				if st.queue.has(id) and not TutorialRules.guide_after_tour(TutorialRules.entry(id)):
					st.queue.erase(id)
					st.guided[id] = 1
			return ok()
		"tutorial_goal":
			var room := str(intent.get("room", ""))
			if room == "": goals.erase(c.id)
			elif ContentDB.room(room).is_empty(): return fail("unknown_room")
			else: goals[c.id] = room
			return ok()
		"tutorial_replay":
			# Settings → Replay tutorials: every tour plays again on its page's next opening; a page's "?" plays its own.
			var one := str(intent.get("tour", ""))
			if one == "":
				st.seen.clear()
				st.at.clear()
				# The coach lets the page open now be (Settings): its tour waits for its next opening, as the others'.
				emit("tutorials_replayed", {"actor": c.id})
			else:
				st.seen.erase(one)
				st.at.erase(one)
			return ok()
	return fail("unknown_intent")

## The character's tutorial record, its fields filled in (an old save's "legacy" mark is settled on the first look).
func state(c) -> Dictionary:
	var st: Dictionary = c.tutorials
	# Settled already (the coach asks every frame): as it is.
	if st.get("seen") is Dictionary and st.get("guided") is Dictionary and st.get("at") is Dictionary and st.get("queue") is Array \
			and not st.has("legacy") and int(st.get("v", 1)) >= TutorialRules.version():
		return st
	for k in ["seen", "guided", "at"]:
		if not (st.get(k) is Dictionary): st[k] = {}
	if not (st.get("queue") is Array): st["queue"] = []
	if st.get("legacy", false):
		st.erase("legacy")
		_know_all(c)
	var v := TutorialRules.version()
	if int(st.get("v", 1)) < v:
		_know_since(c, int(st.get("v", 1)))
		st["v"] = v
	return st

## A new character's record is current (and one that skips the Prologue knows its systems).
func _on_created(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	if not c.tutorials.has("legacy"): c.tutorials["v"] = TutorialRules.version()
	if p.get("skip_prologue", false): _know_prologue(c)

func tick(delta: float) -> void:
	_poll += delta
	if _poll < POLL_S: return
	_poll = 0.0
	_polls += 1
	evaluate(game.active(), [] if _polls % FULL_POLLS == 0 else PASSING)

func _on_change(p: Dictionary, kinds: Array) -> void:
	var c = game.character(str(p.get("actor", game.active_id)))
	if c != null and str(c.id) == game.active_id: evaluate(c, kinds)

## Queue every guide whose trigger holds now and that is not done, waiting or seen (its tour played already); of the
## trigger `kinds` named only (none named: every guide).
func evaluate(c, kinds: Array = []) -> void:
	if c == null or Unlocks.debug_force_all: return
	var st := state(c)
	var added := false
	# A guide to a passing state (points to spend, a bottleneck, a thing in the bag) that has passed is not needed.
	for id in (st.queue as Array).duplicate():
		var qe := TutorialRules.entry(str(id))
		if str(qe.get("trigger", {}).get("kind", "")) in ["points", "bottleneck", "item"] and not TutorialRules.triggered(c, qe):
			st.queue.erase(id)
			st.guided[str(id)] = 1
	for e in TutorialRules.entries():
		var id := str(e.id)
		if st.guided.has(id) or st.queue.has(id) or st.seen.has(id): continue
		if not kinds.is_empty() and not (str((e.get("trigger", {}) as Dictionary).get("kind", "")) in kinds): continue
		if not TutorialRules.triggered(c, e): continue
		st.queue.append(id)
		added = true
	if added: _order(st)

## The queue in priority order (higher first), arrival keeping the order among equals.
func _order(st: Dictionary) -> void:
	var q: Array = st.queue
	var keyed: Array = []
	for i in q.size(): keyed.append([-int(TutorialRules.entry(str(q[i])).get("priority", 0)), i, str(q[i])])
	keyed.sort()
	st.queue = keyed.map(func(k): return k[2])

## The guide at the head of the queue ("" for none).
func head(c) -> String:
	if c == null: return ""
	var q: Array = state(c).queue
	return str(q[0]) if not q.is_empty() else ""

## The room a guide leads to now ("" for none).
func goal_of(c) -> String:
	return str(goals.get(c.id, "")) if c != null else ""

func seen(c, tour: String) -> bool:
	return c != null and state(c).seen.has(tour)

## The step a tour in progress stands at (0 when it has not started).
func step_of(c, tour: String) -> int:
	return int(state(c).at.get(tour, 0)) if c != null else 0

func in_progress(c, tour: String) -> bool:
	return c != null and state(c).at.has(tour)

## An old save (or a character that skipped the Prologue) knows what it has: each entry whose trigger holds now, or
## whose page it could open, is counted guided and seen.
func _know_all(c) -> void:
	var st: Dictionary = c.tutorials
	for e in TutorialRules.entries():
		var tr: Dictionary = e.get("trigger", {})
		var gate := str(tr.get("unlock", ""))
		if TutorialRules.triggered(c, e) or (gate != "" and Unlocks.is_unlocked(c.id, gate)) or (gate == "" and str(tr.get("kind", "")) == "page"):
			st.guided[str(e.id)] = 1
			st.seen[str(e.id)] = 1

## A record saved at version `from` knows what it has of the entries a later version brought: each whose trigger holds
## now, or whose system is open, is counted guided and seen (a Sphere Lord's old save is not taught Spirit Sense).
func _know_since(c, from: int) -> void:
	var st: Dictionary = c.tutorials
	for e in TutorialRules.entries():
		if int(e.get("since", 1)) <= from: continue
		var gate := str(e.get("trigger", {}).get("unlock", ""))
		if TutorialRules.triggered(c, e) or (gate != "" and Unlocks.is_unlocked(c.id, gate)):
			st.guided[str(e.id)] = 1
			st.seen[str(e.id)] = 1
			st.queue.erase(str(e.id))

func _know_prologue(c) -> void:
	if c == null: return
	var st := state(c)
	for e in TutorialRules.entries():
		if e.get("prologue", false):
			st.guided[str(e.id)] = 1
			st.seen[str(e.id)] = 1
			st.queue.erase(str(e.id))
