# P5 · The Bonds family: Companions, Gift and Relations

The Gift as a red-lacquered tray held out over the talk (`docs/page_identity.md` row 28, mockup `21_dialogue_gift`),
the Companions as moon gates in a whitewashed garden wall (row 27) and the Relations as the karma steelyard (row 42);
the last two have no mockup and are drawn from their rows and the family's material (§2: whitewash and red thread).
They are 1280 × 720 as captured, reduced to 256 colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing
them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of its checkpoints taken
by a valley_run on this build in a data folder of its own (`XDG_DATA_HOME` in a scratch folder): `qu5` (Qi Unfurling
4, the checkpoint of mockup 21) and `ls6_end` (Sphere Lord 3). None uses the Max Test character, `--max-character` or
`--unlock-all`. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=4 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `gift_qu5.png` | qu5 | `--talk=lan_yue --tap=640,600` three times, `--tap=1047,520` (Give a gift) | The tray held out over Lan Yue's talk: "A gift for Lan Yue · one a day", Loves and Likes not yet known, ten compartments of the bag's giftable things and "+9", Give shut until something is picked; the strip keeps her portrait, plaque, hearts and "Healer · 0 hearts", the rules and the heart bar, and the talk's other choice (Farewell) |
| `gift_given_qu5.png` | qu5 | as above, then `--tap=308,358 --tap=354,428` (the Herbal Tea, Give) | The gift given: "Lan Yue likes it." and what it taught you, the heart bar at 40 / 100 with +40, Likes now Herbal Tea, Give shut with "They've had a gift from you today. Come back tomorrow." |
| `companions_ls6_end.png` | ls6_end | `--open-page=companions` | The wall under its coping of jade tiles, the title on a lacquer board; Tie Niu and Lan Yue each in a moon gate with the garden beyond, both beside you with their lanterns lit; their hearts as knots on the red thread; Tie Niu chosen (gilded ring) with Active, Gift, Duel (three hearts first) and Swear Siblings (four hearts first) under his gate |
| `companions_chosen_ls6_end.png` | ls6_end | `--open-page=companions --tap=928,272` | A tap on Lan Yue's gate chooses her: the actions move under her gate |
| `relations_karma_ls6_end.png` | ls6_end | `--open-page=relations:karma` | The rafter with the title and the tabs as tally tags; the fame plaque (Rising) on the hook; the beam leaning toward Righteous (Upright +41), merit's gold weight (126) against sin's black (0), the recent merit notched along the beam; the ledger and the Fortune, deeds and debts on two boards hung on hemp cords |
| `relations_bonds_ls6_end.png` | ls6_end | `--open-page=relations:bonds` | The Dao Companion, Master (Elder Hu) and Sworn Siblings boards and the friends with their hearts, hung on red thread |
| `relations_grudges_ls6_end.png` | ls6_end | `--open-page=relations:grudges` | The grudges board on black thread: the Mudwater Bandits at 15 of 30 with blood money and the duel |
| `relations_fame_ls6_end.png` | ls6_end | `--open-page=relations:fame` | Your name: Fame 352, 48 to Renowned, the ladder with Rising marked; no challenger waiting |
| `compare_21_dialogue_gift.png` | — | — | Mockup 21_dialogue_gift above, `gift_given_qu5.png` below |

## Against mockup 21_dialogue_gift

Matches: the tray above the talk at the mockup's place (252, 268, 972 × 188), the title "A gift for …" with "one a
day", Loves and Likes at the right (not yet known until a gift teaches you), a row of ten 76 px compartments with the
counts and "+n" for the rest, the disabled Give with its lock and today's line beside it; under it the talk's own
strip: the portrait, the name plaque, the hearts and who they are, the answer in large ink ("… likes it."), the line
under it, the heart bar with its count to the next heart and the "+40" it moved, the numbered choices at the right.

Differences, each on purpose:

1. **The tray is red lacquer in a gold rim** (row 28 and the family: the HD `gift_tray`), not the kit's teal panel the
   mockup drew; each compartment is a well sunk in it with a gold fillet.
2. **The person is Lan Yue**, whose talk offers the gift at qu5; Elder Hu's talk at this checkpoint offers a quest, and
   a talk with a quest to offer carries no "Give a gift" (the Dialogue's rule). Her Herbal Tea is liked, so her answer
   is the mockup's "likes it" with its +40.
3. **The line under the answer says what the gift taught you** ("Now you know it is something they like."); the
   mockup's "He turns the page to the light…" would need a line per person and gift, which no data holds.
4. **The "Likes it" tag** (a pink tag over a compartment) shows on a thing they are known to like while you still hold
   one; Lan Yue's only Herbal Tea is the one given, so no tag is left in the picture. Known things come first in the
   tray. The `identity_suite` checks the tag.
5. **The choices are the talk's own**: those the talk had besides the gift (four at most, Farewell kept), so Lan Yue's
   strip has Farewell alone; the mockup's "About the Drowned Abbot" was Elder Hu's.
6. **The heart bar's words** say "to the next heart", as the page said before, not "to the fifth heart".

## The other two (no mockup)

- **Companions** keeps every action (Bring along, Gift, the friendly duel, Swear Siblings, ask to be Dao Companions);
  they stand under the chosen friend's gate only, as the row asks. A gate holds a friend full-length from their own
  layers (at 1.6). With no friend yet the wall shows three empty gates and how they come.
- **Relations** keeps its four tabs and every piece of each; the old alignment bar stays on the ledger's board, and
  the beam shows the same lean. The fame ladder's tiers not reached are in mist, not hollow grey, which is too dim on
  the timber.

Not shown in a still: the tray held out from behind the strip as the page opens and a given gift lifting from its
compartment toward the speaker while the bar fills (0.3 s); a lantern lighting when a friend is brought along (0.2 s)
and a new heart's knot tying (0.3 s); the red thread drawn along the wall as the Companions open; the beam swinging to
its lean (0.35 s, damped) and the weights' sway. Under Reduce motion none of these run and each page fades in over 0.2 s.
