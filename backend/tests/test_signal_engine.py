"""
Unit tests for backend.signal_engine module.
Tests cooldown, dedup, BTC crash guard, max signal limit, and reason strings.
"""
import time
import pytest
from backend.signal_engine import (
    generate_signals,
    clear_trackers,
    _is_on_cooldown,
    _has_active_signal,
    _build_reason_string,
    _format_entry_range,
    _cooldown_tracker,
    _active_signals,
    BTC_CRASH_THRESHOLD,
    MAX_SIGNALS_PER_CYCLE,
    COOLDOWN_SECONDS,
)


def _make_metrics(symbol: str, score_target: str = "high",
                  btc_15m_change: float = 0.0) -> dict:
    """Helper to create metric dicts with controllable score outcomes."""
    if score_target == "high":
        return {
            "symbol": symbol,
            "price": 100.0,
            "price_change_5m": 1.5,
            "price_change_15m": 3.0,
            "volume_sma_ratio": 3.0,
            "rsi": 60.0,
            "vwap_deviation": 0.5,
            "btc_regime": "UP",
            "btc_15m_change": btc_15m_change,
        }
    elif score_target == "low":
        return {
            "symbol": symbol,
            "price": 100.0,
            "price_change_5m": -0.5,
            "price_change_15m": -1.0,
            "volume_sma_ratio": 0.5,
            "rsi": 30.0,
            "vwap_deviation": -1.0,
            "btc_regime": "DOWN",
            "btc_15m_change": btc_15m_change,
        }
    else:  # moderate
        return {
            "symbol": symbol,
            "price": 100.0,
            "price_change_5m": 0.6,
            "price_change_15m": 1.2,
            "volume_sma_ratio": 1.8,
            "rsi": 58.0,
            "vwap_deviation": 0.2,
            "btc_regime": "NEUTRAL",
            "btc_15m_change": btc_15m_change,
        }


@pytest.fixture(autouse=True)
def reset_trackers():
    """Reset in-memory trackers before each test."""
    clear_trackers()
    yield
    clear_trackers()


class TestBTCCrashGuard:
    def test_crash_suppresses_all(self):
        """When BTC 15m < -1.5%, no signals should be generated."""
        data = [
            _make_metrics("BTCUSDT", "high", btc_15m_change=-2.0),
            _make_metrics("ETHUSDT", "high", btc_15m_change=-2.0),
        ]
        signals = generate_signals(data)
        assert len(signals) == 0

    def test_normal_market_allows_signals(self):
        """When BTC is stable, signals should be generated."""
        data = [
            _make_metrics("BTCUSDT", "high", btc_15m_change=0.5),
            _make_metrics("ETHUSDT", "high", btc_15m_change=0.5),
        ]
        signals = generate_signals(data)
        assert len(signals) > 0


class TestCooldown:
    def test_cooldown_blocks_repeat(self):
        """Same coin should not signal twice within cooldown period."""
        # Manually set cooldown for ETHUSDT (as if signal was just generated)
        _cooldown_tracker["ETHUSDT"] = time.time()
        data = [_make_metrics("ETHUSDT", "high")]
        signals = generate_signals(data)
        assert len(signals) == 0  # Should be blocked by cooldown

    def test_cooldown_expires(self):
        """After cooldown expires, the coin should signal again."""
        # Set cooldown in the past (expired)
        _cooldown_tracker["ETHUSDT"] = time.time() - COOLDOWN_SECONDS - 1
        data = [_make_metrics("ETHUSDT", "high")]
        signals = generate_signals(data)
        assert len(signals) == 1


class TestDedup:
    def test_no_duplicate_signals(self):
        """Same coin should not have two active signals."""
        data = [_make_metrics("ETHUSDT", "high")]
        signals1 = generate_signals(data)
        assert len(signals1) == 1
        # Try again — should be blocked
        signals2 = generate_signals(data)
        assert len(signals2) == 0


class TestMaxSignals:
    def test_max_three_per_cycle(self):
        """Should emit at most 3 signals per cycle."""
        data = [
            _make_metrics("ETHUSDT", "high"),
            _make_metrics("SOLUSDT", "high"),
            _make_metrics("BNBUSDT", "high"),
            _make_metrics("ADAUSDT", "high"),
            _make_metrics("DOTUSDT", "high"),
        ]
        signals = generate_signals(data)
        assert len(signals) <= MAX_SIGNALS_PER_CYCLE


class TestReject:
    def test_low_score_rejected(self):
        """Low-scoring coins should not generate signals."""
        data = [_make_metrics("ETHUSDT", "low")]
        signals = generate_signals(data)
        assert len(signals) == 0


class TestEmptyInput:
    def test_empty_list(self):
        """Empty market data → no signals."""
        assert generate_signals([]) == []


class TestEntryRange:
    def test_range_around_price(self):
        """Entry range should be ±0.2% around price."""
        low, high = _format_entry_range(100.0)
        assert low == 99.8
        assert high == 100.2

    def test_zero_price(self):
        low, high = _format_entry_range(0.0)
        assert low == 0.0
        assert high == 0.0


class TestReasonString:
    def test_full_reason(self):
        metrics = {
            "price_change_5m": 1.2,
            "volume_sma_ratio": 2.5,
            "rsi": 60.0,
            "btc_regime": "UP",
        }
        reason = _build_reason_string(metrics)
        assert "Momentum" in reason
        assert "Vol" in reason
        assert "RSI" in reason
        assert "BTC" in reason

    def test_empty_metrics(self):
        reason = _build_reason_string({})
        assert reason == "Signal generated"
