# The cultivation loop · spec

This page states the core cultivation loop (M45–M48 in `docs/roadmap_master_ui.md`) as the code runs it at commit
4d0ab66. Every formula carries the file and lines it comes from, so a later change to either shows at once. Numbers
come from data and are tuning values. Where the code and a design page disagree, §13 lists the difference; nothing is
settled silently. §14 is the presentation rule of conflict C3 (Early, Middle, Late, Peak).

Files, by the short names used below:

| Short name | Path |
|---|---|
| `progression_rules.gd` | `scripts/simulation/rules/progression_rules.gd` (pure formulas) |
| `progression_authority.gd` | `scripts/simulation/authority/progression_authority.gd` (owns the Realm track). Since audit 45 S10 its code is in its parts under `scripts/simulation/authority/progression/`; the line numbers here are those of commit 4d0ab66 |
| `cultivator_state.gd` | `scripts/simulation/state/cultivator_state.gd` |
| `account_authority.gd`, `inventory_authority.gd`, `combat_authority.gd`, `quest_authority.gd`, `pet_authority.gd`, `companion_authority.gd`, `post_authority.gd`, `sect_authority.gd` | `scripts/simulation/authority/` |
| `requirement_rules.gd`, `unlock_service.gd`, `content_db.gd` | `scripts/core/` |
| `realms.py` | `tools/data/realms.py` (builds `data/realms.json`) |

---

## 1. The loop in one line

```text
gather Qi → the bar fills → bottleneck (surplus kept as Stored Qi)
  → minor breakthrough: a tap, no risk
  → major breakthrough: requirements, a 3 s channel, from Cloud Stride 9 a heavenly tribulation, a roll on the risk word,
    then fates on success or a failure with its cost
  → consolidation (major only) → gather Qi
```

A breakthrough only ever starts from the `start_breakthrough` intent. No offline, idle or automatic path starts one
(`progression_authority.gd:3-6`, `claim_offline` at `:1506`, `collect_idle` at `account_authority.gd:353`).

## 2. State

| Field | Meaning | Where |
|---|---|---|
| `realm_key` | The sub-level, e.g. `qi_kindling_3` | `cultivator_state.gd` |
| `state` | `accumulating`, `bottleneck` or `consolidating` | `cultivator_state.gd:11` |
| `qp` | Qi points in the current sub-level | — |
| `need()` | The sub-level's `accumulate_needed` | `cultivator_state.gd:94-95` |
| `progress_fraction()` | `clamp(qp / need, 0, 1)`; 1 when need is 0 | `cultivator_state.gd:97-99` |
| `stored_qi` | Surplus kept at a bottleneck | `cultivator_state.gd:13` |
| `consolidation_left`, `consolidation_penalty` | Seconds left after a major breakthrough; halves meditation while set | `cultivator_state.gd:14, 89` |
| `stability` | `unstable`, `settling`, `stable`, `solid`; starts `stable` | `cultivator_state.gd:34` |
| `purity` | True Qi grade 9 (worst) to 1; starts 9 | `cultivator_state.gd:18` |
| `residue`, `heart_demon` | Pill residue; the heart-demon meter 0–100 | `cultivator_state.gd:44-45` |

## 3. The ladder

Nineteen great realms. Each sub-level has a need in Qi points of `100 × T` for each Level it spans, where `T` is the
target active minutes per Level (`realms.py:93-94`, S29).

```text
need(sub-level) = Σ over its Levels of 100 × T          realms.py:113
Level(key, progress) = level + clamp(floor(clamp(progress, 0, 0.9999) × levels), 0, levels − 1)
                                                         progression_rules.gd:11-16
```

| # | Great realm | Sub-levels | Levels per sub-level | Levels | T (min per Level) | Need per sub-level (QP) | Energy | Consolidation after the major (s) | Max years (display) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | Mortal | 1 | 1 | 0 | 5 | 500 | none | — | 80 |
| 1 | Bone Forging | 9 stages | 1 | 1–9 | 12 (stage 1), 32 | 1,200; 3,200 | none; Primal Qi from stage 7 | 60 | 100 |
| 2 | Qi Kindling | 9 stages | 1 | 10–18 | 53 | 5,300 | Primal Qi | 180 | 120 |
| 3 | Qi Unfurling | 9 stages | 1 | 19–27 | 47 | 4,700 | Primal Qi | 300 | 150 |
| 4 | Heart Tempering | 9 stages | 1 | 28–36 | 67 | 6,700 | Primal Qi | 420 | 200 |
| 5 | Cloud Stride | 9 stages | 1 | 37–45 | 80 | 8,000 | True Qi | 600 | 300 |
| 6 | Spirit Awakening | 9 stages | 1 | 46–54 | 87 | 8,700 | True Qi | 900 | 500 |
| 7 | Heaven Glimpse | 3 orders | 3 | 55–63 | 100 | 30,000 | True Qi | 1,200 | 800 |
| 8 | Sage | 3 orders | 3 | 64–72 | 1,050 | 315,000 | Sage Qi | 1,800 | 1,200 |
| 9 | Sage Sovereign | 3 orders | 3 | 73–81 | 200 | 60,000 | Sage Qi | 2,400 | 2,000 |
| 10 | Will Manifest | 3 orders | 3 | 82–90 | 333 | 99,900 | Sage Qi | 3,000 | 3,000 |
| 11 | Sphere Lord | 3 orders | 3 | 91–99 | 333 | 99,900 | Sage Qi | 3,600 | 5,000 |
| 12 | Law Touching | 3 orders | 3 | 100–108 | 400 | 120,000 | Law Qi | 5,400 | 8,000 |
| 13 | Monarch | 3 orders | 3 | 109–117 | 400 | 120,000 | Monarch Qi | 7,200 | 12,000 |
| 14 | Half-Heaven Monarch | 1 | 1 | 118 | 400 | 40,000 | Monarch Qi | 7,200 | 20,000 |
| 15 | Dao Sigil | 1 | 1 | 119 | 400 | 40,000 | Monarch Qi | 7,200 | 30,000 |
| 16 | Heaven's Threshold | 1 | 1 | 120 | 400 | 40,000 | Monarch Qi | 7,200 | 50,000 |
| 17 | Inner Heaven | 9 ranks | 5 | 121–165 | 400 | 200,000 | Heavenforce | 10,800 | 100,000 |
| 18 | World Genesis | 1 | 1 | 166 | — | 0 | Heavenforce | — | without end |

Sources: `realms.py:6-22` (the table), `:87-90` (years), `:97-136` (the rows). Sage's 1,050 minutes is Act II's own
figure (`docs/act2_design.md`, Pacing); S29 gives 267.

- The step into sub-level 1 of a great realm is a **major** breakthrough; every other step is **minor**. The major
  breakthrough's spec sits on the key before it (`realms.py:139-145`), so `is_major(key)` is "this key carries a
  `major_breakthrough`" (`progression_rules.gd:289-293`).
- The three advanced states chain as majors: Monarch 3 → Half-Heaven Monarch → Dao Sigil → Heaven's Threshold
  (`realms.py:75-76, 149-152`). Inner Heaven 9 → World Genesis asks for `genesis_requirements_met` (`:153-154`).
- The energy multiplier (True Qi ×1.3 plus 2.5% per purity grade better than 9, Sage Qi ×1.7, Law Qi ×2.2, Monarch Qi
  ×2.8, Heavenforce ×3.5) scales output, not accumulation (`progression_rules.gd:399-402`, `data/stats.json:266-276`,
  read by `stat_rules.gd:387` and `combat_authority.gd:372`).

## 4. Gathering Qi

### 4.1 Meditation

```text
rate (QP per minute) = 60 × density × method_rate × stability_factor × (1 + bonus)
                         × early(Level)   decision 45's early current, x3 at Mortal tapering to x1 at Level 36
                         × 0.5      while consolidation_penalty is set
                       = 0 when no method is learned                progression_rules.gd meditation_rate
per second after a 1 s settle: apply_progress(rate / 60)           progression_authority.gd:127-134, 172-175
```

| Term | Rule | Source |
|---|---|---|
| 60 | `meditation_qp_per_min` | `data/curves.json` |
| Early current | `meditation_early`, [Level, x] points joined by straight lines: x3.0 at Level 0 and 1, x2.5 at 9, x1.8 at 18, x1.3 at 27, x1.0 from 36 (the end of Heart Tempering) on. It replaced the body stages' x0.3 (decision 45, §16) | `progression_rules.gd` `early_meditation`, `tools/data/stats.py` curves |
| `method_rate` | The method's `rate` (1.0–1.25), ×1.1 when the character's aptitude in the method's element is +0.05 or more, ×0.85 at −0.05 or less | `progression_rules.gd:41-57`, `data/methods.json` |
| `stability_factor` | Unstable 0.7, Settling 0.85, Stable 1.0, Solid 1.1 | `progression_rules.gd:34-35`, `curves.json:29-34` |
| Settle | 1 s before the first tick | `progression_authority.gd:83`, `curves.json:151-152` |
| Consolidation ×0.5 | While a major breakthrough's consolidation runs | `progression_rules.gd:65` |

Meditation stops on movement, on a hit (Qi backlash: a 1 s stun and −5% QI, `progression_authority.gd:967-970`,
`combat_authority.gd:2421-2425`), and cannot start airborne, busy, stunned or during a breakthrough
(`progression_authority.gd:74-87`). The same second also restores HP, QI and Soul at 8× their regeneration (×2 more at a
spring), refills Composure in 5 s, drains Hollowing ×3 and heart demon by 0.2 a minute, and adds purity and Soul
cultivation at 10 an hour each (`progression_authority.gd:155-191`).

### 4.2 Qi density

```text
density = room.qi_density
          + 0.5 for each gathering-formation object within its radius
          + the placed formations' qi_density effect
          × 2 within a Qi spring's radius (qi_springs unlocked, Bone Forging 7)     progression_authority.gd:95-109
```

`qi_spring_mult` is 2 (`curves.json:17`). Zone ranges: the valley 0.8–1.5 (springs 2–3), the Azure Expanse 1.2–2.0,
the Lantern Star Field 1.5–2.5 (`data/zones.json`). Offline seclusion reads only the room's own `qi_density` (§11).

### 4.3 The accumulation bonus, term by term

```text
b = stats.accumulation_rate                                           progression_authority.gd:112
if realm_index(account.highest_realm) − realm_index(own realm) ≥ 2:
    b = (1 + b) × 1.5 − 1                  Ancestral Guidance          :113-114, curves.json:132
b += 0.02 × (number of Account Legacy records)                       :115
b += pets.resonance(c)                                                :116
b += companions.paired_bonus(c)                                       :117
b −= residue_penalty                                                  :118
```

| Term | What feeds it | Source |
|---|---|---|
| `accumulation_rate` | Base 0 (`stat_rules.gd:328`). Modifiers: Qi-Gathering Incense +30% for 10 min (Granny Liu's hut from Bone Forging 1, Stoneford's store; 12 taels) and Deep Current Incense +50% for 15 min (Stoneford from Qi Kindling 1; 45 taels), one stick alight at a time (decision 45); the Sage-Born title +1%; the Fasting vow +5%; the Hungry Dantian fate +8% for the realm; Jade Carp Congee +5% for 30 min; the Qi Flow Pill +20% for 60 min (then +15 toxicity); the guqin +5% plus 10% × the playing score for 30 min | `data/titles.json`, `data/vows.json`, `data/fates.json`, `tools/data/items.py`, `tools/data/economy.py` (shops), `progression_authority.gd:1570-1580`, `data/chess.json:283-291` |
| Ancestral Guidance | ×1.5 on (1 + the stat bonus) only, for a character two great realms or more below the account's highest. The advanced states count as great realms here | `progression_authority.gd:113-114` |
| Account Legacy | +2% per great realm recorded (§12) | `:115`, `account_authority.gd:483-486` |
| Resonance | From Spirit Awakening 1: the active pet in the cultivation role gives its stage's resonance (juvenile 0.05, adult 0.1, awakened 0.2, sovereign and primordial 0.3) plus trait resonance, ×1.25 when the role is its strength, ×0.7 when hungry; a pet under an equal contract gives half | `pet_authority.gd:739-749`, `data/pet_growth.json` |
| Paired cultivation | While meditating: a Dao Companion in the room +0.25; otherwise, once paired cultivation is unlocked (Sage 1), any companion ally +0.15 | `companion_authority.gd:95-106`, `data/bonds.json:12` |
| Residue | −1% per 10 residue, at most −10%; residue does not drain on its own | `progression_rules.gd:350-352`, `data/stats.json:493-505` |

### 4.4 Every other source

| Source | Qi points | Source |
|---|---|---|
| Kill | `22 × role × gap`. Role: normal 1, elite 6, field boss 40, dungeon boss 80, story boss 40, event 0.5, trial 2. Gap by enemy Level − own Level: ≥ 5 ×1.2, ≥ −4 ×1.0, ≥ −9 ×0.5, else ×0.1. From Bone Forging 1 (`kill_progress`) | `progression_rules.gd:69-76`, `progression_authority.gd:981-982`, `curves.json:4-13`, `stats.json:277-294` |
| Training stump, dummy, lifting stone | 40 a minute of use, body stages only | `progression_authority.gd:1036-1048`, `curves.json:18` |
| Quest | A fixed number on hand-in (decision 45, §16): the kind's share (guided 15%, main 25%, side 10%, daily 5%, Act II main 8% and side 4%) of the need of the stage at the quest's own tier, set when the data is built (`quests.json` `tier`, `cultivation`), plus any `add_progress` reward's own fixed amount. A daily mission is pitched at the Level it is posted at | `story.py` `quest_tiers`, `quest_authority.gd` `cultivation_of`, `curves.json` `quest_cultivation` |
| Cores, herbs, accumulation pills | A fixed `amount` by the item's grade (decision 45, §16: the old share of the need at the middle of its grade band) × the pill factor (§9.1); the item's text says the number ("+420 cultivation") | `tools/data/items.py` `cultivation`, `inventory_authority.gd:910-916` |
| Offline seclusion | §11 | `progression_authority.gd:1515-1521` |
| Idle Seclusion and Hunt (characters not played) | §11 | `account_authority.gd:370-386` |
| The Vigil (Keeping Post) | `kill_qp × kills × 0.25` | `post_authority.gd:661-671`, `data/posts.json:140` |
| A chess problem or fortune with no Dao yet | 4 for each point of insight it would give (the hermit's 30: +120; decision 45, was 2% of the need) | `progression_authority.gd` `apply_insight_best`, `curves.json` `insight_fallback_per_point` |
| The River's dream (a once-in-a-life fortune) | +150 (decision 45, was 3% of the need) | `tools/data/living_world.py` |

### 4.5 Where the Qi goes

```text
apply_progress(amount, source, pct_of_need):                           progression_authority.gd:307-330
  amount += pct_of_need × need (a dev tool's full bar only: no content pays a share, decision 45, data_validation)
  nothing happens if amount ≤ 0 or need ≤ 0
  track the foundation (pill Qi against all Qi, this great realm)      :315, :333-342
  if state == bottleneck:
      stored_qi = min(cap, stored_qi + amount × (0.25 at the zone ceiling, else 1))
  else:
      qp += amount
      if qp ≥ need: stored_qi = min(cap, stored_qi + (qp − need)); qp = need; state = bottleneck
```

A foundation is **hollow** when more than 30% of this great realm's Qi came from pills of a resistance family, raw
herbs or cores (`progression_rules.gd:341-347`, `stats.json:493-505`).

## 5. Sub-levels and bottlenecks

- Every sub-level ends in a bottleneck: the bar stops at its need and turns gold, and the next tap opens the
  Breakthrough dialog (S06). A great realm has as many bottlenecks as sub-levels (§3).
- In the order realms (Heaven Glimpse to Monarch) the Level rises at 33% and 66% of each order with no bottleneck; in
  Inner Heaven it rises at each fifth of a rank (`progression_rules.gd:11-16`).
- After 20 minutes at a bottleneck the mentor mails a hint, once per sub-level (`progression_authority.gd:148-153`,
  `curves.json:168`).

## 6. Stored Qi and its cap

```text
cap = need × 1.0                                   progression_rules.gd:285-286, curves.json:54
at the zone ceiling (the zone's ceiling == realm_key), Stored Qi is gained at × 0.25
                                                   progression_authority.gd:302-304, 317, curves.json:55
on a breakthrough: carry = min(stored_qi, new need); stored_qi −= carry; qp = carry
                                                   progression_authority.gd:862-865
if the carry fills the new sub-level, it is at its bottleneck at once   :891-894
```

A grave wound at a bottleneck takes its loss from Stored Qi instead of the bar (§12).

## 7. Minor breakthroughs

At the bottleneck a tap sends `start_breakthrough`. It needs the bottleneck, no cooldown, no channel under way and no
room event running; there are no requirements, no risk and no roll (`progression_authority.gd:432, 441-450`). The step
calls `_advance` as a minor: the next key, the carry of Stored Qi, no consolidation and no stability change
(`:851-895`). Pills and supports play no part.

## 8. Major breakthroughs

### 8.1 Requirements

Each is a Requirement with a cause (energy, structure, understanding, material, environment). Hard ones lock the
button; soft ones add risk (`realms.py:24-82`).

| From → to | Requirements (hard unless marked soft) |
|---|---|
| Mortal → Bone Forging 1 | A method learned; body level 1 (soft). Guaranteed: no roll (`realms.py:146-147`, `progression_authority.gd:491`) |
| Bone Forging 9 → Qi Kindling 1 | Qi full (soft); body level 9 (soft); the method supports the next realm |
| Qi Kindling 9 → Qi Unfurling 1 | A technique at tier 3 (soft); body 18 (soft); Heaven's Cleansing passed; method |
| Qi Unfurling 9 → Heart Tempering 1 | Qi full (soft); body 27 (soft); method |
| Heart Tempering 9 → Cloud Stride 1 | The Heart Trial passed; a Qi Refining Pill, consumed; method |
| Cloud Stride 9 → Spirit Awakening 1 | Purity grade 6 or better; a Mind Lake Opening Pill, consumed; method |
| Spirit Awakening 9 → Heaven Glimpse 1 | A Dao at tier 4; the zone supports Heaven Glimpse; method |
| Heaven Glimpse 3 → Sage 1 | Purity grade 3 or better; a Sage Condensing Pill, consumed; the zone supports Sage |
| Sage 3 → Sage Sovereign 1 | Qi full (soft); a Dao at tier 5; method |
| Sage Sovereign 3 → Will Manifest 1 | Max Soul 1,500; the Presence Trial passed |
| Will Manifest 3 → Sphere Lord 1 | Presence level 5; a Sphere comprehension stone, consumed |
| Sphere Lord 3 → Law Touching 1 | Law affinity 1; a Law Condensing Pill and a Law Touching Pill, consumed |
| Law Touching 3 → Monarch 1 | Two Laws at affinity 3; the zone supports Monarch; a Monarch Condensing Pill (soft, consumed) |
| Monarch 3 → Half-Heaven Monarch | A Heavenly Dao insight (flag) |
| Half-Heaven Monarch → Dao Sigil → Heaven's Threshold | One, then five powers refined |
| Heaven's Threshold → Inner Heaven 1 | Seven powers refined; Qi full; a safe room; a Sigil Anchor Pill (soft, consumed) |
| Inner Heaven 9 → World Genesis | `genesis_requirements_met` |

- "Method supports" compares the method's `ceiling` with the target (`requirement_rules.gd:289-294`). The strongest
  methods end at Sage Sovereign 3, and no major after it asks for a method.
- `law_affinity_at_least` and `powers_refined_at_least` are always unmet today (`requirement_rules.gd:217-219`); v1.3
  builds them.
- The zone ceiling is a second hard lock on every major: a target above the room's zone ceiling fails with "This land
  cannot support …" (`progression_authority.gd:386-391`).

### 8.2 The risk word and the success chance

```text
index = soft_unmet + unstable + injuries − (min(supports, 3) + guard_formation + dao_companion)
        − retreat_room + heart_demon_steps − merit                         progression_authority.gd:430-431
index = clamp(index, 0, 3) → low, moderate, high, severe                  progression_rules.gd:297-299, 363-365
success = 0.95, 0.75, 0.50, 0.25 by word, + a fate's breakthrough_bonus   progression_rules.gd:367-368,
                                                                          curves.json:42-53, progression_authority.gd:468, 492
```

| Term | Rule | Source |
|---|---|---|
| `soft_unmet` | Each soft requirement unmet; a hollow foundation counts as one | `progression_authority.gd:410-413, 418` |
| `unstable` | +1 while Unstable | `:420` |
| `injuries` | +1 per untreated injury kind | `:422` |
| `supports` | −1 per bag item with a `support` block (the Cleansing Pill for Heaven's Cleansing only; the Foundation Guard Pill), at most 3. After two failed attempts at the same breakthrough they stop counting | `:395-407`, `data/items.json` (`cleansing_pill`, `foundation_guard_pill`), `stats.json:493-505` |
| `guard_formation` | −1 with a placed formation whose effect is `breakthrough_risk_step` | `:425`, `data/formations.json:42` |
| `dao_companion` | −1 with the Dao Companion in the party | `:428`, `relations_authority.gd:412-413` |
| `retreat_room` | −1 in a room flagged `retreat` | `:423` |
| `heart_demon_steps` | +1 per 25 heart demon | `progression_rules.gd:355-356` |
| `merit` | −1 once per great realm at 100 merit | `progression_rules.gd:359-361`, `:467` |

Pill quality does not enter the risk or the chance. A required pill is present or not; a support counts as one step
whatever its quality.

### 8.3 The attempt

On `start_breakthrough` for a major (`progression_authority.gd:441-472`):

1. Consumed requirement items and up to three counted supports leave the bag (`:453-461`).
2. Two or more supports add 5 heart demon (`:465-466`, `stats.json:506-515`).
3. Merit is marked used for this great realm, and a fate's `breakthrough_bonus` is spent (`:467-468`).
4. A 3 s channel starts (`CHANNEL_S`, `:8, 469-471`). A hit during it is an **interruption** failure (`:971-974`).
5. When the channel ends, a tribulation runs if the key has a row (§8.4); otherwise the roll settles it (`:474-485`).

### 8.4 Heavenly tribulation

Rows exist for the majors out of Cloud Stride 9 and every major after it (`data/tribulations.json:3-81`). The Heart
Trial stays the set piece into Cloud Stride.

```text
bolts  = row.bolts × row.waves + floor(heart_demon / 25) + floor(sin / 100) + a fate's extra bolts
                                                     progression_rules.gd:175-181, tribulations.json:83-84
damage = max_hp × 0.20 × (1 + sin / 500) × (1 + heart_demon / 200) × (0.5 if guarding)
                                                     progression_rules.gd:183-187, tribulations.json:85-88
```

| Out of | Bolts × waves |
|---|---|
| Cloud Stride 9 | 3 |
| Spirit Awakening 9 | 6 |
| Heaven Glimpse 3 | 9 |
| Sage 3 | 9 × 2 |
| Sage Sovereign 3 | 9 × 3 |
| Will Manifest 3 … Inner Heaven 9 | 9 × 4 … 9 × 11, one wave more per realm |

- Timing: the first bolt at 2 s, then 1 s of warning plus 0.7–1.4 s between bolts, 3 s between waves (breakthrough
  stream; `progression_authority.gd:524-530`, `tribulations.json:89-97`).
- Each bolt draws a ring a second early near the character (combat stream) and strikes inside radius 80, depth 45
  (`:546-560`).
- A Lightning Rod Talisman in the bag absorbs one bolt (`combat_authority.gd:230-232`).
- A bolt that would kill sets HP to 10% and ends the rite as a **bodily failure** (`combat_authority.gd:237-238`,
  `progression_authority.gd:566-569`, `tribulations.json:99`). A grave wound from a foe does the same (`:993`).
- Leaving the room is an **interruption** (`:541-543`).
- Surviving every bolt goes on to the roll (`:579-581`).

### 8.5 Success

`_settle_breakthrough` rolls on the breakthrough stream (`progression_authority.gd:488-503`). On success `_advance` as
a major (`:851-895`):

- the Level rises, and the energy type changes where the new realm's does;
- Stored Qi carries over (§6);
- consolidation starts for the realm's `consolidation_s`, the meditation rate halves while it runs, and stability becomes
  Settling (`:866-872`);
- entering True Qi forges the core (§8.7) (`:873`);
- every pill resistance count drops by one and then halves, `count = (count − 1) // 2` (`:875-880`);
- the support-failure count for this step clears, and the foundation share starts again (`:881-884`);
- the account records its highest realm and, if new, an Account Legacy record (§12), and Aunt Ping writes
  (`account_authority.gd:476-488`);
- three fate cards are offered (§8.6), except on the guaranteed first step (`:494`).

The Sovereign Settling Pill ends a consolidation at once (`progression_authority.gd:1264-1267`).

### 8.6 Fates

```text
offer 3 distinct cards, drawn by weight from the cards whose requirements pass      progression_authority.gd:764-770,
                                                                                    progression_rules.gd:193-211, fates.json:248
choose one: its effects apply now; realm modifiers last the great realm; a `next` waits  :773-785
a `next` is spent once by the next event that asks for it                           :801-808
```

The deck is twelve cards (`data/fates.json`). Two carry a `next` that feeds this loop: **Scar of Failure** (+0.10 on
the next major's success chance; the realm starts Unstable) and **Debt of Heaven** (purity one grade better; +2 bolts on
the next tribulation). **Hungry Dantian** gives +8% accumulation for the realm and +1 resistance in every pill family.

### 8.7 Core Forging

The step into Cloud Stride sets the purity grade the core forms at (`progression_authority.gd:899-915`):

```text
points: the room's element matches the method (Fire also by an earth vent); the hour matches the method's Yin or Yang;
        Composure full; residue under 0.5; a Heavenly Flame Pill within the hour     progression_rules.gd:242-259
each point met counts on a roll under 0.8
grade = max(5, 9 − counted); a flawless Heaven's Cleansing: max(4, grade − 1)        progression_rules.gd:263-267,
                                                                                    stats.json:527-542
purity = grade
```

This is where the quality of the breakthrough shapes the character's stats afterward: purity feeds the True Qi output
multiplier (§3).

### 8.8 Failure and its costs

```text
failure = weak_foundation if the foundation was hollow, else one drawn from the unmet causes, else energy_instability
                                                     progression_authority.gd:500-501, progression_rules.gd:371-380
loss    = a draw in the failure's range              progression_rules.gd:382-385, data/failures.json
qp      = need × (1 − loss); state = accumulating unless qp is still the need   progression_authority.gd:924-940
```

| Failure | Cause it answers | Progress lost | Also | Source |
|---|---|---|---|---|
| Energy instability | energy, or no unmet cause | 10–30% | Meridian injury 1 | `failures.json:5` |
| Weak foundation | structure; a hollow foundation | 20–40% | Unstable | `:18` |
| Insufficient comprehension | understanding | 10% | 300 s cooldown | `:28` |
| Bodily failure | structure; a lethal bolt | 0% | Body injury 2 | `:38` |
| Soul injury | soul (from Spirit Awakening 1) | 0% | Soul injury 2 | `:51` |
| Resource mismatch | material | 0% | Meridian injury 1 | `:65` |
| Interruption | a hit in the channel; leaving the room | 0% | Body injury 1 | `:79` |

- Consumed items are gone whatever the outcome (§8.3). A failed attempt with supports adds one to that step's
  support-failure count (`progression_authority.gd:497-498`).
- **Qi Deviation:** a failure at Severe risk, or on a method with Poor compatibility, adds 10 minutes of Qi Deviation
  (techniques strike with random elements) (`progression_rules.gd:190-191`, `progression_authority.gd:506-510`,
  `stats.json:771-780`).
- A failure never takes a realm (S05). The only planned exception is the Inner World forming (S28, v1.4).

## 9. Pills

### 9.1 Accumulation pills, cores and herbs

```text
factor = resistance × potency × (0.5 if the same item was taken within 300 s) × (0.3 if toxicity would pass tolerance)
                                                                   inventory_authority.gd:880-906
resistance = 1 / (1 + 0.25 × count); one count per 5 doses of a family; a Pill Grain slips past it
                                                                   progression_rules.gd:311-315, progression_authority.gd:351-361
potency    = quality × (1 + halo) × (1 + 0.02 × marks) × prep      inventory_authority.gd:386-390, grades.json:78-87, 133
quality    = flawed 0.5, common 1.0, fine 1.2, superior 1.4, perfect 1.6, pill grain 1.8, pill halo 2.0, pill soul 2.2
effect     = each pct, amount, value and pct_of_need × factor      inventory_authority.gd:910-916
```

- A pill two grades or more above the character's band gives nothing and a meridian injury 2
  (`inventory_authority.gd:900-905`).
- Toxicity rises by the pill's toxicity (×1.5 Flawed, ×0.5 Pill Grain); 5% of it becomes residue; toxicity over
  tolerance adds a meridian injury 1 (`progression_authority.gd:1232-1239`). Toxicity drains 1 a minute, 2 while
  meditating (`:144-147`, `stats.json:470-476`).
- Qi from a resistance family, a raw herb or a core counts toward a hollow foundation (§4.5).

### 9.2 Breakthrough pills

| Pill | Step | Kind |
|---|---|---|
| Qi Refining Pill | Heart Tempering 9 → Cloud Stride 1 | Required, consumed |
| Mind Lake Opening Pill | Cloud Stride 9 → Spirit Awakening 1 | Required, consumed |
| Sage Condensing Pill | Heaven Glimpse 3 → Sage 1 | Required, consumed |
| Sphere comprehension stone | Will Manifest 3 → Sphere Lord 1 | Required, consumed |
| Law Condensing Pill, Law Touching Pill | Sphere Lord 3 → Law Touching 1 | Required, consumed |
| Monarch Condensing Pill | Law Touching 3 → Monarch 1 | Soft, consumed |
| Sigil Anchor Pill | Heaven's Threshold → Inner Heaven 1 | Soft, consumed |
| Cleansing Pill | Heaven's Cleansing only | Support (−1 risk) |
| Foundation Guard Pill | Any major | Support (−1 risk) |
| Heavenly Flame Pill | Heart Tempering 9 → Cloud Stride 1 | A Core Forging point within the hour |
| Sovereign Settling Pill | After a major | Ends the consolidation |

No minor breakthrough uses a pill (§7, §13 F3).

## 10. Stability and consolidation

- Meditation moves stability one step toward Stable every 120 s while it is below Stable (`progression_authority.gd:
  176-180, 193-200`, `curves.json:41`). It never moves it to Solid.
- A major breakthrough sets Settling (`:870`). A method switch sets Unstable, costs 30% of the Qi in the bar (15% with a
  Method Conversion Pill) and adds 10 heart demon (`:1343-1362`, `curves.json:169-173`). Weak foundation and Scar of Failure
  set Unstable.
- Injuries heal 3× faster while meditating and 1.5× slower while Unstable; natural healing is 600, 1,800 and 3,600 s per
  severity step (`:202-220`, `curves.json:160-167`).

## 11. Seclusion, idle tasks and offline caps

### 11.1 The played character's seclusion

```text
enter_seclusion(focus): spot = this room, or the last shrine if this room is not safe;
                        density and cap are read from the room entered in           progression_authority.gd:1441-1452
cap_h = 24 with a gathering_formation room flag, 16 in a retreat room, else 12      :1501-1504, curves.json:125-127
minutes = min(elapsed / 60, cap_h × 60)                                             progression_rules.gd:388-391
Accumulate: qp = meditation_rate(room density, the bonus read at claim time) × 0.1 × minutes
                                                                                    progression_authority.gd:1515-1521,
                                                                                    curves.json:124
```

At a bottleneck the Qi goes to Stored Qi as in §4.5 (×0.25 at the zone ceiling). The paired bonus needs the character
meditating beside a companion, so it does not count offline.

| Focus | Gain over the minutes counted | Unlock |
|---|---|---|
| Accumulate | As above | Bone Forging 7 |
| Temper body | 10 body XP a minute | Bone Forging 7 |
| Heal | Injuries heal at 3× | Bone Forging 7 |
| Contemplate | 5 insight a minute in the chosen Dao | Qi Kindling 4 |
| Refine Qi | 25 purity points an hour | Cloud Stride 2 |
| Nourish soul | 20 Soul cultivation an hour | Spirit Awakening 4 |
| Settle foundation | The pill share falls 5 points an hour; 5 residue an hour; no Qi | Bone Forging 7 |
| Medicinal bath | Body XP, residue and pill share by the bath, over its hours | Qi Unfurling 1, at a Bath station |

Sources: `progression_authority.gd:1514-1558`, `curves.json:119-128`, `stats.json:493-505`. Every focus except Heal
also heals injuries at their natural rate (`:1560`).

### 11.2 Characters not being played

```text
cap_h = 12 + the Meditation Pavilion's hours                  account_authority.gd:361, sect_authority.gd:44-49
Seclusion: qp = meditation_rate(task room density, bonus + Pavilion idle rate) × 0.1 × minutes     :370-373
Hunt:      kills = 6 × clamp(CP / recommended CP, 0.2, 1.5) × 0.25 × minutes;
           qp = kill_qp × kills × 0.1 / 0.25                   :377-386
```

With Keeping Post unlocked, Hunt and Gather become posts and the Vigil (§4.4). No idle path breaks through.

## 12. Death, Ancestral Guidance and the Account Legacy

- **A grave wound** (`progression_authority.gd:989-1012`): the bar loses 10% of the need, or Stored Qi does at a
  bottleneck; from Sage 1 the soul escapes and the loss is 5% (`stats.json:463-469, 752-755`). Half the time a body
  injury 1 (never past severity 2 from defeats alone); +3 heart demon. Under a tribulation it is a bodily failure
  instead (§8.4).
- **Ancestral Guidance** (§4.3): ×1.5 on (1 + the stat bonus) while the character is two great realms or more below the
  account's highest (`progression_authority.gd:113-114`).
- **Account Legacy**: on a major breakthrough that raises the account's highest realm into a great realm not yet
  recorded, and only when the actor has the `account_legacy` unlock, the account records that great realm
  (`account_authority.gd:479-486`). Each record adds +2% to every character's bonus (`progression_authority.gd:115`).
  See F1: the unlock does not exist, so no record is ever made in normal play.

### Worked examples

A Qi Kindling 3 character on Cloudpiercing Canon (rate 1.15, Wind aptitude +0.06 so ×1.1), Stable, meditating at a Qi
spring in a 1.2 room, on the Fasting vow (+5%), with 12 residue, on an account whose highest character is in Heaven
Glimpse:

```text
density = 1.2 × 2 = 2.4;  method_rate = 1.15 × 1.1 = 1.265
bonus   = (1 + 0.05) × 1.5 − 1 − 0.01 = 0.565
early   = 2.5 + (1.8 − 2.5) × (12 − 9) / 9 = 2.267 (Level 12, decision 45)
rate    = 60 × 2.4 × 1.265 × 1.0 × 1.565 × 2.267 = 646.2 QP a minute; a 5,300 need fills in 8.2 minutes
8 h offline in the same room: density 1.2, rate 323.1, × 0.1 × 480 = 15,509 QP:
        5,300 fill the bar, 5,300 go to Stored Qi (its cap), the rest is lost
```

A major with risk: Heaven Glimpse 3 → Sage 1, all requirements met, Unstable, one injury, one Foundation Guard Pill,
30 heart demon, 120 merit unused:

```text
index = 0 + 1 + 1 − 1 − 0 + 1 − 1 = 1 → moderate → 75%
tribulation: 9 × 1 + floor(30 / 25) + 0 = 10 bolts; each 20% × 1.15 = 23% of max HP, 11.5% guarded
```

---

## 13. Findings: where the code and the design differ

| # | Finding | Evidence | Recommendation |
|---|---|---|---|
| F1 | The Account Legacy never records in normal play. The record needs the `account_legacy` unlock, and `data/unlocks.json` has no such entry, so `Unlocks.is_unlocked` is false (it is true only with `debug_force_all`). The +2% per record term is always 0 | `account_authority.gd:484`, `unlock_service.gd:18-25` | Add an `account_legacy` unlock row (account scope, Bone Forging 1, the Build Prompt's "from v0.8") in `tools/data`: a data fix. Rebuilding the records already missed from the account's highest realm needs a one-time save migration |
| F2 | Solid stability (×1.1) cannot be reached: meditation stops at Stable, and the only `set_stability` effect sets Unstable | `progression_authority.gd:196-197`, `tools/data/paths.py:110` | Either a consolidation pill that sets Solid until the next major, or drop Solid from `curves.json` |
| F3 | Conflict C4 says a pill can be required on a minor stage "in data". It cannot without code: any `major_breakthrough` spec makes the step major (a risk roll, fate cards, the resistance halving and the foundation reset). Also `realms.json:758` is the Qi Refining Pill on Heart Tempering 9 → Cloud Stride 1, a major, not a Qi Kindling stage | `progression_rules.gd:289-293`, `progression_authority.gd:448-450, 874-884` | Keep the tap (C4). If stage pills are wanted, add a `stage_requirements` list read by `query_breakthrough` for minor steps: hard requirements only, no roll, no fates |
| F4 | M48 says material quality affects the success chance. Pill quality changes a pill's potency (its Qi), never the chance; supports count one step each. Quality reaches stats through Core Forging (purity) only | §8.2, §9.1 | Record M48 as Partial on the chance. If quality should matter, one line in `query_breakthrough`: a support of Perfect quality or better counts as two steps, still within the cap of 3 |
| F5 | Seclusion reads the density and the cap of the room it is entered in, even when the spot moves to the last shrine; springs and formations are ignored offline. No room sets `gathering_formation`, so the 24-hour cap is unused until the Inner World | `progression_authority.gd:1448-1450, 1501-1504` | Read density and cap from the spot room; leave springs out on purpose (an active bonus) and say so in S07 |
| F6 | The Soul injury failure cannot be drawn: no requirement has the cause `soul`. Environment requirements are all hard, so they never reach the draw | `failures.json:51`, `realms.py:24-82` | Tag `soul_at_least` (Sage Sovereign 3) with cause `soul`, or leave the row for v1.4's Inner World forming |
| F7 | `curves.json` keys the code does not read: `failure_loss` (the ranges live in `failures.json`), `method_switch.unstable_s`, `offline_heal_mult`, and `meditation.hp_mult`, `qi_mult`, `soul_mult`, `injury_heal_mult`, `backlash_on_hit` (the ×8 comes from `stats.json:24-31`). `paired_cultivation` is read but missing, so the code's default 0.15 is the value | `curves.json:151-203`, `companion_authority.gd:105` | Remove the unread keys and add `paired_cultivation: 0.15` in `tools/data/stats.py`, so the data says what runs |
| F8 | `realm_label` shows the first Level of the sub-level, so Heaven Glimpse 2 reads "Lv 58" at 59 and 60 | `content_db.gd:135-138` | Pass the character's Level where a character is known (the band of §14 needs it too) |
| F9 | Ancestral Guidance counts the advanced states as great realms: a Monarch 3 character is "two realms behind" a Dao Sigil account | `progression_authority.gd:113` | Keep; say so in the Codex's catch-up line |

---

## 14. Presentation: Early, Middle, Late and Peak (conflict C3)

The nine sub-levels stay (C3). The four words the Master Prompt asks for are shown as **bands** of a great realm's
nine steps, with no change to `realms.json` or to any rule.

### The rule

| Step of the realm | Band |
|---|---|
| 1–3 | Early |
| 4–6 | Middle |
| 7–8 | Late |
| 9 | Peak |

"Step" means:

- in a realm of **nine stages** (Bone Forging to Spirit Awakening): the stage number;
- in a realm of **three orders** (Heaven Glimpse to Monarch): the Level's place among the realm's nine Levels, `Level −
  first Level + 1`. Order 1 is Early, order 2 Middle, the first two Levels of order 3 are Late, and its last Level
  (from 66% of order 3) is Peak;
- in **Inner Heaven** (nine ranks of five Levels): the rank;
- a realm of **one step** (Mortal, Half-Heaven Monarch, Dao Sigil, Heaven's Threshold, World Genesis) has no band.

S03 calls the three Levels inside one order "early, middle, late". Those words are not shown anywhere today, and they
are retired in favour of the bands, so each word has one meaning. The thirds of an order show as Level numbers only.

### Every great realm

| # | Great realm | Sub-levels | Bottlenecks | Early | Middle | Late | Peak |
|---|---|---|---|---|---|---|---|
| 0 | Mortal | 1 | 1 | — | — | — | — |
| 1 | Bone Forging | 9 stages | 9 | 1–3 | 4–6 | 7–8 | 9 |
| 2 | Qi Kindling | 9 stages | 9 | 1–3 | 4–6 | 7–8 | 9 |
| 3 | Qi Unfurling | 9 stages | 9 | 1–3 | 4–6 | 7–8 | 9 |
| 4 | Heart Tempering | 9 stages | 9 | 1–3 | 4–6 | 7–8 | 9 |
| 5 | Cloud Stride | 9 stages | 9 | 1–3 | 4–6 | 7–8 | 9 |
| 6 | Spirit Awakening | 9 stages | 9 | 1–3 | 4–6 | 7–8 | 9 |
| 7 | Heaven Glimpse | 3 orders | 3 | Lv 55–57 | 58–60 | 61–62 | 63 |
| 8 | Sage | 3 orders | 3 | Lv 64–66 | 67–69 | 70–71 | 72 |
| 9 | Sage Sovereign | 3 orders | 3 | Lv 73–75 | 76–78 | 79–80 | 81 |
| 10 | Will Manifest | 3 orders | 3 | Lv 82–84 | 85–87 | 88–89 | 90 |
| 11 | Sphere Lord | 3 orders | 3 | Lv 91–93 | 94–96 | 97–98 | 99 |
| 12 | Law Touching | 3 orders | 3 | Lv 100–102 | 103–105 | 106–107 | 108 |
| 13 | Monarch | 3 orders | 3 | Lv 109–111 | 112–114 | 115–116 | 117 |
| 14 | Half-Heaven Monarch | 1 | 1 | — | — | — | — |
| 15 | Dao Sigil | 1 | 1 | — | — | — | — |
| 16 | Heaven's Threshold | 1 | 1 | — | — | — | — |
| 17 | Inner Heaven | 9 ranks | 9 | Ranks 1–3 (Lv 121–135) | 4–6 (136–150) | 7–8 (151–160) | 9 (161–165) |
| 18 | World Genesis | 1 | 0 (no Qi points) | — | — | — | — |

In the nine-stage realms and Inner Heaven every band holds at least one bottleneck (the Master Prompt's "a bottleneck at
each stage"). In the order realms the bottlenecks close Early (end of order 1), Middle (end of order 2) and Peak (end of
order 3); Late has none of its own.

### Where it shows

- **The ascent** (P5b, the Cultivation page): each banded realm is drawn as its nine steps in four bands, the word beside
  its band; the current step is lit. A one-step realm is one step with no word.
- **The realm label**, where its box fits it: "Qi Kindling 3 · Early · Lv 12". The Cultivation Overview, the Character
  page, character select and the Characters page have room. The HUD badge and the menu line drop the band first when the
  label is too wide for their box.
- **The false realm** (Concealment) shows the false realm's band, so the band never gives away the true realm.
- The breakthrough text over the player (`world.gd:460`) keeps the plain label.

### Implementation note

One pure function, for example `ProgressionRules.stage_band(key, level) -> String` returning `""`, `early`, `middle`,
`late` or `peak` from the realm row's `sub`, `levels` and the great realm's first Level; four strings
(`realm.band.early` … `realm.band.peak`) in `data/strings/en.json`; and a `realm_label` variant that takes the Level
(F8). A rules test walks every key at progress 0, 0.34, 0.67 and 1.0 against the table above.

## 15. Decisions taken on the findings

| Finding | Decision |
|---|---|
| The Account Legacy never recorded (F1) | Fixed: the `account_legacy` unlock opens account-wide at Bone Forging 1 and backfills the great realms a save already reached (`legacy_suite`) |
| Pills on minor breakthroughs (conflict C4) | Keep the free tap at a minor step. A stage pill, if wanted later, needs a `stage_requirements` field read only for minor steps |
| Solid stability cannot be reached | A consolidation pill that sets Solid until the next major breakthrough, added with v1.3's content (recipe and source in `docs/item_plan.md`) |
| The old name for the step into Inner Heaven | "Ascension" alone, not the name one serial uses for its sixth realm |
| Pill quality and breakthrough odds (M48) | The roadmap overstated it: quality changes a pill's Qi and, through the Core Forging grade, stats, not the odds. M48 is marked Partial; the breakthrough pill's quality becomes a term of the risk index with v1.3 |

## 16. Decision 45: the progression numbers (after build 110)

The user played build 110: charged attacks should out-damage a basic attack; the player should have Qi when the first
technique arrives; meditation should give much more cultivation early, with systems and items that raise its speed;
quests, pills and the like should give a fixed amount of experience instead of a percentage ("that's overpowered");
three quick slots; a 50-slot bag. What changed, old → new. The charged attack and the quick slots are also in
`docs/redesign_top_down_plan.md` ("As built: decision 45").

### 16.1 Meditation's early current

`rate` gains `early(Level)` (§4.1), which replaces the body stages' ×0.3. At a 1.2 room on the par method (1.0), the
balance sim's own spot:

| Realm (Level) | Need | Old a minute | New a minute | Early current | Old minutes to fill | New minutes to fill |
|---|---|---|---|---|---|---|
| Bone Forging 1 (1) | 600 | 22 | 212 | ×2.94 | 28 | 2.8 |
| Bone Forging 2 (2) | 900 | 22 | 208 | ×2.89 | 42 | 4.3 |
| Bone Forging 4 (4) | 1,600 | 22 | 200 | ×2.78 | 74 | 8.0 |
| Bone Forging 5 (5) | 3,100 | 22 | 196 | ×2.72 | 144 | 15.8 |
| Bone Forging 7 (7) | 3,100 | 72 | 188 | ×2.61 | 43 | 16.5 |
| Bone Forging 9 (9) | 3,100 | 72 | 180 | ×2.50 | 43 | 17.2 |
| Qi Kindling 1 (10) | 5,300 | 72 | 174 | ×2.42 | 74 | 30.4 |
| Qi Kindling 9 (18) | 5,300 | 72 | 130 | ×1.80 | 74 | 40.9 |
| Qi Unfurling 9 (27) | 4,700 | 72 | 94 | ×1.30 | 65 | 50.2 |
| Heart Tempering 9 (36) | 6,700 | 72 | 72 | ×1.00 | 93 | 93 |
| Cloud Stride 1 on | | unchanged | unchanged | ×1.00 | | |

Offline seclusion and a resting character's Seclusion read the same rate (§11), so they gain the current too, still
capped at a stage and its Stored Qi. Training at a stump (40 a minute in the body stages) is now well under sitting; it
stays for the body XP.

### 16.2 Cultivation speed you can reach, and where it shows

The Cultivation page's Overview has a speed line under the bar ("Meditating here: 216 a minute · ×3.0"); a tap lists
every term of `meditation_rate` at this spot (the early current, the place, a spring, the method, stability, the
bonuses one by one with the time left on each, consolidation), their product the rate
(`ProgressionAuthority.speed_breakdown`; `rules_tests` checks the product), and the ways to cultivate faster, each lit
once it is open and greyed with the realm it opens at before that:

| Way | Speed | Reachable |
|---|---|---|
| Dense Qi (Lu's boat 1.4, a mentor's peak 1.6, hidden springs) | ×density | From the start |
| **Qi-Gathering Incense** (new) | +30% for 10 minutes | Granny Liu's hut from Bone Forging 1, Stoneford's store; 12 taels |
| Jade Carp Congee | +5% for 30 minutes | Stoneford's tea house |
| The guqin | +5% to +15% for 30 minutes | Stoneford's tea house, 450 taels |
| A Qi spring | ×2 | From Bone Forging 7 (The First Current) |
| **Deep Current Incense** (new) | +50% for 15 minutes | Stoneford's store from Qi Kindling 1; 45 taels |
| A faster method | ×1.0 to ×1.25 (×1.1 on a matching element) | Methods from Qi Kindling on |
| The Qi Flow Pill | +20% for an hour | Alchemy (the Guild's expert recipe) |
| The Fasting vow | +5% | Heart Tempering 1 (Paths) |
| A spirit animal set to Cultivate | +5% to +30% | Spirit Awakening 1 |
| Paired cultivation | +15%, +25% with a Dao Companion | Sage 1 |

The two incense sticks share one source: a new stick replaces the one alight.

### 16.3 Fixed cultivation for quests, items and events

Every quest's tier is found when the data is built (`story.py` `quest_tiers`): its own realm floor or chapter code,
the realm of the unlock that offers it and the tiers of the quests it follows, whichever is highest; with none, the
middle of its numbered chapter; then the Level of the foes it sends you to or the grade band of what it asks you to
bring. It pays its kind's share of that stage's need, rounded to two figures (`realms.round_reward`), whatever stage the
player is in at hand-in. No quest pays more than its own stage. Examples:

| Quest | Kind | Tier | Old | New |
|---|---|---|---|---|
| The Willow Path | guided | Bone Forging 1 | 15% of the player's stage, and 35% more | +90 and +210 |
| Entry Trial | guided | Bone Forging 2 | 15%, and 20% more | +140 and +180 |
| Fish-Gutting Fists | main | Bone Forging 2 | 25%, and 45% more | +230 and +410 |
| Stone and Sweat | guided | Bone Forging 5 | 15% | +470 |
| The First Current | main | Bone Forging 7 | 25% | +780 |
| First Technique | guided | Qi Kindling 1 | 15% | +800 |
| Toward Cleansing Peak | main | Qi Kindling 9 | 25% | +1,300 |
| The Bracket | guided | Cloud Stride 1 | 15% | +1,200 |
| A daily mission | daily | the Level it was posted at | 5% | 5% of that stage (+160 at Bone Forging 5) |
| The River Token's gift on accepting | main | Mortal | 98% of the stage | +430 (the last 70 are its 15 s of meditation) |

An item pays its grade's share of the need at the middle of its grade band (`items.py` `cultivation`), and its text
says the number:

| Item | Grade | Old | New |
|---|---|---|---|
| Qi Gathering Pill | common | 8% of the current stage | +420 cultivation |
| Riverreed Ginseng (10 yr), raw | common | 2.4% | +130 |
| Riverreed Ginseng (100 yr), raw | earth | 5% | +240 |
| Riverreed Ginseng (1,000 yr), raw | heaven | 10% | +800 |
| Pebble Core | common | 5% | +270 |
| Serpent Core, Guardian Stone, a low beast core | earth | 10% | +470 |
| Jade Core | heaven | 10% | +800 |
| A mid beast core | heaven | 15% | +1,200 |
| A high beast core | mystic | 20% | +6,000 |
| A peak beast core | spirit | 25% | +79,000 |
| Spirit Fruit | heaven | 8% | +640 |
| The River's dream (fortune) | — | 3% | +150 |
| A chess problem before any Dao | — | 2% | +120 (4 a point of insight) |

The pill factor (resistance, quality, the repeat window, toxicity; §9.1) still scales an item's amount.

**What stays a percentage, and why.** Every *loss* stays a share of the stage: a grave wound (10%, 5% from Sage 1), a
failed breakthrough (10–40%) and a method switch (30%, 15% with the pill). A loss is meant to cost the same share of the
bar at every realm; a fixed number would be nothing late and ruinous early. The Stored Qi cap (a stage) and the
foundation share (30% of a realm's Qi from pills) are limits, not rewards. `add_progress` keeps `pct_of_need` for the
dev tools' full bar only; `data_validation` refuses it in any content.

### 16.4 The Qi pool at the first technique

| | Old | New |
|---|---|---|
| The Qi pool opens | Bone Forging 7 (The First Current) | Bone Forging 1, with Flowing Palm (the River Token), full |
| Techniques before it | free ("breath only") | the rule stays for a technique met before any realm (none) |
| Pool at Bone Forging 1 | none | about 30 (20 + 8·Level + 0.5·Level², the method's capacity, Essence) |
| Flowing Palm's cost | 0 | 8.3 (8 × 1.04): 3.6 casts from a full pool |
| Qi regeneration, the pool under 100 | 0.75% of the pool a second (0.2 at 30) | as if the pool were 100: 0.75 a second at rest (the pool in 40 s), 6 a second meditating |
| The Qi bar and its tour | Bone Forging 7 | Bone Forging 1 |

The First Current (Bone Forging 7) now wakes the springs (the `qi_springs` unlock offers it).

### 16.5 Pacing (balance_sim)

The sim now places each quest at its own tier and pays its fixed number (it spread the unplaced side quests over Act I
before), and meditates at the early current. Every pacing row still lands within ±15%, so the targets stay:

| Realm | Target (h) | Old sim (h) | New sim (h) |
|---|---|---|---|
| Qi Kindling 1 | 5 | 5.3 | 4.8 |
| Qi Unfurling 1 | 13 | 12.6 | 12.3 |
| Heart Tempering 1 | 20 | 20.9 | 19.4 |
| Cloud Stride 1 | 30 | 31.3 | 30.0 |
| Spirit Awakening 1 | 42 | 43.7 | 43.3 |
| Heaven Glimpse 1 | 55 | 55.6 | 56.2 |
| Sage 1 (Act I's end) | 70 (65) | 60.7 | 64.5 |
| Sage Sovereign 1 | 110 | 103.5 | 105.6 |
| Sphere Lord 3 (Act III's end) | 140–235 | 133 | 164 |

The early hours move less than the meditation rate does because the sim's session sits only a quarter of the time and
its first stages are story and detours; a player who sits between fights breaks through much faster (§16.1). The
thirty-day run of the posts (V10d3) reads none of this and is unchanged (day 30: Craft Diligence 62%, Finesse ×1.86).
