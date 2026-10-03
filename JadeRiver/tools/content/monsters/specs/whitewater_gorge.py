"""Whitewater Gorge's foes (chapter 6, west of Deepwater Bend): the gorge's bandit adepts.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline."""
from content.monsters import person, species

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
