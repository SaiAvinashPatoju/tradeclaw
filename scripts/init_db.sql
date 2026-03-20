-- Market snapshots (append-only, one per scan per coin)
CREATE TABLE IF NOT EXISTS market_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    price_change_5m DOUBLE PRECISION,
    price_change_15m DOUBLE PRECISION,
    price_change_1h DOUBLE PRECISION,
    rsi DOUBLE PRECISION,
    volume_sma_ratio DOUBLE PRECISION,
    vwap DOUBLE PRECISION,
    btc_regime VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Signal records
CREATE TABLE IF NOT EXISTS signals (
    id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    entry_low DECIMAL(18,8),
    entry_high DECIMAL(18,8),
    target_pct DECIMAL(5,2) DEFAULT 5.0,
    stop_loss_pct DECIMAL(5,2) DEFAULT 1.0,
    score INTEGER NOT NULL,
    confidence VARCHAR(20) NOT NULL,
    reason TEXT,
    btc_regime VARCHAR(10),
    rsi DECIMAL(6,2),
    volume_spike DECIMAL(6,2),
    created_at BIGINT NOT NULL,
    expiry_at BIGINT NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    fcm_sent BOOLEAN DEFAULT FALSE
);

-- Trade records (user-driven, for future ML training)
CREATE TABLE IF NOT EXISTS trades (
    id VARCHAR(50) PRIMARY KEY,
    signal_id VARCHAR(50) REFERENCES signals(id),
    symbol VARCHAR(20) NOT NULL,
    entry_price DECIMAL(18,8),
    exit_price DECIMAL(18,8),
    entry_time BIGINT,
    exit_time BIGINT,
    profit_pct DECIMAL(8,4),
    hit_target BOOLEAN,
    hit_stop_loss BOOLEAN,
    manual_exit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_snapshots_time_symbol ON market_snapshots(timestamp, symbol);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status, created_at);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol, created_at);
