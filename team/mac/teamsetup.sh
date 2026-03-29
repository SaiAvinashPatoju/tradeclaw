#!/usr/bin/env bash
set -euo pipefail

echo "[Team Setup][1/3] Checking Docker CLI..."
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI not found. Install Docker Desktop for Mac:"
  echo "https://docs.docker.com/desktop/setup/install/mac-install/"
  exit 1
fi

echo "[Team Setup][2/3] Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Open Docker Desktop and retry."
  exit 1
fi

echo "[Team Setup][3/3] Pulling Spark image..."
docker pull apache/spark:3.5.1 >/dev/null

echo "Setup completed successfully."
