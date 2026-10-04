"""The Tidebreak Front's foes (M4; the Greyfall Breach, the Hollow Wake and the Drone Hive, the Tide Battle, the Ashen
Reach's Cinder Fields and the Lantern's halls, levels 88-99): the Hollow's drones."""
from content.monsters import species

# M4. A Hollow construct that hunts in swarms: a smooth spindle of gunmetal in three riveted sections, a long needle lance
# before it, two small vanes at its back, two pairs of pale wings beating too fast to see, a sickly violet core light in
# its middle with ash-white fissures spreading from it, one empty white Hollow eye. It pulls back and levels its lance as
# its core flares in a violet glow (the tell, held: its grey sting's too) and thrusts; beaten, its core bursts and its
# shell comes apart into grey flakes.
species("hollow_drone", plan="insect.drone", share=True, size=2.5,
        palette=["hd_shell", "hd_lance", "hd_wing", "hd_ghost"], accents=("hd_ghost",), shadow=(8, 3), cycle=11.0, view=True,
        data=dict(level=(88, 99), role="normal", element="hollow_metal", page="lantern",
                  drops=[("drone_shell", 0.5), ("hollow_shard", 0.3), ("star_shard", 0.4, (1, 2))],
                  attacks=[("needle_dive", 0.5, 70, 1.15, dict(dash=160)),
                           ("grey_sting", 0.6, 200, 1.0, dict(damage_type="qi", projectile={"speed": 380, "art": "qi_arc"}))],
                  ai="flyer_ranged", speed=130, flying=True, width=26, height=26, hollowing=4))
