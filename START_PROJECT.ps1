# CommercePulse - Quick Start Script
# This script starts both backend and frontend servers

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  CommercePulse - E-commerce Analytics Platform" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is already running
$backendRunning = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($backendRunning) {
    Write-Host "✓ Backend already running on http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "Starting Backend Server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; python server_with_db.py"
    Start-Sleep -Seconds 5
    Write-Host "✓ Backend started on http://localhost:8000" -ForegroundColor Green
}

# Check if frontend is already running
$frontendRunning = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($frontendRunning) {
    Write-Host "✓ Frontend already running on http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "Starting Frontend Server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
    Start-Sleep -Seconds 3
    Write-Host "✓ Frontend started on http://localhost:3000" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Application Ready!" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Demo Login:" -ForegroundColor Yellow
Write-Host "  Email:    demo@commercepulse.com" -ForegroundColor White
Write-Host "  Password: demo123" -ForegroundColor White
Write-Host ""
Write-Host "Database:     backend/commercepulse.db" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in the server windows to stop" -ForegroundColor Gray
Write-Host ""
