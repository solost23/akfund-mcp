"""
A-share trading calendar: fully live via SZSE official calendar API.
A股交易日历：通过深交所官方接口实时查询，无需维护静态节假日表。
"""

from datetime import date, datetime, timedelta
from typing import TypedDict

from ._http import request_json, request_text


class TradingStatus(TypedDict):
    date: str               # queried date / 查询日期
    is_trading_day: bool    # whether market is open / 是否交易日
    is_pre_holiday: bool    # last trading day before a holiday / 是否节前最后交易日
    reason: str             # 交易日 / 周末 / 节假日 / 补班日
    holiday_name: str       # always "" — SZSE API doesn't provide holiday names
    last_trading_day: str   # most recent trading day / 最近交易日
    next_trading_day: str   # next trading day / 下一个交易日
    days_to_next: int       # calendar days until next trading day / 距下一交易日天数


def _fetch_month_calendar(year: int, month: int) -> dict[date, bool]:
    """
    Fetch trading day flags for a given month from SZSE.
    Returns {date: is_trading_day}.
    """
    import subprocess, json as _json
    month_str = f"{year}-{month:02d}"
    url = f"https://www.szse.cn/api/report/exchange/onepersistenthour/monthList?month={month_str}&random=0.1"
    try:
        raw = request_text(url, extra_headers=[
            "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer: https://www.szse.cn/",
        ])
        data = _json.loads(raw)
        result = {}
        for item in data.get("data", []):
            d = date.fromisoformat(item["jyrq"])
            result[d] = item["jybz"] == "1"
        return result
    except Exception:
        return {}


def _get_calendar_for_dates(start: date, end: date) -> dict[date, bool]:
    """Fetch calendar covering start..end, spanning multiple months if needed."""
    calendar: dict[date, bool] = {}
    cur = date(start.year, start.month, 1)
    while cur <= end:
        calendar.update(_fetch_month_calendar(cur.year, cur.month))
        # advance to next month
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    return calendar


def get_trading_status(date_str: str | None = None) -> TradingStatus:
    """
    Check A-share trading status for a given date (defaults to today).
    查询指定日期（默认今天）的A股交易状态。

    Uses SZSE official trading calendar API — no static holiday table needed,
    works across all years automatically.
    通过深交所官方交易日历接口查询，无需维护节假日表，永久有效。

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today / 日期，默认今天

    Returns:
        TradingStatus with: is_trading_day, is_pre_holiday, reason,
        last_trading_day, next_trading_day, days_to_next.
    """
    d = date.fromisoformat(date_str) if date_str else date.today()

    # Fetch calendar for d's month + next month (for next_trading_day lookup)
    end = d + timedelta(days=14)
    calendar = _get_calendar_for_dates(d, end)

    # Also fetch previous month if d is near the start of the month
    if d.day <= 5:
        prev = date(d.year, d.month, 1) - timedelta(days=1)
        calendar.update(_fetch_month_calendar(prev.year, prev.month))

    is_td = calendar.get(d, False)

    # Determine reason
    if d.weekday() >= 5:
        reason = "周末" if not is_td else "补班日"
    else:
        reason = "交易日" if is_td else "节假日"

    # Find last trading day (on or before d)
    last_td = d
    for i in range(1, 15):
        candidate = d - timedelta(days=i)
        if candidate not in calendar:
            # fetch that month if needed
            calendar.update(_fetch_month_calendar(candidate.year, candidate.month))
        if calendar.get(candidate, False):
            last_td = candidate
            break
    if is_td:
        last_td = d

    # Find next trading day (after d)
    nxt = d + timedelta(days=1)
    for _ in range(14):
        if nxt not in calendar:
            calendar.update(_fetch_month_calendar(nxt.year, nxt.month))
        if calendar.get(nxt, False):
            break
        nxt += timedelta(days=1)

    days_to_next = (nxt - d).days

    # Pre-holiday: today is a trading day and next trading day is 3+ days away
    is_pre_holiday = is_td and days_to_next >= 3

    return {
        "date": d.isoformat(),
        "is_trading_day": is_td,
        "is_pre_holiday": is_pre_holiday,
        "reason": reason,
        "holiday_name": "",
        "last_trading_day": last_td.isoformat(),
        "next_trading_day": nxt.isoformat(),
        "days_to_next": days_to_next,
    }
