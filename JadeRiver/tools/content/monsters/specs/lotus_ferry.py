"""Lotus Ferry's foes: the Reed Shallows (the mud crab, the reed rat, Old Snapper) and the Hollow Night on the village's
river (the hollow minnows and the hollowed eel, the first boss)."""
from content.monsters import species

# The early surprises (docs/research/player_motivation.md item 7, §3.4): the first monsters carry rare rows, a river
# pearl and a manual page (tools/data/enemies.py _EARLY).
EARLY = "early"

species("mudshell_crab", plan="crab.mud", size=1.2,
        palette=["shell", "shell_rim", "shell_pale", "crab_leg", "claw", "claw_tip", "eye"], accents=("claw_tip",), gold=("eye",),
        shadow=(12, 4), cycle=10.0, sideways=True,
        data=dict(level=1, role="normal", element="water", page="valley_shore", drops=[("crab_shell", 0.7), ("river_mud", 0.4)],
                  attacks=[("pinch", 0.4, 40)], ai="slow_melee", speed=55, width=20, height=26, aggro=0),
        # Research §3.3: Guo's three shells drop every kill while still wanted.
        loot=dict(starter=True, finds=EARLY,
                  quest=[{"item": "crab_shell", "chance": 1.0, "count": [1, 1], "quest": "crab_trouble"}]),
        sound=dict(body="shell", tell="water"))

species("reedtail_rat", plan="quadruped.rodent", size=1.26,
        palette=["fur", "fur_light", "pink", "tail_a", "tail_b"], accents=("pink",), shadow=(10, 3), cycle=11.0, view=True,
        data=dict(level=2, role="normal", element="none", page="valley_shore", drops=[("rat_tail", 0.6)], attacks=[("bite", 0.35, 36)],
                  ai="melee", speed=120, flee=0.25, width=18, height=22, aggro=150),
        loot=dict(starter=True, finds=EARLY))

species("old_snapper", plan="shell.snapper", size=1.8,
        palette=["snap_shell", "snap_moss", "snap_moss_lit", "snap_skin", "snap_belly", "snap_beak", "crusher", "crusher_tip", "weed",
                 "snap_eye", "maw"],
        accents=("crusher", "snap_eye"), elite=False, aura=True, shadow=(26, 6), cycle=9.0,
        data=dict(level=3, role="elite", element="water", page="valley_shore", drops=[("snapper_claw", 1.0)],
                  attacks=[("claw_slam", 0.6, 74, 1.4, dict(depth=34, knockback=40))], ai="snapper", speed=45, width=40, height=56,
                  phases=[{"below": 0.5, "action": "dig_in", "duration": 3.0, "invulnerable": True}],
                  appears_after={"item": "crab_shell", "count": 5},
                  # Tuned for a Mortal with bare fists (83 HP, no defence): about 135 HP and a 9-point claw, so a player
                  # who never steps out of the slam still wins with a tea or two, and one who reads the tell barely gets
                  # touched.
                  hp_mult=0.24, attack_mult=0.33),
        loot=dict(starter=True),
        sound=dict(body="shell", tell="water"))

# The Hollow Night (docs/redesign/story_staging.md "The Hollow Night"): grey minnows leap out of the river and dart at you
# in schools, a short tell and then a dash along the ground. One blow fells one, so a combo swung through a school fells
# several. On the height grid they skim under the blow's band (EnemyAuthority._hover). Those about a villager turn on
# you only as you come to the villager (a short sight); the event's waves hunt you (`hunt`).
species("hollow_minnow", plan="fish.minnow", size=1.5,
        palette=["minnow", "minnow_back", "minnow_belly", "minnow_fin", "strand"], accents=("strand",), elite=False, shadow=(5, 2),
        cycle=10.0,
        data=dict(level=1, role="event", element="hollow", page=None, drops=[],
                  attacks=[("dart", 0.55, 30, 0.6, dict(depth=26, dash=60))], ai="flyer", speed=85,
                  hp_override=5, width=14, height=18, flying=True, hollowing=1, aggro=150),
        # The Hollow Night's minnows leave a grey sliver behind now and then: the first Hollow shard the story puts in
        # your hand.
        loot=dict(finds=[{"item": "tiny_hollow_shard", "chance": 0.25, "count": [1, 1]}]),
        sound=dict(body="slime", tell="water"))

# The night's great foe, the first boss (decision 45, docs/redesign/story_staging.md "The first boss"), fought in two
# phases (EnemyAuthority._eel). Phase 1, the fight a player can read: it rears out of the river (the tell), lunges onto
# the bank where you stood, and lies stranded there, open to blows, until it slides back. Tuned for the story's Mortal
# (Level 0, about 80 HP, the first crab's short blade or Guo's gauntlets, no technique yet): a lunge takes about an
# eighth of that; the short blade takes it to four fifths of its HP in about three of its windows (tests/balance_sim.gd,
# "story night").
# Phase 2 at 80% of its HP (or 90 s into the fight, for a player who never strikes it): it wakes. It throws itself back
# into the river and rises again greater (the awakened sheet, its own music, the scene `eel_awakens`), the grey minnows
# fleeing it, and becomes more than a Mortal can meet: the surge, a faster tell, a longer reach and a band three tiles
# wide, that no guard or parry stops and that takes a share of the player's HP whatever they wear (a fifth: three or
# four of them have the player down); and the thrash round it where it lands. Its hide turns every blow: its HP never
# falls below `hp_floor` (72%) again. It cannot be won and it cannot kill: no blow takes the player under `overwhelm_hp`
# (30%), and the fight ends the moment one reaches it, or after `overwhelm_s` of the phase in any case (a player who
# dodges every surge: the river itself rises over the bank). The eel looms over the fallen player and the elders come
# (the scene `elders_come`, whose checkpoint slays it); should no scene play (the side view), the elders slay it in the
# simulation after `rescue_s`. Its flags carry the phase over a reload.
species("hollowed_eel", plan="serpent.eel", size=1.44,
        palette=["eel", "eel_belly", "eel_fin", "eel_mouth", "strand"], accents=("strand",), elite=False, shadow=(13, 4), cycle=12.0,
        sized=True,
        awakened={"size": 1.22, "ramps": {"eel": "eel_wake", "eel_belly": "eel_wake_belly", "eel_fin": "eel_wake_fin",
                                          "eel_mouth": "eel_wake_mouth", "strand": "strand_wake"}},
        data=dict(level=2, role="story_boss", element="hollow", page=None, drops=[("pearl", 1.0)],
                  attacks=[("lunge", 1.1, 34, 1.0, dict(depth=40, knockback=80)),
                           ("surge", 0.6, 60, 1.0, dict(depth=96, knockback=150, unblockable=True, hp_share=0.18, awake=True)),
                           ("thrash", 0.45, 70, 1.0, dict(depth=70, knockback=120, both_sides=True, unblockable=True, hp_share=0.12,
                                                          awake=True))],
                  ai="event_eel", width=26, height=60, flying=True, hollowing=2, hp_mult=1.0, attack_mult=0.3,
                  phases=[{"below": 0.8, "after_s": 90, "action": "awaken", "staged": True}], first_defeat=["hollow_eel_fang"],
                  eel={"glide_speed": 70, "reach": 190, "lunge_s": 0.28, "beached_s": 2.4, "retreat_s": 0.5, "rest_s": [1.6, 2.6],
                       "awaken_s": 1.6,
                       "awake": {"glide_speed": 150, "reach": 300, "lunge_s": 0.18, "beached_s": 0.5, "retreat_s": 0.35,
                                 "rest_s": [0.9, 1.4], "thrash_every": 2, "hp_floor": 0.72, "overwhelm_hp": 0.3, "overwhelm_s": 22.0,
                                 "rise_s": 1.2, "rescue_s": 30.0},
                       "flags": {"awake": "eel_awakened", "overwhelmed": "eel_overwhelmed"}}),
        sound=dict(body="slime", tell="water"))
