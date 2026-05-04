"""
akfund — China mutual fund & market data toolkit
中国公募基金 & 市场行情数据抓取工具库
"""

from .fund import (
    get_realtime_estimate,
    get_nav_history,
    get_fund_metrics,
    get_multi_fund_metrics,
    get_multi_realtime_estimates,
    get_portfolio_summary,
    search_fund,
)
from .market import get_market_quotes
from .sector import get_sector_quotes
from .news import get_eastmoney_news, get_jin10_news, get_domestic_media, get_official_macro, get_overseas
from .brief import get_daily_brief
from .info import get_fund_info, get_multi_fund_info
from .calendar import get_trading_status
from .fees import calc_after_fee_return
from .overlap import get_fund_top_holdings, get_multi_fund_top_holdings, check_portfolio_overlap
from .checklist import run_trade_checklist

__all__ = [
    "get_realtime_estimate",
    "get_nav_history",
    "get_fund_metrics",
    "get_multi_fund_metrics",
    "get_multi_realtime_estimates",
    "get_portfolio_summary",
    "search_fund",
    "get_market_quotes",
    "get_sector_quotes",
    "get_eastmoney_news",
    "get_jin10_news",
    "get_domestic_media",
    "get_official_macro",
    "get_overseas",
    "get_daily_brief",
    "get_fund_info",
    "get_multi_fund_info",
    "get_trading_status",
    "calc_after_fee_return",
    "get_fund_top_holdings",
    "get_multi_fund_top_holdings",
    "check_portfolio_overlap",
    "run_trade_checklist",
]
