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
