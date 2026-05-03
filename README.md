# akfund

China mutual fund & market data toolkit.

Fetch realtime estimates, NAV history, sector quotes, and news from Eastmoney, Jin10, and official Chinese financial sources — no API key required.

中国公募基金 & 市场行情数据抓取工具库。无需 API Key，直接抓取天天基金、东方财富、金十数据、申万行业板块及官方宏观数据。

---

## Requirements / 环境要求

- Python 3.11+
- `curl`（macOS / Linux 系统自带；Windows 需单独安装）

## Installation / 安装

```bash
git clone https://github.com/solost23/akfund.git
cd akfund
pip install -e .
```

## Usage / 使用方法

### 1. 盘中基金估值

```python
import akfund

rt = akfund.get_realtime_estimate("012970")
print(rt)
# {
#   'code': '012970',
#   'gsz': 1.2671,      # 估算净值
#   'gszzl': 5.36,      # 估算涨跌幅 %
#   'gztime': '2026-04-30 15:00'
# }
```

### 2. 历史净值 + 技术指标

```python
# 近180个交易日历史净值（最新在前）
history = akfund.get_nav_history("012970", target=180)
# [{'date': '2026-04-30', 'nav': 1.2626}, ...]

# 技术指标：涨跌幅、最大回撤、高低位、连涨连跌
metrics = akfund.get_fund_metrics("012970")
# {
#   'latest_date': '2026-04-30',
#   'latest_nav': 1.2626,
#   'ret_1w': 9.81,      # 近1周涨跌幅 %
#   'ret_1m': 22.05,     # 近1月
#   'ret_3m': 4.33,      # 近3月
#   'ret_6m': 15.90,     # 近6月
#   'dd30': -8.35,       # 近30日最大回撤 %
#   'position': '高位',  # 相对近3月均值：高位 / 中位 / 低位
#   'streak_dir': '涨',  # 连涨 or 连跌
#   'streak_days': 1
# }
```

### 3. 市场行情

```python
market = akfund.get_market_quotes()
# 默认包含：上证指数、深证成指、创业板指、纳斯达克、标普500、道琼斯、
#           美元指数、恒生指数、沪金主连、美元人民币、美国半导体

print(market["上证指数"])
# {'name': '上证指数', 'price': 4112.16, 'chg_amt': 4.65, 'chg_pct': 0.11}

# 自定义标的（东方财富 secid 格式）
custom = akfund.get_market_quotes({
    "上证指数": "1.000001",
    "黄金主连": "113.aum",
})
```

### 4. 申万行业板块

```python
sectors = akfund.get_sector_quotes()
# 默认包含：半导体、光伏设备、光伏主材、机器人、基础化工、软件开发、黄金、有色金属、计算机

print(sectors["半导体"])
# {'name': '半导体', 'price': 2507.92, 'chg_pct': 3.4}

# 自定义板块
custom = akfund.get_sector_quotes({
    "半导体": "90.BK1036",
    "新能源车": "90.BK1012",
})
```

### 5. 快讯与新闻

```python
# 东方财富快讯（按内置关键词过滤，返回 (时间, 标题) 列表）
for t, title in akfund.get_eastmoney_news(pages=4):
    print(t, title)

# 金十数据快讯（返回 (时间, 是否重要, 内容) 列表，is_important=1 为重要）
for t, is_important, text in akfund.get_jin10_news():
    flag = "★" if is_important else " "
    print(flag, t, text)

# 国内财经媒体头条（中国证券报、财新、证券时报、上海证券报）
media = akfund.get_domestic_media()
for title in media["cs"]:      # cs / caixin / stcn / cnstock
    print(title)

# 官方宏观数据（央行、统计局、证监会、外汇局）
macro = akfund.get_official_macro()
for title in macro["pbc"]:     # pbc / stats / csrc / safe
    print(title)

# 海外来源（美联储货币政策 RSS、世界黄金协会）
overseas = akfund.get_overseas()
for date, title in overseas["fed"]:   # fed / wgc
    print(date, title)
```

### 6. 自定义关键词过滤

所有新闻接口都支持传入自定义关键词列表：

```python
news = akfund.get_eastmoney_news(keywords=["黄金", "美联储", "降息"])
```

### 7. 一键每日报告

```bash
python examples/daily_report.py
```

---

## API reference / 接口一览

| 函数 | 说明 |
|---|---|
| `get_realtime_estimate(code)` | 盘中估算净值和涨跌幅 |
| `get_nav_history(code, target=180)` | 历史净值列表（最新在前） |
| `get_fund_metrics(code, history=None)` | 技术指标（涨跌幅/回撤/位置/连涨跌） |
| `get_market_quotes(markets=None)` | 市场指数、汇率、大宗商品行情 |
| `get_sector_quotes(sectors=None)` | 申万行业板块实时涨跌幅 |
| `get_eastmoney_news(pages=8, keywords=None)` | 东方财富快讯 |
| `get_jin10_news(keywords=None)` | 金十数据快讯 |
| `get_domestic_media(keywords=None)` | 国内财经媒体头条 |
| `get_official_macro()` | 央行、统计局、证监会、外汇局 |
| `get_overseas()` | 美联储 RSS、世界黄金协会 |

---

## Known limitations / 已知限制

以下来源因技术原因无法抓取：

- 第一财经：纯客户端渲染，curl 无法获取正文
- investing.com：Cloudflare 拦截
- 中国基金报：域名 DNS 解析失败

---

## License

MIT
