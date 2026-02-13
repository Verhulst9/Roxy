@echo off
echo ======================================
echo Starting Nakari Desktop Pet
echo ======================================
echo.

REM 检查 API Server 是否运行
curl -s http://localhost:8000/api/status >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] API Server is not running!
    echo Please start the API Server first:
    echo   1. Start Redis: docker start redis-nakari
    echo   2. Start Celery: D:\anaconda\envs\nakari\python.exe -m celery -A tasks.app worker --loglevel=info --pool=solo
    echo   3. Start API: D:\anaconda\envs\nakari\python.exe api_server.py
    echo.
    pause
    exit /b 1
)

echo [1/2] Checking dependencies...
D:\anaconda\envs\nakari\python.exe -c "import PyQt5" 2>nul
if %errorlevel% neq 0 (
    echo Installing PyQt5...
    D:\anaconda\envs\nakari\python.exe -m pip install PyQt5 pyqtgraph trimesh websockets
)

echo [2/2] Launching Desktop Pet...
D:\anaconda\envs\nakari\python.exe modeling\desktop_pet.py

pause
