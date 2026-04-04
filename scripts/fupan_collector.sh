#!/bin/bash

# 复盘啦数据采集脚本
# 功能：采集当日市场热点异动数据
# 路径：首页 → 复盘啦 → OCR识别 → 存储

set -e

ADB="/opt/homebrew/bin/adb"
TEMP_DIR="/tmp/kaipanla"
SCREENSHOT="$TEMP_DIR/fupan_$(date +%Y%m%d_%H%M%S).png"
CSV_FILE="$TEMP_DIR/fupan_data.csv"
LOG_FILE="$TEMP_DIR/fupan.log"

mkdir -p "$TEMP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

# 检查是否是交易日
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" -gt 5 ]; then
    log "周末，跳过"
    exit 0
fi

# 检查是否在交易时段后（复盘数据主要在收盘后有价值，但盘中也可以采集）
CURRENT_HOUR=$(date +%-H)
CURRENT_MIN=$(date +%-M)
CURRENT_TIME=$((CURRENT_HOUR * 60 + CURRENT_MIN))
CLOSE_TIME=$((15 * 60 + 0))  # 15:00

# 复盘数据在 9:25 之后就可以开始采集
if [ "$CURRENT_TIME" -lt $((9 * 60 + 25)) ]; then
    log "非交易时段（${CURRENT_HOUR}:${CURRENT_MIN}），跳过"
    exit 0
fi

log "=== 开始采集复盘啦数据 ==="

# 1. 强制重启开盘啦 App
$ADB shell am force-stop com.aiyu.kaipanla 2>/dev/null
sleep 2
$ADB shell monkey -p com.aiyu.kaipanla -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 8

# 2. 点击"复盘啦"入口（第一行第三个图标，坐标 440, 220）
log "📍 点击复盘啦..."
$ADB shell input tap 440 220
sleep 5

# 3. 下滑查看完整数据（复盘数据可能很长）
$ADB shell input swipe 500 1200 500 400
sleep 2

# 4. 截图
$ADB shell screencap -p > "$SCREENSHOT"
log "📸 截图已保存：$SCREENSHOT"

# 5. 返回首页
$ADB shell input keyevent 4 >/dev/null 2>&1
sleep 1

# 6. 调用 OCR 识别
log "🔍 OCR 识别中..."
OCR_SERVICE_URL="http://127.0.0.1:8765"

OCR_RESPONSE=$(curl -s -X POST "$OCR_SERVICE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"image_path\": \"$SCREENSHOT\"}" \
  2>/dev/null)

# 解析 OCR 响应
OCR_DATA=$(echo "$OCR_RESPONSE" | python3 -c "
import sys, json, re
try:
    d = json.load(sys.stdin).get('data', {})
    texts = d.get('debug', []) or []
    all_text = ' '.join([t[0] if isinstance(t, (list, tuple)) else str(t) for t in texts])
    
    # 提取日期
    date_match = re.search(r'20\d{2}-\d{2}-\d{2}', all_text)
    date = date_match.group(0) if date_match else 'NULL'
    
    # 提取涨跌停数据
    limit_up_match = re.search(r'涨停\s*(\d+)\s*家', all_text)
    limit_up = limit_up_match.group(1) if limit_up_match else 'NULL'
    
    limit_down_match = re.search(r'跌停\s*(\d+)\s*家', all_text)
    limit_down = limit_down_match.group(1) if limit_down_match else 'NULL'
    
    # 提取盘面亮点数据
    highlights = re.findall(r'(\d{2}:\d{2})\s*([^\s]+)\s*([^\s]+)\s*([^\s]+)', all_text)
    
    print(f'DATE={date}')
    print(f'LIMIT_UP={limit_up}')
    print(f'LIMIT_DOWN={limit_down}')
    print(f'HIGHLIGHTS={highlights}')
except Exception as e:
    print(f'ERROR={e}')
" 2>/dev/null)

eval "$OCR_DATA"

log "📊 复盘数据：日期=$DATE | 涨停=$LIMIT_UP | 跌停=$LIMIT_DOWN"

# 7. 存储到 CSV
TODAY=$(date '+%Y-%m-%d')
TIMESTAMP=$(date '+%Y-%m-%d,%H:%M:%S')

# CSV 格式：日期,时间,涨停,跌停,盘面亮点(JSON)
if [ ! -f "$CSV_FILE" ]; then
    echo "日期,时间,涨停,跌停,盘面亮点" >> "$CSV_FILE"
fi

echo "$TODAY,$TIMESTAMP,$LIMIT_UP,$LIMIT_DOWN,$HIGHLIGHTS" >> "$CSV_FILE"

log "✅ 数据已保存到：$CSV_FILE"
log "=== 采集完成 ==="
