from __future__ import annotations

import base64
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
PUBLIC_SIGNAL_REMOVE_MARKERS = ("stop_loss", "take_profit", "cost", "position")


def public_stock_slug(ticker: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", ticker.strip().upper()).strip("-")
    if not slug:
        raise ValueError("ticker is required for public stock share page")
    return slug


def sanitize_public_stock(stock: Dict[str, Any]) -> Dict[str, Any]:
    public = copy.deepcopy(stock)
    for field in PUBLIC_STOCK_REMOVE_FIELDS:
        public.pop(field, None)
    for field in ("signals", "risk_signals", "opportunity_signals"):
        public[field] = [
            signal for signal in public.get(field, [])
            if not any(marker in str(signal) for marker in PUBLIC_SIGNAL_REMOVE_MARKERS)
        ]
    commentary = public.get("ai_commentary")
    if commentary and any(marker in str(commentary) for marker in PUBLIC_SIGNAL_REMOVE_MARKERS):
        public["ai_commentary"] = public.get("suggested_action") or ""
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


def make_private_landing_html(base_url: str = "", include_private_link: bool = False) -> str:
    message = "完整组合报告是私人内容。请使用单只股票分享链接打开公开页面。"
    share_link = f'<p><a href="{base_url.rstrip("/")}/share/">打开分享目录</a></p>' if base_url else ""
    private_link = (
        f'<p><a href="{base_url.rstrip("/")}/private/latest_report.html">打开加密完整报告</a></p>'
        if base_url and include_private_link
        else ""
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>FinAnalysis Private</title>"
        "<style>body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC',Arial,sans-serif;"
        "background:#f6f7f9;color:#111827;display:grid;place-items:center;min-height:100vh}"
        "main{max-width:680px;padding:32px}h1{font-size:28px;margin:0 0 12px}p{color:#5b6472;line-height:1.7}"
        "a{color:#111827;font-weight:700}</style><main><h1>FinAnalysis</h1>"
        f"<p>{message}</p>{private_link}{share_link}</main></html>"
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


def make_manifest_json() -> str:
    import json

    return json.dumps({
        "name": "FinAnalysis Daily Agent",
        "short_name": "FinAnalysis",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f5f4ed",
        "theme_color": "#1B365D",
        "description": "Personal daily investment research agent reports.",
        "icons": [
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 128 128'%3E%3Crect width='128' height='128' rx='24' fill='%231B365D'/%3E%3Ctext x='64' y='78' text-anchor='middle' font-size='42' font-family='Arial' fill='%23fffdf6'%3EFA%3C/text%3E%3C/svg%3E",
                "sizes": "128x128",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            }
        ],
    }, ensure_ascii=False, indent=2)


def make_service_worker_js(share_pages: Dict[str, str], has_private_report: bool) -> str:
    urls = ["./", "./latest_report.html", "./share/"]
    urls.extend("./" + path for path in sorted(share_pages.values()))
    if has_private_report:
        urls.append("./private/latest_report.html")
    import json

    return (
        "const CACHE='finanalysis-v1';\n"
        f"const URLS={json.dumps(urls, ensure_ascii=False)};\n"
        "self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(URLS)).catch(()=>undefined));self.skipWaiting();});\n"
        "self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))));self.clients.claim();});\n"
        "self.addEventListener('fetch',event=>{if(event.request.method!=='GET')return;event.respondWith(fetch(event.request).then(response=>{const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));return response;}).catch(()=>caches.match(event.request).then(cached=>cached||caches.match('./'))));});\n"
    )


def write_json_text(payload: Dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def make_encrypted_report_html(html: str, password: str) -> str:
    if not password:
        raise ValueError("PRIVATE_REPORT_PASSWORD is required to encrypt the private report")

    from cryptography.hazmat.primitives import hashes  # type: ignore
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore

    salt = os.urandom(16)
    nonce = os.urandom(12)
    iterations = 200_000
    aad = b"FinAnalysis private report v1"
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    key = kdf.derive(password.encode("utf-8"))
    ciphertext = AESGCM(key).encrypt(nonce, html.encode("utf-8"), aad)
    payload = {
        "v": 1,
        "kdf": "PBKDF2",
        "hash": "SHA-256",
        "cipher": "AES-GCM",
        "iterations": iterations,
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "aad": base64.b64encode(aad).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>FinAnalysis Private Report</title>"
        "<style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;"
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC',Arial,sans-serif;background:#f6f7f9;color:#111827}"
        "main{width:min(520px,calc(100vw - 32px));background:white;border:1px solid #d8dde6;border-radius:8px;padding:22px}"
        "h1{font-size:24px;margin:0 0 8px}p{color:#5b6472;line-height:1.65}label{display:block;font-weight:800;margin:16px 0 8px}"
        "input{width:100%;height:44px;border:1px solid #cbd5e1;border-radius:7px;padding:0 12px;font:inherit}"
        "button{width:100%;height:44px;margin-top:12px;border:0;border-radius:7px;background:#111827;color:white;font-weight:850;font:inherit}"
        "#msg{min-height:22px;color:#b91c1c}</style></head><body><main>"
        "<h1>FinAnalysis 加密完整报告</h1>"
        "<p>请输入你的私人密码。解密只在当前浏览器本地完成，页面不会上传密码。</p>"
        "<form id=\"form\"><label for=\"pw\">密码</label><input id=\"pw\" type=\"password\" autocomplete=\"current-password\" autofocus>"
        "<button type=\"submit\">打开完整报告</button></form><p id=\"msg\"></p></main>"
        f"<script id=\"encrypted-report\" type=\"application/json\">{write_json_text(payload)}</script>"
        "<script>"
        "const enc=new TextEncoder(),dec=new TextDecoder();"
        "function b64(s){return Uint8Array.from(atob(s),c=>c.charCodeAt(0))}"
        "form.onsubmit=async e=>{e.preventDefault();msg.textContent='正在解密...';try{"
        "const p=JSON.parse(document.getElementById('encrypted-report').textContent),pass=document.getElementById('pw').value;"
        "const km=await crypto.subtle.importKey('raw',enc.encode(pass),'PBKDF2',false,['deriveKey']);"
        "const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:b64(p.salt),iterations:p.iterations,hash:p.hash},km,{name:'AES-GCM',length:256},false,['decrypt']);"
        "const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64(p.nonce),additionalData:b64(p.aad)},key,b64(p.ciphertext));"
        "document.open();document.write(dec.decode(plain));document.close();"
        "}catch(err){msg.textContent='密码不正确，或报告已损坏。';}};"
        "</script></body></html>"
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
    docs_private = docs_root / "private"
    private_password = os.getenv("PRIVATE_REPORT_PASSWORD", "").strip()
    base_url = os.getenv("REPORT_BASE_URL") or os.getenv("GITHUB_PAGES_URL") or config.get("report_base_url") or ""

    if docs_reports.exists() and not public_site.get("publish_full_report", False):
        shutil.rmtree(docs_reports)
    if docs_share.exists():
        shutil.rmtree(docs_share)
    if docs_private.exists():
        shutil.rmtree(docs_private)
    docs_share.mkdir(parents=True, exist_ok=True)
    docs_private.mkdir(parents=True, exist_ok=True)

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
        landing = make_private_landing_html(base_url, include_private_link=bool(private_password))
        docs_latest.write_text(landing, encoding="utf-8")
        docs_index.write_text(landing, encoding="utf-8")
    if share_pages and public_site.get("show_share_index", False):
        (docs_share / "index.html").write_text(make_share_index_html(share_pages), encoding="utf-8")
    else:
        (docs_share / "index.html").write_text(make_private_landing_html(), encoding="utf-8")

    if private_password:
        encrypted_html = make_encrypted_report_html(html, private_password)
        (docs_private / "latest_report.html").write_text(encrypted_html, encoding="utf-8")
        (docs_private / "index.html").write_text(encrypted_html, encoding="utf-8")
    else:
        (docs_private / "index.html").write_text(make_private_landing_html(), encoding="utf-8")

    share_links = ROOT / "output" / "share_links.md"
    rows = ["# 单股分享链接", ""]
    for ticker, path in sorted(share_pages.items()):
        url = f"{base_url.rstrip('/')}/{path}" if base_url else str(docs_root / path)
        rows.append(f"- {ticker}: {url}")
    share_links.write_text("\n".join(rows) + "\n", encoding="utf-8")
    (docs_root / "manifest.webmanifest").write_text(make_manifest_json(), encoding="utf-8")
    (docs_root / "sw.js").write_text(make_service_worker_js(share_pages, bool(private_password)), encoding="utf-8")
    return {"html": latest_html, "json": latest_json, "summary": latest_md, "archive_html": report_html}
