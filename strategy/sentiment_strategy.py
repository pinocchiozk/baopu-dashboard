#!/usr/bin/env python3
"""
连板率择时 + 情绪周期策略
基于开盘啦数据的量化交易策略
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

DB_PATH = "/Users/macclaw/.openclaw/workspace/database/kaipanla.db"

class SentimentStrategy:
    """情绪周期择时策略"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path)
    
    def get_market_data(self, trade_date: str) -> Optional[Dict]:
        """获取指定日期的市场数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT trade_date, sentiment_score, limit_up_count, limit_down_count,
                   up_count, down_count, total_volume, volume_change_pct
            FROM daily_market
            WHERE trade_date = ?
        """, (trade_date,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'trade_date': row[0],
            'sentiment_score': row[1],
            'limit_up_count': row[2],
            'limit_down_count': row[3],
            'up_count': row[4],
            'down_count': row[5],
            'total_volume': row[6],
            'volume_change_pct': row[7]
        }
    
    def get_lianban_data(self, trade_date: str) -> Optional[Dict]:
        """获取指定日期的连板数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT yiban_count, erban_count, sanban_count, sibanshi_count,
                   gaogeng_count, erban_rate, max_lianban_days, max_lianban_stock
            FROM daily_lianban_stats
            WHERE trade_date = ?
        """, (trade_date,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'yiban_count': row[0],
            'erban_count': row[1],
            'sanban_count': row[2],
            'sibanshi_count': row[3],
            'gaogeng_count': row[4],
            'erban_rate': row[5],
            'max_lianban_days': row[6],
            'max_lianban_stock': row[7]
        }
    
    def get_sentiment_data(self, trade_date: str) -> Optional[Dict]:
        """获取情绪指标数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT break_board_rate, yesterday_up_today_return,
                   yesterday_lianban_today_return, yesterday_break_today_return
            FROM daily_sentiment
            WHERE trade_date = ?
        """, (trade_date,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'break_board_rate': row[0],
            'yesterday_up_today_return': row[1],
            'yesterday_lianban_today_return': row[2],
            'yesterday_break_today_return': row[3]
        }
    
    def calc_lianban_rate(self, lianban_data: Dict) -> float:
        """计算连板率"""
        if lianban_data['yiban_count'] == 0:
            return 0.0
        return lianban_data['erban_count'] / lianban_data['yiban_count'] * 100
    
    def calc_clsi(self, lianban_data: Dict) -> float:
        """
        计算综合连板强度指数 (Composite Lianban Strength Index)
        加权考虑各梯队连板数量
        """
        w = [0, 1, 2, 3, 4, 5]  # 一板到更高板的权重
        counts = [
            lianban_data['yiban_count'],
            lianban_data['erban_count'],
            lianban_data['sanban_count'],
            lianban_data['sibanshi_count'],
            lianban_data['gaogeng_count']
        ]
        total = sum(c * w[i] for i, c in enumerate(counts))
        if lianban_data['yiban_count'] == 0:
            return 0.0
        return total / lianban_data['yiban_count'] * 100
    
    def get_sentiment_signal(self, sentiment_score: int) -> Tuple[str, str]:
        """根据情绪分数判断信号"""
        if sentiment_score <= 25:
            return "🧊冰点", "逆向布局区"
        elif sentiment_score <= 40:
            return "📉偏冷", "谨慎观察"
        elif sentiment_score <= 55:
            return "📊正常", "标准操作"
        elif sentiment_score <= 75:
            return "📈偏热", "积极参与"
        else:
            return "⚠️过热", "警惕撤退"
    
    def get_lianban_signal(self, lianban_rate: float) -> Tuple[str, str]:
        """根据连板率判断信号"""
        if lianban_rate < 10:
            return "🧊冰点", "关注强势股"
        elif lianban_rate < 25:
            return "📉偏低", "谨慎操作"
        elif lianban_rate < 40:
            return "📊正常", "顺势而为"
        elif lianban_rate < 60:
            return "📈偏热", "积极参与"
        else:
            return "⚠️过热", "警惕撤退"
    
    def get_position(self, sentiment_score: int, lianban_rate: float) -> int:
        """
        根据情绪分数和连板率确定仓位
        返回: 0-100 (百分比)
        """
        signal_sentiment, _ = self.get_sentiment_signal(sentiment_score)
        signal_lianban, _ = self.get_lianban_signal(lianban_rate)
        
        # 仓位映射表
        position_map = {
            ("🧊冰点", "🧊冰点"): 60,
            ("🧊冰点", "📉偏低"): 40,
            ("🧊冰点", "📊正常"): 50,
            ("🧊冰点", "📈偏热"): 30,
            ("🧊冰点", "⚠️过热"): 20,
            ("📉偏冷", "🧊冰点"): 40,
            ("📉偏冷", "📉偏低"): 30,
            ("📉偏冷", "📊正常"): 40,
            ("📉偏冷", "📈偏热"): 30,
            ("📉偏冷", "⚠️过热"): 20,
            ("📊正常", "🧊冰点"): 50,
            ("📊正常", "📉偏低"): 50,
            ("📊正常", "📊正常"): 50,
            ("📊正常", "📈偏热"): 60,
            ("📊正常", "⚠️过热"): 40,
            ("📈偏热", "🧊冰点"): 50,
            ("📈偏热", "📉偏低"): 40,
            ("📈偏热", "📊正常"): 60,
            ("📈偏热", "📈偏热"): 70,
            ("📈偏热", "⚠️过热"): 50,
            ("⚠️过热", "🧊冰点"): 30,
            ("⚠️过热", "📉偏低"): 20,
            ("⚠️过热", "📊正常"): 30,
            ("⚠️过热", "📈偏热"): 40,
            ("⚠️过热", "⚠️过热"): 20,
        }
        
        return position_map.get((signal_sentiment, signal_lianban), 50)
    
    def get_daily_signal(self, trade_date: str) -> Dict:
        """
        获取指定日期的综合交易信号
        """
        market = self.get_market_data(trade_date)
        lianban = self.get_lianban_data(trade_date)
        sentiment = self.get_sentiment_data(trade_date)
        
        if not market or not lianban:
            return {
                'trade_date': trade_date,
                'error': '数据不足',
                'position': 0
            }
        
        lianban_rate = self.calc_lianban_rate(lianban)
        clsi = self.calc_clsi(lianban)
        
        sentiment_signal, sentiment_desc = self.get_sentiment_signal(market['sentiment_score'])
        lianban_signal, lianban_desc = self.get_lianban_signal(lianban_rate)
        
        position = self.get_position(market['sentiment_score'], lianban_rate)
        
        return {
            'trade_date': trade_date,
            # 市场数据
            'sentiment_score': market['sentiment_score'],
            'limit_up_count': market['limit_up_count'],
            'limit_down_count': market['limit_down_count'],
            # 连板数据
            'yiban_count': lianban['yiban_count'],
            'erban_count': lianban['erban_count'],
            'lianban_rate': round(lianban_rate, 2),
            'clsi': round(clsi, 2),
            'max_lianban_days': lianban['max_lianban_days'],
            'max_lianban_stock': lianban['max_lianban_stock'],
            # 信号
            'sentiment_signal': sentiment_signal,
            'sentiment_desc': sentiment_desc,
            'lianban_signal': lianban_signal,
            'lianban_desc': lianban_desc,
            # 仓位
            'position': position,
            # 情绪指标（如果有）
            'break_board_rate': sentiment['break_board_rate'] if sentiment else None,
            'yesterday_up_return': sentiment['yesterday_up_today_return'] if sentiment else None,
        }
    
    def get_trend_analysis(self, days: int = 5) -> List[Dict]:
        """
        获取最近N日的趋势分析
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT trade_date, sentiment_score
            FROM daily_market
            ORDER BY trade_date DESC
            LIMIT ?
        """, (days,))
        
        rows = cursor.fetchall()
        if not rows:
            return []
        
        results = []
        for trade_date, score in rows:
            signal = self.get_daily_signal(trade_date)
            results.append(signal)
        
        return results
    
    def print_signal_report(self, trade_date: str):
        """打印指定日期的信号报告"""
        signal = self.get_daily_signal(trade_date)
        
        print(f"\n{'='*60}")
        print(f"📊 {trade_date} 每日信号报告")
        print(f"{'='*60}")
        
        if 'error' in signal:
            print(f"❌ {signal['error']}")
            return
        
        print(f"\n【市场情绪】")
        print(f"  情绪分数: {signal['sentiment_score']} {signal['sentiment_signal']}")
        print(f"  市场描述: {signal['sentiment_desc']}")
        print(f"  涨停/跌停: {signal['limit_up_count']} / {signal['limit_down_count']}")
        
        print(f"\n【连板数据】")
        print(f"  一板/二板: {signal['yiban_count']} / {signal['erban_count']}")
        print(f"  连板率: {signal['lianban_rate']}% {signal['lianban_signal']}")
        print(f"  CLSI指数: {signal['clsi']}")
        print(f"  最高板: {signal['max_lianban_days']}连板 ({signal['max_lianban_stock']})")
        
        print(f"\n【综合信号】")
        print(f"  连板描述: {signal['lianban_desc']}")
        print(f"  推荐仓位: {signal['position']}%")
        
        if signal.get('break_board_rate'):
            print(f"\n【情绪指标】")
            print(f"  破板率: {signal['break_board_rate']}%")
            print(f"  昨日涨停今表现: {signal['yesterday_up_return']}%")
        
        print(f"\n{'='*60}")


def main():
    """主函数"""
    strategy = SentimentStrategy()
    
    # 今日信号
    today = "2026-04-03"
    strategy.print_signal_report(today)
    
    # 最近5日趋势
    print("\n\n【最近5日趋势】")
    print("-" * 60)
    print(f"{'日期':<12} {'情绪':<8} {'连板率':<10} {'仓位':<6} {'最高板'}")
    print("-" * 60)
    
    trend = strategy.get_trend_analysis(5)
    for s in trend:
        if 'error' not in s:
            print(f"{s['trade_date']:<12} {s['sentiment_signal']:<8} {s['lianban_rate']:<10} {s['position']:<6} {s['max_lianban_days']}连板")


if __name__ == "__main__":
    main()
