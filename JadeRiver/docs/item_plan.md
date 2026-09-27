# Item plan · named gear, sets and archetypes (P7b)

This page is the plan half of P7b (`docs/roadmap_master_ui.md` §3, items M10–M12 and M33–M35). It does six things:

1. It counts the equipment that exists today, by zone, grade, slot, weapon family and archetype, with the sets, the drop
   rates and the gaps.
2. It sets the target the user chose (decision 5): named gear and sets per archetype and zone, with element and path
   tags, and gives the full list for Acts I–III and v1.3 (counts only for v1.4 and v1.5).
3. It designs six set lines, one per archetype, with bonuses at 2, 4 and 6 pieces checked against the stat scale.
4. It rebalances drop rates by grade and tier and specifies the `balance_sim` drop check.
5. It lists the sprite gaps per region and ranks a backlog for the art pipelines.
6. It orders P7b's data work and says where each change lands.

It also gives a source to each of the 43 items `data_validation` lists in `KNOWN_SOURCE_GAPS` (§2.9) and specifies the
consolidation pill that makes Solid stability reachable (§2.10, `docs/cultivation_loop.md` §13 F2 and §15).

Counts are taken from `data/` at commit 1a4e8b8 (after P7a): `artifacts.json` (142 equipment bases), `sets.json`,
`affixes.json`, `grades.json`, `loot_tables.json` (134 tables), `enemies.json` (121 foes), `data/rooms/` (the spawns),
`shops.json`, `recipes.json`, `quests.json`, `creature_art.json`. Drop rates are modelled from the loot tables and each
room's spawn mix with the rules in `LootRules` and `WorldAuthority._on_actor_defeated`. Nothing here changes data; §6
says what P7b's build changes.

Every name on this page is new and original to Jade River unless it is already in the data.

---

## 1. Today's counts

### 1.1 Equipment by slot and grade

Equipment is 142 bases in `data/artifacts.json`: 98 **banded** bases (one per family or slot per grade, rolled by
`LootRules.make_equipment`) and 44 **named** pieces (a set, a relic, a legend, a unique or a tool with a name).

| Slot | Plain | Common | Earth | Heaven | Mystic | Spirit | Sage | Sovereign | Will | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| Weapon | 9 | 10 | 10 | 13 | 18 | 9 | 11 | 0 | 2 | 82 |
| Hat | 1 | 1 | 4 | 1 | 1 | 1 | 1 | 0 | 0 | 10 |
| Robe | 1 | 2 | 4 | 2 | 1 | 1 | 1 | 0 | 0 | 12 |
| Trousers | 1 | 1 | 3 | 2 | 1 | 1 | 1 | 0 | 0 | 10 |
| Boots | 1 | 1 | 4 | 2 | 1 | 1 | 1 | 0 | 0 | 11 |
| Gourd | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 7 |
| Cape | — | — | — | — | 1 | — | — | — | — | 1 |
| Talisman | — | — | — | 1 | — | — | — | — | — | 1 |
| Furnace (tool slot) | 1 | — | 1 | 2 | 1 | — | — | — | — | 5 |
| Pet collar, talisman, saddle | — | 2 | 1 | — | — | — | — | — | — | 3 |
| **Total** | 15 | 18 | 28 | 24 | 25 | 14 | 16 | 0 | 2 | **142** |

No base exists at Sovereign grade and only four brushes and bells at Will. The grade ladder (`stats.json`
`grade_bands`) runs on to Inner Heaven (Level 165).

### 1.2 By weapon family

| Family | Dao | Banded (Training → Sunsteel) | Named | Total |
|---|---|---|---|---|
| Jian | Sword | 7 | 7 (Mudwater Cleaver, Serpent-Tongue Jian, the Moonlit and Sleeping Blades, two imitations, Riverlight Jian) | 14 |
| Gauntlets | Fist | 7 | 1 (Stone Drum Gauntlets) | 8 |
| Spear | Spear | 7 | 1 (Heron's Reach) | 8 |
| Short blade | Blade | 7 | 1 (Reedwhisper Dagger) | 8 |
| Staff | Staff | 7 | 1 (the Ferryman's Pole) | 8 |
| Heavy sabre | Blade | 7 | 1 (Mountainsplit Sabre) | 8 |
| Bow | Bow | 7 | 1 (Dragonfly Bow) | 8 |
| Fan | Fan | 7 | 1 (Seven Winds Fan) | 8 |
| Flute | Music | 7 | 1 (Crane Mourning Flute) | 8 |
| Brush | Brush | 0 | 2 (Ink-Warden's Brush, sage; Starwrit Brush, will) | 2 |
| Bell | Music | 0 | 2 (Warden's Hand-bell, sage; Tidebreak Bell, will) | 2 |

The guqin is a tool (`type: tool`, the teahouse rhythm page), not a weapon; a held guqin needs seated attack poses in
every garment first (`docs/v2_audit.md`, AGENTS.md). Every grade of a family shares one appearance.

### 1.3 By zone

A banded base belongs to the zone whose fields drop its grade (valley: Plain to Mystic; the Expanse: Spirit and Sage).
A named piece belongs to the zone of its source.

| Zone (tier, Levels) | Banded | Named | Total | Weapons | Armour | Gourd | Other slots |
|---|---|---|---|---|---|---|---|
| Jade River Valley (1, 0–63) | 70 | 31 | 101 | 51 | 35 | 5 | 10 (cape, talisman, 5 furnaces, 3 pet gear) |
| Azure Expanse (2, 55–81) | 28 | 9 | 37 | 27 | 8 | 2 | 0 |
| Lantern Star Field (3, 82–99) | 0 | 4 | 4 | 4 | 0 | 0 | 0 |

### 1.4 By archetype

A piece is tagged by the archetype it serves best. The rule, applied to every base:

| Archetype | What decides it | Families and slots |
|---|---|---|
| Body cultivator | Scales Body first or asks Body (`attribute_req`); the body ladder, knockback, HP | Gauntlets (Fist Dao), heavy sabre and staff (Body requirement), spear (Body first; no archetype of its own) |
| Sword Dao | The Sword Dao: Sword Intent, Sword Release, the swarm, natal treasure | Jian |
| Alchemist | The Poison path and weapon oils, which ride on hits (the short blade strikes fastest after fists); furnaces | Short blade, the furnace slot |
| Beast tamer | Fights at range while the animal holds the line; pet gear | Bow (the whip from v1.3), pet collar, talisman and saddle |
| Formation master | Insight and Qi; zone control; the brush writes talismans (the Confucian scripts) | Fan (until the brush), brush |
| Musician | The Music Dao: the melody aura, the bell's ring, Clear Heart Melody | Flute, bell (the guqin is a tool) |
| General | Serves every build | Banded armour and gourds, capes, the talisman slot, sets with no archetype stat |

| Archetype | Valley banded | Valley named | Expanse banded | Expanse named | Lantern named | Named total |
|---|---|---|---|---|---|---|
| Body cultivator | 20 | 0 | 8 | 4 (legends) | 0 | 4 |
| Sword Dao | 5 | 6 | 2 | 1 (legend) | 0 | 7 |
| Alchemist | 5 | 5 (furnaces) | 2 | 1 (legend) | 0 | 6 |
| Beast tamer | 5 | 3 (pet gear) | 2 | 1 (legend) | 0 | 4 |
| Formation master | 5 (fans) | 0 | 2 | 1 (legend) | 2 (brushes) | 3 |
| Musician | 5 (flutes) | 0 | 2 | 1 (legend) | 2 (bells) | 3 |
| General | 25 | 17 | 10 | 0 | 0 | 17 |

Body, formation and music have no named piece in the valley; outside the legends the Expanse has none; Act III has
the four Bastion weapons and nothing else.

### 1.5 Sets and their bonuses

| Set | Pieces | Grade, iLv | Bonuses | Obtainable today | Archetype |
|---|---|---|---|---|---|
| `jade_current` | hat, robe, trousers, boots | Earth, 27 | 2: +5% max Qi · 4: +10% Water elemental power | 1 of 4 (robe: Jade Sect Mission Hall) | General (water) |
| `cloudpiercing` | hat, robe, trousers, boots | Earth, 27 | 2: +5% move speed · 4: +10% Wind elemental power | 1 of 4 (robe: Cloud Sect Mission Hall) | General (wind) |
| `mudwater` | Mudwater Cleaver (jian), robe | Common, 18 | 2: +10% coin find | 0 of 2 | General |
| `drowned_abbot` | hat, robe, boots | Earth, 30 | 2: +10% Soul Defense · 3: +10% Qi Resistance | 1 of 3 (robe: the Drowned Abbot, every kill) | General |
| `crane` | robe, trousers, boots | Heaven, 45 | 2: +5% flight speed · 3: +10% flight speed | 0 of 3 | General |

No set can be completed. The Mudwater Cleaver is Big Toad Tan's `unique_drop`, a field no code reads. Sets are
excluded from the random roll. No set gives an archetype stat.

### 1.6 Drop rates by grade and tier

**The roll today.** Every loot table carries an `equipment` roll; a hit makes one banded base of the grade of
`clamp(foe Level ± 2, 1, 81)`, chosen at random among the grade's weapons and armour (weapons only once `weapons` is
unlocked). Quality starts at the table's minimum and steps up on one roll (`LootRules.make_equipment`): +3 steps on
5%, +2 on 15%, +1 on 30%, capped at Perfect. The zone tier changes nothing but the item level.

| Source | Tables | Equipment chance | Minimum quality | Quality spread |
|---|---|---|---|---|
| Normal foe | 69 | 3% (bandits 5–6%) | Flawed | 50% Flawed · 30% Common · 15% Fine · 5% Superior |
| A normal spawned as an elite (41 species) | — | its own roll, plus 25% (`world_authority.gd:774-777`) | Fine | 50% Fine · 30% Superior · 20% Perfect |
| Elite (role) | 17 | 25% | Fine | as above |
| Field, dungeon and story boss | 13 | 100% | Superior | 50% Superior · 50% Perfect |
| Event foe | — | 3% | Flawed | as a normal |
| Jars | 4 | 2% | Flawed | as a normal |
| Chests: valley / dungeon, Expanse, Lantern / Tomb, Wreck | 1 / 3 / 2 | 30% / 60% / 80% | Fine | as an elite |
| Spar and trial opponents, set rewards | 22 | none (`no_equipment`) | — | — |

**Gear per hour of hunting.** Modelled per field region: 6 kills a minute (`balance.json` `kills_per_min`), so 360
kills in an hour of pure hunting; each elite spawn slot gives 20 kills an hour (it respawns in 180 s); the rest are the
room's normals by their spawn counts. Averaged over the regions whose foes drop that grade.

| Grade · tier | Regions | Pieces an hour | Fine or better | Superior or better | Perfect |
|---|---|---|---|---|---|
| Plain · 1 | 4 | 14.6 | 6.1 | 2.5 | 0.79 |
| Common · 1 | 4 | 17.3 | 6.3 | 2.5 | 0.71 |
| Earth · 1 | 3 | 15.6 | 5.7 | 2.2 | 0.64 |
| Heaven · 1 | 2 | 16.9 | 8.4 | 3.7 | 1.25 |
| Mystic · 1 | 1 | 15.8 | 7.2 | 3.0 | 1.00 |
| Spirit · 2 | 3 | 15.8 | 7.2 | 3.0 | 1.00 |
| Sage · 2 | 4 | 14.5 | 5.9 | 2.4 | 0.75 |
| Sage · 3 (clamped from 82–99) | 8 | 15.6 | 7.3 | 3.1 | 1.04 |

A mixed session fights 35% of the time (`balance.json` `mix`), so it sees about 5.4 pieces an hour. The flow is the
same in every band: about one Perfect piece an hour of hunting from the first field to the last. Of a random drop,
5 bases in 13 fit one character (its family's weapon and four armour slots): 38%, 33% at Sage where the Bastion's brush
and bell join the pool.

### 1.7 The gaps

| # | Gap | Evidence |
|---|---|---|
| G1 | **No equipment above item Level 81.** `make_equipment` clamps the item Level to 81, and no armour, gourd or ordinary weapon exists at Sovereign or Will. Act III's 18 Levels (82–99, eight field regions) drop Sage gear; salvage has no Sovereign or Will row; `grades.json` has no wear level or socket count for them | `loot_rules.gd:81`, `salvage.json`, `grades.json` |
| G2 | **No set can be completed.** 13 of 16 set pieces have no source; the Mudwater Cleaver's `unique_drop` is read by nothing | `KNOWN_SOURCE_GAPS`, `enemies.py:467` |
| G3 | **No set serves an archetype.** Five sets, all in the valley, give Qi, move speed, coin find, soul defence and flight speed | `sets.json` |
| G4 | **The formation master and the bell musician have no weapon below Level 73.** Brush and bell exist only at Sage and Will (the Bastion armoury); the fan stands in | `items.py:860-870` |
| G5 | **The beast tamer's animal gets nothing after Level 27.** Three pet gear pieces (Common and Earth, crafted); no weapon family of its own until v1.3's whip | `items.py:838-842` |
| G6 | **The alchemist's furnace stops at Level 59.** Bronze, Jadeiron, Cloudsteel, the Nine-Dragon Cauldron (Heaven) and Mistjade; nothing for Acts II and III | `items.py:188-205` |
| G7 | **Slots with no upgrade across a band.** Gourds: nothing obtainable between Jadeiron (27) and Stormsteel (68), nothing after 68 (Cloud, Mistjade and Sunsteel have no source). Cape: one piece (Mystic, a quest), nothing after. Talisman: one piece (Heaven), which the slot opens at Level 46 with and never replaces. Furnace: nothing after 59. Pet gear: nothing after 27. Weapon and armour: nothing from 82 to 99 but the brush and bell at 95 | §1.1, `unlocks.json` (`cape_slot` Heaven Glimpse 1, `spirit_sense` Spirit Awakening 1) |
| G8 | **Named gear per archetype is thin and uneven** (§1.4): body, formation and music have none in the valley; the Expanse has only the legends; Act III has four weapons | §1.4 |
| G9 | **No Qi or Soul weapon affix.** `attack_pct` raises physical attack only, so the fan, flute, brush, bell and the jian's Qi arcs have no damage affix. No affix for taming, crafting, pets, arrays or the melody | `affixes.json` |
| G10 | **No element or path tag on gear** (M11) | `artifacts.json` |
| G11 | **Drops flood** (§1.6): 14.5–17.3 pieces and 2.2–3.7 Superior or better an hour of hunting, flat across bands. The quality steps are constants in `LootRules`, the elite extra roll a constant in `world_authority.gd` | `loot_rules.gd:94-98`, `world_authority.gd:774-777` |
| G12 | **Two named pieces drop on every kill.** The Rogue Cultivator (an elite that respawns every 3 minutes) always drops the Serpent-Tongue Jian; the Drowned Abbot always drops the Drowned Robe | `loot_tables.json` |
| G13 | **Named pieces still roll as ordinary drops.** P7a removed the legends and imitations from the random pool; the Serpent-Tongue Jian (Earth) and the Ink-Warden's Brush and Warden's Hand-bell (Sage) remain, so Expanse foes drop Act III's Bastion weapons | `loot_rules.gd:85-86` |
| G14 | **No repeatable boss in the valley's Heaven band** (Levels 37–54, 25 hours of play): the Drowned Abbot is Level 27 and the Gate Guardian 63 and fought once. Named pieces of that band hang on elites and the Trial Tower until P9 adds a boss | `enemies.json`, `tower.json` |

---

## 2. The target per zone

### 2.1 The rule

Per zone and per archetype, from Act I to v1.3:

- **one set of six pieces** (weapon, hat, robe, trousers, boots and a sixth slot), in the zone's longest band, with the
  weapon offered in every family the archetype uses (body: gauntlets, heavy sabre, staff, spear; formation: fan and
  brush; music: flute and bell; from v1.3 the new families join their archetype);
- **two signature pieces** in the zone's other bands, three in the valley, which spans five grades. Existing named
  pieces count toward the signatures (the legends in the Expanse, the Bastion's brushes and bells in Act III, the
  valley's jian relics and furnaces).

The sixth set slot changes by zone so every slot gets a named line: the valley's sets take the gourd, the Expanse's the
cape (open from Heaven Glimpse 1), the Lantern's the talisman slot (open from Spirit Awakening 1), the Frontier's the
gourd again.

**What a named piece is in data.** An `artifacts.json` row like a banded base (slot, grade, iLv, energy type, sockets
by grade) plus:

```json
"named": {"archetype": "sword", "element": "water", "path": "sword_dao",
          "fixed": [{"id": "penetration", "stat": "penetration", "op": "flat", "value": 0.045}]}
```

- `fixed`: one or two affixes from the archetype's pool (§3.1), rolled at the top third of the affix's range, always
  present; the quality's random affixes come on top as today.
- `element`: +2% elemental power of that element for each named piece worn (conditioned like the sets' element
  bonuses), so a full set is +12%.
- `path`: while the wearer holds that path, a set's 2-piece bonus counts double and a signature's fixed affix counts
  half again (§2.2).
- Named pieces never come from the random roll (the pool excludes `named`, `set`, `relic`, `legend`, `imitation`).
- A named piece reuses an appearance and dye already in `parts.json` (hats: headband, tied, straw, guan, weimao;
  shirts: sleeveless, vneck, cardigan, scholar, disciple; pants: martial, cuffed, loose, scholar, straight; shoes:
  boots, folded, slippers; capes: solid, tattered; dyes on shirt and pants only). Every such pair is already in the
  compatibility gallery, so AGENTS.md needs no new pose review. A weapon takes its family's appearance. The art cost
  of a named piece is its icon.

### 2.2 Element and path tags

| Archetype | Path tag | Held when | Valley element | Expanse | Lantern | Frontier |
|---|---|---|---|---|---|---|
| Body cultivator | `body_ladder` | Copper Body or higher | Earth | Thunder | Fire | Fire |
| Sword Dao | `sword_dao` | Sword Dao at Reliable Execution (tier 3) | Water | Metal | Space | Metal |
| Alchemist | `poison` | the Poison path (a poison art known) | Wood | Fire | Star | Wood |
| Beast tamer | `beast_taming` | Beast Taming Dao tier 2, or a Soul Band worn (v1.3) | Wood | Water | Star | Water |
| Formation master | `confucian` | the Confucian path; before Will Manifest 2, Formation Dao tier 3 | Earth | Earth | Space | Earth |
| Musician | `buddhist` | a vow held (the Buddhist path); or Music Dao tier 3 | Water | Wind | Metal | Life and Death |

Elements follow each zone's Laws (`zones.json` `laws`; the Frontier's worlds favour two each). Two signatures carry
the `blood` path instead (Kharn's Cinder Glaive, the Frayed-Verge Twinblades): on the Blood path their fixed affix
counts half again.

### 2.3 Counts per zone, today against target

| Zone | Named today | New named | Named target | Sets today | Archetype sets target | Banded today | New banded | Banded target |
|---|---|---|---|---|---|---|---|---|
| Act I · Jade River Valley | 31 | 56 | 87 | 5 (general) | 5 general + 6 | 70 | 19 | 89 |
| Act II · Azure Expanse | 9 | 47 | 56 | 0 | 6 | 28 | 12 | 40 |
| Act III · Lantern Star Field | 4 | 49 | 53 | 0 | 6 | 0 | 40 | 40 |
| v1.3 · Star Frontier | — | 64 | 64 | — | 6 | — | 48 | 48 |
| **Through v1.3** | **44** | **216** | **260** | **5** | **29** | **98** | **119** | **217** |
| v1.4 · Outer Heavens (outline) | — | 112 | 112 | — | 12 | — | 48 | 48 |
| v1.5 · World Genesis (outline) | — | 57 | 57 | — | 6 | — | 24 | 24 |

Equipment grows from 142 bases to 477 through v1.3 and about 720 through v1.5.

Named target per archetype and zone (sets with their weapon variants, plus signatures):

| Archetype | Valley | Expanse | Lantern | Frontier | Through v1.3 |
|---|---|---|---|---|---|
| Body cultivator | 12 (set 9, signatures 3) | 14 (set 9, signature 1, legends 4) | 11 (9 + 2) | 11 (9 + 2) | 48 |
| Sword Dao | 13 (set 6, new 1, existing 6) | 8 (6 + 1 + legend) | 8 (6 + 2) | 9 (7 + 2) | 38 |
| Alchemist | 13 (set 6, new 2, furnaces 5) | 8 (6 + 1 + legend) | 8 (6 + 2) | 9 (7 + 2) | 38 |
| Beast tamer | 12 (set 6, new 3, pet gear 3) | 8 (6 + 1 + legend) | 8 (6 + 2) | 9 (7 + 2) | 37 |
| Formation master | 10 (set 7, signatures 3) | 9 (7 + 1 + legend) | 9 (7 + 2 existing) | 10 (8 + 2) | 38 |
| Musician | 10 (set 7, signatures 3) | 9 (7 + 1 + legend) | 9 (7 + 2 existing) | 9 (7 + 2) | 37 |
| General | 17 (the five sets, cape, talisman) | 0 | 0 | 7 (Well-Warden mantles) | 24 |
| **Total** | **87** | **56** | **53** | **64** | **260** |

The sets are listed piece by piece in §3.3. The signatures follow.

### 2.4 Act I · the Jade River Valley (Levels 0–63)

Sets (§3.3): **Pilgrim-Stair** (body), **Mistcutter** (sword), **Willow-Dew** (alchemist), **Grey-Pack** (beast tamer),
**Compass-Flag** (formation), **Falls-Echo** (musician), all Heaven grade (iLv 44–49), dropping in the Crane Cliffs and
on Mist Peak, sold at the valley's halls and guilds, crafted at them, and given by the Trial Tower's floor 20.

New signatures (15). Rates are per kill; `E` marks a row rolled only by elites (§4.2).

| Archetype | Name | Slot · grade · iLv | Element | Source (rate) | What makes it the archetype's piece |
|---|---|---|---|---|---|
| Body | **Boar-Tusk Knuckles** | Gauntlets · Common · 15 | Earth | Thornback Boar, Bamboo Grove (E 5%) | Tusks lashed over the knuckles: the third punch knocks back twice as far; fixed +Body |
| Body | **Serpent-Coil Sabre** | Heavy sabre · Earth · 25 | Water | Riverbed Serpent, field boss and Beast King (20%) | Cut from the rock the serpent coils on: Sundered lasts 2 s longer; fixed +attack |
| Body | **Hollow-Antler Knuckles** | Gauntlets · Mystic · 58 | Wood | Hollow Stag, Summit Ridge (0.2%) | Grey antler over the fist: +knockback resistance and +HP; a Copper Body wears the HP twice over |
| Sword | **Roc-Quill Jian** | Jian · Mystic · 60 | Wind | Cloudpeak Roc, Summit Ridge (E 2.5%) | Long and light as a roc's flight feather: Sword Release reaches 25% further; fixed +penetration |
| Alchemist | **Viper-Fang Dirk** | Short blade · Common · 13 | Wood | Green Viper, Bamboo Grove (E 5%) | A fang set in a bone grip: viper oil takes on 30% of hits instead of 20% |
| Alchemist | **Abbot's Medicine Gourd** | Gourd · Earth · 27 | Water | the Drowned Abbot (25%) | The Abbot's own: +toxicity tolerance, and pills from quick-use restore 10% more |
| Beast tamer | **Marsh-Hunter's Bow** | Bow · Common · 11 | Water | Greyfin, Reed Marsh (E 5%) | Strung with otter gut: +pet damage; the animal strikes first at what you shot |
| Beast tamer | **Serpent-King Collar** | Pet collar · Earth · 25 | Water | Riverbed Serpent (20%) | Worn by your animal: +12% HP and the King's water resistance |
| Beast tamer | **Roc-Plume Saddle** | Pet saddle · Mystic · 60 | Wind | Cloudpeak Roc (0.2%) | A mount wearing it carries you 15% faster and glides off ledges |
| Formation | **Chalkline Brush** | Brush · Common · 16 | Earth | Old Scribe Bai's first talisman lesson (quest reward) | The scribe's first brush: the talismans it writes last 1 s longer |
| Formation | **Talisman-Ghost Veil** | Hat (weimao) · Earth · 25 | Earth | Paper Talisman Ghost, Drowned Shrine (0.2%) | Paper strips sewn into the brim: +array power, fixed +Insight |
| Formation | **Wisp-Mirror Fan** | Fan · Mystic · 58 | Water | Trial Tower floor 30, first clear (10% later) | Its launch writes a binding talisman on the foe it lifts; fixed +Qi attack |
| Musician | **Marsh-Reed Flute** | Flute · Common · 12 | Water | Greyreed Hamlet trader (taels, Qi Kindling 5) | Cut from Greyreed's tallest reed: the melody reaches 20% further |
| Musician | **Sunken-Chime Bell** | Bell · Earth · 27 | Water | Drowned Acolyte, Drowned Shrine (0.2%) | A chime from the drowned temple: each ring seals a foe's Qi for 0.5 s |
| Musician | **Soulbell Circlet** | Hat (tied) · Mystic · 59 | Wood | Weeping Lantern, Mist Peak (0.2%) | Woven with soulbell petals: +soul attack; the melody confuses 4% more often |

Existing valley named pieces kept: the Mudwater Cleaver, Serpent-Tongue Jian, Moonlit and Sleeping Blades and their
imitations (sword); the five furnaces (alchemist); the Bone Collar, Scale Talisman and Reed Saddle (beast tamer); the
five general sets, the Mistjade Cape and the Cloud Talisman (general).

### 2.5 Act II · the Azure Expanse (Levels 64–81)

Sets (§3.3): **Stormhide** (body, Spirit, iLv 68), **Azure Fin** (beast tamer, Spirit, 72), **Kite-String** (musician,
Sage, 76), **Sandking Seal** (formation, Sage, 77), **Amber-Sting** (alchemist, Sage, 78), **Riven-Sky** (sword, Sage, 79).

New signatures (6); the nine legends count as the other.

| Archetype | Name | Slot · grade · iLv | Element | Source (rate) | What makes it the archetype's piece |
|---|---|---|---|---|---|
| Body | **Snow-Ape Mantle** | Cape (solid) · Spirit · 70 | Water | Snow Ape, Rimefrost Heights (E 2.5%) | A white hide over the shoulders: +knockback resistance, and cold slides off |
| Sword | **Harpy-Crest Band** | Hat (tied) · Sage · 76 | Wind | Canyon Harpy, Gale Canyons (E 2.5%) | A russet crest bound at the brow: +crit, and Sword Intent fades 1 s slower |
| Alchemist | **Mirror-Eye Cauldron** | Furnace · Spirit · 70 | Water | Thousand-Eye Toad, field boss (20%) | A named furnace: band +0.12, ten pills a batch, Water pills +5% quality |
| Beast tamer | **Thunderhorn Harness** | Pet saddle · Spirit · 67 | Thunder | Thunderhorn Rhino (0.2%) | A mount wearing it tramples small foes it runs through |
| Formation | **Storm-Ward Compass** | Talisman · Spirit · 68 | Wind | Herder Suo's quest on the Thunderhorn Plains | A lodestone that points into the wind: Array Plates hold 20% longer; +2 Storm Ward |
| Musician | **Frost-Lynx Flute** | Flute · Spirit · 70 | Water | Frost Lynx, Rimefrost Heights (E 2.5%) | Every third melody pulse freezes a slowed foe for 0.5 s |

### 2.6 Act III · the Lantern Star Field (Levels 82–99)

Sets (§3.3): **Driftsilk** (alchemist, Sovereign, 86), **Wyrm-Cradle** (beast tamer, Sovereign, 88), **Orbitwright**
(formation, Will, 92), **Cinder-Palisade** (body, Will, 94), **Watchbell** (musician, Will, 95), **Nightcurrent** (sword,
Will, 96).

New signatures (8); the Bastion's Ink-Warden's Brush, Starwrit Brush, Warden's Hand-bell and Tidebreak Bell are the
formation master's and musician's (they leave the random pool, G13).

| Archetype | Name | Slot · grade · iLv | Element | Source (rate) | What makes it the archetype's piece |
|---|---|---|---|---|---|
| Body | **Broadside Knuckles** | Gauntlets · Sovereign · 88 | Fire | Pirate Gunner, Blackmast Haven (E 2.5%) | Hand-cannon brass over the fist: +knockback resistance; blows shove a foe one step further |
| Body | **Kharn's Cinder Glaive** | Spear · Will · 92 | Fire | Restored at the Bastion armoury from three of Kharn's glaive shards and two pyre embers | The Ashborn general's glaive, relit: +attack, burning ground where the third thrust lands; Blood path tag |
| Sword | **Flagship Jian** | Jian · Sovereign · 90 | Metal | Admiral Voss (25%) | Voss's parade blade: Sword Intent starts at 2 stacks in a Presence clash |
| Sword | **Lantern-Heart Jian** | Jian · Will · 98 | Fire | The Flame Heart's ledge chest, Lantern Heart (15%) | Lit from the first lantern: the flying sword leaves a burn |
| Alchemist | **Pyre-Keeper's Furnace** | Furnace · Will · 93 | Fire | Ashborn Pyre Keeper, Ashen Reach (E 2.5%) | A named furnace that never cools: band +0.14, twelve pills a batch, Fire pills +5% quality |
| Alchemist | **Powder-Horn Gourd** | Gourd · Sovereign · 88 | Fire | Pirate Gunner (0.2%) | A gunner's horn turned pill gourd: throwables +20% damage, +toxicity tolerance |
| Beast tamer | **Hatchling's Nest Collar** | Pet collar · Will · 92 | Star | "The Last Egg" (Wyrmnest Isles), quest reward | Woven from the nest the last egg lay in: +15% HP; a star-tier animal +10% damage |
| Beast tamer | **Comet-Sparrow Bow** | Bow · Sovereign · 85 | Fire | Comet Sparrow (0.2%) | Fletched with comet plumes: arrows trail sparks; fixed +pet damage |

### 2.7 v1.3 · the Star Frontier (Levels 100–120)

Sets (§3.3), all Sphere grade (iLv 104) and each obtainable on both roads (`docs/world_plan.md` §3): **Magmaback** (body),
**Ironbark** (sword), **Drowned-Bloom** (alchemist), **Twin-Leash** (beast tamer), **Root-Lattice** (formation),
**Barrow-Choir** (musician). v1.3's four new families join their archetypes (open question 1): dual blades to the Sword
Dao, the rope dart to the alchemist, the whip to the beast tamer, the umbrella to the formation master.

New signatures (12) and the Seven Wells' mantles (7, general):

| Archetype | Name | Slot · grade · iLv | Element | Source (rate) | What makes it the archetype's piece |
|---|---|---|---|---|---|
| Body | **Throne-Weight Knuckles** | Gauntlets · Law · 113 | Life and Death | the Remnant Monarch (25%) | They carry a little of the Monarch's Weight: blows press a foe's Will; +knockback resistance |
| Body | **Sunroc Mantle** | Cape (solid) · Law · 114 | Fire | Sun Roc, Twinlight Marches (E 2.5%) | Gold-barred plumes: +HP; Unbroken's shield +4% of max HP |
| Sword | **Hour-Between Jian** | Jian · Law · 116 | Space | The Hour Between's chest (eclipse only, 25%) | Forged in the moment sun and moon cross: Sword Intent does not fade for 3 s after a kill |
| Sword | **Frayed-Verge Twinblades** | Dual blades · Law · 115 | Space | Hollowed Legionnaire, the Unwinding (E 2.5%) | Two blades that were one before the Tide: +penetration; Blood path tag |
| Alchemist | **Timekeeper's Censer** | Furnace · Law · 115 | Time | Timekeeper Gong Yi's quest (Monarch 3) | A named furnace: a batch finishes 25% sooner; band +0.16 |
| Alchemist | **Shade-Serpent Rope Dart** | Rope dart · Law · 112 | Water | Shade Serpent, Twinlight Marches (E 2.5%) | Its dart is a serpent's fang: poison on a pulled foe; fixed +crit damage |
| Beast tamer | **Radiant-Lion Whip** | Whip · Law · 113 | Fire | Radiant Lion, Twinlight Marches (E 2.5%) | A lash of lion mane: +pet damage; the animal roars when you crack it |
| Beast tamer | **Moon-Moth Saddle** | Pet saddle · Law · 112 | Water | Moon Moth, Twinlight Marches (0.2%) | A mount wearing it flies at night side speed in the day and glides further |
| Formation | **Contest-Floor Parasol** | Umbrella · Law · 112 | Metal | The throne contest, won (Throne-Sworn) | The canopy the contest's judge sat under: an Array Plate opened under it lasts 20% longer |
| Formation | **Ledger-Vault Seal** | Talisman · Law · 118 | Metal | Hollow Elder Gu (25%) | The seal Gu stamped his ledger with: +array power; foes inside an array take Vulnerable |
| Musician | **Eclipse Bell** | Bell · Law · 114 | Space | The eclipse set piece, Twinlight Marches (reward) | Rung at the crossing: its ring flips the favoured Law's bonus to you for 3 s |
| Musician | **Moonfen Flute** | Flute · Law · 111 | Water | Moon Moth (E 2.5%) | Cut from moonfen reed: the melody heals allies 0.5% more a second |
| General | **Greenwood, Ember, Loam, Brightsteel, Coldspring, Shade and Noon Well-Warden's Mantles** | Cape · Law · 119 | one each (Wood, Fire, Earth, Metal, Water, Yin, Yang) | Each Element Warden (30%) | +10% resistance and +6% elemental power of its element |

### 2.8 v1.4 and v1.5 in outline

| Version | Bands | Sets | Signatures | Other | Named | Banded |
|---|---|---|---|---|---|---|
| v1.4 · Outer Heavens (121–165) | Monarch, Inner Heaven | 12: two per archetype, one per band, split across the two roads (Front road, River road) with sources on both | 18: three per archetype | 4 Relic World relics (general, one per world) | 112 | 48 (two grades of 20, pet gear, furnaces) |
| v1.5 · World Genesis (166+) | one (Genesis) | 6: one per archetype, from the Unwoven Shore and the Grey Loom | 12: two per archetype | memory rooms drop echoes of earlier named pieces at the player's Level (a rule, no new bases) | 57 | 24 |

### 2.9 Banded bases to add

| Addition | Bases | Zone | Why |
|---|---|---|---|
| Brush and bell at Training, Iron, Jadeiron, Cloudsteel, Mistjade, Stormsteel and Sunsteel | 14 | valley, Expanse | G4: every archetype has a family from Level 1. The weapon sheets exist (v1.2), so this is data and icons |
| Sovereign grade (weapons in eleven families, four armour slots, a gourd): **Driftsteel** weapons, **Starsilk** armour, **Driftglass Gourd** | 16 | Act III | G1 |
| Will grade: **Lanternsteel** weapons, **Lanternsilk** armour, **Lantern Gourd** | 16 | Act III | G1 |
| Pet collar, talisman and saddle at every grade from Earth (collar, saddle) and Common (talisman) to Will, crafted at the forge from each zone's beast parts | 3 + 6 + 6 + 6 = 21 in Acts I–III, 6 in v1.3 | all | G5 |
| Furnaces at Spirit, Sage, Sovereign and Will (smithing, as the Jadeiron to Mistjade ones) | 4, and 2 in v1.3 | Acts II–III | G6 |
| Sphere and Law grade in fifteen families (with v1.3's four), four armour slots and a gourd; names from v1.3's ores (proposed: **Orchardsteel** and **Thronesteel**) | 40 | v1.3 | the Frontier's bands |

With the Sovereign and Will bases: `grades.json` gains wear levels (Sovereign 82, Will 91, Sphere 100, Law 109) and
sockets (3 each); `salvage.json` gains Sovereign (2 driftglass, 20 essence) and Will (1 pyre ember, 24 essence) rows;
`grade_colors` gains Law, Monarch and Inner Heaven (colours from P4's palette rules, no red).

### 2.10 Sources for the 43 unsourced items

The P7a scan lists 43 items nothing hands out (`tests/data_validation.gd` `KNOWN_SOURCE_GAPS`, `docs/wiki/items.md`). Each
gets one source here; P7b's data work adds it and removes the item from the list.

| Item | Source | Where, rate or price | Lands in |
|---|---|---|---|
| `metal_core_low`, `metal_core_mid`, `metal_core_high` | The Core Exchange's stock: "cores from beasts of far places" | Hermit Yao, Reed Marsh; two a day each; 4, 12 and 32 Spirit Stones (four times what the exchange pays) | `economy.py` (the `hermit` shop) |
| (later, the natural source) | New metal beasts: the Dust-Mane Jackal (Caravan Road, rank 2), the Iron-Quill Shrike (Crane Cliffs, rank 4–5), the Bronze-Crest Eagle (Summit Ridge, rank 7) | the beast-core roll, 2% a rank | sprite backlog §5.3, ranks 2 and 6 |
| `star_core_low`, `_mid`, `_high`; `space_core_low`, `_mid`, `_high` | Lanternfall goods (Peddler Ning): for star-tier animals hatched young | Harbor Market, from Will Manifest 1; two a day each; 1, 3 and 8 Sage Crystals | `economy.py` (`lanternfall_goods`) |
| `soul_core_high` | Rare loot rows | Weeping Lantern 3%, Mirror Wisp 2% (Mist Peak) | `enemies.py` |
| `soul_core_peak` | Rare loot row | Terracotta Warden 3% (Tomb of Sunscar) | `enemies.py` |
| `wood_core_peak` | A wild **Stormgrass Stag** (wood, Levels 64–68) on the existing `cloud_stag` sheet, in the Stormgrass Verge and Thunderhorn Flats; the core roll gives 16% at rank 8 | two spawn slots, one of them elite | `enemies.py` (the row), `world.py` (spawns); no new art |
| `spirit_stone_high` | Achievement reward; auction lot; chest rows | "Sovereign of Sages" (reach Sage Sovereign 1) gives 1; Nine Peaks auction (weight 0.4, start 90); `chest_tomb` and `chest_wreck` rare 5% | `economy.py`, `enemies.py` |
| `beast_bag_mist` | Hermit Yao's Beast Hall | 6,000 taels, from Heaven Glimpse 1 (the Reed, Hide and Cloud bags already sell there) | `economy.py` |
| `beast_bag_star` | The Herders' Camp (Herder Suo), Thunderhorn Plains | 160 Spirit Stones, from Sage 1 | `economy.py` |
| `hour_incense_2` | Daily activity chest at 40 points | +1 | `living_world.py` (activity) |
| `hour_incense_4` | Activity chest at 60 points | +1 | `living_world.py` |
| `hour_incense_12` | Activity chest at 100 points | +1 | `living_world.py` |
| `hour_incense_24` | Trial Tower guardian floors 15, 20, 25 and 30, first clear; the valley auction | +1 each; lot weight 0.8, start 12 Spirit Stones | `living_world.py` (a `tower_guardian` table), `economy.py` |
| `hour_incense_72` | Nine Peaks auction; Expanse chests | lot weight 0.5, start 40; `chest_expanse` rare 3% | `economy.py`, `enemies.py` |
| `wandering_incense` | Valley auction; Expanse and Lantern chests | lot weight 0.3, start 20 Spirit Stones; `chest_expanse` rare 2%, `chest_lantern` rare 3% | `economy.py`, `enemies.py` |
| `iron_snare_kit` | Smithing recipe (known by default, as the other post tools) | jadeiron ×3, hemp cord ×6, boar hide ×2 | `economy.py` recipes (from `posts.py` `KITS`) |
| `silk_snare_kit` | Smithing recipe | mystic ore ×2, kite silk ×3, bronze rivet ×4 | same |
| `star_snare_kit` | Smithing recipe | driftglass ×2, jelly silk ×3, star shard ×10, whetstone ×2 | same |
| `jade_rite_tablet` | Smithing recipe | jadeiron ×2, spirit wood ×3, cinnabar ×2 | same (from `TABLETS`) |
| `cloud_rite_tablet` | Smithing recipe | cloudsteel ore ×2, spirit wood ×3, soul wax ×1, bronze rivet ×4 | same |
| `star_rite_tablet` | Smithing recipe | driftglass ×2, spirit wood ×3, sky ink ×2, star shard ×10 | same |
| `cloud_gourd` | Stoneford Smith's stock | from Cloud Stride 1, taels at the usual price | `economy.py` |
| `mistjade_gourd` | Stoneford Smith, from Heaven Glimpse 1; Cloudgate Port peddler | taels; Spirit Stones | `economy.py` |
| `sunsteel_gourd` | Ironroot Clan smith, beside the other Sunsteel pieces | Spirit Stones | `economy.py` |
| `jade_current_hat`, `_boots` | Jade Sect Mission Hall | contribution, Inner Disciple (as the robe) | `economy.py` |
| `jade_current_trousers` | Jade Sect Mission Hall | contribution, Core Disciple, so the 4-piece asks the higher rank | `economy.py` |
| `cloudpiercing_hat`, `_boots`, `_trousers` | Cloud Sect Mission Hall | as the Jade Current pieces | `economy.py` |
| `mudwater_cleaver` | Big Toad Tan's loot table (the dead `unique_drop` field goes) | 25% a kill | `enemies.py` |
| `mudwater_robe` | Lieutenant Kuai (elite), Mudwater Hideout | 5% | `enemies.py` |
| `drowned_hat` | Drowned Acolyte, Drowned Shrine | 0.2% | `enemies.py` |
| `drowned_boots` | Rogue Cultivator (elite), Drowned Shrine | 2.5% | `enemies.py` |
| `crane_robe` | "Crane Falls at Dawn", quest reward | once | `story.py` |
| `crane_trousers` | Cloudpeak Roc, Summit Ridge | 0.2% | `enemies.py` |
| `crane_boots` | Achievement "Cloud Stepper" (the Cloud Steps inside the gold par) | once | `economy.py` (achievements) |

### 2.11 The Bedrock Pill (the consolidation pill)

Solid stability (×1.1 on meditation) cannot be reached today: meditation stops at Stable and the only `set_stability`
effect sets Unstable (`docs/cultivation_loop.md` §13 F2). The decision (§15) is a pill that sets Solid until the next
major breakthrough.

| | Value |
|---|---|
| Name, id | **Bedrock Pill**, `bedrock_pill` |
| Text | "Hot root and cold lotus, taken together, and the foundation stops moving. Stability becomes Solid until your next major breakthrough." |
| Grade, realm band | Heaven grade (iLv 45); usable from Cloud Stride 1 (Level 37), when the core has formed, at any later realm |
| Effect | `set_stability` with `word: solid`. Taken only while stability is Stable and no consolidation runs (so it never stands in for the Sovereign Settling Pill). Solid holds until a major breakthrough sets Settling, or a method switch, a weak foundation or a Scar of Failure sets Unstable, as the rules already do. Meditation never moves Solid, since it only climbs toward Stable |
| Pill data | family none (exempt from lifetime resistance); toxicity 12; group utility; cause structure; mark `gate` |
| Recipe (alchemy, Heaven, 900 s, element earth) | Principal: Riverreed Ginseng (100 yr) ×1 (hot) · Minister: Mist Lotus (100 yr) ×1 (cold) · Assistant: Soulbell Flower ×1 (neutral) · Envoy: Willow Moss ×2 (neutral). A hot and a cold herb together hold the Extraction band still, which is the pill's idea. Every herb's roles allow its slot (`items.py` `HERB_NATURE`) |
| Sources | The recipe scroll at the Alchemist Guild, Stoneford: 1,200 taels, the guild's Adept flag and Cloud Stride 1. The pill ready-made at the Condensing Hall (Alchemist Fen, the Expanse): 12 Spirit Stones, from Sage 1. With v1.3, the Keep Market in Lodestar Keep for Law Crystals |
| Lands | With v1.3's content: the item and recipe (`items.py` `pills()`, `economy.py` `recipes()`), the shop rows (`economy.py`), and the effect's `solid` word and its use gate (`game_authority.gd:175`, `progression_authority.gd` `apply_stability`) |
| Pacing | Meditation is a quarter of the mixed session, so Solid is about +2.5% on the whole. `balance.json` keeps `stability: stable`; the pill is an option, not the path |
| Tests | `rules_tests`: the pill refused at Settling, Unstable or in consolidation; Solid kept through meditation; Solid ended by a major, a method switch and a weak-foundation failure; the ×1.1 read by the meditation rate |

---

## 3. New sets

### 3.1 The six set lines

Each archetype has one line of four sets (tier I valley, II Expanse, III Lantern, IV Frontier). The 2- and 4-piece
bonuses are the same at every tier; the 6-piece mechanic grows by tier. The sets' pieces carry fixed affixes from the
archetype's pool.

| Line | 2 pieces | 4 pieces | 6 pieces (I / II / III / IV) | On the path |
|---|---|---|---|---|
| **Body cultivator** (Pilgrim-Stair, Stormhide, Cinder-Palisade, Magmaback) | +5% max HP | +8% Physical Defense; +10% knockback resistance | +8% Physical Attack. **Unbroken**: a blow that would take you below 30% HP raises a shield of 10 / 12 / 14 / 16% of max HP for 5 s, once a minute | Copper Body or higher: the 2-piece counts double (+10% HP) |
| **Sword Dao** (Mistcutter, Riven-Sky, Nightcurrent, Ironbark) | +2% crit chance | +4% penetration | +8% Qi Attack. **Honed Intent**: Sword Intent holds 2 / 2 / 3 / 3 more stacks and fades half as fast | Sword Dao tier 3: +4% crit |
| **Alchemist** (Willow-Dew, Amber-Sting, Driftsilk, Drowned-Bloom) | +20% toxicity tolerance | +6% crafting control; +6% crafting perception | +8% Physical Attack. **Venom Hand**: the Poison Body opens at 35% of tolerance, not 50%; oils take on 25 / 28 / 31 / 34% of hits, not 20% | The Poison path: +40% tolerance |
| **Beast tamer** (Grey-Pack, Azure Fin, Wyrm-Cradle, Twin-Leash) | +5% taming chance | +10% pet damage | +8% Physical Attack (pets inherit it). **Kin-Bond**: your active animal takes 15% less damage, and each Soul Band you wear adds 1 / 1.5 / 2 / 2.5% pet damage | Beast Taming Dao tier 2: +10% taming chance |
| **Formation master** (Compass-Flag, Sandking Seal, Orbitwright, Root-Lattice) | +5% Qi Attack | +15% array power | +8% Qi Attack. **Living Array**: foes inside your Array Plate's ring take the talisman your brush writes (binding: root 1 s; killing: Sundered; guard: Qi Seal 1 s) once each; rings 15 / 20 / 25 / 30% wider | The Confucian path (Formation Dao tier 3 before Will Manifest 2): +10% Qi Attack |
| **Musician** (Falls-Echo, Kite-String, Watchbell, Barrow-Choir) | +5% soul attack | +15% melody power | +8% soul attack. **Sustained Note**: the melody's first 3 s cost no Composure, and it heals allies 1 / 1.25 / 1.5 / 1.75% more a second | A vow held, or Music Dao tier 3: +10% soul attack |

**New stats** (`stats.py` `STAT_LIST`, percent, no cap): `pet_damage` (read with the pet trait sum in
`pet_authority.gd:498`), `array_power` (Array Plate duration and the killing array's damage, read by the
`deploy_array` effect), `melody_power` (the melody's slow and heals, the bell's ring and Clear Heart Melody). The six
mechanics are set-bonus `flag` rows (like the meridian gates' flags), read by the rule that owns each mechanic.

**Affix pools.** New affixes (`affixes.json`); the first five also join the random pools, the rest are named-only:

| Affix | Slots | Stat | Range | Random pool |
|---|---|---|---|---|
| `qi_attack_pct` | weapon | Qi Attack, % | 3–8% | yes (G9) |
| `soul_attack_pct` | weapon, hat | soul attack, % | 3–8% | yes (G9) |
| `essence` | robe, hat | Essence | 1–4, +0.1 a Level | yes |
| `knockback` | robe, boots | knockback resistance | 3–8% | yes |
| `max_soul_pct` | hat, robe | max Soul, % | 3–7% | yes |
| `taming` | hat, gourd | taming chance | 2–5% | no |
| `craft_control` | hat, gourd | crafting control | 2–5% | no |
| `pet_damage` | weapon, gourd | pet damage | 3–8% | no |
| `array_power` | weapon, gourd, talisman | array power | 5–12% | no |
| `melody_power` | weapon, gourd, talisman | melody power | 5–12% | no |

| Archetype | Fixed affixes on its named pieces (by slot) |
|---|---|
| Body | weapon `attack_pct`; hat `body`; robe `hp_pct` or `knockback`; trousers `body`; boots `knockback`; gourd `toxicity_tolerance`; cape `hp_pct` |
| Sword | weapon `penetration` or `qi_attack_pct`; hat `crit`; robe `essence`; trousers `agility`; boots `move_speed`; sixth slot `crit` (hat pool) or `essence` |
| Alchemist | weapon `crit_damage`; hat `craft_control`; robe `essence`; trousers `agility`; boots `evasion`; gourd `toxicity_tolerance`; furnace none (its furnace stats) |
| Beast tamer | weapon `pet_damage`; hat `taming`; robe `hp_pct`; trousers `agility`; boots `evasion`; gourd `taming` |
| Formation | weapon `qi_attack_pct`; hat `insight`; robe `essence`; trousers `tenacity`; boots `evasion`; gourd or talisman `array_power` |
| Musician | weapon `melody_power` or `soul_attack_pct`; hat `soul_attack_pct`; robe `max_soul_pct`; trousers `tenacity`; boots `evasion`; gourd or talisman `melody_power` |

### 3.2 Scale check

Each line's direct damage from the full set is +13% (+5% and +8%, the sword's crit and penetration about the same), and
defence lines stay under +10%. The rule: **a full set at its band's middle is worth less than the step to the next
band's middle at the same quality**, so the next grade's banded gear replaces it and sets never block progression.

Weapon attack is `8 + 3·iLv + 0.12·iLv²` and armour defence `4 + 1.5·iLv + 0.05·iLv²` (`stats.json` `equipment`).

| Tier | Set iLv | Weapon attack | Next band's middle | Weapon step | Armour step | Set's direct line | Share of the step |
|---|---|---|---|---|---|---|---|
| I · valley | 44 (Heaven) | 372 | 603 (Mystic, 59) | +62% | +60% | +13% | 0.21 |
| II · Expanse | 77 (Sage) | 951 | 1,154 (Sovereign, 86) | +21% | +21% | +13% | 0.62 |
| III · Lantern | 95 (Will) | 1,376 | 1,618 (Sphere, 104) | +18% | +17% | +13% | 0.72 |
| IV · Frontier | 104 (Sphere) | 1,618 | 1,910 (Law, 114) | +18% | +18% | +13% | 0.72 |

Against the other gifts in the build:

| Gift | Value |
|---|---|
| Quality Fine → Perfect | +18% on every base stat |
| A legendary weapon's gift | +6–8% of one stat (+4% crit, +12% crit damage) |
| An affix | `attack_pct` 3–8%, `crit` 1–3%, `penetration` 2–5%, `hp_pct` 3–7% |
| Dao tier 1 with its family | +3% attack |
| Copper Body, Iron Body | +5% Physical Defense; +10% knockback resistance |
| Jade Current 4-piece (today) | +10% Water elemental power |
| A named piece's element | +2% elemental power each, +12% for six |

Caps hold with every bonus stacked: a Level 95 sword build reaches about 40% crit (cap 75%) and 29% penetration at full
Honed Intent (cap 40%); a body build's knockback resistance reaches about 55% with Iron Body, the 4-piece and two
`knockback` affixes (cap 90%); taming chance stays under its 90% cap. Unbroken's shield (10–16% of max HP, once a
minute) sits under the Iron Wall Talisman's 20% for 6 s. Kin-Bond's band clause is live once Soul Bands land in v1.3
(`docs/soul_bands_design.md`); the Frontier's Twin-Leash at seven bands gives +17.5% pet damage, inside the 60–90%
share of a comparable technique that Soul Bands are tuned to.

### 3.3 The sets, piece by piece

Rates are per kill (`E`: rolled only by elites; bosses on every kill). "Tower 20" is the Trial Tower's floor 20
(Level 42): its first clear gives the boots of the valley set of the archetype you wield (by weapon family), later
clears 10%. Weapons marked with several families drop in the family you wield, or the first one listed.

#### Act I · the valley (sixth piece: gourd)

**Pilgrim-Stair** (body · Heaven · iLv 44 · Earth · `body_ladder`). The Iron Body is tempered on the Pilgrim Stairs.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Pilgrim-Stair Knuckles · Cleaver (heavy sabre) · Staff · Pike (spear) | family's | Cliff Ape, Crane Cliffs (E 2.5%; a new elite slot) | Worn smooth by the stair's railings; fixed +attack |
| Hat | Pilgrim-Stair Headband | headband | Jade Sentinel, Mist Peak (0.2%) | A sweat-band of rope; fixed +Body |
| Robe | Pilgrim-Stair Vest | sleeveless (earth) | Forge Guild shop, Stoneford (taels, Copper Body) | Bare arms for the stair; fixed +HP% |
| Trousers | Pilgrim-Stair Wraps | martial (ochre) | Iron Body temper trial, first pass | Bound tight at the shin; fixed +Body |
| Boots | Pilgrim-Stair Boots | boots | Tower 20 | Iron-shod for the thousand steps; fixed +knockback |
| Gourd | Pilgrim-Stair Gourd | — | Forge Guild recipe: guardian stone ×4, cloudsteel ore ×2, ape fur ×2 | Holds bone broth; fixed +toxicity tolerance |

**Mistcutter** (sword · Heaven · iLv 46 · Water · `sword_dao`).

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Mistcutter Jian | sword | Stormwing Hawk, Crane Cliffs (E 2.5%) | Thin enough to part the mist without stirring it; fixed +penetration |
| Hat | Mistcutter Crown | guan | Mirror Wisp, Mist Peak (0.2%) | Silver pins that catch the light before a strike; fixed +crit |
| Robe | Mistcutter Robe | vneck (cloud) | Jade and Cloud Mission Halls (contribution, Inner Disciple) | Cut for the wide sword stance; fixed +Essence |
| Trousers | Mistcutter Trousers | cuffed (indigo) | Stormwing Hawk (E 2.5%) | Cuffed so nothing catches on the lunge; fixed +Agility |
| Boots | Mistcutter Boots | folded | Tower 20 | Soft-soled for the plum-blossom poles; fixed +move speed |
| Gourd | Mistcutter Gourd | — | Forge Guild recipe: mirror dust ×3, cloudsteel ore ×2, storm feather ×2 | A whetstone rides in its stopper; fixed +crit |

**Willow-Dew** (alchemist · Heaven · iLv 48 · Wood · `poison`).

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Willow-Dew Dirk | dagger | Weeping Lantern, Mist Peak (E 2.5%) | A groove along the blade holds oil for thirty strikes; fixed +crit damage |
| Hat | Willow-Dew Veil | weimao | Weeping Lantern (0.2%) | Gauze against the furnace smoke; fixed +crafting control |
| Robe | Willow-Dew Robe | scholar (jade) | Alchemist Guild shop (taels, Adept) | Pockets for every herb in a recipe; fixed +Essence |
| Trousers | Willow-Dew Trousers | scholar (earth) | Weeping Lantern (E 2.5%) | Stained to the knee with dew and ash; fixed +Agility |
| Boots | Willow-Dew Slippers | slippers | Tower 20 | Quiet on a pharmacy's boards; fixed +evasion |
| Gourd | Willow-Dew Gourd | — | Alchemist Guild recipe scroll (smithing): soul wax ×2, cloudsteel ore ×2, Mist Lotus (100 yr) ×1 | Keeps pills cool and potent; fixed +toxicity tolerance |

**Grey-Pack** (beast tamer · Heaven · iLv 47 · Wood · `beast_taming`).

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Grey-Pack Bow | bow | Mist Wolf, Mist Peak (E 2.5%) | Strung with wolf sinew, loud enough for a pack to hear; fixed +pet damage |
| Hat | Grey-Pack Hat | straw | Mist Wolf (0.2%) | A wide brim the animal knows from far off; fixed +taming |
| Robe | Grey-Pack Coat | cardigan (earth) | Hermit Yao's Beast Hall (taels, Cloud Stride 1) | Smells of the stable; fixed +HP% |
| Trousers | Grey-Pack Leggings | loose (jade) | Cloudwing Crane, Crane Cliffs (E 2.5%) | Loose for running beside a mount; fixed +Agility |
| Boots | Grey-Pack Boots | boots | Tower 20 | Muffled soles for the hunt; fixed +evasion |
| Gourd | Grey-Pack Gourd | — | Hermit Yao's recipe: mist pelt ×3, cloudsteel ore ×2, hound fang ×2 | Carries treats and bonding offerings; fixed +taming |

**Compass-Flag** (formation · Heaven · iLv 49 · Earth · `confucian`). A formation kit is chalk, a compass and flags.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Compass-Flag Fan · Brush | family's | Rogue Mirror Adept, Mist Peak (elite, 2.5%) | Ribs marked with the compass points; fixed +Qi Attack |
| Hat | Compass-Flag Guan | guan | Jade Sentinel (0.2%) | A needle stands in the crown; fixed +Insight |
| Robe | Compass-Flag Robe | scholar (ink) | Formation Guild shop (Array Master Ren, taels) | Chalk dust in every seam; fixed +Essence |
| Trousers | Compass-Flag Trousers | straight (indigo) | Rogue Mirror Adept (2.5%) | Pockets for flags; fixed +tenacity |
| Boots | Compass-Flag Boots | folded | Tower 20 | Soles that pace an array's radius; fixed +evasion |
| Gourd | Compass-Flag Gourd | — | Formation Guild recipe: mirror dust ×2, blank plate ×2, cloudsteel ore ×2 | Holds spare array plates; fixed +array power |

**Falls-Echo** (musician · Heaven · iLv 45 · Water · `buddhist`). Crane Falls sounds a note no one plays.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Falls-Echo Flute · Bell | family's | Cloudwing Crane (E 2.5%) | Tuned to the falls' own note; fixed +melody power |
| Hat | Falls-Echo Band | tied | Mirror Wisp (0.2%) | A ribbon that trembles with the melody; fixed +soul attack |
| Robe | Falls-Echo Robe | disciple (white) | Stoneford Tea House (Auntie Rong, taels, Cloud Stride 1) | Wide sleeves that keep the flute dry; fixed +max Soul |
| Trousers | Falls-Echo Trousers | straight (cloud) | Cloudwing Crane (0.2%) | Pale as spray; fixed +tenacity |
| Boots | Falls-Echo Slippers | slippers | Tower 20 | Silent on a temple floor; fixed +evasion |
| Gourd | Falls-Echo Gourd | — | Tea House recipe scroll: cloud feather ×3, soulbell flower ×2, cloudsteel ore ×2 | It hums when tapped; fixed +melody power |

#### Act II · the Expanse (sixth piece: cape)

**Stormhide** (body · Spirit · iLv 68 · Thunder · `body_ladder`). The Gold Body is tempered in the Lightning Scar.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Stormhide Knuckles · Cleaver · Staff · Pike | family's | Thunderhorn Rhino (E 2.5%) | Horn-plated; fixed +attack |
| Hat | Stormhide Headband | headband | Snow Ape (0.2%) | White fur against the Rimefrost wind; fixed +Body |
| Robe | Stormhide Vest | sleeveless (grey) | Ironroot Clan smith (Spirit Stones) | Rhino hide that takes a charge; fixed +knockback |
| Trousers | Stormhide Wraps | martial (ink) | Snow Ape (E 2.5%) | Ape hide, stitched double; fixed +Body |
| Boots | Stormhide Boots | boots | Gold Body temper trial, first pass | Scorched by the Scar; fixed +knockback |
| Cape | Stormhide Mantle | solid | Ironroot recipe: thunder horn ×2, snow ape hide ×2, stormsteel ore ×3 | Crackles in dry air; fixed +HP% |

**Azure Fin** (beast tamer · Spirit · iLv 72 · Water · `beast_taming`). The dragonets are carp halfway to dragons.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Azure Fin Bow | bow | Thousand-Eye Toad, field boss (20%) | Strung with a dragonet's whisker; fixed +pet damage |
| Hat | Azure Fin Hat | straw | Azure Carp Dragonet (0.2%) | Scaled like the lake; fixed +taming |
| Robe | Azure Fin Coat | cardigan (jade) | Herders' Camp (Herder Suo, Spirit Stones) | Worn by the herders who raise lake beasts; fixed +HP% |
| Trousers | Azure Fin Leggings | loose (indigo) | Azure Carp Dragonet (E 2.5%) | Dry after wading; fixed +Agility |
| Boots | Azure Fin Boots | boots | River Sentinel (0.2%) | Stone-soled for the causeway; fixed +evasion |
| Cape | Azure Fin Cloak | solid | Herders' Camp recipe: dragonet scale ×3, kite silk ×2, stormsteel ore ×2 | Your animal follows its colour; fixed +taming |

**Kite-String** (musician · Sage · iLv 76 · Wind · `buddhist`). The canyons' kites sing on their strings.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Kite-String Flute · Bell | family's | Wind Kite (E 2.5%) | Pitched to the canyon wind; fixed +melody power |
| Hat | Kite-String Band | tied | Canyon Harpy (0.2%) | Long tails that stream in the melody; fixed +soul attack |
| Robe | Kite-String Robe | disciple (cloud) | Wayfarers' Inn (Innkeeper Tang, Spirit Stones) | A travelling player's robe; fixed +max Soul |
| Trousers | Kite-String Trousers | straight (white) | Canyon Harpy (E 2.5%) | Barred like harpy plumes; fixed +tenacity |
| Boots | Kite-String Slippers | slippers | Wind Kite (0.2%) | Light on the Windbridge; fixed +evasion |
| Cape | Kite-String Cape | tattered | Wayfarers' Inn recipe: kite silk ×4, harpy plume ×2, sunglass ore ×2 | Painted silk that pulls toward the wind; fixed +melody power |

**Sandking Seal** (formation · Sage · iLv 77 · Earth · `confucian`). The Tomb's halls are sealed with arrays.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Sandking Seal Fan · Brush | family's | the Tomb King (25%) | Carved with the Hall of Sand Kings' seal-script; fixed +Qi Attack |
| Hat | Sandking Seal Guan | guan | Terracotta Warden (0.2%) | A clay crest, warm as if fired yesterday; fixed +Insight |
| Robe | Sandking Seal Robe | cardigan (ochre) | Nine Peaks free market (Broker Mu) | Sun-gold thread; fixed +Essence |
| Trousers | Sandking Seal Trousers | straight (earth) | Terracotta Warden (0.2%) | Stiff with tomb dust; fixed +tenacity |
| Boots | Sandking Seal Boots | folded | Tomb chest (`chest_tomb`, 10%) | Soles that do not slip on glass; fixed +evasion |
| Cape | Sandking Seal Cape | solid | Nine Peaks recipe: terracotta shard ×4, sun crown fragment ×1, sunglass ore ×2 | A seal stitched on the back; fixed +array power |

**Amber-Sting** (alchemist · Sage · iLv 78 · Fire · `poison`). Scorpion venom sets in amber beads.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Amber-Sting Dirk | dagger | Sandstorm Scorpion (E 2.5%) | A stinger for a point; fixed +crit damage |
| Hat | Amber-Sting Veil | weimao | Dune Worm (0.2%) | Glass-bead fringe against the sand; fixed +crafting control |
| Robe | Amber-Sting Robe | scholar (ochre) | Condensing Hall (Alchemist Fen, Spirit Stones) | Cool in the Sunscar heat; fixed +Essence |
| Trousers | Amber-Sting Trousers | scholar (earth) | Dune Worm (E 2.5%) | Worm-glass buttons; fixed +Agility |
| Boots | Amber-Sting Slippers | slippers | Oasis of Bones (Keeper Meng, Spirit Stones) | Soft on hot sand; fixed +evasion |
| Cape | Amber-Sting Cape | tattered | Condensing Hall recipe: scorpion stinger ×3, ember cactus ×2, sunglass ore ×2 | Hung with venom phials; fixed +toxicity tolerance |

**Riven-Sky** (sword · Sage · iLv 79 · Metal · `sword_dao`). The Wreck's Riven Peak split under a comet.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Riven-Sky Jian | sword | Starsea Pirate (E 2.5%) | Comet-iron that rings like a bell; fixed +penetration |
| Hat | Riven-Sky Crown | guan | Rogue Nine Peaks Disciple (0.2%) | An Alliance crown with its peak scratched out; fixed +crit |
| Robe | Riven-Sky Robe | vneck (indigo) | Alliance Factor (Factor Ruan, Spirit Stones) | Cut for sky-ship decks; fixed +Essence |
| Trousers | Riven-Sky Trousers | cuffed (ink) | Rogue Nine Peaks Disciple (E 2.5%) | A deserter's, still sound; fixed +Agility |
| Boots | Riven-Sky Boots | folded | Wreck chest (`chest_wreck`, 10%) | Grip on a tilted deck; fixed +move speed |
| Cape | Riven-Sky Cape | tattered | Stormsteel Smith recipe (Smith Hong): comet iron ×3, sky ink ×2, sunglass ore ×2 | Torn by star wind; fixed +crit |

#### Act III · the Lantern Star Field (sixth piece: talisman)

**Driftsilk** (alchemist · Sovereign · iLv 86 · Star · `poison`).

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Driftsilk Dirk | dagger | Star Jellyfish (E 2.5%) | Its edge stings like the jelly's trail; fixed +crit damage |
| Hat | Driftsilk Veil | weimao | Star Jellyfish (0.2%) | Glows for a day after the dive; fixed +crafting control |
| Robe | Driftsilk Robe | scholar (rose) | Lanternfall apothecary (Apothecary Sang) | Woven from jelly silk; fixed +Essence |
| Trousers | Driftsilk Trousers | scholar (cloud) | Comet Sparrow (E 2.5%) | Spark-scorched at the hem; fixed +Agility |
| Boots | Driftsilk Slippers | slippers | Comet Sparrow (0.2%) | Dry on the Driftglass Bank; fixed +evasion |
| Talisman | Driftsilk Charm | — | Apothecary recipe: jelly silk ×4, star lotus ×2, driftglass ×2 | A star lotus seed in glass; fixed +toxicity tolerance |

**Wyrm-Cradle** (beast tamer · Sovereign · iLv 88 · Star · `beast_taming`).

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Wyrm-Cradle Bow | bow | Nest Guardian (E 2.5%) | A guardian's bronze plate for a grip; fixed +pet damage |
| Hat | Wyrm-Cradle Hat | straw | Hollowed Wyrmling (0.2%) | Eggshell-white; hatchlings trust it; fixed +taming |
| Robe | Wyrm-Cradle Coat | cardigan (indigo) | Lanternfall goods (Peddler Ning) | Warm as a nest; fixed +HP% |
| Trousers | Wyrm-Cradle Leggings | loose (earth) | Nest Guardian (0.2%) | Padded for the Eggshell Terraces; fixed +Agility |
| Boots | Wyrm-Cradle Boots | boots | Comet Sparrow (E 2.5%) | Sure on the Nest Cliffs; fixed +evasion |
| Talisman | Wyrm-Cradle Charm | — | Lanternfall goods recipe: guardian scale ×3, comet plume ×2, star shard ×15 | A scale your animal will guard; fixed +taming |

**Orbitwright** (formation · Will · iLv 92 · Space · `confucian`). The Orbit Ruins' gravity is an array.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Orbitwright Fan · Brush | family's | Gravity Golem (E 2.5%) | Weighted ribs that fall true; fixed +Qi Attack |
| Hat | Orbitwright Guan | guan | Orbit Moth (0.2%) | Motes circle the crest; fixed +Insight |
| Robe | Orbitwright Robe | scholar (indigo) | Lanternwright Han's shop | The lanternwright's own cut; fixed +Essence |
| Trousers | Orbitwright Trousers | straight (ink) | Orbit Moth (E 2.5%) | Dusted with moth-glow; fixed +tenacity |
| Boots | Orbitwright Boots | folded | Gravity Golem (0.2%) | Stay down when the hall turns over; fixed +evasion |
| Talisman | Orbitwright Charm | — | Lanternwright recipe: gravity core ×2, orbit stone chip ×4, moth dust ×3 | A chip that orbits your hand; fixed +array power |

**Cinder-Palisade** (body · Will · iLv 94 · Fire · `body_ladder`).

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Cinder-Palisade Knuckles · Cleaver · Staff · Pike | family's | General Kharn (25%) | Tempered in cinder ash; fixed +attack |
| Hat | Cinder-Palisade Headband | headband | Ashborn Raider (0.2%) | Ashborn red; fixed +Body |
| Robe | Cinder-Palisade Vest | sleeveless (crimson) | Bastion armoury (Quartermaster Bai) | Scale over bare shoulders; fixed +knockback |
| Trousers | Cinder-Palisade Wraps | martial (ink) | Ashborn Pyre Keeper (elite, 2.5%) | Fire-proof bindings; fixed +Body |
| Boots | Cinder-Palisade Boots | boots | Ashborn Raider (E 2.5%) | Walk on burning ground; fixed +knockback |
| Talisman | Cinder-Palisade Charm | — | Bastion recipe: cinder ash ×4, pyre ember ×2, driftglass ×2 | A pyre ember that never goes out; fixed +HP% |

**Watchbell** (musician · Will · iLv 95 · Metal · `buddhist`). A bell rung at every change of watch.

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Watchbell Flute · Bell | family's | Hollow Drone (E 2.5%) | Cast from a fallen lantern cage; fixed +melody power |
| Hat | Watchbell Band | tied | Hollowed Wyrmling (0.2%) | A Warden's watch ribbon; fixed +soul attack |
| Robe | Watchbell Robe | disciple (grey) | Bastion armoury | The Tidebreak watch's grey; fixed +max Soul |
| Trousers | Watchbell Trousers | straight (white) | Hollow Drone (0.2%) | Wall-walk white; fixed +tenacity |
| Boots | Watchbell Slippers | slippers | The Flame Heart's ledge chest, Lantern Heart (10%) | Quiet on the battlements; fixed +evasion |
| Talisman | Watchbell Charm | — | Bastion recipe: drone shell ×4, lantern wick ×3, star shard ×20 | A clapper on a cord; fixed +melody power |

**Nightcurrent** (sword · Will · iLv 96 · Space · `sword_dao`).

| Piece | Name | Look (dye) | Source | Line |
|---|---|---|---|---|
| Weapon | Nightcurrent Jian | sword | the Nebula Leviathan, field boss (20%) | It cuts the space between; fixed +penetration |
| Hat | Nightcurrent Crown | guan | Nebula Eel (0.2%) | An eel-bright thread in the crest; fixed +crit |
| Robe | Nightcurrent Robe | vneck (white) | Observatory (Stargazer Ming) | Cut for the Eel Currents; fixed +Essence |
| Trousers | Nightcurrent Trousers | cuffed (indigo) | Void Crab (E 2.5%) | Deeper than they are thick; fixed +Agility |
| Boots | Nightcurrent Boots | folded | Nebula Eel (E 2.5%) | Grip where there is no ground; fixed +move speed |
| Talisman | Nightcurrent Charm | — | Observatory recipe: eel essence ×3, void carapace ×2, star shard ×20 | A drop of bent space; fixed +crit |

#### v1.3 · the Star Frontier (sixth piece: gourd)

Every piece has a source on each road: main (the Ashborn road: Emberwane, Iron Orchard) / alternate (the Barrow road:
Rainroot Mere, Kingsgrave Barrows). All Sphere grade, iLv 104. Robes sell at both roads' rest shops; gourds are Keep
Market recipes from each set's materials. The Frontier's foes and their materials come with v1.3 (`frontier.py`).

| Set | Weapon | Hat | Trousers | Boots | Line |
|---|---|---|---|---|---|
| **Magmaback** (body, Fire) | Knuckles · Cleaver · Staff · Pike: Pyreback 20% / Barrow Marshal 20% | Magma Behemoth 0.2% / Remnant Will 0.2% | Ash Legionnaire E 2.5% / Remnant Will E 2.5% | Cinder Hound E 2.5% / Rust Wraith E 2.5% | Hide from a behemoth's back, still warm |
| **Ironbark** (sword, Metal) | Jian · Twinblades: Forge-Tree Warden 25% / Barrow Marshal 20% | Iron Mantis 0.2% / Rust Wraith 0.2% | Iron Mantis E 2.5% / Remnant Will E 2.5% | Rust Wraith E 2.5% (both roads) | Blades grown on an iron tree |
| **Drowned-Bloom** (alchemist, Wood) | Dirk · Rope Dart: Pyreback 20% / Bloom Mother 20% | Cinder Hound 0.2% / Bloom Siren 0.2% | Ash Legionnaire E 2.5% / Bloom Siren E 2.5% | The Cold Hearth's chest / the Sunken Library's chest | Poison of blooms that open under rain |
| **Twin-Leash** (beast tamer, Water) | Bow · Whip: Magma Behemoth E 2.5% / Tidal Colossus E 2.5% | Magma Behemoth 0.2% / Tidal Colossus 0.2% | Cinder Hound 0.2% / Bloom Siren 0.2% | Beast Taming Dao tier 5 quest (Law Touching 2, either road) | One leash for a hound, one for a colossus |
| **Root-Lattice** (formation, Earth) | Fan · Brush · Parasol: Forge-Tree Warden 25% / The Remnant Battlefield (event reward) | Rust Wraith 0.2% (both roads) | Iron Mantis E 2.5% / Remnant Will 0.2% | The Rust Harvest / The Remnant Battlefield (event rewards) | Arrays drawn like roots through stone |
| **Barrow-Choir** (musician, Life and Death) | Flute · Bell: Magma Behemoth E 2.5% / Bloom Mother 20% | Iron Mantis 0.2% / Tidal Colossus 0.2% | Cinder Hound E 2.5% / Tidal Colossus E 2.5% | Keep the Hearth / The Drowned Choir (event rewards) | Sung over barrows and drowned halls |

Names follow the valley's pattern (Magmaback Headband, Vest, Wraps, Boots, Gourd; Ironbark Crown, Robe, Trousers,
Boots, Gourd; and so on), with each piece's fixed affix from §3.1. No loot table carries more than two named rows of
each kind.

### 3.4 The general sets, fixed

The five general sets stay as they are; each gets its missing sources (§2.10) and two rates change (G12):

| Set | Change |
|---|---|
| Jade Current, Cloudpiercing | Hat and boots at Inner Disciple, trousers at Core Disciple, in each sect's Mission Hall |
| Mudwater | Cleaver: Big Toad Tan 25%; robe: Lieutenant Kuai 5% |
| Drowned Abbot | Robe: the Abbot 35% (was every kill); hat: Drowned Acolyte 0.2%; boots: Rogue Cultivator 2.5% |
| Crane | Robe: "Crane Falls at Dawn"; trousers: Cloudpeak Roc 0.2%; boots: the Cloud Stepper achievement |
| (not a set) Serpent-Tongue Jian | Rogue Cultivator: first defeat, then 10% (was every kill); marked `named`, out of the random pool |

---

## 4. Drop rates

### 4.1 The rules, rebalanced

The quality steps and the elite extra roll move into data: a `drop` block in `grades.json` (`stats.py`) read by
`LootRules` and `WorldAuthority`.

| Source | Equipment chance | Minimum quality | Today |
|---|---|---|---|
| Normal foe | 1.2% | Flawed | 3% |
| Bandit, brigand, pirate (humanoid normals) | 2.0–2.4% | Flawed | 5–6% |
| A normal spawned as an elite | its own roll, plus 8% | Common | plus 25% at Fine |
| Elite (role) | 8% | Common | 25% at Fine |
| Field, dungeon and story boss | 100% | Superior | 100% at Superior |
| Event foe | 1.2% | Flawed | 3% |
| Jars | 1% | Flawed | 2% |
| Valley chest / dungeon, Expanse, Lantern chests / Tomb, Wreck chests | 30% / 50% / 60% | Fine | 30% / 60% / 80% |

| Minimum quality | Flawed | Common | Fine | Superior | Perfect |
|---|---|---|---|---|---|
| Flawed (normals) | 55% | 30% | 12% | 3% | — |
| Common (elites) | — | 50% | 30% | 15% | 5% |
| Fine (chests) | — | — | 50% | 35% | 15% |
| Superior (bosses) | — | — | — | 70% | 30% |

Fortune still shifts the roll down by 0.1% a point, as today.

**Which base.** Weapon or armour first: 40% weapon, 60% armour (one of the four slots). A weapon drop is in the family
the character wields one time in three, any family otherwise. With weapons locked, armour only. A character's share of
usable drops rises from 38% to 76%.

**Item Level.** The foe's Level ±2, clamped to the top Level of the highest grade that has banded bases (computed from
`artifacts.json` at load), not to 81. With Sovereign and Will bases, Act III drops its own grades (G1).

**The pool.** Banded bases only: the roll skips `named`, `set`, `relic`, `legend` and `imitation`, and the slots gourd,
cape, talisman, furnace and pet gear.

### 4.2 Named drop rates

A loot table gains `named` rows (rolled on every kill, like `rare`) and `elite_named` rows (rolled only when the foe is
an elite, by role or by spawn). At most two of each per table.

| Source | Chance a row | Kills an hour of hunting | Expected hours a piece |
|---|---|---|---|
| Normal foe (`named`) | 0.2% (early valley bands 0.4%) | 120–180 of one species | 2.8–4.2 |
| Elite (`elite_named`) | 2.5% (early valley bands 5%) | 20 an elite slot | 2.0 |
| Field boss | 20% | on its timer | 5 kills |
| Dungeon boss | 25% | by its key | 4 runs |
| Secret or dungeon chest | 10–15% | once a reset | — |
| Trial, tower floor, event | first clear; 10% after | — | — |
| Quest, shop, recipe | fixed | — | — |

A named piece drops at its source's quality table with the floor raised to Common. A set's slowest piece takes 3–4
hours of focused hunting; the shop, craft and tower pieces take less.

### 4.3 What the new rates give

Modelled as in §1.6, per hour of hunting:

| Grade · tier | Pieces (today) | Fine or better (today) | Superior or better (today) | Perfect (today) |
|---|---|---|---|---|
| Plain · 1 | 5.5 (14.6) | 1.27 (6.1) | 0.38 (2.5) | 0.063 (0.79) |
| Common · 1 | 6.7 (17.3) | 1.39 (6.3) | 0.39 (2.5) | 0.057 (0.71) |
| Earth · 1 | 6.0 (15.6) | 1.25 (5.7) | 0.35 (2.2) | 0.051 (0.64) |
| Heaven · 1 | 6.3 (16.9) | 1.64 (8.4) | 0.53 (3.7) | 0.100 (1.25) |
| Mystic · 1 | 5.9 (15.8) | 1.45 (7.2) | 0.45 (3.0) | 0.080 (1.00) |
| Spirit · 2 | 5.9 (15.8) | 1.45 (7.2) | 0.45 (3.0) | 0.080 (1.00) |
| Sage · 2 | 5.5 (14.5) | 1.25 (5.9) | 0.37 (2.4) | 0.060 (0.75) |
| Sovereign and Will · 3 (Sage today) | 5.8 (15.6) | 1.46 (7.3) | 0.46 (3.1) | 0.083 (1.04) |

What the player sees: a mixed session (35% fighting) finds about two pieces an hour; in the Earth band (17 hours) about
nine Fine or better pieces fit their slots, two or three Superior pieces drop, and a Perfect piece is a once-a-band
event. Named pieces are the chase. Region spread: 4.3 pieces an hour where a region has no elite slot (Cleansing Peak,
the Tomb) to 8.8 on the Caravan Road's bandits.

### 4.4 The `balance_sim` drop check

`_drops(cfg)` in `tests/balance_sim.gd`, after `_currency`, with its targets in `balance.json` (`stats.py`):

```json
"drops": {"kills_per_hour": 360, "elite_kills_per_slot": 20, "elite_share_cap": 0.33, "hours_per_region": 20,
          "targets": {"pieces": [6.0, 0.30], "fine_up": [1.4, 0.30], "superior_up": [0.45, 0.35], "perfect": [0.08, 0.50]},
          "region_floor": 3.0, "usable_share": [0.6, 0.85],
          "band_hours": {"plain": 4.5, "common": 8, "earth": 17, "heaven": 25, "mystic": 15, "spirit": 40},
          "set_hours": [0.3, 0.8]}
```

What it does:

1. **Per field region** (rooms with spawns, not safe, not a story instance): 20 simulated hours of hunting at 360 kills
   an hour. Elite slots give 20 kills an hour each, at most a third of the kills; the rest are the room's normals by
   their spawn counts. Every kill rolls the real `LootRules.roll` with the elite extra roll and `make_equipment`
   (seeded, `12345 + region index`), for a character of the band's Level wielding each archetype's first family in
   turn.
2. **Counts** pieces by quality and by the grade of the made item; the share of pieces each archetype can use; any
   piece from the random roll that is `named`, `set`, `relic`, `legend` or `imitation`.
3. **Reports** one table: grade and zone tier, pieces, Fine or better, Superior or better, Perfect an hour, and the
   lowest usable share, beside the targets.
4. **Checks** (each a `check` line):
   - each grade's mean (over its regions) of each measure within its target ± tolerance: pieces 6.0 ±30%, Fine or better
     1.4 ±30%, Superior or better 0.45 ±35%, Perfect 0.08 ±50% (the rarest count is the noisiest);
   - every region at least 3 pieces an hour;
   - every archetype's usable share between 60% and 85%;
   - no named piece from the random roll;
   - Act III's regions drop Sovereign or Will gear (no clamp at 81);
   - **each archetype set completes in time:** the expected hours of focused hunting to own all six pieces (the slowest
     drop piece: 1 ÷ (row chance × the source's kills an hour in its room); shop, craft, quest and tower pieces count as
     0) lie between 0.3 and 0.8 of the band's hunting hours (band hours × the fight share 0.35). Bands past Spirit take
     their hours from the Act III simulation once `sim_end` moves past Sage Sovereign 1.

The modelled values of §4.3 sit inside every target. The acceptance line of P7 ("`balance_sim` reports gear per hour of
hunting per grade within the targets") is this check.

### 4.5 Knock-on effects

- **Refining essence.** Salvage feeds the forge; with about 60% fewer pieces, essence falls in step. Raise every
  `salvage.json` essence count by half (`economy.py` `forge_upkeep`), so essence per hunting hour falls about 40%;
  named pieces carry fixed affixes, so fewer rerolls are needed.
- **Taels.** `_taels_per_hour` rolls with `no_equipment`, so the S39 affordability checks are unchanged. Real players
  sell fewer pieces; V10d3's month run should be repeated after the change.
- **The Codex and the wiki.** `tools/dev/wiki.py` shows the new fields (archetype, element, path, fixed affixes) and
  the named rows with their rates.

---

## 5. The sprite gap list

### 5.1 Today

- **68 creature sheets** (`art/creatures/`, `creature_art.json`): 66 used by 67 foes, two by pets only (`cloud_stag`,
  `hatchling_wyrm`). 54 foes are human, drawn from the avatar parts.
- **Shared sheets:** the Thornback Boar and the Fruit Guardian (the S45 herb guardian elite) are one sheet.
- **Palette swaps:** the Hollowed Boarlet is the Wild Boarlet with the Hollow ramp (`cv.hollow`); the Heart Demon and the
  Reflection are the player's own avatar tinted; the Drowned Acolyte and the Drowned Abbot wear one outfit with two
  tints; the Ashborn and the Presence phantoms are tinted avatars.
- **One species in several regions:** the Hollow Drone (Ashen Reach, Tidebreak Front, Lantern Heart), the Hollowed
  Wyrmling (Wyrmnest Isles, Tidebreak Front, Lantern Heart), the Comet Sparrow (Drifting Shoals, Wyrmnest Isles), the
  Starsea Pirate (Skyport Wreck, Blackmast Haven), the Wind Kite (Gale Canyons, Skyport Wreck), the Sandstorm Scorpion
  (Sunscar Desert, Tomb), the Mudwater Bandit (Caravan Road, Mudwater Hideout).
- **Elites look like normals:** 41 normal species spawn as elites with the normal's sheet; only the gold label and
  crown mark them.
- **Human foes:** 52 outfits on one body from five shirts (the v-neck on 20 of them), five trousers, three shoes, six
  hats and two capes. Seven pairs share an outfit and differ only by dye or tint (the Acolyte and the Abbot; the Rogue
  Cultivator, Yun Zhiqiu and Senior Brother Hao Qian; the Canyon Brigand and the Blackreed Disciple; the two Shen Lians;
  Big Toad Tan and Tan the Younger; Young Master Luo Heng and Bai Yuheng; the Ironpine Disciple and Kuai Shan).
- **Equipment:** every grade of a weapon family shares one appearance, so a Sunsteel jian looks like a Training jian in
  the world.

### 5.2 Per region

Hostile field species (normals and elites; bosses apart). "Own" counts species found in no other region.

| Region | Levels | Species | Creature sheets | Human | Own | Shared with | Verdict |
|---|---|---|---|---|---|---|---|
| Lotus Ferry | 0–3 | 3 | 3 | 0 | 3 | — | Enough for a start |
| Willow Path | 1–3 | 2 | 2 | 0 | 2 | — | Enough for a path |
| Stonewall Quarry | 4–7 | 4 | 4 | 0 | 4 | — | Good |
| Reed Marsh | 4–12 | 4 | 4 | 0 | 4 | — (one sheet a palette swap) | Good |
| Bamboo Grove | 10–15 | 3 | 3 | 0 | 3 | — | Good |
| **Caravan Road** | 14–19 | **1** | 0 | 1 | 0 | Mudwater Hideout | **Gap: one foe for six Levels** |
| Mudwater Hideout | 14–20 | 4 | 1 | 3 | 3 | Caravan Road | Good |
| Cleansing Peak | 17–19 | 1 | 1 | 0 | 1 | — | A trial peak; fine |
| Deepwater Bend | 19–25 | 2 | 2 | 0 | 2 | — | Thin |
| Drowned Shrine | 21–27 | 3 | 1 | 2 | 3 | — | Good |
| Whitewater Gorge | 28–36 | 4 | 3 | 1 | 4 | — | Good |
| Crane Cliffs | 37–45 | 3 | 3 | 0 | 3 | — | Good |
| Mist Peak | 46–63 | 5 | 4 | 1 | 5 | — | Good |
| Summit Ridge | 55–63 | 2 | 2 | 0 | 2 | — | Thin |
| Thunderhorn Plains | 64–69 | 2 | 2 | 0 | 2 | — | Thin for 40 hours of Sage |
| Rimefrost Heights | 67–72 | 2 | 2 | 0 | 2 | — | Thin |
| Mirrorwater Lake | 68–75 | 2 | 2 | 0 | 2 | — | Thin |
| Gale Canyons | 73–78 | 3 | 2 | 1 | 2 | Skyport Wreck | Good |
| Sunscar Desert | 73–81 | 2 | 2 | 0 | 1 | Tomb | Thin |
| Tomb of Sunscar | 77 | 2 | 2 | 0 | 1 | Sunscar Desert | A dungeon; fine |
| Skyport Wreck | 76–81 | 3 | 1 | 2 | 1 | Gale Canyons, Blackmast Haven | Thin in creatures |
| Drifting Shoals | 82–87 | 2 | 2 | 0 | 1 | Wyrmnest Isles | Thin |
| **Blackmast Haven** | 85–90 | 2 | **0** | 2 | 1 | Skyport Wreck | **Gap: no creature at all** |
| Wyrmnest Isles | 85–93 | 3 | 3 | 0 | 1 | Shoals, Tidebreak, Lantern Heart | Good |
| Orbit Ruins | 88–93 | 2 | 2 | 0 | 2 | — | Thin |
| Ashen Reach | 88–96 | 3 | 1 | 2 | 2 | Tidebreak, Lantern Heart | Good |
| **Tidebreak Front** | 90–99 | 2 | 2 | 0 | **0** | Ashen Reach, Wyrmnest, Lantern Heart | **Gap: nothing of its own** |
| Nebula Deep | 94–99 | 2 | 2 | 0 | 2 | — | Thin |
| **The Lantern Heart** | 97–99 | 2 | 2 | 0 | **0** | Ashen Reach, Wyrmnest, Tidebreak | **Gap: nothing of its own** |

The valley averages 2.9 species a field region, the Expanse 2.3 and the Lantern Star Field 2.3, while Acts II and III
hold the most hours. Act III's last two regions have no species of their own.

### 5.3 The backlog, ranked

Ranked by hours spent where the gap is, then by cost. `art/creatures` is the creature toolkit (`tools/art/`,
`docs/art-contracts.md`); "avatar parts" builds a human foe from `parts.json` with no new art unless a new garment look
is drawn.

| Rank | Item | Pipeline | Region | Why | Cost |
|---|---|---|---|---|---|
| 1 | **Greyfall Revenant**: a Hollowed Star Warden (disciple robe, grey dye, spear, the Hollow tint), normal, 90–99 | avatar parts | Tidebreak Front, Lantern Heart | Gives both regions a foe of their own; carries the Watchbell's hat row if wanted | none (parts and a tint) |
| 2 | **Breach Maw**: a hollow_space mouth in the Tide that pulls and bites, normal and elite, 92–99 | art/creatures (1 sheet, cell 192) | Tidebreak Front, Lantern Heart | The end of Act III has no creature of its own | one sheet |
| 3 | **Dust-Mane Jackal**: a metal-element road scavenger, normal, 14–19 | art/creatures | Caravan Road | One foe for six Levels; a natural source of `metal_core_low` | one sheet |
| 4 | **Caravan Deserter**: a human archer (sleeveless, straight, ochre, bow) | avatar parts | Caravan Road | A second human on the road | none |
| 5 | **Elite palette pass**: a `cv.elite` ramp shift and a mark in the toolkit, rendered for the 41 species that spawn as elites (or a per-species `elite_tint` in `creature_art.json`) | art/creatures toolkit | every region | Elites read as elites before the label; one pass, then per sheet a render | a toolkit feature, then batch renders |
| 6 | **Powder Gibbon**: a ship ape that throws lit powder kegs, fire, 85–90 | art/creatures | Blackmast Haven | The only field region with no creature | one sheet |
| 7 | **Stormgrass Stag** (wood, 64–68) on the existing `cloud_stag` sheet; **Glacier Owl** (soul, 67–72, a source of `soul_core_peak`); **Mirror Heron** (water, 68–75); **Glass Scarab** (earth, 73–81) | the stag: data only; the rest art/creatures | Thunderhorn, Rimefrost, Mirrorwater, Sunscar | A third species in each thin Expanse field, where Sage takes 40 hours | none, then three sheets |
| 8 | **Iron-Quill Shrike** (metal, 38–43) and **Bronze-Crest Eagle** (metal, 58–63) | art/creatures | Crane Cliffs, Summit Ridge | Natural sources of `metal_core_mid` and `_high`; Summit Ridge's third species | two sheets |
| 9 | A third species each for Deepwater Bend (water, 19–25), the Drifting Shoals (star, 82–87), the Orbit Ruins (space, 88–93) and the Nebula Deep (water, 94–99) | art/creatures | those four | Thin regions of middling length | four sheets |
| 10 | **Two garment looks** for human foes: a lamellar vest (shirt) and a hooded travel cloak (cape) | avatar parts, with the full AGENTS.md review (every action, both facings, every dye) | 52 human foes; named armour | Human foes share five shirts; named armour gains looks | two garments across all animations |
| 11 | **Weapon grade palettes**: a palette per grade for each family's sheet in `tools/art/bake_weapons.py` (no pose change; reviewed in the gallery) | avatar weapon sheets | everywhere | A grade and a named weapon read in the world | eleven families × grade palettes |
| 12 | v1.3's species (Cinder Hound, Magma Behemoth, Ash Legionnaire, Bloom Siren, Tidal Colossus, Iron Mantis, Rust Wraith, Remnant Will, Time-Worn Specter, Sun Roc, Radiant Lion, Moon Moth, Shade Serpent, Hollowed Legionnaire, the bosses) and the four new weapon families' sheets and any new attack actions (the whip and rope dart likely need them, AGENTS.md rule 2) | art/creatures, avatar weapons | the Frontier | v1.3's own art; listed because §2.7's named whips, parasols, rope darts and twinblades wait on it | v1.3 |

Icons are a separate line of work: one per named piece (§6 step 10), drawn by `tools/icons` from the grade silhouette
with an archetype motif and the element's colour.

---

## 6. Build order for P7b's data work

Steps 1–13 land before v1.3 and cover Acts I–III; step 14 lands with v1.3. Code changes are marked; the rest is
data from `tools/data/*.py` through `build_data.py`.

| # | Change | Lands in | Tests |
|---|---|---|---|
| 1 | Tags on equipment: `named` (archetype, element, path, fixed affixes); the element and path rules (§2.1) | `items.py` `artifact()`; **code**: `StatRules.instance_modifiers` (fixed affixes, element bonus, path) | `data_validation`: tag values valid; a named piece's fixed affix comes from its archetype's pool |
| 2 | Drop rules into data: the `drop` block (quality tables, weapon share, family bias, elite extra roll, named-row caps); the item-Level clamp from the highest banded grade; the pool excludes `named` | `stats.py` (`grades.json`); **code**: `LootRules.make_equipment`, `make_instance`, `roll` (`named`, `elite_named`), `world_authority.gd:774-777` | `rules_tests` `drop_pool_suite` extended: family bias, clamp, exclusions, quality tables |
| 3 | New chances in every loot table (§4.1); the Serpent-Tongue Jian, Drowned Robe and Mudwater Cleaver rows (§3.4); drop `unique_drop` | `enemies.py` (tables and chest tables), `world.py` (zone chests) | `data_validation`: no row with a dead field |
| 4 | Affixes: the ten new rows, `named_only` on five | `stats.py` (`affixes.json`); **code**: `LootRules` affix pools skip `named_only` | `data_validation` |
| 5 | Stats `pet_damage`, `array_power`, `melody_power` | `stats.py` `STAT_LIST`; **code**: `pet_authority.gd:498`, the `deploy_array` effect, the flute channel, the bell's ring, Clear Heart Melody | `rules_tests` per reader |
| 6 | Set rows gain `archetype`, `tier`, `element`, `path`; bonus rows may carry a `flag` with values; the path doubling; `sets.json` moves to a new `tools/data/gear.py` | `gear.py` (new, called by `build_data.py`); **code**: `StatRules.set_modifiers`, a `set_flags(c)`, and the readers of Unbroken, Honed Intent, Venom Hand, Kin-Bond, Living Array, Sustained Note | `rules_tests` `set_suite`: each flag at 6 pieces, the path doubling, counts across weapon variants |
| 7 | Banded bases: brush and bell at every grade; Sovereign and Will weapons, armour and gourds; pet gear and furnace ladders; wear levels, sockets, salvage rows, smithing recipes, shop rows | `items.py` (`FAMILY_APPEARANCE`, `GRADE_WORD`, `ARMOUR`, gourds, the energy and socket maps), `stats.py` (`grades.json`), `economy.py` (salvage, recipes, shops) | `data_validation`; `balance_sim` step 11 |
| 8 | Named gear, Acts I–III: the 152 pieces of §2.4–2.6 and §3.3 with their loot rows, shop rows, recipes, quest and trial rewards; a Cliff Ape elite slot in the Crane Cliffs; Tower 20's boots rule and floor 30's fan | `gear.py` (rows, appended by `items.build_artifacts`), `enemies.py` (rows), `economy.py` (shops, recipes, achievements), `story.py` (quest rewards), `living_world.py` (tower), `world.py` (the spawn) | `data_validation`: every named piece sourced; every set completable |
| 9 | The 43 sources of §2.10, and the Stormgrass Stag | `economy.py`, `living_world.py`, `enemies.py`, `world.py`, `story.py`; recipes for the kits and tablets from `posts.py` | `KNOWN_SOURCE_GAPS` empty |
| 10 | Icons for every new base and named piece | `tools/icons/families/weapons.py`, `armour.py`, `misc.py` (gourds, pet gear, furnaces); `icon_manifest.json` | the icon build byte-identical twice |
| 11 | `balance.json` `drops` and `_drops()` | `stats.py`; `tests/balance_sim.gd` | `balance_sim` green (§4.4) |
| 12 | Validation rules: no named piece in the random pool; each archetype has at least its §2.3 count per zone; every archetype set has a source for each piece and a weapon in each of the archetype's families | `tests/data_validation.gd` | — |
| 13 | Wiki and Codex: the new fields and rows; the wiki rebuilt byte-identical; CHANGELOG entry | `tools/dev/wiki.py`, `build_data.py` | wiki rebuild check |
| 14 | **With v1.3:** the Frontier's sets, signatures and Well mantles; Sphere and Law bases with the four new families; the Bedrock Pill (§2.10) | `gear.py`, `items.py`, `enemies.py`, `economy.py` with `frontier.py`; **code**: the `solid` stability word and its gate | `balance_sim` over the Frontier bands; `rules_tests` for the pill |

A new module keeps `items.py` (918 lines) from doubling: `tools/data/gear.py` holds `NAMED` (by zone) and `SETS`, and
`items.build_artifacts` appends its rows.

---

## 7. Open questions

| # | Question | Recommendation |
|---|---|---|
| 1 | Which archetype takes each of v1.3's four families? | Dual blades to the Sword Dao (a second family for the jian's Dao), the rope dart to the alchemist (a poisoned dart on a cord; it also carries Grapple), the whip to the beast tamer (the lash that commands), the umbrella to the formation master (a canopy array). Then every archetype but the musician has two families by v1.3 |
| 2 | Brush and bell at every grade from Training? | Yes. The formation master and the bell musician get a weapon from Level 1; the sheets exist, so it is data and icons |
| 3 | The guqin: a weapon or a tool? | A tool. A held guqin needs seated attack poses in every garment (AGENTS.md); the musician's third instrument stays the teahouse's meditation piece |
| 4 | Weapon drops biased to the wielded family (one in three)? | Yes: usable drops rise from 38% to 76%, which is what lets the drop volume fall |
| 5 | Drops cut from about 15 to about 6 pieces an hour of hunting, with salvage essence raised by half | Yes. The flood makes every banded piece vendor fodder; fewer, better drops and named pieces give the chase |
| 6 | The scope: 216 new named pieces through v1.3 (a set and two or three signatures per archetype per zone) | Keep the full target. If it must shrink, build the sets first (152 set pieces with variants) and the signatures with each act's next content pass |
| 7 | A repeatable boss in the valley's Heaven band (G14)? | Yes, in P9's boss work: a field boss on the Crane Cliffs or Mist Peak takes the valley sets' weapon rows from the elites |
