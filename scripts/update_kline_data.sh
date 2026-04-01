#!/bin/bash

# 情绪 K 线数据自动追加脚本
# 用法：./update_kline_data.sh
# 功能：从 sentiment_daily_k.csv 读取最新数据，追加到 emotion-data.json

set -e

CSV_FILE="/tmp/kaipanla/sentiment_daily_k.csv"
JSON_FILE="/Users/macclaw/.openclaw/workspace/emotion-kline/emotion-data.json"
LOG_FILE="/tmp/kaipanla/kline_update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查 CSV 文件是否存在
if [ ! -f "$CSV_FILE" ]; then
    log "❌ CSV 文件不存在：$CSV_FILE"
    exit 1
fi

# 获取最新一行数据（排除表头）
LATEST_LINE=$(tail -1 "$CSV_FILE")
if [ -z "$LATEST_LINE" ]; then
    log "❌ CSV 文件为空"
    exit 1
fi

# 解析 CSV 数据
# 格式：日期，开盘分，收盘分，最高分，最低分，涨跌幅，状态
DATE=$(echo "$LATEST_LINE" | cut -d',' -f1)
OPEN=$(echo "$LATEST_LINE" | cut -d',' -f2)
CLOSE=$(echo "$LATEST_LINE" | cut -d',' -f3)
HIGH=$(echo "$LATEST_LINE" | cut -d',' -f4)
LOW=$(echo "$LATEST_LINE" | cut -d',' -f5)

# 格式化日期（2026-03-31 → 3 月 31 日）
MONTH=$(echo "$DATE" | cut -d'-' -f2 | sed 's/^0//')
DAY=$(echo "$DATE" | cut -d'-' -f3 | sed 's/^0//')
LABEL="${MONTH}月${DAY}日"

log "📊 读取到最新数据：$DATE | O:$OPEN C:$CLOSE H:$HIGH L:$LOW"

# 检查 JSON 文件是否已存在该日期
if grep -q "\"date\": \"$DATE\"" "$JSON_FILE" 2>/dev/null; then
    log "⚠️ $DATE 数据已存在，跳过追加"
    exit 0
fi

# 使用 Python 追加数据到 JSON（避免手动处理 JSON 格式）
python3 << EOF
import json

# 读取现有数据
with open('$JSON_FILE', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 添加新数据
new_day = {
    "date": "$DATE",
    "label": "$LABEL",
    "open": $OPEN,
    "close": $CLOSE,
    "high": $HIGH,
    "low": $LOW
}

data['days'].append(new_day)

# 写回文件
with open('$JSON_FILE', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ 成功追加：$DATE")
EOF

if [ $? -eq 0 ]; then
    log "✅ 数据追加成功：$DATE"
    
    # 显示当前数据条数
    COUNT=$(python3 -c "import json; print(len(json.load(open('$JSON_FILE'))['days']))")
    log "📈 当前总数据量：$COUNT 天"
    
    # 自动推送到 GitHub
    log "🚀 推送到 GitHub..."
    cd /Users/macclaw/.openclaw/workspace/emotion-kline
    git add emotion-data.json
    git commit -m "自动更新：$DATE 情绪数据" 2>/dev/null || {
        log "⚠️ 没有新更改或提交失败"
    }
    git push origin main 2>&1 | tee -a "$LOG_FILE"
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "✅ GitHub 推送成功"
    else
        log "❌ GitHub 推送失败"
    fi
else
    log "❌ 数据追加失败"
    exit 1
fi
