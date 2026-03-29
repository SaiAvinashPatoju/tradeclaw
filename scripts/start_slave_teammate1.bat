@echo off
setlocal
cd /d "%~dp0"

set "MASTER_IP=%~1"
if "%MASTER_IP%"=="" set /p MASTER_IP=Enter master laptop IP: 
if "%MASTER_IP%"=="" (
  echo Master IP is required.
  pause
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0start_slave_teammate1.ps1" -MasterIp "%MASTER_IP%"
if errorlevel 1 (
  echo.
  echo Failed to start teammate 1 worker.
  pause
  exit /b 1
)

echo Teammate 1 worker started.
pause
