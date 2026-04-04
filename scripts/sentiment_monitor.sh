#!/bin/bash

# A 股市场情绪监测脚本 - 每 30 分钟采集 + 条件推送
# 用法：./sentiment_monitor.sh
# 功能：
#   1. 采集完整的 8 项数据
#   2. 记录到 CSV 文件
#   3. 仅在情绪<25 分或>85 分时推送飞书

set -e

ADB="/opt/homebrew/bin/adb"
TEMP_DIR="/tmp/kaipanla"
SCREENSHOT="$TEMP_DIR/sentiment_$(date +%Y%m%d_%H%M%S).png"
CSV_FILE="$TEMP_DIR/sentiment_data.csv"
LOG_FILE="$TEMP_DIR/monitor.log"

# 推送阈值
ICE_POINT=25    # 冰点阈值（推送买点信号）
OVER_HEAT=75    # 过热阈值（推送风险信号）

# 飞书配置
FEISHU_APP_ID="cli_a9217cf004b89bde"
FEISHU_APP_SECRET="96QItZ1TdXNfuJYaOgvadfycyvepv53E"
FEISHU_USER="ou_ca28f9bde02c28278caca087790d9a52"

# 获取飞书 token
get_feishu_token() {
    curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
      -H "Content-Type: application/json" \
      -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" | \
      python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))" 2>/dev/null
}

mkdir -p "$TEMP_DIR"

# 初始化 CSV 文件（如果不存在）
if [ ! -f "$CSV_FILE" ]; then
    echo "日期，时间，市场情绪，状态" >> "$CSV_FILE"
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

# 检查是否是交易日（周一至周五）
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" -gt 5 ]; then
    log "周末，跳过"
    exit 0
fi

# 检查是否在交易时段（9:15-11:30, 13:00-15:00）
CURRENT_HOUR=$(date +%-H)
CURRENT_MIN=$(date +%-M)
CURRENT_TIME=$((CURRENT_HOUR * 60 + CURRENT_MIN))

OPEN_TIME=$((9 * 60 + 15))      # 9:15
MORNING_CLOSE=$((11 * 60 + 30))  # 11:30
AFTERNOON_OPEN=$((13 * 60 + 0))  # 13:00
CLOSE_TIME=$((15 * 60 + 0))      # 15:00

if [ "$CURRENT_TIME" -lt "$OPEN_TIME" ] || \
   ([ "$CURRENT_TIME" -gt "$MORNING_CLOSE" ] && [ "$CURRENT_TIME" -lt "$AFTERNOON_OPEN" ]) || \
   [ "$CURRENT_TIME" -gt "$CLOSE_TIME" ]; then
    log "非交易时段（${CURRENT_HOUR}:${CURRENT_MIN}），跳过"
    exit 0
fi

send_feishu() {
    local message="$1"
    local token
    token=$(get_feishu_token)
    if [ -z "$token" ]; then
        log "❌ 获取飞书 token 失败"
        return 1
    fi
    # 使用环境变量传递 message，避免 heredoc 转义问题
    local result
    result=$(FEISHU_TOKEN="$token" FEISHU_TARGET_USER="$FEISHU_USER" FEISHU_MSG="$message" python3 << 'PYEOF'
import urllib.request
import json
import os

token = os.environ.get('FEISHU_TOKEN')
user = os.environ.get('FEISHU_TARGET_USER')
message = os.environ.get('FEISHU_MSG')

url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
# 关键：content 必须是 JSON 字符串，不是对象！
data = {
    "receive_id": user,
    "msg_type": "text",
    "content": json.dumps({"text": message})
}

req = urllib.request.Request(url, method='POST')
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', 'application/json')
req.data = json.dumps(data).encode('utf-8')

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        if result.get('code') == 0:
            print("SUCCESS")
        else:
            print(f"FAIL:{result}")
except Exception as e:
    print(f"FAIL:{e}")
PYEOF
)
    if [ "$result" = "SUCCESS" ]; then
        log "✅ 飞书推送成功"
    else
        log "❌ 飞书推送失败：$result"
    fi
}

# 1. 检查 ADB 连接
if ! $ADB devices 2>/dev/null | grep -q "emulator-5554.*device"; then
    log "❌ ADB 连接失败"
    exit 1
fi

# 2. 强制重启开盘啦 App（确保页面状态重置）
$ADB shell am force-stop com.aiyu.kaipanla 2>/dev/null
sleep 2
$ADB shell monkey -p com.aiyu.kaipanla -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 8

# 3. 点击市场情绪图标（首页第一排中间位置）
$ADB shell input tap 350 220
sleep 5

# 4. 等待页面加载并下滑刷新（确保情绪分数显示）
# 先下滑刷新，再等待数据加载
$ADB shell input swipe 500 300 500 800
sleep 3

# 5. 截图
$ADB shell screencap -p > "$SCREENSHOT"

# 6. 返回
$ADB shell input keyevent 4 >/dev/null 2>&1

# 7. OCR 自动识别数据
log "🔍 OCR 识别中..."

OCR_SERVICE_URL="http://127.0.0.1:8765"
SCREENSHOT_PATH="$SCREENSHOT"

# 调用 OCR 服务
OCR_RESPONSE=$(curl -s -X POST "$OCR_SERVICE_URL" \
  -H "Content-Type: application/json" \
  -d "{\"image_path\": \"$SCREENSHOT_PATH\"}" \
  2>/dev/null)

# 解析 OCR 响应（只取情绪分数）
SENTIMENT_SCORE=$(echo "$OCR_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('sentiment_score') or 'NULL')" 2>/dev/null)

# 其他字段不再需要，设为 0
LIMIT_UP=0
LIMIT_DOWN=0
UP_COUNT=0
DOWN_COUNT=0
SH_INDEX="0.00"
SH_CHANGE="0.00"
REAL_VOLUME="0.00"
PREDICT_VOLUME="0.00"

# 如果 OCR 失败，记录警告
if [ "$SENTIMENT_SCORE" = "NULL" ] || [ -z "$SENTIMENT_SCORE" ]; then
    log "⚠️ OCR 识别失败，情绪分数为 0"
    SENTIMENT_SCORE=0
else
    log "✅ OCR 识别成功：情绪$SENTIMENT_SCORE 分"
fi

# 8. 记录到 CSV（只保留情绪分数）
TIMESTAMP=$(date '+%Y-%m-%d,%H:%M:%S')
STATUS="正常"

# 判断状态
if [ "$SENTIMENT_SCORE" -le "$ICE_POINT" ]; then
    STATUS="🧊冰点"
elif [ "$SENTIMENT_SCORE" -ge "$OVER_HEAT" ]; then
    STATUS="🔥过热"
fi

# 追加到 CSV（只记录情绪分数）
echo "$TIMESTAMP,$SENTIMENT_SCORE,$STATUS" >> "$CSV_FILE"

log "✅ 数据已记录：情绪$SENTIMENT_SCORE 分 | 状态:$STATUS"

# 9. 条件推送（只在冰点或过热时推送）
if [ "$SENTIMENT_SCORE" -le "$ICE_POINT" ]; then
    MESSAGE="🧊 冰点预警！市场情绪$SENTIMENT_SCORE 分（≤$ICE_POINT 分）\n\n涨停：$LIMIT_UP 家\n跌停：$LIMIT_DOWN 家\n上涨：$UP_COUNT 家\n下跌：$DOWN_COUNT 家\n\n💡 冰点为买点，可关注龙头低吸机会"
    log "🧊 触发冰点预警，发送飞书推送"
    send_feishu "$MESSAGE"
    
elif [ "$SENTIMENT_SCORE" -ge "$OVER_HEAT" ]; then
    MESSAGE="🔥 过热预警！市场情绪$SENTIMENT_SCORE 分（≥$OVER_HEAT 分）\n\n涨停：$LIMIT_UP 家\n跌停：$LIMIT_DOWN 家\n上涨：$UP_COUNT 家\n下跌：$DOWN_COUNT 家\n\n💡 注意风险，考虑减仓"
    log "🔥 触发过热预警，发送飞书推送"
    send_feishu "$MESSAGE"
fi

# 10. 自动打开截图（macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$SCREENSHOT" 2>/dev/null || true
fi

log "----------------------------------------"
