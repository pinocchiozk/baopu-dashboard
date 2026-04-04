#!/usr/bin/env python3
"""
策略回测框架
用于验证连板率择时和情绪周期策略的有效性
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

DB_PATH = "/Users/macclaw/.openclaw/workspace/database/kaipanla.db"

class Backtest:
    """回测引擎"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path)
    
    def get_data_range(self, start_date: str, end_date: str) -> List[Dict]:
        """获取日期范围内的所有数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                m.trade_date,
                m.sentiment_score,
                m.limit_up_count,
                m.limit_down_count,
                m.up_count,
                m.down_count,
                m.total_volume,
                m.volume_change_pct,
                l.yiban_count,
                l.erban_count,
                l.sanban_count,
                l.gaogeng_count,
                l.erban_rate,
                l.max_lianban_days,
                l.max_lianban_stock,
                s.break_board_rate,
                s.yesterday_up_today_return,
                s.yesterday_lianban_today_return,
                s.yesterday_break_today_return
            FROM daily_market m
            LEFT JOIN daily_lianban_stats l ON m.trade_date = l.trade_date
            LEFT JOIN daily_sentiment s ON m.trade_date = s.trade_date
            WHERE m.trade_date BETWEEN ? AND ?
            ORDER BY m.trade_date
        """, (start_date, end_date))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'trade_date': row[0],
                'sentiment_score': row[1],
                'limit_up_count': row[2],
                'limit_down_count': row[3],
                'up_count': row[4],
                'down_count': row[5],
                'total_volume': row[6],
                'volume_change_pct': row[7],
                'yiban_count': row[8],
                'erban_count': row[9],
                'sanban_count': row[10],
                'gaogeng_count': row[11],
                'erban_rate': row[12],
                'max_lianban_days': row[13],
                'max_lianban_stock': row[14],
                'break_board_rate': row[15],
                'yesterday_up_return': row[16],
                'yesterday_lianban_return': row[17],
                'yesterday_break_return': row[18],
            })
        return results
    
    def get_next_day_return(self, trade_date: str) -> float:
        """获取指定日期下一个交易日的指数收益率"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT index_change FROM daily_market
            WHERE trade_date > ?
            ORDER BY trade_date
            LIMIT 1
        """, (trade_date,))
        row = cursor.fetchone()
        return row[0] if row else 0.0
    
    def calc_lianban_rate(self, yiban: int, erban: int) -> float:
        """计算连板率"""
        if yiban == 0:
            return 0.0
        return erban / yiban * 100
    
    def get_signal(self, data: Dict) -> Tuple[str, int]:
        """
        根据数据计算交易信号
        返回: (信号描述, 仓位)
        """
        sentiment = data.get('sentiment_score', 50)
        yiban = data.get('yiban_count', 0)
        erban = data.get('erban_count', 0)
        
        lianban_rate = self.calc_lianban_rate(yiban, erban)
        
        # 情绪信号
        if sentiment <= 25:
            sentiment_signal = "冰点"
        elif sentiment <= 40:
            sentiment_signal = "偏冷"
        elif sentiment <= 55:
            sentiment_signal = "正常"
        elif sentiment <= 75:
            sentiment_signal = "偏热"
        else:
            sentiment_signal = "过热"
        
        # 连板率信号
        if lianban_rate < 10:
            lianban_signal = "冰点"
        elif lianban_rate < 25:
            lianban_signal = "偏低"
        elif lianban_rate < 40:
            lianban_signal = "正常"
        elif lianban_rate < 60:
            lianban_signal = "偏热"
        else:
            lianban_signal = "过热"
        
        # 仓位
        position_map = {
            ("冰点", "冰点"): 60,
            ("冰点", "偏低"): 40,
            ("冰点", "正常"): 50,
            ("冰点", "偏热"): 30,
            ("冰点", "过热"): 20,
            ("偏冷", "冰点"): 40,
            ("偏冷", "偏低"): 30,
            ("偏冷", "正常"): 40,
            ("偏冷", "偏热"): 30,
            ("偏冷", "过热"): 20,
            ("正常", "冰点"): 50,
            ("正常", "偏低"): 50,
            ("正常", "正常"): 50,
            ("正常", "偏热"): 60,
            ("正常", "过热"): 40,
            ("偏热", "冰点"): 50,
            ("偏热", "偏低"): 40,
            ("偏热", "正常"): 60,
            ("偏热", "偏热"): 70,
            ("偏热", "过热"): 50,
            ("过热", "冰点"): 30,
            ("过热", "偏低"): 20,
            ("过热", "正常"): 30,
            ("过热", "偏热"): 40,
            ("过热", "过热"): 20,
        }
        
        position = position_map.get((sentiment_signal, lianban_signal), 50)
        
        signal = f"{sentiment_signal}+{lianban_signal}"
        return signal, position
    
    def run_backtest(self, start_date: str, end_date: str) -> Dict:
        """
        运行回测
        """
        data_list = self.get_data_range(start_date, end_date)
        
        if not data_list:
            return {'error': '没有数据'}
        
        trades = []
        position = 0
        cash = 100000  # 初始资金10万
        position_value = 0
        total_value = cash
        
        for i, data in enumerate(data_list):
            signal, target_position = self.get_signal(data)
            next_return = self.get_next_day_return(data['trade_date'])
            
            # 根据信号调整仓位
            if target_position != position:
                # 调仓
                if target_position > position:
                    # 加仓
                    add_ratio = (target_position - position) / 100
                    cost = total_value * add_ratio
                    cash -= cost
                else:
                    # 减仓
                    reduce_ratio = (position - target_position) / 100
                    proceeds = position_value * reduce_ratio
                    cash += proceeds
                position = target_position
            
            # 计算当日收益
            if position > 0:
                daily_return = next_return * position / 100
                total_value = cash + position_value * (1 + daily_return / 100)
            else:
                daily_return = 0
                total_value = cash
            
            trades.append({
                'trade_date': data['trade_date'],
                'signal': signal,
                'position': position,
                'next_return': next_return,
                'daily_return': daily_return if position > 0 else 0,
                'total_value': total_value
            })
        
        # 计算绩效指标
        returns = [t['daily_return'] for t in trades]
        total_return = (total_value - 100000) / 100000 * 100
        winning_days = sum(1 for r in returns if r > 0)
        total_days = len(returns)
        win_rate = winning_days / total_days * 100 if total_days > 0 else 0
        
        avg_win = sum(r for r in returns if r > 0) / winning_days if winning_days > 0 else 0
        avg_loss = sum(r for r in returns if r < 0) / (total_days - winning_days) if total_days > winning_days else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 最大回撤
        peak = 100000
        max_drawdown = 0
        for t in trades:
            if t['total_value'] > peak:
                peak = t['total_value']
            drawdown = (peak - t['total_value']) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_return': round(total_return, 2),
            'total_days': total_days,
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'final_value': round(total_value, 2),
            'trades': trades
        }
    
    def print_backtest_report(self, result: Dict):
        """打印回测报告"""
        if 'error' in result:
            print(f"❌ {result['error']}")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 回测报告: {result['start_date']} ~ {result['end_date']}")
        print(f"{'='*60}")
        
        print(f"\n【收益概览】")
        print(f"  总收益率: {result['total_return']}%")
        print(f"  最终资金: {result['final_value']:.2f}")
        print(f"  交易天数: {result['total_days']}天")
        
        print(f"\n【风险指标】")
        print(f"  最大回撤: {result['max_drawdown']}%")
        
        print(f"\n【胜率指标】")
        print(f"  胜率: {result['win_rate']}%")
        print(f"  平均盈利: {result['avg_win']}%")
        print(f"  平均亏损: {result['avg_loss']}%")
        print(f"  盈亏比: {result['profit_loss_ratio']}")
        
        print(f"\n【交易信号分布】")
        signal_stats = defaultdict(lambda: {'count': 0, 'avg_return': 0})
        for t in result['trades']:
            signal_stats[t['signal']]['count'] += 1
            signal_stats[t['signal']]['total_return'] = signal_stats[t['signal']].get('total_return', 0) + t['daily_return']
        
        for signal, stats in sorted(signal_stats.items()):
            avg_ret = stats.get('total_return', 0) / stats['count'] if stats['count'] > 0 else 0
            print(f"  {signal}: {stats['count']}次, 平均收益{avg_ret:.2f}%")
        
        print(f"\n{'='*60}")


def main():
    """主函数"""
    backtest = Backtest()
    
    # 运行回测（使用已有数据）
    result = backtest.run_backtest("2026-04-01", "2026-04-04")
    backtest.print_backtest_report(result)
    
    # 显示每日交易明细
    if 'trades' in result:
        print(f"\n【每日交易明细】")
        print(f"{'日期':<12} {'信号':<20} {'仓位':<8} {'次日收益':<10} {'总资产':<12}")
        print("-" * 70)
        for t in result['trades']:
            print(f"{t['trade_date']:<12} {t['signal']:<20} {t['position']:<8} {t['next_return']:<10} {t['total_value']:<12.2f}")


if __name__ == "__main__":
    main()
