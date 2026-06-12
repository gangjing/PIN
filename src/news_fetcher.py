from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


def news_search_url(ticker: str, name: str) -> str:
    query = urllib.parse.quote(f"{ticker} {name} 财经 新闻 公告")
    return f"https://news.google.com/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"


def classify(title: str, summary: str = "") -> Dict[str, str]:
    text = f"{title} {summary}".lower()
    negative = ["处罚", "诉讼", "召回", "减持", "亏损", "下调", "调查", "风险", "事故", "跌"]
    positive = ["回购", "增持", "增长", "上调", "中标", "盈利", "突破", "合作", "批准", "涨"]
    sentiment = "neutral"
    if any(word in text for word in negative):
        sentiment = "negative"
    elif any(word in text for word in positive):
        sentiment = "positive"
    importance = "high" if any(word in text for word in negative[:5] + positive[:5]) else "medium"
    return {"sentiment": sentiment, "importance": importance}


def fetch_bing_news(ticker: str, name: str, hours: int = 72) -> List[Dict[str, Any]]:
    key = os.getenv("BING_SEARCH_API_KEY", "").strip()
    if not key:
        return []
    query = urllib.parse.quote(f"{ticker} {name} 财经 新闻 公告")
    url = f"https://api.bing.microsoft.com/v7.0/news/search?q={query}&freshness=Week&count=5&mkt=zh-CN"
    req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": key})
    with urllib.request.urlopen(req, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    items = []
    for row in payload.get("value", []):
        title = row.get("name", "")
        summary = row.get("description", "")
        cls = classify(title, summary)
        items.append({
            "ticker": ticker,
            "title": title,
            "source": (row.get("provider") or [{}])[0].get("name", "Bing News"),
            "url": row.get("url", ""),
            "published_at": row.get("datePublished") or datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            **cls,
        })
    return items


def fetch_rss_news(ticker: str, name: str) -> List[Dict[str, Any]]:
    import feedparser  # type: ignore

    query = urllib.parse.quote(f"{ticker} {name} 财经 新闻 公告")
    url = f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        content = response.read()
    feed = feedparser.parse(content)
    if getattr(feed, "bozo", False) and not getattr(feed, "entries", []):
        raise RuntimeError(f"Google News RSS parse failed for {ticker}: {getattr(feed, 'bozo_exception', '')}")
    items = []
    for entry in feed.entries[:5]:
        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "")
        cls = classify(title, summary)
        published = getattr(entry, "published", "")
        try:
            published_at = parsedate_to_datetime(published).isoformat() if published else datetime.now(timezone.utc).isoformat()
        except Exception:
            published_at = published or datetime.now(timezone.utc).isoformat()
        items.append({
            "ticker": ticker,
            "title": title,
            "source": "Google News RSS",
            "url": getattr(entry, "link", ""),
            "published_at": published_at,
            "summary": summary,
            **cls,
        })
    return items


def dedupe_news(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[str] = set()
    out = []
    for item in items:
        key = (item.get("url") or item.get("title") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def fetch_news_for_stock(ticker: str, name: str, disabled: bool = False) -> List[Dict[str, Any]]:
    if disabled:
        return []
    news: List[Dict[str, Any]] = []
    bing_error = None
    try:
        news.extend(fetch_bing_news(ticker, name))
    except Exception as exc:
        bing_error = exc
        logger.warning("Bing news failed for %s: %s; trying Google News RSS", ticker, exc)
    try:
        news.extend(fetch_rss_news(ticker, name))
    except Exception as exc:
        if bing_error:
            raise RuntimeError(f"news fetch failed for {ticker}: Bing={bing_error}; Google News RSS={exc}") from exc
        raise RuntimeError(f"news fetch failed for {ticker}: Google News RSS={exc}") from exc
    return dedupe_news(news)


def attach_news(stocks: List[Dict[str, Any]], disabled: bool = False) -> List[Dict[str, Any]]:
    rows = []
    for stock in stocks:
        ticker = stock["ticker"]
        name = stock["name"]
        rows.append({
            **stock,
            "news": fetch_news_for_stock(ticker, name, disabled),
            "news_search_url": news_search_url(ticker, name),
        })
    return rows
