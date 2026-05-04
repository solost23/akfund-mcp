"""
After-fee true return calculation.
费后真实收益计算：将申购费计入成本基础，展示假设赎回后的净收益。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict

from .fund import get_nav_history


class FundAfterFeeHolding(TypedDict):
    code: str
    shares: float
    latest_nav: float
    latest_date: str
    market_value: float
    position_pct: float


class AfterFeeReturn(TypedDict):
    holdings: list[FundAfterFeeHolding]
    total_value: float
    baseline_value: float
    cumulative_net_inflow: float
    total_fees_paid: float
    true_cost_basis: float
    paper_gain: float
    paper_return_pct: float
    net_proceeds_if_sell: float
    net_gain_if_sell: float
    net_return_if_sell_pct: float
    redemption_fee_pct: float


def calc_after_fee_return(
    holdings: dict[str, float],
    baseline_value: float,
    cumulative_net_inflow: float = 0.0,
    fees_paid: float = 0.0,
    redemption_fee_pct: float = 0.0,
) -> AfterFeeReturn | dict:
    """
    Compute after-fee true return.
    计算费后真实收益。

    Args:
        holdings: Fund code → share count / 基金代码 → 持有份额
        baseline_value: Portfolio value at tracking start / 追踪起始日总市值基准
        cumulative_net_inflow: Net buy-ins since tracking start / 追踪期累计净买入
        fees_paid: Total subscription fees paid since tracking start / 追踪期内累计已付申购费
        redemption_fee_pct: Assumed redemption fee % if selling today (e.g. 0.5) /
                            假设今日赎回费率（如 0.5 表示 0.5%）

    Returns:
        AfterFeeReturn with paper return (fees in cost basis) and net-if-sell return.
        包含账面收益（费用计入成本）和假设赎回后净收益。
    """
    def _fetch(code: str) -> tuple[str, float, str]:
        history = get_nav_history(code, target=1)
        if history:
            return code, history[0]["nav"], history[0]["date"]
        return code, 0.0, ""

    nav_map: dict[str, tuple[float, str]] = {}
    with ThreadPoolExecutor(max_workers=min(len(holdings), 10)) as executor:
        futures = {executor.submit(_fetch, code): code for code in holdings}
        for future in as_completed(futures):
            code, nav, date = future.result()
            nav_map[code] = (nav, date)

    result_holdings: list[FundAfterFeeHolding] = []
    total_value = 0.0
    for code, shares in holdings.items():
        nav, date = nav_map.get(code, (0.0, ""))
        mv = round(shares * nav, 2)
        total_value += mv
        result_holdings.append({
            "code": code,
            "shares": shares,
            "latest_nav": nav,
            "latest_date": date,
            "market_value": mv,
            "position_pct": 0.0,
        })

    total_value = round(total_value, 2)
    for h in result_holdings:
        h["position_pct"] = round(h["market_value"] / total_value * 100, 2) if total_value else 0.0

    # True cost basis includes subscription fees paid
    true_cost_basis = round(baseline_value + cumulative_net_inflow + fees_paid, 2)
    paper_gain = round(total_value - true_cost_basis, 2)
    paper_return_pct = round(paper_gain / true_cost_basis * 100, 2) if true_cost_basis else 0.0

    # Net proceeds if selling everything today after redemption fee
    net_proceeds_if_sell = round(total_value * (1 - redemption_fee_pct / 100), 2)
    net_gain_if_sell = round(net_proceeds_if_sell - true_cost_basis, 2)
    net_return_if_sell_pct = round(net_gain_if_sell / true_cost_basis * 100, 2) if true_cost_basis else 0.0

    return {
        "holdings": result_holdings,
        "total_value": total_value,
        "baseline_value": baseline_value,
        "cumulative_net_inflow": cumulative_net_inflow,
        "total_fees_paid": fees_paid,
        "true_cost_basis": true_cost_basis,
        "paper_gain": paper_gain,
        "paper_return_pct": paper_return_pct,
        "net_proceeds_if_sell": net_proceeds_if_sell,
        "net_gain_if_sell": net_gain_if_sell,
        "net_return_if_sell_pct": net_return_if_sell_pct,
        "redemption_fee_pct": redemption_fee_pct,
    }
