#!/bin/bash

# 每日情绪 K 线生成脚本
# 用法：./generate_daily_kline.sh
# 功能：从 sentiment_data.csv 生成当日日 K 线，写入 sentiment_daily_k.csv

set -e

CSV_FILE="/tmp/kaipanla/sentiment_data.csv"
DAILY_K_FILE="/tmp/kaipanla/sentiment_daily_k.csv"
LOG_FILE="/tmp/kaipanla/kline_generate.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查是否是交易日（周一至周五）
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" -gt 5 ]; then
    log "周末，跳过"
    exit 0
fi

# 检查是否已过 15:00（收盘后）
CURRENT_HOUR=$(date +%-H)
CURRENT_MIN=$(date +%-M)
CURRENT_TIME=$((CURRENT_HOUR * 60 + CURRENT_MIN))
CLOSE_TIME=$((15 * 60 + 0))

if [ "$CURRENT_TIME" -lt "$CLOSE_TIME" ]; then
    log "尚未收盘（${CURRENT_HOUR}:${CURRENT_MIN}），跳过"
    exit 0
fi

log "=== 收盘后，开始生成日 K 线 ==="

# 获取今日日期
TODAY=$(date +%Y-%m-%d)

# 检查 CSV 文件是否存在
if [ ! -f "$CSV_FILE" ]; then
    log "❌ CSV 文件不存在：$CSV_FILE"
    exit 1
fi

# 使用 Python 生成日 K 线
python3 << PYEOF
import csv
from datetime import datetime

today = "$TODAY"
csv_file = "$CSV_FILE"
daily_k_file = "$DAILY_K_FILE"

# 读取今日所有数据
scores = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # 跳过表头
    for row in reader:
        if len(row) >= 3 and row[0] == today:
            try:
                score = int(row[2])
                scores.append(score)
            except (ValueError, IndexError):
                continue

if not scores:
    print(f"❌ 未找到 {today} 的数据")
    exit(1)

# 计算 K 线数据
open_score = scores[0]      # 开盘=首笔
close_score = scores[-1]    # 收盘=末笔
high_score = max(scores)    # 最高
low_score = min(scores)     # 最低

# 计算涨跌幅
if open_score > 0:
    change_pct = round((close_score - open_score) / open_score * 100, 2)
else:
    change_pct = 0.0

# 判断 K 线状态
if close_score >= open_score:
    status = "📈 阳"
else:
    status = "📉 阴"

# 写入日 K 线文件
import os

# 检查是否已存在该日期
file_exists = os.path.exists(daily_k_file) and os.path.getsize(daily_k_file) > 0
already_exists = False

if file_exists:
    with open(daily_k_file, 'r', encoding='utf-8') as f:
        existing_dates = [line.split(',')[0] for line in f.readlines()]
        if today in existing_dates:
            print(f"⚠️ {today} 数据已存在，跳过")
            exit(0)

with open(daily_k_file, 'a', encoding='utf-8') as f:
    if not file_exists:
        f.write("日期，开盘分，收盘分，最高分，最低分，涨跌幅，状态\n")
    
    f.write(f"{today},{open_score},{close_score},{high_score},{low_score},{change_pct},{status}\n")

print(f"✅ 生成 {today} 日 K 线：O:{open_score} C:{close_score} H:{high_score} L:{low_score} {change_pct}% {status}")
PYEOF

if [ $? -eq 0 ]; then
    log "✅ 日 K 线生成成功"
else
    log "❌ 日 K 线生成失败"
    exit 1
fi

log "=== 生成完成 ==="
