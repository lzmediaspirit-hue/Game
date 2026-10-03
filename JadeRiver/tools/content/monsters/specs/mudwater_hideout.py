"""The Mudwater Hideout's foes (chapter 3, through the stockade off the Caravan Road): the bandits' mud hounds, their
archers, Lieutenant Kuai and Big Toad Tan (the quest `mudwater_hideout`).

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline."""
from content.monsters import person, species

# A lean bandit hound caked in dried mud, a leather collar with a brass ring, one ear torn; it barks with its head up
# and lunges to bite. The fox's body made longer in the leg and the muzzle, deep in the chest, its tail thin and ragged.
species("mud_hound", plan="quadruped.canine", share=True, size=1.7,
        parts=dict(Z=7.0, body=[{"at": ((2.9, 0.3), 0.6), "r": ((3.2, 0.0, 0.0), (2.4, 0.5, 0.0), (3.0, 0.0, 0.0))},
                                {"at": ((-0.6, 1.2), 0.9), "r": ((4.2, -2.0, 0.0), (2.1, 0.3, 0.2), (2.0, -0.3, 0.0))},
                                {"at": ((-3.9, 2.6), (0.6, -0.6, 0.0)), "r": ((2.7, -0.6, 0.0), (2.3, 0.0, 0.5), (2.4, -0.4, 0.3))}],
                   coat=dict(mud=0.42),
                   head=dict(skull=(2.5, 2.3, 2.1), muzzle=((1.2, 0.0, -0.4), (5.1, 0.0, -0.95), 1.45, 0.75),
                             nose=((5.35, 0.0, -0.8), 0.7), jaw=dict(to=(3.6, 0.0, -0.3), r=(1.0, 0.6), teeth=(4.3, 0.55, -1.55),
                                                                         tongue=((2.8, 0.0, -0.2), (1.6, 0.8, 0.35))),
                             ears=dict(base=(-0.6, 1.3, 1.4), tip=(-1.6, 2.3, 3.6), r=(1.15, 0.2), torn=1, tip_dark=False),
                             eyes=dict(at=(1.6, 1.25, 0.5), colour="HOUND_EYE"), mask=(-0.75, 1.8), collar=0.3),
                   legs=dict(fore=(3.0, (1.5, 0.8, 0.3)), hind=(-4.0, (1.6, 0.4, 0.9)), bones=((3.3, 3.2), (3.5, 3.4)),
                             r=((1.15, 0.65), (1.45, 0.65)), paw=(0.85, 0.66, 0.5)),
                   tail=dict(root=(-6.0, 1.5), n=7, length=7.0, r=(0.75, 0.85, 0.3), rest=-4.0, droop=-36.0, tip=0.0)),
        mats=dict(coat="hound_fur", pale="hound_pale", sock="hound_mud", mud="hound_mud", ear_in="hound_pale", tip="hound_fur",
                  nose="hound_nose", tongue="tongue", collar="collar", ring="brass"),
        motion={"idle": "pant", "windup": "bark", "attack": "pounce_bite", "death": "topple_side"},
        palette=["hound_fur", "hound_pale", "hound_mud", "hound_nose", "tongue", "collar", "brass"], elite=False, shadow=(14, 4),
        cycle=13.0, view=True,
        data=dict(level=(16, 20), role="normal", element="earth", page="road", drops=[("hound_fang", 0.5)], attacks=[("bite", 0.35, 44, 1.0)],
                  ai="melee", speed=130, pack=True, width=22, height=28))

# A Mudwater archer: a low ponytail under a tied band, the sleeveless vest, cuffed trousers, a bow. Its tell is the bow
# raised and drawn, held; the arrow looses on the blow.
species("bandit_archer", plan="person.archer", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=(16, 20), role="normal", element="none", page="road", drops=[("arrows", 0.6), ("bow_parts", 0.3)],
                  attacks=[("arrow", 0.6, 420, 1.0, dict(projectile={"speed": 600, "art": "arrow"}))], ai="ranged",
                  art=person("Bandit Archer", hair="ponytail", hair_color=0, shirt="sleeveless", pants="cuffed", shoes="boots", weapon="bow",
                             hat="tied"),
                  race="human", energy="primal_qi", speed=90, width=18, height=90, keep_distance=260, equipment_chance=0.02,
                  faction="mudwater"))

# Lieutenant Kuai (S49 grudges: he yields at a fifth of his health; spare him or not): the bandits' sword, in an earth
# brown vest and ink trousers, a headband; his tell is the sword drawn back in a crouch, and he cuts.
species("mudwater_lieutenant", plan="person.fighter", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        data=dict(level=19, role="elite", element="none", page=None, drops=[("cloth", 1.0), ("mudwater_manual", 0.3)],
                  attacks=[("slash", 0.4, 64, 1.15), ("mud_cut", 0.6, 100, 1.3, dict(damage_type="qi", knockback=60))], ai="humanoid",
                  art=person("Lieutenant Kuai", hair="short_knot", hair_color=5, shirt="sleeveless", pants="martial", shoes="boots",
                             weapon="sword", hat="headband", shirt_dye="earth", pants_dye="ink"),
                  race="human", energy="primal_qi", width=18, height=90, faction="mudwater", named=True, surrenders=True,
                  spare_debt="lieutenant_spared", kill_debt="lieutenant_killed", hp_mult=1.6, name="Lieutenant Kuai"))

# Big Toad Tan, the first dungeon boss: the bandits' chief, a head taller than his men, his top knot and bare arms, a
# staff he swings like a club. His tell is the club raised over his head (held), slammed down on the blow; the same
# tell calls his bandits. At half his health he drinks (the phase heals him and calls them again: its moment is the
# room's, the wine jar the side view's).
species("big_toad_tan", plan="person.brute", share=True, size=1.12, elite=False, shadow=(10, 3), cycle=12.0,
        data=dict(level=18, role="dungeon_boss", element="none", page=None, drops=[("mudwater_manual", 1.0)],
                  attacks=[("club_swing", 0.55, 90, 1.2, dict(depth=34, knockback=60)), ("call_bandits", 1.0, 0, 0.0, dict(summon="mudwater_bandit"))],
                  ai="boss_tan",
                  art=person("Big Toad Tan", hair="topknot", hair_color=5, shirt="sleeveless", pants="loose", shoes="boots", weapon="staff",
                             hat="none"),
                  race="human", energy="primal_qi", width=24, height=96,
                  phases=[{"below": 0.5, "action": "drink_wine", "heal": 0.1, "breakable": "wine_jar"}], first_defeat=["mudwater_cleaver"],
                  # The first dungeon boss teaches the pattern (dodge the club, break the wine jars) rather than walls it.
                  hp_mult=0.6, attack_mult=0.8, pet_book={"item": "pet_book_frenzy", "chance": 0.35}, faction="mudwater", named=True))
