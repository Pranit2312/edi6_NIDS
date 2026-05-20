@echo off
REM NIDS Project Setup and Run Script for Windows

echo ================================
echo NIDS - Network Intrusion Detection System
echo ================================
echo.

REM Check Python version
echo [*] Checking Python version...
python --version
if errorlevel 1 (
    echo [!] Python not found. Please install Python 3.8+
    exit /b 1
)

REM Check Node.js version
echo [*] Checking Node.js version...
node --version
npm --version
if errorlevel 1 (
    echo [!] Node.js not found. Please install Node.js 16+
    exit /b 1
)

REM Setup Backend
echo.
echo [*] Setting up Backend...
cd backend

REM Create venv if not exists
if not exist "venv" (
    echo [*] Creating Python virtual environment...
    python -m venv venv
)

REM Activate venv
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [*] Installing Python dependencies...
pip install -r requirements.txt

REM Train ML model
echo [*] Training ML model...
cd ..\ml
python train_model.py

REM Back to backend
cd ..\backend

echo.
echo [*] Backend setup complete!
echo [*] To start backend, run: python app.py
echo.

REM Setup Frontend
echo [*] Setting up Frontend...
cd ..\frontend

if not exist "node_modules" (
    echo [*] Installing Node dependencies...
    call npm install
)

echo.
echo [*] Frontend setup complete!
echo [*] To start frontend, run: npm run dev
echo.

echo ================================
echo Setup Complete!
echo ================================
echo.
echo To run the project:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   venv\Scripts\activate
echo   python app.py
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Then open: http://localhost:3000
echo.
pause
