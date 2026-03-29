@echo off
setlocal
cd /d "%~dp0\.."

if "%~1"=="" (
  echo Usage: planA_master_start.bat MASTER_IP [--fallback]
  echo Example: planA_master_start.bat 192.168.1.10
  echo Example: planA_master_start.bat 192.168.1.10 --fallback
  pause
  exit /b 1
)

set "MASTER_IP=%~1"
set "FALLBACK="
if /I "%~2"=="--fallback" set "FALLBACK=-UseLocalWorkersFallback"

powershell -ExecutionPolicy Bypass -File "%~dp0planA_master_start.ps1" -MasterIp "%MASTER_IP%" %FALLBACK%
if errorlevel 1 (
  echo.
  echo Plan A master start failed.
  pause
  exit /b 1
)
