"""
TradeClaw - Runtime Engine Configuration
Holds mutable in-memory runtime settings controlled via API.
"""
import os

from .rule_engine import ALGORITHM_PROFILES, set_algorithm_profile

DATA_SOURCE_MODES = {"simulator", "real"}


def _env_or_default(name: str, default: str) -> str:
    return os.getenv(name, default).strip().lower()


_runtime_config = {
    "data_source_mode": _env_or_default("TRADECLAW_DATA_SOURCE_MODE", "simulator"),
    "algorithm_profile": _env_or_default("TRADECLAW_ALGORITHM_PROFILE", "mid"),
}


def _sanitize_state() -> None:
    if _runtime_config["data_source_mode"] not in DATA_SOURCE_MODES:
        _runtime_config["data_source_mode"] = "simulator"
    if _runtime_config["algorithm_profile"] not in ALGORITHM_PROFILES:
        _runtime_config["algorithm_profile"] = "mid"


_sanitize_state()
set_algorithm_profile(_runtime_config["algorithm_profile"])


def get_runtime_config() -> dict:
    return {
        "data_source_mode": _runtime_config["data_source_mode"],
        "algorithm_profile": _runtime_config["algorithm_profile"],
    }


def set_data_source_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized not in DATA_SOURCE_MODES:
        raise ValueError(f"Invalid data_source_mode: {mode}")
    _runtime_config["data_source_mode"] = normalized
    return normalized


def set_runtime_algorithm_profile(profile: str) -> str:
    normalized = (profile or "").strip().lower()
    set_algorithm_profile(normalized)
    _runtime_config["algorithm_profile"] = normalized
    return normalized
