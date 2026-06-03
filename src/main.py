"""
股票交易 Skill — 统一入口

用法:
    python -m src.main fetch              # 获取龙虎榜数据
    python -m src.main fetch 20260603     # 获取指定日期
    python -m src.main analyze            # 分析主力动向
    python -m src.main signal            # 生成交易信号
    python -m src.main signal --days 7    # 用最近7天数据生成信号
    python -m src.main backtest           # 回测验证
    python -m src.main all                # 一键执行全流程
"""
import sys
import argparse

from src.fetcher import run as run_fetch
from src.analyzer import run as run_analyze
from src.signal import run as run_signal
from src.backtest import run as run_backtest


def main():
    parser = argparse.ArgumentParser(
        description="股票交易 Skill — 龙虎榜数据分析与交易信号生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.main fetch              获取今日龙虎榜数据
  python -m src.main fetch 20260603     获取指定日期数据
  python -m src.main analyze            分析主力动向
  python -m src.main signal             生成交易信号
  python -m src.main backtest           回测验证
  python -m src.main all                全流程执行
        """,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    # fetch
    p_fetch = sub.add_parser("fetch", help="获取龙虎榜数据")
    p_fetch.add_argument("date", nargs="?", default=None, help="日期 YYYYMMDD")

    # analyze
    sub.add_parser("analyze", help="分析主力动向")

    # signal
    p_signal = sub.add_parser("signal", help="生成交易信号")
    p_signal.add_argument("--days", type=int, default=5, help="使用最近N天数据")

    # backtest
    p_backtest = sub.add_parser("backtest", help="回测验证")
    p_backtest.add_argument("--days", type=int, default=7, help="回测天数")

    # all
    sub.add_parser("all", help="全流程执行（获取→分析→信号）")

    args = parser.parse_args()

    if args.command == "fetch":
        run_fetch(args.date)

    elif args.command == "analyze":
        run_analyze()

    elif args.command == "signal":
        run_signal(days=args.days)

    elif args.command == "backtest":
        run_backtest(days=args.days)

    elif args.command == "all":
        print("\n" + "=" * 60)
        print("  全流程执行: 获取 → 分析 → 信号")
        print("=" * 60 + "\n")

        print(">>> Step 1: 获取数据")
        run_fetch()

        print("\n>>> Step 2: 分析主力动向")
        run_analyze()

        print(">>> Step 3: 生成交易信号")
        run_signal(days=5)

        print("\n✅ 全流程执行完成！")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
