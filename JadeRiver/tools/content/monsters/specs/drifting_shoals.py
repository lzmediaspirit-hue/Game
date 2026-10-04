"""The Drifting Shoals' foes (M4; the Lantern Star Field's Driftglass Bank, Jellyfish Shallows and Sparrow Reefs, and the
Wyrmnest's Nest Cliffs, levels 82-87): the comet sparrows and the star jellyfish."""
from content.monsters import species

# M4. A small fierce sparrow wreathed in comet fire: russet feathers, dark flight feathers tipped in gold, a white-hot
# breast, a forked tail, a gold beak, a little flame crest, big dark eyes, and a comet's tail of fire streaming behind it
# (gold-white through orange and magenta to violet). It pulls up and back, nose down, as its comet flares (the tell, held)
# and streaks down in a burning dive; beaten, its fire gutters to smoke and it tumbles down.
species("comet_sparrow", plan="bird.sparrow", share=True, size=1.7,
        palette=["cs_feather", "cs_flight", "cs_gold", "cs_breast", "cs_flame_or", "cs_flame_mg", "cs_flame_vi", "cs_smoke"],
        accents=("cs_gold",), glow=("cs_flame_or", "cs_flame_mg", "cs_flame_vi"), shadow=(7, 3), cycle=12.0, view=True,
        data=dict(level=(82, 87), role="normal", element="fire", page="lantern", drops=[("comet_plume", 0.45), ("star_shard", 0.4, (1, 2))],
                  attacks=[("comet_dive", 0.5, 110, 1.3, dict(dash=160, status={"id": "burn", "chance": 0.3, "power": 0.01, "duration_s": 3}))],
                  ai="flyer", speed=160, flying=True, pack=True, width=22, height=22, tameable=True))

# M4. A drifting jellyfish of starlight: a translucent indigo-violet bell with a pale-gold star glowing in it, a magenta frill
# round its rim, two short magenta oral arms and four long pale tentacles with stars twinkling down them. Its bell clenches
# and its star flares as a double ring of star glow opens round it and its tentacles curl up and forward (the tell, held:
# its spark trail's too), and it lashes them forward in a stinging arc; beaten, it deflates and sinks, its star going out.
species("star_jellyfish", plan="spirit.jelly", share=True, size=2.5,
        palette=["sj_bell", "sj_frill", "sj_tentacle"], accents=("sj_frill",), shadow=(9, 3), cycle=10.0, view=True,
        data=dict(level=(82, 87), role="normal", element="star", page="lantern",
                  drops=[("jelly_silk", 0.45), ("star_shard", 0.4, (1, 2)), ("star_lotus", 0.05)],
                  attacks=[("star_sting", 0.6, 90, 1.2, dict(depth=40, status={"id": "confusion", "chance": 0.25, "power": 1.0, "duration_s": 2})),
                           ("spark_trail", 0.8, 260, 1.05, dict(damage_type="qi", projectile={"speed": 320, "art": "qi_arc"}))],
                  ai="flyer_ranged", speed=70, flying=True, width=28, height=40),
        sound=dict(body="slime", tell="water"))
