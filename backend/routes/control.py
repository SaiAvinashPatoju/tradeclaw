"""
TradeClaw - Runtime Control Routes
Allows switching data source mode and algorithm profile at runtime.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..runtime_config import (
    DATA_SOURCE_MODES,
    get_runtime_config,
    set_data_source_mode,
    set_runtime_algorithm_profile,
)
from ..rule_engine import ALGORITHM_PROFILES
from ..security import require_api_key

router = APIRouter(prefix="/control", tags=["control"])


class EngineConfigOut(BaseModel):
    data_source_mode: str
    algorithm_profile: str
    available_data_source_modes: list[str]
    available_algorithm_profiles: list[str]


class EngineConfigUpdate(BaseModel):
    data_source_mode: str | None = None
    algorithm_profile: str | None = None


@router.get("/engine", response_model=EngineConfigOut)
async def get_engine_config():
    cfg = get_runtime_config()
    return EngineConfigOut(
        data_source_mode=cfg["data_source_mode"],
        algorithm_profile=cfg["algorithm_profile"],
        available_data_source_modes=sorted(DATA_SOURCE_MODES),
        available_algorithm_profiles=sorted(ALGORITHM_PROFILES),
    )


@router.put("/engine", response_model=EngineConfigOut, dependencies=[Depends(require_api_key)])
async def update_engine_config(payload: EngineConfigUpdate):
    try:
        if payload.data_source_mode is not None:
            set_data_source_mode(payload.data_source_mode)
        if payload.algorithm_profile is not None:
            set_runtime_algorithm_profile(payload.algorithm_profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cfg = get_runtime_config()
    return EngineConfigOut(
        data_source_mode=cfg["data_source_mode"],
        algorithm_profile=cfg["algorithm_profile"],
        available_data_source_modes=sorted(DATA_SOURCE_MODES),
        available_algorithm_profiles=sorted(ALGORITHM_PROFILES),
    )
