extends RefCounted
## The page registry (decision 45, S7; docs/architecture/shell.md): every page id the shell opens, and the script that
## draws it. Page ids that share a script are one page opened on another of its views (the Codex's Collection, Seasons
## and Achievements; the crafts' benches; the Cultivation page's Seclusion, Heart and Body). A page sets its own title
## and tabs, and what unlocks it is the Menu's and the HUD's to say; the shell only opens what it is asked for
## (main.gd `open_page`). Ids that start with "_" are not pages: the shell answers them itself (main.gd `ACTIONS`).
##
## `tools/data/tutorials.py` reads PAGES from this file's text into tutorials.json's page map, so keep its shape: one
## `"id": "res://scripts/ui/pages/<file>.gd",` a line.

const PAGES := {
	"menu": "res://scripts/ui/pages/menu_page.gd",
	"inventory": "res://scripts/ui/pages/inventory_page.gd",
	"character": "res://scripts/ui/pages/character_page.gd",
	"cultivation": "res://scripts/ui/pages/cultivation_page.gd",
	"breakthrough": "res://scripts/ui/pages/breakthrough_page.gd",
	"techniques": "res://scripts/ui/pages/techniques_page.gd",
	"quests": "res://scripts/ui/pages/quest_page.gd",
	"world_map": "res://scripts/ui/pages/map_page.gd",
	"codex": "res://scripts/ui/pages/codex_page.gd",
	"collection": "res://scripts/ui/pages/codex_page.gd",
	"seasons": "res://scripts/ui/pages/codex_page.gd",
	"mail": "res://scripts/ui/pages/mail_page.gd",
	"shop": "res://scripts/ui/pages/shop_page.gd",
	"storage": "res://scripts/ui/pages/storage_page.gd",
	"characters": "res://scripts/ui/pages/characters_page.gd",
	"settings": "res://scripts/ui/pages/settings_page.gd",
	"dialogue": "res://scripts/ui/pages/dialogue_page.gd",
	"welcome": "res://scripts/ui/pages/welcome_page.gd",
	"posts": "res://scripts/ui/pages/posts_page.gd",
	"pouches": "res://scripts/ui/pages/pouches_page.gd",
	"works": "res://scripts/ui/pages/works_page.gd",
	"revival": "res://scripts/ui/pages/revival_page.gd",
	"teleport": "res://scripts/ui/pages/teleport_page.gd",
	"transfer_array": "res://scripts/ui/pages/array_page.gd",
	"emotes": "res://scripts/ui/pages/emotes_page.gd",
	"notice_board": "res://scripts/ui/pages/notice_page.gd",
	"training_sect": "res://scripts/ui/pages/training_sect_page.gd",
	"your_sect": "res://scripts/ui/pages/your_sect_page.gd",
	"spirit_animals": "res://scripts/ui/pages/pets_page.gd",
	"beast_arena": "res://scripts/ui/pages/beast_arena_page.gd",
	"relations": "res://scripts/ui/pages/relations_page.gd",
	"gift": "res://scripts/ui/pages/gift_page.gd",
	"mercy": "res://scripts/ui/pages/mercy_page.gd",
	"calendar": "res://scripts/ui/pages/calendar_page.gd",
	"tower": "res://scripts/ui/pages/tower_page.gd",
	"county": "res://scripts/ui/pages/county_page.gd",
	"guqin": "res://scripts/ui/pages/guqin_page.gd",
	"chess": "res://scripts/ui/pages/chess_page.gd",
	"companions": "res://scripts/ui/pages/companions_page.gd",
	"crafts": "res://scripts/ui/pages/crafts_page.gd",
	"cooking": "res://scripts/ui/pages/crafts_page.gd",
	"alchemy": "res://scripts/ui/pages/crafts_page.gd",
	"forge": "res://scripts/ui/pages/crafts_page.gd",
	"formations": "res://scripts/ui/pages/workshop_page.gd",
	"workshop": "res://scripts/ui/pages/workshop_page.gd",
	"talisman": "res://scripts/ui/pages/crafts_page.gd",
	"guild": "res://scripts/ui/pages/crafts_page.gd",
	"arrays": "res://scripts/ui/pages/crafts_page.gd",
	"charts": "res://scripts/ui/pages/crafts_page.gd",
	"vessels": "res://scripts/ui/pages/crafts_page.gd",
	"garden": "res://scripts/ui/pages/garden_page.gd",
	"core_exchange": "res://scripts/ui/pages/core_exchange_page.gd",
	"fishing": "res://scripts/ui/pages/fishing_page.gd",
	"seclusion": "res://scripts/ui/pages/cultivation_page.gd",
	"heart": "res://scripts/ui/pages/cultivation_page.gd",
	"body": "res://scripts/ui/pages/cultivation_page.gd",
	"fates": "res://scripts/ui/pages/fates_page.gd",
	"library": "res://scripts/ui/pages/shop_page.gd",
	"exchange": "res://scripts/ui/pages/exchange_page.gd",
	"auction": "res://scripts/ui/pages/auction_page.gd",
	"achievements": "res://scripts/ui/pages/codex_page.gd",
}

## The script a page id opens ("" when the id is no page).
static func script_of(id: String) -> String:
	return str(PAGES.get(id, ""))

## Every page script, in the table's order, once for each id that opens it (the order PageWarmer compiles them in).
static func scripts() -> Array:
	return PAGES.values()
