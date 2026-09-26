# IdleOn idle/AFK gathering: how it works, and a spec for Jade River

Research brief for the Jade River team (Godot, offline-first, up to 12 characters where the ones you are not playing keep working).
Date of research: 2026-09-26. Target: Legends of IdleOn (LavaFlame2), current live version (game data around v1.19–1.20, "World 7").

---

## 0. Sources, method and confidence

**How this was researched.** The network sandbox blocked direct page fetches of idleon.wiki, the Fandom wiki, Reddit, Steam discussions, incendar.com, idleon.guide, digitaltq and idleontoolbox.com. Search-engine snippets from those sites were still available. The strongest evidence came from GitHub:

| Source | What it is | Why it matters |
|---|---|---|
| `Morta1/IdleonToolbox` (idleontoolbox.com source) | TypeScript "parsers" that re-implement the game's formulas from decompiled game code, plus extracted game data (`data/website-data/*.json`) | AFK-rate formula, mining efficiency, kills/hour, survivability, respawn, carry capacity, anvil, refinery, printer, traps, worship, tool/node/monster tables |
| `Corgan/idleon-research-optimizer` | JS calculator whose stat descriptors are commented against the game functions (`AFKgainrates`, `AFKgainzzALLmulti`, `SkillStats`), plus raw game lists (`customlists.js`: in-game Hints, SkillDescriptions, MapDetails, TrapBoxInfo, AnvilProductionInfo…) | Cross-checks the AFK-rate formula. In-game hint text is the developer's own description of the mechanics. |
| `Sludging/idleon-efficiency` (idleonefficiency.com source) | Captured verbatim game functions (`docs/game-snippets`), star-sign data | Checks alchemy and cooking, and star-sign AFK values |
| `s0tho/Idleon_game_datas` | Community LaTeX formula book (older, marked "might be wrong now") | EXP curves, hit-chance, food consumption |
| `TwoSpookyBoos/IdleOnAutoReviewBot` | Account-review bot with generated item data | Time-candy texts, stamp definitions |
| Web search snippets | idleon.wiki (Mining, Storage, Prayers, Skilling Efficiency, Game Mechanics AFK), Steam threads, incendar cheat-sheets, gameslikefinder guides, App Store listing | Player-facing descriptions, older values, worked examples |

**Confidence labels used below:**
- **[CODE]**: re-implemented game formula, cross-checked across two independent calculators or backed by game data. High confidence.
- **[DATA]**: read directly from extracted game data tables. High confidence.
- **[HINT]**: developer-written in-game hint or tooltip text. High confidence on behaviour, but no numbers.
- **[COMMUNITY]**: wiki, guide or forum statement. Medium confidence, and it may be out of date.
- **[INFERRED]**: my reconstruction where the exact game code was not available. Treat it as a design proposal.

---

## 1. The core AFK model

### 1.1 How a character becomes "AFK"
- Every character has an **AFK target**: the monster or resource node type of the map it was last left on. The save stores this as `AFKtarget`, and each target has an `AFKtype`. [DATA] The types are `FIGHTING`, `MINING`, `CHOPPIN`, `FISHING`, `CATCHING`, `COOKING`, `LABORATORY`, `DIVINITY`, `SPELUNKING`, `Paying_Respect` (monuments) and `Nothing` (town, which gives no AFK gains).
- In practice you walk a character to a map, stand it next to the monster spawn or the ore vein, tree, fishing spot or bug swarm, and then switch to another character or close the game. That character is now "AFK" on that target. **All characters work all the time.** The developer's in-game hint says: *"Make new characters ASAP at the main menu! ALL of your characters work all the time, so you can play on one, while the others gather materials for you!"* [HINT]
- Many maps carry both a monster and a side node: a tree or bug swarm on a fighting map, or two ore veins on a mining map (`MapAFKtargetSide`) [DATA]. Examples: Spore Meadows has Green Mushroom plus Oak Tree; Freefall Caverns has Iron plus Gold; Jar Bridge has Sandy Pot plus Flies. The target is whichever one the character is standing at or working.
- Some things are not AFK targets at all. Traps, the Anvil, the Refinery, the 3D Printer, alchemy cauldrons and worship charge run on their own timers (§6).

### 1.2 What accrues while away
| AFK type | Accrues |
|---|---|
| Fighting | Kills, which drive Class EXP (monster `ExpGiven` × EXP multi), coins, drops (materials, cards, statues, rare items), kill counts toward portal/map quotas, and kills-based sub-currencies such as DNA, spices and Death Note [CODE/HINT] |
| Mining / Choppin / Fishing / Catching | Resource items (ore, logs, fish, bugs) plus skill EXP. Side drops include leaves from trees and stamps. [HINT] |
| Cooking / Lab / Divinity / Spelunking | Skill EXP and that system's own currency |
| "AFK hours" themselves | Claimed hours are a resource of their own. They level **Shrines** on that map, count toward monuments and achievements ("Claim 2,000 / 30,000 / 111,000 hours"), and give chances for Time Candy (for example "+15% chance on 8+ hour claims" and "40% on 40+ hour claims"), egg chances ("per 10 hrs of AFK claims, up to 100 hrs"), and god bonuses ("when claiming non-candy AFK gains, also progress Refinery / 3D Printer / Cooking / Breeding / Sailing / Gaming by the AFK time") [DATA/HINT] |

### 1.3 AFK gain rate: the central multiplier
The AFK gain rate is the fraction of theoretical full-speed output that the character actually gets while away. It is computed separately for fighting and for each skill. Rates **can exceed 100%** in late game. [CODE]

**Fighting** (game function `AFKgainrates("Fighting")`, re-implemented identically by two calculators):
```
FightAFK = max(0.01, 0.40 + (FightSources + AllAFKSources) / 100) × AllAFKMulti
```
**Skills** (`AFKgainrates("Mining" | "Choppin" | "Fishing" | "Catching" | "Cooking" | "Laboratory")`):
```
SkillAFK = max(0.01, 0.50 + (SkillSources + SkillOnlyShared + AllAFKSources) / 100) × AllAFKMulti
      where SkillOnlyShared includes a flat +2 (the "2 + CardBonus(46)" term), so the effective base is 52%
AllAFKMulti = (1 + ArcaneMapBonus/100) × (1 + Equipment"%AFK_GAINS_MULTI"/100)
Divinity: fixed 1.0 (100%).  Research (W7): hard-capped at 100% and 100% while online.
```
- **Base values:** fighting **40%**, skilling **50% (+2% flat, so 52%)**. [CODE]
- **Disagreement across patches:** a 2021 Steam guide gives *"Basic 20 + 65.21 = 85.21 maximum fighting AFK gains"* (and 85.88% for Journeyman). The base was therefore 20% and the maximum around 85% in early 2021. The current code base is 40%, and the modern source list is much longer. The IdleonToolbox source contains an apparent parenthesisation slip, `((0.4 + sum)/100)`. The research-optimizer uses `0.4 + sum/100` and labels "Base 0.4". I trust the latter.
- **Floor:** 1%.
- **Skill-specific terms:** talents, bubbles, post-office boxes, cards, star signs, the bribe, gear/obol "% SKILL AFK GAIN" and a trapping-milestone bonus all add per skill (full list in §5).

### 1.4 Max AFK time: there is no general cap
- The App Store listing advertises *"unlimited idle gains, unlike most idle games that cap you at 12 hours"*. [COMMUNITY/official listing] Game content assumes very long absences:
  - A star-sign task: *"Leave one of your players AFK for an entire week, which is 168 hours! Anything more counts too!"*
  - A Cosmic Time Candy gives "5 to 500 hours".
  - An achievement: *"Claim 111,000 hours of AFK time… an entire year of all characters idling to the max"*. [DATA]
- The one explicit time cap is a **penalty**. The prayer *Unending Energy* grants +Class/Skill EXP with the curse *"Max AFK time is now 10 hours. Use with caution."* [DATA] Calculator dashboards warn when such a character has been away for more than 10 h.
- **The practical limiter is space, not time.** Per-slot carry capacity, inventory slots (§3), trap durations, worship max charge, anvil capacity and alchemy liquid caps all stop accrual. So does food running out for fighters (survivability). An early patch note, *"AFKing for 5 mins won't override your 10 hour rewards if you don't claim right away"*, is sometimes read as a 10 h cap. It describes a bug fix, not a cap.
- **Incentives for checking in anyway:** Time-Candy chances need claims of at least 8 h, 30 h or 40 h. One Masterclass bonus gives "x more AFK items when you claim 48 hrs or less". Shrine and monument progress needs claims made on the right map.

### 1.5 Claiming flow
- A character's gains are computed **when you log in on that character or switch to it**. The popup appears then. Characters you do not open keep accruing indefinitely. [COMMUNITY/HINT]
- By default, AFK **loot spawns on the ground around the character** and must be picked up. Changing maps or opening the Gem Shop destroys ground loot. Pickup ignores carry limits "in time", so surplus beyond inventory space is lost. [COMMUNITY: Steam threads]
- The popup has a **"Storage" button** that sends the claim straight to the account-wide Storage Chest. [COMMUNITY/HINT]
- QoL upgrades build on this (§8): *Straight to Storage*, the *Auto Claim AFK Gains* toggle and the *Telekinetic Storage* star talent.
- **Instant AFK:** **Time Candy** items (1 h, 2 h, 4 h, 12 h, 24 h, 72 h, plus random ones of 10 min–24 h, 20 min–12 h and 5–500 h) instantly grant that many hours of the current character's AFK gains at its current rates. [DATA] "Candy" claims are excluded from some bonuses, such as egg chances and god progress.

### 1.6 Active vs AFK
- **Active:** the character you are playing fights or gathers in real time at 100% speed. It can use the minigames (mining, choppin and fishing minigames give "Minigame Reward Multi"). An "auto" toggle lets it farm with the game open. The hint says *"You do NOT need to have this on to get AFK gains, it just allows you to farm with the game still open."* [HINT]
- **AFK:** a theoretical per-hour rate × AFK gain rate × hours. For fighting, only attack talents placed on the **attack bar** count toward AFK kill speed: *"Attack talents… affect your AFK gains! But ONLY if they're assigned in the attack bar!"* [HINT]
- Early in the game AFK is worth 40–52% of active play. Late in the game AFK exceeds 100%, so "active" becomes mostly about minigames and setup.

---

## 2. Skilling efficiency (Mining, Choppin, Fishing, Catching; notes on Trapping and Worship)

### 2.1 The per-skill stat panel (what the game shows) [DATA: `SkillDescriptions`]
- **Mining:** Mining Efficiency · Mining Speed · Multi-Ore Drop Chance · Ore Value Per Drop · EXP Multiplier · Minigame Reward Multi · *Chance To Mine Current Rock*
- **Choppin:** Choppin Efficiency · Choppin Speed · Multi-Log Drop Chance · Log Value Per Drop · EXP Multiplier · Minigame Reward Multi · *Chance To Chop Current Tree*
- **Fishing:** Fishing Efficiency · Average Catch Time · Multi-Fish Chance · Fish Value Per Drop · EXP Multiplier · Minigame Reward Multi
- **Catching:** Catching Efficiency · Catching Speed · Multi-Bug Chance · Bug Value Per Drop · EXP Multiplier · Minigame Reward Multi
- **Trapping:** Trapping Efficiency · Bonus Capture for Critters on Current Map · EXP Multiplier · Current Active Traps
- **Worship:** Worship Efficiency · Bonus Souls on This Map · Charge Speed · EXP Multiplier · Current Charge

Every gathering skill therefore uses the same five quantities:
1. **Efficiency** (vs the node's requirement), which gives the chance per action.
2. **Speed**, which gives actions per hour.
3. **Multi-drop chance**, a random extra drop that can chain.
4. **Value per drop**, a deterministic integer multiplier once efficiency passes 100%.
5. **EXP multiplier**.

### 2.2 Which stat drives which skill [HINT/CODE]
| Skill | Main stat | Tool (power) | Class that specialises |
|---|---|---|---|
| Mining | STR | Pickaxe | Warrior line |
| Choppin | WIS (*"works exactly like mining, except Efficiency is boosted by WIS"*) | Hatchet | Mage line |
| Fishing | STR | Fishing rod + bait/line "toolkit" (hidden depth bonus per spot) | Warrior line |
| Catching | AGI | Bug net | Archer line |
| Trapping | AGI | Trap box set | Archer line |
| Worship | WIS | Worship skull | Mage line |

The hint says: *"Warriors specialize in Mining, Fishing, Construction, Cooking, and Gaming. Archers in Smithing, Catching, Trapping, Breeding, and Sailing. Mages in Choppin, Alchemy, Worship, Lab, and Divinity."* [HINT] Late talents such as *Skill Strengthen / Skill Wiz / Skill Ambidexterity* make a class's main stat count more for all skills.

### 2.3 Mining Efficiency formula [CODE: IdleonToolbox `getMiningEff`, trimmed to the early/mid-game terms]
```
P       = pickaxe power
toolEff = P × (1 + ToolProficiency% × (MiningLv/10)/100) × (1 + StronkTools_bubble%/100)
base    = toolEff + 4 + P + MiningStatue + (other flat)
Eff = 12 + ( base^1.3 + (STR+1)^0.6 × (1+SkillStrengthen%) + BaseMiningStamp + AllBaseSkillEff )
         × (1 + MiningLv/200)                      ← "+0.5% efficiency per skill level"
         × (1 + (PostOffice + MaestroHand)/100)
         × (1 + (STR/100)^0.35 × (1+SkillStrengthen%))
         × GoldenFood
         × (1 + (BruteEfficiency% + gear/obol %MiningEff + 10×mastery)/100)
         × (1 + (cards + starsign + vial)/100)
         × (1 + base/100)
         × (1 + HeartyDiggy_bubble × log10(MaxHP)/100)
         × (1 + CopperCollector% × log10(CopperOreInStorage)/100)
         × AllEfficiencies        (guild, meals, prayers, family, card sets… all multiplicative groups)
```
- A worked example with a fresh character (Copper Pickaxe P=6, STR 10, Mining Lv 1, no bonuses) gives Eff ≈ **81**.
- The shape of the formula is the design lesson. The tool enters twice (^1.3 and ×(1+base/100)). The main stat enters twice (^0.6 flat and ^0.35 multiplier). Level adds +0.5% per level. There is a long product of multiplicative groups, so efficiency grows by orders of magnitude over the game.
- Several late terms scale with **log10 of how much of a resource you have stockpiled** (Copper Collector, Leaf Thief, Teleki'net'ic Logs, Invasive Species, Soooouls). Hoarding feeds efficiency.

### 2.4 Node requirement ("toughness") and level gates [DATA: monsters.json `Defence` = required efficiency]
| Ore | Req. | EXP/ore | | Tree | Req. | EXP | | Bug | Req. | EXP |
|---|---|---|---|---|---|---|---|---|---|---|
| Copper | 25 | 2 | | Oak | 10 | 2 | | Flies | 10 | 2 |
| Iron | 140 | 5 | | Birch | 40 | 6 | | Butterflies | 80 | 6 |
| Gold | 1,000 | 10 | | Jungle | 120 | 12 | | Sentient Cereal | 400 | 10 |
| Platinum | 7,500 | 30 | | Forest | 400 | 20 | | Fruitflies | 2,000 | 20 |
| Dementia | 40,000 | 55 | | Palm | 1,000 | 32 | | Mosquisnow | 7,500 | 40 |
| Void | 100,000 | 185 | | Toilet | 3,500 | 50 | | Flycicle | 15,000 | 75 |
| Lustre | 250,000 | 250 | | Stump | 10,000 | 90 | | Bumble Bee | 30,000 | 150 |
| Starfire | 1,000,000 | 500 | | Saharan Foal | 15,000 | 150 | | Fairy | 100,000 | 300 |
| Dreadlo | 5,000,000 | 850 | | Wispy | 30,000 | 275 | | Scarab | 300,000 | 550 |
| Godshard | 40,000,000 | 1,600 | | Alien | 70,000 | 500 | | Dust Mote | 2,000,000 | 1,750 |

- Fish: Small 40 (6 EXP), Medium 20,000 (50), Large 2,000,000 (1,750).
- Critters (trapping, `efficiencyReq`): Froge 35 · Crabbo 400 · Scorpie 1,500 · Mousey 3,500 · Owlio 8,000 · Pingy 15,000 · Bunny 45,000 · Dung Beat 100,000 · Honker 200,000 · Blobfish 500,000 · Tuttle 10,000,000. Shiny chance falls from 5% to 0.001%.
- Ore veins "respawn" in 120–600 s. Trees, fish and bugs are 0 (continuous).
- **Rough ladder:** each tier needs about 3–8× the efficiency of the previous one, and EXP per unit grows about 1.5–3× per tier. Higher tiers give more EXP per action but need far more efficiency. Players are advised to farm the **highest node where they are at 100%** [COMMUNITY].

**Level gates** are separate from efficiency. They sit on the map portals of mining and fishing maps, which show a Mining or Fishing level instead of a kill count (`SkillLvReqSymbol`, `MapDetails`) [DATA]:
- Tunnels Entrance (Copper) → next map needs Mining 10.
- Freefall Caverns (Iron/Gold) → 25.
- Ol' Straightaway (Plat/Dementia) → 40.
- Echoing Egress (Void/Lustre) → 50/60.
- Slip Slidy (Starfire/Dreadlo) → 60.
- Fishing spots: 15 / 30 / 30.

Trees and bugs sit on monster maps and are gated by kill-count portals. Critter types are unlocked through a questline NPC.

### 2.5 From efficiency to resources/hour
**What the game guarantees** [HINT + CODE]:
1. **Green bar = chance per action.** Chance to get a resource rises with Eff/requirement and reaches 100%.
2. **Orange bar = value per drop.** *"Ever notice how the Green bar gets replaced with an Orange bar in the AFK Info for skills? This happens once you get 100% resource chance. Every time you fill this bar, more resources drop per stack! So instead of a drop being 1 resource, it'll be 2, then 3, then 4!… 'Skill Prowess' makes it EASIER to fill up this orange bar."* Only whole numbers count: a bar between 5× and 6× gives 5× [COMMUNITY].
3. **Multi-drop chance** (Multi-Ore/Log/Fish/Bug) is a separate random roll: *"+% base multi-ore drop chance. This can trigger up to 4 times in a row per swing."* [DATA]
4. **Speed** sets actions per hour. It comes from tool "Speed" (3–10) and "% skilling speed" bonuses.
5. **EXP per action** = the node's EXP × the skill EXP multiplier.

**Exact efficiency-to-yield shape, verified in three game functions** [CODE]:
- Worship souls: `bonus = floor(100 × (Eff / (10 × Req))^0.25)` %, applied only if Eff ≥ Req.
- Laboratory/Cooking EXP: `r = Eff/(10×Req)`. If `r^(0.25+Prowess) < 1`, yield = `r^0.25`. Otherwise yield = `floor(r^(0.25+Prowess))`.
- Prowess = `min(0.10, (ProwessBubble−1)/10 + 0.001×StarSign + 0.0005×Meals)`, so the exponent runs from 0.25 to 0.35.

**Community data for mining fits the same "10 × requirement" anchor** [COMMUNITY]: *"Dementia requires 400K efficiency for a 100% hit chance"* (Dementia requirement 40,000 → 10×). A reported example is "235K vs 400K needed → 80% chance". That is 0.5875 of the 100% point, which fits `(Eff/(10·Req))^0.4` (80.8%) better than linear (58.75%) or ^0.25 (87.5%). One guide mentions a floor: "at least ~2.5% of the 100% requirement to have any chance". Older values differ (e.g., "12.5k for gold at 100%"). **The exact exponent of the green bar for gathering is not confirmed**. The anchor at 10× requirement and the floor-integer orange bar are well supported.

**Reconstructed per-hour model** [INFERRED, consistent with everything above]:
```
r            = Eff / (10 × NodeReq)
chance       = r < 1 ? max(0, r^k) : 1                          (k ≈ 0.4; 0 below ~0.025)
valuePerDrop = r ≥ 1 ? max(1, floor(r^(0.25 + Prowess))) : 1     (orange bar)
multiExpect  = 1 + m + m² + m³ + m⁴   (chained multi-drop, m = multi chance, max 4 extra)
actions/hr   = 3600 / actionTime(toolSpeed, skillSpeed%)
               (for ore veins also bounded by vein respawn, 120–600 s)
resources/hr = actions/hr × chance × valuePerDrop × multiExpect × AFKrate
EXP/hr       = actions/hr × chance × NodeEXP × EXPmulti × AFKrate
```
For the action timer, reuse the combat formula as a template: `actionTime = (1 + (10 − toolSpeed)/5) / (1 + speed%/100)` seconds. With tool speed 3 that gives 2.4 s per swing, about 1,500 swings/h. This is my adaptation. IdleOn's exact skill-speed function was not recovered.

### 2.6 Tools [DATA: items.json. "lvReq" is the skill level to equip. Speed is 2–10 on the game's IMMOBILE…WARPSPEED scale]
| Tier | Pickaxe (lv, power, spd) | Hatchet | Rod | Net | Trap set | Worship skull |
|---|---|---|---|---|---|---|
| 0 | Junk (2, 2, 3) | Old (2, 3, 3) | Wood (2, 3, 3) | Bug Net (2, 4, 4) | Cardboard (1, 4) | Wax (1, 4, 4) |
| 1 | Copper (3, 6, 3) | Copper Chopper (4, 7, 3) | Copper (4, 8, 3) | Copper Netted (4, 9, 4) | Silkskin (5, 8) | Ceramic (10, 8, 5) |
| 2 | Iron (8, 10, 4) | Iron (8, 10, 3) | Iron (9, 13, 4) | Reinforced (10, 14, 4) | Wooden (15, 13) | Horned (25, 13, 5) |
| 3 | Gold (15, 13, 4) | Golden (15, 14, 4) | Gold (15, 19, 4) | Golden (15, 20, 5) | Natural (20, 20) | Prickle (35, 20, 6) |
| 4 | Platinum (25, 16, 4, +1% eff) | Plat (20, 18, 4) | Plat (25, 25, 5) | Platinet (20, 26, 5) | Steel (30, 26) | Manifested (40, 26, 7) |
| 5 | Dementia (37, 19, 5, +2%) | Dementia Dicer (25, 23, 5) | Dementia (33, 30, 5) | Dementia (25, 31, 5) | Meaty (40, 34) | Glauss (50, 34, 7) |
| 6 | Void (45, 24, 5, +8%) | Void (30, 26, 5) | Void (40, 36, 5) | Void (30, 37, 5) | Royal (48, 45) | Luciferian (60, 45, 8) |
| 7 | Lustre (55, 30, 6, +12%) | Lustre (40, 29, 6) | Lustre (45, 43, 6) | Lustre (40, 45, 6) | Egalitarian (55, 55) | Dreadnaught (70, 55, 9) |
| 8 | Starfire (65, 35, 6, +16%) | Starfire (50, 35, 6) | Starfire (50, 50, 6) | Starfire (50, 55, 6) | Forbidden (70, 67) | Cultist (90, 63, 9) |
| 9 | Dreadlo (70, 42, 7, +20%) | Dreadlo (65, 40, 7) | Dreadlo (60, 60, 7) | Dreadlo (65, 65, 7) | Containment (85, 80, +4% AFK) | Crystal (120, 70, 10, +4% AFK) |
| 10 | Marbiglass (80, 51, 7, +25%) | Marbiglass (75, 50, 8) | Marbiglass (75, 72, 7) | Marbiglass (80, 78, 7) | Prehistoric (100, 110, +6% AFK) | Prehistoric (150, 90, 10) |
| 11 | Mollo-Gomme (100, 62, 8, +35%) | Yggdrasil (90, 62, 8) | Iliunne (90, 85, 8) | Qoxzul (95, 92, 8) | | |
| 12 | Prehistoric (110, 75, 8, +50%) | Prehistoric (100, 75, 9) | Prehistoric (100, 110, 8) | Prehistoric (105, 110, 8) | | |

- Tools also carry stat lines (STR for picks, WIS for hatchets, AGI for nets) and upgrade slots (0–8).
- There are side-grades with more slots but worse speed: Poopy Pickaxe (15, 18 power, speed 2, 6 slots) and Stinky Axe.
- **Pattern:** power grows roughly linearly (≈ +3–12 per tier), speed goes 3 → 8, and late tools add a "+% skill efficiency" line.

### 2.7 Skill level feeding efficiency
- Each skill level adds **+0.5% efficiency** (the `(1 + Lv/200)` term) [CODE/COMMUNITY].
- Skill level also gates tools, nodes and portals, and scales some talents (e.g., *Tool Proficiency*: pickaxes give +x% more power **per 10 Mining levels**).
- **Skill EXP curve** [COMMUNITY formula book, flagged "might be outdated"]: `XPtoNext(L) = floor((15 + L² + 15L) × (1.225 − min(0.164, 0.135L/(L+50)))^L − 30)`. That gives ~1.6k at L10, ~170k at L30, ~4.9M at L50 and ~3.6B at L100. Class EXP uses `(15 + L^1.9 + 11L) × (1.208 − min(0.164, 0.215L/(L+100)))^L − 15`.

### 2.8 Multi-drop, crit and double-drop style bonuses
- **Multi-Ore/Log/Fish/Bug chance:** a talent says "+% base multi-ore chance, can trigger up to 4 times in a row per swing" [DATA]. Hat and stamp lines add "% Multi Ore/Log Chance" (e.g., a `DoubleMin` stat on hats, decay 15/40). A late upgrade: "Increase the max Multi-Ore by % … for ALL resources".
- **Value per drop** (orange bar), described above.
- **Prowess** (0 to 0.10 added to the exponent) makes the orange bar easier to fill. It comes from a bubble, star sign (+2% "All Skill Prowess") and meals.
- **Claim-time lucky rolls:**
  - Bribe "Double Exp Scheme": 2.2% chance of ×2 EXP on any AFK claim.
  - Star sign: +15% chance for double EXP.
  - Talent *Reroll Pls*: chance to reroll AFK rewards, can chain.
  - "Double AFK claim chance" sources.
  - *Double AFK Gain Tickets* (an account item).

### 2.9 Soft caps and diminishing returns
- Nearly every bonus uses one of the game's standard curves [DATA: talents.json `funcX`]:
  - `add`: x1·L
  - `decay`: x1·L/(L+x2), with an asymptote at x1. Idle Brawling (20, 50) gives 10% at L50, 13.3% at L100 and 16% at L200.
  - `decayMulti`: 1 + x1·L/(L+x2)
  - `bigBase`: x1 + x2·L
  - `intervalAdd`
- **Hard clamps:** Prowess ≤ 0.10. Chance ≤ 100%. Value-per-drop is an integer (floor). The quest-based efficiency talent caps at +x%. Item stacks are clamped at 2.05 billion. Research AFK is ≤ 100%.
- Main-stat terms use sublinear exponents (^0.6, ^0.35). The shared "speed from stat" helper is `1 + 2 × (((AGI+1)^0.37 − 1)/40)` below 1,000 and switches to a saturating form above 1,000.

### 2.10 Trapping and Worship (idle gathering that is not "stand-and-swing")
- **Trapping** [DATA `TrapBoxInfo`]: place traps on critter platforms. Each trap runs for a fixed duration you choose and yields a fixed critter count and EXP, scaled by trapping efficiency and bonuses:
  - Set 0: 20 min → 1 critter / 1 EXP · 1 h → 2/2 · 8 h → 10/8 · 20 h → 20/15.
  - Set 1: adds 40 h → 35/50 and a shiny-critter chance.
  - Set 2: 3 h → 5/5 · 60 h → 50/40 · 120 h → 100/80, plus 120 h "all critters" (200/0) or "all EXP" (0/200) variants.
  - Set 3: EXP-only traps (8 h → 40 EXP … 144 h → 350).
  - Top set: up to 28 days (2,419,000 s) → 550 critters / 1,150 EXP.
  - **Short traps pay more per hour. Long traps pay more per check-in.**
  - Critters need efficiency ≥ their requirement (table above). Surplus raises "Bonus Capture". Better trap sets unlock more duration options and more simultaneous traps.
  - A Hunter talent (*Eagle Eye*) lets you "collect all" remotely. The collected amount is multiplied by the talent value with a floor of 50% (40% for EXP).
- **Worship** [CODE]:
  - Each character builds *charge* over time: `rate ≈ 6 / max(5.7 − 0.2·skullSpeed^1.3 − levelTerms, 0.57)` per hour × bonuses.
  - Max charge: `max(50, cards + stamps + bubbles·⌊Lv/10⌋ + skull tier × …)`. Charge stops at max.
  - Charge is spent to run a tower-defence "totem" (8 totems, one per world). Souls reward per run: `5 × (1 + floor(100·(Eff/(10·MinEff))^0.25)/100) × waveMulti × food`, with `waveMulti = ((5+maxWave)/10)^2.6`.
  - Worship EXP scales with best wave.
  - The design pattern is **time-gated stamina that you cash in actively**.
- **Bug nests** (catching): attacking a nest spawns a swarm and a "Destruction bonus" that raises bug yield. The nest rebuilds every 24 h, but *"you can AFK on a swarm of bugs for longer and get full rewards."* [HINT]
- **Fishing** has two special rules. Fish "bonk" you, so fishing needs HP and defence (survivability). Each spot has a hidden "Depth" bonus that interacts with bait and line "toolkit" items. [HINT/DATA]

---

## 3. Carry capacity

### 3.1 Model [HINT + CODE + COMMUNITY]
- **Carry capacity is the maximum stack size per inventory slot**, set separately for each material category and each character. The hint reads: *"Each item type has a max amount you can carry in a single inventory slot… These Max Capacities [are] character specific, which means new characters you make will start with low carry capacities!"*
- **Base stack is 10** [COMMUNITY: wiki Storage page].
- Total carrying = (number of inventory slots) × (per-slot cap for that category). Inventory bags add slots (e.g., "+4 extra item slots" per bag).
- **Categories** [DATA `CarryCapItemNames`]:
  1. Ores / Bars / Barrels
  2. Logs / Leaves
  3. Health / Boost / Golden Food
  4. Monster Parts / Smithing products ("Materials")
  5. Fish
  6. Bugs
  7. Critters / Shiny Critters
  8. Souls
- Quest items and currencies have fixed huge caps (9,999,999). Equipment stacks to 1.

### 3.2 Carry pouches (per category, per character, "use once; highest used applies") [DATA carryBags.json]
Capacity tiers: **25 · 50 · 100 · 250 · 500 · 1,000 · 2,000 · 5,000 · 10,000 · 20,000 · 25,000 · 30,000 · 35,000**. Names run Miniature → Cramped → Small → Average → Sizable → Big → Large → Massive → Volumetric → Colossal → Gargantuan → Herculean → Enormous. Critter and Soul pouches start at 50. Pouches are crafted at the Anvil or earned from quests, and are usually account-shareable items consumed per character.

### 3.3 Multipliers [CODE]
```
Cap = floor( min(2.05e9,
      (PouchBase + VaultFlat + BundleFlat)
      × (1 + CategoryStamp%/100)            e.g. Mining/Choppin/Fish/Bug/Material carry-cap stamps
      × (1 + 0.25 × GemShopCarryPurchases)  +25% per gem purchase
      × (1 + (AllCarryStamp% + StarSign%)/100)   star signs: +5% OG Skiller, +30% "Mr No Sleep" (−6% AFK)
      × (1 + ExtraBags%/100)                 materials only: 200·L/(L+100)%
      × (1 + (Guild "Rucksack" 70·L/(L+50)% + Telekinetic Storage talent%)/100)
      × (1 + Companion%/100)
      × (1 + PantheonShrine%/100)            +5% base, +1%/level, only on the shrine's map
      × max(0.4, 1 − ZergRushogenCurse%/100) prayer: +AFK rate, −carry cap
      × (1 + (RuckSack prayer% + bribe%)/100) ))
```
The Anvil's production capacity is derived from the character's Material carry cap (§6.1).

### 3.4 What happens beyond capacity
- AFK loot beyond what fits is lost. It can also be dropped on the ground and then destroyed when you change map, and pickup does not stop at the limit, so surplus "vanishes" [COMMUNITY]. **Capacity is the real AFK cap.**
- The Storage Chest is account-wide and shared by all characters. It has its own slots (chests are unlocked one by one, each once per account) and a global ceiling of about 1.05–2.05 billion per stack. Items in storage count for crafting orders in some systems (post office), but **not for smithing crafting**. The developer keeps the chest and the inventory separate on purpose, so that "Pack Mule" challenges stay meaningful [COMMUNITY].
- **Deposit paths:**
  - The "Storage" button on the AFK popup.
  - *Straight to Storage* (gem shop): the node's main resource, or the first item on a monster's table, goes straight to storage; cards and rare drops still land on the ground.
  - *Auto Claim AFK Gains* toggle: always uses "Storage", no popup.
  - *Telekinetic Storage* star talent: deposits the inventory and destroys ground items; passive +carry cap.
  - The 3D Printer auto-deposits hourly.

---

## 4. AFK fighting as gathering

### 4.1 Kills per hour [CODE: IdleonToolbox `getKillsPerHour`]
```
mobs     = number of monsters the map spawns        (MapDetails[1][0], e.g. 15 on the first field)
dist     = map walking distance                      (MapDetails[1][1], e.g. 273)
respawn  = MonsterRespawnTime / (1 + respawn%/100)   (e.g. 15 s for the first mob; 40 s late)
wait     = max(0.1, (1 + (10 − weaponSpeed)/5) / (1 + attackSpeed%/100))       seconds per attack
avgHit   = maxDmg × (mastery + (1−mastery)/2) × (1 + (critDmg−1)×critChance) × hit% × D
           D = product over AFK-flagged attack talents on the bar, × star-talent/bubble bonus
hit%     = acc/Def ≥ 0.5 ? min(100, floor(100 × (0.95 × acc/Def − 0.425))) : 0   → 100% at acc = 1.5×Def
K        = clamp(attack-talent kill factor, 1, 2.2)

killsPerSec = min( mobs / (respawn + 0.1),                                    ← spawn cap
                   K / ( dist/(130 × moveSpeed%) + wait × max((HP/avgHit + 0.52)/hit%, 1) ) )  ← player cap
KillsPerHour_theoretical = floor(3600 × killsPerSec)
FinalAFKKillsPerHour    = floor(theoretical × FightAFKRate × Survivability% × KillPerKill)
```
- **Survivability** is the share of time alive. With incoming damage per hit `max(ceil((Atk − 2.5·DEF^0.8) / max(1, 1 + DEF^1.5/100 × DEF/Atk)), 0)` against food healing, dying costs a respawn of 600 s (reducible, e.g. by the star talent *Bored to Death*). **Food is consumed while AFK**, at `dmgPerHit × 300` (World 1), 500 (W2) or 600 (W3+) per `min(foodHeal, maxHP)`. Running out of food lowers survivability.
- **Multikill** [HINT + CODE]: *"If you do 2x more damage than the max hp of a monster, you'll start Multikilling… If a monster has 1000 HP, and you deal 8000 dmg per hit, you'd be in Tier 3. If your multikill rate was 50%, you'd have 150% multikill."* So tier = floor(log2(maxDmg/HP)), shown as the **purple bar** in AFK Info. From World 7 the base is 5 instead of 2 (diminished). *KillPerKill* also adds sources like "each kill counts double".
- **Worked example** (Green Mushroom, HP 32, respawn 15 s, 15 mobs):
  - Spawn cap ≈ 3,576 kills/h.
  - A one-shotting starter (weapon speed 4 → 2.2 s/attack, 2.1 s walking) manages ≈ 830 kills/h theoretical.
  - At 40% AFK rate and 100% survivability, that is ≈ **335 kills/h** while away.

### 4.2 Drops and conversion to AFK loot
- Each AFK kill rolls the monster's drop table × the character's Drop Rate. Example, Green Mushroom: coins 50% × 5, Spore Cap 22%, plus cards and rare drops.
- Materials are multiplied by multikill.
- Class EXP per kill = the monster's EXP × the class EXP multi (e.g., Green Mushroom 2, Frog 10, Gigafrog 95, Mamooth 1,030, late mobs 90k+).
- A bribe "×2 EXP on 2.2% of claims" and similar rolls apply at claim time.
- AFK Info also lists rare-item tables ("Check AFK Info to see what Tempest Items can be found") and elemental weaknesses.

### 4.3 Monster-kill portals and quotas [DATA mapPortals]
- Maps chain through portals that open after N kills of that map's monster.
- Quotas from the game data table: 21 and 25 on the first fields, then 40–150, then hundreds, thousands (2,000–5,000), tens of thousands (20,000–50,000), and eventually millions in the late worlds (3.2M, 70M, 250M).
- Mining and fishing maps use a skill level instead (§2.4).
- AFK kills count toward quotas. Kill counts also feed *Death Note* (multikill), Barbarian "Zow/Chow" kill milestones and DNA splicing ("amount of DNA… based on the number of kills you got while AFK").

---

## 5. The bonus web (categories and typical magnitudes)

### 5.1 AFK-gain-rate sources [CODE/DATA]
| Category | Examples | Typical size |
|---|---|---|
| Base | fighting / skill | 40% / 52% |
| Class talents | *Idle Brawling / Idle Casting / Idle Shooting* (fight, 20·L/(L+50)); *Idle Skilling / Active AFK'er* (skills, 20·L/(L+40)); *Sleepin' on the Job* (Beginner, fight 21·L/(L+50)); single-skill talents (Catching Some ZZZ's fishing, Sunset on the Hives catching, Waiting to Cool cooking, 20·L/(L+60)) | +10–17% each |
| Star talents (account-level talent tree) | *Tick Tock* (both, 8·L/(L+50)); *Rando Event Looty* (+0.75%/rare event item) | +4–6% |
| Bribes (one-time coin purchases) | +5% fight AFK; skill AFK bribe | +2–5% |
| Star signs | Silly Snoozer +2% fight, Big Comatose +2% skill, OG Skiller +1% skill, Forsaken +6% fight (−80% HP), Mr No Sleep −6% AFK (+30% carry), majors +4% | ±2–6% |
| Prayers (boon + curse) | Zerg Rushogen +AFK% / −carry cap | +5–12% |
| Shrines (placed on a map, levelled by AFK hours there) | Primordial Shrine +1% +0.1%/level on that map | +1–5% |
| Guild | REM Fighting 10·L/(L+50) fight; Sleepy Skiller (skill) | +5% |
| Cards (collected monster cards, equipped or passive) | "+% Skill AFK", "+% Fight AFK", "All AFK (Passive)", card-set bonuses | +1–10% |
| Gear and obols | "% ALL AFK GAIN", "% SKILL AFK GAIN", "% FIGHT AFK GAIN", "% FISH/CATCH AFK GAIN", late "% AFK GAINS MULTI" (multiplicative) | +2–8% each |
| Alchemy bubbles (per skill) | Dream of Ironfish (mining + fishing), Tree Sleeper (choppin), Fly in Mind (catching) | +10–30% late |
| Post-office boxes (per character) | Dwarven Supplies (mining), Taped Up Timber, Sealed Fishheads, Bug Hunting Supplies, Civil War Memory Box (fight) | +5–20% |
| Tasks, merits, arcade, dungeons, divinity (+30% major), companions, voting, golden food, vault, event shop (+20%), bundle (+30%), sigils, lab chips, trapping milestone | many small account-wide sources | +1–30% each |
| Multiplicative layer | "AFK Gains Multi" gear; map-specific arcane bonus | ×1.0–1.5 |

**Rough totals:** a new character has 40% / 52%. A mid-game focused AFK character reaches about 80–120%. Late game is well above 100%, and the old 2021 ceiling was around 85%.

### 5.2 Efficiency sources
| Category | Examples | Size |
|---|---|---|
| Tool power | pickaxe 2 → 75 | dominant early (enters as ^1.3 and ×(1+base/100)) |
| Main stat | STR/WIS/AGI via ^0.6 flat + ^0.35 multiplier; talents make the stat count more | dominant mid |
| Skill level | +0.5% per level; Tool Proficiency per 10 levels | |
| Stamps (account-wide, levelled with coins and materials; "UNDERLEVELED" if the character is too low) | Base Mining/Choppin eff, All-Skill eff, carry-cap stamps | flat and % |
| Statues (collected, levelled by depositing copies) | Mining/Lumberbob/Oceanman/Ol' Reliable/Box/Twosoul statues +0.3 power per level | flat |
| Alchemy bubbles and vials | Stronk Tools (tool power %), Hearty Diggy (×log MaxHP), Prowesessary (prowess), vials +% eff | large late |
| Cards and card sets | "+% Total Mining Efficiency" | +x% per star |
| Talents | Brute/Smart/Elusive Efficiency (all skills), Copper Collector / Leaf Thief (per log10 stock), Big Pick (active swing +150%) | |
| Guild, prayers, meals, family bonuses, golden food, post office | Multi Tool +15% eff; Skilled Dimwit (+eff, −EXP) | multiplicative groups |

---

## 6. Adjacent idle production systems

### 6.1 Anvil (Smithing "Produce" tab) [CODE/DATA]
- **Loop:** each character has its own anvil. It assigns **hammers** (1 at first, up to 3) to smithing components: Thread, Trusty Nails, Boring Brick, Chain Link, Leather Hide, Pinion Spur, Lugi Bracket, Purple Screw, Thingymabob, Tangled Cords, Pristine Cords and 3 late items.
- Production is free (no input) and runs offline. Items accumulate until **capacity**, then stop.
- **Numbers per product** (progress required, Smithing Lv req, EXP):
  - Thread 100 / 1 / 6
  - Nails 200 / 5 / 10
  - Brick 350 / 12 / 16
  - Chain 700 / 17 / 25
  - Hide 1,200 / 25 / 35
  - Spur 2,000 / 30 / 50
  - Bracket 3,000 / 35 / 65
  - Screw 4,000 / 43 / 75
  - Thingymabob 6,000 / 50 / 90
  - Tangled Cords 8,500 / 60 / 110
  - Pristine Cords 12,000 / 70 / 140
- **Rates:**
  - `items/hour per hammer = 3600 × SpeedMulti / progressRequired`. With no bonuses that is 36 Thread/h.
  - `SpeedMulti = (1 + (stamp + 2×SpeedPoints)/100) × (1 + (PO box + statue + vault)/100) × (1 + bubble/100) × AgilitySpeedBonus × (1 + town-speed%/100)`.
  - `Capacity = round(min(2e9, MaterialCarryCapPerSlot × (2 + 0.1 × CapPoints)))`.
  - EXP multi: `(1 + 3×ExpPoints/100) × SmithingEXP`, which soft-caps at 20 and then asymptotes to 75.
- **Anvil points:** +1 per Smithing level, plus points bought with coins (cost `(n³+50)(1+n/100)`, up to 600) and with monster materials (cost `(n+1)^1.5 + n` of a material that changes along a ladder: Spore Cap → Frog Leg → Bean Slices → …). Points are spent on **EXP / Speed / Capacity**.
- **Player decisions:** which components to make, how to split points between speed, capacity and EXP, and how often to collect before hitting the cap. Players claim via the Anvil or "Quick Ref".

### 6.2 3D Printer (World 3, Construction building) [HINT/CODE]
- **Loop:** a star talent (*Printer Sampling*, 10% + 0.075%/level) lets a character "sample" **a % of its current AFK gains** of the resource it is standing on. The sample is stored in the printer: 5 stored slots and 2 printing slots per character.
- **Every hour the printer auto-adds the printed amount to Storage, offline, "all day every day."**
- **Sample rate** = sum of about 15 sources (talent, salt lick, gear, bubble, stamp, prayer *Royal Sampler* with its −EXP curse, merits capped at +5, family, arcade, post office).
- **Print multi** is ×2 if the character is connected in the Lab and ×3 with the Harriep god link, among others.
- **Decisions:** when to resample (after your AFK rates improve), which resource to lock in, and which prayer trade-off to accept.
- Why it matters: it turns a snapshot of a character's gathering rate into a permanent passive income, **freeing that character to do something else**.

### 6.3 Refinery (World 3) [CODE/HINT]
- **Loop:** salt slots (Redox, Explosive, Spontaneity, Dioxide, Purple, Nullo, then later salts) are toggled ON.
- Each cycle, every ON slot consumes its recipe from Storage and produces "power". Recipes are monster parts, ores, logs, fish, bugs, critters and souls, and higher salts need lower salts. Cost per cycle is `floor(rank^1.5) × qty` (^1.3 for salt inputs once a merit is bought).
- Pressing **Refine** converts power into salts. Refining at max power ranks the slot up, which raises both cost and power.
- **Cycle times:** Combustion (salts 1–3) **900 s**; Synthesis (4–6) **3,600 s**; Polymerize (7+) **360,000 s (100 h)**. All are divided by (1 + speed bonuses) × lab ×3 × legend.
- Power per cycle: `floor(min(250,000, rank^1.3))`. Squire-class talents add instant cycles on cooldown.
- **Decisions:** which slots to run, keeping enough input stock in Storage so cycles don't stall, and when to rank up. Salts feed Construction building upgrades and cog-related costs. **The refinery is the main sink that turns AFK gathering into progression.**

### 6.4 Alchemy (World 2) [DATA/CODE]
- **Four bubble cauldrons:** Power (orange/STR), Quicc (green/AGI), High-IQ (purple/WIS), Kazam (yellow/all).
- Characters are **assigned to a cauldron** and contribute brew speed from their Alchemy level and WIS. Brewing progress unlocks new bubbles in order and gives Alchemy EXP.
- **Bubble levelling costs items + liquid.** Example: *Roid Ragin* costs Copper Ore ×baseCost and Liquid1 ×2, rising per level. Bubbles use the decay/add curves.
- **Four liquid cauldrons** (Water Droplets, Liquid N2, Trench Seawater, Toxic Mercury) regenerate liquid per hour up to a cap. Both cap and rate are upgradable ("decant cap/rate").
- **Vials** are rolled or unlocked and levelled by paying a gathered item plus liquid (level 2: 100 items + 3 liquid; level 3: 1,000 + 6; level 4: 2,500 + 9; level 5: 10,000 + 12…). They give account-wide bonuses such as "+% Mining Eff" and "+% carry".
- **Sigils and P2W upgrades** also cost liquid.
- **Decisions:** who brews where, and which bubbles and vials to feed with gathered stock. **This is the biggest "consumer" of bulk gathered resources**: ores, logs, fish and bugs by the million.

### 6.5 Trapping timers
See §2.10. Traps are placed actively, run for a chosen 20 min – 28 day duration, and are collected on return (or remotely with a talent).

### 6.6 Construction and cogs (World 3) [HINT/CODE]
- **Two phases per building:** first "Build" with Build Rate, then "Upgrade" with resources and salts.
- Characters assigned to the construction board provide Build Rate: `floor(3 × (ConsLv/2 + 0.7)^1.6 × (1 + ConsLv×bubble/100) × (1 + (stamps + 0.25×PO + guild + gear + achievements + mastery + vial)/100) × …)`.
- Construction EXP/h = `ceil((BuildRate^0.7/2 + 2 + 6×ConsLv) × (1 + bonuses/100))`.
- **Cogs** placed on a board add build rate and multiply neighbours. Flags speed up cog production.
- **Buildings:** the top row holds utilities (3D Printer, Talent Library, …), the middle row wizard towers (needed for Worship), and the bottom row **Shrines** (placeable on any map, levelled by AFK claims there; moving a shrine loses progress to the next level).

### 6.7 Sailing and Farming (brief)
- **Sailing:** boats on timed voyages to islands; artifacts and loot are claimed on return. Sailing progress can also be granted by AFK claims through god, talent and golden-food chances.
- **Farming:** crops grow on timers with evolution chances. It is account-level ("Farming Lv and EXP shared between all characters"). The decisions are what to plant and when to harvest for evolution vs volume.

---

## 7. Multi-character design

- **Characters:** IdleOn has had a 10-character account for most of its life. Extra slots are gated by account progress; the game list `NewCharLvReq` = [0, 8, 30, 70, 150, 300, 500, 750, 1100, 1500, 5000] looks like total-level thresholds per extra slot (my interpretation).
- **All characters gather simultaneously**, each on one target. The game's own tip is to make characters ASAP.
- **Why players spread characters across skills:**
  1. Each character has one AFK target, so one character equals one resource stream.
  2. Classes specialise: each class line has +efficiency, +AFK talents and main-stat affinity for 5 skills. Late-game classes add account-wide boosts, such as a Maestro "right hand" that gives +efficiency to lower-level characters and family bonuses from the highest-level member of a class.
  3. Many account systems need a *specific* character stationed somewhere: cauldron brewers, the construction builder, a worship charger, a trapper, a Lab-connected character, a divinity link, shrine-map campers.
  4. Per-character caps: carry capacity, anvil and post-office boxes are per character, so parallel characters multiply throughput.
- **Account-wide vs per-character:**

| Account-wide | Per-character |
|---|---|
| Storage Chest, obols inventory | Class level, talents, skill levels |
| Stamps (with "UNDERLEVELED" damping for weak characters), statues, cards | Carry capacity, inventory bags |
| Alchemy bubbles and vials | Anvil |
| Guild, tasks (*"Everything you do with tasks is shared between all your characters"*) | Post-office box upgrades, star signs equipped |
| Refinery, printer storage, shrines | Equipment and tools, AFK target, prayers equipped |
| Breeding, sailing, gaming, farming, research levels | Portal/kill progress |

- **Playstyle this creates:**
  - Log in once or twice a day, or every few hours when active.
  - Cycle through every character: each switch triggers its AFK claim popup. Deposit loot, re-equip, retarget if a better node is now at 100%, restart traps, spend worship charge.
  - Then feed the account systems: bubbles, vials, refinery inputs, anvil collection.
  - "AFK optimisation" means pushing each character's AFK rate, efficiency tier and carry capacity so that check-ins can be rarer without losing loot.
- The World 4 Lab and later systems let players "deactivate" characters for bonuses, and calculator sites exist to answer "which character should sit where". This is heavy optimisation gameplay.

---

## 8. UX

- **Return flow:** open the game → choose a character → **"AFK Gains" popup** for that character.
  - It shows time away, Class and Skill EXP gained (with level-ups), and items gained as icons with counts. Double-EXP or reroll procs are announced: *"You'll know this happens because it literally tells you it happened!"*
  - Buttons: **Storage** (send everything to the chest) or claim/close (loot drops around the character).
  - Switch to the next character and repeat.
- **AFK Info** (Menu → AFK Info) shows current rates for the active target:
  - **Skills:** efficiency bar (green = chance to 100%, then orange = multi-per-drop progress), resources/h, EXP/h, and the stat panel lines (§2.1).
  - **Fighting:** kills/h, AFK gain rate, survivability, the **purple Multikill damage-tier bar**, drop list including rare tables, and elemental weakness.
  - For some systems it shows the hourly rate used by candy ("based on the current hourly rate shown in AFK info").
- **On the map:** nodes show their Lv or efficiency requirement, and portals show the kill count or skill level needed.
- **QoL features:**
  - Auto Claim AFK Gains toggle (auto-Storage, no popup).
  - Straight to Storage (gem shop).
  - Telekinetic Storage star talent (deposit all and clean the ground).
  - **Quick Ref** menu: remote access to account systems, e.g. claiming cogs and anvil items without walking there.
  - Time Candy (instant hours).
  - Remote "Collect All" for traps (talent).
  - Printer auto-deposit.
  - Fast sailing-chest opening.
  - Automatic guild GP claiming.
  - Gem-shop "Auto Claim EZ Access" for daily keys and tickets.
  - Calculators outside the game (Toolbox, Idleon Efficiency) exist because the game exposes rates per character only.

---

## 9. Mapping to Jade River

All names below are original. "Keep" means keep the IdleOn number as the default. "Adapt" means change it and why.

### 9.1 Core idle model

| IdleOn mechanic | Jade River equivalent | Numbers / notes |
|---|---|---|
| AFK state (character left at a target) | **Still-Heart Seclusion**: a disciple left at a node or battlefield "enters seclusion". Each disciple has one *Seclusion Focus* (a node or beast lair). | Keep: one focus per disciple; town = no focus. |
| AFK gain rate (fight / skill) | **Seclusion Yield**, split into *Martial Yield* and *Craft Yield* | Keep base **40% Martial / 52% Craft**, floor 1%. Additive % sources, then one multiplicative *Deep Seclusion* layer. It can exceed 100% late. |
| Max AFK time | **No hard time cap** (faithful to IdleOn). The real cap is pouch space (§9.3). Optional *Qi-Deviation Vow* curse: "seclusion ends after 10 h" in exchange for +EXP. | If you want a soft cap, add a **Seclusion Chamber** upgrade line: base 24 h, extendable to 168 h. Present it as "chamber incense burns out" and keep it generous. Adapt only if playtests show players dislike unbounded absence. |
| Claim on switch or login | **Emergence**: when you select a disciple, its *Emergence Ledger* popup settles all hours since last focus. | Keep per-disciple claiming, and add account-level "settle all" (§9.8). |
| Time Candy | **Hour-Incense sticks**: burn 1, 2, 4, 12, 24 or 72 h; *Wandering Incense* gives random 5–500 h (median about 24 h) | Keep the durations. Make "incense" claims exempt from shrine or egg-style hour bonuses, as IdleOn does. |
| AFK hours as a currency | **Seclusion Hours**: they level *Formation Flags* on the map (see Shrines) and count toward sect achievements. They also give chance-based rewards on long claims (≥ 8 h, ≥ 30 h, ≥ 40 h) and a "claim ≤ 48 h → ×bonus" late perk to reward check-ins. | Keep |

### 9.2 Gathering crafts

| IdleOn | Jade River craft | Efficiency stat | Tool | Node "toughness" |
|---|---|---|---|---|
| Mining (STR) | **Vein Delving**: spirit-ore veins | *Delving Finesse* | **Vein Chisel** | *Vein Obduracy* |
| Choppin (WIS) | **Herb & Spirit-Wood Gathering** | *Gathering Finesse* | **Jade Sickle** | *Root Tenacity* |
| Fishing (STR, hidden depth, fish "bonk") | **River Angling** on the Jade River | *Angling Finesse* | **Reed Rod** + *Lure & Line* kit (hidden *Current Depth* per spot) | *Current Strength* |
| Catching (AGI, bug-nest swarms) | **Spirit-Insect Netting**: firefly and cicada swarms; "stir the hive" gives a *Swarm Fervour* bonus, and the hive rebuilds every 24 h | *Netting Finesse* | **Silk Net** | *Swarm Elusiveness* |
| Trapping (timed traps, critters) | **Beast Snaring**: spirit-beast snares | *Snaring Finesse* | **Snare Kit** tiers | *Beast Wariness* |
| Worship (charge → tower-defence → souls) | **Ancestral Rites**: *Incense Qi* charges over time, then is spent defending an ancestral altar for *Spirit Wisps* | *Rite Finesse* | **Ancestor Tablet** | — |

- **Stat affinity** (keep the three-way split): Body disciples (STR) → Delving and Angling; Swift (AGI) → Netting and Snaring; Mind (WIS) → Gathering and Rites.
- **Efficiency formula (keep the shape and constants):**
  `Finesse = 12 + (base^1.3 + (Stat+1)^0.6 + flat) × (1 + Lv/200) × (1 + (Stat/100)^0.35) × (1 + base/100) × Π(1 + group%/100)`, where `base = 2×ToolPower + 4 + steles`.
  - Keep +0.5% per craft level.
  - Keep the "log10 of stockpile" talents: *"Hoarder's Insight: +x% Delving Finesse per power of 10 spirit ore in the Treasury"*.
- **Node ladder (keep the requirements, rename):**
  - 10 ore tiers at 25 / 140 / 1k / 7.5k / 40k / 100k / 250k / 1M / 5M / 40M, with EXP 2 / 5 / 10 / 30 / 55 / 185 / 250 / 500 / 850 / 1,600. Example names: Cinnabar Seam, Iron-Bone Ore, Sun-Gold Vein, White-Jade Lode, Dream-Silt Ore, Void-Mica, Moonlustre, Star-Ember, Dread-Obsidian, Heaven-Shard.
  - Trees, bugs and critters use their tables as given in §2.4.
  - Gate deeper maps with **craft-level gates** (Delving 10 / 25 / 40 / 50 / 60).
- **Yield per action** (one formula for all crafts, in the IdleOn shape):
  - `r = Finesse/(10×Req)`
  - `chance = min(1, r^0.4)` (0 below r = 0.025)
  - **Abundance** (orange bar): `valuePerDrop = r ≥ 1 ? floor(r^(0.25+Flow)) : 1`
  - *Flow* (≙ prowess) is capped at 0.10.
  - **Echo Strike** (≙ multi-ore) chance chains up to 4 extra drops.
  - Show a green → gold bar in the UI.
  - Adapt the exponent `0.4` if the green bar should feel more generous. It is the least-certain constant.
- **Speed:** `actionTime = (1 + (10 − toolSpeed)/5)/(1 + craftSpeed%/100)`. Tools have speed 3–10. Ore veins also have a regrowth timer of 120–600 s.
- **Tools:** keep the §2.6 power and speed ladders (e.g., chisel tiers 2, 6, 10, 13, 16, 19, 24, 30, 35, 42, 51, 62, 75) with late "+% Finesse" lines. Keep the stat affinity per tool (chisel +STR, sickle +WIS, net +AGI).
- **Snaring:** keep the snare durations and yields (20 min → 1, 1 h → 2, 8 h → 10, 20 h → 20; a later kit adds 40 h → 35 and a "radiant beast" chance; a later kit offers "all beasts" or "all insight" variants; top kit 28 days → 550). Keep the rule that **short snares pay more per hour and long snares pay more per visit**. A *Hunter's Recall* technique collects remotely at 50% minimum.
- **Rites:** keep charge/hour ≈ 6/max(5.7 − 0.2·tabletSpeed^1.3 − lvTerms, 0.57), max charge ≥ 50, and wisps = `5 × (1 + floor(100·(F/(10·Req))^0.25)/100) × ((5+wave)/10)^2.6`.

### 9.3 Carry capacity

| IdleOn | Jade River |
|---|---|
| Per-slot stack cap per category, per character; base 10 | **Mustard-Seed Pouches** (spatial pouches): each category has a per-slot capacity per disciple, base 10. Keep. |
| Pouch tiers 25 → 35,000 | Keep the tiers: 25 · 50 · 100 · 250 · 500 · 1k · 2k · 5k · 10k · 20k · 25k · 30k · 35k. Name the steps Thimble, Palm, Sleeve, Satchel, Gourd, Chest-Gourd, Cavern-Gourd… One series per category: *Ore Gourd, Herb Satchel, River Creel, Insect Jar, Beast Cage-Pouch, Provision Sack, Artisan Satchel, Wisp Lantern*. Consumed once per disciple; highest applies. |
| Categories | Ore/ingots · herbs/wood/leaves · provisions (food) · beast parts/artisan components · fish · insects · spirit beasts · wisps (souls) |
| Multipliers | Keep the product formula (§3.3) with renamed sources: carry **Seal Scripts**, *Sect Alliance "Deep Pockets"* 70·L/(L+50)%, *Storehouse Flag* on a map, *Vow of the Burdened* (+yield / −capacity, floor ×0.4). Hard cap 2.05B. |
| Overflow lost; chest separate | **Sect Treasury** (account-wide). Overflow policy is the big lever. **Recommendation (Adapt):** do not destroy overflow silently. Mirror IdleOn's tension by *capping accrual at capacity* and showing a "pouch full at 7h12m" warning in the ledger. Losing loot to ground-despawn is a mobile-hostile quirk. |
| Straight to Storage / Auto-claim / Telekinetic Storage | **Treasury Seal** (main resource goes directly to the Treasury), *Auto-Settle* toggle, and a late technique *Sleeve of Heaven and Earth* (deposit all + passive capacity) |

### 9.4 Martial seclusion (AFK fighting)

| IdleOn | Jade River |
|---|---|
| Kills/h formula (§4.1) | **Demon-Quelling Vigil**. Keep the formula: spawn cap `lairSize/(respawn+0.1)` vs player cap `K/(walk/(130·move%) + attackWait × max((HP/avgHit+0.52)/hit%, 1))`, then × Martial Yield × Survivability × Sweep. |
| Hit chance 0.95·acc/def − 0.425 | Keep: 100% at accuracy = 1.5× beast *Guard*. Below 0.5×, no hits. |
| Food consumed, survivability, 600 s respawn | Keep: **Provisions** eaten during vigil (×300 / ×500 / ×600 by region). *Meridian Recovery* 600 s after defeat. |
| Only attack-bar skills count while AFK | Keep: *"only techniques placed on the Stance Bar fight during seclusion"*. It is a good build decision. |
| Multikill tiers (log2 of dmg/HP) | **Sweeping Blade tiers**: tier = floor(log2(maxDmg/HP)), shown as a violet bar. Keep. |
| Portal kill quotas | **Mountain-Gate Seals**: slay N beasts to break the seal (21 → 25 → 40 → 150 → 2k → 5k → 20k+). Keep the curve. Delving and Angling gates use craft level. |
| Drops × drop rate, cards | *Fortune* stat. **Bestiary Scrolls** (≙ cards) drop from beasts and give passive bonuses. |

### 9.5 Bonus web (renamed categories; keep the decay curves `x1·L/(L+x2)`)

| IdleOn | Jade River |
|---|---|
| Talents / star talents | **Techniques** / **Heavenly Techniques**. Idle-Brawling-type techniques are *Sleeping Sword Intent* (fight) and *Dreaming Artisan* (craft), each 20·L/(L+50). *Tick-Tock* becomes *Water-Clock Meditation* (8·L/(L+50), both). |
| Stamps | **Seal Scripts**: account-wide carved seals, levelled with silver and materials, damped when a disciple is under-levelled |
| Statues | **Guardian Steles**: +0.3 tool power per level per craft |
| Alchemy bubbles / vials / liquids | **Pill Recipes** in four **Pill Cauldrons** (Body / Swift / Mind / Mystic); **Tinctures**; four **Spirit Springs** that refill over time up to a cap |
| Cards | **Bestiary Scrolls** |
| Shrines | **Formation Flags**: placed on a map, levelled by Seclusion Hours claimed there; moving one loses progress to the next level |
| Prayers (boon + curse) | **Vows** (e.g., *Vow of Endless Breath*: +EXP, seclusion ends at 10 h) |
| Guild | **Sect Alliance** |
| Star signs | **Natal Stars** |
| Bribes | **Magistrate Favours** (one-time silver purchases: +5% Martial Yield, 2.2% "double insight" on emergence) |
| Post office | **Courier Pavilion** crates per disciple |
| Family bonus | **Lineage Blessing** (highest disciple of each path buffs all) |
| Golden food | **Imperial Delicacies** |

### 9.6 Adjacent production systems

| IdleOn | Jade River | Keep / adapt |
|---|---|---|
| Anvil | **Artisan Forge** (per disciple) with 1–3 **Apprentices** (≙ hammers) producing *Silk Thread, Bronze Rivets, Kiln Bricks…* for free | Keep items/h = 3600 × speed / progressReq (thread 100 → 36/h base), capacity = Artisan pouch × (2 + 0.1 × points), and points split among Speed / Capacity / Insight. |
| 3D Printer | **Mirror of Echoes**: *Echo Sampling* (10% + 0.075%/lvl of a disciple's current craft yield) is inscribed; the mirror deposits that amount to the Treasury every hour, offline | Keep. It is the key "free the disciple" device. |
| Refinery | **Calcination Furnace**: slots burn inputs each cycle (15 min / 60 min / 100 h tiers), build "fire", and refine into **Essence Salts**; ranking up raises cost (rank^1.5) and output (rank^1.3) | Keep. It is the main sink for gathered bulk. |
| Alchemy | Pill Cauldrons + Spirit Springs + Tinctures | Keep costs as items + spring water; tincture level ladder 100 / 1k / 2.5k / 10k items + 3 / 6 / 9 / 12 water. |
| Construction / cogs | **Array Engineering**: disciples supply *Array Craft* rate; *Array Stones* (≙ cogs) placed on a grid buff neighbours; buildings are Formation Flags, the Mirror and Rite Towers | Keep build-rate `3 × (Lv/2 + 0.7)^1.6`. |
| Sailing / Farming | **River Barges** (timed voyages) / **Spirit Fields** (shared-level crops with evolution) | Brief. Keep "shared between all disciples". |

### 9.7 Multi-character (12 disciples)
- Keep "every disciple works all the time". With 12 disciples instead of 10, scale account-wide sinks (pill costs, calcination recipes) by about 1.2× to avoid inflation.
- Keep per-disciple pouches, forge and courier crates, and account-wide Treasury, seals, steles, pills and scrolls. That preserves the "spread disciples across crafts" incentive.
- Keep path affinities (Body / Swift / Mind, five crafts each) and station-specific jobs: cauldron brewer, array builder, rite keeper, snarer, flag camper.

### 9.8 UX recommendations (keep IdleOn's clarity, fix its friction)
- **Emergence Ledger** per disciple: hours away, Martial or Craft Yield %, EXP and levels, items with counts, and the procs ("Double insight!").
- Add a **Sect Overview** that settles all 12 disciples at once, with a per-disciple "pouch full / food out / snare done" status. IdleOn lacks this, and players rely on external sites.
- **Seclusion Info** screen, one per disciple:
  - Crafts: green chance bar → gold Abundance bar, resources/h, EXP/h, and "next Abundance at X Finesse".
  - Martial: kills/h, Sweeping tier bar, survivability, provisions remaining, projected loot/h.
- On-map node plates show requirement and your % (green or gold). Gates show the seal count or craft level.
- QoL from day one: Auto-Settle toggle, Treasury Seal, remote collect for snares and forge, Hour-Incense.

### 9.9 Implementation notes for Godot (offline-first)
1. **Settle analytically, not by simulation.** On emergence, compute `hours × rate` for EXP and items. For random drops, use expected value plus a seeded Poisson or binomial draw per item. Cap the result at pouch capacity. Chain sub-caps in order: food → survivability → kills; pouch → items; forge capacity; spring caps.
2. **Rates can change mid-absence** only through account-wide changes made while playing another disciple, such as a new pill. IdleOn uses the rate at claim time. Keep that (simple, and it rewards upgrading before switching), or snapshot at focus time (fairer but more state).
3. **Clock safety.** Store `last_settle_unix` per disciple plus a monotonic "max seen time". Refuse or neutralise negative deltas and cap each settle at, for example, 90 days. Show time-travel detection gently; it is single-player.
4. **Level-ups during a long claim:** IdleOn applies EXP after the fact at the old rate. Do the same, or integrate level-by-level for accuracy. The former is simpler and matches the reference.
