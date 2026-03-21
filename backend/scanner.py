"""
TradeClaw — Market Scanner
Scans dynamic rolling top 80 spot altcoins, fetches klines, and delegates to features.py.
"""
import asyncio
import logging
import time
from binance import AsyncClient

from .features import compute_features, compute_relative_strength

logger = logging.getLogger("tradeclaw.scanner")

RANK_UNIVERSE_SIZE = 80
LIQUIDITY_MIN = 3_000_000 # Minimum 24h volume in USDT

async def _fetch_klines(client: AsyncClient, symbol: str, interval: str, limit: int = 50) -> dict:
    try:
        klines = await client.get_klines(symbol=symbol, interval=interval, limit=limit)
        if not klines:
            return {"opens": [], "highs": [], "lows": [], "closes": [], "volumes": []}
        return {
            "opens": [float(k[1]) for k in klines],
            "highs": [float(k[2]) for k in klines],
            "lows": [float(k[3]) for k in klines],
            "closes": [float(k[4]) for k in klines],
            "volumes": [float(k[5]) for k in klines],
        }
    except Exception as e:
        logger.warning(f"Failed to fetch {interval} klines for {symbol}: {e}")
        return {"opens": [], "highs": [], "lows": [], "closes": [], "volumes": []}

async def _scan_single_pair(client: AsyncClient, ticker_24h: dict) -> dict | None:
    symbol = ticker_24h["symbol"]
    try:
        klines_5m = await _fetch_klines(client, symbol, "5m", 50)
        klines_15m = await _fetch_klines(client, symbol, "15m", 5)
        klines_1h = await _fetch_klines(client, symbol, "1h", 5)

        if not klines_5m["closes"] or not klines_15m["closes"] or not klines_1h["closes"]:
            return None

        # Compute raw features
        features = compute_features(klines_5m, klines_15m, klines_1h, ticker_24h)
        if not features:
            return None
            
        features["symbol"] = symbol
        features["timestamp"] = int(time.time())
        return features

    except Exception as e:
        logger.error(f"Error scanning {symbol}: {e}")
        return None

async def scan_market(api_key: str, api_secret: str) -> list[dict]:
    client = await AsyncClient.create(api_key, api_secret)
    results = []
    try:
        logger.info("Fetching 24h tickers to build dynamic universe...")
        tickers = await client.get_ticker()
        
        # Filter for USDT spot pairs, exclude leveraged tokens and stablecoins
        valid_tickers = []
        for t in tickers:
            sym = t["symbol"]
            if sym.endswith("USDT") and not sym.endswith("DOWNUSDT") and not sym.endswith("UPUSDT"):
                if sym not in ["BUSDUSDT", "USDCUSDT", "TUSDUSDT", "FDUSDUSDT"]:
                    vol = float(t.get("quoteVolume", 0.0))
                    if vol >= LIQUIDITY_MIN:
                        valid_tickers.append(t)
        
        # Sort by volume descending and take top N
        valid_tickers.sort(key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
        universe = valid_tickers[:RANK_UNIVERSE_SIZE]
        logger.info(f"Selected {len(universe)} symbols for core scan.")

        # Also fetch BTC for reference
        btc_features = None
        btc_ticker = next((t for t in tickers if t["symbol"] == "BTCUSDT"), None)
        if btc_ticker:
            btc_features = await _scan_single_pair(client, btc_ticker)

        btc_momentum_5m = btc_features["momentum_5m"] if btc_features else 0.0

        # Scan universe concurrently in batches to avoid rate limits
        batch_size = 10
        raw_features = []
        for i in range(0, len(universe), batch_size):
            batch = universe[i:i + batch_size]
            tasks = [_scan_single_pair(client, ticker) for ticker in batch]
            batch_results = await asyncio.gather(*tasks)
            raw_features.extend([r for r in batch_results if r])
            await asyncio.sleep(0.2) # Avoid Binance rate limit

        # Compute cross-sectional relative strength features
        final_features = compute_relative_strength(raw_features, btc_momentum_5m)
        results = final_features
        logger.info(f"Successfully computed features for {len(results)} pairs.")

    except asyncio.CancelledError:
        logger.warning("Scan cancelled")
    except Exception as e:
        logger.error(f"Market scan failed: {e}")
    finally:
        try:
            await asyncio.shield(client.close_connection())
        except Exception:
            pass

    return results
