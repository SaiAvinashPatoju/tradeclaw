"""
TradeClaw — Binance Market Scanner
Fetches kline data for top USDT pairs and calculates all indicators.
"""
import asyncio
import logging
import time
from binance import AsyncClient

from .indicators import (
    calculate_rsi,
    calculate_vwap,
    calculate_volume_sma_ratio,
    calculate_price_change_pct,
    determine_btc_regime,
    calculate_vwap_deviation,
)

logger = logging.getLogger("tradeclaw.scanner")

# Top USDT pairs to scan (static list, covers major alts)
TOP_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "MATICUSDT", "SHIBUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT",
    "NEARUSDT", "APTUSDT", "OPUSDT", "ARBUSDT", "INJUSDT",
    "SUIUSDT", "SEIUSDT", "TIAUSDT", "JUPUSDT", "WIFUSDT",
    "FETUSDT", "RNDRUSDT", "GRTUSDT", "FILUSDT", "PEPEUSDT",
]


async def _fetch_klines(client: AsyncClient, symbol: str,
                        interval: str, limit: int = 50) -> list:
    """Fetch kline data for a given symbol and interval with error handling."""
    try:
        klines = await client.get_klines(symbol=symbol, interval=interval, limit=limit)
        return klines
    except Exception as e:
        logger.warning(f"Failed to fetch {interval} klines for {symbol}: {e}")
        return []


def _extract_ohlcv(klines: list) -> dict:
    """Extract OHLCV data from Binance kline format."""
    if not klines:
        return {"opens": [], "highs": [], "lows": [], "closes": [], "volumes": []}

    opens = [float(k[1]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    closes = [float(k[4]) for k in klines]
    volumes = [float(k[5]) for k in klines]

    return {
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "volumes": volumes,
    }


async def _scan_single_pair(client: AsyncClient, symbol: str,
                            btc_regime: str, btc_15m_change: float) -> dict | None:
    """Scan a single trading pair and return its metrics."""
    try:
        # Fetch multiple timeframes
        klines_5m = await _fetch_klines(client, symbol, "5m", 50)
        await asyncio.sleep(0.1)  # Rate limit protection
        klines_15m = await _fetch_klines(client, symbol, "15m", 20)
        await asyncio.sleep(0.1)
        klines_1h = await _fetch_klines(client, symbol, "1h", 5)
        await asyncio.sleep(0.1)

        if not klines_5m or not klines_15m or not klines_1h:
            return None

        data_5m = _extract_ohlcv(klines_5m)
        data_15m = _extract_ohlcv(klines_15m)
        data_1h = _extract_ohlcv(klines_1h)

        # Calculate indicators
        price_change_5m = calculate_price_change_pct(
            data_5m["opens"][-1], data_5m["closes"][-1]
        )
        price_change_15m = calculate_price_change_pct(
            data_15m["opens"][-1], data_15m["closes"][-1]
        )
        price_change_1h = calculate_price_change_pct(
            data_1h["opens"][-1], data_1h["closes"][-1]
        )

        rsi = calculate_rsi(data_5m["closes"])
        vwap = calculate_vwap(
            data_5m["highs"], data_5m["lows"],
            data_5m["closes"], data_5m["volumes"]
        )
        volume_sma_ratio = calculate_volume_sma_ratio(data_5m["volumes"])
        current_price = data_5m["closes"][-1]
        vwap_deviation = calculate_vwap_deviation(current_price, vwap)

        return {
            "symbol": symbol,
            "price": current_price,
            "volume": data_5m["volumes"][-1],
            "price_change_5m": price_change_5m,
            "price_change_15m": price_change_15m,
            "price_change_1h": price_change_1h,
            "rsi": rsi,
            "vwap": vwap,
            "vwap_deviation": vwap_deviation,
            "volume_sma_ratio": volume_sma_ratio,
            "btc_regime": btc_regime,
            "btc_15m_change": btc_15m_change,
            "timestamp": int(time.time()),
        }

    except Exception as e:
        logger.error(f"Error scanning {symbol}: {e}")
        return None


async def scan_market(api_key: str, api_secret: str) -> list[dict]:
    """
    Main market scanner. Fetches data for top 30 USDT pairs,
    calculates all indicators, and returns list of metric dicts.
    """
    client = await AsyncClient.create(api_key, api_secret)
    results = []

    try:
        # First, determine BTC regime
        btc_1h_klines = await _fetch_klines(client, "BTCUSDT", "1h", 5)
        btc_15m_klines = await _fetch_klines(client, "BTCUSDT", "15m", 5)

        if btc_1h_klines:
            btc_1h_data = _extract_ohlcv(btc_1h_klines)
            btc_1h_change = calculate_price_change_pct(
                btc_1h_data["opens"][-1], btc_1h_data["closes"][-1]
            )
            btc_regime = determine_btc_regime(btc_1h_change)
        else:
            btc_1h_change = 0.0
            btc_regime = "NEUTRAL"

        if btc_15m_klines:
            btc_15m_data = _extract_ohlcv(btc_15m_klines)
            btc_15m_change = calculate_price_change_pct(
                btc_15m_data["opens"][-1], btc_15m_data["closes"][-1]
            )
        else:
            btc_15m_change = 0.0

        logger.info(f"BTC regime: {btc_regime} (1h: {btc_1h_change:.2f}%, "
                     f"15m: {btc_15m_change:.2f}%)")

        # Scan each pair
        for symbol in TOP_PAIRS:
            metrics = await _scan_single_pair(client, symbol, btc_regime, btc_15m_change)
            if metrics:
                results.append(metrics)

        logger.info(f"Scanned {len(results)}/{len(TOP_PAIRS)} pairs successfully")

    except asyncio.CancelledError:
        logger.warning("Scan cancelled — returning partial results")
    except Exception as e:
        logger.error(f"Market scan failed: {e}")

    finally:
        # Shield the cleanup so CancelledError doesn't cut it off
        try:
            await asyncio.shield(client.close_connection())
        except Exception:
            pass

    return results
