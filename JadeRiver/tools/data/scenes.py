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
  tutorial                true: a beat of the tutorial walk (tests/topdown_tutorial.gd plays each one to its end)
  steps                   the script (SceneRules.STEP_KINDS): actor steps (move, face, emote, pose, say; a pose is an
                          action of the top-down figure, data/topdown/character.json, among them the story's gestures:
                          salute, kneel, point, startle), the camera
                          (camera, zoom, shake, letterbox), the screen (fade, flash, title), the world (spawn, despawn,
                          door, weather, moment, fx, sound), the flow (wait, wait_input, wait_event, branch, label, goto,
                          mark) and the hand-off (handoff: the player acts, a prompt over what to do, until an event)

A scene only asks the authorities for what it changes: its checkpoints (`mark` and `handoff` steps) go to the Quest
authority (scene_mark), which keeps where the scene is (a scene cut short by quitting resumes there) and applies the
step's `effects` once. Cells are the layouts' cells (fractions allowed). SceneRules.problems checks every scene against
the rooms, the people, the tile set, the event contract and the sounds; the suites hold every scene to none.
Every name, place and line here is Jade River's own.
"""
from common import entries, all_of, qactive, qdone, flag, noflag

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
def move(actor, *to, run=False, wait=True, speed=None):
    d = {"do": "move", "actor": actor, "to": [list(t) for t in to], "run": run, "wait": wait}
    if speed:
        d["speed"] = speed
    return d


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
        d["at"] = list(at)
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


def scene(sid, name, room, steps, actors=None, requires=None, trigger=None, live=False, tutorial=True):
    d = {"id": sid, "name": name, "room": room, "actors": actors or {}, "steps": steps, "live": live, "tutorial": tutorial}
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
        handoff("Drink it: tap Quick-use", "hud:quick", until("item_used", item="herbal_tea"), then="live"),
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
def night():
    # The Hollow Night: a storm, the river boils, something grey rises; Granny calls for the hut.
    scene("hollow_rises", "The Hollow Night", "lf_village_night", [
        title("That Night", "", 2.0),
        letterbox(True),
        weather("storm"),
        sound("thunder"),
        flash("MIST", 0.25),
        camera((24, 34), 1.4),
        fx("ring", (14, 35), color="MIST", radius=40, dur=0.8),
        fx("ring", (32, 36), color="MIST", radius=40, dur=0.8),
        sound("hiss"),
        emote("dou", "!", 0.8),
        pose("dou", "startle", 2.4),
        pose("granny", "startle", 2.4),
        say("dou", "Something's in the water! It's coming up!"),
        camera("player", 1.0),
        pose("granny", "point", 2.0),
        say("granny", "Child! Get us to your aunt's hut. Quickly now!"),
    ], actors={"dou": {"object": "npc_dou_night"}, "granny": {"object": "npc_granny_night"}},
        requires=all_of(qactive("the_hollow_night")))

    # Lu's boat after the storm: who Lu thinks you are. Sit, and breathe (the Cultivate button by doing).
    scene("river_token", "The River Token", "lf_lu_boat", [
        letterbox(True),
        weather("clear"),
        face("lu", "player"),
        pose("lu", "point", 2.6),
        say("lu", "That thing in the water was a Hollowed eel. The grey is spreading."),
        pose("lu", "kneel", 2.4),
        say("lu", "You have a gift. I felt it last night. Sit. Breathe as I showed you."),
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


def build():
    del S[:]
    opening()
    lessons()
    crabs()
    night()
    stoneford()
    entries("scenes", S, settings=SETTINGS)


if __name__ == "__main__":
    build()
