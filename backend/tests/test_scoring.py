"""
Unit tests for backend.scoring module.
Tests each sub-scorer independently and composite score with tier classification.
"""
import pytest
from backend.scoring import (
    score_momentum_5m,
    score_momentum_15m,
    score_volume_spike,
    score_rsi,
    score_vwap_position,
    score_btc_regime,
    calculate_composite_score,
    TIER_SNIPER,
    TIER_HIGH,
    TIER_MODERATE,
    TIER_REJECT,
)


class TestMomentum5m:
    def test_zero_change(self):
        assert score_momentum_5m(0) == 0.0

    def test_negative_change(self):
        assert score_momentum_5m(-1.0) == 0.0

    def test_half_percent(self):
        assert score_momentum_5m(0.5) == 50.0

    def test_above_threshold(self):
        assert score_momentum_5m(1.2) == 100.0

    def test_extreme(self):
        assert score_momentum_5m(5.0) == 100.0

    def test_interpolation(self):
        score = score_momentum_5m(0.65)
        assert 50 < score < 70


class TestMomentum15m:
    def test_zero(self):
        assert score_momentum_15m(0) == 0.0

    def test_one_percent(self):
        assert score_momentum_15m(1.0) == 50.0

    def test_above_max(self):
        assert score_momentum_15m(3.0) == 100.0


class TestVolumeSpike:
    def test_normal_volume(self):
        assert score_volume_spike(1.0) == 0.0

    def test_spike_1_5x(self):
        assert score_volume_spike(1.5) == 50.0

    def test_spike_3x(self):
        assert score_volume_spike(3.0) == 100.0

    def test_below_normal(self):
        assert score_volume_spike(0.5) == 0.0


class TestRSI:
    def test_sweet_spot(self):
        """RSI 55-65 is ideal → 100 pts."""
        assert score_rsi(60.0) == 100.0
        assert score_rsi(55.0) == 100.0
        assert score_rsi(65.0) == 100.0

    def test_good_range(self):
        """RSI 50-55 or 65-70 → 70 pts."""
        assert score_rsi(50.0) == 70.0
        assert score_rsi(70.0) == 70.0

    def test_outside(self):
        """RSI outside 50-70 → 0 pts."""
        assert score_rsi(30.0) == 0.0
        assert score_rsi(80.0) == 0.0


class TestVWAPPosition:
    def test_above(self):
        assert score_vwap_position(0.5) == 80.0

    def test_at_vwap(self):
        assert score_vwap_position(0.0) == 50.0

    def test_below(self):
        score = score_vwap_position(-0.5)
        assert score == 20.0


class TestBTCRegime:
    def test_up(self):
        assert score_btc_regime("UP") == 100.0

    def test_neutral(self):
        assert score_btc_regime("NEUTRAL") == 60.0

    def test_down(self):
        assert score_btc_regime("DOWN") == 0.0

    def test_case_insensitive(self):
        assert score_btc_regime("up") == 100.0


class TestCompositeScore:
    def test_perfect_metrics(self):
        """All perfect metrics → SNIPER tier."""
        metrics = {
            "price_change_5m": 1.5,
            "price_change_15m": 3.0,
            "volume_sma_ratio": 3.5,
            "rsi": 60.0,
            "vwap_deviation": 0.5,
            "btc_regime": "UP",
        }
        score, tier = calculate_composite_score(metrics)
        assert score >= 80
        assert tier == TIER_SNIPER

    def test_garbage_metrics(self):
        """All bad metrics → REJECT tier."""
        metrics = {
            "price_change_5m": -1.0,
            "price_change_15m": -1.0,
            "volume_sma_ratio": 0.5,
            "rsi": 30.0,
            "vwap_deviation": -1.0,
            "btc_regime": "DOWN",
        }
        score, tier = calculate_composite_score(metrics)
        assert score < 50
        assert tier == TIER_REJECT

    def test_moderate_metrics(self):
        """Mixed metrics → MODERATE or HIGH tier."""
        metrics = {
            "price_change_5m": 0.5,
            "price_change_15m": 1.0,
            "volume_sma_ratio": 1.5,
            "rsi": 55.0,
            "vwap_deviation": 0.1,
            "btc_regime": "NEUTRAL",
        }
        score, tier = calculate_composite_score(metrics)
        assert 45 <= score <= 75
        assert tier in (TIER_MODERATE, TIER_HIGH)

    def test_empty_metrics(self):
        """Empty dict → should not crash, returns REJECT."""
        score, tier = calculate_composite_score({})
        assert tier == TIER_REJECT

    def test_score_range(self):
        """Score should always be 0-100."""
        metrics = {
            "price_change_5m": 1.5,
            "price_change_15m": 3.0,
            "volume_sma_ratio": 5.0,
            "rsi": 60.0,
            "vwap_deviation": 1.0,
            "btc_regime": "UP",
        }
        score, _ = calculate_composite_score(metrics)
        assert 0 <= score <= 100
