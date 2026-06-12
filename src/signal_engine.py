from __future__ import annotations

from typing import Any, Dict, List


RISK_SIGNAL_LABELS = {
    "below_stop_loss": "跌破止损",
    "near_stop_loss": "接近止损",
    "below_ma20": "跌破 MA20",
    "below_ma60": "跌破 MA60",
    "daily_drop_gt_5": "单日跌幅超过 5%",
    "volume_down": "放量下跌",
    "negative_news": "重大负面新闻",
}

OPPORTUNITY_SIGNAL_LABELS = {
    "above_take_profit": "达到止盈观察区",
    "near_take_profit": "接近止盈",
    "break_ma20": "突破 MA20",
    "break_ma60": "突破 MA60",
    "volume_up": "放量上涨",
    "near_recent_high": "接近近期高点",
    "positive_news": "重大正面新闻",
}


def distance_pct(price: float, target: float) -> float:
    return abs(price - target) / target * 100 if target else 999


def generate_signals(stock: Dict[str, Any]) -> Dict[str, Any]:
    price = stock.get("price")
    change = stock.get("change_pct")
    indicators = stock.get("indicators") or {}
    risk: List[str] = []
    opportunity: List[str] = []
    observe: List[str] = []
    if price is None:
        return {"risk_signals": ["data_missing"], "opportunity_signals": [], "observe_signals": [], "suggested_action": "数据不足，先人工核对", "computed_risk_level": "high"}

    stop_loss = stock.get("stop_loss")
    take_profit = stock.get("take_profit")
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    volume_spike = bool(indicators.get("volume_spike"))

    if stop_loss:
        if price < stop_loss:
            risk.append("below_stop_loss")
        elif distance_pct(price, stop_loss) < 3:
            risk.append("near_stop_loss")
    if take_profit:
        if price >= take_profit:
            opportunity.append("above_take_profit")
        elif distance_pct(price, take_profit) < 3:
            opportunity.append("near_take_profit")
    if ma20:
        if price < ma20:
            risk.append("below_ma20")
        else:
            observe.append("above_ma20")
            if change is not None and change > 0:
                opportunity.append("break_ma20")
    if ma60:
        if price < ma60:
            risk.append("below_ma60")
        elif change is not None and change > 0:
            opportunity.append("break_ma60")
    if change is not None and change <= -5:
        risk.append("daily_drop_gt_5")
    if volume_spike and change is not None:
        if change < 0:
            risk.append("volume_down")
        elif change > 0:
            opportunity.append("volume_up")
    high = stock.get("high_52w")
    if high and price >= high * 0.97:
        opportunity.append("near_recent_high")

    news = stock.get("news") or []
    if any(n.get("sentiment") == "negative" and n.get("importance") in {"high", "medium"} for n in news):
        risk.append("negative_news")
    if any(n.get("sentiment") == "positive" and n.get("importance") == "high" for n in news):
        opportunity.append("positive_news")

    computed_risk = "high" if any(s in risk for s in ["below_stop_loss", "near_stop_loss", "volume_down", "negative_news"]) else "medium" if risk else stock.get("risk_level", "low")
    action = suggest_action(risk, opportunity, stock.get("type", "watchlist"))
    return {
        "risk_signals": sorted(set(risk)),
        "opportunity_signals": sorted(set(opportunity)),
        "observe_signals": sorted(set(observe)),
        "signals": sorted(set(risk + opportunity + observe)),
        "computed_risk_level": computed_risk,
        "suggested_action": action,
    }


def suggest_action(risk: List[str], opportunity: List[str], stock_type: str) -> str:
    if "below_stop_loss" in risk:
        return "跌破止损，需人工确认是否止损"
    if "near_stop_loss" in risk or "volume_down" in risk:
        return "风险升高，优先人工确认"
    if "negative_news" in risk:
        return "先核实负面信息，再决定是否调整"
    if "above_take_profit" in opportunity or "near_take_profit" in opportunity:
        return "接近止盈区，考虑分批确认收益"
    if "volume_up" in opportunity or "break_ma20" in opportunity:
        return "可加入重点观察，不建议追高"
    if stock_type == "holding":
        return "继续持有观察"
    return "继续观察，等待更明确入场信号"


def apply_signals(stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{**stock, **generate_signals(stock)} for stock in stocks]


def build_priority_actions(stocks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    priority = []
    for stock in stocks:
        risk = stock.get("risk_signals") or []
        opp = stock.get("opportunity_signals") or []
        if risk or opp:
            reason = "、".join([RISK_SIGNAL_LABELS.get(s, s) for s in risk[:3]] + [OPPORTUNITY_SIGNAL_LABELS.get(s, s) for s in opp[:2]])
            urgency = "high" if risk and stock.get("computed_risk_level") == "high" else "medium"
            priority.append({
                "ticker": stock["ticker"],
                "name": stock["name"],
                "reason": reason or "出现观察信号",
                "action": stock.get("suggested_action", "人工确认"),
                "urgency": urgency,
            })
    return sorted(priority, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["urgency"], 3))[:5]
