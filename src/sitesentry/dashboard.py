"""Self-contained SiteSentry web dashboard."""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>SiteSentry — Security operations</title>
<style>
:root {
  color-scheme: dark;
  --bg:#0b1115; --sidebar:#0d171b; --surface:#111d22; --surface-2:#15242a;
  --surface-3:#1a2b31; --line:#26383e; --line-soft:#1d2d33;
  --text:#e8efeb; --muted:#91a19d; --quiet:#647671;
  --green:#a9d77b; --green-2:#78b65c; --green-ink:#162413;
  --red:#f08e83; --red-bg:#311f20; --amber:#e5bd72; --amber-bg:#30291d;
  --blue:#8bb8d6; --blue-bg:#1d2c35; --shadow:0 12px 32px rgba(0,0,0,.16);
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  margin:0; min-height:100vh; color:var(--text); background:var(--bg);
  font:13px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased;
}
button,input,select { font:inherit; }
button { cursor:pointer; }
a { color:inherit; }
.shell { min-height:100vh; display:grid; grid-template-columns:230px minmax(0,1fr); }
.sidebar {
  position:sticky; top:0; height:100vh; padding:22px 15px 16px; display:flex; flex-direction:column;
  background:var(--sidebar); border-right:1px solid var(--line-soft);
}
.brand { display:flex; align-items:center; gap:11px; padding:2px 10px 23px; border-bottom:1px solid var(--line-soft); }
.brand-mark {
  display:grid; place-items:center; width:34px; height:34px; flex:none; border-radius:9px;
  color:#142016; background:var(--green);
}
.brand-mark svg { width:20px; height:20px; }
.brand-name { font-size:15px; font-weight:800; letter-spacing:-.04em; line-height:1.1; }
.brand-sub { display:block; margin-top:5px; color:#6f8580; font-size:8px; font-weight:800; letter-spacing:.18em; }
.nav-label { padding:25px 11px 9px; color:#647873; font-size:8px; font-weight:800; letter-spacing:.17em; text-transform:uppercase; }
.nav { display:grid; gap:4px; }
.nav a {
  display:flex; align-items:center; gap:11px; padding:9px 11px; border-radius:6px;
  color:#9cadab; text-decoration:none; font-size:11px; font-weight:650; transition:.15s ease;
}
.nav a svg { width:15px; height:15px; opacity:.78; }
.nav a:hover { color:var(--text); background:#17252a; }
.nav a.active { color:#e9f3e6; background:#1a2a2d; box-shadow:inset 2px 0 var(--green); }
.nav a.active svg { color:var(--green); opacity:1; }
.sidebar-spacer { flex:1; min-height:24px; }
.engine-card { margin:0 3px; padding:12px; border:1px solid #263a3b; border-radius:7px; background:#111f21; }
.engine-head { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.engine-title { color:#d8e5df; font-size:10px; font-weight:750; }
.engine-ready { display:inline-flex; align-items:center; gap:5px; color:var(--green); font-size:8px; font-weight:850; letter-spacing:.1em; }
.engine-ready:before { content:""; width:5px; height:5px; border-radius:50%; background:var(--green); box-shadow:0 0 0 3px #2b3a2b; }
.engine-copy { color:#748782; font-size:9px; line-height:1.5; margin-top:7px; }
.sidebar-foot { color:#586c68; padding:14px 9px 0; font-size:8px; letter-spacing:.12em; }
.workspace { min-width:0; padding:0 clamp(20px,3.2vw,48px) 38px; }
.topbar {
  height:59px; display:flex; align-items:center; justify-content:space-between; gap:18px;
  border-bottom:1px solid var(--line-soft); color:var(--muted); font-size:10px;
}
.crumb { display:flex; align-items:center; gap:9px; }
.crumb strong { color:#d2ddd8; font-weight:700; }
.crumb-sep { color:#50635f; }
.top-actions { display:flex; align-items:center; gap:15px; }
.connection { display:inline-flex; align-items:center; gap:7px; color:#b6d59b; font-size:8px; font-weight:850; letter-spacing:.13em; text-transform:uppercase; }
.connection:before { content:""; width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 0 3px #263626; }
.docs-link { color:#a7b8b1; text-decoration:none; font-size:10px; font-weight:700; }
.docs-link:hover { color:var(--green); }
.page-head { display:flex; align-items:flex-end; justify-content:space-between; gap:20px; padding:28px 0 21px; }
.kicker { display:flex; align-items:center; gap:8px; color:#99bf78; font-size:8px; font-weight:850; letter-spacing:.2em; text-transform:uppercase; }
.kicker-line { width:17px; height:1px; background:#7da65e; }
h1 { margin:7px 0 6px; color:#eef4f0; font-size:clamp(25px,3vw,33px); line-height:1.1; font-weight:760; letter-spacing:-.055em; }
.page-head p { margin:0; color:#84958f; font-size:11px; }
.head-note { display:flex; align-items:center; gap:9px; padding:8px 11px; border:1px solid var(--line); border-radius:5px; background:#111c20; color:#84958f; font-size:9px; white-space:nowrap; }
.head-note strong { color:var(--green); font-size:8px; letter-spacing:.12em; }
.metrics {
  display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); margin-bottom:15px;
  border:1px solid var(--line); border-radius:7px; background:var(--surface); box-shadow:var(--shadow);
}
.stat { position:relative; min-width:0; padding:13px 16px 12px; border-right:1px solid var(--line); }
.stat:last-child { border-right:0; }
.stat-label { color:#84958f; font-size:8px; text-transform:uppercase; letter-spacing:.14em; font-weight:850; }
.stat-value { margin-top:6px; color:#eef4f0; font-size:24px; line-height:1.05; font-weight:800; letter-spacing:-.06em; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stat-sub { margin-top:4px; color:#667973; font-size:9px; }
.layout { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(300px,.95fr); gap:14px; align-items:start; }
.main-column,.side-column { display:contents; }
.panel { min-width:0; overflow:hidden; border:1px solid var(--line); border-radius:7px; background:var(--surface); box-shadow:var(--shadow); }
#new-scan { grid-column:1; grid-row:1; }
#history-panel { grid-column:2; grid-row:1; }
#severity-panel { grid-column:2; grid-row:2; }
#results-panel { grid-column:1 / -1; grid-row:3; }
.panel-head {
  min-height:53px; display:flex; align-items:center; justify-content:space-between; gap:12px;
  padding:12px 15px; border-bottom:1px solid var(--line); background:#142127;
}
.panel-title { display:flex; align-items:center; gap:9px; min-width:0; }
.panel-index { color:#8ebd6a; font-size:8px; letter-spacing:.13em; font-weight:900; }
.panel-head h2 { margin:0; color:#e2ebe6; font-size:11px; font-weight:800; letter-spacing:-.01em; }
.panel-head p { margin:3px 0 0; color:#788a84; font-size:9px; }
.section-tag { color:#81928b; font-size:8px; font-weight:850; letter-spacing:.13em; text-transform:uppercase; white-space:nowrap; }
.panel-body { padding:15px; }
#scan-form { display:grid; gap:12px; }
.field { display:grid; gap:6px; min-width:0; }
.field.full { grid-column:1/-1; }
label { color:#a8b7af; font-size:9px; font-weight:800; letter-spacing:.08em; }
input[type=url],input[type=password],input[type=number],select {
  width:100%; min-width:0; padding:10px 11px; border:1px solid #304249; border-radius:5px;
  outline:none; color:#e6eee9; background:#0d171b; font-size:11px; transition:border .15s,box-shadow .15s;
}
input:focus,select:focus { border-color:#88b66b; box-shadow:0 0 0 3px rgba(140,184,103,.12); }
input::placeholder { color:#5d706b; }
.field-hint { color:#71827b; font-size:8px; font-weight:500; letter-spacing:0; }
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.consent {
  display:flex; align-items:flex-start; gap:9px; padding:9px 10px; border:1px solid #34463a;
  border-radius:5px; background:#17231d; color:#a9bba8; font-size:9px; line-height:1.5; font-weight:500; letter-spacing:0;
}
.consent input { margin:2px 0 0; accent-color:var(--green); flex:none; }
.actions { display:flex; align-items:center; gap:11px; flex-wrap:wrap; }
.primary {
  padding:9px 13px; border:1px solid #9bc76e; border-radius:5px; color:#142013;
  background:var(--green); font-size:10px; font-weight:850; letter-spacing:.01em; transition:.15s ease;
}
.primary:hover { background:#c0e99a; transform:translateY(-1px); }
.primary:disabled { opacity:.55; cursor:wait; transform:none; }
.subtle { color:#70817a; font-size:8px; }
.status-banner {
  display:none; align-items:center; gap:8px; margin-top:11px; padding:9px 10px; border:1px solid var(--line);
  border-radius:5px; background:#172328; color:#b2c1ba; font-size:9px;
}
.status-banner.visible { display:flex; }
.status-banner.error { border-color:#603838; background:#2a1c1e; color:#f1aaa1; }
.status-banner.success { border-color:#3d5735; background:#1c291d; color:#b9dc98; }
.spinner { width:12px; height:12px; flex:none; border:2px solid #53675f; border-top-color:var(--green); border-radius:50%; animation:spin .8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.text-button { padding:2px 0; border:0; background:transparent; color:#a9cf82; font-size:9px; font-weight:850; }
.text-button:hover { color:#d4f0b3; text-decoration:underline; }
.history-list { display:grid; gap:0; }
.history-item {
  display:flex; align-items:center; gap:9px; width:100%; padding:9px 1px; border:0;
  border-bottom:1px solid #1e3035; border-radius:0; background:transparent; color:var(--text); text-align:left;
}
.history-item:last-child { border-bottom:0; }
.history-item:hover,.history-item.active { background:#17262a; }
.history-grade {
  display:grid; place-items:center; flex:none; width:28px; height:28px; border:1px solid #35493d;
  border-radius:5px; color:#b8db94; background:#1a2921; font-size:11px; font-weight:850;
}
.history-text { flex:1; min-width:0; }
.history-url { display:block; overflow:hidden; color:#d4dfd9; font-size:9px; font-weight:750; text-overflow:ellipsis; white-space:nowrap; }
.history-date { display:block; margin-top:2px; color:#74857e; font-size:8px; }
.history-score { color:#a9c889; font-size:9px; font-weight:850; }
.history-empty { padding:12px 1px; color:#758780; font-size:9px; }
.history-footer { display:flex; justify-content:space-between; gap:10px; padding-top:9px; margin-top:4px; border-top:1px solid #203137; color:#71827b; font-size:8px; }
.severity-summary { display:grid; gap:11px; }
.severity-empty { color:#73847d; font-size:9px; padding:4px 0; }
.sev-row { display:grid; grid-template-columns:58px 1fr 25px; align-items:center; gap:8px; }
.sev-name { color:#a6b4ac; font-size:9px; font-weight:700; text-transform:capitalize; }
.sev-track { height:6px; overflow:hidden; border-radius:99px; background:#26363a; }
.sev-fill { height:100%; border-radius:99px; width:0; transition:width .25s; }
.sev-fill.critical,.sev-fill.high { background:#d97970; }
.sev-fill.medium { background:#d0aa60; }
.sev-fill.low { background:#76a9c7; }
.sev-fill.info { background:#84948e; }
.sev-number { color:#d3ddd7; font-size:9px; text-align:right; font-variant-numeric:tabular-nums; }
.severity-legend { display:flex; justify-content:space-between; gap:8px; padding-top:10px; margin-top:4px; border-top:1px solid #203137; color:#71827b; font-size:8px; }
#results-panel { margin-top:14px; }
.result-empty { display:grid; place-items:center; min-height:155px; padding:25px; color:#74857e; text-align:center; font-size:10px; }
.empty-icon { display:grid; place-items:center; width:38px; height:38px; margin-bottom:10px; border:1px solid #2c4036; border-radius:8px; color:var(--green); background:#17251d; }
.empty-icon svg { width:19px; height:19px; }
.result-top { display:flex; align-items:center; justify-content:space-between; gap:14px; flex-wrap:wrap; }
.grade-wrap { display:flex; align-items:center; gap:11px; }
.grade {
  display:grid; place-items:center; width:46px; height:46px; border:1px solid #38503b; border-radius:6px;
  color:#badb93; background:#19271d; font-size:23px; font-weight:900;
}
.grade.good { color:#bce59a; border-color:#3d6040; background:#192a1e; }
.grade.warn { color:#e4bf76; border-color:#655331; background:#2b261b; }
.grade.bad { color:#f09b90; border-color:#673d3a; background:#2c1e20; }
.result-title { color:#e2ebe5; font-size:11px; font-weight:850; }
.result-meta { margin-top:3px; color:#80928a; font-size:8px; overflow-wrap:anywhere; }
.pill { display:inline-flex; align-items:center; gap:6px; padding:5px 8px; border:1px solid #33464a; border-radius:4px; color:#b6c5be; background:#162429; font-size:8px; font-weight:850; text-transform:uppercase; letter-spacing:.08em; }
.score-track { height:5px; margin-top:13px; overflow:hidden; border-radius:99px; background:#2a3a3d; }
.score-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,#71a95b,#c0e990); width:0%; transition:width .3s; }
.report-actions { display:flex; gap:6px; flex-wrap:wrap; margin-top:12px; }
.report-btn {
  padding:6px 9px; border:1px solid #34474b; border-radius:4px; color:#b6c4bd;
  background:#142126; font-size:8px; font-weight:850;
}
.report-btn:hover { border-color:#789a5b; color:#c7e4a8; background:#1a2925; }
.report-btn:disabled { opacity:.5; cursor:wait; }
.result-overview { display:grid; grid-template-columns:205px minmax(0,1fr); gap:20px; align-items:center; padding:16px 0; border-bottom:1px solid #24363b; }
.score-block { display:flex; align-items:center; gap:12px; }
.score-orbit {
  --score:0; display:grid; place-items:center; width:76px; height:76px; flex:none; border-radius:50%;
  background:conic-gradient(var(--green) var(--score), #2b3c40 0);
  position:relative;
}
.score-orbit:before { content:""; position:absolute; inset:6px; border-radius:50%; background:#111d22; }
.score-orbit span { position:relative; z-index:1; color:#edf4ee; font-size:19px; font-weight:850; letter-spacing:-.06em; }
.score-caption { color:#83948b; font-size:8px; margin-top:3px; }
.result-stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); border:1px solid #2a3a3f; border-radius:5px; }
.result-stat { padding:10px 12px; border-right:1px solid #2a3a3f; min-width:0; }
.result-stat:last-child { border-right:0; }
.result-stat strong { display:block; color:#e5ede8; font-size:15px; font-weight:850; }
.result-stat span { display:block; margin-top:3px; color:#81928a; font-size:8px; text-transform:uppercase; letter-spacing:.1em; }
.subsection { margin-top:17px; }
.subsection-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:9px; padding-bottom:8px; border-bottom:1px solid #24363b; }
.subsection-head h3 { margin:0; color:#dce6df; font-size:10px; font-weight:850; }
.count { color:#788a82; font-size:8px; }
.finding-tools { display:flex; align-items:center; gap:8px; }
.finding-tools input,.finding-tools select { width:auto; padding:6px 8px; font-size:9px; }
.finding-tools input { min-width:175px; }
.table-wrap { width:100%; overflow-x:auto; }
.finding-table { width:100%; border-collapse:collapse; min-width:610px; }
.finding-table th {
  padding:8px 9px; border-bottom:1px solid #2a3b40; color:#7e9089; background:#142126;
  font-size:8px; letter-spacing:.12em; text-align:left; text-transform:uppercase;
}
.finding-table td { padding:10px 9px; border-bottom:1px solid #213238; color:#bdcbc3; font-size:9px; vertical-align:middle; }
.finding-table tr:last-child td { border-bottom:0; }
.finding-table tbody tr:hover td { background:#152429; }
.finding-main { color:#e0e9e3; font-size:9px; font-weight:800; }
.finding-sub { display:block; max-width:580px; margin-top:3px; overflow:hidden; color:#75877f; font-size:8px; text-overflow:ellipsis; white-space:nowrap; }
.severity {
  display:inline-flex; align-items:center; padding:4px 6px; border:1px solid #334249;
  border-radius:4px; color:#9aa9a2; background:#172328; font-size:7px; font-weight:900; letter-spacing:.1em; text-transform:uppercase;
}
.severity.high,.severity.critical { color:#f0a29a; border-color:#64403d; background:#2b2021; }
.severity.medium { color:#e3c17f; border-color:#5d4c2d; background:#29251d; }
.severity.low { color:#9dc4dc; border-color:#344e5b; background:#192832; }
.severity.info { color:#a6b3ac; border-color:#35464a; background:#182427; }
.inspect-button { padding:5px 7px; border:1px solid #34474b; border-radius:4px; color:#a9c58d; background:transparent; font-size:8px; font-weight:800; }
.inspect-button:hover { border-color:#86a967; background:#1a2a24; }
.finding-detail-row td { padding:0 9px 11px; background:#132126; }
.finding-detail { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; padding:12px; border:1px solid #2a3c40; border-radius:5px; background:#101b20; }
.detail-label { margin-bottom:4px; color:#71847b; font-size:7px; font-weight:900; letter-spacing:.13em; text-transform:uppercase; }
.detail-value { color:#b9c8c0; font-size:9px; overflow-wrap:anywhere; white-space:pre-wrap; }
.fix-value { color:#b9d998; }
.no-findings { padding:22px 10px; color:#809189; text-align:center; font-size:9px; }
.breakdown { width:100%; border-collapse:collapse; font-size:9px; }
.breakdown th { padding:8px 9px; border-bottom:1px solid #2a3b40; color:#7c8e86; font-size:7px; letter-spacing:.12em; text-align:left; text-transform:uppercase; }
.breakdown td { padding:8px 9px; border-bottom:1px solid #203137; color:#b8c7bf; }
.breakdown td:last-child,.breakdown th:last-child { text-align:right; }
.breakdown tr:last-child td { border-bottom:0; }
.footer { display:flex; justify-content:space-between; gap:12px; padding-top:19px; color:#60736d; font-size:8px; letter-spacing:.07em; }
@media (max-width:1050px) {
  .shell { grid-template-columns:205px minmax(0,1fr); }
  .workspace { padding-left:22px; padding-right:22px; }
  .layout { grid-template-columns:1fr; }
  #new-scan,#history-panel,#severity-panel { grid-column:1; }
  #new-scan { grid-row:1; } #history-panel { grid-row:2; } #severity-panel { grid-row:3; }
  #results-panel { grid-row:4; }
}
@media (max-width:680px) {
  .shell { display:block; }
  .sidebar { position:relative; width:100%; height:auto; min-height:0; padding:11px 13px; flex-direction:row; align-items:center; justify-content:space-between; gap:9px; }
  .brand { padding:0; border:0; } .brand-mark { width:30px; height:30px; }
  .brand-name { font-size:13px; } .brand-sub { font-size:7px; }
  .nav-label,.sidebar-spacer,.engine-card,.sidebar-foot { display:none; }
  .nav { display:flex; gap:2px; } .nav a { padding:7px; font-size:0; } .nav a svg { width:16px; height:16px; }
  .workspace { padding:0 13px 26px; }
  .topbar { height:47px; } .page-head { display:block; padding:23px 0 17px; }
  .head-note { display:inline-flex; margin-top:12px; }
  .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .stat:nth-child(2) { border-right:0; } .stat:nth-child(-n+2) { border-bottom:1px solid var(--line); }
  .result-overview { grid-template-columns:1fr; gap:12px; }
  .finding-detail { grid-template-columns:1fr; }
  .finding-tools { width:100%; } .finding-tools input { min-width:0; flex:1; }
  .subsection-head { align-items:flex-start; flex-direction:column; }
  .footer { flex-direction:column; }
}
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; scroll-behavior:auto!important; } }
</style>
</head>
<body>
<div class="shell">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg>
      </div>
      <div><div class="brand-name">SiteSentry</div><span class="brand-sub">SECURITY OPERATIONS</span></div>
    </div>
    <div class="nav-label">Workspace</div>
    <nav class="nav" aria-label="Main navigation">
      <a class="active" href="#overview" aria-current="page"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="8" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="15" width="7" height="6" rx="1"/></svg>Overview</a>
      <a href="#new-scan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="m16 16 4 4M11 7v8M7 11h8"/></svg>New assessment</a>
      <a href="#history-panel"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h10"/><circle cx="19" cy="17" r="2"/></svg>History</a>
      <a href="#results-panel"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 3h10l4 4v14H5z"/><path d="M14 3v5h5M8 13h8M8 17h8"/></svg>Findings & reports</a>
    </nav>
    <div class="sidebar-spacer"></div>
    <div class="engine-card">
      <div class="engine-head"><span class="engine-title">Scan engine</span><span class="engine-ready">Ready</span></div>
      <div class="engine-copy">16 passive checks · same-origin scope · bounded crawling</div>
    </div>
    <div class="sidebar-foot">SITESENTRY / LOCAL INSTANCE</div>
  </aside>

  <main class="workspace" id="overview">
    <header class="topbar">
      <div class="crumb"><span>Workspace</span><span class="crumb-sep">/</span><strong>Security overview</strong></div>
      <div class="top-actions"><span class="connection">Local engine</span><a class="docs-link" href="/docs" target="_blank" rel="noreferrer">API reference ↗</a></div>
    </header>

    <section class="page-head">
      <div>
        <div class="kicker"><span class="kicker-line"></span> WEB SECURITY / OPERATIONS</div>
        <h1>Security overview</h1>
        <p>One place to assess exposure, review findings and track remediation.</p>
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
              <span class="field-hint">Use the exact website origin you are authorized to assess.</span>
            </div>
            <div class="form-grid">
              <div class="field"><label for="max-pages">MAXIMUM PAGES</label><input id="max-pages" name="max_pages" type="number" min="1" max="500" value="50" required></div>
              <div class="field"><label for="max-depth">CRAWL DEPTH</label><input id="max-depth" name="max_depth" type="number" min="1" max="10" value="2" required></div>
              <div class="field full">
                <label for="api-key">API KEY <span class="field-hint">— if authentication is configured</span></label>
                <input id="api-key" type="password" placeholder="Bearer token (optional)" autocomplete="off">
              </div>
            </div>
            <label class="consent"><input id="permission" type="checkbox" required><span>I own this website or have explicit authorization to assess it. I understand the scanner will send HTTP requests to the target.</span></label>
            <div class="actions"><button class="primary" id="scan-button" type="submit">Start assessment&nbsp; ↗</button><span class="subtle">2 requests/sec default · 1 MB response cap</span></div>
          </form>
          <div class="status-banner" id="status-banner" role="status" aria-live="polite"></div>
        </div>
      </section>

      <section class="panel" id="history-panel">
        <div class="panel-head">
          <div class="panel-title"><span class="panel-index">02</span><div><h2>Recent assessments</h2><p>Saved results from this SiteSentry instance.</p></div></div>
          <button class="text-button" id="refresh-history" type="button">Refresh ↻</button>
        </div>
        <div class="panel-body">
          <div class="history-list" id="history-list"><div class="history-empty">Loading scan history…</div></div>
          <div class="history-footer"><span id="history-count">—</span><span>Newest first</span></div>
        </div>
      </section>

      <section class="panel" id="severity-panel">
        <div class="panel-head">
          <div class="panel-title"><span class="panel-index">03</span><div><h2>Severity profile</h2><p>Finding distribution for the selected scan.</p></div></div>
          <span class="section-tag">Live from results</span>
        </div>
        <div class="panel-body">
          <div class="severity-summary" id="severity-profile"><div class="severity-empty">Severity data will appear when a scan is selected.</div></div>
        </div>
      </section>

      <section class="panel" id="results-panel">
        <div class="panel-head">
          <div class="panel-title"><span class="panel-index">04</span><div><h2>Assessment detail</h2><p id="result-subtitle">Select a saved assessment or start a new scan.</p></div></div>
          <span class="section-tag" id="result-state">No scan selected</span>
        </div>
        <div class="panel-body" id="result-content">
          <div class="result-empty"><div><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="M9 12h6M12 9v6"/></svg></div><strong>No assessment selected</strong><div style="margin-top:5px">Start a scan to inspect its findings, evidence and recommended fixes.</div></div></div>
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
  const state = { selectedId:null, pollTimer:null, pollGeneration:0, findings:[] };
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
    if (kind === "loading") banner.append(node("span","spinner"));
    banner.append(node("span","",message));
  }

  function clearBanner() {
    $("status-banner").className = "status-banner";
    $("status-banner").replaceChildren();
  }

  async function api(path, options) {
    const config = options || {};
    const headers = new Headers(config.headers || {});
    const key = apiKeyInput.value.trim();
    if (key) headers.set("Authorization","Bearer " + key);
    if (config.body && !headers.has("Content-Type")) headers.set("Content-Type","application/json");
    const response = await fetch(path,{...config,headers});
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
    const labels = {pending:"Queued",running:"Scanning",completed:"Completed",failed:"Failed"};
    return labels[value] || value || "Unknown";
  }

  function gradeClass(grade) {
    if (grade === "A" || grade === "B") return "good";
    if (grade === "C") return "warn";
    if (grade === "D" || grade === "F") return "bad";
    return "";
  }

  function allFindings(data) {
    return (data.results || []).flatMap((check) => check.findings || []);
  }

  function severityCounts(findings) {
    const counts = {critical:0,high:0,medium:0,low:0,info:0};
    findings.forEach((finding) => {
      const key = String(finding.severity || "info").toLowerCase();
      counts[key] = (counts[key] || 0) + 1;
    });
    return counts;
  }

  function updateStats(data, findings) {
    const complete = data.status === "completed";
    $("stat-score").textContent = complete ? String(data.score) : "—";
    $("stat-grade").textContent = complete ? (data.grade || "—") : "—";
    $("stat-pages").textContent = complete ? String(data.page_count || 0) : "—";
    $("stat-findings").textContent = complete ? String(findings.length) : "—";
  }

  function addDetail(parent, label, value, extraClass) {
    if (value === undefined || value === null || value === "") return;
    const wrapper = node("div");
    wrapper.append(node("div","detail-label",label));
    wrapper.append(node("div","detail-value" + (extraClass ? " " + extraClass : ""),value));
    parent.append(wrapper);
  }

  function renderSeverity(findings) {
    const root = $("severity-profile");
    root.replaceChildren();
    if (!findings.length) {
      root.append(node("div","severity-empty","No findings to display for this scan."));
      return;
    }
    const counts = severityCounts(findings);
    const max = Math.max(1,...Object.values(counts));
    ["critical","high","medium","low","info"].forEach((severity) => {
      const row = node("div","sev-row");
      row.append(node("span","sev-name",severity));
      const track = node("div","sev-track");
      const fill = node("div","sev-fill " + severity);
      fill.style.width = (counts[severity] / max * 100) + "%";
      track.append(fill);
      row.append(track);
      row.append(node("span","sev-number",counts[severity]));
      root.append(row);
    });
    const legend = node("div","severity-legend");
    legend.append(node("span","",findings.length + " total findings"));
    legend.append(node("span","","Highest severity first"));
    root.append(legend);
  }

  function renderBreakdown(rows) {
    const wrapper = node("div","table-wrap");
    const table = node("table","breakdown");
    const thead = node("thead");
    const header = node("tr");
    ["Security check","Findings","Deduction"].forEach((label) => header.append(node("th","",label)));
    thead.append(header);
    table.append(thead);
    const tbody = node("tbody");
    (rows || []).forEach((row) => {
      const tr = node("tr");
      tr.append(node("td","",row.check_title || row.check_id));
      tr.append(node("td","",row.finding_count));
      tr.append(node("td","","-" + row.capped_deduction));
      tbody.append(tr);
    });
    table.append(tbody);
    wrapper.append(table);
    return wrapper;
  }

  function renderFindingTable(findings) {
    const wrapper = node("div");
    const tools = node("div","subsection-head");
    const left = node("div");
    left.append(node("h3","","Security findings"));
    left.append(node("span","count",findings.length + " issues detected"));
    tools.append(left);

    const controls = node("div","finding-tools");
    const search = node("input");
    search.type = "search";
    search.placeholder = "Search findings…";
    search.setAttribute("aria-label","Search findings");
    const filter = node("select");
    filter.setAttribute("aria-label","Filter by severity");
    [["all","All severities"],["critical","Critical"],["high","High"],["medium","Medium"],["low","Low"],["info","Informational"]].forEach(([value,label]) => {
      const option = node("option","",label);
      option.value = value;
      filter.append(option);
    });
    controls.append(search,filter);
    tools.append(controls);
    wrapper.append(tools);

    const tableWrap = node("div","table-wrap");
    const table = node("table","finding-table");
    const thead = node("thead");
    const header = node("tr");
    ["Finding","Severity","Action"].forEach((label) => header.append(node("th","",label)));
    thead.append(header);
    table.append(thead);
    const tbody = node("tbody");
    table.append(tbody);
    tableWrap.append(table);
    wrapper.append(tableWrap);

    function fillRows() {
      tbody.replaceChildren();
      const q = search.value.trim().toLowerCase();
      const sev = filter.value;
      const visible = findings.filter((finding) => {
        const level = String(finding.severity || "info").toLowerCase();
        const haystack = [finding.title,finding.check_id,finding.url,finding.evidence,finding.explanation].join(" ").toLowerCase();
        return (sev === "all" || level === sev) && (!q || haystack.includes(q));
      });
      if (!visible.length) {
        const row = node("tr");
        const cell = node("td","no-findings",findings.length ? "No findings match these filters." : "No findings were reported by the checks.");
        cell.colSpan = 3;
        row.append(cell);
        tbody.append(row);
        return;
      }
      visible.forEach((finding,index) => {
        const row = node("tr");
        const titleCell = node("td");
        titleCell.append(node("span","finding-main",finding.title || "Security finding"));
        titleCell.append(node("span","finding-sub",(finding.check_id || "check") + " · " + (finding.url || "")));
        row.append(titleCell);
        const severityCell = node("td");
        severityCell.append(node("span","severity " + String(finding.severity || "info").toLowerCase(),finding.severity || "info"));
        row.append(severityCell);
        const actionCell = node("td");
        const inspect = node("button","inspect-button","Inspect");
        inspect.type = "button";
        inspect.setAttribute("aria-expanded","false");
        actionCell.append(inspect);
        row.append(actionCell);
        tbody.append(row);

        const detailRow = node("tr","finding-detail-row");
        detailRow.hidden = true;
        const detailCell = node("td");
        detailCell.colSpan = 3;
        const detail = node("div","finding-detail");
        addDetail(detail,"Evidence",finding.evidence);
        addDetail(detail,"Why it matters",finding.explanation);
        addDetail(detail,"Recommended fix",finding.fix,"fix-value");
        detailCell.append(detail);
        detailRow.append(detailCell);
        tbody.append(detailRow);

        inspect.addEventListener("click",() => {
          detailRow.hidden = !detailRow.hidden;
          inspect.setAttribute("aria-expanded",String(!detailRow.hidden));
          inspect.textContent = detailRow.hidden ? "Inspect" : "Close";
        });
      });
    }
    search.addEventListener("input",fillRows);
    filter.addEventListener("change",fillRows);
    fillRows();
    return wrapper;
  }

  async function downloadReport(scanId,format,button) {
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
      window.setTimeout(() => URL.revokeObjectURL(objectUrl),1000);
    } catch (error) {
      setBanner("Could not download report: " + error.message,"error");
    } finally {
      button.disabled = false;
      button.textContent = previous;
    }
  }

  function renderResult(data) {
    state.selectedId = data.scan_id;
    const findings = allFindings(data);
    state.findings = findings;
    updateStats(data,findings);
    renderSeverity(data.status === "completed" ? findings : []);
    $("result-subtitle").textContent = data.target_url || "Scan details";
    $("result-state").textContent = statusText(data.status);
    const content = $("result-content");
    content.replaceChildren();

    const top = node("div","result-top");
    const gradeWrap = node("div","grade-wrap");
    gradeWrap.append(node("div","grade " + gradeClass(data.grade),data.status === "completed" ? (data.grade || "—") : "…"));
    const titleBlock = node("div");
    titleBlock.append(node("div","result-title",data.status === "completed" ? "Security assessment complete" : "Assessment " + statusText(data.status).toLowerCase()));
    titleBlock.append(node("div","result-meta",data.target_url || ""));
    titleBlock.append(node("div","result-meta","Scan ID: " + (data.scan_id || "") + " · Started " + dateText(data.started_at)));
    gradeWrap.append(titleBlock);
    top.append(gradeWrap);
    top.append(node("span","pill",statusText(data.status)));
    content.append(top);

    const progress = node("div","score-track");
    const progressFill = node("div","score-fill");
    progressFill.style.width = (data.status === "completed" ? Math.max(0,Math.min(100,Number(data.score)||0)) : 0) + "%";
    progress.append(progressFill);
    content.append(progress);

    if (data.status === "pending" || data.status === "running") {
      const message = node("div","status-banner visible");
      message.append(node("span","spinner"));
      message.append(node("span","",data.status === "pending" ? "Waiting for an available scan worker…" : "The scanner is crawling the target and running its passive checks. This view refreshes automatically."));
      content.append(message);
      return;
    }
    if (data.status === "failed") {
      content.append(node("div","status-banner visible error","This scan failed. Check the API server logs for the underlying error."));
      (data.errors || []).forEach((error) => addDetail(content,"Scan error",error));
      return;
    }

    const overview = node("div","result-overview");
    const scoreBlock = node("div","score-block");
    const orbit = node("div","score-orbit");
    orbit.style.setProperty("--score",Math.max(0,Math.min(100,Number(data.score)||0)) + "%");
    orbit.append(node("span","",String(data.score)));
    scoreBlock.append(orbit);
    const scoreCaption = node("div");
    scoreCaption.append(node("div","result-title","Overall score"));
    scoreCaption.append(node("div","score-caption","Calculated from detected findings"));
    scoreBlock.append(scoreCaption);
    overview.append(scoreBlock);

    const resultStats = node("div","result-stats");
    [[String(data.page_count || 0),"Pages scanned"],[String(findings.length),"Total findings"],[String((data.results || []).filter((item) => !item.error && !item.incomplete).length),"Checks completed"]].forEach(([value,label]) => {
      const stat = node("div","result-stat");
      stat.append(node("strong","",value));
      stat.append(node("span","",label));
      resultStats.append(stat);
    });
    overview.append(resultStats);
    content.append(overview);

    const actions = node("div","report-actions");
    [["html","HTML"],["md","Markdown"],["json","JSON"],["sarif","SARIF"]].forEach(([format,label]) => {
      const button = node("button","report-btn","Download " + label);
      button.type = "button";
      button.addEventListener("click",() => downloadReport(data.scan_id,format,button));
      actions.append(button);
    });
    content.append(actions);

    content.append(renderFindingTable(findings));

    const breakdownSection = node("section","subsection");
    const breakdownHead = node("div","subsection-head");
    breakdownHead.append(node("h3","","Check-by-check score"));
    breakdownHead.append(node("span","count",(data.breakdown || []).length + " checks"));
    breakdownSection.append(breakdownHead);
    breakdownSection.append(renderBreakdown(data.breakdown));
    content.append(breakdownSection);

    if (data.has_incomplete_checks) {
      content.append(node("div","status-banner visible error","Some checks did not complete. Review the check results before relying on this grade."));
    }
  }

  function renderHistory(items) {
    const list = $("history-list");
    list.replaceChildren();
    $("history-count").textContent = items.length + " saved scan" + (items.length === 1 ? "" : "s");
    if (!items.length) {
      list.append(node("div","history-empty","No saved scans yet. Completed assessments will appear here."));
      return;
    }
    items.forEach((item) => {
      const button = node("button","history-item" + (item.scan_id === state.selectedId ? " active" : ""));
      button.type = "button";
      button.append(node("span","history-grade",item.status === "completed" ? (item.grade || "—") : "…"));
      const text = node("span","history-text");
      text.append(node("span","history-url",item.target_url));
      text.append(node("span","history-date",dateText(item.started_at) + " · " + statusText(item.status)));
      button.append(text);
      if (item.status === "completed") button.append(node("span","history-score",item.score + "/100"));
      button.addEventListener("click",() => openScan(item.scan_id));
      list.append(button);
    });
  }

  async function refreshHistory() {
    try {
      const response = await api("/api/v1/scans?limit=30");
      renderHistory(await response.json());
    } catch (error) {
      $("history-list").replaceChildren(node("div","history-empty","Could not load history: " + error.message));
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
      setBanner("Could not load scan: " + error.message,"error");
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
          state.pollTimer = window.setTimeout(poll,2000);
        } else {
          state.pollTimer = null;
          setBanner(data.status === "completed" ? "Assessment complete. Review the findings and recommended fixes below." : "Assessment finished with an error. Review the server logs.",data.status === "completed" ? "success" : "error");
          await refreshHistory();
        }
      } catch (error) {
        if (generation === state.pollGeneration) {
          setBanner("Status refresh failed: " + error.message,"error");
          state.pollTimer = window.setTimeout(poll,4000);
        }
      }
    };
    state.pollTimer = window.setTimeout(poll,1200);
  }

  $("scan-form").addEventListener("submit",async (event) => {
    event.preventDefault();
    if (!$("scan-form").reportValidity()) return;
    const button = $("scan-button");
    button.disabled = true;
    button.textContent = "Submitting…";
    stopPolling();
    clearBanner();
    try {
      const body = {
        url:$("target-url").value.trim(),
        confirm_permission:$("permission").checked,
        max_pages:Number($("max-pages").value),
        max_depth:Number($("max-depth").value),
        ignore_robots:false,
        allow_private:false
      };
      const response = await api("/api/v1/scans",{method:"POST",body:JSON.stringify(body)});
      const accepted = await response.json();
      setBanner("Assessment accepted. Waiting for the scanner to begin…","loading");
      await refreshHistory();
      await openScan(accepted.id);
      watchScan(accepted.id);
    } catch (error) {
      setBanner("Could not start assessment: " + error.message,"error");
    } finally {
      button.disabled = false;
      button.textContent = "Start assessment ↗";
    }
  });

  $("refresh-history").addEventListener("click",refreshHistory);
  apiKeyInput.addEventListener("change",refreshHistory);
  refreshHistory();
})();
</script>
"""
