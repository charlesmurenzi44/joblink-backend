# Run on production DB from your PC (uses Railway public Postgres URL).
# Usage: railway run powershell -ExecutionPolicy Bypass -File scripts/seed_production.ps1

$ErrorActionPreference = 'Stop'

if (-not $env:DATABASE_PUBLIC_URL) {
    Write-Error 'DATABASE_PUBLIC_URL not set. Run via: railway run powershell -File scripts/seed_production.ps1'
}

$env:DATABASE_URL = $env:DATABASE_PUBLIC_URL.Trim()
$python = Join-Path $PSScriptRoot '..\venv\Scripts\python.exe'
$manage = Join-Path $PSScriptRoot '..\manage.py'

Write-Host 'Running migrations on production DB...' -ForegroundColor Cyan
& $python $manage migrate --noinput

& $python $manage seed_categories

if (Test-Path (Join-Path $PSScriptRoot '..\jobs\management\commands\seed_demo.py')) {
    & $python $manage seed_demo
} else {
    Write-Host 'seed_demo not found — skipping'
}

& $python $manage create_admin

Write-Host 'Production seed complete.' -ForegroundColor Green
