"""
TradeClaw — Security Utilities
Provides FastAPI dependencies for optional API-key enforcement.
"""
import logging

from fastapi import Header, HTTPException, status

from .config import TRADECLAW_API_KEY

logger = logging.getLogger("tradeclaw.security")


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    """
    FastAPI dependency that enforces the X-API-Key header when
    TRADECLAW_API_KEY is configured. If the env var is empty,
    authentication is skipped (development mode).
    """
    if not TRADECLAW_API_KEY:
        return  # auth disabled — dev/open mode
    if x_api_key != TRADECLAW_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
