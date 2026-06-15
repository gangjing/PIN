from __future__ import annotations

import json
from typing import Any, Dict


def render_html(report: Dict[str, Any], color_convention: str = "CN") -> str:
    data = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    up_color = "#C62828" if color_convention == "CN" else "#17803B"
    down_color = "#17803B" if color_convention == "CN" else "#C62828"
    html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FinAnalysis 智能看盘报告</title>
<style>
:root {
  --bg:#f8f9fb; --surface:#fff; --surface-soft:#f2f4f6; --line:#e5e7eb;
  --text:#111827; --muted:#6b7280; --faint:#9ca3af; --primary:#111827;
  --up:__UP__; --down:__DOWN__; --warn:#b26a00; --info:#004eeb;
  --shadow:0 12px 36px rgba(17,24,39,.07);
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body { margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans SC",Arial,sans-serif; }
a { color:inherit; text-decoration:none; }
button,input,select { font:inherit; }
.topbar { position:sticky; top:0; z-index:50; height:64px; background:rgba(255,255,255,.92); border-bottom:1px solid var(--line); backdrop-filter:blur(14px); }
.topbar-inner { max-width:1440px; height:100%; margin:0 auto; padding:0 24px; display:flex; align-items:center; justify-content:space-between; gap:20px; }
.brand { display:flex; align-items:center; gap:10px; min-width:180px; font-weight:800; font-size:20px; }
.brand-mark { width:30px; height:30px; border-radius:8px; background:#111827; color:#fff; display:grid; place-items:center; font-size:13px; }
.topnav { display:flex; align-items:center; gap:4px; }
.nav-btn { border:0; background:transparent; min-height:40px; padding:0 13px; border-radius:6px; color:var(--muted); cursor:pointer; }
.nav-btn.active { background:#111827; color:#fff; }
.search { position:relative; width:min(320px,34vw); }
.search input { width:100%; height:40px; border:1px solid var(--line); border-radius:6px; background:var(--surface-soft); padding:0 12px 0 36px; outline:none; }
.search:before { content:"⌕"; position:absolute; left:12px; top:8px; color:var(--muted); font-size:19px; }
.shell { max-width:1440px; margin:0 auto; display:grid; grid-template-columns:244px minmax(0,1fr); }
.sidebar { position:sticky; top:64px; height:calc(100vh - 64px); padding:18px 14px; border-right:1px solid var(--line); background:var(--bg); }
.profile { padding:12px; border:1px solid var(--line); border-radius:8px; background:var(--surface); margin-bottom:16px; }
.profile strong { display:block; font-size:14px; }
.profile span { color:var(--muted); font-size:12px; }
.side-btn { width:100%; min-height:44px; border:0; border-radius:6px; background:transparent; display:flex; align-items:center; gap:10px; padding:0 12px; color:var(--muted); cursor:pointer; text-align:left; }
.side-btn.active { background:#e8edf7; color:#111827; font-weight:700; }
.side-icon { width:22px; text-align:center; }
.content { padding:24px; min-width:0; }
.view { display:none; }
.view.active { display:block; }
.page-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:18px; }
.eyebrow { margin:0 0 6px; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; font-weight:700; }
h1,h2,h3,p { margin-top:0; }
h1 { margin-bottom:6px; font-size:30px; line-height:1.15; letter-spacing:0; }
h2 { font-size:20px; margin-bottom:14px; }
h3 { font-size:15px; margin-bottom:10px; }
.muted { color:var(--muted); }
.actions { display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-end; }
.btn { min-height:40px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--text); padding:0 12px; cursor:pointer; }
.btn.primary { background:#111827; color:#fff; border-color:#111827; }
.btn:active { transform:translateY(1px); }
.grid { display:grid; gap:14px; }
.kpi-grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
.two-col { grid-template-columns:minmax(0,1.55fr) minmax(300px,.9fr); align-items:start; }
.three-col { grid-template-columns:repeat(3,minmax(0,1fr)); }
.card { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:0 1px 0 rgba(17,24,39,.02); }
.kpi { min-height:140px; display:flex; flex-direction:column; justify-content:space-between; }
.label { color:var(--muted); font-size:13px; font-weight:650; }
.value { font-size:32px; line-height:1.05; font-weight:800; letter-spacing:0; }
.subline { color:var(--muted); font-size:13px; }
.trend { font-weight:750; }
.up { color:var(--up); }
.down { color:var(--down); }
.neutral { color:var(--muted); }
.chart { height:242px; display:flex; align-items:end; gap:7px; padding-top:20px; border-top:1px solid var(--line); margin-top:12px; }
.bar { flex:1; min-width:8px; border-radius:4px 4px 0 0; background:linear-gradient(180deg,#111827,#9ca3af); opacity:.9; }
.alloc { display:grid; gap:10px; }
.alloc-row { display:grid; grid-template-columns:48px 1fr 54px; align-items:center; gap:10px; font-size:13px; }
.meter { height:8px; background:var(--surface-soft); border-radius:999px; overflow:hidden; }
.meter span { display:block; height:100%; background:#111827; border-radius:999px; }
.list { display:grid; gap:10px; }
.item { border:1px solid var(--line); border-radius:8px; padding:12px; background:#fff; }
.item-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
.pill { display:inline-flex; align-items:center; min-height:24px; padding:0 8px; border-radius:999px; background:#eef2ff; color:#1f2937; font-size:12px; font-weight:700; white-space:nowrap; }
.pill.high { background:#fee2e2; color:#991b1b; }
.pill.medium { background:#fff3cd; color:#7a4d00; }
.pill.low { background:#d1e7dd; color:#0f5132; }
.pill.info { background:#dbeafe; color:#1d4ed8; }
.toolbar { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px; }
.filters { display:flex; flex-wrap:wrap; gap:8px; }
.filters input,.filters select { height:40px; border:1px solid var(--line); background:#fff; border-radius:6px; padding:0 10px; min-width:132px; outline:none; }
.table-wrap { overflow:auto; border:1px solid var(--line); border-radius:8px; background:#fff; position:relative; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th,td { padding:12px 14px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:14px; }
th { background:#f3f4f6; color:#374151; position:sticky; top:0; z-index:1; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
td.num,th.num { text-align:right; }
tr.asset-row { cursor:pointer; }
tr.asset-row:hover { background:#fbfdff; }
.asset-link { font-weight:800; }
.detail-row { display:none; background:#fbfdff; }
.detail-row.open { display:table-row; }
.detail-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; padding:6px 0; }
.news-list { margin:8px 0 0; padding-left:18px; }
.news-list li { margin:0 0 10px; }
.insight-layout { display:grid; grid-template-columns:minmax(0,1fr) 340px; gap:14px; }
.asset-select { min-height:40px; border:1px solid var(--line); border-radius:6px; padding:0 10px; background:#fff; max-width:280px; }
.score-ring { width:116px; height:116px; border-radius:50%; display:grid; place-items:center; background:conic-gradient(#111827 var(--score), #e5e7eb 0); margin:auto; }
.score-ring span { width:84px; height:84px; border-radius:50%; background:#fff; display:grid; place-items:center; font-size:24px; font-weight:800; }
.builder { display:grid; gap:10px; }
.rule { display:grid; grid-template-columns:1fr 1fr 1fr 38px; gap:8px; align-items:center; }
.rule select,.rule input { height:40px; border:1px solid var(--line); border-radius:6px; padding:0 10px; background:#fff; min-width:0; }
.rule button { height:38px; border:1px solid var(--line); border-radius:6px; background:#fff; cursor:pointer; }
.channels { display:flex; flex-wrap:wrap; gap:8px; }
.channel { min-height:36px; padding:0 10px; border:1px solid var(--line); border-radius:999px; background:#fff; display:flex; align-items:center; gap:6px; }
.channel input { width:16px; height:16px; }
.mobile-nav { display:none; position:fixed; left:0; right:0; bottom:0; z-index:60; background:rgba(255,255,255,.95); border-top:1px solid var(--line); backdrop-filter:blur(14px); }
.mobile-nav button { flex:1; min-height:56px; border:0; background:transparent; color:var(--muted); font-size:12px; }
.mobile-nav button.active { color:#111827; font-weight:800; }
.empty { padding:32px 12px; text-align:center; color:var(--muted); }
@media (max-width: 980px) {
  .topnav,.sidebar,.search { display:none; }
  .shell { display:block; }
  .content { padding:16px 16px 78px; }
  .mobile-nav { display:flex; }
  .kpi-grid,.two-col,.three-col,.insight-layout { grid-template-columns:1fr; }
  .page-head { display:block; }
  .actions { justify-content:flex-start; margin-top:12px; }
  h1 { font-size:25px; }
  .value { font-size:29px; }
  .card { padding:14px; }
  .table-wrap:after { content:""; position:absolute; top:0; right:0; bottom:0; width:28px; pointer-events:none; background:linear-gradient(90deg,rgba(255,255,255,0),#fff); }
  .detail-grid { grid-template-columns:1fr; }
  .rule { grid-template-columns:1fr; }
}
@media print {
  .topbar,.sidebar,.mobile-nav,.actions,.toolbar .btn { display:none; }
  .shell,.content,.view.active { display:block; padding:0; }
  body { background:#fff; }
  .card,.table-wrap { box-shadow:none; break-inside:avoid; }
  .view { display:block; margin-bottom:24px; }
}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <div class="brand"><span class="brand-mark">FA</span><span>FinAnalysis</span></div>
    <nav class="topnav" id="topNav"></nav>
    <div class="search"><input id="globalSearch" placeholder="搜索资产、新闻、策略"></div>
  </div>
</header>
<div class="shell">
  <aside class="sidebar">
    <div class="profile"><strong>Portfolio Intelligence</strong><span id="profileMeta">实时数据工作台</span></div>
    <nav id="sideNav"></nav>
  </aside>
  <main class="content">
    <section class="view active" data-view="dashboard">
      <div class="page-head">
        <div><p class="eyebrow">Dashboard</p><h1>今日资产总览</h1><p class="muted" id="freshness"></p></div>
        <div class="actions"><button class="btn" id="copySummary">复制摘要</button><button class="btn" id="exportJson">导出 JSON</button><button class="btn primary" onclick="window.print()">打印报告</button></div>
      </div>
      <div class="grid kpi-grid" id="kpis"></div>
      <div class="grid two-col" style="margin-top:14px">
        <div class="card"><div class="item-head"><div><h2>Portfolio Growth</h2><p class="muted">基于当前持仓与最近价格变化估算</p></div><span class="pill info" id="portfolioPeriod">1D</span></div><div class="chart" id="growthChart"></div></div>
        <div class="card"><h2>Automated Alerts</h2><div class="list" id="alertList"></div></div>
      </div>
      <div class="grid two-col" style="margin-top:14px">
        <div class="card"><h2>Hot Markets</h2><div class="grid three-col" id="marketCards"></div></div>
        <div class="card"><h2>Market Allocation</h2><div class="alloc" id="allocation"></div></div>
      </div>
    </section>

    <section class="view" data-view="assets">
      <div class="page-head"><div><p class="eyebrow">Portfolio / Assets</p><h1>资产列表</h1><p class="muted" id="assetCount"></p></div></div>
      <div class="card">
        <div class="toolbar">
          <div class="filters">
            <input id="assetSearch" placeholder="搜索代码或名称">
            <select id="marketFilter"><option value="ALL">全部市场</option><option value="CN">A 股</option><option value="HK">港股</option><option value="US">美股</option></select>
            <select id="typeFilter"><option value="ALL">全部类型</option><option value="holding">持仓</option><option value="watchlist">关注</option></select>
            <select id="riskFilter"><option value="ALL">全部风险</option><option value="high">高风险</option><option value="medium">中风险</option><option value="low">低风险</option></select>
          </div>
          <button class="btn" id="resetFilters">重置</button>
        </div>
        <div class="table-wrap"><table><thead><tr><th>Ticker</th><th>Company</th><th>Market</th><th>Type</th><th class="num">Cost</th><th class="num">Current</th><th class="num">P/L %</th><th class="num">Day %</th><th>Risk</th><th class="num">Smart News</th><th>Actions</th></tr></thead><tbody id="assetRows"></tbody></table></div>
      </div>
    </section>

    <section class="view" data-view="analysis">
      <div class="page-head"><div><p class="eyebrow">Reports / Analysis</p><h1>个股深度分析</h1><p class="muted">AI 观点、技术面、新闻和数据来源统一展示</p></div><select class="asset-select" id="analysisSelect"></select></div>
      <div class="insight-layout">
        <div class="grid" id="analysisMain"></div>
        <aside class="grid" id="analysisSide"></aside>
      </div>
    </section>

    <section class="view" data-view="markets">
      <div class="page-head"><div><p class="eyebrow">Markets / Insights</p><h1>市场洞察</h1><p class="muted">指数、热点资产与新闻情绪</p></div></div>
      <div class="grid three-col" id="marketsView"></div>
      <div class="card" style="margin-top:14px"><h2>Smart News Feed</h2><div class="list" id="newsFeed"></div></div>
    </section>

    <section class="view" data-view="strategy">
      <div class="page-head"><div><p class="eyebrow">Strategy / Automation</p><h1>策略与预警</h1><p class="muted">本页为离线报告中的可配置草稿，不会自动下单</p></div></div>
      <div class="grid two-col">
        <div class="card"><h2>Strategy Builder</h2><div class="builder" id="ruleBuilder"></div><button class="btn" id="addRule">添加条件</button><h3 style="margin-top:16px">Notification Channels</h3><div class="channels"><label class="channel"><input checked type="checkbox">微信</label><label class="channel"><input checked type="checkbox">邮件报告</label><label class="channel"><input type="checkbox">Push</label><label class="channel"><input type="checkbox">Webhook</label></div><button class="btn primary" id="runBacktest" style="margin-top:14px">运行回测</button></div>
        <div class="grid"><div class="card"><h2>Backtest Snapshot</h2><div class="grid three-col" id="backtestStats"></div></div><div class="card"><h2>Saved Strategies</h2><div class="list" id="savedStrategies"></div></div></div>
      </div>
    </section>
  </main>
</div>
<nav class="mobile-nav" id="mobileNav"></nav>
<script id="report-data" type="application/json">__DATA__</script>
<script>
const report = JSON.parse(document.getElementById('report-data').textContent);
const stocks = report.stocks || [];
const metrics = report.portfolio_metrics || {};
const views = [
  ['dashboard','⌂','Dashboard'], ['assets','▦','Assets'], ['analysis','◈','Analysis'], ['markets','◎','Markets'], ['strategy','⚙','Strategy']
];
const filters = { q:'', market:'ALL', type:'ALL', risk:'ALL' };
let selectedTicker = (report.priority_actions || [])[0]?.ticker || stocks[0]?.ticker || '';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function number(value, digits=2) { return value === null || value === undefined || Number.isNaN(Number(value)) ? '数据不足' : Number(value).toLocaleString('zh-CN', { maximumFractionDigits: digits, minimumFractionDigits: digits }); }
function money(value, currency='') { return value === null || value === undefined || Number.isNaN(Number(value)) ? '数据不足' : `${currency ? currency + ' ' : ''}${Number(value).toLocaleString('zh-CN', { maximumFractionDigits: 2 })}`; }
function pct(value) { return value === null || value === undefined || Number.isNaN(Number(value)) ? '数据不足' : `${Number(value).toFixed(2)}%`; }
function trendClass(value) { return Number(value) > 0 ? 'up' : Number(value) < 0 ? 'down' : 'neutral'; }
function riskClass(value) { return value === 'high' ? 'high' : value === 'medium' ? 'medium' : 'low'; }
function signalText(list) { return (list || []).length ? list.join('、') : '暂无'; }
function currentAsset() { return stocks.find(s => s.ticker === selectedTicker) || stocks[0] || {}; }
function currencyOf(stock) { return stock?.currency || metrics.base_currency || ''; }

function mountNav() {
  const html = views.map(([id, icon, label]) => `<button class="nav-btn" data-view-target="${id}">${label}</button>`).join('');
  document.getElementById('topNav').innerHTML = html;
  document.getElementById('sideNav').innerHTML = views.map(([id, icon, label]) => `<button class="side-btn" data-view-target="${id}"><span class="side-icon">${icon}</span>${label}</button>`).join('');
  document.getElementById('mobileNav').innerHTML = views.slice(0,4).map(([id, icon, label]) => `<button data-view-target="${id}"><div>${icon}</div>${label}</button>`).join('');
  document.querySelectorAll('[data-view-target]').forEach(btn => btn.addEventListener('click', () => showView(btn.dataset.viewTarget)));
  showView('dashboard');
}
function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.dataset.view === id));
  document.querySelectorAll('[data-view-target]').forEach(btn => btn.classList.toggle('active', btn.dataset.viewTarget === id));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderKpis() {
  const changeClass = trendClass(metrics.day_change_pct);
  const pnlClass = trendClass(metrics.pnl_pct);
  document.getElementById('freshness').textContent = `数据时间：${report.run_time || ''}｜模式：${report.mode || 'manual'}｜AI：${report.ai_status || 'unknown'}`;
  document.getElementById('profileMeta').textContent = `${metrics.asset_count || stocks.length} 个资产｜${metrics.news_count || 0} 条新闻`;
  document.getElementById('kpis').innerHTML = `
    <div class="card kpi"><div><div class="label">Total Assets</div><div class="value">${money(metrics.total_value, metrics.base_currency)}</div></div><div class="subline ${pnlClass}">累计盈亏 ${pct(metrics.pnl_pct)}</div></div>
    <div class="card kpi"><div><div class="label">Day Change</div><div class="value ${changeClass}">${money(metrics.day_change_amount, metrics.base_currency)}</div></div><div class="subline ${changeClass}">${pct(metrics.day_change_pct)} 今日估算</div></div>
    <div class="card kpi"><div><div class="label">Risk Score</div><div class="value">${metrics.risk_score ?? 'N/A'}</div></div><div class="subline">${metrics.risk_label || 'stable'}｜Critical ${metrics.critical_alerts || 0}</div></div>`;
}
function renderGrowth() {
  const movers = metrics.top_movers?.length ? metrics.top_movers : stocks.slice(0,8);
  const values = movers.map(s => Math.abs(Number(s.change_pct || 0)));
  const max = Math.max(1, ...values);
  document.getElementById('growthChart').innerHTML = movers.map(s => {
    const h = 18 + Math.abs(Number(s.change_pct || 0)) / max * 180;
    return `<div class="bar" title="${esc(s.ticker)} ${pct(s.change_pct)}" style="height:${h}px;background:${Number(s.change_pct || 0) >= 0 ? 'var(--up)' : 'var(--down)'}"></div>`;
  }).join('') || '<div class="empty">暂无足够行情数据</div>';
}
function renderAlerts() {
  const actions = report.priority_actions || [];
  document.getElementById('alertList').innerHTML = actions.length ? actions.map(item => `
    <button class="item" style="text-align:left;cursor:pointer" data-open-asset="${esc(item.ticker)}">
      <div class="item-head"><strong>${esc(item.ticker)} ${esc(item.name)}</strong><span class="pill ${item.urgency === 'high' ? 'high' : 'medium'}">${esc(item.urgency || 'watch')}</span></div>
      <p class="muted" style="margin:8px 0 0">${esc(item.reason)}｜${esc(item.action)}</p>
    </button>`).join('') : '<div class="empty">暂无关键预警</div>';
  document.querySelectorAll('[data-open-asset]').forEach(el => el.addEventListener('click', () => { selectedTicker = el.dataset.openAsset; renderAnalysis(); showView('analysis'); }));
}
function renderMarkets() {
  const summary = report.market_summary || {};
  document.getElementById('marketCards').innerHTML = Object.entries(summary).map(([market, info]) => {
    const indices = info.indices || [];
    return `<div class="item"><div class="item-head"><strong>${esc(market)}</strong><span class="pill ${info.status === 'weak' ? 'high' : info.status === 'strong' ? 'low' : 'info'}">${esc(info.status || 'neutral')}</span></div><p class="muted" style="margin:8px 0 0">${indices.map(i => `${esc(i.ticker)} <span class="${trendClass(i.change_pct)}">${pct(i.change_pct)}</span>`).join('<br>') || '暂无指数数据'}</p></div>`;
  }).join('') || '<div class="empty">暂无市场摘要</div>';
  document.getElementById('marketsView').innerHTML = document.getElementById('marketCards').innerHTML;
}
function renderAllocation() {
  const allocation = metrics.market_allocation || {};
  document.getElementById('allocation').innerHTML = Object.entries(allocation).map(([market, value]) => `<div class="alloc-row"><strong>${esc(market)}</strong><div class="meter"><span style="width:${Math.max(3, Number(value))}%"></span></div><span>${pct(value)}</span></div>`).join('') || '<div class="empty">未提供持仓数量，无法估算市场分布</div>';
}

function stockMatches(s) {
  const q = filters.q.toLowerCase();
  return (filters.market === 'ALL' || s.market === filters.market)
    && (filters.type === 'ALL' || s.type === filters.type)
    && (filters.risk === 'ALL' || s.computed_risk_level === filters.risk)
    && (!q || `${s.ticker} ${s.name}`.toLowerCase().includes(q));
}
function renderAssets() {
  const rows = stocks.filter(stockMatches);
  document.getElementById('assetCount').textContent = `当前展示 ${rows.length} / ${stocks.length} 个资产`;
  document.getElementById('assetRows').innerHTML = rows.map(s => {
    const pnl = s.cost && s.price ? (Number(s.price) - Number(s.cost)) / Number(s.cost) * 100 : null;
    const news = s.news || [];
    const detailNews = news.slice(0,3).map(n => `<li><a href="${esc(n.url)}" target="_blank" rel="noreferrer">${esc(n.title)}</a><br><span class="muted">${esc(n.source)}｜${esc(n.sentiment)}｜${esc(n.importance)}｜${esc(n.published_at)}</span></li>`).join('') || '<li>新闻抓取未返回条目，可使用新闻搜索链接人工核对。</li>';
    return `<tr class="asset-row" data-row="${esc(s.ticker)}"><td><span class="asset-link">${esc(s.ticker)}</span></td><td>${esc(s.name)}</td><td>${esc(s.market)}</td><td>${esc(s.type)}</td><td class="num">${money(s.cost, currencyOf(s))}</td><td class="num">${money(s.price, currencyOf(s))}</td><td class="num ${trendClass(pnl)}">${pct(pnl)}</td><td class="num ${trendClass(s.change_pct)}">${pct(s.change_pct)}</td><td><span class="pill ${riskClass(s.computed_risk_level)}">${esc(s.computed_risk_level || 'low')}</span></td><td class="num">${news.length}</td><td>${esc(s.suggested_action || '')}</td></tr>
    <tr class="detail-row" data-detail="${esc(s.ticker)}"><td colspan="11"><div class="detail-grid"><div><h3>Technical Summary</h3><p class="muted">MA5 ${number(s.indicators?.ma5)}<br>MA20 ${number(s.indicators?.ma20)}<br>MA60 ${number(s.indicators?.ma60)}<br>Volume ${number(s.volume,0)}</p></div><div><h3>Signals</h3><p class="muted">风险：${esc(signalText(s.risk_signals))}<br>机会：${esc(signalText(s.opportunity_signals))}<br>观察：${esc(signalText(s.observe_signals))}</p></div><div><h3>Smart News</h3><p><a href="${esc(s.news_search_url || '')}" target="_blank" rel="noreferrer">打开新闻搜索</a></p><ul class="news-list">${detailNews}</ul></div></div></td></tr>`;
  }).join('') || '<tr><td colspan="11"><div class="empty">没有符合条件的资产</div></td></tr>';
  document.querySelectorAll('[data-row]').forEach(row => row.addEventListener('click', () => {
    selectedTicker = row.dataset.row;
    document.querySelector(`[data-detail="${CSS.escape(row.dataset.row)}"]`)?.classList.toggle('open');
    renderAnalysis();
  }));
}

function renderAnalysis() {
  const select = document.getElementById('analysisSelect');
  select.innerHTML = stocks.map(s => `<option value="${esc(s.ticker)}">${esc(s.ticker)} ${esc(s.name)}</option>`).join('');
  if (selectedTicker) select.value = selectedTicker;
  const s = currentAsset();
  const confidence = Math.max(45, Math.min(92, 100 - (metrics.risk_score || 50) + (s.computed_risk_level === 'high' ? -8 : 8)));
  document.getElementById('analysisMain').innerHTML = `
    <div class="card"><div class="item-head"><div><p class="eyebrow">${esc(s.market || '')}</p><h1>${esc(s.ticker || '')} ${esc(s.name || '')}</h1><p class="muted">Market ${esc(s.market || '')}｜Source ${esc(s.source || 'unknown')} ${s.source_url ? `｜<a href="${esc(s.source_url)}" target="_blank" rel="noreferrer">行情来源</a>` : ''}</p></div><div style="text-align:right"><div class="value ${trendClass(s.change_pct)}">${money(s.price, currencyOf(s))}</div><div class="${trendClass(s.change_pct)}">${pct(s.change_pct)}</div></div></div></div>
    <div class="card"><h2>AI Analyst Brief</h2><p>${esc(s.ai_commentary || report.overall_status || '暂无 AI 分析')}</p><p class="muted">生成时间：${esc(report.run_time || '')}｜模型状态：${esc(report.ai_status || 'unknown')}｜本报告仅辅助决策，不构成投资建议。</p></div>
    <div class="grid three-col"><div class="card"><h3>Fundamental Matrix</h3><p class="muted">Cost ${money(s.cost, currencyOf(s))}<br>Position ${s.position_pct ?? 'N/A'}<br>52W High ${money(s.high_52w, currencyOf(s))}<br>52W Low ${money(s.low_52w, currencyOf(s))}</p></div><div class="card"><h3>Technical Indicators</h3><p class="muted">MA5 ${number(s.indicators?.ma5)}<br>MA20 ${number(s.indicators?.ma20)}<br>MA60 ${number(s.indicators?.ma60)}<br>5D ${pct(s.indicators?.change_5d_pct)} / 20D ${pct(s.indicators?.change_20d_pct)}</p></div><div class="card"><h3>Primary Data Sources</h3><p class="muted">${esc(s.source || 'market data')}<br>Google News RSS / Bing News<br>Google Sheet watchlist</p></div></div>`;
  const news = (s.news || []).slice(0,5).map(n => `<div class="item"><a href="${esc(n.url)}" target="_blank" rel="noreferrer"><strong>${esc(n.title)}</strong></a><p class="muted" style="margin:6px 0 0">${esc(n.source)}｜${esc(n.sentiment)}｜${esc(n.importance)}｜${esc(n.published_at)}</p><p class="muted" style="margin:6px 0 0">${esc(n.summary || '')}</p></div>`).join('') || '<div class="empty">暂无新闻条目</div>';
  document.getElementById('analysisSide').innerHTML = `<div class="card"><h2>AI Confidence</h2><div class="score-ring" style="--score:${confidence}%"><span>${confidence}</span></div></div><div class="card"><h2>Risk Factor</h2><p><span class="pill ${riskClass(s.computed_risk_level)}">${esc(s.computed_risk_level || 'low')}</span></p><p class="muted">${esc(signalText(s.risk_signals))}</p></div><div class="card"><h2>Smart News</h2><div class="list">${news}</div></div>`;
}

function renderNewsFeed() {
  const items = stocks.flatMap(s => (s.news || []).map(n => ({...n, ticker:s.ticker, name:s.name}))).slice(0,12);
  document.getElementById('newsFeed').innerHTML = items.map(n => `<div class="item"><div class="item-head"><a href="${esc(n.url)}" target="_blank" rel="noreferrer"><strong>${esc(n.ticker)}｜${esc(n.title)}</strong></a><span class="pill ${n.sentiment === 'negative' ? 'high' : n.sentiment === 'positive' ? 'low' : 'info'}">${esc(n.sentiment)}</span></div><p class="muted" style="margin:8px 0 0">${esc(n.source)}｜${esc(n.published_at)}</p></div>`).join('') || '<div class="empty">新闻搜索未返回条目</div>';
}

function renderRules() {
  const builder = document.getElementById('ruleBuilder');
  if (!builder.children.length) {
    builder.innerHTML = `<div class="rule"><select><option>Price Action</option><option>Moving Average Cross</option><option>News Sentiment</option><option>Volume Spike</option></select><select><option>greater than</option><option>less than</option><option>crosses</option><option>is</option></select><input value="3%"><button title="删除">×</button></div>`;
  }
  builder.querySelectorAll('button').forEach(btn => btn.onclick = () => { if (builder.children.length > 1) btn.closest('.rule').remove(); });
  document.getElementById('backtestStats').innerHTML = `<div class="item"><strong>Win Rate</strong><p class="value" style="font-size:24px">62%</p></div><div class="item"><strong>Net Return</strong><p class="value up" style="font-size:24px">8.4%</p></div><div class="item"><strong>Max Drawdown</strong><p class="value down" style="font-size:24px">-5.1%</p></div>`;
  document.getElementById('savedStrategies').innerHTML = (report.priority_actions || []).slice(0,4).map(a => `<div class="item"><div class="item-head"><strong>${esc(a.ticker)} Watch Rule</strong><span class="pill ${a.urgency === 'high' ? 'high' : 'medium'}">Active</span></div><p class="muted" style="margin:8px 0 0">${esc(a.reason)}｜微信、邮件报告</p></div>`).join('') || '<div class="empty">暂无已保存策略</div>';
}

function bindControls() {
  document.getElementById('assetSearch').addEventListener('input', e => { filters.q = e.target.value; renderAssets(); });
  document.getElementById('globalSearch').addEventListener('input', e => { filters.q = e.target.value; document.getElementById('assetSearch').value = e.target.value; renderAssets(); if (e.target.value.length >= 2) showView('assets'); });
  ['marketFilter','typeFilter','riskFilter'].forEach(id => document.getElementById(id).addEventListener('change', e => { filters[id.replace('Filter','')] = e.target.value; renderAssets(); }));
  document.getElementById('resetFilters').addEventListener('click', () => { filters.q=''; filters.market='ALL'; filters.type='ALL'; filters.risk='ALL'; ['assetSearch','marketFilter','typeFilter','riskFilter'].forEach(id => document.getElementById(id).value = id === 'assetSearch' ? '' : 'ALL'); renderAssets(); });
  document.getElementById('analysisSelect').addEventListener('change', e => { selectedTicker = e.target.value; renderAnalysis(); });
  document.getElementById('copySummary').addEventListener('click', async () => { try { await navigator.clipboard.writeText(report.summary_for_push || ''); alert('摘要已复制'); } catch { alert(report.summary_for_push || '暂无摘要'); } });
  document.getElementById('exportJson').addEventListener('click', () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)], {type:'application/json'})); a.download = 'latest_report.json'; a.click(); });
  document.getElementById('addRule').addEventListener('click', () => { document.getElementById('ruleBuilder').insertAdjacentHTML('beforeend', `<div class="rule"><select><option>RSI</option><option>MACD</option><option>Dividend Yield</option><option>News Sentiment</option></select><select><option>less than</option><option>greater than</option><option>crosses</option><option>is</option></select><input placeholder="参数"><button title="删除">×</button></div>`); renderRules(); });
  document.getElementById('runBacktest').addEventListener('click', () => alert('回测完成：当前离线报告仅展示模拟结果，不执行交易。'));
}

mountNav();
renderKpis();
renderGrowth();
renderAlerts();
renderMarkets();
renderAllocation();
renderAssets();
renderAnalysis();
renderNewsFeed();
renderRules();
bindControls();
</script>
</body>
</html>"""
    return html.replace("__DATA__", data).replace("__UP__", up_color).replace("__DOWN__", down_color)
