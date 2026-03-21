"""
TradeClaw — Signal Evaluator
Runs every 5 minutes. Finds signals where evaluation_at has passed,
fetches historical kline data from Binance to determine if TP or SL was hit,
then marks the signal WIN / LOSS / INCOMPLETE.

Evaluation logic:
  - Fetch 5m klines from expiry_at → evaluation_at window
  - Walk candles in order (chronological = simulated real-time)
  - If high >= target_price before low <= stop_price → WIN
  - If low <= stop_price before high >= target_price → LOSS
  - If neither hit in the window → INCOMPLETE (price never reached either level)
  - evaluated_profit_pct:
      WIN       → +target_pct
      LOSS      → -stop_loss_pct
      INCOMPLETE→ (last_close - entry_price_assumed) / entry_price_assumed * 100
"""
import logging
import time
from binance import AsyncClient
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .config import BINANCE_API_KEY, BINANCE_API_SECRET
from .database import AsyncSessionLocal
from .models import Signal

logger = logging.getLogger("tradeclaw.evaluator")


async def _fetch_klines_for_window(
    client: AsyncClient,
    symbol: str,
    start_ts: int,
    end_ts: int,
    interval: str = "5m"
) -> list:
    """Fetch historical klines between two epoch timestamps (milliseconds for Binance)."""
    try:
        klines = await client.get_historical_klines(
            symbol,
            interval,
            start_str=start_ts * 1000,
            end_str=end_ts * 1000,
            limit=500,
        )
        return klines
    except Exception as e:
        logger.warning(f"Failed to fetch klines for {symbol}: {e}")
        return []


def _evaluate_klines(
    klines: list,
    target_price: float,
    stop_price: float,
    entry_price: float,
) -> dict:
    """
    Walk klines chronologically and determine outcome.
    Returns dict with: outcome, max_high, min_low, last_close, evaluated_profit_pct
    """
    if not klines:
        return {
            "outcome": "INCOMPLETE",
            "max_price_reached": entry_price,
            "min_price_reached": entry_price,
            "evaluated_profit_pct": 0.0,
        }

    max_high  = float("-inf")
    min_low   = float("inf")
    last_close = entry_price

    for k in klines:
        candle_high  = float(k[2])
        candle_low   = float(k[3])
        candle_close = float(k[4])

        max_high   = max(max_high, candle_high)
        min_low    = min(min_low,  candle_low)
        last_close = candle_close

        # Check TP hit first within this candle
        tp_hit = candle_high >= target_price
        sl_hit = candle_low  <= stop_price

        if tp_hit and sl_hit:
            # Both hit same candle: conservative assumption → SL hit (safer for training data)
            # In reality this is ambiguous; for training we mark LOSS to be conservative
            outcome = "LOSS"
            profit  = -((entry_price - stop_price) / entry_price) * 100
            return {
                "outcome": outcome,
                "max_price_reached": max_high,
                "min_price_reached": min_low,
                "evaluated_profit_pct": round(profit, 4),
            }
        if tp_hit:
            profit = ((target_price - entry_price) / entry_price) * 100
            return {
                "outcome": "WIN",
                "max_price_reached": max_high,
                "min_price_reached": min_low,
                "evaluated_profit_pct": round(profit, 4),
            }
        if sl_hit:
            profit = -((entry_price - stop_price) / entry_price) * 100
            return {
                "outcome": "LOSS",
                "max_price_reached": max_high,
                "min_price_reached": min_low,
                "evaluated_profit_pct": round(profit, 4),
            }

    # Neither hit — INCOMPLETE
    # Record the actual drift from assumed entry
    actual_pct = ((last_close - entry_price) / entry_price) * 100
    return {
        "outcome": "INCOMPLETE",
        "max_price_reached": max_high if max_high != float("-inf") else entry_price,
        "min_price_reached": min_low  if min_low  != float("inf")  else entry_price,
        "evaluated_profit_pct": round(actual_pct, 4),
    }


async def evaluate_expired_signals():
    """
    Main evaluation job. Called by scheduler every 5 minutes.
    Finds all signals that are EXPIRED (entry window closed) and whose
    evaluation_at timestamp has now passed, fetches price data, determines outcome.
    """
    now = int(time.time())

    async with AsyncSessionLocal() as session:
        # Find signals ready for evaluation
        stmt = (
            select(Signal)
            .where(
                and_(
                    Signal.status.in_(["EXPIRED", "ACTIVE"]),
                    Signal.evaluation_at <= now,
                )
            )
            .limit(20)  # Process at most 20 per cycle
        )
        result = await session.execute(stmt)
        signals_to_eval = result.scalars().all()

    if not signals_to_eval:
        return

    logger.info(f"Evaluating {len(signals_to_eval)} signals...")
    client = await AsyncClient.create(BINANCE_API_KEY, BINANCE_API_SECRET)

    try:
        for sig in signals_to_eval:
            try:
                # Fetch klines for the hold window
                klines = await _fetch_klines_for_window(
                    client,
                    sig.symbol,
                    start_ts=sig.expiry_at,      # hold period starts when entry closes
                    end_ts=sig.evaluation_at,
                    interval="5m",
                )

                result = _evaluate_klines(
                    klines,
                    target_price=sig.target_price,
                    stop_price=sig.stop_price,
                    entry_price=sig.entry_price_assumed or ((sig.entry_low + sig.entry_high) / 2),
                )

                # Write outcome back to DB
                async with AsyncSessionLocal() as session:
                    sig_db = await session.get(Signal, sig.id)
                    if sig_db:
                        sig_db.status               = result["outcome"]
                        sig_db.outcome_at           = now
                        sig_db.max_price_reached    = result["max_price_reached"]
                        sig_db.min_price_reached    = result["min_price_reached"]
                        sig_db.evaluated_profit_pct = result["evaluated_profit_pct"]
                        await session.commit()

                logger.info(
                    f"Evaluated {sig.id} [{sig.symbol}] → "
                    f"{result['outcome']} | PnL: {result['evaluated_profit_pct']:+.2f}%"
                )

            except Exception as e:
                logger.error(f"Failed to evaluate {sig.id}: {e}")

    finally:
        try:
            await client.close_connection()
        except Exception:
            pass


async def expire_entry_windows():
    """
    Marks signals as EXPIRED when expiry_at has passed but evaluation is not yet due.
    Runs every 60s as part of the main scan job.
    """
    now = int(time.time())
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Signal)
            .where(
                and_(
                    Signal.status == "ACTIVE",
                    Signal.expiry_at <= now,
                    Signal.evaluation_at > now,  # not yet time to evaluate
                )
            )
        )
        result = await session.execute(stmt)
        active_expired = result.scalars().all()

        if active_expired:
            for sig in active_expired:
                sig.status = "EXPIRED"
            await session.commit()
            logger.info(f"Expired {len(active_expired)} entry windows → EXPIRED status")
