"""The Trial of Reflections' foe (M3; the heart trial at Heart Tempering 9, level 36, and the weekly Mirror Rite): the
Reflection.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in an outfit,
cast by the character's own pipeline."""
from content.monsters import species

# M3. The Reflection (the heart trial's story boss: "Everything you did not do, I did"): the cultivator's own double in
# pale mirror light. Its row wears the player's own avatar, which the side view draws in the player's clothes under a
# cold pale tint; a sheet is drawn once, so it is cast in the clothes a disciple starts in (Wardrobe.defaults: a topknot,
# the cardigan, loose trousers, boots, a sword) under that tint, faded as the side view's is and ringed in cold mirror
# light (`aura` "mirror"). It is your size. Its tell is your own sword drawn back in a crouch, and it cuts as you do.
species("the_reflection", plan="person.fighter", share=True, size=1.0, elite=False, aura="mirror", shadow=(8, 3), cycle=12.0,
        parts=dict(outfit=dict(hair="topknot", hair_color=0, shirt="cardigan", pants="loose", shoes="boots", weapon="sword",
                               pale=0.65, tint="#c4dcffe8", name="The Reflection", body="light")),
        data=dict(level=36, role="story_boss", element="none", page=None, drops=[], attacks=[("mirror_strike", 0.45, 70, 1.0)],
                  ai="reflection", art={"avatar": "player"}, race="human", energy="primal_qi", width=18, height=90,
                  # P1: at half health the Reflection calls up a heart demon; at a quarter it fights as you would, desperately.
                  phases=[{"below": 0.5, "action": "summon", "summon": "heart_demon", "summon_level": 36},
                          {"below": 0.25, "action": "enrage", "cooldown": 0.75, "damage": 1.2}]))
