@echo off
echo ============================================
echo  Project Cost Performance Tracker
echo ============================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Python not found. Install Python 3.10+ from https://python.org
        pause
        exit /b 1
    )
)

echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo.
echo Starting dashboard at http://localhost:8501
echo Press Ctrl+C to stop the server.
echo.

streamlit run app.py
