"""
Trade record persistence.
交易记录持久化：本地 JSON 存储，支持记录买卖、查询历史、计算累计净买入（含定投自动推算）。
"""

import json
import os
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TypedDict, Literal


class TradeRecord(TypedDict):
    id: str
    date: str           # YYYY-MM-DD
    code: str
    name: str
    action: Literal["buy", "sell"]
    amount: float
    note: str
    recorded_at: str    # ISO datetime


class AutoInvestConfig(TypedDict):
    code: str
    amount: float       # yuan per trading day


class NetInflowResult(TypedDict):
    since_date: str
    trade_count: int
    total_buy: float
    total_sell: float
    manual_net: float
    auto_invest_total: float
    cumulative_net_inflow: float
    trading_days_counted: int
    by_code: dict


def _data_dir() -> Path:
    base = os.environ.get("AKFUND_DATA_DIR")
    return Path(base) if base else Path.home() / ".akfund"


def _trades_file() -> Path:
    d = _data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "trades.json"


def _load() -> list[TradeRecord]:
    f = _trades_file()
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(trades: list[TradeRecord]) -> None:
    _trades_file().write_text(
        json.dumps(trades, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def record_trade(
    code: str,
    action: Literal["buy", "sell"],
    amount: float,
    date_str: str | None = None,
    name: str = "",
    note: str = "",
) -> TradeRecord:
    """
    Record a manual trade to persistent storage (~/.akfund/trades.json).
    记录一笔手动买卖到本地持久化存储。

    Args:
        code: Fund code / 基金代码
        action: "buy" or "sell" / 买入或卖出
        amount: Trade amount in yuan / 交易金额（元）
        date_str: Trade date YYYY-MM-DD, defaults to today / 交易日期，默认今天
        name: Fund name for readability / 基金名称（可选，便于阅读）
        note: Optional note / 备注（可选）
    """
    today = date_str or datetime.now().strftime("%Y-%m-%d")
    record: TradeRecord = {
        "id": str(uuid.uuid4())[:8],
        "date": today,
        "code": code,
        "name": name,
        "action": action,
        "amount": round(float(amount), 2),
        "note": note,
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
    }
    trades = _load()
    trades.append(record)
    _save(trades)
    return record


def delete_trade(trade_id: str) -> dict:
    """
    Delete a trade record by id (for correcting mistakes).
    按 id 删除误录的交易记录。

    Args:
        trade_id: The id field from a TradeRecord / 交易记录的 id 字段
    """
    trades = _load()
    target = next((t for t in trades if t["id"] == trade_id), None)
    if target is None:
        return {"success": False, "error": f"id '{trade_id}' not found", "deleted_record": None}
    trades = [t for t in trades if t["id"] != trade_id]
    _save(trades)
    return {"success": True, "deleted_record": target}


def get_trade_history(days: int = 90, code: str | None = None) -> list[TradeRecord]:
    """
    Get trade history, newest first.
    获取交易历史，最新在前。

    Args:
        days: How many calendar days back to look (default 90) / 往前查多少天，默认90
        code: Filter by fund code / 按基金代码过滤（可选）
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    trades = _load()
    result = [t for t in trades if t["date"] >= cutoff]
    if code:
        result = [t for t in result if t["code"] == code]
    return sorted(result, key=lambda t: (t["date"], t["recorded_at"]), reverse=True)


def get_today_trades(code: str | None = None) -> list[TradeRecord]:
    """
    Get all trades recorded today, optionally filtered by fund code.
    获取今天已记录的交易，可按基金代码过滤。用于自动判断 already_traded_today。

    Args:
        code: Filter by fund code / 按基金代码过滤（可选）
    """
    today = datetime.now().strftime("%Y-%m-%d")
    trades = _load()
    result = [t for t in trades if t["date"] == today]
    if code:
        result = [t for t in result if t["code"] == code]
    return result


def get_cumulative_net_inflow(
    since_date: str,
    auto_invest: list[AutoInvestConfig] | None = None,
) -> NetInflowResult:
    """
    Compute cumulative net inflow (buys - sells) since a baseline date.
    Optionally adds auto-invest amounts by counting actual trading days.
    计算自基准日起的累计净买入，可叠加定投自动推算。

    Args:
        since_date: Baseline date YYYY-MM-DD (exclusive — only trades strictly after this date count).
                    基准日（不含当天，只统计之后的交易）
        auto_invest: List of auto-invest configs, e.g.
                     [{"code": "270023", "amount": 150}, {"code": "017730", "amount": 100}]
                     每只定投基金的每交易日金额，传入后自动按交易日历推算并叠加。
                     不传则只统计手动记录的买卖。

    Returns:
        NetInflowResult with cumulative_net_inflow = manual_net + auto_invest_total.
    """
    # Manual trades
    trades = _load()
    relevant = [t for t in trades if t["date"] > since_date]

    total_buy = round(sum(t["amount"] for t in relevant if t["action"] == "buy"), 2)
    total_sell = round(sum(t["amount"] for t in relevant if t["action"] == "sell"), 2)
    manual_net = round(total_buy - total_sell, 2)

    by_code: dict[str, dict] = {}
    for t in relevant:
        c = t["code"]
        if c not in by_code:
            by_code[c] = {"buy": 0.0, "sell": 0.0}
        by_code[c][t["action"]] = round(by_code[c][t["action"]] + t["amount"], 2)

    # Auto-invest: count trading days between since_date (exclusive) and today (inclusive)
    auto_invest_total = 0.0
    trading_days_counted = 0

    if auto_invest:
        from .calendar import _get_calendar_for_dates

        start = date.fromisoformat(since_date) + timedelta(days=1)
        end = date.today()

        if start <= end:
            calendar = _get_calendar_for_dates(start, end)
            trading_days = sorted(d for d, is_td in calendar.items() if is_td and start <= d <= end)
            trading_days_counted = len(trading_days)

            for cfg in auto_invest:
                c = cfg["code"]
                per_day = float(cfg["amount"])
                total_for_fund = round(per_day * trading_days_counted, 2)
                auto_invest_total = round(auto_invest_total + total_for_fund, 2)
                if c not in by_code:
                    by_code[c] = {"buy": 0.0, "sell": 0.0}
                by_code[c]["buy"] = round(by_code[c]["buy"] + total_for_fund, 2)

    cumulative_net_inflow = round(manual_net + auto_invest_total, 2)

    return {
        "since_date": since_date,
        "trade_count": len(relevant),
        "total_buy": total_buy,
        "total_sell": total_sell,
        "manual_net": manual_net,
        "auto_invest_total": auto_invest_total,
        "cumulative_net_inflow": cumulative_net_inflow,
        "trading_days_counted": trading_days_counted,
        "by_code": {
            c: {
                "buy": round(v["buy"], 2),
                "sell": round(v["sell"], 2),
                "net": round(v["buy"] - v["sell"], 2),
            }
            for c, v in by_code.items()
        },
    }
