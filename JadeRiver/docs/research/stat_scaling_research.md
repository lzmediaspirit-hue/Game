# Stat scaling · how 2D MMORPGs grow their numbers, and what Jade River should do

Research brief for decision 13 of `docs/roadmap_master_ui.md` (2026-09-27): "research how 2D MMORPGs scale stats and
gate main quests by level, compared with Jade River's curves. A high-level character should deal hundreds of thousands
of damage." Date of research: 2026-09-27, on branch `claude/jade-river-game-build-pua2z2` at commit 41d15ae.

The page has four parts: the research (§1–§4), Jade River measured today (§5), the proposal (§6) and open questions
(§7). Sources are numbered `S1`…`S60` in §8. Nothing in `scripts/` or `data/` changes with this page.

---

## 0. Summary

**What the references do.**

- The 2D MMORPGs that grow to big numbers build damage from a **few multiplicative buckets, each fed additively by many
  sources**: stat × attack × (1 + Σ damage% + Σ boss%) × Π(1 + final damage) × crit × (1 − defence × (1 − ignore
  defence)) × skill %. MapleStory is the clearest case (S1, S2, S3). Ragnarok Online keeps a percentage defence plus a
  flat one (S28). Tree of Savior moved to a logarithmic attack-against-defence term so that "fairly balanced results"
  hold at any stage (S34).
- Power grows **exponentially by content tier and polynomially inside a tier**. MapleStory bosses run from 12.6 million
  HP (Normal Zakum) to 168 billion (Chaos Zakum) and to 63–157 trillion per phase (Hard Black Mage) (S15, S13). IdleOn's
  first monster of each world has 32, 5,000, 90,000, 800,000, 25 million, 3 billion and 70 trillion HP (S41). Diablo
  III's Greater Rifts compound +17% monster HP per level (S56).
- **Gates** are a level floor plus, at the top end, a stat check tied to the zone: Arcane Force (damage dealt from 10%
  to 150% of normal by ratio to the requirement) and Sacred Force (−10% final damage per 10 points short) in MapleStory
  (S8, S9, S11), Adventurer Fame in DFO (S38), Combat Power in Elsword (S36). The gates that players hate are the
  ones that demand grind past the natural pace (FFXIV's early level gaps, S51), hang on RNG (Lost Ark's honing wall,
  S52), expire (Perfect World's level-capped quests, S49) or sell the way through (idle RPG CP walls, S45, S48).
- **Big numbers** are kept readable by suffixes (MapleStory's Unit damage skin prints "1.2B", S22), new unit tiers
  (IdleOn's Crystal = 10^18, S42) and, when it goes too far, **compression** (DFO divided damage by 1,000, S39; WoW
  squished stats twice, S53).

**What Jade River does today** (measured with `tools/dev/stat_probe.gd` on copies of the valley_run checkpoints; §5):

| Level | Player max HP | Attack (physical / Qi) | Basic hit | Technique hit | Normal foe HP | Time to kill (basic only) | Foe's blow |
|---|---|---|---|---|---|---|---|
| 1 | 96 | 7 / 7 | 7 | — | 46 | 2.7 s | 6.8% of HP |
| 9 / 13 | 400 / 697 | 30 / 99 at 13 | 32 / 95 | — / 114 | 254 / 410 | 4.7 s / 2.6 s | 8.9% / 6.3% |
| 31 | 3,266 | 283 / 329 | 245 | 336 | 1,552 | 3.7 s | 4.3% |
| 63 | 10,421 | 370 / 520 | 555 | 635 | 5,340 | 5.3 s | 4.6% |
| 80 | 20,188 | 1,887 / 2,722 | 3,030 | 3,031 | 8,270 | 1.5 s | 3.5% |
| 98 | 31,243 | 2,092 / 3,207 | 3,246 | 3,647 | 12,064 | 1.9 s | 2.9% |

- **Today's high-level damage is in the low thousands**: 3,246 per basic hit at Level 98. The best that character can
  reach under today's rules (every piece Perfect and +10, top affixes, Glimpse of Heaven at mastery tier 6, the Sword
  Dao at 6) averages 7,500 per basic hit and 49,000 per technique hit, with a best crit of 86,000. No build reaches
  100,000.
- **Growth is flat for long stretches.** From Level 80 to 98 the basic hit rises 7% while normal foes gain 46% HP. The
  causes: no gear above item Level 81 (`docs/item_plan.md` G1), an energy multiplier that steps only at Cloud Stride
  and Sage for physical blows (at half strength), and attributes worth under 1% a Level.
- Numbers are **polynomial** everywhere: monster HP ×267 from Level 1 to 99, the player's hit ×460. The references grow
  by 10^6 (MapleStory's normal mobs) to 10^33 (IdleOn).
- **Gates** are already of the reference kind: realm floors on 7 of 33 Act I main quests, 13 of 21 in Act II and 2 of
  23 in Act III; chapter openers offered by realm-triggered unlocks; attunement (Storm Ward 6–60, Starsea Endurance
  20–90) as the Arcane Force analogue; zone ceilings; never Combat Power.

**The proposal** (§6):

- One new multiplier, **Might**, ×1.30 per great realm (×1.17 at the major breakthrough, the rest spread over its nine
  Levels), applied to the player's attacks, HP and defences and to every monster of the same Level. Items keep their
  numbers; cultivation carries the scale, as the genre says it should.
- **Target par numbers**: Level 99 basic hit **136K**, technique hit **527K**, crit technique **922K**, sheet attack
  **119K**, max HP **427K**; Level 120 basic 611K; Level 165 basic 5.95M; Level 200 basic 22M. Bone Forging (Levels
  1–9) keeps today's numbers within 5%; the first step is ×1.30 at Qi Kindling 1.
- Monster HP is set from the par character: a normal foe takes **3.5 par basic hits**, an elite ×6, a boss its par time
  × par DPS (Nebula Leviathan about 127M). A normal foe's blow takes **6% of par HP** (8% under Level 20).
- The damage formula gains MapleStory's two missing buckets: one additive **damage%** bucket (damage%, elemental power,
  boss damage) and a multiplicative **final damage** list. The energy multiplier becomes a small **Qi edge**.
- Numbers of 10,000 and more print through a new `UiKit.short` ("136K", "1.27M").
- Main quests open at **explicit chapter floors** (Level floors by realm, a table per act to v1.5), shown in the quest
  log with the gap and where to close it; floors only, never ceilings; never Combat Power.

---

## 1. How 2D MMORPGs build their stats

### 1.1 Primary and derived stats

| Game | Primary stats | Derived / secondary | Notes | Source, confidence |
|---|---|---|---|---|
| MapleStory (PC) | STR, DEX, INT, LUK (a main and a secondary per class) | Attack / Magic Attack, Damage %, Boss %, Ignore Enemy Defence, Final Damage, crit rate and damage, Arcane / Sacred Force | Main stat contributes most; Hyper Stats add "final" STR that % stat does not multiply | S1, S2 · H; S60 · M |
| MapleStory M | as PC | Combat Power from main and secondary stats, attack, damage, boss, final and crit damage; CP rises with HP and with ATK including 20% of crit ATK | CP gates party boss entry (each member and the party sum) | S16, S27 · M |
| Ragnarok Online | STR, AGI, VIT, INT, DEX, LUK (1–99; 120 or 130 for third classes); 4th jobs add POW, STA, WIS, SPL, CON, CRT | ATK/MATK, hard DEF (a %), soft DEF (flat), HIT = 175 + DEX + LUK/3 + base level, ASPD | Each stat point costs more as the stat rises | S28, S29, S30 · H |
| Tree of Savior | STR, CON, INT, SPR, DEX | Attack, defence, crit | Each main stat adds sub-stats per point and a bonus every 10 points; % sub-stats apply only to the base value | S34 · M |
| Elsword | none to allocate | Attack, Final Damage, crit, and a Combat Power figure that gates dungeons | CP was reworked in April 2026 to weigh what matters in combat | S36, S37 · M |
| Dungeon Fighter Online | STR, INT, VIT, SPR | Attack, elemental damage; Adventurer Fame as the gate figure | Fame replaced the older Exorcism figure for dungeon entry | S38 · M |
| Legends of IdleOn | STR, AGI, WIS, LUK (main by class) | Base damage from weapon power and main stat, then per-X and damage % multipliers | Every stage of damage is soft-capped by power laws (below) | S41 · H (code) |
| Flyff | STR, STA, DEX, INT | Attack, a level modifier, element effectiveness, hit and evade | About 2 skill attack per STA | S43 · L |

### 1.2 The damage formula and its buckets

**MapleStory** (S1 · H; S2 · H; S3 · M):

```text
damage ≈ 0.01 × weapon multiplier × stat value × attack × (1 + attack%)
         × (1 + damage% + boss% [or normal-monster%])      ← one additive bucket
         × Π (1 + final damage_i)                          ← multiplicative, each source separately
         × (1 − defence × (1 − IED))                       ← IED = 1 − Π(1 − source_i): multiplicative, diminishing
         × crit (1 + crit damage%) × level-difference × Arcane/Sacred Force factor × skill% × mastery
```

- Damage% and boss% add inside one bucket; final damage multiplies across sources (S2 · H; S3 · M).
- Ignore Enemy Defence stacks multiplicatively, so each source is worth less than the one before (S2 · H).
- Monster defence is about 0.1 for mobbing and 3 to 3.8 (300–380%) for bossing, which is why IED is the endgame stat
  (S2 · M).
- Arcane Force multiplies final damage by 10% to 150% by the ratio of the character's force to the field's
  requirement, in 10% steps above the requirement (1.0× → 100%, 1.1× → 110% … 1.5× → 150%), and the monster's
  damage by 0% to 280%; at 150% the character takes 1 damage (S8 · M; S9 · M; S10 · M).
- Sacred (Authentic) Force: −10% final damage for every 10 points short; 100 or more short leaves 5% (S11 · M).
- Level difference: under Reboot rules a character 20 Levels below a monster loses all damage; bosses take −5% per
  Level of difference (S1 · L).

**Ragnarok Online** (S28 · H): `final = floor[((ATK × skill% × bonuses) × hardDEF − softDEF) × crit]`, with Renewal's
hard DEF as a multiplier `4000 / (4000 + DEF)` (500 hard DEF halves damage) and soft DEF `VIT/2 + AGI/5 + BaseLv/2`
subtracted after it.

**Tree of Savior** (S34 · M): `damage = (% factor) × attack × min{1, log10((attack / (defence + 1))^0.8 + 1)} + flat`.
The developers moved to it so the ratio "could take various attack and defence values and produce fairly balanced
results regardless of character development stage". The log term caps the defence effect at 1.

**Legends of IdleOn** (S41 · H, re-implemented game code):

```text
base    = (weapon power × (1 + talents) + sharpened axe)/3)^2 + main stat + min(150, 2 × WP + stat) + flat sources
base    : soft caps at 4,000 (^0.91 above) and 15,000 (^0.84 above)
damage% : soft caps at 100 (^0.86), 2×10^7 (^0.8), 5×10^8 (^0.6), 2×10^9 (^0.45), 1.5×10^10 (^0.36), 6×10^10 (^0.28)
max hit = base × per-X bonuses × damage%;  min hit = mastery × max hit
```

IdleOn lets the account's hundreds of bonus sources multiply, then bends each stage with a power law so no single
source runs away.

**Elsword, DFO, Flyff.** Elsword's Final Damage multiplies the whole hit by its % (S36 · M). DFO's numbers reached 10–15
billion per measured run in its August 2024 balance data (S40 · M). Flyff applies a level modifier, element
effectiveness and the target's defence (S43 · L).

### 1.3 How the sources stack

| Source | MapleStory | Others | Confidence |
|---|---|---|---|
| Levels | Ability points per Level into the main stat; small by itself late (no fetched source; L) | RO: stat points per Level, dearer as the stat rises (S29, M) | L / M |
| Gear base | weapon attack × the class's weapon multiplier | RO refines add Refine ATK that only Refine DEF reduces; +4 is easy, 50% from +5 and falling (S33) | M |
| Enhancement | Star Force: stars 1–5 add 2 to each stat, 6–14 add 3; weapon attack rises only if the base had some (S21) | ROM refine; DFO reinforcement | M |
| Potential / affixes | 3 lines, 4 tiers (Rare, Epic, Unique, Legendary); % by item Level: 3/6/9/12% at 71–200, 4/7/10/13% at 201+; Legendary prime lines up to 40% boss or 40% IED; a separate 3-line Bonus Potential stacks (S20) | IdleOn obols, stamps, cards | H |
| Sets | set effects add stats, HP%, and damage lines (S60) | Item plan §3 for Jade River | M |
| Skills and passives | skill % × hit count; Hyper Stats (final STR, crit damage, IED, boss %) (S60) | ToS attributes | M |
| Account-wide | Legion/Union, link skills (final damage on conditions, e.g. +9–14% at full HP) (S60) | IdleOn's whole account web | M |
| Zone stats | Arcane/Sacred Force from symbols (+30 Arcane Force per symbol level at the start; Sacred symbols from Level 260, 10 each) (S8, S12) | DFO Fame | M |

---

## 2. Scaling with time

### 2.1 The shapes

| Game | Player power against Level | Monster HP | EXP to level | Confidence |
|---|---|---|---|---|
| MapleStory | Stepped exponential by gear tier (Arcane, Genesis), polynomial by Level | Arcane River normal mobs ×3 HP (×1.8 EXP), Levels 241–249 ×10 HP (×3.7 EXP) (S17); bosses from 12.6M to quadrillions (S15, S13, S11) | The biggest single jump is 199 → 200; 220–250 needs hundreds of billions; 250–300 trillions (S18 · L) | M |
| IdleOn | Exponential by world, soft-capped | World-first monsters 32 → 5K → 90K → 800K → 25M → 3B → 70T; last World 7 foes 10^30–10^35 (S41) | exponential | H |
| Diablo III (not 2D; the clearest exponential) | Paragon, gear | +17% HP and +13.2% damage per Greater Rift level, compounding (S56) | — | M |
| Ragnarok Online | Polynomial (stats to 99/130), jobs step it | Level-based | 99 reachable in under two months of casual play pre-renewal (S32 · L); ±5 Levels full EXP, 21+ Levels apart 40% (S31 · M) | M |
| Flyff | Level cap 165 (v1.41), then Infernal dungeons 166–190 (S43) | — | — | M |
| xianxia idle (Immortal Taoists, Overmortal) | Realm steps: 10 minor realms per major, a tribulation chance per breakthrough, pills +5% each (S46 · M); a breakthrough pill per realm covering its three stages (S47 · M) | — | Cultivation Base accrues every 5 s by realm (S46 · M) | M |
| Design literature | Polynomial `base × Level^e` with e 1.5–2.2 is the "gentle early, steep late" default; pure exponentials make walls (S55 · M). Idle games mix exponential costs against polynomial or exponential production and reset with prestige (S54 · H) | | | |

### 2.2 Damage numbers at the start, the middle and the end

| Game | Level 1 | Middle | End | Source, confidence |
|---|---|---|---|---|
| MapleStory | Beginners hit snails for single digits; magicians "rarely above 2–3"; Three Snails deals 10; a snail gives 2 EXP | Players' top lines went 100K → 999K → 55.5M → 1B over four years to 2017 | A 10-billion-per-line cap, which Nexon called "removing the cap", became the bottleneck for slow hard-hitting classes at Hard Lucid; some builds could reach 30B a line; boss HP 63–157T per Black Mage phase, 6.48 quadrillion for Extreme Seren | S23 · M, S4 · M, S6 · M, S7 · M, S13 · M, S11 · M |
| MapleStory damage cap history | Pre-Big Bang 199,999 (community memory; the pages that list it were blocked) | Visual range cap raised to 99,999,999 on 2016-11-30 (GMS v178) | 10B per line | L, S5 · M, S6 · M |
| DFO | — | — | 10–15 billion per measured run (Aug 2024); earlier a 1:1,000 damage compression | S40 · M, S39 · H |
| IdleOn | Green Mushroom 32 HP | World 4: 800K–20M HP | World 7: 70 trillion to 10^35 HP; a new "Crystal" tier = 1,000,000 trillion | S41 · H, S42 · H |
| Ragnarok Online | tens | thousands (pre-renewal) | Renewal builds are balanced around hundreds of thousands to millions a hit (no fetched source gave a figure) | L |

### 2.3 Time to level, catch-up and caps

- **Catch-up.** MapleStory's Hyper Burning MAX (2024-12-19) gives 1 + 4 Levels per level-up from 10 to 260, and the
  EXP to 260 was halved (S19 · H). ToS hands out fixed-EXP cards to close a gap to the map's Level (S35 · M). WoW
  squished levels (120 → 50) and stats to restore sane numbers (S53 · H). Jade River already has Ancestral Guidance
  (×1.5 accumulation two great realms behind) and the Account Legacy (+2% a great realm) (`docs/cultivation_loop.md`
  §12).
- **Soft and hard caps.** RO caps stats at 99 (120/130) (S29 · M). MapleStory's Arcane Force bonus stops at 150% (S8 ·
  M). IdleOn bends every stage with power laws (S41 · H). ToS's log term tops out at 1 (S34 · M). The MapleStory damage
  cap was a hard cap per line (S6 · M).

---

## 3. Gating

### 3.1 How the references gate

| Game | Level floors | Chain | Stat check | Item / CP |
|---|---|---|---|---|
| MapleStory | Arcane River areas level-locked from 200; Tenebris at 245 (to 275); Black Mage needs 255 and the Limina quests; Will 235/250 by mode | Story quests per area | Arcane Force: Will 560/760, Verus Hilla 820/900, Black Mage 880 (story) and 1,320 (Hard, Extreme); Cernium 50 Sacred, Fallen Cernium 70/100 | CP for party boss entry (MapleStory M and PC boss lobbies) | 
| DFO | Level 110–115 content | — | Adventurer Fame 11,914–40,047 at 110; Labyrinth of Paradox 115 and 58,950 Fame; you can enter below Fame except limited dungeons; the Adventure Navigator lists the items to get | — |
| Elsword | Levels by region | Clear the previous dungeon (Master Class after Varnimyr's last dungeon) | Combat Power 1,400 (Elrianode City), 8,500 / 17,000 (Training Grounds normal / hell); entry at 95% of the requirement | CP |
| Perfect World (PWI, Mobile) | Main quest waits for a Level; PWI's level-capped quests vanish or cannot be handed in past the range | — | — | Cultivation quests at Levels (Mobile) |
| FFXIV (3D, the canonical MSQ) | Every MSQ step has a Level | Linear, 40–50 h per expansion | — | — |
| Lost Ark (2.5D) | — | — | — | Item Level 1,340 → 1,370 by honing at ~30% success |

Sources: S26 · M, S13 · M, S17 · M, S12 · M, S38 · H, S36 · M, S49 · M, S50 · M, S51 · M, S52 · M.

### 3.2 Which gates feel good and which feel bad

| Gate | Reception | Why | Source, confidence |
|---|---|---|---|
| A graded stat check (Arcane Force) | Mixed | It is readable (a ratio, a table) and rewards dailies, but players at 210 without 100 Arcane Force are "stuck between mobs that are too hard and those that give poor experience"; at the other end, taking 1 damage at 150% "is no fun" | S24 · M, S25 · M |
| A floor you can walk below (DFO Fame) | Good | Entry is allowed below Fame except for limited dungeons, and the Navigator says what to get | S38 · H |
| A CP gate with tolerance (Elsword's 95%) | Neutral | Soft edge; but CP must reflect real strength, hence the 2026 rework | S36 · M, S37 · M |
| Main quest waiting for Levels (FFXIV early game, Perfect World) | Bad when the path's own EXP falls short | "Level 37, 12 Levels above my MSQ requirement" felt slow the other way; filler quests drag | S51 · M, S50 · M |
| RNG item-level gate (Lost Ark 1,340 → 1,370) | Bad | "Every hone fails, materials drain … the number refuses to budge" | S52 · M |
| Quests that expire past a Level (PWI) | Bad | Over-levelled players lose rewards and XP for good | S49 · M |
| CP walls in idle RPGs (MapleStory Idle RPG, Immortal Taoists) | Bad | Read as paywalls ("every time you spend money … a new paywall"; the spirit-jade paywall) | S48 · M, S45 · M |
| Realm-ups that stop adding power (Infinite Cultivation) | Bad | "Realm-ups stop raising power and timers jump to 146 days" | S45 · M |

The lesson for Jade River: a floor the main path reaches on its own, a stat check whose material the main path hands
out, a visible reason and a named way through, no expiry, no RNG wall, and every breakthrough must add power.

---

## 4. Big numbers

### 4.1 Why games show hundreds of thousands to billions

- Rising numbers are the cheapest visible proof of progress; watching them climb is itself a reward (S58 · M, S57 · M).
- Exponential tiers let a new tier make the old one trivial at once, which is the point of a tier in MapleStory and
  IdleOn (S17, S41).
- Idle games need exponentials because costs grow exponentially and production must keep up (S54 · H).
- For a xianxia game the genre asks for it: each great realm is a qualitative leap over the one below.

### 4.2 Readability tricks

| Trick | Example | Source, confidence |
|---|---|---|
| Suffixes with three significant figures | MapleStory's Unit damage skin: "1.2B" (GMS), "1B 200M" (MSEA), "12억" (KMS) | S22 · H |
| Local units | Korean 만 (10^4), 억 (10^8), 조 (10^12) between digits: "3억1152만8805" | S22 · H |
| New unit tiers | IdleOn's in-game glyph tiers, then "Crystal" = 10^6 trillion | S41 · H, S42 · H |
| Letter suffixes after T | K, M, B, T, aa, ab… (idle convention; "aa feels like you broke containment") | S44 · M |
| Compression | DFO: max-damage font digits changed, status damage compressed 1:1,000 | S39 · H |
| Squish | WoW 2014 and 2020: item-level power scaled back, levels 120 → 50 | S53 · H |
| Hide them | Elsword and DFO players ask for options to hide damage numbers | S37 · M |

### 4.3 Where it goes wrong

- **Stat inflation**: WoW's item levels ran past what the design expected once hard modes and a fourth raid tier
  arrived (S53 · H).
- **Power creep**: new content makes the old irrelevant, and new or returning players must catch up fast (S57 · M).
- **Caps that bite**: MapleStory's 10B cap hurt slow, hard-hitting classes most (S6 · M, S7 · M).
- **Returning-player shock**: the numbers a player left are meaningless when they return (S57 · M); MapleStory answers
  with Hyper Burning (S19 · H).
- **Numbers that stop meaning anything**: players who hate damage numbers call them "purely aesthetic" (S58 · M).

---

## 5. Jade River today

### 5.1 The formulas as they run

```text
attack   = weapon_attack(ilv) × quality × (1 + 0.05 × enhance) × energy-type limit      stat_rules.gd:41-53, 287-296
           × (1 + 0.008 × main attribute + 0.004 × second)                             stat_rules.gd:295-297
           weapon_attack = 8 + 3·ilv + 0.12·ilv²   (fists: that at the Level × 0.6)     stats.py:103-104
qi_attack  = attack × (1 + 0.005 × Essence) × (1 + family bonus)                       stat_rules.gd:298
max HP   = (50 + 20·L + 0.9·L²) × (1 + 0.01 × Body) + gear + modifiers                 stat_rules.gd:279, stats.py:39
hit      = roll(range × technique mult) × E (physical at half) × (1 + 0.05·Dao tier + 0.08·mastery)
           × (1 + elemental power) × element cycle × fed ground × attunement × realm gap × crit (≤ ×3.0)
           × (1 − defence cut ≤ 75%) × (1 − elemental resistance) × situation         combat_rules.gd:52-105
defence cut = def / (def + 100 + 15 × attacker Level)                                 combat_rules.gd:40-43
E        = 1.0 · True Qi 1.3 (+2.5% a purity grade) · Sage 1.7 · Law 2.2 · Monarch 2.8 · Heavenforce 3.5
                                                                                        stats.py:95-97
monster  HP = (30 + 15·L + 1.1·L²) × role (elite 6, field boss 40, dungeon boss 80, story 20) × hp_mult
         attack = (5 + 2.2·L + 0.1·L²) × role; defence = armour(L) × role (0.8 normal)   stat_rules.gd:393-405
CP       = (HP/10 + attack × attacks a second × crit factor × 0.5 + defences/4) × E    stat_rules.gd:379-390
```

Most other damage in the game is already a share: hazards, tribulations, ground fire and boss markers take a share of
max HP (`docs/boss_design.md` §2.1); heals are percentages; pets strike with a share of the player's attack
(`pet_authority.gd:502`); allies with 35% of it (`companion_authority.gd:86`); thrown items and talismans with a
multiplier of it. Only the arena pets (`PetRules.combatant`) keep their own flat curve, and they fight each other.

### 5.2 Measured numbers

`tools/dev/stat_probe.gd` (run headless with `res://tools/dev/stat_probe.tscn`) copies each valley_run checkpoint
(`user://valley_cp/<section>`, the progressed "Tester" in slot 1, never the Max Tester) into `user://stat_probe_work/`,
loads it and measures with the real rules: `StatRules` for the sheet, `CombatRules.resolve` averaged over 4,000 rolls
against the normal foes whose Level band holds the character's Level (`StatRules.mob_stats`), and the foes' plain blow
against the character. Level 1 is a new character moved to Bone Forging 1 in memory. DPS counts the family's combo only
(no techniques). Hit rate was 100% throughout.

| Checkpoint | Level | Realm | Weapon (iLv, quality, +) | Max HP | Physical / Qi attack | Crit | Basic hit (max) | Best slotted technique (max) | DPS | Normal foe HP | Hits / time to kill | Foe's blow | CP (room's recommended) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new | 1 | Bone Forging 1 | fists | 96 | 7 / 7 | 11% ×1.5 | 7 (12) | — | 16 | 46 | 6 / 2.7 s | 6.8% | 21 (38) |
| bf2 | 2 | Bone Forging 2 | fists | 134 | 9 / 10 | 11% | 9 (16) | — | 20 | 64 | 7 / 3.2 s | 7.3% | 27 (40) |
| qk1 | 9 | Bone Forging 9 | Training Jian (5, Common, +0) | 400 | 30 / 33 | 10% | 32 (54) | — | 54 | 254 | 8 / 4.7 s | 8.9% | 67 (146) |
| qk5 | 13 | Qi Kindling 4 | Iron Jian (14, Common, +0) | 697 | 90 / 99 | 10% | 95 (158) | Flowing Palm 114 (201) | 159 | 410 | 5 / 2.6 s | 6.3% | 144 (236) |
| qu5 | 22 | Qi Unfurling 4 | same | 1,641 | 98 / 112 | 11% | 102 (167) | 101 (229) | 172 | 892 | 9 / 5.2 s | 5.5% | 249 (362) |
| ht1 | 27 | Qi Unfurling 9 | Jadeiron Jian (27, Fine, +0) | 2,447 | 279 / 318 | 12% | 286 (469) | 395 (688) | 489 | 1,236 | 5 / 2.5 s | 4.6% | 464 (524) |
| ht5 | 31 | Heart Tempering 4 | same | 3,266 | 283 / 329 | 12% | 245 (472) | 336 (692) | 420 | 1,552 | 7 / 3.7 s | 4.3% | 552 (524) |
| cs1 | 36 | Heart Tempering 9 | same | 4,189 | 295 / 349 | 12% | 253 (486) | 425 (741) | 437 | 1,496 | 6 / 3.4 s | 4.3% | 655 (596) |
| cs5 | 40 | Cloud Stride 4 | same | 5,031 | 319 / 411 | 13% | 399 (649) | 569 (990) | 694 | 2,390 | 6 / 3.4 s | 4.3% | 1,135 (686) |
| hg1 | 53 | Spirit Awakening 8 | same | 8,452 | 351 / 476 | 14% | 535 (867) | 535 (1,057) | 953 | 3,914 | 8 / 4.1 s | 4.8% | 1,715 (920) |
| ae1 | 63 | Heaven Glimpse 3 | same | 10,421 | 370 / 520 | 14% | 555 (894) | 635 (1,090) | 1,001 | 5,340 | 10 / 5.3 s | 4.6% | 2,039 (1,172) |
| ae3 | 68 | Sage 2 | Stormsteel Jian (68, Common, +0) | 13,662 | 1,412 / 1,952 | 15% | 2,267 (3,645) | 2,039 (4,444) | 4,125 | 6,136 | 3 / 1.5 s | 3.6% | 4,230 (1,226) |
| ae5 | 75 | Sage Sovereign 1 | Sunsteel Jian (77, Common, +0) | 16,776 | 1,830 / 2,594 | 21% | 2,972 (4,653) | 3,011 (5,675) | 5,473 | 7,342 | 3 / 1.3 s | 3.4% | 5,346 (1,352) |
| ae_end | 80 | Sage Sovereign 3 | same | 20,188 | 1,887 / 2,722 | 21% | 3,030 (4,747) | 3,031 (5,787) | 5,629 | 8,270 | 3 / 1.5 s | 3.5% | 6,000 (1,442) |
| ls2_end | 87 | Will Manifest 2 | same | 24,083 | 1,967 / 2,906 | 27% | 3,199 (4,876) | 4,364 (8,510) | 6,015 | 9,660 | 4 / 1.6 s | 2.9% | 6,851 (1,550) |
| ls4_end | 93 | Sphere Lord 1 | same | 27,892 | 2,035 / 3,069 | 28% | 3,324 (5,043) | 4,229 (8,800) | 6,315 | 10,938 | 4 / 1.7 s | 3.0% | 7,620 (1,658) |
| ls6_end | 98 | Sphere Lord 3 | same | 31,243 | 2,092 / 3,207 | 28% | 3,246 (5,133) | 3,647 (6,891) | 6,218 | 12,064 | 4 / 1.9 s | 2.9% | 8,292 (1,784) |
| ceiling | 98 | Sphere Lord 3 | Sunsteel, Perfect +10, top affixes; all armour Perfect +10 | 31,658 | 4,407 / 6,254 | 31% ×1.65 | 7,487 (12,367) | Glimpse of Heaven 49,018 (85,926) | 14,343 | 12,064 | 2 / 0.8 s | 2.5% | 11,837 |

The clock is pinned to the moment each checkpoint was saved, so no offline time is claimed and timed buffs and the
calendar stand as they were. The late crit rates of 21–28% include two Blood Memory fate cards (+5% each; the JSON
lists every crit source). The other checkpoints (bf5, bf8, qu1, sa1, sa5) sit on the same curve; `--out=` writes all
of them as JSON.

The Flowing Palm figures are per hit; it strikes twice. The energy multiplier at Level 40–63 is 1.50 (True Qi with
purity), 1.70 from Sage. Bosses as built (`StatRules.mob_stats` at their Level): Big Toad Tan 31,507 HP (Level 18),
the Drowned Abbot 98,952 (27), the Gate Guardian 106,818 (63), the Tomb King 215,793 (77), Admiral Voss 1,317,120
(90), General Kharn 1,457,974 (92), the Nebula Leviathan 1,082,056 (99).

**Formula curves** (the probe's `curve`, the data alone):

| Level | Realm | Weapon attack at iLv = L | Normal foe HP | Elite HP | Dungeon boss HP (×80) | Foe attack | HP pool base | Same-Level defence cut | E |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Bone Forging 1 | 11 | 46 | 276 | 3,688 | 7 | 70 | 3.7% | 1.0 |
| 10 | Qi Kindling 1 | 50 | 290 | 1,740 | 23,200 | 37 | 340 | 7.1% | 1.0 |
| 30 | Heart Tempering 3 | 206 | 1,470 | 8,820 | 117,600 | 161 | 1,460 | 12.0% | 1.0 |
| 60 | Heaven Glimpse 2 | 620 | 4,890 | 29,340 | 391,200 | 497 | 4,490 | 18.0% | 1.3 |
| 80 | Sage Sovereign 3 | 1,016 | 8,270 | 49,620 | 661,600 | 821 | 7,410 | 21.5% | 1.7 |
| 99 | Sphere Lord 3 | 1,481 | 12,296 | 73,776 | 983,688 | 1,202 | 10,850 | 24.5% | 1.7 |
| 120 | Heaven's Threshold | 2,096 | 17,670 | 106,020 | 1,413,600 | 1,709 | 15,410 | 27.6% | 2.8 |
| 165 | Inner Heaven 9 | 3,770 | 32,452 | 194,715 | 2,596,200 | 3,090 | 27,852 | 33.4% | 3.5 |

**Time to level** (`realms.json` need per Level = 100 × T; `balance_sim` hours, run for this page):

| Level | Realm | T (target minutes a Level) | QP a Level | Normal kills a Level (22 QP each) | Hours played to reach (balance_sim) |
|---|---|---|---|---|---|
| 1 | Bone Forging 1 | 12 | 1,200 | 55 | 0.5 |
| 10 | Qi Kindling 1 | 53 | 5,300 | 241 | 5.4 |
| 19 | Qi Unfurling 1 | 47 | 4,700 | 214 | 11.6 |
| 28 | Heart Tempering 1 | 67 | 6,700 | 305 | 20.8 |
| 37 | Cloud Stride 1 | 80 | 8,000 | 364 | 31.5 |
| 46 | Spirit Awakening 1 | 87 | 8,700 | 395 | 43.7 |
| 55 | Heaven Glimpse 1 | 100 | 10,000 | 455 | 56.1 |
| 64 | Sage 1 | 1,050 | 105,000 | 4,773 | 62.3 |
| 73 | Sage Sovereign 1 | 200 | 20,000 | 909 | 105.1 |
| 82–99 | Will Manifest, Sphere Lord | 333 | 33,300 | 1,514 | not simulated; about 140 h at the sim's Sage income (≈370 QP a minute), 235 h at the nominal 100 |
| 100–165 | Law Touching → Inner Heaven | 400 | 40,000 | 1,818 | — |

A kill pays 22 QP at every Level (`curves.json` `kill_qp`), so the share of a Level that one kill buys falls from 1.8%
at Level 1 to 0.07% at Level 99. That is independent of damage and stays out of this proposal.

### 5.3 Where the scaling is flat

| Stretch | Basic hit (measured) | Normal foe HP | What happens |
|---|---|---|---|
| 13 → 22 | 95 → 102 (+7%) | 410 → 892 (+118%) | Iron Jian held; attributes +1 a Level |
| 27 → 36 | 286 → 253 (−12%) | 1,236 → 1,996 (+61%) | Jadeiron Jian (iLv 27) held from Level 27 to 63; mob defence rises |
| 53 → 63 | 535 → 555 (+4%) | 3,914 → 5,340 (+36%) | the same weapon; True Qi's 1.3 counts half for physical blows |
| 63 → 68 | 555 → 2,267 (×4.1) | 5,340 → 6,136 | Stormsteel (iLv 68) and Sage Qi arrive together: one cliff |
| 80 → 98 | 3,030 → 3,246 (+7%) | 8,270 → 12,064 (+46%) | no gear above iLv 81 (G1); E stays 1.7 from Level 64 to 99; +1 attribute a Level |

Other symptoms:

- **Normal foes stop threatening**: their blow falls from 9% of HP at Level 9 to 2.9% at 98, because player HP
  (quadratic × Body) outgrows monster attack (quadratic).
- **Combat Power drifts from the rooms' figure**: 0.46× the recommended CP at Level 9, 1.05× at 31, 1.7× at 63, 4.6× at
  98. Recommended CP is `20 + 18 × Level` (linear; `world.py`, `rankings.json` `ref_cp`), so idle Hunt runs below
  full pace early (0.46 at Level 9) and at its 1.5 cap from about Level 40 (`account_authority.gd:381`, clamp 0.2–1.5),
  and the Heaven Ranking's seeded rivals fall behind.
- **The spread between the reference and the ceiling is ×2.3 on basic hits and ×13 on techniques**: the multiplier
  stack is wide but the road the valley run walks feeds little of it (Common +0 weapons, Flowing Palm at 1.2).
- **Bosses run long**: the reference's 6,200 DPS against the Leviathan's 1.08M is 174 s of basic strikes before its
  phases; `docs/boss_design.md` §1.3 estimates 6–9 minutes for the three v1.2 bosses.

### 5.4 The references against us

| | MapleStory | IdleOn | DFO | Jade River today | Proposal (§6) |
|---|---|---|---|---|---|
| Shape | Exponential by content tier | Exponential by world, power-law soft caps | Stepped by tier, compressed 1:1,000 once | Quadratic in Level; two energy steps | ×1.30 a great realm on top of today's quadratics |
| First hits | 2–10 | foes of 32 HP | — | 7 | 12 |
| Endgame hits | up to 10B+ per line | foes of 10^30–10^35 HP | 10–15B a run | 3,246 (reference), 49K technique (ceiling) | 136K basic, 527K technique at Level 99; 5.95M basic at 165 |
| Endgame boss HP | 63T–6.48 quadrillion | — | — | 1.46M (Kharn) | 16M (Tomb King) to 127M (Leviathan) |
| Growth Level 1 → end | ~10^9–10^10 (hits) | ~10^33 (foe HP) | — | ×460 (hits) | ×11,000 by 99, ×500,000 by 165 |
| Zone stat check | Arcane / Sacred Force | world progress | Fame | Attunement (Storm Ward, Endurance) | Attunement, unchanged |

### 5.5 How main quests are gated today

Counted from `data/quests.json` and `data/unlocks.json`:

| Act | Main quests | With a realm floor | Floors | Chapter openers offered by a realm-triggered unlock | Other gates |
|---|---|---|---|---|---|
| Prologue, I (ch. 1–10) | 33 | 7 | Bone Forging 4 (Lv 4), Qi Kindling 6 and 7 (15, 16), Heart Tempering 1 and 5 (28, 32), Spirit Awakening 8 (53), Heaven Glimpse 2 (58) | ch. 3 at Bone Forging 7 (7), 4 at Qi Kindling 9 (18), 5 at Qi Unfurling 3 (21), 6 at Heart Tempering 9 (36), 7 at Cloud Stride 1 (37), 8 at Spirit Awakening 2 (47), 9 at Heaven Glimpse 1 (55), 10 at Heaven Glimpse 3 (61) | Quest chains (`quest_done`), sealed portals (in all acts: 15 on a realm, 26 on a quest done, 17 on a quest under way), events (the Heart Trial, the siege), the zone ceiling at Heaven Glimpse 3 |
| II (ch. 11–16) | 21 | 13 | Heaven Glimpse 3 (61), Sage 1–3 (64, 67, 70), Sage Sovereign 1 (73) | Storm Ward at Heaven Glimpse 3; Clans at Sage 2 | Storm Ward in 25 field rooms (6 → 60); Sage Sovereign 3 ceiling |
| III (ch. 17–22) | 23 (tagged `act2_side` for QP) | 2 | Sage Sovereign 3 (79), Will Manifest 3 (88); Presence level 5 for The Observatory | Starsea Endurance at Sage Sovereign 3; Presence at Will Manifest 1; Star beasts at Will Manifest 2 | Endurance in 30 rooms (20 → 90); Sphere Lord 3 ceiling. Chapters 21 and 22 have no floor at all |

Attunement multiplies damage dealt by `min(1.1, 0.3 + 0.7 × ratio)` and damage taken by `1 + max(0, 1 − ratio)`
(`combat_rules.gd:26-31`): the same graded shape as Arcane Force, gentler at the top (110% against 150%). Combat Power
gates nothing; it sets the idle Hunt rate only.

---

## 6. Proposal

**Built** as roadmap phase P12 · Might (2026-09-27). §6.8 lists what was built, where it differs from this section, and
the numbers measured on the valley_run checkpoints before and after.

### 6.1 Principles

1. **Cultivation carries the scale.** A new multiplier, Might, belongs to the realm. Items keep today's numbers. A
   character who breaks through is stronger at once; a treasure amplifies a cultivator, it does not replace one.
2. **Player and monster share one curve.** A monster of Level L has the Might of a player at Level L. Time to kill and
   the share of HP a blow takes stay what the rules make them, whatever the Level.
3. **Numbers are a par character's numbers.** The targets below are what a par character does: Fine quality from
   Level 10, Superior from 37; enhancement about Level ÷ 12 (+8 at 99, +10 from 120); a weapon three Levels behind its
   wearer; the weapon's Dao at tier 1 by Qi Kindling, 3 by Spirit Awakening, 5 by Will Manifest, 6 by Monarch; the
   main technique's mastery at 3, then 4, 5 and 6; an attack affix (5%, then 8%, 12%); four set pieces from Cloud
   Stride (+8% damage) and six from Sage (+13%). The balance_sim builds that character with the real rules and
   checks it against the table (±15%).
4. **Few buckets, each named.** Level, Might, gear, attack%, damage%, final damage, skill, crit, defence, element,
   situation. A player can read which bucket a source feeds.
5. **Every breakthrough adds power.** A major breakthrough is +17% on everything; each Level inside the realm +1.3%
   (Might) on top of what gear and attributes add. Bone Forging stays as today (Might 1.00–1.05).
6. **Readable at every Level.** Every par figure prints in five characters or fewer through `UiKit.short`.

### 6.2 Target curves

**Might.** `STEP = 1.30` per great realm, Bone Forging to Monarch. 60% of the step is taken at the major breakthrough
(×1.17), 40% spread over the realm's other eight Levels (×1.0132 each, on top of each Level's other growth). The three
advanced states (Half-Heaven Monarch, Dao Sigil, Heaven's Threshold) are ×1.10 each. Inner Heaven's nine ranks are
×1.18 each (60% at the rank-up), and World Genesis adds 2% a Genesis Level (166 + Genesis Mastery ÷ 10).

```text
Might(L), L ≤ 117 = 1.30^idx × 1.30^(0.4 × stage / 8)          idx = (L − 1) div 9, stage = (L − 1) mod 9
Might(118 … 120)  = Might(117) × 1.10^(L − 117)
Might(121 … 165)  = Might(120) × 1.18^(rank + 0.6) × 1.18^(0.4 × step / 4)   rank = (L − 121) div 5, step = (L − 121) mod 5
Might(L ≥ 166)    = Might(165) × 1.30^0.6 × 1.02^(L − 166)
```

| Great realm | First Level | Might there | Step at its major |
|---|---|---|---|
| Bone Forging | 1 | 1.00 | — |
| Qi Kindling | 10 | 1.30 | ×1.17 |
| Qi Unfurling | 19 | 1.69 | ×1.17 |
| Heart Tempering | 28 | 2.20 | ×1.17 |
| Cloud Stride | 37 | 2.86 | ×1.17 |
| Spirit Awakening | 46 | 3.71 | ×1.17 |
| Heaven Glimpse | 55 | 4.83 | ×1.17 |
| Sage | 64 | 6.27 | ×1.17 |
| Sage Sovereign | 73 | 8.16 | ×1.17 |
| Will Manifest | 82 | 10.6 | ×1.17 |
| Sphere Lord | 91 | 13.8 | ×1.17 |
| Law Touching | 100 | 17.9 | ×1.17 |
| Monarch | 109 | 23.3 | ×1.17 |
| Half-Heaven Monarch, Dao Sigil, Heaven's Threshold | 118, 119, 120 | 28.5, 31.3, 34.4 | ×1.10 each |
| Inner Heaven | 121 | 38.0 | ×1.10, then ×1.18 a rank |
| World Genesis | 166 | 179 | ×1.17, then +2% a Genesis Level |

**The par character and its monsters** (the model is described in principle 3; hits are against a normal foe of the
same Level, after its defence, before crits unless marked; DPS counts crits and techniques at +60%):

| Level | Realm | Might | Attack (sheet) | Basic hit | Technique hit | Crit technique | Max HP | Normal foe HP | Elite HP | Normal foe's blow | Par DPS | CP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Bone Forging 1 | 1.00 | 12 | 12 | 12 | 17 | 83 | 46 | 277 | 7 | 33 | 21 |
| 10 | Qi Kindling 1 | 1.30 | 65 | 68 | 63 | 95 | 574 | 290 | 1,740 | 46 | 183 | 121 |
| 20 | Qi Unfurling 2 | 1.71 | 275 | 279 | 420 | 630 | 1,999 | 975 | 5,849 | 120 | 763 | 463 |
| 30 | Heart Tempering 3 | 2.26 | 803 | 832 | 1,246 | 1,869 | 5,216 | 2,910 | 17.5K | 313 | 2,299 | 1,283 |
| 45 | Cloud Stride 9 | 3.17 | 2,943 | 3,174 | 7,402 | 11.1K | 15.8K | 11.1K | 66.7K | 949 | 8,899 | 4,354 |
| 60 | Heaven Glimpse 2 | 5.15 | 10.1K | 11.0K | 39.5K | 63.2K | 46.6K | 38.6K | 232K | 2,795 | 32.0K | 14.4K |
| 72 | Sage 3 | 6.97 | 22.0K | 25.4K | 94.5K | 151K | 93.7K | 89.1K | 534K | 5,623 | 74.7K | 30.5K |
| 80 | Sage Sovereign 3 | 8.94 | 36.4K | 41.5K | 154K | 246K | 152K | 145K | 871K | 9,140 | 123K | 50.5K |
| 90 | Will Manifest 3 | 11.8 | 69.4K | 80.6K | 313K | 549K | 263K | 282K | 1.69M | 15.8K | 250K | 96.2K |
| **99** | **Sphere Lord 3** | **15.3** | **119K** | **136K** | **527K** | **922K** | **427K** | **475K** | **2.85M** | **25.6K** | **425K** | **163K** |
| 100 | Law Touching 1 | 17.9 | 148K | 179K | 726K | 1.27M | 512K | 626K | 3.76M | 30.7K | 561K | 201K |
| 108 | Law Touching 3 | 19.9 | 207K | 246K | 999K | 1.75M | 683K | 862K | 5.17M | 41.0K | 780K | 280K |
| 117 | Monarch 3 | 25.9 | 331K | 402K | 1.77M | 3.36M | 1.08M | 1.41M | 8.44M | 64.6K | 1.34M | 462K |
| 120 | Heaven's Threshold | 34.4 | 505K | 611K | 2.69M | 5.11M | 1.52M | 2.14M | 12.8M | 91.4K | 2.04M | 696K |
| 130 | Inner Heaven 2 | 48.0 | 874K | 1.04M | 4.74M | 9.01M | 2.58M | 3.63M | 21.8M | 155K | 3.51M | 1.21M |
| 150 | Inner Heaven 6 | 93.0 | 2.50M | 2.86M | 13.1M | 24.9M | 7.15M | 10.0M | 60.1M | 429K | 9.96M | 3.50M |
| 165 | Inner Heaven 9 | 153 | 5.35M | 5.95M | 27.2M | 51.7M | 15.0M | 20.8M | 125M | 897K | 21.1M | 7.55M |
| 166 | World Genesis | 179 | 6.37M | 7.07M | 32.3M | 61.4M | 17.8M | 24.7M | 148M | 1.07M | 25.1M | 8.99M |
| 200 | World Genesis (GM 340) | 351 | 21.0M | 22.0M | 100M | 191M | 56.4M | 76.9M | 461M | 3.38M | 81.5M | 30.4M |

Rules behind the monster columns:

- **Normal foe HP = 3.5 par basic hits** (never below today's value, which keeps Levels 1–10 unchanged). With the jian's
  1.6 swings a second that is about 2.2 s of basic strikes, 1.5 s with techniques.
- **Elite HP ×6**, as today (`stats.json` `mob.roles`).
- **Normal foe's blow = 6% of par max HP** (8% under Level 20), after the par character's defence; elites ×1.5 (9%);
  a boss's plain blow 15% and its markers their shares (`docs/boss_design.md` §2.1).
- **Boss HP = par DPS × par time**, replacing today's role factors for the thirteen bosses:

| Boss | Level | Par (s) | Par DPS | HP |
|---|---|---|---|---|
| Big Toad Tan | 18 | 90 | 538 | 48.4K |
| Riverbed Serpent | 25 | 120 | 1,268 | 152K |
| Drowned Abbot | 27 | 180 | 1,499 | 270K |
| The Reflection | 36 | 90 | 3,701 | 333K |
| Hollow Behemoth | 58 | 150 | 27.7K | 4.16M |
| Gate Guardian | 63 | 120 | 37.2K | 4.46M |
| Thousand-Eye Toad | 68 | 180 | 59.7K | 10.7M |
| Tomb King | 77 | 150 | 108K | 16.2M |
| Comet Captain Rao | 80 | 150 | 123K | 18.4M |
| Admiral Voss | 90 | 240 | 250K | 59.9M |
| General Kharn | 92 | 240 | 312K | 75.0M |
| Nebula Leviathan | 99 | 300 | 425K | 127M |

Elder Gu (he flees on a clock) keeps a share of his clock instead of a par.

**Against today** at the Levels asked for:

| Level | Basic hit today (reference) | Par basic hit proposed | Technique today → proposed | Normal foe HP today → proposed | Max HP today → proposed |
|---|---|---|---|---|---|
| 1 | 7 (fists) | 12 (with a weapon) | — → 12 | 46 → 46 | 96 → 96 (Might 1.0) |
| 10 | 32 (Lv 9) | 68 | — → 63 | 254 → 290 | 400 → 574 |
| 30 | 245 (Lv 31) | 832 | 336 → 1,246 | 1,552 → 2,910 | 3,266 → 5,216 |
| 60 | 555 (Lv 63) | 11.0K | 635 → 39.5K | 5,340 → 38.6K | 10,421 → 46.6K |
| 80 | 3,030 | 41.5K | 3,031 → 154K | 8,270 → 145K | 20,188 → 152K |
| 99 | 3,246 (Lv 98) | 136K | 3,647 → 527K | 12,064 → 475K | 31,243 → 427K |

Power against hours played (par basic hit at the first Level of each great realm, hours from the balance_sim):

| Hours | 0.5 | 5.4 | 11.6 | 20.8 | 31.5 | 43.7 | 56.1 | 62.3 | 105 | 140–235 |
|---|---|---|---|---|---|---|---|---|---|---|
| Level | 1 | 10 | 19 | 28 | 37 | 46 | 55 | 64 | 73 | 99 |
| Par basic hit | 12 | 68 | 252 | 713 | 1,936 | 4,062 | 8,208 | 16.9K | 30.7K | 136K |

That is ×11,000 in the first 150–250 hours, then ×44 across v1.3 and v1.4 (Level 165) and ×3.7 more by Level 200 in
v1.5. A normal foe's attack follows from the blow rule: about 51 at Level 10, 3,000 at 55, 43.9K at 99, 2.0M at 165.

### 6.3 The formula changes

```text
attack   = weapon_attack(ilv) × quality × (1 + 0.05 × enhance) × attribute scaling      (unchanged)
           × (1 + Σ attack%)                                                           (unchanged)
           × Might(realm, Level)                                                       NEW
max HP, physical defence, Qi resistance, soul defence: their bases × Might             NEW
max Qi, max Soul: unchanged (technique costs, Soul costs and regeneration stay flat or per cent)

hit      = roll(range × technique mult × grade) × (1 + 0.05·Dao + 0.08·mastery)        (unchanged)
           × Qi edge (Qi and Soul damage only)                                          CHANGED from E
           × (1 + Σ damage% + elemental power[element] + boss damage[if elite or boss]) ONE additive bucket, NEW
           × Π (1 + final damage_i)                                                     NEW, rare sources
           × element cycle × fed ground × Law step (v1.3) × attunement × realm gap      (unchanged)
           × crit (≤ ×3.0) × (1 − defence cut) × (1 − elemental resistance) × situation (unchanged)
defence cut = def / (def + (100 + 15 × attacker Level) × Might(attacker Level))        CHANGED: same-Level cuts stay
                                                                                          today's (3.7% at 1, 24.5% at 99)
monster  HP, attack, defence = par tables by Level × role × hp_mult                     CHANGED (§6.2)
CP       = HP/10 + attack × attacks a second × crit factor × 0.5 + defences/4          CHANGED: E drops out (Might is inside)
```

- **Might** replaces the energy multiplier as the realm's power step. The energy types keep a small **Qi edge** on Qi
  and Soul damage: none/Primal 1.00, True Qi 1.10 (+1% a purity grade better than 9), Sage 1.15, Law 1.20, Monarch
  1.25, Heavenforce 1.30. Physical blows lose nothing: today they took E at half, a quirk that left body cultivators and
  every basic jian strike with half of each realm's leap.
- **Damage%** gathers the sources that today have no bucket or an odd one: the sets' damage lines, titles, the named
  pieces' element (+2% each, `docs/item_plan.md` §2.1), and `elemental_power` (kept as a stat, read into the same
  bucket, still capped at 150%). **Boss damage** counts against elites and bosses only. **Final damage** is a short
  list of multiplicative sources: a natal treasure's level, a legend's gift, World Genesis Mastery.
- **Crit, hit chance, attunement, elements and situation** are ratios and need no change.
- **Realm gap** stays as it is (+25% a realm up, −20% a realm down); §7 question 3 asks whether to soften it.

### 6.4 How every bucket is fed

| Bucket | Formula place | Fed by | Par range, Level 1 → 99 → 165 |
|---|---|---|---|
| Level | weapon attack (by item Level), HP pool, attributes | Level; item Level by grade band; +1 all attributes a Level; meridians (2, 3, then 4 points a Level); Body Level; purity; Soul cultivation; Dao tiers into Insight | weapon 11 → 1,481 → 3,770; attribute scaling ×1.08 → ×2.9 → ×4.4 |
| Might | attacks, HP, defences | Realm and Level (§6.2): majors ×1.17, advanced states ×1.10, Inner Heaven ranks ×1.18, Genesis +2% | 1.0 → 15.3 → 153 |
| Gear grades | weapon and armour base | Grade band sets the item Level (`stats.json` `grade_bands`); quality 0.8–1.35; enhancement +5% a level to +10; natal +2% a level | ×1.0 → ×1.75 → ×1.95 |
| Attack% | attack | Affixes (`attack_pct` 3–8%, and the item plan's `qi_attack_pct`, `soul_attack_pct`), the sets' 6-piece +8%, Inner Arts, stances, buffs and foods | 0 → +8% → +12% |
| Damage% (with elemental power, boss damage) | one additive bucket | Sets' 2/4-piece damage lines and element lines (+10%), named pieces' element (+2% each), titles, the Law step's affinity, Kin-Bond; boss damage from Worthy Foes seals (`docs/boss_design.md` §3.11) and the Frontier's named pieces | 0 → +13% → +20%; boss +0 → +10% |
| Final damage | multiplicative list | Natal treasure level; a whole legendary chain's gift; Genesis Mastery (v1.5) | 1.0 → 1.0 → ×1.1 |
| Skill | technique multiplier | Technique multiplier 0.7–3.0 and grade (+0/10/20%); mastery +8% a tier; the technique's Dao +5% a tier; combos; the sect signature | ×1.07 (basic) → ×3.9 (par technique) |
| Crit | multiplier on a crit | Agility, Fortune, family crit, `crit` affixes, the Sword set, Killing Intent (+1% a stack); crit damage 1.5 + affixes, cap 3.0 | 10% ×1.5 → 30% ×1.75 → 43% ×2.0 |
| Qi edge | Qi and Soul damage | Energy type and purity | 1.0 → 1.15 → 1.30 |
| Pets | a separate attacker | A share of the player's attack × care × traits × rarity (`pet_authority.gd:502`), so Might reaches them through the player; `pet_damage` from the Beast set | follows the player |
| Soul Bands (v1.3) | separate attackers | Beast arts strike with `soul_attack` (Might inside) × the art's multiplier; the band's gift is Soul regeneration (`docs/soul_bands_design.md` §3.10) | follow the player |
| Daos | skill and stats | +5% a tier to its techniques; rare Daos' modifiers (attack%, damage%); tier 6 of the weapon Dao at par from Level 109 | 0 → +25% → +30% |
| Allies and treasures | separate attackers | Companions strike with 35% of the player's attack; talismans, thrown items and the sword swarm with multipliers of it | follow the player |

### 6.5 Number display

- **`UiKit.short(n)`** (new, `docs/ui_style_guide.md` §4 rule 3): under 10,000 it returns `UiKit.fmt(n)` ("9,876");
  from 10,000 it keeps three significant figures with a suffix: "18.2K", "136K", "1.27M", "12.5M", "191M", "1.20B",
  "3.40T". The suffixes live in `data/strings/en.json` (`ui.num.k`, `ui.num.m`, `ui.num.b`, `ui.num.t`) so a
  translation can use its own units (万, 亿 as KMS does, S22).
- **Damage numbers** (`world.gd:408`) go through `short`. Crits stay gold and larger. A multi-hit technique of more than
  three hits may print one total instead of each hit (a setting, off by default).
- **HUD bars** show `short` for values of 100,000 and more ("427K / 427K"); pages show `fmt` up to 9,999,999
  ("Attack 118,803") and `short` above.
- **Comparisons** in tooltips give the change in per cent and in `short` ("+12.4% · +14.7K attack").
- **Integers**: Godot's `int` is 64-bit, so the largest par figure (4.6×10^8 at Level 200) is far from any cap.
  `CombatRules.resolve` already rounds to int.
- No compression or squish is planned. If a later act needs one, divide every Might value by the same constant; the
  ratios and every test stay true.

### 6.6 Gating rules for main quests

**The rules.**

1. **Every main chapter has a Level floor**, written as a realm floor on the chapter's first quest (as today), and shown
   as a Level in the quest log. The floor is at most the Level the balance_sim reaches when the previous chapter ends
   and at least that Level minus 4.
2. **Floors only.** No main quest has a Level ceiling or expires (the Perfect World lesson).
3. **The gate says why and how.** A quest the character cannot take yet shows "Opens at Qi Kindling 6 (Level 15)" in
   the quest log, with the fastest ways to close the gap (the Keeping Post, dailies, the side quests open at that
   Level, the region's fields). The DFO Navigator is the model.
4. **The stat check stays attunement**, the Arcane Force analogue, and its material comes from the main path: the
   shards the chapter's quests and fields hand out by the time the floor is reached must cover the rooms the chapter
   sends the player to.
5. **Combat Power never gates a main quest.** It colours the room's recommended CP (green, white, orange, red) and sets
   the idle Hunt rate.
6. **Majors end chapters.** A chapter that crosses a great realm ends at the major breakthrough, which keeps its own
   requirements (pills, trials) and its zone ceiling.
7. **Catch-up** stays with Ancestral Guidance and the Account Legacy; a character more than 5 Levels under a chapter
   floor gets the chapter's daily mission at double QP until it reaches the floor.

**Chapter floors** (today's floors kept where they exist; new ones marked "new"):

| Chapter | Opens at | Level | Status |
|---|---|---|---|
| Prologue, 1 | entry trial | 0–1 | today |
| 2 | Bone Forging 4 | 4 | today |
| 3 | Bone Forging 7 (then Qi Kindling 6 for the Caravan Road) | 7 (15) | today |
| 4 | Qi Kindling 9 | 18 | today (unlock) |
| 5 | Qi Unfurling 3 | 21 | today (unlock) |
| 6 | Heart Tempering 1 (then 5, 9) | 28 (32, 36) | today |
| 7 | Cloud Stride 1 | 37 | today (unlock) |
| 8 | Spirit Awakening 2 (then 8) | 47 (53) | today |
| 9 | Heaven Glimpse 1 (then 2) | 55 (58) | today |
| 10 | Heaven Glimpse 3 | 61 | today (unlock) |
| 11 | Heaven Glimpse 3 | 61 | today |
| 12 | Sage 1 (then 2) | 64 (67) | today |
| 13 | Sage 2 | 67 | today |
| 14 | Sage 3 (then Sage Sovereign 1) | 70 (73) | today |
| 15 | Sage Sovereign 1 | 73 | today |
| 16 | Sage Sovereign 2 | 76 | new |
| 17 | Sage Sovereign 3 | 79 | today |
| 18 | Will Manifest 1 | 82 | new (today by chain only) |
| 19 | Will Manifest 2 | 85 | today (unlock) |
| 20 | Will Manifest 3 | 88 | today |
| 21 | Sphere Lord 1 | 91 | new |
| 22 | Sphere Lord 2 | 94 | new |
| 23 The Frontier Run | Sphere Lord 3 and `act3_complete` | 97 | v1.3 (`docs/world_plan.md` §3) |
| 24 Two Roads | Law Touching 1 | 100 | v1.3 |
| 25 The Empty Throne | Law Touching 3 | 106 | v1.3 |
| 26 Sun and Moon | Monarch 2 | 112 | v1.3 |
| 27 The Unwinding | Monarch 3 | 115 | v1.3 |
| 28 Seven Wells | Half-Heaven Monarch | 118 | v1.3 |
| 29 The Heavengate | Heaven's Threshold | 120 | v1.4 |
| 30 The Grey March | Inner Heaven 1 | 121 | v1.4 |
| 31 Two Roads | Inner Heaven 3 | 131 | v1.4 |
| 32 Duskwall | Inner Heaven 6 | 146 | v1.4 |
| 33 The Sky Sovereign | Inner Heaven 7 | 151 | v1.4 |
| 34 The Tide Edge | Inner Heaven 8 | 156 | v1.4 |
| Epilogue | Genesis requirements; Loose Threads at the Genesis Mastery threshold | 166+ | v1.5 |

What else gates, by act: chains everywhere; attunement for field rooms (Storm Ward 6 → 60, Endurance 20 → 90, Law
Attunement 30 → 120, Hollow Ward 50 → 200, `docs/world_plan.md`); zone ceilings for breakthroughs; story flags and
events. In v1.4 regions open by chapter and Hollow Ward, never by Inner Heaven rank (`docs/world_plan.md` §4), which
these rules keep.

### 6.7 Migration

**Data builders** (`tools/data/`, then `python3 tools/data/build_data.py`):

| File | Change |
|---|---|
| `stats.py` → `stats.json` | A `might` block (`step` 1.30, `major_share` 0.6, `advanced` 1.10, `inner_rank` 1.18, `genesis_per_level` 0.02); `energy_multiplier` becomes `qi_edge` with the values of §6.3; `mob.hp_table` and `mob.attack_table` (Levels 0–200, from the par model; the polynomials stay as the fallback and for Levels under 10); a `par` block for the balance_sim; `cp` without the energy term; `STAT_LIST` gains `damage_pct`, `boss_damage`, `final_damage` (percent, no cap); `body_path.hp_per_qi` becomes a share of max HP |
| `realms.py` → `realms.json` | Optional: a `might` column per row, if the rule reads it from data instead of computing it |
| `items.py`, `artifacts` | Banded bases at Sovereign, Will, Sphere and Law grades (`docs/item_plan.md` G1): the par character needs a weapon at every band |
| `stats.py` affixes, sets | The item plan's new affixes, plus `damage_pct` and `boss_damage` lines; the sets' damage lines into `damage_pct` |
| `enemies.py` | Boss `hp_mult` re-tuned to par times (§6.2) by `boss_suite`; `hp_override` rows checked |
| `world.py`, `rankings.json` | `recommended_cp` from the par CP at the room's middle Level; `ref_cp` replaced by the same table |
| `balance.json` | `sim_end` to `sphere_lord_3`; density and method rows for Act II and III; the `par` gear assumptions |
| `ui_strings.json` | `ui.num.*` suffixes; labels for Damage, Boss damage, Final damage |

**Rules and code** (`scripts/`):

| Where | Change |
|---|---|
| `StatRules.rebuild` | `might(realm_key, level)`; bases of the three attacks, max HP and the three defences × Might; max Qi and max Soul untouched |
| `StatRules.mob_stats` | HP and attack from the par tables × role × `hp_mult`; defences × Might(L) |
| `StatRules.combat_power` | no energy term |
| `CombatRules.resolve` | step 3 reads `qi_edge` for Qi and Soul damage only; step 5 becomes the additive bucket; a final-damage product; `defence_reduction` takes the attacker's Might |
| `CombatAuthority.player_view`, `enemy_view` | carry `damage_pct`, `boss_damage`, `final_damage`, `might`, and the role |
| `PostAuthority._fighter`, `_foe` | the same fields (the Vigil runs the S12 pipeline) |
| `ProgressionRules.energy_multiplier` | renamed `qi_edge`; its readers (CP, views, the Vigil) follow |
| Shields and conversions | Soul Lantern Ward's shield (a share of max Soul) and the Body path's HP-for-Qi, and any blood cost, become shares of max HP, or they shrink to nothing against scaled blows |
| `CalendarRules.rank_cp` | the par CP table |
| `UiKit.short`, `world.gd:408`, `hud.gd` bars, the Character page | §6.5 |

**Tests.**

| Suite | Change |
|---|---|
| `rules_tests` `rules_suite` | Level 10's 290 HP stays (the HP table keeps today's values where 3.5 par hits fall below them); its attack moves from 37 to the table's 51; add a `might_suite`: monotone, ×1.17 at each major, player and monster equal at every Level, Qi and Soul pools unscaled, same-Level defence cut unchanged |
| `balance_sim` | New checks, below |
| `boss_suite` | Measure each boss with the par character against its par (0.8–1.25 ×, `docs/boss_design.md` §2.4) |
| `data_validation` | Tables cover Levels 0–200, rise monotonically, and every `grade_bands` band has a weapon for each family |
| `valley_run` | A labelled "par up" test shortcut at each section start (quality and enhancement to par), so the run fights as the par character; the checkpoints are regenerated |

**`balance_sim` checks to add:**

1. `par_hit`: the par character built by the real rules at Levels 1, 10, 30, 60, 80, 99 (and 108, 120 once v1.3 data
   exists) within ±15% of the basic-hit target and ±20% of the technique target.
2. `ttk`: a normal foe at its own Level falls to 3–4.5 par basic hits; an elite to 18–27.
3. `blow`: a normal foe's plain blow takes 4–8% of par max HP (6–10% under Level 20); a boss's 12–18%.
4. `boss_par`: every boss's HP ÷ par DPS within 0.8–1.25 × its par.
5. `smooth`: the par basic hit rises at every Level; no Level adds under 2% or over 25%, except majors (under 30%).
6. `realm_step`: each major breakthrough raises par attack by 15–30%.
7. `cp_rec`: rooms' recommended CP within ±20% of par CP at the room's middle Level.
8. `digits`: every par figure prints in five characters or fewer through `UiKit.short`.
9. `chapter_floor`: each chapter's floor is at most the sim's Level when the previous chapter ends and at least that
   minus 4; the attunement material the path gives covers the chapter's rooms.
10. `pacing`: hours to Sphere Lord 3 against a target the user sets (§7 question 9).

**Effect on valley_run.** Time to kill and blows are held by the par tables, so the run's pacing holds if it fights as
the par character. Fought as today (Common +0 gear) it would hit at about a quarter of par at Level 98 and need about 13
blows a normal foe instead of 4, which runs into the fight caps (900 s at Admiral Voss). Hence the par-up shortcut.
The relative checks (a bound relic ×1.2 attack, the Blood Dao adds HP, bosses chipped to a share) are unaffected.
Absolute ones in `rules_tests` are listed above.

**Effect on saves.** Maxima are rebuilt from state on load (`Game.boot` calls `StatRules.rebuild`), so nothing stored
needs rescaling except the current pools: `ResourcePool.snapshot` saves absolute HP, Qi and Soul. A one-time migration
in `SaveService` sets current HP to the same fraction of the new max (Qi and Soul are unscaled). Items keep their item
Level and quality; CP, the Heaven Ranking, Vigil estimates and account summaries are recomputed; no save holds damage
totals or thresholds. The migration bumps the save's minor version so it runs once.

**Order.** After P7b's banded gear (G1) and before any v1.3 content is written in today's scale (the Soul Band and
boss examples in the design pages quote today's numbers).

### 6.8 As built (P12 · Might)

**Where it lives.** `tools/data/stats.py` holds Might (`MIGHT`, `might()`), the par character (`PAR`, `par_row()`, the
rules' formulas repeated for the builder) and the monster tables (`mob_tables()`); `stats.json` carries `might.table`,
`par` (its schedule and a table for Levels 0–200), `mob.hp_table` and `mob.attack_table`, `qi_edge` and `hp_share_cap`.
`StatRules.might_at`, `might`, `par`, `par_step` and `by_level` read them; `CombatRules.fighter` and `foe` build the
pipeline's views once for Combat, the Vigil and the probe. `balance_sim` builds the par character with the real rules
and lands within 1% of the table.

**The par character against the targets** (before crits; the real rules):

| Level | Basic (target) | Technique (target) | Crit technique | Max HP (research) | CP (research) |
|---|---|---|---|---|---|
| 1 | 12 (12) | 12 (12) | 18 | 82 (83) | 20 (21) |
| 10 | 63 (68) | 65 (63) | 97 | 589 (574) | 114 (121) |
| 30 | 847 (832) | 1,319 (1,246) | 1,978 | 5,307 (5,216) | 1,159 (1,283) |
| 60 | 10.9K (11.0K) | 38.3K (39.5K) | 61.3K | 49.5K (46.6K) | 12.8K (14.4K) |
| 80 | 41.4K (41.5K) | 154K (154K) | 269K | 163K (152K) | 47.7K (50.5K) |
| 99 | 130K (136K) | 531K (527K) | 929K (922K) | 460K (427K) | 149K (163K) |
| 108 | 241K (246K) | 1.03M (999K) | 1.79M | 738K (683K) | 272K (280K) |
| 120 (table) | 571K (611K) | 2.64M (2.69M) | 4.63M | 1.66M (1.52M) | 646K (696K) |

**What differs from §6.1–§6.7.**

1. **Bone Forging's Might** climbs only to ×1.05 over its nine Levels (the formula would give 1.11 at Level 9, 11% over
   today's numbers); the first step, at Qi Kindling 1, is ×1.30 from Bone Forging 1 (×1.24 from Level 9). Everything
   from Level 10 follows the formula.
2. **Might is a `pct_mul` modifier** on the three attacks, max HP and the three defences, so gear's flat health and
   armour scale too (most of the player's armour is gear; §6.3's "bases × Might" would have left it flat).
3. **The par schedule's steps land a Level or more past a major breakthrough**, so the breakthrough itself is the
   realm's step (checks 5 and 6): Fine from Level 10 as proposed, Superior from 40 (not 37), Perfect from 103; the
   attack affix 5% from 22, 8% from 67, 12% from 103; the sets' damage 8% from 42, 13% from 67, 20% from 124; the Sword
   Dao 1 at 15, 2 at 30, 3 at 49, 4 at 67, 5 at 85, 6 at 112; the main art's mastery 2 at 12, 3 at 21, 4 at 49, 5 at 85,
   6 at 112; crit affixes from 40, 67 and 124. Meridian points go evenly to the five channels.
4. **The par main art** is a Qi strike whose multiplier (grade included) is set by band so the technique meets the
   line of `docs/technique_plan.md` §6.1: 1.0, 1.2 from Level 19, 1.45 from 37, 1.95 at 55, easing to 1.7 by Sphere
   Lord and 1.1 by World Genesis, as mastery, the Dao, the Qi edge and Essence carry more of the ratio. P13 re-tunes it.
5. **Par health runs 0–14% above the research's** (460K at Level 99): the body meridian gate (+5% at 25 points)
   counts. The blow rule reads this table, so a blow is still 6% of it.
6. **Boss roles strike at ×2.5** a normal foe (15%; 12–13.5% with the bosses' own attack factors). Bosses without a
   par time keep their role's health factor over the table.
7. **Allies stand behind their owner's armour**: a foe's attack is set to pass armour, and a spirit animal (40% of its
   owner's health, no armour) would have taken a fifth of its health a blow at Level 99.
8. **The Soul Lantern Ward** shields 10% of max HP; **a body technique short of QI** spends the same share of max HP
   as the QI's share of max QI.
9. **`UiKit.fmt` turns to `short` from ten million**, so every page follows §6.5 without touching the pages; bars do
   so from 100,000 through `UiKit.pool_values`. Tooltip comparisons in `short` are not done.
10. **The checks** (`balance_sim`): par_hit at Level 120 waits for v1.3's weapons (a Will-grade jian carries the
    energy penalty at Monarch); ttk allows up to 5 blows under Level 20, where today's floor holds (4.6 at Level 10);
    the boss blow band is two to three normal blows (16–24% under Level 20); boss_par is a data check (the fought
    `boss_suite` of `docs/boss_design.md` is not built); smooth runs from Level 11 and realm_step allows 10–30% at the
    advanced states and Inner Heaven 1; chapter_floor measures the previous chapter's end as its highest floor or
    breakthrough objective and allows the floor to wait up to 10 Levels past it (§6.6 rule 1's "at most that Level"
    cannot hold for Act I's realm-triggered chapter openers: chapters 2–10 wait 2–10 Levels, chapter 8 the whole of
    Cloud Stride, chapter 14 three); its attunement-material half is not checked; pacing has no user target yet and
    reports 133 h to Sphere Lord 3 against the 140–235 h estimates.
11. **Main-quest gating**: rule 7's catch-up (double QP on the chapter's daily mission) is not built. Chapter 21's
    floor made The Tide Breaks and The Copperjaw Box open together; the box now follows The Tide Breaks.
12. **`damage_pct` and `boss_damage`** exist as stats; no affix rows yet (they come with the Frontier's named pieces
    and the Worthy Foes seals).
13. **valley_run's par-up** also puts the par affixes on the weapon (attack, damage%, crits) and raises the Sword Dao to
    its par tier, and the canyon side stories get more sorties.

**Measured on the valley_run checkpoints** (`tools/dev/stat_probe.gd`; hits before crits; the "before" run is the
build branch at P7b part 1, the "after" run the regenerated checkpoints with the par-up shortcut):

MEASURED_TABLE

---

## 7. Open questions, with recommendations

| # | Question | Recommendation |
|---|---|---|
| 1 | Who is "par"? The valley reference fights in Common +0 gear; par here is Superior, about +Level/12, a weapon within a band, the weapon's Dao at 5 by Will Manifest (§6.1) | Keep par as defined, and show it on the Codex's Cultivation page as "a steady cultivator at this realm" so the target is visible |
| 2 | Scale player HP with Might (symmetric), or keep HP small and make monster damage percentage-based as MapleStory does? | Symmetric. HP in the hundreds of thousands is itself a big number, and the boss markers are already shares of max HP |
| 3 | Keep the realm gap factor (+25% / −20% a realm) on top of Might? | Keep for v1.2; soften to +15% / −12% if `realm_step` shows a realm boundary inside a zone (the Act III fields span Will Manifest 3 to Sphere Lord 1) reads as a wall |
| 4 | Fold the energy multiplier into Might and keep a Qi edge of 1.0–1.3? | Yes. It also ends the half-strength rule that shortchanged physical builds |
| 5 | Put the scale in items (a Level 99 weapon shows 27K attack) or in the realm? | In the realm. It suits the genre and survives gaps in gear (G1). Item numbers keep their polynomial |
| 6 | K, M, B or the Chinese units (万, 亿)? | K, M, B in English through string keys; a Chinese translation swaps in 万 and 亿 |
| 7 | Growth past Level 166 (Genesis) | +2% a Genesis Level, reviewed with v1.5: ×2 from Might by Level 200, ×3.7 with gear and attributes, which is enough |
| 8 | Should CP gate anything? | No. Advisory colours and the idle Hunt rate only |
| 9 | Hours to Level 99: 140 h at the Sage income or 235 h at the nominal rate? | Extend the balance_sim to Sphere Lord 3 first; then the user sets the target |
| 10 | Many-hit techniques: one number or each hit? | Each hit by default; one total as a setting for techniques of more than three hits |
| 11 | Minor steps inside a realm: from Level (as proposed) or only at bottleneck taps? | From Level, so players and monsters share one curve; the major keeps its ×1.17 |
| 12 | Kill QP is 22 at every Level, so kills matter less late | Out of scope here; note for the pacing pass that re-runs the balance_sim to Sphere Lord 3 |

---

## 8. Sources

Web pages could not be opened directly: the session's egress policy blocked every page fetch (maplestorywiki.net,
fandom.com, strategywiki.org, grandislibrary.com, wikipedia.org). Facts from the web come from search-result extracts
of the pages listed. A fact from one extract counts as **M** at best; **H** needs two independent extracts that agree,
or an official page (Nexon, DFO, Flyff, IdleOn patch notes, the author's own article); **L** marks extracts that
disagreed and figures from memory. IdleOn figures come from the game data and re-implemented code in the `Morta1/IdleonToolbox` repository
(cloned for `docs/research/idle_gathering_research.md`), rated **H**. Jade River figures come from the code, the data and
the probe, rated **H**.

| # | Source | Used for |
|---|---|---|
| S1 | MapleStory Wiki, Damage Formula, https://maplestorywiki.net/w/Damage_Formula | Formula, level difference |
| S2 | MapleWiki (Fandom), Damage Formula, https://maplestory.fandom.com/wiki/Damage_Formula | Buckets, IED stacking, defence values |
| S3 | Official MapleStory forum, "How much does Final Damage matter?", https://forums.maplestory.nexon.net/discussion/24397/how-much-does-final-damage-matter | Final damage |
| S4 | Official MapleStory forum, "The progress of maple during the years", https://forums.maplestory.nexon.net/discussion/12057/the-progress-of-maple-during-the-years | 100K → 1B |
| S5 | MapleWiki (Fandom), MapleStory: Unlimited, https://maplestory.fandom.com/wiki/MapleStory:_Unlimited | 99,999,999 visual cap |
| S6 | Official MapleStory forum, "10b Damage cap resulted breaking the game' balance", https://forums.maplestory.nexon.net/discussion/23289/10b-damage-cap-resulted-breaking-the-game-balance | 10B cap, 30B lines |
| S7 | Official MapleStory forum, "Increase damage cap (At least for Hlucid)", https://forums.maplestory.nexon.net/discussion/21778/increase-damage-cap-at-least-for-hlucid | Cap and slow classes |
| S8 | KPRobin, "Arcane Force Extra Damage and Monster Damage List", https://kprobin.blogspot.com/2019/01/arcane-force-extra-damage-and-monster.html | Arcane Force 10–150%, 0–280% |
| S9 | Inven, "아케인 포스에 따른 최종 데미지 비율", https://www.inven.co.kr/board/maple/2816/646 | 10% steps above the requirement |
| S10 | Nexon (KMS) guide, 아케인포스/어센틱포스, https://maplestory.nexon.com/Guide/N23GameInformation/377408 | Arcane and Authentic Force |
| S11 | MapleStory Wiki, Seren/Monster, https://maplestorywiki.net/w/Seren/Monster | Sacred Force penalty, 6.48 quadrillion |
| S12 | MapleStory Wiki, Sacred Symbol, https://maplestorywiki.net/w/Sacred_Symbol | Cernium 50, Fallen Cernium 70/100, Level 260 |
| S13 | MapleStory Wiki, Black Mage/Monster, https://maplestorywiki.net/w/Black_Mage/Monster | 63–157.5T HP, Level 255, 1,320 ARC |
| S14 | Dexless, Black Mage guide, https://dexless.com/guides/black-mage-boss-guide-and-genesis-weapons.366/ | 9999% HP pillars |
| S15 | Games Finder, MapleStory boss ranges, https://gameslikefinder.com/article/maplestory-boss-ranges-guide/ | Zakum 12.6M, Chaos Zakum 168B, Easy Horntail 1.6B |
| S16 | MapleStory Wiki, Combat Power, https://maplestorywiki.net/w/Combat_Power | CP and party entry |
| S17 | StrategyWiki, MapleStory/Arcane River, https://strategywiki.org/wiki/MapleStory/Arcane_River | ×3 / ×10 HP, level locks |
| S18 | whackybeanz EXP tables, https://www.whackybeanz.com/calc/everything-exp/exp-tnl; MapleStory Wiki Leveling Tables, https://maplestorywiki.net/w/Experience/Leveling_Tables | EXP ranges (extracts disagreed) |
| S19 | Nexon, New Age Hyper Burning and Burning World, https://www.nexon.com/maplestory/news/87311/new-age-hyper-burning-and-burning-world; MMORPG.com Go West guide, https://www.mmorpg.com/guides/level-fast-in-maplestorys-go-west-update-everything-you-need-to-know-about-progression-and-hyper-burn-2000132171 | Hyper Burning MAX |
| S20 | AyumiLove, Potential guide, https://ayumilove.net/maplestory-potential-system-guide/; StrategyWiki Potential System | Potential tiers and % |
| S21 | DigitalTQ, Star Force guide, https://www.digitaltq.com/maplestory-star-force-guide | Star Force |
| S22 | MapleStory Wiki, Damage Skin, https://maplestorywiki.net/w/Damage_Skin; forum, "Unit Damage Skin – Decimal Issue", https://forums.maplestory.nexon.net/discussion/33343/unit-damage-skin-decimal-issue | Unit skin 1.2B / 12억 |
| S23 | NiaMeowDB, Snail, https://meowdb.com/msclassic/monsters/2; Wikibooks, MapleStory/Beginner Guide/Skills | Level 1 damage |
| S24 | Official MapleStory forum, "Sitting at 200...", https://forums.maplestory.nexon.net/discussion/26731/sitting-at-200 | Arcane Force wall |
| S25 | Official MapleStory forum, "Nerf Arcane Force (1 dmg taken at lvl 200+ is noFun)", https://forums.maplestory.nexon.net/discussion/33901 | Over-matching |
| S26 | MapleWiki (Fandom), Will/Monster, https://maplestory.fandom.com/wiki/Will/Monster | Will 560/760 ARC, 235/250 |
| S27 | MapleStory M Wiki, Character Stat Introduction, https://maplestorym-archive.fandom.com/wiki/Character_Stat_Introduction | CP in MapleStory M |
| S28 | iRO Wiki, DEF, https://irowiki.org/wiki/DEF; Sivo, physical defence, https://hub.sivo.it.com/ragnarok-online-mechanics/how-does-physical-defense-work-in-ragnarok-online/ | RO defence |
| S29 | iRO Wiki, Stats, https://irowiki.org/wiki/Stats | RO stats |
| S30 | iRO Wiki, Levels, https://irowiki.org/wiki/Levels; WarpPortal, 4th jobs announced | Level 250, trait stats |
| S31 | Ragnarok Mobile Guide, EXP and drop penalty, http://ragnamobileguide.com/experience-exp-and-drop-rate-penalty-guide/; iRO Wiki, Experience | Level-gap penalty |
| S32 | WarpPortal forum, "How Long Does It Take", https://forums.warpportal.com/index.php?/topic/85345-how-long-does-it-take/ | Time to 99 |
| S33 | Ragnarok Mobile Guide, upgrading and refining, http://ragnamobileguide.com/guide-to-upgrading-enhancing-refining-enchanting/ | ROM refine |
| S34 | Tree of Savior forum, Combat System Changes Dossier, https://forum.treeofsavior.com/t/combat-system-changes-dossier-pt-1/356990; treeofsavior.com news n=948 | ToS log formula |
| S35 | Tree of Savior forum, Experience Cards for Noobs, https://forum.treeofsavior.com/t/experience-cards-for-noobs/212722 | EXP cards |
| S36 | ElWiki, Elrianode City, https://elwiki.net/w/Elrianode_City; Elrianode Training Grounds, https://elwiki.net/w/Elrianode_Training_Grounds | CP gates |
| S37 | Elsword, 04/22 pre-announcement (CP rework), https://elsword.koggames.com/2026/04/04-22-pre-announcement/; Steam, "About damage numbers", https://steamcommunity.com/app/237310/discussions/0/1637536330473775762/ | CP rework, hiding numbers |
| S38 | DFO, Adventurer Fame, https://www.dfoneople.com/news/updates/2424/Adventurer-Fame; System update, https://www.dfoneople.com/news/updates/4388/System | Fame gates |
| S39 | DFO, Damage Compression, https://www.dfoneople.com/news/updates/2560/Damage-Compression | 1:1,000 compression |
| S40 | Vortex Gaming, DFO August 2024 balance, https://vortexgaming.io/en/postdetail/528032 | 10–15B |
| S41 | `Morta1/IdleonToolbox`: `parsers/damage.ts` (soft caps, notation), `data/website-data/monsters.json` (monster HP) | IdleOn formula and HP |
| S42 | IdleOn World 7 patch notes, https://steamdb.info/patchnotes/20697793/ | Crystal tier |
| S43 | Flyff Universe dev note v1.41, https://universe.flyff.com/news/devnote141battleformadrigal; Muran's Awakening, https://universe.flyff.com/news/muransawakeningexpansion; Madrigal Inside damage tests | Level 165, 166–190 |
| S44 | SimpleIdle, big number notation, https://www.simpleidle.com/learn/big-number-notation-explained; Soul Saver guide (Medium) | Suffix conventions |
| S45 | BladeRPG, Idle Cultivation Games 2026, https://www.bladerpg.com/en/idle-cultivation-games/ | xianxia idle reception |
| S46 | Immortal Taoists Wiki, Cultivation Realm, https://immortal-taoists.fandom.com/wiki/Cultivation_Realm | Realm structure |
| S47 | Overmortal Global Wiki, Character, https://overmortal-global.fandom.com/wiki/Character | Breakthrough pills |
| S48 | Minireview, MapleStory Idle RPG, https://minireview.io/incremental/maplestory-idle-rpg | CP paywalls |
| S49 | PWI Wiki, Level-capped Quest, https://perfectworldinternational-archive.fandom.com/wiki/Level-capped_Quest | Expiring quests |
| S50 | Perfect World Mobile Wiki, Quests, https://official-perfect-world-mobile.fandom.com/wiki/Quests | Main quest floors |
| S51 | FFXIV Wiki, Main Scenario Quests, https://ffxiv.consolegameswiki.com/wiki/Main_Scenario_Quests; Square Enix forum thread 420192 | MSQ pacing and gaps |
| S52 | Gaming News Analyst, Lost Ark 1,340–1,370, https://gamingnewsanalyst.com/2022/03/29/lost-ark-players-get-frustrated-by-the-1340-1370-item-level-gap-at-end-game/ | RNG wall |
| S53 | Warcraft Wiki, Stat squish, https://warcraft.wiki.gg/wiki/Stat_squish; PC Gamer, level squish | Squish |
| S54 | Pecorella, "The Math of Idle Games, Part I", https://www.gamedeveloper.com/design/the-math-of-idle-games-part-i; GDC Europe 2016 slides | Idle growth |
| S55 | Davide Aversa, RPG level-based progression, https://www.davideaversa.it/blog/gamedesign-math-rpg-level-based-progression/ | XP curve shapes |
| S56 | Maxroll, Diablo III Greater Rifts, https://maxroll.gg/d3/resources/greater-rifts | +17% HP a level |
| S57 | MMORPG.com, power creep editorial, https://www.mmorpg.com/editorials/how-does-power-creep-affect-mmo-games-2000130409; Massively OP, Vague Patch Notes on power creep | Power creep |
| S58 | ResetEra, "Damage Numbers in games. I hate them", https://www.resetera.com/threads/damage-numbers-in-games-i-hate-them.140961/ | Reception of numbers |
| S59 | Steam, Dungeon Fighter Online discussions on hiding damage numbers, https://steamcommunity.com/app/495910/discussions/0/2592234299560529239/ | Hiding numbers |
| S60 | StrategyWiki, MapleStory/Hyper Stats; MapleWiki SupportDesk formulas blog | Hyper Stats, link skills |

Jade River: `scripts/simulation/rules/stat_rules.gd`, `combat_rules.gd`, `progression_rules.gd`,
`scripts/simulation/authority/combat_authority.gd`, `post_authority.gd`, `pet_authority.gd`, `account_authority.gd`,
`tools/data/stats.py` (→ `stats.json`, `curves.json`, `balance.json`, `grades.json`, `affixes.json`, `sets.json`),
`data/realms.json`, `data/quests.json`, `data/unlocks.json`, `data/rooms/`, `data/zones.json`, `tests/balance_sim.gd`,
`tests/rules_tests.gd`, `tests/valley_run.gd`, `docs/cultivation_loop.md`, `docs/item_plan.md`, `docs/boss_design.md`,
`docs/world_plan.md`, `docs/ui_style_guide.md`; the probe `tools/dev/stat_probe.gd`.

## Decisions taken

The recommendations in §7 are taken (2026-09-27) so the build can be planned; the user can overturn any before it
lands. The build is roadmap phase **P12 · Might**, after P7b part 1 (the banded bases above item Level 81) and before
v1.3's content is written.
