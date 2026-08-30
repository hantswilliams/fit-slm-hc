// FIT-SLM-HC Decision Support Tool — Core Logic

(function () {
  "use strict";

  // ── State ──
  let state = { r: null, k: null, o: null, slmScore: null, refScore: null, metricName: "", arThreshold: 0.90, slmLatency: null, cloudLatency: null, leThreshold: 0.0 };

  // ── DOM refs ──
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  // ── Init ──
  document.addEventListener("DOMContentLoaded", () => {
    bindInputs();
    renderReferenceTable();
    renderScatterPlot();
    renderRadarChart();
    update();
  });

  // ── Input binding ──
  function bindInputs() {
    $$('input[name="r"], input[name="k"], input[name="o"]').forEach((el) => {
      el.addEventListener("change", () => { state[el.name] = parseInt(el.value); update(); });
    });
    $("#slm-score").addEventListener("input", (e) => { state.slmScore = parseFloat(e.target.value) || null; update(); });
    $("#ref-score").addEventListener("input", (e) => { state.refScore = parseFloat(e.target.value) || null; update(); });
    $("#metric-name").addEventListener("input", (e) => { state.metricName = e.target.value; update(); });
    $("#ar-threshold").addEventListener("input", (e) => {
      state.arThreshold = parseFloat(e.target.value);
      $("#ar-threshold-val").textContent = state.arThreshold.toFixed(2);
      update();
    });
    $("#slm-latency").addEventListener("input", (e) => { state.slmLatency = parseFloat(e.target.value) || null; update(); });
    $("#cloud-latency").addEventListener("input", (e) => { state.cloudLatency = parseFloat(e.target.value) || null; update(); });
    $("#le-threshold").addEventListener("input", (e) => {
      state.leThreshold = parseFloat(e.target.value);
      $("#le-threshold-val").textContent = state.leThreshold.toFixed(2);
      update();
    });
    $(".about-toggle").addEventListener("click", () => {
      $(".about-content").classList.toggle("open");
    });
  }

  // ── Compute ──
  function computeAR() {
    if (state.slmScore == null || state.refScore == null || state.refScore === 0) return null;
    return state.slmScore / state.refScore;
  }

  function computeLE() {
    if (state.slmLatency == null || state.cloudLatency == null || state.cloudLatency === 0) return null;
    return 1 - state.slmLatency / state.cloudLatency;
  }

  function axisSum() {
    if (state.r == null || state.k == null || state.o == null) return null;
    return state.r + state.k + state.o;
  }

  function getVerdict(ar, le) {
    const hasLE = le !== null;
    const arMet = ar >= state.arThreshold;
    const arBorderline = !arMet && ar >= state.arThreshold - 0.05;
    const leMet = !hasLE || le >= state.leThreshold;
    if (arMet && leMet) return "inside";
    if (arBorderline && leMet) return "borderline";
    return "outside";
  }

  // ── Main update ──
  function update() {
    updateAxisSum();
    updateARDisplay();
    updateLEDisplay();
    updateVerdict();
    updateRadarChart();
    updateScatterPlot();
  }

  function updateAxisSum() {
    const sum = axisSum();
    const el = $("#axis-sum");
    if (sum == null) {
      el.textContent = "Axis Sum: select all three axes";
      el.className = "axis-sum";
      return;
    }
    el.textContent = `Axis Sum: r + k + o = ${sum}`;
    el.className = "axis-sum " + (sum <= 5 ? "low" : sum <= 6 ? "mid" : "high");
  }

  function updateARDisplay() {
    const ar = computeAR();
    const el = $("#ar-value");
    if (ar == null) { el.textContent = "AR = \u2014"; return; }
    el.textContent = "AR = " + ar.toFixed(3);
  }

  function updateLEDisplay() {
    const le = computeLE();
    const el = $("#le-value");
    if (le == null) { el.textContent = "LE = \u2014"; return; }
    el.textContent = "LE = " + le.toFixed(3);
  }

  function updateVerdict() {
    const ar = computeAR();
    const le = computeLE();
    const sum = axisSum();
    const card = $("#verdict-card");
    const icon = $("#verdict-icon");
    const title = $("#verdict-title");
    const metricsEl = $("#verdict-metrics");
    const explanation = $("#verdict-explanation");

    if (ar == null) {
      card.className = "card verdict-card pending";
      icon.textContent = "\u2014";
      title.textContent = "Enter your scores to see the verdict";
      metricsEl.innerHTML = "";
      explanation.innerHTML = '<p>Complete Steps 1 and 2 to receive a deployment recommendation.</p>';
      return;
    }

    const verdict = getVerdict(ar, le);
    card.className = "card verdict-card " + verdict;

    if (verdict === "inside") {
      icon.textContent = "\uD83D\uDD35";
      title.textContent = "INSIDE the SLM Capability Envelope";
    } else if (verdict === "borderline") {
      icon.textContent = "\u26AA";
      title.textContent = "BORDERLINE \u2014 Review Recommended";
    } else {
      icon.textContent = "\uD83D\uDFE0";
      title.textContent = "OUTSIDE the SLM Capability Envelope";
    }

    // Metrics line
    let metricsHTML = `<div class="verdict-metric">AR: <strong>${ar.toFixed(3)}</strong> (threshold: ${state.arThreshold.toFixed(2)})</div>`;
    if (le !== null) {
      metricsHTML += `<div class="verdict-metric">LE: <strong>${le.toFixed(3)}</strong> (threshold: ${state.leThreshold.toFixed(2)})</div>`;
    }
    if (sum !== null) {
      metricsHTML += `<div class="verdict-metric">Axis sum: <strong>${sum}</strong> (${state.r},${state.k},${state.o})</div>`;
    }
    metricsEl.innerHTML = metricsHTML;

    // Explanation
    let explanationHTML = "";
    if (sum !== null) {
      if (sum <= 5) explanationHTML += `<p>${BAND_EXPLANATIONS.low}</p>`;
      else if (sum <= 6) explanationHTML += `<p>${BAND_EXPLANATIONS.mid}</p>`;
      else explanationHTML += `<p>${BAND_EXPLANATIONS.high}</p>`;
    }
    if (verdict === "inside" && sum !== null && sum <= 5) {
      explanationHTML += `<p>${CONTEXTUAL_NOTES.fineTuning}</p>`;
    }
    if (verdict === "outside" || verdict === "borderline") {
      explanationHTML += `<p>${CONTEXTUAL_NOTES.metricSensitivity}</p>`;
      explanationHTML += `<p>${CONTEXTUAL_NOTES.quantization}</p>`;
    }
    // Flag Likert-ordinal caveat whenever the user's output is non-deterministic
    // (templated or creative), since that's where Likert ratings most often appear.
    if (state.o !== null && state.o >= 2) {
      explanationHTML += `<p>${CONTEXTUAL_NOTES.likertCaveat}</p>`;
    }
    if (le === null) {
      explanationHTML += `<p>${CONTEXTUAL_NOTES.latencyGap}</p>`;
    }
    explanationHTML += `<p>${CONTEXTUAL_NOTES.referenceStandard}</p>`;
    explanationHTML += `<p><em>${CONTEXTUAL_NOTES.scope}</em></p>`;
    explanation.innerHTML = explanationHTML;
  }

  // ── Radar Chart ──
  const RADAR_SIZE = 260;
  const RADAR_CX = RADAR_SIZE / 2;
  const RADAR_CY = RADAR_SIZE / 2;
  const RADAR_R = 100;
  const AXES = [
    { label: "Reasoning (r)", angle: -Math.PI / 2 },
    { label: "Knowledge (k)", angle: -Math.PI / 2 + (2 * Math.PI) / 3 },
    { label: "Output (o)", angle: -Math.PI / 2 + (4 * Math.PI) / 3 },
  ];

  function radarPoint(level, axisIndex) {
    const a = AXES[axisIndex].angle;
    const r = (level / 3) * RADAR_R;
    return [RADAR_CX + r * Math.cos(a), RADAR_CY + r * Math.sin(a)];
  }

  function renderRadarChart() {
    const svg = $("#radar-svg");
    svg.setAttribute("viewBox", `0 0 ${RADAR_SIZE} ${RADAR_SIZE}`);
    let html = "";

    // Zone fills (concentric triangles) — neutral palette: orange = cloud,
    // gray = borderline, blue = SLM (matches manuscript Figure 1)
    const zones = [
      { level: 3, fill: "#F8CDB0", opacity: 0.4 },
      { level: 2, fill: "#E7E7E3", opacity: 0.5 },
      { level: 1, fill: "#B9D5F2", opacity: 0.6 },
    ];
    for (const z of zones) {
      const pts = [0, 1, 2].map((i) => radarPoint(z.level, i).join(",")).join(" ");
      html += `<polygon points="${pts}" fill="${z.fill}" opacity="${z.opacity}" stroke="none"/>`;
    }

    // Grid lines
    for (let lvl = 1; lvl <= 3; lvl++) {
      const pts = [0, 1, 2].map((i) => radarPoint(lvl, i).join(",")).join(" ");
      html += `<polygon points="${pts}" fill="none" stroke="#bbb" stroke-width="0.8" stroke-dasharray="${lvl < 3 ? '3,3' : 'none'}"/>`;
    }

    // Axis lines
    for (let i = 0; i < 3; i++) {
      const [ex, ey] = radarPoint(3, i);
      html += `<line x1="${RADAR_CX}" y1="${RADAR_CY}" x2="${ex}" y2="${ey}" stroke="#999" stroke-width="0.8"/>`;
    }

    // Axis labels
    for (let i = 0; i < 3; i++) {
      const [lx, ly] = radarPoint(3.45, i);
      const anchor = i === 0 ? "middle" : i === 1 ? "start" : "end";
      html += `<text x="${lx}" y="${ly}" text-anchor="${anchor}" font-size="10" fill="#555">${AXES[i].label}</text>`;
    }

    // Level numbers
    for (let lvl = 1; lvl <= 3; lvl++) {
      const [px, py] = radarPoint(lvl, 0);
      html += `<text x="${px + 8}" y="${py + 3}" font-size="9" fill="#999">${lvl}</text>`;
    }

    // Placeholder for user polygon (dark neutral so it reads as "your task",
    // not as either zone identity)
    html += '<polygon id="radar-user" points="" fill="rgba(26,26,46,0.22)" stroke="#1a1a2e" stroke-width="2"/>';

    svg.innerHTML = html;
  }

  function updateRadarChart() {
    const poly = $("#radar-user");
    if (!poly) return;
    if (state.r == null || state.k == null || state.o == null) {
      poly.setAttribute("points", "");
      return;
    }
    const pts = [
      radarPoint(state.r, 0),
      radarPoint(state.k, 1),
      radarPoint(state.o, 2),
    ].map((p) => p.join(",")).join(" ");
    poly.setAttribute("points", pts);
  }

  // ── Scatter Plot ──
  const SP = { w: 600, h: 360, ml: 50, mr: 20, mt: 20, mb: 40 };
  const SP_X_MIN = 2.5, SP_X_MAX = 9.5;
  const SP_Y_MIN = 0.55, SP_Y_MAX = 1.80;

  function spX(sum) { return SP.ml + ((sum - SP_X_MIN) / (SP_X_MAX - SP_X_MIN)) * (SP.w - SP.ml - SP.mr); }
  function spY(ar) { return SP.mt + ((SP_Y_MAX - ar) / (SP_Y_MAX - SP_Y_MIN)) * (SP.h - SP.mt - SP.mb); }

  function renderScatterPlot() {
    const svg = $("#scatter-svg");
    svg.setAttribute("viewBox", `0 0 ${SP.w} ${SP.h}`);
    let html = "";

    // Background
    html += `<rect x="${SP.ml}" y="${SP.mt}" width="${SP.w - SP.ml - SP.mr}" height="${SP.h - SP.mt - SP.mb}" fill="#fafafa" stroke="#ddd"/>`;

    // Grid lines
    for (let s = 3; s <= 9; s++) {
      const x = spX(s);
      html += `<line x1="${x}" y1="${SP.mt}" x2="${x}" y2="${SP.h - SP.mb}" stroke="#eee" stroke-width="1"/>`;
      html += `<text x="${x}" y="${SP.h - SP.mb + 14}" text-anchor="middle" font-size="11" fill="#888">${s}</text>`;
    }
    for (let ar = 0.6; ar <= 1.8; ar += 0.2) {
      const y = spY(ar);
      html += `<line x1="${SP.ml}" y1="${y}" x2="${SP.w - SP.mr}" y2="${y}" stroke="#eee" stroke-width="1"/>`;
      html += `<text x="${SP.ml - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="#888">${ar.toFixed(1)}</text>`;
    }

    // AR=1.0 reference line
    const y1ref = spY(1.0);
    html += `<line x1="${SP.ml}" y1="${y1ref}" x2="${SP.w - SP.mr}" y2="${y1ref}" stroke="#aaa" stroke-width="1" stroke-dasharray="4,3"/>`;
    html += `<text x="${SP.w - SP.mr - 2}" y="${y1ref - 4}" text-anchor="end" font-size="9" fill="#aaa">AR = 1.0</text>`;

    // Default threshold line (will be updated) — neutral ink: the threshold
    // is a governance setting, not a property of either zone
    html += `<line id="scatter-threshold" x1="${SP.ml}" y1="${spY(0.90)}" x2="${SP.w - SP.mr}" y2="${spY(0.90)}" stroke="#55534e" stroke-width="1.5" stroke-dasharray="6,4"/>`;
    html += `<text id="scatter-threshold-label" x="${SP.ml + 4}" y="${spY(0.90) - 5}" font-size="9" fill="#55534e">AR threshold = 0.90</text>`;

    // Axis labels
    html += `<text x="${SP.w / 2}" y="${SP.h - 4}" text-anchor="middle" font-size="11" fill="#555">Axis Sum (r + k + o)</text>`;
    html += `<text x="14" y="${SP.h / 2}" text-anchor="middle" font-size="11" fill="#555" transform="rotate(-90, 14, ${SP.h / 2})">Accuracy Ratio (AR)</text>`;

    // Manuscript task dots
    for (let i = 0; i < MANUSCRIPT_TASKS.length; i++) {
      const t = MANUSCRIPT_TASKS[i];
      const sum = t.r + t.k + t.o;
      const cx = spX(sum + jitter(i));
      const cy = spY(t.ar);
      const color = t.envelope ? "#2a78d6" : "#eb6834";
      const r = t.vignette ? 7 : 5;
      const strokeW = t.vignette ? 2 : 1.2;
      const strokeColor = t.vignette ? "#000" : color;
      html += `<circle class="task-dot" data-idx="${i}" cx="${cx}" cy="${cy}" r="${r}" fill="${color}" fill-opacity="0.7" stroke="${strokeColor}" stroke-width="${strokeW}" style="cursor:pointer"/>`;
    }

    // User marker placeholder
    html += '<g id="scatter-user" style="display:none"><polygon points="0,-10 8.66,5 -8.66,5" fill="#1a1a2e" stroke="#000" stroke-width="2"/></g>';

    svg.innerHTML = html;

    // Tooltip events
    const tooltip = $("#scatter-tooltip");
    svg.querySelectorAll(".task-dot").forEach((dot) => {
      dot.addEventListener("mouseenter", (e) => {
        const t = MANUSCRIPT_TASKS[parseInt(dot.dataset.idx)];
        const sum = t.r + t.k + t.o;
        tooltip.innerHTML = `<strong>${t.task}</strong><br>Source: ${t.source}${t.vignette ? " (Vignette " + t.vignette + ")" : ""}<br>SLM: ${t.slm} vs ${t.ref}<br>(r,k,o) = (${t.r},${t.k},${t.o}) \u2192 sum = ${sum}<br>Metric: ${t.metric}<br>AR = ${t.ar.toFixed(2)}${t.le != null ? " | LE = " + t.le.toFixed(2) : ""}<br>${t.envelope ? "\uD83D\uDD35 Inside envelope" : "\uD83D\uDFE0 Outside envelope"}`;
        tooltip.style.display = "block";
      });
      dot.addEventListener("mousemove", (e) => {
        const rect = svg.closest(".chart-scatter").getBoundingClientRect();
        tooltip.style.left = (e.clientX - rect.left + 12) + "px";
        tooltip.style.top = (e.clientY - rect.top - 10) + "px";
      });
      dot.addEventListener("mouseleave", () => { tooltip.style.display = "none"; });
    });
  }

  function jitter(idx) {
    // Deterministic small jitter to separate overlapping dots
    return ((idx * 7 + 3) % 11 - 5) * 0.06;
  }

  function updateScatterPlot() {
    // Update threshold line
    const thLine = $("#scatter-threshold");
    const thLabel = $("#scatter-threshold-label");
    if (thLine) {
      const y = spY(state.arThreshold);
      thLine.setAttribute("y1", y);
      thLine.setAttribute("y2", y);
      thLabel.setAttribute("y", y - 5);
      thLabel.textContent = `AR threshold = ${state.arThreshold.toFixed(2)}`;
    }

    // Update user marker
    const userG = $("#scatter-user");
    if (!userG) return;
    const ar = computeAR();
    const sum = axisSum();
    if (ar == null || sum == null) {
      userG.style.display = "none";
      return;
    }
    userG.style.display = "block";
    const cx = spX(sum);
    const cy = spY(Math.min(Math.max(ar, SP_Y_MIN), SP_Y_MAX));
    userG.setAttribute("transform", `translate(${cx}, ${cy})`);
  }

  // ── Reference Table ──
  let sortCol = null;
  let sortAsc = true;

  function renderReferenceTable() {
    const tbody = $("#ref-tbody");
    const data = getSortedData();
    tbody.innerHTML = data.map((t) => {
      const sum = t.r + t.k + t.o;
      const taskCell = t.note
        ? `<td title="${t.note.replace(/"/g, "&quot;")}">${t.task} <span class="note-marker" aria-label="note">&#9432;</span></td>`
        : `<td>${t.task}</td>`;
      return `<tr class="${t.envelope ? "envelope-yes" : "envelope-no"}">
        ${taskCell}<td>${t.source}</td><td>${t.slm}</td><td>${t.ref}</td>
        <td>(${t.r},${t.k},${t.o})</td><td>${sum}</td><td>${t.metric}</td>
        <td>${fmtScore(t.slmScore)}</td><td>${fmtScore(t.refScore)}</td>
        <td>${t.ar.toFixed(2)}</td><td>${t.le != null ? t.le.toFixed(2) : "NR"}</td>
        <td>${t.envelope ? "\uD83D\uDD35 In" : "\uD83D\uDFE0 Out"}</td></tr>`;
    }).join("");

    // Sort headers
    $$(".ref-table th").forEach((th) => {
      th.addEventListener("click", () => {
        const col = th.dataset.col;
        if (sortCol === col) sortAsc = !sortAsc;
        else { sortCol = col; sortAsc = true; }
        renderReferenceTable();
      });
    });
  }

  function getSortedData() {
    const data = [...MANUSCRIPT_TASKS];
    if (!sortCol) return data;
    data.sort((a, b) => {
      let va, vb;
      switch (sortCol) {
        case "task": va = a.task; vb = b.task; break;
        case "source": va = a.source; vb = b.source; break;
        case "sum": va = a.r + a.k + a.o; vb = b.r + b.k + b.o; break;
        case "ar": va = a.ar; vb = b.ar; break;
        case "le": va = a.le ?? -99; vb = b.le ?? -99; break;
        case "env": va = a.envelope ? 1 : 0; vb = b.envelope ? 1 : 0; break;
        default: return 0;
      }
      if (typeof va === "string") return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      return sortAsc ? va - vb : vb - va;
    });
    return data;
  }

  function fmtScore(v) {
    if (v == null) return "\u2014";
    return v % 1 === 0 ? v.toString() : v < 1 ? v.toFixed(3) : v.toFixed(1);
  }
})();
