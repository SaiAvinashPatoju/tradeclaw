#!/usr/bin/env bash
set -euo pipefail

for worker in tradeclaw-remote-worker-1 tradeclaw-remote-worker-2; do
  echo "Stopping $worker ..."
  docker rm -f "$worker" >/dev/null 2>&1 || true
done

echo "Remote worker cleanup complete."
