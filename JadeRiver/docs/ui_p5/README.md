# P5 · The first pages with their own identity

Screenshots of the Character page as the jade-slip record (`docs/page_identity.md` row 13, mockup 09 v2, decisions 8
and 16), built on the P5 foundation (`docs/page_identity.md` §8). They are 1280 × 720 as captured, reduced to 256
colours; `.gdignore` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays through Acts I–III, from frozen copies of
its checkpoints taken by the full suite on this build (after the merge of the build branch with P12 Might): `ls6_end`
(Sphere Lord 3, Sect Master of the Jade Sect, a Reed Otter, Tie Niu and Lan Yue beside, in the Wardens' Hall) and
`bf2` (Bone Forging 2, early in the Prologue's valley). None uses the Max Test character, `--max-character` or
`--unlock-all`. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

`--tap=x,y` (new with P5, a debug tool like the others) taps the top page once it is open.

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `character_overview.png` | ls6_end | `--open-page=character` | The record: the slips fanned open, the figure at 2.5 on its washed slips with the eight worn slots either side (grade rims, the quality gem), who walks beside, the register, and the titles as honours with the worn one gilded |
| `character_overview_early.png` | bf2 | `--open-page=character` | Early: one pool, one honour; the weapon, cape and talisman slots closed with their locks (a tap says what opens each); the empty hat slot glowing jade because a Plain Straw Hat is in the bag |
| `character_titles_next.png` | ls6_end | `--open-page=character --tap=1080,652` | "15 more ›" turns to the next five honours, each with its own motif (a lotus for accumulation, a star for attunement, a pearl for max HP, a coin for drop rate, a peak for essence) |
| `character_title_worn.png` | ls6_end | `--open-page=character --tap=640,652` | A tap on Beast Friend wears it (`set_title`): it moves first into the gilded frame, the register's line under the name follows |
| `character_aptitude.png`, `character_attunement.png`, `character_wardrobe.png` | ls6_end | `--open-page=character:aptitude`, `:attunement`, `:wardrobe` | The other tabs written on the same slips; the figure stays on Wardrobe |
| `character_text_large.png` | ls6_end | `--text-size=2 --open-page=character` | Settings › Text size › Large: the tabs widen, the long gifts on the honours end in an ellipsis inside their bands |
| `compare_09_character.png` | ls6_end | — | Mockup 09 v2 above, the build below |

## Against mockup 09 v2

Matches: the whole window one mat of vertical jade slips bound by two gold cords with knots; the title and four tabs
as jade tags on the upper cord (the open tab lit, its label inked); the figure full-length on the first slips, washed
lighter; the worn slots down the slips either side with their names under them; "Beside you" with three round chips
and the names; the register (name, realm badge, Level and stage pips, sect, rank and the worn title after a gold ◆,
Combat Power, Relations with fame and alignment, the origin, the three pools, offence and defence in ruled columns with
Soul attack, Soul defence and Will); the titles at the foot, the worn one first, and a button to the rest; the shared
close button at the window's top right.

Differences, each on purpose:

1. **The titles are honours** (decision 16, after the mockup): red lacquer tablets with the title's motif on a gilt
   boss and its gift inscribed in gold on a sunk band, three to a row, five to a page; the worn one in a gilded frame
   with corner studs and the style guide's gold ◆ (§6: "you" is a mark, not a selection), where the mockup wrote
   "· worn" on a plain plaque.
2. **Words on the washed slips are `PAPER`**, not `MIST` as drawn: `MIST` reads 4.21:1 on `cloth_wash`, under the 4.5
   the `ui_suite` now holds every word on a page's own surface to.
3. **The numbers are this build's** (P12 Might): Combat Power 111,543, pools of 100,000 and more in the short form
   ("485K"), and the stats the save gives.
4. **The origin line**: the origin's own words when they fit the line; Fisher's Child's are longer, so the page writes
   what it gave in short ("+3 Body, +2 Essence, leans to water"), as the mockup's hand-shortened line did.
5. **Age and lifespan** stay (under Combat Power), from the old overview; the mockup had no room drawn for them.
6. **Empty cape and talisman slots** are plain: the cloud-seal motif of the mockup is the icon families' work (style
   guide §5, step 9).
7. **The companions' chips** show each companion's whole small figure, not a cropped head.
8. **The pips** follow the save (the Level inside Sphere Lord 3); the gems on the hat, robe, trousers and weapon mark
   their rolled quality, as `grade_rims` does.

Not shown in a still: the opening (the slips fan out from a bundle over 0.35 s; with Reduce motion on, the page only
fades in over 0.2 s), which the `identity_suite` checks.

## The Bag

The Bag was built as the spirit gourd of mockups 07 and 08 v2 and withdrawn before it merged, by decision 15 (no
gourd drawing; the inventory should feel like a big space, with a small card for the chosen item; new concepts go to
the user first). It keeps its P4 page (`docs/ui_after_p4/inventory.png`), so it has no pictures here.
