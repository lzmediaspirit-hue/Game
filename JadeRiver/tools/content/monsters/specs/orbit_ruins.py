"""The Orbit Ruins' foes (M4; the Tumbling Stair, the Orbit Garden, the Golem Foundry and the Inverted Hall, levels
88-93): the orbit moths and the gravity golems."""
from content.monsters import species

# M4. A large soft moth whose wings are a map of the night sky: dusky indigo wings with a rose fringe, a star chart of
# pale-gold stars joined by gold lines and a bright star on each forewing, a fuzzy pale body, feathered gold antennae,
# big dark eyes, three teal-white motes orbiting it. Its wings lift and spread wide as the motes gather into a glowing
# knot before its head (the tell, held: its dust veil's too), and they snap down in a burst of star dust; beaten, it
# folds its wings and spirals down as its motes wink out.
species("orbit_moth", plan="insect.moth", share=True, size=2.6,
        palette=["om_wing", "om_fringe", "om_fur", "om_antenna", "om_eye"], accents=("om_fringe",), gold=("om_eye",), shadow=(9, 3), cycle=11.0,
        view=True,
        data=dict(level=(88, 93), role="normal", element="star", page="lantern", drops=[("moth_dust", 0.5), ("star_shard", 0.5, (1, 2))],
                  attacks=[("orbiting_motes", 0.7, 240, 1.1, dict(damage_type="qi", projectile={"speed": 300, "art": "qi_arc", "count": 2})),
                           ("dust_veil", 0.9, 120, 0.9, dict(depth=60, status={"id": "confusion", "chance": 0.35, "power": 1.0, "duration_s": 2}))],
                  ai="flyer_ranged", speed=90, flying=True, width=30, height=34, tameable=True))

# M4. A construct of dark basalt blocks held together by gravity alone: each part of its body a separate chamfered block
# floating apart from its neighbours, an indigo ripple of gravity in the gaps, a hunched faceless head with a visor
# groove, a violet singularity for an eye in its chest, a ring of pale stones orbiting it. It hauls both arms overhead as
# the singularity swells and draws dark lines and pebbles into it (the tell, held: its gravity well's too) and slams both
# fists down, a shockwave racing out along the ground; beaten, gravity fails and its blocks drop into a heap.
species("gravity_golem", plan="humanoid.golem", share=True, size=3.0,
        palette=["grav_basalt", "grav_ring", "grav_sing"], accents=("grav_sing",), shadow=(16, 5), cycle=12.0, view=True,
        data=dict(level=(88, 93), role="normal", element="earth", page="lantern",
                  drops=[("gravity_core", 0.4), ("star_shard", 0.6, (1, 3)), ("orbit_stone_chip", 0.35)],
                  attacks=[("gravity_well", 1.0, 260, 0.6, dict(depth=90, damage_type="qi", pull=150, both_sides=True)),
                           ("orbit_slam", 1.1, 130, 1.6, dict(depth=70, knockback=140, status={"id": "stun", "chance": 0.3, "power": 1.0, "duration_s": 0.8}))],
                  ai="slow_melee", speed=55, width=70, height=110, knockback_immune=True),
        sound=dict(body="shell"))
