@echo off
echo ==========================================
echo   SatQuery AI - Quick Start Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
)

echo Starting Backend Server...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Start backend in background
echo Starting FastAPI server on port 8000...
start "SatQuery Backend" uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd ..

echo.
echo Starting Frontend Server...
cd frontend

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
)

REM Start frontend
echo Starting React development server on port 5173...
start "SatQuery Frontend" npm run dev

cd ..

echo.
echo ==========================================
echo   SatQuery AI is starting up!
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Close both terminal windows to stop the servers
echo.
pause
