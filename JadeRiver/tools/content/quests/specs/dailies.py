"""The daily mission board (S20, Part 8; mission_templates.json): each template a kind of job, each job one step and
the Levels it is posted at. QuestAuthority._fill_board posts a day's jobs and pays each at the Level it is posted at
(decision 45: its fixed cultivation; contribution and 10 + 3 x Level taels). A job's Levels come from the band of the
foe or node it names (engine.py job_levels) unless written, and a written one says why.

E5b: every hunt follows its foe's band. The Mist Wolves were posted up to Level 70, twenty Levels over the wolves; the
Sacred Ridge's stags and rocs hunt there now. Mist Lotus follows its nodes too (it ran to 70)."""
from common import all_of, unlocked
from content.quests.spec import daily, job, clear, gather, deliver, spar, step

DAILIES = [
    daily("hunt", "Hunt",
          job("Thin the boarlets", clear("wild_boarlet", 8)),
          job("Quarry pests", clear("rock_beetle", 8)),
          job("Marsh leeches", clear("marsh_leech", 8)),
          job("Grey beasts", clear("hollowed_boarlet", 8)),
          job("Monkey business", clear("bamboo_monkey", 8)),
          job("Bandit patrol", clear("mudwater_bandit", 8)),
          job("Shore crabs", clear("tide_crab", 8)),
          job("Rapids watch", clear("rapids_lizard", 8)),
          job("Cliff hawks", clear("stormwing_hawk", 6)),
          job("Wolves in the mist", clear("mist_wolf", 6)),
          job("Stags on the ridge", clear("hollow_stag", 6)),
          job("Rocs over the shrine", clear("cloudpeak_roc", 6))),
    daily("gather", "Gather",
          job("Willow Moss", gather("willow_moss", 5)),
          job("Ember Peppers", gather("ember_pepper", 5)),
          job("Mist Lotus", gather("mist_lotus", 3)),
          requires=all_of(unlocked("herb_gathering"))),
    daily("mine", "Mine",
          job("Copper for the forge", gather("copper_ore", 6)),
          job("Jadeiron", gather("jadeiron", 4), levels=(12, 40),
              why="an adept's vein, posted from Level 12 as the hand board had it; its veins run on to the Echo Cliffs (32-36)"),
          requires=all_of(unlocked("mining"))),
    daily("deliver", "Deliver",
          job("Rice for the kitchen", deliver("rice_ball", 3)),
          job("Teas for the infirmary", deliver("herbal_tea", 3))),
    daily("craft", "Craft",
          job("Kitchen duty", step("craft", "Cook three dishes", 3, craft="cooking")),
          requires=all_of(unlocked("cooking"))),
    daily("spar", "Spar",
          job("Sparring practice", spar())),
]
