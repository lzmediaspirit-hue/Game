# Retention: loops, the psychology behind them, and what the references do

Research for P2 (c) in `docs/roadmap_master_ui.md`: the research half of M21 (daily reasons to log in, social loops,
"one more level"). The engagement plan itself is P2 (e); this page is its evidence. The UI half of P2 (c) is
`docs/research/ui_reference_notes.md`, which covers the same eight references.

Date of research: 2026-09-26. Jade River state: commit bfbb2c5 (v1.2 Phase C).

---

## 0. Sources, method and confidence

**How this was researched.** Web search only. Page fetches were refused by the network sandbox for every site except
github.com, so every source below was seen through the search engine's extract of the named page, not opened. Where
an extract mixed several pages and did not say which one held a claim, the citation names all of them and says so.
Figures quoted from a paper were taken from the extract of the paper's own page or, where noted, from a secondary
summary of it.

**Confidence labels** (as in `idle_gathering_research.md` and `ui_reference_notes.md`):

- **[PAPER]**: a peer-reviewed study. High confidence in what was measured; the step from a loyalty card or a lab task
  to a game is mine and is marked [INFERRED].
- **[OFFICIAL]**: the publisher's own page (patch notes, a store listing, an official blog). High on behaviour at the
  page's date.
- **[WIKI]**: a community wiki. Medium to high.
- **[GUIDE]**: an industry article, a third-party guide or a press review. Medium.
- **[TALK]**: a design talk or a researcher's article for developers. High on intent.
- **[PLAYER]**: one player's post. Low to medium; said so where used.
- **[INFERRED]**: my reading or proposal.
- **[JR]**: Jade River's files in this worktree.

### Sources

**Psychology and industry**

| # | Page title | URL | Label |
|---|---|---|---|
| S1 | The Goal-Gradient Hypothesis Resurrected: Purchase Acceleration, Illusionary Goal Progress, and Customer Retention (Kivetz, Urminsky, Zheng, *Journal of Marketing Research* 43(1), 2006, 39–58) | https://journals.sagepub.com/doi/abs/10.1509/jmkr.43.1.39 | PAPER |
| S2 | The Endowed Progress Effect: How Artificial Advancement Increases Effort (Nunes, Drèze, *Journal of Consumer Research* 32(4), 2006, 504–512) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=991962 | PAPER |
| S3 | Prospect Theory: An Analysis of Decision under Risk (Kahneman, Tversky, *Econometrica* 47, 1979, 263–291) | https://www.econometricsociety.org/publications/econometrica/1979/03/01/prospect-theory-analysis-decision-under-risk | PAPER |
| S4 | Advances in prospect theory: Cumulative representation of uncertainty (Tversky, Kahneman, *Journal of Risk and Uncertainty* 5(4), 1992, 297–323) | https://link.springer.com/article/10.1007/BF00122574 | PAPER |
| S5 | Behavioral Game Design (John Hopson, Gamasutra, 27 April 2001) | https://www.gamedeveloper.com/design/behavioral-game-design | TALK |
| S6 | The Motivational Pull of Video Games: A Self-Determination Theory Approach (Ryan, Rigby, Przybylski, *Motivation and Emotion* 30(4), 2006, 347–363) | https://link.springer.com/article/10.1007/s11031-006-9051-8 | PAPER |
| S7 | Dark Patterns in the Design of Games (Zagal, Björk, Lewis, FDG 2013, 39–46) | http://www.fdg2013.org/program/papers/paper06_zagal_etal.pdf | PAPER |
| S8 | GDC Vault - Idle Games: The Mechanics and Monetization of Self-Playing Games (Anthony Pecorella, GDC 2015) | https://www.gdcvault.com/play/1022065/Idle-Games-The-Mechanics-and | TALK |
| S9 | The Science & Craft of Designing Daily Rewards -- and Why FTP Games Need Them (Game Developer) | https://www.gamedeveloper.com/business/the-science-craft-of-designing-daily-rewards----and-why-ftp-games-need-them | GUIDE |
| S10 | How to Keep Your Players in Game with Appointment Mechanics (GameRefinery) | https://www.gamerefinery.com/keep-your-players-in-game-with-appointment-mechanics/ | GUIDE |
| S11 | Feature Spotlight: Progression Elements in Daily Rewards (GameRefinery) | https://www.gamerefinery.com/feature-spotlight-progression-daily-rewards/ | GUIDE |
| S12 | How Streaks keep Duolingo learners committed to their language goals (Duolingo blog) | https://blog.duolingo.com/how-streaks-keep-duolingo-learners-committed-to-their-language-goals/ | OFFICIAL (not a game) |
| S13 | how duolingo streak builds habit (Duolingo blog) | https://blog.duolingo.com/how-duolingo-streak-builds-habit | OFFICIAL (not a game) |
| S14 | Foundations of the Endowed Progress Effect (ShiftKognition, a secondary summary of S2) | https://shiftkognition.com/en/chapters/effet-progression-dotee-endowed-progress-ia-psychologie-vente-fondements-progression-dotee | GUIDE |

**MapleStory**

| # | Page title | URL | Label |
|---|---|---|---|
| S15 | MAPLE Daily Gift - MapleStory Wiki | https://maplestorywiki.net/w/MAPLE_Daily_Gift | WIKI |
| S16 | MapleStory/Arcane River — StrategyWiki | https://strategywiki.org/wiki/MapleStory/Arcane_River | WIKI |
| S17 | Arcane and Sacred Symbol Power - MapleStory \| General Post | https://www.nexon.com/maplestory/general-post/5581 | OFFICIAL |
| S18 | Boss Content (MapleStorySEA wiki) | https://www.maplesea.com/wiki/Feature/BossContent | OFFICIAL |
| S19 | Progression Guide \| MapleStory \| Grandis Library | https://grandislibrary.com/content/progression-guide | GUIDE |
| S20 | Legion System \| MapleWiki - Fandom | https://maplestory.fandom.com/wiki/Legion_System | WIKI |
| S21 | Monster Collection \| MapleWiki \| Fandom | https://maplestory.fandom.com/wiki/Monster_Collection | WIKI |
| S22 | Runes - MapleStory Wiki | https://maplestorywiki.net/w/Runes | WIKI |
| S23 | MapleStory/Elite Monsters and Elite Bosses — StrategyWiki | https://strategywiki.org/wiki/MapleStory/Elite_Monsters_and_Elite_Bosses | WIKI |
| S24 | Challenger World and Hyper Burning MAX - MapleStory \| News | https://www.nexon.com/maplestory/news/events/27482/challenger-world-and-hyper-burning-max | OFFICIAL |
| S25 | hyper burning - NamuWiki | https://en.namu.wiki/w/%ED%95%98%EC%9D%B4%ED%8D%BC%20%EB%B2%84%EB%8B%9D | WIKI |
| S26 | Guild Skills - MapleStory Wiki | https://maplestorywiki.net/w/Guild_Skills | WIKI |
| S27 | Guilds and Alliances - MapleStory \| Guides | https://www.nexon.com/maplestory/game/maple-guides/all/5894/guilds-and-alliances | OFFICIAL |

**MapleStory M**

| # | Page title | URL | Label |
|---|---|---|---|
| S28 | Attendance Reward \| MapleStory M Wiki \| Fandom | https://maplestorym.fandom.com/wiki/Attendance_Reward | WIKI |
| S29 | Auto Battle - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/Auto_Battle | WIKI |
| S30 | Daily Dungeons - Official MapleStory M Wiki - Fandom | https://maplestorym-archive.fandom.com/wiki/Daily_Dungeons | WIKI |
| S31 | Mu Lung Dojo \| MapleStory M Wiki \| Fandom | https://maplestorym.fandom.com/wiki/Mu_Lung_Dojo | WIKI |
| S32 | Expedition \| MapleStory M Wiki \| Fandom | https://maplestorym.fandom.com/wiki/Expedition | WIKI |
| S33 | MapleStory M Review – An MMO port which only gets the port bit right \| Pocket Gamer | https://www.pocketgamer.com/maplestory-m/review/ | GUIDE (press) |

**Soul Saver: Idle RPG**

| # | Page title | URL | Label |
|---|---|---|---|
| S34 | Soul Saver: Idle RPG (App Store listing) | https://apps.apple.com/vn/app/soul-saver-idle-rpg/id1416402647?l=vi | OFFICIAL |

**Legends of IdleOn**

| # | Page title | URL | Label |
|---|---|---|---|
| S35 | `docs/research/idle_gathering_research.md` (this repository; its sources in its §0) | — | internal |
| S36 | Daily Checklist - IdleOn MMO Wiki | https://idleon.wiki/wiki/Daily_Checklist | WIKI |
| S37 | Tasks - IdleOn MMO Wiki | https://idleon.wiki/wiki/Tasks | WIKI |
| S38 | World 1 Tasks, Achievements and Merit Shop - IdleOn - DigitalTQ | https://www.digitaltq.com/wiki/idleon/world-1-achievements-tasks-merit-unlocks | GUIDE |
| S39 | Guilds - IdleOn MMO Wiki | https://idleon.wiki/wiki/Guilds | WIKI |
| S40 | Cards - IdleOn MMO Wiki | https://idleon.wiki/wiki/Cards | WIKI |
| S41 | Emperor - IdleOn MMO Wiki | https://idleon.wiki/wiki/Emperor | WIKI |
| S42 | Drop Rate - IdleOn MMO Wiki | https://idleon.wiki/wiki/Drop_Rate | WIKI |

**Idle Skilling**

| # | Page title | URL | Label |
|---|---|---|---|
| S43 | Idle Skilling on Steam | https://store.steampowered.com/app/1048370/Idle_Skilling/ | OFFICIAL |
| S44 | Idle Skilling - Apps on Google Play | https://play.google.com/store/apps/details?id=com.lavaflame.IdleSkilling&hl=en_US&gl=US | OFFICIAL |
| S45 | Idle Skilling – Free to Play \| Kongregate | https://www.kongregate.com/en/games/lavaflame2/idle-skilling | OFFICIAL |
| S46 | Idle Skilling - Ultimate Guide (Steam Community guide) | https://steamcommunity.com/sharedfiles/filedetails/?id=2863651114 | PLAYER |
| S47 | Crusades \| Idle Skilling Wiki \| Fandom | https://idle-skilling.fandom.com/wiki/Crusades | WIKI |

**Immortal Taoists**

| # | Page title | URL | Label |
|---|---|---|---|
| S48 | Immortal Taoists - Idle Manga - Apps on Google Play | https://play.google.com/store/apps/details?id=com.immortaltaoists.en&hl=en_US | OFFICIAL |
| S49 | Beginner's Guide to Immortal Taoists on PC (BlueStacks) | https://www.bluestacks.com/blog/game-guides/immortal-taoists/it-beginner-guide-en.html | GUIDE |
| S50 | BlueStacks' Beginners Guide to Playing Immortal Taoists | https://www.bluestacks.com/blog/game-guides/immortal-taoists/imt-beginner-guide-en.html | GUIDE |
| S51 | Breaking Through \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Breaking_Through | WIKI |
| S52 | Tribulation \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Tribulation | WIKI |
| S53 | Sect \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Sect | WIKI |
| S54 | Sect Exchange \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Sect_Exchange | WIKI |
| S55 | Special Event \| Immortal Taoists Wiki \| Fandom | https://immortal-taoists.fandom.com/wiki/Special_Event | WIKI |

**Melvor Idle**

| # | Page title | URL | Label |
|---|---|---|---|
| S57 | Offline Progression - Melvor Idle | https://wiki.melvoridle.com/w/Offline_Progression | WIKI |
| S58 | Completion Log - Melvor Idle | https://wiki.melvoridle.com/w/Completion_Log | WIKI |
| S59 | Mastery - Melvor Idle | https://wiki.melvoridle.com/w/Mastery | WIKI |
| S60 | Pets - Melvor Idle | https://wiki.melvoridle.com/w/Pets | WIKI |
| S61 | Experience Table - Melvor Idle | https://wiki.melvoridle.com/w/Experience_Table | WIKI |

**Diablo Immortal**

| # | Page title | URL | Label |
|---|---|---|---|
| S62 | Daily Reset Times: All Things To Do Daily \| Diablo Immortal (Game8) | https://game8.co/games/Diablo-Immortal/archives/377529 | GUIDE |
| S63 | Battle Points \| Diablo Wiki \| Fandom | https://diablo.fandom.com/wiki/Battle_Points | WIKI |
| S64 | Diablo Immortal Daily and Weekly Checklist Guide (EXPCarry) | https://expcarry.com/diablo-immortal-daily-weekly-checklist | GUIDE |
| S65 | Helliquary \| Diablo Wiki \| Fandom | https://diablo.fandom.com/wiki/Helliquary | WIKI |

---

## 1. The psychology

### 1.1 Variable rewards

- **What the evidence says.** A variable-ratio schedule gives each action a chance of reward, so the chance of reward is
  constant and "the player always has a reason to do the next thing". A fixed-ratio schedule produces a long pause
  after each reward and then a burst of activity until the next [S5 · TALK]. Activity rises with how soon the player
  expects something good to happen [S5 · TALK].
- **In the references.** MapleStory places runes after a *random* number of kills and spawns elite monsters on a
  cooldown [S22, S23 · WIKI]. IdleOn rolls a rare table, then each item on it [S42 · WIKI]. Melvor gives every
  skilling action a small pet chance that grows with action length and level [S60 · WIKI].
- **Caution.** Zagal, Björk and Lewis define dark patterns as design choices that work against the player's
  interests, and give questions for spotting them [S7 · PAPER]. A random reward stays on the right side of that line
  when the odds are known and the fixed rewards alone make steady progress [INFERRED].

### 1.2 Goal gradient

- **What the evidence says.** Effort rises as a reward nears. In a café's "buy 10, get 1 free" program, customers bought
  coffee more often the closer they were to the free one [S1 · PAPER]. The same study found *illusionary* progress
  works: a 12-stamp card with 2 stamps already given was completed faster than a plain 10-stamp card [S1 · PAPER].
- **In the references.** Melvor's mastery pool has four checkpoints (10, 25, 50, 95%) that each unlock a passive
  [S59 · WIKI]. MapleStory's Daily Gift is a 28-step month [S15 · WIKI]. MapleStory M pays a larger attendance reward
  every 7th check [S28 · WIKI]. MapleStory's Monster Collection pays per finished row, not only per finished page
  [S21 · WIKI].
- **Implication** [INFERRED]: long bars need visible intermediate stops; the last stretch before each stop is where
  play is most willing.

### 1.3 Loss aversion

- **What the evidence says.** "Losses loom larger than gains": the value function is steeper for losses than for gains
  of the same size [S3 · PAPER]. The later cumulative version estimates a loss-aversion coefficient of about 2.25
  [S4 · PAPER].
- **In the references.**
  - MapleStory lets elite bosses curse a map whose rune is left unused for five minutes, lowering EXP and drops
    [S22 · WIKI].
  - Warframe's login ladder (as described by an industry article) drops a player back to the lowest tier after one
    missed day; the article says players read this as punishment and some leave [S9 · GUIDE].
  - Immortal Taoists makes a failed breakthrough cost cultivation base, but each failure adds 5% to the next attempt's
    base chance [S51, S52 · WIKI].
  - Outside games, Duolingo says many learners are "highly averse" to losing a streak, and offers a Streak Freeze that
    pauses it for a day [S12, S13 · OFFICIAL].
- **Implication** [INFERRED]: a loss the player can see coming and prevent (a rune, a streak with a freeze) motivates;
  a loss that arrives after a missed day drives people away. For an offline-first single-player game the second kind
  has no place.

### 1.4 Endowed progress

- **What the evidence says.** Car-wash customers given an 8-stamp card starting at 0/8, or a 10-stamp card starting at
  2/10, both needed 8 washes; 19% of the first group and 34% of the second completed the card [S2 · PAPER; the
  figures via the summary S14].
- **In the references.** MapleStory M's auto-battle bank starts full at 120 minutes when it unlocks [S29 · WIKI].
  MapleStory's Hyper Burning MAX counts every level from 10 to 260 as five [S24 · OFFICIAL]; the earlier version gave
  1+2 levels to 250, and the rename to MAX came on 19 December 2024 [S25 · WIKI]. Reading both as endowed progress is
  mine [INFERRED].

### 1.5 Competence, autonomy and relatedness

- **What the evidence says.** Across four studies, perceived autonomy and competence in a game predicted enjoyment and
  the wish to play again; in an online community, relatedness also independently predicted enjoyment and future play
  [S6 · PAPER].
- **Implication** [INFERRED]: social loops are not the only source of relatedness. Companions, bonds and a sect of NPC
  disciples can carry some of it in a single-player game; the paper's online sample is the evidence for the rest,
  which waits for v2.0 Online.

### 1.6 Appointments and idle play

- GameRefinery's study of the top 200 US iOS games found daily gift systems in every category; mid-core games tend to
  ask for a task before the gift, casual and casino games hand it over [S10 · GUIDE]. It counts progressive daily
  rewards in nearly half of the US iOS top-grossing 100 [S11 · GUIDE].
- Pecorella's GDC 2015 talk reports that idle games then had some of the best retention on Kongregate [S8 · TALK,
  via the talk's summary].

---

## 2. The loops, and what each reference does

### 2.1 Daily and weekly loops

| Reference | Daily | Weekly | Source |
|---|---|---|---|
| MapleStory | Arcane River: a daily quest per area pays that area's symbol; the hunt shrinks from 600 to 400 to 200 monsters as later areas open | A weekly quest per area; boss crystals reset on Thursday. The cap is given as 60 sold a week (SEA) by one page and 12 accepted by the Collector by another; the difference is not resolved | [S16 · WIKI; S17, S18 · OFFICIAL; S19 · GUIDE] |
| MapleStory M | Daily Dungeons, 3 free entries, reset at midnight; Mu Lung Dojo, 3 free runs; Expedition bosses, 2 entries a day; a free 2-hour auto-battle charge | Not found | [S29, S30, S31, S32 · WIKI] |
| Soul Saver | Not found | Not found | — |
| Legends of IdleOn | A checklist of dailies: free gems, a task per world, guild point tasks, shop restocks, daily crystal and boss spawns; the Emperor boss once a day | Guild tasks refresh weekly and give at least two gift boxes | [S36, S37, S39, S41 · WIKI; S38 · GUIDE] |
| Idle Skilling | The store text says the game is "meant to be played for 5–10 minutes a day" | Not found | [S43, S44 · OFFICIAL] |
| Immortal Taoists | Sect missions for reputation and contribution; one Sect Order a day from the Sect Exchange | Special events a week long, three sub-events of daily tasks | [S53, S54, S55 · WIKI] |
| Melvor Idle | Not found | Not found | — |
| Diablo Immortal | Up to 8 bounties a day; unfinished ones roll over, up to 24 | Battle Points capped at 2,400 a week, reset on Thursday with a new pass; Helliquary bosses twice a week each | [S62, S64 · GUIDE; S63 · WIKI] |

The rolling bounty board is the one daily loop here that does not punish a missed day [INFERRED, from S62].

### 2.2 Login rewards

| Reference | What it does | Source |
|---|---|---|
| MapleStory | **Daily Gift**: one gift a day, earned by defeating 300 monsters within 20 levels, 28 gifts in sequence per month, reset on the 1st; once per account per day, from level 33; gifts expire 7 days after claiming | [S15 · WIKI] |
| MapleStory M | **Attendance**: earned by time online; once on weekdays and twice on weekend days; a larger reward every 7th check; a missed day can be recovered with an Attendance Pass; account-wide; rewards go to the inbox | [S28 · WIKI] |
| Legends of IdleOn | Each guild member's first login of the day adds 10 guild points to the guild, without claiming | [S39 · WIKI] |
| Industry | Warframe: consecutive days raise the reward tier, one missed day resets it. Puzzle & Dragons: cumulative days (100, 367, 1,000) unlock fixed prizes. The article recommends both consecutive and cumulative rewards, some randomness and an opt-in reminder | [S9 · GUIDE] |
| Industry | Dragon City's calendar lets a player recover a missed day's reward by watching an ad | [S10 · GUIDE] |

Twenty-eight gifts in a month of 28 to 31 days leaves up to three missed days before anything is lost [INFERRED,
from S15].

### 2.3 Offline gains

| Reference | Cap | What accrues | How it is claimed | Source |
|---|---|---|---|---|
| MapleStory | Not found (online play only) | — | — | — |
| MapleStory M | Online only; auto-battle draws on a time bank (120 min to start, 2 h free a day, tickets) | Kills and drops while the game runs | Continuous | [S29 · WIKI] |
| Soul Saver | Not stated | Heroes "grow endlessly" online and offline | Not verified | [S34 · OFFICIAL] |
| Legends of IdleOn | No general time cap; carry capacity is the practical cap; the App Store listing contrasts this with games that cap at 12 hours | Every character's kills or gathering | Per character, on switching to it; bonuses for claims of 8 h and more | [S35 §1.4–1.5] |
| Idle Skilling | Not found | A player's guide says the screen you leave on keeps 100% and the others about 30–35%; another page says cards need the game running (the extract did not say which page) | On visiting each screen | [S45, S46 · PLAYER] |
| Immortal Taoists | Not found | Qi and cultivation base; before Foundation I the Cultivate button runs only five minutes per tap, after it cultivation is automatic | Not verified | [S48 · OFFICIAL; S49, S50 · GUIDE] |
| Melvor Idle | 24 hours | The one skill being trained, simulated as if the game stayed open; combat only with a setting | On return | [S57 · WIKI] |
| Diablo Immortal | Not found | — | — | — |

### 2.4 Collection and completion drives

| Reference | What it does | Source |
|---|---|---|
| MapleStory | **Monster Collection**: register monsters by hunting, pages by area, a box per finished row, and a finished row sent on a timed Exploration for more; shared by a world's characters. **Legion**: every character is a piece on an account stat board | [S21, S20 · WIKI] |
| Legends of IdleOn | Cards rise to five stars with new borders; card sets tier up with the star-weighted count | [S40 · WIKI] |
| Idle Skilling | 60 pets to breed, 135 laboratory bonuses, farming cards | [S45 · OFFICIAL] |
| Melvor Idle | A Completion Log for skills and mastery; pets as rare per-action rewards; the mastery pool's checkpoints | [S58, S59, S60 · WIKI] |
| Immortal Taoists | Not found beyond pills and recipes | — |
| MapleStory M, Soul Saver, Diablo Immortal | Not found | — |

### 2.5 "One more level" pacing

| Reference | What it does | Source |
|---|---|---|
| Melvor Idle | Experience roughly doubles every 7 levels; level 92 is half the experience of level 99 | [S61 · WIKI] |
| MapleStory | Hyper Burning MAX: each level from 10 to 260 counts as five. Runes: +100% EXP for a while. Arcane dailies shrink as the player moves on, so older areas stay cheap to keep up | [S24 · OFFICIAL; S22, S16 · WIKI] |
| Immortal Taoists | A manual five-minute Cultivate until Foundation I, then automatic: early friction removed at a named milestone. A failed breakthrough raises the next chance | [S49, S50 · GUIDE; S51 · WIKI] |
| Legends of IdleOn | More characters, each working all the time; claim bonuses for longer absences | [S35] |
| Idle Skilling | Crusades: after a win, exit to raise the difficulty or replay the same level for more loot | [S47 · WIKI] |
| MapleStory M | Auto-quest and auto-battle shorten the path; a reviewer says players then "rather let the game do everything" | [S33 · GUIDE] |

### 2.6 Social loops

| Reference | What it does | Source |
|---|---|---|
| MapleStory | Guild skills from guild levels; "Noblesse" guild skills that reset each Thursday, bought with points from two weekly guild activities; up to 10 weekly mission points per character | [S26 · WIKI; S27 · OFFICIAL] |
| MapleStory M | Expedition bosses for up to 10 players | [S32 · WIKI] |
| Soul Saver | A guild with 24 guild skills | [S34 · OFFICIAL] |
| Legends of IdleOn | Guilds of up to 210; daily and weekly tasks earn guild points; members vote a "Wanted Bonus"; every member gets every bonus | [S39 · WIKI] |
| Immortal Taoists | Sects: missions, contribution, positions bought in order, each adding to mission rewards | [S53 · WIKI] |
| Diablo Immortal | Helliquary raids for eight players | [S65 · WIKI] |
| Idle Skilling, Melvor Idle | Not found (single-player) | — |

---

## 3. The references against the loops

| | Daily/weekly | Login reward | Offline gains | Collection | Pacing aids | Social |
|---|---|---|---|---|---|---|
| MapleStory | Area dailies, weekly bosses | Task-gated, 28 a month | — | Monster Collection, Legion | Burning, runes, shrinking dailies | Guild weeklies |
| MapleStory M | Dungeon entries | Time-online attendance, recoverable | Time bank, online | — | Auto-quest, auto-battle | Expedition |
| Soul Saver | — | — | Stated | — | — | Guild |
| Legends of IdleOn | Checklist, tasks, daily boss | Guild points on login | Uncapped by time | Card stars | Many characters | Guilds |
| Idle Skilling | "5–10 minutes a day" | — | Partial rates | Pets, cards, lab | Crusade difficulty choice | — |
| Immortal Taoists | Sect missions, weekly events | — | Qi and base | — | Automation at a milestone; failure raises odds | Sects |
| Melvor Idle | — | — | 24 h | Completion Log, pets, mastery | Mastery checkpoints | — |
| Diablo Immortal | Rolling bounties, weekly caps | — | — | — | — | Raids |

"—" means not found in the sources, not proven absent.

---

## 4. Jade River: what it already has, and what it lacks

Checked against `README.md`, `docs/architecture.md` and the files named.

**Already has**

- **Daily loop**: daily sect missions, replaced at each daily reset [JR: `scripts/simulation/authority/quest_authority.gd:587-615`];
  four daily activity chests at 20, 40, 60 and 100 points from capped sources (missions, dungeons, crafting,
  harvesting, sparring, the Tower, the arena, beast trials) [JR: `data/activity.json`]; the Trial Tower's daily sweep,
  county jobs, Keeping Post's daily round (`roadmap_master_ui.md` M21); a daily thief chase in two towns
  [JR: `docs/CHANGELOG.md:388`].
- **Weekly loop**: Sect Service, finished by 20 daily missions or one field boss [JR: `quest_authority.gd:590-606`];
  the Saturday auction, the weekly Beast Tide, the weekly Herb Terraces Trial (M21; `docs/CHANGELOG.md:418`).
- **Offline gains**: seclusion capped at 12 hours with no offline breakthroughs [JR: `data/curves.json` `offline_cap_h`;
  README, `rules_tests`]; Keeping Post with no time cap, the pouch being the cap, and incense sticks of 1 to 72 hours
  [JR: `docs/idle_gathering_design.md:214-220`]; garden beds and racks that grow offline; the Verdant Dew Vial, which
  banks a drop a day up to three [JR: `docs/CHANGELOG.md:1549`]; a Welcome Back page that lists the gains and says when
  the cap was reached [JR: `scripts/ui/pages/welcome_page.gd`]; the Roll-Call's "full in" time per post
  [JR: `scripts/ui/pages/posts_page.gd:68-71`].
- **Collection**: Collection pages filled by kills, with a completion event [JR:
  `scripts/simulation/authority/account_authority.gd:523-529`]; 23 achievements and 44 titles [JR:
  `data/achievements.json`, `data/titles.json`]; the Account Legacy, which records the first major breakthrough of each
  realm across characters [JR: `account_authority.gd:484-486`]; the Codex's Paths Above and Seasons tabs.
- **Pacing**: 89 realm stages, each ending in a bottleneck; the stored-Qi and progress bar along the HUD's bottom edge
  [JR: `scripts/hud.gd:1838-1843`]; breakthrough odds that pills raise.
- **Variable rewards**: equipment and rare rolls on loot tables (M32), the Fortune meter and its encounters,
  heavenly phenomena, Spirit Fruit births and Windfall on posts (`architecture.md`, authority table).
- **Single-player stand-ins for social play**: the Heaven Ranking, young masters' challenges, bonds (Dao Companion,
  sworn siblings, master), four AI companions, your own sect's disciples and the raids to defend it
  (`architecture.md`).

**Lacks**

- **A login reward of any kind**, consecutive or cumulative: none found in `data/` or the authorities.
- **Banked dailies**: missions are replaced and activity chests restart at each daily reset ("everything starts again
  at the daily reset", [JR: `account_authority.gd:533`]); only the Dew Vial banks.
- **A collection that keeps paying once complete**: a finished page emits its completion event, which refreshes the
  character's stats [JR: `scripts/simulation/authority/combat_authority.gd:12-15`], and nothing follows from it later.
- **Catch-up pacing, in part**: a character two great realms or more below the account's highest cultivates at ×1.5
  (Ancestral Guidance), and every realm in the Account Legacy adds 2% [JR:
  `scripts/simulation/authority/progression_authority.gd:111-116`]. There is no easing of older daily work and no event
  that speeds levelling. (Corrected in P2 (e): the first version of this page missed Ancestral Guidance.)
- **Visible intermediate stops on long bars** (Dao comprehension, collection pages, activity points): a UI matter,
  covered in `ui_reference_notes.md` §12.
- **Real social loops** (guild, party, trade, shared bosses): out of scope until v2.0 Online (`architecture.md`,
  "Explicitly not implemented").
- **A written retention plan** (M21): P2 (e).
