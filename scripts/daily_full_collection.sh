#!/bin/bash
# 每日盘后全量采集 + 报告生成

echo "========== $(date) 盘后采集开始 =========="

WORKSPACE="/Users/macclaw/.openclaw/workspace"
DB_DIR="$WORKSPACE/database"
SCRIPT_DIR="$WORKSPACE/scripts"
DATE_STR=$(date +%Y%m%d)

# 1. 采集截图
echo "[1/4] 执行截图采集..."
bash $SCRIPT_DIR/kaipanla_full_collection.sh

# 2. 导入数据库
echo "[2/4] 导入数据库..."
cd $DB_DIR
python import_data.py

# 3. 生成报告
echo "[3/4] 生成每日报告..."
cd $WORKSPACE/strategy
python daily_report.py

# 4. 推送信号
echo "[4/4] 输出策略信号..."
python sentiment_strategy.py

echo "========== $(date) 盘后采集完成 =========="
