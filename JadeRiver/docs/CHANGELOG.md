# Changelog

## 1.1 — The Azure Expanse (Act II)

Built in phases (docs/act2_design.md). All five phases (chapters 11 to 16) are playable end to end, from
the Ascension Gate to the Starsea Launch.

### V3c · Talisman craft and Shattered Relics (S47)
- **Talisman craft** (Qi Kindling 6). Old Scribe Bai in Artisan Row teaches it through the guided quest
  *Ink and Paper*. He opens the Talismans page, a tab of the crafting table.
- **Tracing.**
  - Each talisman has a stroke path. Trace it in one motion on the canvas.
  - Staying near the path and keeping an unhurried pace (0.6 to 5 s) set the quality, Flawed to Perfect.
  - Straying too far breaks the stroke and spoils one sheet of paper; the ink is kept.
  - Inks and spirit paper are made without tracing.
- **Talismans.** They work at the talisman's own grade and quality, never from the user's stats.
  - Attack: Flame (180% fire in a burst) and Thunder (240% thunder, with Shock).
  - Defence: Iron Wall, a shield of 20% max HP for 6 s.
  - Movement: Wind Step, one free dodge within 60 s, even on cooldown.
  - Concealment: Veil, which hides you from foes for 10 s.
  - Sealing: Binding, which roots the nearest foe. Bosses are Steadfast.
  - The Revival and Lightning Rod talismans move here from Formations.
- **Materials.**
  - Talisman paper and spirit paper (paper and Mist Lotus).
  - Cinnabar, sold at Stoneford's general store.
  - Beast-blood ink, from hound fangs and rat tails.
- **Data.** `talismans.json` holds base power by grade, quality multipliers, the stroke paths and the trace
  tolerances. Events: `talisman_crafted` (spoiled or not) and `talisman_used`.
- **Shattered Relics.**
  - The Drowned Abbot's first defeat leaves the Shattered Moon Blade.
  - An Expert smith at a forge restores it into the Moonlit Blade, a Heaven relic whose spirit still sleeps.
    It costs 6 Cloudsteel, 6 Refining Essence and 3000 taels.
  - The Restore button is on the shard's item details. Event: `relic_restored`.
- **Tests.**
  - `talisman_suite`: spoiled strokes, stroke quality, grade-fixed damage whatever your Qi attack, Iron Wall,
    Wind Step on cooldown, Binding, and the relic's gates.
  - The valley run writes the first Flame Talisman at Qi Kindling 6.

### V3c · Natal treasure, wardrobe, blood-drop bind and rogue cultivators (S47)
- **Natal treasure** (Heart Tempering 1).
  - Flag one weapon as Natal, in the forge's Natal mode.
  - It grows from kills and technique uses with it in hand, and from ore fed at the forge (20 XP a grade step), to
    natal level 10, +2% stats a level.
  - Its item level follows yours up to the top of the grade band above its own.
  - It breaks only to a boss's telegraphed shatter blow (the Tomb King's glaive sweep, the Hollow Behemoth's
    stampede) or to overcharging, a 5% chance a technique when your Spirit is below its control demand
    (10 + 5 a level).
  - Broken, its stats go dark and a meridian injury follows (a soul injury from Spirit Awakening), until a
    re-forge. A re-forge mends it, or at its cap carries it into the next band with its growth.
  - Item details show its level and item level. Events: `natal_grew` and `natal_broken`.
- **Wardrobe** (Heart Tempering 1): every look you wear joins the account's wardrobe. The Character page's
  Wardrobe tab lets any of them stand in for a slot's own look; stats do not change.
- **Blood-drop bind**: the first time a Plain to Heaven piece is worn, a drop of blood falls on it (`item_blooded`,
  cosmetic).
- **Rogue cultivators**: elites whose visible weapon or treasure is a guaranteed drop.
  - A Rogue Cultivator in the Drowned Grotto carries the Serpent-Tongue Jian.
  - A Rogue Mirror Adept on the Misty Slopes carries a Bright Mirror.
  - Both carry a Sealed Storage Pouch, which Appraisal opens into something from its own table.
- `natal_wardrobe_suite`: growth, the item-level cap, breaking only to shatter, re-forging, the wardrobe,
  blood-drop, rogue drops and the pouch.

### V3b · Flying sword, Sword Intent, dual loadout and self-detonation (S47)
- **Sword Release.** The Sword Dao's third tier teaches it; it goes on the skill arc.
  - The jian leaves your hand for 8 s, or until you use the technique again to call it back.
  - It homes on the nearest foe within 420, 1.5 strikes a second at 60% of the jian's attack. Each strike is a
    flying-sword projectile that stops at walls.
  - Meanwhile your hands fight with Qi palms: the fist combo at ×0.8.
  - While it is out, the sword hangs point-up over your shoulder between strikes.
  - It returns when the time runs out, when you are wounded, or when you lose the jian.
  - Events: `sword_released` and `sword_returned`.
- **Sword Intent.**
  - Consecutive jian hits (combo, techniques and the flying sword) stack up to 10, each +1% penetration.
  - At 10, a weaker foe may falter (a 10% Fear chance).
  - It fades 3 s after the last jian hit, and ten pips along the player panel's foot show it.
  - Event: `sword_intent_changed`.
- **Dual loadout** (Heart Tempering 1).
  - A second weapon waits in the spare slot: "Set as spare" in the bag.
  - The Swap button (R) trades it for the weapon in hand.
  - Each weapon keeps its own technique bar, and a swap never touches a Dao tier.
  - Event: `loadout_swapped`.
- **Self-detonation.** A spare artifact (an unworn piece of equipment, or a treasure) bursts around you for
  1.5 + 0.75 × grade × Qi attack within 180. It is destroyed, which is the one thing the game ever destroys, and
  only after you confirm. Event: `artifact_detonated`.
- `sword_loadout_suite`: the Dao teaches the art; the sword strikes, the palms stay active and the sword returns;
  Intent stacks and fades; the swap keeps each bar; detonation asks first.

### V3a · Gear upkeep at the forge (S47)
- **Enhancement pity.**
  - An enhancement from +5 upward can fail, and it never breaks the piece or takes a level.
  - Each failure adds 5% to the next try on that piece. The piece keeps its pity and shows it in its details;
    a success clears it.
  - The roll uses the affix stream.
- **Refining Essence** (a new material, from Salvage) steadies a try: +2.5% each, up to four.
- **Salvage** breaks any number of pieces into their grade's metal and Refining Essence (`salvage.json`:
  Plain copper; Common Riverstone and 1 essence; Earth Jadeiron and 3; Heaven Cloudsteel and 6; Mystic ore and 10;
  Spirit and Sage in their zone metals). Worn, bound and locked pieces are never salvaged. The intent is
  `salvage {items[]}`, and it emits `items_salvaged`.
- **Inherit** moves a piece's enhancement, less two levels, onto another piece for the same slot, for 2 Spirit
  Stones a level moved (`enhancement_inherited`).
- **Reroll and affix lock.**
  - A reroll rolls a piece's affixes again, and you choose to keep the old roll or take the new one.
  - Locking one affix keeps it through the reroll, and the reroll then costs double.
- **Forge modes** on the Crafts page: Recipes, Enhance, Inherit, Salvage and Reroll. Each shows the chance, pity,
  costs and returns before you commit.
- Enhancement uses each grade's own metal from `salvage.json`, so Spirit and Sage gear now eat Stormsteel and
  Sunglass instead of copper.
- `forge_upkeep_suite`: pity builds and resets, Inherit moves N − 2 in one slot, Salvage skips locked pieces, and
  a locked affix survives a reroll that costs double.

### V2d · The room verticality catalogue, room lint and Paths Above (S43 rules 14–15)
- **Every valley room is built to its v2 catalogue row** (tools/data/catalogue.py):
  - **Lotus Ferry:**
    - lofts sealed until The Runaway Kite;
    - Aunt Ping's lost ladle (a new quest) on a roof;
    - Home Lane's crates and well;
    - the roof chain and the watchtower;
    - the docks' boat deck and mast lookout;
    - stilt decks and drifting rafts in the Reed Shallows.
  - **Willow Path and Stoneford:**
    - willow branches and a later pine top;
    - Market Street's awnings and bell tower;
    - Artisan Row's scaffolds and chimney (the Tinkerer's Gear, a new item);
    - Stoneford Gate's walltop;
    - the Entry Trials rebuilt: Jade climbs roofs over moving planks, Cloud climbs ropes past a crumbling ledge.
  - **The sects:**
    - the Sword Court's plum-blossom poles and a Wall-Step pillar pair;
    - Elder Sung's rope bridge between peaks;
    - library floors at 120 and 240, sealed by rank.
  - **Fields and dungeons:**
    - scaffolds and a crane lift at the quarry;
    - a cracked slab in the Lower Pit that a Plunge breaks;
    - rafts, a moored chest and a lily-pad bounce in the Grey Pools;
    - sprint gaps and a Wall-Step pillar on the Sunken Causeway;
    - bamboo tiers and a bent-bamboo bounce;
    - rope bridges on Caravan Road and at the Gorge Mouth;
    - the Boss Den's wine shelves and the Abbot's bell ledges;
    - a Wall-Step shaft behind the falls.
- **Verticality pass for every other room** (tools/data/verticality.py):
  - standard heights and landings;
  - a raised route across 40% of wide rooms, with rope bridges where roofs are too far apart;
  - a second tier where a room has only one;
  - later ledges for a named art;
  - two ways up each tier;
  - loot lifted onto tiers.
- **Room lint and reach contract** (tools/data/room_lint.py) runs first in `tools/run_tests.sh`. All 122 rooms pass.
- **Paths Above:**
  - Every later ledge is a row in `paths_above.json` and in a new Codex tab.
  - Standing on one records it (`path_above_found`, with a toast).
  - The World map shows a faint wind glyph where your arts now open a ledge you have not stood on.
- **New kit art:**
  - rope bridges, a walltop, chimneys and stone pillars;
  - bamboo slat platforms, scaffolds and stilt decks, awnings, a causeway slab and a cracked slab;
  - log, rubble, lily-pad and bent-bamboo blocks.
- Monsters that live on tiers now also start on branches, canopies, stilts, scaffolds and causeways.

### V2c · Camera, heights in a fight, monster navigation and allies (S43 rules 10–13)
- **Camera.**
  - Rooms may set camera bounds and look-ahead.
  - The camera leads by a quarter of the velocity and follows the surface underfoot instead of the jump arc,
    settling in 0.4 s after a landing.
  - It follows falls of more than a tier and looks down 60 near a high edge.
  - The vertical range opens to 180 so high tiers stay in view.
- **Heights in a fight.**
  - Blows reach −30 to +60 of the attacker's height, and Qi and Soul techniques −10 to +80: from the ground
    you cannot hit someone on an 88 roof, only mid-jump.
  - Flyers hover at about 48 so grounded fighters can still reach them.
  - Every shot stops at blocks and building walls and passes platform decks.
- **Monsters move through vertical rooms.**
  - Each species has `movement {jump, climb, fly, drop}`. Each room builds a deterministic navigation graph
    of walk, jump, drop and climb edges, and melee monsters hop along it after their target.
  - A monster that cannot reach you waits beneath you. After 2 s it takes half damage from you, and after 6 s
    it goes home, healing 10 % a second.
  - Flyers sink toward the height they hunt at.
  - Archers, imps, frogs, toads and vultures start on raised tiers in five rooms.
- **Allies** walk on surfaces and follow along the graph. More than 480 away, or unable to reach you for 2 s,
  they blink to you in a puff of mist.
- **Landing ring** under an airborne player within 200 of the surface below. The minimap shows blocks,
  climbables and movers. Enemy shadows fall on the surface under them.
- **Tests:**
  - the melee and Qi bands, and shots against blocks and decks;
  - graph edges by species, a graph identical on two builds, and chained paths;
  - a bandit chasing up a ledge, a tortoise hitting the out-of-reach rule, and allies blinking after 2 s and
    past 480.

### V2b · Movement arts, volumes and movers (S43)
- **Four new movement arts**, each taught by a guided quest when the quest is accepted:
  - **Plunge** (*Outer Trial*, Bone Forging 4): Down + Attack in the air drops at 900. The landing strikes
    within 60 for 120 % damage and a 0.5 s stun, breaks jars and cracked floors, and has a 4 s cooldown.
  - **Falling Leaf Glide** (*Leaf on the Wind*, Falls Pool, Qi Kindling 3): hold Jump while falling. The fall
    is capped at 120 a second and drift is 10 % faster, for 2 QI a second. The Falls Pool gains a vine, a
    200 ledge and the waterfall's updraft.
  - **Swallow Dart** (*Swallow Dart*, the library's first floor, Qi Kindling 7): tap Evade in the air to dart
    140 while holding your height for 0.25 s, once per airtime, on the dodge's cooldown.
  - **Water Skimming** (the hermit's side quest *Skipping Stones*, Qi Unfurling 8): sprint across deep water.
    The pond under the hermit's stilts has a rock with a Mist Lotus on it and a raft that poles across.
- **Flight by holding Jump.** Hold Jump as you start to fall to take off. Flight replaces the glide where it
  is allowed and QI is above 10 %. In the air, hold Jump to rise, hold Evade to descend, and tap Evade to
  dash. Flight is refused indoors, on sect grounds, in dungeons and in `no_flight` volumes. The third-press
  take-off is gone.
- **Volumes** in room data:
  - shallow water: ×0.7, no sprint or dodge;
  - deep water: sink in 1 s and return to the last safe spot, or swim 30 s with Breath Control;
  - current, updraft, wind (a 4 s pulse, stronger at edges), bounce (700) and crumble (0.8 s, back after 5 s);
  - rising water keyed to events, hazard and no_flight.

  They are placed in the Flooded Gate (current), Falls Pool and Cliff Faces (updrafts), Windswept Ridge
  (wind), the Fairground (a bounce drum) and the Mudwater Tunnels (rotten boards). In the Serpent's
  Shallows the Riverbed Serpent floods the arena to 30 for 14 s at half health.
- **Movers.** A surface or block follows a path as a pure function of the room clock, in loop, pingpong or
  trigger mode, and carries its riders. The hermit's raft is the first.
- **Controls and feedback:**
  - techniques and attacks wait while climbing;
  - the climb-speed stat now counts;
  - a fall fades the screen briefly;
  - no safe spot is recorded in deep water, on a mover or on a crumbling floor.
- **Learning an art** shows a toast with its name and a one-line how-to. Each of the five arts has its own
  icon.
- **Data.** `data/movement.json` holds every traversal number, and data validation checks the solver
  against it. Every movement art in `secret_arts.json` names its `movement_art`, how-to and quest. The new
  events are `mover_boarded`, `volume_entered` and `volume_left`.
- **Tests.** The solver is tested at each art's numbers:
  - the glide lasts 1.5 s and covers about 300;
  - the dart covers 140 with no height lost;
  - a Plunge breaks a cracked floor.

  Every volume behaves as its table row says, movers replay identically, and rising water follows its
  event. Game-level tests cover the Plunge blow and stun, glide QI, the air dash and flight on sect grounds.
  The valley run plays the four new quests.

### V2a · Traversal engine (S43)
- **Surfaces have sides.** Each walk surface records which of its four edges are open. A platform is closed
  at the back (north) and open on the other three; the ground and ramps are closed all round. Walking off an
  open edge starts a fall; a closed edge stops you.
- **Blocks** (crates, walls, rocks, carts) are solid boxes: you walk around them, or jump onto their tops at
  40, 60, 80 or 110. A block is an obstacle and a small platform at once, open on every side.
- **Jump feel.** Coyote time 0.10 s after walking off an edge, and a 0.12 s jump buffer that fires on landing.
- **Cloud Ladder Step** (double jump, impulse 430, about 202 high from the ground) is learned in *Cloud Ladder*,
  a Qi Unfurling 6 guided quest from the librarians. It no longer comes free with the first realm.
- **Wall-Step** is learned in *Between Two Walls*, a Heart Tempering 4 guided quest at the Echo Cliffs. Push
  into a wall and jump to kick off it, up to three kicks per airtime; each kick springs away from the wall. The
  Echo Cliffs now have a shaft of two rock walls 100 apart that climbs to the 300 ledge.
- **Drop-through.** Down + Jump on a platform drops through it.
- **Mantle.** Falling past a ledge lip within 24 of your feet pulls you up onto it.
- **Climbables.** Ladders, ropes, vines and chains are their own objects, not ramps. Hold toward one for 0.3 s
  (or use the context button) to climb; jumping lets go. The Lotus Ferry hall ladder is the first.
- **Air attacks.** A basic attack in the air is a single stronger strike (×1.1) and slows drift less.
- **Falls.** Falling out of a room returns you to the last safe spot (0.3 s standing, at least 24 from an open
  edge) and costs 5 % of max HP, except in towns, the prologue and the Lotus Ferry.
- **Context button** (1165, 500) appears in a fight when a ladder or door is in reach, since Attack takes
  the main button then.
- **Doors** need Up held 0.3 s, so a passing jump no longer walks you through them.
- **Events:** `jumped`, `landed` (with fall height), `wall_kicked`, `art_used`, `climb_started`,
  `climb_finished` and `fell_out`.
- **Standard heights** 100 (one jump), 176 (double jump, two storeys) and 300 (flight only). The room
  catalogue uses them; docs/movement.md has the reach table.
- **Tests.** A traversal suite covers edges, blocks, coyote time, the buffer, the double jump, drop-through,
  mantle, climbing, Wall-Step and falls, and checks that a room's blocks and climbables reach its geometry. The
  valley run now plays *Cloud Ladder*, *A Treasure in Hand* and *Between Two Walls*.

### V1b · Pill rules follow Build Prompt v2 (S44)
- **Lifetime resistance** counts every 5 doses of a family as 1 (`pill_resistance {family: {count, doses}}`); a
  pill works at 1 ÷ (1 + 0.25 × count). Each major breakthrough drops every count by 1 and then halves it. A
  normal ten pills a realm now keeps pills near two-thirds strength, where the gap report's rule left them at 29 %.
- **Families come from data** (`family` on each pill, raw herb and core):
  - accumulation (Qi Gathering; herbs and cores that add Qi);
  - body (Bone Strengthening);
  - insight (Clear Mind);
  - soul (Soul Soothing);
  - support (Foundation Guard, Cleansing).

  Healing, restoration, antidote, purging and conversion pills are exempt. Pill details show what resistance
  leaves of a pill, or that a Pill Grain ignores it.
- **Foundation.** The share is pill QP ÷ total QP since the last major breakthrough, and resets at each major
  breakthrough. Beast cores count as pill QP. *Settle foundation* lowers the share by 5 points an hour and burns
  off 5 residue an hour.
- **Support pills.** After two failed attempts at the same breakthrough (`support_failures`), support pills stop
  lowering its risk.
- **Pill marks** by quality: Fine 1–2, Superior 2–4, Perfect 4–6, Grain 6–7, Halo 8, Soul 9.
- **Pill Halo** grows +1 % a day, to +20 %, while in a storage chest in a room of Qi density 2 or more. It no
  longer grows in the bag during seclusion.
- **Pill Soul** always carries its recipe's own `soul_effect`.
- **Events and saves.**
  - Events: `pill_resistance_changed` and `foundation_changed` are emitted.
  - Saves move to version 5: version 4 resistance, foundation and support-failure data migrate on load.
- **Tests.** `tools/run_tests.sh` now fails a suite that prints a script error. A runtime error used to abort a
  suite part-way and skip its remaining checks silently.

### V1a · Treasures, talismans and throwables follow Build Prompt v2 (S47, Part 8)
Build Prompt v2 folds the gap report into the build prompt and wins where they disagree (docs/v2_audit.md).
G2a's treasures now match its Part 8.
- **Treasures and sources.** Each treasure has a flat QI cost and, from Spirit Awakening 1, a Soul cost of a
  third of that. Their definitions are in `treasures.json`.

  | Treasure | Effect | Cost | Source |
  |---|---|---|---|
  | Practice Bell | stun 0.5 s, radius 100 | 25 s · 15 QI | *A Treasure in Hand*, the new Heart Tempering 1 guided quest from Elder Hu or Elder Sung; it opens Treasure slot 1 |
  | Bronze Bell | stun 1 s + Qi Seal 3 s, radius 150 | 20 s · 30 QI | Drowned Abbot, first clear |
  | Little Pagoda | holds one foe 4 s, an elite first; bosses immune | 30 s · 40 QI | Gu's Warehouse vault |
  | Bright Mirror | returns projectiles 2 s | 18 s · 25 QI | forged from Jadeiron ×6 and pearls ×2 (blueprint at Heart Tempering 1) |
  | Mountain Seal | 250 % Qi Attack, radius 120 | 25 s · 45 QI | Stone Guardian, rare drop |
  | Taming Cauldron | takes a beast below 20 % HP as its fixed materials, no loot roll | 40 s · 30 QI | Hermit Yao's Beast Hall |
  | Wisp Banner | three wisps fight for 10 s | 45 s · 50 QI | Bai Ling's quest line |
  | Sealing Gourd | drinks projectiles for 3 s | 20 s · 30 QI | Old Ma, after Spirit Awakening 1 |

- **Elder Hu's Talisman** (was the Heaven Splitting Talisman). It sits in a Treasure button and holds three
  charges of the Heaven-Splitting Palm (600 % Qi Attack), with no cooldown. Elder Hu gives it when you accept
  the Heart Trial. The button shows the charges left.
- **Throwables are forged:**
  - Iron Needles ×20 from Riverstone and a beetle shell;
  - Flying Knives ×10 from Jadeiron;
  - Thunderclap Pellets ×3 from ore dust, Ember Pepper and a lantern wick.

  The Lightning-Rod Talisman item exists, ready for tribulation.
- **Vessels** set the flight sprite and QI cost only. The speed changes and the Sealing Gourd's heal were
  inventions, and are gone.
- **HUD.** Treasure 1 is at (887, 470) and Treasure 2 at (799, 470), with the Z and X keys. The Pet button moved
  to (965, 560), clear of skill slot 2.
- **Events** use v2's names:
  - `treasure_used` for deployed treasures; the natural-treasure event is now `natural_treasure_used`;
  - `merit_changed`, `sin_changed`, `debt_recorded` and `debt_called`.
  - Effects `add_merit`, `add_sin`, `record_debt` and `add_residue`.
  - The event contract now lists every S43–S49 event the build emits.
- The Wisp Banner is described as formation light, not bound wisps, to stay clear of soul banners.

### G2a · Treasures, throwables, a talisman treasure and flight vessels (gap report priorities 4–5)
- **Two Treasure buttons** left of Guard (R and T on a keyboard). The first opens at Heart Tempering 1
  with the **Stilling Bell** (quest *Lines in the Sand*), the second at Spirit Awakening 1. Set a treasure
  from the bag. Each treasure is one action with a Qi cost and a cooldown, shown as a sweep on the button:
  - **Stilling Bell:** stuns foes within 220 for 1.5 s and seals their Qi for 4 s. Bosses only lose their Qi.
  - **Nine-Storey Pagoda:** a 4 s prison over the nearest foe, never a boss.
  - **Returning Mirror:** for 2 s every missile that reaches you flies back at its thrower.
  - **Mountain Seal:** 250 % attack to everything within 170, with knockback.
  - **Beast-Taking Cauldron:** takes a beast worn below 20 % HP whole, for twice its materials.
  - **Wisp Banner:** three wisps strike the nearest foes each second for 10 s.
  - **Sealing Gourd:** drinks every missile within reach for 3 s, each mending 1 % HP.

  The Mission Halls, Old Pan and the port peddler sell them. The Hollow Behemoth and the Gate Guardian
  drop the Seal and the Banner on their first defeat.
- **Throwables.** Throwing needles (three at once), flying knives (pierce one) and thunderclap pellets (burst
  and knockback) share a 1.2 s cooldown and can sit in quick-use. Needles and knives can be made at the forge.
- **Talisman treasure.** Elder Hu's gift, the **Heaven Splitting Talisman**, holds three charges of a 12,000
  damage cut, at its own power, not yours. The bag shows the charges left.
- **Flight vessels** ride in the key pouch; choose one in the bag:
  - **Flying Sword:** −20 % Qi, +25 % speed (the reward for *Riding the Wind*);
  - **Cloud Puff:** −35 % Qi, −5 % speed (a Mission Hall);
  - **Jade Gourd:** −15 % Qi, +10 % speed (the other Mission Hall);
  - **Maple Leaf:** −25 % Qi (the hermit's).

  Each is drawn under the rider in flight.
- **Fix: shots now strike short creatures.** Arrows, ranged Qi techniques and throwables fly at chest height, and
  their hit band stopped 36 units above the ground, so they passed over 30 of the 75 monsters (crabs, rats,
  frogs, foxes and every creature under 38 tall). The band now reaches the ground; a shot fired from the air
  still passes over them.
- A new temple-bell sound effect. The first treasure carried goes straight into Treasure 1. 36 new rules checks
  drive every treasure, throwable, the talisman and the vessels through the real authorities, plus the arrow
  regression. `--vessel=<id>` with `--fly` previews a vessel.

### G1 · What pills cost, heart demons, karma, fire and furnace (gap report priorities 1–3)
- **Lifetime pill resistance.** Each dose of a pill family (Qi, body, soul or insight) weakens the next:
  1 / (1 + 0.25 × doses). A major breakthrough forgets one dose. A Pill Grain slips past resistance. A support
  pill that has failed the same breakthrough twice stops lowering its risk.
- **Foundation.** Every great realm tracks how much of its Qi came from pills, raw herbs and cores.
  - Above 30 % the foundation is hollow: the next major breakthrough counts it as an unmet soft requirement,
    and a failure is always *Weak foundation*.
  - The new seclusion focus **Settle foundation** makes pill-given Qi your own and burns off residue.
- **Residue.** 5 % of all toxicity stays behind. Each 10 residue costs 1 % accumulation, up to −10 %.
  Purging Pills don't touch it. A **flawless Heaven's Cleansing** (not hit once) washes it all away.
- **Heart-demon meter (0–100).** It is fed by:
  - a changed method (+10);
  - a pill-forced breakthrough with two or more supports (+5);
  - a defeat (+3);
  - sin.

  Each 25 is a risk step at every major breakthrough and one more crimson **Heart Demon**, wearing your face,
  at the Trial of Reflections. Meditation wears it down. Myriad-Year Calm Incense now really clears 40.
- **Karma ledger.**
  - Merit comes from the Hollow Night rescues, resealing the Tomb, freeing Gu, burning the Black Ledger,
    and ten helping quests. 100 merit eases one great breakthrough in each realm.
  - Sin comes from leaving Gu in chains, sending the ledger pages home, and every purchase in Broker Mu's
    back room. Sin feeds the heart demon.
  - Named debts come back as letters. Freed, Gu repays you two days later; the Gu family remembers otherwise.
- **Fire and furnace** (the S15 "rare fire or special furnace", now defined).
  - Fires:
    - Charcoal takes a pill as far as Perfect.
    - Earth Fire, at a vent in Whitewater Gorge and on the Scorpion Flats, reaches Pill Grain.
    - Beast Fire, burning one beast core a batch, also reaches Pill Grain.
    - Heavenly Flames, absorbed for good, reach Halo and Soul. They are the Cold Lamp (Drowned Abbot),
      the Sunscar Throne Ember (Tomb King) and the Comet Tail (Captain Rao), each a Codex collectable.
  - Each fire widens the strike band. The Crafts page has a fire selector.
  - Furnaces are items that set the batch (Bronze 3, Earth-Vein 5, Cloud-Pattern 8, Mystic Tripod 10),
    with band, filter and yield-chance stats. Each is cast around the last at the forge.
    **Alchemist Fen's Nine-Dragon Cauldron** is a named furnace that reaches Soul on any fire.
- **Pill marks.** Every batch rolls 0–9 gold lines by quality, each +2 % effect, drawn on the slot. When a Halo or
  Soul pill forms, a coloured pill cloud boils up and nearby NPCs cry out.
- **Undefined rules settled.**
  - Pills never decay; the Codex says so.
  - Auto-refine teaches 25 % of the XP refining by hand does.
  - Herbs can be eaten raw in need (a third of a pill, twice the toxicity), and beast cores can be absorbed
    for Qi.
- The Cultivation page has a new **Heart** tab: the meter with its steps, merit, sin and debts, the foundation
  share against the hollow line, residue, and each pill family's resistance.
- 38 new rules checks drive every G1 rule through the real authorities.

### Text and button quality pass
- **Type.** Words and page figures are now set in Cormorant Garamond, as the style guide asks: semi-bold for
  text, bold for headers, with lining figures so "Lv 0" no longer reads as "Lv o". Previously every label was
  in the pixel face, drawn aliased at the phone's non-integer scale, which made glyph pixels uneven. Numbers
  over the world (damage, bar values) keep Pixelify Sans, now anti-aliased.
  - `JadeRiverSymbols.ttf` supplies ✓ ↻ ✦ ★, which both faces lack. It is a renamed DejaVu Sans subset,
    licence included.
  - World nameplates sit on a soft ink plate instead of a heavy outline.
- **HD UI kit** (`tools/ui/build_ui_hd.py`). Every frame, button, tab, slot, plaque, pill, toast, tooltip, bar
  and the dialogue paper is rendered as anti-aliased vector art at 3 texels per screen pixel:
  - gradient jade enamel and bevelled gold trim;
  - filigree corners with jade gems;
  - a paper dialogue box with lacquer seals.
  It is drawn through `HdStyleBox`, a nine-slice scaled by ⅓ with mipmapped linear filtering, so it is crisp
  from 1280×720 to 4K. The build checks that no ornament leaves its corner, since a leaking ornament would
  smear when stretched.
- **HUD buttons** are anti-aliased enamel discs with a gold bezel, a gloss arc and a soft gold halo when active.
  Empty technique slots show a faint cloud seal.
- The minimap title fits its header. The dialogue plaque leaves room for the speaker's name. The creator's
  arrows are proper ◀ ▶ buttons.

### Gap report audit (docs/gap_audit.md)
- Every proposal in the Xianxia Systems Gap Report is checked against the build: 2 present, 38 partial,
  71 missing. The game breaks none of the report's "stay out" rules.
- The missing systems are planned in seven phases (G1–G7) that follow the report's priority table.

### World movement pass (docs/movement.md)
- **Something to climb in every room.** An audit found 79 of 121 rooms flat. Now 7 of 122 are, all by design
  (insight rooms, the first hut, the home boat, story trials).
  - Fields, paths and dungeons get a one-jump ledge (110) and a double-jump ledge (220) with a chest on it.
  - Outdoor rooms from level 37 get a cloud bank at 320 that only fliers reach.
  - Towns get timber decks and halls get lofts.
  - Plum-blossom poles stand in the home sect's yard, and the elders' peaks and cave abodes get rock shelves.
- **Standable props.** Crates, barrels, tables, low walls, carts, boulders, sarcophagi and 9 more props in
  the walk strip are now solid blocks with tops, so a jump lands on them.
- **Secret arts that move you.** They were named in the design but never granted. Now:
  - **Wall-Step** (Heart Tempering 4): kick off a wall once in the air.
  - **Wind Blink** (Spirit Awakening 5): an air dodge that blinks 120 units, with a 10 s cooldown.
  - **Breath Control** (Qi Unfurling 3): opens the flooded shaft below the Scripture Well into the new
    **Drowned Grotto** (deep water, air pockets, drowned acolytes, a ledge chest).
  - **Appraisal Eye** (Qi Kindling 6): appraise without the tool.
  - **Lotus Heart Breathing** now does what it says: it heals 10% over 5 s below 30% HP, once a minute.
- New rules tests drive the real solver: one jump lands on 110 and not on 220, a double jump reaches 220,
  the cloud is out of double-jump reach, a crate takes a landing, and Wall-Step works once and only beside a wall.
- The Collection page no longer stalls its first frame (160–220 ms). Creature sheets load within a 12 ms budget
  per frame, and each sheet's drawn bounds are baked into `creature_art.json`.

### Phase E · the Starsea
- **The Shipwrights' Yard** at the west end of the Cloudgate Skydock: Navigator Sun's chart table, Shipwright
  Lao's slipway, an armillary sphere and the first Starsea dock.
- **Star charts and vessels (S16, Sage 3).** Two new crafts on the Crafts page, shown from Sage 3. Sighting
  stones on high places (the Yard, Rimefrost Summit, the Presence Terrace, the Riven Peak) give one star reading
  every ten minutes. Readings and sky ink make a route's chart (40 XP a route). Vessels are built on the slipway: the Cloud Skiff
  (smithing Adept) and the Storm Sloop (smithing and formations Adept, comet iron, half again as fast).
- **Starsea voyages (S18).** At a dock, a vessel and the route's chart set sail into an instanced crossing on
  the vessel's deck. The crossing lasts as long as the vessel takes: pirates board, wind kites dive, and the
  **star wind** strips Qi from anyone whose Spirit cannot hold it in (Starsea survival). The crossing ends in port
  at the far end. Falling overboard abandons it.
- **The Skyport Wreck** (Lv 76–81, Storm Ward 56–60), reached only by sailing: the Broken Pier, the Pirate
  Deck, the Riven Peak and the Starsea Launch (rest, teleport stone), with a wrecked-sky-port backdrop, an open
  Starsea backdrop for the crossing, and a new synthesized Starsea theme.
- Five new foes drawn with the avatar engine: the **Starsea Pirate**, the **Rogue Nine Peaks Disciple**,
  **Comet Captain Rao** and the Trial Hall's **Presences** (tinted phantoms, and the Ninth Presence).
- **Chapter 15, Pirates of the Starsea**:
  - Gu's Ledger: a page of the valley's secrets turns up at the auction.
  - The Skyport Wreck: chart, build, sail, take back the pages, and free Elder Gu or leave him.
  - Sect War: at Sage Sovereign 2, the defence of the Alliance Gate, with waves of pirates and deserters and then the captain. Burn the Black Ledger or send each page home. Afterwards the Alliance war gong calls a new battle every 20 hours, for Spirit Stones, comet iron and storm shards.
- **Chapter 16, The Presence Trial**:
  - Lu's Last Page, on the Riven Peak.
  - The Presence Trial: at Sage Sovereign 3, ninety seconds beneath the eight seats of the Trial Hall. Their Presence presses down, answered by Will; phantoms attack; the Ninth Presence arrives half-way. Passing it holds the key to Will Manifest, which the Expanse's ceiling still locks.
  - Stars Beyond: chart the Lantern Run, and the Launch's ring lights toward the Lantern Star Field (Act III).
- Act II systems from the v1.1 row:
  - **Elder's token** at Sage Sovereign 1: the training sect's token upgrades, the Elder rank follows, and home is a free teleport.
  - **Expanse Outpost**, a sect building from sect level 8: +1 Storm Ward per level for every member, and expeditions to three Expanse regions.
  - **Paired cultivation** from Sage 1: +15% accumulation while a companion sits with you.
  - **Rare Daos from teachers:**
    - Blood (Matriarch Tie);
    - Life and Death (Bone-Reader Xiu);
    - Emotion (Hermit Shuang).
    - Each has four tiers of stat bonuses and grows only after its teacher opens it.
  - The Expanse's own Laws (Fire, Metal, Thunder, Soul) now deepen past their valley caps there.
- Six side stories (The Deserters, Iron from a Comet, Clear Skies over the Peak and the three Dao lessons), three
  guided quests, five NPCs, six codex entries, seven titles and three achievements.
- Fixes: a tinted avatar enemy (a drowned acolyte, a phantom) kept its hit-flash white instead of its colour.
- Tests: two new valley_run sections (ae5, ae6) sail, build, fight the sect war and sit the Presence Trial through
  intents; 18 new rules checks cover docks, charts, vessels, the star wind, the outpost, rare Daos, zone caps and
  the Elder's token; data validation follows Starsea routes when it checks that every room can be reached.

### Phase D · Sunscar
- **The Sunscar Desert** (Lv 73–81, Storm Ward 45–50), south of Ironroot Hold down the desert road from the
  Clan Hearth: the Glass Dunes, the Scorpion Flats and the Worm Sea, a sand ground of wind ripples and desert
  glass, a new desert backdrop and a synthesized desert theme. The **Oasis of Bones** (rest, teleport stone)
  lies among the ribs of a giant beast, with Keeper Meng's stores and Bone-Reader Xiu.
- **The Tomb of Sunscar** (Lv 77, Storm Ward 55): the Sealed Gate, the Hall of Sand Kings, the Mirror Crypt and
  the **Throne of the Tomb King**, a dungeon boss who summons clay guards at 60% and enrages at 30%. Dungeon
  theme, tomb backdrop, statues, mirrors, sarcophagi and the King's throne.
- Four new monsters: the **Sandstorm Scorpion**, the burrowing **Dune Worm**, the **Terracotta Warden** and the
  **Tomb King of Sunscar**.
- Four new hazards: scorching heat (Essence; shrines give shade), sandstorms (Body; they push and blind),
  quicksand (Agility) and spike traps in the tomb (Agility).
- **Chapter 14, Sunscar**: Glass and Bone (follow the Pilgrim's caravan to the oasis), The Sealed Gate (cut the
  key's pieces out of the Dune Worms and read the gate's inscription, Insight 80), Sovereign (break through to
  Sage Sovereign 1) and The Tomb King (Lu's page in the Mirror Crypt, the King, and the sun seal: keep it, or put
  it back in his hand; either way the Grey Pilgrim leaves without it). Side stories: Cactus Water, Glass Teeth and
  Stingers for the Hold.
- **Sage-grade equipment**: sunsteel weapons and sunsilk armour (with the veiled weimao hat), forged from
  Sunglass and scorpion stingers from Sage Sovereign 1, and sold to Ironroot kin. Sunglass ore, Ember Cactus,
  the **Sovereign Settling Pill** (ends a new stage's consolidation), cactus water (+Essence against the heat),
  three titles and the King Sleeps achievement.
- Fixes: a boss's summoning phase now calls its own minions (the Thousand-Eye Toad summoned paper ghosts),
  phases can set the level of what they summon, and a new enrage phase shortens pauses and hardens blows.
  The Canyon Harpy's bleed was twenty times too strong. Act II delivery quests now take the goods they ask for.
  A burrower travelling underground now shows as a moving mound of sand or earth instead of vanishing.
- Tests: a new ae4 section plays chapter 14 end to end, buying Sage-grade gear before the tomb; the fight
  helper clears a boss's adds when they wear the player down.

### Room hazards (S17)
- The hazards rooms have always listed now act: **falling rocks** (Quarry Rim), **Hollow puddles** (Grey
  Pools), **the rapids current** (Rapids Terraces), **fog** (Misty Slopes), **wind gusts** (Windswept Ridge and
  the Gale Canyons), **lightning** (Thunderhorn Plains), **bitter cold** (Rimefrost Heights), and two the
  spec lists that no room used: **thorn thickets** in the Thicket Heart and **poison mist** from gas vents in
  the Mudwater tunnels.
- Each runs a readable cycle: a quiet tell (dust trickling, storm clouds, bubbles, a hiss), a warning with a
  broken amber border and a "!" mark that read without colour, the active blow, then a cooldown. A dodge
  through a strike avoids it; a shrine shelters from the cold; hazards start mid-cooldown, so nothing
  strikes on arrival, and safe rooms have none.
- One attribute answers each (Body for rocks, gusts, currents, cold, thorns and gas; Spirit for fog and the
  Hollow; Essence for lightning). A room asks k x (5 + its top Level); below that the effect falls to
  half as the answer nears, and once it is met pushes and statuses stop (a strike still lands at 35%).
  The room banner and the World map show each hazard with the attribute and value it asks.
- New thorn thicket and gas vent props, and eight synthesized sounds (rumble, rockfall, charge, thunder,
  gust, surge, hiss, frost). A `--hazard=phase[:fraction]` preview flag holds a room's hazards in one state.
- Tests: 19 new rules checks cover the answer formula, the cycle, strikes, dodging, gusts, currents,
  puddles and shelter.

### Phase C · Nine Peaks
- **Nine Peaks**, seat of the Alliance (town, teleport stone), reached by a second sky-ship route from the
  Skydock once the lake's mirror has spoken: the Alliance Gate, the Hall of Nine, the Auction Pavilion and
  the Presence Terrace, where the Alliance champion takes sparring challenges.
- **Alliance or the free road (S20).** "Nine Seats" ends in a choice kept on the character. The Alliance
  gives its token, the Factor's 10% discount and a smaller auction premium; the free road opens Broker
  Mu's back room (black-market lots) and the smallest premium. Envoy Lanshi changes your path once, for
  300 Spirit Stones. Titles for each: Alliance Envoy (+2 Storm Ward) and Free Cultivator (+3% drops).
- **NPC auction house (S21, Sage 1).** Four lots are open at all times, drawn from a pool of thirteen
  rare goods with staggered closing times. Five NPC bidders answer at once up to a limit they keep to
  themselves. A bid above it holds the lot; outbid stones return at once; a won lot arrives by mail.
  The house premium is 10%, 8% for the Alliance and 4% for the free road. A backward clock never closes
  a lot early.
- **Gale Canyons** (Lv 73–78, Storm Ward 35–42): the Canyon Mouth toll, the Kite Winds, the Harpy Roosts
  and the Windbridge (no flight), with the **Wind Kite** (a living swallow kite that throws wind
  blades), the **Canyon Harpy** and the veiled canyon brigands, under new canyon and Nine Peaks backdrops.
- **Ironroot Clan Hold (clans, Sage 2):** Hold Gate, Clan Hearth and Ancestor Hall. "Ironroot Blood"
  is the adoption: the warden's test of root, the Matriarch, and the ancestral tablets. Kin get the clan
  forge at 15% off and the Ironroot Kin title (+4% max HP).
- **Chapter 13, The Nine Peaks**: Nine Seats, The Canyon Toll (who pays the canyon toll in Hollow
  shards?) and Ironroot Blood, plus the guided Going Once at the auction block. Side stories: Silk on
  the Wind and Plumes for the Bellows.
- New materials (kite silk, harpy plume) and the Alliance and Ironroot tokens, with icons.
- Tests: a new ae3 section plays chapter 13 (path choice, factor discount, auction bids through the
  close and mail, the canyon, the clan and the path change); valley checkpoints now keep the run's clock.

### Phase B · Heights and lake
- **Rimefrost Heights** (Lv 67–72, Storm Ward 16–22): Frostpine Climb, the Snow Ape Ledges, Rimefrost
  Summit and the **Hermit's Ice Cave**, a hidden cave only Spirit Sense finds. Frost Lynx and Snow Ape,
  Frost Lotus herb patches, icicle-hung boulders and a snowbound parallax backdrop.
- **Mirrorwater Lake** (Lv 68–75, Storm Ward 22–28), reached by sky-ship from the Skydock: the Reedless
  Shore, the Mirror Shallows with their lotus lanterns, the Sentinel Causeway, the Lake Shrine and
  **Toad's Hollow**, home of the **Thousand-Eye Toad** (field boss, Lv 68). Azure Carp Dragonet and River
  Sentinel; a backdrop where the lake mirrors the floating peaks.
- **Chapter 12, The Grey Pilgrim**: Shards for Sale (a shadowless stranger buying Hollow shards),
  Frost and Silence (Hermit Shuang, a meditation in the ice cave) and The Mirror Remembers (the Lake
  Shrine's mirror shows the stranger and a young Lu; Lu's second journal page). Three side quests:
  Snow for the Cabinet, Clear Skies and A-Lan's Herd.
- New materials (rime fang, snow ape hide, dragonet scale, sentinel core, mirror eye, frost lotus) with
  icons, an ice-shard projectile, and the lake as a fishing spot.

### Phase A · Foundation
- The crossing: after the Gate Guardian falls, the Ascension Gate opens onto **Cloudgate Port**, a sky
  harbour on a floating island (Arrival Terrace, Port Market, Skydock, the Wayfarers' Inn and the
  Condensing Hall). The Expanse is its own zone: ceiling Sage Sovereign 3, Qi density 1.2–2.0,
  Spirit Stones as the everyday currency.
- **Thunderhorn Plains** (Lv 64–69): the Stormgrass Verge, Thunderhorn Flats, the Lightning Scar and the
  Herders' Camp, with two new monsters, the lightning-spitting **Spark Weasel** and the charging
  **Thunderhorn Rhino**, stormsteel ore veins and a thunder insight stone.
- **Storm Ward attunement** (S18): four jades per zone (Thunder, Gale, Rain, Lightning) on a new
  Character › Attunement tab, each raised with Storm Shards (level n costs n shards, up to 15). The total
  is set against what each room asks; under-attuned, you deal less and take more (S18 formula). Safe
  rooms ask nothing; a Storm Blood Pill adds +4 for 30 minutes.
- **Chapter 11**: Through the Gate, A Sky Full of Toll Roads, Storm in the Blood, Horns for the Furnace
  and Sage — the first breakthrough of the Expanse, to Sage 1 in the Condensing Hall (third-grade purity,
  the Sage Condensing Pill, and a land that can hold it).
- Fifteen new NPCs of the port and plains: the Alliance toll warden and factor, a veiled free broker,
  the Condensing Hall's alchemist, sky-ship hands, a stormsteel smith, an apothecary, innkeeper and
  herders. Two new avatar hats: the jade **Guan** crown of Alliance officials and the veiled
  **Weimao**, pose-registered in every action and both facings.
- Spirit-grade (stormsteel/stormsilk) gear in the Alliance Factor's hall, stormsteel forge blueprints
  from Sage 1 (Sage realms may refine Spirit grade), Thunderhorn Stew, the Storm Blood Pill, and five
  Spirit Stone shops. Spirit Stone prices come from tael prices at the exchange rate; loot coins in the
  Expanse pay Spirit Stones.
- A zone-aware World map (one tab per zone you have set foot in; the Expanse as islands in a sea of
  cloud, with each region's Storm Ward need). Teleporting across zones costs five times the fee.
- Art and sound: two new parallax backdrops (the storm plains under a thunder deck, the sky port among
  floating islands), sky-ships, herders' yurts, storm menhirs, the Alliance banner, stormsteel veins,
  Storm Ward jade icons, and two synthesized music loops (Cloudgate Port, the Thunderhorn Plains).
- Tests: the valley run now crosses the gate and plays chapter 11 to Sage 1 (a new ae1 section);
  the contract suite loads and compiles every script.

## 1.0 — The Complete Valley (Act I)

Built on the v0.13 movement and avatar engine, which is kept intact (its 3,660 engine checks pass).

### A game around the engine
- Five-layer architecture: data, state, rules, authorities, presentation. Sixteen authorities own every
  system; presentation only sends intents. Named random streams, a single clock, event queue, unlock
  service and v3 saves with migration from the v0.13 slots.
- The Jade River Valley: 75 rooms across 20 regions, built from data with painted buildings, ladders,
  depth stairs, driftwood platforms, hidden portals, teleport stones and layered parallax backdrops.
- The Prologue in Lotus Ferry: ten short quests, one lesson each, the HUD filling in one element at a
  time, the Hollow Night, and the first breakthrough on Lu's boat. No weapon and no Qi until earned.
- Act I: twelve chapters of main story, a guided quest for every system, side stories for the village,
  the merchants and all four companions, daily sect missions, a tournament, sieges and a finale at the
  Ascension Gate.

### Systems
- Cultivation: 89 realm stages, bottlenecks and breakthrough risk, methods with ceilings (Lu's fragment
  gives way to a sect scripture at no cost), meridians, body training, purity, stability, injuries,
  Daos and technique mastery, offline seclusion (accumulate, temper body, heal, contemplate, refine Qi,
  nourish soul) with caps and no offline breakthroughs.
- Retreat rooms and cave abodes: inner disciples get a door off the East Terrace or Array Court into
  the sect retreat rooms (seclusion up to 16 h, one breakthrough risk step safer); passing the
  mentor's trial opens a personal cave abode behind the elder's pagoda, with dense Qi, a spring,
  a mat and a bed.
- Combat: weapon-family combos, techniques, guard and dodge dash, elements, statuses, readable wind-ups,
  hit-stun, elites, field bosses, dungeon bosses with phases and weaknesses, story bosses (the
  Reflection, Elder Gu who flees with his ledger, the Gate Guardian), revival at shrines or on the spot.
- Crafts: gathering, mining, fishing, cooking, alchemy and the forge (timing mini-game), array plates,
  appraisal, formations, infirmary healing, worker puppets, manual restoration and teaching.
- Pill qualities: every refined pill keeps its quality (Flawed 50% with extra toxicity up to Perfect
  160%). From Heart Tempering 1 a run with every strike perfect may give a Pill Grain (180%, half the
  toxicity), a Pill Halo (200%, grows up to +50% while you sit in seclusion somewhere the Qi is dense)
  or a Pill Soul (220%, sometimes a unique effect). Sect Alchemy Hall furnaces and the Alchemy Dao
  raise the odds; quality pills glow in the bag with a dot, ring or star mark.
- Natural treasures (Spirit Awakening 8, "Treasures of Heaven and Earth"), one job each and never sold:
  the Mindwell Lotus behind Crane Falls (+500 Soul, mends the soul, shields it for an hour; once per
  great realm); the Evergreen Heart Tree, planted in rich earth on the elder's peak, a cave abode or the
  Back Mountain, whose fruit (one per season) revives you where you fell at full health; and the
  Nine-Bough Jade Tree at the Forgotten Monastery, which answers only an Understanding bottleneck with
  three quarters of your strongest Dao's gap to its next tier, once per stage. New props and icons.
- Spirit animal rarity and breeding: rarity (Common to Primordial) now scales an animal's strength and
  health. From Heaven Glimpse 1, with a level 4 Beast Pavilion, two Adults of one family (river, hound,
  burrow, wing) make an egg over a day; the child takes the higher rarity (sometimes one more), mixes
  its parents' traits and may carry a new one. The Spirit Animals page shows eggs with a Hatch button.
- Formations: the Restraint (monsters move 30% slower) and Concealment (monsters do not notice you until
  you strike) blueprints from library floor 3, completing the five valley formations. The blueprint
  list scrolls.
- Story: "The Riverbreath Trial" (Lu's inheritance at the Scripture Well: hold the ring while the drowned
  rise) before the Drowned Abbot, and "Farewells" split from "Beyond the Valley" (follow Lu's map to the
  Frozen Shrine first), matching the chapter list. Nine new side quests give the valley's quieter people
  a thread each (Fisher Wen, Washer Mei, Proprietor Fang, Smith Bao, Auntie Rong, Kai, Su Qing, Trader
  Min and a Wen Zhao rematch): 127 authored quests in all.
- Balance simulator: optional side quests now cost active time (10 minutes each) as well as paying their
  QP share, so adding side content no longer speeds the pacing. Every realm lands within 0.95-1.09 of the
  pacing table; Act I ends at 65.7 h (target 65).
- Emotes: a wheel in the Menu with the six starting emotes (bow, wave, cheer, fist salute, laugh, sit) and
  two earned from achievements (Champion, Beast Call). The avatar holds a pose, leans or bounces, with a
  speech bubble, until you move or act.
- Release checklist (S40): Settings > Data exports every save to one file (the device's Documents folder
  when allowed) and restores an export found on the device, keeping the current saves as backups; the
  engine log (five rotating files) can be exported for bug reports. A Credits screen (title and Settings)
  lists every LPC author and licence in full, the OFL fonts and the engine. Accessibility adds Bright
  flashes, Vibration and Captions for sounds (boss roars, bells, war drums, heavy wind-ups, off-screen
  notices). The notification toggle now switches every category. The Android preset is version 1.0.0.
- Companions, spirit animals (starter choice, taming with offerings, eggs), your own sect (buildings
  that appear as built, disciples, expeditions, defence raids), mail, achievements and titles.
- 27 pages on one shared frame, a HUD that reveals itself, a minimap, dialogue with portraits, shops,
  storage, map and teleports, codex, settings.

### Art and sound
- Mountain, gorge, quarry and cliff rooms walk on painted rocky ground, and the Summit Ridge on snow
  (`tools/art/bake_ground.py`, seamlessly tiling), instead of courtyard paving.
- 42 creature sheets, 45 backdrop layers, 114 scenery props, 12 music tracks and 39 sound effects.
- Human enemies and all NPCs use the layered avatar engine; shirts and trousers now come in ten baked dyes
  (every action and facing), so villagers, elders and sect robes look distinct. Equipment carries its dye.

### Interface pass (from screenshots of a mid-game save)
- Every item has its own icon: new thread-bound method manuals (cover and emblem by element), tied technique
  scrolls, curios (the fake jade reads as glass), spirit wood, puppet core, array plate and the late-realm
  pills. `data_validation` now checks that every item, piece of equipment and technique has an icon.
- Spirit Animals, Codex and Mail open on an entry instead of an empty pane; pets and the bestiary draw the
  creatures themselves (undiscovered ones as silhouettes); companions are drawn with the avatar engine.
- Your Sect shows real build costs; long descriptions are trimmed to fit; bar labels are outlined; the Main
  quest tab says which chapter comes next and what it waits for; the board never lists the same mission twice.

### Systems finished against the spec
- Flight from Cloud Stride 1: jump again at the top of a double jump to ride a cloud; hold Jump to climb and
  Guard to descend. Combat pays the QI each second, no-flight rooms and interiors refuse, landing or an
  empty pool ends it. "Wings of Cloud" now teaches it.
- Mounts (Cloud Stride 1): the Jade Crane, Mist Wolf and Ember Fox can carry you (Mount role, walk ×1.5);
  you stand on the crane's back as it glides; a hard blow throws you off for a while; a flying mount halves
  flight QI from Cloud Stride 5.
- Binding (Spirit Awakening 3): a found relic's power is sealed until bound with a channel that a blow
  breaks; its Artifact Spirit wakes through a soul contest (a failure bruises the soul). The Sleeping Blade
  goes from bare-hand power to its full edge once bound.
- Spirit animals grow: Hatchling, Juvenile and Adult (a branch choice) need level, hearts and your realm
  together; three hidden traits reveal as they grow and change real numbers; Resonance adds to accumulation.
- Zone ceilings and attunement (S18) are announced and applied; alchemy and forge strikes are scored by
  Crafting; lost raids damage a building until you repair it.
- Every event in the catalogue is emitted by the system that owns it. Enemies notice you with a "!", and the
  HUD reports raids, hatched eggs, revealed paths, codex entries, quests ready to hand in and more.

### Accessibility
- Enemy danger badges carry shapes as well as colours (▲ tougher, ▲▲ a realm above, ▽ weaker), next to the
  left-handed HUD and text-size settings.

### Text
- Every line the player reads (about 730 interface strings plus realms, currencies and unlocks) now comes
  from `data/strings/en.json`, ready for translation; a test keeps new text out of the scripts.

### Balance
- A balance simulator (S38) plays the data with the real rules: every realm of Act I lands within 11% of the
  pacing table (Qi Kindling at 4.7 h, Heaven Glimpse at 52 h, the end of the Act at 61 h), and the next gear
  upgrade costs 0.8 h of play at Level 15 and 1.4 h at Level 25.
- Monster kills before the Weapon Hall can no longer drop equipment.
- The weekly mission from the content catalogue, Sect Service: twenty daily missions or one field boss for
  150 contribution. Every other row of the Part 8 catalogue was already in the data.

### Found and fixed by the scripted Act I run
- Event spawns were wiped on room entry; stale companion uids could delete monsters; daily missions
  dropped four of five; the Hideout key, the library methods, the Sleeping Blade and the Siege had no
  source; the Core Disciple rank could not be reached; tools filled the bag; the first technique could
  not be used with a sword; kept quest items stopped counting once used in a recipe.

### Tests
- `data_validation`, `rules_tests` (with same-seed replay and offline checks), `prologue_run` and
  `valley_run` (the whole of Act I) join the engine checks; `tools/run_tests.sh` and `Test.ps1` run all.
