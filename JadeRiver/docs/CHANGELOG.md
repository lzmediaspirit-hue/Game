# Changelog

## 1.1 (in progress) — The Azure Expanse (Act II)

Built in phases (docs/act2_design.md). Phase A, "Beyond the Gate", is playable end to end.

### Phase A · Foundation
- The crossing: after the Gate Guardian falls, the Ascension Gate opens onto **Cloudgate Port**, a sky
  harbour on a floating island (Arrival Terrace, Port Market, Skydock, the Wayfarers' Inn and the
  Condensing Hall). The Expanse is its own zone: ceiling Sage Sovereign 3, Qi density 1.2–2.0,
  Spirit Stones as the everyday currency.
- **Thunderhorn Plains** (Lv 64–69): the Stormgrass Verge, Thunderhorn Flats, the Lightning Scar and the
  Herders' Camp, with two new monsters, the lightning-spitting **Spark Weasel** and the charging
  **Thunderhorn Rhino**, stormsteel ore veins and a thunder insight stone.
- **Storm Ward attunement** (S18): four jades per zone (Thunder, Gale, Rain, Lightning) on a new
  Character › Attunement tab, each raised with Storm Shards (level n costs n shards, up to 15). The total
  is set against what each room asks; under-attuned, you deal less and take more (S18 formula). Safe
  rooms ask nothing; a Storm Blood Pill adds +4 for 30 minutes.
- **Chapter 11**: Through the Gate, A Sky Full of Toll Roads, Storm in the Blood, Horns for the Furnace
  and Sage — the first breakthrough of the Expanse, to Sage 1 in the Condensing Hall (third-grade purity,
  the Sage Condensing Pill, and a land that can hold it).
- Fifteen new NPCs of the port and plains: the Alliance toll warden and factor, a veiled free broker,
  the Condensing Hall's alchemist, sky-ship hands, a stormsteel smith, an apothecary, innkeeper and
  herders. Two new avatar hats: the jade **Guan** crown of Alliance officials and the veiled
  **Weimao**, pose-registered in every action and both facings.
- Spirit-grade (stormsteel/stormsilk) gear in the Alliance Factor's hall, stormsteel forge blueprints
  from Sage 1 (Sage realms may refine Spirit grade), Thunderhorn Stew, the Storm Blood Pill, and five
  Spirit Stone shops. Spirit Stone prices come from tael prices at the exchange rate; loot coins in the
  Expanse pay Spirit Stones.
- A zone-aware World map (one tab per zone you have set foot in; the Expanse as islands in a sea of
  cloud, with each region's Storm Ward need). Teleporting across zones costs five times the fee.
- Art and sound: two new parallax backdrops (the storm plains under a thunder deck, the sky port among
  floating islands), sky-ships, herders' yurts, storm menhirs, the Alliance banner, stormsteel veins,
  Storm Ward jade icons, and two synthesized music loops (Cloudgate Port, the Thunderhorn Plains).
- Tests: the valley run now crosses the gate and plays chapter 11 to Sage 1 (a new ae1 section);
  the contract suite loads and compiles every script.

## 1.0 — The Complete Valley (Act I)

Built on the v0.13 movement and avatar engine, which is kept intact (its 3,660 engine checks pass).

### A game around the engine
- Five-layer architecture: data, state, rules, authorities, presentation. Sixteen authorities own every
  system; presentation only sends intents. Named random streams, a single clock, event queue, unlock
  service and v3 saves with migration from the v0.13 slots.
- The Jade River Valley: 75 rooms across 20 regions, built from data with painted buildings, ladders,
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
- Retreat rooms and cave abodes: inner disciples get a door off the East Terrace or Array Court into
  the sect retreat rooms (seclusion up to 16 h, one breakthrough risk step safer); passing the
  mentor's trial opens a personal cave abode behind the elder's pagoda, with dense Qi, a spring,
  a mat and a bed.
- Combat: weapon-family combos, techniques, guard and dodge dash, elements, statuses, readable wind-ups,
  hit-stun, elites, field bosses, dungeon bosses with phases and weaknesses, story bosses (the
  Reflection, Elder Gu who flees with his ledger, the Gate Guardian), revival at shrines or on the spot.
- Crafts: gathering, mining, fishing, cooking, alchemy and the forge (timing mini-game), array plates,
  appraisal, formations, infirmary healing, worker puppets, manual restoration and teaching.
- Pill qualities: every refined pill keeps its quality (Flawed 50% with extra toxicity up to Perfect
  160%). From Heart Tempering 1 a run with every strike perfect may give a Pill Grain (180%, half the
  toxicity), a Pill Halo (200%, grows up to +50% while you sit in seclusion somewhere the Qi is dense)
  or a Pill Soul (220%, sometimes a unique effect). Sect Alchemy Hall furnaces and the Alchemy Dao
  raise the odds; quality pills glow in the bag with a dot, ring or star mark.
- Natural treasures (Spirit Awakening 8, "Treasures of Heaven and Earth"), one job each and never sold:
  the Mindwell Lotus behind Crane Falls (+500 Soul, mends the soul, shields it for an hour; once per
  great realm); the Evergreen Heart Tree, planted in rich earth on the elder's peak, a cave abode or the
  Back Mountain, whose fruit (one per season) revives you where you fell at full health; and the
  Nine-Bough Jade Tree at the Forgotten Monastery, which answers only an Understanding bottleneck with
  three quarters of your strongest Dao's gap to its next tier, once per stage. New props and icons.
- Spirit animal rarity and breeding: rarity (Common to Primordial) now scales an animal's strength and
  health. From Heaven Glimpse 1, with a level 4 Beast Pavilion, two Adults of one family (river, hound,
  burrow, wing) make an egg over a day; the child takes the higher rarity (sometimes one more), mixes
  its parents' traits and may carry a new one. The Spirit Animals page shows eggs with a Hatch button.
- Formations: the Restraint (monsters move 30% slower) and Concealment (monsters do not notice you until
  you strike) blueprints from library floor 3, completing the five valley formations. The blueprint
  list scrolls.
- Story: "The Riverbreath Trial" (Lu's inheritance at the Scripture Well: hold the ring while the drowned
  rise) before the Drowned Abbot, and "Farewells" split from "Beyond the Valley" (follow Lu's map to the
  Frozen Shrine first), matching the chapter list. Nine new side quests give the valley's quieter people
  a thread each (Fisher Wen, Washer Mei, Proprietor Fang, Smith Bao, Auntie Rong, Kai, Su Qing, Trader
  Min and a Wen Zhao rematch): 127 authored quests in all.
- Balance simulator: optional side quests now cost active time (10 minutes each) as well as paying their
  QP share, so adding side content no longer speeds the pacing. Every realm lands within 0.95-1.09 of the
  pacing table; Act I ends at 65.7 h (target 65).
- Emotes: a wheel in the Menu with the six starting emotes (bow, wave, cheer, fist salute, laugh, sit) and
  two earned from achievements (Champion, Beast Call). The avatar holds a pose, leans or bounces, with a
  speech bubble, until you move or act.
- Release checklist (S40): Settings > Data exports every save to one file (the device's Documents folder
  when allowed) and restores an export found on the device, keeping the current saves as backups; the
  engine log (five rotating files) can be exported for bug reports. A Credits screen (title and Settings)
  lists every LPC author and licence in full, the OFL fonts and the engine. Accessibility adds Bright
  flashes, Vibration and Captions for sounds (boss roars, bells, war drums, heavy wind-ups, off-screen
  notices). The notification toggle now switches every category. The Android preset is version 1.0.0.
- Companions, spirit animals (starter choice, taming with offerings, eggs), your own sect (buildings
  that appear as built, disciples, expeditions, defence raids), mail, achievements and titles.
- 27 pages on one shared frame, a HUD that reveals itself, a minimap, dialogue with portraits, shops,
  storage, map and teleports, codex, settings.

### Art and sound
- Mountain, gorge, quarry and cliff rooms walk on painted rocky ground, and the Summit Ridge on snow
  (`tools/art/bake_ground.py`, seamlessly tiling), instead of courtyard paving.
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
- Flight from Cloud Stride 1: jump again at the top of a double jump to ride a cloud; hold Jump to climb and
  Guard to descend. Combat pays the QI each second, no-flight rooms and interiors refuse, landing or an
  empty pool ends it. "Wings of Cloud" now teaches it.
- Mounts (Cloud Stride 1): the Jade Crane, Mist Wolf and Ember Fox can carry you (Mount role, walk ×1.5);
  you stand on the crane's back as it glides; a hard blow throws you off for a while; a flying mount halves
  flight QI from Cloud Stride 5.
- Binding (Spirit Awakening 3): a found relic's power is sealed until bound with a channel that a blow
  breaks; its Artifact Spirit wakes through a soul contest (a failure bruises the soul). The Sleeping Blade
  goes from bare-hand power to its full edge once bound.
- Spirit animals grow: Hatchling, Juvenile and Adult (a branch choice) need level, hearts and your realm
  together; three hidden traits reveal as they grow and change real numbers; Resonance adds to accumulation.
- Zone ceilings and attunement (S18) are announced and applied; alchemy and forge strikes are scored by
  Crafting; lost raids damage a building until you repair it.
- Every event in the catalogue is emitted by the system that owns it. Enemies notice you with a "!", and the
  HUD reports raids, hatched eggs, revealed paths, codex entries, quests ready to hand in and more.

### Accessibility
- Enemy danger badges carry shapes as well as colours (▲ tougher, ▲▲ a realm above, ▽ weaker), next to the
  left-handed HUD and text-size settings.

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
