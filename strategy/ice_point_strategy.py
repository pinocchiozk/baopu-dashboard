#!/usr/bin/env python3
"""
冰点修复策略
核心逻辑：情绪冰点后次日情绪修复，套利卖出

使用说明：
1. 需要积累至少30天数据才能跑有效回测
2. 当前只有5天情绪数据，策略框架仅供参考
3. 数据积累后运行: python ice_point_strategy.py
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ==================== 策略参数 ====================
ICE_POINT = 25          # 冰点阈值
REPAIR_TARGET = 40      # 修复目标（卖出参考）
HOLD_DEADLINE = "10:00" # 最晚持有时间
STOP_LOSS = -5         # 止损线（%）
MIN_LIANBAN = 2        # 最小连板数

# ==================== 数据路径 ====================
EMOTION_DATA_PATH = "/Users/macclaw/.openclaw/workspace/emotion-kline/emotion-data.json"
DB_PATH = "/Users/macclaw/.openclaw/workspace/database/kaipanla.db"

# ==================== 策略逻辑 ====================

class IcePointStrategy:
    """冰点修复策略"""
    
    def __init__(self):
        self.emotion_data = []
        self.trades = []  # 交易记录
        self.load_data()
    
    def load_data(self):
        """加载数据"""
        # 加载情绪K线数据
        try:
            with open(EMOTION_DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.emotion_data = data.get('days', [])
                print(f"✅ 加载情绪数据: {len(self.emotion_data)}天")
        except Exception as e:
            print(f"❌ 加载情绪数据失败: {e}")
        
        # 加载涨停数据（如果有）
        # TODO: 从SQLite数据库加载涨停明细
    
    def find_ice_points(self) -> List[Dict]:
        """找出所有冰点日"""
        ice_points = []
        for day in self.emotion_data:
            low = day.get('low', 0)
            if low <= ICE_POINT:
                ice_points.append({
                    'date': day['date'],
                    'low': low,
                    'close': day.get('close', 0)
                })
        return ice_points
    
    def get_next_day_emotion(self, ice_date: str) -> Optional[Dict]:
        """获取冰点日后一天的情绪数据"""
        ice_dt = datetime.strptime(ice_date, '%Y-%m-%d')
        next_date = (ice_dt + timedelta(days=1)).strftime('%Y-%m-%d')
        
        for day in self.emotion_data:
            if day['date'] == next_date:
                return day
        return None
    
    def run_backtest(self):
        """
        运行回测（需要有历史数据）
        
        策略信号：
        - 买入：冰点日收盘前买入
        - 卖出：次日开盘情绪>40 OR 10:00前 OR 跌5%止损
        """
        ice_points = self.find_ice_points()
        
        if not ice_points:
            print("❌ 没有找到冰点日")
            return
        
        print(f"\n📊 找到 {len(ice_points)} 个冰点日")
        
        # 模拟回测
        for ice in ice_points:
            print(f"\n冰点日: {ice['date']} (最低{ice['low']}分)")
            
            # 获取次日数据
            next_day = self.get_next_day_emotion(ice['date'])
            if not next_day:
                print(f"  → 无次日数据")
                continue
            
            print(f"  → 次日 {next_day['date']}: 开盘{next_day.get('open', '?')}分")
            
            # 模拟卖出信号
            next_open = next_day.get('open', 0)
            if next_open >= REPAIR_TARGET:
                print(f"  → 情绪已修复({next_open}>{REPAIR_TARGET})，卖出信号")
            else:
                print(f"  → 情绪未修复({next_open}<{REPAIR_TARGET})，继续持有")
    
    def generate_signal(self, trade_date: str) -> Dict:
        """
        生成当日交易信号
        供每日盘后调用
        """
        signal = {
            'date': trade_date,
            'is_ice_point': False,
            'buy_candidates': [],
            'sell_signals': [],
            'recommendation': '观望'
        }
        
        # 检查是否是冰点日
        for day in self.emotion_data:
            if day['date'] == trade_date:
                if day.get('low', 100) <= ICE_POINT:
                    signal['is_ice_point'] = True
                    signal['recommendation'] = '关注冰点股，明日观察'
                break
        
        # 检查是否有卖出信号（昨日冰点，今日开盘情绪修复）
        yesterday = (datetime.strptime(trade_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        for day in self.emotion_data:
            if day['date'] == yesterday and day.get('low', 100) <= ICE_POINT:
                # 昨日是冰点
                today_data = None
                for d in self.emotion_data:
                    if d['date'] == trade_date:
                        today_data = d
                        break
                
                if today_data and today_data.get('open', 0) >= REPAIR_TARGET:
                    signal['sell_signals'].append({
                        'reason': f'情绪修复({today_data["open"]}>{REPAIR_TARGET})',
                        'action': '卖出'
                    })
                    signal['recommendation'] = '卖出'
        
        return signal
    
    def print_daily_report(self, trade_date: str):
        """打印每日策略报告"""
        signal = self.generate_signal(trade_date)
        
        print(f"\n{'='*50}")
        print(f"📊 冰点修复策略 - {trade_date}")
        print(f"{'='*50}")
        print(f"冰点日: {'是' if signal['is_ice_point'] else '否'}")
        print(f"卖出信号: {len(signal['sell_signals'])}个")
        print(f"操作建议: {signal['recommendation']}")
        
        if signal['sell_signals']:
            print("\n卖出理由:")
            for s in signal['sell_signals']:
                print(f"  - {s['reason']}")


def main():
    """主函数"""
    strategy = IcePointStrategy()
    
    print("="*50)
    print("冰点修复策略 v1.0")
    print("="*50)
    
    # 检查数据量
    if len(strategy.emotion_data) < 30:
        print(f"\n⚠️ 数据量不足: {len(strategy.emotion_data)}天")
        print("   建议积累至少30天数据后再跑回测")
        print()
    
    # 打印最近几天的报告
    recent_dates = [d['date'] for d in strategy.emotion_data[-5:]]
    for date in recent_dates:
        strategy.print_daily_report(date)
    
    # 运行简单回测
    if len(strategy.emotion_data) >= 5:
        print("\n" + "="*50)
        print("📈 历史冰点回测")
        print("="*50)
        strategy.run_backtest()


if __name__ == "__main__":
    main()
