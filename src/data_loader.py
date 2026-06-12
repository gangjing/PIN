from __future__ import annotations

import csv
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import ROOT


@dataclass
class WatchItem:
    market: str
    ticker: str
    name: str
    type: str = "watchlist"
    cost: Optional[float] = None
    quantity: Optional[float] = None
    position_pct: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    watch_reason: str = ""
    risk_level: str = "medium"
    enabled: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def to_float(value: str) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return None
    value = str(value).strip().replace(",", "").replace("%", "")
    if value.upper() in {"#N/A", "N/A", "NA", "NULL", "-"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_bool(value: str) -> bool:
    return str(value).strip().lower() not in {"false", "0", "no", "n", "否"}


def validate_ticker(market: str, ticker: str) -> bool:
    market = market.upper()
    if not ticker:
        return False
    if market == "HK":
        return ticker.endswith(".HK")
    if market == "CN":
        return ticker.endswith(".SZ") or ticker.endswith(".SH") or ticker.endswith(".BJ")
    if market == "US":
        return "." not in ticker or ticker.endswith((".US", ".NYSE", ".NASDAQ"))
    return False


def first_value(row: Dict[str, str], *keys: str, default: str = "") -> str:
    lower_map = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        value = row.get(key)
        if value is None:
            value = lower_map.get(key.lower())
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def normalize_ticker(raw_ticker: str, raw_market: str = "") -> tuple[str, str]:
    ticker = raw_ticker.strip().upper()
    market = raw_market.strip().upper()
    prefix_map = {
        "HKG": ("HK", ".HK"),
        "HK": ("HK", ".HK"),
        "SHE": ("CN", ".SZ"),
        "SZSE": ("CN", ".SZ"),
        "SHA": ("CN", ".SH"),
        "SHH": ("CN", ".SH"),
        "SSE": ("CN", ".SH"),
    }
    if ":" in ticker:
        prefix, code = ticker.split(":", 1)
        if prefix in prefix_map:
            market, suffix = prefix_map[prefix]
            width = 4 if market == "HK" else 6
            return f"{code.zfill(width)}{suffix}", market
    if ticker.endswith(".HK"):
        return ticker, "HK"
    if ticker.endswith((".SZ", ".SH", ".BJ")):
        return ticker, "CN"
    return ticker, market or "US"


def parse_action_goal(value: str) -> tuple[Optional[float], str]:
    text = value.strip()
    lower = text.lower()
    if "sell at" in lower:
        target = to_float(lower.split("sell at", 1)[1].strip())
        return target, text
    return None, text


def row_to_item(row: Dict[str, str]) -> WatchItem:
    ticker, inferred_market = normalize_ticker(
        first_value(row, "ticker", "Ticker", "代码", "证券代码"),
        first_value(row, "market", "Market", "市场"),
    )
    action_take_profit, action_notes = parse_action_goal(first_value(row, "Action Goal", "action_goal", "目标", "notes", "备注"))
    cost = to_float(first_value(row, "cost", "Avg Price", "avg_price", "成本价", "平均成本"))
    quantity = to_float(first_value(row, "quantity", "Shares", "shares", "持仓数量", "数量"))
    return WatchItem(
        market=inferred_market,
        ticker=ticker,
        name=first_value(row, "name", "Company Name", "company_name", "股票名称", "名称"),
        type=first_value(row, "type", "Type", "类型", default="holding" if quantity else "watchlist") or "watchlist",
        cost=cost,
        quantity=quantity,
        position_pct=to_float(first_value(row, "position_pct", "position %", "仓位比例", "仓位")),
        take_profit=to_float(first_value(row, "take_profit", "止盈价")) or action_take_profit,
        stop_loss=to_float(first_value(row, "stop_loss", "止损价")),
        watch_reason=first_value(row, "watch_reason", "watch reason", "关注理由"),
        risk_level=first_value(row, "risk_level", "risk level", "风险等级", default="medium") or "medium",
        enabled=to_bool(first_value(row, "enabled", "启用", default="true")),
        notes=first_value(row, "notes", "备注") or action_notes,
    )


def load_watchlist_csv(path: str) -> List[WatchItem]:
    csv_path = Path(path)
    if not csv_path.is_absolute():
        csv_path = ROOT / path
    items: List[WatchItem] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            item = row_to_item(row)
            if item.enabled and item.ticker:
                items.append(item)
    return items


def load_google_sheet_csv(sheet_id: str, gid: str = "0") -> List[WatchItem]:
    params = urllib.parse.urlencode({"format": "csv", "gid": gid})
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?{params}"
    with urllib.request.urlopen(url, timeout=20) as response:
        text = response.read().decode("utf-8-sig")
    rows = csv.DictReader(text.splitlines())
    items = []
    for row in rows:
        item = row_to_item(row)
        if item.enabled and item.ticker:
            items.append(item)
    return items


def load_watchlist(path: str, prefer_google_sheet: bool = True) -> List[WatchItem]:
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if prefer_google_sheet and sheet_id:
        gid = os.getenv("GOOGLE_SHEET_GID", "0")
        return load_google_sheet_csv(sheet_id, gid)
    if prefer_google_sheet:
        raise RuntimeError("GOOGLE_SHEET_ID is required; Google Sheet is the configured watchlist source.")
    return load_watchlist_csv(path)
