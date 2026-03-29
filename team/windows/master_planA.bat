@echo off
setlocal
cd /d "%~dp0\..\.."

set "MASTER_IP=%~1"
if "%MASTER_IP%"=="" set /p MASTER_IP=Enter this master laptop IP (example 192.168.1.10): 
if "%MASTER_IP%"=="" (
  echo Master IP is required.
  pause
  exit /b 1
)

echo [Master Plan A][1/7] Freeing API port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
  if not "%%a"=="" taskkill /F /PID %%a >nul 2>nul
)

echo [Master Plan A][2/7] Starting core services (postgres + zookeeper + kafka + spark-master)...
docker-compose up -d postgres zookeeper kafka spark-master
if errorlevel 1 (
  echo Failed to start core services.
  pause
  exit /b 1
)

echo [Master Plan A][3/7] Waiting for Kafka...
set KAFKA_READY=
for /L %%i in (1,1,40) do (
  docker exec -i tradeclaw-kafka kafka-topics --bootstrap-server kafka:29092 --list >nul 2>nul
  if not errorlevel 1 (
    set KAFKA_READY=1
    goto :kafka_ready
  )
  timeout /t 2 /nobreak >nul
)
:kafka_ready
if not defined KAFKA_READY (
  echo Kafka not ready in time.
  pause
  exit /b 1
)

echo [Master Plan A][4/7] Waiting for Postgres...
set PG_READY=
for /L %%i in (1,1,40) do (
  docker exec -i tradeclaw-postgres pg_isready -U tradeclaw -d tradeclaw >nul 2>nul
  if not errorlevel 1 (
    set PG_READY=1
    goto :pg_ready
  )
  timeout /t 2 /nobreak >nul
)
:pg_ready
if not defined PG_READY (
  echo Postgres not ready in time.
  pause
  exit /b 1
)

echo [Master Plan A][5/7] Rebuilding database schema...
set PYTHONPATH=.
call venv\Scripts\python.exe rebuild_db.py
if errorlevel 1 (
  echo DB rebuild failed.
  pause
  exit /b 1
)

echo [Master Plan A][6/7] Starting simulator and API...
start "TradeClaw Simulator" cmd /k "call venv\Scripts\activate.bat && set ""PYTHONPATH=."" && set ""KAFKA_BOOTSTRAP_SERVERS=localhost:9092"" && set ""KAFKA_TOPIC=tradeclaw_ticks"" && python -m backend.data_simulator"
start "TradeClaw API" cmd /k "call venv\Scripts\activate.bat && set ""PYTHONPATH=."" && set ""DATABASE_URL=postgresql://tradeclaw:tradeclaw@localhost:5432/tradeclaw"" && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001"

docker exec -i tradeclaw-spark-master sh -lc "pkill -f tradeclaw-streaming-analyzer || true" >nul 2>nul

echo.
echo Ask teammates to run teamsetup and run_slave scripts now.
echo Check Spark UI: http://localhost:8080
echo Press Enter after remote workers appear in Spark UI.
pause >nul

echo [Master Plan A][7/7] Submitting analyzer job with fixed driver ports...
docker exec -it tradeclaw-spark-master /opt/spark/bin/spark-submit ^
  --master spark://spark-master:7077 ^
  --conf spark.driver.bindAddress=0.0.0.0 ^
  --conf spark.driver.host=%MASTER_IP% ^
  --conf spark.driver.port=35000 ^
  --conf spark.blockManager.port=35001 ^
  --conf spark.jars.ivy=/tmp/.ivy ^
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 ^
  /opt/tradeclaw/backend/spark_analyzer.py

pause
