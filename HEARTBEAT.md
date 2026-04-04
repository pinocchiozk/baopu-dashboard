# HEARTBEAT.md - 定时检查任务

## 📊 A股市场情绪监控（交易时段）

**执行时间：** 交易日 9:15-11:30、13:00-15:00，每 30 分钟检查一次

**检查逻辑：**
1. 当前时间是否在交易时段（9:15-15:00）？
2. 距离上次采集是否≥30 分钟？
3. 如果是 → 执行采集脚本
4. 如果否 → 跳过

**预警规则：**
| 情绪分数 | 状态 | 操作 | 推送 |
|---------|------|------|------|
| ≤25 分 | 🧊冰点 | 买点，龙头低吸 | ✅ |
| 26-74 分 | 📊正常 | 持仓待涨 | ❌ |
| ≥75 分 | 🔥过热 | 风险，减仓 | ✅ |

---

## 📋 开盘啦数据采集（核心任务）

### 盘后全量采集（每日 15:05 执行）

**执行脚本：** `/Users/macclaw/.openclaw/workspace/scripts/kaipanla_full_collection.sh`

**采集数据源：**
1. 市场情绪（350, 220）→ 情绪分数、连板梯队
2. 涨停表现二板（343, 1146）→ 二连板个股
3. 涨停表现更高 → 高位板个股
4. 行情-板块（270, 1520）→ 板块强度排名
5. 打板（336, 130）→ 涨跌停明细

**数据落地：**
- 截图：`/tmp/kaipanla/daily/{YYYYMMDD}/`
- 数据库：`/workspace/database/kaipanla.db`
- 报告：`/workspace/daily_{YYYYMMDD}/盘后报告.md`

### 盘中监控采集（交易日 9:30-14:45，每 30 分钟）

**采集内容：**
- 市场情绪快照（情绪分数、涨停/跌停数）
- 连板梯队变化
- 板块强度排名

---

## 📈 情绪K线图自动更新

**执行时间：** 每天 15:05（收盘后 5 分钟）

**执行脚本：** `/Users/macclaw/.openclaw/workspace/scripts/update_kline_data.sh`

**功能：**
1. 从 `sentiment_daily_k.csv` 读取最新日 K 线数据
2. 追加到 `/workspace/emotion-kline/emotion-data.json`
3. 记录日志到 `/tmp/kaipanla/kline_update.log`

---

## 📋 复盘啦数据采集

**执行时间：** 每日 15:10 执行

**执行脚本：** `/Users/macclaw/.openclaw/workspace/scripts/fupan_collector.sh`

**入口坐标：** (440, 220) - 首页第一行第三个图标

**数据价值：**
- 当日市场热点追踪
- 主力异动方向分析
- 板块轮动节奏把握

---

## 🔧 自动化部署（Cron）

```bash
# 盘后全量采集 - 每日15:05
5 15 * * 1-5 /Users/macclaw/.openclaw/workspace/scripts/kaipanla_full_collection.sh >> /tmp/kaipanla/daily_collection.log 2>&1

# 数据导入数据库 - 每日15:15
15 15 * * 1-5 cd /Users/macclaw/.openclaw/workspace/database && python import_data.py >> /tmp/kaipanla/import.log 2>&1
```

---

## 📊 策略信号推送

**执行时间：** 每日 15:30（盘后分析完成后）

**执行内容：**
1. 运行 `strategy/sentiment_strategy.py` 获取每日信号
2. 生成策略信号报告
3. 推送至飞书

**信号内容：**
- 情绪分数 + 连板率
- 推荐仓位
- 市场状态描述

---

## 📁 数据存储结构

```
/tmp/kaipanla/
├── daily/
│   └── {YYYYMMDD}/
│       ├── 01_市场情绪_首页.png
│       ├── 02_市场情绪_中段.png
│       ├── 03_涨停表现_二板.png
│       ├── 04_涨停表现_更高.png
│       ├── 05_行情_板块.png
│       └── 06_打板.png
├── sentiment_data.csv
├── sentiment_daily_k.csv
└── monitor.log

/workspace/
├── database/
│   └── kaipanla.db
├── strategy/
│   ├── sentiment_strategy.py
│   └── backtest.py
└── daily_{YYYYMMDD}/
    └── 盘后报告_{YYYYMMDD}.md
```

---

*最后更新：2026-04-04*
