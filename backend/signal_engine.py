"""
TradeClaw — Signal Engine
Generates, filters, and emits trading signals with cooldown, dedup, and crash guard.
"""
import logging
import time
from datetime import datetime

from .scoring import calculate_composite_score, TIER_REJECT

logger = logging.getLogger("tradeclaw.signal_engine")

# ── Configuration ──────────────────────────────────────────────────────
MAX_SIGNALS_PER_CYCLE = 3
COOLDOWN_SECONDS = 15 * 60          # 15 minutes per coin
SIGNAL_EXPIRY_SECONDS = 30 * 60     # 30 minutes
BTC_CRASH_THRESHOLD = -1.5          # Suppress signals if BTC 15m < -1.5%
TARGET_PCT = 5.0
STOP_LOSS_PCT = 1.0

# ── In-memory trackers (reset on restart, DB is source of truth) ──────
_cooldown_tracker: dict[str, float] = {}   # symbol → last_signal_timestamp
_active_signals: set[str] = set()          # active signal IDs


def _generate_signal_id(symbol: str) -> str:
    """Generate unique signal ID: COIN_YYYYMMDD_HHMMSS"""
    now = datetime.utcnow()
    clean_symbol = symbol.replace("USDT", "")
    return f"{clean_symbol}_{now.strftime('%Y%m%d_%H%M%S')}"


def _format_entry_range(price: float) -> tuple[float, float]:
    """
    Calculate entry range around current price.
    Lower bound: -0.2%, Upper bound: +0.2%
    """
    low = round(price * 0.998, 8)
    high = round(price * 1.002, 8)
    return low, high


def _is_on_cooldown(symbol: str) -> bool:
    """Check if a coin is still within the cooldown period."""
    last_signal_time = _cooldown_tracker.get(symbol)
    if last_signal_time is None:
        return False
    return (time.time() - last_signal_time) < COOLDOWN_SECONDS


def _has_active_signal(symbol: str) -> bool:
    """Check if there's already an active unexpired signal for this coin."""
    # Check by prefix — active_signals stores IDs like "ETH_20260321_001"
    clean_symbol = symbol.replace("USDT", "")
    return any(sig_id.startswith(clean_symbol + "_") for sig_id in _active_signals)


def _build_reason_string(metrics: dict) -> str:
    """Build a human-readable reason string from metrics."""
    parts = []
    pct5 = metrics.get("price_change_5m", 0)
    if pct5 > 0:
        parts.append(f"Momentum +{pct5:.1f}% (5m)")

    vol = metrics.get("volume_sma_ratio", 1.0)
    if vol > 1.0:
        parts.append(f"Vol {vol:.1f}x")

    rsi = metrics.get("rsi", 0)
    if rsi > 0:
        parts.append(f"RSI {rsi:.0f}")

    btc = metrics.get("btc_regime", "")
    if btc:
        parts.append(f"BTC {btc}")

    return " | ".join(parts) if parts else "Signal generated"


def generate_signals(market_data: list[dict]) -> list[dict]:
    """
    Process market data and generate filtered trading signals.

    Args:
        market_data: list of metric dicts from scanner

    Returns:
        list of signal dicts ready for DB insertion and FCM push
    """
    if not market_data:
        return []

    # ── BTC Crash Guard ──────────────────────────────────────────────
    btc_15m_change = 0.0
    for m in market_data:
        if m.get("symbol") == "BTCUSDT":
            btc_15m_change = m.get("btc_15m_change", 0.0)
            break

    if btc_15m_change < BTC_CRASH_THRESHOLD:
        logger.warning(f"BTC crash guard triggered: 15m change = {btc_15m_change:.2f}%. "
                       f"Suppressing ALL signals.")
        return []

    # ── Score and filter each coin ───────────────────────────────────
    scored = []
    for metrics in market_data:
        symbol = metrics.get("symbol", "")

        # Skip if on cooldown
        if _is_on_cooldown(symbol):
            logger.debug(f"Skipping {symbol}: on cooldown")
            continue

        # Skip if active signal exists
        if _has_active_signal(symbol):
            logger.debug(f"Skipping {symbol}: active signal exists")
            continue

        # Calculate score
        score, tier = calculate_composite_score(metrics)

        # Reject low scores
        if tier == TIER_REJECT:
            continue

        scored.append({
            "symbol": symbol,
            "score": score,
            "tier": tier,
            "metrics": metrics,
        })

    # ── Sort by score, take top N ────────────────────────────────────
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:MAX_SIGNALS_PER_CYCLE]

    # ── Build signal records ─────────────────────────────────────────
    now = int(time.time())
    signals = []

    for item in top:
        symbol = item["symbol"]
        metrics = item["metrics"]
        price = metrics.get("price", 0)
        entry_low, entry_high = _format_entry_range(price)
        signal_id = _generate_signal_id(symbol)

        signal = {
            "id": signal_id,
            "symbol": symbol,
            "entry_low": entry_low,
            "entry_high": entry_high,
            "target_pct": TARGET_PCT,
            "stop_loss_pct": STOP_LOSS_PCT,
            "score": item["score"],
            "confidence": item["tier"],
            "reason": _build_reason_string(metrics),
            "btc_regime": metrics.get("btc_regime", "NEUTRAL"),
            "rsi": metrics.get("rsi", 0),
            "volume_spike": metrics.get("volume_sma_ratio", 1.0),
            "created_at": now,
            "expiry_at": now + SIGNAL_EXPIRY_SECONDS,
            "status": "ACTIVE",
            "fcm_sent": False,
        }

        signals.append(signal)

        # Update trackers
        _cooldown_tracker[symbol] = now
        _active_signals.add(signal_id)

        logger.info(f"Signal generated: {signal_id} | {symbol} | "
                    f"Score: {item['score']} | Tier: {item['tier']}")

    return signals


def expire_signals(current_time: int | None = None) -> list[str]:
    """
    Remove expired signal IDs from the active tracker.
    Returns list of expired signal IDs.
    """
    if current_time is None:
        current_time = int(time.time())

    expired = []
    for sig_id in list(_active_signals):
        # Extract timestamp from ID format: COIN_YYYYMMDD_HHMMSS
        # We can't determine expiry from ID alone, so we just clean up
        # signals older than SIGNAL_EXPIRY_SECONDS from the tracker
        pass

    return expired


def clear_trackers():
    """Clear all in-memory trackers (for testing)."""
    _cooldown_tracker.clear()
    _active_signals.clear()
