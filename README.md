# 股票交易 Skill — 龙虎榜数据分析与交易信号

基于 A 股龙虎榜数据，分析主力动向，生成次日买卖推荐信号。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 获取龙虎榜数据
python -m src.main fetch

# 3. 分析主力动向
python -m src.main analyze

# 4. 生成交易信号
python -m src.main signal

# 5. 回测验证
python -m src.main backtest

# 或者一键执行全流程
python -m src.main all
```

## 命令说明

| 命令 | 说明 | 示例 |
|------|------|------|
| `fetch [日期]` | 获取龙虎榜数据 | `python -m src.main fetch 20260603` |
| `analyze` | 分析主力动向 | `python -m src.main analyze` |
| `signal --days N` | 生成交易信号（默认 5 天） | `python -m src.main signal --days 7` |
| `backtest --days N` | 回测验证（默认 7 天） | `python -m src.main backtest --days 10` |
| `all` | 全流程执行 | `python -m src.main all` |

## 项目结构

```
stock-trade-skill/
├── .claude/
│   ├── skills/
│   │   ├── stock-data.md       # 数据获取 Skill
│   │   ├── stock-analysis.md    # 分析 Skill
│   │   └── stock-signal.md      # 信号 Skill
│   └── CLAUDE.md                # Claude Code 项目记忆
├── src/
│   ├── __init__.py
│   ├── config.py                # 全局配置（评分权重、游资席位库）
│   ├── fetcher.py               # 数据获取模块
│   ├── analyzer.py              # 分析模块
│   ├── signal.py                # 信号生成模块
│   ├── backtest.py              # 回测模块
│   └── main.py                  # 统一入口
├── data/                        # 数据存储目录
├── tests/                       # 测试目录
├── requirements.txt
└── README.md
```

## 信号评分规则

| 维度 | 分值 | 说明 |
|------|------|------|
| 知名游资买入 | +20 | 章盟主/溧阳路/荣超等知名游资席位买入 |
| 机构净买入 | +15 | 机构专用席位整体净买入为正 |
| 净买入占比 > 10% | +10 | 主力资金净买入占总成交额比例高 |
| 连续上榜 | +10 | 连续 2 天以上登上龙虎榜 |
| 高胜率席位 | +5 | 历史胜率 > 60% 的游资席位买入 |

推荐阈值: **>= 50 分**，每日取 **Top 5**。

## 知名游资席位

| 昵称 | 席位 | 风格 | 历史胜率 |
|------|------|------|---------|
| 章盟主 | 国泰君安上海江苏路 | 偏好大盘蓝筹，1-3 天 | 65% |
| 溧阳路 | 中信上海溧阳路 | 题材炒作，短线 | 58% |
| 荣超 | 华泰深圳益田路 | 龙头股打板 | 62% |
| 深南东 | 招商深圳深南东路 | 稳健趋势股 | 60% |
| 绍兴帮 | 银河绍兴 | 次新股 | 55% |
| 上海互联网 | 国金上海互联网 | 量化交易 | 57% |

## 配合 Claude Code 使用

在项目目录下启动 Claude Code，Skill 会自动加载：

```bash
claude
"获取今天的龙虎榜"     # → 自动触发 stock-data Skill
"分析主力动向"         # → 自动触发 stock-analysis Skill
"明天买什么"           # → 自动触发 stock-signal Skill
```

## 免责声明

本工具仅供学习研究使用，不构成任何投资建议。股市有风险，投资需谨慎。
