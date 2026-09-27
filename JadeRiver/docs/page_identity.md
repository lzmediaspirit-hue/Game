# Page identity (P5)

Roadmap decision 14 (`docs/roadmap_master_ui.md` §6): each page is a thing from the world, with its own concept,
material and layout signature, and no two pages share one. Only the close button, the primary buttons, the text
tokens, the type scale and the 48 px targets stay shared. The user's words: "make sure that each page in the system
feels unique." Earlier notes point the same way (decisions 8 and 11): the Codex Collection reads as a book, the Old
Scrolls look like nothing else, the world map is a painted landscape, the Roll-Call is friendlier and more interactive,
and the character wears his gear on the Bag and Character pages.

This page catalogues every page in `scripts/ui/pages/` (44 files), the three shell screens (`scripts/shell/`) and the
HUD, one row each, ordered by how often a player opens them. It is the brief for P5a–P5c; each part still follows
U20's shape (concept, wireframe, states, navigation, annotated mockup, implementation notes).

Conventions:

- Paths are relative to `JadeRiver/`. Tokens are `UiKit`'s and the style guide's (`docs/ui_style_guide.md` §1 and §10).
  New drawn surfaces are `SURFACE` entries (§7 below); each is a mix of two existing tokens, so no new hue enters.
- **Art kinds.** *HD*: drawn by `tools/ui/build_ui_hd.py` as a nine-slice or a fixed asset, anti-aliased, like the
  frames (C7). *page.gd*: drawn in the page's `draw_page()` with `draw_rect`, `draw_arc`, `draw_polygon` and tokens,
  as the map scroll and the Go board are today. *Pixel*: original pixel art from the project's pipelines
  (`tools/icons` for 64 px objects and 32 px glyphs in Style A, `tools/props` and `tools/art` for props and creatures),
  drawn 1:1 or at an integer scale. *Existing*: art already in `art/`.
- **How often** is an estimate from the navigation map (`docs/ui_inventory.md` §3: taps from the HUD, whether the page
  opens by itself) and the daily loop (`docs/research/retention_notes.md`); there is no telemetry. Tiers: *constant*,
  *many a session*, *every session*, *most days*, *now and then*.
- **Status.** *Approved*: mockups 00–05. *Revised*: redrawn by another agent to decisions 11 and 14 and merged into
  this branch (06 Techniques, 13 Roll-Call, 16 World Map, 17 Shop, 18 Codex and Old Scrolls); their rows record those
  concepts as drawn, and the other rows were chosen to stay clear of them. *Drawn here*: a full mockup made with this
  page (§9). *Built*: converted in code by the pattern of §8. *Withdrawn*: overturned by a later decision. *Brief*: a row only, for P5.

---

## 1. What stays shared

Every page keeps these, whatever its concept:

| Shared | As |
|---|---|
| The close button | HD `close_button`, 52 px, at the window's top right (frame end − 72, y + 16); Esc and a tap outside the window close too (`page.gd:116`, `:393`, `:425`) |
| Primary buttons | HD `button_primary`, the bright jade face with the label inked by a 2 px `INK` outline (decision 10); secondary buttons `button_secondary`; disabled buttons carry the bronze lock and say why on a tap |
| Text tokens | `PAPER` primary, `MIST` secondary, `GOLD` headings, `PALE_GOLD` titles and names, `BRIGHT_JADE` positive, `RED_TEXT` negative, `WARNING`, `HOLLOW` disabled, `QI`, `SOUL_TEXT`; `PAPER_INK` on every light surface. The contrast rules of the style guide §1.4 hold on every new surface (§7 measures them) |
| The type scale | Cormorant 22–34 for display, Source Serif 4 at 14–22 for words, Pixelify for numerals of 20 px and more over the world; page titles inked like primary labels (decision 10); nothing under 14 px |
| 48 px targets | `Page.MIN_TAP`; page slots 76 px with the 64 px icon 1:1 and compact slots 48 px (decision 7); a row with a tap target is 56 px or more |

Behaviour that stays with them: the world dims behind a page (`DIM`); windows keep the standard rects of the style
guide §2.2, so a page's surface is drawn inside the same rect the frame used; tabs keep their behaviour (48 px, a
locked tab shows its lock and answers a tap with its reason) even where they take the page's form (ribbons in the
Codex, tools on the Workshop wall); locked things stay visible with the line that opens them; one selection style (the
glow); the confirm dialog and the toast.

What each page owns: the surface inside the window (it may replace the `major_window` frame), the title's mount (the
lettering is shared, the plaque is not), the form of its tabs, its dividers, backgrounds and motifs, and its motion.

---

## 2. Families

Related pages share a material; within a family no two share a layout. Each family's material is written in tokens.

| Family | Material | Pages | How their layouts differ |
|---|---|---|---|
| **The self** | Jade and gold: `SURFACE.space` (the jade-dark inside), `GOLD` lips, rings and cords, `SURFACE.gourd`, `SURFACE.cloth` | Bag, Character | A calabash between the figure's ring of slots and a hanging tag; a mat of vertical jade slips bound by two gold cords |
| **The way** | Stone, sky and starlight: `sky_top` / `sky_bottom`, `SURFACE.stone`, `GOLD` light | Cultivation, Breakthrough, Techniques, Revival, Fates | A stair; an archway; an element's chart between a seal rail and a dock; a single lamp; three sticks fanned from a cylinder |
| **The sect** | Red-lacquered pillars and dark timber: `SURFACE.lacquer`, `wood_dark`, `BRONZE`, red paper | Menu, Sect, Your Sect, Characters | Bays of hanging tablets; a hall in one-point perspective; a courtyard panorama; a handscroll unrolled across the page |
| **Bonds** | Whitewash and red thread: `SURFACE.plaster`, `RED` thread, `HEART` | Companions, Gift, Relations | Moon gates in a wall; a tray above the talk; a steelyard beam with threads |
| **Records** | Paper and ink: `scroll`, `SURFACE.almanac`, `PAPER_INK`, `BLOOD` seals | Dialogue, Quests, World map, Mail, Calendar, Notice Board, Codex (with Old Scrolls) | A strip under the scene; a board of pinned slips; a framed painting with a card; an envelope stack and an unfolded letter; a ruled almanac sheet; a collage of posters pasted on a wall; an open book with ribbons, and a black rubbing on a hanging scroll |
| **The post** | Bamboo, hemp and basketry: `SURFACE.bamboo`, `SURFACE.hemp`, `SURFACE.cloth`, `wood` | Roll-Call, Works, Welcome Back, Pouches | A row of hanging tablets over their baskets; an irregular curio shelf; a spiral coil beside a round tray; chalk outlines scattered on cloth |
| **The workshop** | Worked timber and tools: `wood`, `wood_dark`, `ember`, `SURFACE.soil` | Crafts, Workshop, Garden | A vessel centred over its fire; a tool wall above a bench seen from above; terraces stepping down the page |
| **The market** | Brass fittings and paper price tags on trade timber and black lacquer: `GOLD`, `scroll` tags, `wood`, `SURFACE.lacquer_black` | Shop, Storage, Exchange, County Hall, Auction | A stall under its awning with the bag on a crate; an open chest; a barred window; a desk with a warrant tube; a lit pedestal |
| **Beasts** | Straw and rough timber: `SURFACE.straw`, `wood`, `SURFACE.sand`, `SURFACE.clay` | Spirit Animals, Beast Arena, Core Exchange | A column of stall doors; an oval pit ringed with banners; an urn between a shelf and a spout |
| **Stone and bronze** | Cut stone and cast bronze: `SURFACE.stone`, `BRONZE`, `GOLD` | Teleport, Trial Tower, Mercy | Concentric compass rings; a tall pagoda in section; a sword planted upright |
| **Leisure arts** | The instrument's own wood: `board`, `board_line`, `wood`, `bridge`, `peg`, `hui`, `SURFACE.water` | Chess, Guqin, Fishing, Emotes | A square board; five horizontal strings; a cut through the river; a lit paper screen |
| **Shell** | The river at dusk and lantern light: the river backdrop, `SURFACE.river_lacquer`, `PALE_GOLD` glow | Title, Selection, Create Disciple, Settings | A cliff face with the name cut in it; skiffs at a jetty; cloths hung to dry on a pole; a column of drawers |

The HUD is context, not a family: it is the world's own frame (approved in 01 and 02).

---

## 3. The catalogue

Columns: **Job** in one line; **Concept**, the thing from the world; **Material, palette and surface art**, with the
kind of each piece of art in brackets; **Layout signature**, the shape that makes the page recognisable at a glance;
**Motif and motion**, with the reduce-motion fallback (§6); **Kept from the kit**, the shared parts of §1 that the page
uses beyond the five, so the pages still read as one game.

| # | Page | Job | Concept | Material, palette and surface art | Layout signature | Motif and motion | Kept from the kit |
|---|---|---|---|---|---|---|---|
| 1 | **HUD** (`hud.gd`) · constant · context · approved (01, 02) | Play, and reach every page in one tap | Jade discs set in gold, worn on the thumbs | The `hud_ring` disc (`DEEP_TEAL` to `INK`) in a `GOLD` rim; `PLATE` under words over the world; the HP, Qi and Soul fills (HD `hud_ring`, P4 §5; Style A glyphs at 32, pixel) | Two arcs of rings round the 132 px attack ring at the lower right; the name and bars at the upper left; the minimap and four rings at the upper right; the progress edge along the foot | A held toggle or a reached bottleneck lights its ring with a halo; techniques fold into four beads at rest. Reduce: the halo is steady, the fold is a 0.2 s fade | The HUD kit (style guide §9) |
| 2 | **Dialogue** (`dialogue_page.gd`) · many a session · Records · 21, 21_gift | Talk, choose, take a quest, give a gift | Rice paper laid under the scene, a storyteller's caption | `dialogue_box` paper with `PAPER_INK` words; the speaker on a jade plaque; choices on jade tablets (existing kit); the portrait from the speaker's own layers (existing) | Frameless: one full-width paper strip along the foot (48, 464, 1184 × 232), the portrait framed at its left, words in the middle, choices stacked at its right; a quest offer pinned above it as a small scroll; the world stays in view | Words are written in and a tap finishes them; an offer unrolls downward (0.2 s). Reduce: the offer fades; the reveal stays, since a tap ends it | `dialogue_box`, `portrait_frame`, secondary buttons, 76 px slots for gifts |
| 3 | **Bag** (`inventory_page.gd`) · many a session · The self · **built** as concept B (07_bag_b, _card, _pill, 08_bag_b_empty; decisions 8, 15, 24; the gourd of 07 v2 and 08 v2 and concepts A and C stay as the record) | What you carry and wear; equip, use, lock, discard, sort; the key pouch | The heaven in the gourd: no gourd is drawn, the page is the world inside the character's Spirit Gourd, a night sky over a sea of cloud, and a bigger gourd is a wider heaven | The night deepening from `INK` to `SURFACE.space` and `SURFACE.sky`, the sea of cloud in `SURFACE.silk` and `SURFACE.sea`; stars, the light from the gourd's mouth, far islands with pines and a pavilion, the figure's island with a lit `JADE` top and the `GOLD` orbit (page.gd, from a steady scatter: more stars and islands with each gourd, the light once it holds 40). Art: the floating tokens `sky_token` and the item card `sky_card` (HD nine-slices); the live figure (Avatar at 2.5, drawn by the page under its card) | `open_sky_grid_orbit`. No frame: the sky fills the screen. The figure on its island at the left, the eight worn slots riding a gold orbit round it (`CharacterPage.draw_worn`); one grid ten across floating in the sky, five rows in view and the next fading into the cloud, the next gourd's spaces locked at its end; the Spirit Gourd and Key Pouch tokens and the purses along the top, the kinds and Sort under them; "Space n / m" and the next gourd under the grid, the hint in the open sky while the gourd is small; a tapped thing's small card beside its space (what wearing a piece would make of your own totals, `StatRules.equip_change`), the rest of its actions under "···" | The grid rises out of the cloud and the worn slots ride in along the orbit on opening (0.3 s). Reduce: fade in | 76 px slots with grade rims and gems, primary and secondary buttons, the purse pills |
| 4 | **Menu** (`menu_page.gd`, the hub) · many a session · The sect · approved (03) | Reach every system; see what waits in each | The sect's hall of hanging plaques | Teal lacquer tablets (`minor_panel` faces) on `GOLD` cords between red-lacquer pillars (`SURFACE.lacquer`, page.gd); bay plaques (existing) | Five bays under five plaques, tablets hung down each bay on cords; the character line and purses at the foot | Tablets settle with one sway on opening (0.25 s); a ready seal is pressed on (0.15 s). Reduce: fade; the seal simply appears | Badges (count, ready seal, new) |
| 5 | **Cultivation** (`cultivation_page.gd`) · many a session · The way · approved (04) | See the whole climb and this realm's nine steps; meditate; reach the gate | The mountain ascent | The night mountain (`sky_top` / `sky_bottom`); steps in the band colours (`JADE_SHADOW`, `JADE`, `BRONZE`, `GOLD`); the realm path as ink dots with `GOLD` waystations (page.gd); the figure seated (Avatar `meditate`) | The nine-step stair in the centre, the nineteen realms winding up the left, the next step's unlocks and the gate at the right; eight tabs | At a minor breakthrough the figure climbs one step (0.4 s); the bottleneck riser glows. Reduce: the step lights, no climb | Stage bands, unlock chips, `bar_shell` |
| 6 | **Quests** (`quest_page.gd`) · many a session · Records · **drawn here** (12 v2) | What now: the story, today's round, what is near, and where the tracked quest leads | The sect's mission board: paper slips pinned to timber | The board `wood_dark` with grain lines every 3 px (page.gd); slips in `scroll` paper with `PAPER_INK` words (HD nine-slice `paper_slip`, torn top); the main quest's slip headed in `SURFACE.cinnabar` with a gold edge; bronze pins (pixel, 32 px Style A glyph); the done stamp in `BLOOD` (pixel) | A timber board filling the left two-thirds with slips pinned in clusters: the story's slip top-left with a red head; the day's missions as a row of small slips; the day's chests on a red cord along the board's foot; side quests stacked under three region nameboards. The chosen slip is taken down and held large at the right, with its route drawn across it and Go | A tapped slip is unpinned and lifts to the reading place (0.2 s); a finished slip is stamped. Reduce: the reading slip fades in; the stamp appears | 76 and 48 px slots for rewards, `bar_shell` with reward stops, purse pills |
| 7 | **World map** (`map_page.gd`) · many a session · Records · **built** (16, 16_resources; decisions 11, 17, 25) | Where everything is; where the tracked quest leads; where herbs, ores and fish are; travel | The framed painting of the zone: a pixel landscape seen from above at an angle, hung in a dark frame with the sect's pennant | The painted valley (pixel, `tools/ui/build_valley_map.py`, with a close-up of each area for the card); the Azure Expanse and the Lantern Star Field drawn from tokens in the same manner until they have paintings (page.gd); glowing nodes in `JADE` and `GOLD` on dotted routes; name plates of ink with a fine gold edge; a timber frame (`SURFACE.soil`) with a bronze fillet and cloud-scroll corners, the zone tags hung from its top rail; the lacquer card; all page.gd | The painting fills the screen edge to edge inside its frame (`Page.WINDOW_SCREEN`, the one page that does); the title plate and pennant at the upper left, the zone tags and the Heaven Ranking along the top, the area card standing at the right with its picture and Track Route, the Areas, Resources and Objectives tablets and the legend along the foot (decision 11); one layout pass places every plate and mark so none touches another or a node (decision 17); the Heaven Ranking is a lacquer board over the dimmed painting | The chosen area's way lights dot by dot (0.3 s); the card slides in from the frame's edge (0.2 s); a live mark's glow breathes. Reduce: the way shows lit, the card fades, the glow is steady | Primary and secondary buttons, legend marks |
| 8 | **Shop** (`shop_page.gd`) · many a session · The market · revised (17, 17_buyback) | Buy, sell, buy back | The merchant's own street stall: Peddler Ning's Silk and Sundries | A red and cream striped awning with the name on a lacquer sign; plank shelves in `wood` with each ware on a jade mat and a paper price tag; the merchant standing behind her counter (her own layers); the player's bag untied on a crate beside the stall as a quilted indigo bundle | The stall fills the left two-thirds under its awning (wares on two shelves, the merchant at the left with her bark in a speech bubble, the deal laid on the counter plank, the purses on the counter's front); the bag lies open on a crate at the right with its sale prices; buy-back drops as a ledger page from a small control (decision 11) | A bought ware slides down onto the counter (0.25 s); the bark bubble pops. Reduce: fade; the bubble appears | 76 px slots, purse pills, quantity buttons |
| 9 | **Breakthrough** (`breakthrough_page.gd`) · many a session (nine steps a realm) · The way · brief | See what the next step asks, fix it, add supports, see the odds, break through | The heaven gate at the top of the stair: a stone archway whose doors open when you break through | `SURFACE.stone` with `GOLD` leaf on its plaque; the sky behind in `sky_top` / `sky_bottom`; requirement tablets on `RED` cords; three jade offering dishes on the step. Art: the archway (pixel prop, about 280 × 240 art px at 2×); the sky and the tablets (page.gd) | One symmetric archway centred on the page: the next realm's name on its plaque; each requirement hangs from the beam as a tablet, lit gold when met, dark with its Go when not; three offering dishes on the step hold the support items; the chance and the risk word written on the two pillars; Break Through on the threshold | A met requirement's tablet lights (0.2 s); Break Through opens the doors (0.5 s) into moment 05. Reduce: tablets light without the glow ramp; the doors cross-fade | Primary button, 76 px slots for supports, requirement dots |
| 10 | **Title** (`shell_screens.gd` TitleScreen) · every session · Shell · brief | Continue, begin, settings, quit | The game's name cut into the cliff above the river | The river backdrop (existing); a cliff face (pixel, a backdrop layer); the name carved in `PALE_GOLD` with an `INK` bevel (page.gd) | The name cut large into a cliff face in the upper middle; the three buttons stacked on a stone ledge under it; the river across the foot | Mist drifts over the river; the carving catches the light once at launch (0.6 s). Reduce: still mist, no glint | Primary and secondary buttons |
| 11 | **Selection** (`shell_screens.gd` selection) · every session · Shell · brief | Pick who enters the world; add or delete | Skiffs moored at the jetty at dusk, one disciple standing in each | The river (existing), the jetty in `wood`, each skiff's prow lantern in `PALE_GOLD` glow; skiffs and jetty (pixel props); figures (Avatar) | Four skiffs side by side along a jetty in the lower half, a disciple standing in each with a name lantern on the prow; empty moorings (a coiled rope, "a new disciple") for open slots; page arrows at the jetty's ends; Enter World at its head | The chosen skiff rocks once and its lantern lights; Enter World casts it off toward the viewer (0.5 s). Reduce: the lantern lights; a fade on entering | Primary and secondary buttons |
| 12 | **Welcome Back** (`welcome_page.gd`) · every session · The post · brief | What the time away earned; to the Storehouse or kept | The incense coil that burned while you were away, and the haul in a round bamboo winnowing tray | The coil burnt to `HOLLOW` ash with an `ember` tip, the unburnt rest in `BRONZE`, on a bronze stand (page.gd); the tray a woven disc in `SURFACE.bamboo` with a bound rim (page.gd) | A spiral on the left whose burnt length is the time away out of the 12-hour cap, the glowing tip now and the unburnt rest what more the cap would have held; the haul heaped in the round tray at the right; the two choices under the tray | The ember runs to its mark (0.6 s, a tap skips); goods drop into the tray one after another (0.05 s apart). Reduce: the coil is drawn at its mark; goods appear together | 76 px slots, primary and secondary buttons |
| 13 | **Character** (`character_page.gd`) · every session · The self · **built** (09 v2; titles as honours, decision 16) | Who the character is: what they wear, their numbers, titles, origin and ties | The jade-slip record: the cultivator's life kept on bound jade slips, as a sect keeps its disciples' records | Slips in dark jade (`SURFACE.cloth` with `JADE_SHADOW` edges) bound by two `GOLD` cords; the figure's slips washed lighter, as if painted; the register written across the rest; title plaques in `SURFACE.lacquer`. Art: the slip mat (page.gd, vertical slats every 40 px with rounded ends); the cords and knots (page.gd); the figure (Avatar at 2.5) | The whole window is one mat of vertical jade slips bound by a gold cord near the top and the foot, the title tag knotted to the upper cord; the figure stands full-length on the first slips with the eight worn slots down the slips on either side; the register (pools, offence and defence in ruled columns) written across the middle slips; the titles as small lacquer plaques at the foot; the tabs are jade tags on the upper cord | The slips fan open from a bundle on opening (0.35 s); equipping re-inks the figure (0.2 s). Reduce: fade in | 76 px slots, `bar_shell` pools, secondary buttons |
| 14 | **Roll-Call** (`posts_page.gd`) · every session · The post · revised (13, 13_first) | Every character's post: yield, pouch, settle; the Storehouse, Bench and Vows | The sect's duty board: a name tablet for each character hung on the peg rail, their catch in a basket beneath | Wooden tablets on hemp cords hung from a peg rail; each tablet's arched window holds the character's own figure posed by state (standing while played, seated when idle, at work while filling) and a state band; beneath each its container (herb basket, net bag, cicada cage); the Storehouse a small cabinet under a tiled roof; the Bench a craft table | A row of four tall hanging tablets across the upper left with their baskets on a shelf below and a Settle under each, soonest full first; Settle all, the Storehouse cabinet and the Bench stacked at the right; Crafts and Vows as two small tags top left; a tapped tablet turns over to show its post's numbers | A tablet turns over on a tap (0.25 s); settling pours the catch toward the Storehouse (0.4 s). Reduce: the tablet cross-fades; counts change without the pour | Primary button, `bar_shell` with stops, 76 px slots |
| 15 | **Techniques** (`techniques_page.gd`) · every session · The way · revised (06_tree, 06_tree_learned, 06_lost_unknown; decisions 18 and 19) | Learn, realise and slot techniques by element; lost arts; secret arts; the loadout | Each element's tree read one family at a time as a tall tree of illustrated cards (a picture of the art in action, its name, its state) joined by arrows, laid on that element's own chart (the Water tab a tide chart's soundings and currents; Wood a living tree, Fire a forge-lit sky, Earth a cliff in section, Metal the back of a bronze mirror, Wind kite paper, Thunder a storm sky of drums, Soul a lantern lake, Formless an ensō, Space an armillary sphere, Time a water clock); Lost Arts an explorer's album, one leaf per act, found arts pasted in and the rest sealed alike; Secret Arts a practice mat of footwork | A dark lacquer rail across the top with the element seals, three jade-teal panels with gold fittings between (the chooser, the tree, the reading) and the loadout dock across the foot; the card pictures composed from the sprite layers and the emblem grammar (`tools/icons/study/technique_cards.py`); Style A emblems | The element seals along the top and the loadout dock along the foot stay put on every tab; the family chooser at the left with each family's Dao as its mastery bar and the character under it; the tree in the middle (a line of passages, each ring's orthodox art on it and its path art beside it, the act's keystone at the foot); the chosen art's reading at the right (a large picture, prerequisites with ticks and crosses, the cost, Learn) | Changing tab redraws the surface under a fixed rail and dock (0.3 s); a learned art lights along its route (0.4 s). Reduce: the surface cross-fades; the route shows lit | 52 px dock slots, 76 px card pictures, primary button with inked label |
| 16 | **Spirit Animals** (`pets_page.gd`) · every session · Beasts · brief (10 exists) | Care for, grow, breed and arm the animals | The beast stable: stalls with half-doors, each animal looking over its door | Stall timber `wood` with `SURFACE.straw` bedding; name boards; the yard in `SURFACE.soil`. Art: stall doors (pixel prop); creatures (existing sheets); straw (page.gd) | A column of stall half-doors down the left, each with its animal's head over the door and a name board; the chosen animal out in the yard at large scale with its growth path as stepping stones and its bond as hearts on its collar; care, gear and the nest on the tack wall at the right | Animals idle in their stalls; choosing one opens its door and it walks out (existing walk frames, 0.4 s). Reduce: the yard figure changes with a fade | 76 px slots for gear, `bar_shell` with stops |
| 17 | **Mail** (`mail_page.gd`) · every session · Records · **drawn here** (22) | Read letters; claim what they carry | The letter case: sealed envelopes in a stack, and the open letter unfolded on the desk with its parcel tied on | Envelopes in `scroll` paper with a `BLOOD` wax seal while unread; the letter with its two fold creases; `SURFACE.hemp` string; the desk `wood_dark`. Art: `envelope` and `letter_sheet` (HD nine-slices with crease shading); the wax seal (pixel, 32 px); string (page.gd) | A fanned stack of envelopes down the left, newest on top, unread ones sealed, those that carry something tied with string; the open letter large on the right, unfolded, with the sender's line, the words in ink and the sender's name at its foot; what it carries tied beneath it as a parcel, Claim as untying | Choosing an envelope slides it out and the letter unfolds (0.3 s, the two creases opening); a claim unties the string and the goods fly to the bag chip (0.3 s). Reduce: the letter fades in; goods are counted without the flight | 76 px slots, purse pills, primary and secondary buttons |
| 18 | **Crafts** (`crafts_page.gd`) · every session · The workshop · brief (15 exists) | Cook, refine, forge, inscribe, trace, chart, build | The hearth: each trade's vessel on its fire (pot, cauldron, anvil, plate, paper, chart, hull) | Hearth brick `SURFACE.stone` with `ember` fire; the vessel's metal. Art: stations (existing props); fire (existing FX); the step strip (page.gd) | The station centred over its fire with the ingredients on its rim; the steps as a strip across the top; the controls at the right change with the step and nothing else moves | Fire flickers; a finished craft lifts out in a puff (0.4 s). Reduce: no puff, the product appears | 76 and 48 px slots, primary button, heat gauge |
| 19 | **Storage** (`storage_page.gd`) · every session · The market · brief | Move things between your gourd and the account's chest | The storehouse chest: an iron-bound camphor chest with its lid thrown open, beside your gourd's mouth | Camphor `wood` with `BRONZE` bands, a `SURFACE.lacquer` lining inside the lid. Art: `storehouse_chest` (HD fixed asset, the raised lid in perspective); grids (kit) | The open chest over the right two-thirds, its lid raised behind the grid, the Treasury's added rows as a second tray; your gourd's mouth at the left with its grid; a tap moves a thing across | The lid swings open on opening (0.3 s); a moved item arcs across (0.2 s). Reduce: fade; items move without the arc | 76 px slots |
| 20 | **Teleport** (`teleport_page.gd`) · every session · Stone and bronze · brief | Travel to a known stone for a shard | The geomancer's compass: the stones placed on its rings by their bearing from here | A `BRONZE` disc with a `SURFACE.lacquer_black` face, rings ruled in `GOLD`, names in `PALE_GOLD` (page.gd) | A large round compass left of centre: its needle points to the stone you touched; the known stones sit on the outer ring at their bearings; the chosen stone's line and cost at the right | The needle swings to the chosen stone (0.4 s, damped); Teleport spins the rings once (0.5 s) into the fade. Reduce: the needle snaps; fade | Primary button, purse pill |
| 21 | **Notice Board** (`notice_page.gd`) · most days · Records · brief | Take bounties; read the town's requests and sightings | The town wall where the wanted posters are pasted, one over another | Grey brick (`SURFACE.stone` with mortar lines, page.gd); posters in `scroll` paper with `PAPER_INK`, the reward stamped in `BLOOD`, older posters torn and faded beneath; paste stains. Art: `poster` (HD nine-slice, curling and torn corners); portraits from the target's sprite | A collage: the posters pasted over each other at different angles across the wall, the newest largest and on top, torn strips of old ones showing between; the chosen poster's Take strip at its foot; the Board tab's requests and sightings as small handbills in one corner | Taking a bounty tears its strip off (0.25 s); a new poster is slapped on with its paste (0.2 s). Reduce: fades | Primary button |
| 22 | **Calendar** (`calendar_page.gd`) · most days · Records · **decided: the first mockup (19)**, not the almanac (19 v2), by decision 22; the almanac below stays as the record, and the Calendar's layout is 19's: the four seasons as a strip, the week as seven day columns with the events on their days, the Beast Tide across the week, the chosen event with Go there and the weather | When and where: the season, the week's events, the tide, the weather | The yellow almanac: one sheet for the week, ruled in red | `SURFACE.almanac` paper with `PAPER_INK` words; `SURFACE.cinnabar` header band and `BLOOD` rules and seals; the season wheel (page.gd, all of it) | One broad almanac sheet: a red header with the season wheel (four quarters, the current one lit with its time left) and today's day; seven day columns ruled in red with today's first and shaded; each world event a red seal on its day; the Beast Tide a dark ribbon across the week; the weather as the last row; the chosen event's slip with Go there in the right margin | Next week flips the sheet up (0.3 s); a live event's seal glows. Reduce: the sheet cross-fades; the seal is steady | Primary button |
| 23 | **Works** (`works_page.gd`) · most days · The post · **drawn here** (14 v2; its objects redrawn large in 14 v3, decision 21) | Build the account's works that serve every post | The curio cabinet: seven works as seven objects in the compartments of an irregular bamboo shelf | `SURFACE.bamboo` lattice (page.gd); each work an object (pixel, Style A, drawn at 64 and natively at 128 in the cabinet: the manual, the seal, the stele, the favour, the furnace, the flag, the mirror; `tools/icons/study/works_objects.py`); hanging labels in `SURFACE.hemp`; the tray `wood_dark` | An irregular lattice shelf across the top (compartments of different sizes, one work each, its state on a hanging label, locked ones dark behind a lattice screen with the quest and giver that open them); the chosen work's list on the tray below; the account's totals as the cabinet's inventory slip at the right | The chosen object lifts out of its compartment onto the tray (0.25 s); inscribing presses a seal mark (0.2 s). Reduce: the tray fades; the mark appears | Primary button, 48 px compact slots for costs |
| 24 | **Your Sect** (`your_sect_page.gd`) · most days · The sect · brief (11 exists) | Found and raise the sect; disciples, expeditions, territory | The courtyard under construction: the grounds as they stand, raised halls solid and the rest as scaffold outlines | The room's own art (existing backdrop layers); scaffolds in dashed `BRONZE` (page.gd); disciples (Avatar) | A wide panorama of the grounds across the top half, buildings where the room places them, disciples in the yard and candidates at the gate; the sect level bar with its stops under it; the chosen building, the disciples and beyond-the-walls cards along the foot | Raising a building draws its scaffold solid from the ground up (0.5 s); disciples idle. Reduce: the building appears | Primary button, `bar_shell` with stops |
| 25 | **Sect** (`training_sect_page.gd`) · most days · The sect · brief | Rank, contribution, promotion trials, missions, the sect shop; the role's tree | The Sect Hall's seats seen from its door | Receding floor in `wood_dark`, red pillars `SURFACE.lacquer`, cushions coloured by rank from tokens (`HOLLOW`, `JADE`, `GOLD`, `PALE_GOLD`), your seat lit. Art: the hall interior (pixel plate); seats (page.gd) | One-point perspective: the floor recedes to the master's dais at the top centre; ranks are rows of seats, nearer rows lower; your seat marked, the next rank's row lit with its price and gain; Missions and the Sect Shop as the hall's side doors; the Role tab turns to the teaching boards on the side walls | Promotion walks your seat forward one row (0.4 s). Reduce: the seat appears in its row | Primary button |
| 26 | **Codex** (`codex_page.gd`) · most days · Records · revised (18, 18_scrolls) | Look things up; fill the collection; achievements, paths above, seasons; the old scrolls | The field book: a bound book open on the reading desk, its entries drawn on squared paper and taped in. The Old Scrolls tab: a stone rubbing mounted as a hanging scroll on the reading-room wall | Book paper `scroll` with grain and foxing, a gutter shadow and the page block's edges; silk ribbon bookmarks in token colours; specimen drawings on squared paper with tape; ink bars with their stops. Old Scrolls: black rubbing ink (`SURFACE.rubbing`) with the carved rungs standing pale, the stone's chips and crack recorded, bare paper below where the rubbing has not reached, an ink pad; the mount's brocade and rods; a vermilion gloss; the chosen rung's note pinned beside it | A two-page spread with the sections as ribbons standing out of the top edge (the open one lying into the spread) and curled page corners as the navigation. Old Scrolls: the mounted rubbing fills the left two-thirds, black above and bare paper below, the gloss down its right margin, the note pinned at the right; the only black-on-light-inverted surface in the game | Pages turn with a curl (0.35 s); the rubbing darkens a rung as if dabbed when a realm is reached (0.4 s). Reduce: cross-fade | `bar_shell` with stops |
| 27 | **Companions** (`companions_page.gd`) · most days · Bonds · brief | Choose who walks beside you; hearts, gifts, duels, bonds | Moon gates in a whitewashed garden wall, a friend standing in each | `SURFACE.plaster` wall under `JADE_SHADOW` tiles; hearts as knots on a `RED` thread (page.gd); companions (Avatar) | A white wall with a row of round moon gates, a companion standing full-length in each; the two beside you have lanterns lit over their gates; each gate's hearts as knots on the red thread beneath it; the chosen friend's actions under their gate | Choosing a friend lights their lantern (0.2 s); a new heart ties a knot (0.3 s). Reduce: lantern lights; the knot appears | Primary and secondary buttons |
| 28 | **Gift** (`gift_page.gd`) · most days · Bonds · 21_gift | Give one gift a day and see the heart move | A red-lacquered gift tray held out with both hands | `SURFACE.lacquer` tray with a `GOLD` rim and compartments (HD nine-slice `gift_tray`); the liked gift marked with a `HEART` tag | A long shallow tray of compartments above the talk, the liked gift tagged; the heart bar under the speaker's words | The chosen gift lifts from the tray toward the speaker (0.3 s); the heart bar fills. Reduce: fade; the bar is set | 76 px slots, primary button |
| 29 | **Garden** (`garden_page.gd`) · most days · The workshop · brief | Plant, water, feed and harvest beds; dry and steep on racks | Terraced herb beds on the hillside, seen from above | `SURFACE.soil` beds with `SURFACE.stone` terrace edges; herbs growing in four stages (pixel, from the herb icons); grade stakes; the tool basket (pixel) | Terraces stepping down the page, each bed a plot with its herb drawn at its stage and its grade on a stake; the water, Spirit Soil and dew in a basket at the top; the Racks tab as drying racks with trays | Watering darkens the soil (0.3 s); a harvested herb pops into the basket. Reduce: the soil changes at once, no pop | 76 px slots, primary button |
| 30 | **Workshop** (`workshop_page.gd`) · most days · The workshop · brief | Formations, appraisal, the infirmary, puppets, restoration, teaching | The artisan's bench with its tool wall | A pegboard in `wood` with each tool's painted outline in `INK` at 40%; the bench top `wood_dark` seen from above. Art: six tools (pixel, Style A 64: compass, loupe, needle roll, chisel, brush, pointer); the wall (page.gd) | A tool wall across the top where each tab is a hung tool with its outline behind it; the bench top below, seen from above, with the job laid on it (the blueprint, the item under the loupe, the patient's card, the puppet frame, the torn manual, the disciple's slate) | Choosing a tab takes the tool off its hook, its outline stays (0.2 s), and lays it on the bench. Reduce: fade | 76 px slots, primary button |
| 31 | **Fishing** (`fishing_page.gd`) · most days · Leisure arts · brief | Cast, wait, strike, keep the line in the band | The river in section from the bank | `SURFACE.water` with light bands, the bank in `SURFACE.soil`, a bamboo rod; the tension band in `GOLD` on the rod's arc (page.gd); fish (existing icons) | A vertical cut through the water: the surface near the top with the float, the fish below, the rod's arc from the bank at the left; the band of good tension marked on the arc | Ripples at the float; the bite dips it (the game's own cue); the rod bends with tension. Reduce: ripples still; the dip and the bend stay, since they are the game | Primary and secondary buttons |
| 32 | **Characters** (`characters_page.gd`) · most days · The sect · brief | See every character; set this one's idle task; switch | The sect's roster handscroll: every disciple of the account painted in one procession along a scroll unrolled from left to right | A handscroll in `scroll` paper with `SURFACE.silk` borders and a `wood_dark` roller; each disciple painted standing (the figure from its layers, Avatar idle, at 2×) with a column of name, realm and idle task in `PAPER_INK`; the idle task as a small prop at their feet (pixel, from the HUD glyphs); the still-rolled end holds the slots not yet open | One long horizontal band across the middle of the window: the scroll unrolled from the left edge, the disciples in a line along it, an open slot as a blank stretch of paper ("a new disciple"), and the tight roll at the right end whose thickness shows how many slots are still to come, each with its gate on a tag hanging from the roll; the chosen disciple's idle tasks and Switch under the scroll | The scroll unrolls from the left on opening (0.35 s); a newly opened slot unrolls one more stretch. Reduce: fade | Primary and secondary buttons |
| 33 | **Exchange** (`exchange_page.gd`) · most days · The market · brief | Trade a zone's everyday currency with the tier below | The money-changer's barred window | `SURFACE.lacquer_black` counter, `GOLD` brass bars, coin trays; the rate on a board (page.gd); coins (existing currency icons) | A barred window in the centre with a coin slot at its foot; your purse on the near side, the changer's trays behind the bars; the rate board above; the two trades under the slot | Coins slide through the slot (0.25 s). Reduce: the counts change | Purse pills, primary buttons |
| 34 | **Core Exchange** (`core_exchange_page.gd`) · most days · Beasts · brief | Sell beast cores by tier for Spirit Stones; rest the animals | The Beast Hall's core urn and its tally stick | A glazed urn in `SURFACE.clay` (no words on it); a bamboo tally with 60 notches; a straw bed (`SURFACE.straw`). Art: the urn (pixel prop); tally and bed (page.gd); cores (existing icons) | A big urn in the centre; your cores on a shelf at its left by tier; the stones spilling from its spout at the right; the day's tally across the foot; the straw bed corner for resting the animals | A sold core drops into the urn and stones clink out (0.3 s); a notch darkens. Reduce: counts change | 48 px compact slots, primary button |
| 35 | **Trial Tower** (`tower_page.gd`) · most days · Stone and bronze · brief | Climb thirty floors; sweep the cleared ones | The pagoda in section | Stone floors in `SURFACE.stone`, eaves in `JADE_SHADOW` tiles, a `GOLD` lamp on every cleared floor. Art: eave tiles (pixel); floors (page.gd) | A tall narrow pagoda cut open down the left, thirty floors stacked with eaves between, cleared floors lit, the next dark with its lock; the chosen floor's rule, foes and Climb at the right; Sweep at the pagoda's door | The view climbs the tower to the chosen floor (a scroll); a cleared floor's lamp lights. Reduce: the view jumps; the lamp is lit | Primary button |
| 36 | **Beast Arena** (`beast_arena_page.gd`) · most days · Beasts · brief | Challenge the tamer above you; the week's rank pays | The arena pit seen from the stands, ringed with the ten tamers' banners | `SURFACE.sand` pit with a `wood` fence; banners in token colours (page.gd); animals (existing sheets) | An oval sand pit filling the centre with ten banners planted round its rim in rank order, rank 1 at the top, yours and the one you may challenge lit; the last fight replayed inside the pit as two draining bars between the two animals; 1v1 and 3v3 at the pit's gate | The replay's bars drain; a challenge raises your banner (0.3 s). Reduce: the bars show their end values | Primary buttons, `bar_shell` |
| 37 | **County Hall** (`county_page.gd`) · most days · The market · brief | County favour; today's three jobs; the relief fund | The magistrate's bench: the high desk with its warrant tube, gavel and seal | `SURFACE.lacquer_black` desk, warrant sticks tipped in `RED`, the favour banner in `SURFACE.cinnabar`. Art: desk (pixel prop); sticks, banner (page.gd) | The desk across the lower half with a tube holding three tall warrant sticks (today's jobs, each drawn out to read); the county favour tiers as a banner hanging behind the desk at the left; the relief box on the desk's right | A warrant stick slides up out of the tube (0.2 s); the gavel strikes on a finished job. Reduce: fade | Primary button, purse pill |
| 38 | **Auction** (`auction_page.gd`) · now and then · The market · brief | Bid on today's lots; won lots come by mail | The auction stage: the lot on a lit pedestal, the next lots waiting | Stage `SURFACE.lacquer_black`, a `PALE_GOLD` light cone, numbered bid paddles (page.gd) | A pedestal lit from above in the centre with the lot on it (a slot at 2×), its price, holder and time; the other lots on small pedestals along the stage's front; the two bid paddles at the right | The next lot slides onto the pedestal (0.3 s); the hammer. Reduce: fade | 76 px slots, primary button |
| 39 | **Revival** (`revival_page.gd`) · now and then · The way · brief (20 exists) | Return to the shrine or revive here; what was lost and kept | The life lamp at the shrine, burning low | A dark stone niche (`SURFACE.stone`), a bronze lamp (pixel prop) with an `ember` flame and its glow (page.gd) | One lamp in the centre of a dark niche; what was lost in the shadow at its left (`RED_TEXT`), what was kept in its light at its right (`BRIGHT_JADE`); the choices under the lamp | The flame steadies from a gutter (0.6 s). Reduce: the flame is steady | Primary and secondary buttons |
| 40 | **Fates** (`fates_page.gd`) · now and then · The way · brief | Choose one of three fates after a major breakthrough | Fortune sticks shaken from a bamboo cylinder under the stars | The night sky; a bamboo cylinder (`SURFACE.bamboo`); each stick's verse on a `scroll` slip (page.gd) | A cylinder low in the centre with three sticks fanned out of it, each carrying its slip, the gift above and the cost below; Take this fate at each slip's foot | The sticks rise out one by one (0.3 s each, a tap shows all). Reduce: all three appear | Primary button |
| 41 | **Mercy** (`mercy_page.gd`) · now and then · Stone and bronze · brief | Spare or finish a foe who has yielded | The sword planted in the earth between you and the kneeling foe | A steel blade (pixel, a large weapon drawing) in `SURFACE.soil`; the foe's portrait from its layers | The sword standing upright down the middle of the window; Spare on the left (merit, and who may remember it), Finish on the right (sin, and their kin); the foe kneeling behind the blade | The blade glints once (0.3 s). Reduce: no glint | Primary and secondary buttons |
| 42 | **Relations** (`relations_page.gd`) · now and then · Bonds · brief | What the world remembers: karma, bonds, grudges, fame | The karma steelyard: merit and sin weighed on one beam, the threads of bonds and grudges hanging below | A `wood_dark` beam with `GOLD` merit weights and `INK` sin weights (pixel steelyard); `RED` threads for bonds, `INK` threads for grudges (page.gd) | A steelyard beam across the top half, tilted toward righteous or demonic by merit and sin, recent deeds as notches along it; threads hanging from it below, red to those bound to you and black to those who want you dead; fame as the plaque on the hook | The beam settles to its tilt (0.5 s, damped); threads sway. Reduce: drawn at its tilt, still | Primary buttons |
| 43 | **Settings** (`settings_page.gd`) · now and then · Shell · **drawn here** (23) | Sound, controls, accessibility, data | A lacquered cabinet of small drawers | `SURFACE.river_lacquer` drawer fronts with `GOLD` ring pulls; the open drawer's tray in `wood_dark`. Audio as racks of chime bells, toggles as brass latches (page.gd, all of it) | A column of four drawer fronts down the left (Audio, Controls, Accessibility, Data); the open drawer pulled out to the right as a tray holding its controls | The drawer slides out (0.2 s); a bell step chimes (sound). Reduce: the drawer fades | Primary and secondary buttons |
| 44 | **Pouches** (`pouches_page.gd`) · now and then · The post · brief | Tailor Xun deepens one category's pouch at a time | The tailor's chalked patterns on a bolt of cloth | `SURFACE.cloth` with chalk lines in `PAPER` at 70%, a bamboo ruler (page.gd); the pouch's category icon inside each outline (existing) | The seven pouches chalked on the cutting cloth as pouch outlines (a drawstring bag's shape) scattered in two staggered rows, each at its tier's size with the next tier dashed round it and its compartments ruled inside; the ruler laid slantwise across a corner; Sew under each | Sewing runs a stitch round the pattern (0.4 s). Reduce: the pattern turns solid | Primary buttons |
| 45 | **Emotes** (`emotes_page.gd`) · now and then · Leisure arts · brief | Pick a gesture | The shadow-puppet screen | A lamp-lit paper screen (`scroll` warmed by `ember`) in a `wood` frame; each emote's glyph as an `INK` silhouette (existing emote icons tinted) | A lit screen with each emote's puppet standing along it in two rows; locked emotes as grey outlines with their achievement | The chosen puppet hops (0.2 s). Reduce: no hop | Secondary buttons |
| 46 | **Chess** (`chess_page.gd`) · now and then · Leisure arts · brief | Solve today's problem | The Go board at the insight stone | `board`, `board_edge`, `board_line`, the stones (page.gd, as today) | A square 9 × 9 board in the centre with the four lettered points; the answers beneath | A stone is placed with a click. Reduce: as is | Primary buttons |
| 47 | **Guqin** (`guqin_page.gd`) · now and then · Leisure arts · brief | Play a short piece | The zither | `wood`, `wood_dark`, `bridge`, `peg`, `hui` (page.gd, as today) | Five strings across the page, notes gliding to the bridge at the left, the pegs as the buttons | Strings shiver when plucked (the game). Reduce: notes still glide; the shiver is smaller | Primary button |
| 48 | **Create Disciple** (`shell_screens.gd` creator) · now and then · Shell · brief | Make a new character: look, origin, name | The dyer's yard by the river: long dyed cloths hung to dry from a bamboo pole, the new disciple standing before them | The river backdrop (existing); a bamboo pole and a drying line (`SURFACE.bamboo`, `SURFACE.hemp`); long cloths in the game's own dye colours (`parts.json` `_dyes`, drawn page.gd); the figure (Avatar); the name on a paper tag | A drying line strung slantwise from a bamboo pole at the upper left down toward the right, five cloths of different lengths draped on it (Hair, Robe, Trousers, Shoes, Origin) with ◀ ▶ under each and the hair dyes as short strips; the figure stands large at the right below the line's low end, the name tag at its feet, Begin beside it | A changed cloth lifts in the breeze (0.2 s). Reduce: no breeze | Primary and secondary buttons |

---

## 4. How uniqueness was checked

1. **Concepts.** Each row names one physical thing. The 48 things, sorted by their head noun, repeat none: archway,
   board (duty tablets), board (Go), board (mission slips), book (field book), cabinet (curio), cabinet (drawers),
   calabash, chest, cliff, cloths (dyed), coil, compass, courtyard, cylinder, desk (magistrate's), discs, gates (moon),
   hall (plaques), hall (seats), handscroll, hearth, jade slips, lamp, letter case, mountain, pagoda, painting (framed),
   paper strip, patterns (chalk), pit, posters (pasted), river section, rubbing (a tab), screen (puppet), sheet
   (almanac), skiffs, stable, stage, stall, element charts (a tab each), steelyard, sword, terraces, tool wall, tray (gift),
   urn, window
   (barred), zither. Where a noun repeats, the thing differs in kind (three boards: hanging name tablets on a peg
   rail, a Go board, pinned paper slips; two halls: one hung with plaques, one of seats; two cabinets: an open curio
   shelf, a chest of drawers; two trays: a lacquered gift tray and the round winnowing tray in the coil row), and each such pair sits in different families with different layouts. Scrolls appear
   twice and are kept apart by kind and by how they hang: the Old Scrolls' rubbing on a hanging scroll (tall, rods top
   and bottom, the left two-thirds) and the Characters' handscroll (a long horizontal band with a roll at its end). No
   other page is a hanging scroll.
2. **Layout signatures.** Each signature was reduced to a silhouette code, the dominant shape and where it sits
   (for example "calabash, centre" or "one-point perspective, whole window"), and the codes were compared pair by
   pair. The revised pages (13, 16, 17, 18) were taken as fixed and every other row checked against them. The
   near-collisions found while writing, and how each was settled:

   | Near-collision | Settled by |
   |---|---|
   | The Old Scrolls' rubbing, revised as a hanging scroll with rods, against the first Character draft (a hanging portrait scroll left of the register) | The Character page became the jade-slip record: a mat of vertical slips across the whole window, bound by two gold cords, with no rods and no mounting. 09 v2 was redrawn to it |
   | Rows of figures: the revised Roll-Call (four hanging name tablets with a figure in each window), Selection, Companions, and first drafts of the Characters page (a cord of portrait lanterns) and the Notice Board (three portrait posters side by side) | The Roll-Call keeps the row of hanging portrait panels. Characters became the roster handscroll (figures painted along one band, no frames) and the Notice Board a collage of posters pasted over each other at angles. Selection's skiffs sit on water with no frame, Companions' friends stand in round holes in a white wall |
   | Hanging tablets: the Menu (approved, 03) and the revised Roll-Call | Kept, and named here for the user: the Menu is many small teal tablets in five bays under plaques, with no pictures; the Roll-Call is four large wooden tablets with a figure in each and a basket beneath. The bays against one row over baskets tell them apart at a glance |
   | Horizontal bands: the Dialogue strip and the Characters handscroll | The Dialogue strip is frameless at the screen's foot over the live world, with a portrait box and choices; the handscroll sits mid-window inside the page, a procession of figures ending in a thick roll |
   | Big circles: Teleport, Beast Arena, Companions, Welcome Back, and first drafts of the creator (a mirror) and the emotes (a wheel) | The creator became the dyer's cloths and the emotes a lit screen; what is left differs in kind: rings with ticks (compass), an oval of sand ringed with banners (pit), a row of small circles (gates), a spiral (coil) |
   | A bar across the top: Relations (beam), a first draft of Welcome Back (an incense trough), Workshop (tool wall), Pouches (ruler), Create Disciple (the drying pole), and Mercy's first draft (a blade laid flat) | Welcome Back became a spiral and Mercy's sword stands upright; the beam is the Relations page's whole subject, the drying pole carries tall cloths that fill the upper half, and the wall and the ruler are edges of something larger |
   | A big sheet with a stack: first drafts of the Calendar (a tear-off pad) and the Notice Board (a stack of posters), and the Mail (envelopes) | The Calendar became one broad ruled sheet and the Notice Board a collage; only the Mail keeps a fanned stack |
   | Fans from a point: Fates (sticks) and a first draft of Emotes (a folding fan) | Emotes became the puppet screen |
   | Grids of receptacles: Bag, Storage, the revised Shop's bag bundle, and first drafts of Characters (a token case) and Core Exchange (a board of wells) | Characters became the handscroll and Core Exchange the urn; the Bag's grid sits in a calabash, the Storage's under a raised lid, the Shop's in a quilted cloth on a crate beside the stall |
   | Rows of tall columns, found by the squint test on the contact sheets: the Menu's five bays (approved), and first drafts of the Pouches (seven tall patterns in a row) and Create Disciple (five cloths on a level pole) | The Pouches became pouch outlines scattered in two staggered rows, the creator's cloths hang from a slanting line with the figure large at its low end; the Menu keeps its bays |
   | Vertical stacks: Trial Tower (pagoda), Cultivation (stair) and a first draft of the Beast Arena (a ladder of banners) | The arena became the pit; the stair is diagonal and the pagoda a narrow column with eaves |
   | Painted places: the revised World map (a framed painting), Your Sect, Title | The map fills the window inside its frame with a card at the right and tablets at the foot; Your Sect is the room itself in a strip with cards below; the Title is one cliff face |
   | Figure with the worn slots: Bag and Character (decision 8 asks for both) | The Bag rings the figure with its slots on a dais beside the calabash; the Character stands the figure on the jade slips with the slots down the slips either side, in two straight columns |
   | **Not settled: the revised Techniques' Lost Arts tab against the Quests board.** Both are paper pinned to dark timber (Lost Arts with red thread between scraps; Quests with a red cord of chest charms), and the Quests board was the brief's own example | Left for the user (§10). The recommendation: Quests keeps the board it was briefed with, and Lost Arts becomes an explorer's album, an accordion book opened out with one leaf per act and the scraps pasted in, which keeps its kinds, hints and Track |
   | The revised Techniques' tab surfaces against the other pages: Earth's cliff in section against the Title's cliff face; Metal's mirror back and Space's armillary against the Teleport compass; Secret Arts' practice mat against a first draft of Welcome Back (the haul on a woven mat) | Welcome Back's haul moved into a round bamboo tray. The others differ in kind and scale: a strata section filling a tab against a carved face above a river; relief bands and orbiting rings filling a tab against a flat dial with a needle, a stone at each bearing and a card beside it |
   | Paper pages in one family (Records, seven pages) | A strip, a board of slips, a framed painting, an envelope stack, a ruled sheet, a pasted collage and a book: no two share a silhouette |

3. **The contact sheets.** Every row's layout signature is drawn as a thumbnail in `docs/mockups/page_identity_sheet.png`
   and its two companions (§9). The sheets were looked at at 1x, and again in grey with a Gaussian blur of 6 px (a squint
   test), which leaves only the silhouettes. The first render failed it once (the row of tall columns above); after
   that change no two thumbnails blur to the same shape, apart from the Lost Arts tab and the Quests board (above), which are one thumbnail's tab against another page. The pairs that come closest, and are left for the user's eye,
   are the Menu and the Roll-Call (both hang tablets, in bays against a single row over baskets) and the three pages
   with a light slip at the right (Quests, Works, the Old Scrolls), whose left sides differ.

---

## 5. Art to make

| Art | For | Kind | Notes |
|---|---|---|---|
| `gourd_well` | Bag | HD fixed asset | Withdrawn by decision 15 (no gourd drawing): the calabash, two bulbs and a waist in `SURFACE.gourd` |
| `wood_tag` | Bag (the item tag), Works (labels) | HD nine-slice | A tag with a clipped top and a cord hole; the Bag's use withdrawn by decision 15 (a small card instead). On a tag that carries grade colours as words the face must be `wood_dark`, not `SURFACE.gourd_dark`, where the Mystic and Sphere colours fall to 3.1:1 |
| Jade slips | Character | page.gd, **built** (P5) | Vertical slats every 40 px with rounded ends in `SURFACE.cloth` on an `INK` backing, a lit rim; two `GOLD` cords with knots; the figure's slips washed lighter (`SURFACE.cloth_wash`) on the tabs that show the figure; the slips fan out from a bundle as the page opens |
| `jade_tag`, `jade_label` | Character (the tabs, the title) | HD nine-slices, **built** (P5) | Jade tags with a square top and a rounder foot, `selected` the lit `JADE`; the title's tag with a `GOLD` inlay |
| `honour_tablet`, `honour_seal` | Character (the titles, decision 16) | HD nine-slice and fixed asset, **built** (P5) | Each title an honour: a red lacquer tablet (`SURFACE.lacquer`) with cut corners, a gold inlay line and a gloss, the worn one in a gilded frame with a stud at each corner; its motif on a 32 px gilt boss, the sign sunk in lacquer: blade, shield, pearl, cloud, peak, lotus, coin, cauldron or star, by the stat the title's gift raises |
| `paper_slip` | Quests | HD nine-slice | A slip with a torn top edge and a pin shadow |
| `envelope`, `letter_sheet` | Mail | HD nine-slices | Crease shading across the letter; the envelope's flap |
| `poster` | Notice Board | HD nine-slice | Curling and torn corners, paste stains |
| `gift_tray` | Gift | HD nine-slice | Compartments by a repeated centre |
| `storehouse_chest` | Storage | HD fixed asset | The raised lid in perspective with its lining |
| Dyed cloths | Create Disciple | page.gd | Long cloths in the `parts.json` dyes, with a fold shadow; a bamboo pole |
| Handscroll | Characters | HD nine-slice (horizontal) and page.gd | Paper with silk borders; the roll's thickness drawn from the count of closed slots |
| Book spread, ribbons, the rubbing's mount | Codex, Old Scrolls | As drawn in 18 and 18_scrolls | Owned by the 18 redraw |
| The valley painting | World map | Pixel, `tools/ui/build_valley_map.py` | Built (P5): the painting and a close-up per area; the Azure Expanse and the Lantern Star Field are drawn from tokens by the page until they are painted |
| The stall and its awning | Shop | As drawn in 17 | Owned by the 17 redraw |
| Archway | Breakthrough | Pixel prop | About 280 × 240 art px at 2× |
| Skiffs and jetty | Selection | Pixel props | Four skiff states: moored, chosen, empty mooring, locked |
| Cliff face | Title | Pixel backdrop layer | Over the existing river |
| Stall doors | Spirit Animals | Pixel prop | Half-door, open and shut |
| Hall interior | Sect | Pixel plate | One-point perspective, 1088 × 552 |
| Core urn | Core Exchange | Pixel prop | Words never sit on it |
| Magistrate's desk | County Hall | Pixel prop | |
| Life lamp | Revival | Pixel prop | Flame by FX |
| Steelyard | Relations | Pixel prop | Beam, hook, two weights |
| Planted sword | Mercy | Pixel prop | A large blade drawing |
| Eave strip | Trial Tower | Pixel tiles | `JADE_SHADOW` tiles |
| Duty tablets, baskets, net bag, cage | Roll-Call | As drawn in 13 | Owned by the 13 redraw |
| Seven works objects | Works | Pixel, Style A 64 | Manual, seal, stele, sealed favour, furnace, flag, mirror; some can start from today's works icons |
| Six tools | Workshop | Pixel, Style A 64 | Compass, loupe, needle roll, chisel, brush, pointer |
| Bronze pin, wax seal, done stamp | Quests, Mail | Pixel, Style A 32 | |
| Herb stages | Garden | Pixel | Four growth stages per herb family |
| Everything else in §3 marked page.gd | 30 pages | page.gd | Drawn from tokens: the dais and ring, the board's grain, the almanac's rules and seals, the season wheel, the compass rings, the slips and cords, the bamboo lattice, the coil, the terraces, the stair, the stars, the threads, the chalk lines, the drawers and bells |

Pixel art follows `docs/art-contracts.md` and, for figures, `AGENTS.md`: no page asks for a new body pose. Figures
use the registered actions (idle, walk, meditate); animals use their sheets' own actions.

---

## 6. Motion

The rule is the moments design's (`docs/moments_design.md` §4.6, "Reduce motion", decided 2026-09-27): with
`reduce_motion` on there are no camera pans and no shake; slides, wipes, unrolls, swings and flips become fades of
0.2 s; rows fade without rising; durations stay the same so words stay readable. For pages that means:

1. A page's regions are live from its first frame; no opening motion delays a tap, and a tap during one finishes it.
2. Opening motions last 0.35 s at most; a choice's motion 0.3 s at most. Only the Breakthrough doors (0.5 s) run
   longer, and they lead into moment 05, which has its own lock and skip.
3. Motion that is information stays under Reduce motion: the fishing bite, the guqin's notes, the furnace's heat, the
   arena replay's bars. Decoration goes: sway, swing, bob, ripple, glint, flutter, pour.
4. Bright flashes off: glows and halos at 0.3 of their alpha.
5. Battery saver: idle loops (sway, flicker, breathing figures) stop.
6. Sounds follow the page's material: paper rustles on the paper pages, wood knocks on the timber ones, a small bell
   on the drawers and the hanging tablets. `AudioDirector` keys are named with each page's P5 part.

---

## 7. New surface tokens

Each is a mix of two existing tokens (`a` mixed with `t` of `b`), so no new hue enters. Ratios are WCAG 2 contrast of
the text colours allowed on it; a surface marked "no words" carries none.

| `SURFACE` key | Mix | Hex | Words on it | Ratio |
|---|---|---|---|---|
| `gourd` | `BRONZE` + 0.35 `GOLD` | #b4853d | `PAPER_INK` at 20 px and up | 4.77 |
| `gourd_dark` | `BRONZE` + 0.45 `INK` | #584227 | `PAPER`, `PALE_GOLD`, `MIST`, `GOLD` | 7.24, 7.68, 5.44, 5.08 |
| `space` | `DEEP_TEAL` + 0.55 `INK` | #0a1e23 | every text token | `PAPER` 13.17 |
| `lacquer` | `BLOOD` + 0.55 `INK` | #541720 | `PAPER`, `PALE_GOLD`, `MIST`, `GOLD` | 10.59, 11.24, 7.96, 7.43 |
| `lacquer_black` | `INK` + 0.10 `BRONZE` | #161918 | every text token | `PAPER` 13.57 |
| `river_lacquer` | `RIVER_NIGHT` + 0.20 `JADE_SHADOW` | #0c2a2f | every text token | `PAPER` 11.60 |
| `bamboo` | `bridge` + 0.18 `JADE` | #b9ba8b | `PAPER_INK` | 7.84 |
| `hemp` | `PAPER` + 0.30 `BRONZE` | #d1bda1 | `PAPER_INK` | 8.63 |
| `almanac` | `PAPER` + 0.30 `GOLD` | #e7d5a8 | `PAPER_INK`; `BLOOD` for red words | 10.86; 4.58 |
| `cinnabar` | `RED` + 0.50 `BLOOD` | #cc3c43 | `PALE_GOLD` at 20 px and up, inked | 3.98 |
| `rubbing` | `INK` + 0.07 `PAPER` | #171f22 | `PAPER`, `PALE_GOLD`, `MIST` | 12.83, 13.61, 9.64 |
| `stone` | `HOLLOW` + 0.45 `INK` | #4d595e | `PAPER`, `PALE_GOLD`; `GOLD` at 20 px and up | 5.54, 5.88; 3.89 |
| `plaster` | `PAPER` + 0.25 `MIST` | #dadbd0 | `PAPER_INK` | 11.27 |
| `cloth` | `JADE_SHADOW` + 0.45 `INK` | #0f3435 | every text token | `PAPER` 10.30 |
| `silk` | `JADE_SHADOW` + 0.18 `PAPER` | #3b6b66 | `PAPER`, `PALE_GOLD` only | 4.63, 4.91 |
| `sand` | `PAPER` + 0.45 `BRONZE` | #c5ab8a | `PAPER_INK` | 7.17 |
| `straw` | `bridge` + 0.25 `BRONZE` | #c8aa75 | `PAPER_INK` | 7.10 |
| `soil` | `wood_dark` + 0.30 `INK` | #2b1e16 | every text token | `PAPER` 12.39 |
| `water` | `QI` + 0.60 `INK` | #185660 | `PAPER`, `PALE_GOLD`, `MIST` | 6.34, 6.73, 4.77 |
| `clay` | `BRONZE` + 0.25 `RED` | #ac663e | no words | — |
| `cloth_wash` (P5) | `JADE_SHADOW` + 0.20 `JADE` | #1a605c | `PAPER`, `PALE_GOLD` (the Character figure's slips) | 5.61, 5.95 |
| `sky` (P5, the Bag) | `JADE_SHADOW` + 0.58 `INK` | #0d2b2d | every text token (the night at its lightest behind words) | `PAPER` 11.50, `HOLLOW` 4.81 |
| `sea` (P5, the Bag) | `DEEP_TEAL` + 0.16 `MIST` | #27484e | `PAPER`, `PALE_GOLD`, `MIST`, `GOLD` (the sea of cloud) | 7.58, 8.05, 5.70, 5.32 |

In code (`UiKit.SURFACE`, P5) every row above is a token. The talisman's red ink and the zither's strings, which held
the names `cinnabar` and `silk` before this table gave them out, are `cinnabar_ink` and `qin_silk`; their colours did
not change.

Grade and quality colours were made for the dark fills and fail on paper (Superior #5aa7e8 on `scroll` is 2.4:1).
On a light surface a grade shows as a small chip in its colour with the word in `INK`, or by the slot's rim, never as
coloured words. `BLOOD` is the red for words on paper (4.58 on `almanac`, 4.87 on `scroll`); where the paper is tinted (the almanac's live day) red words take `BLOOD` mixed 15% toward `INK`, #991e2a (5.24 on the tint, where `BLOOD` falls to 4.26). The audit
(`tools/dev/ui_style_audit.py`) measures each new surface before it ships (style guide §1.4 rule 4).

## 8. How a page takes its identity

The pattern P5 built, for converting the pages family by family. A page stays an immediate-mode `Page` (C8); it
declares what it is, draws its own surface in the standard window rect, and Page keeps everything that stays shared. A
page that declares nothing keeps the shared window, plaque and tabs exactly as before.

### 8.1 What a page declares

In `_init` (`scripts/ui/page.gd`, `class Identity`):

```gdscript
identity = Identity.new("cloth", false, "own", "slip_mat_whole_two_cords", OPEN_MOTION_MAX)
grade_rims = true   # optional: slots ring every item in its grade and mark a rolled quality with a gem
```

| Field | Means | The Character page |
|---|---|---|
| `surface` | The `UiKit.SURFACE` key of the page's material: the ground under any word that names no other | `cloth` |
| `framed` | `true` keeps the shared `major_window` round the surface; `false` makes the surface the window (Decisions taken, 2) | `false` |
| `title_mount` | `"plaque"` keeps the shared title plaque; `"own"` draws the page's mount | `"own"`: a jade tag knotted to the cord |
| `signature` | The layout signature of §3 as an id. No two pages may share one (the `ui_suite` checks) | `slip_mat_whole_two_cords` |
| `open_s` | The opening's length, at most `Page.OPEN_MOTION_MAX` (0.35 s, §6) | 0.35 |

### 8.2 What a page overrides, and what Page keeps

| Hook | Default (the shared look) | Override it to |
|---|---|---|
| `draw_surface(r)` | A flat `SURFACE` fill | Draw the material inside the window rect `r` (a standard window, style guide §2.2) |
| `content_rect()` | Inside the window, under the title and tabs | Lay the page out on its own surface |
| `title_rect()`, `draw_title_mount(r)` | The 440 × 60 plaque at the top | Place and draw the mount; Page inks the title on it at 34, stepping down the display scale to fit |
| `tab_rects()`, `draw_tab(r, i, state)` | A row of kit tabs under the title | Give the tabs the page's form (the Character's jade tags on the cord) |

Page keeps, whatever the page draws: the dimmed world; the close button at the window's top right (frame end − 72,
y + 16, 52 px), Esc and a tap outside the window; each tab's 48 px target, its lock and its reason; `btn` with inked
primary labels; `text`, `para`, `rich`, `heading`, `bar` on the type scale; `slot_box`; the confirm dialog and the toast.
A page never writes state (`contract_tests`): it submits intents in `on_action` as before.

### 8.3 Grounds: every word is measured on what it sits on

A surface is not a kit fill, so the `ui_suite` cannot know what lies under a word unless the page says so. A page with
its own surface names its grounds as it draws them, and the suite measures every plain word on the last ground drawn
under its centre (4.5:1, or 3:1 from 20 px); the `identity_suite` proves on a probe page that a word too dim for its
ground is caught:

- `ground(rect, color)`: the lightest tone of the surface in `rect` (the Character figure's washed slips, a sunk band).
  Page names the identity's surface itself when `draw_surface` does not.
- `face(rect, asset, state)`: an HD face that words sit on (a tag, a tablet); measured on the kit's own art.
- `panel(rect)`: as before; now also a ground.
- Inked and outlined words (titles, primary labels, the lit tags, bar labels) are measured on `INK`; button labels on
  their kit faces. Every new fill a colour is drawn on is a row of `UiKit.TEXT_ON` (`"surface:<key>"` for a flat
  material), which the `ui_style_suite` measures. When a colour fails, change the colour, not the check: the washed
  slips carry `PAPER`, not `MIST` (4.21 on `cloth_wash`).

### 8.4 Surface art

- **page.gd** from tokens, with the Page helpers `rounded(rect, radius, color)` (anti-aliased corners) and
  `glow(rect, color)` (a radial fade: a lit centre, a wash, a shadow), and anti-aliased `draw_line`/`draw_circle` for
  cords, rims and knots. No colour literals: `Color(UiKit.X, a)` and `UiKit.X.lerp(UiKit.Y, t)` only (the
  `ui_style_suite` scans every page).
- **HD** through `tools/ui/build_ui_hd.py`: a fixed asset (`margins [0, 0, 0, 0]`, drawn with
  `draw_texture_rect(UiKit.hd_texture(asset, state), rect)`) or a nine-slice (drawn with `face`). Colours are the tokens
  and their `mix()`es (the builder's P5 block: `TOKEN`, `mix`, `LACQUER_S`). Keep ornaments inside the corner squares
  (the builder's edge check). The kit builds byte-identical twice; after adding a PNG run Godot's `--import` and set
  `mipmaps/generate=true` in its `.import`, as every HD asset has.
- A new material is a `SURFACE` entry, a mix of two tokens (§7), with its `TEXT_ON` row.

### 8.5 Motion

`unfold(dur)` is the opening's progress, 0 to 1 over the identity's `open_s`, eased out; a page moves its parts by
`1 - unfold()` (the Character's slips fan out from a bundle). Page fades the page in over the same time. Under Reduce
motion (`UiKit.reduce_motion()`, the setting of `docs/moments_design.md` §4.6) `unfold()` is 1 from the first frame and
the page only fades in, over `UiKit.MOTION_FADE_S` (0.2 s). A tap sets the opening to its end. Draw moving parts under
`draw_set_transform` and register their regions at their final places, so every target is live from the first frame.
Decoration that only moves does not run under Reduce motion.

### 8.6 Shared pieces of the self family

`CharacterPage.draw_worn(page, ch, at, id, name_col)` draws the eight worn slots wherever a page puts them (the
Character's two columns): a closed slot shows its lock and answers a tap with what opens it; an empty slot glows jade
while the bag holds a piece the character may wear there. The figure is the live `Avatar` at 2.5 (5 screen px an art
px, decision 8). `grade_rims` rings every slot's item in its grade's colour and marks a rolled quality with a gem
(mockup 09 v2). The Bag takes it too, round its orbit, with `ringed` for the slot its card is about (the dashed gold
ring); `locked_reason` and `wearable_in_bag` are the family's, and `stat_text` writes a stat as the register does.

### 8.7 Converting a page: the steps

1. Read the page's row in §3, its family in §2 and its mockup if it has one; check the decisions of the roadmap (§6)
   that came after the catalogue.
2. Declare the identity; override `draw_surface`, `content_rect`, and the title and tab hooks the row asks for.
3. Draw the surface from tokens, or add its art to `build_ui_hd.py`; add any new `SURFACE` mix and its `TEXT_ON` row.
4. Name the grounds; keep every target 48 px or more and every word on the type scale.
5. Give the opening in `unfold()`; leave decoration off under Reduce motion.
6. Keep the page's intents; add strings through `tools/data/ui_strings.json` and data through `tools/data/`.
7. Run the suite (`ui_suite`, `identity_suite`, `ui_style_suite`, `contract_tests`); take screenshots on a valley_run
   checkpoint copy and compare them with the mockup.

---

## 9. Mockups made with this page

Rendered with `tools/dev/render_mockups.py` from `docs/mockups/src/`; numbers from the valley_run character's
checkpoints, taken as frozen copies of `user://valley_cp/<section>` at 01:33 UTC on 2026-09-27 and read from the save
and from captures of the real pages on those copies (the build at 41d15ae). Listed in `docs/mockups/README.md` under
"P5 page identity". Each was looked at at 1x, and its dense parts cropped and enlarged: no text under 14 px, every tap
target 48 px or more, nothing clipped.

| PNG | Page |
|---|---|
| `page_identity_sheet.png`, `page_identity_sheet_2.png`, `page_identity_sheet_3.png` | The contact sheets: every row of §3 as a labelled thumbnail of its concept, in the order of §3 |
| `07_bag_full_v2.png`, `08_bag_empty_v2.png` | Bag: the spirit gourd, full (ls6_end) and early (bf2); rejected by decision 15, replaced by the concepts `07_bag_a`, `07_bag_b` (with `_card`, `_pill` and `08_bag_b_empty`) and `07_bag_c` |
| `09_character_v2.png` | Character: the jade-slip record (ls6_end) |
| `12_quests_v2.png` | Quests: the mission board (ae_end) |
| `14_works_v2.png` | Works: the curio cabinet (ls6_end) |
| `14_works_v4.png` | Works: the curio cabinet with its seven objects drawn (96 px) and the Seal Scripts tray bigger, five seals at once (ls6_end; decisions 21, 26) |
| `19_calendar_v2.png` | Calendar: the almanac (qu5); rejected by decision 22, the first Calendar (19) stays |
| `22_mail.png` | Mail: the letter case (ls6_end) |
| `23_settings.png` | Settings: the cabinet of drawers (ls6_end) |

---

## 10. For the user to decide

1. The catalogue as a whole: the concept and layout signature of each row, and the families.
2. Whether a page may give up the shared `major_window` frame for its own surface (as the drawn mockups and the revised
   13, 16, 17 and 18 do), keeping the close button, the inked title lettering, primary buttons, the text tokens, the
   type scale, 48 px targets and the standard window rect; or whether the frame stays and only the inside changes.
3. The Character page as jade slips (09 v2). It was first drafted as a hanging portrait scroll; the revised Old Scrolls
   is a rubbing mounted as a hanging scroll, and decision 11 asks that the Old Scrolls look like nothing else.
4. "Your bag" as one thing: the revised Shop shows it as a quilted cloth bundle on a crate, the Bag page as the gourd.
   The recommendation is the gourd everywhere the bag appears beside another page (Shop, Storage, Gift).
5. The Menu (approved) and the revised Roll-Call both hang tablets. They read apart at a glance; the user may still
   want one of them changed.
6. The revised Techniques' Lost Arts tab (a board of pinned fragments) repeats the Quests board (12 v2). One of the two
   should change; the recommendation is that Quests keeps the notice board the brief asked for and Lost Arts becomes an
   explorer's album with one leaf per act (§4).
7. The new `SURFACE` tokens of §7.
8. For each drawn mockup, what `docs/mockups/README.md` lists under it.


## Decisions taken

Taken as recommended (2026-09-27) so P5 can start; the user can overturn any:

1. The catalogue stands as written.
2. A page may drop the shared window frame for its own surface; only the close button, primary buttons, text tokens,
   the type scale and 48 px targets stay shared.
3. Quests keeps the pinned board. The Techniques' Lost Arts tab becomes an explorer's album, one leaf per act.
4. "Your bag" is the spirit gourd everywhere, the shop's included. (Overtaken by decision 15, no gourd drawing: "your bag" beside other pages follows whichever Bag concept the user chooses.)
5. The Menu's hanging plaques and the Roll-Call's tablets stay as drawn; they read apart.
6. The `SURFACE` tokens of §7 join the style guide's token table.

The user's later decisions (roadmap §6) that change this page:

7. Decision 15: no gourd drawing in the Bag. The inventory is to feel like a big space, with a small information card
   for a chosen item instead of a large detail panel; new concepts go to the user as mockups first. Row 3 and its
   mockups 07 v2 and 08 v2 are withdrawn and kept as the record; the Bag keeps its P4 page until a new concept is
   approved. So "your bag" is no longer the gourd (4 above) until that concept says what it is.
8. Decision 16: the Character page's titles look and feel more fancy, each a named honour. Built as red lacquer tablets
   with the title's motif on a gilt boss and its gift inscribed in gold, the worn one in a gilded frame (§5, §8).
9. Decision 24: the Bag is concept B, the heaven in the gourd, built to its row (3) and mockups; "your bag" beside
   the other pages is still to follow it.
