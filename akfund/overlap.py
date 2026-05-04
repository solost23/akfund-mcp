"""
Portfolio overlap analysis: penetrate fund holdings to detect stock concentration risk.
持仓穿透去重预警：抓取各基金前十大持仓股，计算跨基金有效暴露，对超阈值股票发出预警。
"""

import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict

from ._http import request_fund_json


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
    url = (
        f"https://api.fund.eastmoney.com/f10/JJCC"
        f"?fundCode={code}&pageIndex=1&pageSize=10"
    )
    try:
        data = request_fund_json(url)
        # Response structure: {"Data": {"fundStocks": [...], "SYRQDate": "..."}}
        inner = data.get("Data") or {}
        stocks_raw = inner.get("fundStocks") or []
        report_date = inner.get("SYRQDate", "")

        top_holdings: list[StockHolding] = []
        for s in stocks_raw[:10]:
            try:
                top_holdings.append({
                    "stock_code": s.get("GPDM", ""),
                    "stock_name": s.get("GPJC", ""),
                    "weight_pct": float(s.get("JZBL", 0)),
                })
            except (ValueError, TypeError):
                pass

        return {
            "code": code,
            "report_date": report_date,
            "top_holdings": top_holdings,
        }
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
    else:
        warnings.append(f"无股票有效暴露超过 {threshold_pct}%，持仓分散度正常")

    return {
        "fund_holdings": fund_holdings_map,
        "overlap_stocks": overlap_stocks,
        "warnings": warnings,
        "threshold_pct": threshold_pct,
    }
