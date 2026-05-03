"""
A-share trading calendar: holiday check, trading day status.
A股交易日历：节假日判断、交易状态查询。
"""

from datetime import date, timedelta
from typing import TypedDict


class TradingStatus(TypedDict):
    date: str               # queried date / 查询日期
    is_trading_day: bool    # whether market is open / 是否交易日
    is_pre_holiday: bool    # last trading day before a holiday / 是否节前最后交易日
    reason: str             # 交易日 / 周末 / 节假日 / 补班日
    holiday_name: str       # name of upcoming/current holiday / 节假日名称（如有）
    next_trading_day: str   # next trading day / 下一个交易日
    days_to_next: int       # calendar days until next trading day / 距下一交易日天数


# 2026 A-share market holidays
# Source: official CSRC/SSE announcements for 2026
_HOLIDAYS: dict[date, str] = {
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
}

# Makeup workdays: weekends that are trading days due to holiday adjustments
_MAKEUP_WORKDAYS: set[date] = {
    date(2026, 1, 25),   # 春节补班
    date(2026, 2, 8),    # 春节补班
    date(2026, 4, 26),   # 劳动节补班
    date(2026, 9, 27),   # 国庆节补班
    date(2026, 10, 11),  # 国庆节补班
}


def _is_trading_day(d: date) -> bool:
    if d in _MAKEUP_WORKDAYS:
        return True
    if d.weekday() >= 5:
        return False
    return d not in _HOLIDAYS


def _next_trading_day(d: date) -> date:
    nxt = d + timedelta(days=1)
    while not _is_trading_day(nxt):
        nxt += timedelta(days=1)
    return nxt


def get_trading_status(date_str: str | None = None) -> TradingStatus:
    """
    Check trading status for a given date (defaults to today).
    查询指定日期（默认今天）的A股交易状态。

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today / 日期字符串，默认今天

    Returns:
        TradingStatus with trading day flag, pre-holiday flag, and next trading day.
    """
    if date_str:
        d = date.fromisoformat(date_str)
    else:
        d = date.today()

    is_td = _is_trading_day(d)
    nxt = _next_trading_day(d)
    days_to_next = (nxt - d).days

    # Determine reason
    if d in _MAKEUP_WORKDAYS:
        reason = "补班日"
    elif d.weekday() >= 5 and d not in _HOLIDAYS:
        reason = "周末"
    elif d in _HOLIDAYS:
        reason = "节假日"
    else:
        reason = "交易日"

    # Pre-holiday: today is a trading day and tomorrow (or next few days) starts a holiday
    is_pre_holiday = False
    holiday_name = _HOLIDAYS.get(d, "")
    if is_td:
        # check if next calendar day is a holiday
        check = d + timedelta(days=1)
        for _ in range(4):  # look ahead up to 4 days
            if check in _HOLIDAYS:
                is_pre_holiday = True
                holiday_name = _HOLIDAYS[check]
                break
            if _is_trading_day(check):
                break
            check += timedelta(days=1)

    return {
        "date": d.isoformat(),
        "is_trading_day": is_td,
        "is_pre_holiday": is_pre_holiday,
        "reason": reason,
        "holiday_name": holiday_name,
        "next_trading_day": nxt.isoformat(),
        "days_to_next": days_to_next,
    }
