# 开盘啦历史数据库

## 概述

本数据库用于存储每日市场情绪数据，支持策略开发和量化分析。

## 数据库结构

### 表结构

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| `daily_market` | 每日市场概况 | 日期、指数、涨跌家数、量能、情绪分 |
| `daily_lianban_stats` | 连板统计 | 一板、二板、三板、更高等数量和连板率 |
| `daily_limit_up` | 涨停明细 | 股票名称、代码、涨停时间、板块、封单金额 |
| `daily_sector` | 板块数据 | 板块名称、强度、主力净额、机构增仓 |
| `daily_daban` | 打板统计 | 涨停数、封板率、跌停数 |
| `daily_sentiment` | 情绪指标 | 破板率、昨日涨停/连板/破板今表现 |
| `daily_afterhours` | 尾盘异动 | 异动类型、股票、金额 |

### 视图

| 视图名 | 说明 |
|--------|------|
| `v_lianban_pool` | 连板个股池（2板及以上） |
| `v_sector_flow` | 板块资金流排名 |
| `v_profit_monitor` | 赚钱效应监控面板 |

## 使用方法

### 初始化数据库
```bash
cd database
./run_import.sh
```

### 查询示例

```sql
-- 最近5日市场情绪
SELECT * FROM daily_market ORDER BY trade_date DESC LIMIT 5;

-- 连板个股池
SELECT * FROM v_lianban_pool;

-- 板块资金流
SELECT * FROM v_sector_flow WHERE trade_date = '2026-04-03';

-- 赚钱效应监控
SELECT * FROM v_profit_monitor LIMIT 10;
```

### Python接口

```python
import sqlite3
conn = sqlite3.connect('kaipanla.db')

# 查询涨停股
cursor.execute("""
    SELECT trade_date, stock_name, lianban_days 
    FROM daily_limit_up 
    WHERE lianban_days >= 2
    ORDER BY trade_date DESC
""")
```

## 数据来源

- 开盘啦App → 市场情绪
- 开盘啦App → 行情-板块
- 开盘啦App → 打板

## 更新频率

- 盘后采集：每日15:00-15:30
- 盘中采集：每30分钟（交易时段）

## 策略开发用途

1. **连板率择时** - 通过连板率判断市场赚钱效应
2. **板块轮动** - 追踪主力资金流向板块
3. **龙头股追踪** - 监控连板股持续性
4. **情绪周期** - 分析情绪分数与大盘关系
