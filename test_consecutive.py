"""
测试连续上榜功能
"""
import pandas as pd
from src.signal import calculate_score
from src.utils import load_multi_day_data, load_latest_data

print("=== 测试连续上榜功能 ===\n")

# 加载数据
multi_day_df = load_multi_day_data("lhb_detail", days=2)
latest_df, date_str = load_latest_data("lhb_detail")

print(f"最新日期: {date_str}")
print(f"多日数据行数: {len(multi_day_df)}")
print(f"多日日期: {sorted(multi_day_df['date'].unique())}\n")

# 计算分数
scores = calculate_score(latest_df, multi_day_df=multi_day_df)

print("=== 评分结果 ===")
print(scores[["代码", "名称", "净买入占比", "score", "reasons"]])
print()

# 检查是否有连续上榜的股票
code_col = "代码"
consecutive_stocks = scores[scores["reasons"].str.contains("连续上榜", na=False)]

if not consecutive_stocks.empty:
    print("=== 连续上榜股票 ===")
    print(consecutive_stocks[["代码", "名称", "score", "reasons"]])
else:
    print("没有检测到连续上榜股票")
    
print("\n测试完成!")
