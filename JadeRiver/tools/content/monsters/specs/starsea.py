"""The Starsea's foes (M4; the Skyport Wreck's Broken Pier, Pirate Deck and Riven Peak, Blackmast's docks, battery and
cove, and the Sect War at the Alliance Gate, levels 76-90): the starsea pirates, the rogue Nine Peaks disciples and Comet
Captain Rao.

People are drawn as the player and the villagers are (plans/person.py): the shared character body dressed in the
outfit of their row's `art` (person()), cast by the character's own pipeline. The captain is a person of size, sculpted
(humanoid.captain)."""
from content.monsters import person, species

# M4. A pirate of the comet sails (the Starsea's packs, the Sect War's boarders): a short knot under a headband, an indigo
# sleeveless vest, ink cuffed trousers, boots, a cutlass. Its tell is the cutlass drawn back in a crouch (its boarding
# hook's too), and it cuts.
species("starsea_pirate", plan="person.fighter", share=True, size=1.0, shadow=(8, 3), cycle=12.0,
        data=dict(level=(79, 81), role="normal", element="metal", page="azure",
                  drops=[("comet_iron", 0.4), ("storm_shard", 0.55, (1, 2)), ("spirit_stone_shard", 0.4, (1, 2)), ("will_tempering_pill", 0.04)],
                  attacks=[("cutlass_combo", 0.4, 70, 1.2), ("boarding_hook", 0.6, 260, 1.0, dict(projectile={"speed": 560, "art": "arrow"}))],
                  ai="duelist",
                  art=person("Starsea Pirate", hair="short_knot", hair_color=0, shirt="sleeveless", pants="cuffed", shoes="boots", weapon="sword",
                             hat="headband", shirt_dye="indigo", pants_dye="ink"),
                  race="human", energy="sage_qi", width=18, height=90, pack=True))

# M4. A deserter of the Nine Peaks Alliance (the Sect War, the Broken Pier, the Pirate Deck): the sect's grey robe over ink
# trousers, boots, a guan over its topknot, a tattered cape, a jian. Its tell is the sword drawn back in a crouch (its
# nine-step lunge's too), and it cuts.
species("nine_peaks_disciple", plan="person.fighter", share=True, size=1.0, shadow=(8, 3), cycle=12.0,
        data=dict(level=(76, 78), role="normal", element="metal", page="azure", drops=[("alliance_badge", 0.45), ("storm_shard", 0.5, (1, 2))],
                  attacks=[("peak_sword", 0.45, 84, 1.2), ("nine_step_lunge", 0.7, 160, 1.3, dict(dash=120, knockback=70))], ai="duelist",
                  art=person("Rogue Nine Peaks Disciple", hair="topknot", hair_color=2, shirt="disciple", pants="martial", shoes="boots",
                             weapon="sword", hat="guan", shirt_dye="grey", pants_dye="ink", cape="tattered"),
                  race="human", energy="sage_qi", width=18, height=90, name="Rogue Nine Peaks Disciple"))

# M4. Comet Captain Rao (the Riven Peak's story boss): burly and barrel-chested, a head over his men and broad as two, a
# crimson coat open over a pale linen shirt (its tails to his knees, gold-trimmed), a wide belt, ink trousers in high
# boots, a tattered cape of the comet sails' dark navy, his ash-black hair tied back under a jade headband, a short full
# beard and a scar across his eye; his comet anchor of blue-black iron over his shoulder on its chain. His tell is the
# anchor raised high over his head in both hands as comet fire runs along its flukes (held: his anchor throw's too), and
# he slams it down before him in a burst of comet sparks.
species("pirate_captain", plan="humanoid.captain", share=True, size=2.6, elite=False, shadow=(13, 4), cycle=11.0, view=True,
        canvas=(170, 160),
        palette=["folk_skin", "capt_coat", "capt_shirt", "capt_trousers", "capt_belt", "capt_boot", "capt_cape", "capt_hair", "capt_band",
                 "comet_iron", "brass", "maw"],
        data=dict(level=80, role="story_boss", element="metal", page=None,
                  drops=[("comet_iron", 1.0, (3, 5)), ("storm_shard", 1.0, (10, 15)), ("will_tempering_pill", 1.0, (1, 2))],
                  attacks=[("comet_cleave", 0.6, 130, 1.4, dict(depth=50, knockback=110)),
                           ("anchor_throw", 0.9, 330, 1.25, dict(projectile={"speed": 520, "art": "pebble"})),
                           ("boarding_call", 1.0, 0, 0.0, dict(summon="starsea_pirate"))],
                  ai="duelist",
                  art=person("Comet Captain Rao", hair="long_tied", hair_color=5, shirt="vneck", pants="cuffed", shoes="boots", weapon="sword",
                             hat="headband", shirt_dye="crimson", pants_dye="ink", cape="tattered"),
                  race="human", energy="sage_qi", width=20, height=94, name="Comet Captain Rao",
                  hp_mult=1.5, attack_mult=0.9, phases=[{"below": 0.4, "action": "enrage", "cooldown": 0.7, "damage": 1.25},
                                                        # S48: cornered, the Captain burns his nascent soul (a telegraphed blast).
                                                        {"below": 0.12, "action": "self_detonate", "windup": 3.0, "radius": 280, "damage": 0.6}],
                  first_defeat=["comet_tail_flame"]))
