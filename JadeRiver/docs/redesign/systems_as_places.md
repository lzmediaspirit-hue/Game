# Systems as places: which systems live on the map, and which stay in the menu

Roadmap decision 36 (`docs/roadmap_master_ui.md` §6) runs the full game logic in the top-down prototype first. It also
asks for a study of which systems should live on the map as places rather than in the player's menu. This is that
study. It is a proposal for the user to decide; nothing here is built.

It extends `docs/redesign_top_down_plan.md` §3 ("Systems that could live in the world") in four ways:

- it covers every page (`docs/page_identity.md` §3, `scripts/main.gd` `PAGES`);
- it checks each system against what the code already does;
- it adds research on how other games split world and menu;
- it ends with a set for the prototype and a phased list.

The Beasts page review waits for this study (decision 36); its row is in §4.8.

---

## 0. In short

1. **The place opens the same page.** This is §3's rule, and the pages stay as the user likes them. A place adds three
   things: a reason to walk there, a sight in the world, and state on screen (ripe beds, a smoking furnace, papers on a
   board, a flag on the letter box).
2. **Most systems should be "both".** They get a place in the world and keep their menu entry, because the game is
   idle-first and played on phones. The menu keeps them reachable in a two-minute session. The place makes them
   visible and gives them a home.
3. **Some systems should be earned remote.** The first uses happen at the place, and a later unlock (a milestone or an
   item) opens them from anywhere. Pokémon's Box Link and IdleOn's Quick Ref do this. The candidates are Storage, the
   Garden's tending and the Crafts queue.
4. **Only a few systems should be place-only**, where being there is the point: shops and their keepers, the auction,
   the Trial Tower's floors, the Beast Arena's pit, teleport stones and fishing spots. Most of them already are.
5. **The self stays in the menu**: Character, Bag, Techniques, Quests, the map, Relations, Settings. So do the events
   (Fates, Revival, Mercy, Welcome Back).
6. **The home should be built from rooms that exist.** Lotus Ferry is the first home. After the sect choice the home
   becomes the Cave Abode (`ja_cave_abode` / `cm_cave_abode`), which already holds garden beds, a bath station, a Qi
   spring and a treasure plot. This answers most of plan §6 item 4 without a new room kind.
7. **For the prototype room** (Riverside Square), build eight places, which between them try every kind of interaction:
   - the notice board with papers;
   - a stall with its keeper;
   - a storage chest;
   - two garden beds;
   - a furnace;
   - a teleport stone;
   - a meditation spot;
   - a letter box with a flag.

---

## 1. Rules for a place

1. **Same page, pre-set.** A place opens the page it belongs to, on the thing it is: the bed opens the Garden on that
   bed, and the furnace opens Crafts on Alchemy. Pages do not change.
2. **Nothing paid while away waits for a walk.** The Welcome Back page claims offline gains wherever the player is. A
   place only shows them: a full basket at a post, a ripe bed, a finished craft's wisp.
3. **No daily chore of walking.** A system used every day (bounties, county jobs, the Roll-Call) keeps its menu entry,
   or its place sits within a few tiles of a teleport stone.
4. **Services cluster at the arrival point.** In every town the teleport stone, notice board, storage chest and
   letter box stand within about six tiles of each other, in one screen. At home everything is within one view
   (40 × 22 tiles).
5. **Remote access is earned, never taken away.** A system that is in the menu today stays in the menu. A system that
   is place-only today may gain remote access through an unlock.
6. **Being there is the point for a few systems**: the auction's room, the tower's floors, the arena's pit, a
   tribulation's stage, the cast of a line. Those stay place-only.
7. **Keep every id.** Object types, room ids and page ids stay, so quests, direction marks, saves and the
   `quest_guidance_suite` still lead to the right places (plan §2.1).

### How interacting looks in the top-down view

Every place uses the same grammar, so a player learns it once:

1. **Approach.** Within the interact reach (40 units on the plane, ±24 in height, plan §1.7), the object's outline
   lights and the Attack button takes its verb, as the context button does today (`world_authority.gd` `_verb`:
   Tend, Refine, Read, Travel, Open…). In a fight the verb moves to the context slot (the rule in `hud.gd`
   `attack_first`).
2. **Tap.** The body turns to the object and plays the catalogue's `interact` pose (4 frames at 8 fps: gather, open,
   tend, pray; plan §1.4) for about 0.3 s. Some places have their own action:
   - a mat or a spring: sit (`meditate`, drawn facing S);
   - water: cast (`fishing cast`, the four cardinal facings);
   - a shrine or an altar: kneel;
   - a stall: the keeper turns to you, with a coin's chime.
3. **The page opens** on its target. Closing it leaves the body where it stood, facing the object.
4. **State shows without a tap:**
   - beds by their growth stage;
   - stations by smoke, sparks or steam while they work;
   - boards by their papers and a gold "!" when one is new;
   - the letter box by a red ribbon;
   - a post by its basket;
   - a spring by the density of its Qi mist.

   Under Reduce motion the state stays and the motion stops (still smoke, a steady glow).

---

## 2. Research: how other games split the world and the menu

The sources were read through search summaries (the fetch tool could not reach the pages). The claims below keep to
what those summaries say.

| Game | What sits in the world | What is a menu | What Jade River takes from it |
|---|---|---|---|
| **Final Fantasy XIV** | Every housing ward has summoning bells (retainers) and market boards, and a bell can be placed inside your house ([Icy Veins][ff1]). A Miniature Aetheryte on your lawn lets you teleport home at 75% off ([FFXIV wiki][ff2]) | Everything else (character, gear, journal) | A home that gathers the services you use most, plus a cheap way back to it |
| **FFXIV's cities** | Limsa Lominsa has the shortest walk from its main aetheryte to the market board and the bell. Players gathered there: "service clustering, not aesthetic appeal, determines where players congregate" ([Bakharev][mmo1]) | — | Cluster the everyday services round the arrival stone (rule 4) |
| **Old School RuneScape** | Bank booths stand in most banks across the world; the Grand Exchange has booths and clerks, and "Collect" on any bank booth reaches your finished trades ([bank booth][rs1], [GE clerk][rs2]). The player-owned house holds a portal nexus of up to 41 teleports, jewellery boxes and restoring pools ([portal nexus][rs3], [house][rs4]). Spirit trees and fairy rings form teleport networks in the world ([spirit tree & fairy ring][rs5]) | Inventory, skills, quests | Remote results (collect trades at any booth) without remote trading; the home as a hub of conveniences that are built over time; travel networks as places |
| **Albion Online** | Every city has its own market with no global one, by design: prices differ and traders haul goods ([Local Economies][ab1], [Marketplace][ab2]). Personal islands hold farms, animals and laborers that give passive income ([laborers][ab3]). Island crafting stations get no return bonus, "to push people out into the cities to do crafting" ([forum][ab4]) | — | Place-only markets create travel and trade, which suits an MMO sandbox, not a phone idle game. The home should hold the idle earners; the town's stations should keep something the home's lack |
| **Black Desert Mobile** | The Camp is a place you can walk round, with workers and twelve buildings ([official guide][bd1]) | It is run from Gather, Build and Workers buttons and a bird's-eye Manage mode ([TheGamer][bd2]) | A phone game can have a place and manage it through a page. This is "both" |
| **Genshin Impact** | Crafting benches stand in the cities (one a few steps from Liyue Harbor's waypoint), and an Alchemist's Crafting Bench can be placed in your Serenitea Pot home ([Crafting Bench][gi1], [Alchemist's Crafting Bench][gi2]) | Alchemy's lists | Stations in towns first, then a home copy as a reward |
| **Stardew Valley** | The shipping bin is a building on the farm; a Mini-Shipping Bin comes later as a reward ([Shipping Bin][sv1], [Mini-Shipping Bin][sv2]). The calendar and the Help Wanted board stand outside Pierre's shop; the board shows a "!" when a new request is up, and a calendar can later be bought for the farmhouse ([Calendar][sv3], [Quests][sv4]). Mini-Obelisks pair up for teleporting ([Mini-Obelisk][sv5]); Junimo Huts harvest the crops round them ([Junimo Hut][sv6]) | Inventory, collections | Boards that show state from afar; the town copy first and the home copy later; helpers placed in the world that do idle work |
| **Animal Crossing: New Horizons** | Resident Services holds the Nook Stop kiosk, the DIY workbench and the recycle box ([Resident Services][ac1], [Nook Stop][ac2]). The airport's card stand replaced the old post office ([Airport][ac3]) | The phone's apps | One building that gathers the services is enough; mail folds into another place |
| **Pokémon Sword and Shield** | The Pokémon Center PC | The Box Link item opens the boxes from almost anywhere, after an early story point ([GameRevolution][pk1]) | **Earned remote**: the place first, then remote access as an item or unlock |
| **Legends of IdleOn** | Town services: storage chest, anvil, alchemy | The Codex's Quick Ref shows Storage, Alchemy, the Anvil and more from anywhere. For some of them it is look-only: to move items you go to the chest ([Quick Ref][io1]) | For an idle game: a remote view for everything, and remote action only where it is earned |
| **Sea of Stars** | 26 merchants in 19 places; a Hidden Market under a dock in Brisk opens with the Trader's Signet ([merchants][ss1], [Hidden Market][ss2]) | — | Discovery: a place worth finding |
| **Design writing** | Diegetic UI lives in the world and keeps immersion ([Game Developer][dx1]); non-diegetic UI can sit wherever it reads best ([Nasty Rodent][dx2]). "A town must serve a function for the player" ([Conner-Harris][dx3]) | | A place must do something, or players pass it by. The page stays where readability matters |

**Patterns** drawn from these, and used in §4:

- **P1 · Cluster.** Everyday services stand together at the arrival point (FFXIV's Limsa, Animal Crossing's Resident
  Services).
- **P2 · Home hub.** The home gathers conveniences built over time (FFXIV's bell and aetheryte, the OSRS house,
  Genshin's placed bench, the Stardew farm).
- **P3 · Earned remote.** The place first, remote access later (Box Link, the Mini-Shipping Bin, the farmhouse
  calendar). IdleOn's look-only Quick Ref is the gentle version.
- **P4 · Remote results.** Collect what finished anywhere, but start the work at the place (OSRS's Collect on any
  booth).
- **P5 · A place run from a page.** Black Desert Mobile's Camp.
- **P6 · Place-only where locality is the design.** Albion's markets, auctions, arenas.
- **P7 · State you can see.** Stardew's "!" on the board; a helper's work shown in the world.
- **P8 · Discovery.** Sea of Stars' hidden market, OSRS's fairy rings.

---

## 3. What Jade River has today

**Objects in the world that open a page or act as a place** (object types across the 168 rooms in `data/rooms/`; the
interactions are in `world_authority.gd` `interact`):

| Object | Rooms | Opens or does |
|---|---|---|
| `shrine` | 35 | The revival point; heals |
| `garden_bed` | 14 in 6 rooms (both Cave Abodes, the herb terraces, the array court, the herders' camp, the moored hulks) | Garden |
| `qi_spring` | 12 | Meditate here; a gardener bottles its water |
| `teleport_stone` | 10 | Teleport (attunes the stone on first touch) |
| `insight_stone` | 9 | Meditate; a stele's lost art; the chess problem |
| `notice_board` | 7 in 6 towns | Notice Board |
| `fishing_spot` | 7 | Gather (fishing) |
| `spar_post` | 6 | A spar |
| `treasure_plot`, `spirit_mine` | 5 each | Tend; the sect's mine |
| `storage_chest` | 5 (Lotus Ferry, Sect Grounds, three markets) | Storage |
| `alchemy_furnace` | 5 | Crafts: Alchemy |
| `forge_anvil` | 4 | Crafts: Forge |
| `bath_station` | 4 (the Cave Abodes and retreats) | Seclusion (a medicinal bath) |
| `formation_table`, `egg_nest` | 2 each | Formations; a king's egg |
| `cooking_pot`, `chart_table`, `shipyard_slip`, `defence_drum`, `beast_trial_stone` | 1 each | Cooking; Charts; Vessels; the sect's defence; the beast trial |
| `inspect` with `open_page` | Your Sect ×18, Seclusion ×4, Library ×4, Exchange ×4, Tower ×2, County ×2, Auction ×2, Guild, Beast Arena | Those pages |

**NPC services** (`data/npcs.json` `services`): 45 shops; Workshop (8 NPCs); Guild (5); Library and Arrays (2 each);
the Auction, Core Exchange, County, Pouches and Talisman (1 each); missions (2 deacons); six sparring partners.

**The menu** (`menu_page.gd` `ENTRIES`): 20 entries in five bays. The HUD's icon row reaches the Menu, Bag, map and Mail;
the Pet button, the portrait, the tracker and the Cultivate button reach their pages.

**Rules already tied to places:**

- **Crafting needs its station** within 180 units (`CraftingAuthority.station_near`, `STATIONS`): a cooking pot; a
  furnace or earth vent; an anvil; a chart table; a slipway. The Crafts menu entry browses; the craft itself happens
  at the station.
- **Seclusion** can begin anywhere. In a room that is not safe, the spot becomes the last shrine; the room sets the cap
  and the Qi density (`ProgressionAuthority.enter_seclusion`). The bath needs a bath station.
- **A major breakthrough** needs a zone whose ceiling allows the next realm (`query_breakthrough` `zone_ok`); a
  tribulation plays where the body stands.
- **Offline, on the clock:**
  - garden growth and the drying racks (`crafting_authority.gd`);
  - the sect's build queue and expeditions (`sect_authority.gd`);
  - the seclusion claim, capped at 12 h by default;
  - the Keeping Post's yields;
  - the spirit animals' swarm hours.

**Homes in all but name.** The two Cave Abodes hold garden beds, a bath station, a Qi spring and a treasure plot.
Lotus Ferry Village holds a cooking pot, a storage chest, a fishing spot, a notice board, a Qi spring and a shrine.
The Sect Grounds hold a storage chest, the defence drum and eighteen objects that open Your Sect.

---

## 4. Every system, one row each

Columns:

- **Verdict**, one of four:
  - **Menu**: stays a menu page only;
  - **Place**: the place is the only way in;
  - **Both**: the place opens the page and the menu keeps it;
  - **Earned remote**: the place first, then remote after an unlock.
- **Where**: home (Lotus Ferry early, the Cave Abode after the sect choice), village, town, sect or field.
- **In the world**: what the player sees and does.
- **Gains / loses**: discovery, presence and social feel against convenience on a phone.
- **Idle**: what runs while away, and what the place shows on return.
- **Pri.** (§5): P0 = the prototype room now; P1 = the first region's conversion; P2 = Phase 6's home and sect;
  P3 = later set pieces or optional; — = stays as it is.

### 4.1 The self

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Character (`character`) | Menu | — | Nothing new: the body already wears its gear in the world | A place would only slow the look at gear | — | — |
| Bag (`inventory`) | Menu | — | Pickups and the equip popup already happen in the world | Same | — | — |

### 4.2 The way

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Cultivation, meditation (`cultivation`, `heart`, `body`) | Menu; places raise the rate | Qi springs (12), insight stones (9), a mat at home | Walk onto a mat or a spring's edge and tap to sit (the S-facing meditate pose). The Qi mist round a place thickens with its `qi_density` | **Gains:** teaches "Qi-rich places" by sight, and gives springs a reason to visit. **Loses:** nothing, since meditation stays anywhere | Online only; offline is Seclusion | P1 (mist); mat P0 |
| Seclusion (`seclusion`) | Both | Bath stations (4), the home's mat, retreats | The bath: step into the tub and sit in the steam. While a character is in seclusion, its body sits at the spot for any other character of the account who walks by | **Gains:** where you left your body is a real spot, and rooms already differ in density and cap. **Loses:** nothing, since the Cultivation page's tab stays | The offline system. Welcome Back claims it anywhere; the spot shows the sitter | P1 |
| Breakthrough (`breakthrough`) | Both, for major steps | Minor steps: anywhere (the Cultivate button, as now). Major steps: a tribulation terrace per zone, an open height with lightning rods | Tap the terrace's altar: the page opens there, and on Break the bolts fall round the terrace. The height levels make a stage other characters can watch | **Gains:** a set piece at the game's big moments. **Loses:** a trip at each major step if it were required. So the terrace is where the Cultivate button's route leads, not a rule (§6 decision 4) | Never offline: breakthroughs never come from idle paths (`progression_authority.gd`) | P3 |
| Techniques (`techniques`) | Menu; a training ground to practise | Sect training grounds, the Fairground (spar posts, dummies, stumps) | Dummies to try the aim forms and decision 35's drag moves on; spar posts start a spar (they exist) | **Gains:** practice has a home. **Loses:** a loadout swap must stay instant, so the page stays in the menu | — | P1 (a dummy in the prototype is cheap) |
| Revival (`revival`) | Menu (an event) | The shrines (35) are already its places | — | — | — | — |
| Fates (`fates`) | Menu (an event) | — | — | — | — | — |

### 4.3 The sect

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Menu (the hub) | Menu | — | It is the index of everything | — | — | — |
| Your Sect (`your_sect`) | Both (already) | Sect Grounds (`hv_sect_grounds`), whose 18 objects open the page | Each building is a prop you walk to, and it grows with the sect's level: scaffolding while the queue builds, the expedition's party at the gate on its return | **Gains:** the courtyard painting becomes literal. **Loses:** nothing, since the Menu keeps it | Build queue and expeditions run offline; the grounds show them done | P2 |
| Sect (`training_sect`) | Both | The Sect Hall: the deacons (missions), the librarian, the sect shop | Walk to the deacon for missions and the shop (they are there now) | **Gains:** the hall is a social place. **Loses:** nothing, since rank and contribution stay in the Menu | — | P2 |
| Characters (`characters`) | Menu; presence | Home and the sect | The account's other characters stand where they are: at their posts, their seclusion spot, the home | **Gains:** a household that feels lived in, the only social feel a solo account has. **Loses:** nothing | Shows idle tasks at a glance | P3 |

### 4.4 Bonds

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Companions (`companions`) | Menu; presence | The home's moon gate; each friend's own town | Companions not walking with you wait at home. Talk to one to take them along (the page's Bring along) | **Gains:** friends with a place to be. **Loses:** nothing, since party changes stay in the Menu for the road | — | P3 |
| Gift (`gift`) | Place (as now) | The person | Through their talk | — | — | — |
| Relations (`relations`) | Menu | — | What the world remembers is not a place | — | — | — |
| Mercy (`mercy`) | Menu (an event) | — | — | — | — | — |

### 4.5 Records

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Quests (`quests`) | Menu | — | Givers' markers and the tracker are already in the world | — | — | — |
| World map (`world_map`) | Menu | — | Signposts and chart tables stay flavour | — | — | — |
| Mail (`mail`) | Menu, plus a flag in the world | A letter box at home and a courier post in each town | A red ribbon on the box when a letter is unread; tap to open Mail | **Gains:** a little presence. **Loses:** nothing, since the HUD icon stays. Mail is a reward inbox, and forcing a trip would only add friction | Auction wins and rewards arrive while away; the ribbon shows on return | P0 (flag) |
| Calendar (`calendar`) | Both | A calendar board beside every notice board, and one at home later | The season's strip and the week's events on the board, readable from afar (Stardew's pattern) | **Gains:** events feel like the town's own. **Loses:** nothing, since the Menu keeps it | Time-based | P1 |
| Notice Board (`notice_board`) | Place (already) | Towns (7 boards), and the Sect Hall | One paper per open bounty or county job, the count visible from afar, and a gold "!" when one is new (Stardew's board) | **Gains:** draws players to towns, and demand is readable. **Loses:** a trip for bounties, so each board stands by a teleport stone (rule 4) | Bounties refresh daily; the papers show it | P0 |
| Codex and Old Scrolls (`codex`, `collection`, `seasons`, `achievements`) | Menu; a reading desk | The sect's scripture pavilion, later the home | The field book lies open on a desk and opens the Codex; the Old Scrolls sit on their own shelf. Steles and insight stones feed it (they already do) | **Gains:** the book as an object (decision 11: it reads as a book). **Loses:** nothing, since look-ups need speed and the Menu keeps it | — | P3 |
| Dialogue | — | — | It is how people and places talk | — | — | — |

### 4.6 The post

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Roll-Call (`posts`) | Menu; markers in the field; a duty board at home or the sect | Each herb patch, ore vein or fishing spot where a character is posted | A post marker (a banner over a basket) fills as the stock grows. The duty board opens the Roll-Call | **Gains:** idle gathering is visible where it happens, and players find posts by walking. **Loses:** nothing, since the page stays the real tool | The Keeping Post runs offline. Markers show it; the settle stays on the page (never a walk to collect) | P1 markers, P2 board |
| Works (`works`) | Menu; objects | Home and the Sect Grounds | Each of the seven works stands as its object (as the curio shelf draws them) | **Gains:** the account's web is visible. **Loses:** nothing | — | P3 |
| Welcome Back (`welcome`) | Menu (the shell) | — | Flavour only: the incense coil burns in the home | — | Its whole job is offline | — |
| Pouches (`pouches`) | Place (as now) | Tailor Xun | Talk to her | — | — | — |

### 4.7 The workshop

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Crafts: cooking, alchemy, forge, talisman, guild, arrays, charts, vessels (`crafts` and its tabs) | Both, as today: browse in the Menu, craft at the station (cooking, alchemy, smithing, charts and vessels need one; talismans, arrays and guild work do not) | A furnace, anvil and pot at home; the sect's alchemy and weapon halls; Stoneford's artisan row; guild halls | The stations work visibly: smoke from the furnace, sparks at the anvil, steam from the pot while a craft runs. A finished one shows a jade wisp. The minigame keeps its page | **Gains:** work you can see, and hubs that feel alive. **Loses:** nothing new, since the station rule exists; the home's stations remove the trip | The drying racks finish on the clock (`crafting_authority.gd`); the wisp shows it | P0 (one furnace) |
| Workshop (`workshop`, `formations`) | Both | A tool wall and bench at home; the 8 NPC masters; the formation tables (2) | Tap the bench: the page opens on its jobs | **Gains:** the page's pegboard becomes a real wall. **Loses:** nothing | Formations burn their fuel and puppets gather by the hour (up to their cap) on the clock (`workshop_authority.gd`); the bench shows a puppet's full basket | P2 |
| Garden (`garden`) | Earned remote | Home beds (the Cave Abode's exist), the herb terraces | Each bed shows its stage (shoots, then the herb, glowing when ripe). Tap a bed: the Garden page on that bed, with the tend pose | **Gains:** idle state at a glance, and top-down suits plots. **Loses:** a trip to tend, until remote tending unlocks after the first harvest (plan §3) | Growth is settled from the clock offline (`crafting_authority.gd`); the beds show it | P0 |

### 4.8 The market

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Shop (`shop`) | Place (as now) | The keepers of the 45 shops | Stalls show their wares on the counter with the keeper behind. Walk up, talk, and the Shop opens | **Gains:** towns read as markets, and stock is visible. **Loses:** nothing (it is place-only today) | — | P0 (one stall) |
| Storage (`storage`) | Earned remote | Chests: Lotus Ferry, the Sect Grounds, three markets, and the home | The chest opens with the open pose | **Gains:** a natural home object. **Loses:** convenience, which players of idle games expect. So remote access comes with an unlock (Box Link's pattern; plan §3 puts it with the Pouches) | — | P0 (chest); remote P2 |
| Exchange (`exchange`) | Place (as now) | The money-changers' windows (4) | — | — | — | — |
| County Hall (`county`) | Place (as now) | Stoneford's county hall | The magistrate's bench | Jobs are daily, so the hall sits by the stone | Daily | P3 |
| Auction (`auction`) | Place (as now) | The Auction Pavilion at the Nine Peaks | A podium, bidders, the lot on its pedestal | **Gains:** a set piece. Won lots come by mail (remote results, OSRS's Collect) | Lots close while away; wins come by mail | P3 |
| Library, Guild | Place (as now) | Sect librarians; guild masters | — | — | — | — |

### 4.9 Beasts

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Spirit Animals (`spirit_animals`) | Both | The Pet button and the Menu keep it; a stable yard at home | The animals not in the party rest in stalls with half-doors, eggs lie in a nest, and the chosen one walks up. Tap a stall: the page on that animal. Party animals already follow in the world | **Gains:** a visible roster; the yard is the page's own stable of stall doors (mockup 10). **Loses:** nothing | Hunger and the swarm's hours show on return (a hungry animal lies down) | P2 |
| Beast Arena (`beast_arena`) | Place (as now) | The Fairground's pit | The ring room opens the ladder page. A challenge could later be fought in the ring | **Gains:** fights in the world, which read well in top-down. **Loses:** nothing | Weekly rank | P3 |
| Core Exchange (`core_exchange`) | Place (as now) | Hermit Yao's Beast Hall | The urn and the tally | — | — | — |

**For the Beasts page review:** the Spirit Animals page does not need to become a place. It stays as built (the
stable's column of stall doors). The home's yard adds presence round it, and the Arena and Core Exchange are already
places.

### 4.10 Stone and bronze

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Teleport (`teleport`) | Place (as now), plus a home stone | The 10 stones, and one at home | Step onto the stone's ring and tap: the compass page. On travel, a column of light | **Gains:** travel is part of the world (OSRS's networks). **Loses:** nothing. A cheap trip to the home stone (FFXIV's 75% off) keeps a phone session short | — | P0 (one stone); home stone P2 |
| Trial Tower (`tower`) | Place (as now) | `sf_trial_tower` | The floors become arena rooms with a gate you walk through; the page keeps the ladder, the sweep and the rewards | **Gains:** combat already happens in the world. **Loses:** nothing | Sweeping cleared floors stays on the page | P3 |
| Mercy (`mercy`) | Menu (an event) | — | — | — | — | — |

### 4.11 Leisure arts

| System (page) | Verdict | Where | In the world | Gains / loses | Idle | Pri. |
|---|---|---|---|---|---|---|
| Fishing (`fishing`) | Place (as now), cast in the world | The fishing spots (7) and home water | Face the water and cast; the float and the bite happen on the water; the minigame and the log stay on the page (plan §3) | **Gains:** top-down water makes casting natural. **Loses:** nothing, but touch timing must stay as forgiving as the page's | A post can fish while away (the Roll-Call) | P2 |
| Chess, Guqin (`chess`, `guqin`) | Place (as now) | Insight stones, pavilions | — | — | — | — |
| Emotes (`emotes`) | Menu | — | — | — | — | — |

### 4.12 The shell

Settings, Title, Selection and Create Disciple stay screens. None of them is a place in the world.

---

## 5. The home, and what the player gains and loses

**Where the home is.** Build it from rooms that exist, not a new room kind:

1. **Lotus Ferry** is the first home. It already has a cooking pot, a storage chest, a fishing spot, a notice board, a
   Qi spring and a shrine, and the Fisher's Hut is where the story starts.
2. **After the sect choice, the Cave Abode.** `ja_cave_abode` and `cm_cave_abode` already hold garden beds, a bath
   station, a Qi spring and a treasure plot. Add a furnace, a chest, a stable yard, a tool bench, a mat, a letter box
   and a home stone.
3. **It grows with realm and sect level**, using the Sect Grounds' growing-room code, as plan §3 proposed for the home
   courtyard.

**Gains:**

- **Discovery.** The Hidden Market pattern and posts found by walking give places a reason to exist.
- **Presence.** Ripe beds, smoking stations, the Roll-Call's baskets and papers on boards show state without a page.
- **Social feel.** In a solo account the household provides it: the other characters at their posts, companions at
  the moon gate, animals in the yard, villagers at stalls. FFXIV's lesson is that clustered services make crowded,
  lively places, so cluster them.

**Loses:**

- **Convenience on a phone.** A trip before every use would hurt the two-minute session.

**How the losses are held off:**

- the Menu keeps every page it has now (rule 5);
- nothing paid while away waits for a walk (rule 2);
- the everyday places cluster round the stones (rule 4);
- remote access is earned for Storage, the Garden's tending and the Crafts queue (P3).

**Costs:**

- **Art:** growth stages per herb, station states, board papers, post markers, a stable yard.
- **Rooms:** the home rooms need lint and sweep; `quest_guidance_suite` must lead to every new place (plan Phase 6).
- **Performance:** props sort only on screen, within plan §5's budget; `perf_tests` per region.

---

## 6. Recommendation

### The set for the prototype room (Riverside Square, now, with decision 36's full logic)

Eight places. Each shows its state and opens its page through the grammar in §1. Between them they try every kind of
interaction: a person, an object with a page, state from idle time, the station rule, travel and sitting.

| # | Place | Page | Tries | Notes |
|---|---|---|---|---|
| 1 | The notice board (the prop exists) with papers | Notice Board | State from quest data; the "!" | One paper per bounty |
| 2 | A stall with its keeper | Shop | A person's talk opening a page | Wares on the counter |
| 3 | A storage chest by the storehouse | Storage | An object's page; the open pose | — |
| 4 | Two garden beds on the terrace | Garden | Idle state on the clock; the tend pose | Stages from `crafting_authority` |
| 5 | A furnace | Crafts (Alchemy) | The station rule; smoke while it works | `station_near` already works |
| 6 | A teleport stone | Teleport | Travel; attuning | — |
| 7 | A meditation mat by a Qi spring | Meditation, Seclusion | Sitting; the mist by density | — |
| 8 | A letter box | Mail | The unread ribbon | The HUD icon stays |

A training dummy for trying the aim forms and the drag moves would be a cheap ninth.

### Phases

1. **Now, the prototype:** the eight places above, in Riverside Square.
2. **Phase 4, region 1 (Prologue and Lotus Ferry):**
   - Lotus Ferry as the first home, its services clustered round the stone: board with a calendar board beside it,
     chest, letter box, cooking pot and fishing spot;
   - post markers wherever a character is posted;
   - Qi mist at the springs.
3. **Phase 6a (the home and the sect):**
   - the Cave Abode as the home: beds, bath, spring, mat, furnace, chest, stable yard, tool bench, letter box and home
     stone;
   - the Sect Grounds' buildings as places;
   - the duty board;
   - earned remote access for Storage, the Garden and the Crafts queue.
4. **Phase 6b (set pieces):**
   - the Trial Tower's floors as rooms and the Beast Arena's pit;
   - fishing cast in the world;
   - tribulation terraces;
   - the auction's crowd;
   - the Codex's reading desk and the works as objects;
   - companions at home and the household's presence.
5. **Never places:** Character, Bag, Techniques' loadout, Quests, the map, Relations, Emotes, Settings, and the events
   (Fates, Revival, Mercy, Welcome Back).

### For the user to decide

1. **The home:** Lotus Ferry, then the Cave Abode (recommended), or a new home-courtyard room kind (plan §6 item 4).
2. **Earned remote:** which systems get it (recommended: Storage, the Garden's tending, the Crafts queue) and what
   unlocks it (a milestone, an item like the Box Link, or the Pouches).
3. **The home stone:** free, cheap (recommended: FFXIV's 75% off), or full price.
4. **Tribulation terraces:** flavour only, where the Cultivate button's route leads (recommended), or a rule for major
   steps.
5. **When fishing moves into the world:** Phase 6b (recommended) or sooner.

---

## Sources

[ff1]: https://www.icy-veins.com/ffxiv/housing-guide
[ff2]: https://ffxiv.consolegameswiki.com/wiki/Miniature_Aetheryte
[mmo1]: https://medium.com/@alexander.bakharev_16063/so-you-want-to-build-an-mmo-8-18-world-design-level-architecture-c07798d17f1c
[rs1]: https://oldschool.runescape.wiki/w/Bank_booth
[rs2]: https://oldschool.runescape.wiki/w/Grand_Exchange_Clerk
[rs3]: https://oldschool.runescape.wiki/w/Portal_nexus
[rs4]: https://oldschool.runescape.wiki/w/Player-owned_house
[rs5]: https://oldschool.runescape.wiki/w/Spirit_tree_%26_fairy_ring
[ab1]: https://wiki.albiononline.com/wiki/Local_Economies
[ab2]: https://wiki.albiononline.com/wiki/Marketplace
[ab3]: https://albiononline.com/news/laborers-in-albion-online-a-guide
[ab4]: https://forum.albiononline.com/index.php/Thread/117050-Personal-Island-Crafting-Stations-Usefulness/
[bd1]: https://www.world.blackdesertm.com/Ocean/News/Detail?boardNo=163
[bd2]: https://www.thegamer.com/black-desert-mobile-camp-guide/
[gi1]: https://genshin-impact.fandom.com/wiki/Crafting_Bench
[gi2]: https://genshin-impact.fandom.com/wiki/Alchemist's_Crafting_Bench
[sv1]: https://stardewvalley.fandom.com/wiki/Shipping_Bin
[sv2]: https://stardewvalleywiki.com/Mini-Shipping_Bin
[sv3]: https://stardewvalleywiki.com/Calendar
[sv4]: https://stardewvalleywiki.com/Quests
[sv5]: https://stardewvalleywiki.com/Mini-Obelisk
[sv6]: https://stardewvalleywiki.com/Junimo_Hut
[ac1]: https://nookipedia.com/wiki/Resident_Services
[ac2]: https://nookipedia.com/wiki/Nook_Stop
[ac3]: https://nookipedia.com/wiki/Airport
[pk1]: https://www.gamerevolution.com/guides/617288-pokemon-sword-and-shield-box-link-how-to-access-pc-boxes-remotely
[io1]: https://idleon.wiki/wiki/Quick_Ref
[ss1]: https://seaofstars.fandom.com/wiki/List_of_Merchants
[ss2]: https://www.gamerevolution.com/guides/945771-sea-of-stars-traders-signet-how-to-open-hidden-market
[dx1]: https://www.gamedeveloper.com/design/diegesis-and-designing-for-immersion
[dx2]: https://nastyrodent.com/diegetic-and-non-diegetic-ui/
[dx3]: https://www.linkedin.com/pulse/5-essentials-designing-towns-video-games-jacob-conner-harris

- Final Fantasy XIV: [housing guide (Icy Veins)][ff1]; [Miniature Aetheryte (FFXIV wiki)][ff2].
- MMO world design: [A. Bakharev, "So You Want to Build an MMO 8/18"][mmo1].
- Old School RuneScape: [bank booth][rs1]; [Grand Exchange clerk][rs2]; [portal nexus][rs3];
  [player-owned house][rs4]; [spirit tree and fairy ring][rs5].
- Albion Online: [local economies][ab1]; [marketplace][ab2]; [laborers guide][ab3];
  [forum on island crafting stations][ab4].
- Black Desert Mobile: [official camp guide][bd1]; [TheGamer camp guide][bd2].
- Genshin Impact: [Crafting Bench][gi1]; [Alchemist's Crafting Bench][gi2].
- Stardew Valley: [Shipping Bin][sv1]; [Mini-Shipping Bin][sv2]; [Calendar][sv3]; [Quests][sv4];
  [Mini-Obelisk][sv5]; [Junimo Hut][sv6].
- Animal Crossing: New Horizons: [Resident Services][ac1]; [Nook Stop][ac2]; [Airport][ac3].
- Pokémon Sword and Shield: [Box Link (GameRevolution)][pk1].
- Legends of IdleOn: [Quick Ref][io1].
- Sea of Stars: [list of merchants][ss1]; [the Hidden Market (GameRevolution)][ss2].
- Design writing: [Diegesis and designing for immersion (Game Developer)][dx1];
  [diegetic and non-diegetic UI (Nasty Rodent)][dx2]; [J. Conner-Harris, "The 5 Essentials for Designing Towns"][dx3].
