"""
测试工具模块
"""
import pytest
import pandas as pd
from src.utils import _safe_float, _get_code_col, _get_name_col, check_consecutive_listed


def test_safe_float():
    """测试安全浮点数转换"""
    assert _safe_float(10.5) == 10.5
    assert _safe_float("10.5") == 10.5
    assert _safe_float("  10.5  ") == 10.5
    assert _safe_float("1,000.5") == 1000.5
    assert _safe_float("invalid") == 0.0
    assert _safe_float(None) == 0.0


def test_get_code_col():
    """测试获取代码列"""
    df = pd.DataFrame({"代码": ["000001", "000002"], "名称": ["平安银行", "万科A"]})
    assert _get_code_col(df) == "代码"
    
    df2 = pd.DataFrame({"股票代码": ["000001", "000002"], "名称": ["平安银行", "万科A"]})
    assert _get_code_col(df2) == "股票代码"
    
    df3 = pd.DataFrame({"col1": ["000001", "000002"], "col2": ["平安银行", "万科A"]})
    assert _get_code_col(df3) == "col1"


def test_get_name_col():
    """测试获取名称列"""
    df = pd.DataFrame({"代码": ["000001", "000002"], "名称": ["平安银行", "万科A"]})
    assert _get_name_col(df) == "名称"
    
    df2 = pd.DataFrame({"代码": ["000001", "000002"], "股票名称": ["平安银行", "万科A"]})
    assert _get_name_col(df2) == "股票名称"


def test_check_consecutive_listed():
    """测试连续上榜判断"""
    df = pd.DataFrame({
        "代码": ["000001", "000002", "000001", "000003"],
        "date": ["20240101", "20240101", "20240102", "20240102"]
    })
    
    assert check_consecutive_listed("000001", df, "代码") == True
    assert check_consecutive_listed("000002", df, "代码") == False
    assert check_consecutive_listed("000003", df, "代码") == False
    assert check_consecutive_listed("000004", df, "代码") == False
