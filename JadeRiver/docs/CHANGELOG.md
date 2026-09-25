# Changelog

## 1.0 — The Complete Valley (Act I)

Built on the v0.13 movement and avatar engine, which is kept intact (its 3,660 engine checks pass).

### A game around the engine
- Five-layer architecture: data, state, rules, authorities, presentation. Sixteen authorities own every
  system; presentation only sends intents. Named random streams, a single clock, event queue, unlock
  service and v3 saves with migration from the v0.13 slots.
- The Jade River Valley: 71 rooms across 20 regions, built from data with painted buildings, ladders,
  depth stairs, driftwood platforms, hidden portals, teleport stones and layered parallax backdrops.
- The Prologue in Lotus Ferry: ten short quests, one lesson each, the HUD filling in one element at a
  time, the Hollow Night, and the first breakthrough on Lu's boat. No weapon and no Qi until earned.
- Act I: twelve chapters of main story, a guided quest for every system, side stories for the village,
  the merchants and all four companions, daily sect missions, a tournament, sieges and a finale at the
  Ascension Gate.

### Systems
- Cultivation: 89 realm stages, bottlenecks and breakthrough risk, methods with ceilings (Lu's fragment
  gives way to a sect scripture at no cost), meridians, body training, purity, stability, injuries,
  Daos and technique mastery, offline seclusion (accumulate, temper body, heal, contemplate, refine Qi,
  nourish soul) with caps and no offline breakthroughs.
- Combat: weapon-family combos, techniques, guard and dodge dash, elements, statuses, readable wind-ups,
  hit-stun, elites, field bosses, dungeon bosses with phases and weaknesses, story bosses (the
  Reflection, Elder Gu who flees with his ledger, the Gate Guardian), revival at shrines or on the spot.
- Crafts: gathering, mining, fishing, cooking, alchemy and the forge (timing mini-game), array plates,
  appraisal, formations, infirmary healing, worker puppets, manual restoration and teaching.
- Companions, spirit animals (starter choice, taming with offerings, eggs), your own sect (buildings
  that appear as built, disciples, expeditions, defence raids), mail, achievements and titles.
- 27 pages on one shared frame, a HUD that reveals itself, a minimap, dialogue with portraits, shops,
  storage, map and teleports, codex, settings.

### Art and sound
- 42 creature sheets, 45 backdrop layers, 114 scenery props, 12 music tracks and 39 sound effects.
- Human enemies and all NPCs use the layered avatar engine; shirts and trousers now come in ten baked dyes
  (every action and facing), so villagers, elders and sect robes look distinct. Equipment carries its dye.

### Interface pass (from screenshots of a mid-game save)
- Every item has its own icon: new thread-bound method manuals (cover and emblem by element), tied technique
  scrolls, curios (the fake jade reads as glass), spirit wood, puppet core, array plate and the late-realm
  pills. `data_validation` now checks that every item, piece of equipment and technique has an icon.
- Spirit Animals, Codex and Mail open on an entry instead of an empty pane; pets and the bestiary draw the
  creatures themselves (undiscovered ones as silhouettes); companions are drawn with the avatar engine.
- Your Sect shows real build costs; long descriptions are trimmed to fit; bar labels are outlined; the Main
  quest tab says which chapter comes next and what it waits for; the board never lists the same mission twice.

### Systems finished against the spec
- Spirit animals grow: Hatchling, Juvenile and Adult (a branch choice) need level, hearts and your realm
  together; three hidden traits reveal as they grow and change real numbers; Resonance adds to accumulation.
- Zone ceilings and attunement (S18) are announced and applied; alchemy and forge strikes are scored by
  Crafting; lost raids damage a building until you repair it.
- Every event in the catalogue is emitted by the system that owns it. Enemies notice you with a "!", and the
  HUD reports raids, hatched eggs, revealed paths, codex entries, quests ready to hand in and more.

### Text
- Every line the player reads (about 730 interface strings plus realms, currencies and unlocks) now comes
  from `data/strings/en.json`, ready for translation; a test keeps new text out of the scripts.

### Balance
- A balance simulator (S38) plays the data with the real rules: every realm of Act I lands within 11% of the
  pacing table (Qi Kindling at 4.7 h, Heaven Glimpse at 52 h, the end of the Act at 61 h), and the next gear
  upgrade costs 0.8 h of play at Level 15 and 1.4 h at Level 25.
- Monster kills before the Weapon Hall can no longer drop equipment.
- The weekly mission from the content catalogue, Sect Service: twenty daily missions or one field boss for
  150 contribution. Every other row of the Part 8 catalogue was already in the data.

### Found and fixed by the scripted Act I run
- Event spawns were wiped on room entry; stale companion uids could delete monsters; daily missions
  dropped four of five; the Hideout key, the library methods, the Sleeping Blade and the Siege had no
  source; the Core Disciple rank could not be reached; tools filled the bag; the first technique could
  not be used with a sword; kept quest items stopped counting once used in a recipe.

### Tests
- `data_validation`, `rules_tests` (with same-seed replay and offline checks), `prologue_run` and
  `valley_run` (the whole of Act I) join the engine checks; `tools/run_tests.sh` and `Test.ps1` run all.
