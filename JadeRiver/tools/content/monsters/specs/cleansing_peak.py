"""Cleansing Peak's foes (chapter 4, up the Pilgrim Stairs past Crane Falls): the stone guardians of the stairs (the quest
`toward_cleansing_peak`)."""
from content.monsters import species

# A squat carved temple lion-dog statue come alive: warm temple stone with moss on its shoulders, a mane of spiral curls,
# bulging glowing jade eyes and a wide grin of fangs, a carved collar with a stone bell, a flame-curl tail. It hauls both
# fists up over its head as its cracks light up jade (the tell, held), slams them down before it in dust, and comes apart
# into a heap of blocks when beaten.
species("stone_guardian", plan="humanoid.guardian", share=True, size=1.85,
        palette=["sg_stone", "sg_stone_dark", "sg_moss", "sg_mouth"], elite=False, shadow=(13, 4), cycle=11.0, view=True,
        data=dict(level=(17, 19), role="normal", element="earth", page="road", drops=[("guardian_stone", 0.25), ("mountain_seal", 0.02)],
                  attacks=[("fist_slam", 0.6, 70, 1.3, dict(depth=36, knockback=60))], ai="slow_melee", speed=45, width=28, height=60,
                  knockback_immune=True),
        sound=dict(body="wood"))
