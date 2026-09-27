# P5 · The Bag as the heaven in the gourd

Screenshots of the Bag built as concept B (roadmap decision 24; `docs/page_identity.md` row 3; mockups `07_bag_b`,
`07_bag_b_card`, `07_bag_b_pill` and `08_bag_b_empty`), each beside its mockup. They are 1280 × 720 as captured, reduced
to 256 colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of its checkpoints taken
by a valley_run of this build: `ls6_end` (Sphere Lord 3, the Sunsteel Gourd, 43 of 55) and `bf2` (Bone Forging 2, the
Starter Spirit Gourd, 8 of 25). None uses the Max Test character, `--max-character` or `--unlock-all`. Each was captured
headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `bag_full.png` | ls6_end | `--open-page=inventory` | The sky of a big gourd (stars, the light from its mouth, five far islands, the sea of cloud); the figure on its island with the eight worn slots on the gold orbit; the grid ten across, five rows in view and the sixth (the last free spaces and the Driftglass Gourd's five, locked) fading into the cloud; the kinds, the Key Pouch, the purses and Sort as floating tokens; "Space 43 / 55" and the next gourd |
| `bag_card_weapon.png` | ls6_end | `… --tap=1090,454` | The Lanternsteel Jian tapped: its card to the left of its space, "Against your Sunsteel Jian" with the three totals that change most and Combat Power, the rolls, Equip, Set as spare and "···"; the worn jian ringed on the orbit |
| `bag_card_pill.png` | ls6_end | `… --tap=610,214` | The Healing Pills tapped: on the grid's top row the card opens below the space; what it does, its toxicity against yours, what quick-use holds (none left), Use, Quick-use and "···" |
| `bag_early.png` | bf2 | `--open-page=inventory` | A small gourd's small sky (fewer stars, one far island, no light from above), three rows with the Bamboo Gourd's five spaces locked; the empty hat slot glowing jade because the Plain Straw Hat fits it; weapon, cape and talisman locked; the hint in the open sky |
| `bag_worn.png` | ls6_end | `… --tap=317,230` | The worn Sunsteel Jian tapped: its card beside the orbit, "What it gives you" (your totals as they stand and what the jian adds to each), the rolls and Unequip |
| `bag_more.png` | ls6_end | `… --tap=1090,454 --tap=999,566` | "···" opened: Lock, Discard and Self-detonate under the card's actions |
| `bag_pills.png` | ls6_end | `… --tap=660,136` | The Pills kind: only the seven pills, in the bag's order |
| `bag_key_pouch.png` | ls6_end | `… --tap=670,74 --tap=850,374` | The Key Pouch (28) as the same floating grid, the Cloud Skiff's card |
| `bag_text_large.png` | ls6_end | `--text-size=2 … --tap=1090,454` | Settings › Text size › Large: the tokens widen, the Sage Crystals purse gives way to the Key Pouch, the card's rows wrap |
| `compare_07_bag_b.png`, `compare_07_bag_b_card.png`, `compare_07_bag_b_pill.png`, `compare_08_bag_b_empty.png` | — | — | Each mockup above, the build below |

## Against the mockups

Matches: no frame and no gourd, the page a night sky over a sea of cloud that grows with the gourd; the title and the
gourd's line at the top left; the Spirit Gourd and Key Pouch tokens, the purses and the close button along the top; the
kinds with their counts (a kind with none dimmed) and Sort; one grid ten across with grade rims and quality gems, five
rows in view and the next fading into the cloud, the next gourd's spaces locked, the thread of the scroll at the right;
the figure at 2.5 on its island with the eight worn slots on a dotted gold orbit; "Space n / m" and the next gourd; the
card beside the tapped space with its pointer, the comparison written as the totals after the change with the change
beside each, the rolls, and two actions and "···"; below the space on the top row; the worn piece a card is about ringed
in gold dashes; early, the small sky, three rows and the hint with what opens the locked slots.

Differences, each on purpose:

1. **The standard window.** Everything that takes a tap or carries a word stays inside the full window (64–1216 ×
   32–688, the `ui_suite`'s rule), and the close button is Page's, at the window's top right; the sky itself still fills
   the screen. So the layout is the mockup's drawn into 1152 px: the orbit is narrower (the robe and trousers at x 67,
   not 8), the grid starts at 412 and 12 px lower, the purses end left of the close button.
2. **The numbers are this build's.** ls6_end holds 43 of 55 today, 65,239 taels, and a Lanternsteel Jian of Superior
   quality at item level 97 rolled with penetration and physical attack: against the worn Sunsteel Jian +7 it would
   lower every total, so its card's changes are red ▼, as `StatRules.equip_change` gives them (the mockup's numbers came
   from an earlier save). The Healing Pills are 5, in the grid's third column, so the card is below them from the
   grid's left edge.
3. **"5 more spaces"** is a numeral: the string tables have no number words.
4. **Empty spaces and empty worn slots are plain**, with no cloud-seal motif, as on the Character page (the motif is the
   icon families' work).
5. **The empty hat slot glows jade** early, the self family's hint that the bag holds a piece to wear there (shared with
   the Character page); the gold dashes ring the slot a card is about. The bf2 save has no new item, so no jade dot.
6. **The hint** says "The Plain Straw Hat fits your empty hat slot" (a piece need not be new to fit), and hides while a
   card is open.
7. **The scroll thread** is the shared list's thin rail, not a glowing thread.
8. **A worn piece's card** (not drawn in the mockups) shows what it gives you: your totals as they stand and what the
   piece adds to each (the same rule, against the slot left empty), and Unequip.

Not shown in a still: the opening (the grid rises out of the cloud and the worn slots ride in along the orbit over 0.3
s; with Reduce motion on, the page only fades in over 0.2 s), which the `identity_suite` checks.
