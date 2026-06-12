from __future__ import annotations

from typing import Dict, Iterable, List, Optional


def sma(values: Iterable[float], window: int) -> Optional[float]:
    series = [float(v) for v in values if v is not None]
    if len(series) < window:
        return None
    return sum(series[-window:]) / window


def pct_change(values: List[float], periods: int) -> Optional[float]:
    if len(values) <= periods:
        return None
    base = values[-periods - 1]
    if base == 0:
        return None
    return (values[-1] - base) / base * 100


def rsi(values: List[float], period: int = 14) -> Optional[float]:
    if len(values) <= period:
        return None
    gains = []
    losses = []
    for prev, curr in zip(values[-period - 1 : -1], values[-period:]):
        delta = curr - prev
        gains.append(max(delta, 0))
        losses.append(abs(min(delta, 0)))
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = (sum(gains) / period) / avg_loss
    return 100 - (100 / (1 + rs))


def compute_indicators(closes: List[float], volumes: List[float]) -> Dict[str, Optional[float]]:
    current_volume = volumes[-1] if volumes else None
    avg_volume_5 = sma(volumes[:-1], 5) if len(volumes) > 5 else None
    volume_ratio = None
    if current_volume is not None and avg_volume_5:
        volume_ratio = current_volume / avg_volume_5
    return {
        "ma5": sma(closes, 5),
        "ma10": sma(closes, 10),
        "ma20": sma(closes, 20),
        "ma60": sma(closes, 60),
        "change_5d_pct": pct_change(closes, 5),
        "change_20d_pct": pct_change(closes, 20),
        "rsi": rsi(closes),
        "volume_ratio": volume_ratio,
        "volume_spike": bool(volume_ratio and volume_ratio >= 1.5),
    }
