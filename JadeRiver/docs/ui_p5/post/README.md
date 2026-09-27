# P5 · The Post family

Screenshots of the Roll-Call, Works, Welcome Back and Pouches built with their own identity (`docs/page_identity.md`
rows 14, 23, 12 and 44; mockups `13_roll_call`, `13_roll_call_first` and `14_works_v4`; decisions 11, 14, 21 and 26).
They are 1280 × 720 as captured, reduced to 256 colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing
them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of the checkpoints a
valley_run of this build took: `ls6_end` (Sphere Lord 3, in the Wardens' Hall, the Second Disciple beside him on the
account) and `bf5` (early in the Prologue, before Keeping Post). None uses the Max Test character, `--max-character` or
`--unlock-all`. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

`--posts-demo` (S50) sets two more characters at the room's nodes, hours in (one full, one filling), as the mockup's
scratch copy did; `--welcome-demo` (new, a debug tool) brings the active character in from 7.5 hours at its post (or at
the room's first node) and opens Welcome Back on the post authority's real Return Ledger.

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `roll_call.png` | ls6_end | `--room=ja_herb_terraces --posts-demo --open-page=posts` | The board: Tester playing (no post, the dashed basket place), the Second Disciple full and idle with a heaped, glowing basket and a red tag, Bai Lin working, an empty peg; Settle and Switch under each; Settle all with its ready seal, the Storehouse cabinet with its drawers and Auto-Settle, the Bench with its cord, Collect, 6 points and the craft-level bar |
| `roll_call_turned.png` | ls6_end | the same and `--tap=374,300` | The Second Disciple's tablet turned over: Lv 1 · Finesse 52, what comes in an hour, the Chance bar, the Incense locked (none carried) |
| `roll_call_first.png` | bf5 | `--open-page=posts` | A new player's board: Tester alone, "Your first post" pinned where more tablets will hang with its three steps, the Storehouse empty, the Bench locked with what opens it |
| `roll_call_crafts.png`, `roll_call_storehouse.png`, `roll_call_bench.png` | ls6_end | `--open-page=posts:crafts`, `:store`, `:bench` | The other views on the same board, the right column staying |
| `works_seals.png`, `works_furnace.png` | ls6_end | `--open-page=works:seals`, `:furnace` | The curio cabinet: the seven objects at their native 96, Favours and Mirror behind their lattices with what opens them, the chosen compartment lit; five Seal Scripts on the tray; the slip of what the works add |
| `welcome_back.png` | ls6_end | `--room=ja_herb_terraces --welcome-demo` | The coil burnt 7 h 30 m of its 12 h, the ember at the mark; Willow Moss and Spirit Wood in the tray; the post, its EXP and level and the full pouch on the slip; To the Storehouse and Keep in pouch |
| `pouches.png` | ls6_end | `--open-page=pouches` | Seven chalked pouches, unsewn, each with its next fold, price and Sew; the ruler |
| `compare_13_roll_call.png`, `compare_13_roll_call_first.png`, `compare_14_works_v4.png` | — | — | Each mockup above, the build below |

## Against the mockups

Matches (13): the board of dark planks with the gilt cartouche on the beam and the tags at its left; four arched name
tablets on red cords from the peg rail, each with its figure in the window (standing while played, seated at rest), the
name, the craft with its glyph and level, the place and the state band (gold playing, red full and idle, jade filling);
a tassel in the band's colour; the vessels on the shelf filled with the goods, a glow on a full one, the paper tags (red
when full); Settle and the Switch figure under each; the soonest-full line; Settle all with its goods and ready seal; the
Storehouse under its tiled roof with 76 px drawers and the empty ones' cloud mark; Auto-Settle; the Bench with its thing,
tag, Collect, points and the craft-level bar. (13_first): the pinned note with its three numbered steps and glyphs, the
empty Storehouse, the Bench locked with its reason. (14 v4): the bamboo wall and cabinet, the compartments of different
widths, the objects at 96, the hemp labels with the state, the ready seals, the lattices and what opens each, the tray
with five Seal Scripts, their costs in wells, Inscribe, the slip with what the works add, the Storehouse and the silver.

Differences, each on purpose:

1. **The tabs.** The mockup hangs Crafts and Vows on the beam and has no way back to the board; the build hangs Board,
   Crafts and Vows there, and the Storehouse's and the Bench's plaques are their tabs, opening the full cabinet (every
   drawer, the Granary Seal) and the bench (apprentices, points), which the board shows only in summary.
2. **The characters** are the checkpoint's own: Tester has no post at ls6_end, so his place on the shelf is the dashed
   basket; the others come from `--posts-demo` at the Herb Terraces, not the mockup's Bai Lin at Reed Shallows and Wen
   Ruo's cicada cage.
3. **The window's scene** is a sky over the post's ground in tokens; the mockup painted a scene per craft.
4. **The turned tablet** keeps the first output's Chance bar and the incense; the mockup's locked next output (Jade
   Scarab at Netting 12) is not drawn, since the post's rates list only what the level reaches.
5. **Settle and Auto-Settle** are the kit's buttons with their words only (no goods glyph on Settle, no switch drawn on
   Auto-Settle, which says on or off); the mockup's pressed Settle with "+400" is the catch that lifts out on a tap.
6. **The first note** has no quest chip ("Keeping Post, step 2 of 2"); it shows while Keeping Post is not done.
7. **Works' labels** use the tabs' short names (Arts, not Post Arts); the heading on the tray names the work in full.
   The cells are 116 high, not 128, so five 56 px Seal rows fit under them with 48 px buttons.
8. **The slip** writes what the works add from the rules (stele power, seal Finesse, diligence from arts, seals and
   favours, the flags where the character works); the seal's print on paper beside the jade seal is not drawn.

Welcome Back and Pouches have no mockup; they follow their rows: the ember runs over the page's 0.35 s opening (the
row's 0.6 s is past rule 2 of §6), and the rest of the ledger sits on a hemp slip beside the tray.

Not shown in a still: the tablets swinging onto their pegs as the board opens, a tablet turning (0.25 s), the catch
lifting out of a vessel on Settle, the chosen object lifting in its compartment, the coil's ember running, goods dropping
into the tray 0.05 s apart, a stitch running round a sewn pattern; under Reduce motion the pages only fade in and the
tablet changes face at once.
