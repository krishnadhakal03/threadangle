# Threadangle - Quick Start Script
# This script will start both backend and frontend servers

Write-Host "🚀 Starting Threadangle Application" -ForegroundColor Cyan
Write-Host "=" * 60

# Backend
Write-Host "`n📦 BACKEND SERVER" -ForegroundColor Yellow
Write-Host "Starting backend on http://127.0.0.1:8000" -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python start_backend.py"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Frontend  
Write-Host "`n🎨 FRONTEND SERVER" -ForegroundColor Yellow
Write-Host "Starting frontend on http://localhost:5173" -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "`n✅ Both servers are starting in separate windows!" -ForegroundColor Green
Write-Host "📍 Open your browser to: http://localhost:5173" -ForegroundColor Cyan
Write-Host "`nPress any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
