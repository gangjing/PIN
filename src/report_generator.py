from __future__ import annotations

import copy
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .signal_engine import OPPORTUNITY_SIGNAL_LABELS, RISK_SIGNAL_LABELS
from .utils import ROOT, money, pct, timestamp_for_file, write_json


def labeled_stock_signals(report: Dict[str, Any], key: str, labels: Dict[str, str], limit: int) -> List[str]:
    rows = []
    for stock in report.get("stocks", []):
        signals = stock.get(key) or []
        if not signals:
            continue
        reason = "、".join(labels.get(signal, signal) for signal in signals[:3])
        rows.append(f"- {stock.get('ticker')} {stock.get('name')}：{reason}")
        if len(rows) >= limit:
            break
    return rows


def make_summary(report: Dict[str, Any], html_path: str = "") -> str:
    actions = report.get("priority_actions", [])[:3]
    risks = labeled_stock_signals(report, "risk_signals", RISK_SIGNAL_LABELS, 2)
    opportunities = labeled_stock_signals(report, "opportunity_signals", OPPORTUNITY_SIGNAL_LABELS, 2)
    lines = [
        f"# 今日看盘提醒｜{report.get('run_time', '')}",
        f"结论：{report.get('overall_status', 'neutral')}",
        "需要你马上看的股票：",
    ]
    if actions:
        for idx, item in enumerate(actions, 1):
            lines.append(f"{idx}. {item.get('ticker')} {item.get('name')}：{item.get('reason')}，建议：{item.get('action')}")
    else:
        lines.append("暂无必须马上处理的股票，继续观察。")
    lines.append("风险：")
    lines.extend(risks or ["- 暂无明确风险信号"])
    lines.append("机会：")
    lines.extend(opportunities or ["- 暂无明确机会信号，不建议追高"])
    if html_path:
        lines.append(f"完整 HTML 报告：{html_path}")
    lines.append("免责声明：本报告仅用于辅助决策，不构成投资建议。最终交易由本人判断。")
    return "\n".join(lines)


def make_markdown_report(report: Dict[str, Any]) -> str:
    rows = [
        "# 自动看盘报告",
        f"运行时间：{report.get('run_time')}",
        f"模式：{report.get('mode')}",
        f"总体结论：{report.get('overall_status')}",
        "",
        "## 重点处理",
    ]
    for item in report.get("priority_actions", []):
        rows.append(f"- **{item['ticker']} {item['name']}**：{item['reason']}；建议：{item['action']}")
    rows.append("")
    rows.append("## 股票明细")
    for stock in report.get("stocks", []):
        rows.extend([
            f"### {stock.get('ticker')} {stock.get('name')}",
            f"- 当前价：{money(stock.get('price'))}",
            f"- 涨跌幅：{pct(stock.get('change_pct'))}",
            f"- 风险等级：{stock.get('computed_risk_level')}",
            f"- 信号：{', '.join(stock.get('signals') or ['暂无'])}",
            f"- 建议：{stock.get('suggested_action')}",
            f"- AI/规则分析：{stock.get('ai_commentary', '暂无')}",
        ])
    return "\n".join(rows)


def apply_privacy(report: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    privacy = config.get("privacy") or {}
    if not privacy.get("hide_sensitive_fields"):
        return report
    for stock in report.get("stocks", []):
        if privacy.get("hide_quantity", True):
            stock["quantity"] = None
        if privacy.get("hide_cost", False):
            stock["cost"] = None
        if privacy.get("hide_position_pct", False):
            stock["position_pct"] = None
    return report


PUBLIC_STOCK_REMOVE_FIELDS = {
    "quantity",
    "cost",
    "position_pct",
    "take_profit",
    "stop_loss",
    "watch_reason",
    "notes",
}


def public_stock_slug(ticker: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", ticker.strip().upper()).strip("-")
    if not slug:
        raise ValueError("ticker is required for public stock share page")
    return slug


def sanitize_public_stock(stock: Dict[str, Any]) -> Dict[str, Any]:
    public = copy.deepcopy(stock)
    for field in PUBLIC_STOCK_REMOVE_FIELDS:
        public.pop(field, None)
    if public.get("type") == "holding":
        public["type"] = "watchlist"
    return public


def sanitize_public_action(action: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"ticker", "name", "reason", "action", "urgency"}
    return {key: copy.deepcopy(value) for key, value in action.items() if key in allowed}


def make_public_stock_report(report: Dict[str, Any], ticker: str) -> Dict[str, Any]:
    stock = next((item for item in report.get("stocks", []) if item.get("ticker") == ticker), None)
    if not stock:
        raise ValueError(f"stock not found for share page: {ticker}")

    public_stock = sanitize_public_stock(stock)
    actions = [
        sanitize_public_action(action)
        for action in report.get("priority_actions", [])
        if action.get("ticker") == ticker
    ]
    news_count = len(public_stock.get("news") or [])
    negative_news_count = sum(1 for item in public_stock.get("news") or [] if item.get("sentiment") == "negative")
    risk_level = public_stock.get("computed_risk_level") or "low"
    risk_score = min(100, 36 + (32 if risk_level == "high" else 14 if risk_level == "medium" else 0) + negative_news_count * 6)

    public_report = {
        "run_time": report.get("run_time"),
        "mode": report.get("mode"),
        "overall_status": report.get("overall_status"),
        "ai_status": report.get("ai_status"),
        "share_mode": True,
        "share_ticker": ticker,
        "market_summary": {
            public_stock.get("market"): (report.get("market_summary") or {}).get(public_stock.get("market"), {})
        },
        "priority_actions": actions,
        "portfolio_metrics": {
            "base_currency": public_stock.get("currency") or "CNY",
            "total_value": None,
            "cost_value": None,
            "day_change_amount": None,
            "day_change_pct": public_stock.get("change_pct"),
            "pnl_amount": None,
            "pnl_pct": None,
            "risk_score": risk_score,
            "risk_label": risk_level,
            "holding_count": 0,
            "asset_count": 1,
            "critical_alerts": 1 if risk_level == "high" else 0,
            "medium_alerts": 1 if risk_level == "medium" else 0,
            "news_count": news_count,
            "negative_news_count": negative_news_count,
            "market_allocation": {},
            "top_movers": [{
                "ticker": public_stock.get("ticker"),
                "name": public_stock.get("name"),
                "market": public_stock.get("market"),
                "change_pct": public_stock.get("change_pct"),
                "value": None,
            }],
        },
        "stocks": [public_stock],
        "summary_for_push": "",
        "warnings": [],
    }
    public_report["summary_for_push"] = make_summary(public_report)
    return public_report


def make_private_landing_html(base_url: str = "") -> str:
    message = "完整组合报告是私人内容。请使用单只股票分享链接打开公开页面。"
    link = f'<p><a href="{base_url.rstrip("/")}/share/">打开分享目录</a></p>' if base_url else ""
    return (
        "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>FinAnalysis Private</title>"
        "<style>body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC',Arial,sans-serif;"
        "background:#f6f7f9;color:#111827;display:grid;place-items:center;min-height:100vh}"
        "main{max-width:680px;padding:32px}h1{font-size:28px;margin:0 0 12px}p{color:#5b6472;line-height:1.7}"
        "a{color:#111827;font-weight:700}</style><main><h1>FinAnalysis</h1>"
        f"<p>{message}</p>{link}</main></html>"
    )


def make_share_index_html(share_pages: Dict[str, str]) -> str:
    links = "\n".join(
        f'<li><a href="{path}">{ticker}</a></li>'
        for ticker, path in sorted(share_pages.items())
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>FinAnalysis Stock Shares</title>"
        "<style>body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC',Arial,sans-serif;"
        "background:#f6f7f9;color:#111827}main{max-width:760px;margin:auto;padding:28px}"
        "li{margin:10px 0}a{color:#111827;font-weight:750}</style><main>"
        "<h1>单股分享页面</h1><p>这些页面只包含对应股票的公开分析信息，不包含完整组合和个人持仓数据。</p>"
        f"<ul>{links}</ul></main></html>"
    )


def write_outputs(
    report: Dict[str, Any],
    config: Dict[str, Any],
    html: str,
    share_htmls: Optional[Dict[str, str]] = None,
) -> Dict[str, Path]:
    stamp = timestamp_for_file()
    report_html = ROOT / "reports" / f"market_report_{stamp}.html"
    latest_html = ROOT / "output" / "latest_report.html"
    latest_json = ROOT / "output" / "latest_report.json"
    latest_md = ROOT / "output" / "latest_summary.md"
    markdown_report = ROOT / "output" / "latest_report.md"

    report_html.write_text(html, encoding="utf-8")
    latest_html.write_text(html, encoding="utf-8")
    write_json(latest_json, report)

    display_path = str(latest_html)
    base_url = os.getenv("REPORT_BASE_URL") or os.getenv("GITHUB_PAGES_URL") or config.get("report_base_url") or ""
    if base_url:
        display_path = base_url.rstrip("/") + "/latest_report.html"
    summary = report.get("summary_for_push") or make_summary(report, display_path)
    report["summary_for_push"] = summary
    latest_md.write_text(summary, encoding="utf-8")
    markdown_report.write_text(make_markdown_report(report), encoding="utf-8")
    write_json(latest_json, report)

    public_site = config.get("public_site") or {}
    docs_root = ROOT / "docs"
    docs_latest = docs_root / "latest_report.html"
    docs_index = docs_root / "index.html"
    docs_reports = docs_root / "reports"
    docs_share = docs_root / "share"

    if docs_reports.exists() and not public_site.get("publish_full_report", False):
        shutil.rmtree(docs_reports)
    if docs_share.exists():
        shutil.rmtree(docs_share)
    docs_share.mkdir(parents=True, exist_ok=True)

    share_pages: Dict[str, str] = {}
    for ticker, share_html in (share_htmls or {}).items():
        filename = public_stock_slug(ticker) + ".html"
        (docs_share / filename).write_text(share_html, encoding="utf-8")
        share_pages[ticker] = f"share/{filename}"

    if public_site.get("publish_full_report", False):
        docs_report = docs_reports / report_html.name
        docs_reports.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(latest_html, docs_latest)
        shutil.copyfile(report_html, docs_report)
        docs_index.write_text(html, encoding="utf-8")
    else:
        landing = make_private_landing_html(os.getenv("REPORT_BASE_URL") or os.getenv("GITHUB_PAGES_URL") or config.get("report_base_url") or "")
        docs_latest.write_text(landing, encoding="utf-8")
        docs_index.write_text(landing, encoding="utf-8")
    if share_pages and public_site.get("show_share_index", False):
        (docs_share / "index.html").write_text(make_share_index_html(share_pages), encoding="utf-8")
    else:
        (docs_share / "index.html").write_text(make_private_landing_html(), encoding="utf-8")

    share_links = ROOT / "output" / "share_links.md"
    base_url = os.getenv("REPORT_BASE_URL") or os.getenv("GITHUB_PAGES_URL") or config.get("report_base_url") or ""
    rows = ["# 单股分享链接", ""]
    for ticker, path in sorted(share_pages.items()):
        url = f"{base_url.rstrip('/')}/{path}" if base_url else str(docs_root / path)
        rows.append(f"- {ticker}: {url}")
    share_links.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {"html": latest_html, "json": latest_json, "summary": latest_md, "archive_html": report_html}
