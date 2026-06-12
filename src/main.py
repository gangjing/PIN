from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

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
