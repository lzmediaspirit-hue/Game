"""Whitewater Gorge's foes (chapter 6, west of Deepwater Bend): the gorge's bandit adepts; M2: the rapids lizards of the
Rapids Terraces, the boulder serpents and mist vultures of the Echo Cliffs.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline."""
from content.monsters import person, species

# M2. A long, sleek blue-green water lizard (the Rapids Terraces) low on sprawling legs, dark crossbands over its back, a
# pale belly, a webbed crest down its back and along its long tail, a cheek fin. It raises its tail and curls it over its
# back, the crest and fins flared, hissing (the tell, held), and whirls round so its tail lashes out before it (the blow
# strikes on both sides); beaten, it flips onto its back.
species("rapids_lizard", plan="quadruped.saurian", share=True, size=1.85,
        palette=["rl_skin", "rl_belly", "rl_fin", "rl_mouth"], accents=("rl_fin",), shadow=(14, 4), cycle=11.0, view=True,
        data=dict(level=(28, 31), role="normal", element="water", page="gorge", drops=[("lizard_scale", 0.5), ("pearl", 0.1)],
                  attacks=[("tail_whip", 0.4, 60, 1.0, dict(both_sides=True))], ai="melee", speed=130, width=26, height=22))

# A gorge bandit adept: a long tied tail of hair, the cloud tunic, folded boots, a jian; it cuts, and throws a crescent of
# Qi (the same tell: the sword drawn back in a crouch).
species("gorge_bandit_adept", plan="person.fighter", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=(29, 33), role="normal", element="none", page="gorge", drops=[("cloth", 0.4), ("manual_page", 0.06), ("manual_ember_burst", 0.03)],
                  attacks=[("sword_arc", 0.45, 80, 1.1), ("crescent", 0.6, 300, 1.2, dict(damage_type="qi", projectile={"speed": 520, "art": "qi_arc"}))],
                  ai="humanoid",
                  art=person("Gorge Bandit Adept", hair="long_tied", hair_color=2, shirt="vneck", pants="martial", shoes="folded",
                             weapon="sword", hat="none"),
                  race="human", energy="primal_qi", width=18, height=90, guards=True, coin_mult=2.0, equipment_chance=0.024,
                  faction="gorge"))
