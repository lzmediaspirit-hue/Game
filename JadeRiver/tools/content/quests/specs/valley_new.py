"""E5's own side quests (phase 3): optional threads for four converted Act I rooms that had none (the Lower Pit,
Whispering Bamboo, Bend Shore, the Rapids Terraces), each asked by a person of the NPC engine who had no quest. Each
spec names only the giver, the step and the words: the room, the realm and the pay are derived. Placed by story.py's
side_quests() (section act1), last."""
from content.quests.spec import side, clear, fetch, item

QUESTS = [
    # The Lower Pit (Levels 5-7): its moles' claws. Leads to the Lower Pit, opens at Bone Forging 6, pays the Bone
    # Forging band.
    side("claws_for_the_grindstone", fetch("mole_claw", 5, "Bring Ironclaw Mole claws from the Lower Pit"), giver="apprentice_tao",
         offer=["Master Bao's grindstone has gone smooth as a river pebble. Nothing dresses a stone like a mole's claw.",
                "The Lower Pit is full of them. Five claws, and don't tell him it was my idea."],
         done=["Hear it bite? He'll say the stone was always this good.", "Here. Apprentice pay, but it's honest."]),
    # Whispering Bamboo (Levels 10-14): its monkeys. Opens at Qi Kindling 3, pays the Qi Kindling band.
    side("pelted_at_the_fair", clear("bamboo_monkey", 8, "Run the Bamboo Monkeys out of Whispering Bamboo"), giver="adventurer_rui",
         offer=["I took the short way through Whispering Bamboo and the monkeys pelted me with shoots. In front of half the fair.",
                "I'm retired. You're not. Eight of them, and my pride is even."],
         done="Ha! Kai can stop laughing now. Dumplings, on me.", gives=[item("toad_oil_dumplings", 2)]),
    # Bend Shore (Levels 19-23): its jade carp. Opens at Qi Unfurling 3, pays the Qi Unfurling band.
    side("scales_for_the_lanterns", fetch("jade_scale", 4, "Bring Jade Carp scales from Bend Shore"), giver="fair_vendor_he",
         offer=["Lanterns for the next fair, and every vendor in Stoneford hangs paper ones. Mine will shine.",
                "Jade carp scales, four of them. The carp at Bend Shore won't sell me theirs."],
         done="Look at them catch the light! Here, take a charm. Lucky ones. Mostly.", gives=[item("return_charm", 1)]),
    # The Rapids Terraces (Levels 28-33): its lizards. Fisher Gan is home once the well runs clean, so it follows
    # Cleansing the Well and pays that quest's band (Heart Tempering).
    side("the_weir_at_the_rapids", clear("rapids_lizard", 6, "Drive the Rapids Lizards off the Rapids Terraces' weir"), giver="fisher_gan",
         after="cleansing_the_well",
         offer=["Greyreed's nets used to hang in the eddies under the gorge. Three seasons away, and the rapids lizards took the weir.",
                "Six of them. They bask on the terraces where the water breaks."],
         done=["The weir's ours again. My cousin in Stoneford can keep his floor.", "Take the spare net. It's mended. Mostly."],
         gives=[item("hemp_net", 1)]),
]
