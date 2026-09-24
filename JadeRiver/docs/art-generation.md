# Generated environment artwork

Tool: built-in image_gen; no API/CLI fallback used.

## art/environment/sanctuary.png

Use case: stylized-concept. Generate a wide landscape 2D game background, 3:2 or 16:9 landscape. A beautiful finely detailed painterly pixel-art wuxia / xianxia mountain sanctuary at blue twilight: layered misty karst peaks, distant tiered Chinese temple roofs, waterfalls descending floating mountains, jade blue trees, warm amber temple windows, turquoise river at bottom. Atmospheric layered environment, strong teal/navy/antique gold palette. Panoramic side-scrolling game background and character selection backdrop, like premium 2D pixel RPG concept art. Clear quieter central area and readable scenery silhouettes. Scenery only: NO people, characters, animals, monsters, NPCs, boats, loose items, foreground props, UI, text, letters, logos, frames, buttons or icons. Temples and cliffs are part of the distant landscape, bottom is misty river. Save final image.

## art/environment/terrain-atlas.png

Use case: stylized-concept. Asset: 2D wuxia game terrain texture atlas, square 1024x1024, precisely FOUR equal edge-to-edge square quadrants, 2 by 2, no margins or dividing lines. Each quadrant a full flat seamless material texture, orthographic top-down, detailed painterly pixel-art style with fine crisp pixels. TOP LEFT: weathered blue-grey jade stone courtyard paving, small rectangular flagstones with subtle moss in seams. TOP RIGHT: traditional Chinese dark teal ceramic roof tiles in parallel horizontal rows, fine ridges and lichen, restrained jade highlights. BOTTOM LEFT: aged dark warm timber planks horizontal grain, subtle carved wear. BOTTOM RIGHT: dark grey temple masonry wall blocks with subtle mortar and age. Consistent subdued blue twilight illumination. Fine-scale surfaces for a side-scrolling xianxia RPG, game-quality richly textured. No text, no labels, no diagrams, no characters, no objects, no ornaments, no borders, no buildings or perspective scene. Only the four flat material swatches exactly aligned to quadrants.

The returned atlas is used at its supplied resolution, with quadrants addressed proportionally. UI borders and controls are native Godot drawing; the supplied character sprites were recovered, not regenerated.

## Version 0.2 — art/environment/sanctuary-pixel.png

Tool: built-in image_gen. No CLI/API fallback. Final image copied into the project and used by `scripts/backdrop.gd`.

Prompt:
Create ONLY a wide 16:9 background panorama for a 2D wuxia/xianxia pixel-art game. Strict authentic low-resolution pixel art, visible large square pixels, limited 32-color palette, hard pixel clusters, no smooth painting, no antialiasing, no gradients. Looks like a 640x360 game scene enlarged exactly 2x with nearest-neighbor sampling. Jade blue karst mountains, distant Chinese pagodas with curved teal roofs and tiny amber windows, terraced mountain monasteries, mist bands, waterfalls and river, quiet blue evening moonlight. Broad open middle and foreground for player visibility; architecture belongs in distant background. Beautiful handcrafted 16-bit fantasy game scenery. Flat side-scrolling view, layered silhouettes, dark navy, jade, turquoise, muted amber highlights. NO UI, lettering, frames, characters, creatures, NPCs, loot, loose objects, tree-to-cloud climbing route, floating platform chain. Scenery only. Pixel art all the way through, bold readable clusters rather than photographic texture.

The earlier panorama and terrain atlas above are retained as source references. Version 0.2 uses native pixel tile drawing instead of the earlier atlas. All runtime content is additionally rendered through the 640x360 nearest-neighbor viewport.

## Version 0.3
Full new prompts, final paths, and transparency-handling notes are in [art-v03-prompts.md](art-v03-prompts.md).

## Version 0.4

The reference-matched prop, building, and staircase prompts and generated-source paths are in [art-v04-prompts.md](art-v04-prompts.md).

