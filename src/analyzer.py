"""
龙虎榜分析模块

分析主力动向：知名游资操作、机构专用席位、净买入占比排行。
支持两种数据源：
- lhb_detail_*.csv：个股上榜详情（fetcher fetch_lhb_detail）
- lhb_seats_*.csv：营业部买卖明细（fetcher fetch_lhb_seats）
"""
import pandas as pd
from datetime import datetime

from src.config import FAMOUS_SEATS
from src.logger import get_logger
from src.utils import (
    load_latest_data,
    load_multi_day_data,
    _get_seat_col,
    _get_code_col,
    _get_name_col,
    _safe_float,
)

logger = get_logger(__name__)


def analyze_famous_seats(seats_df: pd.DataFrame) -> dict:
    """
    分析知名游资动向（基于营业部买卖明细）

    Args:
        seats_df: lhb_seats 数据

    Returns:
        dict: {nickname: {seat, style, win_rate, buys, sells}}
    """
    results = {}
    seat_col = _get_seat_col(seats_df)
    if seat_col is None:
        return results

    for keyword, info in FAMOUS_SEATS.items():
        mask = seats_df[seat_col].astype(str).str.contains(keyword, na=False)
        seat_df = seats_df[mask]

        if seat_df.empty:
            continue

        code_col = _get_code_col(seats_df)
        name_col = _get_name_col(seats_df)
        buys = []
        sells = []

        for _, row in seat_df.iterrows():
            code = row.get(code_col, "")
            name = row.get(name_col, "")
            buy_amt = _safe_float(row.get("买入金额", 0))
            sell_amt = _safe_float(row.get("卖出金额", 0))

            if buy_amt > 0:
                buys.append({"代码": code, "名称": name, "金额": buy_amt})
            if sell_amt > 0:
                sells.append({"代码": code, "名称": name, "金额": sell_amt})

        results[info["nickname"]] = {
            "seat": info["full_name"],
            "style": info["style"],
            "win_rate": info["win_rate"],
            "buys": sorted(buys, key=lambda x: x["金额"], reverse=True),
            "sells": sorted(sells, key=lambda x: x["金额"], reverse=True),
        }

    return results


def analyze_institutions(seats_df: pd.DataFrame) -> pd.DataFrame:
    """
    分析机构专用席位的买卖情况

    Args:
        seats_df: lhb_seats 数据

    Returns:
        DataFrame: 按股票汇总的机构净买入
    """
    seat_col = _get_seat_col(seats_df)
    if seat_col is None:
        return pd.DataFrame()

    inst_df = seats_df[seats_df[seat_col].astype(str).str.contains("机构专用", na=False)]
    if inst_df.empty:
        return pd.DataFrame()

    code_col = _get_code_col(seats_df)
    name_col = _get_name_col(seats_df)

    grouped = inst_df.groupby([code_col, name_col], group_keys=False).apply(
        lambda g: pd.Series({
            "买入金额": _safe_float(g["买入金额"].sum()),
            "卖出金额": _safe_float(g["卖出金额"].sum()),
        }),
        include_groups=False,
    ).reset_index()

    grouped["机构净买入"] = grouped["买入金额"] - grouped["卖出金额"]
    grouped = grouped.sort_values("机构净买入", ascending=False)
    return grouped


def calculate_net_ratio(detail_df: pd.DataFrame) -> pd.DataFrame:
    """
    计算每只股票的主力净买入占比（基于个股详情数据）

    Args:
        detail_df: lhb_detail 数据

    Returns:
        DataFrame: 按净买入占比排序
    """
    code_col = _get_code_col(detail_df)
    name_col = _get_name_col(detail_df)

    if "龙虎榜净买额" in detail_df.columns:
        result = detail_df[[code_col, name_col, "龙虎榜净买额", "龙虎榜买入额", "龙虎榜卖出额"]].copy()
        result["总成交额"] = result["龙虎榜买入额"] + result["龙虎榜卖出额"]
        result["净买入占比"] = (
            result["龙虎榜净买额"] / result["总成交额"].replace(0, 1) * 100
        ).round(2)
        return result.sort_values("净买入占比", ascending=False)

    return pd.DataFrame()


def generate_report(detail_df: pd.DataFrame, seats_df: pd.DataFrame = None, date_str: str = None):
    """
    生成龙虎榜分析报告

    Args:
        detail_df: 个股详情数据
        seats_df: 营业部明细数据（可选）
        date_str: 日期字符串
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'=' * 60}")
    print(f"  龙虎榜分析报告 | 日期: {date_str}")
    print(f"{'=' * 60}")

    # 一、知名游资动向（需要营业部明细）
    print(f"\n一、知名游资动向")
    print("-" * 45)
    if seats_df is not None and not seats_df.empty:
        famous = analyze_famous_seats(seats_df)
        if not famous:
            print("  今日无知名游资明显操作")
        else:
            for nickname, data in famous.items():
                print(f"\n  [{nickname}] {data['seat'][:25]}...")
                print(f"  风格: {data['style']}")
                print(f"  历史胜率: {data['win_rate'] * 100:.0f}%")
                if data["buys"]:
                    print(f"  买入:")
                    for b in data["buys"][:3]:
                        print(f"    - {b['代码']} {b['名称']} ({b['金额'] / 1e4:.0f}万)")
                if data["sells"]:
                    print(f"  卖出:")
                    for s in data["sells"][:3]:
                        print(f"    - {s['代码']} {s['名称']} ({s['金额'] / 1e4:.0f}万)")
    else:
        print("  未获取营业部明细，跳过游资分析")
        print("  提示: 运行 python -m src.main fetch 获取完整数据")

    # 二、机构专用席位
    print(f"\n二、机构专用席位")
    print("-" * 45)
    if seats_df is not None and not seats_df.empty:
        inst = analyze_institutions(seats_df)
        if inst.empty:
            print("  今日无机构专用席位数据")
        else:
            print("  机构净买入 Top 5:")
            for _, row in inst.head(5).iterrows():
                print(
                    f"    {row.iloc[0]} {row.iloc[1]} - "
                    f"净买入 {row['机构净买入'] / 1e4:.0f}万"
                )
    else:
        print("  未获取营业部明细，跳过机构分析")

    # 三、净买入占比排行
    print(f"\n三、主力净买入占比 Top 10")
    print("-" * 45)
    ratio = calculate_net_ratio(detail_df)
    if ratio.empty:
        print("  无净买额数据")
    else:
        for _, row in ratio.head(10).iterrows():
            print(
                f"  {row.iloc[0]} {row.iloc[1]} - "
                f"净买入占比 {row['净买入占比']:.1f}% "
                f"(净买额 {row['龙虎榜净买额'] / 1e4:.0f}万)"
            )

    print(f"\n{'=' * 60}\n")


def run(date_str: str = None):
    """一键执行分析"""
    # 加载个股详情
    detail_df, loaded_date = load_latest_data("lhb_detail")

    # 尝试加载营业部明细
    try:
        seats_df, _ = load_latest_data("lhb_seats")
    except FileNotFoundError:
        seats_df = None

    generate_report(detail_df, seats_df, date_str or loaded_date)


if __name__ == "__main__":
    run()
