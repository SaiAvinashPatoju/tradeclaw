from pydantic import BaseModel
from typing import List, Optional

class SignalResponse(BaseModel):
    id: str
    symbol: str
    entry_low: float
    entry_high: float
    target_pct: float
    stop_loss_pct: float
    score: int
    confidence: str
    reason: str
    btc_regime: str
    rsi: float
    volume_spike: float
    created_at: int
    expiry_at: int
    status: str

    class Config:
        from_attributes = True

class SignalListResponse(BaseModel):
    signals: List[SignalResponse]

class HealthResponse(BaseModel):
    status: str
    last_scan: Optional[int] = None
    signals_today: int = 0
