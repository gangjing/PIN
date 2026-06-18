from __future__ import annotations

import json
from typing import Any, Dict


_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FinAnalysis Report</title>
<style>
:root{--paper:#f5f4ed;--sheet:#fffdf6;--ink:#172033;--muted:#6f6758;--line:#d9d1bf;--brand:#1B365D;--soft:#ede7d8;--up:__UP__;--down:__DOWN__;--warn:#8a4b00;--bad:#9b1c1c}
[data-theme=dark]{--paper:#151712;--sheet:#1f211a;--ink:#f4f0e6;--muted:#b9ae9b;--line:#3c382f;--brand:#9fb9dc;--soft:#2c2a22;--warn:#f3c26b;--bad:#ff8f8f}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:Georgia,"Times New Roman","Noto Serif SC","Songti SC",serif;line-height:1.5}
button,input,select{font:inherit}
a{color:var(--brand);text-decoration:none}
.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--paper) 92%,transparent);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.topbar{max-width:1180px;margin:auto;padding:10px 18px;display:flex;gap:14px;align-items:center;justify-content:space-between}
.brand{font-weight:700;letter-spacing:.02em;color:var(--brand)}
.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
button{border:1px solid var(--line);background:var(--sheet);color:var(--ink);border-radius:999px;min-height:34px;padding:0 12px;cursor:pointer}
button.active,.primary{background:var(--brand);color:var(--sheet);border-color:var(--brand)}
.search{width:min(260px,34vw);height:34px;border:1px solid var(--line);border-radius:999px;background:var(--sheet);color:var(--ink);padding:0 12px}
.page{max-width:1180px;margin:0 auto;padding:30px 18px 64px}
.cover{display:grid;grid-template-columns:minmax(0,1.2fr) 320px;gap:22px;align-items:end;margin-bottom:22px}
.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:var(--brand);font-size:12px;font-weight:700;margin:0 0 8px}
h1{font-size:44px;line-height:1.08;margin:0 0 10px;font-weight:600;letter-spacing:0}
h2{font-size:25px;line-height:1.18;margin:0 0 14px;font-weight:600}
h3{font-size:19px;margin:0 0 8px;font-weight:600}
p{margin:0 0 10px}.muted{color:var(--muted)}.small{font-size:13px}
.sheet,.paper{background:var(--sheet);border:1px solid var(--line);border-radius:6px;padding:20px;box-shadow:0 1px 0 rgba(27,54,93,.04)}
.toc{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 24px}
.toc a{border:1px solid var(--line);background:var(--sheet);border-radius:999px;padding:7px 11px;font-size:13px;color:var(--ink)}
.grid{display:grid;gap:14px}.kpis{grid-template-columns:repeat(4,minmax(0,1fr))}.cols2{grid-template-columns:1fr 1fr}.cols3{grid-template-columns:repeat(3,minmax(0,1fr))}
.metric{border-left:3px solid var(--brand);padding-left:12px}.metric b{display:block;font-size:24px;line-height:1.12}.metric span{display:block;color:var(--muted);font-size:13px;margin-top:4px}
.up{color:var(--up)}.down{color:var(--down)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.tag{display:inline-flex;align-items:center;min-height:24px;border-radius:999px;background:var(--soft);color:var(--brand);padding:0 9px;font-size:12px;font-weight:700;margin:2px 4px 2px 0}
.tag.high{background:#f4d8d4;color:#8d1c13}.tag.medium{background:#f3e2bd;color:#704100}.tag.low{background:#dfe9d8;color:#28532b}
[data-theme=dark] .tag.high{background:#4a2422;color:#ffaaa2}[data-theme=dark] .tag.medium{background:#4b3820;color:#f4ca7c}[data-theme=dark] .tag.low{background:#243a28;color:#a9d8ae}
table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border-bottom:1px solid var(--line);padding:9px 8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{color:var(--muted);font-size:12px;text-transform:uppercase;font-weight:700}.num{text-align:right}
.report{margin-top:20px}.report-head{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:18px;align-items:start;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:16px}
.price{text-align:right}.price b{display:block;font-size:30px;line-height:1.1}.section{margin-top:18px}.quote{border-left:3px solid var(--brand);padding:4px 0 4px 13px;color:var(--ink)}
.news{display:grid;gap:8px}.news a{display:block;color:var(--ink);font-weight:600}.news-item{border-top:1px solid var(--line);padding-top:9px}
.bars{height:140px;display:flex;gap:7px;align-items:end;border-bottom:1px solid var(--line);padding-top:12px}.bar{flex:1;min-width:8px;background:var(--brand);border-radius:4px 4px 0 0}
.empty{padding:18px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:6px}
.screen-only{display:block}
@media(max-width:860px){.cover,.report-head,.cols2,.cols3,.kpis{grid-template-columns:1fr}.price{text-align:left}.topbar{align-items:flex-start;display:grid}.search{width:100%}h1{font-size:34px}.page{padding:22px 14px 54px}.sheet,.paper{padding:16px}}
@media(max-width:520px){h1{font-size:29px}h2{font-size:22px}.controls{width:100%}.controls button{flex:1}.metric b{font-size:21px}th,td{font-size:13px;padding:8px 6px}}
@media print{.top,.screen-only{display:none}.page{max-width:none;padding:0}.sheet,.paper{box-shadow:none;break-inside:avoid}body{background:white}.report{page-break-before:always}}
</style>
</head>
<body>
<header class="top screen-only"><div class="topbar"><div class="brand">FinAnalysis · Kami Report</div><div class="controls"><input class="search" id="q"><button id="langZh">中</button><button id="langEn">EN</button><button id="themeToggle">夜间</button><button class="primary" onclick="print()" id="printBtn">打印</button></div></div></header>
<main class="page">
  <section class="cover">
    <div>
      <p class="eyebrow" id="coverEye"></p>
      <h1 id="coverTitle"></h1>
      <p class="muted" id="coverMeta"></p>
      <p class="quote" id="coverSummary"></p>
    </div>
    <aside class="sheet">
      <div class="metric"><b id="riskScore"></b><span id="riskLabel"></span></div>
      <div style="height:12px"></div>
      <p class="small muted" id="freshness"></p>
    </aside>
  </section>
  <nav class="toc screen-only" id="toc"></nav>
  <section class="sheet" id="portfolio"></section>
  <section id="reports"></section>
  <section class="sheet report" id="newsFeed"></section>
</main>
<script id="report-data" type="application/json">__DATA__</script>
<script>
const R=JSON.parse(document.getElementById('report-data').textContent),S=R.stocks||[],M=R.portfolio_metrics||{};
let L=localStorage.fa_lang||'zh',T=localStorage.fa_theme==='dark'?'dark':'light',filter='';
const I={zh:{portfolio:'组合总览',single:'个股深度分析',reports:'全部报表',assets:'资产清单',actions:'重点事项',allocation:'市场分布',thesis:'投资逻辑',price:'价格走势',tech:'技术指标',risk:'风险提示',news:'Smart News Feed',sources:'数据来源',empty:'暂无数据',search:'搜索股票或新闻',print:'打印',night:'夜间',day:'日间',current:'现价',change:'涨跌幅',cost:'成本',pl:'盈亏',score:'风险评分',count:'资产数量',total:'估算总资产',daychg:'今日变动',ai:'AI 分析摘要',signals:'信号'},en:{portfolio:'Portfolio Brief',single:'Asset Deep Dive',reports:'All Reports',assets:'Assets',actions:'Priority Actions',allocation:'Market Allocation',thesis:'Investment Logic',price:'Price Action',tech:'Technical Indicators',risk:'Risk Notes',news:'Smart News Feed',sources:'Data Sources',empty:'No data',search:'Search stocks or news',print:'Print',night:'Night',day:'Day',current:'Current',change:'Change',cost:'Cost',pl:'P/L',score:'Risk Score',count:'Assets',total:'Est. Assets',daychg:'Day Change',ai:'AI Analyst Brief',signals:'Signals'}};
function d(){return I[L]}function e(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function n(x){return x==null||isNaN(Number(x))?'N/A':Number(x).toLocaleString(L==='zh'?'zh-CN':'en-US',{maximumFractionDigits:2})}
function pct(x){return x==null||isNaN(Number(x))?'N/A':Number(x).toFixed(2)+'%'}
function cls(x){return Number(x)>0?'up':Number(x)<0?'down':''}
function money(v,c){return (c?e(c)+' ':'')+n(v)}
function riskTag(r){let k=(r||'low').toLowerCase();return `<span class="tag ${e(k)}">${e(r||'low')}</span>`}
function slug(s){return String(s||'').replace(/[^A-Za-z0-9_-]+/g,'-')}
function visibleStocks(){let q=filter.trim().toLowerCase();if(!q)return S;return S.filter(s=>(`${s.ticker} ${s.name} ${(s.news||[]).map(n=>n.title).join(' ')}`).toLowerCase().includes(q))}
function renderCover(){document.documentElement.lang=L==='zh'?'zh-CN':'en';document.documentElement.dataset.theme=T;localStorage.fa_lang=L;localStorage.fa_theme=T;q.placeholder=d().search;printBtn.textContent=d().print;themeToggle.textContent=T==='dark'?d().day:d().night;langZh.classList.toggle('active',L==='zh');langEn.classList.toggle('active',L==='en');let first=S[0]||{},single=R.share_mode||S.length===1;coverEye.textContent=single?d().single:d().portfolio;coverTitle.textContent=single?`${first.name||''} ${first.ticker||''}`:d().portfolio;coverMeta.textContent=`${R.run_time||''} · ${R.mode||'manual'} · AI ${R.ai_status||'unknown'}`;coverSummary.textContent=single?(first.ai_commentary||R.overall_status||''):(R.summary_for_push||R.overall_status||'');riskScore.textContent=M.risk_score??'N/A';riskLabel.textContent=d().score;freshness.textContent=`${d().count}: ${M.asset_count||S.length} · ${d().news}: ${M.news_count||0}`}
function renderToc(){let stocks=visibleStocks();let links=[];if(!R.share_mode)links.push(`<a href="#portfolio">${d().portfolio}</a>`);stocks.forEach(s=>links.push(`<a href="#stock-${slug(s.ticker)}">${e(s.ticker)} ${e(s.name)}</a>`));links.push(`<a href="#newsFeed">${d().news}</a>`);toc.innerHTML=links.join('')}
function renderPortfolio(){if(R.share_mode){portfolio.style.display='none';return}portfolio.style.display='block';let actions=(R.priority_actions||[]).slice(0,6).map(a=>`<tr><td><b>${e(a.ticker)}</b><br><span class=muted>${e(a.name)}</span></td><td>${e(a.reason)}</td><td>${e(a.action)}</td><td>${riskTag(a.urgency||'watch')}</td></tr>`).join('')||`<tr><td colspan=4>${d().empty}</td></tr>`;let rows=visibleStocks().map(s=>{let pl=s.cost&&s.price?(s.price-s.cost)/s.cost*100:null;return `<tr><td><b>${e(s.ticker)}</b><br><span class=muted>${e(s.name)}</span></td><td>${e(s.market)}</td><td class=num>${money(s.price,s.currency||M.base_currency)}</td><td class="num ${cls(s.change_pct)}">${pct(s.change_pct)}</td><td>${riskTag(s.computed_risk_level)}</td></tr>`}).join('')||`<tr><td colspan=5>${d().empty}</td></tr>`;let alloc=Object.entries(M.market_allocation||{}).map(([k,v])=>`<span class=tag>${e(k)} ${pct(v)}</span>`).join('')||d().empty;let movers=(M.top_movers&&M.top_movers.length?M.top_movers:S.slice(0,6)),mx=Math.max(1,...movers.map(s=>Math.abs(Number(s.change_pct||0))));let bars=movers.map(s=>`<div title="${e(s.ticker)} ${pct(s.change_pct)}" class=bar style="height:${18+Math.abs(Number(s.change_pct||0))/mx*112}px;background:${Number(s.change_pct||0)>=0?'var(--up)':'var(--down)'}"></div>`).join('');portfolio.innerHTML=`<p class=eyebrow>${d().portfolio}</p><h2>${d().portfolio}</h2><div class="grid kpis"><div class=metric><b>${money(M.total_value,M.base_currency)}</b><span>${d().total}</span></div><div class=metric><b class="${cls(M.day_change_pct)}">${pct(M.day_change_pct)}</b><span>${d().daychg}</span></div><div class=metric><b>${M.risk_score??'N/A'}</b><span>${d().score}</span></div><div class=metric><b>${M.asset_count||S.length}</b><span>${d().count}</span></div></div><div class="grid cols2 section"><div><h3>${d().actions}</h3><table><tbody>${actions}</tbody></table></div><div><h3>${d().allocation}</h3><p>${alloc}</p><div class=bars>${bars}</div></div></div><div class=section><h3>${d().assets}</h3><table><thead><tr><th>Ticker</th><th>Market</th><th class=num>${d().current}</th><th class=num>${d().change}</th><th>${d().risk}</th></tr></thead><tbody>${rows}</tbody></table></div>`}
function stockReport(s){let news=(s.news||[]).slice(0,5).map(n=>`<div class=news-item><a href="${e(n.url||'#')}" target="_blank" rel="noreferrer">${e(n.title)}</a><p class="small muted">${e(n.source)} · ${e(n.sentiment)} · ${e(n.published_at)}</p></div>`).join('')||`<div class=empty>${d().empty}</div>`;let sig=(s.signals||s.risk_signals||[]).map(x=>`<span class=tag>${e(x)}</span>`).join('')||`<span class=muted>${d().empty}</span>`;let ind=s.indicators||{};return `<article class="paper report" id="stock-${slug(s.ticker)}"><div class=report-head><div><p class=eyebrow>${d().single}</p><h2>${e(s.name)} ${e(s.ticker)}</h2><p class=muted>${e(s.market)} · ${e(s.source||'yfinance / akshare')} · ${e(s.type||'watchlist')}</p></div><div class=price><b>${money(s.price,s.currency||M.base_currency)}</b><span class="${cls(s.change_pct)}">${pct(s.change_pct)}</span></div></div><div class="grid cols2"><section><h3>${d().thesis}</h3><p class=quote>${e(s.ai_commentary||s.suggested_action||R.overall_status||d().empty)}</p><p>${sig}</p></section><section><h3>${d().risk}</h3><p>${riskTag(s.computed_risk_level||s.risk_level)} <span class=tag>${e(s.suggested_action||'watch')}</span></p><p class=muted>${e((s.risk_signals||[]).join(' · ')||s.watch_reason||'')}</p></section></div><div class="grid cols3 section"><div class=metric><b>${money(s.cost,s.currency||M.base_currency)}</b><span>${d().cost}</span></div><div class=metric><b class="${cls(s.change_pct)}">${pct(s.change_pct)}</b><span>${d().change}</span></div><div class=metric><b>${pct(s.indicators?.change_5d_pct)}</b><span>5D</span></div></div><div class="grid cols2 section"><section><h3>${d().tech}</h3><table><tbody><tr><th>MA5</th><td>${n(ind.ma5)}</td></tr><tr><th>MA20</th><td>${n(ind.ma20)}</td></tr><tr><th>MA60</th><td>${n(ind.ma60)}</td></tr><tr><th>RSI</th><td>${n(ind.rsi)}</td></tr></tbody></table></section><section><h3>${d().news}</h3><div class=news>${news}</div></section></div><div class=section><h3>${d().sources}</h3><p class="small muted">yfinance / akshare · Google Sheet · Bing News / Google News RSS</p></div></article>`}
function renderReports(){reports.innerHTML=visibleStocks().map(stockReport).join('')||`<div class=empty>${d().empty}</div>`}
function renderFeed(){let items=visibleStocks().flatMap(s=>(s.news||[]).map(n=>({...n,ticker:s.ticker}))).slice(0,18);newsFeed.innerHTML=`<p class=eyebrow>${d().news}</p><h2>${d().news}</h2><div class=news>${items.map(n=>`<div class=news-item><a href="${e(n.url||'#')}" target=_blank rel=noreferrer>${e(n.ticker)} · ${e(n.title)}</a><p class="small muted">${e(n.source)} · ${e(n.sentiment)} · ${e(n.published_at)}</p></div>`).join('')||`<div class=empty>${d().empty}</div>`}</div>`}
function render(){renderCover();renderToc();renderPortfolio();renderReports();renderFeed()}
langZh.onclick=()=>{L='zh';render()};langEn.onclick=()=>{L='en';render()};themeToggle.onclick=()=>{T=T==='dark'?'light':'dark';render()};q.oninput=ev=>{filter=ev.target.value;renderToc();renderPortfolio();renderReports();renderFeed()};render();
</script>
</body>
</html>"""


def render_html(report: Dict[str, Any], color_convention: str = "CN") -> str:
    data = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    up_color = "#C62828" if color_convention == "CN" else "#17803B"
    down_color = "#17803B" if color_convention == "CN" else "#C62828"
    return _TEMPLATE.replace("__DATA__", data).replace("__UP__", up_color).replace("__DOWN__", down_color)
