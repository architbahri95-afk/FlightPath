"use strict";
const $ = (s) => document.querySelector(s);
const NS = "http://www.w3.org/2000/svg";
const W = 620, H = 660;
const project = (lat, lon) => [(lon - 67) / 31 * W, (37.5 - lat) / 31.5 * H];

// Coarse outline of India (lon, lat) -- stylised, only there to give the chart a shape.
const OUTLINE = [[74.5,37],[77,35.5],[79,34],[78.5,32.5],[80,30.5],[81,30],[84,28.5],[88,27.5],[88.5,26.5],
  [89.5,26.8],[92,27],[95,28],[97,28],[96,27],[95,26],[94,24],[93,22],[92.5,24],[91.5,25],[90,25.2],[89,26],
  [88.7,24],[89,22],[87,21.5],[86.5,20],[85,19.3],[83,17.5],[82,16],[80.3,15.5],[80,13],[79.8,10.5],[79,9.2],
  [77.5,8.1],[76.5,9.5],[75.5,11.5],[74.5,14],[73.5,16.5],[72.8,19],[72.7,21],[70.5,20.8],[69,22.3],[70,23],
  [68.5,23.5],[68.3,24.3],[70.5,25.5],[70.5,27.5],[72,28.5],[74,31],[74.5,32.5],[74,34]];

const state = { airports: {}, routes: [], closed: new Set(), mode: "pick", next: "src", token: 0, timers: [] };
const METRIC = {
  distance: { label: "Distance", fmt: (v) => Math.round(v).toLocaleString("en-IN") + " km" },
  time: { label: "Time", fmt: (v) => { const m = Math.round(v); return Math.floor(m / 60) + " h " + String(m % 60).padStart(2, "0") + " min"; } },
  cost: { label: "Fare", fmt: (v) => "\u20B9" + Math.round(v).toLocaleString("en-IN") },
};

function el(name, attrs, parent) {
  const e = document.createElementNS(NS, name);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
const metric = () => document.querySelector("input[name=metric]:checked").value;
const setStatus = (t) => { $("#status").textContent = t || ""; };
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function init() {
  const net = await (await fetch("/api/network")).json();
  net.airports.forEach((a) => (state.airports[a.code] = a));
  state.routes = net.routes;
  const options = net.airports.slice().sort((a, b) => a.city.localeCompare(b.city))
    .map((a) => `<option value="${a.code}">${esc(a.city)} (${a.code})</option>`).join("");
  $("#src").innerHTML = '<option value="">Select airport</option>' + options;
  $("#dst").innerHTML = '<option value="">Select airport</option>' + options;
  $("#src").value = "DEL"; $("#dst").value = "TRV";
  drawMap();
  syncEnds();
  run();
}

function drawMap() {
  const svg = $("#map");
  svg.innerHTML = "";
  const defs = el("defs", {}, svg);
  const gr = el("linearGradient", { id: "landGrad", x1: 0, y1: 0, x2: 1, y2: 1 }, defs);
  el("stop", { offset: "0", "stop-color": "#1B3A72" }, gr); el("stop", { offset: "1", "stop-color": "#0F2247" }, gr);
  for (let lo = 68; lo <= 98; lo += 5) { const x = project(0, lo)[0]; el("line", { class: "grat", x1: x, y1: 0, x2: x, y2: H }, svg); }
  for (let la = 8; la <= 36; la += 4) { const y = project(la, 0)[1]; el("line", { class: "grat", x1: 0, y1: y, x2: W, y2: y }, svg); }
  el("path", { class: "land", d: "M" + OUTLINE.map(([lo, la]) => project(la, lo).map((n) => n.toFixed(1)).join(",")).join("L") + "Z" }, svg);
  const edges = el("g", {}, svg);
  state.routes.forEach((r) => {
    const a = state.airports[r.from], b = state.airports[r.to];
    const [x1, y1] = project(a.lat, a.lon), [x2, y2] = project(b.lat, b.lon);
    el("line", { class: "edge", x1, y1, x2, y2 }, edges);
  });
  el("g", { id: "seenLayer" }, svg);
  el("g", { id: "routeLayer" }, svg);
  const nodes = el("g", { id: "nodes" }, svg);
  Object.values(state.airports).forEach((a) => {
    const [x, y] = project(a.lat, a.lon);
    const g = el("g", { class: "airport", "data-code": a.code, tabindex: 0, role: "button", "aria-label": a.city + " " + a.code }, nodes);
    el("circle", { cx: x, cy: y, r: 5 }, g);
    const t = el("text", { x: x + 8, y: y + 3.5 }, g);
    t.textContent = a.code;
    el("title", {}, g).textContent = a.city;
    g.addEventListener("click", () => onAirport(a.code));
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onAirport(a.code); } });
  });
  refreshNodes();
}

function refreshNodes() {
  document.querySelectorAll(".airport").forEach((g) => {
    const c = g.dataset.code;
    g.classList.toggle("closed", state.closed.has(c));
    g.classList.toggle("end", c === $("#src").value || c === $("#dst").value);
  });
}
const syncEnds = refreshNodes;

function onAirport(code) {
  if (state.mode === "close") {
    if (code === $("#src").value || code === $("#dst").value) { setStatus("Change the origin or destination before closing " + code + "."); return; }
    state.closed.has(code) ? state.closed.delete(code) : state.closed.add(code);
    refreshNodes();
    run();
    return;
  }
  if (state.closed.has(code)) { setStatus(code + " is closed. Reopen it with Close airports mode."); return; }
  $("#" + state.next).value = code;
  state.next = state.next === "src" ? "dst" : "src";
  refreshNodes();
  setStatus("");
  if ($("#src").value && $("#dst").value) run();
}

function setMode(m) {
  state.mode = m;
  document.querySelectorAll(".seg button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.mode === m));
  $("#hint").textContent = m === "pick"
    ? "Click an airport to set the origin, then another for the destination."
    : "Click airports to close or reopen them. Routes avoid closed airports.";
}

function clearDrawing() {
  state.timers.forEach(clearTimeout);
  state.timers = [];
  $("#seenLayer").innerHTML = "";
  $("#routeLayer").innerHTML = "";
}

function drawRoute(path) {
  const layer = $("#routeLayer");
  layer.innerHTML = "";
  const pts = path.map((c) => project(state.airports[c].lat, state.airports[c].lon).join(",")).join(" ");
  const line = el("polyline", { class: "route", points: pts }, layer);
  const len = line.getTotalLength();
  line.style.strokeDasharray = len;
  line.style.strokeDashoffset = len;
  line.getBoundingClientRect();
  line.style.transition = matchMedia("(prefers-reduced-motion: reduce)").matches ? "none" : "stroke-dashoffset .8s ease-out";
  line.style.strokeDashoffset = 0;
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const plane = el("path", { class: "plane", d: "M0-7 L3 2 L7 4 L7 6 L2 4.5 L1 8 L3 9 L3 10 L0 9.2 L-3 10 L-3 9 L-1 8 L-2 4.5 L-7 6 L-7 4 L-3 2Z" }, layer);
    const m = el("animateMotion", { dur: Math.max(2.5, path.length * 1.1) + "s", repeatCount: "indefinite", rotate: "auto", path: "M" + pts.replace(/ /g, "L") }, plane);
    el("animateTransform", { attributeName: "transform", type: "rotate", values: "90", additive: "sum" }, plane);
  }
}

function animateSearch(visited, path) {
  clearDrawing();
  const layer = $("#seenLayer");
  const step = Math.min(45, 900 / Math.max(visited.length, 1));
  visited.forEach((c, i) => {
    state.timers.push(setTimeout(() => {
      const [x, y] = project(state.airports[c].lat, state.airports[c].lon);
      el("circle", { class: "seen", cx: x, cy: y, r: 10 }, layer);
    }, i * step));
  });
  state.timers.push(setTimeout(() => drawRoute(path), visited.length * step + 150));
}

async function run() {
  const src = $("#src").value, dst = $("#dst").value;
  refreshNodes();
  if (!src || !dst) { setStatus("Choose an origin and a destination."); return; }
  const q = new URLSearchParams({ src, dst, metric: metric(), algo: $("#algo").value, k: 3, avoid: [...state.closed].join(",") });
  const token = ++state.token;
  $("#run").disabled = true;
  try {
    const [route, cmp] = await Promise.all([fetch("/api/route?" + q), fetch("/api/compare?" + q)]).then((rs) => Promise.all(rs.map((r) => r.json())));
    if (token !== state.token) return;
    if (route.error) { setStatus(route.error); clearDrawing(); $("#result").innerHTML = $("#alts").innerHTML = $("#compare").innerHTML = ""; return; }
    setStatus("");
    renderResult(route);
    renderAlts(route);
    renderCompare(cmp, route.metric);
    if (route.found) animateSearch(route.visited, route.path);
    else clearDrawing();
  } catch (e) {
    setStatus("Could not reach the server. Is backend/server.py running?");
  } finally {
    $("#run").disabled = false;
  }
}

function totalsHtml(t, m) {
  return Object.keys(METRIC).map((k) =>
    `<div class="${k === m ? "active" : ""}">${METRIC[k].label}<b>${METRIC[k].fmt(t[k])}</b></div>`).join("");
}
function legsHtml(it) {
  return `<ul class="legs">${it.legs.map((l) =>
    `<li><span>${esc(l.from_city)} to ${esc(l.to_city)}</span><span>${METRIC.distance.fmt(l.distance)} &middot; ${METRIC.time.fmt(l.time)} &middot; ${METRIC.cost.fmt(l.cost)}</span></li>`).join("")}</ul>`;
}

function renderResult(r) {
  if (!r.found) {
    $("#result").innerHTML = `<p class="summary">No route found</p><p class="note">The closed airports cut these two cities apart. Reopen one to restore a path.</p>`;
    return;
  }
  const flights = r.path.length - 1;
  $("#result").innerHTML =
    `<p class="summary">${r.path.join(" \u2192 ")}</p>` +
    `<p class="note">${flights} flight${flights > 1 ? "s" : ""} &middot; found by ${esc(r.label)} after expanding ${r.stats.expanded} airports</p>` +
    `<div class="totals">${totalsHtml(r.itinerary.totals, r.metric)}</div>` + legsHtml(r.itinerary);
}

function renderAlts(r) {
  const box = $("#alts");
  if (!r.found || r.alternatives.length < 2) { box.innerHTML = ""; return; }
  box.innerHTML = `<h3 class="sec-title">Alternative routes (Yen's K-shortest)</h3><ul class="alts">` +
    r.alternatives.map((a, i) =>
      `<li><button type="button" data-i="${i}" aria-pressed="${i === 0}"><span>${a.path.join(" \u2192 ")}</span><small>${METRIC[r.metric].fmt(a.total)}</small></button></li>`).join("") + `</ul>`;
  box.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    box.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
    const alt = r.alternatives[+b.dataset.i];
    state.timers.forEach(clearTimeout);
    $("#seenLayer").innerHTML = "";
    drawRoute(alt.path);
    $("#result").innerHTML =
      `<p class="summary">${alt.path.join(" \u2192 ")}</p>` +
      `<p class="note">Alternative ${+b.dataset.i + 1} of ${r.alternatives.length}</p>` +
      `<div class="totals">${totalsHtml(alt.itinerary.totals, r.metric)}</div>` + legsHtml(alt.itinerary);
  }));
}

function renderCompare(rows, m) {
  const found = rows.filter((r) => r.found);
  if (!found.length) { $("#compare").innerHTML = ""; return; }
  const best = Math.min(...found.map((r) => r.total));
  $("#compare").innerHTML = `<h3 class="sec-title">All algorithms on this query</h3><div class="scroll"><table class="data">
    <thead><tr><th>Algorithm</th><th class="num">${METRIC[m].label}</th><th class="num">Expanded</th><th class="num">Relaxations</th><th class="num">&micro;s</th></tr></thead><tbody>` +
    rows.map((r) => {
      const ok = r.found && Math.abs(r.total - best) < 1e-6;
      const extra = r.found && !ok ? ` <small>(+${(((r.total - best) / best) * 100).toFixed(0)}%)</small>` : "";
      return `<tr class="${ok ? "best" : ""}"><td>${esc(r.label)}</td><td class="num">${r.found ? METRIC[m].fmt(r.total) + extra : "-"}</td>
        <td class="num">${r.expanded}</td><td class="num">${r.relaxations.toLocaleString()}</td><td class="num">${r.micros.toLocaleString()}</td></tr>`;
    }).join("") + `</tbody></table></div>
    <p class="note">The marked rows return the optimal ${METRIC[m].label.toLowerCase()}. BFS minimises the number of flights instead, so it can cost more.</p>`;
}

// ---------- Analysis tab ----------
const COLORS = { dijkstra: "#38D6E8", floyd_warshall: "#E8EEFB", bfs: "#FFB547" };
const NAMES = { dijkstra: "Dijkstra", floyd_warshall: "Floyd-Warshall", bfs: "BFS" };

async function runBenchmark() {
  $("#bench").disabled = true;
  $("#bench-status").textContent = "Running on networks of 10 to 100 airports...";
  try {
    const rows = await (await fetch("/api/benchmark")).json();
    $("#bench-status").textContent = "";
    drawChart(rows);
    $("#bench-table").innerHTML = `<table class="data"><thead><tr><th class="num">Airports</th><th class="num">Routes</th>` +
      Object.keys(NAMES).map((k) => `<th class="num">${NAMES[k]} steps</th>`).join("") + `</tr></thead><tbody>` +
      rows.map((r) => `<tr><td class="num">${r.n}</td><td class="num">${r.edges}</td>` +
        Object.keys(NAMES).map((k) => `<td class="num">${r.results[k].relaxations.toLocaleString()}</td>`).join("") + `</tr>`).join("") + `</tbody></table>`;
  } catch (e) {
    $("#bench-status").textContent = "Benchmark failed. Check that the server is running.";
  } finally {
    $("#bench").disabled = false;
  }
}

function drawChart(rows) {
  const w = 760, h = 380, m = { l: 64, r: 120, t: 16, b: 44 };
  const keys = Object.keys(NAMES);
  const all = rows.flatMap((r) => keys.map((k) => Math.max(1, r.results[k].relaxations)));
  const lo = Math.floor(Math.log10(Math.min(...all))), hi = Math.ceil(Math.log10(Math.max(...all)));
  const xs = rows.map((r) => r.n);
  const X = (n) => m.l + (Math.log(n) - Math.log(xs[0])) / (Math.log(xs[xs.length - 1]) - Math.log(xs[0])) * (w - m.l - m.r);
  const Y = (v) => m.t + (1 - (Math.log10(Math.max(1, v)) - lo) / (hi - lo)) * (h - m.t - m.b);
  let s = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Operations versus number of airports, log-log">`;
  for (let d = lo; d <= hi; d++) {
    s += `<line x1="${m.l}" x2="${w - m.r}" y1="${Y(10 ** d)}" y2="${Y(10 ** d)}" stroke="rgba(140,170,230,.15)"/><text x="${m.l - 8}" y="${Y(10 ** d) + 4}" text-anchor="end">${(10 ** d).toLocaleString()}</text>`;
  }
  xs.forEach((n) => { s += `<text x="${X(n)}" y="${h - m.b + 18}" text-anchor="middle">${n}</text>`; });
  s += `<text x="${(m.l + w - m.r) / 2}" y="${h - 8}" text-anchor="middle">Number of airports (V)</text>`;
  s += `<text transform="translate(14 ${h / 2}) rotate(-90)" text-anchor="middle">Steps for one query</text>`;
  keys.forEach((k) => {
    const pts = rows.map((r) => `${X(r.n)},${Y(r.results[k].relaxations)}`).join(" ");
    s += `<polyline points="${pts}" fill="none" stroke="${COLORS[k]}" stroke-width="2.4"/>`;
    rows.forEach((r) => { s += `<circle cx="${X(r.n)}" cy="${Y(r.results[k].relaxations)}" r="3" fill="${COLORS[k]}"/>`; });
  });
  // end-of-line labels, nudged apart so they never overlap
  const labels = keys.map((k) => ({ k, y: Y(rows[rows.length - 1].results[k].relaxations) })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
  labels.forEach((l) => { s += `<text x="${w - m.r + 8}" y="${l.y + 4}" style="fill:${COLORS[l.k]};font-weight:700">${NAMES[l.k]}</text>`; });
  $("#chart-wrap").innerHTML = s + "</svg>";
}

// ---------- wiring ----------
document.querySelectorAll(".seg button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
$("#run").addEventListener("click", run);
$("#swap").addEventListener("click", () => { const a = $("#src").value; $("#src").value = $("#dst").value; $("#dst").value = a; run(); });
["#src", "#dst", "#algo"].forEach((s) => $(s).addEventListener("change", run));
document.querySelectorAll("input[name=metric]").forEach((r) => r.addEventListener("change", run));
$("#bench").addEventListener("click", runBenchmark);
function showTab(name) {
  ["planner", "analysis"].forEach((t) => {
    $("#" + t).hidden = t !== name;
    $("#tab-" + t).setAttribute("aria-selected", t === name);
  });
}
$("#tab-planner").addEventListener("click", () => showTab("planner"));
$("#tab-analysis").addEventListener("click", () => showTab("analysis"));
init();
