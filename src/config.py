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
SIGNAL_THRESHOLD = 30       # 得分 >= 此值才推荐
TOP_N = 5                   # 每日推荐 Top N

# 交易参数
STOP_LOSS = -0.05           # 止损 -5%
TAKE_PROFIT = 0.10          # 止盈 +10%
HOLD_DAYS = (1, 3)          # 持有周期 1-3 天

# 知名游资席位库（使用简化关键字匹配，包含多个别名）
FAMOUS_SEATS = {
    # 章盟主（顶级游资，大票方向标）
    "江苏路": {"nickname": "章盟主", "win_rate": 0.65},
    # 赵老哥（短线打板，八年万倍）
    "绍兴": {"nickname": "赵老哥", "win_rate": 0.63},
    # 方新侠（大开大合，趋势标的）
    "朱雀大街": {"nickname": "方新侠", "win_rate": 0.62},
    "陕西分公司": {"nickname": "方新侠", "win_rate": 0.62},
    # 炒股养家（通道优势，一字板专家）
    "宛平南路": {"nickname": "炒股养家", "win_rate": 0.61},
    "沧海路": {"nickname": "炒股养家", "win_rate": 0.61},
    # 作手新一（新生代一线）
    "太平南路": {"nickname": "作手新一", "win_rate": 0.60},
    # 小鳄鱼（新生代90后）
    "大钟亭": {"nickname": "小鳄鱼", "win_rate": 0.59},
    "世纪大道": {"nickname": "小鳄鱼", "win_rate": 0.59},
    # 孙哥（题材主升浪）
    "溧阳路": {"nickname": "孙哥", "win_rate": 0.58},
    "庆春路": {"nickname": "孙哥", "win_rate": 0.58},
    # 上塘路（一夜情+核按钮，需谨慎）
    "上塘路": {"nickname": "上塘路", "win_rate": 0.57},
    # 佛山系（翘跌停反核）
    "绿景路": {"nickname": "佛山系", "win_rate": 0.56},
    "祖庙路": {"nickname": "佛山系", "win_rate": 0.56},
    "季华路": {"nickname": "佛山系", "win_rate": 0.56},
    # 陈小群（主动引导）
    "金马路": {"nickname": "陈小群", "win_rate": 0.60},
    # 交易猿（满仓满融激进）
    "东丽开发区二纬路": {"nickname": "交易猿", "win_rate": 0.58},
    # 余哥（机构游资合力）
    "解放南路": {"nickname": "余哥", "win_rate": 0.57},
    # 宁波桑田路（活跃连板）
    "桑田路": {"nickname": "宁波桑田路", "win_rate": 0.55},
    # 湖州劳动路（题材潜伏）
    "隐秀路": {"nickname": "湖州劳动路", "win_rate": 0.56},
    # 金田路（高位接力）
    "金田路": {"nickname": "金田路", "win_rate": 0.55},
    # 益田路（顶级情绪资金，深圳帮）
    "益田路": {"nickname": "益田路", "win_rate": 0.58},
    # 西湖国贸（价投型资金）
    "西湖国贸": {"nickname": "西湖国贸", "win_rate": 0.60},
    # 上海超短帮（小波段+基本面）
    "新闸路": {"nickname": "上海超短帮", "win_rate": 0.59},
    "银城中路": {"nickname": "上海超短帮", "win_rate": 0.59},
    # 陆家嘴（上海机构集中地）
    "陆家嘴": {"nickname": "陆家嘴", "win_rate": 0.55},
    # 一瞬流光（三年百倍）
    "水月亭": {"nickname": "一瞬流光", "win_rate": 0.58},
}
