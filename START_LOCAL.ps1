# PowerShell version of START_LOCAL
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          STARTING THREADANGLE LOCAL ENVIRONMENT            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "[1/2] Starting Backend Server (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd F:\Threadforge\backend; ..\venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "[2/2] Starting Frontend Dev Server (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd F:\Threadforge\frontend; npm run dev"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ Servers starting..." -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening browser in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "✅ DONE! Check the PowerShell windows for logs." -ForegroundColor Green
Write-Host ""
Write-Host "To stop servers: Close the PowerShell windows or run .\STOP_LOCAL.ps1" -ForegroundColor Yellow
Write-Host ""
