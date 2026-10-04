"""The creatures that are not foes (M5): the pets', the mount's and the Copperjaw swarm's. pets.json names a pet's sheet
and its mount's by their `art`, stats.swarm the swarm's and its Queen's; none has an enemies.json row. A spec with no
`data` is drawn alone: its sheets and its foes.json block, no row, loot table or voice. None has an elite (no room makes
one), and each is near its side-view sheet's share of a person.

Their walks are timed for a pet's pace: the room view plays a sheet's walk at its own rate (creatures.rates), which for a
species with no row is the engine's default pace, so each one's `cycle` sets its walk to the rate it wants beside you."""
from content.monsters import species

# M5. The Copperjaw swarm (v1.2 Phase D: the beetle swarm's tab on the Spirit Animals page, its release): a cloud of
# eleven small copper beetles of three sizes over the floor, copper wing cases with a dark seam and a darker pronotum, dark
# chitin heads, pale-gold jaws, their cases flicking open and shut so the cloud buzzes. It hangs, each beetle rounding its
# own loop; it streams forward on the wing (the tab's stage); in its tell it balls up, jaws open, as a copper ring tightens
# round it (held), and lances forward as a spearhead to bite; struck, it scatters; beaten, the beetles rain down onto
# their backs, legs in the air, and fade.
species("copperjaw_swarm", plan="insect.swarm", share=True, elite=False, size=2.2,
        palette=["cj_copper", "cj_chitin", "cj_wing"], shadow=(10, 3), cycle=9.0, view=True)

# M5. The Copperjaw swarm once a Queen has risen in the box (its tab's stage and its release draw this sheet then): the
# same cloud with a large gold-cased Queen at its heart, a pale-gold crown on her, leading its lance and falling with the
# rest.
species("copperjaw_queen", plan="insect.swarm", parts=dict(queen=True), share=True, elite=False, size=2.2,
        palette=["cj_copper", "cj_chitin", "cj_wing", "cj_queen"], shadow=(11, 3), cycle=9.0, view=True)

# M5. A young star wyrm, the player's Primordial Beast (the star-wyrm egg's hatchling): a baby dragonet, endearing and
# noble, pearl-scaled over a blue-violet belly, a big round head on a curved neck, big star-blue eyes, a gold star on its
# brow and gold horns, stub wings webbed in indigo flecked with stars, a tail curling up to a small glowing star. It looks
# about as it breathes and waddles beside you; in its tell it puffs up and rears its head back, its wing stubs flared and
# its chest glowing (held), and breathes a burst of stars; struck, it squeaks; knocked out, it curls up asleep, its lights
# dimmed.
species("hatchling_wyrm", plan="quadruped.hatchling", share=True, elite=False, size=1.8,
        palette=["hatch_pearl", "hatch_belly", "hatch_gold", "hatch_membrane", "hatch_mouth"], shadow=(9, 3), cycle=9.0, view=True)

# M5. The cloud stag, a mount-only spirit stag (the Beast Tide's egg): the stag's frame, cloud-white shaded sky blue with
# faint dapples, calm dark eyes, whole branching antlers with small clouds caught on them, soft cloud wisps trailing off
# its back and clouds under its hooves. Thrown from its saddle by a heavy blow, it lands and walks beside you until you
# mount again; in a fight it rears onto its hind legs as clouds gather under its forehooves (held), and stamps
# down in a ring of cloud and wind; knocked out, its legs fold and it comes apart into cloud. (Its rider's pose and the
# riding sheet are on hold: this is the creature's own sheet.)
species("cloud_stag", plan="quadruped.cervid", share=True, elite=False, size=2.2,
        parts=dict(coat=dict(kind="cloud", belly=-0.45, dapple=0.84),
                   crest=dict(kind="clouds"),
                   head=dict(eyes=dict(colour="INKY"), mist=False, antlers=dict(broken=(), clouds=(1,))),
                   legs=dict(stance=(3.8, -5.0, 2.5, 2.7, 2.0, 2.2))),
        mats=dict(hide="cstag_hide", head="cstag_hide", stripe="cstag_hide", coat="cstag_hide", antler="cstag_antler", pale="cstag_hide",
                  hoof="cstag_hoof", cloud="cstag_cloud"),
        motion={"idle": "alert", "walk": "trot", "windup": "rear_cloud", "attack": "cloud_stamp", "hurt": "stumble", "death": "buckle_roll"},
        opts=dict(hollowed=False, misty=True),
        palette=["cstag_hide", "cstag_antler", "cstag_hoof", "cstag_cloud"], shadow=(14, 4), cycle=6.5, view=True)
