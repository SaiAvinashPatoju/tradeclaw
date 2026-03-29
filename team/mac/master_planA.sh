#!/usr/bin/env bash
set -euo pipefail

MASTER_IP="${1:-}"
if [ -z "$MASTER_IP" ]; then
  read -r -p "Enter this master laptop IP (example 192.168.1.10): " MASTER_IP
fi
if [ -z "$MASTER_IP" ]; then
  echo "Master IP is required."
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "[Master Plan A][1/6] Starting core services..."
docker-compose up -d postgres zookeeper kafka spark-master

echo "[Master Plan A][2/6] Waiting for Kafka/Postgres..."
for _ in $(seq 1 40); do
  if docker exec -i tradeclaw-kafka kafka-topics --bootstrap-server kafka:29092 --list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
for _ in $(seq 1 40); do
  if docker exec -i tradeclaw-postgres pg_isready -U tradeclaw -d tradeclaw >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "[Master Plan A][3/6] Rebuilding DB schema..."
PYTHONPATH=. ./venv/Scripts/python.exe rebuild_db.py

echo "[Master Plan A][4/6] Start simulator/API manually in separate terminals."
echo "Simulator: PYTHONPATH=. KAFKA_BOOTSTRAP_SERVERS=localhost:9092 KAFKA_TOPIC=tradeclaw_ticks ./venv/Scripts/python.exe -m backend.data_simulator"
echo "API:       PYTHONPATH=. DATABASE_URL=postgresql://tradeclaw:tradeclaw@localhost:5432/tradeclaw ./venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8001"

docker exec -i tradeclaw-spark-master sh -lc "pkill -f tradeclaw-streaming-analyzer || true" >/dev/null 2>&1 || true

echo "[Master Plan A][5/6] Ask teammates to run run_slave scripts, then check http://localhost:8080"
read -r -p "Press Enter when workers are visible..." _

echo "[Master Plan A][6/6] Submitting analyzer..."
docker exec -it tradeclaw-spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.driver.host="$MASTER_IP" \
  --conf spark.driver.port=35000 \
  --conf spark.blockManager.port=35001 \
  --conf spark.jars.ivy=/tmp/.ivy \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 \
  /opt/tradeclaw/backend/spark_analyzer.py
