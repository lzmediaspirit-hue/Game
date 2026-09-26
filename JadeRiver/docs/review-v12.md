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
