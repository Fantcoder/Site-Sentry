"""Self-contained SiteSentry web dashboard."""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>SiteSentry — Security overview</title>

<style>
:root {
  color-scheme: light;
  --canvas: #f1f1eb;
  --paper: #fffefa;
  --paper-soft: #f8f8f2;
  --ink: #202923;
  --ink-soft: #46534a;
  --muted: #7b877d;
  --line: #dfe3d9;
  --line-strong: #cbd3c7;
  --forest: #22352b;
  --forest-2: #2d4638;
  --lime: #c8ed72;
  --lime-deep: #91b83d;
  --red: #b84843;
  --red-bg: #fbefed;
  --amber: #936b20;
  --amber-bg: #fbf5e8;
  --blue: #436a8a;
  --blue-bg: #edf3f7;
  --shadow: 0 8px 24px rgba(37,49,39,.045);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0; min-height: 100vh; color: var(--ink); background: var(--canvas);
  font: 14px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}
button, input, select { font: inherit; }
button { cursor: pointer; }
a { color: inherit; }
.shell { min-height: 100vh; display: grid; grid-template-columns: 226px minmax(0,1fr); }
.sidebar {
  background: var(--forest); color: #e7eee5; padding: 26px 16px 20px;
  display: flex; flex-direction: column; min-height: 100vh;
}
.brand { display:flex; align-items:center; gap:11px; padding: 0 10px 27px; border-bottom:1px solid rgba(234,242,229,.13); }
.brand-mark {
  display:grid; place-items:center; width:35px; height:35px; flex:none;
  background:var(--lime); color:var(--forest); border-radius:9px;
}
.brand-mark svg { width:21px; height:21px; }
.brand-name { font-size:16px; letter-spacing:-.04em; font-weight:800; line-height:1.1; }
.brand-sub { display:block; margin-top:5px; color:#a8b8aa; font-size:9px; font-weight:700; letter-spacing:.16em; }
.nav-label { color:#84998a; font-size:9px; letter-spacing:.16em; font-weight:800; padding:25px 12px 9px; text-transform:uppercase; }
.nav { display:grid; gap:4px; }
.nav a {
  display:flex; align-items:center; gap:11px; padding:10px 12px; border-radius:7px;
  text-decoration:none; color:#b8c7ba; font-size:12px; font-weight:600; transition:background .15s,color .15s;
}
.nav a svg { width:16px; height:16px; opacity:.8; }
.nav a:hover { background:rgba(255,255,255,.07); color:#fff; }
.nav a.active { color:#f6f9f3; background:rgba(200,237,114,.12); box-shadow:inset 2px 0 var(--lime); }
.nav a.active svg { color:var(--lime); opacity:1; }
.sidebar-spacer { flex:1; min-height:28px; }
.engine-card { border:1px solid rgba(234,242,229,.14); background:rgba(7,18,12,.13); border-radius:9px; padding:13px; margin:0 4px; }
.engine-top { display:flex; align-items:center; justify-content:space-between; gap:8px; color:#dce8dc; font-size:11px; font-weight:700; }
.engine-status { display:inline-flex; align-items:center; gap:6px; color:#b9d997; font-size:9px; font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
.engine-status:before { content:""; width:6px; height:6px; border-radius:50%; background:var(--lime); }
.engine-copy { color:#98aa9b; font-size:10px; margin-top:7px; line-height:1.5; }
.sidebar-foot { padding:16px 10px 0; color:#7f9585; font-size:9px; letter-spacing:.08em; }
.workspace { min-width:0; padding:0 clamp(22px,4vw,58px) 46px; }
.topbar {
  height:68px; display:flex; align-items:center; justify-content:space-between; gap:20px;
  border-bottom:1px solid var(--line); color:var(--muted); font-size:11px;
}
.crumb { display:flex; align-items:center; gap:9px; }
.crumb strong { color:var(--ink-soft); font-weight:700; }
.crumb-sep { color:#b4bcb1; }
.top-actions { display:flex; align-items:center; gap:16px; }
.connection { display:inline-flex; align-items:center; gap:7px; font-size:10px; font-weight:750; letter-spacing:.07em; color:#55764e; text-transform:uppercase; }
.connection:before { content:""; width:7px; height:7px; border-radius:50%; background:#83b858; box-shadow:0 0 0 3px rgba(131,184,88,.14); }
.docs-link { text-decoration:none; color:var(--ink-soft); font-weight:700; }
.docs-link:hover { color:#547c37; }
.page-head { display:flex; align-items:flex-end; justify-content:space-between; gap:24px; padding:34px 0 25px; }
.kicker { display:flex; align-items:center; gap:8px; color:#6f865d; font-size:9px; font-weight:800; letter-spacing:.17em; text-transform:uppercase; }
.kicker-line { width:20px; height:1px; background:#91ab70; }
h1 { margin:8px 0 7px; font-size:clamp(27px,3vw,35px); line-height:1.1; letter-spacing:-.055em; font-weight:760; }
.page-head p { margin:0; color:var(--muted); font-size:12px; }
.head-note { display:flex; align-items:center; gap:10px; border:1px solid var(--line); background:rgba(255,254,250,.65); padding:9px 12px; border-radius:6px; color:var(--ink-soft); font-size:10px; white-space:nowrap; }
.head-note strong { color:#557b38; font-size:10px; }
.metrics {
  display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); margin-bottom:22px;
  background:var(--paper); border:1px solid var(--line); border-radius:9px; box-shadow:var(--shadow);
}
.stat { position:relative; min-width:0; padding:15px 19px 14px; border-right:1px solid var(--line); }
.stat:last-child { border-right:0; }
.stat-label { color:var(--muted); font-size:9px; text-transform:uppercase; letter-spacing:.13em; font-weight:800; }
.stat-value { margin-top:5px; font-size:26px; line-height:1.1; font-weight:780; letter-spacing:-.06em; color:var(--ink); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stat-sub { color:#9aa398; font-size:9px; margin-top:4px; }
.layout { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr); gap:16px; align-items:stretch; }
.main-column,.side-column { display:contents; }
.panel {
  background:var(--paper); border:1px solid var(--line); border-radius:9px;
  box-shadow:var(--shadow); overflow:hidden; min-width:0;
}
#new-scan { grid-column:1; grid-row:1; }
#history-panel { grid-column:2; grid-row:1; }
#safeguards-panel { grid-column:2; grid-row:2; }
#results-panel { grid-column:1 / -1; grid-row:3; }
.panel-head {
  min-height:59px; display:flex; align-items:center; justify-content:space-between; gap:14px;
  padding:14px 18px; border-bottom:1px solid var(--line); background:var(--paper-soft);
}
.panel-title { display:flex; align-items:center; gap:9px; min-width:0; }
.panel-index { color:#89a268; font-size:9px; letter-spacing:.12em; font-weight:800; }
.panel-head h2 { font-size:12px; margin:0; letter-spacing:-.01em; font-weight:780; }
.panel-head p { font-size:10px; color:var(--muted); margin:3px 0 0; }
.section-tag { color:#7d8e73; font-size:9px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; white-space:nowrap; }
.panel-body { padding:18px; }
#scan-form { display:grid; gap:14px; }
.field { display:grid; gap:6px; min-width:0; }
.field.full { grid-column:1/-1; }
label { color:#556259; font-size:10px; font-weight:750; letter-spacing:.02em; }
input[type=url],input[type=password],input[type=number],select {
  width:100%; min-width:0; border:1px solid var(--line-strong); border-radius:6px;
  color:var(--ink); background:#fff; padding:10px 11px; outline:none; font-size:12px;
  transition:border .15s,box-shadow .15s;
}
input:focus,select:focus { border-color:#8cae5a; box-shadow:0 0 0 3px rgba(145,184,61,.13); }
input::placeholder { color:#a5ada2; }
.field-hint { color:#9aa398; font-size:9px; font-weight:500; }
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.consent {
  display:flex; align-items:flex-start; gap:9px; padding:10px 11px; border:1px solid #dfe6d2;
  background:#f7f9ef; border-radius:6px; color:#64745c; font-size:10px; line-height:1.45; font-weight:500;
}
.consent input { margin:2px 0 0; accent-color:#739c41; flex:none; }
.actions { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.primary {
  border:1px solid var(--forest); border-radius:5px; padding:10px 14px; color:#f6faef;
  background:var(--forest); font-size:11px; font-weight:750; letter-spacing:.01em;
  transition:background .15s,transform .15s;
}
.primary:hover { background:#344d3e; transform:translateY(-1px); }
.primary:disabled { opacity:.55; cursor:wait; transform:none; }
.subtle { color:#8b968b; font-size:9px; }
.status-banner {
  display:none; align-items:center; gap:9px; margin-top:13px; padding:10px 12px;
  border:1px solid var(--line); border-radius:6px; background:#f7f8f2; color:#5b665d; font-size:10px;
}
.status-banner.visible { display:flex; }
.status-banner.error { border-color:#efd1cd; background:var(--red-bg); color:var(--red); }
.status-banner.success { border-color:#d8e6c4; background:#f5f8ed; color:#56753a; }
.spinner { width:13px; height:13px; border:2px solid #d8dfd2; border-top-color:#78994c; border-radius:50%; animation:spin .8s linear infinite; flex:none; }
@keyframes spin { to { transform:rotate(360deg); } }
.text-button { border:0; background:transparent; color:#5e7f43; padding:3px 0; font-size:10px; font-weight:800; }
.text-button:hover { color:#334d2c; text-decoration:underline; }
.history-list { display:grid; gap:0; }
.history-item {
  display:flex; align-items:center; gap:10px; width:100%; text-align:left; padding:11px 2px;
  border:0; border-bottom:1px solid #edf0e9; border-radius:0; background:transparent; color:var(--ink);
}
.history-item:last-child { border-bottom:0; }
.history-item:hover,.history-item.active { background:#f7f9f2; }
.history-grade {
  display:grid; place-items:center; flex:none; width:30px; height:30px; border-radius:5px;
  background:#edf2e4; color:#55763a; font-size:12px; font-weight:850;
}
.history-text { min-width:0; flex:1; }
.history-url { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:10px; font-weight:750; color:#354238; }
.history-date { display:block; color:#929c90; font-size:9px; margin-top:2px; }
.history-score { color:#5c6e59; font-weight:800; font-size:10px; }
.history-empty { color:#8c978b; font-size:10px; padding:14px 2px; }
.history-footer { display:flex; align-items:center; justify-content:space-between; gap:10px; padding-top:10px; margin-top:5px; border-top:1px solid #edf0e9; color:#9aa398; font-size:9px; }
.safeguard-list { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.safeguard { display:flex; align-items:flex-start; gap:8px; color:#59665b; font-size:10px; line-height:1.4; }
.safeguard-mark { display:grid; place-items:center; width:19px; height:19px; flex:none; border-radius:4px; background:#edf3e3; color:#648443; font-size:9px; font-weight:900; }
.safeguard strong { display:block; color:#334238; font-size:10px; margin-bottom:2px; }
.api-docs { display:flex; align-items:center; justify-content:space-between; gap:12px; color:#879287; font-size:10px; }
.api-docs a { color:#557c3b; text-decoration:none; font-weight:800; }
.api-docs a:hover { text-decoration:underline; }
#results-panel { margin-top:16px; }
.result-empty { display:grid; place-items:center; text-align:center; min-height:170px; padding:28px; color:#929c90; font-size:11px; }
.empty-icon { display:grid; place-items:center; width:39px; height:39px; border-radius:8px; background:#f0f4e8; color:#74934d; margin-bottom:10px; }
.empty-icon svg { width:20px; }
.result-top { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.grade-wrap { display:flex; align-items:center; gap:12px; }
.grade {
  display:grid; place-items:center; width:48px; height:48px; border-radius:7px;
  background:#f2f5ea; border:1px solid #dfe7d2; font-size:24px; font-weight:850; color:#688446;
}
.grade.good { color:#527c34; border-color:#d6e6c5; background:#f2f7e9; }
.grade.warn { color:var(--amber); border-color:#e9ddbd; background:var(--amber-bg); }
.grade.bad { color:var(--red); border-color:#edcfcb; background:var(--red-bg); }
.result-title { font-weight:800; font-size:12px; color:#354238; }
.result-meta { color:#899488; font-size:9px; margin-top:3px; overflow-wrap:anywhere; }
.pill { display:inline-flex; align-items:center; gap:6px; padding:5px 8px; border:1px solid #e0e5da; border-radius:4px; background:#f8f9f4; color:#687567; font-size:9px; font-weight:800; }
.score-track { height:5px; border-radius:99px; background:#e9ede5; overflow:hidden; margin-top:14px; }
.score-fill { height:100%; border-radius:99px; background:#8bb650; width:0%; transition:width .3s; }
.report-actions { display:flex; gap:7px; flex-wrap:wrap; margin-top:14px; }
.report-btn {
  border:1px solid #dce2d7; border-radius:4px; padding:7px 9px; color:#536153;
  background:#fffefa; font-size:9px; font-weight:800;
}
.report-btn:hover { border-color:#93ad72; background:#f6f8ef; color:#4d7132; }
.report-btn:disabled { opacity:.5; cursor:wait; }
.subsection { margin-top:21px; }
.subsection-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:9px; padding-bottom:8px; border-bottom:1px solid #e9ede5; }
.subsection-head h3 { margin:0; font-size:11px; font-weight:800; }
.count { color:#929c90; font-size:9px; }
.severity-row { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:11px; }
.sev-count { font-size:9px; border:1px solid #e2e6dd; border-radius:4px; padding:4px 7px; color:#879187; font-weight:800; }
.sev-count.high,.severity.high,.severity.critical { color:#a9433f; border-color:#efd2cd; background:var(--red-bg); }
.sev-count.medium,.severity.medium { color:#8a6826; border-color:#eee0bd; background:var(--amber-bg); }
.sev-count.low,.severity.low { color:#476e8b; border-color:#d8e4ec; background:var(--blue-bg); }
.sev-count.info,.severity.info { color:#7d897f; border-color:#e2e6dd; background:#f7f8f4; }
.finding-list { display:grid; gap:0; }
.finding {
  border:0; border-bottom:1px solid #e9ede5; border-radius:0; background:transparent; overflow:hidden;
}
.finding:last-child { border-bottom:0; }
.finding-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding:11px 2px; }
.finding-title { font-size:11px; font-weight:800; color:#354238; overflow-wrap:anywhere; }
.finding-id { font-size:9px; color:#929c90; margin-top:3px; }
.severity {
  flex:none; padding:4px 6px; border:1px solid #e2e6dd; border-radius:4px;
  font-size:8px; font-weight:850; text-transform:uppercase; letter-spacing:.08em;
}
.finding-body {
  border-top:1px solid #edf0e9; padding:11px 12px; display:grid; grid-template-columns:1fr 1fr 1fr;
  gap:13px; background:#fafbf7;
}
.detail-label { color:#9aa398; text-transform:uppercase; font-size:8px; letter-spacing:.12em; font-weight:850; margin-bottom:4px; }
.detail-value { color:#59665b; font-size:10px; overflow-wrap:anywhere; white-space:pre-wrap; }
.fix-value { color:#55753c; }
.breakdown { width:100%; border-collapse:collapse; font-size:10px; }
.breakdown th { color:#929c90; font-size:8px; letter-spacing:.11em; text-transform:uppercase; text-align:left; padding:8px 9px; border-bottom:1px solid #e3e8df; font-weight:850; }
.breakdown td { color:#536056; padding:8px 9px; border-bottom:1px solid #edf0e9; }
.breakdown tr:last-child td { border-bottom:0; }
.breakdown td:last-child,.breakdown th:last-child { text-align:right; }
.footer { display:flex; justify-content:space-between; gap:14px; padding-top:21px; color:#9aa398; font-size:9px; }
@media (max-width: 1000px) {
  .shell { grid-template-columns:190px minmax(0,1fr); }
  .layout { grid-template-columns:1fr; }
  #new-scan,#history-panel,#safeguards-panel { grid-column:1; }
  #new-scan { grid-row:1; } #history-panel { grid-row:2; } #safeguards-panel { grid-row:3; }
  #results-panel { grid-row:4; }
}
@media (max-width: 680px) {
  .shell { display:block; }
  .sidebar { min-height:auto; padding:12px 14px; display:flex; flex-direction:row; align-items:center; justify-content:space-between; gap:10px; }
  .brand { padding:0; border:0; }
  .brand-mark { width:31px; height:31px; }
  .brand-name { font-size:14px; }
  .brand-sub { font-size:8px; }
  .nav-label,.sidebar-spacer,.engine-card,.sidebar-foot { display:none; }
  .nav { display:flex; gap:3px; }
  .nav a { padding:8px; font-size:0; }
  .nav a svg { width:17px; height:17px; }
  .workspace { padding:0 15px 28px; }
  .topbar { height:51px; }
  .page-head { display:block; padding:25px 0 19px; }
  .head-note { display:inline-flex; margin-top:13px; }
  .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .stat:nth-child(2) { border-right:0; }
  .stat:nth-child(-n+2) { border-bottom:1px solid var(--line); }
  .form-grid { grid-template-columns:1fr 1fr; }
  .safeguard-list { grid-template-columns:1fr; }
  .finding-body { grid-template-columns:1fr; }
  .footer { flex-direction:column; }
}
@media (prefers-reduced-motion: reduce) { *,*::before,*::after { animation-duration:.01ms !important; transition-duration:.01ms !important; scroll-behavior:auto !important; } }
</style>

</head>
<body>
<div class="shell">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg>
      </div>
      <div><div class="brand-name">SiteSentry</div><span class="brand-sub">SECURITY WORKSPACE</span></div>
    </div>
    <div class="nav-label">Workspace</div>
    <nav class="nav" aria-label="Main navigation">
      <a class="active" href="#overview" aria-current="page">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="8" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="15" width="7" height="6" rx="1"/></svg>
        Overview
      </a>
      <a href="#new-scan">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="m16 16 4 4M11 7v8M7 11h8"/></svg>
        New assessment
      </a>
      <a href="#history-panel">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h10"/><circle cx="19" cy="17" r="2"/></svg>
        Scan history
      </a>
      <a href="#results-panel">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 3h10l4 4v14H5z"/><path d="M14 3v5h5M8 13h8M8 17h8"/></svg>
        Findings & reports
      </a>
    </nav>
    <div class="sidebar-spacer"></div>
    <div class="engine-card">
      <div class="engine-top"><span>Scan engine</span><span class="engine-status">Ready</span></div>
      <div class="engine-copy">16 passive checks · bounded crawl · same-origin scope</div>
    </div>
    <div class="sidebar-foot">SITESENTRY / LOCAL INSTANCE</div>
  </aside>

  <main class="workspace" id="overview">
    <header class="topbar">
      <div class="crumb"><span>Workspace</span><span class="crumb-sep">/</span><strong>Overview</strong></div>
      <div class="top-actions"><span class="connection">Local engine</span><a class="docs-link" href="/docs" target="_blank" rel="noreferrer">API reference ↗</a></div>
    </header>

    <section class="page-head">
      <div>
        <div class="kicker"><span class="kicker-line"></span> WEB SECURITY / OPERATIONS</div>
        <h1>Security overview</h1>
        <p>Assess the configuration and exposure of the websites you manage.</p>
      </div>
      <div class="head-note"><strong>PASSIVE MODE</strong><span>·</span><span>16 checks available</span></div>
    </section>

    <section class="metrics" aria-label="Selected scan metrics">
      <div class="stat"><div class="stat-label">Security score</div><div class="stat-value" id="stat-score">—</div><div class="stat-sub">Out of 100 points</div></div>
      <div class="stat"><div class="stat-label">Overall grade</div><div class="stat-value" id="stat-grade">—</div><div class="stat-sub">Assessment rating</div></div>
      <div class="stat"><div class="stat-label">Pages scanned</div><div class="stat-value" id="stat-pages">—</div><div class="stat-sub">Pages visited</div></div>
      <div class="stat"><div class="stat-label">Findings</div><div class="stat-value" id="stat-findings">—</div><div class="stat-sub">Issues detected</div></div>
    </section>

    <div class="layout">
      <section class="panel" id="new-scan">
        <div class="panel-head">
          <div class="panel-title"><span class="panel-index">01</span><div><h2>New assessment</h2><p>Configure a bounded scan of an authorized website.</p></div></div>
          <span class="section-tag">Target setup</span>
        </div>
        <div class="panel-body">
          <form id="scan-form">
            <div class="field">
              <label for="target-url">TARGET URL</label>
              <input id="target-url" name="url" type="url" placeholder="https://yourwebsite.com" autocomplete="url" required>
              <span class="field-hint">Enter the exact website origin you are authorized to assess.</span>
            </div>
            <div class="form-grid">
              <div class="field">
                <label for="max-pages">MAXIMUM PAGES</label>
                <input id="max-pages" name="max_pages" type="number" min="1" max="500" value="50" required>
              </div>
              <div class="field">
                <label for="max-depth">CRAWL DEPTH</label>
                <input id="max-depth" name="max_depth" type="number" min="1" max="10" value="2" required>
              </div>
              <div class="field full">
                <label for="api-key">API KEY <span class="field-hint">— only if authentication is configured</span></label>
                <input id="api-key" type="password" placeholder="Bearer token (optional)" autocomplete="off">
              </div>
            </div>
            <label class="consent">
              <input id="permission" type="checkbox" required>
              <span>I own this website or have explicit authorization to assess it. I understand that the scanner will send HTTP requests to the target.</span>
            </label>
            <div class="actions">
              <button class="primary" id="scan-button" type="submit">Start assessment&nbsp; ↗</button>
              <span class="subtle">2 requests/sec default · 1 MB response cap</span>
            </div>
          </form>
          <div class="status-banner" id="status-banner" role="status" aria-live="polite"><span id="status-text"></span></div>
        </div>
      </section>

      <section class="panel" id="history-panel">
        <div class="panel-head">
          <div class="panel-title"><span class="panel-index">02</span><div><h2>Recent assessments</h2><p>Previously saved scan results.</p></div></div>
          <button class="text-button" id="refresh-history" type="button">Refresh ↻</button>
        </div>
        <div class="panel-body">
          <div class="history-list" id="history-list"><div class="history-empty">Loading scan history…</div></div>
          <div class="history-footer"><span id="history-count">—</span><span>Newest first</span></div>
        </div>
      </section>

      <section class="panel" id="safeguards-panel">
        <div class="panel-head">
          <div class="panel-title"><span class="panel-index">03</span><div><h2>Assessment safeguards</h2><p>Controls applied by the scanner.</p></div></div>
          <span class="section-tag">By default</span>
        </div>
        <div class="panel-body">
          <div class="safeguard-list">
            <div class="safeguard"><span class="safeguard-mark">✓</span><div><strong>Same-origin scope</strong>External links are not followed.</div></div>
            <div class="safeguard"><span class="safeguard-mark">✓</span><div><strong>Private IP protection</strong>Private and link-local ranges are blocked.</div></div>
            <div class="safeguard"><span class="safeguard-mark">✓</span><div><strong>Polite crawling</strong>Rate, depth and page limits apply.</div></div>
            <div class="safeguard"><span class="safeguard-mark">✓</span><div><strong>Passive checks</strong>No exploit or injection payloads.</div></div>
          </div>
        </div>
      </section>

      <section class="panel" id="results-panel">
        <div class="panel-head">
          <div class="panel-title"><span class="panel-index">04</span><div><h2>Assessment detail</h2><p id="result-subtitle">Select a saved assessment or start a new scan.</p></div></div>
          <span class="section-tag" id="result-state">No assessment selected</span>
        </div>
        <div class="panel-body" id="result-content">
          <div class="result-empty">
            <div><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="M9 12h6M12 9v6"/></svg></div><strong>No assessment selected</strong><div style="margin-top:5px">Start a scan to review the security score, evidence and recommended fixes.</div></div>
          </div>
        </div>
      </section>
    </div>

    <footer class="footer"><span>SITESENTRY · PASSIVE WEB SECURITY ASSESSMENT</span><span>ONLY ASSESS ASSETS YOU ARE AUTHORIZED TO TEST</span></footer>
  </main>
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
