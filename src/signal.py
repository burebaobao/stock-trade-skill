"""
交易信号生成模块

综合评分 → 买入推荐 → 风险提示 → 交易计划。
支持两种数据源：
- lhb_detail：个股上榜详情（净买额、涨跌幅等）
- lhb_seats：营业部买卖明细（游资、机构识别）
"""
import pandas as pd
from datetime import datetime

from src.config import (
    SCORING,
    SIGNAL_THRESHOLD,
    TOP_N,
    STOP_LOSS,
    TAKE_PROFIT,
    HOLD_DAYS,
    FAMOUS_SEATS,
)
from src.logger import get_logger
from src.utils import (
    load_latest_data,
    load_multi_day_data,
    _get_seat_col,
    _get_code_col,
    _get_name_col,
    _safe_float,
    check_consecutive_listed,
)
from src.analyzer import analyze_institutions

logger = get_logger(__name__)


def calculate_score(detail_df: pd.DataFrame, seats_df: pd.DataFrame = None, multi_day_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    计算每只股票的综合得分

    评分规则（config.SCORING）:
    - 知名游资买入 +20
    - 机构净买入 +15
    - 净买入占比 > 10% +10
    - 连续上榜 +10
    - 高胜率席位买入 +5

    Args:
        detail_df: 个股详情数据
        seats_df: 营业部明细数据（可选，用于游资/机构识别）
        multi_day_df: 多日数据（可选，用于判断连续上榜）

    Returns:
        DataFrame: 含 score 列，按得分降序
    """
    code_col = _get_code_col(detail_df)
    name_col = _get_name_col(detail_df)

    # 基础数据
    result = detail_df[[code_col, name_col]].copy()
    result = result.drop_duplicates(subset=[code_col]).reset_index(drop=True)

    # 净买额
    if "龙虎榜净买额" in detail_df.columns:
        net_df = detail_df[[code_col, "龙虎榜净买额", "龙虎榜买入额", "龙虎榜卖出额"]].copy()
        net_df = net_df.groupby(code_col).first().reset_index()
        result = result.merge(net_df, on=code_col, how="left")
        result["总成交额"] = result["龙虎榜买入额"] + result["龙虎榜卖出额"]
        result["净买入占比"] = (
            result["龙虎榜净买额"] / result["总成交额"].replace(0, 1) * 100
        ).round(2)
    else:
        result["龙虎榜净买额"] = 0
        result["净买入占比"] = 0

    result["score"] = 0.0
    result["reasons"] = ""

    # 逐只评分
    for idx, row in result.iterrows():
        code = row[code_col]
        score = 0
        reasons = []

        # 1. 知名游资买入（需要营业部明细）
        if seats_df is not None and not seats_df.empty:
            seat_col = _get_seat_col(seats_df)
            if seat_col:
                stock_seats = seats_df[seats_df[code_col] == code]
                # 去重游资，避免重复加分
                added_nicknames = set()
                for keyword, info in FAMOUS_SEATS.items():
                    matched = stock_seats[
                        stock_seats[seat_col].astype(str).str.contains(keyword, na=False)
                    ]
                    buy_amounts = matched["买入金额"].apply(_safe_float)
                    buy_matched = matched[buy_amounts > 0]
                    if not buy_matched.empty and info["nickname"] not in added_nicknames:
                        score += SCORING["famous_buy"]
                        reasons.append(f"{info['nickname']}买入")
                        added_nicknames.add(info["nickname"])
                        if info["win_rate"] > 0.6:
                            score += SCORING["high_win_rate"]
                            reasons.append(f"{info['nickname']}高胜率")

        # 2. 机构净买入
        if seats_df is not None and not seats_df.empty:
            inst = analyze_institutions(seats_df[seats_df[code_col] == code])
            if not inst.empty and inst["机构净买入"].sum() > 0:
                score += SCORING["institution_buy"]
                reasons.append("机构净买入")

        # 3. 净买入占比
        if row["净买入占比"] > 10:
            score += SCORING["net_ratio_high"]
            reasons.append(f"净占比{row['净买入占比']:.0f}%")

        # 4. 连续上榜
        if multi_day_df is not None and check_consecutive_listed(code, multi_day_df, code_col):
            score += SCORING["consecutive"]
            reasons.append("连续上榜")

        result.at[idx, "score"] = score
        result.at[idx, "reasons"] = "、".join(reasons) if reasons else "无明显信号"

    return result.sort_values("score", ascending=False).reset_index(drop=True)


def get_risk_warnings(seats_df: pd.DataFrame) -> list:
    """
    生成风险提示（知名游资卖出、机构大额卖出）

    Args:
        seats_df: 营业部明细数据

    Returns:
        list: 风险提示字符串列表
    """
    if seats_df is None or seats_df.empty:
        return []

    warnings = []
    seat_col = _get_seat_col(seats_df)
    code_col = _get_code_col(seats_df)
    name_col = _get_name_col(seats_df)

    if seat_col is None:
        return warnings

    # 去重游资
    processed_nicknames = set()
    for keyword, info in FAMOUS_SEATS.items():
        if info["nickname"] in processed_nicknames:
            continue
        mask = seats_df[seat_col].astype(str).str.contains(keyword, na=False)
        # 正确过滤卖出记录
        sells = seats_df[mask].copy()
        sells = sells[sells["卖出金额"].apply(_safe_float) > 0]
        
        for _, s in sells.head(3).iterrows():
            code = s.get(code_col, "")
            name = s.get(name_col, "")
            amount = _safe_float(s.get("卖出金额", 0))
            warnings.append(
                f"{code} {name}：{info['nickname']}卖出{amount / 1e4:.0f}万，建议关注"
            )
        processed_nicknames.add(info["nickname"])

    return warnings


def generate_signals(detail_df: pd.DataFrame, seats_df: pd.DataFrame = None, multi_day_df: pd.DataFrame = None, date_str: str = None):
    """
    生成完整的交易信号报告

    Args:
        detail_df: 个股详情数据
        seats_df: 营业部明细数据
        multi_day_df: 多日数据
        date_str: 日期
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'=' * 60}")
    print(f"  交易信号报告 | 生成时间: {date_str} 收盘后")
    print(f"{'=' * 60}")

    # 计算得分
    scores = calculate_score(detail_df, seats_df, multi_day_df)

    # 买入推荐
    qualified = scores[scores["score"] >= SIGNAL_THRESHOLD]
    top = qualified.head(TOP_N)

    print(f"\n【次日买入推荐】（阈值 >= {SIGNAL_THRESHOLD} 分，取 Top {TOP_N}）")
    print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'得分':<6} {'理由'}")
    print("-" * 60)

    if top.empty:
        print("  今日无符合条件的买入信号")
    else:
        code_col = _get_code_col(detail_df)
        name_col = _get_name_col(detail_df)
        for i, (_, row) in enumerate(top.iterrows(), 1):
            print(
                f"{i:<4} {row[code_col]:<8} {row[name_col]:<10} "
                f"{row['score']:<6.0f} {row['reasons']}"
            )
    
    # 显示得分前 10 名（即使不满足阈值）
    print(f"\n【得分前 10 名】（包含未达阈值）")
    print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'得分':<6} {'理由'}")
    print("-" * 60)
    code_col = _get_code_col(detail_df)
    name_col = _get_name_col(detail_df)
    for i, (_, row) in enumerate(scores.head(10).iterrows(), 1):
        print(
            f"{i:<4} {row[code_col]:<8} {row[name_col]:<10} "
            f"{row['score']:<6.0f} {row['reasons']}"
        )

    # 风险提示
    print(f"\n【持仓风险提示】")
    print("-" * 45)
    warnings = get_risk_warnings(seats_df)
    if warnings:
        for w in warnings:
            print(f"  - {w}")
    else:
        print("  今日无特别风险提示")

    # 交易计划
    print(f"\n【交易计划】")
    print("-" * 45)
    print(f"  买入：按推荐排名，每只仓位 {100 // TOP_N}%")
    print(f"  止损：{STOP_LOSS * 100:.0f}%")
    print(f"  止盈：+{TAKE_PROFIT * 100:.0f}%")
    print(f"  持有周期：{HOLD_DAYS[0]}-{HOLD_DAYS[1]} 天")
    print(f"\n{'=' * 60}\n")

    return top


def run(days: int = 5):
    """一键执行信号生成"""
    # 加载多日数据用于连续上榜判断
    multi_day_df = load_multi_day_data("lhb_detail", days=days)
    
    # 加载最新一天的数据用于主要分析
    latest_detail_df, loaded_date = load_latest_data("lhb_detail")

    # 尝试加载营业部明细
    try:
        seats_df = load_multi_day_data("lhb_seats", days=days)
    except FileNotFoundError:
        seats_df = None

    return generate_signals(latest_detail_df, seats_df, multi_day_df, loaded_date)


if __name__ == "__main__":
    run()
