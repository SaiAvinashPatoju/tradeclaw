"""
TradeClaw — Export Routes
GET /export/signals, /export/market, /export/trades with JSON and CSV format support.
"""
import csv
import io
import time
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Signal, MarketSnapshot, TradeOutcome

router = APIRouter(prefix="/export", tags=["export"])


def _rows_to_csv(rows: list[dict]) -> str:
    """Convert list of dicts to CSV string."""
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _model_to_dict(obj) -> dict:
    """Convert an ORM model instance to a dict."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


@router.get("/signals")
async def export_signals(
    from_ts: int = Query(0, alias="from", description="Start timestamp"),
    to_ts: int = Query(0, alias="to", description="End timestamp"),
    format: str = Query("json", description="Output format: json or csv"),
    db: AsyncSession = Depends(get_db),
):
    """Export signal history."""
    if to_ts == 0:
        to_ts = int(time.time())

    stmt = (
        select(Signal)
        .where(Signal.generated_at >= from_ts)
        .where(Signal.generated_at <= to_ts)
        .order_by(Signal.generated_at.desc())
    )
    result = await db.execute(stmt)
    signals = result.scalars().all()
    rows = [_model_to_dict(s) for s in signals]

    if format == "csv":
        csv_data = _rows_to_csv(rows)
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=signals.csv"},
        )
    return rows


@router.get("/market")
async def export_market(
    symbol: str = Query("", description="Filter by symbol"),
    from_ts: int = Query(0, alias="from", description="Start timestamp"),
    to_ts: int = Query(0, alias="to", description="End timestamp"),
    format: str = Query("json", description="Output format: json or csv"),
    db: AsyncSession = Depends(get_db),
):
    """Export market snapshot data."""
    if to_ts == 0:
        to_ts = int(time.time())

    stmt = (
        select(MarketSnapshot)
        .where(MarketSnapshot.captured_at >= from_ts)
        .where(MarketSnapshot.captured_at <= to_ts)
    )
    if symbol:
        stmt = stmt.where(MarketSnapshot.symbol == symbol.upper())
    stmt = stmt.order_by(MarketSnapshot.captured_at.desc())

    result = await db.execute(stmt)
    snapshots = result.scalars().all()
    rows = [_model_to_dict(s) for s in snapshots]

    if format == "csv":
        csv_data = _rows_to_csv(rows)
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=market.csv"},
        )
    return rows


@router.get("/trades")
async def export_trades(
    from_ts: int = Query(0, alias="from", description="Start timestamp"),
    to_ts: int = Query(0, alias="to", description="End timestamp"),
    format: str = Query("json", description="Output format: json or csv"),
    db: AsyncSession = Depends(get_db),
):
    """Export trade records."""
    if to_ts == 0:
        to_ts = int(time.time())

    stmt = (
        select(TradeOutcome)
        .where(TradeOutcome.entry_time >= from_ts)
        .where(TradeOutcome.entry_time <= to_ts)
        .order_by(TradeOutcome.entry_time.desc())
    )
    result = await db.execute(stmt)
    trades = result.scalars().all()
    rows = [_model_to_dict(t) for t in trades]

    if format == "csv":
        csv_data = _rows_to_csv(rows)
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=trades.csv"},
        )
    return rows
