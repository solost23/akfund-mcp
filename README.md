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
| Claude Code | `~/.claude/settings.json` |

---

## 使用方式

akfund-mcp 只负责数据抓取，本身不包含任何投资逻辑。要让 AI 真正帮你做基金决策，还需要在项目目录下准备一个规则文件，告诉 AI 你的持仓、决策框架和操作偏好。

### 规则文件

在你的项目目录（即 Claude Code 的工作目录）下创建一个 Markdown 文件，例如 `基金每日决策助手.md`，内容包括：

- **持仓快照**：你持有哪些基金、当前市值、仓位占比
- **决策框架**：加仓/减仓的触发条件、仓位上限、止盈规则等
- **数据源规则**：各基金对应的申万板块映射、消息源优先级
- **输出格式**：每日决策结果的展示方式

文件准备好后，每天只需对 AI 说一句：

> 按流程跑今天的基金决策

AI 会读取规则文件，调用 akfund-mcp 拉取相关数据，结合你的持仓和规则给出操作建议。



| 工具 | 参数 | 说明 |
|---|---|---|
| `get_realtime_estimate` | `code` | 单只基金盘中估值和涨跌幅 |
| `get_fund_metrics` | `code`, `days=180` | 技术指标（涨跌幅/回撤/高低位/连涨跌） |
| `get_nav_history` | `code`, `days=30` | 历史净值列表 |
| `get_market_quotes` | — | A股、美股、黄金、汇率行情 |
| `get_sector_quotes` | `sectors=["半导体","黄金"]` | 申万行业板块涨跌幅，不传返回全部 |
| `get_eastmoney_news` | `pages=4`, `keywords=[...]` | 东方财富快讯，按关键词过滤 |
| `get_jin10_news` | `keywords=[...]` | 金十数据快讯，按关键词过滤 |
| `get_domestic_media` | `keywords=[...]` | 国内财经媒体头条，按关键词过滤 |
| `get_official_macro` | — | 央行、统计局、证监会、外汇局 |
| `get_overseas` | — | 美联储 RSS、世界黄金协会 |

`get_sector_quotes` 支持的板块名称：半导体、光伏设备、光伏主材、机器人、基础化工、软件开发、黄金、有色金属、计算机、银行、非银金融、医药生物、食品饮料、消费者服务、房地产、建筑材料、建筑装饰、电力设备、电子、通信、传媒、汽车、家用电器、纺织服饰、轻工制造、农林牧渔、钢铁、煤炭、石油石化、交通运输、公用事业、环保、国防军工、商贸零售、社会服务。

---

## License

MIT
