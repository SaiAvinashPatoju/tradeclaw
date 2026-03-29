@echo off
setlocal
cd /d "%~dp0"

echo [0.5/4] Freeing Port 8001 (TradeClaw API Port)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
  if not "%%a"=="" taskkill /F /PID %%a >nul 2>nul
)

echo [1/4] Starting Docker Containers (Master + 3 Workers + Kafka + Postgres)...
docker-compose up -d

echo.
echo [1.1/4] Waiting for Kafka to become ready...
set KAFKA_READY=
for /L %%i in (1,1,30) do (
  docker exec -i tradeclaw-kafka kafka-topics --bootstrap-server kafka:29092 --list >nul 2>nul
  if not errorlevel 1 (
    set KAFKA_READY=1
    goto :kafka_ready
  )
  timeout /t 2 /nobreak >nul
)
:kafka_ready
if not defined KAFKA_READY (
  echo ERROR: Kafka did not become ready in time.
  pause
  exit /b 1
)

echo [1.2/4] Waiting for Postgres to become ready...
set PG_READY=
for /L %%i in (1,1,30) do (
  docker exec -i tradeclaw-postgres pg_isready -U tradeclaw -d tradeclaw >nul 2>nul
  if not errorlevel 1 (
    set PG_READY=1
    goto :pg_ready
  )
  timeout /t 2 /nobreak >nul
)
:pg_ready
if not defined PG_READY (
  echo ERROR: Postgres did not become ready in time.
  pause
  exit /b 1
)

echo.
echo [2/4] Initializing Database Schema...
set PYTHONPATH=.
call venv\Scripts\python.exe rebuild_db.py

echo.
echo [3/5] Starting Tick Simulator in a new window...
start "Tradeclaw Simulator" cmd /k "call venv\Scripts\activate.bat && set ""KAFKA_BOOTSTRAP_SERVERS=localhost:9092"" && set ""KAFKA_TOPIC=tradeclaw_ticks"" && python -m backend.data_simulator"

echo.
echo [4/5] Starting TradeClaw Backend API in a new window...
start "Tradeclaw API" cmd /k "call venv\Scripts\activate.bat && set ""PYTHONPATH=."" && set ""DATABASE_URL=postgresql://tradeclaw:tradeclaw@localhost:5432/tradeclaw"" && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001"

echo.
echo [4.5/5] Clearing stale Spark analyzer processes (if any)...
docker exec -i tradeclaw-spark-master sh -lc "pkill -f tradeclaw-streaming-analyzer || true"

echo.
echo [5/5] Submitting Spark Streaming Job...
echo ^(This will run in this window. Press Ctrl+C to stop^)
echo.
docker exec -it tradeclaw-spark-master /opt/spark/bin/spark-submit ^
  --master spark://spark-master:7077 ^
  --conf spark.jars.ivy=/tmp/.ivy ^
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 ^
  /opt/tradeclaw/backend/spark_analyzer.py

pause
