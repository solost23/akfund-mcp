"""
akfund MCP server — expose akfund tools to any MCP-compatible client.
将 akfund 的数据接口暴露为 MCP 工具，供 Claude 桌面版、Cursor 等客户端直接调用。
"""

import json
from mcp.server.fastmcp import FastMCP
import akfund

mcp = FastMCP("akfund")


@mcp.tool()
def search_fund(name: str, limit: int = 10) -> str:
    """
    Search funds by name or keyword.
    通过名称或关键词搜索基金，返回匹配的基金代码和基本信息。

    Args:
        name: Fund name or keyword, e.g. "鹏华半导体", "黄金ETF", "012970" / 基金名称或关键词
        limit: Max number of results (default 10) / 最多返回条数，默认10
    """
    result = akfund.search_fund(name, limit=limit)
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
def get_realtime_estimate(code: str) -> str:
    """
    Get intraday estimated NAV and change % for a single fund.
    获取单只基金盘中估算净值和涨跌幅。

    Args:
        code: Fund code, e.g. "012970" / 基金代码，例如 "012970"
    """
    result = akfund.get_realtime_estimate(code)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_multi_fund_metrics(codes: list[str], days: int = 180) -> str:
    """
    Get technical metrics for multiple funds concurrently (faster than calling get_fund_metrics repeatedly).
    并发抓取多只基金的技术指标，比逐只调用 get_fund_metrics 快数倍。

    Args:
        codes: List of fund codes, e.g. ["012970", "008702", "012365"] / 基金代码列表
        days: Number of trading days of history to use (default 180) / 历史净值天数，默认180
    """
    result = akfund.get_multi_fund_metrics(codes, days=days)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_multi_realtime_estimates(codes: list[str]) -> str:
    """
    Get intraday estimated NAV and change % for multiple funds concurrently.
    并发抓取多只基金的盘中估值和涨跌幅。

    Args:
        codes: List of fund codes, e.g. ["012970", "008702", "012365"] / 基金代码列表
    """
    result = akfund.get_multi_realtime_estimates(codes)
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
    codes: list[str] | None = None,
) -> str:
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
    result = akfund.get_daily_brief(sectors=sectors, keywords=keywords, news_pages=news_pages, codes=codes)
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


@mcp.tool()
def calc_after_fee_return(
    holdings: dict[str, float],
    baseline_value: float,
    cumulative_net_inflow: float = 0.0,
    fees_paid: float = 0.0,
    redemption_fee_pct: float = 0.0,
) -> str:
    """
    Compute after-fee true return: adjusts cost basis for subscription fees paid,
    and shows net proceeds if selling today after redemption fees.
    计算费后真实收益：将申购费计入成本基础，展示假设赎回后的净收益。

    Args:
        holdings: Fund code → share count, e.g. {"012970": 7090.81} / 基金代码 → 持有份额
        baseline_value: Portfolio value at tracking start / 追踪起始日总市值基准
        cumulative_net_inflow: Net buy-ins since tracking start (buys - sells, including auto-invest) /
                               追踪期累计净买入（买入-卖出，含定投）
        fees_paid: Total subscription fees paid since tracking start (e.g. 45.0 means 45 yuan) /
                   追踪期内累计已付申购费（元），默认0
        redemption_fee_pct: Assumed redemption fee % if selling today (e.g. 0.5 means 0.5%) /
                            假设今日赎回费率（如 0.5 表示 0.5%），默认0

    Returns:
        AfterFeeReturn with paper_gain, paper_return_pct (fees in cost basis),
        and net_gain_if_sell, net_return_if_sell_pct (after redemption fee).
        包含账面收益（费用计入成本）和假设赎回后净收益。
    """
    result = akfund.calc_after_fee_return(
        holdings, baseline_value, cumulative_net_inflow, fees_paid, redemption_fee_pct
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def check_portfolio_overlap(
    fund_positions: dict[str, float],
    threshold_pct: float = 3.0,
) -> str:
    """
    Detect stock concentration risk by penetrating fund holdings across the portfolio.
    穿透各基金持仓，识别跨基金重叠的股票集中度风险，对有效暴露超阈值的股票发出预警。

    Args:
        fund_positions: Fund code → position % in portfolio, e.g. {"012970": 9.64, "021978": 10.36}
                        基金代码 → 该基金在组合中的仓位占比%
        threshold_pct: Effective exposure % above which a warning is raised (default 3.0) /
                       有效暴露超过此阈值时发出预警，默认 3.0%

    Returns:
        PortfolioOverlapResult with per-stock effective exposure and warning messages.
        包含各股有效暴露和预警信息的结果。
    """
    result = akfund.check_portfolio_overlap(fund_positions, threshold_pct=threshold_pct)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def run_trade_checklist(
    action: str,
    code: str,
    amount: float,
    today_change_pct: float,
    position_pct: float,
    streak_dir: str,
    streak_days: int,
    is_trading_day: bool,
    is_pre_holiday: bool,
    already_traded_today: bool = False,
) -> str:
    """
    Run pre-trade regret-free checklist against the decision framework rules.
    按决策框架规则运行交易前强制免悔清单，自动校验关键条件。

    Args:
        action: "buy" or "sell" / 买入或卖出
        code: Fund code / 基金代码
        amount: Trade amount in yuan / 交易金额（元）
        today_change_pct: Today's estimated change % (e.g. 1.8 means +1.8%) / 今日估值涨跌幅
        position_pct: Current position % in portfolio / 该基金当前仓位占比%
        streak_dir: Consecutive direction "涨" or "跌" / 连续方向
        streak_days: Number of consecutive days / 连续天数
        is_trading_day: Whether today is a trading day / 今天是否是交易日
        is_pre_holiday: Whether today is the last trading day before a holiday / 是否节前最后交易日
        already_traded_today: Whether this fund was already traded today (default False) /
                              今天是否已对该基金操作过，默认 False

    Returns:
        TradeChecklist with auto_checks, manual_checks, verdict ("proceed"/"caution"/"block"),
        and verdict_reason.
        包含自动检查项、手动确认项、裁决（proceed/caution/block）和裁决原因。
    """
    result = akfund.run_trade_checklist(
        action=action,
        code=code,
        amount=amount,
        today_change_pct=today_change_pct,
        position_pct=position_pct,
        streak_dir=streak_dir,
        streak_days=streak_days,
        is_trading_day=is_trading_day,
        is_pre_holiday=is_pre_holiday,
        already_traded_today=already_traded_today,
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_fund_rank(code: str) -> str:
    """
    Fetch peer comparison data for a fund: rank, peer average return, quartile rating.
    获取基金同类对比数据：同类排名、同类平均涨幅、四分位评级。

    Args:
        code: Fund code / 基金代码

    Returns:
        FundRank with periods list. Each period includes:
          - fund_return: this fund's return / 基金涨跌幅
          - peer_avg: peer average return / 同类平均涨跌幅
          - vs_peer: fund_return - peer_avg (positive = outperforming) / 超额收益（正数跑赢同类）
          - rank / total: e.g. 140/5003 / 同类排名/总数
          - percentile: rank/total*100, lower is better / 百分位，越低越好
          - quartile: 优秀/良好/一般/不佳 / 四分位评级
        Key for decision rules: vs_peer for 近3月 < -5% triggers heavy-operation review.
        决策规则关键字段：近3月 vs_peer < -5 触发重操作评估。
    """
    result = akfund.get_fund_rank(code)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_multi_fund_rank(codes: list[str]) -> str:
    """
    Fetch peer comparison data for multiple funds concurrently.
    并发抓取多只基金的同类对比数据（排名、同类平均、四分位）。

    Args:
        codes: List of fund codes / 基金代码列表
    """
    result = akfund.get_multi_fund_rank(codes)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def record_trade(
    code: str,
    action: str,
    amount: float,
    date_str: str | None = None,
    name: str = "",
    note: str = "",
) -> str:
    """
    Record a manual trade to persistent storage (~/.akfund/trades.json).
    记录一笔手动买卖到本地持久化存储，用于后续自动计算 cumulative_net_inflow 和 already_traded_today。

    Args:
        code: Fund code / 基金代码
        action: "buy" or "sell" / 买入或卖出
        amount: Trade amount in yuan / 交易金额（元）
        date_str: Trade date YYYY-MM-DD, defaults to today / 交易日期，默认今天
        name: Fund name for readability / 基金名称（可选，便于阅读）
        note: Optional note / 备注（可选）

    Returns:
        The recorded TradeRecord including its id (use id with delete_trade to undo).
        写入的交易记录，含 id 字段（可用 delete_trade 撤销）。
    """
    result = akfund.record_trade(
        code=code, action=action, amount=amount,
        date_str=date_str, name=name, note=note,
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def delete_trade(trade_id: str) -> str:
    """
    Delete a trade record by id (for correcting mistakes).
    按 id 删除误录的交易记录。

    Args:
        trade_id: The id field from a TradeRecord returned by record_trade /
                  record_trade 返回的 id 字段

    Returns:
        {success, deleted_record} or {success: false, error}.
    """
    result = akfund.delete_trade(trade_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_trade_history(days: int = 90, code: str | None = None) -> str:
    """
    Get trade history from persistent storage, newest first.
    从持久化存储获取交易历史，最新在前。

    Args:
        days: How many calendar days back to look (default 90) / 往前查多少天，默认90
        code: Filter by fund code / 按基金代码过滤（可选）

    Returns:
        List of TradeRecord sorted by date descending.
    """
    result = akfund.get_trade_history(days=days, code=code)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_cumulative_net_inflow(
    since_date: str,
    auto_invest: list[dict] | None = None,
) -> str:
    """
    Compute cumulative net inflow (buys - sells) since a baseline date.
    Optionally adds auto-invest amounts by counting actual A-share trading days.
    计算自基准日起的累计净买入（手动买卖 + 定投自动推算），用于传入 get_portfolio_summary 和 calc_after_fee_return。

    Args:
        since_date: Baseline date YYYY-MM-DD (exclusive — only trades strictly after this date count).
                    基准日（不含当天，只统计之后的交易）
        auto_invest: List of auto-invest configs. Each entry: {"code": "270023", "amount": 150}.
                     Amount is yuan per trading day. The tool counts actual trading days since
                     since_date using the SZSE calendar and multiplies by amount.
                     定投配置列表，每项格式 {"code": "基金代码", "amount": 每交易日金额}。
                     工具会自动按深交所交易日历统计交易日数并推算定投总额。
                     示例：[{"code":"270023","amount":150},{"code":"017730","amount":100},{"code":"012920","amount":50}]

    Returns:
        NetInflowResult with:
          - cumulative_net_inflow: total to pass into get_portfolio_summary / 传入 get_portfolio_summary 的值
          - manual_net: net from manual trades only / 手动买卖净额
          - auto_invest_total: inferred auto-invest total / 推算的定投总额
          - trading_days_counted: number of trading days used for auto-invest calc / 定投推算用的交易日数
          - by_code: per-fund breakdown / 各基金明细
    """
    result = akfund.get_cumulative_net_inflow(since_date=since_date, auto_invest=auto_invest)
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")


def main():
    mcp.run(transport="stdio")
