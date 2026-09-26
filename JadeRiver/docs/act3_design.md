# Act III · The Lantern Star Field (v1.2) — design

The build prompt gives Act III in outline: zone tier 3, levels 82–99, ceiling Sphere Lord 3,
Starsea Endurance 20 → 90, elements Fire, Metal, Space (weak) and Star, Qi density 1.5–2.5,
Sage Crystals and Star Jade, eleven monsters and three bosses, plus a list of systems. This page
fills in the geography, the story and the order in which the systems unlock, so each build phase
adds a playable, tested slice. Names are original to Jade River.

## Premise

Past the Starsea the sky becomes a field of drifting islands, and above each island hangs a
**lantern star**: a fallen star held in an old bronze cage, burning so the dark between the islands
stays thin. The **Star Wardens**, an order older than the Nine Peaks, keep the lanterns lit and hold
the line against the **Hollow Tide**, which seeps in wherever a lantern goes out. Pirates of Admiral
Voss hunt the lantern lanes, and the Ashborn legions of Ash Queen Seralet push in from the Ashen
Reach under General Kharn, who wants the lanterns' fire for his people's pyres.

Five threads carry the act:

1. **The dimming lanterns.** Someone is putting the lanterns out, one island at a time. The Grey
   Pilgrim is seen at each dark cage. The Tide follows him.
2. **Elder Gu.** Admiral Voss bought Gu's ledger (Act II) and took Gu on as purser. When Voss falls,
   Gu flees into the Hollow Wake with a grey mark on his hand (he returns Hollowed in Act IV).
3. **Shen Lian.** The rival from Lotus Ferry arrives as a Star Warden aspirant. He competes with the
   player for the Star Warden title and, at the end, stays behind to hold the Greyfall Breach and is
   taken by the Tide (the save-or-defeat choice is Act IV's).
4. **Lu's lantern.** Lu crossed here long ago and relit one lantern with his own fire. His star notes
   lead to the Lantern Heart, where the Lantern Heavenly Flame still burns.
5. **The Ashborn.** Kharn is an enemy, not a villain: race is not morality. At his pyre the player
   may spare him, which opens Ashborn reputation in Act IV.

## Regions and rooms (39, plus instances)

| # | Region | Levels | Endurance | Rooms | Monsters and bosses |
|---|---|---|---|---|---|
| 1 | Lanternfall Harbor (town, teleport stone) | — | 0 | Arrival Quay · Harbor Market · Star Chandlery · Tidelight Inn | — |
| 2 | Drifting Shoals | 82–87 | 20 | Jellyfish Shallows · Sparrow Reefs · Driftglass Bank · Moored Hulks (rest) | Star Jellyfish, Comet Sparrow |
| 3 | Blackmast Haven | 85–90 | 30 | Blackmast Docks · Gunners' Battery · Smugglers' Cove (hidden) · Flagship Deck (boss) | Starsea Pirate, Pirate Gunner, Admiral Voss (90) |
| 4 | Wyrmnest Isles | 85–93 | 40 | Nest Cliffs · Eggshell Terraces · Guardian's Crown · Hatching Cave | Nest Guardian, Hollowed Wyrmling |
| 5 | Star Warden Citadel (town) | — | 0 | Citadel Gate · Wardens' Hall · Observatory · Presence Court | — |
| 6 | Orbit Ruins | 88–93 | 50 | Tumbling Stair · Orbit Garden · Golem Foundry · Inverted Hall (gravity switches) | Gravity Golem, Orbit Moth |
| 7 | Ashen Reach | 88–96 | 60 | Cinder Fields · Ashborn Palisade · War Camp · Kharn's Pyre (boss) | Ashborn Raider, Hollow Drone, General Kharn (92) |
| 8 | Tidebreak Front | 90–99 | 70 | Tidebreak Bastion (fortress, safe) · Greyfall Breach · Hollow Wake · Drone Hive | Hollow Drone, Hollowed Wyrmling |
| 9 | Nebula Deep | 94–99 | 80 | Nebula Verge · Eel Currents · Crab Grottoes · Leviathan's Maw (field boss) | Nebula Eel, Void Crab, Nebula Leviathan (field, 99) |
| 10 | The Lantern Heart (secret realm) | 97–99 | 90 | Wick Gate · Hall of Burning Stars · Flame Heart | Lantern Heavenly Flame |

Room ids use the prefixes lh, dr, bm, wn, wc, or, ar, tf, nd and lt. Story instances (the Hollow Tide
battle, the Sphere trial) use si_. Every room is in zone `lantern_star_field`.

## Monsters and bosses

| Monster | Levels | Element | Role | Notes |
|---|---|---|---|---|
| Star Jellyfish | 82–87 | Star | normal, floats | Stinging trail; Confusion. Drops jelly silk, star shards |
| Comet Sparrow | 82–87 | Fire | normal, flies | Diving burn strike; tameable (star tier) |
| Starsea Pirate | 85–90 | Metal | normal, humanoid | Act II pirate, new level band |
| Pirate Gunner | 85–90 | Fire | ranged, humanoid | Hand-cannon shot and a slow bombard with a ground marker |
| Nest Guardian | 85–93 | Earth | elite-sized | Tail sweep, guards eggs, Presence (small) |
| Hollowed Wyrmling | 88–96 | Hollow Fire | normal | Adds Hollowing; can be cleansed at low HP |
| Gravity Golem | 88–93 | Earth | heavy | Gravity pull, then slam |
| Orbit Moth | 88–93 | Star | flies | Orbiting motes; dust Confusion; tameable (star tier) |
| Hollow Drone | 88–99 | Hollow Metal | pack, flies | Adds Hollowing; swarms in Tide battles |
| Ashborn Raider | 88–96 | Fire | humanoid | Cinder Qi; burning ground |
| Nebula Eel | 94–99 | Water | swims in nebula | Space bite ignores 15% defence |
| Void Crab | 94–99 | Space | shelled | Blinks behind the player; tameable (star tier) |
| **Admiral Voss** | 90 | Metal | dungeon boss, humanoid | 1 cutlass and broadside markers · 2 boarding crew · 3 Presence clash (the first one the player meets) |
| **General Kharn** | 92 | Fire | dungeon boss, humanoid (Ashborn) | 1 cinder glaive · 2 pyre (burning ground) · 3 Sphere of Cinders (the first Sphere clash). Spare or slay |
| **Nebula Leviathan** | 99 | Space | field boss | Current swallow, void breath, gravity well; Presence and Sphere |

## Realms and systems by stage

| Stage | Unlocks |
|---|---|
| Sage Sovereign 3 | The Lantern Run (voyage), currency exchange (Sage Crystal and Star Jade), the zone ceiling lifts to Sphere Lord 3, Starsea Endurance jades |
| Will Manifest 1 | **Presence** (aura level 1–10, the Pressure contest against weaker foes, clashes with other Presences); account slot 12 |
| Will Manifest 2 | Star-tier spirit beasts (Comet Sparrow, Orbit Moth, Void Crab); the Hatchling Wyrm egg; Beast Taming Dao tier 4 |
| Will Manifest 3 | Sect Master succession quest; Will Manifest 3 → Sphere Lord 1 needs Presence level 5 and a Sphere comprehension item |
| Sphere Lord 1 | **Sphere** (terrain by the strongest Dao's element, cutting Sword Domain, Sphere clashes, broken Sphere = meridian injury); pets gain a small Sphere; Space Dao teacher |
| Sphere Lord 2 | **Star Warden** title (zone condition); the Hatchling Wyrm hatches as a companion; Dao tier 6 |
| Sphere Lord 3 | Law pills (Law Condensing, Law Touching); the Frontier voyage is planned for Act IV |

Throughout the zone:

- **Hollowing** is no longer held at the valley's 49%. At 50% technique costs rise 25% and Composure
  falls; at 100% the character loses control for 3 s, Hollowed allies turn hostile for 10 s, and the
  meter falls back to 80%. Surviving 100% once awakens Hollow-Touched. Cleansing: Lantern Incense
  (−15), Hollow Cleansing Pill (−40), resting by a lit lantern (decay ×4).
- **Hollow Tide battles**: a defence event at the Tidebreak Bastion (waves of drones and wyrmlings,
  a lantern to keep lit), repeatable from the calendar after the story battle.
- **Gravity switches**: jade switches that toggle a room's gravity volumes (low gravity 0.45×). The
  base jump never changes; only the room's own volumes do, so geometry stays valid.

## Main story (chapters 17–22)

| Chapter | Quests |
|---|---|
| 17 Lanternfall (SS3–WM1) | The Lantern Run (sail from the Starsea Launch) · Crystal and Jade (exchange; Endurance jades) · Will Manifest (break through beyond the Expanse's ceiling) · A Presence of One's Own (train Presence in the Shoals) |
| 18 Blackmast (WM1–2) | The Purser's Ledger (Gu is with Voss) · Gunners' Battery · The Admiral (Admiral Voss; Gu flees into the Hollow Wake) |
| 19 Wyrmnest (WM2–3) | Star-Tier Beasts (tame a Comet Sparrow) · A Hollowed Brood (the meter above 49%; Lantern Incense) · The Last Egg (the Hatchling Wyrm egg) · The Master's Seat (Sect Master succession in the valley) |
| 20 The Star Wardens (WM3–SL1) | The Citadel (the Wardens; Shen Lian the aspirant) · The Observatory (the Sphere comprehension) · Sphere Lord · The Orbit Ruins (gravity switches; the Orbit Hermit teaches the Space Dao) |
| 21 Ash and Tide (SL1–2) | Cinder Fields · Kharn's Pyre (spare or slay) · The Tide Breaks (the Hollow Tide battle) · Star Warden (the title; the wyrm hatches) |
| 22 The Lantern Heart (SL2–3) | The Leviathan's Maw (optional field boss) · Lu's Lantern (the Lantern Heavenly Flame) · Greyfall (Shen Lian stays behind; the Frontier hook) |

## S43–S49 additions in v1.2

- **Confucian path** (a path layer like Soul or Buddhist): Righteous Qi, +25% against Hollow and demonic
  foes; written-word techniques whose power scales with Insight. Taught at the Star Chandlery by the
  scholar-lanternwright.
- **Brush** and **bell** weapon families: the brush writes a talisman effect with each technique; the
  bell supports (stun ring, Qi Seal).
- **Sword Domain**: a jian wielder's Sphere is labelled Sword Domain and adds cutting hits.
- **Copperjaw Beetle swarm**: an optional box; the swarm grows offline when fed ore; damage scales with
  log(population); a mutation can raise a Queen; Wood counters it.
- **Beast Taming Dao tier 4.**
- **Lantern Heavenly Flame**: absorbed in the Flame Heart.

## Build phases

- **A · Foundation.** The zone, the Lantern Run from the Starsea Launch, currency and Endurance, the
  zone ceiling, Lanternfall Harbor and the Drifting Shoals, Star Jellyfish and Comet Sparrow,
  Will Manifest, Presence, slot 12, chapter 17.
- **B · Blackmast and Wyrmnest.** Pirates, Pirate Gunner, Admiral Voss and the Presence clash; Nest
  Guardian and Hollowed Wyrmling; Hollowing thresholds and cleansing; star-tier pets and the wyrm egg;
  Sect Master; chapters 18–19.
- **C · Citadel and Orbit Ruins.** Star Wardens, Sphere comprehension, Sphere Lord and the Sphere,
  Sword Domain, gravity switches, Gravity Golem and Orbit Moth, Space Dao, Dao tier 6, Confucian path;
  chapter 20.
- **D · Ash and Tide.** Ashen Reach, General Kharn and the Sphere clash, Tidebreak Front and the Hollow
  Tide battle, Star Warden title, the wyrm companion, brush and bell, the beetle swarm, Beast Taming
  tier 4; chapter 21.
- **E · Nebula and the Lantern Heart.** Nebula Deep, the Leviathan, the Lantern Heart and its flame,
  Law pills and Sphere Lord 3; chapter 22; art, music and docs wrap-up.

## Attunement numbers

Starsea Endurance uses the Storm Ward rules with four new jades (Tide, Comet, Wick and Void Jade) and
star shards: raising a jade from level n to n + 1 costs n + 1 shards up to 22, so a full set gives
88 plus the base 2 of any character who has crossed the Starsea (the Voyager of the Starsea title).
Rooms ask for their region's value.
