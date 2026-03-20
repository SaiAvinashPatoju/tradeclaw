import time
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, Text, DateTime, Index
from sqlalchemy.sql import func
from .database import Base

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    __table_args__ = (
        Index('idx_snapshots_time_symbol', 'timestamp', 'symbol'),
    )

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(BigInteger, nullable=False)
    symbol = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    price_change_5m = Column(Float)
    price_change_15m = Column(Float)
    price_change_1h = Column(Float)
    rsi = Column(Float)
    volume_sma_ratio = Column(Float)
    vwap = Column(Float)
    btc_regime = Column(String(10))
    created_at = Column(DateTime, server_default=func.now())

class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        Index('idx_signals_status', 'status', 'created_at'),
        Index('idx_signals_symbol', 'symbol', 'created_at'),
    )

    id = Column(String(50), primary_key=True)
    symbol = Column(String(20), nullable=False)
    entry_low = Column(Float)
    entry_high = Column(Float)
    target_pct = Column(Float, default=5.0)
    stop_loss_pct = Column(Float, default=1.0)
    score = Column(Integer, nullable=False)
    confidence = Column(String(20), nullable=False)
    reason = Column(Text)
    btc_regime = Column(String(10))
    rsi = Column(Float)
    volume_spike = Column(Float)
    created_at = Column(BigInteger, nullable=False)
    expiry_at = Column(BigInteger, nullable=False)
    status = Column(String(20), default="ACTIVE")
    fcm_sent = Column(Boolean, default=False)

class Trade(Base):
    __tablename__ = "trades"

    id = Column(String(50), primary_key=True)
    signal_id = Column(String(50))
    symbol = Column(String(20), nullable=False)
    entry_price = Column(Float)
    exit_price = Column(Float)
    entry_time = Column(BigInteger)
    exit_time = Column(BigInteger)
    profit_pct = Column(Float)
    hit_target = Column(Boolean)
    hit_stop_loss = Column(Boolean)
    manual_exit = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
