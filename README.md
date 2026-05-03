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

akfund-mcp 只负责数据抓取，本身不包含任何投资逻辑。你需要在项目目录下创建一个规则文件，告诉 AI 你的持仓和决策偏好，然后每天对 AI 说一句话，它会自动拉取数据并给出操作建议。

### 第一步：创建规则文件

在你的工作目录下新建一个 Markdown 文件（例如 `基金助手.md`），按以下模板填入你的信息：

```markdown
# 基金每日决策助手

## 持仓

| 基金代码 | 基金名称 | 持有份额 |
|---|---|---:|
| XXXXXX | 基金名称A | 1000.00 |
| XXXXXX | 基金名称B | 2000.00 |

## 收益追踪基准
- 基准日：YYYY-MM-DD，基准市值：XXXXX.XX

## 决策偏好
（在这里写你的操作风格，例如：偏保守/偏激进、止盈止损规则、仓位上限等）

## 执行流程
每天说"按流程跑今天的基金决策"时：
1. 调用 get_trading_status() 判断今天是否交易日
2. 调用 get_portfolio_summary() 计算持仓市值和收益
3. 调用 get_multi_fund_metrics() 获取技术指标
4. 调用 get_multi_realtime_estimates() 获取盘中估值
5. 调用 get_daily_brief() 获取市场行情和新闻
6. 综合以上数据给出操作建议
```

### 第二步：开始使用

文件准备好后，每天只需对 AI 说：

> 按流程跑今天的基金决策

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

**`get_sector_quotes`** 支持的板块名称：
半导体、光伏设备、光伏主材、机器人、基础化工、软件开发、黄金、有色金属、计算机、银行、非银金融、医药生物、食品饮料、消费者服务、房地产、建筑材料、建筑装饰、电力设备、电子、通信、传媒、汽车、家用电器、纺织服饰、轻工制造、农林牧渔、钢铁、煤炭、石油石化、交通运输、公用事业、环保、国防军工、商贸零售、社会服务。

---

## License

MIT
