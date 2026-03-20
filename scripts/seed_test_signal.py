"""
Seed a test signal into the database for development/testing.
Run from project root: python scripts/seed_test_signal.py
"""
import asyncio
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import AsyncSessionLocal, init_db
from backend.models import Signal


async def seed():
    """Insert a test signal with 30-minute expiry."""
    await init_db()

    now = int(time.time())
    test_signal = Signal(
        id=f"TEST_{now}",
        symbol="ETHUSDT",
        entry_low=3420.50,
        entry_high=3435.00,
        target_pct=5.0,
        stop_loss_pct=1.0,
        score=87,
        confidence="SNIPER",
        reason="Test signal | Momentum +1.2% (5m) | Vol 2.8x | RSI 58 | BTC UP",
        btc_regime="UP",
        rsi=58.2,
        volume_spike=2.8,
        created_at=now,
        expiry_at=now + 1800,  # 30 minutes
        status="ACTIVE",
        fcm_sent=False,
    )

    async with AsyncSessionLocal() as session:
        session.add(test_signal)
        await session.commit()
        print(f"✅ Test signal seeded: {test_signal.id}")
        print(f"   Symbol: {test_signal.symbol}")
        print(f"   Score: {test_signal.score} ({test_signal.confidence})")
        print(f"   Expires in 30 minutes")


if __name__ == "__main__":
    asyncio.run(seed())
