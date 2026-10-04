"""The Siege's foe (M3; the story's siege of the sect's wall, level 58): the Hollow Behemoth, which comes out of the grey
north of the wall with its hollowed boarlets."""
from content.monsters import species

# M3. The Hollow Behemoth (story boss): a giant boar assembled out of the Hollow's grey-white drones and armour plates
# over a dark void, twice a person's height at its spiked ridge: rows of plates over its back, hump, flanks and hips, a
# ridge of spiked drones down its spine and a swarm of them in its belly, a plated skull with a pale snout disc and great
# curved tusks, empty white eyes. Its weak points are jagged white cracks on its flank plates and its skull plate,
# glowing cold, and mist pours off it. It rears up on its hind legs as its weak points blaze (the tell, held: its
# stampede's and its drone burst's) and stampedes in dust; struck, its weak points flicker; beaten, it breaks apart into
# drones and a heap of plates.
species("hollow_behemoth", plan="quadruped.behemoth", share=True, size=3.4, elite=False, shadow=(30, 8), cycle=16.0, view=True,
        canvas=(232, 184),
        palette=["hb_plate", "hb_void", "hb_drone", "hb_tusk"],
        data=dict(level=58, role="story_boss", element="hollow_earth", page=None, drops=[("siege_medal", 1.0), ("mistjade_robe", 1.0)],
                  attacks=[("stampede", 0.7, 90, 1.4, dict(dash=240, knockback=120, shatter=True)),
                           ("drone_burst", 1.0, 200, 1.0, dict(both_sides=True, depth=70))],
                  ai="boss_behemoth", width=80, height=140, hollowing=8,
                  # P1: the Behemoth sheds Hollowed boarlets at 60% and stampedes without pause below 30%.
                  phases=[{"below": 0.6, "action": "summon", "summon": "hollowed_boarlet", "summon_level": 56},
                          {"below": 0.3, "action": "enrage", "cooldown": 0.65, "damage": 1.3}]))
