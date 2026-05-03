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


# Comprehensive Shenwan sector name → Eastmoney secid mapping
# 申万行业板块全量映射
ALL_SECTORS: dict[str, str] = {
    "半导体":   "90.BK1036",
    "光伏设备":  "90.BK1031",
    "光伏主材":  "90.BK1318",
    "机器人":   "90.BK1408",
    "基础化工":  "90.BK1206",
    "软件开发":  "90.BK0737",
    "黄金":    "90.BK1617",
    "有色金属":  "90.BK0478",
    "计算机":   "90.BK1207",
    "银行":    "90.BK0475",
    "非银金融":  "90.BK0476",
    "医药生物":  "90.BK0465",
    "食品饮料":  "90.BK0438",
    "消费者服务": "90.BK1448",
    "房地产":   "90.BK0451",
    "建筑材料":  "90.BK0432",
    "建筑装饰":  "90.BK0433",
    "电力设备":  "90.BK1027",
    "电子":    "90.BK0452",
    "通信":    "90.BK0487",
    "传媒":    "90.BK0486",
    "汽车":    "90.BK0481",
    "家用电器":  "90.BK0443",
    "纺织服饰":  "90.BK0436",
    "轻工制造":  "90.BK0449",
    "农林牧渔":  "90.BK0430",
    "钢铁":    "90.BK0455",
    "煤炭":    "90.BK0469",
    "石油石化":  "90.BK0474",
    "交通运输":  "90.BK0461",
    "公用事业":  "90.BK0491",
    "环保":    "90.BK1021",
    "国防军工":  "90.BK0454",
    "商贸零售":  "90.BK1449",
    "社会服务":  "90.BK1447",
    "综合":    "90.BK0490",
}


def get_sector_quotes(sectors: list[str] | None = None) -> dict[str, SectorQuote | dict]:
    """
    Fetch real-time quotes for Shenwan industry sectors.
    抓取申万行业板块实时涨跌幅。

    Args:
        sectors: List of sector names to query, e.g. ["半导体", "黄金"].
                 Must be keys from ALL_SECTORS. Fetches all sectors if None.
                 板块名称列表，如 ["半导体", "黄金"]，必须是 ALL_SECTORS 中的键。
                 不传则返回全部板块。

    Returns:
        Dict keyed by sector name. Each value is a SectorQuote or {"error": str}.
        以板块名称为 key 的字典，值为 SectorQuote 或 {"error": str}。
    """
    if sectors is None:
        target = ALL_SECTORS
    else:
        target = {name: ALL_SECTORS[name] for name in sectors if name in ALL_SECTORS}
        unknown = [name for name in sectors if name not in ALL_SECTORS]
        if unknown:
            pass  # silently skip unknown names

    results: dict[str, SectorQuote | dict] = {}
    for name, secid in target.items():
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
