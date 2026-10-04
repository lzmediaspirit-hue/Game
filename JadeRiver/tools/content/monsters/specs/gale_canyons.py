"""The Gale Canyons' foes (M3; Act II, the Canyon Mouth, the Kite Winds, the Harpy Roosts, the Windbridge and the Riven
Peak, levels 73-78): the veiled canyon brigands, the wind kites and the canyon harpies.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline."""
from content.monsters import person, species

# M3. A veiled canyon brigand (the quest `the_canyon_toll`): a weimao's veil over a ponytail, an ochre v-neck, earth
# cuffed trousers, boots, a dagger. Its tell is the dagger drawn back in a crouch, held; it stabs (and throws knives on
# the same tell).
species("canyon_brigand", plan="person.fighter", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=(73, 76), role="normal", element="wind", page=None, drops=[("storm_shard", 0.5), ("spirit_stone_shard", 0.4, (1, 2))],
                  attacks=[("dagger_flurry", 0.35, 50, 1.1), ("throwing_knife", 0.5, 240, 1.0, dict(projectile={"speed": 600, "art": "arrow"}))],
                  ai="duelist",
                  art=person("Canyon Brigand", hair="ponytail", hair_color=3, shirt="vneck", pants="cuffed", shoes="boots", weapon="dagger",
                             hat="weimao", shirt_dye="ochre", pants_dye="earth"),
                  race="human", energy="sage_qi", width=18, height=90))
