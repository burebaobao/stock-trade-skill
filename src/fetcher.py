"""
龙虎榜数据获取模块

通过 AKShare 获取 A 股龙虎榜数据，清洗后保存为 CSV。

数据来源：
- stock_lhb_detail_em: 东方财富龙虎榜个股上榜详情
- stock_lhb_stock_detail_em: 东方财富营业部买卖明细
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

from src.config import DATA_DIR
from src.logger import get_logger, retry
from src.utils import save_data

logger = get_logger(__name__)


def _find_latest_trade_date() -> str:
    """
    通过范围查询找到最新有数据的交易日

    Returns:
        日期字符串 YYYYMMDD
    """
    today = datetime.now()
    # 向前查最近30天的数据
    start = (today - timedelta(days=30)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    try:
        df = ak.stock_lhb_detail_em(start_date=start, end_date=end)
        if df is None or df.empty:
            # 如果近期无数据，扩大范围到最近180天
            start = (today - timedelta(days=180)).strftime("%Y%m%d")
            df = ak.stock_lhb_detail_em(start_date=start, end_date=end)
        if df is not None and not df.empty and "上榜日" in df.columns:
            dates = sorted(df["上榜日"].unique())
            latest = dates[-1]
            if isinstance(latest, str):
                date_str = latest.replace("-", "")
            else:
                date_str = latest.strftime("%Y%m%d")
            logger.info(f"最新可用交易日: {date_str}")
            return date_str
    except Exception as e:
        logger.warning(f"查找最新交易日失败: {e}")

    # 回退：取最近一个工作日
    d = today
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


@retry(max_attempts=3, delay=2, logger=logger)
def fetch_lhb_detail(date_str: str = None) -> pd.DataFrame:
    """
    获取龙虎榜个股上榜详情（东方财富）

    列包含：代码、名称、上榜日、收盘价、涨跌幅、龙虎榜净买额、
    龙虎榜买入额、龙虎榜卖出额、上榜原因 等。

    Args:
        date_str: 日期 YYYYMMDD，默认最近交易日

    Returns:
        DataFrame
    """
    if date_str is None:
        date_str = _find_latest_trade_date()
    else:
        date_str = str(date_str).replace("-", "")

    # 用范围查询（前后1天）避免单日空数据导致失败
    d = datetime.strptime(date_str, "%Y%m%d")
    start = (d - timedelta(days=1)).strftime("%Y%m%d")
    end = (d + timedelta(days=1)).strftime("%Y%m%d")

    df = ak.stock_lhb_detail_em(start_date=start, end_date=end)
    if df is None or df.empty:
        logger.warning(f"{date_str} 附近无龙虎榜数据")
        return pd.DataFrame()

    df.columns = [c.strip() for c in df.columns]

    # 过滤到目标日期
    if "上榜日" in df.columns:
        target_dates = [date_str, d.strftime("%Y-%m-%d")]
        mask = df["上榜日"].astype(str).str.replace("-", "").isin(
            [x.replace("-", "") for x in target_dates]
        )
        df = df[mask].reset_index(drop=True)

    if df.empty:
        logger.warning(f"{date_str} 无龙虎榜数据")
        return pd.DataFrame()

    logger.info(f"成功获取龙虎榜详情 ({date_str}): {len(df)} 条记录")
    return df


@retry(max_attempts=3, delay=2, logger=logger)
def fetch_lhb_seats(date_str: str = None) -> pd.DataFrame:
    """
    获取上榜股票的营业部买卖明细

    对每只上榜股票，分别获取买入和卖出营业部数据，合并为一张表。

    Args:
        date_str: 日期 YYYYMMDD

    Returns:
        DataFrame，列：代码、名称、营业部名称、买入金额、卖出金额、净额、类型
    """
    if date_str is None:
        date_str = _find_latest_trade_date()
    else:
        date_str = str(date_str).replace("-", "")

    # 先获取当日上榜股票列表
    detail_df = fetch_lhb_detail(date_str)
    if detail_df.empty:
        return pd.DataFrame()

    all_seats = []

    for _, row in detail_df.iterrows():
        code = str(row.get("代码", "")).zfill(6)
        name = row.get("名称", "")

        for flag in ["买入", "卖出"]:
            try:
                seat_df = ak.stock_lhb_stock_detail_em(
                    symbol=code, date=date_str, flag=flag
                )
                if seat_df is not None and not seat_df.empty:
                    seat_df.columns = [c.strip() for c in seat_df.columns]
                    seat_df["代码"] = code
                    seat_df["名称"] = name
                    all_seats.append(seat_df)
            except Exception as e:
                logger.debug(f"获取 {code} {flag} 营业部数据失败: {e}")
                continue

    if not all_seats:
        return pd.DataFrame()

    result = pd.concat(all_seats, ignore_index=True)
    logger.info(f"成功获取营业部明细: {len(result)} 条记录")
    return result


def print_summary(df: pd.DataFrame, date_str: str):
    """打印数据摘要"""
    if df.empty:
        print("[提示] 无数据可展示")
        return

    print(f"\n{'=' * 60}")
    print(f"  龙虎榜数据摘要 | 日期: {date_str}")
    print(f"{'=' * 60}")

    code_col = "代码" if "代码" in df.columns else df.columns[0]
    name_col = "名称" if "名称" in df.columns else df.columns[1]
    stock_count = df[code_col].nunique()

    print(f"  上榜股票数: {stock_count}")
    print(f"  数据总行数: {len(df)}")

    # 如果有净买额列，统计
    if "龙虎榜净买额" in df.columns:
        total_net = df["龙虎榜净买额"].sum()
        print(f"  总净买额: {total_net / 1e8:.2f} 亿")

    print(f"{'=' * 60}\n")

    # 显示核心列
    show_cols = [c for c in [code_col, name_col, "收盘价", "涨跌幅", "龙虎榜净买额", "上榜原因"] if c in df.columns]
    if show_cols:
        print(df[show_cols].head(10).to_string(index=False))
    else:
        print(df.head(10).to_string(index=False))
    print()


def run(date_str: str = None):
    """
    一键执行：获取个股详情 + 营业部买卖明细

    Args:
        date_str: 日期 YYYYMMDD，默认最近交易日
    """
    if date_str is None:
        date_str = _find_latest_trade_date()
    else:
        date_str = str(date_str).replace("-", "")
    logger.info(f"正在获取 {date_str} 龙虎榜数据...")

    # 获取个股详情
    df_detail = fetch_lhb_detail(date_str)
    if not df_detail.empty:
        save_data(df_detail, date_str, prefix="lhb_detail")
        print_summary(df_detail, date_str)

    # 获取营业部买卖明细
    logger.info("正在获取营业部买卖明细...")
    df_seats = fetch_lhb_seats(date_str)
    if not df_seats.empty:
        save_data(df_seats, date_str, prefix="lhb_seats")
        print(f"\n营业部买卖明细: {len(df_seats)} 条")

    if df_detail.empty and df_seats.empty:
        logger.warning("未获取到任何数据，可能是非交易日或接口变动")

    return df_detail, df_seats


if __name__ == "__main__":
    run()
