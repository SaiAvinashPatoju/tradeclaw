"""
TradeClaw — Technical Indicators Module
Pure functions for RSI, VWAP, volume analysis, and BTC regime detection.
"""


def calculate_rsi(closes: list[float], period: int = 14) -> float:
    """
    Calculate RSI using Wilder's smoothing method.
    Returns RSI value between 0 and 100.
    Requires at least `period + 1` close prices.
    """
    if len(closes) < period + 1:
        return 50.0  # Neutral default if insufficient data

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    # Initial average gain/loss
    gains = [d if d > 0 else 0.0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0.0 for d in deltas[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Wilder's smoothing for remaining periods
    for i in range(period, len(deltas)):
        delta = deltas[i]
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


def calculate_vwap(highs: list[float], lows: list[float],
                   closes: list[float], volumes: list[float]) -> float:
    """
    Calculate Volume Weighted Average Price.
    VWAP = sum(typical_price * volume) / sum(volume)
    """
    if not highs or not volumes or len(highs) != len(volumes):
        return 0.0

    total_volume = sum(volumes)
    if total_volume == 0:
        return 0.0

    typical_prices = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
    vwap = sum(tp * v for tp, v in zip(typical_prices, volumes)) / total_volume
    return round(vwap, 8)


def calculate_volume_sma_ratio(volumes: list[float], period: int = 20) -> float:
    """
    Calculate current volume vs SMA of volume.
    Returns ratio: current_volume / sma(volume, period).
    Ratio > 1.0 means above-average volume.
    """
    if len(volumes) < period:
        return 1.0  # Neutral default

    sma = sum(volumes[-period:]) / period
    if sma == 0:
        return 1.0

    current_volume = volumes[-1]
    return round(current_volume / sma, 2)


def calculate_price_change_pct(open_price: float, close_price: float) -> float:
    """
    Calculate percentage price change.
    Returns: (close - open) / open * 100
    """
    if open_price == 0:
        return 0.0
    return round((close_price - open_price) / open_price * 100, 4)


def determine_btc_regime(btc_1h_change: float) -> str:
    """
    Determine BTC market regime from 1h price change.
    UP:      > +0.5%
    NEUTRAL: -0.5% to +0.5%
    DOWN:    < -0.5%
    """
    if btc_1h_change > 0.5:
        return "UP"
    elif btc_1h_change < -0.5:
        return "DOWN"
    else:
        return "NEUTRAL"


def calculate_vwap_deviation(current_price: float, vwap: float) -> float:
    """
    Calculate percentage deviation of price from VWAP.
    Positive = above VWAP, negative = below.
    """
    if vwap == 0:
        return 0.0
    return round((current_price - vwap) / vwap * 100, 4)
