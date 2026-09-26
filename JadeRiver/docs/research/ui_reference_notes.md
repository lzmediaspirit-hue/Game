# UI references: HUD, hub, system screens, feedback and bosses

Research for P2 (c) in `docs/roadmap_master_ui.md`: row U7 (each reference's HUD, hub, themed system screens, frames
and feedback), row U8 (a comparison table against Jade River) and the research half of M38 (boss fights). The
retention half of P2 (c), row M21's research, is `docs/research/retention_notes.md`.

Date of research: 2026-09-26. Jade River state: commit bfbb2c5 (v1.2 Phase C).

---

## 0. Sources, method and confidence

**How this was researched.** Web search only. The network sandbox refused page fetches from every game wiki, store,
press site, Wikipedia, Steam, Fandom, GDC Vault and the Internet Archive; github.com was the one reachable host. So every
source below except two was seen through the search engine's extract of the named page, not opened. The two GitHub
issues marked *(read)* were opened and read. No screenshot or video was viewed. Every statement about *where* an
element sits therefore comes from a written description, not from a picture, and the P3 mockups should check the
layouts that matter against real screenshots before copying a proportion.

Where a claim could not be found in any source, it is not described. Each reference ends with a **Not verified**
line naming what is missing, and the comparison table (§12) uses only verified screens.

**Confidence labels** (the house format of `idle_gathering_research.md`, adapted to UI research):

- **[OFFICIAL]**: the publisher's own page: patch notes, an official guide, a store listing, a staff post. High
  confidence on behaviour at the page's date; another region or a later version may differ.
- **[WIKI]**: a community wiki (Fandom, maplestorywiki.net, StrategyWiki, NamuWiki, idleon.wiki, the Melvor wiki,
  Fextralife). Medium to high.
- **[GUIDE]**: a third-party guide, a press review, or a fan translation of patch notes. Medium.
- **[TALK]**: a developer interview or design talk. High on intent, lower on shipped numbers.
- **[PLAYER]**: one player's post (a Steam guide or thread, a forum post, a bug report). Low to medium; the text says so
  where it is used.
- **[INFERRED]**: my reading, synthesis or proposal. Treat it as a design suggestion.
- **[JR]**: Jade River's own files in this worktree, cited by path and line.

Sources are cited as `[R12 · WIKI]`; the full list with page titles and URLs is §14.

---

## 1. The references at a glance

| Reference | Developer | Platform, orientation | Why it is here | Evidence found |
|---|---|---|---|---|
| MapleStory | Nexon | PC, keyboard and mouse | The side-scrolling world, bosses and account systems the Master Prompt names | Deep: official guides, patch notes, three wikis |
| MapleStory M | Nexon | Mobile, landscape | The same world moved to thumbs, with auto-battle and auto-quest | Good: the official wiki's archive, guides, press |
| Soul Saver: Idle RPG | Funigloo | Mobile | Named by the UI prompt; a side-scrolling idle RPG | Thin: the store listing only |
| Legends of IdleOn | LavaFlame2 | PC and mobile | The idle multi-character model Keeping Post already follows | Good: idleon.wiki, guides |
| Idle Skilling | LavaFlame2 | PC and mobile | The same developer's many-skill idle game | Medium: store pages, wiki, one player guide |
| Immortal Taoists | Not confirmed by the sources found | Mobile | A xianxia idle cultivation game: breakthroughs, sects, pills | Medium: wiki, guides, store |
| Melvor Idle | Malcs [R104] | PC and mobile | A single-player idle game with many skills, a sidebar hub and collection logs | Good: the Melvor wiki, two bug reports read |
| Diablo Immortal | Blizzard [R95, R96] | Mobile, landscape | A landscape mobile action RPG with thumb-first controls and raid bosses | Medium: wiki, guides, two developer interviews |

---

## 2. MapleStory (PC)

**HUD**
- HP, MP and EXP are always shown in fixed positions [R1 · OFFICIAL].
- The minimap can be shown full, partly or hidden. The player is a yellow dot, NPCs are green and other players red,
  purple or orange [R1 · OFFICIAL].
- **Quest notifiers sit directly below the minimap**: a lightbulb for permanent content (themed dungeons, job
  advancements, story quests) and a star for limited-time content (events) [R1 · OFFICIAL].
- A "Quick Move" button below the minimap reaches town services such as the Collector, who buys boss crystals, from
  any town [R30 · OFFICIAL].
- Quick slots can be expanded and remapped [R1 · OFFICIAL]. Since the Korean version 1.2.402 they show from 4×2 to
  16×2 slots, can sit left or right, and can be locked against dragging [R2 · GUIDE, fan translation].
- Potions for a keyboard player are handled by the pet: Auto-HP, Auto-MP and Auto-Cure pet skills, a potion assigned
  in the Pet tab of the Equipment window, and a threshold in the options. The pet drinks one potion when HP falls
  below the threshold and does not drink a second if that one fails to lift it. A pet can also cast up to two buff
  skills by itself and pick up nearby items [R5 · OFFICIAL; R6 · PLAYER].

**Hub and menus**
- A Community button (buddy list, party and boss queue, guild, chat) and a Settings button (channel, options, exit)
  [R1 · OFFICIAL].
- Korean 1.2.402 removed the menu buttons beside the status window and added a **Quick Menu** the player fills from
  the Full Menu's Edit Mode, up to 8 buttons (9 from 1.2.403) [R2 · GUIDE].
- Version 244 (SEA) brought every equipment-enhancement function into one window "instead of being scattered across
  different menus", and shows Star Force odds to two decimals [R3 · OFFICIAL].

**Themed system screens**
- **Skills**: one tab per job advancement; a Hyper tab opens at level 141 with Stat, Passive and Active sub-tabs
  [R9 · GUIDE]. The 6th-job HEXA Matrix sits under a "VI" tab and has four node kinds told apart by colour (Skill,
  Mastery, Boost, Common) [R7 · WIKI]; the 5th-job V Matrix sorts its nodes the same way [R8 · WIKI].
- **Inventory**: tabs Equip, Use, Set-up, Etc and Cash; 48 slots per tab at the start, 128 at most, Cash 256
  [R4 · WIKI].
- **Crafting** (Professions, "Production Skill" in the UI): five professions in two chains (Herbalism → Alchemy;
  Mining → Smithing and Accessory Crafting), a fatigue meter of 500 per character that stops all gathering and
  crafting when full, and crafting only in one town (Ardentmill) or a player home [R10, R11 · WIKI].
- **Guild**: guild levels unlock permanent guild skills; a second set ("Noblesse") resets every Thursday and is bought
  with points from two weekly guild activities, a boss (Culvert) and an obstacle race (Flag Race) [R12, R13 · WIKI].
  Each character can earn up to 10 weekly mission points for the guild from hunting and bosses [R14 · OFFICIAL].
- **Account board (Legion)**: every character becomes a piece shaped by its job class, placed and rotated on a grid
  whose squares each give one of 16 stats; the inner grid is open at once and the outer grid grows with rank
  [R15 · WIKI; R16 · OFFICIAL].
- **Monster Collection**: monsters are registered by hunting them, pages are grouped by area, a finished row pays a
  box, and a finished row can be sent on a timed **Exploration** for more rewards; shared by all characters of a
  world [R17 · WIKI].

**Frames and panels**: the v244 refresh is described as "clearer, cleaner, and easier to use" [R3 · OFFICIAL].
Not verified: panel colours, borders, fonts.

**Feedback**
- Default damage numbers: critical hits red, others orange [R18 · WIKI]. Players have asked for an option to swap the
  two [R19 · PLAYER]. "Unit" damage skins add units to numbers over 10,000 so they read faster [R18 · WIKI].
- Level-up plays an animation and a sound. One player on the official forum says the animation lags busy maps and the
  sound is too long [R20 · PLAYER, single post].
- **Runes** appear at a random spot after a random number of kills and give +100% EXP; a rune left unused for five
  minutes lets the map's elite bosses curse it, lowering EXP and drops [R21 · WIKI]. Elite monsters appear with a
  cooldown of about three minutes [R22 · WIKI].
- Not verified: the rare-drop effect, screen shake, the boss-entry presentation (cutscenes exist, but no source
  described their staging).

**Boss fights**
- **Phases as coloured bars**: Hilla's fight has four HP bars in different colours; emptying each upgrades her old
  attacks and adds new ones [R23 · WIKI].
- **Bars that interact**: Will has a main bar and two "dimension" bars; only the dimension bars can be emptied, and a
  periodic screen-crack attack resets all three to the higher of the two [R24 · WIKI].
- **Death count**: each player has a number of lives for the fight, one lost per death; at zero the player is
  expelled [R25 · WIKI]. Examples: 5 for Verus Hilla, 10 for Will [R23, R24 · WIKI].
- **Time limits**: 30 minutes for Hilla [R23 · WIKI]; for the Black Mage 60 minutes (Hard) or 30 (Extreme), with a
  10-second potion cooldown and a curse rule (two different curses within 6 s cost a life and half the HP)
  [R28 · WIKI].
- **Announced wipe attacks and arena changes**: Lucid's second phase moves to a new map of scattered platforms. Her
  dragon's sweeping breath is announced before it comes; the highest platform and the lowest (with the exit portal)
  are safe. Butterflies build up in the background, and when too many gather the platforms vanish for a bullet-hell
  pattern [R26 · WIKI; R27 · GUIDE].
- **Rewards**: weekly boss crystals reset on Thursday [R30 · OFFICIAL]; a player must deal about 5% of a boss's HP to
  see loot [R29 · GUIDE].

---

## 3. MapleStory M

**HUD (thumbs)**
- Right side: an attack ("sword") button and a jump button, with **four skill slots around the sword**. Presets let
  one slot hold more than one skill. Two hotkey sets can be switched mid-fight, and three sets of item hotkeys hold HP,
  MP and buff items [R31 · WIKI; R32 · GUIDE].
- Two "+" boxes on the right hold the HP and MP potions [R35 · PLAYER].
- **Auto-battle**: an [AUTO] icon beside the chat window; opens at level 20 with a 120-minute time bank; a free 2-hour
  charge once a day; tickets add time; some dungeons forbid it [R34 · WIKI]. In auto-battle the skills fire in
  clockwise slot order, so players put buffs first [R35 · PLAYER].
- **Auto-quest**: active quests are listed top-left; tapping one sends the character there on its mount; at a hunting
  target it dismounts and fights, at an NPC it opens the conversation; there is no time limit on it [R36 · WIKI;
  R37 · GUIDE].
- **Top row**: ten shortcut icons, left to right Guide Mission, Event, Task, Dungeons, Shop, Package, Cash Shop, Mail,
  Bag and the Main Menu [R31 · WIKI].

**Hub**
- The Main Menu holds Character Info, Skills (Active, Buff and Passive per job tier, with SP), Pets (up to three
  pets, their skills, and **which potion tier and at what HP/MP percentage the pet drinks it**) and Jewels (equip,
  fuse, change stats) [R33 · WIKI].
- The Dungeons menu lists ten activities: Daily Dungeon, Elite Dungeon, Expedition, Guild Dungeon, Mini Dungeon,
  Monster Mashers, Mu Lung Dojo, Nett's Pyramid, Star Force Field, The Legends Return [R38 · WIKI].

**Themed screens**
- Mu Lung Dojo: a boss on every floor, points and daily rewards, three free runs a day [R41 · WIKI]. Elite Dungeons:
  three stages, the last a boss, from level 15 [R40 · WIKI]. Daily Dungeons: three free entries, reset at midnight
  [R39 · WIKI].

**Bosses**: Zakum (Normal, Hard, Chaos) and Horntail (Normal, Hard) are Expedition bosses for up to 10 players; entry
was at two fixed times a day until a 10 April 2025 patch replaced that with two entries a day [R42 · WIKI].

**Press view**: Pocket Gamer's review says the conveniences make you "rather let the game do everything", which it
counts against engagement [R43 · GUIDE].

**Not verified**: badges on the top-row icons, panel art, feedback effects, boss telegraphs.

---

## 4. Soul Saver: Idle RPG

The evidence is the store listing and its mirrors; no wiki, guide or review of this title was found.

- Developer Funigloo; described as the mobile version of Soul Saver Online [R45 · GUIDE, store mirror].
- "Full auto fight"; heroes grow "whether you play or turn off the game"; "a single hand is enough to play every
  content" [R44 · OFFICIAL].
- Systems named in the listing: a **Seal** system that spends the souls of defeated monsters to strengthen heroes;
  **28 Talismans** that strengthen heroes, weaken enemies or speed play; a guild with **24 guild skills**
  [R44 · OFFICIAL].
- A sibling title, *Soul Saver: Idle Savers* (a blockchain spin-off), is described by its publisher as side-scrolling,
  with basic attacks that build a "Blue soul" gauge and equipped skills that fire in order, and a slot count that grows
  with character level [R46 · OFFICIAL, for the sibling]. This is not evidence for the reference itself.

**Not verified**: the HUD, the hub, every system screen, frames, feedback, bosses and even the orientation. The
comparison table does not rely on this reference beyond the one-hand claim.

---

## 5. Legends of IdleOn

**HUD**
- The **attack bar** sits at the bottom of the screen. It appears when the player taps the red "Assign Attacks" banner
  in the Talents window; active talents are dragged into it [R50 · GUIDE]. With auto-attack on, skills fire as they come
  off cooldown and MP allows [R50 · GUIDE]. Only talents on the attack bar count toward AFK kill speed (in-game hint,
  `idle_gathering_research.md` §1.6) [R66].
- On mobile, a joystick moves and tapping an enemy attacks; landscape is recommended [R51 · GUIDE, an unofficial fan
  site].

**Hub**
- Bottom buttons include Items, Talents, Codex and Map. The Map teleports to any unlocked map, with free teleports per
  day that stack [R49 · GUIDE].
- The **Codex** is "the in-game reference, as well as a record of character and/or account progress": a Quests tab per
  character, a Guild tab, cards and Quick Ref [R48 · WIKI].
- **Quick Ref** does account chores remotely instead of walking: claim boss keys, visit shops, exchange money and
  items, view, add and upgrade stamps, buy bribes, accept tasks, view achievements, the merit shop, trophies and obols,
  and "View Total Percentages". An **EZ Access** panel in its bottom-left corner holds services unlocked by
  achievements [R47 · WIKI].

**Themed screens**
- **Alchemy**: four coloured cauldrons (Power, Quicc, High-IQ, Kazam). The Brewing tab shows the active bubbles at the
  top, the passive vials at the bottom and the cauldrons, which make liquid and brew speed, on the right; four tabs in
  all [R52 · WIKI; R53 · GUIDE].
- **Stamps**: three categories (combat, skills, misc), account-wide, levelled with coins and items [R54 · WIKI].
- **Cards**: copies of a card raise it to five stars, each with "a shiny new border"; a character equips one card set,
  whose tier rises with the star-weighted count [R55 · WIKI].
- **Guild**: up to 210 members; daily and weekly tasks earn guild points; each member marks a "Wanted Bonus" so the
  leader sees what the guild wants upgraded [R56 · WIKI].
- **Tasks**: a board per world, unlocked through an NPC, paying merit points and trophies [R57 · WIKI].
- **Return screen**: the per-character "AFK Gains" popup and the AFK Info page (`idle_gathering_research.md` §8)
  [R66].

**Feedback**
- A rare drop is a roll on a rare table followed by a roll per item on it, so a rare roll can still yield nothing
  [R58 · WIKI]. Not verified: how a rare drop looks or sounds.
- Multikill tiers show as a purple bar in AFK Info (`idle_gathering_research.md` §4.1) [R66].

**Bosses**
- **Amarok** (World 1): drops three fireballs near the player; lifting his sword telegraphs a wide sweep in front of
  him; standing at his feet avoids most attacks. Keys come from an NPC, Colosseum chests and the Post Office
  [R59 · WIKI; R60 · GUIDE].
- **Efaunt** (World 2): several arms with different attacks; guides give a kill order for them; drops the item that
  opens World 3 [R61 · WIKI].
- **Chizoar** (World 3): five attacks and a shield phase. Ice crystals it spawns on a side platform raise its defence
  until each hit does 10 damage, so the player must go and break them [R62 · WIKI; R63 · GUIDE].
- **The Emperor** (World 6): fought once a day by default, in three forms; toxic balls, fireballs, summoned guards,
  spinning swords and rolling boulders; **every hit he lands heals him**; he grows harder and gives a bonus after each
  win [R64 · WIKI; R65 · GUIDE].

**Not verified**: panel style, level-up presentation.

---

## 6. Idle Skilling

- By LavaFlame2 (IdleOn's developer), on Steam since 15 September 2022 and on mobile [R67, R68 · OFFICIAL]. Its store
  text says it is "meant to be played for 5–10 minutes a day" [R67, R68 · OFFICIAL].
- Content named by the developer's listing: pet breeding (60 pets), a laboratory with 135 bonuses, cards,
  construction, crusade and asylum boss fights, and two prestige layers [R69 · OFFICIAL].
- **Crusades**: four monsters and a boss per encounter; after a win the player either exits, which raises the
  difficulty, or replays at the same difficulty for more loot [R71 · WIKI].
- **Rebirth**: a screen opened after an area called The Mist; a separate currency (BP) buys permanent perks and resets
  most progress [R70 · WIKI].
- **Offline**: a Steam guide by a player says the screen you leave on keeps 100% of its rate while the others earn
  about 30–35% (though the game says 50%), and gains are computed when you visit each screen [R72 · PLAYER].

**Not verified**: the HUD and hub layout, frames and feedback.

---

## 7. Immortal Taoists (xianxia idle)

- A xianxia idle game: Qi and cultivation base accrue offline [R73 · OFFICIAL; R74 · GUIDE].
- **Main screen**: a Cultivate button. Until the Foundation I realm each tap cultivates for five minutes; reaching
  Foundation I makes it automatic. A Sect button sits under the character [R74, R75 · GUIDE].
- **Breakthrough**: when the cultivation base is full, **tapping the character** starts the breakthrough; a prompt
  warns that it can fail and that failure loses cultivation base [R74 · GUIDE]. Higher realms fail more often; each
  failure raises the next attempt's base chance by 5%; each realm pill adds 5% [R76, R77 · WIKI].
- **Explore**: zones of rising difficulty and reward, each costing food; "soul wandering" repeats a cleared zone
  [R78 · WIKI].
- **Alchemy**: pill recipes are bought and refined in an Alchemy Furnace [R79 · WIKI].
- **Sect**: missions earn reputation and contribution; positions are bought with contribution one at a time (no
  skipping), and each position adds 1 to every mission reward; the Sect Exchange trades one Sect Order a day
  [R80, R81 · WIKI].
- **Events**: usually a week long, with three sub-events of daily tasks [R82 · WIKI].

**Not verified**: frames, feedback, bosses.

---

## 8. Melvor Idle

- **Hub**: a sidebar with sections (Combat, Non-Combat, General with the Completion Log and more) [R87 · WIKI]. Each
  section has its own visibility toggle; a player's bug report describes the Non-Combat toggle hiding the section's
  own header *(read)* [R88 · PLAYER]. 9 combat and 20 non-combat skills [R91 · WIKI].
- **Notices**: an item notice when something enters the bank, optionally showing the bank's new total; an "Importance"
  option keeps a notice on screen until tapped [R90 · WIKI].
- **Level-up**: a "Large" level-up setting shows a pop-up; a 2020 bug report says it should list the items the new
  level unlocks and did not *(read)* [R89 · PLAYER]. The expectation itself (a level-up lists what it opens) is the
  useful part.
- **Mastery**: 25% of mastery XP goes to a pool per skill (50% at level 99), spendable on other actions; the pool has
  checkpoints at 10, 25, 50 and 95% that unlock passives [R85 · WIKI].
- **Completion Log** for skills, mastery and more [R84 · WIKI].
- **Pets** as rare rewards: a chance per action of (action seconds × (skill level + 1)) / 25,000,000; a boss pet
  chance per dungeon clear, 1 in 250 for the base game's strongholds [R86 · WIKI].
- **Bosses**: dungeons end in a boss; the final boss sits behind an event that needs level 99 in every skill
  [R92 · WIKI]. A combat triangle gives ±10% accuracy and damage taken [R93 · WIKI].
- **Offline**: up to 24 hours, simulated as if the game had stayed open; combat offline is a setting [R83 · WIKI].

**Not verified**: panel style.

---

## 9. Diablo Immortal (landscape mobile action RPG)

- **Thumbs**: a joystick bottom-left; the abilities along the bottom-right. Skills aim at the nearest enemy by default;
  holding a skill button aims it by hand [R94 · WIKI; R96 · TALK].
- **Potion**: at the top of the right-hand cluster, above the action buttons; three charges with 20 s between uses;
  each heals 10% at once and 7.5% a second for 8 s [R97 · GUIDE; R98 · WIKI].
- Skills and Inventory icons sit at the top right [R94 · WIKI]. The pinned quest is on the left; tapping it
  auto-navigates; the minimap opens the world map [R99 · GUIDE].
- **Design intent**: the developers say the touch feel was where they spent the most time, and that touch lets a skill
  be charged while aiming and lets "custom UI" pop up for specific abilities [R95, R96 · TALK].
- **Bosses**: world bosses sweep red beams and raise spikes in red danger areas [R102 · GUIDE]. Helliquary raids are
  for eight players; after six minutes the boss enrages and pulses damage that rises to 100% of Life within 45 s and
  cannot be mitigated; in some fights the walls close in at health thresholds, acting as the enrage; each repeated death
  lengthens the resurrection cooldown [R100, R101 · WIKI].
- **Loot**: legendary gear lights up with an orange glow [R103 · GUIDE, one article].

**Not verified**: the hub layout, frames, level-up presentation.

---

## 10. What several references agree on

| Pattern | Seen in | Jade River today |
|---|---|---|
| Four skills in an arc around one large attack button, lower right | MapleStory M [R31], Diablo Immortal [R94, R96] | Four technique slots in an arc around Attack at (1165, 605) [JR: `scripts/hud.gd:25-26`]. Matches |
| A healing item with its own place, charges and a visible cooldown | Diablo Immortal [R97]; MapleStory M's potion boxes [R35] | The Gourd at (887, 555) shows its count and a flat dark disc while cooling, with no time left drawn [JR: `scripts/hud.gd:1765-1777`] |
| Something drinks for the player at a set HP | MapleStory pets [R5], MapleStory M pets [R33] | Not found |
| Notifiers next to the minimap, split by kind | MapleStory lightbulb and star [R1] | Minimap only; the icon row below it has no badges [JR: `scripts/hud.gd:42-43`] |
| A hub grouped by kind, plus player-chosen shortcuts | MapleStory Quick Menu [R2], MapleStory M top row [R31], Melvor sidebar sections [R87] | 21 tiles in a 7-column grid, ungrouped; only Mail carries a count [JR: `scripts/ui/pages/menu_page.gd:5-26, 50-52`] |
| Remote account chores without walking | IdleOn Quick Ref [R47], MapleStory Quick Move [R30] | Storage opens from an object in the world [JR: `scripts/simulation/authority/world_authority.gd:599`] |
| Tap a quest and the game walks there and starts the action | MapleStory M auto-quest [R36], Diablo Immortal auto-navigation [R99] | The tracker's auto-path walks the room graph to the target room; it drives portals and hunting, not the final talk [JR: `scripts/presentation/autopilot.gd:1-38`] |
| A level-up says what it opened | Melvor's Large level-up pop-up [R89] | A flash and a sound on breakthrough (`roadmap_master_ui.md` M5) |
| Numbers shortened when large | MapleStory unit skins [R18] | Not found |
| Collections that keep paying after completion | MapleStory Exploration [R17], IdleOn card stars [R55] | Collection pages complete once and emit `collection_page_completed` [JR: `scripts/simulation/authority/account_authority.gd:523-529`] |

---

## 11. Boss presentation (M38's research)

Jade River's bosses today: 11 bosses, 8 with `phases` (a summon at 60%, enrage at 30%), every attack with wind-up,
active and recovery times and a "!" tell, ground markers on the bombard and broadsides, and a single red boss bar
(`roadmap_master_ui.md` M39 [JR]; boss bar at `scripts/hud.gd:1907-1910`).

| Mechanic | Reference and how it is shown | Jade River today | Note for P9 [INFERRED] |
|---|---|---|---|
| Phases shown on the bar | Hilla: four bars in different colours, each a phase [R23] | One red bar; phases trigger at 60% and 30% with no mark on the bar | Notch the bar at each phase threshold and change the fill colour past it |
| Bars that link | Will: two bars that a periodic attack equalises [R24] | None | A two-bodied boss (a pair, a boss and its mirror) could share a bar rule |
| Lives per fight | Death count, 5 to 10 lives [R23, R24, R25] | The Revival page returns the player [JR: `scripts/ui/pages/revival_page.gd`] | For single play, a count of breaths drawn on the boss bar is optional; it matters more for the Online track |
| Time limit and enrage | Hilla 30 min [R23]; Black Mage 60 or 30 min [R28]; Helliquary 6 min then rising pulses [R100, R101] | Enrage at 30% HP, not by time | A soft timer that brings the enrage forward, shown as a burning incense stick beside the bar |
| An announced wipe attack with a safe place | Lucid's dragon: announced, safe on the top and bottom platforms [R26, R27] | The "!" tell per attack; room hazards warn first | Pair the caption of the big attack with a visible safe zone, not only the danger area |
| The arena changes | Lucid moves to a platform map [R26]; Helliquary walls close in [R100] | No boss demands movement by arena geometry (M39) | The most-missing piece of the eleven bosses |
| Adds that change the boss | Chizoar's crystals raise its defence until broken [R62, R63] | A summon at 60% | Give the 60% summon a job (a shield, a heal) so it must be answered |
| The boss punishes being hit | The Emperor heals from every hit he lands [R64, R65] | Not found | A clean way to reward dodging over trading blows |
| Telegraph by pose | Amarok lifts his sword before the sweep [R59, R60] | "!" tell above the head [JR: `enemy_view.gd:178`, via M39] | Pose telegraphs need new body poses; `AGENTS.md` review applies (C11) |
| Re-run reasons | Emperor once a day with rising difficulty and a bonus [R64]; crusades raise or keep difficulty [R71]; Melvor boss pet per clear [R86]; MapleStory weekly crystals [R30] | Dungeon keys, field boss timers, the Trial Tower, Beast Kings (M40) | A per-boss record (fastest time, fewest hits) is cheap and needs no new loot |
| Boss intro | Not verified in any reference | An "appears" toast and a shake on `boss_phase` (M6) | P6 should capture intro staging from video before designing, or design it without a reference |

---

## 12. Comparison table (U8)

Each row takes one Jade River system (from the authority table in `docs/architecture.md` and the README), its closest
verified reference screen, what the reference does better, and one idea to adopt. Ideas use Jade River's own words;
no reference name is carried into the game. All ideas are [INFERRED] proposals for P3–P6 and P9, gated by the P3
approval (C10).

| Jade River system (where) | Closest reference screen | What the reference does better | One idea for Jade River |
|---|---|---|---|
| **HUD combat cluster** (`hud.gd:25-41`: technique arc, Guard, Gourd, Pet, Presence, Sphere) | Diablo Immortal's right-hand cluster with the potion above it [R97]; MapleStory M's four slots around the sword [R31] | The healing item's charges and time left read at a glance | Draw the Gourd's cooldown as a sweep that empties clockwise, as the Draught slot already draws its time left (`hud.gd:1779-1786`), instead of a flat dark disc |
| **HUD minimap and icon row** (`hud.gd:42-43`) | MapleStory's lightbulb and star notifiers under the minimap [R1] | Says that something is waiting, and of which kind, without opening a page | A small mark on the minimap frame's lower edge: a lantern when a story or system quest is on offer, a plum blossom while a calendar event runs; tapping the minimap still opens the map (no new button, per C14) |
| **Menu hub** (`menu_page.gd`: 21 tiles, 7 columns, a count on Mail only) | MapleStory M's top row and Main Menu [R31, R33]; MapleStory's editable Quick Menu [R2]; Melvor's sectioned sidebar [R87] | Groups by kind, and marks what needs attention | Group the tiles into labelled bands (Self, World, Kin and Sect, Crafts and Posts, Letters and Settings) and put a vermilion "ready" seal on any tile whose system has something to claim, fed by events that already exist (a chest's points reached, an expedition back, a pouch full, a bottleneck reached) |
| **Techniques** (`techniques_page.gd`: a list and four slots per tab) | MapleStory's HEXA Matrix, node kinds by colour [R7]; IdleOn's drag-to-bar [R50] | The kind of a node reads from its colour before its text | One colour per technique kind (strike, movement, Inner Art, secret art) used on the page, the future constellation (U13) and the HUD slot rims |
| **Cultivation** (`cultivation_page.gd`, ProgressionAuthority) | Immortal Taoists' main screen: the character and a Cultivate button [R74, R75] | The core action is on the first screen, not in a tab | On the realm ascent (P5b), make the lit bottleneck landing itself the control that opens the Breakthrough page |
| **Breakthrough** (`breakthrough_page.gd`; failures with a cause and a recovery in `data/failures.json`) | Immortal Taoists: a warning before the attempt; a failure raises the next attempt's chance by 5% [R74, R76] | A failure leaves visible progress toward the next attempt | After a failure, open the page on the failure's cause and recovery line (the data already holds both) and mark on the odds bar what the recovery step adds; a rule like +5% per failure is a P10 question |
| **Daos and mastery** (the Dao tab, a list with bars, `cultivation_page.gd:315` via U13) | Melvor's mastery pool with checkpoints at 10/25/50/95% [R85] | Each bar shows where the next reward is | Tick marks on every Dao bar at the levels where something unlocks, with the next unlock's name under the next tick |
| **Seclusion and Welcome Back** (`welcome_page.gd`; 12-hour cap, `data/curves.json` `offline_cap_h`) | IdleOn's AFK Gains popup [R66]; Melvor's 24-hour offline [R83] | IdleOn's popup routes the haul in one tap | Close the Welcome Back page with the time the next absence fills ("seclusion full at 21:40 if you leave now") so the player knows when to return |
| **Inventory** (`inventory_page.gd`: Spirit Gourd and Key Items tabs) | MapleStory's Equip, Use, Set-up, Etc tabs [R4] | Kinds are sorted before the player looks | Kind filters above the bag grid (Gear, Pills and Draughts, Materials, Quest) inside the Spirit Gourd tab |
| **Storage and pouches** (`storage_page.gd`, `pouches_page.gd`) | Melvor's item notice with the bank total [R90] | The pick-up line says how much you now hold | Pick-up lines for materials show the total held in bag and storage ("Iron-grain ore +3 (41)") |
| **Quests and tracker** (`quest_page.gd`; tracker auto-path, `autopilot.gd`) | MapleStory M's auto-quest [R36, R37] | The last leg ends at the NPC or target and starts the talk or fight | Extend the auto-path's last leg inside the target room to the quest giver or objective and open the talk on arrival; any joystick touch still hands control back |
| **Daily missions and activity chests** (`data/activity.json`: chests at 20/40/60/100 points) | IdleOn's Tasks with merit points and trophies per world [R57] | Progress toward a shop and trophies is kept, not reset | Show the day's activity points as one bar with the four chests as ticks on it (retention_notes §2.1 and §2.4 give the rule side) |
| **Economy: shops, exchange, auction** (EconomyAuthority) | MapleStory's Quick Move to the crystal buyer from any town [R30]; IdleOn's remote exchange [R47] | Selling and exchanging need no walk | From any town room, the hub opens the Exchange and the Core Exchange directly; the wilds still need the walk |
| **Crafting** (`crafts_page.gd`: the five-screen furnace; garden, racks, fishing) | IdleOn's Brewing tab: every cauldron and its output on one page [R52, R53] | All running production is visible at once | A "fires" strip at the top of the Crafts page: every furnace, forge, rack and garden bed that is running, with time left, tap to go to it |
| **Workshop and the forge** (appraisal, sockets, refining across WorkshopAuthority and CraftingAuthority) | MapleStory v244's single enhancement window with odds to two decimals [R3] | Every gear-changing action in one place, with exact odds | A gear bench opened from the item detail panel that gathers appraisal, refining, sockets and set status for that one item, with the odds printed |
| **Works** (`works_page.gd`: seals, steles, favours) | IdleOn's stamps in three categories and "View Total Percentages" [R47, R54] | The summed effect is shown, not only each piece | A totals line per craft at the top of the page ("Ore: Finesse +34, capacity +12%") |
| **Training sect** (`training_sect_page.gd`: rank, contribution, three columns of five nodes) | Immortal Taoists' positions, one at a time, each adding to mission rewards [R80] | The next rank's price and gain are stated together | One line on the rank panel: the next rank's cost and what it adds to each mission reward |
| **Your sect** (`your_sect_page.gd`: Buildings, Disciples, Expeditions, Territory) | MapleStory's Legion board: characters placed as shapes on a stat grid [R15, R16] | Placement is spatial and visible | In the courtyard redesign (U16), place disciples on marked posts in the drawing, each post showing its building's bonus, instead of assigning from a list |
| **Spirit animals** (`pets_page.gd`; the HUD pet ring) | MapleStory's pet auto-potion at a set HP, one dose per drop [R5]; MapleStory M's pet potion settings [R33] | The animal does one small chore the player sets | A care setting where the active spirit animal feeds the Gourd's dose below an HP line the player chooses, one dose per drop, sharing the Gourd's cooldown |
| **Companions** (`companions_page.gd`) | MapleStory M's clockwise skill order in auto-battle [R35] | The order of skills is explicit and editable | Number each companion's techniques 1–4 on a small arc like the HUD's, and use that order in fights |
| **Characters and idle tasks** (`characters_page.gd`, AccountAuthority) | MapleStory's Legion: every character counts toward the account [R15] | Shows what each character adds to the whole | Each slot card lists that character's share of the account (its Legacy realms, its post's output) |
| **Keeping Post and the Roll-Call** (`posts_page.gd`: rows with "full in", `posts_page.gd:68-71`) | IdleOn's per-character AFK Gains popup [R66] | (Jade River already settles all characters on one page and shows the fill time; IdleOn does not) | Sort the Roll-Call by time to full, soonest first, and feed the count of full pouches to the hub tile's ready seal |
| **Codex** (`codex_page.gd`: Codex, Collection, Achievements, Paths Above, Seasons) | MapleStory's Monster Collection and Exploration [R17]; IdleOn's card stars [R55] | A finished row keeps paying; stars show depth beyond "found" | A completed Collection page becomes an expedition target for Your Sect's disciples, returning a small haul on a timer |
| **World map and teleports** (`map_page.gd`: one scroll per zone, routes, events, boss timers, ranking) | IdleOn's map teleports with free daily teleports [R49]; Diablo Immortal's minimap-to-map and pinned quest [R99] | The tracked objective is one tap from the map | The tracked quest's region carries a lantern on the scroll with a "go" action that starts the auto-path (this is P1's M27 work) |
| **Trial Tower** (`tower_page.gd`: floors cleared, daily sweep) | MapleStory M's Mu Lung Dojo, a boss per floor and three free runs [R41]; Idle Skilling's crusades that raise or keep difficulty [R71] | The player chooses between pushing and farming | Two buttons after a cleared floor: "climb" (next floor) and "hold" (repeat this floor for its reward), matching the crusade choice |
| **Calendar** (`calendar_page.gd`, CalendarAuthority) | Immortal Taoists' week-long events of three sub-events [R82]; MapleStory's star notifier [R1] | Running events are flagged outside their page | Each running event on the calendar shows its hours left, and the same event feeds the plum-blossom mark on the minimap frame (row 2) |
| **Field powers: Presence and the Sphere** (FieldAuthority; toggles at `hud.gd:30-31`) | Diablo Immortal's ability-specific pop-up UI and charge-while-aiming [R95, R96] | Controls appear for an ability only while it matters | While Presence is held, draw its Soul upkeep as an arc draining on the toggle's ring, and show the Pressure contest as a short tug bar between the two fighters |
| **Combat numbers** (`fx_layer.gd`: crits larger and gold) | MapleStory's unit damage skins above 10,000 [R18] | Large numbers stay readable in a swarm | Shorten numbers of 10,000 and above ("12.4K"), keeping crits gold and larger |
| **Bosses** (EnemyAuthority phases; the bar at `hud.gd:1907-1910`) | Hilla's coloured phase bars [R23] | The current phase and the distance to the next are visible | Notch the boss bar at 60% and 30% and change its colour past each notch (§11 lists the rest for P9) |
| **Room hazards** (WorldAuthority, HazardView) | Lucid's announced breath with safe platforms [R26, R27] | The safe place is shown, not only the danger | During a targeted hazard's warning phase, light the spots it will not strike as well as the ones it will |
| **Loot on the ground** (`loot_view.gd`: bounce and glow by quality) | Diablo Immortal's orange legendary glow [R103] | The rarest drops show from a distance | For the top grades, a column of light in the grade colour that stays until picked up |
| **Breakthrough and level moments** (a flash and a sound, M5) | Melvor's level-up pop-up that lists what the level opens [R89] | Tells the player what is new | After a minor breakthrough, one banner line naming what the stage opens (a slot, a recipe, a region), and none when nothing opens |
| **Settings** (`settings_page.gd`) | Melvor's notice options: bank totals, notices kept until tapped [R90] | The player tunes how noisy the game is | A notices section: pick-up lines on or off, and rare-drop notices kept until tapped |

Not compared, for want of a verified reference screen: the auction, the guqin and chess pages, relations (karma,
bonds, county), mail (it already has a claim-all button, `mail_page.gd:31`) and the shell screens.

---

## 13. What this page does not settle

- **Layouts from pictures.** Every position above comes from text. P3 should take one screenshot per reference screen
  it borrows from (from the publisher's store page or wiki) and keep it with the mockup.
- **Frames and panels.** No reference's panel art could be described from text beyond "clearer, cleaner" [R3]. The
  frame style stays with the build's own kits (U23, C7).
- **Soul Saver.** Nothing but the store listing was found; the reference adds little until someone plays it.
- **Boss intros.** No reference's staging was verified (§11 last row).

---

## 14. Sources

Page titles as the search engine gave them. *(read)* marks a page that was opened; every other page was seen through
the search engine's extract.

### MapleStory (PC)

| # | Page title | URL | Label |
|---|---|---|---|
| R1 | User Interface (MapleStorySEA guide) | https://www.maplesea.com/guide/user_interface/ | OFFICIAL |
| R2 | KMS ver. 1.2.402 – Skill/UI Changes & MapleStory's 22nd Anniversary: Maple University! (Orange Mushroom's Blog) | https://orangemushroom.net/2025/04/17/kms-ver-1-2-402-skill-ui-changes-maplestory-22nd-anniversary-maple-university/ | GUIDE (fan translation) |
| R3 | NEXT III Patch Notes - UI Revamp and Improvements (v244) | https://www.maplesea.com/updates/view/v244_Patch_Notes_2/ | OFFICIAL |
| R4 | Slot Expansion Coupon - MapleStory Wiki | https://maplestorywiki.net/w/Slot_Expansion_Coupon | WIKI |
| R5 | Pets and Androids - MapleStory \| Guides | https://www.nexon.com/maplestory/game/maple-guides/all/29583/pets-and-androids | OFFICIAL |
| R6 | How to use pets and pet skills - Official MapleStory Website (forum) | https://forums.maplestory.nexon.net/discussion/3769/how-to-use-pets-and-pet-skills | PLAYER |
| R7 | HEXA Matrix - MapleStory Wiki | https://maplestorywiki.net/w/HEXA_Matrix | WIKI |
| R8 | V Matrix - MapleStory Wiki | https://maplestorywiki.net/w/V_Matrix | WIKI |
| R9 | MapleStory Hyper Stats Guide - AyumiLove | https://ayumilove.net/maplestory-hyper-stats-guide/ | GUIDE |
| R10 | Professions - MapleStory Wiki | https://maplestorywiki.net/w/Professions | WIKI |
| R11 | MapleStory/Professions — StrategyWiki | https://strategywiki.org/wiki/MapleStory/Professions | WIKI |
| R12 | Guild Skills - MapleStory Wiki | https://maplestorywiki.net/w/Guild_Skills | WIKI |
| R13 | Flag Race - MapleStory Wiki | https://maplestorywiki.net/w/Flag_Race | WIKI |
| R14 | Guilds and Alliances - MapleStory \| Guides | https://www.nexon.com/maplestory/game/maple-guides/all/5894/guilds-and-alliances | OFFICIAL |
| R15 | Legion System \| MapleWiki - Fandom | https://maplestory.fandom.com/wiki/Legion_System | WIKI |
| R16 | [Updated] Join the Legion System! - MapleStory \| News | https://www.nexon.com/maplestory/news/23438 | OFFICIAL |
| R17 | Monster Collection \| MapleWiki \| Fandom | https://maplestory.fandom.com/wiki/Monster_Collection | WIKI |
| R18 | damage skin - NamuWiki | https://en.namu.wiki/w/%EB%8D%B0%EB%AF%B8%EC%A7%80%20%EC%8A%A4%ED%82%A8 | WIKI |
| R19 | Damage Skin Crit/Noncrit Reverse Option - Official MapleStory Website (forum) | https://forums.maplestory.nexon.net/discussion/6567/damage-skin-crit-noncrit-reverse-option | PLAYER |
| R20 | "LEVEL UP" sound effect - Official MapleStory Website (forum) | https://forums.maplestory.nexon.net/discussion/15800/level-up-sound-effect | PLAYER |
| R21 | Runes - MapleStory Wiki | https://maplestorywiki.net/w/Runes | WIKI |
| R22 | MapleStory/Elite Monsters and Elite Bosses — StrategyWiki | https://strategywiki.org/wiki/MapleStory/Elite_Monsters_and_Elite_Bosses | WIKI |
| R23 | Hilla/Monster (Reborn) - MapleStory Wiki | https://maplestorywiki.net/w/Hilla/Monster_(Reborn) | WIKI |
| R24 | MapleStory/Will — StrategyWiki | https://strategywiki.org/wiki/MapleStory/Will | WIKI |
| R25 | MapleStory/Boss Monster/Boss Content - NamuWiki | https://en.namu.wiki/w/%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC/%EB%B3%B4%EC%8A%A4%20%EB%AA%AC%EC%8A%A4%ED%84%B0/%EB%B3%B4%EC%8A%A4%20%EC%BB%A8%ED%85%90%EC%B8%A0 | WIKI |
| R26 | MapleStory/Lucid — StrategyWiki | https://strategywiki.org/wiki/MapleStory/Lucid | WIKI |
| R27 | MapleStory Lucid Boss Guide - DigitalTQ | https://www.digitaltq.com/maplestory-lucid-boss-guide | GUIDE |
| R28 | Black Mage/Monster - MapleStory Wiki | https://maplestorywiki.net/w/Black_Mage/Monster | WIKI |
| R29 | 5% HP Chart of MapleStory Bosses \| The Digital Crowns | https://thedigitalcrowns.com/5-hp-of-maplestory-bosses/ | GUIDE |
| R30 | Boss Content (MapleStorySEA wiki) | https://www.maplesea.com/wiki/Feature/BossContent | OFFICIAL |

### MapleStory M

| # | Page title | URL | Label |
|---|---|---|---|
| R31 | System - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/System | WIKI |
| R32 | MapleStory M Starter Guide \| MMOHuts | https://mmohuts.com/news/maplestory-m-starter-guide | GUIDE |
| R33 | Main Menu - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/Main_Menu | WIKI |
| R34 | Auto Battle - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/Auto_Battle | WIKI |
| R35 | MapleStory M Leveling Guide for PC MapleStory Beginners \| Peak (a player's post on Nexon's community site) | https://peak.nexon.com/en/post/479 | PLAYER |
| R36 | Auto Quest System - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/Auto_Quest_System | WIKI |
| R37 | MapleStory M: How to Turn On Auto Quest and What it Does - Twinfinite | https://twinfinite.net/guides/maplestory-m-auto-battle-turn-on/ | GUIDE |
| R38 | Dungeon \| MapleStory M Wiki \| Fandom | https://maplestorym.fandom.com/wiki/Dungeon | WIKI |
| R39 | Daily Dungeons - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/Daily_Dungeons | WIKI |
| R40 | Elite Dungeons - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/Elite_Dungeons | WIKI |
| R41 | Mu Lung Dojo \| MapleStory M Wiki \| Fandom | https://maplestorym.fandom.com/wiki/Mu_Lung_Dojo | WIKI |
| R42 | Expedition \| MapleStory M Wiki \| Fandom | https://maplestorym.fandom.com/wiki/Expedition | WIKI |
| R43 | MapleStory M Review – An MMO port which only gets the port bit right \| Pocket Gamer | https://www.pocketgamer.com/maplestory-m/review/ | GUIDE (press) |

### Soul Saver: Idle RPG

| # | Page title | URL | Label |
|---|---|---|---|
| R44 | Soul Saver: Idle RPG (App Store listing) | https://apps.apple.com/vn/app/soul-saver-idle-rpg/id1416402647?l=vi | OFFICIAL |
| R45 | Soul Saver: Idle RPG APK for Android Download (APKPure, store mirror) | https://apkpure.com/soul-saver-idle-rpg/com.funigloo.honm | GUIDE |
| R46 | SOUL SAVER: IDLE SAVERS Guide #2 (How to Play) (Medium, the sibling title's publisher) | https://medium.com/soul-saver-idle-savers/soul-saver-idle-savers-guide-content-d669f232bc21 | OFFICIAL (sibling title) |

### Legends of IdleOn

| # | Page title | URL | Label |
|---|---|---|---|
| R47 | Quick Ref - IdleOn MMO Wiki | https://idleon.wiki/wiki/Quick_Ref | WIKI |
| R48 | Codex - IdleOn MMO Wiki | https://idleon.wiki/wiki/Codex | WIKI |
| R49 | IdleOn Beginner Guide - Tips and Tricks - DigitalTQ | https://www.digitaltq.com/wiki/idleon/beginner-guide | GUIDE |
| R50 | Legends of Idleon - How to Use Skills (SlytherGames) | https://www.slythergames.com/2021/05/13/legends-of-idleon-how-to-use-skills/ | GUIDE |
| R51 | Legends of IdleOn - Play Now \| Free Idle MMO Online (idleon.online, unofficial) | https://idleon.online/ | GUIDE |
| R52 | Alchemy - IdleOn MMO Wiki | https://idleon.wiki/wiki/Alchemy | WIKI |
| R53 | Alchemy Guide - IdleOn - DigitalTQ | https://www.digitaltq.com/wiki/idleon/alchemy | GUIDE |
| R54 | Stamps - IdleOn MMO Wiki | https://idleon.wiki/wiki/Stamps | WIKI |
| R55 | Cards - IdleOn MMO Wiki | https://idleon.wiki/wiki/Cards | WIKI |
| R56 | Guilds - IdleOn MMO Wiki | https://idleon.wiki/wiki/Guilds | WIKI |
| R57 | Tasks - IdleOn MMO Wiki | https://idleon.wiki/wiki/Tasks | WIKI |
| R58 | Drop Rate - IdleOn MMO Wiki | https://idleon.wiki/wiki/Drop_Rate | WIKI |
| R59 | Amarok - IdleOn MMO Wiki | https://idleon.wiki/wiki/Amarok | WIKI |
| R60 | IdleOn Amarok Boss Guide - DigitalTQ | https://www.digitaltq.com/wiki/idleon/amarok-boss-guide | GUIDE |
| R61 | Efaunt - IdleOn MMO Wiki | https://idleon.wiki/wiki/Efaunt | WIKI |
| R62 | Chizoar - IdleOn MMO Wiki | https://idleon.wiki/wiki/Chizoar | WIKI |
| R63 | Chizoar Boss Guide - World 3 - IdleOn - DigitalTQ | https://www.digitaltq.com/wiki/idleon/chizoar-boss-guide-world-3 | GUIDE |
| R64 | Emperor - IdleOn MMO Wiki | https://idleon.wiki/wiki/Emperor | WIKI |
| R65 | The Emperor Boss World 6 - IdleOn - DigitalTQ | https://www.digitaltq.com/wiki/idleon/the-emperor-world-6-boss | GUIDE |
| R66 | `docs/research/idle_gathering_research.md` (this repository; its own sources in its §0) | — | internal |

### Idle Skilling

| # | Page title | URL | Label |
|---|---|---|---|
| R67 | Idle Skilling on Steam | https://store.steampowered.com/app/1048370/Idle_Skilling/ | OFFICIAL |
| R68 | Idle Skilling - Apps on Google Play | https://play.google.com/store/apps/details?id=com.lavaflame.IdleSkilling&hl=en_US&gl=US | OFFICIAL |
| R69 | Idle Skilling – Free to Play \| Kongregate | https://www.kongregate.com/en/games/lavaflame2/idle-skilling | OFFICIAL |
| R70 | Rebirth \| Idle Skilling Wiki \| Fandom | https://idle-skilling.fandom.com/wiki/Rebirth | WIKI |
| R71 | Crusades \| Idle Skilling Wiki \| Fandom | https://idle-skilling.fandom.com/wiki/Crusades | WIKI |
| R72 | Idle Skilling - Ultimate Guide (Steam Community guide) | https://steamcommunity.com/sharedfiles/filedetails/?id=2863651114 | PLAYER |

### Immortal Taoists

| # | Page title | URL | Label |
|---|---|---|---|
| R73 | Immortal Taoists - Idle Manga - Apps on Google Play | https://play.google.com/store/apps/details?id=com.immortaltaoists.en&hl=en_US | OFFICIAL |
| R74 | Beginner's Guide to Immortal Taoists on PC (BlueStacks) | https://www.bluestacks.com/blog/game-guides/immortal-taoists/it-beginner-guide-en.html | GUIDE |
| R75 | BlueStacks' Beginners Guide to Playing Immortal Taoists | https://www.bluestacks.com/blog/game-guides/immortal-taoists/imt-beginner-guide-en.html | GUIDE |
| R76 | Breaking Through \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Breaking_Through | WIKI |
| R77 | Tribulation \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Tribulation | WIKI |
| R78 | Explore \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Explore | WIKI |
| R79 | Pills \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Pills | WIKI |
| R80 | Sect \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Sect | WIKI |
| R81 | Sect Exchange \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Sect_Exchange | WIKI |
| R82 | Special Event \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Special_Event | WIKI |

### Melvor Idle

| # | Page title | URL | Label |
|---|---|---|---|
| R83 | Offline Progression - Melvor Idle | https://wiki.melvoridle.com/w/Offline_Progression | WIKI |
| R84 | Completion Log - Melvor Idle | https://wiki.melvoridle.com/w/Completion_Log | WIKI |
| R85 | Mastery - Melvor Idle | https://wiki.melvoridle.com/w/Mastery | WIKI |
| R86 | Pets - Melvor Idle | https://wiki.melvoridle.com/w/Pets | WIKI |
| R87 | Mod Creation/Sidebar API Reference - Melvor Idle | https://wiki.melvoridle.com/w/Mod_Creation/Sidebar_API_Reference | WIKI |
| R88 | [Bug]: NON-COMBAT section in sidemenu disappears permanently when toggling it's visibility · Issue #2513 *(read)* | https://github.com/MelvorIdle/melvoridle.github.io/issues/2513 | PLAYER |
| R89 | Level up notification pop-up · Issue #370 *(read)* | https://github.com/MelvorIdle/melvoridle.github.io/issues/370 | PLAYER |
| R90 | Settings - Melvor Idle | https://wiki.melvoridle.com/w/Settings | WIKI |
| R91 | Skills - Melvor Idle | https://wiki.melvoridle.com/w/Skills | WIKI |
| R92 | Dungeons - Melvor Idle | https://wiki.melvoridle.com/w/Dungeons | WIKI |
| R93 | Combat Triangle - Melvor Idle | https://wiki.melvoridle.com/w/Combat_Triangle | WIKI |

### Diablo Immortal

| # | Page title | URL | Label |
|---|---|---|---|
| R94 | Controls \| Diablo Immortal Wiki (Fextralife) | https://diabloimmortal.wiki.fextralife.com/Controls | WIKI |
| R95 | Diablo Immortal interview: Creating a mobile MMO Diablo experience \| Shacknews | https://www.shacknews.com/article/123135/diablo-immortal-interview-creating-a-mobile-mmo-diablo-experience | TALK |
| R96 | Interview: Diablo Immortal lead designer Wyatt Cheng details what's next for the hotly-anticipated MMO (Android Police) | https://www.androidpolice.com/2021/02/24/interview-diablo-immortal-lead-designer-wyatt-cheng-details-whats-next-for-the-hotly-anticipated-mmo/ | TALK |
| R97 | How to Heal \| Diablo Immortal (Game8) | https://game8.co/games/Diablo-Immortal/archives/378456 | GUIDE |
| R98 | Healing Potions \| Diablo Wiki \| Fandom | https://diablo.fandom.com/wiki/Healing_Potions | WIKI |
| R99 | Auto Navigation Guide \| Diablo Immortal (Game8) | https://game8.co/games/Diablo-Immortal/archives/378464 | GUIDE |
| R100 | Helliquary \| Diablo Wiki \| Fandom | https://diablo.fandom.com/wiki/Helliquary | WIKI |
| R101 | Enrage Timer \| Diablo Wiki \| Fandom | https://diablo.fandom.com/wiki/Enrage_Timer | WIKI |
| R102 | Diablo Immortal: How To Find & Defeat Blood Rose \| World Boss Guide - Gameranx | https://gameranx.com/features/id/314544/article/diablo-immortal-how-to-find-defeat-blood-rose-world-boss-guide/ | GUIDE |
| R103 | Diablo Immortal: How to Find and Farm Legendary Gear \| Den of Geek | https://www.denofgeek.com/games/diablo-immortal-how-to-find-legendary-gear-farming-location-tips/ | GUIDE |

### Other

| # | Page title | URL | Label |
|---|---|---|---|
| R104 | Experience Table - Melvor Idle (quotes the developer, Malcs, from a Steam discussion) | https://wiki.melvoridle.com/w/Experience_Table | WIKI |
