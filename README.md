# Trade Radar and Listing (结汇汇率预警、外贸情报与高转化发品 Skill)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills Standard](https://img.shields.io/badge/Standard-AgentSkills.io-blue)](https://agentskills.io)
[![Multi-Agent Ready](https://img.shields.io/badge/Multi--Agent-Ready-green.svg)]()

> 集“外贸外部宏观情报雷达（实时结汇汇率涨跌精算 + 重点出口国重大外贸事件过滤）”与“内部高转化发品引擎（B2B 搜索词矩阵 + 买家决策七屏详情结构）”于一体的外贸增长 Agent Skill。

---

## 核心功能

- **结汇汇率涨跌监测与毛利安全垫预警**：结合实时获取的最新汇率与报价基准汇率，调用确定性脚本精算汇兑损益对毛利率的侵蚀幅度，自动判断是否需要收紧报价有效期或按建议系数上调外币报价。
- **重点出口国高价值外贸事件精准过滤**：严格聚焦关税反倾销、港口罢工拥堵、清关与认证新规、汇率剧震、重要节假日备货潮五大事件，剔除无关娱乐社会噪音，并配套“业务员今日借势关怀/催单话术”。
- **B2B 平台与独立站高转化发品引擎**：生成分层关键词矩阵（核心大词 + B 端采购意图词 + 材质规格词）、3 组防违规高点击标题，以及直击专业买家的七屏详情页结构文案。

---

## 目录结构

```text
trade-radar-and-listing/
├── SKILL.md                             # Skill 核心指令与情报/发品流
├── README.md                            # 说明文档
├── LICENSE                              # MIT 开源协议
├── references/
│   └── macro-event-and-listing-guide.md # 外贸事件筛选标准与B2B高转化发品指南
└── scripts/
    └── fx_quote_guard.py                # 结汇汇率走势记录与毛利安全垫测算脚本
```

---

## 快速安装

### 方式一：通过 Skills CLI 安装

```bash
npx skills add cnproduct/trade-radar-and-listing -g -y
```

### 方式二：本地目录直接挂载

```bash
git clone https://github.com/cnproduct/trade-radar-and-listing.git ~/.agents/skills/trade-radar-and-listing
```

---

## 依赖与脚本示例

- **运行环境**：`Python 3.9+`（仅依赖 Python 标准库）

```bash
# 记录当日结汇汇率并测算报价毛利安全垫
python3 scripts/fx_quote_guard.py check \
  --pair "USD/CNY" \
  --current-rate 7.12 \
  --baseline-rate 7.25 \
  --gross-margin 0.15 \
  --alert-threshold-pct 1.0 \
  --history-file ./fx_history.csv \
  --markdown
```
