#!/usr/bin/env python3
"""
冰点修复策略 v3.0 - 含真实收益
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
ETF_CODE = "510300.SH"  # 沪深300ETF

# ==================== 数据路径 ====================
EMOTION_DATA_PATH = "/Users/macclaw/.openclaw/workspace/emotion-kline/emotion-data.json"
ETF_DATA_PATH = "/tmp/kaipanla/etf_510300.json"

# ==================== ETF数据 ====================
ETF_DATA = [
    {"date": "2026-03-25", "open": 4.51, "high": 4.549, "low": 4.504, "close": 4.544},
    {"date": "2026-03-26", "open": 4.536, "high": 4.547, "low": 4.477, "close": 4.488},
    {"date": "2026-03-27", "open": 4.45, "high": 4.53, "low": 4.445, "close": 4.508},
    {"date": "2026-03-30", "open": 4.462, "high": 4.505, "low": 4.453, "close": 4.5},
    {"date": "2026-03-31", "open": 4.501, "high": 4.529, "low": 4.462, "close": 4.463},
    {"date": "2026-04-01", "open": 4.52, "high": 4.542, "low": 4.501, "close": 4.534},
    {"date": "2026-04-02", "open": 4.521, "high": 4.526, "low": 4.47, "close": 4.489},
    {"date": "2026-04-03", "open": 4.495, "high": 4.506, "low": 4.446, "close": 4.454},
]

# ==================== 策略逻辑 ====================

class IcePointETFStrategy:
    """冰点修复策略 - ETF版"""
    
    def __init__(self):
        self.emotion_data = []
        self.load_data()
    
    def load_data(self):
        """加载数据"""
        try:
            with open(EMOTION_DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.emotion_data = data.get('days', [])
                print(f"✅ 加载情绪数据: {len(self.emotion_data)}天")
        except Exception as e:
            print(f"❌ 加载情绪数据失败: {e}")
        
        print(f"✅ 加载ETF数据: {len(ETF_DATA)}天")
    
    def get_etf_price(self, date: str) -> Optional[Dict]:
        """获取指定日期的ETF价格"""
        for d in ETF_DATA:
            if d['date'] == date:
                return d
        return None
    
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
    
    def run_backtest(self):
        """
        运行回测，计算真实收益
        """
        ice_points = self.find_ice_points()
        
        if not ice_points:
            print("❌ 没有找到冰点日")
            return []
        
        print(f"\n📊 找到 {len(ice_points)} 个冰点日")
        
        trades = []
        total_return = 0.0
        win_count = 0
        
        for ice in ice_points:
            print(f"\n{'='*50}")
            print(f"冰点日: {ice['date']} (最低{ice['low']}分)")
            
            # 获取次日情绪数据
            next_day = self.get_next_day(ice['date'])
            if not next_day:
                print(f"  → 无次日情绪数据")
                continue
            
            next_open = next_day.get('open', 0)
            print(f"  → 次日 {next_day['date']}: 开盘{next_open}分")
            
            # 检查是否触发卖出
            if next_open < REPAIR_TARGET:
                print(f"  → 情绪未修复({next_open}<{REPAIR_TARGET})")
                print(f"  → 继续持有（不计入统计）")
                continue
            
            # 计算交易收益
            # 买入：冰点日收盘价
            # 卖出：次日开盘价
            buy_etf = self.get_etf_price(ice['date'])
            sell_etf = self.get_etf_price(next_day['date'])
            
            if not buy_etf or not sell_etf:
                print(f"  → 无ETF价格数据")
                continue
            
            buy_price = buy_etf['close']  # 冰点日收盘买入
            sell_price = sell_etf['open']  # 次日开盘卖出
            
            ret = (sell_price - buy_price) / buy_price * 100
            total_return += ret
            
            if ret > 0:
                win_count += 1
            
            trades.append({
                'buy_date': ice['date'],
                'buy_price': buy_price,
                'sell_date': next_day['date'],
                'sell_price': sell_price,
                'return': ret,
                'ice_low': ice['low'],
                'next_open': next_open
            })
            
            print(f"  📈 买入: {buy_price:.3f} (收盘)")
            print(f"  📉 卖出: {sell_price:.3f} (开盘)")
            print(f"  💰 收益: {ret:+.2f}%")
        
        # 统计
        if trades:
            avg_return = total_return / len(trades)
            win_rate = win_count / len(trades) * 100
            print(f"\n{'='*50}")
            print(f"📊 回测统计")
            print(f"{'='*50}")
            print(f"交易次数: {len(trades)}")
            print(f"总收益: {total_return:+.2f}%")
            print(f"平均收益: {avg_return:+.2f}%")
            print(f"胜率: {win_rate:.1f}%")
        
        return trades
    
    def generate_daily_signal(self, trade_date: str) -> Dict:
        """生成当日交易信号"""
        signal = {
            'date': trade_date,
            'action': '观望',
            'target': '510300',
            'reason': ''
        }
        
        # 检查是否是冰点日
        for day in self.emotion_data:
            if day['date'] == trade_date:
                low = day.get('low', 100)
                if low <= ICE_POINT:
                    signal['action'] = '买入'
                    signal['reason'] = f'情绪冰点({low}≤{ICE_POINT})'
                break
        
        # 检查是否是卖出时机
        yesterday = (datetime.strptime(trade_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        for ice in self.find_ice_points():
            if ice['date'] == yesterday:
                today_data = self.get_next_day(yesterday)
                if today_data:
                    today_open = today_data.get('open', 0)
                    if today_open >= REPAIR_TARGET:
                        signal['action'] = '卖出'
                        signal['reason'] = f'情绪修复({today_open}>{REPAIR_TARGET})'
                    else:
                        signal['action'] = '持有'
                        signal['reason'] = f'情绪未修复({today_open}<{REPAIR_TARGET})'
                break
        
        return signal
    
    def print_signal(self, trade_date: str):
        """打印交易信号"""
        signal = self.generate_daily_signal(trade_date)
        
        emoji = {'买入': '🟢', '卖出': '🔴', '持有': '🟡', '观望': '⚪️'}
        
        print(f"\n{'='*50}")
        print(f"📊 {trade_date} 冰点ETF策略信号")
        print(f"{'='*50}")
        print(f"操作: {emoji.get(signal['action'], '')} {signal['action']}")
        print(f"标的: {signal['target']}")
        print(f"理由: {signal['reason']}")


def main():
    """主函数"""
    strategy = IcePointETFStrategy()
    
    print("="*50)
    print("冰点修复策略 v3.0 - 含真实收益")
    print(f"标的: 沪深300ETF (510300)")
    print(f"冰点阈值: {ICE_POINT}分")
    print(f"修复目标: {REPAIR_TARGET}分")
    print("="*50)
    
    # 打印每日信号
    recent_dates = [d['date'] for d in strategy.emotion_data[-5:]]
    for date in recent_dates:
        strategy.print_signal(date)
    
    # 运行回测
    if len(strategy.emotion_data) >= 5:
        print("\n" + "="*50)
        print("📈 历史回测（含真实收益）")
        print("="*50)
        strategy.run_backtest()


if __name__ == "__main__":
    main()
