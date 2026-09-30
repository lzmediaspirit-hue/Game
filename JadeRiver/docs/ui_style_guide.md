# UI style guide (P4)

The style guide of phase P4 in `docs/roadmap_master_ui.md` §3 (rows U22–U29). It writes down the rules the approved
mockups 00–05 follow (`docs/mockups/`), measures the build against them, and lists the code changes that apply them.
It keeps the decisions of §5 and §6 of the roadmap: serif words with Pixelify numerals (C6), HD frames with pixel icons
and motifs inside them (C7), the `UiKit` token table as the Theme resource plan (C8), no portrait roundel on the HUD
(decision 6), icon Style A, "HD pixel" (decision 7), the character's figure on the Bag and Character pages (decision 8),
and version 1.2 (decision 9).

Conventions:

- Paths are relative to `JadeRiver/`. `file:line` refers to commit 723fc5e, the build branch after the architecture
  review (which removed `Page.SAFE` and `UiKit.draw_frame` and unified `UiKit.span`).
- Sizes are screen pixels of the 1280 × 720 canvas (`project.godot`). "Layout size" is the size a page asks for;
  "drawn" is what `UiKit.size_for` makes of it.
- Measurements come from `tools/dev/ui_style_audit.py`, a read-only script added with this page:
  `python3 tools/dev/ui_style_audit.py [section …] [--root DIR]` prints the tokens, the sampled panel fills, the
  contrast of every text colour, the colour literals, text sizes, windows, icon sizes, list pitches, plurals and
  durations. Re-run it after every change in §11.
- Contrast is the WCAG 2 ratio. Body text needs 4.5:1. Text drawn at 20 px or larger needs 3:1. Disabled labels are
  exempt in WCAG; this guide sets a 3:1 floor for them anyway, so a player can read the reason.
- Nothing in `scripts/`, `data/` or `art/` changes with this page. §11 is the list for the second step, which has
  landed: §12 records what each step changed and what the audit measures now.

## 0. What is still open from the P2 review

The P2 bug pass and P4a closed part of `docs/review-v12.md` (d) and `docs/ui_inventory.md` §4.5. This is what the code
at 723fc5e still shows.

| # | Status at 723fc5e | Section |
|---|---|---|
| G1, I7 tap targets | Pages fixed (P4a, `Page.MIN_TAP`, `page.gd:13`). Four HUD targets are still under 48 px | §7 |
| G2 numerals | Fixed (`UiKit.PIXEL_NUMERALS_MIN`, `ui_kit.gd:223`) | §3 |
| G3, G4 HUD crowding, world labels | Fixed in P5a (§9 "As built") | §9 |
| G5 bars without stops | Open, owned by P5 | §9 |
| G6, I1 two kits, procedural widgets | Open: the empty-slot motif and every HUD ring are still pixel-kit or procedural | §5 |
| I2 icons at non-integer scales | Open: 66 of 86 literal icon sizes are off the allowed set (audit `icons`); slots show 64 px icons at 52 | §8 |
| I3, I4 states and selection | Fixed (derived `selected`, `disabled`, `pressed`, `ui_kit.gd:136-153`). Two pages use `selected` to mark "you", and Settings uses `pressed` for "on" | §6 |
| I5 colour literals | Open: 64 hex literals (37 in 12 pages, 27 in `hud.gd`) and 55 float `Color()` literals | §1.6 |
| I6 text under `MIN_SIZE` | Drawn at 14 since B21, but 15 call sites still ask for 13 or 10, and one label is fitted at 13 and drawn at 17 | §3 |
| I8 spacing | Open: every place I8 lists | §2 |
| I9, I10 | Fixed | — |
| I11 numbers | Fixed on the HUD (`UiKit.pool_values`). Damage numbers are still ungrouped (`world.gd:408`) | §4 |
| I12 plurals | Partly fixed (`Tx.plural`, 9 `_one` keys). 105 strings print a count before a plural noun with no `_one` form | §4 |
| I13 window sizes | Open: 13 pages set their own window | §2 |
| I14 durations | Partly fixed (`UiKit.span`, `ui_kit.gd:317`). Nine places still format durations their own way | §4 |

## 1. Palette roles

### 1.1 The `UiKit` tokens

`UiKit` defines fifteen colours (`scripts/ui/ui_kit.gd:11-25`). "Text" says whether the token may colour words; the
ratio is on the lightest page fill (`minor_panel`, lightest texel `#0f2d34`, §1.3). "Uses" counts `UiKit.<TOKEN>` in
`scripts/`.

| Token | Hex | Line | Role | Text | Ratio | Uses |
|---|---|---|---|---|---|---|
| `INK` | #071015 | 11 | Outlines of text and glyphs, shadows, the darkest fill | Only on light faces | — | 55 |
| `RIVER_NIGHT` | #0a2027 | 12 | The flat fallback frame (`ui_kit.gd:169`) | No | — | 0 |
| `DEEP_TEAL` | #0d3035 | 13 | Placeholder and disc fills (`page.gd:286`, `hud.gd:1462`, `emotes_page.gd:20`) | No | — | 3 |
| `JADE_SHADOW` | #15514f | 14 | The Early stage band (mockup 04); the empty-slot motif (§8) | No | — | 0 |
| `JADE` | #2c9e8f | 15 | Progress fills, met-requirement dots, the scroll thumb (`page.gd:375`), the Middle band | No | 4.42 | 27 |
| `BRIGHT_JADE` | #67d6bd | 16 | **Positive**: gains, done, ready, owned; allies' HP | Yes | 8.25 | 125 |
| `BRONZE` | #9a6a35 | 17 | Rules and locks: the heading rule (`page.gd:230`), the lock (`page.gd:154`); the Late band | No | 3.10 | 11 |
| `GOLD` | #e5b84c | 18 | **Heading** (`page.gd:229`) and **accent**: main quest, bottleneck, elites, merit; the Peak band | Yes | 7.81 | 154 |
| `PALE_GOLD` | #ffe6a1 | 19 | **Title and emphasis**: window titles, primary labels, the selected tab, names, key values | Yes | 11.82 | 242 |
| `PAPER` | #e8e1cf | 20 | **Primary text** (`Page.text` default, `page.gd:205`), secondary labels | Yes | 11.14 | 188 |
| `MIST` | #afc9d1 | 21 | **Secondary text**: notes, hints, lock reasons, captions | Yes | 8.37 | 390 |
| `RED` | #e45858 | 22 | **Negative fill**: danger dots, count badges, the ready seal, foes on the minimap | No: use `RED_TEXT` | 4.04 | 82 |
| `QI` | #32bed1 | 23 | **Qi**: bars, Qi numbers, the short-of-Qi ring | Yes | 6.52 | 12 |
| `SOUL` | #9b78d1 | 24 | **Soul**: bars, insight bars, the upkeep arc | No: use `SOUL_TEXT` | 4.15 | 22 |
| `HOLLOW` | #87949a | 25 | **Disabled**: disabled labels (`page.gd:165`), locked tabs, unknown entries | Yes | 4.66 | 65 |

The roles in short. Primary text `PAPER`; secondary `MIST`; heading `GOLD`; title and emphasis `PALE_GOLD`; accent
`GOLD`; positive `BRIGHT_JADE`; negative `RED` (fill) and `RED_TEXT` (words); warning `WARNING`; disabled `HOLLOW`; Qi
`QI`; Soul `SOUL` and `SOUL_TEXT`; Blood `BLOOD`; HP `HP`. `RED_TEXT`, `WARNING`, `SOUL_TEXT`, `BLOOD` and `HP` are
proposed in §1.5. Panel fills are the HD kit's (§1.3); `RIVER_NIGHT` is only the fallback.

### 1.2 Grade and quality colours

The colours live in `data/grades.json` (written by `tools/data/stats.py:512` and `:515`) and are read by
`UiKit.quality_color` and `UiKit.grade_color` (`ui_kit.gd:282`, `:285`). A missing key falls back to `#e8e1cf`. Each
grade and quality is a tier; its colour colours the item's name and the slot's quality rim (`page.gd:289`).

| Grade | Hex | `grades.json` | Ratio | | Quality | Hex | `grades.json` | Ratio |
|---|---|---|---|---|---|---|---|---|
| plain | #b9b2a0 | 67 | 6.88 | | flawed | #9aa3a3 | 53 | 5.63 |
| common | #e8e1cf | 68 | 11.14 | | common | #e8e1cf | 54 | 11.14 |
| earth | #67d67a | 69 | 7.94 | | fine | #67d67a | 55 | 7.94 |
| heaven | #6fb8f0 | 70 | 6.77 | | superior (and rare) | #5aa7e8 | 56, 62 | 5.62 |
| mystic | #b07ce8 | 71 | 4.77 | | perfect (and epic) | #b07ce8 | 57, 63 | 4.77 |
| spirit | #5ee0e8 | 72 | 9.20 | | relic (and primordial) | #e5b84c | 58, 64 | 7.81 |
| sage | #d8c27a | 73 | 8.25 | | pill_grain | #e5b84c | 59 | 7.81 |
| sovereign | #e8a24c | 74 | 6.71 | | pill_halo | #e8764c | 60 | 4.93 |
| will | #f3e3a6 | 75 | 11.31 | | pill_soul | #f2e6ff | 61 | 12.14 |
| sphere | #8f7ae0 | 76 | **4.17** | | | | | |
| law, monarch, inner_heaven | none | — | falls back to common | | | | | |

Two faults: `sphere` is under 4.5:1, and the three highest grades have no colour, so a Law item reads as Common. §1.5
proposes values. Quality never shows by colour alone: pills also carry the corner mark of `_pill_glow`
(`page.gd:310`), and gear carries its material kit (§8).

### 1.3 The fills under text

Sampled from `art/ui/hd/*.png` inside each asset's nine-slice centre and composited over `INK` (audit `fills`). The HD
panels are a vertical gradient from `TEAL_TOP` #11343b to `TEAL_BOT` #081c22 (`tools/ui/build_ui_hd.py:48-49`, `:200`);
the stretched centre is lighter than the bottom.

| Fill | Mean | Lightest (p95) | Carries |
|---|---|---|---|
| `major_window` | #0c282e | #0e2d33 | Every page's words |
| `minor_panel` (and its derived `selected`) | #0c282e | #0f2d34 | Cards, rows, the HUD player panel |
| `minor_panel` `disabled` (derived) | #081a1f | #081c21 | Disabled rows |
| `slot` | #0a2227 | #0c282e | Counts, placeholder letters |
| `toast` (alpha 0.97) | #0a2127 | #0c242a | Toasts, the fortune card, the event card |
| `currency_pill` | #0a2228 | #0c262c | Currency values |
| `realm_badge` | #0e2e34 | #0f3237 | The Cultivation level |
| `tab` / `tab` `selected` | #0d2930 / #18484a | #0e2d35 / #215657 | Tab labels |
| `button_secondary` normal / pressed | #13393f / #0f3238 | #194349 / #10363c | Secondary labels |
| `button_primary` normal / pressed | #2c9688 / #1d6f66 | #42b1a1 / #248175 | Primary labels |
| `title_plaque` | #166058 | #3c9386 (top of the face) | Page titles, the dialogue speaker |
| `minimap_frame` header band | #143d43 | #18464c | The room name |
| `dialogue_box` | #e8ddc2 | #ede3ca | Dialogue words (`#2b2118`) |

The lightest fill any text colour may sit on is `minor_panel` (#0f2d34). It is the reference in §1.4. `tooltip` is in
both kits but drawn nowhere.

### 1.4 Contrast measured

**Text colours on the page fills.** Every token and literal that colours words, on `major_window`, `minor_panel`,
`slot`, `toast` and `currency_pill` (audit `contrast`). The pairs under 4.5:1:

| Colour | Lowest ratio (on `minor_panel`) | Under 4.5:1 | Under 3:1 | Used as text today |
|---|---|---|---|---|
| `RED` #e45858 | 4.04 | Yes | No | 34 text calls (danger, unmet needs, costs) and the HUD log's warnings |
| `SOUL` #9b78d1 | 4.15 | Yes | No | `breakthrough_page.gd:24`, `inventory_page.gd:300` |
| `JADE` #2c9e8f | 4.42 | Yes | No | The risk line, `breakthrough_page.gd:51` |
| `BRONZE` #9a6a35 | 3.10 | Yes | On `realm_badge` (2.93) | Nowhere; keep it off words |
| grade `sphere` #8f7ae0 | 4.17 | Yes | No | Item names of that grade |

Every other text colour passes 4.5:1 on every page fill: `PAPER` 11.1, `PALE_GOLD` 11.8, `MIST` 8.4, `GOLD` 7.8,
`BRIGHT_JADE` 8.3, `QI` 6.5, `HOLLOW` 4.7, the sin red #e07a7a 5.0, merit #e8c872 9.0, orange #f0a040 6.8,
#e0a860 6.9, the side-quest blue #8fc8ff 8.2, the ally blue #8fd3ff 9.0, `hud.gd`'s own gold #d5bd85 7.9, and every
quality and grade colour but `sphere` (lowest: mystic and perfect #b07ce8, 4.77).

**Labels on their own fills**, at the size drawn:

| Label | Fill | Drawn | Lightest | Mean | Needs | Result |
|---|---|---|---|---|---|---|
| `PALE_GOLD`, primary button (`page.gd:164`) | `button_primary` | 22 (steps to 14) | 2.13 | 2.92 | 3.0 (4.5 at 14) | **Fails** |
| `PALE_GOLD`, primary pressed | `button_primary` pressed | 22 | 3.82 | 4.85 | 3.0 | Pass |
| `HOLLOW`, disabled primary (`page.gd:165`) | `button_primary` disabled | 22 | 2.64 | 3.11 | 3.0 floor | **Fails** the floor |
| `PALE_GOLD`, page title (`page.gd:115`) | `title_plaque` | 41 (layout 34) | 2.99 | 5.02 | 3.0 | **Fails** at the top of the face |
| `PALE_GOLD`, dialogue speaker (`dialogue_page.gd:66`) | `title_plaque` | 31 | 2.99 | 5.02 | 3.0 | **Fails** as above |
| `PALE_GOLD`, selected tab (`page.gd:147`) | `tab` selected | 20 | 6.74 | 8.29 | 3.0 | Pass |
| `PAPER`, tab / `HOLLOW`, locked tab | `tab` / derived disabled | 20 | 11.14 / 5.61 | — | 3.0 | Pass |
| `PAPER`, secondary button, at 22 and at 14 | `button_secondary` | 22, 14 | 8.30 | 9.59 | 4.5 | Pass |
| `HOLLOW`, disabled secondary | `button_secondary` disabled | 22 | 4.70 | 4.92 | 3.0 | Pass |
| `PALE_GOLD`, room name (`hud.gd:1620`) | `minimap_frame` header | 14 | 8.46 | 9.57 | 4.5 | Pass |
| `PALE_GOLD`, level (`cultivation_page.gd:43`) | `realm_badge` | 38 (layout 32) | 11.15 | 11.72 | 3.0 | Pass |
| `PALE_GOLD` / `BRIGHT_JADE`, currencies (`hud.gd:1413`, `:1417`) | `currency_pill` | 18 | 12.85 / 8.98 | — | 4.5 | Pass |
| #2b2118, dialogue words (`dialogue_page.gd:97`) | `dialogue_box` | 20 | 12.33 | 11.63 | 3.0 | Pass |

**Words over the world.** Text drawn with `UiKit.draw_outlined` (`ui_kit.gd:225`) carries a 3–4 px ink outline and
is measured against `INK`: every text colour passes (lowest `RED`, 5.33). Words drawn with only the drop shadow over the
scene have no fixed background. Two translucent plates exist:

| Plate | Alpha | Over a white sky: MIST / PAPER / GOLD | Over mid grey | Alpha for MIST 4.5:1 over white |
|---|---|---|---|---|
| Quest tracker (`hud.gd:1556`) | 0.55 | 2.47 / 3.28 / 2.30 | 5.88 / 7.82 / 5.49 | 0.72 |
| Nameplate (`ui_kit.gd:240`) | 0.62 | 3.15 / 4.19 / 2.94 | 6.65 / 8.85 / 6.21 | 0.72 |

The HUD log (`hud.gd:1866`) sits on no plate at all.

Rules that follow:

1. A text colour passes 4.5:1 on `minor_panel`'s lightest texel, or it is only drawn at 20 px and up and passes 3:1.
2. `JADE`, `BRONZE`, `RED`, `SOUL`, `HP`, `BLOOD` and `HEART` never colour words. Words take `BRIGHT_JADE`, `RED_TEXT`
   and `SOUL_TEXT`.
3. Words over the world are outlined (`draw_outlined`) or sit on a plate at alpha 0.72 or more.
4. A new fill that carries text is measured with the audit before it ships.

### 1.5 Proposed tokens

New tokens keep the hue and saturation of the colour they replace. The lightness is raised to about 4.8:1 on the
reference fill, which leaves room for anti-aliasing and the Small text size (the audit prints both the 4.5:1 and the
4.8:1 variant).

| Token | Value | Ratio | Replaces | Role |
|---|---|---|---|---|
| `RED_TEXT` | #e87070 | 4.83 | `RED` as text; the sin red #e07a7a (8 places) | Negative words: danger, unmet needs, costs, sin |
| `SOUL_TEXT` | #a586d6 | 4.83 | `SOUL` as text | Soul words |
| `WARNING` | #f0a040 | 6.79 | #f0a040 (4), #e0a860 (2), #c8923e (bar), `badge_color` "orange" | Warning: a soft need, moderate risk, a meter past its mark |
| `HP` | #c2474f | fill | `hud.gd:1495`; #ae5360 in the legacy panel | The player's HP fill (HUD and Character page) |
| `BLOOD` | #b3202e | fill | `hud.gd:1507`; #d0283c (`cultivation_page.gd:250`); the boss trough #3a1418 as `Color(BLOOD, 0.3)` | The Blood path, the heart-demon meter |
| `HEART` | #e05a6e | fill | `ui_kit.gd:377`, `gift_page.gd:37` | Affection |
| `SKY` | #8fd3ff | 8.95 | #8fc8ff (`hud.gd:1559-1560`), #8fd3ff (`hud.gd:1707`), #8fd6ff (`hud.gd:1973`) | Allies and side quests |
| `HUD_LABEL` | #d5bd85 | 7.92 | `hud.gd:45` `GOLD`, which shadows `UiKit.GOLD` | The HUD's HP, QI and SL labels |
| `PAPER_INK` | #2b2118 | 12.33 on paper | `dialogue_page.gd:97` | Words on paper surfaces |
| `BAR_TROUGH` | #17242c | fill | `hud.gd:1371`, `:1983` | Bar troughs |
| `PLATE` | `Color(0.02, 0.06, 0.075, 0.72)` | MIST 4.5 over white | `hud.gd:1556` (alpha 0.55), `ui_kit.gd:240` (0.62) | Plates over the world |
| `DIM` | `Color(0.01, 0.03, 0.04)` | — | `page.gd:110` (alpha 0.72, modal 0.55) | The world dimmed behind a page |
| `SURFACE` | dictionary, §1.6 | — | The chess, zither, map-scroll, talisman and tribulation-sky literals | Drawn page surfaces |

No `JADE_TEXT`: the one place `JADE` colours words (the risk line, `breakthrough_page.gd:51`) takes `BRIGHT_JADE`
(8.25). The computed variant would be #2ea696 (4.85), too close to `JADE` to earn a token.

Data colours, in `tools/data/stats.py`: `sphere` #8f7ae0 → **#9a87e3** (4.81). The three grades past Sphere were
proposed here as #e98fc6, #ff9a7a and #d6f5ff; P7b gave them their colours first, and with no red, which is the game's
danger colour: `law` **#a8c4ff** (8.31), `monarch` **#e6b3f2** (8.37), `inner_heaven` **#f4f7ff** (13.56). They are
kept.

Kit faces: **decided, option C** (roadmap §6 decision 10, `docs/mockups/00b_button_faces.png`). The bright jade face
of `button_primary` and `title_plaque` approved in mockups 00 and 04 stays, and the kit is not rebuilt for it. Primary
labels (normal, pressed and disabled) and the titles on the plaque (page titles, the dialogue speaker) are drawn with
**a 2 px ink outline**, `UiKit.draw_inked` (`INK_OUTLINE` 2), and are measured against `INK`:

| Label | Fill | On the face alone (lightest texel) | Inked, on `INK` | Needs |
|---|---|---|---|---|
| `PALE_GOLD`, primary normal | `button_primary` | 2.13 | 15.6 | 4.5 (the label steps down to 14) |
| `PALE_GOLD`, primary pressed | `button_primary` pressed | 3.82 | 15.6 | 4.5 |
| `HOLLOW`, primary disabled | `button_primary` disabled | 2.64 | 6.2 | 3.0 (the floor) |
| `PALE_GOLD`, title and speaker | `title_plaque` | 2.99 | 15.6 | 3.0 (drawn at 31 and 41) |

The option B faces (the deeper jade #27897b → #0c3d38, measured at 4.64, 5.59, 3.48 and 3.81) were not built; their
preview PNGs, which only served the choice, are gone, and `00b_button_faces.png` stays as the record.

### 1.6 Literals and the token that replaces each (I5)

Hex literals at 723fc5e, grouped by value (audit `literals`):

| Literal | Places | Token |
|---|---|---|
| #e07a7a | `character_page.gd:255`, `cultivation_page.gd:265`, `fates_page.gd:36`, `mercy_page.gd:21`, `relations_page.gd:7`, `hud.gd:826`, `:842`, `:1104` | `RED_TEXT` |
| #e8c872 | `mercy_page.gd:20`, `relations_page.gd:6` | `GOLD` |
| #f0a040 | `breakthrough_page.gd:30`, `:51`, `cultivation_page.gd:93`, `ui_kit.gd:289` | `WARNING` |
| #e0a860, #c8923e | `cultivation_page.gd:295`, `:301`; `:290` | `WARNING` |
| #d0283c, #7a4a56 | `cultivation_page.gd:250` | `BLOOD`, `Color(BLOOD, 0.45)` |
| #e05a6e | `gift_page.gd:37`, `ui_kit.gd:377` | `HEART` |
| #2b2118 | `dialogue_page.gd:97` | `PAPER_INK` |
| #d5bd85 | `hud.gd:45` (the local `GOLD`) | `HUD_LABEL` |
| #c2474f, #ae5360 | `hud.gd:1495`; `:1984` | `HP` |
| #4bafaa | `hud.gd:1984` | `QI` |
| #b3202e | `hud.gd:1507` | `BLOOD` |
| #3a1418 | `hud.gd:1922` | `Color(BLOOD, 0.3)` |
| #17242c | `hud.gd:1371`, `:1983` | `BAR_TROUGH` |
| #8fc8ff, #8fd3ff, #8fd6ff | `hud.gd:1559`, `:1560`; `:1707`; `:1973` | `SKY` |
| #67d67a, #7a8a8a | `hud.gd:1655` (open and closed portals) | `BRIGHT_JADE`, `HOLLOW` |
| #f0e070 | `hud.gd:1678` (other NPC dots) | `PALE_GOLD` |
| #cfe6f0 | `hud.gd:1535` (sword-intent pips) | `MIST` |
| #344d52 | `hud.gd:1750` (the idle page dot) | `Color(HOLLOW, 0.5)` |
| #e8c89a | `hud.gd:1853` (progress without Qi) | `PALE_GOLD` |
| #f0d08a, #c6a262, #7a5426, #5c4424, #1d5157, #061519 | `hud.gd:1298-1299` (`ring()` rim and disc) | Move into the HD `hud_ring` asset (§5) |
| #c9d6dc, #d9ccaa, #e2ebee, #e8dcbc | `map_page.gd:66-67` | `SURFACE.sky_scroll_edge`, `.scroll_edge`, `.sky_scroll`, `.scroll` |
| #efe3c2, #8a6a3a, #1c1a18 | `crafts_page.gd:510-516`, `guqin_page.gd:106` | `SURFACE.talisman`, `.talisman_edge`, `.brush_ink` |
| #c99a58, #d8ad6c, #4a3218, #1c1b20, #6f6a5e, #f1ece0 | `chess_page.gd:27-45` | `SURFACE.board_edge`, `.board`, `.board_line`, `.stone_black`, `.stone_white_rim`, `.stone_white` |
| #3b2416, #5a3620, #d8c08a, #1b1410, #b8894a, #12352d | `guqin_page.gd:100-121` | `SURFACE.wood_dark`, `.wood`, `.bridge`, `.peg_dark`, `.peg`, `.hui` |

`UiKit.badge_color` (`ui_kit.gd:288-289`) maps its words onto tokens: grey → `HOLLOW`, green → `BRIGHT_JADE`,
white → `PAPER`, orange → `WARNING`, red → `RED_TEXT`.

Float literals: `crafts_page.gd` 22 (the tribulation sky and the furnace glow), `hud.gd` 15, `map_page.gd` 13, one each in
`chess_page.gd`, `fishing_page.gd`, `menu_page.gd`, `quest_page.gd` and `revival_page.gd`. The same rule applies: a
colour is a token, `Color(UiKit.X, alpha)`, or a texture modulate (`Color.WHITE`, `Color(1, 1, 1, alpha)`). The sky and
glow become `SURFACE` entries (`sky_top`, `sky_bottom`, `ember`). Shadows use `Color(UiKit.INK, alpha)`.

## 2. Spacing grid

Rules:

1. Positions and sizes are multiples of **8** px. Inside a dense component (a list's row gap, a badge, a bar's inner
   margin) the half step, 4, is allowed; this is the rule the approved kit already states (`docs/mockups/kit/README.md`,
   Layout).
2. Every window stays inside the safe area x 48–1232, y 24–696 (the old `Page.SAFE`). Every standard window below is on
   the grid and inside it.
3. Fixed art keeps its own size (the 52 px close button, the 440 × 60 title plaque, the 76 px slot); its position is on
   the grid.
4. Component internals are exempt: bar thickness, bevels, rule widths, the HUD's polar ring layout (§9).
5. Gaps: 8 between related controls, 16 between groups and between cards. Text inside a card starts 16 px in.
   Buttons are 48 (compact and in rows), 56 (standard) or 64 (a page's main action) tall.

### 2.1 The places I8 lists

| Place | Where | Now | Grid |
|---|---|---|---|
| Content side inset | `page.gd:70` | 28 | 32 (the HD window's nine-slice margin) |
| Content top, titled page | `page.gd:68` | 84 | 80 (10 px under the plaque) |
| Content top, no title | `page.gd:68` | 24 | 24 |
| Added for tabs | `page.gd:69` | 44 | 56 (48 tab + 8) |
| Content bottom inset | `page.gd:70` | 24 | 24 |
| Tab row y | `page.gd:140` | frame y + 84 | frame y + 80 |
| Tab height | `page.gd:144` | 40 (hit 48 since P4a) | 48, as the kit and mockups 00 and 04 draw it |
| Tab gap | `page.gd:151` | 6 | 8 |
| Tab minimum width | `page.gd:143` | 118 | 120; the width follows the label (label + 40) and is not rounded |
| Close button | `page.gd:116` | frame end − 70, y + 14 | frame end − 72, y + 16 |
| Default modal | `page.gd:43` | 700 × 380 at 290,170 | The small window, below |
| Confirm dialog | `page.gd:382` | 500 × 220 at 390,250; buttons 190 × 54 | 512 × 224 at 384,248; buttons 192 × 56 |
| Page toast | `page.gd:128` | 46 tall, 70 above the window's foot | 48 tall, 72 above |
| List row gap | `page.gd:367` | 4 | 4 (the half step) |
| List scroll gutter | `page.gd:367`, `:372` | rows `w − 10`, thumb 4 px at `end − 6` | rows `w − 8`, thumb 4 px flush right |
| List row pitch | 26 `list()` calls | off the grid | Rounded **up** to 8 (below), so no row gets shorter |
| Bag grid to detail panel | `inventory_page.gd:72-73`, `:105` | 2 px apart | 16 |
| HUD icon row pitch | `hud.gd:43` | 58 (1058, 1116, 1174, 1232), as mockups 01 and 02 draw it | 56 (1064, 1120, 1176, 1232): Mail stays, Menu moves 6 px |
| HUD bottom row pitch | `hud.gd:27-29` | 92 | Replaced by the ring layout of mockup 01 (§9) |
| Neighbouring buttons | many pages | 6, 8, 10, 12, 14, 16, 20 | 8 within a group, 16 between groups |

List pitches off the grid, with the grid value (audit `rows`):

| `list()` | Now → grid | `list()` | Now → grid |
|---|---|---|---|
| `beast_arena_page.gd:29` | 52 → 56 | `relations_page.gd:163` | 38 → 40 |
| `characters_page.gd:17` | 84 → 88 | `shop_page.gd:38` | 76 → 80 |
| `codex_page.gd:68` | 150 → 152 | `shop_page.gd:75`, `:101` | 70 → 72 |
| `core_exchange_page.gd:29` | 66 → 72 | `techniques_page.gd:69` | 58 → 64 |
| `crafts_page.gd:164`, `:282` | 62 → 64 | `teleport_page.gd:17` | 58 → 64 |
| `cultivation_page.gd:321` | 110 → 112 | `tower_page.gd:27` | 58 → 64 |
| `cultivation_page.gd:343` | 76 → 80 | `welcome_page.gd:53` | 36 → 40 |
| `inventory_page.gd:97` | 76 → 80 | `works_page.gd:57` | 78 → 80 |
| `pets_page.gd:30` | 70 → 72 | `works_page.gd:81`, `:115` | 84 → 88 |
| `pets_page.gd:262` | 52 → 56 | `works_page.gd:145` | 122 → 128 |
| `quest_page.gd:67` | 62 → 64 | `your_sect_page.gd:38` | 70 → 72 |
| `relations_page.gd:81` | 36 → 40 | | |

A row that holds a tap target has a pitch of 56 or more, so its panel (pitch − 4) is at least 52.

### 2.2 Standard windows (I13)

Six sizes, centred on the canvas and on the grid. A page picks the smallest that holds it, shrinking by 32 px at most.

| Name | Rect (x, y, w, h) | Content (titled, no tabs) | For |
|---|---|---|---|
| Full | 64, 32, 1152, 656 | 1088 × 552 | Every system page (`page.gd:22`, the default) |
| Large | 128, 56, 1024, 608 | 960 × 504 | A place or a choice that needs width |
| Medium | 256, 72, 768, 576 | 704 × 472 | Lists shown in context |
| Small | 288, 152, 704, 416 | 640 × 312 | Short choices; the default modal |
| Confirm | 384, 248, 512, 224 | — | `Page.ask` |
| Dialogue | 48, 464, 1184, 232 | — | The dialogue strip, inside the safe area |
| Screen | 0, 0, 1280, 720 | — | The world map's painting only (decision 25): its frame is the screen's edge |

| Page | Now | Standard | Change |
|---|---|---|---|
| `beast_arena_page.gd:10` | 1020 × 600 at 130,60 | Large | +4 w, +8 h |
| `core_exchange_page.gd:7` | 940 × 580 at 170,70 | Large | +84 w, +28 h |
| `fates_page.gd:7` | 1040 × 580 at 120,70 | Large | −16 w, +28 h (with the 32 px inset the three cards lose 8 px each) |
| `gift_page.gd:10` | 980 × 600 at 150,60 | Large | +44 w, +8 h |
| `pouches_page.gd:12` | 1000 × 640 at 140,40 | Large | +24 w, −32 h (its seven cards need 480 of the 504) |
| `welcome_page.gd:7` | 760 × 560 at 260,90 | Medium | +8 w, +16 h |
| `teleport_page.gd:7` | 680 × 576 at 300,72 | Medium | +88 w |
| `revival_page.gd:8` | 680 × 500 at 300,110 | Medium | +88 w, +76 h |
| `emotes_page.gd:8` | 600 × 540 at 340,90 | Medium | +168 w, +36 h (the wheel's ellipse widens) |
| `mercy_page.gd:8` | 680 × 400 at 300,150 | Small | +24 w, +16 h |
| `exchange_page.gd:8` | 640 × 420 at 320,150 | Small | +64 w, −4 h |
| `fishing_page.gd:19` | 600 × 420 at 340,150 | Small | +104 w, −4 h |
| `dialogue_page.gd:15` | 1200 × 232 at 40,470 (outside the safe area) | Dialogue | −16 w; the speaker plaque and portrait placed in screen coordinates at `dialogue_page.gd:62-66` move with it |

The other 31 pages use the full window. `your_sect_page.gd:17` (the name field) and `:32` (the Found button) are
still placed in screen coordinates; they are placed from `content` instead.

### 2.3 Slots

The user's decision: page slots are **76 px** with the 64 px icon at 1:1 (inset 6). This replaces today's 64 px slot,
whose icon `slot_box` draws in `rect.grow(-6)` (`page.gd:282`), 52 px wide, scaled by 0.81 with nearest filtering.

| Slot | Size | Icon | Pitch | For |
|---|---|---|---|---|
| Page slot | 76 | 64, the file 1:1 | 80 (gap 4) | Bag, storage, equipment, detail panels, shops, rewards |
| Compact slot | 48 | 32, the native `@32` variant (§8) | 56 (gap 8) | Ingredient lists, costs, rows that show several items |

Both are tap targets of 48 px or more. A list row that shows an item uses the compact slot, unless the row is the
item's own detail; a row that holds a page slot has a pitch of 88 or more. Slots today are 44–84 px; none is 76, and 35
literal `slot_box` calls draw their icon at a size off the rule (audit `icons`). Until P5a lays the Bag out again as the
jade chest, its grid (`inventory_page.gd:72-91`, 420 px wide) holds five columns of 76 px slots at the 80 px pitch
instead of six of 66.

## 3. Type scale

Words are set in serif by the recorded deviation C6; numerals of 20 px and more that are drawn over the world are
Pixelify Sans.

| Role | Face | Layout size | Drawn | Where today |
|---|---|---|---|---|
| Title | Cormorant Garamond 700 | 34 | 41 | Window titles (`page.gd:115`), the room banner (`hud.gd:1868`) |
| Display | Cormorant 700 | 30 | 36 | A realm's name (`cultivation_page.gd:44`), a big caption |
| Heading | Cormorant 700 | 26, stepping down to 22 (to 20 today, `page.gd:228`) | 31 | `Page.heading` (`page.gd:225`), with the `BRONZE` rule |
| Subheading | Cormorant 700 | 22 | 26 | The smallest Cormorant: group names, "Next: …" |
| Button | Source Serif 4, 600 | 22, stepping down to 14 | 22 | `Page.btn` (`page.gd:158`, `:170`) |
| Body | Source Serif 4, 600 | 20 | 20 | `Page.text` (`page.gd:205`) |
| Paragraph and row | Source Serif 4, 600 | 18 | 18 | `Page.para` (default 19 today, `page.gd:233`), rows, HUD names, toasts |
| Caption | Source Serif 4, 600 | 16 | 16 | The HUD tracker and log, captions |
| Hint (the minimum) | Source Serif 4, 600 | 14 | 14 | Hints, sub-lines, tick labels |
| Label | Source Serif 4, 700 | 14–18 | same | World labels, nameplates, card titles, headings under 22 (`UiKit.label_font`, `ui_kit.gd:85`) |
| Numbers under 20 | Source Serif 4, 700, lining figures | 14–18 | same | Bar values, counts, cooldowns (`draw_outlined` under `PIXEL_NUMERALS_MIN`) |
| Numbers of 20 and more, over the world | Pixelify Sans | 20, 26, and up | same | Damage numbers, large counts (`draw_outlined`, `ui_kit.gd:225-231`) |
| Symbols | JadeRiverSymbols | — | — | ✓ ◆ ▶ ★ ➤ as the fallback of every face (`ui_kit.gd:49`) |

Rules:

1. `MIN_SIZE` = 14 (`ui_kit.gd:44`). No call asks for less. `UiKit.size_for` (`ui_kit.gd:116`) raises smaller requests
   to 14, but a request under 14 is a fault the `ui_suite` reports (§11). Today 15 call sites ask for 13 or 10:
   `beast_arena_page.gd:66`, `codex_page.gd:86`, `crafts_page.gd:612`, `map_page.gd:110`, `:268`, `pets_page.gd:208`,
   `:223`, `:238`, `:266`, `pouches_page.gd:41`, `works_page.gd:101`, `:133`, `hud.gd:1492`, `:1702` (10 px), `:1773`.
2. `DISPLAY_MIN` = 22 (`ui_kit.gd:40`). Cormorant is used only from 22 up and is drawn at `WORD_SCALE` 1.2
   (`ui_kit.gd:35`); a display request under 22 is set in the bold serif (`ui_kit.gd:108-113`).
3. `PIXEL_NUMERALS_MIN` = 20 (`ui_kit.gd:223`). Pixelify draws only strings of digits and signs
   (`UiKit.is_numeric`, `ui_kit.gd:101`) at 20 px or more, and only through `draw_outlined`. `draw_text` never uses it.
4. Text is measured at the size it is drawn (B21). `UiKit.text_width` and `UiKit.fit` (`ui_kit.gd:261`, `:272`) measure
   through `size_for`. A caller fits at the size it draws at. One call still breaks this: `beast_arena_page.gd:110` fits
   a name at 13, and `Page.bar` draws the label at 17 (`page.gd:271`).
5. The scale is 14, 16, 18, 20, 22 for words and 22, 26, 30, 34 for display. The pages ask for 13 (11 calls), 15 (106),
   17 (86), 19 (48), 21 (22), 23 (1) and 24 (13) as well. Each moves to the nearest step: up where the `ui_suite` finds
   no overrun, down one step where it does.
6. The Text size setting (`TEXT_SIZES` 0.92 / 1.0 / 1.12, `ui_kit.gd:42`) scales every word after these rules. At Small
   a 14 px word draws at 13; that is the player's choice.
7. Line height is 1.3 × size (`UiKit.line_height`, `ui_kit.gd:125`).

## 4. Numbers, durations and plurals

**Numbers.** One helper groups thousands: `UiKit.fmt` (`ui_kit.gd:329`), which rounds and puts commas ("31,751").
`UiKit.pool_values` (`ui_kit.gd:326`) shows a pool's value and its most, never above the most and never a sliver of life
as 0. Rules:

1. Every number of 1,000 or more is grouped with `fmt`. The damage numbers are not today: `world.gd:408` passes
   `str(amount)`.
2. A value of a total is written "a / b" with spaces, as 16 strings already do. The HUD bars use "%s/%s"
   (`hud.gd:1495`, `:1499`, `:1502`), and two strings use "/" with no spaces.
3. Over the world, numbers of 10,000 or more are shortened to three figures: "18.2K", "1.25M" (mockup 01). This needs
   a new `UiKit.short(n)`, which falls back to `fmt` under 10,000.
4. Percentages are whole ("47%") unless a tenth matters ("27.0%" crit chance, mockup 05).

**Durations (I14).** One style, from one helper: **`UiKit.span(seconds, days := true)`** (`ui_kit.gd:317`), with the
keys `ui.span_dh` "%d d %d h", `ui.span_hm` "%d h %d m", `ui.span_m` "%d m", `ui.span_s` "%d s". Every time left, wait,
cooldown and duration calls it. `UiKit.clock` (`ui_kit.gd:309`, "4:23:55") stays only for a countdown the player is
racing on the HUD: the room event timer, which formats its own "%d:%02d" today (`hud.gd:1955`). The route stopwatch
(`hud.gd:1607`, "12.4 s") counts up and keeps its tenths.

Places that still format durations their own way:

| Place | Today | Change |
|---|---|---|
| `posts_page.gd:319-322` `_dur(h)` | `ui.posts.days` "%d days", `ui.posts.hours_minutes` "%dh %02dm", `ui.posts.minutes` "%d min" | `UiKit.span(h * 3600.0)` |
| `works_page.gd:267-269` `_dur_s` | as above | `UiKit.span` |
| `welcome_page.gd:63-66` `_dur` | `ui.welcome.dh_02dm`, `ui.welcome.minutes` | `UiKit.span` |
| `post_authority.gd:823-826` `_hours_text` | as `posts_page` | `UiKit.span` |
| `auction_page.gd:36` | `ui.auction.closes_in` "Closes in %dh %02dm" | "Closes in %s" with `UiKit.span` |
| `combat_authority.gd:1508` | `sim.combat.talisman_recovering_ds` "(%ds)" | "(%s)" with `UiKit.span` |
| `progression_authority.gd:434` | `sim.progression.your_mind_needs_rest_ds` "(%ds)" | "(%s)" with `UiKit.span` |
| `techniques_page.gd:138` | `ui.techniques.qi_ds` "… · %ds" | "… · %s" with `UiKit.span` |
| `garden_page.gd:52`, `:73`, `:133`; `codex_page.gd:105`; `object_view.gd:249-250`; `hud.gd:1204`, `:1702` | `UiKit.clock` for waits of hours | `UiKit.span`: these are waits, not races |

The keys `ui.posts.days`, `ui.posts.hours_minutes`, `ui.posts.minutes`, `ui.welcome.dh_02dm`, `ui.welcome.minutes` and
`ui.auction.closes_in` leave `tools/data/ui_strings.json` when their callers change; `ui.clock_days` stays with
`clock`.

**Plurals (I12).** A string that prints a count beside a countable noun has a twin key ending in `_one`, and the
caller fetches it with **`Tx.plural(key, count)`** (`scripts/core/tx.gd:11`). Nine keys have their `_one` form today. The
audit (`plurals`) finds 105 keys that print "%d" before a plural noun without one, for example `hud.cores_sold`
"Sold %d %s for %d Spirit Stones", `sim.pet.hearts` "%d hearts", `ui.forge.salvaged` "Salvaged %d pieces." Each is
reviewed. A count of a total ("%d of %d fights left") takes its noun from the total and needs no twin.

## 5. Kits (C7, G6, I1)

The rule: **the HD kit draws every frame; pixel art sits inside frames.** HD means `tools/ui/build_ui_hd.py`, distance
fields at 3 texels per screen px, drawn through `HdStyleBox` (`ui_kit.gd:188`). Pixel means icons, motifs, sprites and
numbers, drawn 1:1 or at an integer scale with nearest filtering. **One kit per asset**: an asset name appears in exactly
one manifest.

Today `UiKit.style` takes the HD asset first and the pixel one second (`ui_kit.gd:161-165`). The 17 assets the HD kit
has are never drawn from the pixel kit. What still draws from the pixel kit, or procedurally:

| Asset or drawing | Today | Replacement |
|---|---|---|
| `slot_empty_motif`, the cloud seal (pixel kit, `build_ui.py:239`, `ui_assets.json:159`) | Loaded by path for empty technique and Treasure slots (`hud.gd:1335`, `:1810`); the mockup kit draws it in empty page slots | A **pixel motif in Style A**: the 64 × 64 art-px cloud seal of the icon study (two curls on a base line, `JADE_SHADOW` at 35%), built by the icon pipeline, drawn 1:1 in the 76 px slot. The HUD draws no empty slot (mockup 01), so `hud.gd` stops loading it |
| `hud_circle`, `hud_circle_large`, `hud_circle_small` (pixel kit, `build_ui.py:433`, `ui_assets.json:61-93`) | Drawn nowhere | Removed with their PNGs (`AGENTS.md` rule 3: no unused assets) |
| The HUD rings, `hud.gd ring()` and `_disc()` (`hud.gd:1291-1313`) | Procedural on every HUD button, with six literal colours | **HD `hud_ring`** in `build_ui_hd.py`: 132, 64, 52 and 48 px, states `normal`, `pressed`, `active` (the lit gold rim and halo), drawn to match `ring()` as mockups 00–02 show it. `hud.gd` draws them with `UiKit.style` |
| The pet-strip discs (`hud.gd:1461-1462`, `INK` and `DEEP_TEAL` circles) | Procedural; the roundel beside them is gone | The 48 px `hud_ring` with an HP arc: the party chips of mockup 01 |
| Tracker plate, run banner, event and tribulation cards (`hud.gd:1556`, `:1591`, `:1927`, `:1962`) | Flat `draw_rect` plates | Plates in the `PLATE` token; the cards use the HD `toast` they already frame with |
| Bar troughs (`hud.gd:1369-1375`; `Page.bar` inner rect, `page.gd:268`) | Flat | Kept flat, coloured `BAR_TROUGH`; `Page.bar` keeps the HD `bar_shell` |
| Hearts (`ui_kit.gd:373-383`), nameplate (`ui_kit.gd:237-257`) | Procedural | Kept procedural, coloured `HEART` and `PLATE` |
| Drawn surfaces: map scroll (`map_page.gd:66-68`), Go board (`chess_page.gd:27-45`), zither (`guqin_page.gd:100-121`), talisman paper (`crafts_page.gd:510-516`), tribulation sky (`crafts_page.gd:768-772`), tension bar (`fishing_page.gd:61-63`) | Procedural with literals | Kept procedural in P4, coloured from `SURFACE` (§1.6); P5 may replace them with art |

After the change `data/ui_assets.json` lists no asset that `data/ui_assets_hd.json` has. The pixel kit's frame PNGs for
those assets are no longer drawn and go too. `UiKit._kit_style` falls back from the HD asset straight to the flat box
(`ui_kit.gd:167-172`). `tooltip` stays in the HD kit for P5's detail pop-ups; its pixel copy goes. The mockup kit
(`docs/mockups/kit/kit.css`, `.k-slot.is-empty`, `.k-hud`) follows the same assets.

## 6. States and selection (I3, I4)

| State | Buttons (`button_primary`, `button_secondary`) | Panels and rows (`minor_panel`) | Slots | Tabs |
|---|---|---|---|---|
| Normal | Kit art; label `PALE_GOLD` (primary) or `PAPER` (secondary) | Kit art | Kit art | Kit art; label `PAPER` |
| Pressed | Kit `pressed` art, label offset (1, 2) (`page.gd:163`), only while the finger is down | Derived: normal × (0.82, 0.86, 0.86) (`ui_kit.gd:139`) | Derived | — |
| Selected | — | Derived: normal + `selected_slot_glow` grown 3 (`ui_kit.gd:144-153`); the name in `PALE_GOLD` | `selected_slot_glow` grown 4 (`page.gd:293`); HD `slot` `selected` art where the slot is the choice | Kit `selected` art; label `PALE_GOLD` |
| Disabled | Kit `disabled` art; label `HOLLOW`; the bronze lock at the top right when it has a reason (`page.gd:174`); a tap shows the reason (`page.gd:434-439`) | Derived: normal × (0.5, 0.56, 0.58) at 0.8 | HD `disabled` art; icon greyed | Derived disabled; label `HOLLOW`; lock |
| Hover | None. The game is touch-first; on a desktop the pressed state shows while the button is held | | | |

**One selection style** for every list, grid and card set: the derived `selected` panel (the glow), and nothing else.
It marks the one thing the page acts on. A second meaning must not borrow it:

- "You" and "now" (your row in the Heaven Ranking, `map_page.gd:265`; the current rung on the Body tab,
  `cultivation_page.gd:138`) are marks, not selections: the normal panel, a `GOLD` ◆ before the name and the name in
  `PALE_GOLD`.
- A toggle's "on" is its own state: the `selected` art. `pressed` is only for the finger. Settings uses `pressed` for on
  (`settings_page.gd:34`, `:90`), and prints Off in `HOLLOW`, the disabled colour; Off is `MIST`.
- Locked things stay visible, dimmed, with the lock and one line saying what opens them (mockup 03).

## 7. Touch targets

**Pages.** `Page.MIN_TAP` = 48 (`page.gd:13`). `Page._register` (`page.gd:181-195`) grows any smaller `btn`, `region`
or `slot_box` rect to 48 round its centre; the art keeps its size, and `full` and `art` are kept for the `ui_suite`. The
suite checks every page and tab, in every context, for targets under 48 and buttons that share a point
(`tests/rules_tests.gd:163`, `:307-308`). New controls are drawn at 48 or more, so the look matches the target: tabs 48
tall (§2.1), compact slots 48, page slots 76.

**The HUD** tests circles in `role_at` (`hud.gd:209-238`), not `Page` regions. A target is at least 48 across
(a hit radius of 24), and at least the drawn radius + 4.

| Target | Line | Drawn | Hit | Verdict |
|---|---|---|---|---|
| Attack / context | 210 | r 66 | r 74 | Pass |
| Jump, Cultivate, Sense | 211-213 | r 32 | r 36 | Pass |
| Presence, Sphere, Quick-use, Pet, Guard, context chip, post, Treasures, Swap | 214-224 | r 26 | r 30 | Pass |
| Draught | 217 | r 20 | r 22 (44 across) | **Under 48**: hit r 24 |
| Technique slots | 226 | r 33 | r 43 | Pass |
| Icon row, auto-hunt | 229, 235 | r 26 | r 27 | Pass |
| Pet strip: active, mount, bag animals | 231 (radii at 1446, 1453, 1450) | r 24, 20, 18 | r + 4 = 28, 24, 22 | **Bag animals under 48** (44): hit r 24 |
| Tracker go button | 234 (drawn at 1565) | 30 × 22 | grown 6: 42 × 34 | **Under 48**: a 48 × 48 button (mockup 02) |
| Player panel | 232 | 360 × 104 or 120 | 360 × 104 | The Soul row (y 120–136) opens Quests, not Character: the hit rect follows the panel |
| Progress edge | 237 | 1280 × 8 | 1280 × 16 | Exception: a shortcut on the screen's edge that the joystick half must not lose; the Cultivation page is also on the Menu |

In the ring layout of mockup 01 neighbouring hit circles overlap (64 px rings 68 px apart on ring 1 with a hit radius of
36). Where two circles overlap, the nearest centre wins.

**Decision 42 (the prototype APK's feedback).** Jump is drawn at r 32 (64 px, from 52), hit r 36. The techniques are
56 px squares (the tree's node pictures, §9), hit r 38, which reaches nearly to their corners. What the world offers in
reach has its own button, r 30, hit r 34; Attack (r 66, hit r 74) never shows it. The `hud_suite` also checks that no
two of the cluster's controls touch, in every state, right- and left-handed.

## 8. Icons

**Decided: Style A, "HD pixel"** (roadmap §6 decision 7; the study in `docs/mockups/icon_study/`, drawn by
`tools/icons/study/`). The redraw is phase P4b, family by family (§11 step 9).

### 8.1 Sizes

| Family | Count | Today: art px → file | Style A: art px = file, shown 1:1 | Native re-renders |
|---|---|---|---|---|
| items | 489 | 32 → 64 (×2) | 64 | `@32` (the HUD item ring, the compact page slot) |
| equipment | 104 | 32 → 64 | 64 | `@32` |
| techniques | 66 | 32 → 64 | 64 | `@48` (the HUD technique ring) |
| hud glyphs | 73 | 16 → 32 | 32 | none; 64 is a 2× draw |
| status | 34 | 12 → 24 | stays 12 → 24 for now | — |
| markers | 17 | 12 → 24 | stays 12 → 24 for now | — |

(`tools/icons/registry.py:4` `FAMILY_SIZE`; 783 icons in `data/icon_manifest.json`.)

### 8.2 The scaling rule (I2)

A pixel icon is drawn only at a size its pipeline wrote, or at an integer multiple of it. Nothing is scaled by a filter
or by a non-integer factor.

| Kind | Allowed draw sizes |
|---|---|
| Items and equipment | 64 (the file, 1:1), 32 (`@32`), 128 (2×) |
| Techniques | 64 (the file, 1:1), 48 (`@48`), 128 (2×) |
| HUD glyphs | 32, 64 |
| Status icons, markers | 24, 48 |
| Sprites and creatures | Integer screen px per art px: an `Avatar` scale of 1, 1.5, 2, 2.5 or 3, since sheets are 2 px per art px; `UiKit.draw_creature` already steps in halves (`ui_kit.gd:354`) |

The engine draws with nearest filtering (`page.gd:41`). Variants are files named `<id>@48.png` and `<id>@32.png`, listed
in the manifest. Until the pipeline writes them, today's 32-art-px icons are exact at 32 (the art grid) and at 64.

Draw sizes off the rule at 723fc5e (audit `icons`): 66 of 86 literal sizes.

- Pages: every `slot_box` except the 44 px slots, whose icon is 32 (the others draw it at slot − 12: 36, 38, 40, 44,
  48, 50, 52, 60, 72); `icon_at` at 28, 36, 40, 44, 52, 56 and 88 px (`character_page.gd:136`, `:144`,
  `garden_page.gd:45`, `:50`, `mail_page.gd:28`, `pets_page.gd:400`, `posts_page.gd:101`, `:236`, `pouches_page.gd:28`,
  `works_page.gd:88`, `:99`, `:121`, `:131`, `:179`, `:225`); item icons at 24 (`posts_page.gd:65`, which the audit
  cannot tell from a status icon); `codex_page.gd:136` at 28; the currency coin at 24 (`page.gd:338`).
- HUD: the lock at 24 (`hud.gd:1330`); the empty motif at 44 (`:1336`); the auto-hunt glyph at 26 (`:1398`); the coin
  at 24 and the spirit stone at 22 (`:1410`, `:1414`); the round-button glyphs at 28 (`:1767`, `:1772`, `:1777`,
  `:1790`, `:1802`, `:1841`, `:1845`); quick-use and Treasure items at 36 (`:1783`, `:1816`); the Draught at 28
  (`:1796`).
- Sprites: the Character page's figure is scaled 2.4 (`character_page.gd:21`), 4.8 px per art px; it becomes 2.5.

### 8.3 Style A rules

From the study (`docs/mockups/icon_study/README.md`, `tools/icons/study/study_lib.py`) and `docs/art-contracts.md`:

1. **One bold object**, at most one supporting symbol. It reads at 48. The UI adds borders, rims and halos; the icon
   shows only the object.
2. **Seven-step ramps** per material: `mat7` (`study_lib.py:75`) extends a palette ramp with a deeper shadow (the darkest
   step mixed 42% with `INK`) and a specular (the lightest mixed 55% with white). The base is step 3. A blade shows a lit
   face, a ridge, a shade face and a rim in distinct steps. Shading picks steps in bands (`BANDS`, `study_lib.py:317`:
   ray, sphere, gradients, and `field` for blades and cylinders).
3. **One light from the top-left.** A **rim light**: a 1 px mist-blue line (`#afc9d1`, `RIM_COOL`, `study_lib.py:37`) on
   the lower-right silhouette edge of metal, glass, jade and porcelain, weaker on cloth and wood (per material kind,
   `KINDS`, `study_lib.py:46`).
4. **A selective outline.** Inside the object, separations are the local material's dark tone (its outline colour, 55%
   `INK`). The outer silhouette mixes towards `INK` by 42–78%, darkest beside a bright pixel, so a dark robe keeps a
   coloured edge and a pale blade a near-black one (`PixelPainter.image`, `study_lib.py:474`).
5. **Textures as pixel patterns, no dithering**: wood grain lines every 3 px with a knot rhythm; a sheen band and a dark
   reflection band on metal; jade and glass lit through, with the light pooling in a crescent on the far side (with more
   steps in the crescent, taken from Style B); fold lines on cloth; laid lines on paper; a wet sheen on clay.
6. **Grade by material kit**: the blade, fittings, grip, wrap, gem and blade work change with the grade
   (`tools/icons/palette.py:113` `GRADES`, plus kits for sovereign, will and sphere, which are missing today). Form and
   trim change, never colour alone. Mystic and above add stepped glow bands at alpha 120, 64 and 28.
7. **The grade halo belongs to the slot.** The soft halo by grade is drawn by `Page.slot_box` behind the icon, as
   `_pill_glow` does for pills today (`page.gd:310`), not baked into the icon (taken from Style B).
8. **Techniques** are a domed disc with a keyline under the mark (taken from Style B); secret arts add the gold rim and
   studs.
9. **HUD glyphs**: 32 art px, a pale-gold face (`GOLD`, `PALE_GOLD`) with an ink outline, a lit edge, a warm shade
   edge, one highlight.
10. **Empty slot**: the 64 px cloud seal in `JADE_SHADOW` at 35% (§5).
11. Palette tokens first (`docs/art-contracts.md`); art keeps a 1 px margin inside the canvas; no stray pixels; builds are
    deterministic and byte-identical.

### 8.4 Technique pictures (decision 42)

The user asked for the skill icons to look like `docs/redesign/feedback/skill_icon_reference.png` (the Techniques
tree's cards as their phone showed them). One picture, `TechniquePicture` (`scripts/presentation/technique_picture.gd`),
is every art's face: the tree's cards (72 px inside the frame), the tree's reading (148 px), the HUD's technique
buttons (round since decision 43, the picture 58 px across inside the ring) and the Techniques page's loadout bar
(42 px). A top-down character is always drawn as the top-down game draws it (`TopdownFigure`); the side view's Avatar
only for a classic side-view character. Decision 43 draws the world's people 46 art px tall; a picture keeps the 38 px
figure it was approved at, from the frames the character build casts for the pictures' poses at that density
(`TopdownFigure.draw` with `picture`; art bible §13).

| Part | Rule |
|---|---|
| Ink | One ramp a picture from its element's colour (`SpriteCache.element_color`): deep (the colour darkened 90%) at lightness 0, mid (darkened 55%) at 0.4, light (lightened 55%) at 1. Every pixel of the picture is a lightness on it (`technique_picture_ink.gdshader`). A locked art on the tree is in a grey ramp. |
| Ground | Mid ink, lighter round the body (a soft halo) and darker toward the edges; small stars in the light ink (a pixel each, one or two five-pixel sparkles); a card with room under the feet (the reading) a floor line and a few strokes on it. Painted at the figure's art pixel, so it is pixel art of one grid with the figure. |
| Figure | The character large at a whole scale: x2 on a card (from the head to about the ankles), x3 in the reading (whole, on its floor), x1 at a button's size (the whole figure: the button is a miniature of the card). Its own lightness pressed toward the dark, so it reads as a dark shape with light touches (the face, highlights) on the mid ground, and a light rim an art pixel out all round. |
| Pose | The pose a fight casts the art in with the art's own weapon family (the free hand for an art of any hand: a palm is a palm; a family art holds the character's weapon when it is of that family, else the family's own), from `TechniquePreview.top_pose`; seated in meditation for an art cast from a sitting whose form rests round the body (ward, domain, chorus, pillar, rain, release). A weapon's blow on the frame it lands, in profile toward the right (E: the blade reads); the bare hand's just after it lands, three-quarters toward the camera and the right (SE: the face over the hand still out); the hand seal toward the camera (S); a stance or a sitting three-quarters (SE). |
| Marks | A few marks of the art's form in the light ink with a dark outline, before the hand or round the body: a palm's crescents, a flurry's crescents high and low, a thrust's lines, a lunge's speed lines and chevrons, a ward's dome, a domain's ring on the ground, a pillar's springs rising, a seal's square, a snare's loop, a chorus's notes, a burst's rays, a wave's ripples, a volley's darts, and so on (`TechniquePicture._marks`). |
| Frame | The caller's: the tree's state colour (jade learned, gold open, slate locked, pale gold chosen), gold in the reading, bright jade on the HUD and the loadout bar; ink outside it. |
| Rank badge | A known art's mastery tier in a small ink-and-jade diamond ringed in bright jade, its number in pale gold: on the frame's lower right corner of a card, the upper right of a button (its lower right holds the lock and the Qi strip); on the HUD's round button, inside the picture's circle at 45° up and right, its middle 8 px in from the circle. |
| A button's size | The HUD's buttons (decision 43: round, 68 px across, the picture 58 px inside a 5 px rim and ring and cut to its circle; decision 42's were 56 px squares with a 50 px picture) and the loadout bar's slots (the picture 42 px), 59 px and under, are a miniature of the card: the whole figure at x1 (about 38 px tall), top to foot in the middle with a few pixels of margin, nothing of it cut by the frame (a figure taller than the picture would keep its head a pixel under the top and lose its feet, never its head). It faces the camera (S) on the frame before its blow lands, so its face always shows (at the landing a punch turns the head away), its body a little left of the middle (`HEAD_X`). The card's look at that size: the same ink and rim, the element's ground (a fall from 0.34 to 0.26 with the light round the body, a few faint stars high up), and one bold mark of the form clear of the figure on the right, light in a dark outline (a palm's crescent, a flurry's two, a ward's dome, a seal's square, a thrust's arrow, a domain's ring...: `TechniquePicture._marks_small`). The rank badge is small and wholly inside the picture's upper right corner, clear of the face; the cooldown's seconds, the Qi strip along the foot and the lock in the lower right stay inside the frame. The HUD dims a short art to 0.72 and a closed one to 0.45, so the figure still reads under the Qi strip and the lock. |

No frame waits on a picture. Each is a cell of an atlas sheet (a 512 px SubViewport of cells of one size) that the GPU
draws: the ground, stars and marks are painted on a worker thread; the main thread only makes their two small textures
and the cell's canvas item, at most six a frame within 1.5 ms. Until a cell is painted the element's plain ground shows
under its region, so a caller that keeps its drawing (the tree's tiles) is not drawn again for it. Cells are kept by
their look; when all ten sheets are full, the least used starts again and `TechniquePicture.generation` moves on (the
tree draws its tiles again). Screenshots, before and after beside the reference, are in
`docs/redesign/feedback/pictures/` (`tools/dev/picture_capture.tscn -- --tag=<before|after>`).

## 9. The HUD spec

Mockups 01 (a fight) and 02 (at rest) as approved, with no portrait roundel: the name, realm and bars take the panel's
width, and the bottleneck shows on the Stored Qi edge (`hud.gd:1484-1485`). Positions are for the right-handed layout;
the left-handed option mirrors x (`hud.gd:92-99`). The cluster keeps x ≥ 925 and y ≥ 425; the lower middle (x 380–900)
stays open for the fight.

| Element | Approved (01, 02) | Today | Change (P5a unless marked) |
|---|---|---|---|
| Player panel | `minor_panel` (16, 16, 360, 120); name 18 `PAPER` at x 34; realm 16 `PALE_GOLD` | (16, 16, 360, 104 or 120) (`hud.gd:1482`); name 18 (`:1486`); realm 15 (`:1491`) | Realm to 16 (P4 type scale) |
| HP, QI, SL bars | 288 wide at x 72; labels 14 bold in `HUD_LABEL` at x 36; values 14 outlined serif, "a / b" | 288 × 14 at x 72, pitch 18 (`hud.gd:1495-1502`); labels 16 in the local `GOLD` (`:1374`); values 14 (`:1375`), "a/b" | Labels to 14 in `HUD_LABEL`; values "a / b" (P4). Bars stay 14 tall, as the P3 note recorded |
| Party chips | 48 px discs at (408, 468, 528; 44), HP arcs, names 14 under at y 72 | Pet strip only, r 24 / 18 / 20 at y 48 (`hud.gd:1440-1475`) | Chips for the pet and the companions, in the 48 px `hud_ring` |
| Statuses | 24 px icons from (20, 144), 4 apart; the Hollowing meter (50, 152, 170 × 10) with stops at 50 and 100 | 24 px from (22, panel foot + 2), 26 apart (`hud.gd:1527`) | Pitch 28 from y 144; the meter |
| Quest tracker | Plate (14, 188, 342 wide), gold left rule; title 17; route 14 `MIST`; lines 16; a 48 × 48 go button at (300, 194) | From y 146 or 162, 312 wide (`hud.gd:1546-1560`); the button 30 × 22 (`:1565`) | Plate in `PLATE` at alpha 0.72; the 48 px button (P4, §7) |
| Boss bar | (400, 130, 480 × 18); name 26 above, "Lv · phase" 16 `MIST`; notches at each phase, the next one's effect in 14 under it | (340, 118, 600 × 14), name 18 (`hud.gd:1920-1924`) | As approved; its fill an ember gradient from `WARNING`, trough `Color(BLOOD, 0.3)` |
| Minimap | (1032, 16, 232, 140); room name 14 bold `PALE_GOLD`; the P1 chevron on the frame | Same (`hud.gd:42`, `:1620`) | None |
| Icon row | Menu, Bag, Map, Mail at y 188, 52 px rings; a count on Mail, a ready seal on Menu | 1058, 1116, 1174, 1232 (`hud.gd:43`) | Pitch 56 (§2.1); the seal |
| Currency pill | (1040, 222, 222 × 34); rests in boss arenas | Grows left from 1262 (`hud.gd:1408`) | Hidden in boss arenas |
| Attack / context | Centre (1165, 605), 132 ring; the context verb and target under it at y 678 | Same centre (`hud.gd:26`); the label at +50 (`:1741`) | Label at y 678 |
| Ring 1, R 132 round the attack | Jump 150° (1051, 671); techniques 180° (1033, 605), 210° (1051, 539), 240° (1099, 491), 270° (1165, 473), 64 px; dodge 300° (1231, 491), 52 px. Techniques only while a foe is near; at rest they fold into four beads on the attack ring (retired by decision 42: see below) | Slots on an arc (`hud.gd:25`); jump, cultivate, sense in a row at pitch 92 (`:27-29`) | As approved |
| Ring 2, R 214 | Fan 160° (964, 678); a held toggle 182° (951, 612); healing 204° (970, 518); Treasure 226° (1016, 451); 52 px; an empty slot is not drawn | Quick-use, Pet, Guard, Treasures, Presence, Sphere at fixed points (`hud.gd:30-38`) | As approved |
| The fan, open | Five toggles at R 150 from the fan: 180° (814, 678), 202° (825, 622), 224° (856, 574), 246° (903, 541), 268° (959, 528); 52 px; captions 14; a paper fan behind | — | New |
| Technique page tab | (1240, 672), 48 px, "1/2" | Two dots (`hud.gd:1750`) | As approved |
| Progress edge | (0, 712, 1280 × 8); stops at each level; gold with a glow at the bottleneck, Stored Qi as a bright lane; "Stored Qi n" 14 and the bottleneck line 16 above it | (0, 712, 1280 × 8) (`hud.gd:1851`); percent at (560, 706) | As approved |
| Log | Above the joystick zone at (20, 414), 16 px, outlined | (20, 596…) over the joystick (`hud.gd:1866`), shadow only | Moved and outlined (§1.4 rule 3) |
| World labels | Foes "Lv n Name", elites gold with a crown; party members an HP line in a fight and nothing out of it; a label never under a control; overlapping labels in rows | Labels at one height | As approved (G4) |
| Damage numbers | Pixelify from 20; "18.2K" from 10,000; crits gold and larger | Pixelify from 20; `str(amount)` (`world.gd:408`) | `UiKit.short` (P4, §4) |

Other things P5a carries from the mockups: the legacy panel (`hud.gd:1977-1988`), which preloads Cormorant outside
`UiKit` (`hud.gd:10`), goes; the HUD hit radii follow §7; toasts (`hud.gd:1906`) go to 408 wide with an 8 px gap.
`docs/mockups/kit/README.md`'s HUD table still gives the pre-note panel (bars 222 px at x 138); mockups 01 and 02 and this
table are the reference.

**As built (P5a).** The table above is built in `hud.gd`, with these choices where the mockups leave room:

- Places come from rings and angles (`RING1_R`, `RING2_R`, `FAN_R`, `_layout`, `_on`), so the left-handed option
  mirrors them. The pinned toggle stands at 178° (the mockup's point, 951, 612; the table's "182°" is the same point
  measured the other way round). Ring 2's places are 178°, 204°, 226°, 248°, 270° and 292°: the pin, the three quick
  slots (decision 45: `quick:0`, the healing slot, at 204°, `quick:1` at 226°, `quick:2` at 248°), the first treasure,
  the context (or Keep Post) and the swap have their own, the first to be drawn keeping a shared one; the second pin,
  the Draught and the second treasure take the next free one; past six, the rest stand on an outer row at R 276
  (216°, 233°, 250°, 267°), every place of both rows at least 62 px from every other.
- The fan (decision 20) holds Cultivate, Presence, Sphere, Sense and Pet, packed from 180° in that order; closed, the
  toggles that are on are pinned; open at rest by default (mockup 02), folded in a fight. The quick slots show while
  they hold something, at rest as in a fight; the treasures show only in a fight (the techniques stay out since
  decision 42).
- Rest and fight: a fight is a living, unhidden foe within 560 px of the player, a boss in the room or a tribulation
  (`WorldLabels.fight_near`), held two seconds after it ends; the fold takes 0.25 s.
- The top centre is one stack (a run's timer, the room's name, an event or tribulation, a fortune card, the toasts, a
  caption) from y 96, or from 184 under a boss bar; toasts that would end in the clear zone wait. The icon row keeps
  P4's 56 px pitch (the mockups draw 58).
- **The clear zone** (`CLEAR_ZONE`, x 380–900, y 324–656): the lower middle where the player and the party stand at
  the common camera positions. No control or panel is drawn in it in a fight or at rest with the fan closed; the open
  fan at rest keeps off the player's own box. The `hud_suite` checks it.
- **World labels** (G4): the views keep a box per label at an offset by kind and draw it on a child at z 3600, over
  every figure and under the effects; `WorldLabels` places the boxes each frame in whole rows round each other and the
  HUD's rects (`hud.obstacle_rects`), a plate under the feet going over the head when no row below is free. Party
  members show a 40 px HP line (30 for an animal) only in a fight.

Screenshots of the build beside mockups 01 and 02 are in `docs/ui_p5/hud/`.

**As built (decision 42, the prototype APK's feedback).** The user asked for a bigger Jump, the techniques and Attack
visible at rest, skill icons like the Techniques tree's pictures, one background when trading, and talks that close
once a quest is given or done. Where this changes the table above:

- **Ring 1.** Jump 150° (1051, 671), 64 px. The techniques no longer fold into beads: they stay out at rest as in a
  fight, as 56 px squares at 180° (1033, 605), 207° (1047, 545), 243° (1105, 487) and 270° (1165, 473), 27°, 36° and
  27° apart so the two across the ring's diagonal keep clear of each other's corners. The page tab shows with them.
- **Attack** keeps the weapon family's glyph always. The context (Talk, Gather, Open, Enter, Climb) has its own 60 px
  button on ring 2 at 270° (1165, 391), lit gold, its verb and target under it ("Talk · Lu"), at rest as in a fight;
  mockup 02's context on the big button is retired. The harvest's hold runs round that button and its tap ring
  shrinks onto it. Keep Post, at rest only, takes 226° (the first treasure's place, in a fight only). Before the Attack
  lesson there is no Attack button; the J and Enter keys use the context then.
- **The technique buttons** are the technique pictures of §8.4 (`TechniquePicture`, `scripts/presentation/`), the
  look the Techniques tree's cards and the loadout bar share, at a button's size a miniature of the card (§8.4): at
  50 px, the whole top-down figure at x1 facing the camera in the art's pose, with a margin inside the frame, on its
  element's ground in its ink, one bold mark of its form clear of it on the right and the small rank badge inside the
  upper right corner, in the tree's bright jade frame. States: cooling, an ink sweep with a pale gold hand and the seconds; short of Qi,
  the picture dimmed and a Qi strip along its foot filled as far as the pool reaches the cost; closed by the weapon in
  hand, a slate frame, the picture dim and a lock. The Techniques page's loadout bar (Ring I and II) draws the same
  pictures in its 52 px slots. A companion's party chip shows the top-down figure's head (a classic side-view
  character keeps the side view's).
- **The shop** draws the bag's side on the stall's own timber wall under the same awning; decision 24's patch of the
  gourd's heaven beside the stall is gone from the shop (the Storage page keeps it).

Screenshots before and after (at rest, in a fight, the Techniques page and its loadout bar, the shop, a quest offered
and taken) are in `docs/redesign/feedback/hud/`, taken by `tools/dev/hud_capture.tscn -- --tag=<before|after>`.

**As built (decision 43, the round technique buttons).** The user asked: "The skills in the HUD should be a little
bigger and circular." Where this changes decision 42's buttons:

- **Round, 1.21x.** Each technique is a round button 68 px across (`hud.gd` `TILE`; the square was 56): an ink rim, a
  4 px ring in the frame's colour (bright jade, slate when closed) and the art's picture inside it, 58 px across
  (`PICTURE`), cut to the circle (`TechniquePicture.draw_round` draws the atlas cell as a textured circle, the element's
  plain ground under it until it is painted). The picture is still the card's miniature at x1 (59 px and under): the
  whole figure stands inside the circle, the tightest corner of its box a few pixels in (the hud_suite's picture check
  holds every picture's box to the circle), and the rank badge sits inside it at 45° up and right.
- **The thumb's arc.** The buttons stand at 184°, 212° and 240° 146 px out and 270° 128 px out round Attack (1019, 595;
  1041, 528; 1093, 480; 1165, 477). The bigger circles keep 2-4 px clear of each other, of Jump (64 px, at 150° on
  ring 1), of Dodge, of ring 2 in a fight (the pinned toggle, the three quick slots, the treasures) and of the context's
  Talk button and its label ("Talk · Lu"), which the last one stands under. Their hit circles are 80 px across (48 px
  at least, P4); where two overlap a tap goes to the nearer centre. Left-handed mirrors them.
- **The states on a circle.** Cooling: the radial sweep, an ink pie over the picture for the part still to wait from
  the top round clockwise, its edge a pale gold hand, the ring dimmed over the same part, the seconds in the middle.
  Ready again: the ring flares pale gold and a ring of light goes out from it and fades over 0.35 s (`READY_S`), the
  picture lit a moment (under Reduce motion the ring's flare alone). Short of Qi: the picture at 0.72 and a Qi arc
  along its foot. Closed: the slate ring, the picture at 0.45 and the lock on its plate at the lower right.
- The rest state is decision 42's: the four techniques and Attack stay out at rest as in a fight, beside the 64 px
  Jump and the context's own button. At a 20:9 phone's 2400 x 1080 the screen keeps its 1280 x 720 layout, scaled
  x1.5 between side bars.

Before and after: `docs/redesign/feedback/hud/<before|after>_round_{rest,fight,cluster,cooldown}.png` at 1280 x 720 and
`..._phone.png` at 2400 x 1080 (`tools/dev/hud_capture.tscn -- --tag=<before|after> --round`, and
`--resolution 2400x1080`).

## 10. The token table (the Theme resource plan, C8)

The pages stay immediate-mode `Page` subclasses. Their theme is these constants and the two kit manifests. "New" marks
what §11 adds.

**Colour** (`scripts/ui/ui_kit.gd`):

| Token | Value | Used for |
|---|---|---|
| `INK` | #071015 | Outlines, shadows (`Color(INK, a)`), text on light faces |
| `RIVER_NIGHT` | #0a2027 | The flat fallback frame |
| `DEEP_TEAL` | #0d3035 | Placeholder and disc fills |
| `JADE_SHADOW` | #15514f | The Early band, the empty-slot motif |
| `JADE` | #2c9e8f | Progress fills, met dots, the scroll thumb, the Middle band |
| `BRIGHT_JADE` | #67d6bd | Positive words and marks |
| `BRONZE` | #9a6a35 | Rules, locks, drawn frames, the Late band |
| `GOLD` | #e5b84c | Headings, accent, merit, the Peak band |
| `PALE_GOLD` | #ffe6a1 | Titles, primary labels, selected tabs, names, key values |
| `PAPER` | #e8e1cf | Primary text |
| `MIST` | #afc9d1 | Secondary text, a toggle's Off |
| `RED` | #e45858 | Negative fills, badges, the ready seal |
| `RED_TEXT` (new) | #e87070 | Negative words |
| `WARNING` (new) | #f0a040 | Soft needs, moderate risk, a meter past its mark |
| `QI` | #32bed1 | Qi bars and words |
| `SOUL` | #9b78d1 | Soul bars |
| `SOUL_TEXT` (new) | #a586d6 | Soul words |
| `HP` (new) | #c2474f | The player's HP fill |
| `BLOOD` (new) | #b3202e | The Blood path, the heart demon, the boss trough |
| `HEART` (new) | #e05a6e | Affection |
| `SKY` (new) | #8fd3ff | Allies, side quests, tribulation bolts |
| `HOLLOW` | #87949a | Disabled and locked |
| `HUD_LABEL` (new) | #d5bd85 | The HUD's bar labels |
| `PAPER_INK` (new) | #2b2118 | Words on paper |
| `BAR_TROUGH` (new) | #17242c | Bar troughs |
| `PLATE` (new) | `Color(0.02, 0.06, 0.075, 0.72)` | Plates over the world |
| `DIM` (new) | `Color(0.01, 0.03, 0.04)` | The world behind a page, at 0.72 (0.55 modal) |
| `SURFACE` (new) | dictionary: `scroll`, `scroll_edge`, `sky_scroll`, `sky_scroll_edge`, `talisman`, `talisman_edge`, `brush_ink`, `cinnabar_ink`, `board`, `board_edge`, `board_line`, `stone_black`, `stone_white`, `stone_white_rim`, `wood`, `wood_dark`, `bridge`, `peg`, `peg_dark`, `hui`, `qin_silk`, `sky_top`, `sky_bottom`, `ember`; P5 adds the materials of `docs/page_identity.md` §7 (`gourd`, `gourd_dark`, `space`, `lacquer`, `lacquer_black`, `river_lacquer`, `bamboo`, `hemp`, `almanac`, `cinnabar`, `rubbing`, `stone`, `plaster`, `cloth`, `silk`, `sand`, `straw`, `soil`, `water`, `clay`), `cloth_wash`, the Bag's `sky` and `sea`, and the Revival niche's `niche`, each a mix of two tokens, with a `TEXT_ON` row for every one words are drawn on | Drawn page surfaces; P5 pages' own materials (`page_identity.md` §7, §8) |
| grade colours | `data/grades.json` `grade_colors` (sphere #9a87e3; law #a8c4ff, monarch #e6b3f2, inner_heaven #f4f7ff from P7b) | Item and technique names by grade |
| quality colours | `data/grades.json` `quality_colors` | Names and slot rims by quality |

**Type** (`scripts/ui/ui_kit.gd`): `MIN_SIZE` 14 (`:44`), `DISPLAY_MIN` 22 (`:40`), `PIXEL_NUMERALS_MIN` 20 (`:223`),
`WORD_SCALE` 1.2 (`:35`), `TEXT_SCALE` 1.0 (`:38`), `TEXT_SIZES` 0.92 / 1.0 / 1.12 (`:42`); faces `display_font`,
`text_font`, `label_font`, `body_font`, `symbols_font` (`:75`, `:80`, `:85`, `:90`, `:49`). New: the scale as
`T_HINT` 14, `T_CAPTION` 16, `T_ROW` 18, `T_BODY` 20, `T_BUTTON` 22, and display `D_SUB` 22, `D_HEADING` 26,
`D_DISPLAY` 30, `D_TITLE` 34.

**Layout** (`scripts/ui/page.gd`): `MIN_TAP` 48 (`:13`). New: `GRID` 8; `SAFE_AREA` (48, 24, 1184, 672); the windows
`WINDOW_FULL`, `WINDOW_LARGE`, `WINDOW_MEDIUM`, `WINDOW_SMALL`, `WINDOW_CONFIRM`, `WINDOW_DIALOGUE` (§2.2); `INSET` 32,
`TOP` 80, `TAB_H` 48, `TAB_GAP` 8, `TAB_MIN_W` 120, `ROW_GAP` 4, `GUTTER` 8, `GAP` 8, `GROUP_GAP` 16, `PAD` 16; `SLOT`
76, `SLOT_COMPACT` 48; `BTN_H` 48 / 56 / 64.

**Icons** (new, `UiKit`): `ICON` 64, `ICON_TECH_HUD` 48, `ICON_ITEM_SMALL` 32, `GLYPH` 32, `STATUS` 24.

**Formats**: `UiKit.fmt` (`:329`), `UiKit.pool_values` (`:326`), `UiKit.span` (`:317`), `UiKit.clock` (`:309`),
`Tx.plural` (`tx.gd:11`); new `UiKit.short`.

**Kit assets**, HD (`data/ui_assets_hd.json`, `"scale": 3`, margins in screen px):

| Asset | States | Margins | Used for |
|---|---|---|---|
| `major_window` | normal | 32 | Windows, the confirm dialog |
| `minor_panel` | normal (+ derived selected, disabled, pressed) | 12 | Cards, rows, the HUD player panel |
| `slot` | normal, selected, disabled (+ derived pressed) | 8 | Item slots, volume steps, name fields |
| `selected_slot_glow` | normal | 12 | The selection glow |
| `button_primary` | normal, pressed, disabled | 16 × 14 | Primary buttons (the face kept; labels inked, §1.5) |
| `button_secondary` | normal, pressed, disabled | 14 × 12 | Secondary buttons |
| `tab` | normal, selected (+ derived disabled) | 16 × 10 | Tabs |
| `title_plaque` | normal | 48 × 26 | Window titles, the dialogue speaker (the face kept; titles inked, §1.5) |
| `close_button` | normal, pressed | fixed 52 | Close |
| `toast` | normal | 20 × 12 | Toasts and HUD cards |
| `bar_shell` | normal | 10 × 8 | `Page.bar` |
| `currency_pill` | normal | 20 × 10 | Currencies |
| `minimap_frame` | normal | 24 | The minimap |
| `dialogue_box` | normal | 24 | Dialogue |
| `portrait_frame` | normal | 16 | The dialogue portrait |
| `realm_badge` | normal | 8 | The Cultivation level |
| `tooltip` | normal | 10 | Kept for P5's detail pop-ups |
| `hud_ring` (new) | normal, pressed, active; 132, 64, 52, 48 | fixed | Every HUD button, the party chips |

Pixel (`data/ui_assets.json`): nothing the HD kit has. The cloud-seal motif moves to the icon pipeline (§5).

## 11. Apply list

The second step, after the script refactor merges. Each step lands alone, with the check that proves it, and the audit
re-run. Screenshots are re-taken at the end and compared with the mockups (roadmap §3, P4 acceptance).

1. **Tokens, no visual change except the text colours.**
   - `scripts/ui/ui_kit.gd`: add the colour tokens of §10 and the `SURFACE` dictionary; `badge_color` and `draw_hearts`
     take tokens.
   - Every page in `scripts/ui/pages/` and `scripts/hud.gd`: replace each literal by its token (§1.6). `hud.gd:45` `GOLD`
     goes; `RED` and `SOUL` as text become `RED_TEXT` and `SOUL_TEXT`; the risk line (`breakthrough_page.gd:51`) takes
     `BRIGHT_JADE`.
   - `tools/data/stats.py:515`: `sphere` #9a87e3, and `law`, `monarch`, `inner_heaven` added; rebuild the data.
   - `ui_suite`: **no off-token colour** in `scripts/ui/pages/` and `hud.gd`. A static scan fails on any `Color("…")`
     and on any float `Color(r, g, b…)` that is not `Color(UiKit.X, a)` or a white modulate.
   - `ui_suite`: every grade in `grades.json` `order` has a colour.
2. **Contrast.**
   - Option C (decision 10, §1.5): primary labels in every state, page titles and the dialogue speaker drawn with a
     2 px ink outline (`UiKit.draw_inked`); the kit faces stay as they are.
   - `hud.gd:1556`, `ui_kit.gd:240`: plates in `PLATE`. `hud.gd:1866`: log words outlined.
   - `ui_suite`: **the contrast of every text token on its panel**. A table in `UiKit`, `TEXT_ON`, lists each text token
     with the fills it is drawn on and the smallest size it is drawn at. The check samples each fill's HD image inside its
     nine-slice centre (the lightest 95th-percentile texel, as the audit does) and asserts 4.5:1, or 3:1 for pairs drawn
     only at 20 px and up. It covers the label pairs of §1.4 too.
3. **Type.**
   - The 15 calls under 14 (§3 rule 1) move to 14. `beast_arena_page.gd:110` fits at 17. `Page.para` defaults to 18.
     Off-scale sizes move to the scale (§3 rule 5).
   - `hud.gd`: realm 16, bar labels 14.
   - `ui_suite`: **no text asked for under `MIN_SIZE`**. `Page._log_text` records the asked size; every page and tab
     asserts it is 14 or more; a static scan covers `hud.gd`'s `draw_text` and `draw_outlined` calls.
   - `ui_suite`: every asked size is on the scale.
4. **Numbers, durations, plurals.**
   - `UiKit.short` added; `world.gd:408` uses it; "a / b" in `hud.gd:1495-1502` and the two strings without spaces.
   - Every place in the §4 table calls `UiKit.span`; the retired keys leave `tools/data/ui_strings.json`.
   - `_one` twins for the plural keys the review keeps; their callers use `Tx.plural`.
   - `contract_tests`: no duration key outside `ui.span_*` and `ui.clock_days`; every counted plural string has its
     `_one`, or sits in a short reviewed allow-list of count-of-total strings.
5. **Spacing and windows.**
   - `scripts/ui/page.gd`: the layout constants; `_layout` (`:67-70`) with inset 32, top 80, tabs +56; `_draw_tabs`
     (`:138-151`) with 48 tall, gap 8, minimum 120; `list` (`:355-376`) gutter 8; the confirm dialog (`:380-386`); the
     toast (`:125-130`); the default modal (`:43`) becomes `WINDOW_SMALL`.
   - The 13 pages of §2.2 take a standard window; `dialogue_page.gd` moves inside the safe area; `your_sect_page.gd:17`,
     `:32` place from `content`.
   - The 26 list pitches of §2.1.
   - `ui_suite`: **every window is one of the standard set and inside the safe area**; every `list()` pitch is a multiple
     of 8; the existing overrun checks stay green.
6. **Slots and icon sizes.**
   - `Page.slot_box` (`page.gd:278`): the 76 px slot draws the icon 1:1 at inset 6; the 48 px compact slot draws the
     `@32` variant at inset 8; the slot draws the grade halo (§8.3 rule 7).
   - Every caller moves to one of the two slots; rows with a page slot take a pitch of 88; the Bag's grid holds five
     columns (§2.3). `Page.icon_at` draws only allowed sizes.
   - `character_page.gd:21`: the figure at scale 2.5.
   - The HUD glyphs at 32 (`hud.gd:1330`, `:1398`, `:1767`, `:1772`, `:1777`, `:1790`, `:1802`, `:1841`, `:1845`); the
     coin and the spirit stone at 32 in a 40 px pill.
   - `ui_suite`: **every icon draw size is allowed** for its kind (an icon log beside `text_log`). HUD item and technique
     rings switch to `@32` and `@48` once step 9 writes them; until then they are listed in the check as known cases.
7. **States.**
   - `settings_page.gd:34`, `:90`: `selected` for on; Off in `MIST`.
   - `map_page.gd:265`, `cultivation_page.gd:138`: the "you" and "now" mark.
   - `ui_suite`: no page draws `pressed` except for the region under the finger.
8. **Touch.**
   - `hud.gd:217` Draught hit r 24; `:231` bag animals hit r 24; `:1565` the tracker's go button 48 × 48; `:232` the panel
     rect follows the panel's height.
   - A new `hud_suite` in `rules_tests`: every HUD target's hit radius is 24 or more and at least the drawn radius + 4;
     overlapping circles resolve to the nearest centre.
9. **Kits and icons (P4b).**
   - `tools/ui/build_ui_hd.py`: `hud_ring` (132, 64, 52, 48; normal, pressed, active); `hud.gd ring()` draws it.
   - `tools/ui/build_ui.py`, `data/ui_assets.json`: `hud_circle*` and every asset the HD kit has, with their PNGs, go.
   - The icon pipeline (the study's plan): a 64 px canvas mode in `tools/icons/pix.py`, `Mat` and `mat7` in `palette.py`,
     the finishing passes (texture, rim light, selective outline), the missing grade kits, `FAMILY_SIZE` items,
     equipment and techniques 64 and hud 32 at scale 1, the `@48` and `@32` variants in the manifest, contact sheets in
     76 px slots. The twelve study icons rebuild within a few pixels of the study; untouched families stay byte-identical.
   - The cloud-seal motif, built by the pipeline; `hud.gd:1335`, `:1810` stop loading the pixel one.
   - Families redrawn in the study's order (HUD, techniques, pills, weapons, armour, then the item groups), a family at a
     time, each sheet to the user before the next family starts on the same page.
   - `ui_suite`: no script loads `res://art/ui/` by path; no asset name is in both manifests.
   - `docs/mockups/kit/kit.css` and its README follow: the 76 px slot, the new faces and tokens, the HUD table of §9.
10. **P5a, from this guide and decision 8.**
    - The HUD of §9.
    - The Bag as the jade chest on the 80 px slot pitch, **with the character's live figure** (`Avatar`, built from the
      real sprite layers, as `inventory_page.gd:20-25` draws it today) wearing the equipped pieces and the equipment
      slots round it.
    - The Character page shows the same figure with its slots round it (`character_page.gd:18-22`). A row of slots
      with no figure is not enough.
11. **Close.**
    - Re-take every screenshot in `docs/ui_inventory/` and compare with mockups 00–05.
    - A `docs/CHANGELOG.md` entry under "The UI review and restyle".
    - The roadmap rows U22–U29 set to Present.

## 12. Applied

The apply list landed in seven steps, each with its check in `tests/` and the full suite green; decision 10 (option C)
replaced step 2's darker faces, and the icon pipeline had already done most of steps 6 and 9. What each step changed:

| Step | What landed | Its check |
|---|---|---|
| 1 Tokens | The tokens of §10 and `SURFACE` in `UiKit`; every hex and float literal in the pages, `Page` and `hud.gd` a token, `Color(token, a)` or a white modulate; `RED` and `SOUL` words `RED_TEXT` and `SOUL_TEXT`; `hud.gd`'s own `GOLD` gone; the grade colours of §1.5 in `tools/data/stats.py`; the HUD rings drawn from the HD kit's `hud_ring_132`, `_64`, `_52` and `_48` (normal, pressed, active) | `rules_tests` `ui_style_suite`: no off-token colour; every grade has a colour |
| 2 Contrast | Option C: primary labels in every state, page titles and the dialogue speaker inked (`UiKit.draw_inked`, 2 px); `PLATE` at 0.72 under the tracker, the run banner and nameplates; the HUD log outlined; `UiKit.TEXT_ON` | Every `TEXT_ON` pair, and every grade and quality colour, measured on the kit's own art |
| 3 Type | Every literal size on the scale of §3; nothing asked for under 14; `Page.btn` and `Page.heading` step down the scale; `Page.para` 18; `Page.bar`'s label 16; the HUD realm 16 and bar labels 14 | Every word every page draws, and every HUD text call, on the scale and at 14 or more |
| 4 Numbers, durations, plurals | `UiKit.short` ("18.2K") on the damage numbers; "a / b" with spaces; `Tx.span` the one duration writer (`UiKit.span` calls it; a whole hour or day drops its zero); every place of §4 and every string that wrote its own time unit takes a span; 75 new `_one` twins, called through `Tx.plural` | `contract_tests`: no string prints a count before a time unit but the span's own and eight rule lengths in prose; every counted plural has its twin or counts a total |
| 5 Spacing | The layout constants of §10 in `Page`; content 32 in and 80 under the title, tabs 48 tall and 8 apart, the confirm dialog, toast and list gutter of §2.1; the twelve windows of their own standard, the dialogue strip inside the safe area; the 22 list pitches; the Bag grid 16 px from its detail panel; the HUD icon row on a 56 px pitch. The Character page figure at 3x (from 2.4) with the worn slots round it, drawn by the Bag's own `InventoryPage.draw_worn` | Every window standard and inside the safe area; every list pitch on the grid |
| 6 States | Settings' on in the selected art, Off in `MIST`; "you" and "now" as a gold ◆ with the name in `PALE_GOLD` on the Heaven Ranking, the Body tab, Roll-Call and Characters | No page draws pressed but under the finger |
| 7 Touch | `hud.gd` `hit_targets`: every round control at least 24 and its drawn radius + 4 (the Draught, the bag animals, the icon row); where circles overlap the nearest centre wins; the tracker's go button 48 × 48; the player panel's target follows its height | `rules_tests` `hud_suite` |

The audit (`tools/dev/ui_style_audit.py`) before the first step and after the last:

| Measure | Before | After |
|---|---|---|
| Hex colour literals in the pages and `hud.gd` | 64 | 0 |
| Float `Color()` literals there | 55 | 0 |
| Grades with no colour | 3 (law, monarch, inner_heaven) | 0 |
| Text colours under 4.5:1 on the lightest page fill | 5 (`JADE`, `BRONZE`, `RED`, `SOUL`, `sphere`) | 0 (the first four colour fills only; words take `BRIGHT_JADE`, `RED_TEXT`, `SOUL_TEXT`) |
| Label pairs short of their mark (§1.4) | 5 (the primary label twice, the titles twice, the disabled primary) | 0 |
| `MIST` on a plate over a white sky | 2.47 (tracker, 0.55), 3.15 (nameplate, 0.62) | 4.56 (`PLATE`, 0.72) |
| Text sizes asked for under 14 | 15 | 0 |
| Pages with a window of their own | 13 | 0 |
| `list()` pitches off the 8 px grid | 22 | 0 |
| Plural keys with a `_one` twin / without | 9 / 105 | 84 / 15 (the reviewed count-of-total list) |
| Literal icon boxes off the allowed sizes | 11 | 11: boxes that `SpriteCache.draw_icon` fills at a whole-number scale; the `ui_suite` checks every icon as drawn |

What is left stays with its phase: the HUD's ring layout, party chips and boss bar of §9 (P5a); the empty-slot motif and
the pixel kit's copies of the HD assets (the rest of step 9); and the literal icon boxes above. The re-taken screenshots
are in `docs/ui_after_p4/`.
