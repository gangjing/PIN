from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ai_analyzer import call_openai, local_analysis
from src.data_loader import load_watchlist
from src.html_report import render_html
from src.market_data import enrich_market_data, fetch_market_summary
from src.news_fetcher import attach_news
from src.report_generator import apply_privacy, make_summary, write_outputs
from src.signal_engine import apply_signals, build_priority_actions
from src.utils import ensure_dirs, load_config, load_env, now_iso, setup_logging


logger = logging.getLogger(__name__)


def build_portfolio_metrics(stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_value = 0.0
    cost_value = 0.0
    day_change_amount = 0.0
    holding_count = 0
    allocation: Dict[str, float] = {}
    critical_count = 0
    medium_count = 0
    news_count = 0
    negative_news_count = 0
    top_movers = []

    for stock in stocks:
        price = stock.get("price")
        quantity = stock.get("quantity")
        cost = stock.get("cost")
        change_pct = stock.get("change_pct")
        value = None
        if price is not None and quantity:
            value = float(price) * float(quantity)
            total_value += value
            holding_count += 1
            market = stock.get("market") or "UNKNOWN"
            allocation[market] = allocation.get(market, 0.0) + value
            if change_pct is not None:
                previous = float(price) / (1 + float(change_pct) / 100) if float(change_pct) != -100 else float(price)
                day_change_amount += (float(price) - previous) * float(quantity)
        if cost is not None and quantity:
            cost_value += float(cost) * float(quantity)

        risk_level = stock.get("computed_risk_level")
        if risk_level == "high":
            critical_count += 1
        elif risk_level == "medium":
            medium_count += 1
        stock_news = stock.get("news") or []
        news_count += len(stock_news)
        negative_news_count += sum(1 for item in stock_news if item.get("sentiment") == "negative")
        if change_pct is not None:
            top_movers.append({
                "ticker": stock.get("ticker"),
                "name": stock.get("name"),
                "market": stock.get("market"),
                "change_pct": change_pct,
                "value": value,
            })

    pnl_amount = total_value - cost_value if cost_value else None
    pnl_pct = (pnl_amount / cost_value * 100) if cost_value and pnl_amount is not None else None
    day_change_pct = (day_change_amount / (total_value - day_change_amount) * 100) if total_value and total_value != day_change_amount else None
    risk_score = min(100, 28 + critical_count * 18 + medium_count * 7 + negative_news_count * 6)
    if critical_count:
        risk_label = "elevated"
    elif risk_score >= 55:
        risk_label = "watch"
    else:
        risk_label = "stable"

    allocation_pct = {}
    if total_value:
        allocation_pct = {market: value / total_value * 100 for market, value in allocation.items()}

    return {
        "base_currency": "CNY",
        "total_value": total_value if total_value else None,
        "cost_value": cost_value if cost_value else None,
        "day_change_amount": day_change_amount if total_value else None,
        "day_change_pct": day_change_pct,
        "pnl_amount": pnl_amount,
        "pnl_pct": pnl_pct,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "holding_count": holding_count,
        "asset_count": len(stocks),
        "critical_alerts": critical_count,
        "medium_alerts": medium_count,
        "news_count": news_count,
        "negative_news_count": negative_news_count,
        "market_allocation": allocation_pct,
        "top_movers": sorted(top_movers, key=lambda item: abs(float(item.get("change_pct") or 0)), reverse=True)[:6],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="个人每日自动看盘助手")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--watchlist", default=None)
    parser.add_argument("--mode", default="manual", choices=["manual", "morning", "afternoon", "pre_close"])
    parser.add_argument("--market", choices=["CN", "HK", "US"], default=None)
    parser.add_argument("--all", action="store_true", help="运行全部市场")
    parser.add_argument("--no-ai", action="store_true", help="不调用 OpenAI，只使用规则分析")
    parser.add_argument("--no-news", action="store_true", help="不抓取新闻")
    parser.add_argument("--html", action="store_true", help="生成 HTML；默认也会生成")
    parser.add_argument("--json", action="store_true", help="生成 JSON；默认也会生成")
    return parser.parse_args()


def build_report(args: argparse.Namespace, config: Dict[str, Any]) -> Dict[str, Any]:
    watchlist_path = args.watchlist or config.get("default_watchlist", "config/watchlist.sample.csv")
    items = load_watchlist(watchlist_path)
    if args.market and not args.all:
        items = [item for item in items if item.market == args.market]
    markets = sorted({item.market for item in items})
    logger.info("loaded %s enabled watchlist items", len(items))

    stocks = enrich_market_data(items)
    stocks = attach_news(stocks, disabled=args.no_news)
    stocks = apply_signals(stocks)
    warnings = sorted({stock.get("warning") for stock in stocks if stock.get("warning")})
    report: Dict[str, Any] = {
        "run_time": now_iso(),
        "mode": args.mode,
        "overall_status": "neutral",
        "market_summary": fetch_market_summary(markets),
        "priority_actions": build_priority_actions(stocks),
        "portfolio_metrics": build_portfolio_metrics(stocks),
        "stocks": stocks,
        "summary_for_push": "",
        "warnings": warnings,
        "ai_status": "skipped" if args.no_ai else "pending",
    }
    if args.no_ai:
        report = local_analysis(report)
        report["ai_status"] = "skipped"
    else:
        report = call_openai(report)
    report["priority_actions"] = report.get("priority_actions") or build_priority_actions(report["stocks"])
    report["summary_for_push"] = make_summary(report)
    return apply_privacy(report, config)


def main() -> int:
    args = parse_args()
    ensure_dirs()
    load_env()
    log_path = setup_logging()
    config = load_config(args.config)
    try:
        report = build_report(args, config)
        display_path = str(Path(__file__).resolve().parents[1] / "output" / "latest_report.html")
        report_base_url = os.getenv("REPORT_BASE_URL") or os.getenv("GITHUB_PAGES_URL") or config.get("report_base_url")
        if report_base_url:
            display_path = report_base_url.rstrip("/") + "/latest_report.html"
        report["summary_for_push"] = make_summary(report, display_path)
        html = render_html(report, config.get("color_convention", "CN"))
        paths = write_outputs(report, config, html)
        logger.info("summary=%s json=%s html=%s log=%s", paths["summary"], paths["json"], paths["html"], log_path)
        print(f"摘要：{paths['summary']}")
        print(f"JSON：{paths['json']}")
        print(f"HTML：{paths['html']}")
        print(f"归档 HTML：{paths['archive_html']}")
        return 0
    except Exception:
        logger.exception("market watch run failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
