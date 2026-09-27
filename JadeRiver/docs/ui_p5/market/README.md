# P5 · The Market family: Shop, Storage, Exchange, County Hall, Auction

Screenshots of the Market family built to its rows in `docs/page_identity.md` (8, 19, 33, 37, 38) and its family in §2
(brass fittings and paper price tags on trade timber and black lacquer), the Shop beside its mockup `17_shop`
(decisions 11, 14 and 24; `17_shop_buyback` is rejected). The other four have no mockup. They are 1280 × 720 as
captured, reduced to 256 colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of this build's own
valley_run checkpoints (run with `--cp=user://valley_cp/` under a scratch `XDG_DATA_HOME`): `ls6_end` (Sphere Lord 3 in
the Lantern Star Field, 41 of 55 in the Sunsteel Gourd), `bf5` and `bf2`. None uses the Max Tester save,
`--max-character` or `--unlock-all`. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `shop.png` | ls6_end | `--open-page=shop:lanternfall_goods --tap=396,350 --tap=1090,214 --tap=616,492 --tap=616,492` | Peddler Ning's stall: the awning and the lacquer sign, Ning behind her counter with her nameplate and her bark, ten wares on two shelves with their price tags in Sage Crystals, the Will Tempering Pill on the counter (3 for 18, 1,213 left after, Buy 3), the purses on the counter's front with the harbour's own coin ringed; beside it the bag in the gourd's heaven, each thing with its sale price, the Healing Pills picked with Sell 1 · 44 and All 4 · 176 |
| `compare_17_shop.png` | — | — | Mockup 17 above, `shop.png` below |
| `shop_buy_back.png` | ls6_end | `… --tap=1134,120 --tap=930,214` | The Buy back token lit: the same spaces show the last 20 sales with their buy-back prices, the Comet Iron picked with Buy back · 1,020 |
| `shop_early.png` | bf2 | `--open-page=shop:old_ma` | Old Ma's Store early: seven wares (the Bamboo Rod, Bonding Offering and Sealing Gourd locked, the River Mud flagged "today"), the counter's hint, one purse, a small gourd of 25 |
| `shop_text_large.png` | ls6_end | `--text-size=2 … --tap=396,350` | Settings › Text size › Large: the words grow in place; a ware's name keeps to two lines |
| `storage.png` | ls6_end | `--open-page=storage` | The chest's lid thrown open with the title's brass plate, 31 of 40 in its tray, what a Treasury would add on the chest's front; the gourd at the left in its heaven, lit from its mouth |
| `exchange.png` | ls6_end | `--open-page=exchange` | The Lantern Star Field's two pairs: their rates on the board's rail, three coin trays behind the bars, the three purses and a trade each way per pair |
| `exchange_valley.png` | bf5 | `--open-page=exchange` | The valley's one pair, two amounts each way |
| `county_jobs.png` | ls6_end | `--open-page=county --tap=548,420` | The bench: the favour banner with its tiers, three warrant sticks in the tube, the second drawn up and its warrant hung at the right, the relief box on the desk |
| `county_relief.png` | ls6_end | `--open-page=county --tap=1050,500` | The relief box tapped: the Relief Fund placard lit and the relief ledger with a Give for each size of gift |
| `auction.png` | ls6_end | `--open-page=auction --tap=560,580` | The stage: the Manual Pages brought up to the lit pedestal from the row of small pedestals, the lot board, your two numbered paddles with Bid 24 and Bid 32 |

## Against mockup 17

Matches: the red and cream awning with its scalloped valance and the name on a black lacquer sign; the merchant behind
her counter at the left with her nameplate (name and title) and her bark in a bubble; the wares five a shelf on two
plank shelves, each on a jade mat with a paper price tag and its name under it, the chosen one ringed in gold; the deal
on the counter plank (the ware on its cloth, its grade and how many you hold, what it does, − n + ×10, the total with
what is left after, Buy n); the purses on the counter's front with the shop's own coin first and ringed; "Prices in Sage
Crystals" and the dawn line; beside the stall the bag five across with each thing's sale price and "Cannot sell" where
it cannot, the chosen thing's Sell 1 and All n at its foot, "Sales pay a quarter, in Silver Taels"; buy-back as a small
control in the bag's header, with no column (decision 11).

Differences, each on purpose:

1. **"Your bag" is the gourd's heaven, not an indigo cloth on a crate** (decision 24: the bag beside another page reads
   as Bag concept B). It is a patch of the Bag's own sky, drawn from the Bag's shared pieces: the night, its stars, a
   far island, the sea of cloud at the foot, the floating tokens and the empty spaces the sky shows through.
2. **Buy-back** (decision 11, `17_shop_buyback` rejected): the header's "Buy back 20" token turns the same floating
   spaces to the last 20 sales, each with its buy-back price, and the foot to the chosen sale's Buy back; "Your bag"
   turns them back. No ledger drops over the bag.
3. **The title is the shop's full name** ("Peddler Ning's Silk and Sundries"); the nameplate carries her name and
   title as the data gives them ("Harbour peddler").
4. **The stock and numbers are this build's**: ls6_end holds 32 Will Tempering Pills and 4 Healing Pills; the harbour's
   stock today has the three Star Cores, not the Star Shard and Jelly Silk, so no ware is flagged "today" here
   (`shop_early.png` shows the flag).
5. **Prices under the bag's spaces** carry a small drawn tael mark, not the 16 px coin icon: icons draw only at whole
   scales of their art (the `ui_suite`).
6. **Everything that takes a tap or carries a word stays inside the full window** (64–1216), so the merchant's plate
   and bubble sit a little right of the mockup's, the purses start at 72 and the bag's grid at 812.

## The other four (no mockup; rows 19, 33, 37 and 38)

- **Storage**: as the row asks, the chest over the right two-thirds with its lid raised behind the grid (HD
  `storehouse_lid`, which swings up over 0.3 s as the page opens), the Treasury's spaces
  (`storage_slots_per_level` a level) as a second tray under a partition (the `identity_suite` shows it with a Treasury
  of level 1; `ls6_end` has no Treasury, so the front says what a Treasury would add), and the gourd's side at the left as
  the Bag's heaven with light from the gourd's mouth. A tap moves a thing across, arcing over (0.2 s).
- **Exchange**: the barred window in the centre with the changer's trays behind brass bars, the coin slot at its foot,
  the rate board above (the title board, each pair's rate on the rail under it), your purses on the near side and the
  trades under the slot. A window of the medium size, since a zone may trade two pairs.
- **County Hall**: the desk across the lower part with the tube of warrant sticks (red-tipped, gold once done, the
  progress on each), the gavel and seal, the relief box on the desk's right, which opens the relief ledger; the favour
  banner behind the desk at the left with the tiers written on its paper; the chosen warrant hung at the right to read,
  since the sticks are too narrow to carry a job's words. The desk is drawn by the page, not a pixel prop. The tabs are
  the hall's two red placards.
- **Auction**: the lot on a lit pedestal in the centre with its slot at 2×, its price, holder, time and the house premium
  on the lot board at the left, the other lots on small pedestals along the stage's front (a tap brings one up, sliding
  on over 0.3 s), and the two numbered bid paddles at the right. The paddles carry your bidder's number; the hammer is
  not drawn.

Not shown in a still: the openings (the awning drops and the bark pops, the lid swings up, a lot slides onto its
pedestal) and a thing's flight (a bought ware down to the counter, a stored thing across, coins through the slot); with
Reduce motion on the pages only fade in and nothing flies, which the `identity_suite` checks for every page.
