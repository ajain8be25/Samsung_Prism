@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher was not found. Install Python 3.10 or newer, then try again.
  pause
  exit /b 1
)
py server.py
if errorlevel 1 (
  echo.
  echo The app could not start. Check that port 8000 is available.
  pause
)
