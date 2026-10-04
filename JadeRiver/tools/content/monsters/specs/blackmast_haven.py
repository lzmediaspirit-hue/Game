"""Blackmast Haven's foes (M4; the Blackmast Docks, the Gunners' Battery and the Flagship Deck, levels 85-90): the
Admiral's gunners and Admiral Voss.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline. The Admiral is a person of size, sculpted
(humanoid.admiral)."""
from content.monsters import person, species

# M4. One of the Admiral's gunners: a ponytail under a headband, an ochre coat, ink cuffed trousers, boots, a powder bomb in
# the right hand, its fuse lit (`person.thrower`). Its tell is the bomb drawn back across the body, the fuse sparking
# (its bombard's too), and it throws on the blow.
species("pirate_gunner", plan="person.thrower", share=True, size=1.0, shadow=(8, 3), cycle=12.0,
        data=dict(level=(85, 90), role="normal", element="fire", page="lantern",
                  drops=[("star_powder", 0.45), ("star_shard", 0.5, (1, 2)), ("comet_iron", 0.2)],
                  attacks=[("powder_bomb", 0.7, 300, 1.2, dict(depth=40, projectile={"speed": 420, "art": "pebble"},
                                                               status={"id": "burn", "chance": 0.3, "power": 0.01, "duration_s": 3})),
                           ("bombard", 1.2, 380, 1.5, dict(depth=70, knockback=120, projectile={"speed": 300, "art": "pebble"}))],
                  ai="ranged",
                  art=person("Pirate Gunner", hair="ponytail", hair_color=3, shirt="vneck", pants="cuffed", shoes="boots", weapon="none",
                             hat="headband", shirt_dye="ochre", pants_dye="ink"),
                  race="human", energy="sage_qi", width=18, height=90, pack=True))

# M4. Admiral Voss (the Flagship Deck's boss): tall, lean and imperious, a long indigo greatcoat to his knees trimmed and
# buttoned in gold with gold epaulettes, a black cape, ink trousers in tall black boots, a black lacquered official's hat
# whose long wings stand out to both sides, his black hair tied back, a thin drooping moustache; a starsteel sabre of pale
# blue light in his right hand, a brass hand cannon with a dragon's mouth in his left. His tell is the cannon levelled
# at you as its fuse sparks and the sabre is drawn back (held: his broadside's too), and he fires as he cuts.
species("admiral_voss", plan="humanoid.admiral", share=True, size=2.5, elite=False, shadow=(12, 4), cycle=11.0, view=True,
        canvas=(170, 160),
        palette=["folk_skin", "adm_coat", "adm_gold", "adm_trousers", "adm_boot", "adm_cape", "adm_hat", "adm_hair", "starsteel", "adm_brass",
                 "halberd_shaft", "maw"],
        data=dict(level=90, role="dungeon_boss", element="metal", page="lantern",
                  drops=[("admirals_seal", 1.0), ("comet_iron", 1.0, (3, 5)), ("star_shard", 1.0, (12, 18)), ("star_powder", 1.0, (2, 4)),
                         ("will_tempering_pill", 1.0, (1, 2))],
                  attacks=[("starsteel_cutlass", 0.5, 120, 1.35, dict(depth=50, knockback=90)),
                           ("broadside", 1.2, 420, 1.5, dict(depth=90, damage_type="qi", projectile={"speed": 360, "art": "pebble"})),
                           ("all_hands", 1.0, 0, 0.0, dict(summon="starsea_pirate"))],
                  ai="duelist",
                  art=person("Admiral Voss", hair="long_tied", hair_color=0, shirt="vneck", pants="martial", shoes="boots", weapon="sword",
                             hat="guan", shirt_dye="indigo", pants_dye="ink", cape="solid"),
                  race="human", energy="sage_qi", width=20, height=96, name="Admiral Voss",
                  hp_mult=1.6, attack_mult=0.9, presence=4,
                  phases=[{"below": 0.6, "action": "summon", "summon": "pirate_gunner", "summon_level": 88},
                          {"below": 0.3, "action": "enrage", "cooldown": 0.7, "damage": 1.3}]))
