"""
回测验证模块

用历史龙虎榜数据验证交易策略的有效性。
"""
import pandas as pd
import glob
from datetime import datetime, timedelta

from src.config import DATA_DIR, SIGNAL_THRESHOLD, TOP_N
from src.signal import calculate_score


def load_history(days: int = 7) -> pd.DataFrame:
    """加载最近 N 天数据"""
    pattern = str(DATA_DIR / "lhb_detail_*.csv")
    files = sorted(glob.glob(pattern))[-days:]
    if len(files) < 2:
        raise ValueError("回测至少需要 2 天数据，请先多次运行 fetcher")

    dfs = []
    for f in files:
        df = pd.read_csv(f, encoding="utf-8-sig")
        df["date"] = f.split("_")[-1].replace(".csv", "")
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def backtest(df: pd.DataFrame):
    """
    简化回测：统计每日推荐股票的信号强度分布

    完整回测需要接入行情数据（次日涨跌幅），这里输出信号统计。

    Args:
        df: 多日龙虎榜数据
    """
    dates = sorted(df["date"].unique())
    print(f"\n{'=' * 60}")
    print(f"  策略回测报告")
    print(f"  数据范围: {dates[0]} ~ {dates[-1]} ({len(dates)} 个交易日)")
    print(f"{'=' * 60}\n")

    total_recommendations = 0
    total_qualified = 0
    score_distribution = {"high": 0, "medium": 0, "low": 0}

    for date in dates:
        day_df = df[df["date"] == date]
        scores = calculate_score(day_df)
        qualified = scores[scores["score"] >= SIGNAL_THRESHOLD]

        total_recommendations += len(scores)
        total_qualified += len(qualified)

        for _, row in scores.iterrows():
            if row["score"] >= 70:
                score_distribution["high"] += 1
            elif row["score"] >= 40:
                score_distribution["medium"] += 1
            else:
                score_distribution["low"] += 1

    # 输出统计
    print("【信号统计】")
    print("-" * 45)
    print(f"  分析股票总数: {total_recommendations}")
    print(f"  达到推荐阈值 (>= {SIGNAL_THRESHOLD} 分): {total_qualified}")
    print(f"  日均推荐数: {total_qualified / len(dates):.1f}")
    print()

    print("【信号强度分布】")
    print("-" * 45)
    print(f"  高信号 (>= 70 分): {score_distribution['high']} 只")
    print(f"  中信号 (40-69 分): {score_distribution['medium']} 只")
    print(f"  低信号 (< 40 分): {score_distribution['low']} 只")
    print()

    print("【每日信号明细】")
    print("-" * 45)
    for date in dates:
        day_df = df[df["date"] == date]
        scores = calculate_score(day_df)
        top = scores[scores["score"] >= SIGNAL_THRESHOLD].head(TOP_N)
        if top.empty:
            print(f"  {date}: 无推荐信号")
        else:
            codes = "、".join(
                [f"{r.iloc[0]}({r['score']:.0f}分)" for _, r in top.iterrows()]
            )
            print(f"  {date}: {codes}")

    print(f"\n{'=' * 60}")
    print("  说明: 完整回测需接入次日行情数据计算实际涨跌幅")
    print("  建议: 接入 AKShare 的 stock_zh_a_hist 接口获取历史行情")
    print(f"{'=' * 60}\n")


def run(days: int = 7):
    """一键执行回测"""
    df = load_history(days=days)
    backtest(df)


if __name__ == "__main__":
    run()
