from src.html_report import render_html
from src.report_generator import make_summary


def sample_report():
    return {
        "run_time": "2026-06-11T14:00:00+08:00",
        "mode": "pre_close",
        "overall_status": "cautious",
        "market_summary": {},
        "priority_actions": [{"ticker": "TTD", "name": "Trade Desk", "reason": "接近止损", "action": "人工确认", "urgency": "high"}],
        "stocks": [{"market": "US", "ticker": "TTD", "name": "Trade Desk", "type": "holding", "price": 70, "change_pct": -2, "cost": 75, "position_pct": 20, "computed_risk_level": "high", "signals": ["near_stop_loss"], "suggested_action": "人工确认", "indicators": {}, "news": []}],
        "summary_for_push": "hello",
        "warnings": [],
    }


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
