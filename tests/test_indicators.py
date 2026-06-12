from src.indicators import compute_indicators, sma


def test_sma():
    assert sma([1, 2, 3, 4, 5], 5) == 3
    assert sma([1, 2], 5) is None


def test_compute_ma_values():
    closes = list(range(1, 81))
    volumes = [100] * 79 + [200]
    result = compute_indicators(closes, volumes)
    assert result["ma5"] == 78
    assert result["ma20"] == 70.5
    assert result["ma60"] == 50.5
    assert result["volume_spike"] is True
