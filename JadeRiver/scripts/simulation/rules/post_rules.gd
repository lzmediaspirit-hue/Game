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
## (each multiplies on its own) and stele power added to the tool base.
static func finesse(power: float, attribute: float, level: int, flat := 0.0, pct_groups: Array = [], stele_power := 0.0) -> float:
	var f: Dictionary = rule("finesse", {})
	var base := 2.0 * power + float(f.get("base_flat", 4.0)) + stele_power
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
