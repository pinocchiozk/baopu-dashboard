#!/bin/bash

# A 股市场情绪数据采集脚本（自动化版）
# 输出格式：8 字段精简版
# 依赖：ADB, MuMu 模拟器 (1440x2560), 开盘啦 App

ADB="adb -s 127.0.0.1:16384"
TEMP_DIR="/tmp/kaipanla"
OUTPUT_FILE="${TEMP_DIR}/sentiment_result.txt"

# 创建临时目录
mkdir -p "$TEMP_DIR"

echo "🔍 开始采集 A 股市场情绪数据..."
echo ""

# 1. 检查 ADB 连接
if ! $ADB devices 2>/dev/null | grep -q "127.0.0.1:16384.*device"; then
    echo "❌ ADB 连接失败，请检查 MuMu 模拟器是否运行"
    exit 1
fi

# 2. 启动开盘啦 App
$ADB shell monkey -p com.aiyu.kaipanla -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1
sleep 5

# 3. 进入市场情绪页面
$ADB shell input tap 300 100
sleep 3

# 4. 下滑查看完整数据
$ADB shell input swipe 500 1500 500 800
sleep 2

# 5. 截取完整数据页面
$ADB shell screencap -p > "${TEMP_DIR}/sentiment.png"

# 6. 返回首页
$ADB shell input keyevent 4
sleep 1

# 7. 输出结果
echo "✅ 数据采集完成"
echo ""
echo "📸 截图已保存：${TEMP_DIR}/sentiment.png"
echo ""
echo "📊 数据格式："
echo "--- BEGIN ---"
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
echo "--- END ---"
echo ""
echo "💡 请查看截图后填写数据"

# macOS 用户自动打开截图
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "${TEMP_DIR}/sentiment.png" 2>/dev/null
fi
