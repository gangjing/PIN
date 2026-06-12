from __future__ import annotations

import logging
from typing import Any, Dict, List

from .data_loader import WatchItem
from .indicators import compute_indicators

logger = logging.getLogger(__name__)


INDEX_TICKERS = {
    "CN": ["000001.SS", "399001.SZ", "399006.SZ"],
    "HK": ["^HSI"],
    "US": ["^IXIC", "^GSPC", "^DJI"],
}


def cn_to_yahoo(ticker: str) -> str:
    if ticker.endswith(".SH"):
        return ticker.replace(".SH", ".SS")
    return ticker


def fetch_with_yfinance(ticker: str) -> Dict[str, Any]:
    import yfinance as yf  # type: ignore

    data = yf.Ticker(ticker)
    hist = data.history(period="1y", interval="1d", auto_adjust=False)
    if hist.empty:
        raise ValueError(f"no yfinance history for {ticker}")
    closes = [float(x) for x in hist["Close"].dropna().tolist()]
    volumes = [float(x) for x in hist["Volume"].fillna(0).tolist()]
    price = closes[-1]
    prev = closes[-2] if len(closes) > 1 else price
    info = {}
    try:
        info = data.fast_info or {}
    except Exception:
        info = {}
    return {
        "price": price,
        "change_pct": None if prev == 0 else (price - prev) / prev * 100,
        "volume": volumes[-1] if volumes else None,
        "high_52w": float(max(closes)) if closes else None,
        "low_52w": float(min(closes)) if closes else None,
        "source": "yfinance",
        "source_url": f"https://finance.yahoo.com/quote/{ticker}",
        "history_closes": closes,
        "history_volumes": volumes,
        "currency": getattr(info, "currency", None) if not isinstance(info, dict) else info.get("currency"),
    }


def fetch_cn_with_akshare(ticker: str) -> Dict[str, Any]:
    import akshare as ak  # type: ignore

    symbol = ticker.split(".")[0]
    hist = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="")
    if hist.empty:
        raise ValueError(f"no akshare history for {ticker}")
    closes = [float(x) for x in hist["收盘"].dropna().tolist()]
    volumes = [float(x) for x in hist["成交量"].fillna(0).tolist()]
    price = closes[-1]
    prev = closes[-2] if len(closes) > 1 else price
    return {
        "price": price,
        "change_pct": None if prev == 0 else (price - prev) / prev * 100,
        "volume": volumes[-1] if volumes else None,
        "high_52w": float(max(closes[-250:])) if closes else None,
        "low_52w": float(min(closes[-250:])) if closes else None,
        "source": "akshare",
        "source_url": f"https://quote.eastmoney.com/{ticker.lower().replace('.', '')}.html",
        "history_closes": closes[-260:],
        "history_volumes": volumes[-260:],
        "currency": "CNY",
    }


def fetch_quote(item: WatchItem) -> Dict[str, Any]:
    if item.market == "CN":
        try:
            return fetch_cn_with_akshare(item.ticker)
        except Exception as exc:
            logger.warning("akshare failed for %s: %s; trying yfinance", item.ticker, exc)
            return fetch_with_yfinance(cn_to_yahoo(item.ticker))
    return fetch_with_yfinance(item.ticker)


def enrich_market_data(items: List[WatchItem]) -> List[Dict[str, Any]]:
    rows = []
    for item in items:
        quote = fetch_quote(item)
        indicators = compute_indicators(quote.get("history_closes", []), quote.get("history_volumes", []))
        rows.append({**item.to_dict(), **quote, "indicators": indicators})
    return rows


def fetch_market_summary(markets: List[str]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for market in markets:
        indices = []
        changes = []
        for ticker in INDEX_TICKERS.get(market, []):
            quote = fetch_with_yfinance(ticker)
            indices.append({"ticker": ticker, "price": quote.get("price"), "change_pct": quote.get("change_pct"), "source": quote.get("source")})
            if quote.get("change_pct") is not None:
                changes.append(float(quote["change_pct"]))
        avg = sum(changes) / len(changes) if changes else 0
        status = "strong" if avg >= 0.8 else "weak" if avg <= -0.8 else "neutral"
        summary[market] = {"status": status, "indices": indices}
    return summary
