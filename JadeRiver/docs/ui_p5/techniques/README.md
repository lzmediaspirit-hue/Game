# P13b · The Techniques page

Screenshots of the Techniques page built to its approved mockups (`docs/mockups/06_techniques_tree.png`,
`06_techniques_tree_learned.png`, `06_techniques_lost_unknown.png`; roadmap §6 decisions 11, 18 and 19;
`docs/page_identity.md` row 15), each compare image with the mockup above and the build below. 1280 × 720 as
captured, reduced to 256 colours.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of this build's own
valley_run checkpoints (run with `XDG_DATA_HOME` in a scratch folder): `ls6_end` (Sphere Lord 3, Level 98) and `ht5`
(Heart Tempering 5, Level 43). None uses the Max Test character. Captured from `JadeRiver/` with

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=1 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `techniques_tree.png` | ls6_end | `--open-page=techniques:water` | The Water tab as it opens: the rail of seals (Time locked), the chooser with the Realisations to place and each family's Dao bar, the free hand's column of the Water tree on its tide chart, nothing chosen yet |
| `techniques_tree_keystone.png` | ls6_end | `… --tap=740,560 --preview-t=0.75` | Hundred Springs Rising chosen: under the chooser the character casting it at three imps at its impact; the reading with the character in its pose, Field and Water, its numbers, the prerequisites ticked and crossed, the cost, and Learn locked with why under it in gold (retaken after the preview; the other pictures of this table are P13b's) |
| `preview_strike.png`, `preview_multi.png`, `preview_ward.png` | ls6_end | `… --tap=120,300 --tap=566,285` (Dew Pillar), `… --tap=540,145` (Flowing Palm), `… --tap=540,285` (Still Water Focus), each with `--preview-t=` at four moments | The live preview under the chooser, four frames each, twice size: a single strike (a pillar on one imp: before, the column rising, the hit and its number, the fall), a multi-hit (Flowing Palm's flurry at a pack of three: the wind-up, the blows, the numbers, the imps knocked back), a ward (the dome rises and an imp's blow glances off it) |
| `techniques_tree_learned.png` | ls6_end | `… --tap=540,170` | Flowing Palm chosen: learned, its mastery diamonds and practice bar, Ring I slot 1 lit in the dock, Unslot and Rank up |
| `techniques_jian.png` | ls6_end | `--open-page=techniques:metal --tap=100,412` | The chooser's Jian row taps the view along the Metal tree to the jian's column: Silver Crescent open, "3 to learn" (its passage and the art) |
| `techniques_lost.png` | ls6_end | `--open-page=techniques:lost --tap=436,150` | The Lost Arts album, Act I: 2 of 21 found (Rain of Reeds, Lotus Mind), the other nineteen leaves sealed alike and only counted; Lotus Mind read at the right with Wear |
| `techniques_secret.png` | ls6_end | `--open-page=techniques:secret --tap=560,116` | The Secret Arts on the practice mat, Plunge read at the right |
| `techniques_drawer.png` | ls6_end | `--open-page=techniques:water --tap=762,688` | An Inner Art slot tapped: the drawer of known Inner Arts and the stances in the reading |
| `techniques_early.png` | ht5 | `--open-page=techniques` | Early: Space and Time locked, 43 to place, ring III and IV not yet reached, four slots open in each ring |
| `compare_06_techniques_tree.png`, `compare_06_techniques_tree_learned.png`, `compare_06_techniques_lost_unknown.png` | — | — | Each mockup above, the build below (the first retaken with the preview and the closed differences) |

## Against the mockups

Matches: the whole screen; the title on the rail and the element seals in the cycle, then Lost Arts and Secret Arts;
the three carved jade-teal panels with gold corner fittings; the chooser with the tab's element, the Realisations to
place, the families with their Daos as bars and the character under them; the tree as cards of 76 px pictures with
their names and state tags (Learned, "N to learn", Locked, the path's need, Keystone) joined by arrows through the
passage diamonds, the ring soundings and grades down the right, "Free-hand arts of Water" on its plaque and the rings
in view; the reading with its plaque, its line (kind, ring, grade, where it was taught), the picture and the emblem,
the numbers, the prerequisites with ticks and crosses, the cost in Realisations and Qi, the primary button; the
learned art's mastery diamonds, practice bar and slot; the Lost Arts album with its counts, found leaves with Unread
or Learned and every other leaf sealed alike; the dock with Ring I and II, the Inner Arts and the stance, and the
tab's verse.

Differences, each on purpose:

1. **The whole tree, not one family.** Decision 11 asks for one huge tree per element: a tab lays every family side by
   side (twelve columns of rings I–VIII, the notables under each act and their channels, the keystones, the Dao arts at
   the gates), dragged to pan; the chooser's rows jump along it and the plaque names the family in view. **Learned**
   (the jump from one learned art to the next) and **Let all go** (the tree's reset) sit small at the chart's top right,
   beside the plaque, with no strip under them, so the rows are 139 px apart as drawn.
2. **Cards show the art's picture composed at run time**, not a painted one (3,171 arts cannot each have a picture):
   the character himself in his gear, in the art's pose on the element's ground (a small still composed once a pose),
   with the art's emblem in its corner, dimmed while the art is closed. The form's own sheet plays in the reading's
   picture and the preview, not on the cards: the 24 sheets together are far too large to hold for a tree in view.
3. **The numbers are this build's.** A valley_run character made after the trees has no opening gift (the migration is
   for older saves), so ls6_end has 135 to place of 135, no passage walked, and the arts past ring I are locked by the
   route where the mockup had passage II walked. The generated names (Red River Eel Lunge, Flood Lullaby) are the
   data's. Act I holds 21 lost arts in the data; the album scrolls past four rows.
4. **Learn names what it spends when it is open** ("Learn · 5 Realisations"), the open point from the review; closed,
   it is plain Learn with the lock, as drawn, and the reason under it in gold is the rules' own ("Realise the way to it
   first").
5. **No "Where it was found"** on a found lost art: the board's card never says where an art came from (decision 19 as
   built in P13a, held by `lost_arts_suite`); the reading says what it is and does, and Wear, Slot or Read.
6. **The Unread leaves** are a manual carried and not yet read (Read on the reading); Tester at ls6_end carries none.
7. **The Dao bar follows the tab**: the free hand's bar is the tab's element Dao (Water on Water, Fire on Fire); a
   weapon family's is its weapon Dao; Formless has none.
8. **Each tab's own chart** is drawn by one painter in the element's colour (currents, depth contours, soundings); the
   plan's eleven distinct projections (a living tree for Wood, a forge sky for Fire …) are later work.
9. **The drawer**: an Inner Art or the stance in the dock opens the known Inner Arts and the stances in the reading, as
   §4.10 plans; the mockups do not draw it.
10. **The live preview** (not in the mockups): the character under the chooser, a little smaller than drawn, casts the
    chosen art as a fight does (its pose, its form's sheet through `FxLayer.cast`, its hits through `FxLayer.hit`) at
    pebble imps: one for a single strike, a pack for a multi-hit or area form; a ward's dome turns an imp's blow, a
    counter parries one, a snare or a seal holds its imp. It loops with a pause, restarts on another art, holds one
    still frame at the impact under Reduce motion and steps at 30 fps under Battery saver; a passage, an Inner Art or an
    art not yet found shows nothing.
