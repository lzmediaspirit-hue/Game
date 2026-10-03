"""E3, the NPC engine (audit 45 §6.3, decision 45; docs/architecture/npc_engine.md). A person of the world is one
`npc(...)` spec (spec.py) in tools/content/npcs/specs/<zone>.py, and engine.py compiles it into every place a person
lives: their npcs.json row (story.py), their work in life.json (topdown_life.py), their look, and, for a person the
engine places itself, their object in the side-view room (world.py) and their anchor in the top-down room (the room
engine)."""
