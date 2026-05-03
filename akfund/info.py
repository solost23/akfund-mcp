"""
Fund info: manager, AUM, fees, dividends.
基金基本信息：基金经理、规模、费率、分红。
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict

from ._http import request_text, request_fund_json

_HEADERS = [
    "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer: https://fundf10.eastmoney.com/",
]


class FundInfo(TypedDict):
    code: str
    name: str
    managers: list[str]   # current manager(s) / 当前基金经理
    aum: str              # AUM with unit, e.g. "12.34亿元" / 资产规模
    aum_date: str         # AUM report date / 规模截止日期
    management_fee: str   # e.g. "1.20%" / 管理费率
    inception_date: str   # e.g. "2021-03-15" / 成立日期
    fund_type: str        # e.g. "指数型-股票" / 基金类型


def get_fund_info(code: str) -> FundInfo | dict:
    """
    Fetch fund basic info: manager, AUM, fees, inception date.
    获取基金基本信息：基金经理、规模、管理费率、成立日期。

    Args:
        code: Fund code / 基金代码
    """
    url = f"https://fundf10.eastmoney.com/jbgk_{code}.html"
    try:
        raw = request_text(url, extra_headers=_HEADERS)
        if not raw or len(raw) < 500:
            return {"code": code, "error": "empty response"}

        def _extract(pattern: str, default: str = "") -> str:
            m = re.search(pattern, raw, re.DOTALL)
            return m.group(1).strip() if m else default

        # Fund name (short name)
        name = _extract(r'基金简称</th><td>([^<]+)</td>')

        # Fund managers
        managers = re.findall(r'基金经理：(?:&nbsp;)*\s*<a[^>]+>([^<]+)</a>', raw)
        seen: set[str] = set()
        unique_managers = []
        for m in managers:
            m = m.strip()
            if m and m not in seen:
                seen.add(m)
                unique_managers.append(m)

        # AUM: "净资产规模：<span>\n  9.40亿元\n  （截止至：2026-03-31）</span>"
        aum_m = re.search(r'净资产规模：<span>\s*([\d.]+亿元)', raw)
        aum = aum_m.group(1) if aum_m else ""
        aum_date_m = re.search(r'净资产规模：<span>.*?截止至：(\d{4}-\d{2}-\d{2})', raw, re.DOTALL)
        aum_date = aum_date_m.group(1) if aum_date_m else ""

        # Management fee: "管理费率</th><td>0.50%（每年）</td>"
        fee_m = re.search(r'管理费率</th><td>([\d.]+%)', raw)
        management_fee = fee_m.group(1) if fee_m else ""

        # Inception date: "成立日期：<span>2021-08-24</span>"
        inception_m = re.search(r'成立日期：<span>(\d{4}-\d{2}-\d{2})</span>', raw)
        inception_date = inception_m.group(1) if inception_m else ""

        # Fund type
        fund_type_m = re.search(r'基金类型</th><td><a[^>]*>([^<]+)</a>', raw)
        if not fund_type_m:
            fund_type_m = re.search(r'基金类型</th><td>([^<]+)</td>', raw)
        fund_type = fund_type_m.group(1).strip() if fund_type_m else ""

        return {
            "code": code,
            "name": name,
            "managers": unique_managers[:3],
            "aum": aum,
            "aum_date": aum_date,
            "management_fee": management_fee,
            "inception_date": inception_date,
            "fund_type": fund_type,
        }
    except Exception as e:
        return {"code": code, "error": str(e)}


def get_multi_fund_info(codes: list[str]) -> dict[str, FundInfo | dict]:
    """
    Fetch basic info for multiple funds concurrently.
    并发抓取多只基金的基本信息。

    Args:
        codes: List of fund codes / 基金代码列表
    """
    results: dict[str, FundInfo | dict] = {}
    with ThreadPoolExecutor(max_workers=min(len(codes), 10)) as executor:
        futures = {executor.submit(get_fund_info, code): code for code in codes}
        for future in as_completed(futures):
            code = futures[future]
            try:
                results[code] = future.result()
            except Exception as e:
                results[code] = {"code": code, "error": str(e)}
    return results
