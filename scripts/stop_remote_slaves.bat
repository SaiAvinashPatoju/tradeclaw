@echo off
setlocal
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "%~dp0stop_remote_slaves.ps1"
echo Remote workers stop command issued.
pause
