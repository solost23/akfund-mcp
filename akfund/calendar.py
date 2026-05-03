"""
A-share trading calendar: hybrid live + static approach.
A股交易日历：今日状态用实时接口，未来交易日用静态节假日表。
"""

from datetime import date, datetime, timedelta
from typing import TypedDict

from ._http import request_json


class TradingStatus(TypedDict):
    date: str               # queried date / 查询日期
    is_trading_day: bool    # whether market is open / 是否交易日
    is_pre_holiday: bool    # last trading day before a holiday / 是否节前最后交易日
    reason: str             # 交易日 / 周末 / 节假日 / 补班日
    holiday_name: str       # name of upcoming/current holiday / 节假日名称（如有）
    last_trading_day: str   # most recent trading day / 最近交易日
    next_trading_day: str   # next trading day / 下一个交易日
    days_to_next: int       # calendar days until next trading day / 距下一交易日天数


# Static holiday table — used only for next_trading_day and is_pre_holiday lookups
# Update each year when CSRC/SSE publishes the official holiday schedule
_HOLIDAYS: dict[date, str] = {
    # 2026
    date(2026, 1, 1):  "元旦",
    date(2026, 1, 28): "春节", date(2026, 1, 29): "春节", date(2026, 1, 30): "春节",
    date(2026, 1, 31): "春节", date(2026, 2, 2):  "春节", date(2026, 2, 3):  "春节",
    date(2026, 4, 4):  "清明节", date(2026, 4, 5): "清明节", date(2026, 4, 6): "清明节",
    date(2026, 5, 1):  "劳动节", date(2026, 5, 2): "劳动节", date(2026, 5, 3): "劳动节",
    date(2026, 5, 4):  "劳动节", date(2026, 5, 5): "劳动节",
    date(2026, 6, 19): "端午节", date(2026, 6, 20): "端午节", date(2026, 6, 21): "端午节",
    date(2026, 10, 1): "国庆节", date(2026, 10, 2): "国庆节", date(2026, 10, 3): "国庆节",
    date(2026, 10, 4): "国庆节", date(2026, 10, 5): "国庆节", date(2026, 10, 6): "国庆节",
    date(2026, 10, 7): "国庆节", date(2026, 10, 8): "国庆节",
    # 2027
    date(2027, 1, 1):  "元旦",
    date(2027, 1, 15): "春节", date(2027, 1, 16): "春节", date(2027, 1, 17): "春节",
    date(2027, 1, 18): "春节", date(2027, 1, 19): "春节", date(2027, 1, 20): "春节",
    date(2027, 1, 21): "春节",
    date(2027, 4, 5):  "清明节",
    date(2027, 5, 1):  "劳动节", date(2027, 5, 2): "劳动节", date(2027, 5, 3): "劳动节",
    date(2027, 5, 4):  "劳动节", date(2027, 5, 5): "劳动节",
    date(2027, 6, 9):  "端午节", date(2027, 6, 10): "端午节", date(2027, 6, 11): "端午节",
    date(2027, 10, 1): "国庆节", date(2027, 10, 2): "国庆节", date(2027, 10, 3): "国庆节",
    date(2027, 10, 4): "国庆节", date(2027, 10, 5): "国庆节", date(2027, 10, 6): "国庆节",
    date(2027, 10, 7): "国庆节",
}

_MAKEUP_WORKDAYS: set[date] = {
    # 2026
    date(2026, 1, 25), date(2026, 2, 8),   # 春节补班
    date(2026, 4, 26),                      # 劳动节补班
    date(2026, 9, 27), date(2026, 10, 11),  # 国庆节补班
    # 2027
    date(2027, 1, 23),                      # 春节补班
    date(2027, 5, 8),                       # 劳动节补班
    date(2027, 9, 18),                      # 国庆节补班
}


def _fetch_last_trade_date() -> date | None:
    """Fetch the last trading date from Eastmoney SSE index live data."""
    try:
        data = request_json(
            "https://push2.eastmoney.com/api/qt/stock/get"
            "?secid=1.000001&fields=f86&fltt=2&ut=fa5fd1943c7b386f172d6893dbfba10b",
            referer="https://www.eastmoney.com/",
        )
        ts = data.get("data", {}).get("f86")
        if ts:
            return datetime.fromtimestamp(int(ts)).date()
    except Exception:
        pass
    return None


def _is_trading_day_static(d: date) -> bool:
    """Static check using holiday table — used for future dates."""
    if d in _MAKEUP_WORKDAYS:
        return True
    if d.weekday() >= 5:
        return False
    return d not in _HOLIDAYS


def _next_trading_day_static(d: date) -> date:
    nxt = d + timedelta(days=1)
    while not _is_trading_day_static(nxt):
        nxt += timedelta(days=1)
    return nxt


def get_trading_status(date_str: str | None = None) -> TradingStatus:
    """
    Check A-share trading status for a given date (defaults to today).
    查询指定日期（默认今天）的A股交易状态。

    Today's is_trading_day uses live Eastmoney data (accurate, no maintenance needed).
    next_trading_day and is_pre_holiday use a static holiday table.
    今日交易状态通过实时接口判断；下一交易日和节前判断使用静态节假日表。

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today / 日期，默认今天

    Returns:
        TradingStatus with: is_trading_day, is_pre_holiday, reason, last_trading_day,
        next_trading_day, days_to_next.
    """
    d = date.fromisoformat(date_str) if date_str else date.today()
    today = date.today()

    # For today: use live API for accurate is_trading_day
    # For other dates: fall back to static table
    last_trade = None
    if d == today:
        last_trade = _fetch_last_trade_date()

    if last_trade is not None:
        is_td = (last_trade == d)
    else:
        is_td = _is_trading_day_static(d)
        last_trade = d if is_td else _next_trading_day_static(d - timedelta(days=1))

    # Determine reason using static table (live API can't distinguish holiday vs weekend)
    if d in _MAKEUP_WORKDAYS:
        reason = "补班日"
    elif d.weekday() >= 5 and d not in _HOLIDAYS:
        reason = "周末"
    elif d in _HOLIDAYS:
        reason = "节假日"
    elif not is_td and d.weekday() < 5:
        # weekday, not in static table, but live API says not trading → unknown holiday
        reason = "节假日"
    else:
        reason = "交易日" if is_td else "周末"

    # Next trading day and pre-holiday: always use static table
    nxt = _next_trading_day_static(d)
    days_to_next = (nxt - d).days

    is_pre_holiday = False
    holiday_name = _HOLIDAYS.get(d, "")
    if is_td:
        check = d + timedelta(days=1)
        for _ in range(5):
            if check in _HOLIDAYS:
                is_pre_holiday = True
                holiday_name = _HOLIDAYS[check]
                break
            if _is_trading_day_static(check):
                break
            check += timedelta(days=1)

    return {
        "date": d.isoformat(),
        "is_trading_day": is_td,
        "is_pre_holiday": is_pre_holiday,
        "reason": reason,
        "holiday_name": holiday_name,
        "last_trading_day": last_trade.isoformat(),
        "next_trading_day": nxt.isoformat(),
        "days_to_next": days_to_next,
    }
