@echo off
setlocal
cd /d "%~dp0"

set "INSTALL_FLAG="
if /I "%~1"=="--install-docker" set "INSTALL_FLAG=-InstallDockerDesktop"

powershell -ExecutionPolicy Bypass -File "%~dp0worker_install_and_prepare.ps1" %INSTALL_FLAG%
if errorlevel 1 (
  echo.
  echo Worker setup failed.
  pause
  exit /b 1
)

echo Worker setup completed.
pause
