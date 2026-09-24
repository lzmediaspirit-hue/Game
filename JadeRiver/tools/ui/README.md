# UI kit generator

```
python3 tools/ui/build_ui.py      # -> art/ui/<asset>__<state>.png + data/ui_assets.json
```

Deterministic (byte-identical on re-run). Uses the shared pixel library in
`tools/props/pixlib.py` and ramps from `tools/props/palette.py`.

* Authored at art pixels and saved x2 nearest, like all game art (a 256x256 window
  is a 128x128 art canvas; a 2 px screen line is one art pixel).
* Frames are painted as concentric rings of a rounded rectangle (distance-to-edge
  bands, per-side bevel colours). Ornaments sit only inside the corner squares, so
  every edge is constant along its stretch axis and panels stretch or tile with no
  seams. The review sheet shows each asset stretched with a nine-slice renderer.
* Palette: ink `#071015` outer line, dark teal fill `#0A2027`, jade inner lines,
  warm gold / pale gold / aged bronze trim, paper `#E8E1CF` for dialogue.

## Manifest (`data/ui_assets.json`)

```json
"button_primary": {"normal": "res://art/ui/button_primary__normal.png",
                   "pressed": "res://art/ui/button_primary__pressed.png",
                   "disabled": "res://art/ui/button_primary__disabled.png",
                   "margins": [16, 14, 16, 14]}
```

One key per state; `margins` = `[left, top, right, bottom]` nine-slice margins in
screen px. Fixed-size art (HUD circles, close button, empty-slot motif) has
margins `[0, 0, 0, 0]`: draw it unstretched.

| Asset | Size | States | Margins |
|---|---|---|---|
| major_window | 256x256 | normal | 24 |
| minor_panel | 128x128 | normal | 12 |
| tooltip | 96x96 | normal | 10 |
| slot | 64x64 | normal, selected, disabled | 8 |
| slot_empty_motif | 64x64 | normal (transparent overlay) | 0 |
| selected_slot_glow | 72x72 | normal (transparent centre) | 12 |
| button_primary | 192x64 | normal, pressed, disabled | 16/14 |
| button_secondary | 160x56 | normal, pressed, disabled | 14/12 |
| tab | 128x48 | normal, selected (open bottom) | 16/10 |
| toast | 256x64 | normal | 20/12 |
| bar_shell | 256x32 | normal | 10/8 |
| title_plaque | 384x72 | normal | 48/16 |
| currency_pill | 160x40 | normal | 20/10 |
| close_button | 52x52 | normal, pressed | 0 |
| hud_circle_large / hud_circle / hud_circle_small | 132 / 64 / 52 | normal, pressed, active | 0 |
| dialogue_box | 256x128 | normal | 24 |
| portrait_frame | 96x96 | normal (transparent centre) | 16 |
| minimap_frame | 232x140 | normal (22 px header band) | 24 |
| realm_badge | 64x24 | normal | 8 |
