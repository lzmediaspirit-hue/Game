"""Decision 39 (docs/redesign/story_staging.md): the story staged in the top-down world. data/scenes.json holds every
staged scene: in-engine scripts played by the SceneDirector (scripts/presentation/scene_director.gd) in a room on the
height grid, the camera moving, the people walking, facing, emoting and speaking there, things happening in the world,
and the player handed the controls to do what the scene teaches.

A scene:
  id, name, room          the room on the grid it plays in (tools/data/topdown_rooms.py lays it out)
  requires                when it may play (the Requirement format); `trigger` {event, when}: it plays when that event
                          comes (MomentRules' matchers), else as soon as the character stands in its room
  actors                  name -> {object: an NPC object of the room} | {npc: a person of npcs.json, at: [x, y] cell,
                          hidden: brought on by a `spawn` step} | {prop: a prop of the tile set, at, level}
  live                    true: a scene played around the player, the controls kept (no cut, no letterbox)
  hold_fight              true: a cut that holds the fight itself (decision 45: the first boss's waking and its
                          rescue): it may start while foes fight, and the simulation stands still under it
  resume                  false: a fight's moment, not taken up again after a reload; its trigger plays it whole
  tutorial                true: a beat of the tutorial walk (tests/topdown_tutorial.gd plays each one to its end)
  steps                   the script (SceneRules.STEP_KINDS): actor steps (move, face, emote, pose, say; a pose is an
                          action of the top-down figure, data/topdown/character.json, among them the story's gestures:
                          salute, kneel, point, startle), the camera
                          (camera, zoom, shake, letterbox), the screen (fade, flash, title), the world (spawn, despawn,
                          door, weather, moment, fx, sound; decision 45: art, a story art of the FX sheets where a
                          target stands, foe, a foe of the room staged, and hitstop, the stage's clock held a moment),
                          the flow (wait, wait_input, wait_event, branch, label, goto, mark) and the hand-off (handoff:
                          the player acts, a prompt over what to do, until an event). A spawn's `at` or a walk's
                          waypoint may be `beside(target, dx, dy)`: cells from wherever that target stands as the step
                          begins (the elders come to where the fight is)

A scene only asks the authorities for what it changes: its checkpoints (`mark` and `handoff` steps) go to the Quest
authority (scene_mark), which keeps where the scene is (a scene cut short by quitting resumes there) and applies the
step's `effects` once. Cells are the layouts' cells (fractions allowed). SceneRules.problems checks every scene against
the rooms, the people, the tile set, the event contract and the sounds; the suites hold every scene to none.
Every name, place and line here is Jade River's own.
"""
from common import entries, all_of, any_of, qactive, qdone, flag, noflag, sect

SETTINGS = {
    "walk": 110.0, "run": 210.0,                   # an actor's pace, world units a second
    "read_base_s": 1.0, "read_word_s": 0.28, "read_min_s": 2.0, "read_max_s": 5.5,   # how long a line holds
    "tap_s": 1.0,                                  # a wait for a tap, as the play clock counts it
    "min_s": 10.0, "max_s": 40.0,                  # a scene's staged seconds (its hand-offs aside)
    "skip_hold_s": 0.8,                            # hold anywhere this long to skip to the next hand-off
    "letterbox_h": 64, "letterbox_s": 0.35,        # the bars, and how long they slide
    "balloon_w": 380, "emote_s": 1.2,              # a speech balloon's widest line; an emote's life
    "home_s": 1.6,                                 # the longest an actor takes walking home after its scene
    "resume_back": True,                           # a scene cut short resumes at its last checkpoint
}


# -------------------------------------------------------------------- the steps
def move(actor, *to, run=False, wait=True, speed=None, est_s=None):
    d = {"do": "move", "actor": actor, "to": [t if isinstance(t, dict) else list(t) for t in to], "run": run, "wait": wait}
    if speed:
        d["speed"] = speed
    if est_s:
        d["est_s"] = est_s          # a walk to beside something where it stands: how long it holds the stage
    return d


def beside(target, dx=0.0, dy=0.0, mirror=None):
    """Decision 45: a place `dx` cells right and `dy` down of wherever `target` stands as the step begins ("player", an
    actor, "enemy:<def>"); a person's spot is the nearest a body can stand on. With `mirror` (another target), the
    offset is written as if that one stood to the right of `target`, and turned about when it stands to the left."""
    out = {"near": target, "off": [dx, dy]}
    if mirror:
        out["mirror"] = mirror
    return out


def face(actor, to):
    return {"do": "face", "actor": actor, "to": list(to) if isinstance(to, tuple) else to}


def emote(actor, kind, s=None, wait=False):
    d = {"do": "emote", "actor": actor, "emote": kind, "wait": wait}
    if s:
        d["s"] = s
    return d


def pose(actor, name, s=None, wait=False):
    d = {"do": "pose", "actor": actor, "pose": name, "wait": wait}
    if s:
        d["s"] = s
    return d


def say(actor, text, box="balloon"):
    return {"do": "say", "actor": actor, "text": text, "box": box}


def wait(s):
    return {"do": "wait", "s": s}


def camera(to="player", s=1.0, wait=True):
    return {"do": "camera", "to": list(to) if isinstance(to, tuple) else to, "s": s, "wait": wait}


def zoom(z, s=0.8, wait=False):
    return {"do": "zoom", "z": z, "s": s, "wait": wait}


def shake(s=0.2, amp=-1.0):
    return {"do": "shake", "s": s, "amp": amp}


def letterbox(on=True):
    return {"do": "letterbox", "on": on}


def fade(to, s=1.0):
    return {"do": "fade", "to": to, "s": s}


def flash(color="PALE_GOLD", s=0.3):
    return {"do": "flash", "color": color, "s": s}


def title(t, sub="", s=2.6):
    return {"do": "title", "title": t, "sub": sub, "s": s}


def spawn(actor, at=None):
    d = {"do": "spawn", "actor": actor}
    if at:
        d["at"] = at if isinstance(at, dict) else list(at)
    return d


def despawn(actor):
    return {"do": "despawn", "actor": actor}


def door(portal):
    return {"do": "door", "portal": portal}


def weather(kind):
    return {"do": "weather", "kind": kind}


def fx(kind, at="player", **kw):
    d = {"do": "fx", "fx": kind, "at": list(at) if isinstance(at, tuple) else at}
    d.update(kw)
    return d


def sound(sfx):
    return {"do": "sound", "sfx": sfx}


def art(name, at="player", scale=1, come_from=None):
    """Decision 45: a story art of the FX sheets (tools/art/fx/story_arts.py) where a target stands. An art that comes
    in from one side (the water dragon: drawn rising east of its mark) is turned to come from `come_from`'s side."""
    d = {"do": "art", "art": name, "at": list(at) if isinstance(at, tuple) else at}
    if scale != 1:
        d["scale"] = scale
    if come_from:
        d["from"] = come_from
    return d


def foe(def_id, pose="", flash=False, dread=None):
    """Decision 45: a foe of the room staged in a cut: its figure held in `pose` (its sheet's action; "" its own
    again), and struck white with `flash`. `dread=False`: the world's dread (TopdownWorld.DREAD, while an awake foe
    lives) lifts from it now, before it falls (the elders have it bound)."""
    d = {"do": "foe", "foe": def_id, "pose": pose, "flash": flash}
    if dread is not None:
        d["dread"] = bool(dread)
    return d


def hitstop(s=0.12):
    """Decision 45: the stage's clock held a moment, its effects and the struck figure with it."""
    return {"do": "hitstop", "s": s}


def label(name):
    return {"do": "label", "name": name}


def goto(name):
    return {"do": "goto", "label": name}


def branch(req, then, otherwise):
    return {"do": "branch", "if": req, "then": then, "else": otherwise}


def until(event, mine=True, **when):
    """An event a hand-off or a wait ends on; `mine`: the active character's own. A value "active" stands for its id."""
    return {"event": event, "when": dict(when, actor="active") if mine else when}


def handoff(prompt, at, *events, done_if=None, s=0.0, then="cut", effects=()):
    d = {"do": "handoff", "prompt": prompt, "at": list(at) if isinstance(at, tuple) else at, "until": list(events), "then": then}
    if done_if:
        d["done_if"] = done_if
    if s:
        d["s"] = s
    if effects:
        d["effects"] = list(effects)
    return d


def mark(*effects):
    return {"do": "mark", "effects": list(effects)}


S = []


def scene(sid, name, room, steps, actors=None, requires=None, trigger=None, live=False, tutorial=True, hold_fight=False, resume=True):
    d = {"id": sid, "name": name, "room": room, "actors": actors or {}, "steps": steps, "live": live, "tutorial": tutorial}
    if hold_fight:
        d["hold_fight"] = True
    if not resume:
        d["resume"] = False
    if requires:
        d["requires"] = requires
    if trigger:
        d["trigger"] = trigger
    for i, st in enumerate(steps):
        assert "do" in st, (sid, i, st)
    S.append(d)


def on(event, **when):
    return {"event": event, "when": dict(when, actor="active")}


# -------------------------------------------------------------------- the opening (docs/tutorial_order.md steps 0-2)
def opening():
    # The river at dawn: who you are (Aunt Ping's charge, your mother's stubborn chin), the tea as the first gift (the
    # Bag), and the first thing you do is walk: the door is the hand-off.
    scene("opening_dawn", "The River at Dawn", "lf_fishers_hut", [
        fade("black", 0.01),
        title("Jade River", "Lotus Ferry, the hour before dawn", 2.8),
        sound("water_step"),
        fade("clear", 1.2),
        letterbox(True),
        emote("ping", "note", 1.4),
        pose("ping", "idle"),
        face("ping", "player"),
        emote("ping", "!", 0.9, wait=True),
        say("ping", "You're up! Good. The river muttered all night and kept me awake with it."),
        move("ping", (8, 5)),
        face("ping", "e"),
        fx("motes", "ping", color="PALE_GOLD", count=6, dur=0.6),
        move("ping", (5, 5)),
        face("ping", "player"),
        say("ping", "Here. Tea for the road. It's in your Bag, beside your hand."),
        fx("ring", "player", color="BRIGHT_JADE", radius=24, dur=0.5),
        sound("pickup"),
        handoff("Your Bag holds her tea", "hud:icon:bag", until("page_opened", page="inventory"), s=3.5),
        say("ping", "Your mother stood at that door every dawn, watching the water. You have her stubborn chin."),
        pose("ping", "point", 2.2),
        say("ping", "Lu wants you at the docks. Something about the river. Go on."),
        handoff("Walk to the door: drag the stick", "portal:exit", until("room_left")),
    ], actors={"ping": {"object": "npc_aunt_ping"}}, requires=all_of(qactive("morning_tide")))

    # Home Lane at dawn: a boat slips by, the villagers talk of grey water, Little Dou's kite snaps free and lands on the
    # inn roof (the lesson waiting there); the camera comes back to you with Lu at the docks to find.
    scene("river_dawn", "Home Lane at Dawn", "lf_village", [
        letterbox(True),
        move("boat", (46, 36), wait=False, speed=95),
        camera((24, 30), 2.4),
        camera("mei", 1.2),
        face("mei", "e"),
        say("mei", "Grey water by the reeds again. Third morning running."),
        move("ping", (11, 22), (13, 29)),
        face("ping", "mei"),
        say("ping", "Hush, Mei. Not where the little ones can hear."),
        emote("mei", "sweat", 1.0),
        sound("gust"),
        camera((55, 15), 1.6, wait=False),
        move("dou", (50, 20), (55, 17), run=True),
        face("dou", "n"),
        emote("dou", "!", 0.9, wait=True),
        pose("dou", "point", 2.0),
        say("dou", "My kite! The wind took it onto the inn roof!"),
        camera("player", 1.4),
        say("ping", "Lu's at the docks, by the boats. Off you go."),
    ], actors={"mei": {"object": "npc_washer_mei"}, "ping": {"object": "npc_aunt_ping_lane"},
               "dou": {"object": "npc_little_dou"}, "boat": {"prop": "boat", "at": [-3, 36], "level": -1}},
        requires=all_of(qactive("a_quiet_river")))

    # Lu's four errands, shown where they wait: Guo at his stump, Dou under the kite, Old Ma's door, Granny Liu's hut.
    scene("four_errands", "Four Errands", "lf_village", [
        letterbox(True),
        pose("lu", "point", 1.6),
        say("lu", "Four errands, four corners of the village. Look."),
        camera("guo", 1.2),
        face("guo", "e"),
        pose("guo", "punch_1", 0.35, wait=True),
        sound("hit"),
        pose("guo", "punch_2", 0.35, wait=True),
        sound("hit"),
        say("guo", "Hah! Hup!"),
        camera("dou", 1.0),
        emote("dou", "?", 1.2, wait=True),
        camera("portal:store_door", 1.0),
        wait(0.6),
        camera("portal:granny_door", 1.0),
        wait(0.6),
        camera("player", 1.0),
        say("lu", "Any order you like. The river will keep until you're done."),
    ], actors={"lu": {"object": "npc_lu_boatman"}, "guo": {"object": "npc_uncle_guo"}, "dou": {"object": "npc_little_dou"}},
        trigger=on("quest_completed", quest="a_quiet_river"))


# -------------------------------------------------------------------- the four lessons (step 3)
def lessons():
    # Fists First: Guo shows the jab, cross, jab on his stump, then hands you the stump.
    scene("guo_fists", "Fists First", "lf_village", [
        letterbox(True),
        move("guo", (30, 25)),
        face("guo", "e"),
        say("guo", "Watch. Jab, cross, jab. The hip turns, the fist follows."),
        pose("guo", "punch_1", 0.3, wait=True),
        fx("spark", "object:stump_guo", color="PALE_GOLD", count=6, dur=0.3),
        sound("hit"),
        pose("guo", "punch_2", 0.3, wait=True),
        fx("spark", "object:stump_guo", color="PALE_GOLD", count=6, dur=0.3),
        sound("hit"),
        pose("guo", "punch_3", 0.35, wait=True),
        fx("ring", "object:stump_guo", color="PALE_GOLD", radius=26, dur=0.35),
        sound("hit_crit"),
        shake(0.15),
        face("guo", "player"),
        say("guo", "Your turn. Five on the stump."),
        handoff("Punch the stump: tap Attack", "object:stump_guo", until("object_hit", object="stump_guo"), then="live"),
        emote("guo", "note", 1.0),
        say("guo", "Elbow in! Good. Keep going."),
    ], actors={"guo": {"object": "npc_uncle_guo"}}, trigger=on("quest_accepted", quest="fists_first"))

    # The Runaway Kite: Dou shows the way up, crates to the hall roof to the inn.
    scene("kite_route", "The Way Up", "lf_village", [
        letterbox(True),
        face("dou", "n"),
        pose("dou", "point", 2.2),
        say("dou", "Up the crates, onto the hall roof, then jump across to the inn!"),
        camera((46, 14), 1.0),
        fx("ring", (46.5, 13), color="BRIGHT_JADE", radius=22, dur=0.6),
        camera((51, 12), 1.0),
        camera((58, 12), 1.0),
        fx("motes", "object:kite", color="PALE_GOLD", count=8, dur=0.8),
        wait(0.6),
        camera("player", 1.0),
        emote("dou", "!", 0.8),
        say("dou", "It's the best kite in Lotus Ferry. Please hurry!"),
    ], actors={"dou": {"object": "npc_little_dou"}}, trigger=on("quest_accepted", quest="the_runaway_kite"))

    # Race to the Tower: Shen Lian counts you down and runs; you chase him to the bell (sprint taught by a race).
    scene("tower_race", "Race to the Tower", "lf_village", [
        letterbox(True),
        face("shen", "player"),
        say("shen", "Race you to the watch-tower bell. Loser guts tomorrow's fish."),
        say("shen", "On three. One... two..."),
        face("shen", "e"),
        emote("shen", "!", 0.6),
        move("shen", (60, 24), (65, 22), run=True, wait=False, speed=150),
        handoff("Race him to the bell: push the stick all the way", "object:tower_bell",
                until("quest_completed", quest="race_to_the_tower"), until("quest_failed", quest="race_to_the_tower"),
                until("object_interacted", object="tower_bell")),
        branch(qdone("race_to_the_tower"), "won", "lost"),
        label("lost"),
        emote("shen", "note", 1.0),
        say("shen", "Too slow! Tomorrow's fish are yours to gut."),
        goto("end"),
        label("won"),
        emote("shen", "anger", 1.0),
        say("shen", "What?! ...Fine. Don't let it go to your head."),
        label("end"),
    ], actors={"shen": {"object": "npc_shen_lian_npc"}}, trigger=on("quest_accepted", quest="race_to_the_tower"))

    # Granny's Remedy: a jar falls from the herb loft and grazes you (a real graze, the HP bar dips), she hands you to
    # the Bag and the Quick-use slot, and you drink: the healing slot taught by an injury.
    scene("granny_jar", "Granny's Remedy", "lf_granny_liu_hut", [
        letterbox(True),
        face("granny", "n"),
        say("granny", "Now where did I put the willow bark..."),
        fx("dust", (3, 3), dur=0.5),
        sound("rockfall"),
        shake(0.2),
        mark({"kind": "restore_resource", "pool": "hp", "pct": -0.3}),
        emote("player", "sweat", 1.0),
        emote("granny", "!", 0.8),
        pose("granny", "startle", 0.7, wait=True),
        move("granny", (7, 8)),
        face("granny", "player"),
        pose("granny", "kneel", 3.0),
        say("granny", "Oh! My clumsy shelves. Hold still, child, you're scratched."),
        say("granny", "Take a tea from your Bag and put it where your hand finds it: Quick-use."),
        handoff("Open your Bag: put Herbal Tea in Quick-use", "hud:icon:bag", until("quick_use_changed", item="herbal_tea"), then="live"),
        # The tea's heal shows (the number over the head, the log's line): the controls stay, and Granny waits a moment
        # before she speaks, her balloon clear of the number (the prototype's QA: a cut hid both at once).
        handoff("Drink it: tap Quick-use", "hud:quick:0", until("item_used", item="herbal_tea"), then="live"),   # decision 45: the first of three
        wait(1.4),
        emote("granny", "heart", 1.0),
        say("granny", "Better. Now bow at the shrine in the square. It remembers those who visit."),
    ], actors={"granny": {"object": "npc_granny_liu"}}, trigger=on("quest_accepted", quest="grannys_remedy"))


# -------------------------------------------------------------------- Crab Trouble (step 4)
def crabs():
    # The four lessons done, Guo opens the East Gate for you.
    scene("east_gate", "The East Gate", "lf_village", [
        letterbox(True),
        say("guo", "The village is done with you. The shallows aren't."),
        camera("portal:east_gate", 1.6),
        door("east_gate"),
        wait(0.8),
        camera("player", 1.2),
        say("guo", "Reed Shallows, just past the gate. Mind the claws."),
    ], actors={"guo": {"object": "npc_uncle_guo"}}, trigger=on("quest_accepted", quest="crab_trouble"))

    # The first fight: the crabs have Washer Mei backed against the reeds. Drive one off (the first kill drops the first
    # weapon), and she thanks you on her way home.
    scene("crabs_mei", "Crabs on the Flats", "lf_reed_shallows", [
        letterbox(True),
        camera((10, 16), 1.2),
        emote("mei", "!", 0.8),
        pose("mei", "startle", 1.2),
        say("mei", "Shoo! Get back in the river, the lot of you!"),
        move("mei", (6, 14), run=True),
        face("mei", "player"),
        say("mei", "They came up out of the water in the night. Dozens!"),
        camera("player", 0.8),
        handoff("Drive off a crab: tap Attack", "enemy:mudshell_crab", until("actor_defeated", False, killer="active", **{"def": "mudshell_crab"}), then="live"),
        emote("mei", "heart", 1.2),
        say("mei", "Thank you! It dropped something. A gutting knife? Keep it."),
        move("mei", (0, 14)),
        despawn("mei"),
    ], actors={"mei": {"npc": "washer_mei", "at": [12, 16]}}, requires=all_of(qactive("crab_trouble")))


# -------------------------------------------------------------------- the night and the boat (steps 6-7)
def wait_event(*events, s=0.0):
    d = {"do": "wait_event", "until": list(events)}
    if s:
        d["s"] = s
    return d


def night():
    # The Hollow Night (decision 42, docs/redesign/story_staging.md "The Hollow Night"): the tutorial's first real danger,
    # an action set piece in beats. The room's event (world.py lf_village_night) and the foes' AI (EnemyAuthority: the
    # minnows' dart, the eel's tell, lunge and window) are the fight; these scenes stage it around the player, live
    # while the fight is on: the storm and the first minnows, each villager running for Aunt Ping's door, the grey
    # spreading up the lane, the eel rising; then (decision 45, the first boss) the eel waking, the cut that holds the
    # fight, and the elders coming to slay it when it has the player down; and the grey lifting after, where the
    # elders tell you what cultivation is.
    villagers_in = all_of(flag("dou_safe"), flag("granny_safe"), flag("ma_safe"))
    night_on = all_of(qactive("the_hollow_night"))
    ping = {"object": "npc_ping_night"}
    scene("hollow_rises", "The Hollow Night", "lf_village_night", [
        title("That Night", "", 2.0),
        letterbox(True),
        weather("storm"),
        sound("thunder"),
        flash("MIST", 0.25),
        camera((24, 34), 1.2),
        shake(0.4),
        sound("rumble"),
        fx("ring", (14, 35), color="MIST", radius=40, dur=0.8),
        fx("ring", (30, 36), color="MIST", radius=52, dur=0.9),
        fx("ring", (41, 35), color="MIST", radius=40, dur=0.8),
        sound("hiss"),
        fx("spark", (44, 27), color="MIST", count=10, dur=0.6),
        camera("dou", 0.9),
        emote("dou", "!", 0.8),
        pose("dou", "startle", 2.4),
        say("dou", "Fish! Grey fish, jumping out of the river! They bite!"),
        camera("granny", 1.0),
        pose("granny", "point", 2.0),
        say("granny", "Child! Get us to your aunt's hut. Quickly now!"),
        camera("ping", 1.0),
        say("ping", "In here, all of you! The door's open and the lamp is lit!"),
        camera("player", 0.8),
        handoff("Strike the grey minnows: tap Attack", "enemy:hollow_minnow",
                until("actor_defeated", False, killer="active", **{"def": "hollow_minnow"}),
                done_if=any_of(flag("dou_safe"), flag("granny_safe"), flag("ma_safe")), then="live"),
        say("ping", "Bring them to my door! The grey things shy from the lamp."),
    ], actors={"dou": {"object": "npc_dou_night"}, "granny": {"object": "npc_granny_night"}, "ping": ping}, requires=night_on)

    # Each villager sent in runs (or hobbles) through the night to Aunt Ping's door.
    for sid, name, flag_id, npc, at, path, run, line, ping_line in [
            ("night_dou_runs", "Little Dou Runs", "dou_safe", "little_dou", (44, 25), [(44, 21), (8, 21), (6.5, 15.5)], True,
             "I'm going! Don't let them bite you!", "Dou! In, in, by the stove. Who's next?"),
            ("night_granny_goes", "Granny Liu Goes In", "granny_safe", "granny_liu", (18, 23), [(17.5, 21), (8, 21), (6.5, 15.5)], False,
             "Bless you, child. There's a healing pill in your hand now: swallow it if that thing bites.", "Granny Liu, lean on me. Go on, child, the others!"),
            ("night_ma_goes", "Old Ma Leaves Her Shop", "ma_safe", "old_ma", (38, 18), [(38, 21), (8, 21), (6.5, 15.5)], True,
             "My stock can drown for all I care. I'm going, I'm going!", "Ma! Mind the step. Inside with you!")]:
        scene(sid, name, "lf_village_night", [
            spawn("who"),
            face("who", "player"),
            say("who", line),
            move("who", *path, run=run),
            despawn("who"),
            emote("ping", "heart", 1.0),
            say("ping", ping_line),
        ], actors={"who": {"npc": npc, "at": list(at), "hidden": True}, "ping": ping}, requires=night_on,
            trigger=on("flag_set", flag=flag_id), live=True)

    # The villagers in, the grey spreads: schools pour up the lane from both ends, and Ping shows where her lamplight is
    # a refuge. Its last step marks it played (the flag grey_spread): the eel's scene waits on it, so the lane's beat
    # always comes first however long the last villager's run took (the eel rises 14 s after they are in, in the game's
    # time; the scenes are live, so the eel may already be out, and no line here speaks of the river).
    scene("grey_spreads", "The Grey Spreads", "lf_village_night", [
        shake(0.35),
        sound("rumble"),
        say("ping", "That's all of them. Now you, child, get in here!"),
        fx("ring", (2, 21), color="MIST", radius=56, dur=0.9),
        fx("ring", (45, 21), color="MIST", radius=56, dur=0.9),
        sound("hiss"),
        emote("ping", "!", 1.0),
        pose("ping", "point", 2.0),
        say("ping", "The lane! They're coming up both ends of it!"),
        wait(1.0),
        fx("ring", (8.5, 16.5), color="PALE_GOLD", radius=90, dur=1.2),
        say("ping", "Too many of them? Come into my lamplight. They won't follow you here!"),
        mark({"kind": "set_flag", "flag": "grey_spread"}),
    ], actors={"ping": ping}, requires=all_of(qactive("the_hollow_night"), villagers_in, noflag("eel_awakened")), live=True)

    # The eel rises (its boss card plays first): the tell taught while it circles, once the lane's beat has played.
    scene("eel_rises", "The Thing in the River", "lf_village_night", [
        sound("surge"),
        shake(0.5),
        say("ping", "Heaven help us, look at it! Child, when it rears up, get out of its line!"),
        handoff("It rears before it lunges: step aside, then strike it on the bank", "enemy:hollowed_eel", s=8.0, then="live"),
        say("ping", "Hit it while it's stranded, before it slides back!"),
        wait(1.0),
        say("ping", "It's only a beast, for all it's grey. It bleeds!"),
    ], actors={"ping": ping}, requires=all_of(qactive("the_hollow_night"), flag("grey_spread"), noflag("eel_awakened")),
        trigger={"event": "enemy_aggro", "when": {"def": "hollowed_eel"}}, live=True)

    # Decision 45, the first boss (docs/redesign/story_staging.md "The first boss"): at four fifths of its HP the eel
    # wakes. A cut that holds the fight: the camera on it, the river boiling round it, its roar, the screen shaking and
    # the night's colours bruising (TopdownWorld's dread), Aunt Ping's warning; then the controls back with the truth of
    # it on the prompt. Played whole again if a reload cuts it short.
    scene("eel_awakens", "The Eel Wakes", "lf_village_night", [
        letterbox(True),
        camera("enemy:hollowed_eel", 0.5),
        zoom(1.2, 0.5),
        foe("hollowed_eel", "windup"),
        sound("story_eel_roar"),
        shake(0.7),
        art("river_boil", "enemy:hollowed_eel"),
        flash("MIST", 0.3),
        fx("ring", "enemy:hollowed_eel", color="MIST", radius=80, dur=0.9),
        wait(0.8),
        sound("story_river_boil"),
        art("river_boil", "enemy:hollowed_eel"),
        say("ping", "The river's boiling round it... it's growing!"),
        shake(0.4),
        emote("ping", "!", 1.0),
        say("ping", "Child, run! No blade can cut that thing now!"),
        say("ping", "Keep moving! Don't let it pin you!"),
        zoom(1.0, 0.4, wait=True),
        foe("hollowed_eel"),
        handoff("Its hide turns every blow now: stay alive!", "player", s=5.0, then="live"),
    ], actors={"ping": ping}, requires=night_on, trigger={"event": "boss_phase", "when": {"def": "hollowed_eel", "action": "awaken"}},
        hold_fight=True, resume=False)

    # The rescue: the eel has the player down, and the elders of Lotus Ferry come out of the dark. Granny Liu, whom you
    # walked to Aunt Ping's door on her old legs, binds it with Nine Seals; Old Ma, who left his shop to drown, drops
    # the Thousand-Catty Palm on it; Lu comes up the river and his river dragon ends it (the checkpoint that slays it:
    # the night is won). Each lands where the fight is (beside), with its art, its sound, a hit-stop and a shake.
    elders = {"granny": {"npc": "granny_liu", "at": [6.5, 16.5], "hidden": True}, "ma": {"npc": "old_ma", "at": [9.5, 16.5], "hidden": True},
              "lu": {"npc": "lu_boatman", "at": [36, 33], "hidden": True}}
    scene("elders_come", "The Elders Come", "lf_village_night", [
        letterbox(True),
        pose("player", "knockdown"),
        camera("player", 0.4),
        foe("hollowed_eel", "windup"),
        sound("story_eel_roar"),
        shake(0.35),
        say("ping", "No! Get away from the child!"),
        spawn("granny", beside("player", -2.2, -0.6, mirror="enemy:hollowed_eel")),
        fx("dust", "granny", color="PAPER", count=8, dur=0.5),
        sound("land"),
        face("granny", "enemy:hollowed_eel"),
        say("granny", "Old legs, child. Not old hands."),
        pose("granny", "cast", 0.7, wait=True),
        foe("hollowed_eel", "windup", dread=False),   # her seals' light takes the night's dread off it
        art("talisman_array", "enemy:hollowed_eel"),
        sound("story_talisman"),
        wait(0.6),
        foe("hollowed_eel", "hurt", flash=True),
        hitstop(0.12),
        flash("PALE_GOLD", 0.2),
        shake(0.3),
        say("granny", "Nine seals. Now it cannot dive."),
        spawn("ma", beside("player", -0.6, -2.0, mirror="enemy:hollowed_eel")),
        fx("dust", "ma", color="PAPER", count=8, dur=0.5),
        sound("land"),
        face("ma", "enemy:hollowed_eel"),
        say("ma", "Thousand-Catty Palm! That one's for my shop!"),
        pose("ma", "punch_2", 0.4, wait=True),
        art("force_palm", "enemy:hollowed_eel"),
        sound("story_palm"),
        wait(0.3),
        foe("hollowed_eel", "hurt", flash=True),
        hitstop(0.18),
        flash("GOLD", 0.2),
        shake(0.5),
        move("boat", beside("enemy:hollowed_eel", -4.0, 2.0, mirror="player"), wait=False, speed=260),
        say("ping", "A lamp on the water... it's Lu!"),
        spawn("lu", beside("enemy:hollowed_eel", -2.2, -0.2, mirror="player")),
        fx("dust", "lu", color="PAPER", count=8, dur=0.5),
        sound("land"),
        face("lu", "enemy:hollowed_eel"),
        say("lu", "Back to the dark, grey thing. This river is mine."),
        pose("lu", "point", 0.8, wait=True),
        zoom(1.15, 0.4),
        art("water_dragon", "enemy:hollowed_eel", come_from="lu"),
        sound("story_dragon"),
        wait(0.75),
        foe("hollowed_eel", "hurt", flash=True),
        mark({"kind": "slay_foe", "enemy": "hollowed_eel", "by": "elders"}),
        hitstop(0.25),
        flash("PAPER", 0.3),
        shake(0.7),
        sound("boss_fall"),
        wait(1.4),
        zoom(1.0, 0.6),
        camera("player", 0.6),
    ], actors=dict(elders, boat={"prop": "boat", "at": [52, 36.5], "level": -1}, ping=ping),
        requires=all_of(qactive("the_hollow_night"), noflag("night_held")), trigger={"event": "boss_overwhelmed", "when": {"def": "hollowed_eel"}},
        hold_fight=True, resume=False)

    # The night won (the elders slew the eel; or, as a last resort, the bank held until its time ran out): the storm
    # passes and the elders tell you what you saw. It plays as you stand in the night with it won (after a reload too);
    # its last checkpoint sets lu_on_the_bank, and the event's way on takes you to his boat, where cultivation begins.
    scene("grey_lifts", "The Grey Lifts", "lf_village_night", [
        letterbox(True),
        weather("clear"),
        sound("gust"),
        spawn("granny", beside("player", -2.5, -1.5)),
        spawn("ma", beside("player", 2.5, -1.5)),
        spawn("lu", beside("player", 2.5, 1.2)),
        camera("player", 0.6),
        fx("motes", "player", color="PALE_GOLD", count=14, dur=1.2),
        mark({"kind": "heal", "pct": 1.0}),
        pose("player", "idle"),
        move("granny", beside("player", -1.2, -0.3), est_s=1.0),
        face("granny", "player"),
        say("granny", "Up you get. A bruise or two. Nothing broken."),
        say("ping", "Granny? Old Ma? You... you fought that thing?"),
        face("ma", "player"),
        say("ma", "Every old dog in this village had a sect once."),
        say("granny", "What you saw was cultivation, child. Qi, drawn in and let out."),
        move("lu", beside("player", 1.2, 0.6), est_s=1.0),
        face("lu", "player"),
        say("lu", "You held the bank with a blade and nothing more."),
        say("lu", "When it struck you, I felt your Qi stir. You have the gift."),
        pose("lu", "point", 1.6),
        say("lu", "Come to my boat. Tonight you begin to cultivate."),
        mark({"kind": "set_flag", "flag": "lu_on_the_bank"}),
        fade("black", 0.8),
    ], actors=dict(elders, ping=ping), requires=all_of(qactive("the_hollow_night"), flag("night_held")))

    # Lu's boat after the storm: who Lu thinks you are. Sit, and breathe (the Cultivate button by doing).
    scene("river_token", "The River Token", "lf_lu_boat", [
        letterbox(True),
        weather("clear"),
        face("lu", "player"),
        pose("lu", "point", 2.6),
        say("lu", "That thing in the water was a Hollowed eel. The grey is spreading."),
        pose("lu", "kneel", 2.4),
        say("lu", "You have a gift. I felt it stir on the bank. Sit. Breathe as I tell you."),
        pose("lu", "meditate"),
        camera("player", 0.8),
        handoff("Meditate: tap Cultivate", "hud:meditate", until("meditation_started")),
    ], actors={"lu": {"object": "npc_lu_boat"}}, requires=all_of(qactive("the_river_token")))

    # The first breakthrough as a scene: the realm's moment plays, then Lu stands, and when the token is handed over he
    # shows the palm on the river and tells you why you leave: west, to the sects.
    scene("first_breakthrough", "Bone Forging", "lf_lu_boat", [
        letterbox(True),
        zoom(1.25, 0.8),
        pose("lu", "idle"),
        emote("lu", "!", 0.8, wait=True),
        say("lu", "There. You felt the bones take it. Bone Forging: your first step."),
        zoom(1.0, 0.6),
        handoff("Talk to Lu", "lu", until("quest_completed", quest="the_river_token")),
        move("lu", (12, 8)),
        face("lu", "e"),
        say("lu", "Watch the water. Push, the way the river pushes the boat."),
        pose("lu", "punch_2", 0.4, wait=True),
        fx("wave", (15, 8), color="BRIGHT_JADE", size=10, radius=60, dur=0.6),
        sound("technique"),
        shake(0.15),
        face("lu", "player"),
        pose("lu", "point", 2.4),
        say("lu", "Flowing Palm. The sects are choosing disciples at Stoneford this spring. Go west."),
        zoom(1.0, 0.2),
    ], actors={"lu": {"object": "npc_lu_boat"}}, trigger=on("breakthrough_succeeded", to="bone_forging_1"))


# -------------------------------------------------------------------- Stoneford and the fair (steps 8-9)
def stoneford():
    # Market Street: a purse snatched at the tea house, the thief away over the west road; the rooftop thief foretold.
    scene("market_thief", "A Thief in the Market", "sf_market", [
        letterbox(True),
        camera((32, 14), 1.4),
        spawn("thief", (33, 15)),
        emote("rong", "anger", 1.0),
        pose("rong", "startle", 1.4),
        say("rong", "My purse! Thief! Stop him!"),
        move("thief", (20, 16), (1, 16), run=True, wait=False, speed=230),
        camera((16, 16), 1.4),
        despawn("thief"),
        camera("player", 1.2),
        face("lin", "player"),
        pose("lin", "point", 2.0),
        say("lin", "Quick-Fingered Hou. He lives on the rooftops, that one."),
        say("lin", "Keep your purse close in Stoneford, newcomer."),
    ], actors={"rong": {"object": "npc_auntie_rong"}, "lin": {"object": "npc_courier_lin"},
               "thief": {"npc": "rooftop_thief", "at": [33, 15], "hidden": True}}, requires=all_of(qdone("the_river_token")))

    # The Recruitment Fair: the two recruiters call over each other; Shen Lian finds you in the crowd.
    scene("fair_arrival", "The Recruitment Fair", "sf_fairground", [
        title("The Recruitment Fair", "Stoneford", 2.4),
        letterbox(True),
        camera("qing", 1.4),
        pose("qing", "salute", 2.2),
        say("qing", "Jade Sect! The sword that writes, the brush that cuts!"),
        camera("mo", 1.0),
        pose("mo", "salute", 2.2),
        say("mo", "Cloud Sect! Why walk to the peak when you could fly there?"),
        emote("qing", "anger", 1.0),
        camera("player", 1.2),
        move("shen", (60, 17), run=True),
        face("shen", "player"),
        say("shen", "You came! Hear them both out, then choose. It's for life."),
    ], actors={"qing": {"object": "npc_recruiter_qing_lan"}, "mo": {"object": "npc_recruiter_mo_yun"},
               "shen": {"object": "npc_shen_lian"}}, requires=all_of(noflag("prologue_done")))

    # The sect chosen, as a scene at the fair: the recruiter welcomes you, the name written over the crowd, and Shen
    # Lian's rivalry begins.
    scene("sect_chosen", "The Sect Chosen", "sf_fairground", [
        letterbox(True),
        branch({"all": [{"kind": "training_sect", "sect": "cloud_sect"}]}, "cloud", "jade"),
        label("jade"),
        camera("qing", 1.0),
        emote("qing", "heart", 1.0),
        pose("qing", "salute", 2.6),
        pose("player", "salute", 2.6),
        say("qing", "Welcome to the Jade Sect. Keep your wrist loose and your word firm.", box="portrait"),
        title("The Jade Sect", "Service Disciple, on trial", 2.2),
        goto("rival"),
        label("cloud"),
        camera("mo", 1.0),
        emote("mo", "heart", 1.0),
        pose("mo", "salute", 2.6),
        pose("player", "salute", 2.6),
        say("mo", "Welcome to the Cloud Sect. We'll teach you to fall before we teach you to fly.", box="portrait"),
        title("The Cloud Sect", "Service Disciple, on trial", 2.2),
        label("rival"),
        camera("player", 1.0),
        emote("shen", "!", 0.8),
        say("shen", "Then I'll see you at the top. Or beat you there."),
    ], actors={"qing": {"object": "npc_recruiter_qing_lan"}, "mo": {"object": "npc_recruiter_mo_yun"},
               "shen": {"object": "npc_shen_lian"}}, trigger=on("sect_joined"))


# -------------------------------------------------------------------- the sect stretch (decision 42: less walking)
SECTS = {"jade_sect": {"tag": "jade", "gate": "ja_gate_street", "steward": "npc_jade_steward", "array": "array_ja_gate",
                       "peak": "ja_elder_hu_peak", "mentor": "npc_elder_hu", "peak_array": "array_ja_peak", "elder": "Elder Hu",
                       "down": "npc_elder_hu_marsh", "glow": "BRIGHT_JADE", "stand": (6, 19), "look": (8, 20)},
         "cloud_sect": {"tag": "cloud", "gate": "cm_cliff_stair", "steward": "npc_cloud_steward", "array": "array_cm_gate",
                        "peak": "cm_elder_sung_peak", "mentor": "npc_elder_sung", "peak_array": "array_cm_peak", "elder": "Elder Sung",
                        "down": "npc_elder_sung_marsh", "glow": "MIST", "stand": (7, 23), "look": (9, 24)}}


def sect_stretch():
    for sid, s in SECTS.items():
        mine = {"kind": "training_sect", "sect": sid}
        # The sect's transfer array, taught at the gate as Strange Tracks begins: the steward stops you on your way out
        # and shows you the ring (the watch post at the marsh keeps its twin). A breath, not half a day's walk.
        scene("array_lesson_" + s["tag"], "The Transfer Array", s["gate"], [
            letterbox(True),
            emote("steward", "!", 0.8),
            face("steward", "player"),
            say("steward", "%s's note? Then you're for the marsh. That's half a day on foot." % s["elder"]),
            move("steward", s["stand"]),
            camera("object:" + s["array"], 1.2),
            fx("ring", "object:" + s["array"], color=s["glow"], radius=44, dur=0.9),
            sound("portal"),
            face("steward", s["look"]),
            pose("steward", "point", 2.2),
            say("steward", "The sect's transfer array. The watch post at the marsh keeps its twin."),
            say("steward", "Stand in the ring and hold up your token. It answers disciples on the sect's errands."),
            camera("player", 1.0),
            handoff("Step onto the array: tap Travel", "object:" + s["array"], until("object_interacted", object=s["array"]), then="live"),
        ], actors={"steward": {"object": s["steward"]}}, requires=all_of(mine, qactive("strange_tracks")))

        # The Humming Token's five boarlets down, the mentor comes to the marsh on the light of his peak's array: the
        # hand-in is taken where the fight was, and he sends you to Mei Qing at the watch post, a few steps away.
        scene("mentor_descends_" + s["tag"], "%s Comes Down" % s["elder"], "rm_marsh_edge", [
            camera("elder", 0.8),
            fx("pillar", "elder", color=s["glow"], radius=20, height=320, dur=1.1),
            sound("surge"),
            shake(0.2),
            fx("wave", "elder", color=s["glow"], size=8, radius=56, dur=0.6),
            emote("elder", "...", 1.0, wait=True),
            face("elder", "player"),
            say("elder", "I felt the token hum from my peak. So the grey came up to meet you."),
            pose("elder", "point", 2.0),
            say("elder", "Five of them, and you still standing. Come, tell me, while it's fresh."),
            camera("player", 0.8),
            handoff("Talk to %s" % s["elder"], "elder", until("quest_completed", quest="the_humming_token")),
            fx("pillar", "elder", color=s["glow"], radius=16, height=320, dur=0.8),
            sound("portal"),
        ], actors={"elder": {"object": s["down"]}}, live=True,
            requires=all_of(mine, {"kind": "quest_ready", "quest": "the_humming_token"}),
            trigger=on("quest_ready", quest="the_humming_token"))

        # Grey at the Edges, the first time up the mentor's peak: what the grey means, and his peak's array keyed to the
        # token (the next trip up is a breath).
        scene("mentor_peak_" + s["tag"], "%s's Peak" % s["elder"], s["peak"], [
            letterbox(True),
            face("elder", "player"),
            say("elder", "Mei Qing's salve draws the grey out of a wound. Then it can be fought, and it will have to be."),
            say("elder", "It is coming down the river from somewhere. Keep Lu's token on you: it hums when the grey is near."),
            camera("object:" + s["peak_array"], 1.2),
            fx("ring", "object:" + s["peak_array"], color=s["glow"], radius=44, dur=0.9),
            sound("portal"),
            say("elder", "My peak's array knows your token now. The sect is yours to cross in a breath."),
            camera("player", 1.0),
        ], actors={"elder": {"object": s["mentor"]}}, trigger=on("quest_completed", quest="grey_at_the_edges"),
            requires=all_of(mine))

    # At the third grey patch the River Token hums: grey shapes rise where the patches were, and The Humming Token is
    # under way on the spot (no walk up the peak and back down).
    scene("grey_rises", "The Token Hums", "rm_marsh_edge", [
        fx("ring", "player", color="BRIGHT_JADE", radius=30, dur=0.7),
        sound("rare_chime"),
        emote("player", "!", 0.9),
        say("player", "(The River Token hums against your chest, the way it did on Lu's boat.)"),
        camera((33, 17), 1.4),
        fx("converge", (19, 16), color="MIST", radius=60, count=16, dur=1.0),
        fx("converge", (33, 17), color="MIST", radius=60, count=16, dur=1.0),
        fx("converge", (44, 16), color="MIST", radius=60, count=16, dur=1.0),
        sound("hiss"),
        wait(1.0),
        camera("player", 1.0),
        say("player", "(Grey shapes shoulder up out of the reeds where the patches were.)"),
    ], live=True, trigger=on("quest_completed", quest="strange_tracks"))

    # Something on the way, the first walk up through the sect's grounds (Grey at the Edges): a spar offered in the
    # training yard, two elders overheard on the terrace, a gardener's favour.
    up = qactive("grey_at_the_edges")
    scene("yard_spar_jade", "A Round at the Post", "ja_pavilion_rooftops", [
        emote("master", "!", 0.8),
        face("master", "player"),
        say("master", "The disciple back from the marsh! One round at the post before you climb?"),
        pose("master", "point", 2.0),
        say("master", "Mind the wind-up. Every disciple on the posts telegraphs the big swing."),
        say("master", "Win and the yard will know your name. Lose and you sweep it."),
        handoff("Spar at the post, or walk on", "object:spar_jp", until("object_interacted", object="spar_jp"), s=8.0, then="live"),
    ], actors={"master": {"object": "npc_jade_hall_master"}}, live=True, requires=all_of(sect("jade_sect"), up))
    scene("terrace_talk_jade", "Overheard on the Terrace", "ja_east_terrace", [
        move("physician", (26, 15)),
        face("physician", "elder"),
        face("elder", "physician"),
        say("physician", "Three watchers came back from the marsh grey to the elbow."),
        say("elder", "Mei Qing's salve drew it out. But grey doesn't blow in from nowhere."),
        emote("physician", "?", 1.0),
        say("physician", "The old maps mark a shrine under the river at Deepwater Bend..."),
        say("elder", "Drowned before either sect was founded. Hush. The new one's listening."),
        emote("elder", "!", 0.8),
        face("elder", "player"),
    ], actors={"elder": {"object": "npc_jade_formation_elder"}, "physician": {"object": "npc_jade_physician"}}, live=True,
        requires=all_of(sect("jade_sect"), up))
    scene("gardener_favour_jade", "A Pot of Tea", "ja_herb_terraces", [
        emote("gardener", "!", 0.8, wait=True),
        move("gardener", (12, 24)),
        face("gardener", "player"),
        say("gardener", "Going up to the elder? Wait, wait!"),
        pose("gardener", "point", 2.0),
        say("gardener", "Take him my lotus root tea. He forgets to drink when he's thinking, and he's always thinking."),
        handoff("Talk to Gardener Ji", "gardener", until("quest_accepted", quest="tea_for_the_elder"), s=8.0, then="live"),
    ], actors={"gardener": {"object": "npc_jade_gardener"}}, live=True, requires=all_of(sect("jade_sect"), up))
    scene("court_spar_cloud", "A Round at the Post", "cm_sword_court", [
        emote("master", "!", 0.8),
        face("master", "player"),
        say("master", "Back from the marsh already? Then a round at the post before you climb."),
        pose("master", "point", 2.0),
        say("master", "Or try the plum-blossom poles. Fall off and you sweep the court."),
        say("master", "Mind the wind-up. Every disciple on the posts telegraphs the big swing."),
        handoff("Spar at the post, or walk on", "object:spar_cm", until("object_interacted", object="spar_cm"), s=8.0, then="live"),
    ], actors={"master": {"object": "npc_cloud_hall_master"}}, live=True, requires=all_of(sect("cloud_sect"), up))
    scene("gardener_favour_cloud", "A Pot of Tea", "cm_array_court", [
        emote("gardener", "!", 0.8, wait=True),
        move("gardener", (10, 18)),
        face("gardener", "player"),
        say("gardener", "Going up to the elder? Wait, wait!"),
        pose("gardener", "point", 2.0),
        say("gardener", "Take him my lotus root tea. He forgets to drink when he's thinking, and he's always thinking."),
        handoff("Talk to Gardener Ren", "gardener", until("quest_accepted", quest="tea_for_the_elder"), s=8.0, then="live"),
    ], actors={"gardener": {"object": "npc_cloud_gardener"}}, live=True, requires=all_of(sect("cloud_sect"), up))
    scene("array_court_talk_cloud", "Overheard in the Array Court", "cm_array_court", [
        move("physician", (31, 16)),
        face("physician", "elder"),
        face("elder", "physician"),
        say("physician", "Two watchers back from the marsh, grey to the elbow."),
        say("elder", "Mei Qing's salve drew it out. But grey doesn't rise out of reeds by itself."),
        emote("physician", "?", 1.0),
        say("physician", "The old maps mark a shrine under the river at Deepwater Bend..."),
        say("elder", "Drowned before either sect was founded. Hush. The new one's listening."),
        emote("elder", "!", 0.8),
        face("elder", "player"),
    ], actors={"elder": {"object": "npc_cloud_formation_elder"}, "physician": {"object": "npc_cloud_physician"}}, live=True,
        requires=all_of(sect("cloud_sect"), up))


def build():
    del S[:]
    opening()
    lessons()
    crabs()
    night()
    stoneford()
    sect_stretch()
    entries("scenes", S, settings=SETTINGS)


if __name__ == "__main__":
    build()
