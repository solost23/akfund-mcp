"""
akfund MCP server — expose akfund tools to any MCP-compatible client.
将 akfund 的数据接口暴露为 MCP 工具，供 Claude 桌面版、Cursor 等客户端直接调用。
"""

import json
from mcp.server.fastmcp import FastMCP
import akfund

mcp = FastMCP("akfund")


@mcp.tool()
def get_realtime_estimate(code: str) -> str:
    """
    Get intraday estimated NAV and change % for a fund.
    获取基金盘中估算净值和涨跌幅。

    Args:
        code: Fund code, e.g. "012970" / 基金代码，例如 "012970"
    """
    result = akfund.get_realtime_estimate(code)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_fund_metrics(code: str, days: int = 180) -> str:
    """
    Get technical metrics for a fund: returns, max drawdown, position, streak.
    获取基金技术指标：各周期涨跌幅、最大回撤、高低位、连涨连跌天数。

    Args:
        code: Fund code / 基金代码
        days: Number of trading days of history to use (default 180) / 历史净值天数，默认180
    """
    history = akfund.get_nav_history(code, target=days)
    result = akfund.get_fund_metrics(code, history=history)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_nav_history(code: str, days: int = 30) -> str:
    """
    Get historical NAV records for a fund, newest first.
    获取基金历史净值列表，最新在前。

    Args:
        code: Fund code / 基金代码
        days: Number of trading days to return (default 30) / 返回交易日数量，默认30
    """
    result = akfund.get_nav_history(code, target=days)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_market_quotes() -> str:
    """
    Get real-time quotes for major market indices, FX, and commodities.
    获取主要市场指数、汇率、大宗商品实时行情（A股、美股、黄金、人民币等）。
    """
    result = akfund.get_market_quotes()
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_sector_quotes(sectors: list[str] | None = None) -> str:
    """
    Get real-time quotes for Shenwan industry sectors.
    获取申万行业板块实时涨跌幅。

    Args:
        sectors: List of sector names to query, e.g. ["半导体", "黄金", "机器人"].
                 Returns all supported sectors if not provided.
                 Available sectors include: 半导体、光伏设备、光伏主材、机器人、基础化工、
                 软件开发、黄金、有色金属、计算机、银行、医药生物、食品饮料、电子、通信、
                 汽车、家用电器、煤炭、石油石化、国防军工 等。
                 板块名称列表，不传则返回全部支持的板块。
    """
    result = akfund.get_sector_quotes(sectors=sectors)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_eastmoney_news(pages: int = 4, keywords: list[str] | None = None) -> str:
    """
    Get flash news from Eastmoney, filtered by keywords.
    获取东方财富快讯，按关键词过滤。

    Args:
        pages: Number of pages to fetch, 50 items/page (default 4) / 抓取页数，每页50条，默认4页
        keywords: Keywords to filter by. Pass only the terms relevant to your holdings
                  to get faster, more targeted results, e.g. ["半导体", "芯片", "光伏"].
                  Defaults to a broad built-in financial keyword list if not provided.
                  过滤关键词，建议只传与持仓相关的词以加快速度，不传则使用内置宽泛关键词列表。
    """
    result = akfund.get_eastmoney_news(pages=pages, keywords=keywords)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_jin10_news(keywords: list[str] | None = None) -> str:
    """
    Get flash news from Jin10 (金十数据), filtered by keywords.
    获取金十数据快讯，按关键词过滤。

    Args:
        keywords: Keywords to filter by. Pass only the terms relevant to your holdings
                  for faster, more targeted results, e.g. ["黄金", "美联储", "汇率"].
                  Defaults to a broad built-in financial keyword list if not provided.
                  过滤关键词，建议只传与持仓相关的词，不传则使用内置宽泛关键词列表。
    """
    result = akfund.get_jin10_news(keywords=keywords)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_domestic_media(keywords: list[str] | None = None) -> str:
    """
    Get headlines from major Chinese financial media.
    获取国内主要财经媒体头条（中国证券报、财新网、证券时报、上海证券报）。

    Args:
        keywords: Keywords to filter by. Pass only the terms relevant to your holdings
                  for faster, more targeted results, e.g. ["半导体", "光伏", "机器人"].
                  Defaults to a broad built-in financial keyword list if not provided.
                  过滤关键词，建议只传与持仓相关的词，不传则使用内置宽泛关键词列表。
    """
    result = akfund.get_domestic_media(keywords=keywords)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_official_macro() -> str:
    """
    Get latest headlines from official Chinese macro sources.
    获取官方宏观数据来源最新标题（央行、国家统计局、证监会、外汇局）。
    """
    result = akfund.get_official_macro()
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_overseas() -> str:
    """
    Get headlines from overseas financial sources.
    获取海外财经来源最新标题（美联储货币政策 RSS、世界黄金协会）。
    """
    result = akfund.get_overseas()
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")


def main():
    mcp.run(transport="stdio")
