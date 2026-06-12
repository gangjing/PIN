from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

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


def write_outputs(report: Dict[str, Any], config: Dict[str, Any], html: str) -> Dict[str, Path]:
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

    docs_latest = ROOT / "docs" / "latest_report.html"
    docs_index = ROOT / "docs" / "index.html"
    docs_report = ROOT / "docs" / "reports" / report_html.name
    shutil.copyfile(latest_html, docs_latest)
    shutil.copyfile(report_html, docs_report)
    docs_index.write_text(html, encoding="utf-8")
    return {"html": latest_html, "json": latest_json, "summary": latest_md, "archive_html": report_html}
