# CommercePulse Development Environment Setup
param()

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RootDir ".env"
$EnvExample = Join-Path $RootDir ".env.example"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "CommercePulse Development Environment Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $EnvFile)) {
    Write-Host "[1/4] Creating .env from .env.example..." -ForegroundColor Green
    Copy-Item -Path $EnvExample -Destination $EnvFile
    Write-Host "  Created: $EnvFile"
    Write-Host "  IMPORTANT: Edit .env and set real values before starting services!" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[1/4] .env already exists, skipping copy." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "[2/4] Creating Docker volumes..." -ForegroundColor Green

$Volumes = @(
    "commercepulse_postgres_data",
    "commercepulse_redis_data",
    "commercepulse_backend_venv",
    "commercepulse_nginx_certs",
    "commercepulse_nginx_cache",
    "commercepulse_nginx_logs"
)

foreach ($Volume in $Volumes) {
    $exists = $false
    try {
        $null = docker volume inspect $Volume 2>&1
        $exists = $true
    } catch {
        $exists = $false
    }

    if ($exists) {
        Write-Host "  Volume exists: $Volume"
    } else {
        docker volume create $Volume | Out-Null
        Write-Host "  Created volume: $Volume"
    }
}
Write-Host ""

Write-Host "[3/4] Verifying Docker and Docker Compose..." -ForegroundColor Green

$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerExists) {
    Write-Host "  ERROR: Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}
Write-Host "  Docker: $(& docker --version)"

$composeExists = $false
try {
    $null = & docker compose version 2>&1
    $composeExists = $true
} catch {
    $composeExists = $false
}

if ($composeExists) {
    Write-Host "  Docker Compose: $(& docker compose version)"
} else {
    Write-Host "  WARNING: Docker Compose not found. Install Docker Compose plugin." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "[4/4] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edit the .env file with your configuration:"
Write-Host "     notepad $EnvFile"
Write-Host ""
Write-Host "2. Start development services:"
Write-Host "     cd $RootDir"
Write-Host "     docker compose up --build"
Write-Host ""
Write-Host "3. Or start specific services only:"
Write-Host "     docker compose up postgres redis"
Write-Host "     docker compose up backend worker"
Write-Host "     docker compose up frontend"
Write-Host ""
Write-Host "4. Include nginx in production mode:"
Write-Host "     docker compose --profile production up --build"
Write-Host ""
Write-Host "5. Run tests:"
Write-Host "     & $RootDir\scripts\run-tests.sh"
Write-Host ""
Write-Host "6. Service URLs:"
Write-Host "     Frontend:  http://localhost:3000"
Write-Host "     Backend:   http://localhost:8000/api/v1"
Write-Host "     API Docs:  http://localhost:8000/docs"
Write-Host "     Postgres:  localhost:5432"
Write-Host "     Redis:     localhost:6379"
Write-Host "     Nginx:     http://localhost (prod profile)"
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
