@echo off
REM CyberSeer Phase 1: Data Pipeline Setup (Windows)
REM Run this to setup and execute Phase 1 pipeline

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo            CyberSeer Phase 1: Data Pipeline Setup (Windows)
echo ================================================================================
echo.

REM Check Python
echo [1] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo [2] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate venv
echo [3] Activating virtual environment...
call venv\Scripts\activate.bat
echo Activated
echo.

REM Install dependencies
echo [4] Installing dependencies from requirements.txt...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    pause
    exit /b 1
)
echo Dependencies installed
echo.

REM Create directories
echo [5] Verifying data directories...
if not exist data\raw\cicids2018 mkdir data\raw\cicids2018
if not exist data\raw\ctu13 mkdir data\raw\ctu13
if not exist data\processed mkdir data\processed
if not exist data\sequences mkdir data\sequences
if not exist data\graphs mkdir data\graphs
echo Data directories ready
echo.

REM Run pipeline
echo [6] Running Phase 1 pipeline (real data only)...
echo.

python -m ml.preprocessing.run_pipeline --dataset ctu13
if errorlevel 1 goto error

echo.
echo ================================================================================
echo                       Phase 1 Complete - SUCCESS
echo.
echo Check data\validation_report.json for detailed statistics.
echo.
echo Processed data ready in:
echo   - data\processed\features.csv
echo   - data\sequences\X_sequences.npy
echo   - data\sequences\y_sequences.npy
echo   - data\graphs\graphs.json
echo.
echo ================================================================================
echo Next: Start Phase 2 - Baseline Models
echo   python ml\models\baseline.py
echo ================================================================================
echo.
pause
exit /b 0

:error
echo.
echo ERROR: Pipeline execution failed
echo Check the output above for details
echo.
pause
exit /b 1
