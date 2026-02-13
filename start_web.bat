@echo off
echo ======================================
echo Starting Nakari Web Interface
echo ======================================
echo.

echo [1/2] Starting API Server...
start "Nakari - API Server" cmd /k "D:\anaconda\envs\nakari\python.exe api_server.py"
timeout /t 2 /nobreak >nul
echo.

echo [2/2] Opening Frontend...
start "" "c:\Users\Administrator\nakari\frontend\index.html"

echo.
echo Web interface is ready!
echo API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
