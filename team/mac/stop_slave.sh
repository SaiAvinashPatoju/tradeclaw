#!/usr/bin/env bash
set -euo pipefail

WORKER_ID="${1:-}"
if [ -z "$WORKER_ID" ]; then
  read -r -p "Enter worker id to stop (1 or 2): " WORKER_ID
fi

if [ "$WORKER_ID" != "1" ] && [ "$WORKER_ID" != "2" ]; then
  echo "Worker ID must be 1 or 2."
  exit 1
fi

WORKER_NAME="tradeclaw-remote-worker-$WORKER_ID"
docker rm -f "$WORKER_NAME" >/dev/null 2>&1 || true

echo "$WORKER_NAME stopped/removed."
