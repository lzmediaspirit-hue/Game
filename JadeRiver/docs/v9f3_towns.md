# V9f3 · Towns and sects: the rest of the room verticality catalogue (Part 8)

Built in `tools/data/catalogue_rows_towns.py`. The Market Street thief route is in `world.rooftop_routes()`.

### Willow Path
- **Willow Path West:** the three training stumps (60) and the two lifting stones (40) are now blocks you can stand
  on. Each block sits over its object and uses the same art, so you can still punch the stumps and lift the stones
  (body training, Dou's lesson). The fallen log stays a 60 block that you jump over.
- **Willow Path East:** Old Pan trades from the deck of his cart (60). Hop up to talk to him. The wheel ruts beside
  it are still there to read. A small roadside shrine stands further along the road, and its roof (88) is one jump
  up. The road's raised route of ledges and branches is still there.

### Stoneford
- **Market Street** (0 · awnings 88 · balconies 176 · rooftops 264 · bell tower 300):
  - The three shops keep their look, but their roofs are now at 176.
  - Timber galleries at 176 span the two gaps between the shops, behind the striped awnings (88).
  - Taller two-storey houses stand behind the shops, with rooftops at 264.
  - The bell tower's lookout is at 300. The notice-board copy is up there.
  - Ladders go to every shop roof, gallery and awning, and to the tower.
  - The Spirit Stone shard is in the gutter where the tea house roof meets the house behind it.
- **The daily rooftop thief** now runs over all of Market Street's tiers:
  - up the store's ladder, over the house behind it, down a gallery and an awning;
  - up the tea house and its upper house, then the same again at the warehouse;
  - a last hop onto the bell tower.
  - Every rise he takes is one jump (88, or 36 onto the tower) or the ladder he starts from, so you can follow him.
- **Fairground** (0 · tent tops 100 · stage 60):
  - Each recruiter tent has a stone stage (60) in front of it. Qing Lan and Mo Yun stand on the stage's front step
    (40), so you can still talk to them from the crowd below.
  - The tents' canopies are tops at 100, with a guy rope up each one.
  - Three Festival Lanterns hang over the great drum. They are too high for any jump; the drum's bounce reaches them.
    Each holds a packet of jasmine dew tea, once.

### The Jade Sect Academy
- **Gate Street:** the mission hall chest waits on the top of the roof chain (264), away from the thief's line.
- **Pavilion Rooftops:**
  - A willow moss pot grows on the pine branch (100).
  - The upper terrace (80) now reaches along to the 300 roof, and a ladder goes up from there.
  - The Retreat Rooms have a second door, on top of the 300 roof (inner disciples, as below). From inside the Retreat
    Rooms, a door leads back up to the roof.
- **East Terrace:**
  - A raised stone terrace (80) now stands behind the square, up depth stairs between two stone lanterns (blocks, 40).
  - The cave abodes are cut into the cliff behind the terrace. A personal disciple's door there (Spirit Awakening 5,
    after The Mentor's Gift, the same gate as the door on Elder Hu's peak) leads into your cave abode, which has a door
    back.
- **Alchemy Hall:** the furnace now stands on a stone platform (40). A mezzanine (88) up a ladder holds the recipe
  shelf, which you can read.
- **Weapon Hall and Forge (both sects):** the weapon racks are blocks you can climb (110). The training dummies stand
  on a raised stone sparring ring (40).
- **Herb Terraces (Jade):**
  - Three stone terraces step up the hillside at 40, 80 and 120, each up its own depth stairs.
  - Each terrace has one garden bed, and the willow moss and the ginseng grow on the terraces.
  - The weekly gathering trial works as before.
- **Elder Hu's Peak:**
  - Cliff ledges at 100, 200 and 300 stand against the cliff. Each has its own ladder, and each is one jump above the
    last.
  - A meditation rock on the 300 ledge gathers Qi while you sit by it (+0.5 Qi density, see the notes).

### The Cloud Sect Monastery
- **Cliff Stair:**
  - The depth stairs now climb to the 100 landing. Before, they sank below the court.
  - A rope goes from the landing up to the high ledge (200). The top ledge (300) is one jump from there, or up its own
    rope from the court.
  - The Cloud Library's upper gate is a door in the cliff on the top ledge. The library has a door back down to it,
    and its Sword Court door is unchanged.
  - The Cloud Steps' bell now hangs where you can see it.
- **Array Court:** a stone dais (40) holds the formation table and the Formation Elder. The formation nodes stand on
  low tables (blocks, 60) behind it. The garden beds and the way east are unchanged.

### The Hidden Vale
- **Back Mountain:** the timber decks are replaced by cliff ledges at 100, 200 and 300, with a rope to each. The
  Cloudtop Orchid grows on the top ledge and the Spirit Stone seam runs through the middle one.

### Notes (what the room data cannot do yet)
- **Heights snapped to the standard ones:** the row's stumps (50), fallen log (70) and merchant cart (70) all stand
  at 60, the nearest standard block top, which the room lint asks for.
- **Recruiters on the step:** the recruiters stand on their stage's 40 step, not the 60 deck. You talk to someone
  within 48 of your height, and the recruitment fair is talked to from the ground.
- **Meditation rock:** the only per-spot Qi bonus the engine has is a gathering-formation object (+0.5 density). On
  the peak (1.6) that makes 2.1, about ×1.3 rather than the row's ×1.5. An exact multiplier needs a per-object
  density factor.
- **Raised doors:** a portal has no altitude. The doors on the 300 roof, the 300 ledge and the 80 terrace are placed
  at the back of their tier, more than a portal's reach behind the ground's edge, so only someone up there can use
  them. Door art stands on the tier. The doors' name plates are drawn at ground level, so they sit hidden behind
  the building or cliff in front; you see Enter when you reach the door.
- **Sect Grounds and Vale Gate roofs by sect level (88 / 176):** the Sect Grounds' buildings appear as they are built,
  but a surface has no condition, so a roof would stand before its building does. The room keeps
  `vertical="grows"`. The Vale Gate keeps its 100 ledge.
- **Cave abodes on the Back Mountain ledges:** there is no cave-abode room for your own sect yet, so the ledges have
  no doors.
- **Objects on platforms** are depth-sorted by their plane position. Anything standing mid-way across a roof or
  ledge is drawn behind that surface's top face. So the new pieces on raised tiers stand near their back edge, or
  on blocks.
