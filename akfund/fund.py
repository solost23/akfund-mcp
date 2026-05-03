"""
Fund data: realtime estimates, NAV history, and technical metrics.
基金数据：盘中实时估值、历史净值、技术指标
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict
from urllib.parse import quote

from ._http import request_fund_json, request_json, request_text


class RealtimeEstimate(TypedDict):
    code: str
    gsz: float        # estimated NAV / 估算净值
    gszzl: float      # estimated change % / 估算涨跌幅
    gztime: str       # estimate timestamp / 估值时间


class NavRecord(TypedDict):
    date: str
    nav: float


class FundMetrics(TypedDict):
    code: str
    latest_date: str
    latest_nav: float
    ret_1w: float
    ret_1m: float
    ret_3m: float
    ret_6m: float
    dd30: float          # max drawdown over last 30 days / 近30日最大回撤
    mean_3m: float       # 3-month average NAV / 近3月均值
    deviation: float     # deviation from 3m mean % / 偏离近3月均值%
    position: str        # 高位 / 中位 / 低位
    streak_dir: str      # 涨 / 跌
    streak_days: int


class FundSearchResult(TypedDict):
    code: str
    name: str
    fund_type: str
    company: str


def search_fund(name: str, limit: int = 10) -> list[FundSearchResult]:
    """
    Search funds by name or keyword using Eastmoney suggest API.
    通过名称或关键词搜索基金，返回匹配的基金代码和基本信息。

    Args:
        name: Fund name or keyword to search / 基金名称或关键词
        limit: Max number of results to return (default 10) / 最多返回条数，默认10

    Returns:
        List of FundSearchResult dicts with code, name, fund_type, company.
        包含 code、name、fund_type、company 的字典列表。
    """
    url = (
        "https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx"
        f"?callback=&m=1&key={quote(name)}"
    )
    try:
        data = request_json(url, referer="https://fund.eastmoney.com/")
        results = []
        for d in data.get("Datas", [])[:limit]:
            base = d.get("FundBaseInfo") or {}
            results.append({
                "code": d.get("CODE", ""),
                "name": d.get("NAME", ""),
                "fund_type": base.get("FTYPE", ""),
                "company": base.get("JJGS", ""),
            })
        return results
    except Exception:
        return []


def get_realtime_estimate(code: str) -> RealtimeEstimate | dict:
    """
    Fetch intraday estimated NAV and change % from Eastmoney.
    从天天基金抓取盘中估算净值和涨跌幅。

    Returns RealtimeEstimate on success, or {"error": str} on failure.
    成功返回 RealtimeEstimate，失败返回 {"error": str}。
    """
    url = f"https://fundgz.1234567.com.cn/js/{code}.js"
    raw = request_text(
        url,
        extra_headers=[
            "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer: https://fund.eastmoney.com/",
        ],
    )
    m = re.search(r"jsonpgz\((\{.*?\})\)", raw)
    if not m:
        return {"error": "no data"}
    try:
        import json
        d = json.loads(m.group(1))
        return {
            "code": code,
            "gsz": float(d.get("gsz", 0)),
            "gszzl": float(d.get("gszzl", 0)),
            "gztime": d.get("gztime", ""),
        }
    except Exception as e:
        return {"error": str(e)}



    """
    Fetch intraday estimated NAV and change % from Eastmoney.
    从天天基金抓取盘中估算净值和涨跌幅。

    Returns RealtimeEstimate on success, or {"error": str} on failure.
    成功返回 RealtimeEstimate，失败返回 {"error": str}。
    """
    url = f"https://fundgz.1234567.com.cn/js/{code}.js"
    raw = request_text(
        url,
        extra_headers=[
            "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer: https://fund.eastmoney.com/",
        ],
    )
    m = re.search(r"jsonpgz\((\{.*?\})\)", raw)
    if not m:
        return {"error": "no data"}
    try:
        import json
        d = json.loads(m.group(1))
        return {
            "code": code,
            "gsz": float(d.get("gsz", 0)),
            "gszzl": float(d.get("gszzl", 0)),
            "gztime": d.get("gztime", ""),
        }
    except Exception as e:
        return {"error": str(e)}


def get_nav_history(code: str, target: int = 180) -> list[NavRecord]:
    """
    Fetch historical NAV records (newest first).
    抓取历史净值（最新在前）。

    Args:
        code: Fund code / 基金代码
        target: Number of trading days to fetch / 抓取交易日数量，默认180
    """
    navs: list[NavRecord] = []
    page = 1
    page_size = 20
    while len(navs) < target:
        url = (
            f"https://api.fund.eastmoney.com/f10/lsjz"
            f"?fundCode={code}&pageIndex={page}&pageSize={page_size}"
        )
        data = request_fund_json(url)
        records = data["Data"]["LSJZList"]
        if not records:
            break
        for r in records:
            try:
                navs.append({"date": r["FSRQ"], "nav": float(r["DWJZ"])})
            except (ValueError, KeyError):
                pass
        if len(records) < page_size:
            break
        page += 1
    return navs[:target]


def get_fund_metrics(code: str, history: list[NavRecord] | None = None) -> FundMetrics | dict:
    """
    Compute technical metrics from NAV history.
    根据历史净值计算技术指标。

    Args:
        code: Fund code / 基金代码
        history: Pre-fetched history (fetched automatically if None) / 预抓取的历史净值，为 None 时自动抓取
    """
    if history is None:
        history = get_nav_history(code)
    if not history:
        return {"error": "no data"}

    navs = history
    latest_date = navs[0]["date"]
    latest_nav = navs[0]["nav"]

    def nav_at(n: int) -> float:
        return navs[n]["nav"] if len(navs) > n else navs[-1]["nav"]

    def pct_change(old: float, new: float) -> float:
        return (new - old) / old * 100

    ret_1w = pct_change(nav_at(5), latest_nav)
    ret_1m = pct_change(nav_at(22), latest_nav)
    ret_3m = pct_change(nav_at(66), latest_nav)
    ret_6m = pct_change(nav_at(132), latest_nav)

    last30 = [r["nav"] for r in navs[:30]][::-1]
    dd30 = _max_drawdown(last30)

    last66 = [r["nav"] for r in navs[:66]]
    mean_3m = sum(last66) / len(last66)
    deviation = (latest_nav - mean_3m) / mean_3m * 100
    position = "高位" if deviation > 5 else ("低位" if deviation < -5 else "中位")

    streak_dir, streak_days = _consecutive_streak(navs)

    return {
        "code": code,
        "latest_date": latest_date,
        "latest_nav": latest_nav,
        "ret_1w": ret_1w,
        "ret_1m": ret_1m,
        "ret_3m": ret_3m,
        "ret_6m": ret_6m,
        "dd30": dd30,
        "mean_3m": mean_3m,
        "deviation": deviation,
        "position": position,
        "streak_dir": streak_dir,
        "streak_days": streak_days,
    }


def _max_drawdown(navs: list[float]) -> float:
    """navs: oldest-first. Returns max drawdown % (negative). / 最大回撤%（负数）"""
    peak = navs[0]
    max_dd = 0.0
    for v in navs:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd
    return max_dd


def _consecutive_streak(navs: list[NavRecord]) -> tuple[str, int]:
    """Returns (direction, days). / 返回（方向, 天数）"""
    if len(navs) < 2:
        return ("N/A", 0)
    direction = None
    count = 0
    for i in range(len(navs) - 1):
        diff = navs[i]["nav"] - navs[i + 1]["nav"]
        d = "涨" if diff > 0 else ("跌" if diff < 0 else "平")
        if direction is None:
            direction = d
        if d == direction and d != "平":
            count += 1
        else:
            break
    return (direction or "N/A", count)


def get_multi_fund_metrics(codes: list[str], days: int = 180) -> dict[str, FundMetrics | dict]:
    """
    Fetch technical metrics for multiple funds concurrently.
    并发抓取多只基金的技术指标。

    Args:
        codes: List of fund codes / 基金代码列表
        days: Number of trading days of history to use (default 180) / 历史净值天数，默认180

    Returns:
        Dict keyed by fund code. Each value is FundMetrics or {"error": str}.
        以基金代码为 key 的字典，值为 FundMetrics 或 {"error": str}。
    """
    def _fetch(code: str) -> tuple[str, FundMetrics | dict]:
        try:
            history = get_nav_history(code, target=days)
            return code, get_fund_metrics(code, history=history)
        except Exception as e:
            return code, {"error": str(e)}

    results: dict[str, FundMetrics | dict] = {}
    with ThreadPoolExecutor(max_workers=min(len(codes), 10)) as executor:
        futures = {executor.submit(_fetch, code): code for code in codes}
        for future in as_completed(futures):
            code, result = future.result()
            results[code] = result
    return results


def get_multi_realtime_estimates(codes: list[str]) -> dict[str, RealtimeEstimate | dict]:
    """
    Fetch intraday estimates for multiple funds concurrently.
    并发抓取多只基金的盘中估值。

    Args:
        codes: List of fund codes / 基金代码列表

    Returns:
        Dict keyed by fund code. Each value is RealtimeEstimate or {"error": str}.
        以基金代码为 key 的字典，值为 RealtimeEstimate 或 {"error": str}。
    """
    def _fetch(code: str) -> tuple[str, RealtimeEstimate | dict]:
        return code, get_realtime_estimate(code)

    results: dict[str, RealtimeEstimate | dict] = {}
    with ThreadPoolExecutor(max_workers=min(len(codes), 10)) as executor:
        futures = {executor.submit(_fetch, code): code for code in codes}
        for future in as_completed(futures):
            code, result = future.result()
            results[code] = result
    return results
