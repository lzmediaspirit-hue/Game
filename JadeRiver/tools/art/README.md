# Jade River art generators

Deterministic Python generators for the game's art. What is here:

| Folder | What it draws |
|---|---|
| `topdown/` | the top-down world: the character's layered figure (`figure/`), the foes' sheets (`creature/`, `build_foes.py`; the monster engine's specs are in `tools/content/monsters/`), tiles, props, foliage, life and vistas |
| `fx/` | the FX sheets (blows, impacts, techniques) |

Props and the few tiles the pages and room objects still draw are in `tools/props/`, the icons in `tools/icons/`.

The side view's creature toolkit (`pixel.py`, `build_creatures.py`, `creatures/<id>.py`, `helpers_batch_*.py`, which
drew `art/creatures/` and `data/creature_art.json`) went with the side view in S12b: every creature the game draws, in
the room and on the pages, is its species' top-down sheet (`art/topdown/foes/`, `data/topdown/foes.json`).
