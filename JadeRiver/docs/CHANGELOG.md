# Changelog

## A rewarding first hour: techniques early, a faster Bone Forging, the story carries the floors

Research docs/research/player_motivation.md, items 3, 4, 5, 8 and 10 of its top ten; the first hour as built is in its
"As built" section and in docs/tutorial_order.md.
- **The first technique at Bone Forging 1, the second at the Weapon Hall.** Lu teaches Flowing Palm on his boat with
  the first breakthrough (The River Token's reward; its unlock realm is now Bone Forging 1). The skill ring and the
  Techniques page open at Bone Forging 1, so the palm takes its slot at once. The Weapon Hall, done, teaches the first
  art of the family in hand, from the arts the training halls and the library already keep: the jian's Cloudpiercing
  Stroke, the spear's Jade Thrust, fists' and gauntlets' Tiger Rush, the short blade's Reedcutter Slash and so on.
  Until the body has a Qi pool (Bone Forging 7) a technique costs no Qi, only its cooldown
  (`stats.json technique_cost.free_without_pool`, `CombatAuthority.breath_only`). A technique learned is its own
  moment (`moments.json` row `technique_learned`: its name, "tap it on the skill ring", the light gathering).
- **Bone Forging 1-4 take 600 / 900 / 1,200 / 1,600 progress** (was 1,200 / 3,200 / 3,200 / 3,200); Bone Forging 5-9
  take 3,700 each (was 3,200), so Qi Kindling 1 lands at 5.1 hours in balance_sim (target 5). The River Token's
  endowed bar starts at 98% (was 92%), so the boat's fifteen breaths fill it.
- **Chapter 2 opens at Bone Forging 2, and the story carries every floor.** The Entry Trial has no "Reach Bone Forging
  2" step; the Willow Path (35% of a stage), the fair and the trial (20%) carry Bone Forging 1 to 2, and Fish-Gutting
  Fists (45%, and the title River Rival) carries 2 to 3, the Weapon Hall's realm. Strange Tracks (chapter 2's floor
  Bone Forging 2; the marsh path opens there too) starts as the mentor's note the moment the Weapon Hall is done. When
  the story does wait on a Level, the tracker's Next entry names a second way to close it: a lesson or side quest on
  offer, or meditation and body training (`QuestAuthority._floor_other_way`). A story quest that follows a lesson now
  waits next (`story_waiting`), so between Fish-Gutting Fists and the Weapon Hall the Next is the Weapon Hall.
- **Nine early quests cut, merged or rewritten.** Morning Tide is under way from waking, Aunt Ping's tea in hand and the
  hut's door open (no teas to hunt, no Bag to open first). A Quiet River (Return) is gone: the fourth lesson done, Guo
  has Crab Trouble at once. Ma's Delivery is one step (sell the net). Fists First asks five on the stump and three on
  the dummy (was 12 and 5). Crab Trouble wants three shells, which drop every kill while he wants them, and pays the
  Straw Sandals with the hat. The Willow Path has no stump quota (was 30): Flowing Palm on a boarlet, five boarlets and
  the herd's elite (a kill objective may now ask for an elite). A Disciple's Chores is a side errand: two spots, and the
  third is the grey itself, with a cache of two spirit stone shards. Eyes for Qi sits 20 s (was 60) and pays a
  ten-year Riverreed Ginseng. Mei Qing's Errand asks the grey hides of the Humming Token's boarlets, not copper ore
  (which needed mining), and they drop every kill while she wants them. The Weapon Hall asks five dummy hits (was 15).
- **Breakthroughs show what they gave, and the look changes.** Every realm step's moment now carries a card, "What the
  breakthrough gave", each number that rose before → after with its gain (Level, Max HP, Physical attack...). The
  character wears an aura by realm (`moments.json auras`: a jade ring at Bone Forging 1, motes at 4, a Qi glow at 7,
  on to gold at Cloud Stride), drawn behind the avatar from plain shapes (no new pose), still with Reduce motion; the
  card names it when a breakthrough changes it.
- **Tests.** `tutorial_order` walks from waking to Strange Tracks with no test shortcut: the story reaches Bone Forging
  2 and 3 by itself, the first technique comes at Bone Forging 1 and the second at the Weapon Hall, and on a play clock
  (`prologue_run.play_s`: the simulated time, walking, a look at each new room, reading) something new comes at least
  every 3 minutes to minute 20 and every 5 to minute 60 (invariant 11); it prints the timeline. `prologue_run` no
  longer grinds to Bone Forging 2. `rules_tests` holds the Next entry's second way. Screenshots of the technique moment
  and the breakthrough cards in `docs/ui_p5/early_game/`.

## Starter gear: a weapon from the start

- **The weapon slot is open from the start, and the first monsters drop weapons** (`docs/research/player_motivation.md`
  items 1-2). A new character fights bare-handed with the slot drawn empty, not locked (Character and Bag pages); Uncle
  Guo's Fists First hands out his old Training Gauntlets, worn at once; the `weapons` unlock moves to that lesson and
  the smiths sell weapons from then on (the weapon Dao stays with the Weapon Hall). The first kill in the Reed Shallows
  always drops the first weapon, a Training Short Blade, with a "Your first weapon" strip, its beam and the equip
  prompt. The first rooms' foes (Mudshell Crab, Reedtail Rat, Old Snapper, Wild Boarlet, Mossback Toad) roll starter
  gear (`grades.json` `drop.starter`, 2% a kill, Old Snapper 25%): training gauntlets, jian, spear or short blade, or
  plain armour, at the par item Level with a weapon never above par quality, so balance_sim finds no weapon of the
  first rooms more than 2% over par attack; the character's first three pieces come by the 15th kill without one
  (`starter_drops`, saved). Tests: rules_tests `starter_gear_suite`, tutorial_order and prologue_run (the slot open,
  the gauntlets, the first kill's weapon and its equip prompt), balance_sim `_starter_checks`.

## Slain foes stay slain

- **Monsters no longer all come back the moment you re-enter a room.** Room load rebuilt every spawn point from the
  room data with no memory of kills (the respawn timers lived only in the loaded room). Now the character remembers
  each kill with the room (`rooms.<room>.slain`, saved), and a spawn point stays empty for its own time in game time
  (Clock), so time away counts: a common foe 1–3 minutes (its spawn's pace x6), an elite at least 10 minutes, a boss
  its own long timer (a field boss its account-wide one), so no boss returns on entry. Foes a quest step still needs
  (a kill count, Crab Trouble's shells) keep their quick pace. While you are in the room a foe returns only out of
  view. The Vigil's and balance maths keep their own `respawn_s`. A beaten boss also no longer returned after a loot pickup.
## Gauntlets are worn on the hands

- **Every gauntlet draws on both hands, in every pose.** The gauntlet family had no avatar look (its appearance was
  "none", the bare-fist look), so the ten gauntlets (Training to Lanternsteel, and the Stone Drum Gauntlets) showed
  only in their icons. `tools/art/bake_gauntlets.py` now draws weapon look `gauntlets` over the body's own hands in
  all 17 catalog actions, both facings, frame for frame: a steel fist shaded from the hand's tones, a bronze rim at
  the wrist and a cuff on a bare forearm. Each pixel sits just over the body layer that draws that hand (z 12, and
  z 92 over the jab and lotus fists), so the torso, sleeves, head and hair hide it where they hide the hand; a
  gauntlet still punches. `engine_tests` checks every gauntlet is drawn in every frame of every pose on the body;
  review sheets in `docs/mockups/gauntlets/`.

## Consumables show what they did

- **Every tea, pill, herb, core, draught and food says what it did.** Drinking the Herbal Tea (Granny's Remedy) showed
  nothing: `item_used` carried no result and nothing drew it; the tea heals over 5 s, only a fifth at once, and at full
  HP (as the prologue's player is) it changed nothing; the log that could have said so is not revealed yet. Now
  `InventoryAuthority.apply_use` reports each effect (`item_used.effects`, `gains`); the world floats the heal over the
  player ("+21 HP", or "HP already full"); the HUD writes "Herbal Tea: +21 HP over 5 s" (shown before the log is
  revealed), shows the heal still to come on the HP bar, and puts the tea's icon with its seconds left in the status
  row (buffs and statuses show their time too). Screenshots in `docs/ui_p5/guidance_fix/`.
## The equip prompt; the tracker at Bone Forging 3

- **A better piece offers itself.** Picked up or received, a piece that beats the one worn in its slot (an empty slot
  counts as worse) and can be worn now shows a small card at the right of the screen for 10 s (`EquipPrompt`): its
  icon and name, the gain the Bag's card names first and Combat Power (the same `StatRules.equip_change`, through
  `InventoryPage.card_rows`), Equip (the equip intent) and ×. It stands clear of the HUD's controls, the purse and the
  clear zone, only its two buttons take a tap, several wait their turn, and with Reduce motion on it does not slide.
  Screenshots in `docs/ui_p5/starter_gear/`.
- **At Bone Forging 3 the tracker leads to the Weapon Hall.** With Fish-Gutting Fists done, the next main quest
  (Strange Tracks) waits on Bone Forging 4, and the story's Next entry, which only looked at main quests, sent the
  tracker and the direction mark to the hunt for it at Willow Path West; the Weapon Hall, the lesson Bone Forging 3
  opens, was on offer and nothing led to it. With no quest of the story to take now, a lesson on offer now comes
  before the Level (`QuestAuthority._story_next`), and one under way leads the tracker itself. The `tutorial_order`
  walk now spars Shen Lian before the Weapon Hall, as a player does, and holds after every step that the tracker and
  the mark lead where the story goes next (invariant 9).
## Codex page-completion rewards (decision 27, mockup 18's two seals)
- **Every collection page has two seals, each with a gift, claimed once for the account.** Seal I: every card filled
  (50). Seal II: every card studied through (500, an elite 200, a boss 100: `kills_to_master`), after seal I. Earned
  the kill the condition first holds (a toast), claimed by the Account authority's `claim_collection_seal` from Claim
  on the book page (the seal stamps in, a toast lists the gift), saved as `collection_seals`. Gifts are data
  (`tools/data/economy.py`, `account_rules.json` `collection_seals`): one small defensive or finding stat for seal I,
  healing received, knockback resistance or mastery gain and a Bestiary Leaf of a page beast for seal II, every stat
  given to each character by `StatRules.rebuild` (source `collection:`); no attack or damage stat. The Codex draws
  both seals on the page head, the page's seals with rule, gift, bar and Claim, a filled card's bar on to its seal II
  mark, and Contents the seal to come; it opens at a page with a seal to claim. Tests: `rules_tests`' codex seals
  (earned exactly on the kill, once, in order, saved and loaded, gifts through the stat rules), `balance_sim`'s
  per-stat budgets and par Combat Power with every seal (+0.9% at Level 30, +0.6% at 99, +0.7% at 165; at most 3%).
  Screenshots in `docs/ui_p5/records/` (`codex_seals_*`).

## Guidance: the sect's first step, the story's Next entry, the Quick-use slot, the hut door, the attack button

Found on the Android build; each fixed at its cause and held by the walks (docs/tutorial_order.md).
- **After the sect choice the sect's first quest is under way.** The choice was recorded (sect, rank, token, method),
  but nothing took it up: the Entry Trial, which the fair's last words send you to, waited for Bone Forging 2 behind
  three unlocks, so at Bone Forging 1 no quest was active and the tracker went blank. The Entry Trial now starts the
  moment a sect is chosen; its first step, Bone Forging 2, leads to a hunting ground ("➤ Hunt at Willow Path West"),
  and the lessons it teaches still open at Bone Forging 2. The Willow Path likewise starts once Lu has handed you the
  River Token (it started at the breakthrough a moment before, pointing ashore while the boat was still shut), and an
  auto-taken lesson now unlocks its systems in the same pass (`GameAuthority._after_pass`).
- **Between main quests the tracker shows the story's Next entry, never a blank plate** (`QuestAuthority.story_next`):
  who gives the next quest and where ("Next: Fish-Gutting Fists · Talk to Shen Lian", ➤ Fairground), or what it still
  waits on and where to get it: another quest first (followed back through requirements and unlock triggers), or a
  Level ("Reach Level 21 (Qi Unfurling 3)", ➤ Hunt at Bend Shore: a field whose foes suit the character's Level, the
  ones P12's gap names). It is a tracker entry like the others, so the P1 direction mark, the P5a plate, the go button
  and the world map lead to it; the story's quests and lessons are always tracked (a full tracker drops a side quest).
  Race to the Tower's bell step threw a script error in the tracker (an objective by object id); fixed.
- **The Quick-use slot is on the HUD.** P5a rested the healing slot outside a fight, so Granny's Remedy asked for a
  slot the player never saw. At rest it is now drawn while a quest step asks for it (glowing, named "Quick-use"; a tap
  on the empty slot opens the Bag) and while it holds something to drink, clear of the open fan. The steps say what
  the player sees: "Bag: put Herbal Tea in Quick-use", "Drink a Herbal Tea: tap Quick-use".
- **The first quest cannot be skipped.** A quest whose step is to leave its room (Morning Tide's "Step outside") keeps
  the room's ways shut while it is on offer and until the steps before it are done, and says which on the door and on
  a try: "Before you go: Open your Bag" (`QuestAuthority.room_hold`, `WorldAuthority.portal_state`). The hut's door
  stays drawn as itself, shut. Taken pickups stay taken on a reload (Aunt Ping's teas came back).
- **In a fight the attack button attacks.** A herb, pickup, person or door in reach took the button whenever no foe
  was aggroed within 400 px (a foe walked up to, or one between blows, did not count). One rule now
  (`HUD.attack_first`): in the P5a fight state (a foe within the fight range, one engaged anywhere in the room, held a
  moment after) the button attacks and the offer waits in ring 2's context slot with its own glyph; at rest the context
  takes the button (mockup 02). Auto-hunt attacks directly and is unchanged.
- "Ready to hand in" no longer flashes for a quest that completes itself (the fair).
- **Tests**: `tutorial_order` holds every step to three more invariants (the control a step names drawn on the real
  HUD, no room left early, the attack button in every fight beside the Reed Shallows' herbs) and, with `valley_run`
  over every main quest of Acts I–III, to the story's guidance (`prologue_run.story_guidance`: the tracker never
  empty, every target a real room the player can walk to, the mark toward it, the Next entry's giver or hunting ground,
  the sect's first quest right after the choice). `rules_tests`: the Next entry (a giver through a chain, a Level),
  the healing slot at rest, the attack-first rule. Each fix, reverted, fails its suite.
- **Screenshots** from a new character (and one `valley_run` checkpoint) in `docs/ui_p5/guidance_fix/`.

## Tutorial order: the first fight, foes' HP bars, doors and quest talks (docs/tutorial_order.md)

Found on the Android build from a new character; each fixed at its cause and held by a new suite.
- **The first fight comes after the HP bars.** The East Gate to the Reed Shallows opened with Fists First, while the
  HP bar comes with Granny's Remedy and the foes' HP bars with Crab Trouble, so a player who went to Uncle Guo first
  fought crabs and rats with neither. The gate now opens with Crab Trouble (the quest that sends you there, after all
  four lessons); Guo's lines say so. Old Ma's and Granny Liu's Trade waits for Coins and Shops (buying needed it and
  the purse was off the HUD).
- **Foes in a fight show their HP bar.** Beyond the reveal above (not a regression of the P5a labels), a foe showed
  its bar only once hurt, so a Reedtail Rat biting you showed none. A foe now shows it from the moment it turns on
  you (`EnemyState.in_fight`, `EnemyView.shows_hp_bar`).
- **Every way into a building shows a door.** Old Ma's store drew an open counter and no door. The store's art now has
  its own plank door under a blue shop curtain in the right bay (`tools/props/defs_buildings.py`); every building prop
  names its doorway (`door` in `data/prop_art.json`) and `Room.building` stands the door portal in it (the Fisher's
  Hut's was 44 px off its door; the harbour's and the port's inns and shops too). A door's arrow and plate draw above
  the facade (they were hidden behind the building). The painted bell towers of the retreat rooms get a door at their
  foot, the Cloud Library's door moved onto the Sword Court hall's doors, the Beast Trial Grove's way stands clear of
  the bell tower, and the Wardens' Hall is a house with a door instead of a watch tower. `data_validation` holds every
  room to it (`PortalView.entrance`).
- **Taking a quest ends the talk.** The dialogue page talked again after an accept and stayed open on a shop, a gift
  or a farewell. `choose_dialogue` now hands back a conversation only when the same person has the next quest to give
  or take back (`QuestAuthority._then`); otherwise the page closes. Every quest-giver alike.
- **Tests**: `tutorial_order` (new) walks the Prologue and the start of Act I fists-first on the real dialogue page and
  checks after every step and tick: no room with foes in reach before the HP bars, every foe in a fight showing its bar,
  a door at every way into a building, the talk closing after each quest taken, each step's control on the HUD when its
  quest is taken. `prologue_run` is split into steps both runs share; `valley_run`'s page check is stricter.
- **Screenshots** from a new character in `docs/ui_p5/tutorial_fix/`.

## P13b · The Techniques page (docs/technique_plan.md "As built: P13b")

Built to the approved mockups 06 (tree, tree learned, lost arts; decisions 11, 18, 19).
- **One tree a tab.** The page is the whole screen: a rail of element seals (Time locked until its Level, then Lost
  Arts and Secret Arts), the chooser, the tree and the reading on carved jade-teal panels, the loadout dock below. A
  tab lays out the element's whole tree, every family side by side with its rings, notables, keystones and the Dao
  arts at its gate, on the element's chart; drag to move along it, tap a family to go to its arts, **Learned** to go
  from one learned art to the next.
- **The reading.** A chosen art shows your character in its pose, its numbers, its prerequisites ticked and crossed,
  the cost, and **Learn · N Realisations**: an art one passage out takes the passage with it. A learned art shows its
  mastery, its slot, Slot or Unslot, Rank up and Let go (its Realisations back); **Let all go** resets a tree.
- **The Dao bar follows the tab**: the free hand shows the tab's element Dao, a weapon its weapon Dao.
- **Lost Arts** is an album, one leaf an act: found arts pasted in, a manual you carry marked Unread with **Read**,
  every other leaf sealed alike and only counted (decision 19).
- The Inner Arts and stances are worn from the dock's drawer; the Secret Arts keep Concealment's false realms.
- **Tests**: `rules_tests techniques_page_suite` (layout, tabs, Learn and Let go, Read, decision 19 on the page, the
  Dao bar); `perf_tests` drags the biggest tree. Screenshots in `docs/ui_p5/techniques/`.

## P13a · Techniques at scale, the data (docs/technique_plan.md)

The techniques of Acts I–III are written, 3,171 in all: every weapon family and cultivation path has hundreds of arts,
each element grows a tree of its own, and the lost arts are found only by finding them. The page that draws the trees
is P13b; today's Techniques page is kept and draws the new arts' emblems.
- **The grammar in data** (`tools/data/technique_grammar.py`, `technique_gen.py`, `technique_hand.py`): an art is a
  FORM (24) × FAMILY (12 built, 16 planned) × ELEMENT (11) × PATH (five and the orthodox) × RING (13). The forms carry
  the shape and the line, the element its verb (Water pulls, Wood blooms, Formless strikes 10% harder with no verb),
  the path its rule and cost, the ring its grade, reach, extra targets and effect tier. Rows are baked and compact
  (`techniques.json`, 974 KB): a row keeps only what its form, ring, element and family do not give it. Every art
  plays its form's effect (the technique animations, decision 23); a keystone plays its template's.
- **Counts**: the trees of v1.2.x hold 1,773 arts (the plan's 1,768 and today's five twin cells): 1,661 in the cells of
  Acts I–III and 112 hand-named keystones; beside them 38 Dao arts and 52 lost techniques (62 lost arts with the Inner
  and Secret ones); the later acts' 1,308 arts are written and locked behind their act. Per tree 192 or 193 (Space 40);
  per family 138 own arts in Acts I–III (the free hand 142); per path of the cells: orthodox 889, Body 152, Blood 150,
  Buddhist 159, Poison 149, Confucian 162; Act I 797, II 468, III 508.
- **Names** from the lexicons only, at most 28 characters, unique, never another thing's name, and checked against a
  146-entry denylist exactly and within two edits: Backwater Swallows, Nightshade Riptide Net, Pine-Needle Burst,
  Scholar's Ghost-Light Shaft; keystones such as Hundred Springs Rising, Drums That Beat Themselves, Pyre That Answers
  Twice.
- **Today's 56 arts** keep their ids: 47 in cells (five cells hold two), five on Dao trunks, four become lost arts.
- **The trees** (`TechniqueTreeRules`, `ProgressionAuthority`): eleven trees (nine elements, Formless, Space from ring
  7; Time from ring 9 waits for v1.3) of twelve sectors in four kin groups, a passage a ring, a notable at each act's
  edge, four keystones an act. Realising a node costs Realisations (Level + 2 × major breakthroughs + Dao tiers +
  mastery tiers past 2); an art's node teaches it. Free out of combat node by node from the leaves, one free reset a
  tree each great realm, then a Clear Heart Incense (the sect Mission Halls). One heavy art (a keystone or a lost art)
  to a ring of four slots. Saves from before the trees light the routes to the arts they know, once.
- **Lost Arts** (roadmap decision 19): found only in the world, never hinted at. Steles (the insight stones, with a
  Rubbing Kit from the Stoneford General Store and a Dao tier, an hour or a season), 28 old writings in 24 rooms, six
  masters' last lessons (a choice beside what they already say), ten foes' manuals (rolled like named rows, sure by the
  pity-th kill, only while the art is lost), four quests, the auction, and Lu's journal (twelve more pages) for the
  Ferryman's Oar. The board counts an act's lost arts and shows a found art's full card; nothing names, draws or places
  an unfound one. Found twice, an art is a Manual Page.
- **Balance**: techniques still grow only through Might. The trees feed the one damage bucket (+15% at most by Level
  99, +25% by 165) and cut Qi cost within the 30% cap; the grade is +0/+10/+20%, flat from ring 3; the par main art now
  follows the grammar's Arc at the band's ring, and with its tree route lands on the plan's line within ±7% from Level
  20 to 165 (1.45 at 20, 3.51 at 60, 4.12 at 99, 4.71 at 165; +10% at 200).
- **Emblems**: today's 56 stay baked; the other 3,115 are composed in the game from one atlas of 361 layers at 64, 48
  and 32 px (466 KB), about 0.6 ms each at 64 px and then held. The icon build writes the same bytes twice.
- **Tests**: `data_validation` `technique_suite` (counts, filled rings, rules 1–3, 5 and 6 of §3.6, names and the
  denylist, reachability, poses) and `lost_art_suite`; every art resolves to an emblem; `rules_tests` `tree_suite`,
  `tree_migration_suite`, `lost_arts_suite` (with the no-leak board) and `tree_queries_suite`; `balance_sim` the
  technique line and the trees' share; `perf_tests` the file's size, v1.5's 4,350 rows read and filled in, the trees'
  index, emblem composition and the Techniques page; `contract_tests` the trees' intents and words.
- **Fixed on the way**: an art with no pose (Blood River Slash, Venom Needles) played "<null>"; it now plays the
  weapon's third stroke.
## Technique animations (docs/roadmap_master_ui.md, decision 23)

- **An FX animation library**: one frame-by-frame pixel-art effect per technique form, the 24 of
  `docs/technique_plan.md` §3.2, drawn by a deterministic generator (`tools/art/fx/`: `fxpix.py` the palette-index
  rasteriser, `elements.py` the eleven element palettes and flourishes, `forms.py` the 24 drawers, `build_fx.py` the
  build) into `art/fx/<form>.png` and `data/fx_art.json`. Slash arcs with smear frames, three-cut flurries, thrust
  trails with a point flash, lunges with afterimages, low sweeping crescents, crescents that form and launch, volleys
  from a muzzle flash, rain that falls and splashes, pillars that rise and flare, a crest that curls and travels,
  bursts that pop into a ring, seekers that gather and fly, a blade that spins out and is called back, snares that
  rise and knot, a counter's guard flash, a ward's dome closing, a chorus's sound rings and notes, blink afterimages
  and the arrival cut, a plunge's crater and cracks, the released sword's streak, an orbit of swarm blades, a seal
  stamp that falls and slams, a domain drawing itself, and an echo's ghost strike; four projectile loops (arc, volley,
  seeker, return).
- **Every element reads as itself** on every form, by a palette swap and its own flourishes: water in droplets and
  ripples, wood in leaves, fire in flame tongues and embers, earth in rock and dust, metal in shards and glints, wind
  in streaks, thunder in forked bolts, soul in thin rings and wisps, formless in plain ink flicks, space in stars
  over a dark rift, time in clock ticks and a half-there ghost of the frame before. Colours sit on the element
  colours and the Style A emblem ramps, so an art's effect matches its icon.
- **Three richness bands** per form for the vfx tiers 1–2, 3–4 and 5–7: thicker strokes, more particles, extra
  layers; the sprite itself grows 1×, 1.5×, 2× for the forms sized by tier, never past a strike's reach. 28 sheets,
  3.6 MB; a rebuild is byte-identical (`build_fx.py --verify`).
- **Wiring** (presentation only): every technique carries `vfx.anim` (its form) and `vfx.pose` (the catalogue action
  the effect is timed to; `combo_1` / `combo_3` for the wielded family's step that `meditate_burst` and a null
  action resolve to), written by `tools/data/technique_anim.py` from the plan's form table (a row P13 tags with
  `form` takes that). `World._cast` plays the sheet through a new `FxLayer` kind, `anim`, timed so its impact frame
  lands on the pose's hit frame (`attack_started`'s `windup`), mirrored for the facing, at the element's row and the
  tier's band, sized to the hitbox: a ring form snapped down so it never passes the true reach (a procedural ring
  still marks the edge), a wave's crest travelling the reach, a rain tiled across it, a pillar or a seal on the foe in
  reach. A technique's Qi bolt is drawn from its form's projectile loop. Reduce motion plays the calmest band and
  Battery saver the middle one at most; the sheets never fill the screen, so the flash limiter stays with the tint.
- **Preview**: `--cast=<technique>[:t]` now also holds the pose the cast would play on the avatar, resolved as the
  timeline resolves it, and lands its hits at the hit frame; with `--capture` the effect and the pose step a sixtieth
  a frame and the simulation holds still from the cast (`World.sim_frozen`, `FxLayer.fixed_step`), so a shot lands on
  the frame `t` names whatever the renderer's pace and shows the effect on the pose, not a boarlet's counter-attack.
  `--load=<folder>` now copies into `user://loaded_<folder name>/` rather than one shared `loaded_copy`, so two
  previews of different checkpoints run at once no longer clobber each other's copy.
- **Review**: `docs/mockups/fx/`: every form × element at each band's impact frame at 1× and 2×, a strip of every
  frame per form, the projectile loops, and in-game captures of one technique per form at four moments of the cast
  from the `ls6_end` checkpoint (its README lists them).
- **Tests**: `data_validation` `_fx_art_suite` (the 24 sheets exist at the size their spec says, a hit frame inside
  each, known anchor and size rules; every technique's animation is a built form and its pose an existing action or
  a combo alias every weapon family resolves); `rules_tests` `moments_suite` case 15 (bands by tier and under Reduce
  motion and Battery saver, element rows, half-step scales, an anim's facing, delay, length and row, a form without a
  sheet); `contract_tests` keeps `anim` in `FxLayer.KINDS`; `perf_tests` casts through the same path.
- **Not done, by design (`AGENTS.md`)**: no new body pose. Every form maps to an existing action; two poses would
  serve some forms better and are listed as follow-ups in the report (a true plunge from the air, a stance hold for
  Counter and Ward).

## Moments (docs/roadmap_master_ui.md, P6)

### P6e · The escalation curve
- **Every technique has a `vfx` block** (`techniques.py`): its tier, 1 to 7, is the band of the realm that teaches it
  (the valley's Common 1, Earth 2, Heaven 3; the Azure Expanse 4; the Lantern Star Field 5; 6 and 7 wait for their
  zones), its shape what it draws on cast, and its particles the hit spark's style. Today: tiers 1–5 hold 16, 22, 9, 1
  and 8 techniques; strike 15, bolt 11, ring 9, domain 9, wave 5, pillar 5, rain 2.
- **A technique's hits grow with its tier** (`moments.json` `vfx_tiers`, §5.2): the spark's count, size, reach and
  white core, the damage number's size, a ring at the caster's feet from tier 2, echo waves inside an area's edge from
  tier 3, one small shake per cast on its first hit from tier 3, and from tier 3 a wash of the element over the screen
  for 0.4 s. Tier 1 is today's look, so the first techniques do not change; a basic blow stays tier 1, and a
  companion's blow of a technique draws a tier lower.
- **Shapes drawn at the true reach** (§5.3–5.4): a slash that grows with the tier; a talisman wave along the reach; a
  ring at the reach with echo rings inside it, never beyond; a rain of streaks over the hitbox (`rain`, new); a pillar
  on the foe in reach; a ring and motes round the caster for a buff or heal; a bolt is its projectile.
- **Sparks by family and element** (§5.6): the brush's ink drops fall, the bell's and flute's (and Soul's) rings
  spread, fire's embers rise and flicker with a pale-gold heart, metal's, ice's and thunder's shards fall; the rest
  keep their squares.
- **Multi-hit numbers** (§5.5): the hits of one cast on one foe rise one after another, 18 px and 0.06 s apart,
  swaying left and right, six at most, and three or more add up to a total in pale gold a size up.
- **Large numbers** (§5.7): from 10,000 a number is written in three figures, 12.4K, 124K, 1.25M (`UiKit.short`, the
  style guide's §4 helper, which the P4 pass landed beside P6e and both now share). Damage numbers still follow
  Settings › Damage numbers.
- **The flash limiter covers tints** (§5.10): a technique's screen tint shares the one-a-second limit with every
  flash, is 0.3 as strong with Bright flashes off, and does not play with Reduce motion or Battery saver, which also
  thin sparks to tier 1's and tier 2's counts.
- Preview: `--cast=<technique>[:t]` draws a technique's cast and its hits on the foes in reach, submitting nothing.
- **Tests:** `moments_suite` case 12 (the tier rows by technique, a spark carrying its tier's count and size, a
  companion a tier lower, the spark styles, a tint under the settings and the limiter) and case 13 (three hits stacked
  18 px and 0.06 s apart on alternating sides then a total; seven hits show six and total seven; two, no total);
  `moments_data_suite` checks every technique's tier against its realm's band and grade, its
  shape and style, and that every shape draws `FxLayer` kinds; `perf_tests` plays the crowd under the major
  breakthrough and again with a Sword Swarm and a Cursive Storm cast each tenth of a second (each striking as many foes
  as many times as it does), inside the frame budget and the FX cap, and prints the view's share (MomentView.advance
  about 0.08 ms a frame; the whole moment, drawn, about 1–2 ms on a desktop).
- **P6 closed:** the screenshots are in `docs/moments/` (its README gives each one's checkpoint and flags); roadmap rows
  M5–M9, M22, M23 and M25 are Present, M6 with P9's intro pan and epithets still to come, and M24 stays Partial for
  P4's biome palette rule.
- **With the P4 pass merged:** a moment's counted line takes its "_one" twin (`plural` in a text source, through
  `Tx.plural`), so one bolt is "1 bolt"; the tribulation card's summary reads "Waves 3 · Bolts 9 · Struck 2"; and
  `UiKit.short` is the style guide's one helper.

### P6d · Rare finds, story beats and trials
- **A rare find** (`rare_drop`) is seen from across the room: a tall beam in the piece's colour stands over it and breathes
  until it is picked up, and a strip names it in its grade or quality colour under "A rare find", with `rare_chime`
  and a short buzz. Finds within 1.5 s share one strip (three names, then "+N"); in a fight it is a toast. What is
  rare is data (`moments.json` `rare`): a Perfect or Relic piece, a legend piece, a spirit animal's book, a treasure,
  and 49 named drops (every boss's unique drop and first-defeat reward, every set piece, every legendary chain piece).
- **A chapter closes** (`story_beat`): when the main quest that ends a chapter is handed in, after its dialogue page
  closes, thin ink bars close in and a band writes the chapter over the quest's name, "The chapter closes" under it,
  with the bell. `moments.json` `chapter_ends` names the closing quest of each of the 23 chapters (the Prologue and
  1–22), read from the quests.
- **A trial opens** on a band in pale gold with the bell (it was red text over the room), and ends when you leave.
- **Tests:** `moments_suite` case 4 on the real rows (after a major breakthrough: the Dao tier, then the title and the
  rare find by arrival), case 14 (the rare rule), two finds sharing a strip, and a chapter's close waiting for its
  page; `moments_data_suite` checks every rare find exists and one quest closes each chapter.

### P6c · Bosses and the loot fountain
- **The boss intro** (`boss_intro`): the first time a boss turns on you in a visit, two ink bars close in top and
  bottom (under the HUD, so its controls stay live), its name is written large with its Level under it, and war drums
  and a falling gong sound (`boss_sting`, new; captioned). The boss does not wait for it and nothing locks, so you keep
  control; until P9 gives the bosses epithets and lines, the Level stands in. It never plays twice in one visit.
- **The phase card** (`boss_phase`): the fight's stage as a gold numeral on an ink band under the boss bar, with the
  shake and the roar it had; one that would come late drops silently.
- **A boss's fall** (`boss_defeated`, `field_boss_defeated`): a pale-gold flash, its name on a band with "Defeated", and
  for a clean dungeon kill the Untouched line (it takes the Untouched achievement's toast into itself); `boss_fall`
  (new) sounds. The HUD's field-boss toast is now the row's fallback.
- **The loot fountain** (`loot_fountain`, §5.8): a boss's, a field boss's, a chest's, a Trial Tower floor's or a rift's
  drop leaves the drop point one piece after another and arcs to where it really lies, higher and longer the more
  there is (capped); rare pieces go last so they land on top, and the first rings `rare_chime` (new) as it lands; a
  boss's coins burst as six and close into one, with a pale-gold flash at the drop. A foe's or a jar's drop bounces as
  before, and so does every drop with Reduce motion. `LootView.launch` flies them.
- **`loot_dropped` says where the loot came from** (finding 6), the one simulation edit of P6: `source` is enemy,
  elite, boss, field_boss, fled, jar, chest, rift or tower, a payload key and nothing else.
- A moment that takes an event into itself now takes back the HUD's toast for it too (a breakthrough's unlock, its
  tribulation, the Untouched achievement). The pill cloud rings `rare_chime`, not the breakthrough gong.
- Previews: `--hold=t[:row]` holds a real moment at t, `--defeat-foe[=s]` defeats the first foe through Combat with its
  real drop, `--foe=` takes an HP share, and `--room=` works with `--load-slot`.
- **Tests:** `moments_suite` plays Big Toad Tan's den for real: his first aggro opens the intro and the second does not,
  his 49% opens the phase card, a phase cuts the major breakthrough (case 5), leaving the den ends his intro with no
  toast (case 8), his clean fall takes the Untouched line, his drop says `boss` and flies (and only bounces with Reduce
  motion), a jar's does not fly. `moments_data_suite`: a numeral for every boss phase, the fountain table.

### P6b · The breakthrough and the progression cards
- **The major breakthrough, as mockup 05 draws it** (`breakthrough_major`): the world darkens round you and the HUD
  recedes, sixteen motes gather into you, a column of light rises and three rings open at your feet (0–0.6 s); the
  great realm's name is written on an ink band in one brush stroke, "BREAKTHROUGH" over it and the step under it, and
  the stage is pressed on in a vermilion seal (0.6–1.4 s); the stats that rose climb in one after another, with the
  tribulation you weathered on a card beside them and what the new stage opens on a chip (1.4–2.4 s). It holds to
  3.6 s and fades by 4.0 s. Input comes back at 1.5 s; a tap before then skips to the full frame. Its sounds are the
  gong and chimes, then a brush stroke and a seal (both new), then the unlock bell only when something opens.
- **A minor breakthrough** writes its step and the Level it gave on a slim ink strip, with any unlock on a chip, and
  keeps the guzheng run (no shake). **A failed one** darkens the world a moment and says why and how to recover
  (`failure.<id>` now has words for all seven causes, finding 8), and after a tribulation how many bolts struck.
- **The tribulation** opens on a band over a shadowed sky that stays while the rite lasts; its storm is laid again
  every 5 s until the result, not once for 6 s (finding 10).
- **The silent milestones speak** (finding 4): a Dao tier (its line from the Dao's tiers, in the element's colour; a
  sixth tier on the large band), a craft's new rank, a guild rank with its title, a body tier, an earned title with its
  bonus and a seal, a spirit animal's new form and an awakened weapon in its grade's colour each have a strip. In a
  fight the celebration cards become toasts; the HUD's old toasts for them are gone.
- A level gained alone rings a short gong (new) instead of the guzheng run.
- **Reduce motion** (Settings › Accessibility, off by default): no camera moves or shakes, bands and cards fade in
  instead of wiping and sliding, bursts thin to tier 1's particles. Bright flashes off leaves a flash or a screen tint
  at 0.3 of its strength. One flash or tint a second from every source (the flash limiter).
- **Art and sound:** the ink band, a dry-brush stroke drawn by `tools/ui/build_ui_hd.py` (`art/ui/hd/ink_band__normal.png`);
  `brush_stroke`, `seal_press` and `gong_short` from the synth. New FX kinds `pillar` and `converge`; `spark` takes a
  count, size and a falling `shard` style, `ring` a count. Strings for every great realm's name, every craft, the
  stat labels and the cards.
- `--breakthrough[=t]` takes the character over its next step through the progression authority and holds the moment
  at t, for screenshots of the real stat rise.
- **Tests:** `moments_suite` runs the gather, the skip, the lock (F4: never more than 1.5 s), pages, fights, the
  settings and the held tribulation on the real rows, and a real minor breakthrough and a level gained by meditating;
  `moments_data_suite` checks the new text sources, the ink band and every great realm, craft, failure and stat string.

### P6a · The table and the view
- **`data/moments.json`** from the new `tools/data/moments.py` (run by `build_data.py` before the contract): one row per
  moment kind with its trigger event, filters, priority, duration, input lock, queue rule, layers, art and a sample
  payload, and the settings the view plays them by (`docs/moments_design.md` §3). The first eleven rows carry today's
  effects: the breakthrough channel, the breakthrough (every one, until P6b gives the major one its own row), a failed
  breakthrough, the realm phenomenon's clouds, the tribulation's storm, a level, a body level, an awakened weapon, a
  Halo or Soul pill, a boss's phase and a trial opening. The escalation curve's seven tiers are in the file too.
- **`MomentView`** (`scripts/presentation/moment_view.gd`, mounted with the world by `main.gd`) plays the rows:
  it gathers the events of one pass and resolves them together, so a breakthrough takes its level and its unlocks
  into itself; world layers run on the row's own clock; screen parts take one slot by priority, wait for pages, cut
  or queue, go stale into a toast, and end on leaving a room. `MomentRules` holds the matchers, the rare rule and the
  text and colour sources. Neither writes game state (`contract_tests`), and the headless suites run without them.
- **Moved out of `world.gd`, the HUD and the audio director into rows**, with nothing to see changed: the
  breakthrough's spiral, name, shake, sound and buzz; the channel ring; the failure line; the phenomenon's clouds and
  storm with the townsfolk's words; the level and body-level lines; the awakened weapon's wave; the pill cloud; the
  boss phase's shake and roar; a trial's name. The one change: **the doubled sounds play once** — a major breakthrough
  no longer rings `breakthrough` twice (once more for its clouds), and a tribulation no longer thunders twice; a
  breakthrough's level no longer rings its own chime under the breakthrough's. The pill cloud takes its quality's
  colour (Halo orange, Soul pale violet) as the grades do (M24).
- **A camera rig in `world.gd`:** `add_shake(s, amp)` is the one writer of the shake (the hazards call it too), and
  every shake stops with Screen shake off; `hold_camera` eases to a point and back for later rows.
- **The Damage numbers setting works** (finding 2): off, no damage number rises; Miss, Immune, Evade and Parry still do
  (`FxLayer.label`).
- **The contract:** `level_changed` and `room_event_started` join the catalogue; the payload keys of every event a
  moment reads are declared, and `contract_tests` checks every emit site names them. `FxLayer.KINDS` lists its kinds.
  `UiKit` names the three colours that left `world.gd` (`HEAVEN_CLOUD`, `HEAVEN_BOLT`, `BODY`).
- **`--moment=<id>[:t]`** plays a row with its sample payload for previews and screenshots.
- **Tests:** `data_validation` `moments_data_suite` (every trigger, merge, payload key, FX kind, sound, string, colour,
  anchor, lock and timing; the curve rises); `contract_tests` (declared payloads, `FxLayer.KINDS`, the moments scripts
  read only); `rules_tests` `moments_suite` (every real row plays from its sample and ends on time; the gather and
  merge, the queue order, a cut, stale and full queues, pages and fights, a room change, the settings and the lock on
  fixture rows).

## P12 · Might (docs/research/stat_scaling_research.md §6)

A par character now hits about 130K with a plain blow at Level 99 and 531K with its main art (929K on a crit), with
460K health; 571K a blow at Level 120. Bone Forging keeps its numbers. The research's §6.8 lists what differs from its
proposal and the numbers measured on the valley_run checkpoints before and after.
- **Might** (`stats.json` `might`, a table for Levels 0–200): ×1.30 a great realm, ×1.17 of it at the major
  breakthrough and the rest over the realm's Levels; Bone Forging climbs only to ×1.05, so Qi Kindling 1 is the first
  ×1.30 step; ×1.10 for each advanced state, ×1.18 an Inner Heaven rank, +2% a World Genesis Level. It multiplies the
  character's three attacks, max HP and three defences (a `might` modifier, so gear and buffs scale with them), never
  max Qi or max Soul, and every monster's armour at its Level. The defence constant grows with the attacker's Might, so a
  same-Level cut is what it was.
- **The par character** (`stats.json` `par`, `StatRules.par` and `par_step`): a steady cultivator of the jian at every
  Level (gear three Levels behind at Fine, then Superior and Perfect, enhanced a Level a dozen; the Sword Dao and the
  main art's mastery by realm; an attack affix; the sets' damage%; crits), modelled in `stats.py` with the rules' own
  formulas and built with the real rules in `balance_sim`, which agree within 1%. The Codex's Realms entry shows it at
  your Level.
- **Monsters from par**: a normal foe has 3.5 par blows of health (never below today's) and a blow of 6% of par health
  after par's armour (8% under Level 20); under Level 10 the old curves stand. Elites ×6 health, ×1.5 attack. The twelve
  bosses have the par DPS of their Level times their par time (Big Toad Tan 46.7K at 90 s, the Nebula Leviathan 121M at
  300 s); a boss's plain blow is 15%.
- **The damage formula**: the energy multiplier becomes a Qi edge (1.00–1.30) on Qi and Soul blows only; one additive
  bucket of damage%, elemental power and (against elites and bosses) boss damage; a product of final-damage sources;
  three new stats (`damage_pct`, `boss_damage`, `final_damage`). Combat Power has no energy term. A damage-over-time share
  of an elite's or a boss's health is capped at 60% of the caster's attack a second. An ally struck by a foe stands
  behind its owner's armour.
- **Numbers**: `UiKit.short` ("18.2K", "136K", "1.27M"; units in `ui.num.*`) for damage numbers, pool bars of 100,000 and
  more, and every page number from ten million.
- **Chapter floors**: every main quest of chapters 2–22 asks its chapter's floor (Bone Forging 4 to Sphere Lord 2; new
  for chapters 16, 18, 21 and 22), floors only; the later acts' floors are recorded in `quests.json`. The quest log names
  the floor, your Level and the fastest ways there. The Copperjaw Box now follows The Tide Breaks, which opens Tinker
  Mei's bastion.
- **Conversions**: the Soul Lantern Ward shields 10% of max HP; a body technique short of QI spends the same share of max
  HP; rooms recommend the par CP at their middle Level and the Heaven Ranking's rivals take the par CP at theirs.
- **Saves**: an old save's health grows by the Might of its Level, once (character minor version 1).
- **Tests**: `balance_sim` gains the research's ten checks (par_hit, ttk, blow, boss_par, smooth, realm_step, cp_rec,
  digits, chapter_floor, pacing) and plays on to Sphere Lord 3 (133 h); `rules_tests` gains `might_suite`; valley_run
  gains the labelled par-up shortcut at each section start from Qi Kindling 1 and a labelled "par pace" for bosses
  (sized to 20 s of its own blows: the scripted fighter neither strikes with a main art at par nor dodges), and its
  checkpoints are regenerated. On them a Level 98 blow went from 2,850 to 85K and a normal foe's blow from 2.9% to 5.7%
  of health.

## The Copperjaw swarm's creature art (v1.2 Phase D)

- **The swarm has a sheet of its own.** `copperjaw_swarm` (`tools/art/creatures/copperjaw_swarm.py`, flying, cell
  128): eleven small copper beetles at three depths, each a copper wing-case oval with a seam and pronotum band, a
  chitin head, pale-gold jaws and, when its cases lift, two pale wing blurs, the cases flicking from beetle to beetle
  so the cloud buzzes. Idle hangs and drifts, walk streams forward with streaks, windup draws back into a ball inside
  a tightening copper ring (held), attack lances forward as a spearhead and bites on frame 1, hurt scatters the cloud
  with copper dust, death rains the beetles down onto their backs and fades. `copperjaw_queen` is the same cloud led
  by a large gold-cased Queen with a pale-gold crown. The swarm config (`stats.swarm`) names them as `art` and
  `queen_art`; `Game.pets.swarm_art` picks the Queen's once she has risen. The Swarm tab shows the cloud on the wing
  on a stage beside its numbers, and while the box is open clouds of beetles circle the bearer in the world (three at
  fifty beetles, five at thousands, the far half behind the body), drawn from the sheet. `data_validation` checks
  both sheets exist and fly; `--beetle-swarm` opens the box for previews. The review sheets (2x, 1x, 8x close-ups)
  and in-game shots from the `ls6_end` checkpoint are in `docs/mockups/creatures/copperjaw_swarm/`.

## P4b · Icons in Style A: the pipeline and the display (docs/mockups/icon_study)

- **The pipeline** (`tools/icons/`, README "How to convert a family"): `pix.py` gains the HD mode the study
  prototyped (`SCanvas`, `Frame`, 7-level bands, `PixelPainter` with its texture, rim-light and selective-outline
  passes); `palette.py` gains `Mat` / `mat7` / `M`, material kinds, and grade kits from Plain to Sphere (Sovereign,
  Will and Sphere are new). Each family module declares `ART`: 32 (legacy) until every icon in it has an HD drawing,
  then 64 (HUD glyphs 32). An HD family builds its icons at 1:1 plus native `@48` (techniques) and `@32` renders, and
  the manifest lists them as `<id>@<px>`. `--only <family> --review-dir` writes the family in the 76 px slot at 1x and
  2x and in context (a Bag grid, the HUD rings); `--preview-hd` shows an unfinished family in the game.
- **The study's twelve icons** are the first HD drawings, in their own families (weapons, armour, pills, herbs,
  minerals, beast parts, workshop, techniques, HUD), behind each family's `ART`, so nothing on screen changes until a
  family flips. The study's Style A library is folded in (the study now renders from the families); from Style B come
  the domed technique disc with a shadow under the mark and a glass crescent in more steps.
- **The display**: every icon is drawn through `SpriteCache.draw_icon`, at a whole-number scale of its art and on
  whole pixels, never filtered (review I2). Page slots are 76 px (`Page.SLOT`: a 64 px icon at 1:1, a legacy icon at
  2x) or 44 px in list rows (`Page.SLOT_SMALL`: 32 px); the Bag keeps the figure between its worn slots, with a
  five-column grid. The HUD takes an HD technique's native 48 and an item's native 32; a legacy technique shows at 2x
  in its ring, HUD glyphs at 32 (2x). The slot draws a soft grade halo behind Mystic items and above. The kit CSS and
  the kit sheet have the 76 px slot. A `ui_suite` rule checks every icon on every page, and `icon_draw_suite` the fit.
- **Pills in Style A** (`tools/icons/families/pills.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/pills/`): the 33 pills redrawn at 64 px with native `@32` renders for the HUD item ring,
  The vessel is now the kind of pill (a jar heals and restores, a footed bottle is taken at
  a breakthrough, a gourd is a draught, a round box remakes the body or a method, a paper wrap holds loose pills) and
  the grade its material and trim (a cloth cap, a jade plug, a silver cloud lid, a domed lid with a gem finial; ring
  handles and the glow from Mystic up; Law and Monarch in night steel and rose gold), driven from one table; the
  effect marks are shapes, and the legacy 32 px code is gone.
- **The HUD family is redrawn in Style A**: all 73 glyphs are HD drawings at 32 art px
  (`families/hud.py`, `ART = 32`), a pale-gold face with a lit edge, a warm shade edge and one highlight under the ink
  outline, shown 1:1 in the button rings and at 2x in the attack ring and on the menu tiles. The attack button's
  weapons share one diagonal frame and the shaft, blade and grip builders; the button glyphs share the book, bust,
  arrow and chest templates. The ASCII tables and the legacy glyph painter are gone. Sheets and in-game screenshots
  from the valley_run checkpoints in `docs/mockups/icon_families/hud/`.
- **Herbs in Style A** (`tools/icons/families/herbs.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/herbs/`): the 26 icons (16 herbs, 6 seeds, spring water, spirit soil, the dyed root and
  rice wine) redrawn at 64 px with native `@32` renders, each herb living plant matter on the clump of earth, stone,
  snow or water it grows from, with leaf ribs, petals, roots, fruit and stems. The nine species drawers take the age
  from one table and show it by form, never by colour alone: an older root is larger with more growth rings and root
  hairs (gold at a hundred years, gold to the tips at a thousand, pale as jade at ten thousand), an older lotus has a
  taller pair of petals and a fuller seed head, an older orchid a third bloom, an older soulbell a third bell, an older
  pepper two dark full pods; leaf veins turn gold at a hundred years, and a Mystic herb and above carries its spirit
  aura as stepped glow bands. The seeds share one hemp pouch with a tag stamped in the herb's colour and their own seeds
  spilled beside it. The legacy 32 px code is gone.
- **Techniques in Style A, as composed emblems** (`families/techniques.py`, `ART = 64`; the sheets and in-game shots
  in `docs/mockups/icon_families/techniques/`): the 66 technique icons are composed by one
  `emblem(element, form, family, grade, kind, path)` from parts drawn once and kept as tables, the technique plan's
  emblem grammar (§3.9): eleven element discs (the domed disc with the keyline under the mark), the 24 forms' marks
  with the family's weapon inset (sixteen weapons and the free hand's palm), rims for the thirteen grades and the four
  kinds (secret art, keystone, Dao art, lost art), the five path stamps, and hand marks for the arts off the grammar's
  line. A technique's row comes from `data/techniques.json` and its form from `FORM_OF`; a path art's mark takes the
  path's colour as well as its stamp. Rendered at 64 with native 48 (the HUD ring) and 32. The 66 hand-drawn legacy
  marks are gone.
- **Minerals in Style A** (`tools/icons/families/minerals.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/minerals/`): the 75 icons (9 ores, the spirit stones and shard, the fuel crystals, the
  stones and cores, the Act II and III materials, the two currencies, the six essence salts and the 40 beast cores)
  redrawn at 64 px with native `@32` renders, one language per kind: raw ore is its material in a chunk of rock with
  stone grain (copper nuggets, jade veins, a crystal cluster, a glass lump with its sand crust); the comet-iron ingot
  shows its three faces and the metal's sheen and reflection bands; a cut crystal or spirit stone has a table, crown
  facets and light pooling through its shade side; a polished stone is a disc, a stele or a chip with an inlay; a core
  is a sphere with a bright heart in its element's shape (a flame, waves, a leaf, peaks, a curl, a bolt, an eye, a
  blade, a star, a ring); the salts are a heap of grains in a footed dish. The templates (rock, nugget, crystal, cut
  gem, core, dish and heap) are driven from tables: the spirit stones grow and gain gold prongs, the beast cores grow
  by rank tier and gain a band, a swirl of light, then a coil and a glint, the salts a richer dish; a Mystic mineral and
  above carries its aura as stepped glow bands. The legacy 32 px code is gone.
- **Beast parts in Style A** (`tools/icons/families/beast_parts.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/beast_parts/`): the 62 parts and the 21 pet-gear ladder pieces (collars, beast
  talismans and saddles, taken over from `banded.py`) redrawn at 64 px with native `@32` renders, each part as the
  material it is in the colour of its beast: fur in strands down a pegged pelt, scales with their growth ridges and
  keels, horn and claw with a keratin sheen and the grain along them, feathers with barbs swept back to the quill,
  through-lit glass, jade and cores with the light pooling on the far side (the Gravity Core with its rings of bent
  light). The kinds share one drawing each (hide, scale, fang, feather, vial, pouch, heap, shard, core) and every icon
  comes from one table. The grade is form and trim (`GRADE_HD`): a plain part is raw, a common one tied with hemp and
  pegged with wood, from Earth bound in the grade's silk with a cap, peg or bead in its metal, and from Mystic the
  aura in the beast's own light at the grade's strength; the ladders take a grade's kit for the band, plaque, seat,
  scales, cord and buckle. The legacy 32 px drawings are gone, except two helpers the unconverted families import.
- **Armour, the gourds, the cape and the soul talisman in Style A** (`tools/icons/families/armour.py`, `ART = 64`;
  the sheets and in-game shots in `docs/mockups/icon_families/armour/`): the 47 icons (nine hats, robes, trousers and
  boots, the mistjade cape, the cloud talisman and the nine spirit gourds, the Sovereign and Will rows folded in from
  `banded.py`) redrawn at 64 px with native `@32` renders. Each piece is shown as it is worn: its row in
  `data/artifacts.json` gives the cut of the avatar layer (`appearance`) and its garment dye (`dye`, now the
  `palette.dye_*` ramps), so the straw douli, the jade circlet, the tied silk band, the gold crown with its jade pin
  and the veiled hat, the vest, the scoop-necked tunic, the sect robe with crossed lapels, the cloud tunic and the
  scholar's coat, the loose, straight, martial, cuffed and scholar trousers, and the leather boots, folded greaves and
  cloth shoes match the figure beside them, with cloth folds, riveted plates and lacquer in their own textures. The
  grade is the kit, Plain to Sphere: the trim of cuffs, hem and collar, the fittings, the plates and greaves in the
  grade's metal, the gem, and the grade's mark (jadeiron plates and scales, cloud scrolls, gold lines, a lightning
  stitch, desert-glass beads, driftglass studs, star dots, pearls), with the aura from Mystic up; the gourds carry the
  same ladder. The legacy 32 px code is gone.
- **Weapons in Style A** (`tools/icons/families/weapons.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/weapons/`): the 103 weapon icons (eleven families at nine grades, Training to
  Lanternsteel, the Sovereign and Will ladders and the brush and bell ladders taken over from `banded.py`, and the
  Wardens' four pieces) redrawn at 64 px with native `@32` renders. Every weapon lies on the study's diagonal frame
  (the bell mouth down-right, the gauntlet a fist over its cuff) and every family is one builder on the shared tassel,
  grip, fitting, blade and gem builders, so the family is the silhouette, after the held sprite: the jian's straight
  blade under a winged guard, the sabre broad and curved under a disc with a ring pommel, the short blade a leaf, the
  spear's leaf head with its tassel on a long shaft, the staff's crook, the recurve bow on its string, the fan open on
  its sticks, the flute with its holes and cord, the brush with its tuft dipped in ink, the bell with its cord and
  clapper. The grade is the kit (`palette.kit`, Plain to Sphere) as material, fittings and work, never a colour
  alone: a wooden blade with its grain and a hemp lattice, iron with a plain fuller, a jade inlay, silver cloud
  curls, gold runes down a dark fuller, a lightning zigzag, desert-glass beads on an ember line, driftglass diamonds
  in a driftteal line, star dots with a starlight edge; a gem in the guard from Earth, a metal bead on the tassel and
  the glow from Mystic; the same work runs along a bow's limb, a fan's leaf, a cuff or a bell's waist. The Ink-Warden's
  Brush keeps its black lacquer collar and falling drop, the Starwrit Brush its lantern-ash tip lit at the point, the
  Warden's Hand-bell its bronze and cloud scroll, the Tidebreak Bell its cage lattice and cold blue mouth. The legacy
  32 px drawings and the recolour rows are gone; `banded.py` keeps only the Sovereign and Will armour, hats and gourds
  and the four furnaces.
- **Fish, insects, critters and food in Style A** (`tools/icons/families/fish.py`, `insects.py`, `critters.py`,
  `food.py`, each `ART = 64`; the sheets and in-game shots in `docs/mockups/icon_families/<family>/`): the posts'
  catches and the dishes, 41 icons, redrawn at 64 px with native `@32` renders, each catch the living animal drawn
  with care in its species' colours (after its sprite where it has one). The seven fish are side views on one
  template in a body frame (`fish.Axis`): the body profile, a forked tail and the dorsal, pectoral, pelvic and anal
  fins with their rays, rows of overlapping scales, the gill cover, a lateral line, the eye with its ring and
  catch-light, and the species' marks (the perch's bars and spiny dorsal, the trout's spots and pink band, the carp's
  gold-edged scales and barbels, the salmon's kype and spray, the moon carp's crescent, the minnows' shoal, the eel's
  ribbon fin and rings). The eight insects are specimens from above, the side or three-quarter on, with jointed legs,
  antennae, compound eyes and segmented abdomens (the firefly's lit tail with its own halo, the cicada's clear veined
  wings, the scarab's jade-sheened shell, the moth's eyespots and comb antennae, the mantis's raised spined forelegs
  and spark, the cricket's cocked hind leg, the locust's fanned ember wings, the mote's star-dusted points). The nine
  critters are bodies from a spine of discs with fur in strands, faces with ringed eyes, noses and whiskers, ears
  with their pink, paws with toes (the frog's gold eyes, the hare's misty ear tips, the marmot's cloud tail, the
  hedgehog's sparking quills, the stoat's black tail tip, the fox's sail ears, the gecko's star spots, the tied
  pearly pelt). The grade is form and trim on `beast_parts.GRADE_HD`, never colour alone: a plain catch as it came;
  from Common a stringer loop at a fish's jaw, a thread round an insect's waist or a cord at a critter's neck, hemp
  at Common and the grade's silk with a metal bead from Earth; the aura from Mystic up. The 17 dishes are their
  vessel and contents with steam and gloss on shared cup, bowl, plate and pot templates, in the grade's ware
  (`WARE_HD`, after the pills' ladder: bare earthenware, a bronze band, porcelain with jade, skyware with silver,
  storm glaze and sand glaze with their aura; a pot takes the grade's metal for its handles and band). Every icon
  comes from its module's table. The legacy 32 px code of the four families is gone.

- **Treasures, legends, Qi jades and the workshop in Style A** (`tools/icons/families/treasures.py`, `legends.py`,
  `jades.py`, `workshop.py`, each `ART = 64`; the sheets and in-game shots in `docs/mockups/icon_families/<family>/`):
  98 icons redrawn at 64 px with native `@32` renders. The 31 treasures are each the object the item is, on shared
  builders: the upright temple bell (a plain iron practice bell against the bronze bell studded with jade), the
  three-legged vessel (the taming cauldron with its gold claw, the grimed curio, the furnaces), the paper talisman
  strip, the Heavenly Flame on its dish (the Lantern Heart in its bronze cage); the pagoda's jade roofs with silver
  ridges, the mirror with its gold bosses, the mountain seal's beast and red face, the wisp banner with its three
  lights, the sealing gourd under the pills' silver cloud lid, the nine swords fanned from their lacquer case, the
  needles, knives and pellet, the flying sword streaming Qi, the cloud, the jade gourd and the maple leaf. The furnace
  ladder (`furnace_hd` on `palette.kit`, the four Act II and III furnaces taken over from `banded.py`, now deleted)
  shows the grade as the walls' metal, the grade's work round the belly (the weapons' `work_hd`), the trim of the rim
  and ears and the jewel as the lid's finial, the Nine-Dragon Cauldron with its gold dragons; the aura from Mystic up
  in the object's own light. The 28 legend pieces are the thing each is named (`legends.PIECES_HD`: a knuckle, a
  cuff, a heart; a hilt, a blade, a soul bead; a spearhead, a shaft, a tassel; an edge, a grip, a sheath; an iron
  cap, an oak shaft, a knot; a spine, an edge, a guard; a rib, a silk, a pin; a mouthpiece, a jade body, a tassel; a
  limb, a string, a sight), built from the weapons' builders in the chain's tint (`chain_kit`) with gold Mystic
  fittings, a lit jagged break where a piece was broken (`broken_hd`) and the Mystic aura in the tint; the Weapon
  Soul Crystal is a gold crystal with an ember flame in it. The 13 jades: five cut stones in bezels (`cut_hd`, any
  outline: a cushion, a marquise, a twelve-sided round, a hexagon, a kite with an eye) and eight bi discs (`bi_hd`)
  carved with their signs in their own light. The 26 workshop goods: thread-bound books (`book_hd`, the cover's
  cloth naming the element, a paw for the pet skill books; the torn manual with its corner gone) and tied scrolls
  with element tags (`EMBLEMS_HD`), the grimed ding, the river-jade bi against its glass fake with a chip and
  bubbles, old coins on a string, the spirit wood with Qi in its grain, the puppet's jade heart in its pegged frame,
  the three array plates with their arrays lit, and the Sphere Comprehension Stone with its folded world and the Will
  aura. The legacy 32 px drawings of all four modules are gone.

- **Miscellany and tools in Style A** (`tools/icons/families/misc.py` and `tools.py`, both `ART = 64`; the sheets and
  in-game shots in `docs/mockups/icon_families/misc/` and `tools/`): the 93 miscellany icons and the 65 tools and
  talismans redrawn at 64 px with native `@32` renders, one language per kind. Miscellany: a manual or a page is paper
  with its laid lines and columns of script (a stance figure, a seal, a river sketch), a closed scroll lies on the
  diagonal with its tie and tag, a hand scroll opens between its rollers; a token hangs upright from a cord loop and
  bead with a tassel, its face carved inside a keyline or a gold rim (the sect discs, the alliance summits, the entry
  gate, the elders' knots and crests); a bag is a drawstring pouch tied at the neck (the storage pouch's seal slip, the
  five beast bags with the paw sewn on in straw, hide, cloud silk, deep jade and starweave); the eggs sit in their
  nests, the wyrm egg on its night cushion; incense stands in a bowl or, for the Roll-Call's hour incense, a tall cup
  whose label carries the hours in pixel numerals over a holder that grows from clay to bronze, porcelain, jade and
  gold; the rite tablets stand in stepped pedestals with their crests; the Keeping Post's components (cord, rivets, the
  brick, lacquer, the whetstone, spirit glue), the Starsea charts and ships, the sun seal and its pieces, the treasures
  and the Ash and Tide pieces are one-offs on the shared builders (the weapons' tassel, the beast parts' cords, vials
  and heaps, the herbs' leaves and lotus, the minerals' dish). Tools: the four Keeping Post ladders (picks, sickles,
  rods, hoop nets, nine tiers each) and the snare kits are one builder each on the weapons' diagonal frame and kit
  builders, painting with the tier's head metal (copper, iron, jadeiron, cloudsteel, mistjade, stormsteel, then
  sunglass and driftglass through-lit) over the grade's kit, so a tier shows as material, fittings and work, never as
  colour alone: a hemp grip on plain wood, then leather on darkwood with the guard metal's butt cap, eye ring, ferrule
  or reel, a gem at the eye from Earth, the grade's work down the head (a fuller, a jade inlay, cloud curls, gold
  runes, a lightning zigzag, ember beads, driftglass diamonds), capped points from Mystic and the aura as stepped glow
  bands; a net's mesh grows finer up the ladder. A talisman is a strip of yellow paper with red bars, its glyph traced
  in the element's ink over the maker's seal; the offerings sit on the minerals' footed dish. The legacy 32 px code is
  gone from both modules.

- **Status icons and markers in Style A** (`tools/icons/families/status.py` and `markers.py`, both `ART = 24`; the
  sheets and in-game shots in `docs/mockups/icon_families/status/` and `markers/`): the last two families, 34 status
  icons and 17 map and quest markers, redrawn at 24 px, the size they are shown at, with a native `@12` render of each
  status icon for the row over an enemy's name. The pipeline gains the 24 px size (`registry.HD_SIZE`, `VARIANTS`) and
  the game draws 24 and 12 natively (`SpriteCache.ICON_PX`; the technique emblems keep their own sizes). The colour
  language stays, never alone: every glyph has its own silhouette. An injury is its object with a red crack cut into
  the outline (a bone, a broken meridian arch with its acupoints, a cracked soul orb); stability is the stepped
  foundation built one tier at a time, red, yellow, jade and gold, the unstable slab cracked and chipped; a buff is its
  object (a sword, a shield, chevrons) with the green up-arrow; cultivation states are jade and gold (the seated figure
  under a halo, the gold diamond with its jade core); the debuffs are their own shapes (a flame, a venom drop, an
  hourglass, a dazed ring of stars, gripping roots, drips from a wound, a snowflake, a bolt, a sealed Qi orb, a split
  shield, a spiral, a ghost, a horned demon, a circuit whose arm turns back, a bolted eye). The markers are one bold
  object each (the gold quest diamond, the blue side-quest seal, the question mark, a figure, a sycee, the medicine
  gourd, the anvil, the shrine, the open and the sealed portal, the teleport stone, the crown, the skull, a leaf, a
  crystal on its rock, a fish, the player's arrow). `asciiart.py` and the unused `glyphs.py` are gone with the ASCII
  sprites; no legacy family remains.

## Wikis and volume (docs/roadmap_master_ui.md, P7)

### P7b · part 1
The data work of `docs/item_plan.md` §6, steps 1–7, 9 and 11–13 (step 10 for the new bases); the named pieces (step 8)
come next. Where it differs from the plan, the plan's §6 says so.
- **Drops are about six pieces an hour of hunting, not fifteen.** Every loot table's chance and quality floor follow
  §4.1 (normal foes 1.2% from Flawed, elites 8% from Common, chests 30/50/60% from Fine); the quality tables, the weapon
  share, the elite spawn's extra roll and the named rows' rules sit in `grades.json` `drop`, which `LootRules` and the
  World read. A weapon drop is in the family in hand one time in three, so about 76% of what drops fits the character.
  The item Level stops at the top of the highest grade with banded bases: Act III drops Sovereign and Will gear.
  Salvage gives half as much Refining Essence again.
- **`balance_sim` measures it:** 29 field regions, each room hunted 20 hours with the real rolls, 5.9 pieces an hour
  on average and every grade inside its §4.4 targets (pieces, Fine, Superior, Perfect), every region at least 3 an
  hour, 75–81% of the pieces usable by each archetype, no named piece from the random roll.
- **Named pieces carry tags** (archetype, zone, element, path, fixed affixes): a fixed affix is always on and counts
  half again on its archetype's path, and each named piece adds 2% elemental power of its element. The Serpent-Tongue
  Jian and the Tidebreak Bastion's brushes and bells have theirs; loot tables gain `named` and `elite_named` rows. Big
  Toad Tan's Mudwater Cleaver comes on his first defeat (the unread `unique_drop` is gone), his robe and the Drowned
  Abbot's hat and boots are 8% rows, the Crane Trousers a Cloudpeak Roc's 0.2%.
- **Ten affixes** (Qi and soul attack, Essence, knockback, max Soul in the random pools; taming, crafting control, pet
  damage, array power and melody power only on named pieces) and **three stats**: pet damage (your animal's strike),
  array power (an Array Plate's time and the killing array's blow) and melody power (the melody's slow and heals, the
  bell's ring, Clear Heart Melody).
- **Sets** move to `tools/data/gear.py` with an archetype, tier, element and path; on its path a set's 2-piece bonus
  counts double. The six archetype lines and their 6-piece mechanics are in `gear.json`, each read by the rule that owns
  it: Unbroken (a shield before a blow breaks 30% HP), Honed Intent (two more stacks of Sword Intent, fading half as
  fast), Venom Hand (the Poison Body at 35%, oils on more hits), Kin-Bond (your animal takes 15% less), Living Array
  (wider rings that lay the brush's talisman) and Sustained Note (a melody's first 3 s free).
- **71 banded bases:** the brush and the bell at every grade from Training, so the formation master and the bell
  musician have a weapon from Level 1; Driftsteel and Lanternsteel weapons in all eleven families, Starsilk and
  Lanternsilk armour and the Driftglass and Lantern Gourds (Sovereign and Will); collars, beast talismans and saddles up
  to Will; the Stormsteel to Lanternsteel furnaces. Each has its wear level, sockets, salvage row, forge recipe and a
  shop, and an icon drawn with its family's existing function (`tools/icons/families/banded.py`).
- **Every item has a source; `KNOWN_SOURCE_GAPS` is empty.** Hermit Yao sells metal cores and Peddler Ning star and
  space cores (two a day each: shop rows can now carry a daily limit); the Weeping Lantern, Mirror Wisp and Terracotta
  Warden carry soul cores; a Stormgrass Stag grazes the Thunderhorn Plains on the Cloud Stag's sheet (the peak wood
  core); the high Spirit Stone from the Sovereign of Sages achievement, the Nine Peaks auction and the Tomb and Wreck
  chests; the beast bags, incense sticks, snare kits, rite tablets and gourds from shops, activity chests, the Trial
  Tower's guardian floors (first clear), auctions and the forge; the sect sets' hats, trousers and boots at their
  Mission Halls; the Crane Robe from "Crane Falls at Dawn" and the Crane Boots from the Cloud Stepper.
- **Checks:** `rules_tests` `drop_pool_suite` (family bias, the Level cap, the pool, quality tables, named rows,
  named-only affixes) and `set_suite` (paths, each line's bonuses and mechanic, the three stats' readers);
  `data_validation` `gear_suite` (tags, fixed affixes from the archetype's pool, every set sourced and completable, every
  banded grade whole, loot-table fields and named rows; the named count per archetype and zone waits for step 8).
- The wiki shows named tags, sets, the drop rules, named rows and shop limits.
- Two checks that depended on the account's random seed now pass whatever it draws: the Cloud Steps run in `rules_tests`
  finishes under the fastest time a rival can draw, and valley_run's Hollowed Wyrmlings get to land their grey flame
  when the fight ends before one has.

### P7a · The item and monster wikis
- **`docs/wiki/items.md`**: all 614 items (472 items, 142 pieces of equipment) by type or slot, each with its icon,
  grade, iLv, stats or effect, requirement, description and every source the data gives, with rates: enemy drops,
  jars and chests, the Trial Tower, gathering nodes and posts, gardens, recipes and other crafts, shops and auctions,
  quest and unlock rewards, mail. Banded equipment names the foes and chests whose roll can make it.
- **`docs/wiki/monsters.md`**: all 121 enemies by zone, each with its sheet, room spawns, other appearances (events,
  set pieces, the tower, tides, summons), level band, stats, attacks and phases, and its full drop table with rates.
- Written by `tools/dev/wiki.py` from `data/` alone and byte-identical on every run; `build_data.py` runs it after a
  full build.
- **Every item has a source.** A `data_validation` rule scans the same channels; an item nothing hands out carries an
  explicit mark instead (`"source": "story"`, `"system"` or `"later"`): the starting gourd, the dyed root, the murky
  pill, the Evergreen Heart fruit and the two Monarch pills. 43 real gaps are listed in the suite's
  `KNOWN_SOURCE_GAPS` for P7b: 12 beast cores no beast carries, the high Spirit Stone, two beast bags, five Hour
  Incenses and the Wandering Incense, six snare kits and rite tablets, three gourds, and 13 set pieces (the sect sets'
  hats, trousers and boots, and the Mudwater, Drowned Abbot and Crane sets but the Abbot's robe).
- **Found by the scan, fixed:**
  - The banded equipment roll could make one of the nine legendary weapons or the two imitation relics as ordinary
    Mystic or Heaven gear; they come only from their chains and the forge now (`drop_pool_suite`).
  - Loot group rows carried a `chance` the roll never read (a group rolls once and picks by weight); the rows keep
    only their weight, and `data_validation` refuses a chance on a group row.
  - The Lantern Star Field's ledge and cloud chests used the valley's chest tables; each zone's chests now use its own
    table (`ZONE_CHESTS` in `tools/data/world.py`). The Flame Heart's ledge chest, in a room with no Level of its own,
    was Level 1; a chest in such a room now takes its region's top Level.
  - The mist trout's valley spot at the Falls Pool had no fishing spot; it has one in the shallows now.
- **Left for P7b:** 43 items nothing in the data hands out (12 beast cores, incense sticks, snare kits and rite tablets,
  three gourds, the sect sets' hats, trousers and boots, pieces of the Mudwater, Drowned and Crane sets,
  `spirit_stone_high`, two beast bags). `data_validation` lists them in `KNOWN_SOURCE_GAPS`: a new unsourced item
  fails, and a listed item fails once it gains a source, so the list only shrinks.

## The UI review and restyle (docs/roadmap_master_ui.md, P2–P5)

### P5 · The first pages with their own identity (`docs/page_identity.md`, decisions 14–16)
- **The foundation** (`docs/page_identity.md` §8, How a page takes its identity). A page declares what it is,
  `Page.Identity`: its `SURFACE` material, whether the shared window frame stays round it, its own title mount, its
  layout signature and its opening. Page then draws the page's surface in the standard window rect in place of the
  shared window, inks the title on the page's own mount and draws the tabs in the page's own form, while the close
  button, Esc and a tap outside, primary buttons with inked labels, the text tokens, the type scale and the 48 px
  targets stay Page's. Pages that declare nothing keep today's look exactly.
- **Every word is measured on what it sits on.** A page with its own surface names its grounds as it draws them
  (`ground`, `face`, `panel`), and the `ui_suite` measures every plain word it draws on the ground under it (4.5:1, or
  3:1 from 20 px). It found the washed slips too light for `MIST` (4.21), so words there are `PAPER`.
- **Motion by the reduced-motion rule** (`docs/moments_design.md` §4.6, page_identity §6): `unfold()` runs a page's
  opening over its declared time (0.35 s at most) and a tap finishes it; under Reduce motion nothing moves and the
  page only fades in, over 0.2 s. Every target is live from the first frame.
- **Tokens.** The twenty `SURFACE` materials of page_identity §7 join `UiKit` (and `cloth_wash`, the washed slips), each
  a mix of two tokens, with `TEXT_ON` rows for those words are drawn on; the talisman's red ink and the zither's
  strings, which had the names `cinnabar` and `silk`, are `cinnabar_ink` and `qin_silk`, unchanged in colour. New Page
  helpers: `rich` (words in several colours), `rounded`, `glow`, and `grade_rims` (slots ring an item in its grade's
  colour and mark a rolled quality with a gem).
- **The Character page as the jade-slip record** (row 13, mockup 09 v2). One mat of vertical jade slips bound by two
  gold cords, fanning open from a bundle as the page opens; the title and the four tabs are jade tags on the upper
  cord. The figure stands at 2.5 on the first slips, washed lighter as if painted there, with the eight worn slots down
  the slips either side (decision 8), a closed slot showing its lock and what opens it, an empty one glowing jade while
  the bag holds a piece for it; who walks beside in round chips. The register is written across the rest: the name,
  the realm with its Level and stage pips, sect, rank and worn title, Combat Power, Relations and age, the origin and
  what it gave, the three pools, and offence and defence in ruled columns with Soul attack, Soul defence and Will
  added. Stats and Titles fold into the Overview, so the tabs are Overview, Aptitude, Attunement and Wardrobe.
- **The titles as honours** (decision 16). Each title is a red lacquer tablet with cut corners and a gold inlay line;
  its motif (blade, shield, pearl, cloud, peak, lotus, coin, cauldron or star, by the stat its gift raises) on a
  gilt boss; its name in pale gold and its gift inscribed in gold on a sunk band. The worn title comes first, in a
  gilded frame with a stud at each corner and the gold ◆ of the style guide's "you" mark. Five to a page and a button
  to the next five; a tap wears one (`set_title`, as before).
- **Art** (`tools/ui/build_ui_hd.py`, byte-identical twice): `jade_tag`, `jade_label`, `honour_tablet` and
  `honour_seal`'s nine motifs; the slips, cords, knots and wash are drawn by the page from tokens.
- **The Bag** was built as the spirit gourd of mockups 07 and 08 v2 and withdrawn before it merged, by decision 15 (no
  gourd drawing; a big space with a small card for the chosen item, new concepts to the user first). The Bag keeps its
  P4 page; the general pieces it used are the foundation above.
- **Tests:** `rules_tests` `ui_suite` (every word on a page with its own surface read on its ground, the close button
  and inked title kept, a signature no other page shares, in every tab), the new `identity_suite` (on a probe page: a
  word too dim for its ground caught, the tabs' targets and the inked title kept, the regions live from the first frame,
  the opening and a tap, Reduce motion's fade; a page with no identity opening at once), `ui_style_suite` (the new
  surfaces and faces measured); every target 48 px or more and every word on the type scale, as before. The full
  suite on this build: room_lint 168 / 0; engine_tests 3785/3785; data_validation 23287 / 0; room_sweep 3568 / 0;
  rules_tests 1830 / 0; contract_tests 1032 / 0; balance_sim 124 / 0; perf_tests 5 / 0; prologue_run 107 / 0;
  valley_run 1257 / 0; check_scripts 0 failures.
- **Screenshots** in `docs/ui_p5/`, on copies of the valley_run checkpoints `ls6_end` and `bf2` taken on this build, with
  the comparison against mockup 09 v2 and why each difference is there; `--tap=x,y` (a debug tool) taps the top page.
- **Roadmap:** U20 Partial and U21 Present (C8), U15 stays Partial with decision 15's withdrawal recorded; the P5 row
  says what has started.

### P5 · The Bag as the heaven in the gourd (concept B, decisions 8, 15 and 24)
- **The page** (`docs/page_identity.md` row 3; mockups 07_bag_b, _card, _pill, 08_bag_b_empty). No gourd is drawn and
  no frame: the page is the world inside the Spirit Gourd, a night sky over a sea of cloud with far islands, and a
  bigger gourd is a wider heaven (more stars and islands, the light from its mouth once it holds 40). The figure stands
  at 2.5 on its own island with the eight worn slots riding a gold orbit round it (`CharacterPage.draw_worn`, which the
  Bag now shares; the figure is drawn by the page, `Avatar.draw_on`, so the card lies over it). What is carried floats
  as one grid ten across, five rows in view and the next fading into the cloud, the next gourd's spaces locked at its
  end with the gourd that opens them; the Spirit Gourd and Key Pouch tokens, the purses (the rarer ones give way when
  room is short), the kinds (All, Gear, Pills, Materials, Other; items.json `bag_kinds`) and Sort; "Space n / m" and
  the next gourd under the grid; while the gourd is small, the hint in the open sky (how things come in, a loose find
  and what a trader pays, the piece that fits an empty slot, what opens the locked ones). The grid rises out of the
  cloud and the worn slots ride in along the orbit as it opens (0.3 s; a fade under Reduce motion).
- **The small card** (decision 15) opens beside a tapped space with a pointer to it: below it on the top row, to its
  right from the first columns and beside the orbit for a worn piece, else to its left, above the line under the grid
  while it fits. The head (icon, name and count, quality, grade, kind, item level); for a piece in the bag what wearing
  it would make of your own totals against the one worn (the three that change most, and Combat Power, each after the
  change with ▲ or ▼ beside it), for a worn one what it gives you; what else is true of it (the rolls, a pill's
  toxicity against yours, what quick-use holds, a furnace's batch, a relic's spirit, a treasure's cost); its action and
  partner (Equip and Set as spare, Use and Quick-use, the Treasure buttons, Unequip and Swap, Ride, Play) and "···" for
  Lock, Discard, Self-detonate and Appraise. A tap on open sky puts it away. Every P4 action and intent is kept.
- **Rules** (pages submit intents only): `StatRules.equip_change` works out the comparison by `rebuild` on scratch
  copies of the character, so the character is never touched and the numbers are the Character page's;
  `InventoryAuthority.bag_kind` and `next_gourd`.
- **Art and tokens.** `build_ui_hd.py` (byte-identical twice): `sky_token` (normal, selected) and `sky_card`; the sky,
  stars, islands, orbit and sea are drawn by the page from tokens. `SURFACE.sky` and `SURFACE.sea` with their
  `TEXT_ON` rows. `Page.rich` can centre its lines.
- **Tests:** `rules_tests` `ui_suite` opens the Bag with its card on a worn jian, a carried one and a pill; the
  `identity_suite`'s Bag part checks the kinds split the bag with nothing lost, the eight worn slots, the card beside
  its space and inside the window with 48 px actions and words that read on it, that `equip_change` leaves the character
  untouched, that its "before" is the character as it stands and that equipping the piece gives what the card said,
  "···", and a pill's Use and Quick-use. The full suite: room_lint 168 / 0; engine_tests 3785/3785; data_validation
  23287 / 0; room_sweep 3568 / 0; rules_tests 1860 / 0; contract_tests 1032 / 0; balance_sim 124 / 0; perf_tests 5 / 0;
  prologue_run 107 / 0; valley_run 1257 / 0.
- **Screenshots** in `docs/ui_p5/bag/`, on copies of this build's valley_run checkpoints `ls6_end` and `bf2`, beside
  each mockup, with why each difference is there. Roadmap U15 Present.

### P5a · The HUD to the approved mockups
- **The right thumb, two rings (mockup 01).** Ring 1 at R 132 round the 132 px attack button holds jump, the page's four
  techniques (64 px, the HD icons at their native 48) and dodge; ring 2 at R 214 holds the fan and, beside it, a toggle
  that is on, the healing slot, the Draught, the treasures, the in-fight context (or Keep Post) and the weapon swap.
  The pinned toggle, the healing slot, the first treasure, the context and the swap have their own places; the rest
  take the next free one, and a heavy load spreads over the arc without two rings touching. A "1/2" tab turns the
  technique page (a swipe on the ring still does). **An empty or locked slot is not drawn** (review G3): no blank
  circles, no empty treasure, no swap without a spare.
- **The fan holds the system toggles (decision 20).** Cultivate, the Presence, the Sphere, Sense and Pet fold into one
  button; a tap opens it on a paper fan with each toggle named (only the ones the character has, packed from the
  first place) and a tap closes it. Closed, a toggle that is on stands pinned beside it (a held Presence with its Soul
  upkeep arc and level; meditation; a raised Sphere), and the fan glows gold at the bottleneck or when a toggle in it
  is new. At rest the fan keeps the player's choice (open, as mockup 02 draws it, until closed); a foe near folds it,
  and in a fight a toggle taken from the open fan folds it again.
- **Rest and fight (mockup 02).** With no foe within 560 px (and no boss in the room) for two seconds, the techniques
  fold into four beads on the attack ring over 0.25 s (a fade with Reduce motion), the healing slot and the treasures
  rest, and the attack button becomes the context with its verb and target under it ("Talk · Peddler Ning"). A foe
  near brings them back. Every existing control, key and reveal is kept.
- **The rest of the HUD to the mockups.** Party chips beside the panel for the animals beside you and the fellow
  disciples, each a 48 px ring with its face (a disciple's from their own sprite layers), an HP arc, a red ring for a
  wound and the name under it; the bag animals and the mount after them. The Hollowing as a meter with its Burden and
  Seizure stops, its value and which way it runs ("46 ▼ lanterns"). The quest tracker on its plate with a 48 px go
  button. A count on Mail and a vermilion ready seal on Menu when the bottleneck is reached or a day's chest is full.
  The purse rests in boss arenas. The boss bar with its name in the display face, "Lv · phase n of m", an ember fill,
  a notch at each phase (gold once passed, the next lit) and what each brings ("60% · Ashborn Pyre Keeper called ✓",
  "30% · Enrage"). The progress edge with a stop and a "Lv n" at each Level; at the bottleneck it glows gold with
  Stored Qi as a bright lane and "◆ Bottleneck reached · breakthrough ready · tap Cultivate". The log above the
  joystick. The top centre as one stack under the chips (or the boss bar): a run's timer, the room's name, an event or
  a tribulation, a fortune card, then toasts 408 wide and 8 apart that stop above the clear zone (the rest wait).
- **World labels never stack (review G4).** Each kind keeps its own offset: a foe's level and name over its head, the
  party's thin HP lines lower (only in a fight; their names are on the chips), an NPC's plate under the feet, a way's
  or a thing's plate over its art. Labels draw above every figure. Each frame `world.gd` hands them to
  `WorldLabels` (`scripts/presentation/world_labels.gd`), which places them in whole rows so none touches another or
  sits under a HUD control (the HUD writes its controls' rects each frame); a plate under the feet with no room below
  goes over the head; a label keeps last frame's row while it is still clear.
- **The clear zone.** No control or panel stands in the lower middle round the player (x 380–900, y 324–656 at 1280 ×
  720, `hud.gd` `CLEAR_ZONE`), in a fight or at rest with the fan closed, left- or right-handed; the log, the
  tracker and the toasts keep out of it, and the open fan at rest keeps off the player at the common camera positions.
- The legacy panel's own Cormorant preload is gone; outlined words are fitted in the face they are drawn in. Debug
  flags for previews: `--toggle=presence|sphere` and `--fan=open|closed`.
- **Tests:** `rules_tests` `hud_suite` rewritten for four states (a fight, the fan open or closed, at rest): every hit
  circle 48 across and its drawn radius + 4, the nearest centre wins, the cluster where the mockups draw it, ring 2's
  places and a heavy load, rest and fight, the fan's open, close, fold and pin, the clear zone (and mirrored), the
  toasts' stop, and G3 on a bound character; a new `labels_suite` checks the layout pass on a crowd, under a control
  and over the head, a second pass holding still, and the real views (foes, a boss, the party's lines, two NPCs on one
  spot). Screenshots from the valley_run checkpoints beside mockups 01 and 02 are in `docs/ui_p5/hud/`.

### P5 · The World map as drawn (mockups 16 and 16_resources, decisions 11, 17 and 25)
- **The framed painting** (`docs/page_identity.md` row 7). The zone's landscape fills the screen inside a lacquered
  frame (timber, a bronze fillet, a gold line, cloud-scroll corners): the valley is the painting of
  `tools/ui/build_valley_map.py`, its nodes where that painting drew each area. The title plate with the map glyph and
  the pennant hang at the upper left, the zone tags from the top rail beside the Heaven Ranking (a zone not yet set foot
  in shows its lock and says why), the close button at the top right. `Page.WINDOW_SCREEN` (0, 0, 1280, 720) is the
  one window that is the screen itself (style guide §2.2); the `ui_suite` allows it.
- **Areas.** Every area a glowing node: jade where you may walk in (you have been there, or a portal open to you leads
  there), gold where you stand, a dark disc with a padlock where the way is shut. Dotted routes along the rooms'
  portals, pale between open areas and dim into a locked one; the way to the chosen area lit gold, dot by dot. Name
  plates carry the level band ("You are here", "Locked · Lv 28–36"), and a known area's field boss with the time till it
  rises; a locked area beside none you know shows its padlock alone. The tracked quest's lantern, the world events' plum
  blossoms (gold under way, violet coming) and the paths above (S43's wind glyph) stand beside their nodes.
- **No text on the map touches (decision 17).** One layout pass places the marks, then the plates (where you stand,
  the chosen area, the open areas, the locked), each at the first place round its node, below, above or beside and
  slid along that side, then a leader step out, clear of every other plate, mark, node and the frame's furniture; a
  plate with no room drops its last lines, and the ones still without room go first on another pass. It never lays one
  thing over another.
- **The card.** Areas: the area's own picture from the painting with what grows there, its kind and band against your
  Level, Act II's attunement, the tracked quest that leads there with Walk there, its world events, its rooms (you, the
  quest's room, seen, unknown) with their hazards, paths above and field bosses, and Track Route with the areas it
  crosses. Resources: Herbs, Ores and Fish, the zone's things of that kind (those in areas not yet reached greyed), the
  chosen one's rank and craft, its rooms and regrowth, the quest or daily that asks for it, a gold ring and its disc on
  every area that holds it, and Track Route to the nearest. Objectives: the tracked quests and the zone's events, the
  chosen one's way lit and Track Route. Track Route and Walk there are the `auto_path` intent; the page writes nothing.
- **What the painting does not place.** A room in a hidden region shows at the nearest placed area by portals; a
  region without a `map` position stands at the mean of its placed neighbours, moved clear of the other nodes. The
  Azure Expanse and the Lantern Star Field have no painting yet: the page draws them from tokens in the same manner
  (far ranges over a sea of cloud; the star river and drifting lanterns), each area an isle under its node.
- **Motion:** the card slides in from the frame's edge (0.2 s), the chosen way lights in 0.3 s; under Reduce motion
  the way shows lit and the page fades; glows at 0.3 with Bright flashes off. Strings through `ui_strings.json`.
- **Tests:** `rules_tests` `map_suite`: the valley's nodes on the painting's map rect with a picture each; every room of
  every zone shows at an area of its zone; the pass on a crowd; on the real data, in every zone, view, kind and chosen
  area, with every area known and with few, at every text size, no plate or mark touches another, a node or the frame's
  furniture, and every word on the painting sits on a plate (180 views); in the valley no plate is left out; Track Route
  and Walk there walk by `auto_path` and close the map; a locked zone's tag says why. The `ui_suite` opens the map's
  three views in every tab. Screenshots beside the mockups in `docs/ui_p5/map/`.

### P5 · The Records family: the Codex, its Old Scrolls and the Calendar (mockups 18, 18_scrolls, 19; decisions 11, 14, 22)
- **The Codex as the field book** (`docs/page_identity.md` row 26). A bound book open on the reading desk: a jade cloth
  cover, the page block's edges, two pages with the gutter's shadow and foxing. The sections are silk ribbons standing
  out of the top edge; the open one hangs longer and carries the page's title, inked. The Collection is a spread for
  each collection page (four beasts a spread, a long page over several): the whole book's cards filled and the next
  stop (the Collector title and its gift), Contents (the fourteen pages, a tap turns to one), the page's name, how many
  beasts and when a card fills, each beast drawn from its sheet on squared paper and taped in (a shadow until met, with
  where it lives once you have been there), its rank, nature, levels, what taming makes of it and its drops, its count
  on an ink bar to the fill, a filled card stamped; the page's seal (every card filled, `collection_pages_done`) with
  its count. The curled corners turn the leaves; the Codex's entries, Achievements, Paths Above and Seasons are written
  on the same spread. A leaf turns over the spread on a turn, a new section and the opening (0.35 s).
- **The Old Scrolls** (decision 11: like nothing else in the game) are a tab of their own: a black stone rubbing on a
  hanging scroll (brocade, silk, rods with jade caps) on the reading room's wall, inked from the top down to the rungs
  the account has reached, the carved names pale, the stone's chips and crack in the ink, the rest bare paper with the
  ink pad where the work stopped; beside each rung the scholar's vermilion gloss of our realms on it (their halves,
  "you", "? ? ?" for one not reached); the chosen rung ringed and its note pinned on a sheet with a vermilion frame
  (levels, steps and years from `realms.json`). A second tap on a rung turns to the other realm on it; the newest rung
  is dabbed in as the tab opens (0.4 s). Each old scroll entry now names its rung and half (`tools/data/story.py`).
- **The Calendar to mockup 19** (row 22, decision 22; the almanac, 19 v2, stays the record). The kit's window: the four
  seasons as a strip from the one now; the week as seven day columns from today with every occurrence of every world
  event on its day as a slip (gold under way, violet coming; a short name each, `tools/data/living_world.py`) and a red
  line at the hour now; the Beast Tide across the week; the chosen event (a slip or the tide) with when, where, what it
  means for you (a repeat run's cap, the Terraces Trial's standing, the tide's week) and **Go there**, the `auto_path`
  intent the World map uses, with how many regions away; the weather with its next change and what each changes. The
  slips drop onto their days as it opens (0.3 s). Everything the old Calendar said is kept.
- **Shared:** Page takes the World map's `_halo`, `_pulse` and `_blossom` (the map and the Calendar draw the same event
  blossom) and `vshade`/`hshade` gradients; dark ink words take no drop shadow (`UiKit.draw_text`); the plaque's title
  is logged like every inked word, so the `ui_suite` finds it. Everything is drawn by the pages from tokens; no new
  HD art or `SURFACE` token.
- **Tests:** the `identity_suite`'s Records part: the field book binds every card once, a page each; the open ribbon
  carries the title; a corner turns the leaf; Contents lists every page and turns to one; the Old Scrolls rub only the
  rungs reached, gloss each, pin the note and turn to the other realm on a second tap, every word reading on the ink,
  the silk or the note, and every great realm names its rung; the Calendar lays every occurrence of the week on its
  day with no two slips touching and the tide across, and Go there walks to the chosen event's room by `auto_path`,
  shut with its reason when no way leads there. The `ui_suite` opens the Codex also with every old scroll rubbed and
  every card filled, and holds a layout signature to its page script (the Codex opens under four ids).
  The three "n of m" counts join `contract_tests`' counts of a total. The full suite after merging the build branch: room_lint 168 / 0;
  engine_tests 3785/3785; data_validation 49083 / 0; room_sweep 3676 / 0; rules_tests 1972 / 0; contract_tests 1051 / 0;
  balance_sim 148 / 0; perf_tests 9 / 0; prologue_run 111 / 0; tutorial_order 340 / 0; valley_run 3253 / 0.
- **Screenshots** in `docs/ui_p5/records/`, on copies of this build's valley_run checkpoints `bf5`, `qu5` and `ls6_end`,
  with each mockup above the build and why each difference is there (18's second seal and the seals' gifts were
  proposals the rules do not hold; the build draws the one seal the game keeps).
### P5 · The Post family: Roll-Call, Works, Welcome Back, Pouches (decisions 11, 14, 21 and 26)
- **Roll-Call as the sect's duty board** (row 14, mockups 13 and 13_first; decision 11, friendlier and more interactive).
  A pale name tablet per character hangs from the peg rail on a red cord, its arched window holding the character's
  live figure (the Avatar at 3 px an art px, clipped to the arch: standing while played or working, seated at rest), the
  craft and its level, the place and a band that says how the post stands (playing now, full and idle for how long,
  full in how long, on vigil, no post). A tap turns the tablet over (0.25 s) to its back: the level and Finesse, what it
  brings in an hour, the first output's Chance or Abundance bar and the Hour Incense. Under each tablet the pouch is a
  woven vessel on the shelf (a basket, a creel or a cage by what the post fills) heaped with the goods to its level and a
  paper tag with the count (red when full), then one big Settle and a Switch. Soonest full first, four at a time with
  page arrows past four. Settle all with its goods and ready seal, the Storehouse as a cabinet of drawers under a tiled
  roof (tap to take 50, Auto-Settle) and the Bench as a work table (what the apprentice made, Collect, points to spend,
  the craft levels to the next point and apprentice) stand at the right. Board, Crafts and Vows hang as tags on the beam;
  the Storehouse's and the Bench's plaques open their full views (every drawer and the Granary Seal; the apprentices and
  the bench points). A new player's board (Keeping Post not yet done) pins a note that teaches the loop in three steps.
  `PostAuthority.roll_call` rows also carry `cap` and `idle_h`.
- **Works as the curio cabinet** (row 23, mockup 14 v4; decisions 21 and 26). The seven works are the compartments of
  an irregular bamboo shelf, and the compartments are the tabs: each object drawn at its native 96 from
  `tools/icons/families/works.py` (the drawings moved there from the study; the icon build renders them at 64 and
  `@96`, and `SpriteCache` reads 96 px renders), its state on a hemp label (points to spend, seals the Storehouse can pay
  for, the highest stele, flags planted, the lit line, favours granted, the mirror), a ready seal where something
  waits, a locked one dark behind a lattice with what opens it. The chosen work's list lies on the tray below; the Seal
  Scripts show five rows at once. The inventory slip at the right writes what the works add for the character, craft by
  craft and at every post, and the Storehouse and silver they are paid with. Every work's actions are kept.
- **Welcome Back as the incense coil and the winnowing tray** (row 12). The coil on its bronze dish is burnt from its
  outer end to the time away out of the cap (the account's `idle_cap_h` and the sect's bonus), the ember at the mark
  (it runs there as the page opens; drawn at its mark under Reduce motion); the goods drop into the round bamboo tray
  one after another (a tap names one); the rest of the summary and the post's Return Ledger is on a hemp slip; To the
  Storehouse and Keep in pouch, or Collect, under the tray.
- **Pouches as the tailor's chalk patterns** (row 44). Seven drawstring pouches chalked on the cutting cloth in two
  staggered rows, each at its tier's size with the next tier dashed round it and its compartments ruled inside, the
  category's thing in it, what it holds, the next fold and its price, and Sew, which runs a stitch round the pattern;
  a bamboo ruler across the corner.
- **Shared** (`scripts/ui/pages/post_kit.gd`): arches, basketry, paper tags, hemp labels, the lattice screen, planks,
  dashed outlines and the ready seal. `TEXT_ON` rows for words on `wood_dark`, `wood`, `bridge`, `hemp` and
  `talisman`. `--welcome-demo` (a debug tool) opens Welcome Back from a real Return Ledger of 7.5 hours at a post.
- **Tests:** `rules_tests` `identity_suite` (the Post family: a tablet per character, the one played first, soonest full
  first, Settle and Switch under each post, the tags' counts, the figures whole-pixel and clipped, a tap turns a tablet;
  the seven compartments as 48 px tabs, each object at its native 96, a closed work saying what opens it, five Seal
  Scripts at once; the coil burnt to the time away out of the cap and every good in the tray; seven patterns, a deeper
  pouch larger; every word read on its ground), `icon_draw_suite` (the Works objects' 96 and 64 renders), and the
  `ui_suite` in every tab. Screenshots beside the mockups in `docs/ui_p5/post/`.

### P4 · The style guide applied (`docs/ui_style_guide.md` §11, §12)
- **Tokens.** `UiKit` gains the roles the palette left to literals: `RED_TEXT`, `SOUL_TEXT`, `WARNING`, `HP`, `BLOOD`,
  `HEART`, `SKY`, `HUD_LABEL`, `PAPER_INK`, `BAR_TROUGH`, `PLATE`, `DIM` and `SURFACE`, the drawn pages' own materials
  (the map scroll, the Go board, the zither, talisman paper, the tribulation sky, the furnace). Every hex and float
  colour literal in the pages, `Page` and the HUD is a token now (64 and 55 of them); red and violet words take the
  text tokens that pass 4.5:1. Sphere's name colour is #9a87e3 (4.81:1, from 4.17); the three grades past it keep the
  colours P7b gave them, and every grade is checked to have one. The HUD's buttons are the HD kit's new `hud_ring` (132, 64, 52 and 48 px; normal, pressed and
  active), and a held button sinks.
- **Contrast, option C (decision 10).** The bright jade primary face stays; primary labels in every state, page titles
  and the dialogue speaker carry a 2 px ink outline (pale gold 15.6:1, a disabled label 6.2:1, where the face alone gave
  2.13 and 2.64). Plates over the world are 0.72 (`PLATE`: secondary words 4.56:1 over a white sky), and the HUD log is
  outlined. The option B previews are gone; `00b_button_faces.png` stays as the record.
- **Type.** Every word is asked for on the scale (14, 16, 18, 20, 22; Cormorant 22, 26, 30, 34) and none under 14;
  buttons and headings step down the scale; paragraphs default to 18; the HUD realm is 16 and its bar labels 14.
- **Numbers, durations, plurals.** Numbers over the world shorten to three figures from 10,000 ("18.2K"); a value of a
  total reads "a / b". Every time left, wait and cooldown is written by one `Tx.span` ("1 h 6 m", "3 h", "2 d 5 h"),
  in the simulation's messages too; six duration strings retire. 75 counted strings gain their singular ("1 heart").
- **Spacing and windows.** Page layout on the 8 px grid: content 32 px in and 80 under the title, 48 px tabs 8 apart,
  a 512 × 224 confirm dialog; the twelve pages with windows of their own take one of the six standard windows, and the
  dialogue strip sits inside the safe area; list rows on the grid; the Bag grid 16 px from its detail panel.
- **The figure on the Character page (decision 8)** is drawn at 3x, crisp, with the worn slots round it (the Bag's own
  drawing); a tap on a slot opens the Bag on it.
- **States.** Settings' toggles are on in the selected art and Off in secondary grey-blue, not the disabled grey. The
  character you play, your row in the Heaven Ranking and the Body rung you climb are marked with a gold ◆ rather than
  the selection glow.
- **Touch.** Every HUD control answers in a circle at least 48 across and its drawn radius + 4 (the Draught, the bag
  animals and the icon row were short); where two overlap the nearest centre wins; the tracker's go button is 48 × 48,
  and the Soul row opens Character.
- **Found in the screenshots, fixed:** the quest tracker's plate hid the status icons (it now starts under them); menu
  tile names touched their frames; a Welcome row's words ran into its value; the vow rows were shorter than their
  buttons.
- **Checks:** `rules_tests` `ui_style_suite` (no off-token colour, every grade coloured, every text colour measured on the
  kit art it sits on, the HUD's text sizes, pressed only under the finger) and `hud_suite` (the HUD's targets); the
  `ui_suite` holds every page to the type scale, the standard windows and the grid; `contract_tests` holds durations to
  the span and every counted plural to its twin. The audit before and after is in the guide's §12; the pages and the HUD
  re-taken from the valley_run checkpoint `ls6_end` are in `docs/ui_after_p4/`.

### P2 · The close-out: rooms walked, objects apart, the mark follows the objective (M16–M18, M20)
- **Every room walked (M16).** A new suite, `room_sweep`, walks every room headless with the real movement solver. It
  checks that every door and interactable can be reached from every way in and that every arrival reaches a way out.
  It walks the route between every pair of them and fails on a body held in place, and it fails on any solid
  footprint that sticks out past its art (an invisible wall). It takes about 18 s.
- **No more walking in under the steps.** In the Herb Terraces, the East Terrace, the Pavilion Rooftops and the Cliff
  Stair the ground ran on under the raised stairs and landings. A walker along the back row ended up inside the
  staircase, and pressing up did nothing there. The ground is now solid under any raised ground surface more than 8
  above it (`under_steps()` in `tools/data/world.py`).
- **No interactable hides another (M18).** A `data_validation` rule fails when one interactable would take the
  context button from another where it stands, or from a door. It found 41: NPCs in six interior doorways and on three
  anvils, chests over ledge herbs, signposts on sealed ways, the Gate Street bunk on the Weapon Hall's door, the
  recruiters on their tent doors, a gravity switch on a herb. All were moved in the builders. Nodes and chests lifted
  onto a tier now keep out of each other's reach.
- **The context button looks at height.** A chest on a ledge could take the button from the herb below it and then
  say "out of reach". The button now skips anything more than 48 above or below, as the interaction already did.
- **The dummy case, played (M17).** As the valley_run character: between Uncle Guo and his dummy the button talks to
  Guo and a blow strikes the dummy only. On the dialogue page a last line with nothing to choose, an accept and a
  hand-in (Stone and Sweat, played on the page) all close the conversation by themselves.
- **The direction mark follows the objective (M20).** It leads to the current objective's place: the room it names,
  the NPC where they stand now and in your own sect, the nearest room with the foe or the herb, the room where a
  dropped item drops. It goes as far as the room that hides a hidden way. Before, 18 main and guided quests had no
  mark and 27 marked one room for every objective. Hand-in marks could point at the Weapon Master's yard before he
  moves there, at Aunt Ping's hut after the Hollow Night, and at the other sect's arena.
- Tests: `room_sweep`; `data_validation` `overlap_suite` and `quest_guidance_suite`, which plays every guided and main
  quest on a probe set at the point where the story offers it (giver, marker, offer, each objective's mark and route,
  the hand-in); `rules_tests` `guidance_suite`; `valley_run` bf5.

### The code review (`docs/review-code.md`)
- **Bugs fixed, each with a `fixes_suite` test that failed before:** the Relations and Calendar authorities now tick.
  Buyback returns the stack as sold and charges only for what fits. Every item instance keeps its own uid across bags
  and splits. A full bag beside loot is announced once, not every tick. Guild orders never take locked pieces and turn
  over with the daily reset. A Wind Step charge is spent only by a dodge that happens. One answer to "the Dao you know
  best" (`ProgressionRules.strongest_dao`) serves the Sphere, Dao Echo, the chess problems and the insight sites. The
  fall cost moved from `world.gd` into Combat.
- **Each authority writes only its own state; pages only submit intents (B19).** Two new intents, `mark_item_seen` and
  `settle_works`, replace the pages' own writes. A `contract_tests` check fails if a page, the HUD or the shell writes
  character or account state.
- **Duplication removed:** one way to mint a uid and find a piece, one dodge cooldown, one defeat path, one in-game day,
  one dotted config lookup, one node yield for gathering and harvest, one duration helper (`UiKit.span`), and the data
  builders' requirement constructors and reach table written once. Dead code removed. `scripts/` and `tools/` are 210
  lines shorter, and `data/` rebuilds byte-identical.
- **Left, with reasons in the review:** whether an ally's blow breaks a monster's wind-up (the pet and companion tests
  say it should; a design call), the three durations whose wording differs, and the two-column page layout (the
  restyle rewrites those pages).

### P2 · The UI bug pass (B1–B25 of `docs/review-v12.md`)
- **Broken, now working:** a Dao at tier 5 or 6 no longer throws a script error every frame, and each Dao row shows
  its own next target (B1). The guqin plays from the key-item pouch (B2). "Trial: <null>" is gone from great
  breakthroughs with no trial (B12), and the HUD, the Cultivation badge and the Ranking show the same Level (B15).
- **Layouts that ran off the window:** the Titles, Secret Arts, Expeditions and Favours lists scroll inside their
  window, the Promotion trial button no longer sits under Missions, the Teleport Stones rows keep 48 px with ten
  stones, and the Paths, Body, Beast Arena and Sect tree cards neither overlap nor stop mid-sentence (B4, B5, B7, B16,
  B17, B18, B22, I7, I9). The `ui_suite` now opens the context pages as well as the menu pages.
- **Words:** every label is fitted at the size it is drawn (B21, I6). Text written in scripts moved into the strings,
  with a `contract_tests` rule (B8). The Roll-Call shows a post for a character keeping one (B20), the three named
  debts show their names (B24), the Sweep button tells the truth on a day with no floor cleared (B25), and the keyboard
  help names every key (B23). Origins have names and a line saying what each one gives (B10).
- **One version, from one place (B9):** `project.godot` holds `application/config/version` ("1.2"); the title screen
  reads it and the Android presets leave `version/name` empty so the APK takes it too. The APK's visible version moves
  from 1.0.4 to 1.2; the version codes stay 104.
- **Selections:** the kit's selected and disabled panels are built from the normal art, so a chosen row looks chosen
  everywhere (B3, I3, I4). The HUD tracker keeps an objective's count whole (B11).
- B6 was fixed in P4a; B19 (pages that change game state) goes to the code review. I2, I5, I8 and I11–I14 go to the
  P4 style guide.

### P7b · The item and archetype plan
- `docs/item_plan.md`: today's gear counted by zone, grade, slot and archetype; a target of 481 pieces through v1.3
  (264 named); 24 archetype sets; drop rates cut to about 6 pieces an hour of hunting with a `balance_sim` drop check;
  a source for each of the 43 unsourced items; the Bedrock Pill (Solid stability); and the sprite gaps by region.
- **Named pieces leave the random pool.** The Serpent-Tongue Jian and the Tidebreak Bastion's brushes and bells carry
  `named` and never come from the banded equipment roll; Expanse foes dropped Act III's Bastion weapons before.
- **The Drowned Abbot's robe** drops on his first defeat only, not on every kill.

### P9 · The boss design, and what it found
- `docs/boss_design.md`: all 13 bosses redesigned (phases, a telegraphed arena mechanic each, enrage timers, reward
  loops, intro and phase cards), the shared marker system, the build order (P9a–P9f) and `boss_suite`.
- **Untouched can be earned.** Its achievement waited on a `boss_defeated` event nothing sent. A dungeon or story boss's
  fall now announces it, clean when no grave wound came first in the room; Untouched asks for a clean dungeon boss.
- `boss_phase`, `enemy_summoned`, `boss_fled` and `boss_defeated` are in the event contract, so `contract_tests`
  checks who sends and hears them (`boss_event_suite` in `rules_tests`).

### P10 · Findings fixed
- **The Account Legacy records again.** It waited on an `account_legacy` unlock that was never defined, so its +2%
  accumulation per recorded great realm was always 0. The unlock now opens for the whole account at Bone Forging 1, and
  a save that reached great realms before this has them recorded once when it opens (`legacy_suite` in `rules_tests`).
- **The old scrolls' names.** Twenty Codex entries set the common xianxia ladder's names beside Jade River's realms
  (Heart Tempering beside Foundation Establishment, Cloud Stride beside Core Formation, and so on); each opens the
  first time the account reaches that great realm (`docs/realm_old_names.md`).

### P3 · Fixes found by the mockups
The open items the mockup agents listed while drawing (`docs/mockups/README.md`), each with a test in `rules_tests`
(`mockup_fixes_suite`) or `data_validation` that failed before.
- **A sect building takes its materials from the Storehouse and storage too.** The Treasury no longer waits while 49
  Copper Ore sit in storage: a build spends from the bag, then the Storehouse, then the storage chest. One spend path
  (`InventoryAuthority.count_owned` and `apply_spend`) serves the sect builds and the Post Vows, each store written by
  its own owner (`PostAuthority.apply_take_storehouse`, `AccountAuthority.apply_take_storage`).
- **Every sect building has a place in the Sect Grounds.** The Herb Terraces (three garden beds before the Treasury),
  the Expanse Outpost (a watchtower beside the pagoda), the Mirror of Echoes (a bronze mirror before the Meditation
  Pavilion) and the Ancestral Shrine (an ancestors' altar by the shrine) appear in `hv_sect_grounds` once raised, like
  the other ten. They pass the room lint, the `room_sweep` and the `overlap_suite`; a `data_validation` rule fails on
  a sect building with no place there.
- **The Treasury's output says what it gives.** Its key `taels_per_level` sized the storage chest; it is now
  `storage_slots_per_level` (20 spaces a level) in the builder, the data and `SectAuthority.treasury_bonus`.
- **`move_speed` is a number.** `stats.json` gave it the percent format while the Character page shows the speed
  itself (242), so a flat bonus would have read "+2000% move speed". Its format is `int`; a test holds that every
  percent stat is a share.
- **Technique sources have names.** Each of the 26 sources (`library_1`, `night_peddler` …) has a string
  `technique_source.<id>` ("Sect library, first floor", "Peddler Shao's night mat"; a quest reads as its name), read
  with `ContentDB.name_of("technique_sources", id)` where a technique's source is shown (an unlearned star's line on
  the proposed Techniques sky). A `data_validation` rule fails on a source without one.
- **A locked feature says everything it waits on.** `Unlocks.locked_text` has one rule: a system's own locked text if
  it has one; else every trigger condition still unmet, in order ("Reach Qi Kindling 1 · Complete "Keeping Post"",
  where it named only the first); and when a quest is all that is left (the one unmet condition, or the system's own
  quest once the trigger holds) that quest and who gives it ("Take "An Idle Art" from Elder Hu", where it said "Not
  yet available"). `RequirementRules.unmet` gives the unmet conditions, and `first_failure_text` is its first.
  `data_validation` holds that every quest the rule may name has a giver.
- **The hub's Works tile reads the same rule.** It showed Keeping Post at `qu5`, where Keeping Post is done; the hub
  asks `Unlocks.locked_text` for its locked tiles, so at `qu5` Works now waits on Elder Hu's An Idle Art.
- **Every weapon family has a stance held without buying anything** (found by the technique planner). The jian's only
  stance was Willow Leaf Parry, also a technique bought at the library, and bare fists, the brush and the bell had
  none. Four basic stances join the eight: Guarding Blade (jian: a parry counters for 120%, attacks 10% slower),
  Tiger Crouch (fists), Steady Wrist (brush) and Deep Tone (bell). Willow Leaf Parry stays the jian's better stance
  (200%) and now holds only for one who has learned its technique (`ProgressionRules.stance_known`, used by
  `set_stance`, the active stance and the Techniques page). `data_validation` holds one basic stance per family.
- **Found, not fixed: the Copperjaw swarm has no creature art.** No sheet fits: `rock_beetle` is the quarry's grey
  stone beetle (an enemy) and `jade_scarab_swarm` a jade insect-netting prop. Nothing maps the swarm to art today (the
  Swarm tab draws none); a new `copperjaw_swarm` sheet in `creature_art.json`, named by an `art` key in the `swarm`
  config of `stats.json` as `pets.json` names an animal's, is a pixel-art task.

### P3 · The first mockups, approved
- Mockups 00–05 (the kit, the HUD in a fight and at rest, the hub, the cultivation ascent, the breakthrough) approved
  by the user, with two notes, both recorded in `docs/roadmap_master_ui.md` §6.
- **The portrait roundel is gone.** The HUD's player panel no longer draws a circle with the character's initial: the
  name and realm sit at the panel's edge, and the HP, Qi and Soul bars take the width it freed (288 px, 14 px tall,
  their numbers inside and grouped by thousands like every page's). The bottleneck, which the roundel's ring showed,
  shows on the Stored Qi bar.
- An icon style study is under way for the user's second note, that every icon in the game should look better.

### P4a · Touch targets
- **Every tap target is at least 48 px on a side.** `Page._register` gives smaller art a margin of hit area round its
  centre (`Page.MIN_TAP`); the art keeps its look. Tabs, which are 40 px tall, now answer a tap anywhere in 48.
- Buttons that were 36–46 px tall are 48: the stance, wardrobe, meridian, path, vow and ledger buttons, the bag's sort,
  the forge mode and guild pickers, the guild exam, the bench points, the core exchange's rest, the Settings toggles and
  the volume steps.
- The stances on the Techniques page's Inner Arts tab are a scrolled list: nine families no longer squeeze nine buttons
  into the panel's height.
- **Numbers that read.** Under 20 px, numbers are drawn in the bold serif's lining figures: in Pixelify Sans a 5 read
  as an S and a 2 as a Z on the HP, Qi and Soul bars. Damage numbers and large counts keep the pixel face.
- The emote wheel lies on an ellipse that fills its dialog: on the old circle the diagonal buttons overlapped their
  neighbours.
- Tests: `rules_tests` `ui_suite` opens every page and tab with every system unlocked and checks that every tap target
  is at least 48 px on a side, that no two buttons share a point, and that text asked for under the minimum size is
  drawn at the minimum.

## V10 · Keeping Post (idle gathering)

The idle gathering milestone (docs/idle_gathering_design.md), after IdleOn's AFK model in Jade River's own names. It
runs between v1.2 Phase B and Phase C.

### P1 · Guidance and gaps (docs/roadmap_master_ui.md)
- **Quest direction.**
  - The tracker names where a tracked quest leads ("➤ Reed Shallows · Lotus Ferry").
  - The minimap's exit toward it pulses gold, with a gold chevron on the frame's edge pointing the way.
  - The world map marks the destination's region with a pulsing gold quest mark and lists the room with a ◆.
  - The main story's quest leads when several are tracked.
- **Head markers, all four.** Gold ! for the main story. Blue ! for a new side quest. The new **jade-ringed gold !**
  marks a new quest from someone you have already helped. Gold ? means ready to hand in. The new **grey bubble of
  three dots** marks a quest of theirs under way. The minimap mirrors the jade ring. The grey bubble does not pull
  the context button to the NPC.
- **Every loot table rolls equipment or says why not.**
  - The five story bosses now drop superior gear like the other bosses.
  - Event foes roll gear like normal foes (3%); jars roll 2%.
  - Spar and trial opponents carry `no_equipment: "spar"`, and the three story vaults `"set_reward"`.
  - A new data-validation rule enforces both.
- **Boss phases.**
  - The Reflection calls up a heart demon at half health and enrages at a quarter.
  - The Hollow Behemoth sheds Hollowed boarlets at 60% and enrages at 30%.
  - Elder Gu cannot be hurt yet, so his phases run on the fight's clock (`after_s`): hired blades at 20 s, a
    cornered rat at 40 s.
  - A validation rule requires phases on every boss.
- Tests: `guidance_suite` walks one NPC through side, again, progress and ready, and checks the route mark and the
  destination's name. The valley run stands beside Uncle Guo's dummy (a blow opens no conversation; beside Guo the
  button talks). A `--guide-demo` debug flag shows every marker in Lotus Ferry.

### V10d3 · The first month
- `balance_sim` plays 30 days of twelve characters: three to each gathering craft on successive rungs, 20 hours a day
  at their posts, and a day's silver from active play. It buys the account web greedily: Post Arts, craft seals,
  steles, the Favour of the Guilds, the Cinnabar line and two plain flags.
- By day 30: craft level about 35, seals at 14 and steles about 18. Craft Diligence is about 62% from arts, the
  Guilds and flags alone. The web multiplies Finesse by about ×1.9.
- The checks hold Craft Diligence between 60% and 80%, the Finesse multiplier between ×1.5 and ×2.5 and still
  growing, and the Cinnabar line at rank 3 or higher. The design doc's §8 records the month.
- Found on the way: GDScript lambdas capture locals by value, so the simulator keeps shared state in a Dictionary.

### V10d2 · Furnace, Flags and the Mirror
- **Calcination Furnace** (Array Master Ren's Fire and Salt, Heart Tempering 6 with the Formation Guild): six salt
  lines on the Works page. A lit line burns floor(rank^1.5) × qty of each input from the Storehouse every cycle (15
  min for the first three salts, 1 h after) and banks floor(rank^1.3) fire; Refine turns the fire into **Essence
  Salts** (Cinnabar, Verdigris, Azurite, Pearl, Amethyst, Star) and ranks the line up at floor(20 × rank^1.8)
  refined. Each line from the second also burns the salt before it and opens when that line reaches rank 3; a
  starved line waits. Lines keep burning while the game is closed (up to 90 days).
- Essence Salts pay for Seal Scripts past level 10 (seals now go to 30) and for the pick, sickle, rod and net tiers
  6–8 (Cinnabar, Verdigris, Azurite).
- **Formation Flags** (Elder Bian's Flags over the Posts, Heart Tempering 8): two flags, each planted for 500 taels
  in a room with posts; a plain flag gives its posts +1% Craft Diligence (+0.1% a level), a deep flag +2% Finesse
  (+0.2% a level); salts raise them to level 20.
- **Mirror of Echoes** (a sect building, Elder Hu's Echoes in Bronze): a slot at level 1, a second at level 5. A
  disciple with the new **Echo Sampling** art (10% + 0.075% a level) inscribes that share of its post's hourly haul,
  +5% a Mirror level; the Mirror keeps adding it to the Storehouse whatever the disciple does next.
- **Auto-Settle** (with the Seal Scripts): a returning disciple's haul goes straight to the Storehouse without the
  Return Ledger. **Favour of the Granary Seal** (a fourth Magistrate's Favour): a chosen post fills the Storehouse
  directly, past its pouch. Both toggles are on the Roll-Call's Storehouse tab.
- Tests: `works_suite` covers the furnace (cycles, starvation, refining, rank-up), seal salts, flags, the Mirror and
  the options; the valley run lights the Cinnabar line, refines it and plants a flag over the Reed Shallows.

### V10d1 · Arts, Seals, Steles and Favours
The account web's multipliers (docs/idle_gathering_design.md §6), on a new **Works of the Post** page (the menu's
Works). Every source uses one of two curves: add (x1·L) or decay (x1·L/(L + x2)).
- **Post Arts** (Elder Hu's An Idle Art, Qi Kindling 6): a character's own, one point for every two craft levels
  across all crafts; forgetting them all costs 1,000 taels.
  - Dreaming Artisan 20·L/(L+40) Craft Diligence; Sleeping Sword 20·L/(L+50) Martial; Water-Clock Breath 8·L/(L+50)
    both; Steady Hand 30·L/(L+60)% Finesse; Deep Sleeves 60·L/(L+60)% pouch capacity; Windfall Knack and Flowing
    Hand feed the Windfall and Flow terms of a post's rates.
  - Hunter's Recall (one point) now gates taking up a snare from afar, at half the catch.
- **Seal Scripts** (Old Scribe Bai's Seals in Red Ink, Qi Unfurling 2): account-wide, paid from the Storehouse,
  ceil(25 × 1.12^L) of the seal's ladder item for the level band. A craft seal gives +3 flat Finesse a level to its
  craft; the Deep Pouch seal pouch capacity; the Unsleeping Hand both Diligences. A character draws on a seal only
  up to its own level in that craft (its highest craft for the others). Levels 1–10 for now; Essence Salts open
  the rest in V10d2.
- **Guardian Steles** (Elder Bian's The Guardian Stones, Qi Unfurling 6): one per craft, +0.3 tool power a level
  for everyone, floor(150 × 1.22^L) taels and ceil(10 × 1.1^L) ore from the Storehouse.
- **Magistrate's Favours** (Magistrate Qian's The County Tribute, Heart Tempering 2): the Watch (+5% Martial
  Diligence), the Guilds (+3% Craft Diligence) and the Red Seal (a 2.2% chance a settle's craft EXP counts twice),
  each earned once with taels and Storehouse tribute.
- Guardian Stele power now adds to the tool's power inside Finesse (it was added to the base once, not twice).
- Tests: `works_suite`; the valley run learns an art, inscribes a seal with its willow moss and raises a stele with
  three hours of a copper post.

### V10c · Snares, Rites and the Bench
- **Beast Snaring** (Agility; Adventurer Kai's Snares Before Swords, a hemp snare kit): 16 beast trails from the Reed
  Shallows to the Drifting Shoals, each with its critter (jade frog, mist hare, reed ferret, cloud marmot, thunder
  hedgehog, frost stoat, sand fox, star gecko).
  - A snare is set for one of the kit's lengths and runs on the clock, whoever is played: 20 min for 1 critter up to
    28 days for 550. Short snares pay more an hour, long ones more a visit.
  - A snare holds nothing if its Finesse is under the beast's Toughness, and (Finesse / Toughness)^0.25 more above
    it. Kits from iron up hold more snares at once, open longer lengths, and bring a radiant pelt now and then.
  - Critters are pet food.
- **Ancestral Rites** (Spirit; Magistrate Qian's The Ancestors' Regard, a wooden rite tablet): rite charge builds by
  itself for everyone with the Rites, 6 / max(5.7 - 0.2 x tablet speed^1.3 - level/40, 0.57) an hour, up to its
  tablet's cap. Held at one of five ancestral altars (the County Hall, both sect libraries, the Hall of Nine, the
  Star Chandlery), it is all spent on the altar's defence; the wave held calls **Spirit Wisps**.
- **Post Vows:** five boons with curses, learned once for the account with Spirit Wisps, two held per disciple. The
  Short Lamp: +25% craft EXP, posts stop after 10 h. The Quiet Hand: +15% Finesse, -30% EXP. The Burdened Back: +8%
  Craft Diligence, pouches hold 60% less. The Iron Fast: +10% Martial Diligence, provisions go twice as fast. The
  Open Palm: +50% Vigil drops, -20% kills.
- **The Apprentice Bench** (Tinkerer Yu's An Apprentice's Hands): apprentices make components while you are away,
  3600 x speed / progress an hour (36 hemp cord at the start), up to the bench's capacity (the material
  compartment x (2 + 0.1 a point)). They are hemp cord, bronze rivets, kiln bricks, lacquer, whetstones and spirit
  glue.
  - More apprentices at 60 and 150 craft levels in all, and a bench point every five for speed, capacity or smithing
    EXP.
  - Tools from tier 4 and pouch folds from the Satchel up now ask for components.
- The Roll-Call gains Bench and Vows tabs; the Crafts tab shows all six crafts, rite charge and snares out; Tailor Xun
  sews all seven pouch categories.
- Tests: `rules_tests` `station_suite`; `valley_run` sets an apprentice, a snare and the rites at Qi Kindling 3.

### V10b · The Vigil
- **Keep vigil** from the Roll-Call in any room with beasts to hunt: the character hunts the room while you play
  someone else, at IdleOn's kills an hour. That is the lesser of the room's spawn cap (spawns / respawn) and the
  fighter's pace (walking, blows needed, hit chance, techniques slotted), times 40% Martial Diligence and the
  **Sweep** tier (a blow of twice a beast's life or more fells extra: tier floor(log2(hit / HP))).
- Blows both ways come from the S12 damage pipeline itself (seeded samples), so a Vigil agrees with the fight you
  would have.
- **Provisions:** the best healing food in the bag is eaten as blows outpace regeneration. Without food the
  character keeps falling, losing 600 s each time, and fights less of the hours.
- Kills roll the room's loot at expected value into the pouch, pay coins, give a quarter of a hunted kill's realm
  progress, and find **Bestiary Leaves**: one in a thousand per species, account-wide. Tiers at 1, 5, 25 and 100
  leaves give a species' bonus (Martial or Craft Diligence, Finesse, pouch capacity or drop rate).
- The Roll-Call shows a Vigil's kills an hour and Sweep tier. The Crafts tab shows Vigil Info in a hunting room:
  what holds it back, blows landed, damage taken and healed, provisions, and time fighting over twelve hours. The
  Return Ledger lists beasts felled, provisions eaten, realm progress, coins, leaves and loot.
- An old idle Hunt task becomes a Vigil; with Keeping Post, hunting while away is only done by Vigil.
- Tests: `rules_tests` `vigil_suite` (the two caps, Sweep, survivability, a four-hour Vigil settled, leaves and their
  bonus, migration).

### V10a · Posts and crafts
- **Keeping post.** Beside an ore vein, a herb patch, a fishing spot or an insect swarm, the Keep Post button (key O)
  leaves the character there and opens the Roll-Call to choose who to play next. Every character with a post works
  while you play someone else, and while the game is put away.
- **Four crafts**, each with its own level (1-200, IdleOn's EXP curve) per character: Vein Delving (Body), Spirit
  Foraging (Insight, spirit wood on the side), River Angling (Body) and Insect Netting (Agility). Hand harvesting
  trains them too.
- **The rules** (`PostRules`, constants in `posts.json`):
  - Finesse = 12 + (base^1.3 + (attribute + 1)^0.6) x (1 + level/200) x (1 + (attribute/100)^0.35) x (1 + base/100),
    with base = 2 x tool power + 4.
  - Against a node's Toughness T: the Chance bar (Finesse / 10T)^0.4, nothing below 2.5% of the mark; past full, the
    Abundance bar floor(r^0.25) units a success.
  - A swing takes 6 x (1 + (10 - tool speed)/5) s. Craft Diligence is 52% of full work.
  - Worked example: a copper pick, Body 10, level 1: Finesse 81, 64% on copper, about 83 ore and 994 EXP an hour.
- **Nodes:** nine ores, nine herbs, seven fish and eight new insects, each with a Toughness, EXP and a level gate.
  Aged herbs stay a thing of the hand.
- **Tools:** four ladders of nine tiers (picks, sickles, rods, nets), 32 of them new, forged by any smith from each
  zone's ores. The best one carried is used.
- **Insect Netting:** 22 swarms across the valley, Mist Peak, the Expanse and the Drifting Shoals, netted by hand or
  kept as posts. Glowfly, reed cicada, jade scarab, silk moth, thunder mantis, frost cricket, ember locust and starwing
  mote. Little Dou's Glowflies teaches it and gives the reed net.
- **Qiankun pouches:** four compartments per category, 10 each unsewn. Tailor Xun on Market Street sews them deeper
  (25 up to 35,000 a compartment). A full category stops filling, EXP does not, and the Return Ledger says when it
  filled.
- **The Storehouse:** the account's bulk store. The Ledger sends a haul there; items come out into the bag in any
  town.
- **The Return Ledger** on entering a character (hours, Diligence, EXP and levels, the haul, full pouches). **The
  Roll-Call** (menu) lists every character's post, rates, pouch and time to full; it can settle one or all, burn
  Hour Incense (1 to 72 hours, or a Wandering 5 to 500) at a post, and switch.
- An old idle Gather task becomes a post. With Keeping Post unlocked, gathering while away is only done at a post.
- Quests: Keeping Post (Fisher Wen), Little Dou's Glowflies, A Pouch for the Road (Tailor Xun).
- Tests:
  - `rules_tests` `post_suite`: the formulas and worked examples; a post taken, settled, filled and emptied; the
    clock moved back; hand EXP; incense; the Roll-Call and settle all; migration; sewing; the save.
  - `balance_sim` checks the calibration targets.
  - `valley_run` plays the lesson with a second disciple, then nets the glowflies.

## 1.2 — The Lantern Star Field (Act III)

Built in phases (docs/act3_design.md): zone tier 3, levels 82-99, ceiling Sphere Lord 3, Starsea Endurance 20 -> 90.

### Phases D and E · art
- **The brush and the bell in hand**: weapon sheets for both families in every pose the avatar has (idle, walk, jump,
  meditate, attack, the three swings, thrusts and punches, the bow and punch combos), baked by
  `tools/art/bake_weapons.py` from the dagger's grips, each in two layers, in front of the body and behind it
  (`data/parts.json`: `weapon/brush`, `weapon/bell`).
- **Icons** (20): cinder ash, the pyre ember, the drone shell, Kharn's glaive shard, the Copperjaw box, eel essence,
  the void carapace, the Leviathan's scale and the Lantern Heart's flame; the four brush and bell weapons; the five
  brush and bell manuals; the `brush` and `bell` glyphs on the attack button.
- `data_validation` is clean again: every item, technique and weapon has its icon and its appearance.

### Phase E · The Nebula Deep and the Lantern Heart (chapter 22)
- **The Nebula Deep** (94-99, Endurance 80-84), past the Drone Hive: Nebula Verge, Eel Currents, Crab Grottoes, and the
  Leviathan's Maw.
- **Monsters:**
  - Nebula Eel (94-99): a space bite that dashes in, and a current coil that drags you close.
  - Void Crab (94-99, shelled: 60% more defence): a blinking claw that closes 320 at once. It can be tamed as a
    star-tier beast.
- **The Nebula Leviathan** (field boss, 99, back every 45 minutes): Presence 5 and a Sphere of Space. It swallows
  the current (a pull from both sides), breathes the void (460 ahead) and crashes down (a stun). Eels answer its
  call at 60%, and it rages at 30%.
- **The Lantern Heart**, a secret realm (97-99, Endurance 90), reached by the stair above Lanternfall's market once
  Lu's notes are found: Wick Gate, Hall of Burning Stars, and the Flame Heart.
  - **The Lantern Heart's flame**, the first lantern's, is a Heavenly Flame like the others: absorbed, it burns
    under every furnace.
- **The Law pills' recipes** (Law Condensing, Law Touching), sold by Stargazer Ming to a Sphere Lord 3, for the step
  past the Field's ceiling. They are made from star lotus and the Deep's drops: eel essence, void carapace and the
  Leviathan's scales.
- **Chapter 22:**
  - Lu's Lantern: the star notes in the Crab Grottoes, the stair, the flame.
  - The Leviathan's Maw (optional).
  - Greyfall: Sphere Lord 3, and a 90-second stand at the Greyfall Breach. When the Tide closes over the Breach,
    Shen Lian is on the far side, and the Frontier waits past the Field.
  - Four codex entries; the flag `act3_complete`.
- Monster stats take a `defence_mult` for shelled foes.
- Tests:
  - `rules_tests` `lantern_heart_suite`: the crab's shell, the Leviathan's Presence, Sphere and phases, the tameable
    crab, the two Law recipes, the flame absorbed, and the Greyfall stand's outcome.
  - `valley_run` `ls6` plays chapter 22: the notes, the flame absorbed, the Leviathan brought down, Sphere Lord 3
    and the Law recipes, the stand held. Act III now plays from the Lantern Run to Greyfall.

### Phase D · Ash and Tide (chapter 21)
- **The brush and the bell**, two new weapon families (docs/act3_design.md, Phase D in detail).
  - The brush (the new Brush Dao): quick Qi strikes. Every technique used with it writes a talisman on each foe it
    strikes, by the technique's element (Fire burns, Water slows, Wood roots, Metal sunders, Earth leaves the foe
    open, Thunder shocks, none seals its Qi); one talisman on a foe at a time.
  - The bell (the Music Dao): its strikes ring out on both sides for soul damage.
  - Five manuals: Splashed Ink and Cursive Storm for the brush; Stilling Peal (a stun ring), Qi Seal Toll and
    Warden's Call (a group heal and defence) for the bell.
  - Four weapons at the Tidebreak Bastion's armoury, the Lantern Star Field's first: the Ink-Warden's Brush and the
    Warden's Hand-bell (Sage grade), the Starwrit Brush and the Tidebreak Bell (Will grade).
- **The Copperjaw Beetle swarm.** A box of beetles from Tinker Mei.
  - Fed ore, the swarm grows 8% an hour while its food lasts, even while you are away, up to 5,000. Unfed, it
    dwindles.
  - Opened in a fight, it chews every foe within 220 for 8 s at 0.12 × ln(1 + population) of your Qi attack a
    second. Wood foes take half.
  - A Queen can rise (1% a fed hour): after that the swarm grows faster and bites harder.
  - The Pets page gains a Swarm tab to feed it and see it.
- **The Hollow Tide battle** (the Tidebreak Bastion's great bell), 150 s.
  - Every foe near the great lantern dims it; standing by it without striking relights it. If it goes out, the Tide
    breaks through.
  - The battle can be fought again once a day.
- **Ground fire**: Ashborn blows leave the ground burning where they land; standing in it burns.
- **Titles**: Star Warden (+10 Starsea Endurance, 8% Hollow Ward) and Tidebreaker (+3% max HP).
- **Rooms** (9):
  - The Ashen Reach, by the Wardens' second skiff: Cinder Fields, Ashborn Palisade, War Camp and Kharn's Pyre.
  - The Tidebreak Front, by the third: the Tidebreak Bastion (safe), Greyfall Breach, Hollow Wake and Drone Hive.
  - The Tide battle's own instance.
- **Monsters:**
  - Ashborn Raider (88-96).
  - Ashborn Pyre-Keeper (elite, rings of fire, Presence 2).
  - Hollow Drone (88-99, a flying pack that spreads the Hollowing).
  - **General Kharn** (92): Presence 4 and a Sphere of Cinders; a leaping cleave and pyre rings that leave fire;
    a Pyre-Keeper at 60%, rage at 30%. At a fifth of his health he kneels, and you decide whether he lives.
- **Chapter 21:**
  - Main quests: Cinder Fields, Kharn's Pyre, The Tide Breaks, Star Warden. Star Warden asks for Sphere Lord 2 and
    the hatched star-wyrm.
  - Side: Brush and Bell. The Copperjaw swarm's quest comes with its unlock.
  - Five NPCs and six codex entries.
- **New quest objectives**: `judge_foe` (a kneeling foe spared or finished) and `hatch_egg`.
- **Fix: Dao caps carry forward.**
  - A zone now keeps at least the cap the zone before it allowed.
  - Before this, Beast Taming fell back to its valley cap of 2 in the Lantern Star Field, and the rare Daos to 0.
- Tests:
  - `rules_tests` `ash_tide_suite`:
    - the brush's talismans (one at a time; Splashed Ink seals) and the bell ringing out both ways;
    - the swarm's growth, shrinking, Queen, bite and cap, then feeding, time away and release (the box stays);
    - ground fire, and Kharn spared counting for his quest;
    - the lantern dimming, relit and going out.
  - `valley_run` `ls5` plays chapter 21, from the Cinder Fields to Star Warden:
    - Kharn spared;
    - the swarm fed and the brush bought;
    - the Tide battle won with the lantern lit;
    - the star-wyrm hatched.

### Phase C · The Citadel, the Sphere and the Orbit Ruins (chapter 20)
- **The Sphere (Sphere Lord 1).** A small world of your own, raised with the Sphere button (H) and drawn from your
  strongest combat Dao.
  - It reaches 160 + 20 a Dao tier (40 more at tier 6) and costs 0.4% of max Qi a second.
  - Its power is (5 + Level) × (1 + 8% a tier, +10% at tier 6).
  - What it does follows its element:
    - Water slows by a fifth, and freezes the surface of water underfoot.
    - Fire burns, hotter on grass. Wood heals you, more on grass.
    - Earth leaves foes open to harm and roots them on stone.
    - Metal cuts. A Sword Dao Sphere with a jian in hand is the Sword Domain, which cuts harder.
    - Wind quickens you. Space pierces defences. Soul lowers the foes' Will. Thunder shocks every other pulse.
  - A technique whose element the room or the Sphere feeds (its own, or the one it generates: Wood feeds Fire)
    strikes 10% harder.
  - Where two Spheres meet, the weaker breaks. A foe's broken Sphere staggers it. Yours tears a meridian and cannot
    be raised again for 30 s.
  - A Sphere Lord's pets carry a small Sphere of their own and strike 10% harder.
- **Dao tier 6, Original Application,** for every weapon and element Dao (the Lantern Star Field allows it).
- **The Space Dao, six tiers** (penetration, speed, evasion, Qi attack, crit damage), opened by the Orbit Hermit.
- **Gravity switches.**
  - A jade switch lightens the air over its part of a room to 45% (a longer, higher jump); press it again to restore
    it.
  - Volumes tied to a switch start off.
  - The Inverted Hall's high gallery (400) is out of reach of any jump (a double jump tops out near 300) until its
    switch is down.
- **The Confucian path** (Will Manifest 2, an upright heart of alignment 20 or more, never beside the Blood path).
  - Righteous Qi strikes Hollow and demonic foes 25% harder.
  - Three glyphs whose strength follows Insight rather than the arm: the Upright Glyph (a Qi strike ahead),
    Benevolent Script (a group heal) and Rite-Seal Script (roots and soul-strikes foes on both sides).
- **Rooms** (8):
  - The Star Warden Citadel, by the Wardens' skiff from the Arrival Quay: the Citadel Gate (with a teleport stone),
    the Wardens' Hall, the Observatory and the Presence Court.
  - The Orbit Ruins, east past the Warden line: the Tumbling Stair (Endurance 50), the Orbit Garden, the Golem Foundry
    and the Inverted Hall (56, no flight).
- **Monsters:**
  - Gravity Golem (88-93): a gravity well that pulls you in, and an orbit slam. It cannot be knocked back.
  - Orbit Moth (88-93): a ranged flyer, tameable as a star-tier pet.
  - Shen Lian, now a Warden aspirant (91), spars with a Sword Domain Sphere of his own.
- **Chapter 20, The Star Wardens:** The Citadel, The Aspirant, The Observatory, Sphere Lord and The Orbit Ruins. Two
  quests come with unlocks: A Sphere of One's Own (the Sphere's lesson) and The Written Word (the Confucian path).
  Six NPCs and five codex entries.
- **Shops:**
  - Lanternwright Han sells the two later glyphs.
  - Stargazer Ming sells another Sphere Comprehension Stone after the Observatory. A failed Sphere Lord breakthrough
    consumes the stone, and without this shop a player could be stuck.
- **Fixes:**
  - Reaching a Presence level now refreshes quest offers. Before, the Observatory's offer waited for a room change.
  - Warden Xiao's harbour talk now waits until The Citadel. Before, it hid the chapter 20 offer.
- Tests:
  - `rules_tests` `sphere_suite`: the radius, power and element rules, feeding, the six Space tiers and tier 6.
    - A switch lightens only its own half of the hall, and the gallery is out of jump reach without it.
    - Raising the Sphere: its Qi cost, a foe slowed inside and not outside, a weaker Sphere broken, yours broken by a
      stronger one and the wait after.
    - The Sword Domain needs a jian.
    - The Confucian gates: locked, alignment, the Blood path.
  - `data_validation`: a switch-tied volume must name a gravity switch in its room.
  - `valley_run` `ls4` plays chapter 20, from the valley stone back to Lanternfall through The Written Word:
    - a 36-bolt Sphere Lord tribulation;
    - a jade switch pressed;
    - three golems broken.

### Phase B · Blackmast, Wyrmnest and the Hollow Tide (chapters 18-19)
- **The Hollow Tide (S28):** the Hollowing is held under half in the valley and the Expanse. In the Lantern Star Field it
  fills.
  - At 50% the burden begins: techniques cost 25% more and Composure drains instead of recovering.
  - At 100% the Tide takes the body for 3 s (no moving, striking or casting). The allies beside you turn on you for
    10 s. The meter falls back to 80%, and surviving it awakens Hollow-Touched.
  - Cleansing: Lantern Incense (-15, the apothecary), the Tide Cleansing Pill (-40; Star Lotus, wyrm ash, jelly silk),
    and resting under a lit lantern (the harbour and the hulks), which draws it out four times as fast.
- **Rooms** (8):
  - Blackmast Haven: Docks (Endurance 30), Gunners' Battery (33, three cannons to spike, gun decks, a hidden door to
    the Smugglers' Cove), the Flagship Deck (36, Admiral Voss).
  - The Wyrmnest Isles, by Old Bo's skiff from the Moored Hulks: Nest Cliffs (40, Tamer Qiu), Eggshell Terraces (44,
    Hollow puddles), Guardian's Crown (48) and the Hatching Cave.
- **Monsters:**
  - Pirate Gunner (85-90): powder bombs and a slow bombard.
  - Nest Guardian (85-93): club tail and crystal stomp, with a small Presence.
  - Hollowed Wyrmling (88-96): grey flame that adds Hollowing.
  - Admiral Voss (90): Presence 4, the first clash. He calls gunners at 60% and rages at 30%.
  - The Starsea pirates now leave the shards of the zone they die in.
- **Star-tier beasts (Will Manifest 2):** the Comet Sparrow can be tamed once Tamer Qiu has shown you how.
- **The Hatchling Wyrm:** the first Primordial line, from the last star-wyrm egg. It warms like any egg but hatches
  only for a Sphere Lord 2, and grows past Sovereign.
- **Sect Master (Will Manifest 3):** the succession quest. Your valley mentor names you Sect Master, a rank above
  Elder: 300 contribution a day and a fifth off in your sect's Mission Hall, plus the Sect Master title.
- **Chapter 18, Blackmast:** The Purser's Ledger, Gunners' Battery, The Admiral. Gu flees into the Hollow Wake with a
  grey hand.
- **Chapter 19, Wyrmnest:** Star-Tier Beasts, A Hollowed Brood, The Last Egg, The Master's Seat. Three new NPCs, six
  codex entries, two titles (Breaker of the Blackmast, Sect Master).
- Metal, Star and Space beast cores (and a parent-element fallback), so every beast of the Field drops a core.
- Icons for the phase's items: star powder, the guardian scale, wyrm ash, the Admiral's seal, the wyrm egg, Lantern
  Incense and the Tide Cleansing Pill.
- Tests:
  - `rules_tests` `hollow_tide_suite`: the valley cap, the burden, the seizure (allies turned, back to 80,
    Hollow-Touched), cleansing and the lantern.
  - `valley_run` `ls2` and `ls3` play chapters 18 and 19, from the docks to the Master's Seat.

### Phase A · Lanternfall and the Presence (chapter 17)
- **The Lantern Run** is charted and open. From the Starsea Launch a vessel crosses the open Starsea (90 s, faster
  in a storm sloop) past Comet Sparrows and Star Jellyfish to **Lanternfall Harbor**, and sails home from its pier.
- **Zone 3, the Lantern Star Field:**
  - Ceiling Sphere Lord 3: the Expanse cannot hold a Will Manifest, the Field can.
  - Laws: Fire, Metal, Space and Star; Qi density 1.5-2.5.
  - Money: loot pays in **Sage Crystals** and savings are kept in **Star Jade**. The harbour exchange trades
    10 Spirit Stones for a crystal and 100 crystals for a Star Jade, less a fifth each way. Shops price in each
    currency's tael value.
  - Ten regions on the map; the ones later phases build show as planned.
- **Starsea Endurance:** four jades (Tide, Comet, Wick, Void), fed with star shards, fifteen levels each at 1.5 a
  level (0 to 90). The Warden's quest opens them.
- **Rooms** (9):
  - Lanternfall Harbor: Arrival Quay (the pier and the Warden), Harbor Market (exchange, teleport stone, shops),
    Star Chandlery (insight), Tidelight Inn (rest).
  - The Drifting Shoals: Jellyfish Shallows (Endurance 20), Moored Hulks (rest, garden beds), Sparrow Reefs (24),
    Driftglass Bank (28, driftglass and Star Lotus, an insight lens).
  - The Lantern Run crossing (instanced).
- **Monsters:** Star Jellyfish (82-87, a confusing sting and spark trails) and Comet Sparrow (82-87, burning dives).
- **Presence (S28, Will Manifest 1)**, a new Field authority:
  - Hold it with the Presence button (key G). It costs 0.25% of max Soul a second and trains by use:
    experience while it presses something, double in a clash, more for a kill made under it. Levels 1-10;
    level 5 is what Sphere Lord asks.
  - Pressure = (5 + Level) x (1 + 6% a Presence level) + the pressure stat. A foe's Will = 5 + its Level, x1.15
    for elites and x1.3 for bosses.
  - A weaker foe in reach loses output and speed by the S12 Pressure rule, min(50%, 25% x (Pressure / Will - 1)).
  - A foe with a Presence of its own meets yours at a visible boundary. Whoever presses harder than the other
    side's Will (or held Presence) presses them by the same rule; the weaker side is pressed, never both. Without
    your Presence, your Will alone stands against theirs.
  - It shows as a pale ring on the ground, a gold or red wall where two meet, and a line on the Cultivation page.
    The requirement `presence_level_at_least` now works.
- **Chapter 17, Lanternfall:** The Lantern Run, Crystal and Jade, Salt of the Stars, Will Manifest, A Presence of
  One's Own. Nine new NPCs (the harbourmaster, Star Warden Xiao Ning, the exchange clerk, a peddler, an apothecary,
  a smith, Chandler Shu, the innkeeper, Old Bo of the hulks), four codex entries, two shops.
- Star Lotus (herb, Master) and driftglass (ore, Master); star shards, jelly silk and comet plumes; lantern jars and
  chests. The Verdant Dew Vial ages herbs to 10,000 years in the Field as in the Expanse.
- New art for the whole act, drawn ahead of the later phases:
  - eleven creature sheets (Star Jellyfish, Comet Sparrow, Nest Guardian, Hollowed Wyrmling, Hatchling Wyrm,
    Gravity Golem, Orbit Moth, Hollow Drone, Nebula Eel, Void Crab, Nebula Leviathan);
  - ten backdrops, one per region (Lanternfall Harbor to the Lantern Heart), four layers each;
  - 32 props (lantern-star cages and posts, driftglass, hulks, cannons, wyrm nests, orbit stones, Ashborn pyres and banners);
  - five music tracks (`lantern_harbor`, `star_field`, `hollow_tide`, `ashen_war`, `lantern_heart`);
  - icons for the zone's items, the Endurance jades, metal, star and space cores, and the Presence button.
- Tests:
  - `rules_tests` `field_suite`: the Pressure rule, foe Will and Pressure, clashes (only the weaker side is
    pressed), levels, the pressed foe, Soul upkeep, a boss's stronger Presence, letting go, the Sphere Lord
    requirement, running out of Soul.
  - `starsea_suite` sails the Lantern Run to Lanternfall.
  - `valley_run` `ls1` plays chapter 17 end to end, from the Starsea Launch to a level-2 Presence.

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
