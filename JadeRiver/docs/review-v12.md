# v1.2 review (P2): the playthrough, the inventory, the references and the plan

The first half of the Full Review (`docs/roadmap_master_ui.md` §3, P2). Its six parts:

- **(a)** the playthrough log, Prologue to the end of v1.2;
- **(b)** the project inventory, `docs/ui_inventory.md`;
- **(c)** the reference research, `docs/research/ui_reference_notes.md` and `docs/research/retention_notes.md`;
- **(d)** the UI review with severity and location;
- **(e)** the engagement, psychology and feel plan, and the Single Player / Online note per system;
- **(f)** every proposed change, ordered by impact against effort.

Every finding here has a fix, and every fix has a test or a screenshot. The page keeps no open bug list.

## (a) The playthrough log

### Method

The game is played by intents only, the way the touch UI submits them, from a new character to the end of Act III:

- `tests/prologue_run.gd` plays the Prologue.
- `tests/valley_run.gd` plays every guided and main quest of Acts I–III, 26 sections from Bone Forging 2 to Greyfall,
  with a checkpoint at each.
  - It travels room to room through the real portals, talks, fights, spars, crafts, attunes and breaks through.
  - Grinding is shortened with named test shortcuts (progress bars, long boss chipping); every other step goes
    through the real authorities.
- Each new region is also opened headlessly with `--room`, and each screenshot is looked at. The
  screenshots are listed with their chapters below.

Each finding reads *finding → root cause → fix → verification*.

### Findings in Act III (chapters 20–22)

| # | Finding | Root cause | Fix | Verification |
|---|---|---|---|---|
| 1 | The Inverted Hall's low-gravity halls were light from the moment you entered, before any switch was pressed | A volume tied to a switch started with `off = invert` instead of `off = not invert` (`zone_geometry.gd`) | A switch-tied volume starts off unless it is inverted | `rules_tests` `sphere_suite`: "with its switch up the hall pulls as hard as anywhere"; the switch toggles it to 45% and back |
| 2 | The high gallery meant to need the switch was reachable with a normal double jump | Natural surface heights snap to multiples of 100 (the verticality pass), so 330 became 300, under the 302 a double jump reaches from the low gallery | The gallery sits at 400 | `sphere_suite`: out of reach of any jump, within a light double jump from the floor |
| 3 | A failed Sphere Lord breakthrough could leave a player stuck for good | A failed major breakthrough consumes its materials, and the Sphere Comprehension Stone had one source (a quest reward) | Stargazer Ming sells another stone after the Observatory (80 crystals) | `valley_run` `ls4`: the first attempt fails and consumes the stone; the run replaces it (a test shortcut standing in for Ming's shop row) and the next attempt holds; `lantern_heart_suite` checks the stone is on Ming's shelf |
| 4 | After training the Presence to level 5, the Observatory quest was not offered until the player changed room | `presence_leveled` was not among the events that refresh quest offers | It is now | `valley_run` `ls4` accepts The Observatory in the same room |
| 5 | Warden Xiao never offered chapter 20 | Her post-Admiral dialogue tree outranks quest offers, and it opened after The Admiral | The tree now waits until The Citadel is done | `valley_run` `ls4` accepts The Citadel from her |
| 6 | Harbormaster Lin would have hidden chapter 22 in the same way | Her tree opened after Crystal and Jade | It now waits until Lu's Lantern is done | `valley_run` `ls6` accepts Lu's Lantern from her |
| 7 | In the Lantern Star Field, Beast Taming could not grow past tier 2 and the rare Daos not at all | Dao caps are per zone, and the Field listed none for them, so they fell back to the valley's caps | A zone keeps at least the cap the zone before it allowed (`techniques.py`) | `rules_tests` `ash_tide_suite`: Beast Taming and the rare Daos hold 4 in the Field |
| 8 | A fresh clone failed the icon checks for the Phase C icons | The icon commit carried the PNGs but not their `.import` files | The `.import` files are committed; later icon commits take them with the PNGs | `git ls-files` counts one `.import` per icon; the full suite passes on a clean snapshot |
| 9 | Kharn was not found when the run entered his pyre | The run looked for him before the room's first spawn tick (not a game bug); his room was also typed as a dungeon where the other story bosses stand in boss arenas | The run waits for the spawn; the room is a boss arena like the Admiral's deck | `valley_run` `ls5` fights him, he kneels, he is spared |
| 10 | The chapter 20 room lint failed twice as the Wardens' skiffs were added | The verticality pass keeps raised routes clear of portals, and a portal in the middle of a route broke it below 40% of the room | Portals moved into gaps between routes | `room_lint`: 168 rooms, 0 failing |

Screenshots taken for this pass:

- Chapter 20: the Citadel Gate, the Observatory, the Inverted Hall, the Orbit Garden, the Presence Court.
- Chapter 21: the Cinder Fields, Kharn's Pyre, the Tidebreak Bastion.
- Chapter 22: the Nebula Verge, the Leviathan's Maw, the Hall of Burning Stars, the Flame Heart.

None showed a layout fault. One cosmetic note is left to P5: with every system unlocked, the HUD's technique arc
and toggles fill the lower middle of the screen. Its fix belongs to the approved HUD mockup (P3), not to a patch.

### Findings in Acts I–II

These are the earlier reviews' findings, all fixed, with their tests:

- `docs/review-v08.md`, `docs/review-v09.md` and `docs/review-v13.md` cover movement, landing and gates.
- P1 (`CHANGELOG.md`, P1) covers the training dummy beside an NPC and quest direction.

The Act I–II sections of `valley_run` pass unchanged on this commit.

## (e) The engagement plan, the psychology and feel plan, and Single Player / Online

The research behind this part is `docs/research/retention_notes.md` (the loops and the psychology, with sources) and
`docs/research/ui_reference_notes.md` §10–§12. Its §4 lists what Jade River already has; this part plans only what it
lacks. Each row names the owning authority, the phase that builds it and the test that proves it. Names are Jade
River's own.

### The engagement plan (M21)

What already works, and stays:

- **Daily:** sect missions, four activity chests, the Trial Tower sweep, county jobs, the thief chase and Keeping
  Post's round.
- **Weekly:** Sect Service, the Saturday auction, the Beast Tide and the Herb Terraces trial.
- **Offline:** seclusion (capped at 12 h), Keeping Post (capped by the pouch), gardens, racks, the Dew Vial and the
  Welcome Back page.
- **Catch-up:** Ancestral Guidance (×1.5 for a character two great realms or more behind the account's highest) and
  the Account Legacy (+2% per realm recorded), in `progression_authority.gd:111-116`. The first version of the
  retention notes missed this, and they are corrected.

The gaps, each with its plan:

| # | Gap | The loop it serves | Plan | Owner and phase | Test |
|---|---|---|---|---|---|
| E1 | No login reward | A daily reason to open the game, without punishing a missed day (loss aversion, `retention_notes.md` §1.3) | **The Dawn Censer.** The first entry of each day lights one incense stick at the account's censer. Every seventh stick gives a censer reward, from a 28-step track that loops. The track is cumulative, not consecutive, so a missed day costs nothing. Rewards are Spirit Stones, a pouch of herbs, Lantern Incense and, every 28th stick, a cosmetic dye | `AccountAuthority`, a `data/censer.json` track; the Welcome Back page shows the stick lit. P5 (the page), v1.3 (the data) | `rules_tests`: one stick per day however many entries; the seventh stick pays; no reset after a gap of five days |
| E2 | Dailies do not bank | Returning after a missed day finds nothing waiting (the "wasted day" feeling) | **Carried missions.** Unfinished daily sect missions carry over for one more day, so at most two days' missions stand on the board. Activity chests do not bank, since they reward the same day's play | `QuestAuthority` (`quest_authority.gd:587-615`). v1.3 | `rules_tests`: a day's missions survive one reset, not two; a carried mission counts for the weekly Sect Service |
| E3 | A complete collection stops giving | Completion drive (§2.4): the last page should open a next goal, not end one | **The second seal.** A completed Collection page can be sealed a second time by ten times the kills, for a second stat line and a Bestiary Leaf. Completion stays a single event per seal | `AccountAuthority` (`account_authority.gd:523-529`). P7b (with the volume plan) | `rules_tests`: the second seal needs ten times the count and pays once |
| E4 | No stops on long bars | Goal gradient (§1.2): a bar with marked stops feels shorter | Tick marks at every reward threshold on the Dao, collection, activity and Presence bars, and the next reward shown at the bar's end | Presentation only. P5 | Screenshots of the four bars against the P3 mockups |
| E5 | "One more level" is not shown | The next reward pulls harder when it is visible (§2.5) | The Cultivation page's ascent names what the next stage unlocks (a system, a slot, a technique grade) beside its requirement | Presentation, from `unlocks.json`. P5 | `rules_tests` `ui_suite`: every stage with an unlock names it |
| E6 | No real social loop | Relatedness (§1.5) | **Single Player:** keep the stand-ins: the AI companions, bonds, your sect's disciples, the Heaven Ranking and the young masters' challenges. **Online (v2.0):** sect alliances between players, trading at the auction, shared field bosses with per-player loot, and mail between players (see the table below) | v2.0 | v2.0's own suites |

### The psychology and feel plan (M22–M26)

| # | Finding | Plan | Owner and phase | Test |
|---|---|---|---|---|
| F1 | Techniques do not grow in spectacle with the realm (M22). `techniques.json` has no effect field; every technique uses one of `fx_layer.gd`'s generic kinds | A `vfx` block on each technique: a shape (strike, wave, ring, rain, pillar, domain), a scale tier from its grade, and the element's colour. `fx_layer.gd` draws each tier larger and with more parts: Mortal grade is a flash, Heaven grade fills the screen for 0.4 s | Data in `tools/data/techniques.py`, drawing in `fx_layer.gd`. P6 | `data_validation`: every technique has a `vfx` block; screenshots of one technique per tier |
| F2 | Numbers and particles are flat (M23): eight sparks, one number per hit | Multi-hit techniques show one number per hit, stacked and fanned; crits keep gold and grow; particles by element (ink drops for the brush, sound rings for the bell) | `fx_layer.gd`. P6 | Screenshots in a fight with a three-hit technique |
| F3 | Colour has no written rule (M24): grade and quality colours exist, biome palettes do not, and no check that colours read on a phone | Palette roles in the style guide: primary, grade, quality, positive, negative, disabled. One rule per biome (a warm or cool bias, the accent). A contrast check of every text colour against its panel | `docs/ui_style_guide.md`, `UiKit`. P4 | `ui_suite`: every text colour has a contrast of 4.5:1 or more on its panel |
| F4 | Rewards land quietly (M25): a breakthrough is a flash and a sound; loot bounces but does not burst | **Breakthrough:** a three-beat sequence (the light gathers, the realm's name is written in a brush stroke, the new stats rise). **Boss loot:** it bursts out in a fountain and settles. **Levels:** a short gong | `world.gd`, `fx_layer.gd`, `Audio`. P6 | Screenshots at each beat; `rules_tests`: the sequence never blocks input for more than 1.5 s |
| F5 | Bosses lack readable danger (M38–M40) | Ground markers before every heavy blow, a phase card at each phase, and an enrage timer | `EnemyBrain`, `fx_layer.gd`. P9 | `boss_suite`: every boss has two phases and a telegraphed mechanic |
| F6 | Defeat should sting without driving a player away (loss aversion) | Keep today's rule: a grave wound, then revive at a shrine, in place with a Revival Talisman, or with an Evergreen Heart Fruit, and no penalty in the Prologue or in marked rooms (`combat_authority.gd:1481-1536`). Add a line on the wound screen that says what was lost and what was kept | Presentation. P5 | Screenshot of the wound screen |

M26 (a plan for each finding) is met by the two tables above and by part (f).

### Single Player and Online, per system (M51)

The per-system split is a second table under the authority table in `docs/architecture.md`. Each system names what
runs locally now and what a v2.0 server must own. The rule behind it is the extension contract in the same page: the
server owns every write, and the client submits the same intents it submits today.
