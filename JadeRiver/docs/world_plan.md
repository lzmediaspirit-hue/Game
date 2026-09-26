# World plan · the whole road, and Acts IV, V and the Epilogue

This page is the world-expansion plan of P10 (`docs/roadmap_master_ui.md` §3, items M2 and M4). It does three things:

1. It sums up every act on two tables: the three acts that are built and the three that are not.
2. It plans v1.3 Star Frontier (Act IV), v1.4 Outer Heavens (Act V) and v1.5 World Genesis (the Epilogue) region by
   region: rooms, biome, levels, Laws, Qi density, attunement, hidden maps, travel, set pieces and bosses.
3. It gives each new act two routes, a main one and an alternate, and says where they join.

Sources: Build Prompt v2 (S17, S18, S19, S28, S43, the unlock timeline, "v1.1 to v1.5", "Later zones at a glance"),
`data/zones.json`, `data/rooms/`, `docs/act2_design.md`, `docs/act3_design.md` and `docs/movement.md`. Where the
Build Prompt gives a name it is kept: the zones, currencies, attunements, monsters and bosses, Lu's World, the Beast
Sovereign Reaches, the Tide Edge, the Relic Worlds, the Keeper of the Crossing and Yan Heng. Every other place and
person on this page is new and original to Jade River.

Each act still gets its own design page when its build starts, as `act2_design.md` and `act3_design.md` did. That page
may move a room or a number. This plan fixes the shape: the regions, their bands, the routes and the hidden places.

---

## 1. The whole game at a glance

Room counts for the built acts are counted from `data/rooms/` (168 rooms). Regions are the mapped regions in
`data/zones.json`; story, crossing and hidden regions are in brackets.

| Act | Version | Zone (tier) | Levels | Realms | Regions | Rooms | Biomes | Laws | Qi density | Attunement | Currency (everyday / high) | Headline system |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Prologue and I | v0.4–v1.0 | Jade River Valley (1) | 0–63 | Mortal → Heaven Glimpse 3 | 20 (+2) | 81 | River village, reed marsh, bamboo, quarry, falls, gorge, cliffs, mist peaks, two sect grounds, the Hidden Vale | Water, Wood, Earth | 0.8–1.5; springs 2–3 | None | Silver taels / Spirit Stones | The cultivation loop, the training sects, your own sect and the account of twelve |
| II | v1.1 | Azure Expanse (2) | 55–81 (fields 64–81) | Sage 1 → Sage Sovereign 3 | 10 (+1) | 46 | Storm plains, frozen heights, mirror lake, gale canyons, desert and tomb, sky wreck | Five elements, Wind, Thunder | 1.2–2.0 | Storm Ward 10 → 60 | Spirit Stones / Sage Crystals | Zone ceilings and attunement; the Starsea crossing |
| III | v1.2 | Lantern Star Field (3) | 82–99 | Will Manifest 1 → Sphere Lord 3 | 10 (+1) | 41 | Starlit shoals, pirate haven, wyrm isles, gravity ruins, ash fields, the Tide front, nebula | Fire, Metal, Space (weak), Star | 1.5–2.5 | Starsea Endurance 20 → 90 | Sage Crystals / Star Jade | Presence and the Sphere; the Hollowing above 49% |
| IV | v1.3 | Star Frontier (4) | 100–120 | Law Touching 1 → Heaven's Threshold | 10 (+1) | 64 | Six broken worlds: an ash-fall volcano world, a drowned rain-forest, an iron orchard, a barrow battlefield, sun-and-moon marches, a world where time frays | All elements, Space, Time (weak), Life and Death | 2.0–3.0 | Law Attunement 30 → 120 | Law Crystals / Monarch Jade | World Laws (the Z step) and the Dao Sigil; Soul Bands (P8b) |
| V | v1.4 | Outer Heavens (5) | 121–165 | Inner Heaven 1 → 9 | 8 (+ each character's Inner World) | 57 | Sky-plains and ramparts, dead world-shards, grey refuges, a small river world, beast grasslands, the unravelling edge of the made world | All Laws, strong Space and Time | 2.5–4.0 | Hollow Ward 50 → 200 | Heaven Pills / Worldseed shards (not sold) | The Inner World |
| Epilogue | v1.5 | The River (no tier) | 166 + Genesis Mastery ÷ 10 | World Genesis | 3 (+ woven and restored worlds) | 17 | The River's headwater, memory rooms of every act, the unwoven shore | Every Law; a woven world holds up to four | 3.0–4.0; a woven world sets its own | None | Worldseed shards / Heaven Pills | World Genesis: walk the River, restore, weave, seed life, mend the Hollowing |

| Act | How the player arrives | Travel inside the act | Routes |
|---|---|---|---|
| Prologue and I | Lu's boat to Lotus Ferry | Walking; teleport stones from Qi Kindling 3 (Stoneford, the two sects, the Hidden Vale); flight from Cloud Stride 1; dungeon gates; hidden portals from Spirit Awakening 2 | Today one spine (Willow Path → Stoneford → Caravan Road → Deepwater Bend → Whitewater Gorge → Crane Cliffs → Mist Peak → Summit Ridge) and one spur (Reed Marsh → Bamboo Grove → Crane Falls → Cleansing Peak). Level bands and sealed gates fix the order |
| II | The Ascension Gate on Mist Peak to Cloudgate Port | Sky-ship to the Alliance Gate; teleport stones (Cloudgate, Nine Peaks, Sunscar, Skyport Wreck); Starsea vessels | Today a hub (Cloudgate Port) with spokes; Storm Ward bands fix the order (M2) |
| III | The Lantern Run from the Starsea Launch | Warden skiffs from the Harbor and the Citadel; teleport stones (Lanternfall, Citadel); gravity switches | Today two hubs (Harbor, Citadel) with spokes; Endurance bands fix the order |
| IV | The Frontier Run from the Tidebreak Bastion | The Gate Ring's six world gates; causeways between worlds; eight teleport stones; Grapple from the rope dart | **Main:** the Ashborn road (Emberwane → Iron Orchard). **Alternate:** the Barrow road (Rainroot Mere → Kingsgrave Barrows). **Join:** the Throne Heart, from Law Touching 3 |
| V | The Heavengate from the Rite Chamber | Seven teleport stones; relic charts to the instanced Relic Worlds; your Inner World from any safe room | **Main:** the Front road (Relic Drift → the lower Beast Sovereign Reaches). **Alternate:** the River road (Refuge Isles → Lu's World). **Join:** Duskwall, at Inner Heaven 6 |
| Epilogue | The Keeper of the Crossing's ferry from Lu's World | Walking the River: a landing in every zone and every woven world; the ferry | **Main:** the Memory road (the memory rooms in act order). **Alternate:** the Loom road (weave, restore, seed, mend). **Join:** the Unwoven Shore |

### A second route for the built acts (later, not part of P10's build)

M2 is Partial because each built act's regions are ordered by attunement bands. One cross-link per act would give each
a second road without new rooms:

| Act | Cross-link | Gives |
|---|---|---|
| I | A waterfall path from Crane Falls to Deepwater Bend, sealed until Qi Unfurling 1 | The marsh spur and the Caravan Road become two roads to Deepwater Bend (levels 10–20 on both) |
| II | An edge from Rimefrost Summit to the Canyon Mouth, sealed at Storm Ward 40 | The north road (Thunderhorn → Rimefrost → Gale Canyons) beside the Alliance road (Port → Nine Peaks → Gale Canyons) |
| III | A Warden skiff lane from the Hatching Cave to the Tumbling Stair | Shoals → Wyrmnest → Orbit Ruins beside Harbor → Citadel → Orbit Ruins (levels 85–93 on both) |

---

## 2. Rules for every new room

### Authoring

- One module per act in `tools/data/`, in the pattern of `tools/data/lantern.py`: `REGIONS`, `STONES`, `VOYAGES`, a
  `zone()` row for `data/zones.json`, and one function per region that calls `world.town()`, `world.field()`,
  `world.interior()`, `r.portal()` and `r.edge()`. Suggested names: `frontier.py`, `heavens.py`, `river.py`.
- Room ids take a two-letter prefix per region. The prefixes below are not in use today.
- While an act is built in phases, portals to unbuilt regions are sealed gates to rooms marked `planned` (S17).
- Instanced rooms (dungeons, secret realms, story instances, Relic Worlds, memory rooms) are exempt from the
  reachability walk; the test checks their entry points (S17).

### Types, widths and contents

| Type | Screens (1,280 units) | Contents (S17) |
|---|---|---|
| Town, fortress | 2–3 | No nodes; shrine, storage, stations; teleport stone in one room per region |
| Field | 3 (2 for a tall room) | 3–6 nodes, 4–8 breakables, 0–1 chest |
| Path | 2 | 1–2 nodes, 2–4 breakables, a signpost |
| Rest | 1–2 | 1–2 nodes, a shrine or Qi spring |
| Insight | 1 | An insight stone or Law stele; flat by design, like the Condensing Hall |
| Dungeon room | 2 | 0–2 nodes, 4–6 breakables, a chest at the end |
| Boss arena | 2–3 (up to 4) | Room to dodge; ledges are not reward ledges |
| Secret | 1–2 | One reward and the rule that hides it |

### Verticality

Every room passes the room lint (`tools/data/room_lint.py`, rules in `docs/movement.md`):

- two tiers above the ground and a raised route across 40% of the width;
- 30% of breakables and a third of gathering nodes on tiers; chests on the highest tier or an optional ledge;
- two ways up to every required tier; landings at least 80 × 60;
- built tiers on the 88 grid, natural ones on the 100 grid; blocks 40, 60, 80 or 110;
- everything required reachable with the arts of the room's lowest realm;
- every later ledge out of reach of the arts the band already has, and within its own art's reach.

From Act IV on every character has flight (ceiling 340), the double jump, Wall-Step, the glide and Wind Blink. So:

- a room that allows flight must still pass the lint without it, because no-flight volumes and landings exist;
- ledges above 340 are reached by updraft columns, as on the Sky Ledges;
- a later ledge must sit above what flight reaches (in a room that allows flight) or in a no-flight room;
- Act IV's later ledges need the rope dart's Grapple (S43, v1.3: a pull to a marked hook within 300 units). Act V and
  the Epilogue add no traversal art, so their later ledges use Grapple and updrafts.

### Attunement, Laws and hazards

- Field rooms ask their region's attunement; safe rooms ask nothing (`progression_authority.gd:224-229`).
- Each hazard is answered by a stat (`data/hazards.json`). New hazards are listed per act.
- **Laws per room (new, v1.3).** `zones.json` holds one `laws` list per zone, and the Z step reads it (S12 step 7,
  S28). The Frontier's worlds and the Outer Heavens' regions each favour different Laws, so v1.3 adds an optional
  `laws` list on a room that overrides the zone's list for the Z step. This is a code change in v1.3, named here so the
  room data carries the field from the start.

---

## 3. Act IV · the Star Frontier (v1.3)

### Premise

Past the Greyfall Breach the Tide runs out into the dark. At the far edge of the Starsea drift the broken worlds of
the **Star Frontier**: whole worlds that the Tide gnawed in an older age, each still holding a few of its Laws. The
Star Wardens keep one fortress there, **Lodestar Keep**, where the Frontier Run comes in. Beyond it six worlds hang in
a ring around a still centre, the **Anchor Spire**, where seven wells of the elements meet.

Five threads carry the act:

1. **Shen Lian.** Taken by the Tide at Greyfall (Act III). He is found in the Unwinding as Hollowed Shen Lian: save
   him or defeat him (the flags `shen_lian_saved` or `shen_lian_defeated`).
2. **Elder Gu's ledger.** Gu, Hollowed, keeps the ledger in the Unwinding (Hollow Elder Gu). Its last page names who
   first paid the Grey Pilgrim.
3. **The Ashborn.** Their world, Emberwane, is going cold as its core fire dies. Kharn spared or slain (`kharn_spared`,
   `kharn_slain`) decides how Ash Queen Seralet's court receives you. The alliance comes at Monarch 3.
4. **The empty throne.** Kingsgrave's throne has had no living Monarch since the old war; what remains of the last
   one, the Remnant Monarch, still guards it. After him, the throne contest gives the Throne-Sworn title at Monarch 2.
5. **Lu's crossing.** Five journal pages (21–25). The last, in the Unwinding, shows Lu walking into a room that had not
   happened yet: the first hint of walking the River.

### Laws, Qi, attunement, money

| | Value |
|---|---|
| Zone | `star_frontier`, tier 4, Levels 100–120, ceiling `heavens_threshold` |
| Laws | All elements, Space, Time (weak), Life and Death. Each world favours two (per-room `laws`, §2) |
| Qi density | 2.0–3.0 |
| Attunement | Law Attunement 30 → 120. Four jades: **Edict, Balance, Thread and Hour Jade**, levelled with law shards; 15 levels at 2.0 each gives 120 (tuning value) |
| Currency | Law Crystals / Monarch Jade; the exchange is in the Keep Market |
| New hazards | Remnant Weight (Will; Kingsgrave and the Throne Heart, S28's leftover Weight), rust rain (Body; Iron Orchard), siren song (Spirit; Rainroot Mere), time fold (Spirit; the Unwinding). Reused: scorching heat, cold, falling rocks, deep water, current |

### Regions and rooms (64)

Room prefixes: `lk`, `ew`, `rr`, `io`, `kb`, `th`, `tw`, `uw`, `as`, `wl`; the Frontier Run crossing is `fc`.

| # | Region | Road | Biome | Levels | Law Att. | Qi | Laws favoured | Rooms | Monsters and bosses |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Lodestar Keep (town, teleport stone) | Hub | A star-fort of the Wardens on a drifting shard, docks on the dark | — | 0 | 2.0–2.2 | — | 5: Frontier Quay (dock) · Keep Market (exchange, teleport stone) · Hall of Laws (insight) · Gate Ring (the six world gates) · Wardens' Barracks (rest) | — |
| 2 | Emberwane | Main | An ash-fall volcano world whose core fire is failing; black slopes, cooling lava, the Ashborn capital under a red sky | 100–106 | 30–45 | 2.0–2.3 | Fire, Earth | 6: Ashfall Slopes · Cinder Flats · Magma Stair (tall) · Ember Court (town, teleport stone) · Hearth of Queens (insight) · The Cold Hearth (secret) | Cinder Hound (100–105), Magma Behemoth (103–106), Ash Legionnaire (100–106); field boss **Pyreback**, an old Magma Behemoth (106, new) |
| 3 | Rainroot Mere | Alternate | A drowned rain-forest under rain that never stops; canopies over black water, a sunken sect | 100–106 | 30–45 | 2.1–2.4 | Wood, Water | 6: Rainroot Shallows · Siren Canopy (canopy decks) · Colossus Deeps (deep water, rafts) · Drowned Pavilion (rest, teleport stone) · Sunken Library (secret) · Bloom Mother's Hollow (boss arena) | Bloom Siren (100–105), Tidal Colossus (103–106); field boss **the Bloom Mother** (106, new) |
| 4 | Iron Orchard | Main | A metal world of iron-barked trees, rust rain and a dead forge-tree the size of a mountain | 104–110 | 50–65 | 2.2–2.5 | Metal, Earth | 6: Rust Orchard · Mantis Rows · Orchard Lodge (rest, teleport stone) · Forge-Tree Gate (dungeon) · Heart of the Forge-Tree (boss arena) · The Seed Vault (secret) | Iron Mantis (104–108), Magma Behemoth (107–108, the forge vents), Rust Wraith (106–110); dungeon boss **the Forge-Tree Warden** (110, new) |
| 5 | Kingsgrave Barrows | Alternate | A battlefield world of barrow-mounds, broken banners and a red dusk that never ends | 104–110 | 50–65 | 2.2–2.5 | Life and Death, Metal | 6: Barrow Field · Broken Legion Road · Mourners' Camp (rest, teleport stone) · The Remnant Battlefield (event) · The Nameless Barrow (secret) · Marshal's Mound (boss arena) | Remnant Will (104–110), Rust Wraith (106–110); field boss **the Barrow Marshal** (110, new) |
| 6 | Throne Heart | Join | The fallen capital at the battlefield's centre: a palace of cracked jade under standing Weight | 109–114 | 70–80 | 2.5–2.7 | Life and Death, Space | 4: Throne Causeway · Hall of Fallen Thrones (dungeon) · Contest Floor (arena, safe between bouts) · Remnant Throne (boss arena) | Remnant Will (109–114), Time-Worn Specter (109–114); **Remnant Monarch** (113) |
| 7 | Twinlight Marches | Shared | A world under a sun and a moon that never set: a burning day side, a frozen night side, a dusk line between | 110–116 | 80–95 | 2.5–2.8 | Fire by day, Water by night, Space | 6: Noon Steppe · Sunroc Eyrie (tall, updrafts) · Dusk Line · Moonfen · Twinlight Waystation (rest, teleport stone) · The Hour Between (secret) | Sun Roc and Radiant Lion (110–116, day side), Moon Moth and Shade Serpent (110–116, night side) |
| 8 | The Unwinding | Shared | The world at the Tide's edge, where time frays: rooms loop, rain falls upward, grey tide-fog | 113–118 | 95–110 | 2.6–2.9 | Time, Space | 7: Frayed Verge · Looping Stair · Frontline Bulwark (fortress, safe, teleport stone) · Timekeeper's Cell (insight) · Greyfold Breach · The Ledger Vault (boss arena) · Shen Lian's Stand (boss arena) | Time-Worn Specter (113–114), Ash Legionnaire (113–117), Hollowed Legionnaire (115–118, new, a Hollowed variant as the Hollowed Wyrmling is); **Hollowed Shen Lian** (117), **Hollow Elder Gu** (118) |
| 9 | Anchor Spire | Shared | A spire of seven-coloured stone at the Frontier's still centre | 118–120 | 110 | 3.0 | All | 3: Anchor Stair (path) · Sigil Sanctum (insight, teleport stone) · Rite Chamber (safe) | — |
| 10 | The Seven Wells (element dungeons) | Shared | Seven wells, one per power, each a descent into one element | 118–119 | 120 | 3.0 | One each | 14: two rooms per well (the descent, the Warden's chamber): Greenwood · Ember · Loam · Brightsteel · Coldspring · Shade · Noon | The seven Element Wardens (119), one per well |
| — | The Frontier Run (crossing) | — | The dark past the Starsea | 99–100 | — | 1.0 | — | 1: the crossing instance | Star wind, Hollow drifts |

Room count: 5 + 6 + 6 + 6 + 6 + 4 + 6 + 7 + 3 + 14 + 1 = **64** (49 in the open worlds, 14 in the Wells, 1 crossing).

Monster Levels in the table are the Levels used in that region. Each stays inside the species' range in the Build
Prompt's "Later zones at a glance" (for example Magma Behemoth 100–108 is split between Emberwane and the Iron Orchard).

The Build Prompt's "six worlds" are Emberwane, Rainroot Mere, the Iron Orchard, Kingsgrave (the Barrows and the Throne
Heart), the Twinlight Marches and the Unwinding. Its "seven element dungeons" are the Seven Wells.

### Routes and cross-links

The two roads cover the same Levels (100–110), the same attunement band (30–65) and the same number of bosses, and each
offers two Laws to raise to affinity 3 for the Monarch breakthrough (Law Touching 3 → Monarch 1 asks for two Laws at
affinity 3). They join at the Throne Heart.

| Road | Regions | Laws it teaches | Why take it |
|---|---|---|---|
| Main: the Ashborn road | Emberwane → Iron Orchard → Throne Heart | Fire, Earth, Metal | The Ashborn story at first hand; the forge-tree's metals |
| Alternate: the Barrow road | Rainroot Mere → Kingsgrave Barrows → Throne Heart | Wood, Water, Life and Death, Metal | The remnant-will battlefields early; the drowned sect's Law manuals |

| Link | From → to | Kind | Opens |
|---|---|---|---|
| Frontier Run | Tidebreak Bastion ↔ Frontier Quay | Voyage (`fc_frontier_crossing`, base 120 s) | Sphere Lord 3 and `act3_complete`; the first crossing is a story ride on the Wardens' frigate, later ones need the Frontier chart and any vessel |
| The Gate Ring | Lodestar Keep ↔ the first room of each world | Six gates | Each world's first attunement need and its chapter; after the join every gate stays open, so any world can be revisited |
| Slag Bridge | Magma Stair ↔ Rust Orchard | Edge | Law Touching 2 |
| Drowned Causeway | Colossus Deeps ↔ Barrow Field | Edge | Law Touching 2 |
| Mourning Road (the switch) | Mantis Rows ↔ Broken Legion Road | Edge | Law Touching 2; changes road halfway |
| Rust Causeway (join, main) | Forge-Tree Gate → Throne Causeway | Edge | Law Touching 3 and chapter 24 done |
| Legion Road (join, alternate) | Broken Legion Road → Throne Causeway | Edge | Law Touching 3 and chapter 24 done |
| Dusk Gate | Throne Causeway ↔ Noon Steppe | Gate | Monarch 1 |
| Grey Fold | Moonfen ↔ Frayed Verge | Edge | Monarch 3 |
| Seven-Coloured Stair | Frontline Bulwark ↔ Anchor Stair | Sealed gate | Half-Heaven Monarch |
| Well mouths | Sigil Sanctum → each well | Dungeon gates | The Greenwood Well at Half-Heaven Monarch, because the step to Dao Sigil needs one power refined and Wood comes first; each later well when the previous Warden falls, from Dao Sigil (the Sigil's order: Wood → Fire → Earth → Metal → Water → Yin → Yang) |

### Travel

- **Arrival:** the Frontier Run, a Starsea voyage from a new dock at the Tidebreak Bastion to the Frontier Quay. A
  Frontier chart is readings from sighting stones at the Greyfall Breach plus void ink (S16). An optional Warden Barque
  (speed 2.0) is built at the Keep once smithing and formations reach Expert (tuning proposal).
- **Teleport stones (8):** Keep Market, Ember Court, Drowned Pavilion, Orchard Lodge, Mourners' Camp, Twinlight
  Waystation, Frontline Bulwark, Sigil Sanctum.
- **Gates:** the Gate Ring's six world gates; the Seven-Coloured Stair; the well mouths.
- **Flight** is allowed in the open fields. **No flight:** the Ember Court (the Ashborn forbid it over their city), the
  Throne Heart and the Kingsgrave barrows (Remnant Weight), the Unwinding (time folds break a flight), the Seven Wells
  (dungeons).
- **Grapple:** the rope dart (v1.3) hooks to marked points; Grapple points stand in the Iron Orchard's canopy, the
  Sunroc Eyrie and the Looping Stair, and reach this act's later ledges.

### Hidden maps

| Hidden map | Where | Kind | How it is found | What it holds |
|---|---|---|---|---|
| The Cold Hearth | Emberwane, behind the Magma Stair | Secret realm: halved Qi, Fire techniques silenced, 10 minutes | A hidden portal at a cold vent, shown by a Spirit Sense pulse | A Fire essence (rank 6), Ashborn standing, Lu's page 21 |
| Sunken Library | Rainroot Mere, under the Drowned Pavilion | Secret room | Breath Control down the flooded stair | Wood and Water Law manuals (Law affinity), Lu's page 22. Each road holds one of pages 21 and 22; the Gate Ring reaches the other |
| The Seed Vault | Iron Orchard, behind the Orchard Lodge | Hidden room | A cracked wall that a Body threshold breaks | Iron seeds for the herb garden; a Metal essence |
| The Nameless Barrow | Kingsgrave Barrows, off the Barrow Field | Inheritance with a moral choice | A Weight zone only a Will threshold crosses | A dead king's legacy art (an Inner Art) or his sword, not both |
| The Hour Between | Twinlight Marches, on the Dusk Line | Secret realm on the calendar | Opens only during the eclipse, when sun and moon cross (a calendar event every few in-game days) | The Frontier Heavenly Flame (S44, v1.3); Yin and Yang essences |
| Yesterday's Room | The Unwinding, on the Looping Stair | Hidden room | Walk the loop backward, which the Time Dao at tier 2 shows | Lu's page 25; a moment of Shen Lian before the Tide took him |
| A sealed Relic World | Throne Causeway | Sealed gate (a hook) | Seen from Law Touching 2 | Opens at Inner Heaven 3 (v1.4) |
| Grapple ledges | Iron Orchard, Sunroc Eyrie, Looping Stair | Paths Above rows | The rope dart's Grapple | Chests; the Codex's Paths Above tab |
| Lu's pages 23 and 24 | The Remnant Throne; the Twinlight Waystation's roof | Pickups | Reached on the shared road | The journal |

### Set pieces and bosses

| Region | Set pieces | Bosses |
|---|---|---|
| Lodestar Keep | The Hall of Laws' first stele: Law affinity 1, which Law Touching 1 asks for | — |
| Emberwane | **Keep the Hearth**: a defence of the Hearth of Queens against the cold and the Tide, the lantern defence's rule turned to fire. Repeats from the calendar | Pyreback (field) |
| Rainroot Mere | **The Drowned Choir**: a survival event under siren song (soul damage, Confusion) while the rafts cross | The Bloom Mother (field) |
| Iron Orchard | **The Rust Harvest**: a timed gathering run under rust rain | The Forge-Tree Warden (dungeon) |
| Kingsgrave Barrows | **The Remnant Battlefield** (Law Touching 2): ghost armies replay an old war and the player holds a banner. Repeats from the calendar | The Barrow Marshal (field) |
| Throne Heart | **The throne contest** (Monarch 2): three bouts against seeded rivals (Ran Yi, the Grave Duke; Vorra, an Ashborn claimant; Jin Ceyang, a sword cultivator of the Marches). Winning gives the Throne-Sworn title (Heavenforce inside this world only, S28) | Remnant Monarch (113): phases, Monarch's Weight as a telegraphed field, P9 standard |
| Twinlight Marches | **The eclipse**: sun and moon cross; the favoured Law flips between Fire and Water for its length and the Hour Between opens | — |
| The Unwinding | **The Frontline**: a fortress defence at the Frontline Bulwark (S28 front-line fortresses). **Shen Lian's Stand**: the save-or-defeat fight | Hollowed Shen Lian (117), Hollow Elder Gu (118) |
| Anchor Spire | **The Dao Sigil** (Half-Heaven Monarch): the seven powers refined in order, the tolerance shown, the starting-rank preview. **The Inner World forming** in the Rite Chamber is v1.4's (the Frontier's ceiling is Heaven's Threshold) | — |
| The Seven Wells | Each well is a descent to its Warden; each Warden drops its element's essence | Seven Element Wardens (119) |

### Realms and systems by stage

| Stage | Unlocks (unlock timeline, v1.3 row, S43–S49 v1.3 row) | Where |
|---|---|---|
| Sphere Lord 3 | The Frontier Run; Law Crystal and Monarch Jade exchange; Law Attunement jades; the ceiling lifts to Heaven's Threshold | Tidebreak Bastion; Keep Market |
| Law Touching 1 | World Laws and the Z step; Law Qi (×2.2) | Hall of Laws |
| Law Touching 2 | Remnant-will battlefields; dual blades, umbrella, whip and rope dart (Grapple); Beast Taming Dao tier 5 | Kingsgrave Barrows; the Keep's and the Ember Court's smiths |
| Law Touching 3 | Monarch Condensing Pill recipe; throne eligibility | Hall of Laws; Contest Floor |
| Monarch 1 | Monarch's Weight; Monarch Qi (×2.8, after conversion) | Throne Heart |
| Monarch 2 | Throne-Sworn title; Beast Taming Dao tier 6 | Contest Floor |
| Monarch 3 | Ashborn alliance; the Time Dao (Timekeeper Gong Yi) | Ember Court; Timekeeper's Cell |
| Half-Heaven Monarch | Dao Sigil screen; the Greenwood Well (the first power) | Sigil Sanctum |
| Dao Sigil | The other six wells (element dungeons); starting-rank preview | Anchor Spire |
| Heaven's Threshold | Sigil Anchor Pill; the Rite Chamber | Anchor Spire |

The Seven Wells' ordinary drops are essences of rank 5 to 7, so an ordinary Inner Heaven start is rank 5 to 7 (S28:
starting rank = lowest power's rank, 7 at most by normal means). The starting-rank preview warns before a low essence is
refined.

### Main story (chapters 23–28, outline)

Before the join each chapter can be finished on either road; the main quest never asks for both.

| Chapter | Quests |
|---|---|
| 23 The Frontier Run (SL3 → LT1) | Beyond Greyfall (the Frontier Run) · The Keep (Keep-Warden Sima Rou) · Crystal and Law (exchange, Law Attunement) · A Law Touched (Law-Reader Qi Wan's stele; Law Touching 1) · Two Gates (the Gatewright Nie Hua opens Emberwane and Rainroot) |
| 24 Two Roads (LT1 → LT3) | Main: The Queen Who Is Cold (Ember Court; Hearthward Oskra) and The Forge-Tree (Iron Orchard; Orchard-Keeper Luo Geng). Alternate: The Drowned Choir (Rainroot; Canopy Hermit Zhuo Ye) and The Banner Holds (Kingsgrave; Barrow-Singer Yin Ce). Both end with two Laws at affinity 3 and the Monarch Condensing recipe |
| 25 The Empty Throne (LT3 → M2) | The Causeway · The Hall of Fallen Thrones · Monarch (the breakthrough, Law Touching 3 → Monarch 1) · Remnant Monarch · The Contest (Throne-Sworn) |
| 26 Sun and Moon (M2 → M3) | The Dusk Line (the eclipse) · The Hour Between (the Frontier Heavenly Flame) · The Queen's Oath (the Ashborn alliance at the Ember Court, reached through the Gate Ring on either road) |
| 27 The Unwinding (M3 → HHM) | The Grey Fold · The Timekeeper (Time Dao) · The Frontline (Captain Liang Ke) · The Ledger (Hollow Elder Gu) · Shen Lian's Stand (save or defeat) · A Heavenly Dao insight (Half-Heaven Monarch) |
| 28 Seven Wells (HHM → HT) | The Sigil (Sigil-Keeper Cen Wu) · The Greenwood Well (Wood; Dao Sigil) · the Ember, Loam, Brightsteel and Coldspring Wells (five powers; Heaven's Threshold) · the Shade and Noon Wells (all seven, which Inner Heaven asks for) · The Rite Chamber (Rite-Mother Dai Huan; the Outer Heavens hook) |

### Headline systems

- **World Laws and the Z step** (S28, S12 step 7): a technique whose element matches the room's Laws deals 1.10–1.15;
  one whose Law is missing deals 0.85. Law affinity is raised at each world's Law steles and by fighting under its Laws.
- **The Dao Sigil** (S28): seven powers refined in the order Wood → Fire → Earth → Metal → Water → Yin → Yang, the
  tolerance from total Dao tiers and stability, the starting-rank preview; Heaven's Threshold at five of seven.
- **Soul Bands (P8b)**: built inside v1.3 from the design in `docs/soul_bands_design.md` (P8a; that page is not
  written yet). The unlock stays Spirit Awakening 1, so a character who arrives in the Frontier can take bands at once
  from any zone's beasts. Every beast from Sage Sovereign up is already `beast_rank` 9, so the Frontier's beasts
  (Cinder Hound, Magma Behemoth, Tidal Colossus, Iron Mantis, Sun Roc, Radiant Lion, Moon Moth, Shade Serpent) are rank 9
  too. P8a must say what sets their bands above an Expanse beast's (an age within rank 9, or a tier above it).
- **Also in v1.3 with no place of their own:** Monarch's Weight; Sovereign pets; sect levels 11–20; the Time Dao; the
  four new weapon families; Beast Taming Dao tiers 5–6.

---

## 4. Act V · the Outer Heavens (v1.4)

### Premise

When the Inner World forms in the Rite Chamber, the Heavengate opens above it onto the **Outer Heavens**: the open sky
between worlds, where those who carry a world inside them live and fight. At the far edge of the made world the Hollow
Tide rises, the loose thread of Yan Heng's loom. Two front fortresses hold the line, **Dawnwall** at the Heavengate and
**Duskwall** near the edge.

Threads:

1. **The front.** Marshal Lei Guang's fortresses; front missions from Inner Heaven 2; Yan Heng's Herald at Duskwall.
2. **Relic Worlds.** Worlds the Tide ate, drifting dead. Salvage them now; restore them in the Epilogue.
3. **Lu's World.** Lu wove a small world once and left it. His study holds the river quest line, a Genesis requirement.
4. **The Beast Sovereigns.** The Sky Sovereign Wyrm rules the Reaches. The Hatchling Wyrm companion from Act III finds its
   kin there; Primordial pets come home to the Inner World.
5. **Shen Lian.** Saved in Act IV, he fights beside you as a companion. Defeated, he is a name on Duskwall's wall.

### Laws, Qi, attunement, money

| | Value |
|---|---|
| Zone | `outer_heavens`, tier 5, Levels 121–165, ceiling `inner_heaven_9` |
| Laws | All Laws, strong Space and Time |
| Qi density | 2.5–4.0 |
| Attunement | Hollow Ward 50 → 200. Four jades: **Dawn, Rampart, Lamp and Loom Jade**, levelled with ward shards; 20 levels at 2.5 each gives 200 (tuning values) |
| Currency | Heaven Pills (a cultivation resource and money, S21) / Worldseed shards (not sold) |
| New hazards | Grey gale (Will; the March), stillness (Essence; Qi halved in the Relic Worlds), unravelling ground (Spirit; the Tide Edge, built as `crumble` volumes that do not come back while the Tide is up) |

The attunement shares its name with the Hollow Ward stat (a percentage, capped at 80%). The pages must show the
attunement in points and the stat in percent so the two never read as one number.

### Starting rank and the ceiling

S28: a character enters Inner Heaven at the rank of their lowest power (7 at most by normal means), earns ranks one by
one, and stops at start + 2 unless a ceiling breaker applies. So:

- a character may arrive at Inner Heaven 1 to 7. Regions and chapters open by chapter and Hollow Ward, never by rank,
  so a character with a low ceiling can still walk to the breakers;
- every road holds at least one ceiling breaker before the join (the table under Hidden maps).

### Regions and rooms (57, and the Inner World)

Room prefixes: `dn`, `gm`, `rd`, `ri`, `lw`, `bs`, `dk`, `te`. Relic World rooms use `rw`.

| # | Region | Road | Biome | Levels | Hollow Ward | Qi | Rooms | Monsters and bosses |
|---|---|---|---|---|---|---|---|---|
| 1 | Dawnwall (front fortress, teleport stone) | Hub | A fortress wall across a sky-bridge, banners, the Heavengate above it | — | 0 | 2.5–2.8 | 5: Heavengate Landing · Rampart Market (Heaven Pill exchange, teleport stone) · Marshal's Hall (interior; front missions) · Wall-Walk (the defence event) · Inner Gate (insight; your first way into the Inner World) | — |
| 2 | Greywind March | Shared | Grey sky-plains of floating turf, broken wall-lines and trenches where Hollow Knights patrol | 121–135 | 50–80 | 2.5–2.9 | 6: Broken Sky Road · Knightfall Trench · Drone Nests · Watchfire Post (rest, teleport stone) · The Severing Line (story) · Banner Hollow | Hollow Knight (121–135), Hollow Drone swarm (121–135); field boss **the Grey Standard-Bearer** (135, new) |
| 3 | Relic Drift | Main | A sea of dead world-shards, each a frozen moment of a world the Tide ate | 131–145 | 80–110 | 2.8–3.2 (halved inside a Relic World) | 14: Salvage Moorings (rest, teleport stone) · Wreck Lanes · four Relic Worlds of three rooms each (approach, heart, vault): **Saltglass World** (a sea turned to glass, 132–136) · **Bellwood World** (a forest of bronze bells, 135–139) · **Lanternless World** (a world whose stars went out, 138–142) · **the Ninefold Kiln** (a world of furnaces, 141–145) | Relic Guardian (131–145), Hollowed Survivor (131–145); each Relic World ends in a Relic Guardian elite |
| 4 | Refuge Isles | Alternate | Inhabited isles overrun by the Tide: grey villages to cleanse and rebuild (S19's Hollowed villages) | 131–145 | 80–110 | 2.8–3.1 | 7: Tidewrack Shore · Grey Refuge (a field until cleansed, then a town) · Survivor's Ford · Ashen Chapel (dungeon) · Cleansing Well (insight) · Last Lamp Shrine (rest, teleport stone) · Orchard of Ash | Hollowed Survivor (131–145), Hollow Knight (131–140), Hollow Drone swarm |
| 5 | Lu's World | Alternate (after the join, one boat ride from Duskwall) | A small, quiet river world: willows, a ferry, one village of woven people; its banks fraying where the Tide has touched | 141–150 | 110–125 | 3.2–3.5 | 5: River Mouth · Willow Reach · Ferry Village (town, teleport stone) · Boatman's Study (insight) · Frayed Bank | Hollow Drone swarm (141–150), Hollowed Survivor (141–150) at the frayed banks only |
| 6 | Beast Sovereign Reaches | Main before the join (lower), shared after (upper) | Vast sky-grasslands and wyrm-spine mountains ruled by beasts, above the Tide's reach | 141–160 | 110–165 | 3.0–3.7 | 8: lower: Wyrmspine Foothills · Grass Sea · Beastspeaker's Camp (rest, teleport stone) · Primordial Den (secret). Upper: Sovereign Plateau · Elder Wyrm Roost (tall, updrafts) · Transformation Pool (insight) · Sky Sovereign's Crown (story) | Elder Wyrm (141–160), Beast Sovereign (146–160); the Sky Sovereign Wyrm (not fought; its trial) |
| 7 | Duskwall (front fortress, teleport stone) | Join | The last fortress: a wall facing the grey, a watchtower over the edge | — | 0 | 3.2 | 4: Duskwall Gate (teleport stone) · Last Market · Tidewatch Tower (insight) · Herald's Breach (story) | — |
| 8 | Tide Edge | Shared | The edge of the made world, where the ground unravels into grey threads over the void | 151–165 | 165–200 | 3.6–4.0 | 8: Unravelling Shore · Primordial Graveyard · Herald's Road · Threadbare Flats · Nest of the Hollowed Primordial (boss arena) · The Frayed Horizon (story) · Worldseed Grove (secret) · The Pilgrim's Camp (secret) | Void Maw (151–165), Hollowed Primordial (151–165), Yan Heng's Herald (156–165), Hollow Drone swarm; **Hollowed Primordial** (158) |
| — | The Inner World | Each character's own | Generated from the seven powers (biomes), their ranks (size), Dao imprints and known Laws (S28) | The character's | — | Set by Heritage | Not authored; built by the same room format and world builder as zones | Corruption to cleanse or sever |

Room count: 5 + 6 + 14 + 7 + 5 + 8 + 4 + 8 = **57**.

Act V runs 45 Levels at 400 target minutes each (S29), three times Act IV's hours. Its extra hours come from the Inner
World, front missions and Relic World runs, not from more rooms.

### Routes and cross-links

| Road | Regions | Ceiling breaker on the way | Why take it |
|---|---|---|---|
| Main: the Front road | Greywind March → Relic Drift → lower Beast Sovereign Reaches → Duskwall | The Primordial Crucible Pill recipe (the Ninefold Kiln); the first step of the Mandate Bloodline (the Primordial Den) | Relic salvage for the Inner World; Primordial pets early |
| Alternate: the River road | Greywind March → Refuge Isles → Lu's World → Duskwall | The same recipe in Lu's hand (Boatman's Study); the Devouring Scripture (the Ashen Chapel) | Merit and visitors from the cleansed villages; the river quest line early |

| Link | From → to | Kind | Opens |
|---|---|---|---|
| Heavengate | Rite Chamber (Frontier) → Heavengate Landing | Ascension gate: one-way at the Inner World forming, two-way after | Inner Heaven 1 |
| March Gate | Wall-Walk ↔ Broken Sky Road | Edge | Chapter 29 |
| Drift Moorings (fork, main) | Banner Hollow ↔ Salvage Moorings | Edge | Inner Heaven 3 (Relic Worlds), chapter 30 |
| Refuge Ferry (fork, alternate) | Knightfall Trench ↔ Tidewrack Shore | Edge | Chapter 30 |
| Crossover (the switch) | Wreck Lanes ↔ Survivor's Ford | Edge | Chapter 30; changes road halfway |
| Relic charts | Salvage Moorings → each Relic World | Voyage to an instance | A relic chart per world (S16 charts) |
| Wyrmspine Pass | Wreck Lanes → Wyrmspine Foothills | Edge | Chapter 31 (main) |
| Lu's Mooring | Grey Refuge → River Mouth | Boat | Chapter 31 (alternate); after the join also from the Last Market |
| Grass Sea road (join, main) | Grass Sea → Duskwall Gate | Edge | Chapter 31 done |
| Frayed Bank road (join, alternate) | Frayed Bank → Duskwall Gate | Edge | Chapter 31 done |
| Sky Bridge | Duskwall Gate ↔ Sovereign Plateau | Edge | Chapter 33 |
| Tidegate | Herald's Breach → Unravelling Shore | Sealed gate | Chapter 32 done |
| Inner World | Any safe room → your Inner World | An intent, not a portal | Inner Heaven 1 |

### Travel

- **Arrival:** the Heavengate, after the Inner World forms (the set piece into Inner Heaven, S05).
- **Teleport stones (7):** Rampart Market, Watchfire Post, Salvage Moorings, Last Lamp Shrine, Ferry Village,
  Beastspeaker's Camp, Duskwall Gate.
- **Vessels:** relic charts take any vessel to an instanced Relic World (secret-realm rules: no flight, halved Qi, one
  Law, a time limit; S18).
- **Flight** everywhere in the open sky except: inside the fortresses' walls, in the Relic Worlds, in the Ashen Chapel,
  and on the Tide Edge's unravelling ground.
- **The Inner World** is entered from any safe room once it exists. The 24-hour offline cap belongs to it (S07).

### Hidden maps

| Hidden map | Where | Kind | How it is found | What it holds |
|---|---|---|---|---|
| Worldseed Grove | Tide Edge, with a second way in behind Banner Hollow in the March | Secret realm: no flight, halved Qi, 15 minutes | A hidden portal shown by a Spirit Sense pulse; the March's way opens from Inner Heaven 3 so a low start can reach it | One Worldseed Fruit per character (+1 rank and +1 ceiling); Worldseed shards |
| The Kiln vault | Relic Drift, the Ninefold Kiln | Vault | Three relic seals, one from each other Relic World | The Primordial Crucible Pill recipe |
| Lu's locked drawer | Lu's World, Boatman's Study | Hidden chest (a Spirit threshold) | A Spirit Sense pulse at Lu's desk | The same recipe in Lu's hand |
| The Chapel crypt | Refuge Isles, the Ashen Chapel | Hidden room (an Insight inscription) | Read the inscription | The Devouring Scripture (a breaker with instability and soul injuries); taking it is a demonic deed (sin, S49) |
| Primordial Den | Beast Sovereign Reaches, lower | Secret room | The Hatchling Wyrm companion leads you in, or Beast Taming Dao tier 6 | Primordial eggs (pets that live in the Inner World); the first step of the Mandate Bloodline |
| The Pilgrim's Camp | Tide Edge | Story room left off the map | Grey footprints after the Herald's Breach, seen with Spirit Sense or the Wandering Eye fate | The Hollowing forced advance (a breaker that makes you dependent); the Pilgrim's token (Epilogue) |
| Tidewatch Tower's crown | Duskwall | Optional ledge above the flight ceiling | The tower's updraft column | The Spirit Avatar secret art (Inner Heaven 8) |
| Lu's pages 26–30 | 26 Banner Hollow · 27 Wreck Lanes (main road) · 28 Survivor's Ford (alternate road) · 29 Boatman's Study · 30 the Frayed Horizon | Pickups | — | The journal's last five pages (all 30 open the Epilogue scene) |

The ceiling breakers of S28 and where they are:

| Breaker | Where | Road | Exclusions and costs (S28) |
|---|---|---|---|
| Worldseed Fruit | Worldseed Grove | Both | One per character |
| Primordial Crucible Pill (supreme quality removes the ceiling) | Recipe in the Kiln vault or Lu's drawer; its ingredients drop from Inner Heaven 6 foes on both roads ("ceiling breakers as world drops") | Both | Useless once the Mandate Bloodline is taken |
| Mandate Bloodline (ignores the ceiling) | Begun in the Primordial Den, finished at the Sky Sovereign's Crown | Main, then shared | Makes the Crucible useless |
| Devouring Scripture | The Chapel crypt | Alternate | Instability and soul injuries |
| Hollowing forced advance | The Pilgrim's Camp | Shared | Dependency |

### Set pieces and bosses

| Region | Set pieces | Bosses |
|---|---|---|
| Dawnwall | **The Wall-Walk defence**: waves of Hollow Knights and drones at the wall; front missions repeat it (Inner Heaven 2) | — |
| Greywind March | **The Severing Line**: the first severing of a corrupted region, shown on a model of the Inner World | The Grey Standard-Bearer (field) |
| Relic Drift | **A Relic World run**: salvage against the time limit; each world's vault holds a relic for the Inner World | Relic Guardian elites |
| Refuge Isles | **Cleansing a village**: the Grey Refuge turns from a field into a town, and its survivors can visit your Inner World (Inner Heaven 5) | — |
| Lu's World | **The river quest line** begins at Boatman's Study (a Genesis requirement) | — |
| Beast Sovereign Reaches | **The Sky Sovereign's trial** (the Mandate Bloodline); **Primordial Beast transformation** at the Transformation Pool (a compatibility test; failure is survivable, S28); the **Wyrmheart Flame**, this act's Heavenly Flame, at the Crown | — |
| Duskwall | **The Herald's Breach**: the Herald's first assault; after it, the Tidegate opens | — |
| Tide Edge | **The Frayed Horizon**: the sight of Yan Heng's loom at the edge of everything; the Genesis requirements quest ends here with the Keeper of the Crossing's ferry | **Hollowed Primordial** (158): a Primordial Beast the Tide took |

### Realms and systems by stage

| Stage | Unlocks (unlock timeline, v1.4 row) | Where |
|---|---|---|
| Inner Heaven 1 | The Inner World, Heavenforce, Heaven Pills; Hollow Ward jades | Heavengate Landing, Inner Gate, Rampart Market |
| Inner Heaven 2 | Front missions; severing | Marshal's Hall; the Severing Line |
| Inner Heaven 3 | Relic Worlds | Salvage Moorings |
| Inner Heaven 4 | Inner World buildings | The Inner World |
| Inner Heaven 5 | Dao imprints; visitors (survivors on the River road, salvagers on the Front road) | The Inner World |
| Inner Heaven 6 | Ceiling breakers as world drops | Both roads (table above) |
| Inner Heaven 7 | The living world | The Inner World; Duskwall |
| Inner Heaven 8 | Spirit Avatar | Tidewatch Tower's crown |
| Inner Heaven 9 | Genesis requirements | The Frayed Horizon; Boatman's Study (the river quest line) |

Also in v1.4: Primordial pets living in the Inner World; Heavenforce with Heritage; one Heavenly Flame (the Wyrmheart
Flame); the legendary weapon chains complete; body tiers beyond Gold as data.

### Main story (chapters 29–34, outline)

| Chapter | Quests |
|---|---|
| 29 The Heavengate (HT → IH1) | The Inner World forming · Dawnwall (Marshal Lei Guang) · A World Inside (the Inner Gate) · Heaven Pills |
| 30 The Grey March (IH1 → IH3) | Front duty (the Wall-Walk) · The Severing Line · The Standard · Two Roads (Relic-Keeper Cheng Wu at the Moorings, or Refuge Elder Kang Ruyi at the Refuge) |
| 31 Two Roads (IH3 → IH6) | Main: The Drowned Glass, The Bells, The Lanternless, The Kiln (Relic Drift), then The Wyrmspine (Beastspeaker Du Ansu; the Primordial Den). Alternate: The Grey Refuge, The Chapel, then Lu's World (the Ferry Village, Boatman's Study). Both end at Duskwall with a ceiling breaker in reach |
| 32 Duskwall (IH6 → IH7) | The Last Wall (Tide-Watcher Guan Lie) · The Herald's Breach · A Living World |
| 33 The Sky Sovereign (IH7 → IH8) | The Plateau · The Elder Wyrms · The Sovereign's Trial (Mandate Bloodline, optional) · The Avatar (Tidewatch Tower) |
| 34 The Tide Edge (IH8 → IH9) | The Unravelling Shore · The Hollowed Primordial · The River Quest (Lu's World, reached by boat from Duskwall on the Front road) · The Frayed Horizon (Genesis requirements; the Keeper's ferry) |

---

## 5. The Epilogue · World Genesis (v1.5)

### Premise

With Inner Heaven 9, a living world, three Daos at Original Application including Space and Time, and the river quest
line done, the Keeper of the Crossing takes you aboard at Lu's World and rows you to the head of the **River**: the River
of Time and Space, of which the Jade River in every backdrop was always one reach. Yan Heng the Unwoven has been
unmaking worlds to weave one of his own; the Hollow Tide is his loom's loose thread. World Genesis is the power to walk
the River, restore, weave, seed and mend (S28).

### Laws, Qi, attunement, money

| | Value |
|---|---|
| Zone | `the_river`, no tier, Level 166 + Genesis Mastery ÷ 10 |
| Laws | Every Law on the River. A woven world holds up to four (S28) |
| Qi density | Riverhead 4.0; a memory room keeps the density of the room it remembers; the Unwoven Shore 3.0–4.0, thinner where the threads are loose; a woven world's density is set when it is woven (proposal: up to 1.0 + Genesis Mastery ÷ 100, at most 4.0) |
| Attunement | None |
| Currency | Worldseed shards pay for weaving; Heaven Pills stay money |
| Progress | Genesis Mastery and worlds woven or restored, not Qi points (S28, `realms.json`: World Genesis needs 0) |

### Regions and rooms (17, and the worlds you make)

Room prefixes: `rh`, `mr`, `us`. Woven worlds take ids from the world builder.

| # | Region | Road | Biome | Levels | Rooms | Foes |
|---|---|---|---|---|---|---|
| 1 | Riverhead (safe) | Hub | The headwater of the River among clouds, a landing, a ferry, a pavilion over the source | — | 3: Crossing Landing · Keeper's Ferry (interior) · Headwater Pavilion (insight; the River Flame, the Epilogue's Heavenly Flame; the Genesis Mastery board) | — |
| 2 | The Memory Reaches | Main | Past moments of every act, replayed on the River; each room is the place as it was | 166+ (echoes take the player's Level) | 10, two per act: Lotus Ferry, the Morning You Left · Cleansing Summit, the First Vision · Cloudgate Port, the First Sky · The Tomb King's Hall · Lanternfall Under the First Lantern · The Greyfall Breach · The Empty Throne · Shen Lian's Stand · Dawnwall, the First Siege · Lu's World Before the Fraying | Memory echoes of that act's foes and bosses |
| 3 | The Unwoven Shore | Shared | Where the world's threads have been pulled loose; grey loom-frames over nothing | 166+ | 4: Loose Threads · The Grey Loom (dungeon) · The Unmaking Hall (boss arena) · The Last Crossing (story) | Memory echoes, loom-threads; **Yan Heng, the Unwoven** |
| — | River landings | — | One landing added to an existing room in every zone (Lotus Ferry's dock, the Skydock, the Arrival Quay, the Frontier Quay, the Heavengate Landing) and one in each woven or restored world | — | 0 new rooms | — |
| — | Woven and restored worlds | Loom road | Made by the player: size, biomes, up to four Laws, a Qi density (S28); a restored Relic World becomes a safe zone | — | Generated; plain zone data loaded by the normal room loader | Tide incursions (woven-world defence) |

Room count: 3 + 10 + 4 = **17**.

### Routes and cross-links

| Road | What it is | Genesis Mastery from |
|---|---|---|
| Main: the Memory road | Walk the River through the memory rooms in act order. Each memory mends one thread | Memories walked |
| Alternate: the Loom road | Weave a first world, restore one Relic World, seed life in it, mend one Hollowed place (the Greyfall Breach closes) | Worlds woven, restored and seeded; places mended |

Both roads meet at **Loose Threads**, which opens at a Genesis Mastery threshold reachable from either road alone (the
number is set by the balance run). The ending asks for nothing more.

| Link | From → to | Kind | Opens |
|---|---|---|---|
| The Keeper's ferry | Lu's World (Boatman's Study) → Crossing Landing | Boat, one-way the first time | Genesis requirements met |
| River landings | Crossing Landing ↔ every zone's landing and every woven world | River portals, no fee | World Genesis |
| Memory doors | Headwater Pavilion → each memory room | Instanced | One per act, in order, on the Memory road |
| Loose Threads | Headwater Pavilion → Loose Threads | Sealed gate | The Genesis Mastery threshold |

### Travel

- **Arrival:** the Keeper of the Crossing's ferry.
- **Walking the River:** fast travel between every zone's landing and every woven world, and the way into the memory
  rooms (S28).
- **No flight** in the memory rooms (you walk as you did then) and on the Unwoven Shore where the threads are loose.

### Hidden maps

| Hidden map | Where | How it is found | What it holds |
|---|---|---|---|
| The First Crossing | A memory room of Lu's own first crossing | All 30 of Lu's journal pages (S19: the Epilogue scene) | Lu's story; a title |
| The Other Choice | Inside the Greyfall Breach and Shen Lian's Stand memories | The Time Dao at Original Application, at the memory's stele | The past choice (Kharn, Shen Lian) as it went the other way; nothing in the present changes |
| The Pilgrim's Memory | Inside the Greyfall Breach memory | Carry the Pilgrim's token from the Tide Edge | Who the Grey Pilgrim was |
| River of Time and Space | Headwater Pavilion | Reaching the Pavilion | The Codex entry locked since v0.4 |

### Set pieces and bosses

| Set piece | What happens |
|---|---|
| Walking the River | A memory replays; its foes are echoes; falling wakes you at the landing |
| The Weaving | The world builder (the one the Inner World uses) makes a new zone from the player's choices |
| The Restoring | An instanced Relic World becomes a safe zone with its own landing |
| Seeding life | A woven or restored world gains inhabitants |
| Mending the Hollowing | A Hollowed place anywhere is cleansed; the Greyfall Breach closes |
| Woven-world defence | Tide incursions into your worlds on the calendar; sect branch halls stand in woven worlds |
| The Unmaking Hall | **Yan Heng, the Unwoven** |
| The Last Crossing | The ending with the Keeper of the Crossing |

---

## 6. What this plan asks of each build

| Build | From this plan |
|---|---|
| v1.3 | `tools/data/frontier.py`; the `star_frontier` zone row with its four jades; a room-level `laws` field read by the Z step; the Frontier Run voyage and chart; eight teleport stones; the new hazards; Grapple points; 64 rooms passing the room lint; `beast_rank` on the Frontier's beasts for P8b; the Rite Chamber built and sealed as `planned` |
| v1.4 | `tools/data/heavens.py`; the `outer_heavens` zone row; the Heavengate; relic charts and instanced Relic Worlds; the Inner World on the world builder; seven teleport stones; the ceiling breakers placed on both roads; region gates by chapter and Hollow Ward, never by rank; 57 rooms |
| v1.5 | `tools/data/river.py`; the River as a zone; landings added to five existing rooms; memory rooms as instances; weaving and restoring through the same world builder; 17 rooms |

Numbers on this page (attunement per region, jade values, densities, the Genesis Mastery threshold) are tuning values.
The balance simulator confirms them as it does for the built acts.
