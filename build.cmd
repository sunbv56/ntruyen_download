@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Simple one-shot build script for Windows (cmd)
REM - Detects Python (without requiring 'py' launcher)
REM - Creates a virtual env
REM - Installs requirements and PyInstaller
REM - Builds a single-file exe from main.py

cd /d "%~dp0"

echo [1/5] Detecting Python...
set "PYEXE="
where python >nul 2>&1 && set "PYEXE=python"
if not defined PYEXE (
    where python3 >nul 2>&1 && set "PYEXE=python3"
)
if not defined PYEXE (
    echo Python was not found in PATH. Please install Python 3 and try again.
    exit /b 1
)

echo [2/5] Creating virtual environment (if missing)...
if not exist .venv (
    %PYEXE% -m venv .venv || (
        echo Failed to create virtual environment. Ensure Python 3 is installed.
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"

if not exist %VENV_PY% (
    echo Virtual environment python not found at %VENV_PY%.
    exit /b 1
)

echo [3/5] Upgrading pip and installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip || (
    echo Failed to upgrade pip.
    exit /b 1
)
if exist requirements.txt (
    "%VENV_PY%" -m pip install -r requirements.txt || (
        echo Failed to install requirements.
        exit /b 1
    )
)
"%VENV_PY%" -m pip install --upgrade pyinstaller || (
    echo Failed to install PyInstaller.
    exit /b 1
)

echo [4/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for %%F in (*.spec) do del /q /f "%%F"

echo [5/5] Building executable (no console window)...
"%VENV_PY%" -m PyInstaller --noconfirm --onefile --noconsole --name tai_truyen_app main.py || (
    echo Build failed.
    exit /b 1
)

echo.
echo Build completed. The executable is at: dist\tai_truyen_app.exe
exit /b 0


