-- Live migration: fix numeric overflow for volume/price/vwap columns
-- Run this once against the existing tradeclaw database

ALTER TABLE market_snapshots
    ALTER COLUMN price TYPE DOUBLE PRECISION,
    ALTER COLUMN volume TYPE DOUBLE PRECISION,
    ALTER COLUMN price_change_5m TYPE DOUBLE PRECISION,
    ALTER COLUMN price_change_15m TYPE DOUBLE PRECISION,
    ALTER COLUMN price_change_1h TYPE DOUBLE PRECISION,
    ALTER COLUMN rsi TYPE DOUBLE PRECISION,
    ALTER COLUMN volume_sma_ratio TYPE DOUBLE PRECISION,
    ALTER COLUMN vwap TYPE DOUBLE PRECISION;

ALTER TABLE signals
    ALTER COLUMN entry_low TYPE DOUBLE PRECISION,
    ALTER COLUMN entry_high TYPE DOUBLE PRECISION;

ALTER TABLE trades
    ALTER COLUMN entry_price TYPE DOUBLE PRECISION,
    ALTER COLUMN exit_price TYPE DOUBLE PRECISION;
