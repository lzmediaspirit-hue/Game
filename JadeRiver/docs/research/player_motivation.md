# Player motivation: why the start feels forced, and how to make it rewarding

The user's feedback, in their own words:

> "the player feels forced to play instead of enjoying"; "the first quests feel boring and the game feels monotone and
> not fun/rewarding"; "the start should feel more rewarding and progressing".

This page does five things. §1 sets out the research on why people enjoy a game and why they sometimes feel they *have*
to play it. §2 checks Jade River's first hours against that research, quoting the real quests and numbers. §3 lays out a
new first hour, minute by minute. §4 gives rules for the whole game, each with a test. §5 is a prioritised change list
that a builder can work through.

It builds on `docs/research/retention_notes.md`, which covers loops, login rewards and offline gains, and on
`docs/research/stat_scaling_research.md` §3 and §6.6, which cover gating. Where those pages already cite a finding,
this page does not repeat it; it applies the finding to the start of the game. Numbers are from `data/*.json` and
`tools/data/*.py` as of branch `claude/jade-river-game-build-pua2z2` (commit `4aa5d8b`). References in square brackets
point to the source list at the end.

---

## 0. Summary

**The diagnosis.** Jade River teaches before it rewards, and it hands out obligations before it hands out power:

- **Nothing drops for the first ~90 minutes.** Weapons unlock at Bone Forging 3, and until then *every* equipment roll
  is switched off (`no_equipment: not Unlocks.is_unlocked(c.id, "weapons")`, `world_authority.gd:595, 818, 1418,
  1717`). The only gear piece before the Weapon Hall is a Plain Straw Hat from Crab Trouble.
- **The first technique arrives at about 5 hours.** Flowing Palm is taught at Qi Kindling 1, and the pacing table sets
  `["qi_kindling_1", 5]` hours (`data/balance.json`).
- **53 unlock rows come before that technique**: 17 in the Prologue and 36 across Bone Forging (`tools/data/story.py`
  `unlocks()`). About four of them add a combat verb: guard, weapons, Plunge and the dodge dash. The rest are pages,
  buttons, crafts and timers.
- **The chores come before the power.** Daily missions ("Five a day. The board refreshes at dawn."), Keeping Post,
  a second character (A Second Path), field-boss timers and seclusion all open at Bone Forging 5–7, before the first
  technique.
- **The story stops and says "go grind".** After Fish-Gutting Fists the tracker reads "Strange Tracks · Reach Level 4
  (Bone Forging 4) · ➤ Hunt at Willow Path West". That gap is 6,400 progress, about 290 kills of Level 1–2 boarlets at
  22 progress each (`curves.json` `kill_qp`), or 48 minutes at the simulator's 6 kills a minute, fought with bare fists.
- **Luck is switched off at the start.** Fortune encounters need a meter that "fills over three hours of play"
  (`relations_authority.gd:589`). The Spirit Fruit trees are excluded from exactly the first two field rooms
  (`world.py` `fruit_trees()`). The first monsters' `rare` tables are empty (`loot_tables.json`).

**The fix, in one line:** hand out power, loot and surprise early and often; keep the lessons short and let the
player act on them at once; make every chore, timer and idle system optional, banked and later; and never let the
story stop on a grind the player cannot shorten.

**Top changes** (§5 has all of them, with files):

1. The weapon slot is open from the start. Uncle Guo's Fists First pays out the training gauntlets.
2. Weapons drop from the first monsters: the first Mudshell Crab kill is guaranteed to drop a weapon, and the valley's
   first rooms get a small equipment chance with a pity counter.
3. A first technique at Bone Forging 1 (from Lu on the boat), and a second one at the Weapon Hall.
4. Bone Forging 1–4 take a quarter of the time they take now. Bone Forging 5–9 absorb the difference, so Qi Kindling
   still lands at about 5 hours.
5. Chapter 2 opens at Bone Forging 2, not 4. The story's own fights carry the player to each floor.
6. Dailies, idle systems and second characters move after Qi Kindling 1 and become optional. Dailies bank.
7. A guaranteed lucky encounter inside the first 45 minutes, and rare tables on the first monsters.
8. Cut, merge or rewrite nine early quests (§3.3).
9. No progress lost on death before Bone Forging 5.
10. Every breakthrough shows its power gain as numbers, and some also change how the character looks.

---

## 1. The psychology

### 1.1 Self-Determination Theory: autonomy, competence, relatedness

Self-Determination Theory (SDT) says people keep doing, of their own accord, the activities that meet three needs:
**autonomy** (I chose this), **competence** (I am getting better at it, and I can see that I am) and **relatedness**
(people I care about are in it with me) [1, 2]. Ryan, Rigby and Przybylski tested this on video games. Across four
studies, the autonomy and competence players felt in a game predicted how much they enjoyed it and whether they meant
to play again. In an online sample, relatedness predicted both as well [1]. A follow-up model ties the same needs to
engagement and to *obsessive* play: when games meet the needs they feel good to play, and when players come back
because they feel they must, the play feels pressured [3].

Applied to Jade River:

- **Autonomy is lost** when a door stays shut until you open a menu, when the tracker has only one line and that line
  says "grind", and when a quest tells you to create a second character.
- **Competence is starved** when fights for the first 90 minutes use the same three-hit fist combo, no new ability
  arrives for hours, and a breakthrough does not show what it gave you.
- **Relatedness** in a single-player game comes from the NPCs. Lu, Aunt Ping, Little Dou and Shen Lian are strong and
  warm. The early quests do use them, and that is a strength to keep.

### 1.2 Flow: challenge against skill

Csikszentmihalyi's flow is the state of deep, enjoyable focus. It appears when the challenge matches the person's skill
and the goals and feedback are clear. Too hard gives anxiety; too easy gives boredom [4]. Chen applied this to games:
players differ, so a good game offers several ways to move the difficulty, preferably by the player's own choices
[5]. Two consequences for a start:

- **Skill has to grow, or the same challenge turns boring.** Punching crabs is flow for five minutes. Punching boarlets
  with the same combo for 48 minutes is not, because neither skill nor challenge is moving.
- **The player needs levers.** A new weapon, a new technique or a harder optional foe lets the player pick their own
  difficulty. In the first 90 minutes Jade River offers none of these.

### 1.3 Intrinsic against extrinsic motivation, and the overjustification effect

Intrinsic motivation means doing something because it is enjoyable in itself; extrinsic means doing it for something
separate from the activity. In Lepper, Greene and Nisbett's classic study, children who expected an award for drawing
later drew less in free time than children who got no award, or who got the same award as a surprise [6]. A
meta-analysis of 128 experiments found that expected, tangible rewards tied to doing or finishing a task reduce
free-choice intrinsic motivation. Unexpected rewards and informational feedback ("you did well") do not [7].

What this means for game design:

- **Surprise rewards are safe; contracted rewards can crowd out fun.** "Kill 5, get 40 taels" turns the fight into
  wages. The same 40 taels dropping unexpectedly from a lucky foe feels like a gift.
- **Feedback about competence is safe and it motivates.** Damage numbers going up after a breakthrough, a new combo
  string, or "your Fist Dao reached tier 1" are informational rewards.
- **Chores kill the activity they are attached to.** Paying the player to sweep three spots does not make sweeping fun.
  It teaches that sect life is a job.

### 1.4 Reward schedules: variable against fixed, and the ethics

Behavioural psychology separates **fixed-ratio** schedules (a reward every N actions) from **variable-ratio** ones
(each action has a chance). Hopson brought this into game design: fixed ratios produce a pause after each reward, then
a burst of effort until the next. Variable ratios produce steady effort, because the next action might always pay
[8]. `retention_notes.md` §1.1 covers the same point.

Variable rewards are also the core of gambling. Zendle and Cairns found, in 7,422 gamers, that spending on paid loot
boxes is linked to problem-gambling severity, and more strongly than other in-game spending [9]. Zagal, Björk and
Lewis define dark patterns as design that works against the player's interest, and give questions for spotting them
[10].

**Jade River's line** (it has no paid randomness, which keeps it clear of the worst of this):

- Random rewards stay **on top of** a steady fixed floor. The fixed quest and progress rewards alone must make good
  progress.
- Odds are **visible**, and a **pity counter** caps the dry streak.
- **No real money** buys a roll, now or later.
- The randomness serves **surprise and delight** (a rare drop, a hidden cave), never the pacing of the main path.

### 1.5 The core loop against the compulsion loop

A **core loop** is the chain of actions the player repeats because it is the game: fight, loot, grow stronger, fight
something harder. A **compulsion loop** is a chain built so the player *anticipates a reward* and feels compelled to
repeat it, whether or not the activity is enjoyable [11, 12]. Every game has a core loop; the question is whether the
loop pays off in the *activity* (competence, discovery) or only in the *anticipation* (timers, streaks, chests on
cooldowns).

Jade River's intended core loop is good: fight → loot → gear and techniques → cultivation breakthrough → new region.
For the first two hours, though, three of its five links are missing (loot, gear and techniques). What is left is
"fight → progress bar", and that reads as a grind. The idle layer (posts, dailies, snares, seclusion) then arrives
before the core loop has formed, so the first loop the player *feels* is a compulsion loop of timers and boards.

### 1.6 Loss aversion, FOMO and daily chores

Prospect theory: losses weigh more than gains of the same size [13], by a factor of about 2 (`retention_notes.md` §1.3).
**Fear of missing out** is the anxiety that others are having rewarding experiences you are missing. Przybylski and
colleagues tie it to *low* satisfaction of the SDT needs [14]. In games, FOMO is built from resets ("the board
refreshes at dawn"), streaks that break, and time-limited rewards. Players and critics call the result "chores" and
"homework" [15].

Rules that follow:

- **An absence must never cost the player anything.** A missed day should bank, not vanish.
- **A loss the player can see coming and prevent** (a guard against a telegraphed claw) teaches. A loss that arrives
  from outside (progress lost to a death in the first hour) only punishes.
- **Daily systems in a single-player, offline-first game** should be a menu of optional bonuses, not a to-do list.

### 1.7 The endowment effect and endowed progress

People value what they already own more highly: mug owners asked about twice what buyers would pay [16]. Progress that
is **given** makes people finish more: a 10-stamp car-wash card with 2 stamps already on it was completed by 34% of
customers, against 19% for a plain 8-stamp card [17]. For a start, this means:

- **Give the player something to own and look after early**: a weapon, a hat, a spirit-animal egg, a named item. They
  will value it and want to improve it.
- **Start bars partly full.** The River Token already does this (`add_progress pct_of_need=0.92`), and it works. Use
  the same idea for the first weapon's mastery, the first Dao, the first collection page and the Fortune meter.

### 1.8 The goal gradient

Effort rises as a goal gets closer. Café customers bought coffee more often as the free one neared [18]. For design,
this means **short, visible goals**. A goal 290 kills away sits on the flat, unmotivating part of the curve. Five goals
of 60 kills each, each with a payoff, keep the player on the steep part.

### 1.9 The first ten minutes: onboarding

Industry data puts most churn in the first session. About 77% of app users are gone after day one, and the problems
"start within the first 10 minutes" [19]. Hodent's onboarding guidance, from cognitive science: teach **one thing at a
time**, **by doing, in context**, **when it is needed**, and give **meaningful feedback** at once. Front-loaded
explanations of things the player cannot yet use are forgotten, and they read as busywork [20]. Lazzaro's "four keys"
research adds that curiosity ("easy fun") matters as much as mastery ("hard fun") [21]. The first minutes need
something to *wonder* about, not only something to *do*.

Jade River's Prologue follows "one thing at a time" well (`docs/tutorial_order.md`). Its weakness is "when it is
needed". It teaches the Bag, the purse, selling, buying, Quick-use, shrines and sprint before the first fight, and it
locks the doors until each lesson is done.

### 1.10 Player motivation types

Bartle's four types (achievers, explorers, socialisers, killers) came from MUD players, along two axes: acting against
interacting, and the world against the players [22]. Quantic Foundry's survey-based model is more current. It has 12
motivations in 6 pairs: Destruction and Excitement (Action), Competition and Community (Social), Challenge and Strategy
(Mastery), Completion and Power (Achievement), Fantasy and Story (Immersion), and Design and Discovery (Creativity)
[23]. It is based on 400,000+ respondents [24].

A wuxia/xianxia cultivation RPG draws mostly from **Power** (growing stronger), **Fantasy and Story** (becoming a
cultivator), **Completion** (collections, realms) and **Discovery** (secrets, hidden realms). The start serves Story
well. It serves **Power** almost not at all: no weapon, no technique and no gear for hours. That is the genre's
primary promise, and the start holds it back.

### 1.11 How idle games avoid feeling like chores

Pecorella's GDC talks on idle games describe their appeal: numbers that always go up, progress while away, and the
player choosing when to engage [25, 26]. The idle games that stay pleasant share four traits (my synthesis of
[25, 26] and `idle_gathering_research.md`):

1. **Offline gains are a gift, not a debt.** Coming back after a day gives *more*, never a penalty.
2. **Caps are long and forgiving.** A cap that fills in 2 hours forces check-ins; 12 hours or more lets people live.
3. **Active play beats idle play but never replaces it.** Idle gains are a percentage of active gains, and the story
   never waits on them.
4. **Idle systems arrive after the core loop is fun.** An idle layer on top of a good game multiplies it. An idle layer
   *instead of* one is a chore list.

Jade River has the first two (a 12-hour seclusion cap, uncapped posts, no offline breakthroughs, `curves.json`). It
breaks the fourth. Keeping Post opens at account Bone Forging 6 and asks the player to "Play someone else, then come
back to the one who kept post". So a second character is effectively asked for about three hours into the game.

---

## 2. Why Jade River feels forced: the audit

### 2.1 The first two hours as they play today

Times are estimates. The Prologue is budgeted at 0.5 hours (`balance.json` `prologue_hours`). Realm times come from
`realms.json` `accumulate_needed` (100 × target minutes per Level) and the gap is filled by kills at 22 progress each
(`curves.json`). Meditation in body stages runs at 60 × 0.3 = 18 progress a minute.

| Time | Quest (giver) | What the player does | What they get |
|---|---|---|---|
| 0–3 | **Morning Tide** (Aunt Ping) | "Pick up Herbal Tea" ×3, "Open your Bag", "Step outside"; the door stays shut until the teas and the Bag are done | Nothing (`rewards=[]`) |
| 3–4 | **A Quiet River** (auto) | Walk to Lu, who lists four chores: "Little Dou lost his kite, Old Ma needs a hand, Granny Liu has something for you, and Guo wants to see your fists. Come back when you've done all four." | Nothing |
| 4–7 | **The Runaway Kite** (Little Dou) | Ladder, roof, jump | 1 rice ball ("only a bit squashed") |
| 7–10 | **Ma's Delivery** (Old Ma) | Sell the Old Net, buy two rice balls | 10 + 30 taels |
| 10–13 | **Granny's Remedy** (Granny Liu) | Put the tea in Quick-use, drink one, pray at the shrine | 3 Herbal Teas |
| 13–16 | **Fists First** (Uncle Guo) | "Punch the training stump" ×12, "Hit the dummy after its wind-up" ×5 | 1 Herbal Tea |
| 16–17 | **A Quiet River (Return)** (auto) | Walk back to Lu to report | Nothing |
| 17–27 | **Crab Trouble** (Uncle Guo) | "Collect Crab Shells" ×5 (the loot group rolls 60% and picks shell or mud, about 30% a kill unless the quest-need boost applies), then Old Snapper | 50 taels, **Plain Straw Hat** (the only gear before minute ~95) |
| 27–30 | **Evening on the River** | Talk to Aunt Ping, then Lu | Nothing (the night begins) |
| 30–33 | **The Hollow Night** | Three villagers to the hut, hold out 60 s | Nothing (a strong story beat) |
| 33–36 | **The River Token** | Meditate 15 s, open the Cultivation page, break through | **Bone Forging 1**, River Token, codex entries |
| 36–45 | **The Willow Path** | "Hit a training stump" ×30, "Defeat Wild Boarlets" ×5 | 3 rice balls |
| 45–52 | **The Recruitment Fair** | Talk to both recruiters, choose a sect | Codex entry. **The first real choice** |
| 52–63 | **Entry Trial** | "Reach Bone Forging 2" (1,200 progress, about 10 min of fists), trial bell, Trial Puppet | Service Disciple rank, entry token |
| 63–67 | **A Disciple's Chores** (steward) | "Sweep the first/second/third spot" | 40 taels, 20 contribution, a bunk |
| 67–70 | **Fish-Gutting Fists** (Shen Lian) | Win a spar | 40 taels, 15% of a stage |
| 70–~95 | *(no quest)* | The tracker reads "Strange Tracks · Reach Level 4 (Bone Forging 4) · ➤ Hunt at Willow Path West" | Kill materials (hide, meat) and 20% coin rolls |
| ~95 | **The Weapon Hall** (Bone Forging 3) | Take a training weapon, dummy ×15, raise guard | **First weapon**, the Guard button |
| ~95–120 | *(no quest)* | Grind on to Bone Forging 4 | — |
| ~120 | **Strange Tracks** | Inspect 3 grey patches | 60 taels |

**What the first hour gives, in total:**

- 1 piece of gear (the hat).
- 1 realm step you can see (Bone Forging 1), and possibly Bone Forging 2.
- About 170 taels.
- About 9 consumables.
- 0 weapons, 0 techniques, 0 random gear drops, 0 lucky encounters.
- 1 choice (the sect), at about minute 50.

The HUD reveals a new button or page almost every quest. Those are **controls, not rewards**: a new button asks
something of the player and gives nothing back.

### 2.2 Gating: waits the player cannot act on

- **The Bone Forging 4 floor on chapter 2.** `strange_tracks` has `requires=all_of(realm("bone_forging_4"), ...)`.
  With the prologue's quests paying 0% progress (`quest_qp_pct.prologue: 0.0`) and the fists-only kill rate, the player
  is told to grind for 40–60 minutes with nothing new to do. The CHANGELOG entry "The tracker at Bone Forging 3" fixed
  where the tracker *points*, not the wait itself.
- **Doors that stay shut for menus.** Morning Tide keeps the hut door shut until three teas are picked up and the Bag
  is opened. Crab Trouble's East Gate stays shut until all four village lessons are done ("Finish helping the others
  first. Lu will tell you when."). Both are hard stops the player cannot act around.
- **The Entry Trial's "Reach Bone Forging 2".** A realm objective inside a guided quest, with nothing to do but fight
  boarlets.
- **Later floors of the same shape**: Bandits on the Road at Qi Kindling 6, Gu's Cargo at 7, Quiet Before the Storm
  at Heart Tempering 1, Shen Lian's Failure at 5, Gu's Warehouse at Spirit Awakening 8, Allies at the Wall at Heaven
  Glimpse 2 (`story.py` `main_quests()`). `stat_scaling_research.md` §3.2 already rates "main quest waiting for Levels
  when the path's own EXP falls short" as **bad**.
- **Mei Qing's Errand** (chapter 2) asks for "Copper Ore" ×3. Copper comes from mining, which opens at Bone Forging 5,
  or from Rock Beetles (Levels 4–5) at a 30% drop. It is an item gate hidden inside a fetch quest.

### 2.3 Chores and obligations before power

In unlock order (`story.py` `unlocks()`), with the realm and roughly when it is reached:

| Realm (≈ hour) | Obligation or timer that opens | Power that opens |
|---|---|---|
| Bone Forging 1 (0.6) | Mail, death now costs 10% of a stage (`stats.json` `death.progress_loss`, active once `kill_progress` is) | — |
| Bone Forging 2 (1.0) | Notice board, sect hub, "A Disciple's Chores" (sweeping) | — |
| Bone Forging 3 (1.6) | — | Weapons, Guard |
| Bone Forging 4 (2.0) | Herb gathering | Plunge |
| Bone Forging 5 (2.5) | Mining, **idle tasks: "Create a second character or set an idle task"** | Dodge dash |
| Bone Forging 6 (3.0) | **Daily missions ("Five a day. The board refreshes at dawn.")**, field-boss timers, **Keeping Post ("Play someone else, then come back")**, insect netting | — |
| Bone Forging 7 (3.5) | Offline seclusion, Qi springs | The Qi bar (but no technique to spend it on) |
| Bone Forging 8 (4.0) | Cooking, fishing | — |
| Bone Forging 9 (4.5) | Bottleneck panel | — |
| Qi Kindling 1 (5.0) | Storage, apprentice bench, pouch sewing | **First technique (Flowing Palm)**, the Dao tree |

The pattern: **seven obligation or timer systems open before the first technique.** Earning Your Keep even makes the
daily board a quest: "Finish daily missions" ×2. Its offer text is "Missions. Five a day. Hunt, gather, deliver.
Contribution buys what money can't."

### 2.4 The number of systems introduced early

17 unlock rows in the Prologue, 36 in Bone Forging, and 10 more in the first half of Qi Kindling. Most arrive with a
guided quest, which is good teaching, but the *count* matters. In 5 hours the player learns about 60 things, and about
5 of them make the character stronger in a fight. The player feels "I am being taught a game", not "I am playing one".

### 2.5 Repetition: kill-N and collect-N

The early quest objectives, in order:

- Collect 3 teas.
- Punch a stump 12 times; hit a dummy 5 times.
- Collect 5 shells.
- Hit a stump **30** times; kill 5 boarlets.
- Reach a realm.
- Sweep 3 spots.
- Hit a dummy 15 times.
- Meditate 60 s; gather 3 moss.
- Inspect 3 patches.
- Kill 5 Hollowed Boarlets.
- Bring 5 moss and 3 copper.
- Mine 5 copper; kill 5 beetles; dodge 3 pebbles.
- Kill 10 bandits.
- Kill 6 bandits.

About two-thirds of them are "do X N times". The stump objectives alone ask for 42 punches of an object that does not
fight back. Only two quests before chapter 3 have a unique set piece: the Hollow Night and the spar with Shen Lian.
Those two are the most memorable, which is not a coincidence.

### 2.6 Rewards per minute, and how often something new appears

| Measure | First hour today | Target (§3) |
|---|---|---|
| New item *kinds* obtained | ~6 (teas, rice balls, hat, shell, tail, hide) | ≥ 15 |
| Gear pieces | 1 (the hat) | ≥ 4, including 2 weapons |
| Techniques | 0 | 2 |
| Realm steps | 1–2 | 4 (Bone Forging 1–4) |
| Random or surprise rewards | coin rolls only (`rare` empty; Fortune meter 3 h) | ≥ 3 (a guaranteed first lucky encounter, a rare drop chance, hidden chests) |
| Real choices | 1 (the sect, at ~50 min) | ≥ 4 (the first weapon family, a hidden path, the sect, the second technique) |
| Longest stretch with nothing new | ~25–45 min (the Bone Forging 4 grind) | ≤ 5 min |
| Changes to how the character looks | 1 (the hat) | ≥ 3 (weapon in hand, hat, a breakthrough aura) |

### 2.7 Choice against obligation

A quest feels like a choice when the player could have done something else and picked this. It feels like an
obligation when it is the only line on the tracker and the doors are shut. For the first hour, the tracker holds one
line almost everywhere. The four village lessons are in any order, which is a small freedom, but all four are required
before the gate opens. Race to the Tower and Aunt Ping's Ladle are the only optional content in the first 30 minutes,
and both are good.

### 2.8 What works and must be kept

- The Hollow Night: a story set piece with stakes, then the River Token and a breakthrough right after.
- The endowed first breakthrough (the River Token's `add_progress pct_of_need=0.92`).
- The NPC voices (Little Dou's squashed rice ball, Guo's "Fists first. Everything else is decoration.").
- The kite's platforming, the race's title, and the ladle on the roof: small, optional and playful.
- Shen Lian's spar: a rival, a stake, a win.
- The breakthrough moments and the equip prompt (`EquipPrompt`, CHANGELOG "The equip prompt"). The presentation for
  rewards exists; there are too few rewards to present.
- No offline breakthroughs, a 12-hour offline cap, and no login streaks (`retention_notes.md` §4). The game already
  avoids the worst FOMO patterns.

---

## 3. The first hour, redesigned

### 3.1 Target curve

Rules for the curve: **a reward or a new thing every 1–3 minutes up to minute 20, every 3–5 minutes up to minute 60.**
"New" means an item kind, gear, a technique, a realm step, a new foe type, a choice, or a secret. A button counts only
when the player can use it at once for something they want.

| Min | Beat | New thing | Kind |
|---|---|---|---|
| 0 | Wake. Aunt Ping: "Lu wants you at the docks. Take a tea." The door is open. | Move, talk, 1 tea in Quick-use already (endowed) | lesson in context |
| 1 | The docks: Lu gives the four errands; the tracker lists all four, any order. **The East Gate is open.** | the tracker with four lines | choice |
| 2–4 | **Fists First** (Guo): stump ×5, dummy ×3 after the wind-up | **Guo's knuckle wraps (`training_gauntlets`), equipped: the weapon slot is open from the start**; the combo string grows by one hit | first gear, visual change |
| 4–6 | **The Runaway Kite**: ladder, roofs, jump | rice ball; **on the inn roof, a hidden chest** (a copper charm with +1% drop rate) | secret |
| 6–8 | **Ma's Delivery**: sell the net and buy one rice ball, *or* skip the buy (one objective) | 40 taels; the shop now lists training weapons | economy |
| 8–10 | **Granny's Remedy**: drink the tea from Quick-use, pray at the shrine | 3 teas; the shrine's blessing (+5% HP for 10 min, shown as a buff) | buff |
| 10–12 | Lu ("Kite, net, tea and fists") and the **Reed Shallows** | first real foes, HP bars | new place |
| 12 | **The first Mudshell Crab kill is guaranteed to drop a weapon** (`training_short_blade`, "a fisher's gutting knife"), shown with the rare beam | second weapon, **first real choice: knife or wraps** | loot, choice |
| 12–18 | **Crab Trouble**: 3 shells (a quest drop at 100% while active), Reedtail Rats | ~2% equipment chance a kill with pity (§3.4); breakables drop coins and teas | variable reward |
| 18 | **Old Snapper**. His claw is telegraphed; **Guard is taught here** ("raise your guard when it rears") | Plain Straw Hat + 50 taels + a guaranteed plain piece (boots or robe) | gear, new verb |
| 20–26 | Evening, the Hollow Night (unchanged) | story | set piece |
| 26–29 | **The River Token**: meditate 15 s, break through | **Bone Forging 1**, and **Lu teaches the first technique** (§5, change 3). The breakthrough card shows "Attack 12 → 17, HP 80 → 110" | power jump, technique |
| 29–34 | **The Willow Path** (rewritten): the stumps are optional. Five boarlets, then the **Tusked Sow** (an elite with a guaranteed drop) | Bone Forging 2 on the way (new pacing); tough meat, boar hide; a plain weapon or armour piece from the Sow | loot, realm |
| 34 | **A guaranteed lucky encounter** on the Willow Path: the "Remnant Soul in a Ring" card (existing `remnant_ring`), 3 manual pages and a line of lore | surprise | secret |
| 35–40 | Willow Path East: new foe (Mossback Toad), a Spirit Fruit tree already ripe (a one-off birth) | fruit: a permanent +1 to an attribute | discovery |
| 40–46 | **The Recruitment Fair**: two recruiters, and each hands a *taste* of the sect (Jade: a jian to try; Cloud: a staff). Choose. | sect robe (a visual change); a third weapon family | choice, visual |
| 46–50 | **Entry Trial**: the bell climb and the Trial Puppet (no realm objective) | Service Disciple rank; **Bone Forging 3** arrives on the way | realm |
| 50–54 | **Fish-Gutting Fists**: spar Shen Lian | 40 taels, and a title | rival |
| 54–58 | **The Weapon Hall** (rewritten): any family to try, and the family's **first technique** | **second technique**, weapon Dao tier 0 → 1 shown | technique |
| 58–60 | **Bone Forging 4**, reached by the story's own fights | Plunge; the next chapter opens | realm |

After the hour: Strange Tracks opens the moment the Weapon Hall is done (chapter 2 floor moved to Bone Forging 2),
and the chores (A Disciple's Chores) become an optional sect errand.

### 3.2 The progress curve behind it

Today's Bone Forging needs are 1,200 / 3,200 / 3,200 / 3,200 / … (`realms.json`). Change them to **600 / 900 / 1,200 /
1,600** for Bone Forging 1–4, and spread the difference (7,300 progress, about 73 minutes) over Bone Forging 5–9, so
`balance_sim`'s pacing row `["qi_kindling_1", 5]` still holds within ±15%.

Give the prologue and chapter 1 quests progress: `quest_qp_pct.prologue` goes from 0.0 to 0.10. The main-path kills
(boarlets, the Sow, the Trial Puppet, Shen Lian) should carry the player to each floor with no extra hunting. §4, P1
gives the test.

### 3.3 Quests to cut, merge or rewrite

| Quest | Today | Change | Why |
|---|---|---|---|
| **Morning Tide** | 3 teas, open the Bag, door shut until both are done | Cut to "Take the tea from the table". The tea starts in Quick-use. The Bag is taught when the first weapon drops (the equip prompt already opens it). Door never shut | Teach when needed (§1.9); no hard stop |
| **A Quiet River (Return)** | Walk back to Lu | Merge: when the fourth errand is done, Lu calls out from the docks ("East Gate's open"). No walk | Removes a pure errand |
| **Ma's Delivery** | Sell + buy ×2 | One objective (sell the net). Buying is optional; the shop's training weapons are the hook | Fewer steps, a reason to shop |
| **Fists First** | Stump ×12, dummy ×5; reward 1 tea | Stump ×5, dummy ×3; reward **training gauntlets, equipped** | The user's ask: the weapon slot open from the start |
| **Crab Trouble** | 5 shells at ~30%; Snapper | 3 shells, dropped at 100% while the quest is active (a `quest_drops` row, as the pirates' ledger pages have); Guard taught on Snapper; a guaranteed gear piece | Less repetition; a new verb at the moment it is needed |
| **The Willow Path** | Stump ×30, boarlets ×5 | Stumps optional (body training stays, with a counter of its own); boarlets ×5, then the Tusked Sow elite | 30 stump punches is the dullest objective in the game |
| **Entry Trial** | "Reach Bone Forging 2", bell, puppet | Drop the realm objective | A realm objective in a lesson is a grind order |
| **A Disciple's Chores** | Sweep 3 spots (main quest) | Make it a **side** errand. Rewrite it so the third spot turns up a grey-dust clue, the first hint of chapter 2, and a hidden cache | An obligation named "chores" on the main path |
| **Earning Your Keep** | Finish 2 daily missions (Bone Forging 6) | Move to Qi Kindling 1. Ask for any 1 mission; the shop opens on acceptance | Dailies as a quest are an obligation |
| **A Second Path** | "Create a second character or set an idle task" (account Bone Forging 5) | Move to after Qi Kindling 1. The idle task alone completes it; a second character is never asked for | Autonomy; no alts on the path |
| **Keeping Post** | "Play someone else, then come back" (account Bone Forging 6) | Move to after Qi Kindling 1. Completed by keeping post with *this* character and coming back after an incense stick | Same |
| **Eyes for Qi** | Meditate 60 s, 3 moss | Meditate 20 s at the glowing spot, which reveals a hidden herb patch worth picking (3 moss + 1 rare herb) | Waiting is not play |
| **Mei Qing's Errand** | 5 moss, 3 copper | 5 moss, and 3 Hollowed Boarlet hides from The Humming Token's fight | No hidden gate on mining |

### 3.4 Where the surprises go

- **The first-kill guarantee.** The first Mudshell Crab kill drops `training_short_blade`, marked once by an account
  flag (`first_weapon_drop`). The rare beam and `rare_chime` moment already exist (`moments.json`).
- **Early equipment with pity.** For the valley's first rooms (Reed Shallows, Willow Path West and East), set
  `equipment.chance` to 0.02 for normals and 0.25 for elites, with `min_quality: "flawed"`. The first three pieces a
  character gets have a pity of 15 kills (the `lost` rows already carry a `pity` field; reuse it). After the first
  hour the chance drops back to the table's 0.012.
- **Rare drops on the first monsters.** The `rare` lists for `mudshell_crab`, `reedtail_rat` and `wild_boarlet` are
  empty. Add a 1–2% "river pearl" (sells for 30 taels), a 0.5% `manual_page`, and a 0.2% cosmetic (the "jade carp
  charm" hat ornament) that shows on the character.
- **A guaranteed first fortune card.** Start the Fortune meter full for a new character (endowed), and force the
  `remnant_ring` card on the first Willow Path gather. After that the 3-hour meter applies as today.
- **A Spirit Fruit tree.** Drop the `rid not in ("lf_reed_shallows", "wp_west")` exclusion for a single scripted birth
  in Willow Path East the first time the player enters it.
- **Hidden spots.** A chest on the Ferry Inn roof (the kite route), a cache under the third sweeping spot, a ledge above
  the Reed Shallows' driftwood reached with a double jump off the second log. Each gives a unique item, not only coins.
- **Random elites.** A 1-in-40 chance that a boarlet spawns as the Tusked Sow (elite, guaranteed gear), marked with
  the existing elite marker. It gives the variable "maybe this one" of §1.4 on a fixed floor.

### 3.5 Short-term goals on screen

The tracker shows up to three lines: the story, one nearby optional goal ("A glint on the inn roof"), and one growth
goal with a short bar ("Fist Dao: 8/20 to tier 1", or "Bone Forging 3: 62%"). Goals are sized so that each line
finishes within 5 minutes during the first hour (the goal gradient, §1.8).

### 3.6 Waiting is always optional

- **No door shut for a menu lesson.** A lesson that needs a control prompts for it at the moment of use.
- **No story step waits on a realm the story does not itself deliver.** If a floor remains, the tracker offers at least
  two *different* activities that close it: a side quest, a dungeon, a spar, an elite hunt. Each shows how much of the
  gap it closes ("Tusked Sow: ~15% of the gap").
- **Timers never block.** Consolidation (60 s at Bone Forging 1, 180 s at Qi Kindling 1) runs while the player fights.
  Snares and posts run in the background, and the story never asks the player to wait for one.

---

## 4. Principles to fix "forced", with tests

Each rule has a check that a test suite can run. The suite named is where it fits best.

| # | Principle | Check |
|---|---|---|
| P1 | **The story never waits on grind.** The main path's own quests and fights reach each chapter floor | `balance_sim`: a story-only bot (main and guided quests, their kills, no extra hunting) meets every floor within 5 minutes of play (`floor_wait` 10 → 5) through chapter 3, and within 10 minutes after |
| P2 | **Something new every few minutes at the start** | `prologue_run` and `tutorial_order` record "novelty events" (a new item id, gear equipped, a technique learned, a realm step, a choice, a fortune card, a hidden chest). The gap between events is ≤ 3 min of simulated play to minute 20 and ≤ 5 min to minute 60 |
| P3 | **Power before chores** | `data_validation`: in `unlocks.json` order, no unlock tagged `obligation` (daily missions, posts, idle tasks, field-boss timers, seclusion, snares, rites) comes before the first technique, the first weapon and Bone Forging 4 |
| P4 | **Obligations are optional and bank** | `rules_tests`: skipping the daily board for 3 days, then opening it, offers 3 days of missions (a cap of 3); no main or guided quest has a `daily_mission_done` objective |
| P5 | **No alts on the path** | `data_validation`: no main or guided quest's objectives need a second character (`second_path`, `settle_post` with another character) |
| P6 | **Every quest pays something the player can feel** | `data_validation`: every prologue, main and guided quest up to chapter 2 grants at least one of: an item the player can use or wear, a technique, visible progress (≥ 10% of a stage), or a title. A codex entry alone does not count (today Morning Tide, A Quiet River, The Recruitment Fair and Two Hands Full fail this; story beats such as The Hollow Night are exempt) |
| P7 | **Early surprise exists and is honest** | `rules_tests`: a fresh character's first crab kill drops a weapon; a character with 15 kills in the first rooms has at least one equipment drop; drop odds shown on the Bestiary card match `loot_tables.json` |
| P8 | **Exploration pays** | `data_validation`: each field room in the first two regions has ≥ 1 hidden or optional reward (a chest, a secret ledge, an optional elite) outside the quest path |
| P9 | **Limited repetition** | `data_validation`: no two consecutive main-path quests are both "kill/collect/hit N"; N ≤ 5 before Bone Forging 5, and no objective asks for more than 10 hits on an object that does not fight back |
| P10 | **Choice at least every 15 minutes in the first hour** | `tutorial_order`: the walk logs the choices offered (a weapon family, the sect, a technique, a path fork, an optional quest). At least 4 by minute 60 |
| P11 | **Every breakthrough visibly adds power** | `rules_tests`: each realm step raises the par character's Combat Power by ≥ 5% before Qi Kindling (the §3.2 lesson of `stat_scaling_research.md`); the breakthrough card shows before and after for two stats; majors change the character's look (aura or robe trim) |
| P12 | **Gentle early failure** | `rules_tests`: death before Bone Forging 5 costs no progress (`death.progress_loss` applies from Bone Forging 5); the revive page says so |
| P13 | **Teach by doing, when needed** | `tutorial_order`: no door is kept shut for a menu objective; each control is taught in the step that first needs it for play (the Bag with the first gear, Guard with Old Snapper) |
| P14 | **Absence never costs** | `rules_tests`: nothing in the save loses value after 7 days away (no reset streaks, no expiring reward, no decay); the Welcome Back page lists only gains |
| P15 | **Rewards inform, not contract** | Design review (not automated): quest offer text leads with the story or the lesson, and names the payment last or not at all; surprise rewards are not announced before the fight |

---

## 5. Prioritised change list

Impact and effort are H/M/L. Effort counts data, code, art and tests. Work in this order, top to bottom. Items 1–10
are the core fix.

| # | Change | Impact | Effort | Files and systems | Test |
|---|---|---|---|---|---|
| 1 | **Weapon slot open from the start.** Move the `weapons` unlock (and `weapon_dao`) to the prologue's `attack` unlock; Fists First rewards `training_gauntlets` and equips it. Remove the `no_equipment` gate, which then never applies | H | L | `tools/data/story.py` `unlocks()` (the `weapons` and `weapon_dao` rows), `fists_first` rewards; `scripts/simulation/authority/world_authority.gd:595, 818, 900, 1418, 1717`; `economy_authority.gd:81`; `inventory_authority.gd:564`; `ui/pages/character_page.gd:187`; README line "Weapons appear only at the Weapon Hall"; `docs/tutorial_order.md` | `tutorial_order` asserts a weapon is worn by the end of Fists First |
| 2 | **Weapon drops from the first monsters, with a first-kill guarantee.** The first Mudshell Crab kill drops `training_short_blade` once (account flag); valley-start rooms get the equipment chance and pity of §3.4 | H | M | `tools/data/economy.py` (loot tables for `mudshell_crab`, `reedtail_rat`, `wild_boarlet`), `scripts/simulation/rules/loot_rules.gd` (a `first_drop` row and an equipment pity counter kept on the character), `world_authority.gd` drop call | `rules_tests`: first kill drops it; 15-kill pity; `balance_sim` drop budget (`balance.json` `drops`) still in band |
| 3 | **A first technique at Bone Forging 1** from Lu on the boat, costing no Qi (a cooldown art) so it works before the Qi bar; the Weapon Hall teaches the family's first art | H | M | `tools/data/techniques.py` (a Bone Forging row with `cost: none` and a cooldown; reuse Flowing Palm's pose and a tier-1 `vfx` block so no new animation is needed, per `AGENTS.md`); `story.py` `the_river_token` `on_accept`/rewards and `the_weapon_hall`; move `technique_slots_2` (`hud:skills`) to Bone Forging 1 | `prologue_run`: a technique is learned and cast by Bone Forging 1 |
| 4 | **A front-loaded Bone Forging curve**: 600 / 900 / 1,200 / 1,600 for Bone Forging 1–4, the rest over 5–9; `quest_qp_pct.prologue` 0.10 | H | L | `tools/data/realms.py` (`accumulate_needed`), `tools/data/stats.py` or the curves source for `quest_qp_pct`; `data/balance.json` pacing unchanged | `balance_sim` pacing ±15%; P1 check |
| 5 | **Chapter 2 opens at Bone Forging 2**; Entry Trial loses "Reach Bone Forging 2"; the story's fights carry each floor | H | L | `story.py` `strange_tracks` `requires`, `entry_trial` objectives; `stat_scaling_research.md` §6.6 table row "2 · Bone Forging 4" → 2 | P1 in `balance_sim`; `valley_run` |
| 6 | **Obligations after Qi Kindling 1, optional and banked**: move `daily_missions`, `contribution_shop`, `field_boss_timers`, `idle_tasks`, `keeping_post`, `insect_netting`, `seclusion`; rewrite Earning Your Keep, A Second Path and Keeping Post (§3.3); dailies bank up to 3 days | H | M | `story.py` `unlocks()` and the three quests; `scripts/simulation/authority/quest_authority.gd` (daily reset, lines ~587–615 per `retention_notes.md`); `account_authority.gd` (activity chests) | P3, P4, P5 |
| 7 | **Early surprises**: the Fortune meter starts full and a forced `remnant_ring` on the first Willow Path gather; a scripted Spirit Fruit birth in Willow Path East; rare rows on the first monsters; the Tusked Sow random elite | H | M | `relations_authority.gd` (`_fill_fortune`, initial meter), `tools/data/living_world.py` / `world.py` `fruit_trees()`, `tools/data/economy.py` loot `rare`, `tools/data/enemies.py` (the Sow reuses the boarlet's creature art at a larger scale and an elite tint) | P7, P8 |
| 8 | **Cut, merge and rewrite nine early quests** (§3.3): Morning Tide, A Quiet River (Return), Ma's Delivery, Crab Trouble, The Willow Path, A Disciple's Chores, Eyes for Qi, Mei Qing's Errand, plus Fists First from item 1 | H | M | `tools/data/story.py` `prologue_quests()`, `guided_quests()`, `main_quests()`; dialogue trees in `data/dialogue/`; `tests/tutorial_order.gd`, `tests/prologue_run.gd`, `docs/tutorial_order.md` | P6, P9, P13 |
| 9 | **No progress loss on death before Bone Forging 5** | M | L | `progression_authority.gd` `_on_gravely_wounded` (`death.progress_loss` from a realm floor); `ui/pages/revival_page.gd` text | P12 |
| 10 | **Breakthroughs show their power**: before and after values for Attack and HP on every realm step's card; an aura or robe-trim change at Bone Forging 1, 4 and 7 | H | M | `data/moments.json` via `tools/data/moments.py` (the breakthrough rows' text layer), `MomentView`; aura as an FX layer (no body art change) | P11 |
| 11 | **Hidden chests and ledges** in Lotus Ferry, the Reed Shallows and the Willow Path (§3.4), each with a unique item | M | M | `tools/data/world.py` (`r.chest`, surfaces), `verticality.py` reach checks; `room_sweep` | P8 |
| 12 | **Guard taught on Old Snapper** (move `guard` from Bone Forging 3 to Crab Trouble) | M | L | `story.py` `unlocks()` `guard`; Crab Trouble text | `tutorial_order` |
| 13 | **Tracker: three lines** (the story, a nearby optional goal, a growth bar) with 5-minute goals in the first hour | M | M | `scripts/hud.gd` quest tracker; `QuestAuthority._story_next` | `tutorial_order` invariant: never one line when optional content is near |
| 14 | **Floors say how to close them**: when the story waits, list two or more activities with their share of the gap | M | M | `QuestAuthority`, `ui/pages/quests_page` | P1 |
| 15 | **A sect "taste" at the fair**: each recruiter lends their family's weapon to try before choosing | M | L | `story.py` `the_recruitment_fair` `on_accept` (a `training_jian` or `training_staff`) | P10 |
| 16 | **Repetition caps on later chapters**: apply P9 to chapters 3–10 (Bandits on the Road ×10 → ×5 plus Tan's lieutenant; Quiet Before the Storm ×8 → a set piece) | M | M | `story.py` `main_quests()` | P9 over all acts |
| 17 | **Softer mid-game floors**: apply P1 to Qi Kindling 6/7, Heart Tempering 1/5, Spirit Awakening 8 and Heaven Glimpse 2 by adding story-path quests or quest progress, not by removing the floors | M | H | `story.py`, `realms.py`, `balance_sim` | P1 at all floors |
| 18 | **Informational reward language**: rewrite offer texts that lead with pay ("Five a day…", "Ten of them…") to lead with the story or the lesson | L | L | `story.py` offer strings, `ui_strings.json` | P15 review |

### Order of work

1. **Items 1, 4, 5, 9, 12.** Data-only or near it. Together they remove the no-weapon hour and the Bone Forging 4 wall.
2. **Items 2, 3, 6, 8.** The loot, technique, obligation and quest rewrites. Update `tutorial_order` and `prologue_run`
   in the same change, since both walk this exact path.
3. **Items 7, 10, 11, 13–15.** Surprise, presentation and choice.
4. **Items 16–18.** The same rules applied past the first hours.

Any new item or animation follows `AGENTS.md`. The plan above reuses existing weapon items (the training family) and
existing poses, so the first two phases need no new art.

---

## As built: items 3, 4, 5, 8 and 10

What was built from §5's items 3, 4, 5, 8 and 10, and where it differs from the plan above. Items 1–2 (the weapon slot
and early drops) and 6, 7, 9 (obligations, surprises, death) are built separately.

- **3. Techniques.** Lu teaches Flowing Palm with the first breakthrough (The River Token's reward; the skill ring and
  the Techniques page open at Bone Forging 1). The Weapon Hall, done, teaches the first art of the family in hand, from
  existing arts: jian Cloudpiercing Stroke, spear Jade Thrust, fists and gauntlets Tiger Rush, short blade Reedcutter
  Slash, staff Riverstone Sweep, bow Twin Reed Shot, sabre Mountain Cleaver, fan Gale Fan (`story.py`
  `WEAPON_HALL_ARTS`). No new art or pose: until the body has a Qi pool (Bone Forging 7) any technique costs no Qi,
  only its cooldown (`stats.json technique_cost.free_without_pool`). Each art taught plays the `technique_learned`
  moment.
- **4. Pacing.** Bone Forging 1–4 need 600 / 900 / 1,200 / 1,600; Bone Forging 5–9 3,100 each. balance_sim puts Qi
  Kindling 1 at 5.2 hours (target 5), the lessons moved to it (item 6) included. `quest_qp_pct.prologue` was left alone: prologue quests never paid progress (the
  hand-in pays only main, guided, side and daily kinds, and only once the Cultivation page is open), so the story's
  quests carry the floors instead, below.
- **5. Floors.** Chapter 2's floor is Bone Forging 2 and the Entry Trial has no realm step. The Willow Path (35% of a
  stage), the fair and the Entry Trial (20%) carry Bone Forging 1 to 2; Fish-Gutting Fists (45%) carries 2 to 3. Strange
  Tracks follows the Weapon Hall, as §3.1 has it, and starts as the mentor's note the moment the hall is done. When the
  story waits on a Level anyway, the Next entry's second line names another way (a lesson or side quest on offer, or
  meditation and body training).
- **8. Quests.** Morning Tide (auto from waking, the tea in hand, the door open), A Quiet River (Return) (merged into
  Crab Trouble), Ma's Delivery (one step), Fists First (5 and 3), Crab Trouble (3 shells at 100% while wanted, Straw
  Sandals added), The Willow Path (no stumps; Flowing Palm, 5 boarlets, the herd's elite), A Disciple's Chores (side;
  the third spot is the grey, with a cache), Eyes for Qi (20 s, a ginseng root), Mei Qing's Errand (grey hides, not
  copper). Guard stays with the Weapon Hall (§5 item 12 is not in this set); the Old Snapper lesson is unchanged.
- **10. Breakthroughs.** Every step's moment carries a card: each number that rose, before → after, with its gain. The
  character's aura follows the realm (a jade ring at Bone Forging 1, motes at 4, a Qi glow at 7, halos from Qi
  Kindling), drawn behind the avatar from plain shapes; the card names it when it changes. Screenshots in
  `docs/ui_p5/early_game/`.

**The first hour as built** (tests/tutorial_order.gd, invariant 14). Minutes are its play clock: the simulated time,
walking at a thumb's pace (150 px/s), 15 s to look round each new room, 3 s a line of dialogue: a floor for a focused
new player, not a measurement. The walk takes Guo first and ends with Strange Tracks under way.

| Min | Step | New |
|---|---|---|
| 0:21 | Wake: Morning Tide under way | Herbal Tea in hand, the door open |
| 2:05 | Fists First | Training Gauntlets, worn (items 1–2) |
| 3:07 | Race to the Tower | title Fleet-Footed |
| 3:25 | The Runaway Kite | the kite, a rice ball |
| 3:42 | Ma's Delivery | first taels, the Old Net sold |
| 5:45 | Crab Trouble: the Reed Shallows | first foe (Mudshell Crab), crab shell, the first weapon (Training Short Blade) |
| 6:10 | Old Snapper | first elite, Snapper Claw |
| 6:43 | Crab Trouble handed in | Plain Straw Hat and Straw Sandals, worn at 8:03; Reedtail Rat at 7:54 |
| 8:52 | The Hollow Night | the set piece |
| 11:27 | The River Token | **Bone Forging 1** (card and jade aura), River Token, **Flowing Palm** at 11:38 |
| 13:03 | The Willow Path | Willow Path, Wild Boarlets, tough meat; a Hemp Robe drop, willow moss, boar hide at 14:11 |
| 14:16 | Stoneford | a new town |
| 16:51 | The Recruitment Fair | **the sect chosen**, jade token |
| 17:55 | Entry Trial | Trial Puppet, entry token, **Bone Forging 2** |
| 19:06 | Fish-Gutting Fists | title River Rival; Bone Forging 2 full |
| 20:17 | A Disciple's Chores (side) | the grey under the flagstone, two spirit stone shards, contribution; **Bone Forging 3** |
| 21:01 | The Weapon Hall | training jian and spear (jian worn at 20:49); **Cloudpiercing Stroke** |
| 23:34 | Strange Tracks | the Reed Marsh, a Reed Frog |

47 new things in 29 minutes on this clock; the longest gap is 2.6 minutes (the Hollow Night to the breakthrough, and
Stoneford to the fair), and the check allows 3 to minute 20 and 5 to minute 60. Bone Forging 4 comes with chapter 2 (the Weapon Hall's share, Strange
Tracks, The Humming Token), not by minute 60 of this clock. Open point: The Humming Token's Hollowed Boarlets are
Level 7–12 (the Grey Pools' band), and the story now reaches them at Level 3–4 (at Level 4 before); valley_run plays
chapter 2 later, so no suite fights them this early.

**With the story staged** (decision 39, `docs/redesign/story_staging.md`), the top-down walk (`tests/topdown_tutorial.gd`)
also counts every staged scene's cuts on this clock. That is fifteen scenes of 10–26 s each. The same 49 new things
then come in about 30 minutes. The rewards keep their order and pacing, but the gaps are tighter. The longest gap to
minute 20 is about 2.9 minutes, from the Hollow Night to Bone Forging 1: the storm scene, Lu's boat and the
meditation fall inside it. Stoneford to the fair is 2.7 minutes. Both stay under the 3-minute rule. The scenes are
trimmed to keep them there.

---

## Sources

1. Ryan, R. M., Rigby, C. S., & Przybylski, A. (2006). The motivational pull of video games: A self-determination theory approach. *Motivation and Emotion*, 30(4), 347–363. <https://link.springer.com/article/10.1007/s11031-006-9051-8> (PDF: <https://selfdeterminationtheory.org/SDT/documents/2006_RyanRigbyPrzybylski_MandE.pdf>)
2. Center for Self-Determination Theory, overview of the theory. <https://selfdeterminationtheory.org/>
3. Przybylski, A. K., Rigby, C. S., & Ryan, R. M. (2010). A motivational model of video game engagement. *Review of General Psychology*, 14(2), 154–166. <https://selfdeterminationtheory.org/SDT/documents/2010_PrzybylskiRigbyRyan_ROGP.pdf>
4. Csikszentmihalyi's flow and the flow zone, as summarised in Chen (2007), [5].
5. Chen, J. (2007). Flow in games (and everything else). *Communications of the ACM*, 50(4), 31–34. <https://dl.acm.org/doi/10.1145/1232743.1232769> (PDF: <https://www.jenovachen.com/flowingames/p31-chen.pdf>)
6. Lepper, M. R., Greene, D., & Nisbett, R. E. (1973). Undermining children's intrinsic interest with extrinsic reward: A test of the "overjustification" hypothesis. *Journal of Personality and Social Psychology*, 28(1), 129–137. <https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Motivation/Lepper_et_al_Undermining_Childrens_Intrinsic_Interest.pdf>
7. Deci, E. L., Koestner, R., & Ryan, R. M. (1999). A meta-analytic review of experiments examining the effects of extrinsic rewards on intrinsic motivation. *Psychological Bulletin*, 125(6), 627–668. <https://home.ubalt.edu/tmitch/642/articles%20syllabus/Deci%20Koestner%20Ryan%20meta%20IM%20psy%20bull%2099.pdf>
8. Hopson, J. (2001). Behavioral game design. *Gamasutra*. <https://www.gamedeveloper.com/design/behavioral-game-design>
9. Zendle, D., & Cairns, P. (2018). Video game loot boxes are linked to problem gambling: Results of a large-scale survey. *PLOS ONE*, 13(11), e0206767. <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0206767>
10. Zagal, J. P., Björk, S., & Lewis, C. (2013). Dark patterns in the design of games. *Foundations of Digital Games 2013*. <https://www.semanticscholar.org/paper/Dark-patterns-in-the-design-of-games-Zagal-Bj%C3%B6rk/19a241378b06d868eb5f6b76027172c3aaca86f4>
11. Compulsion loop (overview and references). <https://en.wikipedia.org/wiki/Compulsion_loop>
12. Webster, D. What's the difference between a "core loop" and a "compulsion loop"? <https://medium.com/@DanlWebster/whats-the-difference-between-a-core-loop-and-a-compulsion-loop-f02d20479cc7>; and The compulsion loop explained, *Game Developer*. <https://www.gamedeveloper.com/business/the-compulsion-loop-explained>
13. Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. *Econometrica*, 47(2), 263–291. <https://www.econometricsociety.org/publications/econometrica/1979/03/01/prospect-theory-analysis-decision-under-risk>
14. Przybylski, A. K., Murayama, K., DeHaan, C. R., & Gladwell, V. (2013). Motivational, emotional, and behavioral correlates of fear of missing out. *Computers in Human Behavior*, 29(4), 1841–1848. <https://selfdeterminationtheory.org/wp-content/uploads/2014/04/2013_PrzybylskiMurayamaDeHaanGladwell_CIHB.pdf>
15. "Daily quests aren't fun, they're tedious", *PC Gamer*. <https://www.pcgamer.com/daily-quests-arent-fun-theyre-tedious/>; "Reconsidering the MMORPG daily quest", *Massively Overpowered*. <https://massivelyop.com/2016/04/14/massively-overthinking-reconsidering-the-mmorpg-daily-quest/>
16. Kahneman, D., Knetsch, J. L., & Thaler, R. H. (1990). Experimental tests of the endowment effect and the Coase theorem. *Journal of Political Economy*, 98(6), 1325–1348. <https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_et_al_1990_Experimental_tests.pdf>
17. Nunes, J. C., & Drèze, X. (2006). The endowed progress effect: How artificial advancement increases effort. *Journal of Consumer Research*, 32(4), 504–512. <https://academic.oup.com/jcr/article-abstract/32/4/504/1787425>
18. Kivetz, R., Urminsky, O., & Zheng, Y. (2006). The goal-gradient hypothesis resurrected. *Journal of Marketing Research*, 43(1), 39–58. <https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf>
19. Onboarding and first-session churn (industry, via AppsFlyer figures): "Onboarding decides your D1". <https://blog.playio.co/mobile-game-onboarding-retention>; and "First Time User Experiences in Mobile Games: An Evaluation of Usability". <https://www.researchgate.net/publication/324760906_First_Time_User_Experiences_in_Mobile_Games_An_Evaluation_of_Usability>
20. Hodent, C. (2016). The Gamer's Brain, Part 2: UX of onboarding and player engagement. GDC 2016. <https://celiahodent.com/gamers-brain-ux-onboarding/> (<https://www.gdcvault.com/play/1023231/The-Gamer-s-Brain-Part>)
21. Lazzaro, N. (2004). Why we play games: Four keys to more emotion without story. <https://www.researchgate.net/publication/248446107_Why_we_Play_Games_Four_Keys_to_More_Emotion_without_Story>
22. Bartle, R. (1996). Hearts, clubs, diamonds, spades: Players who suit MUDs. <https://www.researchgate.net/publication/247190693_Hearts_clubs_diamonds_spades_Players_who_suit_MUDs>
23. Quantic Foundry, Gamer Motivation Model. <https://quanticfoundry.com/gamer-motivation-model/> (reference PDF: <https://quanticfoundry.com/wp-content/uploads/2019/04/Gamer-Motivation-Model-Reference.pdf>)
24. Yee, N. A deep dive into the 12 motivations: Findings from 400,000+ gamers. GDC. <https://www.gdcvault.com/play/1025742/A-Deep-Dive-into-the/>
25. Pecorella, A. (2015). Idle games: The mechanics and monetization of self-playing games. GDC 2015. <https://www.gdcvault.com/play/1022065/Idle-Games-The-Mechanics-and>
26. Pecorella, A. (2016). Quest for progress: The math and design of idle games. GDC Europe 2016. <https://media.gdcvault.com/gdceurope2016/presentations/Pecorella_Anthony_Quest%20for%20Progress.pdf>

Project sources: `README.md`; `docs/tutorial_order.md`; `docs/roadmap_master_ui.md` (Master 3 and 4);
`docs/research/stat_scaling_research.md` §3.2, §5.5, §6.6; `docs/research/retention_notes.md` §1 and §4;
`docs/moments_design.md`; `docs/technique_plan.md`; `tools/data/story.py` (`unlocks()`, `prologue_quests()`,
`guided_quests()`, `main_quests()`); `tools/data/world.py` (`lf_reed_shallows`, `wp_west`, `fruit_trees()`);
`data/realms.json`, `data/curves.json`, `data/balance.json`, `data/loot_tables.json`, `data/enemies.json`,
`data/stats.json`, `data/fortune_deck.json`; `scripts/simulation/authority/world_authority.gd`,
`progression_authority.gd`, `relations_authority.gd`; `scripts/simulation/rules/progression_rules.gd`.
