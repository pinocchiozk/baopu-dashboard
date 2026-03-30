#!/bin/bash

# A 股市场情绪监控 - launchd 包装脚本
# 由 launchd 每 10 分钟调用一次，脚本内部判断是否交易时段

set -e

# 设置完整 PATH（包含 homebrew）
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# 显式指定 ADB 路径
export ADB_PATH="/opt/homebrew/bin/adb"

SCRIPT_DIR="/Users/macclaw/.openclaw/workspace/scripts"
LOG_FILE="/tmp/kaipanla/launchd.log"
CSV_FILE="/tmp/kaipanla/sentiment_data.csv"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查是否是交易日（周一至周五）
DAY_OF_WEEK=$(date +%u)  # 1=周一，7=周日
if [ "$DAY_OF_WEEK" -gt 5 ]; then
    log "周末，跳过"
    exit 0
fi

# 检查是否在交易时段（9:15-11:30, 13:00-15:30）
CURRENT_HOUR=$(date +%H)
CURRENT_MIN=$(date +%M)
CURRENT_TIME=$((CURRENT_HOUR * 60 + CURRENT_MIN))

OPEN_TIME=$((9 * 60 + 15))     # 9:15 = 555 分钟
MORNING_CLOSE=$((11 * 60 + 30)) # 11:30 = 690 分钟
AFTERNOON_OPEN=$((13 * 60 + 0)) # 13:00 = 780 分钟
CLOSE_TIME=$((15 * 60 + 30))    # 15:30 = 930 分钟

# 检查是否在休市时间
if [ "$CURRENT_TIME" -lt "$OPEN_TIME" ] || \
   ([ "$CURRENT_TIME" -gt "$MORNING_CLOSE" ] && [ "$CURRENT_TIME" -lt "$AFTERNOON_OPEN" ]) || \
   [ "$CURRENT_TIME" -gt "$CLOSE_TIME" ]; then
    log "非交易时段（当前：${CURRENT_HOUR}:${CURRENT_MIN}），跳过"
    exit 0
fi

log "=== 开始采集 ==="

# 运行监控脚本
"$SCRIPT_DIR/sentiment_monitor.sh" >> "$LOG_FILE" 2>&1

log "=== 采集完成 ==="

# 15:30 收盘后生成日 K 线
CURRENT_TIME_STR=$(date +%H:%M)
if [ "$CURRENT_TIME_STR" = "15:30" ]; then
    log "📊 收盘，生成日 K 线..."
    "$SCRIPT_DIR/sentiment_daily_k.sh" >> "$LOG_FILE" 2>&1
    log "✅ 日 K 线生成完成"
fi
