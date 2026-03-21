"""
TradeClaw — Health Route
GET /health with status, last scan timestamp, and signals today count.
"""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Signal, MarketSnapshot
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])

# Shared mutable state for last scan time (updated by scheduler)
_last_scan_time: int | None = None


def update_last_scan_time():
    """Called by the scheduler after each scan cycle."""
    global _last_scan_time
    _last_scan_time = int(time.time())


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Return backend health status."""
    # Count signals created today (UTC)
    today_start = int(datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp())

    stmt = select(func.count()).select_from(Signal).where(
        Signal.generated_at >= today_start
    )
    result = await db.execute(stmt)
    signals_today = result.scalar() or 0

    return HealthResponse(
        status="ok",
        last_scan=_last_scan_time,
        signals_today=signals_today,
    )
