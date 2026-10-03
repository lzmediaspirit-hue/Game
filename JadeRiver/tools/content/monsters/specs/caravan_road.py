"""The Caravan Road's foes (chapter 3, east of Stoneford's fairground): the Mudwater bandits who rob the caravans (the
quest `bandits_on_the_road`), met again in their stockade and in Gu's warehouse.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline."""
from content.monsters import person, species

# A Mudwater bandit: a short knot of dark hair under a tied band, the wanderer's sleeveless vest, martial trousers and
# boots, a dagger. Its tell is the dagger drawn back in a crouch; it stabs.
species("mudwater_bandit", plan="person.fighter", share=True, size=1.0, shadow=(8, 3), cycle=12.0,
        data=dict(level=(14, 19), role="normal", element="none", page="road", drops=[("cloth", 0.5), ("rat_tail", 0.0)],
                  attacks=[("slash", 0.4, 60, 1.0), ("qi_strike", 0.55, 90, 1.3, dict(damage_type="qi"))], ai="humanoid",
                  art=person("Mudwater Bandit", hair="short_knot", hair_color=5, shirt="sleeveless", pants="martial", shoes="boots",
                             weapon="dagger", hat="tied"),
                  race="human", energy="primal_qi", speed=100, width=18, height=90, coin_mult=2.0, equipment_chance=0.02,
                  faction="mudwater"))
