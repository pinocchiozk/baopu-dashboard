# A 股市场情绪监控 - launchd 自动任务配置

## ✅ 配置完成

**任务状态：** 已加载并运行
**任务名称：** `com.kaipanla.sentiment.monitor`

---

## 📅 运行时间

| 项目 | 配置 |
|------|------|
| 频率 | 每 30 分钟 |
| 时段 | 交易日 9:15-15:30 |
| 跳过 | 周末、节假日、非交易时段 |

---

## 📁 文件位置

| 文件 | 路径 |
|------|------|
| launchd 配置 | `/Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist` |
| 包装脚本 | `/Users/macclaw/.openclaw/workspace/scripts/sentiment_launchd.sh` |
| 监控脚本 | `/Users/macclaw/.openclaw/workspace/scripts/sentiment_monitor.sh` |
| 数据 CSV | `/tmp/kaipanla/sentiment_data.csv` |
| 运行日志 | `/tmp/kaipanla/launchd.log` |
| 截图目录 | `/tmp/kaipanla/sentiment_YYYYMMDD_HHMMSS.png` |

---

## 🔧 管理命令

### 查看状态
```bash
launchctl list | grep kaipanla
```

### 查看日志
```bash
tail -20 /tmp/kaipanla/launchd.log
```

### 暂停任务
```bash
launchctl unload /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist
```

### 恢复任务
```bash
launchctl load /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist
```

### 永久删除
```bash
launchctl unload /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist
rm /Users/macclaw/.openclaw/workspace/scripts/com.kaipanla.sentiment.monitor.plist
rm /Users/macclaw/.openclaw/workspace/scripts/sentiment_launchd.sh
```

---

## 📊 数据查看

### 查看今日采集记录
```bash
cat /tmp/kaipanla/sentiment_data.csv | grep $(date +%Y-%m-%d)
```

### 查看情绪 K 线
```bash
/Users/macclaw/.openclaw/workspace/scripts/sentiment_daily_k.sh
```

### 查看最新截图
```bash
open /tmp/kaipanla/sentiment_*.png | tail -1
```

---

## ⚠️ 注意事项

1. **MuMu 模拟器必须运行** - ADB 需要连接模拟器
2. **开盘啦 App 需要登录** - 确保已登录账号
3. **屏幕分辨率** - 必须是 1440x2560
4. **截图识别** - 目前需要人工或 AI 识别截图更新 CSV

---

## 🔄 未来优化

- [ ] OCR 自动识别（PaddleOCR/EasyOCR）
- [ ] 自动更新 CSV（无需人工干预）
- [ ] 飞书推送集成（冰点/过热预警）

---

**配置日期：** 2026-03-30
**配置人：** AI Assistant
