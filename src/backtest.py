"""
回测验证模块

用历史龙虎榜数据验证交易策略的有效性。
"""
import pandas as pd
from datetime import datetime, timedelta

from src.config import SIGNAL_THRESHOLD, TOP_N, STOP_LOSS, TAKE_PROFIT
from src.logger import get_logger, retry
from src.utils import load_multi_day_data, _get_code_col, _get_name_col
from src.signal import calculate_score

logger = get_logger(__name__)


@retry(max_attempts=2, delay=1, logger=logger)
def fetch_historical_price(code: str, date_str: str) -> dict:
    """
    获取指定日期的历史行情数据

    Args:
        code: 股票代码
        date_str: 日期字符串 (YYYYMMDD)

    Returns:
        包含开盘价、收盘价等信息的字典
    """
    try:
        import akshare as ak
        
        # 尝试获取历史行情
        # 将日期转换为 YYYY-MM-DD 格式
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        # 获取该日期附近的数据
        df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                start_date=date_str, end_date=date_str)
        
        if not df.empty:
            return {
                "open": df.iloc[0]["开盘"],
                "close": df.iloc[0]["收盘"],
                "high": df.iloc[0]["最高"],
                "low": df.iloc[0]["最低"],
                "change_pct": df.iloc[0]["涨跌幅"]
            }
    except Exception as e:
        logger.debug(f"获取 {code} {date_str} 行情失败: {e}")
    
    return None


def get_next_trading_date(date_str: str) -> str:
    """
    获取下一个交易日（简化版，只跳过周末）

    Args:
        date_str: 日期字符串 (YYYYMMDD)

    Returns:
        下一个交易日日期字符串
    """
    date = datetime.strptime(date_str, "%Y%m%d")
    next_date = date + timedelta(days=1)
    
    # 跳过周末
    while next_date.weekday() >= 5:
        next_date += timedelta(days=1)
    
    return next_date.strftime("%Y%m%d")


def backtest(df: pd.DataFrame):
    """
    完整回测：统计每日推荐股票的实际表现

    Args:
        df: 多日龙虎榜数据
    """
    dates = sorted(df["date"].unique())
    if len(dates) < 2:
        logger.warning("数据不足，无法进行完整回测")
        return

    print(f"\n{'=' * 60}")
    print(f"  策略回测报告")
    print(f"  数据范围: {dates[0]} ~ {dates[-1]} ({len(dates)} 个交易日)")
    print(f"{'=' * 60}\n")

    total_recommendations = 0
    total_qualified = 0
    score_distribution = {"high": 0, "medium": 0, "low": 0}
    performance_stats = {
        "total_trades": 0,
        "winning_trades": 0,
        "total_return": 0.0,
        "max_drawdown": 0.0
    }
    daily_returns = []
    trade_details = []

    # 分析每一天（除了最后一天，因为需要次日数据）
    for i, date in enumerate(dates[:-1]):
        day_df = df[df["date"] == date]
        scores = calculate_score(day_df)
        qualified = scores[scores["score"] >= SIGNAL_THRESHOLD]
        top = qualified.head(TOP_N)

        total_recommendations += len(scores)
        total_qualified += len(qualified)

        # 统计信号分布
        for _, row in scores.iterrows():
            if row["score"] >= 70:
                score_distribution["high"] += 1
            elif row["score"] >= 40:
                score_distribution["medium"] += 1
            else:
                score_distribution["low"] += 1

        # 回测表现
        next_date = get_next_trading_date(date)
        code_col = _get_code_col(day_df)
        name_col = _get_name_col(day_df)
        
        day_return = 0.0
        valid_trades = 0
        
        for _, row in top.iterrows():
            code = str(row[code_col]).zfill(6)
            name = row[name_col]
            score = row["score"]
            
            # 尝试获取次日行情
            price_data = fetch_historical_price(code, next_date)
            
            if price_data:
                # 简化策略：次日开盘买入，持有一天
                entry_price = price_data["open"]
                exit_price = price_data["close"]
                trade_return = (exit_price - entry_price) / entry_price * 100
                
                performance_stats["total_trades"] += 1
                valid_trades += 1
                day_return += trade_return
                
                if trade_return > 0:
                    performance_stats["winning_trades"] += 1
                
                performance_stats["total_return"] += trade_return
                
                trade_details.append({
                    "date": date,
                    "code": code,
                    "name": name,
                    "score": score,
                    "entry": entry_price,
                    "exit": exit_price,
                    "return": trade_return
                })

        if valid_trades > 0:
            daily_returns.append(day_return / valid_trades)

    # 输出统计
    print("【信号统计】")
    print("-" * 45)
    print(f"  分析股票总数: {total_recommendations}")
    print(f"  达到推荐阈值 (>= {SIGNAL_THRESHOLD} 分): {total_qualified}")
    print(f"  日均推荐数: {total_qualified / max(len(dates) - 1, 1):.1f}")
    print()

    print("【信号强度分布】")
    print("-" * 45)
    print(f"  高信号 (>= 70 分): {score_distribution['high']} 只")
    print(f"  中信号 (40-69 分): {score_distribution['medium']} 只")
    print(f"  低信号 (< 40 分): {score_distribution['low']} 只")
    print()

    print("【策略表现】")
    print("-" * 45)
    if performance_stats["total_trades"] > 0:
        win_rate = performance_stats["winning_trades"] / performance_stats["total_trades"] * 100
        avg_return = performance_stats["total_return"] / performance_stats["total_trades"]
        print(f"  总交易次数: {performance_stats['total_trades']}")
        print(f"  胜率: {win_rate:.1f}%")
        print(f"  平均单次收益: {avg_return:.2f}%")
        print(f"  总收益率: {performance_stats['total_return']:.2f}%")
        
        if daily_returns:
            import numpy as np
            print(f"  日均收益率: {np.mean(daily_returns):.2f}%")
            print(f"  收益波动率: {np.std(daily_returns):.2f}%")
    else:
        print("  暂无有效回测数据")
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
            code_col = _get_code_col(day_df)
            codes = "、".join(
                [f"{r[code_col]}({r['score']:.0f}分)" for _, r in top.iterrows()]
            )
            print(f"  {date}: {codes}")

    if trade_details:
        print()
        print("【交易明细】")
        print("-" * 45)
        print(f"{'日期':<10} {'代码':<8} {'名称':<10} {'得分':<6} {'收益':<8}")
        print("-" * 45)
        for trade in trade_details[-10:]:  # 只显示最近10笔
            print(f"{trade['date']:<10} {trade['code']:<8} {trade['name']:<10} "
                  f"{trade['score']:<6.0f} {trade['return']:+.2f}%")

    print(f"\n{'=' * 60}")
    print("  说明: 回测基于次日开盘买入收盘卖出的简化策略")
    print("  实际交易应考虑止损止盈和市场冲击成本")
    print(f"{'=' * 60}\n")


def run(days: int = 7):
    """一键执行回测"""
    df = load_multi_day_data("lhb_detail", days=days)
    backtest(df)


if __name__ == "__main__":
    run()
