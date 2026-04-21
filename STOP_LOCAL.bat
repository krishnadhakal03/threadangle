@echo off
echo ╔════════════════════════════════════════════════════════════╗
echo ║          STOPPING THREADANGLE LOCAL ENVIRONMENT            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo Stopping Backend Server (Port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul
echo ✅ Backend stopped

echo.
echo Stopping Frontend Dev Server (Port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul
echo ✅ Frontend stopped

echo.
echo Stopping Node.js processes...
taskkill /F /IM node.exe 2>nul
echo ✅ Node processes stopped

echo.
echo Stopping Python/Uvicorn processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Threadangle Backend*" 2>nul
echo ✅ Python processes stopped

echo.
echo ════════════════════════════════════════════════════════════
echo ✅ ALL SERVERS STOPPED
echo ════════════════════════════════════════════════════════════
echo.
pause
