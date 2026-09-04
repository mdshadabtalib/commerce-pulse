# CommercePulse - Status Check Script

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CommercePulse - System Status Check" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Backend
$backendPort = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
Write-Host "Backend Server (Port 8000):" -NoNewline
if ($backendPort) {
    Write-Host "  ✓ RUNNING" -ForegroundColor Green
} else {
    Write-Host "  ✗ STOPPED" -ForegroundColor Red
}

# Check Frontend
$frontendPort = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
Write-Host "Frontend Server (Port 3000):" -NoNewline
if ($frontendPort) {
    Write-Host " ✓ RUNNING" -ForegroundColor Green
} else {
    Write-Host " ✗ STOPPED" -ForegroundColor Red
}

# Check Database
Write-Host "Database File:" -NoNewline
if (Test-Path "backend/commercepulse.db") {
    Write-Host "              ✓ EXISTS" -ForegroundColor Green
} else {
    Write-Host "              ✗ MISSING" -ForegroundColor Red
}

Write-Host ""

# Test API if backend is running
if ($backendPort) {
    Write-Host "Testing API..." -ForegroundColor White
    $customers = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/customers" -UseBasicParsing -ErrorAction SilentlyContinue
    $products = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/products" -UseBasicParsing -ErrorAction SilentlyContinue
    
    if ($customers) {
        Write-Host "  Customers in DB: $($customers.Count)" -ForegroundColor Green
    }
    if ($products) {
        Write-Host "  Products in DB:  $($products.Count)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Quick Links" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Demo Login:  demo[at]commercepulse.com / demo123" -ForegroundColor Yellow
Write-Host ""
