from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一个谨慎的个人投资看盘助理。必须用中文输出。不要承诺收益，不要说“必买”“一定上涨”“稳赚”“无风险”“必须满仓”。建议必须说明依据；数据不足时明确说“数据不足”。输出 JSON。"""


def local_analysis(report: Dict[str, Any]) -> Dict[str, Any]:
    high = [a for a in report.get("priority_actions", []) if a.get("urgency") == "high"]
    status = "cautious" if high else "active_watch" if report.get("priority_actions") else "neutral"
    report["overall_status"] = status
    for stock in report.get("stocks", []):
        stock["ai_commentary"] = f"{stock.get('name')}当前建议：{stock.get('suggested_action')}。依据：{', '.join(stock.get('signals') or ['暂无明显信号'])}。本条为规则引擎生成，未调用 AI。"
    return report


def call_openai(report: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return local_analysis(report)
    payload = {
        "watchlist": [{k: s.get(k) for k in ["market", "ticker", "name", "type", "cost", "position_pct", "take_profit", "stop_loss"]} for s in report.get("stocks", [])],
        "market_data": report.get("stocks", []),
        "signals": [{s["ticker"]: s.get("signals", [])} for s in report.get("stocks", [])],
        "news": [{s["ticker"]: s.get("news", [])} for s in report.get("stocks", [])],
        "market_summary": report.get("market_summary", {}),
    }
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "请根据以下 JSON 生成结构化中文看盘分析，只返回 JSON：\n" + json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        ai = json.loads(content)
        merge_ai(report, ai)
        report["ai_status"] = "success"
        return report
    except Exception as exc:
        logger.warning("OpenAI failed: %s", exc)
        report["warnings"].append("OpenAI API 调用失败，已使用本地规则生成分析。")
        return local_analysis(report)


def merge_ai(report: Dict[str, Any], ai: Dict[str, Any]) -> None:
    report["overall_status"] = ai.get("overall_status", report.get("overall_status", "neutral"))
    if ai.get("market_summary"):
        report["ai_market_summary"] = ai["market_summary"]
    if ai.get("priority_actions"):
        report["priority_actions"] = ai["priority_actions"]
    by_ticker = {s["ticker"]: s for s in report.get("stocks", [])}
    for item in ai.get("stock_analysis", []):
        ticker = item.get("ticker")
        if ticker in by_ticker:
            by_ticker[ticker]["ai_commentary"] = item.get("analysis") or item.get("commentary") or json.dumps(item, ensure_ascii=False)
