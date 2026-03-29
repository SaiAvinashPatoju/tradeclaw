"""
Generates high-frequency synthetic market ticks and publishes them to Kafka.

Usage:
  python -m backend.data_simulator

Optional env vars:
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092
  KAFKA_TOPIC=tradeclaw_ticks
  TICKS_PER_SYMBOL_PER_SEC=20
"""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone

from kafka import KafkaProducer


SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
]

BASE_PRICES = {
    "BTCUSDT": 70000.0,
    "ETHUSDT": 3500.0,
    "SOLUSDT": 150.0,
    "BNBUSDT": 600.0,
    "XRPUSDT": 0.65,
    "ADAUSDT": 0.70,
}


def _build_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=5,
        acks=1,
        retries=3,
    )


def _next_price(current_price: float) -> float:
    # Tiny random walk that can sustain high-frequency stream simulation.
    delta = random.uniform(-0.0008, 0.0008)
    return max(0.0000001, current_price * (1 + delta))


def run() -> None:
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").strip()
    topic = os.getenv("KAFKA_TOPIC", "tradeclaw_ticks").strip()
    ticks_per_symbol = int(os.getenv("TICKS_PER_SYMBOL_PER_SEC", "20"))
    sleep_per_tick = 1.0 / max(ticks_per_symbol, 1)

    if not topic:
        raise ValueError("KAFKA_TOPIC cannot be empty")

    prices = dict(BASE_PRICES)
    producer = _build_producer(bootstrap_servers)

    print(
        f"[simulator] Publishing to {topic} @ {bootstrap_servers} | "
        f"{ticks_per_symbol} ticks/s per symbol"
    )

    try:
        while True:
            cycle_start = time.time()
            for symbol in SYMBOLS:
                prices[symbol] = _next_price(prices[symbol])
                payload = {
                    "symbol": symbol,
                    "price": round(prices[symbol], 8),
                    "volume": round(random.uniform(10, 3000), 4),
                    "event_time": datetime.now(tz=timezone.utc).isoformat(),
                    "ts_us": time.time_ns() // 1000,
                }
                producer.send(topic, payload)

            producer.flush(timeout=1)

            elapsed = time.time() - cycle_start
            remaining = sleep_per_tick - elapsed
            if remaining > 0:
                time.sleep(remaining)
    except KeyboardInterrupt:
        print("\n[simulator] Stopped.")
    finally:
        producer.flush(timeout=2)
        producer.close()


if __name__ == "__main__":
    run()
