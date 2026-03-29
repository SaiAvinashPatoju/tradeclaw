"""
TradeClaw — Scheduler Module
APScheduler-based scan loop. Two jobs:
  1. scan_job       — every 60s: scan universe, emit signals, log data
  2. evaluate_job   — every 5min: check expired signals, write outcomes
  3. expire_job     — every 60s: mark ACTIVE→EXPIRED when entry window closes
"""
import logging
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from .config import BINANCE_API_KEY, BINANCE_API_SECRET
from .database import AsyncSessionLocal
from .models import Signal, MarketSnapshot, SignalRejection
from .scanner import scan_market
from .signal_engine import generate_signals
from .evaluator import evaluate_expired_signals, expire_entry_windows
from .fcm import send_signal_push, is_initialized as fcm_ready
from .routes.health import update_last_scan_time
from .runtime_config import get_runtime_config
from .rule_engine import set_algorithm_profile

logger = logging.getLogger("tradeclaw.scheduler")
scheduler = AsyncIOScheduler()


async def _save_market_snapshots(session: AsyncSession, market_data: list[dict]):
    try:
        now = int(time.time())
        for m in market_data:
            snapshot = MarketSnapshot(
                captured_at     = m.get("timestamp", now),
                symbol          = m.get("symbol", ""),
                price           = m.get("price", 0.0),
                volume_5m       = m.get("volume", 0.0),
                volume_24h_usdt = m.get("volume_24h_usdt", 0.0),
                momentum_5m     = m.get("momentum_5m", 0.0),
                momentum_15m    = m.get("momentum_15m", 0.0),
                momentum_1h     = m.get("momentum_1h", 0.0),
                rel_volume      = m.get("rel_volume", 0.0),
                rsi             = m.get("rsi", 0.0),
                body_wick_ratio = m.get("body_wick_ratio", 0.0),
                trend_persist   = m.get("trend_persistence", 0.0),
                spread_pct      = m.get("spread_pct", 0.0),
                rel_strength_5m = m.get("rel_strength_5m", 0.0),
                btc_return_5m   = m.get("coin_vs_btc", 0.0),
            )
            session.add(snapshot)
        await session.commit()
    except Exception as e:
        logger.error(f"Failed to save market snapshots: {e}")
        await session.rollback()


async def _save_signals(session: AsyncSession, signals: list[dict]):
    try:
        for s in signals:
            signal = Signal(
                id                   = s["id"],
                symbol               = s["symbol"],
                generated_at         = s["generated_at"],
                expiry_at            = s["expiry_at"],
                hold_period_secs     = s["hold_period_secs"],
                evaluation_at        = s["evaluation_at"],
                entry_low            = s["entry_low"],
                entry_high           = s["entry_high"],
                entry_price_assumed  = s["entry_price_assumed"],
                target_pct           = s["target_pct"],
                stop_loss_pct        = s["stop_loss_pct"],
                target_price         = s["target_price"],
                stop_price           = s["stop_price"],
                score                = s["score"],
                confidence           = s["confidence"],
                reason               = s["reason"],
                feature_vector       = s.get("feature_vector"),
                status               = s["status"],
            )
            session.add(signal)
        await session.commit()
        logger.info(f"Saved {len(signals)} signals")
    except Exception as e:
        logger.error(f"Failed to save signals: {e}")
        await session.rollback()


async def _save_rejections(session: AsyncSession, rejections: list[dict]):
    if not rejections:
        return
    try:
        for r in rejections:
            rej = SignalRejection(
                rejected_at    = r["rejected_at"],
                symbol         = r["symbol"],
                reject_reason  = r["reject_reason"],
                score          = r["score"],
                feature_vector = r["feature_vector"],
            )
            session.add(rej)
        await session.commit()
    except Exception as e:
        logger.error(f"Failed to save rejections: {e}")
        await session.rollback()


async def _send_notifications(signals: list[dict]):
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
    """Main scan: universe → features → rules → signals → persist → notify."""
    start = time.time()
    logger.info("=" * 50)
    logger.info("Scan cycle v1")

    try:
        runtime_cfg = get_runtime_config()
        if runtime_cfg["data_source_mode"] == "simulator":
            await expire_entry_windows()
            update_last_scan_time()
            logger.info("Simulator mode active - skipped Binance market scan")
            return

        set_algorithm_profile(runtime_cfg["algorithm_profile"])

        market_data = await scan_market(BINANCE_API_KEY, BINANCE_API_SECRET)
        if not market_data:
            logger.warning("No market data")
            update_last_scan_time()
            return

        signals, rejections = generate_signals(market_data)

        async with AsyncSessionLocal() as session:
            await _save_market_snapshots(session, market_data)
            await _save_rejections(session, rejections)
            if signals:
                await _save_signals(session, signals)

        if signals:
            await _send_notifications(signals)

        # Also expire any stale ACTIVE signals in this cycle
        await expire_entry_windows()

        update_last_scan_time()
        elapsed = time.time() - start
        logger.info(
            f"Cycle done {elapsed:.1f}s — "
            f"{len(market_data)} scanned | {len(signals)} emitted | {len(rejections)} rejected"
        )

    except Exception as e:
        logger.error(f"Scan cycle failed: {e}", exc_info=True)


async def evaluate_job():
    """Evaluation job: check expired signals, write WIN/LOSS/INCOMPLETE outcomes."""
    try:
        await evaluate_expired_signals()
    except Exception as e:
        logger.error(f"Evaluation job failed: {e}", exc_info=True)


def start_scheduler():
    scheduler.add_job(scan_job,     "interval", seconds=60,  id="market_scan",      max_instances=1, replace_existing=True)
    scheduler.add_job(evaluate_job, "interval", seconds=300, id="signal_evaluation", max_instances=1, replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — scan every 60s | evaluate every 5min")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
