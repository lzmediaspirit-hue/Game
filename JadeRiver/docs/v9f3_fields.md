# V9f3 · Fields group: the room verticality catalogue rows

The Part 8 catalogue rows for the fields, marsh, gorge and cliff rooms, built in
`tools/data/catalogue_rows_fields.py`. Most rooms are now built whole to their row and checked by the room lint as
built. The Lower Pit, the Collapsed Tunnel and the Rapids Terraces gained pieces and are still finished by the
automatic verticality pass.

## What each room gained
- **Lower Pit** (200 · 100 · 0): falling rocks. Dust trickles from the pit wall, then a shadow marks where each rock
  will land. The rocks fall on the floor and the lower rungs of the ropes; the ledges are clear. The Riverstone vein
  is up on a ledge and the Jadeiron vein is down on the pit floor, as the row asks.
- **Collapsed Tunnel** (0 · rubble 40–80): a rubble heap (40 and 80) with the Spirit Stone shard vein behind it.
  There is also a cracked wall at the back that a Body of 20 breaks open. Behind it is a second shard seam that can
  be mined like any vein.
- **Marsh Edge** (0 · stilts 60–100): seven stilt decks across the reeds at 60, 80 and 100, ladders on every other
  deck, and reed bundles (40) as steps. Reed Frogs live on two of the decks and hop between them. Both Willow Moss
  patches grow up on the stilts.
- **Grey Pools** (0 · log rafts 30 · lily pads): a deep grey pool with a bay reaching toward the reeds.
  - A log raft drifts up and down the pool's east side.
  - A second raft sails a loop: it waits at the north bank, crosses the pool, and stops beside the moored raft in
    the middle. The chest is on the moored raft. No plain jump from any bank reaches it.
  - The lily pad still throws you to the optional 200 ledge.
  - The hamlet door opens at Heart Tempering 1 (see Grey Roofs below).
- **Hermit's Stilt House** (0 · house 120): a deck in front of the house at 120, level with the porch in the house's
  art, over the pond. A ladder goes up at the dry end, and you can also jump to the deck from the rock in the pond.
  The hermit's mat and cold tea are up there. The thatch above is an optional view. Hermit Yao himself waits at the
  foot of his ladder so his Qi Unfurling 5 and 8 quests are asked and handed in there.
- **Hamlet Square, Greyreed** (0 · grey roofs 88 / 176): a roof chain.
  - The chain runs from the grey hall (88) over the two homes (124 and 158) to the granary (176), each roof one
    jump from the next.
  - Ladders go up to the homes and the granary. The well is now a block (60) to hop from onto the hall.
  - A grey lantern sits on the hall roof and another on the granary roof. **Grey Roofs** now asks you to cleanse
    both, as well as clearing the Hollowed from the pools. A lit lantern takes each one's place.
  - The Grey Pools door into the hamlet now opens at Heart Tempering 1, the quest's own requirement. It used to
    wait until Grey Roofs was done, but Elder Gao gives that quest from inside the hamlet, so it could never start.
- **Thicket Heart** (0 · canopy 100 / 200): six canopy decks on vines across the thicket.
  - Two beast nests are up in the high canopy. From Heart Tempering 5 (Spirit Eggs) each gives one Spirit Egg,
    once.
  - The chest and the hundred-year Ember Pepper are on the 200 decks.
- **Falls Pool** (0 · rocks 60–100 · waterfall updraft): the pool is now water to walk and swim in. It has a
  shallow rim, deep water either side, and a shallow channel that leads behind the falls.
  - Stepping rocks (60 and 80) cross the pool.
  - The Mist Lotus grows on the high rock at 100.
  - A rock shelf at 100 leads up to the chest ledge, and the spray's updraft now lifts a glider past it.
- **Pilgrim Stairs** (0 → 80 → 160 → 240, depth stairs · shortcuts 100): the long stair.
  - Three stone flights climb into the mountain, with a landing after each at 80, 160 and 240. The side of the stair
    is a wall.
  - Stone Guardians keep each landing, and the road's own guardians still walk below.
  - Cliff shortcuts at 100 on either side, each with a boulder to step from, let a climber skip the first flight
    and landing. Cliff ledges at 200 lie beyond them.
- **Cleansing Summit** (0 · pillars 60 / 120): five stone pillars ring the rite circle, three at 60 and two at 120.
  The circle and the Heaven's Cleansing waves are unchanged.
- **Bend Shore** (0 · docks 60 · boats): three docks at 60 run out over the deep bend of the river.
  - A sampan is moored at the west dock. The hundred-year Riverreed Ginseng grows on its roof at 88, with a chest
    beside it.
  - A ferry boat plies the stretch between the middle and east docks. Stepping stones cross behind it and out past
    the east dock.
  - The fishing spot is at the end of the east dock.
- **Rapids Terraces** (0 · stepping stones 40–80 · current): a deep, fast stretch of the rapids with a current that
  pushes downstream. Stepping stones (40 to 80) cross it, and the salmon fishing spot is on the big stone in the
  middle.
- **Waterfall Cave** (0 · 100 · 200): wet ledges at 100 and 200 up the back of the cave, with ropes, and the falls'
  pool reaching in.
  - The Mist Lotus and the Spirit Stone shard vein grow on the 100 ledges. Lu's journal page and the chest are on
    the 200 ledge.
  - The reopening cache now stands inside the cave. Before, it stood outside the room.
- **Cliff Faces** (0 · ledges to 600 · updraft columns): the cliff ledges at 100, 200 and 300. Above them are
  isolated crags at 400, 500 and 600, each beside an updraft column that lifts you to it. The Cloudtop Orchid is on
  the 400 crag and a chest is on the 600 crag.
- **Sky Ledges** (400–900, flight only): six cloud ledges from 400 to 900, each over its own updraft column.
  - The lowest cloud drifts to and fro.
  - The Cloudtop Orchids (the rare one too) and two Cloudsteel veins are up on the clouds, and a chest is on the 900
    cloud.
  - The camera now rises with the clouds.

## Engine limits these rows work around
- **Objects do not ride movers.** A chest or herb on a moving raft or boat would hang in the air as the raft moved
  away. So the Grey Pools chest and the Bend Shore ginseng are on a moored raft and a moored sampan, and the moving
  rafts and the ferry carry the player to them.
- **Flight holds at 340** (`flight.ceiling`). The 400 to 900 ledges are reached by riding an updraft column: jump,
  fall or glide into one and it lifts you to its top. Flying into a column does not lift you past 340. A flier who
  takes off again above 340 is set back down to 340 (existing behaviour).
- **Ramps are drawn with the temple-stair art only.** The Lower Pit keeps its ropes, and its rows' "ramps" are not
  built.
- **Heaven's Cleansing has no ground shockwave.** The summit's pillars are solid cover: they block the Stone
  Guardians and arrows. The "shockwaves but not lightning" rule needs a shockwave attack in the event first.
