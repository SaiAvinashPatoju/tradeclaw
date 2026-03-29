#!/usr/bin/env bash
set -euo pipefail

MASTER_IP="${1:-}"
WORKER_ID="${2:-}"

if [ -z "$MASTER_IP" ]; then
  read -r -p "Enter master laptop IP (example 192.168.1.10): " MASTER_IP
fi

if [ -z "$WORKER_ID" ]; then
  read -r -p "Enter worker id (1 or 2): " WORKER_ID
fi

if [ -z "$MASTER_IP" ]; then
  echo "Master IP is required."
  exit 1
fi

if [ "$WORKER_ID" != "1" ] && [ "$WORKER_ID" != "2" ]; then
  echo "Worker ID must be 1 or 2."
  exit 1
fi

if [ "$WORKER_ID" = "1" ]; then
  WORKER_NAME="tradeclaw-remote-worker-1"
  HOST_UI_PORT="8091"
else
  WORKER_NAME="tradeclaw-remote-worker-2"
  HOST_UI_PORT="8092"
fi

docker rm -f "$WORKER_NAME" >/dev/null 2>&1 || true
docker run -d \
  --name "$WORKER_NAME" \
  --restart unless-stopped \
  --add-host "spark-master:$MASTER_IP" \
  -p "$HOST_UI_PORT:8081" \
  apache/spark:3.5.1 \
  /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker \
  spark://spark-master:7077 --webui-port 8081 --cores 2 --memory 2g >/dev/null

echo "Worker started: $WORKER_NAME"
echo "Local UI: http://localhost:$HOST_UI_PORT"
docker ps --filter "name=$WORKER_NAME"
