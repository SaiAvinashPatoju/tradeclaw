"""
TradeClaw — Signal Routes
GET /signals           → active, non-expired signals (dashboard)
GET /signals/archive   → evaluated signals with outcomes (WIN/LOSS/INCOMPLETE)
POST /signals          → manual insert for dev/testing
"""
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Signal

router = APIRouter(prefix="/signals", tags=["signals"])


# ── Pydantic response shapes ──────────────────────────────────────────

class SignalOut(BaseModel):
    id:                   str
    symbol:               str
    score:                float
    confidence:           str
    reason:               str
    # Entry window
    generated_at:         int
    expiry_at:            int
    hold_period_secs:     int
    evaluation_at:        int
    # Trade params
    entry_low:            Optional[float] = None
    entry_high:           Optional[float] = None
    entry_price_assumed:  Optional[float] = None
    target_pct:           Optional[float] = None
    stop_loss_pct:        Optional[float] = None
    target_price:         Optional[float] = None
    stop_price:           Optional[float] = None
    # Lifecycle
    status:               str
    # Outcome (archive only)
    outcome_at:           Optional[int]   = None
    max_price_reached:    Optional[float] = None
    min_price_reached:    Optional[float] = None
    evaluated_profit_pct: Optional[float] = None

    class Config:
        from_attributes = True


class SignalListOut(BaseModel):
    signals: list[SignalOut]
    count:   int


# ── Active signals (dashboard) ────────────────────────────────────────

@router.get("", response_model=SignalListOut)
async def get_active_signals(db: AsyncSession = Depends(get_db)):
    """Return all ACTIVE non-expired signals — shown on the dashboard tile list."""
    now = int(time.time())
    stmt = (
        select(Signal)
        .where(Signal.status == "ACTIVE")
        .where(Signal.expiry_at > now)
        .order_by(Signal.score.desc())
    )
    result  = await db.execute(stmt)
    signals = result.scalars().all()
    out     = [SignalOut.model_validate(s) for s in signals]
    return SignalListOut(signals=out, count=len(out))


# ── Archive (evaluated signals) ───────────────────────────────────────

@router.get("/archive", response_model=SignalListOut)
async def get_archived_signals(
    limit:  int = Query(50,  ge=1,  le=200,  description="Max records to return"),
    offset: int = Query(0,   ge=0,           description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return evaluated signals with their outcomes.
    Status is one of: WIN | LOSS | INCOMPLETE | EXPIRED (awaiting eval)
    """
    stmt = (
        select(Signal)
        .where(Signal.status.in_(["WIN", "LOSS", "INCOMPLETE", "EXPIRED"]))
        .order_by(Signal.evaluation_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result  = await db.execute(stmt)
    signals = result.scalars().all()
    out     = [SignalOut.model_validate(s) for s in signals]
    return SignalListOut(signals=out, count=len(out))


# ── Extra endpoint: signals by status ────────────────────────────────

@router.get("/by-status/{status}", response_model=SignalListOut)
async def get_signals_by_status(
    status: str,
    limit:  int = Query(50, ge=1, le=200),
    db:     AsyncSession = Depends(get_db),
):
    """Filter signals by any lifecycle status."""
    stmt = (
        select(Signal)
        .where(Signal.status == status.upper())
        .order_by(Signal.generated_at.desc())
        .limit(limit)
    )
    result  = await db.execute(stmt)
    signals = result.scalars().all()
    out     = [SignalOut.model_validate(s) for s in signals]
    return SignalListOut(signals=out, count=len(out))


# ── Manual insert (dev/testing) ───────────────────────────────────────

@router.post("", status_code=201)
async def create_signal_manual(signal_data: dict, db: AsyncSession = Depends(get_db)):
    """Manually insert a signal (for dev testing only)."""
    signal_id = signal_data.get("id")
    if not signal_id:
        raise HTTPException(status_code=400, detail="id required")
    existing = await db.get(Signal, signal_id)
    if existing:
        raise HTTPException(status_code=409, detail="Signal ID already exists")
    sig = Signal(**{k: v for k, v in signal_data.items() if hasattr(Signal, k)})
    db.add(sig)
    await db.commit()
    return {"ok": True, "id": signal_id}
