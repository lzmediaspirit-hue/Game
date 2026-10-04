"""Act II side stories of the port, the plains, the heights, the lake, the canyons and the Hold. Placed by story.py's
act2_side_quests() (section act2); they pay spirit stones and Act II's share of a stage (story.py: qp act2_side).

E5b: the canyons' and the desert's side stories follow the story there, but their rooms lie past the realm the story
reaches them at (the Kite Winds 74-76, the Harpy Roosts 75-78, the Worm Sea 77-81, the Scorpion Flats 75-78). Each waits
for its room's realm too (realm=ROOM), so it opens when its foes are the player's match."""
from content.quests.spec import side, clear, fetch, item, stones, PAY, ROOM

QUESTS = [
    side("snow_for_the_cabinet", fetch("frost_lotus", 3, "Pick Frost Lotus on Rimefrost Heights"), giver="apothecary_wu",
         after="frost_and_silence", realm="sage_1",
         offer=["Frost Lotus. Three. It only blooms where the snow never melts.", "It steadies a Sage's Qi. And my prices."],
         done="Perfect petals. Here, Storm Blood Pills, fresh from the cabinet.", pay=40,
         why="the apothecary pays in her own pills: three Storm Blood Pills, and 40 stones", gives=[item("storm_blood_pill", 3), PAY]),
    side("clear_skies", clear("azure_carp_dragonet", 8, "Drive off the Azure Carp Dragonets over the Reedless Shore"), giver="dockmaster_fu",
         during="the_mirror_remembers", target_room="ml_reedless_shore",
         offer=["Dragonets keep spitting at my lake ferry. The sails can't take much more.", "Eight of them. The rest will learn."],
         done="The ferry thanks you. So does my budget.", gives=[item("dragonet_scale", 2)]),
    side("a_lans_herd", clear("spark_weasel", 10, "Drive the Spark Weasels away from the herd"),
         fetch("spark_pelt", 4, "Bring Spark Pelts for new saddle blankets"), giver="herder_a_lan", name="A-Lan's Herd",
         after="storm_in_the_blood", realm="heaven_glimpse_3",
         offer=["The weasels keep stealing lightning out of the grass, and then the rhinos stampede!", "Chase them off? Please?"],
         done="Grandpa says you'd make a good herder. That's the best thing he says about anyone.", pay=stones(50),
         why="the plains pay in spirit stones, Act II's money, though its tier (Heaven Glimpse 3) is an Act I band's",
         gives=[item("thunderhorn_stew", 3)]),
    side("silk_on_the_wind", fetch("kite_silk", 5, "Cut Kite Silk from the Wind Kites of the canyons"), giver="tollkeeper_bai",
         after="nine_seats", realm=ROOM,
         offer=["The canyon wind shreds my toll flags in a week. The kites up there are made of something it can't tear.",
                "Five lengths of their silk. The Alliance can keep its banners."],
         done="Look at that. Not a fray. The next brigand who says he couldn't see the flag can argue with it.",
         gives=[item("storm_shard", 10)]),
    side("plumes_for_the_bellows", fetch("harpy_plume", 4, "Bring Harpy Plumes from the Harpy Roosts"), giver="clan_smith_gang",
         after="ironroot_blood", realm=ROOM,
         offer=["Harpy plumes hold a wind of their own. Line the bellows with them and the forge breathes like a storm.",
                "Four will do. Kin price, of course. Meaning you fetch them."],
         done="Hear that? The fire's roaring on its own. Take some stormsteel. It'll take a better edge now.",
         gives=[item("stormsteel_ore", 4)]),
    side("cactus_water", fetch("ember_cactus", 4, "Pick Ember Cactus flowers on the Glass Dunes"), giver="oasis_keeper_meng",
         after="glass_and_bone",
         offer=["The flowers store the sun. Steep them right and the water keeps the heat out of you instead.",
                "Four flowers. Pick them at dusk if you can. At noon they bite."],
         done="Cactus water. Drink it before the heat and your Essence runs cool. Here, the first jars are yours.",
         gives=[item("cactus_water", 4)]),
    side("glass_teeth", fetch("worm_glass_tooth", 3, "Bring Dune Worm glass teeth"), giver="bone_reader_xiu", after="glass_and_bone",
         realm=ROOM,
         offer=["Bones for the past, glass for the future. A worm's tooth shows what is coming, if you hold it to the sun.",
                "Three teeth. The worms will not give them politely."],
         done="Clear as water. I see... a ship with no sea. Hm. That one is yours to find, not mine.",
         gives=[item("clear_mind_pill", 2)]),
    side("stingers_for_the_hold", fetch("scorpion_stinger", 5, "Bring Sandstorm Scorpion stingers"), giver="clan_smith_gang",
         after=["glass_and_bone", "plumes_for_the_bellows"], realm=ROOM,
         offer=["Scorpion venom on a quenched edge. Old Ironroot trick for the desert raiders. Bring me stingers.", "Five. Mind the tails."],
         done="Good. The raiders will think twice. Here, more ore. Kin price.", gives=[item("stormsteel_ore", 4)]),
]
