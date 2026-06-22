from src.html_report import render_html
from src.report_generator import make_encrypted_report_html, make_public_stock_report, make_service_worker_js, make_summary


def sample_report():
    return {
        "run_time": "2026-06-11T14:00:00+08:00",
        "mode": "pre_close",
        "overall_status": "cautious",
        "market_summary": {},
        "priority_actions": [{"ticker": "TTD", "name": "Trade Desk", "reason": "接近止损", "action": "人工确认", "urgency": "high"}],
        "stocks": [{"market": "US", "ticker": "TTD", "name": "Trade Desk", "type": "holding", "price": 70, "change_pct": -2, "cost": 75, "position_pct": 20, "computed_risk_level": "high", "signals": ["near_stop_loss"], "suggested_action": "人工确认", "indicators": {}, "news": []}],
        "summary_for_push": "hello",
        "run_status": {"status": "success", "google_sheet": "success", "market_data": "success", "news": "empty", "ai": "skipped"},
        "daily_diff": {"has_previous": False},
        "warnings": [],
    }


def multi_stock_report():
    report = sample_report()
    report["stocks"].append({
        "market": "HK",
        "ticker": "1810.HK",
        "name": "Xiaomi",
        "type": "holding",
        "price": 25,
        "change_pct": 1.2,
        "cost": 20,
        "quantity": 1000,
        "position_pct": 30,
        "take_profit": 35,
        "stop_loss": 18,
        "notes": "private note",
        "computed_risk_level": "low",
        "signals": ["above_take_profit", "public_momentum"],
        "suggested_action": "观察",
        "ai_commentary": "依据：above_take_profit",
        "indicators": {},
        "news": [{"title": "Xiaomi news", "url": "https://example.com", "source": "Test", "sentiment": "neutral"}],
    })
    return report


def test_summary_contains_disclaimer():
    text = make_summary(sample_report(), "output/latest_report.html")
    assert "免责声明" in text
    assert "TTD" in text


def test_html_single_file_contains_data():
    html = render_html(sample_report())
    assert "<!doctype html>" in html
    assert "report-data" in html
    assert "Trade Desk" in html


def test_html_contains_language_theme_and_offline_ui():
    html = render_html(sample_report())
    assert 'data-theme="light"' in html
    assert 'id="langZh"' in html
    assert 'id="langEn"' in html
    assert 'id="themeToggle"' in html
    assert "个股深度分析" in html
    assert "Asset Deep Dive" in html
    assert "Smart News Feed" in html
    assert "https://cdn" not in html
    assert 'rel="manifest"' in html
    assert "serviceWorker" in html
    assert "运行状态" in html
    assert "昨日对比" in html
    assert "og:title" in html


def test_public_stock_report_contains_only_selected_stock_and_hides_personal_fields():
    report = make_public_stock_report(multi_stock_report(), "1810.HK")
    html = render_html(report)
    stock = report["stocks"][0]

    assert report["share_mode"] is True
    assert report["share_ticker"] == "1810.HK"
    assert report["run_status"]["status"] == "success"
    assert report["run_status"]["google_sheet"] == "success"
    assert report["run_status"]["market_data"] == "success"
    assert report["run_status"]["news"] == "success"
    assert report["run_status"]["asset_count"] == 1
    assert report["run_status"]["news_count"] == 1
    assert len(report["stocks"]) == 1
    assert stock["ticker"] == "1810.HK"
    assert "TTD" not in html
    assert "quantity" not in stock
    assert "cost" not in stock
    assert "position_pct" not in stock
    assert "take_profit" not in stock
    assert "stop_loss" not in stock
    assert "above_take_profit" not in html
    assert "public_momentum" in html
    assert "private note" not in html


def test_service_worker_caches_share_pages_and_private_report():
    js = make_service_worker_js({"1810.HK": "share/1810.HK.html"}, True)
    assert "./share/1810.HK.html" in js
    assert "./private/latest_report.html" in js
    assert "caches.open" in js


def test_encrypted_report_hides_plain_html_and_can_be_decrypted():
    from base64 import b64decode
    import json
    import re

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    plain = render_html(sample_report())
    encrypted = make_encrypted_report_html(plain, "test-password")
    payload_text = re.search(r'<script id="encrypted-report" type="application/json">(.*?)</script>', encrypted).group(1)
    payload = json.loads(payload_text)

    assert "Trade Desk" not in encrypted
    assert "report-data" not in encrypted
    assert "encrypted-report" in encrypted

    salt = b64decode(payload["salt"])
    nonce = b64decode(payload["nonce"])
    aad = b64decode(payload["aad"])
    ciphertext = b64decode(payload["ciphertext"])
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=payload["iterations"])
    key = kdf.derive(b"test-password")
    decrypted = AESGCM(key).decrypt(nonce, ciphertext, aad).decode("utf-8")
    assert "Trade Desk" in decrypted
    assert "report-data" in decrypted
