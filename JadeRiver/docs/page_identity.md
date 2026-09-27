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
- **Status.** *Approved*: mockups 00–05. *Elsewhere*: another agent is redrawing it now (06 Techniques, 13 Roll-Call,
  16 World Map, 17 Shop, 18 Codex and Old Scrolls); its row records the identity the redraw must keep distinct from
  the rest, to be reconciled when the redraw lands. *Drawn here*: a full mockup with this page (§8). *Brief*: a row
  only, for P5.

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
| **The self** | Jade and gold: `SURFACE.space` (the jade-dark inside), `GOLD` lips and rings, `SURFACE.gourd` and `SURFACE.silk` | Bag, Character | A calabash between the figure's ring of slots and a hanging tag; a tall hanging scroll with the slots in its mounting |
| **The way** | Stone, sky and starlight: `sky_top` / `sky_bottom`, `SURFACE.stone`, `GOLD` light | Cultivation, Breakthrough, Techniques, Revival, Fates | A stair; an archway; a constellation tree; a single lamp; three sticks fanned from a cylinder |
| **The sect** | Red-lacquered pillars and dark timber: `SURFACE.lacquer`, `wood_dark`, `BRONZE`, red paper | Menu, Sect, Your Sect, Characters | Bays of hanging tablets; a hall in one-point perspective; a courtyard panorama; a cord of lanterns |
| **Bonds** | Whitewash and red thread: `SURFACE.plaster`, `RED` thread, `HEART` | Companions, Gift, Relations | Moon gates in a wall; a tray above the talk; a steelyard beam with threads |
| **Records** | Paper and ink: `scroll`, `SURFACE.almanac`, `PAPER_INK`, `BLOOD` seals | Dialogue, Quests, World map, Mail, Calendar, Notice Board, Codex | A strip under the scene; a board of pinned slips; a full-bleed painting; an envelope stack and an unfolded letter; a ruled almanac sheet; three posters under an eave; an open book |
| **The post** | Bamboo and hemp: `SURFACE.bamboo`, `SURFACE.hemp`, `SURFACE.cloth` | Roll-Call, Works, Welcome Back, Pouches | A wall of lattice windows; an irregular curio shelf; a spiral coil beside a mat; chalk patterns under a ruler |
| **The workshop** | Worked timber and tools: `wood`, `wood_dark`, `ember`, `SURFACE.soil` | Crafts, Workshop, Garden | A vessel centred over its fire; a tool wall above a bench seen from above; terraces stepping down the page |
| **The market** | Black lacquer and brass: `SURFACE.lacquer_black`, `GOLD`, paper tags | Shop, Storage, Exchange, County Hall, Auction | A three-part counter; an open chest; a barred window; a desk with a warrant tube; a lit pedestal |
| **Beasts** | Straw and rough timber: `SURFACE.straw`, `wood`, `SURFACE.sand`, `SURFACE.clay` | Spirit Animals, Beast Arena, Core Exchange | A column of stall doors; an oval pit ringed with banners; an urn between a shelf and a spout |
| **Stone and bronze** | Cut stone and cast bronze: `SURFACE.stone`, `BRONZE`, `GOLD` | Teleport, Trial Tower, Mercy | Concentric compass rings; a tall pagoda in section; a sword planted upright |
| **Leisure arts** | The instrument's own wood: `board`, `board_line`, `wood`, `bridge`, `peg`, `hui`, `SURFACE.water` | Chess, Guqin, Fishing, Emotes | A square board; five horizontal strings; a cut through the river; a lit paper screen |
| **Shell** | The river at dusk and lantern light: the river backdrop, `SURFACE.river_lacquer`, `PALE_GOLD` glow | Title, Selection, Create Disciple, Settings | A cliff face with the name cut in it; skiffs at a jetty; a folding screen; a column of drawers |

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
| 3 | **Bag** (`inventory_page.gd`) · many a session · The self · **drawn here** (07 v2, 08 v2) | What you carry and wear; equip, use, lock, discard, sort | The spirit gourd, opened: the character's own calabash in section, its inside a jade-dark space | Gourd skin `SURFACE.gourd` with a `GOLD` lip and a `RED` cord; the inside `SURFACE.space` with faint `JADE` ring marks; the figure's dais in `JADE_SHADOW` light with a thin `GOLD` ring through the worn slots; the chosen item on a dark wooden tag `SURFACE.gourd_dark`. Art: the calabash `gourd_well` (HD fixed asset); the dais, ring, ring marks and the space level (page.gd); `wood_tag` (HD nine-slice); the live figure (Avatar, decision 8) | Three parts in a row: the figure on a round dais inside an oval ring of the eight worn slots (left); the calabash (centre): its upper bulb holds the gourd's name and its space as a level of light, a red cord round its waist carries the kind filters as hanging tags, its lower bulb holds the 5-wide grid; the chosen item's tag hung on red string from the rim (right). Key Pouch: the calabash becomes a drawstring pouch | The stopper lifts and the rows rise into the bulb on opening (0.25 s); a new item drops in with one bob; the tag swings once on a new choice (0.3 s); the level rises as space fills. Reduce: grid and tag fade in over 0.2 s; no bob, no swing | 76 px slots with Style A icons and grade rims, primary and secondary buttons, the purse pills |
| 4 | **Menu** (`menu_page.gd`, the hub) · many a session · The sect · approved (03) | Reach every system; see what waits in each | The sect's hall of hanging plaques | Teal lacquer tablets (`minor_panel` faces) on `GOLD` cords between red-lacquer pillars (`SURFACE.lacquer`, page.gd); bay plaques (existing) | Five bays under five plaques, tablets hung down each bay on cords; the character line and purses at the foot | Tablets settle with one sway on opening (0.25 s); a ready seal is pressed on (0.15 s). Reduce: fade; the seal simply appears | Badges (count, ready seal, new) |
| 5 | **Cultivation** (`cultivation_page.gd`) · many a session · The way · approved (04) | See the whole climb and this realm's nine steps; meditate; reach the gate | The mountain ascent | The night mountain (`sky_top` / `sky_bottom`); steps in the band colours (`JADE_SHADOW`, `JADE`, `BRONZE`, `GOLD`); the realm path as ink dots with `GOLD` waystations (page.gd); the figure seated (Avatar `meditate`) | The nine-step stair in the centre, the nineteen realms winding up the left, the next step's unlocks and the gate at the right; eight tabs | At a minor breakthrough the figure climbs one step (0.4 s); the bottleneck riser glows. Reduce: the step lights, no climb | Stage bands, unlock chips, `bar_shell` |
| 6 | **Quests** (`quest_page.gd`) · many a session · Records · **drawn here** (12 v2) | What now: the story, today's round, what is near, and where the tracked quest leads | The sect's mission board: paper slips pinned to timber | The board `wood_dark` with grain lines every 3 px (page.gd); slips in `scroll` paper with `PAPER_INK` words (HD nine-slice `paper_slip`, torn top); the main quest's slip headed in `SURFACE.cinnabar` with a gold edge; bronze pins (pixel, 32 px Style A glyph); the done stamp in `BLOOD` (pixel) | A timber board filling the left two-thirds with slips pinned in clusters: the story's slip top-left with a red head; the day's missions as a row of small slips; the day's chests on a red cord along the board's foot; side quests stacked under three region nameboards. The chosen slip is taken down and held large at the right, with its route drawn across it and Go | A tapped slip is unpinned and lifts to the reading place (0.2 s); a finished slip is stamped. Reduce: the reading slip fades in; the stamp appears | 76 and 48 px slots for rewards, `bar_shell` with reward stops, purse pills |
| 7 | **World map** (`map_page.gd`) · many a session · Records · elsewhere (16) | Where everything is; where the tracked quest leads; travel | The painted landscape of the zone | Silk painted in ink wash: `JADE` river, `INK` mountains, `PALE_GOLD` nodes on dotted routes; one painting per zone (pixel, the backdrop pipeline) | Full-bleed painted landscape with its landmarks; a floating card with the area's picture, level band, resources and Track Route; tabs along the foot (Areas, Resources, Objectives) with a legend (decision 11). The Heaven Ranking tab needs its own face, settled with the redraw | The painting unrolls sideways on opening (0.3 s); a tracked route's dots light in order. Reduce: fade; the route shows lit | Primary button, legend marks |
| 8 | **Shop** (`shop_page.gd`) · many a session · The market · elsewhere (17) | Buy, sell, buy back | The merchant's lacquered counter | `SURFACE.lacquer_black` counter with `GOLD` brass fittings; paper price tags with `PAPER_INK`; the merchant's bust from her layers (existing) | The merchant over her shelf (left), the counter with the deal (middle), your sack to sell from (right); buy-back a small control (decision 11) | A bought item slides across the counter to your side (0.25 s); coins stack. Reduce: fade | 76 px slots, purse pills, quantity buttons |
| 9 | **Breakthrough** (`breakthrough_page.gd`) · many a session (nine steps a realm) · The way · brief | See what the next step asks, fix it, add supports, see the odds, break through | The heaven gate at the top of the stair: a stone archway whose doors open when you break through | `SURFACE.stone` with `GOLD` leaf on its plaque; the sky behind in `sky_top` / `sky_bottom`; requirement tablets on `RED` cords; three jade offering dishes on the step. Art: the archway (pixel prop, about 280 × 240 art px at 2×); the sky and the tablets (page.gd) | One symmetric archway centred on the page: the next realm's name on its plaque; each requirement hangs from the beam as a tablet, lit gold when met, dark with its Go when not; three offering dishes on the step hold the support items; the chance and the risk word written on the two pillars; Break Through on the threshold | A met requirement's tablet lights (0.2 s); Break Through opens the doors (0.5 s) into moment 05. Reduce: tablets light without the glow ramp; the doors cross-fade | Primary button, 76 px slots for supports, requirement dots |
| 10 | **Title** (`shell_screens.gd` TitleScreen) · every session · Shell · brief | Continue, begin, settings, quit | The game's name cut into the cliff above the river | The river backdrop (existing); a cliff face (pixel, a backdrop layer); the name carved in `PALE_GOLD` with an `INK` bevel (page.gd) | The name cut large into a cliff face in the upper middle; the three buttons stacked on a stone ledge under it; the river across the foot | Mist drifts over the river; the carving catches the light once at launch (0.6 s). Reduce: still mist, no glint | Primary and secondary buttons |
| 11 | **Selection** (`shell_screens.gd` selection) · every session · Shell · brief | Pick who enters the world; add or delete | Skiffs moored at the jetty at dusk, one disciple standing in each | The river (existing), the jetty in `wood`, each skiff's prow lantern in `PALE_GOLD` glow; skiffs and jetty (pixel props); figures (Avatar) | Four skiffs side by side along a jetty in the lower half, a disciple standing in each with a name lantern on the prow; empty moorings (a coiled rope, "a new disciple") for open slots; page arrows at the jetty's ends; Enter World at its head | The chosen skiff rocks once and its lantern lights; Enter World casts it off toward the viewer (0.5 s). Reduce: the lantern lights; a fade on entering | Primary and secondary buttons |
| 12 | **Welcome Back** (`welcome_page.gd`) · every session · The post · brief | What the time away earned; to the Storehouse or kept | The incense coil that burned while you were away, and your pack emptied on a mat | `SURFACE.hemp` mat with weave lines; the coil burnt to `HOLLOW` ash with an `ember` tip, the unburnt rest in `BRONZE` (page.gd); a bamboo stand (`SURFACE.bamboo`) | A spiral on the left whose burnt length is the time away out of the 12-hour cap, the glowing tip now and the unburnt rest what more the cap would have held; the haul spread on a woven mat at the right; the two choices under the mat | The ember runs to its mark (0.6 s, a tap skips); goods drop onto the mat one after another (0.05 s apart). Reduce: the coil is drawn at its mark; goods appear together | 76 px slots, primary and secondary buttons |
| 13 | **Character** (`character_page.gd`) · every session · The self · **drawn here** (09 v2) | Who the character is: what they wear, their numbers, titles, origin and ties | The hanging portrait scroll: an ancestor portrait mounted on silk | Brocade mounting `SURFACE.silk` with a `scroll` paper centre; rollers in `wood_dark` with `GOLD` caps; the register in ruled columns on `SURFACE.space`; title plaques in lacquer. Art: `portrait_scroll` (HD, a vertical nine-slice with its rollers); the figure painted in (Avatar at 2.5); plaques (page.gd) | A tall hanging scroll left of centre with rollers top and bottom; the figure full-length in its paper centre; the eight worn slots set into the brocade border, four a side, like collectors' seals; the name, realm and title as a vertical inscription at the painting's upper right; the register to the right (pools, offence and defence in ruled columns) and the titles as a rack of small plaques | The scroll unrolls downward from its top roller on opening (0.35 s); equipping re-inks the figure (0.2 s). Reduce: fade in | 76 px slots, `bar_shell` pools, secondary buttons |
| 14 | **Roll-Call** (`posts_page.gd`) · every session · The post · elsewhere (13) | Every character's post: yield, pouch, settle; the Storehouse, Bench and Vows | The post-house windows: each character seen at their post through a lattice window, their basket on the sill | `SURFACE.bamboo` lattice (page.gd); each window a crop of the post's own room (existing backdrop layers); the character (Avatar idle); a hemp basket (pixel prop) | A wall of lattice windows, soonest-full first, each framing that character at work in the post's scenery with the basket filling on the sill; the Storehouse door and the gong (Settle all) at the wall's end | Figures breathe (idle frames); tapping a basket settles it and the goods pour toward the door (0.4 s); the gong ripples. Reduce: counts change, no pour or ripple | Primary button, `bar_shell` with stops, 76 px slots |
| 15 | **Techniques** (`techniques_page.gd`) · every session · The way · elsewhere (06) | Learn, rank up and slot techniques; Inner Arts and secret arts | The star chart: one constellation tree per element | The night sky (`sky_top` / `sky_bottom`), stars in `PALE_GOLD`, lit paths in `GOLD`, the element's hue on its tree (page.gd); technique icons (pixel, Style A, 48 and 64) | One tall constellation tree per element tab rising from a root star, learned stars lit and the rest dim; a lost-arts tab of scattered stars found by quests and exploration (decision 11); the loadout as two rings of four along the foot | A learned star ignites and its path draws in (0.4 s); changing tab pans the sky (0.3 s). Reduce: the star appears lit; tabs fade | 76 px slots for the loadout, `bar_shell` with stops |
| 16 | **Spirit Animals** (`pets_page.gd`) · every session · Beasts · brief (10 exists) | Care for, grow, breed and arm the animals | The beast stable: stalls with half-doors, each animal looking over its door | Stall timber `wood` with `SURFACE.straw` bedding; name boards; the yard in `SURFACE.soil`. Art: stall doors (pixel prop); creatures (existing sheets); straw (page.gd) | A column of stall half-doors down the left, each with its animal's head over the door and a name board; the chosen animal out in the yard at large scale with its growth path as stepping stones and its bond as hearts on its collar; care, gear and the nest on the tack wall at the right | Animals idle in their stalls; choosing one opens its door and it walks out (existing walk frames, 0.4 s). Reduce: the yard figure changes with a fade | 76 px slots for gear, `bar_shell` with stops |
| 17 | **Mail** (`mail_page.gd`) · every session · Records · **drawn here** (22) | Read letters; claim what they carry | The letter case: sealed envelopes in a stack, and the open letter unfolded on the desk with its parcel tied on | Envelopes in `scroll` paper with a `BLOOD` wax seal while unread; the letter with its two fold creases; `SURFACE.hemp` string; the desk `wood_dark`. Art: `envelope` and `letter_sheet` (HD nine-slices with crease shading); the wax seal (pixel, 32 px); string (page.gd) | A fanned stack of envelopes down the left, newest on top, unread ones sealed, those that carry something tied with string; the open letter large on the right, unfolded, with the sender's line, the words in ink and the sender's name at its foot; what it carries tied beneath it as a parcel, Claim as untying | Choosing an envelope slides it out and the letter unfolds (0.3 s, the two creases opening); a claim unties the string and the goods fly to the bag chip (0.3 s). Reduce: the letter fades in; goods are counted without the flight | 76 px slots, purse pills, primary and secondary buttons |
| 18 | **Crafts** (`crafts_page.gd`) · every session · The workshop · brief (15 exists) | Cook, refine, forge, inscribe, trace, chart, build | The hearth: each trade's vessel on its fire (pot, cauldron, anvil, plate, paper, chart, hull) | Hearth brick `SURFACE.stone` with `ember` fire; the vessel's metal. Art: stations (existing props); fire (existing FX); the step strip (page.gd) | The station centred over its fire with the ingredients on its rim; the steps as a strip across the top; the controls at the right change with the step and nothing else moves | Fire flickers; a finished craft lifts out in a puff (0.4 s). Reduce: no puff, the product appears | 76 and 48 px slots, primary button, heat gauge |
| 19 | **Storage** (`storage_page.gd`) · every session · The market · brief | Move things between your gourd and the account's chest | The storehouse chest: an iron-bound camphor chest with its lid thrown open, beside your gourd's mouth | Camphor `wood` with `BRONZE` bands, a `SURFACE.lacquer` lining inside the lid. Art: `storehouse_chest` (HD fixed asset, the raised lid in perspective); grids (kit) | The open chest over the right two-thirds, its lid raised behind the grid, the Treasury's added rows as a second tray; your gourd's mouth at the left with its grid; a tap moves a thing across | The lid swings open on opening (0.3 s); a moved item arcs across (0.2 s). Reduce: fade; items move without the arc | 76 px slots |
| 20 | **Teleport** (`teleport_page.gd`) · every session · Stone and bronze · brief | Travel to a known stone for a shard | The geomancer's compass: the stones placed on its rings by their bearing from here | A `BRONZE` disc with a `SURFACE.lacquer_black` face, rings ruled in `GOLD`, names in `PALE_GOLD` (page.gd) | A large round compass left of centre: its needle points to the stone you touched; the known stones sit on the outer ring at their bearings; the chosen stone's line and cost at the right | The needle swings to the chosen stone (0.4 s, damped); Teleport spins the rings once (0.5 s) into the fade. Reduce: the needle snaps; fade | Primary button, purse pill |
| 21 | **Notice Board** (`notice_page.gd`) · most days · Records · brief | Take bounties; read the town's requests and sightings | Wanted posters pasted under the eave of the town's notice wall | Weathered boards `wood` under a strip of `JADE_SHADOW` tiles; posters in `scroll` paper with `PAPER_INK`, the reward stamped in `BLOOD`. Art: the eave (pixel strip); `poster` (HD nine-slice, curling corners); portraits from the target's sprite | Three large posters side by side under the eave, each dominated by its target's portrait, the name large and the reward stamped; the Take strip at each poster's foot to tear off; the Board tab's sightings as smaller placards | Taking a bounty tears its strip off (0.25 s). Reduce: the strip fades | Primary button |
| 22 | **Calendar** (`calendar_page.gd`) · most days · Records · **drawn here** (19 v2) | When and where: the season, the week's events, the tide, the weather | The yellow almanac: one sheet for the week, ruled in red | `SURFACE.almanac` paper with `PAPER_INK` words; `SURFACE.cinnabar` header band and `BLOOD` rules and seals; the season wheel (page.gd, all of it) | One broad almanac sheet: a red header with the season wheel (four quarters, the current one lit with its time left) and today's day; seven day columns ruled in red with today's first and shaded; each world event a red seal on its day; the Beast Tide a dark ribbon across the week; the weather as the last row; the chosen event's slip with Go there in the right margin | Next week flips the sheet up (0.3 s); a live event's seal glows. Reduce: the sheet cross-fades; the seal is steady | Primary button |
| 23 | **Works** (`works_page.gd`) · most days · The post · **drawn here** (14 v2) | Build the account's works that serve every post | The curio cabinet: seven works as seven objects in the compartments of an irregular bamboo shelf | `SURFACE.bamboo` lattice (page.gd); each work an object (pixel, 64 px Style A: the manual, the seal, the stele, the favour, the furnace, the flag, the mirror); hanging labels in `SURFACE.hemp`; the tray `wood_dark` | An irregular lattice shelf across the top (compartments of different sizes, one work each, its state on a hanging label, locked ones dark behind a lattice screen with the quest and giver that open them); the chosen work's list on the tray below; the account's totals as the cabinet's inventory slip at the right | The chosen object lifts out of its compartment onto the tray (0.25 s); inscribing presses a seal mark (0.2 s). Reduce: the tray fades; the mark appears | Primary button, 48 px compact slots for costs |
| 24 | **Your Sect** (`your_sect_page.gd`) · most days · The sect · brief (11 exists) | Found and raise the sect; disciples, expeditions, territory | The courtyard under construction: the grounds as they stand, raised halls solid and the rest as scaffold outlines | The room's own art (existing backdrop layers); scaffolds in dashed `BRONZE` (page.gd); disciples (Avatar) | A wide panorama of the grounds across the top half, buildings where the room places them, disciples in the yard and candidates at the gate; the sect level bar with its stops under it; the chosen building, the disciples and beyond-the-walls cards along the foot | Raising a building draws its scaffold solid from the ground up (0.5 s); disciples idle. Reduce: the building appears | Primary button, `bar_shell` with stops |
| 25 | **Sect** (`training_sect_page.gd`) · most days · The sect · brief | Rank, contribution, promotion trials, missions, the sect shop; the role's tree | The Sect Hall's seats seen from its door | Receding floor in `wood_dark`, red pillars `SURFACE.lacquer`, cushions coloured by rank from tokens (`HOLLOW`, `JADE`, `GOLD`, `PALE_GOLD`), your seat lit. Art: the hall interior (pixel plate); seats (page.gd) | One-point perspective: the floor recedes to the master's dais at the top centre; ranks are rows of seats, nearer rows lower; your seat marked, the next rank's row lit with its price and gain; Missions and the Sect Shop as the hall's side doors; the Role tab turns to the teaching boards on the side walls | Promotion walks your seat forward one row (0.4 s). Reduce: the seat appears in its row | Primary button |
| 26 | **Codex** (`codex_page.gd`) · most days · Records · elsewhere (18) | Look things up; fill the collection; achievements, paths above, seasons; the old scrolls | The bound bestiary: a thread-bound book open on its lectern. The Old Scrolls tab: an ink rubbing of an old stele | Book paper `scroll` with `JADE_SHADOW` cloth covers and thread binding (HD, a two-page spread with a gutter); ribbon bookmarks as tabs. Old Scrolls: `SURFACE.rubbing` (near-black paper) with `PAPER` characters, rubbed edges (page.gd noise) | A two-page spread with ribbon bookmarks down its edge for the tabs; the Collection a page of cards per region. Old Scrolls fills the spread with one rubbing, white on black, the only inverted surface in the game | Pages turn with a curl (0.35 s); the rubbing darkens in as if dabbed (0.4 s). Reduce: cross-fade | `bar_shell` with stops |
| 27 | **Companions** (`companions_page.gd`) · most days · Bonds · brief | Choose who walks beside you; hearts, gifts, duels, bonds | Moon gates in a whitewashed garden wall, a friend standing in each | `SURFACE.plaster` wall under `JADE_SHADOW` tiles; hearts as knots on a `RED` thread (page.gd); companions (Avatar) | A white wall with a row of round moon gates, a companion standing full-length in each; the two beside you have lanterns lit over their gates; each gate's hearts as knots on the red thread beneath it; the chosen friend's actions under their gate | Choosing a friend lights their lantern (0.2 s); a new heart ties a knot (0.3 s). Reduce: lantern lights; the knot appears | Primary and secondary buttons |
| 28 | **Gift** (`gift_page.gd`) · most days · Bonds · 21_gift | Give one gift a day and see the heart move | A red-lacquered gift tray held out with both hands | `SURFACE.lacquer` tray with a `GOLD` rim and compartments (HD nine-slice `gift_tray`); the liked gift marked with a `HEART` tag | A long shallow tray of compartments above the talk, the liked gift tagged; the heart bar under the speaker's words | The chosen gift lifts from the tray toward the speaker (0.3 s); the heart bar fills. Reduce: fade; the bar is set | 76 px slots, primary button |
| 29 | **Garden** (`garden_page.gd`) · most days · The workshop · brief | Plant, water, feed and harvest beds; dry and steep on racks | Terraced herb beds on the hillside, seen from above | `SURFACE.soil` beds with `SURFACE.stone` terrace edges; herbs growing in four stages (pixel, from the herb icons); grade stakes; the tool basket (pixel) | Terraces stepping down the page, each bed a plot with its herb drawn at its stage and its grade on a stake; the water, Spirit Soil and dew in a basket at the top; the Racks tab as drying racks with trays | Watering darkens the soil (0.3 s); a harvested herb pops into the basket. Reduce: the soil changes at once, no pop | 76 px slots, primary button |
| 30 | **Workshop** (`workshop_page.gd`) · most days · The workshop · brief | Formations, appraisal, the infirmary, puppets, restoration, teaching | The artisan's bench with its tool wall | A pegboard in `wood` with each tool's painted outline in `INK` at 40%; the bench top `wood_dark` seen from above. Art: six tools (pixel, Style A 64: compass, loupe, needle roll, chisel, brush, pointer); the wall (page.gd) | A tool wall across the top where each tab is a hung tool with its outline behind it; the bench top below, seen from above, with the job laid on it (the blueprint, the item under the loupe, the patient's card, the puppet frame, the torn manual, the disciple's slate) | Choosing a tab takes the tool off its hook, its outline stays (0.2 s), and lays it on the bench. Reduce: fade | 76 px slots, primary button |
| 31 | **Fishing** (`fishing_page.gd`) · most days · Leisure arts · brief | Cast, wait, strike, keep the line in the band | The river in section from the bank | `SURFACE.water` with light bands, the bank in `SURFACE.soil`, a bamboo rod; the tension band in `GOLD` on the rod's arc (page.gd); fish (existing icons) | A vertical cut through the water: the surface near the top with the float, the fish below, the rod's arc from the bank at the left; the band of good tension marked on the arc | Ripples at the float; the bite dips it (the game's own cue); the rod bends with tension. Reduce: ripples still; the dip and the bend stay, since they are the game | Primary and secondary buttons |
| 32 | **Characters** (`characters_page.gd`) · most days · The sect · brief | See every character; set this one's idle task; switch | A cord of name lanterns, one paper lantern per disciple slot | Red paper lanterns (`SURFACE.cinnabar` panels with `GOLD` ribs) on a dark cord; each lantern carries its disciple's bust; tassels with the idle task's glyph (lanterns page.gd, glyphs pixel, busts from the layers) | A cord swung across the page in a shallow arc with its lanterns: lit ones are characters (name, realm, the idle task on the tassel), a dim one is an open slot, bare hooks are locked slots with their gate on a tag; the chosen lantern lowered with its idle task below | Lanterns sway; the chosen one lowers (0.25 s). Reduce: still lanterns; the lowered one fades in | Primary and secondary buttons |
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
| 44 | **Pouches** (`pouches_page.gd`) · now and then · The post · brief | Tailor Xun deepens one category's pouch at a time | The tailor's chalked patterns on a bolt of cloth | `SURFACE.cloth` with chalk lines in `PAPER` at 70%, a bamboo ruler (page.gd); pouch icons (existing) | Seven pouch patterns chalked on dark cloth, each drawn as its compartments with the next tier dashed round it; the ruler along the top edge marks the tiers; Sew at each pattern's foot | Sewing runs a stitch round the pattern (0.4 s). Reduce: the pattern turns solid | Primary buttons |
| 45 | **Emotes** (`emotes_page.gd`) · now and then · Leisure arts · brief | Pick a gesture | The shadow-puppet screen | A lamp-lit paper screen (`scroll` warmed by `ember`) in a `wood` frame; each emote's glyph as an `INK` silhouette (existing emote icons tinted) | A lit screen with each emote's puppet standing along it in two rows; locked emotes as grey outlines with their achievement | The chosen puppet hops (0.2 s). Reduce: no hop | Secondary buttons |
| 46 | **Chess** (`chess_page.gd`) · now and then · Leisure arts · brief | Solve today's problem | The Go board at the insight stone | `board`, `board_edge`, `board_line`, the stones (page.gd, as today) | A square 9 × 9 board in the centre with the four lettered points; the answers beneath | A stone is placed with a click. Reduce: as is | Primary buttons |
| 47 | **Guqin** (`guqin_page.gd`) · now and then · Leisure arts · brief | Play a short piece | The zither | `wood`, `wood_dark`, `bridge`, `peg`, `hui` (page.gd, as today) | Five strings across the page, notes gliding to the bridge at the left, the pegs as the buttons | Strings shiver when plucked (the game). Reduce: notes still glide; the shiver is smaller | Primary button |
| 48 | **Create Disciple** (`shell_screens.gd` creator) · now and then · Shell · brief | Make a new character: look, origin, name | The dressing screen: a folding screen behind the new disciple with the garments hung over it | Three panels of `SURFACE.river_lacquer` with `GOLD` edges (HD fixed asset); garments over its top edge (their icons); the name on a paper tag | A three-panel folding screen across the back with the figure before its middle panel; hair, robe, trousers and shoes hung over the screen's top with ◀ ▶ on each; the origin as a slip on the left panel; the name tag at the figure's feet; Begin at the right | A changed garment flutters on the screen (0.2 s). Reduce: no flutter | Primary and secondary buttons |

---

## 4. How uniqueness was checked

1. **Concepts.** Each row names one physical thing. The 48 things, sorted by their head noun, repeat none: archway,
   board (Go), board (mission), book, cabinet (curio), cabinet (drawers), calabash, chest, cliff, coil, compass,
   counter, courtyard, cylinder, desk, discs, gates (moon), hall (plaques), hall (seats), hearth, lamp, landscape,
   lanterns, letter case, mountain, pagoda, paper strip, patterns (chalk), pit, posters, rubbing (a tab), screen
   (dressing), screen (puppet), scroll (portrait), sheet (almanac), skiffs, stable, stage, star chart, steelyard,
   sword, tool wall, terraces, tray, urn, window (barred), windows (lattice), zither, river section. Where a noun
   repeats, the thing differs in kind (two halls: one hung with plaques, one of seats; two cabinets: an open curio
   shelf, a chest of drawers; two screens: a dressing screen, a lit puppet screen), and each such pair sits in
   different families with different layouts.
2. **Layout signatures.** Each signature was reduced to a silhouette code, the dominant shape and where it sits
   (for example "calabash, centre" or "one-point perspective, whole window"), and the codes were compared pair by
   pair. The near-collisions found while writing, and how each was settled:

   | Near-collision | Settled by |
   |---|---|
   | Rows of figures in frames: Selection, Roll-Call, Companions, Characters | Each keeps a frame with its own outline: skiffs on water with no frame at all; rectangular lattice windows holding scenery; round holes in a white wall; lanterns with busts only, no full figures |
   | Big circles: Teleport, Beast Arena, Companions, Welcome Back, and first drafts of the creator (a mirror) and the emotes (a wheel) | The creator became a folding screen and the emotes a lit screen; what is left differs in kind: rings with ticks (compass), an oval of sand ringed with banners (pit), a row of small circles (gates), a spiral (coil) |
   | A bar across the top: Relations (beam), a first draft of Welcome Back (an incense trough), Workshop (tool wall), Pouches (ruler), Notice Board (eave), and Mercy's first draft (a blade laid flat) | Welcome Back became a spiral and Mercy's sword stands upright; the beam is the Relations page's whole subject, while the wall, the ruler and the eave are edges of something larger |
   | A big sheet with a stack: first drafts of the Calendar (a tear-off pad) and the Notice Board (a stack of posters), and the Mail (envelopes) | The Calendar became one broad ruled sheet and the Notice Board three posters side by side; only the Mail keeps a fanned stack |
   | Fans from a point: Fates (sticks) and a first draft of Emotes (a folding fan) | Emotes became the puppet screen |
   | Grids of receptacles: Bag, Storage, and first drafts of Characters (a token case) and Core Exchange (a board of wells) | Characters became the lanterns and Core Exchange the urn; the Bag's grid sits in a calabash, the Storage's under a raised lid |
   | Vertical stacks: Trial Tower (pagoda), Cultivation (stair) and a first draft of the Beast Arena (a ladder of banners) | The arena became the pit; the stair is diagonal and the pagoda a narrow column with eaves |
   | Painted places: World map, Your Sect, Title | The map is full-bleed with tabs at its foot; Your Sect is the room itself in a strip with cards below; the Title is one cliff face |
   | Figure with the worn slots: Bag and Character (decision 8 asks for both) | The Bag rings the figure with its slots on a dais beside the calabash; the Character paints the figure inside a hanging scroll with the slots set in the brocade |
   | Paper pages in one family (Records, seven pages) | A strip, a board of slips, a painting, an envelope stack, a ruled sheet, three posters and a book: no two share a silhouette |

3. **The contact sheets.** Every row's layout signature is drawn as a thumbnail in `docs/mockups/page_identity_sheet.png`
   and its two companions (§8). The sheets were looked at at 1x, and again blurred and in grey (a squint test: a
   Gaussian blur of 6 px), which leaves only the silhouettes; no two thumbnails blur to the same shape.

---

## 5. Art to make

| Art | For | Kind | Notes |
|---|---|---|---|
| `gourd_well` | Bag | HD fixed asset | The calabash: two bulbs and a waist, a lacquer ramp from `SURFACE.gourd`, a `GOLD` lip, the cord; the grid's corners inside the lower bulb (a superellipse); its inside left open for `SURFACE.space` |
| `wood_tag` | Bag (the item tag), Works (labels) | HD nine-slice | A tag with a clipped top and a cord hole, `SURFACE.gourd_dark` |
| `portrait_scroll` | Character | HD nine-slice (vertical) | Brocade mounting in `SURFACE.silk`, a paper centre, rollers with `GOLD` caps |
| `paper_slip` | Quests | HD nine-slice | A slip with a torn top edge and a pin shadow |
| `envelope`, `letter_sheet` | Mail | HD nine-slices | Crease shading across the letter; the envelope's flap |
| `poster` | Notice Board | HD nine-slice | Curling lower corners |
| `gift_tray` | Gift | HD nine-slice | Compartments by a repeated centre |
| `storehouse_chest` | Storage | HD fixed asset | The raised lid in perspective with its lining |
| Dressing screen | Create Disciple | HD fixed asset | Three panels |
| Book spread | Codex | HD fixed asset | Two pages and a gutter (with the 18 redraw) |
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
| Eave strip | Notice Board, Trial Tower | Pixel tiles | `JADE_SHADOW` tiles |
| Post-house basket | Roll-Call | Pixel prop | Empty, half, full |
| Seven works objects | Works | Pixel, Style A 64 | Manual, seal, stele, sealed favour, furnace, flag, mirror; some can start from today's works icons |
| Six tools | Workshop | Pixel, Style A 64 | Compass, loupe, needle roll, chisel, brush, pointer |
| Bronze pin, wax seal, done stamp | Quests, Mail | Pixel, Style A 32 | |
| Herb stages | Garden | Pixel | Four growth stages per herb family |
| Everything else in §3 marked page.gd | 30 pages | page.gd | Drawn from tokens: the dais and ring, the board's grain, the almanac's rules and seals, the season wheel, the compass rings, the lanterns, the lattice, the coil, the terraces, the stair, the stars, the threads, the chalk lines, the drawers and bells |

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
   on the drawers and the lanterns. `AudioDirector` keys are named with each page's P5 part.

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

Grade and quality colours were made for the dark fills and fail on paper (Superior #5aa7e8 on `scroll` is 2.4:1).
On a light surface a grade shows as a small chip in its colour with the word in `INK`, or by the slot's rim, never as
coloured words. `BLOOD` is the one red for words on paper (4.58 on `almanac`, 4.87 on `scroll`). The audit
(`tools/dev/ui_style_audit.py`) measures each new surface before it ships (style guide §1.4 rule 4).

---

## 8. Mockups made with this page

Rendered with `tools/dev/render_mockups.py` from `docs/mockups/src/`; numbers from the valley_run character's
checkpoints, taken as frozen copies of `user://valley_cp/<section>` at 01:33 UTC on 2026-09-27 and read from the save
and from a capture of the real page on that copy (the build at this page's commit). Listed in `docs/mockups/README.md`.

| PNG | Page |
|---|---|
| `page_identity_sheet.png`, `page_identity_sheet_2.png`, `page_identity_sheet_3.png` | The contact sheets: every row of §3 as a labelled thumbnail of its concept, in the order of §3 |
| `07_bag_full_v2.png`, `08_bag_empty_v2.png` | Bag: the spirit gourd, full (ls6_end) and early (bf2) |
| `09_character_v2.png` | Character: the portrait scroll (ls6_end) |
| `12_quests_v2.png` | Quests: the mission board (ae_end) |
| `14_works_v2.png` | Works: the curio cabinet (ls6_end) |
| `19_calendar_v2.png` | Calendar: the almanac (qu5) |
| `22_mail.png` | Mail: the letter case (ls6_end) |
| `23_settings.png` | Settings: the cabinet of drawers (ls6_end) |

---

## 9. For the user to decide

1. The catalogue as a whole: the concept and layout signature of each row, and the families.
2. Whether a page may drop the shared `major_window` frame for its own surface (as the drawn mockups do), keeping the
   close button, the title's lettering and the standard window rect; or whether the frame stays and only the inside
   changes.
3. The rows for pages being redrawn elsewhere (6 Techniques, 13 Roll-Call, 16 World Map, 17 Shop, 18 Codex and Old
   Scrolls) state an identity for each; they are to be reconciled with those redraws when they land, and the Old
   Scrolls rubbing proposed here is the "nothing else looks like it" surface only if the redraw does not choose
   another.
4. The new `SURFACE` tokens of §7.
5. For each drawn mockup, what `docs/mockups/README.md` lists under it.
