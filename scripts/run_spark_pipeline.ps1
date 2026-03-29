Param(
    [string]$ComposeFile = "docker-compose.yml"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/4] Starting distributed stack (Kafka + Spark master + 3 workers)..."
docker-compose -f $ComposeFile up -d

Write-Host "[2/4] Running data simulator on host (Ctrl+C to stop)..."
Write-Host "      (Open another shell for step 3 commands)"
Write-Host "python -m backend.data_simulator"

Write-Host "[3/4] Submit Spark analyzer from master container:"
Write-Host "docker exec -it tradeclaw-spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.jars.ivy=/tmp/.ivy --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 /opt/tradeclaw/backend/spark_analyzer.py"

Write-Host "[4/4] Open Spark UI: http://localhost:8080"
Write-Host "      Verify 3 workers and check executor logs for partition distribution"
