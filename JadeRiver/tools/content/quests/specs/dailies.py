"""The daily mission board (S20, Part 8; mission_templates.json): each template a kind of job, each job one step and
the Levels it is posted at. QuestAuthority._fill_board posts a day's jobs and pays each at the Level it is posted at
(decision 45: its fixed cultivation; contribution and 10 + 3 x Level taels). A job's Levels come from the band of the
foe or node it names (engine.py job_levels) unless written."""
from common import all_of, unlocked
from content.quests.spec import daily, job, clear, gather, deliver, spar, step

DAILIES = [
    daily("hunt", "Hunt",
          job("Thin the boarlets", clear("wild_boarlet", 8), levels=(0, 5)),
          job("Quarry pests", clear("rock_beetle", 8)),
          job("Marsh leeches", clear("marsh_leech", 8)),
          job("Grey beasts", clear("hollowed_boarlet", 8), levels=(7, 14)),
          job("Monkey business", clear("bamboo_monkey", 8), levels=(10, 17)),
          job("Bandit patrol", clear("mudwater_bandit", 8), levels=(14, 22)),
          job("Shore crabs", clear("tide_crab", 8)),
          job("Rapids watch", clear("rapids_lizard", 8), levels=(27, 37)),
          job("Cliff hawks", clear("stormwing_hawk", 6)),
          job("Wolves in the mist", clear("mist_wolf", 6), levels=(45, 70))),
    daily("gather", "Gather",
          job("Willow Moss", gather("willow_moss", 5)),
          job("Ember Peppers", gather("ember_pepper", 5), levels=(10, 30)),
          job("Mist Lotus", gather("mist_lotus", 3), levels=(19, 70)),
          requires=all_of(unlocked("herb_gathering"))),
    daily("mine", "Mine",
          job("Copper for the forge", gather("copper_ore", 6), levels=(0, 20)),
          job("Jadeiron", gather("jadeiron", 4), levels=(12, 70)),
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
