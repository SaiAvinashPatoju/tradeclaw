"""
TradeClaw — SQLAlchemy Models (V1 Final)

Signal Lifecycle:
  ACTIVE     → entry window is open, tile shows on dashboard
  EXPIRED    → entry window closed, waiting for hold period to elapse
  EVALUATING → hold period elapsed, price check in progress (transient)
  WIN        → TP was hit during hold period before SL
  LOSS       → SL was hit during hold period before TP
  INCOMPLETE → neither TP nor SL hit during hold period (signal decayed)
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .database import Base


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    __table_args__ = (
        Index('idx_snapshots_time_symbol', 'captured_at', 'symbol'),
    )

    id              = Column(Integer, primary_key=True, index=True)
    captured_at     = Column(BigInteger, nullable=False)
    symbol          = Column(String(20), nullable=False)
    price           = Column(Float, nullable=False)
    volume_5m       = Column(Float)
    volume_24h_usdt = Column(Float)
    momentum_5m     = Column(Float)
    momentum_15m    = Column(Float)
    momentum_1h     = Column(Float)
    rel_volume      = Column(Float)
    rsi             = Column(Float)
    body_wick_ratio = Column(Float)
    trend_persist   = Column(Float)
    spread_pct      = Column(Float)
    rel_strength_5m = Column(Float)
    btc_return_5m   = Column(Float)
    regime          = Column(String(10), default='NEUTRAL')
    created_at      = Column(DateTime, server_default=func.now())


class Signal(Base):
    """
    Full signal record with lifecycle tracking.

    Key timestamps (all epoch seconds):
      generated_at   - when signal was computed
      expiry_at      - when optimal entry window closes (shown as countdown)
      evaluation_at  - when outcome check runs (= expiry_at + hold_period_secs)

    Key prices (computed at signal generation time):
      entry_price_assumed - midpoint of entry_low/entry_high (used for PnL calc)
      target_price        - entry_price_assumed * (1 + target_pct/100)
      stop_price          - entry_price_assumed * (1 - stop_loss_pct/100)

    Outcome fields (filled after evaluation):
      max_price_reached   - highest price seen during hold period
      min_price_reached   - lowest price seen during hold period
      outcome_at          - epoch when outcome was determined
      outcome             - WIN / LOSS / INCOMPLETE
      evaluated_profit_pct - actual % gain/loss (positive = profit)
    """
    __tablename__ = "signals"
    __table_args__ = (
        Index('idx_signals_status_expiry',    'status', 'expiry_at'),
        Index('idx_signals_eval',             'status', 'evaluation_at'),
        Index('idx_signals_symbol_gen',       'symbol', 'generated_at'),
    )

    # Identity
    id              = Column(String(50), primary_key=True)
    symbol          = Column(String(20), nullable=False)

    # Timestamps
    generated_at    = Column(BigInteger, nullable=False)
    expiry_at       = Column(BigInteger, nullable=False)      # entry window closes
    hold_period_secs= Column(Integer,   default=14400)        # default 4h (configurable)
    evaluation_at   = Column(BigInteger, nullable=False)      # = expiry_at + hold_period_secs

    # Trade parameters
    entry_low       = Column(Float)
    entry_high      = Column(Float)
    entry_price_assumed = Column(Float)                       # midpoint, for PnL calc
    target_pct      = Column(Float)
    stop_loss_pct   = Column(Float)
    target_price    = Column(Float)                           # absolute price at TP
    stop_price      = Column(Float)                           # absolute price at SL

    # Signal quality
    score           = Column(Float, nullable=False)
    confidence      = Column(String(20))
    reason          = Column(Text)
    rule_breakdown  = Column(JSONB)
    feature_vector  = Column(JSONB)
    regime_at_emit  = Column(String(10))

    # Lifecycle
    status          = Column(String(20), default="ACTIVE")
    # ACTIVE | EXPIRED | EVALUATING | WIN | LOSS | INCOMPLETE

    # Outcome (filled after evaluation)
    max_price_reached    = Column(Float)
    min_price_reached    = Column(Float)
    outcome_at           = Column(BigInteger)
    evaluated_profit_pct = Column(Float)    # positive = gain, negative = loss

    # Misc
    created_at      = Column(DateTime, server_default=func.now())
    fcm_sent        = Column(Boolean, default=False)


class SignalRejection(Base):
    __tablename__ = "signal_rejections"

    id              = Column(Integer, primary_key=True, index=True)
    rejected_at     = Column(BigInteger, nullable=False)
    symbol          = Column(String(20), nullable=False)
    reject_reason   = Column(String(50), nullable=False)
    score           = Column(Float)
    feature_vector  = Column(JSONB)
    created_at      = Column(DateTime, server_default=func.now())


class TradeOutcome(Base):
    """Manual trade outcomes entered/confirmed by the user."""
    __tablename__ = "trade_outcomes"

    id              = Column(Integer, primary_key=True, index=True)
    signal_id       = Column(String(50))
    symbol          = Column(String(20), nullable=False)
    entry_price     = Column(Float)
    exit_price      = Column(Float)
    entry_time      = Column(BigInteger)
    exit_time       = Column(BigInteger)
    profit_pct      = Column(Float)
    hit_target      = Column(Boolean, default=False)
    hit_stop        = Column(Boolean, default=False)
    time_stopped    = Column(Boolean, default=False)
    manual_exit     = Column(Boolean, default=False)
    position_size   = Column(Float)
    net_pnl_usdt    = Column(Float)
    fees_usdt       = Column(Float)
    notes           = Column(Text)
    created_at      = Column(DateTime, server_default=func.now())
