"""
Unit tests for backend.indicators module.
Tests RSI, VWAP, volume ratio, price change, and BTC regime.
"""
import pytest
from backend.indicators import (
    calculate_rsi,
    calculate_vwap,
    calculate_volume_sma_ratio,
    calculate_price_change_pct,
    determine_btc_regime,
    calculate_vwap_deviation,
)


class TestRSI:
    def test_rsi_all_gains(self):
        """All prices going up → RSI should be 100."""
        closes = [float(i) for i in range(1, 20)]  # 1,2,3,...,19
        assert calculate_rsi(closes) == 100.0

    def test_rsi_all_losses(self):
        """All prices going down → RSI should be 0."""
        closes = [float(i) for i in range(19, 0, -1)]  # 19,18,...,1
        assert calculate_rsi(closes) == 0.0

    def test_rsi_neutral(self):
        """Alternating up/down → RSI should be around 50."""
        closes = [100.0]
        for i in range(20):
            if i % 2 == 0:
                closes.append(closes[-1] + 1.0)
            else:
                closes.append(closes[-1] - 1.0)
        rsi = calculate_rsi(closes)
        assert 40 <= rsi <= 60, f"Expected ~50, got {rsi}"

    def test_rsi_insufficient_data(self):
        """Too few data points → returns neutral 50."""
        closes = [100.0, 101.0, 102.0]
        assert calculate_rsi(closes) == 50.0

    def test_rsi_range(self):
        """RSI should always be between 0 and 100."""
        import random
        random.seed(42)
        closes = [100.0]
        for _ in range(50):
            closes.append(closes[-1] + random.uniform(-5, 5))
        rsi = calculate_rsi(closes)
        assert 0 <= rsi <= 100


class TestVWAP:
    def test_vwap_simple(self):
        """VWAP with equal volumes should equal mean of typical prices."""
        highs = [105.0, 110.0]
        lows = [95.0, 90.0]
        closes = [100.0, 100.0]
        volumes = [1000.0, 1000.0]
        vwap = calculate_vwap(highs, lows, closes, volumes)
        # typical prices: (105+95+100)/3=100, (110+90+100)/3=100
        assert vwap == 100.0

    def test_vwap_weighted(self):
        """VWAP should weight by volume."""
        highs = [30.0, 60.0]
        lows = [10.0, 40.0]
        closes = [20.0, 50.0]
        volumes = [100.0, 300.0]
        vwap = calculate_vwap(highs, lows, closes, volumes)
        # tp1 = 20, tp2 = 50
        # vwap = (20*100 + 50*300) / 400 = 17000/400 = 42.5
        assert vwap == 42.5

    def test_vwap_empty(self):
        """Empty inputs → returns 0."""
        assert calculate_vwap([], [], [], []) == 0.0

    def test_vwap_zero_volume(self):
        """Zero total volume → returns 0."""
        assert calculate_vwap([100.0], [90.0], [95.0], [0.0]) == 0.0


class TestVolumeSMARatio:
    def test_ratio_average(self):
        """Current volume equals average → ratio = 1.0."""
        volumes = [100.0] * 20
        ratio = calculate_volume_sma_ratio(volumes)
        assert ratio == 1.0

    def test_ratio_spike(self):
        """Current volume is 3x average → ratio = 3.0."""
        volumes = [100.0] * 19 + [300.0]
        ratio = calculate_volume_sma_ratio(volumes)
        # SMA of all 20 = (19*100 + 300)/20 = 2200/20 = 110
        # But SMA uses last 20 periods, current = last element
        # ratio = 300 / 110 = 2.73
        assert ratio > 2.0

    def test_ratio_insufficient(self):
        """Too few data points → returns neutral 1.0."""
        volumes = [100.0, 200.0]
        assert calculate_volume_sma_ratio(volumes) == 1.0


class TestPriceChange:
    def test_positive_change(self):
        """Price going up → positive percentage."""
        assert calculate_price_change_pct(100.0, 105.0) == 5.0

    def test_negative_change(self):
        """Price going down → negative percentage."""
        assert calculate_price_change_pct(100.0, 95.0) == -5.0

    def test_no_change(self):
        """Same price → 0%."""
        assert calculate_price_change_pct(100.0, 100.0) == 0.0

    def test_zero_open(self):
        """Zero open price → returns 0 (avoid division by zero)."""
        assert calculate_price_change_pct(0.0, 100.0) == 0.0


class TestBTCRegime:
    def test_up(self):
        assert determine_btc_regime(1.0) == "UP"
        assert determine_btc_regime(0.51) == "UP"

    def test_neutral(self):
        assert determine_btc_regime(0.0) == "NEUTRAL"
        assert determine_btc_regime(0.5) == "NEUTRAL"
        assert determine_btc_regime(-0.5) == "NEUTRAL"

    def test_down(self):
        assert determine_btc_regime(-1.0) == "DOWN"
        assert determine_btc_regime(-0.51) == "DOWN"


class TestVWAPDeviation:
    def test_above_vwap(self):
        dev = calculate_vwap_deviation(103.0, 100.0)
        assert dev == 3.0

    def test_below_vwap(self):
        dev = calculate_vwap_deviation(97.0, 100.0)
        assert dev == -3.0

    def test_at_vwap(self):
        assert calculate_vwap_deviation(100.0, 100.0) == 0.0

    def test_zero_vwap(self):
        assert calculate_vwap_deviation(100.0, 0.0) == 0.0
