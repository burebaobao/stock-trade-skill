"""
公共工具模块
"""
import pandas as pd
import glob
from typing import Optional, Tuple, List
from pathlib import Path
from datetime import datetime, timedelta

from src.config import DATA_DIR
from src.logger import get_logger

logger = get_logger()


def _safe_float(val) -> float:
    """安全转换为 float"""
    try:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            return float(val.replace(",", "").replace(" ", ""))
        return 0.0
    except (ValueError, TypeError):
        return 0.0


def _get_seat_col(df: pd.DataFrame) -> Optional[str]:
    """自动识别营业部名称列"""
    for c in ["交易营业部名称", "营业部名称", "营业部"]:
        if c in df.columns:
            return c
    return None


def _get_code_col(df: pd.DataFrame) -> str:
    """自动识别代码列"""
    for c in ["代码", "股票代码"]:
        if c in df.columns:
            return c
    return df.columns[0]


def _get_name_col(df: pd.DataFrame) -> Optional[str]:
    """自动识别名称列"""
    for c in ["名称", "股票名称"]:
        if c in df.columns:
            return c
    return df.columns[1] if len(df.columns) > 1 else None


def load_latest_data(prefix: str = "lhb_detail") -> Tuple[pd.DataFrame, str]:
    """
    加载最新日期的数据文件
    
    Args:
        prefix: 文件名前缀 (lhb_detail 或 lhb_seats)
    
    Returns:
        (DataFrame, date_str)
    """
    pattern = str(DATA_DIR / f"{prefix}_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(
            f"未找到 {prefix} 数据文件，请先运行: python -m src.main fetch"
        )
    latest = files[-1]
    date_str = latest.split("_")[-1].replace(".csv", "")
    logger.info(f"加载数据文件: {latest} (日期: {date_str})")
    return pd.read_csv(latest, encoding="utf-8-sig"), date_str


def load_multi_day_data(prefix: str = "lhb_detail", days: int = 5) -> pd.DataFrame:
    """
    加载最近 N 天的数据
    
    Args:
        prefix: 文件名前缀
        days: 天数
    
    Returns:
        合并后的 DataFrame
    """
    pattern = str(DATA_DIR / f"{prefix}_*.csv")
    files = sorted(glob.glob(pattern))[-days:]
    if not files:
        raise FileNotFoundError("未找到数据文件")

    dfs = []
    for f in files:
        df = pd.read_csv(f, encoding="utf-8-sig")
        df["date"] = f.split("_")[-1].replace(".csv", "")
        dfs.append(df)

    result = pd.concat(dfs, ignore_index=True)
    logger.info(f"加载 {len(files)} 天数据，共 {len(result)} 条记录")
    return result


def check_consecutive_listed(code: str, multi_day_data: pd.DataFrame, code_col: str) -> bool:
    """
    检查股票是否连续上榜
    
    Args:
        code: 股票代码
        multi_day_data: 多日数据
        code_col: 代码列名
    
    Returns:
        是否连续上榜
    """
    recent_dates = sorted(multi_day_data['date'].unique())[-2:]
    if len(recent_dates) < 2:
        return False
    
    day1_codes = set(multi_day_data[multi_day_data['date'] == recent_dates[0]][code_col])
    day2_codes = set(multi_day_data[multi_day_data['date'] == recent_dates[1]][code_col])
    
    return code in day1_codes and code in day2_codes


def save_data(df: pd.DataFrame, date_str: str, prefix: str = "lhb") -> str:
    """
    保存 DataFrame 到 CSV
    
    Args:
        df: 数据
        date_str: 日期 YYYYMMDD
        prefix: 文件名前缀
    
    Returns:
        保存的文件路径
    """
    filepath = DATA_DIR / f"{prefix}_{date_str}.csv"
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    logger.info(f"保存数据到: {filepath}")
    return str(filepath)


def get_recent_trade_date(date_str: str = None) -> str:
    """
    获取最近交易日日期字符串 (YYYYMMDD)
    
    Args:
        date_str: 指定日期，为空则自动取最近交易日
    
    Returns:
        日期字符串，格式 YYYYMMDD
    """
    if date_str:
        return date_str.replace("-", "")

    today = datetime.now()
    weekday = today.weekday()
    if weekday >= 5:
        today = today - timedelta(days=weekday - 4)
    return today.strftime("%Y%m%d")
