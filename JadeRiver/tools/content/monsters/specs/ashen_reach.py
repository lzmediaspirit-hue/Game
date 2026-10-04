"""The Ashen Reach's foes (M4; the Cinder Fields, the Ashborn Palisade, the War Camp and Kharn's Pyre, levels 88-96): the
Ashborn legions, their pyre keepers and General Kharn.

The Ashborn are drawn as the player and the villagers are (plans/person.py), their ash-grey skin the side view's tint.
The general is a person of size, sculpted (humanoid.general)."""
from content.monsters import person, species

# M4. An Ashborn raider: ash-grey skin, a short knot under a headband, a crimson sleeveless vest, ink trousers, boots, a
# spear. Its tell is the spear drawn back in a crouch (its ember sweep's too), and it thrusts.
species("ashborn_raider", plan="person.fighter", share=True, size=1.0, shadow=(8, 3), cycle=12.0,
        data=dict(level=(88, 96), role="normal", element="fire", page="lantern", drops=[("cinder_ash", 0.5), ("star_shard", 0.5, (1, 3))],
                  attacks=[("cinder_slash", 0.45, 90, 1.25, dict(depth=36)),
                           ("ember_sweep", 0.8, 120, 1.1, dict(depth=50, damage_type="qi", ground_fire={"radius": 60, "duration_s": 4, "pct_per_s": 0.02}))],
                  ai="humanoid",
                  art=person("Ashborn Raider", hair="short_knot", hair_color=5, shirt="sleeveless", pants="martial", shoes="boots", weapon="spear",
                             hat="headband", shirt_dye="crimson", pants_dye="ink", tint="#d4b2a4"),
                  race="ashborn", energy="sage_qi", width=18, height=90, faction="ashborn"))

# M4. An Ashborn pyre keeper (an elite of the Palisade and the War Camp, never drawn as one: no room makes it an elite):
# ash-grey skin, a topknot, an ochre coat, ink trousers, boots, a tattered cape, a staff. Its tell is the staff raised over
# its head (its kindling ring's too), and it brings it down.
species("ashborn_pyre_keeper", plan="person.brute", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=(91, 96), role="elite", element="fire", page="lantern",
                  drops=[("cinder_ash", 1.0, (2, 3)), ("pyre_ember", 0.35), ("star_shard", 1.0, (2, 4))],
                  attacks=[("pyre_staff", 0.55, 110, 1.3, dict(depth=40, knockback=80)),
                           ("kindle_ring", 1.1, 60, 0.8, dict(depth=80, both_sides=True, damage_type="qi",
                                                              ground_fire={"radius": 70, "duration_s": 6, "pct_per_s": 0.025, "ring": [-160, 160]}))],
                  ai="humanoid",
                  art=person("Ashborn Pyre Keeper", hair="topknot", hair_color=0, shirt="vneck", pants="martial", shoes="boots", weapon="staff",
                             hat="none", shirt_dye="ochre", pants_dye="ink", cape="tattered", tint="#d4b2a4"),
                  race="ashborn", energy="sage_qi", width=18, height=92, faction="ashborn", hp_mult=1.4, presence=2))
