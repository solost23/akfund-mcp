"""
Daily brief: aggregate all market data sources in one concurrent call.
每日行情汇总：一次并发调用获取所有市场数据。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from .fund import get_multi_realtime_estimates
from .market import get_market_quotes
from .sector import get_sector_quotes
from .news import get_eastmoney_news, get_jin10_news, get_domestic_media, get_official_macro, get_overseas


def get_daily_brief(
    sectors: list[str] | None = None,
    keywords: list[str] | None = None,
    news_pages: int = 8,
    codes: list[str] | None = None,
) -> dict:
    """
    Fetch all daily market data in one concurrent call: market quotes, sector quotes,
    realtime fund estimates, and all news sources.
    一次并发调用获取所有每日行情数据，替代分别调用7个数据源工具。

    Args:
        sectors: Sector names to query, e.g. ["半导体", "黄金", "机器人"].
                 Returns all sectors if not provided.
                 板块名称列表，不传则返回全部板块。
        keywords: Keywords to filter news, e.g. ["半导体", "光伏", "黄金", "美联储"].
                  Defaults to built-in financial keyword list if not provided.
                  新闻过滤关键词，不传则使用内置财经关键词列表。
        news_pages: Eastmoney news pages to fetch, 50 items/page (default 8) / 东方财富快讯页数，默认8页
        codes: Fund codes to fetch intraday estimates for, e.g. ["012970", "008702"].
               Skipped if not provided.
               基金代码列表，传入后并发拉取盘中估值；不传则跳过。

    Returns:
        Dict with keys: market, sectors, eastmoney, jin10, domestic_media, official_macro,
        overseas, and estimates (if codes provided).
    """
    tasks: dict = {
        "market":         lambda: get_market_quotes(),
        "sectors":        lambda: get_sector_quotes(sectors),
        "eastmoney":      lambda: get_eastmoney_news(pages=news_pages, keywords=keywords),
        "jin10":          lambda: get_jin10_news(keywords=keywords),
        "domestic_media": lambda: get_domestic_media(keywords=keywords),
        "official_macro": lambda: get_official_macro(),
        "overseas":       lambda: get_overseas(),
    }
    if codes:
        tasks["estimates"] = lambda: get_multi_realtime_estimates(codes)

    results: dict = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {executor.submit(fn): key for key, fn in tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": str(e)}

    return results
