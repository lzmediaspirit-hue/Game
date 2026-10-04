"""The Crane Cliffs' foes (M2; the Cliff Faces and the Sky Ledges, levels 37-45): the cloudwing cranes and stormwing hawks
on the wing, and the cliff apes of the ledges."""
from content.monsters import species

# M2. An elegant white spirit crane in flight, its neck stretched out ahead and its legs trailing, a slate face, a red
# crown, a long gold beak, its wing tips curling into pale blue cloud. It rises with both wings high and draws its neck
# back into an S (the tell, held), and swoops to peck; beaten, it folds and falls.
species("cloudwing_crane", plan="bird.crane", share=True, size=1.9,
        palette=["crane_plume", "crane_flight", "cloud_tip", "crane_slate", "crane_beak", "crane_crown"], accents=("crane_crown", "cloud_tip"),
        shadow=(10, 3), cycle=14.0, view=True,
        data=dict(level=(37, 40), role="normal", element="wind", page="cliffs", drops=[("cloud_feather", 0.5)],
                  attacks=[("swoop", 0.5, 60, 1.0, dict(dash=120))], ai="flyer", speed=110, flying=True, width=26, height=50))

# M2. A dark blue storm hawk, a pale barred breast, a zig-zag of lightning gold across each wing, a banded fan tail, a
# hooked beak over a yellow cere, a fierce yellow eye. It mantles its wings forward over its body while sparks crackle
# round it (the tell, held), and dives talons first in a crack of lightning; beaten, it folds and falls.
species("stormwing_hawk", plan="bird.hawk", share=True, size=1.45,
        palette=["hawk_body", "hawk_covert", "hawk_flight", "hawk_breast", "hawk_bolt", "hawk_beak", "hawk_cere"], accents=("hawk_bolt", "hawk_cere"),
        shadow=(8, 3), cycle=14.0, view=True,
        data=dict(level=(38, 43), role="normal", element="thunder", page="cliffs", drops=[("storm_feather", 0.5)],
                  attacks=[("lightning_dive", 0.55, 60, 1.2, dict(dash=140, status={"id": "shock", "chance": 0.3, "power": 0.2, "duration_s": 3}))],
                  ai="flyer", speed=140, flying=True, width=22, height=34,
                  pet_book={"item": "pet_book_thunder_roar", "chance": 0.25, "elite_only": True}))   # S46: only the elite

# M2. A big grey-brown mountain ape of the Sky Ledges, hunched on its knuckles, a shaggy white mane over its shoulders and
# crown, a dark leathery face under a heavy brow, amber eyes. It stands up roaring and hoists a boulder over its head (the
# tell, held: its smash's and its throw's), and smashes it down before it; beaten, it topples over backwards.
species("cliff_ape", plan="humanoid.ape", share=True, size=2.5,
        palette=["ape_fur", "ape_mane", "ape_skin", "ape_face", "maw", "boulder", "boulder_moss"], elite=False, shadow=(14, 4), cycle=12.0, view=True,
        data=dict(level=(41, 45), role="normal", element="earth", page="cliffs", drops=[("ape_fur", 0.5), ("cloudtop_orchid", 0.05)],
                  attacks=[("smash", 0.5, 60, 1.2), ("boulder_throw", 0.7, 320, 1.3, dict(projectile={"speed": 360, "art": "boulder"}))],
                  ai="humanoid", speed=90, width=28, height=56))
