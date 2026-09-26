class_name PostRules
extends RefCounted
## S50 · Keeping Post (V10, docs/idle_gathering_design.md §3): idle gathering after IdleOn's AFK model. Pure
## functions over data/posts.json "rules": craft EXP and levels, Diligence, Finesse, the yield of one action, the
## swing, the hourly rates of a post, pouch capacity and the settle amounts.

## Dotted lookup into posts.json "rules", e.g. "yield.chance_exp".
static func rule(path: String, fallback = 0.0):
	var r = ContentDB.config("posts").get("rules", {})
	for k in path.split("."):
		if not (r is Dictionary) or not r.has(k): return fallback
		r = r[k]
	return r

# ------------------------------------------------------------------ craft levels (§3.2)
## EXP from `level` to the next: floor((15 + L² + 15L) × (1.225 − min(0.164, 0.135·L/(L+50)))^L − 30).
static func xp_to_next(level: int) -> float:
	var x: Dictionary = rule("xp", {})
	var l := float(level)
	var m := float(x.get("base", 1.225)) - minf(float(x.get("cut", 0.164)), float(x.get("k", 0.135)) * l / (l + float(x.get("k_off", 50.0))))
	return maxf(1.0, floorf((float(x.get("a", 15.0)) + l * l + 15.0 * l) * pow(m, l) - float(x.get("minus", 30.0))))

## {level, into, need}: the level `xp` total EXP reaches, the EXP into it and the EXP it needs.
static func level_info(xp: float) -> Dictionary:
	var lv := 1
	var left := maxf(0.0, xp)
	var cap := int(rule("xp.max_level", 200))
	while lv < cap:
		var need := xp_to_next(lv)
		if left < need: return {"level": lv, "into": left, "need": need}
		left -= need
		lv += 1
	return {"level": cap, "into": 0.0, "need": 0.0}

static func level_for(xp: float) -> int:
	return int(level_info(xp).level)

# ------------------------------------------------------------------ Diligence (§3.1)
## The share of full-speed work a post earns: base (52% crafts, 40% Vigil) plus additive sources, then a multiplier.
static func diligence(kind: String, sources_pct := 0.0, multi := 1.0) -> float:
	var d: Dictionary = rule("diligence", {})
	var base := float(d.get("martial_base", 0.40)) if kind == "martial" else float(d.get("craft_base", 0.52))
	return maxf(float(d.get("floor", 0.01)), base + sources_pct / 100.0) * multi

# ------------------------------------------------------------------ Finesse (§3.3)
## Finesse of a craft: tool power, the craft's attribute, the craft level, flat Finesse (seals), percentage groups
## (each multiplies on its own) and Guardian Stele power added to the tool's power.
static func finesse(power: float, attribute: float, level: int, flat := 0.0, pct_groups: Array = [], stele_power := 0.0) -> float:
	var f: Dictionary = rule("finesse", {})
	var base := 2.0 * (power + stele_power) + float(f.get("base_flat", 4.0))
	var a := maxf(0.0, attribute)
	var inner := pow(base, float(f.get("tool_exp", 1.3))) + pow(a + 1.0, float(f.get("stat_flat_exp", 0.6))) + flat
	var v := inner * (1.0 + float(level) * float(f.get("per_level", 0.005))) \
		* (1.0 + pow(a / 100.0, float(f.get("stat_mult_exp", 0.35)))) * (1.0 + base / 100.0)
	for g in pct_groups: v *= 1.0 + float(g) / 100.0
	return float(f.get("flat", 12.0)) + v

# ------------------------------------------------------------------ one action (§3.4)
## {r, chance, abundance, abundance_progress, windfall, next_finesse}. `next_finesse` is the Finesse where the
## Chance bar fills (below full) or the next whole Abundance unit is reached (at full).
static func yield_of(fin: float, toughness: float, flow := 0.0, windfall := 0.0) -> Dictionary:
	var y: Dictionary = rule("yield", {})
	var full_at := float(y.get("full_at", 10.0)) * maxf(1.0, toughness)
	var r := fin / full_at
	var chance := 0.0
	if r >= float(y.get("chance_min_r", 0.025)): chance = minf(1.0, pow(r, float(y.get("chance_exp", 0.4))))
	var ex := float(y.get("abundance_exp", 0.25)) + clampf(flow, 0.0, float(y.get("flow_cap", 0.10)))
	var abundance := 1.0
	var progress := 0.0
	var next := full_at
	if r >= 1.0:
		var raw := pow(r, ex)
		abundance = maxf(1.0, floorf(raw))
		progress = raw - floorf(raw)
		next = pow(abundance + 1.0, 1.0 / ex) * full_at
	var w := clampf(windfall, 0.0, 0.95)
	var wf := 1.0
	var p := 1.0
	for i in int(y.get("windfall_chain", 4)):
		p *= w
		wf += p
	return {"r": r, "chance": chance, "abundance": abundance, "abundance_progress": progress, "windfall": wf, "next_finesse": next}

## Seconds a swing takes with a tool of `speed` (3-10) and speed bonuses: 6 × (1 + (10 − speed)/5) / (1 + %).
static func swing_seconds(speed: float, speed_pct := 0.0) -> float:
	var s: Dictionary = rule("swing", {})
	var t := float(s.get("scale", 6.0)) * (float(s.get("base", 1.0)) + (float(s.get("top_speed", 10)) - speed) * float(s.get("per_speed", 0.2)))
	return maxf(0.5, t / (1.0 + speed_pct / 100.0))

# ------------------------------------------------------------------ rates (§3.6)
## Hourly rates of a craft post. `outputs`: [{item, toughness, exp, weight}] (weights already include night shares).
## Returns {actions_h, items: {item: per hour}, exp_h, outputs: [{item, share, chance, abundance, ...}]}.
static func rates(fin: float, outputs: Array, speed: float, dil: float, flow := 0.0, windfall := 0.0, speed_pct := 0.0, exp_mult := 1.0) -> Dictionary:
	var actions := 3600.0 / swing_seconds(speed, speed_pct)
	var total_w := 0.0
	for o in outputs: total_w += maxf(0.0, float(o.get("weight", 1.0)))
	var items := {}
	var exp_h := 0.0
	var rows: Array = []
	for o in outputs:
		var share := maxf(0.0, float(o.get("weight", 1.0))) / total_w if total_w > 0.0 else 0.0
		var y := yield_of(fin, float(o.get("toughness", 1.0)), flow, windfall)
		var per := actions * share * float(y.chance) * float(y.abundance) * float(y.windfall) * dil
		var id := str(o.get("item", ""))
		items[id] = float(items.get(id, 0.0)) + per
		exp_h += actions * share * float(y.chance) * float(o.get("exp", 0.0)) * exp_mult * dil
		var row := y.duplicate()
		row.merge({"item": id, "share": share, "per_h": per, "toughness": float(o.get("toughness", 1.0))}, true)
		rows.append(row)
	return {"actions_h": actions, "items": items, "exp_h": exp_h, "outputs": rows}

# ------------------------------------------------------------------ pouches (§3.7)
## A category's capacity: compartments × the sewn compartment cap × (1 + capacity %), at most the hard cap.
static func capacity(compartment_cap: float, pct := 0.0) -> float:
	var p: Dictionary = rule("pouch", {})
	return minf(float(p.get("hard_cap", 2050000000)), float(p.get("compartments", 4)) * compartment_cap * (1.0 + pct / 100.0))

## The compartment cap of a sewn tier (0: unsewn, the base 10).
static func compartment_cap(tier: int) -> float:
	var tiers: Array = ContentDB.config("posts").get("pouch_tiers", [])
	if tier <= 0 or tiers.is_empty(): return float(rule("pouch.base_cap", 10))
	return float(tiers[mini(tier, tiers.size()) - 1])

## Hours until a category fills from `held` at `per_h` (INF when nothing flows in).
static func fill_hours(cap: float, held: float, per_h: float) -> float:
	if per_h <= 0.0: return INF
	return maxf(0.0, (cap - held) / per_h)

# ------------------------------------------------------------------ settling (§3.8)
## Expected amounts for `hours` of a post: each category stops filling when its pouch is full, EXP does not.
## `rates_items`: item -> per hour; `category_of`: item -> category; `held` and `caps`: category -> count / capacity.
## Returns {items: {item: expected}, full: {category: hours into the span when it filled}}.
static func settle_amounts(hours: float, rates_items: Dictionary, category_of: Dictionary, held: Dictionary, caps: Dictionary) -> Dictionary:
	var per_cat := {}
	for id in rates_items: per_cat[category_of.get(id, "material")] = float(per_cat.get(category_of.get(id, "material"), 0.0)) + float(rates_items[id])
	var eff := {}
	var full := {}
	for cat in per_cat:
		var fh := fill_hours(float(caps.get(cat, 0.0)), float(held.get(cat, 0.0)), float(per_cat[cat]))
		eff[cat] = minf(hours, fh)
		if fh < hours: full[cat] = fh
	var items := {}
	for id in rates_items:
		items[id] = float(rates_items[id]) * float(eff.get(category_of.get(id, "material"), 0.0))
	return {"items": items, "full": full}

## A seeded whole number for an expected amount: floor(x), plus one with the chance of its fraction.
static func draw(x: float, rng: RandomNumberGenerator) -> int:
	var n := int(floorf(maxf(0.0, x)))
	if rng != null and rng.randf() < x - floorf(x): n += 1
	return n

# ------------------------------------------------------------------ the Vigil (§7.2)
## Kills an hour before Diligence: the room's spawn cap against the fighter's own pace (IdleOn's two caps).
## `pace` scales the fighter's cap to Jade River's slower fights (wind-ups, dodges, hits taken).
static func kills_per_hour(mobs: float, respawn_s: float, walk_s: float, wait_s: float, hp: float, avg_hit: float, hit: float, k := 1.0, pace := 1.0) -> Dictionary:
	var spawn := maxf(0.0, mobs) / (maxf(0.0, respawn_s) + 0.1)
	var swings := maxf((hp / maxf(1.0, avg_hit) + 0.52) / maxf(0.01, hit), 1.0)
	var fighter := clampf(k, 1.0, 2.2) / (maxf(0.0, walk_s) + maxf(0.05, wait_s) * swings) * pace
	return {"spawn_h": 3600.0 * spawn, "fighter_h": 3600.0 * fighter, "kills_h": floorf(3600.0 * minf(spawn, fighter)), "swings": swings,
		"fight_share": (maxf(0.05, wait_s) * swings) / (maxf(0.0, walk_s) + maxf(0.05, wait_s) * swings)}

## Sweep: a blow at least twice a foe's life fells more than one. tier = floor(log2(max hit / HP)); kills x max(1, tier x rate).
static func sweep(max_hit: float, hp: float, rate := 0.5) -> Dictionary:
	if hp <= 0.0 or max_hit < 2.0 * hp: return {"tier": 0, "mult": 1.0}
	var tier := int(floorf(log(max_hit / hp) / log(2.0)))
	return {"tier": tier, "mult": maxf(1.0, float(tier) * rate)}

## How much of `hours` a Vigil keeps fighting. Provisions heal `heal_each` apiece and are eaten as damage outpaces
## regeneration; once they run out the character falls every max_hp / net hours and loses `down_s` each time.
## Returns {alive (share of the hours), food_used, fed_h}.
static func survivability(max_hp: float, dmg_h: float, regen_h: float, heal_each: float, food: int, hours: float, down_s := 600.0) -> Dictionary:
	var net := dmg_h - regen_h
	if net <= 0.0 or hours <= 0.0: return {"alive": 1.0, "food_used": 0, "fed_h": hours}
	var fed_h := 0.0
	var used := 0
	if heal_each > 0.0 and food > 0:
		var per_h := net / heal_each
		fed_h = minf(hours, float(food) / per_h)
		used = mini(food, int(ceilf(fed_h * per_h)))
	var die_h := maxf(0.01, max_hp / net)
	var starving := die_h / (die_h + down_s / 3600.0)
	var alive_h := fed_h + (hours - fed_h) * starving
	return {"alive": alive_h / hours, "food_used": used, "fed_h": fed_h}


# ------------------------------------------------------------------ Beast Snaring and Ancestral Rites (V10c, §7.3)
## A snare's catch: none if Finesse is under the beast's Toughness, else the snare's count x (Finesse / T)^0.25.
static func snare_catch(fin: float, toughness: float, critters: float) -> float:
	if toughness <= 0.0 or fin < toughness or critters <= 0.0: return 0.0
	return critters * pow(fin / toughness, 0.25)

## Rite charge an hour: 6 / max(5.7 - 0.2 x tablet speed^1.3 - level/40, 0.57).
static func rite_charge_rate(speed: float, level: int) -> float:
	var r: Dictionary = rule("rites", {})
	var d := float(r.get("charge_top", 5.7)) - float(r.get("speed_k", 0.2)) * pow(maxf(0.0, speed), 1.3) - float(level) / float(r.get("level_div", 40.0))
	return float(r.get("charge_base", 6.0)) / maxf(d, float(r.get("charge_floor", 0.57)))

static func rite_charge_cap(tablet_tier: int) -> float:
	var r: Dictionary = rule("rites", {})
	return float(r.get("cap_base", 50.0)) + float(r.get("cap_per_tier", 25.0)) * maxf(0.0, float(tablet_tier))

## The altar defence, resolved: the wave held from Finesse against the altar and the charge spent, and the wisps it
## calls: 5 x (1 + floor(100 x (F / 10T)^0.25) / 100) x ((5 + wave) / 10)^2.6.
static func rite_result(fin: float, toughness: float, charge: float) -> Dictionary:
	var r: Dictionary = rule("rites", {})
	var t := maxf(1.0, toughness)
	var wave := clampi(int(floorf(float(r.get("wave_log", 5.0)) * log(1.0 + fin / t) / log(2.0) + charge / float(r.get("wave_per_charge", 25.0)))),
		1, int(r.get("wave_max", 60)))
	var bonus := floorf(100.0 * pow(fin / (10.0 * t), 0.25)) / 100.0 if fin >= t else 0.0
	var wisps := float(r.get("wisps_base", 5.0)) * (1.0 + bonus) * pow((5.0 + wave) / 10.0, 2.6)
	var exp := float(wave) * float(r.get("exp_per_wave", 12.0)) * pow(1.0 + t / 100.0, 0.3)
	return {"wave": wave, "wisps": wisps, "exp": exp}

## Apprentice Bench: items an hour per apprentice, 3600 x speed / progress.
static func bench_rate(progress: float, speed := 1.0) -> float:
	return 3600.0 * maxf(0.0, speed) / maxf(1.0, progress)

# ------------------------------------------------------------------ the account web (V10d, §6)
## The two curves every account source uses: add = x1·L; decay = x1·L/(L + x2).
static func curve(kind: String, x1: float, x2: float, level: float) -> float:
	if level <= 0.0: return 0.0
	if kind == "decay": return x1 * level / (level + x2)
	return x1 * level

## Post Art points a character has for its summed craft levels.
static func art_points(total_levels: int) -> int:
	return int(total_levels / maxi(1, int(ContentDB.config("posts").get("arts", {}).get("points_per_levels", 2))))

## {item, count} to raise a seal from `level` to the next: the ladder's item for the level band, ceil(base × growth^L).
static func seal_cost(level: int, ladder: Array, mult := 1.0) -> Dictionary:
	if ladder.is_empty(): return {}
	var sc: Dictionary = ContentDB.config("posts").get("seal_cost", {})
	var i := mini(level / maxi(1, int(sc.get("step", 4))), ladder.size() - 1)
	return {"item": str(ladder[i]), "count": int(ceil(float(sc.get("base", 25)) * pow(float(sc.get("growth", 1.12)), level) * mult))}

## {taels, item, count} to raise a Guardian Stele from `level` to the next.
static func stele_cost(level: int) -> Dictionary:
	var st: Dictionary = ContentDB.config("posts").get("steles", {})
	var ladder: Array = st.get("ladder", ["copper_ore"])
	var i := mini(level / maxi(1, int(st.get("step", 5))), ladder.size() - 1)
	return {"taels": int(floor(float(st.get("taels", 150)) * pow(float(st.get("taels_growth", 1.22)), level))),
		"item": str(ladder[i]), "count": int(ceil(float(st.get("stone", 10)) * pow(float(st.get("stone_growth", 1.1)), level)))}
