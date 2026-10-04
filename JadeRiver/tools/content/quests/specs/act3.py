"""Act III's side quests, one a chapter, each placed in its chapter among the story's beats (story.py's
act3_citadel_quests, act3_ash_and_tide_quests and act3_lantern_heart_quests). They pay sage crystals and Act II's share of
a stage (story.py: qp act2_side)."""
from content.quests.spec import side, clear, step, item, fx, PAY, ROOM

# Chapter 20 (The Star Wardens), after the Orbit Ruins: the Confucian path.
CITADEL = [
    side("the_written_word", step("use_system", "Walk the Confucian path (the Cultivation page, Paths)", system="confucian_path"),
         giver="lanternwright_han", offered_by_unlock=True, chapter="20", target_room="lh_star_chandlery",
         offer=["The first Wardens were scholars before they were soldiers. Their words held stars in cages.",
                "If your heart is upright, walk the path of the written word with me. Righteous Qi bites the Hollow a quarter harder than any blade."],
         done=["Now the first glyph: Upright. Write it in the air and mean it. The strength of it is in your Insight, not your arm.",
               "The other glyphs are on my shelf, when you have the realm to hold them."],
         gives=[fx("learn_technique", technique="upright_glyph"), PAY, fx("codex", entry="confucian_path")]),
]

# Chapter 21 (Ash and Tide), after the Copperjaw box: the brush and the bell.
ASH_AND_TIDE = [
    side("brush_and_bell", step("buy_item", "Buy the Ink-Warden's Brush from the Bastion's armoury", item="ink_warden_brush"),
         giver="quartermaster_bai", after="kharns_pyre", chapter="21", target_room="tf_tidebreak_bastion",
         offer=["A scribe's brush writes a talisman on whatever it strikes. A Warden's bell rings out on both sides.",
                "Buy one of each if you have the crystals. Swords are for the young."],
         done=["There. A brush wants writing: here is Splashed Ink, the first stroke every Warden scribe learns.",
               "The bell is on the shelf when you want it. Swords are for the young."],
         gives=[fx("learn_technique", technique="splashed_ink")]),
]

# Chapter 22 (The Lantern Heart), first of the chapter: the Leviathan's Maw (optional). E5b: it waits for the Maw's own
# realm too (realm=ROOM: its Levels 97-99 lie past Sphere Lord 1, where the chapter opens).
LANTERN_HEART = [
    side("the_leviathans_maw", clear("nebula_leviathan", 1, "Bring down the Nebula Leviathan in its Maw"), giver="warden_captain_duan",
         name="The Leviathan's Maw", after="star_warden", chapter="22", realm=ROOM,
         offer=["Something in the Nebula Deep swallows the lantern ships whole. The old Wardens called it the Leviathan.",
                "It has a Presence like a storm and a Sphere as wide as a harbour. Go if you are ready. Nobody will think less of you if you are not."],
         done="You brought it down. The ships will run the Deep again. Take its scales; the alchemists will want them for the Law pills.",
         pay=200, why="a world boss: the Nebula Leviathan, and the lantern ships run the Deep again",
         gives=[PAY, item("leviathan_scale", 2), fx("codex", entry="nebula_leviathan")]),
]
