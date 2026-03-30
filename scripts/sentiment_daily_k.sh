#!/bin/bash

# A 股市场情绪日 K 线生成脚本
# 用法：./sentiment_daily_k.sh [日期]
# 输出：当日情绪 K 线数据 + 最近 N 日走势

set -e

CSV_FILE="/tmp/kaipanla/sentiment_data.csv"
DAILY_K_FILE="/tmp/kaipanla/sentiment_daily_k.csv"
TODAY=$(date +%Y-%m-%d)

# 初始化日 K 线文件（如果不存在）
if [ ! -f "$DAILY_K_FILE" ]; then
    echo "日期，开盘分，收盘分，最高分，最低分，涨跌幅，状态" >> "$DAILY_K_FILE"
fi

# 时间定义
OPEN_TIME="09:15"    # 竞价开始作为开盘
CLOSE_TIME="15:30"   # 收盘作为收盘分

# 获取当日所有数据（9:15 及之后，之前的属于上一交易日）
get_daily_data() {
    local date="$1"
    # 过滤掉 9:15 之前的数据（属于上一交易日）
    grep "^$date" "$CSV_FILE" | awk -F',' '$2 >= "09:15"' | sort -t',' -k2
}

# 生成日 K 线
generate_daily_k() {
    local date="$1"
    local data=$(get_daily_data "$date")
    
    if [ -z "$data" ]; then
        echo "❌ 未找到 $date 的数据"
        return 1
    fi
    
    # 提取情绪分数列（第 3 列）
    local scores=$(echo "$data" | cut -d',' -f3)
    
    # 开盘分（9:15 附近的第一条数据）
    local open=$(echo "$data" | head -1 | cut -d',' -f3)
    # 收盘分（15:30 附近的最后一条数据）
    local close=$(echo "$data" | tail -1 | cut -d',' -f3)
    # 最高分
    local high=$(echo "$scores" | sort -n | tail -1)
    # 最低分
    local low=$(echo "$scores" | sort -n | head -1)
    
    # 计算涨跌幅
    local change=0
    if [ "$open" -gt 0 ]; then
        change=$(echo "scale=2; ($close - $open) * 100 / $open" | bc)
    fi
    
    # 判断 K 线状态
    local k_status="📊"
    if [ "$close" -gt "$open" ]; then
        k_status="📈 阳"
    elif [ "$close" -lt "$open" ]; then
        k_status="📉 阴"
    fi
    
    # 输出
    echo "日期：$date"
    echo "开盘分：$open"
    echo "收盘分：$close"
    echo "最高分：$high"
    echo "最低分：$low"
    echo "涨跌幅：${change}%"
    echo "K 线状态：$k_status"
    
    # 记录到 CSV
    echo "$date,$open,$close,$high,$low,$change,$k_status" >> "$DAILY_K_FILE"
}

# 生成最近 N 日情绪 K 线走势（文本版）
generate_k_chart() {
    local days=${1:-5}
    
    echo ""
    echo "📊 最近 $days 日情绪 K 线走势"
    echo "================================"
    
    tail -n $days "$DAILY_K_FILE" | tail -n +2 | while IFS=',' read -r date open close high low change status; do
        # 简单文本 K 线
        local bar=""
        local width=$(( (close > 0 ? close : 0) / 2 ))  # 简化显示
        if [ "$change" != "" ]; then
            local sign=$(echo "$change" | grep -q "^-" && echo "▼" || echo "▲")
            printf "%s %s | O:%-3s C:%-3s H:%-3s L:%-3s %s%5s%%\n" \
                "$date" "$status" "$open" "$close" "$high" "$low" "$sign" "${change#-}"
        fi
    done
}

# 主逻辑
if [ "$1" ]; then
    TARGET_DATE="$1"
else
    TARGET_DATE="$TODAY"
fi

echo "📊 A 股市场情绪日 K 线"
echo "======================"
echo ""

generate_daily_k "$TARGET_DATE"
generate_k_chart 5
