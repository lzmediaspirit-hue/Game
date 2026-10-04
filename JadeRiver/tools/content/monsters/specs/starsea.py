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
