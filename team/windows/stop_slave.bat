@echo off
setlocal

set "WORKER_ID=%~1"
if "%WORKER_ID%"=="" set /p WORKER_ID=Enter worker id to stop (1 or 2): 

if not "%WORKER_ID%"=="1" if not "%WORKER_ID%"=="2" (
  echo Worker ID must be 1 or 2.
  pause
  exit /b 1
)

set "WORKER_NAME=tradeclaw-remote-worker-%WORKER_ID%"
docker rm -f %WORKER_NAME% >nul 2>nul
echo %WORKER_NAME% stopped/removed.
pause
