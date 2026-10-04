"""Mirrorwater Lake's foes (M3; Act II, the Azure Expanse: the Reedless Shore, the Mirror Shallows, the Sentinel Causeway
and Toad's Hollow, levels 68-75): the azure carp dragonets, the river sentinels and the Thousand-Eye Toad."""
from content.monsters import species

# M3. A carp halfway through the Dragon Gate, swimming through the air over Mirrorwater (in legend a carp that leaps the
# gate becomes a dragon): a deep azure carp's body with a silver-white belly, gold-tipped fins and a fish's forked tail,
# its front stretched into a slender rising neck carrying a small dragon head (two short gold antler horns, long gold
# whiskers flowing back, a gold fin mane down its neck, a glowing pearl eye), over a faint turning ring of water, dripping
# from its tail. It coils its neck back, jaws open, as a water orb gathers before them (the tell, held), and lunges and
# spits it in a burst of water; beaten, it drops nose-first out of the air, flops onto the water and fades.
species("azure_carp_dragonet", plan="fish.dragonet", share=True, size=2.3,
        palette=["acd_scale", "acd_belly", "acd_fin", "acd_gold", "acd_orb", "acd_mouth"], accents=("acd_orb",), shadow=(11, 3),
        cycle=12.0, view=True,
        data=dict(level=(68, 72), role="normal", element="water", page="azure", drops=[("dragonet_scale", 0.45), ("storm_shard", 0.4)],
                  attacks=[("water_orb", 0.7, 300, 1.15, dict(damage_type="qi", projectile={"speed": 380, "art": "water_orb"}))],
                  ai="flyer_ranged", speed=90, flying=True, width=30, height=30),
        sound=dict(body="slime", tell="water"))

# M3. The Thousand-Eye Toad (Toad's Hollow's field boss): a lake spirit-toad that has swallowed centuries of reflections,
# huge and squat: deep lake-blue skin with warts, a pearl belly and throat, its wide mouth and heavy lip under its own
# lidded eyes, and its signature: dozens of round mirror eyes of different sizes over its back and flanks (silver-white,
# dark pupils, a few always half-lidded); a crown of water-lily pads on its head with lotus buds and an open lotus. Its
# throat sac swells huge and every eye on its back opens wide and glows violet (the tell, long and held: its belly
# slam's, its tongue's and its mirror gaze's), and it leaps and belly-slams, a wall of lake water bursting up before it;
# struck, every eye squeezes shut; beaten, its eyes close one by one as it deflates and sinks into the lake.
species("thousand_eye_toad", plan="amphibian.toad", share=True, size=4.2, elite=False, shadow=(30, 9), cycle=10.0, view=True,
        canvas=(204, 156),
        parts=dict(body=[{"at": (0.0, 0.0, 0.0), "r": (7.2, 6.8, 4.1)}, {"at": (5.2, 0.0, 0.4), "r": (4.2, 5.8, 2.8)},
                         {"at": (8.2, 0.0, -0.3), "r": (2.0, 4.2, 1.7), "flat": True, "puff": 0.6}],
                   moss=(), ferns=(),
                   eyes_back=dict(rows=((68.0, 4), (50.0, 6), (32.0, 8), (15.0, 9)), u=(75.0, 285.0), r=(0.55, 1.15)), legs=dict(thick=1.45),
                   crown=dict(pads=((4.4, 1.3, 3.0, 1.5, 12.0), (3.4, -1.2, 3.2, 1.3, -10.0), (2.4, 0.4, 3.6, 1.2, 6.0)),
                              buds=((4.0, 1.9, 3.5), (3.0, -1.8, 3.7), (2.2, 1.2, 3.9)), lotus=(3.6, 0.1, 3.9)),
                   slam_water=True),
        mats=dict(skin="tet_skin", belly="tet_belly", moss="tet_skin", fern="tet_lily", sac="tet_belly", eye="tet_sclera", leg="tet_skin",
                  sclera="tet_sclera", sclera_glow="tet_glow", lily="tet_lily", lotus="tet_lotus", tongue="tongue", maw="maw"),
        motion={"idle": "swell_breathe", "walk": "heavy_hop", "windup": "swell_glare", "attack": "belly_slam", "hurt": "squeeze_shut",
                "death": "sink_close"},
        palette=["tet_skin", "tet_belly", "tet_sclera", "tet_glow", "tet_lily", "tet_lotus", "tongue", "maw"],
        data=dict(level=68, role="field_boss", element="water", page="azure",
                  drops=[("mirror_eye", 1.0), ("storm_shard", 1.0, (6, 10)), ("dragonet_scale", 1.0, (2, 3))],
                  attacks=[("belly_slam", 0.8, 140, 1.4, dict(depth=60, knockback=140, both_sides=True)),
                           ("tongue_lash", 0.6, 240, 1.2, dict(depth=40)),
                           ("mirror_gaze", 1.2, 0, 0.0, dict(summon="azure_carp_dragonet"))],
                  ai="boss_toad", width=80, height=100, respawn_min=45,
                  phases=[{"below": 0.5, "action": "summon"}], first_defeat=["cold_lamp_flame"]),
        sound=dict(body="slime", tell="water"))

# M3. An ancient river-stone guardian statue of the Sentinel Causeway that has stood waist-deep in the lake for centuries:
# blue-grey river stone worn smooth, green algae streaking up from the waterline, barnacles crusted on its legs, a tall
# scholar-general's helmet (a crown board standing off its front, a bronze pin through the knot behind), a carved beard,
# its eye slit glowing pale aquamarine, water trickling from the cracks at its joints; a stone trident. It raises the
# trident high and back as water spirals up its shaft (the tell, held) and drives it down before it into the water in a
# splash; beaten, it crumbles into a heap of river stones, its trident beside it.
species("river_sentinel", plan="humanoid.sentinel", share=True, size=2.8,
        parts=dict(paint=dict(kind="riverstone", rows=1.2, belt=(2.0, 3.2), water=1.0),
                   face=dict(crest=((0.2, 0.0, 2.3), (-1.0, 0.0, 2.5), 0.6), board=((0.95, 0.0, 2.5), (0.35, 1.5, 1.45)),
                             pin=((-0.7, 0.0, 2.3), 1.9), beard=((1.6, 0.0, -1.7), (0.7, 0.95, 1.3)), glow="aqua"),
                   armor=dict(runes=()),
                   held=dict(kind="trident", shaft=(7.0, 3.6), r=0.42),
                   trickle="water"),
        mats=dict(body="rsn_stone", limb="rsn_stone", dark="rsn_stone_dark", joint="rsn_stone_dark", neck="rsn_stone_dark", trim="rsn_bronze",
                  shaft="rsn_stone_dark", blade="rsn_stone", algae="rsn_algae", shell="rsn_shell"),
        motion={"idle": "pole_rest", "walk": "pole_march", "windup": "trident_raise", "attack": "trident_drive", "hurt": "pole_rock",
                "death": "pole_crumble"},
        palette=["rsn_stone", "rsn_stone_dark", "rsn_algae", "rsn_bronze", "rsn_shell"], shadow=(12, 4), cycle=12.0, view=True,
        canvas=(156, 150),
        data=dict(level=(70, 75), role="normal", element="water", page="azure", drops=[("sentinel_core", 0.3), ("storm_shard", 0.6, (1, 2))],
                  attacks=[("trident_sweep", 0.85, 110, 1.5, dict(depth=40, knockback=90))],
                  ai="guard_counter", speed=55, width=30, height=70, tameable=False),
        sound=dict(body="wood"))
