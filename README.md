# akfund

China mutual fund & market data toolkit.

Fetch realtime estimates, NAV history, sector quotes, and news from Eastmoney, Jin10, and official Chinese financial sources — no API key required.

中国公募基金 & 市场行情数据抓取工具库。无需 API Key，直接抓取天天基金、东方财富、金十数据、申万行业板块及官方宏观数据。

---

## Features / 功能

- **Realtime fund estimates** — intraday estimated NAV and change % for any fund code
  **盘中基金估值** — 任意基金代码的实时估算净值和涨跌幅
- **NAV history & metrics** — up to 180 trading days, with 1w/1m/3m/6m returns, max drawdown, position, and streak
  **历史净值与技术指标** — 近180个交易日，含近1周/1月/3月/6月涨跌幅、最大回撤、高低位判断、连涨连跌天数
- **Market quotes** — A-share indices, US markets, gold, FX (Eastmoney push2delay)
  **市场行情** — A股指数、美股、黄金、汇率
- **Shenwan sector quotes** — 9 default sectors, fully configurable
  **申万行业板块** — 默认9个板块，可自定义
- **News aggregation** — Eastmoney flash, Jin10, CS.com.cn, Caixin, STCN, PBC, Stats Bureau, CSRC, SAFE, Fed RSS, WGC
  **多源快讯聚合** — 东方财富、金十、中国证券报、财新、证券时报、央行、统计局、证监会、外汇局、美联储、世界黄金协会

## Requirements / 依赖

- Python 3.11+
- `curl` (system, used to avoid TLS issues with Eastmoney APIs / 用于规避东方财富接口 TLS 限制)

## Installation / 安装

```bash
pip install -e .
```

## Quick start / 快速开始

```python
import akfund

# Realtime estimate for a single fund / 单只基金盘中估值
rt = akfund.get_realtime_estimate("012970")
print(rt)
# {'code': '012970', 'gsz': 1.2671, 'gszzl': 5.36, 'gztime': '2026-04-30 15:00'}

# NAV history + technical metrics / 历史净值 + 技术指标
metrics = akfund.get_fund_metrics("012970")
print(metrics["position"], metrics["ret_1m"])
# '高位' 22.05

# Market quotes / 市场行情
market = akfund.get_market_quotes()
print(market["上证指数"])

# Shenwan sector quotes / 申万行业板块
sectors = akfund.get_sector_quotes()
print(sectors["半导体"])

# News / 快讯
for t, title in akfund.get_eastmoney_news(pages=2):
    print(t, title)
```

See [`examples/daily_report.py`](examples/daily_report.py) for a full daily report.

完整每日行情摘要示例见 [`examples/daily_report.py`](examples/daily_report.py)。

## API reference / 接口说明

| Function | Description |
|---|---|
| `get_realtime_estimate(code)` | Intraday estimated NAV / 盘中估值 |
| `get_nav_history(code, target=180)` | Historical NAV records / 历史净值 |
| `get_fund_metrics(code)` | Technical metrics from NAV history / 技术指标 |
| `get_market_quotes(markets=None)` | Market index & FX quotes / 市场行情 |
| `get_sector_quotes(sectors=None)` | Shenwan sector quotes / 申万板块 |
| `get_eastmoney_news(pages=8, keywords=None)` | Eastmoney flash news / 东方财富快讯 |
| `get_jin10_news(keywords=None)` | Jin10 flash news / 金十数据快讯 |
| `get_domestic_media(keywords=None)` | Chinese financial media headlines / 国内财经媒体 |
| `get_official_macro()` | PBC, Stats Bureau, CSRC, SAFE / 官方宏观数据 |
| `get_overseas()` | Fed RSS, WGC / 海外来源 |

## Known limitations / 已知限制

- 第一财经：纯客户端渲染，curl 无法获取正文
- investing.com：Cloudflare 拦截
- 中国基金报：域名 DNS 解析失败

## License

MIT
