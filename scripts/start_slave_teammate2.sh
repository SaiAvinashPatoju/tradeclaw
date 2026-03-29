#!/usr/bin/env bash
set -euo pipefail

MASTER_IP="${1:-}"
if [ -z "$MASTER_IP" ]; then
  read -r -p "Enter master laptop IP: " MASTER_IP
fi

if [ -z "$MASTER_IP" ]; then
  echo "Master IP is required."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/worker_install_and_prepare.sh"

WORKER_NAME="tradeclaw-remote-worker-2"
HOST_UI_PORT="8092"

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
