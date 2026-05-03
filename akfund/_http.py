"""
HTTP utilities shared across modules.
所有模块共用的 HTTP 请求工具（基于 curl，规避 TLS 限流问题）
"""

import json
import random
import subprocess

_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

_ACCEPT_LANGUAGES = [
    "zh-CN,zh;q=0.9,en;q=0.8",
    "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
]


def _rand_headers(referer: str) -> list[str]:
    ua = random.choice(_USER_AGENTS)
    lang = random.choice(_ACCEPT_LANGUAGES)
    return [
        "-H", f"User-Agent: {ua}",
        "-H", "Accept: application/json, text/plain, */*",
        "-H", f"Accept-Language: {lang}",
        "-H", f"Referer: {referer}",
    ]


def request_json(url: str, referer: str = "https://quote.eastmoney.com/", timeout: int = 15) -> dict:
    """Fetch URL and parse response as JSON. / 抓取 URL 并解析为 JSON。"""
    r = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout)] + _rand_headers(referer) + [url],
        capture_output=True, text=True,
    )
    return json.loads(r.stdout)


def request_fund_json(url: str, timeout: int = 15) -> dict:
    """Fetch fund API with fund-specific headers. / 使用基金专用 headers 抓取接口。"""
    headers = [
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "-H", "Accept: application/json, text/plain, */*",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        "-H", "Referer: https://fundf10.eastmoney.com/",
    ]
    r = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout)] + headers + [url],
        capture_output=True, text=True,
    )
    return json.loads(r.stdout)


def request_batch(secids: list[str], fields: str, timeout: int = 15) -> list[dict]:
    """
    Fetch multiple secids in a single request via ulist.np/get.
    一次请求批量抓取多个标的行情，返回 diff 列表。
    """
    url = (
        "https://push2delay.eastmoney.com/api/qt/ulist.np/get"
        f"?secids={','.join(secids)}&fields={fields}"
        "&fltt=2&ut=fa5fd1943c7b386f172d6893dbfba10b&invt=2"
    )
    try:
        data = request_json(url)
        return (data.get("data") or {}).get("diff") or []
    except Exception:
        return []


def request_text(url: str, extra_headers: list[str] | None = None, follow: bool = False, timeout: int = 10) -> str:
    """Fetch URL and return raw text. / 抓取 URL 并返回原始文本。"""
    cmd = ["curl", "-s", "--max-time", str(timeout)]
    if follow:
        cmd.append("-L")
    if extra_headers:
        for h in extra_headers:
            cmd += ["-H", h]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout
