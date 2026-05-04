"""
Pre-trade regret-free checklist.
决策前强制免悔清单：自动校验关键条件，防止情绪化操作。
"""

from typing import TypedDict, Literal


class CheckItem(TypedDict):
    item: str
    status: Literal["pass", "warn", "fail", "manual"]
    detail: str


class TradeChecklist(TypedDict):
    action: str
    code: str
    amount: float
    auto_checks: list[CheckItem]
    manual_checks: list[CheckItem]
    verdict: Literal["proceed", "caution", "block"]
    verdict_reason: str


def run_trade_checklist(
    action: Literal["buy", "sell"],
    code: str,
    amount: float,
    today_change_pct: float,
    position_pct: float,
    streak_dir: str,
    streak_days: int,
    is_trading_day: bool,
    is_pre_holiday: bool,
    already_traded_today: bool = False,
) -> TradeChecklist:
    """
    Run pre-trade checklist against the decision framework rules.
    按决策框架规则运行交易前免悔清单。

    Args:
        action: "buy" or "sell" / 买入或卖出
        code: Fund code / 基金代码
        amount: Trade amount in yuan / 交易金额（元）
        today_change_pct: Today's estimated change % (e.g. 1.8 means +1.8%) / 今日估值涨跌幅
        position_pct: Current position % in portfolio / 该基金当前仓位占比%
        streak_dir: Consecutive direction "涨" or "跌" / 连续方向
        streak_days: Number of consecutive days / 连续天数
        is_trading_day: Whether today is a trading day / 今天是否是交易日
        is_pre_holiday: Whether today is the last trading day before a holiday / 是否节前最后交易日
        already_traded_today: Whether this fund was already traded today / 今天是否已对该基金操作过

    Returns:
        TradeChecklist with auto-checked items, manual items, and a final verdict.
        包含自动检查项、手动确认项和最终裁决的清单。
    """
    auto_checks: list[CheckItem] = []
    manual_checks: list[CheckItem] = []
    blocks = 0
    warns = 0

    # 1. Trading day
    if not is_trading_day:
        auto_checks.append({
            "item": "今天是否是交易日",
            "status": "fail",
            "detail": "今天不是交易日，无法执行",
        })
        blocks += 1
    else:
        auto_checks.append({
            "item": "今天是否是交易日",
            "status": "pass",
            "detail": "是交易日",
        })

    # 2. Pre-holiday
    if is_pre_holiday:
        auto_checks.append({
            "item": "节前最后交易日风险",
            "status": "warn",
            "detail": "今天是节前最后交易日，节假日期间无法操作，需评估假期海外波动风险",
        })
        warns += 1
    else:
        auto_checks.append({
            "item": "节前最后交易日风险",
            "status": "pass",
            "detail": "不是节前最后交易日",
        })

    if action == "buy":
        # 3. No chasing high: today change > +1.5%
        if today_change_pct > 1.5:
            auto_checks.append({
                "item": "今日估值涨幅 ≤ +1.5%（禁止追高）",
                "status": "fail",
                "detail": f"今日估值 {today_change_pct:+.2f}%，超过 +1.5%，当日取消加仓",
            })
            blocks += 1
        else:
            auto_checks.append({
                "item": "今日估值涨幅 ≤ +1.5%（禁止追高）",
                "status": "pass",
                "detail": f"今日估值 {today_change_pct:+.2f}%，未追高",
            })

        # 4. No chasing streak: consecutive up >= 3 days
        if streak_dir == "涨" and streak_days >= 3:
            auto_checks.append({
                "item": "连续上涨天数 < 3（禁止追涨）",
                "status": "fail",
                "detail": f"已连涨 {streak_days} 天，原则上不追涨加仓",
            })
            blocks += 1
        else:
            streak_info = f"连{streak_dir}{streak_days}天" if streak_days > 0 else "无明显连续趋势"
            auto_checks.append({
                "item": "连续上涨天数 < 3（禁止追涨）",
                "status": "pass",
                "detail": streak_info,
            })

        # 5. Position ceiling
        if position_pct >= 15:
            auto_checks.append({
                "item": "单只基金仓位上限（≥15% 需说明）",
                "status": "warn",
                "detail": f"当前仓位 {position_pct:.1f}%，已达 15% 上限，加仓需明确说明突破理由",
            })
            warns += 1
        else:
            label = "10-15% 区间，加仓门槛提高" if position_pct >= 10 else "仓位正常"
            auto_checks.append({
                "item": "单只基金仓位上限（≥15% 需说明）",
                "status": "pass",
                "detail": f"当前仓位 {position_pct:.1f}%，{label}",
            })

        # 6. No same-day repeat buy
        if already_traded_today:
            auto_checks.append({
                "item": "今天未对该基金重复操作",
                "status": "warn",
                "detail": "今天已对该基金操作过，除非盘面有明显新变化，否则不再追加",
            })
            warns += 1
        else:
            auto_checks.append({
                "item": "今天未对该基金重复操作",
                "status": "pass",
                "detail": "今天尚未对该基金操作",
            })

    elif action == "sell":
        # 7. Panic sell check
        if today_change_pct < -3:
            auto_checks.append({
                "item": "非情绪化杀跌",
                "status": "warn",
                "detail": f"今日跌幅 {today_change_pct:+.2f}%，注意是否情绪化杀跌，先确认逻辑是否破坏",
            })
            warns += 1
        else:
            auto_checks.append({
                "item": "非情绪化杀跌",
                "status": "pass",
                "detail": f"今日涨跌 {today_change_pct:+.2f}%，非极端下跌",
            })

        # 8. High position sell check (止盈合理性)
        if today_change_pct > 3 and position_pct >= 10:
            auto_checks.append({
                "item": "大涨止盈合理性",
                "status": "warn",
                "detail": f"今日涨幅 {today_change_pct:+.2f}% 且仓位 {position_pct:.1f}%，"
                          "确认是情绪驱动还是逻辑强化，再决定止盈幅度",
            })
            warns += 1
        else:
            auto_checks.append({
                "item": "大涨止盈合理性",
                "status": "pass",
                "detail": "无大涨止盈特殊情况",
            })

    # Manual checks (always required)
    manual_checks = [
        {
            "item": "原有买入逻辑是否仍然成立",
            "status": "manual",
            "detail": "需人工确认：行业景气度、政策方向、基金经理是否有变化",
        },
        {
            "item": "消息面是否有新增重大利空",
            "status": "manual",
            "detail": "需人工确认：今日新闻是否有影响该基金的重大负面消息",
        },
        {
            "item": "操作是否符合当日优先级",
            "status": "manual",
            "detail": "需人工确认：是否是今日第1或第2优先操作对象，结论是否已因盘面变化而更新",
        },
    ]

    # Verdict
    if blocks > 0:
        verdict: Literal["proceed", "caution", "block"] = "block"
        verdict_reason = f"{blocks} 项硬规则未通过，建议取消本次操作"
    elif warns >= 2:
        verdict = "caution"
        verdict_reason = f"{warns} 项警告，建议降级处理或明确说明突破理由后再执行"
    elif warns == 1:
        verdict = "caution"
        verdict_reason = "1 项警告，核实后再执行"
    else:
        verdict = "proceed"
        verdict_reason = "自动检查全部通过，确认手动项后可执行"

    return {
        "action": action,
        "code": code,
        "amount": amount,
        "auto_checks": auto_checks,
        "manual_checks": manual_checks,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }
