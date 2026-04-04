#!/bin/bash
# 开盘啦盘后全量采集脚本
# 执行时间：每个交易日收盘后

mkdir -p /tmp/kaipanla/daily/$(date +%Y%m%d)
WORKDIR="/tmp/kaipanla/daily/$(date +%Y%m%d)"

echo "========== $(date) 盘后采集开始 =========="

# 返回首页
adb -s 127.0.0.1:16416 shell input keyevent 4
sleep 1
adb -s 127.0.0.1:16416 shell input keyevent 4
sleep 1

# ===== 1. 市场情绪采集 =====
echo "[1/5] 进入市场情绪..."
adb -s 127.0.0.1:16416 shell input tap 350 220
sleep 5
adb -s 127.0.0.1:16416 shell screencap -p > $WORKDIR/01_市场情绪_首页.png
echo "  - 已保存: 01_市场情绪_首页.png"

# 向上滑动查看完整内容
adb -s 127.0.0.1:16416 shell input swipe 500 1200 500 400
sleep 2
adb -s 127.0.0.1:16416 shell screencap -p > $WORKDIR/02_市场情绪_中段.png
echo "  - 已保存: 02_市场情绪_中段.png"

# ===== 2. 涨停表现-二板详情 =====
echo "[2/5] 进入涨停表现-二板详情..."
# 点击二板(3)
/opt/homebrew/bin/adb -s 127.0.0.1:16416 shell input tap 343 1146
sleep 3
adb -s 127.0.0.1:16416 shell screencap -p > $WORKDIR/03_涨停表现_二板.png
echo "  - 已保存: 03_涨停表现_二板.png"

# 返回涨停表现列表
adb -s 127.0.0.1:16416 shell input keyevent 4
sleep 2

# ===== 3. 涨停表现-更高详情 =====
echo "[3/5] 进入涨停表现-更高详情..."
adb -s 127.0.0.1:16416 shell input tap 550 200  # 更高tab
sleep 3
adb -s 127.0.0.1:16416 shell screencap -p > $WORKDIR/04_涨停表现_更高.png
echo "  - 已保存: 04_涨停表现_更高.png"

# 返回
adb -s 127.0.0.1:16416 shell input keyevent 4
sleep 1
adb -s 127.0.0.1:16416 shell input keyevent 4
sleep 1

# ===== 4. 行情-板块 =====
echo "[4/5] 进入行情-板块..."
adb -s 127.0.0.1:16416 shell input tap 270 1520
sleep 4
adb -s 127.0.0.1:16416 shell screencap -p > $WORKDIR/05_行情_板块.png
echo "  - 已保存: 05_行情_板块.png"

# ===== 5. 打板 =====
echo "[5/5] 进入打板..."
adb -s 127.0.0.1:16416 shell input tap 336 130
sleep 3
adb -s 127.0.0.1:16416 shell screencap -p > $WORKDIR/06_打板.png
echo "  - 已保存: 06_打板.png"

echo "========== $(date) 盘后采集完成 =========="
echo "文件位置: $WORKDIR"
ls -la $WORKDIR