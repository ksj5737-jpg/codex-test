@echo off
setlocal
cd /d "%~dp0"
echo Face Library - local photo organizer
echo.
if exist ".venv\Scripts\python.exe" goto install
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    py -3.12 -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Open http://127.0.0.1:5000 in your browser after the server starts.
echo Keep this window open while using the app. Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto failed
goto end
:failed
echo.
echo Startup failed. Read the error above.
echo Python 3.12 is recommended. Install it from python.org if Python is missing.
echo When installing Python, select "Add python.exe to PATH".
:end
pause
