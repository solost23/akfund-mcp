"""
Daily market report example — customize FUNDS and SECTORS to your needs.
每日行情摘要示例 — 按需修改 FUNDS 和 SECTORS。
"""

import akfund

# ── Configure your funds here / 在这里配置你关注的基金 ──────────────────────────
FUNDS = {
    "270023": "广发全球精选QDII",
    "012970": "鹏华半导体芯片",
    "008702": "华夏黄金",
    # add more / 继续添加...
}

# ── Market quotes / 市场行情 ────────────────────────────────────────────────────
print("=" * 60)
print("【市场行情】")
print("=" * 60)
market = akfund.get_market_quotes()
for name, q in market.items():
    if "error" in q:
        print(f"  {name}: ERROR")
    else:
        pct = q["chg_pct"]
        sign = "+" if pct and pct >= 0 else ""
        print(f"  {name:<10} {q['price']:>12}   {sign}{pct:.2f}%")

# ── Sector quotes / 板块行情 ────────────────────────────────────────────────────
print("\n【申万行业板块】")
print("=" * 60)
sectors = akfund.get_sector_quotes()
for name, q in sectors.items():
    if "error" in q:
        print(f"  {name}: ERROR")
    else:
        pct = q["chg_pct"]
        sign = "+" if pct and pct >= 0 else ""
        print(f"  {name:<8} {sign}{pct:.2f}%")

# ── Fund estimates & metrics / 基金估值与技术指标 ───────────────────────────────
print("\n【基金数据】")
print("=" * 60)
for code, name in FUNDS.items():
    rt = akfund.get_realtime_estimate(code)
    metrics = akfund.get_fund_metrics(code)

    if "error" not in rt:
        print(f"  {name} ({code})")
        print(f"    今日估值: {rt['gsz']:.4f}  涨跌: {rt['gszzl']:+.2f}%  时间: {rt['gztime']}")
    if "error" not in metrics:
        print(f"    近1周: {metrics['ret_1w']:+.2f}%  近1月: {metrics['ret_1m']:+.2f}%  "
              f"近3月: {metrics['ret_3m']:+.2f}%  位置: {metrics['position']}  "
              f"连续{metrics['streak_dir']}{metrics['streak_days']}天")
    print()

# ── News / 快讯 ─────────────────────────────────────────────────────────────────
print("【东方财富快讯（相关）】")
print("=" * 60)
for t, title in akfund.get_eastmoney_news(pages=4):
    print(f"  {t}  {title}")

print("\n【金十数据快讯（相关）】")
print("=" * 60)
for t, imp, text in akfund.get_jin10_news():
    flag = "★" if imp else " "
    print(f"  {flag} {t}  {text}")
