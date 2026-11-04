"""Self-contained SiteSentry web dashboard."""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>SiteSentry — Website Security Assessment</title>
<style>
:root {
  color-scheme: light;
  --canvas:#f3f6f8; --surface:rgba(255,255,255,.82); --surface-solid:#fff;
  --surface-soft:#f8fafb; --ink:#111a22; --muted:#627181; --quiet:#8c99a5;
  --line:#e1e8ed; --line-strong:#d4dee5; --green:#24a148; --green-deep:#16843a;
  --green-soft:#e4f5e9; --red:#dc3d4d; --red-soft:#fff0f1;
  --orange:#e87524; --orange-soft:#fff3e9; --yellow:#bd8b12; --yellow-soft:#fff8df;
  --blue:#3284d6; --blue-soft:#edf5ff; --shadow:0 12px 34px rgba(25,45,62,.055),0 2px 7px rgba(25,45,62,.035);
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  margin:0; min-height:100vh; color:var(--ink); background:
    radial-gradient(ellipse at 1% 100%,rgba(191,246,215,.38),transparent 28%),
    radial-gradient(ellipse at 100% 0%,rgba(217,232,255,.42),transparent 30%),var(--canvas);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Inter,sans-serif;
  -webkit-font-smoothing:antialiased;
}
button,input,select { font:inherit; }
button,a { -webkit-tap-highlight-color:transparent; }
button { cursor:pointer; }
a { color:inherit; }
.shell { min-height:100vh; display:grid; grid-template-columns:270px minmax(0,1fr); }
.sidebar {
  position:sticky; top:0; height:100vh; padding:18px 17px 16px; display:flex; flex-direction:column;
  overflow:hidden; background:rgba(250,252,253,.76); border-right:1px solid rgba(216,226,233,.92);
  backdrop-filter:blur(24px); -webkit-backdrop-filter:blur(24px);
}
.window-controls { display:flex; gap:8px; padding:1px 7px 25px; }
.window-dot { width:13px; height:13px; border-radius:50%; box-shadow:inset 0 0 0 1px rgba(0,0,0,.06); }
.window-dot.red { background:#ff5f57; } .window-dot.yellow { background:#febc2e; } .window-dot.green { background:#28c840; }
.brand { display:flex; align-items:center; gap:12px; padding:0 10px 25px; }
.brand-mark {
  display:grid; place-items:center; width:48px; height:48px; flex:none; border-radius:14px;
  color:#fff; background:linear-gradient(145deg,#39c96b,#168a42); box-shadow:0 7px 16px rgba(36,161,72,.19);
}
.brand-mark svg { width:28px; height:28px; }
.brand-name { color:#101820; font-size:20px; font-weight:760; letter-spacing:-.055em; line-height:1.1; }
.brand-sub { display:block; margin-top:4px; color:#718090; font-size:11px; font-weight:550; }
.nav-label { padding:15px 13px 8px; color:#9aa6b0; font-size:9px; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }
.nav { display:grid; gap:5px; }
.nav a {
  display:flex; align-items:center; gap:13px; padding:11px 13px; border-radius:15px;
  color:#334353; text-decoration:none; font-size:14px; font-weight:620; transition:background .16s,color .16s,transform .16s;
}
.nav a svg { width:19px; height:19px; flex:none; stroke:currentColor; }
.nav a:hover { background:rgba(224,235,242,.72); color:#10251a; }
.nav a.active { color:#135b2b; background:linear-gradient(100deg,#dcf4e5,#d5f0df); box-shadow:inset 0 0 0 1px rgba(67,174,98,.04); }
.nav a.active svg { color:#16843a; }
.sidebar-spacer { flex:1; min-height:22px; }
.engine-card { margin:0 4px; padding:13px; border:1px solid #dce9df; border-radius:14px; background:rgba(244,251,246,.88); }
.engine-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.engine-title { color:#273b30; font-size:11px; font-weight:750; }
.engine-ready { display:inline-flex; align-items:center; gap:6px; color:#268747; font-size:9px; font-weight:850; letter-spacing:.08em; text-transform:uppercase; }
.engine-ready:before { content:""; width:6px; height:6px; border-radius:50%; background:#31b65c; box-shadow:0 0 0 3px #d9f2df; }
.engine-copy { margin-top:7px; color:#77887d; font-size:10px; line-height:1.5; }
.sidebar-foot { padding:13px 9px 0; color:#9ba8a9; font-size:8px; font-weight:700; letter-spacing:.1em; }
.workspace { min-width:0; max-width:1800px; width:100%; padding:0 clamp(22px,3vw,54px) 34px; margin:0 auto; }
.topbar { height:64px; display:flex; align-items:center; justify-content:space-between; gap:16px; border-bottom:1px solid rgba(216,226,233,.8); color:var(--muted); font-size:11px; }
.crumb { display:flex; align-items:center; gap:9px; }
.crumb strong { color:#354556; font-weight:700; }
.crumb-sep { color:#b7c2ca; }
.top-actions { display:flex; align-items:center; gap:12px; }
.connection { display:inline-flex; align-items:center; gap:7px; padding:6px 10px; border:1px solid #dce9df; border-radius:99px; color:#278348; background:rgba(245,251,246,.8); font-size:9px; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }
.connection:before { content:""; width:6px; height:6px; border-radius:50%; background:#31b65c; }
.docs-link,.icon-link { color:#526477; text-decoration:none; font-size:11px; font-weight:700; }
.docs-link:hover,.icon-link:hover { color:var(--green-deep); }
.avatar { display:grid; place-items:center; width:32px; height:32px; border:1px solid #d9e2e8; border-radius:50%; color:#334658; background:rgba(255,255,255,.76); font-size:13px; font-weight:700; }
.page-head { padding:29px 0 24px; }
.kicker { display:none; }
h1 { margin:0 0 5px; color:#101820; font-size:clamp(28px,3vw,39px); line-height:1.13; font-weight:760; letter-spacing:-.055em; }
.page-head p { margin:0; color:#637285; font-size:15px; }
.head-note { display:none; }
.panel {
  min-width:0; overflow:hidden; border:1px solid rgba(255,255,255,.92); border-radius:20px;
  background:var(--surface); box-shadow:var(--shadow); backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
}
.panel-head { min-height:60px; display:flex; align-items:center; justify-content:space-between; gap:14px; padding:14px 21px; border-bottom:1px solid rgba(222,231,236,.78); }
.panel-title { display:flex; align-items:center; gap:10px; min-width:0; }
.panel-index { display:none; }
.panel-head h2 { margin:0; color:#17212b; font-size:17px; letter-spacing:-.035em; font-weight:730; }
.panel-head p { margin:3px 0 0; color:#7d8996; font-size:11px; }
.section-tag { color:#87939e; font-size:9px; font-weight:800; letter-spacing:.09em; text-transform:uppercase; white-space:nowrap; }
.panel-body { padding:19px 21px; }
#new-scan { margin-bottom:18px; }
#new-scan .panel-head { display:none; }
#new-scan .panel-body { padding:19px 23px 16px; }
#scan-form { display:grid; grid-template-columns:minmax(280px,1fr) 150px 150px auto; align-items:end; gap:14px; }
.field { display:grid; gap:7px; min-width:0; }
.field.full { grid-column:1/-1; }
label { color:#334456; font-size:11px; font-weight:700; }
input[type=url],input[type=password],input[type=number],select {
  width:100%; min-width:0; padding:12px 14px; border:1px solid var(--line-strong); border-radius:13px;
  outline:none; color:#18232e; background:rgba(255,255,255,.78); font-size:13px;
  box-shadow:inset 0 1px 2px rgba(30,52,68,.025); transition:border .15s,box-shadow .15s,background .15s;
}
input:focus,select:focus { border-color:#85c99a; background:#fff; box-shadow:0 0 0 4px rgba(36,161,72,.11); }
input::placeholder { color:#9aa6b3; }
.field-hint { color:#98a4af; font-size:9px; font-weight:500; }
.form-grid { display:contents; }
#api-options { grid-column:1 / -1; margin-top:1px; }
#api-options summary { color:#657688; font-size:10px; font-weight:650; cursor:pointer; }
#api-options .field { margin-top:9px; max-width:480px; }
.consent {
  grid-column:1 / 4; display:flex; align-items:flex-start; gap:9px; padding:0 2px;
  color:#728091; font-size:10px; line-height:1.45; font-weight:500;
}
.consent input { margin:2px 0 0; accent-color:var(--green); flex:none; }
.actions { display:flex; align-items:center; justify-content:flex-end; gap:10px; }
.primary {
  min-width:150px; padding:12px 19px; border:1px solid #1f9b47; border-radius:13px; color:#fff;
  background:linear-gradient(180deg,#31b85a,#209b46); box-shadow:0 7px 14px rgba(35,164,72,.17);
  font-size:13px; font-weight:730; transition:transform .16s,box-shadow .16s,filter .16s;
}
.primary:hover { transform:translateY(-1px); filter:brightness(1.03); box-shadow:0 9px 18px rgba(35,164,72,.21); }
.primary:disabled { opacity:.55; cursor:wait; transform:none; }
.subtle { color:#98a4ae; font-size:9px; }
.status-banner { display:none; align-items:center; gap:9px; margin-top:13px; padding:10px 12px; border:1px solid #dce7ed; border-radius:11px; background:#f8fbfc; color:#506273; font-size:11px; }
.status-banner.visible { display:flex; }
.status-banner.error { border-color:#f3d0d4; background:var(--red-soft); color:#b92e3c; }
.status-banner.success { border-color:#cfead7; background:#f0faf3; color:#24783e; }
.spinner { width:13px; height:13px; flex:none; border:2px solid #dce8df; border-top-color:#269d49; border-radius:50%; animation:spin .8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.summary-grid { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:18px; margin-bottom:18px; }
.feature-card { min-height:240px; }
.feature-card .panel-body { min-height:180px; }
.latest-layout { display:flex; align-items:center; gap:28px; min-height:135px; }
.score-orbit {
  --score:0%; display:grid; place-items:center; position:relative; width:132px; height:132px; flex:none;
  border-radius:50%; background:conic-gradient(#26b34f var(--score),#e5ebef 0);
  box-shadow:inset 0 0 0 1px rgba(38,179,79,.04);
}
.score-orbit:before { content:""; position:absolute; inset:10px; border-radius:50%; background:#fff; }
.score-orbit span { position:relative; z-index:1; color:#111a22; font-size:36px; font-weight:760; letter-spacing:-.07em; line-height:1; }
.score-orbit small { position:absolute; z-index:1; transform:translateY(28px); color:#82909e; font-size:12px; }
.latest-copy { min-width:0; }
.latest-copy h3 { margin:0 0 4px; color:#17212b; font-size:16px; font-weight:730; letter-spacing:-.03em; }
.latest-copy p { margin:0 0 13px; color:#748295; font-size:11px; overflow-wrap:anywhere; }
.grade-line { display:flex; align-items:center; gap:10px; margin:7px 0 10px; }
.grade-label { color:#283746; font-size:14px; font-weight:720; }
.grade {
  display:inline-grid; place-items:center; min-width:42px; height:38px; padding:0 10px;
  border-radius:99px; background:#e5f7e9; color:#168c3d; font-size:22px; font-weight:800;
}
.grade.warn { background:#fff5dd; color:#a9790a; }
.grade.bad { background:#fff0f0; color:#c83645; }
.latest-summary { max-width:300px; color:#69788a; font-size:12px; line-height:1.5; }
.latest-status { display:inline-flex; margin-top:9px; padding:4px 9px; border-radius:99px; color:#258146; background:#e9f7ec; font-size:9px; font-weight:800; }
.severity-layout { display:grid; grid-template-columns:190px minmax(0,1fr); gap:19px; align-items:center; min-height:140px; }
.donut {
  --segments:conic-gradient(#e6ebef 0 100%); position:relative; display:grid; place-items:center;
  width:154px; height:154px; margin:auto; border-radius:50%; background:var(--segments);
}
.donut:before { content:""; position:absolute; inset:17px; border-radius:50%; background:#fff; }
.donut-center { position:relative; z-index:1; text-align:center; }
.donut-total { display:block; color:#101820; font-size:31px; font-weight:760; letter-spacing:-.06em; line-height:1.1; }
.donut-label { display:block; margin-top:3px; color:#788697; font-size:11px; }
.severity-legend { display:grid; gap:9px; }
.severity-item { display:grid; grid-template-columns:11px 1fr auto; gap:9px; align-items:center; color:#344454; font-size:12px; }
.severity-dot { width:10px; height:10px; border-radius:50%; }
.severity-item strong { color:#17212b; font-weight:720; font-variant-numeric:tabular-nums; }
.severity-item.critical .severity-dot { background:var(--red); }
.severity-item.high .severity-dot { background:var(--orange); }
.severity-item.medium .severity-dot { background:#f2c230; }
.severity-item.low .severity-dot { background:#4a9bea; }
.severity-item.info .severity-dot { background:#aeb9c4; }
.severity-empty { color:#81909d; font-size:11px; text-align:center; }
.metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-bottom:18px; }
.stat {
  display:flex; align-items:center; gap:14px; min-width:0; min-height:92px; padding:15px 17px;
  border:1px solid rgba(255,255,255,.94); border-radius:18px; background:var(--surface); box-shadow:var(--shadow);
}
.stat-icon { display:grid; place-items:center; width:48px; height:48px; flex:none; border-radius:50%; color:#536578; background:#f0f4f6; }
.stat-icon svg { width:23px; height:23px; stroke:currentColor; }
.stat-icon.green { color:#188b3b; background:#e7f8eb; }
.stat-icon.amber { color:#c48b0c; background:#fff7df; }
.stat-copy { min-width:0; }
.stat-label { color:#647385; font-size:11px; font-weight:550; }
.stat-value { margin-top:1px; color:#101820; font-size:23px; line-height:1.2; font-weight:760; letter-spacing:-.045em; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stat-sub { display:none; }
#history-panel { margin-bottom:18px; }
#history-panel .panel-head { min-height:51px; }
#history-panel .panel-body { padding:10px 18px 13px; }
.history-list { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:9px; }
.history-item {
  display:flex; align-items:center; gap:10px; width:100%; min-width:0; padding:10px 11px;
  border:1px solid #e8edf0; border-radius:12px; background:rgba(255,255,255,.58); color:var(--ink); text-align:left;
  transition:border .15s,background .15s,transform .15s;
}
.history-item:hover,.history-item.active { border-color:#b8e3c4; background:#f1fbf4; transform:translateY(-1px); }
.history-grade {
  display:grid; place-items:center; flex:none; width:34px; height:34px; border-radius:10px;
  color:#218846; background:#e8f6eb; font-size:14px; font-weight:800;
}
.history-text { min-width:0; flex:1; }
.history-url { display:block; overflow:hidden; color:#233342; font-size:11px; font-weight:700; text-overflow:ellipsis; white-space:nowrap; }
.history-date { display:block; margin-top:2px; color:#8794a0; font-size:9px; }
.history-score { color:#287d43; font-size:10px; font-weight:800; white-space:nowrap; }
.history-empty { grid-column:1/-1; padding:12px 4px; color:#8a97a2; font-size:11px; }
.history-footer { display:none; }
.text-button { padding:4px 0; border:0; background:transparent; color:#268846; font-size:10px; font-weight:750; }
.text-button:hover { color:#14672e; text-decoration:underline; }
#results-panel { margin-top:0; }
#results-panel .panel-head { min-height:57px; }
#results-panel .panel-body { padding:0 20px 21px; }
.result-empty { display:grid; place-items:center; min-height:205px; padding:30px; color:#8a97a2; text-align:center; font-size:12px; }
.empty-icon { display:grid; place-items:center; width:47px; height:47px; margin-bottom:12px; border-radius:15px; color:#269b4a; background:#eaf7ed; }
.empty-icon svg { width:24px; height:24px; }
.result-top { display:flex; align-items:center; justify-content:space-between; gap:14px; flex-wrap:wrap; padding:17px 0 13px; }
.grade-wrap { display:flex; align-items:center; gap:12px; }
.result-title { color:#18232e; font-size:13px; font-weight:750; }
.result-meta { margin-top:3px; color:#83909d; font-size:10px; overflow-wrap:anywhere; }
.pill { display:inline-flex; align-items:center; padding:5px 10px; border:1px solid #dce9df; border-radius:99px; color:#278348; background:#eff9f1; font-size:9px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; }
.score-track { height:6px; margin:0 0 15px; overflow:hidden; border-radius:99px; background:#e8edf0; }
.score-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,#43c96c,#199943); width:0%; transition:width .3s; }
.report-actions { display:flex; gap:8px; flex-wrap:wrap; padding:0 0 14px; }
.report-btn { padding:7px 11px; border:1px solid #dce5ea; border-radius:9px; color:#526477; background:#fff; font-size:10px; font-weight:700; transition:border .15s,color .15s,background .15s; }
.report-btn:hover { border-color:#b9dfc3; color:#187b36; background:#f5fbf6; }
.report-btn:disabled { opacity:.5; cursor:wait; }
.result-overview { display:none; }
.tabs { display:flex; align-items:center; gap:28px; border-bottom:1px solid #e4eaee; }
.tab {
  position:relative; padding:12px 4px 11px; border:0; color:#718092; background:transparent;
  font-size:12px; font-weight:650;
}
.tab:hover { color:#243849; }
.tab.active { color:#16232d; font-weight:760; }
.tab.active:after { content:""; position:absolute; left:0; right:0; bottom:-1px; height:3px; border-radius:99px; background:#26a34c; }
.tab-content { padding-top:13px; }
.subsection { margin-top:17px; }
.subsection-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:10px; }
.subsection-head h3 { margin:0; color:#1a2733; font-size:13px; font-weight:750; }
.count { color:#8a97a2; font-size:10px; }
.finding-tools { display:flex; align-items:center; gap:8px; }
.finding-tools input,.finding-tools select { width:auto; padding:9px 12px; border-radius:11px; font-size:11px; }
.finding-tools input { min-width:210px; }
.table-wrap { width:100%; overflow-x:auto; }
.finding-table { width:100%; border-collapse:collapse; min-width:590px; }
.finding-table th { padding:10px 11px; border-bottom:1px solid #e8edf0; color:#8793a0; background:#fafcfd; font-size:9px; letter-spacing:.1em; text-align:left; text-transform:uppercase; }
.finding-table td { padding:12px 11px; border-bottom:1px solid #edf1f3; color:#435465; font-size:11px; vertical-align:middle; }
.finding-table tr:last-child td { border-bottom:0; }
.finding-table tbody tr:hover td { background:#fbfdfc; }
.finding-main { color:#1e2b37; font-size:11px; font-weight:730; }
.finding-sub { display:block; max-width:650px; margin-top:3px; overflow:hidden; color:#8794a0; font-size:9px; text-overflow:ellipsis; white-space:nowrap; }
.severity {
  display:inline-flex; align-items:center; padding:5px 9px; border-radius:99px;
  color:#657384; background:#f0f3f5; font-size:9px; font-weight:800; letter-spacing:.025em;
}
.severity.high,.severity.critical { color:#c52e3b; background:#ffe8ea; }
.severity.medium { color:#a56c05; background:#fff3d3; }
.severity.low { color:#236fae; background:#e8f3ff; }
.severity.info { color:#69798a; background:#eef2f5; }
.inspect-button { padding:6px 9px; border:1px solid #dce5e9; border-radius:9px; color:#2a8345; background:#fff; font-size:10px; font-weight:700; }
.inspect-button:hover { border-color:#addcba; background:#f2faf4; }
.finding-detail-row td { padding:0 11px 12px; background:#fbfdfc; }
.finding-detail { display:grid; grid-template-columns:1fr 1fr 1fr; gap:15px; padding:13px; border:1px solid #e5ecef; border-radius:12px; background:#f7fafb; }
.detail-label { margin-bottom:4px; color:#84919d; font-size:8px; font-weight:850; letter-spacing:.1em; text-transform:uppercase; }
.detail-value { color:#455767; font-size:10px; overflow-wrap:anywhere; white-space:pre-wrap; }
.fix-value { color:#257a40; }
.no-findings { padding:25px 10px !important; color:#83919d !important; text-align:center; font-size:11px !important; }
.breakdown { width:100%; border-collapse:collapse; font-size:11px; }
.breakdown th { padding:10px; border-bottom:1px solid #e7ecef; color:#8895a1; font-size:9px; letter-spacing:.1em; text-align:left; text-transform:uppercase; }
.breakdown td { padding:10px; border-bottom:1px solid #eef2f4; color:#465767; }
.breakdown td:last-child,.breakdown th:last-child { text-align:right; }
.breakdown tr:last-child td { border-bottom:0; }
.check-status { display:inline-flex; padding:4px 8px; border-radius:99px; color:#277a42; background:#eaf7ed; font-size:9px; font-weight:750; }
.check-status.findings { color:#a56c05; background:#fff4d9; }
.check-status.incomplete { color:#c52e3b; background:#ffeaec; }
.details-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:11px; }
.detail-card { padding:12px 13px; border:1px solid #e6ecef; border-radius:12px; background:#fbfcfd; }
.detail-card .detail-label { margin-bottom:5px; }
.detail-card .detail-value { color:#263746; font-size:11px; }
.footer { display:flex; justify-content:space-between; gap:12px; padding-top:18px; color:#9aa6af; font-size:8px; font-weight:700; letter-spacing:.08em; }
@media (max-width:1120px) {
  .shell { grid-template-columns:225px minmax(0,1fr); }
  .workspace { padding-left:22px; padding-right:22px; }
  #scan-form { grid-template-columns:minmax(220px,1fr) 125px 125px auto; gap:10px; }
  .severity-layout { grid-template-columns:150px minmax(0,1fr); gap:12px; }
  .donut { width:130px; height:130px; }
  .history-list { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
@media (max-width:820px) {
  .shell { grid-template-columns:1fr; }
  .sidebar { position:relative; height:auto; padding:10px 14px; flex-direction:row; align-items:center; gap:12px; overflow:visible; }
  .window-controls,.nav-label,.sidebar-spacer,.engine-card,.sidebar-foot { display:none; }
  .brand { padding:0; margin-right:auto; }
  .brand-mark { width:36px; height:36px; border-radius:11px; }
  .brand-name { font-size:15px; } .brand-sub { font-size:9px; }
  .nav { display:flex; gap:2px; }
  .nav a { padding:8px; font-size:0; border-radius:10px; }
  .nav a svg { width:19px; height:19px; }
  .summary-grid { grid-template-columns:1fr; }
  .feature-card { min-height:0; }
  .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }
  #scan-form { grid-template-columns:minmax(0,1fr) 120px 120px; }
  .actions { grid-column:1/-1; justify-content:flex-start; }
  .consent { grid-column:1/-1; }
  #api-options { grid-column:1/-1; }
  .history-list { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
@media (max-width:560px) {
  .workspace { padding:0 12px 24px; }
  .topbar { height:49px; }
  .top-actions { gap:7px; } .connection { display:none; }
  .page-head { padding:22px 0 17px; } h1 { font-size:27px; }
  .page-head p { font-size:12px; }
  #new-scan .panel-body { padding:15px; }
  #scan-form { grid-template-columns:1fr 1fr; gap:10px; }
  #scan-form .field:first-child { grid-column:1/-1; }
  .actions { grid-column:1/-1; }
  .primary { width:100%; }
  .consent { font-size:9px; }
  .summary-grid { gap:12px; }
  .panel { border-radius:16px; }
  .panel-body { padding:15px; }
  .latest-layout { gap:15px; }
  .score-orbit { width:105px; height:105px; }
  .score-orbit span { font-size:29px; }
  .score-orbit small { transform:translateY(23px); }
  .severity-layout { grid-template-columns:115px minmax(0,1fr); gap:9px; }
  .donut { width:108px; height:108px; }
  .donut:before { inset:13px; }
  .donut-total { font-size:24px; }
  .severity-item { font-size:10px; gap:6px; }
  .metrics { gap:8px; }
  .stat { min-height:77px; gap:9px; padding:10px; border-radius:14px; }
  .stat-icon { width:36px; height:36px; }
  .stat-icon svg { width:18px; }
  .stat-value { font-size:19px; }
  .stat-label { font-size:9px; }
  .history-list { grid-template-columns:1fr; }
  .tabs { gap:17px; }
  .tab { font-size:11px; }
  .subsection-head { align-items:flex-start; flex-direction:column; }
  .finding-tools { width:100%; }
  .finding-tools input { flex:1; min-width:0; }
  .finding-tools select { max-width:135px; }
  .finding-detail,.details-grid { grid-template-columns:1fr; }
  .footer { flex-direction:column; }
}
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; scroll-behavior:auto!important; } }
</style>
</head>
<body>
<div class="shell">
  <aside class="sidebar">
    <div class="window-controls" aria-hidden="true"><span class="window-dot red"></span><span class="window-dot yellow"></span><span class="window-dot green"></span></div>
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg>
      </div>
      <div><div class="brand-name">SiteSentry</div><span class="brand-sub">Web Security Scanner</span></div>
    </div>
    <div class="nav-label">Workspace</div>
    <nav class="nav" aria-label="Main navigation">
      <a class="active" href="#overview" aria-current="page"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 10 9-7 9 7"/><path d="M5 9v11h5v-6h4v6h5V9"/></svg>Overview</a>
      <a href="#new-scan"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4.5v15L19 12 7 4.5Z"/></svg>Scan</a>
      <a href="#history-panel"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M4 12h16M4 17h10"/><circle cx="19" cy="17" r="2"/></svg>Assessments</a>
      <a href="#results-panel"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 21 19H3L12 3Z"/><path d="M12 9v4m0 3h.01"/></svg>Findings</a>
      <a href="#results-panel"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h7"/></svg>Reports</a>
      <a href="/docs" target="_blank" rel="noreferrer"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m8 8-4 4 4 4m8-8 4 4-4 4m-2-11-4 14"/></svg>API</a>
    </nav>
    <div class="sidebar-spacer"></div>
    <div class="engine-card">
      <div class="engine-head"><span class="engine-title">Scan engine</span><span class="engine-ready">Ready</span></div>
      <div class="engine-copy">16 passive checks · same-origin scope · bounded crawling</div>
    </div>
    <div class="sidebar-foot">SITESENTRY · LOCAL INSTANCE</div>
  </aside>

  <main class="workspace" id="overview">
    <header class="topbar">
      <div class="crumb"><span>Workspace</span><span class="crumb-sep">/</span><strong>Overview</strong></div>
      <div class="top-actions"><span class="connection">Local engine</span><a class="docs-link" href="/docs" target="_blank" rel="noreferrer">API reference ↗</a><span class="avatar" aria-label="SiteSentry">S</span></div>
    </header>

    <section class="page-head">
      <div>
        <h1>Website Security Assessment</h1>
        <p>Scan websites, identify vulnerabilities and get actionable security guidance.</p>
      </div>
    </section>

    <section class="panel" id="new-scan">
      <div class="panel-head"><div class="panel-title"><h2>Start a new scan</h2><p>Configure a bounded assessment of an authorized website.</p></div></div>
      <div class="panel-body">
        <form id="scan-form">
          <div class="field">
            <label for="target-url">Target Website</label>
            <input id="target-url" name="url" type="url" placeholder="https://example.com" autocomplete="url" required>
          </div>
          <div class="field">
            <label for="max-pages">Max Pages</label>
            <input id="max-pages" name="max_pages" type="number" min="1" max="500" value="50" required>
          </div>
          <div class="field">
            <label for="max-depth">Max Depth</label>
            <input id="max-depth" name="max_depth" type="number" min="1" max="10" value="2" required>
          </div>
          <div class="actions"><button class="primary" id="scan-button" type="submit">▷ &nbsp; Start Scan</button></div>
          <label class="consent"><input id="permission" type="checkbox" required><span>I own this website or have explicit authorization to assess it. I understand SiteSentry will send HTTP requests to the target.</span></label>
          <details id="api-options">
            <summary>Advanced · API key (only when authentication is configured)</summary>
            <div class="field"><input id="api-key" type="password" placeholder="Bearer token (optional)" autocomplete="off" aria-label="API key"></div>
          </details>
        </form>
        <div class="status-banner" id="status-banner" role="status" aria-live="polite"></div>
      </div>
    </section>

    <div class="summary-grid">
      <section class="panel feature-card" id="latest-panel">
        <div class="panel-head"><div class="panel-title"><h2>Latest Assessment</h2></div><span class="section-tag" id="latest-status">No scan yet</span></div>
        <div class="panel-body">
          <div class="latest-layout">
            <div class="score-orbit" id="latest-score-ring" style="--score:0%"><span id="latest-score">—</span><small>/100</small></div>
            <div class="latest-copy">
              <p id="latest-target">No assessment selected</p>
              <div class="grade-line"><span class="grade-label">Security Grade</span><span class="grade" id="latest-grade">—</span></div>
              <div class="latest-summary" id="latest-summary">Start a scan to see your website's security posture and recommended improvements.</div>
              <div class="latest-status" id="latest-meta">Awaiting first assessment</div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel feature-card" id="severity-panel">
        <div class="panel-head"><div class="panel-title"><h2>Findings by Severity</h2></div><span class="section-tag">Selected assessment</span></div>
        <div class="panel-body">
          <div class="severity-layout" id="severity-profile">
            <div class="severity-empty">Severity data appears after a scan is selected.</div>
          </div>
        </div>
      </section>
    </div>

    <section class="metrics" aria-label="Selected assessment metrics">
      <div class="stat">
        <span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h7"/></svg></span>
        <div class="stat-copy"><div class="stat-value" id="stat-pages">—</div><div class="stat-label">Pages Scanned</div></div>
      </div>
      <div class="stat">
        <span class="stat-icon green"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg></span>
        <div class="stat-copy"><div class="stat-value" id="stat-checks">—</div><div class="stat-label">Checks Passed</div></div>
      </div>
      <div class="stat">
        <span class="stat-icon amber"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 22 20H2L12 3Z"/><path d="M12 9v5m0 3h.01"/></svg></span>
        <div class="stat-copy"><div class="stat-value" id="stat-findings">—</div><div class="stat-label">Total Findings</div></div>
      </div>
      <div class="stat">
        <span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></span>
        <div class="stat-copy"><div class="stat-value" id="stat-duration">—</div><div class="stat-label">Scan Duration</div></div>
      </div>
    </section>

    <section class="panel" id="history-panel">
      <div class="panel-head">
        <div class="panel-title"><h2>Recent Assessments</h2><p>Saved scan history on this instance.</p></div>
        <button class="text-button" id="refresh-history" type="button">Refresh ↻</button>
      </div>
      <div class="panel-body"><div class="history-list" id="history-list"><div class="history-empty">Loading assessments…</div></div><div class="history-footer"><span id="history-count">—</span><span>Newest first</span></div></div>
    </section>

    <section class="panel" id="results-panel">
      <div class="panel-head">
        <div class="panel-title"><h2>Assessment Results</h2><p id="result-subtitle">Select an assessment or start a new scan.</p></div>
        <span class="section-tag" id="result-state">No scan selected</span>
      </div>
      <div class="panel-body" id="result-content">
        <div class="result-empty"><div><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="M9 12h6M12 9v6"/></svg></div><strong>No assessment selected</strong><div style="margin-top:5px">Start a scan to inspect vulnerabilities, evidence and suggested fixes.</div></div></div>
      </div>
    </section>

    <footer class="footer"><span>SITESENTRY · PASSIVE WEB SECURITY ASSESSMENT</span><span>ONLY ASSESS ASSETS YOU ARE AUTHORIZED TO TEST</span></footer>
  </main>
</div>
<script>
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const state = {selectedId:null,pollTimer:null,pollGeneration:0,findings:[]};
  const apiKeyInput = $("api-key");

  function node(tag,className,text) {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text !== undefined && text !== null) item.textContent = String(text);
    return item;
  }
  function setBanner(message,kind) {
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
  async function api(path,options) {
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
      } catch (_) { /* Keep the status-based message. */ }
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
  function durationText(start,end) {
    if (!start) return "—";
    const a = new Date(start).getTime();
    const b = end ? new Date(end).getTime() : Date.now();
    if (!Number.isFinite(a) || !Number.isFinite(b) || b < a) return "—";
    const seconds = Math.round((b-a)/1000);
    if (seconds < 60) return seconds + "s";
    return Math.floor(seconds/60) + "m " + String(seconds%60).padStart(2,"0") + "s";
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
  function updateStats(data,findings) {
    const complete = data.status === "completed";
    $("stat-pages").textContent = complete ? String(data.page_count || 0) : "—";
    $("stat-findings").textContent = complete ? String(findings.length) : "—";
    const checks = data.results || [];
    const passed = checks.filter((item) => !item.error && !item.incomplete && !(item.findings || []).length).length;
    $("stat-checks").textContent = complete ? (passed + "/" + checks.length) : "—";
    $("stat-duration").textContent = complete ? durationText(data.started_at,data.completed_at) : (data.status === "running" ? durationText(data.started_at,null) : "—");
    $("latest-score").textContent = complete ? String(data.score) : "—";
    $("latest-grade").textContent = complete ? (data.grade || "—") : "—";
    $("latest-grade").className = "grade " + (complete ? gradeClass(data.grade) : "");
    $("latest-score-ring").style.setProperty("--score",complete ? Math.max(0,Math.min(100,Number(data.score)||0)) + "%" : "0%");
    $("latest-target").textContent = data.target_url || "No assessment selected";
    $("latest-status").textContent = statusText(data.status);
    $("latest-meta").textContent = complete ? ("Scanned " + dateText(data.completed_at)) : statusText(data.status);
    $("latest-summary").textContent = complete
      ? (findings.length ? (findings.length + " security findings detected. Review severity, evidence and the recommended fixes below.") : "No findings were returned by the completed passive checks.")
      : (data.status === "failed" ? "This assessment did not complete successfully. Review its error details below." : "Your assessment is in progress. Results will update automatically.");
  }
  function addDetail(parent,label,value,extraClass) {
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
      root.className = "severity-layout";
      root.append(node("div","severity-empty","No findings to display for this assessment."));
      return;
    }
    const counts = severityCounts(findings);
    const order = ["critical","high","medium","low","info"];
    const colors = {critical:"#dc3d4d",high:"#e87524",medium:"#f2c230",low:"#4a9bea",info:"#aeb9c4"};
    let cursor = 0;
    const segments = [];
    order.forEach((severity) => {
      const size = counts[severity] / findings.length * 100;
      if (size > 0) {
        segments.push(colors[severity] + " " + cursor.toFixed(2) + "% " + (cursor+size).toFixed(2) + "%");
        cursor += size;
      }
    });
    root.className = "severity-layout";
    const donut = node("div","donut");
    donut.style.setProperty("--segments","conic-gradient(" + segments.join(",") + ")");
    const center = node("div","donut-center");
    center.append(node("span","donut-total",findings.length));
    center.append(node("span","donut-label","Findings"));
    donut.append(center);
    root.append(donut);
    const legend = node("div","severity-legend");
    order.forEach((severity) => {
      const item = node("div","severity-item " + severity);
      item.append(node("span","severity-dot"));
      item.append(node("span","",severity === "info" ? "Informational" : severity.charAt(0).toUpperCase()+severity.slice(1)));
      item.append(node("strong","",counts[severity]));
      legend.append(item);
    });
    root.append(legend);
  }
  function renderBreakdown(rows) {
    const wrapper = node("div","table-wrap");
    const table = node("table","breakdown");
    const thead = node("thead");
    const header = node("tr");
    ["Security check","Findings","Score deduction"].forEach((label) => header.append(node("th","",label)));
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
  function renderChecks(results) {
    const wrapper = node("div","table-wrap");
    const table = node("table","breakdown");
    const thead = node("thead");
    const header = node("tr");
    ["Security check","Status","Findings"].forEach((label) => header.append(node("th","",label)));
    thead.append(header);
    table.append(thead);
    const tbody = node("tbody");
    (results || []).forEach((item) => {
      const findings = item.findings || [];
      const incomplete = Boolean(item.error || item.incomplete);
      const status = incomplete ? "Incomplete" : (findings.length ? "Review findings" : "Passed");
      const tr = node("tr");
      tr.append(node("td","",item.title || item.check_id));
      const statusCell = node("td");
      statusCell.append(node("span","check-status" + (incomplete ? " incomplete" : (findings.length ? " findings" : "")),status));
      tr.append(statusCell);
      tr.append(node("td","",findings.length));
      tbody.append(tr);
      if (incomplete && item.error) {
        const detail = node("tr");
        const cell = node("td","",item.error);
        cell.colSpan = 3;
        detail.append(cell);
        tbody.append(detail);
      }
    });
    table.append(tbody);
    wrapper.append(table);
    return wrapper;
  }
  function renderDetails(data) {
    const wrap = node("div","details-grid");
    [
      ["Target URL",data.target_url],
      ["Scan ID",data.scan_id],
      ["Started",dateText(data.started_at)],
      ["Completed",dateText(data.completed_at)],
      ["Pages scanned",data.page_count],
      ["Overall score",data.status === "completed" ? (data.score + "/100 · Grade " + (data.grade || "—")) : statusText(data.status)]
    ].forEach(([label,value]) => {
      const card = node("div","detail-card");
      addDetail(card,label,value);
      wrap.append(card);
    });
    if ((data.errors || []).length) {
      const errors = node("div","status-banner visible error");
      errors.append(node("span","","Scan errors: " + data.errors.join(" · ")));
      wrap.append(errors);
    }
    if (data.has_incomplete_checks) {
      wrap.append(node("div","status-banner visible error","Some checks did not complete. Review the check statuses before relying on the grade."));
    }
    const scoreSection = node("section","subsection");
    const head = node("div","subsection-head");
    head.append(node("h3","","Scoring breakdown"));
    head.append(node("span","count",(data.breakdown || []).length + " checks"));
    scoreSection.append(head);
    scoreSection.append(renderBreakdown(data.breakdown));
    const result = node("div");
    result.append(wrap,scoreSection);
    return result;
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
      visible.forEach((finding) => {
        const row = node("tr");
        const titleCell = node("td");
        titleCell.append(node("span","finding-main",finding.title || "Security finding"));
        titleCell.append(node("span","finding-sub",(finding.check_id || "check") + " · " + (finding.url || "")));
        row.append(titleCell);
        const severityCell = node("td");
        severityCell.append(node("span","severity " + String(finding.severity || "info").toLowerCase(),finding.severity || "info"));
        row.append(severityCell);
        const actionCell = node("td");
        const inspect = node("button","inspect-button","Inspect  ›");
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
          inspect.textContent = detailRow.hidden ? "Inspect  ›" : "Close  ×";
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
    titleBlock.append(node("div","result-title",data.status === "completed" ? "Assessment complete" : "Assessment " + statusText(data.status).toLowerCase()));
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
      message.append(node("span","",data.status === "pending" ? "Waiting for an available scan worker…" : "The scanner is crawling the target and running passive checks. This view refreshes automatically."));
      content.append(message);
      return;
    }
    if (data.status === "failed") {
      content.append(node("div","status-banner visible error","This assessment failed. Check the API server logs for the underlying error."));
      (data.errors || []).forEach((error) => addDetail(content,"Scan error",error));
      return;
    }
    const actions = node("div","report-actions");
    [["html","HTML"],["md","Markdown"],["json","JSON"],["sarif","SARIF"]].forEach(([format,label]) => {
      const button = node("button","report-btn","Download " + label);
      button.type = "button";
      button.addEventListener("click",() => downloadReport(data.scan_id,format,button));
      actions.append(button);
    });
    content.append(actions);
    const tabs = node("div","tabs");
    const tabContent = node("div","tab-content");
    const views = {
      findings:() => renderFindingTable(findings),
      checks:() => renderChecks(data.results || []),
      details:() => renderDetails(data)
    };
    const names = [["findings","Findings"],["checks","Passed Checks"],["details","Details"]];
    names.forEach(([key,label],index) => {
      const button = node("button","tab" + (index === 0 ? " active" : ""),label);
      button.type = "button";
      button.addEventListener("click",() => {
        tabs.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        tabContent.replaceChildren(views[key]());
      });
      tabs.append(button);
    });
    tabContent.append(views.findings());
    content.append(tabs,tabContent);
    if (data.has_incomplete_checks) {
      content.append(node("div","status-banner visible error","Some checks did not complete. Review the check statuses before relying on this grade."));
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
    items.slice(0,6).forEach((item) => {
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
      setBanner("Could not load assessment: " + error.message,"error");
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
          $("stat-duration").textContent = durationText(data.started_at,null);
          state.pollTimer = window.setTimeout(poll,2000);
        } else {
          state.pollTimer = null;
          setBanner(data.status === "completed" ? "Assessment complete. Review findings and recommended fixes below." : "Assessment finished with an error. Review the server logs.",data.status === "completed" ? "success" : "error");
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
    button.textContent = "Starting…";
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
      setBanner("Assessment accepted. Connecting to the scan…","loading");
      await refreshHistory();
      await openScan(accepted.id);
    } catch (error) {
      setBanner("Could not start assessment: " + error.message,"error");
    } finally {
      button.disabled = false;
      button.textContent = "▷  Start Scan";
    }
  });
  $("refresh-history").addEventListener("click",refreshHistory);
  apiKeyInput.addEventListener("change",refreshHistory);
  refreshHistory();
})();
</script>"""
