@echo off
setlocal
cd /d "%~dp0\..\.."

set "MASTER_IP=%~1"
set "WORKER_ID=%~2"

if "%MASTER_IP%"=="" set /p MASTER_IP=Enter master laptop IP (example 192.168.1.10): 
if "%WORKER_ID%"=="" set /p WORKER_ID=Enter worker id (1 or 2): 

if "%MASTER_IP%"=="" (
  echo Master IP is required.
  pause
  exit /b 1
)

if not "%WORKER_ID%"=="1" if not "%WORKER_ID%"=="2" (
  echo Worker ID must be 1 or 2.
  pause
  exit /b 1
)

set "WORKER_NAME=tradeclaw-remote-worker-%WORKER_ID%"
if "%WORKER_ID%"=="1" (
  set "HOST_UI_PORT=8091"
) else (
  set "HOST_UI_PORT=8092"
)

echo Starting %WORKER_NAME% connected to master %MASTER_IP% ...
docker rm -f %WORKER_NAME% >nul 2>nul

docker run -d --name %WORKER_NAME% --restart unless-stopped --add-host spark-master:%MASTER_IP% -p %HOST_UI_PORT%:8081 apache/spark:3.5.1 /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077 --webui-port 8081 --cores 2 --memory 2g
if errorlevel 1 (
  echo Failed to start %WORKER_NAME%.
  pause
  exit /b 1
)

echo Worker started. Local UI: http://localhost:%HOST_UI_PORT%
docker ps --filter name=%WORKER_NAME%
pause
