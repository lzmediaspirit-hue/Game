# Tutorial order: the Prologue and the start of Act I

Checked from a brand-new character, step by step, by `tests/tutorial_order.gd` (the walk below, taken fists-first:
Uncle Guo before Granny Liu) and `tests/prologue_run.gd` (Granny first). Every quest is taken and handed in on the
real dialogue page.

| # | Quest | Where (giver) | What it reveals or unlocks | The step it prepares |
|---|---|---|---|---|
| 0 | (new character) | Fisher's Hut | Move and Talk: joystick, context button | walking, talking, picking up |
| 1 | Morning Tide | Fisher's Hut (Aunt Ping) | Bag button | pick up three teas, open the Bag, step outside |
| 2 | A Quiet River (auto) | Home Lane to the Ferry Docks (Lu) | room banner, minimap, quest tracker | find Lu; he hands out the four lessons |
| 3a | Fists First | Village Square (Uncle Guo) | Attack button, damage numbers | the stump and the dummy. The East Gate stays shut |
| 3b | The Runaway Kite | Village Square (Little Dou) | Jump button | ladder, hall roof, jump to the Ferry Inn roof |
| 3c | Ma's Delivery | Old Ma's Store, by its door (Old Ma) | Coins and Shops: the purse, Trade with shopkeepers | sell the Old Net, buy two rice balls |
| 3d | Granny's Remedy | Granny Liu's Herb Hut (Granny Liu) | Quick-use slot, HP bar, player panel; shrines | the tea in the slot, a drink, the shrine |
| 3e | Race to the Tower (optional) | Ferry Docks (Shen Lian) | Sprint, the title Fleet-Footed | the watch-tower bell in 25 s |
| 4 | A Quiet River (Return) (auto) | Ferry Docks (Lu) | after 3a to 3d, in any order | Lu sends you to Guo |
| 5 | Crab Trouble | Village Square (Uncle Guo), then the Reed Shallows | Loot and Log: system log, foes' HP bars, elite marker; the East Gate opens | the first fight: crabs, Reedtail Rats, Old Snapper |
| 5+ | (Crab Trouble done) | | Equipment page | the Plain Straw Hat |
| 6 | Evening on the River | Ferry Docks (Lu) | Menu button | dinner with Aunt Ping, Lu at sunset |
| 7 | The Hollow Night (auto) | Lotus Ferry at Night | | three villagers to the hut, hold out 60 s |
| 8 | The River Token (auto) | Lu's Boat (Lu) | Cultivate button, progress bar, realm badge, Cultivation page, Codex, Breakthrough | meditate, look inward, Bone Forging 1 |
| 9 | The Willow Path (auto, Bone Forging 1) | Willow Path West; the West Gate opens | World map, Mail, Foundation page; body training, progress from fights, shrines remember you | the stump, five Wild Boarlets |
| 10 | The Recruitment Fair | Stoneford Fairground (Qing Lan, Mo Yun) | Sect page, Town services | both recruiters, choose a sect |
| 11 | Entry Trial (auto, Bone Forging 2) | Fairground, the sect's trial ground | Character page, notice board, return charm | the trial bell, the Trial Puppet |
| 12 | A Disciple's Chores | Gate Street or Cliff Stair (the sect steward) | sect hub and dorm | sweep three spots |
| 13 | The Weapon Hall (Bone Forging 3) | the sect's Weapon Hall (weapon master) | Guard button, Equipment page; weapons, weapon Dao | a training weapon, the dummies, raise the guard |

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
