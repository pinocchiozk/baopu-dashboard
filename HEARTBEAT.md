# HEARTBEAT.md - 定时检查任务

## 📊 A 股市场情绪监控（交易时段）

**执行时间：** 交易日 9:15-11:30、13:00-15:00，每 5 分钟检查一次（中午休市 11:30-13:00 不采集）

**采集时间点：**
- 9:15（竞价开盘）
- 9:20、9:25、9:30、9:35、9:40、9:45、9:50、9:55、10:00、10:05、10:10、10:15、10:20、10:25、10:30、10:35、10:40、10:45、10:50、10:55、11:00、11:05、11:10、11:15、11:20、11:25、11:30（上午）
- 13:00、13:05、13:10、13:15、13:20、13:25、13:30、13:35、13:40、13:45、13:50、13:55、14:00、14:05、14:10、14:15、14:20、14:25、14:30、14:35、14:40、14:45、14:50、14:55、15:00（下午，15:00 为收盘采集）

**检查逻辑：**
1. 当前时间是否在交易时段（9:15-15:00）？
2. 距离上次采集是否≥30 分钟？
3. 如果是 → 执行 `/Users/macclaw/.openclaw/workspace/scripts/sentiment_monitor.sh`
4. 如果否 → 跳过

**数据记录位置：**
- CSV：`/tmp/kaipanla/sentiment_data.csv`
- 日志：`/tmp/kaipanla/monitor.log`
- 日 K 线：`/tmp/kaipanla/sentiment_daily_k.csv`

**预警规则：**
| 情绪分数 | 状态 | 操作 | 推送 |
|---------|------|------|------|
| ≤25 分 | 🧊冰点 | 买点，龙头低吸 | ✅ |
| 26-74 分 | 📊正常 | 持仓待涨 | ❌ |
| ≥75 分 | 🔥过热 | 风险，减仓 | ✅ |

**日 K 线生成：**
- 每天 15:00 收盘后自动生成当日情绪 K 线
- 开盘分=9:15，收盘分=15:00，最高/最低=盘中极值
- 合并上午和下午数据，生成完整日 K 线记录

---

## 📈 情绪 K 线图自动更新

**执行时间：** 每天 15:05（收盘后 5 分钟）

**执行脚本：** `/Users/macclaw/.openclaw/workspace/scripts/update_kline_data.sh`

**功能：**
1. 从 `sentiment_daily_k.csv` 读取最新日 K 线数据
2. 追加到 `/workspace/emotion-kline/emotion-data.json`
3. 记录日志到 `/tmp/kaipanla/kline_update.log`

**部署方式：** launchd (`com.kaipanla.kline.update`)

**访问链接：** 需重新部署后更新

---

## 📋 复盘啦数据采集（新增）

**执行脚本：** `/Users/macclaw/.openclaw/workspace/scripts/fupan_collector.sh`

**功能：**
1. 采集当日盘面亮点时间线数据
2. 记录每只股票的异动时间、名称、板块、异动类型
3. 存储到 `/tmp/kaipanla/fupan_data.csv`

**数据价值：**
- 当日市场热点追踪
- 主力异动方向分析
- 板块轮动节奏把握

**入口坐标：** (440, 220) - 首页第一行第三个图标

---
# Keep this file empty (or with only comments) to skip heartbeat API calls.
# Add tasks below when you want the agent to check something periodically.
