# akfund-mcp

中国公募基金 & 市场行情 MCP 工具，支持接入 Claude、Cursor 等 AI 客户端。

---

## 接入 AI 客户端

需要先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

在对应客户端的配置文件中添加以下内容，然后重启客户端：

```json
{
  "mcpServers": {
    "akfund": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/solost23/akfund-mcp", "akfund-mcp"]
    }
  }
}
```

| 客户端 | 配置文件路径 |
|---|---|
| Claude 桌面版（macOS） | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude 桌面版（Windows） | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | 项目根目录 `.cursor/mcp.json` |
| Claude Code | `~/.claude/settings.json` 或 `~/.claude.json` |

---

## 使用方式

akfund-mcp 只负责数据抓取，本身不包含任何投资逻辑。要让 AI 真正帮你做基金决策，还需要在项目目录下准备一个规则文件，告诉 AI 你的持仓、决策框架和操作偏好。

### 规则文件

在你的项目目录（即 Claude Code 的工作目录）下创建一个 Markdown 文件，例如 `基金每日决策助手.md`，内容包括：

- **持仓快照**：持有哪些基金、持有份额、当前市值、仓位占比
- **收益追踪**：基准市值、累计净买入、追踪期收益记录表
- **决策框架**：加仓/减仓的触发条件、仓位上限、止盈规则等
- **数据源规则**：各基金对应的申万板块映射、消息源优先级
- **输出格式**：每日决策结果的展示方式

文件准备好后，每天只需对 AI 说一句：

> 按流程跑今天的基金决策

AI 会读取规则文件，调用 akfund-mcp 拉取相关数据，结合你的持仓和规则给出操作建议。

### 推荐的每日决策流程

每次决策建议按以下顺序并发调用工具，减少等待时间和 token 消耗：

```
1. get_trading_status()                          # 判断今天是否交易日、是否节前
2. get_portfolio_summary(holdings, ...)          # 持仓市值 + 追踪期收益（一次调用）
3. get_multi_fund_metrics(codes, days=180)       # 10只基金技术指标（并发）
4. get_multi_realtime_estimates(codes)           # 盘中估值（并发）
5. get_daily_brief(sectors, keywords)            # 市场行情 + 板块 + 全部新闻（一次并发调用）
```

步骤 2-5 可以并发执行，整体数据采集通常在 10 秒内完成。

### 基金监控

定期（每周或每月）调用以下工具检查持仓基金的基本面变化：

```
get_multi_fund_info(codes)   # 检查基金经理是否变更、规模是否超限
```

---

## 工具列表

### 基金数据

| 工具 | 参数 | 说明 |
|---|---|---|
| `search_fund` | `name`, `limit=10` | 按名称或关键词搜索基金，返回代码和基本信息 |
| `get_realtime_estimate` | `code` | 单只基金盘中估值和涨跌幅 |
| `get_multi_realtime_estimates` | `codes` | 多只基金盘中估值（并发） |
| `get_fund_metrics` | `code`, `days=180` | 技术指标（涨跌幅/回撤/高低位/连涨跌） |
| `get_multi_fund_metrics` | `codes`, `days=180` | 多只基金技术指标（并发） |
| `get_nav_history` | `code`, `days=30` | 历史净值列表 |
| `get_fund_info` | `code` | 基金经理、资产规模、管理费率、成立日期 |
| `get_multi_fund_info` | `codes` | 多只基金基本信息（并发） |
| `get_portfolio_summary` | `holdings`, `baseline_value`, `cumulative_net_inflow=0` | 持仓市值、仓位占比、追踪期收益（并发拉取最新净值） |

### 市场行情

| 工具 | 参数 | 说明 |
|---|---|---|
| `get_market_quotes` | — | A股、美股、黄金、汇率行情（批量） |
| `get_sector_quotes` | `sectors=[...]` | 申万行业板块涨跌幅，不传返回全部 |
| `get_trading_status` | `date_str=None` | A股交易日状态：是否交易日、是否节前、下一交易日 |

### 新闻与宏观

| 工具 | 参数 | 说明 |
|---|---|---|
| `get_eastmoney_news` | `pages=4`, `keywords=[...]` | 东方财富快讯，按关键词过滤（分页并发） |
| `get_jin10_news` | `keywords=[...]` | 金十数据快讯，按关键词过滤 |
| `get_domestic_media` | `keywords=[...]` | 国内财经媒体头条（中证、财新、证券时报、上证报，并发） |
| `get_official_macro` | — | 央行、统计局、证监会、外汇局（并发） |
| `get_overseas` | — | 美联储 RSS、世界黄金协会（并发） |

### 聚合工具

| 工具 | 参数 | 说明 |
|---|---|---|
| `get_daily_brief` | `sectors=[...]`, `keywords=[...]`, `news_pages=8` | 一次并发调用获取全部每日行情数据（市场+板块+所有新闻） |

---

## 参数说明

**`get_portfolio_summary`**
```python
get_portfolio_summary(
    holdings={"012970": 7090.81, "008702": 6852.77, ...},  # 基金代码 → 持有份额
    baseline_value=92861.62,   # 追踪起始日总市值
    cumulative_net_inflow=300, # 追踪期内累计净买入（买入-卖出，含定投）
)
# 返回：每只基金市值、仓位占比、总市值、追踪期收益、收益率
```

**`get_trading_status`**
```python
get_trading_status()              # 查今天
get_trading_status("2026-10-01")  # 查指定日期
# 返回：is_trading_day, is_pre_holiday, reason, holiday_name, next_trading_day, days_to_next
# reason 取值：交易日 / 周末 / 节假日 / 补班日
```

**`get_sector_quotes`** 支持的板块名称：
半导体、光伏设备、光伏主材、机器人、基础化工、软件开发、黄金、有色金属、计算机、银行、非银金融、医药生物、食品饮料、消费者服务、房地产、建筑材料、建筑装饰、电力设备、电子、通信、传媒、汽车、家用电器、纺织服饰、轻工制造、农林牧渔、钢铁、煤炭、石油石化、交通运输、公用事业、环保、国防军工、商贸零售、社会服务。

---

## License

MIT
