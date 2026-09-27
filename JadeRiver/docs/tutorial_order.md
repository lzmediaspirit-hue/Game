# Tutorial order: the Prologue and the start of Act I

Checked from a brand-new character, step by step, by `tests/tutorial_order.gd` (the walk below, taken fists-first:
Uncle Guo before Granny Liu) and `tests/prologue_run.gd` (Granny first). Every quest is taken and handed in on the
real dialogue page. `tests/valley_run.gd` holds every main quest of Acts I–III to the same story guidance (the last
column and "What the walk holds to" below).

The last column is what the quest tracker shows right after the step: the quest under way, or, between quests, the
story's **Next** entry (◇): who gives the next quest and where, or the Level it waits on and where to hunt for it. The
direction mark on the minimap and the tracker's go button lead to it.

| # | Quest | Where (giver) | What it reveals or unlocks | The step it prepares | The tracker after it |
|---|---|---|---|---|---|
| 0 | (new character) | Fisher's Hut | Move and Talk: joystick, context button | walking, talking, picking up; the hut's door stays shut ("Before you go: Talk to Aunt Ping") | (hidden until A Quiet River) |
| 1 | Morning Tide | Fisher's Hut (Aunt Ping) | Bag button | pick up three teas, open the Bag, step outside; the door stays shut until the teas and the Bag are done, and says which | A Quiet River: Find Lu at the Ferry Docks |
| 2 | A Quiet River (auto) | Home Lane to the Ferry Docks (Lu) | room banner, minimap, quest tracker | find Lu; he hands out the four lessons | Next: The Runaway Kite · Talk to Little Dou |
| 3a | Fists First | Village Square (Uncle Guo) | Attack button, damage numbers | the stump and the dummy. The East Gate stays shut | Next: The Runaway Kite · Talk to Little Dou |
| 3b | The Runaway Kite | Village Square (Little Dou) | Jump button | ladder, hall roof, jump to the Ferry Inn roof | Next: Ma's Delivery · Talk to Old Ma (Old Ma's Store) |
| 3c | Ma's Delivery | Old Ma's Store, by its door (Old Ma) | Coins and Shops: the purse, Trade with shopkeepers | sell the Old Net, buy two rice balls | Next: Granny's Remedy · Talk to Granny Liu (her Herb Hut) |
| 3d | Granny's Remedy | Granny Liu's Herb Hut (Granny Liu) | Quick-use slot (drawn at rest while the step asks for it, glowing and named "Quick-use", and while it holds a tea), HP bar, player panel; shrines | "Bag: put Herbal Tea in Quick-use", "Drink a Herbal Tea: tap Quick-use", the shrine | A Quiet River (Return): Report to Lu |
| 3e | Race to the Tower (optional) | Ferry Docks (Shen Lian) | Sprint, the title Fleet-Footed | the watch-tower bell in 25 s | (as before it) |
| 4 | A Quiet River (Return) (auto) | Ferry Docks (Lu) | after 3a to 3d, in any order | Lu sends you to Guo | Next: Crab Trouble · Talk to Uncle Guo |
| 5 | Crab Trouble | Village Square (Uncle Guo), then the Reed Shallows | Loot and Log: system log, foes' HP bars, elite marker; the East Gate opens | the first fight: crabs, Reedtail Rats, Old Snapper, beside the shore's herbs (the attack button attacks; the herb waits on ring 2) | Next: Evening on the River · Talk to Lu |
| 5+ | (Crab Trouble done) | | Equipment page | the Plain Straw Hat | |
| 6 | Evening on the River | Ferry Docks (Lu) | Menu button | dinner with Aunt Ping, Lu at sunset | The Hollow Night |
| 7 | The Hollow Night (auto) | Lotus Ferry at Night | | three villagers to the hut, hold out 60 s | The River Token |
| 8 | The River Token (auto) | Lu's Boat (Lu) | Cultivate button, progress bar, realm badge, Cultivation page, Codex, Breakthrough | meditate, look inward, Bone Forging 1, the token from Lu | The Willow Path: ➤ Willow Path West |
| 9 | The Willow Path (auto, once Lu has handed you the token) | Willow Path West; the West Gate opens | World map, Mail, Foundation page; body training, progress from fights, shrines remember you | the stump, five Wild Boarlets | Next: The Recruitment Fair · Talk to Qing Lan (Fairground) |
| 10 | The Recruitment Fair | Stoneford Fairground (Qing Lan, Mo Yun) | Sect page, Town services | both recruiters, choose a sect: the character is recorded as its member (rank, token, method) | Entry Trial: ➤ Hunt at Willow Path West · Reach Bone Forging 2 |
| 11 | Entry Trial (auto, the moment a sect is chosen) | Willow Path to Bone Forging 2, then the Fairground's trial ground | at Bone Forging 2: Character page, notice board, return charm | the hunt to Bone Forging 2, the trial bell, the Trial Puppet | Next: A Disciple's Chores · Talk to the steward (Gate Street) |
| 12 | A Disciple's Chores | Gate Street or Cliff Stair (the sect steward) | sect hub and dorm | sweep three spots | Next: Fish-Gutting Fists · Talk to Shen Lian (Fairground) |
| 13 | The Weapon Hall (Bone Forging 3) | the sect's Weapon Hall (weapon master) | Guard button, Equipment page; weapons, weapon Dao | a training weapon, the dummies, raise the guard | Next: Fish-Gutting Fists, above The Weapon Hall |

Past the table the story goes on the same way: between main quests the Next entry names the giver and where they
stand, or the Level a chapter waits on ("Reach Level 21 (Qi Unfurling 3)", "➤ Hunt at Bend Shore") and a hunting
ground whose foes suit the character's Level (the fields P12's gap names on the Quests page).

## What the walk holds to

- No room with foes is within reach (or entered) before the HP bar and the foes' HP bars are on the HUD. The Reed
  Shallows, the first, open with Crab Trouble, which follows all four lessons (Granny's Remedy among them).
- Every foe in a fight shows its HP bar over its head (a boss on the HUD's boss bar) from the moment it turns on the
  player, not only once it is hurt; the player's HP bar shows too.
- Every way into a building in the rooms within reach shows a door where it is: the doorway its art draws (a building
  prop's `door` span, a painted hall's doors) or a door set at it (`PortalView.entrance`; `data_validation` holds every
  room to it). A building's door portal stands in its doorway (`Room.building`).
- Taking a quest closes the conversation, unless the same person has the next quest to give or take back.
- What a quest's steps ask for (a button, a page) is on the HUD when it is taken; Trade appears with Coins and Shops.
  The control a step names is drawn (the real HUD asked, at rest), not only revealed, while the step is open: the
  Quick-use slot while Granny's Remedy asks for it, and afterwards while it holds a tea.
- No room is left before the steps it holds you to: a quest whose step is to leave its room (Morning Tide's "Step
  outside") keeps the room's ways shut while it is on offer and until the steps before it are done, the door drawn
  shut with what to do first on its plate, and a try to leave answered with the same words.
- In a fight the attack button attacks, whatever is in reach (a herb, a pickup, a person, a door): the offer waits in
  the context slot on ring 2. At rest the context takes the button.
- The story's guidance, after every step that moves it: the tracker is never empty; every entry's target (the room
  its step is in, its giver's room, a hunting ground) is a real room the player can walk to, and the direction mark
  leads toward the first story entry's; between main quests the first entry is the Next one (its giver stands where it
  says, or its hunting ground suits the Level); right after the sect choice the membership is recorded and the Entry
  Trial leads the tracker with its target and the mark.
