Param(
    [Parameter(Mandatory = $true)]
    [string]$MasterIp,
    [switch]$UseLocalWorkersFallback
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $repoRoot

Write-Host "[Plan A][1/7] Freeing API port 8001..."
$connections = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $connections) {
    try {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    } catch {
    }
}

Write-Host "[Plan A][2/7] Starting core services on master laptop..."
$services = @("postgres", "zookeeper", "kafka", "spark-master")
if ($UseLocalWorkersFallback) {
    $services += @("spark-worker-1", "spark-worker-2", "spark-worker-3")
}
& docker-compose up -d @services

Write-Host "[Plan A][3/7] Waiting for Kafka readiness..."
$kafkaReady = $false
for ($i = 0; $i -lt 40; $i++) {
    & docker exec -i tradeclaw-kafka kafka-topics --bootstrap-server kafka:29092 --list *> $null
    if ($LASTEXITCODE -eq 0) {
        $kafkaReady = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $kafkaReady) {
    throw "Kafka did not become ready in time."
}

Write-Host "[Plan A][4/7] Waiting for Postgres readiness..."
$pgReady = $false
for ($i = 0; $i -lt 40; $i++) {
    & docker exec -i tradeclaw-postgres pg_isready -U tradeclaw -d tradeclaw *> $null
    if ($LASTEXITCODE -eq 0) {
        $pgReady = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $pgReady) {
    throw "Postgres did not become ready in time."
}

$pythonExe = Join-Path $repoRoot "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at $pythonExe"
}

Write-Host "[Plan A][5/7] Initializing DB schema..."
$env:PYTHONPATH = "."
& $pythonExe rebuild_db.py
if ($LASTEXITCODE -ne 0) {
    throw "Database schema initialization failed."
}

Write-Host "[Plan A][6/7] Starting simulator and backend API in separate windows..."
$simCmd = "$env:KAFKA_BOOTSTRAP_SERVERS='localhost:9092'; $env:KAFKA_TOPIC='tradeclaw_ticks'; $env:PYTHONPATH='.'; Set-Location '$repoRoot'; & '$pythonExe' -m backend.data_simulator"
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $simCmd)

$apiCmd = "$env:PYTHONPATH='.'; $env:DATABASE_URL='postgresql://tradeclaw:tradeclaw@localhost:5432/tradeclaw'; Set-Location '$repoRoot'; & '$pythonExe' -m uvicorn backend.main:app --host 0.0.0.0 --port 8001"
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $apiCmd)

Write-Host "[Plan A] Clearing stale analyzer process if present..."
& docker exec -i tradeclaw-spark-master sh -lc "pkill -f tradeclaw-streaming-analyzer || true" *> $null

Write-Host ""
Write-Host "Ask teammates to run their slave start scripts now."
Write-Host "Spark UI: http://localhost:8080"
Read-Host "Press Enter when remote workers are visible"

Write-Host "[Plan A][7/7] Submitting distributed Spark analyzer job..."
$submitArgs = @(
    "exec", "-it", "tradeclaw-spark-master",
    "/opt/spark/bin/spark-submit",
    "--master", "spark://spark-master:7077",
    "--conf", "spark.driver.bindAddress=0.0.0.0",
    "--conf", "spark.driver.host=$MasterIp",
    "--conf", "spark.driver.port=35000",
    "--conf", "spark.blockManager.port=35001",
    "--conf", "spark.jars.ivy=/tmp/.ivy",
    "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3",
    "/opt/tradeclaw/backend/spark_analyzer.py"
)
& docker @submitArgs
