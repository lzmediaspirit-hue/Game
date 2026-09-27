# P5 · The Records family: the Codex, its Old Scrolls, and the Calendar

Screenshots of the Codex as the field book and its Old Scrolls as a mounted rubbing (`docs/page_identity.md` row 26,
mockups 18 and 18_scrolls, decision 11), and of the Calendar built to its first mockup (row 22, mockup 19, decision 22).
They are 1280 × 720 as captured, reduced to 256 colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of its checkpoints taken
by a valley_run on this build in a data folder of its own: `bf5` (Bone Forging 5, the day the collection book opens),
`qu5` (Qi Unfurling 5, the checkpoint mockup 19 was drawn from) and `ls6_end` (Sphere Lord 3, the checkpoint of mockups
18 and 18_scrolls). None uses the Max Test character, `--max-character` or `--unlock-all`. Each was captured headlessly
from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `codex_collection_ls6_end.png` | ls6_end | `--open-page=codex:collection --tap=527,152 --tap=1000,226` | Contents, then Reed Marsh: the spread of mockup 18 (page 4 of 14, leaves 7 and 8, the corners to Stonewall Quarry and Bamboo Grove); four beasts drawn on squared paper, the Hollowed Boarlet's card filled and stamped 50; the page's two seals, each with its gift (decision 27) |
| `codex_seals_claim_ls6_end.png`, `codex_seals_claimed_ls6_end.png` | ls6_end, Reed Marsh's four counts set to 500 in the copy (a stand-in for the hunting after the story; no valley_run reaches a full page) | `--open-page=codex:collection`, then `--tap=1128,542 --tap=1128,602` | Decision 27: the book opens at the page with a seal to claim, seal I glowing with Claim and seal II waiting on it; then both claimed through the intent, stamped, "Sealed", each gift listed |
| `codex_contents_ls6_end.png` | ls6_end | `--open-page=codex:collection --tap=527,152` | Contents on the right page: the fourteen pages, cards filled and each page's seal; the book opens at the first page still being filled (Willow Path) |
| `codex_collection_bf5.png` | bf5 | `--open-page=codex:collection` | Early: every beast a shadow with where it lives once you have been there, no card filled |
| `codex_scrolls_ls6_end.png` | ls6_end | `--open-page=codex:old_scrolls` | The Old Scrolls as mockup 18_scrolls: eight rungs rubbed, the gloss with "you" by Sphere Lord and "? ? ?" for Law Touching, Void Refining ringed and its note pinned |
| `codex_scrolls_rung_ls6_end.png` | ls6_end | `--open-page=codex:old_scrolls --tap=300,305` | A tap on Qi Refining: its note for Qi Unfurling, the upper layers (a second tap turns to Qi Kindling) |
| `codex_scrolls_bf5.png` | bf5 | `--open-page=codex:old_scrolls` | Early: two rungs rubbed, the rest bare paper with the carving only felt, the ink pad where the work stopped |
| `codex_entries_ls6_end.png`, `codex_achievements_ls6_end.png`, `codex_paths_ls6_end.png`, `codex_seasons_ls6_end.png` | ls6_end | `--open-page=codex:<tab>` | The other sections on the same book (no mockup): the contents and the entry read, achievements and paths above on the two pages with the corners to turn, the seasons with their rare herbs |
| `codex_text_large_ls6_end.png` | ls6_end | `--text-size=2` and the Reed Marsh taps | Settings › Text size › Large: long names end in an ellipsis inside their column |
| `calendar_qu5.png` | qu5 | `--open-page=calendar` | Mockup 19's Calendar: the four seasons from Spring, the week from Sunday with each world event on its day, the Drowned Shrine under way and chosen, Go there, the weather with what rain and a storm change |
| `calendar_tide_qu5.png` | qu5 | `--open-page=calendar --tap=640,482` | The Beast Tide chosen: Stoneford Gate, this week's tide and Go there |
| `calendar_bf5.png`, `calendar_ls6_end.png` | bf5, ls6_end | `--open-page=calendar` | Early (Go there shut: no way open to the Abbot's Sanctum yet, a tap says why) and late |
| `calendar_text_large_qu5.png` | qu5 | `--text-size=2 --open-page=calendar` | Large text |
| `compare_18_codex.png`, `compare_18_codex_scrolls.png`, `compare_19_calendar.png` | — | — | Each mockup above, the build below |

## Against mockup 18 (the Collection)

Matches: the desk, the jade cloth cover and the page block; two facing pages with the gutter's shadow and foxing; the
six sections as silk ribbons in their colours, the open one longer with its name inked on it and a bookmark into the
spread; the running heads, "Page 4 of 14" and the leaf numbers 7 and 8; Cards filled with its bar and the next stop
(the Collector title and its gift); Contents; the page's name with "4 beasts · a card fills at 50" and its seal mark;
each beast a drawing on squared paper taped in, its rank, nature and levels, what taming makes of it, its drops with
their icons and its count on an ink bar with its stop, a filled card stamped with its count; the curled corners with
the neighbouring pages' names.

Differences, each on purpose:

1. **The two seals are rules now (decision 27)**, drawn as 18 draws them with a Claim button: seal I every card at 50
   (Reed Marsh's gift +2% Hollow Ward), seal II every card at 500 after seal I (+1% healing received and a Bestiary
   Leaf; the toast on the claim names whose). The gifts are written as the game's other stat gifts are ("+2% hollow
   ward"). A filled card's bar runs on to 500 with the fill a stop on it, and its stamp says 500 once there. Contents
   shows each page's next seal.
2. **The beasts in data order** (Reed Frog, Marsh Leech, Greyfin, Hollowed Boarlet) and four a spread; a page with more
   (the Azure Expanse has 16) runs over several spreads. The ls6_end save has met all four Reed Marsh beasts, so none
   is a shadow here (see `codex_collection_bf5.png` for shadows).
3. **69 cards**, the data's count, where 18 wrote 68.
4. **The note** is what taming makes of a beast (`tame_species`); 18's "Charges twice" has no field in the data.
5. **Sizes on the type scale**: names in display 30 or 26, the running heads 14, where 18 had 15 in places.

## Against mockup 18_scrolls (the Old Scrolls)

Matches: the reading room's wall; the ribbons with Old Scrolls open; the hanging scroll with its brocade, silk, two rods
and jade caps; the rubbing inked from the top down to the rungs reached (Mortal to Void Refining at ls6_end), the carved
names pale, the rails, the cloud band, the chips and the crack; bare paper below with the carving felt and the ink pad;
Void Refining ringed in vermilion; "Our realms" glossed rung by rung (brackets for two realms, the halves, "you", "? ? ?"
for a realm not reached); "The rest is rubbed as you reach it."; the note on a sheet with a printed vermilion frame and
a jade pin: the entry's title, the rung, its half, the scholar's words, the levels, steps and years, the register's own
note and "Tap a rung to read its note".

Differences, each on purpose:

1. **The Old Scrolls are a tab of the Codex** (they were entries in its list); their entries leave the Codex's list,
   and the rung and half each names now live in the data (`tools/data/story.py`).
2. **"3 orders"**, the game's count, where 18 wrote "three orders"; the rung's title at 34, the top of the display scale.
3. **No new-dot on the Old Scrolls ribbon**: the account keeps no record of which entries were read.

## Against mockup 19 (the Calendar)

Matches: the kit's window, plaque and close button; the four seasons as a strip, the one now lit with its bar and time
left, the others with when they come; the week as seven columns from today ("Today" over its weekday, shaded), each
world event a slip on its day, gold under way and violet coming, with the one timer style; the red line at the hour now;
the Beast Tide across the week; the chosen event with its blossom, when and where, what it is and Go there with how many
regions away; the weather in the valley with its next change and what a storm changes.

Differences, each on purpose:

1. **The clock is the capture's**: the Drowned Shrine has 7 h 31 m left and the week starts on the capture's Sunday,
   so the rift, the fruit and the rest fall on their own days; the Spirit Fruit, left out of 19, is in the week.
2. **The line under the chosen event** says what it means for you from the rules (a repeat run's realm cap, the Terraces
   Trial's standing, the tide's week), in its own colour, under the event's words.
3. **The weather's regions keep the game's names** ("Reedmarsh"), and rain says what it changes too.
4. **A slip's name steps down to 14** where it would not fit at 16 ("Drowned Shrine" fits; 19 set every slip at 15).

Not shown in a still: the leaf turning over the spread (0.35 s) on a turn, a new section and the opening; the newest
rung dabbed in as the Old Scrolls open (0.4 s); the Calendar's slips dropping onto their days (0.3 s) and a live slip's
breathing glow. Under Reduce motion none of these run and the page fades in over 0.2 s (the `identity_suite`'s rules).
