"""
TradeClaw — Composite Scoring Engine
Multi-factor scoring system with weighted sub-scores and confidence tier classification.
"""

# ── Weights (must sum to 1.0) ──────────────────────────────────────────
WEIGHT_MOMENTUM_5M = 0.25
WEIGHT_MOMENTUM_15M = 0.20
WEIGHT_VOLUME_SPIKE = 0.20
WEIGHT_RSI = 0.15
WEIGHT_VWAP = 0.10
WEIGHT_BTC_REGIME = 0.10

# ── Confidence Tiers ──────────────────────────────────────────────────
TIER_SNIPER = "SNIPER"      # ≥ 80
TIER_HIGH = "HIGH"          # ≥ 65
TIER_MODERATE = "MODERATE"  # ≥ 50
TIER_REJECT = "REJECT"      # < 50


def _interpolate(value: float, low: float, low_score: float,
                 high: float, high_score: float) -> float:
    """Linear interpolation between two points, clamped to [0, 100]."""
    if value <= low:
        return low_score
    if value >= high:
        return high_score
    ratio = (value - low) / (high - low)
    score = low_score + ratio * (high_score - low_score)
    return max(0.0, min(100.0, score))


def score_momentum_5m(change_pct: float) -> float:
    """
    Score 5-minute momentum.
    +0.5% → 50pts, +0.8% → 70pts, +1.2%+ → 100pts
    """
    if change_pct <= 0:
        return 0.0
    if change_pct <= 0.5:
        return _interpolate(change_pct, 0, 0, 0.5, 50)
    if change_pct <= 0.8:
        return _interpolate(change_pct, 0.5, 50, 0.8, 70)
    if change_pct <= 1.2:
        return _interpolate(change_pct, 0.8, 70, 1.2, 100)
    return 100.0


def score_momentum_15m(change_pct: float) -> float:
    """
    Score 15-minute momentum.
    +1.0% → 50pts, +1.5% → 75pts, +2.5%+ → 100pts
    """
    if change_pct <= 0:
        return 0.0
    if change_pct <= 1.0:
        return _interpolate(change_pct, 0, 0, 1.0, 50)
    if change_pct <= 1.5:
        return _interpolate(change_pct, 1.0, 50, 1.5, 75)
    if change_pct <= 2.5:
        return _interpolate(change_pct, 1.5, 75, 2.5, 100)
    return 100.0


def score_volume_spike(ratio: float) -> float:
    """
    Score volume spike ratio (current vol / SMA vol).
    1.5x → 50pts, 2.0x → 75pts, 3.0x+ → 100pts
    """
    if ratio <= 1.0:
        return 0.0
    if ratio <= 1.5:
        return _interpolate(ratio, 1.0, 0, 1.5, 50)
    if ratio <= 2.0:
        return _interpolate(ratio, 1.5, 50, 2.0, 75)
    if ratio <= 3.0:
        return _interpolate(ratio, 2.0, 75, 3.0, 100)
    return 100.0


def score_rsi(rsi: float) -> float:
    """
    Score RSI sweet spot.
    55–65 → 100pts (ideal), 50–70 → 70pts (good), outside → 0pts
    """
    if 55 <= rsi <= 65:
        return 100.0
    if 50 <= rsi < 55:
        return _interpolate(rsi, 50, 70, 55, 100)
    if 65 < rsi <= 70:
        return _interpolate(rsi, 65, 100, 70, 70)
    return 0.0


def score_vwap_position(deviation_pct: float) -> float:
    """
    Score price position relative to VWAP.
    Above VWAP +0.3% → 80pts, at VWAP → 50pts, below → 20pts
    """
    if deviation_pct >= 0.3:
        return 80.0
    if deviation_pct >= 0:
        return _interpolate(deviation_pct, 0, 50, 0.3, 80)
    if deviation_pct >= -0.3:
        return _interpolate(deviation_pct, -0.3, 20, 0, 50)
    return 20.0


def score_btc_regime(regime: str) -> float:
    """
    Score BTC market regime.
    UP → 100pts, NEUTRAL → 60pts, DOWN → 0pts
    """
    regime_scores = {
        "UP": 100.0,
        "NEUTRAL": 60.0,
        "DOWN": 0.0,
    }
    return regime_scores.get(regime.upper(), 0.0)


def calculate_composite_score(metrics: dict) -> tuple[int, str]:
    """
    Calculate weighted composite score from all factors.

    Args:
        metrics: dict with keys:
            - price_change_5m (float): 5m price change %
            - price_change_15m (float): 15m price change %
            - volume_sma_ratio (float): volume spike ratio
            - rsi (float): RSI value
            - vwap_deviation (float): VWAP deviation %
            - btc_regime (str): "UP" / "NEUTRAL" / "DOWN"

    Returns:
        (score: int, confidence_tier: str)
    """
    s_mom5 = score_momentum_5m(metrics.get("price_change_5m", 0))
    s_mom15 = score_momentum_15m(metrics.get("price_change_15m", 0))
    s_vol = score_volume_spike(metrics.get("volume_sma_ratio", 1.0))
    s_rsi = score_rsi(metrics.get("rsi", 50))
    s_vwap = score_vwap_position(metrics.get("vwap_deviation", 0))
    s_btc = score_btc_regime(metrics.get("btc_regime", "NEUTRAL"))

    composite = (
        s_mom5 * WEIGHT_MOMENTUM_5M +
        s_mom15 * WEIGHT_MOMENTUM_15M +
        s_vol * WEIGHT_VOLUME_SPIKE +
        s_rsi * WEIGHT_RSI +
        s_vwap * WEIGHT_VWAP +
        s_btc * WEIGHT_BTC_REGIME
    )

    score = int(round(composite))

    if score >= 80:
        tier = TIER_SNIPER
    elif score >= 65:
        tier = TIER_HIGH
    elif score >= 50:
        tier = TIER_MODERATE
    else:
        tier = TIER_REJECT

    return score, tier
