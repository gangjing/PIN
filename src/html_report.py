from __future__ import annotations

import json
from typing import Any, Dict


def render_html(report: Dict[str, Any], color_convention: str = "CN") -> str:
    data = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    up_color = "#c62828" if color_convention == "CN" else "#17803b"
    down_color = "#17803b" if color_convention == "CN" else "#c62828"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>自动看盘报告</title>
<style>
:root {{ --up:{up_color}; --down:{down_color}; --risk:#c62828; --warn:#b26a00; --ok:#17803b; --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --bg:#f7f8fa; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif; color:var(--ink); background:var(--bg); }}
header {{ padding:20px; background:#111827; color:white; }}
header h1 {{ margin:0 0 8px; font-size:24px; }}
.meta {{ color:#cbd5e1; display:flex; gap:14px; flex-wrap:wrap; }}
main {{ max-width:1220px; margin:0 auto; padding:16px; }}
.overview {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin:14px 0; }}
.tile {{ background:white; border:1px solid var(--line); border-radius:8px; padding:12px; }}
.tile strong {{ display:block; font-size:20px; margin-top:6px; }}
.toolbar {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:12px 0; }}
button, input, select {{ border:1px solid var(--line); background:white; color:var(--ink); border-radius:6px; padding:8px 10px; font-size:14px; }}
button.active {{ background:#111827; color:white; }}
input {{ min-width:220px; }}
table {{ width:100%; border-collapse:collapse; background:white; border:1px solid var(--line); }}
th, td {{ padding:10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:14px; }}
th {{ background:#f3f4f6; color:#374151; position:sticky; top:0; }}
tr.stock-row {{ cursor:pointer; }}
tr.stock-row:hover {{ background:#f9fafb; }}
.detail {{ display:none; background:#fbfdff; }}
.detail.open {{ display:table-row; }}
.detail-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; padding:14px; }}
.pill {{ display:inline-block; padding:3px 7px; border-radius:999px; background:#eef2ff; margin:2px; font-size:12px; }}
.risk-high {{ color:white; background:var(--risk); }}
.risk-medium {{ color:#7a4d00; background:#fff3cd; }}
.risk-low {{ color:#0f5132; background:#d1e7dd; }}
.up {{ color:var(--up); font-weight:700; }}
.down {{ color:var(--down); font-weight:700; }}
.action {{ color:#111827; font-weight:700; }}
.news {{ margin:0; padding-left:18px; }}
.muted {{ color:var(--muted); }}
@media (max-width: 760px) {{ table {{ display:block; overflow-x:auto; }} th, td {{ white-space:nowrap; }} .detail-grid {{ display:block; }} .tile {{ margin-bottom:8px; }} }}
@media print {{ .toolbar {{ display:none; }} body {{ background:white; }} header {{ color:#111827; background:white; border-bottom:1px solid var(--line); }} }}
</style>
</head>
<body>
<header>
  <h1>自动看盘报告</h1>
  <div class="meta"><span id="runTime"></span><span id="mode"></span><span id="status"></span></div>
</header>
<main>
  <section class="overview" id="overview"></section>
  <section class="tile">
    <div class="toolbar">
      <input id="search" placeholder="搜索代码或名称">
      <button data-filter="market" data-value="ALL" class="active">全部</button>
      <button data-filter="market" data-value="CN">A 股</button>
      <button data-filter="market" data-value="HK">港股</button>
      <button data-filter="market" data-value="US">美股</button>
      <button data-filter="type" data-value="ALL" class="active">全部类型</button>
      <button data-filter="type" data-value="holding">持仓</button>
      <button data-filter="type" data-value="watchlist">关注</button>
      <button data-filter="risk" data-value="ALL" class="active">全部风险</button>
      <button data-filter="risk" data-value="high">高风险</button>
      <button data-filter="risk" data-value="medium">中风险</button>
      <button data-filter="risk" data-value="low">低风险</button>
      <button id="copySummary">复制摘要</button>
      <button id="exportJson">导出 JSON</button>
      <button onclick="window.print()">打印</button>
    </div>
    <table>
      <thead><tr><th>市场</th><th>代码</th><th>名称</th><th>类型</th><th>当前价</th><th>涨跌幅</th><th>成本价</th><th>盈亏</th><th>仓位</th><th>风险</th><th>新闻</th><th>触发信号</th><th>建议动作</th></tr></thead>
      <tbody id="stockBody"></tbody>
    </table>
  </section>
</main>
<script id="report-data" type="application/json">{data}</script>
<script>
const report = JSON.parse(document.getElementById('report-data').textContent);
const filters = {{ market:'ALL', type:'ALL', risk:'ALL', search:'' }};
const pct = v => v === null || v === undefined ? '数据不足' : `${{Number(v).toFixed(2)}}%`;
const money = v => v === null || v === undefined ? '数据不足' : Number(v).toFixed(2);
const riskClass = r => r === 'high' ? 'risk-high' : r === 'medium' ? 'risk-medium' : 'risk-low';
const changeClass = v => Number(v) >= 0 ? 'up' : 'down';
function signalText(s) {{ return (s || []).length ? s.join(', ') : '暂无'; }}
function renderOverview() {{
  document.getElementById('runTime').textContent = `运行时间：${{report.run_time || ''}}`;
  document.getElementById('mode').textContent = `模式：${{report.mode || ''}}`;
  document.getElementById('status').textContent = `结论：${{report.overall_status || 'neutral'}}`;
  const stocks = report.stocks || [];
  const high = stocks.filter(s => s.computed_risk_level === 'high').length;
  const actions = report.priority_actions || [];
  const markets = Object.entries(report.market_summary || {{}}).map(([k,v]) => `<div class="tile"><span>${{k}} 市场</span><strong>${{v.status || 'unknown'}}</strong><div class="muted">${{(v.indices || []).map(i => `${{i.ticker}} ${{pct(i.change_pct)}}`).join(' / ')}}</div></div>`).join('');
  document.getElementById('overview').innerHTML = `<div class="tile"><span>整体结论</span><strong>${{report.overall_status || 'neutral'}}</strong></div><div class="tile"><span>高风险股票</span><strong>${{high}}</strong></div><div class="tile"><span>重点动作</span><strong>${{actions.length}}</strong></div>${{markets}}`;
}}
function rowMatches(s) {{
  const q = filters.search.toLowerCase();
  return (filters.market === 'ALL' || s.market === filters.market)
    && (filters.type === 'ALL' || s.type === filters.type)
    && (filters.risk === 'ALL' || s.computed_risk_level === filters.risk)
    && (!q || `${{s.ticker}} ${{s.name}}`.toLowerCase().includes(q));
}}
function renderRows() {{
  const body = document.getElementById('stockBody');
  body.innerHTML = '';
  (report.stocks || []).filter(rowMatches).forEach((s, idx) => {{
    const pnl = s.cost && s.price ? (s.price - s.cost) / s.cost * 100 : null;
    const tr = document.createElement('tr');
    tr.className = 'stock-row';
    tr.innerHTML = `<td>${{s.market}}</td><td>${{s.ticker}}</td><td>${{s.name}}</td><td>${{s.type}}</td><td>${{money(s.price)}}</td><td class="${{changeClass(s.change_pct)}}">${{pct(s.change_pct)}}</td><td>${{money(s.cost)}}</td><td class="${{changeClass(pnl)}}">${{pct(pnl)}}</td><td>${{s.position_pct ?? ''}}</td><td><span class="pill ${{riskClass(s.computed_risk_level)}}">${{s.computed_risk_level}}</span></td><td>${{(s.news || []).length}} 条</td><td>${{signalText(s.signals)}}</td><td class="action">${{s.suggested_action || ''}}</td>`;
    const detail = document.createElement('tr');
    detail.className = 'detail';
    const searchLink = s.news_search_url ? `<p><a href="${{s.news_search_url}}" target="_blank" rel="noreferrer">打开新闻搜索</a></p>` : '';
    const news = (s.news || []).map(n => `<li><a href="${{n.url}}" target="_blank" rel="noreferrer">${{n.title}}</a><br><span class="muted">${{n.source}}｜${{n.sentiment}}｜${{n.importance}}｜${{n.published_at || ''}}</span><br><span>${{n.summary || ''}}</span></li>`).join('') || '<li>未返回新闻条目，请打开新闻搜索核对。</li>';
    detail.innerHTML = `<td colspan="13"><div class="detail-grid"><div><h3>行情摘要</h3><p>52周高低：${{money(s.high_52w)}} / ${{money(s.low_52w)}}<br>成交量：${{s.volume ?? '数据不足'}}<br>来源：${{s.source || 'unknown'}} ${{s.source_url ? `<a href="${{s.source_url}}" target="_blank">链接</a>` : ''}}</p></div><div><h3>技术面</h3><p>MA5：${{money(s.indicators?.ma5)}}<br>MA20：${{money(s.indicators?.ma20)}}<br>MA60：${{money(s.indicators?.ma60)}}<br>5日/20日：${{pct(s.indicators?.change_5d_pct)}} / ${{pct(s.indicators?.change_20d_pct)}}</p></div><div><h3>风险与机会</h3><p>风险：${{signalText(s.risk_signals)}}<br>机会：${{signalText(s.opportunity_signals)}}<br>建议：<b>${{s.suggested_action || ''}}</b></p></div><div><h3>新闻面</h3>${{searchLink}}<ul class="news">${{news}}</ul></div><div><h3>AI 分析</h3><p>${{s.ai_commentary || '暂无'}}</p></div></div></td>`;
    tr.addEventListener('click', () => detail.classList.toggle('open'));
    body.appendChild(tr); body.appendChild(detail);
  }});
}}
document.querySelectorAll('button[data-filter]').forEach(btn => btn.addEventListener('click', () => {{
  const type = btn.dataset.filter; filters[type] = btn.dataset.value;
  document.querySelectorAll(`button[data-filter="${{type}}"]`).forEach(b => b.classList.remove('active'));
  btn.classList.add('active'); renderRows();
}}));
document.getElementById('search').addEventListener('input', e => {{ filters.search = e.target.value; renderRows(); }});
document.getElementById('copySummary').addEventListener('click', async () => {{ await navigator.clipboard.writeText(report.summary_for_push || ''); alert('摘要已复制'); }});
document.getElementById('exportJson').addEventListener('click', () => {{ const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)], {{type:'application/json'}})); a.download = 'latest_report.json'; a.click(); }});
renderOverview(); renderRows();
</script>
</body>
</html>"""
