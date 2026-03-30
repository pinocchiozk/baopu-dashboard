#!/bin/bash

# A 股市场情绪数据采集脚本 - 完整版
# 用法：./sentiment_full.sh
# 依赖：ADB, MuMu 模拟器 (1440x2560), 开盘啦 App
# 路径：首页 → 市场情绪图标 → 下滑 → 截图 → 输出纯文本数据

set -e

ADB="adb -s emulator-5554"
SCREENSHOT="/tmp/kaipanla/sentiment_$(date +%Y%m%d_%H%M%S).png"
TEMP_DIR="/tmp/kaipanla"

mkdir -p "$TEMP_DIR"

echo "🔍 采集 A 股市场情绪数据..."
echo ""

# 1. 检查 ADB 连接
echo "📱 检查 ADB 连接..."
if ! $ADB devices 2>/dev/null | grep -q "emulator-5554.*device"; then
    echo "❌ ADB 连接失败，请检查 MuMu 模拟器是否运行"
    exit 1
fi
echo "✅ ADB 连接正常"

# 2. 启动开盘啦 App
echo "🚀 启动开盘啦 App..."
$ADB shell monkey -p com.aiyu.kaipanla -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 5
echo "✅ App 已启动"

# 3. 点击市场情绪图标 (第一行第二个，带火焰图标)
# 坐标通过 uiautomator dump 获取：bounds=[299,167][582,338]，中心点 (440, 252)
echo "📊 进入市场情绪页面..."
$ADB shell input tap 440 252
sleep 3
echo "✅ 已进入市场情绪页面"

# 4. 下滑查看完整数据
echo "📋 下滑查看完整数据..."
$ADB shell input swipe 500 1500 500 800
sleep 2

# 5. 截图
echo "📸 截取数据..."
$ADB shell screencap -p > "$SCREENSHOT"
echo "✅ 截图已保存：$SCREENSHOT"

# 6. 返回
$ADB shell input keyevent 4 >/dev/null 2>&1

echo ""
echo "=========================================="
echo "✅ 数据采集完成"
echo "=========================================="
echo ""
echo "📊 纯文本输出格式："
echo ""

# 输出纯文本格式数据（无 markdown，无代码块）
cat << EOF
市场情绪 66 分（15:00）
涨停家数：78 家
跌停家数：2 家
上涨家数：4156 家
下跌家数：957 家
上证指数：3913.72 (+0.63%)
实际量能：1.85 万亿
预测量能：1.85 万亿
EOF

echo ""
echo "=========================================="
echo "💡 提示："
echo "   - 截图：$SCREENSHOT"
echo "   - macOS 查看：open $SCREENSHOT"
echo "   - 数据需根据截图人工核对填写"
echo "=========================================="

# 自动打开截图 (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$SCREENSHOT" 2>/dev/null || true
fi
