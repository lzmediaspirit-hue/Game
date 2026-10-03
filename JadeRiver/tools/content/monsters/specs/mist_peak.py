"""Mist Peak's foes (M2; the Misty Slopes, the Forgotten Monastery and the Ascension Gate, levels 46-63): the mist wolves,
the mirror wisps and the rogue mirror adept of the slopes, the weeping lanterns and jade sentinels of the monastery, and
the gate guardian.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline."""
from content.monsters import person, species

# M2. A pale blue-grey spirit wolf of the Misty Slopes (it hunts hidden in the fog, in packs): a darker saddle, a pale
# chest and belly, a ruff of hackles down its nape, violet soul-glow eyes, its bushy tail fraying into mist. It crouches
# with its hackles raised (the tell, held) and lunges to bite; beaten, it curls up and comes apart into mist.
species("mist_wolf", plan="quadruped.canine", share=True, size=2.2,
        parts=dict(Z=7.4, body=[{"at": ((3.0, 0.3), 0.7), "r": ((3.4, 0.0, 0.0), (2.6, 0.5, 0.0), (3.1, 0.0, 0.0))},
                                {"at": ((-0.6, 1.2), 0.9), "r": ((4.4, -2.0, 0.0), (2.3, 0.3, 0.2), (2.2, -0.3, 0.0))},
                                {"at": ((-4.0, 2.6), (0.6, -0.6, 0.0)), "r": ((2.8, -0.6, 0.0), (2.4, 0.0, 0.5), (2.5, -0.4, 0.3))}],
                   coat=dict(kind="saddle", chest=(-0.1, 1.2), belly=-0.5, saddle=0.3, reach=4.2),
                   crest=dict(kind="hackles", n=7, step=1.0, length=1.7, r=0.5, **{"from": 4.6}),
                   head=dict(skull=(2.6, 2.4, 2.2), muzzle=((1.2, 0.0, -0.4), (5.2, 0.0, -0.9), 1.5, 0.75), nose=((5.45, 0.0, -0.75), 0.7),
                             jaw=dict(to=(3.7, 0.0, -0.3), r=(1.0, 0.6), teeth=(4.4, 0.55, -1.5), tongue=((2.8, 0.0, -0.2), (1.6, 0.8, 0.35))),
                             ears=dict(base=(-0.6, 1.3, 1.5), tip=(-1.2, 2.0, 4.4), r=(1.2, 0.15), torn=0, tip_dark=False),
                             eyes=dict(at=(1.65, 1.25, 0.5), colour="WOLF_EYE"), mask=(-0.7, 1.6)),
                   legs=dict(fore=(3.0, (1.5, 0.8, 0.3)), hind=(-4.0, (1.6, 0.4, 0.9)), bones=((3.4, 3.3), (3.6, 3.5)),
                             r=((1.2, 0.68), (1.5, 0.68)), paw=(0.9, 0.7, 0.5)),
                   tail=dict(root=(-6.2, 1.6), n=8, length=8.4, r=(0.9, 2.0, 0.6), rest=-4.0, droop=-24.0, tip=0.4, mist=True)),
        mats=dict(coat="wolf_fur", pale="wolf_mist", saddle="wolf_saddle", sock="wolf_paw", ear_in="wolf_mist", tip="wolf_mist",
                  nose="hound_nose", tongue="tongue"),
        motion={"idle": "alert", "walk": "trot", "windup": "crouch", "attack": "pounce_bite", "hurt": "knock_squash",
                "death": ("curl_side", {"dissolve": (0.0, 0.0, 0.1, 0.25, 0.45, 0.65, 0.85, 1.0)})},
        opts=dict(misty=True),
        palette=["wolf_fur", "wolf_saddle", "wolf_paw", "wolf_mist", "hound_nose", "tongue"], accents=("wolf_mist",), shadow=(15, 4),
        cycle=14.0, view=True,
        data=dict(level=(46, 50), role="normal", element="water", page="mist_peak", drops=[("mist_pelt", 0.5)],
                  attacks=[("lunge", 0.4, 50, 1.0, dict(dash=60))], ai="melee", speed=150, pack=True, tameable=True, width=28, height=34,
                  hidden_in_fog=True))

# M2. A floating ring of mirror-bright crystal shards round a single great eye (violet iris, a dark socket ring), a faint
# violet halo. Its shards swing round before the eye into a lens as it glows (the tell, held), and it flashes a bolt of
# soul light; beaten, the eye cracks and everything shatters outward and fades.
species("mirror_wisp", plan="spirit.wisp", share=True, size=2.0,
        palette=["mirror_shard", "mirror_shard_back", "wisp_socket", "wisp_sclera", "wisp_iris", "wisp_pupil"],
        accents=("mirror_shard", "wisp_sclera", "wisp_iris"), shadow=(8, 3), cycle=10.0, view=True,
        data=dict(level=(47, 51), role="normal", element="soul", page="mist_peak", drops=[("mirror_dust", 0.5), ("soul_core_high", 0.02)],
                  attacks=[("soul_flash", 0.6, 240, 1.1, dict(damage_type="soul", projectile={"speed": 500, "art": "soul_bolt"}))],
                  ai="flyer_ranged", speed=70, flying=True, width=18, height=30),
        sound=dict(body="shell"))

# M2. A haunted paper lantern of the Forgotten Monastery, lit from inside by a violet soul flame, a sad face painted on its
# paper, crying wax tears, a dark red cap and a red tassel. Its flame flares up out of its top (the tell, held) and it
# throws a ring of soul fire round it (its blow strikes on both sides and may confuse); beaten, its paper crumples and
# it drops. The monastery's elite lantern carries the valley's Heavenly Flame.
species("weeping_lantern", plan="spirit.lantern", share=True, size=2.9,
        palette=["lantern_paper", "lantern_cap", "lantern_tassel", "wax"], accents=("lantern_paper",), shadow=(7, 3), cycle=10.0, view=True,
        data=dict(level=(50, 55), role="normal", element="soul", page="mist_peak",
                  drops=[("lantern_wick", 0.4), ("soul_wax", 0.4), ("soul_core_high", 0.03)],
                  attacks=[("flare", 0.7, 90, 1.0, dict(damage_type="soul", depth=50, both_sides=True,
                                                        status={"id": "confusion", "chance": 0.3, "power": 1, "duration_s": 2}))],
                  ai="flyer", speed=50, flying=True, width=18, height=44,
                  elite_first_defeat=["mist_lantern_flame"]),   # the valley's Heavenly Flame (Part 8): the monastery's elite lantern carries it
        sound=dict(body="wood"))
