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

| 基金代码 | 基金名称 | 持有份额 | 当前市值 | 仓位占比 |
|---|---|---:|---:|---:|
| XXXXXX | 基金名称A | 1000.00 | 0.00 | 0.00% |
| XXXXXX | 基金名称B | 2000.00 | 0.00 | 0.00% |

## 收益追踪基准
- 基准日：YYYY-MM-DD，基准市值：XXXXX.XX
- 收益 = 当前总市值 - 基准市值 - 追踪期累计净买入
- 收益率 = 收益 ÷ (基准市值 + 追踪期累计净买入)

## 决策偏好
（在这里写你的操作风格，例如：偏保守/偏激进、止盈止损规则、仓位上限等）

## 执行流程
每天说"按流程跑今天的基金决策"时：
1. 调用 get_trading_status() 判断今天是否交易日
2. 并发调用以下工具采集数据：
   - get_portfolio_summary() 计算持仓市值和收益
   - calc_after_fee_return() 计算费后真实收益（fees_paid 默认 0）
   - get_multi_fund_metrics() 获取技术指标
   - get_multi_realtime_estimates() 获取盘中估值
   - get_daily_brief() 获取市场行情和新闻
   - check_portfolio_overlap() 检查持仓穿透重叠预警
3. 综合以上数据给出操作建议
4. 对每笔操作建议调用 run_trade_checklist() 做免悔校验：
   - verdict=block：拦截，不输出该建议
   - verdict=caution：保留建议，标注警告项
   - verdict=proceed：正常输出
5. 输出同类替换候选：对每只持仓基金，调用 search_fund() 搜索同类基金池，
   再用 get_multi_fund_rank() 批量拉排名，筛选近3月 + 近1月百分位均 ≤ 25% 的基金作为候选
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
| `calc_after_fee_return` | `holdings`, `baseline_value`, `cumulative_net_inflow=0`, `fees_paid=0`, `redemption_fee_pct=0` | 费后真实收益：将申购费计入成本基础，并展示假设赎回后净收益率 |
| `get_fund_rank` | `code` | 同类排名、同类平均涨幅、四分位评级（今年来/近1周/近1月/近3月/近6月/近1年等各周期） |
| `get_multi_fund_rank` | `codes` | 多只基金同类对比数据（并发） |

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

### 决策辅助

| 工具 | 参数 | 说明 |
|---|---|---|
| `check_portfolio_overlap` | `fund_positions`, `threshold_pct=3.0` | 穿透各基金前十大持仓股，计算跨基金有效暴露，对超阈值股票发出预警；ETF联接和商品基金自动跳过并在 warnings 中标注，持仓数据超过1年的基金标注"数据过期" |
| `run_trade_checklist` | `action`, `code`, `amount`, `today_change_pct`, `position_pct`, `streak_dir`, `streak_days`, `is_trading_day`, `is_pre_holiday`, `already_traded_today=False` | 交易前免悔清单：自动校验追高/追涨/仓位上限/节前风险等，返回 proceed/caution/block |

### 交易记录（持久化）

数据存储在 `~/.akfund/trades.json`，可通过环境变量 `AKFUND_DATA_DIR` 覆盖路径。

| 工具 | 参数 | 说明 |
|---|---|---|
| `record_trade` | `code`, `action`, `amount`, `date_str=None`, `name=""`, `note=""` | 记录一笔手动买卖，返回含 `id` 的记录（可用 `delete_trade` 撤销） |
| `delete_trade` | `trade_id` | 按 id 删除误录的交易记录 |
| `get_trade_history` | `days=90`, `code=None` | 查询历史交易，最新在前，可按基金代码和天数过滤 |
| `get_today_trades` | `code=None` | 查询今天已记录的交易，用于自动判断 `already_traded_today` |
| `get_cumulative_net_inflow` | `since_date`, `auto_invest=None` | 计算自基准日起的累计净买入；传入定投配置后自动按深交所交易日历推算定投天数并叠加，结果直接传入 `get_portfolio_summary` 和 `calc_after_fee_return` |

`auto_invest` 格式示例：
```json
[{"code": "270023", "amount": 150}, {"code": "017730", "amount": 100}, {"code": "012920", "amount": 50}]
```

**`get_sector_quotes`** 支持的板块名称：
半导体、光伏设备、光伏主材、机器人、基础化工、软件开发、黄金、有色金属、计算机、银行、非银金融、医药生物、食品饮料、消费者服务、房地产、建筑材料、建筑装饰、电力设备、电子、通信、传媒、汽车、家用电器、纺织服饰、轻工制造、农林牧渔、钢铁、煤炭、石油石化、交通运输、公用事业、环保、国防军工、商贸零售、社会服务。

---

## License

MIT
