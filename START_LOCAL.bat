@echo off
echo ╔════════════════════════════════════════════════════════════╗
echo ║          STARTING THREADANGLE LOCAL ENVIRONMENT            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Start Backend in new window
echo [1/2] Starting Backend Server (Port 8000)...
start "Threadangle Backend" cmd /k "cd /d F:\Threadforge\backend && call ..\venv\Scripts\activate.bat && uvicorn main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

REM Start Frontend in new window
echo [2/2] Starting Frontend Dev Server (Port 5173)...
start "Threadangle Frontend" cmd /k "cd /d F:\Threadforge\frontend && npm run dev"
timeout /t 3 /nobreak >nul

REM Open browser
echo.
echo ✅ Servers starting...
echo.
echo 🌐 Backend:  http://localhost:8000
echo 🌐 Frontend: http://localhost:5173
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo ✅ DONE! Check the terminal windows for logs.
echo.
echo To stop servers: Close the terminal windows or run STOP_LOCAL.bat
echo.
pause
