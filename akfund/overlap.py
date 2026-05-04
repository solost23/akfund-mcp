"""
Portfolio overlap analysis: penetrate fund holdings to detect stock concentration risk.
持仓穿透去重预警：抓取各基金前十大持仓股，计算跨基金有效暴露，对超阈值股票发出预警。
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict

from ._http import request_text

_HEADERS = [
    "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer: https://fundf10.eastmoney.com/",
]


class StockHolding(TypedDict):
    stock_code: str
    stock_name: str
    weight_pct: float    # weight within the fund / 该股在基金内的权重%


class FundHoldings(TypedDict):
    code: str
    report_date: str
    top_holdings: list[StockHolding]


class OverlapStock(TypedDict):
    stock_code: str
    stock_name: str
    effective_exposure_pct: float          # sum of fund_position% * stock_weight% / 有效暴露%
    contributing_funds: list[dict]         # [{code, fund_position_pct, stock_weight_pct}]
    warning: bool                          # True if effective_exposure > threshold


class PortfolioOverlapResult(TypedDict):
    fund_holdings: dict[str, FundHoldings | dict]
    overlap_stocks: list[OverlapStock]     # sorted by effective_exposure desc
    warnings: list[str]
    threshold_pct: float


def get_fund_top_holdings(code: str) -> FundHoldings | dict:
    """
    Fetch top 10 stock holdings for a fund from Eastmoney.
    从天天基金抓取基金前十大持仓股。

    Args:
        code: Fund code / 基金代码
    """
    url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={code}&topline=10"
    try:
        raw = request_text(url, extra_headers=_HEADERS)
        if not raw or "content:\"\"" in raw:
            # Empty content — fund holds no stocks (e.g. gold ETF)
            return {"code": code, "report_date": "", "top_holdings": []}

        # Report date: 截止至：<font class='px12'>2026-03-31</font>
        date_m = re.search(r"截止至：<font[^>]*>(\d{4}-\d{2}-\d{2})</font>", raw)
        report_date = date_m.group(1) if date_m else ""

        # Each data row: <tr><td>seq</td><td ...>code</td><td ...>name</td>...<td class='tor'>8.68%</td>...
        rows = re.findall(r"<tr>(.*?)</tr>", raw, re.DOTALL)
        top_holdings: list[StockHolding] = []

        for row in rows:
            tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            if len(tds) < 7:
                continue
            def _text(s: str) -> str:
                return re.sub(r"<[^>]+>", "", s).strip()

            seq = _text(tds[0])
            if not seq.isdigit():
                continue  # skip header or non-data rows

            stock_code = _text(tds[1])
            stock_name = _text(tds[2])
            weight_str = _text(tds[6]).rstrip("%")

            if not stock_code or not stock_name:
                continue
            try:
                weight = float(weight_str)
            except ValueError:
                continue

            top_holdings.append({
                "stock_code": stock_code,
                "stock_name": stock_name,
                "weight_pct": weight,
            })

        return {"code": code, "report_date": report_date, "top_holdings": top_holdings[:10]}

    except Exception as e:
        return {"code": code, "error": str(e)}


def get_multi_fund_top_holdings(codes: list[str]) -> dict[str, FundHoldings | dict]:
    """
    Fetch top holdings for multiple funds concurrently.
    并发抓取多只基金的前十大持仓股。
    """
    results: dict[str, FundHoldings | dict] = {}
    with ThreadPoolExecutor(max_workers=min(len(codes), 10)) as executor:
        futures = {executor.submit(get_fund_top_holdings, code): code for code in codes}
        for future in as_completed(futures):
            code = futures[future]
            try:
                results[code] = future.result()
            except Exception as e:
                results[code] = {"code": code, "error": str(e)}
    return results


def check_portfolio_overlap(
    fund_positions: dict[str, float],
    threshold_pct: float = 3.0,
) -> PortfolioOverlapResult:
    """
    Detect stock concentration risk across funds by penetrating holdings.
    穿透各基金持仓，识别跨基金重叠的股票集中度风险。

    Args:
        fund_positions: Fund code → position % in portfolio (e.g. {"012970": 9.64})
                        基金代码 → 该基金在组合中的仓位占比%
        threshold_pct: Effective exposure % above which a warning is raised (default 3.0)
                       有效暴露超过此阈值时发出预警，默认 3.0%

    Returns:
        PortfolioOverlapResult with per-stock effective exposure and warnings.
        包含各股有效暴露和预警的结果。
    """
    codes = list(fund_positions.keys())
    fund_holdings_map = get_multi_fund_top_holdings(codes)

    # Aggregate effective exposure per stock across all funds
    # effective_exposure(stock) = sum over funds of: fund_position_pct * stock_weight_pct / 100
    stock_exposure: dict[str, dict] = {}  # stock_code -> aggregated data

    for code, position_pct in fund_positions.items():
        holdings_data = fund_holdings_map.get(code, {})
        if "error" in holdings_data or not holdings_data.get("top_holdings"):
            continue
        for stock in holdings_data["top_holdings"]:
            sc = stock["stock_code"]
            if not sc:
                continue
            contribution = position_pct * stock["weight_pct"] / 100
            if sc not in stock_exposure:
                stock_exposure[sc] = {
                    "stock_code": sc,
                    "stock_name": stock["stock_name"],
                    "effective_exposure_pct": 0.0,
                    "contributing_funds": [],
                }
            stock_exposure[sc]["effective_exposure_pct"] += contribution
            stock_exposure[sc]["contributing_funds"].append({
                "code": code,
                "fund_position_pct": position_pct,
                "stock_weight_pct": stock["weight_pct"],
            })

    # Round and sort
    overlap_stocks: list[OverlapStock] = []
    for sc, data in stock_exposure.items():
        data["effective_exposure_pct"] = round(data["effective_exposure_pct"], 2)
        data["warning"] = data["effective_exposure_pct"] >= threshold_pct
        overlap_stocks.append(data)  # type: ignore[arg-type]

    overlap_stocks.sort(key=lambda x: x["effective_exposure_pct"], reverse=True)

    # Build warning messages
    warnings: list[str] = []

    # Data quality notes: flag funds with no holdings or stale data (>365 days)
    from datetime import date, timedelta
    stale_cutoff = (date.today() - timedelta(days=365)).isoformat()
    for code, h in fund_holdings_map.items():
        if "error" in h:
            warnings.append(f"【数据缺失】{code} 持仓抓取失败，已跳过穿透计算")
        elif not h.get("top_holdings"):
            warnings.append(f"【无股票持仓】{code} 无个股持仓数据（可能为ETF联接或商品基金，已跳过）")
        elif h.get("report_date", "") < stale_cutoff:
            warnings.append(f"【数据过期】{code} 持仓数据截止 {h['report_date']}（超过1年），穿透结果仅供参考")

    warned = [s for s in overlap_stocks if s["warning"]]
    if warned:
        for s in warned:
            funds_str = "、".join(
                f"{c['code']}({c['stock_weight_pct']:.1f}%)" for c in s["contributing_funds"]
            )
            warnings.append(
                f"【重叠预警】{s['stock_name']}({s['stock_code']}) "
                f"有效暴露 {s['effective_exposure_pct']:.2f}%，"
                f"出现在：{funds_str}"
            )
    elif not any("缺失" in w or "过期" in w for w in warnings):
        warnings.append(f"无股票有效暴露超过 {threshold_pct}%，持仓分散度正常")

    return {
        "fund_holdings": fund_holdings_map,
        "overlap_stocks": overlap_stocks,
        "warnings": warnings,
        "threshold_pct": threshold_pct,
    }
