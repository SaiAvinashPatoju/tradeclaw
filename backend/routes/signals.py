"""
TradeClaw — Signal Routes
GET /signals (active, non-expired) and POST /signals (manual insert for testing).
"""
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Signal
from ..schemas import SignalResponse, SignalListResponse

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=SignalListResponse)
async def get_active_signals(db: AsyncSession = Depends(get_db)):
    """Return all active, non-expired signals."""
    now = int(time.time())
    stmt = (
        select(Signal)
        .where(Signal.status == "ACTIVE")
        .where(Signal.expiry_at > now)
        .order_by(Signal.score.desc())
    )
    result = await db.execute(stmt)
    signals = result.scalars().all()

    return SignalListResponse(
        signals=[SignalResponse.model_validate(s) for s in signals]
    )


@router.post("", response_model=SignalResponse, status_code=201)
async def create_signal(signal_data: SignalResponse, db: AsyncSession = Depends(get_db)):
    """Manually insert a signal (for testing/dev)."""
    existing = await db.get(Signal, signal_data.id)
    if existing:
        raise HTTPException(status_code=409, detail="Signal ID already exists")

    signal = Signal(
        id=signal_data.id,
        symbol=signal_data.symbol,
        entry_low=signal_data.entry_low,
        entry_high=signal_data.entry_high,
        target_pct=signal_data.target_pct,
        stop_loss_pct=signal_data.stop_loss_pct,
        score=signal_data.score,
        confidence=signal_data.confidence,
        reason=signal_data.reason,
        btc_regime=signal_data.btc_regime,
        rsi=signal_data.rsi,
        volume_spike=signal_data.volume_spike,
        created_at=signal_data.created_at,
        expiry_at=signal_data.expiry_at,
        status=signal_data.status,
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return SignalResponse.model_validate(signal)
