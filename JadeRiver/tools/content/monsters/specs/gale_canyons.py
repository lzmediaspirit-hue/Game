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

# M3. A wind spirit of the Kite Winds that took the shape of a giant festival kite, flying flat over its shadow: a
# swallow-shaped sail of crimson silk, gold-rimmed, an ink cloud painted on each wing, on a bamboo frame; a gold bird-head
# prow with a hooked beak, a crimson crest and a jade eye that glows; two crimson streamers banded in gold; wind trailing
# off its wing tips. It rears nose-up, its streamers pulled straight back, as the wind spirals in at its prow and its eyes
# glow (the tell, held), and dives steeply, slashing a wind crescent across the ground; struck, its silk tears; beaten,
# its spar snaps, its sail folds and it spirals down and fades.
species("wind_kite", plan="spirit.kite", share=True, size=2.3,
        palette=["wk_silk", "wk_gold", "wk_ink", "wk_bamboo", "wk_jade"], accents=("wk_jade",), shadow=(12, 4), cycle=14.0, view=True,
        data=dict(level=(73, 76), role="normal", element="wind", page="azure", drops=[("kite_silk", 0.45), ("storm_shard", 0.5, (1, 2))],
                  attacks=[("gust_dive", 0.55, 120, 1.25, dict(dash=140, knockback=90))],
                  ai="flyer", speed=140, flying=True, width=34, height=34, tameable=False))

# M3. A russet bird-woman spirit of the Harpy Roosts, "a human face on a bird's body": hovering upright, a lean barred
# russet body with a pale sandstone front, a pale human face with a hooked slate beak of a nose and burning amber eyes,
# two long barred plumes arching back from her crown like a warrior's pheasant feathers, broad barred wings for arms,
# shaggy feathered thighs and hooked slate talons hanging under her; a tattered crimson sash and a bone-bead necklace, all
# that is left of the cultivator she once was. She rears back, wings high and talons forward, and screeches (the tell,
# held: her rake's and her screech's), and dives to rake with her talons; struck, feathers burst off her; beaten, she
# tumbles out of the air, lands on her back and fades.
species("canyon_harpy", plan="bird.harpy", share=True, size=2.6,
        palette=["ch_plume", "ch_flight", "ch_under", "ch_face", "ch_slate", "ch_sash", "ch_bone", "maw"], accents=("ch_sash",), shadow=(10, 3),
        cycle=14.0, view=True,
        data=dict(level=(74, 78), role="normal", element="wind", page="azure", drops=[("harpy_plume", 0.45), ("storm_shard", 0.55, (1, 2))],
                  attacks=[("talon_rake", 0.5, 80, 1.3, dict(dash=90, status={"id": "bleed", "chance": 0.25, "power": 0.015, "duration_s": 4})),
                           ("screech", 0.8, 220, 0.9, dict(damage_type="soul", depth=80,
                                                          status={"id": "slow", "chance": 0.4, "power": 0.3, "duration_s": 3}))],
                  ai="flyer", speed=120, flying=True, width=34, height=44, tameable=False))
