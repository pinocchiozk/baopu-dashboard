#!/bin/bash

# A 股市场情绪数据采集脚本
# 输出格式：8 字段精简版
# 依赖：ADB, MuMu 模拟器 (1440x2560), 开盘啦 App

ADB="adb -s 127.0.0.1:16384"
TEMP_DIR="/tmp/kaipanla"
OUTPUT_FILE="${TEMP_DIR}/sentiment_data.txt"

# 创建临时目录
mkdir -p "$TEMP_DIR"

echo "🔍 开始采集 A 股市场情绪数据..."

# 1. 检查 ADB 连接
echo "📱 检查 ADB 连接..."
if ! $ADB devices | grep -q "127.0.0.1:16384.*device"; then
    echo "❌ ADB 连接失败，请检查 MuMu 模拟器是否运行"
    exit 1
fi
echo "✅ ADB 连接正常"

# 2. 启动开盘啦 App
echo "🚀 启动开盘啦 App..."
$ADB shell monkey -p com.aiyu.kaipanla -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1
sleep 5

# 3. 截图确认首页
$ADB shell screencap -p > "${TEMP_DIR}/home.png"
echo "📸 已截取首页截图：${TEMP_DIR}/home.png"

# 4. 进入市场情绪页面
echo "📊 尝试进入市场情绪页面..."

# 方法 1: 直接点击 (坐标 300, 100)
$ADB shell input tap 300 100
sleep 3

# 截图确认
$ADB shell screencap -p > "${TEMP_DIR}/sentiment.png"
echo "📸 已截取市场情绪页面截图：${TEMP_DIR}/sentiment.png"

# 5. 下滑查看完整数据
echo "📋 下滑查看完整数据..."
$ADB shell input swipe 500 1500 500 800
sleep 2

# 截图
$ADB shell screencap -p > "${TEMP_DIR}/sentiment_full.png"
echo "📸 已截取完整数据截图：${TEMP_DIR}/sentiment_full.png"

# 6. 返回首页
$ADB shell input keyevent 4
sleep 1

# 7. 输出数据模板（需要人工核对截图填写）
echo ""
echo "=========================================="
echo "📊 A 股市场情绪数据采集完成"
echo "=========================================="
echo ""
echo "截图已保存至：${TEMP_DIR}/"
echo "  - home.png (首页)"
echo "  - sentiment.png (市场情绪页面)"
echo "  - sentiment_full.png (完整数据)"
echo ""
echo "请根据截图填写以下数据："
echo ""
cat << EOF
市场情绪 __ 分（__:__）
涨停家数：__ 家
跌停家数：__ 家
上涨家数：____ 家
下跌家数：____ 家
上证指数：____.__ (+_.__%)
实际量能：_.__ 万亿
预测量能：_.__ 万亿
EOF
echo ""
echo "=========================================="
echo "💡 提示：查看截图可使用以下命令"
echo "   macOS: open ${TEMP_DIR}/sentiment_full.png"
echo "   Linux: xdg-open ${TEMP_DIR}/sentiment_full.png"
echo "=========================================="
