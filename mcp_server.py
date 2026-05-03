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
        keywords: Filter keywords. Defaults to built-in financial keywords / 过滤关键词，不传则使用内置财经关键词
    """
    result = akfund.get_eastmoney_news(pages=pages, keywords=keywords)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_jin10_news(keywords: list[str] | None = None) -> str:
    """
    Get flash news from Jin10 (金十数据), filtered by keywords.
    获取金十数据快讯，按关键词过滤。

    Args:
        keywords: Filter keywords. Defaults to built-in financial keywords / 过滤关键词，不传则使用内置财经关键词
    """
    result = akfund.get_jin10_news(keywords=keywords)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_domestic_media(keywords: list[str] | None = None) -> str:
    """
    Get headlines from major Chinese financial media.
    获取国内主要财经媒体头条（中国证券报、财新网、证券时报、上海证券报）。

    Args:
        keywords: Filter keywords. Defaults to built-in financial keywords / 过滤关键词，不传则使用内置财经关键词
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


@mcp.tool()
def get_portfolio_summary(
    holdings: dict[str, float],
    baseline_value: float,
    cumulative_net_inflow: float = 0.0,
) -> str:
    """
    Compute portfolio market value, position %, and returns from share counts and latest NAVs.
    根据持仓份额和最新净值，并发计算组合市值、仓位占比和追踪期收益。

    Args:
        holdings: Fund code → share count, e.g. {"012970": 7090.81, "008702": 6852.77}
                  基金代码 → 持有份额的映射
        baseline_value: Total portfolio value at tracking start date / 追踪起始日总市值基准
        cumulative_net_inflow: Net buy-ins since tracking start (buys - sells, including auto-invest).
                               Defaults to 0.
                               追踪期内累计净买入（买入-卖出，含定投），默认0
    """
    result = akfund.get_portfolio_summary(holdings, baseline_value, cumulative_net_inflow)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_daily_brief(
    sectors: list[str] | None = None,
    keywords: list[str] | None = None,
    news_pages: int = 8,
) -> str:
    """
    Fetch all daily market data in one concurrent call: market quotes, sector quotes, and all news sources.
    一次并发调用获取所有每日行情数据，替代分别调用7个数据源工具。

    Args:
        sectors: Sector names to query, e.g. ["半导体", "黄金", "机器人"].
                 Returns all sectors if not provided.
                 板块名称列表，不传则返回全部板块。
        keywords: Keywords to filter news, e.g. ["半导体", "光伏", "黄金", "美联储"].
                  Defaults to built-in financial keyword list if not provided.
                  新闻过滤关键词，不传则使用内置财经关键词列表。
        news_pages: Eastmoney news pages to fetch, 50 items/page (default 8) / 东方财富快讯页数，默认8页

    Returns:
        Dict with keys: market, sectors, eastmoney, jin10, domestic_media, official_macro, overseas.
    """
    result = akfund.get_daily_brief(sectors=sectors, keywords=keywords, news_pages=news_pages)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_fund_info(code: str) -> str:
    """
    Fetch fund basic info: manager, AUM, management fee, inception date.
    获取基金基本信息：基金经理、资产规模、管理费率、成立日期。

    Args:
        code: Fund code / 基金代码
    """
    result = akfund.get_fund_info(code)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_multi_fund_info(codes: list[str]) -> str:
    """
    Fetch basic info for multiple funds concurrently.
    并发抓取多只基金的基本信息（经理、规模、费率、成立日期）。

    Args:
        codes: List of fund codes / 基金代码列表
    """
    result = akfund.get_multi_fund_info(codes)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_trading_status(date_str: str | None = None) -> str:
    """
    Check A-share trading status for a given date (defaults to today).
    查询指定日期（默认今天）的A股交易状态：是否交易日、是否节前最后交易日、下一交易日。

    Args:
        date_str: Date in YYYY-MM-DD format. Defaults to today / 日期，默认今天，格式 YYYY-MM-DD

    Returns:
        TradingStatus with: is_trading_day, is_pre_holiday, holiday_name, next_trading_day, days_to_next.
    """
    result = akfund.get_trading_status(date_str)
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
