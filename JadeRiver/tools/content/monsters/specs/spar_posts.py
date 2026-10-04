"""The spar opponents of Act II's posts (M3): the Alliance Champion at the Nine Peaks' Presence Terrace, and the Ironroot
Warden, Tie Shan, who tests you at the Ironroot Hold's gate (the quest `ironroot_blood`).

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline. Each is the same figure as the person who
stands at the post (Champion Qiao, Warden Tie Shan: their outfits are the rows')."""
from content.monsters import person, species

# M3. The Alliance Champion: a guan over a topknot, an indigo disciple's robe, ink trousers, boots, a spear. Its tell is
# the spear drawn back in a crouch, held; it thrusts.
species("alliance_champion", plan="person.fighter", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=72, role="trial", element="metal", page=None, drops=[],
                  attacks=[("peak_thrust", 0.45, 110, 1.2, dict(depth=30)), ("nine_step_sweep", 0.7, 150, 1.3, dict(depth=50, knockback=90))],
                  ai="duelist",
                  art=person("Alliance Champion", hair="topknot", hair_color=0, shirt="disciple", pants="martial", shoes="boots", weapon="spear",
                             hat="guan", shirt_dye="indigo", pants_dye="ink"),
                  race="human", width=18, height=90, spar=True))

# M3. The Ironroot Warden (Tie Shan): a headband over a short knot, an earth-dyed sleeveless jacket and trousers, boots,
# an iron-shod staff. His tell is the staff raised over his head in both hands, held, and brought down like a falling
# root (a brute's overhead blow).
species("ironroot_warden", plan="person.brute", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=70, role="trial", element="earth", page=None, drops=[],
                  attacks=[("root_staff", 0.5, 90, 1.2, dict(depth=36, knockback=80)), ("iron_root_stomp", 0.9, 160, 1.3, dict(depth=70, both_sides=True))],
                  ai="duelist",
                  art=person("Ironroot Warden", hair="short_knot", hair_color=4, shirt="sleeveless", pants="martial", shoes="boots", weapon="staff",
                             hat="headband", shirt_dye="earth", pants_dye="earth"),
                  race="human", width=20, height=92, spar=True))
