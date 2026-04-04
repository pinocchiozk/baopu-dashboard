-- 开盘啦历史数据库
-- 版本: v1.0
-- 创建时间: 2026-04-04

-- ==================== 1. 每日市场概况 ====================
CREATE TABLE IF NOT EXISTS daily_market (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL UNIQUE,  -- 交易日期
    index_code VARCHAR(10),            -- 指数代码
    index_name VARCHAR(20),            -- 指数名称（沪指）
    index_value DECIMAL(10,2),        -- 指数点位
    index_change DECIMAL(10,2),        -- 指数涨跌幅
    up_count INTEGER,                  -- 上涨家数
    down_count INTEGER,                -- 下跌家数
    flat_count INTEGER,                -- 平盘家数
    limit_up_count INTEGER,            -- 涨停家数（过滤ST）
    limit_down_count INTEGER,          -- 跌停家数（过滤ST）
    total_volume DECIMAL(20,2),        -- 总成交额（亿）
    volume_change DECIMAL(20,2),       -- 成交额变化（亿）
    volume_change_pct DECIMAL(10,2),  -- 成交额变化比例
    sentiment_score INTEGER,           -- 情绪分数（0-100）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_market_date ON daily_market(trade_date);

-- ==================== 2. 连板梯队统计 ====================
CREATE TABLE IF NOT EXISTS daily_lianban_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,          -- 交易日期
    yiban_count INTEGER,                -- 一板数量
    erban_count INTEGER,               -- 二板数量
    erban_rate DECIMAL(10,2),          -- 二板率
    sanban_count INTEGER,              -- 三板数量
    sanban_rate DECIMAL(10,2),        -- 三板率
    sibanshi_count INTEGER,           -- 四板数量
    sibanshi_rate DECIMAL(10,2),      -- 四板率
    gaogeng_count INTEGER,            -- 更高板数量
    gaogeng_rate DECIMAL(10,2),       -- 更高板率
    max_lianban_stock VARCHAR(50),    -- 最高连板股名称
    max_lianban_days INTEGER,         -- 最高连板天数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date)
);

-- ==================== 3. 涨停个股明细 ====================
CREATE TABLE IF NOT EXISTS daily_limit_up (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,          -- 交易日期
    stock_name VARCHAR(50),            -- 股票名称
    stock_code VARCHAR(10),            -- 股票代码
    limit_time TIME,                   -- 涨停时间
    board_reason VARCHAR(100),         -- 涨停原因（板块）
    seal_amount DECIMAL(20,2),        -- 封单金额（万）
    lianban_days INTEGER,             -- 连板天数（1为首板）
    is_yinzi TINYINT DEFAULT 0,       -- 游资标的
    is_rongzi TINYINT DEFAULT 0,      -- 融资标的
    rank_no INTEGER,                   -- 当日涨停排名
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, stock_code)
);

CREATE INDEX idx_limit_up_date ON daily_limit_up(trade_date);
CREATE INDEX idx_limit_up_code ON daily_limit_up(stock_code);

-- ==================== 4. 板块强度排名 ====================
CREATE TABLE IF NOT EXISTS daily_sector (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,          -- 交易日期
    sector_code VARCHAR(10),           -- 板块代码
    sector_name VARCHAR(50),           -- 板块名称
    strength INTEGER,                   -- 强度指数
    main_net_inflow DECIMAL(20,2),    -- 主力净额（万）
    inst_increase DECIMAL(20,2),      -- 机构增仓（万）
    rank_no INTEGER,                   -- 当日强度排名
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, sector_code)
);

CREATE INDEX idx_sector_date ON daily_sector(trade_date);
CREATE INDEX idx_sector_strength ON daily_sector(trade_date, strength DESC);

-- ==================== 5. 打板统计 ====================
CREATE TABLE IF NOT EXISTS daily_daban (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL UNIQUE,  -- 交易日期
    limit_up_count INTEGER,            -- 涨停数
    limit_up_yesterday INTEGER,        -- 昨日涨停数
    seal_rate DECIMAL(10,2),          -- 封板率
    seal_rate_yesterday DECIMAL(10,2),-- 昨日封板率
    limit_down_count INTEGER,          -- 跌停数
    limit_down_yesterday INTEGER,      -- 昨日跌停数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 6. 情绪指标每日 ====================
CREATE TABLE IF NOT EXISTS daily_sentiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL UNIQUE,  -- 交易日期
    sentiment_score INTEGER,           -- 综合强度分数
    break_board_rate DECIMAL(10,2),   -- 破板率
    yesterday_up_today_return DECIMAL(10,2),    -- 昨日涨停今表现
    yesterday_lianban_today_return DECIMAL(10,2), -- 昨日连板今表现
    yesterday_break_today_return DECIMAL(10,2),   -- 昨日破板今表现
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 7. 尾盘异动 ====================
CREATE TABLE IF NOT EXISTS daily_afterhours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,          -- 交易日期
    event_type VARCHAR(20),            -- 异动类型（尾盘抢筹、炸板等）
    stock_name VARCHAR(50),            -- 股票名称
    stock_code VARCHAR(10),            -- 股票代码
    amount DECIMAL(20,2),             -- 金额（万）
    description TEXT,                  -- 描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 视图：每日连板个股池 ====================
CREATE VIEW IF NOT EXISTS v_lianban_pool AS
SELECT 
    trade_date,
    stock_name,
    stock_code,
    lianban_days,
    board_reason,
    seal_amount
FROM daily_limit_up
WHERE lianban_days >= 2
ORDER BY trade_date DESC, lianban_days DESC;

-- ==================== 视图：板块主力资金流 ====================
CREATE VIEW IF NOT EXISTS v_sector_flow AS
SELECT 
    trade_date,
    sector_name,
    main_net_inflow,
    inst_increase,
    strength,
    RANK() OVER (PARTITION BY trade_date ORDER BY main_net_inflow DESC) as flow_rank
FROM daily_sector
ORDER BY trade_date DESC, main_net_inflow DESC;

-- ==================== 视图：赚钱效应监控 ====================
CREATE VIEW IF NOT EXISTS v_profit_monitor AS
SELECT 
    d.trade_date,
    d.sentiment_score,
    d.limit_up_count,
    d.limit_down_count,
    l.yiban_count,
    l.erban_count,
    l.sanban_count,
    l.gaogeng_count,
    l.max_lianban_days,
    l.max_lianban_stock,
    s.break_board_rate
FROM daily_market d
LEFT JOIN daily_lianban_stats l ON d.trade_date = l.trade_date
LEFT JOIN daily_sentiment s ON d.trade_date = s.trade_date
ORDER BY d.trade_date DESC;
