#!/usr/bin/env python3
"""
每日盘后报告生成器
自动采集数据、导入数据库、生成报告、输出策略信号
"""

import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = "/Users/macclaw/.openclaw/workspace/database/kaipanla.db"
DAILY_DIR = "/tmp/kaipanla/daily"
WORKSPACE = "/Users/macclaw/.openclaw/workspace"

class DailyReporter:
    """每日报告生成器"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def get_market_summary(self):
        """获取市场概况"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT trade_date, index_value, index_change,
                   up_count, down_count, limit_up_count, limit_down_count,
                   total_volume, volume_change_pct, sentiment_score
            FROM daily_market
            ORDER BY trade_date DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'trade_date': row[0],
            'index_value': row[1],
            'index_change': row[2],
            'up_count': row[3],
            'down_count': row[4],
            'limit_up_count': row[5],
            'limit_down_count': row[6],
            'total_volume': row[7],
            'volume_change_pct': row[8],
            'sentiment_score': row[9]
        }
    
    def get_lianban_summary(self):
        """获取连板统计"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT yiban_count, erban_count, sanban_count, 
                   sibanshi_count, gaogeng_count, erban_rate,
                   max_lianban_stock, max_lianban_days
            FROM daily_lianban_stats
            ORDER BY trade_date DESC
            LIMIT 1
        """)
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
            'max_lianban_stock': row[6],
            'max_lianban_days': row[7]
        }
    
    def get_top_sectors(self, limit=5):
        """获取强势板块"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT sector_name, strength, main_net_inflow, inst_increase
            FROM daily_sector
            WHERE trade_date = (SELECT MAX(trade_date) FROM daily_sector)
            ORDER BY strength DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [{'name': r[0], 'strength': r[1], 'main_net': r[2], 'inst': r[3]} for r in rows]
    
    def get_limit_up_stocks(self, limit=10):
        """获取涨停个股"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT stock_name, stock_code, lianban_days, board_reason, seal_amount
            FROM daily_limit_up
            WHERE trade_date = (SELECT MAX(trade_date) FROM daily_limit_up)
            ORDER BY seal_amount DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [{'name': r[0], 'code': r[1], 'days': r[2], 'board': r[3], 'seal': r[4]} for r in rows]
    
    def get_daban_summary(self):
        """获取打板统计"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT limit_up_count, limit_up_yesterday, seal_rate, 
                   limit_down_count, limit_down_yesterday
            FROM daily_daban
            ORDER BY trade_date DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'limit_up': row[0],
            'limit_up_yest': row[1],
            'seal_rate': row[2],
            'limit_down': row[3],
            'limit_down_yest': row[4]
        }
    
    def calc_signal(self, market, lianban):
        """计算策略信号"""
        sentiment = market.get('sentiment_score', 50)
        yiban = lianban.get('yiban_count', 0)
        erban = lianban.get('erban_count', 0)
        
        lianban_rate = (erban / yiban * 100) if yiban > 0 else 0
        
        # 情绪信号
        if sentiment <= 25:
            sentiment_signal = "🧊冰点"
            sentiment_desc = "逆向布局区"
        elif sentiment <= 40:
            sentiment_signal = "📉偏冷"
            sentiment_desc = "谨慎观察"
        elif sentiment <= 55:
            sentiment_signal = "📊正常"
            sentiment_desc = "标准操作"
        elif sentiment <= 75:
            sentiment_signal = "📈偏热"
            sentiment_desc = "积极参与"
        else:
            sentiment_signal = "⚠️过热"
            sentiment_desc = "警惕撤退"
        
        # 连板率信号
        if lianban_rate < 10:
            lianban_signal = "🧊冰点"
            lianban_desc = "关注强势股"
        elif lianban_rate < 25:
            lianban_signal = "📉偏低"
            lianban_desc = "谨慎操作"
        elif lianban_rate < 40:
            lianban_signal = "📊正常"
            lianban_desc = "顺势而为"
        elif lianban_rate < 60:
            lianban_signal = "📈偏热"
            lianban_desc = "积极参与"
        else:
            lianban_signal = "⚠️过热"
            lianban_desc = "警惕撤退"
        
        # 仓位
        if sentiment <= 25 and lianban_rate < 10:
            position = 60
        elif sentiment <= 40 or lianban_rate < 25:
            position = 40
        elif sentiment <= 55 and lianban_rate < 40:
            position = 50
        elif sentiment >= 75 or lianban_rate >= 60:
            position = 20
        else:
            position = 50
        
        return {
            'sentiment_signal': sentiment_signal,
            'sentiment_desc': sentiment_desc,
            'lianban_signal': lianban_signal,
            'lianban_desc': lianban_desc,
            'lianban_rate': lianban_rate,
            'position': position
        }
    
    def generate_report(self):
        """生成完整报告"""
        market = self.get_market_summary()
        lianban = self.get_lianban_summary()
        sectors = self.get_top_sectors(5)
        stocks = self.get_limit_up_stocks(10)
        daban = self.get_daban_summary()
        signal = self.calc_signal(market, lianban) if market and lianban else None
        
        report = f"""
{'='*60}
📊 每日盘后报告 - {self.today}
{'='*60}

【市场概况】
指数: {market['index_value']} ({market['index_change']:+.2f}%)
涨跌: {market['up_count']} / {market['down_count']}
涨停/跌停: {market['limit_up_count']} / {market['limit_down_count']}
量能: {market['total_volume']}亿 ({market['volume_change_pct']:+.2f}%)

【连板梯队】
一板: {lianban['yiban_count']} | 二板: {lianban['erban_count']} | 三板: {lianban['sanban_count']}
更高板: {lianban['gaogeng_count']} (最高{lianban['max_lianban_days']}连板: {lianban['max_lianban_stock']})
连板率: {signal['lianban_rate']:.2f}% {signal['lianban_signal']}

【打板统计】
涨停: {daban['limit_up']} (昨日{daban['limit_up_yest']})
封板率: {daban['seal_rate']}%
跌停: {daban['limit_down']} (昨日{daban['limit_down_yest']})

【强势板块 TOP5】
"""
        for i, s in enumerate(sectors, 1):
            report += f"  {i}. {s['name']} (强度:{s['strength']}, 主力:{s['main_net']/10000:.1f}亿)\n"
        
        report += f"""
【涨停个股 TOP10】
"""
        for i, s in enumerate(stocks, 1):
            board = s['board'][:15] if s['board'] else ''
            report += f"  {i}. {s['name']}({s['code']}) {s['days']}板 {board}\n"
        
        if signal:
            report += f"""
{'='*60}
🎯 策略信号
{'='*60}
情绪分数: {market['sentiment_score']} {signal['sentiment_signal']}
  → {signal['sentiment_desc']}

连板率: {signal['lianban_rate']:.2f}% {signal['lianban_signal']}
  → {signal['lianban_desc']}

推荐仓位: {signal['position']}%

综合判断: {'偏多' if signal['position'] >= 50 else '偏空'}
{'='*60}
"""
        
        return report
    
    def save_report(self):
        """保存报告到文件"""
        report = self.generate_report()
        
        # 保存为markdown
        date_str = datetime.now().strftime("%Y%m%d")
        daily_dir = os.path.join(WORKSPACE, f"daily_{date_str}")
        os.makedirs(daily_dir, exist_ok=True)
        
        report_path = os.path.join(daily_dir, f"盘后报告_{date_str}.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report_path, report
    
    def close(self):
        self.conn.close()


def main():
    """主函数"""
    print("生成每日盘后报告...")
    
    reporter = DailyReporter()
    
    # 检查是否有今日数据
    market = reporter.get_market_summary()
    if not market:
        print("❌ 今日数据未入库，请先运行采集脚本")
        sys.exit(1)
    
    # 生成并保存报告
    report_path, report = reporter.save_report()
    
    # 打印报告
    print(report)
    print(f"\n✅ 报告已保存: {report_path}")
    
    reporter.close()


if __name__ == "__main__":
    main()
