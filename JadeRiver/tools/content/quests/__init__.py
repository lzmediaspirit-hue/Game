"""E5, the quest engine (audit 45 §6.5, decision 45; docs/architecture/quest_engine.md). A side quest is one `side(...)`
spec and a daily job one `job(...)` (spec.py) in tools/content/quests/specs/; engine.py compiles them into the rows the
game reads (quests.json through story.py, mission_templates.json through economy.py), deriving where each leads, when it
opens and what it pays (the band table, bands.py)."""
