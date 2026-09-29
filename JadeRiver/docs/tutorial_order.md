# Tutorial order: the Prologue and the start of Act I

Checked from a brand-new character, step by step, by `tests/tutorial_order.gd` (the walk below, taken fists-first:
Uncle Guo before Granny Liu) and `tests/prologue_run.gd` (Granny first). `tests/topdown_tutorial.gd` plays the same
walk, to the same invariants, as a character of the top-down world: every room of it on the height grid, from the
Fisher's Hut through the Fairground, the Entry Trial, the sect's grounds and the Marsh Edge, then on to The Humming
Token, Mei Qing's Errand and Grey at the Edges (steps 14-16), and then the sect stretch again from the fair as a Cloud Sect disciple on the Cloud Sect's grounds
(`docs/redesign_top_down_plan.md`, "As built: Phase 4", both parts). Every quest is taken and handed in on the
real dialogue page. `tests/valley_run.gd` holds every main quest of Acts I–III to the same story guidance (the last
column and "What the walk holds to" below).

The last column is what the quest tracker shows right after the step: the quest under way, or, between quests, the
story's **Next** entry (◇): who gives the next quest and where, or the Level it waits on and where to hunt for it. The
direction mark on the minimap and the tracker's go button lead to it.

| # | Quest | Where (giver) | What it reveals or unlocks | The step it prepares | The tracker after it |
|---|---|---|---|---|---|
| 0 | (new character) | Fisher's Hut | Move and Talk: joystick, context button; the weapon slot, open and empty (bare fists; the Character and Bag pages draw it empty, not locked) | walking, talking, picking up; Morning Tide is already under way and the hut's door is open | (hidden until A Quiet River) |
| 1 | Morning Tide (auto, from waking) | Fisher's Hut (Aunt Ping) | Bag button | Aunt Ping's tea is in hand from the start; a second cup waits on the table; step outside. No door is shut, no menu asked for | A Quiet River: Find Lu at the Ferry Docks |
| 2 | A Quiet River (auto) | Home Lane to the Ferry Docks (Lu) | room banner, minimap, quest tracker | find Lu; he hands out the four lessons, in any order | Next: The Runaway Kite · Talk to Little Dou |
| 3a | Fists First | Village Square (Uncle Guo) | Attack button, damage numbers; Weapons: Guo's old Training Gauntlets (Flawed), worn at once | five on the stump, three on the dummy. The East Gate stays shut | Next: The Runaway Kite · Talk to Little Dou |
| 3b | The Runaway Kite | Village Square (Little Dou) | Jump button | ladder, hall roof, jump to the Ferry Inn roof | Next: Ma's Delivery · Talk to Old Ma (Old Ma's Store) |
| 3c | Ma's Delivery | Old Ma's Store, by its door (Old Ma) | Coins and Shops: the purse, Trade with shopkeepers | sell the Old Net (one step; buying is the player's own choice) | Next: Granny's Remedy · Talk to Granny Liu (her Herb Hut) |
| 3d | Granny's Remedy | Granny Liu's Herb Hut (Granny Liu) | Quick-use slot (drawn at rest while the step asks for it, glowing and named "Quick-use", and while it holds a tea), HP bar, player panel; shrines | "Bag: put Herbal Tea in Quick-use", "Drink a Herbal Tea: tap Quick-use", the shrine | Next: Crab Trouble · Talk to Uncle Guo |
| 3e | Race to the Tower (optional) | Ferry Docks (Shen Lian) | Sprint, the title Fleet-Footed | the watch-tower bell in 25 s | (as before it) |
| 4 | Crab Trouble | Village Square (Uncle Guo), then the Reed Shallows | Loot and Log: system log, foes' HP bars, elite marker; the East Gate opens; starter gear: the first kill drops the first weapon (a Training Short Blade: "Your first weapon" and its beam, the equip prompt offers it). The fourth lesson done, Guo has it at once: no walk back to Lu (A Quiet River (Return) is merged into it) | the first fight: three crab shells, which drop every kill while Guo wants them; Reedtail Rats; Old Snapper, beside the shore's herbs (the attack button attacks; the herb waits on ring 2) | Next: Evening on the River · Talk to Lu |
| 4+ | (Crab Trouble done) | | Equipment page | the Plain Straw Hat, worn, and Ping's Boar Bone Broth (+120 body XP, a few body levels for good); no second pair of the Straw Sandals the start wears | |
| 5 | Evening on the River | Ferry Docks (Lu) | Menu button | dinner with Aunt Ping, Lu at sunset | The Hollow Night |
| 6 | The Hollow Night (auto) | Lotus Ferry at Night | | three villagers to the hut, hold out 60 s | The River Token |
| 7 | The River Token (auto) | Lu's Boat (Lu) | Cultivate button, progress bar, realm badge, Cultivation page, Codex, Breakthrough; **skill ring and Techniques page** | meditate (the bar starts 98% full), look inward, Bone Forging 1 (the breakthrough card shows what it gave, and the jade aura appears); Lu hands over the token and **teaches Flowing Palm** (the technique's own moment), slotted, costing no Qi in the body stages | The Willow Path: ➤ Willow Path West |
| 8 | The Willow Path (auto, once Lu has handed you the token) | Willow Path West; the West Gate opens | World map, Mail, Foundation page; body training (optional, with its own counter), progress from fights, shrines remember you | strike with Flowing Palm, five Wild Boarlets and the herd's elite boarlet (at the player's Level 1, apart at the west meadow); no stump quota | Next: The Recruitment Fair · Talk to Qing Lan (Fairground) |
| 8+ | (early surprises) | Willow Path East on the way in; Willow Path West as The Willow Path is done | a fortune card, the Remnant Soul in a Ring (sure the first time, meter or not, with its moment); a Spirit Fruit tree ripens, announced with its moment | reach for the fruit: its guardian alone, at the room's Level; the fruit is yours once. The first fields' foes sometimes come as elites, and the first monsters can drop a pearl or a manual page (a rare find) | (as before it) |
| 9 | The Recruitment Fair | Stoneford Fairground (Qing Lan, Mo Yun) | Sect page, Town services | both recruiters, choose a sect: the character is recorded as its member (rank, token, method) | Entry Trial: ➤ the trial ground |
| 10 | Entry Trial (auto, the moment a sect is chosen) | the Fairground's trial ground | at Bone Forging 2: Character page, notice board, return charm | the trial bell and the Trial Puppet; no realm to grind for. The Willow Path, the fair and the trial carry the character to Bone Forging 2 | Next: Fish-Gutting Fists · Talk to Shen Lian (Fairground) |
| 11 | Fish-Gutting Fists | Stoneford Fairground (Shen Lian) | the title River Rival | beat Shen Lian in a spar, a lesson: he spars at the player's Level, his fist's wind-up long enough to read, and says what to watch for; he is the one who fights (one Shen Lian on the screen). It fills Bone Forging 2, so Bone Forging 3 follows by itself | Next: The Weapon Hall (the weapon master, Weapon Hall) |
| 11b | A Disciple's Chores (side) | Gate Street or Cliff Stair (the sect steward) | sect hub and dorm | two spots to sweep and a grey stain by the gate: under it the grey goes into the earth, and a cache of two spirit stone shards | (as before it) |
| 12 | The Weapon Hall (Bone Forging 3) | the sect's Weapon Hall (weapon master) | Guard button, Equipment page; weapon Dao (the weapon slot has been open since the start); **the second technique** | at Bone Forging 3 the tracker's Next is The Weapon Hall (the weapon master, Weapon Hall), not a hunt; a training weapon from the rack (the jian, the spear and the staff: each sect's own and the spear, never a second of Guo's gauntlets), five on the dummies, raise the guard; done, the master teaches the first art of the family in hand (the jian's Cloudpiercing Stroke, the spear's Jade Thrust, fists' and gauntlets' Tiger Rush, and so on) | Strange Tracks: ➤ Marsh Edge |
| 13 | Strange Tracks (auto, the mentor's note, the moment the Weapon Hall is done) | the sect's gate, where the steward shows its transfer array, to the Marsh Edge's watch post (decision 42) | Transfer arrays: the gate's and the watch post's keyed to the token | chapter 2 (its floor Bone Forging 2): three grey patches, a Reed Frog on the way; done at the third, where the River Token hums | The Humming Token: ➤ Marsh Edge (here) |
| 14 | The Humming Token (auto, at the third patch) | the Marsh Edge | | five Hollowed Boarlets where the grey patches were; the mentor comes down to the marsh for the hand-in | Next: Mei Qing's Errand · Talk to Mei Qing (Marsh Edge) |
| 15 | Mei Qing's Errand (topdown_tutorial) | the Marsh Edge's watch post (Mei Qing, tending the watchers) | | willow moss from the reed frogs, grey hides from the boarlets, handed in at the post | Grey at the Edges: ➤ the mentor's peak |
| 16 | Grey at the Edges (auto, topdown_tutorial) | the watch post's array to the gate, then the first walk up through the sect's grounds to the mentor | the mentor's peak array keyed to the token | something on the way in each room: a spar offered, two elders overheard, the gardener's tea to carry up (Tea for the Elder, side) | Next: The First Current · Reach Level 7 (Bone Forging 7) |

The sect's rooms are its own: the Jade Sect's trial ground, Gate Street, Weapon Hall and Elder Hu's peak, or the Cloud
Sect's trial ground, Cliff Stair, Weapon Hall and Elder Sung's far peak. A sect role's quest (the chores, the Weapon
Hall) leads each disciple to its own sect's grounds.

**Less walking in the sect stretch** (decision 42, `docs/redesign/feedback/sect_walking.md`):

- **The sect's transfer arrays.** There is one on the gate's plaza, one on the mentor's peak, and one at the Marsh
  Edge's watch post, which both sects keep. They open with the Weapon Hall. The steward shows the gate's; the mentor
  keys his peak's when he first receives you. The tracker's route, its go button and auto-path take one once the token
  knows both ends.
- **The marsh's errands are one visit.** Strange Tracks is done at the third patch, The Humming Token begins there, the
  mentor comes down to the marsh for it, and Mei Qing's Errand is taken and handed in at the watch post.
- **The Outer Trial is handed in** to the training hall's master in the yard.
- **The rule.** No step asks for a plain walk over 35 s with nothing on the way, nor a walk out and straight back
  (`tools/data/sect_walks.py --check`).

**The story is staged** (decision 39, `docs/redesign/story_staging.md`). In the top-down world each step plays as a
scene in its room, 10–40 s long and skippable. People walk, talk to each other, emote and speak in balloons; the camera
moves; and a hand-off gives the player the controls to do what the step teaches, with a prompt over the thing to act on:

| Step | Scene | The hand-off |
|---|---|---|
| 0–1 | `opening_dawn`: Aunt Ping wakes you and gives you the tea (the Bag) | Walk to the door |
| 2 | `river_dawn`: a boat on the river, the villagers' talk, the kite lost to the wind; then `four_errands` | — |
| 3a, 3b, 3e | `guo_fists` (Guo's jab, cross, jab), `kite_route` (the way up), `tower_race` (Shen Lian runs) | Punch the stump; race him to the bell |
| 3d | `granny_jar`: a jar falls and grazes you | Put the tea in Quick-use; drink it |
| 4 | `east_gate` (Guo opens the gate), `crabs_mei` (the crabs have Washer Mei on the flats) | Drive off a crab |
| 6–7 | `hollow_rises` (the storm), `river_token` (Lu), `first_breakthrough` (the palm, and why you leave) | Meditate; talk to Lu |
| 8–9 | `market_thief`, `fair_arrival`, `sect_chosen` (the welcome on the portrait strip) | — |
| 13 | `array_lesson_*` (the steward shows the gate's transfer array), `grey_rises` (the token hums at the third patch) | Step onto the array: tap Travel |
| 14 | `mentor_descends_*` (the mentor comes down to the marsh in a column of light) | Talk to the mentor |
| 16 | on the way up: `yard_spar_jade` / `court_spar_cloud`, `terrace_talk_jade` / `array_court_talk_cloud`, `gardener_favour_*`; at the top `mentor_peak_*` (his peak's array keyed) | Spar at the post, or walk on; talk to the gardener |

The quests, their steps and the doors are unchanged. A scene only asks: the Quest authority keeps its checkpoints and
whether it has been seen. `tests/topdown_tutorial.gd` plays every one of these scenes to its end as the walk reaches
it, and its cuts count on the play clock.

Past the table the story goes on the same way: between main quests the Next entry names the giver and where they
stand, or the Level a chapter waits on ("Reach Level 21 (Qi Unfurling 3)", "➤ Hunt at Bend Shore") and a hunting
ground whose foes suit the character's Level (the fields P12's gap names on the Quests page). A Level is never the
only way named: a second line gives a lesson or side quest on offer ("Or: A Disciple's Chores · the steward"), or,
with none, meditation and body training.

## The first hour, as the walk plays it

`tests/tutorial_order.gd` keeps a play clock (`prologue_run.play_s`): the simulated seconds it steps, walking between
the points it stands at at 150 px/s (a thumb on the joystick; the run speed is 205), 15 s to look round each room the
first time, 3 s to read a line of dialogue and 1.5 s a tap, 2 s an interaction and 0.45 s a blow on a stump. It is a
floor for a focused new player, not a measurement. On it, something new comes at least every 3 minutes to minute 20
and every 5 to minute 60 (invariant 14); the suite prints the timeline, and docs/research/player_motivation.md "As
built" keeps it.

**The chores come after the power** (`docs/research/player_motivation.md` item 6). Nothing daily, idle or kept at a
post opens before Qi Kindling 1, and each is optional when it does. Every such unlock row carries `obligation`, and
`data_validation` checks that each opens at Qi Kindling 1 or later:

| Realm | Lesson (giver) | What it opens | What it asks |
|---|---|---|---|
| Qi Kindling 1 | A Second Path (a letter, guided) | idle tasks (Characters page), offline seclusion | set an idle task, *or* enter seclusion once; never a second character |
| Qi Kindling 1 | Earning Your Keep (the deacon, a side errand) | the sect board, the contribution shop, field-boss timers, the activity chests | any one mission, whenever |
| Qi Kindling 1 | Keeping Post (Fisher Wen, guided) | posts and the Roll-Call | keep post at a node, then burn the incense stick Wen gives at it (or put the game away and come back) |
| Qi Kindling 1 | Little Dou's Glowflies (side) | insect netting | five glowflies |

The Bone Forging lessons that used to hold them keep only their own steps: The First Current (Bone Forging 7) asks for
the Qi spring and no longer for seclusion. **A missed day banks** (`account_rules.bank`): the sect board keeps a day's
unfinished missions and adds each missed day's, up to three days' worth, and an activity chest filled and not opened
waits, while each day away doubles the next activity points up to three days' worth. Nothing resets, expires or breaks.

**A fall costs nothing before Bone Forging 5** (`stats.json` `death.grace_below`): no progress, no injury, no heart
demon, and you wake whole at the shrine. The revival page says so in full the first time and in a line afterwards.

## What the walk holds to

- The weapon slot is open from the start: a new character fights bare-handed with the slot drawn empty (never
  locked), Fists First hands out the training gauntlets worn at once, and the first kill in the Reed Shallows drops
  the first weapon, which the equip prompt offers. The first rooms' foes (the Reed Shallows, Willow Path West and East)
  carry starter gear (`grades.json` `drop.starter`): plain training weapons of the four families a Mortal can hold
  and plain armour at the par item Level, a weapon never above par quality; the character's first three pieces after
  the first weapon come by the 15th kill without one at the latest (counted on the character).
- No room with foes is within reach (or entered) before the HP bar and the foes' HP bars are on the HUD. The Reed
  Shallows, the first, open with Crab Trouble, which follows all four lessons (Granny's Remedy among them).
- Every foe in a fight shows its HP bar over its head (a boss on the HUD's boss bar) from the moment it turns on the
  player, not only once it is hurt; the player's HP bar shows too.
- Every way into a building in the rooms within reach shows a door where it is: the doorway its art draws (a building
  prop's `door` span, a painted hall's doors) or a door set at it (`PortalView.entrance`; `data_validation` holds every
  room to it). A building's door portal stands in its doorway (`Room.building`).
- Taking or handing in a quest closes the conversation, even when the same person has the next quest to give or take
  back (decision 42; talking again offers it), and a scene the quest starts plays once it is closed.
- What a quest's steps ask for (a button, a page) is on the HUD when it is taken; Trade appears with Coins and Shops.
  The control a step names is drawn (the real HUD asked, at rest), not only revealed, while the step is open: the
  Quick-use slot while Granny's Remedy asks for it, and afterwards while it holds a tea.
- No room is left before the steps it holds you to: a quest whose step is to leave its room keeps the room's ways
  shut while it is on offer and until the steps before it are done, the door drawn shut with what to do first on its
  plate, and a try to leave answered with the same words. No door is kept shut for a menu lesson: Morning Tide is under
  way from waking, "Step outside" its only step, the hut's door open.
- In a fight the attack button attacks, whatever is in reach (a herb, a pickup, a person, a door): the offer waits in
  the context slot on ring 2. Decision 42: at rest too; the context has its own button on ring 2 and never takes
  Attack's place. At rest, the fan open or closed, Attack and the techniques are drawn as they are unlocked, and nothing
  before (invariant 15).
- The story's guidance, after every step that moves it: the tracker is never empty; every entry's target (the room
  its step is in, its giver's room, a hunting ground) is a real room the player can walk to, and the direction mark
  leads toward the first story entry's; between main quests the first entry is the Next one (its giver stands where it
  says, or its hunting ground suits the Level); right after the sect choice the membership is recorded and the Entry
  Trial leads the tracker with its target and the mark.
- No chore is open or on offer at any step of the walk: no unlock marked `obligation` (the sect board, activity chests,
  idle tasks, seclusion, posts). No main or guided quest asks for a daily mission or a second character, and no step of
  the main story waits on a daily or idle system (`data_validation`'s chores-after-power suite).
- Every fall in the walk costs nothing (the early grace, before Bone Forging 5).
- The first walk onto the Willow Path after the River Token meets the Remnant Soul in a Ring, and as The Willow Path is
  done a Spirit Fruit ripens on Willow Path West, announced once, its tree in view (the walk keeps a checkpoint there:
  `--keep="First Spirit Fruit"`).
- The tracker and the mark lead where the story really goes next, after every step (`leads_to_next`): a quest of the
  story under way, else one to take now, else a lesson under way or on offer (a guided quest its realm opens), and only
  then the Level the story waits on and a hunting ground for it. At Bone Forging 3, with Strange Tracks waiting on the
  Weapon Hall, that is the Weapon Hall.
- The story is staged in the top-down walk (decision 39). Every scene of the tutorial plays to its end, none skipped,
  and the walk's own deeds satisfy each hand-off. No scene holds the game still once the walk has passed it. Every
  scene's script validates, a hold skips to the next hand-off, and a scene cut short by quitting resumes at its last
  checkpoint (`tests/story_scenes.gd`).
- The first hour pays (research player_motivation P1, P2): the story's own quests and fights carry the character to
  every realm the story waits on, Bone Forging 2 by the Entry Trial and 3 by Fish-Gutting Fists, with no test shortcut;
  the first technique is taught at Bone Forging 1 (Flowing Palm, on Lu's boat) and the second at the Weapon Hall; on
  the play clock something new comes at least every 3 minutes to minute 20 and every 5 to minute 60 (an item kind,
  gear worn, a technique, a realm step, a new foe beaten, a title, the sect, the first coin, a new region, a set piece).
