"""The Drowned Shrine's foes (chapter 5, off Deepwater Bend): its drowned acolytes, the rogue cultivator in its grotto,
and the Drowned Abbot (the quest `the_drowned_abbot`).

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline; the drowned in the river's pallor (`tint`)."""
from content.monsters import person, species

# A drowned acolyte: a scholar's coat and trousers, slippers, a staff, pale and blue-grey with the river. It thrusts with
# the staff, and chants (its bell buffs its kin: the same tell).
species("drowned_acolyte", plan="person.fighter", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=(21, 25), role="normal", element="water", page="shrine", drops=[("prayer_beads", 0.4), ("manual_page", 0.04)],
                  attacks=[("staff_strike", 0.45, 80, 1.0), ("bell_chant", 0.8, 0, 0.0, dict(buff_allies=0.15))], ai="caster",
                  art=person("Drowned Acolyte", hair="short_knot", hair_color=1, shirt="scholar", pants="scholar", shoes="slippers",
                             weapon="staff", hat="none", tint="#9fc6c9"),
                  race="human", energy="primal_qi", width=18, height=90))

# A floating spirit made of layered, yellowed paper talismans (the Hall of Lanterns, the Scripture Well): a hooded dome of
# wrapped strips, a dark face under it with two eyes glowing violet and a talisman hanging over it (a red seal, red
# script), strips of paper hanging and fluttering, red script down each, a bundle of strips at each side. It fans its
# bundles out behind it like a peacock (the tell) and flings a talisman.
species("paper_talisman_ghost", plan="spirit.talisman", share=True, size=2.8,
        palette=["talisman", "talisman_old", "cinnabar", "soul_void"], accents=("cinnabar", "soul_void"), elite=False, shadow=(6, 3),
        cycle=10.0, view=True,
        data=dict(level=(22, 26), role="normal", element="soul", page="shrine", drops=[("talisman_paper", 0.5), ("ink", 0.3)],
                  attacks=[("talisman_throw", 0.5, 300, 1.0, dict(damage_type="soul", projectile={"speed": 400, "art": "talisman"}))],
                  ai="flyer_ranged", speed=70, flying=True, width=20, height=40, phases_walls=True),
        sound=dict(body="wood"))

# S47 rogue cultivators: what they carry in the open is what they drop. A long fall of hair, the cloud tunic, a jian; its
# tell is the sword drawn back in a crouch.
species("rogue_cultivator", plan="person.fighter", share=True, size=1.0, shadow=(8, 3), cycle=12.0,
        data=dict(level=(24, 26), role="elite", element="metal", page=None, drops=[("serpent_tongue_jian", 1.0), ("sealed_storage_pouch", 1.0)],
                  attacks=[("serpent_thrust", 0.45, 90, 1.25),
                           ("sword_qi", 0.7, 320, 1.15, dict(damage_type="qi", projectile={"speed": 540, "art": "qi_arc"}))],
                  ai="humanoid",
                  art=person("Rogue Cultivator", hair="flowing", hair_color=1, shirt="vneck", pants="martial", shoes="boots", weapon="sword",
                             hat="none"),
                  race="human", energy="primal_qi", width=18, height=90, guards=True))

# The Drowned Abbot, the shrine's boss (M2: sculpted, a boss of his own build, not the shared figure body his acolytes are
# cast in): tall and gaunt and stooped, pale with the river, a waterlogged robe to the floor with weed hanging off its hem
# and wide sleeves, a faded kasaya across it, long white hair loose from under a wide conical straw hat dripping, eyes
# glowing cold under its brim, prayer beads round his neck; a monk's ringed staff with a drowned bronze bell hung under
# its loop. His tell is the staff raised high in his right hand, its bell over his hat, his left hand raised in prayer (held),
# struck down on the floor in both hands as the bell tolls its shockwave round him (and the same tell calls his ghosts);
# beaten, he collapses into a heap of wet robes.
species("drowned_abbot", plan="humanoid.abbot", share=True, size=2.3, elite=False, shadow=(11, 4), cycle=11.0, view=True,
        palette=["drowned_skin", "abbot_hair", "abbot_robe", "abbot_kasaya", "abbot_hat", "abbot_dark", "abbot_bell", "abbot_patina", "weed",
                 "halberd_shaft", "maw"],
        data=dict(level=27, role="dungeon_boss", element="water", page=None, drops=[("riverbreath_scroll", 1.0)],
                  attacks=[("bell_shockwave", 0.7, 180, 1.2, dict(depth=70, both_sides=True, knockback=80)),
                           ("summon_ghosts", 1.2, 0, 0.0, dict(summon="paper_talisman_ghost"))], ai="boss_abbot",
                  art=person("Drowned Abbot", hair="flowing", hair_color=1, shirt="scholar", pants="scholar", shoes="slippers", weapon="staff",
                             hat="none", tint="#8fb7c2"),
                  race="human", energy="primal_qi", width=22, height=96,
                  phases=[{"below": 0.66, "action": "flood"}, {"below": 0.33, "action": "summon"}],
                  first_defeat=["bronze_bell", "shattered_moon_blade", "drowned_robe"]))
