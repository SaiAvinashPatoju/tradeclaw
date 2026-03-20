"""
TradeClaw — Scheduler Module
APScheduler-based scan loop that runs every 60 seconds.
"""
import logging
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from .config import BINANCE_API_KEY, BINANCE_API_SECRET
from .database import AsyncSessionLocal
from .models import Signal, MarketSnapshot
from .scanner import scan_market
from .signal_engine import generate_signals
from .fcm import send_signal_push, is_initialized as fcm_ready
from .routes.health import update_last_scan_time

logger = logging.getLogger("tradeclaw.scheduler")

scheduler = AsyncIOScheduler()


async def _save_market_snapshots(session: AsyncSession, market_data: list[dict]):
    """Persist market snapshots to DB (non-blocking, best-effort)."""
    try:
        for m in market_data:
            snapshot = MarketSnapshot(
                timestamp=m.get("timestamp", int(time.time())),
                symbol=m.get("symbol", ""),
                price=m.get("price", 0),
                volume=m.get("volume", 0),
                price_change_5m=m.get("price_change_5m"),
                price_change_15m=m.get("price_change_15m"),
                price_change_1h=m.get("price_change_1h"),
                rsi=m.get("rsi"),
                volume_sma_ratio=m.get("volume_sma_ratio"),
                vwap=m.get("vwap"),
                btc_regime=m.get("btc_regime"),
            )
            session.add(snapshot)
        await session.commit()
        logger.info(f"Saved {len(market_data)} market snapshots")
    except Exception as e:
        logger.error(f"Failed to save market snapshots: {e}")
        await session.rollback()


async def _save_signals(session: AsyncSession, signals: list[dict]):
    """Persist signals to DB."""
    try:
        for s in signals:
            signal = Signal(
                id=s["id"],
                symbol=s["symbol"],
                entry_low=s["entry_low"],
                entry_high=s["entry_high"],
                target_pct=s["target_pct"],
                stop_loss_pct=s["stop_loss_pct"],
                score=s["score"],
                confidence=s["confidence"],
                reason=s["reason"],
                btc_regime=s["btc_regime"],
                rsi=s["rsi"],
                volume_spike=s["volume_spike"],
                created_at=s["created_at"],
                expiry_at=s["expiry_at"],
                status=s["status"],
                fcm_sent=False,
            )
            session.add(signal)
        await session.commit()
        logger.info(f"Saved {len(signals)} signals to database")
    except Exception as e:
        logger.error(f"Failed to save signals: {e}")
        await session.rollback()


async def _send_notifications(signals: list[dict]):
    """Send FCM push for each signal (best-effort)."""
    if not fcm_ready():
        return

    for s in signals:
        try:
            success = await send_signal_push(s)
            if success:
                logger.info(f"FCM sent for {s['id']}")
        except Exception as e:
            logger.error(f"FCM error for {s['id']}: {e}")


async def scan_job():
    """Main scheduled job: scan → score → filter → save → push."""
    start_time = time.time()
    logger.info("=" * 50)
    logger.info("Scan cycle started")

    try:
        # 1. Scan market
        market_data = await scan_market(BINANCE_API_KEY, BINANCE_API_SECRET)
        if not market_data:
            logger.warning("No market data received")
            update_last_scan_time()
            return

        # 2. Generate signals
        signals = generate_signals(market_data)

        # 3. Save to DB
        async with AsyncSessionLocal() as session:
            await _save_market_snapshots(session, market_data)
            if signals:
                await _save_signals(session, signals)

        # 4. Send push notifications
        if signals:
            await _send_notifications(signals)

        # 5. Update health endpoint
        update_last_scan_time()

        elapsed = time.time() - start_time
        logger.info(f"Scan cycle completed in {elapsed:.1f}s — "
                    f"{len(market_data)} pairs scanned, {len(signals)} signals emitted")

    except Exception as e:
        logger.error(f"Scan cycle failed: {e}", exc_info=True)


def start_scheduler():
    """Start the APScheduler with the scan job."""
    scheduler.add_job(scan_job, "interval", seconds=60, id="market_scan",
                      max_instances=1, replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — scanning every 60 seconds")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
