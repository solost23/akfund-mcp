"""
Fund peer comparison: rank, peer average return, quartile rating.
同类基金对比：同类排名、同类平均涨幅、四分位评级。
数据来源：天天基金 FundArchivesDatas.aspx?type=jdzf
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict

from ._http import request_text

_HEADERS = [
    "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer: https://fundf10.eastmoney.com/",
]


class PeriodRank(TypedDict):
    period: str             # 近1月 / 近3月 / 近6月 / 近1年 等
    fund_return: str        # 基金涨跌幅，如 "26.35%" 或 "---"
    peer_avg: str           # 同类平均涨跌幅
    hs300: str              # 沪深300涨跌幅
    rank: int | None        # 同类排名（越小越好）
    total: int | None       # 同类基金总数
    percentile: float | None  # 百分位（越低越好），rank/total*100，保留1位小数
    rank_change: str        # 排名变动，如 "+173" 或 "---"
    quartile: str           # 四分位：优秀 / 良好 / 一般 / 不佳 / ---
    vs_peer: float | None   # 基金涨幅 - 同类平均，正数表示跑赢


class FundRank(TypedDict):
    code: str
    periods: list[PeriodRank]


def _parse_pct(s: str) -> float | None:
    """Parse '26.35%' or '-3.21%' to float, return None for '---'."""
    s = s.strip().rstrip("%")
    if s in ("---", "", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def get_fund_rank(code: str) -> FundRank | dict:
    """
    Fetch peer comparison data for a fund: rank, peer average return, quartile.
    获取基金同类对比数据：同类排名、同类平均涨幅、四分位评级。

    Args:
        code: Fund code / 基金代码

    Returns:
        FundRank with a list of PeriodRank for each available period.
        包含各周期同类排名、同类平均涨幅、四分位评级的结果。
        Key field for decision rules: periods[period=="近3月"].vs_peer
        (negative and < -5 triggers heavy-operation review per framework rules)
    """
    url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jdzf&code={code}"
    try:
        raw = request_text(url, extra_headers=_HEADERS)
        if not raw or len(raw) < 200:
            return {"code": code, "error": "empty response"}

        # Each period is wrapped in <ul>...</ul>
        blocks = re.findall(r"<ul[^>]*>(.*?)</ul>", raw, re.DOTALL)
        periods: list[PeriodRank] = []

        for block in blocks:
            items = re.findall(r"<li[^>]*>(.*?)</li>", block, re.DOTALL)
            if len(items) < 6:
                continue

            def _text(s: str) -> str:
                return re.sub(r"<[^>]+>", "", s).strip()

            period_name = _text(items[0])
            # Skip header row (no period name) and rows without recognizable period
            if not period_name or period_name in ("涨幅", "同类平均", "沪深300", "同类排名", "排名变动", "四分位排名"):
                continue

            fund_ret_str = _text(items[1])
            peer_avg_str = _text(items[2])
            hs300_str = _text(items[3])

            # Rank: "420|4796" or "---"
            rank_raw = _text(items[4])
            rank_m = re.search(r"(\d+)\s*\|\s*(\d+)", rank_raw)
            rank_val = int(rank_m.group(1)) if rank_m else None
            total_val = int(rank_m.group(2)) if rank_m else None
            percentile = round(rank_val / total_val * 100, 1) if (rank_val and total_val) else None

            # Rank change: "611↑" or "---"
            change_raw = _text(items[5])
            change_m = re.search(r"(\d+)\s*([↑↓])", change_raw)
            if change_m:
                sign = "+" if change_m.group(2) == "↑" else "-"
                rank_change = f"{sign}{change_m.group(1)}"
            else:
                rank_change = "---"

            # Quartile from <p class='sifen'>
            quartile_m = re.search(r"class=['\"]sifen['\"]>(.*?)</p>", block, re.DOTALL)
            quartile = _text(quartile_m.group(1)) if quartile_m else "---"

            fund_ret = _parse_pct(fund_ret_str)
            peer_avg = _parse_pct(peer_avg_str)
            vs_peer = round(fund_ret - peer_avg, 2) if (fund_ret is not None and peer_avg is not None) else None

            periods.append({
                "period": period_name,
                "fund_return": fund_ret_str if fund_ret_str else "---",
                "peer_avg": peer_avg_str if peer_avg_str else "---",
                "hs300": hs300_str if hs300_str else "---",
                "rank": rank_val,
                "total": total_val,
                "percentile": percentile,
                "rank_change": rank_change,
                "quartile": quartile,
                "vs_peer": vs_peer,
            })

        return {"code": code, "periods": periods}

    except Exception as e:
        return {"code": code, "error": str(e)}


def get_multi_fund_rank(codes: list[str]) -> dict[str, FundRank | dict]:
    """
    Fetch peer comparison data for multiple funds concurrently.
    并发抓取多只基金的同类对比数据。

    Args:
        codes: List of fund codes / 基金代码列表
    """
    results: dict[str, FundRank | dict] = {}
    with ThreadPoolExecutor(max_workers=min(len(codes), 10)) as executor:
        futures = {executor.submit(get_fund_rank, code): code for code in codes}
        for future in as_completed(futures):
            code = futures[future]
            try:
                results[code] = future.result()
            except Exception as e:
                results[code] = {"code": code, "error": str(e)}
    return results
