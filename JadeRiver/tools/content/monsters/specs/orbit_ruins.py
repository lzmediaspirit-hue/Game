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
