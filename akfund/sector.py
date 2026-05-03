"""
Shenwan industry sector quotes.
申万行业板块实时行情
"""

from typing import TypedDict

from ._http import request_json


class SectorQuote(TypedDict):
    name: str
    price: float | None
    chg_pct: float | None


# Default Shenwan sectors and their Eastmoney secids
# 默认申万行业板块及对应东方财富 secid
DEFAULT_SECTORS: dict[str, str] = {
    "半导体":  "90.BK1036",
    "光伏设备": "90.BK1031",
    "光伏主材": "90.BK1318",
    "机器人":  "90.BK1408",
    "基础化工": "90.BK1206",
    "软件开发": "90.BK0737",
    "黄金":   "90.BK1617",
    "有色金属": "90.BK0478",
    "计算机":  "90.BK1207",
}


def get_sector_quotes(sectors: dict[str, str] | None = None) -> dict[str, SectorQuote | dict]:
    """
    Fetch real-time quotes for Shenwan industry sectors.
    抓取申万行业板块实时涨跌幅。

    Args:
        sectors: Mapping of sector name → Eastmoney secid.
                 Defaults to DEFAULT_SECTORS if not provided.
                 板块名称 → 东方财富 secid 映射，不传则使用默认列表。

    Returns:
        Dict keyed by sector name. Each value is a SectorQuote or {"error": str}.
        以板块名称为 key 的字典，值为 SectorQuote 或 {"error": str}。
    """
    if sectors is None:
        sectors = DEFAULT_SECTORS

    results: dict[str, SectorQuote | dict] = {}
    for name, secid in sectors.items():
        url = (
            f"https://push2delay.eastmoney.com/api/qt/stock/get"
            f"?secid={secid}&fields=f43,f170&fltt=2"
            f"&ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        try:
            data = request_json(url)
            if not data:
                results[name] = {"name": name, "error": "empty response"}
                continue
            d = data.get("data") or {}
            results[name] = {
                "name": name,
                "price": d.get("f43"),
                "chg_pct": d.get("f170"),
            }
        except Exception as e:
            results[name] = {"name": name, "error": str(e)}
    return results
