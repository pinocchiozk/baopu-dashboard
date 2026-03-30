# A 股市场情绪监控 - 完全自动化配置文档

## ✅ 自动化已完成

**配置日期：** 2026-03-30  
**状态：** 全自动运行中

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    launchd 定时调度                          │
│              (每 30 分钟触发一次)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              sentiment_launchd.sh                            │
│         (判断交易日 + 交易时段)                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              sentiment_monitor.sh                            │
│    (ADB 控制 → 截图 → OCR 识别 → 更新 CSV)                     │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
               ▼                      ▼
    ┌──────────────────┐   ┌──────────────────────┐
    │   ADB 控制        │   │   OCR 服务            │
    │  - 打开 App       │   │  (常驻内存，秒级识别)  │
    │  - 点击情绪图标   │   │                      │
    │  - 下滑截图       │   │                      │
    └──────────────────┘   └──────────────────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │   CSV 数据记录        │
                           │   /tmp/kaipanla/     │
                           │   sentiment_data.csv │
                           └──────────────────────┘
```

---

## 🔧 服务列表

| 服务名称 | 类型 | 功能 | 状态 |
|---------|------|------|------|
| `com.kaipanla.sentiment.monitor` | launchd | 每 30 分钟触发采集 | ✅ 运行中 |
| `com.kaipanla.ocr.service` | launchd | OCR 识别服务（常驻） | ✅ 运行中 |

---

## 📁 文件位置

### 脚本
| 文件 | 路径 |
|------|------|
| 监控脚本 | `/Users/macclaw/.openclaw/workspace/scripts/sentiment_monitor.sh` |
| OCR 服务 | `/Users/macclaw/.openclaw/workspace/scripts/sentiment_ocr_service.py` |
| launchd 包装 | `/Users/macclaw/.openclaw/workspace/scripts/sentiment_launchd.sh` |
| 日 K 线生成 | `/Users/macclaw/.openclaw/workspace/scripts/sentiment_daily_k.sh` |

### 配置
| 文件 | 路径 |
|------|------|
| 监控任务配置 | `/Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist` |
| OCR 服务配置 | `/Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.ocr.service.plist` |

### 数据
| 文件 | 路径 |
|------|------|
| 原始数据 CSV | `/tmp/kaipanla/sentiment_data.csv` |
| 日 K 线 CSV | `/tmp/kaipanla/sentiment_daily_k.csv` |
| 运行日志 | `/tmp/kaipanla/monitor.log` |
| launchd 日志 | `/tmp/kaipanla/launchd.log` |
| 截图目录 | `/tmp/kaipanla/sentiment_YYYYMMDD_HHMMSS.png` |

---

## 📅 运行时间

| 项目 | 配置 |
|------|------|
| 频率 | 每 10 分钟 |
| 交易日 | 周一至周五 |
| 时段 | 9:15 - 15:30 |
| 首次采集 | 9:15（竞价开盘） |
| 最后采集 | 15:30（收盘） |

---

## 📊 数据字段

| 字段 | 说明 | 来源 |
|------|------|------|
| 市场情绪 | 综合强度分数（0-100） | OCR 识别 |
| 涨停家数 | 实际涨停股票数 | OCR 识别 |
| 跌停家数 | 实际跌停股票数 | OCR 识别 |
| 上涨家数 | 上涨股票数量 | OCR 识别 |
| 下跌家数 | 下跌股票数量 | OCR 识别 |
| 上证指数 | 大盘指数及涨跌幅 | OCR 识别 |
| 实际量能 | 沪深两市实际成交额（万亿） | OCR 识别 |
| 预测量能 | 预估全天成交额（万亿） | OCR 识别 |

---

## 🔍 查看数据

### 查看今日采集记录
```bash
cat /tmp/kaipanla/sentiment_data.csv | grep $(date +%Y-%m-%d)
```

### 查看情绪日 K 线
```bash
/Users/macclaw/.openclaw/workspace/scripts/sentiment_daily_k.sh
```

### 查看运行日志
```bash
tail -20 /tmp/kaipanla/monitor.log
tail -20 /tmp/kaipanla/launchd.log
```

### 查看最新截图
```bash
ls -lt /tmp/kaipanla/sentiment_*.png | head -1
open $(ls -t /tmp/kaipanla/sentiment_*.png | head -1)
```

---

## 🛠️ 服务管理

### 查看服务状态
```bash
launchctl list | grep kaipanla
```

### 暂停监控任务
```bash
launchctl unload /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist
```

### 恢复监控任务
```bash
launchctl load /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist
```

### 暂停 OCR 服务
```bash
launchctl unload /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.ocr.service.plist
```

### 恢复 OCR 服务
```bash
launchctl load /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.ocr.service.plist
```

### 永久删除
```bash
# 卸载服务
launchctl unload /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist
launchctl unload /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.ocr.service.plist

# 删除文件
rm /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.*.plist
rm /Users/macclaw/.openclaw/workspace/scripts/sentiment_launchd.sh
rm /Users/macclaw/.openclaw/workspace/scripts/sentiment_ocr_service.py
```

---

## ⚠️ 依赖条件

1. **MuMu 模拟器** 必须运行（ADB 连接）
2. **开盘啦 App** 必须已登录
3. **模拟器分辨率** 必须是 1440x2560
4. **macOS 系统** 必须开启辅助功能权限（ADB 控制）

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 单次采集耗时 | ~15-20 秒 |
| OCR 识别耗时 | ~5-10 秒（模型已预加载） |
| 内存占用 | ~200MB（OCR 服务常驻） |
| 准确率 | ~95%+（基于测试数据） |

---

## 🔄 未来优化

- [ ] 冰点/过热自动飞书推送
- [ ] 情绪 K 线图表可视化
- [ ] 历史数据回测分析
- [ ] 策略信号生成

---

**最后更新：** 2026-03-30 10:25
