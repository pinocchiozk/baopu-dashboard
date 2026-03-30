#!/bin/bash

# A 股市场情绪预警脚本
# 用法：./sentiment_alert.sh
# 预警规则：
#   - 情绪 < 25 分：冰点（买点）🧊
#   - 情绪 > 80 分：过热（风险）🔥
#   - 25-80 分：正常 📊

set -e

ADB="adb -s emulator-5554"
SCREENSHOT="/tmp/kaipanla/sentiment_$(date +%Y%m%d_%H%M%S).png"
TEMP_DIR="/tmp/kaipanla"
ALERT_LOG="$TEMP_DIR/alert_history.log"

mkdir -p "$TEMP_DIR"

# 预警阈值
ICE_POINT=25    # 冰点阈值（买点）
OVER_HEAT=80    # 过热阈值（风险）

echo "🔍 采集 A 股市场情绪数据并检测预警..."
echo ""

# 1. 检查 ADB 连接
if ! $ADB devices 2>/dev/null | grep -q "emulator-5554.*device"; then
    echo "❌ ADB 连接失败，请检查 MuMu 模拟器是否运行"
    exit 1
fi

# 2. 启动开盘啦 App
$ADB shell monkey -p com.aiyu.kaipanla -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 5

# 3. 点击市场情绪图标 (tap 440 252)
$ADB shell input tap 440 252
sleep 3

# 4. 下滑查看完整数据
$ADB shell input swipe 500 1500 500 800
sleep 2

# 5. 截图
$ADB shell screencap -p > "$SCREENSHOT"

# 6. 返回
$ADB shell input keyevent 4 >/dev/null 2>&1

# 7. 输出数据（示例数据，实际需根据截图填写）
SENTIMENT_SCORE=66      # 市场情绪分数
LIMIT_UP=78             # 涨停家数
LIMIT_DOWN=2            # 跌停家数
UP_COUNT=4156           # 上涨家数
DOWN_COUNT=957          # 下跌家数
SH_INDEX="3913.72"      # 上证指数
SH_CHANGE="+0.63"       # 上证指数涨跌幅
REAL_VOLUME="1.85"      # 实际量能（万亿）
PREDICT_VOLUME="1.85"   # 预测量能（万亿）

# 8. 输出纯文本格式数据
echo ""
echo "=========================================="
echo "📊 A 股市场情绪数据"
echo "=========================================="
echo ""
echo "市场情绪 $SENTIMENT_SCORE 分（15:00）"
echo "涨停家数：$LIMIT_UP 家"
echo "跌停家数：$LIMIT_DOWN 家"
echo "上涨家数：$UP_COUNT 家"
echo "下跌家数：$DOWN_COUNT 家"
echo "上证指数：$SH_INDEX ($SH_CHANGE%)"
echo "实际量能：$REAL_VOLUME 万亿"
echo "预测量能：$PREDICT_VOLUME 万亿"
echo ""

# 9. 情绪预警判断
echo "=========================================="
echo "🚨 情绪预警检测"
echo "=========================================="
echo ""

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

if [ "$SENTIMENT_SCORE" -lt "$ICE_POINT" ]; then
    echo "🧊 冰点预警！市场情绪 $SENTIMENT_SCORE 分（低于 $ICE_POINT 分）"
    echo ""
    echo "💡 操作建议：冰点为买点，可关注以下机会"
    echo "   - 龙头股低吸"
    echo "   - 首板挖掘"
    echo "   - 仓位：可提升至 7-8 成"
    echo ""
    echo "⏰ 时间：$TIMESTAMP"
    echo "=========================================="
    
    # 记录预警日志
    echo "[$TIMESTAMP] 🧊 冰点预警：情绪$SENTIMENT_SCORE 分 | 涨停$LIMIT_UP | 跌停$LIMIT_DOWN" >> "$ALERT_LOG"
    
    # 自动打开截图
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$SCREENSHOT" 2>/dev/null || true
    fi
    
    exit 0
    
elif [ "$SENTIMENT_SCORE" -gt "$OVER_HEAT" ]; then
    echo "🔥 过热预警！市场情绪 $SENTIMENT_SCORE 分（高于 $OVER_HEAT 分）"
    echo ""
    echo "💡 操作建议：注意风险，考虑减仓"
    echo "   - 高位股止盈"
    echo "   - 避免追高"
    echo "   - 仓位：降至 3-5 成"
    echo ""
    echo "⏰ 时间：$TIMESTAMP"
    echo "=========================================="
    
    # 记录预警日志
    echo "[$TIMESTAMP] 🔥 过热预警：情绪$SENTIMENT_SCORE 分 | 涨停$LIMIT_UP | 跌停$LIMIT_DOWN" >> "$ALERT_LOG"
    
    # 自动打开截图
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$SCREENSHOT" 2>/dev/null || true
    fi
    
    exit 0
    
else
    echo "📊 情绪正常：$SENTIMENT_SCORE 分（$ICE_POINT-$OVER_HEAT 分为正常区间）"
    echo ""
    echo "💡 操作建议：正常操作，持仓待涨"
    echo "   - 仓位：5-7 成"
    echo "   - 关注主线板块"
    echo ""
    echo "⏰ 时间：$TIMESTAMP"
    echo "=========================================="
    
    # 记录正常数据
    echo "[$TIMESTAMP] 📊 正常：情绪$SENTIMENT_SCORE 分 | 涨停$LIMIT_UP | 跌停$LIMIT_DOWN" >> "$ALERT_LOG"
    
    # 自动打开截图
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$SCREENSHOT" 2>/dev/null || true
    fi
    
    exit 0
fi
