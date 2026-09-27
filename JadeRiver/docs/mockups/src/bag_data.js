// The Bag concepts (07_bag_a, 07_bag_b, 07_bag_c and B's card, pill and early pages): the character's bag slot by
// slot, as saved at two valley_run checkpoints (frozen copies of user://valley_cp/ls6_end and bf2, 2026-09-27 07:25 UTC).
// Each slot: [icon under art/icons, grade, count, kind, quality (gear), HD]. kind: g gear, p pills, m materials, o other
// (from each item's type). HD 1 marks an icon with its @64 render in data/icon_manifest.json (Style A, drawn 1:1);
// the rest are legacy 32 art px icons drawn at 2x. null is an empty space.
var BAG = {
  ls6_end: {
    gourd: "Sunsteel Gourd", cap: 55, next: "Driftglass Gourd", nextCap: 60, keys: 28,
    counts: {all: 41, g: 6, p: 7, m: 22, o: 6},
    slots: [
      ["items/storm_shard", "spirit", 84, "m", "", 1], ["items/rice_ball", "plain", 29, "o", "", 0],
      ["items/soul_core_peak", "spirit", 1, "m", "", 1], ["items/storm_blood_pill", "mystic", 5, "p", "", 1],
      ["items/thunder_horn", "spirit", 3, "m", "", 1], ["items/comet_iron", "sage", 12, "m", "", 1],
      ["items/tough_meat", "plain", 3, "m", "", 1], ["items/kite_silk", "spirit", 4, "m", "", 1],
      ["items/comet_plume", "sovereign", 6, "m", "", 1], ["items/healing_pill", "common", 6, "p", "", 1],
      ["items/jelly_silk", "sovereign", 5, "m", "", 1], ["items/star_shard", "sovereign", 64, "m", "", 1],
      ["items/star_core_peak", "spirit", 1, "m", "", 1], ["equipment/driftsteel_fan", "sovereign", 1, "g", "common", 1],
      ["items/star_powder", "sovereign", 8, "m", "", 1], ["items/lu_journal_page", "plain", 3, "o", "", 0],
      ["equipment/driftsteel_jian", "sovereign", 1, "g", "common", 1], ["equipment/cloudsteel_jian", "heaven", 1, "g", "common", 1],
      ["items/tide_cleansing_pill", "sovereign", 2, "p", "", 1], ["items/revival_talisman", "common", 2, "o", "", 0],
      ["equipment/driftsteel_heavy_sabre", "sovereign", 1, "g", "superior", 1], ["items/bonding_offering_heaven", "heaven", 3, "o", "", 0],
      ["items/stormsteel_ore", "spirit", 4, "m", "", 1], ["items/lantern_incense", "sovereign", 5, "o", "", 0],
      ["items/spirit_stone_shard", "earth", 23, "m", "", 1], ["items/wyrm_ash", "will", 4, "m", "", 1],
      ["items/hollow_shard", "earth", 12, "m", "", 1], ["items/guardian_scale", "sovereign", 2, "m", "", 1],
      ["items/orbit_stone_chip", "sovereign", 1, "m", "", 1], ["items/cinder_ash", "will", 3, "m", "", 1],
      ["items/clear_mind_pill", "earth", 2, "p", "", 1], ["items/copperjaw_box", "will", 1, "o", "", 0],
      ["items/drone_shell", "will", 12, "m", "", 1], ["equipment/ink_warden_brush", "sage", 1, "g", "common", 1],
      ["items/eel_essence", "will", 8, "m", "", 1], ["items/leviathan_scale", "will", 7, "m", "", 1],
      ["equipment/lanternsteel_jian", "will", 1, "g", "superior", 1], null, null, null,
      ["items/sovereign_settling_pill", "sage", 2, "p", "", 1], null, null,
      ["items/formation_stone", "earth", 2, "m", "", 1], ["items/qi_restoration_pill", "common", 3, "p", "", 1], null, null, null,
      ["items/will_tempering_pill", "sage", 32, "p", "", 1], null, null, null, null, null, null
    ],
    worn: {hat: ["equipment/stormsilk_hat", "spirit"], weapon: ["equipment/sunsteel_jian", "sage"], robe: ["equipment/sunsilk_robe", "sage"],
      gourd: ["equipment/sunsteel_gourd", "sage"], trousers: ["equipment/stormsilk_trousers", "spirit"], cape: null,
      boots: ["equipment/sunsilk_boots", "sage"], talisman: null}
  },
  bf2: {
    gourd: "Starter Spirit Gourd", cap: 25, next: "Bamboo Gourd", nextCap: 30, keys: 3,
    counts: {all: 8, g: 1, p: 0, m: 5, o: 2},
    slots: [
      ["items/tough_meat", "plain", 4, "m", "", 1], ["items/rice_ball", "plain", 6, "o", "", 0],
      ["items/crab_shell", "plain", 5, "m", "", 1], ["items/river_mud", "plain", 3, "m", "", 0],
      ["items/rat_tail", "plain", 3, "m", "", 1], ["items/snapper_claw", "common", 2, "o", "", 1],
      ["equipment/plain_straw_hat", "plain", 1, "g", "common", 1], ["items/boar_hide", "plain", 4, "m", "", 1],
      null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null
    ],
    worn: {hat: null, weapon: "locked", robe: ["equipment/hemp_robe", "plain"], gourd: ["equipment/starter_gourd", "plain"],
      trousers: ["equipment/hemp_trousers", "plain"], cape: "locked", boots: ["equipment/straw_sandals", "plain"], talisman: "locked"}
  }
};

var ICONS = "../../../art/icons/";

// One 76 px page slot (kit .k-slot76): the icon 1:1, the grade rim, the quality gem on gear, the count; opts.sel marks
// the chosen one, opts.cls adds classes, opts.locked draws a next-gourd space.
function slotHTML(s, opts) {
  opts = opts || {};
  var cls = "k-slot k-slot76" + (opts.cls ? " " + opts.cls : "");
  if (opts.locked) return '<div class="' + cls + ' is-disabled"><span class="k-lock-mini" style="position:absolute;left:32px;top:30px"></span></div>';
  if (!s) return '<div class="' + cls + ' is-empty"></div>';
  var h = '<div class="' + cls + (opts.sel ? " is-selected" : "") + '"><img class="ic" src="' + ICONS + s[0] + '.png">' +
    '<div class="k-qrim" style="--q:var(--g-' + s[1] + ')"></div>';
  if (s[4] && s[4] !== "common") h += '<span class="gem" style="--gq:var(--q-' + s[4] + ')"></span>';
  if (s[2] > 1) h += '<span class="k-count t-fig t-outline c-paper">' + s[2] + "</span>";
  if (opts.fresh) h += '<span class="k-new" style="right:5px;top:5px"></span>';
  if (opts.sel) h += '<div class="k-slot-glow"></div>';
  return h + "</div>";
}

// Fill `el` with the checkpoint's slots in order, then `locked` spaces of the next gourd; opts.sel is the chosen index.
function fillGrid(el, cp, opts) {
  opts = opts || {};
  var b = BAG[cp], h = "";
  b.slots.forEach(function (s, i) { h += slotHTML(s, {sel: i === opts.sel, fresh: opts.fresh === i, cls: opts.cls}); });
  for (var k = 0; k < (opts.locked || 0); k++) h += slotHTML(null, {locked: true, cls: opts.cls});
  el.innerHTML = h;
}
