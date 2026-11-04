"""Self-contained SiteSentry web dashboard."""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>SiteSentry | Security Dashboard</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0a1018;
  --panel: #101a26;
  --panel-2: #142130;
  --line: #223345;
  --text: #edf4fa;
  --muted: #91a4b7;
  --accent: #58d6ad;
  --accent-2: #83e3c3;
  --blue: #81b8fa;
  --red: #ff7f87;
  --amber: #f3c56c;
  --shadow: 0 18px 50px rgba(0,0,0,.2);
}
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; color: var(--text);
  background:
    radial-gradient(ellipse at 20% -10%, rgba(48,112,117,.18), transparent 34rem),
    radial-gradient(ellipse at 100% 0%, rgba(56,98,145,.13), transparent 36rem),
    var(--bg);
  font: 15px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button, input, select { font: inherit; }
button { cursor: pointer; }
a { color: var(--accent-2); }
.shell { max-width: 1440px; margin: 0 auto; padding: 30px 34px 60px; }
.topbar { display:flex; align-items:center; justify-content:space-between; gap:20px; padding-bottom:28px; border-bottom:1px solid rgba(145,164,183,.16); }
.brand { display:flex; align-items:center; gap:12px; font-weight:750; letter-spacing:.02em; font-size:18px; }
.brand-mark { display:grid; place-items:center; width:40px; height:40px; border-radius:13px; color:#071511; background:linear-gradient(145deg,#8aebcb,#39b993); box-shadow:0 8px 25px rgba(68,204,160,.2); }
.brand-mark svg { width:23px; height:23px; }
.brand small { display:block; color:var(--muted); font-size:10px; letter-spacing:.19em; font-weight:650; margin-top:-2px; }
.top-actions { display:flex; align-items:center; gap:12px; color:var(--muted); font-size:12px; }
.pill { display:inline-flex; align-items:center; gap:7px; border:1px solid var(--line); border-radius:999px; padding:7px 11px; background:rgba(16,26,38,.7); }
.dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 4px rgba(88,214,173,.1); }
.hero { display:flex; align-items:flex-end; justify-content:space-between; gap:24px; padding:34px 0 25px; }
.eyebrow { color:var(--accent); font-size:10px; font-weight:800; letter-spacing:.2em; text-transform:uppercase; }
h1 { font-size:clamp(28px,4vw,42px); line-height:1.12; letter-spacing:-.04em; margin:9px 0 10px; }
.hero p { max-width:670px; color:var(--muted); margin:0; }
.hero-note { max-width:245px; color:var(--muted); font-size:12px; border-left:2px solid #3e806f; padding-left:14px; }
.layout { display:grid; grid-template-columns:minmax(0,1.7fr) minmax(290px,.85fr); gap:20px; align-items:start; }
.main-column,.side-column { display:grid; gap:20px; min-width:0; }
.panel { background:linear-gradient(160deg,rgba(20,33,48,.96),rgba(14,23,34,.97)); border:1px solid var(--line); border-radius:17px; box-shadow:var(--shadow); overflow:hidden; }
.panel-head { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:19px 21px; border-bottom:1px solid rgba(145,164,183,.13); }
.panel-head h2 { font-size:15px; margin:0; letter-spacing:-.01em; }
.panel-head p { font-size:12px; color:var(--muted); margin:3px 0 0; }
.panel-body { padding:21px; }
.section-tag { color:var(--muted); font-size:10px; font-weight:750; letter-spacing:.16em; text-transform:uppercase; }
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:17px; }
.field { display:grid; gap:7px; min-width:0; }
.field.full { grid-column:1/-1; }
label { color:#c4d1de; font-size:12px; font-weight:650; }
input[type=url],input[type=password],input[type=number],select {
  width:100%; min-width:0; border:1px solid #2b4054; color:var(--text); background:#0b1520; border-radius:10px; padding:12px 13px; outline:none; transition:border .15s,box-shadow .15s;
}
input:focus,select:focus { border-color:#55bd9e; box-shadow:0 0 0 3px rgba(85,189,158,.12); }
input::placeholder { color:#5f7182; }
.field-hint { color:var(--muted); font-size:11px; }
.consent { display:flex; align-items:flex-start; gap:10px; padding:12px 13px; border:1px solid #294238; background:rgba(51,113,88,.10); border-radius:11px; color:#c1d8d0; font-size:12px; }
.consent input { margin-top:3px; accent-color:var(--accent); }
.actions { display:flex; align-items:center; gap:12px; margin-top:17px; flex-wrap:wrap; }
.primary { border:0; border-radius:10px; padding:12px 17px; color:#071711; background:linear-gradient(135deg,#88e8c6,#4cc39c); font-weight:800; box-shadow:0 8px 20px rgba(65,191,148,.16); }
.primary:hover { filter:brightness(1.06); transform:translateY(-1px); }
.primary:disabled { opacity:.6; cursor:wait; transform:none; }
.subtle { color:var(--muted); font-size:11px; }
.status-banner { display:none; align-items:center; gap:10px; margin-top:16px; padding:12px 14px; border:1px solid var(--line); border-radius:10px; background:#0c1722; color:#c6d5e2; font-size:12px; }
.status-banner.visible { display:flex; }
.status-banner.error { border-color:rgba(255,127,135,.35); color:#ffc0c4; }
.status-banner.success { border-color:rgba(88,214,173,.3); color:#b5f2da; }
.spinner { width:14px; height:14px; border:2px solid rgba(145,164,183,.3); border-top-color:var(--accent); border-radius:50%; animation:spin .8s linear infinite; flex:none; }
@keyframes spin { to { transform:rotate(360deg); } }
.stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
.stat { background:rgba(15,25,37,.9); border:1px solid var(--line); border-radius:13px; padding:15px; min-width:0; }
.stat-label { color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.12em; font-weight:750; }
.stat-value { font-size:25px; font-weight:800; letter-spacing:-.04em; margin-top:6px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stat-sub { color:var(--muted); font-size:10px; margin-top:2px; }
.result-empty { display:grid; place-items:center; text-align:center; min-height:200px; padding:30px; color:var(--muted); }
.empty-icon { display:grid; place-items:center; width:48px; height:48px; border-radius:15px; background:rgba(88,214,173,.09); color:var(--accent); margin-bottom:12px; }
.empty-icon svg { width:24px; }
.result-top { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.grade-wrap { display:flex; align-items:center; gap:13px; }
.grade { display:grid; place-items:center; width:58px; height:58px; border-radius:16px; background:#0b1722; border:1px solid var(--line); font-size:29px; font-weight:850; }
.grade.good { color:var(--accent); border-color:rgba(88,214,173,.4); }
.grade.warn { color:var(--amber); border-color:rgba(243,197,108,.4); }
.grade.bad { color:var(--red); border-color:rgba(255,127,135,.4); }
.result-title { font-weight:750; font-size:15px; }
.result-meta { color:var(--muted); font-size:11px; margin-top:3px; overflow-wrap:anywhere; }
.score-track { height:7px; border-radius:99px; background:#263849; overflow:hidden; margin-top:17px; }
.score-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,#35ad88,#8ce2bc); width:0%; transition:width .3s; }
.report-actions { display:flex; gap:8px; flex-wrap:wrap; margin-top:17px; }
.report-btn { border:1px solid #2b4054; border-radius:8px; padding:8px 11px; color:#c6d5e2; background:#0d1925; font-size:11px; font-weight:700; }
.report-btn:hover { border-color:#5aa88f; color:var(--accent-2); }
.subsection { margin-top:23px; }
.subsection-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:11px; }
.subsection-head h3 { margin:0; font-size:13px; }
.count { color:var(--muted); font-size:11px; }
.severity-row { display:flex; gap:7px; flex-wrap:wrap; margin-bottom:13px; }
.sev-count { font-size:10px; border:1px solid var(--line); border-radius:999px; padding:5px 9px; color:var(--muted); }
.sev-count.high,.severity.high,.severity.critical { color:#ffadb2; border-color:rgba(255,127,135,.32); background:rgba(255,127,135,.08); }
.sev-count.medium,.severity.medium { color:#f3cd83; border-color:rgba(243,197,108,.3); background:rgba(243,197,108,.07); }
.sev-count.low,.severity.low { color:#a9c9f4; border-color:rgba(129,184,250,.25); background:rgba(129,184,250,.07); }
.sev-count.info,.severity.info { color:#a7b6c5; }
.finding-list { display:grid; gap:10px; }
.finding { border:1px solid var(--line); border-radius:12px; background:rgba(9,18,28,.55); overflow:hidden; }
.finding-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding:13px 14px; }
.finding-title { font-size:12px; font-weight:750; overflow-wrap:anywhere; }
.finding-id { font-size:10px; color:var(--muted); margin-top:3px; }
.severity { flex:none; padding:4px 7px; border:1px solid var(--line); border-radius:6px; font-size:9px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; }
.finding-body { border-top:1px solid rgba(145,164,183,.12); padding:12px 14px; display:grid; gap:10px; }
.detail-label { color:var(--muted); text-transform:uppercase; font-size:9px; letter-spacing:.13em; font-weight:800; margin-bottom:2px; }
.detail-value { color:#cbd8e3; font-size:11px; overflow-wrap:anywhere; white-space:pre-wrap; }
.fix-value { color:#b9e8d5; }
.breakdown { width:100%; border-collapse:collapse; font-size:11px; }
.breakdown th { color:var(--muted); font-size:9px; letter-spacing:.12em; text-transform:uppercase; text-align:left; padding:9px 8px; border-bottom:1px solid var(--line); }
.breakdown td { color:#cbd8e3; padding:9px 8px; border-bottom:1px solid rgba(145,164,183,.1); }
.breakdown td:last-child,.breakdown th:last-child { text-align:right; }
.history-list { display:grid; gap:7px; }
.history-item { display:flex; align-items:center; gap:10px; width:100%; text-align:left; padding:10px; border:1px solid transparent; border-radius:10px; background:rgba(8,16,25,.48); color:var(--text); }
.history-item:hover,.history-item.active { border-color:#35566b; background:rgba(63,111,126,.13); }
.history-grade { display:grid; place-items:center; flex:none; width:33px; height:33px; border-radius:9px; background:#162637; color:var(--accent-2); font-weight:800; }
.history-text { min-width:0; flex:1; }
.history-url { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:11px; font-weight:700; }
.history-date { color:var(--muted); font-size:10px; }
.history-score { color:#d8e4ec; font-weight:750; font-size:11px; }
.history-empty { color:var(--muted); font-size:12px; padding:12px 4px; }
.history-footer { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-top:12px; color:var(--muted); font-size:10px; }
.text-button { background:transparent; border:0; color:var(--accent-2); padding:0; font-size:11px; font-weight:700; }
.api-docs { display:flex; align-items:center; justify-content:space-between; gap:12px; color:var(--muted); font-size:11px; }
.api-docs a { text-decoration:none; font-weight:700; }
.footer { text-align:center; color:#64788a; font-size:10px; padding-top:28px; }
@media (max-width: 980px) { .layout { grid-template-columns:1fr; } .side-column { grid-template-columns:1fr 1fr; } }
@media (max-width: 650px) {
  .shell { padding:18px 14px 40px; } .topbar { align-items:flex-start; } .top-actions .pill:last-child { display:none; }
  .hero { display:block; padding-top:27px; } .hero-note { margin-top:18px; }
  .stats { grid-template-columns:repeat(2,minmax(0,1fr)); } .form-grid { grid-template-columns:1fr; }
  .field.full { grid-column:auto; } .side-column { grid-template-columns:1fr; }
  .panel-head,.panel-body { padding-left:15px; padding-right:15px; }
}
@media (prefers-reduced-motion: reduce) { *,*::before,*::after { animation-duration:.01ms !important; transition-duration:.01ms !important; } }
</style>
</head>
<body>
<div class="shell">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg>
      </div>
      <div>SiteSentry<small>WEB SECURITY CONSOLE</small></div>
    </div>
    <div class="top-actions">
      <span class="pill"><span class="dot"></span> Passive scan mode</span>
      <span class="pill">Local dashboard</span>
    </div>
  </header>

  <section class="hero">
    <div>
      <div class="eyebrow">Security operations / workspace</div>
      <h1>Website security,<br>at a glance.</h1>
      <p>Run a passive security assessment, review evidence-backed findings and keep an eye on the security posture of websites you manage.</p>
    </div>
    <div class="hero-note">Built for authorized assessments. SiteSentry checks configuration and exposure without sending exploit payloads.</div>
  </section>

  <div class="layout">
    <main class="main-column">
      <section class="panel" id="new-scan">
        <div class="panel-head">
          <div><h2>Start a security scan</h2><p>Choose a target and configure a bounded crawl.</p></div>
          <span class="section-tag">New assessment</span>
        </div>
        <div class="panel-body">
          <form id="scan-form">
            <div class="field">
              <label for="target-url">Website URL</label>
              <input id="target-url" name="url" type="url" placeholder="https://yourwebsite.com" autocomplete="url" required>
              <span class="field-hint">Enter the exact website origin you are authorized to assess.</span>
            </div>
            <div class="form-grid">
              <div class="field">
                <label for="max-pages">Maximum pages</label>
                <input id="max-pages" name="max_pages" type="number" min="1" max="500" value="50" required>
              </div>
              <div class="field">
                <label for="max-depth">Crawl depth</label>
                <input id="max-depth" name="max_depth" type="number" min="1" max="10" value="2" required>
              </div>
              <div class="field full">
                <label for="api-key">API key <span class="field-hint">(only if you configured one)</span></label>
                <input id="api-key" type="password" placeholder="Optional Bearer token" autocomplete="off">
              </div>
            </div>
            <label class="consent" style="margin-top:15px">
              <input id="permission" type="checkbox" required>
              <span>I own this website or have explicit authorization to assess it. I understand the scan makes HTTP requests to the target.</span>
            </label>
            <div class="actions">
              <button class="primary" id="scan-button" type="submit">Start security scan</button>
              <span class="subtle">Default limits: 2 requests/sec · 1 MB response cap</span>
            </div>
          </form>
          <div class="status-banner" id="status-banner" role="status" aria-live="polite"><span id="status-text"></span></div>
        </div>
      </section>

      <section class="stats" aria-label="Selected scan statistics">
        <div class="stat"><div class="stat-label">Security score</div><div class="stat-value" id="stat-score">—</div><div class="stat-sub">Out of 100</div></div>
        <div class="stat"><div class="stat-label">Grade</div><div class="stat-value" id="stat-grade">—</div><div class="stat-sub">A through F</div></div>
        <div class="stat"><div class="stat-label">Pages scanned</div><div class="stat-value" id="stat-pages">—</div><div class="stat-sub">Crawl result</div></div>
        <div class="stat"><div class="stat-label">Findings</div><div class="stat-value" id="stat-findings">—</div><div class="stat-sub">Detected issues</div></div>
      </section>

      <section class="panel" id="results-panel">
        <div class="panel-head">
          <div><h2>Assessment results</h2><p id="result-subtitle">Select a scan from history or start a new assessment.</p></div>
          <span class="section-tag" id="result-state">No scan selected</span>
        </div>
        <div class="panel-body" id="result-content">
          <div class="result-empty">
            <div><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="M9 12h6M12 9v6"/></svg></div><strong>No assessment selected</strong><div style="font-size:12px;margin-top:5px">Start a scan to see its security score, findings and remediation guidance here.</div></div>
          </div>
        </div>
      </section>
    </main>

    <aside class="side-column">
      <section class="panel">
        <div class="panel-head"><div><h2>Scan history</h2><p>Your latest saved assessments.</p></div><button class="text-button" id="refresh-history" type="button">Refresh</button></div>
        <div class="panel-body">
          <div class="history-list" id="history-list"><div class="history-empty">Loading scan history…</div></div>
          <div class="history-footer"><span id="history-count">—</span><span>Most recent first</span></div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-head"><div><h2>Scanner configuration</h2><p>Safe defaults are applied to every scan.</p></div></div>
        <div class="panel-body">
          <div class="history-list">
            <div class="history-item"><span class="history-grade">16</span><div class="history-text"><span class="history-url">Passive security checks</span><span class="history-date">Headers, cookies, TLS, CORS and more</span></div></div>
            <div class="history-item"><span class="history-grade">2/s</span><div class="history-text"><span class="history-url">Polite request rate</span><span class="history-date">Configurable scan pacing</span></div></div>
            <div class="history-item"><span class="history-grade">1 MB</span><div class="history-text"><span class="history-url">Response size cap</span><span class="history-date">Limits response memory use</span></div></div>
            <div class="history-item"><span class="history-grade">SSR</span><div class="history-text"><span class="history-url">Scope and SSRF guard</span><span class="history-date">Restricts target and address scope</span></div></div>
          </div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-body api-docs"><span>Need the API directly?</span><a href="/docs" target="_blank" rel="noreferrer">Open API docs ↗</a></div>
      </section>
    </aside>
  </div>
  <footer class="footer">SITESENTRY · PASSIVE WEB SECURITY ASSESSMENT · ONLY SCAN AUTHORIZED ASSETS</footer>
</div>

<script>
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const state = { selectedId: null, pollTimer: null, pollGeneration: 0 };
  const apiKeyInput = $("api-key");

  function node(tag, className, text) {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text !== undefined && text !== null) item.textContent = String(text);
    return item;
  }

  function setBanner(message, kind) {
    const banner = $("status-banner");
    banner.className = "status-banner visible" + (kind ? " " + kind : "");
    banner.replaceChildren();
    if (kind === "loading") banner.append(node("span", "spinner"));
    banner.append(node("span", "", message));
  }

  function clearBanner() {
    $("status-banner").className = "status-banner";
    $("status-banner").replaceChildren();
  }

  async function api(path, options) {
    const config = options || {};
    const headers = new Headers(config.headers || {});
    const key = apiKeyInput.value.trim();
    if (key) headers.set("Authorization", "Bearer " + key);
    if (config.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const response = await fetch(path, { ...config, headers });
    if (!response.ok) {
      let message = "Request failed (" + response.status + ")";
      try {
        const body = await response.json();
        message = body.detail || body.message || body.title || message;
        if (typeof message === "object") message = JSON.stringify(message);
      } catch (_) { /* Keep status-based message. */ }
      throw new Error(message);
    }
    return response;
  }

  function stopPolling() {
    state.pollGeneration += 1;
    if (state.pollTimer) window.clearTimeout(state.pollTimer);
    state.pollTimer = null;
  }

  function dateText(value) {
    if (!value) return "Date unavailable";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
  }

  function statusText(value) {
    const labels = { pending: "Queued", running: "Scanning", completed: "Completed", failed: "Failed" };
    return labels[value] || value || "Unknown";
  }

  function gradeClass(grade) {
    if (grade === "A" || grade === "B") return "good";
    if (grade === "C") return "warn";
    if (grade === "D" || grade === "F") return "bad";
    return "";
  }

  function updateStats(data) {
    $("stat-score").textContent = data.status === "completed" ? String(data.score) : "—";
    $("stat-grade").textContent = data.status === "completed" ? (data.grade || "—") : "—";
    $("stat-pages").textContent = data.status === "completed" ? String(data.page_count || 0) : "—";
    $("stat-findings").textContent = data.status === "completed" ? String((data.results || []).reduce((sum, check) => sum + (check.findings || []).length, 0)) : "—";
  }

  function addDetail(parent, label, value, extraClass) {
    if (value === undefined || value === null || value === "") return;
    const wrapper = node("div");
    wrapper.append(node("div", "detail-label", label));
    wrapper.append(node("div", "detail-value" + (extraClass ? " " + extraClass : ""), value));
    parent.append(wrapper);
  }

  function renderFindings(findings) {
    const list = node("div", "finding-list");
    const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    findings.forEach((finding) => { counts[finding.severity] = (counts[finding.severity] || 0) + 1; });
    const chips = node("div", "severity-row");
    Object.keys(counts).forEach((severity) => {
      if (counts[severity]) chips.append(node("span", "sev-count " + severity, severity.toUpperCase() + " " + counts[severity]));
    });
    if (chips.childNodes.length) list.append(chips);

    findings.forEach((finding) => {
      const card = node("article", "finding");
      const head = node("div", "finding-head");
      const titleWrap = node("div");
      titleWrap.append(node("div", "finding-title", finding.title || "Security finding"));
      titleWrap.append(node("div", "finding-id", (finding.check_id || "check") + " · " + (finding.url || "")));
      head.append(titleWrap);
      head.append(node("span", "severity " + (finding.severity || "info"), finding.severity || "info"));
      card.append(head);
      const body = node("div", "finding-body");
      addDetail(body, "Evidence", finding.evidence);
      addDetail(body, "Why it matters", finding.explanation);
      addDetail(body, "Recommended fix", finding.fix, "fix-value");
      card.append(body);
      list.append(card);
    });
    if (!findings.length) list.append(node("div", "history-empty", "No findings were returned by the checks."));
    return list;
  }

  function renderBreakdown(rows) {
    const wrapper = node("div");
    const table = node("table", "breakdown");
    const thead = node("thead");
    const header = node("tr");
    ["Security check", "Findings", "Deduction"].forEach((label) => header.append(node("th", "", label)));
    thead.append(header);
    table.append(thead);
    const tbody = node("tbody");
    (rows || []).forEach((row) => {
      const tr = node("tr");
      tr.append(node("td", "", row.check_title || row.check_id));
      tr.append(node("td", "", row.finding_count));
      tr.append(node("td", "", "-" + row.capped_deduction));
      tbody.append(tr);
    });
    table.append(tbody);
    wrapper.append(table);
    return wrapper;
  }

  function renderResult(data) {
    state.selectedId = data.scan_id;
    updateStats(data);
    $("result-subtitle").textContent = data.target_url || "Scan details";
    $("result-state").textContent = statusText(data.status);
    const content = $("result-content");
    content.replaceChildren();

    const top = node("div", "result-top");
    const gradeWrap = node("div", "grade-wrap");
    const grade = node("div", "grade " + gradeClass(data.grade), data.status === "completed" ? (data.grade || "—") : "…");
    gradeWrap.append(grade);
    const titleBlock = node("div");
    titleBlock.append(node("div", "result-title", data.status === "completed" ? "Security assessment complete" : "Assessment " + statusText(data.status).toLowerCase()));
    titleBlock.append(node("div", "result-meta", data.target_url || ""));
    titleBlock.append(node("div", "result-meta", "Scan ID: " + (data.scan_id || "")));
    gradeWrap.append(titleBlock);
    top.append(gradeWrap);
    top.append(node("span", "pill", statusText(data.status)));
    content.append(top);

    const track = node("div", "score-track");
    const fill = node("div", "score-fill");
    fill.style.width = (data.status === "completed" ? Math.max(0, Math.min(100, Number(data.score) || 0)) : 0) + "%";
    track.append(fill);
    content.append(track);

    if (data.status === "pending" || data.status === "running") {
      const message = node("div", "status-banner visible");
      message.append(node("span", "spinner"));
      message.append(node("span", "", data.status === "pending" ? "Waiting for an available scan worker…" : "The scanner is crawling the target and running its passive checks. This page will update automatically."));
      content.append(message);
      return;
    }
    if (data.status === "failed") {
      const message = node("div", "status-banner visible error", "This scan failed. Check the API server logs for the underlying error.");
      content.append(message);
      (data.errors || []).forEach((error) => addDetail(content, "Scan error", error));
      return;
    }

    const actions = node("div", "report-actions");
    [["html","HTML"],["md","Markdown"],["json","JSON"],["sarif","SARIF"]].forEach(([format,label]) => {
      const button = node("button", "report-btn", "Download " + label);
      button.type = "button";
      button.addEventListener("click", () => downloadReport(data.scan_id, format, button));
      actions.append(button);
    });
    content.append(actions);

    const findings = (data.results || []).flatMap((check) => check.findings || []);
    const findingSection = node("section", "subsection");
    const findingHead = node("div", "subsection-head");
    findingHead.append(node("h3", "", "Security findings"));
    findingHead.append(node("span", "count", findings.length + " total"));
    findingSection.append(findingHead);
    findingSection.append(renderFindings(findings));
    content.append(findingSection);

    const breakdownSection = node("section", "subsection");
    const breakdownHead = node("div", "subsection-head");
    breakdownHead.append(node("h3", "", "Check-by-check score"));
    breakdownSection.append(breakdownHead);
    breakdownSection.append(renderBreakdown(data.breakdown));
    content.append(breakdownSection);

    if (data.has_incomplete_checks) {
      content.append(node("div", "status-banner visible error", "Some checks did not complete. Review the scan's check results before relying on its grade."));
    }
  }

  async function downloadReport(scanId, format, button) {
    const previous = button.textContent;
    button.disabled = true;
    button.textContent = "Preparing…";
    try {
      const response = await api("/api/v1/scans/" + encodeURIComponent(scanId) + "/report?format=" + encodeURIComponent(format));
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = node("a");
      link.href = objectUrl;
      link.download = "sitesentry-" + scanId + "." + (format === "md" ? "md" : format);
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    } catch (error) {
      setBanner("Could not download report: " + error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = previous;
    }
  }

  function renderHistory(items) {
    const list = $("history-list");
    list.replaceChildren();
    $("history-count").textContent = items.length + " saved scan" + (items.length === 1 ? "" : "s");
    if (!items.length) {
      list.append(node("div", "history-empty", "No scans yet. Your completed assessments will appear here."));
      return;
    }
    items.forEach((item) => {
      const button = node("button", "history-item" + (item.scan_id === state.selectedId ? " active" : ""));
      button.type = "button";
      const grade = node("span", "history-grade", item.status === "completed" ? (item.grade || "—") : "…");
      const text = node("span", "history-text");
      text.append(node("span", "history-url", item.target_url));
      text.append(node("span", "history-date", dateText(item.started_at) + " · " + statusText(item.status)));
      button.append(grade);
      button.append(text);
      if (item.status === "completed") button.append(node("span", "history-score", item.score + "/100"));
      button.addEventListener("click", () => openScan(item.scan_id));
      list.append(button);
    });
  }

  async function refreshHistory() {
    try {
      const response = await api("/api/v1/scans?limit=30");
      renderHistory(await response.json());
    } catch (error) {
      $("history-list").replaceChildren(node("div", "history-empty", "Could not load history: " + error.message));
      $("history-count").textContent = "Unavailable";
    }
  }

  async function openScan(scanId) {
    stopPolling();
    try {
      const response = await api("/api/v1/scans/" + encodeURIComponent(scanId));
      const data = await response.json();
      renderResult(data);
      await refreshHistory();
      if (data.status === "pending" || data.status === "running") watchScan(scanId);
      else clearBanner();
    } catch (error) {
      setBanner("Could not load scan: " + error.message, "error");
    }
  }

  function watchScan(scanId) {
    stopPolling();
    const generation = state.pollGeneration;
    const poll = async () => {
      if (generation !== state.pollGeneration) return;
      try {
        const response = await api("/api/v1/scans/" + encodeURIComponent(scanId));
        const data = await response.json();
        if (generation !== state.pollGeneration) return;
        renderResult(data);
        if (data.status === "pending" || data.status === "running") {
          state.pollTimer = window.setTimeout(poll, 2000);
        } else {
          state.pollTimer = null;
          setBanner(data.status === "completed" ? "Scan completed. Review the findings and recommended fixes below." : "Scan finished with an error. Review the server logs.", data.status === "completed" ? "success" : "error");
          await refreshHistory();
        }
      } catch (error) {
        if (generation === state.pollGeneration) {
          setBanner("Status refresh failed: " + error.message, "error");
          state.pollTimer = window.setTimeout(poll, 4000);
        }
      }
    };
    state.pollTimer = window.setTimeout(poll, 1200);
  }

  $("scan-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!$("scan-form").reportValidity()) return;
    const button = $("scan-button");
    button.disabled = true;
    button.textContent = "Submitting scan…";
    stopPolling();
    clearBanner();
    try {
      const body = {
        url: $("target-url").value.trim(),
        confirm_permission: $("permission").checked,
        max_pages: Number($("max-pages").value),
        max_depth: Number($("max-depth").value),
        ignore_robots: false,
        allow_private: false
      };
      const response = await api("/api/v1/scans", { method: "POST", body: JSON.stringify(body) });
      const accepted = await response.json();
      setBanner("Scan accepted. Waiting for the scanner to begin…", "loading");
      await refreshHistory();
      await openScan(accepted.id);
      watchScan(accepted.id);
    } catch (error) {
      setBanner("Could not start scan: " + error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Start security scan";
    }
  });

  $("refresh-history").addEventListener("click", refreshHistory);
  apiKeyInput.addEventListener("change", refreshHistory);
  refreshHistory();
})();
</script>
</body>
</html>
"""
