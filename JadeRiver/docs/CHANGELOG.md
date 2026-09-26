# Changelog

## 1.1 — The Azure Expanse (Act II)

Built in phases (docs/act2_design.md). All five phases (chapters 11 to 16) are playable end to end, from
the Ascension Gate to the Starsea Launch.

### V9f3 · The rest of the room verticality catalogue (Part 8, S43)
About forty valley rooms that V2d left partial are now built by hand to their catalogue rows and marked
`authored`, so the movement and verticality passes leave them as built. Every portal, quest object, event and spawn
the story and the tests use still works. One module per group: `tools/data/catalogue_rows_towns.py`, `_fields.py`
and `_dungeons.py`. The room-by-room notes are in `docs/v9f3_towns.md`, `docs/v9f3_fields.md` and
`docs/v9f3_dungeons.md`.
- **Towns and sects:**
  - Willow Path's stumps and lifting stones stand as blocks, and Old Pan trades from his cart deck.
  - Market Street has galleries at 176, rooftops at 264 and the bell tower at 300; the rooftop thief's route follows them.
  - The Fairground has stone stages and tent tops, with festival lanterns only the drum's bounce reaches.
  - Jade Sect: terraced herb beds at 40/80/120, a mezzanine in the Alchemy Hall, weapon racks you can stand on,
    Elder Hu's peak ledges at 100/200/300, and doors to the Retreat Rooms and cave abodes on the high tiers.
  - Cloud Sect: the Cliff Stair's landing, rope and the Library's upper gate, and the Array Court's dais.
  - Hidden Vale's back mountain gets ledges.
- **Fields:**
  - Quarry: a falling-rock pit and a rubble heap with a cracked wall that opens for Body 20.
  - Marsh: stilt decks around the Marsh Edge; rafts, a moored chest raft and a lily-pad climb on the Grey Pools.
  - Greyreed Hamlet: roofs chained at 88 to 176, with two grey lanterns to cleanse for "Grey Roofs". The hamlet
    door now opens at the quest's own realm, which fixes a quest that could never be started.
  - Water: canopy decks and spirit-egg nests in the Thicket Heart; stepping rocks and deep water at the Falls Pool;
    docks, a ferry and a sampan roof at the Bend Shore; a current and stepping stones in the Rapids Terraces.
  - Heights: landings and shortcuts on the Pilgrim Stairs, pillars on the Cleansing Summit, crags with updraft
    columns on the Cliff Faces, and cloud ledges up to 900 on the Sky Ledges.
- **Dungeons and story rooms:**
  - Mudwater Hideout: palisades and watchtowers in the Stockade, spike pits under crumbling planks in the Tunnels,
    stalagmites in the Loot Cave.
  - Drowned Shrine:
    - rafts on a current at the Flooded Gate;
    - swinging and circling lantern platforms up to a loft in the Hall of Lanterns;
    - a descent from a 300 rim to a flooded bottom in the Scripture Well;
    - the Abbot's rising water.
  - Mist Peak and beyond:
    - ruined roofs, crumbling floors and a hidden stair at the Forgotten Monastery;
    - cloud rings at the Ascension Gate;
    - crumbling icicle platforms at the Frozen Shrine;
    - a mirrored arena for the Trial of Reflections;
    - catwalks and rafters in Gu's Warehouse;
    - a battlement and towers for the siege.
- Known limits (engine work for later):
  - Portals have no altitude.
  - Objects placed mid-roof draw behind the roof face.
  - Bosses do not use tiers.
  - Sect-level buildings cannot grow roofs yet.

### V9f2 · Ice, and mounts in a vertical world (S43 rules 5 and 12, v1.1)
- **Ice (the v1.1 traction rule):** a new `ice` volume.
  - On ice, your speed only eases toward what you ask for, at 380 to 420 a second. You slide on when you let go and
    slide to a stop. In the air, control stays total.
  - Glazed ground in the Frozen Shrine (two sheets), on the Rimefrost Summit and on the Frostpine Climb, drawn as a
    pale blue glaze with slow glints.
- **Mount jumps:** a ground mount jumps with its species' impulse. The Cloud Stag's 600 reaches about 156, where a
  jump on foot reaches 122. A flying mount's rider jumps as on foot, because the animal flies instead.
- **No Wall-Step on a ground mount.**
- **Climbing:** a ladder or rope puts the rider down off any mount; it waits below. You are back in the saddle when
  you step off at the top or land. The log says so calmly, not in red.
- Tests: `rules_tests` `ice_mount_suite`:
  - slow speed gain on ice, sliding on and stopping, a dead stop off the ice, air control over it;
  - the 600 jump's height;
  - mount jumps by kind;
  - dismounting for a ladder and remounting at the top.

### V9f1 · The rooftop thief and the Cloud Steps (S43 rule 15)
- **"Catch the thief"**, daily on Market Street (from Qi Kindling 1) and Gate Street (from Qi Kindling 3).
  - Quick-Fingered Hou loiters in the street. Speak to him (the action reads Chase!) and he bolts over the roofs.
  - Market Street: store, awning, tea house, awning, warehouse, then the bell tower. Gate Street: the three-roof
    chain.
  - He pauses at each roof to jeer. A timer runs at the top of the screen.
  - Reach him on his roof, at his height, to catch him. From the street below you cannot lay a hand on him.
  - Market Street pays 150 taels and a Spirit Stone shard; Gate Street pays 120 taels and sect contribution.
  - If he gets over the far wall, nothing is paid. Leaving the street lets him get away too.
  - One chase a street a day, caught or not.
  - Catching ten earns the Thief-Catcher title (+2% coin find).
- **The Cloud Steps**, the Cloud Sect's timed climb:
  - The Cliff Stair now reaches its catalogue's 300 ledge. Touch the flag at the foot (from Bone Forging 3) and reach
    the bell at the top before the incense burns down (60 s).
  - Each week has a board of six sect disciples with fixed, seeded times.
  - A place in the top three pays contribution and taels once a week.
  - Medal pars: bronze 18 s, silver 13 s, gold 10 s. Each medal's reward is paid the first time you beat its par.
    Gold also earns the Cloud Stepper title (+1% move speed).
- New World events `chase_started`, `thief_caught`, `thief_escaped`, `route_started` and `route_finished`, with HUD
  toasts.
- Debug tools: `--interact=<object>` presses a room object in a preview (a thief, a route stone).
- Tests: `rules_tests` `rooftop_routes_suite`:
  - the route clock;
  - every waypoint standing on a roof;
  - the grace moment, the height rule, the catch and its pay, one chase a day, the escape;
  - the Cliff Stair's 300 ledge;
  - the week's board, medals once, a timed finish, the burned-out incense.

### V9e3 · The Cloud Herb Terraces and the ten-thousand-year tier (S45, Part 8, v1.1)
- **Cloud Herb Terraces:** a new room east of the Cloud Sect's Array Court, with three terraces cut into the cliff.
  Willow moss and ember pepper grow at the foot, ginseng on the middle terrace and mist lotus on the high one.
- **The weekly Herb Terraces Trial** is now held on each sect's own terraces, as Part 8 says ("Jade or Cloud Herb
  Terraces"):
  - Cloud Sect disciples gather on the Cloud terraces and Jade Sect disciples on the Jade terraces; a disciple of
    neither sect uses the Jade terraces.
  - Each terraces is ranked against the other sect's gatherers (a fixed, seeded draw per trial). The Jade draw is
    unchanged.
  - Herbs gathered on the other sect's terraces do not count.
  - The Calendar page, the event toast and the ranking name your own terraces. The rewards are unchanged
    (Foundation Guard Pill recipes for the top three).
- **Ten-thousand-year ginseng** (Riverreed Ginseng 10,000 yr, Mystic grade, hot, Principal or Minister):
  - The herb ages now run 10, 100, 1,000 and 10,000 years.
  - It ripens on two high Expanse ledges, a Master's pick, every fifth in-game day:
    - Snow Ape Ledges at dawn, guarded by a Snow Ape elite;
    - Harpy Roosts at night, guarded by a Canyon Harpy elite.
  - None grows in the valley.
  - Its icon wears the Expanse's pale jade over the thousand-year gold.
- **The Verdant Dew Vial's v1.1 tier:**
  - A bed in the valley still holds a herb at 1,000 years.
  - A bed in the Azure Expanse ages it to 10,000. The Herders' Camp on the Thunderhorn Plains lets two High-grade
    plots inside its fence.
  - A herb already as old as it grows says so.
- **Page headings** step their size down to fit instead of being cut off (the World map's "Cloud Sect Monastery").
- Tests: `rules_tests` `expanse_herbs_suite`:
  - the room and its link;
  - each sect's trial room;
  - the rivals by sect;
  - herbs counting only on your own terraces;
  - the dew cap by zone and the ten-thousand-year age;
  - the two guarded Expanse nodes, and none in the valley.

### V9e2 · The five-screen furnace (S15, S44)
- **Alchemy is now played in five screens** (the forge keeps its three strikes). A step tracker shows where you are.
  1. **Ingredients:** the recipe, the batch, each herb's role and nature, and stand-ins. With Spirit Sense, the
     sealed (unappraised) roots the batch would use are counted. At 4% Crafting perception, dyed fakes among them
     are named.
  2. **Furnace:** the fire (as before) and a new **array**, Still Water or Rising Flame.
     - The array that answers the Principal herb's nature widens every heat band by 15%: Still Water under a hot
       herb, Rising Flame under a cold one. The other array narrows the bands by 15%.
     - The screen shows the band width you will get.
  3. **Extraction** (full width), one herb at a time in the recipe's order:
     - Hold **Fan the flame** to raise the heat, and keep it inside a gold band that sways. Hot herbs sit their band
       high on the gauge; cold herbs sit it low.
     - Tap the dark impurities as they rise: they are a quarter of the score. Crafting perception shows more of them
       plainly; the rest are faint.
     - Heat in the band less than 35% of the time **scorches the herb**. That herb's share is lost (early mistakes
       waste ingredients). Put in another and try again, or put out the fire.
  4. **Fusion:** tap the essences into the core in the recipe's order (Principal first), then **turn the array**
     as a needle crosses each of 2–3 marks.
  5. **Condensation:** a ring closes on the pill; press **Condense!** as it meets the outline.
     - Early makes a weaker pill.
     - Late by more than 0.2 s **cracks the pill** and the whole batch is lost (late mistakes ruin the batch).
  6. **Pill tribulation:** unchanged, now drawn full width.
- **Liquids** skip Condensation: they are done at Fusion.
- **Herbs that fight each other** now blow the furnace at Fusion, as they merge.
- **Putting out the fire** mid-refine loses the herbs already in it; the rest stay in the bag. A refine left burning
  when the page closes is picked up where it was.
- **Intents** (S15): `start_refine` draws the plan (band sway, impurities, the marks) on its own RNG stream, so the
  quality roll's stream is untouched. `refine_input {step, value}` sends what the hand did, and the authority clamps
  it to what could happen and scores it. `cancel_refine` puts out the fire. The quality roll uses the three screens'
  scores, averaged; Extraction's score is the mean of its herbs.
- **Crafting perception** now also grows with Spirit (0.1% a point), as S15 asks.
- **Alchemist Guild candles** are longer, allowing about half a minute a refine: Adept five minutes, Expert seven,
  Master ten.
- The numbers live in `forge_upkeep.json` `furnace_game`.
- Previews: `--open-page=alchemy:` followed by `__furnace`, `__extraction`, `__scorched`, `__fusion`,
  `__fusion_turn` or `__condensation`.
- Tests:
  - `rules_tests` `furnace_game_suite`:
    - the plan, the natures and the array;
    - steps out of order;
    - a scorched herb;
    - the clamped report;
    - out-of-order Fusion;
    - a cracked pill;
    - an early (weak) pill;
    - putting out the fire;
    - a liquid;
    - Spirit Sense on sealed herbs;
    - the same seed and the same hand making the same pills;
    - the crafts page played frame by frame by a steady hand.
  - `valley_run` refines every pill through the five screens.

### V9e1 · The Forge and Formation guilds, and the Alchemist Master (S44, S49)
- **Three profession guilds** share one Guild tab in Crafts, with a button for each guild you have opened.
  - Each has three ranks, and each rank is an exam against the candle.
  - Passing gives a badge title (a small crafting bonus), opens more of the guild shop, and raises what the
    commission board pays.
  - Only one candle burns at a time, and the auto-refine queue never counts toward an exam.
- **Alchemist Guild** (Guildmaster Tang): Adept and Expert as before. New **Master** exam: three Superior Storm
  Blood Pills in eight minutes.
  - The reward is the Sage Condensing Pill recipe; the shop adds Soulbell Flower and Frost Lotus.
  - Its badges are now named Alchemist Adept and Alchemist Expert (same ids).
- **Forge Guild** (v1.0; Smith Bao, Artisan Row) opens at Qi Unfurling 3 once you forge. Its exams ask for weapons
  of any family at a grade or better:
  - two Earth-grade at Fine in five minutes (Adept);
  - two Heaven-grade at Superior in seven (Expert; ten Refining Essence);
  - two Spirit-grade at Superior in ten (Master; a Weapon Soul Crystal).

  Its counter sells ore by rank, and its board orders forged pieces.
- **Formation Guild** (v1.1; the new Array Master Ren, Artisan Row) opens at Heart Tempering 5 once you carry array
  plates. Plates are etched, not rolled, so its exams ask only for speed:
  - four Array Plates in three minutes (Adept);
  - three Killing Array Plates in four (Expert);
  - five Binding Array Plates in five (Master).

  Its counter sells plates and stones.
- **Master exams** are sat at Cloudgate Port and need the Sage realm. Smith Hong and Apothecary Wu open the Guild tab
  there; elsewhere the Start button says where to go.
- **Commission boards:** each guild keeps its own, with three orders a day from what you can make, each board
  capped at a fifth of the day's income target. Old saves keep the Alchemist Guild's board.
- The Guild Board on the Artisan Row covers all three guilds. A guild master opens the tab on their own guild.
- The Max Test character holds every guild at Master.
- Tests:
  - `rules_tests`:
    - the Master exam's realm and hall;
    - auto-refines not counting;
    - Forge exams by grade and slot;
    - a forge commission on its own board and cap;
    - the Formation Adept exam.
  - `data_validation` checks every guild's hall, master, shop, gate, ranks, titles and rewards.

### Old Snapper and crowding
- **Old Snapper** (the first elite, *Crab Trouble*) was tuned for a perfect player. A Mortal with bare fists has
  83 HP and no defence. Against them it had 235 HP and a 20-point claw, and two Reedtail Rats spawned beside
  it. A player who did not step out of every slam died in about 7 s with the Snapper at three quarters health.
  - It now has about 135 HP and a 9-point claw (`hp_mult` 0.24, `attack_mult` 0.33).
  - A player who arrives hurt from the crabs, never rests and never dodges wins in about 18 s. Reading the tell
    makes it easy.
- **Reed Shallows.** The rats keep to the west and middle of the shallows, away from the Snapper's bank, and
  come back after 20 s instead of 8.
- **Crowd cap on sight aggro.** An ordinary monster that sees the player stays put, and joins only when struck,
  in two cases (`combat.sight_aggro_cap`):
  - an elite or boss is already fighting the player;
  - two ordinary foes already are.

  Elites, bosses and summoned monsters (a boss's adds, an event's waves) always come. Monsters notice the player
  within 100 px of depth (`combat.sight_depth`, was 140), so foes in other lanes stay out of it.
- Tests:
  - `prologue_run` beats Old Snapper as a new player would, without resting or reading the tell (it fails with the
    old numbers);
  - `rules_tests` `aggro_cap_suite` covers the cap, being struck, elites and summoned adds.
- Both APKs are version 1.0.3 (code 103).

### Two Android builds; no Credits button
- **Max Test APK.** A second Android preset, *Android Max Test* (custom feature `max_test`, package
  `com.jaderiver.cleanengine.maxtest`), installs beside the normal game.
  - On first launch it makes **Max Tester** (`AccountAuthority.create_max_character`): the Prologue behind them, at
    the highest realm this build's zones allow (Sage Sovereign 3, Level 79).
  - Every system is unlocked. Every method, technique (top mastery), Inner Art (worn), movement art, recipe, Dao
    tier and craft rank is theirs.
  - Gear: the best piece for every slot and the best furnace at Perfect +10, one best weapon of each family, every
    flight vessel and a Beast Bag. Ten of every pill, talisman and throwable wait in storage.
  - Every animal at the highest stage the realm reaches, a mount, the companions, Elder of the Jade Sect, and a
    founded sect at level 20 with every building at 10.
  - Every teleport stone and room is known, with 10,000,000 silver, 1,000,000 spirit stones and shards for fees.
  - The build opens every way (`WorldAuthority.debug_open_ways`: portals, hidden ways and climbs, except rooms not
    built yet).
  - Debug tools (`Unlocks.debug_tools()`) now run in debug builds and in this APK; a plain release build still has
    none. `--max-character` does the same in the editor.
- **Credits removed.** The Credits buttons on the title screen and in Settings > Data, and the Credits page, are
  gone. The title's Settings button spans the row. Attribution still ships inside the game (`data/LPC-CREDITS.txt`
  and the font licences) and in the README.
- **HUD money.** The silver and spirit stone pill widens for large balances, and spirit stones show thousands
  separators. Before, 10,000,000 silver ran into the stones.
- Tests: `rules_tests` `max_character_suite` checks the Max Test character:
  - the top realm;
  - every unlock;
  - every technique and movement art;
  - Perfect +10 gear;
  - a bag with room;
  - every stone and room;
  - animals, mount and companions;
  - both sects and the start room;
  - with ways open, every built room reachable.
- **Numbers on Android.** The Android preset left `art/fonts/PixelifySans.ttf` out of the export (a filter from
  before Pixelify was the number font). In every APK up to 1.0.1, numbers over the world failed to draw, and so did
  what came after them in the same draw: HP and Qi values, bag counts, damage numbers, cooldowns. The font now ships.
  `contract_tests` checks that no export preset leaves out a file the scripts load.
- Both APKs are version 1.0.2 (code 102).

### Readability pass and the Fisher's Hut
- **Heavier, clearer type.** Every word in the game was drawn in Cormorant Garamond **Light**: the font's weight was
  set with a plain `"wght"` key, which Godot ignores, so it stayed at its thinnest default. Weights now use OpenType
  tags and take effect.
- **Source Serif 4 for text.** Labels, names, paragraphs, buttons and world labels are now set in Source Serif 4
  (semi-bold for text, bold for world labels and small headings, small optical size). It has a taller x-height and
  twice the stroke weight at the same widths the layouts were drawn for. Headings of 22 px and up stay in
  Cormorant Garamond, now truly bold. Numbers keep Pixelify Sans.
- **Minimum size.** No word or figure is drawn below 14 px (before the text size setting).
- **Settings > Accessibility > Text size now works.** Small, Normal and Large scale every word, and paragraphs and
  dialogue follow with their line height. It was saved before but never applied.
- **World labels are larger and sit on plates.**
  - NPC nameplates, enemy and ally names, loot names, NPC barks and the context verb are all larger.
  - Door and gate names show all the time, not only when you stand at them. They sit on a plate with a bobbing
    arrow and brighten when you are near.
  - Names at a room's edge move inward instead of hanging half off-screen.
- **HUD.**
  - The quest tracker sits on a soft ink panel, so it reads over sky and foliage. Its lines are a size larger.
  - The minimap title, bar values, bag item counts, the Ride/Walk and Auto labels, draught counts and the loadout
    letter are larger.
  - Toasts are larger.
- **Interior doors are drawn.** An exit on an interior's back wall showed only a faint arrow. It now shows the
  carved double door, which swings open as you come to it, with a pool of light at its foot. This covers 19 exits:
  the Fisher's Hut, Old Ma's store, the sect halls and the retreats.
- **Pickups glow.** Anything you can take stands in a warm pool of light. Its item icon bobs in a gold ring above
  it, with turning glints and its name on a plate; the verb shows when you are close.
- **The Fisher's Hut (the first room).**
  - Aunt Ping's three teas now show as tea bowls, not brown jars that read as clods of earth.
  - The tea on the table now sits on the tabletop instead of hidden behind the table.
  - The loft's bonus tea stays out of sight until the loft ladder can be climbed (after *The Runaway Kite*), so the
    first quest shows exactly three.
- **Prologue steps are no longer silent.** The quest tracker is revealed after *Morning Tide*, so until then:
  - the new-quest toast names the first step ("Pick up Herbal Tea 0/3");
  - each step forward shows as a toast ("Pick up Herbal Tea 2/3", ticked when done).

  New `QuestAuthority.steps_forward`.
- **Tests.**
  - `prologue_run`:
    - the hut's exit draws a door;
    - exactly three teas show, each as its icon;
    - each tea is counted as a step while the tracker is hidden;
    - all three are held at once.
  - `rules_tests` `text_suite`:
    - the fonts carry their weights;
    - small headings use the bold serif;
    - the minimum size holds;
    - Large text widens words and lines.
- Debug tools: `--text-size=0|1|2` previews at a text size.
- The Android preset is version 1.0.1 (code 101), so the rebuilt APK installs over 1.0.0.

### V9d3 · Weapon awakening and legendary chains (S47, v1.1+)
- **Weapon awakening.** A weapon can be awakened at any forge (the new Awaken section on the Forge's Enhance tab)
  when:
  - it is Heaven grade or better and at +10;
  - its family's Dao is at Explanation (tier 4);
  - you have a **Weapon Soul Crystal**, which is used up.
- An awakened weapon:
  - glows: a warm halo on the weapon side and gold motes rising in front of the body;
  - strikes on its own every so many blows with its family's skill: Sword Light (jian), Piercing Light (spear),
    Shadow Twin (short blade), Cleaving Wave (heavy sabre), Gale Leaf (fan), Echoing Note (flute), Twin Arrow (bow),
    or, as a ring around you, Thunder Knuckles (gauntlets) and Sweeping Gale (staff).
- New intent `awaken_weapon` and event `weapon_awakened` (a toast and a burst of light).
- *A Blade That Answers* (Smith Hong, Cloudgate Port, after the Ascension Gate) asks you to forge a Heaven weapon to
  +10 and gives the first crystal. After that, the Ironroot Clan Forge sells crystals for 900 spirit stones.
- **Legendary chains** (`legendary_chains.json`). There is one questline per weapon family, nine in all: bare fists
  have no weapon, so the Fist Dao's chain is the gauntlets'.
  - Each chain gathers three pieces. One comes from an old foe of the valley (the Drowned Abbot, the Riverbed Serpent,
    Big Toad Tan and the valley's elites). Two come from the Azure Expanse (its creatures at 12%, and the Thousand-Eye
    Toad, the Scarlet Kiln Warden and the Tomb King).
  - A piece drops only while its chain wants it.
  - An Expert smith makes the pieces whole at a forge (with Mystic ore and Refining Essence). The result is a
    Mystic-grade legend with a gift of its own.
  - Awakened at +10, a legend strikes with its own skill instead of its family's.
  - Smith Bao or Smith Hong gives each chain from the Ascension Gate on. The quest teaches the restoring recipe, and it
    ends when the legend is awake.
- **The nine legends:**
  - Stone Drum Gauntlets (Mountain Drum, a ring);
  - Riverlight Jian (Riverlight Cut);
  - Heron's Reach (Heron Strike);
  - Reedwhisper Dagger (Whisper Through Reeds);
  - The Ferryman's Pole (Pole the Current, a ring);
  - Mountainsplit Sabre (Split the Mountain, a ring);
  - Seven Winds Fan (The Seventh Wind);
  - Crane Mourning Flute (Crane's Lament);
  - Dragonfly Bow (Dragonfly Volley, three arrows).
- **Later steps.** Each chain lists its later steps, a Spirit-grade and a Sage-grade reforging in the Outer Heavens
  (v1.4 and v1.5). They are data only until those zones exist.
- **Art.** 28 new icons: the nine chains' pieces (a hilt, a fragment and a caged heart, in each legend's colour) and
  the Weapon Soul Crystal. The legends use the Mistjade weapon art of their family.
- **Code.** The Artifact Spirit's skill and a weapon's awakened skill share one strike: projectiles that pass through
  every foe in their path, or a ring around the wielder.
- **Tests.**
  - The new rules suite covers:
    - the awakening gates (grade, +10, Dao tier, crystal, forge), one awakening per weapon and the flag;
    - the family skill on its count, and Smith Hong's +10 flag;
    - the nine chains and a chain's quest shape and Expert recipe;
    - the gated piece drop, a legend's gift and own skill, and a ring skill.
  - Data validation checks every chain's weapon, pieces, sources, recipe, quest and later steps, and every
    family's awakening skill.
- Debug flag: `--awaken=item[:awake]`.

### V9d2 · Artifact Spirit depth and imitation relics (S47, v1.0 and v1.1)
- **Affinity.** A bound relic's spirit, asleep or awake, has an affinity meter (0–100) saved on the blade.
  - **Use** feeds it: one point for every 25 blows the relic lands in your hand.
  - **Gifts** feed it: three a day, on the Bag page (Refining Essence 10, Mist Lotus 6, Cloudsteel 4, Jadeiron 2).
    Each spirit's favourite counts double: Mist Lotus for the Moon Spirit, Refining Essence for the Blade Spirit.
  - Affinity raises an awake spirit's gift and skill by up to half again.
- **Waking is a quest per relic.**
  - A spirit answers the soul contest only once it knows your hand (affinity 30), and only where it once slept.
  - *The Blade That Sleeps No More*: the Sleeping Blade wakes in the Abbot's sanctum.
  - *Moon on the Water*: the Moonlit Blade wakes at the Lake Shrine on Mirrorwater Lake.
  - Elder Hu offers each quest once the relic is bound. The quest steps follow the flags `bound:`, `spirit_close:`
    and `spirit_awake:`.
- **Skills.** An awake spirit strikes on its own:
  - the **Moonlit Crescent**, a Qi crescent of moonlight every 8 blows (160%);
  - the **Waking Edge**, a flying edge every 10 blows (220%).
  - Each goes through every foe in its path and is weighed by the spirit's power.
- **Control demand.** An awake spirit needs Spirit at or above its demand: 60 for the Moon Spirit, 80 for the Blade
  Spirit. Below that it gives half its gift, keeps its skill to itself, and says so when you take it in hand.
- **Devour.** Held in hand, the spirit eats a weaker weapon of its own family: a lower grade, or the same grade at a
  lower item level. It will not eat a locked, natal or relic weapon.
  - Each meal adds spirit XP (by grade: 2, 4, 8 or 16) and 2 affinity.
  - Levels 1–5 come at 10, 30, 60, 100 and 150 XP, and each adds 10% to the gift and skill.
- **Barks.** Each spirit has its own one-line barks, for waking, kills, gifts, meals, low health, and refusing a weak
  hand.
  - A line shows in a violet-edged bubble over your head and in the log.
  - Kills speak one time in four, with 40 s of quiet between lines. Waking, gifts, meals and refusals always speak.
- **The Bag page** shows the spirit's affinity and level and what it still needs. It has Subdue, Gift (the best gift
  you carry, favourite first) and Devour (the weakest candidate) for the relic in hand.
- **Imitation relics** (v1.1). Expert smiths forge copies that keep 60% of a boss relic's gift, always on, with no
  binding, spirit or control demand:
  - the **Moonshadow Jian** (+4.8% Qi Attack, from the Moonlit Blade);
  - the **Drowsing Edge** (+6% crit damage, from the Sleeping Blade).
  - Their recipes are sold at the Stoneford Smith (2,400 taels) once you have bound the original.
- New events:
  - Inventory: `spirit_affinity_changed`, `artifact_spirit_spoke` and `artifact_spirit_grew`;
  - Combat: `artifact_skill_used`.
- Tests:
  - The new rules suite covers:
    - affinity from use and gifts, the daily cap and the favourite;
    - the waking gates (affinity and place) and the quest flags;
    - the gift growing with affinity, devouring (family, locks, levels) and the skill every tenth blow;
    - the control demand halving the gift and silencing the skill, and the barks' quiet;
    - the imitation's 60%, and its recipe and scroll gates.
  - The valley run now wins the Blade Spirit's trust with two gifts and wakes it in the Abbot's sanctum.
  - Data validation checks every relic spirit's fields, barks and awakening quest, and every imitation's share.
- Debug flag: `--relic=item[:awake[:affinity]]`. `--open-page=inventory:weapon` opens the Bag on the worn weapon.

### V9d1 · The sword swarm, Array Plates in a fight, and the combat puppet (S47, S48, v1.1)
- **The Sword Swarm** is the Sword Dao's fifth tier. It is a toggle technique (30 QI, 30 s cooldown).
  - Swords of Qi orbit you for 12 s and take turns striking the nearest foe within 420. There is one strike every
    1.2 s divided by the number of swords, each at 0.9 ÷ √n of your attack, so more swords add damage but not in
    proportion.
  - **How many swords:** 3 at Sword Dao 5; 9 with the **Nine Swords Array** (released, or set in a Treasure slot);
    36 with the Array at Original Application (tier 6).
  - **Spirit is the control demand:** you can steer one sword for each 10 Spirit.
  - The **Nine Swords Array** is a new treasure (60 QI, 45 s cooldown; the swarm lasts 12 s). Its recipe is a
    heaven-grade smithing recipe for an expert smith. The scroll is sold at the Ironroot Clan Forge for 60 spirit
    stones.
  - The swords orbit your chest, riding or on foot. The near half of the ring is drawn over the body.
  - **Deviation:** the swarm's swords are the flying sword's seeking projectiles, not one pet-style actor per
    sword. This keeps 36 swords cheap and uses the Sword Release rules already tested.
- **Array Plates in a fight.** A plate from the bag lays an array at your feet for a few seconds. Arrays stay in
  the room they were laid in.
  - **Guarding array** (the old Array Plate): +15% Physical Defense while you stand inside its ring, for 12 s.
  - **Killing array** (new): every foe inside takes 50% of your Qi Attack each second, for 10 s.
  - **Binding array** (new): every foe inside is slowed by 40%, for 10 s.
  - **The Formation Dao scales them.** From tier 1 an array lasts 10% longer, and each tier makes the killing array
    20% sharper. Each plate laid teaches the Formation Dao 3 insight.
  - The two new plates are formations recipes: a blank plate and a formation stone, plus two ore dust (killing) or
    two willow moss (binding). *Carry a Wall* teaches all three plates.
  - Each array is drawn in its plate's colour with its own centre: trigram bars (guarding), four blades pointing
    inward (killing) or a turning chain (binding).
  - New events: `array_deployed` and `array_faded` (world FX and sound).
- **Formations placed in the world:** from Formation Dao tier 1 they hold 10% longer, and each placement teaches the
  Dao 5 insight.
- **The combat puppet** (S48; from Cloud Stride 5, when puppetry opens).
  - Tinkerer Yu builds it at the Stoneford bench from 8 spirit wood, 2 puppet cores and 4 jadeiron. You can own only
    one.
  - It takes a pet slot and fights beside you. It is a construct: it is built full-grown, and it has no traits,
    bloodline, hunger or bond. It cannot breed, fuse, evolve, break through or devour cores, and it only takes the
    combat role.
  - Three knockouts break it, as they wound an animal. A Beast Revival Pill or a rest does not mend it; the
    tinkerer repairs it for 2 spirit wood (the new Repair button on the Puppets tab).
  - The Spirit Animals page shows it as a Construct, with what it can and cannot do, in place of food, traits and
    growth.
- Four new icons: the killing and binding plates, the Nine Swords Array and the Sword Swarm.
- The new rules suite covers:
  - the swarm: its counts, the Spirit cap, Sword Dao 5 teaching it, the toggle and its QI, strikes without a
    button, recall, the time running out, and the treasure release;
  - the arrays: the guarding defence, the killing damage, the binding slow, the Formation Dao scaling, fading, and
    leaving the room;
  - the puppet: the build, one only, no food, only the combat role, no breeding or growth, not mended by pills,
    and the paid repair.
- Debug flags: `--swarm` and `--arrays`.

### V9c3 · Sect role variants and the sect tree (S48, v0.9)
- The Sect page has a new **Role** tab, open from Outer Disciple.
- **Signature lines.** Each sect has one, and each line has a damage and a support variant. The first choice is
  free; changing it costs 50 contribution.
  - **Jade** (Flowing Palm, Palm Wave, Rising Tide):
    - Surging Tide: +25% damage.
    - Mending Current: each use heals you and every ally within 220 by 4%, and slows each foe hit by 20% for two
      seconds.
  - **Cloud** (Jade Thrust, Spear Lance, Dragon Tail Sweep):
    - Piercing Peak: +20% damage, one more target, +10% penetration.
    - Guarding Cloud: a shield of 8% of your health for 4 s, and allies within 220 healed by 3%.
  - Support healing grows with the crafts you have ranked up: +5% per rank step, up to +50% (v2's
    `profession_rank_up` → sect roles).
- **The sect tree**: three branches of five nodes, bought in order with contribution (60, 120, 200, 320, 480). The
  third node needs Inner Disciple and the fifth Core Disciple. Each sect names the branches its own way.
  - Edge: attack, crit damage, signature arts ready 1 s sooner, signature arts +15% damage.
  - Lotus: healing received, QI recovery, the support variant heals half again as much, signature arts cost 20%
    less QI.
  - Root: max HP, Physical Defense, Qi Resistance, Tenacity, guard.
- New events: `sect_role_chosen` and `sect_node_bought` (HUD; stats refresh when a node is bought).
- The new rules suite covers the rank gate, the free first choice and the paid switch, the variant limited to the
  line, the support heal and its craft scaling, buying in order with its rank and contribution gates, the tree's
  flags, and the Cloud shield. Debug flag: `--join=sect[:rank]`.

### V9c2 · The Blood path and the Buddhist path (S48, S49 alignment)
- **The Blood path** (v1.1) is an opt-in for a demonic heart. It never locks anything else.
  - Take it on the Cultivation page's new **Paths** tab (the Vows tab, renamed), from Heart Tempering 1 at alignment
    -20 or lower. Taking it costs 10 alignment and 20 of the training sect's regard, and opens the Blood Dao.
  - Leaving it adds 10 heart demon.
  - While on it: the heart demon grows twice as fast; every hit drinks back 3% of its damage (+1% per Blood Dao
    tier, twice that for Blood arts); kills fill a blood-essence meter (10 a foe, 25 an elite, 50 a boss, up to
    100; it drains after 20 s without a kill). A thin crimson strip under the HUD bars shows it.
  - **Three Blood arts**, sold by Peddler Shao at night to the demonic side only. Each spends health, and blood
    essence pays first (one point per 1% of health). Each use costs a point of sect regard:
    - Crimson Palm (5%, Heart Tempering 1);
    - Blood River Slash (10%, Heart Tempering 5);
    - Sanguine Lotus (15%, Cloud Stride 1).
  - **Sect regard** now shows on the Sect page. Below zero, the Mission Hall lends no technique manuals (the new
    `reputation_at_least` requirement).
- **The Buddhist path** (v1.1):
  - **Golden Body** (Heart Tempering 3): for a vow-keeper only, +25% Physical Defence and Qi Resistance and +15%
    healing received for 10 s. The Mission Halls lend it to the upright (alignment 20, merit 50).
  - **Merit milestones calm the heart**: each hundred merit a vow-keeper crosses takes 10 heart demon away.
  - **Healing an ally is merit**: Clear Heart Melody reaching a companion or pet gives +1 merit, five times a day.
- The Paths tab shows three cards (the Blood path, the Buddhist path, the Poison Body) above the vows.
- New event: `path_changed` (HUD). Four new technique icons.
- The new rules suite covers:
  - the alignment gate, the costs of taking and leaving the path, and the path surviving a save;
  - the doubled heart demon, the Blood arts' costs paid from blood essence, the essence gains and drain;
  - lifesteal, and the sect-regard gate on manuals;
  - merit milestones, the daily healing merit and the Golden Body's vow gate.

### V9c1 · The Soul line, the Poison path and the meridian gates (S48, S10)
- **The Soul line** (S48, v1.0). The Soul Dao's first three tiers each teach a technique:
  - **Sense Lock** (tier 1): fixes your Spirit Sense on one foe within 420 for 8 s. It cannot evade you and cannot
    hide (a burrower stays in sight).
  - **Phantom Double** (tier 2): leaves an illusion where you stand for 6 s (+1 s per Soul Dao tier). Foes within
    500 hunt it until it has been struck three times; bosses see through it. The world draws it as a pale copy of
    you (`illusion_cast` and `illusion_broken`).
  - **Soul Search** (tier 3): a spike into an elite or boss that ignores armour. If it dies within 12 s you read a
    memory from its soul (ten new Codex pages) and find what it hid: one more loot roll (`soul_searched`).
- **Spirit as a main stat.** Soul attack now scales with Spirit and Insight (+0.8% and +0.4% a point) whatever the
  weapon, on top of Spirit's +0.5% soul attack.
- **Soul Lantern Ward** now works: a shield of 20% of max Soul for 6 s. Before, it set a stat nothing read.
- **Teachers for the mentor's techniques.** Three techniques had no source:
  - Elder Hu teaches Mirror Mind Spike in "A Lake Inside" (Spirit Awakening 1);
  - Soul Lantern Ward in "The Mentor's Gift" (Spirit Awakening 5);
  - Still Water Focus in "Brothers in Arms" (Heart Tempering 6).
- **The Poison path** (S48, v1.1).
  - Peddler Shao sells two poison arts at night: Venom Needles (three seeking needles that poison, Qi Unfurling 1)
    and Miasma Palm (poisons every foe within 160, Heart Tempering 1).
  - **Poison Body**: with a poison art known and toxicity past half your tolerance, each hit turns a point of your
    own toxicity into poison on the foe (2% of its health a second for 4 s, once per foe each half second). A HUD
    icon shows while it is open.
- **The S10 meridian gates, completed.** Ten of the fifteen gates had no effect; all now work:
  - Agility 50: a second dodge charge.
  - Essence 25: the first technique of each fight costs no QI. A fight starts after 8 s without a blow.
  - Essence 50: flight costs 20% less QI.
  - Essence 100: Qi projectiles pierce one more foe (flute notes too).
  - Spirit 25: the Sense pulse costs 25% less.
  - Spirit 50: fear and confusion from weaker foes do not take.
  - Spirit 100: soul attacks ignore 20% of Soul Defence.
  - Insight 25: one free affix reroll a week (the Forge says so).
  - Insight 50: insight stones give double.
  - Insight 100: a Dao at Explanation or above gives one more tier's effect.
- New art: five technique icons and two status icons (Sense Locked, Poison Body).
- The new rules suite covers:
  - the grants and the Soul Dao's teaching;
  - Spirit scaling and every gate at its threshold;
  - Sense Lock against an evasive foe;
  - the illusion (drawing foes, breaking, fading) and Soul Search on elites only;
  - the ward, the Poison Body and the peddler's stock.

  Debug flag: `--illusion`.

### V9b · Weapon families: the heavy sabre, the fan and the flute (S47 v1.1, the Music path)
Three new weapon families, each with seven grades (Training to Sunsteel), smithing recipes, icons, avatar art in every
animation, a stance, two techniques and a Dao.
- **The heavy sabre** (Blade Dao, Body).
  - It is slow (0.75 hits a second) and its cleave strikes up to three foes in a line.
  - Every blow may break armour (30%; always on the third stroke). A **Sundered** foe takes every hit through a
    quarter of its defence for 4 s.
  - Its stance is Iron Ox: twice the armour-break chance, 10% slower on foot.
  - Techniques: Mountain Cleaver and Thunder Dao Arc.
- **The fan** (Fan Dao, Agility and Insight).
  - Its wind reaches 140. The third stroke throws the fan 280 units out and back, cutting everything both ways.
  - A foe the wind catches is **launched**: it rises in an arc and can neither move nor strike for 0.8 s. Bosses,
    flyers and immovable foes are not launched.
  - Its stance is Drifting Cloud (+15% reach).
  - Techniques: Gale Fan, and Returning Crane Fan (a thrown fan that returns).
- **The flute** (Music Dao, Insight and Essence).
  - A tap sends a note of Qi 240 units.
  - **Hold Attack** (0.35 s) to play a melody. Every half second it slows the foes within 220 by 30% and may
    confuse them (8%). You recover 1% of your health a second, and every companion and pet in the circle 2%.
  - Composure pays for it at 8 a second. It needs Composure (Qi Unfurling) and ends when you let go, when Composure
    runs out, or when you are stunned, wounded, attack, fly or change rooms. You walk at half pace while playing.
  - Each Music Dao tier carries the melody 5% further. Its stance is Clear Note (a third less Composure).
  - Techniques: Reed Song (three seeking notes) and Clear Heart Melody. Clear Heart Melody now heals the caster and
    every ally within 220 by 4% a second for 6 s, in a fight too.
  - New events in the contract: `melody_changed` and `melody_pulse`. The HUD notes a melody broken or spent, and
    the world draws a jade ring and rising notes.
- **Monsters now answer Fear and Confusion.** A feared monster runs from its foe and a confused one stumbles back
  and forth; neither attacks until it ends. Stun, root and the fan's launch already held them.
- **Getting them.**
  - The Stoneford Smith sells the training and iron grades; the jade-iron grades join its rotation.
  - The Inner Disciple quest teaches each family's Qi technique.
  - The Mission Halls now lend every library technique (library 1 to 3, and the Cloud library for Cloud
    disciples) as a Technique Manual for contribution. Until now these had no source.
- **Art.** Sabre, fan and flute avatar sheets are baked for every action and both facings (`tools/art/bake_weapons.py`).
  They were reviewed in every animation, with plain and dyed robes. New art: equipment and technique icons, HUD
  glyphs, and note and fan projectiles.
- The new rules suite covers:
  - the cleave, Sundered and launch;
  - the returning throw and the note;
  - the melody (slow, heals, drain, release, running dry);
  - Fear, Clear Heart Melody and the Mission Hall manuals.

  Debug flags: `--wield=item`, `--foe=enemy[:count]`, `--melody` and `--throw`.

### V9a · v2 hooks: rule kinds, the treasure-birth pillar, world-event markers and the pet command wheel
A sweep of every v2 audit row against the build after V8g3 lists what v2 makes due by v1.1 and is still open. It
is planned as V9a–V9f in `docs/v2_audit.md`. V9a covers the small hooks:
- **Rule kinds.**
  - New requirements: `heart_demon_at_most` and `foundation_share_at_most`.
  - New effects: `grant_fate` (a fate given as if chosen, leaving any offer alone) and `absorb_flame` (a Heavenly
    Flame given outright).
  - Aliases for v2's names: `art_known` for the secret-art requirement, `grant_art` for learning one.
  - Data validation now reads every alias on a rule line.
- **Treasure births.** World announces each Spirit Fruit ripening (`treasure_birth_announced`, with its room and
  fruit) and the HUD logs it. On the minimap the tree stands up as a pulsing pillar of light while it is ripe.
- **Other minimap markers.** Spirit mines show as a diamond: jade when yours, the holder's colour when not.
- **World map markers.** Each region with a world event gets a diamond: gold and glowing while the event is under
  way, violet while it is coming. The region's panel names each event and its room.
- **The pet command wheel** (v2 HUD). Hold the Pet button (0.45 s) and drag to a choice; a tap still opens the page.
  The choices are:
  - Follow;
  - Stay, which holds its spot and only fights what comes close;
  - Attack, which reaches to 600 instead of 260;
  - Hold back, which never fights;
  - Ride or Dismount;
  - the Pet Bag.

  The order is kept for every animal out with you and for new ones called (`pet_commanded`, now in the contract).
  The active order has a gold ring.
- **Settle foundation** shows as a seclusion focus only once pills make up more than 20% of this realm's foundation
  (the v2 unlock timeline), or while it is the focus.
- **The depth-hooks suite** (v2's test list). A new character carries every S44–S49 field, neutral. Non-neutral
  values of every one survive a save as JSON and a restore. The account's calendar, activity and sect (with its
  mines) round-trip too. `docs/v2_audit.md` records where the build's names differ from v2's.
- New rules tests cover the rule kinds, the announcement and the wheel. Debug flag: `--pet-wheel`.

### V8g3 · The living world: territory and spirit mines (S49)
- **Spirit-stone mines** (`territory.json`). There are five, each a vein in a field room with sacks, a barrel and
  the holder's banner beside it:
  - Lower Pit Seam, Stonewall Quarry: Level 9, 1 stone an hour.
  - Grey Pools Seep, Reed Marsh: Level 14, 2 an hour.
  - Rapids Terrace Vein, Whitewater Gorge: Level 32, 3 an hour.
  - Lightning Scar Lode, Thunderhorn Plains: Level 66, 6 an hour.
  - Glass Dunes Lode, Sunscar: Level 75, 8 an hour.
- **Three rival sects** hold the mines at first:
  - Ironpine Gate: spearmen in ochre.
  - Blackreed Hall: veiled marsh-folk in ink.
  - Scarlet Kiln Sect: forge-cultivators in crimson.

  Each sect has its own disciples, a named warden and a banner. The six new enemies use existing avatar parts and
  dyes only. The four banners are new props, one for each rival and one for your own sect.
- **Taking a mine** (`assault_mine`). This extends the S25 defence waves into offence.
  - Survey the vein and choose *Take the mine*. Three guards stand at the vein at the mine's Level, more come while
    they fall, and the warden stands three Levels higher.
  - Bring the warden down within two minutes and the mine is yours, with +30 Prestige (`mine_claimed`).
  - Your sect can hold one mine, plus one more at every third sect level. Each mine also needs its own sect level.
- **Production.** A mine you hold fills its carts with its rate every hour, up to a day's worth. Collect at the vein
  or on the Territory tab (`collect_mine`) for Spirit Stones and 1 Prestige per stone (`mine_collected`). Only whole
  stones leave the carts.
- **Contests on a timer.**
  - Every two to four days the old holder comes back (`mine_contested`). The timer is seeded by the account and
    runs offline.
  - A toast and a phone notification (the Defence category) give you twelve hours. Hold the mine in person: survive
    a minute of waves, with the warden joining after 20 seconds (`defend_mine`).
  - If you do not come, the guards you posted decide it when the window closes. The chance is 30%, plus 15% for each
    guard and 1% for each of the guard's Levels.
  - A held mine pays +20 Prestige (`mine_defended`). A lost one goes back to its holder with whatever was in the
    carts (`mine_lost`).
- **Guards** (`guard_mine`). Post up to three disciples at each mine. A disciple on guard cannot go on an
  expedition, and one on an expedition cannot stand guard.
- **The Territory tab** on the Your Sect page lists every mine with:
  - its banner, room, Level, rate and needed sect level;
  - its holder, or its carts and when the rivals come;
  - its guards and their chance to hold it.

  It has Collect, Post guard, Recall and Go buttons. Go walks you there by quest auto-path.
- Fixes:
  - An expedition now sends two disciples who are home. Before, every expedition sent disciple 0, because the page
    passed names where the rule wanted indices.
  - The "back" label is now a string, not a literal.
- New rules tests cover the data, the assault and its guards, the cap, the carts and their limit, guards and
  expeditions, the contest timer, holding the mine in person, and losing it with its carts. Debug flags:
  `--mine=id[:contested]` and `--assault=id`.

### V8g2 · The living world: the mortal kingdom and leisure arts (S49)
- **The County Hall** (`sf_county_hall`). It is a new room behind Stoneford Gate. Its door is under a roof that a
  rope bridge joins to the gatehouse.
  - Magistrate Qian, a new NPC made only from existing avatar parts, keeps the hall.
  - The hall has the county job board and the locked relief box. Either one, or the magistrate's "County business"
    service, opens the new County page.
- **County jobs** (`relations.json` `mortal`, Relations authority).
  - Each day, three jobs are drawn for the character from four boards: vermin, raiders, relief deliveries and
    letters. Each board offers only jobs that suit the character's Level.
  - Reading the board accepts the jobs. They show on the Quests page's Daily tab, and yesterday's unfinished jobs
    are taken down.
  - A job pays silver by Level, 10 county favour and the `county_service` deed (+3 merit).
- **County favour** has four named tiers: Stranger (0), Known at the Hall (50), Friend of the County (150) and
  Benefactor (400).
  - The last two grant the county's titles, *Friend of the County* and *Benefactor of Stoneford* (coin find).
  - A Benefactor pays 5% less in Stoneford's shops.
  - The HUD announces a new tier (`favour_changed`).
- **The relief fund.** You can give 100, 1,000 or 10,000 silver, each size once a day (`donate_relief`,
  `relief_donated`). The gifts pay 1, 8 or 60 merit and 3, 30 or 200 favour; the largest also adds Fame.
- **Non-interference.** From Qi Kindling up, using a technique in a mortal town (Lotus Ferry's village or Greyreed
  Hamlet) is the `mortal_interference` deed: +5 sin and -2 alignment, at most once a minute. The magistrate warns
  you about it. In the wild, a technique carries no penalty.
- **Leisure arts: the guqin.** A seven-string guqin is sold at the Stoneford Tea House. Play it from the bag and the
  new Guqin page opens: a short rhythm piece of 16 notes on five strings.
  - Tap the strings, or press 1 to 5, as each note reaches the line. PERFECT and GOOD windows score the playing.
  - A clean piece makes meditation up to 15% faster for 30 minutes, and never less than 5%. Then the hands rest as
    long (`play_guqin`, `guqin_played`).
- **Leisure arts: chess** (`chess.json`, six Go problems on a 9×9 board).
  - Every insight stone offers a chess problem as well as meditation. Each site has its own problem for the day,
    the same on every device. Each problem has four lettered points, and only one is right.
  - The new Chess page gives one answer a day at each site. The right point gives insight into your deepest Dao, or
    a little realm progress before you have one (`solve_chess`, `chess_solved`).
  - The fortune deck's Hermit's Chess Problem now uses the same rule.
- **Regional teas.** Each tea house pours its own tea, with a new icon for each:
  - Jasmine Dew (Stoneford): +10% insight for 30 minutes.
  - Marsh Mist (Greyreed): +8% evasion.
  - Thunderhead (Cloudgate Port): +2 Storm Ward.
- New rules tests cover the jobs, the favour tiers, the titles and discount, the relief fund's limits,
  non-interference in towns and the wild, the guqin's bonus and rest, and the chess problems.

### V8g1 · Mobile conventions: idle-room eligibility, auto-hunt and quest auto-path (S49)
- **Idle rooms.** Idle Hunt and Gather now run only in rooms that list them (`room.idle`, the S23 Hunt rule). A
  town or a dungeon refuses them, with the reason, and the Characters page greys those buttons out there. Saves that
  set an idle hunt somewhere else gain nothing from it. Rest, seclusion and training still go anywhere.
- **Auto-hunt** (`set_auto_hunt`). A small **AUTO** toggle sits under the icon row, shown only where idle Hunt is
  allowed.
  - It is off in towns, trials, dungeons, boss dens and story instances. It switches itself off when a room event
    starts, a boss appears, a tribulation begins or health falls below a fifth.
  - Your character closes on the nearest foe along the room's navigation graph (walking, jumping, climbing,
    dropping). It fights with basic attacks and the equipped techniques, and picks up the drops between fights.
  - It never uses treasures, pills or breakthroughs. Touching the joystick takes over.
- **Quest auto-path** (`auto_path`). A small ➤ button beside each tracked quest walks you to where it leads, or to
  the hand-in NPC's room once it is ready.
  - `WorldRules.route` finds the fewest rooms through the portals open to this character (realm, quests, arts,
    hidden ways found). It also crosses the Starsea by boarding from a dock, and stops there, saying why, if you
    have no vessel or chart.
  - Within a room, the autopilot follows the navigation graph, then presses up at a door or walks out through an
    edge.
  - It stops at danger (the first blow), when you touch the joystick, or on arrival. Verified live: Willow Path West
    to Market Street through Stoneford Gate.
- New tests:
  - Data validation checks that every quest target is reachable from its giver without movement arts the
    character has not been taught (the Breath Control grotto stays closed to it).
  - Rules tests cover the idle-room rule, auto-hunt refusals and cut-offs, routes, the portal to take, stopping at
    danger, arriving, and the Starsea dock.
- Debug flags: `--auto-path=room`, `--auto-hunt` and `--wait=s` (let them run before the capture).

### V8f · The living world: the Heaven Ranking, the Trial Tower and daily activity chests (S49)
- **The Heaven Ranking** (`rankings.json`, Part 8's valley seeds). It is a tab on the World map. The seven ranked
  cultivators are:
  - Shen Lian and Wen Zhao;
  - Yun Zhiqiu and Bai Yuheng, the first disciples of the Cloud and Jade Sects;
  - "Iron Crane" Guo Ming, a rogue cultivator;
  - Captain Lou Chen, Madam Hua's guard captain;
  - Chief Yan Bo of the Gorge Bandit Adepts.
- How the ranking moves:
  - Each ranked cultivator climbs a set number of Levels every week of the account calendar, up to a ceiling. A
    seeded wobble keeps the order moving, and the table is the same on every device.
  - The Calendar announces a new order (`ranking_changed`), and the tab shows who rose or fell since last week.
  - You enter at the top eight by CP, or by reaching the Valley Tournament finals.
  - You can challenge the cultivator directly above you to a spar at their Level. Win, and you hold their place for
    the rest of the week and gain 15 Fame. Four new duelists use existing avatar parts only.
- **The Trial Tower** (`tower.json`, Part 8): thirty floors inside a pagoda at the Stoneford Fairground, Levels 4
  to 62, all in one new room.
  - Each floor is a room event with one of four rules:
    - **Clear**: defeat four foes in 90 seconds.
    - **Swift**: defeat three in 45 seconds.
    - **Survive**: hold out while waves come.
    - **Guardian**: every fifth floor, bring down its guardian and escort.
  - Clearing a floor for the first time pays Spirit Stones and opens the next floor.
  - The Tower page (at the pagoda's board or the stele inside) lists every floor with its rule, foes and rewards.
  - **Sweep** gives each cleared floor's loot once a day, straight to the bag (`sweep_floor`).
- **Daily activity chests** (`activity.json`, Account):
  - Points come from missions, dungeon clears, crafts, harvests, spars, tower floors, arena fights and the Beast
    Trial Grove. Some sources have daily caps.
  - The points fill four chests at 20, 40, 60 and 100, for the whole account, and reset each day.
  - A bar with the chests sits on the Quests page's Daily tab (`claim_activity_chest`). The HUD says when a chest
    is ready.
- Debug flags: `--tower=N`, `--climb=N` and `--activity=N`. New tests cover the tower, sweeps, the chests and the
  ranking.

### V8e · The living world: fortune encounters, heavenly phenomena and lifespan (S49)
- **Fortune encounters** (`fortune_deck.json`, Part 8's eight vignettes). A card can turn up when you enter a room,
  gather, or recover from a fall into the void. It appears as a card at the top of the screen.
  - **The Fortune meter** (Relations) fills over three hours of play and holds one encounter, so encounters cannot be
    farmed. It starts empty, and the Karma tab shows how long it has left to fill.
  - Fortune raises the chance and every card's weight. Merit makes the kind cards likelier. Draws use the
    character's own fortune stream.
  - The cards:
    - A **Hidden Cave**: a fall ends in the Hidden Grotto, a new unmapped room. Its old chest fills again for each
      such fall, and the way up leaves you where you fell.
    - A remnant soul in a ring: three manual pages.
    - The hermit's chess problem: insight into your deepest Dao.
    - A wounded crane: +2 bond with your Jade Crane, and a little merit.
    - A jar of **Hundred-Year Wine**: pour it over the furnace and your next Perfect batch has +25% chance to come
      out Grain.
    - A lost child walked home: +10 merit.
    - A meteor fragment of Cloudsteel.
    - A **Dream of the River** (a Codex entry, once).
  - Debug flag: `--fortune=<card>`.
- **Heavenly phenomena**. The Calendar announces each one:
  - A major breakthrough gathers golden clouds and a pillar of light over the room.
  - A tribulation darkens the room with a storm bank and bolts.
  - People nearby call out, in congratulation or alarm.
  - Where people saw the clouds, a **jealous senior** (Senior Brother Hao Qian) may challenge you to a spar at your
    new level, for Fame.
  - Debug flag: `--phenomenon=cloud|lightning`.
- **Lifespan as flavour** (display only, never a clock):
  - Each great realm grants a span, from 80 years for a mortal to 1,200 at Sage, and without end at World Genesis.
  - Characters start at sixteen and age a year every four weeks (a season a week).
  - The Character page shows your age and lifespan, and the gift page shows named people growing older with you.
  - Longevity treasures add years. A **Longevity Peach** (+10) is sold at Auction Day. A **Thousand-Year Lingzhi**
    (+30) is your master's parting gift in The Elder's Last Lesson, with a Codex entry on years.

### V8d2 · The living world: Auction Day, Spirit Fruit births, the Herb Terraces trial and weather (S49)
- **Auction Day** (Part 8): every Saturday an auctioneer's stall stands on Market Street. It shows only while the
  calendar event runs.
  - The valley house is a second auction beside the Pavilion's. It offers five lots at a time from rare seeds,
    spirit eggs, manual pages and recipe scrolls, for Spirit Stones. Every lot closes when the day ends.
  - Winning a recipe scroll teaches the recipe at once, and a letter confirms it.
  - The Pavilion auction is unchanged. Its lots, seeding and saves are as before.
- **A Spirit Fruit ripens** every fourth day for six hours, under a glowing tree in one of the valley's dry field
  rooms.
  - Reach for it and the room's beasts withdraw. Two rival cultivators and the Fruit-Guardian Boar, two levels
    above the room, stand in the way.
  - Beat all three and the fruit is yours, once per birth. Eating it gives 8% of this realm's progress, and heart
    demons fall by 5.
- **The Herb Terraces Trial** runs every Wednesday on the Jade Herb Terraces. Every herb you gather there while it
  runs counts against five of the valley's gatherers, whose scores come from a seeded draw.
  - The ranking pays out once, when the day is over. The top three learn the Foundation Guard Pill, and the top
    two also receive pills.
  - The Calendar page shows your standing while the trial runs.
- **Weather effects** (never gating):
  - Rain widens the fishing bite window and adds 10% gathering power.
  - Fog adds 5% evasion.
  - A storm adds 10% elemental power to Thunder techniques.
  - The effects apply when you enter a room and change with the sky. Rain and storms draw streaks and a grey tint
    (storms also flash), and fog drifts over the room.
- Debug: `--event=<id>` moves the clock to an event's next opening, and `--weather=rain|fog|storm` previews a sky.

### V8d1 · The living world: the world calendar, spatial rifts and reopenings (S49)
- **Calendar authority** (new, account level). The schedule is pure (`CalendarRules`): it comes from the account
  seed, the account's first day and the UTC clock, so the same save shows the same calendar on any device.
  - Draws come from `Rng.keyed`, which is stateless and never moves a gameplay stream.
  - The authority announces events a day ahead (a notification through the Notifier), when they start and when
    they end, the season and the weather.
- **calendar.json** (`tools/data/living_world.py`):
  - A **Spatial Rift** every three days for an hour, in one of the valley's seventeen field rooms. Its violet tear
    shows only then. Touch it and the room's beasts pour out three levels stronger for a minute; survive, and it
    leaves a chest's roll at your feet (once per rift).
  - **The Drowned Shrine Surfaces** every fifth day, for a day. After its first defeat the Drowned Abbot wakes
    again only then, at Qi Unfurling 9 and below.
  - **The Waterfall Cave Opens** two days later on the same rhythm. A new inner cache fills once per opening,
    at Heart Tempering 9 and below.
  - First visits, the story entry and the vault are never behind the cycle.
  - The weekly Beast Tide shows on the calendar too.
- **Seasons** now run from the account's first week, spring first. Saves from before this keep the old count.
  The account gains `created_utc` and a `calendar` block.
- **Weather** (v1.1 groundwork): a seeded pick every three hours for Reedmarsh and Whitewater Gorge (rain or fog)
  and Summit Ridge (storms or fog). Those rooms carry their region. Effects and visuals came in V8d2.
- **Calendar page** (a new Menu entry; the Menu is now seven tiles wide): the season and its days left, the
  weather by region, this week's Beast Tide, and every world event with when, where and whether its repeat runs
  are open to you.
- New requirement kinds `world_event_active` and `world_event_here`; chests that `reopens` with an event.
- **Events:** `world_event_scheduled`, `world_event_started`, `world_event_ended`, `season_changed`,
  `weather_changed` and `rift_opened`, with HUD notes.
- **Tests:**
  - the same save gives the same calendar, and another seed moves the rifts;
  - each rhythm and duration;
  - repeat runs open and capped, while the first defeat is never gated;
  - the cache is keyed to each opening;
  - the rift tear, its once-per-rift rule and its +3 levels;
  - spring first from the account's week.

### V8c · The living world: grudges, hunters, bounties, mercy and named debts (S49)
- **Grudges** (factions.json) against three factions:
  - the Mudwater Bandits (hunters at 30; 200 taels, or a duel with Tan the Younger);
  - the Gorge Bandits (hunters at 30; 400 taels, or the new quest **Old Scores**: a fair fight with Chief Yan Bo
    at the Gorge Mouth for Trader Min);
  - Elder Gu's Stoneford Smugglers (hunters at 50). Theirs is story-bound: +20 for the cargo, +20 for the hidden
    cargo, and gone for good when the warehouse falls.
- **Grudge rules**:
  - Only named kills raise a grudge (+15), such as Big Toad Tan, the lieutenant and bounty targets.
  - Past the threshold, a hunter may be waiting in the faction's grounds (35%, at most every 30 minutes), at your
    level: a Mudwater Cutthroat, a Gorge Stalker or a Gu Family Enforcer.
- **Bounties** on the town board's new Bounties tab: One-Eye Pang (Caravan Road), Ferryman Lou (Bend Shore) and
  Knife-Hand Sui (Echo Cliffs).
  - You can hold two at a time, and take each one once a day. The target waits in its room while the bounty is
    yours.
  - Claiming pays taels and +10 Fame, and a bounty target is a named kill.
- **Mercy** (Part 8): Lieutenant Kuai, who now guards the Mudwater loot cave, yields at a fifth of his health. He
  kneels and cannot be struck. You judge him on the Mercy page, or with the Judge button when you stand near him.
  - Spare him: +10 merit. Before Gu's warehouse his warning arrives, with three Thunderclap Pellets.
  - Finish him: +15 sin. His brother Kuai Shan then waits for you on the Caravan Road.
- **Named debts** (Part 8):
  - Debts can now fall due with a quest as well as with time.
  - A debt can send a letter, set a flag or post a hunter.
  - Little Dou's rescue in the Hollow Night is repaid when the Heart Trial is done, with a Cloudtop Orchid.
- **The night peddler** (Part 8): Peddler Shao sets out his mat on the Caravan Road after dark. Every purchase
  there is +5 sin.
- **UI**:
  - The Relations page's Grudges tab shows each grudge against its threshold, with Pay and Duel buttons, or
    what settles it.
  - A Mercy page.
  - The Bounties tab.
  - A Codex entry, "Grudges and bounties".
- **Events:** `grudge_changed`, `hunter_dispatched`, `bounty_taken`, `bounty_claimed`, `foe_surrendered` and
  `foe_judged`, with HUD notes. Intents: `pay_grudge`, `take_bounty` and `judge_foe`. Combat's new
  `apply_execute` finishes a foe who yielded.
- **Debug flags:** `--grudge=faction:n`, `--open-page=mercy:def` and `--open-page=notice_board:bounties`.
- **Tests:**
  - named kills and ordinary ones;
  - hunters: chance, level and cooldown;
  - blood money, the duel, Old Scores and the story grudge;
  - a bounty from start to claim, and once a day;
  - surrender, both judgements and their debts;
  - Kuai Shan's hunt;
  - Dou's letter;
  - the night peddler.

### V8b · The living world: hearts, gifts and bonds (S49)
- **NPC affinity**: 0–5 hearts with fourteen named people and the four companions.
  - Part 8's favourite gifts: Aunt Ping's Riverfish Soup, Granny Liu's Mist Lotus, Old Ma's pearls, Mei Qing's
    Cloudtop Orchid, Lan Yue's Lotus Root Tea, Tie Niu's Boar Bone Broth, Qiu Feng's vulture plume and Bai
    Ling's formation stone. There are more for Little Dou, Lu, Uncle Guo, Shen Lian and the two elders.
  - One gift per person a day: a loved gift is a whole heart (+100), a liked one +40, anything else +15.
  - Each quest done for someone is +30.
  - Mei Qing and Shen Lian keep one heart count across their two rows.
  - What someone loves or likes is remembered once you learn it.
- **Hearts pay out once each**: a recipe taught at three (Aunt Ping's soup, Lan Yue's tea, Tie Niu's broth and
  more) and keepsakes at three or five. A shopkeeper takes 5% off at three hearts and 10% at five. New
  requirement kind `hearts_at_least`; new effect `add_affinity`.
- **Companions**, on the Companions page:
  - A friendly duel from three hearts, at your level (+20 for a win, once a day).
  - **Sworn Siblings** at four hearts, up to three: +3% attack and defence for each one in the party, and the
    Sworn Sibling title.
  - A **Dao Companion** at five hearts, only one. While they are with you, they hold the breakthrough support
    slot (one risk step), share +10% insight and meditate with you (+25% resonance meditation, from the day the
    bond is sworn).
- **Master**: passing the personal-disciple trial makes your sect's elder your master. **The Elder's Last
  Lesson** (a new chapter 10 quest before the farewells) passes on their legacy Inner Art, which is never sold:
  Elder Hu's Lotus Mind (+8% insight, +5% Will) or Elder Sung's Drifting Cloud (+6% move speed, +5% evasion).
- **UI**:
  - A **Gift** page from any gift-taker's dialogue ("Give a gift") and from the Companions page.
  - Hearts beside the speaker's name in dialogue.
  - Companion cards show hearts, a bond tag, and Gift, Duel, Swear and Dao Companion buttons.
  - The Relations page's Bonds tab lists every friend with their hearts.
  - A Codex entry, "Hearts and bonds".
- **Events:** `affinity_changed` and `bond_formed`, with HUD notes. Intents: `give_gift`, `offer_bond` and
  `companion_duel`.
- **Debug flags:** `--companion=id`, `--hearts=npc:n` and `--open-page=gift:npc`.
- **Tests:**
  - loved, liked and courtesy gifts, and once a day;
  - gear and key items refused;
  - Mei Qing's shared hearts;
  - one-time heart rewards and quest affinity;
  - keeper discounts;
  - the duel's heart gate, level and daily reward;
  - sworn and Dao Companion rules and their effects;
  - the master and the legacy.
  The valley run now takes the Last Lesson.

### V8a · The living world: the Relations authority, karma deeds, alignment and Fame (S49)
- **Relations authority** (new, per character). It owns the karma ledger, which moves off the cultivator, and old
  saves carry their merit, sin, debts and eased realms across. Progression, Combat and the tribulation now read the
  ledger from it. `merit_changed`, `sin_changed`, `debt_recorded` and `debt_called` are its events now.
- **karma.json** (new, from `tools/data/relations.py`): every deed with its merit, sin, alignment and Fame.
  - A deed fires three ways: from the `deed` effect (quest rewards, dialogue choices), from code (a patient
    healed), or from a matching event (a back-room purchase, the Beast Tide held, a field lord felled, a spar won
    or lost where a town can see).
  - Flags: once, once per boss, per item bought, and town-only.
  - Part 8 numbers: cleansing a Hollowed village or well is +30 merit (it was +15 and +10), and each patient
    healed is +2. The build's own deeds (the Hollow Night rescues, the tomb, Elder Gu, the ledger) are now named
    deeds.
- **Alignment**: −100 (demonic) to +100 (righteous), named Demonic, Shadowed, Balanced, Upright or Righteous.
  - Deeds lean it.
  - New requirement kinds: `alignment_at_least`, `alignment_at_most`, `merit_at_least` and `fame_at_least`.
  - The Cloud Sect sells Calm Heart Incense only to the upright. Broker Mu keeps Mid Soul Cores and Beast
    Essence Blood under the counter for the shadowed.
  - Data validation keeps these kinds off every realm breakthrough.
- **Personal Fame**: Unknown, Noted, Rising, Renowned, Legendary.
  - Raised by tournaments (qualifier +20, last eight +60, finals +150), great foes, cleansings and the Beast Tide.
  - Losing a spar in a town costs 5.
  - From Noted, townsfolk greet you by name.
  - From Rising, Young Master Luo Heng may be waiting when you walk into a town (once a day). Accept, and he
    spars at your level (+15 Fame for humbling him). Decline, and you lose 5.
- **Relations page** (Character → Relations; also the Heart tab's Ledger button) with four tabs:
  - Karma: merit, sin, the merit step, the alignment scale, recent deeds and named debts.
  - Bonds and Grudges: filled in by V8b and V8c.
  - Fame: the tier ladder and what each tier brings, plus a waiting challenge with Accept and Decline.
- Quest rewards list the merit and Fame a deed gives. There are Codex entries for alignment and Fame.
- **Events:** `alignment_changed`, `fame_changed` and `young_master_challenge`, with HUD notes. Intent:
  `answer_challenge`.
- **Debug flags:** `--deed=id` and `--challenge`.
- **Tests:**
  - old-save migration;
  - once-only deeds;
  - public and private spars;
  - once-per-boss Fame;
  - tier-ups;
  - alignment clamps and gates;
  - per-item black-market sin;
  - the young master's chance, daily limit, decline, accept (at your level) and lapse.

### V7e · Spirit beasts: the Beast Arena, the Trial Grove and the Taming Dao (S46)
- **Beast Arena** (the ladder board on Market Street, and a new page). Ten NPC tamers, from Farmhand Qiao at rank 10
  to Jing Mo at rank 1.
  - Challenge the one above you in 1v1 (your active animal) or 3v3 (three beside you or in the bag), five times a
    day. A win takes their rank.
  - The rank held when the week turns pays out: 30 Spirit Stones and Beast Essence Blood at rank 1, down to 3 Spirit
    Stones at rank 10. Then the ladder starts again.
  - The fights are pet-only auto-battles in the new pure `PetRules.battle`, seeded on their own stream. Level,
    rarity, stage, growth, aptitude, gear, core, wounds, traits, skills and awakened skills all count, and an Equal
    Contract opens with its free cast.
  - The page replays the last fight as draining health bars.
- **Beast Trial Grove** (a door off Market Street). Once a day the animals fight ten beasts (their Level following
  yours). Your own blows do no harm there: they rally the animals (+25 % for 5 s, every 8 s). The first clear gives
  the Guardian Spirit skill book; later clears draw essence blood, marrow pills or skill books.
- **Beast Taming Dao**: six tiers, two in the valley and four in the Azure Expanse.
  - Every tier adds 5 % to taming.
  - Tier 2: eggs hatch 10 % sooner.
  - Tier 3: elites can be tamed (not before).
  - Tier 4: you can teach it to your disciples.
  - Tiers 5–6 (Beast King taming, custom contracts) are named hooks for later ages.
- **Pavilion Feeding Trough**: with a Beast Pavilion, hungry animals are fed once a day from storage, their favourite
  food first.
- **Rename** on the Spirit Animals page.
- **Events:** `arena_battle`, `arena_rewarded`, `beast_trial_result` and `pet_fed` (from the trough), with HUD notes.
  Debug flag: `--arena=solo|trio`.
- **Tests:**
  - battle determinism and the free cast;
  - the ladder, the daily limit and the weekly payout;
  - the Grove's once-a-day limit, rally, kill count and first-clear book;
  - the Dao gates for elites and teaching;
  - the trough's once-a-day feeding.

### V7d · Spirit beasts: the Beast Bag, the Mount slot, Beast Kings and the Beast Tide (S46)
- **Spirit Beast Bags** (key items): Reed 2, Hide 3 and Cloud 4 (Hermit Yao), Mistjade 5 and Starweave 6. Pack animals
  somewhere safe (a town, a sect, a rest stop or home).
  - In the field only carried animals can be called, and never in a fight.
  - A swap puts the old active animal in the new one's bag slot.
- **HUD pet strip** beside the portrait:
  - the active animal with its health arc (tap for the Spirit Animals page);
  - the bag's animals (tap to swap one in);
  - the Mount slot with a Ride / Walk toggle.
- **The Mount slot.** Setting an animal to Mount puts it in its own slot, so a combat animal walks beside you while
  you ride. The `set_mount` intent rides or walks. Thrown off by a heavy blow, the mount follows until you climb
  back on. Saves that rode the active animal move it into the slot.
- **Mount-only species**, with new creature art:
  - The **Riverstone Ox** (walk ×1.5, jump 530, no climbing) grazes Quarry Rim from Cloud Stride 1, paw-marked.
  - The **Cloud Stag** (walk ×1.6, jump 600) hatches from the Cloud Stag egg the Beast Tide gives once from Cloud
    Stride 1.
  - Mount-only animals only take the Mount role.
- **Rarity rolls.** A tamed beast is mostly Common, an elite never is, a plain egg is sometimes Rare, and a Beast
  King's nest egg is Rare or better (on the bloodline stream). Bred eggs keep their parents' rarity.
- **Beast Kings** (`beast_kings.json`): the Riverbed Serpent (valley) and the Thousand-Eye Toad (Azure Expanse).
  - While a King lives, its zone's beasts are 10 % stronger, and paw-marked otters and foxes gather on Bend Shore.
  - When it falls, the buff lifts at once, and its lair's nest holds one Rare Spirit Egg per character for 30
    minutes.
- **The Beast Tide.** Once a real week, ring the gong at Stoneford Gate (from Qi Unfurling 1). Three 30-second waves
  of crabs, boarlets and hounds, their Level following yours between 10 and 45 (the S25 room-event waves, now with
  `until_s` and level offsets). Holding the gate gives three cores of your rank, an egg and Spirit Soil.
- **Events:** `pet_swapped`, `beast_king_spawned`, `king_nest_opened`, `beast_tide_started` and `beast_tide_result`,
  with HUD toasts. Debug flags: `--mount=species` and `--bag=species,species`.
- **Tests:**
  - rarity odds;
  - the egg's species;
  - bag capacity, packing, field calls, swaps and the in-combat block;
  - the Mount slot with a combat animal, mount-only rules, speeds and old-save migration;
  - the King's buff, spawns and nest;
  - the tide's due week, wave levels, wave end and rewards;
  - pets never dying.

### V7c · Spirit beasts: skill books, gear, fusion and breakthroughs (S46)
- **Skill books** (`pet_skill_books.json`). Learned slots open by stage (2 as a Juvenile, 3 as an Adult, 4 from
  Awakened); when they are full a new book overwrites a random slot. Teach from the Growth tab, or use a book from
  the gourd on the active animal.
  - Iron Hide: 10 % less damage (Beast Hall shop).
  - Frenzy: strikes 15 % faster for 6 s after a kill (Big Toad Tan, 35 %).
  - Deep Pockets: one more gourd row while it is active (Beast Hall shop).
  - Herb Whisper: rare herbs within 400 show their ripening time (the new chest on the Falls Pool ledge).
  - Thunder Roar: every 15 s of a fight, foes near it are stunned for 1 s (the Stormwing Hawk elite, 25 %).
  - Guardian Spirit: takes one blow meant for you every 30 s (its book comes with the Beast Trial Grove).
  - Book drops roll on their own stream, so the loot roll is unchanged.
- **Pet gear.** The Bone Collar (+10 % HP), Scale Talisman (+10 % attack, +5 % defence) and Reed Saddle (+10 %
  mount speed) are forged at the anvil. They are enhanced like any gear (+10 % of the base a level) and worn by an
  animal. Equipping one from the gourd puts it on the active animal. Random drops never roll pet gear.
- **Fusion** at the Beast Hall or the Beast Pavilion. Fold one animal into another: a 30 % chance at each of its
  traits and learned skills, and half its purity above the kept one's. It asks for confirmation, locked animals are
  never fused, and the sacrificed animal's gear comes back to the gourd.
- **Pet breakthroughs.** From Awakened on, a stage-up is a breakthrough: a 55 % base, +0.2 % a point of purity,
  and up to three support items (cores of its element +5–20 %, essence blood +15 %), capped at 95 %. A failure costs
  a heart or leaves a Grievous Wound.
- **Pet Core Formation** (Adult to Awakened) grades the core from purity, growth, support and a roll: Cracked,
  Common (+5 %), Fine (+10 %) or Flawless (+18 %) to every stat.
- **Spirit Animals page:** Care and Growth tabs. Growth shows the purity bar with the 50 and 90 marks, growth and
  aptitude, the contract and core, learned-skill chips, gear slots, books and gear to use, the breakthrough with
  support toggles, and a Fuse picker. Icons for the six books and three pieces of gear.
- **Events:** `pet_skill_learned`, `pets_fused`, `pet_core_formed`, `pet_breakthrough` and `pet_gear_changed`.
- **Tests:** slots by stage, overwrite under a fixed seed, every skill's effect, gear and enhancement, the saddle
  rule, fusion (place, lock, confirmation, purity, about 30 % odds over 180 rolls), breakthrough odds, success and
  failure, and the core grade.

### V7b · Spirit beasts: awakenings, contracts, command capacity and incubation (S46)
- **Bloodline awakenings.** At 50 purity an ancestral skill wakes: a heavy strike (×2.5) every 12 s of a fight,
  such as the Ember Fox's Nine-Tail Flame. At 90 the animal takes its true form (the Nine-Tail Fox): +10 % to every
  stat, drawn larger and in its lineage's colour. Every point of purity strengthens revealed traits by 0.2 %.
- **Beast Essence Blood** (Hermit Yao, from Heart Tempering 1): +10 purity for the active animal. It also seals a
  Blood Contract and rerolls an egg's hidden trait.
- **Suppression** reads the S12 Pressure contest (`CombatRules.pressure_loss`). An animal's bloodline tier (rarity
  step plus awakenings) against a wild beast's (rank ÷ 2, +1 elite, +2 boss): when it wins, the beast is gripped by
  Fear once and taming it is 10 % likelier.
- **Contracts.**
  - At 10 hearts an animal offers the one Equal Contract a character ever makes. Resonance flows both ways (it
    resonates at half strength whatever its role, and your meditation feeds it XP) and it casts one free skill a
    fight.
  - A Blood Contract costs a drop of essence blood: +15 % to its stats, but its knockout bruises your soul.
- **Command capacity** tied to Soul: 1 animal, 2 from Spirit Awakening, 3 from Sage. "Beside You" on the Spirit
  Animals page brings more animals along; each fights with its own strength.
- **Incubation input**, once of each kind per egg: drip your own essence blood (+10 purity, −10 % max HP for 24
  real hours), add a beast core to steer its element, or Beast Essence Blood to reroll a hidden trait. Animals
  hatched from an egg you warmed start at 3 hearts.
- **Beast Marrow Washing Pill** (alchemy): rerolls the active animal's weakest aptitude, with no toxicity; it waits
  for a Juvenile. Pet medicines now check they can help before they are spent.
- **Fox Spirit's Favour** joins the fate deck once eggs are open: the next egg hatches with +10 purity.
- **Events:** `bloodline_awakened`, `contract_formed`, `contract_offered`, `pet_skill_cast`, `beast_suppressed`,
  `egg_infused` and `party_changed`, with HUD toasts and notes. Debug flags: `--pet=species[:stage[:purity[:hearts]]]`
  and `--egg=species`.
- **Tests:** purity at 49, 50, 89 and 90; trait strength; the Pressure rule and suppression; skill casts; Equal
  once per character and only at 10 hearts; Blood stats and the soul injury; capacity by realm and the party;
  every incubation input; the Fox fate; and the marrow pill.

### V7a · Spirit beasts: bloodline, beast ranks, cores, wounds and taming by nature (S46)
- **Pet state depth.** Every animal now carries these fields, filled with neutral values on animals from older
  saves: bloodline purity, growth, aptitude, contract, learned skills, gear, a wound flag, knockouts, core grade,
  a colour variant and a lock.
  - A hatch or tame rolls purity by rarity (Common 5–15 … Primordial 60–80), a hidden growth (0.8–1.3) and
    aptitude per stat (0.8–1.2), on their own stream. Growth and aptitude show from Juvenile.
  - 1 % of animals wear a rare colour.
  - Growth × aptitude scale the animal's HP and attack.
  - The Spirit Animals page shows all of this and gains a Lock toggle, a Guard role, a wider detail panel and
    localized role buttons.
- **Beast ranks and natures** (Part 8) in `enemies.json`.
  - Rank 1–9 comes from the Level band (1–9 is rank 1 … 73+ is rank 9), for beasts only. Nameplates read
    "Lv 22 · R3" and the Collection shows rank and nature.
  - Ghosts (Paper Talisman Ghost, Mirror Wisp, Weeping Lantern) and constructs (sentinels, puppets, the Gate
    Guardian) are no longer beasts.
  - Green Viper, Mud Hound and Mist Vulture are demonic; the Hollowed Boarlet and Hollow Stag are Hollowed. All
    five can now be tamed into new species: Green Viper, Mud Hound, Mist Vulture, Cleansed Boarlet, Pale Stag.
- **Taming by nature.**
  - A demonic beast takes only a Purifying Offering (Hermit Yao, from Qi Unfurling 7).
  - A Hollowed one must first be cleansed by one; then any offering tames it.
  - The taming fix: a tameable beast struck down while an offering sits on quick-use is subdued at 1 HP for 10 s
    instead of dying (once).
- **Beast cores.** Beasts of rank 2 and up drop a core at 2 % a rank, on their own stream. Cores come in 28 kinds:
  Low, Mid, High and Peak, in seven elements.
  - A pet devours cores of its own element for XP (60 / 200 / 600 / 1,500).
  - The new Core Exchange at Hermit Yao's Beast Hall buys them for 1 / 3 / 8 / 20 Spirit Stones, up to 60 a day.
  - They also burn as Beast Fire.
- **Grievous Wound.** Three knockouts in five minutes leave an animal at 80 %. It mends by resting at the Beast
  Hall or with a Beast Revival Pill (alchemy, or Hermit Yao). Pets still never die.
- **Events:** `pet_wounded`, `pet_healed`, `core_devoured`, `cores_sold`, `beast_cleansed` and `beast_subdued`,
  with HUD notes. Debug flag: `--pet=species[:stage]`.
- **Tests:**
  - bloodline bands, hidden aptitude, and older-save migration;
  - ranks, natures and core odds by rank;
  - devouring by element, and the Exchange cap;
  - the wound window and its cure;
  - demonic and Hollowed taming, and the subdued fix;
  - data validation for tame species, pet art and cores.

### V6c · Processing racks, sealed herbs and garden raids (S45)
- **Racks** on the drying rack (Batch Work's reward, its text now true): two at a time, ten herbs each, on the
  clock and offline too. A new Racks tab on the Garden page runs them.
  - Steaming (1 h): pills made from the herb carry 30 % less toxicity.
  - Wine-soaking (4 h, a jar of rice wine per five herbs; Stoneford General Store): +10 % potency.
  - The herbs come back marked (a `prep` on the stack). A pill takes the prep of its principal herb when there
    is enough prepared of it. Other herbs are taken plain first, so prepared ones aren't wasted.
- **Sealed herbs.** Old Pan's "hundred-year" ginseng comes sealed, each in its own slot, and 30 % are dyed roots.
  - Appraisal (loupe, Appraisal Eye, or Old Pan and Elder Gu in person) shows which, from the item's new Appraise
    button.
  - An unappraised fake in the furnace spoils the pill (Flawed) 60 % of the time. Sealed stacks are taken last.
- **Garden raids.** Once a reset day, checked when you come back, an unguarded planted bed may be hit (8 %):
  - pests halve its growth, or a thief takes the herb;
  - a mail from the gardener tells you which;
  - a pet on the new Guard duty stays home and keeps them off, as does a Protection or Concealment formation
    burning in the bed's room that day.
- Pill tooltips show the prep and its toxicity; sealed herbs say so.
- **Events:** `rack_started`, `rack_collected`, `garden_raided` and `herb_appraised`, with HUD notes.
- **Tests:**
  - rack timing, the wine cost, and the prep carried into a pill;
  - potency and toxicity by prep;
  - sealed slots, appraisal needing a loupe, and fakes revealed only by appraisal;
  - a fake taken into a craft;
  - raids on an unguarded bed and none under a Protection formation.
- **Moved to V8** (they run on the S49 world calendar): treasure births and gathering trials.

### V6b · The herb garden: beds, Spirit Soil, spring water, transplanting and the Verdant Dew Vial (S45)
- **Garden beds** grow a herb from seed on the clock, offline too. A new Garden page, opened from a bed, shows each
  bed with its herb, age, growth and time left.
  - Grow times: willow moss 2 h, ember pepper 3 h, ginseng 4 h, mist lotus 6 h, orchid and soulbell 8 h.
  - A room's Qi speeds its beds by half its bonus.
  - Harvest gives 2–3 of a young herb (one of an aged one), with a 20 % chance of the seed back.
  - A planted bed shows its herb growing from a seedling in the room.
- **Field grades.** A Low bed grows up to Earth-grade herbs, Mid up to Heaven and High up to Mystic.
  - Spirit Soil raises a bed one grade for good. It drops 1 % from beasts of rank 3 and above (Level 19+), and one
    lies in the Drowned Abbot's vault.
  - The Jade Herb Terraces have 3 Low beds. The Cloud Sect's Array Court gets 3 Low beds and Gardener Ren; before,
    Cloud disciples had no beds and could not finish Seeds of the Valley.
  - Each cave abode has 2 Mid beds.
- **Spring water.** A Qi spring gives three bottles a reset day once the garden is open. A bottle poured on a bed
  gives +25 % growth.
- **Transplanting.** With a Spirit Spade (Stoneford General Store, from Cloud Stride 1) and Expert gathering, a
  rare herb offers Pick it or Dig it up.
  - Dug up, it moves at its age to the first free bed that can hold it, grown.
  - It dies 25 % of the time at Expert, 5 % less per rank above. Either way the node waits for its next ripening.
- **The Verdant Dew Vial** (A Lake Inside, Spirit Awakening 1) fills with a drop a day, offline too, up to three.
  A drop ages a bed's herb one tier, up to 1,000 years in the valley.
- **Seeds of the Valley** now gives three willow moss seeds to plant (text fixed to name the seed sources) and three
  bottles of spring water.
- **Events:** `herb_planted`, `bed_watered`, `bed_enriched`, `herb_aged`, `spring_bottled` and
  `transplant_result`, with HUD notes. A Codex entry covers the garden. Debug flag: `--garden-preview`.
- **Tests:**
  - soil caps the grade, and Spirit Soil lifts it;
  - three bottles a day, and +25 % a watering;
  - offline growth to the minute;
  - the dew accrues offline and is capped at three; it ages a root to 1,000 years and no further;
  - transplant odds by rank, and the survival rate under a fixed seed;
  - data validation for beds;
  - the valley run plants three beds and harvests one.

### V6a · Rare herbs, the harvest tap, seeds and seasons (S45)
- **Herb ages.** Every herb has a family and an age (10, 100 or 1,000 years; `garden.json`). New aged herbs, each
  with raw uses and a gold-haloed icon:
  - Riverreed Ginseng (1,000 yr);
  - Ember Pepper, Mist Lotus, Cloudtop Orchid and Soulbell Flower (100 yr).
- **Aged herbs in recipes.** When the herb a recipe calls for runs short, an older one of its family stands in, and
  the craft's quality score rises 0.04 per age tier. A thousand-year root is never spent while ten-year roots are
  to hand.
- **Rare nodes** (Part 8), on raised tiers only, placed after the verticality pass on named surfaces:
  - hundred-year ginseng at Bend Shore and the Rapids Terraces (Tide Crab guardians; dawn, every 2nd day);
  - the thousand-year root on the Serpent's Shallows high rock (the Riverbed Serpent; midnight, every 5th day;
    Summer);
  - hundred-year lotus at the Falls Pool and Behind the Falls (dusk, every 3rd day);
  - the orchid on the Sky Ledges' top ledge (a Stormwing Hawk; midday, every 3rd day; Spring);
  - soulbells on the Misty Slopes and at the Frozen Shrine (Mirror Wisps; midnight, every 3rd day; Autumn);
  - the pepper in the Thicket Heart canopy (a Thornback Boar; midday, every 2nd day; Summer).
  - The Sky Ledges' second orchid moves up to the east ledge.
- **Ripening.** A rare node is ripe for 20 real minutes around its phase on its day (the in-game day is 48 minutes).
  Picking early gives a herb one tier younger, and a picked node grows back with its next ripening. A ripe node
  shimmers gold, and the room log says when one ripens.
- **Guardians** wake once per ripening, when you climb within reach of a ripe node. To pick it:
  - kill the guardian, lure it past its leash, or pick unseen under Concealment while it hasn't noticed you;
  - for the thousand-year root, the Serpent must be away.
- **The harvest tap.** The 1.5 s hold ends in a ring that shrinks toward the Attack button; tap inside the gold band.
  - The band is 12 % of the ring at Apprentice, then 16, 20, 24 and 28 % at Grandmaster (a new rank cap, from Sage
    Sovereign 1).
  - A perfect tap keeps the full age, gives 1.5× gathering XP and may drop a seed (10 %). A miss drops one age tier,
    never below ten years.
- **Seeds.**
  - Willow Moss, Ember Pepper and Riverreed Ginseng seeds are sold at Granny Liu's and in Greyreed Hamlet.
  - Mist Lotus seeds come only from perfect harvests.
  - Cloudtop Orchid and Soulbell seeds come only from Lu's inheritance (the Riverbreath Trial and the Drowned Abbot).
- **Seasons** (`seasons.json`): Spring, Summer, Autumn and Winter, one real week each, turning with the Monday
  reset. A seasonal node out of season lies dormant. They never gate progression.
- **UI:**
  - the harvest ring;
  - a leaf marker on the minimap with the time left (or until it ripens);
  - a Spirit Sense readout over each rare node in reach;
  - a Seasons tab in the Codex, with the calendar and each herb's rhythm (places shown once visited);
  - Codex entries: Rare herbs, Seasons.
- **Events:** `herb_ripening`, `herb_harvested`, `guardian_spawned` and `seed_found`, with HUD notes. Debug flags:
  `--herb-ripe=<object>` and `--tap-preview`.
- **Tests:**
  - the ripening window by time, and an early pick a tier younger;
  - the guardian once per ripening, lured away, and unseen under Concealment;
  - the tap window per rank, and a miss;
  - the seed rate under a fixed seed, and seasons;
  - aged stand-ins in recipes;
  - data validation for families, seeds and every rare node;
  - a guarded hundred-year harvest in the valley run.

### V5d · Vows, epiphany, Killing Intent, Blood Burning, the false realm and the soul's escape (S48)
- **Vows** (`vows.json`, open at Heart Tempering 1): four oaths, each taken or dropped on a new Cultivation tab.
  - Mercy: no killing blow on a fleeing foe (it gets away with its life); +10 % healing received (a new stat).
  - Plain Fare: no burst pills (Tiger Blood, Sunfire); +10 % Physical Defense and Qi Resistance.
  - Silence: no Presence, so Killing Intent never builds; +10 % Will.
  - Fasting: no food that lends a buff; +5 % accumulation.
  - The bag refuses what a vow forbids. Dropping a vow is breaking it: +15 heart demon.
- **Epiphany.** Contemplation, insight stones, technique use and kills each roll 0.2 % (weighted by Insight) on the
  fortune stream. An epiphany gives 60 s of ×5 insight and a 25 % chance that the most-used technique gains a
  mastery tier for free. Then it rests for two hours of play.
- **Killing Intent.** A kill within 10 s of the last adds a stack (up to 10), +1 % crit each. At 10, weaker
  foes within reach hesitate for half a second. It fades 10 s after the last kill.
- **Blood Burning** (a secret technique taught by Blood Remembers with the Blood Dao): +50 % attack for 10 s. It
  costs 30 % of HP and leaves a body injury.
- **The false realm.** With Concealment, the Techniques page's Secret Arts tab picks a realm to show, up to two
  great realms lower.
  - The HUD badge shows it, marked "(veiled)", and the Character page adds "shown as …".
  - Twenty townsfolk, merchants and wardens speak to the weaker cultivator you show. Elders Hu and Sung, the Grey
    Pilgrim, Elder Zhong and Champion Qiao see through it.
  - **Bandit ambushes.** Once a road's own story is done, its gang's stragglers jump travellers who look weak
    enough: the Mudwater on the Caravan Road, the gorge bandits at the Gorge Mouth, the veiled brigands at the
    Canyon Mouth.
    - The chance is 6 % per entry (never on a first visit or during an event), with a 15-minute rest between
      ambushes.
    - Bandits judge the shown realm and leave alone anyone more than 8 levels past them. A false realm doubles
      the odds.
- **Nascent-soul escape.** From Sage, a grave wound costs 5 % of the stage instead of 10 %: the soul flees to the
  shrine, and the revival page says so. A defeat during a tribulation fails the breakthrough as a Bodily failure.
- **Boss self-detonation.** Comet Captain Rao, cornered below 12 % HP, burns his nascent soul. He is invulnerable
  through a 3 s wind-up with a ring on the ground, then deals 60 % of max HP to anyone inside 280 px and is gone.
- **Fix:** a teacher's lesson (the rare Daos of the Expanse) now opens its Dao at exactly tier 1. Before, a Dao
  Echo fate for another Dao (×0.9) or the 60-second repeat damping could leave it just short, at tier 0.
- **Events:** `vow_taken`, `vow_broken`, `false_realm_changed`, `epiphany`, `soul_escaped`,
  `killing_intent_changed` and `ambush_sprung`, with HUD notes. Debug flag: `--false-realm=<realm>`.
- **Tests:**
  - vow gifts, refusals and the breaking cost;
  - Mercy on a fleeing foe;
  - Killing Intent stacks, crit, decay and Silence;
  - the epiphany buff and cooldown, and Blood Burning's cost;
  - false-realm limits, veiled dialogue and ambush odds, and an ambush spawn;
  - the soul's escape, and the Captain's detonation;
  - a teacher's lesson under Dao Echo.

### V5c · Inner Arts, stances, technique grades and combos (S48)
- **Inner Arts** (`inner_arts.json`, the Part 8 eight) are passive arts, worn in slots: 2 at Qi Unfurling 1, 3 at
  Heart Tempering 1, 4 at Spirit Awakening 1.
  - Riverflow Circulation, Iron Shirt, Swallow's Breath (a new `dodge_cooldown` stat), Stone Root and Clear Lake
    work with any weapon. Sword Heart (Sword Intent to 12) needs a jian and Hunter's Patience needs a bow. Ember
    Channel cuts Fire techniques' cost.
  - Both sect Mission Halls sell a manual for each art, for contribution, from its realm.
  - They have a new Techniques tab, and an art tied to another weapon shows as asleep.
- **Stances** (`stances.json`): one toggle per weapon family, held only with that weapon in hand.
  - Willow Leaf Parry (jian): a parry counters for 200 %, and attacks are 10 % slower.
  - Iron Horse (gauntlets): no knockback, 20 % slower on foot.
  - Coiled Dragon (spear): +15 % reach.
  - Low Shadow (short blade): +10 % crit on a foe's back.
  - Mountain Root (staff): guard +10 %.
  - Still Draw (bow): +15 % damage while standing still.
  - Stances open at Qi Kindling 5.
- **Technique grades.** Every technique is Common, Earth or Heaven (+0 / 10 / 20 % to its base), set by the realm
  that teaches it. The Techniques list shows the grade.
- **Combos** (`combos.json`, Part 8): technique A then B within 1 s.
  - Flowing Palm → Tiger Rush: a shockwave.
  - Cloudpiercing Stroke → Crescent Arc: one more target, 15 % further.
  - Jade Thrust → Dragon Tail Sweep: a pull.
  - Reedcutter Slash → Shadow Flick: a fresh bleed.
  - Riverstone Sweep → Bell Toll Strike: a certain stun, 0.3 s longer.
  - Twin Reed Shot → Pinning Arrow: the root holds 0.5 s longer.
- **Events:** `inner_art_learned`, `inner_art_equipped`, `stance_changed` and `combo_landed`, with HUD notes.
- **Tests:**
  - slot counts, learning and wearing, stat gifts, per-element cost;
  - a weapon-linked art asleep and awake;
  - stance ownership, the gauntlet and jian swap, grades and the combo window;
  - data validation for the new tables.

### V5b · Heavenly tribulation, breakthrough fates and Qi Deviation (S48)
- **Heavenly tribulation.** From Cloud Stride 9 on, every great breakthrough draws a cloud over the room once the
  channel ends. The row for each step is in `tribulations.json`.
  - Bolts: 3 into Spirit Awakening, 6 into Heaven Glimpse and 9 into Sage. After that come waves of 9: 2 into Sage
    Sovereign, and one more wave for each great realm after.
  - Each 25 heart demon and each 100 sin adds a bolt. Debt of Heaven adds 2 to the next tribulation.
  - A ring shows where each bolt will land, one second ahead. Step out of it or guard to take half. Roofs do not
    help. A Lightning Rod Talisman in the bag takes one bolt.
  - Damage is 20 % of max HP × (1 + sin ÷ 500) × (1 + heart demon ÷ 200).
  - A bolt that would kill leaves the body at a tenth of its HP and fails the breakthrough as a Bodily failure.
    Leaving the room fails it as an interruption.
  - Weathering every bolt leads to the usual success roll. The bolt timing comes from the breakthrough stream and
    the ring positions from the combat stream.
  - A HUD panel counts the bolts, and the rings and strikes use the lightning hazard's art in any room.
- **Breakthrough fates** (`fates.json`, the Part 8 deck of 12).
  - After each great breakthrough (past the Prologue), three distinct cards are drawn by weight on the breakthrough
    stream. A picker opens; the offer is saved and can be reopened from the Heart tab.
  - A card can give modifiers for life, costs that last until the next great realm, one-off effects (heart demon,
    pill resistance, stability, purity), or something the next tribulation or breakthrough spends.
  - Wandering Eye reveals a hidden way in each room. Blood Memory adds heart demon for every streak of 10 kills.
    Dao Echo speeds your strongest Dao and slows the rest.
  - Fox Spirit's Favour stays out of the deck until pets have purity (S46).
- **Qi Deviation.** A failure at Severe risk, or on a Poor-compatibility method, applies a ten-minute status. While
  it lasts, every technique takes a random element.
- **HUD.** A heart-demon status icon shows at 25 and more, and the Heart tab's bar turns red when it adds risk.
  Toasts cover the tribulation, fates and Qi Deviation.
- **Fixes.**
  - `ContentDB.config()` now also returns an entries table's own constants. The talisman constants were never read
    before: grade power, quality multiplier and trace tolerance.
  - The hazard layer is in every room.
- **Tests:**
  - bolt counts by realm, heart demon and sin, and the damage formula;
  - a tribulation weathered, and one dodged;
  - a lethal bolt as a Bodily failure;
  - three distinct fate cards, with the same draw for the same seed;
  - each fate's gift, cost, realm expiry and spent `next`;
  - Blood Memory's streak;
  - Qi Deviation only under its conditions;
  - valley checks for the core grade, fates kept and a tribulation stood through.

### V5a · The body ladder, Core Forging, named roots and physiques (S48)
- **The body ladder.** Copper (body level 18), Iron (36), Jade (54) and Gold (72) Body, in `body_tiers.json`. Each
  rung needs three things: the body level, its Temper trial and a full soak in its bath.
  - Temper trials start at a Temper drum. Copper is on Willow Path West: three minutes above half HP. Iron is on the
    Pilgrim Stairs: five Stone Guardians in one run. Jade is on the plum-blossom poles in the Sword Court or East
    Terrace: ninety seconds, never two seconds on the ground. Gold is in the Lightning Scar: three minutes above
    half HP.
  - A trial clears the room's own foes and sends foes at the character's own level.
  - Gifts: Copper gives +5 % Physical Defense, and body techniques (Tiger Rush, Stone Skin, Mountain Shaker) spend
    HP when QI runs short. Iron gives +10 % knockback resistance, Jade heals injuries 1.5 times as fast, and Gold
    is immune to Qi Seal.
  - Iron teaches the Jade Marrow Bath and Jade teaches the Golden Body Bath (both new). A bath beyond the rung you
    have reached still injures the body. That check now reads the rung reached, not the body level.
- **Core Forging.** At Heart Tempering 9 → Cloud Stride 1 the core forms at a purity grade instead of always 9.
  - Five preparation points: a room of the method's element, the method's Yin or Yang hour, full Composure, no
    residue, and a Heavenly Flame Pill within the hour (new; it is refined only over a Heavenly Flame).
  - Each point met counts on an 80 % roll. The grade is 9 minus the points counted, never better than 5. A
    flawless Heaven's Cleansing is one more point, down to 4.
  - The Breakthrough dialog shows the checklist, and methods now lean Yin or Yang.
- **Named roots.** The Aptitude tab names the root once the elements show: Heavenly, True, Mixed, Mutated or Faint.
  It also lists every aptitude as a signed percentage and says when hidden ones appear.
- **Physiques** (`physiques.json`), earned by deeds, each with a drawback:
  - Jade Bone: a flawless Cleansing.
  - Yin Vessel: ten nights of meditation at the Falls Pool.
  - Ember Heart: fifty Fire pills.
  - Stone Marrow: Copper Body before Qi Unfurling 3.
  - Cloud Lung: ten kilometres gliding or flying.
  - Hollow-Touched: its hook is ready for v1.2.
  - The Aptitude tab shows progress toward the ones not yet earned.
- **A Body tab** on the Cultivation page shows the four rungs, what each still needs, and its trial and gift.
- **HUD.** A panel shows any running room event (rites, trials, sieges) with its name, time left and rule. Toasts
  now cover passed and failed trials, rungs, physiques and the core grade.
- **Fixes.**
  - Worn titles now apply their bonuses (none ever did), and the Titles tab shows each bonus.
  - The Still Water title pointed at a stat that does not exist.
  - Modifier text now shows signs, percent stats and elements.
  - Room events that had no display name now have one.
  - The quest tracker no longer touches the taller player panel.
- **State.** CultivatorState version 6 adds `body_tier`, `body_trials`, `body_baths`, `core_grade`, `fates`,
  `physiques`, `vows`, `inner_arts`, `stances`, `false_realm` and `epiphany_cooldown`. Older saves load with
  neutral values.
- **Tests:**
  - a rung needs both the trial and the bath;
  - the HP floor and kill-count trial rules;
  - Gold Body's seal immunity and the HP cost of body techniques;
  - physique gifts, counters and the heart-demon multiplier;
  - root names at the affinity edges;
  - core grade from points, and with a fixed seed;
  - title modifiers;
  - data validation for the new files.

### V4e · Pill tribulation and the Pill Soul's flight (S44)
- **Pill tribulation.** When a Heaven-grade (or better) pill reaches Halo or Soul at the furnace, the heavens test
  it before the pills are yours.
  - Bolts come down in turn: 3 for a Heaven pill, 2 more for each grade above, at most 9. Their timing comes from
    the crafting stream.
  - Each bolt is telegraphed by a ring closing on its strike. *Raise shield* as it lands, within 0.22 s either side.
  - Every bolt held keeps the result, with a 10 % chance to rise a tier. One bolt through drops the batch to Perfect.
- **The Pill Soul's flight.** A Soul pill that comes through flees the furnace. One *Catch* tap as it crosses the
  mark keeps it. A miss settles the batch as Pill Halo; the batch is never lost.
- **Unfinished tribulations.** If the page closes or another craft begins, the tribulation settles as though every
  unanswered bolt struck and the Soul got away. Its pills still come.
- **Who plays it.** Only a live refine from the furnace page plays the tribulation. Auto-refine and other callers
  keep the roll as it is.
- **Events:** `pill_tribulation_result` and `pill_soul_flight`, with HUD toasts. The constants are in
  `forge_upkeep.json` (`tribulation`).
- **Tests:** bolt counts by grade, held and missed outcomes, the Soul's flight and a missed catch, settling an
  abandoned tribulation, and buying a named recipe scroll.

### V4d · The Alchemist Guild, ancient recipes and experiments (S44, Part 8)
- **The Alchemist Guild** (Qi Kindling 8, alongside *Batch Work*). Guildmaster Tang keeps its corner of Stoneford's
  Artisan Row: a stall, the Guild Board, and a new **Guild** tab in Crafts.
- **Exams.** An exam starts with *Light the candle*. It counts pills of the right recipe and quality made before the
  time runs out; a burnt-out candle fails it.

  | Rank | Exam | Rewards |
  |---|---|---|
  | Adept | 5 Healing Pills at Fine or better in 3 minutes | Badge title, the guild shop, the commission board |
  | Expert | 3 Foundation Guard Pills at Superior or better in 5 minutes | Badge title, the Qi Flow Pill recipe, better-paid commissions |

- **The guild shop** sells:
  - the Foundation Guard, Clear Mind and Meridian Reversal recipes;
  - the Jadeiron Furnace blueprint, which is no longer known by default;
  - Mist Lotus and jade scales;
  - for an Expert, the Storm Blood Pill.
- **Mei Qing's Recipe Box** now teaches the Qi Gathering, Bone Strengthening, Viper Antidote and Tiger Blood recipes.
  These recipes, and the guild's, could not be learned anywhere before.
- **Commissions.**
  - Three orders each morning, drawn from the pills you can refine: take the order, deliver it, and choose taels or
    contribution.
  - An order pays 1.2 × the pills' shop price, 1.5 × for an Expert.
  - Daily pay is capped at a fifth of the zone's daily income target: Level × 60 taels an hour for three hours of
    play, from S39's worked example.
- **Ancient recipes** come in torn pages on dungeon shelves:
  - the Method Conversion Pill: 3 pages, in the Mudwater Hideout, the Drowned Shrine and the Forgotten Monastery;
  - the Sovereign Settling Pill: 4 pages, in the Tomb of Sunscar, the Oasis of Bones and the Skyport Wreck.

  A full set teaches the recipe. With pages missing, **Deduce** spends one set of ingredients at 20 % a page, plus
  10 % for each Alchemy Dao tier above the third, never above 95 %.
- **Experiments** (Qi Unfurling 1).
  - At the alchemy furnace, choose 2–4 herbs. A hidden recipe of exactly those herbs is learned:
    - the Sunfire Pill, from ginseng and Ember Pepper;
    - the Stillwater Pill, from Mist Lotus, Soulbell and willow moss;
    - the Cloudstep Pill, from Cloudtop Orchid and willow moss.
  - Anything else makes a Murky Pill, and conflicting herbs blow the furnace.
  - Every mix is logged for the whole account. A mix already tried, in any order, is refused. The log is shown on
    the Codex's Experiments page.
- **Fix:** a shop that sells several recipe scrolls now sells the one you chose. It used to sell the first on the
  shelf; the buy intent now names the recipe (`learn`).
- **Events:** `recipe_page_found`, `recipe_deduced`, `experiment_result`, `guild_exam_started`, `guild_exam_failed`,
  `guild_rank_changed` and `commission_completed`, each with a HUD toast.
- **Tests:** Deduce odds and the 95 % cap, a full set teaching the recipe, the hidden recipe, the Murky Pill and the
  log's refusal, both exams (quality counting, the time limit, rewards), and commission pay and cap.

### V4c · New forms: poison pill, oils, a draught, baths, Qi Flow and incense (S44, Part 8)
- **Qi Flow Pill** (Earth): +20 % accumulation for an hour. When it wears off, the 15 toxicity it held back comes
  due. The recipe is the Alchemist Guild's Expert reward (V4d).
- **Viper Smoke Pill**, a poison pill. Thrown from quick-use, it bursts into a cloud: 4 % of max HP a second for
  5 s to everything within 90. It still bursts where it lands if it hits no one.
- **Weapon oils.** Viper Oil (poison) and Ember Oil (burn) coat the blade for 5 minutes. Each hit has a 20 % chance
  to carry the status. A second oil wipes off the first.
- **Riverreed Draught**, a liquid medicine: +30 % HP and a minor body injury mended.
  - A liquid takes two strikes, with no Condensation.
  - It goes straight to the new **Draught slot**, next to Quick-use on the HUD (key V). The slot shows the count
    and the time left.
  - It goes flat 10 minutes after it is made (`draught_expired`), the one thing in the game that spoils.
- **Medicinal baths** (Qi Unfurling 1).
  - A Bath station (a cedar tub) now stands in the retreat rooms and cave abodes.
  - A bath takes the seclusion slot. Choose *Medicinal bath* on the Seclusion page, or *Bathe* on the bath itself.
  - An hour's soak gives:

    | Bath | Body XP | Residue cleared | Foundation pill share |
    |---|---|---|---|
    | Copper Body Bath | +600 | 10 | 10 points lower |
    | Marrow-Washing Bath | +1,500 | 20 | 10 points lower |

  - A bath beyond your body tier injures the body. Body tiers go by body level: Copper Body from 18, Iron from 36,
    until the S48 trials arrive.
  - The two bath recipes come with the unlock.
- **Calm Heart Incense**: heart demon −10.
- **Murky Pill**: what a failed experiment leaves (V4d). It sells for a tael.
- **Fixes.**
  - A heal over time ("30 % HP over 5 s") now runs in a fight too, and resting no longer multiplies it. Before, a
    Healing Pill used mid-fight gave only its first fifth.
  - Accumulation and insight-rate bonuses are now added flat. A percentage of their zero base used to add nothing,
    so the Clear Mind Pill, Jade Carp Congee, raw Mist Lotus and the Sage-Born title had no effect. Data
    validation now guards this.
- **Tests:** the Qi Flow debt, oil chance and exclusivity, the smoke cloud, the draught's slot, strikes and expiry,
  both baths with the body-tier injury, and the incense.

### V4b · Herb natures, recipe roles and furnace blasts (S44, Part 8)
- **Herb natures.** Every herb is hot, cold or neutral:
  - hot: Riverreed Ginseng, Ember Pepper, Ember Cactus;
  - cold: Mist Lotus, Cloudtop Orchid, Frost Lotus;
  - neutral: Willow Moss, Soulbell Flower.

  Each hot herb in a recipe drives the Extraction band 8 % up the bar, and each cold herb draws it 8 % down. The
  item text says which.
- **The furnace's stages.** The three alchemy strikes are labelled Extraction, Fusion and Condensation. The
  Extraction label says which way the herbs push the band.
- **Recipe roles.** Recipe order gives each slot its role: Principal, Minister, Assistant, Envoy. The recipe card
  shows each slot's role and each herb's nature.
- **Substitutes** (Alchemy Dao tier 5):
  - *Swap* lets one herb stand in for another of the same nature, in a role it can fill;
  - the card marks what stands in for what;
  - the refine intent carries `substitute {from, to}`.
- **Herb conflicts** (`herb_conflicts.json`):
  - the pairs: Ember Pepper with Mist Lotus, Ember Pepper with Cloudtop Orchid, and venom sac with Soulbell Flower;
  - when a pair meets in one batch, the furnace blows: the batch is lost, the furnace loses 10 durability, and a
    minor body injury follows (`furnace_blast`, with a HUD warning);
  - the pair is remembered, and the recipe card warns before it happens again;
  - no authored recipe contains a conflicting pair, and data validation checks that.
- **Tests:** natures, the band shift, roles, substitute rules, a blast from each listed conflict, and the blast's
  cost.

### V4a · Furnaces, Beast Fire rank and the valley's Heavenly Flame (S44, Part 8)
- **Furnaces are equipment.** Each furnace is an item instance worn in the new furnace slot, apart from the eight
  worn slots. The first one you get goes straight into the slot. Choose another from the bag with *Use this
  furnace*.

  | Furnace | Grade | Batch | Heat | Filter | Extra pill | Source |
  |---|---|---|---|---|---|---|
  | Bronze Furnace | Plain | 3 | +0 % | 0 % | 0 % | Mei Qing |
  | Jadeiron Furnace | Earth | 5 | +5 % | 10 % | 5 % | Forge: Jadeiron ×8, Riverstone ×6, crab shell ×4 (Adept) |
  | Cloudsteel Furnace | Heaven | 8 | +8 % | 20 % | 10 % | Forge: Cloudsteel ×8, cloud feather ×4, serpent scale ×4 (Expert) |
  | Mistjade Furnace | Mystic | 10 | +10 % | 30 % | 15 % | Forge: Mystic ore ×6, roc feather ×4, vulture plume ×4 (Master) |
  | Nine-Dragon Cauldron | Heaven | 8 | +12 % | 20 % | 10 % | The Drowned Abbot's sealed vault (Spirit Awakening 3) |

- **What a furnace does.**
  - Enhancing a furnace at the forge steadies its heat, +1 % a level.
  - The impurity filter takes out its share of what each strike missed.
  - A furnace of the pill's own element adds 5 % to the quality roll. The Nine-Dragon Cauldron is Water, and every
    alchemy recipe now has an element.
  - Only the Nine-Dragon Cauldron reaches Grain, Halo and Soul on any fire.
- **Durability.**
  - A furnace has durability. At 0 it is cracked and refines nothing.
  - Mend it in the forge's Enhance mode, for its grade's metal: two for each 10 durability lost.
- **Old saves.** Furnaces in the key-item pouch become furnace instances, and the best one goes into the slot.
  The Earth-Vein Furnace, Cloud-Pattern Furnace and Mystic Tripod become the Jadeiron, Cloudsteel and Mistjade
  Furnaces.
- **Beast Fire** burns a beast core of rank 2 or more:
  - rank 2: Serpent Core and Guardian Stone;
  - rank 3: Jade Core;
  - a Pebble Core is rank 1, too weak.
- **Heavenly Flames.**
  - The valley's flame is now the **Mist Lantern Flame**, carried by the elite Weeping Lantern of the Forgotten
    Monastery and dropped the first time you defeat it.
  - The Cold Lamp Flame moves to the Thousand-Eye Toad under Mirrorwater Lake.
  - Alchemist Fen no longer hands over the Nine-Dragon Cauldron. She points you to the Abbot's vault instead.
- **Pages open faster.** Page scripts load in the background from the title screen, so the first time a page opens
  it no longer stalls (the slowest page went from about 130 ms to about 35 ms).
- **Tests.**
  - The furnace slot, swapping furnaces, batch refusal, enhancement heat, the filter and affinity arithmetic,
    cracked furnaces and their mend cost, Beast Fire rank, old-save migration and the flame source.
  - The valley run opens the vault at Spirit Awakening 3 and sets the Nine-Dragon Cauldron.

### V3c · Talisman craft and Shattered Relics (S47)
- **Talisman craft** (Qi Kindling 6). Old Scribe Bai in Artisan Row teaches it through the guided quest
  *Ink and Paper*. He opens the Talismans page, a tab of the crafting table.
- **Tracing.**
  - Each talisman has a stroke path. Trace it in one motion on the canvas.
  - Staying near the path and keeping an unhurried pace (0.6 to 5 s) set the quality, Flawed to Perfect.
  - Straying too far breaks the stroke and spoils one sheet of paper; the ink is kept.
  - Inks and spirit paper are made without tracing.
- **Talismans.** They work at the talisman's own grade and quality, never from the user's stats.
  - Attack: Flame (180% fire in a burst) and Thunder (240% thunder, with Shock).
  - Defence: Iron Wall, a shield of 20% max HP for 6 s.
  - Movement: Wind Step, one free dodge within 60 s, even on cooldown.
  - Concealment: Veil, which hides you from foes for 10 s.
  - Sealing: Binding, which roots the nearest foe. Bosses are Steadfast.
  - The Revival and Lightning Rod talismans move here from Formations.
- **Materials.**
  - Talisman paper and spirit paper (paper and Mist Lotus).
  - Cinnabar, sold at Stoneford's general store.
  - Beast-blood ink, from hound fangs and rat tails.
- **Data.** `talismans.json` holds base power by grade, quality multipliers, the stroke paths and the trace
  tolerances. Events: `talisman_crafted` (spoiled or not) and `talisman_used`.
- **Shattered Relics.**
  - The Drowned Abbot's first defeat leaves the Shattered Moon Blade.
  - An Expert smith at a forge restores it into the Moonlit Blade, a Heaven relic whose spirit still sleeps.
    It costs 6 Cloudsteel, 6 Refining Essence and 3000 taels.
  - The Restore button is on the shard's item details. Event: `relic_restored`.
- **Tests.**
  - `talisman_suite`: spoiled strokes, stroke quality, grade-fixed damage whatever your Qi attack, Iron Wall,
    Wind Step on cooldown, Binding, and the relic's gates.
  - The valley run writes the first Flame Talisman at Qi Kindling 6.

### V3c · Natal treasure, wardrobe, blood-drop bind and rogue cultivators (S47)
- **Natal treasure** (Heart Tempering 1).
  - Flag one weapon as Natal, in the forge's Natal mode.
  - It grows from kills and technique uses with it in hand, and from ore fed at the forge (20 XP a grade step), to
    natal level 10, +2% stats a level.
  - Its item level follows yours up to the top of the grade band above its own.
  - It breaks only to a boss's telegraphed shatter blow (the Tomb King's glaive sweep, the Hollow Behemoth's
    stampede) or to overcharging, a 5% chance a technique when your Spirit is below its control demand
    (10 + 5 a level).
  - Broken, its stats go dark and a meridian injury follows (a soul injury from Spirit Awakening), until a
    re-forge. A re-forge mends it, or at its cap carries it into the next band with its growth.
  - Item details show its level and item level. Events: `natal_grew` and `natal_broken`.
- **Wardrobe** (Heart Tempering 1): every look you wear joins the account's wardrobe. The Character page's
  Wardrobe tab lets any of them stand in for a slot's own look; stats do not change.
- **Blood-drop bind**: the first time a Plain to Heaven piece is worn, a drop of blood falls on it (`item_blooded`,
  cosmetic).
- **Rogue cultivators**: elites whose visible weapon or treasure is a guaranteed drop.
  - A Rogue Cultivator in the Drowned Grotto carries the Serpent-Tongue Jian.
  - A Rogue Mirror Adept on the Misty Slopes carries a Bright Mirror.
  - Both carry a Sealed Storage Pouch, which Appraisal opens into something from its own table.
- `natal_wardrobe_suite`: growth, the item-level cap, breaking only to shatter, re-forging, the wardrobe,
  blood-drop, rogue drops and the pouch.

### V3b · Flying sword, Sword Intent, dual loadout and self-detonation (S47)
- **Sword Release.** The Sword Dao's third tier teaches it; it goes on the skill arc.
  - The jian leaves your hand for 8 s, or until you use the technique again to call it back.
  - It homes on the nearest foe within 420, 1.5 strikes a second at 60% of the jian's attack. Each strike is a
    flying-sword projectile that stops at walls.
  - Meanwhile your hands fight with Qi palms: the fist combo at ×0.8.
  - While it is out, the sword hangs point-up over your shoulder between strikes.
  - It returns when the time runs out, when you are wounded, or when you lose the jian.
  - Events: `sword_released` and `sword_returned`.
- **Sword Intent.**
  - Consecutive jian hits (combo, techniques and the flying sword) stack up to 10, each +1% penetration.
  - At 10, a weaker foe may falter (a 10% Fear chance).
  - It fades 3 s after the last jian hit, and ten pips along the player panel's foot show it.
  - Event: `sword_intent_changed`.
- **Dual loadout** (Heart Tempering 1).
  - A second weapon waits in the spare slot: "Set as spare" in the bag.
  - The Swap button (R) trades it for the weapon in hand.
  - Each weapon keeps its own technique bar, and a swap never touches a Dao tier.
  - Event: `loadout_swapped`.
- **Self-detonation.** A spare artifact (an unworn piece of equipment, or a treasure) bursts around you for
  1.5 + 0.75 × grade × Qi attack within 180. It is destroyed, which is the one thing the game ever destroys, and
  only after you confirm. Event: `artifact_detonated`.
- `sword_loadout_suite`: the Dao teaches the art; the sword strikes, the palms stay active and the sword returns;
  Intent stacks and fades; the swap keeps each bar; detonation asks first.

### V3a · Gear upkeep at the forge (S47)
- **Enhancement pity.**
  - An enhancement from +5 upward can fail, and it never breaks the piece or takes a level.
  - Each failure adds 5% to the next try on that piece. The piece keeps its pity and shows it in its details;
    a success clears it.
  - The roll uses the affix stream.
- **Refining Essence** (a new material, from Salvage) steadies a try: +2.5% each, up to four.
- **Salvage** breaks any number of pieces into their grade's metal and Refining Essence (`salvage.json`:
  Plain copper; Common Riverstone and 1 essence; Earth Jadeiron and 3; Heaven Cloudsteel and 6; Mystic ore and 10;
  Spirit and Sage in their zone metals). Worn, bound and locked pieces are never salvaged. The intent is
  `salvage {items[]}`, and it emits `items_salvaged`.
- **Inherit** moves a piece's enhancement, less two levels, onto another piece for the same slot, for 2 Spirit
  Stones a level moved (`enhancement_inherited`).
- **Reroll and affix lock.**
  - A reroll rolls a piece's affixes again, and you choose to keep the old roll or take the new one.
  - Locking one affix keeps it through the reroll, and the reroll then costs double.
- **Forge modes** on the Crafts page: Recipes, Enhance, Inherit, Salvage and Reroll. Each shows the chance, pity,
  costs and returns before you commit.
- Enhancement uses each grade's own metal from `salvage.json`, so Spirit and Sage gear now eat Stormsteel and
  Sunglass instead of copper.
- `forge_upkeep_suite`: pity builds and resets, Inherit moves N − 2 in one slot, Salvage skips locked pieces, and
  a locked affix survives a reroll that costs double.

### V2d · The room verticality catalogue, room lint and Paths Above (S43 rules 14–15)
- **Every valley room is built to its v2 catalogue row** (tools/data/catalogue.py):
  - **Lotus Ferry:**
    - lofts sealed until The Runaway Kite;
    - Aunt Ping's lost ladle (a new quest) on a roof;
    - Home Lane's crates and well;
    - the roof chain and the watchtower;
    - the docks' boat deck and mast lookout;
    - stilt decks and drifting rafts in the Reed Shallows.
  - **Willow Path and Stoneford:**
    - willow branches and a later pine top;
    - Market Street's awnings and bell tower;
    - Artisan Row's scaffolds and chimney (the Tinkerer's Gear, a new item);
    - Stoneford Gate's walltop;
    - the Entry Trials rebuilt: Jade climbs roofs over moving planks, Cloud climbs ropes past a crumbling ledge.
  - **The sects:**
    - the Sword Court's plum-blossom poles and a Wall-Step pillar pair;
    - Elder Sung's rope bridge between peaks;
    - library floors at 120 and 240, sealed by rank.
  - **Fields and dungeons:**
    - scaffolds and a crane lift at the quarry;
    - a cracked slab in the Lower Pit that a Plunge breaks;
    - rafts, a moored chest and a lily-pad bounce in the Grey Pools;
    - sprint gaps and a Wall-Step pillar on the Sunken Causeway;
    - bamboo tiers and a bent-bamboo bounce;
    - rope bridges on Caravan Road and at the Gorge Mouth;
    - the Boss Den's wine shelves and the Abbot's bell ledges;
    - a Wall-Step shaft behind the falls.
- **Verticality pass for every other room** (tools/data/verticality.py):
  - standard heights and landings;
  - a raised route across 40% of wide rooms, with rope bridges where roofs are too far apart;
  - a second tier where a room has only one;
  - later ledges for a named art;
  - two ways up each tier;
  - loot lifted onto tiers.
- **Room lint and reach contract** (tools/data/room_lint.py) runs first in `tools/run_tests.sh`. All 122 rooms pass.
- **Paths Above:**
  - Every later ledge is a row in `paths_above.json` and in a new Codex tab.
  - Standing on one records it (`path_above_found`, with a toast).
  - The World map shows a faint wind glyph where your arts now open a ledge you have not stood on.
- **New kit art:**
  - rope bridges, a walltop, chimneys and stone pillars;
  - bamboo slat platforms, scaffolds and stilt decks, awnings, a causeway slab and a cracked slab;
  - log, rubble, lily-pad and bent-bamboo blocks.
- Monsters that live on tiers now also start on branches, canopies, stilts, scaffolds and causeways.

### V2c · Camera, heights in a fight, monster navigation and allies (S43 rules 10–13)
- **Camera.**
  - Rooms may set camera bounds and look-ahead.
  - The camera leads by a quarter of the velocity and follows the surface underfoot instead of the jump arc,
    settling in 0.4 s after a landing.
  - It follows falls of more than a tier and looks down 60 near a high edge.
  - The vertical range opens to 180 so high tiers stay in view.
- **Heights in a fight.**
  - Blows reach −30 to +60 of the attacker's height, and Qi and Soul techniques −10 to +80: from the ground
    you cannot hit someone on an 88 roof, only mid-jump.
  - Flyers hover at about 48 so grounded fighters can still reach them.
  - Every shot stops at blocks and building walls and passes platform decks.
- **Monsters move through vertical rooms.**
  - Each species has `movement {jump, climb, fly, drop}`. Each room builds a deterministic navigation graph
    of walk, jump, drop and climb edges, and melee monsters hop along it after their target.
  - A monster that cannot reach you waits beneath you. After 2 s it takes half damage from you, and after 6 s
    it goes home, healing 10 % a second.
  - Flyers sink toward the height they hunt at.
  - Archers, imps, frogs, toads and vultures start on raised tiers in five rooms.
- **Allies** walk on surfaces and follow along the graph. More than 480 away, or unable to reach you for 2 s,
  they blink to you in a puff of mist.
- **Landing ring** under an airborne player within 200 of the surface below. The minimap shows blocks,
  climbables and movers. Enemy shadows fall on the surface under them.
- **Tests:**
  - the melee and Qi bands, and shots against blocks and decks;
  - graph edges by species, a graph identical on two builds, and chained paths;
  - a bandit chasing up a ledge, a tortoise hitting the out-of-reach rule, and allies blinking after 2 s and
    past 480.

### V2b · Movement arts, volumes and movers (S43)
- **Four new movement arts**, each taught by a guided quest when the quest is accepted:
  - **Plunge** (*Outer Trial*, Bone Forging 4): Down + Attack in the air drops at 900. The landing strikes
    within 60 for 120 % damage and a 0.5 s stun, breaks jars and cracked floors, and has a 4 s cooldown.
  - **Falling Leaf Glide** (*Leaf on the Wind*, Falls Pool, Qi Kindling 3): hold Jump while falling. The fall
    is capped at 120 a second and drift is 10 % faster, for 2 QI a second. The Falls Pool gains a vine, a
    200 ledge and the waterfall's updraft.
  - **Swallow Dart** (*Swallow Dart*, the library's first floor, Qi Kindling 7): tap Evade in the air to dart
    140 while holding your height for 0.25 s, once per airtime, on the dodge's cooldown.
  - **Water Skimming** (the hermit's side quest *Skipping Stones*, Qi Unfurling 8): sprint across deep water.
    The pond under the hermit's stilts has a rock with a Mist Lotus on it and a raft that poles across.
- **Flight by holding Jump.** Hold Jump as you start to fall to take off. Flight replaces the glide where it
  is allowed and QI is above 10 %. In the air, hold Jump to rise, hold Evade to descend, and tap Evade to
  dash. Flight is refused indoors, on sect grounds, in dungeons and in `no_flight` volumes. The third-press
  take-off is gone.
- **Volumes** in room data:
  - shallow water: ×0.7, no sprint or dodge;
  - deep water: sink in 1 s and return to the last safe spot, or swim 30 s with Breath Control;
  - current, updraft, wind (a 4 s pulse, stronger at edges), bounce (700) and crumble (0.8 s, back after 5 s);
  - rising water keyed to events, hazard and no_flight.

  They are placed in the Flooded Gate (current), Falls Pool and Cliff Faces (updrafts), Windswept Ridge
  (wind), the Fairground (a bounce drum) and the Mudwater Tunnels (rotten boards). In the Serpent's
  Shallows the Riverbed Serpent floods the arena to 30 for 14 s at half health.
- **Movers.** A surface or block follows a path as a pure function of the room clock, in loop, pingpong or
  trigger mode, and carries its riders. The hermit's raft is the first.
- **Controls and feedback:**
  - techniques and attacks wait while climbing;
  - the climb-speed stat now counts;
  - a fall fades the screen briefly;
  - no safe spot is recorded in deep water, on a mover or on a crumbling floor.
- **Learning an art** shows a toast with its name and a one-line how-to. Each of the five arts has its own
  icon.
- **Data.** `data/movement.json` holds every traversal number, and data validation checks the solver
  against it. Every movement art in `secret_arts.json` names its `movement_art`, how-to and quest. The new
  events are `mover_boarded`, `volume_entered` and `volume_left`.
- **Tests.** The solver is tested at each art's numbers:
  - the glide lasts 1.5 s and covers about 300;
  - the dart covers 140 with no height lost;
  - a Plunge breaks a cracked floor.

  Every volume behaves as its table row says, movers replay identically, and rising water follows its
  event. Game-level tests cover the Plunge blow and stun, glide QI, the air dash and flight on sect grounds.
  The valley run plays the four new quests.

### V2a · Traversal engine (S43)
- **Surfaces have sides.** Each walk surface records which of its four edges are open. A platform is closed
  at the back (north) and open on the other three; the ground and ramps are closed all round. Walking off an
  open edge starts a fall; a closed edge stops you.
- **Blocks** (crates, walls, rocks, carts) are solid boxes: you walk around them, or jump onto their tops at
  40, 60, 80 or 110. A block is an obstacle and a small platform at once, open on every side.
- **Jump feel.** Coyote time 0.10 s after walking off an edge, and a 0.12 s jump buffer that fires on landing.
- **Cloud Ladder Step** (double jump, impulse 430, about 202 high from the ground) is learned in *Cloud Ladder*,
  a Qi Unfurling 6 guided quest from the librarians. It no longer comes free with the first realm.
- **Wall-Step** is learned in *Between Two Walls*, a Heart Tempering 4 guided quest at the Echo Cliffs. Push
  into a wall and jump to kick off it, up to three kicks per airtime; each kick springs away from the wall. The
  Echo Cliffs now have a shaft of two rock walls 100 apart that climbs to the 300 ledge.
- **Drop-through.** Down + Jump on a platform drops through it.
- **Mantle.** Falling past a ledge lip within 24 of your feet pulls you up onto it.
- **Climbables.** Ladders, ropes, vines and chains are their own objects, not ramps. Hold toward one for 0.3 s
  (or use the context button) to climb; jumping lets go. The Lotus Ferry hall ladder is the first.
- **Air attacks.** A basic attack in the air is a single stronger strike (×1.1) and slows drift less.
- **Falls.** Falling out of a room returns you to the last safe spot (0.3 s standing, at least 24 from an open
  edge) and costs 5 % of max HP, except in towns, the prologue and the Lotus Ferry.
- **Context button** (1165, 500) appears in a fight when a ladder or door is in reach, since Attack takes
  the main button then.
- **Doors** need Up held 0.3 s, so a passing jump no longer walks you through them.
- **Events:** `jumped`, `landed` (with fall height), `wall_kicked`, `art_used`, `climb_started`,
  `climb_finished` and `fell_out`.
- **Standard heights** 100 (one jump), 176 (double jump, two storeys) and 300 (flight only). The room
  catalogue uses them; docs/movement.md has the reach table.
- **Tests.** A traversal suite covers edges, blocks, coyote time, the buffer, the double jump, drop-through,
  mantle, climbing, Wall-Step and falls, and checks that a room's blocks and climbables reach its geometry. The
  valley run now plays *Cloud Ladder*, *A Treasure in Hand* and *Between Two Walls*.

### V1b · Pill rules follow Build Prompt v2 (S44)
- **Lifetime resistance** counts every 5 doses of a family as 1 (`pill_resistance {family: {count, doses}}`); a
  pill works at 1 ÷ (1 + 0.25 × count). Each major breakthrough drops every count by 1 and then halves it. A
  normal ten pills a realm now keeps pills near two-thirds strength, where the gap report's rule left them at 29 %.
- **Families come from data** (`family` on each pill, raw herb and core):
  - accumulation (Qi Gathering; herbs and cores that add Qi);
  - body (Bone Strengthening);
  - insight (Clear Mind);
  - soul (Soul Soothing);
  - support (Foundation Guard, Cleansing).

  Healing, restoration, antidote, purging and conversion pills are exempt. Pill details show what resistance
  leaves of a pill, or that a Pill Grain ignores it.
- **Foundation.** The share is pill QP ÷ total QP since the last major breakthrough, and resets at each major
  breakthrough. Beast cores count as pill QP. *Settle foundation* lowers the share by 5 points an hour and burns
  off 5 residue an hour.
- **Support pills.** After two failed attempts at the same breakthrough (`support_failures`), support pills stop
  lowering its risk.
- **Pill marks** by quality: Fine 1–2, Superior 2–4, Perfect 4–6, Grain 6–7, Halo 8, Soul 9.
- **Pill Halo** grows +1 % a day, to +20 %, while in a storage chest in a room of Qi density 2 or more. It no
  longer grows in the bag during seclusion.
- **Pill Soul** always carries its recipe's own `soul_effect`.
- **Events and saves.**
  - Events: `pill_resistance_changed` and `foundation_changed` are emitted.
  - Saves move to version 5: version 4 resistance, foundation and support-failure data migrate on load.
- **Tests.** `tools/run_tests.sh` now fails a suite that prints a script error. A runtime error used to abort a
  suite part-way and skip its remaining checks silently.

### V1a · Treasures, talismans and throwables follow Build Prompt v2 (S47, Part 8)
Build Prompt v2 folds the gap report into the build prompt and wins where they disagree (docs/v2_audit.md).
G2a's treasures now match its Part 8.
- **Treasures and sources.** Each treasure has a flat QI cost and, from Spirit Awakening 1, a Soul cost of a
  third of that. Their definitions are in `treasures.json`.

  | Treasure | Effect | Cost | Source |
  |---|---|---|---|
  | Practice Bell | stun 0.5 s, radius 100 | 25 s · 15 QI | *A Treasure in Hand*, the new Heart Tempering 1 guided quest from Elder Hu or Elder Sung; it opens Treasure slot 1 |
  | Bronze Bell | stun 1 s + Qi Seal 3 s, radius 150 | 20 s · 30 QI | Drowned Abbot, first clear |
  | Little Pagoda | holds one foe 4 s, an elite first; bosses immune | 30 s · 40 QI | Gu's Warehouse vault |
  | Bright Mirror | returns projectiles 2 s | 18 s · 25 QI | forged from Jadeiron ×6 and pearls ×2 (blueprint at Heart Tempering 1) |
  | Mountain Seal | 250 % Qi Attack, radius 120 | 25 s · 45 QI | Stone Guardian, rare drop |
  | Taming Cauldron | takes a beast below 20 % HP as its fixed materials, no loot roll | 40 s · 30 QI | Hermit Yao's Beast Hall |
  | Wisp Banner | three wisps fight for 10 s | 45 s · 50 QI | Bai Ling's quest line |
  | Sealing Gourd | drinks projectiles for 3 s | 20 s · 30 QI | Old Ma, after Spirit Awakening 1 |

- **Elder Hu's Talisman** (was the Heaven Splitting Talisman). It sits in a Treasure button and holds three
  charges of the Heaven-Splitting Palm (600 % Qi Attack), with no cooldown. Elder Hu gives it when you accept
  the Heart Trial. The button shows the charges left.
- **Throwables are forged:**
  - Iron Needles ×20 from Riverstone and a beetle shell;
  - Flying Knives ×10 from Jadeiron;
  - Thunderclap Pellets ×3 from ore dust, Ember Pepper and a lantern wick.

  The Lightning-Rod Talisman item exists, ready for tribulation.
- **Vessels** set the flight sprite and QI cost only. The speed changes and the Sealing Gourd's heal were
  inventions, and are gone.
- **HUD.** Treasure 1 is at (887, 470) and Treasure 2 at (799, 470), with the Z and X keys. The Pet button moved
  to (965, 560), clear of skill slot 2.
- **Events** use v2's names:
  - `treasure_used` for deployed treasures; the natural-treasure event is now `natural_treasure_used`;
  - `merit_changed`, `sin_changed`, `debt_recorded` and `debt_called`.
  - Effects `add_merit`, `add_sin`, `record_debt` and `add_residue`.
  - The event contract now lists every S43–S49 event the build emits.
- The Wisp Banner is described as formation light, not bound wisps, to stay clear of soul banners.

### G2a · Treasures, throwables, a talisman treasure and flight vessels (gap report priorities 4–5)
- **Two Treasure buttons** left of Guard (R and T on a keyboard). The first opens at Heart Tempering 1
  with the **Stilling Bell** (quest *Lines in the Sand*), the second at Spirit Awakening 1. Set a treasure
  from the bag. Each treasure is one action with a Qi cost and a cooldown, shown as a sweep on the button:
  - **Stilling Bell:** stuns foes within 220 for 1.5 s and seals their Qi for 4 s. Bosses only lose their Qi.
  - **Nine-Storey Pagoda:** a 4 s prison over the nearest foe, never a boss.
  - **Returning Mirror:** for 2 s every missile that reaches you flies back at its thrower.
  - **Mountain Seal:** 250 % attack to everything within 170, with knockback.
  - **Beast-Taking Cauldron:** takes a beast worn below 20 % HP whole, for twice its materials.
  - **Wisp Banner:** three wisps strike the nearest foes each second for 10 s.
  - **Sealing Gourd:** drinks every missile within reach for 3 s, each mending 1 % HP.

  The Mission Halls, Old Pan and the port peddler sell them. The Hollow Behemoth and the Gate Guardian
  drop the Seal and the Banner on their first defeat.
- **Throwables.** Throwing needles (three at once), flying knives (pierce one) and thunderclap pellets (burst
  and knockback) share a 1.2 s cooldown and can sit in quick-use. Needles and knives can be made at the forge.
- **Talisman treasure.** Elder Hu's gift, the **Heaven Splitting Talisman**, holds three charges of a 12,000
  damage cut, at its own power, not yours. The bag shows the charges left.
- **Flight vessels** ride in the key pouch; choose one in the bag:
  - **Flying Sword:** −20 % Qi, +25 % speed (the reward for *Riding the Wind*);
  - **Cloud Puff:** −35 % Qi, −5 % speed (a Mission Hall);
  - **Jade Gourd:** −15 % Qi, +10 % speed (the other Mission Hall);
  - **Maple Leaf:** −25 % Qi (the hermit's).

  Each is drawn under the rider in flight.
- **Fix: shots now strike short creatures.** Arrows, ranged Qi techniques and throwables fly at chest height, and
  their hit band stopped 36 units above the ground, so they passed over 30 of the 75 monsters (crabs, rats,
  frogs, foxes and every creature under 38 tall). The band now reaches the ground; a shot fired from the air
  still passes over them.
- A new temple-bell sound effect. The first treasure carried goes straight into Treasure 1. 36 new rules checks
  drive every treasure, throwable, the talisman and the vessels through the real authorities, plus the arrow
  regression. `--vessel=<id>` with `--fly` previews a vessel.

### G1 · What pills cost, heart demons, karma, fire and furnace (gap report priorities 1–3)
- **Lifetime pill resistance.** Each dose of a pill family (Qi, body, soul or insight) weakens the next:
  1 / (1 + 0.25 × doses). A major breakthrough forgets one dose. A Pill Grain slips past resistance. A support
  pill that has failed the same breakthrough twice stops lowering its risk.
- **Foundation.** Every great realm tracks how much of its Qi came from pills, raw herbs and cores.
  - Above 30 % the foundation is hollow: the next major breakthrough counts it as an unmet soft requirement,
    and a failure is always *Weak foundation*.
  - The new seclusion focus **Settle foundation** makes pill-given Qi your own and burns off residue.
- **Residue.** 5 % of all toxicity stays behind. Each 10 residue costs 1 % accumulation, up to −10 %.
  Purging Pills don't touch it. A **flawless Heaven's Cleansing** (not hit once) washes it all away.
- **Heart-demon meter (0–100).** It is fed by:
  - a changed method (+10);
  - a pill-forced breakthrough with two or more supports (+5);
  - a defeat (+3);
  - sin.

  Each 25 is a risk step at every major breakthrough and one more crimson **Heart Demon**, wearing your face,
  at the Trial of Reflections. Meditation wears it down. Myriad-Year Calm Incense now really clears 40.
- **Karma ledger.**
  - Merit comes from the Hollow Night rescues, resealing the Tomb, freeing Gu, burning the Black Ledger,
    and ten helping quests. 100 merit eases one great breakthrough in each realm.
  - Sin comes from leaving Gu in chains, sending the ledger pages home, and every purchase in Broker Mu's
    back room. Sin feeds the heart demon.
  - Named debts come back as letters. Freed, Gu repays you two days later; the Gu family remembers otherwise.
- **Fire and furnace** (the S15 "rare fire or special furnace", now defined).
  - Fires:
    - Charcoal takes a pill as far as Perfect.
    - Earth Fire, at a vent in Whitewater Gorge and on the Scorpion Flats, reaches Pill Grain.
    - Beast Fire, burning one beast core a batch, also reaches Pill Grain.
    - Heavenly Flames, absorbed for good, reach Halo and Soul. They are the Cold Lamp (Drowned Abbot),
      the Sunscar Throne Ember (Tomb King) and the Comet Tail (Captain Rao), each a Codex collectable.
  - Each fire widens the strike band. The Crafts page has a fire selector.
  - Furnaces are items that set the batch (Bronze 3, Earth-Vein 5, Cloud-Pattern 8, Mystic Tripod 10),
    with band, filter and yield-chance stats. Each is cast around the last at the forge.
    **Alchemist Fen's Nine-Dragon Cauldron** is a named furnace that reaches Soul on any fire.
- **Pill marks.** Every batch rolls 0–9 gold lines by quality, each +2 % effect, drawn on the slot. When a Halo or
  Soul pill forms, a coloured pill cloud boils up and nearby NPCs cry out.
- **Undefined rules settled.**
  - Pills never decay; the Codex says so.
  - Auto-refine teaches 25 % of the XP refining by hand does.
  - Herbs can be eaten raw in need (a third of a pill, twice the toxicity), and beast cores can be absorbed
    for Qi.
- The Cultivation page has a new **Heart** tab: the meter with its steps, merit, sin and debts, the foundation
  share against the hollow line, residue, and each pill family's resistance.
- 38 new rules checks drive every G1 rule through the real authorities.

### Text and button quality pass
- **Type.** Words and page figures are now set in Cormorant Garamond, as the style guide asks: semi-bold for
  text, bold for headers, with lining figures so "Lv 0" no longer reads as "Lv o". Previously every label was
  in the pixel face, drawn aliased at the phone's non-integer scale, which made glyph pixels uneven. Numbers
  over the world (damage, bar values) keep Pixelify Sans, now anti-aliased.
  - `JadeRiverSymbols.ttf` supplies ✓ ↻ ✦ ★, which both faces lack. It is a renamed DejaVu Sans subset,
    licence included.
  - World nameplates sit on a soft ink plate instead of a heavy outline.
- **HD UI kit** (`tools/ui/build_ui_hd.py`). Every frame, button, tab, slot, plaque, pill, toast, tooltip, bar
  and the dialogue paper is rendered as anti-aliased vector art at 3 texels per screen pixel:
  - gradient jade enamel and bevelled gold trim;
  - filigree corners with jade gems;
  - a paper dialogue box with lacquer seals.
  It is drawn through `HdStyleBox`, a nine-slice scaled by ⅓ with mipmapped linear filtering, so it is crisp
  from 1280×720 to 4K. The build checks that no ornament leaves its corner, since a leaking ornament would
  smear when stretched.
- **HUD buttons** are anti-aliased enamel discs with a gold bezel, a gloss arc and a soft gold halo when active.
  Empty technique slots show a faint cloud seal.
- The minimap title fits its header. The dialogue plaque leaves room for the speaker's name. The creator's
  arrows are proper ◀ ▶ buttons.

### Gap report audit (docs/gap_audit.md)
- Every proposal in the Xianxia Systems Gap Report is checked against the build: 2 present, 38 partial,
  71 missing. The game breaks none of the report's "stay out" rules.
- The missing systems are planned in seven phases (G1–G7) that follow the report's priority table.

### World movement pass (docs/movement.md)
- **Something to climb in every room.** An audit found 79 of 121 rooms flat. Now 7 of 122 are, all by design
  (insight rooms, the first hut, the home boat, story trials).
  - Fields, paths and dungeons get a one-jump ledge (110) and a double-jump ledge (220) with a chest on it.
  - Outdoor rooms from level 37 get a cloud bank at 320 that only fliers reach.
  - Towns get timber decks and halls get lofts.
  - Plum-blossom poles stand in the home sect's yard, and the elders' peaks and cave abodes get rock shelves.
- **Standable props.** Crates, barrels, tables, low walls, carts, boulders, sarcophagi and 9 more props in
  the walk strip are now solid blocks with tops, so a jump lands on them.
- **Secret arts that move you.** They were named in the design but never granted. Now:
  - **Wall-Step** (Heart Tempering 4): kick off a wall once in the air.
  - **Wind Blink** (Spirit Awakening 5): an air dodge that blinks 120 units, with a 10 s cooldown.
  - **Breath Control** (Qi Unfurling 3): opens the flooded shaft below the Scripture Well into the new
    **Drowned Grotto** (deep water, air pockets, drowned acolytes, a ledge chest).
  - **Appraisal Eye** (Qi Kindling 6): appraise without the tool.
  - **Lotus Heart Breathing** now does what it says: it heals 10% over 5 s below 30% HP, once a minute.
- New rules tests drive the real solver: one jump lands on 110 and not on 220, a double jump reaches 220,
  the cloud is out of double-jump reach, a crate takes a landing, and Wall-Step works once and only beside a wall.
- The Collection page no longer stalls its first frame (160–220 ms). Creature sheets load within a 12 ms budget
  per frame, and each sheet's drawn bounds are baked into `creature_art.json`.

### Phase E · the Starsea
- **The Shipwrights' Yard** at the west end of the Cloudgate Skydock: Navigator Sun's chart table, Shipwright
  Lao's slipway, an armillary sphere and the first Starsea dock.
- **Star charts and vessels (S16, Sage 3).** Two new crafts on the Crafts page, shown from Sage 3. Sighting
  stones on high places (the Yard, Rimefrost Summit, the Presence Terrace, the Riven Peak) give one star reading
  every ten minutes. Readings and sky ink make a route's chart (40 XP a route). Vessels are built on the slipway: the Cloud Skiff
  (smithing Adept) and the Storm Sloop (smithing and formations Adept, comet iron, half again as fast).
- **Starsea voyages (S18).** At a dock, a vessel and the route's chart set sail into an instanced crossing on
  the vessel's deck. The crossing lasts as long as the vessel takes: pirates board, wind kites dive, and the
  **star wind** strips Qi from anyone whose Spirit cannot hold it in (Starsea survival). The crossing ends in port
  at the far end. Falling overboard abandons it.
- **The Skyport Wreck** (Lv 76–81, Storm Ward 56–60), reached only by sailing: the Broken Pier, the Pirate
  Deck, the Riven Peak and the Starsea Launch (rest, teleport stone), with a wrecked-sky-port backdrop, an open
  Starsea backdrop for the crossing, and a new synthesized Starsea theme.
- Five new foes drawn with the avatar engine: the **Starsea Pirate**, the **Rogue Nine Peaks Disciple**,
  **Comet Captain Rao** and the Trial Hall's **Presences** (tinted phantoms, and the Ninth Presence).
- **Chapter 15, Pirates of the Starsea**:
  - Gu's Ledger: a page of the valley's secrets turns up at the auction.
  - The Skyport Wreck: chart, build, sail, take back the pages, and free Elder Gu or leave him.
  - Sect War: at Sage Sovereign 2, the defence of the Alliance Gate, with waves of pirates and deserters and then the captain. Burn the Black Ledger or send each page home. Afterwards the Alliance war gong calls a new battle every 20 hours, for Spirit Stones, comet iron and storm shards.
- **Chapter 16, The Presence Trial**:
  - Lu's Last Page, on the Riven Peak.
  - The Presence Trial: at Sage Sovereign 3, ninety seconds beneath the eight seats of the Trial Hall. Their Presence presses down, answered by Will; phantoms attack; the Ninth Presence arrives half-way. Passing it holds the key to Will Manifest, which the Expanse's ceiling still locks.
  - Stars Beyond: chart the Lantern Run, and the Launch's ring lights toward the Lantern Star Field (Act III).
- Act II systems from the v1.1 row:
  - **Elder's token** at Sage Sovereign 1: the training sect's token upgrades, the Elder rank follows, and home is a free teleport.
  - **Expanse Outpost**, a sect building from sect level 8: +1 Storm Ward per level for every member, and expeditions to three Expanse regions.
  - **Paired cultivation** from Sage 1: +15% accumulation while a companion sits with you.
  - **Rare Daos from teachers:**
    - Blood (Matriarch Tie);
    - Life and Death (Bone-Reader Xiu);
    - Emotion (Hermit Shuang).
    - Each has four tiers of stat bonuses and grows only after its teacher opens it.
  - The Expanse's own Laws (Fire, Metal, Thunder, Soul) now deepen past their valley caps there.
- Six side stories (The Deserters, Iron from a Comet, Clear Skies over the Peak and the three Dao lessons), three
  guided quests, five NPCs, six codex entries, seven titles and three achievements.
- Fixes: a tinted avatar enemy (a drowned acolyte, a phantom) kept its hit-flash white instead of its colour.
- Tests: two new valley_run sections (ae5, ae6) sail, build, fight the sect war and sit the Presence Trial through
  intents; 18 new rules checks cover docks, charts, vessels, the star wind, the outpost, rare Daos, zone caps and
  the Elder's token; data validation follows Starsea routes when it checks that every room can be reached.

### Phase D · Sunscar
- **The Sunscar Desert** (Lv 73–81, Storm Ward 45–50), south of Ironroot Hold down the desert road from the
  Clan Hearth: the Glass Dunes, the Scorpion Flats and the Worm Sea, a sand ground of wind ripples and desert
  glass, a new desert backdrop and a synthesized desert theme. The **Oasis of Bones** (rest, teleport stone)
  lies among the ribs of a giant beast, with Keeper Meng's stores and Bone-Reader Xiu.
- **The Tomb of Sunscar** (Lv 77, Storm Ward 55): the Sealed Gate, the Hall of Sand Kings, the Mirror Crypt and
  the **Throne of the Tomb King**, a dungeon boss who summons clay guards at 60% and enrages at 30%. Dungeon
  theme, tomb backdrop, statues, mirrors, sarcophagi and the King's throne.
- Four new monsters: the **Sandstorm Scorpion**, the burrowing **Dune Worm**, the **Terracotta Warden** and the
  **Tomb King of Sunscar**.
- Four new hazards: scorching heat (Essence; shrines give shade), sandstorms (Body; they push and blind),
  quicksand (Agility) and spike traps in the tomb (Agility).
- **Chapter 14, Sunscar**: Glass and Bone (follow the Pilgrim's caravan to the oasis), The Sealed Gate (cut the
  key's pieces out of the Dune Worms and read the gate's inscription, Insight 80), Sovereign (break through to
  Sage Sovereign 1) and The Tomb King (Lu's page in the Mirror Crypt, the King, and the sun seal: keep it, or put
  it back in his hand; either way the Grey Pilgrim leaves without it). Side stories: Cactus Water, Glass Teeth and
  Stingers for the Hold.
- **Sage-grade equipment**: sunsteel weapons and sunsilk armour (with the veiled weimao hat), forged from
  Sunglass and scorpion stingers from Sage Sovereign 1, and sold to Ironroot kin. Sunglass ore, Ember Cactus,
  the **Sovereign Settling Pill** (ends a new stage's consolidation), cactus water (+Essence against the heat),
  three titles and the King Sleeps achievement.
- Fixes: a boss's summoning phase now calls its own minions (the Thousand-Eye Toad summoned paper ghosts),
  phases can set the level of what they summon, and a new enrage phase shortens pauses and hardens blows.
  The Canyon Harpy's bleed was twenty times too strong. Act II delivery quests now take the goods they ask for.
  A burrower travelling underground now shows as a moving mound of sand or earth instead of vanishing.
- Tests: a new ae4 section plays chapter 14 end to end, buying Sage-grade gear before the tomb; the fight
  helper clears a boss's adds when they wear the player down.

### Room hazards (S17)
- The hazards rooms have always listed now act: **falling rocks** (Quarry Rim), **Hollow puddles** (Grey
  Pools), **the rapids current** (Rapids Terraces), **fog** (Misty Slopes), **wind gusts** (Windswept Ridge and
  the Gale Canyons), **lightning** (Thunderhorn Plains), **bitter cold** (Rimefrost Heights), and two the
  spec lists that no room used: **thorn thickets** in the Thicket Heart and **poison mist** from gas vents in
  the Mudwater tunnels.
- Each runs a readable cycle: a quiet tell (dust trickling, storm clouds, bubbles, a hiss), a warning with a
  broken amber border and a "!" mark that read without colour, the active blow, then a cooldown. A dodge
  through a strike avoids it; a shrine shelters from the cold; hazards start mid-cooldown, so nothing
  strikes on arrival, and safe rooms have none.
- One attribute answers each (Body for rocks, gusts, currents, cold, thorns and gas; Spirit for fog and the
  Hollow; Essence for lightning). A room asks k x (5 + its top Level); below that the effect falls to
  half as the answer nears, and once it is met pushes and statuses stop (a strike still lands at 35%).
  The room banner and the World map show each hazard with the attribute and value it asks.
- New thorn thicket and gas vent props, and eight synthesized sounds (rumble, rockfall, charge, thunder,
  gust, surge, hiss, frost). A `--hazard=phase[:fraction]` preview flag holds a room's hazards in one state.
- Tests: 19 new rules checks cover the answer formula, the cycle, strikes, dodging, gusts, currents,
  puddles and shelter.

### Phase C · Nine Peaks
- **Nine Peaks**, seat of the Alliance (town, teleport stone), reached by a second sky-ship route from the
  Skydock once the lake's mirror has spoken: the Alliance Gate, the Hall of Nine, the Auction Pavilion and
  the Presence Terrace, where the Alliance champion takes sparring challenges.
- **Alliance or the free road (S20).** "Nine Seats" ends in a choice kept on the character. The Alliance
  gives its token, the Factor's 10% discount and a smaller auction premium; the free road opens Broker
  Mu's back room (black-market lots) and the smallest premium. Envoy Lanshi changes your path once, for
  300 Spirit Stones. Titles for each: Alliance Envoy (+2 Storm Ward) and Free Cultivator (+3% drops).
- **NPC auction house (S21, Sage 1).** Four lots are open at all times, drawn from a pool of thirteen
  rare goods with staggered closing times. Five NPC bidders answer at once up to a limit they keep to
  themselves. A bid above it holds the lot; outbid stones return at once; a won lot arrives by mail.
  The house premium is 10%, 8% for the Alliance and 4% for the free road. A backward clock never closes
  a lot early.
- **Gale Canyons** (Lv 73–78, Storm Ward 35–42): the Canyon Mouth toll, the Kite Winds, the Harpy Roosts
  and the Windbridge (no flight), with the **Wind Kite** (a living swallow kite that throws wind
  blades), the **Canyon Harpy** and the veiled canyon brigands, under new canyon and Nine Peaks backdrops.
- **Ironroot Clan Hold (clans, Sage 2):** Hold Gate, Clan Hearth and Ancestor Hall. "Ironroot Blood"
  is the adoption: the warden's test of root, the Matriarch, and the ancestral tablets. Kin get the clan
  forge at 15% off and the Ironroot Kin title (+4% max HP).
- **Chapter 13, The Nine Peaks**: Nine Seats, The Canyon Toll (who pays the canyon toll in Hollow
  shards?) and Ironroot Blood, plus the guided Going Once at the auction block. Side stories: Silk on
  the Wind and Plumes for the Bellows.
- New materials (kite silk, harpy plume) and the Alliance and Ironroot tokens, with icons.
- Tests: a new ae3 section plays chapter 13 (path choice, factor discount, auction bids through the
  close and mail, the canyon, the clan and the path change); valley checkpoints now keep the run's clock.

### Phase B · Heights and lake
- **Rimefrost Heights** (Lv 67–72, Storm Ward 16–22): Frostpine Climb, the Snow Ape Ledges, Rimefrost
  Summit and the **Hermit's Ice Cave**, a hidden cave only Spirit Sense finds. Frost Lynx and Snow Ape,
  Frost Lotus herb patches, icicle-hung boulders and a snowbound parallax backdrop.
- **Mirrorwater Lake** (Lv 68–75, Storm Ward 22–28), reached by sky-ship from the Skydock: the Reedless
  Shore, the Mirror Shallows with their lotus lanterns, the Sentinel Causeway, the Lake Shrine and
  **Toad's Hollow**, home of the **Thousand-Eye Toad** (field boss, Lv 68). Azure Carp Dragonet and River
  Sentinel; a backdrop where the lake mirrors the floating peaks.
- **Chapter 12, The Grey Pilgrim**: Shards for Sale (a shadowless stranger buying Hollow shards),
  Frost and Silence (Hermit Shuang, a meditation in the ice cave) and The Mirror Remembers (the Lake
  Shrine's mirror shows the stranger and a young Lu; Lu's second journal page). Three side quests:
  Snow for the Cabinet, Clear Skies and A-Lan's Herd.
- New materials (rime fang, snow ape hide, dragonet scale, sentinel core, mirror eye, frost lotus) with
  icons, an ice-shard projectile, and the lake as a fishing spot.

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
