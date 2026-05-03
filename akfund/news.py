"""
News aggregation from multiple Chinese and overseas financial sources.
多源财经快讯聚合：东方财富、金十数据、国内媒体、官方宏观、海外来源
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from ._http import request_text

_GOV_UA = "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

_KEYWORDS = [
    "半导体", "芯片", "光伏", "机器人", "化工", "软件", "黄金", "有色", "金属",
    "QDII", "美股", "纳斯达克", "标普", "汇率", "人民币", "美元", "美联储",
    "关税", "贸易", "降息", "加息", "通胀", "CPI", "PPI", "GDP",
    "基金", "ETF", "A股", "创业板", "科创板",
]


def _is_relevant(text: str, keywords: list[str] | None = None) -> bool:
    kws = keywords if keywords is not None else _KEYWORDS
    return any(kw in text for kw in kws)


def _parse_items_from_html(
    raw: str,
    pattern: str,
    max_items: int = 10,
    filter_fn=None,
) -> list[str]:
    items = []
    seen: set[str] = set()
    for m in re.finditer(pattern, raw):
        t = (m.group(1) if m.lastindex == 1 else (m.group(1) or m.group(2))).strip()
        if t and t not in seen and len(t) > 5 and "${" not in t:
            seen.add(t)
            if filter_fn is None or filter_fn(t):
                items.append(t)
            if len(items) >= max_items:
                break
    return items


def _fetch_eastmoney_page(page: int, keywords: list[str] | None) -> list[tuple[str, str]]:
    headers = [
        "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept: application/json, text/plain, */*",
        "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        "Referer: https://finance.eastmoney.com/",
    ]
    url = f"https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_{page}_.html"
    try:
        raw = request_text(url, extra_headers=headers)
        m = re.search(r"var ajaxResult\s*=\s*(\{.*)", raw, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(1))
        return [
            (item.get("showtime", ""), item.get("title", "").strip())
            for item in data.get("LivesList", [])
            if item.get("title", "").strip() and _is_relevant(item.get("title", ""), keywords)
        ]
    except Exception:
        return []


def get_eastmoney_news(pages: int = 8, keywords: list[str] | None = None) -> list[tuple[str, str]]:
    """
    Fetch flash news from Eastmoney, filtered by keywords (pages fetched concurrently).
    并发抓取东方财富快讯，按关键词过滤。

    Args:
        pages: Number of pages to fetch (50 items/page) / 抓取页数，每页50条
        keywords: Filter keywords. Defaults to built-in financial keywords.
    """
    all_news: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=min(pages, 8)) as executor:
        futures = {executor.submit(_fetch_eastmoney_page, p, keywords): p for p in range(1, pages + 1)}
        page_results: dict[int, list[tuple[str, str]]] = {}
        for future in as_completed(futures):
            page_results[futures[future]] = future.result()
    for p in range(1, pages + 1):
        all_news.extend(page_results.get(p, []))
    return all_news


def get_jin10_news(keywords: list[str] | None = None) -> list[tuple[str, int, str]]:
    """
    Fetch flash news from Jin10 (金十数据), filtered by keywords.
    抓取金十数据快讯，按关键词过滤。
    """
    headers = [
        "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer: https://www.jin10.com/",
    ]
    try:
        raw = request_text("https://www.jin10.com/flash_newest.js", extra_headers=headers)
        m = re.search(r"var newest\s*=\s*(\[.*?\]);", raw, re.DOTALL)
        if not m:
            return []
        items = json.loads(m.group(1))
        news = []
        for item in items:
            d = item.get("data", {})
            title = d.get("title", "").strip()
            content = re.sub(r"<[^>]+>", "", d.get("content", "")).strip()
            text = title or content
            if text and _is_relevant(text, keywords):
                news.append((item.get("time", ""), item.get("important", 0), text[:120]))
        return news
    except Exception:
        return []


def _fetch_cs(filter_fn) -> list[str]:
    try:
        raw = request_text("https://www.cs.com.cn/", extra_headers=[_GOV_UA])
        skip = {"中证快讯 7x24", "中国证券报"}
        return _parse_items_from_html(
            raw,
            r'<a[^>]+href="[^"]+\.html"[^>]*>([^<]{8,80})</a>',
            max_items=8,
            filter_fn=lambda t: filter_fn(t) and t not in skip and not t.startswith("·"),
        )
    except Exception:
        return []


def _fetch_caixin(filter_fn) -> list[str]:
    try:
        raw = request_text("https://www.caixin.com/", extra_headers=[_GOV_UA])
        return _parse_items_from_html(
            raw,
            r'<a[^>]+href="https?://[^"]+\.html"[^>]*>([^<]{8,80})</a>',
            max_items=8,
            filter_fn=filter_fn,
        )
    except Exception:
        return []


def _fetch_stcn(filter_fn) -> list[str]:
    try:
        raw = request_text("https://www.stcn.com/", extra_headers=[_GOV_UA])
        if not raw or len(raw) < 1000:
            return []
        return _parse_items_from_html(
            raw,
            r'<a[^>]+href="/article/detail/\d+\.html"[^>]*>([^<]{8,80})</a>',
            max_items=10,
            filter_fn=filter_fn,
        )
    except Exception:
        return []


def _fetch_cnstock(filter_fn) -> list[str]:
    try:
        raw = request_text("https://www.cnstock.com/", extra_headers=[_GOV_UA], follow=True)
        if not raw or len(raw) < 1000:
            return []
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', raw, re.DOTALL)
        if not m:
            return []
        page_data = json.loads(m.group(1))
        _noise = {"专题", "上证", "视频｜", "H5｜", "业绩说明会", "年报"}
        raw_titles: list[str] = []

        def _collect(obj, depth=0):
            if depth > 10:
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ("title", "articleTitle", "headline") and isinstance(v, str) and 10 < len(v) < 100:
                        raw_titles.append(v)
                    else:
                        _collect(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj[:60]:
                    _collect(item, depth + 1)

        _collect(page_data)
        seen: set[str] = set()
        results = []
        for t in raw_titles:
            t = t.strip()
            if t and t not in seen and not any(n in t for n in _noise) and filter_fn(t):
                seen.add(t)
                results.append(t)
            if len(results) >= 10:
                break
        return results
    except Exception:
        return []


def get_domestic_media(keywords: list[str] | None = None) -> dict[str, list[str]]:
    """
    Scrape headlines from major Chinese financial media (sources fetched concurrently).
    并发抓取国内主要财经媒体头条。

    Returns:
        Dict with keys: cs, caixin, stcn, cnstock.
    """
    filter_fn = lambda t: _is_relevant(t, keywords)
    fetchers = {
        "cs":      lambda: _fetch_cs(filter_fn),
        "caixin":  lambda: _fetch_caixin(filter_fn),
        "stcn":    lambda: _fetch_stcn(filter_fn),
        "cnstock": lambda: _fetch_cnstock(filter_fn),
    }
    results: dict[str, list[str]] = {k: [] for k in fetchers}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): key for key, fn in fetchers.items()}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


def _fetch_pbc() -> list[str]:
    try:
        raw = request_text(
            "https://www.pbc.gov.cn/goutongjiaoliu/113456/2986536/index.html",
            extra_headers=[_GOV_UA],
        )
        titles = re.findall(r"<title><!\[CDATA\[([^\]]+)\]\]></title>", raw)
        return [t.strip() for t in titles[1:6]]
    except Exception:
        return []


def _fetch_stats() -> list[str]:
    try:
        raw = request_text("https://www.stats.gov.cn/sj/zxfb/", extra_headers=[_GOV_UA])
        items = re.findall(r'<a[^>]+href="\./[^"]+\.html"[^>]*>([^<]{5,60})</a>', raw)
        seen: set[str] = set()
        results = []
        for title in items:
            title = title.strip()
            if title and title not in seen and "..." not in title:
                seen.add(title)
                results.append(title)
            if len(results) >= 5:
                break
        return results
    except Exception:
        return []


def _fetch_csrc() -> list[str]:
    try:
        raw = request_text(
            "https://www.csrc.gov.cn/csrc/xwfb/index.shtml",
            extra_headers=[_GOV_UA],
            follow=True,
        )
        items = re.findall(r'<a[^>]+href="/csrc/[^"]+\.shtml"[^>]*>([^<]{5,80})</a>', raw)
        seen: set[str] = set()
        results = []
        for title in items:
            title = title.strip()
            if title and title not in seen and "证监会" not in title[:3] and "新闻发布会" not in title:
                seen.add(title)
                results.append(title)
            if len(results) >= 5:
                break
        return results
    except Exception:
        return []


def _fetch_safe() -> list[str]:
    try:
        raw = request_text(
            "https://www.safe.gov.cn/safe/whxw/index.html",
            extra_headers=[_GOV_UA],
        )
        items = re.findall(r'<a[^>]+href="/safe/[^"]+\.html"[^>]*>([^<]{5,80})</a>', raw)
        seen: set[str] = set()
        results = []
        for title in items:
            title = title.strip()
            if title and title not in seen:
                seen.add(title)
                results.append(title)
            if len(results) >= 5:
                break
        return results
    except Exception:
        return []


def get_official_macro() -> dict[str, list[str]]:
    """
    Fetch latest headlines from official Chinese macro sources (fetched concurrently).
    并发抓取国内官方宏观数据来源最新标题。

    Returns:
        Dict with keys: pbc, stats, csrc, safe.
    """
    fetchers = {"pbc": _fetch_pbc, "stats": _fetch_stats, "csrc": _fetch_csrc, "safe": _fetch_safe}
    results: dict[str, list[str]] = {k: [] for k in fetchers}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): key for key, fn in fetchers.items()}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


def _fetch_fed() -> list[tuple[str, str]]:
    try:
        raw = request_text("https://www.federalreserve.gov/feeds/press_monetary.xml")
        titles = re.findall(r"<title>([^<]+)</title>", raw)
        dates = re.findall(r"<pubDate>(?:<!\[CDATA\[)?([^\]<]+?)(?:\]\]>)?</pubDate>", raw)
        return [(date.strip()[:16], title.strip()) for title, date in zip(titles[1:4], dates[:3])]
    except Exception:
        return []


def _fetch_wgc() -> list[tuple[str, str]]:
    try:
        raw = request_text("https://china.gold.org/news/", extra_headers=[_GOV_UA], follow=True)
        titles = re.findall(r"<h[23][^>]*>([^<]{10,80})</h[23]>", raw)
        seen: set[str] = set()
        results = []
        for title in titles:
            title = title.strip()
            if title and title not in seen and "navigation" not in title.lower() and "黄金现货" not in title:
                seen.add(title)
                results.append(("", title))
            if len(results) >= 3:
                break
        return results
    except Exception:
        return []


def get_overseas() -> dict[str, list[tuple[str, str]]]:
    """
    Fetch headlines from overseas financial sources (fetched concurrently).
    并发抓取海外财经来源最新标题。

    Returns:
        Dict with keys: fed, wgc.
    """
    fetchers = {"fed": _fetch_fed, "wgc": _fetch_wgc}
    results: dict[str, list[tuple[str, str]]] = {k: [] for k in fetchers}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(fn): key for key, fn in fetchers.items()}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results
