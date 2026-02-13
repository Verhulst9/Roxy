@echo off
echo ======================================
echo Starting Nakari AI System
echo ======================================
echo.

echo [1/4] Starting Redis...
docker start redis-nakari
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Redis. Please make sure Docker Desktop is running.
    pause
    exit /b 1
)
echo Redis started.
echo.

echo [2/4] Starting Celery Worker...
start "Nakari - Celery Worker" cmd /k "D:\anaconda\envs\nakari\python.exe -m celery -A tasks.app worker --loglevel=info --pool=solo"
timeout /t 3 /nobreak >nul
echo.

echo [3/4] Starting API Server...
start "Nakari - API Server" cmd /k "D:\anaconda\envs\nakari\python.exe api_server.py"
timeout /t 2 /nobreak >nul
echo.

echo [4/4] Opening Frontend...
start "" "c:\Users\Administrator\nakari\frontend\index.html"

echo.
echo ======================================
echo Nakari is running!
echo ======================================
echo.
echo Services:
echo   - Redis:       Running (Docker)
echo   - Celery:      Running (background)
echo   - API Server:  http://localhost:8000
echo   - Frontend:     Opened in browser
echo.
echo API Documentation: http://localhost:8000/docs
echo.
