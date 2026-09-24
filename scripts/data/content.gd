# Generated content tables (stable IDs). Edit here; code reads them via Content.X
class_name Content
extends RefCounted

const ABILITIES = {
	"step": {
		"name": "Step",
		"source": "universal",
		"qi": 0,
		"cd": 0.7,
		"desc": "Dash through danger. Brief evasion.",
		"icon": "step"
	},
	"crescent": {
		"name": "Crescent Slash",
		"source": "weapon",
		"family": "sword",
		"req": {
			"mastery": 20
		},
		"qi": 10,
		"cd": 2.5,
		"dmg": 1.8,
		"reach": 46,
		"shape": "arc",
		"desc": "A wide crescent of Qi in front.",
		"icon": "crescent"
	},
	"swift_draw": {
		"name": "Swift Draw",
		"source": "weapon",
		"family": "sword",
		"req": {
			"mastery": 40,
			"parent": "crescent"
		},
		"qi": 12,
		"cd": 3.5,
		"dmg": 2.2,
		"reach": 90,
		"shape": "lunge",
		"desc": "Dash forward and cut through the line.",
		"icon": "lunge"
	},
	"parry_counter": {
		"name": "Parry Counter",
		"source": "weapon",
		"family": "sword",
		"req": {
			"mastery": 60,
			"parent": "swift_draw"
		},
		"qi": 10,
		"cd": 5,
		"dmg": 2.6,
		"reach": 40,
		"shape": "parry",
		"desc": "Brief parry window; retaliate on block.",
		"icon": "parry"
	},
	"flow_combo": {
		"name": "Flow Combo",
		"source": "weapon",
		"family": "sword",
		"req": {
			"mastery": 60,
			"realm": 1,
			"parent": "swift_draw"
		},
		"qi": 18,
		"cd": 5,
		"dmg": 1.2,
		"hits": 4,
		"reach": 44,
		"shape": "combo",
		"desc": "Four flowing cuts that can strike upward.",
		"icon": "combo"
	},
	"heaven_splitter": {
		"name": "Heaven Splitter",
		"source": "weapon",
		"family": "sword",
		"req": {
			"mastery": 60,
			"realm": 2,
			"cls": "blade_adept",
			"parent": "swift_draw"
		},
		"qi": 30,
		"cd": 8,
		"dmg": 5,
		"reach": 140,
		"shape": "wave",
		"desc": "A towering blade wave that crosses heights.",
		"icon": "wave"
	},
	"spear_thrust": {
		"name": "Spear Thrust",
		"source": "weapon",
		"family": "spear",
		"req": {
			"mastery": 20
		},
		"qi": 10,
		"cd": 2.5,
		"dmg": 2,
		"reach": 62,
		"shape": "thrust",
		"desc": "A piercing thrust that passes through foes.",
		"icon": "thrust"
	},
	"long_thrust": {
		"name": "Long Thrust",
		"source": "weapon",
		"family": "spear",
		"req": {
			"mastery": 40,
			"parent": "spear_thrust"
		},
		"qi": 12,
		"cd": 3.5,
		"dmg": 2.2,
		"reach": 100,
		"shape": "lunge",
		"desc": "Lunge far forward, spear leading.",
		"icon": "lunge"
	},
	"guarding_spear": {
		"name": "Guarding Spear",
		"source": "weapon",
		"family": "spear",
		"req": {
			"mastery": 60,
			"parent": "long_thrust"
		},
		"qi": 10,
		"cd": 6,
		"dmg": 1.5,
		"reach": 50,
		"shape": "spin",
		"desc": "Spin the shaft: knock back and guard for a moment.",
		"icon": "spin"
	},
	"flowing_spear": {
		"name": "Flowing Spear",
		"source": "weapon",
		"family": "spear",
		"req": {
			"mastery": 60,
			"realm": 1,
			"parent": "long_thrust"
		},
		"qi": 18,
		"cd": 5,
		"dmg": 1.3,
		"hits": 4,
		"reach": 60,
		"shape": "combo",
		"desc": "A river of thrusts that can strike upward.",
		"icon": "combo"
	},
	"dragon_art": {
		"name": "Dragon Art",
		"source": "weapon",
		"family": "spear",
		"req": {
			"mastery": 60,
			"realm": 2,
			"cls": "spear_warden",
			"parent": "long_thrust"
		},
		"qi": 40,
		"cd": 8,
		"dmg": 5.5,
		"reach": 150,
		"shape": "wave",
		"desc": "Unleash the dragon’s might. A decisive spear technique that channels your inner flow.",
		"icon": "dragon"
	},
	"nova": {
		"name": "Nova",
		"source": "realm",
		"req": {
			"realm": 1
		},
		"qi": 22,
		"cd": 6,
		"dmg": 2.4,
		"reach": 70,
		"shape": "nova",
		"desc": "A burst of Qi around you. Hits all heights nearby.",
		"icon": "nova"
	},
	"mend": {
		"name": "Mend",
		"source": "realm",
		"req": {
			"realm": 2
		},
		"qi": 25,
		"cd": 12,
		"heal": 45,
		"shape": "heal",
		"desc": "Circulate Qi to heal 45 HP.",
		"icon": "mend"
	},
	"spirit_bolt": {
		"name": "Spirit Bolt",
		"source": "class",
		"req": {
			"cls": "spirit_sage"
		},
		"qi": 8,
		"cd": 1.2,
		"dmg": 1.6,
		"reach": 220,
		"shape": "bolt",
		"desc": "A darting bolt of Qi.",
		"icon": "bolt"
	}
}

const BODY_BRANCHES = [
	{
		"id": "endurance",
		"name": "Endurance",
		"max": 3,
		"per": "+10 max HP",
		"desc": "Temper skin and bone against blows."
	},
	{
		"id": "guard",
		"name": "Guard Stability",
		"max": 3,
		"per": "+8% guard reduction",
		"desc": "Root the stance so a guard holds."
	},
	{
		"id": "mobility",
		"name": "Mobility",
		"max": 3,
		"per": "+4% move speed, -8% Step cooldown",
		"desc": "Light feet across roof and bridge."
	}
]

const BUY_MARKUP = 3

const CLASSES = {
	"blade_adept": {
		"id": "blade_adept",
		"name": "Blade Adept",
		"desc": "Sword timing and footwork. +12% sword damage, faster recovery.",
		"bonus": {
			"swordDmg": 0.12,
			"atkSpeed": 0.1
		}
	},
	"spear_warden": {
		"id": "spear_warden",
		"name": "Spear Warden",
		"desc": "Reach, control and durability. +12% spear damage, +15 HP.",
		"bonus": {
			"spearDmg": 0.12,
			"hp": 15
		}
	},
	"spirit_sage": {
		"id": "spirit_sage",
		"name": "Spirit Sage",
		"desc": "Qi management and technique reach. +20 Qi, arts cost 15% less.",
		"bonus": {
			"qi": 20,
			"artCost": 0.15
		}
	}
}

const CLASS_RETRAIN_FEE = 150

const CLOTHES = [
	{
		"id": "river_traveler",
		"name": "River Traveler",
		"main": "#1f6b5a",
		"trim": "#d8b35a",
		"under": "#e8e0cc",
		"sash": "#b8862e"
	},
	{
		"id": "crimson_adept",
		"name": "Crimson Adept",
		"main": "#9c2a2a",
		"trim": "#e0b050",
		"under": "#2a1a1a",
		"sash": "#e0b050"
	},
	{
		"id": "cloud_scholar",
		"name": "Cloud Scholar",
		"main": "#dfe6ef",
		"trim": "#3b5fa8",
		"under": "#8fa7d0",
		"sash": "#3b5fa8"
	},
	{
		"id": "jade_sentinel",
		"name": "Jade Sentinel",
		"main": "#2c4a3a",
		"trim": "#c9a54a",
		"under": "#1a2a22",
		"sash": "#6b8f4a"
	}
]

const DAOS = {
	"river": {
		"id": "river",
		"name": "River Dao — Flow",
		"desc": "Arts flow onward: technique hits restore 3 Qi and art projectiles pierce.",
		"ranks": [
			0,
			20,
			60,
			140
		]
	},
	"ember": {
		"id": "ember",
		"name": "Ember Dao — Fire",
		"desc": "Arts kindle: technique hits burn for extra damage over time.",
		"ranks": [
			0,
			20,
			60,
			140
		]
	}
}

const ENEMIES = {
	"raider": {
		"name": "River Raider",
		"hp": 40,
		"atk": 8,
		"speed": 0.85,
		"reach": 24,
		"xp": 12,
		"coins": [
			3,
			7
		],
		"look": "raider",
		"drops": [
			[
				"dust",
				0.25
			]
		],
		"windup": 26,
		"cd": 70
	},
	"archer": {
		"name": "Raider Archer",
		"hp": 32,
		"atk": 7,
		"speed": 0.7,
		"reach": 170,
		"ranged": true,
		"xp": 14,
		"coins": [
			3,
			8
		],
		"look": "archer",
		"drops": [
			[
				"dust",
				0.3
			]
		],
		"windup": 40,
		"cd": 110
	},
	"heavy": {
		"name": "Iron Brute",
		"hp": 120,
		"atk": 17,
		"speed": 0.55,
		"reach": 30,
		"xp": 32,
		"coins": [
			8,
			15
		],
		"look": "heavy",
		"scale": 1.25,
		"drops": [
			[
				"dust",
				0.6
			],
			[
				"hide",
				0.2
			]
		],
		"windup": 48,
		"cd": 100,
		"poise": true
	},
	"wolf": {
		"name": "Bamboo Wolf",
		"hp": 50,
		"atk": 10,
		"speed": 1.3,
		"reach": 22,
		"xp": 18,
		"coins": [
			0,
			3
		],
		"look": "wolf",
		"quad": true,
		"drops": [
			[
				"hide",
				0.6
			],
			[
				"core",
				0.04
			]
		],
		"windup": 22,
		"cd": 70
	},
	"spirit_wolf": {
		"name": "Black Wind Wolf",
		"hp": 90,
		"atk": 15,
		"speed": 1.4,
		"reach": 24,
		"xp": 32,
		"coins": [
			2,
			6
		],
		"look": "spirit_wolf",
		"quad": true,
		"drops": [
			[
				"hide",
				0.5
			],
			[
				"core",
				0.25
			]
		],
		"windup": 20,
		"cd": 64
	},
	"acolyte": {
		"name": "Black Wind Acolyte",
		"hp": 95,
		"atk": 14,
		"speed": 0.75,
		"reach": 190,
		"ranged": true,
		"bolt": true,
		"xp": 36,
		"coins": [
			8,
			16
		],
		"look": "acolyte",
		"drops": [
			[
				"dust",
				0.7
			],
			[
				"spirit_shard",
				0.15
			]
		],
		"windup": 44,
		"cd": 100
	},
	"echo": {
		"name": "Inner Echo",
		"hp": 60,
		"atk": 12,
		"speed": 1,
		"reach": 26,
		"xp": 0,
		"coins": [
			0,
			0
		],
		"look": "echo",
		"drops": [],
		"windup": 26,
		"cd": 70
	},
	"captain": {
		"name": "Black River Captain",
		"boss": true,
		"hp": 380,
		"atk": 14,
		"speed": 0.95,
		"reach": 30,
		"xp": 120,
		"coins": [
			60,
			60
		],
		"look": "captain",
		"scale": 1.4,
		"drops": [
			[
				"dust",
				1
			],
			[
				"hide",
				1
			]
		],
		"windup": 30,
		"cd": 60,
		"poise": true
	},
	"sentinel": {
		"name": "Reed Sentinel",
		"boss": true,
		"hp": 760,
		"atk": 20,
		"speed": 0.7,
		"reach": 36,
		"xp": 260,
		"coins": [
			120,
			120
		],
		"look": "sentinel",
		"scale": 1.8,
		"drops": [
			[
				"core",
				1
			],
			[
				"vein_crystal",
				1
			]
		],
		"windup": 40,
		"cd": 70,
		"poise": true
	},
	"qiu": {
		"name": "Master Qiu",
		"boss": true,
		"hp": 1300,
		"atk": 24,
		"speed": 1,
		"reach": 34,
		"xp": 500,
		"coins": [
			300,
			300
		],
		"look": "qiu",
		"scale": 1.5,
		"drops": [
			[
				"core",
				2
			],
			[
				"source_crystal",
				1
			]
		],
		"windup": 30,
		"cd": 60,
		"poise": true
	}
}

const HAIR = [
	{
		"id": "topknot",
		"name": "Topknot"
	},
	{
		"id": "windswept",
		"name": "Windswept"
	},
	{
		"id": "silver_tail",
		"name": "Silver Tail"
	},
	{
		"id": "plum_bob",
		"name": "Plum Bob"
	}
]

const ITEMS = {
	"training_sword": {
		"name": "Training Sword",
		"kind": "weapon",
		"family": "sword",
		"atk": 2,
		"rank": 0,
		"value": 5,
		"icon": "sword",
		"tint": "#9aa3a8",
		"desc": "A wooden-hilted practice blade."
	},
	"training_spear": {
		"name": "Training Spear",
		"kind": "weapon",
		"family": "spear",
		"atk": 3,
		"rank": 0,
		"value": 5,
		"icon": "spear",
		"tint": "#9aa3a8",
		"desc": "A plain ash-wood spear."
	},
	"bronze_sword": {
		"name": "Bronze Jian",
		"kind": "weapon",
		"family": "sword",
		"atk": 6,
		"rank": 0,
		"value": 40,
		"icon": "sword",
		"tint": "#d08a4a",
		"desc": "Balanced bronze blade."
	},
	"bronze_spear": {
		"name": "Bronze Spear",
		"kind": "weapon",
		"family": "spear",
		"atk": 7,
		"rank": 0,
		"value": 40,
		"icon": "spear",
		"tint": "#d08a4a",
		"desc": "Bronze head on a lacquered shaft."
	},
	"steel_sword": {
		"name": "Steel Jian",
		"kind": "weapon",
		"family": "sword",
		"atk": 13,
		"rank": 3,
		"value": 120,
		"icon": "sword",
		"tint": "#cfe0ea",
		"desc": "Folded steel, keen and light."
	},
	"steel_spear": {
		"name": "Steel Spear",
		"kind": "weapon",
		"family": "spear",
		"atk": 15,
		"rank": 3,
		"value": 120,
		"icon": "spear",
		"tint": "#cfe0ea",
		"desc": "Steel spear with a red tassel."
	},
	"jade_sword": {
		"name": "Jadeflow Jian",
		"kind": "weapon",
		"family": "sword",
		"atk": 22,
		"rank": 6,
		"realm": 2,
		"value": 400,
		"icon": "sword",
		"tint": "#5fe0b8",
		"desc": "Jade alloy that hums with Qi."
	},
	"jade_spear": {
		"name": "Jadeflow Spear",
		"kind": "weapon",
		"family": "spear",
		"atk": 25,
		"rank": 6,
		"realm": 2,
		"value": 400,
		"icon": "spear",
		"tint": "#5fe0b8",
		"desc": "A jade-alloy spear that channels flow."
	},
	"straw_hat": {
		"name": "Straw Hat",
		"kind": "cosmetic",
		"slot": "hat",
		"value": 15,
		"icon": "hat",
		"desc": "Keeps the river sun off. Cosmetic."
	},
	"jade_crown": {
		"name": "Jade Hairpiece",
		"kind": "cosmetic",
		"slot": "hat",
		"value": 60,
		"icon": "crown",
		"desc": "A disciple’s jade ornament. Cosmetic."
	},
	"gourd": {
		"name": "Wine Gourd",
		"kind": "cosmetic",
		"slot": "gourd",
		"value": 10,
		"icon": "gourd",
		"desc": "A travelling gourd. Cosmetic."
	},
	"pick": {
		"name": "Bronze Pick",
		"kind": "tool",
		"tool": "mining",
		"value": 0,
		"icon": "pick",
		"desc": "Starter mining pick. Required to mine veins and crystals."
	},
	"kit": {
		"name": "Harvest Kit",
		"kind": "tool",
		"tool": "herbalism",
		"value": 0,
		"icon": "kit",
		"desc": "Sickle and pouch for herbs."
	},
	"rod": {
		"name": "Bamboo Rod",
		"kind": "tool",
		"tool": "fishing",
		"value": 0,
		"icon": "rod",
		"desc": "A light bamboo fishing rod."
	},
	"steel_pick": {
		"name": "Steel Pick",
		"kind": "tool",
		"tool": "mining",
		"speed": 0.6,
		"value": 80,
		"icon": "pick2",
		"desc": "Mines 40% faster."
	},
	"copper": {
		"name": "Copper Ore",
		"kind": "material",
		"value": 6,
		"icon": "ore",
		"tint": "#c96b3c",
		"source": "River Outskirts",
		"desc": "A common ore found in the river quarries. Useful for crafting and upgrades."
	},
	"iron": {
		"name": "Iron Ore",
		"kind": "material",
		"value": 12,
		"icon": "ore",
		"tint": "#7d8a98",
		"source": "Whispering Bamboo",
		"desc": "Dense grey ore from the bamboo cliffs."
	},
	"jade_ore": {
		"name": "Jade Ore",
		"kind": "material",
		"value": 30,
		"icon": "ore",
		"tint": "#4fbf8f",
		"source": "Black Wind Monastery",
		"desc": "Raw jade stone for smithing. Not a cultivation crystal."
	},
	"bronze_ingot": {
		"name": "Bronze Ingot",
		"kind": "material",
		"value": 22,
		"icon": "ingot",
		"tint": "#c9833f",
		"desc": "A sturdy metal ingot used for weapons and gear."
	},
	"steel_ingot": {
		"name": "Steel Ingot",
		"kind": "material",
		"value": 50,
		"icon": "ingot",
		"tint": "#b8c6d0",
		"desc": "Folded steel bar."
	},
	"jade_ingot": {
		"name": "Jade Alloy",
		"kind": "material",
		"value": 120,
		"icon": "ingot",
		"tint": "#58d0a0",
		"desc": "Jade fused with steel; carries Qi."
	},
	"herb": {
		"name": "Dewleaf",
		"kind": "material",
		"value": 5,
		"icon": "herb",
		"source": "Jade River Town, River Outskirts",
		"desc": "Dew-soaked leaf used for healing pills."
	},
	"lotus": {
		"name": "Moon Lotus",
		"kind": "material",
		"value": 18,
		"icon": "lotus",
		"source": "Whispering Bamboo marsh",
		"desc": "Blooms by moonlight; key to Foundation Pills."
	},
	"ginseng": {
		"name": "Spirit Ginseng",
		"kind": "material",
		"value": 40,
		"icon": "ginseng",
		"source": "Cloudrest Court, Black Wind Monastery",
		"desc": "Centuries-old root full of vitality."
	},
	"carp": {
		"name": "River Carp",
		"kind": "material",
		"value": 5,
		"icon": "fish",
		"tint": "#7fb0d8",
		"source": "Riverbank fishing spots",
		"desc": "A plump river carp."
	},
	"eel": {
		"name": "Moon Eel",
		"kind": "material",
		"value": 16,
		"icon": "eel",
		"tint": "#9aa8e8",
		"source": "Lantern Haven, Whispering Bamboo pools",
		"desc": "Silver eel that glows faintly."
	},
	"koi": {
		"name": "Spirit Koi",
		"kind": "material",
		"value": 35,
		"icon": "fish",
		"tint": "#ff9a5a",
		"source": "Cloudrest Court spring",
		"desc": "A koi that has drunk spirit water."
	},
	"dust": {
		"name": "Spirit Dust",
		"kind": "material",
		"value": 8,
		"icon": "dust",
		"source": "Defeated foes",
		"desc": "Residual Qi scattered by defeated foes."
	},
	"hide": {
		"name": "Beast Hide",
		"kind": "material",
		"value": 14,
		"icon": "hide",
		"source": "Wolves of Whispering Bamboo",
		"desc": "Tough hide for grips and body tempering."
	},
	"core": {
		"name": "Beast Core",
		"kind": "material",
		"value": 60,
		"icon": "core",
		"source": "Spirit beasts, bosses",
		"desc": "Condensed beast Qi."
	},
	"spirit_shard": {
		"name": "Spirit Shard",
		"kind": "crystal",
		"essence": 10,
		"value": 20,
		"icon": "crystal",
		"tint": "#8fe8ff",
		"source": "Shrine crystal nodes",
		"desc": "Low-grade Qi crystal. Absorb for 10 Qi essence."
	},
	"vein_crystal": {
		"name": "Vein Crystal",
		"kind": "crystal",
		"essence": 30,
		"value": 60,
		"icon": "crystal",
		"tint": "#6f9bff",
		"source": "Whispering Bamboo high terrace",
		"desc": "Middle-grade Qi crystal. Absorb for 30 Qi essence."
	},
	"source_crystal": {
		"name": "Source Crystal",
		"kind": "crystal",
		"essence": 80,
		"value": 160,
		"icon": "crystal",
		"tint": "#d58cff",
		"source": "Black Wind Monastery",
		"desc": "Refined Qi crystal. Absorb for 80 Qi essence."
	},
	"mend_pill": {
		"name": "Mending Pill",
		"kind": "pill",
		"effect": {
			"hp": 50
		},
		"value": 25,
		"icon": "pill",
		"tint": "#d8453a",
		"desc": "Restores 50 HP."
	},
	"qi_pill": {
		"name": "Clear Qi Pill",
		"kind": "pill",
		"effect": {
			"qi": 40
		},
		"value": 25,
		"icon": "pill",
		"tint": "#3a78d8",
		"desc": "Restores 40 combat Qi."
	},
	"insight_pill": {
		"name": "Insight Pill",
		"kind": "pill",
		"effect": {
			"insight": 20
		},
		"value": 60,
		"icon": "pill",
		"tint": "#b58ae8",
		"desc": "Grants 20 insight."
	},
	"foundation_pill": {
		"name": "Foundation Pill",
		"kind": "pill",
		"effect": {},
		"value": 150,
		"icon": "pill",
		"tint": "#e8b03a",
		"desc": "Required for breakthroughs from Qi Awakening onward. Held, not eaten."
	},
	"seal_fragment": {
		"name": "Seal Fragment",
		"kind": "quest",
		"value": 0,
		"icon": "fragment",
		"desc": "A shard of the broken river seal. Quest item."
	}
}


const MASTERY_CAP = 200

const MASTERY_PER_HIT = 1

const MERIDIANS = [
	{
		"id": "lung",
		"name": "Lung Channel",
		"cost": 15,
		"bonus": {
			"hp": 12
		}
	},
	{
		"id": "heart",
		"name": "Heart Channel",
		"cost": 25,
		"bonus": {
			"qi": 8
		}
	},
	{
		"id": "spleen",
		"name": "Spleen Channel",
		"cost": 40,
		"bonus": {
			"atk": 2
		}
	},
	{
		"id": "liver",
		"name": "Liver Channel",
		"cost": 55,
		"bonus": {
			"hp": 18
		}
	},
	{
		"id": "kidney",
		"name": "Kidney Channel",
		"cost": 75,
		"bonus": {
			"qi": 12
		}
	},
	{
		"id": "governor",
		"name": "Governor Vessel",
		"cost": 100,
		"bonus": {
			"atk": 4,
			"def": 2
		}
	}
]

const NODE_TYPES = {
	"copper": {
		"name": "Copper Ore Seam",
		"prof": "mining",
		"tool": "mining",
		"lv": 1,
		"item": "copper",
		"yield": [
			1,
			2
		],
		"time": 1.6,
		"respawn": 40,
		"xp": 6,
		"sprite": "vein",
		"tint": "#c96b3c"
	},
	"iron": {
		"name": "Iron Ore Vein",
		"prof": "mining",
		"tool": "mining",
		"lv": 2,
		"item": "iron",
		"yield": [
			1,
			2
		],
		"time": 2,
		"respawn": 45,
		"xp": 9,
		"sprite": "vein",
		"tint": "#8793a0"
	},
	"jade": {
		"name": "Jade Vein",
		"prof": "mining",
		"tool": "mining",
		"lv": 4,
		"item": "jade_ore",
		"yield": [
			1,
			2
		],
		"time": 2.4,
		"respawn": 55,
		"xp": 14,
		"sprite": "vein",
		"tint": "#4fbf8f"
	},
	"shard": {
		"name": "Spirit Shard Node",
		"prof": "mining",
		"tool": "mining",
		"lv": 1,
		"item": "spirit_shard",
		"yield": [
			1,
			1
		],
		"time": 1.8,
		"respawn": 50,
		"xp": 8,
		"sprite": "crystal",
		"tint": "#8fe8ff"
	},
	"vein_crystal": {
		"name": "Vein Crystal Node",
		"prof": "mining",
		"tool": "mining",
		"lv": 3,
		"item": "vein_crystal",
		"yield": [
			1,
			1
		],
		"time": 2.2,
		"respawn": 70,
		"xp": 14,
		"sprite": "crystal",
		"tint": "#6f9bff"
	},
	"source_crystal": {
		"name": "Source Crystal Node",
		"prof": "mining",
		"tool": "mining",
		"lv": 5,
		"item": "source_crystal",
		"yield": [
			1,
			1
		],
		"time": 2.6,
		"respawn": 90,
		"xp": 22,
		"sprite": "crystal",
		"tint": "#d58cff"
	},
	"dewleaf": {
		"name": "Dewleaf Patch",
		"prof": "herbalism",
		"tool": "herbalism",
		"lv": 1,
		"item": "herb",
		"yield": [
			1,
			2
		],
		"time": 1.2,
		"respawn": 30,
		"xp": 5,
		"sprite": "herb"
	},
	"lotus": {
		"name": "Moon Lotus",
		"prof": "herbalism",
		"tool": "herbalism",
		"lv": 2,
		"item": "lotus",
		"yield": [
			1,
			1
		],
		"time": 1.6,
		"respawn": 40,
		"xp": 9,
		"sprite": "lotus"
	},
	"ginseng": {
		"name": "Spirit Ginseng",
		"prof": "herbalism",
		"tool": "herbalism",
		"lv": 3,
		"item": "ginseng",
		"yield": [
			1,
			1
		],
		"time": 2,
		"respawn": 60,
		"xp": 14,
		"sprite": "ginseng"
	},
	"carp_pool": {
		"name": "Riverbank Fishing",
		"prof": "fishing",
		"tool": "fishing",
		"lv": 1,
		"item": "carp",
		"yield": [
			1,
			1
		],
		"time": 2.4,
		"respawn": 12,
		"xp": 6,
		"sprite": "fish"
	},
	"eel_pool": {
		"name": "Moon Eel Pool",
		"prof": "fishing",
		"tool": "fishing",
		"lv": 2,
		"item": "eel",
		"yield": [
			1,
			1
		],
		"time": 2.8,
		"respawn": 15,
		"xp": 9,
		"sprite": "fish"
	},
	"koi_spring": {
		"name": "Spirit Koi Spring",
		"prof": "fishing",
		"tool": "fishing",
		"lv": 3,
		"item": "koi",
		"yield": [
			1,
			1
		],
		"time": 3.2,
		"respawn": 20,
		"xp": 14,
		"sprite": "fish"
	}
}

const PROFESSIONS = {
	"mining": {
		"name": "Mining",
		"verb": "Mine"
	},
	"herbalism": {
		"name": "Herbalism",
		"verb": "Harvest"
	},
	"fishing": {
		"name": "Fishing",
		"verb": "Fish"
	},
	"smithing": {
		"name": "Smithing",
		"verb": "Forge"
	},
	"alchemy": {
		"name": "Alchemy",
		"verb": "Brew"
	}
}

const PROF_XP = [
	0,
	0,
	20,
	55,
	110,
	190,
	300,
	450,
	650,
	900,
	1200
]

const REALMS = [
	{
		"id": "mortal",
		"name": "Mortal",
		"req": null,
		"trial": false
	},
	{
		"id": "qi_awakening",
		"name": "Qi Awakening",
		"req": {
			"level": 2,
			"insight": 30,
			"pills": 0
		},
		"trial": false
	},
	{
		"id": "foundation",
		"name": "Foundation",
		"req": {
			"level": 4,
			"insight": 100,
			"pills": 1
		},
		"trial": true
	},
	{
		"id": "golden_core",
		"name": "Golden Core",
		"req": {
			"level": 7,
			"insight": 250,
			"pills": 2
		},
		"trial": true
	},
	{
		"id": "nascent_spirit",
		"name": "Nascent Spirit",
		"req": {
			"level": 10,
			"insight": 500,
			"pills": 3
		},
		"trial": true
	}
]

const REALM_BONUS = {
	"hp": 20,
	"qi": 10,
	"atk": 4
}

const RECIPES = [
	{
		"id": "smelt_bronze",
		"station": "forge",
		"tab": "smithing",
		"name": "Smelt Bronze",
		"desc": "Refine raw copper into solid bronze ingots.",
		"in": {
			"copper": 3
		},
		"out": {
			"bronze_ingot": 1
		},
		"skill": "smithing",
		"lv": 1,
		"xp": 10
	},
	{
		"id": "smelt_steel",
		"station": "forge",
		"tab": "smithing",
		"name": "Smelt Steel",
		"desc": "Fold iron with bronze flux into steel.",
		"in": {
			"iron": 3,
			"bronze_ingot": 1
		},
		"out": {
			"steel_ingot": 1
		},
		"skill": "smithing",
		"lv": 2,
		"xp": 18
	},
	{
		"id": "jade_alloy",
		"station": "forge",
		"tab": "smithing",
		"name": "Jade Alloy",
		"desc": "Fuse jade stone into steel with spirit dust.",
		"in": {
			"jade_ore": 2,
			"steel_ingot": 1,
			"dust": 2
		},
		"out": {
			"jade_ingot": 1
		},
		"skill": "smithing",
		"lv": 4,
		"xp": 30
	},
	{
		"id": "forge_bronze_sword",
		"station": "forge",
		"tab": "smithing",
		"name": "Bronze Jian",
		"desc": "Forge a balanced bronze sword.",
		"in": {
			"bronze_ingot": 2
		},
		"out": {
			"bronze_sword": 1
		},
		"skill": "smithing",
		"lv": 1,
		"xp": 15
	},
	{
		"id": "forge_bronze_spear",
		"station": "forge",
		"tab": "smithing",
		"name": "Bronze Spear",
		"desc": "Forge a bronze spear head.",
		"in": {
			"bronze_ingot": 2
		},
		"out": {
			"bronze_spear": 1
		},
		"skill": "smithing",
		"lv": 1,
		"xp": 15
	},
	{
		"id": "forge_steel_sword",
		"station": "forge",
		"tab": "smithing",
		"name": "Steel Jian",
		"desc": "Forge a steel sword. Equip at Sword Mastery 60.",
		"in": {
			"steel_ingot": 3,
			"hide": 1
		},
		"out": {
			"steel_sword": 1
		},
		"skill": "smithing",
		"lv": 3,
		"xp": 30
	},
	{
		"id": "forge_steel_spear",
		"station": "forge",
		"tab": "smithing",
		"name": "Steel Spear",
		"desc": "Forge a steel spear. Equip at Spear Mastery 60.",
		"in": {
			"steel_ingot": 3,
			"hide": 1
		},
		"out": {
			"steel_spear": 1
		},
		"skill": "smithing",
		"lv": 3,
		"xp": 30
	},
	{
		"id": "forge_jade_sword",
		"station": "forge",
		"tab": "smithing",
		"name": "Jadeflow Jian",
		"desc": "Equip at Sword Mastery 120 and Foundation realm.",
		"in": {
			"jade_ingot": 3,
			"core": 1
		},
		"out": {
			"jade_sword": 1
		},
		"skill": "smithing",
		"lv": 5,
		"xp": 60
	},
	{
		"id": "forge_jade_spear",
		"station": "forge",
		"tab": "smithing",
		"name": "Jadeflow Spear",
		"desc": "Equip at Spear Mastery 120 and Foundation realm.",
		"in": {
			"jade_ingot": 3,
			"core": 1
		},
		"out": {
			"jade_spear": 1
		},
		"skill": "smithing",
		"lv": 5,
		"xp": 60
	},
	{
		"id": "forge_steel_pick",
		"station": "forge",
		"tab": "smithing",
		"name": "Steel Pick",
		"desc": "A faster mining pick.",
		"in": {
			"steel_ingot": 2
		},
		"out": {
			"steel_pick": 1
		},
		"skill": "smithing",
		"lv": 2,
		"xp": 20
	},
	{
		"id": "brew_mend",
		"station": "furnace",
		"tab": "pills",
		"name": "Mending Pill",
		"desc": "Dewleaf pressed into a healing pill.",
		"in": {
			"herb": 2
		},
		"out": {
			"mend_pill": 1
		},
		"skill": "alchemy",
		"lv": 1,
		"xp": 8
	},
	{
		"id": "brew_qi",
		"station": "furnace",
		"tab": "pills",
		"name": "Clear Qi Pill",
		"desc": "Dewleaf and carp broth, condensed.",
		"in": {
			"herb": 1,
			"carp": 1
		},
		"out": {
			"qi_pill": 1
		},
		"skill": "alchemy",
		"lv": 1,
		"xp": 8
	},
	{
		"id": "brew_insight",
		"station": "furnace",
		"tab": "pills",
		"name": "Insight Pill",
		"desc": "Lotus, eel and spirit dust clear the mind.",
		"in": {
			"lotus": 1,
			"eel": 1,
			"dust": 1
		},
		"out": {
			"insight_pill": 1
		},
		"skill": "alchemy",
		"lv": 2,
		"xp": 14
	},
	{
		"id": "brew_foundation",
		"station": "furnace",
		"tab": "pills",
		"name": "Foundation Pill",
		"desc": "Stabilises the dantian for a breakthrough.",
		"in": {
			"lotus": 2,
			"eel": 1,
			"spirit_shard": 1
		},
		"out": {
			"foundation_pill": 1
		},
		"skill": "alchemy",
		"lv": 2,
		"xp": 25
	},
	{
		"id": "brew_foundation_rich",
		"station": "furnace",
		"tab": "pills",
		"name": "Foundation Pill (Ginseng)",
		"desc": "A richer route using ginseng and koi.",
		"in": {
			"ginseng": 1,
			"koi": 1,
			"vein_crystal": 1
		},
		"out": {
			"foundation_pill": 1
		},
		"skill": "alchemy",
		"lv": 3,
		"xp": 30
	}
]

const RESEARCH = [
	{
		"id": "gentle_fire",
		"name": "Gentle Fire",
		"desc": "Mending Pills heal 30% more.",
		"cost": {
			"dust": 4
		},
		"coins": 60
	},
	{
		"id": "clear_spring",
		"name": "Clear Spring",
		"desc": "Clear Qi Pills restore 30% more.",
		"cost": {
			"dust": 4,
			"carp": 2
		},
		"coins": 60
	},
	{
		"id": "still_mind",
		"name": "Still Mind",
		"desc": "Meditation cycles grant +1 Qi essence.",
		"cost": {
			"dust": 8,
			"lotus": 2
		},
		"coins": 150
	}
]

const SAVE_VERSION = 4

const SHOPS = {
	"jr_town": [
		"mend_pill",
		"qi_pill",
		"herb",
		"copper",
		"carp",
		"straw_hat",
		"gourd",
		"training_sword",
		"training_spear"
	],
	"lantern": [
		"mend_pill",
		"qi_pill",
		"lotus",
		"iron",
		"eel",
		"spirit_shard",
		"jade_crown"
	],
	"cloudrest": [
		"mend_pill",
		"qi_pill",
		"insight_pill",
		"ginseng",
		"jade_ore",
		"vein_crystal",
		"hide"
	]
}

const SOUL_MILESTONES = [
	{
		"id": "sense",
		"at": 5,
		"name": "Soul Sense",
		"desc": "Undiscovered resource nodes appear on the minimap."
	},
	{
		"id": "foresight",
		"at": 12,
		"name": "Foresight",
		"desc": "Enemy strikes telegraph earlier with a warning glyph."
	},
	{
		"id": "clarity",
		"at": 20,
		"name": "Clarity",
		"desc": "Meditation yields +25% insight."
	}
]

const WEAPON_TREES = {
	"sword": {
		"name": "Sword Techniques",
		"nodes": [
			[
				"crescent"
			],
			[
				"swift_draw"
			],
			[
				"parry_counter",
				"heaven_splitter",
				"flow_combo"
			]
		]
	},
	"spear": {
		"name": "Spear Techniques",
		"nodes": [
			[
				"spear_thrust"
			],
			[
				"long_thrust"
			],
			[
				"guarding_spear",
				"dragon_art",
				"flowing_spear"
			]
		]
	}
}

const AREAS = {
	"jr_town": {
		"name": "Jade River Town",
		"type": "town",
		"region": 1,
		"theme": "town",
		"width": 1500,
		"lv": "Safe",
		"mapPos": [
			0.085,
			0.52
		],
		"neighbors": [
			"outskirts"
		],
		"mentor": "wen",
		"shop": "jr_town",
		"surfaces": [
			{
				"id": "tea_stair",
				"kind": "stair",
				"x0": 500,
				"x1": 560,
				"d0": 0,
				"d1": 26,
				"h0": 0,
				"h1": 40,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "tea_roof",
				"kind": "terrace",
				"x0": 560,
				"x1": 760,
				"d0": 0,
				"d1": 26,
				"h0": 40,
				"h1": 40,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "roof"
			}
		],
		"stations": [
			{
				"type": "shrine",
				"x": 110,
				"depth": 18
			},
			{
				"type": "shop",
				"x": 400,
				"depth": 10
			},
			{
				"type": "forge",
				"x": 840,
				"depth": 10
			},
			{
				"type": "furnace",
				"x": 970,
				"depth": 10
			},
			{
				"type": "research",
				"x": 1070,
				"depth": 10
			},
			{
				"type": "chest",
				"x": 1160,
				"depth": 14
			},
			{
				"type": "board",
				"x": 1250,
				"depth": 8
			}
		],
		"npcs": [
			{
				"id": "wen",
				"x": 270,
				"depth": 34
			}
		],
		"nodes": [
			{
				"id": "jt_dew1",
				"type": "dewleaf",
				"x": 1330,
				"depth": 44
			},
			{
				"id": "jt_dew2",
				"type": "dewleaf",
				"x": 1375,
				"depth": 64
			},
			{
				"id": "jt_dew_roof",
				"type": "dewleaf",
				"x": 700,
				"depth": 12,
				"surface": "tea_roof"
			},
			{
				"id": "jt_fish",
				"type": "carp_pool",
				"x": 1430,
				"depth": 2
			}
		],
		"enemies": [],
		"portals": [
			{
				"x": 1480,
				"to": "outskirts",
				"spawn": 70,
				"label": "River Outskirts"
			}
		],
		"resources": [
			"herb",
			"carp"
		],
		"monsters": []
	},
	"outskirts": {
		"name": "River Outskirts",
		"type": "field",
		"region": 1,
		"theme": "outskirts",
		"width": 2700,
		"lv": "Lv 1–3",
		"mapPos": [
			0.28,
			0.6
		],
		"neighbors": [
			"jr_town",
			"lantern"
		],
		"chapter": 1,
		"surfaces": [
			{
				"id": "br_stairL",
				"kind": "stair",
				"x0": 640,
				"x1": 720,
				"d0": 6,
				"d1": 30,
				"h0": 0,
				"h1": 64,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "bridge",
				"kind": "bridge",
				"x0": 720,
				"x1": 1120,
				"d0": 6,
				"d1": 30,
				"h0": 64,
				"h1": 64,
				"solid": false,
				"oneWay": true,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "bridge"
			},
			{
				"id": "br_stairR",
				"kind": "stair",
				"x0": 1120,
				"x1": 1200,
				"d0": 6,
				"d1": 30,
				"h0": 64,
				"h1": 0,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "river_terrace",
				"kind": "terrace",
				"x0": 1450,
				"x1": 1640,
				"d0": 0,
				"d1": 30,
				"h0": 38,
				"h1": 38,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "watch_roof",
				"kind": "terrace",
				"x0": 1520,
				"x1": 1600,
				"d0": 0,
				"d1": 14,
				"h0": 76,
				"h1": 76,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "roof"
			}
		],
		"stations": [
			{
				"type": "rest",
				"x": 1290,
				"depth": 14
			}
		],
		"npcs": [],
		"nodes": [
			{
				"id": "ro_dew1",
				"type": "dewleaf",
				"x": 230,
				"depth": 50
			},
			{
				"id": "ro_dew2",
				"type": "dewleaf",
				"x": 330,
				"depth": 20
			},
			{
				"id": "ro_dew3",
				"type": "dewleaf",
				"x": 480,
				"depth": 64
			},
			{
				"id": "ro_cu1",
				"type": "copper",
				"x": 560,
				"depth": 8
			},
			{
				"id": "ro_cu_bridge",
				"type": "copper",
				"x": 900,
				"depth": 10,
				"surface": "bridge"
			},
			{
				"id": "ro_cu_terrace",
				"type": "copper",
				"x": 1570,
				"depth": 8,
				"surface": "river_terrace"
			},
			{
				"id": "ro_dew_roof",
				"type": "dewleaf",
				"x": 1560,
				"depth": 6,
				"surface": "watch_roof"
			},
			{
				"id": "ro_shard",
				"type": "shard",
				"x": 1330,
				"depth": 6
			},
			{
				"id": "ro_fish",
				"type": "carp_pool",
				"x": 1880,
				"depth": 2
			}
		],
		"enemies": [
			{
				"type": "raider",
				"x": 430,
				"depth": 40
			},
			{
				"type": "raider",
				"x": 860,
				"depth": 18,
				"surface": "bridge"
			},
			{
				"type": "raider",
				"x": 1000,
				"depth": 60
			},
			{
				"type": "archer",
				"x": 1120,
				"depth": 70
			},
			{
				"type": "raider",
				"x": 1560,
				"depth": 16,
				"surface": "river_terrace"
			},
			{
				"type": "raider",
				"x": 1760,
				"depth": 50
			},
			{
				"type": "raider",
				"x": 1980,
				"depth": 30
			},
			{
				"type": "archer",
				"x": 2080,
				"depth": 12
			}
		],
		"boss": {
			"type": "captain",
			"id": "captain",
			"x0": 2250,
			"x1": 2640,
			"x": 2520,
			"depth": 40
		},
		"portals": [
			{
				"x": 20,
				"to": "jr_town",
				"spawn": 1440,
				"label": "Jade River Town"
			},
			{
				"x": 2680,
				"to": "lantern",
				"spawn": 70,
				"label": "Lantern Haven",
				"lock": "ch1_done"
			}
		],
		"resources": [
			"herb",
			"copper",
			"spirit_shard",
			"carp"
		],
		"monsters": [
			"River Raider",
			"Raider Archer",
			"Black River Captain"
		]
	},
	"lantern": {
		"name": "Lantern Haven",
		"type": "town",
		"region": 2,
		"theme": "lantern",
		"width": 1500,
		"lv": "Safe",
		"mapPos": [
			0.447,
			0.47
		],
		"neighbors": [
			"outskirts",
			"bamboo"
		],
		"mentor": "suyin",
		"shop": "lantern",
		"unlock": "ch1_done",
		"surfaces": [
			{
				"id": "ln_stair",
				"kind": "stair",
				"x0": 880,
				"x1": 940,
				"d0": 0,
				"d1": 24,
				"h0": 0,
				"h1": 42,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "ln_roof",
				"kind": "terrace",
				"x0": 940,
				"x1": 1120,
				"d0": 0,
				"d1": 24,
				"h0": 42,
				"h1": 42,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "roof"
			}
		],
		"stations": [
			{
				"type": "shrine",
				"x": 120,
				"depth": 18
			},
			{
				"type": "shop",
				"x": 430,
				"depth": 10
			},
			{
				"type": "forge",
				"x": 560,
				"depth": 10
			},
			{
				"type": "furnace",
				"x": 690,
				"depth": 10
			},
			{
				"type": "research",
				"x": 790,
				"depth": 10
			},
			{
				"type": "chest",
				"x": 1200,
				"depth": 14
			},
			{
				"type": "board",
				"x": 1290,
				"depth": 8
			}
		],
		"npcs": [
			{
				"id": "suyin",
				"x": 290,
				"depth": 34
			}
		],
		"nodes": [
			{
				"id": "ln_eel",
				"type": "eel_pool",
				"x": 1420,
				"depth": 2
			},
			{
				"id": "ln_lotus_roof",
				"type": "lotus",
				"x": 1060,
				"depth": 10,
				"surface": "ln_roof"
			}
		],
		"enemies": [],
		"portals": [
			{
				"x": 20,
				"to": "outskirts",
				"spawn": 2620,
				"label": "River Outskirts"
			},
			{
				"x": 1480,
				"to": "bamboo",
				"spawn": 70,
				"label": "Whispering Bamboo"
			}
		],
		"resources": [
			"eel",
			"lotus"
		],
		"monsters": []
	},
	"bamboo": {
		"name": "Whispering Bamboo",
		"type": "field",
		"region": 2,
		"theme": "bamboo",
		"width": 2900,
		"lv": "Lv 4–7",
		"mapPos": [
			0.6,
			0.51
		],
		"neighbors": [
			"lantern",
			"cloudrest"
		],
		"chapter": 2,
		"unlock": "ch1_done",
		"surfaces": [
			{
				"id": "grove_terrace",
				"kind": "terrace",
				"x0": 700,
				"x1": 870,
				"d0": 0,
				"d1": 28,
				"h0": 36,
				"h1": 36,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "grove_roof",
				"kind": "terrace",
				"x0": 760,
				"x1": 840,
				"d0": 0,
				"d1": 14,
				"h0": 74,
				"h1": 74,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "roof"
			},
			{
				"id": "bb_stairL",
				"kind": "stair",
				"x0": 1220,
				"x1": 1300,
				"d0": 4,
				"d1": 28,
				"h0": 0,
				"h1": 60,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "reed_bridge",
				"kind": "bridge",
				"x0": 1300,
				"x1": 1700,
				"d0": 4,
				"d1": 28,
				"h0": 60,
				"h1": 60,
				"solid": false,
				"oneWay": true,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "bridge"
			},
			{
				"id": "bb_stairR",
				"kind": "stair",
				"x0": 1700,
				"x1": 1780,
				"d0": 4,
				"d1": 28,
				"h0": 60,
				"h1": 0,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "seal_step",
				"kind": "terrace",
				"x0": 2380,
				"x1": 2460,
				"d0": 0,
				"d1": 24,
				"h0": 34,
				"h1": 34,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "stone"
			}
		],
		"stations": [
			{
				"type": "rest",
				"x": 1140,
				"depth": 14
			},
			{
				"type": "seal",
				"x": 2200,
				"depth": 12
			}
		],
		"npcs": [],
		"nodes": [
			{
				"id": "bb_lotus1",
				"type": "lotus",
				"x": 400,
				"depth": 60
			},
			{
				"id": "bb_lotus2",
				"type": "lotus",
				"x": 520,
				"depth": 40
			},
			{
				"id": "bb_lotus3",
				"type": "lotus",
				"x": 1060,
				"depth": 66
			},
			{
				"id": "bb_lotus4",
				"type": "lotus",
				"x": 1900,
				"depth": 55
			},
			{
				"id": "bb_iron1",
				"type": "iron",
				"x": 980,
				"depth": 8
			},
			{
				"id": "bb_iron_bridge",
				"type": "iron",
				"x": 1500,
				"depth": 10,
				"surface": "reed_bridge"
			},
			{
				"id": "bb_iron2",
				"type": "iron",
				"x": 2100,
				"depth": 10
			},
			{
				"id": "bb_vein",
				"type": "vein_crystal",
				"x": 800,
				"depth": 6,
				"surface": "grove_roof"
			},
			{
				"id": "bb_shard",
				"type": "shard",
				"x": 1180,
				"depth": 6
			},
			{
				"id": "bb_eel",
				"type": "eel_pool",
				"x": 1990,
				"depth": 2
			},
			{
				"id": "bb_dew",
				"type": "dewleaf",
				"x": 250,
				"depth": 30
			}
		],
		"runes": [
			{
				"id": "r_water",
				"glyph": "water",
				"x": 2270,
				"depth": 22
			},
			{
				"id": "r_wood",
				"glyph": "wood",
				"x": 2330,
				"depth": 62
			},
			{
				"id": "r_fire",
				"glyph": "fire",
				"x": 2420,
				"depth": 10,
				"surface": "seal_step"
			},
			{
				"id": "r_earth",
				"glyph": "earth",
				"x": 2500,
				"depth": 44
			}
		],
		"runeOrder": [
			"r_water",
			"r_wood",
			"r_fire",
			"r_earth"
		],
		"enemies": [
			{
				"type": "wolf",
				"x": 360,
				"depth": 40
			},
			{
				"type": "wolf",
				"x": 620,
				"depth": 60
			},
			{
				"type": "archer",
				"x": 790,
				"depth": 14,
				"surface": "grove_terrace"
			},
			{
				"type": "raider",
				"x": 930,
				"depth": 50
			},
			{
				"type": "wolf",
				"x": 1420,
				"depth": 60
			},
			{
				"type": "raider",
				"x": 1520,
				"depth": 16,
				"surface": "reed_bridge"
			},
			{
				"type": "heavy",
				"x": 1620,
				"depth": 50
			},
			{
				"type": "wolf",
				"x": 1880,
				"depth": 30
			},
			{
				"type": "heavy",
				"x": 2060,
				"depth": 40
			},
			{
				"type": "archer",
				"x": 2360,
				"depth": 70
			}
		],
		"boss": {
			"type": "sentinel",
			"id": "sentinel",
			"x0": 2580,
			"x1": 2860,
			"x": 2770,
			"depth": 40
		},
		"portals": [
			{
				"x": 20,
				"to": "lantern",
				"spawn": 1440,
				"label": "Lantern Haven"
			},
			{
				"x": 2880,
				"to": "cloudrest",
				"spawn": 70,
				"label": "Cloudrest Court",
				"lock": "ch2_done"
			}
		],
		"resources": [
			"lotus",
			"iron",
			"vein_crystal",
			"spirit_shard",
			"eel",
			"hide"
		],
		"monsters": [
			"Bamboo Wolf",
			"Iron Brute",
			"Raider Archer",
			"Reed Sentinel"
		]
	},
	"cloudrest": {
		"name": "Cloudrest Court",
		"type": "town",
		"region": 3,
		"theme": "cloudrest",
		"width": 1500,
		"lv": "Safe",
		"mapPos": [
			0.72,
			0.36
		],
		"neighbors": [
			"bamboo",
			"monastery"
		],
		"mentor": "tao",
		"shop": "cloudrest",
		"unlock": "ch2_done",
		"surfaces": [
			{
				"id": "cc_stair",
				"kind": "stair",
				"x0": 560,
				"x1": 620,
				"d0": 0,
				"d1": 24,
				"h0": 0,
				"h1": 40,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "cc_roof",
				"kind": "terrace",
				"x0": 620,
				"x1": 800,
				"d0": 0,
				"d1": 24,
				"h0": 40,
				"h1": 40,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "roof"
			}
		],
		"stations": [
			{
				"type": "shrine",
				"x": 120,
				"depth": 18
			},
			{
				"type": "shop",
				"x": 420,
				"depth": 10
			},
			{
				"type": "forge",
				"x": 880,
				"depth": 10
			},
			{
				"type": "furnace",
				"x": 1000,
				"depth": 10
			},
			{
				"type": "research",
				"x": 1100,
				"depth": 10
			},
			{
				"type": "chest",
				"x": 1180,
				"depth": 14
			},
			{
				"type": "board",
				"x": 1260,
				"depth": 8
			}
		],
		"npcs": [
			{
				"id": "tao",
				"x": 290,
				"depth": 34
			}
		],
		"nodes": [
			{
				"id": "cc_gin1",
				"type": "ginseng",
				"x": 1330,
				"depth": 44
			},
			{
				"id": "cc_gin_roof",
				"type": "ginseng",
				"x": 740,
				"depth": 10,
				"surface": "cc_roof"
			},
			{
				"id": "cc_koi",
				"type": "koi_spring",
				"x": 1430,
				"depth": 2
			}
		],
		"enemies": [],
		"portals": [
			{
				"x": 20,
				"to": "bamboo",
				"spawn": 2840,
				"label": "Whispering Bamboo"
			},
			{
				"x": 1480,
				"to": "monastery",
				"spawn": 70,
				"label": "Black Wind Monastery"
			}
		],
		"resources": [
			"ginseng",
			"koi"
		],
		"monsters": []
	},
	"monastery": {
		"name": "Black Wind Monastery",
		"type": "field",
		"region": 3,
		"theme": "monastery",
		"width": 3100,
		"lv": "Lv 7–10",
		"mapPos": [
			0.83,
			0.19
		],
		"neighbors": [
			"cloudrest"
		],
		"chapter": 3,
		"unlock": "ch2_done",
		"surfaces": [
			{
				"id": "bw_stair",
				"kind": "stair",
				"x0": 600,
				"x1": 700,
				"d0": 0,
				"d1": 30,
				"h0": 0,
				"h1": 50,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "temple_terrace",
				"kind": "terrace",
				"x0": 700,
				"x1": 1000,
				"d0": 0,
				"d1": 30,
				"h0": 50,
				"h1": 50,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "temple_roof",
				"kind": "terrace",
				"x0": 820,
				"x1": 900,
				"d0": 0,
				"d1": 14,
				"h0": 90,
				"h1": 90,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "roof"
			},
			{
				"id": "bw_stairL",
				"kind": "stair",
				"x0": 1420,
				"x1": 1500,
				"d0": 4,
				"d1": 28,
				"h0": 0,
				"h1": 66,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			},
			{
				"id": "wind_bridge",
				"kind": "bridge",
				"x0": 1500,
				"x1": 1900,
				"d0": 4,
				"d1": 28,
				"h0": 66,
				"h1": 66,
				"solid": false,
				"oneWay": true,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "bridge"
			},
			{
				"id": "bw_stairR",
				"kind": "stair",
				"x0": 1900,
				"x1": 1980,
				"d0": 4,
				"d1": 28,
				"h0": 66,
				"h1": 0,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": true,
					"left": false,
					"right": false
				},
				"style": "stone"
			}
		],
		"stations": [
			{
				"type": "rest",
				"x": 1230,
				"depth": 14
			}
		],
		"npcs": [],
		"nodes": [
			{
				"id": "bw_source",
				"type": "source_crystal",
				"x": 860,
				"depth": 6,
				"surface": "temple_roof"
			},
			{
				"id": "bw_jade1",
				"type": "jade",
				"x": 1340,
				"depth": 10
			},
			{
				"id": "bw_jade_bridge",
				"type": "jade",
				"x": 1700,
				"depth": 10,
				"surface": "wind_bridge"
			},
			{
				"id": "bw_jade2",
				"type": "jade",
				"x": 2120,
				"depth": 10
			},
			{
				"id": "bw_gin1",
				"type": "ginseng",
				"x": 1140,
				"depth": 60
			},
			{
				"id": "bw_gin2",
				"type": "ginseng",
				"x": 2020,
				"depth": 64
			},
			{
				"id": "bw_vein",
				"type": "vein_crystal",
				"x": 1270,
				"depth": 6
			},
			{
				"id": "bw_iron",
				"type": "iron",
				"x": 380,
				"depth": 10
			}
		],
		"enemies": [
			{
				"type": "spirit_wolf",
				"x": 420,
				"depth": 50
			},
			{
				"type": "acolyte",
				"x": 860,
				"depth": 16,
				"surface": "temple_terrace"
			},
			{
				"type": "heavy",
				"x": 1060,
				"depth": 60
			},
			{
				"type": "acolyte",
				"x": 1480,
				"depth": 66
			},
			{
				"type": "heavy",
				"x": 1640,
				"depth": 50
			},
			{
				"type": "acolyte",
				"x": 1760,
				"depth": 16,
				"surface": "wind_bridge"
			},
			{
				"type": "spirit_wolf",
				"x": 2250,
				"depth": 40
			},
			{
				"type": "heavy",
				"x": 2380,
				"depth": 20
			},
			{
				"type": "acolyte",
				"x": 2470,
				"depth": 64
			}
		],
		"boss": {
			"type": "qiu",
			"id": "qiu",
			"x0": 2650,
			"x1": 3060,
			"x": 2900,
			"depth": 40
		},
		"portals": [
			{
				"x": 20,
				"to": "cloudrest",
				"spawn": 1440,
				"label": "Cloudrest Court"
			}
		],
		"resources": [
			"jade_ore",
			"ginseng",
			"source_crystal",
			"vein_crystal",
			"core"
		],
		"monsters": [
			"Black Wind Wolf",
			"Black Wind Acolyte",
			"Iron Brute",
			"Master Qiu"
		]
	},
	"trial": {
		"name": "Inner Sea Trial",
		"type": "trial",
		"region": 0,
		"theme": "trial",
		"width": 640,
		"lv": "Trial",
		"surfaces": [
			{
				"id": "trial_step",
				"kind": "terrace",
				"x0": 260,
				"x1": 380,
				"d0": 0,
				"d1": 24,
				"h0": 34,
				"h1": 34,
				"solid": true,
				"oneWay": false,
				"rails": {
					"back": true,
					"front": false,
					"left": false,
					"right": false
				},
				"style": "jade"
			}
		],
		"stations": [],
		"npcs": [],
		"nodes": [],
		"enemies": [],
		"portals": []
	}
}

const GROUND_DEPTH = 78

const MAP_AREAS = [
	"jr_town",
	"outskirts",
	"lantern",
	"bamboo",
	"cloudrest",
	"monastery"
]

const SANCTUARY_OF = {
	"1": "jr_town",
	"2": "lantern",
	"3": "cloudrest"
}

const CHAPTERS = [
	{
		"id": "ch1",
		"num": "I",
		"name": "The Price of Breath",
		"mentor": "wen",
		"region": 1,
		"intro": [
			"Elder Wen: So you are the new disciple. The river seal broke three nights ago, and raiders pour through the Outskirts.",
			"Elder Wen: Before you can fight, you must breathe. Take this pick, this kit and this rod — the land feeds those who learn it.",
			"Elder Wen: Gather Dewleaf and Copper Ore in River Outskirts. Mind the bridge — the copper seam up there is worth the climb."
		],
		"grant": {
			"items": {
				"pick": 1,
				"kit": 1,
				"rod": 1,
				"mend_pill": 2
			},
			"coins": 30
		},
		"steps": [
			{
				"type": "talk",
				"npc": "wen",
				"text": "Speak with Elder Wen",
				"short": "Speak with Elder Wen"
			},
			{
				"type": "have",
				"items": {
					"herb": 3,
					"copper": 2
				},
				"text": "Gather 3 Dewleaf and 2 Copper Ore in River Outskirts",
				"short": "Find your footing"
			},
			{
				"type": "kill",
				"enemy": "raider",
				"count": 5,
				"text": "Defeat 5 River Raiders",
				"short": "Raiders",
				"chip": "Raiders"
			},
			{
				"type": "craft",
				"recipe": "brew_mend",
				"count": 1,
				"text": "Brew a Mending Pill at the Alchemy Furnace in town",
				"short": "Brew a pill"
			},
			{
				"type": "realm",
				"idx": 1,
				"text": "Meditate at a safe shrine and break through to Qi Awakening",
				"short": "Awaken your Qi"
			},
			{
				"type": "boss",
				"id": "captain",
				"text": "Defeat the Black River Captain at the crossing",
				"short": "The crossing"
			},
			{
				"type": "talk",
				"npc": "wen",
				"text": "Return to Elder Wen with the seal fragment",
				"short": "Return to the sage"
			}
		],
		"stepLines": {
			"2": "Elder Wen: Good hands. Now the raiders — five of them prowl the Outskirts. Strike, step aside, strike again.",
			"3": "Elder Wen: You are bleeding. Brew a Mending Pill at the furnace: two Dewleaf, one pill. Crafting is preparation.",
			"4": "Elder Wen: Now sit at the shrine and meditate. Gather insight until your Qi awakens. Level 2 and 30 insight will do.",
			"5": "Elder Wen: Your Qi flows. The Black River Captain holds the crossing east of the Outskirts. Bring back what he carries.",
			"6": "Elder Wen: You carry a seal fragment! Come — tell me everything."
		},
		"outro": [
			"Elder Wen: A fragment of the Broken Seal… the Captain was only a hired blade. Someone wants the river’s flow.",
			"Elder Wen: Archivist Suyin in Lantern Haven studies the old seals. The road east is open to you now."
		],
		"reward": {
			"items": {
				"seal_fragment": 1,
				"insight_pill": 1
			},
			"coins": 80,
			"xp": 80,
			"flag": "ch1_done"
		}
	},
	{
		"id": "ch2",
		"num": "II",
		"name": "The Hollow Grove",
		"mentor": "suyin",
		"region": 2,
		"intro": [
			"Archivist Suyin: Wen’s disciple? Then you have seen the fragment. The second anchor lies in Whispering Bamboo.",
			"Archivist Suyin: The grove seal is failing. Bring Iron Ore and Moon Lotus — iron to bind the runes, lotus for the Foundation Pill you will need."
		],
		"grant": {
			"items": {
				"spirit_shard": 1
			},
			"coins": 20
		},
		"steps": [
			{
				"type": "talk",
				"npc": "suyin",
				"text": "Speak with Archivist Suyin",
				"short": "Speak with Suyin"
			},
			{
				"type": "have",
				"items": {
					"iron": 3,
					"lotus": 2
				},
				"text": "Gather 3 Iron Ore and 2 Moon Lotus in Whispering Bamboo",
				"short": "Iron and lotus"
			},
			{
				"type": "flag",
				"flag": "seal_repaired",
				"text": "Repair the grove seal: set 2 Spirit Shards in the altar, then touch the runes in the order shown",
				"short": "Repair the seal"
			},
			{
				"type": "realm",
				"idx": 2,
				"text": "Brew a Foundation Pill and pass the Foundation breakthrough trial",
				"short": "Build a Foundation"
			},
			{
				"type": "boss",
				"id": "sentinel",
				"text": "Defeat the Reed Sentinel deep in the grove",
				"short": "The Reed Sentinel"
			},
			{
				"type": "talk",
				"npc": "suyin",
				"text": "Return to Archivist Suyin",
				"short": "Return to Suyin"
			}
		],
		"stepLines": {
			"2": "Archivist Suyin: The seal altar stands east in the grove. It drinks two Spirit Shards. Then follow the order carved on its tablet: water, wood, fire, earth.",
			"3": "Archivist Suyin: The seal holds. Your circulation must hold too — brew a Foundation Pill (lotus, eel, shard) and face the Foundation trial at a shrine.",
			"4": "Archivist Suyin: Foundation! Now the Sentinel — it guards the second fragment. Watch its shockwaves; they travel along the floor, not the roofs.",
			"5": "Archivist Suyin: Return when it falls."
		},
		"outro": [
			"Archivist Suyin: Two fragments. The pattern is clear — the seal was not broken, it was opened. Master Qiu of Black Wind.",
			"Archivist Suyin: Keeper Tao at Cloudrest Court owes Qiu an old debt. Go to him."
		],
		"reward": {
			"items": {
				"seal_fragment": 1,
				"vein_crystal": 1
			},
			"coins": 160,
			"xp": 220,
			"flag": "ch2_done"
		}
	},
	{
		"id": "ch3",
		"num": "III",
		"name": "The Keeper’s Debt",
		"mentor": "tao",
		"region": 3,
		"intro": [
			"Keeper Tao: So Suyin sent you. Qiu was my student once. He believes the river should flow only for him.",
			"Keeper Tao: Learn to tell stone from spirit. Bring me Jade Ore from the monastery veins and Spirit Ginseng from the gardens."
		],
		"grant": {
			"items": {
				"mend_pill": 2,
				"qi_pill": 2
			},
			"coins": 40
		},
		"steps": [
			{
				"type": "talk",
				"npc": "tao",
				"text": "Speak with Keeper Tao",
				"short": "Speak with Tao"
			},
			{
				"type": "have",
				"items": {
					"jade_ore": 2,
					"ginseng": 1
				},
				"text": "Bring 2 Jade Ore and 1 Spirit Ginseng",
				"short": "Stone and spirit"
			},
			{
				"type": "flag",
				"flag": "soul_awakened",
				"text": "Awaken Soul Sense (5 soul points — discover resource sites), then speak with Tao",
				"short": "Awaken the soul"
			},
			{
				"type": "flag",
				"flag": "dao_chosen",
				"text": "Choose your first Dao principle with Keeper Tao",
				"short": "Choose a Dao"
			},
			{
				"type": "boss",
				"id": "qiu",
				"text": "Confront Master Qiu at the Black Wind Monastery",
				"short": "Master Qiu"
			},
			{
				"type": "talk",
				"npc": "tao",
				"text": "Return to Keeper Tao",
				"short": "Return to Tao"
			}
		],
		"stepLines": {
			"2": "Keeper Tao: Jade ore is stone; a crystal is spirit. Your soul must learn the difference. Discover the valley’s resource sites until your Soul Sense wakes, then return.",
			"3": "Keeper Tao: Your soul sees. Now choose a principle — River or Ember. It will shape your arts.",
			"4": "Keeper Tao: Go. Qiu waits at the monastery summit. Do not let him drink the valley’s flow.",
			"5": "Keeper Tao: It is done? Come back to me."
		},
		"outro": [
			"Keeper Tao: The three fragments rejoin. Hear it? The river sings again, for everyone.",
			"Keeper Tao: Qiu’s debt is paid. Yours is only beginning — the valley still has veins to read and realms to climb.",
			"— The Broken Seal is restored. Jade River remains open for cultivation, crafting and commissions. —"
		],
		"reward": {
			"items": {
				"seal_fragment": 1,
				"source_crystal": 1
			},
			"coins": 400,
			"xp": 400,
			"flag": "ch3_done"
		}
	}
]

const COMMISSIONS = {
	"jr_town": [
		{
			"id": "c_dew",
			"text": "Deliver 4 Dewleaf to the apothecary",
			"give": {
				"herb": 4
			},
			"reward": {
				"coins": 30,
				"xp": 20
			}
		},
		{
			"id": "c_cu",
			"text": "Deliver 3 Copper Ore to the forge",
			"give": {
				"copper": 3
			},
			"reward": {
				"coins": 36,
				"xp": 24
			}
		},
		{
			"id": "c_raid",
			"text": "Drive off 6 River Raiders",
			"kill": {
				"raider": 6
			},
			"reward": {
				"coins": 45,
				"xp": 40
			}
		}
	],
	"lantern": [
		{
			"id": "c_eel",
			"text": "Deliver 3 Moon Eel to the lantern cooks",
			"give": {
				"eel": 3
			},
			"reward": {
				"coins": 60,
				"xp": 45
			}
		},
		{
			"id": "c_iron",
			"text": "Deliver 3 Iron Ore to the shipwright",
			"give": {
				"iron": 3
			},
			"reward": {
				"coins": 70,
				"xp": 50
			}
		},
		{
			"id": "c_wolf",
			"text": "Thin the wolf packs: defeat 5 Bamboo Wolves",
			"kill": {
				"wolf": 5
			},
			"reward": {
				"coins": 80,
				"xp": 70
			}
		}
	],
	"cloudrest": [
		{
			"id": "c_koi",
			"text": "Deliver 2 Spirit Koi to the court pond",
			"give": {
				"koi": 2
			},
			"reward": {
				"coins": 110,
				"xp": 90
			}
		},
		{
			"id": "c_gin",
			"text": "Deliver 2 Spirit Ginseng to the physician",
			"give": {
				"ginseng": 2
			},
			"reward": {
				"coins": 120,
				"xp": 100
			}
		},
		{
			"id": "c_aco",
			"text": "Defeat 4 Black Wind Acolytes",
			"kill": {
				"acolyte": 4
			},
			"reward": {
				"coins": 140,
				"xp": 130
			}
		}
	]
}

const COMMISSION_DAILY_CAP = 3

const GUIDANCE = [
	"Move with WASD / arrows or the left stick. Up and down walk toward or away from the camera — on the ground and on roofs and bridges alike.",
	"Space / Jump to leap. Down + Jump drops through a bridge. Stairs and ramps climb to raised decks.",
	"J / Attack strikes. Swipe the Attack button sideways (or K) to Step-dash; swipe up (or hold L) to guard.",
	"Switch to Cultivation Mode (Tab) to Meditate at shrines and open your systems. Danger returns you to Combat Mode.",
	"F / the context button mines, harvests, fishes, talks and uses stations when you stand close — on the same level.",
	"Workshop crafting happens at a Forge or Furnace; recipes can be read anywhere."
]

const LORE = [
	{
		"title": "The Jade River",
		"text": "The valley’s river carries spirit water from the monastery peaks to the lowland towns. Its flow is held in balance by a three-part seal laid by the first keepers."
	},
	{
		"title": "Insight and Qi essence",
		"text": "Insight is understanding — earned by meditation and study, it gates breakthroughs. Qi essence is refined energy absorbed from crystals and meditation, spent to open meridians and temper the body. Your combat Qi bar is neither; it refills."
	},
	{
		"title": "Stone and spirit",
		"text": "Jade ore is stone for the forge. Spirit Shards, Vein Crystals and Source Crystals are spirit — absorb them for Qi essence."
	},
	{
		"title": "Weapon mastery",
		"text": "Each meaningful strike with a sword or spear builds mastery in that family. Switching weapons never erases the other family’s record."
	}
]

const NPCS = {
	"wen": {
		"name": "Elder Wen",
		"look": "wen",
		"area": "jr_town",
		"title": "Elder of Jade River"
	},
	"suyin": {
		"name": "Archivist Suyin",
		"look": "suyin",
		"area": "lantern",
		"title": "Keeper of the Lantern Archive"
	},
	"tao": {
		"name": "Keeper Tao",
		"look": "tao",
		"area": "cloudrest",
		"title": "Warden of Cloudrest"
	}
}

