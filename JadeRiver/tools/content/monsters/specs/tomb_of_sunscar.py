"""The Tomb of Sunscar's foes (M3; Act II, the Azure Expanse: the Sealed Gate, the Hall of Sand Kings, the Mirror Crypt and
the Throne, level 77): the terracotta wardens and the Tomb King."""
from content.monsters import species

# M3. A life-size fired-clay tomb soldier woken by the sand Qi of the Tomb of Sunscar, a slow, heavy guard: a lamellar
# vest of clay plates laced in faded vermilion, a malachite-green collar, a vermilion sash, a knee-length skirt of clay
# panels, puttees wound round its shins, its hair combed into a corded knot, a calm sculpted face with a moustache and
# fine cracks, molten amber eyes; sand trickling from the cracks at its knees and elbows; a ge (a bronze dagger-axe on
# a lacquered shaft, its blade bloomed with verdigris). It hauls the ge up over its head in both hands as its eyes
# flare (the tell, held) and chops it down before it, the blade biting the ground in sand; beaten, it breaks apart into
# shards and sand, its ge beside it.
species("terracotta_warden", plan="humanoid.sentinel", share=True, size=2.5, elite=False,
        parts=dict(paint=dict(kind="clay", vest=(3.2, 7.0), rows=0.9, collar=0.8, hem=(1.2, 2.0), puttee=-4.2),
                   face=dict(kind="human", eyes=(1.9, 0.62, 0.25), brow=(0.32, 0.55, 0.2), brow_tilt=-8.0, nose=(2.1, 0.0, -0.2),
                             mouth=(1.9, 0.45, -0.85), ears=(-0.1, 1.85, 0.0), beard="moustache", hair="topknot", glow="amber"),
                   armor=dict(runes=(), tassets=7, tasset=(1.2, 0.3, 2.2)),
                   held=dict(kind="ge", shaft=(6.0, 4.2), r=0.38),
                   trickle="sand"),
        mats=dict(body="tw_clay", limb="tw_clay", dark="tw_clay_dark", joint="tw_clay_dark", neck="tw_clay", trim="tw_vermilion",
                  plate="tw_plate", lace="tw_vermilion", collar="tw_malachite", shaft="tw_shaft", blade="tw_verdigris", sand="tw_sand",
                  hair="tw_clay_dark", skin="tw_clay", cord="tw_vermilion", maw="maw"),
        motion={"idle": "pole_rest", "walk": "pole_march", "windup": "ge_raise", "attack": "ge_chop", "hurt": "pole_rock",
                "death": "pole_crumble"},
        palette=["tw_clay", "tw_clay_dark", "tw_plate", "tw_vermilion", "tw_malachite", "tw_shaft", "tw_verdigris", "tw_sand", "maw"],
        shadow=(11, 4), cycle=12.0, view=True,
        data=dict(level=77, role="normal", element="earth", page="azure",
                  drops=[("terracotta_shard", 0.5), ("storm_shard", 0.5, (1, 2)), ("soul_core_peak", 0.03)],
                  attacks=[("ge_chop", 0.8, 96, 1.3, dict(depth=36, knockback=90))],
                  ai="slow_melee", speed=70, width=22, height=100, race="construct"),
        sound=dict(body="wood"))
