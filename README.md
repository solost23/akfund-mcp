# akfund-mcp

中国公募基金 & 市场行情 MCP 工具，支持接入 Claude、Cursor 等 AI 客户端。

---

## 安装

需要先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

```bash
uv tool install git+https://github.com/solost23/akfund-mcp
```

升级到最新版本：

```bash
uv tool upgrade akfund-mcp
```

---

## 接入 AI 客户端

在对应客户端的配置文件中添加以下内容，然后重启客户端：

```json
{
  "mcpServers": {
    "akfund": {
      "command": "akfund-mcp"
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

## 可用工具

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
