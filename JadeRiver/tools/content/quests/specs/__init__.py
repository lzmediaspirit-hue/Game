"""E5 quest specs (docs/architecture/quest_engine.md). SECTIONS lists each section story.py places among its hand quests
(`Q.extend(QE.rows(section))`) and the spec lists it holds, in order: a module's `QUESTS`, or `module:LIST`. quests.json
lists a section's quests in this order. DAILIES is the daily mission board (economy.py's missions())."""

SECTIONS = [
    # side_quests(): the valley's small threads, the companions' favours, the Hidden Vale's letters, then E5's own
    ("act1", ["valley", "companions", "hidden_vale", "valley_new"]),
    # act2_side_quests(): the port, the plains, the heights, the lake, the canyons and the Hold
    ("act2", ["expanse"]),
    # act2_starsea_side_quests(), after its three guided lessons: deserters, comet iron, the rare Daos
    ("starsea", ["starsea"]),
    # Act III: each chapter's side quest, placed in its chapter among the story's beats
    ("citadel", ["act3:CITADEL"]),
    ("ash_and_tide", ["act3:ASH_AND_TIDE"]),
    ("lantern_heart", ["act3:LANTERN_HEART"]),
]

DAILIES = "dailies:DAILIES"
