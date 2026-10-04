"""Rimefrost Heights' foes (M3; Act II, the Azure Expanse: the Frostpine Climb, the Snow Ape Ledges and the Rimefrost
Summit, levels 67-72): the frost lynxes and the snow apes."""
from content.monsters import species

# M3. A big pale mountain lynx rimed with ice (they hunt in packs): pale blue-white fur with faint blue-grey rosettes, a
# cream throat and belly, high haunches on long hind legs and big paws, a round head with a short muzzle, tall ears
# ending in dark tufts, a rimed cheek ruff framing its face, glowing ice-blue eyes, ice crystals grown on its shoulders,
# a short dark-tipped bob of a tail. It sinks into a pounce crouch, ears flat, frost breath gathering at its muzzle (the
# tell, held), and pounces with its claws out; beaten, it curls up on its side and fades into frost.
species("frost_lynx", plan="quadruped.canine", share=True, size=1.9,
        parts=dict(Z=6.6, body=[{"at": ((2.6, 0.3), 0.6), "r": ((2.8, 0.0, 0.0), (2.5, 0.5, 0.0), (2.9, 0.0, 0.0))},
                                {"at": ((-0.5, 1.1), 0.8), "r": ((3.2, -1.4, 0.0), (2.3, 0.3, 0.2), (2.3, -0.3, 0.0))},
                                {"at": ((-3.2, 2.2), (1.3, -0.6, 0.0)), "r": ((2.6, -0.5, 0.0), (2.5, 0.0, 0.5), (2.7, -0.4, 0.3))}],
                   coat=dict(kind="rosettes", chest=(-0.1, 1.0), belly=-0.5, spots=0.75),
                   crest=dict(kind="ice", shards=((2.8, 1.2, 1.5, 0.4), (2.0, -1.4, 1.3, 0.6), (3.5, 0.0, 1.1, 0.3), (1.2, 0.9, 1.0, 0.5))),
                   head=dict(skull=(2.75, 2.65, 2.4), muzzle=((1.0, 0.0, -0.45), (3.2, 0.0, -0.9), 1.4, 0.85), nose=((3.95, 0.0, -0.8), 0.6),
                             jaw=dict(at=(0.8, 0.0, -1.1), to=(2.4, 0.0, -0.3), r=(0.85, 0.5), teeth=(2.8, 0.45, -1.3),
                                      tongue=((2.0, 0.0, -0.2), (1.2, 0.6, 0.3))),
                             ears=dict(base=(-0.5, 1.5, 1.5), tip=(-0.9, 1.8, 4.3), r=(1.3, 0.18), spread=(0.25, 0.45), back=2.6, torn=0,
                                       tip_dark=False, tuft=1.1),
                             eyes=dict(at=(2.05, 1.6, 0.6), colour="LYNX_EYE", rim="INKY"), mask=(-0.45, 0.5), ruff=((-0.2, 1.9, -0.6), (1.1, 0.5, 0.9))),
                   legs=dict(fore=(2.7, (1.4, 0.8, 0.3)), hind=(-3.4, (1.5, 0.4, 0.9)), bones=((3.2, 3.1), (3.9, 3.8)),
                             r=((1.15, 0.7), (1.5, 0.7)), paw=(1.05, 0.85, 0.55)),
                   tail=dict(root=(-5.4, 2.2), n=4, length=2.8, r=(0.9, 1.15, 0.7), rest=-14.0, droop=-24.0, tip=0.35, flame=False)),
        mats=dict(coat="fl_fur", pale="fl_belly", sock="fl_fur", ear_in="fl_rime", tip="fl_tip", nose="hound_nose", tongue="tongue",
                  spot="fl_spot", tuft="fl_tip", ruff="fl_rime", ice="fl_ice"),
        motion={"idle": "alert", "walk": "trot", "windup": ("crouch", {"breath": (1, 2, 3)}), "attack": "pounce_bite", "hurt": "knock_squash",
                "death": ("curl_side", {"dissolve": (0.0, 0.0, 0.0, 0.1, 0.25, 0.45, 0.65, 0.85)})},
        opts=dict(misty=True),
        palette=["fl_fur", "fl_belly", "fl_spot", "fl_tip", "fl_ice", "fl_rime", "hound_nose", "tongue"], accents=("fl_ice",), shadow=(12, 4),
        cycle=12.0, view=True,
        data=dict(level=(67, 70), role="normal", element="water", page="azure", drops=[("rime_fang", 0.4), ("storm_shard", 0.45), ("frost_lotus", 0.08)],
                  attacks=[("rime_pounce", 0.45, 70, 1.15, dict(dash=120, status={"id": "slow", "chance": 0.35, "power": 0.3, "duration_s": 3}))],
                  ai="leaper", speed=160, pack=True, width=30, height=34, tameable=False))

# M3. A huge white-furred mountain ape of the Snow Ape Ledges, a heavy brute: the cliff ape's body grown bulkier and
# shaggier, a deeper chest, a thick cape of long white locks over its shoulders and back, a fringe under its belly and
# rump, long forearm fur crusted with frost clumps and icicles; snow-white fur shaded cool, a slate leathery face under a
# heavy brow, two small tusks, frost-blue glowing eyes, slate hands and feet. It rears up roaring and heaves a great block
# of ice over its head, a glint flashing on it (the tell, held: its slam's and its ice throw's), and slams it down
# before it, the ice shattering in shards and snow; beaten, it topples onto its back.
species("snow_ape", plan="humanoid.ape", share=True, size=2.5,
        parts=dict(trunk=[{"at": (0.0, 0.0, 1.0), "r": (3.1, 3.5, 2.6), "paint": True}, {"at": (0.7, 0.0, 3.9), "r": (3.7, 4.3, 3.4), "paint": True},
                          {"at": (0.9, 0.0, 6.8), "r": (3.4, 5.1, 3.1), "paint": True}],
                   face=dict(glow="SA_EYE", tusks=(3.45, 0.6, -2.05)),
                   held=dict(kind="block", r=3.0),
                   shag=dict(cape=11, r=(3.0, 4.6), z=6.8, length=3.4, w=0.9, fringe=9, belly=(2.7, 3.3, 1.0))),
        mats=dict(body="sa_fur", limb="sa_fur", dark="sa_skin", joint="sa_fur", neck="sa_fur", pale="sa_skin", belly="sa_fur", mantle="sa_snow",
                  ice="sa_ice", snow="sa_snow", tusk="sa_tusk", maw="maw"),
        palette=["sa_fur", "sa_skin", "sa_ice", "sa_snow", "sa_tusk", "maw"], accents=("sa_ice",), shadow=(13, 4), cycle=12.0, view=True,
        data=dict(level=(68, 72), role="normal", element="earth", page="azure", drops=[("snow_ape_hide", 0.45), ("storm_shard", 0.5, (1, 2)),
                                                                                     ("tough_meat", 0.3)],
                  attacks=[("ice_slam", 0.8, 90, 1.45, dict(depth=40, knockback=100,
                                                            status={"id": "freeze", "chance": 0.15, "power": 1.0, "duration_s": 1.5})),
                           ("ice_throw", 0.9, 280, 1.1, dict(projectile={"speed": 420, "art": "ice_shard"}))],
                  ai="slow_melee", speed=80, width=36, height=60))
