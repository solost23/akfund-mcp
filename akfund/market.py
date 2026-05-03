"""
Market quotes: A-share indices, US markets, gold, FX, and more.
市场行情：A股指数、美股、黄金、汇率等
"""

from typing import TypedDict

from ._http import request_json


class Quote(TypedDict):
    name: str
    price: float | None
    chg_amt: float | None
    chg_pct: float | None


# Default market secids (Eastmoney push2delay format)
# 默认行情标的（东方财富 push2delay 格式）
DEFAULT_MARKETS: dict[str, str] = {
    "上证指数":   "1.000001",
    "深证成指":   "0.399001",
    "创业板指":   "0.399006",
    "纳斯达克":   "100.NDX",
    "标普500":    "100.SPX",
    "道琼斯":     "100.DJIA",
    "美元指数":   "100.UDI",
    "恒生指数":   "100.HSI",
    "沪金主连":   "113.aum",
    "美元人民币": "120.USDCNYC",
    "美国半导体": "202.US36978",
}


def get_market_quotes(markets: dict[str, str] | None = None) -> dict[str, Quote | dict]:
    """
    Fetch real-time quotes for market indices, FX, and commodities.
    抓取市场指数、汇率、大宗商品实时行情。

    Args:
        markets: Mapping of display name → Eastmoney secid.
                 Defaults to DEFAULT_MARKETS if not provided.
                 标的名称 → 东方财富 secid 映射，不传则使用默认列表。

    Returns:
        Dict keyed by name. Each value is a Quote or {"error": str}.
        以名称为 key 的字典，值为 Quote 或 {"error": str}。
    """
    if markets is None:
        markets = DEFAULT_MARKETS

    results: dict[str, Quote | dict] = {}
    for name, secid in markets.items():
        url = (
            f"https://push2delay.eastmoney.com/api/qt/stock/get"
            f"?secid={secid}&fields=f43,f58,f169,f170&fltt=2"
            f"&ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        try:
            data = request_json(url)
            d = data.get("data") or {}
            results[name] = {
                "name": name,
                "price": d.get("f43"),
                "chg_amt": d.get("f169"),
                "chg_pct": d.get("f170"),
            }
        except Exception as e:
            results[name] = {"name": name, "error": str(e)}
    return results
