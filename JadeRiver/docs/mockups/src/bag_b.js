// Bag concept B: the sky inside the gourd, drawn into <svg class="sky"> with a seeded random so every render is the
// same. drawSky(svg, {stars, islands, seed}): stars scale with the gourd's size; islands are [cx, cy, width, depth]
// (depth 0 near .. 1 far: smaller, hazier, bluer), the figure's own island is drawn by the page.
function rng(seed) { var s = seed >>> 0; return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

function islandPath(cx, cy, w, r) {
  // a floating rock: a gently domed top, a jagged underside tapering to a point below
  var h = w * 0.62, top = [], bot = [], n = 9, i;
  for (i = 0; i <= n; i++) { var t = i / n, x = cx - w / 2 + w * t; top.push([x, cy - Math.sin(Math.PI * t) * w * 0.07 - (r() - 0.5) * w * 0.02]); }
  for (i = n; i >= 0; i--) { var u = i / n, xx = cx - w / 2 + w * u, d = Math.sin(Math.PI * u); bot.push([xx + (r() - 0.5) * w * 0.05, cy + d * h * (0.55 + r() * 0.45)]); }
  var p = "M" + top.map(function (q) { return q[0].toFixed(1) + " " + q[1].toFixed(1); }).join(" L");
  p += " L" + bot.map(function (q) { return q[0].toFixed(1) + " " + q[1].toFixed(1); }).join(" L") + " Z";
  return p;
}

function drawSky(svg, o) {
  var r = rng(o.seed || 7), h = "";
  h += '<defs><radialGradient id="star"><stop offset="0" stop-color="#fff8e0"/><stop offset=".35" stop-color="rgba(255,230,161,.8)"/><stop offset="1" stop-color="rgba(255,230,161,0)"/></radialGradient>' +
    '<linearGradient id="rock" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#56706a"/><stop offset=".3" stop-color="#2f4d49"/><stop offset="1" stop-color="#0c2226"/></linearGradient>' +
    '<linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2c9e8f"/><stop offset="1" stop-color="#15514f"/></linearGradient>' +
    '<linearGradient id="shaft" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgba(255,230,161,.12)"/><stop offset="1" stop-color="rgba(255,230,161,0)"/></linearGradient>' +
    '<linearGradient id="grass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#67d6bd"/><stop offset="1" stop-color="#2c9e8f"/></linearGradient></defs>';
  // stars: most are dust, a few are lit with a cross
  for (var i = 0; i < o.stars; i++) {
    var x = r() * 1280, y = Math.pow(r(), 1.35) * 640, s = r(), a = 0.25 + r() * 0.6;
    if (s > 0.985) h += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="7" fill="url(#star)"/>' +
      '<path d="M' + (x - 7).toFixed(1) + " " + y.toFixed(1) + " H" + (x + 7).toFixed(1) + " M" + x.toFixed(1) + " " + (y - 7).toFixed(1) + " V" + (y + 7).toFixed(1) +
      '" stroke="rgba(255,248,224,.75)" stroke-width="1"/>';
    else h += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="' + (s > 0.9 ? 1.4 : s > 0.6 ? 1 : 0.7) + '" fill="rgba(' +
      (s > 0.8 ? "255,230,161" : s > 0.4 ? "232,225,207" : "175,201,209") + "," + a.toFixed(2) + ')"/>';
  }
  // light falling in through the gourd's mouth, far above
  if (o.shafts) h += '<path d="M640 -10 L760 -10 L1010 640 L470 640 Z" fill="url(#shaft)"/><path d="M690 -10 L720 -10 L800 520 L610 520 Z" fill="url(#shaft)"/>';
  // far islands, the farthest first
  (o.islands || []).slice().sort(function (p, q) { return q[3] - p[3]; }).forEach(function (is) {
    var cx = is[0], cy = is[1], w = is[2], d = is[3], op = (1 - d * 0.55).toFixed(2);
    h += '<g opacity="' + op + '">';
    h += '<ellipse cx="' + cx + '" cy="' + (cy + w * 0.32) + '" rx="' + (w * 0.6) + '" ry="' + (w * 0.16) + '" fill="rgba(103,214,189,' + (0.05 + (1 - d) * 0.05).toFixed(2) + ')"/>';
    h += '<path d="' + islandPath(cx, cy, w, r) + '" fill="url(#rock)" stroke="rgba(103,214,189,' + (0.18 + (1 - d) * 0.2).toFixed(2) + ')" stroke-width="1"/>';
    if (d === 0) h += '<ellipse cx="' + cx + '" cy="' + (cy + 2) + '" rx="' + (w * 0.5) + '" ry="' + (w * 0.075) + '" fill="url(#face)" stroke="#67d6bd" stroke-width="1.5"/>';
    else h += '<path d="M' + (cx - w * 0.48) + " " + (cy + 1) + " Q" + cx + " " + (cy - w * 0.1) + " " + (cx + w * 0.48) + " " + (cy + 1) + '" fill="none" stroke="url(#grass)" stroke-width="' + Math.max(2, w * 0.035).toFixed(1) + '"/>';
    // a pine or two, and on the bigger ones a pavilion roof
    var trees = d === 0 ? 0 : Math.max(1, Math.round(w / 60));
    for (var t = 0; t < trees; t++) {
      var tx = cx - w * 0.3 + r() * w * 0.6, th = w * (0.12 + r() * 0.08);
      h += '<path d="M' + tx.toFixed(1) + " " + (cy - th).toFixed(1) + " L" + (tx + th * 0.35).toFixed(1) + " " + (cy - 1).toFixed(1) + " L" + (tx - th * 0.35).toFixed(1) + " " + (cy - 1).toFixed(1) +
        ' Z" fill="#15514f" stroke="rgba(103,214,189,.35)" stroke-width="1"/>';
    }
    if (w > 110 && d > 0) {
      var px = cx + w * 0.12, pw = w * 0.2;
      h += '<rect x="' + (px - pw * 0.3).toFixed(1) + '" y="' + (cy - pw * 0.5).toFixed(1) + '" width="' + (pw * 0.6).toFixed(1) + '" height="' + (pw * 0.5).toFixed(1) + '" fill="#2b1e16"/>' +
        '<path d="M' + (px - pw * 0.62).toFixed(1) + " " + (cy - pw * 0.46).toFixed(1) + " Q" + px.toFixed(1) + " " + (cy - pw * 0.62).toFixed(1) + " " + (px + pw * 0.62).toFixed(1) + " " + (cy - pw * 0.46).toFixed(1) +
        " L" + (px + pw * 0.4).toFixed(1) + " " + (cy - pw * 0.8).toFixed(1) + " L" + (px - pw * 0.4).toFixed(1) + " " + (cy - pw * 0.8).toFixed(1) + ' Z" fill="#9a6a35" stroke="#071015" stroke-width="1"/>' +
        '<circle cx="' + px.toFixed(1) + '" cy="' + (cy - pw * 0.25).toFixed(1) + '" r="' + (pw * 0.09).toFixed(1) + '" fill="#e5b84c"/>';
    }
    h += "</g>";
  });
  svg.innerHTML = h;
}

// The page itself (07_bag_b, _card, _pill, 08_bag_b_empty): everything but the card and the hint. cfg: cp (checkpoint),
// fig, purses [[icon, value]], sky {seed, stars, islands, shafts}, sel (chosen index), fresh (a new item's index),
// glow (the worn slot a card compares against, or the empty slot a new piece fits, ringed), locked (the next gourd's
// spaces shown), rows (rows in view; more fade out and the rail shows the scroll), subtitle and spaceLine.
var WORN_AT = [["hat", "Hat", 92, 214], ["weapon", "Weapon", 318, 214], ["robe", "Robe", 46, 330], ["gourd", "Gourd", 364, 330],
  ["trousers", "Trousers", 46, 446], ["cape", "Cape", 364, 446], ["boots", "Boots", 92, 562], ["talisman", "Talisman", 318, 562]];

function buildPageB(cfg) {
  var b = BAG[cfg.cp], h = "", scr = document.querySelector(".k-screen");
  var kinds = [["all", "All"], ["g", "Gear"], ["p", "Pills"], ["m", "Materials"], ["o", "Other"]];
  h += '<div class="void"></div><svg class="sky" id="sky" width="1280" height="720"></svg>';
  h += '<svg class="abs" style="left:0;top:0" width="1280" height="720">' +
    '<ellipse cx="205" cy="388" rx="170" ry="232" fill="none" stroke="rgba(229,184,76,.18)" stroke-width="7"/>' +
    '<ellipse cx="205" cy="388" rx="170" ry="232" fill="none" stroke="#e5b84c" stroke-width="1.6" stroke-dasharray="2 6" opacity=".8"/></svg>';
  h += '<div class="sea"></div>';
  h += '<div class="title inked">Bag</div><div class="subtitle">' + cfg.subtitle + "</div>";
  h += '<div class="tok is-on" style="left:420px;top:12px"><span class="inked">Spirit Gourd</span></div>' +
    '<div class="tok" style="left:582px;top:12px"><img class="ic ic-32" src="' + ICONS + 'items/mudwater_key.png">Key Pouch <span class="n">' + b.keys + "</span></div>";
  var px = 1196;
  cfg.purses.slice().reverse().forEach(function (p) {
    var w = 64 + String(p[1]).length * 10;
    px -= w + 12;
    h += '<div class="k-pill abs" style="left:' + px + 'px;top:19px"><img class="ic" src="' + ICONS + p[0] + '.png"><span class="v">' + p[1] + "</span></div>";
  });
  h += '<div class="k-close abs" style="left:1214px;top:10px"></div>';
  h += '<div class="abs flex" style="left:420px;top:96px;gap:8px">';
  kinds.forEach(function (k, i) {
    var n = b.counts[k[0]];
    h += '<div class="tok' + (i === 0 ? " is-on" : n === 0 ? " is-dim" : "") + '" style="position:relative">' + k[1] + ' <span class="n">' + n + "</span></div>";
  });
  h += "</div>";
  h += '<div class="k-btn2 abs" style="left:1136px;top:96px;width:96px;height:48px;font-size:20px">Sort</div>';
  h += '<div class="space" style="left:420px;top:' + (cfg.spaceTop || 664) + 'px;text-align:left"><span class="t-sm c-mist">Space </span><span class="v">' +
    b.slots.filter(function (s) { return s; }).length + " / " + b.cap + '</span><span class="t-sm c-mist" style="margin-left:14px">' +
    '<span class="k-lock-mini" style="vertical-align:-2px;margin-right:6px"></span>' + cfg.spaceLine + "</span></div>";
  h += '<img class="k-fig fig25" style="left:190px;top:592px" src="../assets/' + cfg.fig + '">';
  WORN_AT.forEach(function (w) {
    var s = b.worn[w[0]], ring = cfg.glow === w[0];
    var inner = s === "locked" ? '<div class="k-slot k-slot76 is-disabled"><span class="k-lock-mini" style="position:absolute;left:32px;top:30px"></span></div>'
      : slotHTML(s ? [s[0], s[1], 1, "g", "", 1] : null);
    h += '<div class="worn' + (ring ? ' is-ringed" data-ov-pad="5' : "") + '" style="left:' + (w[2] - 38) + "px;top:" + (w[3] - 38) + 'px">' + inner + "</div>" +
      '<div class="slot-l' + (s === "locked" ? " c-hollow" : ring ? " c-pale" : "") + '" style="left:' + w[2] + "px;top:" + (w[3] + 45) + 'px">' + w[1] + "</div>";
  });
  var rows = Math.ceil((b.slots.length + (cfg.locked || 0)) / 10);
  var inView = cfg.rows || rows;
  h += '<div class="field' + (inView < rows ? '"' : ' no-fade" style="height:' + (rows * 80 - 4) + 'px"') + '><div class="grid" id="grid"></div></div>';
  if (inView < rows) h += '<div class="rail"><div class="th" style="top:0;height:' + Math.round(460 * inView / rows) + 'px"></div></div>';
  scr.insertAdjacentHTML("afterbegin", h);
  drawSky(document.getElementById("sky"), cfg.sky);
  fillGrid(document.getElementById("grid"), cfg.cp, {locked: cfg.locked || 0, sel: cfg.sel, fresh: cfg.fresh});
}
