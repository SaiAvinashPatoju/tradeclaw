@echo off
setlocal
cd /d "%~dp0\..\.."

echo [Team Setup][1/3] Checking Docker CLI...
where docker >nul 2>nul
if errorlevel 1 (
  echo Docker CLI not found. Install Docker Desktop first.
  echo https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

echo [Team Setup][2/3] Checking Docker daemon...
docker info >nul 2>nul
if errorlevel 1 (
  echo Docker daemon is not running. Open Docker Desktop and retry.
  pause
  exit /b 1
)

echo [Team Setup][3/3] Pulling Spark image...
docker pull apache/spark:3.5.1
if errorlevel 1 (
  echo Failed to pull apache/spark:3.5.1
  pause
  exit /b 1
)

echo Setup completed successfully.
pause
