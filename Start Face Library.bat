@echo off
setlocal
cd /d "%~dp0"
echo Face Library - local photo organizer
echo.
rem Use a dedicated environment; preserve any older .venv and user data.
if exist ".venv312\Scripts\python.exe" goto validate
py -3.12 -c "import sys,struct; sys.exit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>&1
if not errorlevel 1 goto create_py
python -c "import sys,struct; sys.exit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>&1
if errorlevel 1 goto need_python
python -m venv .venv312
goto created
:create_py
py -3.12 -m venv .venv312
:created
if errorlevel 1 goto failed
:validate
".venv312\Scripts\python.exe" -c "import sys,struct; sys.exit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)"
if errorlevel 1 goto invalid_venv
:install
".venv312\Scripts\python.exe" -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Open http://127.0.0.1:5000 in your browser after the server starts.
echo Keep this window open while using the app. Press Ctrl+C to stop.
echo.
".venv312\Scripts\python.exe" app.py
if errorlevel 1 goto failed
goto end
:need_python
echo.
echo This app requires Python 3.12, 64-bit. Other Python versions can stay installed.
echo Install it using PowerShell:
echo winget install -e --id Python.Python.3.12 --architecture x64
echo Then close this window and double-click this launcher again.
goto end
:invalid_venv
echo.
echo .venv312 was created with an incompatible Python version.
echo Rename the .venv312 folder, then run this launcher again.
echo Your imported photos and tags are in data, not in .venv312.
goto end
:failed
echo.
echo Startup failed. Read the error above.
echo Python 3.12, 64-bit is required. This launcher does not compile dependencies.
:end
pause
