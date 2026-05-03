"""
Shenwan industry sector quotes.
申万行业板块实时行情
"""

from typing import TypedDict

from ._http import request_batch


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
}


def get_sector_quotes(sectors: list[str] | None = None) -> dict[str, SectorQuote | dict]:
    """
    Fetch real-time quotes for Shenwan industry sectors (single batch request).
    一次批量请求抓取申万行业板块实时涨跌幅。

    Args:
        sectors: List of sector names to query, e.g. ["半导体", "黄金", "机器人"].
                 Must be keys from ALL_SECTORS. Fetches all sectors if None.
                 板块名称列表，必须是 ALL_SECTORS 中的键，不传则返回全部板块。

    Returns:
        Dict keyed by sector name. Each value is a SectorQuote or {"error": str}.
    """
    if sectors is None:
        target = ALL_SECTORS
    else:
        target = {name: ALL_SECTORS[name] for name in sectors if name in ALL_SECTORS}

    if not target:
        return {}

    # secid -> display name, for mapping results back
    secid_to_name = {secid: name for name, secid in target.items()}
    rows = request_batch(list(target.values()), fields="f12,f14,f2,f3")

    results: dict[str, SectorQuote | dict] = {}
    returned: set[str] = set()
    for row in rows:
        # match by secid suffix (API strips the "90." prefix in f12)
        f12 = row.get("f12", "")
        secid = next((s for s in target.values() if s.endswith(f12)), None)
        if not secid:
            continue
        name = secid_to_name[secid]
        returned.add(name)
        results[name] = {
            "name": name,
            "price": row.get("f2"),
            "chg_pct": row.get("f3"),
        }

    for name in target:
        if name not in returned:
            results[name] = {"name": name, "error": "no data"}

    return results
