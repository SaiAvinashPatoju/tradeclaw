"""
TradeClaw — Feature Engineering
Computes explicit engineered features per coin based on v1 architecture spec.
"""
import numpy as np

def calculate_price_change_pct(open_price: float, close_price: float) -> float:
    if open_price == 0:
        return 0.0
    return (close_price - open_price) / open_price

def calculate_rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def compute_features(data_5m: dict, data_15m: dict, data_1h: dict, ticker_24h: dict) -> dict:
    """
    Compute features for a single coin.
    data_* format: {"opens": [...], "highs": [...], "lows": [...], "closes": [...], "volumes": [...]}
    ticker_24h format: {"symbol": "...", "quoteVolume": "...", "askPrice": "...", "bidPrice": "..."}
    """
    closes_5m = data_5m["closes"]
    opens_5m = data_5m["opens"]
    highs_5m = data_5m["highs"]
    lows_5m = data_5m["lows"]
    volumes_5m = data_5m["volumes"]

    # Basic price safety
    if not closes_5m:
        return None

    current_price = closes_5m[-1]

    # --- A. Price Momentum ---
    momentum_5m = calculate_price_change_pct(opens_5m[-1], closes_5m[-1]) if closes_5m else 0.0
    momentum_15m = calculate_price_change_pct(data_15m["opens"][-1], data_15m["closes"][-1]) if data_15m["closes"] else 0.0
    momentum_1h = calculate_price_change_pct(data_1h["opens"][-1], data_1h["closes"][-1]) if data_1h["closes"] else 0.0

    # Body-to-wick ratio
    candle_open, candle_high, candle_low, candle_close = opens_5m[-1], highs_5m[-1], lows_5m[-1], closes_5m[-1]
    body = abs(candle_close - candle_open)
    wick = candle_high - candle_low
    body_wick_ratio = body / (wick + 1e-8)

    # Trend persistence (last 3 candles 5m)
    PERSISTENCE_WINDOW = 3
    if len(closes_5m) > PERSISTENCE_WINDOW:
        recent_closes = closes_5m[-(PERSISTENCE_WINDOW+1):]
        ups = sum(1 for i in range(1, len(recent_closes)) if recent_closes[i] > recent_closes[i-1])
        trend_persistence = ups / PERSISTENCE_WINDOW
    else:
        trend_persistence = 0.0

    # --- B. Relative Volume / Liquidity ---
    VOLUME_MA_PERIOD = 20
    if len(volumes_5m) >= VOLUME_MA_PERIOD:
        volume_ma = sum(volumes_5m[-VOLUME_MA_PERIOD:]) / VOLUME_MA_PERIOD
    elif len(volumes_5m) > 0:
        volume_ma = sum(volumes_5m) / len(volumes_5m)
    else:
        volume_ma = 0.0
        
    rel_volume = volumes_5m[-1] / (volume_ma + 1e-8)

    # 24h liquidity & Spread
    volume_24h_usdt = float(ticker_24h.get("quoteVolume", 0.0))
    ask_price = float(ticker_24h.get("askPrice", 0.0))
    bid_price = float(ticker_24h.get("bidPrice", 0.0))
    
    if ask_price > 0 and bid_price > 0:
        mid_price = (ask_price + bid_price) / 2
        spread_pct = (ask_price - bid_price) / mid_price
    else:
        # fallback estimate if order book snapshot not provided
        spread_pct = 1.0 / (volume_24h_usdt / (current_price + 1e-8) + 1e-8)

    # --- D. Risk / Exhaustion ---
    rsi = calculate_rsi(closes_5m, period=14)
    OVEREXTENSION_THRESHOLD = 0.03 # 3% move built-in in 1h
    overextension = bool(momentum_1h > OVEREXTENSION_THRESHOLD)

    return {
        "price": current_price,
        "momentum_5m": momentum_5m,
        "momentum_15m": momentum_15m,
        "momentum_1h": momentum_1h,
        "body_wick_ratio": body_wick_ratio,
        "trend_persistence": trend_persistence,
        "volume_ma": volume_ma,
        "rel_volume": rel_volume,
        "volume_24h_usdt": volume_24h_usdt,
        "spread_pct": spread_pct,
        "rsi": rsi,
        "overextension": overextension,
        "already_pumped": False, # Defaults for now, usually needs a rolling state tracker
    }

def compute_relative_strength(features_list: list[dict], btc_momentum_5m: float) -> list[dict]:
    """
    Computes cross-sectional features relative to the candidate universe.
    """
    if not features_list:
        return []

    moms_5m = [f["momentum_5m"] for f in features_list if f is not None]
    if not moms_5m:
        return features_list

    market_median_5m = np.median(moms_5m)

    # Ranked ascending: lowest momentum gets 0, highest gets len-1
    temp_sorted = sorted(features_list, key=lambda x: x["momentum_5m"])
    for i, f in enumerate(temp_sorted):
        f["breakout_rank"] = i / len(temp_sorted)

    for f in features_list:
        f["rel_strength_5m"] = f["momentum_5m"] - market_median_5m
        f["coin_vs_btc"] = f["momentum_5m"] - btc_momentum_5m

    return features_list
