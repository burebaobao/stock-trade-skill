"""
全局配置模块
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# 信号评分权重
SCORING = {
    "famous_buy": 20,       # 知名游资买入
    "institution_buy": 15,  # 机构净买入
    "net_ratio_high": 10,    # 净买入占比 > 10%
    "consecutive": 10,       # 连续上榜
    "high_win_rate": 5,      # 高胜率席位买入
}

# 信号阈值
SIGNAL_THRESHOLD = 50       # 得分 >= 此值才推荐
TOP_N = 5                   # 每日推荐 Top N

# 交易参数
STOP_LOSS = -0.05           # 止损 -5%
TAKE_PROFIT = 0.10          # 止盈 +10%
HOLD_DAYS = (1, 3)          # 持有周期 1-3 天

# 知名游资席位库
FAMOUS_SEATS = {
    "国泰君安上海江苏路": {
        "full_name": "国泰君安证券股份有限公司上海江苏路证券营业部",
        "nickname": "章盟主",
        "style": "偏好大盘蓝筹，持股 1-3 天",
        "win_rate": 0.65,
    },
    "中信上海溧阳路": {
        "full_name": "中信证券股份有限公司上海溧阳路证券营业部",
        "nickname": "溧阳路",
        "style": "擅长题材炒作，短线操作",
        "win_rate": 0.58,
    },
    "华泰深圳益田路": {
        "full_name": "华泰证券股份有限公司深圳益田路荣超商务中心证券营业部",
        "nickname": "荣超",
        "style": "专做龙头股，打板高手",
        "win_rate": 0.62,
    },
    "招商深圳深南东路": {
        "full_name": "招商证券股份有限公司深圳深南东路证券营业部",
        "nickname": "深南东",
        "style": "稳健型，偏好趋势股",
        "win_rate": 0.60,
    },
    "银河绍兴": {
        "full_name": "中国银河证券股份有限公司绍兴证券营业部",
        "nickname": "绍兴帮",
        "style": "擅长次新股操作",
        "win_rate": 0.55,
    },
    "国金上海互联网": {
        "full_name": "国金证券股份有限公司上海互联网证券分公司",
        "nickname": "上海互联网",
        "style": "量化交易为主",
        "win_rate": 0.57,
    },
}
