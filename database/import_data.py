#!/usr/bin/env python3
"""
开盘啦数据导入脚本
将采集的截图数据导入SQLite数据库
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "/Users/macclaw/.openclaw/workspace/database/kaipanla.db"

def init_db():
    """初始化数据库"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 读取schema
    with open("/Users/macclaw/.openclaw/workspace/database/schema.sql", "r") as f:
        schema = f.read()
    
    cursor.executescript(schema)
    conn.commit()
    print(f"✅ 数据库初始化完成: {DB_PATH}")
    return conn

def import_daily_market(conn, data):
    """导入每日市场概况"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO daily_market (
            trade_date, index_name, index_value, index_change,
            up_count, down_count, flat_count,
            limit_up_count, limit_down_count,
            total_volume, volume_change, volume_change_pct,
            sentiment_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("trade_date"),
        data.get("index_name", "沪指"),
        data.get("index_value"),
        data.get("index_change"),
        data.get("up_count"),
        data.get("down_count"),
        data.get("flat_count", 0),
        data.get("limit_up_count"),
        data.get("limit_down_count"),
        data.get("total_volume"),
        data.get("volume_change"),
        data.get("volume_change_pct"),
        data.get("sentiment_score")
    ))
    conn.commit()
    print(f"  ✅ 市场概况已导入: {data.get('trade_date')}")

def import_lianban_stats(conn, data):
    """导入连板统计"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO daily_lianban_stats (
            trade_date, yiban_count, erban_count, erban_rate,
            sanban_count, sanban_rate, sibanshi_count, sibanshi_rate,
            gaogeng_count, gaogeng_rate, max_lianban_stock, max_lianban_days
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("trade_date"),
        data.get("yiban_count"),
        data.get("erban_count"),
        data.get("erban_rate"),
        data.get("sanban_count"),
        data.get("sanban_rate"),
        data.get("siban_count", 0),
        data.get("siban_rate", 0),
        data.get("gaogeng_count"),
        data.get("gaogeng_rate"),
        data.get("max_lianban_stock", ""),
        data.get("max_lianban_days", 0)
    ))
    conn.commit()
    print(f"  ✅ 连板统计已导入: {data.get('trade_date')}")

def import_limit_up(conn, trade_date, stocks):
    """导入涨停个股"""
    cursor = conn.cursor()
    for i, stock in enumerate(stocks, 1):
        cursor.execute("""
            INSERT OR REPLACE INTO daily_limit_up (
                trade_date, stock_name, stock_code, limit_time,
                board_reason, seal_amount, lianban_days, rank_no
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_date,
            stock.get("name"),
            stock.get("code"),
            stock.get("time", "09:30"),
            stock.get("board"),
            stock.get("seal_amount", 0),
            stock.get("lianban_days", 1),
            i
        ))
    conn.commit()
    print(f"  ✅ 涨停个股已导入: {len(stocks)}只")

def import_sector(conn, trade_date, sectors):
    """导入板块数据"""
    cursor = conn.cursor()
    for i, sector in enumerate(sectors, 1):
        cursor.execute("""
            INSERT OR REPLACE INTO daily_sector (
                trade_date, sector_code, sector_name,
                strength, main_net_inflow, inst_increase, rank_no
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_date,
            sector.get("code", ""),
            sector.get("name"),
            sector.get("strength", 0),
            sector.get("main_net", 0),
            sector.get("inst", 0),
            i
        ))
    conn.commit()
    print(f"  ✅ 板块数据已导入: {len(sectors)}个")

def import_daban(conn, data):
    """导入打板统计"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO daily_daban (
            trade_date, limit_up_count, limit_up_yesterday,
            seal_rate, seal_rate_yesterday, limit_down_count, limit_down_yesterday
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("trade_date"),
        data.get("limit_up_count"),
        data.get("limit_up_yesterday"),
        data.get("seal_rate"),
        data.get("seal_rate_yesterday"),
        data.get("limit_down_count"),
        data.get("limit_down_yesterday")
    ))
    conn.commit()
    print(f"  ✅ 打板统计已导入: {data.get('trade_date')}")

def query_recent_data(conn, days=5):
    """查询最近N日数据"""
    cursor = conn.cursor()
    
    print(f"\n{'='*50}")
    print(f"最近{days}日市场情绪")
    print(f"{'='*50}")
    
    cursor.execute("""
        SELECT trade_date, sentiment_score, limit_up_count, limit_down_count,
               (SELECT COUNT(*) FROM daily_lianban_stats WHERE trade_date = d.trade_date AND erban_count > 0) as lianban_sectors
        FROM daily_market d
        ORDER BY trade_date DESC
        LIMIT ?
    """, (days,))
    
    print(f"{'日期':<12} {'情绪分':<8} {'涨停':<6} {'跌停':<6} {'有连板':<6}")
    print("-" * 50)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<8} {row[2]:<6} {row[3]:<6} {'是' if row[4] else '否':<6}")
    
    print(f"\n{'='*50}")
    print("连板个股池")
    print(f"{'='*50}")
    
    cursor.execute("""
        SELECT trade_date, stock_name, stock_code, lianban_days, board_reason
        FROM daily_limit_up
        WHERE lianban_days >= 2
        ORDER BY trade_date DESC, lianban_days DESC
        LIMIT 20
    """)
    
    print(f"{'日期':<12} {'股票':<10} {'代码':<10} {'连板':<6} {'板块':<15}")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<10} {row[2]:<10} {row[3]:<6} {row[4]:<15}")
    
    print(f"\n{'='*50}")
    print("板块强度TOP5")
    print(f"{'='*50}")
    
    cursor.execute("""
        SELECT trade_date, sector_name, strength, main_net_inflow
        FROM daily_sector
        ORDER BY trade_date DESC, strength DESC
        LIMIT 5
    """)
    
    print(f"{'日期':<12} {'板块':<15} {'强度':<10} {'主力净额':<12}")
    print("-" * 50)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<15} {row[2]:<10} {row[3]:<12}")

if __name__ == "__main__":
    # 初始化数据库
    conn = init_db()
    
    # 导入2026-04-03数据
    print("\n导入2026-04-03数据...")
    
    # 市场概况
    import_daily_market(conn, {
        "trade_date": "2026-04-03",
        "index_value": 3880.10,
        "index_change": -1.00,
        "up_count": 698,
        "down_count": 4459,
        "limit_up_count": 36,
        "limit_down_count": 24,
        "total_volume": 16565,
        "volume_change": -1865,
        "volume_change_pct": -10.12,
        "sentiment_score": 32
    })
    
    # 连板统计
    import_lianban_stats(conn, {
        "trade_date": "2026-04-03",
        "yiban_count": 32,
        "erban_count": 3,
        "erban_rate": 14.0,
        "sanban_count": 0,
        "sanban_rate": 0,
        "gaogeng_count": 1,
        "gaogeng_rate": 25.0,
        "max_lianban_stock": "津药药业",
        "max_lianban_days": 6
    })
    
    # 涨停个股
    import_limit_up(conn, "2026-04-03", [
        {"name": "中油资本", "code": "000617", "time": "09:30", "board": "跨境支付、数字货币", "seal_amount": 339900, "lianban_days": 1},
        {"name": "翠微股份", "code": "603123", "time": "09:30", "board": "数字货币", "seal_amount": 75700, "lianban_days": 1},
        {"name": "贝肯能源", "code": "002828", "time": "09:30", "board": "石油石化", "seal_amount": 43100, "lianban_days": 1},
        {"name": "汇源通信", "code": "000586", "time": "09:25", "board": "通信", "seal_amount": 18800, "lianban_days": 2},
        {"name": "重药控股", "code": "000950", "time": "09:31", "board": "医药", "seal_amount": 3977, "lianban_days": 2},
        {"name": "新能泰山", "code": "000720", "time": "10:00", "board": "通信", "seal_amount": 11800, "lianban_days": 7},
    ])
    
    # 板块数据
    import_sector(conn, "2026-04-03", [
        {"name": "通信", "strength": 8515, "main_net": 1453000, "inst": 11370000},
        {"name": "芯片", "strength": 4492, "main_net": 342800, "inst": 17780000},
        {"name": "算力", "strength": 2007, "main_net": 468800, "inst": 5485000},
        {"name": "并购重组", "strength": 1065, "main_net": -15000, "inst": 128900},
        {"name": "跨境支付", "strength": 715, "main_net": 204100, "inst": 26200},
        {"name": "股权转让", "strength": 541, "main_net": 29360, "inst": 59390},
        {"name": "面板", "strength": 479, "main_net": -17200, "inst": 316500},
        {"name": "航运", "strength": 464, "main_net": 21100, "inst": 799800},
    ])
    
    # 打板统计
    import_daban(conn, {
        "trade_date": "2026-04-03",
        "limit_up_count": 36,
        "limit_up_yesterday": 27,
        "seal_rate": 75.0,
        "seal_rate_yesterday": 60.0,
        "limit_down_count": 24,
        "limit_down_yesterday": 5
    })
    
    # 查询数据
    query_recent_data(conn)
    
    conn.close()
    print("\n✅ 数据导入完成!")
