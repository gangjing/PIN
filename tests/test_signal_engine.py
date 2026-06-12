from src.signal_engine import generate_signals


def test_stop_loss_signal():
    stock = {"price": 95, "stop_loss": 100, "type": "holding", "indicators": {}}
    result = generate_signals(stock)
    assert "below_stop_loss" in result["risk_signals"]
    assert result["computed_risk_level"] == "high"


def test_take_profit_signal():
    stock = {"price": 103, "take_profit": 105, "type": "holding", "indicators": {}}
    result = generate_signals(stock)
    assert "near_take_profit" in result["opportunity_signals"]


def test_below_ma20_signal():
    stock = {"price": 90, "type": "holding", "indicators": {"ma20": 100}}
    result = generate_signals(stock)
    assert "below_ma20" in result["risk_signals"]
