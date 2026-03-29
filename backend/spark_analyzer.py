"""
PySpark Structured Streaming analyzer for Tradeclaw.

Reads ticks from Kafka, computes fast technical aggregates, repartitions by symbol,
and writes generated signals into the existing `signals` database table.

Usage example from spark-master container:
  spark-submit \
    --master spark://spark-master:7077 \
    /opt/tradeclaw/backend/spark_analyzer.py

Required env vars (inside spark containers):
  DATABASE_URL=postgresql://user:pass@host:5432/dbname
Optional env vars:
    KAFKA_BOOTSTRAP_SERVERS=kafka:29092
  KAFKA_TOPIC=tradeclaw_ticks
  SPARK_CHECKPOINT_DIR=/tmp/tradeclaw_checkpoints/spark_analyzer
"""

from __future__ import annotations

import os
import socket
import time
import uuid
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass
from typing import Iterable

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T


@dataclass(frozen=True)
class AnalyzerConfig:
    kafka_bootstrap_servers: str
    kafka_topic: str
    checkpoint_dir: str
    database_url: str


def _jdbc_config(database_url: str) -> tuple[str, dict[str, str]]:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError("Only postgresql DATABASE_URL is supported for JDBC sink")

    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/")
    jdbc_url = f"jdbc:postgresql://{host}:{port}/{dbname}"

    props = {
        "user": parsed.username or "",
        "password": parsed.password or "",
        "driver": "org.postgresql.Driver",
    }
    return jdbc_url, props


def load_config() -> AnalyzerConfig:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("Missing DATABASE_URL environment variable for spark_analyzer")

    parsed = urlparse(database_url)
    if parsed.hostname in {"localhost", "127.0.0.1"}:
        # Spark runs in a container; localhost there is not the host machine DB.
        netloc = parsed.netloc.replace(parsed.hostname, "host.docker.internal")
        database_url = urlunparse(parsed._replace(netloc=netloc))

    return AnalyzerConfig(
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092").strip(),
        kafka_topic=os.getenv("KAFKA_TOPIC", "tradeclaw_ticks").strip(),
        checkpoint_dir=os.getenv(
            "SPARK_CHECKPOINT_DIR",
            "/tmp/tradeclaw_checkpoints_v2",
        ).strip(),
        database_url=database_url,
    )


def create_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("tradeclaw-streaming-analyzer")
        .config("spark.sql.shuffle.partitions", "12")
        .config("spark.streaming.stopGracefullyOnShutdown", "true")
        .getOrCreate()
    )


def _partition_host_stats(df: DataFrame) -> list[tuple[int, str, int]]:
    def _count_partition(partition_id: int, rows: Iterable) -> Iterable[tuple[int, str, int]]:
        count = 0
        for _ in rows:
            count += 1
        yield (partition_id, socket.gethostname(), count)

    return df.rdd.mapPartitionsWithIndex(_count_partition).collect()


def _insert_signals(batch_df: DataFrame, database_url: str, rows: list[dict]) -> None:
    if not rows:
        return

    jdbc_url, props = _jdbc_config(database_url)
    sink_df = batch_df.sparkSession.createDataFrame(rows)
    (
        sink_df.write
        .mode("append")
        .jdbc(url=jdbc_url, table="signals", properties=props)
    )


def _signal_rows_from_batch(batch_df: DataFrame) -> list[dict]:
    now = int(time.time())
    expiry_at = now + (20 * 60)
    hold_period_secs = 4 * 60 * 60
    evaluation_at = expiry_at + hold_period_secs

    rows = []
    for row in batch_df.collect():
        entry_price = float(row.avg_price)
        momentum_5s = float(row.momentum_5s)
        volume_5s = float(row.volume_5s)

        score = min(100.0, max(0.0, (momentum_5s * 5000.0) + (volume_5s / 100.0)))
        confidence = "HIGH" if score >= 75 else "MEDIUM" if score >= 50 else "LOW"

        target_pct = 2.0
        stop_loss_pct = 0.8
        target_price = round(entry_price * (1 + target_pct / 100), 8)
        stop_price = round(entry_price * (1 - stop_loss_pct / 100), 8)

        rows.append(
            {
                "id": f"SPARK_{row.symbol}_{uuid.uuid4().hex[:12]}",
                "symbol": row.symbol,
                "generated_at": now,
                "expiry_at": expiry_at,
                "hold_period_secs": hold_period_secs,
                "evaluation_at": evaluation_at,
                "entry_low": round(entry_price * 0.999, 8),
                "entry_high": round(entry_price * 1.001, 8),
                "entry_price_assumed": round(entry_price, 8),
                "target_pct": target_pct,
                "stop_loss_pct": stop_loss_pct,
                "target_price": target_price,
                "stop_price": stop_price,
                "score": round(score, 2),
                "confidence": confidence,
                "reason": (
                    f"Spark stream momentum={momentum_5s * 100:.3f}% "
                    f"| vol5s={volume_5s:.2f}"
                ),
                "status": "ACTIVE",
                "fcm_sent": False,
            }
        )

    return rows


def process_batch(batch_df: DataFrame, batch_id: int, database_url: str) -> None:
    if batch_df.rdd.isEmpty():
        print(f"[spark] batch={batch_id} empty")
        return

    # Force distribution by symbol so blocks are spread across workers.
    distributed = batch_df.repartition(6, "symbol")

    host_stats = _partition_host_stats(distributed)
    print(f"[spark] batch={batch_id} partition/host stats: {host_stats}")

    # Relaxed signal thresholds for "mid-algorithm" testing to generate frequent signals
    candidates = distributed.filter(
        (F.col("momentum_5s") > F.lit(0.0001)) &
        (F.col("volume_5s") > F.lit(500.0))
    )

    if candidates.rdd.isEmpty():
        print(f"[spark] batch={batch_id} no signal candidates")
        return

    signal_rows = _signal_rows_from_batch(candidates)
    try:
        _insert_signals(batch_df, database_url, signal_rows)
        print(f"[spark] batch={batch_id} inserted {len(signal_rows)} signals")
    except Exception as exc:
        print(
            f"[spark] batch={batch_id} generated {len(signal_rows)} signals "
            f"but DB write failed: {exc}"
        )


def main() -> None:
    cfg = load_config()
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    schema = T.StructType(
        [
            T.StructField("symbol", T.StringType(), False),
            T.StructField("price", T.DoubleType(), False),
            T.StructField("volume", T.DoubleType(), False),
            T.StructField("event_time", T.StringType(), False),
            T.StructField("ts_us", T.LongType(), False),
        ]
    )

    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", cfg.kafka_bootstrap_servers)
        .option("subscribe", cfg.kafka_topic)
        .option("startingOffsets", "latest")
        .load()
    )

    ticks = (
        raw.select(F.from_json(F.col("value").cast("string"), schema).alias("data"))
        .select("data.*")
        .withColumn("event_ts", F.to_timestamp("event_time"))
        .filter(F.col("event_ts").isNotNull())
    )

    # 5-second rolling windows to capture short-term burst momentum.
    analytics = (
        ticks
        .withWatermark("event_ts", "10 seconds")
        .groupBy(
            F.window("event_ts", "5 seconds", "2 seconds"),
            F.col("symbol"),
        )
        .agg(
            F.avg("price").alias("avg_price"),
            F.max("price").alias("max_price"),
            F.min("price").alias("min_price"),
            F.sum("volume").alias("volume_5s"),
            F.count("*").alias("tick_count"),
        )
        .withColumn(
            "momentum_5s",
            F.when(
                F.col("min_price") > 0,
                (F.col("max_price") - F.col("min_price")) / F.col("min_price"),
            ).otherwise(F.lit(0.0)),
        )
        .select(
            "symbol",
            "avg_price",
            "volume_5s",
            "tick_count",
            "momentum_5s",
        )
    )

    query = (
        analytics.writeStream
        .outputMode("update")
        .foreachBatch(lambda df, batch_id: process_batch(df, batch_id, cfg.database_url))
        .start()
    )

    print("[spark] tradeclaw-streaming-analyzer started")
    query.awaitTermination()


if __name__ == "__main__":
    main()
