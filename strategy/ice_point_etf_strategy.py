#!/usr/bin/env python3
"""
冰点修复策略 v2.0
标的：沪深300ETF（510300）

核心逻辑：
- 冰点日（情绪≤25）买入ETF
- 次日情绪修复（>40）卖出
- 赚取大盘反弹的平均收益
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ==================== 策略参数 ====================
ICE_POINT = 25           # 冰点阈值
REPAIR_TARGET = 40      # 修复目标（卖出参考）
HOLD_DEADLINE = "10:00" # 最晚持有时间
STOP_LOSS = -3         # 止损线（%）

# ETF标的
ETF_CODE = "510300"     # 沪深300ETF
ETF_NAME = "沪深300ETF"

# ==================== 数据路径 ====================
EMOTION_DATA_PATH = "/Users/macclaw/.openclaw/workspace/emotion-kline/emotion-data.json"
ETF_DATA_PATH = "/tmp/kaipanla/etf_510300.csv"  # 需要接入实时数据

# ==================== 策略逻辑 ====================

class IcePointETFStrategy:
    """冰点修复策略 - ETF版"""
    
    def __init__(self):
        self.emotion_data = []
        self.etf_data = []
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
    
    def get_next_day(self, ice_date: str) -> Optional[Dict]:
        """获取冰点日后一天的数据"""
        ice_dt = datetime.strptime(ice_date, '%Y-%m-%d')
        next_date = (ice_dt + timedelta(days=1)).strftime('%Y-%m-%d')
        
        for day in self.emotion_data:
            if day['date'] == next_date:
                return day
        return None
    
    def simulate_trade(self, buy_date: str, sell_date: str, buy_price: float) -> Dict:
        """
        模拟交易（需要ETF价格数据）
        
        参数：
        - buy_date: 买入日期
        - sell_date: 卖出日期
        - buy_price: 买入价格
        
        返回：交易结果
        """
        # TODO: 接入ETF实际价格数据
        # 目前只是框架，数据积累后可计算真实收益
        
        return {
            'buy_date': buy_date,
            'sell_date': sell_date,
            'buy_price': buy_price,
            'sell_price': None,  # 待数据
            'return': None,
            'holding_days': 1
        }
    
    def run_backtest(self):
        """
        运行回测（需要有ETF价格数据）
        
        策略信号：
        - 买入：冰点日收盘前买入ETF
        - 卖出：次日开盘情绪>40 OR 10:00前 OR 跌3%止损
        """
        ice_points = self.find_ice_points()
        
        if not ice_points:
            print("❌ 没有找到冰点日")
            return
        
        print(f"\n📊 找到 {len(ice_points)} 个冰点日")
        
        trades = []
        for ice in ice_points:
            print(f"\n冰点日: {ice['date']} (最低{ice['low']}分)")
            
            # 获取次日数据
            next_day = self.get_next_day(ice['date'])
            if not next_day:
                print(f"  → 无次日数据")
                continue
            
            print(f"  → 次日 {next_day['date']}: 开盘{next_day.get('open', '?')}分")
            
            # 计算信号
            next_open = next_day.get('open', 0)
            if next_open >= REPAIR_TARGET:
                print(f"  → 情绪已修复({next_open}>{REPAIR_TARGET})")
                print(f"  → 卖出信号: 开盘卖出")
                trades.append({
                    'ice_date': ice['date'],
                    'ice_low': ice['low'],
                    'sell_date': next_day['date'],
                    'signal': '情绪修复卖出'
                })
            else:
                print(f"  → 情绪未修复({next_open}<{REPAIR_TARGET})")
                print(f"  → 继续持有或止损")
        
        return trades
    
    def generate_daily_signal(self, trade_date: str) -> Dict:
        """
        生成当日交易信号
        """
        signal = {
            'date': trade_date,
            'action': '观望',  # 买入/卖出/观望
            'target': None,
            'reason': ''
        }
        
        # 检查是否是冰点日
        for day in self.emotion_data:
            if day['date'] == trade_date:
                low = day.get('low', 100)
                if low <= ICE_POINT:
                    signal['action'] = '买入'
                    signal['target'] = ETF_CODE
                    signal['reason'] = f'情绪冰点({low}≤{ICE_POINT})'
                break
        
        # 检查是否是卖出时机（昨日冰点，今日开盘情绪修复）
        yesterday = (datetime.strptime(trade_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        for ice in self.find_ice_points():
            if ice['date'] == yesterday:
                # 昨日是冰点
                today_data = self.get_next_day(yesterday)
                if today_data:
                    today_open = today_data.get('open', 0)
                    if today_open >= REPAIR_TARGET:
                        signal['action'] = '卖出'
                        signal['target'] = ETF_CODE
                        signal['reason'] = f'情绪修复({today_open}>{REPAIR_TARGET})'
                    else:
                        signal['action'] = '持有'
                        signal['reason'] = f'情绪未修复({today_open}<{REPAIR_TARGET})'
                break
        
        return signal
    
    def print_signal(self, trade_date: str):
        """打印交易信号"""
        signal = self.generate_daily_signal(trade_date)
        
        emoji = {
            '买入': '🟢',
            '卖出': '🔴',
            '持有': '🟡',
            '观望': '⚪️'
        }
        
        print(f"\n{'='*50}")
        print(f"📊 {trade_date} 冰点ETF策略信号")
        print(f"{'='*50}")
        print(f"操作: {emoji.get(signal['action'], '')} {signal['action']}")
        print(f"标的: {signal['target'] or '-'}")
        print(f"理由: {signal['reason']}")


def main():
    """主函数"""
    strategy = IcePointETFStrategy()
    
    print("="*50)
    print("冰点修复策略 v2.0 - ETF版")
    print(f"标的: {ETF_NAME} ({ETF_CODE})")
    print(f"冰点阈值: {ICE_POINT}分")
    print(f"修复目标: {REPAIR_TARGET}分")
    print("="*50)
    
    # 检查数据量
    if len(strategy.emotion_data) < 10:
        print(f"\n⚠️ 数据量不足: {len(strategy.emotion_data)}天")
        print("   建议积累更多数据后再回测")
    
    # 打印最近信号
    recent_dates = [d['date'] for d in strategy.emotion_data[-5:]]
    for date in recent_dates:
        strategy.print_signal(date)
    
    # 运行回测
    if len(strategy.emotion_data) >= 5:
        print("\n" + "="*50)
        print("📈 历史冰点统计")
        print("="*50)
        trades = strategy.run_backtest()
        print(f"\n共找到 {len(trades)} 次冰点后的卖出信号")


if __name__ == "__main__":
    main()
